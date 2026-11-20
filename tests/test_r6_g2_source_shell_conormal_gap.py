"""Source-free manufactured shell-side matched-boundary gap diagnostics only."""
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error
from experiments.plate58_deforming_explore_v1.g2_source_shell_conormal_gap import (
    into_face_conormal,matched_shell_gap,source_shell_consistency,
    check_SO3,edge_indices,from_six_vertices,
)


def faces(yq=0.,yp=0.):
    r=6_371_000.
    p=np.array([[0.,yp,r],[2000.,yp,r],[1000.,1000.+yp,r]])
    q=np.array([[2000.,yq,r],[0.,yq,r],[1000.,-1000.+yq,r]])
    ep=p[[0,1]];eq=q[[1,0]]
    return p,q,ep,eq


@pytest.mark.parametrize("shift,expected",[
    (0.,0.),(-10.,10.),(10.,-10.)
])
def test_matched_original_edge_opening_and_closing(shift,expected):
    p,q,ep,eq=faces(yq=shift)
    row=matched_shell_gap(p,q,ep,eq)
    assert row["classification"]=="ENGINEERING_ONLY_MATCHED_SHELL_EDGE_GAP"
    assert row["signed_shell_midpoint_gap_m"]==pytest.approx(expected,abs=1e-10)
    assert row["signed_solid_nonpenetration_m"] is None
    assert row["physical_contact_authorized"] is False
    assert row["inward_conormal_alignment"]==pytest.approx(-1.)


def test_source_inward_conormals_opposite_and_rigid_rotating():
    p,q,ep,eq=faces()
    mp=into_face_conormal(p,ep)
    mq=into_face_conormal(q,eq)
    assert np.allclose(mp,-mq,atol=1e-12)
    assert mp[1]==pytest.approx(1.)
    assert mq[1]==pytest.approx(-1.)


@pytest.mark.parametrize("angle",[.2,.8,2.2])
def test_finite_SO3_rigid_objectivity_of_shell_opening(angle):
    p,q,ep,eq=faces(yq=-10.)
    x=matched_shell_gap(p,q,ep,eq)
    Q=Rotation.from_rotvec(angle*np.array([.4,-.7,.2])).as_matrix()
    y=matched_shell_gap(p@Q.T,q@Q.T,ep@Q.T,eq@Q.T)
    assert y["classification"]==x["classification"]
    assert abs(x["signed_shell_midpoint_gap_m"]-
               y["signed_shell_midpoint_gap_m"])<1e-7
    assert np.allclose(
        Q@np.array(x["shell_opening_normal_cartesian"]),
        y["shell_opening_normal_cartesian"],atol=1e-9)


def test_builtin_so3_audit():
    p,q,ep,eq=faces(yq=-12.)
    m=matched_shell_gap(p,q,ep,eq)
    audit=check_SO3(p,q,ep,eq,m)
    assert audit["signed_gap_error_m"]<1e-7


def test_reject_facet_same_side_of_boundary():
    p,q,ep,eq=faces()
    q[2]=np.array([1000.,1000.,6_371_000.])
    result=matched_shell_gap(p,q,ep,eq)
    assert result["classification"]=="NOT_QUALIFIED"
    assert result["reason"]=="SOURCE_PLATE_FACE_SIDEDNESS_NOT_OPPOSING"
    assert result["signed_shell_midpoint_gap_m"] is None


def test_consistent_six_vertex_fd_gradient_and_virtual_work():
    p,q,ep,eq=faces(yq=-15.)
    result=source_shell_consistency(
        np.stack([p,q]),((0,1),(1,0)),step=.5)
    assert result["max_FD_refinement_error"]<3e-4
    assert result["normalized_force_translation_residual"]<3e-5
    assert result["normalized_virtual_work_error"]<3e-4
    assert result["physical_force_calibrated"] is False


def test_reversing_edge_direction_does_not_change_midpoint_gap():
    p,q,ep,eq=faces(yq=-20.)
    x=matched_shell_gap(p,q,ep,eq)
    y=matched_shell_gap(p,q,ep[::-1],eq[::-1])
    assert x["signed_shell_midpoint_gap_m"]==pytest.approx(
        y["signed_shell_midpoint_gap_m"],abs=1e-12)


def test_ineligible_source_cannot_enter_gradient_audit():
    p,q,ep,eq=faces()
    q[2]=np.array([1000.,1000.,6_371_000.])
    with pytest.raises(SparseP1Error,match="SHELL_AUDIT_WITNESS_INELIGIBLE"):
        source_shell_consistency(
            np.stack([p,q]),((0,1),(1,0)))


def test_source_face_edge_ids_are_matched_by_parent_ids():
    assert edge_indices([1,2,3],[2,1])==[1,0]
    assert edge_indices([2,1,4],[2,1])==[0,1]


def test_from_six_vertices_reuses_same_gap_definition():
    p,q,ep,eq=faces(yq=-5.)
    direct=matched_shell_gap(p,q,ep,eq)
    from6=from_six_vertices(np.stack((p,q)),((0,1),(1,0)))
    assert from6["signed_shell_midpoint_gap_m"]==pytest.approx(
        direct["signed_shell_midpoint_gap_m"],abs=1e-12)
