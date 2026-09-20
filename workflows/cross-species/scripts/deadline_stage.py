import pathlib,json,sys,time,subprocess,yaml,shutil,logging,datetime
R=pathlib.Path(__file__).resolve().parents[1];species,run,stage=sys.argv[1:4];out=R/'per_species'/species/run;sys.path.insert(0,str(R/'software/TYPHON'));limit=json.loads((R/'qc/deadline.json').read_text())['calls_cutoff_epoch'];logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
cfg=yaml.safe_load((out/'config.yaml').read_text());cfg['project']['threads']=4;cfg['options']['enable_integration']=False
status=out/(stage+'_deadline_status.json')
try:
 if stage=='cow_longgf':
  from typhon.modules.postprocess import postprocess
  lg=out/'longgf_results';archive=out/'default_flag_archive';archive.mkdir(exist_ok=True)
  for p in lg.iterdir():
   if p.suffix in ['.log','.csv','.xlsx','.txt']:shutil.copy2(p,archive/p.name)
  with (lg/(run+'.log')).open('w') as f:subprocess.run(['LongGF',str(lg/(run+'_sorted.bam')),cfg['references']['gtf'],'100','50','100','2','0','1','16'],stdout=f,stderr=subprocess.STDOUT,check=True)
  postprocess(str(lg));subprocess.run(['python',str(R/'scripts/normalize_longgf.py'),species,run],check=True)
 elif stage=='jaffal':
  ready=R/'reference'/species/'jaffal_input/reference_ready.json'
  while not ready.exists():
   if time.time()>=limit:raise TimeoutError('Reference not ready before caller cutoff')
   time.sleep(10)
  ref=json.loads(ready.read_text());cfg['modules']['jaffal'].update(enabled=True,jaffal_dir=ref['install'],genome_build=ref['assembly'],annotation=ref['annotation'],threads=4)
  from typhon.modules.run_jaffal import run_jaffal
  result=run_jaffal(cfg['input']['fastq_dir'],ref['install'],str(out),threads=4,keep_intermediate=True,config=cfg)
  assert pathlib.Path(result['combined_results']).exists()
 elif stage=='genion':
  from typhon.utils.genion_reference import prepare_genion_reference_files
  from typhon.modules.run_genion import run_genion
  refs=prepare_genion_reference_files(cfg['references']['gtf'],cfg['references']['transcriptome'],str(out/'genion_references'),threads=4,reference_type='ensembl')
  run_genion(str(R/'raw'/run/'filtered'/(run+'.fastq.gz')),str(out/'longgf_results'/(run+'.sam')),*refs,str(out/'genion_results'),threads=4,keep_intermediate=True,min_support=1)
  assert (out/'genion_results'/(run+'_genion.tsv')).exists()
 elif stage=='reconstruct_longgf':
  if species=='bos_taurus':
   check=out/'cow_longgf_deadline_status.json'
   while not check.exists():
    if time.time()>=limit:raise TimeoutError('Corrected cow calls not ready')
    time.sleep(5)
   assert json.loads(check.read_text())['status']=='complete'
  import pandas as pd
  from typhon.modules.exon_repair import DataIntegrator,BlastSetupProcessor,TranscriptSelector,SequenceReconstructor
  from typhon.modules.exon_repair.exon_data_processing import run_phase4_exon_processing
  work=out/'reconstruction_longgf_only';work.mkdir(exist_ok=True);cfg['project']['output_dir']=str(work)
  cfg['options']['exon_repair']['bam_file']=str(out/'longgf_results'/(run+'.bam'))
  class LongGFOnly(DataIntegrator):
   def _validate_input_files(self,longgf_file,genion_dir,jaffal_file):
    if not pathlib.Path(longgf_file).exists():raise FileNotFoundError(longgf_file)
   def _load_genion_results(self,path):return pd.DataFrame(columns=['Read_ID','Chimera_ID'])
   def _load_jaffal_results(self,path):return pd.DataFrame(columns=['Read_ID','Chimera_ID'])
  integrator=LongGFOnly(cfg,str(work));library=integrator.integrate_tool_data(longgf_file=str(out/'longgf_results/Combined_LongGF_chimera_results_total.csv'),genion_dir='NOT_INCLUDED',jaffal_file='NOT_INCLUDED')
  p2=BlastSetupProcessor(cfg,str(work)).setup_blast_analysis(library)
  p3=TranscriptSelector(cfg,str(work)).analyze_and_select_transcripts(library,p2)
  p4=run_phase4_exon_processing(p3['selected_transcripts_with_order'],p2['transcript_metadata']['exons_bed'],integrator.work_dir,cfg)
  p5=SequenceReconstructor(cfg,str(work)).reconstruct_sequences(p4,library)
  (work/'result.json').write_text(json.dumps({'status':'completed; reference-assisted models require review','caller_scope':'LongGF only','Genion':'not included; unavailable is not negative','JAFFAL':'not included; unavailable is not negative','statistics':p5['statistics'],'fasta':p5['reconstructed_sequences'],'table':p5['final_chimeras_path']},indent=2,default=str))
 else:raise ValueError(stage)
 status.write_text(json.dumps({'stage':stage,'status':'complete','finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
except Exception as e:
 status.write_text(json.dumps({'stage':stage,'status':'failed or cutoff; not a biological negative','error':str(e),'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2));raise
