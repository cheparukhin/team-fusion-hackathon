"""Add executed human reconstruction and limited artifact assessment to the view."""
from pathlib import Path
import hashlib,importlib.util,json,sys,os
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'runs/k562-all-junctions-20260920';sys.path.insert(0,str(ROOT/'src'))
from chrna.pilot_orfs import CODONS,IndexedFasta
spec=importlib.util.spec_from_file_location('exon_replay',ROOT/'scripts/annotate_pilot_exons.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def load(p):return json.loads(p.read_text())
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
 data=load(BASE/'data.json');recs={(r['junction_id'],r['read_id']):r for r in load(BASE/'reconstructions.json')};decs={(r['junction_id'],r['read_id']):r for r in load(BASE/'read_decisions.json')};ads={(r['junction_id'],r['read_id']):r for r in load(BASE/'adapter-read-assessment.json')}
 summaries={}
 for row in load(BASE/'reconstruction-summary.json'):
  v=summaries.setdefault(row['junction_id'],{'qualifying_reads_reconstructed':0,'observed_complete_spanning_ORF_reads':0,'reference_assisted_complete_spanning_ORF_reads':0,'folding_reasons':[],'libraries':{}})
  for key in ['qualifying_reads_reconstructed','observed_complete_spanning_ORF_reads','reference_assisted_complete_spanning_ORF_reads']:v[key]+=row[key]
  v['libraries'][row['library']]=row;v['folding_reasons']+=row['folding_reasons']
 selected={(h['junction_id'],h['read_id']):h for h in load(BASE/'selection.json')['selected']}
 structures=load(BASE/'structures/dashboard-structures.json') if (BASE/'structures/dashboard-structures.json').exists() else {}
 origins={r['junction_id']:r for r in load(BASE/'adapter-origin-summary.json')};genome=IndexedFasta(BASE/'reference/genome.fa')
 for c in data['candidates']:
  c['extension']=summaries[c['id']];c['origin']=origins[c['id']]
  for r in c['reads']:
   k=(c['id'],r['id']);r['adapter']=ads.get(k);r['reconstruction']=None;r['fold_selected']=k in selected;r['structure']=structures.get(selected[k]['protein_id']) if k in selected else None
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
 data['followup']={'scope':'All 414 supported junctions; independent library ORF assessment; no short-read or replication gate','qualifying_reads_reconstructed':len(recs),'assessed_reads_screened':len(ads),'selected_for_folding':len(selected),'new_gpu_instances':1 if structures else 0,'new_worker_charge_usd':load(BASE/'resource-accounting.json').get('launch_to_confirmed_stop_quote_USD') if (BASE/'resource-accounting.json').exists() else None,'limits':'Full-core RTA sequence screen only; raw-signal adapter assessment and same-culture DNA unavailable'}
 path=BASE/'dashboard-data.json';path.write_text(json.dumps(data,indent=2)+'\n')
 template=(ROOT/'scripts/k562/all-dashboard.html').read_text()
 import gzip,base64
 for c in data['candidates']:
  for r in c['reads']:
   for a in r['arms']:a.pop('source_line',None)
   if r.get('structure'):r['structure'].pop('pdb',None)
   rec=r.get('reconstruction')
   if rec and not rec['orfs']:
    rec['sequence_display']='Full sequences retained in A/B/orfs FASTAs and dashboard-data.json; omitted from this compact inline view.'
    rec['observed_rna_length']=len(rec['observed_rna']);rec['reference_assisted_rna_length']=len(rec['reference_assisted_rna'])
    rec['observed_rna']='';rec['reference_assisted_rna']=''
 s=template.replace('__DATA__',base64.b64encode(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0)).decode())
 assert len(s.encode())<1_000_000
 directory=Path(os.environ.get('CHRNA_VIS_DIR',str(ROOT/'reports/k562-all-junctions')));directory.mkdir(parents=True,exist_ok=True);dest=directory/'k562-all-junctions.html';dest.write_text(s);print(dest,len(s.encode()))
if __name__=='__main__':main()
