# Team Fusion — chimeric RNA evidence and protein hypotheses

Our project follows the **FINAL tab** of the [shared team document](https://docs.google.com/document/d/1suaqiVIxDCT2D8bvYndyFK6X1NSLv9tCG7VbrBRzrG4/edit?tab=t.ge1x7g3r1m8e): **RNA ranking, fusion-protein disorder analysis, and a fusion-protein dashboard**.

[Presentation slides](https://docs.google.com/presentation/d/1qZ2owRuz6j3A48Y_XcheWADuoPh6HYkmn2NCLqFDybk/edit) · [Start here](START_HERE.md) · [Claims and evidence](docs/submission/README.md) · [Status](STATUS.md)

We built computational tools to prioritize chimeric-RNA evidence and inspect conditional protein reconstructions. Functional chimeric proteins reported by [Venezia et al.](https://www.nature.com/articles/s41586-026-10982-x) motivate the work. This project does not establish new functional proteins or drug targets.

## The three contributions

| Contribution | What was delivered | Evidence and code |
| --- | --- | --- |
| **RNA ranking** | Read/junction assessment and a frozen RNA-only shortlist; a separate gene-pair RNA/Hi-C benchmark | [Mouse pilot workflow](workflows/mouse-pilot/README.md), [benchmark model card](results/classifier/MODEL_CARD.md) |
| **Disorder and folding comparison** | Sequence-based disorder/domain analysis of conditional peptide hypotheses, plus a Gsdmd–Tmem106a comparison across Boltz2, AlphaFold2 and ESMFold | [Cohort results](results/structure_campaign/RESULTS.md), [model disagreement](results/structure_campaign/cross_model_gsdmd/README.md), [analysis source](scripts/structure_campaign/README.md) |
| **Fusion-protein dashboard** | Linked RNA, exon-origin and predicted-structure views for ten mouse pilot hypotheses and a separate literature control | [Public dashboard](https://chimeric-rna-exon-structures.a-cheparukhin.chatgpt.site), [portable viewer and rebuild](dashboard/README.md) |

The focused mouse pilot assessed one library with LongGF and an independent alignment audit, retained 116 supported exact-junction proposals, and froze ten reference-assisted protein hypotheses. These are technical support calls, not experimentally validated biological positives. The slide's broader multi-caller workflow is not a claim that every caller completed for every dataset.

The separate probe-panel benchmark contains 479 eligible gene pairs with 109 reported NanoString-supported pairs. On the same 401 complete-Hi-C pairs, RNA average precision is **0.296**, versus **0.300** with Hi-C; the paired interval spans zero. This does not establish a predictive gain or biological independence from 3D genome organization. Unreported support remains unknown rather than a verified negative.

The supported-cohort reconstruction yields **188 conditional annotated-start peptide hypotheses from 91 of 109 pairs**. Metapredict V3 calls 42/188 predominantly disordered; V1 calls 18/188. Predictors are reported separately, not combined into a calibrated fitness score. Predicted disorder, model confidence, protein function and druggability are different quantities. See the [claim-to-evidence map](docs/submission/README.md) for denominators and limitations.

## View the outputs

From the repository root, with Python 3:

```sh
python3 scripts/demo/serve.py
```

Open `http://127.0.0.1:8000/dashboard/` for the presented structure viewer or `http://127.0.0.1:8000/demo/` for the gene-pair ranking explorer. The dashboard needs internet for its pinned 3Dmol library; it needs no API key, GPU, or live inference. The optional three-case evidence-review companion is at `/demo/review/`.

Full disorder profiles, model coordinates, report assets and distinct run evidence are **GitHub release assets, outside Git history**. [Download and restore them](preservation/controller-20260920/README.md) into the existing workflow paths. After restoration, the structure report is at `/results/structure_campaign/report/`. Repository summaries can be read without downloading those data.

## Reproduce

For the gene-pair benchmark, use Python 3.12 and the locked CPU environment:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-core.lock
.venv/bin/python scripts/reproduce.py --download
.venv/bin/python -m pytest -q
```

`--download` fetches pinned study tables and annotation while reusing the bundled Hi-C feature table. With input caches already restored, omit it. To rebuild contacts from the public processed Hi-C files, install the optional native reader from `requirements.lock`, then use `--download --download-hic`. `--rna-only` runs the explicit RNA-only fallback. These commands do not provision GPUs or invoke paid APIs.

- [Read/junction workflow and frozen rules](workflows/mouse-pilot/README.md)
- [Disorder/folding analysis and optional dependencies](scripts/structure_campaign/README.md)
- [Dashboard rebuild from bundled inputs](dashboard/README.md)
- [Restore and verify saved evidence](preservation/controller-20260920/README.md)
- [Documentation link and artifact checks](scripts/check_docs.py): `python3 scripts/check_docs.py`

## Other retained work

The [three recorded evidence reviews](scripts/review/README.md), [bounded Parabricks alignment](results/compute/STATUS.md), [separate 383-model folding supplement](results/folding_expansion/README.md), [partial cross-species study](workflows/cross-species/README.md), and K562 extension are inspectable supporting work. They do not add extra headline claims to the FINAL tab or establish full-cohort completion, conservation, measured scientific utility, or new protein function.

The current Google Slides deck is the presentation. Superseded local decks, previews and narrated exports were removed after checking their copies in the earlier published release. [Presentation scope and remaining checks](docs/submission/README.md) · [Open questions](GAPS.md).
