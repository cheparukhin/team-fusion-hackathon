# Scientific review

**Verdict: scientifically defensible as a retrospective evidence-review demonstration, with the limits below.** Reviewed by Codex at the user's request on 20 September 2026. This is an AI review, not independent human signoff or experimental validation. [Verification receipt](../../results/review/scientific_review.json).

## Findings and decisions

| Area | Review conclusion | Evidence |
|---|---|---|
| Ranking | Recalculated AP is 0.295950 for RNA and 0.299593 with Hi-C on the same 401 pairs (92 reported positives). Five folds have no shared parent genes. The +0.003643 difference has a component-bootstrap interval of −0.031044 to +0.046886: no established gain. | [Predictions](../../results/classifier/predictions.tsv), [metrics](../../results/classifier/metrics.json), [implementation](../../src/chrna/model.py) |
| Psap–Lgals3 | Retain the recommendation to reconcile source alignments before choosing an assay. The pinned spreadsheets and GENCODE reconstruction reproduce six distinct read IDs and the nearest second-parent difference of 924 genomic bases. This is not proof of a bad probe or false RNA. | [Source calculation](../../results/review/psap_source_audit.json), [decision](../../results/review/psap-lgals3/decision.json) |
| Gsdmd–Tmem106a | Revised the recommendation and demo to acknowledge published protein and functional experiments, beyond RNA support. Our low-confidence reference model does not contradict those experiments. A follow-up would concern a specified new sample. | [Primary paper, Figures 3–4](https://www.nature.com/articles/s41586-026-10982-x), [revised decision](../../results/review/gsdmd-tmem106a/decision.json), [structure methods](../../results/structures/METHODS.md) |
| Cd274–Lacc1 | Retain published junction evidence. Missing project structure and bounded GPU non-detection do not reject the RNA. Any new confirmation must specify sample, junction and controls. | [Primary paper, Extended Data Figure 2](https://www.nature.com/articles/s41586-026-10982-x), [decision](../../results/review/cd274-lacc1/decision.json) |
| NVIDIA evidence | The real two-million-pair alignment was re-matched, returning zero probe-junction matches. This verifies bounded non-detection, not sensitivity, absence, or a CPU speedup. | [Run evidence](../../results/compute/pilot_summary.json), [matching output](../../results/review/psap-lgals3/step-03.json) |
| Recorded agent | All twelve tool outputs replay exactly. This verifies computations and evidence pointers, not experimental utility or every biological inference. The three examples were selected after inspecting existing results. | [Case selection](../../results/review/case_freeze.json), [replay code](../../scripts/review/verify.py) |

## Interpretation that must stay explicit

- The label is **reported NanoString support** in a selected panel. Unreported rows are not confirmed biological negatives; assay and probe-QC uncertainty can influence predictability. AP is not RNA authenticity or a calibrated probability.
- The matched analysis excludes 78 pairs without complete Hi-C evidence. Its conclusion is confined to that subset. It does not establish that chromatin proximity is biologically irrelevant or contradict the paper's mechanistic experiments.
- RNA features are read support, chromosome relationship and genomic distance. Sample recurrence is unavailable. Preprocessing is fitted within training folds; there is no assay-derived model input. Fixed-prediction bootstrap uncertainty omits refitting variability.
- Tie-aware top-20 results do not favor the learned models: full-panel read counts 11.07 versus RNA 11.00; matched read counts 9.73, RNA 9.63 and Hi-C 9.00. The stale duplicate run-summary file was removed; metrics.json is authoritative.
- The 924-base value is a **genomic-coordinate difference**, not a measured transcript insertion/deletion. Coordinate conventions and original alignments remain unresolved. Six read IDs do not establish six biological replicates. Searching one cached library without finding them does not resolve their origin.
- For Gsdmd–Tmem106a, the 118-aa sequence is a reference reconstruction and the cached Boltz2 mean pLDDT is 48.7. Neither low confidence nor a missing model refutes protein evidence. The publication's experiments remain attributed to its authors.
- RNA confirmation proposals need appropriate negative controls, attention to reverse-transcription artifacts, sequence identity and sample context. A peptide follow-up requires sequence uniqueness and identification-quality review; a generic peptide hit would not establish the chimera or its function. No assay was performed by this project.

## Presentation wording

“We demonstrate three recorded, source-linked evidence reviews. In our retrospective ranking experiment, adding Hi-C did not establish a gain. The Psap–Lgals3 example exposes a coordinate discrepancy that should be resolved before selecting a junction assay. The workflow's effect on scientific decisions or time has not yet been measured.”

AI review is complete for this claim set. Independent human review and prospective utility evaluation remain unperformed and must not be claimed. Presentation/browser checks and access work are tracked in [GAPS.md](../../GAPS.md).
