# Current submission status

Updated 20 September 2026. The repository is **public**; anonymous GitHub access was verified. The Google Slides deck still awaits owner-enabled link sharing. The [reviewed release](https://github.com/cheparukhin/team-fusion-hackathon/releases/tag/submission-expanded-2026-09-20) supplies the consolidated ZIP, public slide preview and narrated fallback.

User-requested [AI scientific review](docs/submission/SCIENTIFIC_REVIEW.md) is complete: source-coordinate reconstruction, held-out metrics, gene separation and twelve tool replays passed the recorded CPU checks. The Gsdmd case now explicitly acknowledges published protein and functional evidence. Independent human review remains unperformed.

## Delivered and verified

- [Folding supplement](results/folding_expansion/README.md): 383 validated models (341 candidate peptides across 223 RNA pairs, 42 controls), 117 missing at cutoff; 34 matched fragment comparisons. All 2,211 archive hashes and the clean-extraction verifier passed. These are conditional reference models, not validated proteins.

- 479 eligible ordered pairs, 109 reported NanoString-supported pairs; 401 complete Hi-C pairs. Unknown assay support is not a biological negative.
- Matched AP: RNA 0.296, RNA + Hi-C 0.300; paired interval spans zero. Tie-aware expected top-20: full-panel read support 11.07 versus RNA 11.00; matched read support 9.73, RNA 9.63, Hi-C 9.00. No established ranking gain.
- Three recorded Codex review cases, twelve exact tool-output replays, source-linked proposals and local scientist-review receipts. All three independent scientist reviews remain pending.
- The Psap–Lgals3 924-nt endpoint discrepancy was independently recalculated from source tables/reference transcripts. None of its six published read UUIDs was found in the one cached mouse library checked; the originating alignments remain unresolved.
- Real Parabricks A100 output: two million paired reads, 85.49 seconds alignment, zero fixed-rule probe-junction matches. Non-detection is not absence; no CPU speedup claim.
- Clean CPU reconstruction produced identical input/folds/predictions. The current code passed 30 Python tests, twelve exact tool replays and keyboard-focus logic checks on the clean extracted bundle on Brev. **The new review page has not passed real-browser or visual checks.** Older explorer browser receipts apply only to their saved version.
- Organiser-template deck: seven presented slides plus appendix, current native snapshots, PDF preview and timed script. A 4:06 synthetic-narration slide walkthrough is available; it is not a browser recording or human rehearsal.
- Compute policy: reserve `chrna-controller` for lightweight shared-repository work. Analysis, tests, rendering, compression and other heavy jobs run on separate worker instances under the shared $200/hour ceiling and fixed shutdown controls. Check stale jobs and the fallback launcher before any controller restart; this policy authorizes no restart or extension.

## Remaining gates

Authorized browser verification; human rehearsal; deck sharing; recovery and verification of remaining sequencing outputs. Prospective utility remains unmeasured. K562 completion metadata reports 8/8 stages but does not establish a ranker gain; it stays outside the core story.

[Start here](START_HERE.md) · [Gaps and next actions](GAPS.md)
