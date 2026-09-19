import csv
import hashlib
import json

import pytest

from chrna.pilot_comparison import compare


def test_published_nonreporting_and_numeric_coordinates_do_not_create_truth_labels(tmp_path):
    run=tmp_path/'run';processed=tmp_path/'processed';processed.mkdir()
    for name in ('selection','assessment','orfs','published-control'):(run/name).mkdir(parents=True)
    def write(name,record):
        path=run/name;path.write_text(json.dumps(record));return path
    ranking=[dict(junction_id='j1',display_rank=1,evidence_state='supported_two_gene_junction',
        chromosome_5p='chr1',strand_5p='+',boundary_5p=100,chromosome_3p='chr2',strand_3p='+',boundary_3p=200)]
    write('selection/rna_ranking.json',ranking)
    write('selection/read_decisions.json',[dict(junction_id='j1',gene_name_5p='A',gene_name_3p='B')])
    write('selection/selection.json',{'selected':[],'decisions':[]})
    recon=write('orfs/reconstructions.json',[]);hyp=write('orfs/protein_hypotheses.json',[])
    write('assessment/unresolved_longgf_proposals.json',[])
    write('published-control/provenance.json',{'protein_sha256':'control'})
    outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (run/'selection').iterdir()}
    write('selection/freeze.json',{'status':'frozen','outputs':outputs,
        'inputs':{k:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in [('reconstructions',recon),('hypotheses',hyp)]}})
    (processed/'evaluation_outcomes.csv').write_text('pair_id,nanostring_reported_support\nA:B,False\n')
    columns=['Chimera_ID','Chromosome_Gene_A','Strand_Gene_A','Breakpoint_Coordinate_Gene_A','Chromosome_Gene_B','Strand_Gene_B','Breakpoint_Coordinate_Gene_B']
    with (processed/'catalogue_junctions.csv').open('w') as stream:
        writer=csv.writer(stream);writer.writerow(columns);writer.writerow(['A:B','chr1','+',100,'chr2','+',200])
    compare(run,processed,tmp_path/'comparison')
    row=json.loads((tmp_path/'comparison/published_comparison.json').read_text())[0]
    assert row['nanostring_pair_status'].startswith('UNKNOWN')
    assert row['numeric_coordinate_agreement_rows']==[2]
    assert row['exact_published_junction_validation'].startswith('UNKNOWN')
    assert row['sample_level_published_confirmation']=='UNKNOWN'


def test_comparison_fails_before_reading_outcomes_without_freeze(tmp_path):
    (tmp_path/'selection').mkdir()
    (tmp_path/'selection/freeze.json').write_text('{"status":"preview_not_frozen"}')
    with pytest.raises(ValueError,match='requires frozen'):
        compare(tmp_path,tmp_path/'missing_outcomes',tmp_path/'comparison')
