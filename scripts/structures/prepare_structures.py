#!/usr/bin/env python3
"""Import verified existing inference and download the experimental parent reference."""
import argparse, hashlib, json, shutil
from pathlib import Path
from datetime import datetime, timezone
import requests

ROOT=Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument('--prior-run',type=Path,default=Path('/home/ubuntu/workspace/chrna/runs/focused-pilot-20260919')); a=p.parse_args()
 out=ROOT/'results/structures'; out.mkdir(exist_ok=True)
 source=a.prior_run; pred=out/'gsdmd_tmem106a'; pred.mkdir(exist_ok=True)
 ident='protein_f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa'
 summary=json.loads((source/'structures/summary.json').read_text())
 job=next(j for j in summary['jobs'] if j['job_id']==ident)
 assert job['status']=='verified' and job['amino_acids']==118
 imported=[]
 def cp(src,dst):
  shutil.copy2(src,dst); imported.append({'source_path':str(src),'path':str(dst.relative_to(ROOT)),'sha256':sha(dst)})
 for rel,expected in job['validation']['files'].items():
  src=source/job['prediction_directory']/rel
  assert sha(src)==expected, f'Cached output hash mismatch: {src}'
  name='model.cif' if src.suffix=='.cif' else ('confidence.json' if src.suffix=='.json' else src.name.split('_protein_')[0]+'.npz')
  cp(src,pred/name)
 for srcname,dstname in [('published_architecture_control.fasta','sequence.fasta'),('published_architecture_control.rna.fasta','rna.fasta'),('provenance.json','reconstruction_provenance.json')]: cp(source/'published-control'/srcname,pred/dstname)
 for suffix in ['fasta','yaml']: cp(source/'fold-inputs'/f'{ident}.{suffix}',pred/f'input.{suffix}')
 for suffix in ['a3m','json']: cp(source/'fold-inputs/msas'/f'{ident}.{suffix}',pred/f'msa.{suffix}')
 (pred/'cached_inference_provenance.json').write_text(json.dumps(job,indent=2)+'\n')
 (pred/'prediction.yaml').write_text('version: 1\nsequences:\n  - protein:\n      id: A\n      sequence: '+''.join((pred/'sequence.fasta').read_text().splitlines()[1:])+'\n      msa: msa.a3m\n')
 parent=out/'gsdmd_parent'; parent.mkdir(exist_ok=True)
 for name,url in [('6N9N.cif','https://files.rcsb.org/download/6N9N.cif'),('rcsb_entry.json','https://data.rcsb.org/rest/v1/core/entry/6N9N'),('rcsb_entity.json','https://data.rcsb.org/rest/v1/core/polymer_entity/6N9N/1')]:
  dst=parent/name
  if not dst.exists():
   r=requests.get(url,timeout=90); r.raise_for_status(); dst.write_bytes(r.content)
  imported.append({'source_url':url,'path':str(dst.relative_to(ROOT)),'sha256':sha(dst)})
 (out/'source_manifest.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),'new_compute_cost_usd':0,'artifacts':imported},indent=2)+'\n')
 print('Imported',len(imported),'verified artifacts; no inference rerun')
if __name__=='__main__': main()
