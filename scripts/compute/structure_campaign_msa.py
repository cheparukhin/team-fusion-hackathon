#!/usr/bin/env python3
"""Serial, deadline-bounded MSA staging using the hash-pinned Boltz 2.2.1 client."""
import argparse,hashlib,importlib.util,json,subprocess,sys,time,zipfile,shutil
from pathlib import Path
from datetime import datetime,timezone
from structure_campaign_stage import save,digest
PRIOR=Path('/home/ubuntu/workspace/chrna/runs/focused-pilot-20260919')
WHEEL_SHA='b8c62bbdede1922931d9203118f62c858f11aa699bf91fd4c05a5ed6a6d8b4fc'
def query(args):
 m=json.loads((args.output/'inputs/manifest.json').read_text());j=next(j for j in m['jobs']if j['sequence_sha256']==args.sequence_sha)
 wheel=PRIOR/'boltz-preparation/boltz-2.2.1-py3-none-any.whl'
 if digest(wheel)!=WHEEL_SHA:raise ValueError('Boltz wheel mismatch')
 cache=args.output/'msa-cache'/args.sequence_sha;cache.mkdir(parents=True,exist_ok=True)
 source=cache/'pinned_client.py'
 with zipfile.ZipFile(wheel)as z:source.write_bytes(z.read('boltz/data/msa/mmseqs2.py'))
 spec=importlib.util.spec_from_file_location('pinned_msa',source);client=importlib.util.module_from_spec(spec);spec.loader.exec_module(client)
 t=time.monotonic();text=client.run_mmseqs2(j['sequence'],prefix=str(cache/'request'),use_env=True,use_filter=True)[0]
 rows=[]
 for line in text.splitlines():
  if line.startswith('>'):rows.append('')
  elif line and not line.startswith('#'):rows[-1]+=line
 if not rows or rows[0]!=j['sequence']:raise ValueError('MSA query differs')
 aligned=[''.join(c for c in row if not c.islower())for row in rows]
 if any(len(r)!=len(j['sequence'])for r in aligned):raise ValueError('MSA aligned width differs')
 dest=args.output/'inputs'/j['msa'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
 save(dest.with_suffix('.json'),{'status':'verified','sequence_sha256':args.sequence_sha,'a3m_sha256':digest(dest),'rows':len(rows),'aligned_non_gap_depth':[sum(row[i]not in '-.'for row in aligned)for i in range(len(j['sequence']))],'wall_seconds':time.monotonic()-t,'server':'https://api.colabfold.com','client_version':'boltz 2.2.1','client_wheel_sha256':WHEEL_SHA,'finished_utc':datetime.now(timezone.utc).isoformat(),'settings':{'use_env':True,'use_filter':True,'use_pairing':False},'interpretation':'Per-residue depth; does not establish homologous full-fusion or cross-junction coevolution'})
def batch(args):
 m=json.loads((args.output/'inputs/manifest.json').read_text());seen=set();history=[];deadline=time.time()+args.max_seconds
 for j in m['jobs']:
  sha=j['sequence_sha256']
  if sha in seen:continue
  seen.add(sha);dest=args.output/'inputs'/j['msa'];dest.parent.mkdir(parents=True,exist_ok=True);side=dest.with_suffix('.json');record={'sequence_sha256':sha,'peptide_id':j['peptide_id']}
  try:
   old=PRIOR/'fold-inputs/msas'/f'protein_{sha}.a3m';oldside=old.with_suffix('.json')
   if not dest.exists() and old.exists() and oldside.exists():
    d=json.loads(oldside.read_text())
    if d['sequence_sha256']!=sha or digest(old)!=d['a3m_sha256']:raise ValueError('Prior MSA integrity failed')
    shutil.copy2(old,dest);shutil.copy2(oldside,side);record['reused_prior_msa']=True
   if dest.exists() and side.exists():
    d=json.loads(side.read_text())
    if d['sequence_sha256']!=sha or digest(dest)!=d['a3m_sha256']:raise ValueError('MSA integrity failed')
   else:
    remaining=deadline-time.time()
    if remaining<30:raise TimeoutError('Serial MSA batch deadline')
    log=args.output/'msa-cache'/sha/'preparation.log';log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('w')as f:
     status=subprocess.run(['timeout','--signal=TERM','--kill-after=10s',str(int(min(900,remaining)))+'s',sys.executable,__file__,'query','--output',str(args.output),'--sequence-sha',sha],stdout=f,stderr=subprocess.STDOUT,check=False).returncode
    if status:raise RuntimeError(f'MSA client exit {status}')
    d=json.loads(side.read_text())
   record.update(status='verified',rows=d['rows'],a3m_sha256=d['a3m_sha256'],msa_wall_seconds=d['wall_seconds'])
  except Exception as e:record.update(status='unavailable',reason=str(e))
  history.append(record);save(args.output/'msa_jobs.json',history)
 print(json.dumps({'verified':sum(r['status']=='verified'for r in history),'unavailable':sum(r['status']!='verified'for r in history)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['batch','query']);p.add_argument('--output',type=Path,required=True);p.add_argument('--max-seconds',type=int,default=3600);p.add_argument('--sequence-sha');a=p.parse_args();a.output=a.output.resolve();query(a)if a.command=='query'else batch(a)
