# Evidence review

The active Codex assistant selected and executed bounded evidence tools on the shared Brev CPU, read their outputs, and wrote three source-linked decisions. Each run retains the actual action reason, timestamp, elapsed tool time, implementation hash, input file hashes and output. These are selected demonstration cases, not a prospective evaluation or an unattended Responses API agent. No new GPU job or hosted NIM call is claimed.

The important decision is what to do with conflicting or missing evidence:

- **Psap:Lgals3:** the high pair-level score does not resolve the probe/read junction discrepancy. Review the original reads before choosing a junction-specific experiment.
- **Gsdmd:Tmem106a:** published RNA support and a low-confidence predicted structure can coexist. The structure does not establish protein function.
- **Cd274:Lacc1:** missing structure and bounded pilot non-detection do not negate published RNA evidence.

## Run a check

From the repository root, use the installed environment:

```sh
python scripts/review/evidence.py --pair Psap:Lgals3 \
  --tool compare_probe_junctions --run results/review/new-review \
  --reason "Check which read junction is represented by the designed probe."
```

Available tools: `retrieve_candidate`, `compare_probe_junctions`, `rematch_parabricks`, `inspect_structure`, `retrieve_sources`. The calling agent chooses tools from this allowlist, with at most eight calls per run. Completed decisions freeze the run. Unknown ordered pairs are rejected. Inputs are treated as data, not executable instructions.

`rematch_parabricks` checks the actual GPU output hash and re-executes the existing strand-aware matcher at the original ±10-nt tolerance. It does not merely read the cached count. The pilot is a two-million-read-pair deterministic prefix sample; a zero is not proof of absence. `inspect_structure` verifies coordinate-file integrity and reports manifest confidence; it does not refold proteins.

## Replay and inspect

```sh
OPENBLAS_NUM_THREADS=1 python scripts/review/verify.py
PYTHONPATH=src pytest tests/test_review.py -q
```

Replay recomputes outputs, checks the recorded implementation hash and source hashes, and resolves every decision evidence pointer. A regenerated `demo/data.json` may have a different timestamp; this is explicitly reported and accepted only when the entire relevant tool output is identical. All other source changes fail verification.

Decision prose received a qualitative review by the active Codex assistant against the referenced evidence. Pointer validation cannot prove that prose follows from its source. An independent biology reviewer has **not** signed off. Experiment suggestions are proposals only, and human review remains pending. No time-saving, accuracy gain, or wet-lab success has been measured.

The selected-case freeze is in `results/review/case_freeze.json`. Tool durations exclude model reasoning and human work and must not be presented as end-to-end review time.
