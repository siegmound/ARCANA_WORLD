"""Read-only adapter from the governed R6 t0 partition to pyGPlates geometry."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from arcana_worldsim.r6.repository_context import resolve_external_payload_path

from .contracts import validate_mapping_inventory

PARTITION_MANIFEST = "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"
JUNCTION_CENSUS = "R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json"


@dataclass(frozen=True)
class MappingInput:
    manifest: dict[str, Any]
    arrays: dict[str, np.ndarray]
    junction_census: dict[str, Any]
    payload_path: Path
    inventory: dict[str, int]


def load_mapping_input(repository_root: str | Path) -> MappingInput:
    """Load only the manifested external NPZ and the existing junction census."""
    root = Path(repository_root).resolve()
    manifest = json.loads((root / PARTITION_MANIFEST).read_text(encoding="utf-8"))
    census = json.loads((root / JUNCTION_CENSUS).read_text(encoding="utf-8"))
    payload_path = resolve_external_payload_path(root, manifest["payload"]["path"])
    if not payload_path.is_file():
        raise FileNotFoundError(f"canonical t0 vector partition payload not found: {payload_path}")
    payload_hash = hashlib.sha256(payload_path.read_bytes()).hexdigest()
    if payload_path.stat().st_size != manifest["payload"]["bytes"]:
        raise ValueError("canonical vector partition payload size differs from its manifest")
    if payload_hash != manifest["payload"]["sha256"]:
        raise ValueError("canonical vector partition payload hash differs from its manifest")

    with np.load(payload_path, allow_pickle=False) as archive:
        arrays = {key: archive[key].copy() for key in archive.files}
    for array in arrays.values():
        array.flags.writeable = False
    inventory = validate_mapping_inventory(manifest, arrays, census)
    if census.get("parent_payload_sha256") not in (None, manifest["payload"]["sha256"]):
        raise ValueError("junction census and vector partition payload identities differ")
    return MappingInput(manifest, arrays, census, payload_path, inventory)


def _feature(pygplates: Any, geometry: Any, name: str, plate_id: int | None = None) -> Any:
    feature = pygplates.Feature(pygplates.FeatureType.gpml_unclassified_feature)
    feature.set_geometry(geometry)
    feature.set_name(name)
    if plate_id is not None:
        feature.set_reconstruction_plate_id(plate_id)
    return feature


def _boundary_endpoints(row: int, col: int, axis: int) -> list[tuple[float, float]]:
    """Return source grid vertices (lat, lon); no boundary motion is assigned."""
    if axis == 0:
        south = -90.0 + row
        longitude = -180.0 + ((col + 1) % 360)
        return [(south, longitude), (south + 1.0, longitude)]
    if axis == 1:
        latitude = -90.0 + row + 1.0
        west = -180.0 + col
        east = -180.0 + ((col + 1) % 360)
        return [(latitude, west), (latitude, east)]
    raise ValueError(f"unknown canonical grid-edge axis: {axis}")


def _junction_lat_lon(vertex_id: str) -> tuple[float, float]:
    if vertex_id == "SOUTH_POLE":
        return -90.0, 0.0
    if vertex_id == "NORTH_POLE":
        return 90.0, 0.0
    prefix, row_text, col_text = vertex_id.split(":")
    if prefix != "GRID_VERTEX":
        raise ValueError(f"unsupported canonical junction vertex ID: {vertex_id}")
    return -90.0 + int(row_text), -180.0 + (int(col_text) % 360)


def construct_geometry_candidates(data: MappingInput, pygplates: Any) -> dict[str, Any]:
    """Construct t0 cell, boundary-support and junction-point geometry candidates.

    This does not resolve topologies, prescribe rotations or classify boundary
    processes. Cell face curves are passed through pyGPlates' spherical polygon
    representation as-is; exact curve-semantic equivalence is not asserted.
    """
    arrays = data.arrays
    rigid_cells: dict[int, list[Any]] = {}
    plate_values = arrays["face_plate_id"]
    face_vertices = arrays["face_vertex_latlon_deg"]
    for plate_id in sorted({int(value) for value in plate_values}):
        rigid_cells[plate_id] = []
    for plate_raw, vertices in zip(plate_values, face_vertices):
        plate_id = int(plate_raw)
        geometry = pygplates.PolygonOnSphere([tuple(map(float, point)) for point in vertices])
        rigid_cells[plate_id].append(_feature(
            pygplates, geometry,
            f"R6_T0_CELL_PLATE_{plate_id}",
            plate_id,
        ))

    boundary_features = []
    for index, (row, col, axis) in enumerate(zip(
        arrays["boundary_edge_row"], arrays["boundary_edge_col"], arrays["boundary_edge_axis"]
    )):
        geometry = pygplates.PolylineOnSphere(_boundary_endpoints(int(row), int(col), int(axis)))
        boundary_features.append(_feature(pygplates, geometry, f"R6_T0_BOUNDARY_SUPPORT_{index:04d}"))

    junction_features = []
    for record in data.junction_census["junctions"]:
        point = pygplates.PointOnSphere(*_junction_lat_lon(record["vertex_id"]))
        junction_features.append(_feature(
            pygplates,
            point,
            f"R6_T0_JUNCTION_{record['junction_id']}",
        ))

    return {
        "rigid_cell_features_by_plate": rigid_cells,
        "boundary_support_features": boundary_features,
        "junction_point_features": junction_features,
    }
