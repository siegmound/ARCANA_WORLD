from __future__ import annotations

import pytest

from scripts.r6_b6g_targeted_validity_gap_closure import evaluate


@pytest.fixture(scope="module")
def b6g():
    return evaluate()


def test_b6g_is_descendant_safe_and_records_current_head(b6g):
    import subprocess

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    assert b6g["result"]["qualified_source_commit"] == head
    assert b6g["result"]["qualification_verdict"] == "PASS_B6G_TARGETED_VALIDITY_GAP_CLOSURE"


def test_full_governed_interface_relations_are_identity_paired(b6g):
    audit = b6g["relations"]
    assert audit["interface_count"] == 1983
    assert audit["unique_interface_id_count"] == 1983
    assert audit["unique_plate_local_side_id_count"] == 3966
    assert audit["interface_structural_identity_pass"] is True
    assert audit["interface_identity_pairing_failures"] == []
    assert audit["geometric_co_location_required"] is False
    motion = b6g["interface_motion"]
    assert motion["decomposed_count"] == 1983
    assert motion["missing_component_count"] == 0
    assert sum(motion["normal_component_counts"].values()) == 1983
    assert motion["normal_separation_semantics"].startswith("Separation does not erase")


def test_all_junctions_preserve_set_valued_incidence_without_owner(b6g):
    audit = b6g["relations"]
    assert audit["junction_relation_count"] == 20
    assert audit["junction_structural_incidence_pass"] is True
    assert audit["junction_incidence_failures"] == []
    assert audit["position_residual_or_velocity_allocation"].startswith("NOT_DEFINED")


def test_rigid_interior_numerical_caps_are_not_first_step_requirements(b6g):
    removed = set(b6g["result"]["false_numerical_blockers_removed"])
    assert "generic maximum rotation angle" in removed
    assert "displacement/interior-edge ratio threshold" in removed
    assert "interior triangle-quality/remesh threshold" in removed
    assert "interface co-location/gap threshold" in removed
    assert "junction single-coordinate/spread threshold" in removed


def test_topology_coverage_remains_partial_and_missing_detection_fails_closed(b6g):
    events = {row["event_class"]: row for row in b6g["events"]}
    assert events["conditional rift-process activation"]["status"] == "QUALIFIED_DETECTOR"
    assert events["conditional rift-process activation"]["positive_horizon_years"] == pytest.approx(27123.405156307464)
    assert events["other unenumerated topology transition"]["status"] == "CANNOT_EXCLUDE"
    assert b6g["result"]["topology_positive_window_status"] == "PARTIAL_EVENT_COVERAGE_ONLY"
    assert b6g["result"]["topology_positive_bound"] is None


def test_all_b6e_state_families_are_adjudicated_and_async_values_preserved(b6g):
    assert len(b6g["state"]) == 15
    assert len({row["state_family"] for row in b6g["state"]}) == 15
    assert b6g["result"]["blocking_state_families"] == []
    assert all(row["first_step_update_required"] is False for row in b6g["state"])
    assert all(row["latest_valid_state_retained"] for row in b6g["state"]
               if row["first_step_classification"] == "ASYNC_RETAINS_LATEST_VALID_STATE")
    assert len(b6g["required_transfers"]) == 1
    assert b6g["required_transfers"][0]["execution_performed"] is False


def test_system_memory_is_retained_and_only_rift_bound_is_reported_not_dt(b6g):
    result = b6g["result"]
    assert len(b6g["memory"]) == 5
    assert result["blocking_memory_classes"] == []
    assert result["qualified_bound_count"] == 1
    assert result["qualified_bounds"][0]["bound_id"] == "B6G_CONDITIONAL_RIFT_ACTIVATION_HORIZON"
    assert result["qualified_bounds"][0]["not_a_dt"] is True
    assert result["current_smallest_qualified_bound_not_a_dt"]["not_a_global_topology_bound"] is True
    assert result["first_dt_readiness"] == "NOT_READY_FOR_FIRST_DT_ADJUDICATION"
    assert result["scientific_side_effect_check"]["dt_selected"] is False
    assert result["scientific_side_effect_check"]["canonical_state_changed"] is False
