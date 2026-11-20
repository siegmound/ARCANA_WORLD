"""Source-free t0 contact normal, closest 3D segments and objective gap Jacobian."""
import math

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error
from experiments.plate58_deforming_explore_v1.spherical_exterior import frames_and_cartesian
from experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity import contact_registry,assemble_split_source
from experiments.plate58_deforming_explore_v1.g2_moving_3d_contact_parallel import (
    boundary_node_edges,moving_contact_geometry,rigid_motion_with_residual
)
from experiments.plate58_deforming_explore_v1.g2_t0_normal_segment_jacobian import (
    closest_segments,geometric_contact_feature_rows,
    normal_jacobian_audit,objective_feature_invariance,
    directional_gap_derivative,displaced_on_sphere,
    t0_source_centroid_edge_normal_audit
)


def fixture(shift=0.):
    ids=[11,12,13,14]
    ll={11:(10.,-159.),12:(10.,-158.),
        13:(11.,-158.),14:(11.,-159.)}
    faces=[(11,12,13),(11,13,14)]
    plates=[5,8]
    contacts=[{
        "source_edge_node_ids":[11,13],
        "plate_pair":[5,8],
        "source_boundary_id":"R6BND-T0-SYNTHETIC-11-13"
    }]
    pre={n:{"crust_thickness_m":20000.,
            "mantle_lithosphere_thickness_m":70000.} for n in ids}
    registry=contact_registry(ids,faces,plates,ll,contacts)
    incident=boundary_node_edges(contacts,registry)
    K,index,coords,plate_views,stats=assemble_split_source(
        ids,faces,plates,ll,pre)
    xyz,radial,east,north=frames_and_cartesian(coords)
    o={5:np.zeros(3),8:np.zeros(3)}
    g=np.zeros(K.shape[0]);u=np.zeros_like(g)
    for row in registry["contacts"]:
        q=index[(8,int(row["parent_node_id"]))]
        u[2*q:2*q+2]=float(shift)*np.asarray(row["normal_EN"])
    moved,rate,R=rigid_motion_with_residual(
        xyz,east,north,plate_views,o,g,u,g,0.)
    geo=moving_contact_geometry(
        moved,rate,R,east,north,index,registry["contacts"],
        incident,np.zeros(len(registry["contacts"])),
        np.zeros(len(registry["contacts"])))
    return contacts,registry,incident,index,registry["contacts"],\
           moved,rate,R,east,north,geo


def test_overlapping_coincident_segment_distance_zero():
    a,b,c,d=[np.array(x,dtype=float) for x in
             ((0,0,0),(2,0,0),(0,0,0),(2,0,0))]
    pa,pb,s,t,dist=closest_segments(a,b,c,d)
    assert dist==pytest.approx(0.,abs=1e-12)
    assert np.linalg.norm(pa-pb)<1e-12
    assert 0<=s<=1 and 0<=t<=1


def test_parallel_segments_uniform_clearance():
    x=closest_segments([0,0,0],[2,0,0],[0,4,0],[2,4,0])
    assert x[-1]==pytest.approx(4.)
    assert 0<=x[2]<=1 and 0<=x[3]<=1


def test_segment_endpoint_clamping():
    x=closest_segments([0,0,0],[1,0,0],[3,4,0],[4,4,0])
    assert x[-1]==pytest.approx(math.sqrt(20))
    assert x[2]==pytest.approx(1)
    assert x[3]==pytest.approx(0)


def test_segment_intersection_inside_both():
    a,b,c,d=([0,0,0],[2,0,0],[1,-1,0],[1,1,0])
    x=closest_segments(a,b,c,d)
    assert x[-1]<1e-12


def test_closest_segment_reversing_endpoints_preserves_distance():
    data=([1,2,-3],[7,5,-1],[6,-1,2],[2,8,4])
    x=closest_segments(*data)
    y=closest_segments(data[1],data[0],data[3],data[2])
    assert x[-1]==pytest.approx(y[-1],abs=1e-12)


def test_degenerate_segment_fails_closed():
    with pytest.raises(SparseP1Error,match="SEGMENT_DEGENERATE"):
        closest_segments([0,0,0],[0,0,0],[0,1,0],[1,1,0])


def test_genuine_source_matched_feature_coincident_at_t0():
    contacts,reg,incident,index,links,pos,v,R,e,n,geo=fixture()
    rows=geometric_contact_feature_rows(contacts,reg,index,pos,geo)
    assert len(rows)==1
    assert rows[0]["source_boundary_id"].startswith("R6BND-T0-")
    assert rows[0]["unsigned_nearest_segment_distance_m"]<1e-10
    assert abs(rows[0]["signed_nearest_segment_separation_m"])<1e-10
    assert geo["geometric_signed_gap_min_m"]==pytest.approx(0.,abs=1e-10)


@pytest.mark.parametrize("shift,sign",[(10.,1),(-10.,-1)])
def test_point_pair_gap_sign_and_nearest_segment_distance(shift,sign):
    contacts,reg,incident,index,links,pos,v,R,e,n,geo=fixture(shift)
    rows=geometric_contact_feature_rows(contacts,reg,index,pos,geo)
    assert rows[0]["unsigned_nearest_segment_distance_m"]>=0.
    assert np.sign(geo["geometric_signed_gap_min_m"])==sign
    # The segment closest distance is an independent unsigned quantity;
    # it is not generally equal to paired nodal normal gap.
    assert rows[0]["nearest_feature_is_not_a_physical_gap_law"] is True


def test_normal_mismatch_is_measured_not_assumed_zero():
    contacts,reg,incident,index,links,pos,v,R,e,n,geo=fixture()
    angles=[x["angle_normal_from_transported_T0_rad"]
            for x in geo["source_link_details"]]
    assert all(np.isfinite(angles))
    assert all(0<=x<=math.pi for x in angles)
    assert len(angles)==2


def test_geometric_jacobian_at_coincident_source_pair():
    contacts,reg,incident,index,links,pos,v,R,e,n,geo=fixture()
    audit=normal_jacobian_audit(
        pos,v,R,e,n,index,links,incident,geo)
    assert audit["sampled_pair_node_links"]==2
    assert audit["max_FD_refinement_discrepancy"]<3e-4
    for row in audit["derivative_details"]:
        a=row["directional_gap_derivatives"]
        assert abs(a["p"]["h0_25_m_derivative"]+1)<0.01
        assert abs(a["q"]["h0_25_m_derivative"]-1)<0.01


def test_geometric_jacobian_for_opening_contact():
    contacts,reg,incident,index,links,pos,v,R,e,n,geo=fixture(12.)
    audit=normal_jacobian_audit(
        pos,v,R,e,n,index,links,incident,geo)
    assert audit["sampled_pair_node_links"]==2
    assert audit["max_FD_refinement_discrepancy"]<3e-4


def test_finite_rotation_preserves_node_gaps_and_closest_edges():
    contacts,reg,incident,index,links,pos,v,R,e,n,geo=fixture(12.)
    checked=objective_feature_invariance(
        pos,v,R,e,n,index,links,incident,contacts,reg,geo)
    assert checked["max_node_pair_signed_gap_absolute_error_m"]<1e-7
    assert checked["max_closest_segment_distance_absolute_error_m"]<1e-7
    assert checked["max_signed_segment_gap_absolute_error_m"]<1e-7


def test_mismatched_source_edge_owner_rejected():
    contacts,reg,incident,index,links,pos,v,R,e,n,geo=fixture()
    wrong=[{**contacts[0],"plate_pair":[5,11]}]
    with pytest.raises(SparseP1Error,match="SOURCE_EDGE_OWNER_MISMATCH"):
        geometric_contact_feature_rows(wrong,reg,index,pos,geo)


def test_spherical_perturbation_preserves_radius():
    p=np.array([6371000.,0,0])
    for h in (0.1,1.):
        q=displaced_on_sphere(p,np.array([0.,h,0.]))
        assert abs(np.linalg.norm(q)-6371000.)<1e-8


def test_finite_difference_direction_uses_actual_current_normal():
    contacts,reg,incident,index,links,pos,v,R,e,n,geo=fixture(7.)
    normal=np.asarray(geo["source_link_details"][0][
        "current_contact_normal_cartesian"])
    forward=directional_gap_derivative(pos,v,R,e,n,index,links,
                                        incident,0,normal,"q",0.5)
    backward=directional_gap_derivative(pos,v,R,e,n,index,links,
                                         incident,0,normal,"p",0.5)
    assert 0.9<forward<1.1
    assert -1.1<backward<-.9



def test_t0_centroid_vs_edge_normal_source_segment_audit():
    ids=[11,12,13,14]
    ll={11:(10.,-159.),12:(10.,-158.),
        13:(11.,-158.),14:(11.,-159.)}
    faces=[(11,12,13),(11,13,14)]
    plates=[5,8]
    source=[{
        "source_edge_node_ids":[11,13],
        "plate_pair":[5,8],
        "source_boundary_id":"R6BND-T0-SYNTHETIC-11-13"
    }]
    r=t0_source_centroid_edge_normal_audit(
        faces,plates,ll,source)
    assert r["original_source_contact_edge_count"]==1
    assert len(r["per_source_boundary_edge"])==1
    row=r["per_source_boundary_edge"][0]
    assert row["source_plate_pair"]==[5,8]
    assert row["original_edge_length_m"]>0
    assert 0<=row["angle_centroid_normal_vs_edge_normal_rad"]<math.pi/2


def test_t0_centroid_vs_edge_rejects_fabricated_plate_pair():
    ll={11:(10.,-159.),12:(10.,-158.),
        13:(11.,-158.),14:(11.,-159.)}
    src=[{"source_edge_node_ids":[11,13],
          "plate_pair":[5,11],
          "source_boundary_id":"R6BND-T0-SYNTHETIC"}]
    with pytest.raises(SparseP1Error,match="EDGE_TRIANGLE_OWNERSHIP_INVALID"):
        t0_source_centroid_edge_normal_audit(
            [(11,12,13),(11,13,14)],[5,8],ll,src)
