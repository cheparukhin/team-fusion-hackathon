# Scientific review and judge questions

Status: reviewed by the active Codex assistant against the saved evidence on 20 September 2026. This is **not independent biology signoff**. Decisions remain unchanged and unsigned.

## What is defensible

| Claim in the current story | Direct evidence | Boundary the presenter must preserve |
|---|---|---|
| Psap–Lgals3 has a 924-nt nearest second-parent endpoint discrepancy | [Independent source-coordinate calculation](../../results/review/psap_source_audit.json); [recorded comparison](../../results/review/psap-lgals3/step-02.json) | It is a descriptive difference between source records and a mapped probe, not a proven probe error, artifact, or alternative isoform. Published coordinate convention remains unresolved. |
| Six published read IDs support the pair | [Source audit](../../results/review/psap_source_audit.json); [candidate retrieval](../../results/review/psap-lgals3/step-01.json) | Pair support does not establish the designed probe junction. Repeated records of the same read are not independent observations. |
| Published RNA evidence exists for Gsdmd–Tmem106a and Cd274–Lacc1 | Primary-paper page 2 in [Gsdmd source retrieval](../../results/review/gsdmd-tmem106a/step-05.json) and [Cd274 source retrieval](../../results/review/cd274-lacc1/step-04.json) | These experiments were performed by the paper's authors. The project did not independently reproduce their PCR/Sanger or functional findings. |
| The cached Gsdmd reference model is low confidence | [Structure evidence](../../results/review/gsdmd-tmem106a/step-04.json) | Mean pLDDT 48.7 does not show that the protein exists, folds stably, or has a function. The model is a reference-sequence reconstruction. |
| NVIDIA output contributes a real independent evidence check | [GPU execution summary](../../results/compute/pilot_summary.json); [direct output re-match](../../results/review/psap-lgals3/step-03.json) | It is a deterministic two-million-pair prefix from one RNA run, not a sensitivity experiment. Sample/timing differ from other assays. Zero matches cannot overturn published support. “Independent” describes another assay source, not an independent reviewer or prospective validation. |
| Codex selected tools and interpreted results | Recorded action reasons, implementation hashes and actual outputs in [three frozen cases](../../results/review/case_freeze.json) | The active Codex assistant ran these checks. The UI replays them; it is not a deployed unattended agent or a live API demonstration. |
| Twelve tool outputs replay exactly | [Extracted-bundle verification](../../results/reproduction/bundle_validation.json) | Exact computation and resolved pointers do not prove that every biological interpretation follows from a source. Human review remains necessary. |
| Hi-C does not establish improved ranking | [Evaluation metrics](../../results/classifier/metrics.json) | AP difference is small and its interval spans zero. Top-20 comparison averages boundary ties; no superiority or causal claim. |

## Why the next actions follow

**Psap–Lgals3:** choosing a junction-specific assay requires knowing which sequence it should target. The endpoint discrepancy makes source alignment/coordinate reconciliation the immediate next step. This is a proposed decision based on a verified uncertainty, not a demonstrated improvement in laboratory outcomes.

**Gsdmd–Tmem106a:** a low-confidence prediction answers neither whether the RNA exists nor whether a protein is present in a new intended sample. Retain published RNA evidence and scope any proposed protein assay to the actual sequence and sample.

**Cd274–Lacc1:** missing structure in this project is missing information, not a negative result. Review the published junction and sample context before an independent RNA confirmation; protein interpretation stays separate.

## Questions to rehearse

**What did you discover?** We identified and source-checked a mismatch that changes the immediate review question. We did not discover a new functional RNA or claim a novel mechanism. The project contribution is the inspectable evidence-to-decision workflow.

**Why use an agent?** The recorded Codex run chose which check addressed each uncertainty and interpreted its result into a next-step proposal. Deterministic tools preserve the evidence and make the computations repeatable. We have not measured whether this beats a scientist using the same tools manually.

**What did NVIDIA change?** Parabricks generated actual independent short-read evidence. The assistant re-matches that output rather than treating the presence of a GPU artifact as validation. Here it returned bounded non-detection; respecting that limit is part of the decision.

**Why not claim the high score is a probability?** It is an uncalibrated score for reported NanoString support in a selected retrospective panel. It does not estimate RNA authenticity, resolve isoforms or establish translation.

**Does exact replay validate the advice?** No. It validates the recorded calculations, source integrity and pointers. Biological interpretation still needs a qualified reviewer; utility needs a prospective comparison.

**What would make the next evaluation credible?** Freeze new review questions and a scoring rubric before assistance; collect independent source-based answers and unsupported-claim counts. Counterbalance review order if measuring time. These three selected demonstrations cannot establish time savings or broad accuracy.

## Independent reviewer handoff

Review the three frozen decisions in the [offline page](../../demo/review/index.html). For each case, inspect the cited source and mark **endorse**, **revise**, or **defer**, giving the scientific reason. Check: factual support; distinction between pair and junction; interpretation of non-detection/missingness; feasibility of the proposed next step; and any omitted contradictory evidence.

Use your own name and actual review date. Download the local receipt so the decision hash is retained. A revision should state the replacement wording and source. Do not count a receipt as an experiment or an authenticated endorsement. Do not record elapsed-time claims retroactively. No acceptance has been filled in on a reviewer's behalf.
