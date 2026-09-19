"""Export audited real artifacts to an offline browser bundle. No scientific values are imputed."""
from __future__ import annotations
import argparse,csv,json,hashlib,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from reports import report_input, fallback, validate_report, digest
ROOT=Path(__file__).resolve().parents[2]
NUMBERS={'label','fold','score_rna','score_rna_matched','score_hic','hic_feature','hic_n_replicates','hic_n_bin_pairs','hic_partial_enrichment','hic_resolution','long_read_support','sample_count','is_interchromosomal','genomic_distance','hic_contact_enrichment','short_read_support','junction_count','parabricks_support'}

def read_tsv(path):
 if not path.exists():return []
 with path.open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
 for r in rows:
  for k,v in list(r.items()):
   if v in ('','NA','NaN','nan','null','None'):r[k]=None
   elif v in ('True','False'):r[k]=v=='True'
   elif k in NUMBERS:
    try:r[k]=float(v) if '.' in v or 'e' in v.lower() else int(v)
    except ValueError:pass
 return rows

def build(root=ROOT):
 task=root/'results/dataset_reconstruction'; rows=read_tsv(task/'candidates.tsv'); preds=read_tsv(root/'results/classifier/predictions.tsv')
 if not rows: raise ValueError('Real candidates.tsv is required; export refuses to silently substitute fixtures.')
 hicmap={x['pair_id']:x for x in read_tsv(root/'results/hic/features.tsv')}
 predmap={x['pair_id']:x for x in preds}; inputs={x['pair_id']:x for x in read_tsv(task/'model_input.tsv')}
 junctions={};probes={};probe_junctions={};gpu_evidence={}
 gpu_path=root/'results/compute/evidence.tsv'
 for r in read_tsv(gpu_path):gpu_evidence.setdefault(r.get('pair_id'),[]).append(r)
 pilot_path=root/'results/compute/pilot_summary.json'
 pilot=json.loads(pilot_path.read_text()) if pilot_path.exists() else {'status':'unavailable','limitations':['No NVIDIA pilot summary is available in this export.']}
 for r in read_tsv(task/'junctions.tsv'):junctions.setdefault(r.get('pair_id'),[]).append(r)
 for r in read_tsv(task/'probe_junctions.tsv'):probe_junctions.setdefault(r.get('pair_id'),[]).append(r)
 for r in read_tsv(task/'probe_panel.tsv'):probes.setdefault(r.get('pair_id'),[]).append(r)
 sourcepath=root/'results/demo/sources/passages.json'; sources=json.loads(sourcepath.read_text()) if sourcepath.exists() else []
 out=[]
 for row in rows:
  if row['pair_id'] not in inputs: continue
  pid=row['pair_id']; c={**row,**inputs.get(pid,{}),**hicmap.get(pid,{}),**predmap.get(pid,{})}
  c.setdefault('label',c.get('reported_nanostring_support',c.get('nanostring_reported_support')))
  if isinstance(c.get('label'),str) and c['label'] in ('0','1'):c['label']=int(c['label'])
  a,b=pid.split(':',1);c.setdefault('parent_a',a);c.setdefault('parent_b',b)
  for k in ['score_rna','score_rna_matched','score_hic','hic_feature','hic_n_replicates','hic_n_bin_pairs','hic_partial_enrichment','hic_resolution','fold','long_read_support','sample_count','hic_contact_enrichment']:c.setdefault(k,None)
  c['junctions']=junctions.get(pid,[]);c['probes']=probes.get(pid,[]);c['probe_junctions']=probe_junctions.get(pid,[])
  if gpu_path.exists():c['gpu_evidence']=gpu_evidence.get(pid,[])
  ri=report_input(c,sources);rp=root/'results/demo/reports'/f"{pid.replace(':','__')}.json"
  report=json.loads(rp.read_text()) if rp.exists() else None
  if report and report.get('provenance',{}).get('input_sha256')==digest(ri):validate_report(report,ri)
  else:report=fallback(ri);report['generator']='Deterministic factual summary (no API call)'
  c['report']=report;out.append(c)
 out.sort(key=lambda c:(c.get('score_rna') is None,-(c.get('score_rna') or 0),c['pair_id']))
 metricpath=root/'results/classifier/metrics.json';metrics=json.loads(metricpath.read_text()) if metricpath.exists() else {'status':'unavailable','limitations':['Model evaluation is not available in this export.']}
 manifestpath=task/'manifest.json'; manifest=json.loads(manifestpath.read_text()) if manifestpath.exists() else {}
 return {'schema_version':1,'is_fixture':False,'generated_at':datetime.now(timezone.utc).isoformat(),'candidates':out,'metrics':metrics,'nvidia_pilot':pilot,'gpu_evidence_export_available':gpu_path.exists(),'sources':sources,'manifest':manifest,'data_scope':'Eligible probe-panel ordered gene pairs only; full discovery catalogue available in results/dataset_reconstruction/candidates.tsv; pair-level reported NanoString support, not biological authenticity.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);args=p.parse_args();data=build(args.root)
 dest=args.root/'demo';dest.mkdir(exist_ok=True)
 serialized=json.dumps(data,ensure_ascii=False,allow_nan=False)
 (dest/'data.json').write_text(serialized+'\n');(dest/'data.js').write_text('window.CHRNA_DATA = '+serialized.replace('</','<\\/')+';\n')
 print(f'Exported {len(data["candidates"])} real candidates to {dest}')
if __name__=='__main__':main()
