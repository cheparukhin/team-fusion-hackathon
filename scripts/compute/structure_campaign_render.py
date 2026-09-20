#!/usr/bin/env python3
"""Render sequence-verified models with unambiguous, audited RNA-origin colors."""
import argparse,csv,gzip,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from structure_campaign_stage import save,validate_model,digest
BLUE='#0000FF';RED='#D22D27'

def main(a):
 import pymol
 from pymol import cmd
 root=Path(__file__).resolve().parents[2];jobs=json.loads((a.output/'jobs.json').read_text());regions=defaultdict(lambda:defaultdict(list))
 with (a.cohort/'regions.tsv').open()as f:
  for r in csv.DictReader(f,delimiter='\t'):regions[r['peptide_id']][r['orf_id']].append((int(r['start_residue_1based']),int(r['end_residue_1based']),r['source_class']))
 selected=[j for j in jobs if j['status']in {'verified','cached_verified'}and j['seed']==20260919 and j['role']in {'primary','sensitivity','reference_control'}][:a.limit]
 need={j['peptide_id']for j in selected};residues=defaultdict(lambda:defaultdict(dict))
 with gzip.open(a.cohort/'residue_map.tsv.gz','rt')as f:
  for r in csv.DictReader(f,delimiter='\t'):
   if r['peptide_id']in need:residues[r['peptide_id']][r['orf_id']][int(r['residue_1based'])]=(r['amino_acid'],r['source_class'])
 gallery=[];skipped=[]
 for j in selected:
  maps=regions[j['peptide_id']];color_maps={};valid_orfs=[]
  for orf,ranges in maps.items():
   seqmap=residues[j['peptide_id']][orf]
   if ''.join(seqmap[i][0]for i in sorted(seqmap))!=j['sequence']:raise ValueError('Residue map sequence mismatch')
   colors=tuple(BLUE if seqmap[i][1].startswith('parent_a_')else RED for i in range(1,len(j['sequence'])+1))
   color_maps[orf]=colors;valid_orfs.append(orf)
  if not valid_orfs or len(set(color_maps.values()))!=1:
   skipped.append({'peptide_id':j['peptide_id'],'reason':'Missing or disagreeing residue-source boundaries across ORF hypotheses'});continue
  representative=sorted(valid_orfs)[0];ranges=sorted(maps[representative]);colors=color_maps[representative]
  path=Path(j['artifacts']['model.cif']);dest=a.output/'gallery';dest.mkdir(exist_ok=True);plain=dest/(j['sequence_sha256']+'_cartoon.png');labeled=dest/(j['sequence_sha256']+'.png')
  validate_model(j['sequence'],path,Path(j['artifacts']['plddt.npz']),Path(j['artifacts']['pae.npz']))
  cmd.reinitialize();cmd.load(str(path),'protein');cmd.hide('everything');cmd.show('cartoon');cmd.set_color('a_blue',[0,0,1]);cmd.set_color('b_red',[210/255,45/255,39/255]);cmd.color('b_red');cmd.color('a_blue','resi '+'+'.join(str(i)for i,c in enumerate(colors,1)if c==BLUE))if BLUE in colors else None;cmd.set('cartoon_loop_radius',.25);cmd.set('cartoon_fancy_helices',1);cmd.set('cartoon_fancy_sheets',1);cmd.set('ray_opaque_background',0);cmd.set('ray_shadows',0);cmd.set('orthoscopic',1);cmd.set('antialias',2);cmd.bg_color('white');cmd.orient();cmd.turn('y',15);cmd.zoom(buffer=3);cmd.png(str(plain),width=2100,height=1600,dpi=300,ray=1)
  title=j['input_mapping'].get('pair_ids',j['peptide_id'][:20]);v=j['validation'];fig,ax=plt.subplots(figsize=(10,8),facecolor='white');ax.imshow(plt.imread(plain));ax.axis('off');fig.text(.06,.94,title,fontsize=18,fontweight='bold');fig.text(.06,.90,f"{j['length_aa']} aa · {j['role']} · conditional reference hypothesis",fontsize=11);fig.text(.06,.125,'Blue: wholly parent A RNA; red: parent B RNA or split junction codon',fontsize=10);fig.text(.06,.08,f"Boltz2 {j.get('msa_mode','precomputed')} · pLDDT {v['mean_plddt']:.1f} · not experimental",fontsize=11);fig.text(.06,.04,'Color denotes nucleotide origin, not canonical protein-domain identity.',fontsize=10,color='#52606D');fig.savefig(labeled,dpi=300);plt.close(fig)
  gallery.append({'peptide_id':j['peptide_id'],'sequence_sha256':j['sequence_sha256'],'png':str(labeled.relative_to(root))if labeled.is_absolute()else str(labeled),'title':title,'representative_orf_id':representative if len(valid_orfs)==1 else None,'equivalent_color_mapping_orf_ids':sorted(valid_orfs),'region_annotation_example_orf_id':representative,'source_regions':[{'start_residue_1based':s,'end_residue_1based':e,'source_class':c}for s,e,c in ranges],'residue_source_boundary_description':'Blue=RNA parent A only; red=RNA parent B or split junction codon. Source-class ranges from audited mapping; canonical/novel-frame distinctions retained separately.','selection_role':j['role'],'protocol_id':j.get('protocol_id','boltz2_2.2.1_precomputed'),'msa_mode':j.get('msa_mode','precomputed'),'reused_prior_prediction':j.get('reused_prior_prediction',False),'confidence_status':'low mean confidence'if v['mean_plddt']<70 else'mean confidence >=70; inspect regional confidence','mean_plddt':v['mean_plddt'],'residue_confidence_tsv':j['artifacts']['residue_confidence.tsv'],'model_sha256':digest(path)})
 save(a.output/'structure_gallery.json',{'assets':gallery,'skipped':skipped,'selection':'First verified first-pass candidate jobs in frozen job order, capped for rendering; not a confidence-based selection'})
 print(f'Rendered{len(gallery)}; skipped{len(skipped)} ambiguous/missing mappings')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--cohort',type=Path,required=True);p.add_argument('--limit',type=int,default=8);a=p.parse_args();a.output=a.output.resolve();a.cohort=a.cohort.resolve();main(a)
