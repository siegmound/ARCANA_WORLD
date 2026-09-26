"""Spherical, query-based R6 boundary-zone reference geometry.

This module defines numerical reference regions only. It does not change plate
membership, add geological support, or advance any physical state.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Iterable

import numpy as np


_EPS = 1e-12


def unit_xyz(lat_deg: float, lon_deg: float) -> np.ndarray:
    if not (math.isfinite(lat_deg) and math.isfinite(lon_deg) and -90 <= lat_deg <= 90):
        raise ValueError("latitude/longitude must be finite and latitude within [-90, 90]")
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    c = math.cos(lat)
    return np.array((c * math.cos(lon), c * math.sin(lon), math.sin(lat)), dtype=np.float64)


def _angle(a: np.ndarray, b: np.ndarray) -> float:
    return math.atan2(float(np.linalg.norm(np.cross(a, b))), float(np.clip(np.dot(a, b), -1.0, 1.0)))


def _normalize_lon(lon: float) -> float:
    return (lon + 180.0) % 360.0 - 180.0


@dataclass(frozen=True, slots=True)
class SphericalSegment:
    """A finite spherical arc: minor great-circle or constant-latitude arc.

    For SMALL_CIRCLE, ``sweep_deg`` is directed east-positive and must describe
    the actual source arc (not the shortest wrapped delta by assumption).
    """

    start_lat_deg: float
    start_lon_deg: float
    end_lat_deg: float
    end_lon_deg: float
    kind: str = "GREAT_CIRCLE"
    sweep_deg: float | None = None

    def __post_init__(self) -> None:
        a = unit_xyz(self.start_lat_deg, self.start_lon_deg)
        b = unit_xyz(self.end_lat_deg, self.end_lon_deg)
        arc_angle = _angle(a, b)
        if arc_angle <= _EPS:
            raise ValueError("zero-length spherical segment")
        if self.kind == "GREAT_CIRCLE" and arc_angle >= math.pi - 1e-10:
            raise ValueError("antipodal endpoints do not define a unique minor great-circle arc")
        if self.kind not in {"GREAT_CIRCLE", "SMALL_CIRCLE"}:
            raise ValueError("kind must be GREAT_CIRCLE or SMALL_CIRCLE")
        if self.kind == "SMALL_CIRCLE":
            if abs(self.start_lat_deg - self.end_lat_deg) > 1e-10:
                raise ValueError("small-circle endpoints must share latitude")
            if self.sweep_deg is None or not math.isfinite(self.sweep_deg) or abs(self.sweep_deg) > 180:
                raise ValueError("small-circle requires finite directed sweep within 180 degrees")
            if abs(self.sweep_deg) <= _EPS:
                raise ValueError("small-circle sweep must be nonzero")
            expected_end = _normalize_lon(self.start_lon_deg + self.sweep_deg)
            if abs(_normalize_lon(expected_end - self.end_lon_deg)) > 1e-9:
                raise ValueError("small-circle sweep does not terminate at declared endpoint")

    def distance_m(self, lat_deg: float, lon_deg: float, radius_m: float = 6_371_000.0) -> float:
        if not (math.isfinite(radius_m) and radius_m > 0):
            raise ValueError("radius_m must be positive and finite")
        p = unit_xyz(lat_deg, lon_deg)
        a = unit_xyz(self.start_lat_deg, self.start_lon_deg)
        b = unit_xyz(self.end_lat_deg, self.end_lon_deg)
        if self.kind == "SMALL_CIRCLE":
            delta = float(self.sweep_deg)
            rel = (lon_deg - self.start_lon_deg) % 360.0 if delta >= 0 else -((self.start_lon_deg - lon_deg) % 360.0)
            inside = (-_EPS <= rel <= delta + _EPS) if delta >= 0 else (delta - _EPS <= rel <= _EPS)
            candidates = [lon_deg] if inside else [self.start_lon_deg, self.end_lon_deg]
            phi0 = math.radians(self.start_lat_deg)
            phi = math.radians(lat_deg)
            best = math.inf
            for candidate_lon in candidates:
                q = unit_xyz(self.start_lat_deg, candidate_lon)
                best = min(best, _angle(p, q))
            return radius_m * best

        normal = np.cross(a, b)
        normal_norm = float(np.linalg.norm(normal))
        if normal_norm <= _EPS:
            return radius_m * min(_angle(p, a), _angle(p, b))
        normal /= normal_norm
        projected = p - float(np.dot(p, normal)) * normal
        projected_norm = float(np.linalg.norm(projected))
        candidates = [a, b]
        if projected_norm > _EPS:
            q = projected / projected_norm
            arc = _angle(a, b)
            for candidate in (q, -q):
                if abs((_angle(a, candidate) + _angle(candidate, b)) - arc) <= 1e-10:
                    candidates.append(candidate)
        return radius_m * min(_angle(p, q) for q in candidates)


@dataclass(frozen=True, slots=True)
class BoundaryFeature:
    """A stable connected network component for one ordered plate pair."""
    boundary_id: str
    plate_a: int
    plate_b: int
    segments: tuple[SphericalSegment, ...]

    def __post_init__(self) -> None:
        if not self.boundary_id or self.plate_a >= self.plate_b or not self.segments:
            raise ValueError("feature needs stable ID, ordered distinct plates and segments")

    def distance_m(self, lat_deg: float, lon_deg: float, radius_m: float) -> float:
        return min(s.distance_m(lat_deg, lon_deg, radius_m) for s in self.segments)


def two_plate_corridor_weights(feature: BoundaryFeature, lat_deg: float, lon_deg: float,
                               width_m: float, plate_owner: int,
                               radius_m: float = 6_371_000.0) -> tuple[tuple[int, float], ...]:
    """Canonical existing two-plate smoothstep operator for a corridor point."""
    if not math.isfinite(width_m) or width_m <= 0:
        raise ValueError("positive finite corridor width required")
    if plate_owner not in (feature.plate_a, feature.plate_b):
        raise ValueError("corridor point's inherited plate owner is not incident")
    distance = feature.distance_m(lat_deg, lon_deg, radius_m)
    signed = -distance if plate_owner == feature.plate_a else distance
    xi = float(np.clip(signed / (width_m / 2.0), -1.0, 1.0))
    t = (xi + 1.0) * 0.5
    blend = t * t * (3.0 - 2.0 * t)
    return ((feature.plate_a, 1.0 - blend), (feature.plate_b, blend))


@dataclass(frozen=True, slots=True)
class Junction:
    junction_id: str
    lat_deg: float
    lon_deg: float
    incident_boundary_ids: tuple[str, ...]
    incident_plate_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class RegionQuery:
    category: str
    plate_ids: tuple[int, ...]
    boundary_ids: tuple[str, ...] = ()
    junction_id: str | None = None
    distance_m: float | None = None
    cross_zone_coordinate: float | None = None
    plate_weights: tuple[tuple[int, float], ...] | None = None
    reason: str | None = None
    support: str = "MODEL_DERIVED_FROM_COARSE_CANONICAL_T0_SUPPORT"


class SphericalBoundaryArrangement:
    """Implicit, deterministic global arrangement queried on the sphere.

    Region membership is a single-valued function, not separately buffered
    polygons. Ambiguous non-junction corridor intersections fail closed.
    ``plate_at`` is the immutable parent-domain resolver.
    """

    def __init__(self, features: Iterable[BoundaryFeature], junctions: Iterable[Junction],
                 width_m: float, plate_at: Callable[[float, float], int],
                 radius_m: float = 6_371_000.0):
        self.features = tuple(sorted(features, key=lambda f: f.boundary_id))
        self.junctions = tuple(sorted(junctions, key=lambda j: j.junction_id))
        self.width_m = float(width_m)
        self.half_width_m = self.width_m / 2.0
        self.radius_m = float(radius_m)
        self.plate_at = plate_at
        if not self.features or self.width_m <= 0 or not math.isfinite(self.width_m):
            raise ValueError("nonempty network and positive finite model width required")
        if self.radius_m <= 0 or not math.isfinite(self.radius_m) or not callable(self.plate_at):
            raise ValueError("positive finite sphere radius and parent-domain resolver required")
        if len({f.boundary_id for f in self.features}) != len(self.features):
            raise ValueError("boundary IDs must be unique")
        if len({j.junction_id for j in self.junctions}) != len(self.junctions):
            raise ValueError("junction IDs must be unique")
        self.feature_by_id = {f.boundary_id: f for f in self.features}
        for j in self.junctions:
            if len(j.incident_boundary_ids) != 3 or len(j.incident_plate_ids) != 3:
                raise ValueError("only degree-3 junctions are supported by this operator")
            if any(bid not in self.feature_by_id for bid in j.incident_boundary_ids):
                raise ValueError("junction references unknown boundary ID")

    def nearest_boundary_features(self, lat_deg: float, lon_deg: float, limit: int = 4) -> tuple[tuple[str, float], ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        values = sorted((f.boundary_id, f.distance_m(lat_deg, lon_deg, self.radius_m)) for f in self.features)
        return tuple(values[:limit])

    def classify(self, lat_deg: float, lon_deg: float) -> RegionQuery:
        nearest_j = sorted((j for j in self.junctions), key=lambda j: (
            _angle(unit_xyz(lat_deg, lon_deg), unit_xyz(j.lat_deg, j.lon_deg)), j.junction_id))
        if nearest_j:
            j = nearest_j[0]
            jd = self.radius_m * _angle(unit_xyz(lat_deg, lon_deg), unit_xyz(j.lat_deg, j.lon_deg))
            if jd <= self.half_width_m:
                if len(nearest_j) > 1 and self.radius_m * _angle(
                    unit_xyz(j.lat_deg, j.lon_deg), unit_xyz(nearest_j[1].lat_deg, nearest_j[1].lon_deg)
                ) < 2 * self.half_width_m:
                    return RegionQuery("INFEASIBLE", (), junction_id=j.junction_id, distance_m=jd,
                                       reason="junction patches overlap at requested global width")
                incident = set(j.incident_boundary_ids)
                nearby = {bid for bid, d in self.nearest_boundary_features(
                    lat_deg, lon_deg, limit=len(self.features)) if d <= self.half_width_m}
                if nearby - incident:
                    return RegionQuery("INFEASIBLE", (), tuple(sorted(nearby)), j.junction_id, jd,
                                       reason="non-incident boundary intersects junction patch support")
                return RegionQuery("JUNCTION_PATCH", tuple(sorted(j.incident_plate_ids)),
                                   tuple(sorted(j.incident_boundary_ids)), j.junction_id, jd)

        distances = self.nearest_boundary_features(lat_deg, lon_deg, limit=len(self.features))
        active = [(bid, d) for bid, d in distances if d <= self.half_width_m]
        if active:
            nearest_id, d = active[0]
            f = self.feature_by_id[nearest_id]
            # A second distinct, non-junction feature inside the footprint is
            # not silently clipped or merged.
            competing = [(bid, dd) for bid, dd in active[1:]]
            if competing:
                return RegionQuery("INFEASIBLE", (), tuple([nearest_id] + [x[0] for x in competing]),
                                   distance_m=d, reason="overlapping non-junction boundary footprints")
            plate = int(self.plate_at(lat_deg, lon_deg))
            if plate not in (f.plate_a, f.plate_b):
                return RegionQuery("INFEASIBLE", (), (nearest_id,), distance_m=d,
                                   reason="parent plate support does not match nearest boundary pair")
            weights = two_plate_corridor_weights(f, lat_deg, lon_deg,
                                                  self.width_m, plate, self.radius_m)
            signed = -d if plate == f.plate_a else d
            xi = float(np.clip(signed / self.half_width_m, -1.0, 1.0))
            return RegionQuery("BOUNDARY_ZONE", (f.plate_a, f.plate_b), (nearest_id,),
                               distance_m=d, cross_zone_coordinate=xi, plate_weights=weights)
        return RegionQuery("RIGID_CORE", (int(self.plate_at(lat_deg, lon_deg)),))
