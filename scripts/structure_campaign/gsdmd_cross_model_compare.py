"""Exact-sequence actual-model comparison; confidence is not disorder or function."""
from pathlib import Path
import argparse, csv, hashlib, importlib.util, importlib.metadata, itertools, json, sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = 'f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa'
REGIONS = [('whole_chain', 1, 118), ('retained_Gsdmd', 1, 73), ('junction_novel_tail', 74, 118)]
HELPER = ROOT / 'scripts/structure_campaign/analyze_model_robustness.py'
spec = importlib.util.spec_from_file_location('campaign_robustness', HELPER)
helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
fitted_rmsd = helper.fitted_rmsd

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_tsv(path, rows, fields):
    with path.open('w') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(rows)
def resolve(path, root):
    p = Path(path); return p if p.is_absolute() else root / p

def check_hash(record, path, logical_key):
    expected = record.get('artifact_sha256', {}).get(path.name, record.get('artifact_sha256', {}).get(logical_key))
    value = sha(path)
    if expected and expected != value:
        raise ValueError('artifact_hash_mismatch:'+logical_key)
    return value

def coordinate_identity(path, sequence):
    import gemmi
    structure = gemmi.read_structure(str(path))
    if len(structure) != 1:
        raise ValueError('expected_one_coordinate_model')
    chains = [c for c in structure[0] if any(gemmi.find_tabulated_residue(r.name).is_amino_acid() for r in c)]
    if len(chains) != 1:
        raise ValueError('expected_one_protein_chain')
    residues = [r for r in chains[0] if gemmi.find_tabulated_residue(r.name).is_amino_acid()]
    actual = ''.join(gemmi.find_tabulated_residue(r.name).one_letter_code for r in residues)
    if actual != sequence or len(residues) != 118:
        raise ValueError('coordinate_sequence_mismatch')
    ca = []
    if len({str(r.seqid) for r in residues}) != 118:
        raise ValueError('duplicate_residue_identifier')
    for i, r in enumerate(residues, 1):
        if r.label_seq is not None and r.label_seq != i:
            raise ValueError('noncontiguous_label_sequence')
        atoms = [a for a in r if a.name == 'CA']
        if len(atoms) != 1:
            raise ValueError('missing_or_ambiguous_CA')
        ca.append([atoms[0].pos.x, atoms[0].pos.y, atoms[0].pos.z])
    ca = np.asarray(ca)
    if not np.isfinite(ca).all(): raise ValueError('nonfinite_coordinates')
    return ca, chains[0].name

def confidence_identity(path, record, sequence):
    if record.get('confidence_scale') != '0-100':
        raise ValueError('confidence_scale_not_explicit_0_100')
    if record.get('confidence_metric', 'pLDDT').lower() != 'plddt':
        raise ValueError('confidence_metric_not_plddt')
    with path.open() as f: rows = list(csv.DictReader(f, delimiter='\t'))
    if len(rows) != len(sequence): raise ValueError('confidence_length_mismatch')
    scores = []
    for i, (r, aa) in enumerate(zip(rows, sequence), 1):
        if int(r['residue']) != i or r['aa'] != aa:
            raise ValueError('confidence_residue_identity_mismatch')
        if r.get('sequence_sha256') and r['sequence_sha256'] != EXPECTED:
            raise ValueError('confidence_sequence_hash_mismatch')
        v = float(r['plddt'])
        if not np.isfinite(v) or not 0 <= v <= 100: raise ValueError('invalid_confidence_value')
        scores.append(v)
    return np.asarray(scores)

def main(root=ROOT):
    root = Path(root); base = root / 'results/structure_campaign/cross_model_gsdmd'; out = base / 'analysis'; out.mkdir(parents=True, exist_ok=True)
    cohort = root / 'results/structure_campaign/cohort/peptides.tsv'
    with cohort.open() as f: selected = [r for r in csv.DictReader(f, delimiter='\t') if r['sequence_sha256'] == EXPECTED]
    if len(selected) != 1: raise ValueError('expected_unique_frozen_cohort_sequence')
    sequence = selected[0]['sequence']
    if len(sequence) != 118 or hashlib.sha256(sequence.encode()).hexdigest() != EXPECTED: raise ValueError('query_identity_invalid')
    inputs = [base / 'baseline_models.json', base / 'compute/model_index.json', base / 'nim/model_index.json']; source_hashes = {}; models = []; ids = set(); source_status = []
    for path in inputs:
        if not path.exists():
            source_status.append(dict(path=str(path.relative_to(root)), status='not_yet_available')); continue
        raw = path.read_bytes(); source_hashes[str(path.relative_to(root))] = hashlib.sha256(raw).hexdigest()
        records = json.loads(raw); records = records['models'] if isinstance(records, dict) else records
        source_status.append(dict(path=str(path.relative_to(root)), status='read', model_records=len(records)))
        for r in records:
            if r['model_id'] in ids: raise ValueError('duplicate_model_id_across_sources:'+r['model_id'])
            ids.add(r['model_id']); models.append((r, str(path.relative_to(root))))
    audits = []; metrics = []; residue_rows = []; valid = {}; artifacts = {}
    for r, source in models:
        row = {k:r.get(k,'') for k in ['model_id','engine_family','engine','protocol_id','status','seed','confidence_scale']}
        row.update(source_index=source, coordinate_status='unavailable', confidence_status='unavailable', reason='', confidence_reason='', model_path=r.get('model_path',''), coordinate_sha256='', confidence_sha256='', chain_id='')
        if r.get('status') not in {'verified','cached_verified'}:
            row['reason']='model_not_verified:'+str(r.get('status')); audits.append(row); continue
        try:
            if r.get('sequence_sha256') != EXPECTED or int(r.get('length_aa',0)) != 118: raise ValueError('model_metadata_sequence_mismatch')
            path = resolve(r['model_path'], root); row['coordinate_sha256'] = check_hash(r,path,'model_path')
            ca, chain = coordinate_identity(path, sequence); row.update(coordinate_status='verified', chain_id=chain); valid[r['model_id']] = (ca,r)
            artifacts[str(path.relative_to(root)) if path.is_relative_to(root) else str(path)] = row['coordinate_sha256']
        except (ValueError, KeyError, OSError, RuntimeError) as exc:
            row.update(coordinate_status='invalid_or_missing', reason=str(exc)); audits.append(row); continue
        try:
            if r.get('confidence_scale') != '0-100': raise ValueError('confidence_scale_not_explicit_0_100')
            path = resolve(r['residue_confidence_tsv'], root); row['confidence_sha256'] = check_hash(r,path,'residue_confidence_tsv')
            scores = confidence_identity(path,r,sequence); row['confidence_status']='verified_0_100_plddt'
            artifacts[str(path.relative_to(root)) if path.is_relative_to(root) else str(path)] = row['confidence_sha256']
            for name, lo, hi in REGIONS:
                v = scores[lo-1:hi]; metrics.append(dict(model_id=r['model_id'],engine_family=r.get('engine_family',''),protocol_id=r.get('protocol_id',''),seed=r.get('seed',''),region=name,start_1based=lo,end_1based=hi,n_residues=len(v),mean_plddt=float(v.mean()),fraction_plddt_ge70=float((v>=70).mean()),confidence_scale='0-100'))
            residue_rows.extend(dict(model_id=r['model_id'],residue=i,aa=aa,plddt=float(v),sequence_sha256=EXPECTED)for i,(aa,v)in enumerate(zip(sequence,scores),1))
        except (ValueError, KeyError, OSError) as exc:
            row.update(confidence_status='invalid_or_missing_or_unknown_scale',confidence_reason=str(exc))
        if r.get('pae_path'):
            path=resolve(r['pae_path'],root)
            if path.is_file(): artifacts[str(path.relative_to(root)) if path.is_relative_to(root) else str(path)]=sha(path)
        audits.append(row)
    comparisons=[]
    for (aid,(a,ra)),(bid,(b,rb)) in itertools.combinations(valid.items(),2):
        same_engine=ra.get('engine_family')==rb.get('engine_family');same_protocol=ra.get('protocol_id')==rb.get('protocol_id')
        category='same_protocol_seed_comparison' if same_protocol else 'same_engine_protocol_comparison' if same_engine else 'cross_engine_comparison'
        for name,lo,hi in REGIONS:
            comparisons.append(dict(model_a=aid,model_b=bid,engine_family_a=ra.get('engine_family',''),engine_family_b=rb.get('engine_family',''),protocol_a=ra.get('protocol_id',''),protocol_b=rb.get('protocol_id',''),seed_a=ra.get('seed',''),seed_b=rb.get('seed',''),comparison_type=category,region=name,start_1based=lo,end_1based=hi,n_matched_CA=hi-lo+1,independently_fitted_CA_rmsd_A=fitted_rmsd(a[lo-1:hi],b[lo-1:hi])))
    write_tsv(out/'model_audit.tsv',audits,list(audits[0]) if audits else ['model_id','coordinate_status','confidence_status'])
    write_tsv(out/'model_region_confidence.tsv',metrics,list(metrics[0]) if metrics else ['model_id','region','mean_plddt'])
    write_tsv(out/'residue_confidence.tsv',residue_rows,['model_id','residue','aa','plddt','sequence_sha256'])
    write_tsv(out/'pairwise_CA_rmsd.tsv',comparisons,list(comparisons[0]) if comparisons else ['model_a','model_b','region','independently_fitted_CA_rmsd_A'])
    (out/'METHODS.md').write_text('''# Exact-sequence cross-model comparison

Only actual coordinates matching all 118 ordered residues and one unambiguous C-alpha per residue enter pairwise comparisons. Source indices, models and confidence files retain hashes. Missing, unsuccessful, identity-failed and unknown-scale records stay in the audit. Confidence is summarized only from a residue-validated TSV explicitly declared pLDDT on a 0–100 scale. Unknown scales are never guessed or converted. No pLDDT value is treated as a disorder, function or stability score; scales sharing a range need not share calibration across engines.

Kabsch superposition uses all matched C-alpha atoms, with proper rotation and no reflection. Whole-chain (1–118), retained Gsdmd (1–73) and junction/novel tail (74–118, including split codon 74) are independently aligned. Regional RMSDs therefore remove each region's rigid-body orientation and do not measure inter-region placement. There is no confidence-based residue cherry-picking. RMSD is descriptive, length/context dependent and affected by low-confidence coordinates, not experimental accuracy, physical ensemble diversity, thermodynamic stability or function. Engine families, protocols and seeds remain labeled separately. Cached baseline models are not claimed as newly executed predictions.

Run `.venv-disorder/bin/python scripts/structure_campaign/gsdmd_cross_model_compare.py` after the compute index is exported. No inference is performed by this command. Use the dedicated `.venv-disorder` environment; the baseline execution used Gemmi 0.7.5 and NumPy 2.5.3. The base `.venv` lacks Gemmi. Actual interpreter and package versions are recorded in the manifest.
''')
    summary=dict(sequence_sha256=EXPECTED,length_aa=118,model_records=len(models),coordinate_validated_models=len(valid),confidence_validated_models=sum(r['confidence_status']=='verified_0_100_plddt'for r in audits),pairwise_model_pairs=len(comparisons)//3,region_comparison_rows=len(comparisons),engine_families=sorted({r.get('engine_family','unknown') for _,r in valid.values()}),source_status=source_status,input_sha256=source_hashes,cohort_sha256=sha(cohort),artifact_sha256=artifacts,driver_sha256=sha(__file__),rmsd_helper_sha256=sha(HELPER),input_changed_during_run=any(sha(root/p)!=h for p,h in source_hashes.items()))
    summary['runtime'] = dict(python_executable=sys.executable, python_version=sys.version.split()[0], gemmi=importlib.metadata.version('gemmi'), numpy=np.__version__)
    summary['output_sha256']={p.name:sha(p)for p in out.iterdir()if p.name in {'model_audit.tsv','model_region_confidence.tsv','residue_confidence.tsv','pairwise_CA_rmsd.tsv','METHODS.md'}}
    (out/'manifest.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps({k:summary[k]for k in ['model_records','coordinate_validated_models','confidence_validated_models','pairwise_model_pairs','engine_families','input_changed_during_run']},indent=2))
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);main(p.parse_args().root)
