#!/usr/bin/env python3
"""Publish protocol-separated outputs without mutating frozen input manifests."""
import argparse,csv,json,shutil
from pathlib import Path
from collections import Counter
from structure_campaign_stage import save

def main(root):
 preserved=root/'precomputed_context';preserved.mkdir(exist_ok=True)
 for name in ['jobs.json','model_metrics.tsv','structure_gallery.json','summary.json']:
  dest=preserved/name
  if not dest.exists()and (root/name).exists():shutil.copy2(root/name,dest)
 jobs={};metrics={};gallery={}
 for source in [preserved,root/'single_sequence_pilot',root/'single_sequence_full',root/'single_sequence_deepdive']:
  if (source/'jobs.json').exists():
   for j in json.loads((source/'jobs.json').read_text()):
    key=j['job_id'];old=jobs.get(key)
    if not old or j['status']in {'verified','cached_verified'}or old['status']not in {'verified','cached_verified'}:jobs[key]=j
  if (source/'model_metrics.tsv').exists():
   with (source/'model_metrics.tsv').open()as f:
    for r in csv.DictReader(f,delimiter='\t'):
     old=metrics.get(r['job_id'])
     if not old or r['status']in {'verified','cached_verified'}or old['status']not in {'verified','cached_verified'}:metrics[r['job_id']]=r
  if (source/'structure_gallery.json').exists():
   for a in json.loads((source/'structure_gallery.json').read_text())['assets']:gallery[(a['sequence_sha256'],a['protocol_id'])]=a
 save(root/'jobs.json',list(jobs.values()))
 if metrics:
  fields=list(next(iter(metrics.values())))
  with (root/'model_metrics.tsv.partial').open('w')as f:w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(metrics.values())
  (root/'model_metrics.tsv.partial').replace(root/'model_metrics.tsv')
 save(root/'structure_gallery.json',{'assets':list(gallery.values()),'interpretation':'Protocols shown separately. Precomputed-MSA cache and single-sequence sensitivity predictions are not pooled.'})
 summary={}
 for j in jobs.values():
  protocol=j['protocol_id'];r=summary.setdefault(protocol,{'planned_models':0,'verified_models':0,'cached_models':0,'failed_models':0,'not_run_or_deferred':0});r['planned_models']+=1
  if j['status']in {'verified','cached_verified'}:r['verified_models']+=1;r['cached_models']+=j['status']=='cached_verified'
  elif j['status']=='failed':r['failed_models']+=1
  else:r['not_run_or_deferred']+=1
 save(root/'summary.json',{'status':'protocol_separated_ledger','protocols':summary,'strict_primary_peptides':len({j['sequence_sha256']for j in jobs.values()if j['role']=='primary'}),'scientific_scope':'Conditional reference hypotheses; no biological translation/function validation. Single-sequence mode reduces accuracy and is separately interpreted.'})
 print(json.dumps(summary,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
