# NVIDIA pilot completed and compute cleaned up

A real NVIDIA Parabricks 4.7.1-1 `rna_fq2bam` run completed on mouse inflammatory BMDM sample GSM9569462 / SRX32404271 / SRR37513722. It used the full GRCm39 primary assembly, GENCODE M28 annotation and a STAR 2.7.2a index. Chimeric output was explicitly enabled. The selected run used the first 2,000,000 paired 151-nt reads; pairing, count, length and input SHA256 checks passed.

| Actual run | Alignment wall time | Raw chimeric records | Resolved split records | Probe-panel matches |
|---|---:|---:|---:|---:|
| Initial 200,000 pairs | 47.77 s | 2,849 | 314 | 0 |
| Selected 2,000,000 pairs | 85.49 s | 28,482 | 3,275 | 0 |

The larger run was the single authorized extension after the initial zero-match result. It reused the same reference, index and instance. Its remaining 25,207 records are encompassing mate pairs, which are excluded from exact junction matching. Both outputs passed `samtools quickcheck`. No CPU benchmark was run; these wall times are not a speedup claim.

**Interpretation:** this demonstrates a working GPU RNA alignment/evidence pipeline. It does not add candidate-specific support for this probe panel. A zero match in this bounded prefix subsample is not evidence that a transcript is absent or false. Published short-read evidence remains separately sourced.

Hardware: NVIDIA A100-SXM4-80GB, 24 CPUs, approximately 113 GiB host RAM, driver 550.144.03, Docker 28.0.1. The final utilization log observed a 100% GPU utilization peak and 21,095 MiB peak GPU memory. Container digest: `sha256:191f3e113631493888c9a54534f6484614f645f6767cb0078c4f1b8ac116a34b`.

The initial alignment invocation failed immediately because the Parabricks default splice-junction overhang (100) did not match the generated index (149). The actual retry and final run explicitly used `--sjdb-overhang 149`. The original failure log and both executed commands are preserved. No index or biological data were fabricated to resolve the mismatch.

Matching converts STAR intronic coordinates to terminal exonic bases and checks both direct and reverse-complement-equivalent read representations against ordered probe parents, requiring both breakpoints within 10 nt. It retains raw STAR coordinates and read IDs, excludes encompassing-mate records, and deduplicates canonical fragment/junction matches. An independent implementation checked all 3,275 split records and confirmed zero matches.

Artifacts:

- `pilot_summary.json`: selected final result, validated denominator, GPU observations, hashes, cost and cleanup.
- `evidence.tsv` / `parabricks_evidence.tsv`: pair-level display-only evidence; zero counts mean not detected in this 2M-pair pilot.
- `parabricks_junction_matches.tsv` and `_raw.tsv`: correctly empty match tables with schemas.
- `pilot_2m/logs/` and `pilot_2m/output/Chimeric.out.junction`: real final logs and raw junction records.
- `run_200k/`: separately archived initial summary/evidence; all archived artifact paths verified to reference the initial run.
- `pilot/`: initial input/output cache, full reference/index provenance, failed setup attempt and successful retry.

Local exported final FASTQs, BAM and junction file were checked against remote SHA256 records before deletion. Large raw bundles, FASTQs and BAMs are cached locally and excluded from Git.

Only the newly created Brev instance `kerxx8tqg` (`chrna-rna-pilot-20260919`) was deleted after exact ID verification and local export. Its absence was confirmed in inventory and its lifecycle watchdog was cancelled. The conservative quoted new-instance compute estimate is **$1.35**, rounding elapsed time upward to the next minute at $1.80/hour; this is an estimate, not an invoice. The original two-hour/$3.60 instance ceiling and $150 total new-allocation limit were respected. The preexisting running controller's matching live quote was $0.11904/hour plus storage; exact preexisting storage/billed duration were not exposed. Preexisting instances were not stopped or deleted. Another CPU instance appeared during the task and was left untouched.

Recompute matching and summary from cached artifacts:

```bash
.venv/bin/python scripts/compute/summarize_pilot.py --artifacts results/compute/pilot_2m --status completed --read-pairs 2000000
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hic.py -q
```

Fresh GPU reproduction uses `scripts/compute/remote_pilot.sh` on a separately quoted, compatible, bounded instance. `remote_extension.sh` reuses its reference/index. `validate_pilot_fastq.py`, `monitor_gpu.py`, `match_junctions.py`, and `summarize_pilot.py` retain validation and provenance. Portable SRA toolkit 3.4.1 and STAR 2.7.2a are pinned; the source manifest preserves their actual run hashes.
