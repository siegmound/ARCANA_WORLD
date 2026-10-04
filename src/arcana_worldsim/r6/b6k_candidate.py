"""Bounded B6K candidate construction; never publishes canonical R6 state."""
from __future__ import annotations

from hashlib import sha256
import json
import math
from decimal import Decimal
from typing import Iterable, Mapping, Sequence

import numpy as np

from .finite_rotation import rotate_vector_constant_euler
from .identity import canonical_bytes, content_hash

DT_YEARS = float.fromhex("0x1.a7cd9ee14b895p+14")
SOURCE_AGE_MA = 210.0
TARGET_AGE_MA = 209.97287659484368


def target_age(source_age_ma: float, elapsed_years: float) -> float:
    if not math.isfinite(source_age_ma) or not math.isfinite(elapsed_years) or elapsed_years <= 0:
        raise ValueError("source age and positive finite elapsed time are required")
    result = float(Decimal(str(source_age_ma)) - Decimal.from_float(elapsed_years)
                   / Decimal(1_000_000))
    if not math.isfinite(result):
        raise ValueError("target age must be finite")
    return result


def unit_xyz(latitude_longitude_degrees: Sequence[float]) -> tuple[float, float, float]:
    lat, lon = map(math.radians, latitude_longitude_degrees)
    return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))


def build_plate_local_positions(*, vertices_lat_lon: np.ndarray,
                                face_node_ids: Sequence[Sequence[int]],
                                face_plate_ids: Sequence[int],
                                plate_omega: Mapping[int, Sequence[float]],
                                elapsed_years: float) -> tuple[tuple[tuple[int, int], ...], np.ndarray]:
    """Rotate every governed (node, plate) incidence independently, IDs 1-based."""
    membership: list[set[int]] = [set() for _ in range(len(vertices_lat_lon))]
    if len(face_node_ids) != len(face_plate_ids):
        raise ValueError("face support arrays differ in length")
    for nodes, plate in zip(face_node_ids, face_plate_ids):
        if int(plate) not in plate_omega:
            raise ValueError(f"no governed Euler vector for plate {plate}")
        for node_id in nodes:
            if not 1 <= int(node_id) <= len(vertices_lat_lon):
                raise ValueError("face references an invalid canonical node")
            membership[int(node_id) - 1].add(int(plate))
    pairs = tuple((node_id, plate) for node_id, plates in enumerate(membership, 1)
                  for plate in sorted(plates))
    index = {pair: i for i, pair in enumerate(pairs)}
    coordinates = np.empty((len(pairs), 3), dtype="<f8")
    for i, (node_id, plate) in enumerate(pairs):
        source = unit_xyz(vertices_lat_lon[node_id - 1])
        coordinates[i] = rotate_vector_constant_euler(source, plate_omega[plate], elapsed_years)
    if not np.isfinite(coordinates).all():
        raise ValueError("candidate contains non-finite coordinates")
    return pairs, coordinates


def deterministic_payload(pairs: Sequence[tuple[int, int]], coordinates: np.ndarray) -> bytes:
    """Stable little-endian header+arrays format with no ZIP timestamps."""
    if coordinates.shape != (len(pairs), 3) or not np.isfinite(coordinates).all():
        raise ValueError("candidate coordinate payload shape/value mismatch")
    header = canonical_bytes({"schema": "R6_B6K_PLATE_LOCAL_COORDINATES_V1",
        "row_count": len(pairs), "coordinate_columns": ["x", "y", "z"],
        "identity_columns": ["node_id_1based", "plate_id"], "units": "unit_sphere"})
    ids = np.asarray(pairs, dtype="<i8").tobytes(order="C")
    xyz = np.asarray(coordinates, dtype="<f8").tobytes(order="C")
    return b"R6B6K\0" + len(header).to_bytes(8, "little") + header + ids + xyz


def topology_identity(*, triangles: np.ndarray, triangle_plate_ids: np.ndarray,
                      boundary_descriptors: Sequence[Mapping[str, object]],
                      junction_node_ids: Sequence[tuple[str, int]]) -> str:
    body = {"triangles": np.asarray(triangles, dtype=np.int64).tolist(),
        "triangle_plate_ids": np.asarray(triangle_plate_ids, dtype=np.int64).tolist(),
        "boundary_ids": sorted(str(row["boundary_id"]) for row in boundary_descriptors),
        "junctions": sorted((str(key), int(node)) for key, node in junction_node_ids)}
    return content_hash(body)


def geometry_diagnostics(*, pairs: Sequence[tuple[int, int]], coordinates: np.ndarray,
                         vertices_lat_lon: np.ndarray, triangles: np.ndarray,
                         triangle_plate_ids: np.ndarray) -> dict[str, object]:
    pair_index = {pair: i for i, pair in enumerate(pairs)}
    source_xyz = np.asarray([unit_xyz(row) for row in vertices_lat_lon], dtype=np.float64)
    radius_drift = np.abs(np.linalg.norm(coordinates, axis=1) - 1.0)
    max_edge = 0.0
    max_area = 0.0
    orientation_failures = 0
    for tri, plate in zip(np.asarray(triangles, dtype=np.int64),
                          np.asarray(triangle_plate_ids, dtype=np.int64)):
        ids = [int(x) for x in tri]
        before = source_xyz[np.asarray(ids) - 1]
        after = np.asarray([coordinates[pair_index[(node, int(plate))]] for node in ids])
        for a, b in ((0, 1), (1, 2), (2, 0)):
            d0 = float(np.linalg.norm(before[a] - before[b]))
            d1 = float(np.linalg.norm(after[a] - after[b]))
            max_edge = max(max_edge, abs(d1 - d0))
        cross0 = np.cross(before[1] - before[0], before[2] - before[0])
        cross1 = np.cross(after[1] - after[0], after[2] - after[0])
        max_area = max(max_area, abs(float(np.linalg.norm(cross1) - np.linalg.norm(cross0))))
        if float(np.dot(cross0, cross1)) <= 0:
            orientation_failures += 1
    return {"coordinate_rows": len(pairs), "finite_coordinate_count": int(np.isfinite(coordinates).all(axis=1).sum()),
        "nan_count": int(np.isnan(coordinates).sum()), "inf_count": int(np.isinf(coordinates).sum()),
        "max_unit_radius_drift": float(radius_drift.max(initial=0.0)),
        "max_plate_local_edge_length_drift": max_edge,
        "max_plate_local_triangle_area_drift": max_area,
        "plate_local_triangle_orientation_failures": orientation_failures}


def candidate_identity(*, source_t0_identity: str, model_identity: str,
                       dt_hex: str, target_age_ma: float, topology_id: str,
                       candidate_payload_sha256: str) -> str:
    return content_hash({"schema": "R6_B6K_CANDIDATE_FIRST_STEP_PRETRANSITION_V1",
        "source_t0_identity": source_t0_identity, "model_identity": model_identity,
        "topology_process_scope": "RIFT_PROCESS_ACTIVATION_PAIR_1_3_PRETRANSITION_ENDPOINT",
        "dt_hex": dt_hex, "target_age_ma": target_age_ma, "topology_identity": topology_id,
        "transfer_policy_version": "B6G_B6I_EXPLICIT_FIELD_SPECIFIC_V1",
        "payload_sha256": candidate_payload_sha256})
