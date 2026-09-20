import importlib.util
from pathlib import Path
import numpy as np
import pytest
spec=importlib.util.spec_from_file_location('robustness',Path(__file__).parents[1]/'scripts/structure_campaign/analyze_model_robustness.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_seed_alignment_removes_rigid_motion_not_deformation():
 a=np.array([[0,0,0],[1,0,0],[0,2,0],[0,0,3]],dtype=float)
 r=np.array([[0,-1,0],[1,0,0],[0,0,1]])
 assert m.fitted_rmsd(a,a@r+5)<1e-10
 b=a.copy();b[0,0]=.5
 assert m.fitted_rmsd(a,b)>.05
 with pytest.raises(ValueError):m.fitted_rmsd(a[:2],b[:2])
