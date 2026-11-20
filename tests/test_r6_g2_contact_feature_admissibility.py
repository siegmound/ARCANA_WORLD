"""ARCANA R6 source-free source-edge witness admissibility tests.

Synthetic geometry only. No manufactured evidence becomes natural rock physics.
"""
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error
from experiments.plate58_deforming_explore_v1.g2_contact_feature_admissibility import (
    classify_edge_pair,verify_engineering_witness,
)


def skew(gap=1.):
    a=np.array([0.,0.,0.]);b=np.array([2.,0.,0.])
    c=np.array([0.,gap,-.05]);d=np.array([2.,gap,.05])
    return np.array([a,b,c,d]),np.array([0.,1.,0.])


@pytest.mark.parametrize("gap,expected",[(1.,1.),(-1.,-1.),(0.,0.)])
def test_opening_closing_grazing_interior_skew_gap(gap,expected):
    x,ref=skew(gap)
    r=classify_edge_pair(*x,ref)
    assert r["classification"]=="ENGINEERING_EDGE_EDGE_INTERIOR"
    assert r["engineered_edge_gap_eligible"] is True
    assert r["physical_surface_contact_qualified"] is False
    assert r["signed_gap_m"]==pytest.approx(expected,abs=1e-12)
    assert r["s"]==pytest.approx(.5,abs=1e-12)
    assert r["t"]==pytest.approx(.5,abs=1e-12)


def test_exact_parallel_abstains():
    r=classify_edge_pair([0,0,0],[2,0,0],[0,1,0],[2,1,0],[0,1,0])
    assert r["classification"]=="AMBIGUOUS"
    assert r["reason"]=="PARALLEL_OR_NEAR_PARALLEL_NONUNIQUE_WITNESS"
    assert r["signed_gap_m"] is None


def test_source_like_near_parallel_abstains():
    a=np.array([0.,0.,0.]);b=np.array([100000.,0.,0.])
    c=np.array([0.,1.,0.]);d=c+np.array([100000.,.25,0.])
    r=classify_edge_pair(a,b,c,d,[0,1,0])
    assert r["classification"]=="AMBIGUOUS"
    assert r["signed_gap_m"] is None
    assert r["parallel_ratio"]<1e-8


def test_source_t0_coincident_edges_abstain():
    r=classify_edge_pair([0,0,0],[2,0,0],[0,0,0],[2,0,0],[0,1,0])
    assert r["classification"]=="AMBIGUOUS"
    assert r["physical_surface_contact_qualified"] is False


def test_endpoint_and_feature_switch_abstains():
    r=classify_edge_pair([0,0,0],[1,0,0],[3,1,-1],[3,1,1],[0,1,0])
    assert r["classification"]=="AMBIGUOUS"
    assert r["reason"]=="BOUNDARY_ENDPOINT_OR_FEATURE_SWITCH"


def test_bad_orientation_abstains():
    x,_=skew()
    r=classify_edge_pair(*x,[0,0,1])
    assert r["classification"]=="AMBIGUOUS"
    assert r["reason"]=="UNSUPPORTED_SOURCE_NORMAL_ORIENTATION"


def test_same_gap_consistent_jacobian_force_torque_work_and_so3():
    x,ref=skew()
    r=verify_engineering_witness(x,ref,step=1e-4)
    assert r["max_absolute_jacobian_fd_error"]<3e-4
    assert r["normalized_net_force"]<1e-8
    assert r["normalized_net_torque"]<1e-6
    assert r["normalized_virtual_work_error"]<3e-4
    assert r["SO3_signed_gap_error_m"]<1e-7
    assert r["physical_force_proved"] is False


@pytest.mark.parametrize("angle",[.3,1.3,2.1])
def test_finite_so3_signed_gap_and_gradient_objective(angle):
    x,ref=skew(2.)
    Q=Rotation.from_rotvec(angle*np.array([.25,-.8,.45])).as_matrix()
    p=classify_edge_pair(*x,ref)
    q=classify_edge_pair(*(x@Q.T),Q@ref)
    assert q["classification"]=="ENGINEERING_EDGE_EDGE_INTERIOR"
    assert abs(p["signed_gap_m"]-q["signed_gap_m"])<1e-8
    assert np.allclose(np.asarray(p["gradient"])@Q.T,q["gradient"],atol=1e-8)


def test_degenerate_segment_fails_closed():
    with pytest.raises(SparseP1Error,match="FEATURE_DEGENERATE_SOURCE_EDGE"):
        classify_edge_pair([0,0,0],[0,0,0],[0,1,0],[1,1,0],[0,1,0])


def test_ambiguous_cannot_enter_virtual_work_solver():
    with pytest.raises(SparseP1Error,match="FEATURE_INELIGIBLE_FOR_JACOBIAN"):
        verify_engineering_witness(
            np.array([[0,0,0],[2,0,0],[0,1,0],[2,1,0]]),
            [0,1,0])


def test_reverse_witness_normal_requires_explicit_reference():
    x,ref=skew(1.)
    a=classify_edge_pair(*x,ref)
    b=classify_edge_pair(*x,-ref)
    assert a["signed_gap_m"]==pytest.approx(-b["signed_gap_m"],abs=1e-12)
    assert a["physical_surface_contact_qualified"] is False
    assert b["physical_surface_contact_qualified"] is False
