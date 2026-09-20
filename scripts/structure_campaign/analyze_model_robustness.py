"""Per-junction model confidence/PAE, geometry checks and within-protocol seed robustness."""
import argparse,json,itertools
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2]

def fitted_rmsd(a,b):
 a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
 if a.shape!=b.shape or a.ndim!=2 or a.shape[1]!=3 or len(a)<3:raise ValueError('At least three matched3D coordinates required')
 a=a-a.mean(0);b=b-b.mean(0);u,_,vt=np.linalg.svd(a.T@b);d=np.linalg.det(u@vt);r=u@np.diag([1,1,d])@vt
 return float(np.sqrt(np.mean(np.sum((a@r-b)**2,axis=1))))

def coordinates(path):
 import gemmi
 structure=gemmi.read_structure(str(path));return np.array([[r['CA'][0].pos.x,r['CA'][0].pos.y,r['CA'][0].pos.z]for r in structure[0][0]])

def main(base):
 jobs=json.loads((base/'compute/jobs.json').read_text());jobs=[j for j in jobs if j['status']in ('verified','cached_verified')]
 orfs=pd.read_csv(base/'cohort/orf_hypotheses.tsv',sep='\t');orfs=orfs[orfs.annotated_donor_start]
 models={};local=[];qc=[]
 for j in jobs:
  files=j['artifacts'];ca=coordinates(files['model.cif']);plddt=np.load(files['plddt.npz'])['plddt'].reshape(-1)*100;pae=np.load(files['pae.npz'])['pae']
  if len(ca)!=len(plddt)or pae.shape!=(len(ca),len(ca)):raise ValueError('Coordinate/confidence mismatch')
  models[j['job_id']]=(ca,plddt,j)
  steps=np.linalg.norm(np.diff(ca,axis=0),axis=1)
  qc.append({'job_id':j['job_id'],'peptide_id':j['peptide_id'],'protocol_id':j['protocol_id'],'seed':j['seed'],'length':len(ca),'ca_step_outside_2_8_to_4_3A':int(((steps<2.8)|(steps>4.3)).sum()),'max_ca_step_A':float(steps.max())if len(steps)else None,'radius_of_gyration_A':float(np.sqrt(np.mean(np.sum((ca-ca.mean(0))**2,axis=1)))),'interpretation':'Geometry context only; compactness and CA distances are not function/stability scores.'})
  source=orfs[orfs.peptide_id.eq(j['peptide_id'])].copy();source['junction_coding_nt']=source.junction_offset_0based-source.start_0based
  for nt,g in source.groupby('junction_coding_nt'):
   left=int(nt//3);right=int((nt+2)//3);lo=max(0,left-15);hi=min(len(ca),right+15)
   # Exclude split codon from cross-parent blocks; both directions of PAE are retained.
   a=pae[max(0,left-15):left,right:min(len(ca),right+15)];b=pae[right:min(len(ca),right+15),max(0,left-15):left]
   local.append({'job_id':j['job_id'],'peptide_id':j['peptide_id'],'protocol_id':j['protocol_id'],'seed':j['seed'],'junction_coding_nt':int(nt),'split_junction_codon':bool(nt%3),'junction_window_start_1based':lo+1,'junction_window_end_1based':hi,'junction_mean_plddt':float(plddt[lo:hi].mean()),'junction_fraction_plddt_ge70':float((plddt[lo:hi]>=70).mean()),'cross_junction_pae_mean_A':float(np.mean(np.concatenate([a.ravel(),b.ravel()])))if a.size and b.size else None,'orf_ids':';'.join(sorted(g.orf_id)),'pair_ids':';'.join(sorted(set(g.pair_id)))})
 comparisons=[]
 for (_,protocol),group in itertools.groupby(sorted(models.values(),key=lambda x:(x[2]['sequence_sha256'],x[2]['protocol_id'])),key=lambda x:(x[2]['sequence_sha256'],x[2]['protocol_id'])):
  for (a,pa,ja),(b,pb,jb)in itertools.combinations(group,2):
   if ja['seed']==jb['seed']:continue
   mask=(pa>=70)&(pb>=70)
   comparisons.append({'peptide_id':ja['peptide_id'],'protocol_id':protocol,'seed_a':ja['seed'],'seed_b':jb['seed'],'whole_chain_fitted_ca_rmsd_A':fitted_rmsd(a,b),'common_confident_residues':int(mask.sum()),'confident_fitted_ca_rmsd_A':fitted_rmsd(a[mask],b[mask])if mask.sum()>=3 else None,'interpretation':'Prediction-seed robustness, not an experimental ensemble or thermodynamic stability.'})
 out=base/'analysis';pd.DataFrame(local).to_csv(out/'model_region_metrics.tsv',sep='\t',index=False);pd.DataFrame(qc).to_csv(out/'model_geometry_qc.tsv',sep='\t',index=False);pd.DataFrame(comparisons).to_csv(out/'seed_robustness.tsv',sep='\t',index=False)
 summary={'verified_models':len(jobs),'junction_metric_rows':len(local),'same_protocol_seed_comparisons':len(comparisons)}
 (out/'structure_metric_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=ROOT/'results/structure_campaign');main(p.parse_args().base)
