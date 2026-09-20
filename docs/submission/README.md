# Final presentation: scope, claims and evidence

**Scope authority:** the [FINAL tab of TeamFusion-Wilbe2026](https://docs.google.com/document/d/1suaqiVIxDCT2D8bvYndyFK6X1NSLv9tCG7VbrBRzrG4/edit?tab=t.ge1x7g3r1m8e). Earlier tabs contain plans, not additional completed-deliverable claims. The three contributions are ranking, fusion-protein disorder analysis, and the fusion-protein dashboard.

**Presentation:** [Fusion chRNA Slides](https://docs.google.com/presentation/d/1qZ2owRuz6j3A48Y_XcheWADuoPh6HYkmn2NCLqFDybk/edit). The deck covers the sequence-led workflow, folding/disorder comparison, and dashboard.

## Claim-to-evidence map

| FINAL-tab contribution or framing | What the repository supports | Evidence and limit |
| --- | --- | --- |
| Ranking: sequence-first analysis | One mouse library was assessed with LongGF and independent split/single-transcript alignment checks; 116 exact-junction proposals met technical support rules; ten reference-assisted hypotheses were frozen for folding. | [Workflow and rules](../../workflows/mouse-pilot/README.md). One caller and one biological sample do not establish multi-caller consensus or biological truth. The diagram shows the broader architecture, not universal completion. |
| Test whether 3D context helps ranking | On 401 complete-contact gene pairs, AP is 0.296 for RNA and 0.300 with Hi-C; the paired interval is −0.0310 to +0.0469. | [Metrics](../../results/classifier/metrics.json), [model card](../../results/classifier/MODEL_CARD.md). This is a separate gene-pair benchmark, not the exact-junction ranker. No established predictive gain; no conclusion of biological independence or condensate causation. CTCF knockout remains a proposed direction. |
| Analyze the NanoString-supported subset | 109 reported supported RNA pairs led to 188 eligible conditional annotated-start hypotheses from 91 pairs; 18 pairs had no eligible reconstruction. | [Cohort results](../../results/structure_campaign/RESULTS.md), [cohort methods](../../results/structure_campaign/cohort/METHODS.md). Pair-level support does not validate every peptide, exon chain, isoform or protein. |
| Estimate disorder and inspect domains | Metapredict V3: 42/188 predominantly disordered; V1: 18/188. Pfam matches occur in 151/188 conditional peptides. | [Disorder methods](../../results/structure_campaign/analysis/METHODS.md), [domain methods](../../results/structure_campaign/domains/METHODS.md). Predictors are reported separately; there is no validated aggregate fitness score. Domain matches do not prove folding or function. |
| Generate and compare structures | The supported campaign has 67 single-sequence Boltz2 predictions across 51 sequences plus one cached MSA-backed result. The presented Gsdmd comparison uses four cached Boltz2 predictions and two new local predictions: AF2 and ESMFold. | [Campaign ledger summary](../../results/structure_campaign/RESULTS.md), [cross-model evidence](../../results/structure_campaign/cross_model_gsdmd/README.md). Seed repeats and cached predictions are not new proteins; not all 109 pairs were folded. |
| Dashboard for experimental follow-up | Eleven linked RNA/exon/structure views: ten single-read pilot hypotheses plus a separately reconstructed literature control. | [Public dashboard](https://chimeric-rna-exon-structures.a-cheparukhin.chatgpt.site), [source and rebuild](../../dashboard/README.md). It is a tool to inspect hypotheses, not a calibrated probability of existence. Prospective usefulness has not been measured. |
| New drug targets / functional chRNAs | This motivates the project and describes a possible future use. Published functional evidence is attributed to Venezia et al. | The project performed no functional or druggability assay. Predicted order, low confidence and model disagreement neither prove nor disprove biological function. |

The FINAL tab also contains exploratory language about a 1,000-structure sample, cross-species conservation, an atlas, CTCF perturbation and NMD/export mechanisms. These are not completed headline results. The separate [383-model supplement](../../results/folding_expansion/README.md), [partial cross-species comparison](../../workflows/cross-species/README.md), and K562 extension remain labeled supporting work. Do not combine their counts with the supported disorder cohort or dashboard pilot.

## Presented model-disagreement example

The exact 118-aa conditional Gsdmd–Tmem106a sequence has mean pLDDT 48.7 in cached MSA-backed Boltz2, 41.6/41.7/42.4 in three Boltz2 single-sequence seeds, 65.5 in AF2, and 47.2 in ESMFold. Whole-sequence disorder calls are 100.0% for V3, 48.3% for V1 and 44.9% for MoreRONN. [Numerical records, thresholds and provenance](../../results/structure_campaign/cross_model_gsdmd/README.md).

Confidence is not calibrated across engines, pLDDT is not an experimental disorder measurement, and the reconstruction is not a solved fusion structure. The retained donor and novel-frame tail have different evidential roles. The paper's functional experiments remain independent evidence.

## Tools actually used

Codex assisted implementation, orchestration, evidence inspection and communication. Boltz2 generated saved structural predictions; the cross-model example added local AF2 and ESMFold. The separate [Parabricks run](../../results/compute/STATUS.md) processed two million short-read pairs on an A100. Prepared hosted AF2/OpenFold NIM routes were blocked by missing credentials and submitted no prediction requests. The optional live OpenAI report adapter was not validated as a live service. Avoid implying every illustrated integration ran successfully.

## Use and reproduce

The presentation uses the [v4 animation](https://drive.google.com/file/d/1TRs6OyIeDtm3aj2tgsS_WBLGzfPSLUF7/view). Its 4K master is also preserved in the evidence release at `animation/trans_splicing_v4_4k_30s.mp4` after restoration. The original renderer in `animation/` documents the illustrative method; it is not the final presentation export.

[Open the dashboard](https://chimeric-rna-exon-structures.a-cheparukhin.chatgpt.site), [run it locally](../../dashboard/README.md), or [reproduce the RNA/Hi-C benchmark](../../README.md#reproduce). [Restore the large evidence files](../../preservation/controller-20260920/README.md) for model coordinates, full profiles and reports.

The linked Google Slides deck is the current presentation. The [earlier frozen release](https://github.com/cheparukhin/team-fusion-hackathon/releases/tag/submission-expanded-2026-09-20) preserves superseded slide exports; they are no longer current repository entry points.
