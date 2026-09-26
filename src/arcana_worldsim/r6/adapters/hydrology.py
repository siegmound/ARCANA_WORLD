"""Fixture-only R6 boundary for the governed B6 hydrology semantics."""

from __future__ import annotations

import math
from typing import Any, Mapping

from ..provenance import ProvenanceRecord
from ..state import (AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass)


class HydrologyAdapterError(ValueError):
    pass


class HydrologyAdapterV0:
    """Validate R6 inputs and normalize a fixture; never imports or runs B6 code."""

    LEGACY_CONTRACT = "R5_17_B6_D1_CANONICAL_HYDROLOGY_REPLAY_CONTRACT.json"
    LEGACY_REPLAY = "R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY.json"
    MODE = "FIXTURE_ONLY_NO_LEGACY_EXECUTION"

    def normalize_fixture(self, *, climate: DomainStateEnvelope,
                          geography: DomainStateEnvelope,
                          shoreline: DomainStateEnvelope,
                          output_values: Mapping[str, Any],
                          output_units: Mapping[str, str]) -> tuple[DomainStateEnvelope, ProvenanceRecord]:
        inputs = (climate, geography, shoreline)
        if tuple(state.domain for state in inputs) != ("climate", "geography", "shoreline"):
            raise HydrologyAdapterError("expected climate, geography, shoreline in order")
        times = {s.time_support.time_key for s in inputs}
        histories = {s.history_id for s in inputs}
        branches = {s.branch_id for s in inputs}
        grids = {s.spatial_support.grid_id for s in inputs}
        cells = {s.spatial_support.cell_ids for s in inputs}
        if (len(times) != 1 or len(histories) != 1 or len(branches) != 1
                or len(grids) != 1 or len(cells) != 1):
            raise HydrologyAdapterError("input temporal/spatial support does not align exactly")
        if set(output_values) != set(output_units) or not output_values:
            raise HydrologyAdapterError("every fixture output requires an explicit unit")
        if any(not str(unit).strip() for unit in output_units.values()):
            raise HydrologyAdapterError("fixture output units must be non-empty")
        for field, field_value in output_values.items():
            _validate_numeric(field_value, field)
        if any(s.support_class in {SupportClass.UNKNOWN, SupportClass.NOT_APPLICABLE,
                                   SupportClass.OUTSIDE_SCOPE} for s in inputs):
            support = SupportClass.UNKNOWN
            authority = AuthorityClass.NONE
            value = None
            uncertainty = {"reason": "UPSTREAM_SUPPORT_INCOMPLETE",
                           "unknown_input_domains": [s.domain for s in inputs
                               if s.support_class in {SupportClass.UNKNOWN,
                                                      SupportClass.NOT_APPLICABLE,
                                                      SupportClass.OUTSIDE_SCOPE}]}
        else:
            support = SupportClass.FIXTURE_ONLY
            authority = AuthorityClass.FIXTURE_ONLY
            value = {"variables": dict(output_values), "units": dict(output_units)}
            uncertainty = {"classification": "SYNTHETIC_FIXTURE_NOT_SCIENTIFIC_RESULT"}
        provenance = ProvenanceRecord.create(
            activity="R6_HYDROLOGY_ADAPTER_FIXTURE_NORMALIZATION_V0",
            input_refs=tuple(str(s.state_id) for s in inputs),
            source_refs=(self.LEGACY_CONTRACT, self.LEGACY_REPLAY),
            parent_provenance_ids=tuple(p for s in inputs for p in s.provenance_ids),
            attributes={"mode": self.MODE, "legacy_semantics_reference_only": True,
                        "scientific_execution": False},
        )
        state = DomainStateEnvelope.create(
            history_id=climate.history_id, branch_id=climate.branch_id,
            domain="hydrology", time_support=climate.time_support,
            spatial_support=climate.spatial_support, support_class=support,
            authority_class=authority, value=value, uncertainty=uncertainty,
            provenance_ids=(str(provenance.record_id),),
            parent_state_ids=tuple(str(s.state_id) for s in inputs),
        )
        return state, provenance

    def bind_governed_result(self, *, climate: DomainStateEnvelope,
                             geography: DomainStateEnvelope,
                             shoreline: DomainStateEnvelope,
                             result_values: Mapping[str, Any],
                             result_units: Mapping[str, str],
                             expected_units: Mapping[str, str],
                             result_sha256: str, authority_refs: tuple[str, ...],
                             temporal_semantics: str,
                             native_resolution: str | None = None
                             ) -> tuple[DomainStateEnvelope, ProvenanceRecord]:
        """Bind an already-produced, governed result without executing a model."""
        import re

        inputs = (climate, geography, shoreline)
        if tuple(row.domain for row in inputs) != ("climate", "geography", "shoreline"):
            raise HydrologyAdapterError("expected climate, geography, shoreline in order")
        if (len({row.time_support for row in inputs}) != 1
                or len({row.history_id for row in inputs}) != 1
                or len({row.branch_id for row in inputs}) != 1
                or len({row.spatial_support.grid_id for row in inputs}) != 1
                or len({row.spatial_support.cell_ids for row in inputs}) != 1):
            raise HydrologyAdapterError("governed input time/grid/cell supports must align exactly")
        if not re.fullmatch(r"[0-9a-f]{64}", result_sha256):
            raise HydrologyAdapterError("result payload SHA-256 is required")
        if not authority_refs or not temporal_semantics.strip():
            raise HydrologyAdapterError("result authority refs and temporal semantics are required")
        if (set(result_values) != set(result_units) or not result_values
                or dict(result_units) != dict(expected_units)):
            raise HydrologyAdapterError("imported result variables/units do not match the declared contract")
        if any(row.support_class in {SupportClass.UNKNOWN, SupportClass.NOT_APPLICABLE,
                                     SupportClass.OUTSIDE_SCOPE, SupportClass.FIXTURE_ONLY}
               for row in inputs):
            raise HydrologyAdapterError("upstream support is not eligible for governed result binding")
        if any(row.authority_class in {AuthorityClass.NONE, AuthorityClass.FIXTURE_ONLY}
               for row in inputs):
            raise HydrologyAdapterError("upstream authority is insufficient for governed binding")
        for field, value in result_values.items():
            _validate_numeric(value, field)
            if isinstance(value, (tuple, list)) and len(value) != len(climate.spatial_support.cell_ids):
                raise HydrologyAdapterError(f"{field} does not align to the declared cell support")
        provenance = ProvenanceRecord.create(
            activity="R6_HYDROLOGY_GOVERNED_RESULT_BINDING_V0",
            input_refs=tuple(str(row.state_id) for row in inputs),
            source_refs=(*authority_refs, f"sha256:{result_sha256}", self.LEGACY_CONTRACT),
            parent_provenance_ids=tuple(ref for row in inputs for ref in row.provenance_ids),
            attributes={"scientific_execution": False,
                        "temporal_semantics": temporal_semantics,
                        "binding_role": "PREEXISTING_GOVERNED_RESULT"},
        )
        state = DomainStateEnvelope.create(
            history_id=climate.history_id, branch_id=climate.branch_id,
            domain="hydrology", time_support=climate.time_support,
            spatial_support=SpatialSupport(
                climate.spatial_support.grid_id, climate.spatial_support.cell_ids,
                native_resolution or climate.spatial_support.native_resolution,
                climate.spatial_support.selector_kind),
            support_class=SupportClass.DERIVED_SUPPORTED,
            authority_class=AuthorityClass.DERIVED_AUTHORITY,
            value={"variables": dict(result_values), "units": dict(result_units)},
            uncertainty={"classification": "SOURCE_RESULT_UNCERTAINTY_PRESERVED_BY_REFERENCE",
                         "authority_refs": list(authority_refs)},
            provenance_ids=(str(provenance.record_id),),
            parent_state_ids=tuple(str(row.state_id) for row in inputs),
            payload_ref=f"sha256:{result_sha256}",
        )
        return state, provenance

def _validate_numeric(value: Any, field: str) -> None:
    if isinstance(value, bool) or value is None:
        raise HydrologyAdapterError(f"{field} must contain finite numeric fixture values")
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise HydrologyAdapterError(f"{field} must contain finite numeric fixture values")
        return
    if isinstance(value, (tuple, list)) and value:
        for item in value:
            _validate_numeric(item, field)
        return
    raise HydrologyAdapterError(f"{field} must contain finite numeric fixture values")
