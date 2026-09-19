# Data contract and limitations

## Granularity

`candidate_pairs.csv` has one row per ordered gene pair represented by the NanoString probe panel. It aggregates the study's long-read evidence; it is not specimen-level data. All coordinates use the paper's GRCm39 annotation context. The code does not lift over coordinates.

`probe_sequences.csv` contains original IDs, plate, sequence, source Excel row and sequence hash. These are published 120-base probe-design windows, not measured full-length RNA sequences. The junction offset is deliberately missing because Table 8 does not explicitly supply it. Do not assume an offset of 60 without independent sequence/reference verification.

Five reviewed `_2` probe aliases are mapped to pair IDs for lookup only. Two pairs have two distinct probe windows. All original IDs remain present; their pair-level confirmation cannot identify which probe variant was supported.

`catalogue_junctions.csv` groups Table 3's read records by its repaired genomic junction. A gene-pair label must not be promoted to a confirmed exact-junction label without establishing a sequence match.

## Outcomes

`nanostring_reported_support=True` means the pair appears in Supplementary Table 7's NanoString list. False means **not listed as supported**, not a proven false RNA. `biological_negative_label` is empty for every row. Full failed-assay and QC outcomes are unavailable from this list.

Short-read support is another published evidence source. It is a legitimate comparator for NanoString-list recovery, but is not an RNA-seq-only prospective prediction if unavailable at deployment. These tools can have correlated sensitivities. The confirmation assays are not an exhaustive biological truth set.

No feature file includes NanoString outcome or protein validation. Do not add outcome-derived columns to a model input. The study's flagship protein is identified only in the separate outcome table for explanatory review.

## Matching and exclusions

Exact ordered names are joined to Table 3. Reverse-name and absent-name records retain missing read support and are excluded from the common baseline pool. A failed lookup must not become zero reads or a negative example. Unmatched names are exported for review.

Table 3 has no sample-to-read mapping. Per-condition reproducibility and expression cannot be inferred from its aggregate counts. Genomic distance is missing for interchromosomal pairs and pairs with multiple repaired junctions, rather than an arbitrary numeric zero.

## Splits and metrics

We form connected components of shared parental genes and identical probe sequences, using all panel features but no outcomes. Components are assigned deterministically to five size-balanced folds; fold 4 is held out. This is stronger than pair-only splitting, but not a full sequence-homology split. Homologous genes can still leak information and must be addressed before claims of family-level generalization.

Top-k recovery uses an analytical expectation across ties. Reported 95% ranges describe random tie-breaking variability only; they are not sampling confidence intervals and do not account for biological label uncertainty.

The pilot measures retrieval of published RNA support within an author-selected panel. It cannot estimate biological false-positive rate, protein translation, functional importance or novelty.
