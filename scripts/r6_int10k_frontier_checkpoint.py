"""Measure and round-trip E2-B frontiers against local E2-A1 references.

This short qualification helper does not claim an append-only store or a
history-independent legacy resume. Outputs must be placed outside the repo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tracemalloc
import platform

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from arcana_worldsim.r6.geological_surface_microdomain import (
    SUPPORTS, load_verified_r6_initial_columns,
)
from arcana_worldsim.r6.int10k_full_history_oracle import (
    _comparison_view, _measure_rss_bytes, compare_reference, verify_oracle,
)
from arcana_worldsim.r6.int10k_frontier_checkpoint import (
    capture_frontier_v2, restore_legacy_checkpoint_v1, seal_checkpoint_v2,
    serialize_checkpoint_v2, serialize_history_prefix,
)
from arcana_worldsim.r6.int10k_short_reference import verify_source_bundle
from arcana_worldsim.r6.regional_geological_evolution import (
    RegionalConfig, run_regional_segment,
)
from arcana_worldsim.r6.unified_multiphysics_microdomain import _state_from_payload


SOURCE_HASHES = {
    "RESULT.json": "24f492ad9861a25369af42b513eb1a971007ef11571f6dc5ab5140729cc10fd5",
    "MANIFEST.json": "a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21",
    "RESULT.json.sha256": "8eab8b24f21088e3de82254f3d4929c61a7ed8a341593e3a4cbbafcc4bca2ce0",
}


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _read_bundle(directory: Path) -> dict:
    manifest_path = directory / "MANIFEST.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if (manifest.get("schema") != "FULL_HISTORY_ORACLE_MANIFEST_V1"
            or manifest.get("completion") != "ALL_VALIDATION_PASSED"
            or manifest.get("classification") != "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY"):
        raise ValueError("ORACLE_BUNDLE_MANIFEST_INVALID")
    expected_names = {"FULL_HISTORY_ORACLE.json", "RUN_REPORT.json"}
    entries = manifest.get("members")
    if not isinstance(entries, list) or {e.get("path") for e in entries} != expected_names:
        raise ValueError("ORACLE_BUNDLE_MEMBERS_INVALID")
    for entry in entries:
        data = (directory / entry["path"]).read_bytes()
        if len(data) != entry.get("byte_length") or _sha_bytes(data) != entry.get("sha256"):
            raise ValueError("ORACLE_BUNDLE_MEMBER_INTEGRITY_FAILED")
    oracle = json.loads((directory / "FULL_HISTORY_ORACLE.json").read_bytes())
    verify_oracle(oracle)
    return oracle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-dir", required=True, type=Path)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    oracle_dir = args.oracle_dir.resolve(strict=True)
    input_dir = args.input_dir.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    if (output_dir.exists() or output_dir == REPOSITORY
            or REPOSITORY in output_dir.parents or output_dir == oracle_dir
            or oracle_dir in output_dir.parents or output_dir == input_dir
            or input_dir in output_dir.parents):
        parser.error("OUTPUT_MUST_BE_NEW_EXTERNAL_EVIDENCE_DIRECTORY")

    oracle = _read_bundle(oracle_dir)
    years = oracle["configuration"]["years"]
    split = oracle["configuration"]["split_at"]
    if (years, split) not in {(3, 1), (10, 5)}:
        parser.error("REFERENCE_CONFIGURATION_NOT_SUPPORTED")
    source_before = verify_source_bundle(input_dir, SOURCE_HASHES)
    payloads, source_identity = load_verified_r6_initial_columns(input_dir)
    if source_identity != oracle["source_identity"] or set(payloads) != set(SUPPORTS):
        parser.error("E0_SOURCE_IDENTITY_OR_SUPPORT_MISMATCH")
    initial_states = {support: _state_from_payload(payloads[support])
                      for support in SUPPORTS}

    cases = oracle["cases"]
    measurements = []
    artifacts = []
    split_checkpoint = None
    split_history = None
    for age, case_name in ((split, "split_prefix"), (years, "split_resumed")):
        legacy_checkpoint = cases[case_name]["checkpoint"]
        frontier_obj, history_obj = capture_frontier_v2(legacy_checkpoint)
        checkpoint_obj = seal_checkpoint_v2(frontier_obj)
        checkpoint_bytes = serialize_checkpoint_v2(checkpoint_obj)
        history_bytes = serialize_history_prefix(history_obj)
        frontier_bytes = frontier_obj.canonical_json
        restored = restore_legacy_checkpoint_v1(
            checkpoint_obj, history_obj, expected_source_identity=source_identity,
            expected_configuration=frontier_obj.payload["configuration"])
        if restored != legacy_checkpoint:
            raise ValueError("LEGACY_CHECKPOINT_ROUNDTRIP_MISMATCH")
        suffix = f"year_{age:02d}"
        for filename, data in ((f"frontier_{suffix}.json", frontier_bytes),
                                (f"checkpoint_{suffix}.json", checkpoint_bytes)):
            artifacts.append((filename, data))
        measurements.append({
            "age_year": age,
            "source_case": case_name,
            "frontier_bytes": len(frontier_bytes),
            "checkpoint_bytes": len(checkpoint_bytes),
            "history_prefix_reference_bytes": len(history_bytes),
            "history_prefix_sha256": _sha_bytes(history_bytes),
            "history_arrays_embedded_in_frontier": False,
            "legacy_checkpoint_roundtrip": "PASS_EXACT",
        })
        if age == split:
            split_checkpoint = checkpoint_obj
            split_history = history_obj

    if split_checkpoint is None or split_history is None:
        raise ValueError("SPLIT_FRONTIER_NOT_CAPTURED")
    rss_before, rss_method = _measure_rss_bytes()
    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start()
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    restored_checkpoint = restore_legacy_checkpoint_v1(
        split_checkpoint, split_history, expected_source_identity=source_identity,
        expected_configuration=split_checkpoint.envelope["frontier"]["configuration"])
    config = RegionalConfig(**oracle["configuration"]["regional_config"])
    actual = run_regional_segment(
        initial_states, source_identity, config=config,
        segment_years=years - split, checkpoint=restored_checkpoint)
    expected = cases["split_resumed"]
    compare_reference(_comparison_view(actual), _comparison_view(expected),
                      abs_tol=float(oracle["configuration"]["abs_tol"]),
                      rel_tol=float(oracle["configuration"]["rel_tol"]))
    resume_wall = time.perf_counter() - started_wall
    resume_cpu = time.process_time() - started_cpu
    _, python_heap_peak = tracemalloc.get_traced_memory()
    rss_after, _ = _measure_rss_bytes()
    if not was_tracing:
        tracemalloc.stop()
    if verify_source_bundle(input_dir, SOURCE_HASHES) != source_before:
        raise ValueError("E0_INPUTS_CHANGED_DURING_FRONTIER_QUALIFICATION")

    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPOSITORY,
                                check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    source_paths = (
        "scripts/r6_int10k_frontier_checkpoint.py",
        "src/arcana_worldsim/r6/int10k_frontier_checkpoint.py",
        "src/arcana_worldsim/r6/int10k_full_history_oracle.py",
        "src/arcana_worldsim/r6/regional_geological_evolution.py",
        "src/arcana_worldsim/r6/unified_multiphysics_microdomain.py",
    )
    implementation_hashes = {
        path: _sha_bytes((REPOSITORY / path).read_bytes()) for path in source_paths
    }
    report = {
        "schema": "INT10K_E2_B_FRONTIER_QUALIFICATION_REPORT_V1",
        "status": "PASS_LOCAL_REFERENCE_FRONTIER_RESTORE_PARITY",
        "classification": "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY",
        "source_commit_at_capture": commit,
        "implementation_source_sha256": implementation_hashes,
        "oracle_source_directory": str(oracle_dir),
        "oracle_run_id": oracle["run_id"],
        "oracle_sha256": oracle["integrity"]["canonical_body_sha256"],
        "operator_reported_fair_oracles_used": False,
        "local_windows_oracle_used": True,
        "e0_source_bundle_verified_before_and_after": True,
        "e0_input_identities_match_oracle": True,
        "checkpoint_size_by_frontier_age": measurements,
        "restored_split_continuation": {
            "status": "PASS_MATCHES_LOCAL_FULL_HISTORY_ORACLE",
            "years": years, "split_at": split,
            "wall_seconds": resume_wall, "process_cpu_seconds": resume_cpu,
            "numeric_tolerance": {
                "absolute": oracle["configuration"]["abs_tol"],
                "relative": oracle["configuration"]["rel_tol"],
            },
            "identities_orders_and_history_coverage": "EXACT_BY_REFERENCE_COMPARISON",
            "tracemalloc_peak_python_bytes": python_heap_peak,
            "rss_bytes_before_after": {"before": rss_before, "after": rss_after,
                                        "method": rss_method,
                                        "sampling": "PHASE_BOUNDARY_ONLY_NOT_CONTINUOUS_PEAK"},
        },
        "runtime": {"python": sys.version, "numpy": _numpy_version(),
                    "platform": platform.platform(), "pid": os.getpid()},
        "frontier_contract_limits": [
            "The frontier omits regional records/snapshots/routing event arrays and unified step records.",
            "The compatibility restore requires the separately supplied complete historical prefix.",
            "The current engine resume path consumes the reattached full history; history-independent continuation is NOT demonstrated.",
            "No append-only history writer, commit transaction, recovery chain, or atomic visibility protocol is implemented.",
            "Dynamic inventories such as stratified deposits and cumulative ledgers remain in the frontier and may grow with actual model evolution.",
        ],
        "resource_limits_enforced": False,
        "world_history_production_authorized": False,
        "geodyn_2b_arcana_forward_authorized": False,
    }
    artifacts.append(("RESTORE_COMPARISON.json", _canonical(report)))
    output_dir.mkdir(parents=True, exist_ok=False)
    members = []
    for filename, payload in artifacts:
        _write_new(output_dir / filename, payload)
        members.append({"path": filename, "sha256": _sha_bytes(payload),
                        "byte_length": len(payload)})
    manifest = {
        "schema": "INT10K_E2_B_FRONTIER_BUNDLE_MANIFEST_V1",
        "completion": "LOCAL_REFERENCE_VALIDATION_PASSED",
        "classification": "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY",
        "members": members,
    }
    manifest_bytes = _canonical(manifest)
    _write_new(output_dir / "MANIFEST.json", manifest_bytes)
    print(json.dumps({"status": report["status"], "output_dir": str(output_dir),
                      "manifest_sha256": _sha_bytes(manifest_bytes),
                      "member_count": len(members), "resume_wall_seconds": resume_wall,
                      "resume_cpu_seconds": resume_cpu,
                      "checkpoint_sizes": measurements}, indent=2))
    return 0


def _numpy_version() -> str | None:
    try:
        import numpy
    except ImportError:
        return None
    return str(numpy.__version__)


if __name__ == "__main__":
    raise SystemExit(main())
