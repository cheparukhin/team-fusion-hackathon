# SG-NEx K562 external verification run — reviewed plan

Owner selected SG-NEx K562 on 2026-09-19. Review status: scientifically scoped; implementation and data preflight remain outstanding. No human analysis or provisioning was executed for this review. This version supersedes the previous plan, preserved in `docs/context/k562_external_plan_before_review_20260919.md`. The older broad Hi-C/structure plan is historical.

## 1. Outcome and limits

Apply the existing mouse RNA discovery/assessment workflow to external human data, demonstrate repeatable computation, and measure exact-junction corroboration across independently processed libraries. These are three separate outcomes. Cross-species portability is not direct reproduction of the paper's human macrophage results, calibrated authenticity prediction, or evidence of translation/function.

K562 is a cancer cell line with DNA-derived fusion possibilities. Keep origin unresolved unless actually assessed. BCR–ABL1 is a prespecified DNA-fusion detection control, not a physiological trans-splicing control. There is no required novel candidate count or mandatory RNA-only nomination.

Preserve mouse outputs, freezes and held-out data. The historical mouse execution deadline does not apply to this new milestone. This run is separate from PROJECT_PLAN's retrospective mouse classifier experiment; no classifier training or held-out mouse evaluation is part of K562 verification.

## 2. Deliver in two checkpoints

**A — first deliverable:** two complete direct-RNA libraries, separately processed; frozen primary-library ranking; exact-junction recurrence; control traces; real-read rerun consistency; candidate evidence report. This establishes external execution and measures within-protocol corroboration.

**B — planned corroboration extension:** one complete paired-end Illumina library, independently aligned and compared with frozen long-read candidates. Adds cross-protocol evidence. Report A and B completion separately: completing A alone does not mean Illumina corroboration has been performed.

Direct-cDNA and PCR-cDNA are later protocol-sensitivity extensions. Hi-C, WGS reprocessing, extra long-read callers, learned scoring, ORF reconstruction, folding and molecule/binder generation are deferred. None is a prerequisite for checkpoint A. Do not let a six-view dashboard create analytical obligations beyond the RNA deliverable.

## 3. Inputs and feasibility

| Role | Manifest alias | Compressed bytes observed in public HTTP HEAD checks |
| --- | --- | ---: |
| Primary library A | `SGNex_K562_directRNA_replicate4_run1` | 1,063,990,132 |
| Corroboration library B | `SGNex_K562_directRNA_replicate5_run1` | 992,767,949 |
| Illumina R1 | `SGNex_K562_Illumina_replicate4_run1` | 4,603,971,288 |
| Illumina R2 | Same paired library | 5,074,387,151 |

All four file URLs returned HTTP 200 during this review. Combined compressed input is 11.74 GB decimal; direct RNA is 2.06 GB and Illumina 9.68 GB. These are transfer sizes, not disk/RAM requirements or downloaded-file integrity checks. References, indexes, uncompressed reads, sorting space and outputs require a separate estimate. Recheck metadata before execution; multipart S3 ETags are not SHA-256 content checksums.

Sources: [SG-NEx](https://github.com/GoekeLab/sg-nex-data), [Nanopore manifest](https://raw.githubusercontent.com/GoekeLab/sg-nex-data/master/docs/samples.tsv), [Illumina manifest](https://raw.githubusercontent.com/GoekeLab/sg-nex-data/master/docs/illumina_samples.tsv). Read exact URLs from pinned rows; Illumina requires both R1 and R2 files.

Freeze the repository commit, raw manifests/row numbers, selected files, checksums, source URLs and access time. The repository documents replacement/re-basecalling of files; preserve actual release provenance and do not attribute an ENA-specific basecaller field to an AWS FASTQ without verification. Validate gzip/FASTQ structure, unique original read identities, paired-end synchronization and sequence/quality lengths. Record full-library read counts.

The direct-RNA libraries use the same kit, but distinct replicate labels do not by themselves establish independent cultures. Verify library/extraction/culture relationships from source metadata. Same-number Illumina and Nanopore replicates are not automatically matched aliquots. If relationships remain unknown, report cross-library corroboration with biological independence UNKNOWN. Do not invent specimen IDs that inflate biological-replicate counts.

Audit duplicate raw-read UUIDs across files; identical sequence alone does not establish the same physical molecule. PCR-derived Illumina support is reported as read-pair/fragment evidence with duplicate flags, not a proven molecule count. Report overlap and ambiguity explicitly.

Select/replace files on metadata and general QC before candidate outcomes. Do not add replicates to rescue BCR–ABL1 or a preferred chimera. A prespecified hashed read subset may measure throughput; full selected libraries are required for scientific checkpoint completion.

## 4. Human reference and implementation contract

Default: realign FASTQ using pinned minimap2/LongGF versions and the inherited settings. SG-NEx BAMs may be inspected as diagnostics, but are not silently interchangeable with this primary run. Use a hash-pinned, compatible GENCODE 43 / GRCh38.p13 genome/GTF/transcript set; validate contig naming and transcript versions. The selected libraries contain sequin spike-ins: pin corresponding synthetic reference sequences or explicitly quarantine their assignments; do not report spike-in/mixed synthetic events as human candidates.

Parameterize sample/library/specimen identities, reference labels/files, expected read counts and output paths throughout worker, acceptance, assessment and workflow code. Existing constants include mouse names, genome labels and counts; changing only the FASTQ is insufficient. Proposed human output root: `runs/k562-pilot/<run-id>/`. Create a separate configuration, reference manifest and human rule snapshot; do not overwrite mouse receipts.

The inherited assessor uses 100-base query/exonic anchors, MAPQ >=20, >=80% split query coverage, gap/overlap within 20 bases and explicit single-transcript/alternative-mapping comparisons. Retain these for the primary portability run. The worker's `-G50k` intron bound and finite secondary search are limitations in human data; preserve them for the baseline and log missed/unresolved explanations. Any sensitivity change is a separately versioned analysis, never a silent correction after seeing preferred outcomes.

Two implementation gaps must remain visible:

- The current assessor does not perform a dedicated internal-adapter assay. Add a separate annotation only with pinned kit-specific sequences, scoring/position rules and technical fixtures; until then mark adapter status NOT_ASSESSED. Mapping-supported must not be called artifact-free. New artifact annotations do not silently alter the inherited ranker.
- Current LongGF association checks read membership in an ordered gene pair, not an independently reconciled exact breakpoint. Retain caller text and label this pair-level association. Exact-junction caller agreement is UNKNOWN unless an adapter resolves and checks both breakpoints. An alignment scan is not another caller.

Unknown biological identities require an explicit schema/report solution before aggregation. Per-library rankings can preserve the single-library ordering without claiming independent specimens; a combined rank must not count arbitrary placeholder identities as replication.

Freeze code, rules, references, environment and matching definitions before K562 candidate inspection. Test fixes on synthetic/previous mouse fixtures. Any outcome-informed change produces an exploratory version and preserves the original run.

## 5. Evaluation design that avoids circularity

1. Run library A independently. Freeze its complete technical-decision ledger and ranking before joining any B/Illumina support.
2. Run B independently with the same method. Compare to A after the freeze. Do not use B-derived recurrence in the primary A ranking and then claim B validates that ranking.
3. Keep combined A+B evidence as a separate descriptive catalogue, generated after evaluation. Its ranking, if supplied, is not the independently evaluated primary ranking.
4. In checkpoint B, align Illumina independently of candidate identities. Compare with frozen A and A+B tables after alignment/filters are frozen; keep its evidence outside primary ranking features.

Canonical comparisons use the same assembly, transcript-order strands and both zero-based interbase boundaries. Retain stable gene identifiers and ambiguous assignments separately; do not join by symbols alone. Primary corroboration requires exact boundary/strand identity and compatible assignment. Preserve raw/normalized placements. Microhomology-shifted or nearby matches are a separate descriptive category; no post-hoc widening of tolerance to increase recovery.

Report supported-junction counts for A and B, intersection, union, A→B and B→A corroboration fractions, and missing/ambiguous mappings. Use explicit denominators: for example |A∩B|/|A| for A→B when |A|>0; empty denominators are undefined. Stratify by read support and cis/trans status. These are recurrence measures, not sensitivity or biological precision. Unequal depth affects overlap; report depth and do not promise a target percentage.

Prespecify a review budget of k=min(20, number of supported A junctions). Compare the inherited A ranker against distinct-read-count ranking on the identical A pool using B corroboration, and later Illumina corroboration, as reported-support outcomes. Average analytically across ties; stable identifiers are for display. Keep unknown assessment states and coverage visible. Do not derive biological FDR, specificity or calibrated probabilities. A null gain is acceptable; this comparison does not require training.

## 6. Illumina implementation and controls

The current mouse workflow has no implemented Illumina corroboration path. For checkpoint B, use CPU STAR 2.7.11b as the proposed single alignment route, with chimeric output explicitly enabled and the same human reference build. Pin binary/container hashes and full parameters before biological inspection. Reference: [STAR documentation](https://github.com/alexdobin/STAR). Do not apply long-read minimap2 settings to Illumina.

Before launching B, freeze tested settings for strandedness, minimum unique split anchors, alignment ambiguity, mismatch allowance, repetitive sequence, duplicate reporting and exact-boundary conversion. Check positive/negative coordinate fixtures on both strands and distinguish split reads from discordant pairs. Do not align exclusively to a candidate fusion FASTA and treat every hit as independent confirmation; plausible parental/genomic alternatives must compete. If B cannot be completed within its measured cap, report it as incomplete/deferred without changing A's result.

BCR–ABL1 receives a separate stage trace in each library: raw proposal, assigned junction, read evidence, mapping alternatives, filter decision and recovered isoform. Gene-pair detection and exact-isoform recovery are separate. Diagnose non-recovery without tuning or substituting a known sequence. Controls are displayed separately; provide ranking comparisons both including and excluding BCR–ABL1 so one familiar event does not dominate the claimed benefit.

Use technical single-transcript, ambiguous-mapping and synthetic junction controls for software behavior. Empirical artifact examples require positive technical evidence. Direct-RNA preparation and multi-protocol concordance are not guarantees of biological authenticity. With DNA/Hi-C deferred, origin stays NOT_ASSESSED/UNRESOLVED for new candidates.

## 7. Repeatability, completion and resource bounds

Rerun a bounded, hash-selected real-read subset through alignment → discovery → assessment with unchanged inputs/configuration; compare canonicalized scientific outputs, excluding volatile metadata and arbitrary ordering. Keep this subset out of outcome-based tuning. Separately run mouse regression fixtures after parameterization. A synthetic fixture alone does not establish end-to-end repeatability; a subset rerun does not establish full-run bitwise reproducibility.

Required implementation checks: human sample/reference propagation, both-strand coordinates, duplicate identity, unknown specimen relationships, paired-end validation, no outcome features, exact-versus-pair caller provenance, control failures and honest missing-data states. Run applicable tests, `chrna build` and development-only `chrna benchmark` after analytical changes. Do not consume held-out mouse data.

Before production, write a resource worksheet with measured transfer/throughput, reference/index/scratch disk estimate, RAM, total-cost forecast and explicit wall-time caps for A and B. No finish time is promised until these are measured. Use existing CPU controller, inspect live leases and avoid competing controllers. One useful CPU worker by default; no GPU required for A. Any later GPU route must justify a bounded job.

Fresh quotes/currency and all project resources/attached charges must pass the budget utility: preferred combined rate below USD 100/hour, hard ceiling USD 500/hour. Unknown prices fail closed. Rate limits are not spending targets. Preserve outputs and stop owned temporary workers after success/failure; leave unrelated resources unchanged.

Deliver manifests/hashes/configuration/commands, read/QC counts, full candidate/read decisions, per-library rankings, freeze receipts, corroboration metrics/baselines, control traces, rerun comparison, report/data export, source-backed limitations and resource/shutdown receipts. Reuse the dashboard's evidence views; no new design module is required.

Track completion separately as A execution, control detection, corroboration result, repeatability result and B execution. Execution can complete with zero corroborated candidates; report that outcome. Unprocessed data or failed required stages cannot become biological zeroes. A failed positive control precludes claiming successful control verification even when processing completed.

Hi-C and downstream protein/design outputs remain DEFERRED / NOT_ASSESSED. All human results, mouse outputs and fictional demo records remain separate. No candidate counts or scientific successes are implied by this plan.
