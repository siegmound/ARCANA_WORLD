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

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "TemporalRecord":
        if row.get("role") != cls.ROLE:
            raise ValueError("temporal record role mismatch")
        record = cls(str(row["record_id"]), str(row["history_id"]),
            str(row["branch_id"]), str(row["time_key"]),
            tuple(row.get("domain_ids", ())), tuple(row.get("state_ids", ())),
            tuple(row.get("authority_refs", ())), tuple(row.get("provenance_refs", ())),
            str(row.get("validation_status", "NOT_VALIDATED")), row.get("details", {}))
        body = {"role": cls.ROLE, "history_id": record.history_id,
            "branch_id": record.branch_id, "time_key": record.time_key,
            "domain_ids": list(record.domain_ids), "state_ids": list(record.state_ids),
            "authority_refs": list(record.authority_refs),
            "provenance_refs": list(record.provenance_refs),
            "validation_status": record.validation_status,
            "details": thaw_json(record.details)}
        digest = sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False).encode()).hexdigest()
        expected = str(EventId.from_payload(body)) if cls.ROLE == "EVENT_RECORD" else f"{cls.ROLE.lower()}_{digest}"
        if expected != record.record_id:
            raise ValueError("temporal record identity does not match content")
        return record


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

    @classmethod
    def create(cls, *, history_id: str, branch_id: str, time_key: str,
               domain_ids: tuple[str, ...] = (), state_ids: tuple[str, ...] = (),
               authority_refs: tuple[str, ...] = (), provenance_refs: tuple[str, ...] = (),
               validation_status: str = "NOT_VALIDATED",
               details: Mapping[str, Any] | None = None,
               temporal_support: Mapping[str, Any] | None = None,
               spatial_support: Mapping[str, Any] | None = None,
               trigger_ref: str | None = None, cause_ref: str | None = None,
               before_state_ids: tuple[str, ...] = (), after_state_ids: tuple[str, ...] = (),
               causal_dependency_ids: tuple[str, ...] = ()) -> "EventRecord":
        contract = {"temporal_support": dict(temporal_support or {"time_key": time_key}),
                    "spatial_support": dict(spatial_support or {}),
                    "trigger_ref": trigger_ref, "cause_ref": cause_ref,
                    "before_state_ids": list(before_state_ids),
                    "after_state_ids": list(after_state_ids),
                    "causal_dependency_ids": list(causal_dependency_ids)}
        event_details = dict(details or {})
        event_details["event_contract"] = contract
        states = tuple(dict.fromkeys((*state_ids, *before_state_ids, *after_state_ids)))
        return TemporalRecord.create.__func__(cls, history_id=history_id, branch_id=branch_id,
            time_key=time_key, domain_ids=domain_ids, state_ids=states,
            authority_refs=authority_refs, provenance_refs=provenance_refs,
            validation_status=validation_status, details=event_details)

    @property
    def event_contract(self) -> Mapping[str, Any]:
        return self.details.get("event_contract", {})

    @property
    def temporal_support(self) -> Mapping[str, Any]:
        return self.event_contract.get("temporal_support", {})

    @property
    def spatial_support(self) -> Mapping[str, Any]:
        return self.event_contract.get("spatial_support", {})

    @property
    def trigger_ref(self) -> str | None:
        return self.event_contract.get("trigger_ref")

    @property
    def cause_ref(self) -> str | None:
        return self.event_contract.get("cause_ref")

    @property
    def before_state_ids(self) -> tuple[str, ...]:
        return tuple(self.event_contract.get("before_state_ids", ()))

    @property
    def after_state_ids(self) -> tuple[str, ...]:
        return tuple(self.event_contract.get("after_state_ids", ()))

    @property
    def causal_dependency_ids(self) -> tuple[str, ...]:
        return tuple(self.event_contract.get("causal_dependency_ids", ()))


@dataclass(frozen=True, slots=True)
class RefinementAnchor(TemporalRecord):
    ROLE: ClassVar[str] = "REFINEMENT_ANCHOR"


@dataclass(frozen=True, slots=True)
class ConsumerCheckpoint(TemporalRecord):
    ROLE: ClassVar[str] = "CONSUMER_CHECKPOINT"


_TEMPORAL_RECORD_TYPES = {
    record_type.ROLE: record_type
    for record_type in (AuthorityAnchor, ProviderTimestamp, SimulationCheckpoint,
                        HistoricalSnapshot, EventRecord, RefinementAnchor,
                        ConsumerCheckpoint)
}


def temporal_record_from_dict(row: Mapping[str, Any]) -> TemporalRecord:
    """Reconstruct and identity-check a serialized record using its declared role."""
    role = row.get("role")
    record_type = _TEMPORAL_RECORD_TYPES.get(str(role))
    if record_type is None:
        raise ValueError(f"unsupported temporal record role: {role!r}")
    return record_type.from_dict(row)
