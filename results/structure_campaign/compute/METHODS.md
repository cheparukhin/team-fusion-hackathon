# Structure inference and artifact verification

The executed panel is a conditional reference-sequence sensitivity analysis. None of these full candidate proteins met the strict primary sequence-evidence gate. NanoString support is RNA-pair evidence; it neither validates the reconstructed complete ORF nor demonstrates protein production. The coordinator froze43 candidate sequences and eight controls, with12 candidate calibrators included in the43. `selection/` and `cohort/` retain the transcript hypotheses, sequence hashes, residue-origin mapping and eligibility assumptions.

## Protocols remain separate

`boltz2_2.2.1_single_sequence` is the newly executed protocol. Each YAML explicitly supplies `msa: empty`; no MSA server flag is used. Model weights and the prediction implementation run locally on the project-owned Brev GPU. Public ColabFold upload was automatically denied twice, and no sequence submission occurred. The coordinator requested explicit permission for that destination; inference proceeded using the authorized no-MSA alternative. Reduced alignment information can reduce prediction accuracy, so the single-sequence results must not be pooled with the cached precomputed-MSA reference.

`boltz2_2.2.1_precomputed` retains a single exact-sequence, exact-settings cached Gsdmd:Tmem106a118-aa model from the earlier project run. The other50 planned MSA-backed records remain not run. This is provenance context, not51 additional completed models. The newly predicted single-sequence Gsdmd model has a distinct protocol/job ID.

Both protocols use Boltz2 version2.2.1, three recycling steps,200 sampling steps, one diffusion sample, step scale1.5, and full PAE output. First-pass seed is20260919. Any approved diagnostic repeats use20260920 and20260921 and are reported as repeated models of existing peptides, not additional unique candidates. Weight/cache SHA256 checks and Torch/CUDA/kernel verification are in the exported environment manifest. No hosted NVIDIA NIM invocation occurred; no NIM credentials were available.

## Execution and calibration

A10080GB PCIe,12vCPU and approximately120GiB host RAM were quoted before resuming the project-owned instance `8mq2074bp`. Calibration ran12 candidates and eight controls serially, spanning32–2498aa. All20 passed sequence/structure/confidence checks on their first attempt. The711-aa model took57.50s and the2498-aa model401.85s; short models were approximately39–43s. These are observed process wall times, not speedup claims. GPU telemetry independently confirms actual utilization and sampled memory use. Long-input observations demonstrate why118-aa timing cannot forecast the full length distribution.

Continuation requires at least11/12 candidate calibrators verified; controls do not inflate that denominator. All candidate calibration outcomes must be terminal before continuation. Full continuation reuses those20 exact job IDs and executes the remaining31; no calibration models are recomputed. The continuation receipt records its runtime estimate against the remaining lease. Each new prediction has a bounded timeout and at most one retry; explicit CUDA out-of-memory errors suppress an identical retry. No failed sequence is cropped or silently replaced.

The lease began2026-09-20 09:21:11UTC and ends by11:21:11UTC, with600seconds reserved for final export and stop. A separate identity-checked watchdog enforces the deadline. The owned GPU is stopped after verified export; no existing instance is deleted. The quote is$1.98/hour. Preflight reservation and final elapsed-rate cleanup estimates are distinct from provider invoices.

## Verification and interpretation

Every successful model must have exactly one chain/model, exactly the frozen amino-acid sequence, one finite alpha carbon per residue, finite per-residue pLDDT in[0,1], and a finite nonnegative NxN PAE matrix. Confidence is exported on the0–100 scale, with positions1-based. Snapshot archives and individual artifact SHA256 values are checked after transfer, then coordinates and arrays are validated again locally. Failed, unavailable and unrun records retain missing metrics rather than zero confidence.

`jobs.json` records actual commands, attempts, time, settings, input hashes, protocol and artifact paths. `model_metrics.tsv` and `summary.json` retain a denominator per protocol. `residue_confidence.tsv`, `model.cif`, `plddt.npz`, `pae.npz` and `confidence.json` accompany each verified job. Atomic file replacement prevents readers from seeing a partially written ledger.

Structure cartoons use real predicted coordinates. Blue means residues encoded wholly by parent-A RNA; red means parent-B RNA or a split junction codon. This color is nucleotide origin, not a claim of canonical protein-domain identity. The detailed source classes preserve canonical, shifted-frame and other reconstruction annotations. A gallery asset is withheld if compatible ORF hypotheses disagree on those color boundaries. pLDDT is model confidence, not measured disorder, folding, biological function or druggability.

## Reproduction

Reusable drivers are `scripts/compute/structure_campaign_*.py`. Stage the frozen selection with `structure_campaign_stage.py stage --msa-mode single_sequence`; execute the bounded worker only on an owned, budgeted compatible GPU; export with `structure_campaign_export.py`; inspect `structure_campaign_runtime_report.py`; render sequence-audited coordinates with `structure_campaign_render.py`. `executed_remote_setup.sh`, `executed_continuation.sh` and subsequent diagnostic receipts preserve the actual commands. The stop driver revalidates the aggregate local artifacts, checks the exact owned instance ID and records confirmed shutdown and watchdog cancellation.

## Completed outcome

All 51 first-pass models and 16 additional diagnostic seed models passed verification. The complete first-pass export remains byte-identical after diagnostic inference. Final model and confidence ledgers are frozen under `ledger_freeze.json`; the prior MSA reference remains a separate protocol. All artifacts were verified before the owned GPU was confirmed stopped at2026-09-20 10:26:51UTC and its watchdog cancelled. The65.66-minute lease has a $2.1669 elapsed-rate GPU-instance estimate; the conservative shared allocation bound remains $106.78/$150, including the separate cross-species task. Actual provider invoices and unquoted storage/egress are not reconciled. `campaign_receipt.json` and `cleanup_receipt.json` contain the machine-readable final records.
