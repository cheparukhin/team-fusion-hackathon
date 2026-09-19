import hashlib
import json

import pytest

from chrna.fold_inputs import prepare


def fixture(tmp_path, status='frozen'):
    selection = tmp_path/'selection';selection.mkdir()
    control = tmp_path/'published-control';control.mkdir()
    sequence = 'M'+'A'*39
    digest = hashlib.sha256(sequence.encode()).hexdigest()
    content = json.dumps({'selected':[{'sequence':sequence,'junction_id':'junction_A_B',
        'selection_order':1,'gene_name_5p':'A','gene_name_3p':'B'}]})
    (selection/'selection.json').write_text(content)
    (selection/'freeze.json').write_text(json.dumps({'status':status,
        'outputs':{'selection.json':hashlib.sha256(content.encode()).hexdigest()}}))
    (control/'provenance.json').write_text(json.dumps({'protein_sha256':digest,
        'status':'reference_reconstruction_matching_published_constraints'}))
    (control/'published_architecture_control.fasta').write_text('>control\n'+sequence+'\n')
    return tmp_path


def test_identical_recovered_and_control_sequence_reuse_prediction_keep_roles(tmp_path):
    run=fixture(tmp_path)
    prepare(run,tmp_path/'inputs')
    manifest=json.loads((tmp_path/'inputs/manifest.json').read_text())
    assert len(manifest['jobs'])==1
    assert {r['role'] for r in manifest['jobs'][0]['roles']}=={
        'pilot_recovered_reference_assisted','published_architecture_reference_control'}
    assert manifest['settings']['diffusion_samples']==1


def test_preview_or_tampered_freeze_cannot_enter_folding(tmp_path):
    run=fixture(tmp_path,status='preview_not_frozen')
    with pytest.raises(ValueError,match='frozen selection'):
        prepare(run,tmp_path/'inputs')
    path=tmp_path/'selection/freeze.json'
    record=json.loads(path.read_text());record['status']='frozen';path.write_text(json.dumps(record))
    (tmp_path/'selection/selection.json').write_text('{"selected":[]}')
    with pytest.raises(ValueError,match='artifact changed'):
        prepare(run,tmp_path/'inputs')
