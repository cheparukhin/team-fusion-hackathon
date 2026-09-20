import pathlib,subprocess,sys,shutil,csv,json
R=pathlib.Path(__file__).resolve().parents[1];species=sys.argv[1]
ref=next(x for x in json.loads((R/'manifest/references.json').read_text()) if x['species']==species)
d=R/'reference'/species;ad=d/'adapted';out=d/'jaffal_input';out.mkdir(exist_ok=True)
build=ref['assembly'];annotation='ensembl115';prefix=build+'_'+annotation
gp=out/(prefix+'.genepred')
subprocess.run(['gtfToGenePred','-genePredExt','-geneNameAsName2',str(ad/'typhon.gtf'),str(gp)],check=True)
header=['name','chrom','strand','txStart','txEnd','cdsStart','cdsEnd','exonCount','exonStarts','exonEnds','score','name2','cdsStartStat','cdsEndStat','exonFrames']
with (out/(prefix+'.tab')).open('w') as tab,(out/(prefix+'.bed')).open('w') as bed:
 tab.write('\t'.join(header)+'\n')
 for line in gp.open():
  f=line.rstrip().split('\t');assert len(f)==15
  tab.write(line)
  for start,end in zip(f[8].strip(',').split(','),f[9].strip(',').split(',')):bed.write('\t'.join([f[1],start,end,f[0],'0',f[2]])+'\n')
# Plain native transcript IDs are supported by JAFFAL and match the table's name column.
shutil.copy2(ad/'native_transcripts.fa',out/(prefix+'.fasta'))
genome=d/ref['genome_url'].split('/')[-1]
link=out/(build+'.fa.gz')
if not link.exists():link.symlink_to(genome)
sys.path.insert(0,str(R/'software/TYPHON'));import setup_jaffal
# Species-specific copies prevent changing the genome setting for another running species.
source=R/'software/jaffal/JAFFA-version-2.3';install=R/'software/jaffal'/species
if not install.exists():shutil.copytree(source,install,symlinks=True)
(install/'references').mkdir(exist_ok=True)
setup_jaffal.update_jaffal_stages(str(install),build,annotation)
setup_jaffal.process_reference_files(str(install),str(out),build,annotation,8)
(out/'reference_ready.json').write_text(json.dumps({'species':species,'assembly':build,'annotation':annotation,'install':str(install),'native_gtf':str(ad/'typhon.gtf'),'coordinates':'genePred and BED 0-based half-open, converted by UCSC gtfToGenePred'},indent=2))
