"""Bounded K562 CPU workflow; source/config hashes are frozen by controller."""
import concurrent.futures,datetime,gzip,hashlib,json,os,shlex,shutil,sqlite3,subprocess,sys,time,urllib.request
from pathlib import Path
BASE=Path(__file__).resolve().parent;os.chdir(BASE);sys.path.insert(0,str(BASE/'src'))
from chrna.pilot_assessment import assess
from chrna.k562 import report
CFG=json.loads((BASE/'config.json').read_text());OUT=BASE/'outputs';LOG=OUT/'logs';INPUT=BASE/'inputs';REF=BASE/'reference'
for p in [OUT,LOG,INPUT,REF]:p.mkdir(exist_ok=True)
ENV={**os.environ,'PATH':str(BASE/'tools/bin')+':'+os.environ['PATH'],'LD_LIBRARY_PATH':str(BASE/'tools/lib'),'PYTHONPATH':str(BASE/'src')}
THREADS=str(CFG['threads']);START=time.time()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.partial');tmp.write_text(json.dumps(d,indent=2)+'\n');tmp.replace(p)
def sha(p,algorithm='sha256'):
 h=hashlib.new(algorithm)
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def status(stage,**more):save(OUT/'status.json',{'stage':stage,'utc':now(),'elapsed_seconds':time.time()-START,**more});print(now(),stage,flush=True)
def cmd(name,args,timeout=7200):
 if isinstance(args,str):args=['bash','-o','pipefail','-c',args]
 with (LOG/(name+'.log')).open('a') as log:
  log.write(json.dumps({'utc':now(),'argv':args})+'\n');log.flush();subprocess.run(args,env=ENV,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=timeout)
def q(p):return shlex.quote(str(p))
def download(url,path,md5=None):
 path=Path(path)
 if not path.exists():cmd('download-'+path.name,['curl','--fail','--location','--retry','3','--connect-timeout','30','--max-time','3600','--output',str(path)+'.partial',url],timeout=3650);Path(str(path)+'.partial').replace(path)
 if md5 and sha(path,'md5')!=md5:raise ValueError('Provider MD5 mismatch: '+str(path))
 receipt={'url':url,'file':str(path.relative_to(BASE)),'bytes':path.stat().st_size,'sha256':sha(path),'provider_md5':md5,'utc':now()};save(OUT/'provenance'/(path.name+'.json'),receipt);return receipt

def fqrecords(path):
 opener=gzip.open if str(path).endswith('.gz') else open
 with opener(path,'rt') as f:
  while True:
   h=f.readline()
   if not h:break
   seq=f.readline().rstrip();plus=f.readline();qual=f.readline().rstrip()
   if not h.startswith('@') or not plus.startswith('+') or len(seq)!=len(qual) or not seq:raise ValueError('Malformed FASTQ: '+str(path))
   yield h[1:].split()[0],seq,qual

def prepare_references():
 status('references')
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(download,r['url'],REF/r['name'],r['md5']) for r in CFG['references']]
  for f in futures:f.result()
 for n in CFG['sequin_files']:
  download('https://raw.githubusercontent.com/XueyiDong/LongReadRNA/'+CFG['sequin_commit']+'/sequins/annotations/'+n,REF/n)
 for source,dest,sequin in [('GRCh38.primary_assembly.genome.fa.gz','genome.fa','rnasequin_decoychr_2.4.fa'),('gencode.v43.transcripts.fa.gz','transcripts.fa','rnasequin_sequences_2.4.fa')]:
  with (REF/dest).open('wb') as out:
   with gzip.open(REF/source,'rb') as src:shutil.copyfileobj(src,out)
   out.write(b'\n');out.write((REF/sequin).read_bytes());out.write(b'\n')
 with gzip.open(REF/'gencode.v43.annotation.gtf.gz','rb') as src,(REF/'annotation.gtf').open('wb') as out:shutil.copyfileobj(src,out)
 cmd('fasta-index',['samtools','faidx',str(REF/'genome.fa')],300)
 contigs={x.split('\t')[0]:int(x.split('\t')[1]) for x in (REF/'genome.fa.fai').read_text().splitlines()}
 assert sum(contigs.values())<4_000_000_000,'Single-part genome index required'
 annotation_contigs=set()
 for line in (REF/'annotation.gtf').open():
  if not line.startswith('#'):annotation_contigs.add(line.split('\t')[0])
 assert annotation_contigs<=contigs.keys(),annotation_contigs-contigs.keys()
 save(OUT/'reference_audit.json',{'genome_sha256':sha(REF/'genome.fa'),'transcript_sha256':sha(REF/'transcripts.fa'),'annotation_sha256':sha(REF/'annotation.gtf'),'contigs':contigs,'annotation_contigs':sorted(annotation_contigs),'spikein_quarantine':'sequin contigs have no human gene annotation; unassigned/mixed segments retained, not human candidates'})
 cmd('minimap-index',['minimap2','-x','splice','-k14','-I4G','-t',THREADS,'-d',str(REF/'genome.mmi'),str(REF/'genome.fa')],1800)

def intake(row,db):
 alias=row['sample_alias'];p=INPUT/(alias+'.fastq.gz');download(row['fastq_path'],p)
 count=0;nbases=0;subset=INPUT/(alias+'.repeat.fastq');begin=time.time()
 with subset.open('w') as small:
  for rid,seq,qual in fqrecords(p):
   # Original identity is preserved; duplicate UUID across files stays auditable.
   db.execute('INSERT INTO reads VALUES (?,?,?)',(alias,rid,hashlib.sha256(seq.encode()).hexdigest()));count+=1;nbases+=len(seq)
   if hashlib.sha256(rid.encode()).digest()[0]==0:small.write('@'+rid+'\n'+seq+'\n+\n'+qual+'\n')
 db.commit();save(OUT/alias/'intake.json',{'reads':count,'bases':nbases,'library':alias,'biological_specimen_id':None,'biological_independence':'UNKNOWN','seconds':time.time()-begin,'fastq_sha256':sha(p),'subset_sha256':sha(subset),'subset_rule':CFG['read_subset_rule']});return p,count

def discover(alias,fastq,expected,root):
 d=root/'discovery';d.mkdir(parents=True,exist_ok=True)
 prefix=q(REF/'genome.mmi');bam=d/'name.bam'
 cmd(alias+'-align',f'minimap2 -ax splice -uf -k14 --secondary=no -G50k -t{THREADS} {prefix} {q(fastq)} | samtools sort -n -@2 -m1G -T {q(d/"sort")} -o {q(bam)} -',7200)
 cmd(alias+'-quickcheck',['samtools','quickcheck','-v',str(bam)],120)
 observed=int(subprocess.check_output(['samtools','view','-c','-F','2304',str(bam)],env=ENV))
 assert observed==expected,(alias,observed,expected)
 cmd(alias+'-LongGF',f'LongGF {q(bam)} {q(REF/"annotation.gtf")} 100 50 100 2 0 1 0 > {q(d/"LongGF.log")}',1800)
 ids=set(subprocess.check_output(['samtools','view','-f','2048',str(bam)],env=ENV,text=True).splitlines());ids={line.split('\t')[0] for line in ids}
 (d/'split_read_ids.txt').write_text(''.join(x+'\n' for x in sorted(ids)))
 written=0
 with (d/'split_reads.fastq').open('w') as f:
  for rid,seq,qual in fqrecords(fastq):
   if rid in ids:f.write('@'+rid+'\n'+seq+'\n+\n'+qual+'\n');written+=1
 assert written==len(ids),(written,len(ids))
 if ids:
  cmd(alias+'-genome-audit',['minimap2','-ax','splice','-uf','-k14','--MD','--secondary=yes','-N50','-p0.1','-G50k','-t',THREADS,str(REF/'genome.mmi'),str(d/'split_reads.fastq'),'-o',str(d/'split_genome_audit.sam')],3600)
  cmd(alias+'-transcript-audit',['minimap2','-ax','map-ont','-k14','--MD','--secondary=yes','-N50','-p0.1','-t',THREADS,str(REF/'transcripts.fa'),str(d/'split_reads.fastq'),'-o',str(d/'split_transcript_audit.sam')],3600)
 else:
  (d/'split_genome_audit.sam').touch();(d/'split_transcript_audit.sam').touch()
 summary=assess(d,REF/'annotation.gtf',root/'assessment',sample_id=alias,biological_sample_id=None,reference_build=CFG['reference_build'],rules_path=BASE/'rules.md')
 save(root/'acceptance.json',{'expected_reads':expected,'primary_records':observed,'split_reads':written,'core_sha256':{p.name:sha(p) for p in [bam,d/'LongGF.log',d/'split_reads.fastq']},'summary':summary})
 save(root/'freeze.json',{'utc':now(),'scope':'Independent per-library assessment, before cross-library joins','sha256':{str(p.relative_to(root)):sha(p) for p in sorted((root/'assessment').glob('*.json'))}})
 return summary

def repeatability(alias):
 status('real_read_repeatability');fq=INPUT/(alias+'.repeat.fastq');n=sum(1 for _ in fqrecords(fq));canonical=[]
 for index in [1,2]:
  dest=OUT/('repeatability-'+str(index));discover(alias+'-repeat',fq,n,dest)
  values={}
  for path in (dest/'assessment').glob('*.json'):
   data=json.loads(path.read_text())
   # canonical JSON key order; provenance SAM line order expected stable with pinned settings.
   values[path.name]=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  canonical.append(values)
 save(OUT/'repeatability.json',{'reads':n,'input_sha256':sha(fq),'rule':CFG['read_subset_rule'],'equal':canonical[0]==canonical[1],'canonical_sha256':canonical,'scope':'Real-read hash subset, not full-data bitwise reproducibility'})
 assert canonical[0]==canonical[1],'Repeatability mismatch; report and diagnose'

def illumina(row):
 status('illumina_setup');name=row['sample_alias'];paths=[INPUT/(name+'_'+mate+'.fastq.gz') for mate in ['R1','R2']]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  fs=[pool.submit(download,row['fastq_path_'+mate],p) for mate,p in zip(['R1','R2'],paths)]
  for f in fs:f.result()
 # Validate every paired record; names normalize only terminal mate suffix.
 import itertools
 count=0;maxlen=0;beg=time.time()
 for a,b in itertools.zip_longest(fqrecords(paths[0]),fqrecords(paths[1])):
  assert a is not None and b is not None,'Unequal paired-end record count'
  assert a[0].removesuffix('/1')==b[0].removesuffix('/2'),'Read mate identifiers mismatch'
  count+=1;maxlen=max(maxlen,len(a[1]),len(b[1]))
 save(OUT/'illumina/intake.json',{'read_pairs':count,'max_read_length':maxlen,'paired_id_validation':'all records','seconds':time.time()-beg})
 tar=INPUT/'STAR.tar.gz';download('https://codeload.github.com/alexdobin/STAR/tar.gz/'+CFG['star_commit'],tar)
 cmd('STAR-unpack',['tar','xzf',str(tar),'-C',str(BASE)],120)
 binary=BASE/('STAR-'+CFG['star_commit'])/'bin/Linux_x86_64_static/STAR';assert binary.exists()
 version=subprocess.check_output([str(binary),'--version'],text=True).strip();assert version=='2.7.11b',version
 save(OUT/'illumina/tool.json',{'version':version,'sha256':sha(binary),'commit':CFG['star_commit']})
 idx=REF/'star-index';idx.mkdir(exist_ok=True)
 cmd('STAR-index',[str(binary),'--runThreadN',THREADS,'--runMode','genomeGenerate','--genomeDir',str(idx),'--genomeFastaFiles',str(REF/'genome.fa'),'--sjdbGTFfile',str(REF/'annotation.gtf'),'--sjdbOverhang',str(maxlen-1),'--limitGenomeGenerateRAM','54000000000'],5400)
 dest=OUT/'illumina';dest.mkdir(exist_ok=True)
 params=[str(binary),'--runThreadN',THREADS,'--genomeDir',str(idx),'--readFilesIn',*[str(p) for p in paths],'--readFilesCommand','zcat','--outFileNamePrefix',str(dest)+'/', '--outSAMtype','None','--chimOutType','Junctions','--chimSegmentMin','20','--chimJunctionOverhangMin','20','--chimMultimapNmax','1','--chimScoreDropMax','20','--chimScoreSeparation','10','--chimNonchimScoreDropMin','10','--outFilterMismatchNoverReadLmax','0.04','--outFilterMultimapNmax','10']
 save(dest/'parameters.json',{'argv':params,'rules':CFG['illumina_rules']});status('illumina_alignment');cmd('STAR-alignment',params,10800)
 final=(dest/'Log.final.out').read_text();input_line=[x for x in final.splitlines() if 'Number of input reads' in x];assert len(input_line)==1 and int(input_line[0].split('|')[1])==count
 save(dest/'complete.json',{'utc':now(),'read_pairs':count,'junction_sha256':sha(dest/'Chimeric.out.junction'),'status':'processed'})

def main():
 save(OUT/'environment.json',{'utc':now(),'python':sys.version,'cpu':os.cpu_count(),'config_sha256':sha(BASE/'config.json'),'rules_sha256':sha(BASE/'rules.md'),'hardware':subprocess.check_output(['bash','-c','uname -a; free -b; df -B1 .'],text=True)})
 cmd('tools-hash',['sha256sum','-c','tools.sha256'],120)
 prepare_references()
 db=sqlite3.connect(OUT/'read_identity.sqlite');db.execute('CREATE TABLE IF NOT EXISTS reads(library TEXT, read_id TEXT, sequence_sha256 TEXT, PRIMARY KEY(library,read_id))')
 longrows=[x['row'] for x in CFG['samples'] if x['row'].get('protocol')=='directRNA'];longrows.sort(key=lambda x:x['sample_alias'])
 starta=time.time()
 for row in longrows:
  assert time.time()-starta<CFG['checkpoint_a_seconds'],'Checkpoint A time budget exhausted'
  alias=row['sample_alias'];status('intake_'+alias);fq,n=intake(row,db);status('discovery_'+alias);discover(alias,fq,n,OUT/alias)
  if row is longrows[0]:save(OUT/'primary_freeze.json',json.loads((OUT/alias/'freeze.json').read_text()))
 duplicates=list(db.execute('SELECT read_id,COUNT(*),COUNT(DISTINCT sequence_sha256) FROM reads GROUP BY read_id HAVING COUNT(*)>1'))
 save(OUT/'cross_library_identity.json',{'overlapping_read_ids':duplicates,'count':len(duplicates),'biological_independence':'UNKNOWN'})
 db.close()
 if duplicates:raise RuntimeError('Cross-library read UUID overlap must be reconciled before corroboration')
 report(BASE);status('checkpoint_A_evidence_complete');repeatability(longrows[0]['sample_alias']);report(BASE)
 errors=[]
 try:illumina(next(x['row'] for x in CFG['samples'] if 'Illumina' in x['row']['sample_alias']))
 except Exception as e:errors.append({'stage':'illumina','type':type(e).__name__,'error':str(e)});save(OUT/'illumina/failure.json',errors[-1])
 result=report(BASE);save(OUT/'completion.json',{'utc':now(),'A_execution':'complete','repeatability':json.loads((OUT/'repeatability.json').read_text()),'B_execution':result['illumina']['status'],'errors':errors,'interpretation':'Execution status distinct from positive-control detection and biological validity','elapsed_seconds':time.time()-START});status('finished',errors=errors)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  save(OUT/'failure.json',{'utc':now(),'error_type':type(e).__name__,'error':str(e)});status('failed',error=str(e));raise
