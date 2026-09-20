# quick_hack recovery and reconciliation — 20 September 2026

Recovered **2,303 files (683,924,307 bytes)** from `/home/ubuntu/workspace/quick_hack` on `chrna-controller`, preserving source bytes and paths. Compared with canonical main `daa9130a1b437f970083df9c76ea7a9355c98f8e`: **292 identical files, 44 differing files retained only in the recovery archive, and 1,967 files absent from main**. This change adds 134 selected source files (11.7 MB) under `snapshot/`, plus verification and disposition records. It does not replace current submission results.

The integration owner confirmed no Git operations were in flight and endorsed a separate isolated PR. Source HEAD was `60a046b94294b324ba39f9cc9dc5a1c0d7a47057`, with tracked changes to README, the original plan and `.gitignore`. The controller was accessible without restart. All comparison, hashing, validation, testing and compression ran locally. No new worker, analysis run, inference job or infrastructure restart was requested or performed.

## Contribution dispositions

Paths in the source column are relative to `/home/ubuntu/workspace/quick_hack/`. The [file-level manifest](file_dispositions.tsv) gives every recovered source path, SHA-256, byte count, destination and disposition.

| Contribution / source | Destination and disposition | Checks and limits |
| --- | --- | --- |
| Published-panel reconstruction, classifier, Hi-C, original compute / `results/{dataset_reconstruction,classifier,hic,compute}` | Exact duplicates remain at existing canonical paths; different files remain in the local archive | 292 exact file matches across the recovered tree. Current tie-aware metrics and reviewed claims are retained. Old classifier metrics/model card must not replace them. |
| Structure reconstruction / `scripts/structure_campaign`, `tests/test_structure_campaign_*`, `results/structure_campaign/cohort` | Selected original code, tests, sequence tables and methods in `snapshot/` | 19 focused tests passed; original 3,345 campaign checks replayed successfully. 188 conditional annotated-start sequences agree exactly with the corresponding sequences in the frozen expansion census. Zero strict observed-full-chain primary peptides remains an evidence limitation. |
| Disorder/domain analysis / `results/structure_campaign/{analysis,domains}` | Summary/evidence tables and provenance in `snapshot/`; full score profiles, maps and supplementary inputs in archive | Saved sequence/score arithmetic verified: 42/188 V3 and 18/188 V1 predominantly-disordered hypotheses. No new disorder inference or Pfam search. These are conditional sequence predictions, not measured protein prevalence. |
| Folding / `results/structure_campaign/compute` | Original combined ledger, summary and methods in `snapshot/`; full coordinates/confidence arrays and per-run exports in archive | Independently verified all 68 successful model records: 67 single-sequence jobs across 51 sequences (43 candidates, 8 controls; 16 extra seed jobs), plus one reused MSA-backed model. Saved hashes, coordinate sequence, finite alpha carbons, pLDDT/PAE shapes/ranges and saved confidence summaries passed. |
| Structural diversity and robustness / `results/structure_campaign/{diversity,analysis}` | Original tables/methods in `snapshot/`; intermediate snapshots in archive | Saved provenance hashes passed. Qualified-span result is 2/43 candidates, 7 spans, 2 candidate-containing clusters; 41/43 remain unclassified. Foldseek itself was not rerun; this is not an independent confirmation of the structural clustering algorithm or a population diversity estimate. |
| Figures, searchable atlas and gallery / `results/structure_campaign/{figures,report}` | Preserved intact among recovered archive files | Historical report/figures retained, not promoted into the current submission. No fresh visual/browser validation. Open `quick_hack/results/structure_campaign/report/index.html` after extracting the archive. |
| Partial cross-species liver workflow / `cross-species/{scripts,tests,manifest,comparison,per_species,qc}` | Selected methods, metadata, native read evidence and comparison tables in `snapshot/cross-species`; other recovered evidence in archive | Ordered-pair tests: 2 passed. Both comparison scripts replayed locally against recovered orthology and gene-name tables; all five comparison output files matched byte-for-byte. Primary tier: 25 human / 153 cow ordered pairs, 0 shared, 19 human pairs mappable for both parents. One run per species; no homologous-junction conservation or replicated species-level absence established. |
| Older README, plans, demo, policies and presentation variants | Originals retained in archive; current main retained | 44 differing same-path files were not overwritten. Old policies, in-progress statuses, arbitrary top-20 tie handling, earlier slides and old protocol-only summaries are historical, not current instructions/results. |
| Existing `animation/` | Original recovered assets in archive; identical files left in main | No animation edits; author ownership preserved. |

## Relationship to the reviewed folding supplement

The [current 383-model supplement](../folding_expansion/README.md) remains unchanged: 341 candidate models across 223 RNA pairs, 42 controls, 117 missing predictions, 34 matched fragment comparisons. Its frozen reconstruction contains all **188** supported-cohort conditional sequences recovered here. Its `scripts/recovery_prepare.py` explicitly excludes `reported=True` hypotheses from expansion selection. Thus **zero of the recovered 51 single-sequence sequences overlaps the 383 completed expansion models**, and no model coordinate file is an exact duplicate of an expansion coordinate file.

This is complementary selected work, not a contradictory census. Do not add RNA pairs, unique peptide hypotheses, controls and repeated-seed model records as if they were the same unit. Keep per-peptide seed protocol and expansion batch-of-eight RNG protocol separate; do not pool confidence distributions or infer translation/function. The older audit's statement that no completed cross-species study was found is superseded only by this **partial comparison**, not by a completed conservation study. Its early structure execution snapshot is superseded by the later protocol-separated ledger recovered here.

## Preservation and reproduction

- [Archive receipt](archive.json): `quick-hack-recovery-20260920.tar.gz` is a local deliverable, **not uploaded to GitHub**. The archive preserves the recovered source files; the compact PR snapshot is intentionally incomplete. Large arrays, coordinates, figures, complete report assets and intermediate snapshots are available in that archive. Original scripts can refer to omitted files or historical absolute paths; original documentation links resolve only where the corresponding files were recovered.
- [File dispositions](file_dispositions.tsv), [inventory summary](inventory_summary.json), [model validation and overlap](model-validation.json), [campaign checks](campaign-validation.json), [independent recovery validation](recovery-validation.json), [additional checks](checks.json), [pinned verification environment](verification-requirements.txt).
- Install the recorded verification requirements in an isolated local environment. After extracting the archive, run from this repository:

```sh
python scripts/recovery/verify_quick_hack.py --snapshot /path/to/extracted/quick_hack
python -m pytest -q -o addopts= results/recovery_20260920/snapshot/tests/test_structure_campaign_*.py
python results/recovery_20260920/snapshot/cross-species/tests/test_pair_comparison.py
```

The verifier only reads saved artifacts; it performs no network operations, inference or provisioning. The campaign validation receipt came from the recovered original validator, with only its output destination redirected to preserve the original receipt. Reconstructing raw-read calls, refolding or downloading large reference databases is outside this recovery.

## Unresolved evidence and recovery limits

This was a bounded, non-atomic transfer, not a whole-workspace backup. It excluded `.git`, environments, caches, raw data/reference directories, software/tool trees, logs, compressed archives, sequencing BAM/FASTQ/HDF5 and individual files over 30 MB. Three exact orthology/gene-name files (47.5 MB total) and the 52.1 MB residue map were separately recovered to support verification. Some smaller files from an interrupted initial transfer remain in the archive and have explicit hashes/dispositions; they are not promoted into the PR. Five transient Foldseek `tmp/latest` symlinks were skipped. Source references and raw reads needed for a full biological rerun are not all present.

A recursive stability recheck was rejected by automatic approval review as too broad for controller policy. A subsequently approved bounded check of three key manifest files confirmed matching sizes and modification times, and the source commit remained unchanged. Internal artifact hashes passed; there is no claim that every source file was unchanged throughout transfer. No remote bulk hashing or compression was performed.

The reference-adapter test could not run locally because `samtools` is unavailable; LongGF synthetic controls and complete raw-read pipelines were not rerun. This does not invalidate the reproduced saved comparison, but caller correctness and original read reconstruction remain independently unverified here. Dog donor/tissue conflicts, rat metadata discrepancies, missing species/callers, biological replication and homologous exon-junction mapping remain unresolved.

The known exact fallback-launcher path was absent when checked. That is **not** confirmation that every deferred launcher/process was cancelled. No controller recovery or restart is authorized by this report. Sequencing/full-mouse and K562 reconciliation are outside this quick_hack recovery; existing task owners retain those handoffs.
