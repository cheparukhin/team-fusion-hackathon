# Caller compatibility findings

TYPHON source remains pinned. Species-native references are adapted reversibly; native coordinates and transcript sequences are preserved.

- Reference adapter: positive/negative strands, exon concatenation, duplicate gene symbols, and absent contigs tested successfully.
- LongGF excludes GTF contigs containing underscores. Such contigs are not evaluable by this caller; they must not be marked biological negatives. Whole-genome alignments retain the original contig names.
- LongGF's default streaming mode omitted the final synthetic split read (2 of 3). Source inspection found its final-read flush condition. Its supported `output_flag=16` all-read processing mode recovered all 3 IDs; negative control remained negative. Use flag 16 consistently. Initial pilot default outputs are archived and corrected before downstream interpretation. This changes processing, not support thresholds.
- Synthetic controls are labelled SYNTHETIC and stored only under qc/synthetic_controls. They are not biological evidence.
- Genion compiled with the TYPHON read-ID patch.
- JAFFA 2.3 compiled from commit 04209e99ca7d953aa099c6f22da825af1b36902d; TYPHON setup functions applied its modifications. Isolated dependencies reused; setup's hard-coded environment name is not a scientific requirement.
- LongGF and Genion completed for the two pilot libraries. Human Genion completed at 11:29:01 UTC, evidenced by its execution log and valid output, although the terminated continuation driver did not write a stage receipt.
- Human JAFFAL failed with `std::out_of_range: map::at` during transcript lookup; cow JAFFAL was interrupted at the caller cutoff. Both are unavailable, never biological negatives.
- TYPHON exon reconstruction required a selected-transcript BED quoting conversion (`exon_number "N"` to `exon_number N`). Coordinates, IDs, numeric values and sequences were unchanged. All 37 human and 200 cow recovered sequences passed independent native-genome concatenation checks, but many repaired boundaries differ from observed read alignments.
- Full three-caller TYPHON integration and biological validation were not achieved.
