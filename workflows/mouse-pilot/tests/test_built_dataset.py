from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def built():
    folder = ROOT / 'data/processed'
    if not folder.exists():
        pytest.skip('Run chrna build for source-data integration checks')
    return folder


def test_outcomes_never_become_biological_negatives_or_input_features(built):
    outcomes = pd.read_csv(built / 'evaluation_outcomes.csv')
    features = pd.read_csv(built / 'candidate_pairs.csv')
    assert outcomes.biological_negative_label.isna().all()
    assert outcomes.loc[~outcomes.nanostring_reported_support, 'rna_evidence_status'].eq('unconfirmed').all()
    assert not set(['nanostring_reported_support','protein_evidence','rna_evidence_status']) & set(features.columns)
    assert features.loc[~features.baseline_eligible, 'long_read_support'].isna().all()


def test_actual_parents_and_sequences_are_split_together(built):
    splits = pd.read_csv(built / 'splits.csv')
    gene_folds = {}
    for row in splits.itertuples():
        for gene in [row.gene_a, row.gene_b]:
            gene_folds.setdefault(gene, set()).add(row.fold)
    assert all(len(folds) == 1 for folds in gene_folds.values())
    probes = pd.read_csv(built / 'probe_sequences.csv').merge(splits[['pair_id','fold']], on='pair_id', validate='many_to_one')
    assert probes.groupby('sequence_sha256').fold.nunique().max() == 1


def test_heldout_evaluation_requires_explicit_request():
    from chrna.benchmark import benchmark
    with pytest.raises(ValueError, match='Freeze'):
        benchmark(ROOT, partition='heldout')
