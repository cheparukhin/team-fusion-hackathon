# Independent model and Hi-C review

Reviewer: data worker (did not implement model.py, score_catalogue.py, or hic.py).

## Findings and resolutions

- **P1 — invalid KR normalization converted to observed zero**. Original `scripts/compute/extract_hic_features.py:24–30` initialized dense arrays to zero from hic-straw records. hic-straw removes NaN/Inf normalized records, so finite-array checks could not identify missing normalization. Independent inspection of normalization vectors found 41 affected previously observed replicate windows (13 A,14 B,14 C), spanning 14 eligible model pairs. Fix now implemented by compute owner: inspect both chromosome-index KR vectors and mask nonfinite/nonpositive/missing vector bins before window extraction. **Resolved and verified**: regenerated outputs now mark all 41 windows unavailable_pixels, with missing enrichment; all 14 affected pairs have unavailable primary contact features. Final eligible observed-contact cohort is 401 pairs / 92 positives.
- **P2 — contact effect mixed with availability signal in original matched comparison**. Original `src/chrna/model.py:174–178` trained the augmented model on full-panel folds with Hi-C imputation/missingness indicators, then evaluated observed-contact rows. This estimates conditional performance of contact-plus-availability, not an isolated additional-contact comparison. Coordinator revised both matched models to train only identical observed-contact training rows, preserving the original gene-disjoint folds and keeping the full-panel RNA model separately. **Resolved and verified**: reviewed revised training masks and score columns; independent fold-0 refits of full RNA, matched RNA and matched RNA+Hi-C each agree with saved scores within 8.4e-17.
- **P2 — incomplete combined-model provenance**. Original metrics saved the RNA input checksum but not the Hi-C feature checksum or feature manifest reference. **Resolved and verified**: final metrics include feature-file SHA256, feature-manifest SHA256, model-code SHA256, per-fold matched train/test counts and the explicit training policy. All saved hashes match the final files. Model card retains the per-replicate-versus-merged paper deviation.

## Verification

- Saved input checksum matches the frozen model input.
- All five original folds are parent-gene-disjoint, including transitive components; fold sizes 94–97 with 21–22 positives.
- Independent fold-by-fold refitting reproduced original saved RNA scores within 1.2e-16 and original augmented scores within 6.7e-16.
- Recomputed baseline/RNA average precision and stable-ID top-20 counts exactly match saved metrics. Original matched metrics and fixed-prediction component bootstrap also recomputed exactly.
- Feature list contains only prespecified read, missing sample recurrence, chromosome, interval-distance, and optional contact inputs; no validation-derived features.
- GENOVA cached source confirms median central 3×3 foreground and median 64 corner pixels for 11×11 windows. Published methods specify 500-kb resolution, balancing, 11 bins and 500-kb distance threshold. Base-to-bin conversion and reversed chromosome-axis handling are correct.
- Baseline missing counts rank last without interpreting missing as zero. Actual eligible panel has no missing read counts.
- Bootstrap is explicitly a component bootstrap of fixed OOF predictions; it is not model-refitting uncertainty or causal evidence.
- Catalogue ranks 29,911 published nonpanel candidates, with no panel labels or scores reused as evaluation. It labels scores exploratory, marks read/distance range extrapolation, and uses only the full-panel RNA refit. No new discovery/external-validation claim is made.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_model.py tests/test_hic.py -q`: **12 passed** at review time.

Final combined metrics were regenerated after normalization correction and verified on the 401-pair cohort. Preserve the per-replicate-versus-merged normalization deviation and the RNA/Hi-C treatment-time mismatch in result interpretation. Do not select features, rows, or methods based on significance.

## Final result check

- Full eligible RNA cohort: 479 pairs / 109 positives; unchanged baseline and RNA metrics.
- Matched contact cohort: 401 pairs / 92 positives. Baseline AP 0.265636; matched RNA AP 0.295950; matched RNA+Hi-C AP 0.299593.
- Added-contact AP difference 0.003643; fixed-prediction component bootstrap 95% interval [-0.031044, 0.046886], so improvement is not established. Top-20 support decreases from 10/20 (RNA) to 9/20 (RNA+Hi-C).
- Every full and matched metric recomputes from saved prediction columns. Every saved matched-fold train/test count is correct, both classes occur in each subset, and parent-gene disjointness remains intact.
- Missing-contact rows have no matched RNA or Hi-C score; all 479 retain full-panel RNA scores.
- The final bootstrap was not rerun redundantly: its implementation and previous output were independently verified, and final counts, predictions, AP delta and provenance were checked.
- **No unresolved review findings.**

## Descriptive directory migration

The dataset directory was subsequently renamed without changing scientific artifacts. One model reproduction refreshed the default-path code provenance; folds, features and predictions remain byte-identical, and all scientific metrics exactly match the reviewed result. Historical review/metric hashes are preserved under history/; see PATH_MIGRATION.md and path_migration_verification.json for the current provenance chain.
