import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

import pytest

spec = importlib.util.spec_from_file_location('controller_restore', Path(__file__).parents[1] / 'preservation/controller-20260920/restore.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture(tmp_path, member='results/example.txt', symlink=False):
    metadata = tmp_path / 'metadata'
    assets = tmp_path / 'assets'
    repo = tmp_path / 'repo'
    for p in (metadata, assets, repo):
        p.mkdir()
    data = b'preserved evidence\n'
    sha = hashlib.sha256(data).hexdigest()
    archive = assets / 'data.tar.gz.part-001'
    with tarfile.open(archive, 'w:gz') as t:
        info = tarfile.TarInfo(member)
        if symlink:
            info.type = tarfile.SYMTYPE
            info.linkname = '../../outside'
            t.addfile(info)
        else:
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    part = {'filename': archive.name, 'bytes': archive.stat().st_size, 'sha256': m.digest(archive)}
    (metadata / 'archives.json').write_text(json.dumps({'groups': [{'parts': [part]}]}))
    (metadata / 'data-files.json').write_text(json.dumps([{'path': 'results/example.txt', 'bytes': len(data), 'sha256': sha}]))
    (metadata / 'aliases.json').write_text(json.dumps([{'path': 'results/second.txt', 'source': 'results/example.txt', 'bytes': len(data), 'sha256': sha}]))
    return metadata, assets, repo


def test_restore_checksums_aliases_and_repeat_run(tmp_path):
    metadata, assets, repo = fixture(tmp_path)
    result = m.restore(metadata, assets, repo)
    assert result['evidence_files'] == 1
    assert (repo / 'results/second.txt').read_bytes() == (repo / 'results/example.txt').read_bytes()
    assert m.restore(metadata, assets, repo) == result
    # Aliases are independent copies, not hardlinks that could mutate another run.
    (repo / 'results/second.txt').write_text('changed')
    assert (repo / 'results/example.txt').read_text() == 'preserved evidence\n'


def test_collision_preflight_preserves_existing_work(tmp_path):
    metadata, assets, repo = fixture(tmp_path)
    (repo / 'results').mkdir()
    (repo / 'results/second.txt').write_text('existing work')
    with pytest.raises(ValueError, match='Refusing to overwrite'):
        m.restore(metadata, assets, repo)
    assert not (repo / 'results/example.txt').exists()
    assert (repo / 'results/second.txt').read_text() == 'existing work'


@pytest.mark.parametrize('member,symlink', [('../outside', False), ('results/example.txt', True)])
def test_unsafe_archive_members_are_rejected(tmp_path, member, symlink):
    metadata, assets, repo = fixture(tmp_path, member, symlink)
    with pytest.raises(ValueError, match='Unexpected archive member'):
        m.restore(metadata, assets, repo)
    assert not list(repo.rglob('*'))
    assert not (tmp_path / 'outside').exists()
