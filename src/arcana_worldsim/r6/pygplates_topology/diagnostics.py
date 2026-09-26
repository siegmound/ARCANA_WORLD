"""Report rendering for the P2.2 topology assembly probe."""
from __future__ import annotations

from typing import Any

from .adapter import identity_digest
from .contracts import governance_flags


def runtime_unavailable_report(data: Any, error: str) -> dict[str, Any]:
    repeatability = identity_digest(data)
    return {
        "artifact": "R6_PYGPLATES_TOPOLOGY_ASSEMBLY_PROBE",
        "classification": "NONCANONICAL_COMPATIBILITY_DIAGNOSTIC",
        "status": "FAIL",
        "decision": "PYGPLATES_RUNTIME_UNAVAILABLE",
        "failure_class": "PYGPLATES_RUNTIME_UNAVAILABLE",
        "pygplates_version": None,
        "runtime_error": error,
        "input_counts": data.inventory,
        "geometry_counts": None,
        "network_created": False,
        "resolved_created": False,
        "plate_identity_preserved": None,
        "boundary_identity_preserved": None,
        "junction_identity_preserved": None,
        "repeatability_sha256": repeatability,
        "gates": {
            "NETWORK_CREATED": False,
            "RESOLUTION_CREATED": False,
            "PLATE_IDENTITY_PRESERVED": None,
            "BOUNDARY_COUNT_PRESERVED": None,
            "JUNCTION_COUNT_PRESERVED": None,
            "REPEATABLE": True,
        },
        "governance": governance_flags(),
    }


def render_markdown(report: dict[str, Any]) -> str:
    counts = report["input_counts"]
    return "\n".join([
        "# R6 pyGPlates canonical topology assembly probe",
        "",
        f"- Status: **{report['status']}**",
        f"- Decision: `{report['decision']}`",
        f"- Failure class: `{report.get('failure_class') or 'none'}`",
        f"- pyGPlates: `{report.get('pygplates_version') or 'unavailable'}`",
        f"- Input: {counts['plate_count']} plates, {counts['face_count']} canonical cells, {counts['boundary_segment_count']} boundary segments, {counts['junction_count']} junctions",
        f"- Network created: `{report.get('network_created')}`; resolved snapshot: `{report.get('resolved_created')}`",
        f"- Resolution status: `{report.get('resolution_status', 'not run')}`",
        f"- Identity gates: plate `{report.get('plate_identity_preserved')}`, boundary `{report.get('boundary_identity_preserved')}`, junction `{report.get('junction_identity_preserved')}`",
        f"- Repeatability SHA-256: `{report.get('repeatability_sha256') or 'unavailable'}`",
        f"- Runtime detail: `{report.get('runtime_error') or 'none'}`",
        "",
        "This is a noncanonical compatibility diagnostic. It assigns no rotations, velocity, strain, W_model, dt, or forward evolution.",
        "",
    ])


def render_static_topology_markdown(report: dict[str, Any]) -> str:
    coverage = report["coverage"]
    lines = [
        "# R6 pyGPlates static canonical topology resolution",
        "",
        f"- Status: **{report['status']}**",
        f"- Decision: `{report['decision']}`",
        f"- pyGPlates: `{report.get('pygplates_version') or 'unavailable'}`",
        f"- ARCANA t0: {report['arcana_time_ma']} Ma; diagnostic epoch: {report['pygplates_diagnostic_epoch']}",
        f"- Topological polygons: {report['topological_polygon_features_created']} / {report['topological_polygon_features_expected']}",
        f"- Shared boundaries: {report['boundary_support_features']}; unique identities: {report['unique_boundary_identities']}",
        f"- Resolved boundaries: {report['resolved_topological_boundaries']}; networks: {report['resolved_topological_networks']}",
        f"- Empty rotation model: `{report['empty_rotation_model_used']}`; rotations assigned: `{report['rotations_assigned']}`",
        f"- Resolution attempted/succeeded: `{report['resolution_attempted']}` / `{report['resolution_succeeded']}`",
        f"- Resolution error: `{report['resolution_error'] or 'none'}`",
        f"- Identity preserved (plate/boundary/junction): `{report['plate_identity_preserved']}` / `{report['boundary_identity_preserved']}` / `{report['junction_identity_preserved']}`",
        f"- Junction incidence validation: `{report['junction_incidence_validation']}`; mismatches: `{report['junction_incidence_mismatches']}`",
        f"- Cell centres tested: {coverage['cell_centres_tested']}; uncovered: {coverage['uncovered_cell_centres']}; multiple: {coverage['multiply_covered_cell_centres']}; wrong plate: {coverage['wrong_plate_cell_centres']}",
        f"- Repeatability: `{report['repeatability']}`; SHA-256 `{report['repeatability_sha256']}`",
        f"- Exact curve semantics: `{report['exact_curve_semantics']}`",
        "",
        "This report is a noncanonical diagnostic. It does not assign motion or alter R6 scientific state.",
        "",
    ]
    return "\n".join(lines)
