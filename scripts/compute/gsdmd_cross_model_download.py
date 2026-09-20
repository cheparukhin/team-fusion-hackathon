#!/usr/bin/env python3
"""Fetch pinned public model weights; never submit protein sequences."""
import argparse,hashlib,json,time,requests
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
revision='75a3841ee059df2bf4d56688166c8fb459ddd97a';meta=requests.get(f'https://huggingface.co/api/models/facebook/esmfold_v1/revision/{revision}?blobs=true',timeout=30).json();target=a.output/'weights/esmfold_v1';target.mkdir(parents=True,exist_ok=True);records=[]
def save(status):
 x={'status':status,'utc':datetime.now(timezone.utc).isoformat(),'repository':'facebook/esmfold_v1','revision':revision,'files':records};q=a.output/'weight_download.json.partial';q.write_text(json.dumps(x,indent=2)+'\n');q.replace(a.output/'weight_download.json')
for item in meta['siblings']:
 name=item['rfilename']
 if name not in ['config.json','pytorch_model.bin','special_tokens_map.json','tokenizer_config.json','vocab.txt']:continue
 dest=target/name;expected=item.get('lfs',{}).get('sha256');record={'file':name,'expected_bytes':item['size'],'expected_sha256':expected,'started_utc':datetime.now(timezone.utc).isoformat()};records.append(record);save('downloading')
 if not dest.exists():
  r=requests.get(f'https://huggingface.co/facebook/esmfold_v1/resolve/{revision}/{name}?download=true&cache_bust={time.time_ns()}',stream=True,timeout=(30,90))
  if r.status_code!=200:record.update(status='failed',http_status=r.status_code);save('failed');raise RuntimeError(f'Public weight download returned HTTP{r.status_code}')
  count=0;last=time.monotonic()
  with dest.with_suffix(dest.suffix+'.partial').open('wb')as f:
   for chunk in r.iter_content(8*1024*1024):
    f.write(chunk);count+=len(chunk)
    if time.monotonic()-last>15:record['downloaded_bytes']=count;save('downloading');last=time.monotonic()
  dest.with_suffix(dest.suffix+'.partial').replace(dest)
 h=hashlib.sha256()
 with dest.open('rb')as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 actual=h.hexdigest();assert dest.stat().st_size==item['size'];assert not expected or expected==actual
 record.update(status='verified',sha256=actual,bytes=dest.stat().st_size,finished_utc=datetime.now(timezone.utc).isoformat());save('downloading')
save('completed');print('Pinned ESMFold weights downloaded and SHA256 verified')
