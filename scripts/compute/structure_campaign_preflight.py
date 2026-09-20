#!/usr/bin/env python3
"""Read-only infrastructure preflight; never starts/stops/deletes a resource."""
import json,subprocess,os,hashlib,argparse
from pathlib import Path
from datetime import datetime,timezone
B=Path('/home/ubuntu/workspace/chrna/runs/focused-pilot-20260919')
def get(*args):return json.loads(subprocess.check_output(['/home/ubuntu/.local/bin/brev',*args],text=True))
def main(out):
 out.mkdir(parents=True,exist_ok=True);now=datetime.now(timezone.utc)
 inv=get('ls','--json');quotes=get('search','gpu','--gpu-name','A100','--json')
 matching=[q for q in quotes if q['type']in {'a100-80gb.1x','denvr_A100_sxm4_80G'}]
 evidence={}
 for rel in ['folding-worker/launch-inventory.json','folding-worker/actual-launch.json','folding-worker-retry-3/resume-provenance.json','folding-worker-retry-3/shutdown-confirmed.json']:
  p=B/rel;evidence[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'record':json.loads(p.read_text())}
 early=datetime.fromisoformat('2026-09-19T15:12:04.807110+00:00');hours=(now-early).total_seconds()/3600
 # Deliberately bill stopped resources at historical maximum RUNNING+disk rate
 # for the entire interval, plus full previous allocation caps for deleted jobs.
 rate=3.643095; prior_bound=hours*rate+20+3.6
 d={'utc':now.isoformat(),'status':'read_only_no_allocation','inventory':inv,'live_quotes':matching,'credential_presence_only':{k:bool(os.environ.get(k))for k in ['NGC_API_KEY','NVIDIA_API_KEY']},'reuse_host_id':'8mq2074bp','reuse_ownership_evidence':evidence,'shared_cap_usd':150,'conservative_visible_project_bound_usd':round(prior_bound,2),'prior_bound_method':{'start_utc':early.isoformat(),'elapsed_hours':hours,'all_three_resources_full_running_plus_disk_usd_per_hour':rate,'deleted_k562_full_incremental_allocation_cap_usd':20,'deleted_parabricks_full_allocation_cap_usd':3.6,'purpose':'Upper-bound reservation using known historical rates; not actual invoice','limitations':['No reconciled provider invoice or account balance available','Controller charges before earliest documented project launch are not represented','No restart permitted until sequence eligibility and coordinator budget gate pass']},'remaining_after_visible_bound_usd':round(150-prior_bound,2),'campaign_gpu_allocation_usd':0}
 (out/'preflight.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'utc':d['utc'],'status':d['status'],'prior_visible_bound_usd':d['conservative_visible_project_bound_usd'],'remaining_after_bound_usd':d['remaining_after_visible_bound_usd'],'matching_quotes':matching},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('results/structure_campaign/compute'));main(p.parse_args().output)
