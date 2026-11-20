"""Synthetic tests for original source-owned open triangle patch inventory.

No natural plate rheology, no closed volume, no physical contact solver.
"""
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import (
    SparseP1Error,
)
from experiments.plate58_deforming_explore_v1.g2_source_owned_face_topology import (
    source_face_incidence,triangle_patch_metrics,
    objective_triangle_patch_check,source_surface_patch_inventory,
)


def sample():
    radius=6_371_000.
    p=np.array([[0.,0.,radius],[2000.,0.,radius],[1000.,1000.,radius]])
    q=np.array([[2000.,0.,radius],[0.,0.,radius],[1000.,-1000.,radius]])
    edge_p=p[[0,1]]
    edge_q=q[[1,0]]
    return p,q,edge_p,edge_q


def source_rows():
    return [{
        "source_boundary_id":"R6BND-T0-SYNTHETIC-1-2",
        "source_edge_node_ids":[1,2],
        "plate_pair":[5,8],
    }]


def test_source_two_faces_correct_owner():
    rows=source_face_incidence(
        [(1,2,3),(2,1,4)],[5,8],source_rows())
    assert len(rows)==1
    assert rows[0]["plate_p_original_triangle_node_ids"]==[1,2,3]
    assert rows[0]["plate_q_original_triangle_node_ids"]==[2,1,4]


def test_source_owner_mismatch_fails_closed():
    with pytest.raises(SparseP1Error,match="SURFACE_SOURCE_FACE_OWNER_MISMATCH"):
        source_face_incidence(
            [(1,2,3),(2,1,4)],[5,5],source_rows())


def test_missing_other_side_source_face_fails_closed():
    with pytest.raises(SparseP1Error,match="SURFACE_SOURCE_FACE_OWNER_MISMATCH"):
        source_face_incidence(
            [(1,2,3)],[5],source_rows())


def test_source_boundary_duplicate_fails_closed():
    with pytest.raises(SparseP1Error,match="SURFACE_SOURCE_ID_DUPLICATE_OR_INVALID"):
        source_face_incidence(
            [(1,2,3),(2,1,4)],[5,8],source_rows()*2)


def test_synthetic_open_facets_are_two_topological_sides():
    p,q,ep,eq=sample()
    r=triangle_patch_metrics(p,q,ep,eq)
    assert r["facet_p_area_m2"]==pytest.approx(1_000_000.)
    assert r["facet_q_area_m2"]==pytest.approx(1.)
    assert r["facet_p_radially_outward_by_source_winding"] is True
    assert r["facet_q_radially_outward_by_source_winding"] is True
    assert r["raw_source_facet_normal_alignment"]==pytest.approx(1.)
    assert r["inward_face_conormal_alignment"]==pytest.approx(-1.)
    assert r["nearest_boundary_edge_unsigned_distance_m"]==pytest.approx(0.)
    assert r["qualified_signed_rock_contact_gap_m"] is None
    assert not r["source_owned_closed_solid_volume_proven"]


def test_reversing_facet_winding_is_measured_not_silently_fixed():
    p,q,ep,eq=sample()
    q=q[[1,0,2]]
    r=triangle_patch_metrics(p,q,ep,eq)
    assert r["facet_q_radially_outward_by_source_winding"] is False
    assert r["raw_source_facet_normal_alignment"]==pytest.approx(-1.)
    assert r["inward_face_conormal_alignment"]==pytest.approx(-1.)


@pytest.mark.parametrize("angle",[.05,.7,1.6])
def test_finite_SO3_preserves_open_patch_topology_diagnostics(angle):
    p,q,ep,eq=sample()
    Q=Rotation.from_rotvec(angle*np.array([.4,-.7,.2])).as_matrix()
    original=triangle_patch_metrics(p,q,ep,eq)
    rotated=triangle_patch_metrics(p@Q.T,q@Q.T,ep@Q.T,eq@Q.T)
    assert abs(original["inward_face_conormal_alignment"]-
               rotated["inward_face_conormal_alignment"])<1e-9
    assert abs(original["nearest_boundary_edge_unsigned_distance_m"]-
               rotated["nearest_boundary_edge_unsigned_distance_m"])<1e-7


def test_finite_SO3_builtin_audit():
    p,q,ep,eq=sample()
    m=triangle_patch_metrics(p,q,ep,eq)
    audit=objective_triangle_patch_check(p,q,ep,eq,m)
    assert audit["max_SO3_edge_distance_error_m"]<1e-7
    assert audit["max_SO3_orientation_dot_error"]<1e-9


def test_geometric_separation_does_not_create_physical_gap():
    p,q,ep,eq=sample()
    shift=np.array([0.,0.,3.])
    q=q+shift
    eq=eq+shift
    r=triangle_patch_metrics(p,q,ep,eq)
    assert r["nearest_boundary_edge_unsigned_distance_m"]==pytest.approx(3.)
    assert r["qualified_signed_rock_contact_gap_m"] is None
    assert not r["physical_contact_force_authorized"]


def test_genuine_boundary_mismatch_to_prior_diagnostic_fails_closed():
    p,q,ep,eq=sample()
    faces=source_face_incidence(
        [(1,2,3),(2,1,4)],[5,8],source_rows())
    index={(5,1):0,(5,2):1,(5,3):2,
           (8,2):3,(8,1):4,(8,4):5}
    pos=np.vstack((p,q))
    prior=[{
        "source_boundary_id":"R6BND-T0-SYNTHETIC-1-2",
        "unsigned_closest_segment_distance_m":1.,
        "classification":"AMBIGUOUS",
    }]
    with pytest.raises(SparseP1Error,match="SURFACE_PRIOR_FAIR_FEATURE_REPLAY_MISMATCH"):
        source_surface_patch_inventory(faces,index,pos,prior)


def test_inventory_preserves_source_ownership_and_zero_physical_volume():
    p,q,ep,eq=sample()
    faces=source_face_incidence(
        [(1,2,3),(2,1,4)],[5,8],source_rows())
    index={(5,1):0,(5,2):1,(5,3):2,
           (8,2):3,(8,1):4,(8,4):5}
    prior=[{
        "source_boundary_id":"R6BND-T0-SYNTHETIC-1-2",
        "unsigned_closest_segment_distance_m":0.,
        "classification":"AMBIGUOUS",
    }]
    inv=source_surface_patch_inventory(
        faces,index,np.vstack((p,q)),prior)
    assert inv["source_faces_at_original_boundary"]==2
    assert inv["source_edges"]==1
    assert inv["face_winding_p_outward_count"]==1
    assert inv["face_winding_q_outward_count"]==1
    assert inv["source_feature_eligibility_counts"]=={"AMBIGUOUS":1}
    assert inv["physically_closed_3D_volume_count"]==0
    assert inv["qualified_signed_solid_contact_count"]==0


def test_degenerate_triangle_rejected():
    p,q,ep,eq=sample()
    p[2]=p[1]
    with pytest.raises(SparseP1Error,match="SURFACE_PATCH_DEGENERATE_FACET"):
        triangle_patch_metrics(p,q,ep,eq)
