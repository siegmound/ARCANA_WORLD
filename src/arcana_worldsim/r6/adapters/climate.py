"""Metadata-first climate provider binding; deliberately performs no acquisition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import math
import re

from ..identity import ProviderBindingId
from ..provenance import ProvenanceRecord
from ..state import (AuthorityClass, DomainStateEnvelope, SpatialSupport,
                     SupportClass, TimeSupport)


@dataclass(frozen=True, slots=True)
class ClimateBindingResult:
    binding_id: ProviderBindingId
    state: DomainStateEnvelope
    provenance: ProvenanceRecord
    binding_record: Mapping[str, Any]

    def persist(self, store: Any) -> None:
        store.append_provider_binding(str(self.binding_id), dict(self.binding_record))
        store.append_provenance(self.provenance)
        store.append_state(self.state)


class ClimateProviderAdapter:
    """Validate caller-supplied provider metadata and values; never reads/downloads files."""

    def bind(self, *, history_id: str, branch_id: str, provider_id: str,
             source_sha256: str, source_semantics: str, time_key: str,
             coordinate_system: str, grid_id: str, cell_ids: tuple[str, ...],
             variable_metadata: Mapping[str, Mapping[str, Any]],
             values: Mapping[str, Any], required_units: Mapping[str, str],
             authority_class: AuthorityClass = AuthorityClass.FIXTURE_ONLY,
             support_class: SupportClass = SupportClass.FIXTURE_ONLY,
             native_resolution: str | None = None,
             authority_refs: tuple[str, ...] = (),
             applicability: Mapping[str, Any] | None = None) -> ClimateBindingResult:
        fixture = (authority_class is AuthorityClass.FIXTURE_ONLY
                   and support_class is SupportClass.FIXTURE_ONLY)
        if not fixture:
            if (authority_class in {AuthorityClass.NONE, AuthorityClass.FIXTURE_ONLY}
                    or support_class in {SupportClass.UNKNOWN, SupportClass.NOT_APPLICABLE,
                                         SupportClass.OUTSIDE_SCOPE, SupportClass.FIXTURE_ONLY}
                    or not authority_refs or not applicability):
                raise ValueError("governed climate binding requires authority refs and applicability")
        if not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
            raise ValueError("provider source identity must be a SHA-256 digest")
        if not provider_id or not source_semantics:
            raise ValueError("provider identity and source semantics are required")
        if set(required_units) - set(variable_metadata) or set(required_units) - set(values):
            raise ValueError("required climate variable is missing")
        normalized_metadata: dict[str, Any] = {}
        for semantic, units in required_units.items():
            meta = variable_metadata[semantic]
            if meta.get("units") != units:
                raise ValueError(f"unit mismatch for {semantic}: expected {units}")
            if not meta.get("dimensions") or not meta.get("temporal_semantics"):
                raise ValueError(f"incomplete dimensions/temporal semantics for {semantic}")
            _validate_finite(values[semantic])
            normalized_metadata[semantic] = {
                "source_variable": str(meta.get("source_variable", semantic)),
                "units": units, "dimensions": list(meta["dimensions"]),
                "temporal_semantics": str(meta["temporal_semantics"]),
            }
        binding_body = {
            "provider_id": provider_id, "source_sha256": source_sha256,
            "source_semantics": source_semantics, "time_key": time_key,
            "coordinate_system": coordinate_system, "grid_id": grid_id,
            "cell_ids": list(cell_ids), "variables": normalized_metadata,
            "authority_class": authority_class.value, "support_class": support_class.value,
            "authority_refs": list(authority_refs),
            "applicability": dict(applicability or {}),
        }
        binding_id = ProviderBindingId.from_payload(binding_body)
        provenance = ProvenanceRecord.create(
            activity="R6_CLIMATE_PROVIDER_BINDING_V0",
            source_refs=(str(binding_id), provider_id, source_sha256, *authority_refs),
            attributes={"semantic_role": "fixture" if fixture else "governed_provider_state",
                        "source_semantics": source_semantics},
        )
        state = DomainStateEnvelope.create(
            history_id=history_id, branch_id=branch_id, domain="climate",
            time_support=TimeSupport(time_key, coordinate_system),
            spatial_support=SpatialSupport(grid_id, tuple(cell_ids), native_resolution),
            support_class=support_class, authority_class=authority_class,
            value={"variables": dict(values), "variable_metadata": normalized_metadata},
            uncertainty={"classification": "NOT_ASSESSED_BY_METADATA_ADAPTER",
                         "applicability": dict(applicability or {})},
            provenance_ids=(str(provenance.record_id),),
        )
        return ClimateBindingResult(binding_id, state, provenance, binding_body)


def _validate_finite(value: Any) -> None:
    if isinstance(value, bool) or value is None:
        raise ValueError("climate values must be numeric and finite")
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise ValueError("climate values must be finite")
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _validate_finite(item)
        return
    raise ValueError("climate values must be numeric arrays/scalars")
