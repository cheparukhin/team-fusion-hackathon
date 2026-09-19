# Execution status

The minimal scientific experiment and offline demo are complete and independently reviewed.

- Dataset: 479 eligible ordered pairs, including 109 reported NanoString positives; exact identities and source hashes preserved.
- Evaluation: five gene-disjoint folds; RNA baseline and matched RNA/Hi-C comparison complete.
- Hi-C: 401 complete-contact pairs; normalization missingness corrected and independently verified.
- Result: incremental Hi-C AP +0.00364, 95% interval [−0.0310, +0.0469]; improvement not established.
- Demo: 479 pairs, 401 Hi-C scores, five cached Codex-authored cited reports, and actual GPU evidence kept separate from model labels and features.
- Verification: 23 focused tests pass. Single-command cached reproduction preserves the independently reviewed classifier metrics exactly. Desktop, mobile, and offline browser checks pass.
- NVIDIA: Parabricks 4.7.1-1 aligned 2,000,000 validated paired reads on an A100 80 GB in 85.49 seconds, excluding reference setup. BAM integrity checks passed. Output: 3,275 split-junction records and 25,207 encompassing-mate records; zero fixed-criteria probe-panel matches. Independent review confirmed these counts and non-detection. The successful 200,000-pair pilot is archived separately.
- Compute: the new instance kerxx8tqg was deleted after verified local export; its watchdog was cancelled. Quote-based lifecycle cost estimate: $1.35, not an invoice. Preexisting and separately created resources were preserved.
- OpenAI: five actual Codex-authored cached evidence reports; the optional Responses API adapter was not invoked without a key.
- Submission: tracked source, reviewed results, demo, presentation runbook, animation renderer/reference inputs, and an internal SHA-256 manifest are bundled by scripts/package_submission.py. Raw sequencing/reference/contact caches remain excluded.

See README.md for run commands and results/presentation/key_results.md for presentation claims.

## Presentation update

Dataset artifacts now use results/dataset_reconstruction/, with unchanged scientific rows, folds, predictions and metric values. A twelve-slide visual PowerPoint gallery, exact candidate exon diagrams, figure-generation/interpretation guide, experimental GSDMD parent structure and sequence-verified cached Boltz2 chimera model are included. The candidate model has low confidence (mean pLDDT 48.7); no experimental chimera structure or druggability claim is made. Other candidate protein models remain explicitly unavailable. Structure rendering reused verified coordinates and incurred no new GPU allocation.
