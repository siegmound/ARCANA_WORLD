"""Provider and temporal-authority registries for R6 bootstrap binding."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping
import re

from .temporal import (AuthorityAnchor, ConsumerCheckpoint, EventRecord,
                       HistoricalSnapshot, RefinementAnchor,
                       ProviderTimestamp, SimulationCheckpoint, TemporalRecord)


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    provider_id: str
    product_id: str
    version: str
    variables: Mapping[str, Mapping[str, Any]]
    native_grid: str
    native_resolution: str
    temporal_support: str
    semantics: str
    authority_role: str
    data_cache_sha256: str | None
    provenance_ref: str
    applicability: Mapping[str, Any]
    missing_variables: tuple[str, ...] = ()
    adapter_id: str = ""
    license_ref: str | None = None

    def __post_init__(self) -> None:
        for field in ("provider_id", "product_id", "version", "native_grid",
                      "native_resolution", "temporal_support", "semantics",
                      "authority_role", "provenance_ref", "adapter_id"):
            if not str(getattr(self, field)).strip():
                raise ValueError(f"provider {field} is required")
        if self.data_cache_sha256 is not None and not re.fullmatch(
                r"[0-9a-f]{64}", self.data_cache_sha256):
            raise ValueError("provider cache identity must be a lowercase SHA-256")
        object.__setattr__(self, "missing_variables", tuple(self.missing_variables))
        normalized: dict[str, dict[str, str]] = {}
        for variable, metadata in self.variables.items():
            units = str(metadata.get("units", "")).strip()
            role = str(metadata.get("semantic_role", "")).strip()
            if not units or not role:
                raise ValueError(f"variable {variable!r} requires units and semantic_role")
            normalized[str(variable)] = {"units": units, "semantic_role": role}
        object.__setattr__(self, "variables", MappingProxyType(
            {key: MappingProxyType(value) for key, value in normalized.items()}))
        object.__setattr__(self, "applicability", MappingProxyType(dict(self.applicability)))

    def to_dict(self) -> dict[str, Any]:
        return {"provider_id": self.provider_id, "product_id": self.product_id,
                "version": self.version,
                "variables": {key: dict(value) for key, value in self.variables.items()},
                "native_grid": self.native_grid, "native_resolution": self.native_resolution,
                "temporal_support": self.temporal_support, "semantics": self.semantics,
                "authority_role": self.authority_role,
                "data_cache_sha256": self.data_cache_sha256,
                "provenance_ref": self.provenance_ref,
                "applicability": dict(self.applicability),
                "missing_variables": list(self.missing_variables),
                "adapter_id": self.adapter_id, "license_ref": self.license_ref}


class ProviderRegistry:
    """Version-aware registry; identical IDs cannot be silently rebound."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderDescriptor] = {}

    def register(self, provider: ProviderDescriptor) -> None:
        prior = self._providers.get(provider.provider_id)
        if prior is not None and prior != provider:
            raise ValueError(f"provider ID is already bound differently: {provider.provider_id}")
        self._providers[provider.provider_id] = provider

    def get(self, provider_id: str) -> ProviderDescriptor:
        return self._providers[provider_id]

    def all(self) -> tuple[ProviderDescriptor, ...]:
        return tuple(self._providers[key] for key in sorted(self._providers))


class TemporalAuthorityRegistry:
    """Keeps source anchors distinct from snapshots, events, and checkpoints."""

    _allowed = (ProviderTimestamp, AuthorityAnchor, SimulationCheckpoint, HistoricalSnapshot,
                EventRecord, RefinementAnchor, ConsumerCheckpoint)

    def __init__(self) -> None:
        self._records: dict[str, TemporalRecord] = {}

    def register(self, record: TemporalRecord) -> None:
        if type(record) not in self._allowed:
            raise TypeError("unsupported temporal record role")
        prior = self._records.get(record.record_id)
        if prior is not None and prior != record:
            raise ValueError(f"temporal record identity conflict: {record.record_id}")
        self._records[record.record_id] = record

    def records(self, role: str | None = None) -> tuple[TemporalRecord, ...]:
        rows = (row for row in self._records.values() if role is None or row.ROLE == role)
        return tuple(sorted(rows, key=lambda row: (row.time_key, row.ROLE, row.record_id)))

    def persist(self, store: Any) -> tuple[str, ...]:
        return tuple(store.append_temporal(row) for row in self.records())
