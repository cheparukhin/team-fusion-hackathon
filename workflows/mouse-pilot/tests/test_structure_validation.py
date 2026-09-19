"""Prediction acceptance rejects biologically wrong sequences and malformed confidence."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

gemmi=pytest.importorskip('gemmi',reason='Structure acceptance requires the structure extra')

spec=importlib.util.spec_from_file_location('prediction_worker',Path(__file__).resolve().parents[1]/'scripts/boltz_worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)


@pytest.fixture
def prediction(tmp_path):
    job={'job_id':'example','sequence':'MAG'}
    p=tmp_path/'boltz_results_example/predictions/example';p.mkdir(parents=True)
    structure=gemmi.Structure();model=gemmi.Model('1');chain=gemmi.Chain('A')
    for i,name in enumerate(['MET','ALA','GLY'],1):
        residue=gemmi.Residue();residue.name=name;residue.seqid=gemmi.SeqId(i,' ')
        atom=gemmi.Atom();atom.name='CA';atom.element=gemmi.Element('C');atom.pos=gemmi.Position(i*3.8,0,0)
        residue.add_atom(atom);chain.add_residue(residue)
    model.add_chain(chain);structure.add_model(model);structure.setup_entities()
    structure.make_mmcif_document().write_file(str(p/'example_model_0.cif'))
    np.savez(p/'plddt_example_model_0.npz',plddt=np.array([.2,.8,.9]))
    np.savez(p/'pae_example_model_0.npz',pae=np.ones((3,3)))
    (p/'confidence_example_model_0.json').write_text(json.dumps({'confidence_score':.8}))
    return job,tmp_path,p


def test_structure_sequence_is_checked_against_frozen_input(prediction):
    job,root,_=prediction
    assert worker.validate(job,root)['amino_acids']==3
    with pytest.raises(ValueError,match='sequence does not match'):
        worker.validate({**job,'sequence':'MAA'},root)


@pytest.mark.parametrize('bad',[[20,80,90],[.1,np.nan,.3],[.1,.2]])
def test_confidence_wrong_scale_nonfinite_or_length_rejected(prediction,bad):
    job,root,path=prediction
    np.savez(path/'plddt_example_model_0.npz',plddt=np.array(bad))
    with pytest.raises(ValueError,match='pLDDT'):
        worker.validate(job,root)


def test_negative_pae_rejected(prediction):
    job,root,path=prediction
    np.savez(path/'pae_example_model_0.npz',pae=-np.ones((3,3)))
    with pytest.raises(ValueError,match='aligned error'):
        worker.validate(job,root)


def test_local_acceptance_allows_roundoff_but_rejects_identity_or_confidence_change(prediction,monkeypatch):
    import copy
    scripts=Path(__file__).resolve().parents[1]/'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    spec=importlib.util.spec_from_file_location('accept_predictions',scripts/'accept_boltz_outputs.py')
    acceptance=importlib.util.module_from_spec(spec);spec.loader.exec_module(acceptance)
    job,root,_=prediction;local=worker.validate(job,root);remote=copy.deepcopy(local)
    remote['mean_plddt_0_to_100']+=1e-6
    acceptance.compare_validations(local,remote)
    remote['sequence_sha256']='different'
    with pytest.raises(ValueError,match='identity'):
        acceptance.compare_validations(local,remote)
    remote=copy.deepcopy(local);remote['mean_plddt_0_to_100']+=1
    with pytest.raises(ValueError,match='confidence'):
        acceptance.compare_validations(local,remote)
