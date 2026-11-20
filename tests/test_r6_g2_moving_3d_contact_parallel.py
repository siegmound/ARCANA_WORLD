"""Source-free diagnostics of moving 3D contact and regional parallel parity.

These prove algebraic properties on small manufactured meshes, not real
tectonic surface clearance or coupled updated-geometry mechanics.
"""
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from experiments.plate58_deforming_explore_v1.spherical_exterior import (
    frames_and_cartesian,
)
from experiments.plate58_deforming_explore_v1.g2_source_contact_objectivity import (
    contact_registry, assemble_split_source, euler_source_en,
)
from experiments.plate58_deforming_explore_v1.g2_global_sparse_p1_static import SparseP1Error
from experiments.plate58_deforming_explore_v1.g2_moving_3d_contact_parallel import (
    rigid_motion_with_residual, boundary_node_edges,
    moving_contact_geometry, compare_serial_parallel, unit,
)


def input_fixture():
    nodes = [11, 12, 13, 14]
    ll = {11:(10.,-159.), 12:(10.,-158.),
          13:(11.,-158.), 14:(11.,-159.)}
    faces = [(11,12,13), (11,13,14)]
    plates = [5,8]
    contacts = [{
        "source_edge_node_ids":[11,13],
        "plate_pair":[5,8],
        "source_boundary_id":"R6BND-T0-MANUFACTURED"
    }]
    pre = {n:{"crust_thickness_m":2e4,
              "mantle_lithosphere_thickness_m":7e4} for n in nodes}
    registry = contact_registry(nodes, faces, plates, ll, contacts)
    incident = boundary_node_edges(contacts, registry)
    K, index, coords, plate_by_view, stats = assemble_split_source(
        nodes, faces, plates, ll, pre
    )
    xyz, radial, east, north = frames_and_cartesian(coords)
    return registry, incident, index, plate_by_view, xyz, east, north


def sample_geometry(shift=0., rotation=None):
    reg, incident, index, plate_by_view, xyz, east, north = input_fixture()
    o = {5:np.zeros(3), 8:np.zeros(3)}
    g = np.zeros(2*len(xyz))
    u = np.zeros_like(g)
    if shift:
        for row in reg["contacts"]:
            idx = index[(8, int(row["parent_node_id"]))]
            u[2*idx:2*idx+2] = shift*np.asarray(row["normal_EN"])
    v = np.zeros_like(g)
    pos, vel, rotations = rigid_motion_with_residual(
        xyz, east, north, plate_by_view, o, g, u, v, 100
    )
    if rotation is not None:
        Q = np.asarray(rotation)
        pos = pos @ Q.T
        vel = vel @ Q.T
        east = east @ Q.T
        north = north @ Q.T
        rotations = {k: Q@R@Q.T for k,R in rotations.items()}
    contact = moving_contact_geometry(
        pos, vel, rotations, east, north, index,
        reg["contacts"], incident, np.zeros(len(reg["contacts"])),
        np.zeros(len(reg["contacts"]))
    )
    return contact, pos, vel


def test_contact_source_edges_only_and_original_boundary_id():
    reg, incident, *_ = input_fixture()
    assert set(incident) == {
        ((5,8),11),((5,8),13)
    }
    assert all(
        edge[1] == "R6BND-T0-MANUFACTURED"
        for rows in incident.values() for edge in rows
    )
    with pytest.raises(SparseP1Error,match="BOUNDARY_PROVENANCE_MISMATCH"):
        boundary_node_edges([{
            "source_edge_node_ids":[11,12],
            "plate_pair":[5,8],
            "source_boundary_id":"R6BND-T0-FAKE"}], reg)


def test_zero_displacement_both_views_coincident():
    result, *_ = sample_geometry(0.)
    assert result["source_contact_link_count"] == 2
    assert result["max_absolute_geometry_minus_T0_gap_m"] < 1e-10
    assert result["geometric_negative_signed_gap_link_count_1microm"] == 0


@pytest.mark.parametrize("shift,sign",[(10.,1),(-10.,-1)])
def test_geometric_point_pair_signed_gap_detects_actual_opening_or_overlap(
    shift,sign
):
    result, *_ = sample_geometry(shift)
    values = [r["signed_geometric_point_pair_gap_m"]
              for r in result["source_link_details"]]
    assert np.all(np.sign(values) == sign)
    assert all(abs(v) > 1. for v in values)
    assert result["geometric_negative_signed_gap_link_count_1microm"] == (
        0 if sign>0 else 2
    )
    assert result["T0_KKT_geometry_closure_proved"] is False


@pytest.mark.parametrize("years", [0.,100.,1000.])
def test_exact_euler_rigid_trajectory_has_no_double_count(years):
    reg, inc, idx, plates, xyz, east, north = input_fixture()
    omega={5:np.array([0.,0.,1e-7]),
           8:np.array([1e-7,0.,0.])}
    # The original Euler component is ALREADY inside u=year*g.
    v=euler_source_en(
        np.asarray([[10.,-159.],[10.,-158.],[11.,-158.],
                    [10.,-159.],[11.,-158.],[11.,-159.]]),
        plates,omega)
    u=years*v
    moved, velocity, q=rigid_motion_with_residual(
        xyz,east,north,plates,omega,v,u,v,years
    )
    for p in set(plates):
        sel=np.flatnonzero(plates==p)
        expected=xyz[sel]@q[p].T
        assert np.max(np.linalg.norm(moved[sel]-expected,axis=1))<1e-7
        expected_velocity=np.cross(omega[p],expected)
        assert np.max(np.linalg.norm(velocity[sel]-expected_velocity,
                                     axis=1))<1e-10


def test_finite_SO3_frame_objectivity_of_geometric_gaps():
    original, pos, vel = sample_geometry(8.)
    Q=Rotation.from_rotvec([.8,-.34,.21]).as_matrix()
    rotated,pos_q,vel_q=sample_geometry(8.,rotation=Q)
    assert np.max(np.abs(pos@Q.T-pos_q))<1e-8
    for a,b in zip(original["source_link_details"],
                   rotated["source_link_details"],strict=True):
        assert a["parent_node_id"]==b["parent_node_id"]
        assert abs(a["signed_geometric_point_pair_gap_m"]-
                   b["signed_geometric_point_pair_gap_m"])<1e-8
        assert np.linalg.norm(
            np.asarray(a["current_contact_normal_cartesian"])@Q.T-
            np.asarray(b["current_contact_normal_cartesian"]))<1e-10


def test_dynamic_material_trajectories_rotate_objectively():
    reg, inc, idx, plates, xyz, east, north = input_fixture()
    omega={5:np.array([0.,0.,1e-7]),8:np.array([1e-7,0.,0.])}
    rng=np.random.default_rng(7)
    u=rng.normal(size=2*len(xyz))
    v=rng.normal(size=2*len(xyz))*.001
    g=np.zeros_like(u)
    a,va,_=rigid_motion_with_residual(
        xyz,east,north,plates,omega,g,u,v,1000.)
    Q=Rotation.from_rotvec([.35,.25,-.6]).as_matrix()
    moved_omega={p:Q@w for p,w in omega.items()}
    b,vb,_=rigid_motion_with_residual(
        xyz@Q.T,east@Q.T,north@Q.T,plates,moved_omega,g,u,v,1000.)
    assert np.max(np.linalg.norm(b-a@Q.T,axis=1))<2e-8
    assert np.max(np.linalg.norm(vb-va@Q.T,axis=1))<1e-9


def test_parallel_parity_accepts_identical_checkpoints():
    serial=[{"extent":8,"computed_field_sha256":"x"*64},
            {"extent":16,"computed_field_sha256":"y"*64}]
    parallel=list(reversed(serial))
    assert compare_serial_parallel(parallel,serial)["status"] == (
        "PASS_EXACT_NUMERICAL_SHA256_PARITY"
    )


def test_parallel_parity_rejects_numerical_drift():
    a=[{"extent":8,"computed_field_sha256":"a"},
       {"extent":16,"computed_field_sha256":"b"}]
    b=[{"extent":8,"computed_field_sha256":"a"},
       {"extent":16,"computed_field_sha256":"c"}]
    with pytest.raises(SparseP1Error,match="PARALLEL_NUMERICAL_PARITY_FAILED"):
        compare_serial_parallel(a,b)


def test_parallel_parity_rejects_missing_extent():
    a=[{"extent":8,"computed_field_sha256":"a"}]
    with pytest.raises(SparseP1Error,match="PARALLEL_SCALE_MISMATCH"):
        compare_serial_parallel(a,a)


def test_zero_vector_does_not_define_contact_normal():
    with pytest.raises(SparseP1Error,match="UNIT_VECTOR_DEGENERATE"):
        unit([0.,0.,0.])
