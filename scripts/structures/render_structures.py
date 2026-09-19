#!/usr/bin/env python3
"""Validate molecular coordinates and render real structures with explicit evidence labels."""
import hashlib, json
from pathlib import Path
import gemmi
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy.interpolate import CubicSpline
import pymol
from pymol import cmd
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'results/structures'
BLUE='#0000FF'; RED='#D22D27'; GRAY='#C6CBD2'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def residues(p):
 return [r for r in gemmi.read_structure(str(p))[0]['A'] if 'CA' in r]
def coords(rr): return np.array([[r['CA'][0].pos.x,r['CA'][0].pos.y,r['CA'][0].pos.z]for r in rr])
def render_pymol(path,dest,parent=False):
 cmd.reinitialize(); cmd.load(str(path),'molecule'); cmd.remove('not (chain A and polymer.protein)'); cmd.hide('everything'); cmd.show('cartoon')
 cmd.set_color('source_blue',[0,0,1]); cmd.set_color('source_red',[210/255,45/255,39/255]); cmd.set_color('context_gray',[.77,.80,.84]);cmd.color('context_gray' if parent else 'source_red','all');cmd.color('source_blue','resi 1-73')
 cmd.set('cartoon_fancy_helices',1);cmd.set('cartoon_fancy_sheets',1);cmd.set('cartoon_loop_radius',.26);cmd.set('cartoon_sampling',14)
 cmd.set('antialias',2);cmd.set('orthoscopic',1);cmd.set('ray_shadows',0);cmd.set('specular',.25);cmd.set('ambient',.45);cmd.set('ray_opaque_background',0);cmd.bg_color('white')
 cmd.orient('all');cmd.turn('y',20);cmd.turn('x',-10);cmd.zoom('all',buffer=3)
 cmd.png(str(dest),width=2400,height=1800,dpi=300,ray=1)
 return list(cmd.get_view())
def vector_trace(rr,dest,parent=False):
 xyz=coords(rr);xyz-=xyz.mean(0);_,_,v=np.linalg.svd(xyz,full_matrices=False); xyz=xyz@v.T
 fig,ax=plt.subplots(figsize=(8,6)); ax.set_aspect('equal');ax.axis('off')
 # Keep experimental gaps separate: no invented peptide links across missing residues.
 groups=[]; current=[]
 for i,r in enumerate(rr):
  if current and (r.seqid.num!=rr[current[-1]].seqid.num+1 or np.linalg.norm(xyz[i]-xyz[current[-1]])>5): groups.append(current);current=[]
  current.append(i)
 if current:groups.append(current)
 for g in groups:
  if len(g)<2:continue
  t=np.arange(len(g));fine=np.linspace(0,len(g)-1,12*(len(g)-1)+1); smooth=CubicSpline(t,xyz[g],bc_type='natural')(fine)
  seg=np.stack([smooth[:-1,:2],smooth[1:,:2]],axis=1)
  cols=[BLUE if rr[g[min(int(f),len(g)-1)]].seqid.num<=73 else GRAY if parent else RED for f in fine[:-1]]
  ax.add_collection(LineCollection(seg,colors=cols,linewidths=2.5,capstyle='round'))
 ax.autoscale();ax.margins(.13);fig.savefig(dest,transparent=True,bbox_inches='tight');plt.close(fig)
def render_confidence():
 p=OUT/'gsdmd_tmem106a';conf=np.load(p/'plddt.npz')['plddt'].reshape(-1)*100
 plt.rcParams['svg.fonttype']='none'
 fig,ax=plt.subplots(figsize=(10,3.5));x=np.arange(1,119)
 ax.plot(x[:73],conf[:73],color=BLUE,lw=2,label='GSDMD-identical residues 1–73')
 ax.plot(x[73:],conf[73:],color=RED,lw=2,label='Novel out-of-frame residues 74–118')
 ax.plot(x[72:74],conf[72:74],color='#647080',lw=1)
 ax.axhline(50,color='#647080',ls='--',lw=1,label='pLDDT 50 threshold')
 ax.set(xlim=(1,118),ylim=(0,100),xlabel='Residue',ylabel='Predicted local confidence (pLDDT)')
 ax.spines[['top','right']].set_visible(False);ax.legend(frameon=False,loc='upper right',fontsize=9)
 ax.set_title('Gsdmd:Tmem106a · low-confidence Boltz2 prediction',loc='left',fontweight='bold')
 fig.text(.12,.01,'53.4% of residues have pLDDT < 50. This is model uncertainty, not measured disorder.',fontsize=9,color='#52606D')
 fig.tight_layout(rect=(0,.04,1,1));fig.savefig(p/'confidence_plot.png',dpi=300);fig.savefig(p/'confidence_plot.svg');plt.close(fig)
def main():
 render_confidence()
 p=OUT/'gsdmd_tmem106a'; q=OUT/'gsdmd_parent';seq=''.join((p/'sequence.fasta').read_text().splitlines()[1:])
 rr=residues(p/'model.cif');actual=''.join(gemmi.find_tabulated_residue(r.name).one_letter_code for r in rr)
 assert actual==seq and len(seq)==118
 assert hashlib.sha256(seq.encode()).hexdigest()=='f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa'
 pr=residues(q/'6N9N.cif');shared=[r for r in pr if 1<=r.seqid.num<=73]
 assert all(gemmi.find_tabulated_residue(r.name).one_letter_code==seq[r.seqid.num-1] for r in shared)
 conf=np.load(p/'plddt.npz')['plddt'];conf=conf.reshape(-1)*100;assert len(conf)==118
 metrics={'mean_plddt':float(conf.mean()),'mean_plddt_shared_1_73':float(conf[:73].mean()),'mean_plddt_novel_74_118':float(conf[73:].mean()),'fraction_below_50':float((conf<50).mean()),'ptm':json.loads((p/'confidence.json').read_text())['ptm'],'parent_shared_residues_observed':len(shared),'parent_shared_residues_missing':sorted(set(range(1,74))-{r.seqid.num for r in shared})}
 (OUT/'validation.json').write_text(json.dumps({'sequence_matches_coordinate_residues':True,'experimental_shared_residues_match':True,**metrics},indent=2)+'\n')
 views={}
 for name,directory,parent in [('chimera',p,False),('parent',q,True)]:
  path=directory/('6N9N.cif' if parent else 'model.cif');views[name]=render_pymol(path,directory/'cartoon.png',parent);vector_trace(pr if parent else rr,directory/'backbone.svg',parent)
 (OUT/'render_views.json').write_text(json.dumps(views,indent=2)+'\n')
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'svg.fonttype':'none'})
 fig=plt.figure(figsize=(14,8),facecolor='white');gs=fig.add_gridspec(2,2,height_ratios=[4,1],hspace=.07,wspace=.12)
 for i,(d,title,sub) in enumerate([(q,'Experimental parent: mouse GSDMD','PDB 6N9N · chain A · X-ray, 3.30 Å'),(p,'Gsdmd:Tmem106a · 118 aa','Boltz2 prediction of a reference reconstruction')]):
  ax=fig.add_subplot(gs[0,i]);ax.imshow(plt.imread(d/'cartoon.png'));ax.axis('off');ax.set_title(title,fontsize=17,fontweight='bold',loc='left',pad=24);ax.text(0,1.01,sub,transform=ax.transAxes,color='#52606D',fontsize=11)
 ax=fig.add_subplot(gs[1,0]);ax.axis('off');ax.text(0,.85,'SHARED N-TERMINUS',color=BLUE,fontweight='bold');ax.text(0,.6,'Residues 1–73; 69 observed in parent chain A',fontsize=11);ax.text(0,.3,'Gray: remainder of experimental parent',color='#657181',fontsize=11);ax.text(0,.06,'Missing parent residues are not modeled.',fontsize=10,color='#657181')
 ax=fig.add_subplot(gs[1,1]);x=np.arange(1,119);ax.plot(x,conf,color='#303C4C',lw=1.3);ax.axvspan(1,73,color=BLUE,alpha=.08);ax.axvspan(73.5,118,color=RED,alpha=.1);ax.axhline(50,color='#76808C',lw=.8,ls='--');ax.set(xlim=(1,118),ylim=(0,100),ylabel='pLDDT',xlabel='Residue');ax.spines[['top','right']].set_visible(False);ax.set_title('Low confidence · mean pLDDT 48.7 · pTM 0.336',fontsize=11,loc='left',color='#99362F')
 fig.text(.55,.325,'Red: novel out-of-frame tail, residues 74–118',color=RED,fontsize=11)
 fig.text(.065,.02,'Experimental parent and predicted chimera are separate structures. Prediction does not establish fold, function or druggability.',fontsize=10,color='#52606D')
 fig.subplots_adjust(top=.87,bottom=.105,left=.065,right=.97);fig.savefig(OUT/'structure_comparison.png',dpi=300);fig.savefig(OUT/'structure_comparison.pdf');plt.close(fig)
 # Compact candidate figure for gallery, preserving caveat directly on image.
 fig,ax=plt.subplots(figsize=(9,7),facecolor='white');ax.imshow(plt.imread(p/'cartoon.png'));ax.axis('off');fig.text(.06,.94,'Gsdmd:Tmem106a',fontsize=22,fontweight='bold');fig.text(.06,.90,'118 aa · reference-reconstructed sequence · Boltz2 prediction',fontsize=11);fig.text(.06,.13,'GSDMD residues 1–73',color=BLUE,fontsize=12);fig.text(.06,.09,'Novel out-of-frame residues 74–118',color=RED,fontsize=12);fig.text(.06,.04,'LOW CONFIDENCE  |  mean pLDDT 48.7; pTM 0.336',color='#99362F',fontsize=11);fig.savefig(p/'labeled.png',dpi=300);plt.close(fig)
 print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
