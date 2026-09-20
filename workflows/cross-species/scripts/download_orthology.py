import pathlib,json,urllib.request,gzip,csv,hashlib,concurrent.futures,datetime
R=pathlib.Path(__file__).resolve().parents[1];sources=json.loads((R/'manifest/compara_urls.json').read_text());species={x['species'] for x in sources};out=R/'reference/orthology';out.mkdir(parents=True,exist_ok=True)
def fetch(item):
 sp,u=item;p=out/sp/u.split('/')[-1];p.parent.mkdir(exist_ok=True)
 if not p.exists():urllib.request.urlretrieve(u,str(p)+'.part');pathlib.Path(str(p)+'.part').rename(p)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 rows=[]
 with gzip.open(p,'rt') as f:
  for r in csv.DictReader(f,delimiter='\t'):
   if r['species'] in species and r['homology_species'] in species and r['species']!=r['homology_species']:rows.append(r)
 p.with_suffix('.provenance.json').write_text(json.dumps({'source_url':u,'sha256':h.hexdigest(),'release':115,'selected_rows':len(rows),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
 print(sp,u.split('/')[-1],len(rows),flush=True);return rows
jobs=[(x['species'],u) for x in sources for u in x['files'] if '_default.' in u]
allrows=[]
with concurrent.futures.ThreadPoolExecutor(2) as pool:
 for rows in pool.map(fetch,jobs):allrows.extend(rows)
with (out/'five_species_homologies.tsv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(allrows[0]),delimiter='\t');w.writeheader();w.writerows(allrows)
print('DONE',len(allrows),flush=True)
