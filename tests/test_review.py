"""Review tools must preserve absent evidence, exact parent order and stale-input detection."""
import copy
import json
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/review'))
from evidence import compare_probe_junctions, rematch_parabricks, record, sha
from verify import validate_decision, verify_run


def data(root, second=200):
    p=root/'demo';p.mkdir(exist_ok=True)
    j=dict(assembly='GRCm39',chrom1='chr1',strand1='+',chrom2='chr2',strand2='-',breakpoint1='100',breakpoint2=str(second),read_ids='read-a')
    c=dict(pair_id='A:B',junctions=[j],probe_junctions=[dict(j,probe_id='A:B',breakpoint2='210')])
    d={'candidates':[c],'nvidia_pilot':{'status':'unavailable'}}
    (p/'data.json').write_text(json.dumps(d))
    return d


def test_offsets_keep_parent_orientation_and_unavailable(tmp_path):
    d=data(tmp_path)
    result,_=compare_probe_junctions(tmp_path,'A:B')
    assert result['comparisons'][0]['closest_max_offset_nt']==10
    d['candidates'][0]['junctions'][0]['strand2']='+'
    (tmp_path/'demo/data.json').write_text(json.dumps(d))
    result,_=compare_probe_junctions(tmp_path,'A:B')
    assert result['comparisons'][0]['closest_max_offset_nt'] is None
    assert rematch_parabricks(tmp_path,'A:B')[0]['support'] is None
    with pytest.raises(ValueError,match='exact ordered pair'):
        compare_probe_junctions(tmp_path,'B:A')


def test_gpu_file_integrity_is_not_assumed(tmp_path):
    d=data(tmp_path);rel='results/compute/pilot_2m/output/Chimeric.out.junction'
    p=tmp_path/rel;p.parent.mkdir(parents=True);p.write_text('changed')
    d['nvidia_pilot']={'status':'completed','artifact_sha256':{rel:'wrong'}}
    (tmp_path/'demo/data.json').write_text(json.dumps(d))
    with pytest.raises(ValueError,match='integrity mismatch'):
        rematch_parabricks(tmp_path,'A:B')


def test_record_preserves_case_and_freeze(tmp_path):
    data(tmp_path);run=tmp_path/'run'
    record(tmp_path,run,'A:B','compare_probe_junctions','check')
    with pytest.raises(ValueError,match='one ordered pair'):
        record(tmp_path,run,'B:A','compare_probe_junctions','check')
    (run/'decision.json').write_text('{}')
    with pytest.raises(ValueError,match='already frozen'):
        record(tmp_path,run,'A:B','compare_probe_junctions','check')


def test_decision_rejects_wrong_pair_and_unknown_evidence():
    run=ROOT/'results/review/psap-lgals3'
    decision=json.loads((run/'decision.json').read_text())
    steps=[json.loads(p.read_text()) for p in sorted(run.glob('step-*.json'))]
    assert validate_decision(decision,steps)
    wrong=copy.deepcopy(decision);wrong['pair_id']='B:A'
    with pytest.raises(ValueError,match='pair mismatch'):validate_decision(wrong,steps)
    wrong=copy.deepcopy(decision);wrong['claims'][0]['evidence'][0]['step']=8
    with pytest.raises(ValueError,match='Unknown evidence'):validate_decision(wrong,steps)
    wrong=copy.deepcopy(decision);wrong['human_review']['status']='approved'
    with pytest.raises(ValueError,match='fabricate'):validate_decision(wrong,steps)


def test_frozen_real_review_recomputes():
    for path in (ROOT/'results/review').glob('*/decision.json'):
        assert verify_run(ROOT,path.parent)['status']=='passed'
