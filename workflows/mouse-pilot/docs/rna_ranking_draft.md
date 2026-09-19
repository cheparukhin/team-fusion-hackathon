# RNA ranking implementation draft

Status: implementation controls only. No biological candidate has been ranked
with this module, and no scientific freeze has occurred. The single-transcript
assessment, mapping-specificity rules, score calibration and caller importers
must be implemented and tested before applying this specification to reads.

`chrna.junction_ranking` defines exact junction identity by reference build,
ordered gene IDs, chromosome, strand and both zero-based interbase boundaries.
Nearby coordinates remain distinct. Original caller gene names, raw coordinates,
reference versions and matching statuses belong in the linked source records;
the stable junction ID must never replace those records.

The provisional order is evidence category, biological sample count, distinct
qualifying reads, mapping-specific qualifying reads, median split-versus-single
score margin, median shorter-side anchor, and caller agreement. Numeric evidence
sorts descending. This makes mapping specificity explicit as required by the
execution goal; it adds that field to the proposal's draft ordering. Thresholds
that establish a qualifying read and mapping specificity remain unset pending
technical-control calibration. Do not assign them from published outcomes.

Each assessed molecule counts once within a sample/junction, regardless of how
many callers report it. Conflicting assessments must be reconciled upstream.
Independent split/clipped-read scans are recorded as proposal sources; they do
not add to the count of LongGF, JAFFAL and Genion callers. Shared biological
sample IDs do not create independent replication. Sequence identity alone never
deduplicates direct-RNA molecules.

Unknown score or anchor measurements remain null. A median is withheld when
any qualifying read lacks the measurement, and sorts after measured medians.
Technical states with no qualifying support remain in the decision ledger.
Those states are not biological true-negative labels. The RNA catalogue must
retain singletons and unresolved proposals regardless of ORF or folding status.

Exact feature ties receive the same rank interval; the stable ID only controls
display order. The parser accepts only the declared RNA-evidence schema, so
published assay outcomes, protein function, ORF length and structure confidence
cannot enter this ranking through extra fields. The read-count baseline,
calibration controls, full source/decision exports, and freeze-bundle interface
still need integration before production use.
