# Actual structure diversity

Every model must pass exact chain-A coordinate sequence/hash and residue-confidence identity checks. Source artifacts are read-only; extracted PDB domains copy all residues/atoms of contiguous Pfam spans, preserving chain and residue numbering (PDB precision0.001Å). Gate: span>=50aa and>=80%residues pLDDT>=70. No discontiguous confident-fragment concatenation. Additional seeds do not become independent diversity units.

Foldseek CLI is verified against the pinned binary and [official documentation](https://github.com/steineggerlab/foldseek). Each protocol is searched separately using exhaustive TMalign, then saved alignments are filtered at alignment-normalized TM>=0.5 and coverage>=0.8 for both partners. Connected-component clusters are explicitly transitive. Pfam no-hits, domain-confidence failures, missing/failed models and clustering failures remain in audits. A singleton or no-hit is not a novel fold.

Finite-set rarefaction samples actual modeled candidate peptides and counts observed thresholded clusters, accounting for multiple domains within a peptide. It is emitted only with at least5actual peptides and2observed clusters; it does not estimate unseen protein diversity or remove selection bias. Cached precomputed-MSA and single-sequence models remain separate protocols. Model-seed ensembles are outside this first-pass analysis.

Reproduce after collecting actual models with `.venv-disorder/bin/python scripts/structure_campaign/analyze_structural_diversity.py`. Optional `--jobs` selects a preserved actual jobs snapshot. No inference/cloud or synthetic structure generation is performed.
