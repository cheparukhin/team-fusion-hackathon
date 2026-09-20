"""Copy an explicit scientific-artifact allowlist into the isolated Git checkout."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'runs/k562-all-junctions-20260920';REPO=ROOT/'publication/k562-human-20260920';DEST=REPO/'workflows/mouse-pilot/runs/k562-all-junctions-20260920'
def copy(src,dest):dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
def main():
 DEST.mkdir(parents=True,exist_ok=True)
 names=['README.md','completion.json','scope-freeze.json','selection-freeze.json','selection.json','selected_proteins.fasta','reconstruction-summary.json','protein_hypotheses.json','candidate-stage-audit.tsv','adapter-rules.json','adapter-read-assessment.json','adapter-origin-summary.json','mouse-workflow-comparison.json','dashboard-validation.json','build-check.log','benchmark-check.log']
 for name in names:
  if (BASE/name).is_file():copy(BASE/name,DEST/name)
 for lib in 'AB':
  for sub in ['assessment/rna_ranking.json','assessment/read_decisions.json','selection.json','orfs/observed_rna.fasta','orfs/reference_assisted_rna.fasta','orfs/protein_hypotheses.fasta','orfs/protein_hypotheses.json','orfs/orf_summary.json']:copy(BASE/lib/sub,DEST/lib/sub)
 for src in (BASE/'fold-inputs').iterdir():
  if src.suffix in ['.json','.yaml','.fasta','.a3m']:copy(src,DEST/'fold-inputs'/src.name)
 sources=['extend_all_rna.py','extend_rna.py','adapter_origin.py','build_all_evidence.py','build_all_dashboard.py','all-dashboard.html','prepare_all_folds.py','run_all_folds.py','delivery_guard.py','accept_all_folds.py','audit_all_junctions.py','publish_run.py']
 for name in sources:copy(ROOT/'scripts/k562'/name,REPO/'workflows/mouse-pilot/scripts/k562'/name)
 copy(ROOT/'scripts/annotate_pilot_exons.py',REPO/'workflows/mouse-pilot/scripts/annotate_pilot_exons.py')
 copy(ROOT/'tests/test_k562_adapter_screen.py',REPO/'workflows/mouse-pilot/tests/test_k562_adapter_screen.py')
 # Derived scientific ledgers, not raw read archives. Compression runs on our
 # already-owned GPU worker, not the shared controller. The original exact hashes
 # are retained so decompression can reconstruct the frozen input bytes.
 previous={r['original']:r for r in json.loads((DEST/'publication.json').read_text())['compressed_derived_ledgers']} if (DEST/'publication.json').exists() else {}
 compressed=[]
 for name in ['reconstructions.json','read_decisions.json','data.json','dashboard-data.json']:
  src=BASE/name;dst=DEST/(name+'.gz')
  if dst.exists():
   record=previous[name];assert hashlib.sha256(dst.read_bytes()).hexdigest()==record['gzip_sha256']
   if name!='dashboard-data.json':assert hashlib.sha256(src.read_bytes()).hexdigest()==record['original_sha256']
   compressed.append(record);continue
  if not dst.exists():
   with src.open('rb') as inp,dst.open('wb') as out:subprocess.run(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=15','chrna-k562-fold-20260920','gzip -n -c'],stdin=inp,stdout=out,env={**os.environ,'SHELL':'/bin/sh'},timeout=180,check=True)
  compressed.append({'original':name,'gzip':name+'.gz','original_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'gzip_sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
 (DEST/'publication.json').write_text(json.dumps({'scope':'All scientific sequences and decision ledgers; raw sequencing archives, genome reference, model weights, authentication and live infrastructure state excluded','compressed_derived_ledgers':compressed,'restore':'gunzip -k *.json.gz; validate original_sha256 before replay','worker_compression':'Owned K562 folding worker; gzip -n -c'},indent=2)+'\n')
 (DEST/'README.md').write_text((DEST/'README.md').read_text()+'\n## Git snapshot\n\nLarge derived JSON ledgers are stored as `.json.gz` (not raw read archives). Run `gunzip -k *.json.gz` and verify `publication.json` hashes to restore the exact frozen files. Reference genomes, raw sequencing archives, model weights and local infrastructure state are excluded. This branch records the separate human follow-up and does not alter submission claims.\n')
 print('Prepared',DEST)
if __name__=='__main__':main()
