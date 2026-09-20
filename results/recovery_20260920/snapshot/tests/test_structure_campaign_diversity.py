import importlib.util
from pathlib import Path
import pytest

SPEC = importlib.util.spec_from_file_location('campaign_diversity', Path(__file__).parents[1] / 'scripts/structure_campaign/analyze_structural_diversity.py')
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)


def test_gate_keeps_complete_contiguous_domain_and_inclusive_thresholds():
    confidence = [70.] * 40 + [10.] * 10
    assert m.domain_gate(1, 50, confidence) == ('qualified', .8)
    assert m.domain_gate(1, 49, confidence)[0] == 'span_below_50aa'
    assert m.domain_gate(1, 50, [70.] * 39 + [69.] * 11)[0] == 'insufficient_local_confidence'
    with pytest.raises(ValueError):m.domain_gate(0, 50, confidence)
    with pytest.raises(ValueError):m.domain_gate(1, 51, confidence)
    with pytest.raises(ValueError):m.domain_gate(1, 50, [float('nan')] * 50)


def test_clusters_include_real_singletons_and_transitivity_is_explicit():
    assert m.connected_components(['a', 'b', 'c', 'd'], [('a', 'b'), ('b', 'c')]) == [['a', 'b', 'c'], ['d']]
    assert m.connected_components([], []) == []
    with pytest.raises(ValueError):m.connected_components(['a'], [('a', 'fake')])


def test_rarefaction_is_by_actual_peptides_not_duplicate_domain_records():
    clusters = {'family1': {'p1', 'p2'}, 'family2': {'p2'}}
    assert m.expected_rarefaction(clusters, 2, 0) == 0
    assert m.expected_rarefaction(clusters, 2, 1) == 1.5
    assert m.expected_rarefaction(clusters, 2, 2) == 2
    with pytest.raises(ValueError):m.expected_rarefaction(clusters, 2, 3)
