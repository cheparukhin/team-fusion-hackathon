import importlib.util
from pathlib import Path
import pytest

SPEC = importlib.util.spec_from_file_location('campaign_domains', Path(__file__).parents[1] / 'scripts/structure_campaign/annotate_domains.py')
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)


def test_one_based_inclusive_boundary_coverage():
    assert m.checked_interval(1, 1, 1) == (1, 1)
    assert m.checked_interval(1, 10, 10) == (1, 10)
    assert m.merged_length([(1, 3), (3, 5), (8, 10)]) == 8
    assert m.merged_length([]) == 0
    for interval in [(0, 3, 10), (3, 2, 10), (1, 11, 10)]:
        with pytest.raises(ValueError):m.checked_interval(*interval)


def test_parent_retention_requires_exact_canonical_sequence():
    parent = 'MABCDEFGHIJK'; candidate = 'ABCXYZHI'
    links = [dict(parent_residue_start_1based=2, parent_residue_end_1based=4, candidate_residue_start_1based=1, candidate_residue_end_1based=3),
             dict(parent_residue_start_1based=9, parent_residue_end_1based=10, candidate_residue_start_1based=7, candidate_residue_end_1based=8)]
    fraction, mapped = m.retained_mapping(candidate, parent, links, 3, 10)
    assert fraction == 4 / 8 and mapped == [(2, 3), (7, 8)]
    assert m.retained_mapping(candidate, parent, [], 3, 10) == (0, [])
    bad = [dict(links[0], candidate_residue_end_1based=4)]
    with pytest.raises(ValueError, match='match'):m.retained_mapping(candidate, parent, bad, 1, 10)
    with pytest.raises(ValueError, match='match'):m.retained_mapping('ZZZXYZHI', parent, links, 1, 10)


def test_overlap_retention_is_not_double_counted():
    links = [dict(parent_residue_start_1based=1, parent_residue_end_1based=5, candidate_residue_start_1based=1, candidate_residue_end_1based=5)] * 2
    fraction, _ = m.retained_mapping('ABCDE', 'ABCDE', links, 1, 5)
    assert fraction == 1
