# Dashboard extension to the K562 pilot prompt

Build an interactive evidence-to-experiment dashboard alongside the analytical deliverables. Use an exact-junction candidate selector and six linked views:

1. **Why the RNA is credible.** Show individual and aggregate read support, biological replication, protocol corroboration, alternative mappings, artifact evidence, origin uncertainty, and source provenance. Keep DNA and Hi-C evidence distinct from RNA support.
2. **Whether translation is supported.** Show observed versus reference-assisted sequence, junction-spanning ORFs, frame and NMD annotations, transcript completeness, and any ribosome or protein evidence. Use “unknown” when appropriate. Do not invent a probability of protein production from an ORF or folding confidence.
3. **Which modality is justified.** Compare an RNA-directed reagent, a junction binder and a small molecule. Explain sequence uniqueness, accessible epitope or pocket, localization, delivery, functional evidence and target selectivity requirements. Distinguish a biochemical detection reagent from a therapeutic intervention. Scenario controls must never change observed evidence.
4. **Generated molecules or binders.** Import actual generation outputs only after an eligible target and bounded job exist. For each design, retain a sequence or SMILES, target sequence/structure hashes, junction or pocket definition, model/checkpoint, seed, parameters, output artifacts and execution status. Keep computational predictions separate from measured binding. If generation has not run, show an explicit empty state. Illustrative records must be visibly synthetic and excluded from scientific results.
5. **Counter-screening against both parents.** Show the same design against the chimera, parent A and parent B, using matched methods, comparable constructs and relevant parental isoforms. Preserve uncertainty and failures. A missing screen cannot pass selectivity; weaker predicted parent interaction is not evidence of absent binding. Include junction specificity and a broader off-target assessment. For RNA-directed reagents, also compare both parental transcripts and the wider transcriptome.
6. **The next experiment.** Identify the immediate evidence gap, proposed assay, necessary controls, decision criterion, and finding that would weaken the hypothesis. Start with independent RNA confirmation and same-culture DNA assessment where needed. Protein detection, experimental binding/selectivity and function are separate subsequent decisions.

Use an evidence-first default. Provide candidate-level exports carrying the same source scope and caveats as the visible view. Preserve unknown, not assessed, failed, predicted and measured as distinct states. Do not pool them into one opaque score. Include a clearly separated demo mode where real outputs are unavailable.

Acceptance requires all six views, working selection and drill-down, preserved provenance, honest missing-data states, checks for cross-candidate contamination, export verification and desktop/mobile rendered review. A polished dashboard is not evidence that the underlying biological or generation jobs ran.

## Local demonstration delivered

- Authoring project: `demos/chimera-dashboard/`.
- Data reproducer: `scripts/build_demo_snapshot.py`.
- Default view: fictional demonstration, including three fictional binder-review records with no sequences or model outputs.
- K562 view: explicitly unexecuted; no imported K562 candidate results.
- Real-data view: ten selected mouse-pilot sequence hypotheses joined to their frozen exact-junction RNA ranking. These remain separate from K562 and from the fictional designs.
- No new discovery, folding, molecule generation, binder design or counter-screening computation was executed for this dashboard task.
