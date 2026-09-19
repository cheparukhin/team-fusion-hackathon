"""Outcome-free intake of the original mouse direct-RNA cohort.

Metadata are data, never executable instructions. Cached bytes are immutable:
refreshes belong in a new intake directory. No archive downloads occur here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source(path: Path) -> dict:
    record = json.loads(Path(str(path) + ".provenance.json").read_text())
    if sha256(path) != record["sha256"] or path.stat().st_size != record["bytes"]:
        raise ValueError(f"Source integrity failure: {path}")
    return record


def fetch_source(url: str, path: Path) -> None:
    if path.exists():
        if verify_source(path)["url"] != url:
            raise ValueError(f"Cached source URL differs: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(16 * 1024 * 1024 + 1)
    if len(data) > 16 * 1024 * 1024:
        raise ValueError("Metadata response exceeds 16 MiB")
    # Exclusive creation prevents silently replacing another operator's intake.
    with path.open("xb") as handle:
        handle.write(data)
    record = {"url": url, "sha256": hashlib.sha256(data).hexdigest(),
              "bytes": len(data), "retrieved_utc": datetime.now(timezone.utc).isoformat()}
    with Path(str(path) + ".provenance.json").open("x") as handle:
        json.dump(record, handle, indent=2)
        handle.write("\n")


def soft_fields(text: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for line in text.splitlines():
        if line.startswith(("!", "^")) and " = " in line:
            key, value = line.split(" = ", 1)
            fields.setdefault(key, []).append(value)
    return fields


def one(fields: dict, key: str) -> str:
    values = fields.get(key, [])
    if len(values) != 1:
        raise ValueError(f"Expected one {key}; found {len(values)}")
    return values[0]


def validate_runs(text: str) -> list[dict]:
    runs = list(csv.DictReader(io.StringIO(text)))
    if len(runs) != 10 or len({r.get("Run") for r in runs}) != 10:
        raise ValueError("Expected ten distinct mouse runs")
    if len({r.get("SampleName") for r in runs}) != 10:
        raise ValueError("Expected one distinct biological sample per run")
    expected = {"BioProject": "PRJNA1109857", "SRAStudy": "SRP506881",
                "ScientificName": "Mus musculus", "TaxID": "10090",
                "Platform": "OXFORD_NANOPORE", "LibraryLayout": "SINGLE"}
    for row in runs:
        if any(row.get(k) != v for k, v in expected.items()):
            raise ValueError(f"Unexpected cohort identity: {row.get('Run')}")
        if not re.fullmatch(r"SRR\d+", row["Run"]) or not re.fullmatch(r"GSM\d+", row["SampleName"]):
            raise ValueError("Invalid accession")
        if any(int(row[k]) <= 0 for k in ("spots", "bases", "size_MB")):
            raise ValueError("Missing or nonpositive archive counts")
    return runs


def sample_record(row: dict, text: str) -> dict:
    fields = soft_fields(text)
    sample = row["SampleName"]
    if one(fields, "!Sample_geo_accession") != sample or one(fields, "^SAMPLE") != sample:
        raise ValueError("Sample accession mismatch")
    if one(fields, "!Sample_series_id") != "GSE267147":
        raise ValueError("Sample series mismatch")
    relations = "\n".join(fields.get("!Sample_relation", []))
    if row["BioSample"] not in relations or row["Experiment"] not in relations:
        raise ValueError("GEO/SRA cross-reference mismatch")
    protocol = "\n".join(fields.get("!Sample_extract_protocol_ch1", []))
    if "SQK-RNA002" not in protocol or "Direct RNA Sequencing" not in protocol:
        raise ValueError("Direct-RNA chemistry is not established by sample protocol")
    title = one(fields, "!Sample_title")
    match = re.fullmatch(r"(.+)_replicate_(\d+)", title)
    if not match:
        raise ValueError("Cannot resolve condition and replicate from sample title")
    treatment = [v.removeprefix("treatment: ") for v in fields.get("!Sample_characteristics_ch1", [])
                 if v.startswith("treatment: ")]
    if len(treatment) != 1:
        raise ValueError("Treatment metadata missing or ambiguous")
    return {"run_id": row["Run"], "sample_id": sample, "biosample": row["BioSample"],
            "experiment": row["Experiment"], "sample_title": title,
            "condition": match[1], "replicate_within_condition": int(match[2]),
            "biological_sample_id": sample, "treatment": treatment[0],
            "archive_library_selection": row["LibrarySelection"],
            "assay_from_protocol": "direct_RNA", "chemistry": "SQK-RNA002",
            "selection_protocol_discrepancy": row["LibrarySelection"] == "cDNA",
            "archive_spots": int(row["spots"]), "archive_bases": int(row["bases"]),
            "archive_size_MB": int(row["size_MB"]), "download_path": row["download_path"],
            "original_ont_read_names": "UNVERIFIED", "raw_signal_availability": "UNVERIFIED"}


def fetch_cohort(root: Path) -> None:
    fetch_source("https://www.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=SRP506881", root / "sra_runinfo.csv")
    fetch_source("https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE267147&targ=self&form=text&view=full", root / "geo_series.txt")
    for row in validate_runs((root / "sra_runinfo.csv").read_text()):
        sample = row["SampleName"]
        fetch_source(f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={sample}&targ=self&form=text&view=full", root / f"{sample}.txt")


def build_manifest(root: Path, output: Path) -> dict:
    run_file = root / "sra_runinfo.csv"
    records = {run_file.name: verify_source(run_file)}
    series = root / "geo_series.txt"
    records[series.name] = verify_source(series)
    runs = validate_runs(run_file.read_text())
    declared_samples = soft_fields(series.read_text()).get("!Series_sample_id", [])
    if len(declared_samples) != 10 or set(declared_samples) != {r["SampleName"] for r in runs}:
        raise ValueError("Series and run sample membership disagree")
    samples = []
    for row in runs:
        path = root / (row["SampleName"] + ".txt")
        records[path.name] = verify_source(path)
        samples.append(sample_record(row, path.read_text()))
    samples.sort(key=lambda row: row["sample_id"])
    # Smallest complete archive is selected without consulting candidates/outcomes.
    pilot = min(samples, key=lambda row: (row["archive_size_MB"], row["run_id"]))
    result = {"schema_version": 1, "study": "GSE267147", "bioproject": "PRJNA1109857",
              "scope": "original_mouse_direct_RNA", "samples": samples,
              "pilot_run_id": pilot["run_id"],
              "pilot_selection_rule": "smallest reported complete SRA archive; run ID breaks ties",
              "total_archive_spots": sum(r["archive_spots"] for r in samples),
              "total_archive_bases": sum(r["archive_bases"] for r in samples),
              "total_archive_size_MB": sum(r["archive_size_MB"] for r in samples),
              "sources": records,
              "limitations": ["Archive size is not peak disk or FASTQ size.",
                              "Original ONT names and deposited signal remain unverified.",
                              "Direct RNA is not artifact-free; protocol is not a truth label."]}
    output.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if output.exists() and output.read_text() != content:
        raise ValueError("Refusing to replace a different intake manifest; use a new run directory")
    output.write_text(content)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["fetch", "build"])
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "fetch":
        fetch_cohort(args.sources)
    else:
        if args.output is None:
            parser.error("build requires --output")
        result = build_manifest(args.sources, args.output)
        print(json.dumps({k: result[k] for k in ["pilot_run_id", "total_archive_spots", "total_archive_bases", "total_archive_size_MB"]}))


if __name__ == "__main__":
    main()
