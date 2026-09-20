#!/usr/bin/env python3
"""Restore checksum-verified release data into existing canonical workflow paths."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_path(root, name):
    rel = Path(name)
    if not name or rel.is_absolute() or '..' in rel.parts:
        raise ValueError(f'Unsafe artifact path: {name}')
    path = root / rel
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Artifact path leaves destination: {name}')
    return path


class PartsReader(io.RawIOBase):
    def __init__(self, paths):
        self.paths = iter(paths)
        self.current = None

    def readable(self):
        return True

    def readinto(self, buffer):
        while True:
            if self.current is None:
                try:
                    self.current = next(self.paths).open('rb')
                except StopIteration:
                    return 0
            count = self.current.readinto(buffer)
            if count:
                return count
            self.current.close()
            self.current = None

    def close(self):
        if self.current:
            self.current.close()
        super().close()


def restore(metadata, assets, repository):
    metadata, assets, repository = map(lambda p: Path(p).resolve(), (metadata, assets, repository))
    repository.mkdir(parents=True, exist_ok=True)
    archives = json.loads((metadata / 'archives.json').read_text())
    records = json.loads((metadata / 'data-files.json').read_text())
    aliases = json.loads((metadata / 'aliases.json').read_text())
    expected = {r['path']: r for r in records}
    if len(expected) != len(records) or len({r['path'] for r in records + aliases}) != len(records) + len(aliases):
        raise ValueError('Duplicate artifact destinations in manifests')
    for row in records + aliases:
        safe_path(repository, row['path'])
    for group in archives['groups']:
        for part in group['parts']:
            p = safe_path(assets, part['filename'])
            if not p.is_file() or p.stat().st_size != part['bytes'] or digest(p) != part['sha256']:
                raise ValueError(f"Archive part checksum mismatch: {part['filename']}")
    with tempfile.TemporaryDirectory(prefix='.controller-restore-', dir=repository.parent) as temporary:
        staging = Path(temporary)
        seen = set()
        for group in archives['groups']:
            paths = [assets / part['filename'] for part in group['parts']]
            with io.BufferedReader(PartsReader(paths)) as stream:
                with tarfile.open(fileobj=stream, mode='r|gz') as archive:
                    for member in archive:
                        if not member.isfile() or member.name not in expected or member.name in seen:
                            raise ValueError(f'Unexpected archive member: {member.name}')
                        row = expected[member.name]
                        if member.size != row['bytes']:
                            raise ValueError(f'Wrong member size: {member.name}')
                        p = safe_path(staging, member.name)
                        p.parent.mkdir(parents=True, exist_ok=True)
                        with archive.extractfile(member) as source, p.open('wb') as target:
                            shutil.copyfileobj(source, target, 8 * 1024 * 1024)
                        p.chmod(0o755 if member.mode & 0o111 else 0o644)
                        if digest(p) != row['sha256']:
                            raise ValueError(f'Wrong member checksum: {member.name}')
                        seen.add(member.name)
        if seen != set(expected):
            raise ValueError('Archive set is incomplete')
        # Check every collision and alias before changing the repository.
        for row in records + aliases:
            target = safe_path(repository, row['path'])
            if target.exists() and (not target.is_file() or target.is_symlink() or digest(target) != row['sha256']):
                raise ValueError(f"Refusing to overwrite a different existing file: {row['path']}")
        for row in aliases:
            source = safe_path(staging, row['source'])
            if not source.is_file():
                source = safe_path(repository, row['source'])
            if not source.is_file() or source.stat().st_size != row['bytes'] or digest(source) != row['sha256']:
                raise ValueError(f"Missing or changed alias source: {row['source']}")
        for row in records:
            target = safe_path(repository, row['path'])
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(staging / row['path']), str(target))
        for row in aliases:
            target = safe_path(repository, row['path'])
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                # Copies keep later edits to one run from changing another run.
                shutil.copy2(repository / row['source'], target)
    return {'status': 'passed', 'evidence_files': len(records), 'deduplicated_paths_restored': len(aliases)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True, help='Downloaded release parts')
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    print(json.dumps(restore(Path(__file__).parent, args.assets, args.repo), indent=2))


if __name__ == '__main__':
    main()
