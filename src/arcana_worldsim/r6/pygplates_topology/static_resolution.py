"""Static topological-polygon resolution diagnostic for the R6 t0 partition."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from arcana_worldsim.r6.pygplates_mapping.adapter import (
    MappingInput,
    _junction_lat_lon,
)

from .adapter import construct_static_topological_polygons, ordered_boundary_sections
from .contracts import governance_flags, validate_topology_input

ARCANA_TIME_MA = 210.0
PYGPLATES_DIAGNOSTIC_EPOCH = 0.0


def _error_text(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def _junction_incidence(
    data: MappingInput,
    resolved_records: list[dict[str, Any]],
    pygplates: Any,
) -> dict[str, Any]:
    results = []
    for junction in data.junction_census["junctions"]:
        point = pygplates.PointOnSphere(*_junction_lat_lon(junction["vertex_id"]))
        incident = set()
        for item in resolved_records:
            points = item["geometry"].get_points()
            if point in points:
                incident.add(item["plate_id"])
        expected = {int(plate_id) for plate_id in junction["incident_plate_ids"]}
        results.append({
            "junction_id": junction["junction_id"],
            "expected_plate_ids": sorted(expected),
            "resolved_plate_ids": sorted(incident),
            "matches": incident == expected,
        })
    available = bool(results) and all(item["resolved_plate_ids"] for item in results)
    mismatches = sum(not item["matches"] for item in results)
    return {
        "available": available,
        "mismatches": mismatches if available else None,
        "records": results if available else [],
        "reason": None if available else "junction vertex incidence is not exposed by resolved polygon vertices",
    }


def _resolved_signature(records: list[dict[str, Any]]) -> str:
    value = []
    for item in sorted(records, key=lambda record: record["plate_id"]):
        points = [tuple(map(float, point)) for point in item["geometry"].to_lat_lon_list()]
        value.append({"plate_id": item["plate_id"], "points": points})
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolved_records(snapshot: Any, pygplates: Any) -> tuple[list[Any], list[Any], list[dict[str, Any]]]:
    resolved_topologies = snapshot.get_resolved_topologies(
        resolve_topology_types=(
            pygplates.ResolveTopologyType.boundary
            | pygplates.ResolveTopologyType.network
        )
    )
    resolved_boundaries = [
        item for item in resolved_topologies
        if isinstance(item, pygplates.ResolvedTopologicalBoundary)
    ]
    resolved_networks = [
        item for item in resolved_topologies
        if isinstance(item, pygplates.ResolvedTopologicalNetwork)
    ]
    records = []
    for item in resolved_boundaries:
        source_feature = item.get_feature()
        plate_id = source_feature.get_reconstruction_plate_id()
        if plate_id is None:
            raise ValueError("resolved topological boundary has no source plate ID")
        records.append({
            "plate_id": int(plate_id),
            "geometry": item.get_resolved_boundary(),
        })
    return resolved_boundaries, resolved_networks, records


def _coverage_counts(data: MappingInput, resolved_records: list[dict[str, Any]]) -> dict[str, int]:
    uncovered = multiple = wrong_plate = 0
    for row, col, plate_id in zip(
        data.arrays["face_row"], data.arrays["face_col"], data.arrays["face_plate_id"]
    ):
        point = (
            -90.0 + int(row) + 0.5,
            -180.0 + int(col) + 0.5,
        )
        matches = [
            item["plate_id"]
            for item in resolved_records
            if item["geometry"].is_point_in_polygon(point)
        ]
        if not matches:
            uncovered += 1
        if len(matches) > 1:
            multiple += 1
        if int(plate_id) not in matches:
            wrong_plate += 1
    return {
        "cell_centres_tested": len(data.arrays["face_plate_id"]),
        "uncovered_cell_centres": uncovered,
        "multiply_covered_cell_centres": multiple,
        "wrong_plate_cell_centres": wrong_plate,
    }


def _base_report(data: MappingInput) -> dict[str, Any]:
    inventory = validate_topology_input(data)
    section_plan = ordered_boundary_sections(data)
    boundary_keys = {
        (int(row), int(col), int(axis))
        for row, col, axis in zip(
            data.arrays["boundary_edge_row"],
            data.arrays["boundary_edge_col"],
            data.arrays["boundary_edge_axis"],
        )
    }
    identity_value = {
        "payload_sha256": data.manifest["payload"]["sha256"],
        "plate_ids": sorted(section_plan),
        "boundary_keys": sorted(boundary_keys),
        "junctions": [
            [record["junction_id"], record["vertex_id"],
             list(record["incident_plate_ids"]), int(record["degree"])]
            for record in sorted(data.junction_census["junctions"], key=lambda item: item["junction_id"])
        ],
    }
    identity_hash = hashlib.sha256(json.dumps(
        identity_value, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return {
        "artifact": "R6_PYGPLATES_STATIC_TOPOLOGY_RESOLUTION",
        "classification": "NONCANONICAL_COMPATIBILITY_DIAGNOSTIC",
        "arcana_time_ma": ARCANA_TIME_MA,
        "pygplates_diagnostic_epoch": PYGPLATES_DIAGNOSTIC_EPOCH,
        "pygplates_version": None,
        "canonical_payload_sha256": data.manifest["payload"]["sha256"],
        "input_counts": inventory,
        "topological_polygon_features_created": None,
        "topological_polygon_features_expected": inventory["plate_count"],
        "boundary_support_features": len(boundary_keys),
        "boundary_support_features_created": None,
        "unique_boundary_identities": len(boundary_keys),
        "resolved_topological_boundaries": None,
        "resolved_topological_networks": None,
        "plate_identity_preserved": None,
        "boundary_identity_preserved": None,
        "junction_identity_preserved": None,
        "junction_incidence_validation": "UNAVAILABLE",
        "junction_incidence_mismatches": None,
        "junction_incidence_reason": "pyGPlates runtime unavailable",
        "coverage": {
            "cell_centres_tested": inventory["face_count"],
            "uncovered_cell_centres": None,
            "multiply_covered_cell_centres": None,
            "wrong_plate_cell_centres": None,
        },
        "empty_rotation_model_used": False,
        "rotations_assigned": False,
        "resolution_attempted": False,
        "resolution_succeeded": False,
        "resolution_error": "PYGPLATES_RUNTIME_UNAVAILABLE",
        "repeatability": True,
        "repeatability_sha256": identity_hash,
        "exact_curve_semantics": "UNBOUND; canonical latitude edges are small-circle arcs while PolygonOnSphere uses great-circle arcs",
        "decision": "PYGPLATES_RUNTIME_UNAVAILABLE",
        "status": "PARTIAL",
        "governance": governance_flags(),
    }


def run_static_topology_resolution(data: MappingInput, pygplates: Any) -> dict[str, Any]:
    """Build 12 shared-edge topological polygons and resolve only at epoch 0."""
    report = _base_report(data)
    report["pygplates_version"] = str(getattr(pygplates, "__version__", "UNKNOWN"))
    try:
        topology = construct_static_topological_polygons(data, pygplates)
    except Exception as exc:
        report.update({
            "topological_polygon_features_created": 0,
            "boundary_support_features_created": 0,
            "decision": "TOPOLOGICAL_POLYGON_CONSTRUCTION_FAILED",
            "status": "FAIL",
            "construction_error": _error_text(exc),
            "resolution_error": None,
        })
        return report

    polygon_features = topology["topological_features_by_plate"]
    boundary_features = topology["boundary_support_features"]
    plate_ids = sorted(polygon_features)
    report.update({
        "topological_polygon_features_created": len(polygon_features),
        "boundary_support_features_created": len(boundary_features),
        "plate_identity_preserved": plate_ids == sorted({
            int(value) for value in data.arrays["face_plate_id"]
        }),
        "boundary_identity_preserved": (
            len(set(topology["boundary_identities"])) == len(boundary_features)
            and len(topology["boundary_identities"]) == report["unique_boundary_identities"]
            and all(len(refs) > 0 for refs in topology["sections_by_plate"].values())
        ),
        "junction_identity_preserved": (
            sorted(topology["junction_points"]) == sorted(
                record["junction_id"] for record in data.junction_census["junctions"]
            )
        ),
        "resolved_topological_boundaries": 0,
        "resolved_topological_networks": 0,
    })
    topological_features = [*boundary_features, *polygon_features.values()]

    try:
        rotation_model = pygplates.RotationModel([])
        report["empty_rotation_model_used"] = True
    except Exception as exc:
        report.update({
            "decision": "EMPTY_ROTATION_MODEL_UNSUPPORTED",
            "status": "PARTIAL",
            "resolution_error": _error_text(exc),
        })
        return report

    try:
        model = pygplates.TopologicalModel(
            topological_features=topological_features,
            rotation_model=rotation_model,
            anchor_plate_id=0,
        )
    except Exception as exc:
        report.update({
            "decision": "TOPOLOGICAL_MODEL_CONSTRUCTION_FAILED",
            "status": "PARTIAL",
            "resolution_error": _error_text(exc),
        })
        return report

    report["resolution_attempted"] = True
    try:
        snapshot = model.topological_snapshot(PYGPLATES_DIAGNOSTIC_EPOCH)
    except Exception as exc:
        report.update({
            "decision": "STATIC_TOPOLOGY_RESOLUTION_FAILED",
            "status": "PARTIAL",
            "resolution_error": _error_text(exc),
        })
        return report

    report["resolution_succeeded"] = True
    report["resolution_error"] = None
    try:
        resolved_boundaries, resolved_networks, resolved_records = _resolved_records(snapshot, pygplates)
        resolved_ids = [record["plate_id"] for record in resolved_records]
        resolved_identity_ok = (
            len(resolved_records) == len(plate_ids)
            and sorted(resolved_ids) == plate_ids
            and len(set(resolved_ids)) == len(resolved_ids)
        )
        report["resolved_topological_boundaries"] = len(resolved_boundaries)
        report["resolved_topological_networks"] = len(resolved_networks)
        report["plate_identity_preserved"] = bool(
            report["plate_identity_preserved"] and resolved_identity_ok
        )

        coverage = _coverage_counts(data, resolved_records)
        report["coverage"] = coverage
        junction_incidence = _junction_incidence(data, resolved_records, pygplates)
        report["junction_incidence_validation"] = (
            "PASS" if junction_incidence["available"] and junction_incidence["mismatches"] == 0
            else "FAIL" if junction_incidence["available"]
            else "UNAVAILABLE"
        )
        report["junction_incidence_mismatches"] = junction_incidence["mismatches"]
        report["junction_incidence_reason"] = junction_incidence["reason"]
        report["junction_incidence_records"] = junction_incidence["records"]

        repeat_model = pygplates.TopologicalModel(
            topological_features=topological_features,
            rotation_model=rotation_model,
            anchor_plate_id=0,
        )
        repeat_snapshot = repeat_model.topological_snapshot(PYGPLATES_DIAGNOSTIC_EPOCH)
        repeat_boundaries, repeat_networks, repeat_records = _resolved_records(repeat_snapshot, pygplates)
        signature_first = _resolved_signature(resolved_records)
        signature_second = _resolved_signature(repeat_records)
        report["repeatability_sha256"] = signature_first
        report["repeatability"] = (
            signature_first == signature_second
            and [item["plate_id"] for item in repeat_records]
            == [item["plate_id"] for item in resolved_records]
            and len(repeat_boundaries) == len(resolved_boundaries)
            and len(repeat_networks) == len(resolved_networks)
        )

        coverage_ok = all(coverage[key] == 0 for key in (
            "uncovered_cell_centres", "multiply_covered_cell_centres", "wrong_plate_cell_centres"
        ))
        if (
            not report["plate_identity_preserved"]
            or not report["boundary_identity_preserved"]
            or not report["junction_identity_preserved"]
            or not resolved_identity_ok
            or len(resolved_networks) != 0
            or not coverage_ok
            or (junction_incidence["available"] and junction_incidence["mismatches"] != 0)
        ):
            report["decision"] = "STATIC_TOPOLOGY_VALIDATION_FAILED"
            report["status"] = "FAIL"
        elif not junction_incidence["available"]:
            report["decision"] = "JUNCTION_INCIDENCE_VALIDATION_UNAVAILABLE"
            report["status"] = "PARTIAL"
        elif not report["repeatability"]:
            report["decision"] = "STATIC_TOPOLOGY_NOT_REPEATABLE"
            report["status"] = "FAIL"
        else:
            report["decision"] = "STATIC_TOPOLOGY_RESOLUTION_PASS"
            report["status"] = "PASS"
    except Exception as exc:
        report.update({
            "decision": "RESOLVED_TOPOLOGY_VALIDATION_UNAVAILABLE",
            "status": "PARTIAL",
            "validation_error": _error_text(exc),
        })
    return report


def runtime_unavailable_report(data: MappingInput, error: str) -> dict[str, Any]:
    report = _base_report(data)
    report["resolution_error"] = error
    return report
