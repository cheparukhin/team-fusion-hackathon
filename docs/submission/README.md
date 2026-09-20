# Submission presentation

[Editable organiser-template deck](https://docs.google.com/presentation/d/1bnxMDj1dVAnIauboX6clVpuLMnzJVSns28jrIecd8QE/edit) · [PDF slide preview](slides-preview.pdf) · [Narrated fallback](evidence-walkthrough.mp4)

Three presented slides plus a technical appendix. All four native slide images were inspected. The PDF is a raster preview of those images, not a native editable export. Google Slides retains the editable presentation. Deck link-sharing is awaiting the owner's change.

## Five-minute presentation

- **0:00–0:50:** a gene-pair score does not identify a testable junction.
- **0:50–2:00:** Codex selected and executed evidence checks; real NVIDIA Parabricks output contributes to review.
- **2:00–4:50:** show the Psap–Lgals3 coordinate discrepancy and explain why the original alignment must be reconciled before assay selection.
- **4:50–5:00:** close with the demonstrated evidence trail and the unmeasured utility limitation.

[Speaker notes](speaker-notes.json) contain the complete planned script and sources. These timings are not a completed human rehearsal. The fallback has disclosed synthetic narration and uses native slide images; it is not a browser recording or live inference. [Transcript](walkthrough-transcript.md) · [Media validation](walkthrough-validation.json).

## Current scientific scope

The [AI scientific review](SCIENTIFIC_REVIEW.md) is complete. The reviewed scientific source version is `76fb5de`; the submission ZIP manifest identifies its complete packaged version. The public repository contains the current source; [download the reviewed release](https://github.com/cheparukhin/team-fusion-hackathon/releases/tag/submission-reviewed-2026-09-20).

The three cases are selected demonstrations. Hi-C has no established ranking gain. The 924-base discrepancy is a genomic-coordinate comparison, not proof of a bad probe or false RNA. Gsdmd–Tmem106a has published protein and functional evidence that our weak model does not contradict. Independent human review and utility measurement remain unperformed.

The **two-million short-read pairs** processed by Parabricks are separate from the mouse **long-read** cohort. A concurrent task is expanding both sequencing workflows; unfinished results are not included in the presentation's claims.

Real-browser verification, human rehearsal and final access checks remain open. See [GAPS.md](../../GAPS.md). To rebuild the synthetic fallback on a Mac with Daniel, ffmpeg and ffprobe installed, run `python3 scripts/presentation/build_walkthrough.py`; the ordinary scientific reproduction does not need these media tools.
