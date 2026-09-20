#!/usr/bin/env python3
"""Serialize CPU folding and enforce aggregate-host memory/runtime limits."""
import argparse,json,os,signal,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
import psutil
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--timeout',type=int,default=1800);a=p.parse_args();root=a.root.resolve();repo=Path(__file__).resolve().parents[2]
receipt={'status':'waiting_for_af2','created_utc':datetime.now(timezone.utc).isoformat(),'timeout_seconds':a.timeout,'minimum_host_available_memory_bytes':768*1024**2,'low_memory_grace_seconds':10,'external_sequence_uploads':0,'new_cloud_allocation_usd':0};target=root/'esmfold_cpu_supervisor.json'
def save():target.write_text(json.dumps(receipt,indent=2)+'\n')
save();wait_started=time.monotonic()
while True:
 r=json.loads((root/'af2_cpu/run.json').read_text())
 if r.get('status')!='running':break
 if time.monotonic()-wait_started>2100:raise RuntimeError('AF2 did not terminate within wait bound')
 time.sleep(5)
if psutil.virtual_memory().available<3*1024**3:raise RuntimeError('Insufficient available host RAM for safe CPU start')
out=root/'esmfold_cpu';out.mkdir(exist_ok=True)
if(out/'run.json').exists():(root/'esmfold_initialization.json').write_text((out/'run.json').read_text())
cmd=[str(repo/'.venv-disorder/bin/python'),str(repo/'scripts/compute/gsdmd_cross_model_esmfold.py'),'--root',str(root),'--device','cpu']
env={**os.environ,'PYTHONPATH':str(root/'setup/esm_packages'),'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','MKL_NUM_THREADS':'2'}
receipt.update(status='running',argv=cmd,started_utc=datetime.now(timezone.utc).isoformat(),host_available_memory_start=psutil.virtual_memory().available);save();start=time.monotonic();low_since=None;minimum=psutil.virtual_memory().available;peak_rss=0
with(out/'run.log').open('w')as log:
 proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 while proc.poll()is None:
  time.sleep(2);elapsed=time.monotonic()-start;available=psutil.virtual_memory().available;minimum=min(minimum,available)
  try:peak_rss=max(peak_rss,psutil.Process(proc.pid).memory_info().rss)
  except psutil.NoSuchProcess:pass
  low_since=(low_since or time.monotonic())if available<768*1024**2 else None
  if elapsed>a.timeout or(low_since and time.monotonic()-low_since>10):
   receipt['failure_reason']='runtime cap'if elapsed>a.timeout else'combined host memory safety limit';os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(timeout=20)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL)
   break
 code=proc.wait()
receipt.update(status='process_completed'if code==0 else'failed',returncode=code,wall_seconds=time.monotonic()-start,minimum_host_available_memory_bytes_observed=minimum,peak_process_rss_bytes=peak_rss,finished_utc=datetime.now(timezone.utc).isoformat());save()
if code!=0:
 current=json.loads((out/'run.json').read_text())if(out/'run.json').exists()else{}
 current.update(status='failed',failure_reason=receipt.get('failure_reason','See run.log'),supervisor_returncode=code);(out/'run.json').write_text(json.dumps(current,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
