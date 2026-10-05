from __future__ import annotations

import pytest

from scripts.r6_b6n4r1_second_timestep_readjudication import (
    evaluate_dependency_closure,
    select_nearest_positive_limiter,
)


def _dep(identifier: str, **changes):
    row = {
        "id": identifier,
        "scope_role": "REQUIRED_FOR_REQUESTED_OUTPUT",
        "authority_status": "AUTHORIZED",
        "impact_bound_status": "BOUNDED",
        "dependency_status": "CLOSED",
    }
    row.update(changes)
    return row


def test_dependency_closure_is_deterministic_and_unknown_impact_blocks() -> None:
    rows = [
        _dep("bounded", positive_validity_years=8214.0),
        _dep("unknown-event", impact_bound_status="UNKNOWN", dependency_status="NOT_PROVEN"),
    ]
    first = evaluate_dependency_closure(rows, 8214.0)
    second = evaluate_dependency_closure(list(reversed(rows)), 8214.0)
    assert first == second
    assert first["status"] == "BLOCKED_RELEVANT_AUTHORITY_UNRESOLVED"
    assert first["blocking_dependencies"] == [
        {"dependency": "unknown-event", "reason": "IMPACT_BOUND_UNRESOLVED"}
    ]
    assert first["SECOND_DT_SELECTED"] is False
    assert first["dt2_years"] is None


def test_not_applicable_mechanics_does_not_block_requested_scope() -> None:
    mechanics = _dep(
        "MECHANICS_REQUIREMENT",
        scope_role="NOT_APPLICABLE_TO_REQUESTED_OUTPUT",
        authority_status="NOT_REQUIRED",
        impact_bound_status="NOT_APPLICABLE",
    )
    limiter = [{"horizon_id": "model-cap", "delta_time_years": 10.0, "authorized": True}]
    result = evaluate_dependency_closure([mechanics], 10.0, limiter)
    assert result["status"] == "AUTHORIZED_POSITIVE_PROPAGATION"
    assert result["positive_propagation_established"] is True
    assert result["nearest_authorized_limiter"]["horizon_id"] == "model-cap"
    assert result["SECOND_DT_SELECTED"] is False
    assert result["T2_CREATED"] is False


def test_authority_block_cannot_be_waived_by_small_or_bounded_impact() -> None:
    rift = _dep("NEXT_RIFT_PROCESS_EVOLUTION", authority_status="NOT_AUTHORIZED")
    result = evaluate_dependency_closure([rift], 8214.0)
    assert result["blocking_dependencies"] == [
        {"dependency": "NEXT_RIFT_PROCESS_EVOLUTION", "reason": "AUTHORITY_NOT_AUTHORIZED"}
    ]


def test_source_provenance_is_distinct_from_successor_model_authority() -> None:
    source = _dep(
        "SOURCE_TEMPORAL_VALIDITY",
        scope_role="SOURCE_PROVENANCE_NOT_EXTENDED",
        authority_status="UNKNOWN",
        impact_bound_status="UNKNOWN",
    )
    successor = _dep("B6N2_SUCCESSOR_MODEL", positive_validity_years=8214.0)
    limiter = [{"horizon_id": "B6N3A_MODEL_SCOPE_CAP", "delta_time_years": 8214.0, "authorized": True}]
    result = evaluate_dependency_closure([source, successor], 8214.0, limiter)
    assert result["status"] == "AUTHORIZED_POSITIVE_PROPAGATION"
    assert result["SECOND_DT_SELECTED"] is False


def test_unknown_is_not_relabelled_absent_and_isolation_must_be_explicit() -> None:
    unknown = _dep(
        "PLATE_INTERFACE_EVENT_PREDICATES",
        impact_bound_status="UNKNOWN",
        dependency_status="NOT_PROVEN",
        event_occurrence="UNKNOWN",
    )
    result = evaluate_dependency_closure([unknown], 8214.0)
    assert unknown["event_occurrence"] == "UNKNOWN"
    assert result["status"] == "BLOCKED_RELEVANT_AUTHORITY_UNRESOLVED"
    assert not result["positive_propagation_established"]


def test_unproven_dependency_is_not_treated_as_isolated_scope() -> None:
    candidate = _dep("topology-event", impact_bound_status="BOUNDED",
                     dependency_status="NOT_PROVEN")
    result = evaluate_dependency_closure([candidate], 8214.0)
    assert result["blocking_dependencies"] == [
        {"dependency": "topology-event", "reason": "DEPENDENCY_CLOSURE_NOT_PROVEN"}
    ]


def test_nearest_limiter_selection_is_deterministic_and_requires_positive_authority() -> None:
    candidates = [
        {"horizon_id": "later", "delta_time_years": 12.0, "authorized": True},
        {"horizon_id": "ignored-unknown", "delta_time_years": 2.0, "authorized": False},
        {"horizon_id": "earlier", "delta_time_years": 4.0, "authorized": True},
        {"horizon_id": "zero", "delta_time_years": 0.0, "authorized": True},
    ]
    assert select_nearest_positive_limiter(candidates) == select_nearest_positive_limiter(list(reversed(candidates)))
    assert select_nearest_positive_limiter(candidates)["horizon_id"] == "earlier"
    assert select_nearest_positive_limiter([]) is None


def test_nonpositive_model_scope_limit_fails_closed() -> None:
    with pytest.raises(ValueError, match="positive duration"):
        evaluate_dependency_closure([], 0.0)


def test_current_closure_preserves_the_four_global_blockers() -> None:
    dependencies = [
        _dep("GENERIC_TOPOLOGY_EVENT_COVERAGE", impact_bound_status="UNKNOWN",
             dependency_status="NOT_PROVEN", event_occurrence="UNKNOWN"),
        _dep("JUNCTION_CONSISTENCY", scope_role="RELEVANT_NON_LIMITING_FOR_REQUESTED_OUTPUT",
             impact_bound_status="UNKNOWN", dependency_status="NOT_PROVEN", event_occurrence=None),
        _dep("MECHANICS_REQUIREMENT", scope_role="NOT_APPLICABLE_TO_REQUESTED_OUTPUT",
             authority_status="NOT_REQUIRED", impact_bound_status="NOT_APPLICABLE"),
        _dep("NEXT_RIFT_PROCESS_EVOLUTION", authority_status="NOT_AUTHORIZED",
             impact_bound_status="UNKNOWN", dependency_status="NOT_PROVEN", event_occurrence="UNKNOWN"),
        _dep("PLATE_INTERFACE_EVENT_PREDICATES", impact_bound_status="UNKNOWN",
             dependency_status="NOT_PROVEN", event_occurrence="UNKNOWN"),
        _dep("SOURCE_TEMPORAL_VALIDITY", scope_role="SOURCE_PROVENANCE_NOT_EXTENDED",
             authority_status="UNKNOWN", impact_bound_status="UNKNOWN", event_occurrence=None),
        _dep("SUPPORT_MEMBERSHIP_VALIDITY", impact_bound_status="UNKNOWN",
             dependency_status="NOT_PROVEN", event_occurrence=None),
        _dep("SUCCESSOR_MODEL_SCOPE_REVALIDATION",
             scope_role="AUTHORIZED_FINITE_UPPER_BOUND_CANDIDATE",
             positive_validity_years=8214.051909111062),
        _dep("ASYNC_DOMAIN_VALIDITY", scope_role="NOT_APPLICABLE_TO_TECTONIC_KINEMATIC_OUTPUT",
             authority_status="NOT_REQUIRED", impact_bound_status="NOT_APPLICABLE"),
        _dep("RIGID_ROTATION_NUMERICAL_STABILITY", scope_role="NOT_APPLICABLE_NO_GOVERNED_LIMIT",
             authority_status="NOT_REQUIRED", impact_bound_status="NOT_APPLICABLE"),
    ]
    result = evaluate_dependency_closure(dependencies, 8214.051909111062)
    assert result["status"] == "BLOCKED_RELEVANT_AUTHORITY_UNRESOLVED"
    assert result["blocking_dependencies"] == [
        {"dependency": "GENERIC_TOPOLOGY_EVENT_COVERAGE", "reason": "IMPACT_BOUND_UNRESOLVED"},
        {"dependency": "NEXT_RIFT_PROCESS_EVOLUTION", "reason": "AUTHORITY_NOT_AUTHORIZED"},
        {"dependency": "PLATE_INTERFACE_EVENT_PREDICATES", "reason": "IMPACT_BOUND_UNRESOLVED"},
        {"dependency": "SUPPORT_MEMBERSHIP_VALIDITY", "reason": "IMPACT_BOUND_UNRESOLVED"},
    ]
    assert dependencies[0]["event_occurrence"] == "UNKNOWN"
    assert result["positive_propagation_established"] is False
    assert result["nearest_authorized_limiter"] is None
    assert result["SECOND_DT_SELECTED"] is False
    assert result["dt2_years"] is None
    assert result["target_age_ma"] is None
    assert result["T2_CREATED"] is False

