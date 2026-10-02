from __future__ import annotations

import json

import pytest

from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.identity import (BranchId, HistoryId, PayloadIdentity,
                                         canonical_bytes, content_hash)
from arcana_worldsim.r6.provenance import ProvenanceRecord, ProvenanceIntegrityError
from arcana_worldsim.r6.query import DifferenceStatus, HistoryQueryService
from arcana_worldsim.r6.replay import ReplayRecipe
from arcana_worldsim.r6.state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
                                      SupportClass, TimeSupport)
from arcana_worldsim.r6.store import HistoryStore, RecordIntegrityError
from arcana_worldsim.r6.temporal import EventRecord


HISTORY = str(HistoryId.from_payload({"fixture": "b0-e-history"}))
BRANCH = str(BranchId.from_payload({"fixture": "b0-e-main"}))
OTHER_BRANCH = str(BranchId.from_payload({"fixture": "b0-e-other"}))
SPACE = SpatialSupport("grid-a", ("cell-1", "cell-2"), "fixture-grid-v1", "CELL_SET")
TIME_A = TimeSupport("t:0", "fixture-clock", "INSTANT")
TIME_B = TimeSupport("t:1", "fixture-clock", "INSTANT")
CONFIG = {"fixture": "b0-e"}
RUNTIME = {"adapter": "fixture-v1"}
SEED = {"seed": 5}


def make_state(domain, time, value, *, branch=BRANCH, support=SupportClass.DIRECT_SUPPORTED,
               authority=AuthorityClass.DERIVED_AUTHORITY, uncertainty=None,
               provenance=(), parents=(), events=(), space=SPACE):
    return DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=branch, domain=domain,
        time_support=time, spatial_support=space, support_class=support,
        authority_class=authority, value=value, uncertainty=uncertainty or {},
        provenance_ids=tuple(provenance), parent_state_ids=tuple(parents),
        event_refs=tuple(events),
    )


def test_history_result_filters_exact_metadata_and_orders_semantically_after_reopen(tmp_path):
    root = tmp_path / "history"
    states = [
        make_state("temperature", TIME_B, 20.0, branch=OTHER_BRANCH),
        make_state("elevation", TIME_A, 4.0),
        make_state("temperature", TIME_B, 20.0, space=SpatialSupport("grid-a", ("cell-1",), "fixture-grid-v1")),
        make_state("temperature", TIME_A, 10.0),
    ]
    for state in reversed(states):
        HistoryStore(root).append_state(state)
    service = HistoryQueryService(HistoryStore(root))
    result = service.history_result(history_id=HISTORY)
    assert result.states == tuple(sorted(states, key=lambda s: (
        s.time_support.coordinate_system, s.time_support.support_kind, s.time_support.time_key,
        s.domain, s.spatial_support.selector_kind, s.spatial_support.grid_id or "",
        tuple(s.spatial_support.cell_ids), str(s.state_id))))
    assert service.history(history_id=HISTORY, branch_id=BRANCH, domain="temperature") == tuple(
        s for s in result.states if s.branch_id == BRANCH and s.domain == "temperature")
    assert service.history_result(history_id=HISTORY, branch_id=BRANCH,
                                  domain="temperature", time_key="t:1",
                                  cell_id="cell-1").states
    assert all(state.to_dict() == HistoryStore(root).read_state(str(state.state_id)).to_dict()
               for state in result.states)


def test_history_order_is_independent_of_insertion_order(tmp_path):
    states = [make_state("d", TIME_A, value) for value in (3, 1, 2)]
    first, second = tmp_path / "first", tmp_path / "second"
    for state in states:
        HistoryStore(first).append_state(state)
    for state in reversed(states):
        HistoryStore(second).append_state(state)
    ids1 = [str(s.state_id) for s in HistoryQueryService(HistoryStore(first)).history(history_id=HISTORY)]
    ids2 = [str(s.state_id) for s in HistoryQueryService(HistoryStore(second)).history(history_id=HISTORY)]
    assert ids1 == ids2
    assert HistoryQueryService(HistoryStore(first)).difference(
        str(states[0].state_id), str(states[1].state_id)) == HistoryQueryService(
            HistoryStore(second)).difference(str(states[0].state_id), str(states[1].state_id))


def test_existing_state_query_support_statuses_remain_distinct(tmp_path):
    store = HistoryStore(tmp_path / "history")
    known = make_state("known", TIME_A, 0)
    unknown = make_state("unknown", TIME_A, None, support=SupportClass.UNKNOWN)
    not_applicable = make_state("na", TIME_A, None, support=SupportClass.NOT_APPLICABLE)
    outside_scope = make_state("outside", TIME_A, None, support=SupportClass.OUTSIDE_SCOPE)
    grid = make_state("grid", TIME_A, 1,
                      space=SpatialSupport("grid-a", (), "fixture-grid-v1", "GRID"))
    store.append_transaction((known, unknown, not_applicable, outside_scope, grid))
    query = HistoryQueryService(store)

    def status(domain, *, cell="cell-1", time=TIME_A.time_key):
        return query.state_at(history_id=HISTORY, branch_id=BRANCH, domain=domain,
                              time_key=time, cell_id=cell).status

    assert status("known") == "FOUND"
    assert status("known", cell="absent-cell") == "OUTSIDE_SUPPORT"
    assert status("grid") == "SUPPORT_MISMATCH"
    assert status("unknown") == "UNKNOWN"
    assert status("na") == "NOT_APPLICABLE"
    assert status("outside") == "OUTSIDE_SCOPE"
    assert status("missing-domain") == "MISSING_DOMAIN"
    assert status("known", time="missing-time") == "MISSING_TIMESTAMP"
    assert query.state_at(history_id=HISTORY, branch_id=BRANCH, domain="known",
                          time_key=TIME_A.time_key).status == "FOUND"


@pytest.mark.parametrize(("a", "b", "expected"), [
    (0, 1, 1), (1, 0, -1),
])
def test_numeric_difference_including_known_zero(tmp_path, a, b, expected):
    store, left, right = _pair(tmp_path, a, b)
    result = HistoryQueryService(store).difference(str(left.state_id), str(right.state_id))
    assert result.status is DifferenceStatus.COMPARABLE
    assert result.operation == "NUMERIC_DELTA_B_MINUS_A"
    assert result.value == expected


@pytest.mark.parametrize(("a", "b", "equal"), [(False, True, False), (True, False, False)])
def test_boolean_difference_reports_change_without_subtraction(tmp_path, a, b, equal):
    store, left, right = _pair(tmp_path, a, b)
    result = HistoryQueryService(store).difference(str(left.state_id), str(right.state_id))
    assert result.status is DifferenceStatus.COMPARABLE
    assert result.operation == "CATEGORICAL_EQUALITY"
    assert result.value is None and result.equal is equal


def test_numeric_vector_difference_requires_exact_shape(tmp_path):
    store, left, right = _pair(tmp_path, [1, 2], [3, 5])
    result = HistoryQueryService(store).difference(str(left.state_id), str(right.state_id))
    assert result.status is DifferenceStatus.COMPARABLE
    assert result.value == (2, 3)
    store, left, right = _pair(tmp_path / "shape", [1, 2], [3])
    result = HistoryQueryService(store).difference(
        str(left.state_id), str(right.state_id))
    assert result.status is DifferenceStatus.TYPE_OR_SHAPE_MISMATCH


@pytest.mark.parametrize(("support", "status"), [
    (SupportClass.UNKNOWN, DifferenceStatus.UNKNOWN_INPUT),
    (SupportClass.NOT_APPLICABLE, DifferenceStatus.NOT_APPLICABLE),
    (SupportClass.OUTSIDE_SCOPE, DifferenceStatus.OUTSIDE_SCOPE),
])
def test_semantic_support_statuses_are_not_numeric_differences(tmp_path, support, status):
    store = HistoryStore(tmp_path / support.value)
    known = make_state("d", TIME_A, 2)
    special = make_state("d", TIME_B, None, support=support)
    store.append_transaction((known, special))
    result = HistoryQueryService(store).difference(str(known.state_id), str(special.state_id))
    assert result.status is status
    assert result.state_a is known or result.state_a == known
    assert result.state_b == special
    reverse = HistoryQueryService(store).difference(str(special.state_id), str(known.state_id))
    assert reverse.status is status


def test_difference_rejects_support_type_and_missing_mismatches(tmp_path):
    store = HistoryStore(tmp_path / "history")
    a = make_state("temperature", TIME_A, 1)
    wrong_space = make_state("temperature", TIME_B, 2,
                             space=SpatialSupport("grid-b", ("cell-1", "cell-2"), "fixture-grid-v1"))
    wrong_domain = make_state("elevation", TIME_B, 2)
    text = make_state("temperature", TIME_B, "2")
    store.append_transaction((a, wrong_space, wrong_domain, text))
    service = HistoryQueryService(store)
    assert service.difference(str(a.state_id), str(wrong_space.state_id)).status is DifferenceStatus.INCOMPATIBLE_SUPPORT
    assert service.difference(str(a.state_id), str(wrong_domain.state_id)).status is DifferenceStatus.INCOMPATIBLE_SUPPORT
    mismatch = service.difference(str(a.state_id), str(text.state_id))
    assert mismatch.status is DifferenceStatus.TYPE_OR_SHAPE_MISMATCH
    assert service.difference(str(a.state_id), "missing-state").status is DifferenceStatus.MISSING_INPUT
    interval = make_state("temperature", TimeSupport("t:1", "fixture-clock", "INTERVAL"), 2)
    store.append_state(interval)
    assert service.difference(str(a.state_id), str(interval.state_id)).status is DifferenceStatus.INCOMPATIBLE_SUPPORT


def test_difference_preserves_both_authorities_uncertainties_and_supports(tmp_path):
    store = HistoryStore(tmp_path / "history")
    a = make_state("d", TIME_A, 1, authority=AuthorityClass.DIRECT_AUTHORITY,
                   uncertainty={"sigma": 0.4}, support=SupportClass.DIRECT_SUPPORTED)
    b = make_state("d", TIME_B, 2, authority=AuthorityClass.SPARSE_AUTHORITY,
                   uncertainty={"range": [1, 3]}, support=SupportClass.SPARSE_AUTHORITY)
    store.append_transaction((a, b))
    result = HistoryQueryService(store).difference(str(a.state_id), str(b.state_id))
    assert result.status is DifferenceStatus.COMPARABLE
    assert result.state_a.authority_class is AuthorityClass.DIRECT_AUTHORITY
    assert result.state_b.authority_class is AuthorityClass.SPARSE_AUTHORITY
    assert result.state_a.uncertainty["sigma"] == 0.4
    assert tuple(result.state_b.uncertainty["range"]) == (1, 3)
    assert result.state_a.support_class is SupportClass.DIRECT_SUPPORTED
    assert result.state_b.support_class is SupportClass.SPARSE_AUTHORITY
    assert result.uncertainty_propagation == "NOT_PROPAGATED"


def test_why_joins_reopened_replay_provenance_event_forcing_checkpoint_and_recipe(tmp_path):
    store = HistoryStore(tmp_path / "history")
    shared = ProvenanceRecord.create(activity="shared-source", source_refs=("provider:fixture",))
    base_prov = ProvenanceRecord.create(activity="base", parent_provenance_ids=(str(shared.record_id),))
    output_prov = ProvenanceRecord.create(activity="synthetic-replay",
        parent_provenance_ids=(str(shared.record_id),), input_refs=("input:fixture",))
    base = make_state("fixture", TIME_A, {"x": 2}, provenance=(str(base_prov.record_id),))
    event = EventRecord.create(history_id=HISTORY, branch_id=BRANCH, time_key=TIME_A.time_key,
                               state_ids=(str(base.state_id),), details={"event": "fixture"})
    forcing = ForcingRecord.create(history_id=HISTORY, branch_id=BRANCH, forcing_kind="fixture",
        domain="fixture", time_support=TIME_A, spatial_support=SPACE,
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"delta": 1}, provenance_ids=(str(output_prov.record_id),),
        source_refs=("forcing-source:fixture",))
    payload = canonical_bytes({"x": 3})
    payload_identity = PayloadIdentity.from_bytes(payload)
    expected = make_state("fixture", TIME_B, {"x": 3}, provenance=(str(output_prov.record_id),),
                          parents=(str(base.state_id),), events=(event.record_id,),
                          authority=AuthorityClass.FIXTURE_ONLY,
                          support=SupportClass.FIXTURE_ONLY)
    checkpoint = CheckpointEnvelope.create(history_id=HISTORY, branch_id=BRANCH,
        time_key=TIME_A.time_key, restart_state_ids=(str(base.state_id),),
        retained_history_state_ids=(str(base.state_id),), runtime_identity=RUNTIME,
        configuration=CONFIG, seed_lineage=SEED, upstream_dependency_ids=(str(shared.record_id),))
    recipe = ReplayRecipe.create(history_id=HISTORY, branch_id=BRANCH,
        base_checkpoint_id=str(checkpoint.checkpoint_id), runtime_identity=RUNTIME,
        configuration_sha256=content_hash(CONFIG), seed_lineage=SEED,
        forcing_ids=(str(forcing.forcing_id),), event_ids=(event.record_id,),
        upstream_dependency_ids=(str(shared.record_id),),
        provenance_ids=(str(output_prov.record_id),),
        expected_output_state_id=str(expected.state_id), model_adapter_id="fixture:adapter",
        expected_payload_identity=payload_identity)
    records = (shared, base_prov, output_prov, base, event, forcing,
               expected, checkpoint, recipe)
    store.append_transaction(records)
    before = _store_bytes(tmp_path / "history")
    result = HistoryQueryService(HistoryStore(tmp_path / "history")).why(str(expected.state_id))
    after = _store_bytes(tmp_path / "history")
    assert before == after
    assert {str(s.state_id) for s in result.state_lineage} == {
        str(expected.state_id), str(base.state_id)}
    assert {str(p.record_id) for p in result.provenance_records} == {
        str(shared.record_id), str(base_prov.record_id), str(output_prov.record_id)}
    assert [e.record_id for e in result.events] == [event.record_id]
    assert [str(f.forcing_id) for f in result.forcings] == [str(forcing.forcing_id)]
    assert [str(c.checkpoint_id) for c in result.checkpoints] == [str(checkpoint.checkpoint_id)]
    assert [str(r.recipe_id) for r in result.replay_recipes] == [str(recipe.recipe_id)]
    assert result.external_references == tuple(sorted(result.external_references))
    assert "provider:fixture" in result.external_references
    assert result.unresolved_references == ()
    assert result.authority_summary[0][1] == AuthorityClass.FIXTURE_ONLY.value
    reordered_store = HistoryStore(tmp_path / "history-reordered")
    for record in reversed(records):
        _append_record(reordered_store, record)
    reordered = HistoryQueryService(reordered_store).why(str(expected.state_id))
    assert reordered == result


def test_why_exposes_dangling_references_and_deduplicates_shared_ancestor(tmp_path):
    store = HistoryStore(tmp_path / "history")
    shared = ProvenanceRecord.create(activity="shared")
    left = ProvenanceRecord.create(activity="left", parent_provenance_ids=(str(shared.record_id),))
    right = ProvenanceRecord.create(activity="right", parent_provenance_ids=(str(shared.record_id),))
    absent_provenance = "r6prov_" + "a" * 64
    absent_state = "r6state_" + "b" * 64
    state = make_state("d", TIME_A, 1,
        provenance=(str(left.record_id), str(right.record_id), absent_provenance),
        parents=(absent_state,))
    store.append_transaction((shared, left, right, state))
    result = HistoryQueryService(store).why(str(state.state_id))
    assert [p.record_id for p in result.provenance_records].count(shared.record_id) == 1
    assert set(result.unresolved_references) == {absent_provenance, absent_state}


def test_why_fails_closed_when_a_typed_record_is_corrupt(tmp_path):
    root = tmp_path / "history"
    store = HistoryStore(root)
    provenance = ProvenanceRecord.create(activity="corrupt-me")
    state = make_state("d", TIME_A, 1, provenance=(str(provenance.record_id),))
    store.append_transaction((provenance, state))
    path = root / "provenance" / f"{provenance.record_id}.json"
    row = json.loads(path.read_text(encoding="utf-8"))
    row["activity"] = "tampered"
    path.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(RecordIntegrityError):
        HistoryQueryService(store).why(str(state.state_id))


def test_history_difference_and_why_are_read_only(tmp_path):
    root = tmp_path / "history"
    store = HistoryStore(root)
    prov = ProvenanceRecord.create(activity="purity")
    a = make_state("d", TIME_A, 1, provenance=(str(prov.record_id),))
    b = make_state("d", TIME_B, 2, provenance=(str(prov.record_id),), parents=(str(a.state_id),))
    store.append_transaction((prov, a, b))
    before = _store_bytes(root)
    query = HistoryQueryService(HistoryStore(root))
    query.history_result(history_id=HISTORY)
    query.difference(str(a.state_id), str(b.state_id))
    query.why(str(b.state_id))
    assert _store_bytes(root) == before


def _pair(root, value_a, value_b):
    store = HistoryStore(root / "history")
    a, b = make_state("measure", TIME_A, value_a), make_state("measure", TIME_B, value_b)
    store.append_transaction((a, b))
    return store, a, b


def _store_bytes(root):
    return {str(path.relative_to(root)): path.read_bytes()
            for path in sorted(root.rglob("*.json")) if path.is_file()}


def _append_record(store, record):
    if isinstance(record, DomainStateEnvelope):
        store.append_state(record)
    elif isinstance(record, ProvenanceRecord):
        store.append_provenance(record)
    elif isinstance(record, EventRecord):
        store.append_event(record)
    elif isinstance(record, ForcingRecord):
        store.append_forcing(record)
    elif isinstance(record, CheckpointEnvelope):
        store.append_checkpoint(record)
    elif isinstance(record, ReplayRecipe):
        store.append_replay_recipe(record)
    else:
        raise TypeError(type(record))
