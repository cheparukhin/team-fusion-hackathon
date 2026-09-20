# Executed chRNA protein-hypothesis campaign

## Main result

Among **188 conditional annotated-start peptide hypotheses** from **91/109 NanoString-supported RNA pairs**, metapredict V3 calls **42 (22.3%) predominantly disordered** (more than half the residues called disordered). V1 sensitivity calls **18 (9.6%)**. Most hypothetical peptides are therefore not predominantly disordered under either method; that is not proof of a stable fold or biological function.

Mean per-peptide disordered fraction is **30.7%**, median **20.7%**, and pooled residue fraction **27.1%**. These are different summaries. Giving each RNA pair equal weight yields mean hypothetical-peptide disordered fraction **28.9%**; equal weighting across alternatives is descriptive, not an expression probability.

**Strict observed-chain primary eligibility is 0.** Public junction evidence does not settle complete exon-chain/start usage. The executed set is an explicitly conditional reference-reconstruction sensitivity arm, not a measured proteome. 30 peptides are invariant across compatible reference isoform combinations. 18 RNA pairs have no eligible annotated-start peptide in this reconstruction; they are unresolved rather than scored as disordered or noncoding. The additional 746 alternative-start peptides are analyzed separately.

## Domain and context evidence

Local Pfam 38.2 search found gathering-threshold domain matches in **151/188** conditional peptides. See [domain methods](domains/METHODS.md) for profile thresholds, overlap handling and domain-truncation comparisons. A match suggests familiar sequence architecture; no match does not establish a novel fold or lack of function.

There are **372** deduplicated comparisons of the same amino-acid region in hypothetical fusion versus complete native-parent context and **267** isolated-fragment comparisons. Median predicted-disorder difference is **0.0** for native-context comparisons. These are model context effects, with related sequences/alternative source mappings retained, not independent biological replicates or causal measurements.

The published functional **Gsdmd–Tmem106a** exemplar illustrates the limit of an order-based function filter: its reconstructed 118-aa peptide is called 100% disordered by V3 but 48.3% by V1, while the separately cached MSA-backed Boltz model has mean pLDDT 48.7. Neither prediction overrides the paper's functional evidence or directly measures physical disorder.

## Actual structure execution

| Protocol | Jobs in ledger | Verified jobs | Unique verified sequences | Reused jobs |
|---|---:|---:|---:|---:|
| boltz2_2.2.1_precomputed | 51 | 1 | 1 | 1 |
| boltz2_2.2.1_single_sequence | 67 | 67 | 51 | 0 |

Completion is technical success, not protein-function validation. MSA-backed and single-sequence models are distinct protocols; their confidence values are not pooled. Failures and deferred inputs remain in the ledger. Seed repeats are additional predictions of the same sequence, not additional proteins. Structural diversity is reported only for confidence-qualified, contiguous domain spans and actual successful searches; missing coverage remains explicit.

## What the structures establish

| Protocol | Verified first-pass candidate peptides | Candidates with qualified spans | Qualified candidate spans | Clusters containing candidates |
|---|---:|---:|---:|---:|
| boltz2_2.2.1_precomputed | 1 | 0 | 0 | 0 |
| boltz2_2.2.1_single_sequence | 43 | 2 | 7 | 2 |

Only 2/43 candidate models contain qualified spans; the remaining 41/43 are unclassified by this procedure. This limited coverage prevents a broad conclusion about chRNA fold diversity.

With the span-length and 80%-of-residues requirements fixed, candidate coverage is 3/43 at residue pLDDT ≥60, 2/43 at residue pLDDT ≥70, 0/43 at residue pLDDT ≥80. These are screening-threshold sensitivities, not alternate structural-cluster counts. See [gate sensitivity](diversity/gate_sensitivity.tsv).

Each eligible span is a contiguous Pfam alignment of at least 50 residues, with at least 80% of residues at pLDDT ≥70. Actual-coordinate Foldseek/TM-align comparisons require alignment TM-score ≥0.5 and coverage ≥0.8 on both spans. Clusters are graph connected components, so membership can be transitive. Overlapping annotations and repeats within one protein are not independent proteins. Control-only clusters are excluded from this table. These counts describe the selected, confidence-qualified subset; they do not estimate total chRNA fold diversity or establish new folds.

The robustness audit contains **24 same-protocol seed-pair comparisons**. Fitted coordinate RMSD measures prediction reproducibility, not thermodynamic stability. See [seed comparisons](analysis/seed_robustness.tsv), [junction confidence and cross-junction PAE](analysis/model_region_metrics.tsv), and [structural-diversity methods](diversity/METHODS.md). Missing qualified structure remains unresolved rather than classified as disordered or nonfunctional.

## Deliverables

- [Offline searchable atlas](report/index.html)
- [PowerPoint gallery](report/structure_campaign_gallery.pptx)
- [Figure generation and interpretation guide](report/FIGURE_GUIDE.md)
- [Cohort methods](cohort/METHODS.md), [disorder methods](analysis/METHODS.md), [domain methods](domains/METHODS.md)
- [Execution changes, constraints and reproduction commands](EXECUTION.md)
- [Frozen folding selection](selection/selection.tsv) and [diagnostic repeat selection](selection/seed_repeats/selection.tsv)
- [Joined candidate evidence table](analysis/candidate_evidence_table.tsv)

All derived campaign data and caches are under `results/structure_campaign/`. No claim of translation, novel function, druggability, or population-wide disorder prevalence follows from these predictions.
