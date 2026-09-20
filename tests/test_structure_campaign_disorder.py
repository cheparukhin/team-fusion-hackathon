import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('disorder',Path(__file__).parents[1]/'scripts/structure_campaign/analyze_disorder.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_residue_threshold_distinct_from_protein_majority():
    result=m.summarize_scores([0.5,0.9,0.1,0.2])
    assert result['f_idr']==0.5
    assert result['longest_idr']==2
    assert not result['predominantly_disordered']

def test_missing_and_empty_regions_not_ordered_zero():
    assert m.region_summary([.2,.8],None,None) is None
    assert m.region_summary([.2,.8],1,1) is None
    assert m.region_summary([.2,.8],1,2)['f_idr']==1
    with pytest.raises(ValueError):m.region_summary([.2,.8],0,3)

def test_invalid_predictions_fail_closed():
    for values in [[],[float('nan')],[-.1],[1.1]]:
        with pytest.raises(ValueError):m.summarize_scores(values)

def test_fasta_duplicate_and_stop_rejected(tmp_path):
    p=tmp_path/'x.fa';p.write_text('>x\nMAA\n>x\nMAA\n')
    with pytest.raises(ValueError):m.read_fasta(p)
    p.write_text('>x\nMAA*\n')
    with pytest.raises(ValueError):m.read_fasta(p)
