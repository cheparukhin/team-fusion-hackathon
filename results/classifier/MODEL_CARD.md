# chRNA reported-support classifier

Target: published NanoString support within the mapped probe panel.

L2 logistic regression, C=1; fold-local median imputation, missingness indicators, and standardization.
Parent-gene connected components are kept entirely within folds; all displayed evaluation scores are out-of-fold.

## Evaluation

| Method | N | Average precision | Supported / top 20 |
|---|---:|---:|---:|
| read_support | 479 | 0.268 | 11.07 / 20 |
| rna | 479 | 0.296 | 11.00 / 20 |

Hi-C comparison trains and evaluates both models on identical rows with observed contact enrichment, within the original folds; see metrics.json.

Hi-C method: mean over distinct ordered probe bin pairs within replicate; equal-weight mean across observed replicates; primary requires all3

Paper deviation: Paper describes merged replicates before processing. GEO supplies individual processed replicate .hic files. This pilot averages independently KR-normalized per-replicate ratios and is not an exact merged-matrix reproduction.

## Limitations

- The target is published NanoString support within a selected probe-design panel, not biological authenticity.
- Unreported support is not a verified negative; testing and probe QC may be unknown.
- Labels and predictions refer to ordered parent-gene pairs, not validated junction isoforms.
- Out-of-fold scores are not calibrated probabilities; all-data refit scores are not evaluation results.
- The selected panel and parent-gene grouping limit generalization to unseen tissues and datasets.
- Top-k metrics average uniformly over tied boundary scores; pair-ID ordering is retained only as an audit field.
- Bootstrap intervals resample parent-gene components of fixed out-of-fold predictions; they do not capture model-refitting uncertainty.
- Hi-C is regional 500-kb context, not splice-junction resolution; its assay timing differs from RNA measurements.
- Public long-read tables do not supply sample-level read provenance; recurrence is unavailable and contributes no signal.

Saved joblib files are local trusted artifacts for all-data refitting; do not load untrusted pickle/joblib files.
