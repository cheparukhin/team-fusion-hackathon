"""All supported human junctions, independently assessed by library."""
from pathlib import Path
import collections, hashlib, json, sys
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from chrna.pilot_orfs import run
from chrna.pilot_selection import select, near_identical
BASE=ROOT/'runs/k562-all-junctions-20260920'
OLD=ROOT/'runs/k562-pilot/20260919-overnight/outputs'
NAMES=['SGNex_K562_directRNA_replicate4_run1','SGNex_K562_directRNA_replicate5_run1']
def load(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 BASE.mkdir(exist_ok=False)
 ranks=[[r for r in load(OLD/n/'assessment/rna_ranking.json') if r['evidence_state']=='supported_two_gene_junction'] for n in NAMES]
 ids=sorted({r['junction_id'] for rs in ranks for r in rs})
 assert list(map(len,ranks))==[220,199] and len(ids)==414
 inputs=[OLD/n/'assessment'/f for n in NAMES for f in ['rna_ranking.json','read_decisions.json']]
 save(BASE/'scope-freeze.json',{'utc':datetime.now(timezone.utc).isoformat(),'junction_ids':ids,'library_counts':[220,199],'selection':'All supported junctions; per-library reconstruction and ORF eligibility; no second-library or short-read gate','structure_batch_rule':'At most ten distinct eligible sequences, interleaved A/B by frozen per-library selected order, deduplicated at <=5% edit distance. Remaining eligible proteins deferred by batch cap.','inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'reconstruction_code_sha256':hashlib.sha256((ROOT/'src/chrna/pilot_orfs.py').read_bytes()).hexdigest(),'selection_code_sha256':hashlib.sha256((ROOT/'src/chrna/pilot_selection.py').read_bytes()).hexdigest()})
 (BASE/'reference').mkdir();(BASE/'reference/genome.fa').symlink_to(ROOT/'runs/k562-extension-20260920/reference/genome.fa');(BASE/'reference/genome.fa.fai').symlink_to(ROOT/'runs/k562-extension-20260920/reference/genome.fa.fai')
 recs=[];hs=[];ds=[];selections=[];summary=[]
 for lib,name,rr in zip('AB',NAMES,ranks):
  dest=BASE/lib;wanted={r['junction_id'] for r in rr};dd=[d for d in load(OLD/name/'assessment/read_decisions.json') if d['junction_id'] in wanted]
  save(dest/'assessment/rna_ranking.json',rr);save(dest/'assessment/read_decisions.json',dd)
  result=run(dest/'assessment',OLD/name/'discovery/split_reads.fastq',BASE/'reference/genome.fa',dest/'orfs',len(rr))
  rc=load(dest/'orfs/reconstructions.json');hh=load(dest/'orfs/protein_hypotheses.json')
  assert len(rc)==sum(r['distinct_qualifying_reads'] for r in rr)
  for records in [rc,hh,dd]:
   for r in records:r.update(library=lib,sample_alias=name)
  selection=select(rr,rc,hh);save(dest/'selection.json',selection);selections.append(selection)
  recs+=rc;hs+=hh;ds+=dd
  for row in rr:
   rs=[r for r in rc if r['junction_id']==row['junction_id']];decision=next(d for d in selection['decisions'] if d['junction_id']==row['junction_id'])
   summary.append({'library':lib,'junction_id':row['junction_id'],'pair':rs[0]['gene_name_5p']+':'+rs[0]['gene_name_3p'],'qualifying_reads_reconstructed':len(rs),'observed_complete_spanning_ORF_reads':sum(bool(r['observed_orfs']) for r in rs),'reference_assisted_complete_spanning_ORF_reads':sum(bool(r['reference_assisted_orfs']) for r in rs),'sequence_resolved_reads':sum(not r['unresolved_sequence_reasons'] for r in rs),'unresolved_reasons':dict(collections.Counter(v['reason'] for r in rs for v in r['unresolved_sequence_reasons'])),'folding_status':decision['status'],'folding_reasons':decision['reasons'],'primary_protein_hypotheses':len(decision['primary_sequence_ids'])})
  print(lib,json.dumps(result),'selected',len(selection['selected']),flush=True)
 selected=[]
 for i in range(10):
  for lib,s in zip('AB',selections):
   if i>=len(s['selected']):continue
   h=s['selected'][i]
   if len(selected)<10 and not any(near_identical(h['sequence'],p['sequence']) for p in selected):selected.append({**h,'library':lib,'selection_order':len(selected)+1})
 for name,records in [('reconstructions',recs),('protein_hypotheses',hs),('read_decisions',ds),('reconstruction-summary',summary)]:save(BASE/(name+'.json'),records)
 save(BASE/'selection.json',{'selected':selected,'library_decisions':{lib:s['decisions'] for lib,s in zip('AB',selections)},'scope':'Library-specific eligibility; no cross-library agreement requirement'})
 (BASE/'selected_proteins.fasta').write_text(''.join('>'+h['protein_id']+' library='+h['library']+' junction='+h['junction_id']+'\n'+h['sequence']+'\n' for h in selected))
 save(BASE/'selection-freeze.json',{'utc':datetime.now(timezone.utc).isoformat(),'frozen':True,'selected':len(selected),'inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'scope-freeze.json',BASE/'selection.json',BASE/'reconstructions.json',BASE/'protein_hypotheses.json']}})
 print('TOTAL',len(recs),'hypotheses',len(hs),'selected',[(h['gene_name_5p'],h['gene_name_3p'],len(h['sequence'])) for h in selected],flush=True)
if __name__=='__main__':main()
