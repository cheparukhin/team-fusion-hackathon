# Presentation facts

**Question:** Can 3D genome context help prioritize chimeric RNA candidates for independent support?

**What we built:** an audited published dataset, a small reproducible classifier, an actual spatial-feature pipeline, and an offline evidence explorer with source-grounded Codex reports.

| Comparison | Evaluation pairs | Reported positives | Average precision | Expected supported in top 20 |
|---|---:|---:|---:|---:|
| Read support, full panel | 479 | 109 | 0.268 | 11.07 |
| RNA/genomic model, full panel | 479 | 109 | 0.296 | 11.00 |
| Read support, matched contact cohort | 401 | 92 | 0.266 | 9.73 |
| RNA/genomic model, matched training and testing | 401 | 92 | 0.296 | 9.63 |
| RNA + Hi-C, matched training and testing | 401 | 92 | 0.300 | 9 |

Top-20 counts average over uniform random ordering within boundary ties. No top-20 uplift over read support is established. Exact boundary sizes and attainable ranges are recorded in metrics.json.

**Honest result:** adding Hi-C did not establish improved prioritization in this selected panel. The average-precision difference is +0.00364, with a 95% group-bootstrap interval of −0.0310 to +0.0469. The models remain a proof of concept.

**Why the execution matters:** probe identities were verified against actual transcript sequences; parent-related examples cannot leak between folds; an independent agent found and fixed a normalization bug; every result can be traced to source data and reproduced. The highest model score without reported support is a useful demo of why evidence review remains essential.

**Claims to avoid:** biological probability, newly validated chRNAs, causal model discovery, RNA-to-protein validation, druggability, proven Hi-C benefit, or GPU speedup without a CPU comparison.

Use ../classifier/evaluation.png or evaluation.svg for the figure, and ../demo/presentation.md for the five-minute runbook. Check ../compute/pilot_summary.json for the actual NVIDIA result before rehearsing that part.

## Executed NVIDIA RNA pilot

Parabricks 4.7.1-1 on NVIDIA A100 80 GB aligned exactly 2,000,000 validated paired 151-nt reads from SRR37513722 in 85.49 seconds (alignment only; reference setup excluded). BAM integrity checks passed. The output contains 3,275 split-junction records and 25,207 encompassing-mate records. Zero probe-panel junctions matched the fixed strand-aware ±10-nt criteria. Non-detection in this bounded sample does not refute candidate transcripts. These observations do not modify classifier labels or scores. No CPU benchmark or speedup claim is made.
