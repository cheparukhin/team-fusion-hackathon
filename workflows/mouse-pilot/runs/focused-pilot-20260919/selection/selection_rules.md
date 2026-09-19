# Focused pilot rules, specified before biological output review

This is a retrospective, single-sample reproduction using SRR28984805 and
GENCODE M28/GRCm39. It is not a prospective validation or a protein-discovery
claim. These rules do not use published outcomes. Full-cohort, SG-NEx and
additional-caller work is deferred under the revised execution goal.

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

Reconstruction and folding selection must be frozen before folding or published
validation joins. Preserve observed sequence separately from any reference-
assisted sequence. Translate continuously across the RNA junction, considering
all three forward frames and ATG-to-stop ORFs of at least 90 nucleotides.
Do not force a downstream parental frame. A resolved, supported junction-
spanning amino-acid sequence is required; unresolved alternatives are deferred.
Complete parental proteins are not required. Coding uncertainty, NMD and
structure confidence do not change the RNA ranking.

Reference assistance follows the observed genomic exon path, skipping CIGAR N
introns. It assumes the reference allele at substitutions below Q30 and restores
reference indels when their read/flank quality is below Q30. Every correction is
exported. Substitutions at Q30 or above retain the observed base; high-quality
insertions/deletions remain unresolved. Overlap between arms requires identical
projected bases; untemplated gaps require Q30 throughout.
Indels within a query overlap remain unresolved because trimming raw query
bases is not equivalent to trimming the indel-corrected reference sequence.
The longest forward
ATG-to-first-stop junction-spanning ORF is the primary hypothesis, with at least
90 coding nucleotides excluding the stop and 15 coding bases on each side of
the uncertain junction interval. Export all alternatives. Conflicting resolved
sequences among supporting reads require review before shortlist freeze.
Reference assistance is an explicit error-correction/allele assumption, not
proof that the inferred sequence was present or translated. NMD stays UNKNOWN
where the observed fragment does not establish full transcript architecture.

Select eight highest-ranked eligible distinct proteins, then one eligible
supported singleton and one eligible different junction/frame class, using
remaining RNA rank to break ties. If absent, fill from remaining eligible
proteins. At most ten recovered sequences; retain deferral reasons for others.
For this pilot, redundancy means global amino-acid edit distance no more than
5% of the longer sequence, including terminal length differences. Keep the
higher-ranked representative for folding while preserving all hypotheses.
The diversity class comprises inter/intrachromosomal status, ordered strands,
and the reconstructed ORF codon phases of both junction interval endpoints.
These phases do not establish parental CDS frame. Stable junction ID resolves
RNA display ties without hiding the original rank interval. Any unresolved
sequence reconstruction or conflicting primary protein sequence among a
junction's supporting reads defers that junction. Reads lacking a complete ORF
do not establish a protein sequence and are recorded separately. All supporting
reads must have been reconstructed before selection. The freeze saves the full
RNA ranking, rules, selected sequences, deferrals and input/output hashes in a
new directory; it never rewrites an existing freeze.
Add the published Gsdmd-Tmem106a sequence only as a labelled control, never as
recovered RNA. At most one necessary parental comparator. Pilot three available
sequence lengths before scheduling remaining folds, one standard Boltz-2 sample
per sequence; optional repeats only after prespecifying cases and checking time.

Freeze available RNA evidence/shortlist by 18:00 UTC; stop additions at 20:00
UTC; stop computation and temporary workers by 21:00 UTC; deliver by 22:00 UTC.
Unavailable results must remain explicit. A report-only fallback is not a
completed scientific pilot.
