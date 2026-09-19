#!/usr/bin/env python3
"""Rebuild the dataset, frozen evaluation, figures, exploratory ranks, and offline demo.

No GPU instance provisioning or paid API calls occur here.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', help='Download missing published tables and reference annotation')
    parser.add_argument('--rebuild-hic', action='store_true', help='Extract features again from cached Hi-C matrices')
    parser.add_argument('--download-hic', action='store_true', help='Fetch the three public processed matrices (~1.5GB), then rebuild features')
    parser.add_argument('--rna-only', action='store_true', help='Explicitly omit Hi-C, even if cached features exist')
    args = parser.parse_args()
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT / 'src')

    def run(*command):
        print('Running:', ' '.join(map(str, command)), flush=True)
        subprocess.run([sys.executable, *map(str, command)], cwd=ROOT, env=env, check=True)

    run('-m', 'chrna.data', '--root', ROOT, *(['--download'] if args.download else []))
    if args.download_hic:
        run('scripts/compute/download_hic.py')
    if args.rebuild_hic or args.download_hic:
        run('scripts/compute/extract_hic_features.py')
    hic = ROOT / 'results/hic/features.tsv'
    if not args.rna_only and not hic.exists():
        raise SystemExit('Hi-C features missing. Use --download-hic or explicitly choose --rna-only; no silent downgrade.')
    run('-m', 'chrna.model', *(['--hic', hic.relative_to(ROOT)] if not args.rna_only else []))
    run('scripts/plot_evaluation.py')
    run('scripts/score_catalogue.py')
    run('scripts/demo/export.py')
    print('Done. Serve locally: .venv/bin/python scripts/demo/serve.py')


if __name__ == '__main__':
    main()
