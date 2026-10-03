from __future__ import annotations

import subprocess

import pytest

from scripts.r6_b6h_topology_event_coverage_closure import (
    RIFT_YEARS,
    evaluate,
    rift_bound_reached,
    topology_delta,
)


@pytest.fixture(scope="module")
def b6h():
    return evaluate()


def test_b6h_qualifies_current_descendant_and_preserves_partial_readiness(b6h):
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    result = b6h["result"]
    assert result["qualified_source_commit"] == head
    assert result["qualification_verdict"] == "PASS_B6H_TOPOLOGY_EVENT_COVERAGE_CLOSURE"
    assert result["topology_event_coverage_status"] == "PARTIAL_EVENT_COVERAGE_ONLY"
    assert result["composite_topology_positive_bound_years"] is None
    assert result["first_dt_readiness"] == "TOPOLOGY_MODEL_EXTENSION_REQUIRED"


def test_governed_t0_topology_inventory_is_rederived_without_mutation(b6h):
    inv = b6h["inventory"]
    assert (inv["node_count"], inv["triangle_count"], inv["plate_support_count"]) == (64442, 128880, 12)
    assert (inv["interface_count"], inv["unique_interface_identity_count"]) == (1983, 1983)
    assert (inv["plate_local_interface_side_count"], inv["unique_plate_local_side_identity_count"]) == (3966, 3966)
    assert inv["boundary_endpoint_references"] == 3966
    assert inv["unique_boundary_endpoint_node_count"] == 1973
    assert (inv["junction_relation_count"], inv["junction_side_count"]) == (20, 60)
    assert len(inv["junction_relations"]) == 20
    assert inv["distinct_adjacent_plate_pair_count"] == 30
    assert inv["source_mesh_sha256"] == "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad"
    safety = b6h["result"]["scientific_side_effect_check"]
    assert all(safety[key] is False for key in (
        "mechanics_authorized", "forward_evolution_authorized", "dt_selected", "t1_created",
        "canonical_state_changed", "canonical_node_motion_executed", "canonical_topology_mutated",
        "shellset_executed", "orbdata_mechanics_executed"))


def test_minimized_relevant_event_classes_have_explicit_noninvented_status(b6h):
    classes = {row["event_class"]: row for row in b6h["classes"]}
    assert len(classes) == 7
    assert classes["RELATION_DEGENERACY_REQUIRING_TOPOLOGY_CHANGE"]["classification"] == "NOT_RELEVANT_WITHIN_FROZEN_FIRST_SEGMENT_MODEL"
    relevant = b6h["relevant"]
    assert {row["event_class"] for row in relevant} == {
        "RIFT_PROCESS_ACTIVATION", "BOUNDARY_IDENTITY_SET_CHANGE",
        "INTERFACE_DECOMPOSITION_CHANGE", "JUNCTION_RELATION_CHANGE",
        "PLATE_SUPPORT_COMPONENT_CHANGE", "OTHER_UNENUMERATED_TOPOLOGY_TRANSITION",
    }
    assert all(row["detector_status"] != "QUALIFIED_EXISTING_DETECTOR"
               for row in relevant if row["event_class"] != "RIFT_PROCESS_ACTIVATION")
    assert all(row["first_event_horizon_computable"] is False
               for row in b6h["predicates"] if row["event_class"] != "RIFT_PROCESS_ACTIVATION")


def test_identity_delta_predicate_has_negative_and_synthetic_positive_cases():
    original = {"plates": ["P1", "P2"], "interfaces": ["I1"], "junctions": ["J1"]}
    assert topology_delta(original, {key: list(value) for key, value in original.items()})["changed"] is False
    changed = topology_delta(original, {"plates": ["P1", "P2"], "interfaces": ["I1", "I2"], "junctions": ["J1"]})
    assert changed["changed"] is True
    assert changed["changes"] == [
        {"entity": "interfaces", "added": ["I2"], "removed": []},
        {"entity": "junctions", "added": [], "removed": []},
        {"entity": "plates", "added": [], "removed": []},
    ]


def test_rift_horizon_is_included_once_and_edge_comparison_is_strictly_defined(b6h):
    assert rift_bound_reached(RIFT_YEARS - 1e-6) is False
    assert rift_bound_reached(RIFT_YEARS) is True
    assert rift_bound_reached(RIFT_YEARS + 1e-6) is True
    rift = b6h["rift"]
    assert rift["elapsed_years"] == RIFT_YEARS
    assert rift["limiting_pair_id"] == "1:3"
    assert rift["event_semantics"].startswith("RIFT_INITIATION")


def test_event_coverage_never_promotes_unknown_or_rift_bound_to_topology_window(b6h):
    table = b6h["coverage"]
    assert sum(row["positive_horizon_years"] is not None for row in table) == 1
    assert all(row["remaining_unknown"] is not None for row in table
               if row["event_class"] not in {"RIFT_PROCESS_ACTIVATION", "RELATION_DEGENERACY_REQUIRING_TOPOLOGY_CHANGE"})
    assert b6h["result"]["rift_event_bound_status"] == "QUALIFIED_EVENT_SPECIFIC_BOUND_NOT_TOPOLOGY_WINDOW"
    assert b6h["result"]["composite_topology_window_status"] == "NOT_COMPUTED_INCOMPLETE_EVENT_COVERAGE"


def test_input_authority_manifests_are_verified_and_no_ubuntu_work_is_needed(b6h):
    assert set(b6h["result"]["input_provenance"]["verified_stage_artifact_counts"]) == {"B5", "B6A", "B6D", "B6E", "B6F", "B6G"}
    assert b6h["result"]["execution_target"] == "WINDOWS"
    assert b6h["result"]["ubuntu_work_required"] is False

