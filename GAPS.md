# Current gaps and action plan

Updated 20 September 2026 after repository publication and documentation audit. The submission is not ready for final signoff.

Delivered capabilities and verification are listed in [STATUS.md](STATUS.md).

## Next actions, in priority order

1. **Independent biology review:** a qualified scientist reviews all three frozen decisions and presentation claims, recording corrections/endorsement/deferral. [Instructions and source audit](docs/submission/SCIENTIFIC_REVIEW.md). All three reviews are currently pending; prior agent reviews do not satisfy this gate.
2. **Real browser verification:** once the enforced browser-policy check is available, verify case switching, keyboard navigation, evidence links, review persistence and downloads. Current mock-document tests are not browser tests. Do not bypass the policy check.
3. **Presentation and access:** update the native appendix/speaker notes to reflect the now-public repository; share the owner-only deck; rehearse twice under five minutes and check fallback pronunciation. The video is not an interactive demo recording or a human rehearsal.
4. **Final release:** incorporate accepted corrections, regenerate/inspect changed artifacts, build and verify the final bundle, then publish the approved release and verify non-owner access. Pin the final source version across the deck, demo, README and bundle. The public “Latest” release is currently the old checkpoint.
5. **Utility evaluation:** use a prespecified comparison with actual reviewers if feasible. Otherwise report utility as unmeasured. The three selected demonstrations cannot establish time savings or broad accuracy.

## Scope and compute

Keep K562 outside the current three-slide story: completion metadata reports 8/8 stages, but the reported top-20 result ties the read-count baseline. The imported K562 worktree remains an older snapshot; do not silently combine its artifacts with the later completion metadata. No extra cohorts, folding, models, binder design, dashboard redesign or animations are on the critical path.

The user’s overnight compute ceiling was $400/hour. No new cloud instance was provisioned by this improvement task; work used an isolated directory on the shared CPU with bounded threads. Last inventory check at about 00:33 UTC showed only the controller running. Inventory and billing must be rechecked before any future launch; this is not a live cost monitor.

[Current status](STATUS.md)
