# Submission gaps and action plan

This is the working checklist from the [20 September assessment](docs/hackathon-assessment/assessment.md). The assessment preserves its original observations; checkboxes here describe this checkpoint.

## Priority 0 — one reliable release
- [x] Save the current implementation, demo, scientific outputs, and gap assessment in one GitHub repository.
- [x] Keep published-panel results, mouse-pilot hypotheses, and ongoing K562 work explicitly separate.
- [x] Verify the public-table/reference download and core reproduction path in a clean source directory and fresh environment. Twenty-five tests pass; rebuilt input, folds and predictions are byte-identical. Cached Hi-C and GPU outputs remain explicit inputs; see [validation](results/reproduction/clean_cpu_validation.json).
- [ ] Freeze a final release; ensure slides, demo, downloadable bundle and README all refer to it.
- [ ] Grant judges access when submitting; this checkpoint repository is private.

## Priority 1 — demonstrate the scientist's decision
- [ ] Agree one product statement: an assistant that helps scientists decide which chimeric-RNA candidates merit experimental validation.
- [ ] Demonstrate an actual bounded agent run: retrieve candidate/junction evidence, choose an evidence check, interpret its result, recommend the next discriminating experiment, and record scientist review.
- [x] Show how actual NVIDIA-generated evidence informs that review. Retain inputs, outputs, versions and an offline replay.
- [ ] Review unsupported qualitative claims explicitly; citation-ID and numeric checks do not establish that a source supports a biological assertion.

## Priority 2 — demonstrate utility without overstating accuracy
- [x] Correct top-20 evaluation for tied scores. The read-count baseline has approximately 11.07 expected reported-supported pairs under random tie-breaking, compared with 11.00 for the RNA model.
- [ ] Retain the null Hi-C result: AP 0.296 to 0.300; paired interval includes zero.
- [ ] Freeze 3–5 review cases before evaluation. Compare manual and assisted evidence review for accuracy, unsupported claims, usable recommendations and elapsed time; report the small sample honestly.
- [ ] Have a biology reviewer sign off on presentation claims and distinguish published validation from this project's computations.

## Priority 3 — finish the submission
- [ ] Complete the organiser template: three presented slides plus the non-presented technical appendix.
- [ ] Record a short backup demo and rehearse twice within five minutes.
- [ ] Verify deck/repository access and be ready by 15:00 BST on Sunday.
- [ ] Include K562 only if completed, checked and useful before the evidence freeze.

## Scope cuts
No additional models, cohorts, hyperparameter searches, folding comparisons, drug-design modules, dashboard redesigns or animation iterations on the submission's critical path. Hi-C remains an honest ablation; structure predictions remain hypotheses.

Suggested Sunday gates: scope 09:30; stable release 10:30; agent demonstration 12:00; evidence freeze 12:30; packaging and rehearsal completed 14:30.

[Detailed rationale and evidence](docs/hackathon-assessment/assessment.md) · [Checkpoint contents](CURRENT_PROGRESS.md)


## Overnight iteration plan — 20 September, 00:40 BST

Deadline: 09:00 BST (08:00 UTC). Optimize the existing scientist-review workflow, not scope.

1. Correct tied top-k evaluation; preserve the null Hi-C result and all saved predictions.
2. Verify reproduction on the shared CPU in a separate directory, with bounded threads and no interference with teammates.
3. Deliver a bounded evidence-checking agent demonstration with replay, claim-level review, and an honest human-review handoff.
4. Package the strongest three-slide story and technical appendix, verify links and demo, and reassess remaining gaps.

Compute inventory: controller and K562 CPU are running; both listed GPU/pilot instances are stopped. No new instance has been provisioned. User's combined rate ceiling is $400/hour; obtain live prices before any launch. Existing GPU evidence is sufficient for the next iteration.

Iteration 1: top-k expectations now integrate boundary ties exactly, with attainable ranges and the previous pair-ID ordering preserved for audit. Exhaustive-permutation and edge-case tests pass on the shared CPU. Full-panel read-count baseline is approximately 11.07 expected supported pairs versus 11.00 for the model: do not claim top-20 uplift. Next priority is reliable reproduction and a useful evidence-review decision.

Iteration 2: fresh environment installation and `scripts/reproduce.py --download` completed on the shared CPU. Rebuilt scientific inputs, folds and predictions match the checkpoint byte-for-byte; all 25 tests pass. No shared system packages changed. Next priority: the review demo. The Psap:Lgals3 case has a concrete probe-versus-read junction discrepancy worth showing rather than adding more models.

Iteration 3: three bounded Codex review runs now retain actual tool outputs and source hashes. Re-matching uses the verified NVIDIA Parabricks junction file; decisions distinguish pair-level support, probe/read discrepancies, non-detection, and low-confidence/missing structures. These are selected demonstration cases, not a blinded study. Codex qualitative review is recorded; independent scientist signoff and measured utility remain pending. Next priority is a clear replay and scientist-review interface, followed by presentation packaging—not additional inference runs.

Iteration 4: added an offline scientist-review page with three evidence-led cases, recorded-tool navigation, source-linked claims and locally saved/downloadable review receipts bound to the decision hash. Application logic checks pass for persistence, case isolation, required fields, stale records, storage failure and escaping. Browser/visual inspection remains OPEN: the Codex browser tool twice could not verify its enforced security policy; no alternative browser was used to bypass that check. Next priority is the submission story and remaining factual audit while browser access is unavailable. Do not present mock-document tests as browser validation or local self-reported receipts as independent signoff.
