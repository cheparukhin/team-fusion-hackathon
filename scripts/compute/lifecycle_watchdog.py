"""Bound the pilot ID this task created; never touch preexisting instances."""
import datetime,json,pathlib,subprocess,time
root=pathlib.Path(__file__).resolve().parents[2]
manifest=root/'results/compute/spending_manifest.json'
x=json.loads(manifest.read_text())
assert x['name']=='chrna-rna-pilot-20260919' and x['instance_id']=='kerxx8tqg'
end=datetime.datetime.fromisoformat(x['created_utc']).timestamp()+x['runtime_cap_seconds']
time.sleep(max(0,end-time.time()))
x=json.loads(manifest.read_text())
if x.get('status') in ('deleted','cancelled'):raise SystemExit(0)
r=subprocess.run(['/home/ubuntu/.local/bin/brev','ls','--json'],text=True,capture_output=True,check=True)
instances=json.loads(r.stdout).get('workspaces',[])
if not any(v['id']==x['instance_id'] and v['name']==x['name'] for v in instances):raise SystemExit(0)
r=subprocess.run(['/home/ubuntu/.local/bin/brev','delete',x['instance_id']],input='y\n',text=True,capture_output=True)
(root/'results/compute/watchdog_termination.log').write_text(r.stdout+r.stderr)
x=json.loads(manifest.read_text());x.update(watchdog_termination_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),watchdog_returncode=r.returncode);manifest.write_text(json.dumps(x,indent=2))
