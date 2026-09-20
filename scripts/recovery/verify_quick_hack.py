"""Read-only verification of an extracted quick_hack recovery (no inference/network)."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import gemmi
import numpy as np


def verify(snapshot, dispositions):
    """Verify the recovery manifest and all successful ledger model artifacts."""
    files = list(csv.DictReader(dispositions.open(), delimiter='\t'))
    for row in files:
        rel = Path(row['archive_path']).relative_to('quick_hack')
        path = snapshot / rel
        if path.stat().st_size != int(row['bytes']):
            raise ValueError(f'File size mismatch: {rel}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError(f'File hash mismatch: {rel}')
    jobs = json.loads((snapshot / 'results/structure_campaign/compute/jobs.json').read_text())
    passed = []
    for job in jobs:
        if job['status'] not in {'verified', 'cached_verified'}:
            continue
        paths = {}
        for name, rel in job['artifacts'].items():
            relative = Path(rel)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError(f'Unexpected artifact path: {rel}')
            path = snapshot / relative
            if hashlib.sha256(path.read_bytes()).hexdigest() != job['artifact_sha256'][name]:
                raise ValueError(f'Ledger artifact mismatch: {rel}')
            paths[name] = path
        sequence = job['sequence']
        if hashlib.sha256(sequence.encode()).hexdigest() != job['sequence_sha256']:
            raise ValueError('Sequence hash mismatch')
        structure = gemmi.read_structure(str(paths['model.cif']))
        if len(structure) != 1 or len(structure[0]) != 1:
            raise ValueError('Expected a single-chain, single-model structure')
        residues = list(structure[0][0])
        observed = ''.join(gemmi.find_tabulated_residue(r.name).one_letter_code.upper() for r in residues)
        if observed != sequence:
            raise ValueError(f"Coordinate sequence mismatch: {job['job_id']}")
        for residue in residues:
            ca = [atom for atom in residue if atom.name == 'CA']
            if len(ca) != 1 or not np.isfinite([ca[0].pos.x, ca[0].pos.y, ca[0].pos.z]).all():
                raise ValueError('Invalid alpha carbon')
        with np.load(paths['plddt.npz'], allow_pickle=False) as data:
            confidence = data['plddt'].reshape(-1)
        with np.load(paths['pae.npz'], allow_pickle=False) as data:
            pae = data['pae']
        n = len(sequence)
        if confidence.shape != (n,) or not np.isfinite(confidence).all() or not ((confidence >= 0) & (confidence <= 1)).all():
            raise ValueError('Invalid pLDDT array')
        if pae.shape != (n, n) or not np.isfinite(pae).all() or (pae < 0).any():
            raise ValueError('Invalid PAE array')
        if abs(float(confidence.mean() * 100) - job['validation']['mean_plddt']) > 1e-5:
            raise ValueError('Saved pLDDT summary mismatch')
        passed.append(job)
    return {'status': 'passed', 'manifest_files': len(files), 'validated_model_jobs': len(passed),
            'protocol_counts': dict(Counter(job['protocol_id'] for job in passed)),
            'limitations': 'Artifact integrity and prediction consistency; no translation or function validation.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True, help='Extracted quick_hack directory')
    parser.add_argument('--manifest', type=Path, default=Path(__file__).resolve().parents[2] / 'results/recovery_20260920/file_dispositions.tsv')
    args = parser.parse_args()
    print(json.dumps(verify(args.snapshot.resolve(), args.manifest), indent=2))
