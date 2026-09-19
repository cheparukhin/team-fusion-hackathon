"""Trace frozen protein hypotheses to GENCODE exons without selecting new biology.

Internal coordinates are zero-based, half-open. Display coordinates are one-based,
inclusive. Transcript representatives are display choices, never isoform calls.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, Counter
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

from chrna.pilot_orfs import CODONS, IndexedFasta, revcomp


def project_positions(alignment):
    """Coordinate counterpart of project_arm: restore D, omit I, skip N."""
    positions = []
    r = alignment['start']
    for n, op in re.findall(r'(\d+)([MIDNSHP=X])', alignment['cigar']):
        n = int(n)
        if op in 'M=XD':
            positions.extend(range(r, r + n))
            r += n
        elif op == 'N':
            r += n
    if alignment['strand'] == '-':
        positions.reverse()
    return positions


def join_positions(left, right, gap):
    """Each base retains all locus explanations at a shared query overlap."""
    if gap < 0:
        n = -gap
        assert n <= min(len(left), len(right))
        return [[('left', p)] for p in left[:-n]] + [
            [('left', a), ('right', b)] for a, b in zip(left[-n:], right[:n])
        ] + [[('right', p)] for p in right[n:]]
    return [[('left', p)] for p in left] + [[] for _ in range(gap)] + [[('right', p)] for p in right]


def translate(sequence):
    assert len(sequence) % 3 == 0
    return ''.join(CODONS.get(sequence[i:i+3], 'X') for i in range(0, len(sequence), 3))


def read_annotation(path, genes):
    transcripts = {}
    with gzip.open(path, 'rt') as source:
        for row, line in enumerate(source, 1):
            if line.startswith('#'):
                continue
            fields = line.rstrip().split('\t')
            if fields[2] not in ('transcript', 'exon', 'CDS', 'UTR'):
                continue
            attrs = dict(re.findall(r'(\w+)\s+"?([^";]+)"?;', fields[8]))
            attrs = {k: v.strip() for k, v in attrs.items()}
            if attrs.get('gene_id') not in genes:
                continue
            tid = attrs.get('transcript_id')
            if not tid:
                continue
            tx = transcripts.setdefault(tid, dict(transcript_id=tid, gene_id=attrs['gene_id'],
                gene_name=attrs.get('gene_name'), transcript_name=attrs.get('transcript_name', tid),
                gene_type=attrs.get('gene_type'), transcript_type=attrs.get('transcript_type'),
                chromosome=fields[0], strand=fields[6], exons=[], cds=[], utr=[]))
            if fields[2] == 'transcript':
                continue
            feature = dict(start=int(fields[3])-1, end=int(fields[4]), source_row=row,
                           source_line=line.rstrip(), exon_id=attrs.get('exon_id'),
                           exon_number=int(attrs['exon_number']) if attrs.get('exon_number') else None,
                           phase=int(fields[7]) if fields[7] != '.' else None)
            tx[{'exon': 'exons', 'CDS': 'cds', 'UTR': 'utr'}[fields[2]]].append(feature)
    for tx in transcripts.values():
        for key in ('exons', 'cds', 'utr'):
            tx[key].sort(key=lambda e: e['start'], reverse=tx['strand']=='-')
    return transcripts


def feature_at(features, p):
    return next((e for e in features if e['start'] <= p < e['end']), None)


def label_position(tx, p):
    exon = feature_at(tx['exons'], p)
    if not exon:
        return None, 'non-exonic'
    if feature_at(tx['cds'], p):
        region = 'CDS'
    elif feature_at(tx['utr'], p):
        region = 'UTR'
    elif tx['gene_type'] != 'protein_coding':
        region = 'noncoding exon'
    else:
        region = 'exon outside annotated CDS'
    return exon, region


def choose_transcript(transcripts, gene_id, coding_positions, full_positions):
    candidates = []
    jumps = [(a,b) for a,b in zip(full_positions,full_positions[1:]) if abs(b-a)>1]
    for tx in transcripts.values():
        if tx['gene_id'] != gene_id:
            continue
        covered = sum(feature_at(tx['exons'], p) is not None for p in coding_positions)
        full_covered = sum(feature_at(tx['exons'], p) is not None for p in full_positions)
        boundaries = set()
        for a,b in zip(tx['exons'],tx['exons'][1:]):
            boundaries.add((a['end']-1,b['start']) if tx['strand']=='+' else (a['start'],b['end']-1))
        splice_matches = sum(pair in boundaries for pair in jumps)
        candidates.append(dict(transcript_id=tx['transcript_id'], coding_bases_exonic=covered,
                               exact_splice_jumps=splice_matches, full_arm_bases_exonic=full_covered))
    if not candidates:
        raise ValueError('No annotated transcript for '+gene_id)
    score = lambda c: (c['coding_bases_exonic'], c['exact_splice_jumps'], c['full_arm_bases_exonic'])
    candidates.sort(key=lambda c: tuple(-n for n in score(c))+(c['transcript_id'],))
    best = score(candidates[0])
    tied = [c['transcript_id'] for c in candidates if score(c)==best]
    return transcripts[candidates[0]['transcript_id']], candidates, tied


def reference_sequence(genome, chrom, strand, positions):
    """Group contiguous positions before random access to the indexed genome."""
    if not positions:
        return ''
    chunks=[]; start=0; step=1 if strand=='+' else -1
    for i in range(1,len(positions)+1):
        if i==len(positions) or positions[i]!=positions[i-1]+step:
            span=positions[start:i]
            seq=genome.fetch(chrom,min(span),max(span)+1)
            chunks.append(seq if strand=='+' else revcomp(seq))
            start=i
    return ''.join(chunks)


def codon_frame(maps, tx_by_arm):
    states=[]
    for start in range(0,len(maps),3):
        codon=maps[start:start+3]
        if any(len(x)!=1 for x in codon) or len({x[0][0] for x in codon})!=1:
            states.append('junction/shared/unmapped codon');continue
        arm=codon[0][0][0];tx=tx_by_arm[arm]
        features=[feature_at(tx['cds'],x[0][1]) for x in codon]
        if any(f is None for f in features):
            states.append('outside annotated CDS');continue
        same=True
        for i,(entry,f) in enumerate(zip(codon,features)):
            pos=entry[0][1]
            local=pos-f['start'] if tx['strand']=='+' else f['end']-1-pos
            if (local-(f['phase'] or 0))%3 != i:
                same=False
        states.append('same annotated CDS frame' if same else 'alternative CDS frame')
    return states


def summarize_record(h, rna, maps, arms, transcripts, genome, fixed_tx=None):
    begin,end=h['orf']['start'],h['orf']['stop_start']
    coding=rna[begin:end];cm=maps[begin:end]
    assert len(maps)==len(rna), (h['protein_id'],len(maps),len(rna))
    assert translate(coding)==h['sequence'], h['protein_id']
    assert hashlib.sha256(h['sequence'].encode()).hexdigest()==h['sequence_sha256']
    tx_by_arm={};tx_meta={};matches=[]
    for arm,info in arms.items():
        full=[p for entry in maps for a,p in entry if a==arm]
        pos=[p for entry in cm for a,p in entry if a==arm]
        if fixed_tx:
            tx=transcripts[fixed_tx[arm]];alternatives=[];tied=[tx['transcript_id']]
        else:
            tx,alternatives,tied=choose_transcript(transcripts,info['gene_id'],pos,full)
        assert tx['strand']==info['strand'] and tx['chromosome']==info['chromosome']
        tx_by_arm[arm]=tx
        tx_meta[arm]=dict(**info,representative_transcript=tx['transcript_id'],transcript_name=tx['transcript_name'],
                         equally_scoring_transcripts=tied,candidate_transcripts=alternatives,
                         transcript_choice='provenance control reconstruction' if fixed_tx else 'display representative; not an isoform identification')
        # Exact verification of every genomic attribution, including both overlap arms.
        mapped_seq=reference_sequence(genome,info['chromosome'],info['strand'],pos)
        expected=''.join(coding[i] for i,x in enumerate(cm) for a,p in x if a==arm)
        assert mapped_seq==expected, ('Reference mismatch', h['protein_id'],arm)
    # Preserve all transcript-specific exon assignments, not only display representatives.
    for arm,info in arms.items():
        for tx in transcripts.values():
            if tx['gene_id']!=info['gene_id']:
                continue
            for exon in tx['exons']:
                indices=[i for i,x in enumerate(cm) if any(a==arm and exon['start']<=p<exon['end'] for a,p in x)]
                if indices:
                    matches.append(dict(arm=arm,gene=info['gene_name'],gene_id=info['gene_id'],transcript_id=tx['transcript_id'],
                        chromosome=info['chromosome'],strand=info['strand'],exon_id=exon['exon_id'],exon_number=exon['exon_number'],
                        exon_start_1=exon['start']+1,exon_end_1=exon['end'],coding_nt_start_1=min(indices)+1,
                        coding_nt_end_1=max(indices)+1,coding_bases=len(indices),aa_start_1=min(indices)//3+1,
                        aa_end_1=max(indices)//3+1,source_row=exon['source_row'],source_line=exon['source_line']))
    def key(entry):
        if not entry:return ('unmapped',)
        if len(entry)>1:return ('shared junction',)
        arm,p=entry[0];exon,region=label_position(tx_by_arm[arm],p)
        return arm,(exon['exon_id'] if exon else None),region
    segments=[];start=0
    for i in range(1,len(cm)+1):
        if i<len(cm) and key(cm[i])==key(cm[start]):
            a,b=cm[i-1],cm[i]
            if len(a)==len(b)==1 and abs(a[0][1]-b[0][1])==1:continue
            if len(a)!=1:continue
        k=key(cm[start]);loci=[]
        for arm in arms:
            pp=[p for entry in cm[start:i] for a,p in entry if a==arm]
            if pp:
                ex,region=label_position(tx_by_arm[arm],pp[0])
                loci.append(dict(arm=arm,gene=arms[arm]['gene_name'],chromosome=arms[arm]['chromosome'],strand=arms[arm]['strand'],
                    start_1=min(pp)+1,end_1=max(pp)+1,exon_number=ex['exon_number'] if ex else None,
                    exon_id=ex['exon_id'] if ex else None,region=region,transcript_id=tx_by_arm[arm]['transcript_id']))
        segments.append(dict(coding_nt_start_0=start,coding_nt_end_0=i,aa_start_1=start//3+1,aa_end_1=(i-1)//3+1,
                             category=k[0],loci=loci))
        start=i
    return dict(protein_id=h['protein_id'],name=h['gene_name_5p']+' → '+h['gene_name_3p'],
        amino_acids=len(h['sequence']),sequence=h['sequence'],sequence_sha256=h['sequence_sha256'],
        read_id=h.get('read_id'),junction_id=h.get('junction_id'),source=h['sequence_source'],
        coding_rna=coding,orf=h['orf'],reference_build='GRCm39 / GENCODE M28',
        transcript_mapping=tx_meta,segments=segments,all_exon_assignments=matches,
        frame_by_residue=codon_frame(cm,tx_by_arm),frame_counts=dict(Counter(codon_frame(cm,tx_by_arm))),
        genomic_sequence_match='exact for every coding base and each alternative overlap attribution',
        protein_translation_match=True,coding_base_loci=[dict(coding_nt_1=i+1,loci=[dict(arm=a,position_1=p+1) for a,p in x]) for i,x in enumerate(cm)])


def build(root,output):
    run=root/'runs/focused-pilot-20260919'
    read=lambda p:json.loads(p.read_text())
    selected=read(run/'selection/selection.json')['selected']
    decisions={(d['junction_id'],d['read_id']):d for d in read(run/'assessment/read_decisions.json')}
    reconstructions={(d['junction_id'],d['read_id']):d for d in read(run/'orfs/reconstructions.json')}
    control=read(run/'published-control/provenance.json')
    genes={decisions[(h['junction_id'],h['read_id'])][key] for h in selected for key in ('gene_5p','gene_3p')}
    control_gene_ids={e['gene']:re.search(r'gene_id "([^"]+)"',e['source_line'])[1] for e in control['chosen_reconstruction']['exon_path']}
    genes.update(control_gene_ids.values())
    gtf=root/'data/references/gencode_M28/gencode.vM28.annotation.gtf.gz'
    transcripts=read_annotation(gtf,genes)
    genome=IndexedFasta(root/'data/references/gencode_M28/GRCm39.primary_assembly.genome.fa')
    results=[]
    for h in selected:
        d=decisions[(h['junction_id'],h['read_id'])];r=reconstructions[(h['junction_id'],h['read_id'])]
        assert not any(c['action']=='retain_high_quality_observed_substitution' for c in r['corrections_and_variants']), 'Retained variant requires explicit variant-aware verification'
        arms={arm:dict(gene_name=h['gene_name_'+suffix],gene_id=d['gene_'+suffix],chromosome=d[arm+'_alignment']['target'],
                        strand=d[arm+'_alignment']['strand'],alignment_source_row=d[arm+'_alignment']['source_line']) for arm,suffix in [('left','5p'),('right','3p')]}
        maps=join_positions(project_positions(d['left_alignment']),project_positions(d['right_alignment']),d['comparison']['query_gap'])
        results.append(summarize_record(h,r['reference_assisted_rna'],maps,arms,transcripts,genome))
    c=control['chosen_reconstruction'];maps=[];arms={}
    for e in c['exon_path']:
        arm='left' if e['gene']=='Gsdmd' else 'right'
        positions=list(range(e['start'],e['end']))
        if e['strand']=='-':positions.reverse()
        maps.extend([[(arm,p)] for p in positions])
        arms[arm]=dict(gene_name=e['gene'],gene_id=control_gene_ids[e['gene']],chromosome=e['chromosome'],strand=e['strand'])
    h=dict(protein_id='protein_'+control['protein_sha256'],sequence_sha256=control['protein_sha256'],sequence=c['protein'],
           gene_name_5p='Gsdmd',gene_name_3p='Tmem106a',orf=c['orf'],sequence_source='separate published-architecture reference control')
    out=summarize_record(h,c['rna'],maps,arms,transcripts,genome,dict(zip(['left','right'],c['parent_transcripts'])))
    out['equivalent_control_transcript_combinations']=control['equivalent_parent_transcript_combinations'];results.append(out)
    output.mkdir(parents=True,exist_ok=True)
    sources=[gtf,run/'selection/selection.json',run/'orfs/reconstructions.json',run/'assessment/read_decisions.json',run/'published-control/provenance.json']
    audit=dict(created_utc=datetime.now(timezone.utc).isoformat(),status='verified',records=len(results),
        sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        method='Project frozen reconstructed coding RNA through original CIGARs; retain overlap alternatives; intersect GTF exons and CDS; verify exact genomic bases and translation.',
        transcript_policy='Maximize coding exon coverage, exact splice jumps, full-arm exon coverage, then transcript ID. Representative only; all overlaps exported.',
        coordinates='JSON base maps and TSV: 1-based inclusive; segment coding_nt_*_0: 0-based half-open; aa ranges may overlap at split codons.',
        limitations=['Not independent confirmation of the reference-assisted sequences.', 'No unique parental isoform claim.',
                     'Exon source does not imply the parental CDS frame or protein function.', 'All ten recovered hypotheses have one supporting read; control is separate.'])
    (output/'mapping.json').write_text(json.dumps(dict(audit=audit,proteins=results),indent=2)+'\n')
    rows=[dict(protein_id=r['protein_id'],pair=r['name'],**e) for r in results for e in r['all_exon_assignments']]
    with (output/'all_transcript_exon_assignments.tsv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
    print(json.dumps(dict(status='verified',proteins=len(results),exon_assignments=len(rows),output=str(output))))
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--output',type=Path,default=Path('reports/exon_atlas'))
    a=p.parse_args();build(a.root.resolve(),a.output.resolve())


if __name__=='__main__':main()
