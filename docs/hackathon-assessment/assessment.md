# Hackathon assessment — 20 September 2026, 00:06 BST

**Recommendation: submit one agent-assisted chimeric-RNA evidence-review workflow.** The current assets are substantial, but neither improved biological prediction nor a complete agentic product has been demonstrated. Concentrate on a scientist making a better-supported validation decision.

This is a read-only assessment of the running project, not a new implementation. Reviewed the live organiser guide and slide template, team document, MASTER and PROJECT_PLAN tasks, both remote workspaces, model/report/export code, numerical results, mouse completion records, GPU receipts, K562 progress and a saved demo screenshot. Ran the current focused tests and an in-memory demo export. Concurrent work continued during inspection.

## What actually exists

| Workstream | Verified evidence | Submission role |
|---|---|---|
| Mouse raw-read pilot, `chrna` | 2,238,871 reads; 6,466 proposed exact junctions; 116 passing technical evidence rules; 10 frozen reference-assisted protein hypotheses plus one separate published-architecture control; 11 structure outputs | Genuine execution evidence. All ten selected hypotheses have one supporting read from one sample. Structure predictions do not validate protein expression/function. |
| Published-panel experiment, `quick_hack` | 479 eligible pairs, 109 reported NanoString positives; five parent-gene-disjoint folds; 401 complete Hi-C rows | Best organised submission base. Retrospective reported-support prediction, not authenticity classification or new discovery. |
| GPU short-read pilot | Parabricks processed two million read pairs in 85.49 seconds of alignment; 3,275 split-junction records; zero fixed-criteria probe-junction matches | Real NVIDIA execution. Timing excludes setup; no measured CPU speedup. Non-detection is not a negative biological label. |
| Demo/OpenAI | Polished offline explorer; five Codex-authored cited reports; optional unexecuted live API adapter | Useful foundation. Current generation is supplied-evidence-to-prose, not an implemented iterative tool-selection workflow. |
| Human K562 | Latest checked progress: 2/8 stages, discovery of first direct-RNA library; no corroboration/repeatability results yet | Optional external evidence, conditional on completion and review. Do not make presentation depend on it. |

The published flagship Gsdmd–Tmem106a was not recovered de novo in the bounded mouse pilot. Its structure control is a separate reconstruction of the published architecture. Never join this control, panel evidence and novel pilot candidates as if they were one experimentally validated result.

## Main judging gaps

The organisers weight scientific impact, NVIDIA/OpenAI application, execution, originality, and presentation/reproducibility equally.

1. **Scientific benefit is not established.** RNA model AP is 0.296 versus read-count 0.268, but the saved paired interval for the difference is −0.0011 to +0.0634. Adding Hi-C gives 0.296 → 0.300 on matched rows, interval −0.0310 to +0.0469. Neither supports a robust superiority claim. The top-20 read-count baseline breaks ties by pair name: its reported 10 becomes **11.07 expected supported pairs under random tie-breaking**, versus 11.00 for the RNA model. This is a reporting correction, not an invitation to tune on the same evaluation data. Unreported NanoString support remains unknown biological truth.

2. **Agentic contribution is too thin.** The app browses cached results; the optional live adapter writes a report from supplied inputs. No executed retrieve → choose/check evidence → revise recommendation → scientist review trace was found. NVIDIA has genuine outputs, but the submission needs to show how those outputs inform the scientist's decision.

3. **Originality and user value are buried.** The paper already establishes chimeric transcripts and selected functional examples; TYPHON already provides a fusion-detection workflow. The defensible contribution is a reproducible assistant that reconciles heterogeneous evidence, identifies unsupported conclusions and proposes the next discriminating experiment. This is a positioning recommendation, not a claim of proven novelty across all literature.

4. **Release integrity is unfinished.** During review, the move from `results/task1` to `results/dataset_reconstruction` initially broke a test and the exporter. Concurrent work repaired this: final check **23 tests passed; in-memory export returned 479 candidates and five Codex reports**. The saved ZIP still represents an earlier commit; recent changes remain uncommitted, and `git remote -v` returned no configured remote. A fresh-clone reproduction and judge-accessible repository remain release gates. No completed team submission deck was verified in inspected files/targeted Drive search.

5. **Correctness checks need narrower claims.** The report validator checks citation IDs, numeric tokens and structured values; it accepted an unsupported qualitative assertion with a valid citation ID in a diagnostic test. It does not establish semantic entailment. Keep biological claim review explicit. The current runbook also spends too much stage time explaining caveats and the experiment, with little demonstration of a scientist reaching a decision.

## Focused delivery plan

Suggested owners are roles to assign, not people already committed.

| Deadline, Sunday BST | Owner | Deliverable and acceptance gate |
|---|---|---|
| 09:30 | Team lead | Freeze one sentence, one user, one demo. Use `quick_hack` as submission base; keep mouse and human evidence in explicitly separate cases. One owner controls integration and release. |
| 10:30 | Release owner | Finish path migration, refresh linked evidence/caches, commit coherent release, establish one GitHub repository. Clean checkout builds the displayed results; tests and evidence links pass; ZIP hashes match release. |
| 12:00 | Workflow owner + biology reviewer | Demonstrate one bounded agent workflow over existing evidence tools: retrieve pair/junction facts, inspect independent GPU evidence, identify an uncertainty, recommend the next validation step, record scientist acceptance/override. Preserve actual tool inputs/outputs and replay them offline. Do not build general autonomous infrastructure. |
| 12:30 | Biology/evaluation owner | Freeze 3–5 review cases before running the demo evaluation: a published positive, an unresolved high-score pair, an evidence-conflict case; use a technically rejected case only if its rejection is actually evidenced. Compare manual review with assisted review on the same question, checking evidence accuracy, unsupported claims and time to a usable recommendation. Report small-sample scope; no invented speedup. Correct top-k ties and retain the null Hi-C result. |
| 13:00–14:30 | Presenter + release owner | Complete the organisers' three presented slides and non-presented technical appendix; record a short demo backup; verify repository/deck access; rehearse twice in five minutes. Use 15:00 as readiness deadline because organiser schedule sections disagree between 15:00 and 16:00. |

If K562 finishes by the evidence freeze, assess its positive-control trace, independent exact-junction corroboration and reproducibility before adding one result. Otherwise retain as ongoing work. Existing jobs need not be cancelled to remove them from the submission's critical path.

**Cut:** new architectures, hyperparameter searches, more folding/model comparisons, additional cohorts, druggability/binder work, dashboard redesign, and further animation iterations. Keep Hi-C as one honest ablation; protein hypotheses in the appendix unless an already-reviewed case materially helps the core decision.

**Five-minute story:** 40 seconds on the scientist's problem; 50 seconds on the workflow and actual OpenAI/NVIDIA roles; 150 seconds on one evidence-to-decision demo; 60 seconds on measured evaluation, principal limitation and reproducibility. The required technical appendix holds versions, accessions, commands and repository link.

## Sources and audit receipts

- [Organiser guide](https://docs.google.com/document/d/1mCli3i4DZAVsEn8f6TETGYrWR0X1MuEVaMtJv13fCWI/edit?tab=t.uyo6les0pjn6): five equal criteria, five-minute talk, single GitHub repository and supplied template.
- [Submission template](https://docs.google.com/presentation/d/1Gh_loKW2OFL-wi1wUd6lGqa67wVCpw6ARQZ6U82Ms1w/edit): overview; workflow; demo/evidence/usefulness; technical appendix marked not presented.
- [Venezia et al.](https://www.nature.com/articles/s41586-026-10982-x) and [TYPHON](https://github.com/erenada/TYPHON): prior work boundaries.
- Local evidence snapshots: [classifier metrics](evidence/classifier-metrics.json), [mouse completion audit](evidence/mouse-completion-audit.json), [GPU pilot](evidence/parabricks-pilot-summary.json), [K562 progress](evidence/k562-progress.json), [saved explorer screenshot](evidence/explorer_desktop.png).
- Inspected code: `quick_hack/src/chrna/model.py`, `scripts/demo/{reports,export,cache_agent_reports}.py`, `scripts/reproduce.py`, `scripts/package_submission.py`, and focused tests. Final validation: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`; in-memory `export.build()`.

