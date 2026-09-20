# Sequence-led RNA ranking and mouse/K562 workflows

The focused mouse pipeline supports the FINAL tab's ranking contribution and the presented dashboard. It assesses read/junction evidence, ranks RNA proposals, freezes a shortlist, and reconstructs conditional junction-spanning ORFs before folding. It is distinct from the root repository's gene-pair logistic-regression/Hi-C benchmark.

## Completed focused mouse pilot

The SRR28984805 pilot assessed 9,167 split reads, recorded 6,466 exact-junction proposals and classified 116 as supported by its technical rules. LongGF and an independent supplementary-alignment audit were executed. One sample and one caller do not establish replication or multi-caller consensus. The broader workflow diagram's JAFFAL/Genion boxes and all-eligible folding goal do not mean every branch completed here.

The pilot froze ten reference-assisted hypotheses for folding, with selection and deferrals recorded. All ten selected pilot hypotheses have a single supporting read in this library. A separately reconstructed Gsdmd–Tmem106a literature control was added for comparison; it was not recovered by the pilot. These are the eleven records displayed in the [dashboard](../../dashboard/README.md).

- [Data contract](docs/data_contract.md)
- [Prespecified pilot rules](docs/focused_pilot_rules.md)
- [Frozen selection rules](runs/focused-pilot-20260919/selection/selection_rules.md)
- [Discovery receipt](runs/focused-pilot-20260919/discovery-validation.json)
- [Completion audit](runs/focused-pilot-20260919/completion-audit.json)

The prespecified rules are dated experiment records, not authorization to repeat historical compute. Missing support and unresolved reconstructions remain unknown biological truth.

## Run and inspect

[Restore saved evidence](../../preservation/controller-20260920/README.md) into these existing paths. Full raw-read reruns additionally need the original public inputs, pinned reference/index and external tools. Use a separate environment for this workflow's `chrna` package; its module name is also used by the root benchmark.

```sh
cd workflows/mouse-pilot
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/chrna --help
```

The `pilot-literature` subcommand traces published read IDs in a supplied FASTQ while keeping literature inclusion separate from discovery support. It writes to a new output directory and does not change the RNA ranking. Structure/caller and Linux watchdog checks require their documented external dependencies.

## Supporting K562 extension

K562 is retained as an additional workflow, not a fourth headline contribution. Completion metadata reports 8/8 stages and five cross-library junction overlaps; the ranker and read-count baseline both recover five top-20 overlaps. No ranking gain is established. [K562 rules](runs/k562-pilot/20260919-overnight/rules.md) and restored run evidence keep these results separate from the mouse pilot and NanoString panel.

[Current project scope](../../docs/submission/README.md) · [Remaining checks](../../GAPS.md).
