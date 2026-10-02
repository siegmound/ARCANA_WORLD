"""Support-aware historical state query and provenance explanation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Mapping

from .checkpoint import CheckpointEnvelope
from .forcing import ForcingRecord
from .provenance import ProvenanceRecord
from .replay import ReplayRecipe
from .state import DomainStateEnvelope, SupportClass
from .store import HistoryStore
from .temporal import EventRecord


@dataclass(frozen=True, slots=True)
class QueryResult:
    status: str
    state: DomainStateEnvelope | None
    provenance: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class HistoryResult:
    """Complete immutable state records in a deterministic exact-filter result."""

    states: tuple[DomainStateEnvelope, ...]
    ordering: str = "TIME_KEY_DOMAIN_SELECTOR_GRID_CELLS_STATE_ID"


class DifferenceStatus(str, Enum):
    COMPARABLE = "COMPARABLE"
    INCOMPATIBLE_SUPPORT = "INCOMPATIBLE_SUPPORT"
    UNKNOWN_INPUT = "UNKNOWN_INPUT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    OUTSIDE_SCOPE = "OUTSIDE_SCOPE"
    MISSING_INPUT = "MISSING_INPUT"
    TYPE_OR_SHAPE_MISMATCH = "TYPE_OR_SHAPE_MISMATCH"


@dataclass(frozen=True, slots=True)
class DifferenceResult:
    status: DifferenceStatus
    state_a: DomainStateEnvelope | None
    state_b: DomainStateEnvelope | None
    value: Any = None
    operation: str | None = None
    equal: bool | None = None
    reason: str | None = None
    uncertainty_propagation: str = "NOT_PROPAGATED"


@dataclass(frozen=True, slots=True)
class WhyResult:
    target_state: DomainStateEnvelope
    state_lineage: tuple[DomainStateEnvelope, ...]
    provenance_records: tuple[ProvenanceRecord, ...]
    events: tuple[EventRecord, ...]
    forcings: tuple[ForcingRecord, ...]
    checkpoints: tuple[CheckpointEnvelope, ...]
    replay_recipes: tuple[ReplayRecipe, ...]
    external_references: tuple[str, ...]
    unresolved_references: tuple[str, ...]

    @property
    def authority_summary(self) -> tuple[tuple[str, str, str], ...]:
        return tuple((str(state.state_id), state.authority_class.value, state.support_class.value)
                     for state in self.state_lineage)


class HistoryQueryService:
    def __init__(self, store: HistoryStore):
        self._store = store

    def state_at(self, *, history_id: str, branch_id: str, domain: str,
                 time_key: str, cell_id: str | None = None) -> QueryResult:
        all_domain = self._store.find_states(history_id=history_id, branch_id=branch_id,
                                             domain=domain)
        if not all_domain:
            return QueryResult("MISSING_DOMAIN", None, None)
        at_time = self._store.find_states(history_id=history_id, branch_id=branch_id,
                                          domain=domain, time_key=time_key)
        if not at_time:
            return QueryResult("MISSING_TIMESTAMP", None, None)
        candidates = self._store.find_states(history_id=history_id, branch_id=branch_id,
                                             domain=domain, time_key=time_key, cell_id=cell_id)
        if not candidates:
            if cell_id is not None:
                if all(state.spatial_support.selector_kind == "CELL_SET" for state in at_time):
                    return QueryResult("OUTSIDE_SUPPORT", None, {
                        "requested_cell_id": cell_id,
                        "declared_cell_ids": sorted({cell for state in at_time
                                                     for cell in state.spatial_support.cell_ids}),
                    })
                return QueryResult("SUPPORT_MISMATCH", None, {
                    "requested_cell_id": cell_id,
                    "selector_kinds": sorted({state.spatial_support.selector_kind
                                               for state in at_time}),
                    "reason": "CELL_MEMBERSHIP_CANNOT_BE_RESOLVED_FOR_DECLARED_SELECTOR",
                })
            return QueryResult("NOT_FOUND", None, None)
        if len(candidates) > 1:
            return QueryResult("CONFLICT", None, {
                "candidate_state_ids": sorted(str(item.state_id) for item in candidates),
                "reason": "MULTIPLE_STATES_MATCH_QUERY; ADJUDICATION_REQUIRED",
            })
        state = candidates[0]
        if state.support_class == SupportClass.UNKNOWN:
            status = "UNKNOWN"
        elif state.support_class == SupportClass.NOT_APPLICABLE:
            status = "NOT_APPLICABLE"
        elif state.support_class == SupportClass.OUTSIDE_SCOPE:
            status = "OUTSIDE_SCOPE"
        else:
            status = "FOUND"
        return QueryResult(status, state, self._store.trace_provenance(state))

    def history(self, *, history_id: str, branch_id: str | None = None,
                domain: str | None = None) -> tuple[DomainStateEnvelope, ...]:
        """Backward-compatible history listing with semantic deterministic ordering."""
        return self.history_result(history_id=history_id, branch_id=branch_id,
                                   domain=domain).states

    def history_result(self, *, history_id: str, branch_id: str | None = None,
                       domain: str | None = None, time_key: str | None = None,
                       cell_id: str | None = None, selector_kind: str | None = None) -> HistoryResult:
        """Return complete state records filtered only by represented exact dimensions."""
        states = self._store.find_states(history_id=history_id, branch_id=branch_id,
            domain=domain, time_key=time_key, cell_id=cell_id)
        if selector_kind is not None:
            states = tuple(state for state in states
                           if state.spatial_support.selector_kind == selector_kind)
        return HistoryResult(tuple(sorted(states, key=_history_order)))

    def difference(self, state_a_id: str, state_b_id: str) -> DifferenceResult:
        """Compare exact retained states. No interpolation or support conversion occurs."""
        try:
            state_a = self._store.read_state(state_a_id)
        except FileNotFoundError:
            return DifferenceResult(DifferenceStatus.MISSING_INPUT, None, None,
                                    reason="STATE_A_MISSING")
        try:
            state_b = self._store.read_state(state_b_id)
        except FileNotFoundError:
            return DifferenceResult(DifferenceStatus.MISSING_INPUT, state_a, None,
                                    reason="STATE_B_MISSING")
        for support_class, status in (
            (SupportClass.UNKNOWN, DifferenceStatus.UNKNOWN_INPUT),
            (SupportClass.NOT_APPLICABLE, DifferenceStatus.NOT_APPLICABLE),
            (SupportClass.OUTSIDE_SCOPE, DifferenceStatus.OUTSIDE_SCOPE),
        ):
            if state_a.support_class == support_class or state_b.support_class == support_class:
                return DifferenceResult(status, state_a, state_b,
                    reason=f"{support_class.value}_IS_NOT_A_NUMERIC_DIFFERENCE")
        incompatible = _support_mismatch(state_a, state_b)
        if incompatible:
            return DifferenceResult(DifferenceStatus.INCOMPATIBLE_SUPPORT, state_a, state_b,
                                    reason=incompatible)
        operation, value, equal, mismatch = _compare_values(state_a.value, state_b.value)
        if mismatch:
            return DifferenceResult(DifferenceStatus.TYPE_OR_SHAPE_MISMATCH, state_a, state_b,
                                    reason=mismatch)
        return DifferenceResult(DifferenceStatus.COMPARABLE, state_a, state_b,
                                value=value, operation=operation, equal=equal)

    def why(self, state_id: str) -> WhyResult:
        """Join only explicitly recorded state/provenance/event/replay relationships."""
        try:
            target = self._store.read_state(state_id)
        except FileNotFoundError:
            raise

        states: dict[str, DomainStateEnvelope] = {}
        provenances: dict[str, ProvenanceRecord] = {}
        events: dict[str, EventRecord] = {}
        forcings: dict[str, ForcingRecord] = {}
        checkpoints: dict[str, CheckpointEnvelope] = {}
        recipes: dict[str, ReplayRecipe] = {}
        recipes_by_output: dict[str, list[ReplayRecipe]] = {}
        for recipe in self._store.replay_recipes():
            recipes_by_output.setdefault(recipe.expected_output_state_id, []).append(recipe)
        external: set[str] = set()
        unresolved: set[str] = set()
        pending_states = [str(target.state_id)]
        pending_provenance: list[str] = []
        pending_refs: list[str] = []
        queued_recipe_ids: set[str] = set()

        def add_state(ref: str) -> None:
            if ref in states:
                return
            try:
                state = self._store.read_state(ref)
            except FileNotFoundError:
                unresolved.add(ref)
                return
            states[ref] = state
            pending_states.append(ref)

        def add_provenance(ref: str) -> None:
            if ref in provenances:
                return
            try:
                record = ProvenanceRecord.from_dict(self._store.read_provenance(ref))
            except FileNotFoundError:
                unresolved.add(ref)
                return
            provenances[ref] = record
            pending_provenance.append(ref)

        def resolve_typed_ref(ref: str) -> bool:
            match = re.fullmatch(r"([a-z0-9]+)_([0-9a-f]{64})", ref)
            if not match:
                return False
            prefix = match.group(1)
            try:
                if prefix == "r6state":
                    add_state(ref)
                elif prefix == "r6prov":
                    add_provenance(ref)
                elif prefix == "r6event":
                    if ref not in events:
                        events[ref] = EventRecord.from_dict(self._store.read_event(ref))
                elif prefix == "r6forcing":
                    if ref not in forcings:
                        forcings[ref] = ForcingRecord.from_dict(self._store.read_forcing(ref))
                elif prefix == "r6checkpoint":
                    if ref not in checkpoints:
                        checkpoints[ref] = CheckpointEnvelope.from_dict(self._store.read_checkpoint(ref))
                elif prefix == "r6recipe":
                    if ref not in recipes:
                        recipes[ref] = self._store.read_replay_recipe(ref)
                else:
                    return False
            except FileNotFoundError:
                unresolved.add(ref)
            return True

        while pending_states or pending_provenance or pending_refs:
            while pending_states:
                ref = pending_states.pop(0)
                state = states.get(ref)
                if state is None:
                    add_state(ref)
                    state = states.get(ref)
                    if state is None:
                        continue
                pending_states.extend(parent for parent in state.parent_state_ids
                                      if parent not in states and parent not in unresolved)
                pending_provenance.extend(pid for pid in state.provenance_ids
                                          if pid not in provenances and pid not in unresolved)
                pending_refs.extend(state.event_refs)
                for recipe in recipes_by_output.get(ref, ()):
                    recipe_ref = str(recipe.recipe_id)
                    if recipe_ref not in queued_recipe_ids:
                        queued_recipe_ids.add(recipe_ref)
                        pending_refs.append(recipe_ref)
            while pending_provenance:
                ref = pending_provenance.pop(0)
                if ref not in provenances:
                    add_provenance(ref)
                record = provenances.get(ref)
                if record is None:
                    continue
                pending_provenance.extend(pid for pid in record.parent_provenance_ids
                                          if pid not in provenances and pid not in unresolved)
                pending_refs.extend(record.input_refs)
                external.update(record.source_refs)
            while pending_refs:
                ref = pending_refs.pop(0)
                if ref in events:
                    event = events[ref]
                    pending_states.extend(sid for sid in event.state_ids
                                          if sid not in states and sid not in unresolved)
                    pending_provenance.extend(pid for pid in event.provenance_refs
                                              if pid not in provenances and pid not in unresolved)
                    continue
                if resolve_typed_ref(ref):
                    event = events.get(ref)
                    if event is not None:
                        pending_states.extend(sid for sid in event.state_ids
                                              if sid not in states and sid not in unresolved)
                        pending_provenance.extend(pid for pid in event.provenance_refs
                                                  if pid not in provenances and pid not in unresolved)
                    forcing = forcings.get(ref)
                    if forcing is not None:
                        pending_provenance.extend(pid for pid in forcing.provenance_ids
                                                  if pid not in provenances and pid not in unresolved)
                        external.update(forcing.source_refs)
                    checkpoint = checkpoints.get(ref)
                    if checkpoint is not None:
                        pending_states.extend(sid for sid in checkpoint.restart_state_ids
                                              if sid not in states and sid not in unresolved)
                        pending_states.extend(sid for sid in checkpoint.retained_history_state_ids
                                              if sid not in states and sid not in unresolved)
                        pending_refs.extend(checkpoint.upstream_dependency_ids)
                        pending_refs.extend(checkpoint.authority_input_refs)
                        pending_refs.extend(checkpoint.provider_manifest_refs)
                    recipe = recipes.get(ref)
                    if recipe is not None:
                        pending_refs.append(recipe.base_checkpoint_id)
                        pending_refs.extend(recipe.forcing_ids)
                        pending_refs.extend(recipe.event_ids)
                        pending_refs.extend(recipe.provenance_ids)
                        pending_refs.extend(recipe.upstream_dependency_ids)
                        pending_states.append(recipe.expected_output_state_id)
                        external.add(f"runtime_identity:{recipe.runtime_identity!r}")
                        external.add(f"configuration_sha256:{recipe.configuration_sha256}")
                        external.add(f"seed_lineage:{recipe.seed_lineage!r}")
                        external.add(f"model_adapter_id:{recipe.model_adapter_id}")
                else:
                    external.add(ref)

        # The ID maps and pending queues collapse cycles and shared ancestors.
        return WhyResult(target, tuple(states[key] for key in sorted(states)),
                         tuple(provenances[key] for key in sorted(provenances)),
                         tuple(events[key] for key in sorted(events)),
                         tuple(forcings[key] for key in sorted(forcings)),
                         tuple(checkpoints[key] for key in sorted(checkpoints)),
                         tuple(recipes[key] for key in sorted(recipes)),
                         tuple(sorted(external)), tuple(sorted(unresolved)))

    def search(self, *, history_id: str, branch_id: str | None = None,
               domain: str | None = None, time_key: str | None = None,
               cell_id: str | None = None,
               equals: dict[str, Any] | None = None) -> tuple[DomainStateEnvelope, ...]:
        """Exact metadata/value search; no interpolation or inferred ordering."""
        matches = self._store.find_states(history_id=history_id, branch_id=branch_id,
            domain=domain, time_key=time_key, cell_id=cell_id)
        predicates = equals or {}
        return tuple(state for state in sorted(matches, key=lambda item: str(item.state_id))
            if all(_value_at(state.value, key) == expected
                   for key, expected in predicates.items()))

    def lineage(self, state_id: str) -> dict[str, Any]:
        states: list[DomainStateEnvelope] = []
        missing: list[str] = []
        seen: set[str] = set()

        def visit(current_id: str) -> None:
            if current_id in seen:
                return
            seen.add(current_id)
            try:
                current = self._store.read_state(current_id)
            except FileNotFoundError:
                missing.append(current_id)
                return
            states.append(current)
            for parent_id in sorted(current.parent_state_ids):
                visit(parent_id)

        visit(state_id)
        if not states:
            raise FileNotFoundError(state_id)
        return {"state_id": state_id,
                "state_lineage": [{"state_id": str(state.state_id),
                    "parent_state_ids": list(state.parent_state_ids),
                    "event_refs": list(state.event_refs),
                    "refinement_lineage": state.refinement_lineage,
                    "provenance": self._store.trace_provenance(state)} for state in states],
                "missing_parent_state_ids": sorted(missing)}

    def available_resolution(self, *, history_id: str, branch_id: str | None = None,
                             domain: str | None = None, time_key: str | None = None,
                             region_cell_ids: tuple[str, ...] = ()) -> dict[str, Any]:
        states = self._store.find_states(history_id=history_id, branch_id=branch_id,
            domain=domain, time_key=time_key)
        region = set(region_cell_ids)
        rows = [state for state in states if not region or
                region.intersection(state.spatial_support.cell_ids)]
        resolutions = sorted({state.spatial_support.native_resolution for state in rows
                              if state.spatial_support.native_resolution is not None})
        return {"status": "AVAILABLE" if rows else "NO_STORED_SUPPORT",
                "native_resolutions": resolutions, "state_count": len(rows),
                "cell_count": len({cell for state in rows for cell in state.spatial_support.cell_ids}),
                "interpolation_performed": False}

    def refinement_candidates(self, *, history_id: str, branch_id: str,
                              domain: str | None = None,
                              region_id: str | None = None) -> tuple[dict[str, Any], ...]:
        rows = self._store.temporal_records(role="REFINEMENT_ANCHOR")
        found = []
        for row in rows:
            details = row.get("details", {})
            if row.get("history_id") != history_id or row.get("branch_id") != branch_id:
                continue
            if domain is not None and domain not in row.get("domain_ids", []):
                continue
            if region_id is not None and details.get("region_id") != region_id:
                continue
            found.append({"record_id": row["record_id"],
                "validation_status": row.get("validation_status", "NOT_VALIDATED"),
                "candidate_status": "RECORDED_UNVALIDATED" if row.get("validation_status") != "VALIDATED" else "RECORDED_VALIDATED",
                "details": details})
        for branch in self._store.refinement_branches():
            if branch.history_id != history_id or branch.parent_branch_id != branch_id:
                continue
            if domain is not None and domain not in branch.requested_domains:
                continue
            if region_id is not None and branch.region_id != region_id:
                continue
            found.append({"record_id": str(branch.branch_id),
                "validation_status": branch.validation_status,
                "candidate_status": "RECORDED_UNVALIDATED" if branch.validation_status != "VALIDATED" else "RECORDED_VALIDATED",
                "details": branch.to_dict()})
        return tuple(sorted(found, key=lambda item: item["record_id"]))


def _history_order(state: DomainStateEnvelope) -> tuple[Any, ...]:
    spatial = state.spatial_support
    return (state.time_support.coordinate_system, state.time_support.support_kind,
            state.time_support.time_key, state.domain, spatial.selector_kind,
            spatial.grid_id or "", tuple(spatial.cell_ids), str(state.state_id))


def _support_mismatch(state_a: DomainStateEnvelope, state_b: DomainStateEnvelope) -> str | None:
    if state_a.domain != state_b.domain:
        return "DOMAIN_SEMANTICS_DIFFER"
    if state_a.spatial_support != state_b.spatial_support:
        return "SPATIAL_SUPPORT_DIFFERS"
    if (state_a.time_support.coordinate_system != state_b.time_support.coordinate_system
            or state_a.time_support.support_kind != state_b.time_support.support_kind):
        return "TEMPORAL_SEMANTICS_DIFFER"
    return None


def _compare_values(value_a: Any, value_b: Any) -> tuple[str | None, Any, bool | None, str | None]:
    numeric_a = isinstance(value_a, (int, float)) and not isinstance(value_a, bool)
    numeric_b = isinstance(value_b, (int, float)) and not isinstance(value_b, bool)
    if numeric_a and numeric_b:
        return "NUMERIC_DELTA_B_MINUS_A", value_b - value_a, value_a == value_b, None
    sequence_a = isinstance(value_a, (tuple, list))
    sequence_b = isinstance(value_b, (tuple, list))
    if sequence_a or sequence_b:
        if not (sequence_a and sequence_b) or len(value_a) != len(value_b):
            return None, None, None, "VALUE_SHAPE_DIFFERS"
        numeric_vector_a = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value_a)
        numeric_vector_b = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value_b)
        if numeric_vector_a and numeric_vector_b:
            delta = tuple(b - a for a, b in zip(value_a, value_b))
            return "NUMERIC_VECTOR_DELTA_B_MINUS_A", delta, tuple(value_a) == tuple(value_b), None
        boolean_vector_a = all(isinstance(v, bool) for v in value_a)
        boolean_vector_b = all(isinstance(v, bool) for v in value_b)
        if boolean_vector_a and boolean_vector_b:
            return "CATEGORICAL_EQUALITY", None, tuple(value_a) == tuple(value_b), None
        scalar_types_a = {type(v) for v in value_a}
        scalar_types_b = {type(v) for v in value_b}
        simple = (all(t in {str, bool, int, float} for t in scalar_types_a | scalar_types_b)
                  and len(scalar_types_a) <= 1 and len(scalar_types_b) <= 1
                  and scalar_types_a == scalar_types_b)
        if simple:
            return "CATEGORICAL_EQUALITY", None, tuple(value_a) == tuple(value_b), None
        return None, None, None, "VALUE_VECTOR_TYPE_OR_SHAPE_UNSUPPORTED"
    if type(value_a) is type(value_b):
        if isinstance(value_a, (str, bool, Mapping)):
            return "CATEGORICAL_EQUALITY", None, value_a == value_b, None
    return None, None, None, "VALUE_TYPES_DIFFER_OR_ARE_UNSUPPORTED"


def _value_at(value: Any, path: str) -> Any:
    current = value
    for key in path.split("."):
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current
