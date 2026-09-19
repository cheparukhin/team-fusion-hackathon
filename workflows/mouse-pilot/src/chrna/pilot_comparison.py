"""Post-freeze published comparisons, preserving each source's evidence grain."""
import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path


def load(path):return json.loads(path.read_text())


def compare(run,processed,output):
    freeze_path=run/'selection/freeze.json'
    freeze=load(freeze_path)
    if freeze['status']!='frozen':raise ValueError('Published comparison requires frozen RNA/selection')
    for name,digest in freeze['outputs'].items():
        if hashlib.sha256((freeze_path.parent/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Frozen artifact changed: '+name)
    ranking=load(run/'selection/rna_ranking.json')
    selection=load(run/'selection/selection.json')
    decisions=load(run/'selection/read_decisions.json')
    for key in ('reconstructions','hypotheses'):
        record=freeze['inputs'][key]
        if hashlib.sha256(Path(record['path']).read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Frozen ORF input changed: '+key)
    names={d['junction_id']:(d['gene_name_5p'],d['gene_name_3p']) for d in decisions}
    outcomes={}
    with (processed/'evaluation_outcomes.csv').open() as stream:
        for row_number,row in enumerate(csv.DictReader(stream),2):
            if row['nanostring_reported_support'] not in ('True','False'):
                raise ValueError('Unknown published support encoding')
            outcomes[row['pair_id']]={**row,'source_row':row_number}
    catalogue=defaultdict(list)
    with (processed/'catalogue_junctions.csv').open() as stream:
        for row_number,row in enumerate(csv.DictReader(stream),2):
            catalogue[row['Chimera_ID']].append({**row,'source_row':row_number})
    rows=[]
    for r in ranking:
        a,b=names[r['junction_id']];pair=a+':'+b
        outcome=outcomes.get(pair)
        published=catalogue.get(pair,[])
        numeric=[]
        for p in published:
            try:
                coordinates=(p['Chromosome_Gene_A'],p['Strand_Gene_A'],int(float(p['Breakpoint_Coordinate_Gene_A'])),
                             p['Chromosome_Gene_B'],p['Strand_Gene_B'],int(float(p['Breakpoint_Coordinate_Gene_B'])))
            except ValueError:
                continue
            if coordinates==(r['chromosome_5p'],r['strand_5p'],r['boundary_5p'],r['chromosome_3p'],r['strand_3p'],r['boundary_3p']):
                numeric.append(p['source_row'])
        rows.append({'junction_id':r['junction_id'],'ordered_pair':pair,'rna_rank':r['display_rank'],
            'rna_evidence_state':r['evidence_state'],
            'nanostring_pair_status':'reported_supported' if outcome and outcome['nanostring_reported_support']=='True' else 'UNKNOWN_not_reported_or_not_in_panel',
            'published_pair_outcome':outcome,'published_catalogue_pair_present':bool(published),
            'published_catalogue_coordinate_records':published,'numeric_coordinate_agreement_rows':numeric,
            'exact_published_junction_validation':'UNKNOWN_coordinate_convention_and_assay_grain_not_established',
            'sample_level_published_confirmation':'UNKNOWN','protein_existence_from_this_pilot':'UNKNOWN',
            'other_published_full_protein_sequence_comparison':'UNKNOWN_author_full_sequence_files_unavailable'})
    pair='Gsdmd:Tmem106a'
    flagship=[r for r in rows if r['ordered_pair']==pair]
    jids={r['junction_id'] for r in flagship}
    flagged=[d for d in decisions if d['junction_id'] in jids]
    reconstructed=[r for r in load(run/'orfs/reconstructions.json') if r['junction_id'] in jids]
    hypotheses=[h for h in load(run/'orfs/protein_hypotheses.json') if h['junction_id'] in jids]
    selected=[h for h in selection['selected'] if h['junction_id'] in jids]
    control=load(run/'published-control/provenance.json')
    raw_unresolved=load(run/'assessment/unresolved_longgf_proposals.json')
    trace={'ordered_pair':pair,'sample':'SRR28984805','biological_sample':'GSM8260877',
        'assessment_junctions':[r['junction_id'] for r in flagship],
        'read_decision_counts':dict(Counter(d['state'] for d in flagged)),
        'assessed_read_ids':sorted({d['read_id'] for d in flagged}),
        'unresolved_LongGF_source_proposals':[r for r in raw_unresolved if r['longgf_pair'] in (pair,'Tmem106a:Gsdmd')],
        'reconstructed_read_ids':sorted({r['read_id'] for r in reconstructed}),
        'protein_hypotheses':[{'protein_id':h['protein_id'],'read_id':h['read_id'],
             'sequence_resolved_under_assumptions':h['sequence_resolved_under_assumptions'],
             'matches_separate_reference_control':h['sequence_sha256']==control['protein_sha256']} for h in hypotheses],
        'selected_protein_ids':[h['protein_id'] for h in selected],
        'selection_decisions':[r for r in selection['decisions'] if r['junction_id'] in jids],
        'published_control_role':'Separate reference reconstruction of published architecture; never substituted for pilot recovery.',
        'rescue_alignment_or_outcome_based_ranking_used':False,
        'absence_interpretation':'No proposal or resolved sequence in this bounded pilot would remain UNKNOWN biological presence; this sample and proposal scope do not reproduce the full study.',
        'author_coordinate_comparison':'Unavailable: author prediction coordinates have not been retrieved.'}
    output.mkdir(parents=True,exist_ok=False)
    (output/'published_comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
    (output/'flagship_stage_trace.json').write_text(json.dumps(trace,indent=2)+'\n')
    receipt={'status':'compared_after_freeze','created_utc':datetime.now(timezone.utc).isoformat(),
             'freeze_sha256':hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
             'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                 (processed/'evaluation_outcomes.csv',processed/'catalogue_junctions.csv')},
             'junctions_compared':len(rows),
             'limitations':['Supplementary Table 7 confirms ordered gene pairs, not individual junctions or samples.',
                 'Table 3 aggregates reads across the study; its breakpoint coordinate convention is not established here.',
                 'Numeric coordinate agreement is reported without promoting it to exact experimental validation.',
                 'Published control protein is reference-reconstructed, not an author-provided full-sequence file.',
                 'No known biological true-negative labels exist in these inputs.']}
    (output/'comparison_provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,default=Path('runs/focused-pilot-20260919'))
    parser.add_argument('--processed',type=Path,default=Path('data/processed'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(compare(args.run,args.processed,args.output),indent=2))
