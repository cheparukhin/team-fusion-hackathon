# Current gaps and action plan

Updated 20 September 2026 after repository publication and documentation audit. AI scientific review is complete for the current claim set; presentation and delivery checks remain open.

Delivered capabilities and verification are listed in [STATUS.md](STATUS.md). The user-requested [AI scientific review](docs/submission/SCIENTIFIC_REVIEW.md) confirmed the core calculations and corrected missing protein-evidence context. Independent human review remains unperformed; this AI review must not be presented as human signoff.

Work window extended by the user to **13:07 BST on 20 September 2026**.

**Current integration blocker:** sequencing stopped at its cutoff without a complete full-dataset result; the frozen folding supplement is now independently verified. The controller outage interrupted output recovery. Keep integration local and use only recovered, hash-checked artifacts; the public release remains the verified baseline.

## Next actions, in priority order

1. **Verify final analysis handoffs:** distinguish recovered artifacts from newer observed progress. Folding verification is complete; retain the explicit missingness and sequence-hypothesis limits. Keep RNA pairs, peptide hypotheses and models separate; do not infer translation or function from a fold.
2. **Presentation and access:** seven presented slides and appendix are visually checked, with a 4:06 synthetic fallback. Deck metadata still reports owner-only access; verify after the owner enables link viewing. Human rehearsal and pronunciation review remain open.
3. **Browser verification, when available:** the enforced policy check is blocked. Once restored, verify case switching, keyboard navigation, source links, review persistence and downloads. Mock-document checks do not establish browser behaviour; do not bypass the policy.
4. **Utility:** independent reviewer evaluation remains unperformed. Report utility as unmeasured; three selected demonstrations cannot establish time savings or broad accuracy.

## Scope and compute

The sequencing owner confirmed all three workers stopped; its current local shutdown receipt was inspected. Complete full-cohort results are not recovered and verified, so the presentation retains the completed **two-million paired short-read Parabricks** result.

The [folding supplement](results/folding_expansion/README.md) contains **341 verified candidate peptide models across 223 RNA pairs plus 42 controls**, with 117 of 500 selected predictions missing. All archive hashes, model checks and 34 matched fragment comparisons passed independent review. Keep the random and enriched arms separate; neither model completion nor confidence establishes translation, function or population-wide prevalence.

Keep K562 outside the current seven-slide story: completion metadata reports 8/8 stages, but the reported top-20 result ties the read-count baseline. The imported K562 worktree remains an older snapshot; do not silently combine its artifacts with the later completion metadata. This polishing task owns evidence review and submission integration. Separate tasks own the authorized sequencing and folding expansions; unfinished outputs do not change the submission claims.

The current shared project compute ceiling is $200/hour, only where needed; it is not a spending target. No new cloud instance was provisioned by this improvement task; work used an isolated directory on the shared CPU with bounded threads. Concurrent sequencing and folding tasks now own additional workers and their shutdowns. No teammate resource was altered. Check their live inventory and combined cost before any future launch; this document is not a live cost monitor.

[Current status](STATUS.md)
