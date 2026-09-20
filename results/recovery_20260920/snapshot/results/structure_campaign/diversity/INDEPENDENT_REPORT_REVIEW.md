# Bounded independent scientific review

Reviewed by the data worker on 20 September 2026. Read-only review of the coordinator scripts and report; no model or source changes. No substantive scientific defect found.

Independently exercised checks: 188 unique candidate evidence rows; peptide-to-pair sets exactly match annotated-start ORF sources; no duplicate first-seed peptide/protocol joins; reported V3 42/188 and V1 18/188 predominantly-disordered counts, peptide mean 0.3072025974 and residue-weighted fraction 0.2707711300 reproduce; Gsdmd exemplar V3 1.0 and V1 0.4830508475 reproduce. All 23 verified model artifacts then available had NPZ pLDDT ×100 agreeing with validated residue-confidence TSV and finite nonnegative PAE of the expected dimensions. Rigid-transform fitted RMSD was approximately 6.7e-16 Å.

Inspection confirmed that split junction codons are excluded from the two cross-parent PAE blocks, both PAE directions are averaged, and seed comparisons group by sequence SHA256 plus protocol. Parent-domain retention is an explicitly any-compatible-hypothesis flag, not observed isoform or function evidence. Missing confidence remains missing; protocol columns stay separate; interpretation avoids translation, function and physical-disorder claims.

At review time the report listed 22 verified single-sequence models plus one cached MSA reference, while diversity used the preceding 20-model calibration snapshot. This was an interim freshness difference, not a scientific estimator change. The coordinator was notified to rebuild execution/diversity/report outputs in dependency order after final freeze. No repeated full-code audit is required solely because more actual models arrive.

The review was reported before this note was saved. The following are hashes of files at note-save time; they are not asserted to be byte-identical to their earlier review-time versions if the coordinator updated them in between.

- `scripts/structure_campaign/build_evidence_table.py`: `13959d36051af6d3b86e37775c67216bac2683deb17809020d6c27094b1b5b6f`
- `scripts/structure_campaign/analyze_model_robustness.py`: `17718e3d0d81a34474bbef48bc64c398979c2172e97356c86c498edceec558bc`
- `scripts/structure_campaign/write_summary_report.py`: `fd9119260ce05962460824bb33bbe41fb45e39c6c68469f0360f24a32676fe67`
- `results/structure_campaign/RESULTS.md`: `a9e7273ececf208ebeebf50868df6c0dac60552036c222831d51308089529a23`

Final ledger binding and first-pass structural coverage will be recorded in `manifest.json` and `STATUS.md`; repeated seeds remain excluded from first-pass diversity.
