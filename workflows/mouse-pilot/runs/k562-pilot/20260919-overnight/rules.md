# Frozen K562 external verification rules

Authorized overnight 2026-09-19, after completion of the separate mouse pilot. RNA evidence only; no proteins, Hi-C, training or held-out mouse evaluation. Primary library R4; R5 and Illumina R4 are corroboration only. Complete each library independently; freeze R4 before external joins. Uncorroborated means UNKNOWN, never a biological negative.

Reference: GRCh38.p13 / GENCODE43 with RNA sequin decoys. Original aliases and sequences are preserved. Specimen independence is UNKNOWN; aliases are not proof of independent cultures. PacBio is outside this two-Nanopore-library run.

Discovery uses the pinned TYPHON minimap2 splice settings and LongGF settings
100/50/100/2/0/1/0. LongGF's pseudogene value 2 means no pseudogene filter.
All reads with supplementary genome alignments also enter an independent
alignment assessment, including those not emitted by LongGF. This does not
exhaustively rescue every unmapped or soft-clipped read. Secondary mappings are
retained in the audit remapping (up to 50 per query with minimap2's -p0.1 bound).
Finite mapper search is not proof that no other explanation exists.

The assessment uses adjacent nonsecondary segments in original read order.
Each segment is assigned every same-strand gene whose exons overlap its aligned
blocks. Ambiguous assignments remain explicit. Junction identity consists of
both ordered gene IDs, chromosomes, strands and zero-based interbase boundaries;
nearby endpoints are not silently merged. Original read names, caller text,
SAM records and reference provenance remain available.

A supported read requires at least 100 aligned query bases per arm, at least
100 exonic overlap bases per assigned gene, unique gene assignment at the
100-base threshold, MAPQ >=20 on both arms, no similarly scoring alternative
genomic placement, at least 80% query coverage, and query gap/overlap within
20 bases. Failure of these checks produces an explicit unresolved or
insufficient-anchor state, not biological absence. Nearby genes, noncoding
biotypes, microhomology and noncanonical splice sites are not exclusion rules.

Every proposed junction is compared against all returned alignments to the
complete GENCODE transcript set, including noncoding and retained-intron
transcripts. Scores are recomputed from CIGAR and MD on the same query window:
match +1, substitution -2, insertion/deletion -2 per base, unaligned query base
-2, genomic introns unpenalized. Overlapping split positions use the lower
score from the two arms to avoid double counting. This is an explicit
heuristic, not a likelihood or calibrated biological error rate.

The best single-transcript explanation excludes a proposed read from support
if it covers >=90% of the split query window and its score is within
max(20, 5% of window length) of the split score or better. A near-scoring
competitor without that coverage, uncertain mapping, or unresolved gene
assignment remains ambiguous. Missing score evidence remains unknown. A
secondary genome placement covering >=90% of an arm and within
max(10, 5% of arm length) of its score makes mapping specificity ambiguous.

RNA ranking uses the existing deterministic RNA-only junction ranker: evidence
state, actual biological sample count, distinct supporting reads, mapping
specificity, split/single score margin, shorter anchor and caller agreement.
One sample supplies no replication, and LongGF alone supplies no multi-caller
consensus. Unresolved and excluded technical proposals remain in the ledger.


The same RNA ranking is used within each library. Unknown biological specimen identities share a placeholder internally and are exported as null; no replication gain. LongGF association is only read and ordered gene-pair level, not exact-junction caller consensus. Internal adapters and RNA origin are NOT_ASSESSED.

Exact identity comparison uses unchanged ordered genes, strands and interbase coordinates. No near-junction merge. Cross-library UUID duplicates must be reconciled before corroboration. Report full and BCR:ABL1-excluded comparisons, cis/trans and min-read strata. BCR:ABL1 is a DNA-fusion positive control, not physiological trans-splicing validation. Top-20 comparison against read-count ranking averages ties analytically.

STAR short-read validation: pinned 2.7.11b, full paired FASTQ IDs checked, same reference. Minimum segment and overhang 20, chimeric multimaps 1, score drop 20, separation and nonchimeric score advantage 10, mismatch fraction <=0.04. Canonical types 1/2 resolve transcript orientation; type 2 reverses order/strands; noncanonical or repeat-ambiguous records are not exact corroboration. Distinct read-pair IDs and distinct alignment geometries are reported separately, not molecular counts. No short-read evidence enters primary ranking. Settings and all source commits are in config.json.

Repeatability: rerun twice the predeclared SHA256(read ID) first-byte-zero subset, compare canonical assessment JSON hashes. This tests computational repeatability on actual reads, not biological reproducibility or bitwise full-data identity.
