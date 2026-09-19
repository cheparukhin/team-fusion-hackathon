# Hi-C feature extraction completed

Real public processed contact maps downloaded from GSE324391: siNeg LPS biological replicates GSM9574808, GSM9574809, GSM9574815. Their binary headers contain 500-kb resolution although GEO text omits it. Assembly is mm39/GRCm39. SHA256 checksums and download URLs are in download_manifest.json.

The input is independently sequence-mapped probe endpoints from results/dataset_reconstruction/probe_junctions.tsv, converted from 1-based inclusive terminal bases to 0-based 500-kb bins. Ordered pair identity is retained. Matrix orientation may transpose only for symmetric chromosome lookup. Distinct probe bin pairs are deduplicated within each pair.

Explicit KR normalization vectors mask invalid/nonpositive bins before sparse windows are formed. SHA256 input integrity is verified before extraction.

Features use KR normalization (GENOVA Juicer balancing=TRUE), an 11×11 window, median central 3×3 foreground and median of 64 pixels four-quadrant background. Zero/undefined background, chromosome-edge windows, missing normalization, and cis bin distances below 500 kb remain unavailable. Feature=log2(0.5+enrichment). Per-loop GENOVA raw arrays are not clipped by the aggregate-only outlier filter.

**Deviation:** the paper describes pooled replicates before processing. Deposited files are individual replicate .hic maps. This pilot averages enrichment over distinct bin pairs within each independently KR-normalized replicate, then equally averages replicate ratios. The primary feature requires all three replicates. This is not an exact pooled-matrix reproduction. Hi-C is 6 h LPS, whereas RNA experiments differ in stimulation/timing. CTCF-knockdown maps are excluded.

446 pairs across the entire published candidate collection have all 3 replicates;401/479 model-eligible pairs have complete features.78 eligible pairs are unavailable and none has usable partial replicate coverage. features.tsv exposes missingness/QC; bin_pair_contacts.tsv contains auditable numeric foreground/background values.

Reproduce:

```bash
.venv/bin/python scripts/compute/download_hic.py
PYTHONPATH=src .venv/bin/python scripts/compute/extract_hic_features.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hic.py -q
```

Tests passed: coordinate boundaries, GENOVA quadrant masks, undefined background, chromosome edges, ordered-pair aggregation, replicate completeness, and STAR endpoint matching. Raw .hic files are cached locally and must not be committed.
