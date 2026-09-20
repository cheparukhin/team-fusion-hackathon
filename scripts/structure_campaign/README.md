# Structure and disorder campaign

Recovered analysis source from `quick_hack`, now at the repository's normal
`scripts/structure_campaign/` path. The existing ranker, reviewed metrics, and
frozen folding supplement are unchanged. Unit tests are in
`tests/test_structure_campaign_*.py` and run with the core test suite.

Use the [controller recovery guide](../../preservation/controller-20260920/README.md)
to obtain the full input/output tree. Large score profiles, model coordinates,
confidence arrays, residue maps, report assets, and references live in release
assets, not Git history. For saved results, start with the
[reviewed recovered campaign](../../results/recovery_20260920/README.md).

Restore data into this repository with the command in the recovery guide. For
example, reconstruction then supports:

```sh
python scripts/structure_campaign/reconstruct.py --root . --output /path/to/new-reconstruction
```

Use a fresh output directory. This rebuilds from supplementary inputs and is not
required to inspect saved results. Optional disorder/domain/structure packages
are pinned in the adjacent requirement files; they are not dependencies of the
core ranker. Compute launchers are source only and are not invoked by tests.
