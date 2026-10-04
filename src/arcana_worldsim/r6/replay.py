"""Closed-input replay validation and bounded deterministic runner boundary."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Mapping, TYPE_CHECKING

from .checkpoint import CheckpointEnvelope
from .forcing import ForcingRecord
from .identity import (PayloadIdentity, ReplayRecipeId, freeze_json,
                       thaw_json, verify_payload)
from .provenance import ProvenanceRecord
from .state import DomainStateEnvelope, SupportClass
from .temporal import EventRecord

if TYPE_CHECKING:
    from .store import HistoryStore

REPLAY_RECIPE_SCHEMA = "ARCANA_R6_REPLAY_RECIPE_V0"
_UNSUPPORTED = {SupportClass.UNKNOWN, SupportClass.NOT_APPLICABLE,
                SupportClass.OUTSIDE_SCOPE}


def _pinned_store_read(method):
    @wraps(method)
    def wrapped(store, *args, **kwargs):
        with store.read_view():
            return method(store, *args, **kwargs)
    return wrapped


class ReplayInputError(ValueError):
    """Replay cannot proceed because its declared input closure is not valid."""


@dataclass(frozen=True, slots=True)
class ReplayRecipe:
    recipe_id: ReplayRecipeId
    history_id: str
    branch_id: str
    base_checkpoint_id: str
    runtime_identity: Mapping[str, Any]
    configuration_sha256: str
    seed_lineage: Mapping[str, Any]
    forcing_ids: tuple[str, ...]
    event_ids: tuple[str, ...]
    upstream_dependency_ids: tuple[str, ...]
    provenance_ids: tuple[str, ...]
    expected_output_state_id: str
    expected_payload_identity: PayloadIdentity | None
    model_adapter_id: str
    schema_version: str = REPLAY_RECIPE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != REPLAY_RECIPE_SCHEMA:
            raise ValueError("unsupported replay recipe schema")
        if not all((self.history_id, self.branch_id, self.base_checkpoint_id,
                    self.expected_output_state_id, self.model_adapter_id)):
            raise ValueError("replay scope, checkpoint, output, and adapter are required")
        if len(self.configuration_sha256) != 64:
            raise ValueError("invalid replay configuration SHA-256")
        if any(character not in "0123456789abcdef" for character in self.configuration_sha256):
            raise ValueError("invalid replay configuration SHA-256")
        for label, refs in (("forcing", self.forcing_ids), ("event", self.event_ids),
                            ("dependency", self.upstream_dependency_ids),
                            ("provenance", self.provenance_ids)):
            if len(refs) != len(set(refs)):
                raise ValueError(f"duplicate {label} identity in replay recipe")
        object.__setattr__(self, "runtime_identity", freeze_json(self.runtime_identity))
        object.__setattr__(self, "seed_lineage", freeze_json(self.seed_lineage))
        for name in ("forcing_ids", "event_ids", "upstream_dependency_ids", "provenance_ids"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        if ReplayRecipeId.from_payload(self._identity_body()) != self.recipe_id:
            raise ValueError("replay recipe identity does not match content")

    def _identity_body(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "history_id": self.history_id,
                "branch_id": self.branch_id, "base_checkpoint_id": self.base_checkpoint_id,
                "runtime_identity": thaw_json(self.runtime_identity),
                "configuration_sha256": self.configuration_sha256,
                "seed_lineage": thaw_json(self.seed_lineage),
                "forcing_ids": list(self.forcing_ids), "event_ids": list(self.event_ids),
                "upstream_dependency_ids": list(self.upstream_dependency_ids),
                "provenance_ids": list(self.provenance_ids),
                "expected_output_state_id": self.expected_output_state_id,
                "expected_payload_identity": (None if self.expected_payload_identity is None
                                              else self.expected_payload_identity.to_dict()),
                "model_adapter_id": self.model_adapter_id}

    @classmethod
    def create(cls, *, history_id: str, branch_id: str, base_checkpoint_id: str,
               runtime_identity: Mapping[str, Any], configuration_sha256: str,
               seed_lineage: Mapping[str, Any], forcing_ids: tuple[str, ...],
               expected_output_state_id: str, model_adapter_id: str,
               event_ids: tuple[str, ...] = (), upstream_dependency_ids: tuple[str, ...] = (),
               provenance_ids: tuple[str, ...] = (),
               expected_payload_identity: PayloadIdentity | None = None) -> "ReplayRecipe":
        body = {"schema_version": REPLAY_RECIPE_SCHEMA, "history_id": history_id,
                "branch_id": branch_id, "base_checkpoint_id": base_checkpoint_id,
                "runtime_identity": dict(runtime_identity),
                "configuration_sha256": configuration_sha256, "seed_lineage": dict(seed_lineage),
                "forcing_ids": list(forcing_ids), "event_ids": list(event_ids),
                "upstream_dependency_ids": list(upstream_dependency_ids),
                "provenance_ids": list(provenance_ids),
                "expected_output_state_id": expected_output_state_id,
                "expected_payload_identity": (None if expected_payload_identity is None
                                              else expected_payload_identity.to_dict()),
                "model_adapter_id": model_adapter_id}
        return cls(ReplayRecipeId.from_payload(body), history_id, branch_id, base_checkpoint_id,
                   runtime_identity, configuration_sha256, seed_lineage, forcing_ids, event_ids,
                   upstream_dependency_ids, provenance_ids, expected_output_state_id,
                   expected_payload_identity, model_adapter_id)

    def to_dict(self) -> dict[str, Any]:
        return {"recipe_id": str(self.recipe_id), **self._identity_body()}

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "ReplayRecipe":
        payload = row.get("expected_payload_identity")
        identity = None if payload is None else PayloadIdentity(str(payload["algorithm"]), str(payload["digest"]))
        return cls(ReplayRecipeId(str(row["recipe_id"])), str(row["history_id"]),
                   str(row["branch_id"]), str(row["base_checkpoint_id"]),
                   row["runtime_identity"], str(row["configuration_sha256"]), row["seed_lineage"],
                   tuple(row["forcing_ids"]), tuple(row.get("event_ids", ())),
                   tuple(row.get("upstream_dependency_ids", ())), tuple(row.get("provenance_ids", ())),
                   str(row["expected_output_state_id"]), identity, str(row["model_adapter_id"]),
                   str(row["schema_version"]))


@dataclass(frozen=True, slots=True)
class ResolvedReplayInputs:
    checkpoint: CheckpointEnvelope
    base_states: tuple[DomainStateEnvelope, ...]
    forcings: tuple[ForcingRecord, ...]
    events: tuple[EventRecord, ...]
    expected_state: DomainStateEnvelope
    provenance: tuple[ProvenanceRecord, ...]
    forcing_payloads: Mapping[str, bytes]


@dataclass(frozen=True, slots=True)
class ReplayExecutionOutput:
    state: DomainStateEnvelope
    payload_bytes: bytes | None = None


@dataclass(frozen=True, slots=True)
class ReplayVerificationResult:
    recipe_id: str
    base_checkpoint_id: str
    produced_state_id: str
    expected_state_id: str
    produced_payload_identity: PayloadIdentity | None
    expected_payload_identity: PayloadIdentity | None
    status: str
    mismatches: tuple[str, ...]


@_pinned_store_read
def validate_replay_inputs(store: "HistoryStore", recipe: ReplayRecipe, *,
                           payload_resolver: Callable[[str], bytes | bytearray | memoryview | Path | str] | None = None
                           ) -> ResolvedReplayInputs:
    """Resolve exactly the declared closure; never search for substitutes."""
    try:
        checkpoint = CheckpointEnvelope.from_dict(store.read_checkpoint(recipe.base_checkpoint_id))
        if (checkpoint.history_id, checkpoint.branch_id) != (recipe.history_id, recipe.branch_id):
            raise ReplayInputError("recipe/checkpoint scope mismatch")
        if checkpoint.validation_status != "VALIDATED":
            raise ReplayInputError("base checkpoint is not validated")
        if (dict(checkpoint.runtime_identity) != thaw_json(recipe.runtime_identity)
                or checkpoint.configuration_sha256 != recipe.configuration_sha256
                or thaw_json(checkpoint.seed_lineage) != thaw_json(recipe.seed_lineage)):
            raise ReplayInputError("recipe runtime/configuration/seed differs from checkpoint")
        if tuple(checkpoint.upstream_dependency_ids) != recipe.upstream_dependency_ids:
            raise ReplayInputError("recipe dependencies differ from checkpoint")

        base_states = tuple(store.read_state(state_id) for state_id in checkpoint.restart_state_ids)
        if not base_states:
            raise ReplayInputError("checkpoint has no restart states")
        for state in base_states:
            if (state.history_id, state.branch_id) != (recipe.history_id, recipe.branch_id):
                raise ReplayInputError("restart state scope mismatch")
            if state.support_class in _UNSUPPORTED:
                raise ReplayInputError("restart state has unusable support")

        forcings = tuple(ForcingRecord.from_dict(store.read_forcing(forcing_id))
                         for forcing_id in recipe.forcing_ids)
        payloads: dict[str, bytes] = {}
        for forcing in forcings:
            if (forcing.history_id, forcing.branch_id) != (recipe.history_id, recipe.branch_id):
                raise ReplayInputError("forcing scope mismatch")
            if forcing.support_class in _UNSUPPORTED:
                raise ReplayInputError("forcing has unusable support")
            if forcing.payload_ref is not None:
                if payload_resolver is None:
                    raise ReplayInputError("forcing payload needs a resolver")
                source = payload_resolver(forcing.payload_ref)
                identity = verify_payload(forcing.payload_ref, source)
                if isinstance(source, (bytes, bytearray, memoryview)):
                    payloads[str(forcing.forcing_id)] = bytes(source)
                elif isinstance(source, (str, Path)):
                    payloads[str(forcing.forcing_id)] = Path(source).read_bytes()
                else:
                    raise ReplayInputError("payload resolver must return bytes or a path")
                if PayloadIdentity.from_bytes(payloads[str(forcing.forcing_id)]) != identity:
                    raise ReplayInputError("resolved forcing payload identity mismatch")

        events = tuple(EventRecord.from_dict(store.read_event(event_id)) for event_id in recipe.event_ids)
        for event in events:
            if (event.history_id, event.branch_id) != (recipe.history_id, recipe.branch_id):
                raise ReplayInputError("event scope mismatch")
            for state_id in event.state_ids:
                event_state = store.read_state(state_id)
                if (event_state.history_id, event_state.branch_id) != (recipe.history_id, recipe.branch_id):
                    raise ReplayInputError("event state scope mismatch")

        expected = store.read_state(recipe.expected_output_state_id)
        if (expected.history_id, expected.branch_id) != (recipe.history_id, recipe.branch_id):
            raise ReplayInputError("expected output state scope mismatch")
        provenance_ids = list(recipe.provenance_ids)
        for state in (*base_states, expected):
            provenance_ids.extend(state.provenance_ids)
        for forcing in forcings:
            provenance_ids.extend(forcing.provenance_ids)
        for event in events:
            provenance_ids.extend(event.provenance_refs)
        records: dict[str, ProvenanceRecord] = {}
        pending = list(dict.fromkeys(provenance_ids))
        while pending:
            provenance_id = pending.pop(0)
            if provenance_id in records:
                continue
            record = ProvenanceRecord.from_dict(store.read_provenance(provenance_id))
            records[provenance_id] = record
            pending.extend(record.parent_provenance_ids)

        # Declared dependencies must resolve to a typed record or a traversed provenance record.
        resolved_ids = {str(state.state_id) for state in base_states}
        resolved_ids.update(str(forcing.forcing_id) for forcing in forcings)
        resolved_ids.update(event.record_id for event in events)
        resolved_ids.update(state_id for event in events for state_id in event.state_ids)
        resolved_ids.update(records)
        for dependency in recipe.upstream_dependency_ids:
            if dependency not in resolved_ids:
                try:
                    store.read_state(dependency)
                except Exception as exc:
                    raise ReplayInputError(f"unresolved dependency identity: {dependency}") from exc
        return ResolvedReplayInputs(checkpoint, base_states, forcings, events, expected,
                                    tuple(records[key] for key in sorted(records)), payloads)
    except ReplayInputError:
        raise
    except Exception as exc:
        raise ReplayInputError(f"replay input closure failed: {exc}") from exc


@_pinned_store_read
def execute_replay(store: "HistoryStore", recipe: ReplayRecipe,
                   deterministic_runner: Callable[[ReplayRecipe, ResolvedReplayInputs], ReplayExecutionOutput],
                   *, payload_resolver: Callable[[str], bytes | bytearray | memoryview | Path | str] | None = None
                   ) -> ReplayVerificationResult:
    """Run an injected adapter on immutable resolved inputs and verify its candidate output."""
    inputs = validate_replay_inputs(store, recipe, payload_resolver=payload_resolver)
    output = deterministic_runner(recipe, inputs)
    if not isinstance(output, ReplayExecutionOutput):
        raise TypeError("runner must return ReplayExecutionOutput")
    produced_payload = (None if output.payload_bytes is None
                        else PayloadIdentity.from_bytes(output.payload_bytes))
    mismatches: list[str] = []
    if str(output.state.state_id) != recipe.expected_output_state_id:
        mismatches.append("produced state identity differs from expected")
    if (output.state.history_id, output.state.branch_id) != (recipe.history_id, recipe.branch_id):
        mismatches.append("produced state scope differs from recipe")
    expected = inputs.expected_state
    if (output.state.authority_class != expected.authority_class
            or output.state.support_class != expected.support_class):
        mismatches.append("produced state authority/support differs from expected")
    if output.state.payload_ref != expected.payload_ref:
        mismatches.append("produced state payload reference differs from expected")
    expected_payload = recipe.expected_payload_identity
    if expected_payload is not None:
        if produced_payload != expected_payload:
            mismatches.append("produced payload identity differs from expected")
        if output.state.payload_reference is None or output.state.payload_reference.identity != expected_payload:
            mismatches.append("expected state payload reference does not bind expected identity")
    elif produced_payload is not None:
        mismatches.append("runner produced an undeclared payload")
    return ReplayVerificationResult(str(recipe.recipe_id), recipe.base_checkpoint_id,
        str(output.state.state_id), recipe.expected_output_state_id, produced_payload,
        expected_payload, "VERIFIED" if not mismatches else "MISMATCH", tuple(mismatches))
