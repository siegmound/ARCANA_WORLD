"""Small traversable provenance records for explaining stored R6 state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .identity import ProvenanceRecordId, freeze_json, thaw_json


class ProvenanceIntegrityError(ValueError):
    """Raised when a state refers to missing/corrupt provenance records."""


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    record_id: ProvenanceRecordId
    activity: str
    input_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    parent_provenance_ids: tuple[str, ...]
    output_state_ids: tuple[str, ...]
    attributes: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_refs", tuple(self.input_refs))
        object.__setattr__(self, "source_refs", tuple(self.source_refs))
        object.__setattr__(self, "parent_provenance_ids", tuple(self.parent_provenance_ids))
        object.__setattr__(self, "output_state_ids", tuple(self.output_state_ids))
        object.__setattr__(self, "attributes", freeze_json(self.attributes))

    @classmethod
    def create(cls, *, activity: str, input_refs: tuple[str, ...] = (),
               source_refs: tuple[str, ...] = (),
               parent_provenance_ids: tuple[str, ...] = (),
               output_state_ids: tuple[str, ...] = (),
               attributes: Mapping[str, Any] | None = None) -> "ProvenanceRecord":
        body = {"activity": activity, "input_refs": list(input_refs),
                "source_refs": list(source_refs),
                "parent_provenance_ids": list(parent_provenance_ids),
                "output_state_ids": list(output_state_ids),
                "attributes": dict(attributes or {})}
        return cls(ProvenanceRecordId.from_payload(body), activity, tuple(input_refs),
                   tuple(source_refs), tuple(parent_provenance_ids),
                   tuple(output_state_ids), dict(attributes or {}))

    def to_dict(self) -> dict[str, Any]:
        return {"record_id": str(self.record_id), "activity": self.activity,
                "input_refs": list(self.input_refs), "source_refs": list(self.source_refs),
                "parent_provenance_ids": list(self.parent_provenance_ids),
                "output_state_ids": list(self.output_state_ids),
                "attributes": thaw_json(self.attributes)}
