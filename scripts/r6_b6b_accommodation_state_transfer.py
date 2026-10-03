#!/usr/bin/env python3
"""Read-only adjudication of first-step plate accommodation and state transfer."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "r6/b6b-first-step-accommodation-state-transfer"
HEAD = "66ff83a8cf8b86b483c60a75b12d1da9594d1740"
OUT = ROOT / "outputs/r6_b6b_accommodation_state_transfer"
REPORT = ROOT / "docs/arcana/B6B_FIRST_STEP_ACCOMMODATION_STATE_TRANSFER.md"
DECISION = "PASS_B6B_FIRST_STEP_ACCOMMODATION_STATE_TRANSFER"
GATES = {
    "runtime_authorized": True,
    "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
    "mechanics_authorized": False,
    "forward_evolution_authorized": False,
    "dt_selected": False,
    "t1_created": False,
    "canonical_state_changed": False,
    "node_motion_executed": False,
    "topology_mutation_executed": False,
    "shellset_executed": False,
    "orbdata_mechanics_executed": False,
}

JSON_SOURCES = [
    "outputs/r6_b6a_positive_duration_authority/B6A_RESULT.json",
    "outputs/r6_b6a_positive_duration_authority/B6A_MOTION_LAW_ADJUDICATION.json",
    "outputs/r6_b6a_positive_duration_authority/B6A_TOPOLOGY_TEMPORAL_BOUND.json",
    "R6_T0_CANONICAL_PLATE_KINEMATICS.json",
    "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json",
    "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json",
    "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json",
    "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json",
    "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json",
    "R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json",
    "R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json",
    "R6_T0_CONTINUUM_DEFORMATION_GUARD.json",
    "R6_TOPOLOGY_CONTACT_GUARD.json",
    "R6_PHYSICAL_EVENT_MODEL_CONTRACT.json",
    "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_RESULT.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_PLATE_SUPPORT.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_TEMPORAL_VALIDITY.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_TOPOLOGY_EVENT_CONTRACT.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_NODE_PLATE_SUPPORT_MAP_V1.json",
    "outputs/r6_world_history_b3_t0_ingest/B3_T0_STATE_INVENTORY.json",
    "outputs/r6_world_history_b3_t0_ingest/B3_T0_RETENTION_MAP.json",
]


class B6BError(ValueError):
    pass


def _git(root: Path, *args: str) -> str:
    run = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                         text=True, check=False)
    if run.returncode:
        raise B6BError(f"git source identity check failed: {' '.join(args)}")
    return run.stdout.strip()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rigid_rotate(point: Sequence[float], matrix: Sequence[Sequence[float]]) -> tuple[float, float, float]:
    """Apply a supplied rigid transform; fixture helper only, no ARCANA data read."""
    if len(point) != 3 or len(matrix) != 3 or any(len(row) != 3 for row in matrix):
        raise B6BError("rigid transform requires one XYZ point and a 3x3 matrix")
    return tuple(sum(float(matrix[i][j]) * float(point[j]) for j in range(3)) for i in range(3))


def shared_coordinate_compatible(candidates: Sequence[Sequence[float]]) -> bool:
    """Exact fixture comparison: never averages, snaps, or picks an owner."""
    return bool(candidates) and all(tuple(x) == tuple(candidates[0]) for x in candidates[1:])


def validate_result(data: dict[str, Any]) -> bool:
    r = data["result"]
    if r.get("decision") != DECISION or r.get("qualified_source_commit") != HEAD:
        raise B6BError("B6B result/source identity invalid")
    gates = r.get("scientific_side_effect_check", {})
    if any(gates.get(k) is not False for k in (
            "mechanics_authorized", "forward_evolution_authorized", "dt_selected",
            "t1_created", "canonical_state_changed", "node_motion_executed",
            "topology_mutation_executed", "shellset_executed", "orbdata_mechanics_executed")):
        raise B6BError("B6B safety gate opened")
    if r.get("first_dt_status_after_B6B") != "NOT_READY_FOR_FIRST_DT":
        raise B6BError("first dt cannot be ready while state transfer/accommodation is blocked")
    if r.get("shellset_decision") != "SHELLSET_REQUIREMENT_STILL_UNRESOLVED":
        raise B6BError("B6B cannot select ShellSet without a governed physical model")
    return True


def adjudicate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    branch, head = _git(root, "branch", "--show-current"), _git(root, "rev-parse", "HEAD")
    if branch != BRANCH or head != HEAD:
        raise B6BError(f"expected {BRANCH}@{HEAD}, found {branch}@{head}")
    evidence: dict[str, Any] = {}
    source: dict[str, Any] = {}
    for logical in JSON_SOURCES:
        path = root / logical
        if not path.is_file():
            raise B6BError(f"required governed evidence is absent: {logical}")
        try:
            source[logical] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise B6BError(f"required evidence JSON is invalid: {logical}") from exc
        evidence[logical] = {"path": logical, "sha256": _sha(path), "byte_size": path.stat().st_size}

    b6a = source["outputs/r6_b6a_positive_duration_authority/B6A_RESULT.json"]
    b6a_motion = source["outputs/r6_b6a_positive_duration_authority/B6A_MOTION_LAW_ADJUDICATION.json"]
    b6a_topology = source["outputs/r6_b6a_positive_duration_authority/B6A_TOPOLOGY_TEMPORAL_BOUND.json"]
    kinematics = source["R6_T0_CANONICAL_PLATE_KINEMATICS.json"]
    rift = source["R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json"]
    census = source["R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json"]
    boundary_manifest = source["R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json"]
    finite = source["R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json"]
    deformation = source["R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json"]
    continuum = source["R6_T0_CONTINUUM_DEFORMATION_GUARD.json"]
    topology_guard = source["R6_TOPOLOGY_CONTACT_GUARD.json"]
    feg = source["R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"]
    b5 = source["outputs/r6_b5_plate_support_topology_qualification/B5_RESULT.json"]
    b5_support = source["outputs/r6_b5_plate_support_topology_qualification/B5_PLATE_SUPPORT.json"]
    b5_temporal = source["outputs/r6_b5_plate_support_topology_qualification/B5_TEMPORAL_VALIDITY.json"]
    node_map = source["outputs/r6_b5_plate_support_topology_qualification/B5_NODE_PLATE_SUPPORT_MAP_V1.json"]
    b3 = source["outputs/r6_world_history_b3_t0_ingest/B3_T0_STATE_INVENTORY.json"]
    retention = source["outputs/r6_world_history_b3_t0_ingest/B3_T0_RETENTION_MAP.json"]

    if b6a.get("decision") != "PASS_B6A_POSITIVE_DURATION_AUTHORITY_ADJUDICATION":
        raise B6BError("B6A authority result is not passing")
    if b5.get("decision") != "PASS_B5_PLATE_SUPPORT_TOPOLOGY_TEMPORAL_INTEGRATION":
        raise B6BError("B5 spatial support qualification is not passing")
    if b5_support.get("node_count") != 64442 or boundary_manifest.get("boundary_count") != 1983 or boundary_manifest.get("junction_count_degree_ge_3") != 20:
        raise B6BError("B5/T0 support cardinality changed")
    if b5.get("node_support_counts") != {"INTERIOR_PLATE": 62469, "BOUNDARY_SHARED": 1953, "JUNCTION_SHARED": 20, "UNKNOWN": 0}:
        raise B6BError("B5 node support counts changed")
    if b6a.get("topology_temporal_bound_status") != "NO_POSITIVE_BOUND" or b6a.get("first_dt_status_after_B6A") != "NOT_READY_FOR_FIRST_DT":
        raise B6BError("B6A topology/dt status changed; re-adjudicate B6B")
    if finite.get("finite_step_status_counts") != {"BLOCKED": 1983} or finite.get("junction_status_counts") != {"BLOCKED": 20}:
        raise B6BError("current finite-step boundary/junction guard changed")
    if topology_guard.get("global_topology_guard_horizon_years") is not None or topology_guard.get("first_positive_dt_authorized") is not False:
        raise B6BError("topology guard now supplies a positive step; revise this adjudication")
    if deformation.get("decision") != "NO_PHYSICALLY_DEFENSIBLE_POSITIVE_ACCOMMODATION_FOUND":
        raise B6BError("shared boundary physical policy changed")
    if rift.get("first_interval_contract_authorized") is not False and rift.get("numerical_policy", {}).get("first_interval_contract_authorized") is not False:
        raise B6BError("rift law execution gate changed")

    mesh = feg.get("canonical_mesh", {})
    # The production FEG is a separately derived runtime-frame artifact. Its
    # normalized bytes/hash are expected to differ from the canonical mesh
    # because the governed runtime coordinate-frame rotation is applied.
    # Compare cardinality here; preserve and report both identities distinctly.
    if mesh.get("node_count") != 64442 or mesh.get("triangle_count") != 128880:
        raise B6BError("canonical FEG mesh cardinality changed")

    fixture_matrices = {
        "identity": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        "quarter_turn_z": ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
        "half_turn_z": ((-1, 0, 0), (0, -1, 0), (0, 0, 1)),
    }
    fixture_point = (1.0, 0.0, 0.0)
    interior_out = rigid_rotate(fixture_point, fixture_matrices["quarter_turn_z"])
    boundary_candidates = [rigid_rotate(fixture_point, fixture_matrices[name]) for name in ("identity", "half_turn_z")]
    junction_candidates = [rigid_rotate(fixture_point, fixture_matrices[name]) for name in fixture_matrices]
    fixtures = {
        "schema": "R6_B6B_SYNTHETIC_FIXTURE_QUALIFICATION_V1",
        "authority": "FIXTURE_ONLY; no ARCANA coordinates, rates, duration, or topology used",
        "rigid_interior": {"source_xyz": fixture_point, "supplied_transform": "quarter_turn_z", "candidate_xyz": interior_out,
            "result": "DETERMINISTIC_RIGID_COORDINATE_TRANSFER", "mechanics_used": False},
        "two_plate_boundary": {"source_xyz": fixture_point, "candidate_positions_by_plate": boundary_candidates,
            "single_shared_coordinate_compatible": shared_coordinate_compatible(boundary_candidates),
            "result": "UNRESOLVED_REQUIRES_PHYSICAL_MODEL", "owner_assigned": False, "average_snap_or_slip_invented": False},
        "triple_junction": {"source_xyz": fixture_point, "candidate_positions_by_incident_plate": junction_candidates,
            "single_shared_coordinate_compatible": shared_coordinate_compatible(junction_candidates),
            "result": "UNRESOLVED_REQUIRES_JUNCTION_MODEL", "owner_assigned": False, "least_squares_or_average_used": False},
        "candidate_remesh": {"fixture_only": True, "result": "BLOCKED_WITHOUT_TOPOLOGY_EVENT_AND_PARENT_LINEAGE_CONTRACT", "remesh_executed": False},
        "missing_accommodation": {"fixture_only": True, "result": "FAIL_CLOSED_NO_CANDIDATE_STATE", "fallback": "NONE"},
    }

    transformations = {
        "schema": "R6_B6B_FIRST_STEP_TRANSFORMATIONS_V1",
        "transformations": [
        {"item": "strictly interior node coordinates", "classification": "RIGID_KINEMATIC_TRANSFER", "status": "CONDITIONAL_RULE; CARTESIAN_ACTION_CONVENTION_MUST_BE_EXPLICIT", "rule": "x_candidate = R(omega_plate, elapsed_time) x_T0 in the declared internal gauge; requires governed plate ID, T0 coordinate, an interval inside the conditional first segment, and an explicit/verified mapping from governed Euler-vector axes to coordinate rotation action", "frame_orientation_evidence": "B5 reference-frame evidence says Cartesian axis handedness is not separately declared; no sign/axis transform is inferred here", "no_interpolation": True},
            {"item": "face geometry whose nodes all have the same single-plate support", "classification": "DETERMINISTIC_GEOMETRIC_TRANSFER", "status": "CONDITIONAL_ON_TOPOLOGY_AND_SEGMENT_GUARDS", "rule": "apply the same plate rigid transform to each face vertex; preserve face connectivity/identity", "no_remesh": True},
            {"item": "two-plate boundary-shared node", "classification": "REQUIRES_PHYSICAL_MODEL", "status": "BLOCKED", "reason": "set-valued support has no single transformed coordinate when incident plate transforms differ; B5 assigns no owner and all 1,983 boundary segments are blocked"},
            {"item": "junction-shared node", "classification": "REQUIRES_PHYSICAL_MODEL", "status": "BLOCKED", "reason": "degree-three incidence has no governed common coordinate, residual allocation, or compatible junction law; all 20 junctions blocked"},
            {"item": "connectivity/topology identity", "classification": "UNKNOWN", "status": "NO_TOPOLOGY_HOLD_AUTHORITY", "reason": "no positive topology bound or invariance interval"},
            {"item": "plate and boundary support membership", "classification": "CAN_DEFER", "status": "REFERENCE_ONLY_AT_T0", "reason": "can remain a T0 reference; using it as next-state membership requires an explicit topology-hold contract"},
            {"item": "physical field transport/remapping", "classification": "UNKNOWN", "status": "MODEL_REQUIRED", "reason": "no governed advection, material attachment, remap, or interpolation rule for the full B3 field inventory"},
            {"item": "system-memory transfer", "classification": "UNKNOWN", "status": "REQUIRED_BY_B0_G_BUT_FIELD_POLICY_INCOMPLETE", "reason": "B0-G forbids discarding required SYSTEM_MEMORY; domain adapter has not supplied field-by-field reconstruction/update rules"},
            {"item": "provenance, event, replay and checkpoint records", "classification": "DETERMINISTIC_GEOMETRIC_TRANSFER", "status": "REQUIRED_IF_A_CANDIDATE_STATE_IS_AUTHORIZED", "reason": "record source state, forcing/law IDs, uncertainty, support/topology identities, replay recipe and checkpoint lineage; none created in B6B"},
        ],
    }
    boundary = {
        "schema": "R6_B6B_BOUNDARY_ACCOMMODATION_V1",
        "support": {"boundary_segments": boundary_manifest.get("boundary_count"), "adjacent_plate_pairs": boundary_manifest.get("plate_pair_count"), "boundary_shared_nodes": 1953, "all_segments_with_nonzero_relative_motion": topology_guard.get("segments_with_nonzero_relative_motion")},
        "geometric_accommodation": "REQUIRES_A_GOVERNED_SHARED_INTERFACE_COORDINATE_OR_FINITE_DEFORMATION_TRANSFER_RULE",
        "mechanical_accommodation": "REQUIRED_UNDER_CURRENT_ZERO_CAPACITY_FAIL_CLOSED_POLICY_BEFORE_A_PHYSICAL_NEXT_STATE",
        "selected_rule": deformation.get("selected_semantics", {}).get("centerline_velocity"),
        "selected_width": deformation.get("selected_semantics", {}).get("boundary_width"),
        "geological_type_and_polarity": "UNKNOWN_NOT_ASSIGNABLE_FROM_RELATIVE_VELOCITY_ALONE",
        "permitted_now": "retain the shared interface and kinematic diagnostics as immutable T0 evidence only",
        "forbidden_fallbacks": ["single-plate ownership", "midpoint or least-squares motion", "averaging", "snapping", "duplicating nodes as an implicit fault", "zero-width residual ledger presented as an evolved state"],
        "decision": "BLOCKING_NO_BOUND_PHYSICAL_OR_GEOMETRIC_ACCOMMODATION",
    }
    junction = {
        "schema": "R6_B6B_JUNCTION_ADJUDICATION_V1",
        "count": 20,
        "support": "degree >= 3; set-valued incident plate IDs and stable T0 junction IDs",
        "current_status": "BLOCKED",
        "canonical_velocity": "UNBOUND",
        "least_squares_solution": "NOT_RUN_NO_BOUNDARY_TYPES_OR_RESIDUAL_ALLOCATION_RULE",
        "needed_model": ["compatibility of all incident boundary laws", "shared coordinate or explicit multi-branch geometry", "residual allocation/finite zone or event handoff", "junction identity and lineage across any remesh"],
        "arbitrary_owner_or_velocity": False,
        "decision": "BLOCKING_NO_GOVERNED_JUNCTION_RESPONSE",
    }
    topology_hold = {
        "schema": "R6_B6B_TOPOLOGY_HOLD_CONTRACT_V1",
        "decision": "EXPLICIT_TOPOLOGY_INVARIANCE_MODEL_REQUIRED",
        "current_status": "NOT_GOVERNED; NO_POSITIVE_BOUND",
        "minimum_requirements": ["declare fixed plate IDs, face assignments, boundary adjacency, junction incidence and IDs over a stated interval", "define event eligibility and guards for split/merge/create/terminate/boundary birth/death/adjacency/junction reassignment", "provide a positive event lead-time lower bound or interval-specific proof/authority of invariance", "stop/reject before an unhandled transition and retain parent-child lineage if transition occurs"],
        "absence_of_event_records_is_proof_of_invariance": False,
        "conditional_rift_horizon_years": census.get("global_event_guard", {}).get("earliest_model_activation_elapsed_years"),
        "rift_horizon_is_topology_bound": False,
    }
    mesh_transfer = {
        "schema": "R6_B6B_MESH_STATE_TRANSFER_V1",
        "t0_mesh": {"node_count": mesh.get("node_count"), "triangle_count": mesh.get("triangle_count"), "fault_count": mesh.get("fault_count"), "canonical_normalized_sha256": mesh.get("normalized_sha256"), "production_runtime_normalized_sha256": feg.get("production_feg", {}).get("normalized_sha256"), "runtime_hash_is_distinct_by_governed_frame_transform": feg.get("production_feg", {}).get("normalized_sha256") != mesh.get("normalized_sha256")},
        "b5_plate_faces": 64800,
        "node_support": b5.get("node_support_counts"),
        "field_inventory": feg.get("nodal_fields"),
        "world_history_boundary": "FEG/runtime package is derived runtime support and is discarded from B3 canonical minimal-state ingest; no dynamic FEG remap is authorized.",
        "items": [
            {"item": "coordinates", "status": "RIGIDLY_TRANSFORMED", "scope": "single-plate interiors only, conditional on first-segment model; shared boundary/junction coordinates BLOCKED"},
            {"item": "connectivity", "status": "UNCHANGED_REFERENCE", "scope": "T0 mesh identity only; cannot assert next-state connectivity without topology-hold authority"},
            {"item": "plate membership", "status": "UNCHANGED_REFERENCE", "scope": "T0 support map only; candidate next membership needs topology hold or event remap"},
            {"item": "boundary/junction membership", "status": "UNKNOWN", "scope": "IDs/incidence valid at T0; no future update/lineage rule"},
            {"item": "field values", "status": "UNKNOWN", "scope": "no governed transport/advection/interpolation for B3 states or FEG nodal runtime fields"},
            {"item": "system memory", "status": "TRANSFER_REQUIRED_POLICY_UNKNOWN", "scope": "B0-G SYSTEM_MEMORY may not be discarded; B3 producer adapter is reference-only"},
        ],
        "interpolation": "NOT_AUTHORIZED; no nearest-neighbor, barycentric, conservative remap, snapping, or grid interpolation rule found",
        "remeshing": "BLOCKED; no deterministic remesh plus ID lineage/state transfer contract",
        "candidate_mesh_created": False,
    }
    retention_items = retention.get("items", [])
    memory = {
        "schema": "R6_B6B_SYSTEM_MEMORY_TRANSFER_V1",
        "generic_rule": "B0-G: SYSTEM_MEMORY cannot be DISCARD; future-dependent values survive even if not directly queried.",
        "producer_policy_status": "REVIEW_REQUIRED_FOR_SCIENTIFIC_MINIMALITY; adapter boundary reference-only, no governed field arrays copied",
        "retention_map": retention_items,
        "field_dispositions": [
            {"field": "T0 physical_geography/land_ocean/province_state/topography payload", "current_action": "MATERIALIZE", "candidate_next_state": "REFERENCE_IMMUTABLE_T0_ONLY_UNLESS_A_RESPONSE_MODEL_REQUIRES_NEW_VALUES", "advect_or_copy_rule": "NOT_BOUND"},
            {"field": "T0 tectonic_plate_partition payload", "current_action": "DERIVED_SUPPORTED_SYSTEM_MEMORY", "candidate_next_state": "NEW_PARTITION_REQUIRED_FOR_TOPOLOGY_CHANGE; otherwise T0 reference only", "transfer_rule": "BLOCKED_BY_TOPOLOGY_HOLD_OR_EVENT_CONTRACT"},
            {"field": "T0 plate kinematics", "current_action": "STATIC SYSTEM_MEMORY", "candidate_next_state": "reference as driver through conditional first segment", "transfer_rule": "no renewal beyond first segment"},
            {"field": "B5 node-to-plate support", "current_action": "DERIVED_T0_SUPPORT", "candidate_next_state": "retain parent support identity; recompute only under authorized mesh/topology adapter", "transfer_rule": "no next-state remap exists"},
            {"field": "rift cumulative opening progress", "current_action": "zero T0 initial progress under authorial rift law; source of truth only", "candidate_next_state": "update would be memory and must persist; no substate or advance is authorized", "transfer_rule": "law exists but geometry accommodation and execution remain blocked"},
            {"field": "shortening/slip/damage/weakness/junction response", "current_action": "NOT_MATERIALIZED or UNKNOWN", "candidate_next_state": "UNKNOWN; cannot initialize as zero or discard if later law depends on it", "transfer_rule": "requires model-specific authority"},
        ],
        "no_memory_discarded": True,
    }
    numerical = {
        "schema": "R6_B6B_NUMERICAL_CONSTRAINTS_V1",
        "constraints": [
            {"constraint": "maximum angular displacement / rotation", "classification": "MODEL_VALUE_REQUIRED", "current_value": None, "reason": "no precommitted limit in current T0/B6A law"},
            {"constraint": "maximum node displacement or fraction of local edge length", "classification": "MODEL_VALUE_REQUIRED", "current_value": None, "reason": "no geometry accuracy/deformation bound"},
            {"constraint": "boundary crossing/gap/overlap rejection", "classification": "MODEL_VALUE_REQUIRED", "current_value": None, "reason": "current topology guard has no positive horizon; shared interfaces have no accommodation law"},
            {"constraint": "mesh orientation/inversion/Jacobian criterion", "classification": "MODEL_VALUE_REQUIRED", "current_value": None, "reason": "continuum guard reports minimum_jacobian=null and no precommitted criterion"},
            {"constraint": "remesh threshold and lineage policy", "classification": "MODEL_VALUE_REQUIRED", "current_value": None, "reason": "no deterministic remeshing/state transfer contract"},
            {"constraint": "topology/event stop bound", "classification": "MODEL_VALUE_REQUIRED", "current_value": None, "reason": "no topology invariant interval/event-time authority"},
            {"constraint": "rift activation horizon", "classification": "GOVERNED_VALUE_AVAILABLE", "current_value_years": census.get("global_event_guard", {}).get("earliest_model_activation_elapsed_years"), "role": "conditional rift-process event boundary only; not dt, topology bound, or solver stability bound"},
            {"constraint": "solver stability bound", "classification": "SOLVER_DEPENDENT", "current_value": None, "reason": "no solver selected; may be not required if a later non-solver law is authorized"},
            {"constraint": "event localization/restart tolerance", "classification": "SOLVER_DEPENDENT", "current_value": None, "reason": "rift law requires stop/localize but explicitly leaves solver-specific tolerance unbound"},
        ],
    }
    shellset = {
        "schema": "R6_B6B_SHELLSET_DECISION_V1",
        "decision": "SHELLSET_REQUIREMENT_STILL_UNRESOLVED",
        "why": "physical boundary/junction response is required, but current authority does not establish that it must be computed by ShellSet or any numerical mechanics solver; a different explicit physical law may be selected later.",
        "exact_outputs_if_a_future_law_selects_a_solver": "NOT_SCOPABLE_UNTIL_LAW_AND_REQUIRED_OUTPUTS_ARE_SELECTED",
        "currently_authorized_outputs": [],
    }
    b7 = {
        "schema": "R6_B6B_B7_CONTRACT_V1",
        "status": "NOT_READY_TO_QUALIFY_A_MECHANICS_SOLVER",
        "execution_authorized": False,
        "scope_if_later_selected": "only the selected boundary/junction response and mesh/state validity contract; not generic mechanics",
        "inputs_pending_authority": ["first-segment temporal contract and its validity horizon", "T0 mesh/plate-support/boundary/junction identities", "selected boundary/geological model and parameters", "topology-hold/event guard", "field/memory transfer contract"],
        "outputs_to_scope_after_model_selection": ["only selected boundary/junction displacement or velocity response", "junction compatibility residuals if required", "mesh validity diagnostics against precommitted thresholds", "deterministic provenance/replay evidence"],
        "units_and_acceptance_thresholds": "MODEL_DEPENDENT_AND_NOT_YET_GOVERNED",
        "solver_identity": None,
        "candidate_shellset": "NOT_SELECTED",
        "execution_target_if_expensive_native_solver_is_eventually_required": "UBUNTU_WORKSTATION",
        "current_next_action": "AUTHORIAL_PHYSICAL_MODEL_DECISION_BEFORE_B7_SCOPING",
    }
    candidate = {
        "schema": "R6_B6B_FIRST_STEP_CANDIDATE_STATE_CONTRACT_V1",
        "status": "CONTRACT_ONLY_NO_CANDIDATE_STATE_CREATED",
        "requires": ["source T0 state IDs/hashes", "conditional first-segment forcing ID and model identity", "supported node/face/boundary/junction parent identities", "topology hold or explicit topology event record", "physical boundary/junction response and mesh/state-transfer rule", "field-by-field SYSTEM_MEMORY retention/reconstruction", "uncertainty and provider provenance", "WorldHistory state/provenance/event/forcing records", "checkpoint plus replay recipe"],
        "references_unchanged_t0": ["physical_geography", "land_ocean", "province_state", "topography", "T0 plate kinematics", "parent mesh/support identities"],
        "new_values_required_if_transition_executes": ["plate interior coordinates", "boundary/junction coordinates or explicit accommodation state", "topology/support only if event changes it", "any dependent physical fields selected by the response model", "cumulative opening memory if advanced"],
        "cannot_claim": ["unchanged future fields without a hold law", "same connectivity without topology validity", "single owner at shared nodes", "interpolated material IDs", "unrecorded state-memory loss"],
        "not_created": True,
    }
    blockers = [
        {"blocker": "positive-duration kinematics", "status": "PARTIALLY_CLOSED", "reason": "conditional constant-T0 first segment exists; not executable and has no renewal law/numerical validity"},
        {"blocker": "topology/event bound", "status": "BLOCKING", "reason": "rift horizon is not topology bound; no invariance interval or topology-event calendar"},
        {"blocker": "boundary/junction accommodation", "status": "BLOCKING", "reason": "all 1,983 segments and 20 junctions fail closed under unbound physical response"},
        {"blocker": "mesh/state transfer", "status": "BLOCKING", "reason": "only single-plate interior rigid transform is specified; shared support and fields lack transfer rules"},
        {"blocker": "numerical/model validity", "status": "BLOCKING", "reason": "no displacement, rotation, mesh-validity or solver-specific thresholds"},
    ]
    first_dt_inputs = {
        "schema": "R6_B6B_FIRST_DT_INPUTS_V1",
        "inputs": [
            {"name": "T0 angular rates", "status": "GOVERNED_AT_210_MA", "value": "12 Euler vectors", "role": "driver"},
            {"name": "first-segment motion law", "status": "CONDITIONAL_GOVERNED_MODEL", "value": "constant T0 Euler state through first segment only", "role": "kinematic validity"},
            {"name": "segment renewal horizon", "status": "UNKNOWN_AFTER_FIRST_SEGMENT", "value": None, "role": "blocking"},
            {"name": "rift activation bound", "status": "CONDITIONAL_GOVERNED_MODEL_BOUND", "value_years": census.get("global_event_guard", {}).get("earliest_model_activation_elapsed_years"), "role": "event stop only; not dt or topology bound"},
            {"name": "topology invariance/event bound", "status": "UNKNOWN", "value": None, "role": "blocking"},
            {"name": "boundary/junction accommodation validity", "status": "UNKNOWN", "value": None, "role": "blocking"},
            {"name": "mesh/state transfer validity", "status": "UNKNOWN", "value": None, "role": "blocking"},
            {"name": "displacement/rotation/Jacobian thresholds", "status": "UNKNOWN", "value": None, "role": "blocking"},
            {"name": "solver stability", "status": "SOLVER_DEPENDENT", "value": None, "role": "not applicable until solver choice"},
        ],
        "dt_selected": False,
    }
    execution = {
        "schema": "R6_B6B_EXECUTION_TARGETS_V1",
        "tasks": [
            {"task": "authorial boundary/junction response and topology-hold model decision", "target": "WINDOWS", "heavy": False},
            {"task": "mesh/state transfer contract plus small synthetic tests", "target": "WINDOWS", "heavy": False},
            {"task": "native solver qualification if selected after model authority", "target": "UBUNTU_WORKSTATION", "heavy": True, "authorized_now": False},
        ],
        "heavy_execution_during_B6B": False,
    }
    result = {
        "schema": "R6_B6B_RESULT_V1", "decision": DECISION, "branch": branch,
        "qualified_source_commit": head,
        "first_step_transformation_inventory": transformations["transformations"],
        "interior_rigid_transfer_status": "CONDITIONAL_RIGID_TRANSFER_NO_MECHANICS_FOR_SINGLE_PLATE_INTERIORS; COORDINATE_ACTION_CONVENTION_MUST_BE_EXPLICIT",
        "boundary_accommodation_status": boundary["decision"],
        "junction_accommodation_status": junction["decision"],
        "boundary_geological_type_requirement": "UNKNOWN_CAN_REMAIN_ONLY_IF_LATER_SELECTED_LAW_PROVES_TYPE_AGNOSTIC; CURRENTLY_BLOCKS_MODEL_SELECTION_FOR_TYPE_DEPENDENT_RESPONSE",
        "topology_hold_contract": topology_hold["decision"],
        "mesh_state_transfer_status": "PARTIAL_INTERIOR_ONLY; GLOBAL_CANDIDATE_TRANSFER_BLOCKED",
        "system_memory_transfer_status": "REQUIRED_BY_B0_G_BUT_FIELD_POLICY_INCOMPLETE",
        "census_v3_horizon_role": "CONDITIONAL_RIFT_ACTIVATION_EVENT_BOUND_ONLY_NOT_DT_OR_TOPOLOGY_BOUND",
        "shellset_decision": shellset["decision"],
        "b7_status": b7["status"],
        "b7_execution_target": b7["execution_target_if_expensive_native_solver_is_eventually_required"],
        "blocker_status_after_B6B": blockers,
        "first_dt_status_after_B6B": "NOT_READY_FOR_FIRST_DT",
        "maximum_next_authorization": "AUTHORIZE_TARGETED_MODEL_DECISION",
        "production_source_changes": False,
        "scientific_side_effect_check": GATES,
    }
    data = {"result": result, "transformations": transformations, "fixtures": fixtures,
            "boundary": boundary, "junction": junction, "topology_hold": topology_hold,
            "mesh_transfer": mesh_transfer, "memory": memory, "numerical": numerical,
            "shellset": shellset, "b7": b7, "candidate": candidate,
            "blockers": {"schema": "R6_B6B_BLOCKER_STATUS_V1", "blockers": blockers},
            "first_dt_inputs": first_dt_inputs, "execution": execution,
            "sources": sorted(evidence.values(), key=lambda x: x["path"])}
    validate_result(data)
    return data


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _report(d: dict[str, Any]) -> str:
    r = d["result"]
    lines = [
        "# R6 B6B First-Step Accommodation and State Transfer", "",
        f"Decision: **{r['decision']}**", "",
        "## A. Baseline and authority", "",
        f"Qualified source commit `{r['qualified_source_commit']}`. This is a read-only adjudication. T0 is 210 Ma; B5 supplies 64,800 plate faces, 64,442 node supports (62,469 interior, 1,953 boundary-shared, 20 junction-shared), 1,983 boundaries and 20 degree-three junctions.", "",
        "## B. Rigid interiors", "",
        "A strictly single-plate interior point/face admits a rigid-transfer rule, applying one transform by plate ID and preserving face identity/connectivity. No mechanics solver or interpolation is needed for that limited geometric operation. It remains conditional: B5 says Cartesian axis handedness is not separately declared, so the mapping from Euler-vector axes to coordinate rotation action must be made explicit before applying it. No ARCANA coordinates were transformed.", "",
        "## C. Shared boundaries and junctions", "",
        "The B5 node support is set-valued and assigns no owner. B5 and the finite-step census report nonzero relative motion on all 1,983 boundaries; current fail-closed policy blocks all of them. A single shared coordinate cannot follow distinct plate transforms without a governed interface/deformation response. Do not average, snap, select a side, or duplicate nodes as an implicit fault.", "",
        "All 20 degree-three junctions are blocked, have no canonical velocity, and lack boundary types or a residual allocation rule. A common junction coordinate requires a compatible multi-boundary model. Incidence alone does not define it.", "",
        "Geological type and polarity remain UNKNOWN; relative motion is only a kinematic diagnostic. Those unknowns can remain only if an explicitly selected response law proves type-agnostic. No such law is currently selected, so type-dependent model selection is blocked.", "",
        "## D. Topology hold", "",
        "An explicit topology-invariance/event model is required. It must state which plate IDs, faces, edges, junctions and identities stay fixed over the authorized interval, and guard split, merge, creation/termination, boundary birth/death, adjacency change and junction reassignment. B6A's 27,123.405-year census bound concerns conditional rift activation only; it is not a topology bound or dt.", "",
        "## E. Mesh and fields", "",
        "The T0 FEG manifest identifies 64,442 nodes and 128,880 triangles (fault_count=0); B5's 64,800 entries are plate-cell faces, not triangles. Connectivity/support are valid T0 references, but there is no next-state topology hold, shared-node geometry, field transport, remap or remesh lineage contract. Nearest-neighbor, barycentric, conservative remap, snapping and arbitrary grid interpolation are not authorized.", "",
        "The FEG/runtime package is derived runtime support and is excluded from B3's canonical WORLD_HISTORY minimal-state ingest. The B3 inventory has 14 state domains. Existing retention declares initial supported fields as SYSTEM_MEMORY, T0 partition and kinematics STATIC system memory, unknown masks as support evidence, and FEG/runtime product as derived/discarded. B0-G requires any future-dependent SYSTEM_MEMORY to survive; producer adapter policy remains review-required and field-specific transfer is incomplete.", "",
        "## F. Numerical validity", "",
        "No governed angular rotation, node displacement, edge-fraction, inversion/Jacobian, remesh, or topology validity threshold exists. Solver stability and event-localization tolerance are solver-dependent. The rift horizon is only an event boundary to respect if that model is used; it supplies none of these numerical limits.", "",
        "## G. ShellSet and B7", "",
        "A physical boundary/junction response is required before a physically valid next state, but the evidence does not establish that ShellSet or any numerical solver is necessary. The model family and required outputs are not yet selectable. B7 is therefore not ready to qualify; if a native solver is later selected for expensive qualification, use Ubuntu after defining its narrow I/O/acceptance contract.", "",
        "## H. Candidate state contract and blockers", "",
        "The machine-readable candidate-state contract lists required source IDs, support, selected forcing/law, per-field memory transfer, uncertainty, event/provenance, checkpoint and replay recipe. No state was produced.", "",
        *[f"- `{x['blocker']}` — **{x['status']}**: {x['reason']}" for x in d["blockers"]["blockers"]], "",
        "First dt remains **NOT_READY_FOR_FIRST_DT**. Next authorization: `AUTHORIZE_TARGETED_MODEL_DECISION`. All safety gates remain closed.", "",
    ]
    tests = d.get("test_results")
    if tests:
        full = tests["active_r6"]
        compatible = tests.get("active_r6_non_branch_pinned", {})
        lines += [f"Validation verdict: **{r.get('qualification_verdict', 'PENDING')}**. Focused B6B: {tests['focused_b6b']['tests_passed']} passed. Full `test_r6_*.py`: {full['tests_passed']} passed, {full.get('errors', 0)} setup errors. py_compile {tests['py_compile']}; JSON/manifest/path {tests['json_manifest_path_validation']}; diff check {tests['diff_check']}.", ""]
    return "\n".join(lines)


def run(root: Path = ROOT) -> dict[str, Any]:
    data = adjudicate(root)
    OUT.mkdir(parents=True, exist_ok=True)
    test_path = OUT / "B6B_TEST_RESULTS.json"
    if test_path.is_file():
        data["test_results"] = json.loads(test_path.read_text(encoding="utf-8"))
        full = data["test_results"].get("active_r6", {})
        if full.get("errors", 0) or full.get("tests_failed", 0):
            data["result"]["qualification_validation_status"] = "BLOCKED"
            data["result"]["qualification_verdict"] = "BLOCKED_B6B_FULL_R6_SUITE_HAS_BRANCH_PINNED_B6A_ERRORS"
        else:
            data["result"]["qualification_validation_status"] = "PASS"
            data["result"]["qualification_verdict"] = DECISION
    _write_json(OUT / "B6B_INPUT_EVIDENCE.json", {"schema": "R6_B6B_INPUT_EVIDENCE_V1", "source_commit": HEAD, "sources": data["sources"]})
    artifacts = {
        "B6B_RESULT.json": data["result"],
        "B6B_FIRST_STEP_TRANSFORMATIONS.json": data["transformations"],
        "B6B_SYNTHETIC_FIXTURE_QUALIFICATION.json": data["fixtures"],
        "B6B_BOUNDARY_ACCOMMODATION.json": data["boundary"],
        "B6B_JUNCTION_ADJUDICATION.json": data["junction"],
        "B6B_TOPOLOGY_HOLD_CONTRACT.json": data["topology_hold"],
        "B6B_MESH_STATE_TRANSFER.json": data["mesh_transfer"],
        "B6B_SYSTEM_MEMORY_TRANSFER.json": data["memory"],
        "B6B_NUMERICAL_CONSTRAINTS.json": data["numerical"],
        "B6B_SHELLSET_DECISION.json": data["shellset"],
        "B6B_B7_CONTRACT.json": data["b7"],
        "B6B_FIRST_STEP_CANDIDATE_STATE_CONTRACT.json": data["candidate"],
        "B6B_BLOCKER_STATUS.json": data["blockers"],
        "B6B_FIRST_DT_INPUTS.json": data["first_dt_inputs"],
        "B6B_EXECUTION_TARGETS.json": data["execution"],
    }
    for name, value in artifacts.items():
        _write_json(OUT / name, value)
    (OUT / "README.md").write_text("# R6 B6B evidence package\n\nRead-only adjudication of first-step accommodation, topology validity, mesh/state transfer and remaining dt inputs. No first state or timestep is created.\n", encoding="utf-8", newline="\n")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(_report(data), encoding="utf-8", newline="\n")
    retained = sorted([p for p in OUT.iterdir() if p.is_file() and p.name != "B6B_ARTIFACT_MANIFEST.json"] + [REPORT], key=lambda p: p.as_posix())
    rows = []
    for p in retained:
        rel = p.relative_to(OUT).as_posix() if p.is_relative_to(OUT) else "../../docs/arcana/B6B_FIRST_STEP_ACCOMMODATION_STATE_TRANSFER.md"
        blob = p.read_bytes()
        rows.append({"relative_path": rel, "byte_size": len(blob), "sha256": hashlib.sha256(blob).hexdigest()})
    _write_json(OUT / "B6B_ARTIFACT_MANIFEST.json", {"schema": "R6_B6B_ARTIFACT_MANIFEST_V1", "artifacts": rows, "manifest_self_hash": "OMITTED_BY_POLICY"})
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        d = run(args.repository_root.resolve())
        print(json.dumps({"decision": d["result"]["decision"], "source_commit": HEAD,
                          "first_dt": d["result"]["first_dt_status_after_B6B"],
                          "shellset": d["shellset"]["decision"],
                          "next_authorization": d["result"]["maximum_next_authorization"]}, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"B6B_ADJUDICATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
