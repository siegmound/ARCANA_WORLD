import math

import numpy as np
import pytest

from arcana_worldsim.r6.physical.boundary_geometry import (
    BoundaryFeature,
    Junction,
    SphericalBoundaryArrangement,
    SphericalSegment,
    unit_xyz,
)
from arcana_worldsim.r6.physical.junction_basis import ThreePlateJunctionBasis
from arcana_worldsim.r6.physical.reference_mesh import (
    OwnershipSample,
    build_icosphere,
    integrate_spherical_ownership,
    validate_spherical_mesh,
)

R = 6_371_000.0


def test_meridian_is_minor_great_circle_and_distance_is_spherical():
    edge = SphericalSegment(-20, 30, 20, 30)
    assert edge.distance_m(0, 31, R) == pytest.approx(R * math.radians(1), rel=1e-10)


def test_latitude_parallel_is_small_circle_not_great_circle():
    edge = SphericalSegment(60, 0, 60, 1, "SMALL_CIRCLE", 1)
    great_circle = SphericalSegment(60, 0, 60, 1)
    assert edge.distance_m(59.5, 0.5, R) == pytest.approx(R * math.radians(0.5), abs=1e-5)
    assert edge.distance_m(59.5, 0.5, R) < great_circle.distance_m(59.5, 0.5, R)


def test_small_circle_dateline_sweep_and_endpoints():
    edge = SphericalSegment(10, 179, 10, -179, "SMALL_CIRCLE", 2)
    assert edge.distance_m(10, 180, R) == pytest.approx(0, abs=1e-7)
    assert edge.distance_m(10, -179, R) == pytest.approx(0, abs=1e-7)
    expected = R * math.acos(math.sin(math.radians(10)) ** 2 +
                             math.cos(math.radians(10)) ** 2 * math.cos(math.radians(1)))
    assert edge.distance_m(10, 178, R) == pytest.approx(expected, abs=1e-6)


def test_polar_meridian_is_stable():
    edge = SphericalSegment(89, -90, 90, -90)
    assert edge.distance_m(90, 135, R) == pytest.approx(0, abs=1e-6)


def test_segment_endpoint_is_included():
    edge = SphericalSegment(0, 0, 0, 1, "SMALL_CIRCLE", 1)
    assert edge.distance_m(1, 0, R) == pytest.approx(R * math.radians(1), rel=1e-10)


def test_curved_multisegment_and_unequal_segmentation_converge():
    whole = SphericalSegment(0, 0, 20, 20)
    midpoint = (unit_xyz(0, 0) + unit_xyz(20, 20))
    midpoint /= math.sqrt(float(midpoint @ midpoint))
    mid_lat = math.degrees(math.asin(float(midpoint[2])))
    mid_lon = math.degrees(math.atan2(float(midpoint[1]), float(midpoint[0])))
    split = (SphericalSegment(0, 0, mid_lat, mid_lon),
             SphericalSegment(mid_lat, mid_lon, 20, 20))
    query = (12.0, 8.0)
    d_whole = whole.distance_m(*query, R)
    d_split = min(s.distance_m(*query, R) for s in split)
    assert d_split == pytest.approx(d_whole, abs=2.0)


def test_short_segment_remains_non_degenerate():
    edge = SphericalSegment(0, 0, 0, 0.01, "SMALL_CIRCLE", 0.01)
    assert 0 < edge.distance_m(0.001, 0.005, R) < 200


def test_two_plate_zone_and_core_partition_of_unity():
    edge = SphericalSegment(-5, 0, 5, 0)
    feature = BoundaryFeature("B0", 1, 2, (edge,))
    domain = lambda lat, lon: 1 if lon < 0 else 2
    arrangement = SphericalBoundaryArrangement((feature,), (), 400_000, domain, R)
    zone = arrangement.classify(0, 1)
    assert zone.category == "BOUNDARY_ZONE"
    assert sum(w for _, w in zone.plate_weights) == pytest.approx(1)
    assert all(0 <= w <= 1 for _, w in zone.plate_weights)
    core = arrangement.classify(30, 30)
    assert core.category == "RIGID_CORE" and core.plate_ids == (2,)


def test_degree3_junction_is_one_patch_with_stable_incidence():
    features = (
        BoundaryFeature("ab", 1, 2, (SphericalSegment(0, 0, 20, 0),)),
        BoundaryFeature("ac", 1, 3, (SphericalSegment(0, 0, -10, -17),)),
        BoundaryFeature("bc", 2, 3, (SphericalSegment(0, 0, -10, 17),)),
    )
    j = Junction("J0", 0, 0, ("ab", "ac", "bc"), (1, 2, 3))
    arrangement = SphericalBoundaryArrangement(features, (j,), 200_000,
                                                lambda lat, lon: 1, R)
    result = arrangement.classify(0, 0)
    assert result.category == "JUNCTION_PATCH"
    assert result.plate_ids == (1, 2, 3)
    assert result.junction_id == "J0"


@pytest.mark.parametrize("center, endpoints", [
    ((61.0, 179.8), ((78.0, 177.0), (48.0, 164.0), (53.0, -164.0))),
    ((82.0, -35.0), ((88.0, 72.0), (70.0, -156.0), (66.0, 4.0))),
    ((-12.0, 36.0), ((13.0, 44.0), (-28.0, 12.0), (-20.0, 65.0))),
])
def test_asymmetric_high_latitude_and_dateline_junction_has_single_region_owner(center, endpoints):
    lat, lon = center
    pairs = ((1, 2), (2, 3), (1, 3))
    features = tuple(
        BoundaryFeature(f"b{i}", *pairs[i],
                        (SphericalSegment(lat, lon, end_lat, end_lon),))
        for i, (end_lat, end_lon) in enumerate(endpoints)
    )
    junction = Junction("J", lat, lon, tuple(f.boundary_id for f in features), (1, 2, 3))
    arrangement = SphericalBoundaryArrangement(features, (junction,), 200_000,
                                                lambda _lat, _lon: 1, R)

    query = arrangement.classify(lat, lon)

    assert query.category == "JUNCTION_PATCH"
    assert query.junction_id == "J"
    assert query.plate_ids == (1, 2, 3)
    # Ownership is one-valued, but the present point-query API deliberately
    # exposes no three-plate basis; this must not be mistaken for readiness.
    assert query.plate_weights is None


def test_close_parallel_nonjunction_footprints_fail_closed():
    features = (
        BoundaryFeature("a", 1, 2, (SphericalSegment(0, -2, 0, 2, "SMALL_CIRCLE", 4),)),
        BoundaryFeature("b", 2, 3, (SphericalSegment(0.5, -2, 0.5, 2, "SMALL_CIRCLE", 4),)),
    )
    arrangement = SphericalBoundaryArrangement(features, (), 200_000,
                                                lambda lat, lon: 2, R)
    result = arrangement.classify(0.25, 0)
    assert result.category == "INFEASIBLE"
    assert result.reason == "overlapping non-junction boundary footprints"


def test_closed_loop_preserves_inside_and_outside_parent_domains():
    loop = BoundaryFeature("loop", 1, 2, (
        SphericalSegment(-5, -5, -5, 5, "SMALL_CIRCLE", 10),
        SphericalSegment(-5, 5, 5, 5),
        SphericalSegment(5, 5, 5, -5, "SMALL_CIRCLE", -10),
        SphericalSegment(5, -5, -5, -5),
    ))
    arrangement = SphericalBoundaryArrangement((loop,), (), 100_000,
                                                lambda lat, lon: 1 if abs(lat) < 5 and abs(lon) < 5 else 2, R)
    assert arrangement.classify(0, 0).plate_ids == (1,)
    assert arrangement.classify(20, 20).plate_ids == (2,)


def test_narrow_intervening_plate_core_is_detected_as_overlap():
    features = (
        BoundaryFeature("south", 1, 2, (SphericalSegment(0, -5, 0, 5, "SMALL_CIRCLE", 10),)),
        BoundaryFeature("north", 2, 3, (SphericalSegment(0.5, -5, 0.5, 5, "SMALL_CIRCLE", 10),)),
    )
    arrangement = SphericalBoundaryArrangement(features, (), 200_000,
                                                lambda lat, lon: 2, R)
    assert arrangement.classify(0.25, 0).category == "INFEASIBLE"


def test_two_nearby_junction_patches_are_not_merged_implicitly():
    features = tuple(BoundaryFeature(f"b{i}", i + 1, i + 2,
        (SphericalSegment(0, i, 1, i),)) for i in range(6))
    js = (Junction("J0", 0, 0, ("b0", "b1", "b2"), (1, 2, 3)),
          Junction("J1", 0, 1, ("b3", "b4", "b5"), (4, 5, 6)))
    arrangement = SphericalBoundaryArrangement(features, js, 200_000, lambda lat, lon: 1, R)
    result = arrangement.classify(0, 0)
    assert result.category == "INFEASIBLE"
    assert result.reason == "junction patches overlap at requested global width"


def test_corridor_weights_are_continuous_at_centerline_and_support_is_inherited():
    feature = BoundaryFeature("B", 1, 2, (SphericalSegment(-10, 0, 10, 0),))
    arrangement = SphericalBoundaryArrangement((feature,), (), 400_000,
                                                lambda lat, lon: 1 if lon < 0 else 2, R)
    left, center, right = (arrangement.classify(0, x) for x in (-1e-7, 0, 1e-7))
    assert all(x.category == "BOUNDARY_ZONE" for x in (left, center, right))
    assert left.plate_weights[0][1] == pytest.approx(0.5, abs=1e-7)
    assert center.plate_weights == ((1, 0.5), (2, 0.5))
    assert right.plate_weights[1][1] == pytest.approx(0.5, abs=1e-7)
    assert center.support == "MODEL_DERIVED_FROM_COARSE_CANONICAL_T0_SUPPORT"


def test_duplicate_ids_and_invalid_small_circle_are_rejected():
    with pytest.raises(ValueError):
        SphericalSegment(0, 0, 1, 1, "SMALL_CIRCLE", 1)
    f = BoundaryFeature("x", 1, 2, (SphericalSegment(0, 0, 1, 1),))
    with pytest.raises(ValueError):
        SphericalBoundaryArrangement((f, f), (), 100_000, lambda lat, lon: 1, R)
    with pytest.raises(ValueError):
        SphericalSegment(0, 0, 0, 180)
    with pytest.raises(ValueError):
        SphericalSegment(0, 0, 0, 2, "SMALL_CIRCLE", 1)


@pytest.mark.parametrize("azimuths", [(90.0, 210.0, 330.0), (77.0, 196.0, 305.0)])
def test_conforming_three_plate_fan_has_nonnegative_partition_and_shared_edge_traces(azimuths):
    basis = ThreePlateJunctionBasis("J-test", 0, 0, (10, 20, 30), 100_000,
                                    subdivisions_per_side=8, azimuths_deg=azimuths)
    center = basis.weights_xy(0, 0)
    assert center is not None
    assert tuple(p for p, _ in center) == (10, 20, 30)
    assert [w for _, w in center] == pytest.approx([1 / 3] * 3)
    assert len({triangle.triangle_id for triangle in basis.triangles}) == 24
    for triangle in basis.triangles:
        for nodal in triangle.nodal_weights:
            assert min(nodal) >= 0
            assert sum(nodal) == pytest.approx(1.0, abs=1e-14)
    # Every shared fan edge is represented by the same endpoint nodal state;
    # each outer edge exactly recovers the existing pairwise smoothstep trace.
    for edge in range(3):
        for t in (0.0, 0.125, 0.5, 0.875, 1.0):
            xy0, xy1 = basis.vertices[edge], basis.vertices[(edge + 1) % 3]
            xy = (xy0[0] * (1 - t) + xy1[0] * t,
                  xy0[1] * (1 - t) + xy1[1] * t)
            actual = basis.weights_xy(*xy)
            expected = basis.boundary_trace(edge, t)
            assert actual is not None
            assert tuple(p for p, _ in actual) == tuple(p for p, _ in expected)
            assert [w for _, w in actual] == pytest.approx([w for _, w in expected], abs=2e-10)
            assert sum(weight for _, weight in actual) == pytest.approx(1.0, abs=1e-12)
            assert all(0.0 <= weight <= 1.0 for _, weight in actual)


@pytest.mark.parametrize("center", [(82.0, 179.8), (89.0, -45.0), (-76.0, 31.0)])
def test_three_plate_basis_is_spherical_and_stable_at_poles_and_dateline(center):
    basis = ThreePlateJunctionBasis("J-sphere", *center, (1, 2, 3), 80_000,
                                    subdivisions_per_side=8, azimuths_deg=(12, 151, 282))
    # Exponential-map construction gives the same local point independently of
    # longitude wrapping and remains nonsingular at high latitude.
    xy = (8_000.0, -5_000.0)
    theta = math.hypot(*xy) / R
    tangent = xy[0] * basis.east + xy[1] * basis.north
    p = math.cos(theta) * basis.center + (math.sin(theta) / math.hypot(*xy)) * tangent
    lat = math.degrees(math.asin(float(p[2])))
    lon = math.degrees(math.atan2(float(p[1]), float(p[0])))
    first = basis.weights_at(lat, lon)
    wrapped = basis.weights_at(lat, lon + 360.0)
    assert first is not None
    assert wrapped is not None
    assert tuple(p for p, _ in first) == tuple(p for p, _ in wrapped)
    assert [w for _, w in first] == pytest.approx([w for _, w in wrapped], abs=1e-12)
    assert sum(value for _, value in first) == pytest.approx(1.0, abs=1e-12)


def test_between_node_junction_trace_matches_corridor_with_predeclared_error_bound():
    tolerance = 1e-4  # dimensionless numerical handoff tolerance, predeclared
    basis = ThreePlateJunctionBasis("J-trace", 0, 0, (1, 2, 3), 120_000,
                                    subdivisions_per_side=128)
    assert basis.max_smoothstep_trace_error <= tolerance
    velocities = {1: np.array((1.0, 0.0, 0.0)),
                  2: np.array((-1.0, 0.0, 0.0)),
                  3: np.array((0.0, 1.0, 0.0))}
    max_velocity_jump = 0.0
    for edge in range(3):
        a, b = basis.vertices[edge], basis.vertices[(edge + 1) % 3]
        p0, p1 = basis.plate_ids[edge], basis.plate_ids[(edge + 1) % 3]
        for k in range(128):
            t = (k + 0.5) / 128
            xy = (a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t)
            junction = dict(basis.weights_xy(*xy))
            blend = t * t * (3 - 2 * t)
            corridor = {p: 0.0 for p in basis.plate_ids}
            corridor[p0], corridor[p1] = 1 - blend, blend
            assert max(abs(junction[p] - corridor[p]) for p in basis.plate_ids) <= tolerance
            vj = sum((junction[p] * velocities[p] for p in basis.plate_ids), np.zeros(3))
            vc = sum((corridor[p] * velocities[p] for p in basis.plate_ids), np.zeros(3))
            max_velocity_jump = max(max_velocity_jump, float(np.linalg.norm(vj - vc)))
    assert max_velocity_jump <= 2 * tolerance


def test_deterministic_global_spherical_mesh_area_closure_and_nested_refinement():
    l0a, l0b = build_icosphere(0), build_icosphere(0)
    l1 = build_icosphere(1)
    check0, check1 = validate_spherical_mesh(l0a), validate_spherical_mesh(l1)
    assert l0a.face_ids == l0b.face_ids and l0a.faces == l0b.faces
    assert l0a.face_count == 20 and l1.face_count == 80
    assert l1.node_ids[:len(l0a.node_ids)] == l0a.node_ids
    assert check0["topology_pass"] and check1["topology_pass"]
    assert check0["area_closure_pass"] and check1["area_closure_pass"]
    assert check0["relative_area_error"] < 1e-12
    assert check1["relative_area_error"] < 1e-12


def test_adaptive_global_ownership_preserves_unresolved_area_and_is_deterministic():
    mesh = build_icosphere(0)

    def three_sector_owner(p):
        lon = math.atan2(float(p[1]), float(p[0])) % (2 * math.pi)
        lat = math.asin(float(p[2]))
        owner = f"CORE_{int(lon / (2 * math.pi / 3)) % 3}"
        # Exact nearest distance to the finite meridian arc, including polar
        # endpoints (not distance to its antipodal continuation).
        angles = (0.0, 2 * math.pi / 3, 4 * math.pi / 3)
        distances = []
        for angle in angles:
            delta = math.atan2(math.sin(lon - angle), math.cos(lon - angle))
            plane_distance = math.asin(min(1.0, abs(math.cos(lat) * math.sin(delta))))
            distances.append(plane_distance if math.cos(delta) >= 0 else
                             min(plane_distance, math.pi / 2 - abs(lat)))
        return OwnershipSample(owner, R * min(distances))

    l0 = integrate_spherical_ownership(mesh, three_sector_owner, max_depth=2)
    l0_repeat = integrate_spherical_ownership(mesh, three_sector_owner, max_depth=2)
    l1 = integrate_spherical_ownership(mesh, three_sector_owner, max_depth=3)
    assert l0 == l0_repeat
    assert l0["multiowned_area_m2"] == 0.0
    assert l1["multiowned_area_m2"] == 0.0
    assert l0["closure_error_m2"] < 1.0
    assert l1["closure_error_m2"] < 1.0
    assert l0["unassigned_ambiguous_area_m2"] > 0
    assert l1["unassigned_ambiguous_area_m2"] <= l0["unassigned_ambiguous_area_m2"]
    assert set(l1["owner_area_m2"]) == {"CORE_0", "CORE_1", "CORE_2"}
