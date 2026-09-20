#!/usr/bin/env python3
"""Bounded local AF2 run on cached MSA; external MSA endpoint deliberately disabled."""
import argparse,json,os,signal,subprocess,time,hashlib
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--timeout',type=int,default=1800);a=p.parse_args();root=a.root.resolve();out=root/'af2_cpu';out.mkdir(exist_ok=True)
command=[str(root/'setup/af2_env/bin/colabfold_batch'),str(root/'inputs/gsdmd_tmem106a.a3m'),str(out/'raw'),'--model-type','alphafold2_ptm','--num-models','1','--model-order','1','--num-recycle','3','--recycle-early-stop-tolerance','0','--num-seeds','1','--random-seed','20260919','--max-msa','128:256','--num-relax','0','--data',str(root/'setup/weights/af2'),'--host-url','http://127.0.0.1:9','--overwrite-existing-results']
env={**os.environ,'CUDA_VISIBLE_DEVICES':'','JAX_PLATFORMS':'cpu','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','MKL_NUM_THREADS':'2','TF_NUM_INTRAOP_THREADS':'2','TF_NUM_INTEROP_THREADS':'1','XLA_FLAGS':'--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2','TF_CPP_MIN_LOG_LEVEL':'3'}
r={'status':'running','started_utc':datetime.now(timezone.utc).isoformat(),'argv':command,'device':'cpu','timeout_seconds':a.timeout,'process_tree_rss_limit_bytes':5*1024**3,'msa_source_rows':913,'msa_max_clusters':128,'msa_max_extra':256,'sequence_cropped':False,'external_msa_service_disabled':True,'new_cloud_allocation_usd':0};(out/'run.json').write_text(json.dumps(r,indent=2)+'\n');start=time.monotonic();maxrss=0
with (out/'run.log').open('w')as log:
 proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 while proc.poll()is None:
  time.sleep(2);elapsed=time.monotonic()-start
  try:
   import psutil
   p=psutil.Process(proc.pid);rss=sum(x.memory_info().rss for x in [p,*p.children(recursive=True)]if x.is_running());maxrss=max(maxrss,rss)
  except Exception:rss=0
  if elapsed>a.timeout or rss>5*1024**3:
   r['failure_reason']='runtime cap'if elapsed>a.timeout else'process tree memory cap';os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(timeout=20)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL)
   break
 r.update(status='process_completed'if proc.wait()==0 else'failed',returncode=proc.returncode,wall_seconds=time.monotonic()-start,peak_process_tree_rss_bytes=maxrss,finished_utc=datetime.now(timezone.utc).isoformat());(out/'run.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
