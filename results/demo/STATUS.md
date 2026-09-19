# Demo worker — complete

Frozen against the final classifier and NVIDIA artifacts: **479 eligible pairs, 109 reported-support labels, 401 held-out Hi-C scores**. The demo serves real cached data and works without a network connection. No fixture values are included.

## Deliverables

- `demo/`: responsive ranked explorer; full-panel and matched-model scores; ordered-parent schematic; exact read-junction, sequence-mapped probe-junction, and probe-design records; reported versus unreported labels and explicit unknown assay/sample status; source-grounded reports; matched and interchromosomal evaluation; actual NVIDIA run panel. Existing `animation/v2/` assets reused without edits.
- `scripts/demo/export.py`, `serve.py`, `reports.py`: standard-library export/server and optional strict-schema OpenAI Responses API adapter. No API key was available and no Responses API call occurred.
- Five actual Codex-authored reports with source passages, instruction provenance, model identifier, exact inputs, and matching SHA-256 hashes. The remaining candidates show labeled deterministic factual summaries. `cache_agent_reports.py` packages existing authored prose; it does not invoke a model.
- `demo/README.md`, `results/demo/report_review.md`, and `results/demo/presentation.md`: commands, limitations, source review, and five-minute presentation with an explicit twenty-second actual NVIDIA-result segment.

## Final NVIDIA result

The selected Parabricks run used an NVIDIA A100-SXM4-80GB and **2,000,000 read pairs**. Alignment wall time was **85.49 seconds**, excluding setup. The output contains **28,482 raw chimeric records**, including **3,275 resolved split-junction records** eligible for matching. **Zero probe-panel junction matches** were found. This bounded negative result is not evidence that the candidates are absent; no CPU speedup is claimed.

Run summary, exact evidence rows, command/container logs, and provenance are linked in the Methods view. The quote-based shared instance cost estimate is **$1.35, not an invoice**; cleanup status is `deleted_and_watchdog_cancelled`.

Candidate `gpu_evidence` is a separate independently generated evidence stream: it is not a model feature, label, or input to the already-authored published-evidence reports. Missing output remains distinct from a genuine reported zero-support pilot. All five report hashes remain valid.

## Final verification

- **5 focused pytest tests passed**, including hallucinated citation/numeric rejection, missing-value/false parsing, real-input requirement, cohort/report hash integrity, and unavailable GPU output versus actual zero support.
- JavaScript syntax check passed.
- **Chromium browser checks passed**: 479 rows, 109 reported-support filter, search/selection/empty state, observed-only Hi-C ranking, matched score cards, evaluation, source links, actual NVIDIA status, 390-px mobile without horizontal overflow, direct `file://` offline loading, and no JavaScript errors.
- Refreshed screenshots: `explorer_desktop.png`, `evaluation_desktop.png`, `methods_desktop.png`, `nvidia_pilot.png`, and `explorer_mobile.png`. Explorer/evaluation/NVIDIA screenshots visually inspected.
- Browser/PDF tooling and runtime libraries were isolated under `/tmp`; no root dependency changes, Git mutations, credential logging, or edits to `animation/`.

## Commands

```bash
python scripts/demo/export.py
python scripts/demo/serve.py
# http://127.0.0.1:8000/demo/
.venv/bin/pytest -q tests/test_demo.py
node --check demo/app.js
# Optional installed Playwright validation:
LD_LIBRARY_PATH=/tmp/chrna-browser-libs/extracted/usr/lib/x86_64-linux-gnu PYTHONPATH=/tmp/chrna-demo-tools python3 scripts/demo/browser_check.py
```

After changing published report inputs, inspect the retained prose before running `python scripts/demo/cache_agent_reports.py`, then export again. GPU evidence is displayed independently and does not alter those report inputs.
