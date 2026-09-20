# Mouse/K562 workflow

This directory contains the supplementary alignment and junction-assessment pipeline. The primary submission is the [three-case evidence review](../../START_HERE.md); this workstream is outside its scientific claims.

K562 completion metadata reports 8/8 stages and five cross-library junction overlaps. The ranker and read-count baseline both recover five top-20 overlaps, so no ranking advantage is established. The bundled workflow outputs do not include the entire completed run; do not treat this directory as its final release.

Retained contracts and prespecified rules:

- [Data contract](docs/data_contract.md)
- [Focused pilot rules](docs/focused_pilot_rules.md)
- [Frozen selection rules](runs/focused-pilot-20260919/selection/selection_rules.md)
- [K562 rules](runs/k562-pilot/20260919-overnight/rules.md)

Code, data and machine-readable provenance are preserved. Current project priorities are maintained only in [GAPS.md](../../GAPS.md).

## Recovered controller work

The [controller preservation release](../../preservation/controller-20260920/README.md)
now preserves the selected complete saved mouse/K562 run trees, newer source,
at the existing paths. These saved runs retain their original limits;
they do not change the primary submission claims above.

The recovered `pilot-literature` CLI subcommand is integrated here with its
original focused tests. It traces published read IDs in a supplied FASTQ while
keeping literature inclusion separate from discovery support:

```sh
PYTHONPATH=workflows/mouse-pilot/src python -m chrna.cli --help
```

Call `chrna pilot-literature --help` after installing this workflow package for
its required paths. It writes only to a new output directory and does not alter
the discovery ranking. Newer controller scripts are integrated here. Superseded project/dashboard
copies were discarded; distinct saved evidence is in the release.
