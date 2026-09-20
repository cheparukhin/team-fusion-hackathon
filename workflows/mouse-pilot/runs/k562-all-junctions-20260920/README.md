# K562 all-junction RNA-to-structure run

Completed 20 September 2026 using the focused mouse pilot workflow. All 220 library-A and 199 library-B supported junctions were processed (414 distinct); no second-library or Illumina agreement requirement was applied.

450 qualifying reads were reconstructed. Fifteen reads had reference-assisted spanning ORFs, yielding 20 sequence hypotheses. Six sequence-resolved hypotheses were selected independently by library and folded with Boltz-2; all six predictions passed exact sequence, residue numbering, copied-file hash and confidence-array checks. The uncorrected observed reads yielded no complete spanning ORFs under these rules.

| Hypothesis | Library | Residues | Mean pLDDT /100 |
|---|---|---:|---:|
| SEC14L1 → GMNN | B | 45 | 79.1 |
| BICRAL → RAI1 | A | 88 | 63.0 |
| PPP2R5C → PSMC2 | B | 138 | 46.0 |
| ORC6 → HNRNPDL | B | 88 | 88.6 |
| NUDT14 → NDUFS8 | A | 75 | 60.5 |
| CREG1 → CDKN1C | B | 61 | 60.4 |

All six selected hypotheses have one qualifying read in one library. These are reference-assisted sequence hypotheses; predicted structure and confidence do not establish protein production, physiological RNA joining or function.

The remaining junctions comprise 399 without a complete spanning ORF in these reconstructed reads and nine with unresolved ORF sequence. These are computational dispositions, not biological negatives.

Adapter assessment screened 469 read/junction records: no internal near-join matches to the two tested RTA cores and seven internal poly(A/T) flags; none of the six selected reads carried either flag. Raw-signal artifacts and same-culture DNA origin remain unassessed.

Compute: one owned A100; six inference calls took 38.5–41.5 seconds each after setup. Launch through confirmed stop took 826.1 seconds. The conservative quote-based compute/storage estimate is USD 0.4934, not a reconciled provider invoice. Shared controller and other tasks are excluded. The owned worker was stopped and deleted after verification. Other users’ instances were not modified.

Validation: 119 tests, data build and development benchmark passed; held-out data were not evaluated. All 450 reconstructed RNAs and all 20 ORF translations were replay-verified for the linked view. The rendered browser audit covers all six selected hypotheses, shared codon mapping and narrow-screen layout.

## Files

- `candidate-stage-audit.tsv`: all 414 junctions and dispositions.
- `A/orfs/`, `B/orfs/`: full observed/reference-assisted RNA FASTAs and protein hypotheses.
- `selection.json`, `selected_proteins.fasta`: frozen six-protein selection.
- `fold-inputs/`: exact sequences, verified MSAs and Boltz input configurations.
- `structures/`: verified full-atom PDBs, confidence summary and raw prediction outputs.
- `scope-freeze.json`, `selection-freeze.json`, `mouse-workflow-comparison.json`: provenance and exact mouse-code comparison.
- `dashboard-data.json.gz`: RNA/exon/residue mapping checkpoint before structures were attached; final structure data are separate in `structures/dashboard-structures.json`.
- `publication.json`: lossless compressed-ledger hashes; `gunzip -k *.json.gz` restores frozen JSON bytes.
- `completion.json`, `dashboard-validation.json`, `resource-accounting.json`: execution and validation receipts.

## Reproduction

Run from `workflows/mouse-pilot/`. Restore the compressed derived ledgers first. The scripts in `scripts/k562/` record the executed reconstruction, independent-library selection, artifact screen, MSA and bounded folding paths. Reference genomes and original discovery inputs must be restored from the pinned SG-NEx/GENCODE provenance to recompute from reads; they are not included here. GPU launch code always requires fresh pricing and inventory checks. The historical one-hour deadline must not be reused for a new run.

Raw sequencing archives, genome references, model weights, credentials and local infrastructure state are excluded from this Git snapshot. Full scientific sequences and derived decision ledgers are retained. This separate human follow-up does not alter the repository’s submission claims.
