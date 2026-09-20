# Sequence-led workflow in the final presentation

![Sequence-led chimeric RNA workflow](chimeric-rna-workflow.png)

This is the image embedded on slide 3 of the [current team presentation](https://docs.google.com/presentation/d/1qZ2owRuz6j3A48Y_XcheWADuoPh6HYkmn2NCLqFDybk/edit). It replaces the older cohort-summary illustration at this path.

The diagram describes the workflow architecture: callers, read support, rank/freeze, RNA-to-ORF reconstruction, folding, evidence comparison and delivery. Its completed focused implementation is documented in the [mouse pilot](../../workflows/mouse-pilot/README.md): one library, LongGF plus an independent alignment audit, 116 technically supported exact-junction proposals, and ten frozen reference-assisted folding hypotheses plus a separate literature control.

The JAFFAL/Genion boxes are broader caller branches, not completed multi-caller consensus for that pilot. “Every eligible distinct sequence” is a coverage goal, not a claim that every possible peptide or planned prediction finished; the pilot selected ten and the separate expansion has explicit missingness. “AF3 if accessible” is conditional, not a successful AF3 result. The presented cross-model example actually used [Boltz2, AF2 and ESMFold](../../results/structure_campaign/cross_model_gsdmd/README.md).

The diagram's RNA-only junction ordering is distinct from the [gene-pair RNA/Hi-C classifier](../../results/classifier/MODEL_CARD.md). Folding, disorder and published outcomes do not become ranking inputs. [Final scope and claim boundaries](../submission/README.md).
