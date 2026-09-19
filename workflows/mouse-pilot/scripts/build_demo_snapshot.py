"""Create a bounded evidence snapshot; never changes scientific rankings."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'runs/focused-pilot-20260919'
OUT = ROOT / 'demos/chimera_snapshot.json'

def main():
    selected_path = ROOT / 'reports/focused_pilot_artifacts/selected_candidates.csv'
    ranking_path = RUN / 'selection/rna_ranking.json'
    ranking = {r['junction_id']: r for r in json.loads(ranking_path.read_text())}
    records = []
    for r in csv.DictReader(selected_path.open()):
        q = ranking[r['junction_id']]
        records.append(dict(id=r['junction_id'], name=f"{r['gene_name_5p']} → {r['gene_name_3p']}",
            parentA=r['gene_name_5p'], parentB=r['gene_name_3p'], classification='observed_pipeline',
            species='Mouse', sample='SRR28984805', assembly=q['reference_build'],
            reads=q['distinct_qualifying_reads'], replicates=q['biological_samples'],
            callers=', '.join(q['callers']), anchor=q['median_shorter_anchor_nt'],
            rank=q['display_rank'], proteinLength=len(r['sequence']), sequence=r['sequence'],
            sequenceSource=r['sequence_source'], proteinExistence=r['protein_existence'],
            sequenceHash=r['sequence_sha256'], readId=r['read_id'],
            chrA=q['chromosome_5p'], boundaryA=q['boundary_5p'], strandA=q['strand_5p'],
            chrB=q['chromosome_3p'], boundaryB=q['boundary_3p'], strandB=q['strand_3p'],
            rna='Supported in one sample', translation='Unknown', dna='Not assessed', hic='Not assessed',
            provenance='Frozen mouse-pilot selection; reference-assisted protein hypothesis. Not a K562 result.'))
    sources = [selected_path, ranking_path]
    provenance = [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]
    snapshot = dict(title='Chimeric RNA · evidence to experiment', surface='dashboard',
        status='mixed_observed_and_illustrative', buildStatus='creating', generatedAt=datetime.now(timezone.utc).isoformat(), filters=[], queries={
        'pilot': dict(rows=records, source=dict(label='Mouse pilot: frozen RNA selection and reference-assisted ORFs',
            files=provenance, caveats=['One biological sample and one caller. No evidence of protein expression or function.',
            'Selection is for structural exploration, not confirmation of translation. DNA, Hi-C and parent selectivity are unassessed.'],
            evidenceFlow=[dict(title='Reproduce snapshot',detail='Run python3 scripts/build_demo_snapshot.py. Join the frozen RNA ranking to selected_candidates.csv by exact junction_id. Preserve UNKNOWN values.')],
            metricDefinitions=[dict(label='Qualifying reads',definition='Distinct qualifying reads reported for the exact junction in the frozen ranking.'),dict(label='Protein length',definition='Amino-acid length of the reference-assisted sequence hypothesis; not evidence of protein production.') ])),
        'k562': dict(rows=[dict(id='k562-pending',name='K562 pilot', classification='not_executed',parentA='Parent A',parentB='Parent B',reads=None,replicates=None,proteinLength=None,rna='Not assessed',translation='Unknown',dna='Not assessed',hic='Not assessed',sequence=None,provenance='Proposed SG-NEx integration. No K562 candidates were executed or imported for this dashboard.')],
            source=dict(label='Proposed K562 pilot; no executed results',links=[dict(label='SG-NEx',url='https://github.com/GoekeLab/sg-nex-data')],caveats=['Missing data are not zero results.'])),
        'scenario': dict(rows=[dict(id='illustrative-a-b',name='Demo A → Demo B',parentA='Demo A',parentB='Demo B',classification='synthetic',sample='Illustrative K562-like scenario',assembly='Not assigned',reads=8,replicates=2,callers='Illustrative agreement',anchor=180,proteinLength=312,sequence=None,rna='Corroborated · illustrative',translation='Unverified',dna='No match · illustrative',hic='Context only · illustrative',provenance='Entirely fictional UI scenario. No real genes, supporting reads, molecular sequences or generated structures.')],
            source=dict(label='Synthetic demonstration scenario',caveats=['All values are fabricated for interface demonstration. They are not K562 findings.'],evidenceFlow=[dict(title='Demo construction',detail='Hand-authored fictional example for the requested dashboard demo. Excluded from all project rankings and benchmarks.')])),
        'designs': dict(rows=[dict(id='SIM-B01',modality='Junction binder',target='Illustrative favorable prediction',parentA='Illustrative low interaction',parentB='Illustrative low interaction',decision='Assay required',sequence=None,status='Synthetic display record'),dict(id='SIM-B02',modality='Junction binder',target='Illustrative favorable prediction',parentA='Illustrative cross-reactivity',parentB='Illustrative low interaction',decision='Reject in this scenario',sequence=None,status='Synthetic display record'),dict(id='SIM-B03',modality='Junction binder',target='Illustrative favorable prediction',parentA='Not assessed',parentB='Not assessed',decision='Hold: incomplete screens',sequence=None,status='Synthetic display record')],
            source=dict(label='Synthetic binder-result display records',caveats=['No binder generation, docking or binding assays were run. No sequences or structures are available. These records demonstrate pass, reject and missing-screen handling.'])),
        'methods': dict(rows=[dict(modality='RNA-directed reagent',requirement='Validated unique RNA junction; delivery and parental-transcript specificity',role='RNA perturbation or detection'),dict(modality='Junction binder',requirement='Resolved protein sequence, accessible junction epitope and target localization',role='Protein detection or binding hypothesis'),dict(modality='Small molecule',requirement='A defensible pocket, functional assay and matched parent comparisons',role='Pocket-directed exploration')],
            source=dict(label='Proposed decision framework; not experimental results',links=[dict(label='NVIDIA protein binder blueprint',url='https://build.nvidia.com/nvidia/protein-binder-design-for-drug-discovery')],caveats=['Modality choices are conditional research hypotheses. Predicted interactions do not establish affinity, specificity, delivery or therapeutic benefit.']))
    })
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(snapshot,indent=2)+'\n')
    print(f'{OUT}: {len(records)} source-backed mouse records; K562 unassessed; synthetic examples isolated')

if __name__ == '__main__': main()
