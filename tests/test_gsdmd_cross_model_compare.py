import csv, importlib.util
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('gsdmd_compare',ROOT/'scripts/structure_campaign/gsdmd_cross_model_compare.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_rmsd_removes_rigid_motion_but_not_mirror_geometry():
    a=np.array([[0.,0,0],[1,0,0],[0,2,0],[0,0,3]])
    q=np.array([[0,-1,0],[1,0,0],[0,0,1]])
    assert m.fitted_rmsd(a,a@q+5)<1e-12
    assert m.fitted_rmsd(a,a*np.array([-1,1,1]))>.1

def test_confidence_requires_explicit_units_and_ordered_identity(tmp_path):
    p=tmp_path/'confidence.tsv'
    p.write_text('residue\taa\tplddt\n1\tM\t60\n2\tA\t80\n')
    with pytest.raises(ValueError,match='scale'):m.confidence_identity(p,{},'MA')
    with pytest.raises(ValueError,match='identity'):m.confidence_identity(p,{'confidence_scale':'0-100'},'AM')
    assert m.confidence_identity(p,{'confidence_scale':'0-100'},'MA').tolist()==[60,80]
    p.write_text('residue\taa\tplddt\n1\tM\tnan\n2\tA\t80\n')
    with pytest.raises(ValueError,match='invalid_confidence'):m.confidence_identity(p,{'confidence_scale':'0-100'},'MA')

def test_coordinate_identity_rejects_actual_model_residue_substitution(tmp_path):
    import json
    gemmi = pytest.importorskip("gemmi", reason="Optional saved-model validation dependency")
    baseline = ROOT / "results/structure_campaign/cross_model_gsdmd/baseline_models.json"
    if not baseline.is_file():
        pytest.skip("Restore the controller evidence assets to validate saved coordinates")
    record=json.loads((ROOT/'results/structure_campaign/cross_model_gsdmd/baseline_models.json').read_text())['models'][0]
    with (ROOT/'results/structure_campaign/cohort/peptides.tsv').open()as f:
        sequence=next(r['sequence']for r in csv.DictReader(f,delimiter='\t')if r['sequence_sha256']==m.EXPECTED)
    src=ROOT/record['model_path']
    if not src.is_file():
        pytest.skip('Restore the controller evidence assets to validate saved coordinates')
    ca,_=m.coordinate_identity(src,sequence);assert ca.shape==(118,3)
    structure=gemmi.read_structure(str(src));structure[0][0][0].name='ALA';p=tmp_path/'changed.cif';structure.make_mmcif_document().write_file(str(p))
    with pytest.raises(ValueError,match='sequence'):m.coordinate_identity(p,sequence)
