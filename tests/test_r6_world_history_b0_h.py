"""Integrated synthetic qualification of the existing R6 WORLD_HISTORY core."""

from __future__ import annotations

import json
import shutil

import pytest

from arcana_worldsim.r6.checkpoint import CheckpointEnvelope, RefinementBranchEnvelope
from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.identity import (
    BranchId, EventId, HistoryId, PayloadIdentity, canonical_bytes, content_hash,
)
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import DifferenceStatus, HistoryQueryService
from arcana_worldsim.r6.refinement import (
    RefinementExecutionOutput, RefinementOutputManifestEntry,
    RefinementReconstructionRecipe, execute_refinement,
)
from arcana_worldsim.r6.replay import (
    ReplayExecutionOutput, ReplayRecipe, execute_replay,
)
from arcana_worldsim.r6.retention import (
    InformationRole, MinimalStateContract, MinimalStateExtractionResult,
    RetentionAction, RetentionItem, extract_minimal_state,
)
from arcana_worldsim.r6.state import (
    AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport,
)
from arcana_worldsim.r6.storage import (
    AccountingRoot, AccountingScope, StorageCategory, account_storage,
    history_store_scope,
)
from arcana_worldsim.r6.store import (
    HistoryStore, RecordIntegrityError, TransactionRecoveryError,
)
from arcana_worldsim.r6.temporal import EventRecord
from arcana_worldsim.r6.identity import verify_payload, PayloadIntegrityError


class _SimulatedProcessInterruption(BaseException):
    pass


HISTORY = str(HistoryId.from_payload({"fixture": "b0-h-history-v1"}))
PARENT_BRANCH = str(BranchId.from_payload({"fixture": "b0-h-parent-v1"}))
T0 = TimeSupport("fixture:t0", "fixture-clock", "SNAPSHOT")
T1 = TimeSupport("fixture:t1", "fixture-clock", "SNAPSHOT")
SPACE = SpatialSupport("fixture-grid", ("cell-1",), "one-cell", "CELL_SET")
RUNTIME = {"adapter": "fixture-arithmetic-v1", "version": 1}
CONFIG = {"operation": "core + memory + forcing"}
SEED = {"seed": 41}


def _state(domain, time, value, provenance_id, *, payload_ref=None, support=SupportClass.FIXTURE_ONLY,
           space=SPACE, parents=(), events=()):
    return DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=PARENT_BRANCH, domain=domain,
        time_support=time, spatial_support=space, support_class=support,
        authority_class=(AuthorityClass.FIXTURE_ONLY if support is SupportClass.FIXTURE_ONLY
                         else AuthorityClass.NONE), value=value,
        uncertainty={"fixture_only": True}, provenance_ids=(provenance_id,) if provenance_id else (),
        parent_state_ids=parents, payload_ref=payload_ref, event_refs=events)


class _FixtureExtractor:
    adapter_id = "b0-h-fixture-extractor-v1"

    def extract(self, raw, contract):
        payload_ref = raw["payload_ref"]
        fields = {
            "core_state": ("fixture-main", raw["core_state"], SupportClass.FIXTURE_ONLY, SPACE),
            "memory_state": ("fixture-memory", raw["memory_state"], SupportClass.FIXTURE_ONLY, SPACE),
            "known_zero": ("fixture-zero", 0, SupportClass.FIXTURE_ONLY, SPACE),
            "known_false": ("fixture-flag", False, SupportClass.FIXTURE_ONLY, SPACE),
            "unknown_state": ("fixture-unknown", None, SupportClass.UNKNOWN, SPACE),
            "outside_state": ("fixture-outside", None, SupportClass.OUTSIDE_SCOPE, SPACE),
            "region_state": ("fixture-region", 9, SupportClass.FIXTURE_ONLY,
                             SpatialSupport("fixture-region-grid", (), "coarse", "REGION")),
        }
        records = {}
        for key, (domain, value, support, spatial) in fields.items():
            records[key] = (_state(domain, T0, value, raw["provenance_id"],
                                   payload_ref=payload_ref if support is SupportClass.FIXTURE_ONLY else None,
                                   support=support, space=spatial),)
        return MinimalStateExtractionResult(
            contract.contract_id, records,
            forcing_identities=(raw["forcing_id"],),
            reconstruction_identities=("recipe:fixture-display-v1",),
            omitted_item_ids=("derived_display", "forcing", "diagnostic_trace",
                              "temporary_intermediate"))


def _replay_runner(recipe, inputs):
    by_domain = {state.domain: state for state in inputs.base_states}
    core = by_domain["fixture-main"].value
    memory = by_domain["fixture-memory"].value
    result_value = {"value": core + memory + inputs.forcings[0].value,
                    "memory": memory + inputs.forcings[0].value}
    payload = canonical_bytes(result_value)
    digest = PayloadIdentity.from_bytes(payload)
    output = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=PARENT_BRANCH, domain="fixture-main", time_support=T1,
        spatial_support=SPACE, support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.FIXTURE_ONLY, value=result_value,
        uncertainty={"fixture_only": True}, provenance_ids=recipe.provenance_ids,
        parent_state_ids=tuple(str(state.state_id) for state in inputs.base_states),
        payload_ref=f"sha256:{digest.digest}", event_refs=recipe.event_ids)
    return ReplayExecutionOutput(output, payload)


def _refinement_runner(inputs):
    parent = inputs.parent_states[0]
    offsets = inputs.boundary_conditions["offsets"]
    result = []
    for index, entry in enumerate(inputs.recipe.output_manifest):
        value = parent.value + offsets[index]
        payload = canonical_bytes({"cell": entry.child_cell_ids[0], "value": value})
        identity = PayloadIdentity.from_bytes(payload)
        state = DomainStateEnvelope.create(
            history_id=HISTORY, branch_id=str(inputs.branch.branch_id),
            domain="fixture-refined", time_support=T0,
            spatial_support=SpatialSupport("fixture-fine-grid", entry.child_cell_ids,
                                           "fine", "CELL_SET"),
            support_class=SupportClass.FIXTURE_ONLY,
            authority_class=AuthorityClass.FIXTURE_ONLY, value={"value": value},
            uncertainty={"fixture_only": True}, provenance_ids=parent.provenance_ids,
            parent_state_ids=(str(parent.state_id),),
            payload_ref=f"sha256:{identity.digest}",
            refinement_lineage={"parent_cell_ids": list(entry.parent_cell_ids),
                                "child_branch": str(inputs.branch.branch_id)})
        result.append(RefinementExecutionOutput(state, payload))
    return tuple(result)


def _build_records(*, reverse=False):
    payload = canonical_bytes({"fixture": "shared-payload", "version": 1})
    payload_identity = PayloadIdentity.from_bytes(payload)
    payload_ref = f"sha256:{payload_identity.digest}"
    forcing = ForcingRecord.create(
        history_id=HISTORY, branch_id=PARENT_BRANCH, forcing_kind="synthetic-increment",
        domain="fixture-force", time_support=T0, spatial_support=SPACE,
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value=3, source_refs=("fixture:forcing-source",))
    provenance = ProvenanceRecord.create(
        activity="B0_H_SYNTHETIC_BOOTSTRAP",
        input_refs=(str(forcing.forcing_id),), source_refs=("fixture:authority-v1",),
        attributes={"authority": "FIXTURE_ONLY"})
    contract = MinimalStateContract("b0-h-fixture-extractor-v1", (
        *(RetentionItem(name, RetentionAction.MATERIALIZE,
                        InformationRole.SYSTEM_MEMORY if name == "memory_state"
                        else InformationRole.QUERY_OUTPUT)
          for name in ("core_state", "memory_state", "known_zero", "known_false",
                       "unknown_state", "outside_state", "region_state")),
        RetentionItem("derived_display", RetentionAction.DERIVE, InformationRole.QUERY_OUTPUT,
                      reconstruction_refs=("recipe:fixture-display-v1", "parent:core_state")),
        RetentionItem("forcing", RetentionAction.FORCING, InformationRole.INPUT,
                      reconstruction_refs=(f"forcing:{forcing.forcing_id}",)),
        RetentionItem("diagnostic_trace", RetentionAction.DISCARD, InformationRole.DIAGNOSTIC),
        RetentionItem("temporary_intermediate", RetentionAction.DISCARD, InformationRole.INTERMEDIATE),
    ))
    raw = {"core_state": 2, "memory_state": 5, "derived_display": 7,
           "forcing_value": 3, "forcing_id": str(forcing.forcing_id),
           "provenance_id": str(provenance.record_id), "payload_ref": payload_ref,
           "diagnostic_trace": ["trace omitted"], "temporary_intermediate": {"scratch": True}}
    extraction = extract_minimal_state(raw, contract, _FixtureExtractor(),
                                       history_id=HISTORY, branch_id=PARENT_BRANCH)
    assert extraction.validation_status == "PASS", extraction.validation_errors
    states = {key: value[0] for key, value in extraction.materialized.items()}
    core, memory = states["core_state"], states["memory_state"]
    event = EventRecord.create(
        history_id=HISTORY, branch_id=PARENT_BRANCH, time_key=T0.time_key,
        domain_ids=("fixture-main", "fixture-memory"),
        state_ids=(str(core.state_id), str(memory.state_id)),
        provenance_refs=(str(provenance.record_id),), trigger_ref=str(forcing.forcing_id),
        causal_dependency_ids=(str(forcing.forcing_id), str(provenance.record_id)),
        details={"meaning": "synthetic input event"})
    checkpoint = CheckpointEnvelope.create(
        history_id=HISTORY, branch_id=PARENT_BRANCH, time_key=T0.time_key,
        restart_state_ids=(str(core.state_id), str(memory.state_id)),
        retained_history_state_ids=tuple(sorted(str(state.state_id) for state in states.values())),
        runtime_identity=RUNTIME, configuration=CONFIG, seed_lineage=SEED,
        upstream_dependency_ids=(str(provenance.record_id),))
    output_value = {"value": raw["core_state"] + raw["memory_state"] + raw["forcing_value"],
                    "memory": raw["memory_state"] + raw["forcing_value"]}
    output_payload = canonical_bytes(output_value)
    output_identity = PayloadIdentity.from_bytes(output_payload)
    expected = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=PARENT_BRANCH, domain="fixture-main", time_support=T1,
        spatial_support=SPACE, support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.FIXTURE_ONLY, value=output_value,
        uncertainty={"fixture_only": True}, provenance_ids=(str(provenance.record_id),),
        parent_state_ids=(str(core.state_id), str(memory.state_id)),
        payload_ref=f"sha256:{output_identity.digest}", event_refs=(event.record_id,))
    recipe = ReplayRecipe.create(
        history_id=HISTORY, branch_id=PARENT_BRANCH,
        base_checkpoint_id=str(checkpoint.checkpoint_id), runtime_identity=RUNTIME,
        configuration_sha256=content_hash(CONFIG), seed_lineage=SEED,
        forcing_ids=(str(forcing.forcing_id),), event_ids=(event.record_id,),
        upstream_dependency_ids=(str(provenance.record_id),),
        provenance_ids=(str(provenance.record_id),),
        expected_output_state_id=str(expected.state_id),
        expected_payload_identity=output_identity, model_adapter_id="fixture:b0-h-arithmetic-v1")
    initial_records = [*states.values(), provenance, event, forcing, checkpoint, expected, recipe]
    if reverse:
        initial_records.reverse()
    return {"records": initial_records, "states": states, "provenance": provenance,
            "event": event, "forcing": forcing, "checkpoint": checkpoint,
            "expected": expected, "recipe": recipe, "payload": payload,
            "output_payload": output_payload, "payload_identity": payload_identity,
            "contract": contract, "extraction": extraction, "raw": raw}


def _make_refinement(bundle):
    parent = bundle["states"]["core_state"]
    provenance = bundle["provenance"]
    checkpoint = bundle["checkpoint"]
    boundary = {"offsets": [1, 2], "boundary_id": "fixture-boundary-v1"}
    branch = RefinementBranchEnvelope.create(
        history_id=HISTORY, parent_branch_id=PARENT_BRANCH, base_history_id=HISTORY,
        refinement_anchor_id="fixture:anchor:t0", region_id="fixture-region",
        time_interval=(T0.time_key, T0.time_key), requested_domains=("fixture-refined",),
        requested_resolution="fixture-fine-grid", parent_boundary_conditions=boundary,
        provenance_refs=(str(provenance.record_id),))
    child_cells = ("child-1", "child-2")
    outputs = []
    for cell, offset in zip(child_cells, boundary["offsets"]):
        value = parent.value + offset
        payload = canonical_bytes({"cell": cell, "value": value})
        identity = PayloadIdentity.from_bytes(payload)
        state = DomainStateEnvelope.create(
            history_id=HISTORY, branch_id=str(branch.branch_id), domain="fixture-refined",
            time_support=T0, spatial_support=SpatialSupport("fixture-fine-grid", (cell,), "fine"),
            support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
            value={"value": value}, uncertainty={"fixture_only": True},
            provenance_ids=(str(provenance.record_id),), parent_state_ids=(str(parent.state_id),),
            payload_ref=f"sha256:{identity.digest}",
            refinement_lineage={"parent_cell_ids": ["cell-1"], "child_branch": str(branch.branch_id)})
        outputs.append((state, payload, identity))
    manifest = tuple(RefinementOutputManifestEntry(
        str(state.state_id), ("cell-1",), tuple(state.spatial_support.cell_ids), identity)
        for state, _payload, identity in outputs)
    recipe = RefinementReconstructionRecipe.create(
        branch=branch, base_checkpoint_id=str(checkpoint.checkpoint_id),
        parent_state_ids=(str(parent.state_id),), parent_region_cell_ids=("cell-1",),
        runtime_identity=RUNTIME, configuration_sha256=content_hash({"refinement": boundary}),
        seed_lineage=SEED, model_adapter_id="fixture:b0-h-refinement-v1",
        output_manifest=manifest, materialization_status="DECLARED")
    materialized = RefinementReconstructionRecipe.create(
        branch=branch, base_checkpoint_id=str(checkpoint.checkpoint_id),
        parent_state_ids=(str(parent.state_id),), parent_region_cell_ids=("cell-1",),
        runtime_identity=RUNTIME, configuration_sha256=content_hash({"refinement": boundary}),
        seed_lineage=SEED, model_adapter_id="fixture:b0-h-refinement-v1",
        output_manifest=manifest, materialization_status="MATERIALIZED")
    return branch, recipe, materialized, tuple(outputs)


def _publish_initial(root, bundle, *, interrupt=False):
    if interrupt:
        def fail(stage, count):
            if (stage, count) == ("after_publication", 1):
                raise _SimulatedProcessInterruption("fixture interruption")
        store = HistoryStore(root, _fault_injector=fail)
        with pytest.raises(_SimulatedProcessInterruption, match="fixture interruption"):
            store.append_transaction(bundle["records"])
        recovered = HistoryStore(root)
        published_state_ids = {str(state.state_id) for state in recovered.states()}
        bundle_state_ids = {str(state.state_id) for state in bundle["states"].values()}
        assert not (published_state_ids & bundle_state_ids)
        return recovered
    store = HistoryStore(root)
    store.append_transaction(bundle["records"])
    return store


def _integrated_lifecycle(root, *, reverse=False):
    bundle = _build_records(reverse=reverse)
    store = _publish_initial(root, bundle, interrupt=True)
    # Retrying after recovery publishes one complete logical initial bundle.
    store.append_transaction(bundle["records"])
    first_ids = {"states": tuple(sorted(str(state.state_id) for state in store.states())),
                 "forcing": tuple(str(item.forcing_id) for item in store.forcings()),
                 "event": tuple(item.record_id for item in store.events()),
                 "checkpoint": tuple(str(item.checkpoint_id) for item in store.checkpoints()),
                 "recipe": tuple(str(item.recipe_id) for item in store.replay_recipes())}
    del store

    # A new store instance verifies real filesystem reopen and all typed readers.
    store = HistoryStore(root)
    assert store.states() and store.events() and store.forcings()
    assert store.read_provenance(str(bundle["provenance"].record_id))
    assert store.checkpoints() and store.replay_recipes()
    assert store.read_replay_recipe(str(bundle["recipe"].recipe_id)) == bundle["recipe"]
    assert store.read_checkpoint(str(bundle["checkpoint"].checkpoint_id)) == bundle["checkpoint"].to_dict()
    assert store.read_state(str(bundle["states"]["core_state"].state_id)).state_id == \
        bundle["states"]["core_state"].state_id
    assert bundle["states"]["core_state"].state_id != bundle["states"]["memory_state"].state_id
    assert bundle["states"]["core_state"].payload_ref == bundle["states"]["memory_state"].payload_ref

    query = HistoryQueryService(store)
    core = bundle["states"]["core_state"]
    q = query.state_at(history_id=HISTORY, branch_id=PARENT_BRANCH,
                       domain="fixture-main", time_key=T0.time_key, cell_id="cell-1")
    assert q.status == "FOUND" and q.state.state_id == core.state_id
    assert query.state_at(history_id=HISTORY, branch_id=PARENT_BRANCH,
        domain="fixture-zero", time_key=T0.time_key).state.value == 0
    assert query.state_at(history_id=HISTORY, branch_id=PARENT_BRANCH,
        domain="fixture-flag", time_key=T0.time_key).state.value is False
    assert query.state_at(history_id=HISTORY, branch_id=PARENT_BRANCH,
        domain="fixture-unknown", time_key=T0.time_key).status == "UNKNOWN"
    assert query.state_at(history_id=HISTORY, branch_id=PARENT_BRANCH,
        domain="fixture-outside", time_key=T0.time_key).status == "OUTSIDE_SCOPE"
    assert query.state_at(history_id=HISTORY, branch_id=PARENT_BRANCH,
        domain="missing", time_key=T0.time_key).status == "MISSING_DOMAIN"
    assert query.state_at(history_id=HISTORY, branch_id=PARENT_BRANCH,
        domain="fixture-main", time_key="fixture:missing").status == "MISSING_TIMESTAMP"
    assert query.state_at(history_id=HISTORY, branch_id=PARENT_BRANCH,
        domain="fixture-main", time_key=T0.time_key, cell_id="not-declared").status == "OUTSIDE_SUPPORT"
    assert query.state_at(history_id=HISTORY, branch_id=PARENT_BRANCH,
        domain="fixture-region", time_key=T0.time_key, cell_id="cell-1").status == "SUPPORT_MISMATCH"
    assert query.why(str(core.state_id)).target_state.state_id == core.state_id

    # Expected output already exists as replay contract data; executor remains read-only.
    before_replay_state_ids = {str(state.state_id) for state in store.states()}
    recipe = store.read_replay_recipe(str(bundle["recipe"].recipe_id))
    replay = execute_replay(store, recipe, _replay_runner)
    assert replay.status == "VERIFIED"
    assert replay.produced_state_id == str(bundle["expected"].state_id)
    assert replay.produced_payload_identity == recipe.expected_payload_identity
    assert {str(state.state_id) for state in store.states()} == before_replay_state_ids
    assert bundle["expected"].authority_class is AuthorityClass.FIXTURE_ONLY
    store.append_state(bundle["expected"])

    zero_t1 = _state("fixture-zero", T1, 0, str(bundle["provenance"].record_id),
                     payload_ref=bundle["states"]["known_zero"].payload_ref)
    flag_t1 = _state("fixture-flag", T1, True, str(bundle["provenance"].record_id),
                     payload_ref=bundle["states"]["known_false"].payload_ref)
    store.append_transaction((zero_t1, flag_t1))
    zero_diff = query.difference(str(bundle["states"]["known_zero"].state_id), str(zero_t1.state_id))
    flag_diff = query.difference(str(bundle["states"]["known_false"].state_id), str(flag_t1.state_id))
    unknown_diff = query.difference(str(bundle["states"]["unknown_state"].state_id),
                                    str(bundle["expected"].state_id))
    assert zero_diff.status is DifferenceStatus.COMPARABLE and zero_diff.equal is True
    assert flag_diff.status is DifferenceStatus.COMPARABLE and flag_diff.equal is False
    assert unknown_diff.status is DifferenceStatus.UNKNOWN_INPUT
    main_history = query.history_result(history_id=HISTORY, branch_id=PARENT_BRANCH,
                                        domain="fixture-main").states
    assert tuple(item.time_support.time_key for item in main_history) == (T0.time_key, T1.time_key)

    explanation = query.why(str(bundle["expected"].state_id))
    assert str(bundle["recipe"].recipe_id) in {str(x.recipe_id) for x in explanation.replay_recipes}
    assert str(bundle["checkpoint"].checkpoint_id) in {str(x.checkpoint_id) for x in explanation.checkpoints}
    assert str(core.state_id) in {str(x.state_id) for x in explanation.state_lineage}
    assert str(bundle["forcing"].forcing_id) in {str(x.forcing_id) for x in explanation.forcings}
    assert bundle["event"].record_id in {x.record_id for x in explanation.events}
    assert str(bundle["provenance"].record_id) in {str(x.record_id) for x in explanation.provenance_records}
    assert "fixture:authority-v1" in explanation.external_references

    # A real filesystem payload is independently verified and separately accounted.
    payload_root = root.parent / (root.name + "_payloads")
    payload_root.mkdir(parents=True, exist_ok=True)
    shared_path = payload_root / "shared.bin"
    shared_path.write_bytes(bundle["payload"])
    assert verify_payload(bundle["states"]["core_state"].payload_ref, shared_path) == \
        bundle["payload_identity"]
    output_path = payload_root / "replay-output.bin"
    output_path.write_bytes(bundle["output_payload"])
    assert verify_payload(bundle["expected"].payload_ref, output_path) == recipe.expected_payload_identity

    # Declare, execute, materialize and reopen an isolated child refinement.
    branch, declared, materialized, expected_children = _make_refinement(bundle)
    refinement_result = execute_refinement(store, branch, declared, _refinement_runner)
    assert refinement_result.status == "VERIFIED", refinement_result.mismatches
    parent_state_path = root / "states" / f"{core.state_id}.json"
    parent_bytes_before = parent_state_path.read_bytes()
    parent_state_ids_before = {str(item.state_id) for item in query.history(
        history_id=HISTORY, branch_id=PARENT_BRANCH)}
    child_records = (bundle["provenance"], *(state for state, _payload, _identity in expected_children))
    store.append_refinement_transaction(branch, materialized, child_records)
    assert parent_state_path.read_bytes() == parent_bytes_before
    assert {str(item.state_id) for item in query.history(history_id=HISTORY,
        branch_id=PARENT_BRANCH)} == parent_state_ids_before
    child_states = query.history(history_id=HISTORY, branch_id=str(branch.branch_id))
    assert len(child_states) == len(expected_children)
    child_why = query.why(str(child_states[0].state_id))
    assert str(core.state_id) in {str(x.state_id) for x in child_why.state_lineage}
    assert child_states[0].authority_class is AuthorityClass.FIXTURE_ONLY
    assert query.difference(str(core.state_id), str(child_states[0].state_id)).status is \
        DifferenceStatus.INCOMPATIBLE_SUPPORT

    storage_scope = history_store_scope(store, external_payloads=(shared_path, shared_path, output_path))
    storage = account_storage(storage_scope, hard_cap_bytes=10**9)
    assert storage.categories[StorageCategory.CANONICAL_METADATA.value].file_count > 0
    assert storage.categories[StorageCategory.CANONICAL_PAYLOAD.value].file_count == 2
    assert storage.categories[StorageCategory.OPERATIONAL_METADATA.value].file_count >= 0
    assert storage.within_hard_cap is True
    scratch = root.parent / (root.name + "_scratch")
    scratch.mkdir(exist_ok=True)
    (scratch / "scratch.tmp").write_bytes(b"scratch")
    scoped = account_storage(AccountingScope((
        AccountingRoot(root / "metadata", StorageCategory.CANONICAL_METADATA),
        AccountingRoot(scratch, StorageCategory.SCRATCH),
    )), hard_cap_bytes=1)
    assert scoped.canonical_persistent_bytes < storage.canonical_persistent_bytes
    assert not scoped.within_hard_cap

    final_ids = {"states": tuple(sorted(str(state.state_id) for state in store.states())),
                 "parent_history": tuple(str(x.state_id) for x in query.history(
                     history_id=HISTORY, branch_id=PARENT_BRANCH)),
                 "child_history": tuple(str(x.state_id) for x in query.history(
                     history_id=HISTORY, branch_id=str(branch.branch_id))),
                 "replay": replay.produced_state_id,
                 "refinement": refinement_result.produced_state_ids,
                 "retention": tuple(sorted(bundle["extraction"].materialized)),
                 "accounting": (storage.canonical_persistent_bytes, storage.within_hard_cap)}

    # Second close/reopen must reproduce queries, WHY, replay, refinement and accounting.
    del query, store
    reopened = HistoryStore(root)
    query2 = HistoryQueryService(reopened)
    assert {"states": tuple(sorted(str(state.state_id) for state in reopened.states())),
            "parent_history": tuple(str(x.state_id) for x in query2.history(
                history_id=HISTORY, branch_id=PARENT_BRANCH)),
            "child_history": tuple(str(x.state_id) for x in query2.history(
                history_id=HISTORY, branch_id=str(branch.branch_id))),
            "replay": execute_replay(reopened, reopened.read_replay_recipe(
                str(bundle["recipe"].recipe_id)), _replay_runner).produced_state_id,
            "refinement": execute_refinement(reopened,
                reopened.read_refinement_branch(str(branch.branch_id)),
                reopened.read_refinement_recipe(str(materialized.recipe_id)),
                _refinement_runner).produced_state_ids,
            "retention": tuple(sorted(bundle["extraction"].materialized)),
            "accounting": (account_storage(history_store_scope(
                reopened, external_payloads=(shared_path, shared_path, output_path)),
                hard_cap_bytes=10**9).canonical_persistent_bytes, True)} == final_ids
    assert query2.difference(str(bundle["states"]["known_zero"].state_id), str(zero_t1.state_id)).equal
    assert query2.why(str(bundle["expected"].state_id)).unresolved_references == ()

    return {"bundle": bundle, "final_ids": final_ids, "main_history": main_history,
            "storage": storage, "branch": branch, "recipe": materialized,
            "expected_children": expected_children, "first_ids": first_ids,
            "reopened": reopened}


def test_full_synthetic_world_history_lifecycle_and_deterministic_second_build(tmp_path):
    first = _integrated_lifecycle(tmp_path / "history-a")
    second = _integrated_lifecycle(tmp_path / "history-b", reverse=True)
    assert first["final_ids"] == second["final_ids"]
    assert first["first_ids"] == second["first_ids"]
    assert first["main_history"] == second["main_history"]
    assert first["storage"].canonical_persistent_bytes == second["storage"].canonical_persistent_bytes


def test_integrated_corruption_and_ambiguous_journal_fail_closed(tmp_path):
    bundle = _build_records()
    root = tmp_path / "source"
    store = _publish_initial(root, bundle)
    corrupted = tmp_path / "corrupted"
    shutil.copytree(root, corrupted)
    state_path = corrupted / "states" / f"{bundle['states']['core_state'].state_id}.json"
    row = json.loads(state_path.read_text())
    row["value"] = 99
    state_path.write_text(json.dumps(row))
    with pytest.raises(RecordIntegrityError):
        HistoryStore(corrupted).read_state(str(bundle["states"]["core_state"].state_id))

    payload_file = tmp_path / "payload.bin"
    payload_file.write_bytes(bundle["payload"] + b"tamper")
    with pytest.raises(PayloadIntegrityError):
        verify_payload(bundle["states"]["core_state"].payload_ref, payload_file)

    forcing_store = HistoryStore(tmp_path / "forcing-corrupt")
    forcing_store.append_transaction(bundle["records"])
    forcing_path = forcing_store.root / "forcings" / f"{bundle['forcing'].forcing_id}.json"
    forcing_row = json.loads(forcing_path.read_text())
    forcing_row["value"] = 999
    forcing_path.write_text(json.dumps(forcing_row))
    with pytest.raises(RecordIntegrityError):
        HistoryStore(forcing_store.root).forcings()

    branch, _declared, materialized, children = _make_refinement(bundle)
    refinement_store = HistoryStore(tmp_path / "refinement-corrupt")
    refinement_store.append_transaction(bundle["records"])
    refinement_store.append_refinement_transaction(
        branch, materialized, (bundle["provenance"], *(state for state, _payload, _ in children)))
    recipe_path = refinement_store.root / "refinement_recipes" / f"{materialized.recipe_id}.json"
    recipe_row = json.loads(recipe_path.read_text())
    recipe_row["parent_region_cell_ids"] = ["forged"]
    recipe_path.write_text(json.dumps(recipe_row))
    with pytest.raises(RecordIntegrityError):
        HistoryStore(refinement_store.root).read_refinement_recipe(str(materialized.recipe_id))

    journal_root = tmp_path / "journal-corrupt"
    def interrupt(stage, count):
        if (stage, count) == ("after_publication", 1):
            raise _SimulatedProcessInterruption("interrupted")
    with pytest.raises(_SimulatedProcessInterruption, match="interrupted"):
        HistoryStore(journal_root, _fault_injector=interrupt).append_transaction(bundle["records"])
    transaction = next(path for path in (journal_root / ".history_transactions").iterdir()
                       if path.name != ".retired")
    manifest_path = transaction / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["entries"][0]["preexisting"] = not manifest["entries"][0]["preexisting"]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(TransactionRecoveryError):
        HistoryStore(journal_root)


def test_initial_atomic_recovery_preserves_preexisting_records_and_is_idempotent(tmp_path):
    bundle = _build_records()
    root = tmp_path / "recovery"
    store = HistoryStore(root)
    sentinel = _state("fixture-sentinel", T0, 123, None)
    store.append_state(sentinel)
    def interrupt(stage, count):
        if (stage, count) == ("after_publication", 1):
            raise _SimulatedProcessInterruption("interrupted initial bundle")
    with pytest.raises(_SimulatedProcessInterruption):
        HistoryStore(root, _fault_injector=interrupt).append_transaction(bundle["records"])
    # Accounting is read-only and sees the pending operational transaction journal.
    interrupted_measurement = account_storage(history_store_scope(store))
    assert interrupted_measurement.categories[StorageCategory.OPERATIONAL_METADATA.value].file_count > 0
    recovered = HistoryStore(root)
    assert recovered.read_state(str(sentinel.state_id)) == sentinel
    assert recovered.states() == (sentinel,)
    second_reopen = HistoryStore(root)
    assert second_reopen.states() == (sentinel,)
    second_reopen.append_transaction(bundle["records"])
    assert {str(state.state_id) for state in HistoryStore(root).states()} == (
        {str(state.state_id) for state in bundle["states"].values()} |
        {str(bundle["expected"].state_id), str(sentinel.state_id)})

