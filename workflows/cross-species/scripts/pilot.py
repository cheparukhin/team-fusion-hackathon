import pathlib,json,subprocess,yaml,shutil,datetime
R=pathlib.Path(__file__).resolve().parents[1]
refs={x['species']:x for x in json.loads((R/'manifest/references.json').read_text())}
for species,run in [('homo_sapiens','SRR31438987'),('bos_taurus','SRR31429688')]:
 ref=refs[species];d=R/'reference'/species;adapter=d/'adapted';out=R/'per_species'/species/run
 genome=d/ref['genome_url'].split('/')[-1][:-3];gtf=d/ref['gtf_url'].split('/')[-1][:-3]
 if not (adapter/'adapter_qc.json').exists():subprocess.run(['python',str(R/'scripts/adapt_reference.py'),str(genome),str(gtf),str(adapter)],check=True)
 fq=R/'raw'/run/'filtered'/(run+'.fastq.gz')
 if not fq.exists():subprocess.run(['python',str(R/'scripts/filter_fastq.py'),str(R/'raw'/run/(run+'.fastq.gz')),str(fq)],check=True)
 config=yaml.safe_load((R/'software/TYPHON/config_template.yaml').read_text());config['project'].update(name=species+'_'+run,output_dir=str(out),threads=14)
 config['input']['fastq_dir']=str(fq.parent);config['references']={'genome':str(genome),'gtf':str(adapter/'typhon.gtf'),'transcriptome':str(adapter/'typhon_transcripts.fa')}
 config['modules']['longgf']['keep_intermediate']=True
 config['modules']['longgf']['output_flag']=16
 config['modules']['genion'].update(enabled=False,output_bin_dir=str(R/'software/TYPHON/bin'))
 config['modules']['jaffal']['enabled']=False
 config['options'].update(enable_integration=False,cleanup_intermediate=False,temp_dir=str(R/'scratch'))
 config['options']['exon_repair']['bam_file']=str(out/'longgf_results'/(run+'.bam'))
 (R/'scratch').mkdir(exist_ok=True);out.mkdir(parents=True,exist_ok=True)
 path=out/'config.yaml';path.write_text(yaml.safe_dump(config))
 if shutil.disk_usage(R).free<40*1024**3:raise RuntimeError('Insufficient free scratch disk')
 with (out/'execution.log').open('a') as log:
  rc=subprocess.run(['python',str(R/'software/TYPHON/typhon_main.py'),'--config',str(path),'--modules','longgf'],stdout=log,stderr=subprocess.STDOUT).returncode
 (out/'execution_status.json').write_text(json.dumps({'step':'TYPHON LongGF pilot','returncode':rc,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'other_callers':'pending; not negative','conservation':'not evaluated'},indent=2))
 if rc:raise RuntimeError(f'{species} caller failed; inspect log')
