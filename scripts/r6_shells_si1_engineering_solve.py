#!/usr/bin/env python3
"""Isolated ShellSet SI1 engineering run; no canonical publication.

This runner builds only the tracked vendored ShellSet source in a fresh
workspace, verifies the ARCANA FEG/runtime inputs, derives plate outlines from
the explicit canonical partition payload, and performs a KSize preflight
before any stiffness-matrix allocation. It is intended for Ubuntu/Fair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

try:
    import resource
except ImportError:  # Windows static/unit validation; runtime is Linux-only.
    resource = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "configs/r6_shells_si1/engineering_case.json"
LOCK_PATH = ROOT / "configs/r6_shells_si1/shellset_source_lock.json"
FEG_PATH = ROOT / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
FEG_MANIFEST_PATH = ROOT / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"
RUNTIME_PATH = ROOT / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
RUNTIME_MANIFEST_PATH = ROOT / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json"
PARTITION_MANIFEST_PATH = ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"
SUCCESSOR_PROVENANCE_PATH = ROOT / "R6_PRE_ORBDATA_SHELLSET_SUCCESSOR_PATCH_PROVENANCE.json"
SHELLSET_FAIR_QUALIFICATION_PATH = ROOT / "R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json"
ORBDATA_FAIR_QUALIFICATION_PATH = ROOT / "R6_T0_ORBDATA_ARCANA_FAIR_RUNTIME_QUALIFICATION.json"
SHELLSET_SOURCE = ROOT / "external/ShellSet-v1.1.0"
K_SIZE_RE = re.compile(
    r"SI1_KSIZE\s+nRank=(\d+)\s+nKRows=(\d+)\s+nCodiagonals=(\d+)\s+matrix_bytes=([0-9.Ee+\-]+)"
)
FLOAT_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?$")


class SI1Error(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def run_checked(command: list[str], *, cwd: Path, timeout: int | None = None,
                stdout_path: Path | None = None, env: dict[str, str] | None = None,
                address_space_bytes: int | None = None) -> subprocess.CompletedProcess[str]:
    def limit_address_space() -> None:
        if address_space_bytes is not None and resource is not None:
            resource.setrlimit(resource.RLIMIT_AS, (address_space_bytes, address_space_bytes))

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            preexec_fn=limit_address_space if address_space_bytes is not None else None,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        if stdout_path is not None:
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            stdout_path.write_text(captured, encoding="utf-8", newline="\n")
        raise
    if stdout_path is not None:
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text(result.stdout or "", encoding="utf-8", newline="\n")
    return result


def verify_source_lock(source_root: Path, lock: dict[str, Any]) -> dict[str, str]:
    source_root = source_root.resolve()
    expected_paths = set(lock["files"])
    actual_source_paths = {"Makefile"}
    actual_source_paths.update(
        path.relative_to(source_root).as_posix()
        for path in (source_root / "src").glob("*.f90")
        if path.is_file()
    )
    if actual_source_paths != expected_paths:
        raise SI1Error(
            "ShellSet source inventory differs from lock; "
            f"unlocked={sorted(actual_source_paths - expected_paths)}, "
            f"missing_from_source={sorted(expected_paths - actual_source_paths)}"
        )
    actual: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        candidate = (source_root / relative).resolve()
        if source_root.resolve() not in candidate.parents:
            raise SI1Error(f"ShellSet source path escapes source root: {relative}")
        if not candidate.is_file():
            raise SI1Error(f"required ShellSet source is missing: {relative}")
        digest = sha256(candidate)
        if digest != expected:
            raise SI1Error(f"ShellSet source SHA mismatch for {relative}: {digest}")
        actual[relative] = digest
    return actual


def reconcile_source_evidence(source_hashes: dict[str, str], lock: dict[str, Any]) -> dict[str, Any]:
    """Reconcile current vendored source with, but do not rewrite, old evidence."""
    provenance = json.loads(SUCCESSOR_PROVENANCE_PATH.read_text(encoding="utf-8"))
    shellset_qualification = json.loads(SHELLSET_FAIR_QUALIFICATION_PATH.read_text(encoding="utf-8"))
    orbdata_qualification = json.loads(ORBDATA_FAIR_QUALIFICATION_PATH.read_text(encoding="utf-8"))
    historical_absence = provenance.get("source_tree_available_in_current_workspace") is False
    successor_identity = provenance.get("successor_patch_identity")
    capacity = shellset_qualification.get("qualified_runtime", {})
    arcana = orbdata_qualification.get("shellset", {})
    if not source_hashes or not lock.get("vendored_arcana_source_commit"):
        raise SI1Error("current vendored ShellSet source identity is incomplete")
    if not capacity.get("commit") or not capacity.get("executable_sha256"):
        raise SI1Error("historical ShellSet capacity qualification identity is incomplete")
    if not arcana.get("qualified_arcana_commit") or not arcana.get("qualified_patched_executable_sha256"):
        raise SI1Error("historical ARCANA runtime qualification identity is incomplete")
    return {
        "current_vendored_source": {
            "source_commit_claim_from_lock": lock["vendored_arcana_source_commit"],
            "locked_file_count": len(source_hashes),
            "all_locked_hashes_match": True,
        },
        "historical_successor_provenance": {
            "artifact": SUCCESSOR_PROVENANCE_PATH.name,
            "artifact_sha256": sha256(SUCCESSOR_PROVENANCE_PATH),
            "recorded_decision": provenance.get("decision"),
            "recorded_source_tree_unavailable": historical_absence,
            "current_workspace_source_tree_available": True,
            "historical_absence_statement_superseded_by_current_inventory": historical_absence,
            "successor_patch_identity_recorded": successor_identity,
            "interpretation": "The old artifact remains historical evidence; current source hashes are reconciled independently and do not retroactively qualify a successor executable.",
        },
        "historical_shellset_capacity_qualification": {
            "artifact": SHELLSET_FAIR_QUALIFICATION_PATH.name,
            "qualified_source_commit": capacity["commit"],
            "executable_sha256": capacity["executable_sha256"],
            "scope": "CAPACITY_AND_UPSTREAM_EXAMPLE_ONLY",
            "arcana_mechanics_authorized": shellset_qualification.get("authorization_boundary", {}).get("arcana_t0_mechanics_authorized"),
        },
        "historical_arcana_runtime_qualification": {
            "artifact": ORBDATA_FAIR_QUALIFICATION_PATH.name,
            "qualified_arcana_commit": arcana["qualified_arcana_commit"],
            "qualified_patched_executable_sha256": arcana["qualified_patched_executable_sha256"],
            "qualification_decision": orbdata_qualification.get("decision"),
            "shellset_mechanics_executed_in_that_qualification": orbdata_qualification.get("authorization_boundary", {}).get("shellset_mechanics_authorized"),
        },
        "si1_scope": "Current source reconciliation only; does not claim Fair rebuild, successor executable qualification, OrbData execution, or mechanics pass.",
    }


def _unit(lat_deg: np.ndarray, lon_deg: np.ndarray) -> np.ndarray:
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)
    cos_lat = np.cos(lat)
    return np.column_stack((cos_lat * np.cos(lon), cos_lat * np.sin(lon), np.sin(lat)))


def _lat_lon(vector: np.ndarray) -> tuple[float, float]:
    unit = vector / np.linalg.norm(vector)
    return math.degrees(math.asin(float(unit[2]))), math.degrees(math.atan2(float(unit[1]), float(unit[0])))


def canonical_plate_rings(partition_path: Path, forward_rotation: list[list[float]]) -> dict[int, list[tuple[float, float]]]:
    """Trace the explicit 1-degree face partition into oriented closed rings."""
    with np.load(partition_path, allow_pickle=False) as payload:
        required = {
            "face_row", "face_col", "face_plate_id", "boundary_edge_row",
            "boundary_edge_col", "boundary_edge_axis", "boundary_plate_a", "boundary_plate_b",
        }
        if not required.issubset(payload.files):
            raise SI1Error(f"partition payload missing arrays: {sorted(required - set(payload.files))}")
        arrays = {key: np.asarray(payload[key]) for key in required}

    if len(arrays["face_row"]) != 180 * 360:
        raise SI1Error("partition face cardinality is not 64,800")
    if len(arrays["boundary_edge_row"]) != 1983:
        raise SI1Error("partition boundary cardinality is not 1,983")
    plate_grid = np.full((180, 360), -1, dtype=np.int16)
    for row, col, plate in zip(arrays["face_row"], arrays["face_col"], arrays["face_plate_id"]):
        row_i, col_i = int(row), int(col)
        if not (0 <= row_i < 180 and 0 <= col_i < 360) or plate_grid[row_i, col_i] >= 0:
            raise SI1Error("partition has an out-of-range or duplicate face cell")
        plate_grid[row_i, col_i] = int(plate)
    if (plate_grid < 0).any():
        raise SI1Error("partition does not cover the complete 180x360 face grid")
    plate_ids = sorted(int(x) for x in np.unique(arrays["face_plate_id"]))
    if len(plate_ids) != 12:
        raise SI1Error(f"expected 12 ARCANA plate IDs, found {len(plate_ids)}")

    from collections import Counter, defaultdict
    edges: dict[int, list[tuple[tuple[int, int], tuple[int, int]]]] = defaultdict(list)

    def vertex(y: int, x: int) -> tuple[int, int]:
        return (y, 0) if y in (0, 180) else (y, x % 360)

    for row, col, axis, plate_a, plate_b in zip(
        arrays["boundary_edge_row"], arrays["boundary_edge_col"], arrays["boundary_edge_axis"],
        arrays["boundary_plate_a"], arrays["boundary_plate_b"],
    ):
        r, c, ax = int(row), int(col), int(axis)
        if ax == 0:
            left, right = int(plate_grid[r, c]), int(plate_grid[r, (c + 1) % 360])
            start, end = vertex(r, c + 1), vertex(r + 1, c + 1)
            edges[left].append((start, end)); edges[right].append((end, start))
        elif ax == 1:
            south, north = int(plate_grid[r, c]), int(plate_grid[r + 1, c])
            start, end = vertex(r + 1, c), vertex(r + 1, c + 1)
            edges[north].append((start, end)); edges[south].append((end, start))
        else:
            raise SI1Error(f"unsupported boundary axis {ax}")
        edge_sides = {left, right} if ax == 0 else {south, north}
        if edge_sides != {int(plate_a), int(plate_b)}:
            raise SI1Error("boundary edge plate IDs disagree with adjacent faces")

    matrix = np.asarray(forward_rotation, dtype=np.float64)
    if matrix.shape != (3, 3) or not np.isfinite(matrix).all() or abs(np.linalg.det(matrix) - 1.0) > 1e-10:
        raise SI1Error("FEG coordinate rotation is not a finite proper 3x3 rotation")
    result: dict[int, list[tuple[float, float]]] = {}
    for plate in plate_ids:
        plate_edges = edges[plate]
        outgoing: dict[tuple[int, int], tuple[int, int]] = {}
        incoming = Counter(end for _, end in plate_edges)
        for start, end in plate_edges:
            if start in outgoing:
                raise SI1Error(f"plate {plate} outline branches at {start}")
            outgoing[start] = end
        if set(outgoing) != set(incoming) or any(count != 1 for count in incoming.values()):
            raise SI1Error(f"plate {plate} outline is open or has a non-manifold vertex")
        visited: set[tuple[int, int]] = set()
        rings: list[list[tuple[int, int]]] = []
        for start in sorted(outgoing):
            if start in visited:
                continue
            current, ring = start, [start]
            while current not in visited:
                visited.add(current)
                current = outgoing[current]
                ring.append(current)
            if current != start:
                raise SI1Error(f"plate {plate} edge chain does not close")
            rings.append(ring)
        if len(rings) != 1:
            raise SI1Error(f"plate {plate} requires {len(rings)} rings; expected one governed polygon")
        coords: list[tuple[float, float]] = []
        for y, x in rings[0]:
            lat = 90.0 if y == 180 else -90.0 if y == 0 else -90.0 + y
            lon = 0.0 if y in (0, 180) else -180.0 + x
            rotated = matrix @ _unit(np.asarray([lat]), np.asarray([lon]))[0]
            out_lat, out_lon = _lat_lon(rotated)
            coords.append((out_lon, out_lat))
        if len(coords) < 4 or coords[0] != coords[-1]:
            raise SI1Error(f"plate {plate} outline is not a closed polygon")
        result[plate] = coords
    return result


def _plate_symbols(shared_vars: Path) -> list[str]:
    text = shared_vars.read_text(encoding="utf-8")
    match = re.search(r"data\s+names\s*/(.*?)/", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise SI1Error("could not read fixed ShellSet plate-slot symbols")
    symbols = re.findall(r"'([A-Z0-9]{2})'", match.group(1))
    if len(symbols) != 52 or len(set(symbols)) != 52:
        raise SI1Error("ShellSet source no longer declares the expected 52 distinct plate slots")
    return symbols


def _find_empty_outline_anchor(feg_path: Path) -> tuple[float, float]:
    with feg_path.open("r", encoding="ascii") as stream:
        stream.readline()
        counts = stream.readline().split()
        n_nodes = int(counts[0])
        node_lat, node_lon = [], []
        for _ in range(n_nodes):
            fields = stream.readline().split()
            if len(fields) < 3:
                raise SI1Error("FEG node row is truncated while selecting empty-slot outline")
            node_lon.append(float(fields[1])); node_lat.append(float(fields[2]))
    nodes = _unit(np.asarray(node_lat), np.asarray(node_lon))
    candidates = [
        (float(lat), float(lon))
        for lat in np.arange(-88.13, 88.14, 2.731)
        for lon in np.arange(-179.37, 180.0, 5.213)
    ]
    best: tuple[float, float, float] | None = None
    for offset in range(0, len(candidates), 24):
        batch = candidates[offset:offset + 24]
        points = _unit(np.asarray([x[0] for x in batch]), np.asarray([x[1] for x in batch]))
        nearest = np.arccos(np.clip(points @ nodes.T, -1.0, 1.0)).min(axis=1)
        index = int(np.argmax(nearest))
        candidate = (float(nearest[index]), batch[index][0], batch[index][1])
        if best is None or candidate[0] > best[0]:
            best = candidate
    if best is None or best[0] < math.radians(0.1):
        raise SI1Error("cannot place unused ShellSet slot outlines safely away from all FEG nodes")
    return best[1], best[2]


def write_plate_outlines(path: Path, rings: dict[int, list[tuple[float, float]]], symbols: list[str], feg_path: Path) -> dict[str, Any]:
    if len(rings) != 12:
        raise SI1Error("exactly 12 ARCANA rings are required")
    mapping = {str(plate): symbols[index] for index, plate in enumerate(sorted(rings))}
    if any(len(ring) > 1250 for ring in rings.values()):
        raise SI1Error("an ARCANA outline exceeds ShellSet's nPBnd=1250 input capacity")
    center_lat, center_lon = _find_empty_outline_anchor(feg_path)
    epsilon = 0.01
    anchor_clearance = _empty_anchor_clearance(feg_path, center_lat, center_lon)
    # The spherical angular radius of a +/-epsilon degree square is bounded
    # by its diagonal; a much larger clearance proves no FEG node is inside it.
    if anchor_clearance <= math.radians(math.sqrt(2.0) * epsilon):
        raise SI1Error("empty compatibility outline is not proven node-free")
    dummy = [
        (center_lon - epsilon, center_lat - epsilon),
        (center_lon + epsilon, center_lat - epsilon),
        (center_lon + epsilon, center_lat + epsilon),
        (center_lon - epsilon, center_lat + epsilon),
        (center_lon - epsilon, center_lat - epsilon),
    ]
    rows: list[str] = []
    for plate in sorted(rings):
        rows.append(mapping[str(plate)])
        rows.extend(f"{lon:+.10f},{lat:+.10f}" for lon, lat in rings[plate])
        rows.append("***")
    for symbol in symbols[12:]:
        rows.append(symbol)
        rows.extend(f"{lon:+.10f},{lat:+.10f}" for lon, lat in dummy)
        rows.append("***")
    path.write_text("\n".join(rows) + "\n", encoding="ascii", newline="\n")
    return {
        "canonical_plate_id_to_shellset_slot": mapping,
        "canonical_plate_polygons": len(rings),
        "empty_compatibility_slots": 40,
        "empty_slot_semantics": "repeated small runtime-only outlines placed in a verified node-free region; no FEG node may be assigned to these slots",
        "empty_slot_anchor_lat_lon_degrees": [center_lat, center_lon],
        "empty_slot_minimum_node_clearance_degrees": math.degrees(anchor_clearance),
        "empty_slot_node_free_verified": True,
        "max_outline_vertices": max(len(ring) for ring in rings.values()),
        "geometry_authority": "NUMERICAL_RUNTIME_SUPPORT_ONLY; source-derived cell-edge rings transformed by the manifested FEG rigid frame",
        "geometry_approximation": "canonical latitude small-circle cell edges are represented by ShellSet great-circle outline segments between vertices; no physical-resolution promotion or boundary-type semantics",
    }


def _empty_anchor_clearance(feg_path: Path, lat: float, lon: float) -> float:
    with feg_path.open("r", encoding="ascii") as stream:
        stream.readline(); n_nodes = int(stream.readline().split()[0])
        node_lon, node_lat = [], []
        for _ in range(n_nodes):
            fields = stream.readline().split(); node_lon.append(float(fields[1])); node_lat.append(float(fields[2]))
    center = _unit(np.asarray([lat]), np.asarray([lon]))[0]
    nodes = _unit(np.asarray(node_lat), np.asarray(node_lon))
    return float(np.arccos(np.clip(nodes @ center, -1.0, 1.0)).min())


def write_input_files(input_dir: Path, *, feg_name: str = "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg") -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "SI1 ARCANA engineering input set",
        "SI1_ENGINEERING_REFERENCE.in",
        feg_name,
        "X",
        "------------------------------------------------------------------------------------------",
        "",
        "OrbData inputs unused; pre-materialized ARCANA FEG/package",
        "X",
        "X",
        "X",
        "X",
        "------------------------------------------------------------------------------------------",
        "",
        "Shells (Main work loop):",
        "SI1_NO_VELOCITY.bcs",
        "ARCANA_PLATE_OUTLINES.dig",
        "SI1_UNUSED_PLATE_PAIR.dig",
        "------------------------------",
        "X",
        "X",
        "X",
        "------------------------------------------------------------------------------------------",
        "",
        "Shells (Final OR Non-Iterating run):",
        "SI1_NO_VELOCITY.bcs",
        "ARCANA_PLATE_OUTLINES.dig",
        "SI1_UNUSED_PLATE_PAIR.dig",
        "------------------------------",
        "X",
        "X",
        "X",
        "------------------------------------------------------------------------------------------",
        "",
        "OrbScore unused; engineering solve output only",
        "X",
        "X",
        "X",
        "X",
        "X",
        "X",
        "------------------------------------------------------------------------------------------",
    ]
    if len(lines) != 41:
        raise AssertionError("InputFiles.in parser layout changed")
    (input_dir / "InputFiles.in").write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    (input_dir / "ListInput.in").write_text(
        "1,1\nfFric\n---------- Var1:\n0.10\n----------\n", encoding="ascii", newline="\n"
    )
    (input_dir / "SI1_NO_VELOCITY.bcs").write_text(
        "ARCANA_SI1_GLOBAL_CONTINUUM_NO_VELOCITY_CONSTRAINTS\n", encoding="ascii", newline="\n"
    )
    (input_dir / "SI1_UNUSED_PLATE_PAIR.dig").write_text(
        "SI1_UNUSED_NO_FAULT_BOUNDARY_GEOMETRY\n", encoding="ascii", newline="\n"
    )


def _preflight_source(source: Path, destination: Path) -> None:
    text = source.read_text(encoding="utf-8")
    declaration_anchor = "       INTEGER nRank, nCodiagonals, nKRows, iDiagonal\n       COMMON  nRank, nCodiagonals, nKRows, iDiagonal"
    declaration_replacement = declaration_anchor + "\n       CHARACTER(LEN=8) :: si1_preflight\n       INTEGER :: si1_env_status"
    if text.count(declaration_anchor) != 1:
        raise SI1Error("SHELLS source declaration anchor changed; refusing preflight instrumentation")
    text = text.replace(declaration_anchor, declaration_replacement, 1)
    call = re.compile(r"(       CALL KSize \(brief, iUnitP, iUnitLog, mxEl, mxFEl, mxNode, &.*?jCol1, jCol2\)\s*!)", re.DOTALL)
    matches = list(call.finditer(text))
    if len(matches) != 1:
        raise SI1Error("could not locate the unique KSize call for pre-allocation instrumentation")
    stop = (
        "\n       CALL GET_ENVIRONMENT_VARIABLE('ARCANA_SI1_PREFLIGHT_ONLY', &\n"
        "     &      si1_preflight, STATUS=si1_env_status)\n"
        "       IF (si1_env_status == 0 .AND. TRIM(si1_preflight) == '1') THEN\n"
        "          WRITE(*,'(A,I0,1X,A,I0,1X,A,I0,1X,A,ES24.16)') &\n"
        "     &         'SI1_KSIZE nRank=', nRank, 'nKRows=', nKRows, &\n"
        "     &         'nCodiagonals=', nCodiagonals, 'matrix_bytes=', &\n"
        "     &         8.0D0 * DBLE(nKRows) * DBLE(nRank)\n"
        "          CALL FatalError('SI1_KSIZE_PREFLIGHT_STOP', ThID)\n"
        "          RETURN\n"
        "       END IF\n"
    )
    match = matches[0]
    text = text[:match.end()] + stop + text[match.end():]
    destination.write_text(text, encoding="utf-8", newline="\n")


def _copy_build_tree(source_root: Path, dest: Path, *, preflight: bool) -> None:
    dest.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source_root / "Makefile", dest / "Makefile")
    src_out = dest / "src"
    src_out.mkdir()
    for path in sorted((source_root / "src").glob("*.f90")):
        target = src_out / path.name
        if preflight and path.name == "SHELLS_v5.0.f90":
            _preflight_source(path, target)
        else:
            shutil.copy2(path, target)


def _solver_env() -> dict[str, str]:
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    env["OPENBLAS_NUM_THREADS"] = "1"
    return env


def _stage_case(run_dir: Path, *, plate_metadata_path: Path,
                parameter_reference: Path) -> None:
    input_dir = run_dir / "INPUT"
    write_input_files(input_dir)
    shutil.copy2(FEG_PATH, input_dir / FEG_PATH.name)
    shutil.copy2(RUNTIME_PATH, input_dir / RUNTIME_PATH.name)
    shutil.copy2(parameter_reference, input_dir / "SI1_ENGINEERING_REFERENCE.in")
    shutil.copy2(plate_metadata_path, input_dir / "ARCANA_PLATE_OUTLINES.dig")


def _capture_run_log(run_dir: Path, output_dir: Path, prefix: str) -> list[str]:
    copied: list[str] = []
    for candidate in sorted(run_dir.rglob("*")):
        if candidate.is_file() and (candidate.suffix.lower() in {".txt", ".log", ".22", ".24"} or candidate.name.startswith("fort_")):
            rel = candidate.relative_to(run_dir)
            dest = output_dir / "logs" / prefix / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, dest)
            copied.append(dest.relative_to(output_dir).as_posix())
    return copied


def _parse_finite_velocity_files(run_dir: Path) -> dict[str, Any]:
    candidates = sorted(p for p in run_dir.rglob("*") if p.is_file() and (p.name.endswith(".22") or p.name.endswith(".24")))
    if not candidates:
        return {"status": "NO_SHELLS_VELOCITY_OUTPUT_FOUND", "files": []}
    result: dict[str, Any] = {"status": "PASS", "files": []}
    for path in candidates:
        text = path.read_text(encoding="ascii", errors="replace")
        values: list[float] = []
        malformed = False
        for token in re.findall(r"[^\s,]+", text):
            if token.strip("()") in {"", "-"}:
                continue
            if FLOAT_RE.match(token):
                values.append(float(token.replace("D", "E").replace("d", "e")))
            elif re.search(r"\*{3,}|nan|inf", token, re.IGNORECASE):
                malformed = True
        finite = bool(values) and all(math.isfinite(value) for value in values)
        if not finite or malformed:
            result["status"] = "FAIL_NONFINITE_OR_UNPARSEABLE_SHELLS_OUTPUT"
        result["files"].append({"path": path.relative_to(run_dir).as_posix(), "numeric_values": len(values), "all_finite": finite, "overflow_or_nonfinite_marker": malformed, "sha256": sha256(path), "_values": values})
    return result


def _compare_output_sets(first: dict[str, Any], second: dict[str, Any], abs_tol: float, rel_tol: float) -> dict[str, Any]:
    f = {item["path"]: item for item in first.get("files", [])}
    s = {item["path"]: item for item in second.get("files", [])}
    if set(f) != set(s):
        return {"status": "FAIL_OUTPUT_FILE_SET_CHANGED", "first_files": sorted(f), "second_files": sorted(s)}
    max_abs = 0.0
    max_rel = 0.0
    compared = 0
    for key in sorted(f):
        left_values = f[key].get("_values", [])
        right_values = s[key].get("_values", [])
        if len(left_values) != len(right_values):
            return {"status": "FAIL_NUMERIC_VALUE_COUNT_CHANGED", "file": key,
                    "first_count": len(left_values), "second_count": len(right_values)}
        for left, right in zip(left_values, right_values):
            delta = abs(left - right)
            scale = max(abs(left), abs(right))
            relative = delta / scale if scale else 0.0
            max_abs = max(max_abs, delta)
            max_rel = max(max_rel, relative)
            compared += 1
            if delta > abs_tol and relative > rel_tol:
                return {"status": "FAIL_NUMERIC_OUTPUT_OUTSIDE_TOLERANCE", "file": key,
                        "compared_values": compared, "max_abs": max_abs, "max_rel": max_rel}
    return {"status": "PASS_NUMERICALLY_REPRODUCIBLE", "files": sorted(f),
            "compared_values": compared, "max_abs": max_abs, "max_rel": max_rel,
            "tolerances": {"absolute": abs_tol, "relative": rel_tol}}


def _public_output_validation(parsed: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": parsed.get("status"),
        "files": [
            {key: value for key, value in item.items() if key != "_values"}
            for item in parsed.get("files", [])
        ],
    }


def _converged(log_text: str) -> bool:
    return re.search(r"\bCONVERGED\s*!{3,}", log_text, flags=re.IGNORECASE) is not None


def _copy_executable_and_inputs(build_dir: Path, run_dir: Path, plate_path: Path,
                                parameter_reference: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(build_dir / "ShellSet.exe", run_dir / "ShellSet.exe")
    _stage_case(run_dir, plate_metadata_path=plate_path, parameter_reference=parameter_reference)


def _write_failure(output_dir: Path, decision: str, message: str, baseline: dict[str, Any]) -> None:
    result = dict(baseline)
    result.update({"decision": decision, "failure": message})
    canonical_json(output_dir / "SI1_RESULT.json", result)


def _seal_output_manifest(output_dir: Path) -> None:
    entries = []
    for path in sorted(p for p in output_dir.rglob("*") if p.is_file() and p.name != "SI1_ARTIFACT_MANIFEST.json"):
        relative = path.relative_to(output_dir).as_posix()
        if relative == "SI1_RESULT.json":
            role = "RUN_DECISION_AND_METRICS"
        elif relative.startswith("logs/"):
            role = "BUILD_OR_RUNTIME_LOG"
        elif relative.startswith("build_"):
            role = "ISOLATED_BUILD_ARTIFACT"
        elif relative.startswith(("solve_run_", "preflight_run/")):
            role = "ISOLATED_STAGED_INPUT_OR_SOLVER_OUTPUT"
        else:
            role = "RUNNER_GENERATED_EVIDENCE"
        entries.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path), "role": role})
    canonical_json(output_dir / "SI1_ARTIFACT_MANIFEST.json", {
        "schema": "arcana_worldsim.r6.shells_si1_artifact_manifest.v1",
        "membership": "all regular files recursively except this manifest",
        "artifacts": entries,
    })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shellset-root", type=Path, default=SHELLSET_SOURCE)
    parser.add_argument("--partition-payload", type=Path, required=True,
                        help="explicit R6_T0_VECTOR_PLATE_PARTITION.npz; its SHA must match the governed manifest")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="new isolated evidence/work directory; must not exist")
    parser.add_argument("--memory-cap-gib", type=float, required=True,
                        help="per-process RLIMIT_AS in GiB, applied to preflight and solver MPI processes")
    parser.add_argument("--runtime-limit-seconds", type=int, required=True,
                        help="wall-clock timeout for each MPI preflight/solve invocation")
    args = parser.parse_args(argv)

    out = args.output_dir.resolve()
    if out.exists():
        print(f"SI1 error: output directory already exists: {out}", file=sys.stderr)
        return 2
    if " " in str(out) or len(str(out)) >= 90:
        print("SI1 error: ShellSet -Dir requires a space-free path shorter than 90 characters", file=sys.stderr)
        return 2
    if not sys.platform.startswith("linux"):
        print("SI1 error: this engineering runner is for Linux/Fair only", file=sys.stderr)
        return 2
    if resource is None:
        print("SI1 error: Linux resource limits are unavailable", file=sys.stderr)
        return 2
    if args.memory_cap_gib <= 0 or args.runtime_limit_seconds <= 0:
        print("SI1 error: memory and runtime limits must be positive", file=sys.stderr)
        return 2
    out.mkdir(parents=True)
    git_identity = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    source_revision = git_identity.stdout.strip()
    if git_identity.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        _write_failure(out, "BLOCKED_SI1_SOURCE_REVISION_UNAVAILABLE",
                       "Git did not provide a full 40-character source commit SHA", {})
        _seal_output_manifest(out)
        print("BLOCKED_SI1_SOURCE_REVISION_UNAVAILABLE", file=sys.stderr)
        return 2
    result: dict[str, Any] = {
        "schema": "arcana_worldsim.r6.shells_si1_result.v1",
        "case_id": "ARCANA_SHELLS_GLOBAL_CONTINUUM_ENGINEERING_V0",
        "classification": "NON_CANONICAL_ENGINEERING_CANDIDATE",
        "source_revision": source_revision,
        "memory_cap_gib_per_process": args.memory_cap_gib,
        "runtime_limit_seconds_per_invocation": args.runtime_limit_seconds,
        "status": {
            "ARCANA_INPUT_ARTIFACTS_VERIFIED": False,
            "SHELLSET_SOURCE_RECONCILED": False,
            "ORBDATA_CONSUMER_PASS": "NOT_RUN_PREMATERIALIZED_FEG_PACKAGE",
            "SHELLS_ASSEMBLY_PASS": False,
            "SHELLS_GLOBAL_GAUGE_DIAGNOSTIC_PASS": "UNASSESSED_NO_BC_RUN_REQUIRED",
            "SHELLS_MECHANICAL_SOLVE_PASS": False,
            "ENGINE_OUTPUT_NORMALIZATION_PASS": False,
            "ENGINEERING_REPRODUCIBILITY_PASS": False,
        },
        "preserved_gates": {
            "canonical_state_changed": False,
            "WORLD_HISTORY_changed": False,
            "T2_created": False,
            "forward_evolution_authorized": False,
            "canonical_mechanics_authorized": False,
        },
    }
    try:
        case = json.loads(CASE_PATH.read_text(encoding="utf-8"))
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        partition_manifest = json.loads(PARTITION_MANIFEST_PATH.read_text(encoding="utf-8"))
        feg_manifest = json.loads(FEG_MANIFEST_PATH.read_text(encoding="utf-8"))
        runtime_manifest = json.loads(RUNTIME_MANIFEST_PATH.read_text(encoding="utf-8"))
        if sha256(FEG_PATH) != case["feg"]["sha256"] or sha256(RUNTIME_PATH) != case["runtime_package"]["sha256"]:
            raise SI1Error("FEG/runtime package SHA does not match the SI1 governed input lock")
        if sha256(args.partition_payload.resolve()) != case["partition"]["sha256"]:
            raise SI1Error("canonical partition payload SHA does not match the governed manifest")
        if sha256(RUNTIME_MANIFEST_PATH) != case["runtime_package"]["manifest_sha256"]:
            raise SI1Error("runtime package manifest SHA does not match the SI1 lock")
        if partition_manifest.get("payload", {}).get("sha256") != case["partition"]["sha256"]:
            raise SI1Error("partition payload and manifest identity disagree")
        if feg_manifest.get("production_feg", {}).get("header", {}).get("nRealN") != 64442:
            raise SI1Error("FEG manifest node count is not the expected ARCANA 64,442")
        if runtime_manifest.get("node_count") != 64442 or runtime_manifest.get("invalid_count") != 0:
            raise SI1Error("runtime package node coverage is incomplete")
        result["status"]["ARCANA_INPUT_ARTIFACTS_VERIFIED"] = True

        source_root = args.shellset_root.resolve()
        source_hashes = verify_source_lock(source_root, lock)
        parameter_reference = source_root / "INPUT/iEarth5-049.in"
        if sha256(parameter_reference) != lock["parameter_reference_sha256"]:
            raise SI1Error("ShellSet engineering parameter reference changed from the checked-in source lock")
        result["source_reconciliation"] = reconcile_source_evidence(source_hashes, lock)
        result["status"]["SHELLSET_SOURCE_RECONCILED"] = True
        result["source_identity"] = {"vendored_arcana_source_commit": lock["vendored_arcana_source_commit"], "file_hashes": source_hashes}
        result["parameter_reference"] = {"classification": "ENGINEERING_SOLVER_REFERENCE_NOT_ARCANA_GEOLOGY", "sha256": sha256(parameter_reference)}

        matrix = feg_manifest.get("runtime_coordinate_frame", {}).get("forward_rotation_matrix")
        rings = canonical_plate_rings(args.partition_payload.resolve(), matrix)
        symbols = _plate_symbols(source_root / "src/MOD_SharedVars.f90")
        geometry_path = out / "ARCANA_PLATE_OUTLINES.dig"
        plate_metadata = write_plate_outlines(geometry_path, rings, symbols, FEG_PATH)
        result["runtime_plate_support"] = plate_metadata
        result["runtime_plate_support"]["outline_sha256"] = sha256(geometry_path)

        commands: dict[str, Any] = {}
        for tool in ("nvfortran", "mpifort", "mpiexec"):
            probe = subprocess.run([tool, "--version"], capture_output=True, text=True, check=False)
            output = (probe.stdout + probe.stderr).strip()
            commands[tool] = {"returncode": probe.returncode, "version_first_line": output.splitlines()[0] if output else "NO_VERSION_OUTPUT", "version_excerpt": output[:2000]}
            if probe.returncode != 0:
                raise SI1Error(f"required compiler/launcher unavailable: {tool}")
        if "nvfortran" not in (commands["mpifort"]["version_excerpt"] + commands["nvfortran"]["version_excerpt"]).lower():
            raise SI1Error("mpifort does not identify the NVHPC/NVFortran toolchain")
        canonical_json(out / "TOOLCHAIN.json", commands)

        preflight_build = out / "build_preflight"
        _copy_build_tree(source_root, preflight_build, preflight=True)
        build = run_checked(["make", "ShellSet"], cwd=preflight_build, timeout=args.runtime_limit_seconds,
                            stdout_path=out / "logs/build_preflight.log", env=_solver_env())
        if build.returncode != 0 or not (preflight_build / "ShellSet.exe").is_file():
            raise SI1Error("isolated NVHPC preflight build failed")
        preflight_dir = out / "preflight_run"
        _copy_executable_and_inputs(preflight_build, preflight_dir, geometry_path, parameter_reference)
        env = _solver_env(); env["ARCANA_SI1_PREFLIGHT_ONLY"] = "1"
        command = ["mpiexec", "-n", "2", "./ShellSet.exe", "-Iter", "1", "-InOpt", "List", "-Dir", "RUN_OUTPUT", "-V"]
        try:
            preflight = run_checked(command, cwd=preflight_dir, timeout=args.runtime_limit_seconds,
                                    stdout_path=out / "logs/preflight_stdout.log", env=env,
                                    address_space_bytes=int(args.memory_cap_gib * (1024 ** 3)))
        except subprocess.TimeoutExpired as exc:
            raise SI1Error("KSize preflight exceeded the operator wall-clock limit") from exc
        preflight_text = preflight.stdout or ""
        ksize = K_SIZE_RE.search(preflight_text)
        if not ksize:
            raise SI1Error("KSize preflight did not emit the expected pre-allocation diagnostic")
        n_rank, n_krows, n_codiags = (int(ksize.group(i)) for i in (1, 2, 3))
        matrix_bytes = float(ksize.group(4).replace("D", "E").replace("d", "e"))
        actual_formula = 8 * n_rank * n_krows
        if abs(matrix_bytes - actual_formula) > 0.5:
            raise SI1Error("KSize matrix byte diagnostic disagrees with 8*nRank*nKRows")
        matrix_gib = matrix_bytes / (1024 ** 3)
        result["ksize_preflight"] = {"nRank": n_rank, "nKRows": n_krows, "nCodiagonals": n_codiags,
                                     "matrix_bytes": int(matrix_bytes), "matrix_gib": matrix_gib,
                                     "mpi_ranks": 2, "aggregate_matrix_bytes_upper_estimate": int(matrix_bytes * 2),
                                     "aggregate_matrix_gib_upper_estimate": matrix_gib * 2,
                                     "preflight_exit_code": preflight.returncode,
                                     "stopped_before_stiffness_allocation": "SI1_KSIZE_PREFLIGHT_STOP" in preflight_text}
        if not result["ksize_preflight"]["stopped_before_stiffness_allocation"]:
            raise SI1Error("preflight did not confirm stop before stiffness allocation")
        if matrix_bytes > args.memory_cap_gib * (1024 ** 3):
            result["decision"] = "BLOCKED_SI1_MATRIX_EXCEEDS_EXPLICIT_MEMORY_CAP"
            canonical_json(out / "SI1_RESULT.json", result)
            _seal_output_manifest(out)
            print(result["decision"])
            return 3

        # Rebuild from a fresh exact-source copy with no diagnostic source changes.
        solve_build = out / "build_solver"
        _copy_build_tree(source_root, solve_build, preflight=False)
        solve_build_result = run_checked(["make", "ShellSet"], cwd=solve_build, timeout=args.runtime_limit_seconds,
                                         stdout_path=out / "logs/build_solver.log", env=_solver_env())
        if solve_build_result.returncode != 0 or not (solve_build / "ShellSet.exe").is_file():
            raise SI1Error("isolated normal ShellSet build failed")

        solve_dir = out / "solve_run_1"
        _copy_executable_and_inputs(solve_build, solve_dir, geometry_path, parameter_reference)
        solve_command = ["mpiexec", "-n", "2", "./ShellSet.exe", "-Iter", "1", "-InOpt", "List", "-Dir", "RUN_OUTPUT", "-V"]
        try:
            solve = run_checked(solve_command, cwd=solve_dir, timeout=args.runtime_limit_seconds,
                                stdout_path=out / "logs/solve_1_stdout.log", env=_solver_env(),
                                address_space_bytes=int(args.memory_cap_gib * (1024 ** 3)))
        except subprocess.TimeoutExpired as exc:
            raise SI1Error("global continuum solve exceeded the operator wall-clock limit") from exc
        parsed_1 = _parse_finite_velocity_files(solve_dir / "RUN_OUTPUT")
        result["solve_1"] = {"returncode": solve.returncode, "logs": _capture_run_log(solve_dir, out, "solve_1"),
                             "output_validation": _public_output_validation(parsed_1),
                             "command": solve_command}
        assembly_log = (out / "logs/solve_1_stdout.log").read_text(encoding="utf-8", errors="replace")
        combined_logs = assembly_log
        for log_path in (out / "logs/solve_1").rglob("*") if (out / "logs/solve_1").exists() else []:
            if log_path.is_file() and log_path.suffix.lower() in {".txt", ".log"}:
                combined_logs += "\n" + log_path.read_text(encoding="utf-8", errors="replace")
        error_files = [str(path.relative_to(solve_dir).as_posix()) for path in solve_dir.rglob("FatalError.txt")]
        error_files += [str(path.relative_to(solve_dir).as_posix()) for path in solve_dir.rglob("ModelError.txt")]
        error_marker_in_logs = re.search(r"\b(?:FatalError|ModelError)\b", combined_logs) is not None
        assembly_seen = "Size of banded linear system" in combined_logs or "nKRows" in combined_logs
        result["solve_1"]["convergence_marker_found"] = _converged(combined_logs)
        result["solve_1"]["error_files"] = error_files
        result["solve_1"]["error_marker_in_logs"] = error_marker_in_logs
        result["status"]["SHELLS_ASSEMBLY_PASS"] = assembly_seen and not error_files and not error_marker_in_logs
        result["status"]["SHELLS_GLOBAL_GAUGE_DIAGNOSTIC_PASS"] = "NOT_ESTABLISHED_NO_VELOCITY_BC_NULLSPACE_ANALYSIS_REQUIRED"
        result["status"]["SHELLS_MECHANICAL_SOLVE_PASS"] = (
            result["status"]["SHELLS_ASSEMBLY_PASS"] and
            solve.returncode == 0 and parsed_1["status"] == "PASS"
            and result["solve_1"]["convergence_marker_found"] and not error_files and not error_marker_in_logs
        )
        result["status"]["ENGINE_OUTPUT_NORMALIZATION_PASS"] = "PENDING_FIELD_SEMANTICS_AND_UNIT_REVIEW"
        result["status"]["ENGINEERING_REPRODUCIBILITY_PASS"] = False
        if result["status"]["SHELLS_MECHANICAL_SOLVE_PASS"]:
            # A second fresh process/run is required. Exact bytes are not a
            # criterion; compare the finite numeric output at declared tolerances.
            solve_dir_2 = out / "solve_run_2"
            _copy_executable_and_inputs(solve_build, solve_dir_2, geometry_path, parameter_reference)
            solve_2 = run_checked(solve_command, cwd=solve_dir_2, timeout=args.runtime_limit_seconds,
                                  stdout_path=out / "logs/solve_2_stdout.log", env=_solver_env(),
                                  address_space_bytes=int(args.memory_cap_gib * (1024 ** 3)))
            parsed_2 = _parse_finite_velocity_files(solve_dir_2 / "RUN_OUTPUT")
            log_2 = (out / "logs/solve_2_stdout.log").read_text(encoding="utf-8", errors="replace")
            logs_2 = _capture_run_log(solve_dir_2, out, "solve_2")
            for log_path in (out / "logs/solve_2").rglob("*") if (out / "logs/solve_2").exists() else []:
                if log_path.is_file() and log_path.suffix.lower() in {".txt", ".log"}:
                    log_2 += "\n" + log_path.read_text(encoding="utf-8", errors="replace")
            tol = case["solver"]["reproducibility_tolerance"]
            reproducibility = _compare_output_sets(parsed_1, parsed_2, tol["absolute"], tol["relative"])
            converged_2 = _converged(log_2)
            result["solve_2"] = {"returncode": solve_2.returncode, "logs": logs_2,
                                  "output_validation": _public_output_validation(parsed_2),
                                  "convergence_marker_found": converged_2, "command": solve_command}
            result["engineering_reproducibility"] = reproducibility
            result["status"]["ENGINEERING_REPRODUCIBILITY_PASS"] = (
                solve_2.returncode == 0 and parsed_2["status"] == "PASS" and converged_2
                and reproducibility["status"] == "PASS_NUMERICALLY_REPRODUCIBLE"
            )
            result["decision"] = (
                "SHELLS_ENGINEERING_SOLVE_CONVERGED_GAUGE_AND_OUTPUT_REVIEW_REQUIRED"
                if result["status"]["ENGINEERING_REPRODUCIBILITY_PASS"]
                else "BLOCKED_SI1_SECOND_RUN_OR_NUMERIC_REPRODUCIBILITY_FAILED"
            )
        else:
            result["decision"] = "BLOCKED_SI1_NO_CONVERGED_FINITE_MECHANICAL_SOLUTION_OR_ASSEMBLY"
        canonical_json(out / "SI1_RESULT.json", result)
        _seal_output_manifest(out)
        print(result["decision"])
        return 0 if result["status"]["ENGINEERING_REPRODUCIBILITY_PASS"] else 4
    except Exception as exc:  # Fail closed and retain compact run evidence.
        _write_failure(out, "BLOCKED_SI1_ENGINEERING_RUNNER", str(exc), result)
        _seal_output_manifest(out)
        print(f"BLOCKED_SI1_ENGINEERING_RUNNER: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
