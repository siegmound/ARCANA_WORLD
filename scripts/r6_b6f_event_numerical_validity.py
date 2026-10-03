#!/usr/bin/env python3
"""Reproduce the read-only R6 B6F event/numerical validity qualification."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "r6/b6f-event-numerical-validity-qualification"
EXPECTED_HEAD = "83061d1a3ecba3455be7bada00a13c8c8a7d16e2"
OUT_REL = Path("outputs/r6_b6f_event_numerical_validity")
HORIZON_YEARS = 27123.405156307464
EARTH_RADIUS_M = 6_371_000.0
SAMPLE_YEARS = (0.0, 1.0, 10.0, 100.0, 1_000.0, 10_000.0, HORIZON_YEARS)


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _check_manifest(directory: Path, manifest_name: str) -> None:
    manifest = _json(directory / manifest_name)
    for item in manifest.get("artifacts", []):
        path = (directory / item["relative_path"]).resolve()
        if not path.is_file():
            raise ValueError(f"missing manifested artifact: {item['relative_path']}")
        if path.stat().st_size != item["byte_size"] or _sha(path) != item["sha256"]:
            raise ValueError(f"manifest mismatch: {item['relative_path']}")


def _rotation_matrix(omega: np.ndarray, years: float) -> np.ndarray:
    """Construct matrix by applying the qualified exact point-rotation kernel."""
    from arcana_worldsim.r6.finite_rotation import rotate_vector_constant_euler

    basis = np.eye(3)
    return np.column_stack([rotate_vector_constant_euler(basis[:, i], omega, years)
                            for i in range(3)])


def _spherical_area(unit: np.ndarray, tri: np.ndarray) -> np.ndarray:
    a, b, c = unit[tri[:, 0]], unit[tri[:, 1]], unit[tri[:, 2]]
    det = np.einsum("ij,ij->i", a, np.cross(b, c))
    den = 1.0 + np.einsum("ij,ij->i", a, b) + np.einsum("ij,ij->i", b, c) + np.einsum("ij,ij->i", c, a)
    return 2.0 * np.arctan2(det, den)


def _unit_vectors(lat_lon: np.ndarray) -> np.ndarray:
    lat, lon = np.radians(lat_lon[:, 0]), np.radians(lat_lon[:, 1])
    return np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))


def _event_taxonomy() -> list[dict[str, str]]:
    return [
        {"event_class": "rift activation", "status": "DETECTOR_AVAILABLE", "scope": "conditional rift-process activation only; not plate split"},
        {"event_class": "plate split / merge / creation / termination", "status": "MODEL_REQUIRED", "scope": "no governed event law or detector"},
        {"event_class": "boundary birth / death / interface split / merge", "status": "DETECTOR_IMPLEMENTATION_REQUIRED", "scope": "no complete detector or acceptance semantics"},
        {"event_class": "plate adjacency change", "status": "DETECTOR_IMPLEMENTATION_REQUIRED", "scope": "current geometric support is static; transition predicate absent"},
        {"event_class": "junction birth / death / connectivity reassignment", "status": "MODEL_REQUIRED", "scope": "no governed junction transition law"},
        {"event_class": "plate-support split / merge", "status": "DETECTOR_IMPLEMENTATION_REQUIRED", "scope": "support transition detector and lineage semantics absent"},
        {"event_class": "interface crossing / gap / overlap", "status": "MODEL_REQUIRED", "scope": "diagnostic residuals measurable; tolerated/invalid boundary semantics unqualified"},
        {"event_class": "other unenumerated topology transition", "status": "UNKNOWN", "scope": "no completeness proof for the event vocabulary"},
    ]


def evaluate(*, enforce_identity: bool = False) -> dict[str, Any]:
    branch, head = _git("branch", "--show-current"), _git("rev-parse", "HEAD")
    if enforce_identity and (branch != EXPECTED_BRANCH or head != EXPECTED_HEAD):
        raise ValueError(f"qualification source mismatch: {branch} {head}")

    b5 = ROOT / "outputs/r6_b5_plate_support_topology_qualification"
    b6a = ROOT / "outputs/r6_b6a_positive_duration_authority"
    b6d = ROOT / "outputs/r6_b6d_authorial_mvp_model_freeze"
    b6e = ROOT / "outputs/r6_b6e_minimal_mvp_model_implementation"
    _check_manifest(b5, "B5_ARTIFACT_MANIFEST.json")
    _check_manifest(b6a, "B6A_ARTIFACT_MANIFEST.json")
    _check_manifest(b6d, "B6D_ARTIFACT_MANIFEST.json")
    _check_manifest(b6e, "B6E_ARTIFACT_MANIFEST.json")

    from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh, _unit_vectors as mesh_unit_vectors
    mesh = load_canonical_mesh(ROOT)
    kin = _json(ROOT / "R6_T0_CANONICAL_PLATE_KINEMATICS.json")
    b5_contract = _json(b5 / "B5_BOUNDARY_CONTRACT.json")
    b5_result = _json(b5 / "B5_RESULT.json")
    b6e_result = _json(b6e / "B6E_RESULT.json")
    b6e_interfaces = _json(b6e / "B6E_BOUNDARY_INTERFACES.json")
    b6e_junctions = _json(b6e / "B6E_JUNCTION_RELATIONS.json")
    b6e_memory = _json(b6e / "B6E_SYSTEM_MEMORY_TRANSFER.json")
    b6a_bound = _json(b6a / "B6A_TOPOLOGY_TEMPORAL_BOUND.json")

    if len(mesh.vertices_lat_lon) != 64_442 or len(mesh.triangles) != 128_880:
        raise ValueError("canonical mesh cardinality differs from B5/B6E authority")
    expected_representation = {"interior_entities": 62469, "boundary_side_entities": 3966,
                               "interfaces": 1983, "junction_side_entities": 60,
                               "junction_relations": 20}
    if any(b6e_result["t0_representation_counts"].get(k) != v
           for k, v in expected_representation.items()):
        raise ValueError("B6E governed representation counts differ from frozen authority")
    plate_rows = {int(p["plate_id"]): np.asarray(p["euler_vector_rad_per_year"], dtype=np.float64)
                  for p in kin["plates"]}
    tri_plate = np.asarray(mesh.triangle_plate_id, dtype=np.int64)
    if set(np.unique(tri_plate).tolist()) != set(plate_rows):
        raise ValueError("mesh plate supports differ from canonical kinematics")

    unit = _unit_vectors(mesh.vertices_lat_lon)
    tri = np.asarray(mesh.triangles, dtype=np.int64) - 1
    area0 = _spherical_area(unit, tri)
    edge_set = set()
    for a, b, c in tri:
        for left, right in ((a, b), (b, c), (c, a)):
            edge_set.add(tuple(sorted((int(left), int(right)))))
    edges = np.asarray(sorted(edge_set), dtype=np.int64)
    chord = np.linalg.norm(unit[edges[:, 0]] - unit[edges[:, 1]], axis=1)
    lengths = 2.0 * EARTH_RADIUS_M * np.arcsin(np.clip(chord / 2.0, 0.0, 1.0))
    node_support: list[set[int]] = [set() for _ in range(len(unit))]
    for t, pid in zip(tri, tri_plate):
        for node in t:
            node_support[int(node)].add(int(pid))
    speed = np.zeros(len(unit), dtype=np.float64)
    local_edge = np.full(len(unit), np.inf)
    for (i, j), length in zip(edges, lengths):
        local_edge[i] = min(local_edge[i], length)
        local_edge[j] = min(local_edge[j], length)
    for node_id, supports in enumerate(node_support):
        if supports:
            speed[node_id] = max(float(np.linalg.norm(np.cross(plate_rows[pid], unit[node_id])))
                                 * EARTH_RADIUS_M for pid in supports)
    mixed_nodes = sum(len(s) > 1 for s in node_support)
    if not np.isfinite(local_edge).all() or np.any(local_edge <= 0):
        raise ValueError("mesh has a node without positive incident edge scale")

    descriptors = b5_contract.get("descriptors", [])
    if not descriptors:
        raise ValueError("B5 boundary descriptors missing")
    sweep = []
    junction_records = b6e_junctions.get("samples", [])
    for years in SAMPLE_YEARS:
        rotated_by_plate = {}
        for pid, omega in plate_rows.items():
            matrix = _rotation_matrix(omega, years)
            rotated_by_plate[pid] = unit @ matrix.T
        max_local_ratio = 0.0
        max_surface_displacement = 0.0
        for node_id, supports in enumerate(node_support):
            for pid in supports:
                moved = rotated_by_plate[pid][node_id]
                sine = float(np.linalg.norm(np.cross(unit[node_id], moved)))
                cosine = float(np.clip(np.dot(unit[node_id], moved), -1.0, 1.0))
                arc_m = EARTH_RADIUS_M * math.atan2(sine, cosine)
                max_surface_displacement = max(max_surface_displacement, arc_m)
                max_local_ratio = max(max_local_ratio, arc_m / float(local_edge[node_id]))
        # Keep shared vertices duplicated by plate-local support for this diagnostic;
        # no single coordinate/owner is assigned to a discontinuous interface.
        area = np.empty(len(tri), dtype=np.float64)
        all_finite = True
        for pid in plate_rows:
            selected = np.flatnonzero(tri_plate == pid)
            local_xyz = rotated_by_plate[pid][tri[selected]]
            all_finite = all_finite and bool(np.isfinite(local_xyz).all())
            area[selected] = _spherical_area(local_xyz.reshape(-1, 3),
                                             np.arange(len(selected) * 3).reshape(-1, 3))
        ratios = area / area0
        interface_gaps = []
        for descriptor in descriptors:
            pa, pb = map(int, descriptor["adjacent_plate_ids"])
            n0, n1 = [int(x) - 1 for x in descriptor["endpoint_node_ids"]]
            for node in (n0, n1):
                delta = rotated_by_plate[pa][node] - rotated_by_plate[pb][node]
                interface_gaps.append(float(2.0 * EARTH_RADIUS_M * math.asin(
                    min(1.0, float(np.linalg.norm(delta)) / 2.0))))
        junction_spreads = []
        for relation in junction_records:
            node = int(relation["source_node_id"]) - 1
            positions = [rotated_by_plate[int(pid)][node] for pid in relation["incident_plate_ids"]]
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    junction_spreads.append(float(2.0 * EARTH_RADIUS_M * math.asin(
                        min(1.0, float(np.linalg.norm(positions[i] - positions[j])) / 2.0))))
        sweep.append({
            "elapsed_years_hypothetical_diagnostic_only": years,
            "all_coordinates_finite": all_finite,
            "negative_orientation_count": int(np.count_nonzero(area <= 0)),
            "max_abs_spherical_area_ratio_error": float(np.max(np.abs(ratios - 1.0))),
            "max_abs_area_error_sr": float(np.max(np.abs(area - area0))),
            "max_hypothetical_surface_displacement_m": max_surface_displacement,
            "max_hypothetical_displacement_to_local_edge_ratio": max_local_ratio,
            "max_hypothetical_plate_rotation_angle_rad": max(float(np.linalg.norm(omega)) * years for omega in plate_rows.values()),
            "max_hypothetical_interface_side_separation_m": max(interface_gaps, default=0.0),
            "max_hypothetical_junction_incident_position_spread_m": max(junction_spreads, default=0.0),
            "canonical_or_future_state_written": False,
        })

    max_relative_speed = 0.0
    for item in descriptors:
        pa, pb = map(int, item["adjacent_plate_ids"])
        a, b = [int(x) - 1 for x in item["endpoint_node_ids"]]
        va = np.cross(plate_rows[pa], unit[a]) * EARTH_RADIUS_M
        vb = np.cross(plate_rows[pb], unit[a]) * EARTH_RADIUS_M
        max_relative_speed = max(max_relative_speed, float(np.linalg.norm(va - vb)))
    boundary_count = len(descriptors)
    junction_count = int(b6e_result["t0_representation_counts"]["junction_relations"])

    constraints = [
        ("kinematic_law", "first-segment duration", "year", "governed plate support", "validate constant-T0 Euler interval", "THRESHOLD_QUALIFICATION_REQUIRED", "no numeric duration or renewal law"),
        ("topology_event", "all applicable topology events", "event/time", "plates/interfaces/junctions", "complete detector or positive invariance proof", "EVENT_COVERAGE_REQUIRED", "event coverage incomplete"),
        ("rigid_rotation", "exact finite rotation action", "dimensionless", "plate-local points", "exact quaternion kernel; rigid invariance", "NOT_APPLICABLE_TO_MVP", "no intrinsic ODE stability limit; no angle accuracy threshold is governed"),
        ("node_displacement", "spherical path length", "m", "plate-local nodes", "exact rotation angle and radius", "THRESHOLD_QUALIFICATION_REQUIRED", "no governed displacement threshold"),
        ("local_mesh_scale", "displacement / minimum incident edge", "1", "node supports", "derived local edge and angular speed", "THRESHOLD_QUALIFICATION_REQUIRED", "no qualified ratio threshold"),
        ("interface_representation", "side gap/crossing/order residual", "m or predicate", "1983 interfaces", "plate-wise exact transform diagnostic", "THRESHOLD_QUALIFICATION_REQUIRED", "no gap/crossing acceptance semantics"),
        ("junction_compatibility", "multi-interface positional spread", "m", "20 junction relations", "plate-wise exact transform diagnostic", "THRESHOLD_QUALIFICATION_REQUIRED", "no compatibility tolerance or response law"),
        ("mesh_geometric", "oriented spherical area and finiteness", "sr", "128880 triangles", "full mesh exact rigid-transform sweep", "QUALIFIED_BOUND_AVAILABLE", "intrinsic shape preserved within each rigid plate; interfaces remain unresolved"),
        ("state_transfer", "field-specific applicability", "classification", "B6E state families", "read transfer declarations", "UNKNOWN", "required physical geography/material transfers are unbound"),
        ("system_memory", "causal memory transfer", "classification", "B6E memory declarations", "read retention/update declarations", "UNKNOWN", "initial-world supported fields remain MODEL_REQUIRED"),
        ("remesh_trigger", "remeshing trigger", "not applicable", "none in MVP", "D4/B6D model", "NOT_APPLICABLE_TO_MVP", "no remesh in the frozen MVP"),
        ("solver_stability", "solver-specific stability", "not applicable", "none in MVP", "D7/no mechanics solver", "NOT_APPLICABLE_TO_MVP", "no mechanics solver in MVP"),
    ]
    categories = {"kinematic_law": "KINEMATIC_LAW_VALIDITY", "topology_event": "TOPOLOGY_EVENT_VALIDITY",
        "rigid_rotation": "RIGID_ROTATION_VALIDITY", "node_displacement": "NODE_DISPLACEMENT_VALIDITY",
        "local_mesh_scale": "DISPLACEMENT_LOCAL_MESH_SCALE_VALIDITY", "interface_representation": "BOUNDARY_INTERFACE_VALIDITY",
        "junction_compatibility": "JUNCTION_COMPATIBILITY_VALIDITY", "mesh_geometric": "MESH_GEOMETRIC_VALIDITY",
        "state_transfer": "STATE_TRANSFER_APPLICABILITY", "system_memory": "SYSTEM_MEMORY_VALIDITY",
        "remesh_trigger": "REMESH_TRIGGER_APPLICABILITY", "solver_stability": "SOLVER_LIMIT_APPLICABILITY"}
    authorities = {"kinematic_law": "B6A first-segment adjudication", "topology_event": "B6A topology bound and B6D D1 event policy",
        "rigid_rotation": "B6D rotation action contract and exact finite quaternion implementation",
        "node_displacement": "B6D numerical contract; no displacement limit selected",
        "local_mesh_scale": "B5 governed mesh plus B6D spatial accuracy contract; ratio threshold missing",
        "interface_representation": "B5 interface relations and B6D D2; response rule/threshold missing",
        "junction_compatibility": "B5/B6E set-valued relations and B6D D3; compatibility rule missing",
        "mesh_geometric": "B5 canonical mesh and B6D D4; rigid invariance tested, interface validity open",
        "state_transfer": "B6E field-specific transfer declarations", "system_memory": "B0-G memory retention and B6E memory declarations",
        "remesh_trigger": "B6D D4; remeshing not selected in MVP", "solver_stability": "B6D D7; no mechanics solver in MVP"}
    threshold_sources = {"kinematic_law": "no numeric segment duration/renewal law in B6A",
        "topology_event": "only conditional rift activation horizon; general detector/invariance rule absent",
        "rigid_rotation": "exact action has no intrinsic ODE stability bound; no separate angular accuracy threshold",
        "node_displacement": "no governed displacement threshold", "local_mesh_scale": "no qualified displacement/edge ratio threshold",
        "interface_representation": "no accepted gap/crossing/overlap criterion", "junction_compatibility": "no positional spread tolerance or accommodation law",
        "mesh_geometric": "intrinsic plate-local shape preserved; no cross-interface acceptance threshold",
        "state_transfer": "not a scalar threshold; required transfers remain MODEL_REQUIRED/UNKNOWN",
        "system_memory": "not a scalar threshold; field-specific update rule is unresolved",
        "remesh_trigger": "not applicable to frozen MVP", "solver_stability": "not applicable without a selected solver"}
    inventory = [{"constraint_id": i, "category": categories[i], "quantity": q, "units": u, "support": s,
                  "evaluation_method": e, "authority_source": authorities[i], "threshold_source": threshold_sources[i],
                  "threshold_status": status,
                  "positive_bound_status": ("NOT_APPLICABLE_TO_MVP" if i in {"rigid_rotation", "remesh_trigger", "solver_stability"} else status),
                  "dependency": "see unresolved constraint and source references", "failure_meaning": why}
                 for i, q, u, s, e, status, why in constraints]

    qualified_bounds = [{
        "bound_id": "B6F_CONDITIONAL_RIFT_ACTIVATION_HORIZON",
        "value": b6a_bound["positive_conditional_rift_activation_bound"]["elapsed_years"],
        "unit": "year", "category": "MODEL_EVENT_HORIZON", "support": "eligible quiescent rift support; limiting pair 1:3",
        "authority": "B6A governed rift guard / B6D topology event policy",
        "derivation": "precommitted 5000 m activation lower threshold divided by maximum supported positive opening rate under fixed T0 Euler rates",
        "coverage": "conditional rift-process activation only; does not cover topology changes",
        "semantics": "strict event horizon only within stated model; NOT_A_DT",
        "applicability_conditions": ["constant T0 Euler rates", "eligible rift model support", "within separately valid first segment"]
    }]
    unresolved = [x[0] for x in constraints if x[5] in {"THRESHOLD_QUALIFICATION_REQUIRED", "EVENT_COVERAGE_REQUIRED", "UNKNOWN"}]
    result = {
        "schema": "R6_B6F_RESULT_V1", "qualification_verdict": "PASS_B6F_EVENT_NUMERICAL_VALIDITY_QUALIFICATION",
        "qualified_source_commit": head, "branch": branch,
        "constraint_inventory_status": "PASS_COMPLETE_MINIMUM_INVENTORY_WITH_EXPLICIT_GAPS",
        "kinematic_validity_status": "CONDITIONAL_CONSTANT_T0_EULER_RULE_NO_GOVERNED_NUMERIC_DURATION",
        "kinematic_positive_bound": None,
        "topology_event_coverage_status": "INCOMPLETE", "topology_validity_status": "NO_POSITIVE_TOPOLOGY_BOUND",
        "topology_positive_bound": None,
        "rotation_validity_status": "EXACT_FINITE_ROTATION_NO_INTRINSIC_ODE_STABILITY_LIMIT",
        "rotation_bound": None,
        "local_scale_validity_status": "DIAGNOSTIC_DERIVABLE_THRESHOLD_UNQUALIFIED",
        "local_scale_bound": None,
        "interface_validity_status": "GAP_MODEL_AND_ACCEPTANCE_THRESHOLD_UNQUALIFIED",
        "interface_bound": None, "junction_validity_status": "GAP_COMPATIBILITY_RULE_UNQUALIFIED",
        "junction_bound": None, "mesh_validity_status": "PLATE_INTERIOR_RIGID_INVARIANCE_QUALIFIED_INTERFACE_RELATIONS_OPEN",
        "mesh_bound": None, "state_transfer_applicability_status": "BLOCKED_BY_MODEL_REQUIRED_FAMILIES",
        "system_memory_validity_status": "RETAINED_BUT_FUTURE_TRANSFER_RULES_UNRESOLVED",
        "qualified_bound_count": 1, "qualified_bounds": qualified_bounds,
        "unresolved_constraints": unresolved,
        "current_smallest_qualified_bound_not_a_dt": None,
        "first_dt_prerequisite_status": "BLOCKED_BY_TOPOLOGY_INTERFACE_JUNCTION_TRANSFER_AND_NUMERICAL_THRESHOLDS",
        "b6g_readiness": "NOT_READY_FOR_FIRST_DT_ADJUDICATION",
        "execution_target": "WINDOWS", "ubuntu_work_required": False,
        "next_stage_recommendation": "AUTHORIZE_TARGETED_VALIDITY_GAP_CLOSURE",
        "scientific_side_effect_check": {"mechanics_authorized": False, "forward_evolution_authorized": False,
            "dt_selected": False, "t1_created": False, "canonical_state_changed": False,
            "canonical_node_motion_executed": False, "canonical_topology_mutated": False,
            "shellset_executed": False, "orbdata_mechanics_executed": False,
            "runtime_authorized": True, "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE"},
        "mesh_evidence": {"node_count": len(unit), "triangle_count": len(tri), "edge_count": len(edges),
            "normalized_mesh_sha256": mesh.normalized_sha256, "mixed_plate_support_node_count": mixed_nodes,
            "edge_length_m": {"minimum": float(np.min(lengths)), "p01": float(np.quantile(lengths, .01)),
                "p05": float(np.quantile(lengths, .05)), "median": float(np.median(lengths)),
                "p95": float(np.quantile(lengths, .95)), "maximum": float(np.max(lengths))},
            "max_surface_speed_m_per_year": float(np.max(speed)),
            "max_local_displacement_rate_per_year": float(np.max(speed / local_edge))},
        "governed_representation_counts": b6e_result["t0_representation_counts"],
        "boundary_evidence": {"interface_count": boundary_count, "junction_relation_count": junction_count,
            "max_relative_boundary_speed_m_per_year": max_relative_speed,
            "geological_boundary_type": "UNKNOWN", "physical_response": "UNKNOWN"},
        "source_evidence": {"B5_result": b5_result["decision"], "B6E_result": b6e_result["decision"],
            "kinematics_payload_identity_sha256": kin["payload_identity_sha256"],
            "B6A_rift_horizon_years": b6a_bound["positive_conditional_rift_activation_bound"]["elapsed_years"],
            "B6A_topology_status": b6a_bound["status"]},
    }
    return {"result": result, "inventory": inventory, "sweep": sweep,
            "taxonomy": _event_taxonomy(), "interfaces": b6e_interfaces,
            "junctions": b6e_junctions, "memory": b6e_memory,
            "state_transfer": _json(b6e / "B6E_STATE_TRANSFER_DECLARATIONS.json"),
            "kinematics": {"status": result["kinematic_validity_status"], "rule": "constant governed T0 Euler vectors, conditional first segment", "numeric_duration_years": None,
                "conditional_rift_activation_horizon_years": HORIZON_YEARS, "not_a_topology_bound": True, "not_a_dt": True},
            "rotation": {"status": result["rotation_validity_status"], "kernel": "rotate_vector_constant_euler", "exact_finite_rotation": True,
                "intrinsic_ode_stability_bound": None, "small_angle_threshold_invented": False},
            "mesh": result["mesh_evidence"], "boundary": result["boundary_evidence"]}


def _write_package(data: dict[str, Any], out: Path,
                   test_results: dict[str, Any] | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    names = {
        "B6F_RESULT.json": data["result"], "B6F_CONSTRAINT_INVENTORY.json": data["inventory"],
        "B6F_KINEMATIC_VALIDITY.json": data["kinematics"], "B6F_TOPOLOGY_EVENT_TAXONOMY.json": data["taxonomy"],
        "B6F_TOPOLOGY_VALIDITY.json": {"status": data["result"]["topology_validity_status"], "positive_bound": None, "events": data["taxonomy"]},
        "B6F_ROTATION_VALIDITY.json": data["rotation"], "B6F_LOCAL_SCALE_ANALYSIS.json": {"mesh": data["result"]["mesh_evidence"], "hypothetical_sweep": data["sweep"], "acceptance_threshold": "MISSING"},
        "B6F_INTERFACE_VALIDITY.json": {"status": data["result"]["interface_validity_status"], "evidence": data["boundary"], "hypothetical_sweep": data["sweep"], "acceptance_threshold": "MISSING"},
        "B6F_JUNCTION_VALIDITY.json": {"status": data["result"]["junction_validity_status"], "relation_count": data["result"]["boundary_evidence"]["junction_relation_count"], "hypothetical_sweep": data["sweep"], "compatibility_threshold": "MISSING"},
        "B6F_MESH_VALIDITY.json": {"status": data["result"]["mesh_validity_status"], "mesh": data["mesh"], "sweep": data["sweep"]},
        "B6F_STATE_TRANSFER_APPLICABILITY.json": data["state_transfer"],
        "B6F_SYSTEM_MEMORY_VALIDITY.json": {"declarations": data["memory"], "status": data["result"]["system_memory_validity_status"]},
        "B6F_QUALIFICATION_SWEEP.json": {"purpose": "hypothetical read-only geometry diagnostics; not future scientific state", "samples": data["sweep"]},
        "B6F_THRESHOLD_JUSTIFICATION.json": {"threshold_policy": "No ungoverned threshold or safety factor selected", "missing_thresholds": data["result"]["unresolved_constraints"]},
        "B6F_QUALIFIED_BOUND_SET.json": {"bounds": data["result"]["qualified_bounds"], "current_smallest_qualified_bound_not_a_dt": None},
        "B6F_UNRESOLVED_CONSTRAINTS.json": data["result"]["unresolved_constraints"],
        "B6F_FIRST_DT_PREREQUISITES.json": {"status": data["result"]["first_dt_prerequisite_status"], "readiness": data["result"]["b6g_readiness"]},
        "B6F_EXECUTION_PLAN.json": {"next_stage_recommendation": data["result"]["next_stage_recommendation"], "ubuntu_work_required": False},
        "B6F_TEST_RESULTS.json": test_results or {"status": "NOT_RECORDED", "source_commit": data["result"]["qualified_source_commit"]},
    }
    for name, value in names.items():
        (out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    readme = "# B6F qualification evidence\n\nRead-only event, geometry and numerical validity qualification. Hypothetical sweeps are diagnostic only. No dt, T1, motion, or topology mutation is produced.\n"
    (out / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    manifest = []
    for path in sorted(out.iterdir()):
        if path.name == "B6F_ARTIFACT_MANIFEST.json" or not path.is_file():
            continue
        manifest.append({"relative_path": path.name, "byte_size": path.stat().st_size, "sha256": _sha(path), "role": "B6F qualification evidence"})
    report = ROOT / "docs/arcana/B6F_EVENT_NUMERICAL_VALIDITY_QUALIFICATION.md"
    if report.is_file():
        manifest.append({"relative_path": "../../docs/arcana/B6F_EVENT_NUMERICAL_VALIDITY_QUALIFICATION.md",
                         "byte_size": report.stat().st_size, "sha256": _sha(report), "role": "human qualification report"})
    manifest.sort(key=lambda item: item["relative_path"])
    (out / "B6F_ARTIFACT_MANIFEST.json").write_text(json.dumps({"schema": "R6_B6F_ARTIFACT_MANIFEST_V1", "manifest_self_hash": "OMITTED_BY_POLICY", "artifacts": manifest}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regression", action="store_true", help="run against a descendant checkout without strict branch/HEAD pin")
    parser.add_argument("--output", type=Path, default=ROOT / OUT_REL)
    parser.add_argument("--test-results-json", type=Path)
    args = parser.parse_args()
    data = evaluate(enforce_identity=not args.regression)
    tests = _json(args.test_results_json) if args.test_results_json else None
    _write_package(data, args.output, tests)
    print(json.dumps(data["result"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
