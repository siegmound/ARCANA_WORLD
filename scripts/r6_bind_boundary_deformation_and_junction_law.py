"""Adjudicate whether R6 has authority for a positive t0 boundary step.

This is a contract/census generator only. It never advances geometry or
materializes future deformation.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.repository_context import require_repository_context, repository_provenance, verify_protected_staged_blobs
HEAD = "592b1651b405363373590092e133bd25569d99a5"
VECTOR_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
KIN_SHA = "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4"
T0_SHA = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
INDEX_BLOBS = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}


def canonical(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def write_task_json(name: str, obj: dict) -> None:
    path = ROOT / name
    data = canonical(obj)
    if path.exists() and path.read_bytes() != data:
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            old = {}
        old_parent_vector = old.get("parent_vector_partition_sha256") or old.get("parents", {}).get("vector_partition_sha256")
        if old.get("artifact") != obj.get("artifact") or old_parent_vector != VECTOR_SHA:
            raise FileExistsError(f"refusing to overwrite artifact outside this authority lineage: {name}")
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


def write_task_md(name: str, data: str) -> None:
    path = ROOT / name
    encoded = data.encode("utf-8")
    if path.exists() and path.read_bytes() != encoded:
        if not path.read_text(encoding="utf-8").startswith(data.splitlines()[0] + "\n"):
            raise FileExistsError(f"refusing to overwrite Markdown outside this title lineage: {name}")
    if not path.exists() or path.read_bytes() != encoded:
        path.write_bytes(encoded)


def classify_finite_step(segment: dict) -> tuple[str, str]:
    """No segment can advance absent an adopted accommodation transition law."""
    vn = float(segment["relative_normal_velocity_m_per_year"])
    vt = float(segment["relative_tangential_velocity_m_per_year"])
    if vn > 0:
        reason = "DIVERGENT_RESIDUAL_HAS_NO_AUTHORIZED_GEOMETRIC_ZONE; RIFT_PROGRESS_IS_NOT_A_PARTITION_TRANSITION"
    elif vn < 0:
        reason = "CONVERGENT_SHORTENING_RESPONSE_UNBOUND; RIGID_CORE_OVERLAP_NOT_ALLOWED"
    else:
        reason = "NO_BOUNDARY_VELOCITY_OR_DEFORMATION_RULE"
    if abs(vt) > 1e-9:
        reason += "; TANGENTIAL_RELATIVE_DISPLACEMENT_HAS_NO_BOUND_INTERFACE_STATE"
    return "BLOCKED", reason


def verify_inputs() -> tuple[dict, dict, dict, dict]:
    require_repository_context(ROOT, required_ancestor=HEAD, expected_refs={"origin/main": HEAD})
    for ref in ("origin/main",):
        if subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip() != HEAD:
            raise RuntimeError(f"unexpected {ref}")
    verify_protected_staged_blobs(ROOT, INDEX_BLOBS)
    rule = read_json("R6_SHARED_BOUNDARY_MOTION_AND_TOPOLOGY_CONTACT_RULE.json")
    manifest = read_json("R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json")
    census = read_json("R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json")
    readiness = read_json("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V5.json")
    rift = read_json("R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json")
    partition = read_json("R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    kin = read_json("R6_T0_CANONICAL_PLATE_KINEMATICS.json")
    if partition["payload"]["sha256"] != VECTOR_SHA or partition["canonical_parent_sha256"] != T0_SHA:
        raise RuntimeError("partition identity mismatch")
    if kin["payload_identity_sha256"] != KIN_SHA or kin["parent_vector_partition_sha256"] != VECTOR_SHA:
        raise RuntimeError("kinematics identity mismatch")
    if manifest["parent_vector_partition_sha256"] != VECTOR_SHA or manifest["canonical_kinematics_sha256"] != KIN_SHA:
        raise RuntimeError("shared boundary manifest identity mismatch")
    if len(manifest["segments"]) != 1983 or len(manifest["junctions"]) != 20 or len(census["segments"]) != 1983:
        raise RuntimeError("unexpected boundary/junction census size")
    if rule["decision"] != "SHARED_BOUNDARY_NETWORK_BOUND_AS_MASTER_INTERFACE; TRANSITION_LAW_BLOCKED":
        raise RuntimeError("unexpected prior shared-boundary decision")
    if readiness["forward_evolution_executed"] or readiness["first_step"]["dt_first_years"] is not None:
        raise RuntimeError("unexpected previous evolution/readiness status")
    if rift["initial_state"]["progress_m"] != 0.0 or not rift["first_segment_policy"]["no_time_evolution_in_this_task"]:
        raise RuntimeError("unexpected rift authority")
    return rule, manifest, census, rift


def main() -> None:
    prior_rule, manifest, source_census, rift = verify_inputs()
    source_by_id = {x["boundary_id"]: x for x in source_census["segments"]}
    boundary_by_id = {x["boundary_id"]: x for x in manifest["segments"]}
    if len(source_by_id) != 1983 or set(source_by_id) != set(boundary_by_id):
        raise RuntimeError("boundary IDs are not a one-to-one match across source artifacts")

    segments = []
    status_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    for bid in sorted(source_by_id):
        source = source_by_id[bid]
        status, reason = classify_finite_step(source)
        if not (source["relative_normal_velocity_m_per_year"] or source["relative_tangential_velocity_m_per_year"]):
            status = "FINITE_STEP_SUPPORTED"  # no relative displacement to accommodate
            reason = "ZERO_RELATIVE_MOTION_AT_T0_DIAGNOSTIC_TOLERANCE"
        record = {
            "boundary_id": bid,
            "ordered_plate_pair": boundary_by_id[bid]["ordered_plate_pair"],
            "length_m": boundary_by_id[bid]["length_m"],
            "relative_normal_velocity_m_per_year": source["relative_normal_velocity_m_per_year"],
            "relative_tangential_velocity_m_per_year": source["relative_tangential_velocity_m_per_year"],
            "t0_kinematic_class": source["local_kinematic_diagnostic"],
            "finite_step_status": status,
            "blocking_reason": reason,
            "topology_changed": False,
        }
        segments.append(record)
        status_counts[status] += 1
        mode_counts[record["t0_kinematic_class"]] += 1

    junctions = []
    for item in manifest["junctions"]:
        incident = [boundary_by_id[x] for x in item["incident_boundary_ids"]]
        plates = sorted({p for edge in incident for p in edge["ordered_plate_pair"]})
        junctions.append({
            "junction_id": item["junction_id"], "vertex_id": item["vertex_id"],
            "degree": item["degree"], "incident_boundary_ids": item["incident_boundary_ids"],
            "incident_plate_ids": plates, "compatibility_status": "BLOCKED",
            "canonical_position": "T0_PARENT_GRID_VERTEX_ONLY",
            "canonical_velocity": None, "least_squares_solution": "NOT_RUN_NO_BOUNDARY_TYPES_OR_RESIDUAL_ALLOCATION_RULE",
            "residual_handling": "UNBOUND; no residual assigned to a boundary by averaging",
            "reason": "NO_GOVERNED_BOUNDARY_CLASS/VELOCITY_CONSTRAINTS; topology change and junction migration cannot be inferred from incidence alone",
        })
    junction_counts = Counter(x["compatibility_status"] for x in junctions)

    model_contract = {
        "artifact": "R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT",
        "schema": "R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT_V1",
        "decision": "NO_PHYSICALLY_DEFENSIBLE_POSITIVE_ACCOMMODATION_FOUND",
        "verdict": "PASS_MODEL_FAMILY_ADJUDICATION__BLOCKED_FINITE_TIME_BOUNDARY_RESPONSE",
        "scope": "R6 synthetic t0 boundary representation and proposed first substep only; no forward evolution",
        "repository_baseline": repository_provenance(ROOT),
        "parents": {"shared_boundary_rule": "R6_SHARED_BOUNDARY_MOTION_AND_TOPOLOGY_CONTACT_RULE.json",
                    "t0_boundary_manifest": "R6_T0_SHARED_BOUNDARY_STATE_MANIFEST.json",
                    "t0_kinematic_census": "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json",
                    "rift_law": "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json",
                    "vector_partition_sha256": VECTOR_SHA, "kinematics_sha256": KIN_SHA, "canonical_t0_sha256": T0_SHA},
        "model_families": [
            {"family": "A_ZERO_WIDTH_SHARED_CENTERLINE_PLUS_RESIDUAL", "disposition": "ALGEBRAIC_DIAGNOSTIC_ONLY_NOT_SELECTED_AS_PHYSICAL_TRANSITION",
             "candidate": "choose v_boundary by weighted fit to vA/vB; store rA=vA-v_boundary and rB=vB-v_boundary",
             "conservation_identity": "vB-vA = rB-rA; exact algebraically for any shared v_boundary",
             "why_insufficient": "A residual ledger alone has no finite spatial support, material mapping, or rule for how rigid-core geometry joins the shared interface. It can record unresolved displacement but cannot establish a physically valid partition transition or bounded capacity."},
            {"family": "B_FINITE_WIDTH_DEFORMING_BOUNDARY_ZONE", "disposition": "NOT_BOUND_PARAMETER_AND_PHYSICS_REQUIRED",
             "why": "Requires interface width/footprint, support, mapping from plate-normal/shear displacement to strain/material motion, and constitutive or explicitly authorial capacity/threshold semantics. No such t0 zone exists; 1-degree cell width cannot stand in for a physical width."},
            {"family": "C_TRIANGULATED_DEFORMING_NETWORK", "disposition": "GEOMETRY_BACKEND_CANDIDATE_NOT_BOUND_AS_ARCANA_LAW",
             "why": "GPlates-style networks represent finite regions with triangulation and track strain; they require network geometry and modeling choices. A mesh resolver does not supply ARCANA's causal rift/shortening/shear law or junction/event policy."},
            {"family": "D_ZERO_CAPACITY_FAIL_CLOSED", "disposition": "SELECTED_CURRENT_GOVERNED_POLICY",
             "meaning": "Any supported nonzero relative boundary motion blocks positive physical evolution until an explicit boundary response/interface law and compatible junction policy are bound."},
        ],
        "selected_semantics": {
            "rigid_plate_cores": "RETAINED_AS_T0_KINEMATIC_ABSTRACTION; no claim their entire future topological domains remain rigid",
            "shared_boundary_network": "MASTER_TOPOLOGICAL_INTERFACE; polygons/domains are derived from a resolved network",
            "boundary_width": "UNKNOWN; no physical or numerical width assigned",
            "centerline_velocity": "UNBOUND; no midpoint/half-stage, one-sided attachment, or least-squares motion selected",
            "opening": "Existing cumulative local normal opening / rift progress is the sole progress source; no second opening accumulator. It is not a geometry accommodation law and is not advanced.",
            "shortening": "NOT_MATERIALIZED; a signed/positive convergence displacement could be an internal neutral ledger in a future authorized checkpoint, but it is not subduction, thickening, orogeny, or a positive-capacity law.",
            "shear": "NOT_MATERIALIZED; a future signed tangential displacement ledger would be kinematic only, not fault slip; no junction/remesh response exists.",
            "finite_width_required_for_family_B": True,
            "universal_finite_width_requirement_claimed": False,
            "minimum_missing_authority": "A physically governed mapping from relative plate displacement to shared-interface/material geometry and junction-compatible state; a finite-width zone is one candidate and would need its own width/support authority.",
            "remeshing": "BLOCKED_NOT_REQUIRED_AT_T0; deterministic remesh policy must preserve identity/state and cannot create topology changes",
        },
        "operator_split": {"integrator_substate_possible_in_principle": True,
            "current_substate_authorized": False,
            "reason": "Current state lacks a selected boundary velocity, finite deformation map, capacity/handoff, and junction residual allocation; merely storing relative displacement would be an unresolved bookkeeping record, not an evolved partition-valid state.",
            "historical_snapshot_policy": "CHECKPOINT_ONLY until process response has consumed all unresolved accommodation and externally valid partition checks pass"},
        "capacity_and_event_handoff": {"divergent": "rift model event envelope remains conditional; no geometry response before initiation is bound",
            "convergent": "no transferable minimum shortening capacity/threshold for an untyped synthetic boundary; ZERO_CAPACITY_FAIL_CLOSED",
            "shear": "no fault/interface capacity or displacement tolerance; ZERO_CAPACITY_FAIL_CLOSED",
            "event_handoff": "stop at explicitly governed rift/contact/junction/topology event; no automatic continuation"},
        "prohibitions": {"forward_evolution": False, "future_geometry_created": False, "canonical_t0_changed": False,
            "canonical_kinematics_changed": False, "canonical_partition_changed": False, "opening_advanced": False,
            "shortening_advanced": False, "slip_advanced": False, "oceanic_crust_created": False},
        "literature_and_technical_sources": [
            {"citation": "Bird (2003), An updated digital model of plate boundaries", "doi": "10.1029/2001GC000252",
             "url": "https://doi.org/10.1029/2001GC000252", "type": "PRIMARY_BOUNDARY_MODEL",
             "relevance": "Boundary types use relative velocity together with geological evidence; several diffuse orogenic regions are expressly not expected to behave as rigid plates. Does not give a universal ARCANA shortening threshold."},
            {"citation": "Gordon (1998), The plate tectonic approximation: Plate nonrigidity, diffuse plate boundaries, and global plate reconstructions", "doi": "10.1146/annurev.earth.26.1.615",
             "url": "https://doi.org/10.1146/annurev.earth.26.1.615", "type": "MAJOR_REVIEW",
             "relevance": "Diffuse boundaries accommodate deformation across zones; their widths and rates vary, so no width or capacity transfers to untyped synthetic ARCANA boundaries."},
            {"citation": "Gurnis et al. (2018), Global tectonic reconstructions with continuously deforming and evolving rigid plates", "doi": "10.1016/j.cageo.2018.04.007",
             "url": "https://doi.org/10.1016/j.cageo.2018.04.007", "type": "PRIMARY_METHOD_PAPER",
             "relevance": "Deforming regions are continuously evolving polygons tessellated by triangular meshes, tracking strain rate/cumulative strain; finite deformation zone geometry and modeling inputs are required."},
            {"citation": "McKenzie & Morgan (1969), Evolution of triple junctions", "doi": "10.1038/224125a0",
             "url": "https://doi.org/10.1038/224125a0", "type": "PRIMARY_KINEMATIC_STUDY",
             "relevance": "Triple junctions can be stable or unstable depending on boundary configuration and plate motion; incidence alone does not define a common node velocity."},
            {"citation": "Cronin (1992), Types and kinematic stability of triple junctions", "doi": "10.1016/0040-1951(92)90391-I",
             "url": "https://doi.org/10.1016/0040-1951(92)90391-I", "type": "PRIMARY_KINEMATIC_STUDY",
             "relevance": "Stability depends on boundary types and evolving relative motions; instantaneous pairwise vectors alone do not establish stable junction evolution."},
            {"citation": "pyGPlates Primer, Topological networks and deformation", "url": "https://www.gplates.org/docs/pygplates/pygplates_primer",
             "type": "OFFICIAL_TECHNICAL_DOCUMENTATION", "relevance": "A network uses a boundary polygon, optional rigid blocks, deforming points and triangulation; it is a resolver/representation, not a physical law."},
        ],
    }

    junction_contract = {
        "artifact": "R6_JUNCTION_COMPATIBILITY_CONTRACT", "schema": "R6_JUNCTION_COMPATIBILITY_CONTRACT_V1",
        "decision": "JUNCTION_COMPATIBILITY_MODEL_UNSUPPORTED", "status": "BLOCKED_T0_INCIDENCE_ONLY",
        "parent_vector_partition_sha256": VECTOR_SHA, "canonical_kinematics_sha256": KIN_SHA,
        "junction_count": len(junctions), "junctions": junctions,
        "rule": "No arithmetic mean of incident plate velocities and no unconstrained least-squares node velocity are adopted. Kinematic stability requires boundary-type/orientation constraints; types are not authorized from relative motion alone.",
        "least_squares_candidate": {"objective": "NOT_BOUND", "weights": "NOT_BOUND", "hard_constraints": "NOT_BOUND",
            "residual_interpretation": "NOT_BOUND", "tolerance": "NOT_BOUND", "failure_state": "BLOCKED_NO_SOLUTION_PERSISTED"},
        "junction_guard": {"node_inversion": "UNBOUND", "edge_crossing": "UNBOUND", "boundary_collapse": "UNBOUND",
            "ordering_change": "EVENT_REQUIRES_AUTHORIZED_TOPOLOGY_RULE", "degree_change": "EVENT_REQUIRES_AUTHORIZED_TOPOLOGY_RULE"},
        "forward_evolution_executed": False,
    }
    census = {
        "artifact": "R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS", "schema": "R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS_V1",
        "time_ma": 210.0, "t0_diagnostic_only": True, "parent_vector_partition_sha256": VECTOR_SHA,
        "canonical_kinematics_sha256": KIN_SHA, "parent_census": "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json",
        "finite_step_status_counts": dict(sorted(status_counts.items())), "t0_kinematic_class_counts": dict(sorted(mode_counts.items())),
        "segment_count": len(segments), "segments": segments, "junction_status_counts": dict(sorted(junction_counts.items())),
        "junction_count": len(junctions), "junctions": junctions,
        "opening_progress_source_of_truth": "EXISTING_RIFT_PROGRESS_ONLY_NOT_ADVANCED",
        "shortening_state": "NOT_MATERIALIZED", "tangential_slip_state": "NOT_MATERIALIZED",
        "interpretation": "Every segment requires nonzero relative motion accommodation; all are blocked under the selected zero-capacity fail-closed policy. Statuses do not assign geological boundary type.",
        "future_state_created": False,
    }
    guard = {
        "artifact": "R6_BOUNDARY_AND_JUNCTION_GUARD", "schema": "R6_BOUNDARY_AND_JUNCTION_GUARD_V1",
        "decision": "NO_PHYSICALLY_DEFENSIBLE_POSITIVE_ACCOMMODATION_FOUND",
        "boundary_guard_horizon_years": None, "junction_guard_horizon_years": None, "combined_guard_horizon_years": None,
        "first_positive_dt_authorized": False, "rift_event_guard_years": 27123.405156307464,
        "rift_event_guard_is_legal_dt": False, "segments_blocked": sum(status_counts.values()), "junctions_blocked": len(junctions),
        "blocking_families": ["FINITE_TIME_OPENING_GEOMETRY", "CONVERGENT_SHORTENING_RESPONSE", "TANGENTIAL_SHEAR_ACCOMMODATION", "MULTIPLATE_JUNCTION_COMPATIBILITY"],
        "numerical_step_register": "R6_FIRST_INTERVAL_DT_LIMIT_REGISTER.json; unchanged; topology/contact remains its active blocker",
        "no_predictive_geometry_computed": True, "forward_evolution_executed": False,
    }
    readiness = {
        "artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V6", "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V6",
        "repository": repository_provenance(ROOT),
        "decision": "CONVERGENT_SHORTENING_MODEL_UNSUPPORTED",
        "verdict": "PASS_BOUNDARY/JUNCTION_FAIL_CLOSED_ADJUDICATION__FIRST_INTERVAL_BLOCKED",
        "t0_ma": 210.0, "positive_interval": False, "dt_first_years": None,
        "segments": {"total": len(segments), "finite_step_supported": status_counts["FINITE_STEP_SUPPORTED"],
                     "supported_with_accommodation": status_counts["FINITE_STEP_SUPPORTED_WITH_ACCOMMODATION"],
                     "event_guarded": status_counts["EVENT_GUARDED"], "blocked": status_counts["BLOCKED"]},
        "junctions": {"total": len(junctions), "compatible": junction_counts["COMPATIBLE"],
                       "guarded": junction_counts["GUARDED"], "blocked": junction_counts["BLOCKED"]},
        "master_topology": "SHARED_BOUNDARY_NETWORK; t0 only; post-t0 transition not bound",
        "canonical_t0_changed": False, "canonical_kinematics_changed": False, "canonical_partition_changed": False,
        "forward_evolution_executed": False, "execution_contract_created": False,
        "historical_snapshot_with_unresolved_accommodation": "CHECKPOINT_ONLY",
        "remaining_blocker": "NO_AUTHORIZED_CONVERGENT_SHORTENING/INTERFACE_RESPONSE; current zero-capacity policy blocks all nonzero-motion boundaries; junction compatibility also remains blocked",
        "next_action": "R6_MINIMAL_CONVERGENT_SHORTENING_RESPONSE_LAW_BINDING",
    }

    write_task_json("R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.json", model_contract)
    write_task_md("R6_SHARED_BOUNDARY_DEFORMATION_LAW_CONTRACT.md", model_markdown(model_contract))
    write_task_json("R6_JUNCTION_COMPATIBILITY_CONTRACT.json", junction_contract)
    write_task_md("R6_JUNCTION_COMPATIBILITY_CONTRACT.md", junction_markdown(junction_contract))
    write_task_json("R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.json", census)
    write_task_md("R6_SHARED_BOUNDARY_FINITE_STEP_CENSUS.md", census_markdown(census))
    write_task_json("R6_BOUNDARY_AND_JUNCTION_GUARD.json", guard)
    write_task_md("R6_BOUNDARY_AND_JUNCTION_GUARD.md", guard_markdown(guard))
    write_task_json("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V6.json", readiness)
    write_task_md("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V6.md", readiness_markdown(readiness))
    print(json.dumps({"decision": readiness["decision"], "segments": status_counts, "junctions": junction_counts,
                      "dt_first_years": None, "execution_contract_created": False}, sort_keys=True))


def model_markdown(x: dict) -> str:
    return """# R6 shared-boundary deformation law contract

## Decision

**NO_PHYSICALLY_DEFENSIBLE_POSITIVE_ACCOMMODATION_FOUND.** Keep the shared network as the master interface representation, but do not authorize a finite-time transition. Current policy is zero-capacity/fail-closed.

## Candidate adjudication

| Family | Disposition | Reason |
|---|---|---|
| Zero-width centerline + residual | Algebraic diagnostic only | It can conserve relative velocity algebraically, but residual bookkeeping has no spatial support or physical map to keep rigid-core boundaries compatible. |
| Finite-width deforming zone | Not bound | Requires physical footprint/width, support, deformation mapping, and capacity/constitutive semantics absent from t0. The 1° cell is not a physical width. |
| Triangulated deforming network | Backend candidate only | GPlates-style networks resolve finite deforming regions and strain; the software does not provide ARCANA's causal law or event semantics. |
| Zero-capacity fail-closed | Selected current policy | Any nonzero unsupported relative motion blocks advancement. |

## State semantics

- Shared boundary network: one interface identity, never duplicated by side.
- Rigid cores remain a t0 kinematic abstraction; future topological domains may include deforming margins and must not be called rigid polygons.
- Existing cumulative local normal opening/rift progress is the sole opening-progress source. It is not advanced and does not itself define boundary geometry.
- Shortening and tangential slip are not materialized. If future operators use ledgers, they mean unresolved relative displacement only—not subduction, thickening, fault slip, or uplift.
- A future unresolved state may be restartable as an integrator checkpoint only; not a World History snapshot until physical response is consumed and partition checks pass.

The symmetric residual identity `vB-vA = (vB-v_boundary) - (vA-v_boundary)` is exact for any selected `v_boundary`; it does not select a physical boundary velocity. Midpoint/half-stage, one-sided attachment, or least-squares fitting is therefore not adopted.

## Why the step remains blocked

All 1,983 current segments have nonzero relative motion. Opening has no geometric zone, convergence lacks a shortening/contact response and transferable minimum capacity, shear lacks an interface state/remesh law, and all 20 multi-plate junctions lack typed kinematic constraints and residual allocation. No finite guard horizon or legal `dt` follows. The existing 27,123.405-year rift horizon remains conditional and is not a timestep.

## Research basis

Bird's PB2002 associates boundary types with geological evidence as well as relative velocity and explicitly excludes diffuse orogenic zones from rigid-plate accuracy. Gordon reviews diffuse boundaries as finite zones of distributed deformation. Gurnis et al. describe continuously deforming regions as polygons tessellated by meshes with strain tracked. McKenzie & Morgan and Cronin show junction stability depends on boundary configuration and plate motions. None supplies a universal shortening capacity for these untyped synthetic ARCANA boundaries.

Sources: [Bird 2003](https://doi.org/10.1029/2001GC000252); [Gordon 1998](https://doi.org/10.1146/annurev.earth.26.1.615); [Gurnis et al. 2018](https://doi.org/10.1016/j.cageo.2018.04.007); [McKenzie & Morgan 1969](https://doi.org/10.1038/224125a0); [Cronin 1992](https://doi.org/10.1016/0040-1951(92)90391-I); [pyGPlates primer](https://www.gplates.org/docs/pygplates/pygplates_primer).
"""


def junction_markdown(x: dict) -> str:
    return ("# R6 junction compatibility contract\n\n"
            "**JUNCTION_COMPATIBILITY_MODEL_UNSUPPORTED.** All 20 degree-3-or-higher t0 junctions remain `BLOCKED`. No node velocity is averaged or fit: plate-boundary types and the associated geometric/kinematic constraints are not authorized, and an unconstrained least-squares residual has no approved allocation to incident interfaces.\n\n"
            "Junction degree/order changes are physical topology events and require an explicit event rule; numerical crossing, inversion, or collapse is a rejection, not an automatic repair.\n")


def census_markdown(x: dict) -> str:
    return ("# R6 shared-boundary finite-step census\n\n"
            "t0-only evaluation at synthetic 210 Ma; no proposed transition or geometry update was run.\n\n"
            f"- Segments: {x['segment_count']}\n- Status counts: `{json.dumps(x['finite_step_status_counts'], sort_keys=True)}`\n"
            f"- t0 component classes: `{json.dumps(x['t0_kinematic_class_counts'], sort_keys=True)}`\n"
            f"- Junctions: {x['junction_count']}\n- Junction status counts: `{json.dumps(x['junction_status_counts'], sort_keys=True)}`\n\n"
            "Every segment status is individually recorded in the JSON by its stable boundary ID and blocking reason. The existing rift-progress value is the only opening source of truth and is not advanced. No shortening or slip state is created.\n")


def guard_markdown(x: dict) -> str:
    return ("# R6 boundary and junction guard\n\n"
            "No positive boundary, junction, or combined guard horizon is bound. All current segments and junctions are blocked under the selected zero-capacity policy. The 27,123.405-year conditional rift-event horizon is not a legal dt. No t0 predictive geometry, future state, or interval execution contract was created.\n")


def readiness_markdown(x: dict) -> str:
    return ("# R6 first physical interval readiness V6\n\n"
            f"Decision: **{x['decision']}**\n\n{ x['verdict'] }.\n\n"
            f"Blocked segments: {x['segments']['blocked']}/{x['segments']['total']}; blocked junctions: {x['junctions']['blocked']}/{x['junctions']['total']}. `dt_first_years = null`. Forward evolution and execution-contract creation are false.\n\n"
            f"Next action: `{x['next_action']}`.\n")


if __name__ == "__main__":
    main()
