from __future__ import annotations

import json

import pytest

from arcana_worldsim.r6.checkpoint import CheckpointEnvelope, RefinementBranchEnvelope
from arcana_worldsim.r6.identity import (BranchId, HistoryId, PayloadIdentity,
                                         canonical_bytes, content_hash)
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import DifferenceStatus, HistoryQueryService
from arcana_worldsim.r6.refinement import (RefinementExecutionOutput, RefinementInputError,
    RefinementOutputManifestEntry, RefinementReconstructionRecipe, execute_refinement)
from arcana_worldsim.r6.state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
                                      SupportClass, TimeSupport)
from arcana_worldsim.r6.store import HistoryStore, RecordIntegrityError


HISTORY = str(HistoryId.from_payload({"fixture": "b0-f-history"}))
PARENT = str(BranchId.from_payload({"fixture": "b0-f-parent"}))
TIME = TimeSupport("fixture:t0", "synthetic-clock", "SNAPSHOT")
PARENT_SPACE = SpatialSupport("coarse-grid", ("A", "B", "C", "D"), "coarse", "CELL_SET")
CONFIG = {"refinement": "synthetic-2x"}
RUNTIME = {"adapter": "fixture-refiner-v1"}
SEED = {"seed": 23}
CHILD_VALUES = {"B1": 11, "B2": 12, "B3": 13, "B4": 14}


def _child_state(branch_id, parent, provenance_id, cell_id, value):
    payload = canonical_bytes({"cell_id": cell_id, "value": value})
    digest = PayloadIdentity.from_bytes(payload)
    state = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=branch_id, domain="fixture-field",
        time_support=TIME,
        spatial_support=SpatialSupport("fine-grid", (cell_id,), "2x", "CELL_SET"),
        support_class=SupportClass.FIXTURE_ONLY,
        authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"value": value}, provenance_ids=(provenance_id,),
        parent_state_ids=(str(parent.state_id),), payload_ref=f"sha256:{digest.digest}",
        refinement_lineage={"parent_cell_ids": ["B"], "branch_id": branch_id},
    )
    return state, payload, digest


def _setup_parent(root, *, checkpoint_state_override=None):
    store = HistoryStore(root)
    provenance = ProvenanceRecord.create(activity="synthetic-parent-source",
                                          source_refs=("fixture:coarse-parent",))
    parent = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=PARENT, domain="fixture-field",
        time_support=TIME, spatial_support=PARENT_SPACE,
        support_class=SupportClass.DIRECT_SUPPORTED,
        authority_class=AuthorityClass.DIRECT_AUTHORITY,
        value={"cells": {"A": 0, "B": 10, "C": 20, "D": 30}},
        uncertainty={"fixture": "coarse-known"}, provenance_ids=(str(provenance.record_id),),
    )
    checkpoint_state_id = checkpoint_state_override or str(parent.state_id)
    checkpoint = CheckpointEnvelope.create(
        history_id=HISTORY, branch_id=PARENT, time_key=TIME.time_key,
        restart_state_ids=(checkpoint_state_id,), retained_history_state_ids=(checkpoint_state_id,),
        runtime_identity=RUNTIME, configuration=CONFIG, seed_lineage=SEED,
        upstream_dependency_ids=(str(provenance.record_id),),
    )
    store.append_transaction((provenance, parent, checkpoint))
    return store, provenance, parent, checkpoint


def _make_branch_recipe(parent, checkpoint, provenance, *,
                        parent_branch=PARENT, history_id=HISTORY,
                        region_cells=("B",), boundary=None,
                        output_cell_ids=("B1", "B2", "B3", "B4")):
    boundary = boundary or {"boundary_values": [1, 2, 3, 4], "boundary_identity": "fixture-bc-v1"}
    # Branch identity is independent of output state IDs to avoid a branch/state identity cycle.
    branch = RefinementBranchEnvelope.create(
        history_id=history_id, parent_branch_id=parent_branch,
        base_history_id=history_id, refinement_anchor_id="fixture-anchor:t0",
        region_id="region-B", time_interval=(TIME.time_key, TIME.time_key),
        requested_domains=("fixture-field",), requested_resolution="2x",
        parent_boundary_conditions=boundary, provenance_refs=(str(provenance.record_id),),
    )
    output_entries = []
    expected_states = []
    for index, cell_id in enumerate(output_cell_ids):
        value = CHILD_VALUES.get(cell_id, 11 + index)
        state, payload, digest = _child_state(str(branch.branch_id), parent,
            str(provenance.record_id), cell_id, value)
        expected_states.append((state, payload))
        output_entries.append(RefinementOutputManifestEntry(
            str(state.state_id), tuple(region_cells), (cell_id,), digest))
    recipe = RefinementReconstructionRecipe.create(
        branch=branch, base_checkpoint_id=str(checkpoint.checkpoint_id),
        parent_state_ids=(str(parent.state_id),), parent_region_cell_ids=tuple(region_cells),
        runtime_identity=RUNTIME, configuration_sha256=content_hash(CONFIG),
        seed_lineage=SEED, model_adapter_id="fixture:bilinear-refinement-v1",
        output_manifest=tuple(output_entries), materialization_status="DECLARED",
    )
    return branch, recipe, tuple(expected_states)


def runner(inputs):
    parent = inputs.parent_states[0]
    parent_value = parent.value["cells"]["B"]
    offsets = inputs.boundary_conditions["boundary_values"]
    outputs = []
    for index, entry in enumerate(inputs.recipe.output_manifest):
        cell_id = entry.child_cell_ids[0]
        state, payload, _digest = _child_state(
            str(inputs.branch.branch_id), parent,
            parent.provenance_ids[0], cell_id, parent_value + offsets[index])
        outputs.append(RefinementExecutionOutput(state, payload))
    return tuple(outputs)


def _materialized_recipe(branch, recipe):
    return RefinementReconstructionRecipe.create(
        branch=branch, base_checkpoint_id=recipe.base_checkpoint_id,
        parent_state_ids=recipe.parent_state_ids,
        parent_region_cell_ids=recipe.parent_region_cell_ids,
        runtime_identity=dict(recipe.runtime_identity),
        configuration_sha256=recipe.configuration_sha256,
        seed_lineage=dict(recipe.seed_lineage), model_adapter_id=recipe.model_adapter_id,
        output_manifest=recipe.output_manifest, materialization_status="MATERIALIZED")


def test_synthetic_branch_reconstructs_after_reopen_without_parent_mutation(tmp_path):
    root = tmp_path / "history"
    store, provenance, parent, checkpoint = _setup_parent(root)
    parent_paths = (root / "states" / f"{parent.state_id}.json",
                    root / "provenance" / f"{provenance.record_id}.json",
                    root / "checkpoints" / f"{checkpoint.checkpoint_id}.json")
    before = {path: path.read_bytes() for path in parent_paths}
    branch, recipe, expected = _make_branch_recipe(parent, checkpoint, provenance)
    result = execute_refinement(store, branch, recipe, runner)
    assert result.status == "VERIFIED"
    assert len(result.produced_state_ids) == 4
    materialized = _materialized_recipe(branch, recipe)
    child_records = (provenance, *(state for state, _ in expected))
    store.append_refinement_transaction(branch, materialized, child_records)
    assert {path: path.read_bytes() for path in parent_paths} == before

    reopened = HistoryStore(root)
    loaded_branch = reopened.read_refinement_branch(str(branch.branch_id))
    loaded_recipe = reopened.read_refinement_recipe(str(materialized.recipe_id))
    rerun = execute_refinement(reopened, loaded_branch, loaded_recipe, runner)
    assert rerun.status == result.status == "VERIFIED"
    assert rerun.produced_state_ids == result.produced_state_ids
    assert rerun.expected_state_ids == result.expected_state_ids
    assert {path: path.read_bytes() for path in parent_paths} == before
    query = HistoryQueryService(reopened)
    parent_history = query.history(history_id=HISTORY, branch_id=PARENT)
    child_history = query.history(history_id=HISTORY, branch_id=str(branch.branch_id))
    assert parent_history == (parent,)
    assert {str(item.state_id) for item in child_history} == set(result.expected_state_ids)
    assert all(item.branch_id == str(branch.branch_id) for item in child_history)
    assert query.state_at(history_id=HISTORY, branch_id=str(branch.branch_id),
        domain="fixture-field", time_key=TIME.time_key, cell_id="B").status == "OUTSIDE_SUPPORT"
    assert query.difference(str(parent.state_id), str(child_history[0].state_id)).status is \
        DifferenceStatus.INCOMPATIBLE_SUPPORT
    explanation = query.why(str(child_history[0].state_id))
    assert str(parent.state_id) in {str(state.state_id) for state in explanation.state_lineage}
    assert str(checkpoint.checkpoint_id) in {str(item.checkpoint_id) for item in explanation.checkpoints}
    assert str(branch.branch_id) in {str(item.branch_id) for item in explanation.refinement_branches}
    assert str(materialized.recipe_id) in {str(item.recipe_id) for item in explanation.refinement_recipes}
    assert child_history[0].authority_class is AuthorityClass.FIXTURE_ONLY


def test_registered_child_rejects_unscoped_writes_and_parent_branch_masquerade(tmp_path):
    store, provenance, parent, checkpoint = _setup_parent(tmp_path / "history")
    branch, recipe, expected = _make_branch_recipe(parent, checkpoint, provenance)
    materialized = _materialized_recipe(branch, recipe)
    child_states = tuple(state for state, _ in expected)
    store.append_refinement_transaction(branch, materialized, (provenance, *child_states))
    with pytest.raises(ValueError, match="append_refinement_transaction"):
        store.append_state(child_states[0])
    with pytest.raises(ValueError, match="branch-bound transaction"):
        store.append_transaction((child_states[0],))
    malicious = DomainStateEnvelope.create(
        history_id=HISTORY, branch_id=PARENT, domain="fixture-field",
        time_support=TIME, spatial_support=SpatialSupport("fine-grid", ("B1",), "2x"),
        support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
        value={"malicious": True}, parent_state_ids=(str(parent.state_id),),
    )
    with pytest.raises(ValueError):
        store.append_refinement_transaction(branch, materialized,
            (provenance, malicious, *child_states[1:]))


def test_wrong_parent_history_and_missing_checkpoint_fail_closed(tmp_path):
    store, provenance, parent, checkpoint = _setup_parent(tmp_path / "history")
    branch, recipe, _ = _make_branch_recipe(parent, checkpoint, provenance,
                                            parent_branch=str(BranchId.from_payload({"wrong": 1})))
    with pytest.raises(RefinementInputError, match="base checkpoint"):
        execute_refinement(store, branch, recipe, runner)
    missing_branch, missing_recipe, _ = _make_branch_recipe(parent, checkpoint, provenance)
    missing_recipe = RefinementReconstructionRecipe.create(
        branch=missing_branch, base_checkpoint_id="r6checkpoint_" + "f" * 64,
        parent_state_ids=(str(parent.state_id),), parent_region_cell_ids=("B",),
        runtime_identity=RUNTIME, configuration_sha256=content_hash(CONFIG), seed_lineage=SEED,
        model_adapter_id="fixture:adapter", output_manifest=missing_recipe.output_manifest)
    with pytest.raises(RefinementInputError, match="closure failed"):
        execute_refinement(store, missing_branch, missing_recipe, runner)


def test_wrong_history_wrong_boundary_and_outside_region_fail_closed(tmp_path):
    store, provenance, parent, checkpoint = _setup_parent(tmp_path / "history")
    branch, recipe, _ = _make_branch_recipe(parent, checkpoint, provenance,
                                            history_id=str(HistoryId.from_payload({"other": 1})))
    with pytest.raises(RefinementInputError, match="base checkpoint"):
        execute_refinement(store, branch, recipe, runner)
    branch, recipe, _ = _make_branch_recipe(parent, checkpoint, provenance,
                                            boundary={"boundary_values": [1, 2, 3, 4], "changed": True})
    with pytest.raises(ValueError, match="identity"):
        tampered_recipe = RefinementReconstructionRecipe(
            recipe.recipe_id, recipe.branch_id, recipe.history_id, recipe.parent_branch_id,
            recipe.base_checkpoint_id, recipe.parent_state_ids, recipe.parent_region_cell_ids,
            "0" * 64, recipe.runtime_identity, recipe.configuration_sha256, recipe.seed_lineage,
            recipe.model_adapter_id, recipe.output_manifest, recipe.materialization_status,
            recipe.schema_version)
        execute_refinement(store, branch, tampered_recipe, runner)
    branch, recipe, _ = _make_branch_recipe(parent, checkpoint, provenance, region_cells=("Z",))
    with pytest.raises(RefinementInputError, match="exceeds parent state support"):
        execute_refinement(store, branch, recipe, runner)


def test_wrong_recipe_branch_output_identity_and_payload_fail(tmp_path):
    store, provenance, parent, checkpoint = _setup_parent(tmp_path / "history")
    branch, recipe, expected = _make_branch_recipe(parent, checkpoint, provenance)
    other_branch, _, _ = _make_branch_recipe(parent, checkpoint, provenance,
                                               boundary={"boundary_values": [2, 3, 4, 5]})
    wrong_binding = RefinementReconstructionRecipe.create(
        branch=other_branch, base_checkpoint_id=recipe.base_checkpoint_id,
        parent_state_ids=recipe.parent_state_ids, parent_region_cell_ids=recipe.parent_region_cell_ids,
        runtime_identity=RUNTIME, configuration_sha256=content_hash(CONFIG), seed_lineage=SEED,
        model_adapter_id="fixture:adapter", output_manifest=recipe.output_manifest)
    with pytest.raises(RefinementInputError, match="another child branch"):
        execute_refinement(store, branch, wrong_binding, runner)

    def wrong_outputs(inputs):
        valid = list(runner(inputs))
        first = valid[0]
        state = DomainStateEnvelope.create(
            history_id=HISTORY, branch_id=str(branch.branch_id), domain="fixture-field",
            time_support=TIME, spatial_support=first.state.spatial_support,
            support_class=SupportClass.FIXTURE_ONLY, authority_class=AuthorityClass.FIXTURE_ONLY,
            value={"wrong": "output"}, provenance_ids=first.state.provenance_ids,
            parent_state_ids=first.state.parent_state_ids,
            payload_ref=first.state.payload_ref, refinement_lineage=first.state.refinement_lineage)
        valid[0] = RefinementExecutionOutput(state, first.payload_bytes)
        return tuple(valid)
    assert execute_refinement(store, branch, recipe, wrong_outputs).status == "MISMATCH"

    def wrong_payload(inputs):
        valid = list(runner(inputs))
        valid[0] = RefinementExecutionOutput(valid[0].state, b"wrong-payload")
        return tuple(valid)
    assert execute_refinement(store, branch, recipe, wrong_payload).status == "MISMATCH"


def test_missing_parent_input_and_corrupt_branch_metadata_fail_closed(tmp_path):
    root = tmp_path / "history"
    absent_id = "r6state_" + "9" * 64
    store, provenance, parent, checkpoint = _setup_parent(root, checkpoint_state_override=absent_id)
    branch, recipe, _ = _make_branch_recipe(parent, checkpoint, provenance)
    recipe = RefinementReconstructionRecipe.create(
        branch=branch, base_checkpoint_id=str(checkpoint.checkpoint_id),
        parent_state_ids=(absent_id,), parent_region_cell_ids=("B",),
        runtime_identity=RUNTIME, configuration_sha256=content_hash(CONFIG), seed_lineage=SEED,
        model_adapter_id="fixture:adapter", output_manifest=recipe.output_manifest)
    with pytest.raises(RefinementInputError, match="closure failed"):
        execute_refinement(store, branch, recipe, runner)

    normal_root = tmp_path / "normal"
    store, provenance, parent, checkpoint = _setup_parent(normal_root)
    branch, recipe, outputs = _make_branch_recipe(parent, checkpoint, provenance)
    materialized = _materialized_recipe(branch, recipe)
    store.append_refinement_transaction(branch, materialized,
        (provenance, *(state for state, _ in outputs)))
    path = normal_root / "refinement_branches" / f"{branch.branch_id}.json"
    body = json.loads(path.read_text(encoding="utf-8")); body["region_id"] = "tampered"
    path.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(RecordIntegrityError):
        HistoryStore(normal_root).read_refinement_branch(str(branch.branch_id))


def test_refinement_transaction_failure_rolls_back_branch_recipe_and_children(tmp_path):
    root = tmp_path / "history"
    store, provenance, parent, checkpoint = _setup_parent(root)
    branch, recipe, outputs = _make_branch_recipe(parent, checkpoint, provenance)
    materialized = _materialized_recipe(branch, recipe)

    def inject(stage, count):
        if (stage, count) == ("after_publication", 2):
            raise RuntimeError("injected child publication failure")

    failing = HistoryStore(root, _fault_injector=inject)
    with pytest.raises(RuntimeError, match="injected"):
        failing.append_refinement_transaction(branch, materialized,
            (provenance, *(state for state, _ in outputs)))
    reopened = HistoryStore(root)
    with pytest.raises(FileNotFoundError):
        reopened.read_refinement_branch(str(branch.branch_id))
    with pytest.raises(FileNotFoundError):
        reopened.read_refinement_recipe(str(materialized.recipe_id))
    assert all(not (root / "states" / f"{state.state_id}.json").exists()
               for state, _ in outputs)


def test_reused_parent_state_id_cannot_be_rewritten_and_child_authority_stays_explicit(tmp_path):
    root = tmp_path / "history"
    store, provenance, parent, checkpoint = _setup_parent(root)
    branch, recipe, outputs = _make_branch_recipe(parent, checkpoint, provenance)
    materialized = _materialized_recipe(branch, recipe)
    store.append_refinement_transaction(branch, materialized,
        (provenance, *(state for state, _ in outputs)))
    path = root / "states" / f"{parent.state_id}.json"
    before = path.read_bytes()
    with pytest.raises(ValueError):
        store.append_state(DomainStateEnvelope.from_dict({**parent.to_dict(), "value": {"cells": {}}}))
    assert path.read_bytes() == before
    assert all(state.authority_class is AuthorityClass.FIXTURE_ONLY for state, _ in outputs)
