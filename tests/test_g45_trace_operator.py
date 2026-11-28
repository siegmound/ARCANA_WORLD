"""Independent hanging-Q2 trace oracle: diagonal lumping must not pass."""
from pathlib import Path
import importlib.util
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
import pytest

p=Path(__file__).parents[1]/'experiments/r6_thermo_provider_pilot_v1/g45_distributed_cbf_v1/audit.py'
spec=importlib.util.spec_from_file_location('g45_audit',p);a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def test_signed_q2_constraint_requires_full_condensed_mass():
    H=np.vstack((np.eye(3),[3/8,3/4,-1/8]));weights=np.array([2.,3.,4.,5.]);r=np.array([7.,-3.,2.,4.])
    active,M,b=a.trace_operator(sparse.csr_matrix(H),weights,r)
    expected=sum(w*np.outer(row,row) for w,row in zip(weights,H))
    np.testing.assert_allclose(M.toarray(),expected,rtol=0,atol=0)
    x=spsolve(M,b);v=np.array([.3,-.7,.2])
    assert abs(np.dot(weights*(H@x),H@v)-np.dot(r,H@v))<1e-13
    wrong=b/M.diagonal()
    assert np.linalg.norm(M@wrong-b)/np.linalg.norm(b)>.01
    assert np.linalg.eigvalsh(expected).min()>0

def test_topology_reproduces_translation_and_position():
    H=sparse.csr_matrix(np.vstack((np.eye(3),[3/8,3/4,-1/8])))
    np.testing.assert_array_equal(H@np.ones(3),np.ones(4))
    np.testing.assert_array_equal(H@np.array([0.,.5,1.]),np.array([0.,.5,1.,.25]))

def test_empty_trace_is_rejected():
    with pytest.raises(a.Rejected,match='EMPTY_TRACE'):a.trace_operator(sparse.eye(3),np.zeros(3),np.ones(3))
