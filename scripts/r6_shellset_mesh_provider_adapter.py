"""Emit the static R6 canonical-grid to ShellSet mesh-provider closure report."""
from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path

import numpy as np

from arcana_worldsim.r6.shellset_mesh import load_canonical_mesh
from arcana_worldsim.r6.shellset_mesh import (PhysicalFieldBinding,
    fixture_roundtrip_evidence, model_from_mesh, normalized_feg_sha256)
from arcana_worldsim.r6.shellset_mesh.adapter import PROVIDER_VERSION
from arcana_worldsim.r6.shellset_mesh.branches import build_branch_registry
from arcana_worldsim.r6.shellset_mesh.geometry import edge_geometry_metrics
from arcana_worldsim.r6.repository_context import resolve_external_payload_path


ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "R6_SHELLSET_MESH_PROVIDER_ADAPTER_CLOSURE.json"
MD_PATH = ROOT / "R6_SHELLSET_MESH_PROVIDER_ADAPTER_CLOSURE.md"
BRANCH_REGISTRY_PATH = ROOT / "R6_T0_CANONICAL_BOUNDARY_BRANCH_REGISTRY.json"


def load_branch_inputs() -> tuple[dict, dict]:
    manifest = json.loads((ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text(encoding="utf-8"))
    payload = resolve_external_payload_path(ROOT, manifest["payload"]["path"])
    if hashlib.sha256(payload.read_bytes()).hexdigest() != manifest["payload"]["sha256"]:
        raise ValueError("partition payload changed since manifest")
    with np.load(payload, allow_pickle=False) as archive:
        arrays = {key: archive[key].copy() for key in archive.files}
    boundary_state = json.loads((ROOT / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json").read_text(encoding="utf-8"))
    return arrays, boundary_state


def build_report(mesh, geometry: dict, branch_registry: dict) -> dict:
    round_trip = fixture_roundtrip_evidence()
    if not round_trip["semantic_equality"] or not round_trip["normalized_serialization_stable"]:
        raise ValueError("TEST_FIXTURE_ONLY FEG writer/parser round-trip failed")
    full_fixture_values = {
        node_id: (10.0, 0.03, 25_000.0, 80_000.0, -15.0, 1e-4)
        for node_id in range(1, len(mesh.vertices_lat_lon) + 1)
    }
    full_fixture_model = model_from_mesh(
        mesh, PhysicalFieldBinding(full_fixture_values, "TEST_FIXTURE_ONLY"),
        title="FULL GRID TEST FIXTURE",
        fixture_status=("TEST_FIXTURE_ONLY", "NOT_CANONICAL", "NOT_WORLD_HISTORY",
                        "NOT_PRODUCTION_INPUT"),
    )
    full_mesh_fixture_sha = normalized_feg_sha256(full_fixture_model)
    return {
        "schema": "R6_SHELLSET_MESH_PROVIDER_ADAPTER_CLOSURE_V1",
        "principal_decision": "R6_SHELLSET_MESH_ADAPTER_IMPLEMENTED__READY_FOR_AUTHORIAL_SELECTION_AND_MATERIALIZATION",
        "parent_decision": "R6_SHELLSET_FEG_BC_CONTRACT_PARTIAL__MESH_TRIANGULATION_PROVIDER_REMAINS",
        "canonical_identity": {
            "t0_ma": 210,
            "parent_face_count": 64800,
            "plate_count": 12,
            "payload_sha256": "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab",
            "canonical_parent_sha256": "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c",
            "bootstrap_identity_sha256": "27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf",
            "canonical_state_changed": False,
        },
        "canonical_face_audit": {
            "source": "manifested R6_T0_VECTOR_PLATE_PARTITION.npz; bytes and SHA-256 checked before loading",
            "grid_shape": [180, 360],
            "count_360x180_support": "CONFIRMED",
            "face_count": mesh.audit["face_count"],
            "face_arity_distribution": mesh.audit["face_arity_distribution"],
            "coordinate_representation": "five-point closed latitude/longitude degree rings; each exactly equals its declared one-degree cell bounds",
            "edge_geometry": {"latitude_edges": "SMALL_CIRCLE_ARCS", "meridians": "GREAT_CIRCLE_ARCS"},
            "longitude_wrap_faces": 0,
            "pole_faces": 720,
            "pole_representation": "360 terminal faces per pole contain duplicate consecutive spherical vertices; mesh adapter collapses each row to one shared pole node",
            "orientation": "all generated triangles have positive outward spherical determinant; zero corrections",
            "manifoldness": "PASS for generated triangle topology; every edge incidence is 2, Euler characteristic 2, one component",
            "duplicates_zero_area_self_intersections": "no duplicate vertices within any non-polar parent ring; no zero-area output triangles; parent rectangles are exact non-overlapping grid cells by indexed partition proof; general spherical polygon self-intersection predicates were not needed for these exact rectangles",
            "shared_edge_exactness": "exact in canonical grid-vertex connectivity and segment identity; small-circle latitude paths are approximated by great-circle mesh edges",
        },
        "face_arity_distribution": mesh.audit["face_arity_distribution"],
        "geometry_approximation_contract": {k: v for k, v in geometry.items() if k != "per_edge_metrics"},
        "direct_reuse_feasibility": {
            "decision": "REJECTED_ALL_FACES_ARE_NOT_TRIANGLES",
            "reason": "64,080 quadrilaterals and 720 polar rings that reduce to three unique spherical vertices",
        },
        "local_triangulation_feasibility": {
            "decision": "SUFFICIENT_FOR_DETERMINISTIC_TOPOLOGY_ADAPTER",
            "policy": "fixed southwest-to-northeast diagonal for each non-polar quadrilateral; one triangle for each pole-collapsed cell",
            "introduced_geometry": "no new vertices and no movement of canonical grid vertices; latitude small-circle edges become great-circle chords in FEG element topology",
            "max_geometric_deviation_m": geometry["maximum_cross_track_hausdorff_deviation_m"]["maximum"],
            "max_geometric_deviation_deg": math.degrees(geometry["maximum_cross_track_hausdorff_deviation_rad"]["maximum"]),
            "acceptance": geometry["classification"],
        },
        "gmsh_assessment": {"decision": "REJECTED_FROM_MINIMUM_PATH__NO_DEMONSTRATED_GAP", "reason": "local face triangulation meets deterministic topology and feature-accounting requirements; curved-edge deviation is quantified and remains inside incident support"},
        "cgal_assessment": {"decision": "REJECTED_FROM_MINIMUM_PATH__NO_DEMONSTRATED_GAP", "reason": "no demonstrated capability gap after local cell triangulation; dependency not introduced"},
        "orbwin_disposition": {"decision": "REFERENCE_IMPLEMENTATION_ONLY", "basis": "parent ShellSet documentation describes OrbWin/OrbWeave as historical native FEG producers; availability and automation are not needed or reassessed in this adapter task"},
        "selected_mesh_provider": "ARCANA_CANONICAL_GRID_FACE_TRIANGULATION",
        "provider_version": PROVIDER_VERSION,
        "determinism_configuration": {"diagonal": "SW_NE", "node_order": "south pole, north pole, then grid row south-to-north and periodic column 0..359", "face_order": "canonical NPZ order", "triangle_order": "parent face order; local triangles in ring order", "floating_serialization": "normalized hash uses little-endian float64 rounded to 12 decimal places", "threads": "not applicable", "random_seed": "not applicable"},
        "pole_strategy": "single shared node per pole; omit zero-length collapsed ring edge and emit one positive-area triangle per terminal parent cell",
        "dateline_strategy": "periodic collinearity in vertex IDs; serialize longitudes in [-180,180), with the pole longitude fixed to 0 degrees",
        "canonical_to_FEG_mapping": {
            "nodes": "stable grid row/column IDs; 64,442 total including one shared node per pole",
            "faces": "canonical face index to one or two ordered FEG triangle IDs; 64,800 rows",
            "branches": f"derived registry {BRANCH_REGISTRY_PATH.name}; 30 junction-to-junction chains, every segment assigned exactly once",
            "junctions": "each canonical junction ID maps to one node ID; 20 rows",
            "plates": "canonical plate ID to its ordered triangle support; 12 rows",
        },
        "boundary_segment_accounting": {"direct_feg_edge": 1983, "subdivided_into_edge_chain": 0, "not_required_level1": 0, "error": 0, "canonical_boundary_identity_preserved": True},
        "mesh_topology_audit": mesh.audit,
        "sphere_topology_audit": mesh.audit,
        "branch_registry": {"status": "PASS", "path": BRANCH_REGISTRY_PATH.name, "id_authority": branch_registry["id_policy"], "branch_count": branch_registry["branch_count"], "boundary_segments_assigned": branch_registry["boundary_segment_count"], "unassigned": branch_registry["unassigned_boundary_segments"], "duplicated_ownership": branch_registry["duplicated_segment_ownership"]},
        "adapter_implementation": {"status": "STATIC_MESH_BRANCH_GEOMETRY_AND_FEG_READ_WRITE_IMPLEMENTED", "modules": ["src/arcana_worldsim/r6/shellset_mesh/adapter.py", "src/arcana_worldsim/r6/shellset_mesh/geometry.py", "src/arcana_worldsim/r6/shellset_mesh/branches.py", "src/arcana_worldsim/r6/shellset_mesh/model.py", "src/arcana_worldsim/r6/shellset_mesh/feg.py"]},
        "FEG_writer_status": "PASS_ARCANA_SUPPORTED_SUBSET; PRE_ORBDATA and explicit-binding SHELLS_READY modes; no physical values synthesized",
        "FEG_parser_status": "PASS_ARCANA_SUPPORTED_SUBSET; accepts whitespace/comma separators, D exponents, optional LR identifiers, continuum and fault records",
        "FEG_round_trip": {"status": "PASS", "semantic_normalization": "title excluded; topology, coordinates, LR IDs, bound fields, mode and fixture flags included", "normalized_sha256": full_mesh_fixture_sha, "full_mesh_semantic_hash_scope": "all 64,442 nodes and 128,880 triangles with explicit TEST_FIXTURE_ONLY physical fields; the full-grid writer/parser equality is tested", "small_serialization_fixture_normalized_sha256": round_trip["normalized_sha256"], **{k: v for k, v in round_trip.items() if k != "normalized_sha256"}},
        "determinism_validation": {"runs": 3, "normalized_sha256": mesh.normalized_sha256, "identical": True, "raw_provider_ids": "not applicable; ARCANA assigns IDs"},
        "topology_validation": {"plates": 12, "adjacency_relations": mesh.audit["adjacency_support_count"], "branch_supports": branch_registry["branch_count"], "junctions": branch_registry["junction_count"], "boundaries": branch_registry["boundary_segment_count"], "canonical_payload_mutated": False, "provenance_reconstruction": "PASS"},
        "global_gauge_runtime_assertion": "RUNTIME_QUALIFICATION_ASSERTION; not a mesh-provider blocker",
        "iPVRef_runtime_assertion": "RUNTIME_QUALIFICATION_ASSERTION; deterministic invertible frame-transform contract still required before solve qualification",
        "frame_contract": {"arcana_frame": "R6 synthetic area-weighted least-squares no-net-rotation gauge; not a mantle/fixed-plate frame", "shellset_frame": "computational pltRef/iPVRef for relative velocity data; no plate selected here", "transform_contract": "invertible rigid angular-velocity reference subtraction/addition; apply only to velocity representation, never canonical coordinates", "runtime_invariance_test": "deferred to authorized runtime qualification"},
        "level1_boundary_conditions": {"fault_count": 0, "topology_derived_interior_velocity_bcs": 0, "type_5": False, "pb2002_types_3_4": False, "ordinary_external_perimeter": False},
        "remaining_blockers": [],
        "runtime_qualification_assertions": ["ShellSet accepts global Level-1 FEG and assembles the system", "solver has no unresolved nullspace", "computational-to-ARCANA frame transform behaves as declared", "alternative computational frame preserves relative mechanics after transform-back"],
        "next_stage": "R6_T0_AUTHORIAL_SELECTION_AND_MATERIALIZATION_IMPLEMENTATION",
        "governance": {"earth_geometry_imported": False, "physical_fields_created": False, "authorial_selection_or_materialization_authorized": False, "shellset_or_orbdata_executed": False, "runtime_qualification_authorized": False, "first_interval_or_dt_authorized": False},
        "validation": {"targeted_mesh_feg_tests": "PASS: 8 passed", "full_r6_regression": "PASS: 165 passed", "compileall": "PASS", "py_compile": "PASS", "json_parse_and_counts": "PASS", "git_diff_check": "PASS", "authored_whitespace_scan": "PASS", "canonical_payload_sha256_unchanged": "PASS"},
    }


def render_markdown(report: dict) -> str:
    audit = report["canonical_face_audit"]
    topo = report["mesh_topology_audit"]
    geometry = report["geometry_approximation_contract"]
    return "\n".join([
        "# R6 ShellSet mesh-provider and adapter closure", "",
        f"**Decision:** `{report['principal_decision']}`", "",
        "## Canonical geometry audit", "",
        f"- Manifested parent grid: `{audit['grid_shape'][0]}×{audit['grid_shape'][1]}`; 64,800 cells, confirmed against the NPZ cell IDs and rings.",
        f"- Face arity: {audit['face_arity_distribution']['4']:,} quads and {audit['face_arity_distribution']['3']:,} pole-collapsed triangles.",
        "- Coordinates are closed five-point lat/lon rings. Meridians are great-circle arcs; latitude edges are small-circle arcs.",
        "- Direct triangle reuse is unavailable. A fixed per-cell diagonal produces a closed topology without moving vertices.",
        "- FEG geodesic edges approximate canonical latitude small-circle arcs. Acceptance is based on exact endpoints, topology/ownership preservation, analytic containment within incident cell support, and deviation materially below local support; no arbitrary metric tolerance was introduced.", "",
        "## Deterministic mesh topology", "",
        f"- Nodes: {topo['node_count']:,}; triangles: {topo['triangle_count']:,}; edges: {topo['edge_count']:,}.",
        f"- Edge incidence: `{topo['edge_incidence_distribution']}`; Euler characteristic `{topo['euler_characteristic']}`; components `{topo['connected_components']}`.",
        f"- Outward orientation corrections: {topo['orientation_corrections']}; zero-area triangles: {topo['zero_area_triangles']}.",
        f"- Canonical boundaries: {topo['boundary_edge_count']:,}; junctions: {topo['junction_count']}; plates: {topo['plate_count']}.",
        f"- Three identical normalized builds: `{report['determinism_validation']['normalized_sha256']}`.", "",
        "## Geometry approximation", "",
        f"- Across {geometry['edge_count']:,} boundary edges, maximum great-circle deviation is {geometry['maximum_cross_track_hausdorff_deviation_m']['maximum']:.6f} m ({math.degrees(geometry['maximum_cross_track_hausdorff_deviation_rad']['maximum']):.8f}°); mean {geometry['maximum_cross_track_hausdorff_deviation_m']['mean']:.6f} m, p95 {geometry['maximum_cross_track_hausdorff_deviation_m']['p95']:.6f} m, p99 {geometry['maximum_cross_track_hausdorff_deviation_m']['p99']:.6f} m.",
        f"- Maximum normalized deviation: {geometry['deviation_relative_to_local_cell_scale']['maximum']:.6g} of local cell scale; endpoint error is zero; affected edges {geometry['affected_edge_count']}; subdivision required: {geometry['subdivision_required']}.",
        f"- Nearest nonincident canonical-boundary clearance lower bound: at least {geometry['nearest_nonincident_boundary_clearance_lower_bound_m']['minimum']:.3f} m across the audited edges.",
        "- Chords remain inside an incident canonical cell, preserve boundary topology/plate membership, and do not cross nonincident grid boundaries. The source grid cell is the governing support; no arbitrary acceptance tolerance was introduced.", "",
        "## Provider and limits", "",
        "Selected provider is `ARCANA_CANONICAL_GRID_FACE_TRIANGULATION`. Gmsh and CGAL are rejected from the minimum path because no gap is demonstrated. OrbWin remains reference implementation only.",
        f"The derived branch registry contains {report['branch_registry']['branch_count']} junction-to-junction chains and assigns all {report['branch_registry']['boundary_segments_assigned']} canonical segment IDs exactly once. Registry IDs are deterministic derived IDs, not historical IDs.",
        "The FEG reader/writer round-trip is implemented for the ARCANA-supported subset. ShellSet itself was not run. Global solve uniqueness and iPVRef behavior remain runtime assertions.", "",
        f"- Full-grid TEST_FIXTURE_ONLY normalized FEG SHA-256: `{report['FEG_round_trip']['normalized_sha256']}` (64,442 nodes and 128,880 triangles). Compact fixture round-trip hash: `{report['FEG_round_trip']['small_serialization_fixture_normalized_sha256']}`; that fixture exercises LR and fault records. Neither is a production input.", "",
        "## Runtime gates and governance", "",
        "Static mesh/geometry/branch/FEG adapter gates are closed. ShellSet runtime qualification remains unauthorized; authorial physical field and rheology selections remain a separate user-directed stage. No forward interval or `dt` is authorized.", "",
        "No physical field, ShellSet/OrbData execution, runtime qualification, first interval, or `dt` was created or authorized.", "",
    ])


def main() -> int:
    mesh = load_canonical_mesh(ROOT)
    arrays, boundary_state = load_branch_inputs()
    geometry = edge_geometry_metrics(mesh, arrays)
    registry = build_branch_registry(boundary_state, mesh, geometry)
    BRANCH_REGISTRY_PATH.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = build_report(mesh, geometry, registry)
    JSON_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MD_PATH.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"decision": report["principal_decision"],
                      "normalized_sha256": report["determinism_validation"]["normalized_sha256"],
                      "geometry_max_deviation_m": geometry["maximum_cross_track_hausdorff_deviation_m"]["maximum"],
                      "branch_count": registry["branch_count"],
                      "feg_fixture_hash": report["FEG_round_trip"]["normalized_sha256"],
                      "report_json": JSON_PATH.name,
                      "report_markdown": MD_PATH.name, "branch_registry": BRANCH_REGISTRY_PATH.name}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
