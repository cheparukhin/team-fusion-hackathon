"""Snakemake adapters for the bounded, complete pilot SRA intake."""
from __future__ import annotations

import argparse
import json
import shutil
import signal
import sys
from pathlib import Path

from .intake import sha256
from .local_job import run_job, write_record
from .read_intake import verify_archive_names


def receipt(path: Path, value: dict):
    """Preserve existing receipt fields and reject changed evidence."""
    if path.exists():
        previous = json.loads(path.read_text())
        if any(previous.get(key) != item for key, item in value.items()):
            raise ValueError(f"Receipt changed; preserve the original and use a new run: {path}")
        return
    write_record(path, value)


def completed_job(run_dir: Path, name: str) -> dict:
    path = run_dir / f"{name}-attempt-1/job.json"
    result = json.loads(path.read_text())
    if result["status"] != "succeeded":
        raise RuntimeError(f"{name} is not successfully complete; inspect the recorded live handle or failure before retrying")
    return result


def execute(run_dir: Path, name: str, spec: dict, lock_name: str | None = None) -> dict:
    attempt = run_dir / f"{name}-attempt-1"
    if attempt.exists():
        job = completed_job(run_dir, name)
        if job["spec"]["argv"] != spec["argv"] or job["spec"].get("env", {}) != spec.get("env", {}):
            raise ValueError("Existing attempt used different command/environment; create an explicitly versioned attempt")
        return job
    (run_dir / "specs").mkdir(parents=True, exist_ok=True)
    write_record(run_dir / "specs" / f"{name}.json", spec)
    job = run_job(spec, attempt, run_dir / "locks" / f"{lock_name or name}.lock")
    if job["status"] != "succeeded":
        raise RuntimeError(f"{name} failed; original attempt and partial outputs retained")
    return job


def stage(config: dict, name: str):
    root = Path.cwd()
    run_dir = root / config["run_directory"]
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = root / config["cohort_manifest"]
    manifest = json.loads(manifest_path.read_text())
    sample = next(row for row in manifest["samples"] if row["run_id"] == config["run_id"])
    if config["run_id"] != manifest["pilot_run_id"]:
        raise ValueError("This intake adapter is pilot-only until full-sample resource review")
    accession = sample["run_id"]
    archive_root = root / config["archive_directory"]
    fastq_dir = root / config["fastq_directory"]
    fastq = fastq_dir / f"{accession}.fastq"
    tools = root / config["tool_bin"]
    tool_spec = json.loads((root / config["tool_manifest"]).read_text())
    for executable, expected in tool_spec["executable_sha256"].items():
        if sha256(tools / executable) != expected:
            raise ValueError(f"SRA executable differs from pinned build: {executable}")
    common = {"cwd": str(root), "env": {"NCBI_SETTINGS": "/dev/null"}, "timeout_seconds": 1800}
    if name == "prefetch":
        if shutil.disk_usage(root).free < config["minimum_free_bytes"]:
            raise RuntimeError("Insufficient free disk for the declared pilot intake envelope")
        spec = {**common, "argv": [str(tools / "prefetch"), accession, "--max-size", "3G", "--transport", "https", "-O", str(archive_root)]}
        execute(run_dir, "prefetch", spec)
        matches = list(archive_root.rglob(f"{accession}.sra"))
        if len(matches) != 1:
            raise ValueError("Expected exactly one complete accession archive")
        archive = matches[0]
        archive_record = {"run_id": accession, "archive_path": str(archive.relative_to(root)),
                   "sha256": sha256(archive), "bytes": archive.stat().st_size,
                   "prefetch_job": "prefetch-attempt-1/job.json"}
        receipt(run_dir / "archive_receipt.json", archive_record)
        return
    archive_receipt = json.loads((run_dir / "archive_receipt.json").read_text())
    archive = root / archive_receipt["archive_path"]
    if name == "validate":
        if sha256(archive) != archive_receipt["sha256"]:
            raise ValueError("Archive bytes changed after download")
        execute(run_dir, "validate", {**common, "argv": [str(tools / "vdb-validate"), str(archive_root)]}, "archive-validation")
        receipt(run_dir / "archive_validation.json", {"status": "validated", "archive_sha256": archive_receipt["sha256"], "job": "validate-attempt-1/job.json"})
        return
    validation = json.loads((run_dir / "archive_validation.json").read_text())
    if validation["status"] != "validated" or validation["archive_sha256"] != archive_receipt["sha256"]:
        raise ValueError("Archive integrity validation is not established")
    if name == "extract":
        if shutil.disk_usage(root).free < config["minimum_free_bytes"]:
            raise RuntimeError("Insufficient free disk for complete extraction")
        fastq_dir.mkdir(parents=True, exist_ok=True)
        scratch = root / config["scratch_directory"]
        scratch.mkdir(parents=True, exist_ok=True)
        argv = [str(tools / "fasterq-dump"), str(archive.parent), "--split-spot", "--skip-technical",
                "--threads", "2", "--mem", "512M", "--outdir", str(fastq_dir), "--temp", str(scratch),
                "--seq-defline", "@$ac.$si/$ri original_name=$sn", "--qual-defline", "+"]
        execute(run_dir, "extract", {**common, "argv": argv})
        if not fastq.is_file() or fastq.stat().st_size == 0:
            raise ValueError("Expected complete extracted FASTQ is missing")
        receipt(run_dir / "extraction_receipt.json", {"status": "extracted_pending_qc", "fastq_path": str(fastq.relative_to(root)), "bytes": fastq.stat().st_size,
                                                           "archive_sha256": archive_receipt["sha256"], "job": "extract-attempt-1/job.json"})
    elif name == "names":
        argv = [str(tools / "vdb-dump"), str(archive), "-C", "NAME,READ_LEN,READ_TYPE", "-I", "-f", "tab"]
        execute(run_dir, "archive-names", {**common, "argv": argv})
        source = run_dir / "archive-names-attempt-1/stdout.log"
        receipt(run_dir / "archive_names_receipt.json", {"status": "exported", "sha256": sha256(source), "bytes": source.stat().st_size, "job": "archive-names-attempt-1/job.json"})
    elif name == "qc":
        argv = [sys.executable, "-m", "chrna.read_intake", "--manifest", str(manifest_path), "--run", accession,
                "--fastq", str(fastq), "--output", str(run_dir / "qc")]
        execute(run_dir, "read-qc", {**common, "argv": argv})
        result = json.loads((run_dir / "qc/qc.json").read_text())
        if result["status"] != "validated":
            raise ValueError("Complete-run FASTQ QC failed")
        if sha256(fastq) != result["fastq_sha256"]:
            raise ValueError("FASTQ changed after read QC")
        names = run_dir / "archive-names-attempt-1/stdout.log"
        names_receipt = json.loads((run_dir / "archive_names_receipt.json").read_text())
        if sha256(names) != names_receipt["sha256"]:
            raise ValueError("Archive name export changed")
        verify_archive_names(run_dir / "qc/read_ids.sqlite", names, sample["archive_spots"], run_dir / "qc/archive_name_validation.json")
        receipt(run_dir / "intake_validation.json", {"status": "validated", "run_id": accession,
                "archive_sha256": archive_receipt["sha256"], "fastq_sha256": result["fastq_sha256"],
                "reads": result["reads"], "bases": result["bases"],
                "qc_sha256": sha256(run_dir / "qc/qc.json"),
                "name_validation_sha256": sha256(run_dir / "qc/archive_name_validation.json"),
                "crosswalk_sha256": sha256(run_dir / "qc/read_id_crosswalk.tsv"),
                "scope": "Complete pilot input validation, not candidate analysis"})
    else:
        raise ValueError("Unknown intake stage")


def main():
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--stage", choices=["prefetch", "validate", "extract", "names", "qc"], required=True)
    args = parser.parse_args()
    stage(json.loads(args.config.read_text()), args.stage)


if __name__ == "__main__":
    main()
