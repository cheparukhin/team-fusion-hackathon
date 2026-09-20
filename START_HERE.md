# Start here — Team Fusion

We help scientists decide which chimeric-RNA junction to test next. The example is a recorded, inspectable Codex review of three selected candidates. It does not claim prospective utility or new biological discovery.

## Watch the decision

1. Clone or download the public repository, keeping its directory structure. A complete [reviewed ZIP](https://github.com/cheparukhin/team-fusion-hackathon/releases/tag/submission-reviewed-2026-09-20) is also available.
2. Open `demo/review/index.html` in a browser. No API keys, GPU or package installation is needed to read the cached cases. For reliable local links, run `python3 scripts/demo/serve.py` from the repository root, then open `http://127.0.0.1:8000/demo/review/`.
3. Start with **Psap–Lgals3**. Inspect the **924-nt endpoint discrepancy**, the recorded comparison, and the source-linked proposal to reconcile original alignments before selecting an assay.
4. Switch to **Gsdmd–Tmem106a** and **Cd274–Lacc1** to see how weak or unavailable structure evidence is handled without dismissing published RNA findings.
5. A scientist may endorse, revise or defer a proposal and download a local review receipt. The demonstration is unsigned. A receipt is self-reported, stored only in that browser, and not an authenticated endorsement.

Browser interaction and visual verification of this new review page remain pending: the authoring browser tool could not verify its enforced security policy. Application-logic checks pass; the deck has been visually inspected separately.

## Present

[Current organiser-template deck and all four inspected slide previews](docs/submission/README.md). Three presented slides plus a non-presented appendix; planned five-minute script. This is the primary submission story. A [2:19 narrated evidence walkthrough](docs/submission/evidence-walkthrough.mp4) is available as a fallback, with synthetic narration clearly disclosed. Interactive demo recording and human rehearsal remain open.

## Verify

The ZIP's `SUBMISSION_MANIFEST.json` identifies its exact Git commit and SHA-256 for every bundled tracked file. GPU outputs are cached real artifacts; none of these reproduction commands provisions compute.

Install Python 3.12 and the locked environment using the [README instructions](README.md#reproduce), then run:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/review/verify.py
.venv/bin/python -m pytest -q
```

Core reconstruction downloads the pinned public source inputs with `.venv/bin/python scripts/reproduce.py --download`. The independent source-case audit is `.venv/bin/python scripts/review/audit_source_case.py` after those downloads. The rebuild reuses the audited cached Hi-C feature table. Detailed scope is in [clean CPU validation](results/reproduction/clean_cpu_validation.json).

## Interpret

- **Real evidence:** 479 eligible ordered pairs; 109 reported NanoString-supported pairs. Unknown support is not a proven negative.
- **No demonstrated Hi-C improvement:** AP 0.296 → 0.300, paired interval includes zero. No top-20 improvement over tied read counts.
- **Actual NVIDIA execution:** Parabricks on A100, two million paired reads. Bounded non-detection does not prove absence. Alignment-only runtime is not a CPU speedup measurement.
- **Actual OpenAI work:** Codex chose evidence checks, executed tools and authored source-linked decisions. Twelve recorded outputs replay exactly; this is not live inference.
- **Still pending:** independent biology signoff, prospective utility measurements, browser verification, rehearsal and deck sharing. See [GAPS.md](GAPS.md).
