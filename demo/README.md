# Offline demos

Start with the [scientist review](review/index.html): three recorded Codex cases, source-linked evidence and locally saved review receipts. The [full explorer](index.html) shows all 479 eligible probe-panel pairs and their saved out-of-fold scores.

From the repository root:

```sh
python3 scripts/demo/serve.py
# http://127.0.0.1:8000/demo/review/
# http://127.0.0.1:8000/demo/
```

Cached viewing needs no credentials or paid services. Receipts are browser-local and self-reported, not authenticated scientific endorsements. All three independent reviews are pending. The review page passes application-logic checks; real-browser and visual verification remain blocked by unavailable enforced browser-policy verification. Resolve that check before browser testing.

## Maintain the explorer

After model or report-input changes:

```sh
python3 scripts/demo/export.py
python3 scripts/demo/cache_agent_reports.py
python3 scripts/demo/export.py
```

Five source-grounded reports are Codex-authored cached prose; packaging does not regenerate them or invoke a model. Reports are reused only when input hashes match; other rows receive labeled deterministic summaries. The optional live adapter in `scripts/demo/reports.py` requires credentials and has not been validated with a live API call.

## Interpret the evidence

Reported NanoString support is pair-level evidence. Unreported support is not a biological negative, and assay/QC availability remains unknown. Scores are uncalibrated. Exact read/probe coordinates and missing evidence remain separate. GPU non-detection is not absence; Hi-C has no established ranking gain. No report is used as a training label or feature.

[Recorded tool replay and review instructions](../scripts/review/README.md) · [Model card](../results/classifier/MODEL_CARD.md) · [Current gaps](../GAPS.md)
