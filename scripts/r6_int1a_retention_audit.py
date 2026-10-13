#!/usr/bin/env python3
"""Bounded offline INT-1A retention/reconstruction audit for the verified R4 bundle.

This module reads immutable candidate artifacts and writes a new analysis bundle.
It never imports or calls the provider-backed evolution runner.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import stat
from typing import Any


EXPECTED_MANIFEST_SHA256 = "191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236"
EXPECTED_RUN_SHA256 = "b7625dfc636bc86f062ab38db42ee04215864de2390b78f69fbfe17c2438124a"
EXPECTED_SOURCE_COMMIT = "91fc83d50ec15d8bb9b826926ac2f2dc859281e8"
EXPECTED_SOURCE_IDENTITY = "b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca"
EXPECTED_MEMBERS: dict[str, tuple[int, str]] = {
    "CANDIDATE_CHECKPOINT.json": (83624, "3aaf0a8aafe69798087abb7c4ca17c082a54941fb79c409ada117871194a71e0"),
    "CANDIDATE_TRAJECTORY.json": (215173, "5a9d238dfe51dc3c8f4da5590a6f6a882db5dfc3bb04d9e97894398babbecbd1"),
    "DIAGNOSTIC_NUMERICAL_SAMPLES.json": (85583, "ca9c5a4bc6ff4441b198219183e4e564a391d239dfda6e2f87598b7bd14bebad"),
    "EDGE_AUDIT_MATRIX.json": (98300, "d89bd4d9cca8928f8e6b913ad6bf1955c429ac2e2e1bb4dc6b6263f7165a59c7"),
    "REPLAY_RESTART.json": (924, "baee231f00d65cb463aced5fe7d3cf3ce5969d26cd0d40dceec4bdd8702b510c"),
    "SELECTED_SECTION_AND_PROFILES.json": (49603, "57d841424d31673fb4586ad9978b95e075591cacab02b78c909e351e929621ae"),
    "THERMAL_CONVERGENCE.json": (148380, "dc1ac1437f5beb5ce978c9ec0179778dd2d36f4d5886ac3e0883649b696a7f84"),
    "RUN_RESULT.json": (7127, EXPECTED_RUN_SHA256),
}
EXPECTED_PROVIDERS = {
    "event_census": "e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e",
    "kinematics_artifact": "0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2",
    "kinematics_semantic": "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4",
    "mapping": "b8d57495bc6e196a0b9fe7afd466079bebd97d0f63baafe232f215e45897a09f",
    "source_set": EXPECTED_SOURCE_IDENTITY,
    "support_binding_index": "aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00",
    "thermal_field_package": "39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e",
    "vector_partition": "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab",
}
MAX_JSON_BYTES = 2_000_000
YEAR_SECONDS = 31_557_600.0
SCALAR_FIELDS = ("width_m", "crust_m", "lithosphere_m", "beta", "accumulated_strain")
ARRAY_FIELDS = ("z_m", "temperature_k")
UNITS = {"width_m": "m", "crust_m": "m", "lithosphere_m": "m", "beta": "1",
         "accumulated_strain": "1", "z_m": "m", "temperature_k": "K"}


class AuditError(ValueError):
    """Input is incomplete, inconsistent, or outside the declared audit scope."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def _write_verified(path: Path, data: bytes) -> None:
    if path.write_bytes(data) != len(data) or path.read_bytes() != data:
        raise AuditError(f"ANALYSIS_OUTPUT_READBACK_MISMATCH:{path.name}")


def _reject_constant(token: str) -> None:
    raise AuditError(f"NONFINITE_JSON_CONSTANT:{token}")


def _read_json_snapshot(path: Path) -> tuple[bytes, Any]:
    path = _absolute_checked(path, must_exist=True)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise AuditError(f"INPUT_READ_FAILED:{path.name}:{exc}") from exc
    if len(data) > MAX_JSON_BYTES:
        raise AuditError(f"INPUT_SIZE_LIMIT:{path.name}:{len(data)}")
    try:
        value = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"INPUT_JSON_INVALID:{path.name}:{exc}") from exc
    return data, value


def _absolute_checked(path: Path, *, must_exist: bool) -> Path:
    """Use lexical absolute paths and reject traversal/reparse components.

    Path.resolve() uses a Windows final-path query that can be denied by the
    managed AppContainer even for readable files. This check avoids following
    a link and rejects reparse points in every existing component instead.
    """
    raw = Path(path)
    if ".." in raw.parts:
        raise AuditError("PATH_TRAVERSAL_REJECTED")
    absolute = Path(os.path.abspath(os.fspath(raw)))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            if must_exist:
                raise AuditError(f"PATH_COMPONENT_MISSING:{current}")
            continue
        except OSError as exc:
            raise AuditError(f"PATH_COMPONENT_UNVERIFIABLE:{current}:{exc}") from exc
        attributes = getattr(info, "st_file_attributes", 0)
        reparse = bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        if stat.S_ISLNK(info.st_mode) or reparse:
            raise AuditError(f"PATH_REPARSE_COMPONENT_REJECTED:{current}")
    if must_exist and not absolute.exists():
        raise AuditError("INPUT_PATH_MISSING")
    return absolute


def load_verified_bundle(root: Path, *, expected_manifest_sha256: str = EXPECTED_MANIFEST_SHA256,
                         expected_members: dict[str, tuple[int, str]] = EXPECTED_MEMBERS
                         ) -> tuple[dict[str, Any], dict[str, int], dict[str, str], dict[str, bytes]]:
    """Verify exact directory membership, externally fixed digests, and parse verified bytes."""
    root = _absolute_checked(root, must_exist=True)
    if not root.is_dir() or root.name != "INT0B_TF2B_5_11_R4_20261013_04":
        raise AuditError("UNEXPECTED_R4_SOURCE_DIRECTORY")
    manifest_path = root / "CANDIDATE_MANIFEST.json"
    manifest_bytes, manifest = _read_json_snapshot(manifest_path)
    if _sha256(manifest_bytes) != expected_manifest_sha256:
        raise AuditError("CANDIDATE_MANIFEST_SHA256_MISMATCH")
    if manifest.get("schema") != "ARCANA_R6_TF2B_INT0_OUTPUT_MANIFEST_V1":
        raise AuditError("CANDIDATE_MANIFEST_SCHEMA_MISMATCH")
    if manifest.get("canonical_publication") is not False:
        raise AuditError("SOURCE_BUNDLE_NOT_NONCANONICAL")
    expected_names = set(expected_members) | {"CANDIDATE_MANIFEST.json"}
    entries = list(root.iterdir())
    actual_names = {p.name for p in entries}
    if (actual_names != expected_names or any(not p.is_file() or p.is_symlink() for p in entries)):
        raise AuditError("CANDIDATE_DIRECTORY_MEMBERSHIP_MISMATCH")
    if set(manifest.get("files", {})) != set(expected_members) - {"RUN_RESULT.json"}:
        raise AuditError("MANIFEST_MEMBER_SET_MISMATCH")
    if manifest.get("RUN_RESULT.json") != {"bytes": expected_members["RUN_RESULT.json"][0],
                                               "sha256": expected_members["RUN_RESULT.json"][1]}:
        raise AuditError("MANIFEST_RUN_RESULT_IDENTITY_MISMATCH")
    docs: dict[str, Any] = {"CANDIDATE_MANIFEST.json": manifest}
    sizes = {"CANDIDATE_MANIFEST.json": len(manifest_bytes)}
    digests = {"CANDIDATE_MANIFEST.json": _sha256(manifest_bytes)}
    snapshots = {"CANDIDATE_MANIFEST.json": manifest_bytes}
    for name, (expected_size, expected_hash) in expected_members.items():
        entry = manifest["RUN_RESULT.json"] if name == "RUN_RESULT.json" else manifest["files"].get(name)
        if entry != {"bytes": expected_size, "sha256": expected_hash}:
            raise AuditError(f"MANIFEST_EXPECTED_IDENTITY_MISMATCH:{name}")
        data, parsed = _read_json_snapshot(root / name)
        if len(data) != expected_size or _sha256(data) != expected_hash:
            raise AuditError(f"MEMBER_INTEGRITY_MISMATCH:{name}")
        docs[name] = parsed
        sizes[name] = len(data)
        digests[name] = _sha256(data)
        snapshots[name] = data
    return docs, sizes, digests, snapshots


def validate_r4_provenance(docs: dict[str, Any]) -> None:
    manifest = docs["CANDIDATE_MANIFEST.json"]
    result = docs["RUN_RESULT.json"]
    trajectory = docs["CANDIDATE_TRAJECTORY.json"]
    section = docs["SELECTED_SECTION_AND_PROFILES.json"]
    samples = docs["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]
    checkpoint = docs["CANDIDATE_CHECKPOINT.json"]
    replay = docs["REPLAY_RESTART.json"]
    if result.get("decision") != "CONTINENTAL_ENGINEERING_SLICE_PASS":
        raise AuditError("RUN_RESULT_DECISION_MISMATCH")
    if result.get("checkpoint_commit") != EXPECTED_SOURCE_COMMIT:
        raise AuditError("RUN_SOURCE_COMMIT_MISMATCH")
    if result.get("pair_5_11_event_eligibility", {}).get("pair_id") != "5:11":
        raise AuditError("RUN_PAIR_MISMATCH")
    if result.get("selected_support_ids") != ["R6G1D-R091-C029", "R6G1D-R091-C028"]:
        raise AuditError("RUN_SUPPORT_IDENTITY_MISMATCH")
    if result.get("preserved_non_actions", {}).get("world_history_accessed") is not False or result.get(
            "preserved_non_actions", {}).get("world_history_mutated") is not False:
        raise AuditError("WORLD_HISTORY_NONACTION_MISMATCH")
    source = trajectory.get("source_code", {})
    if source.get("commit") != EXPECTED_SOURCE_COMMIT or source.get("source_identity_sha256") != EXPECTED_SOURCE_IDENTITY:
        raise AuditError("TRAJECTORY_SOURCE_IDENTITY_MISMATCH")
    if trajectory.get("providers") != EXPECTED_PROVIDERS or manifest.get("provider_identities") != EXPECTED_PROVIDERS:
        raise AuditError("PROVIDER_IDENTITY_MISMATCH")
    if trajectory.get("b0_replay_status") != "DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE":
        raise AuditError("B0_REPLAY_AUTHORITY_MISMATCH")
    if trajectory.get("canonical_publication") is not False:
        raise AuditError("TRAJECTORY_CANONICAL_FLAG_MISMATCH")
    if section.get("ordered_plate_pair") != [5, 11] or section.get("physical_section_selected") is not False:
        raise AuditError("SECTION_SCOPE_MISMATCH")
    if section.get("source_set_identity_sha256") != EXPECTED_SOURCE_IDENTITY:
        raise AuditError("SECTION_SOURCE_IDENTITY_MISMATCH")
    if samples.get("canonical_publication") is not False or samples.get("interpolation") != "NONE":
        raise AuditError("SAMPLE_SCOPE_MISMATCH")
    if samples.get("resolution_fraction") != 0.0005:
        raise AuditError("SAMPLE_RESOLUTION_IDENTITY_MISMATCH")
    if samples.get("support_ids") != result.get("selected_support_ids"):
        raise AuditError("SAMPLE_RUN_SUPPORT_MISMATCH")
    expected_map = manifest.get("files", {})
    if result.get("artifact_sha256") != {name: entry["sha256"] for name, entry in expected_map.items()}:
        raise AuditError("RUN_RESULT_ARTIFACT_MAP_MISMATCH")
    fields = {row["support_id"]: row for row in trajectory.get("fields", [])}
    if set(fields) != set(samples["support_ids"]):
        raise AuditError("TRAJECTORY_SUPPORT_BINDING_MISMATCH")
    initial_states, final_states = checkpoint.get("initial_states"), checkpoint.get("candidate_states")
    if not isinstance(initial_states, list) or not isinstance(final_states, list) or len(initial_states) != 2 or len(final_states) != 2:
        raise AuditError("CHECKPOINT_STATE_CARDINALITY_MISMATCH")
    state_keys = ("width_m", "crust_m", "lithosphere_m", "beta", "accumulated_strain",
                  "material_coordinate", "temperature_k", "z_m")
    for position, support in enumerate(samples["support_ids"]):
        rows = samples["samples_by_support"][support]
        field = fields[support]
        initial, final = field["initial"], field["candidate"]
        for key in state_keys:
            if rows[0].get(key) != initial.get(key) or rows[-1].get(key) != final.get(key):
                raise AuditError(f"TRAJECTORY_SAMPLE_ENDPOINT_MISMATCH:{support}:{key}")
            if initial_states[position].get(key) != initial.get(key) or final_states[position].get(key) != final.get(key):
                raise AuditError(f"CHECKPOINT_TRAJECTORY_STATE_MISMATCH:{support}:{key}")
    if replay != result.get("replay_restart") or replay.get("restart_pass") is not True:
        raise AuditError("REPLAY_ARTIFACT_RESULT_MISMATCH")


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AuditError(f"NUMERIC_FIELD_INVALID:{label}")
    number = float(value)
    if not math.isfinite(number):
        raise AuditError(f"NUMERIC_FIELD_NONFINITE:{label}")
    return number


def _difference_metrics(actual: list[float], reconstructed: list[float]) -> dict[str, Any]:
    if len(actual) != len(reconstructed) or not actual:
        raise AuditError("ERROR_VECTOR_CARDINALITY_INVALID")
    errors = []
    for index, (a, r) in enumerate(zip(actual, reconstructed)):
        aa = _finite_number(a, f"actual[{index}]")
        rr = _finite_number(r, f"reconstructed[{index}]")
        delta = aa - rr
        if not math.isfinite(delta):
            raise AuditError("ERROR_DIFFERENCE_NONFINITE")
        errors.append(delta)
    max_abs = max(abs(e) for e in errors)
    scale = max_abs
    rmse = 0.0 if scale == 0.0 else scale * math.sqrt(math.fsum((e / scale) ** 2 for e in errors) / len(errors))
    relative_values = [abs(e) / abs(a) for e, a in zip(errors, actual) if a != 0.0]
    undefined = sum(1 for e, a in zip(errors, actual) if a == 0.0 and e != 0.0)
    return {"value_count": len(actual), "max_abs_error": max_abs, "rmse": rmse,
            "max_component_relative_error": max(relative_values) if relative_values else None,
            "zero_reference_nonzero_error_count": undefined,
            "relative_error_status": "ZERO_REFERENCE_NONZERO_ERROR" if undefined else
                                     ("UNDEFINED_ALL_REFERENCES_ZERO" if not relative_values else "DEFINED")}


def _interp(t: float, left_t: float, right_t: float, left: float, right: float) -> float:
    if not left_t < t < right_t:
        raise AuditError("INTERPOLATION_BRACKET_INVALID")
    value = left + (right - left) * ((t - left_t) / (right_t - left_t))
    if not math.isfinite(value):
        raise AuditError("INTERPOLATION_NONFINITE")
    return value


def _interpolate_record(rows: list[dict[str, Any]], retained: tuple[int, ...], target: int,
                        field: str) -> list[float]:
    before = max(index for index in retained if index < target)
    after = min(index for index in retained if index > target)
    t = float(rows[target]["elapsed_years"])
    lt, rt = float(rows[before]["elapsed_years"]), float(rows[after]["elapsed_years"])
    left, right = rows[before][field], rows[after][field]
    if field in SCALAR_FIELDS:
        return [_interp(t, lt, rt, float(left), float(right))]
    if len(left) != len(right) or len(left) != len(rows[target][field]):
        raise AuditError(f"PROFILE_CARDINALITY_MISMATCH:{field}")
    return [_interp(t, lt, rt, float(a), float(b)) for a, b in zip(left, right)]


def _sample_error(rows: list[dict[str, Any]], retained: tuple[int, ...], target: int,
                  field: str) -> dict[str, Any]:
    reconstructed = _interpolate_record(rows, retained, target, field)
    actual_raw = rows[target][field]
    actual = [float(actual_raw)] if field in SCALAR_FIELDS else [float(x) for x in actual_raw]
    metrics = _difference_metrics(actual, reconstructed)
    if field == "temperature_k":
        errors = [abs(a-b) for a, b in zip(actual, reconstructed)]
        index = max(range(len(errors)), key=errors.__getitem__)
        metrics["max_abs_error_node_index_0based"] = index
        metrics["max_abs_error_material_coordinate"] = rows[target]["material_coordinate"][index]
    return metrics


def _adaptive_index(all_rows: dict[str, list[dict[str, Any]]]) -> tuple[int, float]:
    """Retrospective max normalized endpoint-chord residual; uses the full trajectory."""
    scores: dict[int, float] = {}
    for rows in all_rows.values():
        for index in range(1, len(rows)-1):
            t = float(rows[index]["elapsed_years"])
            for field in SCALAR_FIELDS + ARRAY_FIELDS:
                predicted = _interpolate_record(rows, (0, len(rows)-1), index, field)
                actual_raw = rows[index][field]
                actual = [float(actual_raw)] if field in SCALAR_FIELDS else [float(x) for x in actual_raw]
                if field in SCALAR_FIELDS:
                    ranges = [max(float(row[field]) for row in rows) - min(float(row[field]) for row in rows)]
                else:
                    ranges = [max(float(row[field][node]) for row in rows) -
                              min(float(row[field][node]) for row in rows) for node in range(len(actual))]
                normalized = []
                for a, p, span in zip(actual, predicted, ranges):
                    delta = abs(a-p)
                    if span == 0.0:
                        if delta != 0.0:
                            normalized.append(math.inf)
                    else:
                        normalized.append(delta/span)
                if normalized:
                    scores[index] = max(scores.get(index, 0.0), max(normalized))
    if not scores:
        raise AuditError("NO_INTERIOR_SAMPLES_FOR_ADAPTIVE_COMPARISON")
    chosen = max(sorted(scores), key=lambda index: scores[index])
    return chosen, scores[chosen]


def _validate_samples(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if document.get("schema") != "ARCANA_R6_TF2B_NUMERICAL_STEP_SAMPLES_V2":
        raise AuditError("SAMPLE_SCHEMA_MISMATCH")
    if document.get("all_numerical_substeps_captured") is not True:
        raise AuditError("SAMPLE_COMPLETENESS_FLAG_FALSE")
    supports = document.get("support_ids")
    rows_by_support = document.get("samples_by_support")
    if (not isinstance(supports, list) or not supports or
            not all(isinstance(item, str) for item in supports) or
            len(set(supports)) != len(supports) or not isinstance(rows_by_support, dict) or
            set(supports) != set(rows_by_support)):
        raise AuditError("SAMPLE_SUPPORT_MEMBERSHIP_MISMATCH")
    if document.get("sample_count_by_support") != {key: len(rows_by_support[key]) for key in supports}:
        raise AuditError("SAMPLE_COUNT_METADATA_MISMATCH")
    result: dict[str, list[dict[str, Any]]] = {}
    reference_times: list[float] | None = None
    reference_coords: list[float] | None = None
    for support in supports:
        rows = rows_by_support[support]
        if not isinstance(rows, list) or len(rows) < 3 or len(rows) > 10_001:
            raise AuditError(f"SAMPLE_COUNT_OUT_OF_SCOPE:{support}")
        times = []
        coords = None
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise AuditError("SAMPLE_ROW_NOT_OBJECT")
            if row.get("support_id") != support:
                raise AuditError("ROW_SUPPORT_ID_MISMATCH")
            time_y = _finite_number(row.get("elapsed_years"), "elapsed_years")
            time_s = _finite_number(row.get("time_s"), "time_s")
            if time_y != time_s / YEAR_SECONDS:
                raise AuditError("TIME_UNIT_RECONCILIATION_MISMATCH")
            times.append(time_y)
            if index == 0 and row.get("record_type") != "DIAGNOSTIC_SAMPLE":
                raise AuditError("INITIAL_RECORD_TYPE_MISMATCH")
            if index == len(rows)-1 and row.get("record_type") != "ENDPOINT_STATE":
                raise AuditError("FINAL_RECORD_TYPE_MISMATCH")
            current_coords = row.get("material_coordinate")
            if not isinstance(current_coords, list) or not current_coords:
                raise AuditError("MATERIAL_COORDINATE_MISSING")
            current_coords = [_finite_number(x, "material_coordinate") for x in current_coords]
            if coords is None:
                coords = current_coords
            elif current_coords != coords:
                raise AuditError("MATERIAL_COORDINATE_ALIGNMENT_CHANGED")
            if len(current_coords) > 73:
                raise AuditError("PROFILE_NODE_LIMIT_EXCEEDED")
            if len(current_coords) != len(row.get("z_m", [])) or len(current_coords) != len(row.get("temperature_k", [])):
                raise AuditError("PROFILE_ARRAY_CARDINALITY_MISMATCH")
            for field in SCALAR_FIELDS:
                _finite_number(row.get(field), field)
            for field in ARRAY_FIELDS:
                for value in row[field]:
                    _finite_number(value, field)
            lithosphere = float(row["lithosphere_m"])
            if row["z_m"] != [coordinate * lithosphere for coordinate in current_coords]:
                raise AuditError("DEPTH_COORDINATE_RECONCILIATION_MISMATCH")
            result[support] = rows
        if any(right <= left for left, right in zip(times, times[1:])):
            raise AuditError(f"SAMPLE_TIMES_NOT_STRICTLY_INCREASING:{support}")
        if reference_times is None:
            reference_times, reference_coords = times, coords
        elif times != reference_times or coords != reference_coords:
            raise AuditError("SUPPORT_TEMPORAL_OR_MATERIAL_SUPPORT_MISMATCH")
        if rows[0]["elapsed_years"] != 0.0 or rows[0]["time_s"] != 0.0:
            raise AuditError("INITIAL_TIME_NOT_ZERO")
    return result


def _variation(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [float(row[field]) for row in rows]
    start, end = values[0], values[-1]
    delta = end - start
    return {"initial": start, "final": end, "absolute_change": delta,
            "relative_change": delta / abs(start) if start != 0.0 else None,
            "relative_change_status": "DEFINED" if start != 0.0 else "ZERO_INITIAL_REFERENCE"}


def _field_inventory() -> list[dict[str, Any]]:
    return [
        {"field": "elapsed_years", "unit": "year", "representation": "JSON number",
         "role": "independent temporal coordinate", "present": "all records", "restart": "required as time coordinate"},
        {"field": "time_s", "unit": "s", "representation": "JSON number",
         "role": "independent kernel time coordinate", "present": "all records", "restart": "required"},
        {"field": "width_m", "unit": "m", "representation": "JSON binary64-compatible number",
         "role": "evolving reduced-state variable", "present": "all records", "restart": "required"},
        {"field": "crust_m", "unit": "m", "representation": "JSON binary64-compatible number",
         "role": "evolving reduced-state variable", "present": "all records", "restart": "required"},
        {"field": "lithosphere_m", "unit": "m", "representation": "JSON binary64-compatible number",
         "role": "evolving reduced-state variable", "present": "all records", "restart": "required"},
        {"field": "temperature_k", "unit": "K", "representation": "73-element JSON number array",
         "role": "evolving thermal state on material-coordinate nodes", "present": "all records", "restart": "required"},
        {"field": "material_coordinate", "unit": "1", "representation": "73-element JSON number array",
         "role": "fixed material support coordinate", "present": "all records", "restart": "required for node correspondence"},
        {"field": "z_m", "unit": "m", "representation": "73-element JSON number array",
         "role": "derived as material_coordinate × lithosphere_m", "present": "all records", "restart": "recomputable by declared code relation; retained for diagnostics"},
        {"field": "beta", "unit": "1", "representation": "JSON number",
         "role": "derived as width_m / initial_width_m", "present": "all records", "restart": "derivable if initial width retained"},
        {"field": "accumulated_strain", "unit": "1", "representation": "JSON number",
         "role": "derived as ln(beta) in ReducedState update", "present": "all records", "restart": "derivable if beta retained; exact float bits not promised"},
        {"field": "materials", "unit": "mixed SI coefficients", "representation": "per-node records",
         "role": "fixed material/rheology configuration consumed by thermal kernel", "present": "full endpoint/checkpoint, omitted from compact intermediate samples", "restart": "required; compact diagnostic records alone are insufficient"},
        {"field": "initial_width_m / initial_crust_m / initial_lithosphere_m", "unit": "m", "representation": "JSON number",
         "role": "initial-state anchors", "present": "full endpoint/checkpoint; compact samples omit them", "restart": "required for state reconstruction"},
        {"field": "surface_temperature_k / base_temperature_k", "unit": "K", "representation": "JSON number",
         "role": "fixed thermal boundary values", "present": "full endpoint/checkpoint", "restart": "required by kernel"},
        {"field": "area_m2", "unit": "m2", "representation": "JSON number",
         "role": "derived diagnostic: width_m × lithosphere_m", "present": "full endpoint/checkpoint", "restart": "recomputable; compared as derived output"},
        {"field": "crust_fraction", "unit": "1", "representation": "JSON number",
         "role": "initial-state/configuration scalar held fixed by this kernel", "present": "full endpoint/checkpoint", "restart": "must be retained or reconstructed from its initialization contract"},
    ]


def analyze_samples(document: dict[str, Any], original_serialized_bytes: int | None = None) -> dict[str, Any]:
    rows_by_support = _validate_samples(document)
    support_ids = list(document["support_ids"])
    count = len(next(iter(rows_by_support.values())))
    internal = tuple(range(1, count-1))
    fixed_sets: list[tuple[int, ...]] = []
    for internal_count in range(len(internal)+1):
        for chosen in itertools.combinations(internal, internal_count):
            fixed_sets.append((0, *chosen, count-1))
    adaptive_index, adaptive_score = _adaptive_index(rows_by_support)
    strategies = []
    for retained in fixed_sets:
        strategies.append({"strategy": "FIXED_ACTUAL_TIMESTAMP_SUBSET",
                           "retained_indices_0based": list(retained), "adaptive": False})
    adaptive_retained = tuple(sorted((0, adaptive_index, count-1)))
    strategies.append({"strategy": "RETROSPECTIVE_ADAPTIVE_MAX_NORMALIZED_CHORD_RESIDUAL",
                       "retained_indices_0based": list(adaptive_retained), "adaptive": True,
                       "selected_interior_index_0based": adaptive_index,
                       "selection_score": adaptive_score,
                       "uses_complete_trajectory_and_future_endpoint": True,
                       "causal_online_policy_validated": False})
    strategy_results = []
    for strategy in strategies:
        retained = tuple(strategy["retained_indices_0based"])
        omitted = [i for i in range(count) if i not in retained]
        support_errors: dict[str, Any] = {}
        for support in support_ids:
            rows = rows_by_support[support]
            fields: dict[str, Any] = {}
            for field in SCALAR_FIELDS + ARRAY_FIELDS:
                per_sample = [{"sample_index_0based": target,
                               "elapsed_years": rows[target]["elapsed_years"],
                               **_sample_error(rows, retained, target, field)} for target in omitted]
                flat_actual, flat_reconstructed = [], []
                for target in omitted:
                    flat_actual.extend([float(rows[target][field])] if field in SCALAR_FIELDS else
                                        [float(value) for value in rows[target][field]])
                    flat_reconstructed.extend(_interpolate_record(rows, retained, target, field))
                combined = _difference_metrics(flat_actual, flat_reconstructed) if omitted else {
                    "value_count": 0, "max_abs_error": 0.0, "rmse": 0.0,
                    "max_component_relative_error": 0.0, "zero_reference_nonzero_error_count": 0,
                    "relative_error_status": "NO_OMITTED_STATES"}
                fields[field] = {"combined_omitted_state_metrics": combined,
                                 "per_omitted_sample": per_sample}
            derived: dict[str, Any] = {}
            derived_values: dict[str, tuple[list[float], list[float]]] = {
                "area_m2_from_width_times_lithosphere": ([], []),
                "beta_from_width_over_initial_width": ([], []),
                "accumulated_strain_from_log_beta": ([], []),
            }
            initial_width = float(rows[0]["width_m"])
            for target in omitted:
                width = _interpolate_record(rows, retained, target, "width_m")[0]
                lithosphere = _interpolate_record(rows, retained, target, "lithosphere_m")[0]
                beta = width / initial_width
                if beta <= 0.0 or not math.isfinite(beta):
                    raise AuditError("DERIVED_BETA_INVALID")
                strain = math.log(beta)
                area = width * lithosphere
                if not all(math.isfinite(value) for value in (strain, area)):
                    raise AuditError("DERIVED_QUANTITY_NONFINITE")
                derived_values["area_m2_from_width_times_lithosphere"][0].append(
                    float(rows[target]["width_m"]) * float(rows[target]["lithosphere_m"]))
                derived_values["area_m2_from_width_times_lithosphere"][1].append(area)
                derived_values["beta_from_width_over_initial_width"][0].append(float(rows[target]["beta"]))
                derived_values["beta_from_width_over_initial_width"][1].append(beta)
                derived_values["accumulated_strain_from_log_beta"][0].append(
                    float(rows[target]["accumulated_strain"]))
                derived_values["accumulated_strain_from_log_beta"][1].append(strain)
            for name, (actual, reconstructed) in derived_values.items():
                derived[name] = (_difference_metrics(actual, reconstructed) if actual else {
                    "value_count": 0, "max_abs_error": 0.0, "rmse": 0.0,
                    "max_component_relative_error": 0.0, "zero_reference_nonzero_error_count": 0,
                    "relative_error_status": "NO_OMITTED_STATES"})
            support_errors[support] = {"recorded_fields": fields, "derived_quantities": derived}
        strategy_results.append({**strategy, "retained_state_count_per_support": len(retained),
            "omitted_state_count_per_support": len(omitted),
            "retention_ratio": len(retained)/count,
            "diagnostic_reconstruction": "PIECEWISE_LINEAR_AT_RECORDED_TIMESTAMPS; NOT COMPUTED PHYSICAL HISTORY",
            "support_errors": support_errors})
    return {"schema": "ARCANA_R6_INT1A_RETENTION_METRICS_V1",
        "analysis_scope": "EXISTING_NONCANONICAL_INT0B_R4_ENGINEERING_TRAJECTORY_ONLY",
        "sample_count_per_support": count,
        "support_ids": support_ids,
        "sample_times_years": [float(row["elapsed_years"]) for row in rows_by_support[support_ids[0]]],
        "full_diagnostic_artifact_bytes": original_serialized_bytes,
        "full_sample_record_standalone_json_bytes": sum(len(_json_bytes(row)) for rows in rows_by_support.values() for row in rows),
        "field_inventory": _field_inventory(),
        "observed_variation_by_support": {support: {field: _variation(rows, field)
            for field in SCALAR_FIELDS} | {"temperature_k_profile": {
                "initial_min_k": min(rows[0]["temperature_k"]), "initial_max_k": max(rows[0]["temperature_k"]),
                "final_min_k": min(rows[-1]["temperature_k"]), "final_max_k": max(rows[-1]["temperature_k"]),
                "max_node_abs_change_k": max(abs(a-b) for a,b in zip(rows[-1]["temperature_k"],rows[0]["temperature_k"])),
                "material_coordinate_preserved": all(row["material_coordinate"] == rows[0]["material_coordinate"] for row in rows)}}
            for support, rows in rows_by_support.items()},
        "strategies": strategy_results,
        "storage_scope_note": "JSON byte counts are for the serialized diagnostic sample artifact or generated subset documents; they are not HistoryStore costs, RSS, compact binary sizes, or a canonical storage policy.",
        "online_adaptive_policy": "UNKNOWN_NOT_VALIDATED; retrospective selector uses all four samples including final endpoint",
        "event_retention": "UNKNOWN_NO_PHYSICAL_EVENT_AUTHORITY_IN_THIS_ENGINEERING_RUN",
        "general_policy": "NOT_QUALIFIED_FROM_TWO_SUPPORTS_AND_FOUR_SAMPLES"}


def _retained_document(source: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    result = dict(source)
    retained_indices = strategy["retained_indices_0based"]
    result["scope"] = "INT1A_RETENTION_SUBSET_DIAGNOSTIC_ONLY_NOT_COMPUTED_HISTORY"
    result["sampling"] = "INT1A_SUBSET_OF_EXISTING_RECORDED_TIMESTAMPS"
    result["all_numerical_substeps_captured"] = len(retained_indices) == len(source["samples_by_support"][source["support_ids"][0]])
    result["sample_count_by_support"] = {support: len(retained_indices) for support in source["support_ids"]}
    result["samples_by_support"] = {support: [source["samples_by_support"][support][i] for i in retained_indices]
                                    for support in source["support_ids"]}
    return result


def run_audit(source_dir: Path, output_dir: Path) -> dict[str, Any]:
    source = _absolute_checked(source_dir, must_exist=True)
    out = _absolute_checked(output_dir, must_exist=False)
    if out.exists():
        raise AuditError("OUTPUT_DIRECTORY_ALREADY_EXISTS")
    if out == source or source in out.parents or out in source.parents:
        raise AuditError("INPUT_OUTPUT_PATH_OVERLAP")
    docs, sizes, hashes, snapshots = load_verified_bundle(source)
    validate_r4_provenance(docs)
    samples_raw = snapshots["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]
    # The production serializer is deterministic; full retention must reproduce its bytes exactly.
    if _json_bytes(docs["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]) != samples_raw:
        raise AuditError("SOURCE_SAMPLE_SERIALIZATION_NOT_CANONICAL")
    metrics = analyze_samples(docs["DIAGNOSTIC_NUMERICAL_SAMPLES.json"], sizes["DIAGNOSTIC_NUMERICAL_SAMPLES.json"])
    trajectory = docs["CANDIDATE_TRAJECTORY.json"]
    metrics["source_provenance"] = {"candidate_manifest_sha256": hashes["CANDIDATE_MANIFEST.json"],
        "source_commit": trajectory["source_code"]["commit"],
        "source_identity_sha256": trajectory["source_code"]["source_identity_sha256"],
        "provider_identities": trajectory["providers"],
        "run_result_sha256": hashes["RUN_RESULT.json"],
        "source_directory": "outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04"}
    metrics["input_artifact_identity"] = {name: {"bytes": sizes[name], "sha256": hashes[name]} for name in sorted(sizes)}
    checkpoint_bytes = sizes["CANDIDATE_CHECKPOINT.json"]
    metrics["storage_observations"] = {
        "full_diagnostic_sample_artifact_bytes": sizes["DIAGNOSTIC_NUMERICAL_SAMPLES.json"],
        "complete_initial_and_candidate_checkpoint_artifact_bytes": checkpoint_bytes,
        "diagnostic_vs_checkpoint_byte_difference": sizes["DIAGNOSTIC_NUMERICAL_SAMPLES.json"] - checkpoint_bytes,
        "b0_replay_cost": "NOT_MEASURED; replay recipe is descriptor-only and not registered in HistoryStore",
        "minimal_physical_state_encoding": "NOT_DEFINED; no arbitrary schema/encoding was selected"}
    # For each strategy, compare deterministic serialized subset size. Full-set output must match source.
    storage_rows = []
    for strategy in metrics["strategies"]:
        is_full = len(strategy["retained_indices_0based"]) == len(metrics["sample_times_years"])
        if is_full:
            payload = samples_raw
        else:
            subset = _retained_document(docs["DIAGNOSTIC_NUMERICAL_SAMPLES.json"], strategy)
            payload = _json_bytes(subset)
        strategy["deterministic_subset_json_bytes"] = len(payload)
        strategy["subset_bytes_fraction_of_full_sample_artifact"] = len(payload) / sizes["DIAGNOSTIC_NUMERICAL_SAMPLES.json"]
        storage_rows.append({"strategy": strategy["strategy"],
            "retained_indices_0based": ",".join(map(str, strategy["retained_indices_0based"])),
            "retained_states_per_support": strategy["retained_state_count_per_support"],
            "omitted_states_per_support": strategy["omitted_state_count_per_support"],
            "retention_ratio": strategy["retention_ratio"],
            "serialized_subset_bytes": len(payload),
            "fraction_of_full_sample_artifact": strategy["subset_bytes_fraction_of_full_sample_artifact"],
            "adaptive_retrospective": strategy["adaptive"]})
        if is_full:
            if payload != samples_raw:
                raise AuditError("FULL_RETENTION_BYTE_IDENTITY_MISMATCH")
    out.mkdir(parents=True, exist_ok=False)
    metrics_bytes = _json_bytes(metrics)
    _write_verified(out / "INT1A_RETENTION_METRICS.json", metrics_bytes)
    with (out / "INT1A_RETENTION_STORAGE.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(storage_rows[0]))
        writer.writeheader()
        writer.writerows(storage_rows)
    output_files = {}
    for name in ("INT1A_RETENTION_METRICS.json", "INT1A_RETENTION_STORAGE.csv"):
        data = (out / name).read_bytes()
        output_files[name] = {"bytes": len(data), "sha256": _sha256(data)}
    manifest = {"schema": "ARCANA_R6_INT1A_OUTPUT_MANIFEST_V1",
        "source_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "source_run_result_sha256": EXPECTED_RUN_SHA256,
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "source_identity_sha256": EXPECTED_SOURCE_IDENTITY,
        "files": output_files,
        "scope": "OFFLINE_ANALYSIS_ONLY; ORIGINAL_R4_BUNDLE_READ_ONLY; NONCANONICAL"}
    manifest_bytes = _json_bytes(manifest)
    _write_verified(out / "INT1A_ANALYSIS_MANIFEST.json", manifest_bytes)
    sidecar = (_sha256(manifest_bytes) + "  INT1A_ANALYSIS_MANIFEST.json\n").encode("ascii")
    _write_verified(out / "INT1A_ANALYSIS_MANIFEST.json.sha256", sidecar)
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        metrics = run_audit(args.source, args.output)
    except (AuditError, OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        parser.error(str(exc))
    print(json.dumps({"decision": "INT1A_RETENTION_ANALYSIS_COMPLETE_BOUNDED_SCOPE",
                      "supports": metrics["support_ids"], "sample_count_per_support": metrics["sample_count_per_support"],
                      "strategy_count": len(metrics["strategies"]), "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
