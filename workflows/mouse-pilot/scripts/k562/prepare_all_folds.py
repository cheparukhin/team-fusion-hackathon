"""Reuse the verified mouse MSA workflow for the frozen human protein batch."""
from pathlib import Path
import json,hashlib,subprocess,sys,shutil,time
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'runs/k562-all-junctions-20260920';OUT=BASE/'fold-inputs'
def main():
 OUT.mkdir(exist_ok=True);jobs=[]
 for h in json.loads((BASE/'selection.json').read_text())['selected']:
  pid=h['protein_id'];(OUT/(pid+'.fasta')).write_text('>'+pid+'\n'+h['sequence']+'\n')
  job={'job_id':pid,'sequence':h['sequence'],'sequence_sha256':h['sequence_sha256'],'amino_acids':len(h['sequence']),'fasta':pid+'.fasta','msa':pid+'.a3m','yaml':pid+'.yaml','roles':[{'role':'recovered_reference_assisted_hypothesis','junction_id':h['junction_id'],'library':h['library']}]};jobs.append(job)
  (OUT/job['yaml']).write_text(json.dumps({'version':1,'sequences':[{'protein':{'id':'A','sequence':h['sequence'],'msa':job['msa']}}]},indent=2)+'\n')
 manifest={'status':'inputs_prepared_not_inferred','selection_freeze_sha256':hashlib.sha256((BASE/'selection-freeze.json').read_bytes()).hexdigest(),'jobs':jobs}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');history=[]
 for j in jobs:
  cache=BASE/'msa-cache'/j['job_id'];cache.mkdir(parents=True,exist_ok=True);started=time.time()
  try:
   with (cache/'preparation.log').open('w') as log:subprocess.run([sys.executable,str(ROOT/'scripts/prepare_boltz_msa.py'),'--fasta',str(OUT/j['fasta']),'--output',str(cache)],stdout=log,stderr=subprocess.STDOUT,timeout=600,check=True,cwd=ROOT)
   receipt=json.loads((cache/'msa.json').read_text());assert receipt['sequence_sha256']==j['sequence_sha256']
   shutil.copyfile(cache/'alignment.a3m',OUT/j['msa']);shutil.copyfile(cache/'msa.json',(OUT/j['msa']).with_suffix('.json'))
   history.append({'job_id':j['job_id'],'status':'verified','rows':receipt['rows'],'seconds':time.time()-started})
  except Exception as e:history.append({'job_id':j['job_id'],'status':'unavailable','error':str(e)})
  (OUT/'msa-preparation.json').write_text(json.dumps(history,indent=2)+'\n');print(history[-1],flush=True)
 available=sorted((j for j in jobs if any(h['job_id']==j['job_id'] and h['status']=='verified' for h in history)),key=lambda j:j['amino_acids'])
 manifest['timing_pilot_job_ids']=[available[i]['job_id'] for i in sorted({0,len(available)//2,len(available)-1})] if available else []
 manifest['msa_unavailable_job_ids']=[h['job_id'] for h in history if h['status']=='unavailable'];(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
