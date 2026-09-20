"""Accept only sequence-identical, hash-verified human Boltz predictions."""
from pathlib import Path
import hashlib,importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'runs/k562-all-junctions-20260920';spec=importlib.util.spec_from_file_location('bw',ROOT/'scripts/boltz_worker.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def load(p):return json.loads(p.read_text())
def main(attempt):
 import gemmi
 inputs=BASE/'fold-inputs';manifest=load(inputs/'manifest.json');freeze=BASE/'selection-freeze.json';assert hashlib.sha256(freeze.read_bytes()).hexdigest()==manifest['selection_freeze_sha256']
 for name,sha in load(freeze)['inputs'].items():assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==sha
 worker=attempt/'worker-outputs/predictions';history=load(worker/'jobs.json');jobs={j['job_id']:j for j in manifest['jobs']};assert {h['job_id'] for h in history}==set(jobs)
 dest=BASE/'structures';dest.mkdir(exist_ok=True);records={};summary=[]
 for h in history:
  job=jobs[h['job_id']];target=worker/job['job_id']
  if h['status']!='verified':summary.append(h);continue
  prior=load(target/'validation.json')
  for name,sha in prior['files'].items():assert hashlib.sha256((target/name).read_bytes()).hexdigest()==sha
  checked=m.validate(job,target)
  cif=target/('boltz_results_'+job['job_id'])/'predictions'/job['job_id']/(job['job_id']+'_model_0.cif');structure=gemmi.read_structure(str(cif));chain=structure[0][0]
  assert chain.name=='A' and [r.seqid.num for r in chain]==list(range(1,job['amino_acids']+1))
  pdb=structure.make_pdb_string();(dest/(job['job_id']+'.pdb')).write_text(pdb)
  records[job['job_id']]={'pdb':pdb,'sequence_sha256':job['sequence_sha256'],'sequence':job['sequence'],'plddt':checked['plddt_0_to_100'],'mean_plddt':checked['mean_plddt_0_to_100'],'ca_trace':[[round(r['CA'][0].pos.x,3),round(r['CA'][0].pos.y,3),round(r['CA'][0].pos.z,3)] for r in chain],'chain':'A','numbering':'1-based consecutive; complete sequence; no missing residues'}
  summary.append({**h,'validation':checked,'local_pdb':str((dest/(job['job_id']+'.pdb')).relative_to(BASE))})
 (dest/'dashboard-structures.json').write_text(json.dumps(records,indent=2)+'\n');(dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('Verified structures',len(records))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
