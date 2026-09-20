"""Local independent MoreRONN disorder for the exact audited Gsdmd fusion."""
from pathlib import Path
import csv, hashlib, json, math, os, subprocess, time
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'results/structure_campaign/cross_model_gsdmd/method_audit'
EXPECTED = 'f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa'
REVISION = 'f65f31f130010346e0e3b93bd1bb6c2ce1b81c65'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    source = BASE / 'moreronn_source'
    manifest = json.loads((source / 'source_manifest.json').read_text())
    assert manifest['revision'] == REVISION
    for path, value in manifest['source_sha256'].items():
        assert sha(source / path) == value, path
    cohort = ROOT / 'results/structure_campaign/cohort/peptides.tsv'
    with cohort.open() as f:
        selected = [r for r in csv.DictReader(f, delimiter='\t') if r['sequence_sha256'] == EXPECTED]
    assert len(selected) == 1
    seq = selected[0]['sequence']
    assert len(seq) == 118 and hashlib.sha256(seq.encode()).hexdigest() == EXPECTED
    compile_command = ['g++', '-O3', '-fopenmp', '-I'+str(source/'src/include'),
        '-DDATA_PATH="'+str(source/'data')+'"', str(source/'src/MoreRONN.cpp'),
        str(source/'src/mclBBF.cpp'), '-lrt', '-lm', '-lgomp', '-o', str(BASE/'moreRONN')]
    result = subprocess.run(compile_command, capture_output=True, text=True, timeout=90)
    (BASE/'compile.log').write_text(result.stdout+result.stderr)
    (BASE/'compile_command.json').write_text(json.dumps(compile_command, indent=2)+'\n')
    result.check_returncode()
    (BASE/'query.fasta').write_text('>Gsdmd_Tmem106a_118aa\n'+seq+'\n')
    command = [str(BASE/'moreRONN'), '-f', str(BASE/'query.fasta'), '-p0']
    env = os.environ.copy(); env['OMP_NUM_THREADS'] = '2'
    start = time.monotonic()
    result = subprocess.run(command, cwd=BASE, capture_output=True, text=True, env=env, timeout=120)
    elapsed = time.monotonic()-start
    (BASE/'moreronn_raw.txt').write_text(result.stdout); (BASE/'moreronn_stderr.txt').write_text(result.stderr)
    result.check_returncode()
    rows = []
    for line in result.stdout.splitlines():
        parts = line.split('\t')
        if len(parts) == 2 and len(parts[0]) == 1:
            value = float(parts[1]); assert math.isfinite(value) and 0 <= value <= 1
            rows.append(dict(residue=len(rows)+1, aa=parts[0], score=value, disordered=value > .5,
                sequence_sha256=EXPECTED, origin_region='retained_Gsdmd_1_73' if len(rows)<73 else 'junction_novel_tail_74_118'))
    assert len(rows) == 118 and ''.join(r['aa'] for r in rows) == seq
    with (BASE/'moreronn_residues.tsv').open('w') as f:
        writer = csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');writer.writeheader();writer.writerows(rows)
    regions=[]
    for name, lo, hi in [('whole_peptide',1,118),('retained_Gsdmd',1,73),('junction_novel_tail',74,118)]:
        subset=rows[lo-1:hi];n=sum(r['disordered'] for r in subset)
        regions.append(dict(region=name,start_1based=lo,end_1based=hi,n_residues=len(subset),
            n_disordered=n,fraction_disordered=n/len(subset),mean_score=sum(r['score'] for r in subset)/len(subset)))
    summary=dict(method='MoreRONN',version='4.9',source_repository='https://github.com/varun-ramraj/MoreRONN',
        revision=REVISION,license='GPL-3.0; retained full source, model data and LICENSE',
        sequence_sha256=EXPECTED,peptide_id=selected[0]['peptide_id'],pair_id='Gsdmd:Tmem106a',length_aa=118,
        threshold='score >0.5, matching the original symbolic prediction code',disorder_weight=.5,
        runtime_seconds=elapsed,threads=2,execution='actual local CPU prediction; no sequence upload',
        compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
        command=command,regions=regions,predominantly_disordered=regions[0]['fraction_disordered']>.5,
        interpretation='Independent RONN-family sequence-based disorder estimate, not an experimental disorder label. Method disagreement does not establish folding, stability or function. Metapredict V1/V3 are related versions and are not independent predictors.',
        source_manifest_sha256=sha(source/'source_manifest.json'),cohort_sha256=sha(cohort),
        driver_sha256=sha(__file__),binary_sha256=sha(BASE/'moreRONN'),
        artifacts_sha256={p:sha(BASE/p)for p in ['query.fasta','moreronn_raw.txt','moreronn_stderr.txt','moreronn_residues.tsv','compile_command.json','compile.log']})
    (BASE/'moreronn_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(regions,indent=2))
if __name__ == '__main__': main()
