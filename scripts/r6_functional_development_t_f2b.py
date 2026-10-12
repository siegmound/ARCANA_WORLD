#!/usr/bin/env python3
"""Noncanonical T-F2B continental engineering experiment; never publishes T1/T2."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.functional_development import (  # noqa: E402
    ReducedState, initial_reduced_state, pure_shear_thermal_step,
    state_from_payload,
)
from arcana_worldsim.r6.int0a_pipeline import (  # noqa: E402
    advance_pair, capture_numerical_step_samples, prepare_pair_5_11,
    trajectory_document, MAX_DIAGNOSTIC_SAMPLES_PER_SUPPORT,
)

SECONDS_PER_YEAR = 31_557_600.0
ENGINEERING_DURATION_YEARS = 1_000.0
RESOLUTION_FACTORS = (0.001, 0.0005, 0.00025)
OUTPUT_RELATIVE = Path("outputs/r6_functional_development/TF2B_5_11_CONTINENTAL_ENGINEERING_V0")
MAX_DIAGNOSTIC_PROFILE_NODES = 73


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _area_relative_errors(states: list[ReducedState], width_m: float) -> list[float]:
    return [abs((state.width_m * state.lithosphere_m)
                - (width_m * state.initial_lithosphere_m))
            / (width_m * state.initial_lithosphere_m) for state in states]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--expected-branch", default="r6/si1-bandwidth-f2av")
    parser.add_argument("--output-relative", type=Path, default=OUTPUT_RELATIVE)
    args = parser.parse_args()
    root = args.repository_root.resolve()
    output_path = (root / args.output_relative).resolve()
    allowed_root = (root / "outputs/r6_functional_development").resolve()
    if allowed_root not in output_path.parents:
        parser.error("output must remain below outputs/r6_functional_development")
    if output_path.exists():
        parser.error(f"refusing to overwrite existing output: {args.output_relative.as_posix()}")

    plan = prepare_pair_5_11(root, expected_branch=args.expected_branch)
    assessment = plan.assessment
    selected = plan.selected_section
    sides = selected["sides_plate_a_then_plate_b"]
    profiles = list(plan.profiles)
    if len(profiles) != 2 or profiles[0].material_roles != profiles[1].material_roles:
        raise RuntimeError("TWO_SIDED_MATERIAL_ROLE_CONSISTENCY_FAILED")
    if not all(len(p.temperature_k) == len(p.z_m) == len(p.materials) for p in profiles):
        raise RuntimeError("T0_PROFILE_CARDINALITY_MISMATCH")
    if any(len(p.temperature_k) > MAX_DIAGNOSTIC_PROFILE_NODES for p in profiles):
        raise RuntimeError("DIAGNOSTIC_PROFILE_NODE_LIMIT_EXCEEDED")
    edge = selected["parent_grid_edge"]
    width = plan.initial_width_m
    if not math.isfinite(width) or width <= 0:
        raise RuntimeError("ENGINEERING_XE_SUPPORT_DISTANCE_INVALID")
    ux = plan.signed_extension_m_per_year
    if ux <= 0:
        raise RuntimeError("SELECTED_SECTION_IS_NOT_EXTENSIONAL")
    duration_s = ENGINEERING_DURATION_YEARS * SECONDS_PER_YEAR

    resolution_results = []
    middle_fraction = RESOLUTION_FACTORS[1]
    diagnostic_sample_records: dict[str, list[dict[str, object]]] | None = None
    for fraction in RESOLUTION_FACTORS:
        if fraction == middle_fraction:
            evolved, diagnostics, diagnostic_sample_records = capture_numerical_step_samples(
                plan, duration_s=duration_s,
                maximum_kinematic_fraction_per_substep=fraction)
        else:
            evolved, diagnostics = advance_pair(plan, duration_s=duration_s,
                maximum_kinematic_fraction_per_substep=fraction)
        evolved, diagnostics = list(evolved), list(diagnostics)
        deltas = [max(abs(a - b) for a, b in zip(profile.temperature_k, state.temperature_k))
                  for profile, state in zip(profiles, evolved)]
        resolution_results.append({
            "maximum_kinematic_fraction_per_substep": fraction,
            "side_diagnostics": diagnostics,
            "final_states": [state.payload() for state in evolved],
            "temperature_change_linf_k_by_side": deltas,
            "max_temperature_change_linf_k": max(deltas),
            "max_area_relative_error": max(_area_relative_errors(evolved, width)),
            "all_temperatures_finite": all(math.isfinite(x) for state in evolved for x in state.temperature_k),
        })
    if not all(row["all_temperatures_finite"] for row in resolution_results):
        raise RuntimeError("ENGINEERING_TEMPERATURE_FIELD_NONFINITE")
    if any(row["max_area_relative_error"] > 1e-12 for row in resolution_results):
        raise RuntimeError("PURE_SHEAR_AREA_CONSERVATION_FAILED")
    if diagnostic_sample_records is None:
        raise RuntimeError("DIAGNOSTIC_SAMPLES_MISSING_FOR_REFERENCE_RESOLUTION")
    for index, (support_id, final_state) in enumerate(zip(plan.support_ids,
                                                           resolution_results[1]["final_states"])):
        records = diagnostic_sample_records[support_id]
        times = [float(row["time_s"]) for row in records]
        if (not records or times[0] != 0.0
                or any(earlier >= later for earlier, later in zip(times, times[1]))):
            raise RuntimeError("DIAGNOSTIC_SAMPLE_TIME_SEQUENCE_INVALID")
        endpoint = records[-1]
        endpoint_fields = ("time_s", "elapsed_years", "width_m", "crust_m",
                           "lithosphere_m", "beta", "accumulated_strain",
                           "material_coordinate", "temperature_k")
        if any(endpoint[field] != final_state[field] for field in endpoint_fields):
            raise RuntimeError(f"DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH:{support_id}:{index}")
        expected_z = [value * float(final_state["lithosphere_m"])
                      for value in final_state["material_coordinate"]]
        if endpoint["z_m"] != expected_z:
            raise RuntimeError(f"DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH:{support_id}:{index}")

    # The middle resolution is the explicit deterministic replay/restart case.
    direct, _ = advance_pair(plan, duration_s=duration_s,
                             maximum_kinematic_fraction_per_substep=middle_fraction)
    replay, _ = advance_pair(plan, duration_s=duration_s,
                             maximum_kinematic_fraction_per_substep=middle_fraction)
    direct, replay = list(direct), list(replay)
    direct_hashes = [_sha256_bytes(_canonical_bytes(state.payload())) for state in direct]
    replay_hashes = [_sha256_bytes(_canonical_bytes(state.payload())) for state in replay]
    half = duration_s / 2.0
    restarted = []
    for profile in profiles:
        state0 = initial_reduced_state(profile, initial_width_m=width)
        first_half, _ = pure_shear_thermal_step(
            state0, duration_s=half, extension_velocity_m_s=ux / SECONDS_PER_YEAR,
            maximum_kinematic_fraction_per_substep=middle_fraction)
        checkpoint_payload = first_half.payload()
        reopened = state_from_payload(json.loads(_canonical_bytes(checkpoint_payload)))
        second_half, _ = pure_shear_thermal_step(
            reopened, duration_s=half, extension_velocity_m_s=ux / SECONDS_PER_YEAR,
            maximum_kinematic_fraction_per_substep=middle_fraction)
        restarted.append(second_half)
    restart_hashes = [_sha256_bytes(_canonical_bytes(state.payload())) for state in restarted]
    restart_replay = []
    for profile in profiles:
        state0 = initial_reduced_state(profile, initial_width_m=width)
        first_half, _ = pure_shear_thermal_step(
            state0, duration_s=half, extension_velocity_m_s=ux / SECONDS_PER_YEAR,
            maximum_kinematic_fraction_per_substep=middle_fraction)
        reopened = state_from_payload(json.loads(_canonical_bytes(first_half.payload())))
        second_half, _ = pure_shear_thermal_step(
            reopened, duration_s=half, extension_velocity_m_s=ux / SECONDS_PER_YEAR,
            maximum_kinematic_fraction_per_substep=middle_fraction)
        restart_replay.append(second_half)
    restart_replay_hashes = [_sha256_bytes(_canonical_bytes(state.payload())) for state in restart_replay]
    restart_temperature_differences = [
        max(abs(a - b) for a, b in zip(full.temperature_k, restart.temperature_k))
        for full, restart in zip(direct, restarted)]
    replay_ok = direct_hashes == replay_hashes and restart_hashes == restart_replay_hashes
    if not replay_ok:
        raise RuntimeError("ENGINEERING_REPLAY_OR_RESTART_MISMATCH")

    section = {
        "scope": "T0_CONTINENTAL_ENGINEERING_EXTENSION_EXPERIMENT",
        "boundary_id": selected["boundary_id"],
        "ordered_plate_pair": [5, 11],
        "side_order": "PLATE_A_THEN_PLATE_B",
        "support_ids": [side["support_id"] for side in sides],
        "side_profiles": [side["t0_profile"] for side in sides],
        "section_frame": {"orientation": "TANGENT_NORMAL_PLANE_AT_PARENT_GRID_EDGE_MIDPOINT",
            "normal_from_plate_a_to_plate_b_xyz": selected["velocity_components"]["normal_ab_xyz"],
            "tangent_xyz": selected["velocity_components"]["tangent_xyz"],
            "edge_axis": edge["axis"]},
        "euler_source_identity_sha256": assessment["kinematics_semantic_identity_sha256"],
        "euler_source_record_raw_sha256": assessment["kinematics_artifact_sha256"],
        "source_set_identity_sha256": assessment["source_identity_sha256"],
        "euler_plate_vectors_rad_per_year": assessment["plate_euler_vectors_rad_per_year"],
        "relative_velocity_components": selected["velocity_components"],
        "signed_candidate_Ux_m_per_year": ux,
        "forcing_mode": "FROZEN_INSTANTANEOUS_ENGINEERING_DRIVER",
        "Xe_engineering_reference": {"value_m": width,
            "definition": "GREAT_CIRCLE_DISTANCE_BETWEEN_ADJACENT_PARENT_CELL_CENTRES",
            "authority": "NUMERICAL_ENGINEERING_REFERENCE_ONLY_NOT_BUCK_PHYSICAL_XE"},
        "support_uncertainty_provenance": {
            "grid_id": "R6_GLOBAL_GEOGRAPHY_1DEG_V1",
            "resolution": "ONE_DEGREE_PARENT_CELL_SUPPORT; NO_SUBCELL_PHYSICAL_RESOLUTION_PROMOTION",
            "boundary_support": "COARSE_SUPPORT_ON_FINE_GRID",
            "vector_partition_payload_sha256": assessment["vector_partition_payload_sha256"],
            "field_package_sha256": assessment["b6n8n_field_package_sha256"],
            "binding_index_sha256": assessment["b6n8n_index_sha256"],
            "kinematics_uncertainty": assessment["kinematics_uncertainty"],
            "event_census_uncertainty": assessment["pair_event_census"]["uncertainty"],
            "side_profile_support_lineage": [side["t0_profile"]["support_lineage"] for side in sides]},
        "duration_years": ENGINEERING_DURATION_YEARS,
        "temperature_boundary_conditions": "EXISTING_TF1_COLUMN_CONTRACT_FIXED_SURFACE_AND_MODEL_BASE",
        "lateral_thermal_coupling": "NOT_MODELED_IN_REDUCED_1D_COLUMN_PAIR",
        "physical_temporal_validity": "NOT_ESTABLISHED",
        "canonical_event_or_T1_T2": False,
        "physical_section_selected": False,
        "engineering_reference_section_selected": True,
        "lateral_physical_section_model_qualified": False,
    }
    run_result = {
        "decision": "CONTINENTAL_ENGINEERING_SLICE_PASS",
        "scope": "T0_CONTINENTAL_ENGINEERING_EXTENSION_EXPERIMENT",
        "checkpoint_commit": assessment["source_head"],
        "source_branch": assessment["source_branch"],
        "mapping_identity_sha256": assessment["mapping_join"]["mapping_sha256"],
        "pair_5_11_event_eligibility": assessment["pair_event_census"],
        "pair_5_11_edge_count": len(assessment["edge_matrix"]),
        "pair_5_11_admitted_two_sided_nonjunction_extension_count": sum(
            row["SECTION_ELIGIBILITY"] == "ELIGIBLE" for row in assessment["edge_matrix"]),
        "selected_boundary_id": selected["boundary_id"],
        "physical_section_selected": False,
        "engineering_reference_section_selected": True,
        "selected_support_ids": section["support_ids"],
        "signed_Ux_m_per_year": ux,
        "Xe_engineering_reference_m": width,
        "duration_years": ENGINEERING_DURATION_YEARS,
        "resolution_control": "MAXIMUM_KINEMATIC_FRACTION_PER_SUBSTEP",
        "resolution_factors": list(RESOLUTION_FACTORS),
        "resolution_results": [{k: v for k, v in row.items() if k != "final_states"}
                               for row in resolution_results],
        "replay_restart": {"direct_state_sha256": direct_hashes,
            "replay_state_sha256": replay_hashes,
            "restart_state_sha256": restart_hashes,
            "restart_replay_state_sha256": restart_replay_hashes,
            "deterministic_replay": direct_hashes == replay_hashes,
            "deterministic_restart": restart_hashes == restart_replay_hashes,
            "restart_vs_uninterrupted_temperature_max_abs_difference_k": restart_temperature_differences,
            "restart_pass": replay_ok},
        "preserved_non_actions": {"canonical_publication": False,
            "world_history_accessed": False, "world_history_mutated": False,
            "post_event_B6N2_forcing_consumed": False, "canonical_T1_or_T2_created": False,
            "topology_or_global_plate_geometry_changed": False,
            "1_3_oceanic_pair_repurposed": False},
        "output_relative_path": args.output_relative.as_posix(),
    }
    artifacts = {
        "EDGE_AUDIT_MATRIX.json": {"schema": "ARCANA_R6_TF2B_PAIR_EDGE_AUDIT_V1",
                                   **assessment},
        "SELECTED_SECTION_AND_PROFILES.json": section,
        "CANDIDATE_CHECKPOINT.json": {"schema": "ARCANA_R6_TF2B_ENGINEERING_CHECKPOINT_V1",
            "scope": section["scope"], "initial_states": [
                initial_reduced_state(profile, initial_width_m=width).payload() for profile in profiles],
            "candidate_states": resolution_results[1]["final_states"],
            "elapsed_years": ENGINEERING_DURATION_YEARS, "canonical_publication": False},
        "THERMAL_CONVERGENCE.json": {"resolution_results": resolution_results,
            "comparison_to_finest": [
                {"factor": row["maximum_kinematic_fraction_per_substep"],
                 "temperature_max_abs_difference_k": max(
                     max(abs(a - b) for a, b in zip(state["temperature_k"], fine["temperature_k"]))
                     for state, fine in zip(row["final_states"], resolution_results[-1]["final_states"]))}
                for row in resolution_results],
            "comparison_is_numerical_refinement_only": True},
        "DIAGNOSTIC_NUMERICAL_SAMPLES.json": {
            "schema": "ARCANA_R6_TF2B_NUMERICAL_STEP_SAMPLES_V1",
            "scope": "NONCANONICAL_ENGINEERING_REFERENCE_TRAJECTORY",
            "support_ids": list(plan.support_ids),
            "sampling": "INITIAL_AND_EVERY_MIDDLE_RESOLUTION_NUMERICAL_SUBSTEP",
            "resolution_fraction": middle_fraction,
            "interpolation": "NONE",
            "maximum_samples_per_support_including_initial": MAX_DIAGNOSTIC_SAMPLES_PER_SUPPORT,
            "maximum_profile_nodes": MAX_DIAGNOSTIC_PROFILE_NODES,
            "units": {"time_s": "s", "elapsed_years": "year", "width_m": "m",
                "crust_m": "m", "lithosphere_m": "m", "beta": "1",
                "accumulated_strain": "1", "material_coordinate": "1",
                "z_m": "m", "temperature_k": "K"},
            "all_numerical_substeps_captured": True,
            "sample_count_by_support": {key: len(value)
                for key, value in diagnostic_sample_records.items()},
            "samples_by_support": diagnostic_sample_records,
            "canonical_publication": False,
        },
        "REPLAY_RESTART.json": run_result["replay_restart"],
        "CANDIDATE_TRAJECTORY.json": trajectory_document(
            plan, tuple(direct), duration_s=duration_s,
            numerical_configuration={
                "maximum_kinematic_fraction_per_substep": middle_fraction,
                "kernel": "functional_development.pure_shear_thermal_step",
                "duration_years": ENGINEERING_DURATION_YEARS,
            }),
    }
    output_path.mkdir(parents=True)
    hashes = {}
    for name, value in artifacts.items():
        data = _canonical_bytes(value)
        (output_path / name).write_bytes(data)
        hashes[name] = _sha256_bytes(data)
    run_result["artifact_sha256"] = hashes
    run_result_bytes = _canonical_bytes(run_result)
    (output_path / "RUN_RESULT.json").write_bytes(run_result_bytes)
    output_manifest = {
        "schema": "ARCANA_R6_TF2B_INT0_OUTPUT_MANIFEST_V1",
        "canonical_publication": False,
        "provider_identities": dict(plan.provider_identities),
        "configuration_sha256": plan.configuration_sha256,
        "files": {name: {"bytes": len(_canonical_bytes(value)), "sha256": hashes[name]}
                  for name, value in artifacts.items()},
        "RUN_RESULT.json": {"bytes": len(run_result_bytes),
                            "sha256": _sha256_bytes(run_result_bytes)},
    }
    (output_path / "CANDIDATE_MANIFEST.json").write_bytes(_canonical_bytes(output_manifest))
    print(json.dumps({"decision": run_result["decision"],
        "selected_boundary_id": selected["boundary_id"],
        "selected_support_ids": section["support_ids"], "signed_Ux_m_per_year": ux,
        "output": args.output_relative.as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
