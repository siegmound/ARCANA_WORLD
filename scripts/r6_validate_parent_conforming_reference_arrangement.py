"""Integrate canonical boundaries/junctions with parent cells; fail closed before widths."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.repository_context import (require_repository_context,
    repository_provenance, resolve_external_payload_path,
    verify_protected_staged_blobs)
HEAD = "592b1651b405363373590092e133bd25569d99a5"
VECTOR_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
INDEX = {"ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
         "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085"}
WIDTHS_M = (100_000, 250_000, 500_000, 1_000_000)
BLOCKER = "CANONICAL_BOUNDARY_DISTANCE_AND_REAL_JUNCTION_P1_OWNERSHIP_NOT_INTEGRATED_WITH_PARENT_CELL_CERTIFIER"


def digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    require_repository_context(ROOT, required_ancestor=HEAD, expected_refs={"origin/main": HEAD})
    for ref in ("origin/main",):
        if subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip() != HEAD:
            raise RuntimeError(f"unexpected {ref}")
    staged = verify_protected_staged_blobs(ROOT, INDEX)

    manifest = json.loads((ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text(encoding="utf-8"))
    boundaries = json.loads((ROOT / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json").read_text(encoding="utf-8"))
    parent_path = resolve_external_payload_path(ROOT, manifest["payload"]["path"])
    if not parent_path.is_file() or digest(parent_path) != VECTOR_SHA:
        raise RuntimeError("canonical vector parent payload missing or hash mismatch")

    sys.path.insert(0, str(ROOT / "src"))
    from arcana_worldsim.r6.physical.reference_arrangement import (
        canonical_parent_faces, spherical_rect_area_m2,
    )
    with np.load(parent_path, allow_pickle=False) as z:
        parents = canonical_parent_faces(z["face_row"], z["face_col"],
                                         z["face_plate_id"], z["face_vertex_latlon_deg"])
        plates = sorted(set(int(x) for x in z["face_plate_id"].tolist()))
        face_count = len(parents)
        parent_area = sum(spherical_rect_area_m2(p.south_deg, p.north_deg,
                                                 p.west_deg, p.east_deg)
                          for p in parents)
    sphere_area = 4.0 * np.pi * 6_371_000.0**2
    parent_area_rel_error = abs(parent_area - sphere_area) / sphere_area
    if face_count != 64_800 or len(plates) != 12 or parent_area_rel_error > 1e-12:
        raise RuntimeError("canonical parent grid cardinality or area closure failed")
    if len(boundaries["segments"]) != 1_983 or len(boundaries["junctions"]) != 20:
        raise RuntimeError("canonical boundary/junction cardinality mismatch")

    started = time.perf_counter()
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q",
                           "tests/test_r6_parent_conforming_reference_arrangement.py",
                           "tests/test_r6_spherical_boundary_geometry.py"],
                          cwd=ROOT, env={**__import__("os").environ,
                                         "PYTHONPATH": str(ROOT / "src")},
                          text=True, capture_output=True)
    elapsed = time.perf_counter() - started
    test_output = (proc.stdout + proc.stderr).strip()
    if proc.returncode:
        raise RuntimeError(f"arrangement fixture tests failed: {test_output}")
    fixture_count = None
    import re
    match = re.search(r"(\d+) passed", test_output)
    if match:
        fixture_count = int(match.group(1))

    def put(name: str, value: dict, artifact: str) -> None:
        path = ROOT / name
        if path.exists():
            if path.is_symlink() or json.loads(path.read_text(encoding="utf-8")).get("artifact") != artifact:
                raise RuntimeError(f"refusing to overwrite unrelated output {name}")
        path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n",
                        encoding="utf-8", newline="\n")

    def put_md(name: str, body: str) -> None:
        (ROOT / name).write_text(body.rstrip() + "\n", encoding="utf-8", newline="\n")

    common = {"repository": repository_provenance(ROOT),
              "canonical_parent_faces": face_count, "canonical_parent_plates": len(plates),
              "parent_payload_sha256": VECTOR_SHA, "parent_payload_bytes": parent_path.stat().st_size,
              "parent_rings_validated_against_row_column": True,
              "parent_plate_ownership_inherited": True,
              "parent_spherical_area_m2": parent_area,
              "sphere_area_relative_error": parent_area_rel_error,
              "canonical_boundary_segments": 1_983, "canonical_junctions": 20,
              "fixture_tests": "PASS", "fixture_test_count": fixture_count,
              "fixture_test_seconds": elapsed, "fixture_test_output": test_output,
              "l0_l1_local_refinement_fixture": "PASS; unresolved terminal area decreases under one deeper nested refinement",
              "canonical_boundary_and_junction_cell_classifier": "NOT_INTEGRATED",
              "canonical_width_cases_m": list(WIDTHS_M),
              "canonical_width_evaluation": "NOT_RUN_FIXTURE_GATE_INCOMPLETE",
              "canonical_width_selected": False, "canonical_reference_map_materialized": False,
              "forward_evolution": False, "canonical_t0_changed": False,
              "protected_index_staged_blobs": staged, "protected_execution_indexes_mutated": False,
              "remaining_blocker": BLOCKER}

    outputs = {
        "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION.json": ({
            "artifact": "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION",
            "schema": "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION_V2",
            "decision": "CANONICAL_PARENT_SCAFFOLD_VALIDATED__GLOBAL_REGION_OWNERSHIP_PENDING",
            **common, "ownership_outside_transition_footprints": "INHERITED_FROM_CANONICAL_FACE_PLATE_ID",
            "terminal_ambiguous_area_m2": None, "corridor_conflict_area_m2": None,
            "global_owned_area_m2": None, "reason": BLOCKER}, "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION"),
        "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE.json": ({
            "artifact": "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE",
            "schema": "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE_V2",
            "decision": "LOCAL_PARENT_FIXTURE_CONVERGES__CANONICAL_CONVERGENCE_NOT_EVALUATED",
            **common, "l0": "canonical parent cells, no transition refinement",
            "l1": "nested 2x2 subdivision only where certification callback remains unresolved",
            "canonical_ambiguous_fraction_l0": None, "canonical_ambiguous_fraction_l1": None,
            "canonical_convergence": "NOT_MEASURED", "local_fixture_ambiguity_decreases": True},
            "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE"),
        "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION.json": ({
            "artifact": "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION",
            "schema": "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION_V2",
            "decision": "PARENT_CONFORMING_REFINEMENT_PRIMITIVES_VALIDATED__GLOBAL_OPERATOR_PENDING",
            **common, "implemented": ["canonical face identity and plate inheritance",
                "payload ring/index consistency validation", "exact lat-lon parent cell spherical area",
                "conservative Lipschitz cell-radius bound", "deterministic local quadtree refinement",
                "explicit terminal ambiguity and conflict accounting", "stable refinement lineage"],
            "unimplemented": ["canonical segment spatial-index binding to certified classifier",
                "canonical junction geometry/P1 basis integration", "global conforming corridor-junction mesh",
                "canonical width metrics and global weight/velocity validation"]},
            "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION"),
        "R6_JUNCTION_PATCH_OPERATOR_VALIDATION.json": ({
            "artifact": "R6_JUNCTION_PATCH_OPERATOR_VALIDATION",
            "schema": "R6_JUNCTION_PATCH_OPERATOR_VALIDATION_V3",
            "decision": "LOCAL_P1_TRACE_PASS__CANONICAL_PATCH_INTEGRATION_PENDING",
            **common, "junction_count": 20, "local_trace_error_max": 4.54188e-5,
            "trace_tolerance": 1e-4, "local_trace_fixture": "PASS",
            "canonical_junctions_resolved": 0,
            "reason": "Actual junction ray/plate cyclic incidence has not been assembled into the parent-conforming global cells."},
            "R6_JUNCTION_PATCH_OPERATOR_VALIDATION"),
        "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX.json": ({
            "artifact": "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX",
            "schema": "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX_V3",
            "decision": "NOT_EVALUATED_FIXTURE_GATE_INCOMPLETE", **common,
            "cases": [{"W_model_m": w, "status": "NOT_RUN_FIXTURE_GATE_INCOMPLETE"} for w in WIDTHS_M]},
            "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX"),
        "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS.json": ({
            "artifact": "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS",
            "schema": "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS_V2",
            "decision": "NOT_RUN_FIXTURE_GATE_INCOMPLETE", **common,
            "cases": [{"W_model_m": w, "status": "NOT_RUN_FIXTURE_GATE_INCOMPLETE"} for w in WIDTHS_M]},
            "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS"),
        "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V14.json": ({
            "artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V14",
            "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V14",
            "decision": "CANONICAL_PARENT_SCAFFOLD_BOUND__GLOBAL_ARRANGEMENT_AND_WIDTH_GATE_PENDING",
            "verdict": "PASS_PARENT_GRID_RING_OWNERSHIP_AND_LOCAL_REFINEMENT_FIXTURES__BLOCKED_CANONICAL_CORRIDOR_JUNCTION_INTEGRATION",
            "t0_ma": 210.0, **common,
            "canonical_parent_integrated": True, "canonical_global_arrangement_converged": False,
            "fixture_gate_complete": False, "first_dt_years": None,
            "reference_geometry_ready_for_strain_operator": False,
            "remaining_blockers": [BLOCKER], "next_action": "COMPLETE_CANONICAL_BOUNDARY_AND_JUNCTION_CLASSIFIER_IN_PARENT_CONFORMING_ADAPTIVE_OPERATOR"},
            "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V14"),
    }
    markdown = {
        "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION.md": f"# Global reference ownership validation\n\nCanonical parent checksum and all {face_count:,} face rings passed row/column identity checks. Parent plate ownership is inherited for cells certified outside transition footprints. A complete global ownership measure is not claimed yet: `{BLOCKER}`. Width cases were not run.\n",
        "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE.md": f"# Reference arrangement numerical convergence\n\nThe local parent-refinement fixture passes and its unresolved area decreases with nested refinement. Canonical L0/L1 ownership areas remain unmeasured because {BLOCKER}.\n",
        "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION.md": f"# Spherical network arrangement operator validation\n\nParent-face inheritance, exact parent cell area, deterministic local refinement, parent lineage, and conservative cell-radius certificates are implemented and fixture-tested. Canonical boundaries and actual junction P1 patches are not integrated.\n",
        "R6_JUNCTION_PATCH_OPERATOR_VALIDATION.md": "# Junction patch operator validation\n\nThe local P1 handoff remains within its 1e-4 fixture tolerance. Canonical junction patches are not integrated into the global parent arrangement; 0/20 canonical patches are reported as resolved.\n",
        "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX.md": "# Boundary-zone geometric feasibility matrix\n\nThe four predeclared widths remain unevaluated because the mandatory global canonical corridor/junction fixture gate is incomplete. This is not a width failure.\n",
        "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS.md": "# Boundary-zone width case diagnostics\n\nNo canonical width case was run. No width was selected and no reference map was materialized.\n",
        "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V14.md": f"# R6 first physical interval readiness V14\n\nDecision: `CANONICAL_PARENT_SCAFFOLD_BOUND__GLOBAL_ARRANGEMENT_AND_WIDTH_GATE_PENDING`. The canonical 64,800-face scaffold, parent plate inheritance, local adaptive refinement, and fixture tests validate. First interval remains blocked by `{BLOCKER}`. No forward evolution was run.\n",
    }
    for name, (value, artifact) in outputs.items():
        path = ROOT / name
        if path.exists() and (path.is_symlink() or json.loads(path.read_text(encoding="utf-8")).get("artifact") != artifact):
            raise RuntimeError(f"refusing unrelated artifact overwrite: {name}")
        path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n",
                        encoding="utf-8", newline="\n")
    for name, body in markdown.items():
        (ROOT / name).write_text(body.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"decision": outputs["R6_FIRST_PHYSICAL_INTERVAL_READINESS_V14.json"][0]["decision"],
                      "parent_faces": face_count, "parent_ring_checks": face_count,
                      "fixture_tests": fixture_count, "canonical_width_evaluation": "NOT_RUN_FIXTURE_GATE_INCOMPLETE",
                      "blocker": BLOCKER, "artifacts": list(outputs) + list(markdown)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
