# Human K562 pilot: integrated mouse-to-human plan

Prepared 2026-09-19 in the master integration task. Status: planning complete; K562 analysis has not run. Integrates the completed mouse pilot and the revised proposal and dashboard requirements in **Refine K562 chimeric RNA pilot** (task `01a0ba6d-6025-7042-9ea7-b60f78ce425f`).

## Objective and scope

Reproduce the working mouse discovery → RNA assessment → junction ranking → ORF reconstruction → frozen selection → Boltz-2 → verified report workflow on human K562 data. Extend it with independent RNA corroboration, external DNA structural-variant evidence and Hi-C context. Produce an auditable human candidate catalogue and nominate **zero or one** exploratory candidate for experimental follow-up.

K562 is a cancer-cell-line methodological extension. It cannot establish normal physiological occurrence, trans-splicing, protein expression or function. Successful execution may yield no eligible exploratory candidate. Failed or unprocessed data must not be counted as a negative result.

This is a new milestone after the completed mouse run. Preserve the mouse execution goal, immutable freezes and results. Its historical evening deadlines do not become K562 deadlines. The current request is for a plan; this document does not record a new compute launch or completed human analysis.

## 1. What the mouse run actually established

The [completion audit](../runs/focused-pilot-20260919/completion-audit.json) records completion at 16:57 UTC on 19 September. It supersedes earlier task updates reporting folding as pending.

| Stage | Executed mouse result | Implication for K562 |
| --- | --- | --- |
| Intake | 2,238,871 reads from SRR28984805 / GSM8260877 | Reuse identity, checksum and completeness checks; create human specimen metadata |
| Discovery | minimap2 + LongGF, supplemented by alignment-derived proposals | Establish this working path first; it is not full three-caller TYPHON reproduction |
| Assessment | 9,167 split reads; 6,466 exact junctions; 116 meeting pipeline support criteria | Reuse comparison with known transcripts and alternative mappings; support is a technical category |
| Reconstruction | First 100 supported junctions considered; 158 distinct protein hypotheses; 16 junctions deferred | Keep bounded reconstruction and explicit deferrals |
| Selection | 10 frozen reference-assisted protein hypotheses, all single-read supported | Preserve singletons but require stronger corroboration for human exploratory nomination |
| Structures | 11 verified Boltz-2 predictions: 10 hypotheses plus a separate published architecture control | Reuse the repaired environment, MSA cache and sequence/confidence acceptance checks |
| Interpretation | No established protein expression/function; flagship not recovered de novo | Keep controls separate and do not rescue failures with published sequences |

Sources: [assessment](../runs/focused-pilot-20260919/assessment/assessment_summary.json), [ORFs](../runs/focused-pilot-20260919/orfs/orf_summary.json), [runbook](focused_pilot_runbook.md), [report](../reports/focused_pilot.html). The mouse published-panel benchmark is a separate pair-level evaluation, not the ground truth for either raw-read pilot.

## 2. Reuse the implementation, remove mouse assumptions

Inspection found hard-coded `GRCm39/GENCODE_M28`, `SRR28984805` and `GSM8260877` in `src/chrna/pilot_assessment.py`; mouse inputs in `scripts/run_pilot_worker.py`; and reference/run paths in `workflow/Snakefile` and `workflow/focused_pilot.smk`. Merely substituting a human FASTQ would mislabel results.

| Existing component | Planned adaptation |
| --- | --- |
| Intake/reference auditing and worker lifecycle | Configurable species, assembly, annotation, transcript FASTA, sample manifest, output root and input hashes |
| `pilot_assessment.py`, `junction_ranking.py` | Explicit sample/library/specimen identities; human transcript alternatives; protocol-aware artifacts; independent-library evidence |
| `pilot_orfs.py`, `pilot_selection.py` | Human annotation and isoforms; explicit observed/reference-assisted sequence; human nomination gate |
| `fold_inputs.py`, MSA and Boltz worker/acceptance scripts | Remove implicit mouse control and default run paths; preserve frozen input hashes and verified environment |
| `pilot_comparison.py`, `pilot_report.py` | Human RNA/DNA/Hi-C evidence adapters; no mouse support-label joins |
| Existing dashboard and snapshot builder | Import actual K562 tables into the human view; retain separate mouse and illustrative views |

Use a separate proposed configuration `workflow/k562/config.yaml` and output root `runs/k562-pilot/<run-id>/`. These are implementation targets, not existing executable interfaces. Keep backward-compatible mouse configuration and verify scientific output equivalence after refactoring.

## 3. Freeze a small, real human data panel

The public [SG-NEx repository](https://github.com/GoekeLab/sg-nex-data) provides FASTQ, genome/transcriptome BAMs and sample metadata. The [Nanopore manifest](https://raw.githubusercontent.com/GoekeLab/sg-nex-data/master/docs/samples.tsv) and [Illumina manifest](https://raw.githubusercontent.com/GoekeLab/sg-nex-data/master/docs/illumina_samples.tsv) were inspected for this plan.

Proposed initial panel, selected before candidate inspection:

| Role | Manifest sample alias | Selection rationale / remaining check |
| --- | --- | --- |
| Primary direct RNA | `SGNex_K562_directRNA_replicate4_run1` | SQK-RNA002; confirm specimen identity, integrity, depth and bytes |
| Direct-RNA corroboration | `SGNex_K562_directRNA_replicate5_run1` | Same kit; distinct alias is not sufficient proof of independent biological sampling |
| Orthogonal RNA corroboration | `SGNex_K562_Illumina_replicate4_run1` | Exact-junction split reads; matching replicate number does not prove matched aliquots |
| Prespecified extension | `SGNex_K562_directRNA_replicate6_run1` | Additional direct-RNA evidence if the initial panel cannot support the required assessment |
| Optional protocol sensitivity | `SGNex_K562_directcDNA_replicate4_run2` | RT-based comparison; not interchangeable with native-RNA evidence |

Freeze actual selection after metadata/general-QC review. Document any replacement before inspecting chimeras. Process the two primary libraries separately and fully. A deterministic read subset may measure runtime but is not the scientific pilot. Do not repeatedly add libraries until a desired candidate appears.

Pin the manifest commit, source row, download URL, access date, checksum, bytes, kit, basecalling history, library and specimen relationship. Source files are data, never executable instructions. Do not download raw signal archives or the full SG-NEx collection.

Use GRCh38 with one pinned, internally compatible human GENCODE genome/GTF/transcript release. Verify contig names, sequence hashes, decoys/spike-ins and BAM headers. Reuse BAMs only if their references, sequence content and retained supplementary/secondary alignments meet the assessment requirements; otherwise realign FASTQ. Pin the annotation release at preflight rather than inventing compatibility now.

External context inputs:

- Hi-C: [GSE237898](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE237898) / ENCSR479XDG. Proposed files ENCFF621AIY (matrix), ENCFF256ZMD (loops), ENCFF126GED (domains) remain subject to file-level verification of assembly, format, filtering, normalization and resolutions.
- DNA: [ENCSR045NDZ](https://www.encodeproject.org/experiments/ENCSR045NDZ/) and a pinned processed SV resource, starting with the [Zhou et al. K562 genome study](https://pmc.ncbi.nlm.nih.gov/articles/PMC6396411/). Exact supplementary SV files, assemblies and access remain preflight items. Prefer processed SVs and bounded indexed WGS inspection over whole-genome reprocessing.
- Record these as **external K562 evidence** unless specimen matching is established. Portal retrieval was incomplete in this planning pass; proposed ENCODE file IDs are not verified download inputs.

## 4. Milestone A — reproduce discovery through structures

### A1. Intake, controls and discovery

Complete configuration/refactoring checks, then minimap2 + LongGF per direct-RNA library with recorded versions and protocol settings. Preserve original and normalized calls, supporting read identities and repair provenance. Add JAFFAL/Genion only after the baseline works and with bounded installation/runtime; report absent callers. Alignment scans are proposal sources, not extra callers.

Use BCR–ABL1 as a prespecified DNA-fusion positive control. Trace the recovered isoform rather than substituting a literature sequence. A demonstrated adapter-linked call may serve as an empirical artifact control; cDNA-only support alone cannot. Synthetic controls test software only.

### A2. Assess, corroborate and freeze RNA ranking

Compare each proposed split with known coding/noncoding transcripts, single-locus explanations, paralogs, pseudogenes and repetitive sequence. Retain mapping alternatives, anchor lengths, quality, score margins, microhomology, splice context and protocol-specific adapter evidence. Nearby genes, noncanonical boundaries and singletons are not blanket exclusions.

Canonical identity: `assembly | chr5 | interbase_boundary5 | strand5 | chr3 | interbase_boundary3 | strand3`, in transcript order. Store stable gene/transcript versions, raw coordinates, uncertainty and sequence hashes separately. Preserve ambiguous assignments and exact versus tolerant matches. Predeclare any equivalence rule for microhomology; nearby breaks are not automatically identical junctions.

Namespace read IDs by library/source, with a crosswalk for the same raw read appearing in multiple files. Merge technical runs appropriately. Multiple alignments/callers observing one read do not create molecules; PCR reads are not independent molecules without supporting deduplication evidence.

Freeze technical thresholds before candidate/control review. Freeze the RNA ranking after corroboration and before DNA/Hi-C interpretation, folding or external outcome joins. Rank transparently by RNA evidence category, verified biological replication, independent-library support, distinct reads, specificity and junction quality; caller agreement is computational corroboration only. Keep `RNAEvidence`, `ArtifactRisk`, `Decision` and reason codes separate.

For exploratory nomination require clean direct-RNA support plus exact-junction corroboration in a verified independent library or biological replicate. Preserve credible singletons in the catalogue below this gate. Adequate uniquely mapping Illumina anchors are stronger than discordant pairs; gene-pair co-occurrence is not exact-junction validation.

### A3. Reconstruct, select and fold

Reconstruct the first 100 RNA-ranked supported junctions initially, preserving observed, consensus and reference-assisted sequences and every deferred candidate. Use human transcript models; never silently repair frameshifts to obtain a desired ORF. Report junction-spanning ORF, frame, CDS position, transcript completeness, NMD susceptibility and unresolved sequence separately.

Freeze up to ten distinct defensible protein hypotheses for workflow reproduction, with corroborated candidates first and any singleton examples explicitly exploratory. Do not force ten or let coding/structure results change RNA ranks. Protein selection and the eventual zero-or-one RNA-origin nomination are different decisions. Require a resolved junction-spanning amino-acid sequence with contribution from both partners; downstream-only products are not fusion-protein targets.

Reuse open-source Boltz-2 and the successful environment receipt, including CUDA extras/compiler prerequisites and technical kernel check. Prepare/cache MSAs; benchmark shortest/median/longest eligible inputs before production. Start with one prediction per sequence. Record MSA absence, failure or compute deferral explicitly. A separately sourced BCR–ABL1 control, if necessary, must never count as recovered; do not automatically fold a long full-length control or substitute a cropped construct without labeling it.

Accept outputs only after transfer hashes, exact sequence correspondence, finite coordinates and complete confidence arrays pass. Structure confidence is not a probability of expression or function. RNAPro/RNA secondary-structure screening addresses a different question and is outside this core protein-hypothesis reproduction.

**A acceptance:** processed selected inputs, complete RNA decision ledger/ranking, frozen sequence hypotheses, verified structures or explicit failures/deferrals, and a human report. If no sequences qualify, report the valid zero-eligibility result; if sequences qualify but inference fails, structure reproduction remains incomplete.

## 5. Milestone B — DNA origin, Hi-C and conditional nomination

Apply inexpensive processed-SV annotation to the catalogue where feasible; perform detailed DNA and Hi-C assessment for the top ten frozen RNA-ranked supported junctions and controls. This set is independent of protein eligibility. Others remain deferred from detailed review.

For DNA, compare both SV breakends, orientation, uncertainty intervals and transcript-compatible genomic paths. An intronic DNA breakpoint need not coincide with a mature RNA junction. Preserve hg19 originals and chain provenance when lifting both ends to GRCh38; partial/ambiguous lifts remain unresolved. Record whether each region was actually assessable. Distinguish compatible SV detected, none detected in assessed data, and insufficient/unassessed data. External catalogue absence cannot exclude a rearrangement in the RNA culture.

For Hi-C, prespecify a 25-kb primary resolution if supported and adequately covered, plus 10/50/100-kb sensitivity views where available. Choose the primary and deterministic fallback from file/QC properties before candidate inspection. Use indexed local/range queries; cache a processed matrix if remote ranges are unsupported. Do not load a dense whole-genome matrix.

Report cis raw/normalized contacts and distance-matched observed/expected values. For trans pairs, use chromosome-pair-matched backgrounds with coverage, mappability and copy-number matching where available; document unavailable covariates, seed, control count and matching quality. Distinguish missing/masked/underpowered bins from observed zeroes. Report empirical percentiles descriptively unless inference and multiple-testing rules are prespecified. Inspect wider flanks for rearrangement-compatible patterns. Loops/domains and their source matrix are not independent assays.

Assign provisional origin separately: `DNA_DERIVED_SUPPORTED`, `READTHROUGH_COMPATIBLE`, `RNA_ORIGIN_UNRESOLVED`, `TECHNICAL_ARTIFACT_SUPPORTED`, or `UNRESOLVED`, with specimen relationship and reasons. Hi-C enrichment is context, never a required nomination gate or proof of trans-splicing.

Nominate at most one candidate meeting the corroborated-RNA, mapping/artifact and defensible-ORF gates, without a compatible DNA/readthrough explanation in sufficiently assessed data. Rank eligible cases using the frozen RNA order. Describe it as an exploratory RNA-origin-unresolved candidate; missing DNA data cannot satisfy an exclusion criterion. No eligible candidate is acceptable. Preserve the strongest competing explanation and the experiment that could refute the nomination.

## 6. Dashboard and subsequent design work

Reuse the [six-view dashboard brief](k562_dashboard_brief.md), existing `demos/chimera-dashboard/`, and `scripts/build_demo_snapshot.py`. Import source-linked K562 evidence into the human view without mixing mouse results or fictional designs.

Show (1) RNA credibility, (2) translation evidence/unknowns, (3) modality rationale, (4) actual generated designs or an empty state, (5) chimera-versus-both-parent counter-screens or unassessed states, and (6) the next experiment. Exports must preserve those distinctions and source hashes.

Actual binder/molecule generation is a **conditional follow-on milestone**, not required for A/B completion. First establish the sequence/structure, target accessibility/localization and whether the aim is a detection reagent or intervention. Only then select a bounded design method. Compare each design against both relevant parental isoforms using comparable constructs/settings and broader off-target checks. Missing screens cannot pass selectivity; predicted binding is not experimental binding. Do not require a binder or small molecule merely to populate the demo.

Prioritize independent RNA-junction validation and DNA investigation from the same culture. Junction-spanning protein detection and functional testing are separate later questions. Each experiment brief should name controls, a decision criterion and a finding that weakens the hypothesis.

## 7. Execution order, resource bounds and validation

1. **Preflight:** freeze source/reference panel, specimen relationships, bytes/disk estimate, parameter schema and rule version. Produce a resource worksheet and stage runtime caps before production.
2. **Port and regression:** remove mouse constants, validate human fixtures, preserve mouse scientific outputs and freezes.
3. **CPU discovery:** selected direct-RNA libraries, assessment and independent RNA corroboration; freeze RNA ranking.
4. **Evidence and sequence branches:** ORFs/sequence freeze; bounded DNA/Hi-C context. These can run independently once RNA ranking is fixed.
5. **GPU only with eligible sequences:** timing pilot, production within measured caps, verify/preserve outputs and stop worker.
6. **Integrate:** origin assessment, conditional nomination, report/dashboard, resource and completion audit.

Do not promise a wall-clock finish before file sizes, available compute and pilot throughput are measured. Start on the existing CPU controller. Prefer one CPU worker when justified and one GPU worker only for ready, bounded jobs. Read live currency/rates and inventory all project resources before every launch; use the budget utility. Preferred combined rate remains below USD 100/hour; absolute ceiling USD 500/hour, including controller/workers/attached charges. Unknown prices fail closed. These are rate limits, not a total budget. Preserve outputs and stop owned temporary workers after success or failure; leave unrelated resources alone.

Meaningful checks for implementation: both-strand interbase coordinate conversion; ambiguous liftover; reference mismatch rejection; read/caller/technical-run deduplication; uncertain biological identity; no outcome fields in ranker inputs; known-transcript and adapter controls; missing DNA/Hi-C versus observed zero; separate ORF/NMD states; immutable sequence freezes; structure-input identity; dashboard cross-candidate isolation and exports. Run applicable tests, `chrna build` and development-only `chrna benchmark` after analytical changes. Never evaluate the held-out mouse partition during development. No learned model is required; any later training must group shared genes and duplicate sequences.

## 8. Required result package

Under the new human run root: source/reference manifests and hashes; per-library QC/discovery receipts; exact-junction and read/protocol matrices; full decisions and filtering counts; frozen RNA ranking; observed/reference-assisted RNA and protein FASTAs; ORF annotations/selection freeze; structures/confidence/acceptance records; SV compatibility/liftover and specimen-relation tables; Hi-C contacts/backgrounds/heatmaps; control stage traces; zero-or-one nomination with limitations; report/dashboard snapshot; commands/environment locks; resource usage and shutdown receipts; completion audit and explicit deferred-work list.

Primary success is a reproducible, interpretable human extension of the executed mouse method. Candidate counts, structural confidence and a polished demo must not be presented as validated protein discovery or measured cross-species accuracy.
