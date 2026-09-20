from pathlib import Path
import json,hashlib,pandas as pd
ROOT=Path(__file__).resolve().parents[2];b=ROOT/'results/structure_campaign';out=b/'analysis/controls';out.mkdir(parents=True,exist_ok=True)
p=pd.read_csv(b/'cohort/peptides.tsv',sep='\t');o=pd.read_csv(b/'cohort/orf_hypotheses.tsv',sep='\t');l=pd.read_csv(b/'cohort/control_links.tsv',sep='\t');c=pd.read_csv(b/'cohort/parent_controls.tsv',sep='\t')
valid=o[o.annotated_donor_start & o.peptide_id.isin(p[p.conditional_census_eligible].peptide_id)]
l=l[l.orf_id.isin(valid.orf_id)]
c=c[c.control_id.isin(l.control_id)].copy();c['sequence_analysis_eligible']=c.length_aa.ge(30)
c.to_csv(out/'control_audit.tsv',sep='\t',index=False)
c=c[c.sequence_analysis_eligible].copy();c['peptide_id']=c.control_id;c['role']='control';c['cohort_tier']=c.control_types;c['pair_ids']=''
c.to_csv(out/'metadata.tsv',sep='\t',index=False)
(out/'sequences.fasta').write_text(''.join(f'>{r.control_id}\n{r.sequence}\n'for r in c.itertuples()))
l.to_csv(out/'links.tsv',sep='\t',index=False)
(out/'selection.json').write_text(json.dumps({'n_controls':len(c),'n_links':len(l),'minimum_length':30,'reason':'Avoid extrapolating protein disorder networks to very short isolated fragments; shorter controls stay in audit.','input_sha256':{str(z.relative_to(ROOT)):hashlib.sha256(z.read_bytes()).hexdigest() for z in [b/'cohort/parent_controls.tsv',b/'cohort/control_links.tsv',b/'cohort/orf_hypotheses.tsv']}},indent=2)+'\n');print('Controls',len(c))
