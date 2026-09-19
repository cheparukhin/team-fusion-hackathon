# Automated post-freeze scientific review

These agent-written notes annotate the frozen computational result. They do not
change RNA ranking, protein selection, thresholds or outcome joins. Independent
human review has not been recorded.

- The ten selected junctions are all singletons in SRR28984805. This provides
  neither biological replication nor evidence that a protein is expressed.
- Every selected protein is a reference-assisted sequence hypothesis. The
  reconstruction ledger preserves the observed RNA, sequence edits and retained
  high-quality variants. Independent Biopython translation checks establish
  arithmetic consistency, not correctness of the assumed reference alleles.
- Higher-ranked RNA can be deferred because supporting reads yield conflicting
  primary proteins or lack a complete resolved spanning ORF. Folding eligibility
  is distinct from RNA support; the complete RNA ranking is preserved.
- The Rn18s-rs5 → Lgals1 selection involves a noncoding parental annotation.
  Biotype was not a rejection rule. An ATG-to-stop ORF in a corrected RNA fragment
  does not demonstrate its translation or establish a complete transcript.
- Alignment scanning generated proposals beyond LongGF. It is not a second
  independent caller, and these proposals must not be called caller consensus.
- Published gene-pair overlap is descriptive, post-freeze evidence. Numeric
  breakpoint agreement is not treated as exact validation while the original
  coordinate convention and assay resolution remain unestablished.
- Gsdmd → Tmem106a has no proposal in this sample's assessed discovery outputs.
  Its separately reconstructed 118-residue published architecture control is
  never substituted for recovery. Absence in this bounded pilot leaves biological
  presence unknown.
- The Boltz predictions, when available, describe hypothetical monomers. Their
  confidence cannot establish expression, stable folding, biological function,
  oligomerization or membrane context. Author-coordinate comparison is unavailable.

Full-cohort discovery, other callers, additional samples, parental inference,
repeat predictions, learning, SG-NEx and broader structural searches are deferred
under the focused execution goal. No held-out model benchmark was performed.
