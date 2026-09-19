"""One owned CPU worker: live priced launch, bounded pilot, copy outputs, stop.

No retries of provisioning. A separate process independently enforces the lease.
Never touches existing resources except reading the shared controller inventory.
"""
import datetime
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'runs/focused-pilot-20260919'
RUN = BASE
NAME = 'chrna-pilot-cpu-20260919'
TYPE = 'n2d-standard-16'
REMOTE = '/home/ubuntu/workspace/chrna-pilot'
URL = 'https://api.brev.dev/devplaneapi.v1.InstanceService/ListPublicInstanceType'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(name, value):
    path = RUN / name
    tmp = path.with_suffix(path.suffix + '.partial')
    with tmp.open('w') as out:
        json.dump(value, out, indent=2)
        out.write('\n')
        out.flush()
        os.fsync(out.fileno())
    tmp.replace(path)


def transport_env():
    # OpenSSH Match exec uses SHELL. Service accounts may inherit nologin,
    # which silently prevents Brev certificate matching and alias resolution.
    return {**os.environ, "SHELL": "/bin/sh"}


def wait_for_ssh(timeout=180):
    deadline = time.monotonic() + timeout
    attempt = 0
    while time.monotonic() < deadline:
        attempt += 1
        command(f"ssh-refresh-{attempt}", ["brev", "refresh"], timeout=60)
        try:
            code = command(f"ssh-probe-{attempt}",
                ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", NAME, "true"],
                timeout=25, check=False)
            if code == 0:
                save("ssh-ready.json", {"utc": now(), "attempt": attempt, "shell": "/bin/sh", "status": "connected"})
                return
        except subprocess.TimeoutExpired:
            pass
        time.sleep(5)
    raise RuntimeError("Worker API ready but SSH connection did not succeed within bounded timeout")


def command(label, argv, timeout=120, check=True):
    print(now(), label, flush=True)
    with (RUN / (label+'.log')).open('a') as out:
        out.write(json.dumps({'utc':now(), 'argv':argv})+'\n')
        out.flush()
        result = subprocess.run(argv, stdout=out, stderr=subprocess.STDOUT, timeout=timeout, env=transport_env())
    if check and result.returncode:
        raise RuntimeError(f'{label} exited {result.returncode}')
    return result.returncode


def inventory():
    return json.loads(subprocess.check_output(['brev','ls','--json'], text=True, timeout=60, env=transport_env()))['workspaces']


def stop_owned():
    for attempt in range(15):
        current = [x for x in inventory() if x['name'] == NAME]
        if not current:
            return 'absent'
        if current[0]['status'] in ('STOPPED', 'DELETED'):
            return current[0]['status']
        # The launch name was absent in the persisted preflight inventory.
        command('stop', ['brev','stop',NAME], timeout=90, check=False)
        time.sleep(10)
    raise RuntimeError('Owned worker stop not confirmed; watchdog remains responsible')


def watchdog():
    lease = json.loads((RUN/'lease.json').read_text())
    while time.time() < lease['expires_epoch']:
        if (RUN/'shutdown-confirmed.json').exists():
            return
        time.sleep(min(20, max(0, lease['expires_epoch']-time.time())))
    # Outputs already live in the persistent workspace, even if a local copy fails.
    status = stop_owned()
    save('watchdog-stop.json', {'utc':now(), 'status':status})


def preflight():
    current = inventory()
    controllers = [x for x in current if x['name']=='chrna-controller']
    workers = [x for x in current if x['name']==NAME]
    if len(controllers)!=1 or controllers[0]['instance_type']!='cpu-e2.4vcpu-16gb' or len(current)!=len(controllers)+len(workers):
        raise RuntimeError('Inventory changed; price every existing project resource before proceeding')
    if workers:
        if RUN==BASE or not (BASE/'shutdown-confirmed.json').exists():
            raise RuntimeError('Prior owned lease must be terminal before resuming this worker')
        original=json.loads((BASE/'actual-launch.json').read_text())['instances'][0]
        if len(workers)!=1 or workers[0]['id']!=original['id'] or workers[0]['instance_type']!=TYPE:
            raise RuntimeError('Existing worker ownership or type changed')
    req = urllib.request.Request(URL, data=json.dumps({'options':{'includeCpu':True,'skipAccessFilter':False}}).encode(), headers={'Content-Type':'application/json','Connect-Protocol-Version':'1'})
    with urllib.request.urlopen(req,timeout=60) as response:
        quotes = json.load(response)
    save('launch-live-quotes.json', {'utc':now(),'url':URL,'response':quotes})
    save('launch-inventory.json', {'utc':now(),'workspaces':current})
    selected = {}
    rates = []
    for sku, disk in [('cpu-e2.4vcpu-16gb',121), (TYPE,150)]:
        matches = [q for q in quotes['items'] if q['type']==sku]
        if len(matches)!=1:
            raise RuntimeError('Ambiguous or missing quote')
        quote = matches[0]
        money = [quote['basePrice'], *quote.get('locationPrices',{}).values()]
        storage = [s['pricePerGbHr'] for s in quote['supportedStorage']]
        if any(x.get('currency')!='USD' for x in money+storage):
            raise RuntimeError('Currency not USD')
        rate = max(float(x['amount']) for x in money) + disk*max(float(x['amount']) for x in storage)
        rates.append(rate)
        selected[sku] = {'disk_gib_upper_bound':disk,'usd_per_hour_upper_bound':rate,'quote':quote}
    spec = importlib.util.spec_from_file_location('budget', ROOT/'scripts/check_budget.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.check(json.loads((ROOT/'infra/budget-policy.json').read_text()), rates[:1], rates[1])
    save('launch-budget.json', {'utc':now(),'currency':'USD','calculation':'Maximum quoted region and storage-class rate; controller disk observed as 120 GiB plus 1 MiB, rounded up to 121 GiB. Worker requested 150 GiB. Recheck actual instance type and disk after launch.','resources':selected,'check':result})
    return result


def main():
    RUN.mkdir(exist_ok=True)
    if (RUN/'lease.json').exists():
        raise RuntimeError('Lease already exists: inspect actual worker state, do not relaunch')
    assert (BASE/'tools-and-script.tar.gz').exists()
    budget = preflight()
    cutoff = datetime.datetime(2026,9,19,21,tzinfo=datetime.timezone.utc).timestamp()
    expiry = min(time.time()+5400, cutoff)
    if expiry-time.time()<4500:
        raise RuntimeError('Insufficient bounded time for this job before compute cutoff')
    save('lease.json', {'created_utc':now(),'name':NAME,'type':TYPE,'expires_epoch':expiry,'maximum_seconds':5400,'controller_pid':os.getpid(),'budget':budget})
    with (RUN/'watchdog.log').open('a') as log:
        guard = subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--watchdog','--attempt-directory',str(RUN)], stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
    save('watchdog.json',{'pid':guard.pid,'started_utc':now(),'expires_epoch':expiry})
    started = time.time()
    state = {'started_utc':now(),'status':'starting','name':NAME,'goal_scope':'focused pilot; minimap2/LongGF plus split-read mapping audit'}
    save('worker-controller.json',state)
    remote_prepared=False
    try:
        if RUN==BASE:
            command('create',['brev','create',NAME,'--type',TYPE,'--provider','gcp','--count','1','--min-disk','150','--stoppable','--timeout','900','--jupyter=false'],timeout=960)
        else:
            command('start',['brev','start',NAME],timeout=960)
        ready_deadline=time.monotonic()+600
        while time.monotonic()<ready_deadline:
            observed=[x for x in inventory() if x['name']==NAME]
            save('readiness.json',{'utc':now(),'instances':observed})
            if observed and observed[0]['status']=='RUNNING' and observed[0]['shell_status']=='READY' and observed[0]['build_status']=='COMPLETED':
                break
            time.sleep(10)
        else:
            raise RuntimeError('Worker did not reach shell/build readiness within 10 minutes')
        actual = [x for x in inventory() if x['name']==NAME]
        save('actual-launch.json', {'utc':now(),'instances':actual})
        if len(actual)!=1 or actual[0]['instance_type']!=TYPE or actual[0]['status']!='RUNNING':
            raise RuntimeError('Actual launch does not match priced SKU or is not running')
        wait_for_ssh()
        command('prepare-remote',['brev','exec',NAME,f'mkdir -p {REMOTE}/inputs {REMOTE}/outputs'],timeout=120)
        remote_prepared=True
        command('actual-hardware',['brev','exec',NAME,"python3 -c 'import json,subprocess; x=json.loads(subprocess.check_output([\"lsblk\",\"-b\",\"-J\",\"-o\",\"NAME,SIZE,TYPE\"])); print(json.dumps(x)); assert sum(int(d[\"size\"]) for d in x[\"blockdevices\"] if d[\"type\"]==\"disk\") <= 151*1024**3'"],timeout=120)
        sources = [ROOT/'data/raw/fastq/SRR28984805.fastq', *[ROOT/'data/references/gencode_M28'/n for n in ('GRCm39.primary_assembly.genome.fa.gz','gencode.vM28.annotation.gtf.gz','gencode.vM28.transcripts.fa.gz')]]
        command('copy-tools',['brev','copy',str(BASE/'tools-and-script.tar.gz'),f'{NAME}:{REMOTE}/tools-and-script.tar.gz'],timeout=180)
        for i, source in enumerate(sources):
            command(f'copy-input-{i}',['brev','copy',str(source),f'{NAME}:{REMOTE}/inputs/{source.name}'],timeout=600)
        command('unpack',['brev','exec',NAME,f'cd {REMOTE} && tar xzf tools-and-script.tar.gz'],timeout=120)
        state['status']='running'
        save('worker-controller.json',state)
        command('discovery',['brev','exec',NAME,f'timeout --signal=TERM --kill-after=30s 3600s bash {REMOTE}/worker.sh'],timeout=3660)
        state['status']='succeeded'
    except BaseException as error:
        state.update(status='failed', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        try:
            if remote_prepared:
                command('preserve-outputs',['brev','copy',f'{NAME}:{REMOTE}/outputs',str(RUN/'worker-outputs')],timeout=600,check=False)
        finally:
            state['finished_utc']=now()
            state['wall_seconds']=time.time()-started
            save('worker-controller.json',state)
            stopped=stop_owned()
            save('shutdown-confirmed.json',{'utc':now(),'name':NAME,'status':stopped,'outputs':'worker-outputs; if copy failed, preserved on stopped persistent workspace'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watchdog',action='store_true')
    parser.add_argument('--attempt-directory',type=Path,default=BASE)
    args=parser.parse_args()
    RUN=args.attempt_directory.resolve()
    if args.watchdog:
        watchdog()
    else:
        def interrupted(signum, frame):
            raise KeyboardInterrupt('Controller interrupted; preserve outputs and stop worker')
        signal.signal(signal.SIGTERM, interrupted)
        main()
