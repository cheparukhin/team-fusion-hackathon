# Venezia et al. (2026): reproducibility summary

**Paper:** *Functional chimeric mRNAs encode proteins in mammalian immunity*, Nature, [DOI 10.1038/s41586-026-10982-x](https://doi.org/10.1038/s41586-026-10982-x). The supplied PDF is stored beside this note.

Venezia et al. identify inflammation-responsive chimeric RNAs (chRNAs) in mouse and human macrophages using direct RNA sequencing, which avoids reverse-transcription/template-switching artifacts. In mouse BMDMs, ten biological replicates produced 52.9 million passing Oxford Nanopore reads and 30,390 candidate exon-exon chRNAs. Calls were built from LongGF, JAFFAL and Genion, then prioritized by independent short-read, NanoString, PCR/Sanger and functional evidence. About 88% were interchromosomal; 4.5% proximal intrachromosomal; 7.5% distal intrachromosomal. Human macrophages yielded >900 chRNAs and 33 conserved parent-gene pairs.

The functional exemplar, **Gsdmd-Tmem106a**, joins the Gsdmd 5′ UTR/start codon to an out-of-frame Tmem106a-derived C terminus. Its LPS-inducible product is membrane-associated and promotes GSDMD pore formation and early IL-1β/IL-18 release. The study supports an RNA-level, spliceosome- and CTCF-dependent mechanism—not a detectable DNA translocation—but this requires the experimental validation below.

## Primary datasets and inputs

| Asset | Accession / version |
| --- | --- |
| Mouse direct-RNA long reads | [GSE267147](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE267147) |
| Human macrophage direct-RNA long reads | [GSE277057](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE277057) |
| Mouse short-read RNA-seq | [GSE324139](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE324139) |
| Mouse Hi-C | [GSE324391](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE324391) |
| K562 BCR-ABL1 benchmark | [GSE123191](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123191) |
| Annotations | GENCODE M28 / GRCm39 (mouse); GENCODE 43 / GRCh38.p13 (human) |
| Pipeline | [TYPHON](https://github.com/erenada/TYPHON) |

Supplementary Tables 1/5/10 provide sample QC and identities; 3/4/6 caller outputs; 7 the cross-validated shortlist; 8 NanoString probes; 9 PCR/Sanger primers; 11/12 human calls and conservation. Pin the TYPHON commit and record downloaded-file checksums: the paper does not specify a code commit hash.

## Sequencing and biological setup

- Mouse BMDMs: femur/tibia progenitors, M-CSF 50 ng ml⁻¹ for 7 d (refreshed day 4); inflammatory polarization with LPS 100 ng ml⁻¹ + IFNγ 20 ng ml⁻¹ for 24 h. Functional priming generally used LPS 100 ng ml⁻¹ for 6 h; nigericin 10 µM activated NLRP3 (usually 30 min).
- Direct RNA: ONT SQK-RNA002 on PromethION P24 / FLO-PRO002, 72 h; MinKNOW 22.03.4 / Core 5.0.0, Bream 7.0.9, Guppy 6.0.7. Merge passing FASTQs per sample.
- Short read: KAPA mRNA HyperPrep; NovaSeq 6000, paired-end 150 bp.

## TYPHON / long-read workflow

1. Align with Minimap2 2.24 (`-ax splice -uf -k14`); assess with NanoPlot 1.42.0/SAMtools 1.15. For LongGF realign with `--secondary=no -G 50k`, name-sort BAM, then run:

   ```text
   LongGF <bam> <gtf> 100 50 100 2 0 1 0 > <results.log>
   ```

2. Run LongGF 0.1.2, JAFFAL 2.2/2.3 (`MIN_LOW_SPANNING_READS=1`), and Genion 1.2.3 (`--min-support 1`, blank `genomicSuperDups.txt`). For Genion, convert GENCODE to Ensembl-style chromosome/identifier conventions; make `selfalign.tsv` from `minimap2 -X -c` transcriptome self-alignment and sample PAFs with `paftools.js sam2paf`.
3. **Use the patched Genion build:** enable full debug output and emit one row per supporting read with `Read_ID`. This is essential because TYPHON unions callers and deduplicates by read ID. K562 benchmarking alone used unmodified Genion.
4. Extract chimeric reads, BLAST+ 2.13.0 against the transcriptome, remove reads not mapping to ≥1 isoform of *each* parent, and disallow retained-intron isoforms. Select the highest-bit-score hit per parent, retain the read’s biological parent order, infer breakpoint exons from cumulative transcript-exon length, and reconstruct exon-repaired transcripts from the genome. Do not use raw caller labels/breakpoints as final identities.
5. Call forward-strand ORFs with orfipy 0.0.4:

   ```text
   orfipy <chimeric_fasta> --min 90 --max 1000000000 --procs 1 \
     --strand f --start ATG --stop TAA,TAG,TGA --table 1 \
     --outdir <outdir> --pep <predicted_peptides.fa>
   ```

Quantify standard transcripts with Salmon 1.10.2 (`quant --ont -t <transcriptome.fa> -lU --numBootstraps 30 -a <bam>`), import via tximport `lengthScaledTPM`, and test with DESeq2 1.50.2 (`cooksCutoff=TRUE`). Summary expression is `log2(TPM + 1)` where TPM > 0 in ≥1 sample.

## Orthogonal confirmation

Trim short reads with fastp 0.23.2 defaults (FusionCatcher and Pizzly used untrimmed FASTQ). Run Arriba 2.4.0, FusionCatcher 1.33, STAR-Fusion 1.12.0, STAR-SEQR 0.6.7, JAFFA 2.3 and Pizzly 0.37.3. A short-read junction matches a long-read call only if **both** parent breakpoints are within 10 nt of the exon-repaired long-read breakpoints. More than 250 short-read candidates met this criterion.

FFPM-like values are support estimates for prioritization, not gene expression: `(split reads + discordant mates) / (mapped reads / 1e6)`, then `log2(FFPM + 0.01)` and limma testing. Treat these cautiously because the authors observed many likely RT/PCR artifacts.

For NanoString, use NanoTube 1.6.0 with nSolver normalization, background proportion 0.33 and threshold 2; transform `log2(normalized_count + 0.5)` and retain calls above background in ≥75% of replicates of at least one condition. Confirm selected junctions by Supplementary Table 9 PCR/Sanger primers. To assess mechanism, pair junction RT-PCR with negative long-range genomic PCR, and test pladienolide B/U1 snRNA and CTCF perturbation.

## Non-negotiable cautions

- A single fusion caller or modality is insufficient evidence of trans-splicing.
- Preserve annotation releases, Genion’s patch, read IDs and BLAST-derived biological order.
- Perform exon repair before comparing junctions, counting chRNAs or assessing conservation.
- Start new functional work from the independently supported candidates in Supplementary Table 7, not the full 30,390-call catalogue.

The [Nature article](https://www.nature.com/articles/s41586-026-10982-x) hosts methods, supplementary tables and source data; use the [TYPHON repository](https://github.com/erenada/TYPHON) for installation/orchestration instructions.
