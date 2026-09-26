"""Noncanonical PASS/FAIL report generation for P2 mapping diagnostics."""
from __future__ import annotations

from collections import Counter
from typing import Any

from .contracts import governance_flags

ARTIFACT = "R6_PYGPLATES_CANONICAL_MAPPING_REPORT"


def build_report(data: Any, pygplates_version: str | None, geometry: dict[str, Any] | None,
                 runtime_error: str | None = None) -> dict[str, Any]:
    arrays = data.arrays
    inventory = data.inventory
    constructed = geometry is not None
    if constructed:
        plates = geometry["rigid_cell_features_by_plate"]
        cell_feature_count = sum(len(features) for features in plates.values())
        boundary_feature_count = len(geometry["boundary_support_features"])
        junction_feature_count = len(geometry["junction_point_features"])
    else:
        plates = {}
        cell_feature_count = boundary_feature_count = junction_feature_count = None

    pair_counts = Counter(
        (int(a), int(b)) for a, b in zip(arrays["boundary_plate_a"], arrays["boundary_plate_b"])
    )
    runtime_available = pygplates_version is not None
    rigid_supported = (
        cell_feature_count == inventory["face_count"]
        if constructed
        else None if not runtime_available else False
    )
    return {
        "artifact": ARTIFACT,
        "classification": "NONCANONICAL_FEASIBILITY_DIAGNOSTIC",
        "status": "PASS" if constructed and runtime_error is None else "FAIL",
        "decision": "PYGPLATES_MAPPING_DIAGNOSTIC_COMPLETE" if constructed and runtime_error is None else (
            "PYGPLATES_RUNTIME_UNAVAILABLE" if not runtime_available else "PYGPLATES_GEOMETRY_CANDIDATE_CONSTRUCTION_FAILED"
        ),
        "pygplates_version": pygplates_version,
        "pygplates_runtime_available": runtime_available,
        "runtime_error": runtime_error,
        "canonical_source": {
            "schema": data.manifest["schema"],
            "time_ma": data.manifest["time_ma"],
            "payload_sha256": data.manifest["payload"]["sha256"],
            "payload_bytes": data.manifest["payload"]["bytes"],
        },
        "arcana_plates": inventory["plate_count"],
        "canonical_faces": inventory["face_count"],
        "boundary_segments": inventory["boundary_segment_count"],
        "boundary_plate_pair_count": len(pair_counts),
        "junctions": inventory["junction_count"],
        "canonical_state_changed": False,
        "forward_evolution": False,
        "dt_first_authorized": False,
        "w_model_selected": False,
        "rift_advanced": False,
        "pygplates_scientific_authority": False,
        "all_finite": True,
        "mapping": {
            "rigid_blocks_supported": rigid_supported,
            "rigid_plate_count_represented": len(plates) if constructed else None,
            "rigid_cell_polygon_count": cell_feature_count,
            "deforming_region_supported": constructed if runtime_available else None,
            "deforming_region_support_basis": "SYNTHETIC_P1_CAPABILITY_ONLY; no canonical regions assigned",
            "canonical_deforming_region_assignment": "UNBOUND",
            "canonical_deforming_region_count": 0,
            "boundary_support_geometry_count": boundary_feature_count,
            "unresolved_boundary_count": inventory["boundary_segment_count"],
            "unresolved_boundary_semantics": "UNBOUND; no convergence/divergence law or geological boundary class assigned",
            "junction_point_geometry_count": junction_feature_count,
            "unresolved_junction_count": inventory["junction_count"],
            "unresolved_junction_semantics": "UNBOUND; no junction velocity, topology change, or residual allocation assigned",
            "exact_curve_semantics_adjudication": "UNBOUND; no geometry loss tolerance specified",
            "pygplates_topology_resolution_executed": False,
        },
        "boundary_plate_pair_counts": [
            {"plate_a": a, "plate_b": b, "edge_count": count}
            for (a, b), count in sorted(pair_counts.items())
        ],
        "junction_records": [
            {
                "junction_id": record["junction_id"],
                "vertex_id": record["vertex_id"],
                "incident_plate_ids": record["incident_plate_ids"],
                "degree": record["degree"],
                "semantics": "UNBOUND",
            }
            for record in data.junction_census["junctions"]
        ],
        "governance": governance_flags(),
    }


def render_markdown(report: dict[str, Any]) -> str:
    mapping = report["mapping"]
    return "\n".join([
        "# R6 pyGPlates canonical mapping diagnostic",
        "",
        f"- Status: **{report['status']}**",
        f"- Decision: `{report['decision']}`",
        f"- Classification: `{report['classification']}`",
        f"- pyGPlates version: `{report['pygplates_version'] or 'UNAVAILABLE'}`",
        f"- Runtime detail: `{report['runtime_error'] or 'none'}`",
        f"- Canonical t0: {report['canonical_source']['time_ma']} Ma; payload SHA-256 `{report['canonical_source']['payload_sha256']}`",
        "",
        "## Inventory and representability",
        "",
        f"- ARCANA plates: {report['arcana_plates']}; canonical faces: {report['canonical_faces']}",
        f"- Boundary segments: {report['boundary_segments']}; boundary plate pairs: {report['boundary_plate_pair_count']}",
        f"- Junctions: {report['junctions']}",
        f"- Rigid polygon candidates: {mapping['rigid_cell_polygon_count']}; represented plate groups: {mapping['rigid_plate_count_represented']}",
        f"- Rigid blocks supported: `{mapping['rigid_blocks_supported']}`",
        f"- Deforming-network API supported: `{mapping['deforming_region_supported']}`; canonical region assignment: `{mapping['canonical_deforming_region_assignment']}`",
        f"- Boundary support geometries: {mapping['boundary_support_geometry_count']}; unresolved boundary semantics: {mapping['unresolved_boundary_count']}",
        f"- Junction point geometries: {mapping['junction_point_geometry_count']}; unresolved junction semantics: {mapping['unresolved_junction_count']}",
        f"- Exact curve semantics: `{mapping['exact_curve_semantics_adjudication']}`",
        "",
        "The adapter constructs geometry candidates only. It does not resolve topologies or assign motion, boundary process, strain semantics, or junction behavior. A `PASS` means this diagnostic completed; it is not a solver-selection or scientific-authority decision.",
        "",
        "Canonical state unchanged; forward evolution, dt authorization, W_model selection, and rift advancement remain false.",
        "",
    ])
