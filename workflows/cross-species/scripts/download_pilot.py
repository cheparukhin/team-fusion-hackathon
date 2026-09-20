import pathlib,csv,json,urllib.request,hashlib,concurrent.futures,gzip,shutil,datetime
R=pathlib.Path(__file__).resolve().parents[1]
def fetch(url,p,md5=None,unzip=False):
 p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  urllib.request.urlretrieve(url,str(p)+'.part');pathlib.Path(str(p)+'.part').rename(p)
 h=hashlib.md5();sha=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b);sha.update(b)
 if md5 and h.hexdigest()!=md5:raise ValueError(f'Checksum mismatch {p}')
 rec={'url':url,'file':str(p.relative_to(R)),'bytes':p.stat().st_size,'md5':h.hexdigest(),'expected_md5':md5,'sha256':sha.hexdigest(),'download_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 p.with_suffix(p.suffix+'.provenance.json').write_text(json.dumps(rec,indent=2))
 if unzip and not p.with_suffix('').exists():
  with gzip.open(p,'rb') as src,p.with_suffix('').open('wb') as dst:shutil.copyfileobj(src,dst)
 print('COMPLETE',p,flush=True)
jobs=[]
for s in json.loads((R/'manifest/references.json').read_text()):
 if s['species'] not in ['homo_sapiens','bos_taurus']:continue
 for k in ['genome_url','gtf_url']:
  u=s[k];jobs.append((u,R/'reference'/s['species']/u.split('/')[-1],None,True))
for r in csv.DictReader((R/'manifest/samples.tsv').open(),delimiter='\t'):
 if r['run_accession'] not in ['SRR31438987','SRR31429688']:continue
 jobs.append(('https://'+r['fastq_ftp'],R/'raw'/r['run_accession']/(r['run_accession']+'.fastq.gz'),r['fastq_md5'],False))
with concurrent.futures.ThreadPoolExecutor(3) as pool:
 list(pool.map(lambda a:fetch(*a),jobs))
(R/'qc/pilot_downloads_ready').touch()
