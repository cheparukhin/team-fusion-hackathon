# Partial cross-species liver workflow

Supporting work for the FINAL tab’s open cross-species direction; not a completed conservation claim.

Calling, reference preparation, ordered-pair comparison, and review
scripts from `quick_hack/cross-species`. This workflow is separate from the
primary ranking experiment. Its partial human/cow comparison does not establish
conserved exon junctions, population prevalence, or species-level absence.

The [earlier reviewed recovery](../../results/recovery_20260920/README.md)
records the scientific scope. The [controller preservation release](../../preservation/controller-20260920/README.md)
contains the complete selected saved result tree, manifests, orthology tables,
reference-adaptation records under
this directory after running the restore command. Raw downloads and installed callers must be
obtained separately where a full rerun requires them.

Source-only ordered-pair checks:

```sh
python workflows/cross-species/tests/test_pair_comparison.py
```

Reference-adapter and caller integration tests require their external tools.
Run full workflow commands here after restoring evidence to preserve relative
paths. Review environment, input manifests, and historical run limits first;
archiving a launcher does not execute or authorize new compute.
