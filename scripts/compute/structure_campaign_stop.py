#!/usr/bin/env python3
"""Stop only the recorded owned GPU after a verified final local export."""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
from structure_campaign_stage import save,digest,validate_model
p=argparse.ArgumentParser();p.add_argument('--lease',type=Path,required=True);p.add_argument('--final-output',type=Path,required=True);a=p.parse_args()
lease=json.loads(a.lease.read_text());identity=('chrna-boltz-20260919','8mq2074bp')
if (lease['name'],lease['instance_id'])!=identity or not lease.get('project_creation_receipts_verified'):raise ValueError('Ownership mismatch')
receipt=json.loads((a.final_output/'export_receipt.json').read_text())
if digest(a.final_output/'snapshot.tar.gz')!=receipt['archive_sha256']:raise ValueError('Final snapshot hash mismatch')
jobs=json.loads((a.lease.parent.parent/'jobs.json').read_text())
if not jobs or any(j['status']=='running'for j in jobs):raise ValueError('Final export still includes active jobs')
for j in jobs:
 if j['status']in {'verified','cached_verified'}:
  for name,sha in j['artifact_sha256'].items():
   if digest(j['artifacts'][name])!=sha:raise ValueError('Local model artifact hash mismatch')
  validate_model(j['sequence'],j['artifacts']['model.cif'],j['artifacts']['plddt.npz'],j['artifacts']['pae.npz'])
verified_exports=[]
for folder in ['single_sequence_pilot','single_sequence_full','single_sequence_deepdive']:
 path=a.lease.parent.parent/folder
 if (path/'export_receipt.json').exists():
  r=json.loads((path/'export_receipt.json').read_text())
  if digest(path/'snapshot.tar.gz')!=r['archive_sha256']:raise ValueError('Prior export snapshot hash mismatch')
  verified_exports.append({'directory':str(path),'archive_sha256':r['archive_sha256'],'counts':r['counts']})
brev='/home/ubuntu/.local/bin/brev'
def inventory():
 all_rows=json.loads(subprocess.check_output([brev,'ls','--json'],text=True))['workspaces']
 rows=[i for i in all_rows if (i['name'],i['id'])==identity]
 if len(rows)!=1:raise ValueError('Current instance identity mismatch')
 return rows[0],all_rows
row,before=inventory();started=datetime.now(timezone.utc).isoformat();save(a.lease.parent/'cleanup_inventory_before.json',before)
if row['status']!='STOPPED':
 r=subprocess.run([brev,'stop',lease['instance_id']],text=True,capture_output=True,timeout=180);(a.lease.parent/'cleanup_stop.log').write_text(r.stdout+r.stderr);r.check_returncode()
for _ in range(60):
 row,after=inventory()
 if row['status']=='STOPPED':break
 time.sleep(5)
else:raise RuntimeError('Stop not confirmed; watchdog remains active')
external_path=a.lease.parent.parent/'external_allocation.json';external=json.loads(external_path.read_text())if external_path.exists()else {};external_cap=external.get('new_allocation_cap_usd',0)
finished=datetime.now(timezone.utc);elapsed=finished.timestamp()-datetime.fromisoformat(lease['created_utc']).timestamp()
lease.update(status='stopped',stop_requested_utc=started,stopped_confirmed_utc=finished.isoformat(),elapsed_seconds=elapsed,gpu_elapsed_cost_estimate_usd=round(elapsed/3600*lease['gpu_quote_usd_per_hour'],4));save(a.lease,lease)
watch=a.lease.parent/'watchdog.json';cancel='lease marked stopped; watchdog will exit without future resource action'
if watch.exists():
 w=json.loads(watch.read_text());pid=w.get('pid')
 if pid:
  try:
   cmd=Path(f'/proc/{pid}/cmdline').read_bytes().decode().replace('\0',' ')
   if 'structure_campaign_watchdog.py' in cmd and str(a.lease.resolve())in cmd:os.kill(pid,signal.SIGTERM);cancel=f'Confirmed owned watchdog PID{pid} terminated after stop verification'
  except FileNotFoundError:cancel='Owned watchdog already exited'
save(a.lease.parent/'cleanup_inventory_after.json',after)
final={'status':'stopped_confirmed','instance_name':identity[0],'instance_id':identity[1],'stop_requested_utc':started,'stopped_confirmed_utc':finished.isoformat(),'watchdog_cancelled_utc':datetime.now(timezone.utc).isoformat(),'watchdog_action':cancel,'final_export_directory':str(a.final_output),'final_export_sha256':receipt['archive_sha256'],'verified_export_snapshots':verified_exports,'locally_verified_model_records':sum(j['status']in {'verified','cached_verified'}for j in jobs),'elapsed_seconds_including_startup_and_stop':elapsed,'gpu_hourly_quote_usd':lease['gpu_quote_usd_per_hour'],'gpu_elapsed_cost_estimate_usd':lease['gpu_elapsed_cost_estimate_usd'],'visible_background_and_compute_elapsed_upper_bound_usd':round(elapsed/3600*lease['all_visible_resources_hourly_bound_usd'],4),'prior_visible_project_bound_usd':lease['prior_visible_project_bound_usd'],'elapsed_rate_shared_budget_bound_usd':round(lease['prior_visible_project_bound_usd']+elapsed/3600*lease['all_visible_resources_hourly_bound_usd']*1.25+external_cap,2),'conservative_shared_budget_cumulative_bound_usd':round(lease['prior_visible_project_bound_usd']+lease['reservation_with25percent_contingency_usd']+external_cap,2),'separate_task_incremental_allocation_cap_usd':external_cap,'separate_task_accounting_receipt':str(external_path)if external else None,'shared_budget_cap_usd':150,'unmeasured_storage_cost_usd':None,'storage_note':'Quoted visible disk rates are included in the conservative background bound; unquoted storage, egress and future retained storage are not measured. No provider invoice reconciliation available.','cost_note':'Elapsed-rate estimate, not provider invoice. Background bound includes all visible resources at their quoted rates; retained storage continues after GPU stop. No resource deleted; other instances unchanged.'}
save(a.lease.parent/'cleanup_receipt.json',final);save(a.lease.parent.parent/'cleanup_receipt.json',final);print(json.dumps(final,indent=2))
