#!/usr/bin/env python3
"""Validate exact Gsdmd models and atomically publish the cross-engine interface."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
import gemmi
SHA='f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa'

def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve();repo=Path(__file__).resolve().parents[2]
 seq=''.join(x.strip()for x in(root/'inputs/sequence.fasta').read_text().splitlines()if not x.startswith('>'));assert len(seq)==118 and hashlib.sha256(seq.encode()).hexdigest()==SHA
 rel=lambda p:str(Path(p).resolve().relative_to(repo))
 models=[]
 for modelid,engine,protocol,folder in [('af2_model1_ptm_seed20260919','AlphaFold2','colabfold1.5.5_af2_ptm_model1_cached_msa','af2_cpu'),('esmfold_v1_seed20260919','ESMFold','transformers4.57.3_esmfold_v1_single_sequence','esmfold_cpu')]:
  d=root/folder;r=json.loads((d/'run.json').read_text())if(d/'run.json').exists()else{}
  m={'model_id':modelid,'engine_family':engine,'engine':engine,'protocol_id':protocol,'status':'running'if r.get('status')=='running'else'not_run','sequence_sha256':SHA,'length_aa':118,'seed':20260919,'confidence_scale':'0-100','confidence_metric':'pLDDT','msa_mode':'cached_precomputed'if engine=='AlphaFold2'else'single_sequence','reused_prior_prediction':False,'source_boundary':'Blue residues1–73; red residues74–118 (novel out-of-frame tail)','run_receipt':rel(d/'run.json'),'limitations':['Reference-assisted candidate ORF; not experimentally solved protein.','pLDDT is model confidence, not disorder or function.']}
  if r.get('status')=='failed':m.update(status='failed',failure_reason=r.get('error',r.get('failure_reason','See preserved run log')))
  if r.get('status')!='process_completed':models.append(m);continue
  if engine=='AlphaFold2':
   pdbs=list((d/'raw').glob('*unrelaxed_rank_001*model_1*seed_20260919.pdb'));scores=list((d/'raw').glob('*scores_rank_001*model_1*seed_20260919.json'));assert len(pdbs)==len(scores)==1
   raw=pdbs[0];score=json.loads(scores[0].read_text());conf=np.asarray(score['plddt'],float);pae=np.asarray(score['pae'],float)
  else:
   raw=d/'model.pdb';rows=list(csv.DictReader((d/'residue_confidence.tsv').open(),delimiter='\t'));conf=np.asarray([float(x['plddt'])for x in rows]);pae=np.load(d/'pae.npz')['pae']
  st=gemmi.read_structure(str(raw));chains=[c for c in st[0]if any(r.find_atom('CA','*')for r in c)];assert len(st)==len(chains)==1
  residues=[x for x in chains[0]if x.find_atom('CA','*')];observed=''.join(gemmi.find_tabulated_residue(x.name).one_letter_code for x in residues);assert observed==seq and len(residues)==118
  assert len(conf)==118 and np.isfinite(conf).all()and conf.min()>=0 and conf.max()<=100
  assert pae.shape==(118,118)and np.isfinite(pae).all()and pae.min()>=0
  dest=d/'verified';dest.mkdir(exist_ok=True)
  for i,res in enumerate(residues):
   assert res.seqid.num==i+1
   for atom in res:atom.b_iso=float(conf[i])
  pdb=dest/'model.pdb';cif=dest/'model.cif';st.write_pdb(str(pdb));st.make_mmcif_document().write_file(str(cif));tab=dest/'residue_confidence.tsv'
  with tab.open('w')as f:
   w=csv.writer(f,delimiter='\t');w.writerow(['residue','aa','plddt']);w.writerows((i+1,aa,float(v))for i,(aa,v)in enumerate(zip(seq,conf)))
  np.savez_compressed(dest/'pae.npz',pae=pae)
  m.update(status='verified',model_path=rel(cif),pdb_path=rel(pdb),raw_model_path=rel(raw),residue_confidence_tsv=rel(tab),pae_path=rel(dest/'pae.npz'),wall_seconds=r['wall_seconds'],mean_plddt=float(conf.mean()),fraction_plddt_ge70=float((conf>=70).mean()),fraction_plddt_ge90=float((conf>=90).mean()),fraction_plddt_lt50=float((conf<50).mean()),weight_revision=r.get('weight_revision','alphafold_params_2021-07-14'),artifact_sha256={x.name:digest(x)for x in[pdb,cif,tab,dest/'pae.npz']})
  png=dest/'cartoon.png'
  if png.exists():m['png']=rel(png);m['artifact_sha256'][png.name]=digest(png)
  models.append(m)
 out={'sequence_sha256':SHA,'length_aa':118,'models':models,'selection':'One fixed model/seed per engine, not selected by confidence','new_cloud_allocation_usd':0}
 tmp=root/'model_index.json.tmp';tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(root/'model_index.json');print(json.dumps({m['engine']:m['status']for m in models}))
if __name__=='__main__':main()
