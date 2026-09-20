"""Join independent evidence axes without inventing a probability of function."""
from pathlib import Path
import json,pandas as pd
ROOT=Path(__file__).resolve().parents[2];b=ROOT/'results/structure_campaign'
x=pd.read_csv(b/'analysis/disorder_summary.tsv',sep='\t')
a=pd.read_csv(b/'domains/architectures.tsv',sep='\t');a=a[a.role.eq('conditional_candidate')].rename(columns={'sequence_id':'peptide_id','pfam_domain_hit_count':'pfam_GA_hit_count','distinct_pfam_count':'pfam_distinct_family_count','aligned_residue_union_coverage':'pfam_aligned_residue_coverage','architecture':'pfam_architecture'})
x=x.merge(a[['peptide_id','pfam_GA_hit_count','pfam_distinct_family_count','pfam_aligned_residue_coverage','pfam_architecture','domain_status']],on='peptide_id',how='left')
r=pd.read_csv(b/'domains/parent_domain_retention.tsv',sep='\t');qualified=r[(r.parent_domain_hmm_coverage>=.8)&(r.retained_aligned_span_fraction>=.9)]
x['any_source_hypothesis_retains_90pct_parent_domain_span']=x.peptide_id.isin(qualified.peptide_id)
m=pd.read_csv(b/'compute/model_metrics.tsv',sep='\t');m=m[m.status.isin(['verified','cached_verified']) & m.seed.eq(20260919)]
for protocol,prefix in [('boltz2_2.2.1_single_sequence','single_sequence'),('boltz2_2.2.1_precomputed','msa_backed')]:
 v=m[m.protocol_id.eq(protocol)].drop_duplicates('peptide_id');cols=['mean_plddt','fraction_plddt_ge70','ptm']
 v=v[['peptide_id',*cols]].rename(columns={c:prefix+'_'+c for c in cols});x=x.merge(v,on='peptide_id',how='left');x[prefix+'_model_available']=x[prefix+'_mean_plddt'].notna()
x['protein_translation_status']='not_established_for_current_hypothesis';x['function_status']='unknown';x['paper_functional_reference']=x.pair_ids.fillna('').str.contains('Gsdmd:Tmem106a');x['interpretation']='Conditional reconstruction; evidence axes are not a function probability.'
x.to_csv(b/'analysis/candidate_evidence_table.tsv',sep='\t',index=False)
(b/'analysis/candidate_evidence_schema.json').write_text(json.dumps({'rows':'188conditional annotated-start peptide hypotheses; no ranking by an invented function score','parent_retention_flag':'At least one compatible source mapping retains>=90%of a parental aligned Pfam span whose parent hit covers>=80%of its HMM. This is an any-hypothesis flag, not resolved isoform evidence.','confidence':'Firstseed20260919 only; engines/protocols in separate columns. Missing structures remain blank, never zero.','paper_functional_reference':'Flags the paper exemplar, not a new validation experiment or blanket confirmation of our full transcript reconstruction.','disorder':'metapredict V3 residue score>=0.5; f_IDR>0.5 defines predominantly disordered computationally.'},indent=2)+'\n')
print('Evidence rows',len(x))
