"""Measure and qualify history-independent INT10K continuation for 3/10 years.

The collector is deliberately external to engine checkpoints. This remains a
lossless in-memory/history-file qualification harness, not an append-only store.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
import tracemalloc

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from arcana_worldsim.r6.geological_surface_microdomain import (  # noqa: E402
    SUPPORTS, load_verified_r6_initial_columns,
)
from arcana_worldsim.r6.int10k_full_history_oracle import (  # noqa: E402
    _measure_rss_bytes, compare_reference, verify_oracle,
)
from arcana_worldsim.r6.int10k_history_independent import (  # noqa: E402
    HistoryCollector, HistoryContinuationError, HistoryReader,
    verify_history_independent_checkpoint,
)
from arcana_worldsim.r6.int10k_source_provenance import (  # noqa: E402
    inspect_measured_sources_git, qualification_exit_code, qualification_may_execute,
)
from arcana_worldsim.r6.int10k_short_reference import (  # noqa: E402
    verify_source_bundle,
)
from arcana_worldsim.r6.regional_geological_evolution import (  # noqa: E402
    RegionalConfig, run_regional_segment,
)
from arcana_worldsim.r6.unified_multiphysics_microdomain import (  # noqa: E402
    _accumulate_history_record, _empty_history_accumulators, _state_from_payload,
)


SOURCE_HASHES = {
    "RESULT.json": "24f492ad9861a25369af42b513eb1a971007ef11571f6dc5ab5140729cc10fd5",
    "MANIFEST.json": "a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21",
    "RESULT.json.sha256": "8eab8b24f21088e3de82254f3d4929c61a7ed8a341593e3a4cbbafcc4bca2ce0",
}


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_oracle(directory: Path) -> dict:
    manifest_bytes = (directory / "MANIFEST.json").read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if (manifest.get("schema") != "FULL_HISTORY_ORACLE_MANIFEST_V1"
            or manifest.get("completion") != "ALL_VALIDATION_PASSED"
            or manifest.get("classification") != "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY"):
        raise ValueError("ORACLE_MANIFEST_INVALID")
    members = manifest.get("members")
    if not isinstance(members, list) or {row.get("path") for row in members} != {
            "FULL_HISTORY_ORACLE.json", "RUN_REPORT.json"}:
        raise ValueError("ORACLE_MEMBER_SET_INVALID")
    for member in members:
        data = (directory / member["path"]).read_bytes()
        if len(data) != member.get("byte_length") or _sha(data) != member.get("sha256"):
            raise ValueError("ORACLE_MEMBER_INTEGRITY_FAILED")
    oracle = json.loads((directory / "FULL_HISTORY_ORACLE.json").read_text(encoding="utf-8"))
    verify_oracle(oracle)
    return oracle


def _write_new(path: Path, payload: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _without_region_history(state: dict) -> dict:
    value = json.loads(_canonical(state))
    for key in ("records", "snapshots", "routing_events", "initial_condition_events",
                "history_independent_continuation"):
        value.pop(key, None)
    return value


def _without_unified_history(state: dict) -> dict:
    value = json.loads(_canonical(state))
    for key in ("records", "history_independent_continuation", "history_accumulators"):
        value.pop(key, None)
    return value


def _joined(prefix: dict, suffix: dict) -> dict:
    return {key: prefix[key] + suffix[key] for key in (
        "regional_records", "regional_snapshots", "regional_events", "unified_steps")}


def _assert_history(actual: dict, expected_result: dict, *, years: int) -> None:
    state = expected_result["state"]
    unified = expected_result["subsurface_unified_result"]
    compare_reference(actual["regional_records"], state["records"], abs_tol=1e-8, rel_tol=2e-14)
    compare_reference(actual["regional_snapshots"], state["snapshots"], abs_tol=1e-8, rel_tol=2e-14)
    compare_reference(actual["unified_steps"], unified["steps"], abs_tol=1e-8, rel_tol=2e-14)
    record_events = [event for row in state["records"] for event in row.get("events", [])]
    embedded_routing = Counter(_canonical(event) for event in record_events
                               if event.get("kind") == "DRAINAGE_CONNECTIVITY_CHANGED")
    expected_events = list(state["initial_condition_events"]) + record_events
    for event in state["routing_events"]:
        key = _canonical(event)
        if event.get("kind") == "DRAINAGE_CONNECTIVITY_CHANGED" and embedded_routing[key]:
            embedded_routing[key] -= 1
        else:
            expected_events.append(event)
    expected_event_bytes = sorted(_canonical(event) for event in expected_events)
    actual_event_bytes = sorted(_canonical(event) for event in actual["regional_events"])
    if actual_event_bytes != expected_event_bytes:
        raise ValueError("REGIONAL_EVENT_STREAM_COVERAGE_INVALID")
    if [row.get("time_year") for row in actual["regional_records"]] != list(range(1, years + 1)):
        raise ValueError("REGIONAL_RECORD_COVERAGE_INVALID")
    if [row.get("time_year") for row in actual["regional_snapshots"]] != list(range(years + 1)):
        raise ValueError("REGIONAL_SNAPSHOT_COVERAGE_INVALID")
    if [row.get("step") for row in actual["unified_steps"]] != list(range(1, years + 1)):
        raise ValueError("UNIFIED_STEP_COVERAGE_INVALID")


def _compare_result(actual: dict, expected: dict, *, source: dict, configuration: dict,
                    complete_unified_steps: list[dict]) -> dict:
    actual_state = actual["state"]
    expected_state = expected["state"]
    compare_reference(_without_region_history(actual_state),
                      _without_region_history(expected_state), abs_tol=1e-8, rel_tol=2e-14)
    actual_unified = actual["subsurface_unified_result"]
    expected_unified = expected["subsurface_unified_result"]
    for key in ("initial", "final", "integrated_balances", "scope", "identity_semantics",
                "source_identity", "authority_and_limits"):
        if key != "integrated_balances":
            compare_reference(actual_unified[key], expected_unified[key],
                              abs_tol=1e-8, rel_tol=2e-14)
            continue
        actual_balances = json.loads(_canonical(actual_unified[key]))
        expected_balances = json.loads(_canonical(expected_unified[key]))
        actual_residuals = actual_balances["mechanical"].pop("per_step_residuals_j")
        expected_residuals = expected_balances["mechanical"].pop("per_step_residuals_j")
        derived_residuals = [row["mechanics"]["energy_balance_residual_j"]
                             for row in complete_unified_steps]
        compare_reference(derived_residuals, expected_residuals,
                          abs_tol=1e-8, rel_tol=2e-14)
        segment_steps = actual_unified["steps"]
        segment_residuals = [row["mechanics"]["energy_balance_residual_j"]
                             for row in segment_steps]
        compare_reference(actual_residuals, segment_residuals,
                          abs_tol=1e-8, rel_tol=2e-14)
        compare_reference(actual_balances, expected_balances,
                          abs_tol=1e-8, rel_tol=2e-14)
    actual_config = dict(actual_unified["configuration"])
    expected_config = dict(expected_unified["configuration"])
    actual_config.pop("segment_external_step_count", None)
    expected_config.pop("segment_external_step_count", None)
    compare_reference(actual_config, expected_config, abs_tol=1e-8, rel_tol=2e-14)
    compare_reference(actual["balances"], expected["balances"], abs_tol=1e-8, rel_tol=2e-14)

    expected_cp = expected["checkpoint"]
    actual_cp = verify_history_independent_checkpoint(
        actual["checkpoint"], source_identity=source, configuration=configuration)
    compare_reference(_without_region_history(expected_cp["regional_state"]),
                      _without_region_history(actual_cp["regional_state"]),
                      abs_tol=1e-8, rel_tol=2e-14)
    expected_unified_state = expected_cp["unified_checkpoint"]["state"]
    actual_unified_state = actual_cp["unified_checkpoint"]["state"]
    compare_reference(_without_unified_history(expected_unified_state),
                      _without_unified_history(actual_unified_state),
                      abs_tol=1e-8, rel_tol=2e-14)
    accumulator = _empty_history_accumulators(
        tuple(expected_unified["configuration"]["deep_initial_inventory_j_by_support"][support]
              for support in SUPPORTS))
    for row in expected_unified["steps"]:
        _accumulate_history_record(accumulator, row)
    compare_reference(accumulator, actual_unified_state["history_accumulators"],
                      abs_tol=1e-8, rel_tol=2e-14)
    return {"dynamic_regional_state": "PASS", "dynamic_unified_state": "PASS",
            "history_accumulators_against_full_records": "PASS"}


def _numpy_version() -> str:
    import numpy
    return str(numpy.__version__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-dir", required=True, type=Path)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--qualification-expected-commit",
        help="require exact clean measured-source provenance; failed runs still emit diagnostic evidence",
    )
    args = parser.parse_args()
    oracle_dir = args.oracle_dir.resolve(strict=True)
    input_dir = args.input_dir.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    if (output_dir.exists() or output_dir == REPOSITORY or REPOSITORY in output_dir.parents
            or output_dir == oracle_dir or oracle_dir in output_dir.parents
            or output_dir == input_dir or input_dir in output_dir.parents):
        parser.error("OUTPUT_MUST_BE_NEW_EXTERNAL_EVIDENCE_DIRECTORY")

    source_paths = (
        "scripts/r6_int10k_e2b2_history_independent.py",
        "src/arcana_worldsim/r6/int10k_history_independent.py",
        "src/arcana_worldsim/r6/int10k_source_provenance.py",
        "src/arcana_worldsim/r6/regional_geological_evolution.py",
        "src/arcana_worldsim/r6/unified_multiphysics_microdomain.py",
    )
    try:
        git_provenance = inspect_measured_sources_git(
            REPOSITORY, source_paths,
            expected_commit=args.qualification_expected_commit)
    except ValueError as exc:
        parser.error(str(exc))
    source_hashes_before = {
        name: _sha((REPOSITORY / name).read_bytes()) for name in source_paths}
    if not qualification_may_execute(git_provenance):
        output_dir.mkdir(parents=True, exist_ok=False)
        gate_report = {
            "schema": "INT10K_E2_B2_HISTORY_INDEPENDENT_REPORT_V1",
            "status": "BLOCKED_EXACT_SOURCE_PREFLIGHT",
            "classification": "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY",
            "evidence_scope": "DIAGNOSTIC_ONLY_EXACT_COMMIT_QUALIFICATION_REJECTED",
            "numerical_execution_performed": False,
            "implementation_source_commit": git_provenance["commit"],
            "implementation_expected_commit": git_provenance["expected_commit"],
            "implementation_source_sha256": source_hashes_before,
            "implementation_measured_sources_git_status": git_provenance["status"],
            "implementation_measured_sources_dirty_paths": git_provenance["dirty_paths"],
            "implementation_worktree_dirty_for_measured_sources": git_provenance["dirty"],
            "exact_commit_qualification": git_provenance,
            "world_history_production_authorized": False,
            "geodyn_2b_arcana_forward_authorized": False,
            "int10k_long_run_authorized": False,
        }
        report_bytes = _canonical(gate_report)
        _write_new(output_dir / "REPORT.json", report_bytes)
        manifest_bytes = _canonical({
            "schema": "INT10K_E2_B2_MANIFEST_V1",
            "completion": "EXACT_SOURCE_GATE_REJECTED_NO_NUMERICAL_EXECUTION",
            "classification": gate_report["classification"],
            "members": [{"path": "REPORT.json", "sha256": _sha(report_bytes),
                         "byte_length": len(report_bytes)}],
        })
        _write_new(output_dir / "MANIFEST.json", manifest_bytes)
        print(json.dumps({"status": gate_report["status"],
                          "output_dir": str(output_dir),
                          "manifest_sha256": _sha(manifest_bytes),
                          "exact_commit_qualification": git_provenance}, indent=2))
        return qualification_exit_code(git_provenance)

    oracle = _read_oracle(oracle_dir)
    oracle_manifest_bytes = (oracle_dir / "MANIFEST.json").read_bytes()
    oracle_manifest = json.loads(oracle_manifest_bytes.decode("utf-8"))
    years = oracle["configuration"]["years"]
    split = oracle["configuration"]["split_at"]
    if (years, split) not in {(3, 1), (10, 5)}:
        parser.error("REFERENCE_CONFIGURATION_NOT_SUPPORTED")
    source_before = verify_source_bundle(input_dir, SOURCE_HASHES)
    payloads, source_identity = load_verified_r6_initial_columns(input_dir)
    if source_identity != oracle["source_identity"] or set(payloads) != set(SUPPORTS):
        parser.error("E0_SOURCE_IDENTITY_OR_SUPPORT_MISMATCH")
    initial = {support: _state_from_payload(payloads[support]) for support in SUPPORTS}
    config = RegionalConfig(**oracle["configuration"]["regional_config"])
    history_configuration = {
        "regional_config": oracle["configuration"]["regional_config"],
        "unified_config": {
            # Constructed by the runner from RegionalConfig; this copy binds the
            # exact effective values and is obtained from a no-evolution setup
            # only through the same public config construction below.
        },
    }
    from dataclasses import asdict
    from arcana_worldsim.r6.unified_multiphysics_microdomain import UnifiedConfig
    effective_unified = UnifiedConfig(
        duration_years=float(config.duration_years), external_step_years=1.0,
        hydrology_dt_seconds=31_557_600.0, opening_rate_m_year=0.01,
        prescribed_uplift_total_m_by_support=(0.1, 0.0),
        precipitation_m_year_by_support=(0.0, 0.0),
        evapotranspiration_m_year_by_support=(0.0, 0.0),
        infiltration_capacity_m_year_by_support=(0.0, 0.0),
        substrate_erosion_enabled=False,
    )
    history_configuration["unified_config"] = asdict(effective_unified)

    rss_before, rss_method = _measure_rss_bytes()
    tracing_before = tracemalloc.is_tracing()
    if not tracing_before:
        tracemalloc.start()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()

    direct_history = HistoryCollector()
    direct = run_regional_segment(
        initial, source_identity, config=config, segment_years=years,
        history_independent_continuation=True, history_consumer=direct_history.emit)
    prefix_history = HistoryCollector()
    prefix = run_regional_segment(
        initial, source_identity, config=config, segment_years=split,
        history_independent_continuation=True, history_consumer=prefix_history.emit)
    split_checkpoint = prefix["checkpoint"]
    if split_checkpoint["time_year"] != split or "records" in split_checkpoint["regional_checkpoint"]["regional_state"]:
        raise ValueError("SPLIT_FRONTIER_CONTAINS_HISTORY_OR_WRONG_TIME")

    # The resumed process receives only the typed checkpoint and original
    # immutable initialization identities. The prefix collector is not passed.
    resumed_history = HistoryCollector(regional_start_year=split,
                                       unified_start_step=split,
                                       include_initial_snapshot=False)
    resumed = run_regional_segment(
        initial, source_identity, config=config, segment_years=years - split,
        checkpoint=split_checkpoint, history_independent_continuation=True,
        history_consumer=resumed_history.emit)
    direct_events = direct_history.export()
    prefix_events = prefix_history.export()
    resumed_events = resumed_history.export()
    split_history = _joined(prefix_events, resumed_events)
    if direct_events != split_history:
        compare_reference(direct_events, split_history, abs_tol=1e-8, rel_tol=2e-14)
    _assert_history(direct_events, oracle["cases"]["direct"], years=years)
    _assert_history(split_history, oracle["cases"]["split_resumed"], years=years)
    direct_result_comparison = _compare_result(
        direct, oracle["cases"]["direct"], source=source_identity,
        configuration=history_configuration,
        complete_unified_steps=direct_events["unified_steps"])
    prefix_result_comparison = _compare_result(
        prefix, oracle["cases"]["split_prefix"], source=source_identity,
        configuration=history_configuration,
        complete_unified_steps=prefix_events["unified_steps"])
    _assert_history(prefix_events, oracle["cases"]["split_prefix"], years=split)
    compare_reference(direct["state"]["routing_events"],
                      oracle["cases"]["direct"]["state"]["routing_events"],
                      abs_tol=0.0, rel_tol=0.0)
    compare_reference(direct["state"]["initial_condition_events"],
                      oracle["cases"]["direct"]["state"]["initial_condition_events"],
                      abs_tol=0.0, rel_tol=0.0)
    compare_reference(prefix["state"]["routing_events"] + resumed["state"]["routing_events"],
                      oracle["cases"]["split_resumed"]["state"]["routing_events"],
                      abs_tol=0.0, rel_tol=0.0)
    compare_reference(prefix["state"]["initial_condition_events"],
                      oracle["cases"]["split_resumed"]["state"]["initial_condition_events"],
                      abs_tol=0.0, rel_tol=0.0)
    split_result_comparison = _compare_result(
        resumed, oracle["cases"]["split_resumed"], source=source_identity,
        configuration=history_configuration,
        complete_unified_steps=split_history["unified_steps"])

    reader = HistoryReader(direct_events)
    for year in range(years + 1):
        snapshot = reader.regional_snapshot(year)
        cell_id = snapshot["cells"][0]["cell_id"]
        compare_reference(reader.regional_materials(year, cell_id)[0], {
            "time_year": year, "cell_id": cell_id,
            "substrate": snapshot["cells"][0]["substrate"],
            "mobile_kg_by_material": snapshot["cells"][0]["mobile_kg_by_material"],
            "suspended_kg_by_material": snapshot["cells"][0]["suspended_kg_by_material"],
            "deposits": snapshot["cells"][0]["deposits"],
        }, abs_tol=0.0, rel_tol=0.0)
    for year in range(1, years + 1):
        reader.regional_record(year)
        reader.unified_step(year)
        first_volume = next(iter(direct_events["unified_steps"][year - 1]["deep"]
                                 ["inventory_j_by_material_volume"]))
        reader.deep_inventory(year, first_volume)
    for query in (lambda: reader.regional_record(years + 1),
                  lambda: reader.regional_snapshot(years + 1),
                  lambda: reader.unified_step(years + 1)):
        try:
            query()
        except HistoryContinuationError as exc:
            if str(exc) != "TIME_NOT_ARCHIVED":
                raise
        else:
            raise ValueError("HISTORY_QUERY_INVENTED_MISSING_TIME")
    history_direct_bytes = _canonical(direct_events)
    history_split_bytes = _canonical(split_history)
    checkpoint_data = {
        "direct_final": direct["checkpoint"],
        "split_boundary": split_checkpoint,
        "split_final": resumed["checkpoint"],
    }
    checkpoint_bytes = {name: _canonical(value) for name, value in checkpoint_data.items()}
    wall_seconds = time.perf_counter() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    _, heap_peak = tracemalloc.get_traced_memory()
    rss_after, _ = _measure_rss_bytes()
    if not tracing_before:
        tracemalloc.stop()
    if verify_source_bundle(input_dir, SOURCE_HASHES) != source_before:
        raise ValueError("E0_INPUTS_CHANGED_DURING_QUALIFICATION")

    output_dir.mkdir(parents=True, exist_ok=False)
    members = []
    payloads_out = {
        "HISTORY_DIRECT.json": history_direct_bytes,
        "HISTORY_SPLIT_JOINED.json": history_split_bytes,
        "CHECKPOINTS.json": _canonical(checkpoint_data),
    }
    measurements = {
        "years": years, "split_at": split,
        "frontier_bytes": {
            "split_boundary": len(checkpoint_bytes["split_boundary"]),
            "split_final": len(checkpoint_bytes["split_final"]),
            "direct_final": len(checkpoint_bytes["direct_final"]),
        },
        "history_bytes": {"direct": len(history_direct_bytes),
                          "split_joined": len(history_split_bytes)},
        "records": {key: len(value) for key, value in direct_events.items()},
        "wall_seconds": wall_seconds, "process_cpu_seconds": cpu_seconds,
        "tracemalloc_peak_python_bytes": heap_peak,
        "rss_bytes": {"before": rss_before, "after": rss_after,
                      "method": rss_method,
                      "sampling": "PHASE_BOUNDARY_ONLY_NOT_CONTINUOUS_PEAK"},
    }
    for name, data in payloads_out.items():
        _write_new(output_dir / name, data)
        members.append({"path": name, "sha256": _sha(data), "byte_length": len(data)})
    report = {
        "schema": "INT10K_E2_B2_HISTORY_INDEPENDENT_REPORT_V1",
        "status": "PASS_LOCAL_HISTORY_INDEPENDENT_CONTINUATION_PARITY",
        "classification": "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY",
        "source_identity": source_identity,
        "configuration_sha256": hashlib.sha256(_canonical(history_configuration)).hexdigest(),
        "oracle_run_id": oracle["run_id"],
        "oracle_sha256": oracle["integrity"]["canonical_body_sha256"],
        "oracle_bundle_manifest_sha256": _sha(oracle_manifest_bytes),
        "oracle_bundle_members": oracle_manifest["members"],
        "oracle_origin": str(oracle_dir),
        "e0_hashes_rechecked_before_after": source_before,
        "history_prefix_passed_to_resume": False,
        "legacy_oracle_parity": "PASS_ALL_RECORDS_STATES_BALANCES_EVENTS_AND_QUERYABLE_ROWS",
        "direct_vs_split_history_equality": "PASS_EXACT",
        "checkpoint_comparison": {"direct": direct_result_comparison,
                                   "split_prefix": prefix_result_comparison,
                                   "split": split_result_comparison,
                                   "split_boundary_frontier": "PASS_VERIFIED_AND_HISTORY_FREE"},
        "accumulator_parity": "PASS_AGAINST_REDUCED_FULL_HISTORY_IN_ORDER",
        "query_contract": "PASS_EXACT_TIME_CELL_MATERIAL_AND_DEEP_LOOKUPS; MISSING_TIME_FAILS",
        "resource_limits_enforced": False,
        "telemetry": measurements,
        "limitations": [
            "Collector is lossless but in-memory; transactional append-only history is not implemented.",
            "Runner results retain the records generated in the current invocation for API compatibility; the resumed frontier does not require prior records.",
            "RSS is sampled at phase boundaries, not a continuous process-tree peak.",
            "Measured time is a short local synthetic engineering run, not a long-run projection.",
            "No scientific or canonical authority is inferred.",
        ],
        "world_history_production_authorized": False,
        "geodyn_2b_arcana_forward_authorized": False,
        "int10k_long_run_authorized": False,
        "runtime": {"python": sys.version, "numpy": _numpy_version(),
                    "platform": platform.platform(), "pid": os.getpid()},
    }
    source_hashes_after = {
        name: _sha((REPOSITORY / name).read_bytes()) for name in source_paths}
    sources_unchanged = source_hashes_before == source_hashes_after
    report["implementation_source_commit"] = git_provenance["commit"]
    report["implementation_expected_commit"] = git_provenance["expected_commit"]
    report["implementation_source_sha256"] = source_hashes_after
    report["implementation_source_sha256_at_start"] = source_hashes_before
    report["implementation_measured_sources_git_status"] = git_provenance["status"]
    report["implementation_measured_sources_dirty_paths"] = git_provenance["dirty_paths"]
    report["implementation_worktree_dirty_for_measured_sources"] = git_provenance["dirty"]
    report["implementation_measured_sources_unchanged_during_run"] = sources_unchanged
    qualification = dict(git_provenance)
    if not sources_unchanged and qualification["expected_commit"] is not None:
        qualification["qualification_status"] = "FAIL"
        qualification["qualification_reasons"] = [
            *qualification["qualification_reasons"], "MEASURED_SOURCE_CHANGED_DURING_RUN"]
    report["exact_commit_qualification"] = qualification
    if qualification["expected_commit"] is not None and qualification["qualification_status"] != "PASS":
        report["evidence_scope"] = "DIAGNOSTIC_ONLY_EXACT_COMMIT_QUALIFICATION_REJECTED"
    else:
        report["evidence_scope"] = "LOCAL_PARITY_DIAGNOSTIC"
    report_bytes = _canonical(report)
    _write_new(output_dir / "REPORT.json", report_bytes)
    members.append({"path": "REPORT.json", "sha256": _sha(report_bytes),
                    "byte_length": len(report_bytes)})
    manifest = {"schema": "INT10K_E2_B2_MANIFEST_V1",
                "completion": "LOCAL_PARITY_AND_INTEGRITY_PASSED",
                "classification": report["classification"], "members": members}
    manifest_bytes = _canonical(manifest)
    _write_new(output_dir / "MANIFEST.json", manifest_bytes)
    print(json.dumps({"status": report["status"], "output_dir": str(output_dir),
                      "manifest_sha256": _sha(manifest_bytes), "measurements": measurements,
                      "exact_commit_qualification": qualification}, indent=2))
    return qualification_exit_code(qualification)


if __name__ == "__main__":
    raise SystemExit(main())
