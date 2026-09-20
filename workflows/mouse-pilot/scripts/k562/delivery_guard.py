"""Shorten an existing owned worker lease for the user's one-hour delivery."""
from pathlib import Path
import datetime,json,os,signal,subprocess,time
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'runs/k562-all-junctions-20260920/folding-worker-live';NAME='chrna-k562-fold-20260920'
def main():
 plan=json.loads((RUN/'delivery-deadline.json').read_text());lease=json.loads((RUN/'lease.json').read_text())
 while time.time()<plan['compute_cutoff_epoch']:
  if (RUN/'shutdown-confirmed.json').exists():return
  time.sleep(min(15,plan['compute_cutoff_epoch']-time.time()))
 pid=lease['controller_pid'];path=Path('/proc')/str(pid)/'cmdline'
 if path.exists() and b'scripts/k562/run_all_folds.py' in path.read_bytes():os.kill(pid,signal.SIGTERM)
 limit=plan['shutdown_cutoff_epoch']
 while time.time()<limit:
  if (RUN/'shutdown-confirmed.json').exists():return
  time.sleep(10)
 env={**os.environ,'SHELL':'/bin/sh'}
 xs=json.loads(subprocess.check_output(['brev','ls','--json'],env=env,text=True,timeout=60))['workspaces']
 mine=[x for x in xs if x['name']==NAME]
 actual=json.loads((RUN/'actual-launch.json').read_text())['instances']
 if mine and actual and mine[0]['id']==actual[0]['id'] and mine[0]['status'] not in ('STOPPED','DELETED'):
  subprocess.run(['brev','stop',NAME],env=env,timeout=120,check=True)
 (RUN/'delivery-guard-fired.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Requested graceful preserve/shutdown; fallback owned-worker stop if necessary'},indent=2))
if __name__=='__main__':main()
