import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_activation_contract_does_not_mean_structural_transition():
    contract = _json("contracts/R6_RIFT_PROCESS_ACTIVATION_MODEL_V1.json")
    assert contract["activation_semantics"]["successor_process_state"] == "RIFT_PROCESS_ACTIVE"
    assert "TOPOLOGY_SPLIT_COMPLETED" in contract["activation_semantics"]["not_equivalent_to"]
    assert contract["instantaneous_transition"]["physical_duration"] == 0
    assert contract["instantaneous_transition"]["existing_plate_split"] is False


def test_post_event_kinematics_are_restricted_and_source_support_is_instant_only():
    contract = _json("contracts/R6_POST_EVENT_KINEMATIC_AUTHORITY_V1.json")
    assert contract["status"] == "POST_EVENT_KINEMATIC_AUTHORITY_CONTINUES_WITH_RESTRICTED_SCOPE"
    assert contract["temporal_scope"]["source_temporal_support"] == "INSTANT_ONLY"
    assert contract["temporal_scope"]["source_interval_beyond_anchor"].startswith("UNKNOWN")
    assert contract["applicable_scope"]["kinematics"] == "PLATE_LOCAL_RIGID_KINEMATICS"
    assert "does not" in contract["applicable_scope"]["plate_pair_1_3"]


def test_model_scope_horizon_is_not_a_structural_event_bound():
    contract = _json("contracts/R6_POST_EVENT_KINEMATIC_REVALIDATION_HORIZON_V1.json")
    assert contract["horizon_class"] == "MODEL_SCOPE_REVALIDATION"
    assert contract["derivation"]["horizon_delta_years"] == 8214.051909111062
    assert "not a predicted time to a geological event" in contract["scientific_meaning"]
    assert "not proof of an event-free interval" in contract["scientific_meaning"]


def test_b6n4r1_blockers_remain_four_distinct_dependencies():
    attestation = _json("docs/arcana/qualifications/R6_B6N4R1_ATTESTATION.json")
    blocker_ids = {item["dependency"] for item in attestation["four_relevant_blockers"]}
    assert blocker_ids == {
        "NEXT_RIFT_PROCESS_EVOLUTION",
        "GENERIC_TOPOLOGY_EVENT_COVERAGE",
        "PLATE_INTERFACE_EVENT_PREDICATES",
        "SUPPORT_MEMBERSHIP_VALIDITY",
    }
    assert "does **not** prove" in (
        ROOT / "docs/arcana/B6N5_POST_RIFT_STRUCTURAL_TRANSITION_AUTHORITY.md"
    ).read_text(encoding="utf-8").lower()


def test_existing_event_predicates_do_not_cover_future_topology_transitions():
    predicates = _json("outputs/r6_b6h_topology_event_coverage_closure/B6H_EVENT_PREDICATES.json")["predicates"]
    by_class = {item["event_class"]: item for item in predicates}
    assert by_class["RIFT_PROCESS_ACTIVATION"]["first_event_horizon_computable"] is True
    for event_class in (
        "BOUNDARY_IDENTITY_SET_CHANGE",
        "INTERFACE_DECOMPOSITION_CHANGE",
        "JUNCTION_RELATION_CHANGE",
        "PLATE_SUPPORT_COMPONENT_CHANGE",
        "OTHER_UNENUMERATED_TOPOLOGY_TRANSITION",
    ):
        assert by_class[event_class]["first_event_horizon_computable"] is False


def test_no_transition_authority_or_mechanics_is_inferred():
    attestation = _json("docs/arcana/qualifications/R6_B6N4R1_ATTESTATION.json")
    dt_gate = _json("contracts/R6_SECOND_DT_AUTHORIZATION_AFTER_RIFT_V1.json")
    assert attestation["authorization"]["authorizes_mechanics"] is False
    assert attestation["authorization"]["authorizes_topology_transition"] is False
    assert attestation["decision_state"]["mechanics_executed"] is False
    assert attestation["decision_state"]["forward_propagation_executed"] is False
    assert dt_gate["second_dt_authorized_by_this_contract"] is False
    assert dt_gate["dt2_value"] is None
    assert dt_gate["t2_creation_authorized"] is False


def test_historical_deterministic_replay_evidence_and_b6n5_decision_are_preserved():
    attestation = _json("docs/arcana/qualifications/R6_B6N4R1_ATTESTATION.json")
    replay = attestation["qualification_validation"]["deterministic_runner_replay"]
    assert replay.startswith("PASS; two invocations produced identical JSON")
    report = (ROOT / "docs/arcana/B6N5_POST_RIFT_STRUCTURAL_TRANSITION_AUTHORITY.md").read_text(
        encoding="utf-8"
    )
    assert "BLOCKED_B6N5_INSUFFICIENT_STRUCTURAL_TRANSITION_AUTHORITY" in report
    assert "UNKNOWN" in report
    assert "27123.405156307464" in report
    assert "SECOND_DT_SELECTED=false" in report
    assert "T2_CREATED=false" in report
