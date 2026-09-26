"""Support-aware historical state query and provenance explanation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
                 time_key: str, cell_id: str) -> QueryResult:
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
