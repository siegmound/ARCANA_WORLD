from __future__ import annotations

import pytest

from scripts.r6_b6f_event_numerical_validity import evaluate


@pytest.fixture(scope="module")
def b6f_data():
    return evaluate(enforce_identity=False)


def test_b6f_is_diagnostic_only_and_does_not_select_dt_or_t1(b6f_data):
    result = b6f_data["result"]
    assert result["b6g_readiness"] == "NOT_READY_FOR_FIRST_DT_ADJUDICATION"
    assert result["qualified_source_commit"]
    assert result["scientific_side_effect_check"]["dt_selected"] is False
    assert result["scientific_side_effect_check"]["t1_created"] is False
    assert result["scientific_side_effect_check"]["canonical_state_changed"] is False


def test_conditional_rift_horizon_is_not_a_topology_bound_or_dt(b6f_data):
    result = b6f_data["result"]
    assert result["qualified_bound_count"] == 1
    bound = result["qualified_bounds"][0]
    assert bound["value"] == pytest.approx(27123.405156307464)
    assert bound["semantics"].endswith("NOT_A_DT")
    assert result["topology_positive_bound"] is None
    assert result["current_smallest_qualified_bound_not_a_dt"] is None


def test_mesh_counts_identity_and_plate_local_rigid_invariance(b6f_data):
    mesh = b6f_data["result"]["mesh_evidence"]
    assert mesh["node_count"] == 64442
    assert mesh["triangle_count"] == 128880
    assert mesh["normalized_mesh_sha256"] == "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad"
    assert mesh["edge_count"] == 193320
    assert b6f_data["result"]["governed_representation_counts"] == {
        "boundary_side_entities": 3966, "boundary_vertex_representatives": 7932,
        "interfaces": 1983, "interior_entities": 62469,
        "junction_relations": 20, "junction_side_entities": 60,
        "representative_count": 70461}
    assert all(sweep["all_coordinates_finite"] for sweep in b6f_data["sweep"])
    assert all(sweep["negative_orientation_count"] == 0 for sweep in b6f_data["sweep"])
    assert max(s["max_abs_spherical_area_ratio_error"] for s in b6f_data["sweep"]) < 1e-10


def test_interface_and_junction_validity_remain_unqualified(b6f_data):
    result = b6f_data["result"]
    assert result["boundary_evidence"]["interface_count"] == 1983
    assert result["boundary_evidence"]["junction_relation_count"] == 20
    assert result["interface_bound"] is None
    assert result["junction_bound"] is None
    assert result["boundary_evidence"]["geological_boundary_type"] == "UNKNOWN"


def test_constraint_inventory_has_required_categories_and_closed_inapplicable_items(b6f_data):
    rows = b6f_data["inventory"]
    ids = {row["constraint_id"] for row in rows}
    assert {"kinematic_law", "topology_event", "rigid_rotation", "node_displacement",
            "local_mesh_scale", "interface_representation", "junction_compatibility",
            "mesh_geometric", "state_transfer", "system_memory", "remesh_trigger",
            "solver_stability"} <= ids
    assert all(row["threshold_status"] in {
        "QUALIFIED_BOUND_AVAILABLE", "DERIVABLE_BOUND_AVAILABLE",
        "THRESHOLD_QUALIFICATION_REQUIRED", "EVENT_COVERAGE_REQUIRED",
        "NOT_APPLICABLE_TO_MVP", "UNKNOWN"} for row in rows)
    assert next(row for row in rows if row["constraint_id"] == "solver_stability")["threshold_status"] == "NOT_APPLICABLE_TO_MVP"


def test_event_absence_is_not_assumed_from_missing_detectors(b6f_data):
    taxonomy = {row["event_class"]: row["status"] for row in b6f_data["taxonomy"]}
    allowed = {"DETECTOR_AVAILABLE", "DERIVABLE_DETECTOR", "DETECTOR_IMPLEMENTATION_REQUIRED",
               "MODEL_REQUIRED", "NOT_RELEVANT_TO_FIRST_SEGMENT", "UNKNOWN"}
    assert set(taxonomy.values()) <= allowed
    assert taxonomy["rift activation"] == "DETECTOR_AVAILABLE"
    assert taxonomy["plate split / merge / creation / termination"] == "MODEL_REQUIRED"
    assert taxonomy["junction birth / death / connectivity reassignment"] == "MODEL_REQUIRED"

