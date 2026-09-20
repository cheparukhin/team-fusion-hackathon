"""Build a compact, checksummed preliminary package without regenerable caches."""
from pathlib import Path
import shutil,tarfile,hashlib,json,datetime,subprocess
R=Path(__file__).resolve().parents[1];D=R/'preliminary-human-cow';D.mkdir(exist_ok=True)
selected={}
def add(p):
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(R))]=p
def tree(name):
 for p in (R/name).rglob('*'):
  if '__pycache__' not in p.parts:add(p)
for name in ['PRELIMINARY_REPORT.md','README.md','STATUS.md','PLAN.md']:add(R/name)
for name in ['comparison','review','manifest','scripts','tests','raw']:tree(name)
for p in (R/'qc').glob('*'):
 if p.suffix in ['.json','.md','.tsv','.log'] and p.name not in ['cpu_quotes.json','gpu_quotes.json','post_create_inventory.json','package_verification.json']:add(p)
for p in (R/'qc/synthetic_controls').rglob('*'):
 if p.is_file() and p.stat().st_size<5_000_000:add(p)
for p in (R/'logs').glob('*.log'):add(p)
for p in (R/'reference').rglob('*'):
 if p.is_file() and (p.suffix=='.json' or p.name in ['gene_names.tsv','transcript_names.tsv','five_species_homologies.tsv']):add(p)
excluded={'genion_references','blast_reference','modified_exon_repair','references','__pycache__'}
for p in (R/'per_species').rglob('*'):
 if not p.is_file() or excluded.intersection(p.parts):continue
 if p.suffix in ['.paf','.sam','.bai','.part']:continue
 if p.suffix=='.bam' and not p.name.endswith('evidence.bam'):continue
 if p.stat().st_size>20_000_000:raise RuntimeError('Unexpected large noncache artifact: '+str(p))
 add(p)
versions={}
for name in ['TYPHON','LongGF_source','JAFFA_source']:
 repo=R/'software'/name
 versions[name]={'commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),'working_tree_changes':subprocess.check_output(['git','-C',str(repo),'status','--short'],text=True).strip()}
 archive=R/'software'/(name+'_pinned_source.tar.gz')
 subprocess.run(['git','-C',str(repo),'archive','--format=tar.gz','--output='+str(archive),'HEAD'],check=True)
 add(archive)
(R/'software/source_versions.json').write_text(json.dumps(versions,indent=2)+'\n')
for name in ['source_versions.json','environment.explicit.txt','environment.yml','jaffal_install.json']:add(R/'software'/name)
for rel,p in sorted(selected.items()):
 dest=D/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
(D/'PACKAGE_README.md').write_text('''# PRELIMINARY — human–cow liver chRNA comparison

Read PRELIMINARY_REPORT.md first. Zero shared ordered orthologous pairs were detected; no conserved chRNA is established. One library per species cannot establish absence.

## Main files

- comparison/candidate_pair_catalog.tsv: all 238 reported ordered pairs (38 human, 200 cow); primary_unique_reads > 0 selects the 25 human and 153 cow primary pairs.
- comparison/all_read_evidence.tsv: caller-specific evidence with exact native boundaries, original read IDs and QC flags. Lower-confidence rows are retained explicitly.
- comparison/reviewed_pair_matches.tsv and conserved_chRNAs.tsv: intentionally header-only; no shared pair or conserved event established.
- review/reviewed_top_cases.tsv: ten reviewed single-species cases, including counterpart parent coverage.
- review/junction_review.tsv: observed versus reconstructed boundary checks.
- per_species/: original supporting FASTQ, candidate BAMs, normalized evidence, caller outputs/logs, reconstructed FASTA and independent checks.
- qc/completed_vs_pending.tsv, analysis_freeze.json and final_evidence_validation.json: scope, cutoff and integrity results.
- qc/remote_export_verification.json: SHA256 agreement with the original runtime for critical evidence.
- manifest/, reference/, raw/: source provenance, orthology, native name maps, input checksums and original read-ID maps.
- scripts/, tests/, software/: workflow, controls, dependency lock and pinned source archives.

## Verify or reproduce

From this extracted directory run `sha256sum -c SHA256SUMS`.
The candidate comparison is reproducible without downloading genomes: `python3 scripts/review_comparison.py` (writes its comparison outputs, so use a copy if preserving the frozen package). Focused logic checks: `python3 tests/test_pair_comparison.py`.
Full alignment/reconstruction requires restoring native genomes, GTFs, raw library FASTQs and the recorded software environment. Paths in original configs/logs refer to the historical runtime `/home/ubuntu/cross-species`; rebase those for a new machine. Genome indices, full-library alignments, transcriptome self-alignments and software binaries are regenerable and omitted from this compact package. Source URLs/checksums, caller outputs, candidate alignments, selected exon BEDs and reference-assisted sequences are retained. Source archives reproduce the pinned upstream code; TYPHON setup scripts and compatibility records document applied integration patches.

The wider sample manifest, orthology input and original PLAN.md are historical setup artifacts. The frozen biological analysis includes only SRR31438987 and SRR31429688. No additional species were analyzed for this deliverable. Synthetic controls are labelled and never enter the biological candidate tables.
''')
files=sorted(p for p in D.rglob('*') if p.is_file() and p.name not in ['SHA256SUMS','package_manifest.json'])
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'label':'PRELIMINARY','scope':'one human and one cow bulk liver library','file_count_before_manifests':len(files),'uncompressed_bytes':sum(p.stat().st_size for p in files),'regenerable_caches_omitted':True}
(D/'package_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');files.append(D/'package_manifest.json')
with (D/'SHA256SUMS').open('w') as f:
 for p in sorted(files):f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(D))+'\n')
archive=R/'preliminary-human-cow.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=6) as t:t.add(D,arcname=D.name)
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
(R/'preliminary-human-cow.tar.gz.sha256').write_text(digest+'  '+archive.name+'\n')
print(json.dumps({**manifest,'archive_bytes':archive.stat().st_size,'archive_sha256':digest},indent=2))
