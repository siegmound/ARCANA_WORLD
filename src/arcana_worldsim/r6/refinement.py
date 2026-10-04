"""Branch-bound refinement reconstruction records and synthetic executor."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Mapping, TYPE_CHECKING

from .checkpoint import CheckpointEnvelope, RefinementBranchEnvelope
from .identity import (PayloadIdentity, RefinementRecipeId, content_hash, freeze_json,
                       thaw_json)
from .state import DomainStateEnvelope

if TYPE_CHECKING:
    from .store import HistoryStore

REFINEMENT_RECIPE_SCHEMA = "ARCANA_R6_REFINEMENT_RECONSTRUCTION_V0"


def _pinned_store_read(method):
    @wraps(method)
    def wrapped(store, *args, **kwargs):
        with store.read_view():
            return method(store, *args, **kwargs)
    return wrapped


class RefinementInputError(ValueError):
    """A declared refinement reconstruction input is absent or inconsistent."""


@dataclass(frozen=True, slots=True)
class RefinementOutputManifestEntry:
    state_id: str
    parent_cell_ids: tuple[str, ...]
    child_cell_ids: tuple[str, ...]
    payload_identity: PayloadIdentity | None = None

    def __post_init__(self) -> None:
        if not self.state_id or not self.parent_cell_ids or not self.child_cell_ids:
            raise ValueError("refinement output requires state and parent/child support IDs")
        object.__setattr__(self, "parent_cell_ids", tuple(self.parent_cell_ids))
        object.__setattr__(self, "child_cell_ids", tuple(self.child_cell_ids))
        if len(set(self.parent_cell_ids)) != len(self.parent_cell_ids):
            raise ValueError("duplicate parent support cell in output manifest")
        if len(set(self.child_cell_ids)) != len(self.child_cell_ids):
            raise ValueError("duplicate child support cell in output manifest")

    def to_dict(self) -> dict[str, Any]:
        return {"state_id": self.state_id, "parent_cell_ids": list(self.parent_cell_ids),
                "child_cell_ids": list(self.child_cell_ids),
                "payload_identity": (None if self.payload_identity is None
                                     else self.payload_identity.to_dict())}

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "RefinementOutputManifestEntry":
        payload = row.get("payload_identity")
        identity = None if payload is None else PayloadIdentity(str(payload["algorithm"]),
                                                                 str(payload["digest"]))
        return cls(str(row["state_id"]), tuple(row["parent_cell_ids"]),
                   tuple(row["child_cell_ids"]), identity)


@dataclass(frozen=True, slots=True)
class RefinementReconstructionRecipe:
    recipe_id: RefinementRecipeId
    branch_id: str
    history_id: str
    parent_branch_id: str
    base_checkpoint_id: str
    parent_state_ids: tuple[str, ...]
    parent_region_cell_ids: tuple[str, ...]
    boundary_conditions_sha256: str
    runtime_identity: Mapping[str, Any]
    configuration_sha256: str
    seed_lineage: Mapping[str, Any]
    model_adapter_id: str
    output_manifest: tuple[RefinementOutputManifestEntry, ...]
    materialization_status: str = "DECLARED"
    schema_version: str = REFINEMENT_RECIPE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != REFINEMENT_RECIPE_SCHEMA:
            raise ValueError("unsupported refinement recipe schema")
        if not all((self.branch_id, self.history_id, self.parent_branch_id,
                    self.base_checkpoint_id, self.model_adapter_id)):
            raise ValueError("refinement recipe scope and identities are required")
        for name in ("boundary_conditions_sha256", "configuration_sha256"):
            value = getattr(self, name)
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError(f"invalid {name}")
        if self.materialization_status not in {"DECLARED", "MATERIALIZED"}:
            raise ValueError("unsupported refinement materialization status")
        object.__setattr__(self, "parent_state_ids", tuple(self.parent_state_ids))
        object.__setattr__(self, "parent_region_cell_ids", tuple(self.parent_region_cell_ids))
        object.__setattr__(self, "runtime_identity", freeze_json(self.runtime_identity))
        object.__setattr__(self, "seed_lineage", freeze_json(self.seed_lineage))
        object.__setattr__(self, "output_manifest", tuple(self.output_manifest))
        if not self.parent_state_ids or not self.parent_region_cell_ids or not self.output_manifest:
            raise ValueError("refinement recipe requires parent states, region support, and outputs")
        state_ids = tuple(item.state_id for item in self.output_manifest)
        if len(set(state_ids)) != len(state_ids):
            raise ValueError("duplicate output state in refinement manifest")
        if RefinementRecipeId.from_payload(self._identity_body()) != self.recipe_id:
            raise ValueError("refinement recipe identity does not match content")

    def _identity_body(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "branch_id": self.branch_id,
                "history_id": self.history_id, "parent_branch_id": self.parent_branch_id,
                "base_checkpoint_id": self.base_checkpoint_id,
                "parent_state_ids": list(self.parent_state_ids),
                "parent_region_cell_ids": list(self.parent_region_cell_ids),
                "boundary_conditions_sha256": self.boundary_conditions_sha256,
                "runtime_identity": thaw_json(self.runtime_identity),
                "configuration_sha256": self.configuration_sha256,
                "seed_lineage": thaw_json(self.seed_lineage),
                "model_adapter_id": self.model_adapter_id,
                "output_manifest": [entry.to_dict() for entry in self.output_manifest],
                "materialization_status": self.materialization_status}

    @classmethod
    def create(cls, *, branch: RefinementBranchEnvelope, base_checkpoint_id: str,
               parent_state_ids: tuple[str, ...], parent_region_cell_ids: tuple[str, ...],
               runtime_identity: Mapping[str, Any], configuration_sha256: str,
               seed_lineage: Mapping[str, Any], model_adapter_id: str,
               output_manifest: tuple[RefinementOutputManifestEntry, ...],
               materialization_status: str = "DECLARED") -> "RefinementReconstructionRecipe":
        boundary_hash = content_hash(thaw_json(branch.parent_boundary_conditions))
        body = {"schema_version": REFINEMENT_RECIPE_SCHEMA,
                "branch_id": str(branch.branch_id), "history_id": branch.history_id,
                "parent_branch_id": branch.parent_branch_id,
                "base_checkpoint_id": base_checkpoint_id,
                "parent_state_ids": list(parent_state_ids),
                "parent_region_cell_ids": list(parent_region_cell_ids),
                "boundary_conditions_sha256": boundary_hash,
                "runtime_identity": dict(runtime_identity),
                "configuration_sha256": configuration_sha256,
                "seed_lineage": dict(seed_lineage), "model_adapter_id": model_adapter_id,
                "output_manifest": [entry.to_dict() for entry in output_manifest],
                "materialization_status": materialization_status}
        return cls(RefinementRecipeId.from_payload(body), str(branch.branch_id), branch.history_id,
                   branch.parent_branch_id, base_checkpoint_id, parent_state_ids,
                   parent_region_cell_ids, boundary_hash, runtime_identity,
                   configuration_sha256, seed_lineage, model_adapter_id,
                   output_manifest, materialization_status)

    def to_dict(self) -> dict[str, Any]:
        return {"recipe_id": str(self.recipe_id), **self._identity_body()}

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "RefinementReconstructionRecipe":
        return cls(RefinementRecipeId(str(row["recipe_id"])), str(row["branch_id"]),
                   str(row["history_id"]), str(row["parent_branch_id"]),
                   str(row["base_checkpoint_id"]), tuple(row["parent_state_ids"]),
                   tuple(row["parent_region_cell_ids"]), str(row["boundary_conditions_sha256"]),
                   row["runtime_identity"], str(row["configuration_sha256"]),
                   row["seed_lineage"], str(row["model_adapter_id"]),
                   tuple(RefinementOutputManifestEntry.from_dict(item)
                         for item in row["output_manifest"]),
                   str(row["materialization_status"]), str(row["schema_version"]))


@dataclass(frozen=True, slots=True)
class ResolvedRefinementInputs:
    branch: RefinementBranchEnvelope
    recipe: RefinementReconstructionRecipe
    checkpoint: CheckpointEnvelope
    parent_states: tuple[DomainStateEnvelope, ...]
    expected_outputs: tuple[DomainStateEnvelope, ...]
    boundary_conditions: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class RefinementExecutionOutput:
    state: DomainStateEnvelope
    payload_bytes: bytes | None = None


@dataclass(frozen=True, slots=True)
class RefinementVerificationResult:
    branch_id: str
    recipe_id: str
    status: str
    produced_state_ids: tuple[str, ...]
    expected_state_ids: tuple[str, ...]
    mismatches: tuple[str, ...]


@_pinned_store_read
def validate_refinement_inputs(store: "HistoryStore",
                               branch_arg: str | RefinementBranchEnvelope,
                               recipe_arg: str | RefinementReconstructionRecipe
                               ) -> ResolvedRefinementInputs:
    try:
        branch = (store.read_refinement_branch(branch_arg)
                  if isinstance(branch_arg, str) else branch_arg)
        recipe = (store.read_refinement_recipe(recipe_arg)
                  if isinstance(recipe_arg, str) else recipe_arg)
        if recipe.branch_id != str(branch.branch_id):
            raise RefinementInputError("recipe is bound to another child branch")
        if (recipe.history_id, recipe.parent_branch_id) != (branch.history_id, branch.parent_branch_id):
            raise RefinementInputError("recipe/branch history or parent mismatch")
        if branch.branch_id.value == branch.parent_branch_id:
            raise RefinementInputError("child branch must differ from its parent")
        if recipe.boundary_conditions_sha256 != content_hash(thaw_json(branch.parent_boundary_conditions)):
            raise RefinementInputError("boundary-condition identity mismatch")
        if (branch.output_state_ids
                and tuple(branch.output_state_ids) != tuple(item.state_id for item in recipe.output_manifest)):
            raise RefinementInputError("branch output IDs differ from reconstruction manifest")
        checkpoint = CheckpointEnvelope.from_dict(store.read_checkpoint(recipe.base_checkpoint_id))
        if (checkpoint.history_id, checkpoint.branch_id) != (recipe.history_id, recipe.parent_branch_id):
            raise RefinementInputError("base checkpoint does not belong to parent branch/history")
        if checkpoint.validation_status != "VALIDATED":
            raise RefinementInputError("base checkpoint is not validated")
        declared_parent_ids = set(checkpoint.restart_state_ids) | set(checkpoint.retained_history_state_ids)
        if not set(recipe.parent_state_ids).issubset(declared_parent_ids):
            raise RefinementInputError("parent states are not in the base checkpoint closure")
        parents = tuple(store.read_state(state_id) for state_id in recipe.parent_state_ids)
        parent_cells: set[str] = set()
        for state in parents:
            if (state.history_id, state.branch_id) != (recipe.history_id, recipe.parent_branch_id):
                raise RefinementInputError("parent state scope mismatch")
            parent_cells.update(state.spatial_support.cell_ids)
        if not set(recipe.parent_region_cell_ids).issubset(parent_cells):
            raise RefinementInputError("declared refinement region exceeds parent state support")
        persisted_outputs: list[DomainStateEnvelope] = []
        for entry in recipe.output_manifest:
            try:
                persisted_outputs.append(store.read_state(entry.state_id))
            except FileNotFoundError:
                pass
        if persisted_outputs and len(persisted_outputs) != len(recipe.output_manifest):
            raise RefinementInputError("only part of the refinement output bundle is persisted")
        for manifest in recipe.output_manifest:
            if not set(manifest.parent_cell_ids).issubset(recipe.parent_region_cell_ids):
                raise RefinementInputError("output parent support exceeds declared refinement region")
        for manifest, state in zip(recipe.output_manifest, persisted_outputs):
            if (state.history_id, state.branch_id) != (recipe.history_id, recipe.branch_id):
                raise RefinementInputError("output state is not scoped to refinement child")
            if state.domain not in branch.requested_domains:
                raise RefinementInputError("output domain is not declared by refinement branch")
            if state.time_support.time_key not in branch.time_interval:
                raise RefinementInputError("output time is outside declared branch interval")
            if tuple(state.spatial_support.cell_ids) != manifest.child_cell_ids:
                raise RefinementInputError("output spatial support differs from manifest")
            actual_payload = None if state.payload_reference is None else state.payload_reference.identity
            if actual_payload != manifest.payload_identity:
                raise RefinementInputError("output payload identity differs from manifest")
        return ResolvedRefinementInputs(branch, recipe, checkpoint, parents,
                                        tuple(persisted_outputs),
                                        thaw_json(branch.parent_boundary_conditions))
    except RefinementInputError:
        raise
    except Exception as exc:
        raise RefinementInputError(f"refinement input closure failed: {exc}") from exc


@_pinned_store_read
def execute_refinement(store: "HistoryStore",
                       branch: str | RefinementBranchEnvelope,
                       recipe: str | RefinementReconstructionRecipe,
                       deterministic_runner: Callable[[ResolvedRefinementInputs], tuple[RefinementExecutionOutput, ...]]) -> RefinementVerificationResult:
    """Run a bounded injected adapter; it receives no store or parent write capability."""
    inputs = validate_refinement_inputs(store, branch, recipe)
    outputs = tuple(deterministic_runner(inputs))
    expected_by_id = {entry.state_id: entry for entry in inputs.recipe.output_manifest}
    persisted_by_id = {str(state.state_id): state for state in inputs.expected_outputs}
    mismatches: list[str] = []
    produced_ids: list[str] = []
    for output in outputs:
        if not isinstance(output, RefinementExecutionOutput):
            raise TypeError("refinement runner must return RefinementExecutionOutput values")
        state = output.state
        state_id = str(state.state_id)
        produced_ids.append(state_id)
        manifest = expected_by_id.pop(state_id, None)
        if manifest is None:
            mismatches.append(f"unexpected output state: {state_id}")
            continue
        if (state.history_id, state.branch_id) != (inputs.recipe.history_id, inputs.recipe.branch_id):
            mismatches.append(f"output state branch/history differs: {state_id}")
        if state.domain not in inputs.branch.requested_domains:
            mismatches.append(f"output domain is undeclared: {state_id}")
        if state.time_support.time_key not in inputs.branch.time_interval:
            mismatches.append(f"output time is outside declared interval: {state_id}")
        if tuple(state.spatial_support.cell_ids) != manifest.child_cell_ids:
            mismatches.append(f"output spatial support differs: {state_id}")
        if not set(manifest.parent_cell_ids).issubset(inputs.recipe.parent_region_cell_ids):
            mismatches.append(f"output parent support exceeds region: {state_id}")
        persisted = persisted_by_id.get(state_id)
        if persisted is not None and state.to_dict() != persisted.to_dict():
            mismatches.append(f"output state content differs from persisted state: {state_id}")
        payload_identity = (None if output.payload_bytes is None
                            else PayloadIdentity.from_bytes(output.payload_bytes))
        if payload_identity != manifest.payload_identity:
            mismatches.append(f"output payload identity differs: {state_id}")
        state_payload = None if state.payload_reference is None else state.payload_reference.identity
        if state_payload != manifest.payload_identity:
            mismatches.append(f"output state payload reference differs: {state_id}")
    if expected_by_id:
        mismatches.append("one or more expected output states were not produced")
    expected_ids = tuple(item.state_id for item in inputs.recipe.output_manifest)
    return RefinementVerificationResult(str(inputs.branch.branch_id), str(inputs.recipe.recipe_id),
        "VERIFIED" if not mismatches and tuple(produced_ids) == expected_ids else "MISMATCH",
        tuple(produced_ids), expected_ids, tuple(mismatches))
