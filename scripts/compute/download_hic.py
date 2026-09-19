import concurrent.futures, hashlib, json, pathlib, urllib.request, time
root=pathlib.Path(__file__).resolve().parents[2]/'results/hic'
(root/'raw').mkdir(exist_ok=True)
def get(pair):
 acc,letter=pair;name=f'{acc}_OV_siNeg_LPS_{letter}.prejuicer.hic';url=f'https://ftp.ncbi.nlm.nih.gov/geo/samples/GSM9574nnn/{acc}/suppl/{name}';p=root/'raw'/name
 if not p.exists(): urllib.request.urlretrieve(url,p)
 digest=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
 return {'accession':acc,'replicate':letter,'url':url,'path':str(p),'bytes':p.stat().st_size,'sha256':digest,'assembly':'GRCm39','treatment':'scramble siRNA; LPS6h'}
x=list(concurrent.futures.ThreadPoolExecutor(3).map(get,[('GSM9574808','A'),('GSM9574809','B'),('GSM9574815','C')]))
(root/'download_manifest.json').write_text(json.dumps(x,indent=2));print(json.dumps(x,indent=2))
