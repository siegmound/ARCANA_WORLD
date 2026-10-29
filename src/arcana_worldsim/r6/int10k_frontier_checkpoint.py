"""Typed E2-B frontier/checkpoint projection with explicit legacy-history binding.

This module does not implement an append-only history store or a transaction
chain. The current regional/unified runners still require historical arrays at
resume; callers must provide the matching history prefix explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping

from .geological_surface_microdomain import SUPPORTS
from .regional_geological_evolution import (
    RegionalModelError, seal_regional_checkpoint, verify_regional_checkpoint,
)
from .unified_multiphysics_microdomain import (
    SurfaceMicrodomainError, seal_unified_checkpoint, verify_unified_checkpoint,
)


FRONTIER_SCHEMA = "ARCANA_R6_INT10K_FRONTIER_V2"
CHECKPOINT_SCHEMA = "ARCANA_R6_INT10K_CHECKPOINT_V2"
HISTORY_PREFIX_SCHEMA = "ARCANA_R6_INT10K_HISTORY_PREFIX_REFERENCE_V1"
CLASSIFICATION = "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY"
_REGIONAL_HISTORY_KEYS = (
    "records", "snapshots", "routing_events", "initial_condition_events",
)
_UNIFIED_HISTORY_KEYS = ("records",)
_HASH_KEYS = (
    "source_archive_sha256", "source_manifest_sha256", "source_result_sha256",
)
_REGIONAL_FRONTIER_FIELDS = {
    "authority", "baseline_drainage_targets", "cells", "config", "cumulative",
    "drainage_targets", "initial_totals", "interfaces", "material_catalog",
    "r6_support_mapping", "routing_mode", "schema", "source_identity",
    "source_identity_sha256", "t0_boundary_reference",
    "unperturbed_reference_drainage_targets", "time_years",
}
_UNIFIED_FRONTIER_FIELDS = {
    "cumulative_sediment", "cumulative_substrate_erosion_kg", "cumulative_water",
    "deep_inventory_j_by_support", "deep_volume_ids", "deep_zeta_by_support",
    "elapsed_external_steps", "geometry_roundoff_tolerance_m3",
    "initial_cover_mass_kg", "initial_deep_inventory_j",
    "initial_geometry_area_m2_by_support", "initial_material_inventory",
    "initial_state_sha256_by_support", "initial_substrate_mass_kg",
    "initial_surface_snapshot", "initial_suspended_sediment_kg",
    "initial_thermal_states", "initial_water_storage_m3", "mechanical_reference_cells",
    "opening_total_m", "planned_external_steps", "previous_displacement_m_by_support",
    "previous_interface_gap_m", "previous_stored_energy_j",
    "run_identity", "run_identity_sha256", "sediment_roundoff_tolerance_kg",
    "source_identity", "surface_state", "synthetic_modal_parameters_by_role",
    "thermal_states_by_support", "total_strain", "viscous_strain",
    "water_roundoff_tolerance_m3",
}


class FrontierCheckpointError(ValueError):
    """Unsupported, incompatible, incomplete, or corrupted frontier data."""


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FrontierCheckpointError("NON_CANONICAL_FRONTIER_VALUE") from exc


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def hash_canonical(value: Any) -> str:
    """Public canonical SHA256 helper for independent envelope tooling."""
    return _sha(value)


def _is_sha256(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


@dataclass(frozen=True)
class FrontierV2:
    """Immutable typed view; canonical bytes prevent nested-mapping mutation."""

    canonical_json: bytes

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.canonical_json.decode("utf-8"))

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json).hexdigest()


@dataclass(frozen=True)
class HistoryPrefixV1:
    """History objects kept outside the frontier/checkpoint payload."""

    canonical_json: bytes

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.canonical_json.decode("utf-8"))

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json).hexdigest()


@dataclass(frozen=True)
class CheckpointV2:
    """Immutable versioned checkpoint envelope represented by canonical JSON."""

    canonical_json: bytes

    @property
    def envelope(self) -> dict[str, Any]:
        return json.loads(self.canonical_json.decode("utf-8"))

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json).hexdigest()


def _validate_legacy_checkpoint(legacy: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        regional = verify_regional_checkpoint(legacy)
        unified_envelope = legacy.get("unified_checkpoint")
        unified = verify_unified_checkpoint(unified_envelope)
    except (RegionalModelError, SurfaceMicrodomainError, TypeError, KeyError) as exc:
        raise FrontierCheckpointError("LEGACY_CHECKPOINT_INVALID") from exc
    if not isinstance(regional, dict) or not isinstance(unified, dict):
        raise FrontierCheckpointError("LEGACY_CHECKPOINT_INVALID")
    return regional, unified


def _input_identities(source: Mapping[str, Any]) -> dict[str, Any]:
    missing = [key for key in _HASH_KEYS if not _is_sha256(source.get(key))]
    support_hashes = source.get("support_state_sha256")
    if (missing or not isinstance(support_hashes, Mapping)
            or set(support_hashes) != set(SUPPORTS)
            or any(not _is_sha256(v) for v in support_hashes.values())):
        raise FrontierCheckpointError("E0_INPUT_IDENTITY_INCOMPLETE")
    return {**{key: source[key] for key in _HASH_KEYS},
            "support_state_sha256": dict(support_hashes)}


def _history_payload(regional: Mapping[str, Any], unified: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": HISTORY_PREFIX_SCHEMA,
        "classification": CLASSIFICATION,
        "source_identity_sha256": _sha(regional["source_identity"]),
        "configuration_sha256": _config_sha(regional, unified),
        "time_year": regional["time_years"],
        "regional_year_records": regional["records"],
        "regional_snapshots": regional["snapshots"],
        "regional_routing_events": regional.get("routing_events", []),
        "regional_initial_events": regional.get("initial_condition_events", []),
        "unified_step_records": unified["records"],
    }


def _config_body(regional: Mapping[str, Any], unified: Mapping[str, Any]) -> dict[str, Any]:
    run_identity = unified.get("run_identity")
    if not isinstance(run_identity, Mapping) or not isinstance(run_identity.get("config"), Mapping):
        raise FrontierCheckpointError("CONFIGURATION_IDENTITY_MISSING")
    return {"regional": regional.get("config"),
            "unified": run_identity["config"],
            "unified_run_identity_sha256": unified.get("run_identity_sha256")}


def _config_sha(regional: Mapping[str, Any], unified: Mapping[str, Any]) -> str:
    config = _config_body(regional, unified)
    if not isinstance(config["regional"], Mapping) or not _is_sha256(
            config["unified_run_identity_sha256"]):
        raise FrontierCheckpointError("CONFIGURATION_IDENTITY_INVALID")
    if unified.get("run_identity_sha256") != _sha(unified.get("run_identity")):
        raise FrontierCheckpointError("CONFIGURATION_IDENTITY_INVALID")
    return _sha(config)


def _validate_prefix_history(payload: Mapping[str, Any], *, source_sha: str,
                              config_sha: str, time_year: int) -> None:
    expected_fields = {
        "schema", "classification", "source_identity_sha256", "configuration_sha256",
        "time_year", "regional_year_records", "regional_snapshots",
        "regional_routing_events", "regional_initial_events", "unified_step_records",
    }
    if set(payload) != expected_fields or type(time_year) is not int or time_year < 0:
        raise FrontierCheckpointError("HISTORY_PREFIX_FIELDS_OR_TIME_INVALID")
    if (payload.get("schema") != HISTORY_PREFIX_SCHEMA
            or payload.get("classification") != CLASSIFICATION
            or payload.get("source_identity_sha256") != source_sha
            or payload.get("configuration_sha256") != config_sha
            or payload.get("time_year") != time_year):
        raise FrontierCheckpointError("HISTORY_PREFIX_IDENTITY_MISMATCH")
    years = list(range(1, time_year + 1))
    snaps = list(range(0, time_year + 1))
    steps = [float(i) for i in years]
    for key, wanted, field, error in (
        ("regional_year_records", years, "time_year", "REGIONAL_HISTORY_COVERAGE_INVALID"),
        ("regional_snapshots", snaps, "time_year", "REGIONAL_HISTORY_COVERAGE_INVALID"),
        ("unified_step_records", steps, "elapsed_years", "UNIFIED_HISTORY_COVERAGE_INVALID"),
    ):
        rows = payload.get(key)
        if not isinstance(rows, list) or [r.get(field) if isinstance(r, Mapping) else None
                                          for r in rows] != wanted:
            raise FrontierCheckpointError(error)
    for key in ("regional_routing_events", "regional_initial_events"):
        if not isinstance(payload.get(key), list):
            raise FrontierCheckpointError("REGIONAL_HISTORY_SHAPE_INVALID")


def capture_frontier_v2(legacy_checkpoint: Mapping[str, Any]) -> tuple[FrontierV2, HistoryPrefixV1]:
    """Project a verified legacy checkpoint into frontier and separate history."""
    regional, unified = _validate_legacy_checkpoint(legacy_checkpoint)
    source = regional.get("source_identity")
    if not isinstance(source, Mapping) or unified.get("source_identity") != source:
        raise FrontierCheckpointError("SOURCE_IDENTITY_MISMATCH")
    source_sha = _sha(source)
    if regional.get("source_identity_sha256") != source_sha:
        raise FrontierCheckpointError("SOURCE_IDENTITY_MISMATCH")
    _input_identities(source)
    config_sha = _config_sha(regional, unified)
    year = regional.get("time_years")
    steps = unified.get("elapsed_external_steps")
    if (type(year) is not int or year < 0 or type(steps) is not int or steps != year):
        raise FrontierCheckpointError("FRONTIER_TIME_ORDINAL_MISMATCH")
    if unified.get("planned_external_steps", 0) < year:
        raise FrontierCheckpointError("FRONTIER_PLAN_INVALID")

    history = _history_payload(regional, unified)
    _validate_prefix_history(history, source_sha=source_sha,
                             config_sha=config_sha, time_year=year)
    region_frontier = {k: v for k, v in regional.items()
                       if k not in _REGIONAL_HISTORY_KEYS}
    unified_frontier = {k: v for k, v in unified.items()
                        if k not in _UNIFIED_HISTORY_KEYS}
    if any(k in region_frontier for k in _REGIONAL_HISTORY_KEYS) or "records" in unified_frontier:
        raise FrontierCheckpointError("HISTORY_EMBEDDED_IN_FRONTIER")
    frontier_payload = {
        "schema": FRONTIER_SCHEMA,
        "classification": CLASSIFICATION,
        "source_identity": dict(source),
        "source_identity_sha256": source_sha,
        "configuration": _config_body(regional, unified),
        "configuration_sha256": config_sha,
        "e0_input_identities": _input_identities(source),
        "time_year": year,
        "next_regional_record_ordinal": year + 1,
        "next_regional_snapshot_ordinal": year + 1,
        "next_unified_step_ordinal": year + 1,
        "regional_dynamic_state": region_frontier,
        "unified_dynamic_state": unified_frontier,
        "history_high_water_mark": {
            "last_regional_record_ordinal": year,
            "last_regional_snapshot_ordinal": year,
            "last_unified_step_ordinal": year,
            "time_year": year,
            "regional_record_count": year,
            "regional_snapshot_count": year + 1,
            "unified_step_count": year,
            "history_reference_sha256": _sha(history),
        },
        "commit_chain_head": {
            "status": "NOT_IMPLEMENTED_NO_APPEND_ONLY_CHAIN",
            "sha256": None,
        },
        "omitted_history_fields": {
            "regional": list(_REGIONAL_HISTORY_KEYS),
            "unified": list(_UNIFIED_HISTORY_KEYS),
        },
    }
    frontier = FrontierV2(_canonical(frontier_payload))
    checkpoint_payload = {
        "schema": CHECKPOINT_SCHEMA,
        "schema_version": 2,
        "classification": CLASSIFICATION,
        "frontier": frontier.payload,
        "frontier_sha256": frontier.sha256,
        "source_identity_sha256": source_sha,
        "configuration_sha256": config_sha,
        "e0_input_identities": _input_identities(source),
        "history_high_water_mark": frontier_payload["history_high_water_mark"],
        "commit_chain_head": frontier_payload["commit_chain_head"],
    }
    checkpoint_payload["checkpoint_sha256"] = _sha(checkpoint_payload)
    return frontier, HistoryPrefixV1(_canonical(history))


def seal_checkpoint_v2(frontier: FrontierV2 | Mapping[str, Any]) -> CheckpointV2:
    payload = frontier.payload if isinstance(frontier, FrontierV2) else dict(frontier)
    _validate_frontier_payload(payload)
    envelope = {
        "schema": CHECKPOINT_SCHEMA, "schema_version": 2,
        "classification": CLASSIFICATION, "frontier": payload,
        "frontier_sha256": _sha(payload),
        "source_identity_sha256": payload["source_identity_sha256"],
        "configuration_sha256": payload["configuration_sha256"],
        "e0_input_identities": payload["e0_input_identities"],
        "history_high_water_mark": payload["history_high_water_mark"],
        "commit_chain_head": payload["commit_chain_head"],
    }
    envelope["checkpoint_sha256"] = _sha(envelope)
    return CheckpointV2(_canonical(envelope))


def _validate_frontier_payload(frontier: Mapping[str, Any]) -> None:
    if (frontier.get("schema") != FRONTIER_SCHEMA
            or frontier.get("classification") != CLASSIFICATION):
        raise FrontierCheckpointError("FRONTIER_SCHEMA_UNSUPPORTED")
    required = {
        "source_identity", "source_identity_sha256", "configuration",
        "configuration_sha256", "e0_input_identities", "time_year",
        "next_regional_record_ordinal", "next_regional_snapshot_ordinal",
        "next_unified_step_ordinal", "regional_dynamic_state",
        "unified_dynamic_state", "history_high_water_mark", "commit_chain_head",
        "omitted_history_fields",
    }
    if set(frontier) != required | {"schema", "classification"}:
        raise FrontierCheckpointError("FRONTIER_FIELDS_INCOMPLETE_OR_UNKNOWN")
    source = frontier["source_identity"]
    if not isinstance(source, Mapping) or _sha(source) != frontier["source_identity_sha256"]:
        raise FrontierCheckpointError("SOURCE_IDENTITY_MISMATCH")
    if frontier["e0_input_identities"] != _input_identities(source):
        raise FrontierCheckpointError("E0_INPUT_IDENTITY_MISMATCH")
    if not _is_sha256(frontier["configuration_sha256"]):
        raise FrontierCheckpointError("CONFIGURATION_IDENTITY_INVALID")
    year = frontier["time_year"]
    hwm = frontier["history_high_water_mark"]
    if (type(year) is not int or year < 0 or not isinstance(hwm, Mapping)
            or hwm.get("time_year") != year
            or hwm.get("last_regional_record_ordinal") != year
            or hwm.get("last_regional_snapshot_ordinal") != year
            or hwm.get("last_unified_step_ordinal") != year
            or hwm.get("regional_record_count") != year
            or hwm.get("regional_snapshot_count") != year + 1
            or hwm.get("unified_step_count") != year
            or frontier["next_regional_record_ordinal"] != year + 1
            or frontier["next_regional_snapshot_ordinal"] != year + 1
            or frontier["next_unified_step_ordinal"] != year + 1
            or not _is_sha256(hwm.get("history_reference_sha256"))):
        raise FrontierCheckpointError("FRONTIER_TIME_ORDINAL_MISMATCH")
    if frontier["commit_chain_head"] != {
            "status": "NOT_IMPLEMENTED_NO_APPEND_ONLY_CHAIN", "sha256": None}:
        raise FrontierCheckpointError("COMMIT_CHAIN_REFERENCE_INVALID")
    region = frontier["regional_dynamic_state"]
    unified = frontier["unified_dynamic_state"]
    if not isinstance(region, Mapping) or not isinstance(unified, Mapping):
        raise FrontierCheckpointError("FRONTIER_STATE_SHAPE_INVALID")
    if set(region) != _REGIONAL_FRONTIER_FIELDS:
        raise FrontierCheckpointError("REGIONAL_FRONTIER_FIELDS_INCOMPLETE_OR_UNKNOWN")
    if set(unified) != _UNIFIED_FRONTIER_FIELDS:
        raise FrontierCheckpointError("UNIFIED_FRONTIER_FIELDS_INCOMPLETE_OR_UNKNOWN")
    if (region.get("time_years") != year
            or region.get("source_identity") != source
            or region.get("source_identity_sha256") != frontier["source_identity_sha256"]
            or unified.get("source_identity") != source
            or unified.get("elapsed_external_steps") != year
            or not isinstance(unified.get("run_identity"), Mapping)
            or unified.get("run_identity_sha256") != _sha(unified.get("run_identity"))
            or unified.get("planned_external_steps", 0) < year):
        raise FrontierCheckpointError("FRONTIER_DYNAMIC_IDENTITY_OR_TIME_INVALID")
    if _sha(frontier["configuration"]) != frontier["configuration_sha256"]:
        raise FrontierCheckpointError("CONFIGURATION_IDENTITY_INVALID")
    if any(k in region for k in _REGIONAL_HISTORY_KEYS) or any(
            k in unified for k in _UNIFIED_HISTORY_KEYS):
        raise FrontierCheckpointError("HISTORY_EMBEDDED_IN_FRONTIER")
    for payload in (region, unified):
        _require_finite(payload)


def _require_finite(value: Any) -> None:
    if isinstance(value, Mapping):
        for child in value.values():
            _require_finite(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _require_finite(child)
    elif isinstance(value, float) and not math.isfinite(value):
        raise FrontierCheckpointError("FRONTIER_NONFINITE_STATE")


def serialize_checkpoint_v2(checkpoint: CheckpointV2 | Mapping[str, Any]) -> bytes:
    envelope = (json.loads(checkpoint.canonical_json.decode("utf-8"))
                if isinstance(checkpoint, CheckpointV2) else dict(checkpoint))
    verify_checkpoint_v2(envelope)
    return _canonical(envelope)


def verify_checkpoint_v2(checkpoint: Mapping[str, Any], *,
                         expected_source_identity: Mapping[str, Any] | None = None,
                         expected_configuration: Mapping[str, Any] | None = None) -> dict[str, Any]:
    required = {
        "schema", "schema_version", "classification", "frontier", "frontier_sha256",
        "source_identity_sha256", "configuration_sha256", "e0_input_identities",
        "history_high_water_mark", "commit_chain_head", "checkpoint_sha256",
    }
    if set(checkpoint) != required or checkpoint.get("schema") != CHECKPOINT_SCHEMA \
            or checkpoint.get("schema_version") != 2:
        raise FrontierCheckpointError("CHECKPOINT_SCHEMA_UNSUPPORTED_OR_FIELDS_INVALID")
    body = {k: v for k, v in checkpoint.items() if k != "checkpoint_sha256"}
    if not _is_sha256(checkpoint.get("checkpoint_sha256")) or _sha(body) != checkpoint["checkpoint_sha256"]:
        raise FrontierCheckpointError("CHECKPOINT_DIGEST_MISMATCH")
    frontier = checkpoint.get("frontier")
    if not isinstance(frontier, Mapping):
        raise FrontierCheckpointError("CHECKPOINT_FRONTIER_MISSING")
    _validate_frontier_payload(frontier)
    if (_sha(frontier) != checkpoint.get("frontier_sha256")
            or frontier.get("source_identity_sha256") != checkpoint.get("source_identity_sha256")
            or frontier.get("configuration_sha256") != checkpoint.get("configuration_sha256")
            or frontier.get("e0_input_identities") != checkpoint.get("e0_input_identities")
            or frontier.get("history_high_water_mark") != checkpoint.get("history_high_water_mark")
            or frontier.get("commit_chain_head") != checkpoint.get("commit_chain_head")):
        raise FrontierCheckpointError("CHECKPOINT_BINDING_MISMATCH")
    if expected_source_identity is not None and dict(expected_source_identity) != frontier["source_identity"]:
        raise FrontierCheckpointError("INCOMPATIBLE_SOURCE_IDENTITY")
    if expected_configuration is not None and _sha(expected_configuration) != frontier["configuration_sha256"]:
        raise FrontierCheckpointError("INCOMPATIBLE_CONFIGURATION")
    return json.loads(_canonical(dict(checkpoint)).decode("utf-8"))


def parse_checkpoint_v2(payload: bytes | str, *,
                         expected_source_identity: Mapping[str, Any] | None = None,
                         expected_configuration: Mapping[str, Any] | None = None) -> CheckpointV2:
    try:
        value = json.loads(payload.decode("utf-8") if isinstance(payload, bytes) else payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FrontierCheckpointError("CHECKPOINT_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise FrontierCheckpointError("CHECKPOINT_JSON_INVALID")
    verify_checkpoint_v2(value, expected_source_identity=expected_source_identity,
                         expected_configuration=expected_configuration)
    return CheckpointV2(_canonical(value))


def serialize_history_prefix(history: HistoryPrefixV1 | Mapping[str, Any]) -> bytes:
    payload = history.payload if isinstance(history, HistoryPrefixV1) else dict(history)
    source_sha, config_sha, year = (payload.get("source_identity_sha256"),
                                   payload.get("configuration_sha256"),
                                   payload.get("time_year"))
    _validate_prefix_history(payload, source_sha=source_sha, config_sha=config_sha,
                             time_year=year)
    return _canonical(payload)


def restore_legacy_checkpoint_v1(checkpoint: CheckpointV2 | Mapping[str, Any] | bytes | str,
                                 history_prefix: HistoryPrefixV1 | Mapping[str, Any] | bytes | str,
                                 *, expected_source_identity: Mapping[str, Any],
                                 expected_configuration: Mapping[str, Any]) -> dict[str, Any]:
    """Materialize a legacy checkpoint only from separately supplied history.

    The current runner consumes historical arrays on resume. This explicit
    bridge fails closed when the caller cannot supply the complete prefix.
    """
    if isinstance(checkpoint, CheckpointV2):
        cp_obj = parse_checkpoint_v2(checkpoint.canonical_json,
                                     expected_source_identity=expected_source_identity,
                                     expected_configuration=expected_configuration)
    elif isinstance(checkpoint, Mapping):
        cp_obj = parse_checkpoint_v2(_canonical(dict(checkpoint)),
                                     expected_source_identity=expected_source_identity,
                                     expected_configuration=expected_configuration)
    else:
        cp_obj = parse_checkpoint_v2(checkpoint,
                                     expected_source_identity=expected_source_identity,
                                     expected_configuration=expected_configuration)
    if isinstance(history_prefix, HistoryPrefixV1):
        history = history_prefix.payload
    elif isinstance(history_prefix, Mapping):
        history = dict(history_prefix)
    else:
        try:
            history = json.loads(history_prefix.decode("utf-8") if isinstance(history_prefix, bytes)
                                 else history_prefix)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FrontierCheckpointError("HISTORY_PREFIX_JSON_INVALID") from exc
    frontier = cp_obj.envelope["frontier"]
    year = frontier["time_year"]
    source_sha = frontier["source_identity_sha256"]
    config_sha = frontier["configuration_sha256"]
    _validate_prefix_history(history, source_sha=source_sha,
                             config_sha=config_sha, time_year=year)
    if _sha(history) != frontier["history_high_water_mark"]["history_reference_sha256"]:
        raise FrontierCheckpointError("HISTORY_PREFIX_DIGEST_MISMATCH")
    region = dict(frontier["regional_dynamic_state"])
    region.update({
        "records": history["regional_year_records"],
        "snapshots": history["regional_snapshots"],
        "routing_events": history["regional_routing_events"],
        "initial_condition_events": history["regional_initial_events"],
    })
    unified = dict(frontier["unified_dynamic_state"])
    unified["records"] = history["unified_step_records"]
    unified_envelope = seal_unified_checkpoint(unified)
    legacy = seal_regional_checkpoint(region, unified_checkpoint=unified_envelope)
    try:
        restored_region = verify_regional_checkpoint(legacy)
        restored_unified = verify_unified_checkpoint(legacy["unified_checkpoint"])
    except (RegionalModelError, SurfaceMicrodomainError, TypeError, KeyError) as exc:
        raise FrontierCheckpointError("RESTORED_LEGACY_CHECKPOINT_INVALID") from exc
    if (restored_region.get("time_years") != year
            or restored_unified.get("elapsed_external_steps") != year
            or restored_unified.get("records") != history["unified_step_records"]):
        raise FrontierCheckpointError("RESTORED_FRONTIER_COVERAGE_INVALID")
    return legacy
