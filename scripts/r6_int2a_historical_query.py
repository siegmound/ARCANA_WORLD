#!/usr/bin/env python3
"""Verified, read-only historical queries over the R4 and INT-1D bundles.

This is an offline engineering-evidence reader. It never imports an evolution
kernel, writes HistoryStore, or creates a physical state.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from r6_int1a_retention_audit import (
    ARRAY_FIELDS,
    EXPECTED_MANIFEST_SHA256 as R4_MANIFEST_SHA256,
    EXPECTED_SOURCE_COMMIT as R4_SOURCE_COMMIT,
    EXPECTED_SOURCE_IDENTITY as R4_SOURCE_IDENTITY,
    SCALAR_FIELDS,
    UNITS,
    AuditError,
    _absolute_checked,
    _difference_metrics,
    _finite_number,
    _interp,
    _json_bytes,
    _read_json_snapshot,
    _retained_document,
    _sample_error,
    _sha256,
    _validate_samples,
    analyze_samples,
    load_verified_bundle,
    validate_r4_provenance,
)


INT1D_MANIFEST_SHA256 = "0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571"
INT1D_RUN_SHA256 = "603c4e36c7f25d29df300bedb5496bd8ecfb5fa471fb07c29a41af096e3a469b"
INT1D_SOURCE_COMMIT = "3fa149b7639f59c934a4d722acb388eacc4c9628"
INT1D_SOURCE_IDENTITY = "a1a4503fe57206750884e454d8a12d778caee38e34b35586805241ad51c01954"
INT1D_BOUNDARY = "R6BND-T0-27e4d497530e681071fb"
INT1D_SUPPORTS = ["R6G1D-R094-C026", "R6G1D-R094-C025"]
INT1D_PROVIDERS = {
    "event_census": "e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e",
    "kinematics_artifact": "0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2",
    "kinematics_semantic": "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4",
    "mapping": "b8d57495bc6e196a0b9fe7afd466079bebd97d0f63baafe232f215e45897a09f",
    "source_set": INT1D_SOURCE_IDENTITY,
    "support_binding_index": "aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00",
    "thermal_field_package": "39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e",
    "vector_partition": "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab",
}
INT1D_MEMBERS = {
    "CANDIDATE_CHECKPOINT.json": (84879, "b3da8fa3053620bdcea5dba9f5614a274327d7d82cd876a653c18f8198a93cb7"),
    "CANDIDATE_TRAJECTORY.json": (217802, "0a09459471dcb9f85f205497dfa9bcff74d17ccb69cdcb5df0cfe1b1ad7436d6"),
    "DIAGNOSTIC_NUMERICAL_SAMPLES.json": (157705, "540c668b7e0e186e7c0efe36e5fc94d1afe09550a2f5b235ef3485e8b77b1916"),
    "EDGE_AUDIT_MATRIX.json": (98359, "5bbf524d40c7560533640a61f1a9be27a2b4b3f677b49e41f39f6f77c46ec46a"),
    "REPLAY_RESTART.json": (926, "3f7d4dfe2466c6eeca306c3aa51c523fb9510bbcca3be3464a94941018339f84"),
    "SELECTED_SECTION_AND_PROFILES.json": (50059, "4e9c23e0451063461d2648c3aa407a91f8206e61823e46691fb540202fa4fa91"),
    "THERMAL_CONVERGENCE.json": (200193, "8ee8b2c19946a798270e59a3420a1b8507d5c08b5eaf8a7def6fbdc78cee07a0"),
    "RUN_RESULT.json": (8901, INT1D_RUN_SHA256),
}
INT1D_DIRNAME = "INT1D_TF2B_5_11_R094C025_C026_20261014_02"
FIELD_ALLOWLIST = frozenset((*SCALAR_FIELDS, "temperature_k", "z_m", "material_coordinate"))
RECONSTRUCTABLE_FIELDS = frozenset((*SCALAR_FIELDS, "temperature_k", "z_m"))
MODES = frozenset({"EXACT_OBSERVED", "BRACKET", "DIAGNOSTIC_RECONSTRUCTION"})


def _verify_int1d_bundle(root: Path) -> tuple[dict[str, Any], dict[str, int], dict[str, str], dict[str, bytes]]:
    root = _absolute_checked(root, must_exist=True)
    if root.name != INT1D_DIRNAME or not root.is_dir():
        raise AuditError("UNEXPECTED_INT1D_SOURCE_DIRECTORY")
    manifest_raw, manifest = _read_json_snapshot(root / "CANDIDATE_MANIFEST.json")
    if _sha256(manifest_raw) != INT1D_MANIFEST_SHA256:
        raise AuditError("INT1D_MANIFEST_SHA256_MISMATCH")
    expected_names = set(INT1D_MEMBERS) | {"CANDIDATE_MANIFEST.json"}
    entries = list(root.iterdir())
    if {p.name for p in entries} != expected_names or any(not p.is_file() or p.is_symlink() for p in entries):
        raise AuditError("INT1D_BUNDLE_MEMBERSHIP_MISMATCH")
    if (manifest.get("schema") != "ARCANA_R6_TF2B_INT0_OUTPUT_MANIFEST_V1"
            or manifest.get("canonical_publication") is not False
            or manifest.get("RUN_RESULT.json") != {"bytes": INT1D_MEMBERS["RUN_RESULT.json"][0],
                                                    "sha256": INT1D_RUN_SHA256}
            or set(manifest.get("files", {})) != set(INT1D_MEMBERS) - {"RUN_RESULT.json"}
            or manifest.get("provider_identities") != INT1D_PROVIDERS):
        raise AuditError("INT1D_MANIFEST_CONTRACT_MISMATCH")
    docs: dict[str, Any] = {"CANDIDATE_MANIFEST.json": manifest}
    sizes = {"CANDIDATE_MANIFEST.json": len(manifest_raw)}
    hashes = {"CANDIDATE_MANIFEST.json": _sha256(manifest_raw)}
    snapshots = {"CANDIDATE_MANIFEST.json": manifest_raw}
    for name, (size, digest) in INT1D_MEMBERS.items():
        entry = manifest["RUN_RESULT.json"] if name == "RUN_RESULT.json" else manifest["files"].get(name)
        if entry != {"bytes": size, "sha256": digest}:
            raise AuditError(f"INT1D_MANIFEST_MEMBER_IDENTITY_MISMATCH:{name}")
        raw, parsed = _read_json_snapshot(root / name)
        if len(raw) != size or _sha256(raw) != digest:
            raise AuditError(f"INT1D_MEMBER_INTEGRITY_MISMATCH:{name}")
        docs[name], sizes[name], hashes[name], snapshots[name] = parsed, len(raw), _sha256(raw), raw
    _validate_int1d_provenance(docs)
    return docs, sizes, hashes, snapshots


def _validate_int1d_provenance(docs: dict[str, Any]) -> None:
    manifest, run = docs["CANDIDATE_MANIFEST.json"], docs["RUN_RESULT.json"]
    trajectory, samples = docs["CANDIDATE_TRAJECTORY.json"], docs["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]
    if (run.get("decision") != "CONTINENTAL_ENGINEERING_SLICE_PASS"
            or run.get("checkpoint_commit") != INT1D_SOURCE_COMMIT
            or run.get("selected_support_ids") != INT1D_SUPPORTS
            or run.get("selected_boundary_id") != INT1D_BOUNDARY
            or run.get("requested_boundary_id") != INT1D_BOUNDARY
            or run.get("preserved_non_actions", {}).get("canonical_publication") is not False
            or run.get("preserved_non_actions", {}).get("world_history_accessed") is not False
            or run.get("preserved_non_actions", {}).get("world_history_mutated") is not False):
        raise AuditError("INT1D_RUN_PROVENANCE_MISMATCH")
    expected_artifacts = {name: entry["sha256"] for name, entry in manifest.get("files", {}).items()}
    if (run.get("artifact_sha256") != expected_artifacts
            or trajectory.get("configuration_sha256") != manifest.get("configuration_sha256")):
        raise AuditError("INT1D_RUN_MANIFEST_CROSS_BINDING_MISMATCH")
    source = trajectory.get("source_code", {})
    if (source.get("commit") != INT1D_SOURCE_COMMIT
            or source.get("source_identity_sha256") != INT1D_SOURCE_IDENTITY
            or trajectory.get("providers") != INT1D_PROVIDERS
            or manifest.get("provider_identities") != INT1D_PROVIDERS
            or trajectory.get("boundary_id") != INT1D_BOUNDARY
            or trajectory.get("b0_replay_status") != "DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE"
            or trajectory.get("canonical_publication") is not False
            or trajectory.get("world_history_accessed") is not False
            or trajectory.get("world_history_mutated") is not False):
        raise AuditError("INT1D_TRAJECTORY_PROVENANCE_MISMATCH")
    if (samples.get("canonical_publication") is not False
            or samples.get("interpolation") != "NONE"
            or samples.get("selected_boundary_id") != INT1D_BOUNDARY
            or samples.get("requested_boundary_id") != INT1D_BOUNDARY
            or samples.get("support_ids") != INT1D_SUPPORTS
            or samples.get("resolution_fraction") != 0.000125):
        raise AuditError("INT1D_SAMPLE_IDENTITY_MISMATCH")
    checkpoint = docs["CANDIDATE_CHECKPOINT.json"]
    convergence = docs["THERMAL_CONVERGENCE.json"]
    replay = docs["REPLAY_RESTART.json"]
    if replay != run.get("replay_restart") or replay.get("restart_pass") is not True:
        raise AuditError("INT1D_REPLAY_BINDING_MISMATCH")
    if (checkpoint.get("canonical_publication") is not False or checkpoint.get("elapsed_years") != 1000.0
            or convergence.get("comparison_is_numerical_refinement_only") is not True):
        raise AuditError("INT1D_CHECKPOINT_OR_REFINEMENT_SCOPE_MISMATCH")
    rows_by_support = _validate_samples(samples)
    if set(rows_by_support) != set(INT1D_SUPPORTS):
        raise AuditError("INT1D_SAMPLE_SUPPORTS_MISMATCH")
    fields = {row["support_id"]: row for row in trajectory.get("fields", [])}
    initial_states, candidate_states = checkpoint.get("initial_states"), checkpoint.get("candidate_states")
    if set(fields) != set(INT1D_SUPPORTS) or not isinstance(initial_states, list) or not isinstance(candidate_states, list):
        raise AuditError("INT1D_ENDPOINT_STATE_BINDING_MISSING")
    if len(initial_states) != 2 or len(candidate_states) != 2:
        raise AuditError("INT1D_CHECKPOINT_CARDINALITY_MISMATCH")
    diagnostic_rung = next((item for item in convergence.get("resolution_results", [])
                            if item.get("maximum_kinematic_fraction_per_substep") == 0.000125), None)
    checkpoint_rung = next((item for item in convergence.get("resolution_results", [])
                            if item.get("maximum_kinematic_fraction_per_substep") == 0.0005), None)
    if (diagnostic_rung is None or checkpoint_rung is None
            or len(diagnostic_rung.get("final_states", [])) != 2
            or len(checkpoint_rung.get("final_states", [])) != 2):
        raise AuditError("INT1D_RESOLUTION_ENDPOINT_BINDING_MISSING")
    state_keys = ("width_m", "crust_m", "lithosphere_m", "beta", "accumulated_strain",
                  "material_coordinate", "temperature_k", "z_m")
    for index, support in enumerate(INT1D_SUPPORTS):
        rows = rows_by_support[support]
        field = fields[support]
        for key in state_keys:
            if (rows[0].get(key) != field.get("initial", {}).get(key)
                    or initial_states[index].get(key) != field["initial"].get(key)
                    or candidate_states[index].get(key) != field["candidate"].get(key)
                    or field["candidate"].get(key) != checkpoint_rung["final_states"][index].get(key)
                    or rows[-1].get(key) != diagnostic_rung["final_states"][index].get(key)):
                raise AuditError(f"INT1D_ENDPOINT_RECONCILIATION_FAILED:{support}:{key}")


def load_sources(r4_root: Path, int1d_root: Path) -> dict[str, dict[str, Any]]:
    r4_root = _absolute_checked(r4_root, must_exist=True)
    int1d_root = _absolute_checked(int1d_root, must_exist=True)
    if r4_root == int1d_root or r4_root in int1d_root.parents or int1d_root in r4_root.parents:
        raise AuditError("INPUT_BUNDLE_PATH_OVERLAP")
    r4_docs, r4_sizes, r4_hashes, r4_snapshots = load_verified_bundle(r4_root)
    validate_r4_provenance(r4_docs)
    int1d_docs, int1d_sizes, int1d_hashes, int1d_snapshots = _verify_int1d_bundle(int1d_root)
    if _json_bytes(r4_docs["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]) != r4_snapshots["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]:
        raise AuditError("R4_SAMPLE_SERIALIZATION_NOT_CANONICAL")
    if _json_bytes(int1d_docs["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]) != int1d_snapshots["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]:
        raise AuditError("INT1D_SAMPLE_SERIALIZATION_NOT_CANONICAL")
    return {
        "R4": _source_record("R4", r4_root, r4_docs, r4_sizes, r4_hashes,
                              R4_SOURCE_COMMIT, R4_SOURCE_IDENTITY),
        "INT1D": _source_record("INT-1D", int1d_root, int1d_docs, int1d_sizes, int1d_hashes,
                                INT1D_SOURCE_COMMIT, INT1D_SOURCE_IDENTITY),
    }


def _source_record(experiment: str, root: Path, docs: dict[str, Any], sizes: dict[str, int],
                   hashes: dict[str, str], commit: str, source_identity: str) -> dict[str, Any]:
    samples = docs["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]
    rows = _validate_samples(samples)
    trajectory = docs["CANDIDATE_TRAJECTORY.json"]
    return {"experiment": experiment, "root": root, "documents": docs, "rows": rows,
            "manifest_sha256": hashes["CANDIDATE_MANIFEST.json"],
            "run_result_sha256": hashes["RUN_RESULT.json"], "source_commit": commit,
            "source_identity_sha256": source_identity,
            "boundary_id": trajectory["boundary_id"], "resolution_fraction": samples["resolution_fraction"],
            "sampling": samples["sampling"], "sample_artifact_bytes": sizes["DIAGNOSTIC_NUMERICAL_SAMPLES.json"],
            "sample_artifact_sha256": hashes["DIAGNOSTIC_NUMERICAL_SAMPLES.json"],
            "supports": list(samples["support_ids"]), "canonical_publication": False}


def _validated_time(value: Any) -> float:
    number = _finite_number(value, "requested_elapsed_years")
    if number < 0.0:
        raise AuditError("QUERY_TIME_OUT_OF_RANGE")
    return number


def _value_at(row: dict[str, Any], field: str) -> Any:
    if field not in FIELD_ALLOWLIST:
        raise AuditError(f"UNSUPPORTED_NUMERIC_FIELD:{field}")
    if field == "material_coordinate":
        return list(row[field])
    value = row[field]
    return list(value) if isinstance(value, list) else value


def _base_provenance(source: dict[str, Any], support: str, field: str, mode: str) -> dict[str, Any]:
    if support not in source["rows"]:
        raise AuditError(f"UNKNOWN_SUPPORT:{support}")
    if field not in FIELD_ALLOWLIST:
        raise AuditError(f"UNSUPPORTED_NUMERIC_FIELD:{field}")
    return {"source_experiment": source["experiment"], "source_commit": source["source_commit"],
            "source_identity_sha256": source["source_identity_sha256"],
            "source_manifest_sha256": source["manifest_sha256"],
            "source_run_result_sha256": source["run_result_sha256"],
            "source_sample_artifact_sha256": source["sample_artifact_sha256"],
            "boundary_id": source["boundary_id"], "support_id": support,
            "field": field, "units": UNITS.get(field, "1"), "retrieval_mode": mode,
            "resolution_fraction": source["resolution_fraction"], "sampling": source["sampling"],
            "scientific_authority": "UNKNOWN_NOT_QUALIFIED_ENGINEERING_EVIDENCE_ONLY",
            "canonical_state": False}


def query(source: dict[str, Any], *, support_id: str, elapsed_years: Any,
          field: str, mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise AuditError(f"UNSUPPORTED_RETRIEVAL_MODE:{mode}")
    time = _validated_time(elapsed_years)
    rows = source["rows"].get(support_id)
    if rows is None:
        raise AuditError(f"UNKNOWN_SUPPORT:{support_id}")
    if field not in FIELD_ALLOWLIST:
        raise AuditError(f"UNSUPPORTED_NUMERIC_FIELD:{field}")
    times = [row["elapsed_years"] for row in rows]
    if time < times[0] or time > times[-1]:
        raise AuditError("QUERY_TIME_OUT_OF_RANGE")
    provenance = _base_provenance(source, support_id, field, mode)
    if mode == "EXACT_OBSERVED":
        matches = [i for i, observed_time in enumerate(times) if time == observed_time]
        if not matches:
            raise AuditError("EXACT_OBSERVATION_NOT_FOUND")
        index = matches[0]
        row = rows[index]
        return {**provenance, "status": "OBSERVED", "observed": True,
                "elapsed_years": time, "sample_index_0based": index,
                "record_type": row["record_type"], "value": _value_at(row, field),
                "material_coordinate": list(row["material_coordinate"]) if field in ARRAY_FIELDS else None}
    if mode == "BRACKET":
        pair = next(((i, i + 1) for i in range(len(times) - 1) if times[i] < time < times[i + 1]), None)
        if pair is None:
            if time in times:
                raise AuditError("TIME_IS_OBSERVED_USE_EXACT_OBSERVED")
            raise AuditError("STRICT_BRACKET_NOT_FOUND")
        left_i, right_i = pair
        return {**provenance, "status": "OBSERVED_BRACKET", "observed": True,
                "elapsed_years": time, "left": {"sample_index_0based": left_i,
                    "elapsed_years": times[left_i], "record_type": rows[left_i]["record_type"],
                    "value": _value_at(rows[left_i], field)},
                "right": {"sample_index_0based": right_i,
                    "elapsed_years": times[right_i], "record_type": rows[right_i]["record_type"],
                    "value": _value_at(rows[right_i], field)},
                "material_coordinate": list(rows[left_i]["material_coordinate"]) if field in ARRAY_FIELDS else None}
    if field not in RECONSTRUCTABLE_FIELDS:
        raise AuditError(f"FIELD_NOT_RECONSTRUCTABLE:{field}")
    pair = next(((i, i + 1) for i in range(len(times) - 1) if times[i] < time < times[i + 1]), None)
    if pair is None:
        raise AuditError("DIAGNOSTIC_RECONSTRUCTION_REQUIRES_INTERIOR_TIME")
    li, ri = pair
    if field in ARRAY_FIELDS and rows[li]["material_coordinate"] != rows[ri]["material_coordinate"]:
        raise AuditError("MATERIAL_COORDINATE_SUPPORT_MISMATCH")
    # Reuse the INT-1A interpolation operation. Only same-index temporal values
    # are interpolated; no spatial remapping or categorical interpolation occurs.
    left, right = rows[li][field], rows[ri][field]
    if field in SCALAR_FIELDS:
        reconstructed = [_interp(time, times[li], times[ri], left, right)]
    else:
        if len(left) != len(right):
            raise AuditError("PROFILE_CARDINALITY_MISMATCH")
        reconstructed = [_interp(time, times[li], times[ri], a, b) for a, b in zip(left, right)]
    return {**provenance, "status": "DIAGNOSTIC_RECONSTRUCTION", "observed": False,
            "elapsed_years": time, "interpolation_method": "PIECEWISE_LINEAR_TIME",
            "bracket": {"left_index_0based": li, "left_elapsed_years": times[li],
                        "right_index_0based": ri, "right_elapsed_years": times[ri]},
            "value": reconstructed[0] if field in SCALAR_FIELDS else reconstructed,
            "material_coordinate": list(rows[li]["material_coordinate"]) if field in ARRAY_FIELDS else None,
            "limitations": ["APPROXIMATE_DIAGNOSTIC_ONLY", "NOT_PHYSICALLY_SIMULATED",
                            "NOT_CANONICAL", "NO_INTEGRATION_CONVERGENCE_CLAIM"]}


def inspect_interval(source: dict[str, Any], *, support_id: str, start_years: Any,
                     end_years: Any) -> dict[str, Any]:
    start, end = _validated_time(start_years), _validated_time(end_years)
    if end < start:
        raise AuditError("INSPECTION_INTERVAL_REVERSED")
    rows = source["rows"].get(support_id)
    if rows is None:
        raise AuditError(f"UNKNOWN_SUPPORT:{support_id}")
    selected = [{"sample_index_0based": i, "elapsed_years": row["elapsed_years"],
                 "record_type": row["record_type"], "fields": {
                     field: _value_at(row, field) for field in sorted(FIELD_ALLOWLIST)
                 }} for i, row in enumerate(rows) if start <= row["elapsed_years"] <= end]
    return {"source_experiment": source["experiment"], "source_commit": source["source_commit"],
            "source_identity_sha256": source["source_identity_sha256"],
            "source_manifest_sha256": source["manifest_sha256"],
            "source_sample_artifact_sha256": source["sample_artifact_sha256"],
            "boundary_id": source["boundary_id"], "resolution_fraction": source["resolution_fraction"],
            "sampling": source["sampling"], "field_units": {field: UNITS.get(field, "1")
                                                                  for field in FIELD_ALLOWLIST},
            "support_id": support_id, "interval_years": [start, end], "status": "OBSERVED_TEMPORAL_INSPECTION",
            "observations": selected, "physical_computation_performed": False}


def physical_refinement_request(source: dict[str, Any], *, support_id: str,
                                requested_years: Any) -> dict[str, Any]:
    time = _validated_time(requested_years)
    if support_id not in source["rows"]:
        raise AuditError(f"UNKNOWN_SUPPORT:{support_id}")
    return {"source_experiment": source["experiment"], "source_commit": source["source_commit"],
            "source_identity_sha256": source["source_identity_sha256"],
            "source_manifest_sha256": source["manifest_sha256"],
            "source_sample_artifact_sha256": source["sample_artifact_sha256"],
            "boundary_id": source["boundary_id"], "support_id": support_id, "requested_elapsed_years": time,
            "requested_operation": "ADDITIONAL_PHYSICAL_STEPS_OR_FINER_SPATIAL_RESOLUTION",
            "resolution_or_step_size": "UNKNOWN_NOT_SELECTED", "status": "PHYSICAL_REFINEMENT_NOT_EXECUTED",
            "missing_dependencies": ["AUTHORIZED_EXECUTABLE_KERNEL_BINDING", "BOUND_INPUT_AND_STATE_PROVENANCE",
                                     "APPROVED_PHYSICAL_CONFIGURATION", "NUMERICAL_ACCEPTANCE_AUTHORITY",
                                     "SEPARATE_EXECUTION_AUTHORIZATION"],
            "physical_computation_performed": False}


def _retention_summary(source: dict[str, Any], strategy_name: str,
                       retained: tuple[int, ...], metrics: dict[str, Any]) -> dict[str, Any]:
    document = source["documents"]["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]
    count = len(next(iter(source["rows"].values())))
    omitted = [i for i in range(count) if i not in retained]
    strategy = {"strategy": strategy_name, "retained_indices_0based": list(retained)}
    if len(retained) == count:
        serialized_size = source["sample_artifact_bytes"]
    else:
        subset = _retained_document(document, {"retained_indices_0based": list(retained)})
        serialized_size = len(_json_bytes(subset))
    support_results = {}
    for support in source["supports"]:
        rows = source["rows"][support]
        fields = {}
        for field in (*SCALAR_FIELDS, *ARRAY_FIELDS):
            errors = [_sample_error(rows, retained, i, field) for i in omitted]
            # INT-1A strategy metrics are the established numerical evaluator;
            # repeat only its public aggregate field result for this chosen subset.
            stored = next((s for s in metrics["strategies"]
                           if tuple(s["retained_indices_0based"]) == retained), None)
            metric = (stored["support_errors"][support]["recorded_fields"][field]["combined_omitted_state_metrics"]
                      if stored else _difference_metrics([], []))
            fields[field] = {"omitted_sample_count": len(omitted),
                             "max_abs_error": metric["max_abs_error"], "rmse": metric["rmse"],
                             "per_omitted_sample": errors}
        support_results[support] = fields
    times = metrics["sample_times_years"]
    return {"strategy": strategy_name, "retained_indices_0based": list(retained),
            "retained_times_years": [times[i] for i in retained], "omitted_times_years": [times[i] for i in omitted],
            "exact_answerable_count": len(retained), "observed_sample_count": count,
            "omitted_sample_count": len(omitted),
            "bracket_answerable_omitted_count": len(omitted) if len(retained) >= 2 else 0,
            "reconstruction_answerable_omitted_count": len(omitted) if len(retained) >= 2 else 0,
            "sample_json_bytes": serialized_size, "support_errors": support_results,
            "retrospective": strategy_name.startswith("RETROSPECTIVE"),
            "causal_online_policy_qualified": False}


def analyze_retention(source: dict[str, Any]) -> dict[str, Any]:
    doc = source["documents"]["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]
    samples = analyze_samples(doc, source["sample_artifact_bytes"])
    count = samples["sample_count_per_support"]
    middle = (count - 1) // 2
    if count < 3:
        raise AuditError("RETENTION_SAMPLE_COUNT_TOO_SMALL")
    fixed_one = tuple(sorted({0, middle, count - 1}))
    fixed_two = tuple(sorted({0, max(1, count // 3), min(count - 2, (2 * count) // 3), count - 1}))
    retrospective = next(tuple(item["retained_indices_0based"]) for item in samples["strategies"]
                         if item.get("adaptive") is True)
    strategies = [("FULL_OBSERVED", tuple(range(count))),
                  ("ENDPOINT_ONLY", (0, count - 1)),
                  ("FIXED_ONE_INTERIOR", fixed_one),
                  ("FIXED_TWO_INTERIOR", fixed_two)]
    strategies.append(("RETROSPECTIVE_ADAPTIVE", retrospective))
    return {"sample_times_years": samples["sample_times_years"],
            "full_sample_artifact_bytes": source["sample_artifact_bytes"],
            "strategies": [_retention_summary(source, name, retained, samples)
                           for name, retained in strategies],
            "support_series_identical_within_experiment": _support_rows_equivalent(source)}


def _support_rows_equivalent(source: dict[str, Any]) -> bool:
    supports = source["supports"]
    if len(supports) < 2:
        return True
    baseline = source["rows"][supports[0]]
    fields = (*SCALAR_FIELDS, *ARRAY_FIELDS, "elapsed_years", "time_s", "material_coordinate")
    return all(len(source["rows"][support]) == len(baseline) and all(
        all(row.get(field) == baseline[i].get(field) for field in fields)
        for i, row in enumerate(source["rows"][support])) for support in supports[1:])


def build_analysis(r4_root: Path, int1d_root: Path) -> dict[str, Any]:
    sources = load_sources(r4_root, int1d_root)
    examples = {
        "r4_exact_width_at_zero": query(sources["R4"], support_id=sources["R4"]["supports"][0],
                                         elapsed_years=0.0, field="width_m", mode="EXACT_OBSERVED"),
        "int1d_bracket_temperature": query(sources["INT1D"], support_id=sources["INT1D"]["supports"][0],
                                           elapsed_years=200.0, field="temperature_k", mode="BRACKET"),
        "int1d_reconstructed_temperature": query(sources["INT1D"], support_id=sources["INT1D"]["supports"][0],
                                                   elapsed_years=200.0, field="temperature_k",
                                                   mode="DIAGNOSTIC_RECONSTRUCTION"),
    }
    sample_support = sources["INT1D"]["supports"][0]
    examples["int1d_temporal_inspection_200_to_400"] = inspect_interval(
        sources["INT1D"], support_id=sample_support, start_years=200.0, end_years=400.0)
    examples["int1d_physical_refinement_request"] = physical_refinement_request(
        sources["INT1D"], support_id=sample_support, requested_years=200.0)
    retention = {name: analyze_retention(source) for name, source in sources.items()}
    b0 = {"find_states": "SUPPORTED_BY_HISTORYSTORE_FIND_STATES",
          "missing_minimum_adapter": ["read_only engineering bundle source", "verified manifest/provenance binding",
                                      "noncanonical temporal-support bridge to DomainStateEnvelope",
                                      "explicit history/branch scope and provenance records"],
          "existing_engineering_replay": "DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE",
          "executable_replay_registered": False, "canonical_world_history_written": False}
    source_identity = {name: {key: source[key] for key in (
        "experiment", "source_commit", "source_identity_sha256", "manifest_sha256", "run_result_sha256",
        "sample_artifact_sha256", "boundary_id", "resolution_fraction", "sampling", "sample_artifact_bytes",
        "supports")} for name, source in sources.items()}
    return {"schema": "ARCANA_R6_INT2A_HISTORICAL_QUERY_RESULT_V1",
            "decision": "INT2A_OFFLINE_HISTORICAL_QUERY_RECONSTRUCTION_EVIDENCED__B0_EXECUTABLE_BINDING_NOT_QUALIFIED",
            "scope": "READ_ONLY_VERIFIED_NONCANONICAL_ENGINEERING_BUNDLES",
            "source_identities": source_identity, "query_examples": examples,
            "retention_and_answerability": retention,
            "query_contract": {"modes": sorted(MODES), "fields": sorted(FIELD_ALLOWLIST),
                "interpolation": "PIECEWISE_LINEAR_TIME_ONLY_FOR_NUMERIC_FIELDS",
                "exact_match": "EXACT_FLOAT_EQUALITY_TO_VERIFIED_STORED_ELAPSED_YEARS",
                "bracket": "STRICT_INTERIOR_TWO_OBSERVED_RECORDS; EXACT_HITS_REQUIRE_EXACT_OBSERVED",
                "out_of_range_or_missing": "REJECT; NO_NEAREST_SUBSTITUTION",
                "profile_node_mapping": "SAME_INDEX_ONLY_WHEN_MATERIAL_COORDINATE_ARRAYS_MATCH_EXACTLY",
                "categorical_fields": "UNSUPPORTED", "physical_refinement": "REPORTS_MISSING_DEPENDENCIES_ONLY"},
            "b0_integration_assessment": b0,
            "limitations": ["ENGINEERING_EVIDENCE_ONLY", "NO_SCIENTIFIC_OR_CANONICAL_AUTHORITY",
                            "RECONSTRUCTION_IS_NOT_PHYSICAL_INTEGRATION", "NO_GENERAL_RETENTION_POLICY_QUALIFIED",
                            "RETROSPECTIVE_SELECTION_USES_FUTURE_DATA", "NO_HISTORYSTORE_BINDING_OR_EXECUTABLE_REPLAY"]}


def write_bundle(output_dir: Path, result: dict[str, Any]) -> dict[str, Any]:
    out = _absolute_checked(output_dir, must_exist=False)
    if out.exists():
        raise AuditError("OUTPUT_DIRECTORY_ALREADY_EXISTS")
    out.mkdir(parents=True, exist_ok=False)
    data = _json_bytes(result)
    target = out / "INT2A_QUERY_RESULTS.json"
    if target.write_bytes(data) != len(data) or target.read_bytes() != data:
        raise AuditError("OUTPUT_READBACK_MISMATCH")
    member = {"bytes": len(data), "sha256": _sha256(data)}
    manifest = {"schema": "ARCANA_R6_INT2A_OUTPUT_MANIFEST_V1", "files": {target.name: member},
                "source_manifests": {key: value["manifest_sha256"]
                                     for key, value in result["source_identities"].items()},
                "decision": result["decision"], "scope": result["scope"]}
    manifest_bytes = _json_bytes(manifest)
    mpath = out / "INT2A_OUTPUT_MANIFEST.json"
    if mpath.write_bytes(manifest_bytes) != len(manifest_bytes) or mpath.read_bytes() != manifest_bytes:
        raise AuditError("MANIFEST_READBACK_MISMATCH")
    sidecar = (_sha256(manifest_bytes) + "  INT2A_OUTPUT_MANIFEST.json\n").encode("ascii")
    spath = out / "INT2A_OUTPUT_MANIFEST.json.sha256"
    if spath.write_bytes(sidecar) != len(sidecar) or spath.read_bytes() != sidecar:
        raise AuditError("SIDECAR_READBACK_MISMATCH")
    if {p.name for p in out.iterdir()} != {target.name, mpath.name, spath.name}:
        raise AuditError("OUTPUT_MEMBERSHIP_MISMATCH")
    return {"result_bytes": len(data), "result_sha256": _sha256(data),
            "manifest_bytes": len(manifest_bytes), "manifest_sha256": _sha256(manifest_bytes),
            "manifest_sidecar_sha256": sidecar.decode("ascii").split()[0]}


def _reject_output_overlap(output_dir: Path, *source_dirs: Path) -> Path:
    out = _absolute_checked(output_dir, must_exist=False)
    for source_dir in source_dirs:
        source = _absolute_checked(source_dir, must_exist=True)
        if out == source or out in source.parents or source in out.parents:
            raise AuditError("OUTPUT_INPUT_PATH_OVERLAP")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r4", type=Path, required=True)
    parser.add_argument("--int1d", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        output = _reject_output_overlap(args.output, args.r4, args.int1d)
        result = build_analysis(args.r4, args.int1d)
        identity = write_bundle(output, result)
    except (AuditError, OSError, ValueError, TypeError, KeyError, IndexError, StopIteration) as exc:
        parser.error(str(exc))
    print(json.dumps({"decision": result["decision"], "output": str(args.output), **identity}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
