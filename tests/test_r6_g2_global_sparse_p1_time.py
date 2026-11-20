"""Numerical engineered global-time kernel tests; no real Arcana T1."""
import math
import numpy as np
import pytest
from scipy import sparse

from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_time import (
    SparseP1Error, iterate_global,
)


def test_zero_tangent_returns_original_G1_target():
    l=sparse.csr_matrix((2,2),dtype=float)
    g=np.array([0.09,-0.03])
    out=iterate_global(l,g,1,100,checkpoints=(100,))
    assert np.allclose(out["snapshots"][100]["u"],100*g,rtol=0,atol=1e-12)
    assert np.allclose(out["snapshots"][100]["v"],g,rtol=0,atol=1e-12)
    assert out["maximum_relative_force_balance"]<1e-12
    assert out["maximum_relative_energy_identity"]<1e-12


def test_nonrigid_feedback_and_virtual_work_small_system():
    k=sparse.csr_matrix([[2.,-1.],[-1.,2.]])
    out=iterate_global(k,np.array([.1,-.05]),1,1000,checkpoints=(100,1000))
    assert np.linalg.norm(out["snapshots"][1000]["v"]-[.1,-.05])>1e-6
    assert out["maximum_relative_force_balance"]<1e-7
    assert out["maximum_relative_energy_identity"]<1e-7
    assert out["snapshots"][1000]["elastic_energy_normalized"]>=0


def test_restart500_plus500_bit_parity():
    k=sparse.csr_matrix([[1.,-.5],[-.5,1.]])
    g=np.array([.10,-.03])
    all_steps=iterate_global(k,g,1,1000,checkpoints=(500,1000))
    resumed=iterate_global(k,g,1,500,initial=all_steps["snapshots"][500],
                           start_year=500,checkpoints=(1000,))
    assert np.max(np.abs(
        all_steps["state"]["u"]-resumed["state"]["u"]))<1e-12
    assert np.max(np.abs(
        all_steps["state"]["v"]-resumed["state"]["v"]))<1e-12


def test_analytic_scalar_euler_order_at_subyear_steps():
    k=sparse.diags([.2,2.],format="csr")
    g=np.array([.1,.05])
    exact=g*200/np.array([.2,2.])*(
        1-np.exp(-np.array([.2,2.])*100/(200*(1+np.array([.2,2.])))))
    e=[]
    for dt in (1.,.5,.25):
        out=iterate_global(k,g,dt,int(round(100/dt)),checkpoints=(100,))
        e.append(np.linalg.norm(out["snapshots"][100]["u"]-exact))
    assert e[0]>e[1]>e[2]
    assert .85<math.log(e[0]/e[1],2)<1.15
    assert .85<math.log(e[1]/e[2],2)<1.15


def test_rigid_plate_null_field_passes_unchanged():
    k=sparse.csr_matrix([[1.,-1.],[-1.,1.]])
    g=np.array([.08,.08])
    out=iterate_global(k,g,5,20,checkpoints=(100,))
    assert np.max(np.abs(out["state"]["u"]-100*g))<1e-10
    assert out["maximum_relative_force_balance"]<1e-10


def test_bad_negative_step_rejected():
    k=sparse.eye(2,format="csr")
    with pytest.raises(SparseP1Error,match="INVALID_INPUT"):
        iterate_global(k,[.1,.1],-1,100)


def test_nans_are_rejected():
    k=sparse.eye(2,format="csr")
    with pytest.raises(SparseP1Error,match="INVALID_INPUT"):
        iterate_global(k,[float("nan"),.1],1,10)


def test_invalid_restart_state_rejected():
    k=sparse.eye(2,format="csr")
    with pytest.raises(SparseP1Error,match="RESTART_INVALID"):
        iterate_global(k,[.1,.2],1,5,
                       initial={"u":[float("inf"),0.],"v":[0,0]})


def test_implicit_solver_residual_not_confused_with_physical_force():
    k=sparse.diags([1.,3.],format="csr")
    out=iterate_global(k,[0.3,0.4],1,100,checkpoints=(100,))
    assert out["linear_steps"]==100
    assert out["matrix_nnz"]==2
    assert out["maximum_cg_iterations_per_step"]>=0
    assert out["maximum_relative_force_balance"]<2e-7
