#!/usr/bin/env python3
"""Summarize observed execution; never extrapolate long-sequence feasibility."""
import argparse,csv,json,statistics
from pathlib import Path
from datetime import datetime,timezone
from structure_campaign_stage import save
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
jobs=json.loads((a.output/'jobs.json').read_text()); first=[j for j in jobs if j['seed']==20260919]
def group(rows):
 done=[j for j in rows if j['status']in {'verified','cached_verified'}]
 timed=[j['wall_seconds']for j in rows if j.get('wall_seconds')is not None]
 return {'planned':len(rows),'verified':len(done),'failed':sum(j['status']=='failed'for j in rows),'pending_or_deferred':sum(j['status']not in {'verified','cached_verified','failed'}for j in rows),'observed_wall_seconds':{'min':min(timed),'median':statistics.median(timed),'max':max(timed),'sum':sum(timed)}if timed else None}
cal=[j for j in first if j['calibration']and j['role']in {'primary','sensitivity'}]; ctr=[j for j in first if j['role']in {'control','reference_control'}]
gate=group(cal);gate['threshold_met']=bool(cal)and gate['verified']/len(cal)>=.9;gate['passed']=gate['threshold_met']and gate['pending_or_deferred']==0
long=[{k:j.get(k)for k in ['job_id','length_aa','status','wall_seconds','reason']}for j in cal if j['length_aa']>612]
tele=a.output/'remote/gpu_utilization.csv'; gpu={};samples=[]
if tele.exists():
 with tele.open()as f:
  rows=list(csv.reader(f))
 # Header is emitted by our monitor; numeric readings may be absent during teardown.
 values=[]
 for r in rows:
  try:
   values.append((float(r[2]),float(r[3]),float(r[4])));samples.append((datetime.fromisoformat(r[0]).timestamp(),float(r[2]),float(r[3])))
  except (ValueError,IndexError):pass
 if values:gpu={'samples':len(values),'max_utilization_percent':max(r[0]for r in values),'max_memory_used_mib':max(r[1]for r in values),'device_total_memory_mib':max(r[2]for r in values),'sampling_interval_seconds':2,'interpretation':'Sampled maxima; short peaks may be missed. Includes between-job startup/idle periods.'}
timing=[]
for j in jobs:
 attempts=[x for x in j.get('attempts',[])if x.get('finished_utc')]
 start=min((datetime.fromisoformat(x['started_utc']).timestamp()for x in attempts),default=None);end=max((datetime.fromisoformat(x['finished_utc']).timestamp()for x in attempts),default=None)
 matched=[x for x in samples if start is not None and start<=x[0]<=end]
 timing.append({'job_id':j['job_id'],'protocol_id':j['protocol_id'],'length_aa':j['length_aa'],'role':j['role'],'seed':j['seed'],'status':j['status'],'wall_seconds':j.get('wall_seconds'),'attempts':len(j.get('attempts',[])),'sampled_peak_gpu_memory_mib':max((x[2]for x in matched),default=None),'sampled_peak_gpu_utilization_percent':max((x[1]for x in matched),default=None)})
if timing:
 with (a.output/'runtime_by_job.tsv').open('w')as f:
  w=csv.DictWriter(f,fieldnames=list(timing[0]),delimiter='\t');w.writeheader();w.writerows(timing)
bands={}
for name,lo,hi in [('<=150',0,150),('151-300',151,300),('301-600',301,600),('601-1000',601,1000),('>1000',1001,float('inf'))]:bands[name]=group([j for j in first if lo<=j['length_aa']<=hi])
save(a.output/'runtime_report.json',{'utc':datetime.now(timezone.utc).isoformat(),'candidate_calibration':gate,'controls':group(ctr),'long_candidate_calibrators':long,'length_bands':bands,'gpu_telemetry':gpu,'scope':'Observed single-sequence protocol performance, not an MSA-backed forecast or biological validation.'})
print(json.dumps({'candidate_calibration':gate,'controls':group(ctr),'long_candidate_calibrators':long},indent=2))
