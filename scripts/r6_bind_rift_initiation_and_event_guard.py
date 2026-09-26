#!/usr/bin/env python3
"""Evaluate the precommitted R6 t0 rift guard; never advances physical state."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.r6.repository_context import (require_repository_context,
    repository_provenance, resolve_external_payload_path, verify_protected_staged_blobs)
EXPECTED_HEAD = "592b1651b405363373590092e133bd25569d99a5"
EXPECTED_T0 = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
EXPECTED_VECTOR = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
EXPECTED_KIN = "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4"
RADIUS_M = 6_371_000.0
SECONDS_PER_YEAR = 365.25 * 24 * 60 * 60


def read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(name: str, obj: dict) -> None:
    (ROOT / name).write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_md(name: str, content: str) -> None:
    (ROOT / name).write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    import subprocess

    require_repository_context(ROOT, required_ancestor=HEAD, expected_refs={"origin/main": HEAD})
    if subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip() != EXPECTED_HEAD:
        raise RuntimeError("origin/main differs from governed baseline")
    verify_protected_staged_blobs(ROOT, {
        "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
        "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
    })

    law = read_json("R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json")
    kin = read_json("R6_T0_CANONICAL_PLATE_KINEMATICS.json")
    kman = read_json("R6_T0_INITIAL_KINEMATICS_MANIFEST.json")
    partition = read_json("R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    prior = read_json("R6_T0_INITIAL_MOTION_GENERATIVE_PRIOR_CONTRACT.json")
    canonical = read_json("R6_CANONICAL_INITIAL_STATE_PACKAGE.json")
    if law["status"] != "PRECOMMITTED_BEFORE_T0_CENSUS_V3":
        raise RuntimeError("law was not precommitted")
    if law["threshold_authority"]["lower_guard_bound_m"] != 5000.0 or law["threshold_authority"]["upper_bound_m"] != 30000.0:
        raise RuntimeError("unexpected threshold contract")
    if law["initial_state"]["state"] != "RIFT_QUIESCENT_AT_EXACT_T0" or law["initial_state"]["progress_m"] != 0.0:
        raise RuntimeError("initial rift state mismatch")
    if kin["payload_identity_sha256"] != EXPECTED_KIN or kman["kinematics_sha256"] != EXPECTED_KIN:
        raise RuntimeError("kinematics identity mismatch")
    if partition["payload"]["sha256"] != EXPECTED_VECTOR or partition["canonical_parent_sha256"] != EXPECTED_T0:
        raise RuntimeError("vector partition identity mismatch")
    if canonical["materialized_payload"]["sha256"] != EXPECTED_T0:
        raise RuntimeError("canonical t0 identity mismatch")
    if prior["authority_class"] != "STOCHASTIC_CANONICAL_MODEL_REALIZATION":
        raise RuntimeError("prior authority mismatch")
    vector_path = resolve_external_payload_path(ROOT, partition["payload"]["path"])
    if not vector_path.is_file() or vector_path.stat().st_size != partition["payload"]["bytes"] or sha256(vector_path) != EXPECTED_VECTOR:
        raise RuntimeError("external vector payload missing or changed")

    plates = {int(x["plate_id"]): np.asarray(x["euler_vector_rad_per_year"], dtype=np.float64) for x in kin["plates"]}
    if sorted(plates) != list(range(12)) or any(not np.isfinite(v).all() for v in plates.values()):
        raise RuntimeError("invalid canonical plate Euler state")
    nr, nc = map(int, partition["parent_grid"]["shape"])
    groups = {(int(x["plate_a"]), int(x["plate_b"])): x for x in partition["adjacency_groups"]}
    edge_acc: dict[tuple[int, int], list[tuple[float, float, float]]] = {key: [] for key in groups}
    with np.load(vector_path, allow_pickle=False) as z:
        rows = z["face_row"].astype(np.int64)
        cols = z["face_col"].astype(np.int64)
        face_pid = z["face_plate_id"].astype(np.int64)
        erow = z["boundary_edge_row"].astype(np.int64)
        ecol = z["boundary_edge_col"].astype(np.int64)
        axis = z["boundary_edge_axis"].astype(np.int64)
        pa = z["boundary_plate_a"].astype(np.int64)
        pb = z["boundary_plate_b"].astype(np.int64)
        lengths = z["boundary_length_m"].astype(np.float64)
    if len(erow) != 1983 or len(groups) != 30 or not (len(erow) == len(ecol) == len(axis) == len(pa) == len(pb) == len(lengths)):
        raise RuntimeError("boundary topology cardinality mismatch")
    lookup = np.full((nr, nc), -1, dtype=np.int16)
    lookup[rows, cols] = face_pid.astype(np.int16)
    if np.any(lookup < 0):
        raise RuntimeError("face-to-grid mapping incomplete")

    for row, col, ax, a, b, length in zip(erow, ecol, axis, pa, pb, lengths):
        pair = (int(a), int(b))
        if pair not in edge_acc or not math.isfinite(float(length)) or length <= 0:
            raise RuntimeError("invalid or unregistered boundary edge")
        lat = math.radians(-90.0 + row + (0.5 if ax == 0 else 1.0))
        lon = math.radians(-180.0 + col + (1.0 if ax == 0 else 0.5))
        r = np.array([math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)])
        if ax == 0:
            normal = np.array([-math.sin(lon), math.cos(lon), 0.0])
        elif ax == 1:
            normal = np.array([-math.sin(lat) * math.cos(lon), -math.sin(lat) * math.sin(lon), math.cos(lat)])
        else:
            raise RuntimeError("unrecognized boundary edge axis")
        side_pid = int(lookup[row, col])
        if side_pid not in pair:
            raise RuntimeError("edge's reference-side face does not match pair")
        if side_pid != int(a):
            normal = -normal
        relative_m_y = np.cross(plates[int(b)] - plates[int(a)], r) * RADIUS_M
        normal_m_y = float(np.dot(relative_m_y, normal))
        tangent_m_y = math.sqrt(max(0.0, float(np.dot(relative_m_y, relative_m_y)) - normal_m_y**2))
        edge_acc[pair].append((normal_m_y, tangent_m_y, float(length)))

    theta_min = float(law["threshold_authority"]["lower_guard_bound_m"])
    theta_max = float(law["threshold_authority"]["upper_bound_m"])
    candidates = []
    for pair, group in sorted(groups.items()):
        edge_values = edge_acc[pair]
        if len(edge_values) != int(group["edge_count"]):
            raise RuntimeError(f"edge count mismatch for {pair}")
        total_len = sum(x[2] for x in edge_values)
        if not math.isclose(total_len, float(group["length_m"]), rel_tol=0, abs_tol=0.003):
            raise RuntimeError(f"edge length mismatch for {pair}")
        signed_mean = sum(x[0] * x[2] for x in edge_values) / total_len
        tangential_mean = sum(x[1] * x[2] for x in edge_values) / total_len
        rel_speed_mean = sum(math.hypot(x[0], x[1]) * x[2] for x in edge_values) / total_len
        max_local_open = max(0.0, max(x[0] for x in edge_values))
        positive_edges = sum(1 for x in edge_values if x[0] > 0)
        if signed_mean > 0:
            normal_direction = "DIVERGENT_PAIR_MEAN"
        elif signed_mean < 0:
            normal_direction = "CONVERGENT_PAIR_MEAN"
        else:
            normal_direction = "ZERO_NORMAL_PAIR_MEAN"
        motion_mode = "TRANSFORM_DOMINATED" if tangential_mean >= abs(signed_mean) else normal_direction
        if positive_edges:
            eligibility = "ELIGIBLE_QUIESCENT"
            time_years = theta_min / max_local_open
            threshold_max_years = theta_max / max_local_open
            guard_status = "POSITIVE_MODEL_EVENT_HORIZON_BOUND"
        else:
            eligibility = "INELIGIBLE"
            time_years = None
            threshold_max_years = None
            guard_status = "NO_OPENING_DRIVER_IN_FIXED_T0_SEGMENT"
        candidates.append({
            "pair_id": f"{pair[0]}:{pair[1]}", "plate_a": pair[0], "plate_b": pair[1],
            "boundary_edge_count": len(edge_values), "boundary_length_m": total_len,
            "pair_mean_signed_normal_velocity_m_per_year": signed_mean,
            "pair_mean_opening_velocity_m_per_year": max(0.0, signed_mean),
            "pair_mean_convergence_velocity_m_per_year": max(0.0, -signed_mean),
            "pair_mean_tangential_velocity_m_per_year": tangential_mean,
            "pair_mean_relative_speed_m_per_year": rel_speed_mean,
            "positive_opening_edge_count": positive_edges,
            "maximum_local_opening_velocity_m_per_year": max_local_open,
            "rift_progress_initial_m": 0.0,
            "initial_process_state": "RIFT_QUIESCENT_AT_EXACT_T0",
            "weak_zone_susceptibility": "UNKNOWN",
            "weakness_required_by_this_guard_law": False,
            "eligibility": eligibility,
            "progress_rate_upper_bound_m_per_year": max_local_open,
            "earliest_modeled_initiation_elapsed_years": time_years,
            "upper_threshold_activation_elapsed_years": threshold_max_years,
            "event_guard_status": guard_status,
            "uncertainty": "MODEL_UNCERTAINTY; threshold interval is authorial model envelope; local boundary support follows the coarse parent grid",
            "authority": "R6_T0_CANONICAL_PLATE_KINEMATICS.json + R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json + precommitted R6 rift law",
            "normal_direction_diagnostic": normal_direction,
            "kinematic_mode_diagnostic": motion_mode,
        })
    if len(candidates) != 30:
        raise RuntimeError("expected exactly 30 adjacent plate pairs")
    max_open = max(float(x["maximum_local_opening_velocity_m_per_year"]) for x in candidates)
    if max_open <= 0:
        global_years = None
        global_pair = None
        global_guard = "NO_POSITIVE_OPENING_DRIVER_AT_T0"
    else:
        global_years = theta_min / max_open
        global_pair = max(candidates, key=lambda x: x["maximum_local_opening_velocity_m_per_year"])["pair_id"]
        global_guard = "BOUND_BY_PRECOMMITTED_AUTHORIAL_MODEL_THRESHOLD_ENVELOPE"
    counts = {state: sum(1 for x in candidates if x["eligibility"] == state) for state in ("INELIGIBLE", "ELIGIBLE_QUIESCENT", "ACTIVE", "UNKNOWN")}
    all_edge_normals = [v[0] for edge_list in edge_acc.values() for v in edge_list]
    rates_cm = [x * 100 for x in all_edge_normals]
    diagnostics = {
        "adjacent_pair_count": len(candidates), "boundary_edge_count": len(all_edge_normals),
        "divergent_pair_mean_count": sum(x["normal_direction_diagnostic"] == "DIVERGENT_PAIR_MEAN" for x in candidates),
        "convergent_pair_mean_count": sum(x["normal_direction_diagnostic"] == "CONVERGENT_PAIR_MEAN" for x in candidates),
        "transform_dominated_pair_count": sum(x["kinematic_mode_diagnostic"] == "TRANSFORM_DOMINATED" for x in candidates),
        "zero_normal_pair_mean_count": sum(x["normal_direction_diagnostic"] == "ZERO_NORMAL_PAIR_MEAN" for x in candidates),
        "zero_local_normal_driver_edge_count": sum(x == 0 for x in all_edge_normals),
        "mixed_sign_boundary_pairs": sum(x["positive_opening_edge_count"] > 0 and x["pair_mean_signed_normal_velocity_m_per_year"] <= 0 for x in candidates),
        "positive_opening_edge_count": sum(x > 0 for x in all_edge_normals),
        "zero_or_negative_edge_opening_count": sum(x <= 0 for x in all_edge_normals),
        "maximum_local_opening_cm_per_year": max(rates_cm, default=0.0),
        "minimum_local_signed_normal_cm_per_year": min(rates_cm, default=0.0),
        "maximum_relative_boundary_speed_cm_per_year": max(math.hypot(n, t) * 100 for edges in edge_acc.values() for n, t, _ in edges),
    }
    census = {
        "artifact": "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3", "schema": "R6_T0_EVENT_ELIGIBILITY_CENSUS_V3",
        "time_ma": 210.0, "canonical_kinematics_sha256": EXPECTED_KIN, "vector_partition_sha256": EXPECTED_VECTOR,
        "rift_law": "R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json", "census_is_t0_evaluation_only": True,
        "time_evolution_executed": False, "event_created": False, "plate_split": False,
        "initial_rift_state": "RIFT_QUIESCENT_AT_EXACT_T0", "initial_progress_m": 0.0,
        "weak_zone_state": "UNKNOWN", "weakness_required_by_minimal_guard": False,
        "eligibility_semantics": {"INELIGIBLE": "no positive local normal-opening driver on any supported boundary edge under the fixed t0 Euler segment", "ELIGIBLE_QUIESCENT": "positive opening can accumulate the precommitted model progress while the state remains below activation threshold", "ACTIVE": "threshold reached; prohibited at exact t0 by initial state and not assigned here", "UNKNOWN": "required kinematic/topological support missing or invalid; not converted to zero"},
        "counts": counts, "diagnostics": diagnostics, "candidates": candidates,
        "global_event_guard": {"status": "CONDITIONAL_BOUND_WITHIN_FIXED_T0_EULER_SEGMENT" if global_years is not None else global_guard, "limiting_pair_id": global_pair,
            "earliest_model_activation_elapsed_years": global_years,
            "earliest_model_activation_elapsed_Ma": global_years / 1e6 if global_years is not None else None,
            "earliest_model_activation_age_Ma": 210.0 - global_years / 1e6 if global_years is not None else None,
            "threshold_lower_bound_m": theta_min, "not_a_natural_minimum": True,
            "validity_scope": "conditional on holding the canonical t0 Euler rates fixed; only applies within a first numerical step whose duration is separately bounded",
            "post_segment_guard_bound": False},
        "conservation_or_mutation": {"canonical_t0_changed": False, "kinematics_changed": False, "vector_topology_changed": False, "forward_evolution": False},
    }
    write_json("R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json", census)
    md = ["# R6 t0 event eligibility census V3", "", "Evaluation only at synthetic 210 Ma t0; no state was advanced and no event was emitted.", "",
          f"Counts: `{json.dumps(counts, sort_keys=True)}`.", "",
          f"Fastest local opening is {diagnostics['maximum_local_opening_cm_per_year']:.6g} cm/year; the minimum modeled activation envelope gives {global_years / 1e6:.6g} Ma elapsed." if global_years is not None else "No positive opening driver; no finite model event horizon.",
          "This is an ARCANA model-bound event guard, not a natural lower bound on rift initiation. Its horizon is conditional on the canonical t0 Euler rates remaining fixed during one first step; it does not bound later motion renewal. Weakness remains UNKNOWN and is not assigned.", "",
          "| Pair | Mean normal (m/y) | Max local opening (m/y) | Progress rate bound (m/y) | Eligibility | Earliest modeled event (years) | Guard |",
          "|---|---:|---:|---:|---|---:|---|"]
    for x in candidates:
        md.append(f"| {x['pair_id']} | {x['pair_mean_signed_normal_velocity_m_per_year']:.8g} | {x['maximum_local_opening_velocity_m_per_year']:.8g} | {x['progress_rate_upper_bound_m_per_year']:.8g} | {x['eligibility']} | {x['earliest_modeled_initiation_elapsed_years'] if x['earliest_modeled_initiation_elapsed_years'] is not None else '—'} | {x['event_guard_status']} |")
    write_md("R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.md", "\n".join(md))

    evidence = {
        "artifact": "R6_RIFT_INITIATION_PARAMETER_EVIDENCE_MATRIX", "schema": "R6_RIFT_INITIATION_PARAMETER_EVIDENCE_MATRIX_V1",
        "decision_basis": "Targeted primary/review literature supports dependence on rheology, strength, thermal state, rate and inheritance, but does not supply a universal transferable onset threshold. The operational envelope below is explicitly authorial ARCANA model authority, not an empirical threshold.",
        "parameters": [
            {"id": "RIFT_PROGRESS", "quantity": "cumulative local boundary-normal opening displacement E", "units": "m", "authority": "ARCANA model definition", "evidence": "direct integral of existing relative kinematics; avoids unbound deformation-zone width", "status": "BOUND_FOR_EVENT_GUARD_ONLY"},
            {"id": "INITIAL_PROGRESS", "quantity": "E at exact synthetic t0", "value": 0.0, "units": "m", "authority": "AUTHORIAL_MODEL_INITIAL_CONDITION", "status": "BOUND", "not_earth_observation": True},
            {"id": "OPENING_DRIVER", "quantity": "max(0, (vB-vA) dot nAB)", "units": "m/year", "authority": "derived from bound Euler kinematics and vector boundary support", "status": "COMPUTED_AT_T0"},
            {"id": "ACTIVATION_THRESHOLD", "quantity": "operational RIFT_INITIATION threshold theta", "lower_m": theta_min, "upper_m": theta_max, "distribution": None, "authority": "BOUNDED_AUTHORIAL_MODEL_ASSUMPTION_CONSTRAINED_BY_LITERATURE_CONTEXT", "status": "BOUND_AS_MODEL_ENVELOPE_NOT_NATURAL_CONSTANT", "transfer_limit": "No claim that natural rifts require at least this extension; no observation uniquely calibrates ARCANA's synthetic state."},
            {"id": "WEAK_ZONE_SUSCEPTIBILITY", "quantity": "mechanical weakness", "value": "UNKNOWN", "numeric_value_assigned": False, "required_by_minimal_guard": False, "status": "UNKNOWN_PRESERVED"},
            {"id": "HEALING_OR_RESET", "quantity": "progress relaxation under non-opening motion", "value": "NONE_AUTHORIZED; progress stalls", "status": "DEFERRED_NOT_INVENTED"},
            {"id": "NUMERICAL_LOCALIZATION_TOLERANCE", "quantity": "solver event localization tolerance", "value": None, "status": "UNBOUND"},
        ],
        "literature": [
            {"citation": "Buck (1991), Modes of continental lithospheric extension", "doi": "10.1029/91JB01485", "url": "https://doi.org/10.1029/91JB01485", "evidence": "extension style depends on crustal thickness, heat flow, strain rate and rheology; hence strain/beta cannot be parameterized here without missing fields", "kind": "PRIMARY_MODEL"},
            {"citation": "Brune et al. (2023), Geodynamics of continental rift initiation and evolution", "doi": "10.1038/s43017-023-00391-3", "url": "https://doi.org/10.1038/s43017-023-00391-3", "evidence": "review describes transient competing driving, resisting, weakening and inherited structural processes; not one universal onset threshold", "kind": "MAJOR_REVIEW"},
            {"citation": "Boone et al. (2018), East African Rift / Lokichar Basin extension study", "doi": "10.1002/2017TC004575", "url": "https://doi.org/10.1002/2017TC004575", "evidence": "regional extension magnitude is context only, not a transferable onset threshold", "kind": "PRIMARY_REGIONAL_STUDY"},
            {"citation": "Korchinski et al. (2021), extension rate and lithospheric rheology in rift evolution", "doi": "10.1016/j.marpetgeo.2020.104715", "url": "https://doi.org/10.1016/j.marpetgeo.2020.104715", "evidence": "setting-specific numerical study; rate/rheology affect rift behavior and localization, not a universal delay", "kind": "PRIMARY_MODEL"},
        ],
    }
    write_json("R6_RIFT_INITIATION_PARAMETER_EVIDENCE_MATRIX.json", evidence)
    write_md("R6_RIFT_INITIATION_PARAMETER_EVIDENCE_MATRIX.md", "# R6 rift-initiation parameter evidence matrix\n\nThe literature supports process dependence and substantial non-uniqueness; it does **not** establish a universal onset threshold. ARCANA therefore uses the explicitly authorial 5–30 km operational activation envelope solely to define its own first-event guard. It is not presented as a natural minimum or empirically calibrated value. Weakness remains UNKNOWN.\n\n| Quantity | Bound / disposition | Status |\n|---|---|---|\n| Rift progress | Cumulative local normal opening, metres | Bound for guard |\n| Initial progress | 0 m, synthetic authorial t0 condition | Bound |\n| Activation envelope | 5–30 km, no distribution | Authorial model assumption |\n| Weak-zone strength | UNKNOWN; no numeric value | Preserved |\n| Healing/reset | None; stalls when opening <= 0 | No unsupported rule |\n| Numerical event tolerance | Unbound | Blocks dt/execution contract |\n\nSources: [Buck 1991](https://doi.org/10.1029/91JB01485); [Brune et al. 2023](https://doi.org/10.1038/s43017-023-00391-3); [Boone et al. 2018](https://doi.org/10.1002/2017TC004575); [Korchinski et al. 2021](https://doi.org/10.1016/j.marpetgeo.2020.104715). These studies inform process structure and transfer limitations, not ARCANA parameter values.")

    readiness = {
        "artifact": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V3", "schema": "R6_FIRST_PHYSICAL_INTERVAL_READINESS_V3",
        "decision": "FIRST_PHYSICAL_INTERVAL_EVENT_GUARD_BOUND__NUMERICAL_STEP_POLICY_UNBOUND",
        "verdict": "PASS_R6_RIFT_EVENT_GUARD_BOUND__NUMERICAL_STEP_POLICY_REMAINS_UNBOUND",
        "t0_ma": 210.0, "kinematics_bound": True, "event_guard_status": global_guard,
        "strictly_positive_model_event_time_lower_bound_years_with_fixed_t0_euler": global_years,
        "strictly_positive_model_event_time_lower_bound_Ma": global_years / 1e6 if global_years is not None else None,
        "limiting_pair_id": global_pair, "P02_motion_segment": "BOUND_CONDITIONALLY_TO_FIRST_SEGMENT_ONLY", "P03_motion_renewal": "NOT_EXERCISED_WITHIN_FIRST_SEGMENT; LONGER_TERM_LAW_UNBOUND",
        "P05_weak_zone": "UNKNOWN_PRESERVED; NOT_REQUIRED_BY_MINIMAL_GUARD_LAW", "P07_eligibility": "COMPUTED_AT_T0_UNDER_EXPLICIT_MINIMAL_LAW",
        "P08_rift_initiation": "BOUND_EVENT_GUARD_ONLY; NO_EVENT_EXECUTED", "P09_split_lineage": "DEFERRED_UNTIL_RIFT_INITIATION",
        "P10_census": "EXECUTED_AT_T0; 30 PAIRS", "P11_numerical_step_acceptance": "UNBOUND",
        "dt_first_Ma": None, "motion_guard_scope": "Event horizon applies only while canonical t0 Euler rates are fixed; it does not bound later motion renewal. P02 is bound only for one first subthreshold step, not indefinite persistence.",
        "active_unbound_numerical_requirements": ["solver/runtime identity", "vertex displacement or verified geometry-error tolerance", "angular rotation limit", "topology rejection/validity rule", "event-localization tolerance", "restart/replay equivalence"],
        "P01_P12_status": {
            "P01_INITIAL_PLATE_KINEMATICS": "BOUND_CANONICAL_MODEL_REALIZATION",
            "P02_MOTION_SEGMENT_VALIDITY": "BOUND_FOR_ONE_FIRST_SUBTHRESHOLD_STEP_ONLY",
            "P03_MOTION_CHANGE_LAW": "NOT_EXERCISED_WITHIN_FIRST_SEGMENT; LONG_TERM_UNBOUND",
            "P04_T0_MASTER_PLATE_GEOMETRY": "MATERIALIZED_AND_VALIDATED",
            "P05_WEAK_ZONE_STATE_AND_STRENGTH": "EXPLICIT_UNKNOWN; NOT_REQUIRED_BY_MINIMAL_GUARD",
            "P06_EXTENSIONAL_FORCING_STATE": "COMPUTED_AT_T0_FROM_RELATIVE_KINEMATICS",
            "P07_RIFT_ELIGIBILITY_RULE": "BOUND_FOR_THIS_OPERATIONAL_GUARD",
            "P08_RIFT_INITIATION_TRIGGER": "BOUND_EVENT_GUARD_ONLY",
            "P09_RIFT_REALIZATION_AND_SPLIT_TOPOLOGY": "DEFERRED_UNTIL_RIFT_INITIATION",
            "P10_INITIAL_EVENT_ELIGIBILITY_CENSUS": "EXECUTED_AT_T0",
            "P11_NUMERICAL_STEP_ACCEPTANCE": "UNBOUND",
            "P12_CANONICAL_UNCERTAINTY_BINDING": "MODEL_UNCERTAINTY_AND_AUTHORIAL_THRESHOLD_ENVELOPE_EXPLICIT; NO_DISTRIBUTION_SAMPLED"
        },
        "first_interval_execution_contract_created": False, "first_interval_executable": False,
        "full_rift_physics_solved": False, "forward_evolution_executed": False, "event_created": False, "plate_split": False,
        "bathymetry": "UNKNOWN", "deep_geodynamic_coupling": "OPTIONAL_UNBOUND", "next_action": "R6_FIRST_INTERVAL_NUMERICAL_STEPPING_BINDING",
    }
    write_json("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V3.json", readiness)
    write_md("R6_FIRST_PHYSICAL_INTERVAL_READINESS_V3.md", f"# R6 first physical interval readiness V3\n\n**Decision:** `{readiness['decision']}`\n\nThe first-event guard is bound only to the explicit ARCANA threshold envelope and the fixed t0 kinematic segment. Its earliest modeled event is {global_years / 1e6:.8g} Ma elapsed, limited by pair `{global_pair}`. This is not a natural minimum. Numerical step acceptance remains unbound, so no first dt or execution contract is authorized. No forward evolution, event, or split occurred.\n\nNext action: `{readiness['next_action']}`.\n")
    print(json.dumps({"decision": readiness["decision"], "counts": counts, "diagnostics": diagnostics,
                      "global_guard_elapsed_years": global_years, "limiting_pair": global_pair,
                      "first_interval_executable": False}, indent=2))


if __name__ == "__main__":
    main()
