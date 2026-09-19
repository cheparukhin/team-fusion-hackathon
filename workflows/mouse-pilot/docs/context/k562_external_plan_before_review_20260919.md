# SG-NEx K562 external verification run

Owner selection recorded on 2026-09-19 in the master task. Status: dataset and scope selected; no K562 execution is claimed by this planning update. The previous broader plan is archived at `docs/context/k562_integrated_plan_before_scope_revision_20260919.md`; its mandatory Hi-C/structure deliverables are superseded.

## Objective

Apply the completed mouse RNA discovery, assessment and ranking workflow to independent human SG-NEx K562 data. Demonstrate repeatable execution and workflow portability, and measure exact-junction corroboration across independently documented RNA libraries.

This is external workflow verification, not direct reproduction of the paper's human macrophage dataset or proof of biological accuracy. K562 is a cancer cell line. Credible chimeric RNA does not establish normal physiological occurrence, trans-splicing, translation or function. Preserve the completed mouse outputs, freezes and held-out partition.

## Selected scope

Required: source/reference intake, human parameterization, method freeze, two-library direct-RNA discovery and assessment, independent RNA corroboration, a BCR–ABL1 control trace, rerun consistency checks, and an evidence report.

Deferred: Hi-C downloads/analysis/heatmaps, full WGS processing, extra callers, model training, protein folding, binder/molecule generation and forced nomination of an RNA-only candidate. ORF reconstruction and bounded processed-SV annotation may follow the RNA deliverable. They do not block this external verification milestone.

## Proposed input panel

| Role | SG-NEx sample alias |
| --- | --- |
| Primary discovery | `SGNex_K562_directRNA_replicate4_run1` |
| Separately processed corroboration | `SGNex_K562_directRNA_replicate5_run1` |
| Orthogonal RNA evidence | `SGNex_K562_Illumina_replicate4_run1` |

These aliases were checked in the public manifests during planning. Freeze actual files after verifying specimen relationships, general QC, integrity and sizes. Different replicate labels alone do not prove biological independence; matching numbers across protocols do not establish matched aliquots. Replace samples only on metadata/QC grounds before candidate inspection. Do not expand sampling to rescue a preferred fusion.

Sources: [SG-NEx](https://github.com/GoekeLab/sg-nex-data), [Nanopore manifest](https://raw.githubusercontent.com/GoekeLab/sg-nex-data/master/docs/samples.tsv), [Illumina manifest](https://raw.githubusercontent.com/GoekeLab/sg-nex-data/master/docs/illumina_samples.tsv).

Record manifest revision, original rows, URLs, checksums, bytes, kit/basecalling history, protocol, library/specimen IDs and matching status. Namespace read IDs with duplicate-read crosswalks. Technical runs, multiple alignments and callers observing the same read cannot create independent molecules or biological replicates.

Use internally compatible human genome/GTF/transcript references, with GENCODE 43 / GRCh38.p13 as the intended paper-aligned choice subject to file/contig validation. Freeze exact hashes. Reuse BAMs only if reference compatibility, sequence content and necessary alternative alignments are preserved; otherwise realign FASTQ. Do not download the full SG-NEx collection or raw signal archives.

## Implementation and freeze

The current mouse code contains fixed reference/sample IDs in `src/chrna/pilot_assessment.py`, fixed worker inputs in `scripts/run_pilot_worker.py`, and fixed workflow paths. Parameterize references, species, sample/library/specimen metadata and output root before human execution. Proposed new paths are `workflow/k562/config.yaml` and `runs/k562-pilot/<run-id>/`; these are implementation targets, not existing commands.

Reuse minimap2 + LongGF and the mouse assessment rules where applicable. Record every human/protocol adaptation. Keep the inherited RNA ranking as the primary portability output; new cross-library and Illumina evidence appear separately. Any changed ranking receives a separate method version and cannot be called the unchanged mouse method.

Freeze source/environment hashes, thresholds, deduplication, coordinates and matching rules before inspecting candidate or control outcomes. Preserve the first run if changes become necessary. Never tune thresholds to rescue BCR–ABL1. An alignment scan is not an independent caller.

Preserve ordered parents, stable identifiers, zero-based interbase boundaries, original/normalized coordinates, uncertainty and sequence hashes. Compare split explanations with coding/noncoding transcripts, paralogs, pseudogenes and repeats. Preserve alternatives and exclusion reasons. Singletons and absent corroboration are not biological negatives. Mouse NanoString outcomes must never become human labels or ranking features.

## What verification measures

1. **Repeatable execution:** rerun a bounded deterministic fixture using identical inputs/configuration; compare normalized scientific outputs, excluding timestamps/paths. Record deviations.
2. **External execution:** account for all selected reads, proposed junctions, exclusions, unresolved cases and deferrals. A small timing subset is not complete-library processing.
3. **Cross-library corroboration:** process direct-RNA libraries separately. Report exact-junction intersection, union and directional recovery with explicit denominators and support/mapping strata. These measure recurrence, not sensitivity against an exhaustive truth set.
4. **Orthogonal corroboration:** prespecify the Illumina alignment/junction-check method and unique-anchor requirements. Separate exact split reads from discordant pairs. Keep this evidence out of the inherited ranker; if used for selection, do not reuse it as independent evaluation of that selection.
5. **BCR–ABL1 control:** trace actual reads, junction and isoform through every stage. It is a DNA-derived fusion detection control. Failure limits claims of successful detection verification and needs diagnosis; never substitute a published sequence for recovery.
6. **Artifact controls:** positively explained empirical artifacts where available; synthetic fixtures test software only. Keep RNAEvidence, ArtifactRisk and Decision separate.

No held-out mouse evaluation or calibrated authenticity/protein-function claim is part of this run.

## Delivery and compute

Sequence: metadata/reference/size preflight → parameterization and mouse regression → method freeze → CPU discovery/assessment → independent RNA corroboration → rerun checks → report and preserved artifacts.

Before production record bytes/disk needs, measured throughput, runtime caps and forecast cost. Check live resources/leases to avoid duplicate controllers. Start on CPU. Launch only bounded useful workers under fresh verified prices; preferred combined project rate below USD 100/hour, hard ceiling USD 500/hour including controller and attached charges. Unknown prices fail closed. Preserve outputs and stop owned temporary workers after success or failure. The old mouse deadline does not transfer to this run.

After analytical changes run meaningful reference/coordinate/provenance/deduplication/outcome-exclusion tests, mouse regression checks, applicable tests, `chrna build` and development-only `chrna benchmark`. Keep shared genes and duplicate sequences together in any later model split.

Required artifacts: pinned manifests/configuration/environment; commands and run receipts; per-library QC; junction/read evidence tables; inherited ranking and complete decisions; corroboration results; BCR–ABL1 trace; rerun comparison; evidence report/dashboard export; resource/shutdown records; limitations and completion audit.

Hi-C is DEFERRED / NOT ASSESSED, never zero or negative evidence. Keep human outputs, previous mouse results and fictional dashboard examples separate. Missing required processing means incomplete execution, not an empty biological result.

Presentation claim, conditional on actual results: “We applied the documented mouse RNA-evidence workflow to independent human K562 data and measured repeatability of execution and cross-library junction corroboration.” Counts and control recovery must come from saved outputs.
