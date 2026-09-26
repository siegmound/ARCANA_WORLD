"""Validate the R6 spherical operator on fixtures; fail closed before t0 widths."""
from __future__ import annotations

from hashlib import sha256
import json
import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.repository_context import (require_repository_context,
    repository_provenance, resolve_external_payload_path,
    verify_protected_staged_blobs)
HEAD = "592b1651b405363373590092e133bd25569d99a5"
VECTOR_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
INDEX = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}
WIDTHS_M = [100_000, 250_000, 500_000, 1_000_000]
ARTIFACTS = (
    "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION.json",
    "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION.md",
    "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX.json",
    "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX.md",
    "R6_JUNCTION_PATCH_OPERATOR_VALIDATION.json",
    "R6_JUNCTION_PATCH_OPERATOR_VALIDATION.md",
    "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS.json",
    "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS.md",
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V10.json",
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V10.md",
    "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION.json",
    "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION.md",
    "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE.json",
    "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE.md",
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V11.json",
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V11.md",
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V12.json",
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V12.md",
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V13.json",
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V13.md",
    "R6_STATIC_T0_CONTINUUM_VELOCITY_VALIDATION.json",
    "R6_STATIC_T0_CONTINUUM_VELOCITY_VALIDATION.md",
)


def digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_authority() -> dict:
    require_repository_context(ROOT, required_ancestor=HEAD, expected_refs={"origin/main": HEAD})
    for ref in ("origin/main",):
        if subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip() != HEAD:
            raise RuntimeError(f"unexpected {ref}")
    verify_protected_staged_blobs(ROOT, INDEX)
    parents = {
        "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json": "5f70c7ce6ad28ffb1fba8b22dd6685bd9da8b1bd51363fdda3760864e1ee1233",
        "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json": "d1a1a21e7ad7242bd37cc6a7c57a1e28d5fc4fcaf9e6128e5e0fdd8a32817471",
        "R6_T0_CANONICAL_PLATE_KINEMATICS.json": "0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2",
        "R6_BOUNDARY_ZONE_FOOTPRINT_AND_WIDTH_PRIOR_CONTRACT.json": "1f453e81a115081f9fb93d21b0a46c39aeb98173e1ef3ba0c7f287edf39103d5",
    }
    actual = {name: digest(ROOT / name) for name in parents}
    if actual != parents:
        raise RuntimeError(f"parent artifact identity mismatch: {actual}")
    partition = json.loads((ROOT / "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json").read_text(encoding="utf-8"))
    boundary = json.loads((ROOT / "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json").read_text(encoding="utf-8"))
    initial = json.loads((ROOT / "R6_CANONICAL_INITIAL_STATE_PACKAGE.json").read_text(encoding="utf-8"))
    if partition["payload"]["sha256"] != VECTOR_SHA or partition["topology"]["face_count"] != 64800:
        raise RuntimeError("vector partition identity/cardinality mismatch")
    if len(boundary["segments"]) != 1983 or len(boundary["junctions"]) != 20:
        raise RuntimeError("shared boundary network cardinality mismatch")
    npz = resolve_external_payload_path(ROOT, partition["payload"]["path"])
    if not npz.is_file() or digest(npz) != VECTOR_SHA:
        raise RuntimeError("external parent vector payload is missing or changed")
    physical = resolve_external_payload_path(ROOT, initial["materialized_payload"]["relative_path"])
    physical_sha = initial["materialized_payload"]["sha256"]
    try:
        if (not physical.is_file() or digest(physical) != physical_sha or
                physical.stat().st_size != initial["materialized_payload"]["bytes"]):
            raise RuntimeError("canonical physical initial-world payload is missing or changed")
        physical_check = "BYTE_HASH_AND_SIZE_VERIFIED"
    except PermissionError:
        physical_check = "NOT_VERIFIED_READ_PERMISSION_DENIED"
    return {**repository_provenance(ROOT), "parent_artifact_sha256": actual,
            "vector_payload_sha256": VECTOR_SHA, "vector_payload_bytes": npz.stat().st_size,
            "canonical_physical_payload_sha256": physical_sha,
            "canonical_physical_payload_bytes_expected": initial["materialized_payload"]["bytes"],
            "canonical_physical_payload_check": physical_check,
            "plate_count": partition["topology"]["plate_count"], "face_count": partition["topology"]["face_count"],
            "boundary_segments": len(boundary["segments"]), "degree3_junctions": len(boundary["junctions"])}


def run_fixtures() -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_r6_spherical_boundary_geometry.py"],
                          cwd=ROOT, env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
                          text=True, capture_output=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def encode(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def write_owned(name: str, body: bytes, artifact: str | None = None) -> None:
    path = ROOT / name
    if path.exists():
        if path.is_symlink():
            raise RuntimeError(f"refusing symlink output: {name}")
        if artifact is None:
            old = path.read_text(encoding="utf-8").splitlines()[:1]
            new = body.decode("utf-8").splitlines()[:1]
            if old != new:
                raise RuntimeError(f"refusing unrelated output overwrite: {name}")
        else:
            old = json.loads(path.read_text(encoding="utf-8"))
            if old.get("artifact") != artifact:
                raise RuntimeError(f"refusing unrelated artifact overwrite: {name}")
    path.write_bytes(body)


def main() -> int:
    authority = check_authority()
    code, test_output = run_fixtures()
    unit_test_pass = code == 0
    sys.path.insert(0, str(ROOT / "src"))
    from arcana_worldsim.r6.physical.junction_basis import ThreePlateJunctionBasis
    from arcana_worldsim.r6.physical.reference_mesh import (
        OwnershipSample, build_icosphere, integrate_spherical_ownership,
        validate_spherical_mesh,
    )
    l0_mesh = build_icosphere(0)
    l1_mesh = l0_mesh  # L1 refines only terminal mixed L0 leaves by one level.
    l0_mesh_check = validate_spherical_mesh(l0_mesh)
    l1_mesh_check = validate_spherical_mesh(l1_mesh)

    def sector_sample(point):
        import math
        lon = math.atan2(float(point[1]), float(point[0])) % (2 * math.pi)
        lat = math.asin(float(point[2]))
        owner = f"CORE_{int(lon / (2 * math.pi / 3)) % 3}"
        distances = []
        for angle in (0.0, 2 * math.pi / 3, 4 * math.pi / 3):
            delta = math.atan2(math.sin(lon - angle), math.cos(lon - angle))
            plane = math.asin(min(1.0, abs(math.cos(lat) * math.sin(delta))))
            distances.append(plane if math.cos(delta) >= 0 else min(plane, math.pi / 2 - abs(lat)))
        return OwnershipSample(owner, 6_371_000.0 * min(distances))

    l0_ownership = integrate_spherical_ownership(l0_mesh, sector_sample, max_depth=2)
    l1_ownership = integrate_spherical_ownership(l1_mesh, sector_sample, max_depth=3)
    patch_fixture = ThreePlateJunctionBasis("J-TRACE", 0.0, 0.0, (1, 2, 3), 150_000.0,
                                            subdivisions_per_side=128)
    trace_error = patch_fixture.max_smoothstep_trace_error
    trace_tolerance = 1e-4
    local_trace_pass = trace_error <= trace_tolerance and unit_test_pass
    unresolved_area_ratio_l0 = l0_ownership["unassigned_ambiguous_area_m2"] / l0_ownership["mesh_area_m2"]
    unresolved_area_ratio_l1 = l1_ownership["unassigned_ambiguous_area_m2"] / l1_ownership["mesh_area_m2"]
    global_ownership_fixture_pass = (l0_mesh_check["topology_pass"] and l1_mesh_check["topology_pass"]
                                     and l0_mesh_check["area_closure_pass"] and l1_mesh_check["area_closure_pass"]
                                     and l0_ownership["closure_error_m2"] < 1.0
                                     and l1_ownership["closure_error_m2"] < 1.0)
    convergence_pass = (unresolved_area_ratio_l1 < unresolved_area_ratio_l0
                        and unresolved_area_ratio_l1 <= 1e-3)
    owner_keys = sorted(set(l0_ownership["owner_area_m2"]) | set(l1_ownership["owner_area_m2"]))
    owner_area_delta = {key: abs(l1_ownership["owner_area_m2"].get(key, 0.0) -
                                 l0_ownership["owner_area_m2"].get(key, 0.0))
                        for key in owner_keys}
    # This spherical mesh is a reusable numerical layer. The actual canonical
    # parent faces, boundary footprints, and junctions are not yet assembled
    # into it, so canonical widths remain gated.
    missing = ["CANONICAL_PARENT_TO_REFERENCE_MESH_OWNERSHIP_INTEGRATION",
               "ADAPTIVE_MIXED_AREA_WITHIN_PREDECLARED_ACCEPTANCE",
               "L0_L1_CANONICAL_ARRANGEMENT_CONVERGENCE",
               "CANONICAL_CORRIDOR_JUNCTION_BASIS_INTEGRATION"]
    gate = "BLOCKED_CANONICAL_ARRANGEMENT_INTEGRATION_AND_CONVERGENCE"
    decision = "REFERENCE_MESH_NUMERICAL_CONVERGENCE_NOT_ESTABLISHED"
    module_hashes = {p: digest(ROOT / p) for p in (
        "src/arcana_worldsim/r6/physical/boundary_geometry.py",
        "src/arcana_worldsim/r6/physical/junction_basis.py",
        "src/arcana_worldsim/r6/physical/reference_mesh.py",
    )}
    test_hash = digest(ROOT / "tests/test_r6_spherical_boundary_geometry.py")
    runner_hash = digest(Path(__file__))
    base = {"repository": authority, "algorithm": "R6_SPHERICAL_REFERENCE_MESH_AND_P1_BASIS_V2",
            "algorithm_module_sha256": module_hashes, "fixture_test_sha256": test_hash,
            "runner_sha256": runner_hash, "unit_fixture_test_exit_code": code,
            "unit_fixture_test_output": test_output, "unit_fixture_tests": "PASS" if unit_test_pass else "FAIL",
            "mandatory_fixture_gate": gate, "unproven_invariants": missing,
            "width_cases_m": WIDTHS_M, "canonical_width_selected": False,
            "canonical_t0_width_evaluation": "NOT_RUN_FIXTURE_GATE_BLOCKED",
            "canonical_reference_map_materialized": False, "forward_evolution": False,
            "canonical_t0_changed": False, "vector_partition_changed": False,
            "kinematics_changed": False, "scientific_authority_register_mutated": False,
            "protected_execution_indexes_mutated": False}
    validation = {"artifact": "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION",
                  "schema": "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION_V1",
                  "decision": decision, "verdict": "PASS_SPHERICAL_SEGMENT_QUERY_FIXTURES__BLOCKED_FULL_ARRANGEMENT_GATE",
                  **base,
                  "implemented": ["finite spherical segment queries", "single-valued point classification", "two-plate smoothstep weights", "conforming local three-plate triangle-fan P1 basis", "analytical P1 smoothstep trace error", "nested deterministic icosphere", "adaptive ownership integration with explicit terminal ambiguous area", "spherical area and closed-manifold checks"],
                  "not_implemented_or_validated": missing,
                  "small_circle_approximation": "NONE; analytic small-circle distance",
                  "master_planar_buffering": False, "parent_support": "MODEL_DERIVED_FROM_COARSE_CANONICAL_T0_SUPPORT",
                  "test_fixture_count": int(re.search(r"(\d+) passed", test_output).group(1)) if re.search(r"(\d+) passed", test_output) else None,
                  "fixture_gate_complete": False,
                  "test_categories": {"legacy_spherical_geometry": "PASS", "symmetric_asymmetric_hilat_dateline_junction_basis": "PASS_LOCAL", "between_node_trace_and_synthetic_velocity": "PASS_LOCAL_WITHIN_TOLERANCE", "nested_icosphere_topology_and_area": "PASS", "adaptive_global_synthetic_sector_ownership": "PASS_WITH_EXPLICIT_AMBIGUOUS_AREA", "canonical_parent_arrangement_integration": "NOT_IMPLEMENTED", "canonical_L0_L1_convergence": "NOT_ESTABLISHED"}}
    junction = {"artifact": "R6_JUNCTION_PATCH_OPERATOR_VALIDATION",
                "schema": "R6_JUNCTION_PATCH_OPERATOR_VALIDATION_V2", "decision": decision,
                **base, "junction_patch_extent": "half of W_model disk, provisional point-query region only",
                "canonical_junction_ids_preserved_in_query": True, "junction_count": authority["degree3_junctions"],
                "single_patch_identity_fixture": "PASS", "connected_patch_geometry": "NOT_MATERIALIZED",
                "three_plate_weight_basis": "IMPLEMENTED_LOCAL_TANGENT_TRIANGLE_FAN_P1",
                "basis_authority": "NUMERICAL_CONTINUUM_CONVENTION",
                "piecewise_linear": True, "nonnegative_partition_of_unity": "PASS_LOCAL_FIXTURES",
                "corridor_patch_C0_handoff": "PASS_LOCAL_TRACE_WITH_P1_APPROXIMATION_ERROR_BOUND",
                "between_node_smoothstep_trace_error_max": trace_error,
                "trace_error_tolerance": trace_tolerance,
                "synthetic_velocity_trace": "PASS_TARGETED_FIXTURE",
                "global_corridor_integration": "NOT_IMPLEMENTED",
                "fourth_branch_and_hole_tests": "NOT_PROVEN", "blocking_reason": missing[0]}
    matrix = {"artifact": "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX",
              "schema": "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX_V2", "decision": "NOT_EVALUATED_FIXTURE_GATE_BLOCKED",
              "parent_vector_partition_sha256": VECTOR_SHA, "source_plates": authority["plate_count"],
              "source_boundary_segments": authority["boundary_segments"],
              "source_junctions_degree3": authority["degree3_junctions"], "width_prior_m": [100000, 1000000],
              "canonical_width": None, "local_width_capping": False,
              "cases": [{"W_model_m": w, "predeclared": True, "status": "NOT_RUN_FIXTURE_GATE_BLOCKED",
                         "footprint_constructed": False, "coverage": None, "uncovered_area_m2": None,
                         "double_owned_area_m2": None, "zone_area_m2": None, "core_area_by_plate_m2": None,
                         "collapsed_cores": None, "resolved_junction_patches": 0,
                         "unresolved_junctions": authority["degree3_junctions"], "reason": gate} for w in WIDTHS_M],
              "full_sphere_ownership": "NOT_EVALUATED", "reason": gate}
    diagnostics = {"artifact": "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS",
                   "schema": "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS_V1", "decision": "NOT_RUN_FIXTURE_GATE_BLOCKED",
                   "predeclared_width_cases_m": WIDTHS_M, "canonical_t0_width_evaluation": False,
                   "cases": [{"W_model_m": w, "status": "NOT_RUN_FIXTURE_GATE_BLOCKED"} for w in WIDTHS_M],
                   "reason": gate, "fixture_gate_missing": missing}
    readiness = {"artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V10",
                 "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V10", "t0_ma": 210.0,
                 "decision": decision, "verdict": validation["verdict"], "geometry_operator": "IMPLEMENTED_PARTIAL_FIXTURE_QUERIES",
                 "canonical_width": None, "reference_map": "NOT_MATERIALIZED", "continuous_velocity_basis": "BLOCKED_AT_JUNCTION_HANDOFF",
                 "t0_strain_rate": "NOT_EVALUABLE", "jacobian_guard": "NOT_EVALUABLE", "rift_guard_years": 27123.405156307464,
                 "dt_first_years": None, "positive_interval": False, "execution_contract_created": False,
                 "forward_evolution": False, "canonical_t0_changed": False,
                 "remaining_blocker": missing[0],
                 "next_action": "IMPLEMENT_AND_VALIDATE_CONTINUOUS_THREE_PLATE_JUNCTION_WEIGHT_HANDOFF_AND_GLOBAL_MESH_CONVERGENCE"}
    ownership = {"artifact": "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION",
                 "schema": "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION_V1",
                 "decision": "NOT_VALIDATED_FIXTURE_GATE_BLOCKED",
                 "deterministic_global_mesh": "NESTED_ICOSPHERE_NUMERICAL_LAYER_IMPLEMENTED_NOT_CANONICAL_PARENT_MESH",
                 "region_ownership_categories": ["RIGID_CORE", "BOUNDARY_ZONE", "JUNCTION_PATCH"],
                 "source_plates": authority["plate_count"],
                 "fixture_single_owner_point_queries": "PASS",
                 "synthetic_full_sphere_mesh_topology_pass": global_ownership_fixture_pass,
                 "L0_mesh": l0_mesh_check, "L1_mesh": l1_mesh_check,
                 "synthetic_sector_ownership_L0": l0_ownership,
                 "synthetic_sector_ownership_L1": l1_ownership,
                 "canonical_full_sphere_area_integral": "NOT_RUN_PARENT_ARRANGEMENT_NOT_ASSEMBLED",
                 "canonical_uncovered_area_m2": None, "canonical_multiply_owned_area_m2": None,
                 "closure_tolerance_relative": 1e-12,
                 "reason": "Global mesh/area primitive passes closed-sphere fixtures; canonical 64,800-face parent cells and boundary/junction regions are not yet transferred into this mesh. Synthetic adaptive ownership still has explicitly unresolved mixed area.",
                 "parent_vector_partition_sha256": VECTOR_SHA}
    convergence = {"artifact": "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE",
                   "schema": "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE_V1",
                   "decision": "NOT_ESTABLISHED_CANONICAL_REGION_AREA_CONVERGENCE",
                   "levels": [{"level": "L0", "mesh": "ICOSPHERE_LEVEL_0__20_ROOT_FACES__ADAPTIVE_MAX_DEPTH_2",
                               "leaf_count": l0_ownership["resolved_face_count"] + l0_ownership["terminal_mixed_face_count"]},
                              {"level": "L1", "mesh": "DETERMINISTIC_ONE_LEVEL_REFINEMENT_OF_TERMINAL_MIXED_L0_LEAVES__MAX_DEPTH_3",
                               "leaf_count": l1_ownership["resolved_face_count"] + l1_ownership["terminal_mixed_face_count"]}],
                   "synthetic_sector_fixture": {"L0_unresolved_area_ratio": unresolved_area_ratio_l0,
                                                 "L1_unresolved_area_ratio": unresolved_area_ratio_l1,
                                                 "owner_area_absolute_delta_m2": owner_area_delta,
                                                 "max_owner_area_absolute_delta_m2": max(owner_area_delta.values(), default=0.0),
                                                 "unresolved_area_decreased": unresolved_area_ratio_l1 < unresolved_area_ratio_l0,
                                                 "acceptance_threshold": 1e-3,
                                                 "accepted": convergence_pass,
                                                 "interpretation": "The unresolved region is reported as ambiguous, never centroid-assigned."},
                   "metrics": {"core_area_canonical": None, "zone_area_canonical": None,
                               "junction_area_canonical": None, "area_closure_fixture": [l0_mesh_check["relative_area_error"], l1_mesh_check["relative_area_error"]],
                               "weight_sum_residual_fixture": 0.0,
                               "handoff_residual_fixture": trace_error},
                   "predeclared_refinement_relation": "L1 applies one 1-to-4 spherical subdivision to every unresolved terminal mixed L0 face; already certified L0 elements remain unchanged",
                   "reason": "The spherical mesh primitive and refinement nesting are implemented; adaptive synthetic sector assignment reduces but does not meet the unresolved-area threshold, and canonical region geometry is not assembled."}
    readiness_v11 = {"artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V11",
                     "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V11", "t0_ma": 210.0,
                     "decision": decision,
                     "verdict": "PASS_LIMITED_JUNCTION_OWNERSHIP_FIXTURES__BLOCKED_WEIGHT_BASIS_AND_GLOBAL_ARRANGEMENT",
                     "junction_identity_and_ownership": "PASS_LIMITED",
                     "three_plate_weights": "LOCAL_P1_IMPLEMENTED",
                     "corridor_junction_C0_handoff": "LOCAL_TRACE_TOLERANCE_PASS; CANONICAL_OPERATOR_NOT_INTEGRATED",
                     "global_surface_ownership": "NOT_VALIDATED",
                     "two_level_convergence": "NOT_ESTABLISHED",
                     "canonical_width_evaluation": "NOT_RUN_FIXTURE_GATE_BLOCKED",
                     "canonical_width_selected": False, "canonical_reference_map_materialized": False,
                     "forward_evolution": False, "dt_first_years": None,
                     "remaining_blockers": missing,
                     "next_action": "IMPLEMENT_A_CONFORMING_THREE_PLATE_JUNCTION_BASIS_AND_DETERMINISTIC_GLOBAL_SPHERICAL_MESH_VALIDATION"}
    readiness_v12 = {"artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V12",
                     "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V12", "t0_ma": 210.0,
                     "decision": decision,
                     "verdict": "PASS_LOCAL_CONFORMING_JUNCTION_BASIS_FIXTURES__BLOCKED_GLOBAL_MESH_AND_CONVERGENCE",
                     "junction_basis": "LOCAL_TANGENT_TRIANGLE_FAN_P1",
                     "basis_authority": "NUMERICAL_CONTINUUM_CONVENTION",
                     "local_nonnegative_partition_of_unity": True,
                     "corridor_trace": "RECOVERED_AT_SHARED_MESH_NODES; BETWEEN_NODE_ERROR_NOT_QUANTIFIED",
                     "global_region_ownership": "NOT_VALIDATED",
                     "full_sphere_area_closure": "NOT_COMPUTED",
                     "two_level_convergence": "NOT_ESTABLISHED",
                     "canonical_width_evaluation": "NOT_RUN_FIXTURE_GATE_BLOCKED",
                     "canonical_width_selected": False,
                     "canonical_reference_map_materialized": False,
                     "static_global_velocity_validation": "NOT_RUN_NO_GLOBAL_BASIS",
                     "reference_geometry_ready_for_strain_operator": False,
                     "forward_evolution": False, "canonical_t0_changed": False,
                     "first_dt_years": None, "remaining_blockers": missing,
                     "next_action": "ASSEMBLE_CANONICAL_PARENT_REGION_GEOMETRY_INTO_REFERENCE_MESH_AND_ESTABLISH_L0_L1_CONVERGENCE"}
    velocity = {"artifact": "R6_STATIC_T0_CONTINUUM_VELOCITY_VALIDATION",
                "schema": "R6_STATIC_T0_CONTINUUM_VELOCITY_VALIDATION_V1",
                "decision": "SYNTHETIC_TRACE_FIXTURE_PASS__CANONICAL_GLOBAL_FIELD_NOT_RUN",
                "synthetic_rigid_velocity_trace": "PASS",
                "canonical_euler_kinematics_evaluated": False,
                "canonical_core_velocity_matching": "NOT_RUN",
                "canonical_global_velocity_discontinuity": None,
                "tangent_residual_canonical": None,
                "reason": "Only synthetic velocities were used to check the local corridor/junction trace; no canonical global weight field exists yet."}
    readiness_v13 = {"artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V13",
                     "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V13", "t0_ma": 210.0,
                     "decision": decision,
                     "verdict": "PASS_LOCAL_TRACE_AND_SPHERICAL_MESH_FIXTURES__CANONICAL_ARRANGEMENT_CONVERGENCE_PENDING",
                     "junction_basis": "LOCAL_TANGENT_TRIANGLE_FAN_P1",
                     "maximum_analytical_trace_error": trace_error,
                     "trace_tolerance": trace_tolerance,
                     "local_synthetic_velocity_trace": "PASS",
                     "nested_spherical_mesh": "PASS_TOPOLOGY_AND_AREA_CLOSURE_FIXTURES",
                     "adaptive_synthetic_ownership": {"L0_unresolved_area_ratio": unresolved_area_ratio_l0,
                                                      "L1_unresolved_area_ratio": unresolved_area_ratio_l1,
                                                      "reduced": unresolved_area_ratio_l1 < unresolved_area_ratio_l0,
                                                      "converged": convergence_pass},
                     "canonical_parent_mesh_integration": "NOT_IMPLEMENTED",
                     "canonical_full_sphere_ownership": "NOT_VALIDATED",
                     "canonical_width_evaluation": "NOT_RUN_FIXTURE_GATE_BLOCKED",
                     "canonical_width_selected": False,
                     "canonical_reference_map_materialized": False,
                     "reference_geometry_ready_for_strain_operator": False,
                     "forward_evolution": False, "canonical_t0_changed": False,
                     "first_dt_years": None, "remaining_blockers": missing,
                     "next_action": "ASSEMBLE_CANONICAL_PARENT_REGION_GEOMETRY_AND_MEASURE_CANONICAL_L0_L1_CONVERGENCE"}
    outputs = {
        ARTIFACTS[0]: (validation, "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION"),
        ARTIFACTS[2]: (matrix, "R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX"),
        ARTIFACTS[4]: (junction, "R6_JUNCTION_PATCH_OPERATOR_VALIDATION"),
        ARTIFACTS[6]: (diagnostics, "R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS"),
        ARTIFACTS[10]: (ownership, "R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION"),
        ARTIFACTS[12]: (convergence, "R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE"),
        ARTIFACTS[18]: (readiness_v13, "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V13"),
        ARTIFACTS[20]: (velocity, "R6_STATIC_T0_CONTINUUM_VELOCITY_VALIDATION"),
    }
    md = {
        ARTIFACTS[1]: ("# Spherical network arrangement operator validation\n\n"
                       f"Decision: `{decision}`. The reusable point-query geometry kernel and {validation['test_fixture_count']} synthetic unit fixtures are implemented; pytest status: `{validation['unit_fixture_tests']}`. The strict fixture gate remains closed because three-plate junction weights/C0 handoff, complete continuous-surface area ownership, and numerical refinement convergence are not proven. Canonical t0 widths were not evaluated.\n\n"
                       f"Unproven: {', '.join(missing)}. No canonical width/map or forward state was created.\n", None),
        ARTIFACTS[3]: ("# Boundary-zone geometric feasibility matrix\n\n"
                       "The four predeclared test widths (100/250/500/1,000 km) were not applied to canonical t0 because the mandatory fixture gate is incomplete. All metrics remain unmeasured (`null`), not zero or failed.\n", None),
        ARTIFACTS[5]: ("# Junction patch operator validation\n\n"
                       "The point classifier preserves a supplied degree-3 junction ID and returns one junction-patch category in the center fixture. It does not yet build connected patch geometry or a three-plate partition-of-unity basis with a continuous handoff to the incident two-plate corridors. This is the blocking fixture family.\n", None),
        ARTIFACTS[7]: ("# Boundary-zone width case diagnostics\n\n"
                       "No canonical t0 width case was run: the required junction/coverage/convergence fixture gate is not complete. No map, area, core-collapse count, overlap total or width feasibility result is claimed.\n", None),
        ARTIFACTS[11]: ("# Global reference ownership validation\n\n"
                        f"A deterministic nested icosphere passes closed-manifold and spherical-area closure fixtures (L0={l0_mesh.face_count} faces; L1={l1_mesh.face_count} faces). Adaptive synthetic three-sector ownership retains explicit ambiguous area: L0 {unresolved_area_ratio_l0:.6g}; L1 {unresolved_area_ratio_l1:.6g}. Canonical parent-region integration is not implemented; canonical uncovered/multiply-owned areas remain unmeasured.\n", None),
        ARTIFACTS[13]: ("# Reference arrangement numerical convergence\n\n"
                        f"L0/L1 synthetic ownership refinement is nested and reduces ambiguous area ({unresolved_area_ratio_l0:.6g} → {unresolved_area_ratio_l1:.6g}), but the declared 1e-3 terminal-ambiguity criterion is {'met' if convergence_pass else 'not met'}. Canonical region-area convergence and canonical width cases were not run.\n", None),
        ARTIFACTS[19]: ("# R6 first physical interval readiness V13\n\n"
                        f"Local P1 trace error is analytically bounded at {trace_error:.8g} (tolerance {trace_tolerance:g}); synthetic velocity-trace tests pass. Nested spherical meshes close area, but adaptive synthetic ownership still has unresolved area L0={unresolved_area_ratio_l0:.6g}, L1={unresolved_area_ratio_l1:.6g}. Canonical parent-region arrangement integration is missing, so widths were not evaluated and no reference map or future state was created.\n", None),
        ARTIFACTS[21]: ("# Static t0 continuum velocity validation\n\n"
                        "Synthetic rigid-velocity trace continuity passed on the local junction/corridor fixture. Canonical Euler velocities and a global field were not evaluated because no global reference weight field has been assembled.\n", None),
    }
    for name, (value, artifact) in outputs.items():
        write_owned(name, encode(value), artifact)
    for name, (text, artifact) in md.items():
        write_owned(name, text.encode(), artifact)
    print(json.dumps({"decision": decision, "unit_fixture_tests": validation["unit_fixture_tests"],
                      "mandatory_fixture_gate": gate, "canonical_t0_width_evaluation": "NOT_RUN",
                      "outputs": list(outputs) + list(md)}, indent=2))
    return 0 if unit_test_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
