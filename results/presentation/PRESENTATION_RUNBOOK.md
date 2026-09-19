# Five-minute PowerPoint run

Open `chRNA_gallery.pptx`. The first slide is the workflow, as requested. All twelve slides form a figure gallery; individual SVG/PNG/PDF exports can be reused or reordered. Use the PowerPoint-rendered PDF as the backup when available, and keep the offline evidence explorer available for questions.

| Time | Slides | Say/show |
|---|---|---|
| 0:00–0:25 | 1 — Workflow | “Can 3D genome context help prioritize chimeric RNAs for independent support?” Trace published tables → audited pairs → fixed models → held-out evaluation → inspectable evidence. |
| 0:25–1:00 | 2–3 — Cohort and evidence units | 479 eligible pairs; 109 reported NanoString positives. Explain that a pair, a junction, and a translated protein are different claims. Unknown assay reporting/QC is not a proven negative. |
| 1:00–1:40 | 4 — Gsdmd architecture | Trace blue Gsdmd exon 2 into red Tmem106a exon 6. Show the 118-aa reference reconstruction: 73 residues match GSDMD, followed by a novel tail in a different frame. This is the paper's functional exemplar; our reconstruction and model are separately labeled. |
| 1:40–2:00 | 5 — Other examples | Show Cd274–Lacc1 and Psap–Lgals3 exact junction diagrams. A high score with no reported-positive label is a prioritization example, not a discovery or a proven false call. |
| 2:00–2:20 | 6 — Evaluation | Keep shared parent genes together. Both models train and evaluate on the same 401 pairs with complete Hi-C. |
| 2:20–2:55 | 7 — Main result | AP 0.296 versus 0.300; paired difference interval crosses zero. “This experiment does not establish an improvement from Hi-C.” |
| 2:55–3:15 | 8 — Screening view | Matched top-20 support is 10 for RNA versus 9 with Hi-C. More elaborate input did not produce a clearly better shortlist. |
| 3:15–3:40 | 9 — NVIDIA execution | Actual Parabricks A100 run, two million read pairs, 85.49-second alignment. 3,275 split-junction records but no fixed-criteria probe matches. Tiny-sample non-detection is not biological absence; no CPU speedup claim. |
| 3:40–4:05 | 10 — OpenAI and explorer | Show one cited observation and one unknown from the five Codex-authored reports. They are cached, source-grounded reports; no live Responses API call is claimed. |
| 4:05–4:35 | 11 — Structural context | Experimental mouse GSDMD parent versus a genuine cached Boltz2 prediction of the reconstructed chimera. Low confidence is visible: mean pLDDT 48.7. Geometry is a hypothesis, not experimental evidence or a druggability screen. |
| 4:35–5:00 | 12 — What comes next | External assay-tested candidates, explicit QC, and independent validation. End on the reproducible evidence workflow, with the inconclusive result stated clearly. |

For every source, generation command and interpretation, see `FIGURE_GUIDE.md`. Do not describe the paper's AlphaFold 3 illustration as an experimental chimeric structure, the current Boltz2 model as the author's coordinates, or either candidate protein model as high confidence. Additional candidate-specific protein predictions are explicitly unavailable rather than invented.
