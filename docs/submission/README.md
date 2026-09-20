# Hackathon submission guide

The [shared group doc, FINAL tab](https://docs.google.com/document/d/1suaqiVIxDCT2D8bvYndyFK6X1NSLv9tCG7VbrBRzrG4/edit?tab=t.ge1x7g3r1m8e) defines three contributions: ranking, fusion-protein disorder analysis and the fusion-protein dashboard.

- **Final team deck:** [Fusion chRNA Slides](https://docs.google.com/presentation/d/1qZ2owRuz6j3A48Y_XcheWADuoPh6HYkmn2NCLqFDybk/edit).
- **Single repository:** [team-fusion-hackathon](https://github.com/cheparukhin/team-fusion-hackathon).
- **Live demo:** [Chimeric RNA Structure Explorer](https://chimeric-rna-exon-structures.a-cheparukhin.chatgpt.site).
- **Local demo and code:** [portable dashboard](../../dashboard/README.md), [ranking reproduction](../../README.md#reproduce), [disorder methods and source](../../scripts/structure_campaign/README.md).

## Submission gates

At the 20 September 2026 cleanup check, the final deck still contained organizer-template placeholders (team names, workflow, evidence, repository URL and reproduction instructions). Another presentation task is editing it. Complete and check that deck before submission; the older PDFs below do not represent it. Confirm anonymous viewer access and rehearse the five-minute talk.

The organizer asks for a five-minute presentation using its template and access to one GitHub repository containing reproduction/demo code. This repository includes the portable dashboard renderer and frozen inputs; full disorder score profiles and model coordinates are published as [versioned release assets](../../preservation/controller-20260920/README.md), with a verified restore command. Fresh browser interaction checks are blocked by the browser tool's unavailable policy check. No organizer submission has been sent by this cleanup.

## Claim-to-evidence map

| Contribution | Supported statement | Evidence |
| --- | --- | --- |
| Ranking | No established improvement from Hi-C in this retrospective evaluation | [Metrics](../../results/classifier/metrics.json), [model card](../../results/classifier/MODEL_CARD.md) |
| Disorder | 42/188 V3 vs 18/188 V1 predominantly-disordered conditional hypotheses | [Report](../../results/structure_campaign/RESULTS.md), [summary](../../results/structure_campaign/analysis/summary.json) |
| Dashboard | Ten pilot protein hypotheses and a separate literature control linked to exon origins | [Source, frozen inputs and rebuild](../../dashboard/README.md) |
| NVIDIA | Real Parabricks A100 processing and Boltz-2 structure predictions | [Compute evidence](../../results/compute/STATUS.md), [folding supplement](../../results/folding_expansion/README.md) |
| OpenAI | Codex-assisted implementation and three recorded, source-linked evidence reviews | [Replay instructions](../../scripts/review/README.md), [scientific review](SCIENTIFIC_REVIEW.md) |

A null ranking comparison does not demonstrate that RNA formation is independent of 3D genome organization. Predicted disorder or low model confidence does not establish absence of function. The published Gsdmd–Tmem106a evidence remains distinct from the pilot's failure to recover it.

---

The material below is retained as a historical fallback. Its deck permissions, timing and validation statements refer to that older version only.

# Historical evidence-review presentation

[Editable organiser-template deck](https://docs.google.com/presentation/d/1bnxMDj1dVAnIauboX6clVpuLMnzJVSns28jrIecd8QE/edit) · [PDF slide preview](slides-preview.pdf) · [Narrated fallback](evidence-walkthrough.mp4)

Seven presented slides plus a technical appendix. All eight native slide images were inspected. The PDF is a raster preview of those images, not a native editable export. Google Slides retains the editable presentation. Deck link-sharing is awaiting the owner's change.

## Submission links

| Material | Public access |
| --- | --- |
| [Presentation PDF](https://github.com/cheparukhin/team-fusion-hackathon/releases/download/submission-expanded-2026-09-20/slides-preview.pdf) | Anonymous download and checksum verified |
| [4:06 narrated fallback](https://github.com/cheparukhin/team-fusion-hackathon/releases/download/submission-expanded-2026-09-20/evidence-walkthrough.mp4) | Anonymous download and checksum verified |
| [Reproducible core ZIP](https://github.com/cheparukhin/team-fusion-hackathon/releases/tag/submission-expanded-2026-09-20) | Published; pinned to source 928b7bc |
| [Verified folding supplement](https://github.com/cheparukhin/team-fusion-hackathon/releases/tag/folding-evidence-2026-09-20) | Published; 383 models and complete frozen artifacts |
| [Current repository](https://github.com/cheparukhin/team-fusion-hackathon) | Public; current methods, status and operating policy |

The core ZIP contains the presentation and original evidence workflow. The separate folding archive adds 341 candidate peptide models across 223 RNA pairs and 42 controls; 117 selected predictions are missing. Both archives retain their exact source manifests. [Access-check receipt](public-access-check.json).

**Owner actions:** enable anyone-with-link viewing on the editable deck, rehearse the five-minute talk, and submit the deck/repository through the organiser's submission route. No submission has been sent by this task. The public PDF and video remain available independently of Google Slides permissions.

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

The **two-million short-read pairs** processed by Parabricks are separate from the mouse **long-read** cohort. The expanded sequencing analysis did not finish within its cutoff; unrecovered or incomplete results are excluded from the presentation.

Real-browser verification, human rehearsal and final access checks remain open. See [GAPS.md](../../GAPS.md). To rebuild the synthetic fallback on a Mac with Daniel, ffmpeg and ffprobe installed, run `python3 scripts/presentation/build_walkthrough.py`; the ordinary scientific reproduction does not need these media tools.

The [verified folding supplement](../../results/folding_expansion/README.md) is available separately for technical inspection. It does not change the seven-slide core story or establish new biological findings.
