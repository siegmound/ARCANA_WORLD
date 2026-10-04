from __future__ import annotations

import json
import multiprocessing
import shutil
import threading

import pytest

from arcana_worldsim.r6.identity import BranchId, HistoryId
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import DifferenceStatus, HistoryQueryService
from arcana_worldsim.r6.state import (AuthorityClass, DomainStateEnvelope,
    SpatialSupport, SupportClass, TimeSupport)
from arcana_worldsim.r6.store import (HistoryStore, ImmutableRecordConflict,
    ReadViewMigrationRequired)


def _state(label: str, cell: str | None = None) -> DomainStateEnvelope:
    history = str(HistoryId.from_payload({"b6m-r1a": "history"}))
    branch = str(BranchId.from_payload({"b6m-r1a": "branch"}))
    return DomainStateEnvelope.create(history_id=history,
        branch_id=branch, domain="fixture",
        time_support=TimeSupport(label, "B6MR1A_FIXTURE"),
        spatial_support=SpatialSupport("fixture_grid", (cell or label,), "fixture", "CELL_SET"),
        support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.FIXTURE_ONLY, value={"label": label})


def _bundle(label: str):
    provenance = ProvenanceRecord.create(activity="B6MR1A_VISIBILITY_FIXTURE",
        source_refs=(f"fixture://{label}",))
    return provenance, _state(label)


class SimulatedCrash(BaseException):
    pass


def _hold_process_read_view(root, ready, release, result):
    store = HistoryStore(root)
    with store.read_view() as view:
        ready.put(view.view_id)
        if not release.wait(timeout=20):
            raise TimeoutError("test did not release pinned process read-view")
        result.put((view.view_id, tuple(str(state.state_id) for state in store.states())))


def _hold_process_writer_lock(root, locked, release):
    store = HistoryStore(root)
    with store._writer_lock():
        locked.set()
        if not release.wait(timeout=20):
            raise TimeoutError("test did not release independent-process writer lock")


def test_uncommitted_records_are_invisible_through_materialization_and_visible_after_switch(tmp_path):
    root = tmp_path / "history"
    reader = HistoryStore(root)
    provenance, candidate = _bundle("candidate")
    observations = []

    def inspect(stage, count):
        if stage == "after_publication" and count in (1, 2):
            observations.append((stage, count, tuple(reader.states())))
            with pytest.raises(FileNotFoundError):
                reader.read_state(str(candidate.state_id))
        if stage == "before_visibility_switch":
            observations.append((stage, count, tuple(reader.states())))
            with pytest.raises(FileNotFoundError):
                reader.read_state(str(candidate.state_id))
        if stage == "after_visibility_switch":
            observations.append((stage, count, tuple(reader.states())))

    writer = HistoryStore(root, _fault_injector=inspect)
    writer.append_transaction((provenance, candidate))
    assert [row[0] for row in observations] == [
        "after_publication", "after_publication", "before_visibility_switch",
        "after_visibility_switch"]
    assert all(not rows for _, _, rows in observations[:-1])
    assert observations[-1][2] == (candidate,)
    assert reader.read_state(str(candidate.state_id)) == candidate


def test_pinned_read_view_and_compound_difference_do_not_mix_generations(tmp_path, monkeypatch):
    root = tmp_path / "history"
    base = _state("base", "same-cell")
    store = HistoryStore(root)
    store.append_state(base)
    reader = HistoryStore(root)
    writer = HistoryStore(root)
    provenance = ProvenanceRecord.create(activity="B6MR1A_VISIBILITY_FIXTURE",
        source_refs=("fixture://next",))
    candidate = _state("next", "same-cell")
    service = HistoryQueryService(reader)
    original_read_state = reader.read_state
    calls = 0

    def publish_between_lookups(state_id):
        nonlocal calls
        calls += 1
        if calls == 2:
            writer.append_transaction((provenance, candidate))
        return original_read_state(state_id)

    monkeypatch.setattr(reader, "read_state", publish_between_lookups)
    result = service.difference(str(base.state_id), str(candidate.state_id))
    assert result.status == DifferenceStatus.MISSING_INPUT
    assert result.reason == "STATE_B_MISSING"
    assert service.difference(str(base.state_id), str(candidate.state_id)).status == DifferenceStatus.COMPARABLE


def test_transaction_recovers_old_view_before_switch_and_new_view_after_switch(tmp_path):
    records = _bundle("recover")
    root_before = tmp_path / "before-switch"

    def stop_before(stage, _count):
        if stage == "before_visibility_switch":
            raise SimulatedCrash()

    with pytest.raises(SimulatedCrash):
        HistoryStore(root_before, _fault_injector=stop_before).append_transaction(records)
    reopened_before = HistoryStore(root_before)
    assert reopened_before.states() == ()
    assert not (root_before / "states" / f"{records[1].state_id}.json").exists()

    root_after = tmp_path / "after-switch"

    def stop_after(stage, _count):
        if stage == "after_visibility_switch":
            raise SimulatedCrash()

    with pytest.raises(SimulatedCrash):
        HistoryStore(root_after, _fault_injector=stop_after).append_transaction(records)
    assert HistoryStore(root_after).states() == (records[1],)
    assert not [p for p in (root_after / ".history_transactions").iterdir()
                if p.name != ".retired"]


def test_failure_after_view_preparation_leaves_old_view_and_no_transaction(tmp_path):
    root = tmp_path / "view-preparation-failure"
    records = _bundle("view-preparation")

    def stop(stage, _count):
        if stage == "after_view_preparation":
            raise SimulatedCrash()

    with pytest.raises(SimulatedCrash):
        HistoryStore(root, _fault_injector=stop).append_transaction(records)
    reopened = HistoryStore(root)
    assert reopened.states() == ()
    transaction_root = root / ".history_transactions"
    assert not transaction_root.exists() or not [
        p for p in transaction_root.iterdir() if p.name != ".retired"]
    # Prepared but unreachable immutable view metadata is an orphan candidate.
    assert len(list((root / ".history_visibility" / "views").glob("view_*.json"))) == 2


def test_direct_typed_all_pins_before_raw_record_enumeration(tmp_path, monkeypatch):
    root = tmp_path / "typed-all-race"
    reader = HistoryStore(root)
    writer = HistoryStore(root)
    provenance, candidate = _bundle("typed-all-race")
    original_all = reader._all
    calls = 0

    def enumerate_then_publish(bucket):
        nonlocal calls
        rows = original_all(bucket)
        if bucket == "states" and calls == 0:
            calls += 1
            writer.append_transaction((provenance, candidate))
        return rows

    monkeypatch.setattr(reader, "_all", enumerate_then_publish)
    assert reader.states() == ()
    assert reader.states() == (candidate,)


def test_stale_writer_parent_fails_closed_and_identical_repeat_is_idempotent(tmp_path):
    root = tmp_path / "history"
    store = HistoryStore(root)
    with store.read_view() as parent:
        old_view_id = parent.view_id
    records = _bundle("one")
    store.append_transaction(records, expected_parent_view_id=old_view_id)
    view_after = store._active_read_view().view_id
    store.append_transaction(records)
    assert store._active_read_view().view_id == view_after
    with pytest.raises(ImmutableRecordConflict, match="stale"):
        store.append_transaction(_bundle("two"), expected_parent_view_id=old_view_id)
    assert len(store.states()) == 1


def test_legacy_store_requires_explicit_validating_migration(tmp_path):
    root = tmp_path / "legacy"
    store = HistoryStore(root)
    item = _state("legacy")
    store.append_state(item)
    shutil.rmtree(root / ".history_visibility")
    with pytest.raises(ReadViewMigrationRequired):
        HistoryStore(root)
    migrated = HistoryStore(root, _migrate_legacy_visibility=True)
    assert migrated.states() == (item,)


def test_read_view_pointer_and_manifest_are_content_addressed(tmp_path):
    store = HistoryStore(tmp_path / "history")
    with store.read_view() as view:
        pointer = json.loads((store.root / ".history_visibility" / "CURRENT.json").read_text())
        manifest = json.loads((store.root / ".history_visibility" / "views" /
                               f"{view.view_id}.json").read_text())
    assert pointer["view_id"] == view.view_id == manifest["view_id"]


def test_independent_process_reader_keeps_its_pinned_generation(tmp_path):
    root = str(tmp_path / "process-store")
    writer = HistoryStore(root)
    context = multiprocessing.get_context("spawn")
    ready, release, result = context.Queue(), context.Event(), context.Queue()
    process = context.Process(target=_hold_process_read_view,
        args=(root, ready, release, result))
    process.start()
    old_view_id = ready.get(timeout=20)
    provenance, candidate = _bundle("process")
    writer.append_transaction((provenance, candidate))
    release.set()
    pinned_id, pinned_states = result.get(timeout=20)
    process.join(timeout=20)
    assert process.exitcode == 0
    assert pinned_id == old_view_id
    assert pinned_states == ()
    assert HistoryStore(root).states() == (candidate,)


def test_thread_reader_keeps_its_pinned_generation(tmp_path):
    root = tmp_path / "thread-store"
    reader = HistoryStore(root)
    writer = HistoryStore(root)
    pinned, release, result = threading.Event(), threading.Event(), []
    provenance, candidate = _bundle("thread")

    def read_in_thread():
        with reader.read_view() as view:
            pinned.set()
            assert release.wait(timeout=10)
            result.append((view.view_id, tuple(reader.states())))

    thread = threading.Thread(target=read_in_thread)
    thread.start()
    assert pinned.wait(timeout=10)
    writer.append_transaction((provenance, candidate))
    release.set()
    thread.join(timeout=10)
    assert not thread.is_alive()
    assert result and result[0][1] == ()
    assert reader.states() == (candidate,)


def test_independent_process_writer_lock_serializes_publication(tmp_path):
    root = str(tmp_path / "process-writer-store")
    writer = HistoryStore(root)
    context = multiprocessing.get_context("spawn")
    locked, release = context.Event(), context.Event()
    process = context.Process(target=_hold_process_writer_lock,
        args=(root, locked, release))
    process.start()
    assert locked.wait(timeout=20)

    done = threading.Event()
    records = _bundle("process-writer")
    thread = threading.Thread(target=lambda: (writer.append_transaction(records), done.set()))
    thread.start()
    assert not done.wait(timeout=0.25)
    release.set()
    thread.join(timeout=20)
    process.join(timeout=20)
    assert not thread.is_alive()
    assert process.exitcode == 0
    assert done.is_set()
    assert writer.states() == (records[1],)
