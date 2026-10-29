"""History-independent continuation primitives for the INT10K E2-B2 pilot.

The collector is deliberately external to engine checkpoints. It is a lossless
in-memory test consumer, not a transactional or append-only archive.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Mapping


CHECKPOINT_SCHEMA = "ARCANA_R6_INT10K_HISTORY_INDEPENDENT_CHECKPOINT_V1"
CHAIN_HEAD_NOT_IMPLEMENTED = "NOT_IMPLEMENTED_NO_APPEND_ONLY_CHAIN"


class HistoryContinuationError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise HistoryContinuationError("HISTORY_VALUE_NOT_CANONICAL_JSON") from exc


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def seal_history_independent_checkpoint(
    regional_checkpoint: Mapping[str, Any], *, time_year: int,
    source_identity: Mapping[str, Any], configuration: Mapping[str, Any],
) -> dict[str, Any]:
    if type(time_year) is not int or time_year < 0:
        raise HistoryContinuationError("FRONTIER_TIME_INVALID")
    region = regional_checkpoint.get("regional_state")
    unified_cp = regional_checkpoint.get("unified_checkpoint")
    if not isinstance(region, Mapping) or not isinstance(unified_cp, Mapping):
        raise HistoryContinuationError("FRONTIER_ENGINE_CHECKPOINT_INVALID")
    forbidden = {"records", "snapshots", "routing_events", "initial_condition_events"}
    if forbidden.intersection(region):
        raise HistoryContinuationError("FRONTIER_CONTAINS_REGIONAL_HISTORY")
    unified = unified_cp.get("state")
    if not isinstance(unified, Mapping) or "records" in unified:
        raise HistoryContinuationError("FRONTIER_CONTAINS_UNIFIED_HISTORY")
    if region.get("time_years") != time_year:
        raise HistoryContinuationError("FRONTIER_REGIONAL_TIME_MISMATCH")
    if unified.get("elapsed_external_steps") != time_year:
        raise HistoryContinuationError("FRONTIER_UNIFIED_TIME_MISMATCH")
    payload = {
        "schema": CHECKPOINT_SCHEMA,
        "time_year": time_year,
        "next_regional_record_ordinal": time_year + 1,
        "next_snapshot_ordinal": time_year + 1,
        "next_unified_step_ordinal": time_year + 1,
        "history_high_water_mark": time_year,
        "history_commit_chain_head": CHAIN_HEAD_NOT_IMPLEMENTED,
        "source_identity": json.loads(_canonical(dict(source_identity))),
        "source_identity_sha256": _sha(dict(source_identity)),
        "configuration": json.loads(_canonical(dict(configuration))),
        "configuration_sha256": _sha(dict(configuration)),
        "regional_checkpoint": dict(regional_checkpoint),
        "history_prefix_required": False,
        "classification": "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY",
    }
    return {**payload, "checkpoint_sha256": _sha(payload)}


def verify_history_independent_checkpoint(
    checkpoint: Mapping[str, Any], *, source_identity: Mapping[str, Any],
    configuration: Mapping[str, Any],
) -> dict[str, Any]:
    required = {
        "schema", "time_year", "next_regional_record_ordinal", "next_snapshot_ordinal",
        "next_unified_step_ordinal", "history_high_water_mark", "history_commit_chain_head",
        "source_identity", "source_identity_sha256", "configuration", "configuration_sha256",
        "regional_checkpoint", "history_prefix_required", "classification", "checkpoint_sha256",
    }
    if not isinstance(checkpoint, Mapping) or set(checkpoint) != required:
        raise HistoryContinuationError("FRONTIER_FIELDS_INVALID")
    body = {key: checkpoint[key] for key in required if key != "checkpoint_sha256"}
    if checkpoint.get("schema") != CHECKPOINT_SCHEMA or _sha(body) != checkpoint.get("checkpoint_sha256"):
        raise HistoryContinuationError("FRONTIER_DIGEST_OR_SCHEMA_INVALID")
    year = checkpoint.get("time_year")
    if (type(year) is not int or year < 0
            or checkpoint.get("history_high_water_mark") != year
            or checkpoint.get("next_regional_record_ordinal") != year + 1
            or checkpoint.get("next_snapshot_ordinal") != year + 1
            or checkpoint.get("next_unified_step_ordinal") != year + 1
            or checkpoint.get("history_commit_chain_head") != CHAIN_HEAD_NOT_IMPLEMENTED
            or checkpoint.get("history_prefix_required") is not False
            or checkpoint.get("classification") != "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY"):
        raise HistoryContinuationError("FRONTIER_ORDINAL_OR_AUTHORITY_INVALID")
    if (checkpoint.get("source_identity_sha256") != _sha(dict(source_identity))
            or checkpoint.get("configuration_sha256") != _sha(dict(configuration))
            or _sha(checkpoint.get("source_identity")) != _sha(dict(source_identity))
            or _sha(checkpoint.get("configuration")) != _sha(dict(configuration))):
        raise HistoryContinuationError("FRONTIER_SOURCE_OR_CONFIG_MISMATCH")
    regional = checkpoint.get("regional_checkpoint")
    if not isinstance(regional, Mapping) or not isinstance(regional.get("regional_state"), Mapping):
        raise HistoryContinuationError("FRONTIER_ENGINE_CHECKPOINT_INVALID")
    pre_unified = regional.get("unified_checkpoint")
    pre_state = pre_unified.get("state") if isinstance(pre_unified, Mapping) else None
    if not isinstance(pre_state, Mapping):
        raise HistoryContinuationError("FRONTIER_UNIFIED_CHECKPOINT_INVALID")
    if "history_accumulators" not in pre_state:
        raise HistoryContinuationError("FRONTIER_ACCUMULATORS_MISSING")
    _validate_accumulators(pre_state["history_accumulators"])
    try:
        from .regional_geological_evolution import verify_regional_checkpoint
        verify_regional_checkpoint(regional)
    except (ValueError, TypeError, KeyError) as exc:
        raise HistoryContinuationError("FRONTIER_ENGINE_CHECKPOINT_INVALID") from exc
    region = regional["regional_state"]
    unified_cp = regional.get("unified_checkpoint")
    unified = unified_cp.get("state") if isinstance(unified_cp, Mapping) else None
    if not isinstance(unified, Mapping):
        raise HistoryContinuationError("FRONTIER_UNIFIED_CHECKPOINT_INVALID")
    if (region.get("time_years") != year or unified.get("elapsed_external_steps") != year
            or "records" in unified
            or {"records", "snapshots", "routing_events", "initial_condition_events"}.intersection(region)):
        raise HistoryContinuationError("FRONTIER_HISTORY_OR_TIME_INVALID")
    accum = unified.get("history_accumulators")
    if not isinstance(accum, Mapping):
        raise HistoryContinuationError("FRONTIER_ACCUMULATORS_MISSING")
    _validate_accumulators(accum)
    return dict(regional)


def _validate_accumulators(value: Mapping[str, Any]) -> None:
    required = {"material_flows", "mechanical", "deep"}
    if set(value) != required:
        raise HistoryContinuationError("FRONTIER_ACCUMULATORS_INVALID")
    expected = {
        "material_flows": {"bedrock_detachment_kg_by_material_id", "outlet_export_kg_by_material_id",
                           "deposition_kg_by_material_id", "internal_transfer_kg_by_material_id",
                           "mobile_cover_erosion_kg_by_material_id"},
        "mechanical": {"external_work_j", "viscous_dissipation_j", "algorithmic_energy_increment_j"},
        "deep": {"gross_internal_transport_j", "net_transport_0_to_1_j", "minimum_reservoir_stock_j"},
    }
    for group, keys in expected.items():
        row = value[group]
        if not isinstance(row, Mapping) or set(row) != keys:
            raise HistoryContinuationError("FRONTIER_ACCUMULATORS_INVALID")
        for item in row.values():
            items = item.values() if isinstance(item, Mapping) else (item,)
            for number in items:
                if not isinstance(number, (int, float)) or isinstance(number, bool) or not math.isfinite(float(number)):
                    raise HistoryContinuationError("FRONTIER_ACCUMULATORS_NONFINITE")


@dataclass
class HistoryCollector:
    """Lossless test consumer; its history is never inserted into a frontier."""

    regional_start_year: int = 0
    unified_start_step: int = 0
    include_initial_snapshot: bool = True
    regional_records: list[dict[str, Any]] = field(default_factory=list)
    regional_snapshots: list[dict[str, Any]] = field(default_factory=list)
    regional_events: list[dict[str, Any]] = field(default_factory=list)
    unified_steps: list[dict[str, Any]] = field(default_factory=list)

    def emit(self, kind: str, record: Mapping[str, Any]) -> None:
        row = json.loads(_canonical(dict(record)))
        if kind == "REGIONAL_YEAR_RECORD":
            expected = self.regional_start_year + len(self.regional_records) + 1
            if row.get("time_year") != expected:
                raise HistoryContinuationError("REGIONAL_RECORD_ORDINAL_INVALID")
            self.regional_records.append(row)
        elif kind == "REGIONAL_SNAPSHOT":
            expected = (self.regional_start_year + len(self.regional_snapshots)
                        if self.include_initial_snapshot
                        else self.regional_start_year + len(self.regional_snapshots) + 1)
            if row.get("time_year") != expected:
                raise HistoryContinuationError("REGIONAL_SNAPSHOT_ORDINAL_INVALID")
            self.regional_snapshots.append(row)
        elif kind == "REGIONAL_EVENT":
            self.regional_events.append(row)
        elif kind == "UNIFIED_STEP":
            expected = self.unified_start_step + len(self.unified_steps) + 1
            if row.get("step") != expected or row.get("elapsed_years") != float(expected):
                raise HistoryContinuationError("UNIFIED_STEP_ORDINAL_INVALID")
            self.unified_steps.append(row)
        else:
            raise HistoryContinuationError("HISTORY_RECORD_KIND_UNKNOWN")

    def export(self) -> dict[str, Any]:
        return {
            "regional_records": json.loads(_canonical(self.regional_records)),
            "regional_snapshots": json.loads(_canonical(self.regional_snapshots)),
            "regional_events": json.loads(_canonical(self.regional_events)),
            "unified_steps": json.loads(_canonical(self.unified_steps)),
        }


@dataclass(frozen=True)
class HistoryReader:
    """Exact historical lookup over a separately supplied archived history."""

    history: Mapping[str, Any]

    def regional_record(self, time_year: int) -> dict[str, Any]:
        return self._exact("regional_records", "time_year", time_year)

    def regional_snapshot(self, time_year: int) -> dict[str, Any]:
        return self._exact("regional_snapshots", "time_year", time_year)

    def unified_step(self, step: int) -> dict[str, Any]:
        return self._exact("unified_steps", "step", step)

    def regional_materials(self, time_year: int, cell_id: str | None = None) -> list[dict[str, Any]]:
        snapshot = self.regional_snapshot(time_year)
        cells = snapshot.get("cells", [])
        if cell_id is not None:
            cells = [cell for cell in cells if cell.get("cell_id") == cell_id]
            if not cells:
                raise HistoryContinuationError("CELL_NOT_ARCHIVED")
        return [{"time_year": time_year, "cell_id": cell["cell_id"],
                 "substrate": cell["substrate"],
                 "mobile_kg_by_material": cell["mobile_kg_by_material"],
                 "suspended_kg_by_material": cell["suspended_kg_by_material"],
                 "deposits": cell["deposits"]} for cell in cells]

    def deep_inventory(self, time_year: int, volume_id: str) -> dict[str, Any]:
        if type(time_year) is not int or time_year < 1:
            raise HistoryContinuationError("HISTORICAL_QUERY_TIME_INVALID")
        step = self.unified_step(time_year)
        inventory = step.get("deep", {}).get("inventory_j_by_material_volume", {})
        if volume_id not in inventory:
            raise HistoryContinuationError("MATERIAL_VOLUME_NOT_ARCHIVED")
        return {"time_year": time_year, "volume_id": volume_id,
                "inventory_j": inventory[volume_id], "interpolated": False}

    def material_provenance(self, material_id: str) -> list[dict[str, Any]]:
        if not isinstance(material_id, str) or not material_id:
            raise HistoryContinuationError("MATERIAL_ID_INVALID")
        matches = []
        for row in self.history.get("regional_records", ()):
            for event in row.get("events", ()):
                if event.get("material_id") == material_id:
                    matches.append(json.loads(_canonical(event)))
        return matches

    def _exact(self, key: str, field_name: str, target: int) -> dict[str, Any]:
        if type(target) is not int or target < 0:
            raise HistoryContinuationError("HISTORICAL_QUERY_TIME_INVALID")
        matches = [row for row in self.history.get(key, ()) if row.get(field_name) == target]
        if len(matches) > 1:
            raise HistoryContinuationError("HISTORICAL_QUERY_DUPLICATE")
        if not matches:
            raise HistoryContinuationError("TIME_NOT_ARCHIVED")
        return json.loads(_canonical(matches[0]))
