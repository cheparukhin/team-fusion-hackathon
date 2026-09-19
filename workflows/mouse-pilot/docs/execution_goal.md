# Tonight's focused chimeric-RNA reproduction

Owner-approved revision, 19 September 2026. This supersedes the earlier requirement to finish the full mouse cohort, fold every eligible protein, and run SG-NEx in this goal. Preserve completed work. The prior broad plan is future work, not tonight's acceptance criteria.

## Outcome and deadline

Deliver by 23:00 Europe/London on 2026-09-19 (22:00 UTC) a reproducible pilot: complete raw-read discovery on the prepared mouse sample SRR28984805, auditable RNA-junction ranking, supported ORF reconstruction, Boltz-2 structures for up to ten evidence-selected candidate proteins, and an HTML report with a separately labelled published Gsdmd-Tmem106a sequence control. Deliver fewer candidates if fewer defensible sequences exist; do not manufacture recovery. Report unavailable results and blocking stages honestly. A report-only fallback does not mean the scientific pilot was achieved.

Work in /srv/chrna-team/project through the existing shared chrna-codex tmux session using gpt-6-astra, medium reasoning, normal speed (Fast off), execution/default mode. Keep the native goal active until the focused deliverable is complete or a genuine blocking condition applies. No token budget was requested.

## Scope and sequence

1. Reuse the validated pilot FASTQ, references, installed environment and completed intake. Finish minimap2 + LongGF and run the complete pilot before integrating every caller. Within 90 minutes of accepting this revised goal, aim to have working discovery and real pilot candidates. JAFFAL/Genion integration must not hold up the end-to-end pilot; document missing callers and the resulting limitation on paper-method reproduction.
2. Keep Snakemake resumption and essential tests for the actual path. Avoid extra infrastructure or rechecking already validated stages without cause. First resolve live worker pricing/currency, available resources, and a bounded launch/output-preservation/shutdown path.
3. Assess each proposed two-gene junction against the best single-known-transcript explanation, including noncoding transcripts. Keep every candidate's evidence and decision reasons. Preserve supported singletons and alternative mappings; distinguish exclusion, unresolved ambiguity, and time/cost deferral. Nearby genes, biotype, microhomology, noncanonical boundaries and downstream alternative frames are not blanket rejection rules.
4. Rank exact junctions transparently using evidence category, biological replication where actually available, distinct read support, mapping specificity, junction quality and caller agreement where available. Do not imply replication from one sample or consensus from one caller. Prespecify rules before published-outcome comparison.
5. Reconstruct ORFs in a bounded batch of the strongest RNA candidates, expanding only until enough defensible sequences are available. Require a supported junction-spanning ORF and a resolved amino-acid sequence; distinguish observed, consensus and reference-assisted reconstruction. Materially ambiguous protein sequences stay unresolved. Do not require full-length parental proteins. NMD and disorder predictions are annotations, not automatic exclusions.
6. Freeze selection rules before folding and validation joins. Target eight strongest eligible distinct proteins, avoiding redundant near-identical isoforms, plus two additional eligible diversity cases selected by explicit rules (for example a supported singleton and a different junction/frame class). If such cases are absent, fill from the remaining ranked eligible list. Keep the complete RNA ranking unchanged. Record reasons for selection and deferral; use no learned scorer tonight.
7. Fold up to ten recovered sequences, plus the published flagship as a separate control and at most one new necessary parental comparator (prefer suitable existing coordinates). Reuse identical-sequence predictions while keeping provenance separate. Never substitute the published sequence for failed de novo recovery. Pilot three representative sequence lengths to measure MSA/preparation/inference time, then schedule only jobs that fit the deadline. Start with one Boltz-2 sample per sequence using the selected runner's standard inference settings. Repeat up to three prespecified cases only if time remains. Use one working deployment path, cached MSAs/results and bounded retries; no full local MSA database download. If NIM credentials are unavailable, use the open-source Boltz runner rather than making credential setup a prerequisite.
8. After freezing, compare available results with published evidence at its actual resolution: gene pairs, junctions and full protein sequences separately. Trace Gsdmd-Tmem106a through the stages without rescue rules. Structural confidence is not proof of expression/function; numerical comparison to the authors requires their coordinates.
9. Deliver candidate tables, decision records/filter waterfall, RNA and protein FASTAs, structure/confidence files, exon/ORF diagrams, HTML report, reproducible commands and explicit deferred-work list. Keep human review distinct from frozen computational results.

Optional only within remaining time: one inflammatory sample, additional callers, or focused repeat predictions. Defer the full ten-sample cohort, SG-NEx, model training, Hi-C prediction, broad complexes, Foldseek and routine second-model predictions.

## Cutoffs (Europe/London, 19 September 2026)

- By 19:00: freeze available RNA evidence and the protein shortlist; begin production folding. If missed, reduce scope and report the delay rather than silently moving the deadline.
- At 21:00: stop adding samples or proteins; finish only jobs expected to complete before the compute cutoff.
- By 22:00: stop computation, preserve outputs and shut down temporary workers. Leave the shared CPU controller available.
- By 23:00: deliver the verified report and completion/limitation record. Do not continue the superseded full-cohort objective overnight.

## Brev budget and resource policy

The preferred combined project rate is below USD 100/hour. The absolute hard ceiling is USD 500/hour across all project Brev instances, including the existing controller and CPU/GPU workers. This supersedes the previous USD 100/hour hard ceiling. These are hourly rate limits, not a total budget or permission to spend toward the ceiling.

Check live quotes, currency, existing project resources and applicable attached-resource charges before every launch. Unknown prices fail closed. Start with one suitable CPU worker and one GPU worker only when sequences are ready. Additional GPU workers are permitted only for bounded independent jobs when measured throughput demonstrates a material deadline benefit; preserve the preferred rate where feasible and always stay below the hard ceiling. Do not launch a speculative fleet. Record forecast and actual resource usage/cost. Preserve outputs and stop temporary workers promptly after success or failure. Never alter unrelated teammate resources. Reconcile the existing budget utility with these owner-approved values before launches.

## Restart coordination and current state

At the handoff checkpoint, the existing main task was RESTART_READY for an owner-requested controller-managed restart to load science plugins, with no live analysis children. Preserve that coordination; do not initiate a competing restart or alter authentication/services. Update the native goal now; after the coordinating controller resumes this task, read this file and proceed under this reduced scope. The previous full-cohort continuation instructions in the restart checkpoint are superseded by this file.

Scientific sources: https://www.nature.com/articles/s41586-026-10982-x ; GSE267147 / PRJNA1109857 ; https://github.com/erenada/TYPHON . The Google Doc and prior reproduction proposal remain background; the constraints above govern tonight's execution.

## Owner authorization: full access and end-to-end execution

The owner explicitly requested Full Access permissions and autonomous end-to-end completion of this focused goal. Run the shared Codex task with sandbox_mode=danger-full-access and approval_policy=never, retaining Astra medium and normal speed. Perform required environment setup, bounded Brev provisioning, computation, validation, reporting, output preservation and temporary-worker shutdown within the existing scope, deadline and budget. Do not stop at a plan, prepared scripts, or a successful smoke test; execute the actual scientific stages and deliver the artifacts. Continue through routine recoverable failures. Missing credentials, provider failures or scientifically unresolved sequences must be reported honestly, not disguised as completion. Full Access does not expand the scientific scope, waive the spending ceiling, or authorize changes to unrelated resources. The controller is completing the previously requested restart now; once resumed, the previous wait-for-restart instruction is fulfilled and execution should proceed.
