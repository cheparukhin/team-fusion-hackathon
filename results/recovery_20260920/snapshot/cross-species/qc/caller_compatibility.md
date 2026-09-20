# Caller compatibility findings

TYPHON source remains pinned. Species-native references are adapted reversibly; native coordinates and transcript sequences are preserved.

- Reference adapter: positive/negative strands, exon concatenation, duplicate gene symbols, and absent contigs tested successfully.
- LongGF excludes GTF contigs containing underscores. Such contigs are not evaluable by this caller; they must not be marked biological negatives. Whole-genome alignments retain the original contig names.
- LongGF's default streaming mode omitted the final synthetic split read (2 of 3). Source inspection found its final-read flush condition. Its supported `output_flag=16` all-read processing mode recovered all 3 IDs; negative control remained negative. Use flag 16 consistently. Initial pilot default outputs are archived and corrected before downstream interpretation. This changes processing, not support thresholds.
- Synthetic controls are labelled SYNTHETIC and stored only under qc/synthetic_controls. They are not biological evidence.
- Genion compiled with the TYPHON read-ID patch.
- JAFFA 2.3 compiled from commit 04209e99ca7d953aa099c6f22da825af1b36902d; TYPHON setup functions applied its modifications. Isolated dependencies reused; setup's hard-coded environment name is not a scientific requirement.
- Actual biological caller outputs and reconstruction still require validation. Successful installation is not successful integration.
