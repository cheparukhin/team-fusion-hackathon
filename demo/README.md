# chRNA evidence explorer

This static, offline-capable explorer displays the **479 eligible probe-panel ordered pairs**, with real saved out-of-fold scores and original evidence provenance. It does not present the complete discovery catalogue as the evaluation population. The full catalogue and exploratory refit rankings are linked separately.

From the repository root:

```bash
python scripts/demo/export.py
python scripts/demo/cache_agent_reports.py
python scripts/demo/export.py
python scripts/demo/serve.py
# Open http://127.0.0.1:8000/demo/
```

Opening `demo/index.html` directly also works for the cached UI. The local server makes source artifact links convenient. No network, JavaScript package manager, or Python third-party package is needed for export, report packaging, or serving. Run `python scripts/demo/export.py` after model changes; cached reports are used only when their source-input SHA-256 matches. Stale reports fall back to clearly labeled deterministic summaries.

## OpenAI usage, stated precisely

Five reports were authored by the Codex agent from the real candidate rows and primary-source PDF passages: Gsdmd:Tmem106a, Cd274:Lacc1, Psap:Lgals3, Rb1:Itm2b, and Aoah:Sirt5. Their generator is **Codex agent-authored · cached (no API call)**. The authored prose is preserved in `results/demo/agent_report_drafts.json`; the packaging command does not invoke a model or pretend to regenerate that prose. Cached reports retain the model identifier, report instructions, the authoring-task excerpt, input snapshot, source references and input hash.

The other candidates show a deterministic factual summary. No API credential was available during implementation; **no OpenAI Responses API call was made**. A real API adapter is provided separately:

```bash
# Set OPENAI_API_KEY securely in the environment; never put it in source code.
python scripts/demo/reports.py --live --model gpt-4.1-mini --limit 5
python scripts/demo/export.py
```

`--pair Gsdmd:Tmem106a` (repeatable) selects candidates. `OPENAI_MODEL` can supply the model. The adapter calls the Responses endpoint with `store:false` and a strict JSON schema, rejects incomplete responses and unknown citations, checks numeric tokens against cited source inputs, and validates structured numeric claims against exact evidence fields. Model availability and account access remain untested. API failures do not silently become successful generated reports. See the [official structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs).

Automatic citation/numeric screening is not semantic entailment verification. The five authored reports were manually reviewed against the retrieved primary passages and candidate rows, including supported, unreported, and missing-data cases. Any newly generated API reports still need substantive source review before presentation. None of these reports is a training feature or label.

## Evidence boundaries

- NanoString membership is reported **pair-level support**, not authenticity or isoform validation. Not reported is distinct from unknown testing/QC.
- Raw junctions, sequence-mapped probe junctions, probe designs, read IDs, coordinates, assembly, source rows, and provenance are retained separately.
- Missing sample counts and contacts are never converted to zero. Short-read reporting is displayed as orthogonal published evidence.
- Full-panel RNA scores and matched-contact ablation metrics are separate evaluation populations. The latter uses the saved matched-cohort methods from `metrics.json`.
- Hi-C feature provenance and normalization deviations are linked. Bootstrap intervals are shown; an interval spanning zero does not establish benefit.
- NVIDIA status is read from `results/compute/pilot_summary.json`. Candidate GPU evidence is included only if `results/compute/evidence.tsv` exists, preserving reported zero support separately from missing output. It is neither a model feature/label nor part of the published-evidence report input; those existing report hashes remain unchanged by this separate evidence stream.
- The optional animation is read from the existing `animation/v2/` work and is explicitly conceptual.

## Verification

```bash
.venv/bin/pytest -q tests/test_demo.py
node --check demo/app.js
```

Optional real-browser test, with Playwright and Chromium separately installed, while the server runs on port 8000:

```bash
python scripts/demo/browser_check.py
```

Screenshots and the browser check record are under `results/demo/`. The supplied PDF passages were extracted with isolated pypdf 6.19.0 and retain their PDF checksum/page locations; runtime uses the checked-in snapshots.
