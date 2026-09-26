"""Conforming local P1 basis for a three-plate spherical junction patch.

This is a numerical continuum reference-coordinate convention, not a
geological junction law. The patch is a tangent-plane triangle mapped to the
sphere by the exponential map. Its three boundary traces are nodal samples of
the existing two-plate smoothstep corridor basis; a shared fan mesh supplies
a C0 P1 extension into the patch. Between-node trace error is computed exactly
and decreases with edge subdivision count.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np

from .boundary_geometry import unit_xyz


def _smoothstep(t: float) -> float:
    t = min(1.0, max(0.0, float(t)))
    return t * t * (3.0 - 2.0 * t)


def _piecewise_linear_smoothstep_error(subdivisions: int) -> float:
    """Exact maximum nodal-P1 trace error, found from cubic error extrema."""
    maximum = 0.0
    for k in range(subdivisions):
        a, b = k / subdivisions, (k + 1) / subdivisions
        fa, fb = _smoothstep(a), _smoothstep(b)
        slope = (fb - fa) / (b - a)
        discriminant = 1.0 - 2.0 * slope / 3.0
        if discriminant < 0:
            continue
        for t in ((1.0 - math.sqrt(discriminant)) / 2.0,
                  (1.0 + math.sqrt(discriminant)) / 2.0):
            if a < t < b:
                linear = fa + slope * (t - a)
                maximum = max(maximum, abs(_smoothstep(t) - linear))
    return maximum


@dataclass(frozen=True, slots=True)
class JunctionMeshTriangle:
    triangle_id: str
    xy_m: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    nodal_weights: tuple[tuple[float, float, float], tuple[float, float, float],
                         tuple[float, float, float]]


class ThreePlateJunctionBasis:
    """One deterministic triangular P1 patch with three compatible traces.

    ``plate_ids`` are in cyclic order around the local patch. ``azimuths_deg``
    set the three outer vertices in the local east/north tangent plane and may
    be asymmetric. The patch circumradius is supplied from the already
    governed corridor footprint (normally W_model/2); no second scale is
    introduced here.
    """

    def __init__(self, junction_id: str, center_lat_deg: float, center_lon_deg: float,
                 plate_ids: Iterable[int], footprint_radius_m: float,
                 subdivisions_per_side: int = 16,
                 azimuths_deg: tuple[float, float, float] = (90.0, 210.0, 330.0),
                 sphere_radius_m: float = 6_371_000.0):
        self.junction_id = str(junction_id)
        self.center_lat_deg = float(center_lat_deg)
        self.center_lon_deg = float(center_lon_deg)
        self.plate_ids = tuple(int(p) for p in plate_ids)
        self.radius_m = float(footprint_radius_m)
        self.sphere_radius_m = float(sphere_radius_m)
        self.subdivisions = int(subdivisions_per_side)
        if not self.junction_id or len(self.plate_ids) != 3 or len(set(self.plate_ids)) != 3:
            raise ValueError("a stable junction ID and three distinct plate IDs are required")
        if not math.isfinite(self.radius_m) or self.radius_m <= 0:
            raise ValueError("positive governed footprint radius required")
        if self.subdivisions < 2 or self.subdivisions > 4096:
            raise ValueError("subdivisions_per_side must be in [2, 4096]")
        if len(azimuths_deg) != 3 or any(not math.isfinite(float(a)) for a in azimuths_deg):
            raise ValueError("exactly three finite tangent-plane azimuths required")
        if len({round(float(a) % 360.0, 10) for a in azimuths_deg}) != 3:
            raise ValueError("junction ray azimuths must be distinct")
        if not math.isfinite(self.sphere_radius_m) or self.sphere_radius_m <= self.radius_m:
            raise ValueError("sphere radius must exceed the local patch radius")
        unit_xyz(self.center_lat_deg, self.center_lon_deg)
        self.center = unit_xyz(self.center_lat_deg, self.center_lon_deg)
        lat = math.radians(self.center_lat_deg)
        lon = math.radians(self.center_lon_deg)
        self.east = np.array((-math.sin(lon), math.cos(lon), 0.0))
        self.north = np.array((-math.sin(lat) * math.cos(lon),
                               -math.sin(lat) * math.sin(lon), math.cos(lat)))
        self.vertices = tuple((self.radius_m * math.cos(math.radians(a)),
                               self.radius_m * math.sin(math.radians(a))) for a in azimuths_deg)
        self.max_smoothstep_trace_error = _piecewise_linear_smoothstep_error(self.subdivisions)
        for i in range(3):
            a = np.asarray(self.vertices[i])
            b = np.asarray(self.vertices[(i + 1) % 3])
            determinant = float(a[0] * b[1] - a[1] * b[0])
            if abs(determinant) <= self.radius_m * self.radius_m * 1e-10:
                raise ValueError("adjacent junction rays create a degenerate fan element")
        self.triangles = self._build_mesh()

    def _edge_value(self, edge: int, t: float) -> tuple[float, float, float]:
        weights = [0.0, 0.0, 0.0]
        a, b = edge, (edge + 1) % 3
        blend = _smoothstep(t)
        weights[a], weights[b] = 1.0 - blend, blend
        return tuple(weights)

    def _build_mesh(self) -> tuple[JunctionMeshTriangle, ...]:
        c = (0.0, 0.0)
        center_w = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
        result = []
        n = self.subdivisions
        for edge in range(3):
            a = np.asarray(self.vertices[edge], dtype=float)
            b = np.asarray(self.vertices[(edge + 1) % 3], dtype=float)
            for k in range(n):
                t0, t1 = k / n, (k + 1) / n
                p0 = tuple((a * (1 - t0) + b * t0).tolist())
                p1 = tuple((a * (1 - t1) + b * t1).tolist())
                result.append(JunctionMeshTriangle(
                    f"{self.junction_id}:E{edge}:T{k:04d}",
                    (c, p0, p1),
                    (center_w, self._edge_value(edge, t0), self._edge_value(edge, t1))))
        return tuple(result)

    def _log_map_xy(self, lat_deg: float, lon_deg: float) -> tuple[float, float]:
        p = unit_xyz(lat_deg, lon_deg)
        theta = math.atan2(float(np.linalg.norm(np.cross(self.center, p))),
                           float(np.clip(np.dot(self.center, p), -1.0, 1.0)))
        if theta <= 1e-14:
            return 0.0, 0.0
        tangent = p - float(np.dot(self.center, p)) * self.center
        norm = float(np.linalg.norm(tangent))
        if norm <= 1e-14:
            raise ValueError("antipodal query is outside the local junction chart")
        tangent *= theta * self.sphere_radius_m / norm
        return float(np.dot(tangent, self.east)), float(np.dot(tangent, self.north))

    @staticmethod
    def _barycentric(p: np.ndarray, tri: np.ndarray) -> tuple[float, float, float] | None:
        a, b, c = tri
        matrix = np.column_stack((a - c, b - c))
        determinant = float(np.linalg.det(matrix))
        if abs(determinant) <= 1e-16:
            return None
        uv = np.linalg.solve(matrix, p - c)
        w = (float(uv[0]), float(uv[1]), float(1.0 - uv[0] - uv[1]))
        tol = 2e-10
        return w if min(w) >= -tol and max(w) <= 1.0 + tol else None

    def weights_xy(self, x_m: float, y_m: float) -> tuple[tuple[int, float], ...] | None:
        """Evaluate the C0, nonnegative P1 basis; return None outside the patch."""
        p = np.array((float(x_m), float(y_m)))
        if not np.all(np.isfinite(p)):
            raise ValueError("query coordinates must be finite")
        for triangle in self.triangles:
            tri = np.asarray(triangle.xy_m, dtype=float)
            bary = self._barycentric(p, tri)
            if bary is None:
                continue
            values = np.asarray(bary) @ np.asarray(triangle.nodal_weights)
            values[np.abs(values) < 1e-14] = 0.0
            values = np.maximum(values, 0.0)
            values /= float(values.sum())
            return tuple((plate, float(weight)) for plate, weight in zip(self.plate_ids, values))
        return None

    def weights_at(self, lat_deg: float, lon_deg: float) -> tuple[tuple[int, float], ...] | None:
        return self.weights_xy(*self._log_map_xy(lat_deg, lon_deg))

    def latlon_at_xy(self, x_m: float, y_m: float) -> tuple[float, float]:
        """Map local tangent coordinates to the sphere with the inverse exp map."""
        x, y = float(x_m), float(y_m)
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("tangent coordinates must be finite")
        distance = math.hypot(x, y)
        theta = distance / self.sphere_radius_m
        if theta <= 1e-14:
            return self.center_lat_deg, self.center_lon_deg
        tangent = (x * self.east + y * self.north) / distance
        point = math.cos(theta) * self.center + math.sin(theta) * tangent
        lat = math.degrees(math.asin(float(np.clip(point[2], -1.0, 1.0))))
        lon = math.degrees(math.atan2(float(point[1]), float(point[0])))
        return lat, lon

    def boundary_trace(self, edge: int, t: float) -> tuple[tuple[int, float], ...]:
        if edge not in (0, 1, 2) or not (0.0 <= t <= 1.0):
            raise ValueError("edge must be 0..2 and t must be in [0,1]")
        values = self._edge_value(edge, t)
        return tuple((plate, values[i]) for i, plate in enumerate(self.plate_ids))
