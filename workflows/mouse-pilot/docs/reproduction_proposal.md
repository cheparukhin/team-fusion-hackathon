# Technical proposal: reproduce chimeric RNA and protein predictions

Prepared 19 September 2026. Status: proposed analysis, not an executed reproduction. No sequencing downloads, GPU jobs or structure predictions were performed for this proposal.

**Recommendation.** Build a Snakemake workflow with a paper-method reproduction branch and a separately specified discovery/audit branch. Use minimap2, LongGF, JAFFAL and Genion for RNA evidence; explicit transcript-level competing explanations for filtering; orfipy and Biopython for translation; Boltz-2 for the complete eligible protein set; ESMFold2 for a prespecified cross-check; and AlphaFold 3 for direct comparison with the paper. Use NVIDIA BioNeMo Agent Toolkit for MSA-Search and Boltz-2 NIM deployment/validation where their interfaces meet the reproducibility contract. Train no classifier in the initial reproduction.

The main engineering challenge is preserving the connection from a raw read to a junction, an inferred transcript, and a predicted protein. A good fold cannot repair a wrong nucleotide sequence.

**1. Scope and existing work**

I read the referenced tasks, “Assess chimeric protein project” and “Find open protein structure model”, and inspected the earlier project artifacts. The existing [pilot README](/Users/cheparukhin/Documents/Codex/2026-09-18/t/outputs/chimeric-rna-prioritization/README.md) describes a benchmark built from published tables. Reuse its source checksums, explicit evidence states, tie-aware evaluation and budget controls. Its published-candidate inputs and short-read ranking features must not feed the new direct-RNA-only discovery ranking.

This is a prespecified retrospective reproduction. We already know the flagship result and some validation outcomes from the earlier discussion; a later freeze cannot make this a genuinely blinded rediscovery. We can still prevent further outcome-driven tuning by isolating comparison inputs and freezing all primary decisions before running the comparison.

The requested five goals define the primary scope. Reproducing differential expression, Hi-C, animal experiments or functional assays is outside this scope. Start with all ten mouse samples; the human cohort can be a separately declared extension.

Rosalind Workbench's local plugin bundle is present. Its callable launcher is unavailable in this session, directory search returned no usable entry, and computer use cannot operate the Codex app. I used the available NGS analysis guidance and inspected the local workbench metadata; I did not execute a Rosalind workflow or use GPT-Rosalind. The available NGS registry has no dedicated direct-RNA fusion route, so a generic short-read RNA-seq workflow would be an inappropriate substitute. Once accessible, Rosalind should be the evidence-review interface for this workflow, with the versioned command-line pipeline retaining the scientific record.

**2. Data and reference contract**

Use mouse [GSE267147](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE267147), BioProject PRJNA1109857, SRA study SRP506881. A live [SRA RunInfo query](https://www.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo?acc=SRP506881) returned ten runs, 52,903,853 reads, 52,141,082,386 bases and 45,544 MB of reported SRA archive size. The accompanying [run manifest](evidence/sra-run-manifest.csv) records the run-to-sample mapping. These archive sizes do not estimate extracted FASTQ or peak working disk use.

The GEO sample protocol identifies SQK-RNA002 direct RNA sequencing despite the archive field `LibrarySelection=cDNA`. Preserve both fields and record the discrepancy; classify the assay from the explicit protocol. The ENA query returned incomplete transfer/count fields, whereas SRA returned populated records. Missing ENA fields must not be interpreted as zero data. [Sample protocol](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM8260870&targ=self&form=text&view=full).

The paper's baseline uses GRCm39/GENCODE M28, minimap2 2.24, LongGF 0.1.2, Genion 1.2.3 and JAFFAL 2.2/2.3. It reconstructs exons and predicts ORFs with orfipy 0.0.4. Its AlphaFold Server predictions use seed 9999. These are compatibility targets, not permission to substitute current defaults silently. [Paper methods](https://www.nature.com/articles/s41586-026-10982-x#Sec7).

Resolve and hash the exact genome, comprehensive GTF, transcript FASTA and matching JAFFAL resources. Include protein-coding and non-coding transcript biotypes. Preserve original versions and identifiers before alias normalization. Add any extra contaminant references or newer annotations only in named sensitivity branches.

Download using SRA Toolkit, validate archives, and extract FASTQ with an explicit original-read-name policy. Preserve a crosswalk between archive spot IDs and original ONT read IDs; otherwise published read-level comparisons may be impossible even when junction-level comparisons succeed. Record extraction tool, options, checksum, read count, sample, treatment and biological replicate. Confirm whether original raw signal is actually deposited before proposing rebasecalling. Use deposited basecalled reads for the baseline; any chemistry-compatible rebasecall is a separate sensitivity analysis.

**3. Recommended stack**

| Layer | Choice | Reason and boundary |
|---|---|---|
| Workflow | Snakemake; per-stage locked environments and container digests | Fits the existing Python project and file-based CPU/GPU jobs. Supports resumption and deployment isolation. Nextflow is reasonable if the team already operates it; there is no scientific gain from using both. |
| Long-read QC | SeqKit, NanoPlot; MultiQC where supported | Length, quality, sample counts and alignment summaries. No generic short-read trimming recipe. |
| Discovery | TYPHON wrapping LongGF, JAFFAL and patched Genion | Closest available implementation of the authors' workflow; pin the commit and retain every caller's raw output. |
| Independent audit | minimap2, SAMtools, pysam, BEDTools, BLAST+; small tested Python module | Reconstruct competing explanations and retain secondary/supplementary mappings for ambiguity assessment. |
| Transcript and ORF processing | Biopython, pysam FASTA access, orfipy | Explicit exon paths, orientation, nucleotide provenance, junction coordinates and translation. |
| Tables and report | Parquet/TSV, DuckDB or Polars, static HTML; IGV-compatible alignments | Separate read-, junction-, transcript- and protein-level objects; inspect supporting evidence. |
| Structure batch | Local Boltz-2 on Brev | Open code/weights, controllable inputs and practical batch execution. |
| BioNeMo integration | MSA-Search NIM and Boltz-2 NIM through the toolkit's documented adapters | Cache actual fusion-sequence alignments, validate model outputs and pin deployment artifacts. Retain an open-source Boltz adapter if NIM omits required controls. |
| Structural cross-check | ESMFold2 single-sequence mode | Different model/input strategy, useful for unusual fusion tails; no claimed fusion-specific accuracy superiority. |
| Paper reference | AlphaFold 3 / AlphaFold Server | Matches the paper's model family. Server and local outputs are not necessarily identical. |
| Structural comparison | US-align, residue-mapped RMSD/contact comparisons, Mol* | Quantitative comparisons with explicit residue coverage and visual inspection. |

Primary implementation documentation: [Snakemake](https://snakemake.readthedocs.io/en/stable/snakefiles/deployment.html), [TYPHON](https://github.com/erenada/TYPHON), [minimap2](https://github.com/lh3/minimap2), [pysam](https://github.com/pysam-developers/pysam), [orfipy](https://github.com/urmi-21/orfipy), [Biopython](https://github.com/biopython/biopython), [US-align](https://github.com/pylelab/USalign).

**4. Two branches with shared inputs**

The reproduction branch starts from the complete FASTQ inputs and follows the published method as closely as documented. TYPHON is described as a reimplementation of the authors' manually computed analysis, so matching its current output alone is not proof of exact paper reproduction. Audit its scripts and reference handling against the methods, including Genion's read-ID patch, singleton settings, retained-intron handling and exon reconstruction. Log all deviations.

The discovery/audit branch applies the user's single-transcript exclusion rule. Genome and transcript alignments must be available before irreversible classification. Use the union of callers plus an explicit scan of cross-gene split alignments and suspicious clipped reads as proposals. This scan makes it possible to investigate cases suppressed by caller-specific filters. Preserve all proposals, including those subsequently rejected.

Keep the paper-compatible alignment and a separate ambiguity-audit alignment. In the latter, secondary mappings must remain available; supplementary alignments representing separate parts of a read must never be mistaken for redundant secondary mappings. Any restrictive intron-length setting belongs in the paper-compatible branch; inspect whether a longer ordinary intron explains a putative split event in the audit branch.

Do not require consensus of all callers. They share data, annotations and algorithmic assumptions; agreement is a feature, not independent experimental replication.

**5. The single-transcript filter**

For each read, compare two hypotheses:

- **S:** one known transcript explains the informative read sequence, in the correct orientation and exon order, allowing measured sequencing errors and truncated read ends.
- **F:** two ordered segments assigned to different gene IDs explain a junction, with informative sequence on both sides and no equally good ordinary-transcript explanation.

The known-transcript search includes mRNAs and non-coding RNAs. A read can be a partial observation of a known transcript and still be fully explained by it. Conversely, two local hits to different annotated transcripts do not make a read ordinary.

Use a conservative proposed starting rule for S: at least 95% informative query coverage, at least 80% alignment identity, no unexplained internal interval longer than 20 nt, and no credible cross-gene segment that materially improves the explanation. These numbers are draft calibration settings, not validated biological thresholds. A candidate F initially requires at least 50 informative aligned nt per side; classify shorter anchors and substantial overlap/gaps as unresolved rather than deleting their records. MAPQ is evidence of mapping ambiguity, not a universal probability of fusion correctness.

A few percent of unexplained sequence may contain a real second segment. Therefore query coverage alone can never trigger rejection: examine the residual sequence and all competing cross-gene mappings. Re-score the best competing transcript reconstructions with the same alignment method and gap penalties before computing a split-versus-single margin; raw scores from different aligners or parameterizations are not comparable. Calibrate the split penalty and margin on technical controls, and freeze their numeric values before production comparison.

Record one of `single_transcript_explained`, `supported_two_gene_junction`, `ambiguous_single_vs_split`, `insufficient_anchor`, `artifact_suspected`, or `unmapped/unresolved`. An ambiguous match to paralogues, pseudogenes or overlapping annotations must not become a confident fusion solely through gene-name assignment. Same-gene alternative splicing is not a two-gene event. Nearby cross-gene readthrough remains a candidate category, not evidence of trans-splicing specifically.

Preserve all reasons, measured values, thresholds and competing transcript IDs. Keep annotation status as a field. Use an annotated-splice-site subset for paper comparison, while retaining non-annotated junction hypotheses in a separate discovery category. Annotation-based exon repair must not manufacture support absent from the read.

**6. Candidate identities, ranking and freeze**

Define a junction by reference build, ordered gene IDs, strands and both genomic breakpoints. Store transcript/exon alternatives separately. Internally use zero-based half-open coordinates and convert at import/export boundaries. Preserve raw breakpoints and their uncertainty; report exact coordinate matches separately from a predeclared ±10-nt comparison. Avoid clustering distinct nearby exon junctions into one candidate merely because they share gene names.

Count distinct read IDs within samples, after detecting duplicate file ingestion. One molecule reported by three callers is one supporting observation. Do not apply PCR-style coordinate deduplication to direct RNA reads. Identical sequences alone do not prove that two read records are the same molecule. Replicate recurrence must refer to biological samples, not lanes or caller outputs.

Use a deterministic, transparent RNA-only ordering. First separate supported, ambiguous and rejected evidence states. Within the supported set sort by: biological samples with support; distinct qualifying reads; median split-versus-single score margin; median shorter-side anchor length; number of callers. Sort all evidence quantities descending and use a stable ID for display-only tie breaking. Report tied-rank intervals and tie-aware recall. Keep singletons in the ranked list; a high-confidence singleton and a recurrent candidate are distinct evidence situations.

This is a review priority, not a probability of biological truth. ORF length, folding confidence, gene function, published probe membership and experimentally supported status cannot influence the RNA ranking. A simple read-count ranking should be retained as a baseline.

Before inspecting new candidate-to-validation joins, write a freeze bundle containing candidate tables, excluded/unresolved proposals, read evidence, filter configuration, ranking specification, sequence-reconstruction rules, ORF/structure eligibility, sensitivity-analysis definitions, code commit, input hashes and timestamps. Store the bundle checksum in a signed or independently timestamped record where feasible. Comparison steps consume this bundle read-only. Any subsequent fix creates a new explicitly labelled analysis version; the original result remains reportable.

Validate engineering with synthetic single-transcript reads, non-coding transcripts, same-gene splice variants, cross-gene joins, paralogue ambiguity, both strands, junction-spanning codons and sequencing indels. These are implementation controls, not biological labels. Use non-flagship pilot data for runtime and label-free calibration; record every tuning decision. Do not tune thresholds to force recovery of Gsdmd–Tmem106a.

**7. RNA reconstruction, exon and coding QC, then translation output**

Add an explicit **exon and coding QC classifier** between RNA reconstruction and release of protein sequences for folding. Begin with transparent rules, not a learned classifier: the annotation, alignment and ORF evidence already support interpretable categories, while biological training labels remain limited. The stage includes ORF enumeration and provisional translation; it runs before protein FASTA export and structure prediction, not before any computation of reading frames.

Give each candidate two independent assessments. **RNA origin** is single-gene, intergene on the same chromosome, interchromosomal, or unresolved because of competing mappings. Resolve gene/transcript IDs, exon order, strand and splice boundaries against the pinned comprehensive GENCODE annotation. Exon numbers must be attached to their transcript accession/version because isoforms can number exons differently. Gene-origin checks feed the RNA candidate decision before its freeze. **Coding status** is a complete junction-spanning ORF, a junction-spanning ORF conditional on reference completion, no junction-spanning ORF detected under the specified search, or an incomplete/ambiguous coding sequence. Coding status determines folding eligibility without changing the frozen RNA evidence ranking.

Check which portions of exons are observed and which are inferred; do not require every parental exon or every segment to be a complete known exon. A short predicted product relative to a parent is distinct from an incompletely sequenced coding region. A stop upstream of the junction prevents that particular ORF from encoding a fusion protein but does not invalidate the fusion RNA or exclude other ORFs. A stop downstream of the junction may be the legitimate end of a novel protein. Check potential sequencing indels and reconstruction assumptions before interpreting apparent frame disruptions.

Add an exon/ORF viewer using an interactive SVG schematic alongside IGV read inspection. Show parental reference transcripts, the observed read-supported exon path, the reconstructed RNA, and selectable ORFs. Colour by gene; label chromosome, strand and transcript; mark the fusion boundary, start/stop positions, untranslated regions, complete/partial exon coverage and frame relative to each parental CDS. Distinguish observed sequence from inferred sequence visually. Selecting an alternative transcript or ORF updates the display, while a saved manual interpretation remains separate from the frozen primary classification. No manual figure editing should alter the underlying evidence.

The supplied Gsdmd–Tmem106a schematic is the design example: exons downstream of the new stop remain part of the RNA without contributing to that predicted protein. Its alternative-frame tail and shortened upstream protein fragment must not trigger automatic rejection. Keep RNA-supported candidates with no resolved protein in the RNA catalogue; route ambiguous coding hypotheses to review and only eligible, explicitly labelled sequences to folding.

Keep three sequence objects: the original noisy read; a consensus where multiple reads support the same exon path; and a reference-exon reconstruction conditional on that path. Each inferred or replaced nucleotide needs a provenance record. Do not merge different isoforms during consensus or correct all reads jointly in a way that could erase a rare junction. A single read cannot establish every missing base or a missing 5′ end.

Use the raw sequence to support the junction and identify discrepancies; use reference-assisted sequences for a paper-compatible translation hypothesis. Preserve equally supported isoform paths and sequence variants. Distinguish complete observed CDS, complete but reference-completed CDS, and partial/unresolved CDS. Agreement with a reference-repaired protein is weaker than independent base-level recovery.

Enumerate forward-strand ORFs in all three frames after orienting each reconstructed RNA biologically. Start with the paper-compatible ATG, standard-code stop codons and 90-nt minimum using orfipy. Confirm stop-codon length semantics in tests. Require the translated coding interval, excluding the stop codon, to cross the junction. Record how bases from both parents contribute, including a codon assembled from both sides. Preserve all qualifying ORFs with their start, stop, frame, CDS completeness, start-codon context and sequence source; an annotated upstream start may be flagged, but not used to discard other alternatives silently.

Translate the assembled nucleotide sequence continuously. The downstream RNA may be in a different frame from its parental CDS without any ribosomal frameshift. Never concatenate the two annotated parental proteins or force both parental frames to agree. Non-coding parent annotation does not itself prohibit an ORF hypothesis.

A read containing a frameshifting error can change the whole downstream protein. Report the raw-versus-reconstructed translation difference and unresolved alternatives. Do not select the nucleotide correction or ORF that obtains the best structure score.

**8. Structure programme**

Use a single intact protein chain for each fusion. The two RNA parents are not separate protein chains. Deduplicate identical amino-acid sequences by hash while retaining links to every candidate and ORF.

Proposed eligibility is: an accepted RNA candidate, a junction-spanning ORF under the frozen rule, a complete start-to-stop CDS in an explicitly identified reconstruction, and no unresolved amino-acid identity in that CDS. Reference-completed proteins are eligible only as labelled conditional predictions. Partial proteins can have exploratory fragment models, but those do not count as complete-protein recovery. Ambiguous/rejected RNA candidates retain their status and are not rescued by a fold. Report all eligibility exclusions and all execution failures.

Run local **Boltz-2 for every distinct eligible sequence**, with a pinned checkpoint and five retained diffusion samples per input. Use no paper structure as a template or constraint. Select the representative using a frozen within-model rule and report the complete ensemble. Boltz provides MIT-licensed code and weights; its small-molecule affinity output is irrelevant to this RNA/protein existence question. [Repository](https://github.com/jwohlwend/boltz), [prediction inputs and outputs](https://raw.githubusercontent.com/jwohlwend/boltz/main/docs/prediction.md).

Generate MSAs from the actual translated fusion sequence, cache them, and record database versions or server provenance. Examine coverage separately on both sides of the junction. Do not stitch unrelated parent alignments into artificial full-length homologues, and do not align an alternative-frame tail to the canonical downstream protein as if they were homologous. Prespecify a no-MSA sensitivity run for sparse/partial-coverage inputs. Changing public MSA services can limit exact reruns even with identical model seeds.

Use **ESMFold2 in single-sequence mode** for a prespecified cross-check set: the top 20 RNA-ranked eligible proteins, a fixed-seed sample from lower ranks, and Gsdmd–Tmem106a as a separately labelled known case. If resources permit, extend that same model to the full set. Its released implementation supports optional MSAs and single-sequence inference; this motivates the cross-check, not a claim that it is the best model for chimeras. [Official implementation](https://github.com/biohub/esm).

For the flagship, add **AlphaFold 3** using the recovered sequence and the paper's stated seed. Check research-use eligibility and model access before choosing server or local execution. Archive full inputs, outputs, model/server date and settings. A seed alone does not reproduce a changing server, MSA database or backend. [AlphaFold 3 repository](https://github.com/google-deepmind/alphafold3), [weights terms](https://github.com/google-deepmind/alphafold3/blob/main/WEIGHTS_TERMS_OF_USE.md).

Record per-residue pLDDT, PAE, pTM where provided, junction-window and tail confidence, sample-to-sample structural variation, and numerical/geometry warnings. Specify each model's confidence scale; do not compare raw scores as if they had identical calibration. Use cross-junction PAE within a fusion chain; ipTM is relevant only to actual multichain models. High confidence in a parental fragment does not establish confidence in the novel tail or in their relative placement.

Separate uncertainty about RNA detection, transcript sequence, ORF choice and predicted conformation. Low-confidence disorder is a valid modelling outcome, not evidence that the RNA or protein does not exist. Model agreement is not experimental validation. Do not silently restrict the promised batch to the top candidates, truncate long proteins, or drop failed folds; use a completion ledger and larger-memory retries for eligible jobs that fail.

**BioNeMo deployment decision.** I read the toolkit's [Boltz-2 skill](/Users/cheparukhin/.codex/plugins/cache/openai-curated-remote/bionemo-agent-toolkit/0.1.0/skills/boltz2-nim/SKILL.md), [MSA-Search skill](/Users/cheparukhin/.codex/plugins/cache/openai-curated-remote/bionemo-agent-toolkit/0.1.0/skills/msa-search-nim/SKILL.md), Boltz API/validation references and OpenFold3 guidance. Use these for concrete adapters and preflight rather than inventing API payloads. They are deployment guidance; no NIM inference was executed here.

Pilot Boltz-2 NIM on Brev with a pinned image digest, cached model files, explicit fusion-chain inputs and saved raw responses. Request five samples and `write_full_pae=true`; verify sample count, full sequence identity, confidence array indexing and matrix dimensions. Current NVIDIA 1.8.0 documentation provides full PAE plus aggregate confidence fields. Verify how per-residue confidence is exported, and whether seed control is available in the deployed version; the documented request schema has no seed parameter. If these requirements cannot be met, use the pinned open-source Boltz runner for the primary batch and retain NIM as a deployment comparison. Never label an aggregate confidence scalar as per-residue pLDDT. [NVIDIA inference documentation](https://docs.nvidia.com/nim/bionemo/boltz2/1.8.0/inference.html).

Use MSA-Search NIM for actual fusion-protein sequences. A hosted pilot can avoid a large database download if account quota permits; cache the returned A3M and request metadata. For sustained local processing, choose the database set before launch, use the toolkit's parallel-download plus `NIM_MODEL_NAME` route, and keep database versions/checksums. Query-only MSAs should be explicit controls, not silently substituted for failed searches. A fusion monomer requires a single-sequence query; paired searches are reserved for genuinely separate interacting chains.

The toolkit's example Boltz image is 1.6.0 while the checked official documentation includes 1.8.0. Do not mix their schemas: inspect the selected image's API and record the resolved version. Local NIM startup requires verified NGC access, the documented API-key fallback and persistent cache paths; Brev GPU access alone does not establish NGC entitlement. Keep credentials outside logs and artifacts. NIM packaging terms are separate from the underlying model's open-source licence.

Local MSA storage is material: NVIDIA's MSA-Search 2.5 documentation lists 1,660 GB for the full database set, while the toolkit describes a roughly 490-GB UniRef30-only setup. Reserve at least a separately sized database volume plus container/cache headroom; the full set needs more than a 1-TB disk. Start with the smaller pinned profile or hosted service, and declare broader database searches as a preplanned sensitivity analysis. Do not run a resident MSA GPU server and a fold model concurrently on one GPU unless their combined memory has been measured. [NVIDIA support matrix](https://docs.nvidia.com/nim/bionemo/msa-search/2.5.0/prerequisites.html).

OpenFold3 NIM is an optional disagreement-resolution model if ESMFold2 cannot be deployed or additional complex modelling is needed. Declare a model substitution before the relevant comparison; OpenFold3 output is not an exact reproduction of AlphaFold 3. Binder-design and molecule-generation parts of BioNeMo do not advance this reproduction task.

**9. Comparison with the paper**

After the freeze, join external validation evidence at its actual resolution. Compare ordered gene pairs, exact junctions, tolerance-based junctions, exon paths, nucleotide sequences and translated proteins separately. A pair-level NanoString label must not be assigned to every proposed isoform. Keep assayed-and-supported, assayed-but-not-detected, assay-unresolved and untested categories distinct.

For Gsdmd–Tmem106a, the expected reference is the Gsdmd exon-2/Tmem106a exon-6 junction and a 118-aa product with 73 upstream-derived residues and a 45-aa alternative-frame tail. The paper presents both an isolated prediction and co-folding with GSDMD-NT. [Paper](https://www.nature.com/articles/s41586-026-10982-x). The prior task reported a singleton long-read entry; independently verify that count during post-freeze reconciliation rather than hardcoding a rescue.

Check the complete amino-acid string, not merely its length or first domain. Obtain an explicit published sequence from source/supplementary records, retaining the extraction provenance. A reconstructed expected sequence is not automatically an independently supplied author sequence. If modelled separately, the published sequence is a positive comparison control and must never replace a failed de novo recovery.

Request or locate the authors' coordinate files, exact construct, chain stoichiometry and confidence files. With coordinates, report sequence-mapped RMSD, TM-score with stated length normalization, aligned coverage, secondary structure and contacts, for the full protein and its two sequence regions. For co-folding, match partner construct and stoichiometry first; a convenient heterodimer is not automatically equivalent to a pore-context prediction. A figure alone allows a qualitative comparison, not a defensible numerical structural match.

For every reference example, produce a stage trace: raw read located; candidate proposed; single-transcript test; mapping ambiguity; junction accepted; rank; reconstructed transcript; ORF found; sequence match; structure eligibility; fold status; structural comparison. Report the first blocking stage and all other flags. If the input data never sampled a reference example, distinguish that from removal by a filter.

Report recovery at fixed review budgets (for example 20, 100 and 1,000), exact/tolerant match counts, sequence discrepancies and changes between the two branches. Stratify by singleton support, biotype and readthrough/interchromosomal class. Untested candidates are not false positives, and these selected validation assays cannot establish catalogue-wide biological precision or FDR.

**10. Brev execution and resources**

The earlier project's [controller record](/Users/cheparukhin/Documents/Codex/2026-09-18/t/outputs/chimeric-rna-prioritization/docs/remote_controller.md) documents 4 vCPUs, 16 GiB RAM and 50 GiB disk. This is a historical configuration, not a fresh inventory check. It is adequate for orchestration and insufficient for this full raw-data workflow.

My initial planning allocation is a separate CPU worker with roughly 32 vCPUs, 128 GiB RAM and 1 TB working storage, adjusted after one complete sample. TYPHON documents at least 64 GB RAM and approximately 8–10 times compressed-input size in disk space; retained audit intermediates can increase that. Do not equate the 45.5-GB SRA archive estimate with compressed FASTQ size. Measure extraction scratch, BAMs, indices and caller intermediates before processing all samples. [TYPHON requirements](https://github.com/erenada/TYPHON).

Use one A100 80-GB or H100 80-GB GPU worker for the initial Boltz/ESMFold2 pilot. This is a conservative planning choice, not a minimum-memory guarantee. Benchmark representative short, median and long candidates; use smaller hardware if measured cost per completed protein improves. Run models in separate environments. Keep alignment jobs off the GPU worker where possible. Brev provides CUDA, Docker and SSH-capable instances. [Brev documentation](https://docs.nvidia.com/brev/concepts/gpu-instances).

Estimate the batch only after counting distinct eligible proteins: sum measured runtime by sequence-length bin × sampling settings, then add MSA, setup and retry time. Do not promise a runtime or dollar figure from the number of gene pairs. Save caches and outputs on persistent storage and copy the manifest/results before terminating a worker. A stopped instance can retain storage charges; deletion removes its local data.

Carry forward the earlier budget policy as a planning constraint: one GPU worker, bounded jobs, fresh combined price checks and shutdown after completion/failure. Its preferred rate and ceiling are not provider-enforced limits or new authorization to spend. No resources were provisioned in preparing this proposal.

**11. Deliverables and acceptance gates**

**Shared Codex access from the CPU VM.** Use one Codex CLI session inside `tmux`, named `chrna-codex`, on `chrna-controller`. Teammates with existing Brev SSH access attach to the same terminal and see the same conversation and command output. Coordinate one person typing at a time; others can attach read-only if desired. `Ctrl-b`, then `d` detaches without stopping Codex. This survives SSH disconnections, not VM reboots; the saved Codex task can be resumed after a reboot. Keep Snakemake's durable run state for the scientific workflow. No custom dashboard, operator tokens or separate application logins are required. The earlier App Server/token design was withdrawn and its running service and tokens removed; the team API login and saved task are retained.

| Deliverable | Required content |
|---|---|
| Reproducible workflow | Snakefile/rules, locked containers/environments, input manifest, reference hashes, run instructions, meaningful fixture tests, resource profile and run logs |
| Candidate evidence | One junction table plus linked read and transcript tables; support, samples, competing explanations, anchors, ambiguity, category, rank and tie interval |
| Filtering record | Per-read and per-candidate decisions with rule/version, observed value, threshold, reasons, alternate mappings and funnel counts |
| Sequence records | Raw/consensus/reference-assisted RNA FASTAs, nucleotide provenance, exon paths, junction offsets, ORF table and protein FASTA |
| Freeze bundle | Immutable candidate/rule/ranking snapshot and hashes, with predeclared comparison and structure protocols |
| Structure predictions | All eligible sequence hashes, model inputs, checkpoint/MSA provenance, mmCIF/PDB, ensembles, confidence arrays and explicit failure/eligibility ledger |
| Comparison report | All supported reference examples with stage traces; exact and tolerant junction recovery; full protein comparisons; flagship structural comparison and remaining uncertainty |

Suggested relational keys are `sample_id`, `read_id`, `junction_id`, `transcript_hypothesis_id`, `orf_id`, `protein_sha256` and `structure_run_id`. Store an append-only decision table rather than a single overwritten pass/fail column.

Proceed through five gates: (1) verify archive/sample/reference identities and environment readiness; (2) demonstrate one complete sample plus synthetic-control tests; (3) run all mouse samples and freeze discovery outputs; (4) finish reconstruction and every eligible fold under the frozen rules; (5) reveal comparison inputs and produce discrepancy traces. Validation labels stay outside discovery execution. The flagship can remain unrecovered without making the workflow fail; a correctly explained non-recovery is a scientific result.

The unresolved prerequisites are exact sample-specific JAFFAL reference/version choices, retention of original ONT read names after archive extraction, availability of raw signal, and author structure/sequence files. None prevents writing the pipeline, but each limits what degree of reproduction can honestly be claimed. The first concrete implementation task is the intake manifest and one-sample discovery/audit run—not model training.

Local readiness check for this proposal found Python and a Docker executable on PATH, but not Snakemake, minimap2 or SAMtools. Docker daemon readiness, the current Brev inventory, NGC entitlement and remote GPU compatibility were not tested. The generic NGS preflight registry has no fusion-analysis profile; implementation needs a task-specific preflight covering the selected callers, references and model adapters. No installation or working-runtime claim is implied by this proposal.
