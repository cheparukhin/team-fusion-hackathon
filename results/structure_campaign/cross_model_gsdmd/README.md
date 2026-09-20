# Gsdmd–Tmem106a: model disagreement shown in the final slides

This comparison uses one exact **118-aa conditional reference reconstruction**. Six verified structures span three engine families: four cached Boltz2 predictions and two newly executed local predictions, AlphaFold2 and ESMFold. It is a computational sensitivity example, not a solved fusion structure or new functional assay.

| Model / protocol | Mean pLDDT | Residues below pLDDT 50 |
| --- | ---: | ---: |
| Boltz2, cached MSA-backed | 48.7 | 53.4% |
| Boltz2, single sequence, seed 20260919 | 41.6 | 90.7% |
| Boltz2, single sequence, seed 20260920 | 41.7 | 84.7% |
| Boltz2, single sequence, seed 20260921 | 42.4 | 86.4% |
| AlphaFold2, cached MSA input | 65.5 | 16.1% |
| ESMFold, single sequence | 47.2 | 50.8% |

| Sequence-disorder predictor | Whole sequence | Donor residues 1–73 | Tail residues 74–118 |
| --- | ---: | ---: | ---: |
| metapredict V3 | 100.0% | 100.0% | 100.0% |
| metapredict V1 | 48.3% | 17.8% | 97.8% |
| MoreRONN | 44.9% | 11.0% | 100.0% |

[Exact values, thresholds, sequence identity and input hashes](comparison.json) · [Per-region model confidence](analysis/model_region_confidence.tsv).

V3 uses score ≥0.5, V1 ≥0.42 and MoreRONN >0.5. The predictors are reported separately. V1/V3 are related networks; V3 includes AlphaFold-derived training information. Confidence is not calibrated across engines, and low pLDDT is not a measured disorder call. The red region includes the junction codon and novel-frame tail, not an intact canonical TMEM106A domain. Published functional evidence is not overturned by these predictions.

The four Boltz2 rows overlap the [earlier supported-cohort campaign](../RESULTS.md); do not add them again as four new proteins or jobs. AF2 and ESMFold are the two new predictions in this comparison. Hosted AF2/OpenFold NIM requests were not submitted because credentials were unavailable; local execution is recorded instead.

Coordinates, per-residue arrays, raw receipts and comparison images are [release-backed evidence](../../../preservation/controller-20260920/README.md). Restore before running the optional saved-coordinate tests or rebuilding reports. Analysis source is in [scripts/structure_campaign](../../../scripts/structure_campaign/README.md). The separate 383-model supplement and the ten dashboard pilot candidates have different cohorts and protocols.
