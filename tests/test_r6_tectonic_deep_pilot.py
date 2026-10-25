from __future__ import annotations

import math

import numpy as np
import pytest

from arcana_worldsim.r6.functional_development import NodeMaterial, ReducedState
from arcana_worldsim.r6.tectonic_deep_pilot import (
    DEFAULT_GRID,
    PilotGrid,
    conservative_two_cell_transport,
    mapped_sensible_energy_j,
    run_multistep_transport_comparison,
    run_tiny_coupling,
)


def _state() -> ReducedState:
    n = 73
    xi = tuple(i / (n - 1) for i in range(n))
    temps = tuple(280.0 + 1380.0 * x for x in xi)
    materials = tuple(
        NodeMaterial("CRUST" if x <= 0.35 else "MANTLE", 2.5, 2800.0, 1000.0, 0.0)
        if x <= 0.35 else NodeMaterial("MANTLE", 3.3, 3300.0, 1200.0, 0.0)
        for x in xi
    )
    return ReducedState(
        time_s=0.0, initial_width_m=110_000.0, width_m=110_000.0,
        initial_crust_m=28_000.0, initial_lithosphere_m=80_000.0,
        crust_m=28_000.0, lithosphere_m=80_000.0, beta=1.0,
        accumulated_strain=0.0, crust_fraction=0.35, material_coordinate=xi,
        temperature_k=temps, materials=materials, surface_temperature_k=280.0,
        base_temperature_k=1660.0,
    )


def test_kernel_output_reaches_deep_thermal_mode_with_separate_ledgers():
    start = _state()
    initial_temp = start.temperature_k
    input_j = mapped_sensible_energy_j(start, DEFAULT_GRID)
    result = run_tiny_coupling(start, duration_years=1.0)
    thermal = result["thermal"]
    deep = result["deep"]

    assert start.temperature_k == initial_temp
    assert thermal["mapped_sensible_energy_before_j"] == pytest.approx(input_j.tolist())
    assert thermal["time_after_s"] > thermal["time_before_s"]
    assert thermal["width_after_m"] > thermal["width_before_m"]
    assert deep["background_thermal_inventory_at_deep_step_start_j"] == thermal["mapped_sensible_energy_after_j"]
    assert deep["photo_contribution_inventory_before_j"] == pytest.approx(
        [0.05 * x for x in thermal["mapped_sensible_energy_after_j"]]
    )
    assert deep["geological_inventory_dfeu"] is None
    assert deep["accessible_dfeu"] is None
    assert deep["solar_flux_or_spatial_irradiance"] is None
    assert deep["geological_accessibility_A_X"] == list(DEFAULT_GRID.geological_accessibility_a_x)
    assert deep["exposure_zeta"] == list(DEFAULT_GRID.exposure_zeta)
    assert deep["energy_closure_relative_to_max_inventory"] <= 64.0 * np.finfo(np.float64).eps
    assert deep["available_energy_j"] is None
    assert all(math.isfinite(v) for v in deep["remaining_background_inventory_j_after"])
    assert all(math.isfinite(v) for v in deep["remaining_photo_inventory_j_after"])


def test_changed_tectonic_input_changes_deep_input_not_just_metadata():
    start = _state()
    no_extension = run_tiny_coupling(start, duration_years=1.0, extension_velocity_m_per_year=0.0)
    extension = run_tiny_coupling(start, duration_years=1.0, extension_velocity_m_per_year=0.11467052868814648)
    assert no_extension["thermal"]["mapped_sensible_energy_after_j"] != extension["thermal"]["mapped_sensible_energy_after_j"]
    assert no_extension["deep"]["background_thermal_inventory_at_deep_step_start_j"] != extension["deep"]["background_thermal_inventory_at_deep_step_start_j"]


def test_noncanonical_two_cell_mapping_is_explicit_and_validated():
    result = run_tiny_coupling(_state())
    grid = result["grid"]
    assert grid["grid_shape"] == [1, 2]
    assert grid["mapping_semantics"] == "TWO_DISJOINT_C029_VERTICAL_CONTROL_VOLUME_SAMPLES_NOT_GLOBAL_CELLS"
    invalid = PilotGrid("x", ("a", "b"), (24, 25), (1.1, 0.8), (0.4, 0.7), (0.6, 0.8), (0.2, 0.3))
    with pytest.raises(ValueError, match="PILOT_GRID_FRACTION_INVALID"):
        mapped_sensible_energy_j(_state(), invalid)


def test_duration_and_accessibility_inputs_fail_closed():
    with pytest.raises(ValueError, match="PILOT_DURATION_MUST_BE_POSITIVE"):
        run_tiny_coupling(_state(), duration_years=0.0)
    invalid = PilotGrid("x", ("a", "b"), (24, 25), (0.5, 0.8), (0.4, 0.7), (0.6, 0.8), (0.2, 0.3), strike_length_m=0.0)
    with pytest.raises(ValueError, match="PILOT_GRID_STRIKE_LENGTH_INVALID"):
        mapped_sensible_energy_j(_state(), invalid)


def test_two_cell_transport_is_conservative_and_preserves_nonnegative_reservoirs():
    initial = np.asarray((9.0, 1.0))
    moved, flux = conservative_two_cell_transport(initial, 0.2)
    assert flux == pytest.approx(1.6)
    assert moved == pytest.approx((7.4, 2.6))
    assert moved.sum() == pytest.approx(initial.sum(), rel=0.0, abs=2 * np.finfo(float).eps * initial.sum())
    assert np.all(moved >= 0.0)
    with pytest.raises(ValueError, match="TRANSPORT_REQUIRES_TWO_FINITE_NONNEGATIVE_RESERVOIRS"):
        conservative_two_cell_transport(np.asarray((1.0, -1.0)), 0.2)
    with pytest.raises(ValueError, match="TRANSPORT_FRACTION_OUTSIDE_CONSERVATIVE_BOUNDS"):
        conservative_two_cell_transport(initial, 0.51)


def test_multistep_coupling_updates_tectonics_deep_and_transport_per_step():
    start = _state()
    initial_temperatures = start.temperature_k
    result = run_multistep_transport_comparison(start, steps=3, step_years=1.0)
    off = result["without_transport"]
    on = result["with_transport"]
    assert result["steps"] == 3
    assert len(off["step_records"]) == len(on["step_records"]) == 3
    assert start.temperature_k == initial_temperatures
    assert result["comparison"]["final_temperature_linf_difference_k"] == 0.0
    assert result["comparison"]["transport_changes_spatial_distribution"] is True
    assert result["comparison"]["max_abs_final_cell_distribution_difference_j"] > 0.0
    for record in on["step_records"]:
        assert record["thermal_time_end_s"] > record["thermal_time_start_s"]
        assert record["thermal_substeps"] >= 1
        scale = record["deep_total_energy_before_transport_j"]
        assert abs(record["background_transport_sum_residual_j"]) / scale <= 64.0 * np.finfo(float).eps
        assert abs(record["photo_transport_sum_residual_j"]) / scale <= 64.0 * np.finfo(float).eps
        assert record["energy_balance_residual_relative"] <= 64.0 * np.finfo(np.float64).eps
        assert all(v >= 0.0 and math.isfinite(v) for v in record["deep_background_after_operator_j"])
        assert all(v >= 0.0 and math.isfinite(v) for v in record["deep_photo_after_operator_j"])
    assert result["energy_semantics"]["geological_inventory_dfeu"] is None
    assert result["energy_semantics"]["accessible_dfeu"] is None
    assert result["energy_semantics"]["thermal_transfer_is_physical_law"] is False
    assert result["energy_semantics"]["solar_flux"] is None


def test_branch_comparison_has_exactly_same_thermal_path():
    state = _state()
    result = run_multistep_transport_comparison(state, steps=2, step_years=0.5, transport_fraction=0.3)
    assert result["without_transport"]["step_records"][0]["thermal_energy_after_j"] == result["with_transport"]["step_records"][0]["thermal_energy_after_j"]
    assert result["without_transport"]["step_records"][1]["thermal_energy_after_j"] == result["with_transport"]["step_records"][1]["thermal_energy_after_j"]
