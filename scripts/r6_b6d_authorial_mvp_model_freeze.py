#!/usr/bin/env python3
"""Materialize and validate the R6 B6D authorial MVP model freeze."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "r6/b6d-authorial-mvp-first-step-model-freeze"
HEAD = "5f924e25300ea4e26281b4419620f9ed5ee9c500"
OUT = ROOT / "outputs/r6_b6d_authorial_mvp_model_freeze"
REPORT = ROOT / "docs/arcana/B6D_AUTHORIAL_MVP_FIRST_STEP_MODEL_FREEZE.md"
DECISION = "PASS_B6D_AUTHORIAL_MVP_FIRST_STEP_MODEL_FREEZE"
INPUTS = [
    "docs/arcana/B0_B_RECORD_STORE_IDENTITY_SUPPORT_CLOSURE.md",
    "docs/arcana/B0_C_PERSISTENCE_FAILURE_ATOMICITY_CLOSURE.md",
    "docs/arcana/B0_D_FORCING_REPLAY_CLOSURE.md",
    "docs/arcana/B0_E_QUERY_COMPLETION_CLOSURE.md",
    "outputs/r6_b6c_targeted_model_decision/B6C_RESULT.json",
    "outputs/r6_b6c_targeted_model_decision/B6C_AUTHORIAL_DECISION_REGISTER.json",
    "outputs/r6_b6c_targeted_model_decision/B6C_ROTATION_CONVENTION.json",
    "outputs/r6_b6c_targeted_model_decision/B6C_STATE_TRANSFER_MODEL.json",
    "outputs/r6_b6c_targeted_model_decision/B6C_NUMERICAL_VALIDITY_MODEL.json",
    "outputs/r6_b6c_targeted_model_decision/B6C_FIRST_DT_CLOSURE.json",
    "outputs/r6_b6b_accommodation_state_transfer/B6B_RESULT.json",
    "outputs/r6_b5_plate_support_topology_qualification/B5_TOPOLOGY_EVENT_CONTRACT.json",
    "docs/arcana/B0_G_MINIMAL_STATE_STORAGE_ACCOUNTING_CLOSURE.md",
    "docs/arcana/B0_F_REFINEMENT_ISOLATION_RECONSTRUCTION_CLOSURE.md",
    "docs/arcana/B0_H_SYNTHETIC_LIFECYCLE_INTEGRATION_CLOSURE.md",
    "scripts/r6_b6c_targeted_model_decision.py",
    "tests/test_r6_b6c_targeted_model_decision.py",
    "tests/test_r6_b6b_accommodation_state_transfer.py",
    "scripts/r6_b6d_authorial_mvp_model_freeze.py",
    "tests/test_r6_b6d_authorial_mvp_model_freeze.py",
]


class B6DError(ValueError):
    pass


def _git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if p.returncode:
        raise B6DError(f"git identity query failed: {' '.join(args)}")
    return p.stdout.strip()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adjudicate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    branch, head = _git(root, "branch", "--show-current"), _git(root, "rev-parse", "HEAD")
    if (branch, head) != (BRANCH, HEAD):
        raise B6DError(f"expected {BRANCH}@{HEAD}, found {branch}@{head}")
    inputs = []
    for name in INPUTS:
        path = root / name
        if not path.is_file():
            raise B6DError(f"required governed input missing: {name}")
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise B6DError(f"invalid JSON input: {name}") from exc
        inputs.append({"path": name, "byte_size": path.stat().st_size, "sha256": _sha(path)})

    decisions = {
        "schema": "R6_B6D_AUTHORIAL_DECISIONS_V1",
        "decisions": [
            {"id": "D1", "policy": "EVENT_DRIVEN_TOPOLOGY_HOLD", "authority": "AUTHORIAL_FREEZE", "semantics": ["topology unchanged between explicitly detected topology events", "no accepted interval crosses a known or detected unresolved topology event", "not an assertion of indefinite invariance", "topology changes only through governed event/transition", "27,123.405156307464 years is conditional rift activation horizon only; not generic topology window or dt"], "qualification_needed": "positive event detection or interval-specific validity evidence; unknown event classes fail closed"},
            {"id": "D2", "policy": "KINEMATIC_DISCONTINUOUS_INTERFACE", "authority": "AUTHORIAL_FREEZE", "semantics": ["rigid plate interiors under governed first-segment Euler rule", "adjacent plate velocities may differ at interface", "relative motion represented as kinematic discontinuity", "no fabricated shared-node velocity or averaging"], "unknowns_preserved": ["fault type", "polarity", "stress", "rheology", "slip law", "subduction", "uplift", "distributed deformation"]},
            {"id": "D3", "policy": "MULTI_INTERFACE_SET_VALUED_JUNCTION", "authority": "AUTHORIAL_FREEZE", "semantics": ["retain incident plate/interface relations at all 20 junctions", "no unique plate owner or residual allocation", "explicit compatibility relation required", "physical accommodation remains UNKNOWN", "plate-local representatives may be linked by junction relation"]},
            {"id": "D4", "policy": "PLATE_LOCAL_LAGRANGIAN_WITH_EXPLICIT_INTERFACE_REPRESENTATION", "authority": "AUTHORIAL_FREEZE", "semantics": ["plate-interior geometry follows rigid plate motion", "retain plate-local connectivity where valid", "do not force one shared boundary/junction node through incompatible transforms", "represent sides/duplicates only as runtime/candidate geometry with explicit topology links", "no global remesh; local remesh only after later validity trigger contract"]},
            {"id": "D5", "policy": "EXPLICIT_FIELD_SPECIFIC_TRANSFER_ONLY", "authority": "AUTHORIAL_FREEZE", "allowed_classes": ["IDENTITY_REFERENCE", "RIGID_ADVECT", "REINDEX_ONLY", "RECOMPUTE", "REPLAY", "CONSERVATIVE_REMAP_REQUIRED", "MODEL_REQUIRED", "UNKNOWN"], "rules": ["no implicit interpolation, averaging, nearest-neighbour or fabricated values", "preserve semantic identity when payload identity changes", "satisfy B0-G system memory", "unclosed transfer is MODEL_REQUIRED or UNKNOWN"]},
            {"id": "D6", "policy": "ASYNCHRONOUS_DOMAIN_VALIDITY", "authority": "AUTHORIAL_FREEZE", "semantics": ["tectonic advancement does not advance climate, hydrology, ecology, Deep or other domains", "each domain retains its latest valid state until its own provider/model updates it", "queries expose per-domain temporal validity; no fabricated synchronization"]},
            {"id": "D7", "policy": "MECHANICS_NOT_REQUIRED_BY_DEFAULT_FOR_FIRST_KINEMATIC_STEP", "authority": "AUTHORIAL_FREEZE", "semantics": ["MVP first transition may be kinematic", "ShellSet is deferred until mechanical response is causally, state-continuation or query required", "this does not assert mechanics is never required"]},
            {"id": "D8", "policy": "ADAPTIVE_CONSTRAINT_DRIVEN_TIMESTEP", "authority": "AUTHORIAL_FREEZE", "semantics": ["candidate interval is minimum applicable qualified positive bound", "only active qualified constraints participate", "rift horizon is only its event/model bound and is not automatically dt", "no dt selected in B6D"]},
        ],
        "rotation_contract": {"authority": "B6C_DERIVED_CONVENTION", "action": "ACTIVE_ROTATION_OF_COLUMN_POSITION_VECTOR", "handedness": "RIGHT_HANDED", "coordinates": "XYZ", "positive_z_test": "+Z maps +X toward +Y", "angular_rate_units": "rad/year", "frame": "internal synthetic gauge; not Earth-fixed or mantle-fixed"},
    }

    consistency = {"schema": "R6_B6D_MODEL_CONSISTENCY_V1", "status": "MODEL_CONTRACT_CONSISTENT", "checks": [
        {"pair": "D1 topology hold / event detector", "status": "IMPLEMENTATION_REQUIRED", "finding": "A hold between governed events is coherent only with positive event/validity evidence; detector completeness is not assumed."},
        {"pair": "D2 discontinuous interfaces / D4 plate-local geometry", "status": "MODEL_CONTRACT_CONSISTENT", "finding": "Plate-local sides avoid fabricating a shared coordinate for incompatible rigid transforms."},
        {"pair": "D3 set-valued junction / D2 interface", "status": "MODEL_CONTRACT_CONSISTENT", "finding": "Junction keeps all incident relations; explicit compatibility remains required and physical accommodation stays UNKNOWN."},
        {"pair": "D4 mesh / D5 field transfer", "status": "IMPLEMENTATION_REQUIRED", "finding": "Representation can be specified without moving canonical nodes; every field needs an explicit transfer class and lineage."},
        {"pair": "D5 transfer / B0-G system memory", "status": "QUALIFICATION_REQUIRED", "finding": "No discard is allowed; field-specific rules and replay/reconstruction must close for retained memory."},
        {"pair": "D6 asynchronous clocks / WORLD_HISTORY", "status": "MODEL_CONTRACT_CONSISTENT", "finding": "Per-domain latest-valid state is compatible with temporal query and provenance; no cross-domain state is fabricated."},
        {"pair": "D7 no default mechanics / D2 kinematic discontinuity", "status": "MODEL_CONTRACT_CONSISTENT", "finding": "Kinematics does not assert stress, strain or mechanical accommodation; mechanics remains conditional on later requirements."},
        {"pair": "D8 adaptive dt / D1 event-driven hold", "status": "IMPLEMENTATION_REQUIRED", "finding": "No first interval is admissible until active bounds and positive topology validity are qualified."},
        {"pair": "D1-D8 / governed T0 and UNKNOWN", "status": "MODEL_CONTRACT_CONSISTENT", "finding": "T0 remains source state; unknown boundary/junction/geology and unbound fields remain explicit UNKNOWN/MODEL_REQUIRED."},
    ], "scientific_contradictions": [], "interpretation": "No internal scientific contradiction found. Implementation and qualification gaps remain intentionally open."}

    interface = {"schema": "R6_B6D_BOUNDARY_INTERFACE_CONTRACT_V1", "status": "CONTRACT_ONLY_NO_GEOMETRY_MATERIALIZED", "records": [
        {"record": "PlateLocalInterior", "minimum_refs": ["source_state_id", "plate_id", "support_id", "connectivity_identity", "coordinate_payload_ref", "lineage_ref"], "invariant": "single plate support per interior element; rigid transform only under qualified interval"},
        {"record": "BoundarySide", "minimum_refs": ["boundary_identity", "incident_plate_id", "side_identity", "plate_local_geometry_ref", "source_boundary_ref"], "invariant": "two sides remain distinct when kinematic actions differ; unknown boundary type/polarity preserved"},
        {"record": "InterfaceRelation", "minimum_refs": ["boundary_identity", "side_refs", "plate_support_refs", "relative_motion_ref", "model_policy_id"], "invariant": "kinematic discontinuity; no averaging; physical stress/slip/accommodation unknown"},
        {"record": "JunctionSide", "minimum_refs": ["junction_identity", "incident_interface_ref", "incident_plate_id", "side_identity", "plate_local_geometry_ref"], "invariant": "set-valued incident support; no unique owner"},
        {"record": "JunctionRelation", "minimum_refs": ["junction_identity", "incident_side_refs", "compatibility_rule_id", "residual_status", "lineage_ref"], "invariant": "explicit multi-interface compatibility; fail closed when absent/unsatisfied; physical accommodation may remain UNKNOWN"},
        {"record": "TopologyIdentity", "minimum_refs": ["topology_state_id", "parent_topology_id", "plate_identity_set", "boundary_identity_set", "junction_identity_set", "event_ref_or_hold_ref"], "invariant": "append-only identity and explicit parent/event relation; no topology mutation in B6D"},
    ], "shared_payload_policy": "records reference existing identities/payloads; duplicate physical payload only when distinct side coordinates are later actually materialized and justified"}

    junction = {"schema": "R6_B6D_JUNCTION_CONTRACT_V1", "junction_count": 20, "support": "set-valued incident plates/interfaces", "owner_plate": None, "compatibility": {"required": True, "must_reference": ["all incident side/interface relations", "explicit compatibility equation/rule", "residual definition and qualified limit", "stop/event rule", "identity/lineage transfer"]}, "physical_accommodation": "UNKNOWN", "residual_allocation": "FORBIDDEN_UNLESS_LATER_GOVERNED", "status": "IMPLEMENTATION_AND_QUALIFICATION_REQUIRED"}

    state_families = [
        ("physical_geography", "spatial grid/cell support", "tectonic-only clock remains t0 unless a field model advances it", "MODEL_REQUIRED", "field-specific physical attachment and conservation are not established"),
        ("land_ocean", "surface-cell support", "independent domain clock", "MODEL_REQUIRED", "requires governed surface/water update rule"),
        ("province_state", "province identity/support", "independent domain clock", "MODEL_REQUIRED", "province attachment and boundary semantics unbound"),
        ("topography", "surface support", "independent domain clock", "MODEL_REQUIRED", "no uplift/subsidence/erosion or hold law selected"),
        ("tectonic_plate_partition", "plate/cell support at T0", "tectonic topology identity changes only on governed event", "IDENTITY_REFERENCE under topology hold; REINDEX_ONLY on explicit event; else MODEL_REQUIRED", "preserve parent identity and event lineage"),
        ("plate_kinematics", "plate identity; Euler forcing support", "conditional first-segment validity only", "REPLAY / IDENTITY_REFERENCE within selected segment; UNKNOWN beyond", "forcing and recipe must be retained/replayable"),
        ("tectonic_kinematics_grid", "spatial support absent", "not established", "UNKNOWN", "do not spatialize plate rates without rule"),
        ("boundary_classification", "boundary identity", "not established", "UNKNOWN", "no type/polarity inference"),
        ("bathymetry", "surface/water support", "independent domain clock", "UNKNOWN; RECOMPUTE only after governed surface model", "no implicit interpolation"),
        ("deep", "deep-domain support absent", "independent domain clock", "UNKNOWN / passive", "coupling model required"),
        ("climate", "climate-domain support", "clock remains at latest valid time", "UNKNOWN / passive", "no climate(t1)=climate(t0) fabrication"),
        ("hydrology", "hydrology-domain support", "clock remains at latest valid time", "UNKNOWN / passive", "no hydrology(t1)=hydrology(t0) fabrication"),
        ("weak_zone_state", "weak-zone support absent", "not established", "UNKNOWN", "must not initialize to zero; model required if consumed"),
        ("junction_physical_semantics", "20 junction identities and incident relations", "topology event validity", "UNKNOWN", "requires explicit multi-interface physical closure if used"),
        ("FEG/ShellSet runtime fields", "numerical runtime support", "derived per candidate runtime", "RECOMPUTE from governed inputs; not canonical state", "no authority promotion from runtime artifacts"),
    ]
    transfer = {"schema": "R6_B6D_STATE_TRANSFER_MATRIX_V1", "status": "EXPLICIT_FIELD_SPECIFIC_TRANSFER_ONLY", "source_inventory": "B6C T0 family inventory (15 families)", "families": [
        {"family": f, "support": s, "temporal_validity": t, "transfer_class": c, "required_model": reason, "conservation_requirement": "NOT_INFERRED; define field-specific invariant if physically applicable", "recompute_or_replay": "use governed recipe/provider only; otherwise do not fabricate", "unknown_behavior": "retain UNKNOWN or MODEL_REQUIRED; never substitute a value"}
        for f, s, t, c, reason in state_families
    ], "global_rule": "B0-G SYSTEM_MEMORY remains retained/reconstructable; no family is silently discarded or interpolated."}

    event = {"schema": "R6_B6D_TOPOLOGY_EVENT_POLICY_V1", "policy": "EVENT_DRIVEN_TOPOLOGY_HOLD", "known_detectable_events": [{"event": "conditional rift activation", "evidence": "Census V3 / governed rift guard", "horizon_years": 27123.405156307464, "scope": "that conditional rift model only", "generic_topology_bound": False}], "unsupported_or_unqualified_event_classes": ["plate split", "plate merge", "boundary birth", "boundary death", "junction reassignment", "other unenumerated topology events"], "event_fields": {"event_time": "must be bounded/detected before accepted interval; currently not available for general topology", "precondition": "governed event eligibility and support predicates", "transition": "explicit event-specific topology and identity/lineage map", "post_event_model": "explicitly selected successor model and validity qualification"}, "absence_of_detector_means_absence": False, "first_dt_gap": "demonstrate complete applicable event detection OR a positive interval-specific topology validity basis that conservatively fails closed for unsupported event classes", "status": "BLOCKS_FIRST_DT_ADJUDICATION"}

    numeric_rows = [
        ("positive_duration_kinematics", "positive-duration first-segment validity", "year", "governed Euler forcing support", "validate conditional constant-T0 Euler segment and its usable positive interval", "B6A conditional first-segment law; no renewal law", "MODEL_QUALIFICATION_REQUIRED", False),
        ("rotation_angle", "maximum angular displacement", "rad", "plate support", "max_plate_norm_omega_times_dt", "first-segment Euler authority + selected accuracy model", "THRESHOLD_MISSING", False),
        ("node_displacement", "maximum supported node displacement", "m", "node/plate-local geometry", "max spherical arc displacement", "mesh/geometric accuracy model", "THRESHOLD_MISSING", False),
        ("local_edge_fraction", "displacement/local-edge-length ratio", "1", "supported nodes and incident edges", "per-node displacement divided by governed edge length", "spatial accuracy contract", "THRESHOLD_MISSING", False),
        ("interface_guard", "boundary gap/crossing/overlap residual", "m or normalized residual", "each interface side pair", "selected interface geometry guard", "D2/D4 interface model", "MODEL_QUALIFICATION_REQUIRED", False),
        ("mesh_quality", "minimum element quality/inversion", "dimensionless", "plate-local elements", "oriented area/Jacobian quality after candidate transfer", "mesh validity and lineage contract", "MODEL_QUALIFICATION_REQUIRED", False),
        ("topology_event_bound", "event time or positive validity duration", "year", "all applicable topology/event classes", "qualified detector or interval validity proof", "D1 event policy", "MODEL_QUALIFICATION_REQUIRED", False),
        ("remesh_trigger", "predeclared mesh validity trigger", "model-specific", "only if remesh is later selected", "deterministic trigger plus parent-child mapping", "D4 mesh policy", "NOT_APPLICABLE_TO_MVP", False),
        ("solver_stability", "solver stability/convergence bound", "solver-specific", "mechanics solver", "qualified solver estimator", "D7; no mechanics required by default", "NOT_APPLICABLE_TO_MVP", True),
        ("rift_activation_horizon", "conditional rift activation event horizon", "year", "eligible rift support only", "Census V3 governed event guard", "existing rift authority", "BOUND_AVAILABLE", False),
    ]
    numeric = {"schema": "R6_B6D_NUMERICAL_CONSTRAINT_CONTRACT_V1", "dt_policy": "ADAPTIVE_CONSTRAINT_DRIVEN_TIMESTEP", "dt_selected": False, "candidate_rule": "minimum positive bound among applicable qualified constraints only", "constraints": [
        {"constraint_id": cid, "quantity": q, "units": u, "support": s, "evaluation_method": ev, "authority_source": auth, "threshold_status": stat, "solver_dependency": solver, "applicability": "MVP_ACTIVE_CANDIDATE" if stat not in {"NOT_APPLICABLE_TO_MVP"} else "MVP_NOT_APPLICABLE", "failure_semantics": "fail closed; no positive dt if an applicable bound is absent/unqualified"}
        for cid, q, u, s, ev, auth, stat, solver in numeric_rows
    ], "rift_horizon_warning": "not dt; not generic topology validity; not necessarily minimum active constraint"}

    query = {"schema": "R6_B6D_MVP_QUERY_ACCEPTANCE_V1", "status": "CONTRACT_MATERIALIZED_NOT_EXECUTED_OVER_T1", "queries": [
        {"query": "STATE", "acceptance": "return state for requested age/location/support with source identity, authority and per-domain temporal validity; unsupported values remain UNKNOWN"},
        {"query": "HISTORY", "acceptance": "return ordered causal records between states, including forcing, events, models and provenance"},
        {"query": "DIFFERENCE", "acceptance": "report actual changed fields/support and distinguish unchanged, absent and UNKNOWN"},
        {"query": "WHY", "acceptance": "trace changed state to forcing/model/event/authority and replay recipe"},
        {"query": "SUPPORT", "acceptance": "return set-valued plate/interface/junction support without implicit owner"},
        {"query": "REPLAY", "acceptance": "reconstruct candidate deterministically from retained state, forcing, model and recipe identities"},
        {"query": "REFINEMENT", "acceptance": "recompute a bounded region/interval in an isolated branch while preserving parent identity and lineage"},
        {"query": "UNKNOWN", "acceptance": "preserve unknown/missing support without default zero, interpolation or inference"},
        {"query": "TEMPORAL_VALIDITY", "acceptance": "report each domain's latest valid time; tectonics at t1 does not imply climate/hydrology/ecology/Deep at t1"},
    ], "fixture_scope": "future synthetic tests may qualify contract; no T1 query is run in B6D"}

    decisions_register = {"schema": "R6_B6D_DECISION_REGISTER_V1", "authorial_decisions_frozen": [f"D{i}" for i in range(1, 9)], "derived_contract": ["rotation action convention from B6C"], "still_open_before_first_dt": ["event detector/positive topology validity", "field and system-memory transfer implementation", "junction/interface compatibility implementation and qualification", "mesh validity/lineage contract implementation", "active numerical thresholds and estimators"]}
    feature_policy = {"schema": "R6_B6D_QUERY_DRIVEN_FEATURE_POLICY_V1", "entry_conditions": ["required for causal coherence", "required to continue state correctly", "required by an objective WORLD_HISTORY query", "required for deterministic replay/refinement"], "otherwise": "DEFER_FEATURE_NO_CURRENT_QUERY_OR_CAUSAL_REQUIREMENT", "future_scientific_improvement_allowed": True, "review_record": ["feature", "satisfied condition", "causal/query/state requirement", "authority and uncertainty", "new state/transfer/replay obligations"]}
    mechanics = {"schema": "R6_B6D_MECHANICS_DECISION_V1", "decision": "MVP_FIRST_STEP_KINEMATIC_NO_MECHANICS_REQUIRED", "scope": "MVP first kinematic step only", "shellset_status": "SHELLSET_DEFERRED_UNTIL_MECHANICAL_RESPONSE_REQUIRED", "reopen_trigger": ["causal requirement", "state continuation requirement", "objective query requires stress/strain/finite-width deformation/uplift/fault mechanics"], "not_a_claim": "mechanics is never required"}
    gaps = {"schema": "R6_B6D_REMAINING_GAPS_V1", "first_dt_readiness": "NOT_READY_FOR_FIRST_DT", "minimal_blocking_set": [
        {"gap": "positive topology validity/event coverage", "execution_target": "WINDOWS", "why": "event-driven hold needs detector qualification or interval-specific positive validity evidence"},
        {"gap": "interface and junction representation/compatibility", "execution_target": "WINDOWS", "why": "implement side-valued support and explicit multi-interface relations without physical accommodation invention"},
        {"gap": "field-specific state and SYSTEM_MEMORY transfer", "execution_target": "WINDOWS", "why": "materialize only justified transfer classes; unsupported fields stay MODEL_REQUIRED/UNKNOWN"},
        {"gap": "mesh validity and lineage qualification", "execution_target": "EITHER", "why": "qualify plate-local transforms, interface sides and deterministic lineage; no remesh unless triggered"},
        {"gap": "active numerical thresholds/estimators", "execution_target": "EITHER", "why": "bind measured quantities, units, tolerance rationale and fail-closed tests"},
        {"gap": "conditional positive-duration segment qualification", "execution_target": "UBUNTU_WORKSTATION", "why": "qualify computational behavior only after contracts and bounds are closed; no mechanics required by default"},
    ], "not_blocking_by_default": ["ShellSet/mechanics; deferred unless a causal, state-continuation or query requirement activates it"]}
    execution = {"schema": "R6_B6D_EXECUTION_PLAN_V1", "ordered_stages": [
        {"stage": "B6E_MINIMAL_CONTRACT_IMPLEMENTATION", "target": "WINDOWS", "scope": "interfaces, junction sets, field transfer metadata, query-contract synthetic tests; no canonical motion"},
        {"stage": "B6F_EVENT_AND_NUMERICAL_QUALIFICATION", "target": "EITHER", "scope": "detector coverage, positive validity, thresholds, mesh/interface bounds; no dt selection"},
        {"stage": "B7_FIRST_DT_ADJUDICATION", "target": "WINDOWS", "scope": "calculate candidate from all active qualified bounds and review authorial gates; no automatic T1"},
        {"stage": "HEAVY_NUMERICAL_QUALIFICATION_IF_NEEDED", "target": "UBUNTU_WORKSTATION", "scope": "large sweeps or expensive numerical qualification only"},
    ], "authorization": "B6D authorizes no T0 motion, dt, T1 or forward evolution"}

    result = {"schema": "R6_B6D_RESULT_V1", "decision": DECISION, "branch": branch, "qualified_source_commit": head, "authorial_decisions_frozen": [f"D{i}" for i in range(1, 9)], "model_consistency_status": "MODEL_CONTRACT_CONSISTENT", "rotation_contract_status": "DERIVED_CONTRACT_CLOSED", "topology_policy_status": "FROZEN_EVENT_DRIVEN_TOPOLOGY_HOLD__VALIDITY_QUALIFICATION_REQUIRED", "boundary_model_status": "FROZEN_KINEMATIC_DISCONTINUOUS_INTERFACE", "junction_model_status": "FROZEN_MULTI_INTERFACE_SET_VALUED__COMPATIBILITY_IMPLEMENTATION_REQUIRED", "mesh_representation_status": "FROZEN_PLATE_LOCAL_LAGRANGIAN_WITH_EXPLICIT_INTERFACE_REPRESENTATION", "state_transfer_policy_status": "FROZEN_EXPLICIT_FIELD_SPECIFIC_TRANSFER_ONLY__MATRIX_OPEN", "asynchronous_clock_status": "FROZEN_ASYNCHRONOUS_DOMAIN_VALIDITY", "timestep_policy_status": "FROZEN_ADAPTIVE_CONSTRAINT_DRIVEN__NO_DT_SELECTED", "mvp_mechanics_decision": mechanics["decision"], "shellset_status": mechanics["shellset_status"], "topology_event_gaps": gaps["minimal_blocking_set"][0]["gap"], "state_transfer_gaps": gaps["minimal_blocking_set"][2]["gap"], "numerical_constraint_gaps": gaps["minimal_blocking_set"][4]["gap"], "mvp_query_acceptance_status": query["status"], "first_dt_readiness": "NOT_READY_FOR_FIRST_DT", "next_stage_recommendation": "AUTHORIZE_MINIMAL_MVP_MODEL_IMPLEMENTATION", "maximum_next_authorization": "AUTHORIZE_MINIMAL_MVP_MODEL_IMPLEMENTATION", "production_source_changes": False, "scientific_side_effect_check": {"canonical_state_changed": False, "canonical_node_motion_executed": False, "canonical_topology_mutated": False, "dt_selected": False, "t1_created": False, "mechanics_authorized": False, "shellset_executed": False, "orbdata_mechanics_executed": False, "forward_evolution_authorized": False, "runtime_authorized": True, "runtime_authorized_scope": "LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE"}}
    validate({"result": result, "decisions": decisions, "consistency": consistency, "transfer": transfer, "numeric": numeric, "event": event, "query": query, "gaps": gaps, "mechanics": mechanics})
    return {"result": result, "decisions": decisions, "consistency": consistency, "interface": interface, "junction": junction, "transfer": transfer, "event": event, "numeric": numeric, "query": query, "decision_register": decisions_register, "feature_policy": feature_policy, "mechanics": mechanics, "gaps": gaps, "execution": execution, "inputs": inputs}


def validate(data: dict[str, Any]) -> bool:
    r = data["result"]
    if r["decision"] != DECISION or r["qualified_source_commit"] != HEAD:
        raise B6DError("B6D identity/decision mismatch")
    if len(data["decisions"]["decisions"]) != 8:
        raise B6DError("D1-D8 are not all materialized")
    if data["consistency"]["scientific_contradictions"]:
        raise B6DError("scientific contradiction requires stop")
    if r["first_dt_readiness"] != "NOT_READY_FOR_FIRST_DT":
        raise B6DError("B6D must not authorize first dt")
    gates = r["scientific_side_effect_check"]
    for key in ("canonical_state_changed", "canonical_node_motion_executed", "canonical_topology_mutated", "dt_selected", "t1_created", "mechanics_authorized", "shellset_executed", "orbdata_mechanics_executed", "forward_evolution_authorized"):
        if gates[key] is not False:
            raise B6DError(f"scientific safety gate opened: {key}")
    return True


def _report(d: dict[str, Any]) -> str:
    r = d["result"]
    lines = [
        "# R6 B6D Authorial MVP First-Step Model Freeze", "",
        f"Decision: **{r['decision']}**. Qualified source `{r['qualified_source_commit']}` on `{r['branch']}`.", "",
        "## Frozen decisions", "",
        "D1 event-driven topology hold; D2 kinematic discontinuous interfaces; D3 set-valued multi-interface junctions; D4 plate-local Lagrangian representation with explicit interface sides; D5 explicit field-specific transfer; D6 asynchronous domain clocks; D7 no mechanics requirement by default for the first kinematic step; D8 adaptive constraint-driven timestep. These freeze the MVP contract, not an executed trajectory.", "",
        "Rotation uses the B6C-derived active, right-handed XYZ column-vector convention; +Z maps +X toward +Y, Euler rates are rad/year, and the frame is an internal synthetic gauge.", "",
        "## Consistency and implementation boundary", "",
        "The decisions are mutually consistent and preserve T0 authority and UNKNOWN. The event-driven hold does not imply indefinite invariance: the current conditional rift horizon (27,123.405156307464 years) is only that rift model's event horizon and is neither a generic topology bound nor dt. Unsupported event classes fail closed.", "",
        "The interface contract defines references for plate-local interiors, boundary sides, interface relations, junction sides/relations and topology identity. It materializes no geometry and assigns no physical boundary type, polarity, accommodation, stress, rheology or residual allocation.", "",
        "The state-transfer matrix covers the 15 B6C state families. Unbound families remain MODEL_REQUIRED/UNKNOWN; there is no implicit interpolation or value fabrication. B0-G SYSTEM_MEMORY remains retained/reconstructable. Domain clocks remain independent.", "",
        "## Mechanics, dt and next work", "",
        "MVP decision: `MVP_FIRST_STEP_KINEMATIC_NO_MECHANICS_REQUIRED`. ShellSet is `SHELLSET_DEFERRED_UNTIL_MECHANICAL_RESPONSE_REQUIRED`, not removed from the roadmap. First dt remains `NOT_READY_FOR_FIRST_DT` until topology validity, interface/junction, transfer, mesh validity and active numerical bounds are implemented and qualified.", "",
        "MVP query acceptance is specified for STATE, HISTORY, DIFFERENCE, WHY, SUPPORT, REPLAY, REFINEMENT, UNKNOWN and TEMPORAL_VALIDITY; no T1 queries are run.", "",
        "Next recommendation: `AUTHORIZE_MINIMAL_MVP_MODEL_IMPLEMENTATION`. This does not authorize dt, T1 or forward evolution.", "",
        "Scientific side effects: none. No canonical state or payload changed; no node movement, topology mutation, mechanics, ShellSet, OrbData mechanics, dt or T1 was executed.", "",
    ]
    tests = d.get("test_results")
    if tests:
        lines += [f"Validation: focused B6D {tests['focused_b6d']['tests_passed']} passed; full active R6 {tests['active_r6']['tests_passed']} passed; py_compile {tests['py_compile']}; JSON/manifest {tests['json_manifest_validation']}; portable paths {tests['portable_path_validation']}; diff check {tests['diff_check']}.", ""]
    return "\n".join(lines)


def run(root: Path = ROOT) -> dict[str, Any]:
    d = adjudicate(root)
    out = root / OUT.relative_to(ROOT)
    report = root / REPORT.relative_to(ROOT)
    out.mkdir(parents=True, exist_ok=True)
    test_path = out / "B6D_TEST_RESULTS.json"
    if test_path.is_file():
        d["test_results"] = json.loads(test_path.read_text(encoding="utf-8"))
        d["result"]["qualification_validation"] = d["test_results"]
    artifacts = {
        "B6D_RESULT.json": d["result"], "B6D_AUTHORIAL_DECISIONS.json": d["decisions"],
        "B6D_MODEL_CONSISTENCY.json": d["consistency"], "B6D_ROTATION_CONTRACT.json": d["decisions"]["rotation_contract"],
        "B6D_TOPOLOGY_EVENT_POLICY.json": d["event"], "B6D_BOUNDARY_INTERFACE_CONTRACT.json": d["interface"],
        "B6D_JUNCTION_CONTRACT.json": d["junction"], "B6D_MESH_REPRESENTATION_CONTRACT.json": {"schema": "R6_B6D_MESH_REPRESENTATION_V1", "policy": d["decisions"]["decisions"][3]["policy"], "semantics": d["decisions"]["decisions"][3]["semantics"], "canonical_nodes_moved": False, "remeshing_authorized": False},
        "B6D_STATE_TRANSFER_MATRIX.json": d["transfer"], "B6D_ASYNCHRONOUS_CLOCK_POLICY.json": d["decisions"]["decisions"][5],
        "B6D_NUMERICAL_CONSTRAINT_CONTRACT.json": d["numeric"], "B6D_MECHANICS_DECISION.json": d["mechanics"],
        "B6D_MVP_QUERY_ACCEPTANCE_CONTRACT.json": d["query"], "B6D_QUERY_DRIVEN_FEATURE_POLICY.json": d["feature_policy"],
        "B6D_REMAINING_GAPS.json": d["gaps"], "B6D_EXECUTION_PLAN.json": d["execution"],
        "B6D_INPUT_EVIDENCE.json": {"schema": "R6_B6D_INPUT_EVIDENCE_V1", "qualified_source_commit": HEAD, "inputs": d["inputs"]},
    }
    if "test_results" in d:
        artifacts["B6D_TEST_RESULTS.json"] = d["test_results"]
    for name, value in artifacts.items():
        _write_json(out / name, value)
    (out / "README.md").write_text("# R6 B6D evidence package\n\nAuthorial MVP model freeze and contract materialization only. No T0 motion, dt, T1, mechanics or forward evolution is executed.\n", encoding="utf-8", newline="\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(_report(d), encoding="utf-8", newline="\n")
    rows = []
    for path in sorted([p for p in out.iterdir() if p.is_file() and p.name != "B6D_ARTIFACT_MANIFEST.json"] + [report], key=lambda p: p.as_posix()):
        rel = path.relative_to(out).as_posix() if path.is_relative_to(out) else "../../docs/arcana/B6D_AUTHORIAL_MVP_FIRST_STEP_MODEL_FREEZE.md"
        content = path.read_bytes()
        rows.append({"relative_path": rel, "byte_size": len(content), "sha256": hashlib.sha256(content).hexdigest(), "role": "qualification evidence" if path != report else "human closure report"})
    _write_json(out / "B6D_ARTIFACT_MANIFEST.json", {"schema": "R6_B6D_ARTIFACT_MANIFEST_V1", "artifacts": rows, "manifest_self_hash": "OMITTED_BY_POLICY"})
    return d


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = run(args.repository_root.resolve())["result"]
        print(json.dumps({"decision": result["decision"], "qualified_source_commit": result["qualified_source_commit"], "consistency": result["model_consistency_status"], "mechanics": result["mvp_mechanics_decision"], "first_dt": result["first_dt_readiness"], "next_authorization": result["maximum_next_authorization"]}, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"B6D_FREEZE_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

