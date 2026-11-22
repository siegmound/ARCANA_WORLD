"""Negative authority, numerical, and source-contract tests for 1000y experiment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from arcana_worldsim.r6 import experimental_thermal_column as old
from arcana_worldsim.r6 import experimental_thermal_column_1000y as m

ROOT = Path(__file__).resolve().parents[1]
CONFIG = (ROOT / "experiments/thermal_column_1000y_v1"
          / "SYNTHETIC_OCEANIC_REFERENCE_COLUMN.json")


def config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def material():
    return {
        "rho_kg_m3": 2890.,
        "cp_j_kg_k": 1000.,
        "conductivity_w_m_k": 2.2,
        "volumetric_heat_production_w_m3": 3e-7,
        "provenance": "AUTHORIAL_SPECIALIST_REFERENCE_NOT_NATURAL_T0_MEASUREMENT",
        "material_reference_source_blob": old.REF_BLOB,
    }


def synthetic_100y_oracle(root, cfg, **kwargs):
    assert cfg["requested_duration_years"] == 100
    return {
        "physical_T1": None,
        "history_store_mutations": 0,
        "world_history_production_authorized": False,
        "source_plate_id": 8,
        "source_original_T0_cell": "R6G1D-R089-C359",
        "source_field_sha256":
            "39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e",
        "source_plate_sha256":
            "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab",
        "source_model_reference_coefficients": material(),
        "decision":
            "EXPERIMENTAL_NONCANONICAL_100Y_CONSERVATIVE_THERMAL_BENCHMARK_PASS",
        "convergence_levels": [
            old.evolve_neumann_cosine(
                n_cells=n, step_years=dt, duration_years=100,
                depth_m=1000., reference=material(), base_k=300.,
                amplitude_k=15.)
            for n,dt in old.LEVELS],
    }


def test_governance_remains_pinned_and_noncanonical():
    gov = old.governance(ROOT)
    assert gov["horizons_longer_than_100_years_require_separate_qualification"]
    assert gov["automatic_promotion_after_simulator_completion"] is False
    assert gov["physical_T1"] is None


def test_new_study_configuration_is_exactly_1000y_and_separate():
    cfg = m.validate_config(config())
    assert cfg["requested_duration_years"] == 1000
    assert cfg["baseline_100y_config_git_blob"] == m.BASELINE_CONFIG_BLOB
    assert m.BASELINE_CONFIG_BLOB == (
        old._gitblob((ROOT/m.BASELINE_CONFIG).read_bytes()))


@pytest.mark.parametrize("field,value,code", [
    ("authority", "CANONICAL", "AUTHORITY_INVALID"),
    ("requested_duration_years", 100, "SCOPE_INVALID"),
    ("requested_duration_years", 1000.0, "SCOPE_INVALID"),
    ("source_parent_cell_id", "R6G1D-R089-C358", "SCOPE_INVALID"),
    ("synthetic_column_depth_m", 7000, "SCOPE_INVALID"),
    ("baseline_100y_config_git_blob", "0"*40, "STUDY_NOT_DECLARED"),
    ("boundary_sensitivity_mode", "PHYSICAL_T0", "STUDY_NOT_DECLARED"),
    ("reference_parameter_sensitivity_mode", "SAMPLED_NATURAL",
     "STUDY_NOT_DECLARED"),
    ("experimental_run_label", "physical_t1", "STUDY_NOT_DECLARED"),
])
def test_invalid_study_refuses_unsupported_physics(field, value, code):
    cfg = config()
    cfg[field] = value
    with pytest.raises(old.ExperimentalColumnError, match=code):
        m.validate_config(cfg)


def test_canonical_field_injection_is_rejected():
    cfg = config()
    cfg["canonical_T1"] = True
    with pytest.raises(old.ExperimentalColumnError, match="CONFIG_FIELDS_INVALID"):
        m.validate_config(cfg)


def test_real_pinned_reference_ranges_only():
    ranges = m.reference_ranges(ROOT, material())
    assert ranges == {
        "rho_kg_m3": [2850., 2930.],
        "cp_j_kg_k": [800., 1200.],
        "conductivity_w_m_k": [1.8, 2.8],
        "volumetric_heat_production_w_m3": [0., 5e-7],
    }


def test_bad_reference_nominal_refused():
    wrong = material()
    wrong["rho_kg_m3"] = 3000.
    with pytest.raises(old.ExperimentalColumnError, match="REFERENCE_RANGE_DRIFT"):
        m.reference_ranges(ROOT, wrong)


@pytest.mark.parametrize("n,dt", old.LEVELS)
def test_1000y_insulated_conservative_analytic(n, dt):
    r = old.evolve_neumann_cosine(
        n_cells=n, step_years=dt, duration_years=1000,
        depth_m=1000., reference=material(),
        base_k=300., amplitude_k=15.)
    assert r["time_steps"] == int(1000/dt)
    assert r["energy_balance_pass"]
    assert abs(r["energy_balance_residual_j_m2"]) < 1
    assert r["max_abs_error_against_synthetic_exact_k"] < 0.001
    assert r["physical_historical_T1"] is None


@pytest.mark.parametrize("n,dt", old.LEVELS)
def test_1000y_dirichlet_manufactured_exact_and_energy(n, dt):
    r = m.dirichlet_fv(
        n_cells=n, step_years=dt, years=1000,
        material=material(), manufactured=True)
    assert r["energy_balance_pass"]
    assert abs(r["energy_balance_residual_j_m2"]) <= 1
    assert r["max_abs_error_against_synthetic_exact_k"] < 0.001
    assert r["physical_T1"] is None


def test_dirichlet_analytic_convergence_ratios_are_second_order():
    rr = [m.dirichlet_fv(
        n_cells=n, step_years=dt, years=1000,
        material=material(), manufactured=True)
        for n, dt in old.LEVELS]
    e = [r["max_abs_error_against_synthetic_exact_k"] for r in rr]
    assert e[2] < e[1] < e[0]
    assert 3 < e[0]/e[1] < 5
    assert 3 < e[1]/e[2] < 5


def test_matched_initial_dirichlet_has_no_fake_exact_claim():
    r = m.dirichlet_fv(
        n_cells=100, step_years=0.25, years=1000,
        material=material(), manufactured=False)
    assert r["max_abs_error_against_synthetic_exact_k"] is None
    assert r["energy_balance_pass"]
    assert r["physical_T1"] is None


def test_unstable_dirichlet_grid_is_rejected():
    with pytest.raises(old.ExperimentalColumnError, match="UNSTABLE_CFL"):
        m.dirichlet_fv(n_cells=200, step_years=20, years=1000,
                       material=material(), manufactured=True)


def test_time_grid_and_negative_heat_rejected():
    with pytest.raises(old.ExperimentalColumnError, match="TIME_GRID_INVALID"):
        m.dirichlet_fv(n_cells=50, step_years=3, years=1000,
                       material=material(), manufactured=True)
    bad = material()
    bad["volumetric_heat_production_w_m3"] = -1
    with pytest.raises(old.ExperimentalColumnError, match="MATERIAL_INVALID"):
        m.dirichlet_fv(n_cells=50, step_years=1, years=1000,
                       material=bad, manufactured=True)


def test_full_noncanonical_study_with_existing_100y_oracle(monkeypatch):
    monkeypatch.setattr(old, "run", synthetic_100y_oracle)
    result = m.run(ROOT, config())
    assert result["numerical_study_executed"] is True
    assert result["requested_duration_years"] == 1000
    assert result["source_plate_id"] == 8
    assert len(result["one_factor_reference_sensitivities"]) == 8
    assert len(result["insulated_1000y_convergence_levels"]) == 3
    assert len(result["fixed_temperature_1000y_manufactured_levels"]) == 3
    assert (result["fixed_vs_insulated_max_abs_difference_at_five_sampled_centres_k"]
            > 0)
    assert result["canonical_history_created"] is False
    assert result["automatic_promotion_authorized"] is False
    assert result["history_store_mutations"] == 0
    assert result["physical_T1"] is None
    assert result == m.run(ROOT, config())


def test_rejects_100y_oracle_fabricating_physical_t1(monkeypatch):
    def false_oracle(*args, **kwargs):
        r = synthetic_100y_oracle(*args, **kwargs)
        r["physical_T1"] = {"temperature": 1}
        return r
    monkeypatch.setattr(old, "run", false_oracle)
    with pytest.raises(old.ExperimentalColumnError,
                       match="SOURCE_ORACLE_INVALID"):
        m.run(ROOT, config())


def test_write_once_sha_and_no_overwrite(monkeypatch, tmp_path):
    monkeypatch.setattr(old, "run", synthetic_100y_oracle)
    report = m.run(ROOT, config())
    out = tmp_path/"r6_1000y"
    m.write_once(out, report, repository_root=ROOT)
    raw = (out/"REPORT.json").read_bytes()
    manifest = json.loads((out/"MANIFEST.json").read_text())
    assert manifest["report_sha256"] == hashlib.sha256(raw).hexdigest()
    assert manifest["authority"] == old.AUTHORITY
    assert manifest["physical_T1"] is None
    with pytest.raises(old.ExperimentalColumnError,match="ALREADY_EXISTS"):
        m.write_once(out, report, repository_root=ROOT)


def test_no_repository_writes_even_when_output_path_is_new():
    out = ROOT/"PROJECT_LEDGER"/"ILLEGAL_1000Y_EXPERIMENT"
    with pytest.raises(old.ExperimentalColumnError,
                       match="OUTSIDE_REPOSITORY"):
        m.write_once(out, {"physical_T1": None}, repository_root=ROOT)


def test_write_once_rejects_canonicalization(monkeypatch, tmp_path):
    monkeypatch.setattr(old, "run", synthetic_100y_oracle)
    report = m.run(ROOT, config())
    report["canonical_history_created"] = True
    with pytest.raises(old.ExperimentalColumnError,
                       match="REPORT_GOVERNANCE_INVALID"):
        m.write_once(tmp_path/"forbidden", report, repository_root=ROOT)


def test_original_100y_pilot_still_rejects_1000y_extension():
    previous = json.loads((ROOT/m.BASELINE_CONFIG).read_text(encoding="utf-8"))
    previous["requested_duration_years"] = 1000
    with pytest.raises(old.ExperimentalColumnError,
                       match="EXPERIMENTAL_100Y_ONLY_1000Y_NOT_YET_QUALIFIED"):
        old.validate_config(previous)
