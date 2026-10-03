from __future__ import annotations

import json
import subprocess

import pytest

from scripts.r6_b6j_first_dt_adjudication import (
    active_qualified_bounds,
    decide_endpoint,
    evaluate,
    normalize_years,
    select_limiting_bound,
)


@pytest.fixture(scope="module")
def b6j():
    return evaluate()


def test_active_constraint_filtering_and_no_false_numeric_blocker(b6j):
    rows = b6j["active"]["constraints"]
    assert len(rows) == b6j["active"]["candidate_constraint_count"]
    assert len(b6j["active"]["active_constraints"]) == b6j["result"]["active_constraint_count"] == 2
    assert {row["status"] for row in b6j["active"]["active_constraints"]} == {
        "ACTIVE_QUALIFIED_BOUND", "ACTIVE_NONNUMERIC_CONDITION"}
    assert [row["constraint_id"] for row in rows if row["status"] == "ACTIVE_QUALIFIED_BOUND"] == ["FIRST_SEGMENT_TOPOLOGY_VALIDITY"]
    assert not any(row["status"] == "BLOCKING_UNKNOWN" for row in rows)
    assert next(row for row in rows if row["constraint_id"] == "MECHANICS_SOLVER_STABILITY")["status"] == "NOT_APPLICABLE"
    bounds = active_qualified_bounds(rows, b6j["bounds"]["bounds"])
    assert [row["bound_id"] for row in bounds] == [b6j["result"]["limiting_constraint"]]


def test_bound_units_and_minimum_selection_are_deterministic():
    assert normalize_years(27.123405156307464, "kyr") == 27123.405156307464
    selected = select_limiting_bound([
        {"bound_id": "later", "value": 30, "unit": "kyr"},
        {"bound_id": "earlier", "value": 20_000, "unit": "year"},
    ])
    assert selected["bound_id"] == "earlier"
    with pytest.raises(ValueError, match="unsupported temporal unit"):
        normalize_years(1, "fortnight")


def test_exactly_one_qualified_finite_bound_and_horizon_provenance(b6j):
    assert b6j["bounds"]["finite_active_bound_count"] == 1
    assert b6j["bounds"]["hidden_smaller_qualified_bound"] is False
    row = b6j["bounds"]["bounds"][0]
    assert row["value_years"] == 27123.405156307464
    assert row["limiting_entity"] == "plate pair 1:3"
    assert row["authority"].startswith("B6A Census V3")
    assert [item["stage"] for item in b6j["bounds"]["cross_stage_bound_verification"]] == ["B6F", "B6G", "B6H", "B6I"]
    assert all(item["value_years"] == row["value_years"] for item in b6j["bounds"]["cross_stage_bound_verification"])


def test_rift_equality_semantics_and_event_aligned_endpoint(b6j):
    assert b6j["strictness"]["predicate_satisfied_at_equality"] is True
    assert b6j["strictness"]["activation_becomes_possible_at_equality"] is True
    assert b6j["strictness"]["actual_event_created"] is False
    assert b6j["strictness"]["interval"] == "0 <= t < horizon"
    assert b6j["strictness"]["no_accepted_segment_crosses"] is True
    assert b6j["endpoint"]["status"] == "EVENT_ALIGNED_ENDPOINT_AUTHORIZED"
    assert b6j["endpoint"]["topology_mutation_during_step"] is False
    assert b6j["strictness"]["numeric_tolerance"].startswith("NONE_FOR_ANALYTIC_BOUND_SELECTION")


def test_ambiguous_endpoint_semantics_fail_closed():
    with pytest.raises(ValueError, match="explicit booleans"):
        decide_endpoint(interval_open_at_horizon=None, capture_boundary_authorized=True,
                        event_at_equality=True)
    assert decide_endpoint(interval_open_at_horizon=True, capture_boundary_authorized=False,
                           event_at_equality=True) == "STRICT_PRE_EVENT_ENDPOINT_REQUIRED"
    assert decide_endpoint(interval_open_at_horizon=False, capture_boundary_authorized=True,
                           event_at_equality=False) == "ENDPOINT_POLICY_BLOCKED"


def test_dt_and_geological_age_sign_precision(b6j):
    result = b6j["result"]
    assert result["first_dt_selection_status"] == "FIRST_DT_SELECTED"
    assert result["first_dt_value"] == 27123.405156307464
    assert result["source_age_ma"] == 210.0
    assert result["target_age_ma"] == 209.97287659484368
    assert result["target_age_ma"] < result["source_age_ma"]
    assert b6j["dt"]["numeric_representation"]["hex"] == float(result["first_dt_value"]).hex()


def test_event_boundary_is_contract_only_and_transition_is_not_executed(b6j):
    event = b6j["event"]
    assert event["status"] == "EVENT_BOUNDARY_CONTRACT_DEFINED_NOT_EVENT_CREATED"
    assert event["event_class"] == "RIFT_PROCESS_ACTIVATION"
    assert event["pre_event_topology_identity"] == "GOVERNED_T0_TOPOLOGY"
    assert event["transition_status"] == "NOT_EXECUTED"
    assert b6j["result"]["rift_transition_executed"] is False


def test_dt_provenance_and_replay_selection_are_closed(b6j):
    assert b6j["provenance"]["status"] == "WHY_PROVENANCE_SPECIFIED"
    assert b6j["provenance"]["numeric_tolerance"].startswith("NONE_ADDED")
    assert b6j["provenance"]["future_solver_tolerance"].startswith("UNSELECTED")
    assert b6j["replay"]["status"] == "PASS_DETERMINISTIC_SELECTION_REPLAY"
    assert "wall clock" in b6j["replay"]["excluded_inputs"]


def test_current_revision_is_qualified_without_rewriting_b6i_history(b6j):
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    assert b6j["result"]["qualified_source_commit"] == head
    assert b6j["result"]["qualified_prior_stage_source_commit"] == "a3d351b0abf8231308a8394feadf9480794dc0ea"
    assert b6j["result"]["qualified_prior_stage_source_commit"] != head


def test_no_candidate_t1_node_motion_topology_or_scientific_runtime_side_effect(b6j):
    result = b6j["result"]
    assert result["dt_selected"] is True
    assert result["t1_created"] is False
    assert result["canonical_state_changed"] is False
    assert result["canonical_node_motion_executed"] is False
    assert result["canonical_topology_mutated"] is False
    assert result["mechanics_authorized"] is False
    assert result["forward_evolution_authorized"] is False
    assert result["shellset_executed"] is False
    assert result["orbdata_mechanics_executed"] is False


def test_serialized_evidence_is_path_independent_and_valid_json(b6j):
    encoded = json.dumps(b6j["dt"], sort_keys=True, separators=(",", ":"))
    assert "F:\\" not in encoded
    assert "Users\\" not in encoded
    assert json.loads(encoded)["value"] == b6j["result"]["first_dt_value"]


def test_independent_reconstruction_replays_identical_dt_event_and_age():
    first = evaluate()
    second = evaluate()
    fields = ("dt", "age", "event", "endpoint", "provenance")
    encode = lambda result: json.dumps({key: result[key] for key in fields}, sort_keys=True,
                                       separators=(",", ":"), allow_nan=False)
    assert encode(first) == encode(second)

