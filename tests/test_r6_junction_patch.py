"""Structural tests for overlap-derived junction patches and P1 traces."""
from __future__ import annotations

import math

import pytest

from arcana_worldsim.r6.physical.junction_patch import (
    _component_from_grid, _ear_clip, _extract_contour, _extract_ring,
    analyze_membership_topology, branch_exclusive_run,
    classify_trace_reach, deterministic_domain_radii,
    classify_corner_refinement, dirichlet_corner_errors, _refine_trace_edge,
)


def _signed_area(points):
    return 0.5 * math.fsum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )


def test_deterministic_ear_clipping_supports_nonconvex_simple_patch():
    # A simple concave L polygon; the former triangular fan assumption is not
    # imposed by this numerical triangulator.
    polygon = [(0., 0.), (3., 0.), (3., 1.), (1., 1.), (1., 3.), (0., 3.)]
    triangles = _ear_clip(polygon)
    assert triangles == _ear_clip(polygon)
    assert len(triangles) == len(polygon) - 2
    area = math.fsum(abs(_signed_area([polygon[i] for i in tri])) for tri in triangles)
    assert area == pytest.approx(abs(_signed_area(polygon)), rel=1e-12)


def test_two_of_three_overlap_extracts_only_seed_connected_component():
    mask = [[False] * 7 for _ in range(7)]
    for r in range(2, 5):
        for c in range(2, 5):
            mask[r][c] = True
    mask[6][6] = True  # disconnected overlap lobe is not part of the patch
    import numpy as np
    component = _component_from_grid(np.asarray(mask), (3, 3))
    assert int(component.sum()) == 9
    ring = _extract_ring(component)
    assert len(ring) == 4


def test_membership_topology_labels_ports_from_grid_adjacency():
    import numpy as np
    masks = np.zeros((7, 7), dtype=np.uint8)
    masks[3, 3] = 3  # central two-corridor patch
    masks[3, 2] = masks[3, 1] = 1
    masks[3, 4] = masks[3, 5] = 2
    masks[2, 3] = masks[1, 3] = 4
    result = analyze_membership_topology(masks, (3, 3))
    assert result["patch_component_count"] == 1
    assert result["exclusive_region_node_counts"] == {"1": 2, "2": 2, "4": 2}
    assert result["port_component_counts"] == {"1": 1, "2": 1, "4": 1}
    assert result["membership_mask_counts_in_central_domain"]["011"] == 1
    assert result["membership_mask_counts_in_patch"]["011"] == 1
    assert sum(result["port_component_counts"].values()) == 3


def test_membership_topology_preserves_disconnected_port_components():
    import numpy as np
    masks = np.zeros((7, 7), dtype=np.uint8)
    masks[3, 3] = 3
    # Two disconnected mask-100 neighbors create two distinct interfaces.
    masks[2, 3] = 1
    masks[4, 3] = 1
    result = analyze_membership_topology(masks, (3, 3))
    assert result["port_component_counts"]["1"] == 2
    assert result["port_component_counts"]["2"] == 0
    assert result["port_component_counts"]["4"] == 0


def test_acute_branch_requires_deterministic_domain_expansion_for_port():
    # A narrow-angle overlap remains multi-corridor for longer before the
    # exclusive run; the status changes only when the predeclared domain grows.
    samples = [3, 3, 3, 1, 1, 1]
    initial = branch_exclusive_run(samples, 1, initial_sample_count=3,
                                   topological_limit_sample=6, minimum_persistent_samples=2)
    expanded = branch_exclusive_run(samples, 1, initial_sample_count=6,
                                    topological_limit_sample=6, minimum_persistent_samples=2)
    assert initial["status"] == "LOCAL_DOMAIN_EXPANSION_REQUIRED"
    assert expanded["status"] == "EXCLUSIVE_CORRIDOR_FOUND"
    assert expanded["first_persistent_sample_index"] == 3


def test_branch_search_stops_at_next_topological_feature_without_fabricating_port():
    result = branch_exclusive_run([3, 3, 3, 1, 1], 1, initial_sample_count=2,
                                 topological_limit_sample=3,
                                 minimum_persistent_samples=2)
    assert result["status"] == "NO_EXCLUSIVE_CORRIDOR_BEFORE_TOPOLOGICAL_LIMIT"
    assert result["first_persistent_sample_index"] is None


def test_domain_expansion_is_deterministic_and_strictly_topology_bounded():
    radii = deterministic_domain_radii(100.0, 450.0, max_level=5)
    assert radii == deterministic_domain_radii(100.0, 450.0, max_level=5)
    assert radii[:3] == (100.0, 200.0, 400.0)
    assert radii[-1] < 450.0
    assert len(radii) == 4


def test_trace_reach_distinguishes_pretrace_corner_failure_from_trace_failure():
    assert classify_trace_reach("INVALID", "corner port trace disagreement 0.01") == (
        "TRACE_NOT_REACHED", "PORT_CORNER_DIRICHLET_CONFLICT")
    assert classify_trace_reach("INVALID", "corridor trace tolerance unmet at depth 12") == (
        "TRACE_FAIL", "TRACE_REFINEMENT_LIMIT_REACHED")
    assert classify_trace_reach("BOUND", None, True) == ("TRACE_PASS", "TRACE_CONVERGED")
    assert classify_trace_reach("BOUND", None, False) == ("TRACE_FAIL", "TRACE_NONCONVERGENT")


def test_corner_dirichlet_compatibility_requires_pure_shared_plate_value():
    point=(1.0,0.0,0.0)
    result=dirichlet_corner_errors((0,1,0),(0,1,0),(0,1,0),point,point)
    assert result["status"]=="CORNER_COMPATIBLE"
    assert result["E_corner"]==0
    assert result["same_spherical_point_used_for_both_port_evaluators"]
    conflict=dirichlet_corner_errors((0.3,0.7,0),(0,0.6,0.4),(0,1,0),point,point)
    assert conflict["status"]=="CORNER_DIRICHLET_CONFLICT"
    assert conflict["E_corner"]==pytest.approx(0.4)
    with pytest.raises(ValueError,match="same spherical point"):
        dirichlet_corner_errors((0,1,0),(0,1,0),(0,1,0),point,(0,1e-8,1))


def test_corner_refinement_distinguishes_convergence_plateau_and_unresolved():
    assert classify_corner_refinement((0.1,0.02,0.001,0.00005))=="CORNER_COMPATIBLE"
    assert classify_corner_refinement((0.1,0.02,0.001,0.00005),
        expected_errors=(0.1,0.02,0.001,0.00008))=="CORNER_COMPATIBLE"
    assert classify_corner_refinement((0.1,0.02,0.001,0.00005),
        expected_errors=(0.1,0.02,0.001,0.002))=="CORNER_NUMERICALLY_UNRESOLVED"
    assert classify_corner_refinement((0.4,0.21,0.202,0.201))=="CORNER_DIRICHLET_CONFLICT"
    assert classify_corner_refinement((0.1,0.02,0.001,0.00005),
        expected_errors=(0.4,0.21,0.202,0.201))=="CORNER_DIRICHLET_CONFLICT"
    assert classify_corner_refinement((0.4,0.21,0.13,0.08))=="CORNER_NUMERICALLY_UNRESOLVED"


def test_membership_ports_do_not_require_convex_patch_shape():
    import numpy as np
    masks = np.zeros((7, 7), dtype=np.uint8)
    # Concave, four-neighbour connected >=2 mask set.
    masks[1, 1:4] = 3
    masks[2:5, 1] = 3
    masks[4, 2:5] = 3
    masks[1, 4] = 1
    masks[2, 0] = 2
    masks[4, 5] = 4
    result = analyze_membership_topology(masks, (1, 1))
    assert result["patch_component_count"] == 1
    assert result["port_component_counts"] == {"1": 1, "2": 1, "4": 1}


def test_spherical_membership_contour_bisects_actual_overlap_boundary():
    import numpy as np
    axis = np.linspace(-2., 2., 17)
    mask = np.zeros((17, 17), dtype=bool)
    for r, y in enumerate(axis):
        for c, x in enumerate(axis):
            mask[r, c] = x*x + y*y <= 1.2**2
    component = _component_from_grid(mask, (8, 8))
    ring = _extract_contour(component, axis,
                            lambda x, y: x*x + y*y <= 1.2**2,
                            root_tolerance_m=1e-9)
    assert len(ring) >= 8
    assert all(abs(math.hypot(x, y) - 1.2) < 1e-8 for x, y in ring)
    assert _signed_area(ring) > 0


def test_adaptive_port_trace_refines_from_existing_operator_and_is_deterministic():
    def smoothstep(t):
        return t * t * (3. - 2. * t)
    def exact(_port, xy):
        v = smoothstep(xy[0])
        return (1. - v, v, 0.)
    points, metrics = _refine_trace_edge((0., 0.), (1., 0.), (1., 0., 0.),
                                         (0., 1., 0.), "AB", exact, 1e-4, 12, "e0")
    assert metrics["subdivision_count"] > 0
    assert len(points) == metrics["final_edge_count"]
    assert points == _refine_trace_edge((0., 0.), (1., 0.), (1., 0., 0.),
                                        (0., 1., 0.), "AB", exact, 1e-4, 12, "e0")[0]
    for (a, wa), (b, wb) in zip(points, points[1:] + [((1., 0.), (0., 1., 0.))]):
        for t in (.25, .5, .75):
            x = a[0] * (1-t) + b[0] * t
            linear = (1-t) * wa[1] + t * wb[1]
            assert abs(linear - smoothstep(x)) <= 1e-4


def test_adaptive_port_trace_fails_closed_at_declared_depth():
    def exact(_port, xy):
        v = xy[0] ** 0.25
        return (1. - v, v, 0.)
    with pytest.raises(ValueError, match="tolerance unmet at depth"):
        _refine_trace_edge((0., 0.), (1., 0.), (1., 0., 0.),
                           (0., 1., 0.), "AB", exact, 1e-12, 0, "e0")
