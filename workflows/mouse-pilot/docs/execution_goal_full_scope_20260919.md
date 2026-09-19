# Chimeric RNA reproduction: agreed execution goal

Execute the chimeric-RNA reproduction project from our shared Brev CPU machine.

Work in the existing project at /srv/chrna-team/project, using the shared Codex session in tmux. Inspect the repository, project instructions, existing results and available resources first; reuse working components. Keep the shared-terminal setup simple.

Objective: reproduce the original mouse study from its direct long-read RNA data, producing an auditable chain from RNA-junction evidence to reconstructed sequences, predicted proteins and structures.

Use these sources:
- Paper: https://www.nature.com/articles/s41586-026-10982-x
- Primary mouse dataset: GSE267147 / PRJNA1109857.
- TYPHON: https://github.com/erenada/TYPHON
- Planning reference: https://docs.google.com/document/d/1suaqiVIxDCT2D8bvYndyFK6X1NSLv9tCG7VbrBRzrG4/edit?tab=t.eeppo2w5fxj1

The decisions below govern where the planning reference differs.

1. Build a resumable Snakemake workflow with pinned environments and references. Maintain a paper-method baseline using TYPHON's LongGF, JAFFAL and Genion approach, and a separately reported evidence-assessment branch. Audit existing caller filters and respect software licences.

2. Exclude reads adequately explained by one known transcript, including noncoding transcripts. Retain evidence joining two different genes even when both segments are annotated. Preserve singleton candidates, alternative mappings and unresolved cases. Treat microhomology, readthrough proximity, biotype and splice-boundary concerns as explicit annotations or justified evidence decisions, not blanket exclusions. Record reasons for every decision.

3. Rank exact RNA junctions transparently by sequencing evidence: evidence category, biological replication, distinct supporting reads, mapping specificity, junction quality and caller agreement. Prespecify the reconstruction, folding-eligibility and comparison rules. Freeze the candidate list, exclusions, rules and ranking before joining published validation outcomes. Describe this as a retrospective reproduction; the flagship example is already known.

4. Reconstruct supported RNA sequences and plausible transcript alternatives. Distinguish observed, consensus and reference-inferred sequence. Identify and translate junction-spanning ORFs continuously through the RNA, allowing the downstream segment to differ from its parental reading frame. Keep exon completeness, coding uncertainty and NMD predictions separate from the RNA ranking. Do not require full-length parental proteins.

5. Predict structures for every eligible distinct protein sequence using Boltz-2. Use NVIDIA BioNeMo tools where they improve deployment, MSA generation or output validation. Preserve model settings, sequence identity, confidence outputs and failures. Use AlphaFold 3 for the paper-specific comparison when accessible; clearly report unavailable comparisons. Ranking controls processing order, not final folding coverage.

6. After freezing, compare recovered gene pairs, junctions and complete protein sequences with the paper at the resolution supported by each reference. Give Gsdmd-Tmem106a a complete stage-by-stage trace without special rescue rules. Do not equate an unreported candidate with a false positive, or a confident fold with protein existence or function.

7. Deliver a reproducible workflow, candidate evidence table, filtering record, RNA/protein FASTAs, structure files and an HTML report with exon/ORF diagrams and a concise discrepancy analysis. Record scientific review decisions separately from the frozen results.

Start with one complete sample, then process the full mouse cohort. Add a small depth-matched SG-NEx protocol comparison only after the core works. Treat protocol groups as observational categories, not biological truth labels. Defer model training and Hi-C-based prediction.

Use the CPU VM for orchestration and provision temporary Brev workers only for concrete bounded jobs. Check live prices and existing project resources, follow the established budget policy, preserve outputs and stop temporary workers after completion or failure. Measure pilot resource use before scaling.

Proceed through routine implementation and verification without repeated approval requests. Ask only for genuinely missing access, consequential scientific choices or spending outside existing authorization. Report measured results, limitations and remaining work honestly; non-recovery of an expected example is a result to explain.

## Dispatch instructions from the project owner

The owner requested this as a persistent goal in the existing shared session, using gpt-6-astra with medium reasoning and normal speed (Fast off), in execution rather than Plan mode. No token budget was specified. Create or continue the native goal and begin execution. Keep progress, checkpoints and resource accounting in the project so teammates can inspect them. The existing project ceiling is USD 100/hour combined for instances launched for this project; this is a ceiling, not a spending target. Prefer substantially cheaper measured allocations. Do not change authentication or build a custom shared-session service.

Additional scientific clarifications from reconciliation: direct RNA is not artifact-free; cDNA-only does not prove artifact. RNA evidence alone does not prove trans-splicing rather than readthrough or a DNA rearrangement. BCR-ABL1 is a fusion-detection control, not a physiological trans-splicing control. Do not tune tiers to place Gsdmd-Tmem106a first. Keep published-sequence controls distinct from de novo recovery, and require author coordinates for quantitative structural agreement.
