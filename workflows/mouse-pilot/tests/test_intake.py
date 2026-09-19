import csv
import io
import json
from pathlib import Path

import pytest

from chrna.intake import build_manifest, sample_record, validate_runs, verify_source

SOURCES = Path(__file__).resolve().parents[1] / "runs/intake-20260919"


def run_text(rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


@pytest.fixture
def rows():
    return list(csv.DictReader((SOURCES / "sra_runinfo.csv").open()))


def test_original_cohort_and_label_free_pilot(tmp_path):
    output = tmp_path / "manifest.json"
    result = build_manifest(SOURCES, output)
    assert result["total_archive_spots"] == 52903853
    assert result["total_archive_bases"] == 52141082386
    assert result["total_archive_size_MB"] == 45544
    assert result["pilot_run_id"] == "SRR28984805"
    assert len({r["biological_sample_id"] for r in result["samples"]}) == 10
    assert all(r["selection_protocol_discrepancy"] for r in result["samples"])
    assert build_manifest(SOURCES, output) == result
    output.write_text("{}")
    with pytest.raises(ValueError, match="replace"):
        build_manifest(SOURCES, output)


@pytest.mark.parametrize("key,value", [("BioProject", "other"), ("LibraryLayout", "PAIRED"),
                                       ("TaxID", "9606"), ("spots", "0")])
def test_wrong_cohort_or_missing_counts_rejected(rows, key, value):
    rows[0][key] = value
    with pytest.raises(ValueError):
        validate_runs(run_text(rows))


def test_duplicate_ingestion_rejected(rows):
    rows[0] = rows[1].copy()
    with pytest.raises(ValueError):
        validate_runs(run_text(rows))


def test_protocol_not_inferred_from_archive_cdna(rows):
    row = rows[0]
    text = (SOURCES / (row["SampleName"] + ".txt")).read_text()
    assert sample_record(row, text)["assay_from_protocol"] == "direct_RNA"
    with pytest.raises(ValueError, match="chemistry"):
        sample_record(row, text.replace("SQK-RNA002", "unknown"))
    with pytest.raises(ValueError, match="cross-reference"):
        sample_record(row, text.replace(row["BioSample"], "SAMNwrong"))


def test_changed_cached_bytes_fail_integrity_check(tmp_path):
    path = tmp_path / "metadata.txt"
    path.write_text("changed")
    Path(str(path) + ".provenance.json").write_text(json.dumps({"sha256": "0" * 64, "bytes": 7}))
    with pytest.raises(ValueError, match="integrity"):
        verify_source(path)
