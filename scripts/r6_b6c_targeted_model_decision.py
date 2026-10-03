#!/usr/bin/env python3
"""Evidence-backed B6C first-step model decision; no model is executed."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "r6/b6c-targeted-first-step-model-decision"
HEAD = "7b8f21bd6c1802df2a50a7eece70cfa36b2d9278"
OUT = ROOT / "outputs/r6_b6c_targeted_model_decision"
REPORT = ROOT / "docs/arcana/B6C_TARGETED_FIRST_STEP_MODEL_DECISION.md"
DECISION = "PASS_B6C_TARGETED_FIRST_STEP_MODEL_DECISION"
HISTORICAL_B6A = "8f53f1586413b1e2e3b6738185727e5b6314c30c"
SOURCES = [
    "src/arcana_worldsim/r6/finite_rotation.py",
    "src/arcana_worldsim/r6/plate_kinematics_adapter.py",
    "scripts/r6_bind_t0_motion_prior_and_event_guard.py",
    "scripts/r6_bind_shared_boundary_topology_contact.py",
    "scripts/r6_b6_dependency_temporal_gap_adjudication.py",
    "R6_T0_CANONICAL_PLATE_KINEMATICS.json",
    "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json",
    "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json",
    "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json",
    "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json",
    "R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json",
    "R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json",
    "R6_TOPOLOGY_CONTACT_GUARD.json",
    "R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_RESULT.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_TEMPORAL_VALIDITY.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_TOPOLOGY_EVENT_CONTRACT.json",
    "outputs/r6_b6a_positive_duration_authority/B6A_RESULT.json",
    "outputs/r6_b6a_positive_duration_authority/B6A_MOTION_LAW_ADJUDICATION.json",
    "outputs/r6_b6a_positive_duration_authority/B6A_REFERENCE_FRAME_RESULT.json",
    "outputs/r6_b6a_positive_duration_authority/B6A_DERIVABILITY.json",
    "outputs/r6_b6b_accommodation_state_transfer/B6B_RESULT.json",
    "outputs/r6_b6b_accommodation_state_transfer/B6B_FIRST_STEP_TRANSFORMATIONS.json",
    "outputs/r6_b6b_accommodation_state_transfer/B6B_TOPOLOGY_HOLD_CONTRACT.json",
    "outputs/r6_b6b_accommodation_state_transfer/B6B_MESH_STATE_TRANSFER.json",
    "outputs/r6_b6b_accommodation_state_transfer/B6B_SYSTEM_MEMORY_TRANSFER.json",
    "outputs/r6_b6b_accommodation_state_transfer/B6B_NUMERICAL_CONSTRAINTS.json",
    "outputs/r6_b6b_accommodation_state_transfer/B6B_SHELLSET_DECISION.json",
    "outputs/r6_world_history_b3_t0_ingest/B3_T0_STATE_INVENTORY.json",
    "outputs/r6_world_history_b3_t0_ingest/B3_T0_RETENTION_MAP.json",
]

GATES = {
    "runtime_authorized": True,
    "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE",
    "mechanics_authorized": False,
    "forward_evolution_authorized": False,
    "dt_selected": False,
    "t1_created": False,
    "canonical_state_changed": False,
    "canonical_node_motion_executed": False,
    "canonical_topology_mutated": False,
    "shellset_executed": False,
    "orbdata_mechanics_executed": False,
}


class B6CError(ValueError):
    pass


def _git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if p.returncode:
        raise B6CError(f"git identity query failed: {' '.join(args)}")
    return p.stdout.strip()


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def adjudicate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    branch, head = _git(root, "branch", "--show-current"), _git(root, "rev-parse", "HEAD")
    if (branch, head) != (BRANCH, HEAD):
        raise B6CError(f"expected {BRANCH}@{HEAD}, found {branch}@{head}")
    src: dict[str, Any] = {}
    evidence = []
    for logical in SOURCES:
        p = root / logical
        if not p.is_file():
            raise B6CError(f"required current authority/source missing: {logical}")
        if p.suffix == ".json":
            try:
                src[logical] = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise B6CError(f"invalid JSON authority: {logical}") from exc
        evidence.append({"path": logical, "byte_size": p.stat().st_size, "sha256": _sha(p)})

    b6a = src["outputs/r6_b6a_positive_duration_authority/B6A_RESULT.json"]
    motion = src["outputs/r6_b6a_positive_duration_authority/B6A_MOTION_LAW_ADJUDICATION.json"]
    frame = src["outputs/r6_b6a_positive_duration_authority/B6A_REFERENCE_FRAME_RESULT.json"]
    derivability = src["outputs/r6_b6a_positive_duration_authority/B6A_DERIVABILITY.json"]
    b6b = src["outputs/r6_b6b_accommodation_state_transfer/B6B_RESULT.json"]
    b5 = src["outputs/r6_b5_plate_support_topology_qualification/B5_RESULT.json"]
    boundary = src["R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json"]
    boundary_law = src["R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json"]
    topology_guard = src["R6_TOPOLOGY_CONTACT_GUARD.json"]
    census = src["R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json"]
    feg = src["R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.json"]
    inventory = src["outputs/r6_world_history_b3_t0_ingest/B3_T0_STATE_INVENTORY.json"]
    retention = src["outputs/r6_world_history_b3_t0_ingest/B3_T0_RETENTION_MAP.json"]
    if b6a.get("qualified_source_commit") != HISTORICAL_B6A:
        raise B6CError("historical B6A source provenance changed")
    if b6a.get("decision") != "PASS_B6A_POSITIVE_DURATION_AUTHORITY_ADJUDICATION":
        raise B6CError("B6A qualification is not passing")
    if b6b.get("decision") != "PASS_B6B_FIRST_STEP_ACCOMMODATION_STATE_TRANSFER":
        raise B6CError("B6B adjudication is not passing")
    if (b6b.get("qualified_source_commit") != "66ff83a8cf8b86b483c60a75b12d1da9594d1740"
            or b6b.get("first_dt_status_after_B6B") != "NOT_READY_FOR_FIRST_DT"):
        raise B6CError("B6B source or first-dt status changed")
    if b6b.get("scientific_side_effect_check", {}).get("dt_selected") is not False:
        raise B6CError("B6B safety gates unexpectedly changed")
    if b5.get("boundary_count") != 1983 or b5.get("junction_count") != 20:
        raise B6CError("B5 boundary/junction cardinalities changed")
    if boundary.get("finite_step_status_counts") != {"BLOCKED": 1983} or boundary.get("junction_status_counts") != {"BLOCKED": 20}:
        raise B6CError("boundary/junction fail-closed evidence changed")
    if topology_guard.get("global_topology_guard_horizon_years") is not None:
        raise B6CError("a topology horizon now exists; model decision must be revised")
    if motion.get("positive_duration_motion_law_status") != "GOVERNED_CONDITIONAL_CONSTANT_T0_EULER_FIRST_SEGMENT":
        raise B6CError("first-segment motion law changed")

    rotation = {
        "schema": "R6_B6C_ROTATION_ACTION_CONVENTION_V1",
        "status": "UNIQUELY_DERIVABLE",
        "action": "ACTIVE_ROTATION_OF_COLUMN_POSITION_VECTOR",
        "differential_definition": "d(x)/dt = omega cross x; finite action is x(t)=exp([omega]_x t)x(0) for a constant omega within the authorized conditional first segment",
        "vector_and_multiplication_convention": "XYZ column vectors; quaternion code applies q*x*q_conjugate (equivalently active Rodrigues rotation); constant single-axis-vector action has no multi-step composition order ambiguity",
        "axis_orientation": {"positive_x": "lon=0 degrees, equator", "positive_y": "lon=+90 degrees, equator", "positive_z": "north pole", "handedness": "right-handed, fixed by the explicit cross-product implementation omega cross r"},
        "angular_velocity_sign": "positive omega follows the right-hand active rotation convention; verified by the infinitesimal derivative of finite_rotation.py and the T0 producer's numpy.cross(omega, r)",
        "coordinates": {"position": "unit-sphere Cartesian XYZ for rotation; multiply by R=6,371,000 m for linear distance", "source_grid": "R6_GLOBAL_GEOGRAPHY_1DEG_V1 latitude/longitude degrees", "omega": "rad/year", "time": "years older-to-younger elapsed time", "internal_frame": "SYNTHETIC_AREA_WEIGHTED_LEAST_SQUARES_NO_NET_ROTATION_GAUGE; not Earth/mantle fixed"},
        "evidence": ["src/arcana_worldsim/r6/finite_rotation.py::_cross and rotate_vector_constant_euler quaternion action", "scripts/r6_bind_t0_motion_prior_and_event_guard.py uses numpy.cross(omega, r)*RADIUS_M", "outputs/r6_b6a_positive_duration_authority/B6A_REFERENCE_FRAME_RESULT.json", "scripts/r6_b6_dependency_temporal_gap_adjudication.py records +X/+Y/+Z and right-handed cross-product semantics"],
        "limits": ["does not authorize a time interval, node motion, or T1", "does not provide an external Earth/mantle frame transform", "no time-varying rotation composition is governed"],
        "reconciles_b6b": "The earlier B6B caution relied on B5's limited field statement that handedness was not separately declared; the existing producer and finite-rotation code uniquely determine the internal active action. No new convention is invented.",
    }

    topo_options = {
        "schema": "R6_B6C_TOPOLOGY_MODEL_OPTIONS_V1",
        "known": {"positive_topology_bound": None, "rift_activation_horizon_years": census.get("global_event_guard", {}).get("earliest_model_activation_elapsed_years"), "rift_bound_semantics": "conditional rift-process activation only, not plate split/merge or topology-invariance", "topology_events": ["plate split", "plate merge", "creation/termination", "boundary birth/death", "adjacency change", "junction reassignment"]},
        "options": [
            {"model": "TOPOLOGY_FIXED_UNTIL_EVENT_DETECTOR", "meaning": "hold current incidence until a detector triggers a governed event", "authority_needed": ["event catalog", "detection criteria", "positive lead/stopping rule for every transition class", "no-unhandled-event guarantee"], "can_support_first_dt": "only after detector coverage and bounds are qualified", "status": "NOT_SELECTED"},
            {"model": "EXPLICIT_TOPOLOGY_INVARIANCE_WINDOW", "meaning": "author an interval-specific invariance assertion", "authority_needed": ["positive window", "scope over plate IDs/faces/edges/junctions", "evidence/assumptions establishing invariance"], "can_support_first_dt": "if the interval is authorized and independently qualified", "status": "NOT_SELECTED"},
            {"model": "EVENT_DRIVEN_TOPOLOGY_MODEL", "meaning": "explicit causal transition laws update topology and lineage", "authority_needed": ["transition laws", "event time/guard", "parent-child identity and support remapping"], "can_support_first_dt": "after event localization and transfer validity are established", "status": "NOT_SELECTED"},
            {"model": "EXTERNAL_TOPOLOGY_PROVIDER", "meaning": "import a time-resolved topology authority", "authority_needed": ["provider authority", "frame/time conversion", "identity mapping", "uncertainty and provenance"], "can_support_first_dt": "only for provider-supported interval and successful adapter qualification", "status": "NOT_SELECTED"},
            {"model": "AUTHORIAL_SEGMENT_MODEL", "meaning": "author a limited first-segment fixed-topology model", "authority_needed": ["explicit interval scope", "event exclusions/guards", "stop semantics and lineage"], "can_support_first_dt": "not until authorial premise and independent guard validity are accepted", "status": "NOT_SELECTED"},
        ],
        "interaction_with_rift_horizon": "The 27,123.405156307464-year bound may terminate a step using the conditional rift model; it supplies no topology invariance or general event bound.",
        "decision": "AUTHORIAL_MODEL_CHOICE_REQUIRED; no candidate is selected by current authority",
    }

    boundary_options = {
        "schema": "R6_B6C_BOUNDARY_MODEL_OPTIONS_V1",
        "current_support": {"segments": 1983, "all_finite_steps_blocked": True, "geological_type": "UNKNOWN", "polarity": "UNKNOWN", "nonzero_relative_motion": True},
        "options": [
            {"model": "DISCONTINUOUS_SLIP_INTERFACE", "role": "physical interface law plus two-sided geometry", "requires": ["which relative components are accommodated", "side/identity semantics", "finite displacement rule", "junction compatibility"], "geometry_only": False, "kinematics_only": "possible only if explicitly prescribed as type-agnostic; that would be a new physical assumption", "mechanics_solver": "not inherently; depends on whether slip is prescribed or solved", "rheology_fault_parameters_remesh": "not inherently, but may be required by selected law/mesh validity", "status": "NOT_SELECTED"},
            {"model": "FINITE_WIDTH_DEFORMATION_ZONE", "role": "distributed boundary deformation", "requires": ["width", "strain/deformation law", "field and material response", "mesh support"], "geometry_only": False, "mechanics_solver": "likely if response is solved rather than prescribed", "rheology": "required if constitutive response is asserted", "remeshing": "conditional on width representation and quality guard", "status": "NOT_SELECTED"},
            {"model": "DUPLICATED_BOUNDARY_GEOMETRY", "role": "representation choice only", "requires": ["parent-node/face lineage", "two-sided support", "an accompanying interface law"], "geometry_only": True, "physical_closure_by_itself": False, "status": "NOT_A_STANDALONE_PHYSICAL_MODEL"},
            {"model": "CONSTRAINT_SOLVED_INTERFACE", "role": "solve compatible shared/interface motion", "requires": ["constraint equations", "closure/objective or constitutive law", "junction constraints", "tolerance/solver contract"], "mechanics_solver": "yes", "rheology": "depends on closure; cannot be inferred", "status": "NOT_SELECTED"},
            {"model": "OTHER_TYPE_AGNOSTIC_INTERFACE_LAW", "role": "possible only if explicitly shown to conserve/close all demanded motion without using unknown type/polarity", "requires": ["authorial physical justification", "boundary and junction compatibility", "validity domain"], "status": "AUTHORIAL_PROPOSAL_REQUIRED"},
        ],
        "minimum_defensible_requirement": "A governed operator must map each set-valued boundary support and its adjacent plate motions to a physically interpretable finite shared-interface or explicitly two-sided state, with a fail-closed validity condition. Current authority does not select its law or show solver necessity.",
        "decision": "AUTHORIAL_DECISION_REQUIRED",
    }

    junction_options = {
        "schema": "R6_B6C_JUNCTION_MODEL_OPTIONS_V1",
        "count": 20,
        "current": {"support": "set-valued degree-three-or-higher incidence", "velocity": "UNBOUND", "relative_constraints": "UNBOUND", "residual_allocation": "NOT_AUTHORIZED"},
        "decision": "A boundary model plus set-valued support is sufficient only if it explicitly includes a multi-interface compatibility closure. A distinct closure rule is required; it may be a component of one unified boundary model, but cannot be implicit.",
        "required_constraints": ["all incident interface laws evaluated at shared junction identity", "one compatible coordinate or explicit multi-branch junction geometry", "conservation/compatibility residual definitions", "finite bounds and stop-on-violation", "identity/lineage across any representation change"],
        "forbidden": ["unique plate owner", "unjustified least-squares velocity", "averaged incident velocities", "silent node split or topology mutation"],
        "status": "AUTHORIAL_DECISION_REQUIRED; FAIL_CLOSED_UNTIL_CLOSED",
    }

    mesh = {
        "schema": "R6_B6C_MESH_REPRESENTATION_V1",
        "source": {"nodes": feg.get("canonical_mesh", {}).get("node_count"), "triangles": feg.get("canonical_mesh", {}).get("triangle_count"), "fault_count": feg.get("canonical_mesh", {}).get("fault_count"), "boundary_shared_nodes": 1953, "junction_shared_nodes": 20},
        "options": [
            {"model": "SAME_CONNECTIVITY_RIGID_COORDINATE_UPDATE", "fit": "single-plate interiors only", "global_fit": False, "missing": "cannot assign one coordinate to differently moving shared support; topology validity also absent"},
            {"model": "BOUNDARY_NODE_DUPLICATION", "fit": "only with selected two-sided interface semantics and explicit lineage", "physical_law_by_itself": False},
            {"model": "LOCAL_REMESH", "fit": "may support finite-width/localized accommodation", "requires": "selected physical zone, trigger, deterministic remesh and parent-child state mapping"},
            {"model": "GLOBAL_REMESH", "fit": "no present authority or need demonstrated", "status": "NOT_JUSTIFIED"},
            {"model": "LAGRANGIAN_MESH", "fit": "representation family; does not close boundaries/junctions itself", "status": "NOT_SELECTED"},
            {"model": "MIXED_REPRESENTATION", "fit": "could combine rigid interiors with explicit interface/junction representation", "requires": "authorial physical model plus identity/lineage contract"},
        ],
        "decision": "NO_GLOBAL_NEXT_STATE_MESH_REPRESENTATION_SELECTED; compatible choice depends on interface and topology model",
        "no_mesh_created": True,
    }

    state_transfer = {
        "schema": "R6_B6C_STATE_TRANSFER_MODEL_V1",
        "authority_rule": "B0-G SYSTEM_MEMORY cannot be discarded; B3 T0 is reference-only/minimal ingest and the field adapter has no arrays/transfer law. Do not infer material attachment or silently hold physical fields.",
        "families": [
            {"family": "physical_geography", "current": "DERIVED_SUPPORTED T0 payload", "required_rule": "MODEL_REQUIRED", "candidates": ["RIGID_ADVECT if material-attached is authorized", "IDENTITY_REFERENCE only under a field-specific hold law", "RECOMPUTE/REPLAY if derived by a governed recipe"]},
            {"family": "land_ocean", "current": "DERIVED_SUPPORTED T0 payload", "required_rule": "MODEL_REQUIRED", "candidates": ["advect/recompute/replay according to the selected physical surface model; no current rule"]},
            {"family": "province_state", "current": "DERIVED_SUPPORTED T0 payload", "required_rule": "MODEL_REQUIRED", "reason": "province identity/attachment and boundary transition semantics not bound"},
            {"family": "topography", "current": "DERIVED_SUPPORTED T0 payload", "required_rule": "MODEL_REQUIRED", "reason": "no uplift/subsidence/erosion or material-following update rule"},
            {"family": "tectonic_plate_partition", "current": "DERIVED_SUPPORTED T0 support", "required_rule": "IDENTITY_REFERENCE only if topology hold is selected; otherwise REINDEX_ONLY/event rebuild under explicit lineage; currently MODEL_REQUIRED"},
            {"family": "plate_kinematics", "current": "STATIC SYSTEM_MEMORY and conditional first-segment forcing", "required_rule": "REPLAY/IDENTITY_REFERENCE for the authorized segment only; renewal beyond it UNKNOWN"},
            {"family": "tectonic_kinematics_grid", "current": "UNKNOWN/no payload", "required_rule": "UNKNOWN; do not materialize from plate-level values without a governed spatial rule"},
            {"family": "boundary_classification", "current": "UNKNOWN/no payload", "required_rule": "UNKNOWN; no type inference from relative motion"},
            {"family": "bathymetry", "current": "UNKNOWN/no payload", "required_rule": "UNKNOWN or RECOMPUTE only after governed physical surface/water model"},
            {"family": "deep", "current": "UNKNOWN/no payload", "required_rule": "UNKNOWN/passive unless a coupled model is selected"},
            {"family": "climate", "current": "UNKNOWN/no payload; separate clock", "required_rule": "UNKNOWN/passive for tectonic step unless a temporal coupling contract is selected"},
            {"family": "hydrology", "current": "UNKNOWN/no payload; separate clock", "required_rule": "UNKNOWN/passive for tectonic step unless a temporal coupling contract is selected"},
            {"family": "weak_zone_state", "current": "UNKNOWN/no payload", "required_rule": "UNKNOWN; cannot initialize to zero; required if selected boundary law depends on it"},
            {"family": "junction_physical_semantics", "current": "UNKNOWN/no payload", "required_rule": "UNKNOWN; needs junction model if used"},
            {"family": "FEG/ShellSet runtime fields", "current": "derived numerical runtime support, not canonical B3 physical state", "required_rule": "RECOMPUTE from governed parent/model inputs after a future candidate is authorized; never promote runtime artifact to canonical state"},
        ],
        "remap_if_required": {"status": "MODEL_REQUIRED_NOT_IMPLEMENTED", "properties_to_define": ["conserved quantities for each field", "support/mask and UNKNOWN behavior", "mass/area/volume or integral consistency where physically applicable", "boundedness/positivity where the field semantics require it", "deterministic parent-child provenance and replay", "error estimator/tolerance and mesh validity"]},
        "decision": "BLOCKED_PENDING_FIELD_SPECIFIC_PHYSICAL_TRANSFER_AUTHORITY",
    }

    numerical = {
        "schema": "R6_B6C_NUMERICAL_VALIDITY_MODEL_V1",
        "constraints": [
            {"quantity": "maximum angular displacement", "units": "rad (or declared deg)", "evaluation": "max_plate |omega| * candidate elapsed years", "authority": "first-segment Euler law plus model-selected accuracy/guard threshold", "value_exists": False, "solver_dependent": False},
            {"quantity": "maximum node displacement", "units": "m", "evaluation": "max over supported nodes of spherical arc/chord displacement under the selected transfer model", "authority": "mesh/geometric accuracy model", "value_exists": False, "solver_dependent": False},
            {"quantity": "displacement/local-edge-length ratio", "units": "dimensionless", "evaluation": "per-node displacement divided by governed local edge length; use predeclared max threshold", "authority": "spatial accuracy/model contract", "value_exists": False, "solver_dependent": False},
            {"quantity": "boundary crossing/gap/overlap", "units": "m or dimensionless normalized residual", "evaluation": "selected interface geometry/contact guard", "authority": "boundary model", "value_exists": False, "solver_dependent": "depends on selected model"},
            {"quantity": "mesh quality/inversion", "units": "dimensionless Jacobian/area/orientation metrics", "evaluation": "minimum element quality after candidate geometry transfer", "authority": "mesh validity/remesh contract", "value_exists": False, "solver_dependent": False},
            {"quantity": "topology event/lead bound", "units": "years or Ma", "evaluation": "event detector or interval-specific invariance proof over all transition types", "authority": "topology model", "value_exists": False, "solver_dependent": "depends on detector"},
            {"quantity": "remesh trigger and lineage validity", "units": "model-specific quality metric", "evaluation": "precommitted mesh trigger and deterministic parent-child mapping", "authority": "mesh representation model", "value_exists": False, "solver_dependent": "mesh algorithm dependent"},
            {"quantity": "solver stability/convergence", "units": "solver-specific", "evaluation": "solver stability/accuracy estimator", "authority": "only if selected solver", "value_exists": False, "solver_dependent": True},
            {"quantity": "rift activation event horizon", "units": "years", "evaluation": "existing conditional threshold/opening-rate calculation", "authority": "Census V3 under fixed-T0 first segment", "value_exists": True, "value": census.get("global_event_guard", {}).get("earliest_model_activation_elapsed_years"), "role": "event stop for that rift model only; not topology bound or dt"},
        ],
        "decision": "REQUIRED_LIMITS_UNBOUND; NO_NUMERICAL_VALUE_SELECTED",
    }

    authorial = {
        "schema": "R6_B6C_AUTHORIAL_DECISION_REGISTER_V1",
        "decisions": [
            {"decision_id": "B6C-AD-01", "question": "Which positive-duration topology policy governs the first interval?", "options": ["topology fixed until complete event detector", "explicit invariance window", "event-driven topology law", "external topology provider", "authorial segment model"], "scientific_consequence": "controls whether plate/edge/junction identities persist or change", "downstream_consequence": "dt bounds, remesh/lineage, replay and state transfer", "reversible": "model-dependent; executed canonical transitions become history and cannot be erased", "affects_canon": True, "evidence_needed": ["causal event definitions and/or interval-specific support", "positive event/validity bounds", "transition geometry and lineage rules"]},
            {"decision_id": "B6C-AD-02", "question": "How is relative normal/tangential motion physically accommodated at UNKNOWN boundaries?", "options": ["prescribed discontinuous interface", "finite-width deformation zone", "constraint-solved interface", "other justified type-agnostic law"], "scientific_consequence": "sets physical continuity/discontinuity and how plate-relative demand changes geometry", "downstream_consequence": "solver need, fault/zone parameters, mesh representation and field transfer", "reversible": "law selection reversible before execution; realized states remain append-only history", "affects_canon": True, "evidence_needed": ["authorial physical rationale or targeted evidence for selected family", "boundary support/polarity semantics if required", "units, validity domain, uncertainty and fail conditions"]},
            {"decision_id": "B6C-AD-03", "question": "What compatibility law closes multi-boundary motion at 20 shared junctions?", "options": ["junction conditions embedded in one unified boundary law", "separate junction constitutive/kinematic law", "explicit event handoff with stop before incompatibility"], "scientific_consequence": "determines whether incident boundary motions admit one junction geometry/lineage", "downstream_consequence": "boundary solver, residual checks, mesh and topology events", "reversible": "reversible before execution; realized lineage is historical", "affects_canon": True, "evidence_needed": ["multiway compatibility equations", "residual definitions and limits", "stop/event/identity transfer rule"]},
            {"decision_id": "B6C-AD-04", "question": "Which T0 fields are material-attached, held, recomputed, or replayed through the chosen geometry change?", "options": ["field-specific rigid/material advection", "governed identity hold", "recompute/replay", "UNKNOWN until a domain model exists"], "scientific_consequence": "determines conservation and persistence of physical state/system memory", "downstream_consequence": "remapping, WORLD_HISTORY payloads, provenance and query semantics", "reversible": "policy reversible before execution; committed state history is append-only", "affects_canon": True, "evidence_needed": ["per-field physical attachment and update laws", "conservation/consistency invariants", "UNKNOWN/support/memory rules"]},
            {"decision_id": "B6C-AD-05", "question": "Which geometric accuracy, topology and (if selected) solver limits bound the first dt?", "options": ["authorial/model-specific thresholds plus estimator", "solver-specific stability/error controller", "event-limited interval with explicit geometric limits"], "scientific_consequence": "defines admissible numerical resolution and stop behavior", "downstream_consequence": "first-dt adjudication and possibly native solver qualification", "reversible": "thresholds can be revised before execution; executed trajectory is retained", "affects_canon": False, "evidence_needed": ["selected physical/topology/mesh models", "units and measurable estimators", "verification tests and uncertainty/sensitivity rationale"]},
        ],
        "rotation_convention_escalation": "NONE; uniquely derivable from source and already represented in the internal computational gauge",
    }

    shellset = {
        "schema": "R6_B6C_SHELLSET_DECISION_V1",
        "decision": "SHELLSET_DECISION_STILL_BLOCKED_BY_AUTHORIAL_MODEL_CHOICE",
        "reason": "No boundary/junction physical model has been selected. A prescribed kinematic interface might not require a solver; a solved finite-zone/constraint model might. ShellSet cannot be selected by availability alone.",
        "exact_outputs": "NOT_SCOPABLE_BEFORE_MODEL_SELECTION",
    }
    b7 = {
        "schema": "R6_B6C_B7_CONTRACT_V1",
        "status": "NOT_READY; no solver/model selected",
        "inputs": ["governed T0 plate rates/support and internal rotation convention", "selected topology and boundary/junction model", "T0 geometry/state identities", "field transfer contract", "numerical thresholds and uncertainty"],
        "outputs": "Only the exact boundary/junction or mesh response required by the selected model; not generic mechanics.",
        "units_support_runtime_authority_acceptance_failure": "MUST_BE_DEFINED_AFTER_MODEL_SELECTION; include units, support/UNKNOWN, runtime/package identity, authority level, tolerance/fail-closed criteria and scale.",
        "execution_target": "UBUNTU_WORKSTATION if a native or compute-intensive solver is selected; otherwise WINDOWS for contract/small fixtures",
        "execution_authorized": False,
    }
    prereqs = {
        "schema": "R6_B6C_FIRST_DT_CLOSURE_V1",
        "items": [
            {"item": "rotation convention", "status": "CLOSED", "reason": "uniquely derived active action from producer and finite-rotation implementation"},
            {"item": "positive-duration kinematics", "status": "MODEL_SELECTED_NOT_QUALIFIED", "reason": "conditional first-segment model exists; its finite interval remains separately bounded/not executable"},
            {"item": "topology model", "status": "AUTHORIAL_DECISION_REQUIRED"},
            {"item": "boundary model", "status": "AUTHORIAL_DECISION_REQUIRED"},
            {"item": "junction model", "status": "AUTHORIAL_DECISION_REQUIRED"},
            {"item": "mesh transfer", "status": "STILL_MISSING", "reason": "depends on topology/interface representation and lineage"},
            {"item": "state transfer", "status": "STILL_MISSING", "reason": "field-specific material attachment, memory and remap rules absent"},
            {"item": "numerical validity", "status": "STILL_MISSING", "reason": "thresholds/estimators remain unbound"},
            {"item": "mechanics requirement", "status": "AUTHORIAL_DECISION_REQUIRED", "reason": "follows from selected physical model; no solver requirement established"},
        ],
        "minimal_remaining_blocking_set": ["author topology/event policy and positive validity basis", "author boundary accommodation model", "multiway junction compatibility closure", "field/system-memory transfer rules", "mesh representation/lineage compatible with those models", "numerical validity bounds and conditional kinematic segment qualification"],
        "first_dt_readiness": "NOT_READY_FOR_FIRST_DT",
    }
    execution = {
        "schema": "R6_B6C_EXECUTION_PLAN_V1",
        "actions": [
            {"action": "author topology/boundary/junction model decisions", "target": "WINDOWS", "reason": "authorial/model contract work; no heavy computation"},
            {"action": "write field transfer and numerical validity contracts plus small synthetic fixtures after choices", "target": "WINDOWS", "reason": "implementation/audit"},
            {"action": "qualify selected native mechanics solver or large remeshing model, if required", "target": "UBUNTU_WORKSTATION", "reason": "compute-intensive; not authorized now"},
            {"action": "first-dt adjudication", "target": "WINDOWS", "condition": "only after all prerequisite authority/model qualification is closed"},
        ],
        "heavy_execution_during_b6c": False,
    }
    result = {
        "schema": "R6_B6C_RESULT_V1", "decision": DECISION, "branch": branch, "qualified_source_commit": head,
        "rotation_action_convention_status": rotation["status"],
        "topology_model_decision": topo_options["decision"], "topology_model_status": "AUTHORIAL_DECISION_REQUIRED",
        "boundary_model_decision": boundary_options["decision"], "boundary_model_status": "AUTHORIAL_DECISION_REQUIRED",
        "junction_model_decision": junction_options["status"], "junction_model_status": "AUTHORIAL_DECISION_REQUIRED",
        "mesh_representation_decision": mesh["decision"], "mesh_representation_status": "MODEL_REQUIRED_NOT_SELECTED",
        "state_transfer_model_decision": state_transfer["decision"], "state_transfer_model_status": "BLOCKED_PENDING_FIELD_SPECIFIC_PHYSICAL_TRANSFER_AUTHORITY",
        "numerical_validity_model": numerical["decision"], "numerical_validity_status": "BLOCKING_UNBOUND_LIMITS",
        "shellset_decision": shellset["decision"], "first_dt_readiness": prereqs["first_dt_readiness"],
        "next_stage_recommendation": "AUTHORIZE_AUTHORIAL_MODEL_DECISION",
        "maximum_next_authorization": "AUTHORIZE_AUTHORIAL_MODEL_DECISION",
        "production_source_changes": False,
        "scientific_side_effect_check": GATES,
    }
    data = {"result": result, "rotation": rotation, "topology": topo_options,
            "boundary": boundary_options, "junction": junction_options, "mesh": mesh,
            "state_transfer": state_transfer, "numerical": numerical,
            "authorial": authorial, "shellset": shellset, "b7": b7,
            "prereqs": prereqs, "execution": execution,
            "sources": sorted(evidence, key=lambda x: x["path"]),
            "source_facts": {"b6a": b6a, "motion": motion, "frame": frame,
                             "derivability": derivability, "b6b": b6b,
                             "boundary_law": boundary_law, "inventory": inventory,
                             "retention": retention}}
    validate(data)
    return data


def validate(data: dict[str, Any]) -> bool:
    r = data["result"]
    if r.get("decision") != DECISION or r.get("qualified_source_commit") != HEAD:
        raise B6CError("B6C source/decision identity mismatch")
    if r.get("rotation_action_convention_status") != "UNIQUELY_DERIVABLE":
        raise B6CError("rotation convention did not close from evidence")
    if r.get("first_dt_readiness") != "NOT_READY_FOR_FIRST_DT":
        raise B6CError("first dt cannot be ready with open model decisions")
    if r.get("shellset_decision") != "SHELLSET_DECISION_STILL_BLOCKED_BY_AUTHORIAL_MODEL_CHOICE":
        raise B6CError("ShellSet cannot be chosen without model selection")
    gates = r.get("scientific_side_effect_check", {})
    for key in ("mechanics_authorized", "forward_evolution_authorized", "dt_selected", "t1_created", "canonical_state_changed", "canonical_node_motion_executed", "canonical_topology_mutated", "shellset_executed", "orbdata_mechanics_executed"):
        if gates.get(key) is not False:
            raise B6CError(f"scientific safety gate opened: {key}")
    return True


def _write_json(p: Path, value: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _report(d: dict[str, Any]) -> str:
    r = d["result"]
    lines = [
        "# R6 B6C Targeted First-Step Model Decision", "",
        f"Decision: **{r['decision']}**; qualified source `{r['qualified_source_commit']}`.", "",
        "## Rotation action", "",
        "The T0 realization convention is uniquely derivable, rather than an authorial gap: the producer computes `v = omega × r`; the Cartesian axes are +X at longitude 0° on the equator, +Y at +90°, +Z north, with the cross product fixing the right-handed orientation. `finite_rotation.py` applies the positive quaternion action to column XYZ vectors, whose infinitesimal derivative is `omega × x`. This yields an active right-hand rotation for constant omega in the internal synthetic NNR gauge. Angular units are rad/year, coordinates are unit-sphere XYZ, and the physical sphere radius is 6,371,000 m. This closes convention only; no interval or coordinate motion is authorized. B5's earlier statement that handedness was not separately declared is superseded by these directly inspected producer/code semantics.", "",
        "## Topology, boundary and junction decisions", "",
        "No candidate topology model is selected. The fixed-until-detector, explicit invariance-window, event-driven, external-provider and authorial-segment alternatives require different scientific authority and stopping/lineage behavior. The 27,123.405-year rift bound is only a conditional rift activation event, not a topology window.", "",
        "The 1,983 boundaries have unresolved geological type and polarity, and all current finite steps remain blocked. Discontinuous slip, finite-width deformation and constraint-solved interfaces are distinct physical models; duplicated geometry is representation only. No evidence selects a type, polarity, rheology, fault law or solver. A unified law may handle boundaries and junctions only if it supplies explicit multi-interface compatibility for all 20 junctions without owner assignment.", "",
        "## Mesh and state transfer", "",
        "Same-connectivity rigid coordinate update fits single-plate interiors only. Duplication requires an authorized two-sided interface plus lineage; local remesh needs a selected zone/trigger/state map; global remesh is unsupported. No next-state mesh representation is selected. B3's 14 state families are inventoried in the machine package: supported geography fields require field-specific material/hold/recompute rules, plate support depends on topology policy, UNKNOWN domains remain UNKNOWN, and B0-G SYSTEM_MEMORY cannot be discarded. Remapping is not implemented or authorized.", "",
        "## Numerical validity and first-dt closure", "",
        "No value is selected for angular displacement, nodal displacement, edge-fraction, boundary gap/crossing, mesh quality, topology event lead, remesh trigger or solver stability. Their measurement variables and units are registered in JSON. The rift horizon remains a model event stop only.", "",
        "Rotation convention is CLOSED. Conditional positive-duration kinematics remain MODEL_SELECTED_NOT_QUALIFIED. Topology, interface/junction physics, mesh/state transfer and numerical limits remain authorial/model blockers. ShellSet remains undecided until a physical model is selected; B7 execution is not authorized. First dt remains NOT_READY_FOR_FIRST_DT.", "",
        "## Authorial decisions and next action", "",
        *[f"- **{x['decision_id']}** — {x['question']}" for x in d["authorial"]["decisions"]], "",
        "Next recommendation: `AUTHORIZE_AUTHORIAL_MODEL_DECISION`. This does not authorize dt, T1, canonical motion, topology mutation or forward evolution. All scientific execution gates remain closed.", "",
    ]
    tests = d.get("test_results")
    if tests:
        lines += [f"Validation: focused B6C {tests['focused_b6c']['tests_passed']} passed; full R6 suite {tests['active_r6']['tests_passed']} passed; py_compile {tests['py_compile']}; JSON/manifest {tests['json_manifest_validation']}; portability {tests['portable_path_validation']}; diff check {tests['diff_check']}.", ""]
    return "\n".join(lines)


def run(root: Path = ROOT) -> dict[str, Any]:
    d = adjudicate(root)
    OUT.mkdir(parents=True, exist_ok=True)
    test_path = OUT / "B6C_TEST_RESULTS.json"
    if test_path.is_file():
        d["test_results"] = json.loads(test_path.read_text(encoding="utf-8"))
    artifacts = {
        "B6C_RESULT.json": d["result"], "B6C_ROTATION_CONVENTION.json": d["rotation"],
        "B6C_TOPOLOGY_MODEL_OPTIONS.json": d["topology"], "B6C_BOUNDARY_MODEL_OPTIONS.json": d["boundary"],
        "B6C_JUNCTION_MODEL_OPTIONS.json": d["junction"], "B6C_MESH_REPRESENTATION.json": d["mesh"],
        "B6C_STATE_TRANSFER_MODEL.json": d["state_transfer"], "B6C_NUMERICAL_VALIDITY_MODEL.json": d["numerical"],
        "B6C_AUTHORIAL_DECISION_REGISTER.json": d["authorial"], "B6C_SHELLSET_DECISION.json": d["shellset"],
        "B6C_B7_CONTRACT.json": d["b7"], "B6C_FIRST_DT_CLOSURE.json": d["prereqs"],
        "B6C_EXECUTION_PLAN.json": d["execution"],
        "B6C_INPUT_EVIDENCE.json": {"schema": "R6_B6C_INPUT_EVIDENCE_V1", "source_commit": HEAD, "sources": d["sources"]},
    }
    if "test_results" in d:
        artifacts["B6C_TEST_RESULTS.json"] = d["test_results"]
    for name, val in artifacts.items():
        _write_json(OUT / name, val)
    (OUT / "README.md").write_text("# R6 B6C evidence package\n\nModel adjudication only. No dt, motion, mechanics, topology mutation, or T1 is executed.\n", encoding="utf-8", newline="\n")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(_report(d), encoding="utf-8", newline="\n")
    rows = []
    for p in sorted([x for x in OUT.iterdir() if x.is_file() and x.name != "B6C_ARTIFACT_MANIFEST.json"] + [REPORT], key=lambda x: x.as_posix()):
        rel = p.relative_to(OUT).as_posix() if p.is_relative_to(OUT) else "../../docs/arcana/B6C_TARGETED_FIRST_STEP_MODEL_DECISION.md"
        b = p.read_bytes()
        rows.append({"relative_path": rel, "byte_size": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    _write_json(OUT / "B6C_ARTIFACT_MANIFEST.json", {"schema": "R6_B6C_ARTIFACT_MANIFEST_V1", "artifacts": rows, "manifest_self_hash": "OMITTED_BY_POLICY"})
    return d


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        d = run(args.repository_root.resolve())
        print(json.dumps({"decision": d["result"]["decision"], "source_commit": HEAD,
                          "rotation": d["rotation"]["status"], "first_dt": d["prereqs"]["first_dt_readiness"],
                          "next_authorization": d["result"]["maximum_next_authorization"]}, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"B6C_ADJUDICATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

