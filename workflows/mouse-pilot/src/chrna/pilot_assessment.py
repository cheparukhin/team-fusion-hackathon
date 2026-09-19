"""Explicit single-sample split-read assessment; no published outcomes are inputs."""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, asdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import re

from chrna.junction_ranking import Junction, aggregate_and_rank


@dataclass
class Alignment:
    read: str
    flag: int
    target: str
    start: int
    end: int
    mapq: int
    cigar: str
    strand: str
    qstart: int
    qend: int
    length: int
    blocks: list
    scores: dict
    source_line: int

    def score(self, start, end):
        return sum(self.scores.get(i, -2) for i in range(start, end))


def parse_alignment(line, source_line=0):
    f = line.rstrip().split('\t')
    flag = int(f[1])
    if flag & 4:
        return None
    ops = [(int(n), op) for n, op in re.findall(r'(\d+)([MIDNSHP=X])', f[5])]
    if ''.join(f'{n}{op}' for n,op in ops) != f[5]:
        raise ValueError('Invalid CIGAR')
    tags = dict((x.split(':',2)[0],x.split(':',2)[2]) for x in f[11:])
    if 'MD' not in tags:
        raise ValueError('MD tag is required for comparable edit rescoring')
    md_matches = []
    for token in re.findall(r'\d+|\^[A-Za-z]+|[A-Za-z]', tags['MD']):
        if token.isdigit():
            md_matches.extend([True]*int(token))
        elif not token.startswith('^'):
            md_matches.append(False)
    match_iter = iter(md_matches)
    length = sum(n for n,op in ops if op in 'MIS= XH'.replace(' ',''))
    q = 0
    ref = int(f[3])-1
    scores = {}
    blocks = []
    leading_deletion = 0
    for n, op in ops:
        if op in 'M=X':
            blocks.append((ref,ref+n))
            for _ in range(n):
                try:
                    matched = next(match_iter)
                except StopIteration as error:
                    raise ValueError('MD/CIGAR length mismatch') from error
                scores[q] = 1 if matched else -2
                if leading_deletion:
                    scores[q] -= leading_deletion
                    leading_deletion = 0
                q += 1
            ref += n
        elif op == 'I':
            for _ in range(n):
                scores[q] = -2
                q += 1
        elif op == 'D':
            # Charge the adjacent aligned base once; keep introns distinct.
            if scores:
                scores[max(scores)] -= 2*n
            else:
                leading_deletion += 2*n
            ref += n
        elif op == 'N':
            ref += n
        elif op in 'SH':
            q += n
    if next(match_iter, None) is not None:
        raise ValueError('Extra MD positions')
    if not scores or not blocks:
        raise ValueError('Mapped record has no aligned bases')
    strand = '-' if flag & 16 else '+'
    if strand == '-':
        scores = {length-1-k:v for k,v in scores.items()}
    return Alignment(f[0],flag,f[2],int(f[3])-1,ref,int(f[4]),f[5],strand,
                     min(scores),max(scores)+1,length,blocks,scores,source_line)


def load_sam(path):
    records = defaultdict(list)
    with path.open() as source:
        for number, line in enumerate(source,1):
            if line.startswith('@'):
                continue
            alignment = parse_alignment(line,number)
            if alignment:
                records[alignment.read].append(alignment)
    return records


def sam_groups(path):
    """Minimap2 emits consecutive records per query, in input order.

    Keep only one read's secondary alternatives in memory. Both audit SAMs use
    the same FASTQ and single-part indexes; mismatched order fails explicitly.
    Include unmapped query groups so absence of an alignment stays explicit.
    """
    current=None
    rows=[]
    with path.open() as source:
        for number,line in enumerate(source,1):
            if line.startswith('@'):
                continue
            read=line.split('\t',1)[0]
            if current is not None and read!=current:
                yield current,rows
                rows=[]
            current=read
            record=parse_alignment(line,number)
            if record:
                rows.append(record)
        if current is not None:
            yield current,rows


def merge_intervals(intervals):
    result = []
    for start,end in sorted(intervals):
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0],max(end,result[-1][1]))
        else:
            result.append((start,end))
    return result


def overlap(a,b):
    return max(0,min(a[1],b[1])-max(a[0],b[0]))


class GeneIndex:
    def __init__(self, path):
        self.genes = {}
        self.bins = defaultdict(set)
        opener = gzip.open if str(path).endswith('.gz') else open
        with opener(path,'rt') as source:
            for line in source:
                if line.startswith('#'):
                    continue
                f = line.rstrip().split('\t')
                if f[2] not in ('gene','exon'):
                    continue
                attrs = dict(re.findall(r'(\w+) "([^"]*)"',f[8]))
                gid = attrs['gene_id']
                gene = self.genes.setdefault(gid,{'gene_id':gid,'gene_name':attrs.get('gene_name',gid),
                    'chromosome':f[0],'strand':f[6],'biotype':attrs.get('gene_type','UNKNOWN'), 'exons':[]})
                if f[2]=='exon':
                    gene['exons'].append((int(f[3])-1,int(f[4])))
        for gid,gene in self.genes.items():
            gene['exons'] = merge_intervals(gene['exons'])
            for start,end in gene['exons']:
                for index in range(start//100000,(end-1)//100000+1):
                    self.bins[(gene['chromosome'],gene['strand'],index)].add(gid)

    def assign(self, alignment):
        candidates = set()
        for start,end in alignment.blocks:
            for index in range(start//100000,(end-1)//100000+1):
                candidates.update(self.bins[(alignment.target,alignment.strand,index)])
        result=[]
        for gid in candidates:
            matched = sum(overlap(block,exon) for block in alignment.blocks for exon in self.genes[gid]['exons'])
            if matched:
                result.append({'gene_id':gid,'exonic_overlap':matched})
        return sorted(result,key=lambda x:(-x['exonic_overlap'],x['gene_id']))


def compare_split(left,right,transcripts,genome):
    start,end = min(left.qstart,right.qstart),max(left.qend,right.qend)
    span = end-start
    split = sum(min(a for a in (left.scores.get(i),right.scores.get(i)) if a is not None)
                if i in left.scores or i in right.scores else -2 for i in range(start,end))
    best = max(transcripts,key=lambda x:x.score(start,end),default=None)
    best_score = best.score(start,end) if best else None
    margin = split-best_score if best else None
    tx_coverage = overlap((best.qstart,best.qend),(start,end))/span if best else None
    tolerance = max(20,0.05*span)
    competitors = []
    for arm in (left,right):
        for other in genome:
            if other is arm or not other.flag & 256:
                continue
            if other.target==arm.target and other.strand==arm.strand and abs(other.start-arm.start)<=20 and abs(other.end-arm.end)<=20:
                continue
            width=arm.qend-arm.qstart
            if overlap((other.qstart,other.qend),(arm.qstart,arm.qend)) >= 0.9*width and other.score(arm.qstart,arm.qend) >= arm.score(arm.qstart,arm.qend)-max(10,0.05*width):
                competitors.append({'source_line':other.source_line,'target':other.target,'start':other.start,'end':other.end})
    return {'split_score':split,'single_score':best_score,'split_single_margin':margin,
            'single_target':best.target if best else None,'single_source_line':best.source_line if best else None,
            'single_coverage':tx_coverage,'score_tolerance':tolerance,'query_window':[start,end],
            'query_gap':right.qstart-left.qend,'split_coverage':len(set(left.scores)|set(right.scores))/left.length,
            'alternative_genome_placements':competitors,
            'single_explains':best is not None and tx_coverage>=0.9 and margin<=tolerance}


def decide(left,right,left_genes,right_genes,ga,gb,comparison):
    reasons=[]
    if comparison['single_explains']:
        return 'single_transcript_explained',['Known transcript covers split window with a near-equal or better edit score']
    shorter=min(len(left.scores),len(right.scores))
    if shorter<100 or min(ga['exonic_overlap'],gb['exonic_overlap'])<100:
        return 'insufficient_anchor',['Fewer than 100 aligned query or exonic overlap bases on an arm']
    if sum(g['exonic_overlap']>=100 for g in left_genes)!=1 or sum(g['exonic_overlap']>=100 for g in right_genes)!=1:
        reasons.append('Multiple gene assignments meet the anchor threshold')
    if min(left.mapq,right.mapq)<20:
        reasons.append('At least one arm has MAPQ below 20')
    if comparison['alternative_genome_placements']:
        reasons.append('Alternative genomic placement has a near-equal arm score')
    if comparison['split_coverage']<0.8:
        reasons.append('Split segments cover less than 80% of the query')
    if abs(comparison['query_gap'])>20:
        reasons.append('Query gap or overlap exceeds 20 bases')
    if comparison['split_single_margin'] is not None and comparison['split_single_margin']<=comparison['score_tolerance']:
        reasons.append('Single-transcript score is too close to split score')
    # A complete search with no returned transcript alignment is explicit absence
    # of an alignment, not proof of biological absence; mapper limits are reported.
    return ('ambiguous_single_vs_split',reasons) if reasons else ('supported_two_gene_junction',['Meets prespecified RNA mapping criteria'])


def longgf_membership(path):
    result=defaultdict(set)
    pair=None
    for line in path.read_text().splitlines():
        if line.startswith('GF\t'):
            pair=line.split()[1]
        elif line.startswith('SumGF'):
            pair=None
        elif pair:
            for read in re.findall(r'/([^()]+):\d+-\d+\)',line):
                result[read].add(pair)
    return result


def assess(directory,gtf,output, *, sample_id="SRR28984805", biological_sample_id="GSM8260877",
           reference_build="GRCm39/GENCODE_M28", rules_path=Path("docs/focused_pilot_rules.md")):
    # Unknown specimen identity is not an independent biological replicate.
    unknown_specimen = biological_sample_id is None
    rank_specimen = biological_sample_id or "UNKNOWN_SHARED_SPECIMEN"
    output.mkdir(parents=True,exist_ok=True)
    index=GeneIndex(gtf)
    genome=sam_groups(directory/'split_genome_audit.sam')
    transcript=sam_groups(directory/'split_transcript_audit.sam')
    membership=longgf_membership(directory/'LongGF.log')
    ranking=[]
    decisions=[]
    unassigned=[]
    read_count=0
    for genome_group,transcript_group in itertools.zip_longest(genome,transcript):
        if genome_group is None or transcript_group is None or genome_group[0]!=transcript_group[0]:
            raise ValueError('Audit SAM query ordering or completeness differs; reconcile before assessment')
        read,alignments=genome_group
        read_count+=1
        primary=sorted((a for a in alignments if not a.flag & 256),key=lambda a:(a.qstart,a.qend))
        for left,right in zip(primary,primary[1:]):
            lg,rg=index.assign(left),index.assign(right)
            comparison=compare_split(left,right,transcript_group[1],alignments)
            if not lg or not rg:
                unassigned.append({'read_id':read,'left_source_line':left.source_line,'right_source_line':right.source_line,'state':'unmapped/unresolved','reason':'At least one segment lacks a same-strand exonic gene assignment','left_gene_assignments':lg,'right_gene_assignments':rg,'comparison':comparison})
            for ga,gb in itertools.product(lg,rg):
                if ga['gene_id']==gb['gene_id']:
                    continue
                a,b=index.genes[ga['gene_id']],index.genes[gb['gene_id']]
                junction=Junction(reference_build,ga['gene_id'],left.target,left.strand,left.end if left.strand=='+' else left.start,
                                  gb['gene_id'],right.target,right.strand,right.start if right.strand=='+' else right.end)
                state,reasons=decide(left,right,lg,rg,ga,gb,comparison)
                pair=a['gene_name']+':'+b['gene_name']
                caller='LongGF' if pair in membership.get(read,set()) else 'alignment_scan'
                specific=min(left.mapq,right.mapq)>=20 and not comparison['alternative_genome_placements'] and sum(g['exonic_overlap']>=100 for g in lg)==1 and sum(g['exonic_overlap']>=100 for g in rg)==1
                ranking.append({'junction':junction,'sample_id':sample_id,'biological_sample_id':rank_specimen,'read_id':read,'state':state,
                                'mapping_specific':specific,'split_single_margin':comparison['split_single_margin'],'shorter_anchor_nt':min(len(left.scores),len(right.scores)),'caller':caller})
                decisions.append({'junction_id':junction.junction_id,**asdict(junction),'read_id':read,'state':state,'reasons':reasons,
                    'gene_name_5p':a['gene_name'],'gene_name_3p':b['gene_name'],'biotype_5p':a['biotype'],'biotype_3p':b['biotype'],
                    'proposal_source':caller,'longgf_pairs_for_read':sorted(membership.get(read,set())),
                    'left_alignment':{k:v for k,v in asdict(left).items() if k!='scores'},'right_alignment':{k:v for k,v in asdict(right).items() if k!='scores'},
                    'left_gene_assignments':lg,'right_gene_assignments':rg,'comparison':comparison})
    ranked=aggregate_and_rank(ranking)
    if unknown_specimen:
        for row in ranked:
            row["biological_samples"] = None
            row["biological_independence"] = "UNKNOWN"
            row["caller_association_resolution"] = "read_and_ordered_gene_pair"
            row["exact_caller_junction_agreement"] = None
            row["adapter_status"] = "NOT_ASSESSED"
    for name,rows in [('read_decisions.json',decisions),('rna_ranking.json',ranked),('unassigned_segments.json',unassigned)]:
        (output/name).write_text(json.dumps(rows,indent=2)+'\n')
    represented={(d['read_id'],d['gene_name_5p']+':'+d['gene_name_3p']) for d in decisions}
    unresolved=[{'read_id':read,'longgf_pair':pair,'state':'unmapped/unresolved',
                 'reason':'LongGF source pair not resolved to the same ordered two-gene junction by audit remapping; retain original caller record'}
                for read,pairs in membership.items() for pair in sorted(pairs) if (read,pair) not in represented]
    (output/'unresolved_longgf_proposals.json').write_text(json.dumps(unresolved,indent=2)+'\n')
    summary={'assessed_split_reads':read_count,'exact_junctions':len(ranked),
        'supported_exact_junctions':sum(r['evidence_state']=='supported_two_gene_junction' for r in ranked),
        'longgf_read_memberships':len(membership),'unassigned_segment_pairs':len(unassigned),'biological_samples':None if unknown_specimen else 1,'sample_id':sample_id,'reference_build':reference_build,
        'rules_sha256':hashlib.sha256(Path(rules_path).read_bytes()).hexdigest(),
        'status':'assessed_not_frozen','limitations':['One sample; no independent replication.','One caller; no multi-caller consensus.','Finite mapper search and supplementary-alignment proposal scope.','Heuristic technical thresholds; not a biological false-positive rate.']}
    (output/'assessment_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--gtf',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(assess(args.directory,args.gtf,args.output),indent=2))


if __name__=='__main__':
    main()
