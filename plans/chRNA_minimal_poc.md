# chRNA hackathon: minimal proof of concept

## Objective and scope

**Question:** Does 3D genome context help prioritize overlooked chimeric RNAs for independent validation?

Build a reproducible mouse macrophage candidate dataset, a small classifier, and an evidence explorer. Compare an RNA-only model with the same model augmented by Hi-C. A negative result is acceptable: demonstrate the experiment clearly rather than promise an improvement.

Team: 2–3 builders. Deadline: tomorrow; freeze the working demo at least three hours before the actual presentation time. The schedule below is relative to implementation kickoff.

Minimum deliverables:

1. Published candidate/evidence tables reconstructed with provenance and explicit evidence levels.
2. A retrospective classifier predicting **reported NanoString support within the probe-design panel**.
3. A held-out comparison of read-support ranking, RNA-only classification, and RNA + Hi-C classification if the Hi-C feasibility gate passes.
4. One working demo: ranked candidates → junction/evidence details → source-grounded biological explanation.
5. Reproduction command, pinned dependencies, cached outputs, and five-minute presentation.

Full raw-data TYPHON reproduction, SG-Nex discovery, protein structures, pathway screening, docking, molecule generation, and general arbitrary-modality prediction are outside the minimum. Do not run these in parallel until the core result and demo are frozen.

## Scientific target and data contract

Reference: `docs/Venezia_2026_reproduction_notes.md` and the supplied paper in `docs/`.

The published spreadsheets inspected during scoping contain:

- Supplementary Table 8: 529 distinct probe-design IDs and junction sequences.
- Supplementary Table 7: 109 NanoString-supported gene-pair IDs, 287 short-read-supported IDs, and 13 cross-supported IDs.
- Exact matching joins 107 NanoString IDs to the probe panel. `Aoah:Sirt5` and `Tbc1d23:Xdh` require reconciliation. Never silently rename them or inflate the matched count.

These are table counts, not a claim that 529 probes passed assay QC. Table 7 uses gene-pair labels, not complete junction identities.

**Primary target:** membership in the published NanoString-supported list among mapped biological probe-panel candidates. Positive means reported supported; zero means not reported supported. Exclude controls and unresolved identities. Preserve separate flags for probe design, confirmed assay testing, QC status, and reported support. Unknown testing/QC remains unknown; never describe these zero labels as proven non-chRNAs or confirmed assay failures.

If complete assay results and QC become available, produce a secondary analysis restricted to successfully tested probes. Do not reverse-engineer labels from heatmap values or assume the notes' threshold paraphrase resolves the paper's ambiguous filtering wording.

Use one evaluation row per ordered gene pair in the mapped probe panel. Retain probe sequences and junction records separately. Aggregate long-read read IDs without double-counting caller overlaps; sum support over the pair's observed junctions and count unique supporting biological samples. Display exact junction evidence where available, while labeling predictions as pair-level. Do not propagate a pair-level positive label into supposedly validated junction isoforms.

Dataset outputs under `results/dataset_reconstruction/`:

- `candidates.tsv`: ordered pair ID, species/build, parent IDs, chromosomes, evidence summaries, source references.
- `junctions.tsv`: pair ID, ordered breakpoint coordinates/strands, sequence when available, supporting read/sample provenance.
- `probe_panel.tsv`: probe ID, pair mapping, sequence, plate, control/test/QC flags, published support label, exclusion reason.
- `manifest.json`: source URLs, file checksums, annotation versions, retrieval date, transformation versions.
- `audit.md`: counts, duplicate handling, unmatched IDs, evidence definitions, and unresolved limitations.

Use mouse GRCm39 / GENCODE M28. Preserve parent order, colon-separated names, and stable identifiers; gene symbols alone are not an unrestricted alias-matching license. Table 3/4 supplies long-read evidence; Table 7 supplies evaluation labels; Table 8 defines the candidate panel. Keep short-read support as displayed orthogonal evidence, not an input to the primary experiment.

## Classifier and evaluation

**Baseline:** descending deduplicated long-read support, with stable pair-ID tie breaking.

**RNA model:** L2-regularized logistic regression, fixed C=1, no class weighting or hyperparameter search. Features: log1p total long-read support, supporting-sample count, interchromosomal indicator, and log1p minimum genomic separation between parent gene intervals for intrachromosomal pairs. Set separation to zero for interchromosomal pairs and retain the indicator. Do not use gene names, NanoString measurements, probe plate, published validation flags, or downstream literature summaries as predictors. Caller count is not useful within a panel selected for three-caller agreement.

Fit median imputation, missingness indicators, and scaling on training data only. Exclude candidates with unmappable parent coordinates rather than inventing genomic context. Report actual feature availability; do not substitute zero for unavailable read evidence.

**RNA + Hi-C model:** the same classifier and RNA features plus one prespecified spatial feature: log2(0.5 + local contact enrichment) from control-siRNA, LPS-stimulated macrophages. Use processed GSE324391 contact data at the paper's 500-kb resolution and the paper/GENOVA foreground-to-background definition. Map probe junction coordinates to bin pairs; average enrichment across distinct mapped bin pairs for a gene pair. Treat zero/undefined background as missing. Exclude CTCF-knockdown data from predictor construction; reserve it for biological context. Record the timing mismatch between the Hi-C and RNA experiments.

Do not use the unlabeled vectors in Figure 2 source spreadsheets as candidate-specific features: the inspected effect tables lack candidate identities. Resolve the exact processed-file format and normalization before extracting contacts. Never infer missing identities from row order.

**Evaluation:** deterministic five-fold out-of-fold predictions, seed 42. Form groups as connected components of pairs sharing any parent gene; keep each component entirely in one fold. Balance label counts across groups where feasible. All preprocessing is fold-local. Compare all three methods on identical rows with observed Hi-C; additionally evaluate RNA-only on the full eligible panel. This prevents missing Hi-C coverage from masquerading as model improvement.

Report average precision, positive-label prevalence, precision@20, recall@20, and group-bootstrap uncertainty for the difference in average precision (1,000 resamples of saved out-of-fold predictions). Report interchromosomal performance separately when both labels are present; do not let easy local readthrough cases substantiate a trans-splicing claim. Keep all isoforms, repeated probes, and samples of a pair together.

If five folds cannot contain both classes, use three. If three valid gene-disjoint folds cannot be formed, report the limitation and descriptive ranking only; do not silently relax to a leaky random split. Keep Gsdmd–Tmem106a and Cd274–Lacc1 as traceable examples using their out-of-fold scores, without tuning to improve their ranks.

Classifier outputs are **reported-support scores**, not calibrated probabilities of biological authenticity, translation, function, or druggability. Generalization beyond the selected probe panel is exploratory. After evaluation, fit on all eligible panel data to rank remaining published candidates, clearly marking those rankings as outside the evaluation population.

Outputs under `results/classifier/`: feature table, fold assignments, out-of-fold predictions, metrics JSON, comparison plot, fitted preprocessing/models, and a concise model card. Provide a single command that regenerates dataset joins, features, evaluation, and demo exports from pinned inputs.

## Feasibility gates and technology use

**First 90 minutes:** reconcile panel labels and gene identities, inspect support availability, establish valid evaluation groups, and inspect processed Hi-C files. Freeze labels before fitting models.

**Hi-C gate:** proceed only if indexed candidate-level contacts can be extracted from available processed files within two hours. Otherwise ship RNA-only classification, explicitly label the spatial hypothesis as untested, and retain Hi-C as the first follow-up. Do not start full raw Hi-C processing overnight as a dependency of the demo.

**NVIDIA — preferred core role:** run Parabricks `rna_fq2bam` on one bounded mouse short-read sample with chimeric output explicitly enabled. Join candidate junction evidence using the paper's ±10-nt breakpoint matching rule on both parents. Use it to produce independent evidence displayed in the explorer, not the NanoString training labels. Record hardware, input size, command, wall time, and output provenance. Verify output against known junction records; do not promise recovery from a tiny subsample. Do not claim acceleration without a matched CPU measurement.

Time-box Parabricks setup and a pilot run to two hours. If unavailable, document the failure and use published short-read evidence for the demo; recognize that this weakens the technology criterion rather than pretending the requirement is satisfied.

**OpenAI — core product role:** generate structured candidate evidence reports from supplied evidence rows and retrieved primary-source passages. Each biological statement must link to its supporting source; distinguish observed support, inferred mechanism, and unknown function. Validate cited IDs and numeric claims against the input rows. Use no LLM-generated evidence as a training label or numeric classifier feature. Cache reports for the presentation and retain prompts, model identifier, and source snapshots for reproduction.

**BioNeMo — stretch only:** after the core is frozen, use a protein model on a small number of correctly reconstructed ORFs for exploratory interpretation. Its output must add a clear biological question, not merely a visual. Predicted structure is not structural ground truth; confidence/disorder is not a test of RNA authenticity or druggability. No forced protein embedding feature in this small RNA-evidence classifier.

## Workstreams and delivery order

Create separate implementation tasks only when requested; this document does not dispatch them.

| Workstream | Owner | Deliverable and dependency |
|---|---|---|
| Dataset and labels | Builder 1 | Dataset reconstruction outputs, identity/QC audit, frozen panel; first priority |
| Models and GPU evidence | Builder 2 | Hi-C feasibility, classifier comparisons, bounded Parabricks run; consumes frozen IDs |
| Explorer and presentation | Builder 3, or Builder 1 after data handoff | Evidence UI, OpenAI reports, animation integration, presentation; starts against explicitly labeled fixture data |

Hours 0–2: data/Hi-C/GPU gates and frozen interfaces. Hours 2–6: baseline, RNA model, Hi-C ablation where feasible, UI integration. Hours 6–8: audit, frozen results, cached reports, rehearsal. Remaining time: fixes first, then one stretch only. Hard presentation freeze takes precedence over these relative windows.

Keep the UI small: ranked table with reported-support score and evidence availability; candidate detail with ordered parents/junction schematic, assay evidence, and cited report; evaluation view with the three-method comparison and limitations. Reuse the existing `animation/` work if suitable. Never display fixtures as real results.

Five-minute presentation:

- 0:00–0:40: biological problem and short animation; therapeutic relevance is motivation, not a drug-discovery claim.
- 0:40–1:20: candidate panel, independent assay target, and 3D-context hypothesis.
- 1:20–2:20: pipeline and held-out baseline/ablation results, including null results.
- 2:20–4:10: live cached demo of two candidates, GPU-generated evidence where available, and source-grounded OpenAI explanation.
- 4:10–5:00: selection bias, missing/QC limitations, coarse Hi-C resolution, and reproducibility; external-data application is the next step.

## Acceptance checks and fallback

- Reproduce published table counts before exclusions and document the final cohort with reasons for every exclusion.
- Resolve or explicitly exclude the two unmatched NanoString names; verify that all labeled rows map to the correct ordered pairs.
- No shared parent genes across evaluation folds; no validation-derived predictors; preprocessing fit only on training folds.
- No duplicated read counts from multiple callers; no gene-pair labels presented as isoform-specific validation.
- Coordinate assembly, parent order, Hi-C bin mapping, and missing-value behavior verified on known examples.
- All metrics recompute from saved predictions. Identical candidate sets underpin each ablation comparison.
- Inspect at least five generated reports, including a supported, unsupported, and missing-data example; verify every numeric assertion and citation.
- Demo runs from cached artifacts without network access. Document the live API path separately; rehearse a recorded backup.
- Repository includes source manifest, environment specification, commands, random seed, artifacts, limitations, and an accurate statement of NVIDIA/OpenAI usage.

Fallback hierarchy: full RNA + Hi-C experiment → RNA-only classifier with spatial hypothesis explicitly untested → transparent evidence ranking if valid labels/splits cannot be established. Always retain the reconstructed dataset, audited evidence explorer, and an honest account of what was demonstrated.

## Sources

- [Venezia et al., Nature (2026)](https://www.nature.com/articles/s41586-026-10982-x)
- [Supplementary Table 7](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10982-x/MediaObjects/41586_2026_10982_MOESM9_ESM.xlsx)
- [Supplementary Table 8](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-10982-x/MediaObjects/41586_2026_10982_MOESM10_ESM.xlsx)
- [Hi-C GSE324391](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE324391)
- [TYPHON](https://github.com/erenada/TYPHON)
- [Parabricks RNA alignment](https://docs.nvidia.com/clara/parabricks/tool-reference/tools/rna_fq2bam)
