# Submission presentation

[Editable organiser-template deck](https://docs.google.com/presentation/d/1bnxMDj1dVAnIauboX6clVpuLMnzJVSns28jrIecd8QE/edit) · [PDF slide preview](slides-preview.pdf) · [Narrated fallback](evidence-walkthrough.mp4)

Seven presented slides plus a technical appendix. All eight native slide images were inspected. The PDF is a raster preview of those images, not a native editable export. Google Slides retains the editable presentation. Deck link-sharing is awaiting the owner's change.

## Five-minute presentation

- **0:00–0:30:** which fusion is worth testing?
- **0:30–1:00:** distinguish gene-pair, exact-junction and protein evidence.
- **1:00–1:45:** show what Codex and NVIDIA actually contributed.
- **1:45–2:40:** trace the 924-base endpoint discrepancy visually.
- **2:40–3:20:** interpret the Gsdmd model alongside published experiments.
- **3:20–4:05:** compare held-out RNA and Hi-C results with uncertainty.
- **4:05–4:50:** close with the delivered workflow and next validation; ten seconds of buffer.

[Speaker notes](speaker-notes.json) contain the complete planned script and sources. These timings are not a completed human rehearsal. The fallback has disclosed synthetic narration and uses native slide images; it is not a browser recording or live inference. [Transcript](walkthrough-transcript.md) · [Media validation](walkthrough-validation.json).

## Current scientific scope

The [AI scientific review](SCIENTIFIC_REVIEW.md) is complete. The reviewed scientific source version is `76fb5de`; the submission ZIP manifest identifies its complete packaged version. The public repository contains the current source; [download the reviewed release](https://github.com/cheparukhin/team-fusion-hackathon/releases/tag/submission-expanded-2026-09-20).

The three cases are selected demonstrations. Hi-C has no established ranking gain. The 924-base discrepancy is a genomic-coordinate comparison, not proof of a bad probe or false RNA. Gsdmd–Tmem106a has published protein and functional evidence that our weak model does not contradict. Independent human review and utility measurement remain unperformed.

The **two-million short-read pairs** processed by Parabricks are separate from the mouse **long-read** cohort. A concurrent task is expanding both sequencing workflows; unfinished results are not included in the presentation's claims.

Real-browser verification, human rehearsal and final access checks remain open. See [GAPS.md](../../GAPS.md). To rebuild the synthetic fallback on a Mac with Daniel, ffmpeg and ffprobe installed, run `python3 scripts/presentation/build_walkthrough.py`; the ordinary scientific reproduction does not need these media tools.
