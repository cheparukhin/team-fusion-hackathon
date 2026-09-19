import json

import numpy as np
import pandas as pd
import pytest

from chrna.model import feature_frame, gene_components, run, split_folds, validate


def panel():
    rows = []
    for i in range(30):
        for j in range(2):
            rows.append(dict(pair_id=f'A{i}:B{i}_{j}', parent_a=f'A{i}', parent_b=f'B{i}_{j}',
                             label=(i + j) % 2, long_read_support=i + j + 1,
                             sample_count=np.nan, is_interchromosomal=j, genomic_distance=1000 * (i + 1)))
    return pd.DataFrame(rows)


def test_transitive_and_reversed_gene_links_stay_together():
    frame = pd.DataFrame({'parent_a': ['A', 'C', 'D', 'X'], 'parent_b': ['B', 'B', 'C', 'Y']})
    groups = gene_components(frame)
    assert groups[0] == groups[1] == groups[2]
    assert groups[3] != groups[0]


def test_folds_have_no_shared_parent_gene_and_are_repeatable():
    frame = panel()
    folds, _ = split_folds(frame)
    assert np.array_equal(folds, split_folds(frame)[0])
    for fold in set(folds):
        train, test = frame[folds != fold], frame[folds == fold]
        assert not (set(train.parent_a) | set(train.parent_b)) & (set(test.parent_a) | set(test.parent_b))


def test_impossible_gene_disjoint_evaluation_rejected():
    frame = panel()
    frame['parent_a'] = 'SHARED'
    with pytest.raises(ValueError, match='Cannot form'):
        split_folds(frame)


def test_validation_features_are_not_model_inputs_and_distance_semantics():
    frame = panel()
    frame['nanostring_count'] = frame.label * 1000
    features = feature_frame(frame)
    assert 'nanostring_count' not in features
    assert 'label' not in features
    assert features.loc[frame.is_interchromosomal == 1, 'log_genomic_distance'].eq(0).all()
    assert features.sample_count.isna().all()


def test_duplicate_pair_cannot_leak_as_another_example():
    frame = panel()
    with pytest.raises(ValueError, match='unique'):
        validate(pd.concat([frame, frame.iloc[:1]]))


def test_end_to_end_preserves_missing_hic_and_metrics_cohort(tmp_path):
    frame = panel()
    frame.loc[0, 'long_read_support'] = np.nan
    source = tmp_path / 'input.tsv'
    frame.to_csv(source, sep='\t', index=False)
    hic = frame[['pair_id']].copy()
    hic['hic_contact_enrichment'] = np.where(np.arange(len(frame)) % 3 == 0, np.nan, np.arange(len(frame)) + 1)
    hic_path = tmp_path / 'hic.tsv'
    hic.to_csv(hic_path, sep='\t', index=False)
    result = run(source, tmp_path / 'out', hic_path, bootstrap_n=10)
    predictions = pd.read_csv(tmp_path / 'out/predictions.tsv', sep='\t')
    assert predictions.score_rna.notna().all()
    assert predictions.loc[predictions.hic_contact_enrichment.isna(), 'score_hic'].isna().all()
    assert result['full_panel']['rna']['n'] == result['full_panel']['read_support']['n'] == len(frame)
    assert result['matched_hic']['rna']['n'] == result['matched_hic']['hic']['n'] == hic.hic_contact_enrichment.notna().sum()
    assert any('recurrence is unavailable' in text for text in result['limitations'])
    assert json.loads((tmp_path / 'out/metrics.json').read_text())['status'] == 'complete'


def test_top_k_ties_match_exhaustive_permutations():
    from itertools import permutations
    from chrna.model import evaluate
    # One certain positive, then select two of a three-way tie with one positive.
    labels, scores = [1, 1, 0, 0, 0], [3, 2, 2, 2, 1]
    result = evaluate(labels, scores, list("abcde"), k=3)
    outcomes = [1 + sum(order[:2]) for order in permutations([1, 0, 0])]
    assert result['supported_at_k'] == pytest.approx(np.mean(outcomes))
    assert result['boundary_tie']['supported_at_k_range'] == [min(outcomes), max(outcomes)]
    assert result['precision_at_k'] == pytest.approx(np.mean(outcomes) / 3)
    assert evaluate(labels, scores, list("edcba"), k=3)['supported_at_k'] == result['supported_at_k']


def test_top_k_no_ties_small_cohort_and_missing_scores():
    from chrna.model import evaluate
    result = evaluate([1, 0, 1], [2, 1, np.nan], ['a', 'b', 'c'], k=20)
    assert result['k'] == 2
    assert result['supported_at_k'] == 1
    assert result['boundary_tie']['supported_at_k_range'] == [1, 1]
    assert evaluate([0, 0], [1, 1], ['a', 'b'])['recall_at_k'] is None
    with pytest.raises(ValueError, match='positive integer'):
        evaluate([1], [1], ['a'], k=0)
