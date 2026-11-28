from pathlib import Path
import sys
import numpy as np
from scipy import sparse
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'experiments/r6_thermo_provider_pilot_v1/g45_distributed_cbf_v1'))
import rigid_motion as r

def test_combined_constant_cannot_hide_component_mixing():
    H=sparse.csr_matrix([[0.,1.],[1.,0.]])
    np.testing.assert_array_equal(H@np.ones(2),np.ones(2))
    with pytest.raises(r.audit.Rejected,match='COMPONENT_TRANSLATION'):r.translations(H,np.array([0,1]))

def test_signed_hanging_map_preserves_each_cartesian_translation():
    scalar=np.eye(4);scalar[3]=[3/8,3/4,-1/8,0]
    H=sparse.block_diag((scalar,scalar,scalar)).tocsr();errors=r.translations(H,np.repeat(np.arange(3),4))
    assert errors==[0.,0.,0.]
