"""Parent-conforming spherical ownership integration primitives for R6.

The canonical 1-degree face ownership is authoritative. This module only
subdivides those faces for numerical integration; it never infers interior
plate ownership from a substitute global mesh. Cells retain their parent and
refinement lineage, and unresolved terminal area remains explicit.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
from typing import Callable, Iterable

import numpy as np


ALGORITHM_VERSION = "R6_PARENT_CONFORMING_REFERENCE_ARRANGEMENT_V1"
MODEL_REFINEMENT_SUPPORT = "MODEL_NUMERICAL_REFINEMENT_OF_CANONICAL_PARENT_FACE"


def _vertex_latlon(vertex_id: str) -> tuple[float, float]:
    prefix, row, col = vertex_id.split(":")
    if prefix != "GRID_VERTEX":
        raise ValueError(f"unsupported canonical vertex identity: {vertex_id}")
    row_i, col_i = int(row), int(col)
    if not (0 <= row_i <= 180 and 0 <= col_i <= 360):
        raise ValueError(f"canonical vertex outside grid: {vertex_id}")
    return -90.0 + row_i, -180.0 + col_i


def _normalized_vertex_id(vertex_id: str) -> tuple[int, int]:
    prefix, row, col = vertex_id.split(":")
    if prefix != "GRID_VERTEX":
        raise ValueError(f"unsupported canonical vertex identity: {vertex_id}")
    return int(row), int(col) % 360


@dataclass(frozen=True, slots=True)
class CanonicalBoundary:
    boundary_id: str
    component_id: str
    plate_pair: tuple[int, int]
    segment: object
    mid_lat_deg: float
    mid_lon_deg: float
    endpoint_vertex_ids: tuple[str, str]


class CanonicalBoundarySpatialIndex:
    """Deterministic row/longitude-window index over canonical edge segments.

    Candidate windows are expanded by the requested geodesic radius and a
    full source-cell margin. Exact distances are then evaluated by the
    existing finite great-circle/small-circle operator.
    """

    def __init__(self, segment_records: Iterable[dict], radius_m: float = 6_371_000.0):
        from .boundary_geometry import SphericalSegment
        self.radius_m = float(radius_m)
        if not math.isfinite(self.radius_m) or self.radius_m <= 0:
            raise ValueError("positive sphere radius required")
        records = []
        for record in sorted(segment_records, key=lambda x: x["boundary_id"]):
            (lat1, lon1), (lat2, lon2) = (_vertex_latlon(v) for v in record["endpoint_vertex_ids"])
            if abs(lat1 - lat2) < 1e-10:
                dlon = lon2 - lon1
                if dlon > 180: dlon -= 360
                if dlon < -180: dlon += 360
                geom = SphericalSegment(lat1, lon1, lat2, lon2, "SMALL_CIRCLE", dlon)
                mid_lon = (lon1 + dlon / 2.0 + 180.0) % 360.0 - 180.0
            elif abs(lon1 - lon2) < 1e-10:
                geom = SphericalSegment(lat1, lon1, lat2, lon2, "GREAT_CIRCLE")
                mid_lon = lon1
            else:
                raise ValueError(f"canonical parent edge is not meridional/parallel: {record['boundary_id']}")
            pair = tuple(sorted(map(int, record["ordered_plate_pair"])))
            if pair[0] == pair[1]:
                raise ValueError("boundary must separate distinct plates")
            records.append(CanonicalBoundary(str(record["boundary_id"]), "", pair, geom,
                                             (lat1 + lat2) / 2.0,
                                             mid_lon,
                                             tuple(record["endpoint_vertex_ids"])))
        if len({r.boundary_id for r in records}) != len(records):
            raise ValueError("canonical boundary IDs must be unique")
        by_pair_endpoint: dict[tuple[tuple[int, int], str], list[int]] = {}
        for i, rec in enumerate(records):
            for endpoint in rec.endpoint_vertex_ids:
                by_pair_endpoint.setdefault((rec.plate_pair, str(_normalized_vertex_id(endpoint))), []).append(i)
        unseen = set(range(len(records)))
        while unseen:
            root = min(unseen, key=lambda i: records[i].boundary_id)
            component, todo = set(), [root]
            while todo:
                i = todo.pop()
                if i not in unseen:
                    continue
                unseen.remove(i)
                component.add(i)
                rec = records[i]
                for endpoint in rec.endpoint_vertex_ids:
                    todo.extend(by_pair_endpoint.get((rec.plate_pair, str(_normalized_vertex_id(endpoint))), ()))
            ids = sorted(records[i].boundary_id for i in component)
            pair = records[root].plate_pair
            component_id = f"R6CORRIDOR:{pair[0]}:{pair[1]}:{sha256('|'.join(ids).encode()).hexdigest()[:12]}"
            for i in component:
                old = records[i]
                records[i] = CanonicalBoundary(old.boundary_id, component_id, old.plate_pair,
                                               old.segment, old.mid_lat_deg, old.mid_lon_deg,
                                               old.endpoint_vertex_ids)
        self.records = tuple(records)
        components: dict[str, list[CanonicalBoundary]] = {}
        for record in self.records:
            components.setdefault(record.component_id, []).append(record)
        self.by_component = {key: tuple(value) for key, value in components.items()}
        rows: dict[int, list[CanonicalBoundary]] = {}
        for record in self.records:
            row = min(179, max(0, int(math.floor(record.mid_lat_deg + 90.0))))
            rows.setdefault(row, []).append(record)
        self.by_latitude_row = {row: tuple(items) for row, items in rows.items()}

    def query(self, lat_deg: float, lon_deg: float, radius_m: float) -> tuple[tuple[CanonicalBoundary, float], ...]:
        if not math.isfinite(radius_m) or radius_m < 0:
            raise ValueError("query radius must be finite and nonnegative")
        angular_deg = math.degrees(min(math.pi, (radius_m / self.radius_m))) + 1.5
        first_row = max(0, int(math.floor(lat_deg - angular_deg + 90.0)))
        last_row = min(179, int(math.floor(lat_deg + angular_deg + 90.0)))
        extreme_lat = min(90.0, abs(lat_deg) + angular_deg)
        min_cos = math.cos(math.radians(extreme_lat))
        if min_cos <= 1e-8 or angular_deg >= 90:
            lon_delta = 180.0
        else:
            lon_delta = min(180.0, angular_deg / min_cos + 1.5)
        found = []
        for row in range(first_row, last_row + 1):
            for record in self.by_latitude_row.get(row, ()):
                dlon = abs((record.mid_lon_deg - lon_deg + 180.0) % 360.0 - 180.0)
                if dlon > lon_delta:
                    continue
                distance = record.segment.distance_m(lat_deg, lon_deg, self.radius_m)
                if distance <= radius_m:
                    found.append((record, distance))
        return tuple(sorted(found, key=lambda item: (item[1], item[0].boundary_id)))


def junction_geography(junction_records: Iterable[dict]) -> tuple[dict, ...]:
    """Bind canonical junction IDs and grid-vertex coordinates."""
    result = []
    for record in sorted(junction_records, key=lambda x: x["junction_id"]):
        lat, lon = _vertex_latlon(record["vertex_id"])
        if int(record["degree"]) != 3 or len(record["incident_boundary_ids"]) != 3:
            raise ValueError(f"degree-3 junction contract violated: {record['junction_id']}")
        result.append({"junction_id": record["junction_id"], "lat_deg": lat, "lon_deg": lon,
                       "vertex_id": record["vertex_id"],
                       "incident_boundary_ids": tuple(record["incident_boundary_ids"])})
    if len({item["junction_id"] for item in result}) != len(result):
        raise ValueError("junction IDs must be unique")
    return tuple(result)


def build_canonical_junction_bases(junction_records: Iterable[dict],
                                   boundary_index: CanonicalBoundarySpatialIndex,
                                   width_m: float,
                                   subdivisions_per_side: int = 128,
                                   parent_plate_grid: np.ndarray | None = None) -> tuple[dict, ...]:
    """Instantiate the existing P1 patch at each real junction.

    The three patch-side plate pairs are matched exactly to the canonical
    incident boundary pairs. Side-normal directions are fitted to the three
    measured outgoing branch bearings; no equal-angle geometry is substituted.
    """
    from itertools import permutations
    from .boundary_geometry import unit_xyz
    from .junction_basis import ThreePlateJunctionBasis
    if not math.isfinite(width_m) or width_m <= 0:
        raise ValueError("positive finite model width required")
    if parent_plate_grid is not None:
        parent_plate_grid = np.asarray(parent_plate_grid)
        if parent_plate_grid.shape != (180, 360) or not np.issubdtype(parent_plate_grid.dtype, np.integer):
            raise ValueError("parent_plate_grid must be an integer 180x360 canonical ownership array")
    records = {r.boundary_id: r for r in boundary_index.records}
    patches = []
    for junction in junction_geography(junction_records):
        result = {"junction_id": junction["junction_id"], "vertex_id": junction["vertex_id"],
                  "lat_deg": junction["lat_deg"], "lon_deg": junction["lon_deg"],
                  "incident_boundary_ids": junction["incident_boundary_ids"],
                  "status": "BLOCKED", "reason": None, "basis": None}
        try:
            incident = [records.get(bid) for bid in junction["incident_boundary_ids"]]
            if any(record is None for record in incident):
                raise ValueError("missing canonical incident boundary")
            lat = math.radians(junction["lat_deg"])
            lon = math.radians(junction["lon_deg"])
            east = np.array((-math.sin(lon), math.cos(lon), 0.0))
            north = np.array((-math.sin(lat) * math.cos(lon),
                              -math.sin(lat) * math.sin(lon), math.cos(lat)))
            rays = []
            for record in incident:
                endpoints = record.endpoint_vertex_ids
                normalized_junction = _normalized_vertex_id(junction["vertex_id"])
                if normalized_junction not in {_normalized_vertex_id(v) for v in endpoints}:
                    raise ValueError(f"incident edge misses canonical junction vertex: {record.boundary_id}")
                matched_index = next(i for i, v in enumerate(endpoints)
                                     if _normalized_vertex_id(v) == normalized_junction)
                other_id = endpoints[1 - matched_index]
                other_lat, other_lon = _vertex_latlon(other_id)
                p = unit_xyz(other_lat, other_lon)
                theta_i = math.atan2(float(np.dot(p, north)), float(np.dot(p, east))) % (2 * math.pi)
                rays.append((theta_i, record))
            rays.sort(key=lambda item: (item[0], item[1].boundary_id))
            theta = [item[0] for item in rays]
            pair_sequence = [item[1].plate_pair for item in rays]
            plate_set = sorted({p for pair in pair_sequence for p in pair})
            if len(plate_set) != 3 or len(set(pair_sequence)) != 3:
                raise ValueError("canonical junction does not bind three distinct plate pairs")
            plate_orders = [order for order in permutations(plate_set)
                            if all(tuple(sorted((order[i], order[(i + 1) % 3]))) == pair_sequence[i]
                                   for i in range(3))]
            if not plate_orders:
                raise ValueError("canonical plate-pair incidence has no cyclic P1 trace order")
            t = theta
            gaps = (t[1] - t[0], t[2] - t[1], t[0] + 2 * math.pi - t[2])
            if any(gap <= 1e-10 or gap >= math.pi - 1e-10 for gap in gaps):
                raise ValueError("canonical branch rays do not define a nondegenerate convex three-side P1 patch")
            # Side-normal angles are solved on the unwrapped cyclic branch rays.
            phi = (t[0] - t[1] + t[2] - math.pi,
                   t[0] + t[1] - t[2] + math.pi,
                   -t[0] + t[1] + t[2] - math.pi)
            if not (phi[0] < phi[1] < phi[2] < phi[0] + 2 * math.pi):
                raise ValueError("fitted P1 patch vertices are not cyclic")
            azimuths = tuple(math.degrees(x) % 360.0 for x in phi)
            basis = None
            plate_order = None
            for order in plate_orders:
                candidate = ThreePlateJunctionBasis(junction["junction_id"], junction["lat_deg"],
                                                    junction["lon_deg"], order, width_m / 2.0,
                                                    subdivisions_per_side=subdivisions_per_side,
                                                    azimuths_deg=azimuths)
                if parent_plate_grid is not None:
                    endpoint_match = True
                    for edge in range(3):
                        va = np.asarray(candidate.vertices[edge])
                        vb = np.asarray(candidate.vertices[(edge + 1) % 3])
                        for t, expected_plate in ((1e-4, order[edge]), (1.0 - 1e-4, order[(edge + 1) % 3])):
                            qlat, qlon = candidate.latlon_at_xy(*(va * (1.0 - t) + vb * t))
                            row = min(179, max(0, int(math.floor(qlat + 90.0))))
                            col = int(math.floor((qlon + 180.0) % 360.0))
                            if int(parent_plate_grid[row, col]) != int(expected_plate):
                                endpoint_match = False
                                break
                        if not endpoint_match:
                            break
                    if not endpoint_match:
                        continue
                basis, plate_order = candidate, order
                break
            if basis is None:
                raise ValueError("P1 side endpoints do not match canonical parent plate sectors")
            result.update(status="BOUND", reason=None,
                          incident_boundary_ids_in_cyclic_order=tuple(x[1].boundary_id for x in rays),
                          incident_plate_pairs_in_cyclic_order=tuple(pair_sequence),
                          plate_ids_in_p1_cycle=tuple(plate_order),
                          branch_ray_azimuths_rad=tuple(theta),
                          p1_vertex_azimuths_deg=azimuths, basis=basis)
        except ValueError as exc:
            result["reason"] = str(exc)
        patches.append(result)
    return tuple(patches)


@dataclass(frozen=True, slots=True)
class ParentFace:
    parent_face_id: str
    plate_id: int
    row: int
    column: int
    south_deg: float
    north_deg: float
    west_deg: float
    east_deg: float

    def __post_init__(self) -> None:
        if not self.parent_face_id or self.plate_id < 0:
            raise ValueError("parent ID and nonnegative inherited plate ID are required")
        if not (0 <= self.row < 180 and 0 <= self.column < 360):
            raise ValueError("canonical parent index outside 180x360 domain")
        if not (-90 <= self.south_deg < self.north_deg <= 90):
            raise ValueError("invalid parent latitude interval")
        if not (math.isfinite(self.west_deg) and math.isfinite(self.east_deg)
                and self.east_deg > self.west_deg and self.east_deg - self.west_deg <= 360):
            raise ValueError("invalid unwrapped parent longitude interval")


@dataclass(frozen=True, slots=True)
class ArrangementCell:
    cell_id: str
    parent_face_id: str
    parent_plate_id: int
    refinement_path: tuple[int, ...]
    depth: int
    south_deg: float
    north_deg: float
    west_deg: float
    east_deg: float
    category: str
    owner_id: str | None
    area_m2: float
    support: str = MODEL_REFINEMENT_SUPPORT


def canonical_parent_faces(face_row: np.ndarray, face_col: np.ndarray,
                           face_plate_id: np.ndarray,
                           face_vertex_latlon_deg: np.ndarray | None = None) -> tuple[ParentFace, ...]:
    """Bind canonical 1-degree face indices and plate IDs without remapping."""
    rows = np.asarray(face_row)
    cols = np.asarray(face_col)
    plates = np.asarray(face_plate_id)
    if rows.shape != (64_800,) or cols.shape != rows.shape or plates.shape != rows.shape:
        raise ValueError("canonical parent arrays must each contain exactly 64,800 entries")
    if not (np.issubdtype(rows.dtype, np.integer) and np.issubdtype(cols.dtype, np.integer)
            and np.issubdtype(plates.dtype, np.integer)):
        raise ValueError("canonical parent row/column/plate arrays must be integer-valued")
    if (rows.min() != 0 or rows.max() != 179 or cols.min() != 0 or cols.max() != 359
            or len(set(zip(rows.tolist(), cols.tolist()))) != 64_800):
        raise ValueError("parent grid must be a unique complete 180x360 partition")
    rings = None if face_vertex_latlon_deg is None else np.asarray(face_vertex_latlon_deg)
    if rings is not None and rings.shape != (64_800, 5, 2):
        raise ValueError("canonical face rings must have shape (64800, 5, 2)")
    result = []
    for index, (row, col, plate) in enumerate(zip(rows.tolist(), cols.tolist(), plates.tolist())):
        # Payload row 0 is the southernmost band: [-90,-89]. Longitude cells
        # remain unwrapped, preserving the dateline cell as a one-degree face.
        south = -90.0 + int(row)
        north = south + 1.0
        west = -180.0 + int(col)
        if rings is not None:
            expected = np.asarray(((south, west), (south, west + 1.0),
                                   (north, west + 1.0), (north, west), (south, west)))
            if not np.array_equal(rings[index], expected):
                raise ValueError(f"canonical parent ring disagrees with row/column at payload index {index}")
        result.append(ParentFace(f"R6PARENT:{int(row):03d}:{int(col):03d}", int(plate),
                                 int(row), int(col), south, north, west, west + 1.0))
    return tuple(sorted(result, key=lambda f: (f.row, f.column)))


def spherical_rect_area_m2(south_deg: float, north_deg: float,
                           west_deg: float, east_deg: float,
                           radius_m: float = 6_371_000.0) -> float:
    """Exact area of a lat/lon rectangle bounded by meridians/parallels."""
    if not (math.isfinite(radius_m) and radius_m > 0 and -90 <= south_deg < north_deg <= 90
            and math.isfinite(west_deg) and math.isfinite(east_deg)
            and 0 < east_deg - west_deg <= 360):
        raise ValueError("invalid spherical rectangle")
    return (radius_m * radius_m * math.radians(east_deg - west_deg)
            * (math.sin(math.radians(north_deg)) - math.sin(math.radians(south_deg))))


def split_parent_face(face: ParentFace) -> tuple[ParentFace, ...]:
    """Four deterministic equal-coordinate children, each nested in one parent."""
    mid_lat = (face.south_deg + face.north_deg) / 2.0
    mid_lon = (face.west_deg + face.east_deg) / 2.0
    bounds = ((face.south_deg, mid_lat, face.west_deg, mid_lon),
              (face.south_deg, mid_lat, mid_lon, face.east_deg),
              (mid_lat, face.north_deg, face.west_deg, mid_lon),
              (mid_lat, face.north_deg, mid_lon, face.east_deg))
    return tuple(ParentFace(face.parent_face_id, face.plate_id, face.row, face.column,
                            south, north, west, east) for south, north, west, east in bounds)


def certify_parent_region(parent_plate_id: int, boundary_distances_m: dict[str, float],
                          boundary_plate_pairs: dict[str, tuple[int, int]],
                          junction_distances_m: dict[str, float],
                          junction_incident_boundaries: dict[str, tuple[str, ...]],
                          half_width_m: float, cell_radius_m: float
                          ) -> tuple[str | None, str | None, bool]:
    """Conservative Lipschitz certificate for core/corridor/junction ownership.

    Distances are evaluated at the cell center. Since distance-to-a-fixed-set
    is 1-Lipschitz, the cell's distance interval is [d-rho, d+rho]. This
    function never assigns from a centroid when those intervals straddle a
    category boundary. Boundary/junction geometry remains a caller-owned
    canonical authority and IDs are returned unchanged.
    """
    if (not math.isfinite(half_width_m) or half_width_m <= 0 or
            not math.isfinite(cell_radius_m) or cell_radius_m < 0):
        raise ValueError("positive footprint and nonnegative cell radius required")
    if set(boundary_distances_m) != set(boundary_plate_pairs):
        raise ValueError("each boundary distance must have exactly one plate-pair authority")
    if any(not math.isfinite(d) or d < 0 for d in boundary_distances_m.values()):
        raise ValueError("boundary distances must be finite and nonnegative")
    if any(not math.isfinite(d) or d < 0 for d in junction_distances_m.values()):
        raise ValueError("junction distances must be finite and nonnegative")
    junction_candidates = [j for j, d in junction_distances_m.items()
                           if d + cell_radius_m <= half_width_m]
    if len(junction_candidates) == 1:
        junction_id = junction_candidates[0]
        incident = set(junction_incident_boundaries.get(junction_id, ()))
        other_possible = [bid for bid, d in boundary_distances_m.items()
                          if bid not in incident and d - cell_radius_m <= half_width_m]
        competing_junction = [j for j, d in junction_distances_m.items()
                              if j != junction_id and d - cell_radius_m <= half_width_m]
        if not other_possible and not competing_junction:
            return "JUNCTION_PATCH", junction_id, True
    # A feature can intersect the cell if its center distance minus the cell
    # radius is within the requested half-width. Only a unique feature whose
    # entire cell remains inside its footprint can own the whole cell.
    possible = [bid for bid, d in boundary_distances_m.items()
                if d - cell_radius_m <= half_width_m]
    contained = [bid for bid, d in boundary_distances_m.items()
                 if d + cell_radius_m <= half_width_m]
    if len(contained) >= 2:
        return "CORRIDOR_CONFLICT", "+".join(sorted(contained)), True
    if len(possible) == 1:
        bid = possible[0]
        if boundary_distances_m[bid] + cell_radius_m <= half_width_m:
            pair = boundary_plate_pairs[bid]
            if parent_plate_id in pair:
                return "BOUNDARY_ZONE", bid, True
            return "CORRIDOR_CONFLICT", bid, True
    if not possible and all(d - cell_radius_m > half_width_m
                            for d in junction_distances_m.values()):
        return "RIGID_CORE", f"PLATE:{int(parent_plate_id)}", True
    return "MIXED_REQUIRES_REFINEMENT", None, False


def classify_canonical_parent_cell(cell: ParentFace,
                                   boundary_index: CanonicalBoundarySpatialIndex,
                                   junction_patches: Iterable[dict],
                                   width_m: float,
                                   radius_m: float = 6_371_000.0) -> dict[str, object]:
    """Apply canonical boundary/junction distance certificates to one cell.

    The input is one cell nested inside an immutable canonical parent face.
    Candidate lookup expands by H plus the conservative cell radius. Junction
    ownership is certified against the actual P1 triangle, not a centroid or
    a surrogate circular buffer.
    """
    from .boundary_geometry import unit_xyz
    if not math.isfinite(width_m) or width_m <= 0:
        raise ValueError("positive finite width required")
    lat, lon, rho = cell_center_radius_m(cell, radius_m)
    half_width = width_m / 2.0
    candidates = boundary_index.query(lat, lon, half_width + rho)
    nearest_by_component: dict[str, tuple[CanonicalBoundary, float]] = {}
    for record, distance in candidates:
        current = nearest_by_component.get(record.component_id)
        if current is None or (distance, record.boundary_id) < (current[1], current[0].boundary_id):
            nearest_by_component[record.component_id] = (record, distance)
    pair_distances = {cid: d for cid, (_, d) in sorted(nearest_by_component.items())}
    pair_map = {cid: rec.plate_pair for cid, (rec, _) in sorted(nearest_by_component.items())}

    patches = tuple(junction_patches)
    junction_distances = {}
    patch_by_id = {}
    point = unit_xyz(lat, lon)
    for patch in patches:
        jlat = float(patch["lat_deg"])
        jlon = float(patch["lon_deg"])
        center = unit_xyz(jlat, jlon)
        angle = math.atan2(float(np.linalg.norm(np.cross(point, center))),
                           float(np.clip(np.dot(point, center), -1.0, 1.0)))
        distance = radius_m * angle
        if distance <= half_width + rho:
            jid = str(patch["junction_id"])
            junction_distances[jid] = distance
            patch_by_id[jid] = patch
    incident_corridors = {}
    for patch in patches:
        jid = str(patch["junction_id"])
        incident = set()
        for bid in patch.get("incident_boundary_ids_in_cyclic_order", patch.get("incident_boundary_ids", ())):
            rec = next((r for r in boundary_index.records if r.boundary_id == bid), None)
            if rec is not None:
                incident.add(rec.component_id)
        incident_corridors[jid] = tuple(sorted(incident))
    category, owner, certified = certify_parent_region(
        cell.plate_id, pair_distances, pair_map, junction_distances,
        incident_corridors, half_width, rho)
    if category == "JUNCTION_PATCH" and certified:
        patch = patch_by_id[owner]
        basis = patch.get("basis")
        if basis is not None and _cell_inside_junction_triangle(basis, lat, lon, rho):
            return {"category": category, "owner_id": owner, "certified": True,
                    "canonical_boundary_ids": tuple(patch.get("incident_boundary_ids_in_cyclic_order", ())),
                    "candidate_count": len(candidates), "cell_radius_m": rho}
        return {"category": "MIXED_REQUIRES_REFINEMENT", "owner_id": None,
                "certified": False, "candidate_count": len(candidates), "cell_radius_m": rho}
    if junction_distances:
        # The P1 triangles, not H-disks, define governed junction support. Any
        # cell close enough to possibly intersect one is refined until it can
        # be certified inside/outside the actual triangular patch.
        possible_patch = False
        for patch in patches:
            basis = patch.get("basis")
            if basis is None:
                continue
            xy = basis._log_map_xy(lat, lon)
            if _cell_near_junction_triangle(basis, xy, rho):
                possible_patch = True
                break
        if possible_patch:
            return {"category": "MIXED_REQUIRES_REFINEMENT", "owner_id": None,
                    "certified": False, "candidate_count": len(candidates), "cell_radius_m": rho}
    if category == "BOUNDARY_ZONE" and certified:
        rec = nearest_by_component[owner][0]
        return {"category": category, "owner_id": owner, "certified": True,
                "canonical_boundary_ids": (rec.boundary_id,),
                "candidate_count": len(candidates), "cell_radius_m": rho}
    return {"category": category, "owner_id": owner, "certified": certified,
            "canonical_boundary_ids": (), "candidate_count": len(candidates),
            "cell_radius_m": rho}


def _junction_signed_edge_distances(basis, x_m: float, y_m: float) -> tuple[float, float, float]:
    point = np.array((x_m, y_m), dtype=float)
    vertices = [np.asarray(v, dtype=float) for v in basis.vertices]
    area2 = float(np.linalg.det(np.column_stack((vertices[1] - vertices[0],
                                                  vertices[2] - vertices[0]))))
    if abs(area2) <= 1e-12:
        raise ValueError("degenerate canonical junction triangle")
    signs = 1.0 if area2 > 0 else -1.0
    result = []
    for i in range(3):
        a, b = vertices[i], vertices[(i + 1) % 3]
        edge = b - a
        signed = signs * float(edge[0] * (point[1] - a[1]) - edge[1] * (point[0] - a[0]))
        result.append(signed / float(np.linalg.norm(edge)))
    return tuple(result)


def _cell_inside_junction_triangle(basis, lat_deg: float, lon_deg: float, rho_m: float) -> bool:
    x, y = basis._log_map_xy(lat_deg, lon_deg)
    distances = _junction_signed_edge_distances(basis, x, y)
    theta = math.hypot(x, y) / basis.sphere_radius_m
    chart_factor = max(1.0, theta / max(math.sin(theta), 1e-12))
    return min(distances) > rho_m * chart_factor + 1e-6


def _cell_near_junction_triangle(basis, xy: tuple[float, float], rho_m: float) -> bool:
    distances = _junction_signed_edge_distances(basis, *xy)
    # Conservative triangle vicinity test: inside, or within rho of at least
    # the complete signed half-spaces defining one of its edges.
    return all(d >= -rho_m for d in distances)


def cell_center_radius_m(face: ParentFace, radius_m: float = 6_371_000.0) -> tuple[float, float, float]:
    """Return center lat/lon and a conservative geodesic cell-radius bound.

    The bound is half the latitude span plus half the longitude span, in
    radians. Every point is reachable by a meridian path followed by a
    parallel path, whose length is no greater than this sum times R. It is
    used only as a Lipschitz distance enclosure, not as support resolution.
    """
    lat = (face.south_deg + face.north_deg) / 2.0
    lon = (face.west_deg + face.east_deg) / 2.0
    half_path = 0.5 * math.radians((face.north_deg - face.south_deg)
                                   + (face.east_deg - face.west_deg))
    rho = min(math.pi * radius_m, radius_m * half_path * (1.0 + 2e-12) + 1e-6)
    return lat, ((lon + 180.0) % 360.0) - 180.0, rho


def build_parent_conforming_reference_arrangement(
    canonical_parent_partition: Iterable[ParentFace],
    classify_and_certify: Callable[[ParentFace, float], tuple[str | None, str | None, bool]],
    width_m: float,
    refinement_level: int,
    radius_m: float = 6_371_000.0,
) -> dict[str, object]:
    """Build an adaptive parent-owned spherical arrangement.

    ``classify_and_certify(cell, rho)`` returns (category, owner_id, proven).
    ``proven=False`` forces deterministic four-way subdivision. No centroid
    fallback exists. Terminal uncertainty is accounted separately.
    """
    if not math.isfinite(width_m) or width_m <= 0:
        raise ValueError("positive finite requested width is required")
    if not isinstance(refinement_level, int) or not 0 <= refinement_level <= 12:
        raise ValueError("refinement_level must be in [0, 12]")
    parents = tuple(canonical_parent_partition)
    ids = [f.parent_face_id for f in parents]
    if len(ids) != 64_800 or len(set(ids)) != len(ids):
        raise ValueError("exactly 64,800 uniquely identified canonical parent faces are required")
    if len({(f.row, f.column) for f in parents}) != 64_800:
        raise ValueError("duplicate or missing canonical parent grid index")
    leaves: list[ArrangementCell] = []
    refined_parent_ids: set[str] = set()
    terminal_area = 0.0
    def visit(parent: ParentFace, cell: ParentFace, path: tuple[int, ...]) -> None:
        nonlocal terminal_area
        _, _, rho = cell_center_radius_m(cell, radius_m)
        category, owner, proven = classify_and_certify(cell, rho)
        if proven and category not in (None, "MIXED_REQUIRES_REFINEMENT", "CORRIDOR_CONFLICT"):
            leaves.append(ArrangementCell(
                f"{parent.parent_face_id}/" + (".".join(map(str, path)) if path else "L0"),
                parent.parent_face_id, parent.plate_id, path, len(path), cell.south_deg,
                cell.north_deg, cell.west_deg, cell.east_deg, category, owner,
                spherical_rect_area_m2(cell.south_deg, cell.north_deg, cell.west_deg,
                                       cell.east_deg, radius_m)))
            return
        if len(path) < refinement_level:
            refined_parent_ids.add(parent.parent_face_id)
            for i, child in enumerate(split_parent_face(cell)):
                visit(parent, child, path + (i,))
            return
        area = spherical_rect_area_m2(cell.south_deg, cell.north_deg, cell.west_deg,
                                      cell.east_deg, radius_m)
        terminal_area += area
        category = category if category == "CORRIDOR_CONFLICT" else "MIXED_REQUIRES_REFINEMENT"
        leaves.append(ArrangementCell(
            f"{parent.parent_face_id}/" + (".".join(map(str, path)) if path else "L0"),
            parent.parent_face_id, parent.plate_id, path, len(path), cell.south_deg,
            cell.north_deg, cell.west_deg, cell.east_deg, category, owner, area))
    for parent in parents:
        visit(parent, parent, ())
    area_by_category: dict[str, float] = {}
    for cell in leaves:
        area_by_category[cell.category] = area_by_category.get(cell.category, 0.0) + cell.area_m2
    total = math.fsum(c.area_m2 for c in leaves)
    sphere = 4.0 * math.pi * radius_m * radius_m
    return {"algorithm_version": ALGORITHM_VERSION, "width_m": width_m,
            "refinement_level": refinement_level, "parent_face_count": len(parents),
            "cells": tuple(leaves), "terminal_cell_count": len(leaves),
            "refined_parent_face_count": len(refined_parent_ids),
            "refined_parent_face_ids": tuple(sorted(refined_parent_ids)),
            "area_by_category_m2": dict(sorted(area_by_category.items())),
            "ambiguous_area_m2": area_by_category.get("MIXED_REQUIRES_REFINEMENT", 0.0),
            "conflict_area_m2": area_by_category.get("CORRIDOR_CONFLICT", 0.0),
            "accounted_area_m2": total, "sphere_area_m2": sphere,
            "area_closure_error_m2": abs(total - sphere),
            "ownership_complete": (terminal_area == 0.0 and
                                   area_by_category.get("MIXED_REQUIRES_REFINEMENT", 0.0) == 0.0 and
                                   area_by_category.get("CORRIDOR_CONFLICT", 0.0) == 0.0),
            "support": MODEL_REFINEMENT_SUPPORT}


def validate_parent_conforming_arrangement(result: dict[str, object],
                                            relative_area_tolerance: float = 1e-12) -> dict[str, object]:
    if relative_area_tolerance <= 0 or not math.isfinite(relative_area_tolerance):
        raise ValueError("positive finite area tolerance required")
    cells = result.get("cells")
    if not isinstance(cells, tuple) or not cells:
        raise ValueError("arrangement must contain terminal cells")
    if any(c.area_m2 <= 0 or c.parent_face_id not in c.cell_id for c in cells):
        raise ValueError("invalid area or broken parent provenance")
    accounted = math.fsum(c.area_m2 for c in cells)
    sphere = float(result["sphere_area_m2"])
    closure = abs(accounted - sphere) / sphere
    return {"parent_face_count": result["parent_face_count"], "cell_count": len(cells),
            "area_accounting_pass": math.isclose(accounted, float(result["accounted_area_m2"]),
                                                rel_tol=1e-13, abs_tol=1e-3),
            "sphere_closure_relative_error": closure,
            "sphere_closure_pass": closure <= relative_area_tolerance,
            "ambiguous_area_m2": result["ambiguous_area_m2"],
            "conflict_area_m2": result["conflict_area_m2"],
            "ownership_complete": result["ownership_complete"]}
