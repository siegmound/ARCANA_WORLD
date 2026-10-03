#!/usr/bin/env python3
"""Produce B6 dependency/temporal-gap adjudication from current B3-B5 evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
B6_BRANCH = "r6/b6-dependency-temporal-gap-adjudication"
OUT_DEFAULT = ROOT / "outputs/r6_b6_dependency_temporal_gap_adjudication"
REPORT = ROOT / "docs/arcana/B6_DEPENDENCY_TEMPORAL_GAP_ADJUDICATION.md"
GRAPH_EDGE_KINDS = {"REQUIRES", "DERIVES_FROM", "PROVIDED_BY", "BLOCKED_BY",
                    "OPTIONAL_FOR_FIRST_STEP", "REQUIRED_BEFORE_MECHANICS"}
EXPECTED_DECISION = "PASS_B6_DEPENDENCY_TEMPORAL_GAP_ADJUDICATION"
GATES = {
    "runtime_authorized": True,
    "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
    "mechanics_authorized": False,
    "forward_evolution_authorized": False,
    "dt_selected": False,
    "t1_created": False,
    "canonical_state_changed": False,
    "shellset_executed": False,
    "orbdata_mechanics_executed": False,
    "forward_plate_reconstruction_executed": False,
    "node_movement_executed": False,
    "topology_mutation_executed": False,
}


class B6QualificationError(ValueError):
    pass


def validate_causal_graph(graph: Mapping[str, Any]) -> bool:
    nodes = graph.get("nodes", [])
    ids = [str(row.get("node_id", "")) for row in nodes]
    if not ids or any(not value for value in ids) or len(ids) != len(set(ids)):
        raise B6QualificationError("causal graph node IDs must be nonempty and unique")
    adjacency = {node_id: [] for node_id in ids}
    indegree = {node_id: 0 for node_id in ids}
    for edge in graph.get("edges", []):
        source, target, kind = (str(edge.get(key, "")) for key in ("from", "to", "kind"))
        if source not in adjacency or target not in adjacency:
            raise B6QualificationError("causal graph edge references an unknown node")
        if kind not in GRAPH_EDGE_KINDS:
            raise B6QualificationError("causal graph edge kind is not governed by B6 schema")
        adjacency[source].append(target)
        indegree[target] += 1
    ready = sorted(node for node, count in indegree.items() if count == 0)
    visited = 0
    while ready:
        node = ready.pop(0)
        visited += 1
        for target in sorted(adjacency[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort()
    if visited != len(ids):
        raise B6QualificationError("causal dependency graph contains a cycle")
    return True


def validate_b6_decision(result: Mapping[str, Any], prerequisites: Mapping[str, Any],
                         graph: Mapping[str, Any]) -> bool:
    if result.get("decision") != EXPECTED_DECISION:
        raise B6QualificationError("B6 adjudication result is not a passing evidence decision")
    gates = result.get("scientific_side_effect_check", {})
    for key in ("mechanics_authorized", "forward_evolution_authorized", "dt_selected",
                "t1_created", "canonical_state_changed", "shellset_executed",
                "orbdata_mechanics_executed"):
        if gates.get(key) is not False:
            raise B6QualificationError(f"scientific safety gate must remain false: {key}")
    if result.get("first_dt_readiness") != "NOT_READY_FOR_FIRST_DT":
        raise B6QualificationError("B6 cannot mark first dt ready while exact blockers remain")
    rows = prerequisites.get("requirements", [])
    blocking = [row for row in rows if row.get("blocks_first_dt") is True]
    if not blocking:
        raise B6QualificationError("first-dt blocker set cannot be empty")
    declared = set(result.get("minimal_blocking_set", []))
    if not {row.get("requirement_id") for row in blocking}.issubset(declared):
        raise B6QualificationError("result omits an explicit first-dt blocker")
    validate_causal_graph(graph)
    return True


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(root: Path, logical: str) -> tuple[dict[str, Any], dict[str, Any]]:
    path = root / logical
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B6QualificationError(f"required source JSON is unreadable: {logical}") from exc
    return value, {"logical_path": logical, "sha256": _sha(path), "byte_size": path.stat().st_size}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                            text=True, check=False)
    if result.returncode:
        raise B6QualificationError(f"Git identity check failed: {' '.join(args)}")
    return result.stdout.strip()


def _check_manifest(root: Path, directory: str) -> list[dict[str, Any]]:
    manifest, _ = _json(root, f"{directory}/B5_ARTIFACT_MANIFEST.json")
    rows = manifest.get("artifacts", [])
    seen = set()
    for row in rows:
        rel = str(row.get("relative_path", ""))
        candidate = (root / directory / rel).resolve()
        if not rel or not candidate.is_file() or rel in seen:
            raise B6QualificationError(f"B5 manifest contains a missing or duplicate artifact: {rel}")
        if _sha(candidate) != row.get("sha256") or candidate.stat().st_size != row.get("byte_size"):
            raise B6QualificationError(f"B5 manifest artifact integrity mismatch: {rel}")
        seen.add(rel)
    return rows


def build_adjudication(root: Path) -> dict[str, Any]:
    root = root.resolve()
    branch, head = _git(root, "branch", "--show-current"), _git(root, "rev-parse", "HEAD")
    if branch != B6_BRANCH:
        raise B6QualificationError(f"expected B6 branch {B6_BRANCH}, found {branch}")
    inputs: dict[str, dict[str, Any]] = {}
    def read(name: str) -> dict[str, Any]:
        value, provenance = _json(root, name)
        inputs[name] = provenance
        return value

    b3 = read("outputs/r6_world_history_b3_t0_ingest/B3_T0_STATE_INVENTORY.json")
    b3_authority = read("outputs/r6_world_history_b3_t0_ingest/B3_T0_AUTHORITY_INVENTORY.json")
    b4 = read("outputs/r6_b4_plate_kinematics_qualification/B4_RESULT.json")
    b4_temporal = read("outputs/r6_b4_plate_kinematics_qualification/B4_TEMPORAL_SUPPORT.json")
    b4_gaps = read("outputs/r6_b4_plate_kinematics_qualification/B4_DEPENDENCY_GAPS.json")
    b5 = read("outputs/r6_b5_plate_support_topology_qualification/B5_RESULT.json")
    b5_support = read("outputs/r6_b5_plate_support_topology_qualification/B5_PLATE_SUPPORT.json")
    b5_prereq = read("outputs/r6_b5_plate_support_topology_qualification/B5_FIRST_DT_PREREQUISITES.json")
    b5_temporal = read("outputs/r6_b5_plate_support_topology_qualification/B5_TEMPORAL_CONSTRAINT_REGISTRY.json")
    motion = read("R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json")
    kin_manifest = read("R6_T0_INITIAL_KINEMATICS_MANIFEST.json")
    event_guard = read("R6_T0_FIRST_INTERVAL_EVENT_GUARD.json")
    boundary_rule = read("R6_SHARED_BOUNDARY_MOTION_AND_TOPOLOGY_CONTACT_RULE.json")
    boundary_law = read("R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json")
    continuum_guard = read("R6_T0_CONTINUUM_DEFORMATION_GUARD.json")
    topology_guard = read("R6_TOPOLOGY_CONTACT_GUARD.json")
    vector_manifest = read("R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    feg_manifest = read("R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json")
    kin_source = root / "scripts/r6_bind_t0_motion_prior_and_event_guard.py"
    boundary_source = root / "scripts/r6_bind_shared_boundary_topology_contact.py"
    if b3.get("state_count") != 14 or len(b3.get("domains", [])) != 14:
        raise B6QualificationError("B3 T0 semantic state inventory changed from 14 states/domains")
    if b4.get("decision") != "PASS_B4_PLATE_KINEMATICS_TEMPORAL_ADAPTER_QUALIFICATION":
        raise B6QualificationError("B4 qualification is not passing")
    if b5.get("decision") != "PASS_B5_PLATE_SUPPORT_TOPOLOGY_TEMPORAL_INTEGRATION":
        raise B6QualificationError("B5 qualification is not passing")
    if (b5.get("node_support_counts") != {"INTERIOR_PLATE": 62469,
            "BOUNDARY_SHARED": 1953, "JUNCTION_SHARED": 20, "UNKNOWN": 0}
            or b5.get("boundary_count") != 1983):
        raise B6QualificationError("B5 support or boundary census does not match current T0 authority")
    b5_source_commit = str(b5.get("qualified_source_commit", ""))
    if not b5_source_commit:
        raise B6QualificationError("B5 evidence does not identify its qualified source commit")
    _git(root, "merge-base", "--is-ancestor", b5_source_commit, head)
    b5_manifest_path = root / "outputs/r6_b5_plate_support_topology_qualification/B5_ARTIFACT_MANIFEST.json"
    manifest_rows = _check_manifest(root, "outputs/r6_b5_plate_support_topology_qualification")
    inputs["outputs/r6_b5_plate_support_topology_qualification/B5_ARTIFACT_MANIFEST.json"] = {
        "logical_path": "outputs/r6_b5_plate_support_topology_qualification/B5_ARTIFACT_MANIFEST.json",
        "sha256": _sha(b5_manifest_path), "byte_size": b5_manifest_path.stat().st_size}
    b5_code = b5.get("qualification_implementation", [])
    for item in b5_code:
        logical_path = str(item["logical_path"])
        path = root / logical_path
        if not path.is_file() or _sha(path) != item.get("sha256"):
            raise B6QualificationError(f"B5 implementation source hash changed: {logical_path}")
        committed_blob = _git(root, "rev-parse", f"HEAD:{logical_path}")
        worktree_blob = _git(root, "hash-object", logical_path)
        if committed_blob != worktree_blob:
            raise B6QualificationError(f"B5 implementation is not committed unchanged at current HEAD: {logical_path}")
    for path in (kin_source, boundary_source):
        if not path.is_file():
            raise B6QualificationError(f"reference-frame derivation source is missing: {path.name}")
        rel = path.relative_to(root).as_posix()
        inputs[rel] = {"logical_path": rel, "sha256": _sha(path), "byte_size": path.stat().st_size}

    support = b3["state_authorities"]
    domain_rows = []
    specs = {
        "physical_geography": ("STATIC_AUTHORITY", "Retain immutable T0 reference at 210 Ma; do not treat it as a held or evolved future surface."),
        "land_ocean": ("STATIC_AUTHORITY", "Retain the T0 map as an immutable anchor; any later moving-support transfer needs a separate rule."),
        "province_state": ("STATIC_AUTHORITY", "Retain T0 labels as anchor evidence; do not infer plate attachment or future movement."),
        "topography": ("STATIC_AUTHORITY", "Retain T0 topography only at its anchor; no vertical response or constancy law is inferred."),
        "tectonic_plate_partition": ("MUST_UPDATE_FIRST_STEP", "A physical plate-geometry transition changes support/topology; current boundary law blocks publishing it."),
        "plate_kinematics": ("DRIVER_ONLY", "The 210 Ma Euler vector is an instantaneous driver; it needs a separately governed positive-time segment."),
        "bathymetry": ("CAN_DEFER", "B3 support is UNKNOWN; it may remain unknown only while no seafloor/surface-response process consumes it."),
        "tectonic_kinematics_grid": ("DRIVER_ONLY", "B3 state remains UNKNOWN; B5 supplies a separate exact derived node-support map, not a temporal velocity field."),
        "boundary_classification": ("UNKNOWN_REQUIREMENT", "Geological/process type is UNKNOWN; the missing accommodation model must either consume types or justify a type-agnostic law."),
        "deep": ("CAN_DEFER", "B3 support is UNKNOWN and no mantle-force coupling is authorized; a prescribed temporal model would need to state this scope explicitly."),
        "climate": ("CAN_DEFER", "B3 support is UNKNOWN; retain its own clock and do not consume it in the first tectonic transition."),
        "hydrology": ("CAN_DEFER", "B3 support is UNKNOWN; retain its own clock and do not consume it in the first tectonic transition."),
        "weak_zone_state": ("UNKNOWN_REQUIREMENT", "Event guard lists weak-zone/eligibility inputs as blocking; T0 rift quiescence does not bound a later event."),
        "junction_physical_semantics": ("UNKNOWN_REQUIREMENT", "Twenty junction identities are known, but compatible positive-time junction response is unbound."),
    }
    for domain in b3["domains"]:
        classification, why = specs[domain]
        authority = support[domain]
        domain_rows.append({"domain": domain, "current_support_class": authority["support_class"],
            "current_authority_class": authority["authority_class"], "update_classification": classification,
            "first_step_role": ("ANCHOR_ONLY" if classification == "STATIC_AUTHORITY" else
                "DRIVER" if classification == "DRIVER_ONLY" else
                "CONDITIONAL_DOMAIN_CLOCK" if classification == "CAN_DEFER" else
                "BLOCKED_STATE_DEPENDENCY"),
            "change_required_to_become_a_temporal_state": classification == "MUST_UPDATE_FIRST_STEP",
            "authorized_hold_constant": False,
            "can_remain_unknown": classification == "CAN_DEFER",
            "first_step_requirement": why})

    graph = {"schema": "R6_B6_FIRST_STEP_CAUSAL_GRAPH_V1",
        "edge_orientation": "from consumer/output to its prerequisite for REQUIRES and DERIVES_FROM",
        "nodes": [
            {"node_id": "T0", "kind": "GOVERNED_STATE", "status": "AVAILABLE_ANCHOR_ONLY"},
            {"node_id": "KIN0", "kind": "FORCING", "status": "AVAILABLE_INSTANT_ONLY"},
            {"node_id": "SUPPORT0", "kind": "SPATIAL_SUPPORT", "status": "B5_DERIVED_GOVERNED"},
            {"node_id": "BOUNDARY0", "kind": "TOPOLOGY", "status": "AVAILABLE_T0_GRAPH_ONLY"},
            {"node_id": "KIN_LAW", "kind": "TEMPORAL_MODEL", "status": "MISSING_VALIDITY_AND_CHANGE_LAW"},
            {"node_id": "EVENT_BOUND", "kind": "TEMPORAL_CONSTRAINT", "status": "MISSING_POSITIVE_LEAD_TIME"},
            {"node_id": "BOUNDARY_RESPONSE", "kind": "PHYSICAL_MODEL", "status": "ZERO_CAPACITY_FAIL_CLOSED"},
            {"node_id": "JUNCTION_RESPONSE", "kind": "PHYSICAL_MODEL", "status": "MISSING_COMPATIBILITY_RULE"},
            {"node_id": "MESH_TRANSFER", "kind": "STATE_UPDATE_RULE", "status": "MISSING_VALIDITY_AND_TRANSFER_CRITERIA"},
            {"node_id": "DOMAIN_TRANSFER", "kind": "STATE_UPDATE_RULE", "status": "UNKNOWN_DEPENDENCY_POLICY"},
            {"node_id": "CANDIDATE_STATE", "kind": "WORLD_HISTORY_STATE", "status": "NOT_CREATED"},
            {"node_id": "CHECKPOINT", "kind": "WORLD_HISTORY_CHECKPOINT", "status": "SCHEMA_AVAILABLE_NOT_PUBLISHED"},
        ],
        "edges": [
            {"from": "SUPPORT0", "to": "T0", "kind": "DERIVES_FROM", "status": "QUALIFIED"},
            {"from": "SUPPORT0", "to": "BOUNDARY0", "kind": "DERIVES_FROM", "status": "QUALIFIED"},
            {"from": "KIN_LAW", "to": "KIN0", "kind": "REQUIRES", "status": "REQUIRED_NOT_SATISFIED"},
            {"from": "KIN_LAW", "to": "SUPPORT0", "kind": "REQUIRES", "status": "SATISFIED_B5"},
            {"from": "EVENT_BOUND", "to": "BOUNDARY0", "kind": "REQUIRES", "status": "REQUIRED_NOT_SATISFIED"},
            {"from": "BOUNDARY_RESPONSE", "to": "BOUNDARY0", "kind": "REQUIRES", "status": "REQUIRED_NOT_SATISFIED"},
            {"from": "BOUNDARY_RESPONSE", "to": "KIN0", "kind": "REQUIRES", "status": "INSTANTANEOUS_INPUT_AVAILABLE"},
            {"from": "JUNCTION_RESPONSE", "to": "BOUNDARY0", "kind": "REQUIRES", "status": "REQUIRED_NOT_SATISFIED"},
            {"from": "MESH_TRANSFER", "to": "SUPPORT0", "kind": "REQUIRES", "status": "CURRENT_SUPPORT_AVAILABLE"},
            {"from": "CANDIDATE_STATE", "to": "T0", "kind": "REQUIRES", "status": "REQUIRED"},
            {"from": "CANDIDATE_STATE", "to": "KIN_LAW", "kind": "REQUIRES", "status": "BLOCKED"},
            {"from": "CANDIDATE_STATE", "to": "EVENT_BOUND", "kind": "REQUIRES", "status": "BLOCKED"},
            {"from": "CANDIDATE_STATE", "to": "BOUNDARY_RESPONSE", "kind": "REQUIRES", "status": "BLOCKED_BY_ZERO_CAPACITY_POLICY"},
            {"from": "CANDIDATE_STATE", "to": "JUNCTION_RESPONSE", "kind": "REQUIRES", "status": "BLOCKED"},
            {"from": "CANDIDATE_STATE", "to": "MESH_TRANSFER", "kind": "REQUIRES", "status": "BLOCKED"},
            {"from": "CANDIDATE_STATE", "to": "DOMAIN_TRANSFER", "kind": "REQUIRES", "status": "BLOCKED_IF_SURFACE_FIELDS_ADVANCE"},
            {"from": "CHECKPOINT", "to": "CANDIDATE_STATE", "kind": "REQUIRES", "status": "ONLY_AFTER_VALID_STATE_EXISTS"},
        ]}
    validate_causal_graph(graph)

    positive_authority = {
        "status": "ABSENT_NO_POSITIVE_DURATION_AUTHORITY",
        "sources": [
            {"source": "R6_T0_INITIAL_KINEMATICS_MANIFEST", "class": "GOVERNED_AUTHORITY",
             "supports": "single 210 Ma model-realization anchor", "does_not_support": "a positive interval"},
            {"source": "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.motion_process", "class": "CANDIDATE_CONDITIONAL_MODEL",
             "supports": "constant initial Euler state only as a conditional segment", "does_not_support": "segment validity; explicitly not exercised"},
            {"source": "B4_TEMPORAL_SUPPORT", "class": "GOVERNED_QUALIFICATION_EVIDENCE",
             "supports": "instant-only; positive request rejected", "does_not_support": "any temporal interval"},
            {"source": "pyGPlates/PB2002/Earth5R", "class": "CANDIDATE_OR_REFERENCE_ONLY",
             "supports": "no ARCANA temporal authority", "does_not_support": "promotion to ARCANA input"},
        ],
        "stage_or_finite_rotations": "ABSENT_FROM_CURRENT_GOVERNED_R6_SOURCE_SET",
        "multiple_hard_kinematic_anchors": [210.0],
        "declared_angular_velocity_validity_intervals": [],
        "interpolation_rule": None,
    }
    frame = {
        "status": "UNIQUELY_DERIVABLE_INTERNAL_T0_COMPUTATIONAL_FRAME",
        "derivation": {"latlon_to_xyz": "x=cos(lat)cos(lon), y=cos(lat)sin(lon), z=sin(lat)",
            "velocity": "v=omega cross r", "basis": "+X at lon=0 equator; +Y at lon=+90 degrees; +Z north; right-handed XYZ by the stated cross-product convention",
            "radius_m": vector_manifest.get("parent_grid", {}).get("radius_m"),
            "longitude_bounds_deg": vector_manifest.get("parent_grid", {}).get("longitude_bounds_deg"),
            "latitude_bounds_deg": vector_manifest.get("parent_grid", {}).get("latitude_bounds_deg")},
        "evidence": [{"logical_path": "scripts/r6_bind_t0_motion_prior_and_event_guard.py", "lines": [24, 109, 110, 214], "sha256": _sha(kin_source)},
            {"logical_path": "scripts/r6_bind_shared_boundary_topology_contact.py", "lines": [33, 119, 189, 190], "sha256": _sha(boundary_source)},
            {"logical_path": "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json", "fact": "XYZ Euler components and synthetic gauge"}],
        "physical_frame_authority": "SYNTHETIC_NO_NET_ROTATION_GAUGE_ONLY; NOT_EARTH_FIXED/MANTLE/HOTSPOT",
        "external_frame_transform": "NOT_REQUIRED_FOR_CURRENT_INTERNAL_T0_DIAGNOSTIC; any external motion source must bind an explicit transform",
    }
    topology = {"status": "TOPOLOGY_EVENT_BOUND_REQUIRED",
        "full_long_term_calendar_before_first_dt": False,
        "minimum_required": "a governed positive lower bound on the earliest relevant event or an explicit interval-specific no-event authority for the candidate interval",
        "reason": "T0 quiescence does not imply positive post-T0 delay; current event guard has 30 UNKNOWN candidate pairs and null lead-time/horizon",
        "unknown_candidate_count": event_guard.get("unknown_candidate_count"),
        "positive_event_lead_time_lower_bound_ma": event_guard.get("positive_event_lead_time_lower_bound_ma"),
        "first_interval_decision": event_guard.get("decision"),
    }
    accommodation = {
        "requirement": "REQUIRED_BEFORE_FIRST_PHYSICAL_STEP",
        "basis": boundary_law.get("selected_semantics", {}).get("minimum_missing_authority"),
        "current_policy": boundary_law.get("selected_semantics", {}).get("opening"),
        "zero_capacity_policy": boundary_law.get("selected_semantics", {}).get("boundary_width"),
        "topology_guard": {"advance_allowed_segments": topology_guard.get("advance_allowed_segments"),
            "advance_allowed_with_accommodation_segments": topology_guard.get("advance_allowed_with_accommodation_segments"),
            "nonzero_relative_motion_segments": topology_guard.get("segments_with_nonzero_relative_motion"),
            "junction_status": topology_guard.get("junction_guard", {}).get("status")},
        "solver_requirement": "UNRESOLVED; a physically justified kinematic/interface model may satisfy this without ShellSet; no model has been selected",
        "shellset_decision": "SHELLSET_REQUIREMENT_UNRESOLVED",
    }
    blockers = [
        {"requirement_id": "B6_TEMPORAL_KINEMATIC_LAW", "quantity": "positive-duration motion segment validity/change law for 12 plate Euler rates", "why_needed": "anchor-only vectors do not define motion on Δt>0", "current_status": "ABSENT", "authority": "HARD_AUTHORITY_REQUIRED", "source": "B4 temporal support; motion-prior contract", "derivable": False, "tool_provider": "TEMPORAL_KINEMATIC_MODEL", "temporal_support": "positive interval", "spatial_support": "12 plates + B5 face/node support", "blocks_first_dt": True, "blocks_first_step": True, "requires_mechanics": False, "execution_target": "WINDOWS", "next_action": "AUTHORIAL_DECISION_AND_TEMPORAL_MODEL_DESIGN"},
        {"requirement_id": "B6_TOPOLOGY_EVENT_BOUND", "quantity": "positive lower bound on next relevant rift/topology event or interval-specific no-event authority", "why_needed": "the 30 candidate pairs remain UNKNOWN and T0 quiescence is not a future delay bound", "current_status": "NO_BOUND", "authority": "HARD_AUTHORITY_REQUIRED", "source": "R6_T0_FIRST_INTERVAL_EVENT_GUARD; topology contact guard", "derivable": False, "tool_provider": "TOPOLOGY_TRANSITION_MODEL", "temporal_support": "candidate interval/event horizon", "spatial_support": "30 adjacent plate-pair candidates; 20 junctions", "blocks_first_dt": True, "blocks_first_step": True, "requires_mechanics": False, "execution_target": "WINDOWS", "next_action": "TARGETED_EVENT_ELIGIBILITY_AND_LEAD_TIME_MODEL_ADJUDICATION"},
        {"requirement_id": "B6_BOUNDARY_JUNCTION_ACCOMMODATION", "quantity": "shared boundary and junction physical response to nonzero relative motion", "why_needed": "current governed zero-capacity rule blocks all 1,983 nonzero boundaries; junction velocities unbound", "current_status": "NO_PHYSICALLY_DEFENSIBLE_POSITIVE_ACCOMMODATION", "authority": "HARD_AUTHORITY_REQUIRED", "source": "R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT; R6_TOPOLOGY_CONTACT_GUARD", "derivable": False, "tool_provider": "BOUNDARY_ACCOMMODATION_MODEL", "temporal_support": "first interval and event handoffs", "spatial_support": "1,983 boundaries and 20 junctions", "blocks_first_dt": True, "blocks_first_step": True, "requires_mechanics": True, "execution_target": "WINDOWS_THEN_EITHER_ENGINE_QUALIFICATION", "next_action": "AUTHORIAL_MODEL_FAMILY_SELECTION_AND_TARGETED_MODEL_DESIGN"},
        {"requirement_id": "B6_MESH_STATE_TRANSFER", "quantity": "partition-preserving geometry update/remap criterion and support/material transfer for a candidate state", "why_needed": "rigid plate motion alone yields undefined shared nodes/gaps/overlap; current Jacobian/mesh guard is absent", "current_status": "ABSENT", "authority": "MODEL_OUTPUT_ACCEPTABLE_IF_QUALIFIED", "source": "R6_T0_CONTINUUM_DEFORMATION_GUARD; shared-boundary contact rule", "derivable": False, "tool_provider": "MESH_UPDATE_RULE", "temporal_support": "candidate interval and event stop", "spatial_support": "64,442 nodes; 128,880 triangles; 64,800 faces", "blocks_first_dt": True, "blocks_first_step": True, "requires_mechanics": "DEPENDS_ON_SELECTED_ACCOMMODATION_MODEL", "execution_target": "WINDOWS_FOR_CONTRACT; UBUNTU_ONLY_IF_HEAVY_SOLVER", "next_action": "DEFINE_TRANSFER_INVARIANTS_AFTER_BOUNDARY_MODEL_SELECTION"},
        {"requirement_id": "B6_NUMERICAL_VALIDITY_LIMITS", "quantity": "precommitted displacement/rotation/topology/Jacobian limits and any selected solver stability bound", "why_needed": "B4 dt formula has null input horizons; current deformation guard explicitly has no positive bound", "current_status": "NO_GOVERNED_VALUES", "authority": "NUMERICAL_REQUIREMENT_AFTER_MODEL_SELECTION", "source": "motion-prior numerical policy; continuum deformation guard", "derivable": False, "tool_provider": "OTHER_NUMERICAL_POLICY", "temporal_support": "first interval", "spatial_support": "mesh and boundary supports", "blocks_first_dt": True, "blocks_first_step": True, "requires_mechanics": "ONLY_IF_SOLVER_SELECTED", "execution_target": "WINDOWS_FOR_ADJUDICATION", "next_action": "PRECOMMIT_LIMITS_AND_QUALIFY_GUARD_AFTER_PHYSICAL_MODEL_IS_FIXED"},
    ]
    prereq_doc = {"schema": "R6_B6_FIRST_DT_PREREQUISITES_V1", "requirements": blockers,
        "first_dt_selection_inputs": [
            {"input": "kinematic segment validity horizon", "status": "MISSING", "value": None, "units": "years or Ma interval", "source": "none", "uncertainty": "UNBOUND", "blocking": True},
            {"input": "earliest event/topology lead-time bound", "status": "MISSING", "value": None, "units": "years or Ma interval", "source": "event guard", "uncertainty": "30 pair candidates UNKNOWN", "blocking": True},
            {"input": "boundary/junction accommodation validity and displacement limit", "status": "MISSING", "value": None, "units": "model-specific", "source": "none", "uncertainty": "UNBOUND", "blocking": True},
            {"input": "mesh/partition validity criterion", "status": "MISSING", "value": None, "units": "dimensionless Jacobian/geometry tolerance if selected", "source": "none", "uncertainty": "UNBOUND", "blocking": True},
            {"input": "kinematic reference frame", "status": "UNIQUELY_DERIVABLE_INTERNAL_T0_FRAME", "value": "synthetic NNR gauge; XYZ convention by producer equations", "units": "rad/year and m/year", "source": "current producer code + manifests", "uncertainty": "not Earth-fixed", "blocking": False},
            {"input": "solver stability/CFL bound", "status": "NOT_APPLICABLE_UNTIL_SOLVER_SELECTED", "value": None, "units": None, "source": "none", "uncertainty": "N/A", "blocking": False},
            {"input": "climate/hydrology coupling limit", "status": "ASYNCHRONOUS_NOT_IN_FIRST_TECTONIC_CLOCK", "value": None, "units": None, "source": "WORLD_HISTORY separate-clock capability", "uncertainty": "unknown domains remain unknown", "blocking": False},
        ]}
    domain_doc = {"schema": "R6_B6_T0_DOMAIN_UPDATE_MATRIX_V1", "domains": domain_rows,
        "inventory_state_count": b3["state_count"], "surface_fields_share_parent_payload": True,
        "hold_policy": "NO_DYNAMIC_DOMAIN_IS_DECLARED_CONSTANT; STATIC_AUTHORITY MEANS RETAIN T0 ANCHOR ONLY"}
    authority_floor = {"schema": "R6_B6_AUTHORITY_FLOOR_V1", "requirements": [
        {"requirement_id": row["requirement_id"], "minimum_authority": row["authority"],
         "software_is_scientific_authority": False} for row in blockers] + [
        {"requirement_id": "B6_FRAME_CONVENTION", "minimum_authority": "DERIVED_GOVERNED_ACCEPTABLE",
         "status": frame["status"], "software_is_scientific_authority": False},
    ]}
    unknown_policy = {"schema": "R6_B6_UNKNOWN_POLICY_V1",
        "can_remain_unknown_for_first_step": [
            {"quantity": "deep state", "condition": "first motion model is explicitly prescribed and does not claim mantle force balance"},
            {"quantity": "climate/hydrology/bathymetry", "condition": "remain separate-clock UNKNOWN/passive T0 references and are not consumed by first tectonic step"},
            {"quantity": "geological boundary type", "condition": "only if selected accommodation law is explicitly valid without typing; not true of current authority"},
        ],
        "block_first_step": [
            {"quantity": "positive-duration motion validity", "reason": "no segment interval law"},
            {"quantity": "boundary/junction accommodation", "reason": "current zero-capacity fail-closed contract and 20 unbound junction responses"},
            {"quantity": "event lead-time/topology bound", "reason": "unknown event eligibility and no positive lower bound"},
            {"quantity": "mesh/state transfer validity", "reason": "no partition-preserving update criterion"},
        ],
        "do_not_interpret_unknown_as_zero_or_absent": True}
    research = {"schema": "R6_B6_PROVIDER_RESEARCH_DECISIONS_V1", "decisions": [
        {"gap": "positive-duration kinematics", "next": ["AUTHORIAL_DECISION", "NEW_MODEL_DESIGN"], "repository_audit": "already establishes no positive interval", "external_research": "only targeted if the chosen model claims an empirical/geological basis", "engine_qualification": "after model authority exists"},
        {"gap": "event/topology horizon", "next": ["TARGETED_REPOSITORY_AUDIT", "NEW_MODEL_DESIGN", "AUTHORIAL_DECISION"], "external_research": "not needed to establish current absence; targeted input research only if adopting an external event provider", "engine_qualification": "not yet"},
        {"gap": "boundary and junction accommodation", "next": ["AUTHORIAL_DECISION", "NEW_MODEL_DESIGN"], "external_research": "targeted comparison only after choosing candidate physical family; existing B5/B6 authority already rejects universal transfer", "engine_qualification": "required after physical law and outputs are fixed; engine not selected"},
        {"gap": "mesh/state transfer", "next": ["TARGETED_REPOSITORY_AUDIT", "NEW_MODEL_DESIGN"], "external_research": "not initially", "engine_qualification": "qualify deterministic geometry/state invariants after model selection"},
        {"gap": "internal T0 frame", "next": ["NO_RESEARCH_EXISTING_CODE_SUFFICIENT"], "external_research": "none", "engine_qualification": "no separate frame qualification for internal T0 diagnostic"},
        {"gap": "climate/hydrology/surface coupling", "next": ["CAN_DEFER_TO_SEPARATE_DOMAIN_CLOCKS"], "external_research": "later only when those domains enter a causal transition", "engine_qualification": "not first tectonic step"},
    ]}
    execution = {"schema": "R6_B6_EXECUTION_TARGETS_V1", "tasks": [
        {"task": "authorial scope and temporal/boundary model adjudication", "target": "WINDOWS", "reason": "design/audit and small tests; no heavy runtime"},
        {"task": "B6 static qualification and regression", "target": "WINDOWS", "reason": "portable Python evidence only"},
        {"task": "future solver/NVHPC/native ShellSet qualification, if selected", "target": "UBUNTU_WORKSTATION", "reason": "native scientific build/runtime needed"},
        {"task": "large reconstruction, sweep or solver run, if authorized later", "target": "UBUNTU_WORKSTATION", "reason": "long-running CPU/RAM-intensive execution"},
    ], "heavy_execution_required_during_B6": False}
    b7 = {"schema": "R6_B6_B7_DECISION_V1",
        "decision": "B7_DECISION_BLOCKED_BY_MISSING_TEMPORAL_AUTHORITY",
        "boundary_response_needed_before_any_physical_step": True,
        "whether_numerical_mechanics_solver_is_required": "UNRESOLVED; no selected physical accommodation model",
        "shellset": accommodation["shellset_decision"],
        "reason": "A solver qualification cannot be scoped until positive-time motion/event bounds and a physical boundary/junction response law define required input/output semantics.",
        "future_narrow_contract_if_authorized": {"inputs": ["governed interval driver", "event horizon", "T0 mesh/partition/support identities", "boundary adjacency/relative motion", "selected accommodation and junction law", "material configuration if required"], "outputs": ["only selected boundary/junction response fields", "partition/mesh validity diagnostics", "deterministic support/state transfer evidence"], "no_outputs_assumed": ["stress", "strain", "fault slip", "traction", "full velocity field unless selected model requires them"]}}
    readiness = "NOT_READY_FOR_FIRST_DT"
    first_set = {"status": "CANDIDATE_SET_NOT_AUTHORIZED_WHILE_BLOCKED",
        "candidate_domains": ["tectonic_plate_partition", "plate_kinematics", "tectonic_kinematics_grid"],
        "required_supports": ["plate faces/nodes", "shared boundary topology", "junction identities"],
        "conditional_physical_response": ["boundary/junction accommodation", "mesh/state transfer"],
        "other_domains": "may retain independent T0 or UNKNOWN clocks only if not consumed; no dynamic hold is authorized",
        "reason": "these are the smallest causal tectonic components, but current temporal and physical response blockers prevent a first transition"}
    registry = {"schema": "R6_TEMPORAL_CONSTRAINT_REGISTRY_V2", "anchor": {"time_ma": 210.0, "authority": "GOVERNED_T0_INSTANT_ANCHOR"},
        "positive_duration_authority": "ABSENT", "known_forcing_intervals": [],
        "topology_event_bounds": {"known": [], "earliest_relevant_event_lower_bound_ma": None,
            "candidate_pair_count_unknown": event_guard.get("unknown_candidate_count")},
        "reference_frame": frame,
        "model_validity_bounds": [],
        "numerical_constraints": [{"name": "precommitted_dt_rule", "status": "MODEL_REQUIREMENT_INPUTS_MISSING", "value": None},
            {"name": "existing_rift_guard_years", "status": "DIAGNOSTIC_ONLY_NOT_A_DT", "value": continuum_guard.get("existing_rift_guard_years"), "is_legal_dt": continuum_guard.get("existing_rift_guard_is_legal_dt"), "positive_horizon_bound": continuum_guard.get("positive_horizon_bound")}],
        "unknown_intervals": "ALL_POSITIVE_DURATION_AFTER_210_MA",
        "future_required_constraints": [row["requirement_id"] for row in blockers],
        "dt_selected": False}
    graph["nodes"].extend([
        {"node_id": "FRAME0", "kind": "REFERENCE_FRAME", "status": frame["status"]},
        {"node_id": "REL_MOTION0", "kind": "DERIVED_INSTANT_DIAGNOSTIC", "status": "AVAILABLE_AT_210_MA_ONLY"},
    ])
    graph["edges"].extend([
        {"from": "REL_MOTION0", "to": "KIN0", "kind": "DERIVES_FROM", "status": "GOVERNED_T0_DERIVATION"},
        {"from": "REL_MOTION0", "to": "BOUNDARY0", "kind": "DERIVES_FROM", "status": "GOVERNED_T0_DERIVATION"},
        {"from": "CANDIDATE_STATE", "to": "FRAME0", "kind": "REQUIRES", "status": "UNIQUELY_DERIVABLE_INTERNAL_T0"},
        {"from": "BOUNDARY_RESPONSE", "to": "REL_MOTION0", "kind": "REQUIRES", "status": "INPUT_AVAILABLE_AT_ANCHOR"},
    ])
    validate_causal_graph(graph)
    result = {"schema": "R6_B6_ADJUDICATION_RESULT_V1", "decision": EXPECTED_DECISION,
        "qualified_source_commit": head, "branch": branch,
        "B5_qualified_source_commit": b5_source_commit,
        "B5_qualified_source_is_ancestor_of_current_HEAD": True,
        "B5_implementation_committed_unchanged_at_current_HEAD": True,
        "baseline_worktree_contains_uncommitted_B5_qualification": False,
        "B3_t0_inventory_count": b3["state_count"], "B4_decision": b4["decision"], "B5_decision": b5["decision"],
        "positive_duration_kinematic_authority": positive_authority["status"],
        "reference_frame_status": frame["status"], "topology_time_requirement": topology["status"],
        "boundary_mechanics_requirement": accommodation["requirement"], "shellset_decision": accommodation["shellset_decision"],
        "B7_decision": b7["decision"], "first_dt_readiness": readiness,
        "minimal_blocking_set": [row["requirement_id"] for row in blockers],
        "next_stage_recommendation": "AUTHORIZE_TARGETED_GAP_CLOSURE",
        "maximum_next_authorization": "AUTHORIZE_TARGETED_GAP_CLOSURE",
        "scientific_side_effect_check": GATES,
        "source_evidence": sorted(inputs.values(), key=lambda row: row["logical_path"]),
        "B5_manifest_artifact_count": len(manifest_rows)}
    return {"result": result, "graph": graph, "domains": domain_doc,
        "prerequisites": prereq_doc, "registry": registry, "authority_floor": authority_floor,
        "unknown_policy": unknown_policy, "research": research, "execution": execution,
        "b7": b7, "positive_authority": positive_authority, "frame": frame,
        "topology": topology, "accommodation": accommodation, "first_set": first_set,
        "inputs": sorted(inputs.values(), key=lambda row: row["logical_path"])}


def _manifest_artifact(path: Path, relative: str) -> dict[str, Any]:
    data = path.read_bytes()
    return {"relative_path": relative, "byte_size": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _human_report(data: Mapping[str, Any]) -> str:
    result = data["result"]
    focused = data.get("test_results")
    sections = [
        "# R6 B6 Dependency and Temporal-Gap Adjudication", "",
        f"Decision: **{result['decision']}**", "",
        "## A. Baseline", "",
        f"Branch `{result['branch']}`, source commit `{result['qualified_source_commit']}`. The committed B5 source qualification `{result['B5_qualified_source_commit']}` is an ancestor of this baseline; its implementation files and retained evidence were hash-checked against the current committed tree.", "",
        "## B. First-step causal graph", "",
        "T0, instantaneous forcing, and B5 spatial support are present. A positive-time candidate state requires a temporal segment, event bound, shared-boundary/junction accommodation, and geometry/state transfer policy. The dependency graph is machine-readable in `B6_FIRST_STEP_CAUSAL_GRAPH.json`.", "",
        "## C. Current T0 domain requirements", "",
        "B3 contains 14 semantic states. Plate partition is the state that must spatially transition; plate kinematics is a driver; B5 supplies derived grid/node support. Climate, hydrology, deep, and bathymetry remain UNKNOWN or separate-clock references only when not consumed. No domain is declared dynamically constant.", "",
        "## D. Positive-duration kinematic authority", "",
        "ABSENT. B4 qualifies only the 210 Ma instantaneous Euler anchor. The prior describes a constant first segment conditionally but explicitly says it was not exercised and has no validity/change horizon. No stage rotations, finite rotations, multiple anchors, or interpolation rule are governed.", "",
        "## E. Reference-frame adjudication", "",
        "The internal T0 computational axes are uniquely derivable from producer code: spherical `lat/lon` to XYZ and velocity `omega × r`, with +X at lon 0°, +Y at +90°, +Z north (right-handed by that cross-product convention). The gauge is synthetic NNR, not Earth-fixed/mantle/hotspot authority. No external-frame transform is authorized.", "",
        "## F. Topology-time requirements", "",
        "A full long-term event calendar is not required before the first interval, but a positive lower bound on the next relevant event—or explicit interval-specific no-event authority—is required. The 30 candidate plate pairs remain UNKNOWN and the current guard horizon is null.", "",
        "## G. Mechanics necessity", "",
        "A physical shared-boundary/junction accommodation response is required before any first physical step. Current governed policy is zero-capacity fail-closed; all 1,983 boundaries have nonzero relative motion, no segment may advance, and junction response is blocked. Whether that response needs a numerical solver is unresolved.", "",
        "## H. ShellSet decision", "",
        f"**{data['accommodation']['shellset_decision']}**. ShellSet is not required merely because it exists; no physical law or minimum solver-output contract has selected it. Legacy Earth5R BCS is not ARCANA authority.", "",
        "## I. External/provider/model gaps", "",
        "The minimum providers are a temporal kinematic model, event/topology bound, boundary/junction accommodation model, and mesh/state transfer validity rule. Provider research is targeted after authorial model-family selection; no provider search or installation occurred in B6.", "",
        "## J. First-step state semantics", "",
        "A future candidate needs plate geometry/partition, driver and support identities, shared boundary/junction response, support/state transfer, source provenance and uncertainty, and an event/forcing record. WORLD_HISTORY checkpoint/replay schema can retain those dependencies. No candidate state was created.", "",
        "## K. Temporal constraints", "",
        "Only the 210 Ma anchor is known. The existing 27,123.405-year rift guard is diagnostic and explicitly not a legal dt or positive horizon. No numerical threshold is supplied.", "",
        "## L. Multi-domain clocks", "",
        "WORLD_HISTORY supports distinct clocks. Climate and hydrology need not run on the tectonic clock if left UNKNOWN/passive and not consumed; no stale state may be represented as an updated simultaneous state.", "",
        "## M. Minimum active domain set", "",
        "Candidate set, not authorized: `tectonic_plate_partition`, `plate_kinematics`, and B5 `tectonic_kinematics_grid` support, plus boundary/junction accommodation and mesh transfer. Other domains enter only where the selected causal model consumes them.", "",
        "## N. Authority floors", "",
        "Positive-time motion, event bounds, and boundary accommodation need explicit hard authority. Deterministic support and the internal frame derivation may be derived from governed inputs. A qualified processor cannot substitute for scientific input authority.", "",
        "## O. UNKNOWN policy", "",
        "Deep, climate, hydrology and bathymetry may remain UNKNOWN only when outside the first transition's consumed inputs. Weak-zone/event eligibility and boundary/junction response cannot be treated as absent or zero under current guards.", "",
        "## P. Provider research decisions", "",
        "The next step is authorial decision and targeted model design, with narrowly scoped repository audits. External research is conditional on selecting a physical family. ShellSet/engine qualification follows only after its input/output contract is fixed.", "",
        "## Q. Windows/Ubuntu execution plan", "",
        "Windows: authority adjudication, model design, static adapter work and small tests. Ubuntu: later native solver/NVHPC qualification or genuinely heavy solver/reconstruction work only if selected and authorized. No heavy task is required now.", "",
        "## R. B7 decision", "",
        f"**{data['b7']['decision']}**. Mechanical boundary response is required, but solver necessity and exact outputs cannot be scoped before temporal and physical law authority exists.", "",
        "## S. First-dt readiness", "",
        "**NOT_READY_FOR_FIRST_DT**. B6 does not authorize dt, mechanics, T1 or evolution.", "",
        "## T. Exact blocking set", "",
        *[f"- `{row['requirement_id']}` — {row['quantity']}" for row in data["prerequisites"]["requirements"] if row["blocks_first_dt"]], "",
        "Scientific gates remain: runtime permission is limited to loading/consuming the governed ARCANA T0 runtime package; mechanics, dt, T1, canonical mutation and forward evolution remain false.", "",
    ]
    if focused:
        sections += [f"Validation: active R6 suite {focused['active_r6']['tests_passed']} passed; B6 focused tests {focused['focused_b6']['tests_passed']} passed; py_compile {focused['py_compile']}; JSON/manifest/path checks {focused.get('json_manifest_path_validation', 'PENDING')}; diff check {focused.get('diff_check', 'PENDING')}.", ""]
    return "\n".join(sections)


def run(root: Path, output_dir: Path) -> dict[str, Any]:
    data = build_adjudication(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    inputs = output_dir / "B6_INPUT_EVIDENCE.json"
    _write_json(inputs, {"schema": "R6_B6_INPUT_EVIDENCE_V1", "sources": data["inputs"],
        "source_commit": data["result"]["qualified_source_commit"],
        "B5_qualification_committed_in_source_baseline": True})
    result = data["result"]
    test_path = output_dir / "B6_TEST_RESULTS.json"
    test_results = json.loads(test_path.read_text(encoding="utf-8")) if test_path.is_file() else None
    data["test_results"] = test_results
    artifacts = {
        "B6_RESULT.json": result,
        "B6_FIRST_STEP_CAUSAL_GRAPH.json": data["graph"],
        "B6_DOMAIN_UPDATE_MATRIX.json": data["domains"],
        "B6_FIRST_DT_PREREQUISITES.json": data["prerequisites"],
        "B6_TEMPORAL_CONSTRAINT_REGISTRY.json": data["registry"],
        "B6_AUTHORITY_FLOOR.json": data["authority_floor"],
        "B6_UNKNOWN_POLICY.json": data["unknown_policy"],
        "B6_PROVIDER_RESEARCH_DECISIONS.json": data["research"],
        "B6_EXECUTION_TARGETS.json": data["execution"],
        "B6_B7_DECISION.json": data["b7"],
        "B6_POSITIVE_DURATION_AUTHORITY.json": data["positive_authority"],
        "B6_REFERENCE_FRAME_ADJUDICATION.json": data["frame"],
        "B6_TOPOLOGY_TIME_REQUIREMENT.json": data["topology"],
        "B6_FIRST_STEP_ACTIVE_DOMAIN_SET.json": data["first_set"],
    }
    for name, body in artifacts.items():
        _write_json(output_dir / name, body)
    (output_dir / "B6_INPUT_EVIDENCE.json").write_text(inputs.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    if test_results is not None:
        validate_b6_decision(result, data["prerequisites"], data["graph"])
    readme = "# R6 B6 adjudication package\n\nRead-only decision package for the minimum causal and temporal prerequisites before any first positive interval. It does not select dt or authorize evolution. See `B6_RESULT.json` and `docs/arcana/B6_DEPENDENCY_TEMPORAL_GAP_ADJUDICATION.md`.\n"
    (output_dir / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    report = _human_report(data)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8", newline="\n")
    retained = sorted([path for path in output_dir.iterdir() if path.is_file() and path.name != "B6_ARTIFACT_MANIFEST.json"] + [REPORT], key=lambda path: path.as_posix())
    entries = []
    for path in retained:
        try:
            rel = path.relative_to(output_dir).as_posix()
        except ValueError:
            rel = "../../docs/arcana/B6_DEPENDENCY_TEMPORAL_GAP_ADJUDICATION.md"
        entries.append(_manifest_artifact(path, rel))
    manifest = {"schema": "R6_B6_ARTIFACT_MANIFEST_V1", "artifacts": sorted(entries,
        key=lambda row: row["relative_path"]), "manifest_self_hash": "OMITTED_BY_POLICY"}
    _write_json(output_dir / "B6_ARTIFACT_MANIFEST.json", manifest)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()
    try:
        data = run(args.repository_root.resolve(), args.output_dir.resolve())
        print(json.dumps({"decision": data["result"]["decision"],
            "first_dt_readiness": data["result"]["first_dt_readiness"],
            "minimal_blocking_set": data["result"]["minimal_blocking_set"],
            "b7_decision": data["b7"]["decision"]}, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"B6_ADJUDICATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
