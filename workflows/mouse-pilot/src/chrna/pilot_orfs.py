"""Observed and reference-assisted ORF hypotheses for an RNA-only ranking.

Reference-assisted hypotheses assume the reference allele at low-quality read
discrepancies. High-quality indels near the junction remain unresolved. These
are sequence hypotheses, never evidence that a protein exists.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re


_BASES='TCAG'
_AMINO='FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG'
CODONS={a+b+c:aa for (a,b,c),aa in zip(((a,b,c) for a in _BASES for b in _BASES for c in _BASES),_AMINO)}


def revcomp(seq):
    return seq.translate(str.maketrans('ACGTNacgtn','TGCANtgcan'))[::-1]


def spanning_orfs(rna,junction_start,junction_end,min_coding_nt=90):
    """Every ATG-to-first-stop forward ORF, with >=15 coding nt each side."""
    result=[]
    for start in range(len(rna)-2):
        if rna[start:start+3]!='ATG':
            continue
        protein=[]
        for end in range(start,len(rna)-2,3):
            aa=CODONS.get(rna[end:end+3],'X')
            if aa=='*':
                if end-start>=min_coding_nt and start+15<=junction_start and end>=junction_end+15 and 'X' not in protein:
                    result.append({'start':start,'stop_start':end,'end_including_stop':end+3,
                                   'frame':start%3,'protein':''.join(protein),'coding_nt':end-start})
                break
            protein.append(aa)
    return sorted(result,key=lambda x:(-x['coding_nt'],x['start'],x['protein']))


class IndexedFasta:
    def __init__(self,path):
        self.path=Path(path)
        self.index={}
        for line in Path(str(path)+'.fai').read_text().splitlines():
            f=line.split('\t')
            self.index[f[0]]=tuple(map(int,f[1:5]))

    def fetch(self,chrom,start,end):
        length,offset,width,linebytes=self.index[chrom]
        if not 0<=start<=end<=length:
            raise ValueError('Reference coordinates out of range')
        if start==end:
            return ''
        first=offset+(start//width)*linebytes+start%width
        last=offset+((end-1)//width)*linebytes+(end-1)%width+1
        with self.path.open('rb') as src:
            src.seek(first)
            value=src.read(last-first).replace(b'\n',b'').replace(b'\r',b'').decode().upper()
        assert len(value)==end-start
        return value


def project_arm(alignment,genome,read,quality):
    """Restore reference indels; retain high-quality observed substitutions.

    A high-quality indel is ambiguous rather than silently repaired. Low-quality
    corrections are recorded and remain reference assumptions in the report.
    """
    sequence=revcomp(read) if alignment['strand']=='-' else read
    qual=quality[::-1] if alignment['strand']=='-' else quality
    q=0
    r=alignment['start']
    chunks=[]
    changes=[]
    unresolved=[]
    for n,op in [(int(n),op) for n,op in re.findall(r'(\d+)([MIDNSHP=X])',alignment['cigar'])]:
        if op in 'M=X':
            reference=genome.fetch(alignment['target'],r,r+n)
            chars=list(reference)
            for i,base in enumerate(reference):
                if sequence[q+i]!=base:
                    phred=ord(qual[q+i])-33
                    action='retain_high_quality_observed_substitution' if phred>=30 else 'reference_assisted_low_quality_correction'
                    if phred>=30:
                        chars[i]=sequence[q+i]
                    changes.append({'query_position':q+i,'reference_position':r+i,'observed':sequence[q+i],'reference':base,'phred':phred,'action':action})
            chunks.append(''.join(chars));q+=n;r+=n
        elif op=='I':
            qs=[ord(c)-33 for c in qual[q:q+n]]
            if qs and min(qs)>=30:
                unresolved.append({'reason':'high_quality_insertion','query_position':q,'length':n})
            changes.append({'action':'reference_assisted_insertion_removal','query_position':q,'length':n,'minimum_phred':min(qs) if qs else None})
            q+=n
        elif op=='D':
            flank=[ord(qual[i])-33 for i in (q-1,q) if 0<=i<len(qual)]
            if flank and min(flank)>=30:
                unresolved.append({'reason':'deletion_with_high_quality_flanks','query_position':q,'length':n})
            chunks.append(genome.fetch(alignment['target'],r,r+n))
            changes.append({'action':'reference_assisted_deletion_restoration','query_position':q,'length':n,'minimum_flank_phred':min(flank) if flank else None})
            r+=n
        elif op=='N':
            r+=n
        elif op in 'SH':
            q+=n
    projected=''.join(chunks)
    if alignment['strand']=='-':
        projected=revcomp(projected)
    return projected,changes,unresolved


def reconstruct(decision,genome,sequence,quality):
    left,lc,lu=project_arm(decision['left_alignment'],genome,sequence,quality)
    right,rc,ru=project_arm(decision['right_alignment'],genome,sequence,quality)
    gap=decision['comparison']['query_gap']
    unresolved=lu+ru
    if gap<0:
        count=-gap
        interval=(decision['right_alignment']['qstart'],decision['left_alignment']['qend'])
        for arm in ('left','right'):
            for indel in overlap_indels(decision[arm+'_alignment'],interval,len(sequence)):
                unresolved.append({'reason':'indel_within_query_overlap_requires_coordinate_resolution','arm':arm,**indel})
        if left[-count:]!=right[:count]:
            unresolved.append({'reason':'overlap_has_different_reference_sequences','overlap_nt':count})
        assisted=left+right[count:]
        boundary=(len(left)-count,len(left))
    elif gap>0:
        start=decision['left_alignment']['qend'];end=decision['right_alignment']['qstart']
        insert=sequence[start:end]
        if min(ord(c)-33 for c in quality[start:end])<30:
            unresolved.append({'reason':'untemplated_gap_sequence_below_Q30','gap_nt':gap})
        assisted=left+insert+right
        boundary=(len(left),len(left)+len(insert))
    else:
        assisted=left+right
        boundary=(len(left),len(left))
    observed_bounds=sorted([decision['left_alignment']['qend'],decision['right_alignment']['qstart']])
    for arm,changes in (('left',lc),('right',rc)):
        alignment=decision[arm+'_alignment']
        for change in changes:
            change.update(arm=arm,reference_target=alignment['target'],alignment_strand=alignment['strand'],
                          query_coordinate_space='SAM alignment strand, including hard clips')
    return {'observed_rna':sequence,'observed_junction_interval':observed_bounds,
            'reference_assisted_rna':assisted,'reference_assisted_junction_interval':list(boundary),
            'corrections_and_variants':lc+rc,'unresolved_sequence_reasons':unresolved,
            'observed_orfs':spanning_orfs(sequence,*observed_bounds),
            'reference_assisted_orfs':spanning_orfs(assisted,*boundary),
            'assumption':'Reference allele at low-quality discrepancies; high-quality substitutions retained. Unvalidated sequence hypothesis, not a measured protein.',
            'nmd':'UNKNOWN: observed fragments do not establish full transcript architecture'}


def overlap_indels(alignment,interval,read_length):
    """Raw query overlap cannot be trimmed as projected bases across an indel."""
    q=0
    result=[]
    for n,op in [(int(n),op) for n,op in re.findall(r'(\d+)([MIDNSHP=X])',alignment['cigar'])]:
        start,end=q,q+(n if op=='I' else 0)
        if alignment['strand']=='-':
            start,end=read_length-end,read_length-start
        if (op=='I' and start<interval[1] and end>interval[0]) or (op=='D' and interval[0]<=start<=interval[1]):
            result.append({'operation':op,'length':n,'original_query_interval':[start,end]})
        if op in 'MIS=XH':
            q+=n
    return result


def run(assessment,fastq,genome_path,output,limit=100):
    output.mkdir(parents=True,exist_ok=True)
    ranked=json.loads((assessment/'rna_ranking.json').read_text())
    decisions=json.loads((assessment/'read_decisions.json').read_text())
    chosen=[r for r in ranked if r['evidence_state']=='supported_two_gene_junction'][:limit]
    order={r['junction_id']:r for r in chosen}
    by_read=defaultdict(list)
    for d in decisions:
        if d['junction_id'] in order and d['state']=='supported_two_gene_junction':
            by_read[d['read_id']].append(d)
    genome=IndexedFasta(genome_path)
    reconstructed=[]
    with fastq.open() as source:
        while True:
            lines=[source.readline().rstrip() for _ in range(4)]
            if not lines[0]:
                break
            rid=lines[0][1:].split()[0]
            for d in by_read.get(rid,[]):
                record=reconstruct(d,genome,lines[1],lines[3])
                record.update(read_id=rid,junction_id=d['junction_id'],rna_rank=order[d['junction_id']]['display_rank'],
                              gene_name_5p=d['gene_name_5p'],gene_name_3p=d['gene_name_3p'],
                              reference_build=d['reference_build'],source_fastq_header=lines[0])
                reconstructed.append(record)
    (output/'reconstructions.json').write_text(json.dumps(reconstructed,indent=2)+'\n')
    for label in ('observed','reference_assisted'):
        with (output/f'{label}_rna.fasta').open('w') as out:
            for i,r in enumerate(reconstructed):
                out.write(f'>{label}_{i} junction={r["junction_id"]} read={r["read_id"]}\n{r[label+"_rna"]}\n')
    hypotheses=[]
    for r in reconstructed:
        eligible=not r['unresolved_sequence_reasons']
        for i,orf in enumerate(r['reference_assisted_orfs']):
            digest=hashlib.sha256(orf['protein'].encode()).hexdigest()
            hypotheses.append({'protein_id':'protein_'+digest,'sequence_sha256':digest,'sequence':orf['protein'],
                'junction_id':r['junction_id'],'read_id':r['read_id'],'rna_rank':r['rna_rank'],
                'gene_name_5p':r['gene_name_5p'],'gene_name_3p':r['gene_name_3p'],
                'orf':{k:v for k,v in orf.items() if k!='protein'},'sequence_source':'reference_assisted',
                'sequence_resolved_under_assumptions':eligible,'longest_spanning_orf_for_read':i==0,
                'deferral_reasons':r['unresolved_sequence_reasons'],
                'protein_existence':'UNKNOWN','function':'UNKNOWN'})
    (output/'protein_hypotheses.json').write_text(json.dumps(hypotheses,indent=2)+'\n')
    with (output/'protein_hypotheses.fasta').open('w') as out:
        seen=set()
        for r in hypotheses:
            if r['protein_id'] not in seen:
                out.write(f'>{r["protein_id"]} source=reference_assisted eligibility_pending_shortlist_review\n{r["sequence"]}\n')
                seen.add(r['protein_id'])
    summary={'status':'reconstructed_not_selected_or_frozen','rna_junctions_considered':len(chosen),
             'read_reconstructions':len(reconstructed),'distinct_protein_hypotheses':len({r['protein_id'] for r in hypotheses}),
             'batch_limit':limit,'remaining_supported_rna_junctions_deferred':sum(r['evidence_state']=='supported_two_gene_junction' for r in ranked)-len(chosen)}
    (output/'orf_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assessment',type=Path,required=True)
    p.add_argument('--fastq',type=Path,required=True)
    p.add_argument('--genome',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--limit',type=int,default=100)
    a=p.parse_args()
    print(json.dumps(run(a.assessment,a.fastq,a.genome,a.output,a.limit),indent=2))


if __name__=='__main__':
    main()
