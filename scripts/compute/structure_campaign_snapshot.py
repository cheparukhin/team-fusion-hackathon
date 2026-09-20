#!/usr/bin/env python3
"""Snapshot only validated model artifacts and bounded progress logs for export."""
import argparse,hashlib,io,json,tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);a=p.parse_args()
rows=json.loads((a.output/'jobs.json').read_text())if(a.output/'jobs.json').exists()else []
with tarfile.open(a.archive,'w:gz')as t:
 data=(json.dumps(rows,indent=2)+'\n').encode();item=tarfile.TarInfo('jobs.json');item.size=len(data);t.addfile(item,io.BytesIO(data))
 for name in ['environment_validation.json','requirements-lock.txt','gpu_utilization.csv','monitor.log','worker.log','worker.pid','runtime.json','summary.json']:
  file=a.output/name
  if file.exists():t.add(file,arcname=name)
 for r in rows:
  if r['status']=='verified':
   for name in ['model.cif','plddt.npz','pae.npz','confidence.json','validation.json']:
    file=a.output/'models'/r['job_id']/name;t.add(file,arcname=str(file.relative_to(a.output)))
  for log in (a.output/'models'/r['job_id']).glob('attempt_*/boltz.log'):t.add(log,arcname=str(log.relative_to(a.output)))
print(json.dumps({'archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'counts':{s:sum(r['status']==s for r in rows)for s in sorted({r['status']for r in rows})},'models':[{k:r.get(k)for k in ['peptide_id','length_aa','status','wall_seconds','reason']}for r in rows]}))
