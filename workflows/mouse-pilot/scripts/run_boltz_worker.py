"""One priced A100 worker; frozen inputs, independent deadline, copy and stop."""
import argparse
import datetime
import importlib.util
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time
import urllib.request


ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'runs/focused-pilot-20260919'
RUN=BASE/'folding-worker'
RESUME_FROM=None
DISK_GIB_BOUND=1200
NAME='chrna-boltz-20260919'
TYPE='a100-80gb.1x'
spec=importlib.util.spec_from_file_location('pilot_transport',ROOT/'scripts/run_pilot_worker.py')
transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
transport.RUN=RUN;transport.NAME=NAME


def save(name,record):transport.save(name,record)
def command(*args,**kwargs):return transport.command(*args,**kwargs)


def preflight():
    inventory=transport.inventory()
    allowed={'chrna-controller':('2gnfmgobs','cpu-e2.4vcpu-16gb',121),
             'chrna-pilot-cpu-20260919':('6k9lx0737','n2d-standard-16',150)}
    if RESUME_FROM is not None:
        shutdown=json.loads((RESUME_FROM/'shutdown-confirmed.json').read_text())
        original=json.loads((RESUME_FROM/'actual-launch.json').read_text())['instances']
        if shutdown['status']!='STOPPED' or len(original)!=1 or original[0]['name']!=NAME or original[0]['instance_type']!=TYPE:
            raise RuntimeError('Previous owned GPU attempt is not safely resumable')
        allowed[NAME]=(original[0]['id'],TYPE,DISK_GIB_BOUND)
        owned=[w for w in inventory if w['name']==NAME]
        if len(owned)!=1 or owned[0]['status']!='STOPPED':raise RuntimeError('Resume requires the existing owned GPU to be stopped')
    if 'chrna-controller' not in {w['name'] for w in inventory} or {w['name'] for w in inventory}-set(allowed):
        raise RuntimeError('Unpriced or already existing resource; reconcile before launch')
    for w in inventory:
        expected=allowed[w['name']]
        if (w['id'],w['instance_type'])!=expected[:2]:
            raise RuntimeError('Known project resource identity changed')
    request=urllib.request.Request(transport.URL,data=json.dumps({'options':{'includeCpu':True,'skipAccessFilter':False}}).encode(),
        headers={'Content-Type':'application/json','Connect-Protocol-Version':'1'})
    quotes=json.load(urllib.request.urlopen(request,timeout=60))
    save('launch-live-quotes.json',{'utc':transport.now(),'url':transport.URL,'response':quotes})
    save('launch-inventory.json',{'utc':transport.now(),'workspaces':inventory})
    resources=[(w['name'],w['instance_type'],allowed[w['name']][2]) for w in inventory if w['name']!=NAME]+[(NAME,TYPE,DISK_GIB_BOUND)]
    prices=[]
    for name,sku,disk in resources:
        rows=[q for q in quotes['items'] if q['type']==sku]
        if len(rows)!=1:raise RuntimeError('Quote missing or ambiguous: '+sku)
        q=rows[0]
        if sku==TYPE and (q['provider']!='crusoe' or not q.get('isAvailable') or not q.get('stoppable')):
            raise RuntimeError('Chosen GPU is unavailable or not stoppable')
        money=[q['basePrice'],*q.get('locationPrices',{}).values()]
        storage=[s.get('pricePerGbHr') for s in q['supportedStorage']]
        if not storage or any(not m or m.get('currency')!='USD' for m in money+storage):
            raise RuntimeError('Unknown currency or attached storage price')
        # Ceil GiB bytes to decimal GB is conservative for either billing convention.
        billed_units=math.ceil(disk*1024**3/10**9)
        rate=max(float(m['amount']) for m in money)+billed_units*max(float(m['amount']) for m in storage)
        prices.append({'name':name,'type':sku,'disk_gib_upper_bound':disk,'storage_billing_units_upper_bound':billed_units,
                       'usd_per_hour_upper_bound':rate,'quote':q})
    budget_spec=importlib.util.spec_from_file_location('budget',ROOT/'scripts/check_budget.py')
    budget=importlib.util.module_from_spec(budget_spec);budget_spec.loader.exec_module(budget)
    result=budget.check(json.loads((ROOT/'infra/budget-policy.json').read_text()),
        [p['usd_per_hour_upper_bound'] for p in prices[:-1]],prices[-1]['usd_per_hour_upper_bound'])
    save('launch-budget.json',{'utc':transport.now(),'currency':'USD','resources':prices,'check':result,
        'method':f'Maximum quoted regional compute and storage rates; existing stopped CPU charged as running conservatively. All visible GPU disks, including local NVMe, charged conservatively at the maximum quoted persistent-storage rate up to {DISK_GIB_BOUND} GiB.'})
    return result


def watchdog():
    lease=json.loads((RUN/'lease.json').read_text())
    while time.time()<lease['expires_epoch']:
        if (RUN/'shutdown-confirmed.json').exists():return
        time.sleep(min(20,lease['expires_epoch']-time.time()))
    stopped=transport.stop_owned()
    save('watchdog-stop.json',{'utc':transport.now(),'status':stopped})


def validate_inputs(inputs):
    manifest=json.loads((inputs/'manifest.json').read_text())
    if manifest['status']!='inputs_prepared_not_inferred' or not 1<=len(manifest['jobs'])<=11:
        raise RuntimeError('Expected frozen monomer batch of at most 10 recovered proteins plus one control')
    freeze_path=BASE/'selection/freeze.json'
    if hashlib.sha256(freeze_path.read_bytes()).hexdigest()!=manifest['selection_freeze_sha256']:
        raise RuntimeError('Selection freeze changed after folding input preparation')
    freeze=json.loads(freeze_path.read_text())
    if freeze['status']!='frozen':raise RuntimeError('Selection is not frozen')
    for name,sha in freeze['outputs'].items():
        if hashlib.sha256((freeze_path.parent/name).read_bytes()).hexdigest()!=sha:
            raise RuntimeError('Frozen artifact changed: '+name)
    msa_history={r['job_id']:r for r in json.loads((inputs/'msa-preparation.json').read_text())}
    verified_count=0
    for job in manifest['jobs']:
        msa=inputs/job['msa']
        if job['job_id'] in manifest.get('msa_unavailable_job_ids',[]):
            if msa_history[job['job_id']]['status']!='unavailable':raise RuntimeError('Undocumented MSA deferral')
            continue
        if not msa.is_file():raise RuntimeError('Prepare and verify every available MSA before GPU launch')
        receipt=json.loads(msa.with_suffix('.json').read_text())
        if receipt['sequence_sha256']!=job['sequence_sha256'] or hashlib.sha256(msa.read_bytes()).hexdigest()!=receipt['a3m_sha256']:
            raise RuntimeError('MSA receipt does not match input')
        config=json.loads((inputs/job['yaml']).read_text())
        if config!={'version':1,'sequences':[{'protein':{'id':'A','sequence':job['sequence'],'msa':job['msa']}}]}:
            raise RuntimeError('Boltz YAML differs from manifest')
        if hashlib.sha256(job['sequence'].encode()).hexdigest()!=job['sequence_sha256']:
            raise RuntimeError('Manifest sequence hash mismatch')
        verified_count+=1
    if not verified_count:raise RuntimeError('No verified MSA inputs; no useful GPU job')
    return manifest


def main(inputs):
    manifest=validate_inputs(inputs)
    if RUN.exists():raise RuntimeError('Existing folding attempt; inspect it instead of relaunching')
    RUN.mkdir()
    budget=preflight()
    transport.save('resume-provenance.json',{'prior_attempt':str(RESUME_FROM) if RESUME_FROM else None,
                   'disk_gib_upper_bound':DISK_GIB_BOUND,'action':'start existing owned GPU' if RESUME_FROM else 'create one GPU'})
    cutoff=datetime.datetime(2026,9,19,21,tzinfo=datetime.timezone.utc).timestamp()
    expiry=min(time.time()+3*3600,cutoff)
    if expiry-time.time()<3600:raise RuntimeError('Insufficient setup and bounded inference time')
    save('lease.json',{'name':NAME,'type':TYPE,'created_utc':transport.now(),'expires_epoch':expiry,
                       'controller_pid':os.getpid(),'budget':budget})
    with (RUN/'watchdog.log').open('w') as log:
        guard=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--watchdog','--attempt-dir',str(RUN)],
            stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
    save('watchdog.json',{'pid':guard.pid,'expires_epoch':expiry})
    state={'status':'starting','started_utc':transport.now(),'name':NAME}
    save('worker-controller.json',state)
    remote=None
    try:
        if RESUME_FROM is not None:
            command('start',['brev','start',NAME],timeout=960)
        else:
            command('create',['brev','create',NAME,'--type',TYPE,'--provider','crusoe','--count','1',
                             '--min-disk','150','--stoppable','--timeout','900','--jupyter=false'],timeout=960)
        ready=time.monotonic()+600
        while time.monotonic()<ready:
            current=[w for w in transport.inventory() if w['name']==NAME]
            save('actual-launch.json',{'utc':transport.now(),'instances':current})
            if current and current[0]['status']=='RUNNING' and current[0]['shell_status']=='READY' and current[0]['build_status']=='COMPLETED':break
            time.sleep(10)
        else:raise RuntimeError('GPU readiness deadline exceeded')
        if len(current)!=1 or current[0]['instance_type']!=TYPE:raise RuntimeError('Actual launch differs from priced GPU')
        transport.wait_for_ssh()
        remote_home=subprocess.check_output(['ssh','-T','-o','BatchMode=yes',NAME,
             "python3 -c 'from pathlib import Path; print(Path.home())'"],env=transport.transport_env(),text=True,timeout=30).strip()
        if not remote_home.startswith('/') or any(c not in '/_-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' for c in remote_home):
            raise RuntimeError('Unexpected remote home path')
        remote=remote_home+'/chrna-boltz'
        command('prepare',['brev','exec',NAME,f'mkdir -p {remote}/outputs'],timeout=60)
        command('hardware',['brev','exec',NAME,
            f"nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader; python3 -c 'import json,subprocess; d=json.loads(subprocess.check_output([\"lsblk\",\"-b\",\"-J\",\"-o\",\"NAME,SIZE,TYPE\"])); print(json.dumps(d)); assert sum(int(x[\"size\"]) for x in d[\"blockdevices\"] if x[\"type\"]==\"disk\")<={DISK_GIB_BOUND}*1024**3'"],timeout=60)
        bundle=RUN/'input-bundle.tar.gz'
        with tarfile.open(bundle,'w:gz') as archive:
            archive.add(inputs,arcname='inputs')
            archive.add(ROOT/'scripts/boltz_worker.py',arcname='boltz_worker.py')
            archive.add(ROOT/'scripts/setup_boltz_worker.sh',arcname='setup_boltz_worker.sh')
            preparation=BASE/'boltz-preparation'
            for name in ('boltz-2.2.1-py3-none-any.whl','weights-manifest.json'):
                archive.add(preparation/name,arcname='inputs/'+name)
        save('input-bundle.json',{'utc':transport.now(),'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),
            'bytes':bundle.stat().st_size,'selection_freeze_sha256':manifest['selection_freeze_sha256'],
            'source_hashes':{name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest()
                             for name in ('run_boltz_worker.py','boltz_worker.py','setup_boltz_worker.sh')}})
        command('copy-inputs',['brev','copy',str(bundle),f'{NAME}:{remote}/input-bundle.tar.gz'],timeout=300)
        command('setup',['brev','exec',NAME,f'cd {remote} && tar xzf input-bundle.tar.gz && timeout --signal=TERM --kill-after=30s 1200s bash setup_boltz_worker.sh'],timeout=1260)
        state['status']='inference';save('worker-controller.json',state)
        remaining=int(expiry-time.time()-420)
        if remaining<300:raise RuntimeError('Insufficient time after setup')
        command('inference',['brev','exec',NAME,
            f'cd {remote} && timeout --signal=TERM --kill-after=30s {remaining}s .venv/bin/python boltz_worker.py --inputs inputs --output outputs/predictions --cache cache --deadline-epoch {expiry-420}'],timeout=remaining+60)
        state['status']='batch_finished'
    except BaseException as error:
        state.update(status='failed',error=str(error),error_type=type(error).__name__)
        raise
    finally:
        try:
            if remote:command('preserve-outputs',['brev','copy',f'{NAME}:{remote}/outputs',str(RUN/'worker-outputs')],timeout=300,check=False)
        finally:
            state['finished_utc']=transport.now();save('worker-controller.json',state)
            stopped=transport.stop_owned()
            save('shutdown-confirmed.json',{'utc':transport.now(),'status':stopped,'name':NAME})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watchdog',action='store_true')
    parser.add_argument('--inputs',type=Path)
    parser.add_argument('--attempt-dir',type=Path,default=RUN)
    parser.add_argument('--resume-from',type=Path)
    args=parser.parse_args()
    RUN=args.attempt_dir.resolve();transport.RUN=RUN
    if not RUN.is_relative_to(BASE.resolve()):parser.error('Attempt directory must be within the focused run')
    RESUME_FROM=args.resume_from.resolve() if args.resume_from else None
    if args.watchdog:watchdog()
    else:
        if args.inputs is None:parser.error('--inputs is required')
        def interrupted(signum,frame):raise KeyboardInterrupt('Preserve outputs and stop owned GPU')
        signal.signal(signal.SIGTERM,interrupted)
        main(args.inputs.resolve())
