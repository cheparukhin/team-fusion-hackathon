"""Read-only adaptation of frozen K562 evidence for a linked RNA dashboard."""
from pathlib import Path
import csv,gzip,hashlib,json,re,collections
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'runs/k562-pilot/20260919-overnight';OUT=RUN/'outputs';DEST=ROOT/'runs/k562-all-junctions-20260920'
NAMES=['SGNex_K562_directRNA_replicate4_run1','SGNex_K562_directRNA_replicate5_run1']
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def attrs(s):return dict(re.findall(r'(\w+)\s+"?([^";]+)"?\s*;',s))
def overlap(blocks,a,b):return sum(max(0,min(y,b)-max(x,a)) for x,y in blocks)
def main():
 rankings=[load(OUT/n/'assessment/rna_ranking.json') for n in NAMES]
 ids=set(r['junction_id'] for r in rankings[0] if r['evidence_state']=='supported_two_gene_junction')|set(r['junction_id'] for r in rankings[1] if r['evidence_state']=='supported_two_gene_junction')
 decisions=[[d for d in load(OUT/n/'assessment/read_decisions.json') if d['junction_id'] in ids] for n in NAMES]
 genes={d[k] for ds in decisions for d in ds for k in ['gene_5p','gene_3p']}
 gtf=ROOT/'reports/k562-dashboard/gencode.v43.annotation.gtf.gz';ref=load(OUT/'provenance/gencode.v43.annotation.gtf.gz.json');assert sha(gtf)==ref['sha256']
 transcripts=collections.defaultdict(dict);plain=hashlib.sha256()
 with gzip.open(gtf,'rb') as stream:
  for raw in stream:
   plain.update(raw)
   if raw.startswith(b'#'):continue
   f=raw.decode().rstrip().split('\t')
   if f[2]!='exon':continue
   a=attrs(f[8]);gid=a.get('gene_id')
   if gid not in genes:continue
   tid=a['transcript_id'];tx=transcripts[gid].setdefault(tid,{'id':tid,'exons':[]})
   tx['exons'].append({'n':int(a['exon_number']),'start':int(f[3])-1,'end':int(f[4]),'strand':f[6]})
 assert plain.hexdigest()==load(OUT/'reference_audit.json')['annotation_sha256']
 for ts in transcripts.values():
  for t in ts.values():t['exons'].sort(key=lambda e:e['n'])
 rows={r['junction_id']:r for r in csv.DictReader((OUT/'primary_candidates.tsv').open(),delimiter='\t')};candidates=[]
 for jid in sorted(ids,key=lambda j:(min(r['display_rank'] for rs in rankings for r in rs if r['junction_id']==j),j)):
  sample=next(d for ds in decisions for d in ds if d['junction_id']==jid)
  rna=[]
  for lib,ds in enumerate(decisions):
   for d in ds:
    if d['junction_id']!=jid:continue
    arms=[]
    for side,genek,namek in [('left_alignment','gene_5p','gene_name_5p'),('right_alignment','gene_3p','gene_name_3p')]:
     a=d[side];txs=[]
     for t in transcripts[d[genek]].values():
      ex=[{**e,'overlap':overlap(a['blocks'],e['start'],e['end'])} for e in t['exons']]
      score=sum(e['overlap'] for e in ex)
      if score:txs.append({'id':t['id'],'overlap':score,'exons':[e for e in ex if e['overlap']]})
     txs.sort(key=lambda t:(-t['overlap'],t['id']))
     arms.append({**{k:a[k] for k in ['target','strand','start','end','qstart','qend','length','mapq','cigar','blocks','source_line']},'gene':d[namek],'gene_id':d[genek],'transcripts':txs})
    rna.append({'id':d['read_id'],'library':'AB'[lib],'state':d['state'],'reasons':d['reasons'],'arms':arms,'comparison':d['comparison'],'caller_pairs':d['longgf_pairs_for_read']})
  supports=[next((r for r in rs if r['junction_id']==jid),{'distinct_qualifying_reads':0,'display_rank':None}) for rs in rankings]
  assert [len({r['id'] for r in rna if r['library']==lib and r['state']=='supported_two_gene_junction'}) for lib in 'AB']==[r['distinct_qualifying_reads'] for r in supports]
  candidates.append({'id':jid,'pair':sample['gene_name_5p']+' → '+sample['gene_name_3p'],'coordinates':{k:sample[k] for k in ['reference_build','gene_5p','gene_3p','chromosome_5p','chromosome_3p','boundary_5p','boundary_3p','strand_5p','strand_3p']},'support':[r['distinct_qualifying_reads'] for r in supports],'rank':[r['display_rank'] for r in supports],'illumina':int(rows[jid]['Illumina_fragment_ids']) if jid in rows else None,'geometry':int(rows[jid]['Illumina_distinct_geometries']) if jid in rows else None,'reads':rna,'control':sample['gene_name_5p']=='BCR' and sample['gene_name_3p']=='ABL1'})
 data={'candidates':candidates,'summary':load(OUT/'corroboration.json'),'cost':load(RUN/'resource-accounting.json'),'scope':'All 414 distinct supported junctions; 220 in A and 199 in B; no corroboration gate','reference_sha256':plain.hexdigest()}
 (DEST/'data.json').write_text(json.dumps(data,indent=2)+'\n')
 sources=[OUT/'corroboration.json',OUT/'primary_candidates.tsv',OUT/'reference_audit.json']+[OUT/n/'assessment'/f for n in NAMES for f in ['rna_ranking.json','read_decisions.json']]
 (DEST/'provenance.json').write_text(json.dumps({'read_only':True,'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sources},'scope':data['scope'],'annotation_source':ref,'coordinate_system':'0-based half-open intervals; exon labels are transcript-specific','transcript_choice':'Sorted by overlap with M/= /X aligned reference blocks, ties by ID; not isoform inference','protein_reconstruction':'NOT_PERFORMED','structure_prediction':'NOT_PERFORMED'},indent=2)+'\n')
 print(json.dumps({'data':str(DEST/'data.json'),'candidates':len(candidates),'reads':sum(len(c['reads']) for c in candidates)}))
if __name__=='__main__':main()
