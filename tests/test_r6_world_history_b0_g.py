from __future__ import annotations

from pathlib import Path

import pytest

from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.identity import BranchId, HistoryId
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import DifferenceStatus, HistoryQueryService
from arcana_worldsim.r6.retention import (
    InformationRole, MinimalStateContract, MinimalStateExtractionResult,
    RetentionAction, RetentionItem, extract_minimal_state, validate_extraction,
)
from arcana_worldsim.r6.state import (
    AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport,
)
from arcana_worldsim.r6.storage import (
    AccountingRoot, AccountingScope, StorageAccountingError, StorageCategory,
    account_storage, history_store_scope,
)
from arcana_worldsim.r6.store import HistoryStore


HISTORY = str(HistoryId.from_payload({"fixture": "b0-g"}))
BRANCH = str(BranchId.from_payload({"fixture": "b0-g"}))
TIME = TimeSupport("fixture:t0", "synthetic", "SNAPSHOT")


def _forcing():
    return ForcingRecord.create(
        history_id=HISTORY, branch_id=BRANCH, forcing_kind="fixture-input",
        domain="fixture", time_support=TIME, spatial_support=SpatialSupport(None, (), None, "GLOBAL"),
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"increment": 3}, source_refs=("fixture:forcing",))


def _contract(forcing_id: str):
    return MinimalStateContract("fixture-adapter-v1", (
        RetentionItem("core_state", RetentionAction.MATERIALIZE, InformationRole.QUERY_OUTPUT),
        RetentionItem("memory_state", RetentionAction.MATERIALIZE, InformationRole.SYSTEM_MEMORY),
        RetentionItem("derived_display", RetentionAction.DERIVE, InformationRole.QUERY_OUTPUT,
                      reconstruction_refs=("recipe:display-v1", "parent:core_state")),
        RetentionItem("forcing", RetentionAction.FORCING, InformationRole.INPUT,
                      reconstruction_refs=(f"forcing:{forcing_id}",)),
        RetentionItem("diagnostic_trace", RetentionAction.DISCARD, InformationRole.DIAGNOSTIC),
        RetentionItem("temporary_intermediate", RetentionAction.DISCARD, InformationRole.INTERMEDIATE),
    ))


class FixtureExtractor:
    adapter_id = "fixture-adapter-v1"

    def extract(self, raw_output, contract):
        states = {}
        for item_id in ("core_state", "memory_state"):
            if item_id not in raw_output:
                continue
            state = DomainStateEnvelope.create(
                history_id=HISTORY, branch_id=BRANCH, domain=f"fixture:{item_id}",
                time_support=TIME, spatial_support=SpatialSupport("fixture-grid", ("cell-1",)),
                support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
                value={"value": raw_output[item_id]}, uncertainty={"fixture": True})
            states[item_id] = (state,)
        omissions = ("derived_display", "forcing", "diagnostic_trace", "temporary_intermediate")
        return MinimalStateExtractionResult(
            contract.contract_id, states, forcing_identities=(raw_output["forcing_id"],),
            reconstruction_identities=("recipe:display-v1",),
            omitted_item_ids=omissions)


def _raw(forcing):
    return {"core_state": 7, "memory_state": 11, "derived_display": 18,
            "forcing_value": 3, "forcing_id": str(forcing.forcing_id),
            "diagnostic_trace": ["not persisted"], "temporary_intermediate": object()}


def _evolve(core, memory, forcing_value):
    # memory carries a latent accumulator required to match complete-run evolution.
    new_memory = memory + forcing_value
    return {"core_state": core + new_memory, "memory_state": new_memory}


def test_minimal_extraction_reopens_queries_and_matches_complete_fixture(tmp_path):
    forcing = _forcing()
    contract = _contract(str(forcing.forcing_id))
    raw = _raw(forcing)
    extracted = extract_minimal_state(raw, contract, FixtureExtractor(),
                                      history_id=HISTORY, branch_id=BRANCH)
    assert extracted.validation_status == "PASS"
    assert {"diagnostic_trace", "temporary_intermediate"}.issubset(extracted.omitted_item_ids)
    assert {"core_state", "memory_state"} == set(extracted.materialized)
    assert contract.contract_id.startswith("r6ret_")

    full_next = _evolve(raw["core_state"], raw["memory_state"], raw["forcing_value"])
    assert raw["derived_display"] == sum(
        extracted.materialized[key][0].value["value"] for key in ("core_state", "memory_state"))

    store = HistoryStore(tmp_path / "history")
    provenance = ProvenanceRecord.create(activity="fixture-minimal-extraction",
                                          input_refs=(str(forcing.forcing_id),),
                                          source_refs=("fixture:source",))
    for states in extracted.materialized.values():
        record = states[0]
        with_provenance = DomainStateEnvelope.create(
            history_id=record.history_id, branch_id=record.branch_id, domain=record.domain,
            time_support=record.time_support, spatial_support=record.spatial_support,
            support_class=record.support_class, authority_class=record.authority_class,
            value=record.value, uncertainty=record.uncertainty,
            provenance_ids=(str(provenance.record_id),))
        store.append_state(with_provenance)
        if record.domain == "fixture:core_state":
            core_id = str(with_provenance.state_id)
    store.append_transaction((forcing, provenance))

    reopened = HistoryStore(tmp_path / "history")
    query = HistoryQueryService(reopened)
    result = query.state_at(history_id=HISTORY, branch_id=BRANCH,
                            domain="fixture:core_state", time_key=TIME.time_key,
                            cell_id="cell-1")
    assert result.status == "FOUND"
    assert len(query.history_result(history_id=HISTORY, branch_id=BRANCH).states) == 2
    reopened_states = {state.domain.removeprefix("fixture:"): state
                       for state in query.history(history_id=HISTORY, branch_id=BRANCH)}
    assert raw["derived_display"] == sum(
        reopened_states[key].value["value"] for key in ("core_state", "memory_state"))
    minimal_next = _evolve(reopened_states["core_state"].value["value"],
                           reopened_states["memory_state"].value["value"],
                           forcing.value["increment"])
    assert minimal_next == full_next
    assert minimal_next["core_state"] == 21
    expected = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, domain="future_state", time_support=TIME,
        spatial_support=SpatialSupport("fixture-grid", ("cell-1",)),
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value=full_next, uncertainty={"fixture": True}, provenance_ids=(str(provenance.record_id),))
    replay_branch = str(BranchId.from_payload({"fixture": "b0-g-replay"}))
    replayed = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=replay_branch, domain="future_state", time_support=TIME,
        spatial_support=SpatialSupport("fixture-grid", ("cell-1",)),
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value=minimal_next, uncertainty={"fixture": True}, provenance_ids=(str(provenance.record_id),))
    reopened.append_transaction((expected, replayed))
    comparison = HistoryQueryService(HistoryStore(tmp_path / "history")).difference(
        str(expected.state_id), str(replayed.state_id))
    assert comparison.status is DifferenceStatus.COMPARABLE
    assert comparison.equal is True
    explanation = query.why(core_id)
    assert str(forcing.forcing_id) in {str(record.forcing_id) for record in explanation.forcings}
    assert explanation.unresolved_references == ()


def test_required_future_memory_cannot_be_dropped_or_reclassified_discard():
    forcing = _forcing()
    contract = _contract(str(forcing.forcing_id))
    extraction = extract_minimal_state(_raw(forcing), contract, FixtureExtractor())
    broken = MinimalStateExtractionResult(contract.contract_id,
        {"core_state": extraction.materialized["core_state"]},
        forcing_identities=(str(forcing.forcing_id),),
        omitted_item_ids=extraction.omitted_item_ids + ("memory_state",))
    checked = validate_extraction(contract, broken)
    assert checked.validation_status == "FAIL"
    assert any("required persistent state missing: memory_state" in error
               for error in checked.validation_errors)
    with pytest.raises(ValueError, match="future system memory"):
        MinimalStateContract("fixture-adapter-v1", (
            RetentionItem("memory", RetentionAction.DISCARD, InformationRole.SYSTEM_MEMORY),))


@pytest.mark.parametrize("item", [
    RetentionItem("derived", RetentionAction.DERIVE, InformationRole.QUERY_OUTPUT),
    RetentionItem("refine", RetentionAction.REFINE, InformationRole.QUERY_OUTPUT),
    RetentionItem("static", RetentionAction.STATIC, InformationRole.INPUT),
    RetentionItem("forcing", RetentionAction.FORCING, InformationRole.INPUT),
])
def test_reconstructable_actions_require_explicit_anchors(item):
    with pytest.raises(ValueError):
        MinimalStateContract("adapter", (item,))


def test_missing_forcing_scope_duplicate_and_branch_mismatch_fail_closed():
    forcing = _forcing()
    contract = _contract(str(forcing.forcing_id))
    extracted = extract_minimal_state(_raw(forcing), contract, FixtureExtractor())
    missing = MinimalStateExtractionResult(contract.contract_id, extracted.materialized,
        forcing_identities=(), omitted_item_ids=extracted.omitted_item_ids)
    assert "forcing dependency missing: forcing" in validate_extraction(contract, missing).validation_errors
    missing_recipe = MinimalStateExtractionResult(contract.contract_id, extracted.materialized,
        forcing_identities=(str(forcing.forcing_id),), omitted_item_ids=extracted.omitted_item_ids)
    assert any("reconstruction identity missing" in error for error in
               validate_extraction(contract, missing_recipe).validation_errors)
    missing_parent = MinimalStateExtractionResult(contract.contract_id,
        {"memory_state": extracted.materialized["memory_state"]},
        forcing_identities=(str(forcing.forcing_id),),
        reconstruction_identities=("recipe:display-v1",),
        omitted_item_ids=extracted.omitted_item_ids + ("core_state",))
    parent_errors = validate_extraction(contract, missing_parent).validation_errors
    assert any("required persistent state missing: core_state" in error for error in parent_errors)
    assert any("retained parent state missing" in error for error in parent_errors)
    duplicate = RetentionItem("core_state", RetentionAction.DISCARD, InformationRole.DIAGNOSTIC)
    with pytest.raises(ValueError, match="duplicate/conflicting"):
        MinimalStateContract("adapter", (duplicate, duplicate))
    other_branch_state = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=str(BranchId.from_payload({"other": 1})), domain="fixture",
        time_support=TIME, spatial_support=SpatialSupport(None, (), None, "GLOBAL"),
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"x": 1})
    wrong = MinimalStateExtractionResult(contract.contract_id,
        {"core_state": (other_branch_state,), "memory_state": extracted.materialized["memory_state"]},
        forcing_identities=(str(forcing.forcing_id),), omitted_item_ids=extracted.omitted_item_ids)
    assert any("branch scope mismatch" in e for e in validate_extraction(
        contract, wrong, history_id=HISTORY, branch_id=BRANCH).validation_errors)


def _write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_storage_categories_dedup_optional_required_and_cap(tmp_path):
    metadata = tmp_path / "metadata"
    payload = tmp_path / "payload" / "shared.bin"
    cache = tmp_path / "cache"
    _write(metadata / "manifest.json", b"abc")
    _write(payload, b"12345")
    _write(cache / "c.bin", b"x")
    scope = AccountingScope((
        AccountingRoot(metadata, StorageCategory.CANONICAL_METADATA),
        AccountingRoot(cache, StorageCategory.PROVIDER_CACHE),
        AccountingRoot(tmp_path / "absent", StorageCategory.SCRATCH, required=False, label="optional scratch"),
    ), external_payloads=(payload, payload))
    report = account_storage(scope, hard_cap_bytes=9)
    assert report.categories[StorageCategory.CANONICAL_METADATA.value].logical_bytes == 3
    assert report.categories[StorageCategory.CANONICAL_PAYLOAD.value].file_count == 1
    assert report.categories[StorageCategory.CANONICAL_PAYLOAD.value].logical_bytes == 5
    assert report.categories[StorageCategory.PROVIDER_CACHE.value].logical_bytes == 1
    assert report.canonical_persistent_bytes == 8
    assert report.within_hard_cap is True
    assert report.missing_optional_roots == ("optional scratch",)
    assert account_storage(scope, hard_cap_bytes=8).within_hard_cap is False


def test_storage_rejects_overlapping_and_missing_required_roots(tmp_path):
    parent = tmp_path / "parent"
    child = parent / "child"
    _write(child / "f", b"x")
    with pytest.raises(StorageAccountingError, match="overlapping"):
        account_storage(AccountingScope((
            AccountingRoot(parent, StorageCategory.CANONICAL_METADATA),
            AccountingRoot(child, StorageCategory.INDEX))))
    with pytest.raises(StorageAccountingError, match="required"):
        account_storage(AccountingScope((
            AccountingRoot(tmp_path / "missing", StorageCategory.INDEX),)))


def test_storage_order_is_deterministic_and_symlinks_are_excluded(tmp_path):
    root = tmp_path / "root"
    _write(root / "z", b"zz")
    _write(root / "a", b"a")
    target = root / "a"
    link = root / "link"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        link = None
    scope = AccountingScope((AccountingRoot(root, StorageCategory.INDEX),))
    first = account_storage(scope)
    second = account_storage(scope)
    assert first.files == second.files
    assert [Path(row[1]).name for row in first.files] == ["a", "z"]
    if link is not None:
        assert any(Path(item).name == "link" for item in first.symlinks_excluded)
        assert first.categories[StorageCategory.INDEX.value].file_count == 2


def test_history_store_accounting_and_shared_payload_count_once(tmp_path):
    store = HistoryStore(tmp_path / "store")
    report = account_storage(history_store_scope(store))
    assert report.categories[StorageCategory.CANONICAL_METADATA.value].file_count == 1
    assert report.canonical_persistent_bytes > 0
    payload = tmp_path / "external" / "payload.bin"
    _write(payload, b"payload")
    shared = history_store_scope(store, external_payloads=(payload, payload))
    measured = account_storage(shared)
    assert measured.categories[StorageCategory.CANONICAL_PAYLOAD.value].file_count == 1
    assert measured.categories[StorageCategory.CANONICAL_PAYLOAD.value].logical_bytes == 7


def test_initial_world_inventory_requires_domain_adapter_not_rewrite():
    # The materializer emits one packed NPZ and multiple semantic state records
    # with shared payload references; retention decisions require field-level
    # domain selection and therefore an adapter around its existing interface.
    from arcana_worldsim.r6.initial_world.model import InitialWorldFields
    assert "arrays" in InitialWorldFields.__dict__
    assert "metadata" in InitialWorldFields.__dataclass_fields__
    assert "payload_ref" in DomainStateEnvelope.__dataclass_fields__
