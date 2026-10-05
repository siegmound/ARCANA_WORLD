from __future__ import annotations

from dataclasses import replace

import pytest

from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.event_impact import (
    DIMENSIONS,
    AuthorityClass,
    AuthorityStatus,
    DependencyStatus,
    EventImpactAssessment,
    EventOccurrence,
    ImpactBoundStatus,
    PropagationScope,
    ResolutionRelation,
    SignificanceClass,
    adjudicate_event_impact,
)
from arcana_worldsim.r6.identity import BranchId, HistoryId, content_hash
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.replay import ReplayExecutionOutput, ReplayRecipe, execute_replay
from arcana_worldsim.r6.state import (
    AuthorityClass as StateAuthorityClass,
    DomainStateEnvelope,
    SpatialSupport,
    SupportClass,
    TimeSupport,
)
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.temporal import EventRecord


HISTORY = str(HistoryId.from_payload({"fixture": "b6n4a-event-impact"}))
BRANCH = str(BranchId.from_payload({"fixture": "b6n4a-branch"}))


def assessment(**changes) -> EventImpactAssessment:
    dimensions = {key: ResolutionRelation.BELOW_REPRESENTED_RESOLUTION for key in DIMENSIONS}
    evidence = {key: "fixture-only governed relation" for key in DIMENSIONS}
    values = {
        "subject_id": "fixture-event-1",
        "subject_kind": "PHYSICAL_EVENT",
        "authority_class": AuthorityClass.PHYSICAL_EVENT_UNCERTAINTY,
        "authority_status": AuthorityStatus.AUTHORIZED,
        "authority_basis": "fixture authority reference",
        "occurrence": EventOccurrence.UNKNOWN,
        "impact_bound_status": ImpactBoundStatus.BOUNDED,
        "dimension_relations": dimensions,
        "dimension_evidence": evidence,
        "spatial_resolution": "FIXTURE_GRID_10KM",
        "temporal_resolution": "FIXTURE_ANNUAL",
        "represented_domains": ("tectonic_geometry",),
        "requested_outputs": ("tectonic_geometry",),
        "affected_domains": ("tectonic_geometry",),
        "authority_scope": PropagationScope.REGIONAL,
        "impact_scope": PropagationScope.LOCAL,
        "dependency_status": DependencyStatus.ISOLATION_PROVEN,
        "resolution_context_id": "fixture-resolution-v1",
    }
    values.update(changes)
    return EventImpactAssessment(**values)


def test_unknown_occurrence_below_all_dimensions_is_not_no_event() -> None:
    result = adjudicate_event_impact(assessment())
    assert result["significance_class"] == SignificanceClass.SUBRESOLUTION_UNKNOWN.value
    assert result["event_occurrence_remains"] == "UNKNOWN"
    assert result["event_absence_asserted"] is False
    assert result["state_action"] == "EVENT_LEDGER_OR_ADJUDICATION_EVIDENCE_ONLY; NO_STATE_OR_CHECKPOINT"
    assert result["current_scope_crossing_policy"] == (
        "NO_STATE_BOUNDARY_REQUIRED_AT_DECLARED_RESOLUTION_IF_OTHER_AUTHORITIES_ALLOW")
    assert result["policy_authorizes_propagation"] is False


def test_unknown_event_and_unknown_impact_bound_are_separate() -> None:
    candidate = assessment(impact_bound_status=ImpactBoundStatus.UNKNOWN)
    candidate.dimension_relations["spatial_footprint"] = ResolutionRelation.UNKNOWN
    result = adjudicate_event_impact(candidate)
    assert result["event_occurrence_remains"] == "UNKNOWN"
    assert result["significance_class"] == SignificanceClass.INSUFFICIENT_IMPACT_BOUND.value
    assert result["blocking_scope"] == PropagationScope.LOCAL.value


def test_source_authority_limit_cannot_be_bypassed_by_subresolution_impact() -> None:
    result = adjudicate_event_impact(assessment(
        authority_class=AuthorityClass.SOURCE_AUTHORITY_LIMIT,
        authority_status=AuthorityStatus.UNKNOWN,
        authority_basis=None,
        authority_scope=PropagationScope.SYSTEMIC,
    ))
    assert result["significance_class"] == SignificanceClass.AUTHORITY_BLOCKED.value
    assert result["blocking_scope"] == PropagationScope.SYSTEMIC.value
    assert result["policy_authorizes_propagation"] is False


def test_local_impact_does_not_automatically_block_global_scope() -> None:
    result = adjudicate_event_impact(assessment(
        occurrence=EventOccurrence.OCCURRED,
        dimension_relations={key: ResolutionRelation.STATE_SIGNIFICANT_AT_REPRESENTED_RESOLUTION
                             for key in DIMENSIONS},
        impact_scope=PropagationScope.LOCAL,
        dependency_status=DependencyStatus.CLOSED,
    ))
    assert result["significance_class"] == SignificanceClass.LOCAL_CHECKPOINT_REQUIRED.value
    assert result["blocking_scope"] == PropagationScope.LOCAL.value
    assert result["unaffected_scopes_potentially_eligible"] is False


def test_local_unknown_only_isolates_when_dependency_graph_proves_it() -> None:
    significant = {key: ResolutionRelation.STATE_SIGNIFICANT_AT_REPRESENTED_RESOLUTION
                   for key in DIMENSIONS}
    unproven = adjudicate_event_impact(assessment(
        dimension_relations=significant, dependency_status=DependencyStatus.NOT_PROVEN))
    isolated = adjudicate_event_impact(assessment(
        dimension_relations=significant, dependency_status=DependencyStatus.ISOLATION_PROVEN))
    assert unproven["significance_class"] == SignificanceClass.INSUFFICIENT_IMPACT_BOUND.value
    assert unproven["blocking_scope"] == PropagationScope.GLOBAL.value
    assert isolated["significance_class"] == SignificanceClass.LOCAL_REFINEMENT_UNKNOWN.value
    assert isolated["blocking_scope"] == PropagationScope.LOCAL.value
    assert isolated["unaffected_scopes_potentially_eligible"] is True
    assert isolated["policy_authorizes_propagation"] is False


def test_significance_is_relative_to_resolution_context() -> None:
    coarse = adjudicate_event_impact(assessment())
    fine_relations = {key: ResolutionRelation.BELOW_REPRESENTED_RESOLUTION for key in DIMENSIONS}
    fine_relations["spatial_footprint"] = ResolutionRelation.STATE_SIGNIFICANT_AT_REPRESENTED_RESOLUTION
    fine = adjudicate_event_impact(assessment(
        dimension_relations=fine_relations,
        spatial_resolution="FIXTURE_GRID_100M",
        resolution_context_id="fixture-resolution-fine-v1",
    ))
    assert coarse["significance_class"] == SignificanceClass.SUBRESOLUTION_UNKNOWN.value
    assert fine["significance_class"] == SignificanceClass.LOCAL_REFINEMENT_UNKNOWN.value
    assert coarse["event_occurrence_remains"] == fine["event_occurrence_remains"] == "UNKNOWN"


def test_event_only_creates_no_state_or_checkpoint_and_systemic_event_does() -> None:
    event_only = adjudicate_event_impact(assessment(occurrence=EventOccurrence.OCCURRED))
    systemic = adjudicate_event_impact(assessment(
        occurrence=EventOccurrence.OCCURRED,
        dimension_relations={key: ResolutionRelation.STATE_SIGNIFICANT_AT_REPRESENTED_RESOLUTION
                             for key in DIMENSIONS},
        impact_scope=PropagationScope.SYSTEMIC,
        authority_scope=PropagationScope.SYSTEMIC,
        dependency_status=DependencyStatus.CLOSED,
    ))
    assert event_only["significance_class"] == SignificanceClass.EVENT_ONLY.value
    assert event_only["state_action"] == "EVENT_LEDGER_ONLY; NO_STATE_OR_CHECKPOINT"
    assert systemic["significance_class"] == SignificanceClass.SYSTEMIC_STATE_REQUIRED.value
    assert systemic["state_action"] == "SYSTEMIC_CAUSAL_STATE_BOUNDARY_REQUIRED"


def test_every_significance_dimension_requires_evidence() -> None:
    rows = {key: ResolutionRelation.BELOW_REPRESENTED_RESOLUTION for key in DIMENSIONS}
    rows.pop("topology_impact")
    with pytest.raises(ValueError, match="every significance dimension"):
        assessment(dimension_relations=rows)


def test_adjudication_replay_is_deterministic() -> None:
    item = assessment()
    assert adjudicate_event_impact(item) == adjudicate_event_impact(item)


def test_non_event_scope_is_not_coerced_to_unknown_occurrence() -> None:
    result = adjudicate_event_impact(assessment(
        subject_id="mechanics-not-requested",
        subject_kind="MECHANICS_SCOPE_HORIZON",
        authority_class=AuthorityClass.MECHANICS_SCOPE_LIMIT,
        occurrence=None,
        impact_bound_status=ImpactBoundStatus.NOT_APPLICABLE,
        dimension_relations={key: ResolutionRelation.NOT_APPLICABLE for key in DIMENSIONS},
        dimension_evidence={key: "mechanics output is outside this geometry-only request"
                            for key in DIMENSIONS},
        requested_outputs=("restricted_geometry_only_kinematics",),
        affected_domains=("mechanics",),
        authority_scope=PropagationScope.NONE,
        impact_scope=PropagationScope.NONE,
        dependency_status=DependencyStatus.CLOSED,
    ))
    assert result["assessment"]["event_occurrence"] is None
    assert result["event_occurrence_remains"] is None
    assert result["significance_class"] == SignificanceClass.NOT_APPLICABLE.value
    assert result["current_scope_crossing_policy"] == "NOT_APPLICABLE_TO_REQUESTED_SCOPE"
    assert result["event_absence_asserted"] is False


def test_unknown_state_and_event_survive_store_query_and_replay(tmp_path) -> None:
    store = HistoryStore(tmp_path / "history")
    time = TimeSupport("210Ma", "R6_GLOBAL_MA_OLDER_TO_YOUNGER")
    space = SpatialSupport(None, (), "fixture", "NONE")
    base = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, domain="event_adjudication_base",
        time_support=time, spatial_support=space,
        support_class=SupportClass.DIRECT_SUPPORTED,
        authority_class=StateAuthorityClass.DIRECT_AUTHORITY,
        value={"fixture": "base"},
    )
    unknown = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, domain="event_adjudication",
        time_support=time, spatial_support=space,
        support_class=SupportClass.UNKNOWN,
        authority_class=StateAuthorityClass.NONE,
        value=None,
        uncertainty={"event_occurrence": "UNKNOWN", "impact": "UNKNOWN"},
        parent_state_ids=(str(base.state_id),),
    )
    event = EventRecord.create(
        history_id=HISTORY, branch_id=BRANCH, time_key="210Ma",
        domain_ids=("event_adjudication",),
        validation_status="VALIDATED",
        details={"record_kind": "IMPACT_ADJUDICATION", "physical_event_occurrence": "UNKNOWN"},
    )
    checkpoint = CheckpointEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, time_key="210Ma",
        restart_state_ids=(str(base.state_id),), retained_history_state_ids=(str(base.state_id),),
        runtime_identity={"fixture": True}, configuration={}, seed_lineage={},
    )
    recipe = ReplayRecipe.create(
        history_id=HISTORY, branch_id=BRANCH,
        base_checkpoint_id=str(checkpoint.checkpoint_id),
        runtime_identity={"fixture": True}, configuration_sha256=content_hash({}),
        seed_lineage={}, forcing_ids=(), event_ids=(event.record_id,),
        expected_output_state_id=str(unknown.state_id), model_adapter_id="fixture-unknown-preserver",
    )
    store.append_transaction((base, unknown, event, checkpoint, recipe))

    queried = HistoryQueryService(store).state_at(
        history_id=HISTORY, branch_id=BRANCH, domain="event_adjudication", time_key="210Ma")
    assert queried.status == "UNKNOWN" and queried.state is not None
    assert queried.state.state_id == unknown.state_id
    loaded = DomainStateEnvelope.from_dict(store.read_state(str(unknown.state_id)).to_dict())
    assert loaded.support_class == SupportClass.UNKNOWN and loaded.value is None
    assert loaded.uncertainty["event_occurrence"] == "UNKNOWN"

    def runner(_recipe, inputs):
        assert inputs.events[0].details["physical_event_occurrence"] == "UNKNOWN"
        return ReplayExecutionOutput(inputs.expected_state)

    replay = execute_replay(store, recipe, runner)
    assert replay.status == "VERIFIED"
    assert replay.produced_state_id == str(unknown.state_id)
