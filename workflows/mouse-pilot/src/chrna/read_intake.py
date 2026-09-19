"""Validate complete single-read SRA FASTQ and preserve read-ID provenance."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter
from itertools import zip_longest
from pathlib import Path

HEADER = re.compile(r"@(SRR\d+)\.([1-9]\d*)/([1-9]\d*) original_name=(.*)")
ONT_NAME = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")


def records(path: Path):
    """Strict four-line FASTQ, as emitted by our pinned fasterq-dump invocation."""
    with path.open("rb") as handle:
        while header := handle.readline():
            sequence, plus, quality = (handle.readline() for _ in range(3))
            raw = header + sequence + plus + quality
            if not all(line.endswith(b"\n") for line in (header, sequence, plus, quality)):
                raise ValueError("Truncated FASTQ record")
            header, sequence, plus, quality = (line.rstrip(b"\r\n") for line in (header, sequence, plus, quality))
            match = HEADER.fullmatch(header.decode("ascii"))
            if not match:
                raise ValueError("FASTQ header does not match frozen archive/name format")
            if plus != b"+" or not sequence or len(sequence) != len(quality):
                raise ValueError("Malformed FASTQ sequence/quality record")
            if re.search(b"[^ACGTNacgtn]", sequence) or any(q < 33 or q > 126 for q in quality):
                raise ValueError("Invalid FASTQ sequence or quality encoding")
            yield match.groups(), sequence, quality, raw


def inspect_fastq(path: Path, sample: dict, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    database = sqlite3.connect(output / "read_ids.sqlite")
    database.execute("CREATE TABLE reads (read_id TEXT PRIMARY KEY, spot_id INTEGER NOT NULL UNIQUE, read_number INTEGER NOT NULL, original_name TEXT, length INTEGER NOT NULL, sequence_sha256 TEXT NOT NULL)")
    digest = hashlib.sha256()
    lengths = Counter()
    name_states = Counter()
    count = bases = quality_sum = n_bases = 0
    try:
        with (output / "read_id_crosswalk.tsv").open("w", newline="") as crosswalk:
            writer = csv.writer(crosswalk, delimiter="\t")
            writer.writerow(["sample_id", "run_id", "read_id", "archive_spot_id", "archive_read_number", "submitted_name", "name_status", "sequence_length", "sequence_sha256"])
            for (run, spot, read, name), sequence, quality, raw in records(path):
                if run != sample["run_id"] or read != "1":
                    raise ValueError("Wrong run or unexpected multi-read spot in single-read cohort")
                count += 1
                bases += len(sequence)
                quality_sum += sum(quality) - 33 * len(quality)
                n_bases += sequence.upper().count(b"N")
                lengths[len(sequence)] += 1
                digest.update(raw)
                name_state = "missing" if not name else "uuid_shaped" if ONT_NAME.fullmatch(name) else "non_uuid_submitted_name"
                name_states[name_state] += 1
                read_id = f"{run}.{spot}/{read}"
                sequence_sha = hashlib.sha256(sequence).hexdigest()
                try:
                    database.execute("INSERT INTO reads VALUES (?, ?, ?, ?, ?, ?)",
                                     (read_id, int(spot), int(read), name or None, len(sequence), sequence_sha))
                except sqlite3.IntegrityError as error:
                    raise ValueError("Duplicate archive molecule/spot ID; possible duplicate ingestion") from error
                writer.writerow([sample["sample_id"], run, read_id, spot, read, name, name_state, len(sequence), sequence_sha])
                if count % 10000 == 0:
                    database.commit()
            database.commit()
        database.execute("CREATE INDEX original_name ON reads(original_name)")
        database.commit()
        duplicate_names = database.execute("SELECT count(*), coalesce(sum(n),0) FROM (SELECT count(*) n FROM reads WHERE original_name IS NOT NULL GROUP BY original_name HAVING count(*)>1)").fetchone()
        result = {"schema_version": 1, "sample_id": sample["sample_id"], "run_id": sample["run_id"],
                  "fastq_sha256": digest.hexdigest(), "reads": count, "bases": bases,
                  "expected_spots": sample["archive_spots"], "expected_bases": sample["archive_bases"],
                  "name_states": dict(name_states), "duplicate_submitted_name_groups": duplicate_names[0],
                  "reads_in_duplicate_name_groups": duplicate_names[1],
                  "n_bases": n_bases, "mean_base_phred": quality_sum / bases if bases else None,
                  "min_length": min(lengths) if lengths else None,
                  "max_length": max(lengths) if lengths else None,
                  "mean_length": bases / count if count else None,
                  "status": "validated" if count == sample["archive_spots"] and bases == sample["archive_bases"] else "count_mismatch",
                  "name_validation": "Submitted names preserved from defline; independent SRA NAME comparison required.",
                  "duplicate_policy": "No sequence or coordinate deduplication. Repeated submitted names require molecule-identity review."}
        (output / "qc.json").write_text(json.dumps(result, indent=2) + "\n")
        with (output / "read_length_histogram.tsv").open("w") as out:
            out.write("length\tread_count\n")
            for length, occurrences in sorted(lengths.items()):
                out.write(f"{length}\t{occurrences}\n")
        if result["status"] != "validated":
            raise ValueError("Extracted counts disagree with complete-run manifest; QC evidence retained")
        return result
    finally:
        database.close()


def verify_archive_names(database_path: Path, archive_rows: Path, expected_spots: int, output: Path) -> dict:
    """Compare independently extracted SRA NAME/READ_LEN/READ_TYPE to each read."""
    count = mismatches = missing_names = 0
    examples = []
    with sqlite3.connect(f"file:{database_path.resolve()}?mode=ro", uri=True) as database, archive_rows.open() as handle:
        extracted = database.execute("SELECT spot_id,original_name,length FROM reads ORDER BY spot_id")
        for observed, source_line in zip_longest(extracted, handle):
            count += 1
            error = None
            if observed is None or source_line is None:
                error = "archive_and_fastq_row_count_disagree"
            else:
                columns = source_line.rstrip("\n").split("\t")
                if len(columns) != 4:
                    error = "unexpected_archive_row_format"
                else:
                    spot, name, length, read_type = columns
                    try:
                        expected = (int(spot), name or None, int(length))
                    except ValueError:
                        error = "non_scalar_archive_spot_or_length"
                    else:
                        if tuple(observed) != expected:
                            error = "archive_and_fastq_identity_or_length_disagree"
                        elif read_type != "SRA_READ_TYPE_BIOLOGICAL":
                            error = "unexpected_archive_read_type"
                        elif not name:
                            missing_names += 1
            if error:
                mismatches += 1
                if len(examples) < 100:
                    examples.append({"row": count, "reason": error})
    result = {"rows_compared": count, "expected_spots": expected_spots,
              "mismatches": mismatches, "examples": examples, "missing_submitted_names": missing_names,
              "status": "validated" if mismatches == 0 and count == expected_spots else "failed",
              "meaning": "Every extracted submitted name and sequence length matches the independently read archive NAME and READ_LEN; no claim about raw signal availability."}
    output.write_text(json.dumps(result, indent=2) + "\n")
    if result["status"] != "validated":
        raise ValueError("Archive-name crosswalk validation failed; discrepancy record retained")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--run", required=True)
    parser.add_argument("--fastq", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    cohort = json.loads(args.manifest.read_text())
    matches = [sample for sample in cohort["samples"] if sample["run_id"] == args.run]
    if len(matches) != 1:
        parser.error("Expected exactly one matching run in manifest")
    print(json.dumps(inspect_fastq(args.fastq, matches[0], args.output), indent=2))


if __name__ == "__main__":
    main()
