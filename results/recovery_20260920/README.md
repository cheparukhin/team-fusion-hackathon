# Recovery validation records — 20 September 2026

This directory retains the audit receipts from the earlier recovery. Its
separate `snapshot/` source tree has been consolidated into the existing
repository and removed. Use these current locations:

- [Structure/disorder source](../../scripts/structure_campaign/README.md) and
  [campaign results](../structure_campaign/RESULTS.md).
- [Cross-species source and comparison](../../workflows/cross-species/README.md).
- [Large evidence files and safe restore command](../../preservation/controller-20260920/README.md).

The original receipts preserve what was checked at that time: 188 conditional
annotated-start peptide hypotheses; 68 verified model jobs; saved disorder,
domain, diversity and partial human/cow comparison outputs. The later controller
integration rechecked all 68 model jobs and retained the newer report renderer
and assets. Prediction consistency does not establish translation or function.
The separate frozen [383-model folding supplement](../folding_expansion/README.md)
remains unchanged; do not pool distinct protocols or counts.

The historical `file_dispositions.tsv` and JSON receipts refer to original
`quick_hack`/snapshot paths and the older local archive. They are audit records,
not the current restore manifest. Current canonical paths, exclusions, checksums,
and verification are maintained in
[`preservation/controller-20260920/`](../../preservation/controller-20260920/README.md).
