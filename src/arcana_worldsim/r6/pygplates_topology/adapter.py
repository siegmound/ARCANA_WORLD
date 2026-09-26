"""Build pyGPlates geometry candidates while preserving source identities."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any

from arcana_worldsim.r6.pygplates_mapping.adapter import (
    MappingInput,
    _boundary_endpoints,
    _junction_lat_lon,
    _feature,
)


def identity_digest(data: MappingInput) -> str:
    """Hash canonical identity fields in a stable order, not runtime reprs."""
    a = data.arrays
    identity = {
        "payload_sha256": data.manifest["payload"]["sha256"],
        "plates": sorted({int(value) for value in a["face_plate_id"]}),
        "faces": [
            [int(row), int(col), int(plate)]
            for row, col, plate in zip(a["face_row"], a["face_col"], a["face_plate_id"])
        ],
        "boundaries": [
            [int(row), int(col), int(axis), int(pa), int(pb)]
            for row, col, axis, pa, pb in zip(
                a["boundary_edge_row"], a["boundary_edge_col"],
                a["boundary_edge_axis"], a["boundary_plate_a"], a["boundary_plate_b"],
            )
        ],
        "junctions": [
            {
                "junction_id": record["junction_id"],
                "vertex_id": record["vertex_id"],
                "incident_plate_ids": list(record["incident_plate_ids"]),
                "degree": int(record["degree"]),
            }
            for record in sorted(data.junction_census["junctions"], key=lambda item: item["junction_id"])
        ],
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _plate_boundary_rings(data: MappingInput) -> dict[int, list[list[tuple[float, float]]]]:
    """Trace the manifested positive-length grid edges into plate rings.

    The function refuses branching or disconnected outlines instead of making
    an ordering choice. Pole vertices are identified as single spherical points.
    """
    import numpy as np

    a = data.arrays
    plate_grid = np.full((180, 360), -1, dtype=np.int16)
    for row, col, plate_id in zip(a["face_row"], a["face_col"], a["face_plate_id"]):
        plate_grid[int(row), int(col)] = int(plate_id)
    if (plate_grid < 0).any():
        raise ValueError("canonical face rows/columns do not cover the 180x360 grid")

    edges_by_plate: dict[int, list[tuple[tuple[int, int], tuple[int, int]]]] = defaultdict(list)

    def node(y: int, x: int) -> tuple[int, int]:
        return (y, 0) if y in (0, 180) else (y, x % 360)

    for row, col, axis, plate_a, plate_b in zip(
        a["boundary_edge_row"], a["boundary_edge_col"], a["boundary_edge_axis"],
        a["boundary_plate_a"], a["boundary_plate_b"],
    ):
        row_i, col_i, axis_i = int(row), int(col), int(axis)
        if axis_i == 0:
            west_id = int(plate_grid[row_i, col_i])
            east_id = int(plate_grid[row_i, (col_i + 1) % 360])
            start, end = node(row_i, col_i + 1), node(row_i + 1, col_i + 1)
            side_ids = {west_id, east_id}
            edges_by_plate[west_id].append((start, end))
            edges_by_plate[east_id].append((end, start))
        elif axis_i == 1:
            south_id = int(plate_grid[row_i, col_i])
            north_id = int(plate_grid[row_i + 1, col_i])
            start, end = node(row_i + 1, col_i), node(row_i + 1, col_i + 1)
            side_ids = {south_id, north_id}
            edges_by_plate[north_id].append((start, end))
            edges_by_plate[south_id].append((end, start))
        else:
            raise ValueError(f"unsupported canonical boundary axis: {axis_i}")
        if side_ids != {int(plate_a), int(plate_b)} or len(side_ids) != 2:
            raise ValueError("boundary edge plate identities disagree with adjacent canonical faces")

    rings_by_plate: dict[int, list[list[tuple[float, float]]]] = {}
    for plate_id in sorted({int(value) for value in a["face_plate_id"]}):
        edges = edges_by_plate[plate_id]
        outgoing: dict[tuple[int, int], tuple[int, int]] = {}
        incoming = Counter(end for _, end in edges)
        for start, end in edges:
            if start in outgoing:
                raise ValueError(f"plate {plate_id} boundary branches at {start}")
            outgoing[start] = end
        if set(outgoing) != set(incoming) or any(count != 1 for count in incoming.values()):
            raise ValueError(f"plate {plate_id} boundary is open or branched")

        seen: set[tuple[int, int]] = set()
        rings: list[list[tuple[float, float]]] = []
        for start in sorted(outgoing):
            if start in seen:
                continue
            current = start
            vertices = [start]
            while current not in seen:
                seen.add(current)
                current = outgoing[current]
                vertices.append(current)
            if current != start:
                raise ValueError(f"plate {plate_id} boundary does not close into a ring")
            coords = [
                (90.0 if y == 180 else -90.0 if y == 0 else -90.0 + y,
                 0.0 if y in (0, 180) else -180.0 + x)
                for y, x in vertices
            ]
            # Repeated pole nodes have already been collapsed; retain the
            # explicit final closure required by PolygonOnSphere.
            if len(coords) < 4:
                raise ValueError(f"plate {plate_id} outline has fewer than three edges")
            rings.append(coords)
        if len(rings) != 1:
            raise ValueError(f"plate {plate_id} has {len(rings)} rings; a single polygon is not justified")
        rings_by_plate[plate_id] = rings
    return rings_by_plate


def construct_geometry_candidates(data: MappingInput, pygplates: Any) -> dict[str, Any]:
    """Construct face polygons, support lines and named junction points.

    The canonical partition is represented by 12 plate polygon candidates
    traced from all 64,800 canonical cells and their shared grid edges. No
    smoothing or sub-cell inference is applied. Boundary identity is the exact
    canonical grid-edge tuple (row, column, axis), because the partition payload
    contains no boundary-ID field. Junction IDs come from the manifested census.

    PolygonOnSphere uses great-circle arcs. Canonical latitude edges are
    small-circle arcs, so exact curve equivalence is not claimed by this probe.
    """
    a = data.arrays
    rings_by_plate = _plate_boundary_rings(data)
    plate_features: dict[int, Any] = {}
    for plate_id, rings in rings_by_plate.items():
        geometry = pygplates.PolygonOnSphere(rings[0])
        plate_features[plate_id] = _feature(
            pygplates, geometry, f"R6_T0_PLATE_{plate_id}", plate_id,
        )

    boundary_features = []
    boundary_identities = []
    for row, col, axis, plate_a, plate_b in zip(
        a["boundary_edge_row"], a["boundary_edge_col"], a["boundary_edge_axis"],
        a["boundary_plate_a"], a["boundary_plate_b"],
    ):
        row_i, col_i, axis_i = int(row), int(col), int(axis)
        plate_a_i, plate_b_i = int(plate_a), int(plate_b)
        geometry = pygplates.PolylineOnSphere(_boundary_endpoints(row_i, col_i, axis_i))
        # No reconstruction plate ID is assigned: either side would be an
        # arbitrary physical/topological choice absent a governed rule.
        boundary_features.append(_feature(
            pygplates, geometry,
            f"R6_T0_EDGE_R{row_i:03d}_C{col_i:03d}_A{axis_i}",
        ))
        boundary_identities.append((row_i, col_i, axis_i, plate_a_i, plate_b_i))

    junction_features = []
    junction_identities = []
    for record in sorted(data.junction_census["junctions"], key=lambda item: item["junction_id"]):
        point = pygplates.PointOnSphere(*_junction_lat_lon(record["vertex_id"]))
        junction_features.append(_feature(pygplates, point, record["junction_id"]))
        junction_identities.append({
            "junction_id": record["junction_id"],
            "vertex_id": record["vertex_id"],
            "incident_plate_ids": list(record["incident_plate_ids"]),
            "degree": int(record["degree"]),
        })

    return {
        "plate_features_by_id": plate_features,
        "plate_polygon_rings": rings_by_plate,
        "face_identities": [
            (int(row), int(col), int(plate_id))
            for row, col, plate_id in zip(a["face_row"], a["face_col"], a["face_plate_id"])
        ],
        "boundary_support_features": boundary_features,
        "boundary_identities": boundary_identities,
        "junction_point_features": junction_features,
        "junction_identities": junction_identities,
    }


def attempt_network_assembly(geometry: dict[str, Any], pygplates: Any) -> dict[str, Any]:
    """Ask pyGPlates 1.0 to section boundary support without inventing IDs."""
    sections = []
    rejected = 0
    for feature in geometry["boundary_support_features"]:
        section = pygplates.GpmlTopologicalSection.create(
            feature,
            topological_geometry_type=pygplates.GpmlTopologicalNetwork,
        )
        if section is None:
            rejected += 1
        else:
            sections.append(section)

    # Empty/partial network containers would turn a failed identity mapping
    # into a misleading constructed network, so only build when every support
    # segment has an admissible network section.
    if rejected or len(sections) != len(geometry["boundary_support_features"]):
        return {
            "network_created": False,
            "network_feature": None,
            "boundary_sections_created": len(sections),
            "boundary_sections_rejected": rejected,
            "failure_class": "BOUNDARY_SUPPORT_NOT_RECONSTRUCTABLE_BY_PLATE_ID_OR_HALF_STAGE_ROTATION",
        }

    network = pygplates.GpmlTopologicalNetwork(sections, [])
    network_feature = pygplates.Feature.create_topological_network_feature(network)
    return {
        "network_created": network_feature is not None,
        "network_feature": network_feature,
        "boundary_sections_created": len(sections),
        "boundary_sections_rejected": 0,
        "failure_class": None if network_feature is not None else "NETWORK_FEATURE_FACTORY_RETURNED_NONE",
    }
