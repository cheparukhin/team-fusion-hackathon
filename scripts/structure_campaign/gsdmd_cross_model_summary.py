"""Join exact-reference folding and disorder evidence without a function score."""
from pathlib import Path
import csv,hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'results/structure_campaign/cross_model_gsdmd'
SHA='f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa'
def read(path):return json.loads(path.read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 inputs=[BASE/'baseline_models.json',ROOT/'results/structure_campaign/analysis/profiles.json']
 models=read(inputs[0])['models']
 for path in [BASE/'compute/model_index.json',BASE/'nim/model_index.json']:
  if path.exists():
   inputs.append(path);models.extend(read(path)['models'])
 audit_path=BASE/'analysis/model_audit.tsv'
 audits={}
 if audit_path.exists():
  inputs.append(audit_path)
  audits={r['model_id']:r for r in csv.DictReader(audit_path.open(),delimiter='\t')}
 manifest_path=BASE/'analysis/manifest.json'
 if not manifest_path.exists():raise ValueError('Missing independent audit manifest')
 inputs.append(manifest_path)
 for path,expected in read(manifest_path)['input_sha256'].items():
  if digest(ROOT/path)!=expected:raise ValueError('Stale source-index audit: '+path)
 for path in [BASE/'baseline_models.json',BASE/'compute/model_index.json',BASE/'nim/model_index.json']:
  if path.exists() and str(path.relative_to(ROOT)) not in read(manifest_path)['input_sha256']:raise ValueError('Model index not independently audited: '+str(path))
 seen=set()
 for m in models:
  if m['model_id']in seen:raise ValueError('Duplicate model ID')
  seen.add(m['model_id'])
  if m['sequence_sha256']!=SHA or m['length_aa']!=118:raise ValueError('Mixed reference sequences')
  m.setdefault('confidence_metric','pLDDT');m.setdefault('reused_prior_prediction',False)
  a=audits.get(m['model_id'],{})
  m['sequence_audit_passed']=a.get('coordinate_status')=='verified' and a.get('confidence_status')=='verified_0_100_plddt'
  if m['sequence_audit_passed']:
   for field,hash_key in [('model_path','coordinate_sha256'),('residue_confidence_tsv','confidence_sha256')]:
    if digest(ROOT/m[field])!=a[hash_key]:raise ValueError('Stale artifact audit: '+m['model_id'])
  m['sequence_verified']=m['sequence_audit_passed']
  if m['status']=='verified' and not m['sequence_audit_passed']:raise ValueError('Verified model lacks independent coordinate and confidence audit: '+m['model_id'])
  if m.get('model_path'):inputs.append(ROOT/m['model_path'])
  m.setdefault('png',None);m.setdefault('mean_plddt',None)
  if m.get('residue_confidence_tsv') and m['status']=='verified':
   path=ROOT/m['residue_confidence_tsv'];inputs.append(path)
   rows=list(csv.DictReader(path.open(),delimiter='\t'))
   if len(rows)!=118:raise ValueError('Wrong confidence length')
   if m['confidence_scale']not in ['0-100','0_100','0–100']:raise ValueError('Confidence units must be explicit before comparison')
   vals=np.array([float(r['plddt'])for r in rows]);seq=''.join(r['aa']for r in rows)
   if hashlib.sha256(seq.encode()).hexdigest()!=SHA or not np.isfinite(vals).all() or vals.min()<0 or vals.max()>100:raise ValueError('Confidence identity/range failure')
   m['mean_plddt']=float(vals.mean());m['fraction_plddt_ge70']=float((vals>=70).mean());m['fraction_plddt_below50']=float((vals<50).mean());m['donor_mean_plddt']=float(vals[:73].mean());m['tail_mean_plddt']=float(vals[73:].mean())
  m['representative_for_slide']=(m.get('seed')in [None,20260919]) and not m.get('parameter_variant_nonrepresentative',False)
  png=BASE/'report/structures'/f"{m['model_id']}.png"
  if png.exists():m['png']=str(png.relative_to(ROOT))
 profile=read(inputs[1])['peptide_'+SHA]
 sequence=profile['sequence']
 if hashlib.sha256(sequence.encode()).hexdigest()!=SHA:raise ValueError('Disorder reference mismatch')
 methods=[];traces=[]
 for key,label,threshold in [('metapredict_v3','metapredict V3',.5),('metapredict_v1_sensitivity','metapredict V1',.42)]:
  values=np.asarray(profile[key]);called=values>=threshold
  methods.append({'method':label,'version':'metapredict package 3.0.2','sequence_sha256':SHA,'fraction_disordered':float(called.mean()),'donor_fraction_disordered':float(called[:73].mean()),'tail_fraction_disordered':float(called[73:].mean()),'threshold':f'score >= {threshold}','independence_note':'V1/V3 are related networks; V3 includes AlphaFold-derived training information.'})
  traces.extend({'method':label,'residue':i+1,'aa':aa,'score':float(score),'disordered':bool(d),'sequence_sha256':SHA}for i,(aa,score,d)in enumerate(zip(sequence,values,called)))
 more=BASE/'method_audit/moreronn_summary.json'
 if more.exists():
  inputs.append(more);r=read(more)
  if r['sequence_sha256']!=SHA:raise ValueError('MoreRONN sequence mismatch')
  region={a['region']:a for a in r['regions']}
  methods.append({'method':'MoreRONN','version':r['version'],'sequence_sha256':SHA,'fraction_disordered':region['whole_peptide']['fraction_disordered'],'donor_fraction_disordered':region['retained_Gsdmd']['fraction_disordered'],'tail_fraction_disordered':region['junction_novel_tail']['fraction_disordered'],'threshold':r['threshold'],'independence_note':'Independent RONN-family sequence method; not an experimental assay.'})
  path=BASE/'method_audit/moreronn_residues.tsv';inputs.append(path)
  for row in csv.DictReader(path.open(),delimiter='\t'):traces.append({'method':'MoreRONN','residue':int(row['residue']),'aa':row['aa'],'score':float(row['score']),'disordered':row['disordered']=='True','sequence_sha256':SHA})
 for method in methods:method['name']=method['method']
 target=BASE/'inputs';target.mkdir(exist_ok=True)
 with (target/'disorder_profiles.tsv').open('w')as f:
  writer=csv.DictWriter(f,fieldnames=list(traces[0]),delimiter='\t');writer.writeheader();writer.writerows(traces)
 unavailable=[]
 for engine in ['alphafold2','openfold2','openfold3']:
  path=BASE/'nim'/engine/'status.json'
  if path.exists():
   inputs.append(path);r=read(path)
   if not any(m['protocol_id'].startswith(engine+'_nim') and m['status']=='verified'for m in models):unavailable.append({'engine':engine+' NIM','status':r['status'],'reason':r.get('reason',r.get('error_type','See raw saved response; no sequence-verified structure yet.'))})
 obj={'schema_version':1,'pair_id':'Gsdmd:Tmem106a','sequence_sha256':SHA,'length_aa':118,'sequence':sequence,'origin_boundary':{'parent_a_residues':[1,73],'parent_b_or_split_residues':[74,118],'split_codon_residue':74},'models':models,'disorder_methods':methods,'disorder_profiles_tsv':str((target/'disorder_profiles.tsv').relative_to(ROOT)),'unavailable_methods':unavailable,'interpretation':['Cross-model computational sensitivity, not experimental validation of this fusion.','pLDDT measures confidence, not percent disorder; confidence calibration differs between engines.','MSA-backed and sequence-only protocols differ in evidence as well as engine.','Parameter sets and random seeds are variants within a model family, not independent algorithm families.','The experimental 6N9N structure is parent-only context.'],'inputs_sha256':{str(p.relative_to(ROOT)):digest(p)for p in inputs},'builder_sha256':digest(Path(__file__))}
 (BASE/'comparison.json').write_text(json.dumps(obj,indent=2)+'\n')
 write_report(obj)
 print(json.dumps({'models':len(models),'verified_models':sum(m['status']=='verified'for m in models),'disorder_methods':len(methods),'unavailable_nim_methods':len(unavailable)}))
def write_report(obj):
 verified=[m for m in obj['models'] if m['status']=='verified']
 counts=f"{len(verified)} verified structures across {len({m['engine_family'] for m in verified})} engine families: {sum(not m['reused_prior_prediction'] for m in verified)} newly executed predictions and {sum(m['reused_prior_prediction'] for m in verified)} cached baseline predictions."
 lines=['# Gsdmd–Tmem106a: folding and disorder comparison','',
 'This is a computational sensitivity analysis of the exact 118-aa conditional fusion reconstruction. It is not experimental validation of translation, structure, or function. All coordinate and confidence records marked verified passed ordered sequence identity checks.','',
 '## Sequence-based disorder','',
 '| Predictor | Whole sequence | Gsdmd residues 1–73 | Novel tail 74–118 | Calling rule |',
 '|---|---:|---:|---:|---|']
 for m in obj['disorder_methods']:
  lines.append(f"| {m['method']} | {100*m['fraction_disordered']:.1f}% | {100*m['donor_fraction_disordered']:.1f}% | {100*m['tail_fraction_disordered']:.1f}% | {m['threshold']} |")
 lines+=['','The tail is called largely disordered by all three methods. The retained Gsdmd segment drives the disagreement about whole-sequence disorder. V1 and V3 are related metapredict networks; MoreRONN is a separate RONN-family sequence method. V3 includes AlphaFold-derived training information, so it is not fully orthogonal to structure-model confidence. Percent ordered alone is therefore an unstable basis for ranking this fusion’s functional viability.','',
 '## Actual folding outputs','',counts,'',
 '| Engine / protocol | Seed | Reused | Mean pLDDT | Gsdmd mean | Tail mean |',
 '|---|---:|---|---:|---:|---:|']
 for m in obj['models']:
  if m['status']=='verified':
   lines.append(f"| {m['engine']} / {m['protocol_id']} | {m.get('seed','—')} | {m['reused_prior_prediction']} | {m['mean_plddt']:.1f} | {m['donor_mean_plddt']:.1f} | {m['tail_mean_plddt']:.1f} |")
 lines+=['','Confidence measures are not calibrated across engines. Low pLDDT is not a direct disorder call. Seed repeats and parameter sets are within-family variants. MSA-backed versus sequence-only predictions also differ in available evidence. Pairwise fitted Cα RMSDs are available in [analysis/pairwise_CA_rmsd.tsv](analysis/pairwise_CA_rmsd.tsv); whole-chain and independently aligned donor/tail values are descriptive, especially in low-confidence regions.','',
 '## Access and incomplete tracks','']
 for m in obj['unavailable_methods']:
  lines.append(f"- {m['engine']}: {m['status']}. {m['reason']}")
 lines+=['','Local AlphaFold2 and ESMFold run on the existing CPU host; no GPU was resumed or new cloud allocation made. Local execution receipts and model availability are recorded under `compute/`. No pending or unsuccessful run is included as a structural result. See [PLAN.md](PLAN.md) for parallel execution scope.','',
 '## Reproduction and provenance','',
 'Run from the repository root after inference outputs are available:', '', '```bash',
 '.venv-disorder/bin/python scripts/structure_campaign/gsdmd_cross_model_compare.py',
 '.venv/bin/python scripts/structure_campaign/gsdmd_cross_model_summary.py', '```','',
 '[comparison.json](comparison.json) records exact sequence and input hashes. [analysis/METHODS.md](analysis/METHODS.md) documents coordinate validation and alignment; [method_audit/METHODS.md](method_audit/METHODS.md) documents MoreRONN and provider access. Source-colored cartoons use blue for residues 1–73 and red for residues 74–118; the latter includes a junction codon and novel-frame tail, not an intact canonical TMEM106A domain. PDB 6N9N supplies experimental parent-only context, not a fusion ground truth.','',
 'This single illustrative reference cannot estimate disorder prevalence or structural diversity of the wider chRNA population. The separately frozen 188-peptide hypothesis cohort and 67-prediction campaign remain unchanged.','']
 (BASE/'RESULTS.md').write_text('\n'.join(lines))
if __name__=='__main__':main()
