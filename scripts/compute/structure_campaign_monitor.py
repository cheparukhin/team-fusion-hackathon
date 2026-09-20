#!/usr/bin/env python3
"""Record actual GPU telemetry until the run deadline; no credentials or cloud calls."""
import argparse,csv,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--deadline-epoch',type=float,required=True);a=p.parse_args()
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('w')as f:
 w=csv.writer(f);w.writerow(['utc','gpu_name','gpu_utilization_percent','memory_used_mib','memory_total_mib'])
 while time.time()<a.deadline_epoch:
  r=subprocess.run(['nvidia-smi','--query-gpu=name,utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
  if r.returncode:break
  for line in r.stdout.splitlines():w.writerow([datetime.now(timezone.utc).isoformat(),*[x.strip()for x in line.split(',')]])
  f.flush();time.sleep(min(2,max(0,a.deadline_epoch-time.time())))
