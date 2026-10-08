#!/usr/bin/env python3
"""Noncanonical T-F2B continental engineering experiment; never publishes T1/T2."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.functional_development import (  # noqa: E402
    NodeMaterial, ReducedState, T0Profile, initial_reduced_state,
    pure_shear_thermal_step, state_from_payload,
)
from arcana_worldsim.r6.functional_spatial_support import (  # noqa: E402
    audit_pair_5_11,
)

SECONDS_PER_YEAR = 31_557_600.0
ENGINEERING_DURATION_YEARS = 1_000.0
RESOLUTION_FACTORS = (0.001, 0.0005, 0.00025)
OUTPUT_RELATIVE = Path("outputs/r6_functional_development/TF2B_5_11_CONTINENTAL_ENGINEERING_V0")


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _profile_from_mapping(side: dict) -> T0Profile:
    raw = side["t0_profile"]
    materials = tuple(NodeMaterial(**item) for item in raw["material_properties"])
    temperatures = tuple(float(item) for item in raw["temperature_k"])
    return T0Profile(
        support_id=str(side["support_id"]), support_class=str(side["support_class"]),
        scenario_id=str(raw["scenario_id"]), crust_m=float(raw["crust_m"]),
        model_base_m=float(raw["model_base_m"]),
        surface_temperature_k=float(raw["surface_temperature_k"]),
        base_temperature_k=temperatures[-1],
        surface_heat_flow_w_m2=float(raw["surface_heat_flow_w_m2"]),
        z_m=tuple(float(item) for item in raw["z_m"]), temperature_k=temperatures,
        materials=materials, material_roles=tuple(raw["material_roles"]),
        provenance=dict(raw["support_lineage"]))


def _center_xyz(row: int, column: int, radius_m: float) -> tuple[float, float, float]:
    latitude = math.radians(-90.0 + row + 0.5)
    longitude = math.radians(-180.0 + column + 0.5)
    return (radius_m * math.cos(latitude) * math.cos(longitude),
            radius_m * math.cos(latitude) * math.sin(longitude),
            radius_m * math.sin(latitude))


def _distance_m(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    dot = sum(a * b for a, b in zip(first, second))
    norm_first = math.sqrt(sum(x * x for x in first))
    norm_second = math.sqrt(sum(x * x for x in second))
    cosine = max(-1.0, min(1.0, dot / (norm_first * norm_second)))
    return norm_first * math.acos(cosine)


def _advance_pair(profiles: list[T0Profile], width_m: float, ux_m_per_year: float,
                  kinematic_fraction: float, duration_s: float) -> tuple[list[ReducedState], list[dict]]:
    initial = [initial_reduced_state(profile, initial_width_m=width_m) for profile in profiles]
    result, diagnostics = [], []
    for state in initial:
        evolved, diag = pure_shear_thermal_step(
            state, duration_s=duration_s,
            extension_velocity_m_s=ux_m_per_year / SECONDS_PER_YEAR,
            maximum_kinematic_fraction_per_substep=kinematic_fraction,
        )
        result.append(evolved)
        diagnostics.append(asdict(diag))
    return result, diagnostics


def _area_relative_errors(states: list[ReducedState], width_m: float) -> list[float]:
    return [abs((state.width_m * state.lithosphere_m)
                - (width_m * state.initial_lithosphere_m))
            / (width_m * state.initial_lithosphere_m) for state in states]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--expected-branch", default="r6/tectonics-drift-functional-mvp")
    parser.add_argument("--output-relative", type=Path, default=OUTPUT_RELATIVE)
    args = parser.parse_args()
    root = args.repository_root.resolve()
    output_path = (root / args.output_relative).resolve()
    allowed_root = (root / "outputs/r6_functional_development").resolve()
    if allowed_root not in output_path.parents:
        parser.error("output must remain below outputs/r6_functional_development")
    if output_path.exists():
        parser.error(f"refusing to overwrite existing output: {args.output_relative.as_posix()}")

    assessment = audit_pair_5_11(root, expected_branch=args.expected_branch)
    selected = next(row for row in assessment["edge_matrix"]
                    if row["boundary_id"] == assessment["selected_boundary_id"])
    sides = selected["sides_plate_a_then_plate_b"]
    profiles = [_profile_from_mapping(side) for side in sides]
    if len(profiles) != 2 or profiles[0].material_roles != profiles[1].material_roles:
        raise RuntimeError("TWO_SIDED_MATERIAL_ROLE_CONSISTENCY_FAILED")
    if not all(len(p.temperature_k) == len(p.z_m) == len(p.materials) for p in profiles):
        raise RuntimeError("T0_PROFILE_CARDINALITY_MISMATCH")
    edge = selected["parent_grid_edge"]
    width = _distance_m(_center_xyz(sides[0]["row"], sides[0]["column"],
                                   float(assessment["source_grid_radius_m"])),
                        _center_xyz(sides[1]["row"], sides[1]["column"],
                                   float(assessment["source_grid_radius_m"])))
    if not math.isfinite(width) or width <= 0:
        raise RuntimeError("ENGINEERING_XE_SUPPORT_DISTANCE_INVALID")
    ux = float(selected["signed_Ux_m_per_year"])
    if ux <= 0:
        raise RuntimeError("SELECTED_SECTION_IS_NOT_EXTENSIONAL")
    duration_s = ENGINEERING_DURATION_YEARS * SECONDS_PER_YEAR

    resolution_results = []
    for fraction in RESOLUTION_FACTORS:
        evolved, diagnostics = _advance_pair(profiles, width, ux, fraction, duration_s)
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

    # The middle resolution is the explicit deterministic replay/restart case.
    middle_fraction = RESOLUTION_FACTORS[1]
    direct, _ = _advance_pair(profiles, width, ux, middle_fraction, duration_s)
    replay, _ = _advance_pair(profiles, width, ux, middle_fraction, duration_s)
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
        "REPLAY_RESTART.json": run_result["replay_restart"],
    }
    output_path.mkdir(parents=True)
    hashes = {}
    for name, value in artifacts.items():
        data = _canonical_bytes(value)
        (output_path / name).write_bytes(data)
        hashes[name] = _sha256_bytes(data)
    run_result["artifact_sha256"] = hashes
    (output_path / "RUN_RESULT.json").write_bytes(_canonical_bytes(run_result))
    print(json.dumps({"decision": run_result["decision"],
        "selected_boundary_id": selected["boundary_id"],
        "selected_support_ids": section["support_ids"], "signed_Ux_m_per_year": ux,
        "output": args.output_relative.as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
