#!/usr/bin/env python3
"""Create a portable source/artifact bundle from tracked files, without raw caches."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
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
# Source snapshots can legitimately carry Unix-epoch modification times. ZIP's
# DOS timestamp starts in 1980; clamp metadata without changing file contents.
# Publish only after CRC and manifest verification, preserving an older good ZIP.
with tempfile.TemporaryDirectory(prefix='chrna-package-', dir=out.parent) as temporary:
    pending = Path(temporary) / out.name
    with zipfile.ZipFile(pending, 'w', zipfile.ZIP_DEFLATED, compresslevel=6,
                         strict_timestamps=False) as archive:
        for path in paths:
            archive.write(ROOT / path, 'chrna/' + path)
        archive.writestr('chrna/SUBMISSION_MANIFEST.json', json.dumps(manifest, indent=2))
    with zipfile.ZipFile(pending) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise RuntimeError(f'Archive integrity failure: {corrupt}')
        for path, expected in manifest['files'].items():
            payload = archive.read('chrna/' + path)
            if len(payload) != expected['bytes'] or hashlib.sha256(payload).hexdigest() != expected['sha256']:
                raise RuntimeError(f'File changed during packaging: {path}; retry from a stable checkout.')
    pending.replace(out)
print(json.dumps({'archive': str(out), 'files': len(paths), 'bytes': out.stat().st_size, 'crc_verified': True}, indent=2))
