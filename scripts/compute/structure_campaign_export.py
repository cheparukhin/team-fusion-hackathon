#!/usr/bin/env python3
"""Export one consistent validated-results snapshot from the owned campaign host."""
import argparse,hashlib,json,os,shlex,subprocess,sys,tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--remote-base',required=True);p.add_argument('--merge-output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
if not a.remote_base.startswith('/home/ubuntu/results/structure_campaign/compute/'):raise ValueError('Campaign-only remote path required')
if (a.output/'firstpass_freeze.json').exists():raise RuntimeError('Frozen first-pass export cannot be overwritten; use a separate diagnostic output directory')
root=Path(__file__).resolve().parents[2];env={**os.environ,'SHELL':'/bin/sh'}
cmd='python3 - --output '+shlex.quote(a.remote_base+'/outputs')+' --archive '+shlex.quote(a.remote_base+'/snapshot.tar.gz')
r=subprocess.run(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15','chrna-boltz-20260919',cmd],input=(root/'scripts/compute/structure_campaign_snapshot.py').read_text(),text=True,capture_output=True,env=env,timeout=120);(a.output/'export_ssh.log').write_text(r.stderr);r.check_returncode();receipt=json.loads(r.stdout)
subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15','chrna-boltz-20260919:'+a.remote_base+'/snapshot.tar.gz',str(a.output/'snapshot.tar.gz')],env=env,timeout=240,check=True)
if hashlib.sha256((a.output/'snapshot.tar.gz').read_bytes()).hexdigest()!=receipt['archive_sha256']:raise ValueError('Snapshot transfer hash mismatch')
(a.output/'export_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
with tarfile.open(a.output/'snapshot.tar.gz')as t:t.extractall(a.output/'remote',filter='data')
subprocess.run([sys.executable,str(root/'scripts/compute/structure_campaign_collect.py'),'--output',str(a.output)],check=True)
if a.merge_output:subprocess.run([sys.executable,str(root/'scripts/compute/structure_campaign_merge.py'),'--output',str(a.merge_output)],check=True)
print(json.dumps({'snapshot_sha256':receipt['archive_sha256'],'counts':receipt['counts']}))
