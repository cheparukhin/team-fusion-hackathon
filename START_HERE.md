# Start here — Team Fusion

We connect chimeric-RNA evidence, conditional protein predictions and inspectable exon/structure views. The latest [team plan](https://docs.google.com/document/d/1suaqiVIxDCT2D8bvYndyFK6X1NSLv9tCG7VbrBRzrG4/edit?tab=t.ge1x7g3r1m8e) has three contributions.

## Three-minute judge walkthrough

1. **Dashboard:** open the [public RNA/exon/structure explorer](https://chimeric-rna-exon-structures.a-cheparukhin.chatgpt.site). Compare a pilot candidate with Gsdmd–Tmem106a, explicitly labeled a literature reference control that the pilot did not recover. Ten selected pilot hypotheses plus one control are shown; all ten pilot hypotheses have one supporting read in the sampled library.
2. **Ranking:** inspect [saved metrics](results/classifier/metrics.json). On 401 complete-contact pairs, RNA AP is 0.296 and RNA + Hi-C AP is 0.300; the paired interval spans zero. This does not establish ranking improvement or biological independence from 3D genome organization.
3. **Disorder:** inspect [the campaign report](results/structure_campaign/RESULTS.md). Among 188 conditional annotated-start hypotheses across 91 supported pairs, V3 classifies 42 as predominantly disordered and V1 classifies 18. These are predictions under sequence assumptions, not measured proteome prevalence. Full profiles and model files are available through the [evidence restore command](preservation/controller-20260920/README.md).

## Run locally

From the repository root, with Python 3:

```sh
python3 scripts/demo/serve.py
```

Open `http://127.0.0.1:8000/dashboard/` for the structure dashboard, `http://127.0.0.1:8000/demo/` for the ranking evidence explorer, or `http://127.0.0.1:8000/demo/review/` for the three recorded Codex review cases. No API keys or GPU are needed. The structure viewer loads pinned 3Dmol from a CDN and therefore needs internet; the recorded review cases are cached locally.

## Reproduce and present

[CPU installation and reconstruction](README.md#reproduce) · [Dashboard rebuild and provenance](dashboard/README.md) · [Final deck and submission gates](docs/submission/README.md).

After installing the locked CPU environment:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/review/verify.py
node tests/test_review_ui.mjs
```

The Node check tests application logic, not rendering. Fresh browser validation, final deck completion/access and human rehearsal remain open. [Current status](STATUS.md) · [Remaining gates](GAPS.md).

The separate [383-model folding supplement](results/folding_expansion/README.md) is an additional selected cohort, not the 188-hypothesis disorder cohort or the ten dashboard pilot candidates. Do not combine their denominators or seed protocols.
