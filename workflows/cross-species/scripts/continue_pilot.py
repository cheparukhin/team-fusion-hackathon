import pathlib,json,time,subprocess,shutil,sys,yaml,datetime
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'software/TYPHON'))
from typhon.modules.postprocess import postprocess
for species,run in [('homo_sapiens','SRR31438987'),('bos_taurus','SRR31429688')]:
 out=R/'per_species'/species/run;status=out/'execution_status.json'
 while not status.exists():time.sleep(15)
 first=json.loads(status.read_text())
 if first['returncode']:raise RuntimeError('LongGF pilot failed: '+str(status))
 config=yaml.safe_load((out/'config.yaml').read_text());lg=out/'longgf_results'
 # Correct the demonstrated last-read edge case before interpreting support counts.
 if config['modules']['longgf'].get('output_flag',0)!=16:
  archive=out/'default_flag_archive';archive.mkdir(exist_ok=True)
  for p in lg.iterdir():
   if p.suffix in ['.log','.txt','.csv','.xlsx']:shutil.copy2(p,archive/p.name)
  with (lg/(run+'.log')).open('w') as log:
   subprocess.run(['LongGF',str(lg/(run+'_sorted.bam')),config['references']['gtf'],'100','50','100','2','0','1','16'],check=True,stdout=log,stderr=subprocess.STDOUT)
  postprocess(str(lg));config['modules']['longgf']['output_flag']=16
 config['modules']['genion']['enabled']=True;config['modules']['genion']['threads']=6;config['project']['threads']=6
 config['options']['enable_integration']=False
 cp=out/'continuation_config.yaml';cp.write_text(yaml.safe_dump(config))
 with (out/'genion_execution.log').open('w') as log:
  rc=subprocess.run(['python',str(R/'software/TYPHON/typhon_main.py'),'--config',str(cp),'--modules','genion'],stdout=log,stderr=subprocess.STDOUT).returncode
 (out/'genion_status.json').write_text(json.dumps({'returncode':rc,'status':'complete' if rc==0 else 'failed; not negative'},indent=2))
 if rc:raise RuntimeError('Genion failed; review '+str(out))
 ready=R/'reference'/species/'jaffal_input/reference_ready.json'
 while not ready.exists():time.sleep(15)
 ref=json.loads(ready.read_text());ja=config['modules']['jaffal'];ja.update(enabled=True,jaffal_dir=ref['install'],genome_build=ref['assembly'],annotation=ref['annotation'],threads=6)
 config['options']['enable_integration']=True;config['options']['exon_repair']['enabled']=True
 cp.write_text(yaml.safe_dump(config))
 with (out/'jaffal_integration_execution.log').open('w') as log:
  rc=subprocess.run(['python',str(R/'software/TYPHON/typhon_main.py'),'--config',str(cp),'--modules','jaffal'],stdout=log,stderr=subprocess.STDOUT).returncode
 (out/'integration_status.json').write_text(json.dumps({'returncode':rc,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'requires output validation' if rc==0 else 'failed; not negative','conservation':'not evaluated'},indent=2))
 if rc:raise RuntimeError('JAFFAL/integration failed; inspect '+str(out))
