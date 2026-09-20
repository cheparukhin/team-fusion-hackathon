# Sequence disorder analysis

CPU metapredict 3.0.2, disorder network V3; raw normalized per-residue outputs, no predicted-pLDDT API. Residues with score >=0.5 are called disordered. f_IDR is their fraction; predominantly disordered means f_IDR >0.5, with protein-level 0.4/0.6 sensitivity. Longest IDR here is the longest consecutive run above threshold; separately saved segment calls use package defaults (minimum IDR12, minimum non-disordered segment50, gap closure10). Non-disordered segments are not experimentally established domains.

V1 (residue threshold >=0.42) is a within-package sensitivity analysis, not an independent predictor. V3 training includes AlphaFold-derived information, so agreement with fold confidence is not independent validation. IUPred was not run: its official local distribution requires academic registration/license; no identity or affiliation was invented.

Every cohort tier is reported separately. Reconstructable hypothetical peptides are not demonstrated translation products. Protein-equal and residue-weighted means answer different questions. These finite-census summaries have no sampling confidence interval; predictor, ORF and ascertainment uncertainty remain. No unavailable sequence is assigned an order/disorder result.

Sources: https://github.com/idptools/metapredict ; https://metapredict.readthedocs.io/en/latest/usage/using-in-python.html ; https://iupred3.elte.hu/download_new
