"""Explicitly noncanonical 100-year thermal-column numeric experiment.

FAIR verification of a *synthetic* 1D heat-transport benchmark anchored only
to original T0 *model* geometry and specialist *reference* properties.
It cannot produce physical ARCANA T1, canonical WorldHistory, or actual ore/Deep.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from .geological_source_t0_adapter import (
    extract as extract_original_t0,
    gitblob as _gitblob,
)
from .identity import content_hash

SCHEMA = "ARCANA_R6_EXPERIMENTAL_100Y_THERMAL_COLUMN_CONFIG_V1"
REPORT_SCHEMA = "ARCANA_R6_EXPERIMENTAL_NONCANONICAL_100Y_COLUMN_REPORT_V1"
AUTHORITY = "EXPERIMENTAL_NONCANONICAL_ONLY"
POLICY = "docs/arcana/governance/R6_EXPERIMENTAL_RUN_NONCANONICAL_POLICY.json"
POLICY_BLOB = "75658d37b12ac3d2c3b3fed5b9e56203a6ae3cf1"
REF_PATH = "R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json"
REF_BLOB = "e041e7dc91f617cf7f755b46ab36e7417d486fd0"
JULIAN_YEAR_S = 365.25 * 24 * 3600
LEVELS = ((50, 1.0), (100, 0.25), (200, 0.0625))


class ExperimentalColumnError(ValueError):
    """Refuse invalid science inputs, authenticity, or numerical stability."""


def must(ok, reason):
    if not ok:
        raise ExperimentalColumnError(reason)


def _pinned_json(root: Path, path: str, blob: str) -> dict:
    raw = (root / path).read_bytes()
    must(_gitblob(raw) == blob, "EXPERIMENTAL_PINNED_SOURCE_DRIFT:" + path)
    return json.loads(raw)


def governance(root: Path) -> dict:
    policy = _pinned_json(root, POLICY, POLICY_BLOB)
    must(policy["schema"] ==
         "ARCANA_R6_EXPERIMENTAL_SIMULATION_GOVERNANCE_V1"
         and policy["status"] == "ACTIVE"
         and policy["rule"] ==
             "EXPERIMENTAL_RUNS_ARE_ALWAYS_NONCANONICAL_AND_NEVER_AUTO_PROMOTE"
         and policy["experimental_authority"] == AUTHORITY
         and policy["canonical_world_history_write_authorized"] is False
         and policy["physical_t1_authorized"] is False
         and policy["history_store_mutations_authorized"] is False
         and policy["automatic_promotion_after_simulator_completion"] is False
         and policy["new_production_runs_required_after_ratification"] is True
         and policy["target_initial_pilot_duration_years"] == 100
         and policy["D_024"] == "ACTIVE"
         and policy["physical_T1"] is None,
         "EXPERIMENTAL_WORLD_SIM_GOVERNANCE_NOT_ACCEPTED")
    return policy


def validate_config(raw: dict) -> dict:
    must(type(raw) is dict and set(raw) == {
        "schema", "authority", "source_parent_cell_id",
        "requested_duration_years", "synthetic_column_depth_m",
        "initial_temperature_k", "adiabatic_boundary_conditions",
        "material_property_mode", "heat_production_mode",
        "experimental_run_label"},
        "EXPERIMENTAL_CONFIG_FIELDS_INVALID")
    must(raw["schema"] == SCHEMA and raw["authority"] == AUTHORITY,
         "EXPERIMENTAL_ONLY_AUTHORITY_REQUIRED")
    must(raw["source_parent_cell_id"] == "R6G1D-R089-C359",
         "EXPERIMENTAL_SELECTED_SOURCE_CELL_NOT_QUALIFIED")
    must(type(raw["requested_duration_years"]) is int
         and raw["requested_duration_years"] == 100,
         "EXPERIMENTAL_100Y_ONLY_1000Y_NOT_YET_QUALIFIED")
    depth = raw["synthetic_column_depth_m"]
    must(type(depth) in (int, float) and
         math.isfinite(depth) and float(depth) == 1000.0,
         "EXPERIMENTAL_DEPTH_EXACT_SYNTHETIC_BENCHMARK_REQUIRED")
    temp = raw["initial_temperature_k"]
    must(type(temp) is dict and set(temp) == {
        "kind", "base_k", "cosine_amplitude_k", "authority"},
        "EXPERIMENTAL_INITIAL_TEMPERATURE_SCHEMA_INVALID")
    must(temp["kind"] == "CELL_CENTERED_COSINE_MODE"
         and temp["authority"] == "DECLARED_SYNTHETIC_NOT_PHYSICAL_T0"
         and type(temp["base_k"]) in (int, float)
         and type(temp["cosine_amplitude_k"]) in (int, float)
         and math.isfinite(temp["base_k"])
         and math.isfinite(temp["cosine_amplitude_k"])
         and temp["base_k"] == 300.0
         and temp["cosine_amplitude_k"] == 15.0,
         "EXPERIMENTAL_SYNTHETIC_INITIAL_PROFILE_REQUIRED")
    must(raw["adiabatic_boundary_conditions"] ==
         {"top": "ZERO_HEAT_FLUX",
          "bottom": "ZERO_HEAT_FLUX",
          "authority": "SYNTHETIC_EXPERIMENT_BOUNDARY_ONLY"},
         "EXPERIMENTAL_BOUNDARY_CONDITIONS_NOT_QUALIFIED")
    must(raw["material_property_mode"] ==
         "AUTHORED_SPECIALIST_OCEANIC_CRUST_BULK_REFERENCE_NOT_CELL_OBSERVED"
         and raw["heat_production_mode"] ==
         "AUTHORED_SPECIALIST_OCEANIC_BULK_REFERENCE_NOT_CELL_OBSERVED",
         "EXPERIMENTAL_REFERENCE_NOT_NATURAL_PROPERTIES_REQUIRED")
    label = raw["experimental_run_label"]
    must(type(label) is str
         and label == "synthetic_ocean_column_100y_validation",
         "EXPERIMENTAL_RUN_ID_NOT_DECLARED")
    return dict(raw)


def reference_parameters(root: Path, source_record: dict) -> dict:
    authored = _pinned_json(root, REF_PATH, REF_BLOB)
    must(authored["authority_classification"].startswith(
        "AUTHORIAL_SPECIALIST_REFERENCE")
        and source_record["source_model_crust_domain_label"] ==
        "NORMAL_OCEANIC"
        and source_record["source_plate_id"] == 8
        and source_record["source_authored_crustal_thickness_m"] == 6500.0
        and source_record["actual_local_bulk_density_kg_m3"] is None
        and source_record["actual_mineral_phase_field"] is None
        and source_record["actual_ore_resource_field"] is None
        and source_record["actual_Deep_accessibility"] is None,
        "EXPERIMENTAL_T0_MODEL_ANCHOR_NOT_AS_EXPECTED")
    config = authored["thermal_properties"]["oceanic_crust"]
    rho = authored["density"]["oceanic_crust"]
    q = authored["radiogenic_heat"]["oceanic_crust"]
    params = {"rho_kg_m3": rho["nominal"],
              "cp_j_kg_k": config["Cp"]["nominal"],
              "conductivity_w_m_k": config["k"]["nominal"],
              "volumetric_heat_production_w_m3": q["nominal"]}
    for val in params.values():
        must(type(val) in (int, float)
             and math.isfinite(val) and val > 0,
             "EXPERIMENTAL_REFERENCE_PROPERTY_INVALID")
    must(params["rho_kg_m3"] ==
         source_record["reference_crust_density_nominal_kg_m3"],
         "EXPERIMENTAL_REFERENCE_DENSITY_NOT_SOURCE_BOUND")
    must(params["rho_kg_m3"] == 2890
         and params["cp_j_kg_k"] == 1000
         and params["conductivity_w_m_k"] == 2.2
         and params["volumetric_heat_production_w_m3"] == 3e-7,
         "EXPERIMENTAL_REFERENCE_PARAMETER_SOURCE_DRIFT")
    params["provenance"] = (
        "AUTHORIAL_SPECIALIST_REFERENCE_NOT_NATURAL_T0_MEASUREMENT")
    params["material_reference_source_blob"] = REF_BLOB
    return params


def evolve_neumann_cosine(*, n_cells: int, step_years: float,
                          duration_years: int, depth_m: float,
                          reference: dict, base_k: float, amplitude_k: float
                         ) -> dict:
    """Cell-centred conservative finite-volume explicit Euler and analytic check.

    Heat equation rho Cp dT/dt = k d²T/dz² + Q with zero face flux.
    The cosine is an exact continuum Neumann eigenmode, but synthetic.
    """
    must(type(n_cells) is int and n_cells >= 4,
         "EXPERIMENTAL_COLUMN_RESOLUTION_INVALID")
    must(step_years > 0 and math.isfinite(step_years)
         and duration_years > 0,
         "EXPERIMENTAL_TIME_GRID_INVALID")
    steps_float = duration_years / step_years
    steps = round(steps_float)
    must(steps > 0 and abs(steps_float - steps) < 1e-10,
         "EXPERIMENTAL_DURATION_MUST_DIVIDE_TIME_STEP")
    dz = depth_m / n_cells
    t_seconds = duration_years * JULIAN_YEAR_S
    dt = step_years * JULIAN_YEAR_S
    rho = float(reference["rho_kg_m3"])
    cp = float(reference["cp_j_kg_k"])
    k = float(reference["conductivity_w_m_k"])
    q = float(reference["volumetric_heat_production_w_m3"])
    volumetric_capacity = rho * cp
    alpha = k / volumetric_capacity
    cfl = alpha * dt / (dz*dz)
    must(cfl <= 0.5 and cfl > 0,
         "EXPERIMENTAL_EXPLICIT_DIFFUSION_UNSTABLE_CFL")
    z = (np.arange(n_cells, dtype=np.float64) + 0.5) * dz
    initial = base_k + amplitude_k * np.cos(np.pi*z/depth_m)
    t = initial.copy()
    source_step_k = dt*q/volumetric_capacity
    # Reflecting FV boundary: only neighboring face transports heat;
    # fluxes telescope so there is no invented through-boundary energy.
    for _ in range(steps):
        flux_diff = np.zeros_like(t)
        jump = t[1:] - t[:-1]
        flux_diff[:-1] += jump
        flux_diff[1:] -= jump
        t += cfl * flux_diff + source_step_k
    exact = (base_k + amplitude_k*np.exp(
        -alpha*(np.pi/depth_m)**2*t_seconds)
        * np.cos(np.pi*z/depth_m)
        + q*t_seconds/volumetric_capacity)
    e0 = float(np.sum(initial)*dz*volumetric_capacity)
    e1 = float(np.sum(t)*dz*volumetric_capacity)
    injected = q*depth_m*t_seconds
    residual = (e1 - e0) - injected
    energy_tolerance = max(10.0, abs(injected)*1e-4)
    return {
      "n_cells": n_cells, "depth_resolution_m": dz,
      "step_years": step_years, "time_steps": steps,
      "diffusive_cfl": cfl,
      "thermal_diffusivity_m2_s_reference": alpha,
      "max_abs_error_against_synthetic_exact_k": float(
          np.max(np.abs(t-exact))),
      "mean_temperature_initial_k": float(np.mean(initial)),
      "mean_temperature_final_k": float(np.mean(t)),
      "temperature_min_final_k": float(t.min()),
      "temperature_max_final_k": float(t.max()),
      "column_energy_initial_j_m2": e0,
      "column_energy_final_j_m2": e1,
      "reference_volumetric_heat_added_j_m2": injected,
      "closed_column_boundary_energy_j_m2": 0.0,
      "energy_balance_residual_j_m2": residual,
      "energy_balance_tolerance_j_m2": energy_tolerance,
      "energy_balance_pass": abs(residual) <= energy_tolerance,
      "temperature_k_sampled_cell_centres": [
          {"z_m": float(z[j]), "synthetic_temperature_k": float(t[j])}
          for j in sorted({0, n_cells//4, n_cells//2,
                           3*n_cells//4, n_cells-1})],
      "initial_profile_authority": "SYNTHETIC_COSINE",
      "boundary_authority": "SYNTHETIC_INSULATED",
      "physical_historical_T1": None,
    }


def run(root: Path, config: dict, *,
        field_package: Path | None = None,
        plate_partition: Path | None = None) -> dict:
    root = Path(root).resolve()
    gov = governance(root)
    conf = validate_config(config)
    source = extract_original_t0(
        root, [conf["source_parent_cell_id"]],
        field_package=field_package, plate_partition=plate_partition)
    must(source["selected_cell_count"] == 1
         and source["physical_T1"] is None
         and source["history_store_writes"] == 0,
         "EXPERIMENTAL_SOURCE_ADAPTER_NOT_READ_ONLY")
    anchor = source["native_cell_source_records"][0]
    pars = reference_parameters(root, anchor)
    depth = float(conf["synthetic_column_depth_m"])
    must(depth < anchor["source_authored_crustal_thickness_m"],
         "EXPERIMENTAL_REFERENCE_COLUMN_EXCEEDS_SOURCE_CRUST")
    conditions = conf["initial_temperature_k"]
    outcomes = [
        evolve_neumann_cosine(
            n_cells=n, step_years=step,
            duration_years=100, depth_m=depth,
            reference=pars, base_k=float(conditions["base_k"]),
            amplitude_k=float(conditions["cosine_amplitude_k"]))
        for n,step in LEVELS]
    errors = [x["max_abs_error_against_synthetic_exact_k"]
              for x in outcomes]
    convergence_ok = (
        all(x["energy_balance_pass"] for x in outcomes)
        and all(0 < x["diffusive_cfl"] <= 0.5 for x in outcomes)
        and errors[2] < errors[1] < errors[0]
        and errors[2] < 0.001)
    must(convergence_ok,
         "EXPERIMENTAL_100Y_THERMAL_CONVERGENCE_OR_ENERGY_CHECK_FAILED")
    return {
      "schema": REPORT_SCHEMA,
      "decision":
          "EXPERIMENTAL_NONCANONICAL_100Y_CONSERVATIVE_THERMAL_BENCHMARK_PASS",
      "run_config_sha256": content_hash(conf),
      "governance_policy_git_blob": POLICY_BLOB,
      "authority": AUTHORITY,
      "source_original_T0_cell": anchor["parent_cell_id"],
      "source_plate_id": anchor["source_plate_id"],
      "source_model_crust_domain": anchor["source_model_crust_domain_label"],
      "source_model_crust_thickness_m":
          anchor["source_authored_crustal_thickness_m"],
      "source_field_sha256": source["source_field_package_sha256"],
      "source_plate_sha256": source["source_vector_partition_sha256"],
      "source_model_reference_coefficients": pars,
      "initial_condition":
          "DECLARED_SYNTHETIC_COSINE_NOT_ARCANA_T0_THERMAL_PROFILE",
      "boundary_condition":
          "DECLARED_SYNTHETIC_ZERO_HEAT_FLUX_BOTH_ENDS",
      "reference_heat_production_is_not_cellwise_natural": True,
      "requested_duration_years": 100,
      "experimental_end_time_relative_years": 100,
      "numerical_method": "EXPLICIT_FV_CELL_CENTERED_1D_DIFFUSION",
      "analytical_benchmark": "INSULATED_COSINE_DECAY_PLUS_UNIFORM_HEATING",
      "convergence_levels": outcomes,
      "convergence_error_strictly_decreases": True,
      "all_energy_balances_pass": True,
      "synthetic_numerical_run_executed": True,
      "natural_ARCANA_T0_temperature_profile_qualified": False,
      "natural_ARCANA_T1_temperature_profile_created": False,
      "simulator_complete": False,
      "automatically_canonicalizable": False,
      "world_history_production_authorized": False,
      "history_store_mutations": 0,
      "actual_mineral_or_ore_or_Deep_assignments": 0,
      "D_024": "ACTIVE",
      "physical_T1": None,
    }


def write_once(out: Path, result: dict, *, repository_root: Path):
    # Even operator-selected evidence must stay OUTSIDE the source repository.
    # This prevents accidentally writing the experimental report into a
    # canonical WorldSim working tree or an in-repo history directory.
    must(not out.resolve().is_relative_to(Path(repository_root).resolve()),
         "EXPERIMENTAL_EVIDENCE_MUST_BE_OUTSIDE_REPOSITORY")
    must(not out.exists(), "EXPERIMENTAL_EVIDENCE_ALREADY_EXISTS")
    out.mkdir(parents=True, exist_ok=False)
    payload = (json.dumps(result, indent=2, allow_nan=False,
                          ensure_ascii=False)+"\n").encode("utf-8")
    (out/"REPORT.json").write_bytes(payload)
    (out/"MANIFEST.json").write_text(json.dumps({
        "schema": "ARCANA_R6_THERMAL_COLUMN_EXPERIMENT_EVIDENCE_V1",
        "report_sha256": hashlib.sha256(payload).hexdigest(),
        "governance_policy_git_blob": POLICY_BLOB,
        "authority": AUTHORITY,
        "no_history_store_writes": True,
        "world_history_production_authorized": False,
        "physical_T1": None,
    }, indent=2)+"\n")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--repo-root", type=Path,
                     default=Path(__file__).resolve().parents[3])
    cli.add_argument("--config", type=Path, required=True)
    cli.add_argument("--field-package", type=Path)
    cli.add_argument("--plate-partition", type=Path)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    result = run(args.repo_root, json.loads(
        args.config.read_text(encoding="utf-8")),
        field_package=args.field_package,
        plate_partition=args.plate_partition)
    write_once(args.output, result, repository_root=args.repo_root)
    print(json.dumps({
       "decision":result["decision"],
       "synthetic_numerical_run_executed":True,
       "duration_years":100,
       "convergence_errors_k":[x["max_abs_error_against_synthetic_exact_k"]
                               for x in result["convergence_levels"]],
       "energy_balance_pass":result["all_energy_balances_pass"],
       "canonical_history_created":False,
       "physical_T1":None}))


if __name__ == "__main__":
    main()
