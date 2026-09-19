import pytest

from chrna.junction_ranking import Junction, aggregate_and_rank


def row(boundary=100, read="r1", sample="s1", caller="LongGF", **changes):
    return {"junction": Junction("GRCm39", "g1.1", "chr1", "+", boundary, "g2.1", "chr2", "-", 200),
            "sample_id": sample, "biological_sample_id": sample, "read_id": read,
            "state": "supported_two_gene_junction", "mapping_specific": True,
            "split_single_margin": 20, "shorter_anchor_nt": 60, "caller": caller, **changes}


def test_caller_agreement_does_not_multiply_molecules():
    ranked = aggregate_and_rank([row(caller=c) for c in ["LongGF", "JAFFAL", "Genion"]])
    assert ranked[0]["distinct_qualifying_reads"] == 1
    assert ranked[0]["biological_samples"] == 1
    assert ranked[0]["caller_agreement"] == 3


def test_biological_replication_precedes_read_depth_and_singletons_remain():
    records = [row(100, read=f"r{i}") for i in range(10)] + [row(101, sample=s) for s in ["s1", "s2"]] + [row(102)]
    ranked = aggregate_and_rank(records)
    assert [r["boundary_5p"] for r in ranked] == [101, 100, 102]


def test_exact_coordinates_and_strands_define_distinct_candidates():
    first, second = row(100), row(101)
    assert first["junction"].junction_id != second["junction"].junction_id
    assert len(aggregate_and_rank([first, second])) == 2


def test_display_identifier_does_not_break_scientific_ties():
    ranked = aggregate_and_rank([row(100), row(101), row(102)])
    assert all((r["rank_min"], r["rank_max"]) == (1, 3) for r in ranked)
    assert ranked == aggregate_and_rank([row(102), row(100), row(101)])


def test_same_molecule_conflicting_evidence_requires_reconciliation():
    with pytest.raises(ValueError, match="Conflicting"):
        aggregate_and_rank([row(), row(caller="JAFFAL", split_single_margin=30)])


def test_outcomes_cannot_enter_ranking_schema():
    with pytest.raises(ValueError, match="schema"):
        aggregate_and_rank([{**row(), "nanostring_reported_support": True}])


def test_unknown_margins_remain_unknown_and_not_zero():
    ranked = aggregate_and_rank([row(100, split_single_margin=None), row(101, split_single_margin=-5)])
    assert ranked[0]["boundary_5p"] == 101
    assert ranked[1]["median_split_single_margin"] is None


def test_single_transcript_explained_is_retained_without_qualifying_support():
    ranked = aggregate_and_rank([row(state="single_transcript_explained")])
    assert ranked[0]["distinct_qualifying_reads"] == 0
    assert ranked[0]["assessed_distinct_reads"] == 1
    assert ranked[0]["evidence_state"] == "single_transcript_explained"


def test_same_gene_event_is_not_a_two_gene_junction():
    with pytest.raises(ValueError, match="Same-gene"):
        Junction("GRCm39", "g1.1", "chr1", "+", 100, "g1.1", "chr1", "+", 200)


def test_unresolved_measurements_can_remain_unknown():
    ranked = aggregate_and_rank([row(state="unmapped/unresolved", mapping_specific=None,
                                    shorter_anchor_nt=None, split_single_margin=None)])
    assert ranked[0]["assessed_distinct_reads"] == 1
    assert ranked[0]["median_shorter_anchor_nt"] is None


def test_scan_is_preserved_without_inflating_caller_agreement():
    ranked = aggregate_and_rank([row(caller="alignment_scan"), row(caller="LongGF")])
    assert ranked[0]["caller_agreement"] == 1
    assert ranked[0]["proposal_sources"] == ["LongGF", "alignment_scan"]


def test_sample_identity_cannot_manufacture_replication():
    with pytest.raises(ValueError, match="biological identities"):
        aggregate_and_rank([row(), row(read="r2", biological_sample_id="invented")])
