from __future__ import annotations

import json

import pytest

from arcana_worldsim.r6.checkpoint import CheckpointEnvelope
from arcana_worldsim.r6.forcing import ForcingRecord
from arcana_worldsim.r6.identity import (BranchId, EventId, HistoryId, PayloadIdentity,
                                         canonical_bytes, content_hash)
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.replay import (ReplayExecutionOutput, ReplayInputError,
                                       ReplayRecipe, execute_replay, validate_replay_inputs)
from arcana_worldsim.r6.state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
                                      SupportClass, TimeSupport)
from arcana_worldsim.r6.store import HistoryStore, RecordIntegrityError
from arcana_worldsim.r6.temporal import EventRecord


HISTORY = str(HistoryId.from_payload({"fixture": "b0-d-history"}))
BRANCH = str(BranchId.from_payload({"fixture": "b0-d-branch"}))
TIME0 = TimeSupport("fixture:s0", "synthetic-clock")
TIME1 = TimeSupport("fixture:s1", "synthetic-clock")
SPACE = SpatialSupport("fixture-grid", ("cell-1",), "fixture-resolution")
CONFIG = {"case": "synthetic-b0-d", "factor": 10}
RUNTIME = {"adapter": "synthetic-integer-v1"}
SEED = {"seed": 17}


def _state(time_support, value, provenance, *, payload_ref=None, domain="fixture-state"):
    return DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, domain=domain,
        time_support=time_support, spatial_support=SPACE,
        support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.FIXTURE_ONLY,
        value=value, provenance_ids=(str(provenance.record_id),), payload_ref=payload_ref,
    )


def _fixture(root):
    provenance = ProvenanceRecord.create(
        activity="synthetic-b0-d-fixture", source_refs=("fixture:input",),
        attributes={"purpose": "infrastructure-only"},
    )
    base = _state(TIME0, {"fixture_value": 2}, provenance)
    event = EventRecord.create(
        history_id=HISTORY, branch_id=BRANCH, time_key=TIME0.time_key,
        state_ids=(str(base.state_id),), details={"fixture_event": "declared"},
    )
    forcing = ForcingRecord.create(
        history_id=HISTORY, branch_id=BRANCH, forcing_kind="fixture-addend",
        domain="fixture-domain", time_support=TIME0, spatial_support=SPACE,
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value=3, provenance_ids=(str(provenance.record_id),), source_refs=("fixture:forcing",),
    )
    forcing2 = ForcingRecord.create(
        history_id=HISTORY, branch_id=BRANCH, forcing_kind="fixture-step-two",
        domain="fixture-domain", time_support=TIME0, spatial_support=SPACE,
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value=4, provenance_ids=(str(provenance.record_id),), source_refs=("fixture:forcing-2",),
    )
    output_value = {"fixture_value": (2 * CONFIG["factor"] + 3) * CONFIG["factor"] + 4 + SEED["seed"]}
    payload = canonical_bytes(output_value)
    payload_identity = PayloadIdentity.from_bytes(payload)
    expected = _state(TIME1, output_value, provenance,
                      payload_ref=f"sha256:{payload_identity.digest}")
    checkpoint = CheckpointEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, time_key=TIME0.time_key,
        restart_state_ids=(str(base.state_id),), retained_history_state_ids=(str(base.state_id),),
        runtime_identity=RUNTIME, configuration=CONFIG, seed_lineage=SEED,
        upstream_dependency_ids=(str(provenance.record_id),),
    )
    recipe = ReplayRecipe.create(
        history_id=HISTORY, branch_id=BRANCH,
        base_checkpoint_id=str(checkpoint.checkpoint_id), runtime_identity=RUNTIME,
        configuration_sha256=content_hash(CONFIG), seed_lineage=SEED,
        forcing_ids=(str(forcing.forcing_id), str(forcing2.forcing_id)), event_ids=(event.record_id,),
        upstream_dependency_ids=(str(provenance.record_id),),
        provenance_ids=(str(provenance.record_id),),
        expected_output_state_id=str(expected.state_id), model_adapter_id="fixture:integer-step-v1",
        expected_payload_identity=payload_identity,
    )
    store = HistoryStore(root)
    store.append_transaction((base, provenance, forcing, forcing2, event, checkpoint, expected, recipe))
    return store, {"provenance": provenance, "base": base, "forcing": forcing,
                   "forcing2": forcing2, "event": event, "checkpoint": checkpoint, "expected": expected,
                   "recipe": recipe, "payload": payload}


def runner(recipe, inputs):
    initial = inputs.base_states[0].value["fixture_value"]
    accumulated = initial
    for forcing in inputs.forcings:
        accumulated = accumulated * 10 + forcing.value
    result = {"fixture_value": accumulated + recipe.seed_lineage["seed"]}
    payload = canonical_bytes(result)
    state = _state(TIME1, result, inputs.provenance[0],
                   payload_ref=f"sha256:{PayloadIdentity.from_bytes(payload).digest}")
    return ReplayExecutionOutput(state, payload)


def test_synthetic_recipe_transaction_reopens_and_replays_repeatably(tmp_path):
    store, records = _fixture(tmp_path / "history")
    reopened = HistoryStore(tmp_path / "history")
    recipe = reopened.read_replay_recipe(str(records["recipe"].recipe_id))
    first = execute_replay(reopened, recipe, runner)
    second = execute_replay(HistoryStore(tmp_path / "history"), recipe, runner)
    assert first.status == second.status == "VERIFIED"
    assert first.produced_state_id == second.produced_state_id == str(records["expected"].state_id)
    assert first.produced_payload_identity == second.produced_payload_identity
    assert first.produced_payload_identity == records["recipe"].expected_payload_identity
    assert records["expected"].authority_class == AuthorityClass.FIXTURE_ONLY
    assert records["expected"].support_class == SupportClass.FIXTURE_ONLY
    assert reopened.forcings() == tuple(sorted((records["forcing"], records["forcing2"]),
                                                key=lambda item: str(item.forcing_id)))


def test_missing_forcing_fails_closed(tmp_path):
    store, records = _fixture(tmp_path / "history")
    recipe = ReplayRecipe.create(**_recipe_args(records, forcing_ids=("r6forcing_" + "0" * 64,)))
    with pytest.raises(ReplayInputError, match="closure failed"):
        execute_replay(store, recipe, runner)


def test_wrong_forcing_identity_fails_closed(tmp_path):
    store, records = _fixture(tmp_path / "history")
    recipe = ReplayRecipe.create(**_recipe_args(records, forcing_ids=("not-a-forcing-id",)))
    with pytest.raises(ReplayInputError, match="closure failed"):
        execute_replay(store, recipe, runner)


def test_corrupt_forcing_fails_identity_verification(tmp_path):
    root = tmp_path / "history"
    store, records = _fixture(root)
    path = root / "forcings" / f"{records['forcing'].forcing_id}.json"
    body = json.loads(path.read_text(encoding="utf-8"))
    body["value"] = 999
    path.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(RecordIntegrityError, match="forcing"):
        store.read_forcing(str(records["forcing"].forcing_id))


@pytest.mark.parametrize("field", ["runtime_identity", "configuration_sha256", "seed_lineage"])
def test_runtime_configuration_and_seed_mismatch_fail_closed(tmp_path, field):
    store, records = _fixture(tmp_path / "history")
    args = _recipe_args(records)
    args[field] = {"different": True} if field != "configuration_sha256" else "f" * 64
    recipe = ReplayRecipe.create(**args)
    with pytest.raises(ReplayInputError, match="runtime/configuration/seed"):
        execute_replay(store, recipe, runner)


def test_missing_event_and_dependency_fail_closed(tmp_path):
    store, records = _fixture(tmp_path / "history")
    args = _recipe_args(records, event_ids=(str(EventId.from_payload({"missing": True})),))
    with pytest.raises(ReplayInputError, match="closure failed"):
        execute_replay(store, ReplayRecipe.create(**args), runner)
    args = _recipe_args(records, upstream_dependency_ids=("missing-dependency",))
    with pytest.raises(ReplayInputError, match="dependencies differ"):
        execute_replay(store, ReplayRecipe.create(**args), runner)


def test_declared_but_unresolved_checkpoint_dependency_fails_closed(tmp_path):
    store, records = _fixture(tmp_path / "history")
    missing = "unresolved-upstream-identity"
    checkpoint = CheckpointEnvelope.create(
        history_id=HISTORY, branch_id=BRANCH, time_key=TIME0.time_key,
        restart_state_ids=(str(records["base"].state_id),),
        retained_history_state_ids=(str(records["base"].state_id),),
        runtime_identity=RUNTIME, configuration=CONFIG, seed_lineage=SEED,
        upstream_dependency_ids=(missing,),
    )
    store.append_checkpoint(checkpoint)
    recipe = ReplayRecipe.create(**_recipe_args(
        records, base_checkpoint_id=str(checkpoint.checkpoint_id),
        upstream_dependency_ids=(missing,)))
    with pytest.raises(ReplayInputError, match="unresolved dependency"):
        execute_replay(store, recipe, runner)


def test_forcing_payload_is_verified_when_resolved(tmp_path):
    store, records = _fixture(tmp_path / "history")
    payload = b"synthetic forcing bytes"
    payload_id = PayloadIdentity.from_bytes(payload)
    forcing = ForcingRecord.create(
        history_id=HISTORY, branch_id=BRANCH, forcing_kind="fixture-payload",
        domain="fixture-domain", time_support=TIME0, spatial_support=SPACE,
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        payload_ref=f"sha256:{payload_id.digest}",
        provenance_ids=(str(records["provenance"].record_id),),
    )
    store.append_forcing(forcing)
    recipe = ReplayRecipe.create(**_recipe_args(records, forcing_ids=(str(forcing.forcing_id),)))
    resolved = validate_replay_inputs(store, recipe, payload_resolver=lambda _: payload)
    assert resolved.forcing_payloads[str(forcing.forcing_id)] == payload
    with pytest.raises(ReplayInputError, match="closure failed"):
        validate_replay_inputs(store, recipe, payload_resolver=lambda _: b"wrong bytes")


def test_changed_forcing_order_changes_recipe_and_fails_expected_identity(tmp_path):
    store, records = _fixture(tmp_path / "history")
    original = records["recipe"]
    changed = ReplayRecipe.create(**_recipe_args(
        records, forcing_ids=tuple(reversed(original.forcing_ids))))
    assert changed.recipe_id != original.recipe_id
    result = execute_replay(store, changed, runner)
    assert result.status == "MISMATCH"
    assert "produced state identity differs from expected" in result.mismatches


def test_produced_state_id_mismatch_is_a_mismatch_not_success(tmp_path):
    store, records = _fixture(tmp_path / "history")

    def wrong_runner(recipe, inputs):
        value = {"fixture_value": -1}
        payload = canonical_bytes(value)
        state = _state(TIME1, value, inputs.provenance[0],
                       payload_ref=f"sha256:{PayloadIdentity.from_bytes(payload).digest}")
        return ReplayExecutionOutput(state, payload)

    result = execute_replay(store, records["recipe"], wrong_runner)
    assert result.status == "MISMATCH"
    assert result.mismatches


def test_produced_payload_hash_mismatch_is_a_mismatch(tmp_path):
    store, records = _fixture(tmp_path / "history")

    def wrong_payload(recipe, inputs):
        valid = runner(recipe, inputs)
        return ReplayExecutionOutput(valid.state, valid.payload_bytes + b"changed")

    result = execute_replay(store, records["recipe"], wrong_payload)
    assert result.status == "MISMATCH"
    assert any("payload identity" in item for item in result.mismatches)


def _recipe_args(records, **overrides):
    recipe = records["recipe"]
    args = {"history_id": recipe.history_id, "branch_id": recipe.branch_id,
            "base_checkpoint_id": recipe.base_checkpoint_id,
            "runtime_identity": dict(recipe.runtime_identity),
            "configuration_sha256": recipe.configuration_sha256,
            "seed_lineage": dict(recipe.seed_lineage), "forcing_ids": recipe.forcing_ids,
            "event_ids": recipe.event_ids,
            "upstream_dependency_ids": recipe.upstream_dependency_ids,
            "provenance_ids": recipe.provenance_ids,
            "expected_output_state_id": recipe.expected_output_state_id,
            "expected_payload_identity": recipe.expected_payload_identity,
            "model_adapter_id": recipe.model_adapter_id}
    args.update(overrides)
    return args
