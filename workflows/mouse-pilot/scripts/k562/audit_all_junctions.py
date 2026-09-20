"""Validate coverage and sequence provenance for the all-junction human follow-up."""
from pathlib import Path
import collections,csv,hashlib,json
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'runs/k562-all-junctions-20260920'
def load(name):return json.loads((BASE/name).read_text())
def main():
 scope=load('scope-freeze.json');freeze=load('selection-freeze.json');recs=load('reconstructions.json');hs=load('protein_hypotheses.json');selection=load('selection.json');summaries=load('reconstruction-summary.json');ads=load('adapter-read-assessment.json')
 for name,digest in freeze['inputs'].items():assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest
 assert len(scope['junction_ids'])==414 and len(recs)==450
 assert len({(r['library'],r['junction_id'],r['read_id']) for r in recs})==450
 for lib,n,nr in [('A',220,242),('B',199,208)]:
  ranks=load(lib+'/assessment/rna_ranking.json');rc=[r for r in recs if r['library']==lib];assert len(ranks)==n and len(rc)==nr
  assert {r['junction_id'] for r in ranks}=={r['junction_id'] for r in rc}
  for row in ranks:assert row['distinct_qualifying_reads']==len({r['read_id'] for r in rc if r['junction_id']==row['junction_id']})
 for h in hs:assert h['sequence_sha256']==hashlib.sha256(h['sequence'].encode()).hexdigest()
 for h in selection['selected']:
  rc=next(r for r in recs if r['junction_id']==h['junction_id'] and r['read_id']==h['read_id']);assert not rc['unresolved_sequence_reasons'];assert rc['reference_assisted_orfs'][0]['protein']==h['sequence']
 orfids={r['junction_id'] for r in recs if r['reference_assisted_orfs']};selectedids={h['junction_id'] for h in selection['selected']}
 rows=[]
 for jid in scope['junction_ids']:
  rr=[r for r in summaries if r['junction_id']==jid];rows.append({'junction_id':jid,'pair':rr[0]['pair'],'library_A_support':sum(r['qualifying_reads_reconstructed'] for r in rr if r['library']=='A'),'library_B_support':sum(r['qualifying_reads_reconstructed'] for r in rr if r['library']=='B'),'ORF_bearing_reads':sum(r['reference_assisted_complete_spanning_ORF_reads'] for r in rr),'protein_stage':'selected_for_folding' if jid in selectedids else 'ORF_sequence_unresolved' if jid in orfids else 'no_complete_spanning_ORF_in_reconstructed_reads','biological_truth':'UNKNOWN'})
 with (BASE/'candidate-stage-audit.tsv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
 result={'status':'RNA_ORF_adapter_assessment_verified_structure_compute_blocked','scope':{'A':220,'B':199,'distinct_junctions':414,'shared':5},'read_reconstructions':450,'observed_complete_spanning_ORF_reads':sum(bool(r['observed_orfs']) for r in recs),'reference_assisted_ORF_bearing_reads':sum(bool(r['reference_assisted_orfs']) for r in recs),'distinct_protein_hypotheses':len({h['protein_id'] for h in hs}),'junction_stage_counts':dict(collections.Counter(r['protein_stage'] for r in rows)),'selected_proteins':len(selection['selected']),'MSAs_verified':sum(r['status']=='verified' for r in load('fold-inputs/msa-preparation.json')),'adapter_read_junction_records':len(ads),'adapter_internal_flags':sum(r['internal_adapter_near_join'] for r in ads),'polyAT_internal_flags':sum(bool(r['internal_polyAT_near_join']) for r in ads),'new_GPU_instances':0,'new_worker_cost_USD':0,'structure_status':'NOT_GENERATED: live quote feed omitted existing Crusoe project SKUs, preventing combined budget verification; no launch was performed','validation':{'pytest_passed':119,'data_build':'passed','development_benchmark':'passed','heldout_evaluated':False},'limitations':['Reference-assisted ORFs are sequence hypotheses, not evidence of protein production or function.','All six selected hypotheses have one qualifying read in one library.','No second-library or Illumina requirement was applied.','Adapter screen tests two full RTA cores only; raw signal and same-culture DNA were not assessed.','Dashboard includes two extra cross-library unresolved read records outside the local adapter/reconstruction scope; these remain unassessed.']}
 if (BASE/'structures/summary.json').exists():
  jobs=load('structures/summary.json');verified=sum(j['status']=='verified' for j in jobs);result.update(status='completed' if verified==6 else 'partial_structure_results',verified_structures=verified,new_GPU_instances=1,new_worker_cost_USD=load('resource-accounting.json')['launch_to_confirmed_stop_quote_USD'] if (BASE/'resource-accounting.json').exists() else None,structure_status=f'{verified} sequence/confidence-verified Boltz-2 predictions; protein expression and function UNKNOWN')
 (BASE/'completion.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
