import pandas as pd

from chrna.data import assign_components, PROBE_PAIR_ALIASES


def test_connected_genes_and_duplicate_sequences_do_not_cross_folds():
    pairs = pd.DataFrame({"pair_id": ["A:B", "B:C", "D:E", "F:G", "H:I"],
                          "gene_a": ["A", "B", "D", "F", "H"],
                          "gene_b": ["B", "C", "E", "G", "I"]})
    probes = pd.DataFrame({"pair_id": pairs.pair_id, "sequence_sha256": ["s1", "s2", "shared", "shared", "s3"]})
    splits = assign_components(pairs, probes, folds=3).set_index("pair_id")
    assert splits.loc["A:B", "fold"] == splits.loc["B:C", "fold"]
    assert splits.loc["D:E", "fold"] == splits.loc["F:G", "fold"]
    for gene in set(pairs.gene_a) | set(pairs.gene_b):
        ids = pairs.loc[(pairs.gene_a == gene) | (pairs.gene_b == gene), "pair_id"]
        assert splits.loc[ids, "fold"].nunique() == 1


def test_probe_aliases_are_explicit_and_do_not_rewrite_arbitrary_gene_names():
    assert PROBE_PAIR_ALIASES["Aoah:Sirt5_2"] == "Aoah:Sirt5"
    assert PROBE_PAIR_ALIASES.get("A:GENE_2", "A:GENE_2") == "A:GENE_2"
