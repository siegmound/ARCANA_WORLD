"""Read-only canonical grid to deterministic ShellSet triangle topology adapter.

This creates numerical support only. One-degree small-circle latitude edges are
represented by great-circle triangle edges between canonical vertices; no
geometric tolerance or physical nodal field is implied by this conversion.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from arcana_worldsim.r6.repository_context import resolve_external_payload_path

PARTITION_MANIFEST = "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"
EXPECTED_PARENT_SHA256 = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
EXPECTED_PAYLOAD_SHA256 = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
PROVIDER_VERSION = "ARCANA_CANONICAL_GRID_FACE_TRIANGULATION_V1"


@dataclass(frozen=True)
class CanonicalMesh:
    """Stable vertex, triangle and provenance arrays; IDs are one-based."""

    vertices_lat_lon: np.ndarray
    triangles: np.ndarray
    triangle_parent_face: np.ndarray
    triangle_plate_id: np.ndarray
    parent_face_triangles: tuple[tuple[int, ...], ...]
    boundary_edge_nodes: tuple[tuple[int, int], ...]
    boundary_ids: tuple[str, ...]
    adjacency_supports: tuple[tuple[tuple[int, int], tuple[str, ...]], ...]
    junction_node_ids: tuple[tuple[str, int], ...]
    plate_triangle_ids: tuple[tuple[int, tuple[int, ...]], ...]
    normalized_sha256: str
    audit: dict[str, Any]


def _node_id(row_line: int, col_line: int) -> int:
    """Map grid-line coordinates to stable FEG IDs, collapsing both poles."""
    if row_line == 0:
        return 1
    if row_line == 180:
        return 2
    return 3 + (row_line - 1) * 360 + (col_line % 360)


def _vertex(row_line: int, col_line: int) -> tuple[float, float]:
    if row_line == 0:
        return -90.0, 0.0
    if row_line == 180:
        return 90.0, 0.0
    longitude = -180.0 + (col_line % 360)
    return float(-90 + row_line), float(longitude)


def _unit_vectors(vertices: np.ndarray) -> np.ndarray:
    lat = np.radians(vertices[:, 0])
    lon = np.radians(vertices[:, 1])
    return np.column_stack((np.cos(lat) * np.cos(lon),
                            np.cos(lat) * np.sin(lon), np.sin(lat)))


def _normalized_hash(vertices: np.ndarray, triangles: np.ndarray,
                     parent: np.ndarray, plates: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(b"R6_SHELLSET_CANONICAL_GRID_TRIANGULATION_V1\0")
    for label, array in ((b"vertices", np.round(vertices, 12).astype("<f8")),
                         (b"triangles", triangles.astype("<i8")),
                         (b"parent", parent.astype("<i8")),
                         (b"plates", plates.astype("<i8"))):
        digest.update(label + b"\0")
        digest.update(np.asarray(array.shape, dtype="<i8").tobytes())
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _validate_face_rings(arrays: dict[str, np.ndarray]) -> dict[str, int]:
    rows, cols = arrays["face_row"], arrays["face_col"]
    plates, rings = arrays["face_plate_id"], arrays["face_vertex_latlon_deg"]
    n = len(rows)
    if n != 64_800 or cols.shape != (n,) or plates.shape != (n,) or rings.shape != (n, 5, 2):
        raise ValueError("canonical grid arrays have unexpected shapes/counts")
    if len(set(zip(rows.tolist(), cols.tolist()))) != n:
        raise ValueError("canonical parent cell IDs are not unique")
    arity3 = arity4 = 0
    for row, col, ring in zip(rows.tolist(), cols.tolist(), rings):
        south, west = -90 + int(row), -180 + int(col)
        expected = np.asarray(((south, west), (south, west + 1),
                               (south + 1, west + 1), (south + 1, west),
                               (south, west)), dtype=np.float64)
        if not np.array_equal(ring, expected):
            raise ValueError("face coordinates differ from declared parent grid cell")
        # Ring closure is represented by the fifth coordinate. At a pole the
        # first two or last two points are the same physical spherical point.
        if int(row) in (0, 179):
            arity3 += 1
        else:
            arity4 += 1
    return {"triangle_faces_after_pole_collapse": arity3,
            "quadrilateral_faces": arity4}


def build_canonical_mesh(arrays: dict[str, np.ndarray],
                         junction_census: dict[str, Any],
                         boundary_state: dict[str, Any] | None = None,
                         adjacency_groups: list[dict[str, Any]] | None = None) -> CanonicalMesh:
    """Triangulate each canonical cell independently with a fixed SW-NE split."""
    arity = _validate_face_rings(arrays)
    rows = arrays["face_row"].astype(np.int64, copy=False)
    cols = arrays["face_col"].astype(np.int64, copy=False)
    plates = arrays["face_plate_id"].astype(np.int64, copy=False)
    if len(rows) != 180 * 360 or set(map(int, np.unique(plates))) != set(range(12)):
        raise ValueError("canonical face/plate inventory differs from R6 invariants")

    vertices = np.empty((64_442, 2), dtype=np.float64)
    vertices[0] = _vertex(0, 0)
    vertices[1] = _vertex(180, 0)
    for r in range(1, 180):
        for c in range(360):
            vertices[_node_id(r, c) - 1] = _vertex(r, c)

    triangles: list[tuple[int, int, int]] = []
    tri_parent: list[int] = []
    tri_plate: list[int] = []
    face_triangles: list[tuple[int, ...]] = []
    for face_index, (row, col, plate) in enumerate(zip(rows, cols, plates)):
        sw = _node_id(int(row), int(col))
        se = _node_id(int(row), int(col) + 1)
        ne = _node_id(int(row) + 1, int(col) + 1)
        nw = _node_id(int(row) + 1, int(col))
        if sw == se:
            local = ((sw, ne, nw),)
        elif ne == nw:
            local = ((sw, se, ne),)
        else:
            local = ((sw, se, ne), (sw, ne, nw))
        ids = []
        for tri in local:
            ids.append(len(triangles) + 1)
            triangles.append(tri)
            tri_parent.append(face_index)
            tri_plate.append(int(plate))
        face_triangles.append(tuple(ids))

    triangle_array = np.asarray(triangles, dtype=np.int64)
    unit = _unit_vectors(vertices)
    signed = np.einsum("ij,ij->i", unit[triangle_array[:, 0]-1],
                       np.cross(unit[triangle_array[:, 1]-1], unit[triangle_array[:, 2]-1]))
    if np.any(np.abs(signed) < 1e-14):
        raise ValueError("triangulation contains a zero-area spherical triangle")
    inverted = signed < 0
    if np.any(inverted):
        triangle_array[inverted, 1], triangle_array[inverted, 2] = (
            triangle_array[inverted, 2].copy(), triangle_array[inverted, 1].copy())
        signed[inverted] *= -1

    boundary_pairs = []
    boundary_keys = []
    boundary_plate_pairs = []
    for row, col, axis in zip(arrays["boundary_edge_row"], arrays["boundary_edge_col"],
                              arrays["boundary_edge_axis"]):
        row, col, axis = int(row), int(col), int(axis)
        if axis == 0:
            pair = (_node_id(row, col + 1), _node_id(row + 1, col + 1))
            key = (row, col, "EAST")
        elif axis == 1:
            pair = (_node_id(row + 1, col), _node_id(row + 1, col + 1))
            key = (row, col, "NORTH")
        else:
            raise ValueError(f"unknown boundary edge axis {axis}")
        boundary_pairs.append(pair)
        boundary_keys.append(key)
        boundary_plate_pairs.append(tuple(sorted((int(arrays["boundary_plate_a"][len(boundary_pairs)-1]),
                                                   int(arrays["boundary_plate_b"][len(boundary_pairs)-1])))))
    if len(set(tuple(sorted(pair)) for pair in boundary_pairs)) != len(boundary_pairs):
        raise ValueError("canonical boundary segments map to duplicate mesh edges")
    if boundary_state is None:
        boundary_ids = tuple(f"UNRESOLVED_BOUNDARY_INDEX_{i:04d}"
                             for i in range(len(boundary_pairs)))
    else:
        state_records = boundary_state.get("segments", [])
        state_by_key = {}
        for record in state_records:
            edge = record["parent_grid_edge"]
            key = (int(edge["row"]), int(edge["column"]), str(edge["axis"]))
            if key in state_by_key:
                raise ValueError(f"duplicate canonical boundary key: {key}")
            state_by_key[key] = str(record["boundary_id"])
        if set(boundary_keys) != set(state_by_key):
            raise ValueError("boundary mesh edges do not match canonical boundary registry")
        boundary_ids = tuple(state_by_key[key] for key in boundary_keys)
    support_ids: dict[tuple[int, int], list[str]] = {}
    for pair, boundary_id in zip(boundary_plate_pairs, boundary_ids):
        support_ids.setdefault(pair, []).append(boundary_id)
    adjacency_supports = tuple((pair, tuple(ids)) for pair, ids in sorted(support_ids.items()))
    if adjacency_groups is not None:
        expected = {(min(int(g["plate_a"]), int(g["plate_b"])),
                     max(int(g["plate_a"]), int(g["plate_b"]))): int(g["edge_count"])
                    for g in adjacency_groups}
        observed = {pair: len(ids) for pair, ids in adjacency_supports}
        if observed != expected or len(expected) != 30 or sum(observed.values()) != 1_983:
            raise ValueError("canonical boundary to adjacency support mapping is incomplete")

    junction_nodes = []
    for record in junction_census["junctions"]:
        vertex_id = record["vertex_id"]
        if vertex_id in ("SOUTH_POLE", "NORTH_POLE"):
            row_line, col_line = (0 if vertex_id == "SOUTH_POLE" else 180), 0
        else:
            _, row_text, col_text = vertex_id.split(":")
            row_line, col_line = int(row_text), int(col_text)
        junction_nodes.append((str(record["junction_id"]), _node_id(row_line, col_line)))

    plate_triangles = tuple((int(p), tuple((np.flatnonzero(np.asarray(tri_plate) == p) + 1).tolist()))
                            for p in sorted(set(tri_plate)))
    # Every triangle edge is counted once per incident triangle.
    edge_counts: dict[tuple[int, int], int] = {}
    for x, y, z in triangle_array.tolist():
        for a, b in ((x, y), (y, z), (z, x)):
            key = (a, b) if a < b else (b, a)
            edge_counts[key] = edge_counts.get(key, 0) + 1
    incidence = sorted(edge_counts.values())
    roots = list(range(len(vertices)))

    def find(value: int) -> int:
        while roots[value] != value:
            roots[value] = roots[roots[value]]
            value = roots[value]
        return value

    for u, v in edge_counts:
        root_u, root_v = find(u - 1), find(v - 1)
        if root_u != root_v:
            roots[root_v] = root_u
    connected_components = len({find(i) for i in range(len(vertices))})
    tri_xyz = unit[triangle_array - 1]
    a, b, c = tri_xyz[:, 0], tri_xyz[:, 1], tri_xyz[:, 2]
    spherical_area = 2 * np.arctan2(
        np.abs(np.einsum("ij,ij->i", a, np.cross(b, c))),
        1 + np.einsum("ij,ij->i", a, b) + np.einsum("ij,ij->i", b, c)
        + np.einsum("ij,ij->i", c, a),
    )
    boundary_edge_keys = {tuple(sorted(pair)) for pair in boundary_pairs}
    direct_boundary_edges = len(boundary_edge_keys & set(edge_counts))
    adjacency_components = {}
    for pair, _ in adjacency_supports:
        graph: dict[int, set[int]] = {}
        for edge_pair, edge in zip(boundary_plate_pairs, boundary_pairs):
            if edge_pair == pair:
                u, v = edge
                graph.setdefault(u, set()).add(v)
                graph.setdefault(v, set()).add(u)
        seen: set[int] = set()
        component_count = 0
        for start in graph:
            if start in seen:
                continue
            component_count += 1
            pending = [start]
            seen.add(start)
            while pending:
                current = pending.pop()
                for neighbor in graph[current] - seen:
                    seen.add(neighbor)
                    pending.append(neighbor)
        adjacency_components[f"{pair[0]}:{pair[1]}"] = component_count
    audit = {
        "face_count": len(rows), "face_arity_distribution": {"3": arity["triangle_faces_after_pole_collapse"],
                                                                  "4": arity["quadrilateral_faces"]},
        "node_count": len(vertices), "triangle_count": len(triangle_array),
        "edge_count": len(edge_counts), "edge_incidence_distribution": {
            str(k): incidence.count(k) for k in sorted(set(incidence))},
        "euler_characteristic": len(vertices) - len(edge_counts) + len(triangle_array),
        "connected_components": connected_components, "boundary_edge_count": len(boundary_pairs),
        "boundary_direct_feg_edges": direct_boundary_edges,
        "junction_count": len(junction_nodes), "plate_count": len(plate_triangles),
        "adjacency_support_count": len(adjacency_supports),
        "adjacency_support_components": adjacency_components,
        "orientation_corrections": int(inverted.sum()),
        "zero_area_triangles": int(np.count_nonzero(np.abs(signed) < 1e-14)),
        "minimum_spherical_triangle_area_sr": float(spherical_area.min()),
        "spherical_area_sum_sr": float(spherical_area.sum()),
    }
    if (len(triangle_array) != 128_880 or len(edge_counts) != 193_320
            or set(incidence) != {2} or audit["euler_characteristic"] != 2
            or len(boundary_pairs) != 1_983 or len(junction_nodes) != 20
            or len(adjacency_supports) != 30 or connected_components != 1
            or direct_boundary_edges != 1_983 or set(adjacency_components.values()) != {1}
            or np.any(spherical_area <= 0)
            or abs(float(spherical_area.sum()) - 4 * math.pi) > 1e-10
            or audit["orientation_corrections"] != 0):
        raise ValueError(f"spherical mesh topology validation failed: {audit}")
    digest = _normalized_hash(vertices, triangle_array, np.asarray(tri_parent), np.asarray(tri_plate))
    return CanonicalMesh(
        vertices_lat_lon=vertices, triangles=triangle_array,
        triangle_parent_face=np.asarray(tri_parent, dtype=np.int64),
        triangle_plate_id=np.asarray(tri_plate, dtype=np.int64),
        parent_face_triangles=tuple(face_triangles), boundary_edge_nodes=tuple(boundary_pairs),
        boundary_ids=boundary_ids, adjacency_supports=adjacency_supports,
        junction_node_ids=tuple(junction_nodes), plate_triangle_ids=plate_triangles,
        normalized_sha256=digest, audit=audit,
    )


def load_canonical_mesh(repository_root: str | Path) -> CanonicalMesh:
    root = Path(repository_root).resolve()
    manifest = json.loads((root / PARTITION_MANIFEST).read_text(encoding="utf-8"))
    if manifest.get("canonical_parent_sha256") != EXPECTED_PARENT_SHA256:
        raise ValueError("canonical parent identity differs from the R6 manifest")
    if manifest.get("payload", {}).get("sha256") != EXPECTED_PAYLOAD_SHA256:
        raise ValueError("canonical vector partition identity differs from the R6 manifest")
    source = resolve_external_payload_path(root, manifest["payload"]["path"])
    if hashlib.sha256(source.read_bytes()).hexdigest() != EXPECTED_PAYLOAD_SHA256:
        raise ValueError("canonical payload bytes do not match the manifested identity")
    census_path = root / "R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json"
    census = json.loads(census_path.read_text(encoding="utf-8"))
    boundary_path = root / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json"
    boundary_state = json.loads(boundary_path.read_text(encoding="utf-8"))
    with np.load(source, allow_pickle=False) as archive:
        arrays = {name: archive[name].copy() for name in archive.files}
    return build_canonical_mesh(arrays, census, boundary_state,
                                manifest.get("adjacency_groups"))


def project_cell_field_to_nodes(
    mesh: CanonicalMesh,
    face_row: np.ndarray,
    face_col: np.ndarray,
    cell_values: np.ndarray,
    *,
    unknown_mask: np.ndarray | None = None,
    categorical: bool = False,
    cell_uncertainty: np.ndarray | None = None,
) -> dict[str, Any]:
    """Attach canonical cell support to existing FEG vertices deterministically.

    Continuous values use one source cell per node: the lexicographically first
    incident canonical (row, column) cell. This is a numerical support mapping,
    not interpolation or an increase in scientific resolution. Categorical
    values are emitted only where every incident source cell is known and all
    categories agree; mixed boundary support remains an explicit ``None``.
    """
    rows = np.asarray(face_row, dtype=np.int64)
    cols = np.asarray(face_col, dtype=np.int64)
    values = np.asarray(cell_values)
    if rows.ndim != 1 or cols.shape != rows.shape:
        raise ValueError("face row/column inventories must be equal-length vectors")
    if values.ndim != 2:
        raise ValueError("cell field must be a two-dimensional row/column array")
    if not categorical and not np.issubdtype(values.dtype, np.number):
        raise ValueError("continuous cell fields must be numeric")
    if len(set(zip(rows.tolist(), cols.tolist()))) != len(rows):
        raise ValueError("canonical face row/column support contains duplicates")
    if np.any(rows < 0) or np.any(cols < 0) or np.any(rows >= values.shape[0]) or np.any(cols >= values.shape[1]):
        raise ValueError("face inventory indexes outside the supplied cell field")
    if len(rows) != len(mesh.triangle_parent_face) or np.any(mesh.triangle_parent_face < 0) or np.any(mesh.triangle_parent_face >= len(rows)):
        raise ValueError("mesh triangle-to-parent-face lineage is incomplete")
    if unknown_mask is not None:
        unknown = np.asarray(unknown_mask, dtype=bool)
        if unknown.shape != values.shape:
            raise ValueError("unknown mask shape differs from cell field")
    else:
        unknown = np.zeros(values.shape, dtype=bool)
    if np.issubdtype(values.dtype, np.floating):
        unknown = unknown | ~np.isfinite(values)
    if cell_uncertainty is not None:
        uncertainties = np.asarray(cell_uncertainty, dtype=np.float64)
        if uncertainties.shape != values.shape:
            raise ValueError("uncertainty shape differs from cell field")
        if np.any(np.isfinite(uncertainties) & (uncertainties < 0)):
            raise ValueError("cell uncertainty must be nonnegative")
        if np.any(np.isfinite(uncertainties) & ~unknown & (uncertainties < 0)):
            raise ValueError("known cell values require a valid nonnegative uncertainty")
        if np.any(~unknown & ~np.isfinite(uncertainties)):
            raise ValueError("known cell values cannot have unknown uncertainty")
    else:
        uncertainties = None

    canonical_source = {
        "shape": list(values.shape), "dtype": str(values.dtype),
        "values": [[None if unknown[r, c] else
                    (values[r, c].item() if hasattr(values[r, c], "item") else values[r, c])
                    for c in range(values.shape[1])] for r in range(values.shape[0])],
        "unknown_mask": unknown.tolist(),
        "uncertainty": None if uncertainties is None else [
            [None if unknown[r, c] or not np.isfinite(uncertainties[r, c]) else float(uncertainties[r, c])
             for c in range(values.shape[1])] for r in range(values.shape[0])],
    }
    source_sha256 = hashlib.sha256(json.dumps(
        canonical_source, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str
    ).encode("utf-8")).hexdigest()

    incident: list[set[int]] = [set() for _ in range(len(mesh.vertices_lat_lon))]
    for triangle, parent_face in zip(mesh.triangles, mesh.triangle_parent_face):
        for node_id in triangle:
            incident[int(node_id) - 1].add(int(parent_face))
    if any(not support for support in incident):
        raise ValueError("a mesh vertex has no canonical-cell source support")

    projected: list[int | float | None] = []
    lineage: list[dict[str, Any]] = []
    for node_id, support in enumerate(incident, 1):
        ordered = sorted(support, key=lambda face: (int(rows[face]), int(cols[face])))
        cells = [(int(rows[face]), int(cols[face])) for face in ordered]
        known_categories = sorted({str(values[r, c].item() if hasattr(values[r, c], "item") else values[r, c])
                                   for r, c in cells if not unknown[r, c]})
        has_unknown = any(unknown[r, c] for r, c in cells)
        if categorical:
            distinct = {values[r, c].item() if hasattr(values[r, c], "item") else values[r, c]
                        for r, c in cells if not unknown[r, c]}
            output = next(iter(distinct)) if not has_unknown and len(distinct) == 1 else None
            selected = None
            uncertainty = None
        else:
            selected = cells[0]
            output = None if has_unknown else (
                values[selected].item() if hasattr(values[selected], "item") else values[selected]
            )
            uncertainty = (None if uncertainties is None or has_unknown
                           else float(uncertainties[selected]))
        projected.append(output)
        lineage.append({
            "node_id": node_id,
            "incident_source_cells_row_col": [list(cell) for cell in cells],
            "selected_source_cell_row_col": list(selected) if selected is not None else None,
            "rule": "CATEGORICAL_UNANIMOUS_INCIDENT_CELLS" if categorical else "LEXICOGRAPHIC_FIRST_INCIDENT_CELL",
            "weight": 1.0 if selected is not None else None,
            "category_support": known_categories if categorical else None,
            "unknown_incident_source_count": sum(unknown[r, c] for r, c in cells),
            "source_uncertainty": uncertainty,
            "extrapolation_state": "NONE; source support is incident canonical cell set",
            "error_estimate": "NOT_ESTIMATED; retains source-cell support, no resolution claim",
            "status": "UNKNOWN_OR_MIXED_SUPPORT" if output is None else "NUMERICAL_DERIVED_SUPPORT",
        })
    body = {
        "schema": "ARCANA_CELL_TO_FEG_NODE_SUPPORT_PROJECTION_V1",
        "classification": "NUMERICAL_DERIVED_SUPPORT",
        "categorical": categorical,
        "source_grid_shape": list(values.shape),
        "source_array_sha256": source_sha256,
        "source_known_cell_count": int(np.count_nonzero(~unknown)),
        "source_unknown_cell_count": int(np.count_nonzero(unknown)),
        "node_count": len(projected),
        "known_node_count": sum(value is not None for value in projected),
        "unknown_node_count": sum(value is None for value in projected),
        "coverage": {"known_feg_nodes": sum(value is not None for value in projected),
                     "unknown_feg_nodes": sum(value is None for value in projected),
                     "total_feg_nodes": len(projected)},
        "projected_values": projected,
        "lineage": lineage,
    }
    body["projection_sha256"] = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str
    ).encode("utf-8")).hexdigest()
    body["values_by_node_id"] = {str(i): value for i, value in enumerate(projected, 1)}
    return body
