"""Prepare or run independent hosted NIM requests for the frozen 118-aa reference.

No inference is claimed without a saved response and validated structure.
Credentials are loaded only from documented environment variables or workspace .env.
"""
import argparse, concurrent.futures, hashlib, json, os, time
from datetime import datetime, timezone
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'results/structure_campaign/cross_model_gsdmd/nim'
EXPECTED='f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa'
ENDPOINTS={
 'alphafold2':'https://health.api.nvidia.com/v1/protein-structure/alphafold2/predict-structure-from-sequence',
 'openfold2':'https://health.api.nvidia.com/v1/biology/openfold/openfold2/predict-structure-from-msa-and-template',
 'openfold3':'https://health.api.nvidia.com/v1/biology/openfold/openfold3/predict',
}
def save(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.partial');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(path)
def key():
 values=dict(os.environ)
 # Parse only literal KEY=value entries. Never execute a credential file.
 env=ROOT/'.env'
 if env.exists():
  for line in env.read_text().splitlines():
   line=line.strip().removeprefix('export ')
   if '=' in line and not line.startswith('#'):
    name,value=line.split('=',1)
    if name.strip() in {'NGC_API_KEY','NVIDIA_API_KEY'} and not values.get(name.strip()):values[name.strip()]=value.strip().strip('\"\'')
 return values.get('NGC_API_KEY') or values.get('NVIDIA_API_KEY')
def prepare():
 source=ROOT/'results/structures/gsdmd_tmem106a/sequence.fasta'
 seq=''.join(x.strip()for x in source.read_text().splitlines()if not x.startswith('>'))
 if len(seq)!=118 or hashlib.sha256(seq.encode()).hexdigest()!=EXPECTED:raise ValueError('Frozen reference identity mismatch')
 msa_path=ROOT/'results/structures/gsdmd_tmem106a/msa.a3m';msa=msa_path.read_text()
 records=[];current=''
 for line in msa.splitlines():
  if line.startswith('#'):continue
  if line.startswith('>'):
   if current:records.append(current)
   current=''
  else:current+=line.strip()
 if current:records.append(current)
 if not records or ''.join(c for c in records[0] if not c.islower()).replace('-','')!=seq:raise ValueError('Cached MSA query mismatch')
 requests_by_engine={
  'alphafold2':{'sequence':seq,'selected_models':[1,2,3,4,5],'relax_prediction':False,'skip_template_search':True},
  'openfold2':{'sequence':seq,'input_id':'gsdmd_tmem106a_118aa','selected_models':[1,2,3,4,5],'relax_prediction':False,'use_templates':False,'alignments':{'cached_msa':{'a3m':{'alignment':msa,'format':'a3m'}}}},
  'openfold3':{'inputs':[{'input_id':'gsdmd_tmem106a_118aa','output_format':'cif','molecules':[{'type':'protein','id':'A','sequence':seq,'diffusion_samples':1,'msa':{'cached_msa':{'a3m':{'alignment':msa,'format':'a3m'}}}}]}]},
 }
 for engine,payload in requests_by_engine.items():save(BASE/engine/'request.json',payload)
 save(BASE/'preflight.json',{'sequence_sha256':EXPECTED,'length_aa':118,'credential_present':bool(key()),'endpoints':ENDPOINTS,'cached_msa_sha256':hashlib.sha256(msa_path.read_bytes()).hexdigest(),'cached_msa_records':len(records),'protocol_note':'AlphaFold2 endpoint prepares its own MSA; OpenFold2/3 requests use the exact existing cached MSA. No parent-only structures substitute for fusion inference.','utc':datetime.now(timezone.utc).isoformat()})
 return requests_by_engine

def run_one(engine,payload,token):
 out=BASE/engine;start=time.monotonic();record={'engine':engine,'sequence_sha256':EXPECTED,'endpoint':ENDPOINTS[engine],'status':'running','started_utc':datetime.now(timezone.utc).isoformat()};save(out/'status.json',record)
 try:
  headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','NVCF-POLL-SECONDS':'30'}
  response=requests.post(ENDPOINTS[engine],headers=headers,json=payload,timeout=(30,300))
  # NVIDIA asynchronous responses may provide a request identifier for polling.
  deadline=time.monotonic()+900
  while response.status_code==202 and time.monotonic()<deadline:
   rid=response.headers.get('NVCF-REQID')
   if not rid:break
   time.sleep(3)
   response=requests.get('https://api.nvcf.nvidia.com/v2/nvcf/pexec/status/'+rid,headers=headers,timeout=(30,60))
  record['http_status']=response.status_code
  try:body=response.json()
  except ValueError:body={'response_text':response.text[:12000]}
  save(out/'response.json',body)
  response.raise_for_status()
  if response.status_code==202:record['status']='pending_server_response'
  else:
   found=[]
   def visit(obj,path='response'):
    if isinstance(obj,dict):
     for name,value in obj.items():visit(value,path+'.'+name)
    elif isinstance(obj,list):
     for i,value in enumerate(obj):visit(value,path+'.'+str(i))
    elif isinstance(obj,str)and(obj.lstrip().startswith('data_')or any(line.startswith('ATOM  ')for line in obj.splitlines())):
     suffix='.cif'if obj.lstrip().startswith('data_')else'.pdb';dest=out/f'structure_{len(found)+1}{suffix}';dest.write_text(obj);found.append({'path':str(dest.relative_to(ROOT)),'response_field':path,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
   visit(body);record.update(status='structures_received_awaiting_identity_validation'if found else'response_received_no_structure_text',structures=found)
 except Exception as error:
  # Do not serialize request objects, headers, URLs with credentials or tracebacks.
  record.update(status='request_failed',error_type=type(error).__name__)
 record['elapsed_seconds']=time.monotonic()-start;save(out/'status.json',record);return record
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--engines',nargs='+',choices=list(ENDPOINTS),default=list(ENDPOINTS));a=p.parse_args();payloads=prepare();token=key()
 if not a.execute:print('Prepared three exact-sequence requests; no inference submitted.')
 elif not token:
  for engine in a.engines:save(BASE/engine/'status.json',{'engine':engine,'status':'blocked_missing_credentials','sequence_sha256':EXPECTED,'reason':'No NGC_API_KEY or NVIDIA_API_KEY is configured; no prediction request submitted.'})
  print('No NIM credentials configured; no requests submitted.')
 else:
  with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
   for result in pool.map(lambda e:run_one(e,payloads[e],token),a.engines):print(json.dumps(result))
