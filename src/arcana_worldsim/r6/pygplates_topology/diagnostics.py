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
