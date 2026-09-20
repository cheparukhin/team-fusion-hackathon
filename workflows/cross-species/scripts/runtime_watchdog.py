import json,pathlib,subprocess,time,datetime
R=pathlib.Path(__file__).resolve().parents[1]; p=R/'qc/spending_manifest.json'
x=json.loads(p.read_text()); ident=x['instance_id']; name=x['name']; end=x['deadline_epoch']
assert name=='chrna-cross-species-20260920'
while time.time()<end:
 if (R/'qc/watchdog_cancelled').exists():raise SystemExit(0)
 time.sleep(min(30,end-time.time()))
r=subprocess.run(['brev','ls','--json'],capture_output=True,text=True,check=True)
a=json.loads(r.stdout)['workspaces']
if not any(i['id']==ident and i['name']==name for i in a):raise SystemExit(0)
# Only the uniquely recorded task-owned instance is eligible for deletion.
r=subprocess.run(['brev','delete',ident],input='y\n',text=True,capture_output=True,timeout=180)
(R/'logs/watchdog_termination.log').write_text(r.stdout+r.stderr)
x=json.loads(p.read_text()); x.update(watchdog_returncode=r.returncode,termination_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());p.write_text(json.dumps(x,indent=2))
