#!/usr/bin/env python3
"""Create a portable source/artifact bundle from tracked files, without raw caches."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--'], cwd=ROOT).returncode:
    raise SystemExit('Commit tracked changes before packaging so the recorded Git revision matches the bundle.')
paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
paths = sorted(p for p in paths if p and (ROOT / p).is_file())
manifest = {'created_utc': datetime.now(timezone.utc).isoformat(),
            'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
            'reproduce': '.venv/bin/python scripts/reproduce.py --download',
            'rebuild_hic': '.venv/bin/python scripts/reproduce.py --download --download-hic',
            'files': {p: {'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest(), 'bytes': (ROOT / p).stat().st_size} for p in paths},
            'excluded': 'Untracked files, git metadata, Python environment, raw sequencing/contact data, and genomic-reference caches.'}
out = ROOT / 'dist/chrna_submission.zip'
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in paths:
        archive.write(ROOT / path, 'chrna/' + path)
    archive.writestr('chrna/SUBMISSION_MANIFEST.json', json.dumps(manifest, indent=2))
with zipfile.ZipFile(out) as archive:
    corrupt = archive.testzip()
    if corrupt:
        raise RuntimeError(f'Archive integrity failure: {corrupt}')
print(json.dumps({'archive': str(out), 'files': len(paths), 'bytes': out.stat().st_size, 'crc_verified': True}, indent=2))
