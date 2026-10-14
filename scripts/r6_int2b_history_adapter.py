#!/usr/bin/env python3
"""Bind verified noncanonical INT-0B/INT-1D observations to B0 query records.

This adapter never opens WORLD_HISTORY and never registers reconstructed rows.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from arcana_worldsim.r6.identity import BranchId, HistoryId
from arcana_worldsim.r6.provenance import ProvenanceRecord
from arcana_worldsim.r6.query import HistoryQueryService
from arcana_worldsim.r6.state import (
    AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport,
)
from arcana_worldsim.r6.store import HistoryStore
from r6_int1a_retention_audit import _absolute_checked, _json_bytes, _sha256
from r6_int2a_historical_query import AuditError, load_sources


DOMAIN = "tf2b-noncanonical-engineering-observation"
GRID_ID = "tf2b-observed-support-identifiers-v1"
TIME_COORDINATE = "elapsed_engineering_years_from_T0"
FIELD_UNITS = {
    "width_m": "m", "crust_m": "m", "lithosphere_m": "m", "beta": "1",
    "accumulated_strain": "1", "temperature_k": "K", "z_m": "m",
    "material_coordinate": "1",
}
EXPECTED_EXPERIMENTS = {"R4": "R4", "INT1D": "INT-1D"}


class AdapterError(ValueError):
    """A verified engineering observation cannot be represented safely."""


def exact_time_key(elapsed_years: float) -> str:
    if isinstance(elapsed_years, bool) or not isinstance(elapsed_years, (int, float)):
        raise AdapterError("OBSERVED_TIME_MUST_BE_NUMERIC")
    value = float(elapsed_years)
    if not math.isfinite(value) or value < 0.0:
        raise AdapterError("OBSERVED_TIME_INVALID")
    return f"engineering_elapsed_years:{value!r}"


def _provider_refs(source: dict[str, Any]) -> dict[str, str]:
    manifest = source["documents"]["CANDIDATE_MANIFEST.json"]
    providers = manifest.get("provider_identities")
    if not isinstance(providers, dict) or not providers:
        raise AdapterError("VERIFIED_PROVIDER_PROVENANCE_MISSING")
    if any(not isinstance(k, str) or not isinstance(v, str) or len(v) != 64
           for k, v in providers.items()):
        raise AdapterError("VERIFIED_PROVIDER_PROVENANCE_INVALID")
    return dict(sorted(providers.items()))


def build_observation_records(
    sources: dict[str, dict[str, Any]],
) -> tuple[tuple[ProvenanceRecord | DomainStateEnvelope, ...], dict[str, Any]]:
    """Create typed immutable B0 records from validated observed sample rows only."""
    if set(sources) != set(EXPECTED_EXPERIMENTS):
        raise AdapterError("UNEXPECTED_SOURCE_EXPERIMENT_SET")
    all_records: list[ProvenanceRecord | DomainStateEnvelope] = []
    summary: dict[str, Any] = {}
    ids: set[str] = set()
    for name in ("R4", "INT1D"):
        source = sources[name]
        if source.get("experiment") != EXPECTED_EXPERIMENTS[name]:
            raise AdapterError(f"SOURCE_EXPERIMENT_IDENTITY_MISMATCH:{name}")
        manifest_sha = source.get("manifest_sha256")
        sample_sha = source.get("sample_artifact_sha256")
        run_sha = source.get("run_result_sha256")
        if any(not isinstance(v, str) or len(v) != 64 for v in
               (manifest_sha, sample_sha, run_sha, source.get("source_identity_sha256"))):
            raise AdapterError(f"SOURCE_DIGEST_MISSING:{name}")
        provider_refs = _provider_refs(source)
        history_id = str(HistoryId.from_payload({
            "scope": "NONCANONICAL_ENGINEERING_IMPORT_V1", "experiment": name,
            "manifest_sha256": manifest_sha,
        }))
        branch_id = str(BranchId.from_payload({
            "scope": "NONCANONICAL_ENGINEERING_IMPORT_V1", "experiment": name,
            "manifest_sha256": manifest_sha,
        }))
        source_refs = (
            f"experiment:{name}", f"candidate_manifest_sha256:{manifest_sha}",
            f"run_result_sha256:{run_sha}", f"sample_artifact_sha256:{sample_sha}",
            f"source_commit:{source['source_commit']}",
            f"source_composite_sha256:{source['source_identity_sha256']}",
            f"boundary_id:{source['boundary_id']}",
            *(f"provider_sha256:{key}:{value}" for key, value in provider_refs.items()),
        )
        provenance = ProvenanceRecord.create(
            activity="REGISTER_VERIFIED_NONCANONICAL_TF2B_OBSERVATION",
            source_refs=tuple(source_refs),
            attributes={
                "scope": "NONCANONICAL_ENGINEERING_OBSERVATION",
                "canonical_publication": False,
                "scientific_authority": "NOT_CLAIMED",
                "experiment": name,
                "history_id": history_id,
                "branch_id": branch_id,
                "manifest_sha256": manifest_sha,
                "run_result_sha256": run_sha,
                "sample_artifact_sha256": sample_sha,
                "source_commit": source["source_commit"],
                "source_composite_sha256": source["source_identity_sha256"],
                "boundary_id": source["boundary_id"],
                "provider_identities": provider_refs,
                "resolution_fraction": source["resolution_fraction"],
                "sampling": source["sampling"],
            },
        )
        all_records.append(provenance)
        per_experiment = 0
        support_rows = source.get("rows")
        if not isinstance(support_rows, dict) or set(support_rows) != set(source["supports"]):
            raise AdapterError(f"SOURCE_SUPPORT_SET_MISMATCH:{name}")
        for support_id in source["supports"]:
            rows = support_rows[support_id]
            if not rows:
                raise AdapterError(f"EMPTY_OBSERVED_SUPPORT:{name}:{support_id}")
            for ordinal, row in enumerate(rows):
                if row.get("record_type") not in {"DIAGNOSTIC_SAMPLE", "ENDPOINT_STATE"}:
                    raise AdapterError("NON_OBSERVED_OR_RECONSTRUCTED_ROW_REJECTED")
                if row.get("support_id") != support_id:
                    raise AdapterError("ROW_SUPPORT_IDENTITY_MISMATCH")
                elapsed = row.get("elapsed_years")
                time_key = exact_time_key(elapsed)
                coordinates = row.get("material_coordinate")
                z_values = row.get("z_m")
                temperature = row.get("temperature_k")
                if (not isinstance(coordinates, list) or not isinstance(z_values, list)
                        or not isinstance(temperature, list) or not coordinates
                        or len(coordinates) != len(z_values) or len(z_values) != len(temperature)):
                    raise AdapterError("OBSERVED_PROFILE_SHAPE_INVALID")
                fields = {field: row[field] for field in FIELD_UNITS}
                for field, value in fields.items():
                    values = value if isinstance(value, list) else [value]
                    if any(isinstance(v, bool) or not isinstance(v, (int, float))
                           or not math.isfinite(float(v)) for v in values):
                        raise AdapterError(f"OBSERVED_FIELD_NONFINITE_OR_INVALID:{field}")
                record_value = {
                    "record_type": row["record_type"],
                    "elapsed_years": float(elapsed),
                    "time_s": row["time_s"],
                    "field_values": fields,
                    "field_units": FIELD_UNITS,
                    "source_row_ordinal": ordinal,
                    "source_sample_sha256": sample_sha,
                }
                state = DomainStateEnvelope.create(
                    history_id=history_id, branch_id=branch_id, domain=DOMAIN,
                    time_support=TimeSupport(time_key, TIME_COORDINATE, "INSTANT"),
                    spatial_support=SpatialSupport(
                        GRID_ID, (support_id,), str(source["resolution_fraction"]), "CELL_SET"),
                    support_class=SupportClass.DERIVED_SUPPORTED,
                    authority_class=AuthorityClass.NONE,
                    value=record_value,
                    uncertainty={"status": "UNKNOWN_NOT_REPORTED_BY_SOURCE"},
                    provenance_ids=(str(provenance.record_id),),
                    model_derived=True,
                    applicability={
                        "scope": "NONCANONICAL_ENGINEERING_OBSERVATION",
                        "canonical_publication": False,
                        "physical_geographic_authority": "NOT_CLAIMED",
                        "experiment": name,
                        "boundary_id": source["boundary_id"],
                        "support_id": support_id,
                        "resolution_fraction": source["resolution_fraction"],
                        "sampling": source["sampling"],
                        "time_key_semantics": "EXACT_OBSERVED_ENGINEERING_ELAPSED_YEARS",
                    },
                )
                state_id = str(state.state_id)
                if state_id in ids:
                    raise AdapterError("DUPLICATE_OBSERVED_STATE_ID")
                ids.add(state_id)
                all_records.append(state)
                per_experiment += 1
        summary[name] = {
            "experiment": source["experiment"], "history_id": history_id,
            "branch_id": branch_id, "domain": DOMAIN,
            "manifest_sha256": manifest_sha, "run_result_sha256": run_sha,
            "sample_artifact_sha256": sample_sha,
            "source_commit": source["source_commit"],
            "source_composite_sha256": source["source_identity_sha256"],
            "boundary_id": source["boundary_id"], "support_ids": list(source["supports"]),
            "resolution_fraction": source["resolution_fraction"],
            "observed_state_count": per_experiment,
            "authority_class": AuthorityClass.NONE.value,
            "support_class": SupportClass.DERIVED_SUPPORTED.value,
        }
    return tuple(all_records), summary


def probe_hardlink_capability(directory: Path) -> tuple[bool, str | None]:
    """Probe actual same-directory hard-link publication; clean only own names."""
    directory = Path(os.path.abspath(directory))
    if not directory.is_dir():
        return False, "PROBE_DIRECTORY_UNAVAILABLE"
    try:
        fd, source_name = tempfile.mkstemp(prefix=".int2b-link-probe-", dir=directory)
    except OSError as exc:
        return False, f"{type(exc).__name__}:{exc}"
    os.close(fd)
    source = Path(source_name)
    link = source.with_name(source.name + ".link")
    failure: str | None = None
    try:
        source.write_bytes(b"ARCANA_INT2B_HARDLINK_PROBE\x00\xff")
        os.link(source, link)
        if source.read_bytes() != link.read_bytes():
            failure = "HARDLINK_BYTES_DIFFER"
        elif source.stat().st_ino != link.stat().st_ino:
            failure = "HARDLINK_IDENTITY_NOT_SHARED"
    except OSError as exc:
        failure = f"{type(exc).__name__}:{exc}"
    finally:
        for path in (link, source):
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                failure = failure or f"PROBE_CLEANUP_FAILED:{type(exc).__name__}:{exc}"
    if source.exists() or link.exists():
        failure = failure or "PROBE_CLEANUP_INCOMPLETE"
    return failure is None, failure


def _filesystem_type(path: Path) -> str:
    """Return the detected filesystem type, or UNKNOWN when unavailable."""
    path = Path(os.path.realpath(os.path.abspath(path)))
    if os.name == "nt":
        try:
            from ctypes import wintypes

            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            volume_path = ctypes.create_unicode_buffer(32768)
            filesystem = ctypes.create_unicode_buffer(256)
            kernel.GetVolumePathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
            kernel.GetVolumePathNameW.restype = wintypes.BOOL
            if not kernel.GetVolumePathNameW(str(path), volume_path, len(volume_path)):
                return "UNKNOWN"
            kernel.GetVolumeInformationW.argtypes = [
                wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
                ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
                ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD,
            ]
            kernel.GetVolumeInformationW.restype = wintypes.BOOL
            if not kernel.GetVolumeInformationW(
                    volume_path.value, None, 0, None, None, None,
                    filesystem, len(filesystem)):
                return "UNKNOWN"
            return filesystem.value or "UNKNOWN"
        except (AttributeError, OSError, TypeError, ValueError):
            return "UNKNOWN"
    if sys.platform.startswith("linux"):
        try:
            candidates: list[tuple[int, str]] = []
            for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
                left, separator, right = line.partition(" - ")
                if not separator:
                    continue
                fields = left.split()
                filesystem_fields = right.split()
                if len(fields) < 5 or not filesystem_fields:
                    continue
                mountpoint = re.sub(
                    r"\\([0-7]{3})",
                    lambda match: chr(int(match.group(1), 8)),
                    fields[4],
                )
                try:
                    if os.path.commonpath((str(path), mountpoint)) == mountpoint:
                        candidates.append((len(mountpoint), filesystem_fields[0]))
                except ValueError:
                    continue
            if candidates:
                return max(candidates)[1]
        except (OSError, UnicodeError):
            pass
    return "UNKNOWN"


def _filesystem_capability(path: Path, hardlink_ok: bool, reason: str | None) -> dict[str, Any]:
    return {"volume": _filesystem_type(path), "hardlink_probe_pass": hardlink_ok,
            "reason": reason}


def query_and_measure(
    store: HistoryStore,
    records: tuple[ProvenanceRecord | DomainStateEnvelope, ...],
    sources: dict[str, dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    state_records = tuple(r for r in records if isinstance(r, DomainStateEnvelope))
    service = HistoryQueryService(store)
    query_samples: list[dict[str, Any]] = []
    checked = 0
    for name in ("R4", "INT1D"):
        source = sources[name]
        binding = summary[name]
        for support_id in source["supports"]:
            for row in source["rows"][support_id]:
                key = exact_time_key(row["elapsed_years"])
                started = time.perf_counter_ns()
                result = service.state_at(
                    history_id=binding["history_id"], branch_id=binding["branch_id"],
                    domain=DOMAIN, time_key=key, cell_id=support_id)
                elapsed_ns = time.perf_counter_ns() - started
                expected = next(
                    state for state in state_records
                    if state.history_id == binding["history_id"]
                    and state.spatial_support.cell_ids == (support_id,)
                    and state.time_support.time_key == key)
                if result.status != "FOUND" or result.state != expected:
                    raise AdapterError(f"EXACT_QUERY_READBACK_MISMATCH:{name}:{support_id}:{key}")
                if result.provenance is None or len(result.provenance["provenance_records"]) != 1:
                    raise AdapterError("PROVENANCE_TRACE_INCOMPLETE")
                if result.state.to_dict()["value"]["field_values"] != {
                        field: row[field] for field in FIELD_UNITS}:
                    raise AdapterError("QUERY_VALUE_DIFFERS_FROM_OBSERVED_SAMPLE")
                checked += 1
                if len(query_samples) < 4:
                    query_samples.append({"experiment": name, "support_id": support_id,
                                          "elapsed_years": row["elapsed_years"],
                                          "time_key": key, "status": result.status,
                                          "state_id": str(result.state.state_id),
                                          "latency_ns": elapsed_ns})
    for name in ("R4", "INT1D"):
        binding = summary[name]
        sample_time = exact_time_key(sources[name]["rows"][sources[name]["supports"][0]][0]["elapsed_years"])
        missing = service.state_at(history_id=binding["history_id"], branch_id=binding["branch_id"],
                                   domain=DOMAIN, time_key="engineering_elapsed_years:999999999.0")
        if missing.status != "MISSING_TIMESTAMP":
            raise AdapterError("MISSING_TIMESTAMP_QUERY_SEMANTICS_CHANGED")
        ambiguous = service.state_at(history_id=binding["history_id"], branch_id=binding["branch_id"],
                                     domain=DOMAIN, time_key=sample_time)
        if ambiguous.status != "CONFLICT":
            raise AdapterError("AMBIGUOUS_SUPPORT_QUERY_SEMANTICS_CHANGED")
        outside = service.state_at(history_id=binding["history_id"], branch_id=binding["branch_id"],
                                   domain=DOMAIN, time_key=sample_time, cell_id="UNKNOWN_SUPPORT")
        if outside.status != "OUTSIDE_SUPPORT":
            raise AdapterError("MISSING_SUPPORT_QUERY_SEMANTICS_CHANGED")
    store_files = sorted(p for p in store.root.rglob("*") if p.is_file())
    store_bytes = sum(p.stat().st_size for p in store_files)
    return {"readback_state_count": checked,
            "store_file_count": len(store_files), "store_bytes": store_bytes,
            "query_samples": query_samples,
            "query_latency_ns_observed_sample": {
                "min": min(item["latency_ns"] for item in query_samples),
                "max": max(item["latency_ns"] for item in query_samples),
                "sample_count": len(query_samples)},
            "query_semantics": {"missing_timestamp": "MISSING_TIMESTAMP",
                                 "missing_support": "OUTSIDE_SUPPORT",
                                 "ambiguous_support_without_cell_selector": "CONFLICT"}}


def _write_output(output_dir: Path, result: dict[str, Any]) -> dict[str, Any]:
    payload = _json_bytes(result)
    target = output_dir / "INT2B_B0_BINDING_RESULT.json"
    if target.exists() or target.write_bytes(payload) != len(payload) or target.read_bytes() != payload:
        raise AdapterError("OUTPUT_WRITE_OR_READBACK_FAILED")
    manifest = {"schema": "ARCANA_R6_INT2B_NONCANONICAL_OUTPUT_MANIFEST_V1",
                "files": {target.name: {"bytes": len(payload), "sha256": _sha256(payload)}},
                "source_manifests": {name: result["source_identities"][name]["manifest_sha256"]
                                     for name in ("R4", "INT1D")},
                "decision": result["decision"], "scope": result["scope"]}
    manifest_data = _json_bytes(manifest)
    manifest_path = output_dir / "INT2B_OUTPUT_MANIFEST.json"
    if manifest_path.exists() or manifest_path.write_bytes(manifest_data) != len(manifest_data):
        raise AdapterError("OUTPUT_MANIFEST_WRITE_FAILED")
    sidecar = f"{_sha256(manifest_data)}  INT2B_OUTPUT_MANIFEST.json\n".encode("ascii")
    sidecar_path = output_dir / "INT2B_OUTPUT_MANIFEST.json.sha256"
    if sidecar_path.exists() or sidecar_path.write_bytes(sidecar) != len(sidecar):
        raise AdapterError("OUTPUT_SIDECAR_WRITE_FAILED")
    if target.read_bytes() != payload or manifest_path.read_bytes() != manifest_data or sidecar_path.read_bytes() != sidecar:
        raise AdapterError("OUTPUT_FINAL_READBACK_FAILED")
    return {"result_bytes": len(payload), "result_sha256": _sha256(payload),
            "manifest_bytes": len(manifest_data), "manifest_sha256": _sha256(manifest_data),
            "sidecar_sha256": _sha256(sidecar)}


def run_int2b(r4_root: Path, int1d_root: Path, output_dir: Path) -> dict[str, Any]:
    output_dir = _absolute_checked(Path(output_dir), must_exist=False)
    r4_root = _absolute_checked(Path(r4_root), must_exist=True)
    int1d_root = _absolute_checked(Path(int1d_root), must_exist=True)
    if any(output_dir == source or output_dir in source.parents or source in output_dir.parents
           for source in (r4_root, int1d_root)):
        raise AdapterError("OUTPUT_PATH_OVERLAPS_INPUT_BUNDLE")
    repository_root = Path(__file__).resolve().parents[1]
    protected_roots = (repository_root / "WORLD_HISTORY",
                       repository_root / "world_history_bindings" / "r6_physical_world_t0")
    for protected in protected_roots:
        protected_abs = Path(os.path.abspath(protected))
        if output_dir == protected_abs or output_dir in protected_abs.parents or protected_abs in output_dir.parents:
            raise AdapterError("OUTPUT_PATH_OVERLAPS_CANONICAL_HISTORY")
    if output_dir.exists():
        raise AdapterError("OUTPUT_DIRECTORY_ALREADY_EXISTS")
    sources = load_sources(r4_root, int1d_root)
    records, summary = build_observation_records(sources)
    output_dir.mkdir(parents=True, exist_ok=False)
    link_ok, link_reason = probe_hardlink_capability(output_dir)
    checkpoint_status: dict[str, Any] = {}
    from arcana_worldsim.r6.functional_development import state_from_payload
    for name in ("R4", "INT1D"):
        candidates = sources[name]["documents"]["CANDIDATE_CHECKPOINT.json"]["candidate_states"]
        restored = [state_from_payload(payload) for payload in candidates]
        checkpoint_status[name] = {
            "candidate_state_count": len(restored),
            "reduced_state_deserialization": "PASS",
            "kernel_restart_complete": False,
            "missing_restart_binding": ["registered B0 checkpoint envelope", "closed runner/configuration binding",
                                        "forcing and deterministic engine adapter"],
        }
    result: dict[str, Any] = {
        "schema": "ARCANA_R6_INT2B_B0_BINDING_RESULT_V1",
        "scope": "NONCANONICAL_VERIFIED_ENGINEERING_OBSERVATIONS_ONLY",
        "decision": "INT2B_BLOCKED_STORE_ATOMIC_PUBLICATION_UNAVAILABLE",
        "source_identities": summary,
        "planned_registration": {"state_count": sum(x["observed_state_count"] for x in summary.values()),
                                  "provenance_count": len(summary),
                                  "records_built_from_verified_observed_samples": True},
        "checkpoint_assessment": checkpoint_status,
        "filesystem_capability": _filesystem_capability(output_dir, link_ok, link_reason),
        "history_store": {"created": False, "registration": "NOT_ATTEMPTED_AFTER_HARDLINK_PROBE_FAILURE",
                          "queries_executed": False, "store_bytes": None,
                          "query_latency": None},
        "replay": {"candidate_checkpoint_deserializes_as_reduced_state": True,
                   "registered_checkpoint_envelope": False,
                   "executable_replay_qualified": False},
        "canonical_world_history_written": False,
        "limitations": ["NO_B0_STORE_QUERY_PASS", "NO_EXECUTABLE_REPLAY_QUALIFICATION",
                        "NO_SCIENTIFIC_AUTHORITY", "NO_CANONICAL_PUBLICATION"],
    }
    if link_ok:
        try:
            store = HistoryStore(output_dir / "isolated_history_store")
            store.append_transaction(records)
            measured = query_and_measure(store, records, sources, summary)
            result["decision"] = "INT2B_NONCANONICAL_B0_STATE_QUERY_BINDING_EVIDENCED__EXECUTABLE_REPLAY_NOT_QUALIFIED"
            result["history_store"] = {"created": True, "registration": "TRANSACTION_COMMITTED_AND_READBACK_VERIFIED",
                                        "queries_executed": True, **measured}
        except Exception as exc:
            failed_store = output_dir / "isolated_history_store"
            partial_inventory = []
            if failed_store.exists():
                for path in sorted(p for p in failed_store.rglob("*") if p.is_file()):
                    data = path.read_bytes()
                    partial_inventory.append({"path": path.relative_to(failed_store).as_posix(),
                                              "bytes": len(data), "sha256": _sha256(data)})
            result["decision"] = "INT2B_BLOCKED_STORE_REGISTRATION_OR_QUERY_FAILURE"
            result["history_store"].update({"created": (output_dir / "isolated_history_store").exists(),
                                             "registration": "FAILED_CLOSED",
                                             "failure_type": type(exc).__name__,
                                             "failure": str(exc),
                                             "partial_store_inventory": partial_inventory})
    metadata = _write_output(output_dir, result)
    return {"decision": result["decision"], "output": str(output_dir), **metadata}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r4", type=Path, required=True)
    parser.add_argument("--int1d", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run_int2b(args.r4, args.int1d, args.output), sort_keys=True))
    except (AuditError, AdapterError, OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(f"{type(exc).__name__}:{exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
