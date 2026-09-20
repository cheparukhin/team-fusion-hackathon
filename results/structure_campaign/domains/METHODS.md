# Local Pfam domain annotation

Pinned Pfam 38.2 was searched with PyHMMER 0.12.3 using model-specific sequence/domain gathering thresholds. Profiles were streamed in batches of at most64 against the small target sequence database with two CPU threads; no complete in-memory Pfam profile set and no sequence upload. Domain/HMM alignment and envelope coordinates are 1-based inclusive, validated against their lengths. Both sequence and domain inclusion flags must pass. Raw domain alignments are preserved.

HMM coverage is the covered profile-coordinate span divided by model length; sequence coverage is aligned target span divided by target length. Architecture coverage unions overlapping target intervals so residues are not double counted. All above-threshold domain hits are retained, including overlaps, with no clan competition filter. E-values reflect hmmsearch against this target sequence database and should not be presented as hmmscan database E-values.

Every target, including no-hit targets, has an architecture row. No hit does not establish a novel fold or absence of a domain/function. Parent-domain retention uses full-parent hits and exact amino-acid-matched canonical retained fragments per source ORF/transcript. Coverage is the fraction of the parent hit aligned span retained; >=90% is an operational annotation, not a folding or function guarantee. Novel-frame sequence is never assigned a canonical-parent domain through nucleotide provenance. Partial parent profile coverage remains explicit. Missing full-parent controls restrict retention claims.

Reproduce with `.venv-disorder/bin/python scripts/structure_campaign/annotate_domains.py --cpus 2`. Inputs, engine version, profile count, runtime, peak RSS and output hashes are in manifest.json.
