"""First-class, domain-neutral forcing records for R6 history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .identity import ForcingId, freeze_json, thaw_json
from .state import AuthorityClass, SpatialSupport, SupportClass, TimeSupport

FORCING_SCHEMA = "ARCANA_R6_FORCING_V0"
_UNSUPPORTED = {SupportClass.UNKNOWN, SupportClass.NOT_APPLICABLE,
                SupportClass.OUTSIDE_SCOPE}


@dataclass(frozen=True, slots=True)
class ForcingRecord:
    forcing_id: ForcingId
    history_id: str
    branch_id: str
    forcing_kind: str
    domain: str
    time_support: TimeSupport
    spatial_support: SpatialSupport
    support_class: SupportClass
    authority_class: AuthorityClass
    value: Any = None
    payload_ref: str | None = None
    provenance_ids: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    schema_version: str = FORCING_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != FORCING_SCHEMA:
            raise ValueError("unsupported forcing schema")
        if not self.history_id or not self.branch_id or not self.forcing_kind or not self.domain:
            raise ValueError("forcing scope, kind, and domain are required")
        if self.support_class in _UNSUPPORTED and (self.value is not None or self.payload_ref is not None):
            raise ValueError(f"{self.support_class.value} forcing must not carry a value or payload")
        if self.value is not None and self.payload_ref is not None:
            raise ValueError("forcing must use either an inline value or payload reference")
        if self.support_class not in _UNSUPPORTED and self.value is None and self.payload_ref is None:
            raise ValueError("supported forcing requires an inline value or payload reference")
        if self.payload_ref is not None and not self.payload_ref:
            raise ValueError("payload reference must be non-empty")
        object.__setattr__(self, "value", freeze_json(self.value))
        object.__setattr__(self, "provenance_ids", tuple(self.provenance_ids))
        object.__setattr__(self, "source_refs", tuple(self.source_refs))
        if ForcingId.from_payload(self._identity_body()) != self.forcing_id:
            raise ValueError("forcing identity does not match content")

    def _identity_body(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "history_id": self.history_id,
                "branch_id": self.branch_id, "forcing_kind": self.forcing_kind,
                "domain": self.domain, "time_support": self.time_support.to_dict(),
                "spatial_support": self.spatial_support.to_dict(),
                "support_class": self.support_class.value,
                "authority_class": self.authority_class.value,
                "value": thaw_json(self.value), "payload_ref": self.payload_ref,
                "provenance_ids": list(self.provenance_ids),
                "source_refs": list(self.source_refs)}

    @classmethod
    def create(cls, *, history_id: str, branch_id: str, forcing_kind: str,
               domain: str, time_support: TimeSupport, spatial_support: SpatialSupport,
               support_class: SupportClass, authority_class: AuthorityClass,
               value: Any = None, payload_ref: str | None = None,
               provenance_ids: tuple[str, ...] = (), source_refs: tuple[str, ...] = ()) -> "ForcingRecord":
        body = {"schema_version": FORCING_SCHEMA, "history_id": history_id,
                "branch_id": branch_id, "forcing_kind": forcing_kind, "domain": domain,
                "time_support": time_support.to_dict(), "spatial_support": spatial_support.to_dict(),
                "support_class": support_class.value, "authority_class": authority_class.value,
                "value": thaw_json(freeze_json(value)), "payload_ref": payload_ref,
                "provenance_ids": list(provenance_ids), "source_refs": list(source_refs)}
        return cls(ForcingId.from_payload(body), history_id, branch_id, forcing_kind, domain,
                   time_support, spatial_support, support_class, authority_class, value,
                   payload_ref, provenance_ids, source_refs)

    def to_dict(self) -> dict[str, Any]:
        return {"forcing_id": str(self.forcing_id), **self._identity_body()}

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "ForcingRecord":
        space = row["spatial_support"]
        return cls(ForcingId(str(row["forcing_id"])), str(row["history_id"]),
                   str(row["branch_id"]), str(row["forcing_kind"]), str(row["domain"]),
                   TimeSupport(**row["time_support"]),
                   SpatialSupport(space.get("grid_id"), tuple(space.get("cell_ids", ())),
                                  space.get("native_resolution"), space.get("selector_kind", "CELL_SET")),
                   SupportClass(row["support_class"]), AuthorityClass(row["authority_class"]),
                   row.get("value"), row.get("payload_ref"), tuple(row.get("provenance_ids", ())),
                   tuple(row.get("source_refs", ())), str(row["schema_version"]))
