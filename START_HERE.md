# Start here — Team Fusion

The [FINAL tab](https://docs.google.com/document/d/1suaqiVIxDCT2D8bvYndyFK6X1NSLv9tCG7VbrBRzrG4/edit?tab=t.ge1x7g3r1m8e) defines three contributions. The [current slides](https://docs.google.com/presentation/d/1qZ2owRuz6j3A48Y_XcheWADuoPh6HYkmn2NCLqFDybk/edit) present the sequence workflow, a folding/disorder comparison, and the dashboard.

1. **Ranking:** inspect the [read/junction workflow](workflows/mouse-pilot/README.md) and its frozen evidence rules. The focused pilot produced 116 technically supported exact-junction proposals in one library. The separate [RNA/Hi-C benchmark](results/classifier/MODEL_CARD.md) evaluates reported support at gene-pair level; its null comparison does not demonstrate independence from 3D genome organization.
2. **Disorder and folding:** read the [188-hypothesis cohort result](results/structure_campaign/RESULTS.md) and the [118-aa Gsdmd–Tmem106a comparison](results/structure_campaign/cross_model_gsdmd/README.md) shown in the slides. Confidence, disorder and function must not be equated.
3. **Dashboard:** open the [public explorer](https://chimeric-rna-exon-structures.a-cheparukhin.chatgpt.site). Ten selected pilot hypotheses are shown with a separate Gsdmd–Tmem106a literature control that the pilot did not recover. The pilot hypotheses each have one supporting read in the sampled library.

## Run locally

```sh
python3 scripts/demo/serve.py
```

Open `http://127.0.0.1:8000/dashboard/` for the presented viewer or `/demo/` for the gene-pair explorer. The dashboard uses a pinned 3Dmol CDN library. Cached viewing requires no credentials or paid inference.

[CPU benchmark reproduction](README.md#reproduce) · [Dashboard rebuild](dashboard/README.md) · [Evidence restore](preservation/controller-20260920/README.md) · [Claim-to-evidence map](docs/submission/README.md).

After installing the CPU environment, run `python3 scripts/check_docs.py`, `.venv/bin/python -m pytest -q`, and `.venv/bin/python scripts/review/verify.py`. Optional saved-model tests require restored evidence and `gemmi`. `node tests/test_review_ui.mjs` checks the supplemental review app's logic, not browser rendering.

The 188 disorder hypotheses, ten dashboard candidates, and separate 383-model folding supplement are different cohorts. [Current status](STATUS.md) · [Remaining limitations](GAPS.md).
