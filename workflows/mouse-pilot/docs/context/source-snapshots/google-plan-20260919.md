# Google planning document — reference snapshot

Source: https://docs.google.com/document/d/1suaqiVIxDCT2D8bvYndyFK6X1NSLv9tCG7VbrBRzrG4
Title: TeamFusion-Wilbe2026
Revision: ANLCKQlkp4E7Hkp-FdzDmuV-wgajUW2AIDogBKUPTgXeJX9UHKvcnS43IsEyijkP4mZ729xVG3Le4ivhxrIP2VQcOZPNtr9QRNHAfJgyUmA
Retrieved: 2026-09-19

This is source context, not the current execution instruction. Some proposals are superseded or scientifically qualified by docs/execution_goal.md and docs/decision_history.md. Tab boundaries are preserved below.

## Tab t.0

setup

People: |  | Amber Wu

## Tab t.4plrnki7xem6

Fleeting Idea Board

Desc: Put random thoughts for related projects or open directions / next steps for current projects here.

Core Ideas

Structural prediction of all identified chRNAs. Pipeline to take high confidence chRNAs and predict their structures in AlphaFold 

Related Ideas

Integration Chromatin interaction HiC data => non-coding genome cis/trans regulatory interactions producing possible interesting chimera regions (this can also serve as the verification - chromatin looping)



## Tab t.58s4wkxjdqga

chRNA PROJECT A

Desc: Main project; 

Identify chRNAs in long read sequencing and filter out all others.

Validate the presence of chimeras in the short-read sequencing

Filter out chimeras formed by DNA-fusion rather than RNA trans-splicing (e.g. BCR-ABL)

Use Hi-C to filter out chimeras that are unlikely to be made by trans-splicing based on genomic distance.

Go back through old short read datasets and look for our validated chRNAs (identified from the biggest correlated datasets). 

Scientific Output Hopes

Chimeras with new domains ; 

Deliverables.

1 Dataset

Phase 1: Paper triage.

Format

Papers

Accession Number

ONT long-read RNAseq

Illumina short-read

ONT + Illumina

…

Phase 2: Structured read dataset.

Pull raw reads from each accession number.

Wrangle into dataframe

Labels: TP/TN from chRNA paper, 

DataBase

Dataset

Type

Samples

Long-read

Short-read

Pairing level

Access

SG-NEx<br>(Nat Methods 2025)

Bulk

5 core cell lines (A549, K562, MCF7, HepG2, HCT116), plus extended cell lines and tissues

ONT PCR-cDNA / direct cDNA / direct RNA + PacBio Iso-Seq

Illumina 150bp PE

Same cell line sample, ≥3 high-quality replicates

Open; AWS Open Data, tutorials at GoekeLab/sg-nex-data

LRGASP

Bulk

WTC11, H1-mix, mouse ES, manatee (with SIRV spike-ins)

PacBio + ONT across multiple library protocols (cDNA, dRNA, R2C2, CapTrap)

Illumina

Aliquots of the same RNA — the strictest

Open; ENCODE portal

GTEx long-read<br>(Glinos et al., Nature 2022)

Bulk

88 GTEx tissue samples and cell lines

ONT (mostly PCR-cDNA)

GTEx's own Illumina data

Same donor / same tissue sample

dbGaP controlled access

Zajac et al.<br>(NARGAB 2025)

Single-cell

ccRCC tumour

PacBio MAS-ISO-seq

Illumina

Same 10x 3′ cDNA, barcode + UMI, so per-molecule matching is possible — strictest of the single-cell options

See paper's data availability

A few notes:

How tightly matched: LRGASP (same RNA tube) > Zajac (same cDNA) > SG-NEx (same cell line batch) > GTEx (same tissue block, but short and long are two independent library preps). For technical benchmarking, go with the first two; for biological questions, GTEx wins on sample size.

Some SG-NEx samples also carry spike-ins and matched m6A profiling, useful if modification analysis comes up later.

Only GTEx needs an application; the other three download freely.

2 Models

Fine Tuned ESM2 / genomic language model > 3D contact predict

Fine tune RNA language model - Evo 2 model?

Chimeric RNA classifier - 

3 Agentic Workflow

Convert 

Open Directions.

SAEs: Decompose foundation model activations into interpretable features. Locate features which fire on chimeric RNAs e.g. via ground truth labels in chRNA paper ; auto-interpretability pipeline.

Correctly folded chimeras ; Do we expect more disordered regions, 

Project Template Cues

Slide 1: Project Overview

What did you build and who does it help? (one clear sentence)



Who has this problem, and why does it matter scientifically or in a real workflow?



What is your solution approach?



What does your solution make faster, easier, cheaper, or newly possible?



Slide 2: What You Built

Can you create a simple workflow diagram showing the key inputs, system steps, and outputs?



What is a short description of what you built?



Slide 3: Demo, Evidence, and Usefulness

Can you demonstrate your solution with a live demo, screenshots, example outputs, or a short backup recording?



What did you test, and what were the results?



Who would use this in the real world, and where does it fit into existing workflows?



What is the most important limitation or unanswered question?



Slide 4: Technical Appendix

What is your GitHub repository URL?

What is your demo or application URL (if applicable)?

What environment or installation requirements are needed?

What command or process runs the project?

How do you reproduce the results you've shown?

What NVIDIA technologies and versions did you use?

What OpenAI models and tools did you use?

What data sources and evaluation methods did you use?

What other dependencies or infrastructure is required?

## Tab t.b423pr7u1nck

Shared prompts

1. Reproducing elements of chRNA paper,

Task:

Reproduce the paper’s computational findings from its original direct long-read RNA-sequencing data.

Filter out reads fully explained by a single known transcript, including ordinary mRNAs and non-coding RNAs. Retain reads that support a junction between two different genes, even when both contributing segments are already annotated.

Assemble a candidate chimeric RNA list and rank it by sequencing evidence. Freeze the candidate list, filtering rules and ranking before comparing them with the paper’s experimentally supported candidates.

Reconstruct candidate RNA sequences and identify open reading frames spanning each fusion junction. Translate these into predicted protein sequences, allowing the downstream segment to use a different reading frame from its parental protein.

Compare the recovered RNA junctions and predicted protein sequences with those reported in the paper. Record matches, discrepancies and which processing steps retained or removed each example.

Predict structures for all eligible candidate protein sequences and report confidence and uncertainty. Check whether we recover Gsdmd–Tmem106a, its reported protein sequence and a structure consistent with the paper’s prediction. A confident predicted fold is not proof that the protein exists or functions.

Deliver a reproducible pipeline, candidate evidence table, filtering record, structure predictions and a concise comparison with the paper.

Additional thing we can check -  

Output Format:

Data set: 

https://www.rna-seqblog.com/singapore-scientists-unveil-one-of-worlds-largest-long-read-rna-sequencing-datasets-to-advance-disease-research/



https://www.encodeproject.org/matrix/?type=Experiment&internal_tags=LRGASP&limit=200

Potential pipeline prompt (Chris)

# ROLE AND OBJECTIVE

You are an autonomous Bioinformatics pipeline agent. Your objective is to triage chimeric mRNAs identified by the TYPHON pipeline from long-read RNA sequencing data, predicting whether they form functional proteins with novel structural arrangements that could be investigated as future targets in drug design.

# DATA SOURCES & ENVIRONMENT

You will operate on the following matched datasets (aligned to GRCh38):

1.  **Transcriptomic Input:** TYPHON fusion outputs derived from the SG-NEx Oxford Nanopore (ONT) dataset for reference cancer cell lines (e.g., K562, MCF-7).

2.  **Spatial Input:** Matched high-resolution Hi-C contact matrices (.mcool files) downloaded from the 4D Nucleome (4DN) or ENCODE portals.

# PIPELINE STEPS AND QC GATES

Execute the following pipeline sequentially. At each defined [QC GATE], you must halt execution, generate a summary report of the filtered data, and await manual human review and approval before proceeding to the next step.

## Step 1: Spatial Proximity Validation (Hi-C)

*   **Action:** For every chimeric pair in the TYPHON output, use the `cooler` Python library to query the .mcool Hi-C matrix. Extract the normalized contact frequency between the 5' and 3' genomic coordinates.

*   **Filter:** Flag any fusion pairs with background-level or zero spatial contact. Retain fusions co-localizing within the same TAD or exhibiting significant inter-chromosomal contact.

*   **[QC GATE 1]:** Output a CSV containing all queried pairs, their Hi-C contact frequencies, and your pass/fail classification. Wait for human validation of the threshold cutoffs to rule out trans-splicing library artifacts.

## Step 2: Sequence Reconstruction & Translation

*   **Action:** For spatially validated chimeras, extract the flanking exonic sequences across the fusion junction from the GRCh38 reference genome. 

*   **Action:** Translate the sequences using TransDecoder to identify the longest continuous Open Reading Frame (ORF).

*   **Filter:** Flag transcripts resulting in a total protein length of <100 amino acids. Retain all others, explicitly noting whether the downstream sequence is in-frame or has undergone a frameshift.

*   **[QC GATE 2]:** Generate a summary table mapping the original TYPHON breakpoints to the predicted translation lengths and reading frame status. 

## Step 3: Nonsense-Mediated Decay (NMD) Filtering

*   **Action:** Map the location of the transcript's primary stop codon relative to the final exon-exon splice junction.

*   **Filter:** Apply the 50-nucleotide rule. Flag any transcript where the premature termination codon (PTC) is >50 nucleotides upstream of the final splice junction.

*   **[QC GATE 3]:** Output a list of NMD-vulnerable transcripts for manual review. Await human confirmation to discard these from the therapeutic pipeline.

## Step 4: Branching Therapeutic Analysis

Split the surviving dataset based on the reading frame status identified in Step 2.

### Branch 4A: In-Frame Fusions (Structural Targets)

*   **Action (Domain):** Run sequences through InterProScan. Flag chimeras lacking an intact catalytic or signaling domain.

*   **Action (Structure):** Process retained sequences through ESMFold. Flag proteins with severe structural disorder (low pLDDT) localized at the fusion junction.

*   **Action (Targeting):** Query structurally stable chimeras against DGIdb to identify existing small-molecule vulnerabilities.

*   **[QC GATE 4A]:** Export the generated .pdb files, InterProScan domain maps, and DGIdb drug matches. 

### Branch 4B: Frameshift Fusions (Immunotherapy Targets)

*   **Action (Extraction):** Isolate the novel 15-21 amino acid polypeptide tail generated downstream of the frameshift junction.

*   **Action (Binding):** Run these novel peptides through netMHCpan against the specific HLA alleles of the cell line.

*   **[QC GATE 4B]:** Export a ranked list of high-affinity neoantigen peptides. These will be manually reviewed for downstream engineering of personalized cell-based therapies or T-cell engagers.

# EXECUTION RULES

*   Never guess genomic coordinates; strictly use GRCh38.

*   If a tool (e.g., netMHCpan, ESMFold) throws an API error or timeout, log the specific sequence ID and continue processing the rest of the batch.

*   Do not proceed past a [QC GATE] until explicit user continuation is provided.

2. Plan updates

## Tab t.eeppo2w5fxj1

chRNA Triage — project plan

London AIxBio Hack, 19–20 Sep 2026. Track 02 Orchestration (primary) / 03 Benchmarking (secondary).

0. The one-sentence claim

Long-read chimeric-RNA callers emit candidates with no biological filtering and no way to tell a real trans-spliced transcript from a reverse-transcriptase artifact. We build the missing layer: a deterministic filter cascade benchmarked on matched direct-RNA vs cDNA data, plus a structural triage that says which surviving chimeras could encode a working protein.

Why this is defensible, not incremental

We read the TYPHON source (the companion pipeline to Venezia et al. 2026). What is actually in the code:

Filter

Present in TYPHON?

Minimum supporting reads

min_sup_read: 1, min_support: 1, min_low_spanning_reads: 1

Cross-caller consensus

No — pd.concat([longgf, jaffal, genion]) is a UNION

Splice-site canonicality (GT-AG)

No

Read-through / adjacent-gene exclusion

No

Paralogue / homology filter

No

Mitochondrial / rRNA exclusion

No

Segmental-duplication filter

Available via Genion -d, but defaults to an empty file

BLAST identity cutoff in exon repair

No (blastn -outfmt 6, no -perc_identity)

Template-switching / microhomology test

No

So the field's published pipeline accepts a chimera supported by one read with one caller and no junction check. The discrimination between genuine trans-splicing and RT artifact is made experimentally (direct RNA-seq has no reverse-transcription step) and argued in prose — it is not implemented anywhere. That gap is our project.

Licence note: TYPHON is CC BY-NC 4.0. We do not vendor or fork its code. We re-implement the caller invocations ourselves (the underlying tools — minimap2, LongGF, Genion, JAFFA — are independently licensed) and cite TYPHON as the reference workflow. Put this on the appendix slide; a judge may ask.

1. Sources and modalities

1.1 Ground truth — Venezia et al. 2026

Venezia O, Kane H, Du G, … Jackson R. Functional chimeric mRNAs encode proteins in mammalian immunity. Nature (2026). DOI 10.1038/s41586-026-10982-x, PMID 42686912.

Definition of chRNA used throughout this project is theirs: a transcript joining an annotated splice donor and an annotated splice acceptor from two distinct genes. This is an RNA-level trans-splicing event, not a DNA-level gene fusion. Every filter below is designed around that definition.

System: mouse BMDMs (C57BL/6J, BALB/cJ, WSB/EiJ) and human monocyte-derived macrophages; steady-state / reparative / inflammatory; LPS 6–24 h; nigericin.

Detection: ONT PromethION direct RNA-seq, 10 biological replicates, 52.9 M passing reads, consensus across LongGF + JAFFAL + Genion, exon repair, BLAST validation; orthogonal deep Illumina; targeted NanoString nCounter tandem-junction probes.

Anchor case: Gsdmd–Tmem106a. Gsdmd exons 1–2 in frame, then Tmem106a exon 6 read out of frame, giving a truncated GSDMD-NT (residues 1–73) plus a novel 45-residue C-terminus (74–118). Membrane-localised; binds canonical GSDMD-NT; accelerates pore formation and IL-1β release. Loss protects against lethal sepsis but impairs antibacterial defence.

HARD DEPENDENCY — resolve in the first 30 minutes. The Data Availability statement is behind the Nature paywall/truncation and Europe PMC has indexed zero database links for this paper (.../MED/42686912/databaseLinks returns empty). We have NOT CONFIRMED any GEO/SRA/ENA accession, Zenodo deposit, or the supplementary table listing validated chimeras. Owner: whoever has institutional access. Open the PDF, read Data Availability + Code Availability, download the supplementary tables. Also try: https://www.ncbi.nlm.nih.gov/pubmed/42686912 → "Associated data"; and eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=gds&id=42686912&retmode=json Fallback if the data is not public: the project does not die. Venezia becomes the motivating anchor and a single hand-curated positive control (Gsdmd–Tmem106a, reconstructible from the paper figure), and the SG-NEx axis in §1.2 carries the benchmark entirely. Decide by 11:30 and do not revisit.

1.2 Primary benchmark data — SG-NEx (this is the one that makes the demo work)

SG-NEx (Chen, Davidson, Wan et al., Nat Methods 22:801–812, 2025, doi 10.1038/s41592-025-02623-4) ships ONT runs on the same cell lines under both direct-RNA and cDNA protocols. Direct RNA has no reverse-transcription step, so:

chimeras called in cDNA only → enriched for RT template-switching artifacts → negatives

chimeras called in direct RNA → candidate genuine trans-splicing → positives

chimeras in both → strongest positives

This gives a labelled set that costs us nothing to generate and that nobody has published. It is the spine of the benchmark slide.

Access (no credentials, pre-aligned BAMs — we skip basecalling and alignment entirely):

# metadata: 120 samples, 21 cols, includes per-sample HTTPS bam paths

wget https://raw.githubusercontent.com/GoekeLab/sg-nex-data/master/docs/samples.tsv

aws s3 ls --no-sign-request s3://sg-nex-data/data/sequencing_data_ont/bam/genome/

aws s3 ls --no-sign-request --human-readable --recursive \

  s3://sg-nex-data/data/sequencing_data_ont/bam/genome/SGNex_K562_directRNA_replicate1_run1/

aws s3 sync --no-sign-request \

  s3://sg-nex-data/data/sequencing_data_ont/bam/genome/SGNex_K562_directRNA_replicate1_run1 .

aws s3 sync --no-sign-request s3://sg-nex-data/data/annotations/gtf_file .

Bucket s3://sg-nex-data, region ap-southeast-1. Registry: https://registry.opendata.aws/sgnex/

Naming: SGNex_<cellLine>_<protocol>_replicate<N>_run<M>; protocol ∈ directRNA, cDNA, cDNAStranded, directcDNA. Match on filenames, not the protocol column — the column says direct-cDNA while filenames say directcDNA, and HCT116 is spelled Hct116.

Matched pairs to start with: SGNex_K562_directRNA_replicate1_run1 ↔ SGNex_K562_cDNA_replicate1_run3 SGNex_HepG2_directRNA_replicate1_run3 ↔ SGNex_HepG2_cDNA_replicate1_run4

K562 carries BCR-ABL1 — a real, known fusion. It is our positive control: if the pipeline does not recover BCR-ABL1, the pipeline is broken. Wire this in as a smoke test.

Genome BAMs are aligned to Ensembl GRCh38 v91. Sizes NOT CONFIRMED — check with the --human-readable listing before committing to a download. Expect ~0.5–3 GB per run.

1.3 Modality summary — what each one can and cannot tell you

Modality

Resolves

Blind to

Role here

ONT direct RNA

Full-length native transcript, junction on one molecule, no RT

Low throughput, ~5–15% error, 3'-biased

Primary evidence. Absence of RT is what makes it artifact-free

ONT / PacBio cDNA

Full-length, higher accuracy (PacBio HiFi esp.)

Introduces RT template switching

Negative-control channel. Its artifacts are our labels

Illumina short-read

Depth, junction-spanning read counts

Cannot phase a junction to a full transcript; assembly-dependent

Orthogonal support / read-count evidence

Hi-C / 3C

Physical proximity of parent loci; Venezia show inflammation induces interchromosomal contacts

Population average, no transcript-level link

Prior, not proof. A strong contact raises prior odds of trans-splicing; it never confirms one event. See §7

Mass spec

Whether the chimeric protein exists

Needs junction-spanning peptide, poor coverage, rarely in public data for a novel ORF

The real validation we cannot do this weekend. State as limitation

Say the Hi-C caveat out loud in the talk. A judge who works on genome architecture will ask, and "proximity is a prior, not evidence" is the right answer.

2. Building the labelled chRNA dataset

2.1 Candidate generation (reproduce, don't innovate)

Run on each matched dRNA/cDNA pair. We reimplement TYPHON's invocations rather than using its code (see licence note).

minimap2 -ax splice -uf -k14 --secondary=no -G 50k (skip if using pre-aligned BAMs)

samtools sort -n — LongGF requires name-sorted input

LongGF min_overlap_len 100, bin_size 50, min_map_len 100, pseudogene 2, secondary_alignment 0, min_sup_read 1

Genion via paftools.js sam2paf, --min-support 1, with a real genomic_superdups file supplied (TYPHON leaves it empty — we do not)

JAFFAL (JAFFA v2.3), blast_options -perc_identity 96, blat_options -minIdentity=96

Union the three callers, tag Origin, keep 2-gene events, dedup on Read_ID

Output schema mirrors TYPHON so results are comparable: Read_ID, Chimera_ID, Origin, GeneA, GeneB, Chr_A, Strand_A, Chr_B, Strand_B, breakpoints, Chromosomal_Status.

If time is short (likely): skip steps 1–5 entirely for the demo path and run only LongGF on a downsampled BAM, or ship precomputed candidate tables. The contribution is §2.2, not §2.1. Do not burn Saturday on caller installs.

2.2 The filter cascade — this is the contribution

Each filter is deterministic, independently testable, and emits a reason string, not just a boolean. Every rejected candidate carries why it was rejected. That is what makes the output auditable and the demo legible.

#

Filter

Rule

Rationale

F1

Junction canonicality

Donor must be GT (or GC), acceptor AG, at annotated exon boundaries of both parents

The definition of trans-splicing. Non-canonical junctions are alignment or RT artifacts

F2

Annotated-boundary snap

Breakpoint within ±5 bp of an annotated donor/acceptor in GENCODE; snap and record offset

ONT error rate smears breakpoints. Un-snappable = reject

F3

Microhomology scan

Compute longest exact match between the 5' donor flank and the sequence immediately 3' of the acceptor, window ±20 nt. Flag ≥4 nt

The mechanistic template-switching signature. RT jumps are driven by short homology. This is our single best artifact discriminator and it is absent from every existing pipeline

F4

Read-through exclusion

Reject same-strand, same-chromosome pairs with gene order preserved and intergenic distance < 100 kb

Conjoined/read-through transcripts are the classic false positive

F5

Paralogue / homology

Reject if GeneA and GeneB protein products share > 70% identity, or if the junction maps to a segmental duplication

Most fusion-caller FPs are the wrong partner at the right breakpoint

F6

Mitochondrial + rRNA + low-complexity

Reject chrM, rRNA/snoRNA biotypes, and junctions inside RepeatMasker low-complexity

JAFFAL found 116 mito chimeras present only in cDNA — pure artifact class

F7

Read support + reproducibility

≥ 2 supporting reads AND present in ≥ 2 replicates (tiered: report at 1/2/3)

TYPHON's min_sup_read: 1 is indefensible

F8

Caller consensus

Record how many of {LongGF, JAFFAL, Genion} called it; tier rather than hard-reject

Consensus is evidence, not a gate

F9

Protocol provenance

Tag dRNA_only / cDNA_only / both

The label itself. cDNA-only is the negative class

Implementation: one filters.py with one pure function per filter, (candidate, refs) -> (bool, reason), and a pytest file with a hand-built fixture per filter. Write the tests. "Another team could reproduce this" is 20% of the score and tests are the cheapest way to earn it.

2.3 The headline number

Compute and put on one slide:

Candidates surviving each filter stage, as a waterfall (start → F1 → … → F9)

Artifact depletion: fraction of cDNA_only candidates removed by F1–F6, versus fraction of dRNA candidates removed. A good filter kills the former and spares the latter. Report both; the ratio is the result.

Precision/recall of the cascade treating cDNA_only as negatives and both as positives

BCR-ABL1 recovered in K562 (smoke test, binary)

State plainly: cDNA_only is a proxy for artifact, not a gold label — some real chimeras will be seen only in cDNA by chance at low depth. Quantify that with a depth-matched subsample if time allows; otherwise name it as the main caveat.

3. Translation to amino acids

For each surviving chimera, reconstruct the transcript and translate deterministically.

Reconstruct the mature chimeric mRNA: GeneA exons up to the donor + GeneB exons from the acceptor onward, using the GENCODE primary transcript for each parent (same bit-score → primary → longest rule TYPHON uses, so results are comparable)

Locate the start codon: the annotated ATG of GeneA's primary transcript. Record the 5' UTR length. If the junction falls 5' of the ATG, the chimera is UTR-only → flag non_coding_junction, keep it (it may still be regulatory) but exclude from §4

Translate in the GeneA frame through the junction, then continue into GeneB

Determine the junction frame offset: (cumulative_CDS_length_A) mod 3. Report in_frame (0) or out_of_frame (1 or 2) relative to GeneB's own annotated frame. This is the Gsdmd–Tmem106a case exactly: in-frame through Gsdmd exon 2, out-of-frame into Tmem106a exon 6, producing a novel C-terminus that exists in no annotated protein

Find the first stop codon downstream of the junction. Record the novel C-terminal segment: its length and sequence

NMD prediction (deterministic, and a genuinely good verifier): apply the 50–55 nt rule — if the stop codon lies > 55 nt upstream of the final exon–exon junction of the chimeric transcript, the transcript is a predicted NMD target and the protein is unlikely to accumulate. Emit NMD_predicted / NMD_escape. This single check is defensible, costs nothing, and is exactly the kind of thing a judge means by "meaningfully better than the current alternative" — no chimera caller does it.

Outputs per chimera: protein.fasta, frame_status, n_term_source_residues, novel_c_term_len, stop_position, nmd_flag, junction_residue_index.

4. Structure prediction and functionality proxies

We are not proving function. We are ranking which chimeras are worth an experiment.

4.1 Folding

Primary: Boltz-2 or OpenFold3 via NVIDIA NIM (build.nvidia.com) — hosted, no local GPU setup, and it makes the NVIDIA use central rather than decorative

Fallback: ESMFold locally on Brev if the NIM queue is slow. Have both paths ready by Saturday afternoon; do not discover the queue at 10am Sunday

Fold three things per chimera, because the comparison is the point:

the chimeric protein

parent A's annotated protein

parent B's annotated protein

4.2 Proxy metrics (all computed, none claimed as truth)

Metric

How

Interprets as

Retained-domain integrity

TM-score / RMSD of the chimera's N-terminal region vs the same region in parent A's structure

Did the inherited domain survive truncation? The GSDMD-NT in the figure clearly does

Mean pLDDT, retained region

From the folding model

Confidence the inherited fold is real

Novel-segment disorder

Fraction of novel C-terminal residues with pLDDT < 50, cross-checked with IUPred3

The Gsdmd–Tmem106a novel C-terminus is visibly disordered in the paper figure — this metric should reproduce that

Domain retention (sequence)

InterProScan / Pfam-HMMER on the chimeric sequence vs each parent

Which annotated domains are kept, truncated, lost

Structural neighbours

Foldseek the chimeric structure against AFDB/PDB

Does the chimera resemble anything with known function?

Interface plausibility

If parent A homo-oligomerises (as GSDMD does), fold chimera + parent A N-term with Boltz-2 and read ipTM / PAE-interaction

Can the chimera still engage its parent's partner? This is the GSDMD-NT binding result

Membrane / localisation

DeepTMHMM or hydrophobicity on the novel segment

GSDMD–TMEM106A is membrane-localised; a novel hydrophobic tail is a real signal

4.3 Composite triage score

Do not invent a weighted score and present it as validated. Present a transparent rubric: each chimera gets a tier (A/B/C) from explicit rules, e.g.

Tier A: NMD_escape AND retained-domain TM-score > 0.7 AND novel segment either ordered or membrane-predicted

Tier B: NMD_escape AND retained domain intact, novel segment fully disordered

Tier C: everything else

Then show that Gsdmd–Tmem106a lands in Tier A. That is the money slide. One known functional chimera, recovered blind by a rubric written without looking at it.

If Venezia's supplementary table is obtainable, extend this: rank all their validated chimeras and show they concentrate in Tier A relative to the filtered background.

5. HTML gene-annotation renderer

Reproduce the left panel of the paper figure, generated automatically per chimera.

Inline SVG, no JS chart library. Exons as stacked rectangles, parent A above, parent B below, with a bracket linking the translated span to the protein

Colour semantics from the figure: grey = untranslated, blue = in-frame translation, red = out-of-frame translation, pale = stop codon

Label each exon (Exon 1, ATG, chRNA Stop), mark the junction, annotate the 5' UTR

Right panel: embed the folded structure. Simplest path is a pre-rendered PNG per chimera (PyMOL/py3Dmol headless); nicer path is a 3Dmol.js viewer from an inline PDB string

Beneath: the filter audit trail — every filter, pass/fail, and the reason string. This is what makes it look like an instrument rather than a figure

One self-contained .html per chimera plus an index page with the tier table

Publish the index as an Artifact so judges can click it during the talk

Build this early, with fake data. A renderer that works on a hardcoded Gsdmd–Tmem106a record by Saturday evening de-risks the whole presentation; wiring real data into it on Sunday is an hour.

6. Agentic workflow (the Track 02 story)

The agent's job is orchestration and judgement at the decision points, not computation. Every number comes from deterministic code. Say this explicitly on the architecture slide — "the LLM never asserts anything the code has not checked" is the line that earns criterion 2.

Tools exposed to the agent (typed JSON in/out, each one a plain Python function):

fetch_candidates(sample, protocol)        -> candidate table

annotate_junction(chimera_id)             -> donor/acceptor seq, flanks, GENCODE context

run_filters(chimera_id)                   -> per-filter pass/fail + reason strings

translate_chimera(chimera_id)             -> AA seq, frame status, stop pos, NMD flag

fold(sequence, model)                     -> structure + pLDDT/PAE           [NIM]

compare_to_parents(chimera_id)            -> TM-score, disorder fraction, domain table

foldseek_search(structure)                -> structural neighbours

render_report(chimera_id)                 -> path to self-contained HTML

Agent loop: rank candidates → for the top N, gather evidence → decide whether the evidence is sufficient or another tool is needed (e.g. "retained domain scored 0.68, just under threshold — run the oligomer interface check before tiering") → assign tier with a written justification → emit report.

GPT-Rosalind / Codex does the orchestration and writes the per-chimera narrative. Its genuine added value is the literature step: pull what is known about each parent gene and say why this pairing might matter biologically. That is a real reasoning task, not a wrapper.

NVIDIA: Boltz-2 / OpenFold3 NIMs for folding; Evo 2 embeddings of the junction window as a feature if there is time (see §7); Brev for the pipeline run.

Human decision point (the track brief explicitly asks for these): the agent proposes tiers; the scientist confirms or overrides in the HTML report, and the override is logged. Show this in the demo — it is a differentiator and it is honest about what the system is for.

Demo script (5 minutes, rehearse it twice):

30 s — the problem: TYPHON's filter table above, on screen

60 s — run the agent live on a held-out K562 pair; candidates stream in

60 s — the filter waterfall and the artifact-depletion number

90 s — open the Gsdmd–Tmem106a report: exon diagram, frame flip, NMD escape, GSDMD-NT fold retained, novel C-terminus disordered, Tier A

30 s — limitations: cDNA-only is a proxy label; no mass spec; Hi-C is a prior

30 s — repo, one-command reproduce

Record a backup video Sunday at 13:00. Live demos fail.

7. Open directions

Put these on the final slide as "where this goes", not as things you claim to have done.

1. Sequence + Hi-C → chRNA probability model (your suggestion, and the strongest) Train a classifier that takes genomic sequence around candidate donor/acceptor pairs plus Hi-C contact frequency between the parent loci, and outputs P(chRNA). Label it with the direct-RNA-derived set from §2. The payoff is a genome-wide prior that does not require direct RNA sequencing — you could score every annotated donor–acceptor pair in the genome and produce a ranked atlas. Features: Evo 2 embeddings of both junction flanks, splice-site PWM scores, contact frequency at matched resolution, expression of both parents, interchromosomal vs intrachromosomal. Honest framing: Hi-C raises the prior, it does not witness an event; the model would be a screening tool that direct RNA-seq then confirms. The natural evaluation is exactly the comparison you name — how well does a sequence+Hi-C model recover what direct RNA sequencing finds?

2. Inflammation-conditional chRNA. Venezia show inflammation induces interchromosomal contacts between parent loci. Do chRNAs appear preferentially at loci that change contact on stimulation? Needs paired Hi-C and dRNA across conditions.

3. Evolutionary question. Is rapid induced response the rule or the exception? Test whether chRNA parent pairs are enriched for immediate-early / inflammatory genes relative to expression-matched controls. Cheap, and it addresses "why would this evolve".

4. Artifact model as a standalone contribution. The microhomology + protocol-provenance work is publishable on its own as a template-switching detector for long-read data, useful far beyond chimeras.

5. Druggability. A chimera is a good target only if the junction epitope is surface- exposed and the parent proteins are not. Foldseek + surface accessibility of the junction-spanning region gives a first pass. This is the honest version of "are chRNAs actually a good drug target" — currently unanswered.

6. Cross-species. Run the cascade on mouse and human macrophage data and ask whether chRNA pairs are conserved. Conservation would be the strongest argument against artifact that does not require new experiments.

8. Schedule and ownership

When

What

Owner

Sat 11:00–11:30

Resolve the Venezia data dependency. Pick spine: Venezia+SG-NEx or SG-NEx only

whoever has journal access

Sat 11:00–12:00

Repo scaffold, env, samples.tsv, start SG-NEx download in background

infra

Sat 11:00–13:00

Reference prep: GENCODE GTF, genome FASTA, superdups, RepeatMasker

data

Sat 12:00–15:00

filters.py F1–F9 + pytest fixtures

filters lead

Sat 12:00–15:00

HTML renderer against hardcoded Gsdmd–Tmem106a

viz

Sat 13:00–16:00

Candidate generation on one matched pair; BCR-ABL1 smoke test

pipeline

Sat 15:00–18:00

Translation + NMD module

filters lead

Sat 16:00–19:00

NIM folding path working end to end on one sequence

structure

Sat 19:00–20:00

Integration checkpoint. Everything talks to everything, even if ugly

all

Sun 10:00–12:00

Proxy metrics, tiering rubric, run on the full candidate set

structure + filters

Sun 10:00–12:00

Agent tool wrappers + loop

orchestration

Sun 12:00–13:00

Headline numbers, waterfall figure

all

Sun 13:00

Record backup demo video. Non-negotiable

viz

Sun 13:00–15:00

Slides (4-slide template), README with one-command reproduce, rehearse ×2

all

Scope-cut order if behind (decide, don't drift): drop §2.1 live caller runs → drop Foldseek and interface metrics → drop the agent loop and demo the pipeline as a CLI → drop multi-chimera and demo Gsdmd–Tmem106a alone. The filter cascade, the translation/NMD module and the HTML report are the irreducible core. Protect those three.

9. Repo layout

chrna-triage/

  README.md              # one-command reproduce, the first thing a judge reads

  env/environment.yml

  data/                  # .gitignored, download script only

  src/

    candidates.py        # caller invocations / table ingest

    filters.py           # F1-F9, pure functions returning (bool, reason)

    translate.py         # frame, stop, NMD

    structure.py         # NIM clients, TM-score, disorder

    report.py            # SVG + HTML

    agent/tools.py       # typed tool surface

    agent/loop.py

  tests/test_filters.py  # one fixture per filter

  notebooks/benchmark.ipynb

  results/               # waterfall figure, tier table, example reports

README must contain: exact accessions used, exact commands, the filter table from §0, the headline numbers, and a limitations section. Reproducibility is 20% and it is the cheapest 20% on the board.

