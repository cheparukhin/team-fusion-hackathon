"""Bounded local jobs with exclusive ownership and durable attempt records.

This does not provision or shut down provider instances. Remote launches need
their own validated lifecycle controller and live price/inventory preflight.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import resource
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_record(path: Path, value: dict):
    temporary = path.with_suffix(".partial.json")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def stop_group(process, grace_seconds=3):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    # The leader can exit before a child. Kill any survivors in its group.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def run_job(spec: dict, attempt: Path, lock_path: Path) -> dict:
    command = spec["argv"]
    if not isinstance(command, list) or not command or any(not isinstance(s, str) for s in command):
        raise ValueError("argv must be a nonempty list of strings")
    timeout = spec["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 7200:
        raise ValueError("Local job timeout must be positive and at most two hours")
    watchdog = shutil.which("timeout")
    if watchdog is None:
        raise RuntimeError("GNU timeout is required for an independent job watchdog")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        attempt.mkdir(parents=True, exist_ok=False)
        cwd = Path(spec.get("cwd", ".")).resolve()
        record = {"schema_version": 1, "spec": spec, "cwd": str(cwd),
                  "spec_sha256": hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest(),
                  "started_utc": utc_now(), "status": "starting", "controller_pid": os.getpid(),
                  "scope": "existing local CPU; no provider launch",
                  "watchdog": "GNU timeout with TERM, then KILL after 3 seconds; Python timeout is a backup"}
        record_path = attempt / "job.json"
        write_record(record_path, record)
        start = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        process = None
        env = os.environ.copy()
        env.update(spec.get("env", {}))
        try:
            with (attempt / "stdout.log").open("xb") as stdout, (attempt / "stderr.log").open("xb") as stderr:
                process = subprocess.Popen([watchdog, "--signal=TERM", "--kill-after=3s", f"{timeout}s", *command], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                           stdout=stdout, stderr=stderr, start_new_session=True)
                record.update(status="running", child_pid=process.pid)
                write_record(record_path, record)
                try:
                    code = process.wait(timeout=timeout + 5)
                    record.update(status="succeeded" if code == 0 else "timed_out" if code == 124 else "failed", exit_code=code)
                except subprocess.TimeoutExpired:
                    stop_group(process)
                    record.update(status="timed_out", exit_code=process.returncode)
        except BaseException as error:
            if process is not None:
                stop_group(process)
            record.update(status="interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed",
                          error_type=type(error).__name__)
            raise
        finally:
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            record.update(finished_utc=utc_now(), wall_seconds=time.monotonic() - start,
                          child_user_cpu_seconds=usage.ru_utime - before.ru_utime,
                          child_system_cpu_seconds=usage.ru_stime - before.ru_stime,
                          child_max_rss_kib=usage.ru_maxrss,
                          resource_note="Linux child-process high-water RSS; not simultaneous process-tree memory or peak scratch disk.")
            write_record(record_path, record)
        return record


def main():
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--lock", required=True, type=Path)
    args = parser.parse_args()
    result = run_job(json.loads(args.spec.read_text()), args.attempt, args.lock)
    print(json.dumps(result, indent=2))
    if result["status"] != "succeeded":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
