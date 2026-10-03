#!/usr/bin/env python3
"""Audit current R6 authority for first-segment kinematics and topology time bounds."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "r6/b6a-positive-duration-kinematic-authority"
HEAD = "8f53f1586413b1e2e3b6738185727e5b6314c30c"
OUT = ROOT / "outputs/r6_b6a_positive_duration_authority"
REPORT = ROOT / "docs/arcana/B6A_POSITIVE_DURATION_KINEMATIC_AUTHORITY.md"
DECISION = "PASS_B6A_POSITIVE_DURATION_AUTHORITY_ADJUDICATION"
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

SOURCES = [
    "R6_T0_INITIAL_KINEMATICS_MANIFEST.json",
    "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json",
    "R6_T0_CANONICAL_PLATE_KINEMATICS.json",
    "R6_T0_MOTION_PRIOR_ADJUDICATION.json",
    "R6_INITIAL_PLATE_KINEMATICS_AND_RIFT_PARAMETER_AUTHORITY_BINDING.json",
    "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json",
    "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json",
    "R6_T0_FIRST_INTERVAL_EVENT_GUARD.json",
    "R6_PHYSICAL_EVENT_MODEL_CONTRACT.json",
    "R6_PLATE_KINEMATICS_INTERFACE_CONTRACT.json",
    "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json",
    "outputs/r6_b4_plate_kinematics_qualification/B4_TEMPORAL_SUPPORT.json",
    "outputs/r6_b4_plate_kinematics_qualification/B4_FORCING_INVENTORY.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_TEMPORAL_VALIDITY.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_TOPOLOGY_EVENT_CONTRACT.json",
    "outputs/r6_b6_dependency_temporal_gap_adjudication/B6_RESULT.json",
    "outputs/r6_b6_dependency_temporal_gap_adjudication/B6_TEMPORAL_CONSTRAINT_REGISTRY.json",
]
CODE_SOURCES = [
    "scripts/r6_bind_rift_initiation_and_event_guard.py",
    "scripts/r6_bind_t0_motion_prior_and_event_guard.py",
]


class B6AError(ValueError):
    pass


def _git(root: Path, *args: str) -> str:
    run = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                         text=True, check=False)
    if run.returncode:
        raise B6AError(f"git identity/provenance check failed: {' '.join(args)}")
    return run.stdout.strip()


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(root: Path, logical: str, sources: dict[str, Any]) -> Any:
    path = root / logical
    if not path.is_file():
        raise B6AError(f"required current R6 evidence is missing: {logical}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B6AError(f"required JSON evidence is invalid: {logical}") from exc
    sources[logical] = {"path": logical, "sha256": _hash(path), "byte_size": path.stat().st_size}
    return value


def adjudicate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    branch, head = _git(root, "branch", "--show-current"), _git(root, "rev-parse", "HEAD")
    if branch != BRANCH or head != HEAD:
        raise B6AError(f"expected {BRANCH}@{HEAD}, found {branch}@{head}")
    evidence: dict[str, Any] = {}
    docs = {name: _read(root, name, evidence) for name in SOURCES}
    for logical in CODE_SOURCES:
        path = root / logical
        if not path.is_file():
            raise B6AError(f"required current R6 producer source is missing: {logical}")
        evidence[logical] = {"path": logical, "sha256": _hash(path), "byte_size": path.stat().st_size}
    motion = docs["R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json"]
    realized = docs["R6_T0_CANONICAL_PLATE_KINEMATICS.json"]
    manifest = docs["R6_T0_INITIAL_KINEMATICS_MANIFEST.json"]
    rift = docs["R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json"]
    census = docs["R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json"]
    old_guard = docs["R6_T0_FIRST_INTERVAL_EVENT_GUARD.json"]
    b4 = docs["outputs/r6_b4_plate_kinematics_qualification/B4_TEMPORAL_SUPPORT.json"]
    b5 = docs["outputs/r6_b5_plate_support_topology_qualification/B5_TEMPORAL_VALIDITY.json"]
    b5_events = docs["outputs/r6_b5_plate_support_topology_qualification/B5_TOPOLOGY_EVENT_CONTRACT.json"]
    b6 = docs["outputs/r6_b6_dependency_temporal_gap_adjudication/B6_RESULT.json"]
    b6_registry = docs["outputs/r6_b6_dependency_temporal_gap_adjudication/B6_TEMPORAL_CONSTRAINT_REGISTRY.json"]

    if b6.get("decision") != "PASS_B6_DEPENDENCY_TEMPORAL_GAP_ADJUDICATION":
        raise B6AError("the required B6 adjudication is not passing")
    if manifest.get("plate_count") != 12 or manifest.get("time_ma") != 210.0:
        raise B6AError("T0 kinematic manifest no longer has 12 plates at 210 Ma")
    if len(realized.get("plates", [])) != 12:
        raise B6AError("canonical T0 realization no longer contains 12 plate rates")
    vector_sha = docs["R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json"].get("payload", {}).get("sha256")
    if realized.get("parent_vector_partition_sha256") != vector_sha:
        raise B6AError("canonical T0 kinematics no longer bind to the governed vector partition")
    if manifest.get("kinematics_sha256") != realized.get("payload_identity_sha256"):
        raise B6AError("T0 kinematics manifest no longer binds the canonical rate realization")
    if census.get("time_ma") != 210.0 or census.get("time_evolution_executed") is not False:
        raise B6AError("V3 census is not an exact-T0 evaluation-only artifact")
    if census.get("canonical_kinematics_sha256") != realized.get("payload_identity_sha256"):
        raise B6AError("V3 event census does not bind the current canonical kinematics")
    if rift.get("status") != "PRECOMMITTED_BEFORE_T0_CENSUS_V3":
        raise B6AError("rift guard law is not the precommitted law bound to census V3")
    if b4.get("hard_anchors_ma") != [210.0] or b5.get("hard_anchors_ma") != [210.0]:
        raise B6AError("B4/B5 temporal anchors changed; review B6A classifications")

    guard = census.get("global_event_guard", {})
    conditional_years = guard.get("earliest_model_activation_elapsed_years")
    if (guard.get("status") != "CONDITIONAL_BOUND_WITHIN_FIXED_T0_EULER_SEGMENT"
            or not isinstance(conditional_years, (int, float)) or conditional_years <= 0
            or guard.get("post_segment_guard_bound") is not False):
        raise B6AError("V3 conditional rift activation bound is missing or changed")
    if census.get("counts") != {"ACTIVE": 0, "ELIGIBLE_QUIESCENT": 26, "INELIGIBLE": 4, "UNKNOWN": 0}:
        raise B6AError("V3 candidate eligibility census changed; re-adjudicate event authority")
    max_candidate = max(census.get("candidates", []), key=lambda row: row["maximum_local_opening_velocity_m_per_year"])
    derived_years = guard["threshold_lower_bound_m"] / max_candidate["maximum_local_opening_velocity_m_per_year"]
    if max_candidate["pair_id"] != guard.get("limiting_pair_id") or not math.isclose(derived_years, conditional_years, rel_tol=1e-12):
        raise B6AError("V3 rift activation bound does not reproduce from governed threshold/rate inputs")
    if rift.get("first_segment_policy", {}).get("no_time_evolution_in_this_task") is not True:
        raise B6AError("rift-law first-segment scope changed; require renewed adjudication")
    if rift.get("first_segment_policy", {}).get("motion", "").find("Hold the canonical t0 Euler state constant only through the first segment") < 0:
        raise B6AError("the explicit conditional constant-T0 first segment is absent")
    if rift.get("numerical_policy", {}).get("first_interval_contract_authorized") is not False:
        raise B6AError("first-interval execution authorization changed")
    if rift.get("p09_semantics", "").find("no plate split or lineage change is defined") < 0:
        raise B6AError("rift activation and plate-split semantics are no longer explicitly separated")

    activation = {
        "status": guard["status"],
        "eligibility_counts": census["counts"],
        "maximum_local_opening_velocity_m_per_year": max_candidate["maximum_local_opening_velocity_m_per_year"],
        "elapsed_years": conditional_years,
        "elapsed_ma": guard.get("earliest_model_activation_elapsed_Ma"),
        "earliest_model_activation_age_ma": guard.get("earliest_model_activation_age_Ma"),
        "limiting_pair_id": guard.get("limiting_pair_id"),
        "threshold_lower_bound_m": guard.get("threshold_lower_bound_m"),
        "not_a_natural_minimum": guard.get("not_a_natural_minimum"),
        "validity_scope": guard.get("validity_scope"),
        "event_semantics": rift["driver_and_transition_law"]["event_condition"],
        "does_not_bound": ["plate split", "merge", "creation/termination", "boundary birth/death", "adjacency change", "junction reassignment", "post-segment renewal"],
    }
    authority = {
        "schema": "R6_B6A_AUTHORITY_INVENTORY_V1",
        "instantaneous_anchor": {"status": "GOVERNED_CURRENT", "time_ma": 210.0,
            "plate_count": 12, "rate_units": "rad/year", "source": "R6_T0_CANONICAL_PLATE_KINEMATICS.json"},
        "conditional_first_segment": {"status": "GOVERNED_CURRENT_CONDITIONAL_MODEL", "law": "hold canonical T0 Euler state constant only through first segment; stop at earliest event/law boundary", "renewal": "UNBOUND_BEYOND_FIRST_SEGMENT", "execution_authorized": False},
        "rift_activation_bound": {"status": "DERIVABLE_GOVERNED_WITHIN_AUTHORED_MODEL", "scope": "conditional rift-process activation only", "elapsed_years": conditional_years},
        "topology_transition_ages_or_invariance": {"status": "ABSENT", "event_types": ["plate split", "plate merge", "plate creation/termination", "boundary birth/death", "adjacency change", "junction reassignment"]},
        "external_rotation_series": {"status": "ABSENT_FROM_CURRENT_R6_PROVENANCE", "legacy_search_scope": "followed only current R6 provenance pointers; no unreferenced historical output scan"},
        "processor": {"status": "REFERENCE_ONLY_CANDIDATE", "software_does_not_supply_temporal_authority": True},
        "search_inventory": {
            "finite_or_stage_rotation_sequence": "ABSENT; finite-rotation papers are cited as methodology only",
            "Euler_vectors_at_multiple_times": "ABSENT; one governed T0 realization at 210 Ma",
            "angular_velocity_history": "ABSENT; only a conditional fixed-T0 first segment is bound",
            "declared_numeric_kinematic_validity_interval": "ABSENT",
            "long_term_segment_renewal_or_interpolation": "ABSENT",
            "topology_event_ages_or_invariance_intervals": "ABSENT",
            "R6_rift_activation_horizon": "CONDITIONAL_MODEL_BOUND_ONLY; not a topology event time",
        },
    }
    temporal_source_audit = {
        "schema": "R6_B6A_TEMPORAL_SOURCE_AUDIT_V1",
        "sources": [
            {"path": "R6_T0_CANONICAL_PLATE_KINEMATICS.json", "classification": "GOVERNED_CURRENT", "finding": "12 synthetic Euler-rate vectors at the single T0 anchor; no temporal sequence."},
            {"path": "R6_T0_INITIAL_KINEMATICS_MANIFEST.json", "classification": "GOVERNED_CURRENT", "finding": "one canonical realization at 210 Ma; first-segment renewal remains unbound."},
            {"path": "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json", "classification": "GOVERNED_CURRENT", "finding": "T0 initial condition only; its held-constant segment is explicitly conditional and not exercised by that contract."},
            {"path": "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json", "classification": "GOVERNED_CURRENT", "finding": "explicit authorial constant-T0 first-segment policy and rift-initiation guard; no time evolution or plate split."},
            {"path": "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json", "classification": "GOVERNED_CURRENT", "finding": "deterministic conditional rift-activation bound; not a natural minimum or topology-change time."},
            {"path": "R6_T0_FIRST_INTERVAL_EVENT_GUARD.json", "classification": "SUPERSEDED_FOR_RIFT_ELIGIBILITY", "finding": "references the older V1 census with 30 UNKNOWN pairs; V3 binds current T0 kinematics and has 26 eligible, 4 ineligible, 0 unknown. It does not supersede the absent topology-transition bound or numerical authorization gaps."},
            {"path": "outputs/r6_b4_plate_kinematics_qualification/B4_TEMPORAL_SUPPORT.json", "classification": "GOVERNED_CURRENT_QUALIFICATION_EVIDENCE", "finding": "adapter itself provides only an instant anchor; does not negate the later conditional R6 first-segment model."},
            {"path": "outputs/r6_b5_plate_support_topology_qualification/B5_TEMPORAL_VALIDITY.json", "classification": "GOVERNED_CURRENT_QUALIFICATION_EVIDENCE", "finding": "B5 spatial support has one anchor and no topology dates; synthetic event schema is not an actual event calendar."},
            {"path": "outputs/r6_b5_plate_support_topology_qualification/B5_TOPOLOGY_EVENT_CONTRACT.json", "classification": "CANDIDATE_SCHEMA_ONLY", "finding": "event examples are marked actual_arcana_event=false and provide no ages."},
            {"path": "R6_INITIAL_PLATE_KINEMATICS_AND_RIFT_PARAMETER_AUTHORITY_BINDING.json", "classification": "SUPERSEDED_FOR_T0_VECTOR_MATERIALIZATION; CURRENT_FOR_OPEN_MODEL_GAPS", "finding": "its earlier vector-unbound statement is superseded by the canonical T0 realization; its unresolved motion renewal/numerical validity gaps remain."},
            {"path": "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json#research_references", "classification": "REFERENCE_ONLY", "finding": "finite-rotation literature is methodological context expressly not transferred as ARCANA temporal law."},
            {"path": "R6_PYGPLATES_*", "classification": "REFERENCE_ONLY_CANDIDATE", "finding": "processor capability cannot create missing trajectory or topology authority."},
            {"path": "additional governed temporal anchors", "classification": "ABSENT", "finding": "the audited current R6/B4/B5 inputs expose only 210 Ma."},
        ],
    }
    motion_adjudication = {
        "schema": "R6_B6A_MOTION_LAW_ADJUDICATION_V1",
        "instantaneous_rate_status": "GOVERNED_AT_T0_ONLY",
        "multiple_temporal_anchor_status": {"status": "SINGLE_GOVERNED_ANCHOR_ONLY", "times_ma": [210.0], "plate_count": 12},
        "positive_duration_motion_law_status": "GOVERNED_CONDITIONAL_CONSTANT_T0_EULER_FIRST_SEGMENT",
        "law": rift["first_segment_policy"]["motion"],
        "scope_limitations": ["first segment only", "no renewal/change law beyond segment", "segment ends at earliest event/law boundary", "numeric displacement/rotation/runtime horizon remains unbound"],
        "rate_is_not_law_finding": "The T0 rates alone do not authorize continuation; the separate precommitted R6 rift binding supplies a conditional first-segment rule. It does not authorize execution or a selected interval.",
        "not_assumed": "omega(t)=omega(T0) beyond the explicitly bounded first segment",
        "event_guard": activation,
        "first_interval_contract_authorized": False,
        "dt_selected": False,
    }
    frame = {
        "schema": "R6_B6A_REFERENCE_FRAME_RESULT_V1",
        "requirement": "SUFFICIENT_FOR_INTERNAL_RELATIVE_MOTION",
        "internal_frame": "SYNTHETIC_AREA_WEIGHTED_LEAST_SQUARES_NO_NET_ROTATION_GAUGE",
        "evidence": ["T0 motion-prior contract common gauge", "producer uses xyz from lat/lon and v=omega cross r on the declared synthetic sphere"],
        "earth_fixed_or_mantle_fixed": False,
        "external_frame_transform": "FRAME_TRANSFORM_REQUIRED_IF_AN_EXTERNAL_EARTH/MANTLE-FRAME_PROVIDER_IS_LATER_SELECTED",
        "temporal_semantics": "first-segment constant T0 Euler state is interpreted within the same synthetic internal gauge; no external frame trajectory is implied",
    }
    topology = {
        "schema": "R6_B6A_TOPOLOGY_TEMPORAL_BOUND_V1",
        "status": "NO_POSITIVE_BOUND",
        "next_topology_event_status": "NOT_GOVERNED_OR_BOUNDED",
        "event_types": ["plate split", "plate merge", "plate creation/termination", "boundary birth/death", "adjacency change", "junction reassignment"],
        "known_topology_event_times_ma": [],
        "topology_invariance_interval_ma": None,
        "positive_conditional_rift_activation_bound": activation,
        "why_rift_bound_does_not_close_topology": "The governed guard terminates at RIFT_INITIATION, which is a rift-process activation state; P09 plate split and lineage/topology changes are explicitly deferred and have no event geometry/time law.",
        "v1_guard_reconciliation": "V3 supersedes V1 for rift eligibility/activation calculations only. V3 does not prove topology invariance through its conditional horizon.",
    }
    derivability = {
        "schema": "R6_B6A_DERIVABILITY_V1",
        "T0_instantaneous_relative_motion": {"status": "DERIVABLE_GOVERNED", "reason": "governed T0 Euler vectors, plate support and deterministic spherical cross-product rule"},
        "first_segment_motion": {"status": "GOVERNED_AUTHORED_MODEL_NOT_DERIVED_FROM_RATE_ALONE", "reason": "the conditional constant-rate first-segment policy is an explicit R6 model rule"},
        "rift_activation_model_bound": {"status": "DERIVABLE_GOVERNED_WITHIN_MODEL", "reason": "precommitted lower threshold divided by maximum supported positive opening rate under the constant first segment", "value_years": conditional_years},
        "topology_transition_or_invariance_bound": {"status": "NOT_DERIVABLE", "reason": "no governing split/merge/adjacency/junction event-time law or interval-invariance rule"},
        "overall_joint_interval": "NOT_DERIVABLE_FROM_CURRENT_GOVERNED_INPUTS",
    }
    joint = {
        "schema": "R6_B6A_JOINT_TEMPORAL_SUPPORT_V1",
        "status": "NO_JOINT_KINEMATIC_TOPOLOGY_SUPPORT",
        "kinematics": "conditional constant-T0 first segment; not executable because no joint topology bound and numerical interval remains unbound",
        "topology": "no positive bound or topology-invariance interval",
        "requires_both": True,
        "positive_interval_status": "POSITIVE_INTERVAL_REQUIRES_MODEL_DECISION",
        "dt_selected": False,
    }
    model_contract = {
        "schema": "R6_B6A_MINIMUM_MODEL_CONTRACT_V1",
        "existing_partial_contract": {"type": "AUTHORIAL_MODEL", "rule": rift["first_segment_policy"]["motion"], "scope": "first segment only"},
        "additional_contract_required": True,
        "missing_contract_type": "AUTHORIAL_MODEL",
        "required_components": [
            "explicit validity semantics for the existing conditional first segment",
            "governed positive interval with both motion and topology validity",
            "topology-event eligibility and earliest split/merge/create/terminate/boundary/junction transition behavior or an interval-specific topology-invariance rule",
            "state whether rift activation can occur without topology change and bind P09 split separately",
            "event stop/localization and uncertainty/provenance semantics",
            "frame semantics kept in the current synthetic gauge unless an explicit external-frame transform is authorized",
            "numerical displacement/rotation/runtime horizon remains a later dt prerequisite, not a value to invent here",
        ],
        "no_model_values_selected": True,
    }
    research = {
        "schema": "R6_B6A_PROVIDER_RESEARCH_DECISIONS_V1",
        "decisions": [
            {"gap": "first-segment T0 Euler continuation", "decision": "EXISTING_ARCANA_DATA_SUFFICIENT_FOR_CONDITIONAL_MODEL_RULE", "evidence": "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.first_segment_policy", "remaining": "do not extend beyond first segment"},
            {"gap": "rift activation within fixed first segment", "decision": "EXISTING_ARCANA_DATA_SUFFICIENT_FOR_CONDITIONAL_MODEL_BOUND", "evidence": "census V3 + precommitted authorial threshold and T0 rates", "remaining": "bound is not a natural minimum and applies only within separately bounded first step"},
            {"gap": "next topological transition or invariance", "decision": "AUTHORIAL_MODEL_DECISION_REQUIRED", "needed": "define causal eligible transitions and either event-time lower bounds or interval-specific invariance; distinguish rift initiation from P09 split"},
            {"gap": "physical calibration of future event law", "decision": "TARGETED_EXTERNAL_RESEARCH_REQUIRED_ONLY_IF_AUTHOR_SELECTS_EMPIRICAL_PHYSICAL_FAMILY", "scope": "targeted comparison for selected law; no provider authority chosen by B6A"},
            {"gap": "external frame transform", "decision": "TARGETED_REPOSITORY_RECOVERY_IF_AN_EXISTING_ARCANA_TRANSFORM_IS_CLAIMED; otherwise AUTHORIAL_MODEL_DECISION_REQUIRED", "needed": "bind transform and frame time semantics before using an external trajectory"},
            {"gap": "processor", "decision": "NO_RESEARCH_REQUIRED_NOW", "reason": "pyGPlates cannot supply missing scientific motion/topology authority"},
        ],
    }
    execution = {
        "schema": "R6_B6A_EXECUTION_TARGETS_V1",
        "tasks": [
            {"task": "authorial topology-validity/event-law decision and focused repository audit", "target": "WINDOWS", "heavy_computation": False},
            {"task": "targeted literature check if an empirical law family is selected", "target": "WINDOWS", "heavy_computation": False},
            {"task": "later native solver qualification only after physical law and I/O contract exist", "target": "UBUNTU_WORKSTATION", "heavy_computation": True, "authorized_now": False},
        ],
        "heavy_task_required_during_B6A": False,
    }
    handoff = {
        "schema": "R6_B6A_B6B_HANDOFF_V1",
        "provide": ["conditional first-segment constant-T0 Euler model and exact scope", "conditional rift-activation bound and limitations", "synthetic T0 gauge semantics", "no topology-invariance or split-time authority"],
        "B6B_must_not_assume": ["that rift activation equals plate split", "that V3 guard bounds all topology changes", "that omega remains constant after first segment", "that T0 support determines boundary accommodation"],
        "still_required_for_later_first_dt": ["topology-event/invariance contract", "boundary/junction accommodation", "mesh/state transfer", "numerical validity limits"],
        "mechanics_or_execution_authorized": False,
    }
    result = {
        "schema": "R6_B6A_RESULT_V1", "decision": DECISION, "branch": branch,
        "qualified_source_commit": head,
        "instantaneous_rate_status": motion_adjudication["instantaneous_rate_status"],
        "multiple_temporal_anchor_status": motion_adjudication["multiple_temporal_anchor_status"]["status"],
        "positive_duration_motion_law_status": motion_adjudication["positive_duration_motion_law_status"],
        "reference_frame_requirement": frame["requirement"],
        "topology_temporal_bound_status": topology["status"],
        "next_topology_event_status": topology["next_topology_event_status"],
        "conditional_rift_activation_bound_years": conditional_years,
        "derivability_result": derivability["overall_joint_interval"],
        "positive_interval_status": joint["positive_interval_status"],
        "joint_kinematic_topology_support": joint["status"],
        "model_contract_required": model_contract["additional_contract_required"],
        "model_type_required": model_contract["missing_contract_type"],
        "first_dt_status_after_B6A": "NOT_READY_FOR_FIRST_DT",
        "maximum_next_authorization": "AUTHORIZE_TARGETED_B6B_GAP_CLOSURE",
        "scientific_side_effect_check": GATES,
        "source_evidence": sorted(evidence.values(), key=lambda x: x["path"]),
        "scientific_conclusion_changed_from_B6": True,
        "change_summary": "The current authorial R6 binding supplies a conditional fixed-T0 first-segment law and census V3 supplies a conditional rift-activation bound; no bound to topology mutations or joint-validity interval exists.",
    }
    return {"result": result, "authority": authority, "temporal_source_audit": temporal_source_audit,
            "motion": motion_adjudication, "frame": frame, "topology": topology,
            "derivability": derivability, "joint": joint, "model_contract": model_contract,
            "research": research, "execution": execution, "handoff": handoff,
            "inputs": sorted(evidence.values(), key=lambda x: x["path"])}


def validate_decision(data: dict[str, Any]) -> bool:
    result = data["result"]
    if result.get("decision") != DECISION or result.get("qualified_source_commit") != HEAD:
        raise B6AError("B6A decision/source identity invalid")
    if data["topology"]["status"] != "NO_POSITIVE_BOUND":
        raise B6AError("B6A cannot claim a topology temporal bound from rift activation alone")
    if data["joint"]["status"] != "NO_JOINT_KINEMATIC_TOPOLOGY_SUPPORT":
        raise B6AError("joint temporal support must remain absent")
    if data["joint"]["dt_selected"] is not False:
        raise B6AError("B6A must not select dt")
    if result["scientific_side_effect_check"] != GATES:
        raise B6AError("scientific safety gates changed")
    return True


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _report(data: dict[str, Any]) -> str:
    result, activation = data["result"], data["topology"]["positive_conditional_rift_activation_bound"]
    sources = data["temporal_source_audit"]["sources"]
    lines = [
        "# R6 B6A Positive-Duration Kinematic Authority Adjudication", "",
        f"Decision: **{result['decision']}**", "",
        "## A. Baseline and scope", "",
        f"Branch `{result['branch']}`, qualified source commit `{result['qualified_source_commit']}`. Read-only authority adjudication; no evolution, dt, mechanics, node movement, or topology mutation.", "",
        "## B. Temporal source audit", "",
        *[f"- `{x['path']}` — **{x['classification']}**: {x['finding']}" for x in sources], "",
        "## C. Instantaneous rates and first-segment law", "",
        "The 12 T0 Euler vectors at 210 Ma are instantaneous values; the values alone do not authorize continuation. The precommitted R6 rift-law binding separately defines a conditional first segment that holds the canonical T0 Euler state constant until the earliest event/law boundary. This is a governed authorial model rule, limited to that first segment; renewal/change afterward remains unbound. The first-interval contract is not authorized and no time evolution was executed.", "",
        "## D. Multiple anchors and frame", "",
        "Only one current governed temporal anchor is present: 210 Ma. The shared synthetic area-weighted no-net-rotation gauge and spherical XYZ calculation are sufficient for internal relative motion in this synthetic model. They are not Earth-fixed or mantle-fixed. Any future external trajectory requires an explicit frame transform.", "",
        "## E. Event bound versus topology bound", "",
        f"Census V3 classifies 26 adjacent pairs as eligible quiescent, 4 as ineligible, and 0 as unknown. Its fastest supported local opening and precommitted 5 km lower model threshold give a conditional rift-process activation horizon of {activation['elapsed_years']:.6f} years ({activation['elapsed_ma']:.12g} Ma), limited by pair `{activation['limiting_pair_id']}`. It is expressly not a natural minimum and applies only while the fixed T0 Euler segment is valid and a first numerical step is separately bounded. Rift activation is not plate split.", "",
        "No positive time or invariant interval is governed for plate split/merge, plate creation/termination, boundary birth/death, adjacency change, or junction reassignment. P09 split/lineage behavior is explicitly deferred. The older first-interval guard V1 is superseded for rift eligibility by census V3, but its separate concerns about topology and numerical limits remain open.", "",
        "## F. Derivability and joint support", "",
        "T0 instantaneous relative motion is deterministically derivable. The conditional rift activation bound is derivable within its authored model. Neither supplies a topology-event bound; there is no joint kinematic-topology temporal support.", "",
        "## G. Minimum remaining model contract", "",
        "An authorial topology/event model must define the eligibility and validity of the next topological transitions, or provide an interval-specific topology-invariance authority; distinguish rift activation from P09 split; preserve event provenance/uncertainty; and use the existing synthetic gauge unless a transform is explicitly authorized. Numerical validity limits remain a later dt prerequisite. No values or timestep were selected.", "",
        "## H. B6B handoff and execution target", "",
        "B6B receives the scoped first-segment law and rift-only conditional horizon, but must not treat them as an all-topology event calendar or extend constant omega beyond the segment. Authorial/model adjudication and any narrow research are Windows tasks. Ubuntu is reserved for a later authorized native solver qualification, if one is selected; no heavy task is required now.", "",
        "## I. Decision and gates", "",
        "Positive interval status: **POSITIVE_INTERVAL_REQUIRES_MODEL_DECISION**. First dt remains **NOT_READY_FOR_FIRST_DT**. Maximum next authorization: `AUTHORIZE_TARGETED_B6B_GAP_CLOSURE`.", "",
        "`runtime_authorized` remains limited to `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`; mechanics, forward evolution, dt, T1, and canonical changes remain false.", "",
    ]
    tests = data.get("test_results")
    if tests:
        lines += [f"Validation: focused B6A {tests['focused_b6a']['tests_passed']} passed; active R6 {tests['active_r6']['tests_passed']} passed; py_compile {tests['py_compile']}; JSON/manifest/path {tests['json_manifest_path_validation']}; diff check {tests['diff_check']}.", ""]
    return "\n".join(lines)


def run(root: Path = ROOT) -> dict[str, Any]:
    data = adjudicate(root)
    validate_decision(data)
    OUT.mkdir(parents=True, exist_ok=True)
    _write_json(OUT / "B6A_INPUT_EVIDENCE.json", {"schema": "R6_B6A_INPUT_EVIDENCE_V1", "source_commit": HEAD, "sources": data["inputs"]})
    test_path = OUT / "B6A_TEST_RESULTS.json"
    if test_path.is_file():
        data["test_results"] = json.loads(test_path.read_text(encoding="utf-8"))
    artifacts = {
        "B6A_RESULT.json": data["result"],
        "B6A_AUTHORITY_INVENTORY.json": data["authority"],
        "B6A_TEMPORAL_SOURCE_AUDIT.json": data["temporal_source_audit"],
        "B6A_MOTION_LAW_ADJUDICATION.json": data["motion"],
        "B6A_REFERENCE_FRAME_RESULT.json": data["frame"],
        "B6A_TOPOLOGY_TEMPORAL_BOUND.json": data["topology"],
        "B6A_DERIVABILITY.json": data["derivability"],
        "B6A_JOINT_TEMPORAL_SUPPORT.json": data["joint"],
        "B6A_MINIMUM_MODEL_CONTRACT.json": data["model_contract"],
        "B6A_PROVIDER_RESEARCH_DECISIONS.json": data["research"],
        "B6A_EXECUTION_TARGETS.json": data["execution"],
        "B6A_B6B_HANDOFF.json": data["handoff"],
    }
    for name, payload in artifacts.items():
        _write_json(OUT / name, payload)
    (OUT / "README.md").write_text("# R6 B6A evidence package\n\nRead-only adjudication of the conditional first-segment kinematic rule and topology-time authority. No dt, evolution, mechanics, or topology mutation is authorized.\n", encoding="utf-8", newline="\n")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(_report(data), encoding="utf-8", newline="\n")
    retained = sorted([p for p in OUT.iterdir() if p.is_file() and p.name != "B6A_ARTIFACT_MANIFEST.json"] + [REPORT], key=lambda p: p.as_posix())
    rows = []
    for path in retained:
        rel = path.relative_to(OUT).as_posix() if path.is_relative_to(OUT) else "../../docs/arcana/B6A_POSITIVE_DURATION_KINEMATIC_AUTHORITY.md"
        blob = path.read_bytes()
        rows.append({"relative_path": rel, "byte_size": len(blob), "sha256": hashlib.sha256(blob).hexdigest()})
    _write_json(OUT / "B6A_ARTIFACT_MANIFEST.json", {"schema": "R6_B6A_ARTIFACT_MANIFEST_V1", "artifacts": rows, "manifest_self_hash": "OMITTED_BY_POLICY"})
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        data = run(args.repository_root.resolve())
        print(json.dumps({"decision": data["result"]["decision"], "source_commit": HEAD,
                          "motion_law": data["motion"]["positive_duration_motion_law_status"],
                          "topology_bound": data["topology"]["status"],
                          "joint_support": data["joint"]["status"]}, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"B6A_ADJUDICATION_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
