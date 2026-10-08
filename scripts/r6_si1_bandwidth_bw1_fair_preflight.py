#!/usr/bin/env python3
"""Build and run only the fail-closed SI1-BW1 KSize Fair preflight.

The sole executable built by this runner contains an unconditional ERROR STOP
immediately after KSize. This runner has no normal-solve mode or executable
override. It is intended for Linux/Fair; Windows can run its unit tests only.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))


class _LazyModule:
    """Keep source-contract tests importable without the Fair NumPy/SciPy stack."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.module: Any | None = None

    def __getattr__(self, name: str) -> Any:
        if self.module is None:
            self.module = importlib.import_module(self.name)
        return getattr(self.module, name)


si1 = _LazyModule("r6_shells_si1_engineering_solve")
bw0 = _LazyModule("arcana_worldsim.r6.si1_bandwidth")
bw1 = _LazyModule("arcana_worldsim.r6.si1_bandwidth_bw1")
np = _LazyModule("numpy")
DEFAULT_FEG = ROOT / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
DEFAULT_FEG_MANIFEST = ROOT / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"
DEFAULT_PACKAGE = ROOT / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
DEFAULT_PACKAGE_MANIFEST = ROOT / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json"
BW1_ROOT = ROOT / "outputs" / "r6_si1_bandwidth_bw1"


SHELLSET_ROOT = ROOT / "external" / "ShellSet-v1.1.0"
LOCK_PATH = ROOT / "configs" / "r6_shells_si1" / "shellset_source_lock.json"
PARTITION_PATH = ROOT / "R6_T0_VECTOR_PLATE_PARTITION.npz"
PARTITION_MANIFEST_PATH = ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"
BW1_REPORT_PATH = BW1_ROOT / "reports" / "BW1_REPORT.json"
EXPECTED_NODES = 64_442
EXPECTED_TRIANGLES = 128_880
EXPECTED_FIELDS = 51
EXPECTED_KSIZE = {
    "nRank": 128_884,
    "nCodiagonals": 727,
    "nKRows": 2_182,
    "matrix_bytes": 2_249_799_104,
}
MPI_RANKS = 2
MEMORY_CAP_GIB_PER_PROCESS = 32
TIMEOUT_SECONDS = 1_800
PREFLIGHT_MARKER = "BW1_PREFLIGHT_STOP_BEFORE_STIFFNESS"
def _shared_ksize_pattern() -> re.Pattern[str]:
    helper_path = ROOT / "scripts" / "r6_shells_si1_engineering_solve.py"
    tree = ast.parse(helper_path.read_text(encoding="utf-8"), filename=str(helper_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "K_SIZE_RE" for target in node.targets
        ):
            call = node.value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "compile" and call.args:
                pattern = ast.literal_eval(call.args[0])
                if isinstance(pattern, str):
                    return re.compile(pattern)
    raise RuntimeError("shared SI1 K_SIZE_RE contract is missing or unsupported")


K_SIZE_RE = _shared_ksize_pattern()
ERROR_BEFORE_KSIZE_RE = re.compile(
    r"(?im)(?:^|\b)(?:FATAL\s+ERROR|ERROR\s+STOP|MPI_ABORT|NVFORTRAN-S-|"
    r"FORTRAN\s+RUNTIME\s+ERROR|SEGMENTATION\s+FAULT|SIGSEGV)(?:\b|:)"
)
SOLVE_OUTPUT_RE = re.compile(r"(?i)\b(?:CONVERGED\s*!{3,}|SHELLS\s+MECHANICAL\s+SOLVE)\b")


class BW1PreflightError(RuntimeError):
    """Fail-closed BW1 Fair preflight failure."""


def _edge_table(*args: Any, **kwargs: Any) -> Any:
    return bw0._edge_table(*args, **kwargs)


def _ksize(*args: Any, **kwargs: Any) -> Any:
    return bw0._ksize(*args, **kwargs)


def _spherical_geometry(*args: Any, **kwargs: Any) -> Any:
    return bw0._spherical_geometry(*args, **kwargs)


def parse_shellset_feg(*args: Any, **kwargs: Any) -> Any:
    return bw0.parse_shellset_feg(*args, **kwargs)


def validate_runtime_package(*args: Any, **kwargs: Any) -> Any:
    return bw0.validate_runtime_package(*args, **kwargs)


def _parse_runtime(*args: Any, **kwargs: Any) -> Any:
    return bw1._parse_runtime(*args, **kwargs)


def _read_feg_full(*args: Any, **kwargs: Any) -> Any:
    return bw1._read_feg_full(*args, **kwargs)


def _roundtrip_check(*args: Any, **kwargs: Any) -> Any:
    return bw1._roundtrip_check(*args, **kwargs)


def _verify_authorities(*args: Any, **kwargs: Any) -> Any:
    return bw1._verify_authorities(*args, **kwargs)


def verify_output_manifest(*args: Any, **kwargs: Any) -> Any:
    return bw1.verify_output_manifest(*args, **kwargs)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_sha256(path: Path, expected: str, label: str) -> str:
    if not path.is_file():
        raise BW1PreflightError(f"required {label} is missing: {path}")
    actual = _sha256(path)
    if actual != expected:
        raise BW1PreflightError(f"{label} SHA256 mismatch: expected {expected}, found {actual}")
    return actual


def _instrumentation_anchor(text: str) -> tuple[re.Match[str], re.Match[str]]:
    call_lines = list(re.finditer(r"(?im)^\s*CALL\s+KSize\b", text))
    if len(call_lines) != 1:
        raise BW1PreflightError(f"expected exactly one KSize call, found {len(call_lines)}")
    call = re.search(
        r"(?im)^\s*CALL\s+KSize\s*\(\s*brief\s*,\s*iUnitP\s*,\s*iUnitLog\s*,"
        r"[\s\S]*?jCol1\s*,\s*jCol2\s*\)[ \t]*![^\r\n]*$",
        text,
    )
    if call is None:
        raise BW1PreflightError("unique KSize call no longer matches the locked signature")
    allocations = list(re.finditer(r"(?im)^\s*ALLOCATE\s*\(\s*stiff\s*\(", text))
    if len(allocations) != 1:
        raise BW1PreflightError(f"expected exactly one active stiffness allocation, found {len(allocations)}")
    if call.end() >= allocations[0].start():
        raise BW1PreflightError("stiffness allocation does not follow KSize in this source")
    return call, allocations[0]


def instrument_source_text(text: str) -> tuple[str, dict[str, Any]]:
    """Add one unconditional KSize report + ERROR STOP to a disposable source copy."""
    call, allocation = _instrumentation_anchor(text)
    if PREFLIGHT_MARKER in text or "BW1_KSIZE" in text:
        raise BW1PreflightError("source already contains BW1 instrumentation marker")
    line_end = text.find("\n", call.end())
    if line_end < 0:
        raise BW1PreflightError("KSize call has no terminating newline")
    block = (
        "       WRITE(*,'(A,I0,1X,A,I0,1X,A,I0,1X,A,I0)') &\n"
        "     &      'SI1_KSIZE nRank=', nRank, 'nKRows=', nKRows, &\n"
        "     &      'nCodiagonals=', nCodiagonals, 'matrix_bytes=', &\n"
        "     &      INT(8.0D0 * DBLE(nKRows) * DBLE(nRank), KIND=8)\n"
        f"       WRITE(*,'(A)') '{PREFLIGHT_MARKER}'\n"
        "       FLUSH(6)\n"
        "       ERROR STOP 73\n"
    )
    instrumented = text[: line_end + 1] + block + text[line_end + 1 :]
    proof = inspect_instrumentation(instrumented)
    proof["insertion_offset"] = line_end + 1
    proof["allocation_offset_original"] = allocation.start()
    return instrumented, proof


def inspect_instrumentation(text: str) -> dict[str, Any]:
    """Prove one KSize call, then unconditional stop, then one stiffness allocation."""
    call, allocation = _instrumentation_anchor(text)
    marker_pos = text.find(PREFLIGHT_MARKER)
    stop_matches = list(re.finditer(r"(?im)^\s*ERROR\s+STOP\s+73\s*$", text))
    flush_matches = list(re.finditer(r"(?im)^\s*FLUSH\s*\(\s*6\s*\)\s*$", text))
    if marker_pos < call.end() or marker_pos >= allocation.start():
        raise BW1PreflightError("preflight marker is not between KSize and stiffness allocation")
    if text.count(PREFLIGHT_MARKER) != 1 or len(stop_matches) != 1 or len(flush_matches) != 1:
        raise BW1PreflightError("instrumentation marker, FLUSH, or unconditional ERROR STOP is missing/duplicated")
    stop = stop_matches[0]
    flush = flush_matches[0]
    if not (call.end() < marker_pos < flush.start() < stop.start() < allocation.start()):
        raise BW1PreflightError("KSize / marker / FLUSH / ERROR STOP / allocation order is invalid")
    block = text[call.end() : allocation.start()]
    if re.search(r"(?im)^\s*(?:IF\b|CALL\s+GET_ENVIRONMENT_VARIABLE)", block):
        raise BW1PreflightError("preflight stop is conditional; expected an unconditional guard")
    return {
        "ksize_call_count": 1,
        "stiffness_allocation_count": 1,
        "unconditional_error_stop_count": 1,
        "output_flush_before_stop": True,
        "marker_before_stiffness_allocation": True,
        "error_stop_before_stiffness_allocation": True,
        "environment_or_cli_guard_used": False,
        "normal_solver_build_created": False,
    }


def parse_ksize_output(text: str) -> dict[str, int]:
    matches = list(K_SIZE_RE.finditer(text))
    if not matches:
        raise BW1PreflightError("KSize diagnostic is missing or incomplete")
    parsed = []
    for match in matches:
        try:
            value = float(match.group(4).replace("D", "E").replace("d", "e"))
        except ValueError as exc:
            raise BW1PreflightError("KSize matrix_bytes value cannot be parsed") from exc
        if not value.is_integer():
            raise BW1PreflightError("KSize matrix_bytes is not an integer byte count")
        parsed.append({
            "nRank": int(match.group(1)),
            "nKRows": int(match.group(2)),
            "nCodiagonals": int(match.group(3)),
            "matrix_bytes": int(value),
        })
    if any(item != parsed[0] for item in parsed[1:]):
        raise BW1PreflightError("MPI ranks reported inconsistent KSize values")
    if parsed[0] != EXPECTED_KSIZE:
        raise BW1PreflightError(f"KSize differs from the BW1 expected values: {parsed[0]}")
    return parsed[0]


def validate_preflight_log(text: str) -> dict[str, Any]:
    ksize = parse_ksize_output(text)
    marker_positions = [m.start() for m in re.finditer(re.escape(PREFLIGHT_MARKER), text)]
    if not marker_positions:
        raise BW1PreflightError("unconditional pre-allocation stop marker is missing")
    first_ksize = K_SIZE_RE.search(text)
    assert first_ksize is not None
    before_ksize = text[: first_ksize.start()]
    error = ERROR_BEFORE_KSIZE_RE.search(before_ksize)
    if error:
        raise BW1PreflightError(f"runtime error occurred before KSize: {error.group(0)}")
    if SOLVE_OUTPUT_RE.search(text):
        raise BW1PreflightError("solve/convergence output appeared in KSize-only run")
    if min(marker_positions) < first_ksize.end():
        raise BW1PreflightError("stop marker appeared before the KSize diagnostic")
    return {
        "ksize": ksize,
        "ksize_diagnostic_count": len(list(K_SIZE_RE.finditer(text))),
        "stop_marker_count": len(marker_positions),
        "errors_before_ksize": False,
        "solve_output_detected": False,
        "stopped_before_stiffness_allocation": True,
    }


def _require_inside(path: Path, root: Path, label: str) -> Path:
    resolved, resolved_root = path.resolve(), root.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise BW1PreflightError(f"{label} must be inside {resolved_root}")
    return resolved


def _validate_geometry(feg_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    mesh = parse_shellset_feg(feg_path)
    if (mesh["num_nodes"], mesh["num_elements"], mesh["num_faults"]) != (EXPECTED_NODES, EXPECTED_TRIANGLES, 0):
        raise BW1PreflightError("derived FEG cardinality/fault count differs from BW1 contract")
    edges, incidence = _edge_table(mesh["triangles_1based"])
    geom = _spherical_geometry(mesh["coordinates_lon_lat_deg"], mesh["triangles_1based"], edges)
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    rows = np.concatenate((edges[:, 0] - 1, edges[:, 1] - 1))
    cols = np.concatenate((edges[:, 1] - 1, edges[:, 0] - 1))
    graph = coo_matrix((np.ones(rows.size, dtype=np.int8), (rows, cols)), shape=(EXPECTED_NODES, EXPECTED_NODES)).tocsr()
    components, labels = connected_components(graph, directed=False, return_labels=True)
    hist: dict[str, int] = {}
    for value in incidence.values():
        hist[str(value)] = hist.get(str(value), 0) + 1
    euler = EXPECTED_NODES - len(edges) + EXPECTED_TRIANGLES
    if components != 1 or euler != 2 or hist != {"2": 193_320}:
        raise BW1PreflightError("derived FEG closed-sphere topology invariant failed")
    if geom["triangle_spherical_area_sr"]["zero_or_nonpositive_count"] != 0 or geom["triangle_spherical_area_sr"]["nonfinite_count"] != 0:
        raise BW1PreflightError("derived FEG has nonpositive or nonfinite spherical triangle areas")
    return mesh, {
        "connected_components": int(components),
        "unique_edges": int(len(edges)),
        "edge_incidence_histogram": hist,
        "euler_characteristic": int(euler),
        "geometry": geom,
        "all_nodes_in_largest_component": bool(np.all(labels == labels[0])),
    }


def validate_bw1_inputs(shellset_root: Path, bw1_root: Path) -> dict[str, Any]:
    """Validate originals, BW1 manifest/permutation/payload pair, geometry and source lock."""
    bw1_root = Path(bw1_root).resolve()
    shellset_root = Path(shellset_root).resolve()
    bw1_report = json.loads((bw1_root / "reports" / "BW1_REPORT.json").read_text(encoding="utf-8"))
    manifest_validation = verify_output_manifest(bw1_root)
    perm_doc = json.loads((bw1_root / "permutation" / "BW1_NODE_PERMUTATION_V1.json").read_text(encoding="utf-8"))
    expected_originals = _verify_authorities(DEFAULT_FEG, DEFAULT_PACKAGE, DEFAULT_FEG_MANIFEST, DEFAULT_PACKAGE.with_suffix(".json"))
    if perm_doc.get("input_feg_sha256") != expected_originals["feg_sha256"] or perm_doc.get("input_runtime_package_sha256") != expected_originals["runtime_package_sha256"]:
        raise BW1PreflightError("permutation source hashes do not match the governed original inputs")
    report_artifacts = bw1_report.get("artifacts", {}).get("sha256", {})
    derived_feg_path = bw1_root / "derived" / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
    derived_runtime_path = bw1_root / "derived" / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
    permutation_path = bw1_root / "permutation" / "BW1_NODE_PERMUTATION_V1.json"
    for key, path in (
        ("feg", derived_feg_path),
        ("runtime_package", derived_runtime_path),
        ("permutation", permutation_path),
    ):
        _require_sha256(path, str(report_artifacts.get(key, "")), f"BW1 report artifact {key}")
    report_input_hashes = bw1_report.get("source", {}).get("input_hashes", {})
    if report_input_hashes.get("feg_sha256") != expected_originals["feg_sha256"] or report_input_hashes.get("runtime_package_sha256") != expected_originals["runtime_package_sha256"]:
        raise BW1PreflightError("BW1 report source hashes do not match governed originals")

    feg_original = parse_shellset_feg(DEFAULT_FEG)
    feg_derived_path = derived_feg_path
    runtime_derived_path = derived_runtime_path
    feg_derived = parse_shellset_feg(feg_derived_path)
    old_to_new = np.asarray(perm_doc["old_to_new"], dtype=np.int64)
    new_to_old = np.asarray(perm_doc["new_to_old"], dtype=np.int64)
    if len(old_to_new) != EXPECTED_NODES or len(new_to_old) != EXPECTED_NODES:
        raise BW1PreflightError("permutation is incomplete for the governed node count")
    expected_triangles = old_to_new[feg_original["triangles_1based"] - 1]
    if not np.array_equal(expected_triangles, feg_derived["triangles_1based"]):
        raise BW1PreflightError("derived FEG connectivity disagrees with old_to_new mapping")
    if not np.array_equal(feg_derived["coordinates_lon_lat_deg"], feg_original["coordinates_lon_lat_deg"][new_to_old - 1]):
        raise BW1PreflightError("derived FEG coordinates do not follow new_to_old mapping")
    orig_parts = _read_feg_full(DEFAULT_FEG)
    der_parts = _read_feg_full(feg_derived_path)
    if orig_parts[0] != der_parts[0] or orig_parts[2] != der_parts[2] or orig_parts[4] != der_parts[4]:
        raise BW1PreflightError("derived FEG changed header, triangle count, or fault framing")
    _roundtrip_check(orig_parts[1], orig_parts[3], der_parts[1], der_parts[3], new_to_old, old_to_new)

    orig_header, original_records, original_runtime_meta = _parse_runtime(DEFAULT_PACKAGE, EXPECTED_NODES)
    der_header, derived_records, derived_runtime_meta = _parse_runtime(runtime_derived_path, EXPECTED_NODES)
    if orig_header != der_header:
        raise BW1PreflightError("runtime package header/schema changed")
    for new_id, old_id in enumerate(new_to_old, start=1):
        if derived_records[new_id - 1].split()[1:] != original_records[int(old_id) - 1].split()[1:]:
            raise BW1PreflightError(f"runtime fields changed under node mapping at new node {new_id}")
    if original_runtime_meta != derived_runtime_meta or derived_runtime_meta["mixed_physical_support_count"] != 2_697:
        raise BW1PreflightError("runtime branch or mixed-support counts changed under permutation")
    runtime_alignment = validate_runtime_package(runtime_derived_path, EXPECTED_NODES, EXPECTED_FIELDS)

    original_mesh, original_topology = _validate_geometry(DEFAULT_FEG)
    derived_mesh, derived_topology = _validate_geometry(feg_derived_path)
    if (original_mesh["num_nodes"], original_mesh["num_elements"], original_topology["unique_edges"]) != (derived_mesh["num_nodes"], derived_mesh["num_elements"], derived_topology["unique_edges"]):
        raise BW1PreflightError("topology cardinality changed under reordering")
    if _ksize(EXPECTED_NODES, derived_mesh["triangles_1based"], _edge_table(derived_mesh["triangles_1based"])[0]) != bw1_report.get("ksize", {}).get("reordered"):
        raise BW1PreflightError("independent Python KSize disagrees with the retained BW1 report")

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    source_hashes = si1.verify_source_lock(shellset_root, lock)
    parameter_reference = shellset_root / "INPUT" / "iEarth5-049.in"
    if si1.sha256(parameter_reference) != lock["parameter_reference_sha256"]:
        raise BW1PreflightError("ShellSet engineering parameter reference SHA differs from source lock")
    partition_manifest = json.loads(PARTITION_MANIFEST_PATH.read_text(encoding="utf-8"))
    partition_sha = si1.sha256(PARTITION_PATH)
    if partition_manifest.get("payload", {}).get("sha256") != partition_sha:
        raise BW1PreflightError("canonical partition payload and manifest SHA disagree")
    return {
        "classification": "NON_CANONICAL_ENGINEERING_REORDERED_INPUT",
        "manifest_validation": manifest_validation,
        "source_inputs": expected_originals,
        "derived_inputs": {
            "feg_sha256": si1.sha256(feg_derived_path),
            "runtime_package_sha256": si1.sha256(runtime_derived_path),
        },
        "permutation": {
            "sha256": si1.sha256(bw1_root / "permutation" / "BW1_NODE_PERMUTATION_V1.json"),
            "bijection_inverse_verified": True,
            "identity_preserved": True,
        },
        "counts": {
            "nodes": EXPECTED_NODES,
            "triangles": EXPECTED_TRIANGLES,
            "fault_elements": 0,
            "runtime_fields_including_node_id": runtime_alignment["token_count_per_record_including_node_id"],
            "runtime_branch_code_counts": derived_runtime_meta["branch_code_counts"],
            "mixed_support_nodes": derived_runtime_meta["mixed_physical_support_count"],
        },
        "topology": derived_topology,
        "shellset_source_lock": {
            "locked_source_commit_claim": lock["vendored_arcana_source_commit"],
            "locked_file_count": len(source_hashes),
            "all_locked_hashes_match": True,
            "parameter_reference_sha256": si1.sha256(parameter_reference),
        },
        "node_indexed_input_audit": {
            "node_indexed_and_remapped": ["FEG nodal record IDs/order", "FEG triangle connectivity IDs", "runtime package record order and first node_id field"],
            "not_node_indexed_in_this_case": ["plate outlines keyed by ShellSet plate slot", "global no-velocity boundary-condition fixture", "ListInput control values"],
            "fault_record_count": 0,
        },
        "partition_payload_sha256": partition_sha,
    }


def _copy_and_instrument_sources(source_root: Path, build_root: Path) -> dict[str, Any]:
    build_root.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source_root / "Makefile", build_root / "Makefile")
    src_out = build_root / "src"
    src_out.mkdir()
    source_hashes: dict[str, str] = {}
    for source in sorted((source_root / "src").glob("*.f90")):
        target = src_out / source.name
        original_digest = si1.sha256(source)
        if source.name == "SHELLS_v5.0.f90":
            transformed, proof = instrument_source_text(source.read_text(encoding="utf-8"))
            target.write_text(transformed, encoding="utf-8", newline="\n")
            proof["original_sha256"] = original_digest
            proof["instrumented_sha256"] = si1.sha256(target)
            source_hashes[source.name] = proof["instrumented_sha256"]
        else:
            shutil.copy2(source, target)
            if si1.sha256(target) != original_digest:
                raise BW1PreflightError(f"temporary source copy hash mismatch: {source.name}")
            source_hashes[source.name] = original_digest
    instrumented_path = src_out / "SHELLS_v5.0.f90"
    proof = inspect_instrumentation(instrumented_path.read_text(encoding="utf-8"))
    proof["original_sha256"] = si1.sha256(source_root / "src" / "SHELLS_v5.0.f90")
    proof["instrumented_sha256"] = si1.sha256(instrumented_path)
    return {"files": source_hashes, "instrumentation": proof}


def _probe_tool(name: str) -> dict[str, Any]:
    result = subprocess.run([name, "--version"], capture_output=True, text=True, check=False)
    excerpt = (result.stdout + result.stderr).strip()
    if result.returncode != 0 or not excerpt:
        raise BW1PreflightError(f"required Fair tool unavailable or failed version probe: {name}")
    return {"tool": name, "returncode": result.returncode, "version_first_line": excerpt.splitlines()[0], "version_excerpt": excerpt[:2000]}


def _write_report(output_dir: Path, report: dict[str, Any]) -> None:
    (output_dir / "BW1_FAIR_PREFLIGHT_RESULT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    lines = [
        "# SI1-BW1 Fair KSize-Only Preflight", "",
        f"Decision: `{report.get('decision', 'BLOCKED_BW1_FAIR_PREFLIGHT')}`.", "",
        f"Scope: {report.get('scope', 'Fail-closed KSize-only preflight; no solve.')}", "",
        "## Evidence", "",
        f"- Branch / HEAD: `{report.get('repository', {}).get('branch')}` / `{report.get('repository', {}).get('head')}`.",
        f"- Derived FEG SHA256: `{report.get('inputs', {}).get('derived_inputs', {}).get('feg_sha256')}`.",
        f"- Derived runtime SHA256: `{report.get('inputs', {}).get('derived_inputs', {}).get('runtime_package_sha256')}`.",
        f"- Toolchain: {json.dumps(report.get('toolchain', {}), sort_keys=True)}.",
        f"- KSize: {json.dumps(report.get('preflight', {}).get('ksize'), sort_keys=True)}.",
        f"- Stopped before stiffness allocation: {report.get('preflight', {}).get('stopped_before_stiffness_allocation', False)}.",
        f"- Failure: {report.get('failure', 'none')}.", "",
        "The only executable in this package is built from the locked ShellSet source copied into a temporary build tree and instrumented with an unconditional `ERROR STOP 73` after KSize. No ordinary solve executable is built or accepted by this runner.", "",
        "Governed FEG/runtime inputs and WORLD_HISTORY are read-only. BW1 files are explicitly classified as noncanonical engineering-derived inputs.", "",
    ]
    (output_dir / "BW1_FAIR_PREFLIGHT_RESULT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _git_value(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise BW1PreflightError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _seal_preflight_manifest(output_dir: Path) -> None:
    entries = []
    files = sorted(
        (path for path in output_dir.rglob("*") if path.is_file() and path.name != "BW1_FAIR_PREFLIGHT_ARTIFACT_MANIFEST.json"),
        key=lambda path: (path.relative_to(output_dir).as_posix().casefold(), path.relative_to(output_dir).as_posix()),
    )
    for path in files:
        relative = path.relative_to(output_dir).as_posix()
        role = (
            "BUILD_OR_RUNTIME_LOG" if relative.startswith("logs/")
            else "ISOLATED_BUILD_ARTIFACT" if relative.startswith("build_preflight/")
            else "ISOLATED_STAGED_INPUT_OR_RUNTIME_OUTPUT" if relative.startswith("preflight_run/")
            else "RUNNER_DECISION_OR_EVIDENCE"
        )
        entries.append({"path": relative, "bytes": path.stat().st_size, "sha256": _sha256(path), "role": role})
    manifest = {
        "schema": "R6_SI1_BW1_FAIR_PREFLIGHT_ARTIFACT_MANIFEST_V1",
        "membership": "all regular files recursively except this manifest",
        "artifacts": entries,
    }
    (output_dir / "BW1_FAIR_PREFLIGHT_ARTIFACT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shellset-root", type=Path, default=SHELLSET_ROOT)
    parser.add_argument("--bw1-root", type=Path, default=BW1_ROOT)
    parser.add_argument("--partition-payload", type=Path, default=PARTITION_PATH)
    parser.add_argument("--output-dir", type=Path, required=True, help="new, isolated evidence directory")
    return parser


def run_preflight(shellset_root: Path, bw1_root: Path, partition_payload: Path, output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise BW1PreflightError(f"output directory must be new; refusing existing path: {output_dir}")
    if output_dir == Path(shellset_root).resolve() or Path(shellset_root).resolve() in output_dir.parents:
        raise BW1PreflightError("evidence output may not be created inside the ShellSet source checkout")
    output_dir.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {
        "schema": "R6_SI1_BW1_FAIR_PREFLIGHT_V1",
        "classification": "NON_CANONICAL_ENGINEERING_REORDERED_INPUT",
        "decision": "BLOCKED_BW1_FAIR_PREFLIGHT",
        "scope": "Compile and run one isolated executable that validates the staged pair and terminates immediately after KSize.",
        "repository": {
            "branch": None,
            "head": None,
        },
        "execution_limits": {
            "mpi_ranks": MPI_RANKS,
            "memory_cap_gib_per_process": MEMORY_CAP_GIB_PER_PROCESS,
            "timeout_seconds": TIMEOUT_SECONDS,
            "mpi_version_flag_used": False,
        },
        "preserved_gates": {
            "canonical_feg_modified": False,
            "canonical_runtime_package_modified": False,
            "world_history_changed": False,
            "mechanics_or_solve_executed": False,
            "t1_or_t2_created": False,
        },
    }
    original_hashes: dict[str, str] = {}
    try:
        report["repository"] = {
            "branch": _git_value("branch", "--show-current"),
            "head": _git_value("rev-parse", "HEAD"),
        }
        if not sys.platform.startswith("linux"):
            raise BW1PreflightError("Fair runtime is Linux-only; this Windows runner instance performs validation/tests, not execution")
        inputs = validate_bw1_inputs(Path(shellset_root), Path(bw1_root))
        if Path(partition_payload).resolve() != PARTITION_PATH.resolve() or si1.sha256(Path(partition_payload)) != inputs["partition_payload_sha256"]:
            raise BW1PreflightError("partition payload path/SHA differs from the manifested canonical partition")
        report["inputs"] = inputs
        original_hashes = {
            "feg": inputs["source_inputs"]["feg_sha256"],
            "runtime_package": inputs["source_inputs"]["runtime_package_sha256"],
            "shellset_sources": {key: value for key, value in si1.verify_source_lock(Path(shellset_root), json.loads(LOCK_PATH.read_text(encoding="utf-8"))).items()},
        }
        toolchain = [_probe_tool(tool) for tool in ("nvfortran", "mpifort", "mpiexec")]
        compiler_text = "\n".join(item["version_excerpt"] for item in toolchain[:2]).lower()
        if "nvfortran" not in compiler_text or "25.11" not in compiler_text:
            raise BW1PreflightError("Fair compiler probes do not identify the qualified NVIDIA HPC SDK 25.11")
        report["toolchain"] = toolchain

        build_root = output_dir / "build_preflight"
        report["instrumented_build"] = _copy_and_instrument_sources(Path(shellset_root).resolve(), build_root)
        build = si1.run_checked(
            ["make", "ShellSet"], cwd=build_root, timeout=TIMEOUT_SECONDS,
            stdout_path=output_dir / "logs" / "build_preflight.log", env=si1._solver_env(),
        )
        if build.returncode != 0 or not (build_root / "ShellSet.exe").is_file():
            raise BW1PreflightError(f"isolated preflight-only ShellSet build failed with exit code {build.returncode}")
        if list(build_root.rglob("ShellSet.exe")) != [build_root / "ShellSet.exe"]:
            raise BW1PreflightError("build tree contains unexpected/multiple ShellSet executables")

        run_dir = output_dir / "preflight_run"
        run_dir.mkdir()
        input_dir = run_dir / "INPUT"
        si1.write_input_files(input_dir)
        derived_feg = Path(bw1_root) / "derived" / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
        derived_runtime = Path(bw1_root) / "derived" / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
        shutil.copy2(derived_feg, input_dir / DEFAULT_FEG.name)
        shutil.copy2(derived_runtime, input_dir / DEFAULT_PACKAGE.name)
        parameter_reference = Path(shellset_root) / "INPUT" / "iEarth5-049.in"
        shutil.copy2(parameter_reference, input_dir / "SI1_ENGINEERING_REFERENCE.in")
        matrix = json.loads(DEFAULT_FEG_MANIFEST.read_text(encoding="utf-8"))["runtime_coordinate_frame"]["forward_rotation_matrix"]
        rings = si1.canonical_plate_rings(Path(partition_payload), matrix)
        symbols = si1._plate_symbols(Path(shellset_root) / "src" / "MOD_SharedVars.f90")
        outline_path = input_dir / "ARCANA_PLATE_OUTLINES.dig"
        report["plate_outline_support"] = si1.write_plate_outlines(outline_path, rings, symbols, derived_feg)
        shutil.copy2(build_root / "ShellSet.exe", run_dir / "ShellSet.exe")
        report["staged_input_hashes"] = {
            path.name: si1.sha256(path)
            for path in sorted(input_dir.iterdir()) if path.is_file()
        }
        original_hashes["derived_feg"] = inputs["derived_inputs"]["feg_sha256"]
        original_hashes["derived_runtime_package"] = inputs["derived_inputs"]["runtime_package_sha256"]
        original_hashes["staged_inputs"] = dict(report["staged_input_hashes"])
        expected_stage = {"InputFiles.in", "ListInput.in", "SI1_NO_VELOCITY.bcs", "SI1_UNUSED_PLATE_PAIR.dig", "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg", "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat", "SI1_ENGINEERING_REFERENCE.in", "ARCANA_PLATE_OUTLINES.dig"}
        if {p.name for p in input_dir.iterdir() if p.is_file()} != expected_stage:
            raise BW1PreflightError("isolated ShellSet input staging set is incomplete or contains an extra input")
        run_executables = list(run_dir.glob("*.exe"))
        if len(run_executables) != 1 or run_executables[0].name != "ShellSet.exe":
            raise BW1PreflightError("staging directory does not contain exactly the one preflight executable")

        command = ["mpiexec", "-n", str(MPI_RANKS), "./ShellSet.exe", "-Iter", "1", "-InOpt", "List", "-Dir", "RUN_OUTPUT"]
        report["mpi_command"] = command
        try:
            run = si1.run_checked(
                command, cwd=run_dir, timeout=TIMEOUT_SECONDS,
                stdout_path=output_dir / "logs" / "preflight_mpi.log",
                env=si1._solver_env(), address_space_bytes=MEMORY_CAP_GIB_PER_PROCESS * 1024**3,
            )
        except subprocess.TimeoutExpired as exc:
            captured = exc.stdout or ""
            report["preflight_log_excerpt"] = captured.decode("utf-8", errors="replace")[-4000:] if isinstance(captured, bytes) else str(captured)[-4000:]
            raise BW1PreflightError("Fair MPI KSize preflight exceeded the fixed 1800-second timeout") from exc
        log_path = output_dir / "logs" / "preflight_mpi.log"
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        guard = inspect_instrumentation((build_root / "src" / "SHELLS_v5.0.f90").read_text(encoding="utf-8"))
        log_validation = validate_preflight_log(log_text)
        report["preflight"] = {
            **log_validation,
            "mpi_exit_code": run.returncode,
            "mpi_exit_code_nonzero_expected_or_acceptable": run.returncode != 0,
            "static_stop_guard": guard,
            "diagnostic_log_sha256": si1.sha256(log_path),
            "build_log_sha256": si1.sha256(output_dir / "logs" / "build_preflight.log"),
        }
        after_feg_sha = si1.sha256(DEFAULT_FEG)
        after_runtime_sha = si1.sha256(DEFAULT_PACKAGE)
        if after_feg_sha != original_hashes["feg"] or after_runtime_sha != original_hashes["runtime_package"]:
            raise BW1PreflightError("governed FEG/runtime source changed during isolated preflight")
        if si1.sha256(Path(bw1_root) / "derived" / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg") != original_hashes["derived_feg"]:
            raise BW1PreflightError("BW1 derived FEG changed during isolated preflight")
        if si1.sha256(Path(bw1_root) / "derived" / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat") != original_hashes["derived_runtime_package"]:
            raise BW1PreflightError("BW1 derived runtime package changed during isolated preflight")
        for name, digest in original_hashes["staged_inputs"].items():
            staged_path = input_dir / name
            if not staged_path.is_file() or si1.sha256(staged_path) != digest:
                raise BW1PreflightError(f"staged preflight input changed during execution: {name}")
        for relative, digest in original_hashes["shellset_sources"].items():
            if si1.sha256(Path(shellset_root) / relative) != digest:
                raise BW1PreflightError(f"governed ShellSet source changed during preflight: {relative}")
        report["original_input_preservation"] = {"original_feg_unchanged": True, "original_runtime_package_unchanged": True, "shellset_checkout_unchanged": True}
        report["decision"] = "PASS_BW1_FAIR_KSIZE_ONLY"
    except Exception as exc:
        report["failure"] = f"{type(exc).__name__}: {exc}"
    if report["decision"] != "PASS_BW1_FAIR_KSIZE_ONLY":
        report["decision"] = "BLOCKED_BW1_FAIR_PREFLIGHT"
    _write_report(output_dir, report)
    _seal_preflight_manifest(output_dir)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run_preflight(args.shellset_root, args.bw1_root, args.partition_payload, args.output_dir)
    except (OSError, ValueError, BW1PreflightError) as exc:
        parser.exit(2, f"BLOCKED_BW1_FAIR_PREFLIGHT: {exc}\n")
    print(result["decision"])
    if result["decision"] == "BLOCKED_BW1_FAIR_PREFLIGHT":
        print(result.get("failure", "preflight gate failed"), file=sys.stderr)
        return 2
    print(f"BW1_KSIZE={json.dumps(result['preflight']['ksize'], sort_keys=True)}")
    print(f"BW1_EVIDENCE={args.output_dir / 'BW1_FAIR_PREFLIGHT_RESULT.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
