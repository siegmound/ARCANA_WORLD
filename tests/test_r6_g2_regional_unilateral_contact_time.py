"""Manufactured normal-contact KKT and time-stepping checks (not real faults)."""
import numpy as np
import pytest
from scipy import sparse

from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error
from experiments.plate58_deforming_explore_v1.g2_regional_unilateral_contact_time import (
    normal_constraint_matrix,prepare_qp,frictionless_normal_qp,integrate,
)


def simple():
    J=sparse.csr_matrix([[-1.,1.]])
    K=sparse.eye(2,format="csr",dtype=float)
    return K,J


def test_qp_enforces_exact_closing_constraint():
    A=sparse.eye(2,format="csr")
    _,J=simple()
    response=frictionless_normal_qp(A,[.08,-.08],J,[0.])
    v=response["velocity"]
    assert (J@v)[0]>=-1e-12
    assert response["lambda"][0]>0
    assert abs(response["lambda"][0]*(J@v)[0])<1e-12
    assert response["force_relative_residual"]<1e-12
    # Contact pair is exactly action/reaction in source EN frame.
    force=J.T@response["lambda"]
    assert abs(float(np.sum(force)))<1e-12


def test_opening_contact_has_zero_reaction():
    _,J=simple()
    response=frictionless_normal_qp(sparse.eye(2),[-.08,.08],J,[0.])
    assert response["lambda"][0]==pytest.approx(0.,abs=1e-12)
    assert (J@response["velocity"])[0]>0


def test_gap_positive_allows_later_closing_motion():
    _,J=simple()
    response=frictionless_normal_qp(
        sparse.eye(2),[.08,-.08],J,[-.5])
    assert response["lambda"][0]==pytest.approx(0.,abs=1e-12)
    assert (J@response["velocity"])[0]<0


def test_twin_links_shared_junction_bounded_dual():
    # Two contact normals in a synthetic three-owner junction.
    J=sparse.csr_matrix([[-1,1,0],[0,-1,1]],dtype=float)
    result=frictionless_normal_qp(
        sparse.eye(3),[.3,.0,-.2],J,[0,0])
    assert np.min(J@result["velocity"])>=-1e-11
    assert np.min(result["lambda"])>=-1e-11
    assert result["max_scaled_complementarity"]<1e-11


def test_rank_deficient_contact_rejected_instead_of_forcing():
    J=sparse.csr_matrix([[-1,1],[-1,1]],dtype=float)
    with pytest.raises(SparseP1Error,match="REDUNDANT_OR_DEPENDENT"):
        prepare_qp(sparse.eye(2),J)


def test_real_source_pair_node_constraint_sign():
    links=[{"plate_pair":(5,8),"parent_node_id":34587,
            "normal_EN":np.array([1.,0.])}]
    index={(5,34587):0,(8,34587):1}
    J=normal_constraint_matrix(links,index,4)
    assert np.allclose(J.toarray(),[[-1,0,1,0]])


def test_dynamic_zero_initial_gap_never_negative():
    K,J=simple()
    out=integrate(K,J,[.05,-.05],1,100,checkpoints=(100,))
    assert out["min_gap_over_run"]>=-1e-10
    assert out["snapshots"][100]["minimum_gap"]>=-1e-10
    assert out["snapshots"][100]["active_count"]==1
    assert out["max_scaled_complementarity"]<1e-9


def test_dynamic_opening_keeps_zero_reactions():
    K,J=simple()
    out=integrate(K,J,[-.05,.05],1,100,checkpoints=(100,))
    assert out["snapshots"][100]["minimum_gap"]>0
    assert out["snapshots"][100]["active_count"]==0
    assert out["max_reaction"]==pytest.approx(0,abs=1e-12)


def test_dynamic_restart_500_plus_500_same_displacement():
    K=sparse.csr_matrix([[2.,-.2],[-.2,1.]])
    J=sparse.csr_matrix([[-1.,1.]])
    long=integrate(K,J,[.05,-.05],1,1000,checkpoints=(500,1000))
    state=long["snapshots"][500]
    replay=integrate(K,J,[.05,-.05],1,500,
         initial={"displacement":state["displacement"],"gap":state["gap"]},
         start_year=500,checkpoints=(1000,))
    assert np.max(np.abs(replay["state"]["displacement"]-
                         long["state"]["displacement"]))<1e-9
    assert np.min(replay["state"]["gap"])>=-1e-8


def test_source_contact_no_fake_gap_from_zero_drive():
    K,J=simple()
    out=integrate(K,J,[0.,0.],10,10,checkpoints=(100,))
    assert np.max(np.abs(out["state"]["displacement"]))==0
    assert np.max(np.abs(out["state"]["gap"]))==0


def test_invalid_restart_fails_closed():
    K,J=simple()
    with pytest.raises(SparseP1Error,match="RESTART_INVALID"):
        integrate(K,J,[0.1,-.1],1,10,initial={
            "displacement":[0.,float("nan")],"gap":[0.]})


def test_invalid_normal_index_fails_closed():
    links=[{"plate_pair":(5,8),"parent_node_id":3,
            "normal_EN":np.array([1.,0.])}]
    with pytest.raises((KeyError,SparseP1Error)):
        normal_constraint_matrix(links,{(5,3):0},4)
