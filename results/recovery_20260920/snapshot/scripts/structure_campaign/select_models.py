"""Freeze descriptive conditional structure panel, never promote it to strict primary."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'results/structure_campaign';out=base/'selection';out.mkdir(exist_ok=True)
p=pd.read_csv(base/'cohort/peptides.tsv',sep='\t');d=pd.read_csv(base/'analysis/disorder_summary.tsv',sep='\t')
x=p[p.conditional_census_eligible].merge(d[['peptide_id','f_idr']],on='peptide_id')
x['length_band']=pd.cut(x.length_aa,[0,150,300,600,float('inf')],labels=['short','medium','long','very_long'])
x['disorder_band']=pd.cut(x.f_idr,[-.001,.2,.5,1],labels=['low','intermediate','high'])
consensus=x[x.eligibility_tier.eq('conditional_consensus')].sort_values('sequence_sha256')
ambiguous=x[~x.eligibility_tier.eq('conditional_consensus')].sort_values('sequence_sha256')
rng=np.random.default_rng(42);extra=[]
for _,g in ambiguous.groupby(['length_band','disorder_band'],observed=True):
 extra.append(g.iloc[int(rng.integers(len(g)))].to_dict())
extras=pd.DataFrame(extra)
selected=pd.concat([consensus,extras],ignore_index=True)
ref=x[x.calibration_reference]
selected=pd.concat([selected,ref],ignore_index=True).drop_duplicates('sequence_sha256')
# Twelve length-spanning pilot cases, including extremes. Selection is diagnostic.
order=selected.sort_values(['length_aa','sequence_sha256'])
calibration=set(order.iloc[np.unique(np.linspace(0,len(order)-1,min(12,len(order))).round().astype(int))].peptide_id)
rows=[]
for r in selected.to_dict('records'):
 rows.append({'peptide_id':r['peptide_id'],'sequence_sha256':r['sequence_sha256'],'role':'sensitivity','sequence_audit_passed':True,'calibration':r['peptide_id']in calibration,'deep_dive':False,'selection_cohort':r['eligibility_tier'],'orf_assumptions':'Public GENCODE M28 annotated donor start and exon-prefix/suffix across exact probe junction; full fusion exon chain and translation unobserved.','pair_ids':r['pair_ids'],'length_aa':r['length_aa'],'f_idr':r['f_idr'],'sequence':r['sequence'],'selection_reason':'all_conditional_consensus' if r['eligibility_tier']=='conditional_consensus' else ('published_architecture_reference' if r['calibration_reference'] else 'one_random_per_length_disorder_stratum'),'population_estimation':False})
links_source=out/'source_snapshot/control_links.tsv'
if not links_source.exists():
 links_source=base/'cohort/control_links.tsv'
links=pd.read_csv(links_source,sep='\t');orfs=pd.read_csv(base/'cohort/orf_hypotheses.tsv',sep='\t')
validorfs=set(orfs[orfs.annotated_donor_start].orf_id)
links=links[links.orf_id.isin(validorfs)&links.peptide_id.isin(selected.peptide_id)]
controls=pd.read_csv(base/'cohort/parent_controls.tsv',sep='\t')
controls=controls[controls.control_id.isin(links.control_id)&controls.length_aa.between(30,600)]
# Twelve controls provide bounded contextual comparisons, not a fully matched experiment.
controls=controls.sort_values(['control_types','sequence_sha256'])
chosen=[]
for _,g in controls.groupby('control_types',sort=True):
 take=min(6,len(g));chosen.extend(g.iloc[np.unique(np.linspace(0,len(g)-1,take).round().astype(int))].to_dict('records'))
for r in chosen[:12]:
 if r['sequence_sha256'] in {z['sequence_sha256']for z in rows}:continue
 rows.append({'peptide_id':r['control_id'],'sequence_sha256':r['sequence_sha256'],'role':'control','sequence_audit_passed':True,'calibration':True,'deep_dive':False,'selection_cohort':r['control_types'],'orf_assumptions':'Reference parent sequence or exact retained canonical fragment; contextual control.','pair_ids':'','length_aa':r['length_aa'],'sequence':r['sequence'],'selection_reason':'bounded_parent_fragment_control','population_estimation':False})
f=pd.DataFrame(rows);f.drop(columns=['sequence']).to_csv(out/'selection.tsv',sep='\t',index=False)
(out/'selected.fasta').write_text(''.join(f">{r['peptide_id']}\n{r['sequence']}\n"for r in rows))
links[links.control_id.isin(f[f.role.eq('control')].peptide_id)].to_csv(out/'control_links.tsv',sep='\t',index=False)
manifest={'status':'frozen','strict_primary_count':0,'conditional_candidates':int(f.role.eq('sensitivity').sum()),'controls':int(f.role.eq('control').sum()),'seed':42,'purpose':'Conditional descriptive panel, not representative of all109pairs or all188hypotheses. Consensus census plus one random ambiguous peptide per nonempty length/disorder stratum and published reference.','deep_dive':'Select after first-pass confidence results, at most20 with twoextra seeds; separate frozen stage.','inputs':{str(z.relative_to(ROOT)):hashlib.sha256(z.read_bytes()).hexdigest() for z in [base/'cohort/peptides.tsv',base/'analysis/disorder_summary.tsv',links_source]},'outputs':{z.name:hashlib.sha256(z.read_bytes()).hexdigest() for z in out.glob('*') if z.is_file() and z.name!='manifest.json'}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
