# Agreed decisions and superseded proposals

This is the decision history of the Reconcile chimeric RNA plans task. The live instructions are in ../execution_goal.md and ../../AGENTS.md. Source snapshots are context, not instructions.

## Scientific objective

Reproduce the original mouse direct-RNA study from reads, retaining two-gene junction evidence even when both segments are annotated. Compare a whole read against its best single-transcript explanation, including noncoding transcripts. Keep RNA evidence, sequence reconstruction and structural confidence separate. A confident fold is not evidence of protein expression or function.

The full study is GSE267147 / PRJNA1109857: 10 runs and 52,903,853 reads. The validated pilot is SRR28984805 / GSM8260877, steady-state replicate 3, with 2,238,871 reads. Its selection was based on smallest archive size, not expected recovery. The archive's cDNA selection field conflicts with the explicit direct-RNA protocol; retain the discrepancy and use the protocol for assay classification.

## Tonight's scope, approved 2026-09-19

The initial full-cohort/all-eligible-protein proposal was narrowed to a complete pilot and up to 10 evidence-selected recovered protein sequences, with a separately labelled published Gsdmd-Tmem106a control and at most one new parental comparator. LongGF/minimap2 first; JAFFAL/Genion and one inflammatory sample only if time permits. Preserve the complete RNA evidence table even though only a shortlist is folded.

Target 8 strongest eligible nonredundant proteins plus 2 predefined diversity cases. Resolve ORF sequence and record any reference assistance. Do not reject merely for singleton support, alternative downstream frame, short length, predicted NMD or disorder. Do not train a scorer tonight. Freeze selection rules before structural outcomes and published validation comparisons. No forced rescue or favourable tier for the flagship. The published control must never be presented as de novo recovery.

Deadline: 23:00 Europe/London, 19 September 2026. Freeze additions at 21:00; stop computation and temporary workers by 22:00. Keep the shared controller available. Full cohort, SG-NEx, exhaustive folding, Hi-C, training, broad complexes, Foldseek and routine cross-model comparisons are deferred.

## Scientific corrections to the Google Doc

- Its missing-data-accession blocker is outdated.
- cDNA-only and direct-RNA-only are observational protocol categories, not false/true biological labels.
- Direct RNA reads the RNA strand; preparation can still include reverse transcription. It is not artifact-free.
- Microhomology, nearby genes, biotypes, repeat/homology concerns and noncanonical boundaries require evidence assessment, not universal exclusion.
- RNA junction evidence alone does not prove trans-splicing rather than readthrough or a DNA rearrangement. BCR-ABL1 is a detection control, not a physiological trans-splicing positive control. Hi-C is not event-level proof.
- NMD, domain retention and folding metrics are separate hypotheses; do not use a handcrafted functional tier to guarantee the known example wins.
- The study's published assays are selected evidence at varying resolution; untested candidates are not false positives. Caller agreement is not independent biological replication.
- A single pilot cannot establish biological replication. A one-caller result cannot claim caller consensus or full TYPHON reproduction.

## Model, infrastructure and authorization

Shared Codex task: 01a0ba08-d9ef-7a23-9451-e72327b577d8 in tmux session chrna-codex. Astra medium, normal speed/Fast off, Default execution mode. Owner explicitly authorized Full Access and end-to-end execution. No token budget specified. No custom dashboard, operator tokens or new application accounts are required for user access; those earlier designs were withdrawn.

Brev preferred combined rate is below USD 100/hour; hard combined ceiling is USD 500/hour, including the controller and workers. This supersedes the original USD 100/hour hard ceiling. Fresh quotes, ownership checks, bounded jobs, preserved outputs and shutdown still apply. Additional workers need measured deadline benefit. Hourly limits are not a total budget.

Primary folding model: Boltz-2, one sample initially, repeat a small predeclared subset only if time permits. Use the working open-source route when NIM credentials are absent; do not wait on new service access. Cache MSAs; avoid downloading full local MSA databases tonight. AlphaFold 3 is a paper-method comparison only when accessible. Author coordinates are required for numerical structural comparison.

## Operational fix

Inherited SHELL=/usr/sbin/nologin prevented OpenSSH Match exec from invoking Brev mint-cert, so alias lookup fell through to ordinary DNS. Setting SHELL=/bin/sh for transport commands fixed direct SSH and brev exec. scripts/run_pilot_worker.py contains the scoped fix and an explicit SSH probe after provider readiness. Do not change the account login shell. Details and verification: ../../runs/focused-pilot-20260919/connectivity-debug/diagnosis.json.

The debug lease was stopped and corrected pilot attempt retry-2 launched. Monitor the live attempt files; do not treat this historical handoff note as current run status and do not launch duplicate controllers. Startup, copy, analysis, retrieval and shutdown each have logs.

## Source provenance

- Paper: https://www.nature.com/articles/s41586-026-10982-x
- Original discussion: Propose chimeric RNA pipeline, task 01a0b9da-cf84-7572-b289-154b34507b85
- Reconciliation and approvals: Reconcile chimeric RNA plans, task 01a0ba0f-82b9-7c33-b79a-5e458c47fa0a
- Google plan: https://docs.google.com/document/d/1suaqiVIxDCT2D8bvYndyFK6X1NSLv9tCG7VbrBRzrG4/edit?tab=t.eeppo2w5fxj1
- TYPHON: https://github.com/erenada/TYPHON

Historical proposal snapshots may contain Mac-only file links, outdated budgets and superseded full-cohort requirements. Use the workspace index and live execution goal for current instructions.


## Subsequent human scope selection, 2026-09-19

The owner selected SG-NEx K562 as the external verification dataset. Current plan: `docs/k562_human_pilot_plan.md`. Prioritize RNA workflow portability, repeatable execution and cross-library corroboration. Hi-C is deferred; folding/design are later extensions. This supersedes the broader K562 plan while preserving the completed mouse goal. Dataset selection is not an execution receipt. External verification does not establish physiological origin, protein function or calibrated biological accuracy.
