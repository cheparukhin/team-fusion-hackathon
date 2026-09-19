"""Build auditable, transcript-specific diagram inputs from exact probe mappings."""
import csv,gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'results/dataset_reconstruction'
def rows(p):
 with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
pairs=['Gsdmd:Tmem106a','Cd274:Lacc1','Psap:Lgals3']
mappings=[r for r in rows(DATA/'probe_sequence_mapping.tsv') if r['pair_id'] in pairs]
transcripts={r['transcript_id'] for r in mappings}
exons={t:[] for t in transcripts}
gtf=ROOT/'data/reference/gencode.vM28.annotation.gtf.gz'
with gzip.open(gtf,'rt') as f:
 for line in f:
  if line.startswith('#'):continue
  parts=line.rstrip('\n').split('\t')
  if len(parts)!=9 or parts[2]!='exon':continue
  a={k:v.strip('"') for k,v in (field.strip().split(' ',1) for field in parts[8].split(';') if field.strip())}
  t=a.get('transcript_id')
  if t in exons:exons[t].append({'exon_number':int(a['exon_number']),'start':int(parts[3]),'end':int(parts[4]),'strand':parts[6]})
for t in exons:exons[t].sort(key=lambda x:x['exon_number'])
pred={r['pair_id']:r for r in rows(ROOT/'results/classifier/predictions.tsv')}
probes=[r for r in rows(DATA/'probe_junctions.tsv') if r['pair_id'] in pairs]
out={'assembly':'GRCm39','annotation':'GENCODE M28','coordinate_convention':'1-based inclusive terminal retained parent bases','colors':{'parent_a':'#0000FF','parent_b':'#D22D27'},'selection':'Two traceable paper examples and one high-scoring not-reported-supported contrast; not a top-ranked discovery list.','candidates':[]}
for pair in pairs:
 p=pred[pair]
 c={'pair_id':pair,'reported_nanostring_support':int(p['label'])==1,'unique_long_reads':int(p['long_read_support']),'score_rna':float(p['score_rna']),'score_hic':float(p['score_hic']) if p['score_hic'] else None,'probe_examples':[],'protein_claim':'No validated protein ORF is assigned by this diagram.'}
 if pair=='Gsdmd:Tmem106a':c['protein_claim']='Paper Fig3a:118aa;residues1–73GSDMD-derived;74–118novel out-of-frame TMEM106A-derived tail. Structural rendering in paper is AlphaFold3 prediction,not experimental structure.'
 for probe in sorted((r for r in probes if r['pair_id']==pair),key=lambda r:r['probe_id']):
  item={'probe_id':probe['probe_id'],'sequence':probe['sequence'],'sides':{}}
  for side in ['a','b']:
   alternatives=[]
   for m in sorted((m for m in mappings if m['probe_id']==probe['probe_id'] and m['side']==side),key=lambda m:m['transcript_id']):
    bp=int(m['breakpoint']); ee=exons[m['transcript_id']]
    hit=[e for e in ee if e['start']<=bp<=e['end']]
    assert len(hit)==1,(m,hit)
    e=hit[0]; n=e['exon_number']
    itemside={'transcript_id':m['transcript_id'],'gene_id':m['gene_id'],'chromosome':m['chrom'],'strand':m['strand'],'breakpoint':bp,'junction_exon':n,'exons':ee,'retained_exon_numbers':[v['exon_number'] for v in ee if (v['exon_number']<=n if side=='a' else v['exon_number']>=n)]}
    alternatives.append(itemside)
   assert alternatives
   item['sides'][side]={'representative':alternatives[0],'alternative_transcripts':alternatives,'selection_rule':'Lexicographically first exact60nt-matched transcript; representative annotation,not an isoform uniquely validated by the probe.'}
  c['probe_examples'].append(item)
 out['candidates'].append(c)
files=[DATA/'probe_sequence_mapping.tsv',DATA/'probe_junctions.tsv',ROOT/'results/classifier/predictions.tsv',gtf]
out['input_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
p=ROOT/'results/presentation/candidate_examples.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2)+'\n')
for c in out['candidates']:
 print(c['pair_id'],[(p['probe_id'],[(s,x['representative']['transcript_id'],x['representative']['junction_exon'],x['representative']['breakpoint']) for s,x in p['sides'].items()]) for p in c['probe_examples']])
