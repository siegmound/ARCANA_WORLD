"""Explicit rigid coordinate frame used only by serialized ShellSet FEG support."""
from __future__ import annotations

import math

import numpy as np

RUNTIME_FRAME_ID = "ARCANA_SHELLSET_RUNTIME_RX_PLUS_0P5_DEG_V1"
RUNTIME_ROTATION_DEGREES = 0.5


def rotation_matrices() -> tuple[np.ndarray, np.ndarray]:
    """Return the proper +X rotation and its exact transpose inverse."""
    angle = math.radians(RUNTIME_ROTATION_DEGREES)
    cosine, sine = math.cos(angle), math.sin(angle)
    forward = np.asarray(((1.0, 0.0, 0.0),
                          (0.0, cosine, -sine),
                          (0.0, sine, cosine)), dtype=np.float64)
    return forward, forward.T.copy()


def _unit_vectors(lat_lon: np.ndarray) -> np.ndarray:
    coordinates = np.asarray(lat_lon, dtype=np.float64)
    if coordinates.ndim != 2 or coordinates.shape[1] != 2:
        raise ValueError("coordinates must have shape (node_count, 2) as latitude/longitude")
    lat = np.radians(coordinates[:, 0])
    lon = np.radians(coordinates[:, 1])
    return np.column_stack((np.cos(lat) * np.cos(lon),
                            np.cos(lat) * np.sin(lon), np.sin(lat)))


def _lat_lon(vectors: np.ndarray) -> np.ndarray:
    lat = np.degrees(np.arcsin(np.clip(vectors[:, 2], -1.0, 1.0)))
    lon = np.degrees(np.arctan2(vectors[:, 1], vectors[:, 0]))
    lon = (lon + 180.0) % 360.0 - 180.0
    return np.column_stack((lat, lon))


def runtime_coordinates_lat_lon(canonical_lat_lon: np.ndarray) -> np.ndarray:
    """Transform coordinates without changing or mutating canonical geometry."""
    vectors = _unit_vectors(canonical_lat_lon)
    forward, _inverse = rotation_matrices()
    return _lat_lon(vectors @ forward.T)


def _triangle_area(vectors: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    tri = np.asarray(triangles, dtype=np.int64) - 1
    a, b, c = vectors[tri[:, 0]], vectors[tri[:, 1]], vectors[tri[:, 2]]
    numerator = np.abs(np.einsum("ij,ij->i", a, np.cross(b, c)))
    denominator = (1.0 + np.einsum("ij,ij->i", a, b)
                   + np.einsum("ij,ij->i", b, c)
                   + np.einsum("ij,ij->i", c, a))
    return 2.0 * np.arctan2(numerator, denominator)


def prove_rigid_runtime_frame(canonical_lat_lon: np.ndarray,
                              runtime_lat_lon: np.ndarray,
                              triangles: np.ndarray) -> dict[str, float | bool | int | str]:
    """Numerically verify matrix, unit-vector, mesh-edge, area, and inverse invariants."""
    canonical = np.asarray(canonical_lat_lon, dtype=np.float64)
    runtime = np.asarray(runtime_lat_lon, dtype=np.float64)
    tri = np.asarray(triangles, dtype=np.int64)
    if canonical.shape != runtime.shape or canonical.ndim != 2 or canonical.shape[1] != 2:
        raise ValueError("runtime frame coordinate inventory differs from canonical mesh")
    forward, inverse = rotation_matrices()
    identity = np.eye(3, dtype=np.float64)
    orthonormal_error = float(np.max(np.abs(forward.T @ forward - identity)))
    determinant = float(np.linalg.det(forward))
    source_vectors = _unit_vectors(canonical)
    runtime_vectors = _unit_vectors(runtime)
    expected_vectors = source_vectors @ forward.T
    unit_error = float(np.max(np.abs(np.linalg.norm(runtime_vectors, axis=1) - 1.0)))
    transform_error = float(np.max(np.abs(runtime_vectors - expected_vectors)))
    restored = runtime_vectors @ inverse.T
    inverse_error = float(np.max(np.abs(restored - source_vectors)))

    edges = np.concatenate((tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]), axis=0)
    edges = np.unique(np.sort(edges, axis=1), axis=0) - 1
    source_edge_a, source_edge_b = source_vectors[edges[:, 0]], source_vectors[edges[:, 1]]
    runtime_edge_a, runtime_edge_b = runtime_vectors[edges[:, 0]], runtime_vectors[edges[:, 1]]
    source_edge_angles = np.arctan2(
        np.linalg.norm(np.cross(source_edge_a, source_edge_b), axis=1),
        np.einsum("ij,ij->i", source_edge_a, source_edge_b))
    runtime_edge_angles = np.arctan2(
        np.linalg.norm(np.cross(runtime_edge_a, runtime_edge_b), axis=1),
        np.einsum("ij,ij->i", runtime_edge_a, runtime_edge_b))
    edge_angular_error = float(np.max(np.abs(source_edge_angles - runtime_edge_angles)))
    source_areas = _triangle_area(source_vectors, tri)
    runtime_areas = _triangle_area(runtime_vectors, tri)
    area_error = float(np.max(np.abs(source_areas - runtime_areas)))
    if not np.all(np.isfinite(runtime)) or not np.all(np.isfinite(runtime_vectors)):
        raise ValueError("runtime coordinates contain NaN or infinity")
    if np.any(runtime_areas <= 0.0):
        raise ValueError("runtime coordinate transform introduced a zero-area triangle")
    maximum_latitude = float(np.max(np.abs(runtime[:, 0])))
    checks = (orthonormal_error <= 2e-15 and abs(determinant - 1.0) <= 2e-15
              and unit_error <= 2e-15 and transform_error <= 2e-14
              and inverse_error <= 2e-14 and edge_angular_error <= 2e-12
              and area_error <= 2e-12 and maximum_latitude < 89.99)
    if not checks:
        raise ValueError("runtime coordinate frame failed rigid geometry invariants")
    return {
        "frame_id": RUNTIME_FRAME_ID,
        "orthonormal": True,
        "determinant": determinant,
        "max_orthonormal_error": orthonormal_error,
        "max_unit_vector_error": unit_error,
        "max_transform_error": transform_error,
        "max_inverse_roundtrip_error": inverse_error,
        "unique_mesh_edge_count": int(len(edges)),
        "max_edge_angular_difference_rad": edge_angular_error,
        "triangle_count": int(len(tri)),
        "max_spherical_triangle_area_difference_sr": area_error,
        "minimum_runtime_spherical_triangle_area_sr": float(np.min(runtime_areas)),
        "maximum_absolute_runtime_latitude_deg": maximum_latitude,
        "no_nan_inf": True,
        "zero_area_triangles": int(np.count_nonzero(runtime_areas <= 0.0)),
        "all_checks_pass": True,
    }
