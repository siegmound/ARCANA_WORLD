"""1000-year synthetic thermal-column validation, permanently noncanonical.

Independent experiment: uses the immutable 100-year pilot as an oracle and
source-authenticated T0 model geometry, but never mutates that experiment,
HistoryStore, physical T1, mineralogy, Deep or canonical WORLD_HISTORY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from . import experimental_thermal_column as old
from .identity import content_hash

SCHEMA = "ARCANA_R6_EXPERIMENTAL_1000Y_THERMAL_COLUMN_CONFIG_V1"
REPORT_SCHEMA = "ARCANA_R6_EXPERIMENTAL_NONCANONICAL_1000Y_COLUMN_REPORT_V1"
AUTHORITY = old.AUTHORITY
BASELINE_CONFIG = "experiments/thermal_column_100y_v1/SYNTHETIC_OCEANIC_REFERENCE_COLUMN.json"
BASELINE_CONFIG_BLOB = "ea1355175145894edf8a8e24268bf843b9368bdf"
LEVELS = old.LEVELS


def require(ok: bool, code: str) -> None:
    old.must(bool(ok), code)


def validate_config(cfg: dict) -> dict:
    require(type(cfg) is dict and set(cfg) == {
        "schema", "authority", "source_parent_cell_id", "requested_duration_years",
        "synthetic_column_depth_m", "baseline_100y_config_git_blob",
        "boundary_sensitivity_mode", "reference_parameter_sensitivity_mode",
        "experimental_run_label",
    }, "EXPERIMENTAL_1000Y_CONFIG_FIELDS_INVALID")
    require(cfg["schema"] == SCHEMA and cfg["authority"] == AUTHORITY,
            "EXPERIMENTAL_1000Y_AUTHORITY_INVALID")
    require(cfg["source_parent_cell_id"] == "R6G1D-R089-C359"
            and type(cfg["requested_duration_years"]) is int
            and cfg["requested_duration_years"] == 1000
            and type(cfg["synthetic_column_depth_m"]) in (int, float)
            and math.isfinite(cfg["synthetic_column_depth_m"])
            and cfg["synthetic_column_depth_m"] == 1000,
            "EXPERIMENTAL_1000Y_SCOPE_INVALID")
    require(cfg["baseline_100y_config_git_blob"] == BASELINE_CONFIG_BLOB
            and cfg["boundary_sensitivity_mode"] ==
                "MATCHED_COSINE_INITIAL_PROFILE_PLUS_DIRICHLET_ANALYTIC"
            and cfg["reference_parameter_sensitivity_mode"] ==
                "ONE_FACTOR_AT_A_TIME_SOURCE_PINNED_ENDPOINTS"
            and cfg["experimental_run_label"] ==
                "synthetic_ocean_column_1000y_validation",
            "EXPERIMENTAL_1000Y_STUDY_NOT_DECLARED")
    return dict(cfg)


def reference_ranges(root: Path, nominal: dict) -> dict:
    """Only declared authored reference ranges, not observed ARCANA variability."""
    source = old._pinned_json(root, old.REF_PATH, old.REF_BLOB)
    options = {
        "rho_kg_m3": source["density"]["oceanic_crust"],
        "cp_j_kg_k": source["thermal_properties"]["oceanic_crust"]["Cp"],
        "conductivity_w_m_k": source["thermal_properties"]["oceanic_crust"]["k"],
        "volumetric_heat_production_w_m3": source["radiogenic_heat"]["oceanic_crust"],
    }
    bounds = {}
    for name, record in options.items():
        values = record["sensitivity_range"]
        require(type(values) is list and len(values) == 2
                and all(type(v) in (int, float) and math.isfinite(v) and v >= 0
                        for v in values)
                and float(values[0]) < float(values[1])
                and float(values[0]) <= nominal[name] <= float(values[1])
                and record["nominal"] == nominal[name],
                "EXPERIMENTAL_1000Y_REFERENCE_RANGE_DRIFT")
        bounds[name] = [float(values[0]), float(values[1])]
    return bounds


def dirichlet_fv(*, n_cells: int, step_years: float, years: int,
                 material: dict, manufactured: bool) -> dict:
    """Explicit FV: fixed top/bottom temperatures and exact flux accounting.

    Manufactured case: steady parabola + decaying first sine eigenmode.
    Matched case: same initial cosine as insulated pilot; no analytic
    solution is claimed for that different initial-boundary-value problem.
    """
    require(type(n_cells) is int and n_cells >= 4
            and years == 1000 and step_years > 0
            and math.isfinite(step_years), "EXPERIMENTAL_DIRICHLET_GRID_INVALID")
    steps = round(years / step_years)
    require(steps > 0 and abs(steps * step_years - years) < 1e-9,
            "EXPERIMENTAL_DIRICHLET_TIME_GRID_INVALID")
    L = 1000.0
    dz = L / n_cells
    dt_s = step_years * old.JULIAN_YEAR_S
    elapsed_s = years * old.JULIAN_YEAR_S
    rho, cp, k, q = (float(material[key]) for key in
                    ("rho_kg_m3", "cp_j_kg_k", "conductivity_w_m_k",
                     "volumetric_heat_production_w_m3"))
    require(all(math.isfinite(v) and v > 0 for v in (rho, cp, k))
            and math.isfinite(q) and q >= 0,
            "EXPERIMENTAL_DIRICHLET_MATERIAL_INVALID")
    c = rho * cp
    alpha = k / c
    cfl = alpha * dt_s / (dz * dz)
    require(0 < cfl <= 0.5, "EXPERIMENTAL_DIRICHLET_UNSTABLE_CFL")
    top, bottom = 315.0, 285.0
    z = (np.arange(n_cells, dtype=np.float64) + 0.5) * dz
    stationary = (top + (bottom - top) * z/L
                  + q * z * (L-z) / (2*k))
    if manufactured:
        initial = stationary + 8.0 * np.sin(np.pi*z/L)
        exact = (stationary + 8.0 * np.sin(np.pi*z/L)
                 * math.exp(-alpha * (np.pi/L)**2 * elapsed_s))
    else:
        initial = 300.0 + 15.0 * np.cos(np.pi*z/L)
        exact = None
    temperature = initial.copy()
    boundary_energy = 0.0
    for _ in range(steps):
        jumps = temperature[1:] - temperature[:-1]
        f = np.zeros_like(temperature)
        f[:-1] += jumps
        f[1:] -= jumps
        # Boundary face distance is half a cell; flux into the column is
        # positive. Sum with volume heating for the integral balance.
        face_flux = (2*k/dz) * (
            (top - temperature[0]) + (bottom - temperature[-1]))
        boundary_energy += dt_s * face_flux
        f[0] += 2.0 * (top - temperature[0])
        f[-1] += 2.0 * (bottom - temperature[-1])
        temperature += cfl * f + dt_s*q/c
    e0 = float(np.sum(initial) * dz * c)
    e1 = float(np.sum(temperature) * dz * c)
    source_energy = q * L * elapsed_s
    # The boundary-flux accumulator has NumPy scalar type after the first
    # update. Explicitly normalize the report scalars rather than weakening
    # JSON strictness or installing a serializer that silently coerces data.
    boundary_energy = float(boundary_energy)
    residual = float((e1-e0) - (source_energy+boundary_energy))
    error = None if exact is None else float(np.max(np.abs(temperature-exact)))
    return {
        "n_cells": n_cells, "step_years": step_years, "time_steps": steps,
        "cfl": cfl, "initial_profile": (
            "SYNTHETIC_DIRICHLET_STEADY_PLUS_SINE"
            if manufactured else "SYNTHETIC_COSINE_MATCHED_TO_INSULATED_CASE"),
        "fixed_top_k": top, "fixed_bottom_k": bottom,
        "max_abs_error_against_synthetic_exact_k": error,
        "energy_initial_j_m2": e0, "energy_final_j_m2": e1,
        "volumetric_source_energy_j_m2": source_energy,
        "boundary_heat_into_column_j_m2": boundary_energy,
        "energy_balance_residual_j_m2": residual,
        "energy_balance_pass": bool(abs(residual) <= 1.0),
        "mean_final_temperature_k": float(np.mean(temperature)),
        "temperature_k_five_sampled_centres": [
            {"z_m": float(z[j]), "synthetic_temperature_k": float(temperature[j])}
            for j in sorted({0, n_cells//4, n_cells//2,
                             3*n_cells//4, n_cells-1})],
        "physical_T1": None,
    }


def run(root: Path, config: dict, *, field_package: Path | None = None,
        plate_partition: Path | None = None) -> dict:
    root = Path(root).resolve()
    cfg = validate_config(config)
    policy = old.governance(root)
    require(policy["horizons_longer_than_100_years_require_separate_qualification"]
            is True, "EXPERIMENTAL_LONG_HORIZON_GOVERNANCE_CHANGED")
    old_cfg = old._pinned_json(root, BASELINE_CONFIG, BASELINE_CONFIG_BLOB)
    # Re-run the unchanged, independently authenticated 100y source-anchored
    # oracle in memory; no evidence is overwritten or published.
    baseline_100 = old.run(
        root, old_cfg, field_package=field_package,
        plate_partition=plate_partition)
    require(baseline_100["physical_T1"] is None
            and baseline_100["history_store_mutations"] == 0
            and baseline_100["world_history_production_authorized"] is False
            and baseline_100["source_plate_id"] == 8,
            "EXPERIMENTAL_100Y_SOURCE_ORACLE_INVALID")
    material = baseline_100["source_model_reference_coefficients"]
    bounds = reference_ranges(root, material)
    outcomes = [
        old.evolve_neumann_cosine(
            n_cells=n, step_years=step, duration_years=1000,
            depth_m=1000.0, reference=material, base_k=300.0,
            amplitude_k=15.0)
        for n, step in LEVELS]
    errors = [r["max_abs_error_against_synthetic_exact_k"] for r in outcomes]
    require(errors[2] < errors[1] < errors[0]
            and errors[2] < 0.001
            and all(r["energy_balance_pass"]
                    and abs(r["energy_balance_residual_j_m2"]) < 1
                    and r["physical_historical_T1"] is None for r in outcomes),
            "EXPERIMENTAL_1000Y_BASELINE_CONVERGENCE_OR_ENERGY_FAILED")
    # One-at-a-time sensitivity: declared range endpoints, not mineral
    # uncertainty posteriors or estimates of the actual planet.
    nominal = outcomes[1]
    sensitivity = []
    for name, (lo, hi) in bounds.items():
        for label, val in (("low", lo), ("high", hi)):
            alternative = dict(material)
            alternative[name] = val
            result = old.evolve_neumann_cosine(
                n_cells=100, step_years=0.25, duration_years=1000,
                depth_m=1000.0, reference=alternative,
                base_k=300.0, amplitude_k=15.0)
            require(result["energy_balance_pass"]
                    and abs(result["energy_balance_residual_j_m2"]) < 1,
                    "EXPERIMENTAL_1000Y_SENSITIVITY_ENERGY_FAILED")
            values = result["temperature_k_sampled_cell_centres"]
            nv = nominal["temperature_k_sampled_cell_centres"]
            require([p["z_m"] for p in values] == [p["z_m"] for p in nv],
                    "EXPERIMENTAL_1000Y_SENSITIVITY_GRID_CHANGED")
            sensitivity.append({
                "varied_parameter": name, "endpoint": label, "value": val,
                "source": "PINNED_AUTHORIAL_REFERENCE_SENSITIVITY_RANGE",
                "mean_temperature_shift_from_nominal_k":
                    result["mean_temperature_final_k"] -
                    nominal["mean_temperature_final_k"],
                "max_abs_shift_at_five_sampled_centres_k":
                    max(abs(a["synthetic_temperature_k"] -
                            b["synthetic_temperature_k"])
                        for a,b in zip(values,nv)),
                "energy_balance_residual_j_m2":
                    result["energy_balance_residual_j_m2"],
                "physical_T1": None,
            })
    manufactured = [
        dirichlet_fv(n_cells=n, step_years=dt, years=1000,
                     material=material, manufactured=True)
        for n, dt in LEVELS]
    dir_errors = [x["max_abs_error_against_synthetic_exact_k"]
                  for x in manufactured]
    require(dir_errors[2] < dir_errors[1] < dir_errors[0]
            and dir_errors[2] < 0.001
            and all(x["energy_balance_pass"] for x in manufactured),
            "EXPERIMENTAL_1000Y_DIRICHLET_MANUFACTURED_FAILED")
    matched = dirichlet_fv(
        n_cells=200, step_years=0.0625, years=1000,
        material=material, manufactured=False)
    require(matched["energy_balance_pass"]
            and matched["max_abs_error_against_synthetic_exact_k"] is None,
            "EXPERIMENTAL_1000Y_MATCHED_BOUNDARY_ENERGY_FAILED")
    baseline_samples = outcomes[2]["temperature_k_sampled_cell_centres"]
    fixed_samples = matched["temperature_k_five_sampled_centres"]
    require([v["z_m"] for v in baseline_samples] ==
            [v["z_m"] for v in fixed_samples],
            "EXPERIMENTAL_1000Y_BOUNDARY_GRIDS_DIFFER")
    boundary_delta = max(
        abs(a["synthetic_temperature_k"]-b["synthetic_temperature_k"])
        for a,b in zip(baseline_samples, fixed_samples))
    require(math.isfinite(boundary_delta) and boundary_delta > 1e-8,
            "EXPERIMENTAL_1000Y_BOUNDARY_COMPARISON_NOT_MEANINGFUL")
    return {
        "schema": REPORT_SCHEMA,
        "decision": "EXPERIMENTAL_NONCANONICAL_1000Y_THERMAL_STUDY_NUMERICAL_PASS",
        "authority": AUTHORITY, "config_sha256": content_hash(cfg),
        "original_100y_config_git_blob": BASELINE_CONFIG_BLOB,
        "governance_policy_git_blob": old.POLICY_BLOB,
        "source_original_T0_cell": baseline_100["source_original_T0_cell"],
        "source_plate_id": 8,
        "source_field_sha256": baseline_100["source_field_sha256"],
        "source_plate_sha256": baseline_100["source_plate_sha256"],
        "source_material_reference_git_blob": old.REF_BLOB,
        "nominal_reference_coefficients": material,
        "reference_sensitivity_ranges": bounds,
        "source_material_is_not_natural_T0_measurement": True,
        "initial_temperature_is_synthetic": True,
        "baseline_100y": {
            "decision": baseline_100["decision"],
            "numerical_errors_k": [
                r["max_abs_error_against_synthetic_exact_k"]
                for r in baseline_100["convergence_levels"]],
        },
        "requested_duration_years": 1000,
        "insulated_1000y_convergence_levels": outcomes,
        "insulated_1000y_numerical_errors_k": errors,
        "one_factor_reference_sensitivities": sensitivity,
        "fixed_temperature_1000y_manufactured_levels": manufactured,
        "fixed_temperature_1000y_manufactured_errors_k": dir_errors,
        "fixed_temperature_1000y_matched_initial_state": matched,
        "fixed_vs_insulated_max_abs_difference_at_five_sampled_centres_k":
            boundary_delta,
        "fixed_vs_insulated_difference_is_not_historical_prediction": True,
        "numerical_study_executed": True,
        "world_history_production_authorized": False,
        "natural_T0_temperature_qualified": False,
        "canonical_history_created": False,
        "automatic_promotion_authorized": False,
        "actual_rock_mineral_ore_or_Deep_assignments": 0,
        "history_store_mutations": 0,
        "D_024": "ACTIVE",
        "physical_T1": None,
    }


def write_once(output: Path, result: dict, *, repository_root: Path) -> None:
    require(not output.resolve().is_relative_to(repository_root.resolve()),
            "EXPERIMENTAL_1000Y_EVIDENCE_MUST_BE_OUTSIDE_REPOSITORY")
    require(not output.exists(), "EXPERIMENTAL_1000Y_EVIDENCE_ALREADY_EXISTS")
    require(result["authority"] == AUTHORITY
            and result["physical_T1"] is None
            and result["history_store_mutations"] == 0
            and result["canonical_history_created"] is False
            and result["world_history_production_authorized"] is False,
            "EXPERIMENTAL_1000Y_REPORT_GOVERNANCE_INVALID")
    payload = (json.dumps(result, indent=2, allow_nan=False,
                          ensure_ascii=False) + "\n").encode("utf-8")
    output.mkdir(parents=True, exist_ok=False)
    (output/"REPORT.json").write_bytes(payload)
    (output/"MANIFEST.json").write_text(json.dumps({
        "schema": "ARCANA_R6_THERMAL_COLUMN_1000Y_EXPERIMENT_EVIDENCE_V1",
        "report_sha256": hashlib.sha256(payload).hexdigest(),
        "authority": AUTHORITY, "physical_T1": None,
        "no_history_store_writes": True,
        "world_history_production_authorized": False,
        "governance_policy_git_blob": old.POLICY_BLOB,
    }, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[3])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--field-package", type=Path)
    parser.add_argument("--plate-partition", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.repo_root,
                 json.loads(args.config.read_text(encoding="utf-8")),
                 field_package=args.field_package,
                 plate_partition=args.plate_partition)
    write_once(args.output, result, repository_root=args.repo_root)
    print(json.dumps({
        "decision": result["decision"],
        "source_original_T0_cell": result["source_original_T0_cell"],
        "duration_years": 1000,
        "baseline_errors_k": result["insulated_1000y_numerical_errors_k"],
        "fixed_boundary_errors_k":
            result["fixed_temperature_1000y_manufactured_errors_k"],
        "boundary_sensitivity_sampled_max_k":
            result["fixed_vs_insulated_max_abs_difference_at_five_sampled_centres_k"],
        "reference_sensitivity_runs":
            len(result["one_factor_reference_sensitivities"]),
        "canonical_history_created": False,
        "physical_T1": None,
    }))


if __name__ == "__main__":
    main()
