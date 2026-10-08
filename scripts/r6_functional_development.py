#!/usr/bin/env python3
"""Run a noncanonical T-F1/T-F2 engineering development slice."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.functional_development import (  # noqa: E402
    ENGINEERING_SCENARIO,
    T0_TO_T1_SECONDS,
    evolve_fixed_geometry_thermal_profile,
    materialize_admitted_continental_t0,
    select_pair_13_interior_segment,
)


FLAGS = ["NON_CANONICAL", "ENGINEERING_REFERENCE", "MODEL_DEPENDENT", "NOT_RECONSTRUCTED_HISTORY"]


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _write(path: Path, value: object) -> str:
    data = _json_bytes(value)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    parser.add_argument("--support-id", help="one exact admitted continental native support ID")
    parser.add_argument("--output-root", type=Path, default=ROOT / "outputs/r6_functional_development")
    args = parser.parse_args()
    root = args.repository_root.resolve()
    output_root = args.output_root.resolve()
    expected_output = (root / "outputs/r6_functional_development").resolve()
    if output_root != expected_output:
        parser.error("development outputs must remain under outputs/r6_functional_development")
    run_root = output_root / "TF1_TF2_REFERENCE_ENGINEERING_V0"
    if run_root.exists():
        parser.error(f"output already exists; refusing to overwrite: {run_root}")

    profile, authority = materialize_admitted_continental_t0(root, args.support_id)
    pair = select_pair_13_interior_segment(root)
    output = {
        "scope": FLAGS,
        "scenario_id": ENGINEERING_SCENARIO,
        "model_identity": "DEVELOPMENT_PURE_SHEAR_THERMAL_STRETCHING_V0",
        "source_commit": authority["source_commit"],
        "stage_status": {
            "T0_MATERIALIZATION_PASS": True,
            "REDUCED_KERNEL_TEST_PASS": "SEE_TEST_SUITE; POST_EVENT_RIFT_COUPLING_NOT_RUN",
            "LOCAL_FUNCTIONAL_SLICE_PASS": False,
            "BLOCKED_BY_REAL_SUPPORT_MAPPING": True,
        },
        "T0_profile": {
            "support_id": profile.support_id,
            "support_class": profile.support_class,
            "world_age_ma": 210.0,
            "node_count": len(profile.z_m),
            "moho_depth_m": profile.crust_m,
            "model_base_depth_m": profile.model_base_m,
            "model_base_semantics": "AUTHORED_TOTAL_THERMAL_THICKNESS_NOT_PHYSICAL_LAB",
            "surface_heat_flow_w_m2": profile.surface_heat_flow_w_m2,
            "surface_temperature_k": profile.surface_temperature_k,
            "moho_temperature_k": profile.temperature_k[profile.z_m.index(profile.crust_m)],
            "base_temperature_k": profile.base_temperature_k,
            "minimum_temperature_k": min(profile.temperature_k),
            "maximum_temperature_k": max(profile.temperature_k),
            "profile_provenance": dict(profile.provenance),
        },
        "pre_event_thermal_development": {
            "target_selector": "T1_PRE_EVENT_APPROXIMATION",
            "target_age_ma": 209.97287659484368,
            "elapsed_years": (210.0 - 209.97287659484368) * 1_000_000.0,
            "elapsed_seconds": T0_TO_T1_SECONDS,
            "geometry": "HELD_CONSTANT_ENGINEERING_APPROXIMATION",
            "surface_boundary": "FIXED_AT_GOVERNED_REFERENCE_T0_TEMPERATURE",
            "model_base_boundary": "FIXED_AT_T0_COLUMN_ENDPOINT_TEMPERATURE; MODEL_BASE_NOT_PHYSICAL_LAB",
            "post_event_rift_forcing_applied": False,
            "thermal_equation": "EXPLICIT_FINITE_VOLUME_CONDUCTION_PLUS_NODEWISE_RADIOGENIC_SOURCE_ON_FIXED_PHYSICAL_GRID",
        },
        "pair_1_3_section": pair,
        "forcing_manifest": {
            "scope": FLAGS,
            "FORCING_MODE": "NOT_INSTANTIATED",
            "allowed_mode_if_mapping_closes": "FROZEN_INSTANTANEOUS_ENGINEERING_DRIVER",
            "PHYSICAL_TEMPORAL_VALIDITY": "NOT_ESTABLISHED",
            "HISTORICAL_RECONSTRUCTION": False,
            "CANONICAL_STATE": False,
            "driver_application": "NOT_APPLIED; section-adjacent admitted two-sided material binding is absent",
            "post_event_B6N2_data_consumed": False,
            "local_functional_rift_step_executed": False,
        },
        "preserved_gates": {
            "WORLD_HISTORY_mutated": False,
            "canonical_publication": False,
            "T2_created": False,
            "dt2_canonical_selected": False,
            "mechanics_executed": False,
            "topology_changed": False,
        },
    }

    # The pre-event endpoint is an explicitly noncanonical approximation. Run
    # independent coarse/fine integrations to retain a small convergence trace.
    convergence = []
    thermal_runs = {}
    for divisor in (1, 2, 4, 8):
        values, diag = evolve_fixed_geometry_thermal_profile(
            profile, duration_s=T0_TO_T1_SECONDS,
            maximum_substep_s=T0_TO_T1_SECONDS / divisor,
        )
        thermal_runs[divisor] = values
        convergence.append({"nominal_steps": divisor, "actual_substeps": diag.substeps,
                            "max_stability_ratio": diag.max_stability_ratio,
                            "temperature_change_linf_k": diag.temperature_change_linf_k,
                            "linf_difference_from_dt_over_8_k": max(abs(a-b) for a,b in zip(values, thermal_runs.get(8, values))) if divisor == 8 else None})
    # Fill convergence differences after all four states exist.
    finest = thermal_runs[8]
    for row in convergence:
        divisor = row["nominal_steps"]
        row["linf_difference_from_dt_over_8_k"] = max(abs(a-b) for a,b in zip(thermal_runs[divisor], finest))
    thermal_values, thermal_diag = evolve_fixed_geometry_thermal_profile(
        profile, duration_s=T0_TO_T1_SECONDS,
    )
    initial_payload = {
        "schema": "ARCANA_R6_FUNCTIONAL_DEVELOPMENT_INITIAL_STATE_V1",
        "scope": FLAGS, "state_role": "T0_REFERENCE_ENGINEERING_INITIAL_STATE",
        "scenario_id": ENGINEERING_SCENARIO, "world_age_ma": 210.0,
        "support_id": profile.support_id, "support_class": profile.support_class,
        "z_m": list(profile.z_m), "temperature_k": list(profile.temperature_k),
        "materials": [item.__dict__ for item in profile.materials],
        "material_ids_are_discrete_and_not_interpolated": True,
        "provenance": dict(profile.provenance),
    }
    evolved_payload = {
        "schema": "ARCANA_R6_FUNCTIONAL_DEVELOPMENT_EVOLVED_STATE_V1",
        "scope": FLAGS, "state_role": "T1_PRE_EVENT_ENGINEERING_APPROXIMATION",
        "scenario_id": ENGINEERING_SCENARIO, "world_age_ma": 209.97287659484368,
        "support_id": profile.support_id, "support_class": profile.support_class,
        "z_m": list(profile.z_m), "temperature_k": list(thermal_values),
        "materials": [item.__dict__ for item in profile.materials],
        "geometry_held_constant": True,
        "post_event_rift_forcing_applied": False,
        "boundary_conditions": {"surface_temperature_k": profile.surface_temperature_k,
                                "model_base_temperature_k": profile.base_temperature_k},
    }
    convergence_payload = {
        "scope": FLAGS,
        "method": "FORWARD_EULER_EXPLICIT_FINITE_VOLUME; same spatial grid and fixed boundaries",
        "stability_limit_s": thermal_diag.min_stability_limit_s,
        "runs": convergence,
        "interpretation": "engineering numerical convergence trace only; not physical-model validation",
    }

    run_root.mkdir(parents=True)
    files = {
        "initial_state.json": initial_payload,
        "pre_event_t1_approximation.json": evolved_payload,
        "section_and_support_manifest.json": {"scope": FLAGS, "section_probe": pair},
        "forcing_manifest.json": output["forcing_manifest"],
        "thermal_convergence.json": convergence_payload,
        "step_diagnostics.json": {"scope": FLAGS, "diagnostics": asdict(thermal_diag)},
        "checkpoint.json": {"scope": FLAGS,
                             "checkpoint_type": "NONCANONICAL_ENGINEERING_RESTART",
                             "state": evolved_payload},
    }
    hashes = {name: _write(run_root / name, data) for name, data in files.items()}
    # Restart/replay compares exact deterministic JSON bytes from a fresh
    # reconstruction of the persisted initial profile.
    replay_values, replay_diag = evolve_fixed_geometry_thermal_profile(
        profile, duration_s=T0_TO_T1_SECONDS,
    )
    replay_payload = {**evolved_payload, "temperature_k": list(replay_values)}
    replay_equal = _json_bytes(evolved_payload) == _json_bytes(replay_payload)
    replay = {"scope": FLAGS,
              "checkpoint_schema": "NONCANONICAL_ENGINEERING_RESTART",
              "replay_byte_identical": replay_equal,
              "initial_state_sha256": hashes["initial_state.json"],
              "evolved_state_sha256": hashes["pre_event_t1_approximation.json"],
              "replay_diagnostics": asdict(replay_diag),
              "canonical_publication": False}
    hashes["replay_comparison.json"] = _write(run_root / "replay_comparison.json", replay)
    output["artifact_hashes"] = hashes
    output["output_relative_path"] = run_root.relative_to(root).as_posix()
    output["world_history_accessed"] = False
    output["world_history_mutated"] = False
    _write(run_root / "RUN_RESULT.json", output)
    print(json.dumps({"decision": "BLOCKED_BY_REAL_SUPPORT_MAPPING",
                      "T0_MATERIALIZATION_PASS": True,
                      "REDUCED_KERNEL_TEST_PASS": "runner numerical integration and kernel regression required",
                      "LOCAL_FUNCTIONAL_SLICE_PASS": False,
                      "support_id": profile.support_id,
                      "output": run_root.relative_to(root).as_posix()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
