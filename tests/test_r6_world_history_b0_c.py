from __future__ import annotations

import json

import pytest

from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.identity import BranchId, HistoryId
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.state import (
    AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport,
)
from arcana_worldsim.r6.store import (
    HistoryStore, ImmutableRecordConflict, TransactionRecoveryError,
)
from arcana_worldsim.r6.temporal import EventRecord


HISTORY = str(HistoryId.from_payload({"fixture": "b0-c-history"}))
BRANCH = str(BranchId.from_payload({"fixture": "b0-c-branch"}))
TIME = TimeSupport("b0-c:t0", "fixture-clock")
SPACE = SpatialSupport("fixture-grid", ("cell-1",), "native", "CELL_SET")


def state(domain: str, *, provenance: tuple[str, ...] = ()) -> DomainStateEnvelope:
    return DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, domain=domain,
        time_support=TIME, spatial_support=SPACE,
        support_class=SupportClass.DIRECT_SUPPORTED,
        authority_class=AuthorityClass.DIRECT_AUTHORITY,
        value={"fixture": domain}, uncertainty={}, provenance_ids=provenance,
    )


def bundle():
    provenance = ProvenanceRecord.create(activity="synthetic-b0-c-fixture",
                                         source_refs=("fixture-source",))
    current = state("bundle-state", provenance=(str(provenance.record_id),))
    event = EventRecord.create(
        history_id=HISTORY, branch_id=BRANCH, time_key=TIME.time_key,
        domain_ids=(current.domain,), state_ids=(str(current.state_id),),
        details={"event_type": "synthetic-bundle-fixture"},
    )
    checkpoint = CheckpointEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, time_key=TIME.time_key,
        restart_state_ids=(str(current.state_id),),
        retained_history_state_ids=(str(current.state_id),),
        runtime_identity={"engine": "fixture"}, configuration={"case": "b0-c"},
        seed_lineage={"seed": 17}, upstream_dependency_ids=("fixture-source",),
    )
    return provenance, event, current, checkpoint


def test_successful_transaction_is_visible_after_new_store_reopen(tmp_path):
    root = tmp_path / "history"
    records = bundle()
    store = HistoryStore(root)
    ids = store.append_transaction(records)
    assert len(ids) == len(records)
    reopened = HistoryStore(root)
    provenance, event, current, checkpoint = records
    assert reopened.read_provenance(str(provenance.record_id)) == provenance.to_dict()
    assert reopened.read_event(event.record_id) == event.to_dict()
    assert reopened.read_state(str(current.state_id)) == current
    assert reopened.read_checkpoint(str(checkpoint.checkpoint_id)) == checkpoint.to_dict()


def test_preflight_conflict_publishes_none_of_new_bundle(tmp_path):
    root = tmp_path / "history"
    store = HistoryStore(root)
    conflict = state("already-present")
    store.append_state(conflict)
    conflicting_path = root / "states" / f"{conflict.state_id}.json"
    corrupted = json.loads(conflicting_path.read_text())
    corrupted["value"] = {"different": True}
    conflicting_path.write_text(json.dumps(corrupted))
    new_state = state("must-not-publish")
    with pytest.raises(ImmutableRecordConflict):
        store.append_transaction((new_state, conflict))
    assert not (root / "states" / f"{new_state.state_id}.json").exists()
    assert json.loads(conflicting_path.read_text())["value"] == {"different": True}


@pytest.mark.parametrize(("stage", "count"), [
    ("before_publication", 0),
    ("after_publication", 1),
    ("after_publication", 2),
    ("before_commit", 4),
])
def test_injected_precommit_failures_roll_back_all_new_records(tmp_path, stage, count):
    root = tmp_path / f"history-{stage}-{count}"
    records = bundle()

    def inject(found_stage, found_count):
        if (found_stage, found_count) == (stage, count):
            raise RuntimeError("injected transaction interruption")

    store = HistoryStore(root, _fault_injector=inject)
    with pytest.raises(RuntimeError, match="injected"):
        store.append_transaction(records)
    reopened = HistoryStore(root)
    provenance, event, current, checkpoint = records
    for bucket, record_id in (
        ("provenance", str(provenance.record_id)), ("events", event.record_id),
        ("states", str(current.state_id)),
        ("checkpoints", str(checkpoint.checkpoint_id)),
    ):
        assert not (root / bucket / f"{record_id}.json").exists()
    assert not [path for path in (root / ".history_transactions").iterdir()
                if path.name != ".retired"]


def test_rollback_preserves_preexisting_identical_and_unrelated_records(tmp_path):
    root = tmp_path / "history"
    preexisting = state("included-preexisting")
    unrelated = state("unrelated")
    store = HistoryStore(root)
    store.append_state(preexisting)
    store.append_state(unrelated)
    records = (*bundle(), state("new-state"), preexisting)

    def inject(stage, count):
        if stage == "before_commit":
            raise RuntimeError("rollback after full publication")

    failing = HistoryStore(root, _fault_injector=inject)
    with pytest.raises(RuntimeError):
        failing.append_transaction(records)
    reopened = HistoryStore(root)
    assert reopened.read_state(str(preexisting.state_id)) == preexisting
    assert reopened.read_state(str(unrelated.state_id)) == unrelated
    new_state = next(record for record in records
                     if isinstance(record, DomainStateEnvelope) and record.domain == "new-state")
    assert not (root / "states" / f"{new_state.state_id}.json").exists()


class SimulatedProcessInterruption(BaseException):
    pass


def test_reopen_recovers_interrupted_publication_idempotently(tmp_path):
    root = tmp_path / "history"
    records = bundle()

    def interrupt(stage, count):
        if (stage, count) == ("after_publication", 1):
            raise SimulatedProcessInterruption()

    store = HistoryStore(root, _fault_injector=interrupt)
    with pytest.raises(SimulatedProcessInterruption):
        store.append_transaction(records)
    active_journals = [p for p in (root / ".history_transactions").iterdir()
                       if p.name != ".retired"]
    assert len(active_journals) == 1

    recovered = HistoryStore(root)
    for bucket, record_id in (("provenance", str(records[0].record_id)),
                              ("events", records[1].record_id),
                              ("states", str(records[2].state_id)),
                              ("checkpoints", str(records[3].checkpoint_id))):
        assert not (root / bucket / f"{record_id}.json").exists()
    before = sorted((root / ".history_transactions").rglob("*"))
    HistoryStore(root)
    after = sorted((root / ".history_transactions").rglob("*"))
    assert before == after
    assert recovered.states() == ()


def test_corrupt_transaction_journal_fails_closed(tmp_path):
    root = tmp_path / "history"
    records = bundle()

    def interrupt(stage, count):
        if (stage, count) == ("after_publication", 1):
            raise SimulatedProcessInterruption()

    with pytest.raises(SimulatedProcessInterruption):
        HistoryStore(root, _fault_injector=interrupt).append_transaction(records)
    transaction_dir = next(path for path in (root / ".history_transactions").iterdir()
                           if path.name != ".retired")
    manifest_path = transaction_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["entries"][0]["preexisting"] = not manifest["entries"][0]["preexisting"]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(TransactionRecoveryError, match="journal"):
        HistoryStore(root)


def test_cleanup_failure_keeps_committed_records_and_reopen_finalizes(tmp_path):
    root = tmp_path / "history"
    records = bundle()

    def fail_cleanup(stage, count):
        if stage == "during_cleanup":
            raise RuntimeError("injected cleanup failure")

    store = HistoryStore(root, _fault_injector=fail_cleanup)
    store.append_transaction(records)
    active = [p for p in (root / ".history_transactions").iterdir()
              if p.name != ".retired"]
    assert len(active) == 1
    reopened = HistoryStore(root)
    assert reopened.read_state(str(records[2].state_id)) == records[2]
    assert not [p for p in (root / ".history_transactions").iterdir()
                if p.name != ".retired"]


def test_single_record_append_remains_idempotent(tmp_path):
    store = HistoryStore(tmp_path / "history")
    item = state("single")
    assert store.append_state(item) == str(item.state_id)
    assert store.append_state(item) == str(item.state_id)
    assert store.read_state(str(item.state_id)) == item
