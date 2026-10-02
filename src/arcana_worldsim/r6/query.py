"""Support-aware historical state query and provenance explanation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .state import DomainStateEnvelope, SupportClass
from .store import HistoryStore


@dataclass(frozen=True, slots=True)
class QueryResult:
    status: str
    state: DomainStateEnvelope | None
    provenance: dict[str, Any] | None


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
        """Return stored states in deterministic identity order."""
        return tuple(sorted(self._store.find_states(history_id=history_id,
            branch_id=branch_id, domain=domain), key=lambda state: str(state.state_id)))

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


def _value_at(value: Any, path: str) -> Any:
    current = value
    for key in path.split("."):
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current
