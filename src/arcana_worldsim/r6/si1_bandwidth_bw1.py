"""Materialize a NON_CANONICAL RCM-reordered SI1 engineering input pair."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import reverse_cuthill_mckee

from .si1_bandwidth import (
    DEFAULT_FEG,
    DEFAULT_FEG_MANIFEST,
    DEFAULT_PACKAGE,
    EXPECTED_ELEMENTS,
    EXPECTED_NODES,
    RUNTIME_VALUE_COUNT,
    REPO_ROOT,
    _git_value,
    _edge_table,
    _ksize,
    _sha256,
    parse_shellset_feg,
)


SCHEMA = "R6_SI1_BW1_ISOLATED_REORDERED_INPUT_V1"
OUTPUT_ROOT = Path(__file__).resolve().parents[3] / "outputs" / "r6_si1_bandwidth_bw1"
FEG_NAME = "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
PACKAGE_NAME = "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"


def _replace_tokens(line: str, replacements: dict[int, str]) -> str:
    """Replace zero-based whitespace-delimited fields without changing others."""
    spans = list(re.finditer(r"\S+", line))
    if any(index < 0 or index >= len(spans) for index in replacements):
        raise ValueError("record does not contain every requested field")
    for index in sorted(replacements, reverse=True):
        match = spans[index]
        line = line[: match.start()] + replacements[index] + line[match.end() :]
    return line


def build_permutation(triangles_1based: np.ndarray, node_count: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (old_to_new, new_to_old), both 1-based, from deterministic SciPy RCM."""
    if node_count < 1 or triangles_1based.ndim != 2 or triangles_1based.shape[1] != 3:
        raise ValueError("invalid node count or triangle shape")
    if triangles_1based.size and (
        int(triangles_1based.min()) < 1 or int(triangles_1based.max()) > node_count
    ):
        raise ValueError("triangle references node outside permutation domain")
    edges, _ = _edge_table(triangles_1based)
    rows = np.concatenate((edges[:, 0] - 1, edges[:, 1] - 1))
    cols = np.concatenate((edges[:, 1] - 1, edges[:, 0] - 1))
    graph = coo_matrix((np.ones(rows.size, dtype=np.int8), (rows, cols)), shape=(node_count, node_count)).tocsr()
    new_to_old_zero = reverse_cuthill_mckee(graph, symmetric_mode=True).astype(np.int64, copy=False)
    new_to_old = new_to_old_zero + 1
    old_to_new = np.empty(node_count, dtype=np.int64)
    old_to_new[new_to_old_zero] = np.arange(1, node_count + 1, dtype=np.int64)
    validate_permutation(old_to_new, new_to_old, node_count)
    return old_to_new, new_to_old


def validate_permutation(old_to_new: np.ndarray, new_to_old: np.ndarray, node_count: int) -> None:
    if node_count < 1:
        raise ValueError("permutation node count must be positive")
    if old_to_new.shape != (node_count,) or new_to_old.shape != (node_count,):
        raise ValueError("permutation has missing or extra IDs")
    expected = np.arange(1, node_count + 1, dtype=np.int64)
    if not np.array_equal(np.sort(old_to_new), expected) or not np.array_equal(np.sort(new_to_old), expected):
        raise ValueError("permutation is not a complete bijection")
    if not np.array_equal(old_to_new[new_to_old - 1], expected):
        raise ValueError("permutation maps are not exact inverses")


def _read_lines(path: Path) -> list[str]:
    raw = path.read_bytes()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(f"expected ASCII text input: {path.name}") from exc
    if "\r" in text:
        raise ValueError(f"CR/CRLF input is not accepted for deterministic LF processing: {path.name}")
    return text.splitlines(keepends=True)


def _parse_runtime(path: Path, expected_nodes: int) -> tuple[list[str], list[str], dict[str, int]]:
    lines = _read_lines(path)
    if len(lines) != expected_nodes + 1:
        raise ValueError("runtime package line count differs from header plus expected records")
    header = lines[0].split()
    if len(header) != 3 or int(header[2]) != expected_nodes:
        raise ValueError("runtime package header/count mismatch")
    records: list[str | None] = [None] * expected_nodes
    branch_counts: dict[str, int] = {}
    mixed_support_count = 0
    for ordinal, line in enumerate(lines[1:], start=1):
        fields = line.split()
        if len(fields) != RUNTIME_VALUE_COUNT:
            raise ValueError(f"runtime record {ordinal} has {len(fields)} fields, expected {RUNTIME_VALUE_COUNT}")
        raw_node_id = float(fields[0])
        if not math.isfinite(raw_node_id) or not raw_node_id.is_integer():
            raise ValueError(f"runtime node ID is not a finite integer at record {ordinal}")
        node_id = int(raw_node_id)
        if not 1 <= node_id <= expected_nodes or records[node_id - 1] is not None:
            raise ValueError(f"invalid or duplicate runtime node ID {node_id}")
        numeric = np.asarray([float(value) for value in fields], dtype=np.float64)
        if not bool(np.isfinite(numeric).all()):
            raise ValueError(f"runtime record {node_id} contains NaN or infinity")
        branch = str(int(float(fields[8]) + 0.5))
        branch_counts[branch] = branch_counts.get(branch, 0) + 1
        if int(float(fields[5]) + 0.5) == 1:
            mixed_support_count += 1
        records[node_id - 1] = line
    if any(line is None for line in records):
        raise ValueError("runtime package has missing node IDs")
    return lines[:1], [line for line in records if line is not None], {
        "branch_code_counts": branch_counts,
        "mixed_physical_support_count": mixed_support_count,
    }


def _feg_sections(path: Path) -> tuple[list[str], list[str], list[str], list[str]]:
    lines = _read_lines(path)
    parsed = parse_shellset_feg(path)
    n_nodes, n_triangles = parsed["num_nodes"], parsed["num_elements"]
    node_start, tri_count_index = 2, 2 + n_nodes
    tri_start, fault_count_index = tri_count_index + 1, tri_count_index + 1 + n_triangles
    if fault_count_index >= len(lines) or int(lines[fault_count_index].split()[0]) != 0:
        raise ValueError("BW1 requires the audited nFl=0 FEG")
    if any(line.strip() for line in lines[fault_count_index + 1 :]):
        raise ValueError("unexpected trailing FEG content")
    return lines[:node_start], lines[node_start:tri_count_index], lines[tri_count_index:tri_start], lines[tri_start:fault_count_index + 1]


def _remap_feg(header: list[str], nodes: list[str], triangle_prefix: list[str], triangles: list[str], old_to_new: np.ndarray, new_to_old: np.ndarray) -> tuple[list[str], list[str], list[str], list[str]]:
    node_by_id: list[str | None] = [None] * len(nodes)
    for line in nodes:
        fields = line.split()
        node_id = int(float(fields[0]) + 0.5)
        if not 1 <= node_id <= len(nodes) or node_by_id[node_id - 1] is not None:
            raise ValueError(f"invalid or duplicate FEG node ID {node_id}")
        node_by_id[node_id - 1] = line
    if any(line is None for line in node_by_id):
        raise ValueError("FEG nodal IDs are incomplete")
    output_nodes = [
        _replace_tokens(node_by_id[int(old_id) - 1], {0: str(new_id)})
        for new_id, old_id in enumerate(new_to_old, start=1)
    ]
    output_triangles = []
    for line in triangles:
        fields = line.split()
        ids = [int(token) for token in fields[1:4]]
        output_triangles.append(_replace_tokens(line, {i + 1: str(int(old_to_new[node_id - 1])) for i, node_id in enumerate(ids)}))
    return header, output_nodes, triangle_prefix, output_triangles


def _roundtrip_check(original_nodes: list[str], original_triangles: list[str], reordered_nodes: list[str], reordered_triangles: list[str], new_to_old: np.ndarray, old_to_new: np.ndarray) -> None:
    reconstructed_nodes: list[str | None] = [None] * len(original_nodes)
    for new_id, old_id in enumerate(new_to_old, start=1):
        reconstructed_nodes[int(old_id) - 1] = _replace_tokens(reordered_nodes[new_id - 1], {0: str(int(old_id))})
    if reconstructed_nodes != original_nodes:
        raise ValueError("FEG inverse permutation failed byte-preserving nodal round-trip")
    restored_triangles = []
    for line in reordered_triangles:
        fields = line.split()
        new_ids = [int(token) for token in fields[1:4]]
        restored_triangles.append(_replace_tokens(line, {i + 1: str(int(new_to_old[node_id - 1])) for i, node_id in enumerate(new_ids)}))
    if restored_triangles != original_triangles:
        raise ValueError("FEG inverse permutation failed byte-preserving connectivity round-trip")


def _verify_authorities(feg: Path, package: Path, feg_manifest: Path, package_manifest: Path) -> dict[str, Any]:
    fm = json.loads(feg_manifest.read_text(encoding="utf-8"))
    pm = json.loads(package_manifest.read_text(encoding="utf-8"))
    expected_feg = fm["production_feg"]["raw_sha256"]
    expected_package = pm["runtime_data_sha256"]
    actual_feg, actual_package = _sha256(feg), _sha256(package)
    if actual_feg != expected_feg:
        raise ValueError("governed FEG raw SHA256 does not match its manifest")
    if actual_package != expected_package:
        raise ValueError("governed runtime package SHA256 does not match its manifest")
    return {"feg_sha256": actual_feg, "feg_manifest_sha256": _sha256(feg_manifest), "runtime_package_sha256": actual_package, "runtime_manifest_sha256": _sha256(package_manifest)}


def verify_output_manifest(output_dir: Path) -> dict[str, Any]:
    """Fail closed if a retained BW1 input artifact is missing or has changed."""
    output_dir = Path(output_dir).resolve()
    manifest_path = output_dir / "manifests" / "BW1_INPUT_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "R6_SI1_BW1_ARTIFACT_MANIFEST_V1":
        raise ValueError("unexpected BW1 artifact manifest schema")
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != 5:
        raise ValueError("BW1 input manifest must enumerate exactly five input artifacts")
    seen: set[str] = set()
    for entry in entries:
        relative = entry.get("path")
        if not isinstance(relative, str) or relative in seen:
            raise ValueError("BW1 manifest contains an invalid or duplicate path")
        seen.add(relative)
        path = (output_dir / Path(relative)).resolve()
        if output_dir not in path.parents or not path.is_file():
            raise ValueError(f"BW1 manifest path escapes output root or is missing: {relative}")
        if path.stat().st_size != entry.get("size_bytes") or _sha256(path) != entry.get("sha256"):
            raise ValueError(f"BW1 artifact integrity mismatch: {relative}")
    expected = {
        "derived/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg",
        "derived/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
        "fair_staging/INPUT/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg",
        "fair_staging/INPUT/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat",
        "permutation/BW1_NODE_PERMUTATION_V1.json",
    }
    if seen != expected:
        raise ValueError("BW1 manifest does not cover the exact required input artifact set")
    maps = json.loads((output_dir / "permutation" / "BW1_NODE_PERMUTATION_V1.json").read_text(encoding="utf-8"))
    old_to_new = np.asarray(maps.get("old_to_new", []), dtype=np.int64)
    new_to_old = np.asarray(maps.get("new_to_old", []), dtype=np.int64)
    validate_permutation(old_to_new, new_to_old, int(maps.get("node_count", 0)))
    map_blob = np.ascontiguousarray(np.concatenate((old_to_new.astype("<i8"), new_to_old.astype("<i8")))).tobytes()
    if hashlib.sha256(map_blob).hexdigest() != maps.get("serialized_maps_sha256_little_endian_int64"):
        raise ValueError("BW1 serialized permutation map digest mismatch")
    return {"valid": True, "file_count": len(entries), "manifest_sha256": _sha256(manifest_path)}


def materialize(feg_path: Path = DEFAULT_FEG, package_path: Path = DEFAULT_PACKAGE, feg_manifest_path: Path = DEFAULT_FEG_MANIFEST, package_manifest_path: Path | None = None, output_dir: Path = OUTPUT_ROOT) -> dict[str, Any]:
    """Validate sources, materialize isolated FEG/runtime copies, and seal outputs."""
    feg_path, package_path = Path(feg_path), Path(package_path)
    feg_manifest_path = Path(feg_manifest_path)
    package_manifest_path = Path(package_manifest_path) if package_manifest_path else package_path.with_suffix(".json")
    output_dir = Path(output_dir)
    protected = {p.resolve() for p in (feg_path, package_path, feg_manifest_path, package_manifest_path)}
    if output_dir.resolve() == feg_path.parent.resolve() or any(output_dir.resolve() == p.parent.resolve() for p in protected):
        raise ValueError("output directory must be isolated from governed inputs")
    input_hashes = _verify_authorities(feg_path, package_path, feg_manifest_path, package_manifest_path)
    feg_parsed = parse_shellset_feg(feg_path)
    n_nodes = feg_parsed["num_nodes"]
    if n_nodes != EXPECTED_NODES or feg_parsed["num_elements"] != EXPECTED_ELEMENTS or feg_parsed["num_faults"] != 0:
        raise ValueError("input FEG differs from the audited SI1 BW0 cardinality")
    old_to_new, new_to_old = build_permutation(feg_parsed["triangles_1based"], n_nodes)
    old_to_new_repeat, new_to_old_repeat = build_permutation(feg_parsed["triangles_1based"], n_nodes)
    if not np.array_equal(old_to_new, old_to_new_repeat) or not np.array_equal(new_to_old, new_to_old_repeat):
        raise ValueError("SciPy RCM mapping is not deterministic across repeated invocation")

    header, original_nodes, triangle_prefix, original_triangles, fault_section = _read_feg_full(feg_path)
    new_header, new_nodes, tri_prefix, new_triangles = _remap_feg(header, original_nodes, triangle_prefix, original_triangles, old_to_new, new_to_old)
    _roundtrip_check(original_nodes, original_triangles, new_nodes, new_triangles, new_to_old, old_to_new)
    if original_nodes is new_nodes:
        raise AssertionError("internal source/derived node records unexpectedly alias")

    runtime_header, runtime_records, runtime_meta = _parse_runtime(package_path, n_nodes)
    derived_runtime = [_replace_tokens(runtime_records[int(old_id) - 1], {0: str(new_id)}) for new_id, old_id in enumerate(new_to_old, start=1)]
    restored_runtime: list[str | None] = [None] * n_nodes
    for new_id, old_id in enumerate(new_to_old, start=1):
        restored_runtime[int(old_id) - 1] = _replace_tokens(derived_runtime[new_id - 1], {0: str(int(old_id))})
    if restored_runtime != runtime_records:
        raise ValueError("runtime package inverse permutation failed byte-preserving round-trip")

    mapped_triangles = feg_parsed["triangles_1based"].copy()
    mapped_triangles = old_to_new[mapped_triangles - 1]
    original_edges, _ = _edge_table(feg_parsed["triangles_1based"])
    mapped_edges, _ = _edge_table(mapped_triangles)
    original_ksize = _ksize(n_nodes, feg_parsed["triangles_1based"], original_edges)
    mapped_ksize = _ksize(n_nodes, mapped_triangles, mapped_edges)
    if mapped_ksize["nCodiagonals"] != 727 or mapped_ksize["nKRows"] != 2182 or mapped_ksize["matrix_bytes"] != 2249799104:
        raise ValueError("reordered KSize differs from the unforced BW0 target")

    perm_blob = np.ascontiguousarray(np.concatenate((old_to_new.astype("<i8"), new_to_old.astype("<i8")))).tobytes()
    perm_path = output_dir / "permutation" / "BW1_NODE_PERMUTATION_V1.json"
    derived_feg_path = output_dir / "derived" / FEG_NAME
    derived_package_path = output_dir / "derived" / PACKAGE_NAME
    staging_input = output_dir / "fair_staging" / "INPUT"
    for path in (perm_path, derived_feg_path, derived_package_path, staging_input / FEG_NAME, staging_input / PACKAGE_NAME):
        path.parent.mkdir(parents=True, exist_ok=True)
    map_doc = {"schema": "R6_SI1_BW1_NODE_PERMUTATION_V1", "algorithm": "scipy.sparse.csgraph.reverse_cuthill_mckee", "orientation": "new_to_old maps each reordered 1-based position to original 1-based node ID; old_to_new is its inverse", "scipy_version": scipy.__version__, "node_count": n_nodes, "input_feg_sha256": input_hashes["feg_sha256"], "input_runtime_package_sha256": input_hashes["runtime_package_sha256"], "old_to_new": old_to_new.tolist(), "new_to_old": new_to_old.tolist(), "serialized_maps_sha256_little_endian_int64": hashlib.sha256(perm_blob).hexdigest()}
    _write_json(perm_path, map_doc)
    _write_text(derived_feg_path, "".join(new_header + new_nodes + tri_prefix + new_triangles + fault_section))
    _write_text(derived_package_path, "".join(runtime_header + derived_runtime))
    # The staging tree contains only the two node-indexed payloads. The Fair contract
    # specifies additional unchanged SI1 controls to be supplied by the operator.
    _copy_bytes(derived_feg_path, staging_input / FEG_NAME)
    _copy_bytes(derived_package_path, staging_input / PACKAGE_NAME)

    derived_hashes = {"permutation": _sha256(perm_path), "feg": _sha256(derived_feg_path), "runtime_package": _sha256(derived_package_path), "staged_feg": _sha256(staging_input / FEG_NAME), "staged_runtime_package": _sha256(staging_input / PACKAGE_NAME)}
    if derived_hashes["feg"] != derived_hashes["staged_feg"] or derived_hashes["runtime_package"] != derived_hashes["staged_runtime_package"]:
        raise ValueError("staging copy differs from derived artifact")
    report = {
        "schema": SCHEMA,
        "classification": "NON_CANONICAL_ENGINEERING_REORDERED_INPUT",
        "decision": "BLOCKED_BW1",
        "decision_reason": "Isolated derived pair and Fair staging contract are complete, but no preflight-only Fair runner is provided to mechanically enforce immediate termination after KSize; do not launch ShellSet until that guard is independently implemented and verified.",
        "source": {"repository_branch": _git_value(REPO_ROOT, "branch", "--show-current"), "repository_head": _git_value(REPO_ROOT, "rev-parse", "HEAD"), "input_hashes": input_hashes, "feg_manifest_path": feg_manifest_path.name, "runtime_manifest_path": package_manifest_path.name, "scipy_version": scipy.__version__, "algorithm": "SciPy Reverse Cuthill-McKee", "mapping_orientation": map_doc["orientation"]},
        "counts": {"nodes": n_nodes, "triangles": feg_parsed["num_elements"], "fault_elements": 0, "runtime_fields_per_record_including_node_id": RUNTIME_VALUE_COUNT, **runtime_meta},
        "permutation": {"is_bijection": True, "inverse_exact": True, "repeat_invocation_identical": True, "serialization_sha256_little_endian_int64": map_doc["serialized_maps_sha256_little_endian_int64"]},
        "preservation": {"triangle_order_preserved": True, "triangle_local_orientation_preserved": True, "node_coordinates_and_other_feg_tokens_preserved": True, "runtime_fields_2_through_51_preserved_as_exact_text": True, "feg_roundtrip_byte_identical": True, "runtime_roundtrip_byte_identical": True, "canonical_inputs_modified": False, "world_history_changed": False},
        "ksize": {"original": original_ksize, "reordered": mapped_ksize, "matrix_bytes_reduction_factor": original_ksize["matrix_bytes"] / mapped_ksize["matrix_bytes"], "matrix_bytes_reduction_percent": 100.0 * (1 - mapped_ksize["matrix_bytes"] / original_ksize["matrix_bytes"])},
        "artifacts": {"derived_feg": str(derived_feg_path.relative_to(output_dir)).replace("\\", "/"), "derived_runtime_package": str(derived_package_path.relative_to(output_dir)).replace("\\", "/"), "permutation": str(perm_path.relative_to(output_dir)).replace("\\", "/"), "fair_staging_input_dir": str(staging_input.relative_to(output_dir)).replace("\\", "/"), "sha256": derived_hashes},
        "fair_boundary": {"allowed": ["compile isolated preflight source", "validate FEG/runtime staging compatibility", "execute KSize only"], "forbidden": ["stiffness allocation", "ShellSet mechanics solve", "OrbData mechanics", "canonical input replacement"], "preflight_runner_provided": False, "contract_only": True, "launch_authorized": False},
        "preserved_gates": {"canonical_state_changed": False, "world_history_changed": False, "mechanics_executed": False, "solve_executed": False, "t1_created": False, "t2_created": False},
    }
    report_json = output_dir / "reports" / "BW1_REPORT.json"
    report_md = output_dir / "reports" / "BW1_REPORT.md"
    _write_json(report_json, report)
    _write_text(report_md, _render_report(report))
    staging_contract = output_dir / "fair_staging" / "BW1_FAIR_PREFLIGHT_CONTRACT.md"
    _write_text(staging_contract, _render_contract(report))
    # This manifest seals the input/permutation artifacts; reports intentionally
    # reference its hash and are therefore not included in the manifest itself.
    manifest_files = [perm_path, derived_feg_path, derived_package_path, staging_input / FEG_NAME, staging_input / PACKAGE_NAME]
    manifest = {"schema": "R6_SI1_BW1_ARTIFACT_MANIFEST_V1", "classification": "NON_CANONICAL_ENGINEERING_REORDERED_INPUT", "files": [{"path": str(path.relative_to(output_dir)).replace("\\", "/"), "size_bytes": path.stat().st_size, "sha256": _sha256(path)} for path in sorted(manifest_files, key=lambda p: str(p.relative_to(output_dir)).casefold())]}
    manifest_path = output_dir / "manifests" / "BW1_INPUT_MANIFEST.json"
    _write_json(manifest_path, manifest)
    report["artifacts"]["manifest"] = str(manifest_path.relative_to(output_dir)).replace("\\", "/")
    report["artifacts"]["manifest_sha256"] = _sha256(manifest_path)
    _write_json(report_json, report)
    _write_text(report_md, _render_report(report))
    report["artifact_manifest_validation"] = verify_output_manifest(output_dir)
    _write_json(report_json, report)
    _write_text(report_md, _render_report(report))
    return report


def _read_feg_full(path: Path) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    lines = _read_lines(path)
    parsed = parse_shellset_feg(path)
    n_nodes, n_triangles = parsed["num_nodes"], parsed["num_elements"]
    node_end = 2 + n_nodes
    triangle_count_end = node_end + 1
    triangle_end = triangle_count_end + n_triangles
    fault_end = triangle_end + 1
    if fault_end != len(lines):
        raise ValueError("unexpected FEG framing or trailing content")
    return lines[:2], lines[2:node_end], lines[node_end:triangle_count_end], lines[triangle_count_end:triangle_end], lines[triangle_end:fault_end]


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _copy_bytes(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def _render_report(report: dict[str, Any]) -> str:
    ksize = report["ksize"]
    return "\n".join([
        "# R6 SI1-BW1 Isolated Mesh Reordering Report", "",
        f"Decision: `{report['decision']}` — {report['decision_reason']}", "",
        "Classification: `NON_CANONICAL_ENGINEERING_REORDERED_INPUT`. This is an input-compatibility and KSize preflight candidate, not a canonical mesh or physical-state change.", "",
        f"- Nodes / triangles / fault elements: {report['counts']['nodes']:,} / {report['counts']['triangles']:,} / {report['counts']['fault_elements']}.",
        f"- Runtime record fields including node ID: {report['counts']['runtime_fields_per_record_including_node_id']}.",
        f"- SciPy: {report['source']['scipy_version']}.",
        f"- Permutation SHA256 (little-endian int64 maps): `{report['permutation']['serialization_sha256_little_endian_int64']}`.",
        "", "## KSize comparison", "",
        "| Metric | Original | Reordered |", "|---|---:|---:|",
        f"| nCodiagonals | {ksize['original']['nCodiagonals']:,} | {ksize['reordered']['nCodiagonals']:,} |",
        f"| nKRows | {ksize['original']['nKRows']:,} | {ksize['reordered']['nKRows']:,} |",
        f"| Estimated REAL*8 matrix bytes | {ksize['original']['matrix_bytes']:,} | {ksize['reordered']['matrix_bytes']:,} |",
        f"| Memory reduction | — | {ksize['matrix_bytes_reduction_percent']:.6f}% ({ksize['matrix_bytes_reduction_factor']:.3f}x) |",
        "", "## Preservation checks", "",
        "All node-record text except the node identifier is retained in its source spelling. Triangle element order and local vertex order are unchanged; all node references are remapped. Both derived files pass byte-identical inverse reconstruction.",
        "", "The derived files are duplicated into the isolated Fair staging `INPUT` directory under ShellSet's expected filenames. The accompanying contract is deliberately preflight-only. No compile, MPI, ShellSet, OrbData, mechanics, or solve was executed on Windows.",
        "", "Original governed FEG/runtime files and WORLD_HISTORY were not modified. RCM changes only node numbering/order and is not a scientific or canonical authority decision.", "",
    ])


def _render_contract(report: dict[str, Any]) -> str:
    return "\n".join([
        "# SI1-BW1 Fair Preflight Contract", "",
        "Classification: `NON_CANONICAL_ENGINEERING_REORDERED_INPUT`.", "",
        "Use only the files staged in this directory's `INPUT/` subdirectory. They use the original ShellSet filenames but are a distinct derived FEG/runtime pair; do not replace canonical inputs.", "",
        f"FEG SHA256: `{report['artifacts']['sha256']['staged_feg']}`", "",
        f"Runtime package SHA256: `{report['artifacts']['sha256']['staged_runtime_package']}`", "",
        "## Permitted on Fair", "",
        "1. Copy the two staged files into a disposable isolated ShellSet run directory under `INPUT/`.",
        "2. Supply the same already-qualified SI1 control files that are not node-indexed (parameter/control inputs, plate outlines, and required non-node-indexed boundary-condition files), without editing them.",
        "3. Build only a disposable preflight source copy instrumented to print the KSize values and terminate immediately after KSize returns.",
        "4. Confirm the printed values are `nRank=128884`, `nCodiagonals=727`, `nKRows=2182`, and `matrix_bytes=2249799104`.",
        "5. Verify termination occurs before stiffness-matrix allocation and before mechanics/solve entry.", "",
        "## Prohibited", "",
        "Do not invoke the existing SI1 engineering solve runner unchanged: its normal below-cap path can continue into mechanics. Do not allocate stiffness, run SHELLS/OrbData mechanics, use production MPI solve mode, overwrite governed files, or publish this pair as canonical.", "",
        "This repository deliverable supplies the isolated staging contract only; it does not supply a preflight executable or claim Fair execution. Any inability to prove an immediate post-KSize stop is a fail-closed reason to stop the Fair run.", "",
    ])
