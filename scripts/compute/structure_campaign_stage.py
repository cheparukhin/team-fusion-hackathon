#!/usr/bin/env python3
"""Freeze explicit sequence selections and reuse only sequence/protocol-matched models.

No GPU or network actions. Every input must already have passed the coordinator's
sequence and sampling gates. The selected TSV never silently promotes sensitivity ORFs.
"""
import argparse,csv,hashlib,json,shutil
from pathlib import Path
from datetime import datetime,timezone
SETTINGS={'model':'boltz2','boltz_version':'2.2.1','recycling_steps':3,'sampling_steps':200,'diffusion_samples':1,'step_scale':1.5,'write_full_pae':True}
SEEDS=[20260919,20260920,20260921]
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(p.suffix+'.partial');q.write_text(json.dumps(d,indent=2)+'\n');q.replace(p)
def fasta(p):
 result={};key=None
 for line in Path(p).read_text().splitlines():
  if line.startswith('>'):key=line[1:].split()[0];assert key not in result;result[key]=''
  elif line.strip():
   if key is None:raise ValueError('FASTA sequence before header')
   result[key]+=line.strip()
 return result

def validate_model(sequence,cif,plddt,pae):
 import gemmi,numpy as np
 s=gemmi.read_structure(str(cif))
 if len(s)!=1 or len(s[0])!=1:raise ValueError('Expected single-chain single-model prediction')
 residues=list(s[0][0]);observed=''.join(gemmi.find_tabulated_residue(r.name).one_letter_code.upper()for r in residues)
 if observed!=sequence:raise ValueError('Coordinate sequence mismatch')
 for r in residues:
  ca=[a for a in r if a.name=='CA']
  if len(ca)!=1 or not np.isfinite([ca[0].pos.x,ca[0].pos.y,ca[0].pos.z]).all():raise ValueError('Invalid alpha carbon')
 p=np.load(plddt)['plddt'].reshape(-1);e=np.load(pae)['pae'];n=len(sequence)
 if p.shape!=(n,)or not np.isfinite(p).all()or not ((p>=0)&(p<=1)).all():raise ValueError('Invalid pLDDT0–1')
 if e.shape!=(n,n)or not np.isfinite(e).all()or (e<0).any():raise ValueError('Invalid PAE matrix')
 return {'sequence_matches':True,'length_aa':n,'mean_plddt':float(p.mean()*100),'fraction_plddt_below_50':float((p<.5).mean()),'fraction_plddt_ge70':float((p>=.7).mean()),'fraction_plddt_ge90':float((p>=.9).mean()),'mean_pae_angstrom':float(e.mean())}

def stage(args):
 msa_mode=getattr(args,'msa_mode','precomputed')
 seqs=fasta(args.fasta)
 with args.selection.open()as f:rows=list(csv.DictReader(f,delimiter='\t'))
 seen=set();jobs=[]
 for r in rows:
  key=r['peptide_id'];role=r['role']
  if role not in {'primary','sensitivity','control','reference_control'}:raise ValueError('No implicit promotion of sensitivity sequences')
  if key in seen:raise ValueError('Deduplicate selected peptides before staging')
  seen.add(key);seq=seqs[key]
  if not seq or set(seq)-set('ACDEFGHIKLMNPQRSTVWY'):raise ValueError('Only complete standard amino-acid sequences accepted')
  sha=hashlib.sha256(seq.encode()).hexdigest()
  if r['sequence_sha256']!=sha:raise ValueError('Frozen sequence hash mismatch')
  if r.get('sequence_audit_passed','').lower()not in {'true','1'}:raise ValueError('Conditional or primary sequence-audit gate not passed')
  if role=='sensitivity' and (not r.get('selection_cohort') or not r.get('orf_assumptions')):raise ValueError('Sensitivity inputs require explicit cohort and ORF assumptions')
  for seed in SEEDS[:3 if r.get('deep_dive','').lower()in {'true','1'} else 1]:
   jobs.append({'job_id':f'protein_{sha}_{msa_mode}_seed{seed}','peptide_id':key,'sequence_sha256':sha,'sequence':seq,'length_aa':len(seq),'seed':seed,'role':role,'msa_mode':msa_mode,'protocol_id':f'boltz2_2.2.1_{msa_mode}','calibration':r.get('calibration','').lower()in {'true','1'},'input_mapping':r,'status':'prepared'})
 if sum(r['role']in {'primary','sensitivity'}for r in rows)>150:raise ValueError('Primary cap exceeded')
 if sum(r['role']in {'control','reference_control'}for r in rows)>60:raise ValueError('Control cap exceeded')
 if sum(r.get('deep_dive','').lower()in {'true','1'}for r in rows)>20:raise ValueError('Deep-dive cap exceeded')
 if any(r['role']in {'control','reference_control'} and r.get('deep_dive','').lower()in {'true','1'}for r in rows):raise ValueError('Repeated control seeds require revised authorization')
 if len({r['sequence_sha256']for r in rows})!=len(rows):raise ValueError('Exact peptide sequences must be deduplicated')
 out=args.output;out.mkdir(parents=True,exist_ok=True)
 inputs=out/'inputs';inputs.mkdir(exist_ok=True)
 if (inputs/'manifest.json').exists():
  prior=json.loads((inputs/'manifest.json').read_text())
  if prior['selection_sha256']!=digest(args.selection)or prior['input_fasta_sha256']!=digest(args.fasta)or prior.get('msa_mode','precomputed')!=msa_mode:raise ValueError('Frozen staging inputs changed; use a new output directory')
 for j in jobs:
  j['fasta']=f"{j['job_id']}.fasta";j['yaml']=f"{j['job_id']}.yaml";j['msa']=f"msas/{j['sequence_sha256']}.a3m" if msa_mode=='precomputed' else 'empty'
  (inputs/j['fasta']).write_text(f">{j['job_id']}\n{j['sequence']}\n")
  (inputs/j['yaml']).write_text(f"version: 1\nsequences:\n  - protein:\n      id: A\n      sequence: {j['sequence']}\n      msa: {j['msa']}\n")
 m={'status':'staged_not_inferred','created_utc':datetime.now(timezone.utc).isoformat(),'settings':SETTINGS,'msa_mode':msa_mode,'protocol_id':f'boltz2_2.2.1_{msa_mode}','seeds':SEEDS,'input_fasta':str(args.fasta.resolve()),'input_fasta_sha256':digest(args.fasta),'selection_tsv':str(args.selection.resolve()),'selection_sha256':digest(args.selection),'jobs':jobs}
 save(inputs/'manifest.json',m)
 print(json.dumps({'jobs':len(jobs),'unique_sequences':len(rows),'primary_peptides':sum(r['role']=='primary'for r in rows)}))

def import_cache(args):
 manifest=args.output/'inputs/manifest.json';m=json.loads(manifest.read_text());prior=args.prior
 if m.get('msa_mode','precomputed')!='precomputed':raise ValueError('MSA-backed cached models cannot enter the single-sequence panel')
 old=json.loads((prior/'structures/summary.json').read_text());settings=json.loads((prior/'fold-inputs/manifest.json').read_text())['settings']
 if any(settings.get(k)!=v for k,v in SETTINGS.items())or settings.get('seed')!=20260919:raise ValueError('Cached protocol differs')
 cached={j['sequence_sha256']:j for j in old['jobs']if j['status']=='verified'}
 ledger=[]
 for j in m['jobs']:
  c=cached.get(j['sequence_sha256'])
  if not c or j['seed']!=20260919:continue
  dst=args.output/'models'/j['job_id'];dst.mkdir(parents=True,exist_ok=True);paths={}
  for rel,expected in c['validation']['files'].items():
   src=prior/c['prediction_directory']/rel
   if digest(src)!=expected:raise ValueError('Cached artifact hash differs')
   name='model.cif' if src.suffix=='.cif'else 'confidence.json'if src.suffix=='.json'else src.name.split('_protein_')[0]+'.npz'
   shutil.copy2(src,dst/name);paths[name]=str((dst/name).resolve())
  validation=validate_model(j['sequence'],paths['model.cif'],paths['plddt.npz'],paths['pae.npz'])
  save(dst/'validation.json',validation);save(dst/'prior_provenance.json',c)
  record={**j,'status':'cached_verified','reused_prior_prediction':True,'new_inference':False,'prior_wall_seconds':c['wall_seconds'],'prior_finished_utc':c['finished_utc'],'artifacts':paths,'validation':validation}
  ledger.append(record)
 save(args.output/'cached_jobs.json',ledger);print(json.dumps({'cached_jobs':len(ledger)}))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 x=sub.add_parser('stage');x.add_argument('--selection',type=Path,required=True);x.add_argument('--fasta',type=Path,required=True);x.add_argument('--output',type=Path,required=True);x.add_argument('--msa-mode',choices=['precomputed','single_sequence'],default='precomputed')
 x=sub.add_parser('import-cache');x.add_argument('--output',type=Path,required=True);x.add_argument('--prior',type=Path,default=Path('/home/ubuntu/workspace/chrna/runs/focused-pilot-20260919'))
 a=p.parse_args();stage(a)if a.command=='stage'else import_cache(a)
