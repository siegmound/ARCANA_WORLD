from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from arcana_worldsim.r6.identity import PayloadIdentity
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.replay import ReplayExecutionOutput, execute_replay
from arcana_worldsim.r6.rift_activation import (
    EVENT_TIME_KEY, MODEL_ID, build_activation_bundle,
    replay_activation,
)
from arcana_worldsim.r6.state import (
    AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport,
)
from arcana_worldsim.r6.store import HistoryStore
from arcana_worldsim.r6.temporal import EventRecord


CONTRACT_HASHES = {
    "activation": "a" * 64,
    "same_time": "b" * 64,
    "second_dt": "c" * 64,
}
PAYLOAD = b"synthetic-fixture-geometry-payload"
PAYLOAD_SHA = sha256(PAYLOAD).hexdigest()
ASYNC_DOMAIN_VALIDITY = tuple(json.loads(Path(
    "contracts/R6_RIFT_PROCESS_ACTIVATION_MODEL_V1.json").read_text(encoding="utf-8"))[
        "asynchronous_domain_validity"])


def _pre_event() -> tuple[DomainStateEnvelope, EventRecord]:
    time = TimeSupport(EVENT_TIME_KEY, "R6_GLOBAL_MA_OLDER_TO_YOUNGER")
    support = SpatialSupport("synthetic-grid", selector_kind="GLOBAL")
    pre = DomainStateEnvelope.create(history_id="r6hist_" + "1" * 64,
        branch_id="r6branch_" + "2" * 64, domain="tectonic_geometry",
        time_support=time, spatial_support=support,
        support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={"topology_identity": "topology-fixture", "plate_ids": [1, 3]},
        payload_ref=f"sha256:{PAYLOAD_SHA}")
    predicate = EventRecord.create(history_id=pre.history_id, branch_id=pre.branch_id,
        time_key=EVENT_TIME_KEY, domain_ids=("tectonic_geometry",),
        details={"event_class": "RIFT_PROCESS_ACTIVATION", "predicate": "SATISFIED",
                 "transition": "NOT_EXECUTED"},
        temporal_support={"time_key": EVENT_TIME_KEY},
        spatial_support={"topology_identity": "topology-fixture"},
        before_state_ids=(str(pre.state_id),), after_state_ids=(str(pre.state_id),))
    # The production predicate binds the already materialized T1 as its after state.
    return pre, predicate


def test_causal_successor_is_deterministic_and_preserves_physical_state():
    pre, predicate = _pre_event()
    first = build_activation_bundle(pre, predecessor_event=predicate,
        contract_hashes=CONTRACT_HASHES, async_domain_validity=ASYNC_DOMAIN_VALIDITY)
    second = build_activation_bundle(pre, predecessor_event=predicate,
        contract_hashes=CONTRACT_HASHES, async_domain_validity=ASYNC_DOMAIN_VALIDITY)
    assert first.post_state.state_id == second.post_state.state_id
    assert first.post_state.time_support == pre.time_support
    assert first.post_state.payload_ref == pre.payload_ref
    assert first.post_state.spatial_support == pre.spatial_support
    assert first.post_state.value["topology_identity"] == pre.value["topology_identity"]
    assert first.post_state.value["process_state"] == "RIFT_PROCESS_ACTIVE"
    assert first.post_state.applicability["causal_order_key"]["causal_phase"] == "POST_EVENT"
    assert DomainStateEnvelope.from_dict(first.post_state.to_dict()).state_id == first.post_state.state_id
    assert first.post_state.applicability["refinement_checkpoint_policy"] == (
        "GEOMETRY_REUSABLE_WITH_EXPLICIT_CAUSAL_TOPOLOGY_VERSION")
    assert first.application_event.cause_ref == predicate.record_id
    assert first.application_event.temporal_support["causal_order_key"]["causal_sequence"] == 1
    assert first.memory_state.value["mechanics_executed_false"] is True
    assert first.memory_state.value["second_dt_selected"] is False
    assert len(first.post_state.applicability["async_domain_validity"]) == 14
    assert first.post_state.applicability["async_domain_validity"] == ASYNC_DOMAIN_VALIDITY
    assert first.application_event.details["cleared_continuation_guard"] == (
        "CONTINUATION_BLOCKED_PENDING_RIFT_TRANSITION")
    assert first.replay_recipe.forcing_ids == ()
    assert first.replay_recipe.event_ids == (str(first.application_event.record_id),)
    assert first.checkpoint.restart_state_ids == (str(pre.state_id),)
    assert MODEL_ID in first.application_event.authority_refs


def test_same_time_query_history_why_replay_and_idempotent_bundle(tmp_path):
    pre, predicate = _pre_event()
    store = HistoryStore(tmp_path / "history")
    store.append_transaction((pre, predicate))
    bundle = build_activation_bundle(pre, predecessor_event=predicate,
        contract_hashes=CONTRACT_HASHES, async_domain_validity=ASYNC_DOMAIN_VALIDITY)
    with store.read_view() as parent_view:
        parent_view_id = parent_view.view_id
    store.append_transaction(bundle.records, expected_parent_view_id=parent_view_id)
    with store.read_view() as first_published_view:
        first_view_id = first_published_view.view_id
    store.append_transaction(bundle.records, expected_parent_view_id=first_view_id)
    with store.read_view() as retry_view:
        assert retry_view.view_id == first_view_id

    query = HistoryQueryService(store)
    selected_pre = query.state_at(history_id=pre.history_id, branch_id=pre.branch_id,
        domain=pre.domain, time_key=EVENT_TIME_KEY, causal_phase="PRE_EVENT",
        causal_event_id=str(predicate.record_id))
    selected_post = query.state_at(history_id=pre.history_id, branch_id=pre.branch_id,
        domain=pre.domain, time_key=EVENT_TIME_KEY, causal_phase="POST_EVENT",
        causal_event_id=str(predicate.record_id))
    ambiguous = query.state_at(history_id=pre.history_id, branch_id=pre.branch_id,
        domain=pre.domain, time_key=EVENT_TIME_KEY)
    assert selected_pre.state.state_id == pre.state_id
    assert selected_post.state.state_id == bundle.post_state.state_id
    assert ambiguous.status == "CONFLICT"
    assert ambiguous.provenance["reason"] == "AMBIGUOUS_CAUSAL_STATE"
    assert [s.state_id for s in query.history_result(history_id=pre.history_id,
        branch_id=pre.branch_id, domain=pre.domain, time_key=EVENT_TIME_KEY).states] == [
            pre.state_id, bundle.post_state.state_id]
    assert query.event_at(history_id=pre.history_id, branch_id=pre.branch_id,
        time_key=EVENT_TIME_KEY, causal_event_id=str(predicate.record_id)) == (bundle.application_event,)
    assert query.support_at(history_id=pre.history_id, branch_id=pre.branch_id,
        domain=pre.domain, time_key=EVENT_TIME_KEY, causal_phase="POST_EVENT",
        causal_event_id=str(predicate.record_id))["status"] == "PRESERVED_MEMBERSHIP_WITH_NEW_CAUSAL_VERSION"
    why = query.why(str(bundle.post_state.state_id))
    assert {str(item.record_id) for item in why.events} >= {
        str(bundle.application_event.record_id), str(predicate.record_id)}

    reopened = HistoryStore(tmp_path / "history")
    reopened_bundle = build_activation_bundle(pre, predecessor_event=predicate,
        contract_hashes=CONTRACT_HASHES, async_domain_validity=ASYNC_DOMAIN_VALIDITY)
    assert reopened_bundle.post_state.state_id == bundle.post_state.state_id
    recipe = reopened.read_replay_recipe(str(bundle.replay_recipe.recipe_id))
    replayed = execute_replay(reopened, recipe,
        lambda _recipe, inputs: ReplayExecutionOutput(
            replay_activation(inputs.base_states[0], predecessor_event=predicate,
                contract_hashes=CONTRACT_HASHES,
                async_domain_validity=ASYNC_DOMAIN_VALIDITY), PAYLOAD))
    assert replayed.status == "VERIFIED"
    assert replayed.produced_payload_identity == PayloadIdentity("sha256", PAYLOAD_SHA)

