"""Complete, versioned in-memory reference for bounded INT10K E1 regressions.

This is an oracle/capture layer, not a streaming archive or a replacement
physics runner. It preserves the complete raw result of the existing regional
and unified operators, including the genuine split-boundary checkpoint.
"""
from __future__ import annotations

from copy import deepcopy
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import time
import tracemalloc
from typing import Any, Mapping
from uuid import uuid4

from .geological_surface_microdomain import SUPPORTS
from .int10k_short_reference import (
    ShortReferenceConfig, ShortReferenceError, compare_reference,
)
from .regional_geological_evolution import (
    RegionalConfig, run_regional_segment, verify_regional_checkpoint,
)
from .unified_multiphysics_microdomain import verify_unified_checkpoint


SCHEMA = "FULL_HISTORY_ORACLE_V1"
CLASSIFICATION = "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY"


class FullHistoryOracleError(ValueError):
    """Invalid, incomplete, divergent, or corrupted full-history oracle."""


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FullHistoryOracleError("ORACLE_NOT_CANONICAL_JSON") from exc


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def _assert_sequence(rows: Any, expected: list[Any], *, key: str,
                     error: str) -> None:
    if not isinstance(rows, (list, tuple)):
        raise FullHistoryOracleError(error)
    values = []
    for row in rows:
        if not isinstance(row, Mapping) or key not in row:
            raise FullHistoryOracleError(error)
        values.append(row[key])
    if values != expected:
        raise FullHistoryOracleError(error)


def _verify_result(result: Mapping[str, Any], *, years: int,
                   expected_unified_steps: int | None = None) -> None:
    state = result.get("state")
    unified = result.get("subsurface_unified_result")
    if not isinstance(state, Mapping) or not isinstance(unified, Mapping):
        raise FullHistoryOracleError("ORACLE_RESULT_SHAPE_INVALID")
    if type(state.get("time_years")) is not int or state["time_years"] != years:
        raise FullHistoryOracleError("REGIONAL_TERMINAL_TIME_INVALID")
    _assert_sequence(state.get("records"), list(range(1, years + 1)),
                     key="time_year", error="REGIONAL_RECORD_COVERAGE_INVALID")
    _assert_sequence(state.get("snapshots"), list(range(years + 1)),
                     key="time_year", error="REGIONAL_SNAPSHOT_COVERAGE_INVALID")

    steps = unified.get("steps")
    if not isinstance(steps, (list, tuple)):
        raise FullHistoryOracleError("UNIFIED_STEP_COVERAGE_INVALID")
    expected_steps = years if expected_unified_steps is None else expected_unified_steps
    if len(steps) != expected_steps:
        raise FullHistoryOracleError("UNIFIED_STEP_COVERAGE_INVALID")
    step_times = [row.get("elapsed_years") if isinstance(row, Mapping) else None
                  for row in steps]
    if step_times != [float(i) for i in range(1, expected_steps + 1)]:
        raise FullHistoryOracleError("UNIFIED_STEP_ORDER_OR_TIME_INVALID")

    regional_checkpoint = result.get("checkpoint")
    if not isinstance(regional_checkpoint, Mapping):
        raise FullHistoryOracleError("REGIONAL_CHECKPOINT_MISSING")
    try:
        checkpoint_state = verify_regional_checkpoint(regional_checkpoint)
        unified_checkpoint_state = verify_unified_checkpoint(
            regional_checkpoint.get("unified_checkpoint", {}))
    except (ValueError, TypeError, KeyError) as exc:
        raise FullHistoryOracleError("CHECKPOINT_INTEGRITY_INVALID") from exc
    if checkpoint_state.get("time_years") != years:
        raise FullHistoryOracleError("REGIONAL_CHECKPOINT_TIME_INVALID")
    try:
        compare_reference(dict(state), checkpoint_state, abs_tol=0.0, rel_tol=0.0)
    except ShortReferenceError as exc:
        raise FullHistoryOracleError("REGIONAL_CHECKPOINT_STATE_MISMATCH") from exc
    returned_unified_checkpoint = unified.get("continuation")
    if returned_unified_checkpoint != regional_checkpoint.get("unified_checkpoint"):
        raise FullHistoryOracleError("UNIFIED_CHECKPOINT_REFERENCE_MISMATCH")
    try:
        compare_reference(list(steps), unified_checkpoint_state.get("records"),
                          abs_tol=0.0, rel_tol=0.0)
    except ShortReferenceError as exc:
        raise FullHistoryOracleError("UNIFIED_CHECKPOINT_RECORD_MISMATCH") from exc
    if (unified_checkpoint_state.get("elapsed_external_steps") != expected_steps or
            len(unified_checkpoint_state.get("records", [])) != expected_steps):
        raise FullHistoryOracleError("UNIFIED_CHECKPOINT_COVERAGE_INVALID")
    _assert_sequence(unified_checkpoint_state.get("records"),
                     [float(i) for i in range(1, expected_steps + 1)],
                     key="elapsed_years", error="UNIFIED_CHECKPOINT_COVERAGE_INVALID")


def _comparison_view(result: Mapping[str, Any]) -> dict[str, Any]:
    """Remove only the declared per-invocation segment-length diagnostic."""
    view = deepcopy(dict(result))
    unified = view["subsurface_unified_result"]
    configuration = unified.get("configuration")
    if isinstance(configuration, dict):
        configuration.pop("segment_external_step_count", None)
    return view


def _verify_split_checkpoint(result: Mapping[str, Any], *, split_at: int) -> None:
    _verify_result(result, years=split_at, expected_unified_steps=split_at)
    regional_state = result["checkpoint"]["regional_state"]
    if regional_state["time_years"] != split_at:
        raise FullHistoryOracleError("SPLIT_REGIONAL_FRONTIER_NOT_AT_BOUNDARY")
    unified_state = result["checkpoint"]["unified_checkpoint"]["state"]
    if unified_state["elapsed_external_steps"] != split_at:
        raise FullHistoryOracleError("SPLIT_UNIFIED_FRONTIER_NOT_AT_BOUNDARY")


def _measure_rss_bytes() -> tuple[int | None, str]:
    """Best-effort instantaneous RSS; absence is reported, never guessed."""
    try:
        if os.name == "nt":
            from ctypes import wintypes

            class _Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t),
                            ("PeakPagefileUsage", ctypes.c_size_t)]

            counters = _Counters()
            counters.cb = ctypes.sizeof(counters)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            getter = ctypes.windll.psapi.GetProcessMemoryInfo
            getter.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Counters), wintypes.DWORD]
            getter.restype = wintypes.BOOL
            ok = getter(handle, ctypes.byref(counters), counters.cb)
            if ok:
                return int(counters.WorkingSetSize), "WINDOWS_PROCESS_WORKING_SET"
            return None, "WINDOWS_RSS_UNAVAILABLE"
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value * (1 if sys_platform_is_macos() else 1024)), "PROCESS_PEAK_RSS"
    except (ImportError, OSError, AttributeError, ValueError, ctypes.ArgumentError) as exc:
        return None, f"RSS_UNAVAILABLE:{type(exc).__name__}"


def sys_platform_is_macos() -> bool:
    import sys
    return sys.platform == "darwin"


def capture_full_history_oracle(
    states_by_support: Mapping[str, Any], source_identity: Mapping[str, Any], *,
    config: ShortReferenceConfig, regional_config: RegionalConfig | None = None,
    implementation_commit: str | None = None,
    implementation_source_sha256: Mapping[str, str] | None = None,
    implementation_worktree_dirty: bool | None = None,
) -> dict[str, Any]:
    """Run direct/prefix/resume with existing operators and preserve all outputs."""
    config.validate()
    if set(states_by_support) != set(SUPPORTS) or not source_identity:
        raise FullHistoryOracleError("ORACLE_INPUT_IDENTITY_INVALID")
    region_cfg = regional_config or RegionalConfig(duration_years=config.years)
    if region_cfg.duration_years != config.years:
        raise FullHistoryOracleError("ORACLE_PLANNED_DURATION_MISMATCH")
    region_cfg.validate()

    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start()
    rss_before, rss_method = _measure_rss_bytes()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()

    phase_start = time.perf_counter()
    direct_cpu_start = time.process_time()
    direct = run_regional_segment(states_by_support, source_identity,
                                  config=region_cfg, segment_years=config.years)
    direct_wall = time.perf_counter() - phase_start
    direct_cpu = time.process_time() - direct_cpu_start

    phase_start = time.perf_counter()
    split_cpu_start = time.process_time()
    prefix = run_regional_segment(states_by_support, source_identity,
                                  config=region_cfg, segment_years=config.split_at)
    _verify_split_checkpoint(prefix, split_at=config.split_at)
    resumed = run_regional_segment(
        states_by_support, source_identity, config=region_cfg,
        segment_years=config.years - config.split_at,
        checkpoint=prefix["checkpoint"])
    split_wall = time.perf_counter() - phase_start
    split_cpu = time.process_time() - split_cpu_start
    wall_total = time.perf_counter() - wall_start
    cpu_total = time.process_time() - cpu_start
    _, python_heap_peak = tracemalloc.get_traced_memory()
    rss_after, _ = _measure_rss_bytes()
    if not was_tracing:
        tracemalloc.stop()

    _verify_result(direct, years=config.years)
    _verify_result(resumed, years=config.years)
    _verify_split_checkpoint(prefix, split_at=config.split_at)
    try:
        compare_reference(_comparison_view(direct), _comparison_view(resumed),
                          abs_tol=config.abs_tol, rel_tol=config.rel_tol)
    except ShortReferenceError as exc:
        raise FullHistoryOracleError(f"DIRECT_RESTART_DIVERGENCE:{exc}") from exc

    source = deepcopy(dict(source_identity))
    implementation = {"commit": implementation_commit,
                      "source_sha256": dict(implementation_source_sha256 or {}),
                      "tracked_source_changes_present": implementation_worktree_dirty}
    identity_inputs = {
        "source_identity": source,
        "configuration": {
            "years": config.years, "split_at": config.split_at,
            "abs_tol": config.abs_tol, "rel_tol": config.rel_tol,
            "regional_config": json.loads(json.dumps(region_cfg.__dict__, allow_nan=False)),
        },
        "schema": SCHEMA,
        "implementation": implementation,
    }
    run_id = "int10k-full-history-" + _sha(identity_inputs)[:24]
    cases = {"direct": direct, "split_prefix": prefix, "split_resumed": resumed}
    serialization_started = time.perf_counter()
    payload_bytes = {name: canonical_bytes(result) for name, result in cases.items()}
    cp_bytes = {name: canonical_bytes(result["checkpoint"]) for name, result in cases.items()}
    serialization_seconds = time.perf_counter() - serialization_started
    payload_sizes = {name: len(payload) for name, payload in payload_bytes.items()}
    cp_sizes = {name: len(payload) for name, payload in cp_bytes.items()}
    # Query indexes name existing rows only; no state is interpolated or synthesized.
    query_index = _build_query_index(cases)
    record_counts = {}
    event_counts = {}
    record_sizes = {}
    for name, result in cases.items():
        regional_state = result["state"]
        regional_events = [event for row in regional_state["records"]
                           for event in row.get("events", [])]
        unified_steps = result["subsurface_unified_result"]["steps"]
        unified_events = [event for row in unified_steps
                          for event in row.get("events", [])]
        record_counts[name] = {
            "regional_year_records": len(regional_state["records"]),
            "regional_snapshots": len(regional_state["snapshots"]),
            "unified_step_records": len(result["subsurface_unified_result"]["steps"]),
        }
        event_counts[name] = {"regional_events": len(regional_events),
                              "unified_events": len(unified_events)}
        record_sizes[name] = {
            "regional_year_records_bytes": len(canonical_bytes(regional_state["records"])),
            "regional_snapshots_bytes": len(canonical_bytes(regional_state["snapshots"])),
            "unified_step_records_bytes": len(canonical_bytes(unified_steps)),
            "regional_events_bytes": len(canonical_bytes(regional_events)),
            "unified_events_bytes": len(canonical_bytes(unified_events)),
        }
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "status": "PASS_FULL_HISTORY_ORACLE_DIRECT_RESTART_PARITY",
        "run_id": run_id,
        "attempt_id": str(uuid4()),
        "source_identity": source,
        "implementation_commit": implementation_commit,
        "implementation_provenance": implementation,
        "configuration": identity_inputs["configuration"],
        "coverage": {
            "regional_year_records": list(range(1, config.years + 1)),
            "regional_snapshots": list(range(0, config.years + 1)),
            "unified_elapsed_years": [float(i) for i in range(1, config.years + 1)],
            "split_boundary_year": config.split_at,
            "checkpoint_origin": "ACTUAL_SPLIT_PREFIX_RUN_OUTPUT",
        },
        "cases": cases,
        "query_index": query_index,
        "validation": {
            "full_direct_vs_resumed_result_parity": "PASS",
            "split_checkpoint_integrity_and_coverage": "PASS",
            "identity_metadata_comparison": "EXACT",
            "numeric_comparison": {"absolute_tolerance": config.abs_tol,
                                    "relative_tolerance": config.rel_tol,
                                    "source": "EXISTING_E1_POLICY"},
            "queries": "INDEXED_ACTUAL_ROWS_ONLY_NO_INTERPOLATION",
        },
        "telemetry": {
            "wall_seconds": {"direct": direct_wall, "prefix_plus_resume": split_wall,
                             "total": wall_total},
            "process_cpu_seconds": {"direct": direct_cpu,
                                    "prefix_plus_resume": split_cpu,
                                    "total": cpu_total},
            "rss_bytes": {"before": rss_before, "after": rss_after,
                          "method": rss_method,
                          "peak_sampled": max(x for x in (rss_before, rss_after) if x is not None)
                          if rss_before is not None or rss_after is not None else None,
                          "sampling": "PHASE_BOUNDARY_ONLY; short local capture"},
            "tracemalloc_peak_python_bytes": python_heap_peak,
            "serialization_bytes_by_case": payload_sizes,
            "checkpoint_bytes_by_case": cp_sizes,
            "serialization_seconds_for_size_measurement": serialization_seconds,
            "record_counts_by_case": record_counts,
            "event_counts_by_case": event_counts,
            "record_payload_bytes_by_case": record_sizes,
            "query_index_entry_count": len(query_index),
            "resource_limits_enforced_by_oracle": False,
        },
        "limitations": [
            "This complete oracle is an in-memory legacy-runner reference, not E2 streaming.",
            "The three cases preserve raw full histories and therefore duplicate direct/resumed history.",
            "RSS values are process observations, not allocations or hard quotas.",
            "No provider or physical authority beyond the bound source identity is inferred.",
        ],
    }
    body["integrity"] = {"algorithm": "SHA256", "canonical_body_sha256": _sha(body)}
    verify_oracle(body)
    return body


def _build_query_index(cases: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = []
    for case_name, result in cases.items():
        state = result.get("state", {})
        for kind, rows, domain, time_key in (
            ("REGIONAL_SNAPSHOT", state.get("snapshots", []), "regional", "time_year"),
            ("REGIONAL_YEAR_RECORD", state.get("records", []), "regional", "time_year"),
            ("UNIFIED_STEP_RECORD",
             result.get("subsurface_unified_result", {}).get("steps", []),
             "unified", "elapsed_years"),
        ):
            for position, row in enumerate(rows):
                if not isinstance(row, Mapping):
                    raise FullHistoryOracleError("QUERY_INDEX_SOURCE_ROW_INVALID")
                index.append({"case": case_name, "domain": domain, "record_type": kind,
                              "time": row.get(time_key), "sequence": position,
                              "source_path": f"cases.{case_name}.{domain}.{kind}[{position}]"})
    return index


def verify_oracle(oracle: Mapping[str, Any]) -> None:
    if (oracle.get("schema") != SCHEMA or oracle.get("classification") != CLASSIFICATION
            or oracle.get("status") != "PASS_FULL_HISTORY_ORACLE_DIRECT_RESTART_PARITY"):
        raise FullHistoryOracleError("ORACLE_SCHEMA_OR_STATUS_INVALID")
    integrity = oracle.get("integrity")
    if not isinstance(integrity, Mapping) or integrity.get("algorithm") != "SHA256":
        raise FullHistoryOracleError("ORACLE_INTEGRITY_RECORD_INVALID")
    body = {key: value for key, value in oracle.items() if key != "integrity"}
    if integrity.get("canonical_body_sha256") != _sha(body):
        raise FullHistoryOracleError("ORACLE_DIGEST_MISMATCH")
    cases = oracle.get("cases")
    coverage = oracle.get("coverage")
    if not isinstance(cases, Mapping) or set(cases) != {"direct", "split_prefix", "split_resumed"}:
        raise FullHistoryOracleError("ORACLE_CASE_SET_INVALID")
    if not isinstance(coverage, Mapping):
        raise FullHistoryOracleError("ORACLE_COVERAGE_MISSING")
    configuration = oracle.get("configuration")
    years = configuration.get("years") if isinstance(configuration, Mapping) else None
    split = coverage.get("split_boundary_year")
    if (type(years) is not int or years < 1 or type(split) is not int
            or not 0 < split < years):
        raise FullHistoryOracleError("ORACLE_COVERAGE_INVALID")
    implementation = oracle.get("implementation_provenance")
    if not isinstance(implementation, Mapping):
        raise FullHistoryOracleError("ORACLE_IMPLEMENTATION_PROVENANCE_MISSING")
    identity_inputs = {"source_identity": oracle.get("source_identity"),
                       "configuration": configuration, "schema": SCHEMA,
                       "implementation": implementation}
    if oracle.get("run_id") != "int10k-full-history-" + _sha(identity_inputs)[:24]:
        raise FullHistoryOracleError("ORACLE_RUN_ID_MISMATCH")
    if not isinstance(oracle.get("attempt_id"), str) or not oracle["attempt_id"]:
        raise FullHistoryOracleError("ORACLE_ATTEMPT_ID_MISSING")
    expected_coverage = {
        "regional_year_records": list(range(1, years + 1)),
        "regional_snapshots": list(range(years + 1)),
        "unified_elapsed_years": [float(i) for i in range(1, years + 1)],
    }
    for key, expected in expected_coverage.items():
        if coverage.get(key) != expected:
            raise FullHistoryOracleError("ORACLE_COVERAGE_INVALID")
    _verify_result(cases["direct"], years=years)
    _verify_split_checkpoint(cases["split_prefix"], split_at=split)
    _verify_result(cases["split_resumed"], years=years)
    expected_index = _build_query_index(cases)
    if oracle.get("query_index") != expected_index:
        raise FullHistoryOracleError("ORACLE_QUERY_INDEX_INVALID")
    try:
        compare_reference(_comparison_view(cases["direct"]),
                          _comparison_view(cases["split_resumed"]),
                          abs_tol=float(oracle["configuration"]["abs_tol"]),
                          rel_tol=float(oracle["configuration"]["rel_tol"]))
    except (ShortReferenceError, KeyError, TypeError, ValueError) as exc:
        raise FullHistoryOracleError("ORACLE_DIRECT_RESTART_DIVERGENCE") from exc


def query_history(oracle: Mapping[str, Any], *, case: str, domain: str,
                  time_exact: int | float | None = None,
                  time_range: tuple[int | float, int | float] | None = None,
                  position_id: str | None = None, support_id: str | None = None,
                  material_id: str | None = None) -> dict[str, Any]:
    """Return archived rows only; time queries never interpolate."""
    verify_oracle(oracle)
    if case not in oracle["cases"] or domain not in {"regional", "unified"}:
        raise FullHistoryOracleError("QUERY_SELECTOR_INVALID")
    if (time_exact is None) == (time_range is None):
        raise FullHistoryOracleError("QUERY_TIME_SELECTOR_INVALID")
    if time_exact is not None and (type(time_exact) not in (int, float)
                                   or not math.isfinite(float(time_exact))):
        raise FullHistoryOracleError("QUERY_TIME_SELECTOR_INVALID")
    if time_range is not None:
        if (not isinstance(time_range, (tuple, list)) or len(time_range) != 2
                or any(type(value) not in (int, float) or not math.isfinite(float(value))
                       for value in time_range)
                or time_range[0] > time_range[1]):
            raise FullHistoryOracleError("QUERY_TIME_RANGE_INVALID")
    temporal_candidates = []
    for entry in oracle["query_index"]:
        if entry["case"] != case or entry["domain"] != domain:
            continue
        value = entry["time"]
        if time_exact is not None and value != time_exact:
            continue
        if time_range is not None and not time_range[0] <= value <= time_range[1]:
            continue
        temporal_candidates.append(entry)
    if not temporal_candidates:
        return {"status": "TIME_NOT_ARCHIVED", "records": [], "interpolated": False}
    matches = []
    for entry in temporal_candidates:
        result = oracle["cases"][case]
        if entry["record_type"] == "REGIONAL_SNAPSHOT":
            row = result["state"]["snapshots"][entry["sequence"]]
        elif entry["record_type"] == "REGIONAL_YEAR_RECORD":
            row = result["state"]["records"][entry["sequence"]]
        else:
            row = result["subsurface_unified_result"]["steps"][entry["sequence"]]
        if not _matches_identity(row, position_id, support_id, material_id):
            continue
        matches.append({"record_type": entry["record_type"], "time": entry["time"],
                        "source_path": entry["source_path"], "record": row})
    if not matches:
        return {"status": "NO_MATCH", "records": [], "interpolated": False}
    return {"status": "PASS_ARCHIVED_ROWS_ONLY", "records": matches,
            "interpolated": False}


def _matches_identity(row: Any, position_id: str | None, support_id: str | None,
                      material_id: str | None) -> bool:
    if position_id is not None and not _contains_value(row, {"cell_id", "position_id"}, position_id):
        return False
    if support_id is not None and not _contains_value(row, {"support_id", "support"}, support_id):
        return False
    if material_id is not None and not _contains_value(row, {"material_id", "material_role_id"}, material_id):
        return False
    return True


def _contains_value(value: Any, keys: set[str], target: str) -> bool:
    if isinstance(value, Mapping):
        return any(key == target or (key in keys and item == target)
                   or _contains_value(item, keys, target)
                   for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_value(item, keys, target) for item in value)
    return False


def write_new_oracle_bundle(oracle: Mapping[str, Any], output_dir: str | Path, *,
                           report: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Create an immutable new bundle after validation; never overwrite."""
    verify_oracle(oracle)
    target = Path(output_dir)
    if target.exists():
        raise FullHistoryOracleError("OUTPUT_DIRECTORY_COLLISION")
    target.mkdir(parents=True, exist_ok=False)
    oracle_payload = canonical_bytes(oracle)
    members = []
    files = [("FULL_HISTORY_ORACLE.json", oracle_payload)]
    if report is not None:
        files.append(("RUN_REPORT.json", canonical_bytes(report)))
    for name, payload in files:
        path = target / name
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        members.append({"path": name, "sha256": sha256_bytes(payload),
                        "byte_length": len(payload)})
    manifest = {"schema": "FULL_HISTORY_ORACLE_MANIFEST_V1",
                "completion": "ALL_VALIDATION_PASSED",
                "classification": CLASSIFICATION, "members": members}
    manifest_payload = canonical_bytes(manifest)
    with (target / "MANIFEST.json").open("xb") as stream:
        stream.write(manifest_payload)
        stream.flush()
        os.fsync(stream.fileno())
    return {**manifest, "manifest_sha256": sha256_bytes(manifest_payload),
            "output_bytes": sum(item["byte_length"] for item in members)
            + len(manifest_payload)}
