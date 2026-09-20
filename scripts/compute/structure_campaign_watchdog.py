#!/usr/bin/env python3
"""Enforce one ownership-verified resumed-host lease; never delete resources."""
import argparse,json,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
from structure_campaign_stage import save
p=argparse.ArgumentParser();p.add_argument('--lease',type=Path,required=True);a=p.parse_args()
while True:
 lease=json.loads(a.lease.read_text())
 if lease.get('status')in {'stopped','cancelled'}:break
 if (lease['name'],lease['instance_id'])!=('chrna-boltz-20260919','8mq2074bp')or not lease.get('project_creation_receipts_verified'):raise RuntimeError('Unverified ownership')
 remaining=lease['deadline_epoch']-time.time()
 if remaining>0:time.sleep(min(20,remaining));continue
 inventory=json.loads(subprocess.check_output(['/home/ubuntu/.local/bin/brev','ls','--json'],text=True))['workspaces']
 matches=[i for i in inventory if i['id']==lease['instance_id']and i['name']==lease['name']]
 if len(matches)!=1:raise RuntimeError('Resource identity no longer matches lease')
 if matches[0]['status']!='STOPPED':
  result=subprocess.run(['/home/ubuntu/.local/bin/brev','stop',lease['instance_id']],capture_output=True,text=True,timeout=180)
  (a.lease.parent/'watchdog_stop.log').write_text(result.stdout+result.stderr)
  if result.returncode:raise RuntimeError('Stop failed; manual resource review required')
 save(a.lease.parent/'watchdog_receipt.json',{'utc':datetime.now(timezone.utc).isoformat(),'instance_id':lease['instance_id'],'action':'stop_requested_or_already_stopped','final_inventory_verification_required':True})
 break
