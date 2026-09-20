"""Build a numerical execution summary from actual campaign manifests."""
from pathlib import Path
import json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];b=ROOT/'results/structure_campaign'
def j(path):
 p=b/path;return json.loads(p.read_text()) if p.exists()else{}
c=j('cohort/manifest.json')['counts'];d=j('analysis/census_summary.json');domains=j('domains/manifest.json');reg=j('analysis/region_summary.json');div=j('analysis/diversity_summary.json')
metrics=b/'compute/model_metrics.tsv';models=pd.read_csv(metrics,sep='\t')if metrics.exists()else pd.DataFrame();rows=[]
structural_rows=[]
structural_notes=[]
cluster_path=b/'diversity/clusters.tsv'
clusters=pd.read_csv(cluster_path,sep='\t') if cluster_path.exists()else pd.DataFrame()
for protocol in div.get('protocols',[]):
 key=protocol['protocol_id']
 candidate=clusters[clusters.protocol_id.eq(key)&clusters.role.eq('sensitivity')] if len(clusters)else pd.DataFrame()
 count=candidate.peptide_id.nunique() if len(candidate)else 0
 nclusters=candidate.cluster_id.nunique() if len(candidate)else 0
 structural_rows.append(f"| {key} | {protocol['candidate_peptides_in_rarefaction_denominator']} | {count} | {len(candidate)} | {nclusters} |")
 if key=='boltz2_2.2.1_single_sequence':
  denominator=protocol['candidate_peptides_in_rarefaction_denominator']
  structural_notes.append(f"Only {count}/{denominator} candidate models contain qualified spans; the remaining {denominator-count}/{denominator} are unclassified by this procedure. This limited coverage prevents a broad conclusion about chRNA fold diversity.")
gate_note=''
gate_path=b/'diversity/gate_sensitivity.tsv'
if gate_path.exists():
 gate=pd.read_csv(gate_path,sep='\t');gate=gate[gate.protocol_id.eq('boltz2_2.2.1_single_sequence')&gate.population.eq('candidate')]
 gate_note='With the span-length and 80%-of-residues requirements fixed, candidate coverage is '+', '.join(f"{int(r.peptides_with_passing_spans)}/{int(r.actual_validated_peptide_denominator)} at residue pLDDT ≥{int(r.residue_plddt_threshold)}" for r in gate.itertuples())+'. These are screening-threshold sensitivities, not alternate structural-cluster counts.'
robustness=j('analysis/structure_metric_summary.json')
if len(models):
 for protocol,g in models.groupby('protocol_id'):
  good=g[g.status.isin(['verified','cached_verified'])]
  rows.append(f"| {protocol} | {len(g)} | {len(good)} | {good.sequence_sha256.nunique()} | {int(good.reused_prior_prediction.astype(str).str.lower().eq('true').sum())} |")
text=f'''# Executed chRNA protein-hypothesis campaign

## Main result

Among **{d['n_conditional_peptides']} conditional annotated-start peptide hypotheses** from **{d['n_source_pairs']}/{d['n_reference_pairs']} NanoString-supported RNA pairs**, metapredict V3 calls **{d['n_predominantly_disordered_v3']} ({100*d['fraction_predominantly_disordered_v3']:.1f}%) predominantly disordered** (more than half the residues called disordered). V1 sensitivity calls **{d['n_predominantly_disordered_v1']} ({100*d['fraction_predominantly_disordered_v1']:.1f}%)**. Most hypothetical peptides are therefore not predominantly disordered under either method; that is not proof of a stable fold or biological function.

Mean per-peptide disordered fraction is **{100*d['peptide_equal_mean_f_idr']:.1f}%**, median **{100*d['peptide_equal_median_f_idr']:.1f}%**, and pooled residue fraction **{100*d['residue_weighted_f_idr']:.1f}%**. These are different summaries. Giving each RNA pair equal weight yields mean hypothetical-peptide disordered fraction **{100*d['pair_equal_mean_hypothesis_f_idr']:.1f}%**; equal weighting across alternatives is descriptive, not an expression probability.

**Strict observed-chain primary eligibility is {c['strict_primary_peptides']}.** Public junction evidence does not settle complete exon-chain/start usage. The executed set is an explicitly conditional reference-reconstruction sensitivity arm, not a measured proteome. {c['conditional_consensus_unique_peptides']} peptides are invariant across compatible reference isoform combinations. {d['n_pairs_without_eligible_conditional_peptide']} RNA pairs have no eligible annotated-start peptide in this reconstruction; they are unresolved rather than scored as disordered or noncoding. The additional {c['alternative_start_only_unique_peptides']} alternative-start peptides are analyzed separately.

## Domain and context evidence

Local Pfam {domains.get('pfam_release','unavailable')} search found gathering-threshold domain matches in **{domains.get('candidate_sequences_with_hits','unavailable')}/{d['n_conditional_peptides']}** conditional peptides. See [domain methods](domains/METHODS.md) for profile thresholds, overlap handling and domain-truncation comparisons. A match suggests familiar sequence architecture; no match does not establish a novel fold or lack of function.

There are **{reg.get('n_deduplicated_native_context_comparisons',0)}** deduplicated comparisons of the same amino-acid region in hypothetical fusion versus complete native-parent context and **{reg.get('n_deduplicated_retained_fragment_comparisons',0)}** isolated-fragment comparisons. Median predicted-disorder difference is **{reg.get('native_context_median_delta_f_idr','unavailable')}** for native-context comparisons. These are model context effects, with related sequences/alternative source mappings retained, not independent biological replicates or causal measurements.

The published functional **Gsdmd–Tmem106a** exemplar illustrates the limit of an order-based function filter: its reconstructed118-aa peptide is called100% disordered by V3 but48.3% by V1, while the separately cached MSA-backed Boltz model has mean pLDDT48.7. Neither prediction overrides the paper's functional evidence or directly measures physical disorder.

## Actual structure execution

| Protocol | Jobs in ledger | Verified jobs | Unique verified sequences | Reused jobs |
|---|---:|---:|---:|---:|
{chr(10).join(rows) if rows else '| Not yet available | 0 | 0 | 0 | 0 |'}

Completion is technical success, not protein-function validation. MSA-backed and single-sequence models are distinct protocols; their confidence values are not pooled. Failures and deferred inputs remain in the ledger. Seed repeats are additional predictions of the same sequence, not additional proteins. Structural diversity is reported only for confidence-qualified, contiguous domain spans and actual successful searches; missing coverage remains explicit.

## What the structures establish

| Protocol | Verified first-pass candidate peptides | Candidates with qualified spans | Qualified candidate spans | Clusters containing candidates |
|---|---:|---:|---:|---:|
{chr(10).join(structural_rows) if structural_rows else '| Not yet available | 0 | 0 | 0 | 0 |'}

{chr(10).join(structural_notes)}

{gate_note} See [gate sensitivity](diversity/gate_sensitivity.tsv).

Each eligible span is a contiguous Pfam alignment of at least 50 residues, with at least 80% of residues at pLDDT ≥70. Actual-coordinate Foldseek/TM-align comparisons require alignment TM-score ≥0.5 and coverage ≥0.8 on both spans. Clusters are graph connected components, so membership can be transitive. Overlapping annotations and repeats within one protein are not independent proteins. Control-only clusters are excluded from this table. These counts describe the selected, confidence-qualified subset; they do not estimate total chRNA fold diversity or establish new folds.

The robustness audit contains **{robustness.get('same_protocol_seed_comparisons',0)} same-protocol seed-pair comparisons**. Fitted coordinate RMSD measures prediction reproducibility, not thermodynamic stability. See [seed comparisons](analysis/seed_robustness.tsv), [junction confidence and cross-junction PAE](analysis/model_region_metrics.tsv), and [structural-diversity methods](diversity/METHODS.md). Missing qualified structure remains unresolved rather than classified as disordered or nonfunctional.

## Deliverables

- [Offline searchable atlas](report/index.html)
- [PowerPoint gallery](report/structure_campaign_gallery.pptx)
- [Figure generation and interpretation guide](report/FIGURE_GUIDE.md)
- [Cohort methods](cohort/METHODS.md), [disorder methods](analysis/METHODS.md), [domain methods](domains/METHODS.md)
- [Execution changes, constraints and reproduction commands](EXECUTION.md)
- [Frozen folding selection](selection/selection.tsv) and [diagnostic repeat selection](selection/seed_repeats/selection.tsv)
- [Joined candidate evidence table](analysis/candidate_evidence_table.tsv)

All derived campaign data and caches are under `results/structure_campaign/`. No claim of translation, novel function, druggability, or population-wide disorder prevalence follows from these predictions.
'''
text=text.replace('reconstructed118-aa','reconstructed 118-aa').replace('called100%','called 100%').replace('but48.3%','but 48.3%').replace('pLDDT48.7','pLDDT 48.7')
(b/'RESULTS.md').write_text(text)
inputs=['cohort/manifest.json','analysis/census_summary.json','analysis/summary.json','analysis/region_summary.json','domains/manifest.json','analysis/diversity_summary.json','diversity/clusters.tsv','diversity/gate_sensitivity.tsv','analysis/structure_metric_summary.json','compute/model_metrics.tsv']
(b/'summary_provenance.json').write_text(json.dumps({'inputs':{p:hashlib.sha256((b/p).read_bytes()).hexdigest()for p in inputs if(b/p).exists()},'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((b/'RESULTS.md').read_bytes()).hexdigest()},indent=2)+'\n')
print(b/'RESULTS.md')
