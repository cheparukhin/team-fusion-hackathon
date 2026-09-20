# Current gaps and action plan

Updated 20 September 2026 after repository publication and documentation audit. AI scientific review is complete for the current claim set; presentation and delivery checks remain open.

Delivered capabilities and verification are listed in [STATUS.md](STATUS.md). The user-requested [AI scientific review](docs/submission/SCIENTIFIC_REVIEW.md) confirmed the core calculations and corrected missing protein-evidence context. Independent human review remains unperformed; this AI review must not be presented as human signoff.

Work window extended by the user to **13:07 BST on 20 September 2026**.

## Next actions, in priority order

1. **Real browser verification:** once the enforced browser-policy check is available, verify case switching, keyboard navigation, evidence links, review persistence and downloads. Current mock-document tests are not browser tests. Do not bypass the policy check.
2. **Presentation and access:** native slides and notes now reflect the public repository and completed AI review. Verify link sharing after the owner enables it; rehearse twice under five minutes and check fallback pronunciation. The video is not an interactive demo recording or a human rehearsal.
3. **Final release:** incorporate accepted corrections, regenerate/inspect changed artifacts, build and verify the final bundle, then publish the approved release and verify non-owner access. Pin the final source version across the deck, demo, README and bundle. The public “Latest” release is currently the old checkpoint.
4. **Utility evaluation:** use a prespecified comparison with actual reviewers if feasible. Otherwise report utility as unmeasured. The three selected demonstrations cannot establish time savings or broad accuracy.

## Scope and compute

A separate task is expanding both sequencing workflows, including ten mouse long-read samples (~52.9 million reads), under its one-hour cutoff and $100/hour combined ceiling. No full-cohort result is verified yet; the presentation still cites the completed **two-million paired short-read Parabricks** run. Integrate only completed, source-checked findings; preserve sample identity and distinguish the two assays.

Keep K562 outside the current three-slide story: completion metadata reports 8/8 stages, but the reported top-20 result ties the read-count baseline. The imported K562 worktree remains an older snapshot; do not silently combine its artifacts with the later completion metadata. No extra cohorts, folding, models, binder design, dashboard redesign or animations are on the critical path.

The user’s overnight compute ceiling was $400/hour. No new cloud instance was provisioned by this improvement task; work used an isolated directory on the shared CPU with bounded threads. The latest inventory shows the controller, a cross-species CPU and the existing Boltz A100 running; they belong to concurrent work and were not altered. Inventory and billing must be rechecked before any future launch; this is not a live cost monitor.

[Current status](STATUS.md)
