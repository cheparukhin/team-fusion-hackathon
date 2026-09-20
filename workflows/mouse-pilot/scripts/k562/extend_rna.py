"""Exploratory follow-up of five shared junctions; frozen discovery remains unchanged."""
from pathlib import Path
import collections,copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from chrna.pilot_orfs import run as reconstruct_run
from chrna.pilot_selection import select
BASE=ROOT/'runs/k562-extension-20260920';ORIGINAL=ROOT/'runs/k562-pilot/20260919-overnight/outputs'
NAMES=['SGNex_K562_directRNA_replicate4_run1','SGNex_K562_directRNA_replicate5_run1']
def load(p):return json.loads(p.read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 scope=load(BASE/'scope-freeze.json');wanted=set(scope['junction_ids']);recons=[];hypotheses=[];ranks=[];all_dec=[]
 for lib,name in zip('AB',NAMES):
  src=ORIGINAL/name;dest=BASE/lib;assess=dest/'assessment';assess.mkdir(parents=True,exist_ok=True)
  rr=[r for r in load(src/'assessment/rna_ranking.json') if r['junction_id'] in wanted];dd=[d for d in load(src/'assessment/read_decisions.json') if d['junction_id'] in wanted]
  save(assess/'rna_ranking.json',rr);save(assess/'read_decisions.json',dd)
  result=reconstruct_run(assess,src/'discovery/split_reads.fastq',BASE/'reference/genome.fa',dest/'orfs',5)
  rec=load(dest/'orfs/reconstructions.json');hs=load(dest/'orfs/protein_hypotheses.json')
  assert len(rec)==sum(r['distinct_qualifying_reads'] for r in rr)
  for r in rec:r.update(library=lib,sample_alias=name)
  for h in hs:h.update(library=lib,sample_alias=name)
  for d in dd:d.update(library=lib,sample_alias=name)
  recons.extend(rec);hypotheses.extend(hs);ranks.append(rr);all_dec.extend(dd)
  save(dest/'selection.json',select(rr,rec,hs));print(lib,result,flush=True)
 joined=copy.deepcopy(ranks[0]);b={r['junction_id']:r for r in ranks[1]}
 for r in joined:
  r['distinct_qualifying_reads']+=b[r['junction_id']]['distinct_qualifying_reads'];r['followup_pooling']='Distinct original read IDs across A and B; biological replication UNKNOWN; original A rank retained'
 assert len({r['read_id'] for r in recons})==len(recons),'Read-ID overlap must be reconciled'
 combined=select(joined,recons,hypotheses)
 save(BASE/'reconstructions.json',recons);save(BASE/'protein_hypotheses.json',hypotheses);save(BASE/'read_decisions.json',all_dec);save(BASE/'selection.json',combined)
 summary=[]
 for jid in scope['junction_ids']:
  rs=[r for r in recons if r['junction_id']==jid];d=next(x for x in combined['decisions'] if x['junction_id']==jid)
  summary.append({'junction_id':jid,'pair':rs[0]['gene_name_5p']+':'+rs[0]['gene_name_3p'],'qualifying_reads_reconstructed':len(rs),'observed_complete_spanning_ORF_reads':sum(bool(r['observed_orfs']) for r in rs),'reference_assisted_complete_spanning_ORF_reads':sum(bool(r['reference_assisted_orfs']) for r in rs),'sequence_resolved_reads':sum(not r['unresolved_sequence_reasons'] for r in rs),'unresolved_reasons':dict(collections.Counter(v['reason'] for r in rs for v in r['unresolved_sequence_reasons'])),'folding_status':d['status'],'folding_reasons':d['reasons'],'primary_protein_hypotheses':len(d['primary_sequence_ids'])})
 save(BASE/'reconstruction-summary.json',summary)
 save(BASE/'selection-freeze.json',{'scope':'post-corroboration follow-up; five shared junctions; consistency across all qualifying A/B reads','inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'scope-freeze.json',BASE/'reconstructions.json',BASE/'protein_hypotheses.json',BASE/'selection.json',ROOT/'src/chrna/pilot_selection.py']},'selected':len(combined['selected']),'frozen':True})
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
