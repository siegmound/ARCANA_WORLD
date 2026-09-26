"""Distinct temporal roles; this module defines records, not a scheduler."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, ClassVar, Mapping
import json

from .identity import EventId, freeze_json, thaw_json


@dataclass(frozen=True, slots=True)
class TemporalRecord:
    record_id: str
    history_id: str
    branch_id: str
    time_key: str
    domain_ids: tuple[str, ...]
    state_ids: tuple[str, ...]
    authority_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    validation_status: str
    details: Mapping[str, Any]
    ROLE: ClassVar[str] = "TEMPORAL_RECORD"

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain_ids", tuple(self.domain_ids))
        object.__setattr__(self, "state_ids", tuple(self.state_ids))
        object.__setattr__(self, "authority_refs", tuple(self.authority_refs))
        object.__setattr__(self, "provenance_refs", tuple(self.provenance_refs))
        object.__setattr__(self, "details", freeze_json(self.details))

    @classmethod
    def create(cls, *, history_id: str, branch_id: str, time_key: str,
               domain_ids: tuple[str, ...] = (), state_ids: tuple[str, ...] = (),
               authority_refs: tuple[str, ...] = (), provenance_refs: tuple[str, ...] = (),
               validation_status: str = "NOT_VALIDATED",
               details: Mapping[str, Any] | None = None) -> "TemporalRecord":
        body = {"role": cls.ROLE, "history_id": history_id, "branch_id": branch_id,
                "time_key": time_key, "domain_ids": list(domain_ids),
                "state_ids": list(state_ids), "authority_refs": list(authority_refs),
                "provenance_refs": list(provenance_refs),
                "validation_status": validation_status, "details": thaw_json(freeze_json(details or {}))}
        digest = sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False, allow_nan=False).encode()).hexdigest()
        record_id = str(EventId.from_payload(body)) if cls.ROLE == "EVENT_RECORD" else f"{cls.ROLE.lower()}_{digest}"
        return cls(record_id, history_id, branch_id, time_key,
                   tuple(domain_ids), tuple(state_ids), tuple(authority_refs),
                   tuple(provenance_refs), validation_status, details or {})

    def to_dict(self) -> dict[str, Any]:
        return {"record_id": self.record_id, "role": self.ROLE,
                "history_id": self.history_id, "branch_id": self.branch_id,
                "time_key": self.time_key, "domain_ids": list(self.domain_ids),
                "state_ids": list(self.state_ids), "authority_refs": list(self.authority_refs),
                "provenance_refs": list(self.provenance_refs),
                "validation_status": self.validation_status, "details": thaw_json(self.details)}


@dataclass(frozen=True, slots=True)
class AuthorityAnchor(TemporalRecord):
    ROLE: ClassVar[str] = "AUTHORITY_ANCHOR"


@dataclass(frozen=True, slots=True)
class ProviderTimestamp(TemporalRecord):
    ROLE: ClassVar[str] = "PROVIDER_TIMESTAMP"


@dataclass(frozen=True, slots=True)
class SimulationCheckpoint(TemporalRecord):
    ROLE: ClassVar[str] = "SIMULATION_CHECKPOINT"


@dataclass(frozen=True, slots=True)
class HistoricalSnapshot(TemporalRecord):
    ROLE: ClassVar[str] = "HISTORICAL_SNAPSHOT"


@dataclass(frozen=True, slots=True)
class EventRecord(TemporalRecord):
    ROLE: ClassVar[str] = "EVENT_RECORD"


@dataclass(frozen=True, slots=True)
class RefinementAnchor(TemporalRecord):
    ROLE: ClassVar[str] = "REFINEMENT_ANCHOR"


@dataclass(frozen=True, slots=True)
class ConsumerCheckpoint(TemporalRecord):
    ROLE: ClassVar[str] = "CONSUMER_CHECKPOINT"
