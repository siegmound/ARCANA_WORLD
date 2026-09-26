"""Immutable R6 domain state and explicit evidence/support envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .identity import BranchId, DomainStateId, HistoryId, freeze_json, thaw_json

STATE_SCHEMA = "ARCANA_R6_DOMAIN_STATE_V0"


class SupportClass(str, Enum):
    DIRECT_SUPPORTED = "DIRECT_SUPPORTED"
    DERIVED_SUPPORTED = "DERIVED_SUPPORTED"
    SPARSE_AUTHORITY = "SPARSE_AUTHORITY"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    OUTSIDE_SCOPE = "OUTSIDE_SCOPE"
    FIXTURE_ONLY = "FIXTURE_ONLY"


class AuthorityClass(str, Enum):
    DIRECT_AUTHORITY = "DIRECT_AUTHORITY"
    DERIVED_AUTHORITY = "DERIVED_AUTHORITY"
    SPARSE_AUTHORITY = "SPARSE_AUTHORITY"
    FIXTURE_ONLY = "FIXTURE_ONLY"
    NONE = "NONE"


@dataclass(frozen=True, slots=True)
class TimeSupport:
    time_key: str
    coordinate_system: str
    support_kind: str = "INSTANT"

    def __post_init__(self) -> None:
        if not self.time_key or not self.coordinate_system:
            raise ValueError("time key and coordinate system are required")
        if self.support_kind not in {"INSTANT", "INTERVAL", "SNAPSHOT"}:
            raise ValueError("unsupported time support kind")

    def to_dict(self) -> dict[str, str]:
        return {"time_key": self.time_key, "coordinate_system": self.coordinate_system,
                "support_kind": self.support_kind}


@dataclass(frozen=True, slots=True)
class SpatialSupport:
    grid_id: str | None
    cell_ids: tuple[str, ...] = ()
    native_resolution: str | None = None
    selector_kind: str = "CELL_SET"

    def __post_init__(self) -> None:
        object.__setattr__(self, "cell_ids", tuple(str(c) for c in self.cell_ids))
        if len(self.cell_ids) != len(set(self.cell_ids)):
            raise ValueError("spatial cell IDs must be unique")
        if self.selector_kind not in {"CELL_SET", "GRID", "REGION", "GLOBAL", "NONE"}:
            raise ValueError("unsupported spatial selector kind")

    def to_dict(self) -> dict[str, Any]:
        return {"grid_id": self.grid_id, "cell_ids": list(self.cell_ids),
                "native_resolution": self.native_resolution,
                "selector_kind": self.selector_kind}


@dataclass(frozen=True, slots=True)
class DomainStateEnvelope:
    state_id: DomainStateId
    history_id: str
    branch_id: str
    domain: str
    time_support: TimeSupport
    spatial_support: SpatialSupport
    support_class: SupportClass
    authority_class: AuthorityClass
    value: Any
    uncertainty: Mapping[str, Any]
    provenance_ids: tuple[str, ...] = ()
    parent_state_ids: tuple[str, ...] = ()
    payload_ref: str | None = None
    schema_version: str = STATE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != STATE_SCHEMA:
            raise ValueError(f"unsupported state schema: {self.schema_version}")
        if not self.history_id or not self.branch_id or not self.domain:
            raise ValueError("history, branch, and domain are required")
        HistoryId(self.history_id)
        BranchId(self.branch_id)
        object.__setattr__(self, "value", freeze_json(self.value))
        object.__setattr__(self, "uncertainty", freeze_json(self.uncertainty))
        object.__setattr__(self, "provenance_ids", tuple(self.provenance_ids))
        object.__setattr__(self, "parent_state_ids", tuple(self.parent_state_ids))
        if self.support_class in {SupportClass.UNKNOWN, SupportClass.NOT_APPLICABLE,
                                  SupportClass.OUTSIDE_SCOPE} and self.value is not None:
            raise ValueError(f"{self.support_class.value} must not carry a state value")
        identity_body = {
            "schema_version": self.schema_version, "history_id": self.history_id,
            "branch_id": self.branch_id, "domain": self.domain,
            "time_support": self.time_support.to_dict(),
            "spatial_support": self.spatial_support.to_dict(),
            "support_class": self.support_class.value,
            "authority_class": self.authority_class.value,
            "value": thaw_json(self.value), "uncertainty": thaw_json(self.uncertainty),
            "provenance_ids": list(self.provenance_ids),
            "parent_state_ids": list(self.parent_state_ids), "payload_ref": self.payload_ref,
        }
        if DomainStateId.from_payload(identity_body) != self.state_id:
            raise ValueError("state identity does not match state content")

    @classmethod
    def create(cls, *, history_id: str, branch_id: str, domain: str,
               time_support: TimeSupport, spatial_support: SpatialSupport,
               support_class: SupportClass, authority_class: AuthorityClass,
               value: Any = None, uncertainty: Mapping[str, Any] | None = None,
               provenance_ids: tuple[str, ...] = (),
               parent_state_ids: tuple[str, ...] = (),
               payload_ref: str | None = None) -> "DomainStateEnvelope":
        body = {
            "schema_version": STATE_SCHEMA, "history_id": history_id,
            "branch_id": branch_id, "domain": domain,
            "time_support": time_support.to_dict(),
            "spatial_support": spatial_support.to_dict(),
            "support_class": support_class.value,
            "authority_class": authority_class.value, "value": thaw_json(freeze_json(value)),
            "uncertainty": thaw_json(freeze_json(uncertainty or {})),
            "provenance_ids": list(provenance_ids),
            "parent_state_ids": list(parent_state_ids),
            "payload_ref": payload_ref,
        }
        return cls(DomainStateId.from_payload(body), history_id, branch_id, domain,
                   time_support, spatial_support, support_class, authority_class,
                   value, uncertainty or {}, provenance_ids, parent_state_ids,
                   payload_ref)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "state_id": str(self.state_id),
            "history_id": self.history_id, "branch_id": self.branch_id,
            "domain": self.domain, "time_support": self.time_support.to_dict(),
            "spatial_support": self.spatial_support.to_dict(),
            "support_class": self.support_class.value,
            "authority_class": self.authority_class.value, "value": thaw_json(self.value),
            "uncertainty": thaw_json(self.uncertainty),
            "provenance_ids": list(self.provenance_ids),
            "parent_state_ids": list(self.parent_state_ids),
            "payload_ref": self.payload_ref,
        }

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "DomainStateEnvelope":
        if row.get("schema_version") != STATE_SCHEMA:
            raise ValueError("state schema version mismatch")
        spatial = row["spatial_support"]
        state = cls(
            DomainStateId(str(row["state_id"])), str(row["history_id"]),
            str(row["branch_id"]), str(row["domain"]),
            TimeSupport(**row["time_support"]),
            SpatialSupport(spatial.get("grid_id"), tuple(spatial.get("cell_ids", ())),
                           spatial.get("native_resolution"), spatial.get("selector_kind", "CELL_SET")),
            SupportClass(row["support_class"]), AuthorityClass(row["authority_class"]),
            row.get("value"), row.get("uncertainty", {}),
            tuple(row.get("provenance_ids", ())), tuple(row.get("parent_state_ids", ())),
            row.get("payload_ref"), str(row["schema_version"]),
        )
        expected = cls.create(
            history_id=state.history_id, branch_id=state.branch_id, domain=state.domain,
            time_support=state.time_support, spatial_support=state.spatial_support,
            support_class=state.support_class, authority_class=state.authority_class,
            value=state.value, uncertainty=state.uncertainty,
            provenance_ids=state.provenance_ids, parent_state_ids=state.parent_state_ids,
            payload_ref=state.payload_ref,
        ).state_id
        if str(expected) != str(state.state_id):
            raise ValueError("state identity does not match serialized content")
        return state
