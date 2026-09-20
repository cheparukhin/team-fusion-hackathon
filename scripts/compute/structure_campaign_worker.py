#!/usr/bin/env python3
"""Bounded remote Boltz execution on an already provisioned owned GPU.

This script never controls cloud resources. A separate ownership-checked watchdog
must enforce the host lease. Inputs explicitly choose prepared MSAs or single-sequence mode.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
from structure_campaign_stage import save,digest,validate_model,SETTINGS

def run(a):
 import torch
 m=json.loads((a.inputs/'manifest.json').read_text())
 if m['settings']!=SETTINGS:raise ValueError('Protocol mismatch')
 if not torch.cuda.is_available()or torch.cuda.device_count()!=1:raise RuntimeError('Exactly one CUDA GPU required')
 device=torch.cuda.get_device_properties(0)
 if 'A100'not in device.name or device.total_memory<75*1024**3:raise RuntimeError('Expected compatible A10080GB')
 a.output.mkdir(parents=True,exist_ok=True)
 save(a.output/'runtime.json',{'utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':device.name,'gpu_total_memory_bytes':device.total_memory,'deadline_epoch':a.deadline_epoch,'stage':a.stage,'manifest_sha256':digest(a.inputs/'manifest.json')})
 cached=json.loads(a.cached.read_text())if a.cached and a.cached.exists()else []
 cached_ids={j['job_id']for j in cached if j['status']=='cached_verified'}
 previous=json.loads((a.output/'jobs.json').read_text())if (a.output/'jobs.json').exists()else []
 histories={j['job_id']:j for j in previous};histories.update({j['job_id']:j for j in cached})
 calibration=[j for j in m['jobs']if j['calibration']and j['seed']==20260919 and j['role'] in {'primary','sensitivity'}]
 controls=[j for j in m['jobs']if j['calibration']and j['seed']==20260919 and j['role'] in {'control','reference_control'}]
 if a.stage=='remaining':
  good=sum(histories.get(j['job_id'],{}).get('status')in {'verified','cached_verified'}for j in calibration)
  if not calibration or good/len(calibration)<.9:raise RuntimeError('Calibration gate below90%')
  if any(histories.get(j['job_id'],{}).get('status')not in {'verified','cached_verified','failed','unavailable'}for j in calibration):raise RuntimeError('Candidate calibration outcomes still pending')
 if a.stage=='diagnostic':
  first=[j for j in m['jobs']if j['seed']==20260919]
  if not first or len(first)>8 or len(m['jobs'])>24 or any(j['role']not in {'primary','sensitivity'}for j in m['jobs']):raise ValueError('Diagnostic panel exceeds8 candidates/24 total seed records')
  for j in first:
   prior=histories.get(j['job_id'],{})
   if prior.get('status')not in {'verified','cached_verified'}or any(prior.get(k)!=j[k]for k in ['sequence_sha256','sequence','protocol_id','msa_mode','seed']):raise ValueError('Diagnostic repeat requires verified matching first-pass model')
   for name,sha in prior.get('artifact_sha256',{}).items():
    if digest(prior['artifacts'][name])!=sha:raise ValueError('First-pass artifact changed before diagnostic repeat')
   validate_model(j['sequence'],prior['artifacts']['model.cif'],prior['artifacts']['plddt.npz'],prior['artifacts']['pae.npz'])
  if any(j['seed']not in {20260919,20260920,20260921}for j in m['jobs']):raise ValueError('Unexpected diagnostic seed')
 ordered=sorted(m['jobs'],key=lambda j:(not j['calibration'],j['seed']!=20260919,j['length_aa'],j['job_id']))
 def flush():save(a.output/'jobs.json',[histories.get(j['job_id'],{**j,'status':'not_run'})for j in m['jobs']])
 for j in ordered:
  if j['job_id']in cached_ids or histories.get(j['job_id'],{}).get('status')=='verified':continue
  if a.stage=='calibration' and not (j['calibration']and j['seed']==20260919):continue
  row={**j,'attempts':histories.get(j['job_id'],{}).get('attempts',[]),'reused_prior_prediction':False,'new_inference':True};histories[j['job_id']]=row
  if j.get('msa_mode','precomputed')=='precomputed':
   msa=a.inputs/j['msa'];side=msa.with_suffix('.json')
   if not msa.exists()or not side.exists():row.update(status='unavailable',reason='Prepared MSA missing');flush();continue
   receipt=json.loads(side.read_text())
   if digest(msa)!=receipt['a3m_sha256']or receipt['sequence_sha256']!=j['sequence_sha256']:raise ValueError('MSA hash mismatch')
  elif j['msa_mode']=='single_sequence':
   if j['msa']!='empty' or 'msa: empty'not in (a.inputs/j['yaml']).read_text():raise ValueError('Single-sequence YAML mismatch')
  else:raise ValueError('Unrecognized MSA protocol')
  if time.time()+690>=a.deadline_epoch:row.update(status='deferred',reason='Runtime budget reserve');flush();continue
  target=a.output/'models'/j['job_id'];target.mkdir(parents=True,exist_ok=True)
  for attempt in range(len(row['attempts']),2):
   available=a.deadline_epoch-time.time()-630
   if available<60:row.update(status='deferred',reason='Insufficient retry/runtime reserve');break
   attempt_dir=target/f'attempt_{attempt+1}';attempt_dir.mkdir(exist_ok=True)
   cmd=[str(Path(sys.executable).parent/'boltz'),'predict',str(a.inputs/j['yaml']),'--out_dir',str(attempt_dir),'--cache',str(a.cache),'--model','boltz2','--accelerator','gpu','--devices','1','--recycling_steps','3','--sampling_steps','200','--diffusion_samples','1','--step_scale','1.5','--seed',str(j['seed']),'--write_full_pae']
   event={'attempt':attempt+1,'argv':cmd,'started_utc':datetime.now(timezone.utc).isoformat()};row['attempts'].append(event);row['status']='running';flush();started=time.monotonic()
   try:
    with (attempt_dir/'boltz.log').open('w')as log:
     code=subprocess.run(['timeout','--signal=TERM','--kill-after=30s',str(int(min(a.max_job_seconds,available)))+'s',*cmd],cwd=a.inputs,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'HF_HUB_OFFLINE':'1','HF_DATASETS_OFFLINE':'1','WANDB_MODE':'disabled'},check=False).returncode
    if code:raise RuntimeError(f'Boltz exited {code}')
    predicted=attempt_dir/('boltz_results_'+j['job_id'])/'predictions'/j['job_id'];artifacts={}
    names={'model.cif':j['job_id']+'_model_0.cif','plddt.npz':'plddt_'+j['job_id']+'_model_0.npz','pae.npz':'pae_'+j['job_id']+'_model_0.npz','confidence.json':'confidence_'+j['job_id']+'_model_0.json'}
    valid=validate_model(j['sequence'],predicted/names['model.cif'],predicted/names['plddt.npz'],predicted/names['pae.npz'])
    for name,source in names.items():shutil.copy2(predicted/source,target/name);artifacts[name]=str((target/name).resolve())
    save(target/'validation.json',valid);row.update(status='verified',validation=valid,artifacts=artifacts,artifact_sha256={k:digest(v)for k,v in artifacts.items()})
    event['status']='verified'
   except Exception as e:event.update(status='failed',error=str(e),error_type=type(e).__name__);row.update(status='failed',reason=str(e))
   finally:event.update(wall_seconds=time.monotonic()-started,finished_utc=datetime.now(timezone.utc).isoformat());row['wall_seconds']=sum(x.get('wall_seconds',0)for x in row['attempts']);flush()
   if row['status']=='failed' and any(token in (attempt_dir/'boltz.log').read_text(errors='replace').lower()for token in ['cuda out of memory','torch.outofmemoryerror']):
    row['reason']='Deterministic CUDA out of memory; identical retry suppressed; full input retained';row['failure_class']='cuda_oom';flush();break
   if row['status']=='verified':break
 flush();good=sum(histories.get(j['job_id'],{}).get('status')in {'verified','cached_verified'}for j in calibration)
 save(a.output/'summary.json',{'status':'stage_complete','stage':a.stage,'calibration_denominator':'not applicable to diagnostic repeats; matching verified firstpass required'if a.stage=='diagnostic'else'candidate calibrators only; controls excluded','calibration_planned':len(calibration),'calibration_verified':good,'control_calibrators_planned':len(controls),'control_calibrators_verified':sum(histories.get(j['job_id'],{}).get('status')in {'verified','cached_verified'}for j in controls),'long_candidate_calibrators':[{'job_id':j['job_id'],'length_aa':j['length_aa'],'status':histories.get(j['job_id'],{}).get('status','not_run'),'reason':histories.get(j['job_id'],{}).get('reason')}for j in calibration if j['length_aa']>612],'calibration_gate_passed':None if a.stage=='diagnostic'else bool(calibration)and good/len(calibration)>=.9,'verified':sum(j.get('status')=='verified'for j in histories.values()),'cached_verified':sum(j.get('status')=='cached_verified'for j in histories.values()),'failed':sum(j.get('status')=='failed'for j in histories.values()),'deadline_epoch':a.deadline_epoch,'finished_utc':datetime.now(timezone.utc).isoformat()})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--cached',type=Path);p.add_argument('--deadline-epoch',type=float,required=True);p.add_argument('--max-job-seconds',type=int,default=1800);p.add_argument('--stage',choices=['calibration','remaining','diagnostic'],required=True);a=p.parse_args()
 for k in ['inputs','output','cache','cached']:
  if getattr(a,k):setattr(a,k,getattr(a,k).resolve())
 run(a)
