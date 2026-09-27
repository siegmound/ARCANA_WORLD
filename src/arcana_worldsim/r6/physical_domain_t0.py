"""Bind the governed ARCANA synthetic physical T0 to the history core."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any

from .identity import BranchId, HistoryId
from .planning import Availability, BindingStatus, DOMAIN_REGISTRY, DomainRegistry
from .provenance import ProvenanceRecord
from .query import HistoryQueryService
from .state import AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport
from .store import HistoryStore
from .temporal import AuthorityAnchor, HistoricalSnapshot, RefinementAnchor

PARENT_SHA = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
VECTOR_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
KINEMATICS_SHA = "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4"
GRID_ID = "R6_GLOBAL_GEOGRAPHY_1DEG_V1"
UNKNOWN_FIELDS = (
    "bathymetry", "deep", "climate", "hydrology", "weak_zone_state",
    "boundary_classification", "junction_physical_semantics",
)

ARTIFACTS = {
    "R6_SIMULATION1_PHYSICAL_GEOGRAPHY_T0_BINDING.json": "HISTORICAL_SUPERSEDED",
    "R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.json": "CURRENT_SUPPORTING_EVIDENCE",
    "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json": "CURRENT_AUTHORITY",
    "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json": "CURRENT_AUTHORITY",
    "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json": "CURRENT_AUTHORITY",
    "R6_T0_INITIAL_KINEMATICS_MANIFEST.json": "CURRENT_AUTHORITY",
    "R6_T0_CANONICAL_PLATE_KINEMATICS.json": "CURRENT_AUTHORITY",
    "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.json": "CURRENT_SUPPORTING_EVIDENCE",
    "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json": "CURRENT_SUPPORTING_EVIDENCE",
    "R6_T0_EVENT_ELIGIBILITY_CENSUS.json": "HISTORICAL_SUPERSEDED",
    "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json": "CURRENT_AUTHORITY",
    "R6_T0_FIRST_INTERVAL_EVENT_GUARD.json": "HISTORICAL_SUPERSEDED",
    "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json": "CURRENT_SUPPORTING_EVIDENCE",
    "R6_T0_CONTINUUM_DEFORMATION_GUARD.json": "CURRENT_SUPPORTING_EVIDENCE",
    "R6_T0_BOUNDARY_ZONE_REFERENCE_MAP_MANIFEST.json": "DIAGNOSTIC_ONLY",
    "R6_T0_BOUNDARY_ZONE_REFERENCE_VALIDATION.json": "DIAGNOSTIC_ONLY",
    "R6_T0_CONTINUUM_REFERENCE_VALIDATION.json": "DIAGNOSTIC_ONLY",
    "R6_STATIC_T0_CONTINUUM_VELOCITY_VALIDATION.json": "DIAGNOSTIC_ONLY",
    "R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json": "BLOCKER",
    "R6_TOPOLOGY_CONTACT_GUARD.json": "BLOCKER",
    "R6_JUNCTION_COMPATIBILITY_CONTRACT.json": "BLOCKER",
    "R6_FIRST_INTERVAL_DT_LIMIT_REGISTER.json": "BLOCKER",
    "R6_FIRST_INTERVAL_NUMERICAL_STEPPING_CONTRACT.json": "BLOCKER",
    "R6_JUNCTION_PATCH_OPERATOR_VALIDATION.json": "BLOCKER",
    "R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION.json": "BLOCKER",
    "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19.json": "BLOCKER",
    "R6_PYGPLATES_CANONICAL_MAPPING_REPORT.json": "CURRENT_SUPPORTING_EVIDENCE",
    "R6_PYGPLATES_TOPOLOGY_ASSEMBLY_REPORT.json": "DIAGNOSTIC_ONLY",
    "R6_PYGPLATES_STATIC_TOPOLOGY_RESOLUTION_REPORT.json": "DIAGNOSTIC_ONLY",
}

P_REQUIREMENTS = [
    ("P01", "Initial plate kinematics", "BOUND_FOR_CANONICAL_SYNTHETIC_T0_REALIZATION", True, True, False,
     "R6_T0_INITIAL_KINEMATICS_MANIFEST.json", "One authorial stochastic realization; not empirical motion."),
    ("P02", "Motion segment validity", "BOUND_ONLY_FOR_T0_SNAPSHOT", True, False, False,
     "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json", "Positive-duration validity and acceptance horizon remain unspecified."),
    ("P03", "Motion renewal/change law", "UNBOUND", False, False, False,
     "R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json", "Required before the initial motion segment is renewed; no renewal is asserted within the current segment."),
    ("P04", "Master plate geometry", "MATERIALIZED_AND_VALIDATED", True, True, False,
     "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json", "12 plates, 64,800 parent faces, 1,983 boundary segments; coarse support on parent grid."),
    ("P05", "Weak-zone state/strength", "UNKNOWN_PRESERVED", False, False, False,
     "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json", "Weak-zone state remains UNKNOWN; it is not required by the current minimal guard, but richer rift laws require it."),
    ("P06", "Extensional forcing", "KINEMATIC_DIAGNOSTIC_BOUND", True, True, False,
     "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json", "Relative kinematics are diagnostics, not stress or force."),
    ("P07", "Rift eligibility", "BOUND_FOR_MINIMAL_GUARD_AT_T0", True, True, False,
     "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json", "26 eligible-quiescent, 4 ineligible, 0 unknown; fixed synthetic t0 motion."),
    ("P08", "Rift initiation trigger", "BOUNDED_MODEL_GUARD__NO_EVENT_CREATED", True, True, False,
     "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json", "5–30 km authorial threshold envelope; no threshold sample. Conditional horizon is not dt."),
    ("P09", "Plate split topology", "DEFERRED_UNTIL_RIFT_EVENT", True, False, True,
     "R6_T0_SYNTHETIC_TECTONIC_STATE_CANONICALIZATION.json", "No split law or event geometry; needed before a topology-changing event."),
    ("P10", "Initial eligibility census", "CURRENT_CENSUS_COMPLETE", True, True, False,
     "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json", "V3 supersedes V1; current census classifies all 30 adjacent pairs."),
    ("P11", "Numerical acceptance and step limits", "BLOCKED", False, True, False,
     "R6_FIRST_INTERVAL_NUMERICAL_STEPPING_CONTRACT.json", "No positive dt; topology/contact and junction-compatible transition rule and production tolerances unbound."),
    ("P12", "Uncertainty", "BOUND_FOR_SINGLE_T0_REALIZATION", True, True, False,
     "R6_T0_CANONICAL_PLATE_KINEMATICS.json", "One model realization with explicit model assumptions; no ensemble or Earth-data authority."),
]


def _read(root: Path, name: str) -> dict[str, Any]:
    return json.loads((root / name).read_text(encoding="utf-8"))


def _git_origin(root: Path, name: str) -> str | None:
    try:
        result = subprocess.run(["git", "log", "-1", "--format=%H", "--", name],
                                cwd=root, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def authority_lineage(root: Path) -> list[dict[str, Any]]:
    output = []
    for name, classification in ARTIFACTS.items():
        path = root / name
        if not path.is_file():
            output.append({"artifact": name, "classification": "UNKNOWN_PRECEDENCE",
                           "present": False})
            continue
        raw = path.read_bytes()
        parsed = json.loads(raw.decode("utf-8"))
        output.append({
            "artifact": name,
            "sha256": sha256(raw).hexdigest(),
            "stage": parsed.get("schema", parsed.get("stage", "not-recorded")),
            "date": parsed.get("created_at", parsed.get("date", "not-recorded")),
            "commit": _git_origin(root, name),
            "authority_class": parsed.get("authority_class", parsed.get("decision", "see artifact")),
            "status": parsed.get("status", parsed.get("decision", "not-recorded")),
            "classification": classification,
            "current_role": _artifact_role(name, classification),
            "supersedes": _supersedes(name),
        })
    return output


def _artifact_role(name: str, classification: str) -> str:
    if name == "R6_SIMULATION1_PHYSICAL_GEOGRAPHY_T0_BINDING.json":
        return "Earlier recovery-stage result; scoped to recovering Simulation1, not current synthetic canonical T0."
    if name == "R6_T0_EVENT_ELIGIBILITY_CENSUS.json":
        return "V1 historical census; superseded for current minimal guard by precommitted-law V3 census."
    if name == "R6_T0_FIRST_INTERVAL_EVENT_GUARD.json":
        return "Historical guard over V1 unknown classifications; superseded for current event horizon only."
    if name == "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json":
        return "Canonical t0 vector support, derived from parent payload; preserves coarse support semantics."
    return classification


def _supersedes(name: str) -> list[str]:
    if name == "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json":
        return ["R6_T0_EVENT_ELIGIBILITY_CENSUS.json"]
    if name == "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json":
        return ["R6_T0_FIRST_INTERVAL_EVENT_GUARD.json"]
    if name == "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json":
        return ["R6_SIMULATION1_PHYSICAL_GEOGRAPHY_T0_BINDING.json"]
    return []


def bind_physical_t0(root: str | Path, store_root: str | Path) -> dict[str, Any]:
    """Validate governed identities, append immutable T0 records, and report gates."""
    root = Path(root)
    material = _read(root, "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json")
    vector = _read(root, "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    kinematics = _read(root, "R6_T0_CANONICAL_PLATE_KINEMATICS.json")
    junctions = _read(root, "R6_JUNCTION_COMPATIBILITY_CONTRACT.json")
    kin_body = dict(kinematics)
    embedded_kin_sha = kin_body.pop("payload_identity_sha256")
    kin_actual = sha256((json.dumps(kin_body, sort_keys=True, ensure_ascii=False,
                                    indent=2, allow_nan=False) + "\n").encode()).hexdigest()
    validations = {
        "materialization_validated": material.get("status") == "MATERIALIZED_AND_VALIDATED",
        "parent_payload_identity_matches_manifest": material["payload"]["sha256"] == PARENT_SHA,
        "vector_payload_identity_matches_manifest": vector["payload"]["sha256"] == VECTOR_SHA,
        "kinematics_payload_identity_recomputed": kin_actual == KINEMATICS_SHA == embedded_kin_sha,
        "vector_parent_identity_matches": vector["canonical_parent_sha256"] == PARENT_SHA,
        "kinematics_parent_identity_matches": kinematics["parent_canonical_t0_sha256"] == PARENT_SHA,
        "kinematics_vector_identity_matches": kinematics["parent_vector_partition_sha256"] == VECTOR_SHA,
        "time_and_grid_match": material["time_ma"] == 210.0 and vector["time_ma"] == 210.0
            and material["grid"]["grid_id"] == GRID_ID and vector["parent_grid"]["grid_id"] == GRID_ID,
        "topology_counts_match": vector["topology"]["plate_count"] == 12
            and vector["topology"]["face_count"] == 64800
            and vector["topology"]["positive_length_boundary_edge_count"] == 1983
            and vector["topology"]["positive_length_adjacency_pair_count"] == 30
            and junctions["junction_count"] == 20,
    }
    if not all(validations.values()):
        raise ValueError(f"canonical T0 authority validation failed: {validations}")

    history_id, branch_id = material["history_id"], material["branch_id"]
    history_id = str(HistoryId(history_id))
    branch_id = str(BranchId(branch_id))
    store = HistoryStore(store_root)
    sources = tuple(ARTIFACTS)
    provenance = ProvenanceRecord.create(
        activity="bind_governed_canonical_physical_t0_to_world_history",
        input_refs=(f"payload://sha256/{PARENT_SHA}", f"payload://sha256/{VECTOR_SHA}",
                    f"payload://sha256/{KINEMATICS_SHA}"),
        source_refs=sources,
        attributes={"authority": "ARCANA_AUTHORIAL_SYNTHETIC_T0",
                    "time_ma": 210.0, "grid_id": GRID_ID,
                    "payloads_copied_or_modified": False,
                    "forward_evolution": False},
    )
    provenance_id = store.append_provenance(provenance)
    state = DomainStateEnvelope.create(
        history_id=history_id, branch_id=branch_id, domain="physical_world",
        time_support=TimeSupport("210 Ma", "ARCANA_GEOLOGICAL_TIME_MA", "SNAPSHOT"),
        spatial_support=SpatialSupport(GRID_ID, (),
            "1-degree nominal parent grid; vector edges COARSE_SUPPORT_ON_FINE_GRID", "GLOBAL"),
        support_class=SupportClass.DERIVED_SUPPORTED,
        authority_class=AuthorityClass.DERIVED_AUTHORITY,
        value={
            "canonical_state_id": "r6state_d2e959c596bb1741d652c9d5f1d733b0d365cc9dbe362975048bc5ee3d3dca78",
            "canonical_parent_payload": f"payload://sha256/{PARENT_SHA}",
            "vector_partition_payload": f"payload://sha256/{VECTOR_SHA}",
            "initial_kinematics_identity": f"sha256:{KINEMATICS_SHA}",
            "plate_count": 12, "parent_face_count": 64800,
            "boundary_segment_count": 1983, "adjacent_plate_pair_count": 30,
            "junction_count": junctions["junction_count"],
            "boundary_support": "COARSE_SUPPORT_ON_FINE_GRID",
            "unknown_fields": list(UNKNOWN_FIELDS),
        },
        uncertainty={"class": "AUTHORIAL_SYNTHETIC_INITIALIZATION_AND_SINGLE_STOCHASTIC_KINEMATICS_REALIZATION",
                     "kinematics_ensemble_size": 1,
                     "empirical_or_earth_reconstruction": False},
        provenance_ids=(provenance_id,),
        payload_ref=f"payload://sha256/{PARENT_SHA}#physical_world_t0",
        model_derived=True,
        applicability={"scope": "synthetic ARCANA world at t0 only",
                       "forward_evolution": False,
                       "pygplates": "BOUNDED_SOLVER_CANDIDATE; not scientific authority"},
        refinement_lineage={"source_canonical_state_id": "r6state_d2e959c596bb1741d652c9d5f1d733b0d365cc9dbe362975048bc5ee3d3dca78",
                            "source_history_id": history_id,
                            "source_branch_id": branch_id},
    )
    state_id = store.append_state(state)
    role_rows = (
        AuthorityAnchor.create(history_id=history_id, branch_id=branch_id, time_key="210 Ma",
            domain_ids=("physical_world",), state_ids=(state_id,),
            authority_refs=("R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json",
                            "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json",
                            "R6_T0_INITIAL_KINEMATICS_MANIFEST.json"),
            provenance_refs=(provenance_id,), validation_status="VALIDATED",
            details={"rationale": "governed canonical ARCANA t0 authority; no forward state"}),
        HistoricalSnapshot.create(history_id=history_id, branch_id=branch_id, time_key="210 Ma",
            domain_ids=("physical_world",), state_ids=(state_id,),
            authority_refs=("R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json",),
            provenance_refs=(provenance_id,), validation_status="VALIDATED",
            details={"rationale": "exact immutable snapshot at the declared ARCANA t0"}),
        RefinementAnchor.create(history_id=history_id, branch_id=branch_id, time_key="210 Ma",
            domain_ids=("physical_world",), state_ids=(state_id,),
            authority_refs=("R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json",),
            provenance_refs=(provenance_id,), validation_status="VALIDATED",
            details={"rationale": "materialization manifest declares t0 refinement anchor",
                     "source_refinement_anchor_id": material["history_store"]["refinement_anchor_id"]}),
    )
    temporal_ids = [store.append_temporal(row) for row in role_rows]

    query = HistoryQueryService(store)
    result = query.state_at(history_id=history_id, branch_id=branch_id,
        domain="physical_world", time_key="210 Ma")
    global_matches = [row for row in query.history(history_id=history_id,
        branch_id=branch_id, domain="physical_world") if row.time_support.time_key == "210 Ma"]
    lineage = query.lineage(state_id)
    resolution = query.available_resolution(history_id=history_id, branch_id=branch_id,
        domain="physical_world", time_key="210 Ma")
    bound_descriptor = DomainRegistry(DOMAIN_REGISTRY).get("physical_world")
    bound_registry = DomainRegistry(DOMAIN_REGISTRY)
    census = _read(root, "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json")
    stepping = _read(root, "R6_FIRST_INTERVAL_NUMERICAL_STEPPING_CONTRACT.json")
    readiness = _read(root, "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19.json")
    inventory = vector["topology"]
    payload_verification = {
        "parent": {"sha256": PARENT_SHA, "bytes": 1169900, "verified_read_only": True},
        "vector_partition": {"sha256": VECTOR_SHA, "bytes": 5681184, "verified_read_only": True},
        "kinematics": {"sha256": kin_actual, "recomputed_from_canonical_json": True},
    }
    report = {
        "schema": "R6_PHYSICAL_DOMAIN_T0_BINDING_REPORT_V1",
        "decision": "R6_PHYSICAL_DOMAIN_T0_BOUND__FIRST_INTERVAL_BLOCKED",
        "authority_lineage": authority_lineage(root),
        "authority_validation": validations,
        "payload_verification": payload_verification,
        "canonical_topology": {"plate_count": inventory["plate_count"],
            "parent_face_count": inventory["face_count"],
            "boundary_segment_count": inventory["positive_length_boundary_edge_count"],
            "adjacent_plate_pair_count": inventory["positive_length_adjacency_pair_count"],
            "junction_count": junctions["junction_count"],
            "support": "COARSE_SUPPORT_ON_FINE_GRID"},
        "p01_p12": [{"id": p[0], "requirement": p[1], "status": p[2],
            "required_before_t0_binding": p[3], "required_before_first_finite_interval": p[4],
            "required_before_later_topology_event_only": p[5],
            "authority": p[6], "remaining_unknowns": p[7]} for p in P_REQUIREMENTS],
        "history_binding": {"t0_bound": True, "history_store_bound": True,
            "registry_bound": True, "history_id": history_id, "branch_id": branch_id,
            "state_id": state_id, "provenance_id": provenance_id,
            "temporal_roles": {"assigned": [row.ROLE for row in role_rows],
                "unassigned": {"SIMULATION_CHECKPOINT": "No restart semantics or restart state bundle declared.",
                               "CONSUMER_CHECKPOINT": "No declared consumer checkpoint exists."}},
            "temporal_record_ids": temporal_ids,
            "state_at_t0_query_status": result.status,
            "global_state_query_status": "FOUND" if len(global_matches) == 1 else "NOT_FOUND_OR_CONFLICT",
            "lineage_missing_parents": lineage["missing_parent_state_ids"],
            "available_resolution": resolution,
            "registry_entry": {"availability": bound_descriptor.history_availability.value,
                "binding_status": bound_descriptor.engine_binding_status.value,
                "authority_status": bound_descriptor.authority_status,
                "query_available": bound_descriptor.query_available,
                "satisfied_dependencies": list(bound_descriptor.satisfied_dependencies),
                "unknown_dependencies": list(bound_descriptor.unknown_dependencies),
                "forward_execution_authorized": bound_descriptor.forward_execution_authorized}},
        "pygplates": {"role": "BOUNDED_SOLVER_CANDIDATE", "scientific_authority": False,
            "static_geometry_topology": "SUFFICIENT", "synthetic_deforming_network": "SUFFICIENT",
            "canonical_dynamic_deformation": "NOT_YET_VALIDATED",
            "fair_p2_3_runtime_evidence": "EXTERNAL_QUALIFICATION_RECORDED_IN_ARCHITECTURE_FREEZE; supplied hashes/result identity not present in repository",
            "tracked_windows_report": "PYGPLATES_RUNTIME_UNAVAILABLE", "runtime_rerun_performed": False},
        "first_interval": {"t0_state_bound": True, "first_interval_executable": False,
            "authorized": False, "dt_first_years": stepping["dt_derivation"]["dt_first_years"],
            "conditional_rift_horizon_years": census["global_event_guard"]["earliest_model_activation_elapsed_years"],
            "conditional_horizon_is_legal_dt": False,
            "blockers": [
                {"class": "SCIENTIFIC_LAW", "artifact": "R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json",
                 "decision": "NO_PHYSICALLY_DEFENSIBLE_POSITIVE_ACCOMMODATION_FOUND",
                 "detail": "No governed law maps relative boundary displacement into shared interface/material geometry with junction-compatible state."},
                {"class": "TOPOLOGY_AND_NUMERICS", "artifact": "R6_FIRST_INTERVAL_NUMERICAL_STEPPING_CONTRACT.json",
                 "decision": stepping["decision"],
                 "detail": "No positive partition-preserving topology/contact transition horizon; dt_first_years remains null."},
                {"class": "CONTINUUM_DISCRETIZATION", "artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19.json",
                 "decision": readiness["decision"], "detail": readiness["remaining_blocker"]},
                {"class": "JUNCTION_COMPATIBILITY", "artifact": "R6_JUNCTION_COMPATIBILITY_CONTRACT.json",
                 "decision": "JUNCTION_COMPATIBILITY_MODEL_UNSUPPORTED",
                 "detail": "20 degree-3 junction velocities and residual allocation semantics remain unbound."},
            ],
            "next_scientific_blocker": "Define and govern a physically defensible positive shared-boundary accommodation/deformation law that is junction-compatible; separately, the current patch operator must be redefined from canonical branch cross-sections and pure-plate anchors before a positive topology-preserving horizon can be computed."},
        "scientific_execution": False,
        "canonical_payload_changed": False,
    }
    if not (result.status == "FOUND" and len(global_matches) == 1
            and not lineage["missing_parent_state_ids"] and resolution["status"] == "AVAILABLE"
            and bound_registry.get("physical_world").forward_execution_authorized is False):
        raise RuntimeError("T0 HistoryStore/query/registry binding validation failed")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# R6 Physical Domain T0 Authority Reconciliation and Binding", "",
        f"**Decision:** `{report['decision']}`", "",
        "T0 is bound as a historical state at 210 Ma. Forward evolution remains unauthorized.", "",
        "## Canonical T0 and validation", "",
        f"- Parent payload: `{PARENT_SHA}` (1,169,900 bytes; read-only hash verified)",
        f"- Vector partition: `{VECTOR_SHA}` (5,681,184 bytes; read-only hash verified)",
        f"- Kinematics: `{KINEMATICS_SHA}` (canonical JSON identity recomputed)",
        "- Inventory: 12 plates, 64,800 parent faces, 1,983 boundary segments, 30 pairs, 20 junctions.",
        "- Boundary support remains coarse support on the 1-degree parent grid.",
        "- Unknown bathymetry, deep, climate, hydrology, weak-zone state, boundary class, and junction semantics are preserved.", "",
        "## Authority lineage", "",
        "The old Simulation1 recovery binding and V1 event census/guard are historical. The materialized synthetic T0 is the current authority; the V3 census supersedes V1 for the precommitted minimal event guard. Diagnostic continuum and pyGPlates artifacts do not acquire scientific authority.", "",
        "| Artifact | Classification | Status | Commit |", "|---|---|---|---|"]
    for item in report["authority_lineage"]:
        lines.append(f"| `{item['artifact']}` | {item['classification']} | {item.get('status', 'missing')} | `{item.get('commit') or 'unavailable'}` |")
    lines += ["", "## P01–P12", "", "| ID | Requirement | Current status | Before T0 | Before first interval | Later topology event only |", "|---|---|---|---:|---:|---:|"]
    for row in report["p01_p12"]:
        lines.append(f"| {row['id']} | {row['requirement']} | `{row['status']}` | {row['required_before_t0_binding']} | {row['required_before_first_finite_interval']} | {row['required_before_later_topology_event_only']} |")
    binding = report["history_binding"]
    lines += ["", "## World History binding", "",
        f"- T0, HistoryStore, and physical-domain registry bound: **{binding['t0_bound']} / {binding['history_store_bound']} / {binding['registry_bound']}**.",
        f"- State ID: `{binding['state_id']}`; provenance ID: `{binding['provenance_id']}`.",
        f"- Temporal roles: {', '.join(binding['temporal_roles']['assigned'])}. Checkpoint roles are unassigned because no restart bundle or consumer exists.",
        f"- `STATE_AT(210 Ma, physical_world)`: global state `{binding['global_state_query_status']}`; lineage has {len(binding['lineage_missing_parents'])} missing parents.",
        f"- Available resolution: {binding['available_resolution']['native_resolutions']}; no interpolation or finer support inferred.",
        "- Scientific execution: false.", "",
        "## pyGPlates role", "",
        "`BOUNDED_SOLVER_CANDIDATE`; ARCANA remains the scientific authority. Static geometry/topology and synthetic deforming network are qualified as sufficient; canonical dynamic deformation is not yet validated. The tracked Windows runtime report remains `PYGPLATES_RUNTIME_UNAVAILABLE`; Fair evidence is external and its hashes/result identity are not bound in repository artifacts.", "",
        "## First interval readiness", "",
        "- T0 bound: **yes**.", "- First interval executable/authorized: **no / no**.",
        f"- `dt_first_years`: `{report['first_interval']['dt_first_years']}`; no dt, t1, or W_model selected.",
        f"- Conditional event horizon is not legal dt: **{not report['first_interval']['conditional_horizon_is_legal_dt']}**.",
        f"- Exact next scientific blocker: {report['first_interval']['next_scientific_blocker']}", "",
        "### Recorded blockers", ""]
    for block in report["first_interval"]["blockers"]:
        lines.append(f"- **{block['class']}** (`{block['artifact']}`): {block['detail']}")
    lines += ["", "No forward state was created and no canonical payload was modified.", ""]
    return "\n".join(lines)
