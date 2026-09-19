import fcntl
import json
import sys

import pytest

from chrna.local_job import run_job


def spec(code, timeout=5):
    return {"argv": [sys.executable, "-c", code], "timeout_seconds": timeout}


def test_success_logs_and_immutable_attempt(tmp_path):
    attempt, lock = tmp_path / "attempt", tmp_path / "lock"
    result = run_job(spec("print('complete')"), attempt, lock)
    assert result["status"] == "succeeded"
    assert (attempt / "stdout.log").read_text() == "complete\n"
    with pytest.raises(FileExistsError):
        run_job(spec("print('changed')"), attempt, lock)
    assert json.loads((attempt / "job.json").read_text())["status"] == "succeeded"


def test_failure_retains_outputs(tmp_path):
    result = run_job(spec("import sys; print('partial'); sys.exit(7)"), tmp_path / "attempt", tmp_path / "lock")
    assert result["status"] == "failed"
    assert result["exit_code"] == 7
    assert (tmp_path / "attempt/stdout.log").read_text() == "partial\n"


def test_timeout_is_not_success(tmp_path):
    result = run_job(spec("import time; time.sleep(20)", 0.1), tmp_path / "attempt", tmp_path / "lock")
    assert result["status"] == "timed_out"
    assert result["wall_seconds"] < 5


def test_second_operator_cannot_start_same_task(tmp_path):
    lock_path = tmp_path / "lock"
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            run_job(spec("print('duplicate')"), tmp_path / "attempt", lock_path)
    assert not (tmp_path / "attempt").exists()


@pytest.mark.parametrize("timeout", [0, -1, float('nan'), float('inf'), True, 7201])
def test_unbounded_timeout_rejected(tmp_path, timeout):
    with pytest.raises(ValueError):
        run_job(spec("pass", timeout), tmp_path / "attempt", tmp_path / "lock")
