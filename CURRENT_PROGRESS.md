# Saved project checkpoint

This repository captures the Team Fusion working files from 20 September 2026. It is a progress checkpoint, not a declaration that the hackathon submission is complete.

## Start here
- [Working gap checklist](GAPS.md)
- [Detailed assessment and evidence](docs/hackathon-assessment/assessment.md)
- [Main project README and reproduction commands](README.md)
- [Source-file checkpoint manifest](CHECKPOINT_MANIFEST.json)
- [Validation receipt](CHECKPOINT_VALIDATION.json)

## Included
- At the repository root: the current `quick_hack` implementation, 479-pair reported-support experiment, Hi-C features and evaluation, cached evidence explorer, source-grounded reports, animation source/assets, presentation gallery, structure-related outputs and supporting scripts.
- Under [workflows/mouse-pilot](workflows/mouse-pilot/): the separate `chrna` pipeline's code, tests, documentation, reports, selected mouse scientific artifacts and a bounded K562 progress snapshot. Its historic absolute paths reflect the execution host; this archive has not been independently reproduced here.
- The original assessment and evidence snapshots, preserved with their timestamps. A presentation gallery was added by teammates after that assessment; its presence does not establish completion of the organiser's submission deck.

The published panel has 479 eligible ordered pairs and 109 reported NanoString-supported pairs. Neither the RNA model's AP comparison nor the incremental Hi-C comparison establishes a robust performance improvement. Unreported assay support is not a proven biological negative.

The separate mouse pilot reports 116 technically supported junctions and 10 frozen reference-assisted protein hypotheses plus one separate published-architecture control. The 11 structure outputs do not establish protein expression or function. The published Gsdmd–Tmem106a control is not de novo recovery.

The Parabricks pilot processed two million read pairs and found no fixed-criteria probe-junction matches. K562 progress is an in-progress snapshot; consult its timestamp, not this repository's creation time.

## Large files and exclusions
The 147 MB 4K animation is stored in the [checkpoint release](https://github.com/cheparukhin/team-fusion-hackathon/releases/tag/checkpoint-2026-09-20) rather than a normal Git file. Its expected SHA-256 is recorded in the manifest; lower-resolution animations and render sources are included.

Raw sequencing archives, reference/contact caches, model weights, Python environments, credential files, authentication caches and local infrastructure state are excluded. Fetch required public inputs using the documented commands. No GPU job or paid API call is triggered by cloning this repository.

## Provenance
The main workspace's source Git HEAD is recorded in the manifest. This checkpoint also contains uncommitted working files and keeps the separate pipelines under distinct paths. It does not rewrite or replace teammates' live checkout or the earlier public repository.

Use [GAPS.md](GAPS.md) as the next-work checklist; retain the dated assessment as the evidence for those priorities.

