"""Fetch a recorded run/reference with checksums; no accession guessing."""
import argparse,csv,pathlib,json,urllib.request,hashlib,gzip,shutil,subprocess,time,datetime,xml.etree.ElementTree as E
R=pathlib.Path(__file__).resolve().parents[1]
def fetch(url,path,expected=None):
 path.parent.mkdir(parents=True,exist_ok=True)
 if not path.exists():
  for attempt in range(4):
   try:
    with urllib.request.urlopen(url,timeout=120) as src,path.with_suffix(path.suffix+'.part').open('wb') as dst:shutil.copyfileobj(src,dst,8*1024*1024)
    path.with_suffix(path.suffix+'.part').rename(path);break
   except Exception:
    if attempt==3:raise
    time.sleep(5*(attempt+1))
 md5=hashlib.md5();sha=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):md5.update(b);sha.update(b)
 if expected and md5.hexdigest()!=expected:raise ValueError('Checksum mismatch: '+str(path))
 path.with_suffix(path.suffix+'.provenance.json').write_text(json.dumps({'url':url,'expected_md5':expected,'md5':md5.hexdigest(),'sha256':sha.hexdigest(),'bytes':path.stat().st_size,'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
 return path
def reference(species):
 x=next(x for x in json.loads((R/'manifest/references.json').read_text()) if x['species']==species)
 for key in ['genome_url','gtf_url']:
  p=fetch(x[key],R/'reference'/species/x[key].split('/')[-1]);dest=p.with_suffix('')
  if not dest.exists():
   with gzip.open(p,'rb') as src,dest.open('wb') as dst:shutil.copyfileobj(src,dst,8*1024*1024)
 return x
def run_reads(run):
 row=next(x for x in csv.DictReader((R/'manifest/samples.tsv').open(),delimiter='\t') if x['run_accession']==run);out=R/'raw'/run;fq=out/(run+'.fastq.gz')
 if row['fastq_ftp']:
  urls=row['fastq_ftp'].split(';');md5s=row['fastq_md5'].split(';');assert len(urls)==1,'Unexpected multi-file layout'
  fetch('https://'+urls[0],fq,md5s[0])
 else:
  tree=E.parse(R/'manifest'/(run+'_ncbi.xml'));files=[x for x in tree.findall('.//SRAFile') if x.get('semantic_name')=='SRA Normalized']
  assert len(files)==1,'Ambiguous normalized archive';x=files[0];url=x.get('url');assert url,'No archive URL';archive=fetch(url,out/(run+'.sra'),x.get('md5'))
  if not fq.exists():
   subprocess.run(['fasterq-dump',str(archive),'--threads','6','--outdir',str(out),'--temp',str(R/'scratch'),'--seq-defline','@$ac.$si $sn','--qual-defline','+'],check=True)
   plain=out/(run+'.fastq');assert plain.exists()
   with plain.open('rb') as src,gzip.open(fq,'wb',compresslevel=1) as dst:shutil.copyfileobj(src,dst,8*1024*1024)
   plain.unlink()
 if not (out/'read_id_map.tsv.gz').exists():subprocess.run(['python',str(R/'scripts/map_read_ids.py'),str(fq)],check=True)
 return fq
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--species');p.add_argument('--run');a=p.parse_args()
 if a.species:reference(a.species)
 if a.run:run_reads(a.run)
