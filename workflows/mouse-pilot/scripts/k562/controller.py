"""Own one bounded CPU lease, preserve results and stop; never alter other jobs."""
import argparse,datetime,hashlib,importlib.util,json,os,shlex,signal,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUN=ROOT/'runs/k562-pilot/20260919-overnight'
NAME='chrna-k562-cpu-20260919';TYPE='n2d-standard-16';REMOTE='/home/ubuntu/k562-external';ENV={**os.environ,'SHELL':'/bin/sh'}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,data):
 p=RUN/name;tmp=p.with_suffix(p.suffix+'.partial');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(p)
def inventory():return json.loads(subprocess.check_output(['brev','ls','--json'],env=ENV,text=True,timeout=60))['workspaces']
def command(label,args,timeout=120,check=True):
 print(now(),label,flush=True)
 with (RUN/(label+'.log')).open('a') as f:
  f.write(json.dumps({'utc':now(),'argv':args})+'\n');f.flush();r=subprocess.run(args,env=ENV,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 if check and r.returncode:raise RuntimeError(label+' exited '+str(r.returncode))
 return r.returncode

def priced_preflight():
 current=inventory();assert not any(x['name']==NAME for x in current),'New lease name already exists'
 url='https://api.brev.dev/devplaneapi.v1.InstanceService/ListPublicInstanceType'
 req=urllib.request.Request(url,data=json.dumps({'options':{'includeCpu':True,'skipAccessFilter':False}}).encode(),headers={'Content-Type':'application/json','Connect-Protocol-Version':'1'})
 quotes=json.load(urllib.request.urlopen(req,timeout=60));save('live-quotes.json',{'utc':now(),'url':url,'response':quotes});save('inventory-before.json',{'utc':now(),'instances':current})
 prices=[];items=[]
 for inst in current+[{'name':NAME,'instance_type':TYPE,'status':'PROPOSED'}]:
  qs=[x for x in quotes['items'] if x['type']==inst['instance_type']];assert len(qs)==1,'Unknown or ambiguous SKU';quote=qs[0]
  money=[quote['basePrice'],*quote.get('locationPrices',{}).values()]
  assert all(x['currency']=='USD' for x in money)
  compute=max(float(x['amount']) for x in money) if inst['status'] not in ('STOPPED','DELETED') else 0
  # Conservative maximum configurable single-disk bound for existing resources,
  # plus included fixed disk. New job requests 250 GiB and rejects >251 actual.
  disk=251 if inst['name']==NAME else {'n2d-standard-16':16384,'cpu-e2.4vcpu-16gb':2560,'a100-80gb.1x':10368,'denvr_A100_sxm4_80G':2125}.get(inst['instance_type'])
  assert disk is not None,'Storage inventory not priced'
  storage=[x['pricePerGbHr'] for x in quote.get('supportedStorage',[]) if 'pricePerGbHr' in x]
  if storage:
   assert all(x['currency']=='USD' for x in storage);disk_rate=disk*max(float(x['amount']) for x in storage)
  else:
   assert inst['instance_type']=='denvr_A100_sxm4_80G' and all(x.get('size') not in ('0B',None) and not x.get('maxSize') for x in quote['supportedStorage'])
   disk_rate=0 # fixed included disk in this provider's instance quote, no configurable storage
  item={'name':inst['name'],'id':inst.get('id'),'sku':inst['instance_type'],'status':inst['status'],'currency':'USD','compute_per_hour':compute,'storage_bound_gib':disk,'storage_per_hour_bound':disk_rate,'usd_per_hour_bound':compute+disk_rate};items.append(item);prices.append(compute+disk_rate)
 spec=importlib.util.spec_from_file_location('budget',ROOT/'scripts/check_budget.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 check=module.check(json.loads((ROOT/'infra/budget-policy.json').read_text()),prices[:-1],prices[-1])
 assert prices[-1]*8<=20,'Incremental eight-hour compute cap exceeded'
 assert sum(prices)*8<=500,'Total credits reserve insufficient at conservative project rates'
 receipt={'utc':now(),'resources':items,'check':check,'new_job_max_hours':8,'new_job_compute_ceiling_usd':prices[-1]*8,'new_job_incremental_cap_usd':20,'remaining_credit_ceiling_usd':500,'all_visible_resources_eight_hour_bound_usd':sum(prices)*8,'note':'Rate arithmetic is not provider enforcement. Existing instances remain untouched. Existing variable storage priced conservatively up to one provider-max root volume; known project receipts show smaller disks. Public ingress and result egress are not included in compute quote; incremental cap retains headroom. New instance stopped automatically, then deleted only after verified result preservation.'}
 save('budget.json',receipt);return receipt

def stop_owned():
 lease=json.loads((RUN/'lease.json').read_text())
 for attempt in range(20):
  xs=[x for x in inventory() if x['name']==NAME]
  if not xs:return 'ABSENT'
  x=xs[0]
  if lease.get('instance_id') and x['id']!=lease['instance_id']:raise RuntimeError('Ownership identity changed; refusing mutation')
  if x['status'] in ('STOPPED','DELETED'):return x['status']
  command('stop-owned',['brev','stop',NAME],120,False);time.sleep(10)
 raise RuntimeError('Shutdown not confirmed')

def watchdog():
 lease=json.loads((RUN/'lease.json').read_text())
 while time.time()<lease['expires_epoch']:
  if (RUN/'shutdown.json').exists():return
  time.sleep(15)
 status=stop_owned();save('watchdog-shutdown.json',{'utc':now(),'status':status})

def main():
 if (RUN/'lease.json').exists():raise RuntimeError('Lease exists: inspect before resuming')
 budget=priced_preflight();start=time.time();lease={'name':NAME,'created_utc':now(),'controller_pid':os.getpid(),'expires_epoch':start+8*3600,'instance_id':None,'incremental_cap_usd':20};save('lease.json',lease)
 with (RUN/'watchdog.log').open('a') as f:
  guard=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--watchdog'],env=ENV,stdin=subprocess.DEVNULL,stdout=f,stderr=f,start_new_session=True)
 save('watchdog.json',{'pid':guard.pid,'expires_epoch':lease['expires_epoch']})
 state={'status':'provisioning','utc':now()};save('controller.json',state);prepared=False;preserved=False
 try:
  command('create',['brev','create',NAME,'--type',TYPE,'--provider','gcp','--count','1','--min-disk','250','--stoppable','--timeout','900','--jupyter=false'],960)
  deadline=time.time()+600
  while time.time()<deadline:
   xs=[x for x in inventory() if x['name']==NAME]
   if xs:
    lease['instance_id']=xs[0]['id'];save('lease.json',lease)
    if xs[0]['status']=='RUNNING' and xs[0]['shell_status']=='READY':break
   time.sleep(10)
  else:raise RuntimeError('Worker readiness timeout')
  actual=xs[0];save('actual-launch.json',actual);assert actual['instance_type']==TYPE,'Unpriced fallback instance'
  command('refresh',['brev','refresh'],90)
  for trial in range(8):
   if command('ssh-ready',['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15',NAME,'true'],25,False)==0:break
   time.sleep(10)
  else:raise RuntimeError('SSH readiness failed')
  hardware="python3 -c 'import json,subprocess,os; x=json.loads(subprocess.check_output([\"lsblk\",\"-b\",\"-J\",\"-o\",\"NAME,SIZE,TYPE\"])); print(json.dumps(x)); assert sum(int(d[\"size\"]) for d in x[\"blockdevices\"] if d[\"type\"]==\"disk\") <= 251*1024**3; assert os.cpu_count() >= 14; print(subprocess.check_output([\"free\",\"-b\"],text=True))'"
  command('actual-hardware',['brev','exec',NAME,hardware],120)
  command('mkdir',['brev','exec',NAME,'mkdir -p '+REMOTE],120)
  command('copy-bundle',['brev','copy',str(RUN/'bundle.tar.gz'),NAME+':'+REMOTE+'/bundle.tar.gz'],300)
  command('unpack',['brev','exec',NAME,'cd '+REMOTE+' && tar xzf bundle.tar.gz && sha256sum -c source.sha256'],120);prepared=True
  state.update(status='running',utc=now());save('controller.json',state)
  remaining=int(lease['expires_epoch']-time.time()-1200)
  command('workflow',['brev','exec',NAME,f'cd {REMOTE} && timeout --signal=TERM --kill-after=60s {remaining}s python3 -u worker.py'],remaining+120)
  state.update(status='workflow_finished',utc=now())
 except BaseException as e:
  state.update(status='failed',utc=now(),error_type=type(e).__name__,error=str(e))
 finally:
  try:
   if prepared:
    # Raw inputs and full primary BAMs are reproducible; preserve all split-read
    # evidence, metadata, logs and reports locally before deleting our own VM.
    command('pack-results',['brev','exec',NAME,f'cd {REMOTE} && tar --exclude=name.bam --exclude=read_identity.sqlite -czf results.tar.gz outputs && sha256sum results.tar.gz > results.sha256'],600,False)
    rc=command('copy-results',['brev','copy',NAME+':'+REMOTE+'/results.tar.gz',str(RUN/'results.tar.gz')],600,False)
    rc2=command('copy-result-hash',['brev','copy',NAME+':'+REMOTE+'/results.sha256',str(RUN/'results.sha256')],120,False)
    if rc==rc2==0:
     expected=(RUN/'results.sha256').read_text().split()[0];h=hashlib.sha256()
     with (RUN/'results.tar.gz').open('rb') as f:
      for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
     assert h.hexdigest()==expected,'Result transfer checksum mismatch'
     command('unpack-results',['tar','xzf',str(RUN/'results.tar.gz'),'-C',str(RUN)],120)
     preserved=True;save('preservation.json',{'utc':now(),'sha256':expected,'status':'verified','excluded':'Primary BAM and UUID database omitted; supporting FASTQ/SAM, decisions, source hashes and all report artifacts preserved. Raw public inputs reproducible.'})
  except BaseException as e:state['preservation_error']=str(e)
  finally:
   state['elapsed_seconds']=time.time()-start;state['results_preserved']=preserved;save('controller.json',state)
   stopped=stop_owned();save('shutdown.json',{'utc':now(),'name':NAME,'instance_id':lease.get('instance_id'),'status':stopped})
   if preserved:
    xs=[x for x in inventory() if x['name']==NAME]
    if xs and xs[0]['id']==lease['instance_id'] and xs[0]['status']=='STOPPED':
     rc=command('delete-owned-after-preservation',['brev','delete',NAME],120,False)
     remaining=[x for x in inventory() if x['name']==NAME]
     save('teardown.json',{'utc':now(),'delete_exit_code':rc,'only_new_owned_instance':NAME,'results_preserved':True,'remaining_status':[x['status'] for x in remaining]})
   save('resource-accounting.json',{'utc':now(),'wall_hours':(time.time()-start)/3600,'quoted_compute_upper_bound_usd':(time.time()-start)/3600*budget['resources'][-1]['usd_per_hour_bound'],'incremental_cap_usd':20,'shutdown':stopped,'credits_ceiling_usd':500,'other_instances_modified':False})
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--watchdog',action='store_true');args=parser.parse_args()
 if args.watchdog:watchdog()
 else:
  def interrupted(sig,frame):raise KeyboardInterrupt('Controller interrupted; preserving and stopping owned worker')
  signal.signal(signal.SIGTERM,interrupted);main()
