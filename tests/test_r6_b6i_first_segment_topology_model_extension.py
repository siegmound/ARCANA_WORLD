from __future__ import annotations

import subprocess

import pytest

from arcana_worldsim.r6.topology_process_registry import (
    EventQueryStatus,
    FirstSegmentStatus,
    FIRST_SEGMENT_REGISTRY,
    RIFT_ACTIVATION_HORIZON_YEARS,
    UnknownTopologyEventError,
    registry_as_dict,
)
from scripts.r6_b6i_first_segment_topology_model_extension import evaluate


@pytest.fixture(scope="module")
def b6i():
    return evaluate()


def test_b6i_is_descendant_safe_and_qualifies_current_commit(b6i):
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    assert b6i["result"]["qualified_source_commit"] == head
    assert b6i["result"]["qualification_verdict"] == "PASS_B6I_FIRST_SEGMENT_TOPOLOGY_MODEL_EXTENSION"


def test_only_rift_process_is_enabled_and_known_nonrift_classes_are_out_of_scope():
    registry = registry_as_dict()
    rows = registry["processes"]
    assert [row["event_class"] for row in rows if row["first_segment_status"] == "ENABLED"] == ["RIFT_PROCESS_ACTIVATION"]
    assert [row["event_class"] for row in rows if row["first_segment_status"] == "DERIVED_FROM_ENABLED_EVENT"] == ["RIFT_ACTIVATION_BOUNDARY_TOPOLOGY_TRANSITION"]
    out = {row["event_class"] for row in rows if row["first_segment_status"] == "OUT_OF_SCOPE_FOR_FIRST_SEGMENT_MODEL"}
    assert {"BOUNDARY_DEATH", "INTERFACE_SPLIT", "INTERFACE_MERGE", "JUNCTION_BIRTH",
            "JUNCTION_DEATH", "JUNCTION_CONNECTIVITY_CHANGE", "PLATE_SUPPORT_SPLIT",
            "PLATE_SUPPORT_MERGE", "OTHER_NON_RIFT_TOPOLOGY_MUTATION"} <= out
    assert all(row["first_segment_status"] in {item.value for item in FirstSegmentStatus} for row in rows)


def test_unknown_event_classes_fail_closed_instead_of_defaulting_enabled():
    with pytest.raises(UnknownTopologyEventError):
        FIRST_SEGMENT_REGISTRY.get("UNREGISTERED_NEW_EVENT")
    with pytest.raises(UnknownTopologyEventError):
        FIRST_SEGMENT_REGISTRY.classify_observation("UNREGISTERED_NEW_EVENT", False)


def test_topology_hold_is_valid_before_but_not_at_or_after_enabled_event():
    assert FIRST_SEGMENT_REGISTRY.topology_hold_applies(0.0)
    assert FIRST_SEGMENT_REGISTRY.topology_hold_applies(RIFT_ACTIVATION_HORIZON_YEARS - 1e-6)
    assert not FIRST_SEGMENT_REGISTRY.topology_hold_applies(RIFT_ACTIVATION_HORIZON_YEARS)
    assert not FIRST_SEGMENT_REGISTRY.topology_hold_applies(RIFT_ACTIVATION_HORIZON_YEARS + 1e-6)
    with pytest.raises(ValueError):
        FIRST_SEGMENT_REGISTRY.topology_hold_applies(-1.0)


def test_query_distinguishes_model_scope_from_evaluated_nonoccurrence():
    registry = FIRST_SEGMENT_REGISTRY
    assert registry.classify_observation("RIFT_PROCESS_ACTIVATION", False) is EventQueryStatus.EVENT_DID_NOT_OCCUR
    assert registry.classify_observation("RIFT_PROCESS_ACTIVATION", None) is EventQueryStatus.UNKNOWN
    assert registry.classify_observation("INTERFACE_SPLIT", False) is EventQueryStatus.MODEL_SCOPE_LIMITATION
    assert registry.classify_observation("BOUNDARY_DEATH", True) is EventQueryStatus.MODEL_SCOPE_LIMITATION


def test_qualified_rift_horizon_keeps_authority_pair_and_model_scope(b6i):
    bound = b6i["topology_bound"]
    assert bound["status"] == "FIRST_SEGMENT_POSITIVE_TOPOLOGY_BOUND_QUALIFIED"
    assert bound["value"] == RIFT_ACTIVATION_HORIZON_YEARS
    assert bound["limiting_entity_pair"] == "1:3"
    assert bound["not_a_dt"] is True
    assert bound["transition_executed"] is False
    assert "not a claim of physical impossibility" in bound["model_scope_limitation"]
    assert b6i["bound"]["integration_count"] == 1


def test_registry_and_evaluation_do_not_mutate_topology_or_select_dt(b6i):
    result = b6i["result"]
    assert result["first_dt_readiness"] == "READY_FOR_FIRST_DT_ADJUDICATION"
    gates = result["scientific_side_effect_check"]
    assert gates["dt_selected"] is False
    assert gates["t1_created"] is False
    assert gates["canonical_state_changed"] is False
    assert gates["canonical_topology_mutated"] is False
    assert gates["rift_transition_executed"] is False
    assert gates["mechanics_authorized"] is False
    assert gates["forward_evolution_authorized"] is False


def test_future_extension_requires_explicit_authority_and_query_replay_compatibility(b6i):
    required = b6i["extension_contract"]["promotion_requires"]
    assert required == ["explicit model addition", "event predicate", "authority/provenance",
                        "detector/horizon qualification where required", "regression against existing history semantics",
                        "query/replay compatibility"]
    assert b6i["extension_contract"]["no_implicit_promotion"] is True


def test_b5_through_b6h_manifests_are_verified_before_qualification(b6i):
    counts = b6i["result"]["input_provenance"]["verified_stage_artifact_counts"]
    assert set(counts) == {"B5", "B6A", "B6D", "B6E", "B6F", "B6G", "B6H"}
    assert b6i["result"]["execution_target"] == "WINDOWS"
    assert b6i["result"]["ubuntu_work_required"] is False
