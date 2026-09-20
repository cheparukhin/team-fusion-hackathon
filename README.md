# chRNA evidence prioritization

**Current submission:** [start here](START_HERE.md) · [verified status](STATUS.md) · [gaps and action plan](GAPS.md)

An evidence-review assistant that helps scientists decide which chimeric-RNA junctions merit experimental follow-up. It checks the evidence behind a ranked pair, distinguishes conflicts from missing information, and proposes the next discriminating check for scientist review.

The underlying ranking experiment tests whether 3D genome context adds useful signal. This is a retrospective proof of concept, not a claim of new biological discovery or measured improvement in scientific productivity.

The reconstructed probe panel contains **479 eligible ordered gene pairs, including 109 reported NanoString positives**. Five-fold evaluation keeps all pairs sharing any parent gene in the same fold. The label is **reported NanoString support**, not RNA authenticity; an unreported candidate is not a proven negative.

In **our retrospective evaluation** on the **401 pairs with complete Hi-C evidence**, average precision is **0.296 for RNA features versus 0.300 with Hi-C**. The paired difference is +0.00364, with a 95% component-bootstrap interval of [−0.0310, +0.0469]: this experiment **does not establish an improvement from Hi-C**. These are our calculated results, not paper-reported metrics; see [saved evaluation](results/classifier/metrics.json) and [scientific review](docs/submission/SCIENTIFIC_REVIEW.md). The useful deliverable is an audited, leakage-controlled experiment and an evidence explorer that makes that result inspectable.

## Replay the scientist’s decision

**[Open the scientist review demo](demo/review/index.html)** — three cases, recorded evidence checks, and a downloadable local review receipt.

Three [recorded review cases](results/review/case_freeze.json) contain actual Codex-selected tool calls and source-linked decisions. Start with [Psap–Lgals3](results/review/psap-lgals3/decision.json): its high pair-level score hides a probe/read junction discrepancy. The review rechecks real NVIDIA Parabricks output and recommends resolving the junction before choosing an experiment.

[Tool and replay instructions](scripts/review/README.md) · [Gsdmd–Tmem106a](results/review/gsdmd-tmem106a/decision.json) · [Cd274–Lacc1](results/review/cd274-lacc1/decision.json). Human review is pending; these selected cases are not a blinded utility study.

## Submission presentation

[Three-slide organiser-template deck, technical appendix and timed script](docs/submission/README.md). This is the current submission narrative. The slide previews were visually inspected; independent biology review, final release publication and Google Slides sharing remain pending. The repository is public.

## Open the demo

```bash
.venv/bin/python scripts/demo/serve.py
```

Open **`http://127.0.0.1:8000/demo/review/`** for the scientist-review story, or `http://127.0.0.1:8000/demo/` for the full evidence explorer. The browser loads cached data, evidence, and reports without external services. From your own computer with Brev authenticated, run `brev port-forward chrna-controller -p 8000:8000`, then open the same URL. The static `demo/index.html` also embeds its data through `data.js`; linked provenance and animation are easiest to use through the local server.

## Reproduce

Python 3.12 and `uv` are used here. To rebuild the environment:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.lock
```

The optional native Hi-C reader needs a C++ compiler, Python headers, libcurl and zlib headers; on Ubuntu these are `g++ python3-dev libcurl4-openssl-dev zlib1g-dev`.

Rebuild from the cached published inputs and cached Hi-C feature table:

```bash
.venv/bin/python scripts/reproduce.py
.venv/bin/python -m pytest -q
```

On a fresh checkout, download the pinned tables and GENCODE annotation while reusing the bundled, audited Hi-C feature table:

```bash
.venv/bin/python scripts/reproduce.py --download
```

To also reconstruct contact features from the three public processed Hi-C files (~1.5 GB):

```bash
.venv/bin/python scripts/reproduce.py --download --download-hic
```

To explicitly run the RNA-only fallback:

```bash
.venv/bin/python scripts/reproduce.py --download --rna-only
```

No reproduction command provisions GPUs or invokes paid APIs. Parabricks execution and optional live OpenAI reports are separate, documented operations. Source checksums, annotation releases, and random seed are recorded in the generated manifests.

## What is implemented

- **Data:** published long-read catalogue and NanoString panel joined to GENCODE M28/GRCm39; probe sequences resolve ambiguous design suffixes and map to exact parent coordinates. Unique read IDs are counted once. The 529 probe designs map to 527 pairs; 48 unresolved biological candidate/control pairs are excluded, leaving 479.
- **RNA model:** fixed L2 logistic regression on log read support, chromosome relationship, and genomic separation. Sample recurrence is unavailable in the published tables and contributes no signal. Imputation and scaling are fitted within each training fold.
- **Spatial model:** the same model plus a 500-kb Hi-C contact-enrichment feature. The primary comparison trains and evaluates both models on identical complete-contact rows within the original gene-disjoint folds. Missing Hi-C uses the separately evaluated RNA-only model.
- **Evaluation:** average precision, expected supported pairs in the top 20 (averaged over tied scores), interchromosomal results, and component-bootstrap uncertainty. See `results/classifier/metrics.json` and `results/classifier/MODEL_CARD.md` for the actual results and limitations.
- **Exploratory application:** the RNA-only refit ranks 29,911 already published candidates outside the probe panel. These scores are unvalidated outside the selected training population; out-of-range features are flagged. They do not establish new chRNAs.
- **NVIDIA execution:** Parabricks 4.7.1-1 aligned 2,000,000 validated paired reads from SRR37513722 on an A100 80 GB in 85.49 seconds (alignment only). Its output contains 3,275 split-junction records and 25,207 encompassing-mate records. No sequence-mapped probe junction matched the fixed chromosome/strand/±10-nt criteria. This bounded sample does not establish absence; the evidence remains separate from training labels and features. No CPU speedup is claimed.
- **Evidence explorer:** real pair/junction/probe evidence, honest missingness, quantitative comparison, and cached source-grounded candidate reports. OpenAI workflow provenance distinguishes Codex-authored cached reports, deterministic summaries, and live API output.

GPU run provenance and its quote-based cost estimate are in `results/compute/spending_manifest.json`; this is not a live billing total.

## Scientific limits

NanoString panel selection and uncertain testing/QC status limit the target. Pair-level reporting cannot validate every junction isoform. Hi-C contacts are coarse regional evidence, with assay timing different from the RNA experiments. The paper pooled Hi-C replicates before processing; this pilot averages independently KR-normalized per-replicate enrichment ratios and requires all three replicates. It is not an exact reproduction of the paper's pooled Hi-C analysis. A positive model coefficient or higher score does not establish causality, translation, function, or druggability.

No hyperparameter search, post-hoc threshold optimization, or test-set-driven feature selection is used. Scores are not calibrated biological probabilities. Bootstrap intervals describe fixed out-of-fold predictions rather than retraining uncertainty.

## Artifacts

| Directory | Contents |
|---|---|
| `results/dataset_reconstruction/` | Audited dataset, source manifest, exact read/probe mappings |
| `results/classifier/` | Features, folds, held-out predictions, model files, metrics, figures, catalogue rankings |
| `results/hic/` | Candidate contacts, feature/QC table, source and extraction manifests |
| `results/compute/` | Actual GPU execution and budget provenance |
| `results/demo/` | Source passages, cached reports, screenshots and browser checks |
| `results/structures/` | Verified model/reference coordinates, confidence, renderings and provenance |
| `demo/` | Offline evidence explorer |
| `animation/` | Existing separately developed biology explainer |

Large raw sequencing/contact files and downloaded reference assets are excluded from Git. Model files are trusted local joblib artifacts; do not load untrusted pickle/joblib files.

Primary source: [Venezia et al., Nature (2026)](https://www.nature.com/articles/s41586-026-10982-x). See the source manifest for exact supplementary files and GENCODE inputs.

## Submission bundle

The repository is public, but the current candidate release is still a draft at `e908480`; anonymous judges cannot download it. The older public “Latest” release is the initial checkpoint. The draft ZIP intentionally preserves its recorded source commit and does not include later documentation updates.

After committing the intended files, run `.venv/bin/python scripts/package_submission.py`. The ZIP in `dist/chrna_submission.zip` contains tracked code/artifacts and an internal SHA-256 manifest, with raw caches excluded.
