"""Freeze eight diagnostic seed repeats after the descriptive first pass.

Purposive quadrants include discordant cases; this panel estimates no prevalence.
"""
from pathlib import Path
import json,hashlib,shutil,pandas as pd
ROOT=Path(__file__).resolve().parents[2];b=ROOT/'results/structure_campaign';out=b/'selection/seed_repeats';out.mkdir(parents=True,exist_ok=True)
s=pd.read_csv(b/'selection/selection.tsv',sep='\t');m=pd.read_csv(b/'compute/model_metrics.tsv',sep='\t');p=pd.read_csv(b/'cohort/peptides.tsv',sep='\t')
m=m[m.protocol_id.eq('boltz2_2.2.1_single_sequence')&m.role.eq('sensitivity')&m.seed.eq(20260919)]
if len(m)!=43 or not m.status.isin(['verified','failed','deferred','unavailable']).all():raise RuntimeError('Wait for complete terminal first-pass candidate ledger')
snapshot=out/'source_snapshot';snapshot.mkdir(exist_ok=True)
shutil.copyfile(b/'compute/model_metrics.tsv',snapshot/'model_metrics.tsv')
x=s[s.role.eq('sensitivity')].merge(m[m.status.eq('verified')][['peptide_id','mean_plddt']],on='peptide_id')
x['high_disorder']=x.f_idr.gt(.5);x['high_mean_confidence']=x.mean_plddt.ge(70)
selected=[]
reference=x[x.pair_ids.fillna('').str.contains('Gsdmd:Tmem106a')]
if len(reference):selected.append(reference.iloc[0].peptide_id)
for _,g in x.groupby(['high_disorder','high_mean_confidence'],sort=True):
 selected.extend(g.sort_values('sequence_sha256').peptide_id.head(2))
selected=list(dict.fromkeys(selected))[:8]
for key in x.sort_values('sequence_sha256').peptide_id:
 if len(selected)>=8:break
 if key not in selected:selected.append(key)
r=x[x.peptide_id.isin(selected)].copy();r['calibration']=False;r['deep_dive']=True;r['selection_reason']='diagnostic_disorder_confidence_quadrants_plus_functional_reference';r['population_estimation']=False
r.to_csv(out/'selection.tsv',sep='\t',index=False)
seqs=p.set_index('peptide_id').sequence
(out/'selected.fasta').write_text(''.join(f'>{key}\n{seqs[key]}\n'for key in r.peptide_id))
manifest={'purpose':'Prediction robustness, not thermodynamic ensembles; diagnostic purposive sample, not population sampling.','n_peptides':len(r),'new_seed_jobs':2*len(r),'first_seed':'reuse actual matching single-sequence20260919 results','additional_seeds':[20260920,20260921],'selection_rule':'Gsdmd reference if complete; two lowest peptide hashes in each f_IDR>0.5 x mean_pLDDT>=70 quadrant; stable hash fill to8. Empty quadrants explicit in table.','source_metrics_sha256':hashlib.sha256((b/'compute/model_metrics.tsv').read_bytes()).hexdigest()}
manifest['source_metrics_snapshot']=str((snapshot/'model_metrics.tsv').relative_to(ROOT))
manifest['source_selection_sha256']=hashlib.sha256((b/'selection/selection.tsv').read_bytes()).hexdigest()
manifest['code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
manifest['output_sha256']={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ['selection.tsv','selected.fasta']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
