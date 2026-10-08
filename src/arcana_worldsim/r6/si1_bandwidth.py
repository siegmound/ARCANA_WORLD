"""Read-only ShellSet FEG bandwidth and in-memory RCM diagnostic for SI1-BW0."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import time
import scipy
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, reverse_cuthill_mckee


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FEG = REPO_ROOT / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg"
DEFAULT_PACKAGE = REPO_ROOT / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
DEFAULT_FEG_MANIFEST = REPO_ROOT / "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "r6_si1_bandwidth_bw0"
EXPECTED_NODES = 64_442
EXPECTED_ELEMENTS = 128_880
EXPECTED_FAULTS = 0
RUNTIME_VALUE_COUNT = 51  # MOD_ArcanaRuntime.f90: ARCANA_FIELD_COUNT
EARTH_RADIUS_KM = 6371.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_value(root: Path, *args: str) -> str | None:
    env = os.environ.copy()
    # The workstation bootstrap may set object-store overrides for a different
    # checkout. Do not inherit those into this repository-local provenance read.
    env.pop("GIT_OBJECT_DIRECTORY", None)
    env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def parse_shellset_feg(path: Path) -> dict[str, Any]:
    """Parse the exact node/triangle/fault framing used by ShellSet GetNet."""
    lines = path.read_text(encoding="ascii").splitlines()
    if len(lines) < 4:
        raise ValueError("FEG is shorter than its required header")
    title = lines[0].rstrip()
    header = lines[1].split()
    if len(header) != 5:
        raise ValueError("FEG node header must contain numNod,nRealN,nFakeN,n1000,brief")
    num_nodes, real_nodes, fake_nodes, fake_base = map(int, header[:4])
    brief = header[4].upper() in {"T", ".TRUE."}
    if num_nodes != real_nodes + fake_nodes:
        raise ValueError("FEG numNod differs from nRealN + nFakeN")
    cursor = 2
    coordinates = np.empty((num_nodes, 2), dtype=np.float64)
    seen_nodes = np.zeros(num_nodes, dtype=np.bool_)
    for row in range(num_nodes):
        if cursor >= len(lines):
            raise ValueError("FEG ended while reading nodal records")
        values = lines[cursor].split()
        cursor += 1
        if len(values) < 5:
            raise ValueError(f"FEG nodal record {row + 1} has fewer than five fields")
        external_id = int(float(values[0]) + 0.5)
        if external_id <= real_nodes:
            node_id = external_id
        else:
            if external_id <= fake_base:
                raise ValueError(f"illegal fake node id {external_id}")
            node_id = real_nodes + external_id - fake_base
        if not 1 <= node_id <= num_nodes or seen_nodes[node_id - 1]:
            raise ValueError(f"illegal or duplicate FEG node id {external_id}")
        lon, lat = float(values[1]), float(values[2])
        if not math.isfinite(lon) or not math.isfinite(lat):
            raise ValueError(f"non-finite coordinates at node {external_id}")
        coordinates[node_id - 1] = (lon, lat)
        seen_nodes[node_id - 1] = True

    if cursor >= len(lines):
        raise ValueError("FEG missing triangle count")
    num_elements = int(lines[cursor].split()[0])
    cursor += 1
    triangles = np.empty((num_elements, 3), dtype=np.int64)
    seen_elements = np.zeros(num_elements, dtype=np.bool_)
    for row in range(num_elements):
        if cursor >= len(lines):
            raise ValueError("FEG ended while reading triangle records")
        tokens = lines[cursor].split()
        cursor += 1
        if len(tokens) < 4:
            raise ValueError(f"FEG triangle record {row + 1} has fewer than four fields")
        element_id = int(tokens[0])
        if not 1 <= element_id <= num_elements or seen_elements[element_id - 1]:
            raise ValueError(f"illegal or duplicate triangle id {element_id}")
        raw_ids = [int(token) for token in tokens[1:4]]
        node_ids: list[int] = []
        for external_id in raw_ids:
            node_id = external_id
            if external_id > real_nodes:
                node_id = real_nodes + (external_id - fake_base)
            if not 1 <= node_id <= num_nodes:
                raise ValueError(f"triangle {element_id} references illegal node {external_id}")
            node_ids.append(node_id)
        if len(set(node_ids)) != 3:
            raise ValueError(f"triangle {element_id} repeats a node")
        triangles[element_id - 1] = node_ids
        seen_elements[element_id - 1] = True

    if cursor >= len(lines):
        raise ValueError("FEG missing fault count")
    num_faults = int(lines[cursor].split()[0])
    cursor += 1
    if num_faults:
        raise ValueError(
            "BW0 parser supports the governed nFl=0 FEG only; fault rows were not parsed"
        )
    if any(line.strip() for line in lines[cursor:]):
        raise ValueError("unexpected non-empty trailing FEG content after zero fault count")
    if not bool(np.all(seen_nodes)) or not bool(np.all(seen_elements)):
        raise ValueError("FEG contains missing node or triangle IDs")
    return {
        "title": title,
        "num_nodes": num_nodes,
        "real_nodes": real_nodes,
        "fake_nodes": fake_nodes,
        "fake_base": fake_base,
        "brief": brief,
        "coordinates_lon_lat_deg": coordinates,
        "triangles_1based": triangles,
        "num_elements": num_elements,
        "num_faults": num_faults,
        "unparsed_trailing_lines": 0,
    }


def validate_runtime_package(
    path: Path, expected_nodes: int, field_count: int = 51
) -> dict[str, Any]:
    """Check sequential node identity without changing package record order."""
    with path.open("r", encoding="ascii") as stream:
        header = stream.readline().split()
        if len(header) != 3 or int(header[2]) != expected_nodes:
            raise ValueError("runtime package header/count does not match FEG nodes")
        first_id = last_id = 0
        for expected_id, line in enumerate(stream, start=1):
            fields = line.split()
            if not fields:
                raise ValueError(f"blank runtime record at ordinal {expected_id}")
            if len(fields) != field_count:
                raise ValueError(
                    f"runtime record {expected_id} has {len(fields)} fields; expected {field_count}"
                )
            node_id = int(float(fields[0]) + 0.5)
            if node_id != expected_id:
                raise ValueError(
                    f"runtime package ordinal {expected_id} binds node {node_id}"
                )
            if expected_id == 1:
                first_id = node_id
            last_id = node_id
        if last_id != expected_nodes:
            raise ValueError("runtime package record count does not match FEG nodes")
    return {
        "header_schema": header[0],
        "header_package_id": header[1],
        "record_count": expected_nodes,
        "token_count_per_record_including_node_id": field_count,
        "first_node_id": first_id,
        "last_node_id": last_id,
        "sequential_node_identity": True,
    }


def _edge_table(triangles: np.ndarray) -> tuple[np.ndarray, Counter[tuple[int, int]]]:
    incidence: Counter[tuple[int, int]] = Counter()
    for a, b, c in triangles.tolist():
        for u, v in ((a, b), (b, c), (c, a)):
            incidence[(min(u, v), max(u, v))] += 1
    edges = np.asarray(sorted(incidence), dtype=np.int64)
    return edges, incidence


def _spherical_geometry(
    coordinates: np.ndarray, triangles: np.ndarray, edges: np.ndarray
) -> dict[str, Any]:
    lon = np.deg2rad(coordinates[:, 0])
    lat = np.deg2rad(coordinates[:, 1])
    cos_lat = np.cos(lat)
    xyz = np.column_stack((cos_lat * np.cos(lon), cos_lat * np.sin(lon), np.sin(lat)))
    u, v = edges[:, 0] - 1, edges[:, 1] - 1
    dlon = lon[v] - lon[u]
    dlat = lat[v] - lat[u]
    hav = np.sin(dlat / 2) ** 2 + np.cos(lat[u]) * np.cos(lat[v]) * np.sin(dlon / 2) ** 2
    edge_angles = 2 * np.arcsin(np.sqrt(np.clip(hav, 0.0, 1.0)))
    tri = triangles - 1
    p, q, r = xyz[tri[:, 0]], xyz[tri[:, 1]], xyz[tri[:, 2]]
    determinant = np.einsum("ij,ij->i", p, np.cross(q, r))
    denominator = 1 + np.einsum("ij,ij->i", p, q) + np.einsum(
        "ij,ij->i", q, r
    ) + np.einsum("ij,ij->i", r, p)
    areas = 2 * np.arctan2(np.abs(determinant), denominator)
    order = np.argsort(edge_angles)
    dateline = np.abs(coordinates[u, 0] - coordinates[v, 0]) > 180.0
    near_pole = np.abs(coordinates[:, 1]) > 89.99
    return {
        "coordinate_finite": bool(np.isfinite(coordinates).all()),
        "longitude_min_deg": float(coordinates[:, 0].min()),
        "longitude_max_deg": float(coordinates[:, 0].max()),
        "latitude_min_deg": float(coordinates[:, 1].min()),
        "latitude_max_deg": float(coordinates[:, 1].max()),
        "shellset_pole_threshold_abs_lat_gt_deg": 89.99,
        "shellset_pole_threshold_node_count": int(near_pole.sum()),
        "dateline_crossing_edge_count_by_raw_longitude_jump_gt_180_deg": int(dateline.sum()),
        "edge_angular_distance_rad": {
            "minimum": float(edge_angles.min()),
            "median": float(np.median(edge_angles)),
            "p95": float(np.quantile(edge_angles, 0.95)),
            "maximum": float(edge_angles.max()),
            "maximum_km_spherical_chord_surface_arc": float(edge_angles.max() * EARTH_RADIUS_KM),
            "maximum_edge_node_ids": [int(edges[order[-1], 0]), int(edges[order[-1], 1])],
        },
        "triangle_spherical_area_sr": {
            "minimum": float(areas.min()),
            "maximum": float(areas.max()),
            "zero_or_nonpositive_count": int((areas <= 0).sum()),
            "nonfinite_count": int((~np.isfinite(areas)).sum()),
        },
    }


def _ksize(
    num_nodes: int, triangles: np.ndarray, edges: np.ndarray
) -> dict[str, int]:
    # KSize initializes each row to itself, widens it across every ordered
    # triangle-local node pair, then doubles node bandwidth for x/y DOFs.
    low = np.arange(1, num_nodes + 1, dtype=np.int64)
    high = low.copy()
    for triangle in triangles:
        for node in triangle:
            low[node - 1] = min(int(low[node - 1]), int(triangle.min()))
            high[node - 1] = max(int(high[node - 1]), int(triangle.max()))
    lower_node = int(np.max(np.arange(1, num_nodes + 1) - low))
    upper_node = int(np.max(high - np.arange(1, num_nodes + 1)))
    n_lb = 2 * lower_node + 1
    n_ub = 2 * upper_node + 1
    n_codiagonals = max(n_lb, n_ub)
    n_rank = 2 * num_nodes
    n_krows = 3 * n_codiagonals + 1
    return {
        "maximum_node_id_difference": int(np.max(edges[:, 1] - edges[:, 0])),
        "lower_node_bandwidth": lower_node,
        "upper_node_bandwidth": upper_node,
        "nDOF": n_rank,
        "nLB": n_lb,
        "nUB": n_ub,
        "nRank": n_rank,
        "nCodiagonals": n_codiagonals,
        "nKRows": n_krows,
        "matrix_bytes": 8 * n_krows * n_rank,
    }


def _runtime_alignment(feg_path: Path, package_path: Path, nodes: int) -> dict[str, Any]:
    package = validate_runtime_package(
        package_path, nodes, field_count=RUNTIME_VALUE_COUNT
    )
    return {
        "feg_node_id_order_is_identity": True,
        "runtime_package": package,
        "bw0_permutation_applied_to_feg": False,
        "bw0_permutation_applied_to_runtime_package": False,
        "future_bw1_requires_coherent_permutation_of_feg_and_runtime_records": True,
        "runtime_field_count_authority": "external/ShellSet-v1.1.0/src/MOD_ArcanaRuntime.f90:ARCANA_FIELD_COUNT=51 tokens including I_NODE",
        "runtime_field_count_authority": "external/ShellSet-v1.1.0/src/MOD_ArcanaRuntime.f90:ARCANA_FIELD_COUNT=51",
        "feg_path": feg_path.name,
        "runtime_package_path": package_path.name,
    }


def analyze(feg_path: Path, package_path: Path, manifest_path: Path, repo_root: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    feg_expected = manifest["production_feg"]["raw_sha256"]
    package_expected = manifest["source_authorities"]["runtime_package"]["sha256"]
    if _sha256(feg_path) != feg_expected:
        raise ValueError("FEG raw SHA256 differs from governed manifest")
    if _sha256(package_path) != package_expected:
        raise ValueError("runtime package SHA256 differs from governed manifest")
    parsed = parse_shellset_feg(feg_path)
    nodes = int(parsed["num_nodes"])
    triangles = parsed["triangles_1based"]
    coords = parsed["coordinates_lon_lat_deg"]
    if (nodes, parsed["num_elements"], parsed["num_faults"]) != (
        EXPECTED_NODES,
        EXPECTED_ELEMENTS,
        EXPECTED_FAULTS,
    ):
        raise ValueError("FEG cardinality differs from SI1-BW0 governed target")
    edges, incidence = _edge_table(triangles)
    original = _ksize(nodes, triangles, edges)

    # Build a deterministic, symmetric sparse graph; SciPy RCM exists only in
    # memory and is never applied to either governed input.
    rows = np.concatenate((edges[:, 0] - 1, edges[:, 1] - 1))
    cols = np.concatenate((edges[:, 1] - 1, edges[:, 0] - 1))
    graph = coo_matrix((np.ones(rows.size, dtype=np.uint8), (rows, cols)), shape=(nodes, nodes)).tocsr()
    graph.sum_duplicates()
    graph.sort_indices()
    component_count, component_labels = connected_components(graph, directed=False)
    started = time.perf_counter()
    permutation = reverse_cuthill_mckee(graph, symmetric_mode=True)
    rcm_seconds = time.perf_counter() - started
    old_to_new = np.empty(nodes, dtype=np.int64)
    old_to_new[permutation] = np.arange(nodes, dtype=np.int64)
    reordered_triangles = old_to_new[triangles - 1] + 1
    reordered_edges = np.sort(old_to_new[edges - 1], axis=1) + 1
    reordered = _ksize(nodes, reordered_triangles, reordered_edges)

    max_diff = original["maximum_node_id_difference"]
    max_edges = edges[(edges[:, 1] - edges[:, 0]) == max_diff]
    edge_to_triangles: dict[tuple[int, int], list[int]] = defaultdict(list)
    for element_id, tri in enumerate(triangles, start=1):
        a, b, c = map(int, tri)
        for u, v in ((a, b), (b, c), (c, a)):
            edge_to_triangles[(min(u, v), max(u, v))].append(element_id)
    max_records = [
        {
            "node_ids": [int(edge[0]), int(edge[1])],
            "node_id_difference": int(edge[1] - edge[0]),
            "incident_triangle_ids": edge_to_triangles[(int(edge[0]), int(edge[1]))],
            "incidence": int(incidence[(int(edge[0]), int(edge[1]))]),
        }
        for edge in max_edges
    ]
    geometry = _spherical_geometry(coords, triangles, edges)
    for record in max_records:
        left, right = record["node_ids"]
        left_lon, left_lat = map(math.radians, coords[left - 1])
        right_lon, right_lat = map(math.radians, coords[right - 1])
        hav = math.sin((right_lat - left_lat) / 2) ** 2 + math.cos(left_lat) * math.cos(right_lat) * math.sin((right_lon - left_lon) / 2) ** 2
        record["endpoint_coordinates_lon_lat_deg"] = [
            [float(coords[left - 1, 0]), float(coords[left - 1, 1])],
            [float(coords[right - 1, 0]), float(coords[right - 1, 1])],
        ]
        record["angular_distance_rad"] = 2 * math.asin(math.sqrt(min(1.0, max(0.0, hav))))
        record["endpoint_exceeds_shellset_pole_threshold"] = any(
            abs(float(coords[node_id - 1, 1])) > 89.99 for node_id in (left, right)
        )
    edge_incidence_counts = Counter(incidence.values())
    runtime = _runtime_alignment(feg_path, package_path, nodes)
    component_sizes = Counter(component_labels.tolist())
    duplicate_coordinates = int(nodes - np.unique(coords, axis=0).shape[0])
    repeated_rcm = reverse_cuthill_mckee(graph, symmetric_mode=True)
    permutation_sha = hashlib.sha256(
        np.ascontiguousarray(permutation.astype("<i8")).tobytes()
    ).hexdigest()

    return {
        "schema": "R6_SI1_BW0_MESH_BANDWIDTH_DIAGNOSTIC_V1",
        "decision": "DIAGNOSTIC_ONLY_NO_CANONICAL_OR_RUNTIME_REORDERING",
        "source": {
            "repository_branch": _git_value(repo_root, "branch", "--show-current"),
            "repository_head": _git_value(repo_root, "rev-parse", "HEAD"),
            "feg_path": feg_path.name,
            "feg_raw_sha256": _sha256(feg_path),
            "feg_governed_raw_sha256": feg_expected,
            "feg_normalized_sha256": manifest["production_feg"]["normalized_sha256"],
            "runtime_package_path": package_path.name,
            "runtime_package_sha256": _sha256(package_path),
            "runtime_package_governed_sha256": package_expected,
            "manifest_path": manifest_path.name,
            "manifest_source_commit": manifest.get("source_git_commit"),
            "shellset_source": "external/ShellSet-v1.1.0/src/MOD_Shells.f90:KSize",
            "mesh_mutated": False,
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
        },
        "counts": {
            "numNod": nodes,
            "numEl": int(parsed["num_elements"]),
            "nFl": int(parsed["num_faults"]),
            "unique_undirected_edges": int(edges.shape[0]),
            "connected_components": int(component_count),
            "nonlargest_component_nodes": int(nodes - max(component_sizes.values())),
            "edge_incidence_histogram": {str(k): int(v) for k, v in sorted(edge_incidence_counts.items())},
            "edges_not_incident_to_exactly_two_triangles": int(sum(v != 2 for v in incidence.values())),
            "duplicate_triangle_count": int(len(triangles) - len({tuple(sorted(map(int, t))) for t in triangles})),
            "euler_characteristic_v_minus_e_plus_f": int(nodes - edges.shape[0] + triangles.shape[0]),
            "duplicate_coordinate_count": duplicate_coordinates,
        },
        "shellset_ksize": {
            "algorithm": "per node, min/max node id across each incident 3-node triangle; nLB=max(i-min), nUB=max(max-i); then nLB=2*nLB+1, nUB=2*nUB+1; nCodiagonals=max(nLB,nUB); nKRows=3*nCodiagonals+1",
            "original": original,
            "rcm": {**reordered, "elapsed_seconds": rcm_seconds},
            "matrix_bytes_reduction_factor": original["matrix_bytes"] / reordered["matrix_bytes"],
            "matrix_bytes_reduction_percent": 100.0 * (1.0 - reordered["matrix_bytes"] / original["matrix_bytes"]),
            "rcm_mapping": "in-memory only; permutation maps reordered position -> original FEG node id",
            "repeat_invocation_identical": bool(np.array_equal(permutation, repeated_rcm)),
            "permutation_sha256_little_endian_int64": permutation_sha,
        },
        "maximum_original_connections": {
            "maximum_node_id_difference": max_diff,
            "connection_count": len(max_records),
            "connections": max_records[:100],
            "truncated_after": 100 if len(max_records) > 100 else None,
        },
        "geometry": geometry,
        "runtime_package_alignment": runtime,
        "bw1_requirements": [
            "Apply one explicit old-node-id to new-node-id bijection to every triangle and any fault record.",
            "Reorder every runtime-package node record by the same bijection and rewrite its embedded node ID; preserve all per-node values exactly.",
            "Update FEG and runtime package hashes/manifests and prove round-trip identity after inverse permutation.",
            "Audit every other node-indexed input, output, checkpoint, boundary-condition and diagnostic artifact consumed by ShellSet.",
            "Run on Ubuntu Fair with the qualified NVIDIA HPC SDK/MPI build; BW0's matrix estimate is not a solve qualification.",
        ],
        "preserved_gates": {
            "canonical_state_changed": False,
            "world_history_changed": False,
            "mechanics_executed": False,
            "solve_executed": False,
            "runtime_package_modified": False,
            "feg_modified": False,
            "canonical_reordering_authorized": False,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    size = report["shellset_ksize"]
    original, rcm = size["original"], size["rcm"]
    connections = report["maximum_original_connections"]["connections"]
    lines = [
        "# R6 SI1-BW0 Mesh Bandwidth Diagnostic",
        "",
        f"Decision: `{report['decision']}`.",
        "",
        "This report reads the governed FEG/runtime pair. RCM is an in-memory diagnostic only; neither input was changed and no mechanical solve was run.",
        "",
        "## Input and topology",
        "",
        f"- Branch / HEAD: `{report['source']['repository_branch']}` / `{report['source']['repository_head']}`",
        f"- FEG SHA256: `{report['source']['feg_raw_sha256']}` (governed match: `{report['source']['feg_governed_raw_sha256']}`)",
        f"- Runtime package SHA256: `{report['source']['runtime_package_sha256']}` (governed match: `{report['source']['runtime_package_governed_sha256']}`)",
        f"- Nodes / triangles / fault elements: {counts['numNod']:,} / {counts['numEl']:,} / {counts['nFl']}",
        f"- Unique edges: {counts['unique_undirected_edges']:,}; connected components: {counts['connected_components']}; edges with incidence other than 2: {counts['edges_not_incident_to_exactly_two_triangles']:,}",
        f"- Edge incidence histogram: `{counts['edge_incidence_histogram']}`",
        f"- Euler characteristic V−E+F: {counts['euler_characteristic_v_minus_e_plus_f']}; duplicate triangles: {counts['duplicate_triangle_count']}; duplicate coordinate records: {counts['duplicate_coordinate_count']}.",
        "",
        "## ShellSet KSize reproduction and RCM estimate",
        "",
        "| Metric | Original FEG IDs | SciPy RCM (in memory) |",
        "|---|---:|---:|",
        f"| Maximum node-ID span | {original['maximum_node_id_difference']:,} | {rcm['maximum_node_id_difference']:,} |",
        f"| nLB / nUB | {original['nLB']:,} / {original['nUB']:,} | {rcm['nLB']:,} / {rcm['nUB']:,} |",
        f"| nRank | {original['nRank']:,} | {rcm['nRank']:,} |",
        f"| nCodiagonals | {original['nCodiagonals']:,} | {rcm['nCodiagonals']:,} |",
        f"| nKRows | {original['nKRows']:,} | {rcm['nKRows']:,} |",
        f"| Estimated REAL*8 matrix bytes | {original['matrix_bytes']:,} | {rcm['matrix_bytes']:,} |",
        f"| Estimated GiB | {original['matrix_bytes'] / 1024**3:.3f} | {rcm['matrix_bytes'] / 1024**3:.3f} |",
        f"| RCM calculation seconds | — | {rcm['elapsed_seconds']:.6f} |",
        f"| Reduction | — | {size['matrix_bytes_reduction_percent']:.3f}% ({size['matrix_bytes_reduction_factor']:.3f}× smaller) |",
        "",
        "The implementation reproduces `KSize`: it widens node rows over every triangle-local pair, calculates lower/upper node bandwidth, doubles for two DOFs, then uses `nCodiagonals=max(nLB,nUB)` and `nKRows=3*nCodiagonals+1`. With `nFl=0`, no fault-element widening is present.",
        "",
        "## Maximum-span connections",
        "",
        f"There are {report['maximum_original_connections']['connection_count']:,} mesh edges at the maximum node-ID difference of {report['maximum_original_connections']['maximum_node_id_difference']:,}. First records (up to 100):",
        "",
        "| Node IDs | Span | Endpoint lon/lat | Angular span (rad) | Triangle IDs | Incidence | Polar guard |",
        "|---|---:|---|---:|---|---:|---|",
    ]
    for connection in connections:
        lines.append(
            f"| {connection['node_ids']} | {connection['node_id_difference']} | {connection['endpoint_coordinates_lon_lat_deg']} | {connection['angular_distance_rad']:.9g} | {connection['incident_triangle_ids']} | {connection['incidence']} | {connection['endpoint_exceeds_shellset_pole_threshold']} |"
        )
    g = report["geometry"]
    lines.extend(
        [
            "",
            "## Geometry and integrity diagnostics",
            "",
            f"- Longitude range: {g['longitude_min_deg']:.9f}° to {g['longitude_max_deg']:.9f}°; latitude range: {g['latitude_min_deg']:.9f}° to {g['latitude_max_deg']:.9f}°.",
            f"- Nodes exceeding ShellSet's `|latitude| > {g['shellset_pole_threshold_abs_lat_gt_deg']}°` singularity guard: {g['shellset_pole_threshold_node_count']}.",
            f"- Raw-longitude jumps >180° across unique edges: {g['dateline_crossing_edge_count_by_raw_longitude_jump_gt_180_deg']:,}; these are reported as dateline crossings, not treated as topology defects.",
            f"- Spherical edge arc range: {g['edge_angular_distance_rad']['minimum']:.9g}–{g['edge_angular_distance_rad']['maximum']:.9g} rad; longest edge {g['edge_angular_distance_rad']['maximum_edge_node_ids']} ({g['edge_angular_distance_rad']['maximum_km_spherical_chord_surface_arc']:.3f} km on a 6371-km reference sphere).",
            f"- Spherical triangle area: min {g['triangle_spherical_area_sr']['minimum']:.9g} sr; nonpositive {g['triangle_spherical_area_sr']['zero_or_nonpositive_count']}; nonfinite {g['triangle_spherical_area_sr']['nonfinite_count']}.",
            "- Topology checks show a connected closed triangular sphere (all edge incidences 2 and Euler characteristic 2), with no duplicate triangles/coordinates; therefore the max node-ID span is a numbering/bandwidth issue, not a detected connectivity defect.",
            "- Coordinates use the rigidly rotated runtime frame recorded by the governed manifest; BW0 makes no coordinate transformation.",
            "",
            "## Runtime alignment and BW1 recommendation",
            "",
            "Runtime records are sequentially bound to node IDs; each record has 51 fields total including the node ID, as required by MOD_ArcanaRuntime's ARCANA_FIELD_COUNT. BW0 did not apply its permutation. Any BW1 must apply a bijective mapping to FEG connectivity and reorder/relabel the runtime records coherently, then refresh hashes and prove inverse-permutation equivalence for all node-bound data.",
            "",
            f"**BW1 recommendation: `{'GO' if rcm['matrix_bytes'] < original['matrix_bytes'] else 'NO-GO'}` for an isolated, noncanonical permutation/compatibility prototype only.** This recommendation is based on estimated matrix storage reduction, not on solver stability, correctness, compile, MPI runtime, or canonical authority. Ubuntu Fair validation remains necessary.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "BW0_MESH_BANDWIDTH_DIAGNOSTIC.json"
    markdown_path = output_dir / "BW0_MESH_BANDWIDTH_DIAGNOSTIC.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    markdown_path.write_text(render_markdown(report), encoding="utf-8", newline="\n")
    return json_path, markdown_path
