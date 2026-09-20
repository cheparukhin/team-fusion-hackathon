import pathlib,subprocess,json,time,os,signal
R=pathlib.Path(__file__).resolve().parents[1];deadline=json.loads((R/'qc/deadline.json').read_text());jobs=[]
for sp,run,stage in [('bos_taurus','SRR31429688','cow_longgf'),('homo_sapiens','SRR31438987','jaffal'),('bos_taurus','SRR31429688','jaffal'),('bos_taurus','SRR31429688','genion'),('homo_sapiens','SRR31438987','reconstruct_longgf'),('bos_taurus','SRR31429688','reconstruct_longgf')]:
 log=R/'logs'/f'deadline_{sp}_{stage}.log';p=subprocess.Popen([str(R/'software/bin/micromamba'),'run','-p',str(R/'software/env'),'python',str(R/'scripts/deadline_stage.py'),sp,run,stage],stdout=log.open('w'),stderr=subprocess.STDOUT,start_new_session=True);jobs.append({'pid':p.pid,'species':sp,'run':run,'stage':stage,'log':str(log)})
(R/'qc/deadline_jobs.json').write_text(json.dumps(jobs,indent=2))
while time.time()<deadline['calls_cutoff_epoch']:time.sleep(min(15,deadline['calls_cutoff_epoch']-time.time()))
for j in jobs:
 try:os.killpg(j['pid'],signal.SIGTERM)
 except ProcessLookupError:pass
# Existing human Genion was started before this bounded scheduler. Stop its verified descendant tree only.
ps=subprocess.check_output(['ps','-eo','pid=,ppid='],text=True);children={}
for l in ps.splitlines():
 pid,ppid=map(int,l.split());children.setdefault(ppid,[]).append(pid)
def descendants(pid):
 return [x for child in children.get(pid,[]) for x in [*descendants(child),child]]
if pathlib.Path('/proc/30008/cmdline').exists() and b'TYPHON/typhon_main.py' in pathlib.Path('/proc/30008/cmdline').read_bytes():
 for pid in descendants(30008)+[30008]:
  try:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:pass
(R/'qc/calls_frozen_at_deadline').write_text(str(time.time()))
