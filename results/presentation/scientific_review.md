# Independent scientific presentation review

Reviewed 2026-09-19 by the data/review worker. Scope: `candidate_examples.json`, `reference_orf_verification.json`, `FIGURE_GUIDE.md`, `gallery/figure_manifest.json`, `gallery/scenes.json`, and the presentation construction scripts, checked against frozen dataset, prediction, metric, and structure artifacts. This is a bounded scientific source review, not a new model run or PowerPoint rendering certification.

## Outcome

No unresolved material scientific discrepancies found. One transient provenance finding—the gallery manifest initially recorded an older structure-manifest SHA—was reported to the author and resolved by regeneration. All five recorded gallery input hashes match the current files at final review.

## Independently checked

- **Candidate identities and endpoints:** The three examples retain ordered parent genes and GRCm39 coordinates. Their published-support labels, deduplicated long-read counts, and saved out-of-fold scores agree with the frozen tables: Gsdmd:Tmem106a (reported support, 1 read), Cd274:Lacc1 (reported support, 1 read), and Psap:Lgals3 (not reported supported, 6 reads). Every displayed representative endpoint lies at the appropriate strand-aware exon boundary. Exon numbers belong to the explicitly selected GENCODE M28 transcript, not to a uniquely established isoform. Alternative exact-half transcript matches remain recorded. The candidate contrast uses explicitly identified full-panel RNA scores; it does not present them as the matched-cohort RNA comparison.
- **Evidence units:** Exact probe-derived endpoints are distinguished from published long-read junction records and their coordinate-convention uncertainty. Gene-pair NanoString reporting labels are not promoted to junction validation, successful assay QC, biological authenticity, translation, or function. Psap:Lgals3 has no inferred protein/function claim.
- **Evaluation figures:** Primary comparison uses the same 401 observed-contact pairs, including 92 reported positives. AP values are baseline 0.2656357295, RNA 0.2959500513, and RNA + Hi-C 0.2995931726. The AP difference is 0.0036431213 with the recorded component-bootstrap interval [-0.0310440353, 0.0468855011]. Both models use matched observed-contact training rows within the fixed gene-disjoint folds. The interval resamples saved predictions without model refitting; the figure does not claim demonstrated improvement.
- **Top-20 figures:** Matched-cohort supported counts are baseline 9, RNA 10, and RNA + Hi-C 9 of 20. In the same 244 interchromosomal observed-contact pairs (58 positives), counts are RNA 5 and RNA + Hi-C 7 of 20. These are counts of reported-support labels, not verified true chimeras; compared ranked lists need not contain the same pairs.
- **Reference ORF:** Checked recorded transcript/source hashes, junction/ORF arithmetic, protein length, protein SHA, and equality to the structure-input sequence. The reference transcript reconstruction gives 118 residues with sequence SHA-256 `f0766d124b52f0061597ce4e822e9275a04152df574f9a512631a0fa6ed8a2fa`. The first 73 complete residues are GSDMD-derived. The donor supplies 220 coding nucleotides: residue 74 spans the junction, and residues 74–118 form the novel out-of-frame tail. Thus the red tail is not a canonical TMEM106A protein domain. This architecture-matched reference reconstruction is not an author-supplied full construct sequence or de novo isoform discovery.
- **Structure distinctions:** The experimental mouse GSDMD parent is PDB 6N9N, chain A, X-ray resolution 3.30 Å. Of shared positions 1–73, 69 have observed coordinates; missing positions 1/71/72/73 are not filled. The chimera asset is a genuine cached prior open-source Boltz2 model, not an experimental structure, a new NIM execution, or the paper's AlphaFold3 model. The paper Figure 3a model is separately identified as AlphaFold3. Recomputed confidence summaries from the cached pLDDT array agree with mean pLDDT 48.704315, shared-region 51.20903, novel-tail 44.64111, and 53.3898% of residues below 50; recorded pTM is 0.335918. The low confidence is visible and is not presented as proof of disorder or absence of function. Experimental parent coordinates do not validate the chimera fold.
- **GPU pilot and reporting:** The gallery distinguishes the actual 2,000,000-pair bounded alignment from biological validation: 28,482 chimeric records comprise 3,275 split records and 25,207 encompassing-mate records, with zero probe-panel matches. The 85.49-second figure is alignment time, not a CPU speedup measurement. Cached cited explanations remain separate from labels and predictors.

## Frozen inputs at final check

| Artifact | SHA-256 |
|---|---|
| `results/classifier/metrics.json` | `9c9233baf2b6c9f388b27bba7f127b1f62dc4b86ded00939153d7511a0de0338` |
| `results/classifier/predictions.tsv` | `012ca471c5ce4cd504f515b6e64a7d3d0c7321f1e63cd91e3cc500f4a7f1d4ca` |
| `results/presentation/candidate_examples.json` | `8add7d42cd77e21b976e42f46ef676f0640948df633831fa786e1bbe78f91b48` |
| `results/compute/pilot_summary.json` | `76a622e5db3ecf5640577250bbdb84eb7b649404627d3eb672307dfb8d0dd740` |
| `results/structures/manifest.json` | `0abd73741124511faba480b3259e6edbbae34e39bb031e53166b905c6ab340e6` |

No dataset, model, coordinate, label, or structure file was changed during this review. Presentation export/render validation is tracked separately by the presentation author.
