"""Deterministic nested spherical triangulation for numerical validation.

The icosphere here is a numerical integration mesh, not a replacement for the
canonical R6 parent partition and not a geological support upgrade.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True, slots=True)
class SphericalReferenceMesh:
    level: int
    node_ids: tuple[str, ...]
    xyz: tuple[tuple[float, float, float], ...]
    face_ids: tuple[str, ...]
    faces: tuple[tuple[int, int, int], ...]
    radius_m: float

    @property
    def face_count(self) -> int:
        return len(self.faces)

    def face_area_m2(self, face: tuple[int, int, int]) -> float:
        a, b, c = (np.asarray(self.xyz[i], dtype=float) for i in face)
        determinant = abs(float(np.dot(a, np.cross(b, c))))
        denominator = 1.0 + float(np.dot(a, b) + np.dot(b, c) + np.dot(c, a))
        excess = 2.0 * math.atan2(determinant, denominator)
        return excess * self.radius_m * self.radius_m

    def total_area_m2(self) -> float:
        return math.fsum(self.face_area_m2(face) for face in self.faces)


@dataclass(frozen=True, slots=True)
class OwnershipSample:
    """Single categorical owner plus a certified lower bound to its boundary."""
    owner: str | None
    clearance_lower_bound_m: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.clearance_lower_bound_m) or self.clearance_lower_bound_m < 0:
            raise ValueError("clearance lower bound must be finite and nonnegative")


def _spherical_area_xyz(a: np.ndarray, b: np.ndarray, c: np.ndarray, radius_m: float) -> float:
    det = abs(float(np.dot(a, np.cross(b, c))))
    den = 1.0 + float(np.dot(a, b) + np.dot(b, c) + np.dot(c, a))
    return 2.0 * math.atan2(det, den) * radius_m * radius_m


def integrate_spherical_ownership(mesh: SphericalReferenceMesh, sampler,
                                  max_depth: int = 4) -> dict[str, object]:
    """Deterministically integrate certified single-owner faces adaptively.

    ``sampler(xyz)`` returns :class:`OwnershipSample`. A face is assigned only
    when all vertex/centroid owners agree and the supplied certified boundary
    clearance, reduced by the face diameter, proves no transition can cross
    the face. Terminal ambiguous area remains explicit and unassigned.
    """
    if not isinstance(max_depth, int) or max_depth < 0 or max_depth > 10:
        raise ValueError("max_depth must be an integer in [0, 10]")
    areas: dict[str, list[float]] = {}
    ambiguous: list[float] = []
    resolved = 0
    terminal_mixed = 0
    def subdivide(v: tuple[np.ndarray, np.ndarray, np.ndarray], depth: int, face_id: str) -> None:
        nonlocal resolved, terminal_mixed
        a, b, c = v
        area = _spherical_area_xyz(a, b, c, mesh.radius_m)
        centroid = a + b + c
        centroid /= np.linalg.norm(centroid)
        samples = [sampler(p) for p in (a, b, c, centroid)]
        if any(not isinstance(s, OwnershipSample) for s in samples):
            raise TypeError("sampler must return OwnershipSample for every query")
        owners = {s.owner for s in samples}
        diameter = mesh.radius_m * max(
            math.atan2(float(np.linalg.norm(np.cross(x, y))),
                       float(np.clip(np.dot(x, y), -1.0, 1.0)))
            for x, y in ((a, b), (b, c), (c, a)))
        certified = (len(owners) == 1 and None not in owners and
                     min(s.clearance_lower_bound_m for s in samples) >= diameter)
        if certified:
            owner = next(iter(owners))
            areas.setdefault(owner, []).append(area)
            resolved += 1
            return
        if depth >= max_depth:
            ambiguous.append(area)
            terminal_mixed += 1
            return
        mids = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            mid = v[i] + v[j]
            mid /= np.linalg.norm(mid)
            mids.append(mid)
        ab, bc, ca = mids
        children = ((a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca))
        for index, child in enumerate(children):
            subdivide(child, depth + 1, f"{face_id}/{index}")

    for fid, face in zip(mesh.face_ids, mesh.faces):
        subdivide(tuple(np.asarray(mesh.xyz[i], dtype=float) for i in face), 0, fid)
    total = math.fsum(mesh.face_area_m2(f) for f in mesh.faces)
    owned = {owner: math.fsum(parts) for owner, parts in sorted(areas.items())}
    ambiguous_area = math.fsum(ambiguous)
    return {"owner_area_m2": owned, "assigned_area_m2": math.fsum(owned.values()),
            "unassigned_ambiguous_area_m2": ambiguous_area,
            "multiowned_area_m2": 0.0, "mesh_area_m2": total,
            "closure_error_m2": abs(math.fsum((math.fsum(owned.values()), ambiguous_area)) - total),
            "resolved_face_count": resolved, "terminal_mixed_face_count": terminal_mixed,
            "max_depth": max_depth,
            "ownership_complete": terminal_mixed == 0}


def build_icosphere(level: int, radius_m: float = 6_371_000.0) -> SphericalReferenceMesh:
    """Build nested L0/L1/... icosphere meshes with stable parent/child IDs."""
    if not isinstance(level, int) or level < 0 or level > 7:
        raise ValueError("level must be an integer in [0, 7]")
    if not math.isfinite(radius_m) or radius_m <= 0:
        raise ValueError("radius_m must be positive and finite")
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    raw = [(-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
           (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
           (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)]
    vertices = [np.asarray(v, dtype=float) / np.linalg.norm(v) for v in raw]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
             (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
             (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
             (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    face_ids = [f"I:{i:02d}" for i in range(len(faces))]
    for current in range(1, level + 1):
        midpoint_cache: dict[tuple[int, int], int] = {}

        def midpoint(i: int, j: int) -> int:
            key = tuple(sorted((i, j)))
            if key not in midpoint_cache:
                point = vertices[i] + vertices[j]
                norm = float(np.linalg.norm(point))
                if norm <= 1e-15:
                    raise ValueError("antipodal edge in spherical mesh")
                midpoint_cache[key] = len(vertices)
                vertices.append(point / norm)
            return midpoint_cache[key]

        new_faces: list[tuple[int, int, int]] = []
        new_ids: list[str] = []
        for fid, (a, b, c) in zip(face_ids, faces):
            ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
            children = ((a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca))
            for child_index, child in enumerate(children):
                new_faces.append(child)
                new_ids.append(f"{fid}/{current}.{child_index}")
        faces, face_ids = new_faces, new_ids
    node_ids = tuple(f"I:{i:08d}" for i in range(len(vertices)))
    return SphericalReferenceMesh(level, node_ids,
                                  tuple(tuple(float(x) for x in v) for v in vertices),
                                  tuple(face_ids), tuple(faces), float(radius_m))


def validate_spherical_mesh(mesh: SphericalReferenceMesh,
                            relative_area_tolerance: float = 1e-12) -> dict[str, float | int | bool]:
    """Check closed two-manifold topology and deterministic spherical area closure."""
    if not math.isfinite(relative_area_tolerance) or relative_area_tolerance <= 0:
        raise ValueError("positive finite relative area tolerance required")
    incidence: dict[tuple[int, int], int] = {}
    for face in mesh.faces:
        if len(set(face)) != 3 or any(i < 0 or i >= len(mesh.xyz) for i in face):
            raise ValueError("invalid triangular face")
        for i, j in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edge = tuple(sorted((i, j)))
            incidence[edge] = incidence.get(edge, 0) + 1
    area = mesh.total_area_m2()
    sphere_area = 4.0 * math.pi * mesh.radius_m * mesh.radius_m
    error = abs(area - sphere_area)
    relative = error / sphere_area
    closed = bool(incidence) and all(count == 2 for count in incidence.values())
    euler = len(mesh.xyz) - len(incidence) + len(mesh.faces)
    return {"vertex_count": len(mesh.xyz), "edge_count": len(incidence),
            "face_count": len(mesh.faces), "euler_characteristic": euler,
            "two_manifold_closed": closed, "sphere_area_m2": sphere_area,
            "accounted_area_m2": area, "absolute_area_error_m2": error,
            "relative_area_error": relative,
            "area_closure_pass": relative <= relative_area_tolerance,
            "topology_pass": closed and euler == 2}
