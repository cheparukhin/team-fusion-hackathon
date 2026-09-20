"""Add executed human reconstruction and limited artifact assessment to the view."""
from pathlib import Path
import hashlib,importlib.util,json,sys,os
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'runs/k562-extension-20260920';sys.path.insert(0,str(ROOT/'src'))
from chrna.pilot_orfs import CODONS,IndexedFasta
spec=importlib.util.spec_from_file_location('exon_replay',ROOT/'scripts/annotate_pilot_exons.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def load(p):return json.loads(p.read_text())
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
 data=load(ROOT/'reports/k562-dashboard/data.json');recs={(r['junction_id'],r['read_id']):r for r in load(BASE/'reconstructions.json')};decs={(r['junction_id'],r['read_id']):r for r in load(BASE/'read_decisions.json')};ads={(r['junction_id'],r['read_id']):r for r in load(BASE/'adapter-read-assessment.json')}
 summaries={r['junction_id']:r for r in load(BASE/'reconstruction-summary.json')};origins={r['junction_id']:r for r in load(BASE/'adapter-origin-summary.json')};genome=IndexedFasta(BASE/'reference/genome.fa')
 for c in data['candidates']:
  c['extension']=summaries[c['id']];c['origin']=origins[c['id']]
  for r in c['reads']:
   k=(c['id'],r['id']);r['adapter']=ads[k];r['reconstruction']=None
   if k not in recs:continue
   rec=recs[k];d=decs[k];left=m.projected_sequence(d['left_alignment'],genome,rec['corrections_and_variants'],'left');right=m.projected_sequence(d['right_alignment'],genome,rec['corrections_and_variants'],'right');gap=d['comparison']['query_gap']
   reconstructed=left+right[-gap:] if gap<0 else left+rec['observed_rna'][d['left_alignment']['qend']:d['right_alignment']['qstart']]+right if gap>0 else left+right
   assert reconstructed==rec['reference_assisted_rna'];blocks=[]
   for side,key in enumerate(['left_alignment','right_alignment']):
    offset=0 if side==0 else len(left)+gap
    for start,end in m.reference_blocks(d[key]):
     blocks.append({'arm':side,'rna_start':offset,'rna_end':offset+end-start,'start':start,'end':end,'strand':d[key]['strand'],'chrom':d[key]['target']});offset+=end-start
   orfs=[]
   for o in rec['reference_assisted_orfs']:
    protein=''.join(CODONS[reconstructed[i:i+3]] for i in range(o['start'],o['stop_start'],3));assert protein==o['protein']
    residues=[]
    for i,aa in enumerate(protein):
     st=o['start']+3*i;bases=[]
     for pos in range(st,st+3):
      refs=[]
      for b in blocks:
       if b['rna_start']<=pos<b['rna_end']:
        g=b['start']+pos-b['rna_start'] if b['strand']=='+' else b['end']-1-(pos-b['rna_start'])
        refs.append({'arm':b['arm'],'chrom':b['chrom'],'position':g})
      bases.append({'rna_position':pos,'reference_assignments':refs})
     residues.append({'residue':i+1,'aa':aa,'bases':bases})
    orfs.append({**o,'sequence_sha256':digest(protein),'residues':residues})
   r['reconstruction']={key:rec[key] for key in ['observed_rna','reference_assisted_rna','observed_junction_interval','reference_assisted_junction_interval','unresolved_sequence_reasons','nmd']}
   r['reconstruction'].update(observed_orf_count=len(rec['observed_orfs']),orfs=orfs,correction_events=len(rec['corrections_and_variants']),rna_sha256=digest(reconstructed),rna_replay_verified=True)
 data['followup']={'scope':'Post-corroboration exploratory follow-up of five shared junctions; not all 414 supported junctions','qualifying_reads_reconstructed':len(recs),'assessed_reads_screened':len(ads),'selected_for_folding':0,'new_gpu_instances':0,'new_worker_charge_usd':0,'limits':'Full-core RTA sequence screen only; raw-signal adapter assessment and same-culture DNA unavailable'}
 path=BASE/'dashboard-data.json';path.write_text(json.dumps(data,indent=2)+'\n')
 template=(ROOT/'scripts/k562/extension-dashboard.html').read_text();s=template.replace('__DATA__',json.dumps(data,separators=(',',':')).replace('</','<\\/'))
 assert len(s.encode())<1_000_000
 directory=Path(os.environ.get('CHRNA_VIS_DIR',str(ROOT/'reports/k562-extension')))
 directory.mkdir(parents=True,exist_ok=True)
 dest=directory/'k562-rna-orf-assessment.html';dest.write_text(s);print(dest,len(s.encode()))
if __name__=='__main__':main()
