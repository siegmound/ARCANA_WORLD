"""Orchestrate the noncanonical assembly and resolution capability probe."""
from __future__ import annotations

from typing import Any

from .adapter import attempt_network_assembly, construct_geometry_candidates, identity_digest
from .contracts import governance_flags, validate_topology_input


def run_probe(data: Any, pygplates: Any) -> dict[str, Any]:
    inventory = validate_topology_input(data)
    geometry = construct_geometry_candidates(data, pygplates)
    network = attempt_network_assembly(geometry, pygplates)
    plate_ids = sorted(geometry["plate_features_by_id"])
    plate_identity_preserved = plate_ids == sorted({int(value) for value in data.arrays["face_plate_id"]})
    boundary_identity_preserved = len(set(geometry["boundary_identities"])) == inventory["boundary_segment_count"]
    junction_ids = [item["junction_id"] for item in geometry["junction_identities"]]
    source_junction_ids = [item["junction_id"] for item in sorted(
        data.junction_census["junctions"], key=lambda item: item["junction_id"]
    )]
    junction_identity_preserved = junction_ids == source_junction_ids

    # Resolution requires a rotation model. Supplying one would cross the
    # explicitly forbidden motion-assignment boundary, so it is only attempted
    # if a network exists and a no-motion model is independently governed.
    resolved_created = False
    resolution_status = "NOT_ATTEMPTED_NETWORK_NOT_CREATED"
    if network["network_created"]:
        resolution_status = "NOT_ATTEMPTED_ROTATION_MODEL_REQUIRED_AND_FORBIDDEN"

    repeatability_first = identity_digest(data)
    repeatability_second = identity_digest(data)
    repeatability = repeatability_first
    gates = {
        "NETWORK_CREATED": bool(network["network_created"]),
        "RESOLUTION_CREATED": resolved_created,
        "PLATE_IDENTITY_PRESERVED": plate_identity_preserved,
        "BOUNDARY_COUNT_PRESERVED": boundary_identity_preserved,
        "JUNCTION_COUNT_PRESERVED": junction_identity_preserved,
        "REPEATABLE": repeatability_first == repeatability_second,
    }
    return {
        "artifact": "R6_PYGPLATES_TOPOLOGY_ASSEMBLY_PROBE",
        "classification": "NONCANONICAL_COMPATIBILITY_DIAGNOSTIC",
        "status": "PASS" if all(gates.values()) else "FAIL",
        "decision": "TOPOLOGY_ASSEMBLY_COMPATIBLE" if all(gates.values()) else "TOPOLOGY_ASSEMBLY_BLOCKED",
        "failure_class": network["failure_class"],
        "pygplates_version": str(getattr(pygplates, "__version__", "UNKNOWN")),
        "time_ma": data.manifest["time_ma"],
        "input_counts": inventory,
        "geometry_counts": {
            "plate_identity_groups": len(plate_ids),
            "plate_polygon_features": len(geometry["plate_features_by_id"]),
            "canonical_cell_identities_represented": len(geometry["face_identities"]),
            "boundary_support_features": len(geometry["boundary_support_features"]),
            "junction_point_features": len(geometry["junction_point_features"]),
        },
        "network_created": bool(network["network_created"]),
        "boundary_sections_created": network["boundary_sections_created"],
        "boundary_sections_rejected": network["boundary_sections_rejected"],
        "resolved_created": resolved_created,
        "resolution_status": resolution_status,
        "plate_identity_preserved": plate_identity_preserved,
        "boundary_identity_preserved": boundary_identity_preserved,
        "junction_identity_preserved": junction_identity_preserved,
        "repeatability_sha256": repeatability,
        "gates": gates,
        "identity_notes": {
            "boundary_id": "canonical grid edge tuple (row, column, axis); the NPZ has no boundary-ID array",
            "plate_geometry": "12 polygons traced from all 64800 canonical cells; no smoothing or sub-cell inference",
            "curve_semantics": "PolygonOnSphere uses great-circle arcs; canonical latitude edges are small-circle arcs; exact curve equivalence and loss tolerance are UNBOUND",
            "junction_metadata": "junction ID, vertex ID, incident plate IDs, and degree are preserved from the census",
        },
        "governance": governance_flags(),
    }
