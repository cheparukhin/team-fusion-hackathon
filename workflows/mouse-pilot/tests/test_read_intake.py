import json
import sqlite3

import pytest

from chrna.read_intake import inspect_fastq, verify_archive_names

NAME = "12345678-1234-1234-1234-123456789012"


def fastq(tmp_path, names=(NAME, ""), sequence="ACGTN"):
    path = tmp_path / "reads.fastq"
    path.write_text("".join(f"@SRR123.{i}/1 original_name={name}\n{sequence}\n+\n{'I'*len(sequence)}\n" for i, name in enumerate(names, 1)))
    sample = {"sample_id": "GSM1", "run_id": "SRR123", "archive_spots": len(names), "archive_bases": len(names)*len(sequence)}
    return path, sample


def test_crosswalk_missing_names_and_identical_sequences_preserved(tmp_path):
    path, sample = fastq(tmp_path)
    output = tmp_path / "qc"
    result = inspect_fastq(path, sample, output)
    assert result["reads"] == 2
    assert result["name_states"] == {"uuid_shaped": 1, "missing": 1}
    with sqlite3.connect(output / "read_ids.sqlite") as db:
        assert db.execute("SELECT count(*),count(distinct sequence_sha256) FROM reads").fetchone() == (2,1)
    assert NAME in (output / "read_id_crosswalk.tsv").read_text()


def test_duplicate_molecule_rejected(tmp_path):
    path, sample = fastq(tmp_path)
    path.write_text(path.read_text().replace("SRR123.2/1", "SRR123.1/1"))
    with pytest.raises(ValueError, match="Duplicate"):
        inspect_fastq(path, sample, tmp_path / "qc")


def test_repeated_submitted_names_flagged_without_removing_reads(tmp_path):
    path, sample = fastq(tmp_path, (NAME, NAME))
    result = inspect_fastq(path, sample, tmp_path / "qc")
    assert result["reads"] == 2
    assert result["duplicate_submitted_name_groups"] == 1
    assert result["reads_in_duplicate_name_groups"] == 2


def test_count_disagreement_preserves_failure_evidence(tmp_path):
    path, sample = fastq(tmp_path)
    sample["archive_spots"] = 3
    output = tmp_path / "qc"
    with pytest.raises(ValueError, match="counts"):
        inspect_fastq(path, sample, output)
    assert json.loads((output / "qc.json").read_text())["status"] == "count_mismatch"


@pytest.mark.parametrize("change", [lambda s:s[:-2], lambda s:s.replace("IIIII", "IIII"),
                                    lambda s:s.replace("SRR123", "SRR999"), lambda s:s.replace("/1", "/2")])
def test_corruption_or_wrong_run_fails(tmp_path, change):
    path, sample = fastq(tmp_path)
    path.write_text(change(path.read_text()))
    with pytest.raises(ValueError):
        inspect_fastq(path, sample, tmp_path / "qc")


def test_independent_archive_name_comparison(tmp_path):
    path, sample = fastq(tmp_path)
    output = tmp_path / "qc"
    inspect_fastq(path, sample, output)
    archive = tmp_path / "names.tsv"
    archive.write_text(f"1\t{NAME}\t5\tSRA_READ_TYPE_BIOLOGICAL\n2\t\t5\tSRA_READ_TYPE_BIOLOGICAL\n")
    report = output / "name_check.json"
    result = verify_archive_names(output / "read_ids.sqlite", archive, 2, report)
    assert result["status"] == "validated"
    assert result["missing_submitted_names"] == 1
    archive.write_text(archive.read_text().replace(NAME, "altered"))
    with pytest.raises(ValueError, match="crosswalk"):
        verify_archive_names(output / "read_ids.sqlite", archive, 2, report)
    assert json.loads(report.read_text())["mismatches"] == 1
