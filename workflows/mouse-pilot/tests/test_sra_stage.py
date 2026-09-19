import json
import sys

import pytest

from chrna.sra_stage import execute, receipt


def test_completed_attempt_is_reused_but_different_command_rejected(tmp_path):
    spec = {"argv": [sys.executable, "-c", "print('one run')"], "timeout_seconds": 5}
    first = execute(tmp_path, "fixture", spec)
    assert execute(tmp_path, "fixture", spec) == first
    with pytest.raises(ValueError, match="different command"):
        execute(tmp_path, "fixture", {**spec, "argv": [sys.executable, "-c", "print('changed')"]})


def test_running_or_failed_attempt_never_restarted_from_state_file(tmp_path):
    folder = tmp_path / "fixture-attempt-1"
    folder.mkdir()
    for state in ("running", "failed", "interrupted", "timed_out"):
        (folder / "job.json").write_text(json.dumps({"status": state}))
        with pytest.raises(RuntimeError, match="not successfully complete"):
            execute(tmp_path, "fixture", {"argv": ["not-executed"], "timeout_seconds": 1})


def test_receipts_preserve_extra_provenance_and_reject_changes(tmp_path):
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps({"sha256": "old", "additional_provenance": "keep"}))
    receipt(path, {"sha256": "old"})
    assert json.loads(path.read_text())["additional_provenance"] == "keep"
    with pytest.raises(ValueError, match="Receipt changed"):
        receipt(path, {"sha256": "new"})
