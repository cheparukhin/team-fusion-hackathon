"""Local source-region disorder and exact retained-fragment paired comparisons."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from analyze_disorder import summarize_scores
ROOT=Path(__file__).resolve().parents[2];b=ROOT/'results/structure_campaign';a=b/'analysis'
profiles=json.loads((a/'profiles.json').read_text());controls=json.loads((a/'controls/profiles.json').read_text())
orfs=pd.read_csv(b/'cohort/orf_hypotheses.tsv',sep='\t');orfs=orfs[orfs.annotated_donor_start & orfs.peptide_id.isin(profiles)].copy()
regions=pd.read_csv(b/'cohort/regions.tsv',sep='\t');regions=regions[regions.orf_id.isin(orfs.orf_id)]
rows=[]
for r in regions.itertuples():
 scores=profiles[r.peptide_id]['metapredict_v3'];lo=int(r.start_residue_1based)-1;hi=int(r.end_residue_1based)
 if not 0<=lo<hi<=len(scores):raise ValueError('Invalid source region')
 rows.append({'orf_id':r.orf_id,'peptide_id':r.peptide_id,'region':r.source_class,'start_residue_1based':lo+1,'end_residue_1based':hi,'n_residues':hi-lo,**summarize_scores(scores[lo:hi])})
for r in orfs.itertuples():
 scores=profiles[r.peptide_id]['metapredict_v3'];j=(r.junction_offset_0based-r.start_0based)/3
 lo=max(0,int(np.floor(j))-15);hi=min(len(scores),int(np.ceil(j))+15)
 rows.append({'orf_id':r.orf_id,'peptide_id':r.peptide_id,'region':'junction_window','start_residue_1based':lo+1,'end_residue_1based':hi,'n_residues':hi-lo,**summarize_scores(scores[lo:hi])})
r=pd.DataFrame(rows);r.to_csv(a/'region_metrics.tsv',sep='\t',index=False)
links=pd.read_csv(a/'controls/links.tsv',sep='\t');links=links[links.orf_id.isin(orfs.orf_id)&links.control_id.isin(controls)&links.control_type.eq('retained_canonical_fragment')]
pairs=[]
for row in links.itertuples():
 lo=int(row.candidate_residue_start_1based)-1;hi=int(row.candidate_residue_end_1based)
 candidate=profiles[row.peptide_id];control=controls[row.control_id]
 if candidate['sequence'][lo:hi]!=control['sequence']:raise ValueError('Retained-fragment control sequence mismatch')
 c=summarize_scores(candidate['metapredict_v3'][lo:hi]);p=summarize_scores(control['metapredict_v3'])
 pairs.append({'orf_id':row.orf_id,'peptide_id':row.peptide_id,'control_id':row.control_id,'start_residue_1based':lo+1,'end_residue_1based':hi,'length':hi-lo,'candidate_region_f_idr':c['f_idr'],'isolated_fragment_f_idr':p['f_idr'],'delta_f_idr':c['f_idr']-p['f_idr']})
p=pd.DataFrame(pairs)
if len(p):
 p=p.groupby(['peptide_id','control_id','start_residue_1based','end_residue_1based','length','candidate_region_f_idr','isolated_fragment_f_idr','delta_f_idr'],dropna=False).agg(orf_ids=('orf_id',lambda x:';'.join(sorted(set(x))))).reset_index()
p.to_csv(a/'paired_controls.tsv',sep='\t',index=False)
# Finite per-peptide averages over annotated-start hypotheses; source ambiguity retained.
per_region=r.groupby(['peptide_id','region']).agg(mean_f_idr=('f_idr','mean'),min_f_idr=('f_idr','min'),max_f_idr=('f_idr','max'),n_hypotheses=('orf_id','nunique')).reset_index()
per_region.to_csv(a/'region_peptide_summary.tsv',sep='\t',index=False)
summary={'n_annotated_start_orfs':len(orfs),'n_region_rows':len(r),'n_deduplicated_retained_fragment_comparisons':len(p),'retained_fragment_median_delta_f_idr':float(p.delta_f_idr.median())if len(p)else None,'caveat':'Delta compares identical amino acids predicted in full fusion context versus isolated fragment. It is not a biological effect size or independent experimental validation. Mapping alternatives are retained, not chosen by best prediction.'}
(a/'region_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
# Same retained amino acids in the complete native parent context, where available.
all_links=pd.read_csv(a/'controls/links.tsv',sep='\t')
full=all_links[all_links.control_type.eq('annotated_parent_complete_ORF') & all_links.control_id.isin(controls)]
full_by={}
for row in full.itertuples():full_by.setdefault((row.orf_id,row.transcript_id),set()).add(row.control_id)
native=[]
for row in links.itertuples():
 for cid in full_by.get((row.orf_id,row.transcript_id),[]):
  lo=int(row.candidate_residue_start_1based)-1;hi=int(row.candidate_residue_end_1based)
  ps=int(row.parent_residue_start_1based)-1;pe=int(row.parent_residue_end_1based)
  candidate=profiles[row.peptide_id];parent=controls[cid]
  if candidate['sequence'][lo:hi]!=parent['sequence'][ps:pe]:raise ValueError('Full-native parent segment mismatch')
  cf=summarize_scores(candidate['metapredict_v3'][lo:hi])['f_idr'];pf=summarize_scores(parent['metapredict_v3'][ps:pe])['f_idr']
  native.append({'orf_id':row.orf_id,'peptide_id':row.peptide_id,'parent_control_id':cid,'start_residue_1based':lo+1,'end_residue_1based':hi,'parent_start_residue_1based':ps+1,'parent_end_residue_1based':pe,'length':hi-lo,'candidate_region_f_idr':cf,'native_parent_region_f_idr':pf,'delta_f_idr':cf-pf})
n=pd.DataFrame(native)
if len(n):
 keys=[c for c in n.columns if c!='orf_id'];n=n.groupby(keys,dropna=False).agg(orf_ids=('orf_id',lambda x:';'.join(sorted(set(x))))).reset_index()
n.to_csv(a/'paired_native_regions.tsv',sep='\t',index=False)
summary['n_deduplicated_native_context_comparisons']=len(n)
summary['native_context_median_delta_f_idr']=float(n.delta_f_idr.median())if len(n)else None
summary['native_context_mean_delta_f_idr']=float(n.delta_f_idr.mean())if len(n)else None
(a/'region_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('Native paired regions',len(n),summary['native_context_median_delta_f_idr'])
x=per_region[per_region.region.isin(['parent_a_canonical','parent_b_out_of_frame'])].pivot(index='peptide_id',columns='region',values='mean_f_idr').dropna()
x['out_of_frame_minus_retained_donor']=x.parent_b_out_of_frame-x.parent_a_canonical
x.to_csv(a/'paired_novel_tail_regions.tsv',sep='\t')
tail={'n_paired_peptides':len(x),'median_out_of_frame_fraction':float(x.parent_b_out_of_frame.median()),'median_retained_donor_fraction':float(x.parent_a_canonical.median()),'median_paired_difference':float(x.out_of_frame_minus_retained_donor.median()),'note':'Exploratory within-hypothesis source-region comparison; short tails, unequal lengths, shared parents and alternative mappings limit inference. Means across valid source ORFs are a descriptive convention.'}
(a/'novel_tail_summary.json').write_text(json.dumps(tail,indent=2)+'\n')
