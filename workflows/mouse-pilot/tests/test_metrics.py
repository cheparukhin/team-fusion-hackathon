import itertools

import numpy as np
import pytest

from chrna.metrics import tie_aware_topk


def test_random_ranking_matches_sampling_expectation():
    result = tie_aware_topk([1, 1, 0, 0, 0], [0] * 5, 2)
    assert result["expected_supported_at_k"] == pytest.approx(0.8)
    assert result["known_positive_recall_at_k"] == pytest.approx(0.4)


def test_ties_match_exhaustive_enumeration():
    labels = np.array([1, 1, 0, 0, 1, 0])
    score = np.array([4, 2, 2, 2, 2, 0])
    actual = tie_aware_topk(labels, score, 3)["expected_supported_at_k"]
    all_orders = list(itertools.combinations([1, 2, 3, 4], 2))
    expected = np.mean([1 + labels[list(x)].sum() for x in all_orders])
    assert actual == pytest.approx(expected)


def test_missing_score_is_not_silently_ranked_as_zero():
    with pytest.raises(ValueError):
        tie_aware_topk([1, 0], [1, np.nan], 1)


def test_complete_recovery_and_no_positives():
    assert tie_aware_topk([1, 0, 1], [3, 2, 1], 3)["known_positive_recall_at_k"] == 1
    assert tie_aware_topk([0, 0], [1, 0], 1)["known_positive_recall_at_k"] is None


@pytest.mark.parametrize("labels", [[True, np.nan], ["False", "True"], [None, 1], [0, 2]])
def test_missing_or_string_labels_cannot_silently_become_positive(labels):
    with pytest.raises(ValueError, match="Labels"):
        tie_aware_topk(labels, [2, 1], 1)
