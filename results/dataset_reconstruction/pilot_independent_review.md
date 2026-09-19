# Independent bounded GPU-pilot review

Reviewer: data worker, independent of the compute implementation. Reviewed `scripts/compute/match_junctions.py`, `summarize_pilot.py`, and `validate_pilot_fastq.py` read-only; corrections were implemented by the compute owner.

## Three findings — all resolved

1. **P1: Reverse-complement STAR junctions were missed.** STAR preserves read/segment orientation, which need not be biological RNA direction. The matcher now checks the direct tuple and its reverse-complement equivalent (swap endpoints and flip both strands), retaining canonical ordered parent IDs and raw STAR coordinates. A simple reversed biological order is still rejected. Canonical fragment/junction matches are deduplicated, and raw matching records are retained separately.
2. **P2: The pilot denominator was accepted from CLI metadata.** Completed summaries now require the run's `fastq_validation.json`, derive actual paired-record counts/read lengths from it, verify accession and any requested count, and cross-check FASTQ hashes against the alignment input checksum log. A missing validation artifact cannot support a completed summary.
3. **P2: Subsequent or failed runs could retain stale prior results.** Per-run result fields are reset before parsing. Failed-run summaries archive/remove prior selected evidence, and prior generated running/zero-match/failure limitations are removed before composing the current status. Missing failed-run read lengths are reset as well.

## Independent checks

- Confirmed the cached accession chain SRR37513722 → SRX32404271 → GSM9569462: mouse bone-marrow-derived macrophages, inflammatory LPS + IFNγ treatment for 24 hours.
- Reviewed paired FASTQ identifier equality, complete record structure, equal sequence/quality lengths, counted paired records, and file hashes. The compute owner reported that the real 200,000-pair, 151-nt input passed validation; this review did not independently rerun the remote FASTQ scan.
- Verified STAR's documented one-based intronic coordinates and strand definitions against the cached STAR 2.7.2a manual and upstream junction-output source. Donor conversion subtracts strand direction; acceptor conversion adds it.
- Independently exercised three matcher cases for canonical A(+):100 → B(+):200: direct representation matched once; reverse-complement B(-):200 → A(-):100 matched once; a different biological order B(+) → A(+) did not match.
- The focused matcher test passed (`pytest tests/test_hic.py -k star_matching -q`). It checks the inclusive 10-nt boundary on both endpoints, rejection when one endpoint differs by 11 nt, rejection of encompassing-mate type −1 records, reverse-complement matching, and raw coordinate provenance.
- Verified that support aggregates unique fragment/read IDs rather than junction-line counts. No identical probe coordinate tuple is shared by distinct ordered panel pairs.
- Reviewed the corrected summary branches and confirmed that actual completion requires a completion marker, exactly one junction output, and validated inputs. Zero pilot matches are described as nondetection in the bounded sample, not biological absence; no matched CPU benchmark or acceleration claim is inferred.

## Verified actual GPU outcome

The selected extension **completed on 2,000,000 paired 151-nt records** from SRR37513722. The exported FASTQ validation count and hashes agree with the alignment input manifest; the aligner's final log independently reports 2,000,000 input fragments and mean paired length 302 nt. The selected alignment wall time is 85.49 seconds; the start-to-completion pipeline interval is 273 seconds. Neither is an acceleration claim without a matched CPU benchmark.

- Independently counted **28,482 chimeric records / unique fragments**: **3,275 split-junction records** and **25,207 encompassing-mate records**. Encompassing mates were excluded from endpoint matching.
- A separately implemented coordinate-index matcher examined all 3,275 split records, including direct and reverse-complement-equivalent orientations, and required both endpoints within ±10 nt of the ordered probe endpoints. It found **zero probe-panel matches**, independently confirming the compute worker's result.
- Selected `evidence.tsv` has 527 distinct ordered panel pairs, each with zero support and an explicit `not_detected_in_2000000_pair_pilot` status. The selected junction-match table is empty, as expected. Junction/probe hashes match `match_manifest.json`.
- Independently verified every path and artifact hash in the selected 2M summary and archived `run_200k/pilot_summary.json`. The archived initial run contains 200,000 validated pairs and 2,849 chimeric records: 314 split-junction records and 2,535 encompassing-mate records. Its selected evidence paths correctly point into `run_200k`, while immutable original run logs remain under `pilot`.
- The 2M prefix contains the original 200k prefix; these runs are not independent samples and their read counts or support must not be added.
- A stale `extension_status` text saying running was reported to the compute owner during final cleanup. It did not affect counts, matching, or scientific results.
- Frozen classifier metrics remain byte-for-byte unchanged: SHA256 `4be5d101441003d003aadded8230a3803ce2815d65a0d34206191bbe7913a0be`. No model or Hi-C code, labels, or metrics were changed during GPU review.

The actual result demonstrates a completed bounded GPU alignment and an honestly reported zero-match outcome. It does **not** demonstrate biological absence, sensitivity, candidate validation, or acceleration. Final cloud cleanup and cost fields are owned by the compute worker; they were still being finalized at this verification step.
