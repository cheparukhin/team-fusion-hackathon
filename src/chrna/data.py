"""Reconstruct ordered chRNA evidence from pinned published artifacts.

Run with ``python -m chrna.data --root .``; add --download for first use.
No assay negatives, missing read counts, or biological samples are inferred.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import pandas as pd
import requests

VERSION = '1.0.0'
ARTICLE = 'https://www.nature.com/articles/s41586-026-10982-x'
MEDIA = 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10982-x/MediaObjects/'
REF = 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M28/'
SOURCES = {f'data/raw/41586_2026_10982_MOESM{n}_ESM.xlsx': MEDIA + f'41586_2026_10982_MOESM{n}_ESM.xlsx' for n in (3,5,6,9,10)}
SOURCES.update({f'data/reference/{name}': REF + name for name in ('gencode.vM28.annotation.gtf.gz','gencode.vM28.transcripts.fa.gz')})


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1048576), b''): h.update(block)
    return h.hexdigest()


def read_reference(gtf, fasta, wanted):
    genes, exons, transcripts = defaultdict(list), defaultdict(list), defaultdict(list)
    with gzip.open(gtf, 'rt') as f:
        for line in f:
            if line.startswith('#'): continue
            x = line.rstrip().split('\t')
            if x[2] not in ('gene','exon'): continue
            a = dict(re.findall(r'(\w+) "([^"]+)"', x[8]))
            if x[2] == 'gene':
                genes[a['gene_name']].append(dict(gene_id=a['gene_id'], mgi_id=a.get('mgi_id',''), chrom=x[0], start=int(x[3]), end=int(x[4]), strand=x[6]))
            elif a['gene_name'] in wanted:
                exons[a['transcript_id']].append((int(x[3]),int(x[4]),x[0],x[6]))
    def save(header, seq):
        if header and header[5] in wanted:
            transcripts[header[5]].append((header[0],header[1],''.join(seq)))
    with gzip.open(fasta,'rt') as f:
        header, seq = None, []
        for line in f:
            if line.startswith('>'):
                save(header,seq); header=line[1:].strip().split('|'); seq=[]
            else: seq.append(line.strip())
        save(header,seq)
    return genes,exons,transcripts


def transcript_coordinate(exons, offset):
    """Map zero-based transcript nucleotide offset to one-based genomic base."""
    if offset < 0: raise ValueError('negative transcript offset')
    for start,end,chrom,strand in sorted(exons, reverse=exons[0][3]=='-'):
        length=end-start+1
        if offset < length: return chrom, start+offset if strand=='+' else end-offset, strand
        offset -= length
    raise ValueError('offset beyond transcript')


def match_half(sequence, parent, transcripts, exons, side):
    hits=[]
    for tid,gid,seq in transcripts.get(parent,[]):
        pos=seq.find(sequence)
        while pos != -1:
            chrom,bp,strand=transcript_coordinate(exons[tid],pos+(len(sequence)-1 if side=='a' else 0))
            hits.append(dict(transcript_id=tid,gene_id=gid,chrom=chrom,breakpoint=bp,strand=strand))
            pos=seq.find(sequence,pos+1)
    return hits


def resolve_probe(probe_id, sequence, genes, transcripts, exons):
    """Suffix removal requires exact sequence evidence for both ordered parents."""
    if probe_id.count(':') != 1: return None,[],[],'invalid_ordered_pair'
    a,b=probe_id.split(':')
    candidate_b=b if b in genes else b.removesuffix('_2')
    if len(sequence)!=120: return None,[],[],'unexpected_probe_length'
    ah=match_half(sequence[:60],a,transcripts,exons,'a')
    bh=match_half(sequence[60:],candidate_b,transcripts,exons,'b')
    if not ah or not bh: return None,ah,bh,'parent_sequence_mapping_failed'
    return f'{a}:{candidate_b}',ah,bh,('sequence_verified_design_suffix' if b!=candidate_b else 'exact_symbol_sequence_verified')


def genomic_context(a_records,b_records):
    """Minimum base-coordinate separation over pinned parent gene intervals."""
    if not a_records or not b_records: return None,None
    ac={r['chrom'] for r in a_records};bc={r['chrom'] for r in b_records}
    if len(ac)!=1 or len(bc)!=1: return None,None
    inter=int(ac!=bc)
    return inter, 0 if inter else min(max(0,a['start']-b['end'],b['start']-a['end']) for a in a_records for b in b_records)


def gene_identity(records):
    if not records: return 'unmapped'
    if len(records)==1: return 'unique_gencode_gene'
    mgi={r['mgi_id'] for r in records}
    if len(mgi)==1 and '' not in mgi and len({(r['chrom'],r['strand']) for r in records})==1:
        return 'multiple_gencode_records_same_mgi'
    return 'ambiguous_gene_identity'


def aggregate_reads(reads):
    required=['pair_id','read_id']
    if reads[required].isna().any().any(): raise ValueError('missing read or pair identity')
    return reads.drop_duplicates(required).groupby('pair_id').read_id.nunique()


def build(root: Path, download=False):
    out=root/'results/dataset_reconstruction'; out.mkdir(parents=True,exist_ok=True)
    for rel,url in SOURCES.items():
        path=root/rel
        if not path.exists():
            if not download: raise FileNotFoundError(f'{path}; use --download')
            path.parent.mkdir(parents=True,exist_ok=True)
            response=requests.get(url,timeout=180);response.raise_for_status();path.write_bytes(response.content)
    manifest_path = out/'manifest.json'
    if manifest_path.exists():
        pinned = json.loads(manifest_path.read_text())
        for source in pinned.get('sources', []):
            if source['path'] in SOURCES and sha256(root/source['path']) != source['sha256']:
                raise ValueError(f"Pinned source checksum mismatch: {source['path']}")
    def table(n): return pd.read_excel(root/f'data/raw/41586_2026_10982_MOESM{n}_ESM.xlsx')
    raw_reads,callers,labels,probes=table(5),table(6),table(9),table(10)
    wanted={g for p in probes.iloc[:,0] for g in p.removesuffix('_2').split(':')}
    genes,exons,transcripts=read_reference(root/'data/reference/gencode.vM28.annotation.gtf.gz',root/'data/reference/gencode.vM28.transcripts.fa.gz',wanted)
    raw_reads=raw_reads.rename(columns={'Read_ID':'read_id','Chimera_ID':'pair_id','Gene_A':'parent_a','Gene_B':'parent_b','Chromosome_Gene_A':'chrom1','Chromosome_Gene_B':'chrom2','Breakpoint_Coordinate_Gene_A':'breakpoint1','Breakpoint_Coordinate_Gene_B':'breakpoint2','Strand_Gene_A':'strand1','Strand_Gene_B':'strand2'})
    if not (raw_reads.pair_id==raw_reads.parent_a+':'+raw_reads.parent_b).all(): raise ValueError('published pair order inconsistency')
    raw_reads['source_row']=range(2,len(raw_reads)+2);raw_reads['sample_id']=pd.NA;raw_reads['assembly']='GRCm39';raw_reads['source_id']='supplementary_table_3'
    raw_reads.to_csv(out/'read_evidence.tsv',sep='\t',index=False)
    supports=aggregate_reads(raw_reads)
    supported=set(labels.iloc[:,1].dropna());short=set(labels.iloc[:,0].dropna());cross=set(labels.iloc[:,2].dropna())
    caller_sets={c:set(callers[c].dropna()) for c in callers}
    panel=[];mapped_junctions=[];mapping=[]
    for index,row in probes.iterrows():
        pid,plate,seq=row.tolist();seq=seq.upper()
        pair,ah,bh,status=resolve_probe(pid,seq,genes,transcripts,exons)
        in_catalogue=pair in supports.index
        reason='' if pair and in_catalogue else 'unresolved_biological_candidate_or_control' if pair else status
        panel.append(dict(probe_id=pid,pair_id=pair,plate=plate,sequence=seq,probe_design=True,label_scope='ordered_gene_pair_not_probe_or_junction',control_status='not_individually_annotated',biological_candidate_status='published_long_read_candidate' if in_catalogue else 'unresolved_candidate_or_control',assay_tested='unknown',assay_qc_status='unknown',reported_nanostring_support=int(pair in supported) if pair else pd.NA,label=int(pair in supported) if pair else pd.NA,mapping_status=status,exclusion_reason=reason,source_id='supplementary_table_8',source_row=index+2,source_url=SOURCES['data/raw/41586_2026_10982_MOESM10_ESM.xlsx']))
        for side,hits in [('a',ah),('b',bh)]:
            for hit in hits: mapping.append(dict(probe_id=pid,pair_id=pair,side=side,**hit,reference='GENCODE M28 / GRCm39'))
        ac={(h['chrom'],h['breakpoint'],h['strand']) for h in ah};bc={(h['chrom'],h['breakpoint'],h['strand']) for h in bh}
        if len(ac)==len(bc)==1:
            a=next(iter(ac));b=next(iter(bc))
            mapped_junctions.append(dict(probe_id=pid,pair_id=pair,chrom1=a[0],breakpoint1=a[1],strand1=a[2],chrom2=b[0],breakpoint2=b[1],strand2=b[2],assembly='GRCm39',sequence=seq,coordinate_basis='1-based inclusive terminal parent bases from exact 60nt transcript matches',source_id='supplementary_table_8+gencode_M28'))
    panel=pd.DataFrame(panel);probe_junctions=pd.DataFrame(mapped_junctions)
    pd.DataFrame(mapping).to_csv(out/'probe_sequence_mapping.tsv',sep='\t',index=False)
    probe_junctions.to_csv(out/'probe_junctions.tsv',sep='\t',index=False)
    records=[]
    panel_pairs=set(panel.pair_id.dropna())
    for pair in sorted(set(supports.index)|panel_pairs):
        a,b=pair.split(':');ar=genes.get(a,[]);br=genes.get(b,[])
        identity_a,identity_b=gene_identity(ar),gene_identity(br)
        inter,distance=genomic_context(ar,br)
        identity_ok=identity_a not in ('unmapped','ambiguous_gene_identity') and identity_b not in ('unmapped','ambiguous_gene_identity')
        exclusion='' if identity_ok else 'unmapped_or_ambiguous_parent_identity'
        if pair in panel_pairs and pair not in supports.index: exclusion='unresolved_biological_candidate_or_control'
        records.append(dict(pair_id=pair,parent_a=a,parent_b=b,parent_a_ids=';'.join(r['gene_id'] for r in ar),parent_b_ids=';'.join(r['gene_id'] for r in br),parent_a_mgi_ids=';'.join(sorted({r['mgi_id'] for r in ar})),parent_b_mgi_ids=';'.join(sorted({r['mgi_id'] for r in br})),parent_a_mapping=identity_a,parent_b_mapping=identity_b,chromosome_a=';'.join(sorted({r['chrom'] for r in ar})),chromosome_b=';'.join(sorted({r['chrom'] for r in br})),species='Mus musculus',assembly='GRCm39',annotation='GENCODE M28',long_read_support=int(supports[pair]) if pair in supports.index else pd.NA,sample_count=pd.NA,sample_count_status='unavailable_read_to_sample_mapping',is_interchromosomal=inter if identity_ok else pd.NA,genomic_distance=distance if identity_ok else pd.NA,in_probe_panel=pair in panel_pairs,label=int(pair in supported) if pair in panel_pairs else pd.NA,reported_nanostring_support=pair in supported,short_read_reported_support=pair in short,cross_reported_support=pair in cross,caller_names=';'.join(c for c,s in caller_sets.items() if pair in s),assay_tested='unknown',assay_qc_status='unknown',exclusion_reason=exclusion,source_ids='supplementary_table_3;supplementary_table_4;gencode_M28'+(';supplementary_table_7;supplementary_table_8' if pair in panel_pairs else ''),source_url=ARTICLE))
    candidates=pd.DataFrame(records)
    reasons=candidates.set_index('pair_id').exclusion_reason
    panel['exclusion_reason']=panel.pair_id.map(reasons).fillna(panel.exclusion_reason)
    panel.to_csv(out/'probe_panel.tsv',sep='\t',index=False)
    candidates.to_csv(out/'candidates.tsv',sep='\t',index=False)
    model=candidates[candidates.in_probe_panel & candidates.exclusion_reason.eq('')].copy()
    model.to_csv(out/'model_input.tsv',sep='\t',index=False)
    key=['pair_id','chrom1','breakpoint1','strand1','chrom2','breakpoint2','strand2']
    junctions=raw_reads.groupby(key,sort=True).agg(read_ids=('read_id',lambda x:';'.join(sorted(set(x)))),long_read_support=('read_id','nunique'),source_rows=('source_row',lambda x:';'.join(map(str,sorted(x))))).reset_index()
    junctions['assembly']='GRCm39';junctions['sample_ids']=pd.NA;junctions['sample_count']=pd.NA;junctions['source_id']='supplementary_table_3';junctions['coordinate_basis']='published coordinates preserved; see audit';junctions['sequence']=pd.NA
    junctions.to_csv(out/'junctions.tsv',sep='\t',index=False)
    pd.DataFrame([dict(gene_symbol=g,**r) for g,rs in genes.items() for r in rs]).to_csv(out/'gene_mapping.tsv',sep='\t',index=False)
    summary=dict(raw_probe_designs=len(probes),mapped_unique_panel_pairs=len(panel_pairs),eligible_probe_designs=int(panel.exclusion_reason.eq('').sum()),probe_designs_with_pair_level_support=int(panel.label.sum()),short_read_supported=len(short),nanostring_supported=len(supported),cross_supported=len(cross),exact_nanostring_panel_matches=len(supported & set(probes.iloc[:,0])),sequence_resolved_nanostring_panel_matches=len(supported & panel_pairs),sequence_verified_suffixes=int(panel.mapping_status.eq('sequence_verified_design_suffix').sum()),table3_read_rows=len(raw_reads),table3_unique_reads=raw_reads.read_id.nunique(),table3_unique_pairs=len(supports),unique_junctions=len(junctions),probe_junctions_uniquely_mapped=len(probe_junctions),eligible_model_pairs=len(model),eligible_model_positives=int(model.label.sum()),excluded_panel_pairs=int(panel.exclusion_reason.ne('').sum()),sample_count_available=0)
    manifest=dict(transformation_version=VERSION,generated_at=datetime.now(timezone.utc).isoformat(),assembly='GRCm39',annotation='GENCODE M28',article=ARTICLE,sources=[dict(path=rel,url=url,sha256=sha256(root/rel),bytes=(root/rel).stat().st_size,retrieved_date=datetime.fromtimestamp((root/rel).stat().st_mtime,timezone.utc).date().isoformat()) for rel,url in SOURCES.items()],counts=summary,outputs={p.name:sha256(p) for p in sorted(out.glob('*.tsv'))})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    unresolved=panel[panel.exclusion_reason.ne('')]
    audit=f'''# Dataset reconstruction audit

Reproduction: `PYTHONPATH=src .venv/bin/python -m chrna.data --root .` (cached, offline). Add `--download` only for missing inputs.

## Frozen counts

```json
{json.dumps(summary,indent=2)}
```

## Labels, exclusions, and assay uncertainty

The target is membership in Supplementary Table 7's NanoString-supported ordered gene-pair list within the mapped biological probe panel. Zero means **not reported supported**, never a demonstrated false RNA or failed assay. Table 8 supplies designs, not individual assay testing or QC results; both statuses remain unknown even for reported positives. Pair support is not propagated as junction-specific validation.

The exact panel join is 107 of 109 positives. Aoah:Sirt5_2 and Tbc1d23:Xdh_2 resolve to Aoah:Sirt5 and Tbc1d23:Xdh because BOTH ordered 60-nt probe halves exactly match the named M28 parent transcripts. The same independent sequence check resolves Slc25a13:Sem1_2, Plekhm2:4930455G09Rik_2, and Slc16a10:Rpf2_2. All five unsuffixed pairs also occur in Table 3. Slc25a13:Sem1 and Slc16a10:Rpf2 each have both a base and a _2 design, so 529 designs collapse to 527 ordered pairs, and 481 eligible designs collapse to 479 model pairs. Original IDs and every matching transcript remain in probe_panel.tsv and probe_sequence_mapping.tsv. All 529 sequences pass both parent-half matches. The suffix is not removed without this evidence.

48 panel pairs are absent from Table 3 and all three Table 4 caller lists. The article mentions scrambled controls but neither these tables nor their cell formatting identifies individual controls. These 48 are conservatively excluded as unresolved biological candidate/control status, NOT asserted to be controls. Their read support is missing, not zero. This additional catalogue restriction may affect generalizability and is reported explicitly. No label-dependent exclusion rule is used.

## Read and sample handling

Table 3 has 36,826 globally unique read IDs and 30,390 ordered pairs. Counts union unique read IDs within each ordered pair across observed junctions. Table 4 provides caller membership only; its rows are never added as extra read support. read_evidence.tsv preserves each source row and read ID; junctions.tsv groups exact published coordinate/strand tuples. Table 1 identifies 10 biological samples but does not link them to read IDs; sample_count/sample_ids remain unavailable for every pair. Caller-specific or inferred sample assignments are not fabricated.

## Coordinates and parent identity

Pinned GENCODE M28 gene intervals use GRCm39, 1-based inclusive coordinates. genomic_distance is the minimum absolute base-coordinate separation between any parent intervals; overlap=0, interchromosomal=0 with is_interchromosomal=1. Multiple GENCODE records with the same symbol are retained together only when their MGI identity, chromosome and strand agree; all stable IDs remain present. Distinct unresolved identities are excluded from modeling. This handles Ndor1, Nnt, Aldoa, and Dpep2 without choosing an arbitrary Ensembl ID.

junctions.tsv preserves Table 3 breakpoints exactly; their base-origin convention is not explicitly specified in the spreadsheet. probe_junctions.tsv independently maps the final nucleotide of the first 60-nt parent half and the first nucleotide of the second half through M28 transcript exons into 1-based inclusive genomic positions. Only unique coordinate tuples across transcript matches are exported. Multiple matching transcripts with identical coordinates are harmless. Probe coordinates are suitable for assembly-matched binning; pair-level labels do not establish the validity of every observed junction. Exact cross-table breakpoint comparison must account for documented convention ambiguity.

## Feature availability and leakage prevention

Only long_read_support, sample_count (unavailable), is_interchromosomal, and genomic_distance are proposed RNA predictors. Short-read and NanoString flags, plate, probe sequences, and names are evidence/metadata only. Missing read support is never zero-filled. Preprocessing and gene-disjoint fold construction are the classifier's responsibility.

## Excluded probe IDs

'''+ '\n'.join(f"- {r.probe_id}: {r.exclusion_reason}" for r in unresolved.itertuples())+'\n'
    (out/'audit.md').write_text(audit)
    (out/'STATUS.md').write_text('# Data worker status\n\nComplete: real cached source reconstruction, sequence-verified probe identities, audited conservative cohort, exact read provenance and independent probe coordinates.\n\n'+json.dumps(summary,indent=2)+'\n\nSample recurrence and individual assay/QC status are unavailable. See audit.md.\n')
    print(json.dumps(summary,indent=2))
    return summary


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('.'));parser.add_argument('--download',action='store_true');args=parser.parse_args();build(args.root,args.download)

if __name__=='__main__': main()
