from __future__ import annotations

import math

import pytest

from arcana_worldsim.r6.material_rheology_provider import (
    DEFAULT_BENCHMARK, evaluate_dislocation_creep, evaluate_reduced_state_column,
)
from arcana_worldsim.r6.constitutive_mechanics_microdomain import (
    DEFAULT_CONSTITUTIVE_CONFIG, solve_layered_interface_increment,
)
from test_r6_constitutive_mechanics_microdomain import _columns


def test_dry_olivine_benchmark_viscosity_responds_to_temperature_and_strain_rate():
    base = evaluate_dislocation_creep(temperature_k=1000.0, strain_rate_s=5e-15,
                                      pressure_pa=1e9)
    hot = evaluate_dislocation_creep(temperature_k=1100.0, strain_rate_s=5e-15,
                                     pressure_pa=1e9)
    faster = evaluate_dislocation_creep(temperature_k=1000.0, strain_rate_s=5e-14,
                                        pressure_pa=1e9)
    assert hot["effective_shear_viscosity_pa_s"] < base["effective_shear_viscosity_pa_s"]
    assert faster["effective_shear_viscosity_pa_s"] < base["effective_shear_viscosity_pa_s"]
    assert base["maxwell_relaxation_time_s"] == pytest.approx(
        base["effective_shear_viscosity_pa_s"] / DEFAULT_BENCHMARK.shear_modulus_pa)
    assert base["equivalent_1d_maxwell_viscosity_pa_s"] / base["young_modulus_pa"] == pytest.approx(
        base["maxwell_relaxation_time_s"])


def test_adapter_uses_r6_node_temperature_density_depth_without_role_mineralogy():
    state, cells_a, _ = _columns()
    profile = evaluate_reduced_state_column(
        state, cells_a, support_id="R6G1D-R091-C028", strain_rate_s=5e-15)
    assert profile["node_count"] == 73
    assert profile["material_role_to_mineralogy"].startswith("UNKNOWN")
    assert profile["pressure_method"].startswith("rho_kg_m3")
    assert profile["nodes"][0]["r6_temperature_k"] == state.temperature_k[0]
    assert profile["nodes"][0]["r6_density_kg_m3"] == state.materials[0].rho_kg_m3
    assert profile["nodes"][0]["pressure_proxy_pa"] == 0.0
    assert profile["nodes"][-1]["pressure_proxy_pa"] > 0
    assert set(profile["young_modulus_pa_by_cell"]) == {row["cell_id"] for row in cells_a}
    assert all(value == pytest.approx(75e9) for value in profile["young_modulus_pa_by_cell"].values())


def test_adapter_rejects_cell_mapping_mismatch_and_invalid_inputs():
    state, cells_a, _ = _columns()
    wrong = [dict(row) for row in cells_a]
    wrong[0]["node_index_zero_based"] = 1
    with pytest.raises(ValueError, match="CELL_TO_R6_MATERIAL"):
        evaluate_reduced_state_column(state, wrong, support_id="R6G1D-R091-C028",
                                      strain_rate_s=5e-15)
    with pytest.raises(ValueError, match="OUT_OF_DOMAIN"):
        evaluate_dislocation_creep(temperature_k=0.0, strain_rate_s=5e-15,
                                   pressure_pa=1e9)
    with pytest.raises(ValueError, match="NONFINITE"):
        evaluate_dislocation_creep(temperature_k=1000.0, strain_rate_s=math.nan,
                                   pressure_pa=1e9)


def test_provider_cell_properties_change_mechanical_response_and_balance_energy():
    state, cells_a, cells_b = _columns()
    profiles = [evaluate_reduced_state_column(
        state, cells, support_id=support, strain_rate_s=5e-15)
        for support, cells in (("R6G1D-R091-C028", cells_a), ("R6G1D-R091-C029", cells_b))]
    young_by_cell = {key: value for profile in profiles
                     for key, value in profile["young_modulus_pa_by_cell"].items()}
    eta_by_cell = {key: value for profile in profiles
                   for key, value in profile["eta_1d_pa_s_by_cell"].items()}
    cfg = DEFAULT_CONSTITUTIVE_CONFIG
    args = dict(
        reference_width_a_m=state.initial_width_m,
        reference_width_b_m=state.initial_width_m,
        lithosphere_a_m=state.initial_lithosphere_m,
        lithosphere_b_m=state.initial_lithosphere_m,
        strike_length_m=1.0,
        interface_stiffness_pa_per_m=cfg["interface_normal_stiffness_pa_per_m"],
        opening_total_m=0.01, opening_increment_m=0.01, dt_s=31_557_600.0,
        young_by_role=cfg["young_modulus_pa_by_role"],
        eta_by_role=cfg["maxwell_viscosity_pa_s_by_role"], model="MAXWELL",
        viscous_strain={}, previous_total_strain={}, previous_displacement_a_m=0.0,
        previous_displacement_b_m=0.0, previous_interface_gap_m=0.0,
        previous_stored_energy_j=0.0,
    )
    synthetic = solve_layered_interface_increment(cells_a, cells_b, **args)
    provider = solve_layered_interface_increment(
        cells_a, cells_b, **args, young_by_cell=young_by_cell, eta_by_cell=eta_by_cell)
    assert provider["interface_force_n"] != pytest.approx(synthetic["interface_force_n"])
    assert provider["interface_stress_pa"] == pytest.approx(
        provider["interface_force_n"] / provider["interface_area_m2"])
    assert provider["viscous_dissipation_increment_j"] > 0
    assert provider["energy_balance_residual_j"] == pytest.approx(0.0, abs=1e-5)
