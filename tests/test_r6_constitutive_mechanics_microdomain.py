from __future__ import annotations

from dataclasses import replace
import math
from time import sleep

import pytest

from arcana_worldsim.r6.constitutive_mechanics_microdomain import (
    DEFAULT_CONSTITUTIVE_CONFIG, _RssSampler, _read_process_rss_bytes,
    solve_layered_interface_increment,
)
from arcana_worldsim.r6.integrated_geological_microdomain import _column_geometry
from arcana_worldsim.r6.tectonic_boundary_microdomain import _series_spring_partition
from test_r6_tectonic_deep_pilot import _state


def _columns():
    base = _state()
    state = replace(base, materials=tuple(replace(
        item, role_id=("CONTINENTAL_CRUST_REFERENCE" if item.role_id == "CRUST"
                       else "LITHOSPHERIC_MANTLE_REFERENCE")) for item in base.materials))
    return (state, _column_geometry(state, "R6G1D-R091-C028", 1.0),
            _column_geometry(state, "R6G1D-R091-C029", 1.0))


def _step(model, opening_total, increment, *, prev_disp=(0.0, 0.0), prev_gap=0.0,
          prev_energy=0.0, history=None, prior_strain=None):
    state, a, b = _columns()
    cfg = DEFAULT_CONSTITUTIVE_CONFIG
    history = {} if history is None else history
    prior_strain = {} if prior_strain is None else prior_strain
    return solve_layered_interface_increment(
        a, b, reference_width_a_m=state.initial_width_m,
        reference_width_b_m=state.initial_width_m,
        lithosphere_a_m=state.initial_lithosphere_m,
        lithosphere_b_m=state.initial_lithosphere_m,
        strike_length_m=1.0,
        interface_stiffness_pa_per_m=cfg["interface_normal_stiffness_pa_per_m"],
        opening_total_m=opening_total, opening_increment_m=increment,
        dt_s=cfg["step_years"] * 31_557_600.0,
        young_by_role=cfg["young_modulus_pa_by_role"],
        eta_by_role=cfg["maxwell_viscosity_pa_s_by_role"], model=model,
        viscous_strain=history, previous_total_strain=prior_strain,
        previous_displacement_a_m=prev_disp[0], previous_displacement_b_m=prev_disp[1],
        previous_interface_gap_m=prev_gap, previous_stored_energy_j=prev_energy,
    )


def test_layered_elastic_force_equilibrium_and_cumulative_load():
    first = _step("ELASTIC", 0.01, 0.01)
    third = _step("ELASTIC", 0.03, 0.03)
    assert first["interface_force_n"] > 0
    assert third["interface_force_n"] == pytest.approx(3.0 * first["interface_force_n"])
    assert abs(third["column_a_force_balance_residual_n"]) < 1e-6
    assert abs(third["column_b_force_balance_residual_n"]) < 1e-6
    assert third["interface_stress_pa"] == pytest.approx(
        third["interface_force_n"] / third["interface_area_m2"])
    assert third["energy_balance_residual_j"] == pytest.approx(0.0, abs=1e-5)
    assert len(third["stress_pa_by_material_cell"]) == 146


def test_maxwell_dissipation_and_mechanical_unloading_are_explicit():
    first = _step("MAXWELL", 0.01, 0.01)
    second = _step("MAXWELL", 0.02, 0.01,
                   prev_disp=(first["column_a_displacement_total_m"], first["column_b_displacement_total_m"]),
                   prev_gap=first["interface_gap_total_m"], prev_energy=first["stored_energy_j"],
                   history=first["updated_viscous_strain"],
                   prior_strain=first["updated_total_strain"])
    unload = _step("MAXWELL", 0.0, -0.02,
                   prev_disp=(second["column_a_displacement_total_m"], second["column_b_displacement_total_m"]),
                   prev_gap=second["interface_gap_total_m"], prev_energy=second["stored_energy_j"],
                   history=second["updated_viscous_strain"],
                   prior_strain=second["updated_total_strain"])
    assert first["viscous_dissipation_increment_j"] > 0
    assert second["viscous_dissipation_increment_j"] > 0
    assert unload["opening_increment_m"] < 0
    assert unload["column_a_displacement_increment_m"] < 0
    assert unload["energy_balance_residual_j"] == pytest.approx(0.0, abs=1e-5)
    assert all(math.isfinite(v) for v in unload["stress_pa_by_material_cell"].values())


def test_previous_three_spring_reference_is_increment_vs_cumulative():
    one_cm = _series_spring_partition(0.01, (2e6, 1e6, 2e6), 1.0)
    three_cm = _series_spring_partition(0.03, (2e6, 1e6, 2e6), 1.0)
    assert one_cm["interface_force_n"] == pytest.approx(5_000.0)
    assert three_cm["interface_force_n"] == pytest.approx(15_000.0)
    assert three_cm["interface_force_n"] != one_cm["interface_force_n"]


def test_os_rss_probe_is_labeled_and_configuration_keeps_synthetic_materials():
    rss = _read_process_rss_bytes()
    assert rss is None or (isinstance(rss, int) and rss > 0)
    assert DEFAULT_CONSTITUTIVE_CONFIG["young_modulus_pa_by_role"]
    assert set(DEFAULT_CONSTITUTIVE_CONFIG["young_modulus_pa_by_role"]) == set(
        DEFAULT_CONSTITUTIVE_CONFIG["deep_initial_density_j_m3_by_role"])
    with _RssSampler(interval_s=0.01) as sampler:
        sleep(0.04)
    observed = sampler.summary()
    assert observed["sample_count"] > 0
    assert observed["sample_errors"] == 0
    assert observed["peak_sampled_rss_bytes"] >= observed["initial_rss_bytes"] > 0
