import hashlib
import io
import json
from pathlib import Path

import pytest

from chrna.references import fetch_reference


def spec(data):
    return {"url": "https://example.org/ref.gz", "md5": hashlib.md5(data).hexdigest(), "max_bytes": 100}


def test_transfer_hash_and_resume_without_network(tmp_path, monkeypatch):
    data = b"reference fixture"
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: io.BytesIO(data))
    target = tmp_path / "ref.gz"
    result = fetch_reference(spec(data), target)
    assert result["sha256"] == hashlib.sha256(data).hexdigest()
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: pytest.fail("refetched valid cache"))
    assert fetch_reference(spec(data), target) == result
    target.write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        fetch_reference(spec(data), target)


def test_bad_transfer_is_not_promoted(tmp_path, monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: io.BytesIO(b"wrong"))
    target = tmp_path / "ref.gz"
    with pytest.raises(ValueError, match="checksum"):
        fetch_reference(spec(b"right"), target)
    assert not target.exists()
    assert not Path(str(target) + ".provenance.json").exists()


def test_oversize_response_fails_closed(tmp_path, monkeypatch):
    data = b"x" * 101
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: io.BytesIO(data))
    with pytest.raises(ValueError, match="limit"):
        fetch_reference(spec(data), tmp_path / "ref.gz")


def test_source_change_rejected_even_with_same_bytes(tmp_path, monkeypatch):
    data = b"fixture"
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: io.BytesIO(data))
    target = tmp_path / "ref.gz"
    fetch_reference(spec(data), target)
    changed = {**spec(data), "url": "https://example.org/different.gz"}
    with pytest.raises(ValueError, match="receipt"):
        fetch_reference(changed, target)
