#!/usr/bin/env python3
"""Verify a restored controller snapshot using only the Python standard library."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, help='Repository root with restored evidence')
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_name('files.tsv'))
    args = parser.parse_args()
    root = args.root.resolve()
    failures, count, total = [], 0, 0
    with args.manifest.open() as handle:
        for row in csv.DictReader(handle, delimiter='\t'):
            relative = Path(row['path'])
            path = root / relative
            if relative.is_absolute() or '..' in relative.parts or not path.resolve().is_relative_to(root):
                failures.append({'path': row['path'], 'reason': 'unsafe path'})
                continue
            if not path.is_file() or path.is_symlink():
                failures.append({'path': row['path'], 'reason': 'missing file or unexpected symlink'})
            elif path.stat().st_size != int(row['bytes']) or digest(path) != row['sha256']:
                failures.append({'path': row['path'], 'reason': 'size or SHA-256 mismatch'})
            count += 1
            total += int(row['bytes'])
    print(json.dumps({'status': 'failed' if failures else 'passed', 'files': count,
                      'bytes': total, 'failures': failures}, indent=2))
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
