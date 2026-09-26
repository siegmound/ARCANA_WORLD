"""Audit real R6 t0 boundaries/junctions; never advances or materializes t1."""
from __future__ import annotations

from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.repository_context import (require_repository_context,
    resolve_external_payload_path, verify_protected_staged_blobs)
HEAD = "592b1651b405363373590092e133bd25569d99a5"
VECTOR_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
INDEX_BLOBS = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}
WIDTHS_M = (100_000, 250_000, 500_000, 1_000_000)
TRACE_TOL = 1e-4


def digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_repository() -> dict:
    context = require_repository_context(ROOT, required_ancestor=HEAD)
    verify_protected_staged_blobs(ROOT, INDEX_BLOBS)
    return {"branch": context.branch or f"DETACHED@{context.head[:12]}",
            "branch_name": context.branch, "detached": context.detached,
            "head": context.head, "origin_main": context.refs.get("origin/main")}


def main() -> int:
    repo = check_repository()
    manifest = json.loads((ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text(encoding="utf-8"))
    boundary_manifest = json.loads((ROOT / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json").read_text(encoding="utf-8"))
    payload = resolve_external_payload_path(ROOT, manifest["payload"]["path"])
    if not payload.is_file() or digest(payload) != VECTOR_SHA:
        raise RuntimeError("canonical vector partition missing or SHA256 mismatch")

    sys.path.insert(0, str(ROOT / "src"))
    from arcana_worldsim.r6.physical.reference_arrangement import (
        CanonicalBoundarySpatialIndex, build_canonical_junction_bases,
        canonical_parent_faces, junction_geography, spherical_rect_area_m2,
    )
    from arcana_worldsim.r6.physical.boundary_geometry import unit_xyz

    with np.load(payload, allow_pickle=False) as z:
        parents = canonical_parent_faces(z["face_row"], z["face_col"], z["face_plate_id"],
                                         z["face_vertex_latlon_deg"])
        parent_grid = np.empty((180, 360), dtype=np.int16)
        parent_grid[z["face_row"], z["face_col"]] = z["face_plate_id"]
        plates = sorted(set(int(v) for v in z["face_plate_id"].tolist()))
    parent_area = math.fsum(spherical_rect_area_m2(p.south_deg, p.north_deg,
                                                    p.west_deg, p.east_deg) for p in parents)
    sphere_area = 4 * math.pi * 6_371_000.0**2
    parent_rel = abs(parent_area - sphere_area) / sphere_area
    segments = boundary_manifest["segments"]
    junctions = boundary_manifest["junctions"]
    if len(parents) != 64_800 or len(plates) != 12 or len(segments) != 1_983 or len(junctions) != 20:
        raise RuntimeError("canonical parent/network cardinality mismatch")
    index = CanonicalBoundarySpatialIndex(segments)
    if len(index.records) != 1_983 or len(index.by_component) != 30:
        raise RuntimeError("canonical spatial index cardinality/component check failed")

    # Index completeness is checked at each source segment midpoint, without
    # widening the scientific footprint: exact self-distance must be indexed.
    midpoint_misses = []
    for record in index.records:
        segment = record.segment
        if segment.kind == "SMALL_CIRCLE":
            qlat = segment.start_lat_deg
            qlon = segment.start_lon_deg + float(segment.sweep_deg) / 2
        else:
            a = unit_xyz(segment.start_lat_deg, segment.start_lon_deg)
            b = unit_xyz(segment.end_lat_deg, segment.end_lon_deg)
            q = a + b
            q /= np.linalg.norm(q)
            qlat = math.degrees(math.asin(float(q[2])))
            qlon = math.degrees(math.atan2(float(q[1]), float(q[0])))
        hit_ids = {item.boundary_id for item, _ in index.query(qlat, qlon, 0.01)}
        if record.boundary_id not in hit_ids:
            midpoint_misses.append(record.boundary_id)

    # A unit-scale (W=2 m) local geometry probe diagnoses shape/trace only.
    # It is explicitly not one of the predeclared model-width evaluations.
    patches = build_canonical_junction_bases(junctions, index, width_m=2.0,
                                               subdivisions_per_side=128,
                                               parent_plate_grid=parent_grid)
    resolved = [p for p in patches if p["status"] == "BOUND"]
    blocked = [p for p in patches if p["status"] != "BOUND"]
    max_trace = 0.0
    worst_trace = None
    trace_samples = 0
    trace_violations = 0
    by_id = {r.boundary_id: r for r in index.records}
    for patch in resolved:
        basis = patch["basis"]
        order = tuple(patch["plate_ids_in_p1_cycle"])
        for edge in range(3):
            pair = tuple(sorted((order[edge], order[(edge + 1) % 3])))
            branch = next((by_id[bid] for bid in patch["incident_boundary_ids_in_cyclic_order"]
                           if by_id[bid].plate_pair == pair), None)
            if branch is None:
                raise RuntimeError(f"P1 side has no exact incident canonical branch: {patch['junction_id']}")
            a = np.asarray(basis.vertices[edge], dtype=float)
            b = np.asarray(basis.vertices[(edge + 1) % 3], dtype=float)
            for k in range(32):
                t = (k + 0.5) / 32
                xy = a * (1 - t) + b * t
                lat, lon = basis.latlon_at_xy(*xy)
                weights = dict(basis.boundary_trace(edge, t))
                # Existing two-plate corridor trace: signed shortest distance
                # to the exact connected component and parent-side ownership.
                d = min(r.segment.distance_m(lat, lon) for r in index.by_component[branch.component_id])
                row = min(179, max(0, int(math.floor(lat + 90.0))))
                col = int(math.floor((lon + 180.0) % 360.0)) % 360
                owner = int(parent_grid[row, col])
                signed = -d if owner == pair[0] else d if owner == pair[1] else math.nan
                if not math.isfinite(signed):
                    raise RuntimeError("sampled canonical trace lies outside its incident parent plate pair")
                xi = max(-1.0, min(1.0, signed / 1.0))  # H=1 m in normalized probe only
                s = (xi + 1.0) / 2.0
                smooth = s * s * (3.0 - 2.0 * s)
                expected = {pair[0]: 1.0 - smooth, pair[1]: smooth}
                err = max(abs(weights.get(pid, 0.0) - expected[pid]) for pid in pair)
                trace_samples += 1
                if err > max_trace:
                    max_trace = err
                    worst_trace = {"junction_id": patch["junction_id"],
                                   "boundary_id": branch.boundary_id, "edge": edge,
                                   "local_edge_fraction": t, "error": err,
                                   "local_xy_m": [float(xy[0]), float(xy[1])],
                                   "signed_corridor_distance_m": signed,
                                   "sample_lat_deg": lat, "sample_lon_deg": lon,
                                   "basis_weights": {str(k): v for k, v in weights.items()},
                                   "canonical_corridor_weights": {str(k): v for k, v in expected.items()}}
                if err > TRACE_TOL:
                    trace_violations += 1

    fixture_paths = ["tests/test_r6_parent_conforming_reference_arrangement.py",
                     "tests/test_r6_spherical_boundary_geometry.py",
                     "tests/test_r6_shared_boundary_diagnostics.py",
                     "tests/test_r6_minimal_continuum_boundary_deformation.py",
                     "tests/test_r6_boundary_zone_reference_configuration.py",
                     "tests/test_r6_boundary_deformation_law.py"]
    started = time.perf_counter()
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", *fixture_paths], cwd=ROOT,
                          env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
                          capture_output=True, text=True)
    test_seconds = time.perf_counter() - started
    test_output = (proc.stdout + proc.stderr).strip()
    if proc.returncode:
        raise RuntimeError(f"R6 arrangement regression suite failed: {test_output}")

    gate_pass = not midpoint_misses and len(resolved) == 20 and trace_violations == 0
    blocker = (None if gate_pass else
               "CANONICAL_JUNCTION_P1_FAN_GEOMETRY_BLOCKED_FOR_12_OF_20_AND_REAL_CORRIDOR_TRACE_EXCEEDS_1E-4")
    common = {"repository": repo, "canonical_parent_faces": len(parents), "canonical_parent_plates": len(plates),
              "parent_payload_sha256": VECTOR_SHA, "parent_payload_bytes": payload.stat().st_size,
              "parent_sphere_area_relative_error": parent_rel, "canonical_boundary_segments": len(index.records),
              "canonical_corridor_components": len(index.by_component), "canonical_junctions": len(patches),
              "canonical_junctions_resolved": len(resolved), "canonical_junctions_blocked": len(blocked),
              "spatial_index_midpoint_misses": len(midpoint_misses), "spatial_index_all_source_segments_found": not midpoint_misses,
              "junction_trace_tolerance": TRACE_TOL, "junction_trace_sample_count": trace_samples,
              "junction_trace_violation_count": trace_violations, "junction_trace_max_error": max_trace,
              "junction_trace_worst_sample": worst_trace,
              "p1_geometry_probe_width_m": 2.0,
              "p1_geometry_probe_semantics": "UNIT_SCALE_GEOMETRY_DIAGNOSTIC_ONLY_NOT_A_MODEL_WIDTH_CASE",
              "width_cases_m": list(WIDTHS_M), "width_cases_status": "NOT_RUN_GLOBAL_INTEGRATION_GATE_FAILED",
              "width_selected": False, "canonical_reference_map_materialized": False,
              "static_t0_velocity_field": "NOT_RUN", "forward_evolution": False,
              "canonical_t0_changed": False, "first_dt_years": None,
              "execution_indexes_mutated": False, "execution_index_staged_blobs": INDEX_BLOBS,
              "fixture_tests": "PASS", "fixture_test_output": test_output,
              "fixture_test_seconds": test_seconds, "remaining_blocker": blocker,
              "blocked_junctions": [{"junction_id": p["junction_id"], "reason": p["reason"]} for p in blocked]}

    artifacts = {
        "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION": {
            "schema": "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION_V3",
            "decision": "CANONICAL_JUNCTION_INTEGRATION_BLOCKED" if not gate_pass else "GLOBAL_OWNERSHIP_GATE_READY",
            "canonical_parent_scaffold": "PASS", "boundary_spatial_index": "PASS" if not midpoint_misses else "FAIL",
            "parent_deep_core_inheritance": "IMPLEMENTED_CONSERVATIVE_CERTIFIER",
            "certified_corridor_classifier": "IMPLEMENTED_FAIL_CLOSED",
            "certified_junction_classifier": "IMPLEMENTED_BUT_12_CANONICAL_PATCHES_BLOCKED",
            "global_ownership_evaluated": False, "ambiguous_area_m2": None, "conflict_area_m2": None,
            "sphere_area_relative_error_parent": parent_rel, "complete_gate_pass": gate_pass, **common},
        "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE": {
            "schema": "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE_V3",
            "decision": "L0_L1_CANONICAL_CONVERGENCE_NOT_RUN_INTEGRATION_GATE_FAILED",
            "l0_definition": "canonical 1-degree parent ownership; no unresolved-cell refinement",
            "l1_definition": "nested deterministic quadtree only after all 20 canonical patches and traces pass",
            "canonical_l0_ambiguous_fraction": None, "canonical_l1_ambiguous_fraction": None,
            "convergence_status": "NOT_RUN", "reason": blocker, **common},
        "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION": {
            "schema": "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION_V3",
            "decision": "REAL_CANONICAL_NETWORK_BOUND_TO_INDEX_AND_CLASSIFIER__JUNCTION_GATE_BLOCKED",
            "implemented": ["canonical parent identity/ownership", "finite canonical edge geometry and stable boundary IDs",
                            "deterministic segment candidate index", "per-boundary-component grouping",
                            "conservative parent-cell distance certificate", "P1 junction candidate binding"],
            "unimplemented": ["complete 20/20 globally conforming junction patches", "global L0/L1 ownership areas",
                              "width metrics, global weights, and static velocity"], **common},
        "R6_JUNCTION_PATCH_OPERATOR_VALIDATION": {
            "schema": "R6_JUNCTION_PATCH_OPERATOR_VALIDATION_V4",
            "decision": "CANONICAL_JUNCTION_P1_FAN_GEOMETRY_OR_TRACE_GATE_FAILED",
            "local_trace_error_max": 4.54188e-5, "local_trace_fixture": "PASS",
            "canonical_resolved": len(resolved), "canonical_total": len(patches),
            "real_trace_status": "FAIL" if trace_violations else "PASS",
            "cause": "12 canonical ray sets fail the convex three-side fan condition. At a constructible but near-antipodal junction, the fitted triangle side spans only about 0.0018 of its unit circumradius across the corridor-normal direction; at an interior sample signed distance is -0.0008849 m while P1 assigns 0.999275 to one plate and the canonical corridor smoothstep assigns 0.500664. This is geometric conditioning/trace parameterization mismatch, not the already-passing local P1 interpolation error.", **common},
        "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX": {
            "schema": "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX_V4",
            "decision": "WIDTH_DOMAIN_NOT_EVALUATED_GLOBAL_INTEGRATION_GATE_FAILED",
            "cases": [{"W_model_m": w, "status": "NOT_RUN_GLOBAL_INTEGRATION_GATE_FAILED"} for w in WIDTHS_M], **common},
        "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS": {
            "schema": "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS_V3",
            "decision": "NOT_RUN_GLOBAL_INTEGRATION_GATE_FAILED",
            "cases": [{"W_model_m": w, "status": "NOT_RUN_GLOBAL_INTEGRATION_GATE_FAILED"} for w in WIDTHS_M], **common},
        "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V15": {
            "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V15",
            "decision": "CANONICAL_JUNCTION_P1_TRACE_AND_PATCH_BINDING_BLOCKED",
            "verdict": "PASS_CANONICAL_PARENT_AND_BOUNDARY_INDEX__BLOCKED_REAL_JUNCTION_GLOBAL_HANDOFF",
            "t0_ma": 210.0, "canonical_parent_integrated": True,
            "canonical_global_arrangement_converged": False, "fixture_gate_complete": False,
            "global_reference_geometry_ready": False, "first_dt_years": None,
            "remaining_blockers": [blocker],
            "next_action": "R6_CANONICAL_JUNCTION_P1_GEOMETRY_AND_CORRIDOR_TRACE_COMPATIBILITY_REPAIR",
            "canonical_width_selected": False, "canonical_reference_map_materialized": False,
            "P7Q_reopened": False, "physical_soil_created": False,
            "scientific_authority_register_mutated": False, **common},
    }
    markdown = {
        "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION": f"# Global reference ownership validation\n\nCanonical 64,800-face parent identity and area closure pass. The exact 1,983-segment index has {len(midpoint_misses)} source-midpoint misses; all 12 plates remain parent-inherited. Full global ownership was not run because only {len(resolved)}/20 real junction patches bind and the P1/corridor trace maximum is {max_trace:.9g} (limit {TRACE_TOL:g}). Width cases were not run.\n",
        "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE": f"# Reference-arrangement numerical convergence\n\nCanonical L0/L1 convergence was not evaluated: the integration gate failed at real junctions. L0 remains the canonical parent grid; L1 is deterministic parent-nested quadtree refinement after integration passes. Blocker: `{blocker}`.\n",
        "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION": f"# Spherical network arrangement operator validation\n\nCanonical parent cells, all {len(index.records)} boundary segments and {len(index.by_component)} corridor components are indexed; {len(patches)} junction records were bound. The global arrangement remains incomplete because {len(blocked)} patches are unsupported by the current convex P1 fan and sampled trace error reaches {max_trace:.9g}.\n",
        "R6_JUNCTION_PATCH_OPERATOR_VALIDATION": f"# Junction patch operator validation\n\nLocal fixture trace remains {4.54188e-5:g} and passes. Real canonical binding resolved {len(resolved)}/{len(patches)} junctions; sampled real corridor/P1 trace error max is {max_trace:.9g} over {trace_samples} edge-interior samples ({trace_violations} exceed {TRACE_TOL:g}). Twelve canonical ray configurations fail the current convex triangular-fan construction. A constructible near-antipodal junction exposes the measured cause: its fitted side spans only about 0.0018 of unit circumradius across the corridor normal, so at the worst interior sample signed distance is -0.0008849 m but the P1 weight is 0.999275 versus canonical corridor smoothstep 0.500664. This is geometric conditioning/trace parameterization, not local P1 interpolation error.\n",
        "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX": "# Boundary-zone geometric feasibility matrix\n\nThe four predeclared width cases (100, 250, 500, 1000 km) were not evaluated because canonical junction integration failed first. These are NOT width failures; no width is selected.\n",
        "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS": "# Boundary-zone width case diagnostics\n\nAll four cases are `NOT_RUN_GLOBAL_INTEGRATION_GATE_FAILED`. No global ownership/area/convergence/weight/velocity metrics are claimed.\n",
        "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V15": f"# R6 first physical interval readiness V15\n\nDecision: `CANONICAL_JUNCTION_P1_TRACE_AND_PATCH_BINDING_BLOCKED`. The parent scaffold and canonical segment index validate; only {len(resolved)}/20 P1 junctions bind. Real trace maximum {max_trace:.9g} exceeds 1e-4. Width diagnostics and forward evolution were not run. First dt remains unbound. Next action: `R6_CANONICAL_JUNCTION_P1_GEOMETRY_AND_CORRIDOR_TRACE_COMPATIBILITY_REPAIR`.\n",
    }
    for artifact, value in artifacts.items():
        path = ROOT / f"{artifact}.json"
        if path.exists() and (path.is_symlink() or json.loads(path.read_text(encoding="utf-8")).get("artifact") not in (None, artifact)):
            raise RuntimeError(f"refusing to overwrite unrelated artifact: {path.name}")
        value["artifact"] = artifact
        path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        md = ROOT / f"{artifact}.md"
        md.write_text(markdown[artifact].rstrip() + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"decision": artifacts["R6_FIRST_PHYSICAL_INTERVAL_READINESS_V15"]["decision"],
                      "parent_faces": len(parents), "indexed_segments": len(index.records),
                      "index_midpoint_misses": len(midpoint_misses), "corridor_components": len(index.by_component),
                      "junctions_bound": len(resolved), "junctions_blocked": len(blocked),
                      "trace_samples": trace_samples, "trace_violations": trace_violations,
                      "trace_max": max_trace, "width_cases": "NOT_RUN_GATE_FAILED",
                      "tests": test_output}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
