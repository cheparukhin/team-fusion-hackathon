#!/usr/bin/env python3
"""Validate locally exported results and publish one ledger including failed jobs."""
import argparse,csv,json,shutil
from pathlib import Path
import numpy as np
from structure_campaign_stage import save,digest,validate_model

def main(a):
 m=json.loads((a.output/'inputs/manifest.json').read_text());history={}
 for source in [a.output/'cached_jobs.json',a.output/'remote/jobs.json']:
  if source.exists():
   for row in json.loads(source.read_text()):history[row['job_id']]=row
 jobs=[];metrics=[]
 for j in m['jobs']:
  row=history.get(j['job_id'],{**j,'status':'not_run','reason':'No actual prediction or validated cache'})
  if row['status']in {'verified','cached_verified'}:
   dst=a.output/'models'/j['job_id'];dst.mkdir(parents=True,exist_ok=True)
   if row['status']=='verified':
    src=a.output/'remote/models'/j['job_id']
    for key,expected in row['artifact_sha256'].items():
     p=src/key
     if digest(p)!=expected:raise ValueError(f'Export integrity failure: {p}')
     shutil.copy2(p,dst/key)
   valid=validate_model(j['sequence'],dst/'model.cif',dst/'plddt.npz',dst/'pae.npz')
   plddt=np.load(dst/'plddt.npz')['plddt'].reshape(-1)*100
   with (dst/'residue_confidence.tsv').open('w')as f:
    w=csv.writer(f,delimiter='\t');w.writerow(['peptide_id','sequence_sha256','seed','residue','aa','plddt'])
    w.writerows([j['peptide_id'],j['sequence_sha256'],j['seed'],i,aa,float(p)]for i,(aa,p)in enumerate(zip(j['sequence'],plddt),1))
   valid['ptm']=json.loads((dst/'confidence.json').read_text())['ptm'];row['validation']=valid
   row['artifacts']={p.name:str(p)for p in dst.iterdir()if p.is_file()};row['artifact_sha256']={k:digest(v)for k,v in row['artifacts'].items()}
  jobs.append(row);v=row.get('validation',{})
  metrics.append({**{k:j[k]for k in ['job_id','peptide_id','sequence_sha256','seed','role','length_aa','protocol_id','msa_mode']},'selection_cohort':j['input_mapping'].get('selection_cohort',''),'status':row['status'],'reused_prior_prediction':row.get('reused_prior_prediction',False),**{k:v.get(k)for k in ['mean_plddt','fraction_plddt_ge70','fraction_plddt_ge90','fraction_plddt_below_50','mean_pae_angstrom','ptm']},'reason':row.get('reason','')})
 save(a.output/'jobs.json',jobs)
 if metrics:
  with (a.output/'model_metrics.tsv.partial').open('w')as f:
   w=csv.DictWriter(f,fieldnames=list(metrics[0]),delimiter='\t');w.writeheader();w.writerows(metrics)
  (a.output/'model_metrics.tsv.partial').replace(a.output/'model_metrics.tsv')
 complete=sum(r['status']in {'verified','cached_verified'}for r in jobs)
 save(a.output/'summary.json',{'status':'complete'if complete==len(jobs)else'partial','planned_models':len(jobs),'verified_models':complete,'newly_verified_models':sum(r['status']=='verified'for r in jobs),'cached_verified_models':sum(r['status']=='cached_verified'for r in jobs),'primary_unique_peptides':len({r['sequence_sha256']for r in jobs if r['role']=='primary'}),'sensitivity_unique_peptides':len({r['sequence_sha256']for r in jobs if r['role']=='sensitivity'}),'interpretation':'Computational characterization only; no inference of translation, function or experimental disorder. Sensitivity models retain all reconstruction assumptions.'})
 print(f'Published {complete}/{len(jobs)} verified models including cache')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args())
