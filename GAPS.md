# Current gaps and action plan

Updated 20 September 2026 after repository publication and documentation audit. AI scientific review is complete for the current claim set; presentation and delivery checks remain open.

Delivered capabilities and verification are listed in [STATUS.md](STATUS.md). The user-requested [AI scientific review](docs/submission/SCIENTIFIC_REVIEW.md) confirmed the core calculations and corrected missing protein-evidence context. Independent human review remains unperformed; this AI review must not be presented as human signoff.

Work window extended by the user to **13:07 BST on 20 September 2026**.

**Current integration blocker:** host access to `chrna-controller` reportedly recovered, but severe memory pressure remains (about 243 MB available, no swap). Keep integration local. The published release is available independently; analysis owners are recovering outputs and maintaining independent worker cutoffs. Do not add controller load or assume controller-based watchers are healthy. New results remain unverified.

## Next actions, in priority order

1. **Real browser verification:** once the enforced browser-policy check is available, verify case switching, keyboard navigation, evidence links, review persistence and downloads. Current mock-document tests are not browser tests. Do not bypass the policy check.
2. **Presentation and access:** native slides and notes now reflect the public repository and completed AI review. Verify link sharing after the owner enables it; rehearse twice under five minutes and check fallback pronunciation. The video is not an interactive demo recording or a human rehearsal.
3. **New-results integration:** inspect the sequencing and folding tasks’ completed outputs and provenance before changing any scientific claim. Distinguish supported RNA pairs, conditional peptide hypotheses and completed models. A public reviewed release of the current evidence workflow is available with an exact source manifest and clean-bundle validation. Keep a usable release available if the full analysis is incomplete at its cutoff.
4. **Utility evaluation:** use a prespecified comparison with actual reviewers if feasible. Otherwise report utility as unmeasured. The three selected demonstrations cannot establish time savings or broad accuracy.

## Scope and compute

A separate task is expanding both sequencing workflows, including ten mouse long-read samples (~52.9 million reads), under its one-hour cutoff. No full-cohort result is verified yet; the presentation still cites the completed **two-million paired short-read Parabricks** run. Integrate only completed, source-checked findings; preserve sample identity and distinguish the two assays.

Keep K562 outside the current seven-slide story: completion metadata reports 8/8 stages, but the reported top-20 result ties the read-count baseline. The imported K562 worktree remains an older snapshot; do not silently combine its artifacts with the later completion metadata. This polishing task owns evidence review and submission integration. Separate tasks own the authorized sequencing and folding expansions; unfinished outputs do not change the submission claims.

The current shared project compute ceiling is $200/hour, only where needed; it is not a spending target. No new cloud instance was provisioned by this improvement task; work used an isolated directory on the shared CPU with bounded threads. Concurrent sequencing and folding tasks now own additional workers and their shutdowns. No teammate resource was altered. Check their live inventory and combined cost before any future launch; this document is not a live cost monitor.

[Current status](STATUS.md)
