from __future__ import annotations

import pytest

from arcana_worldsim.r6.geological_surface_microdomain import SUPPORTS, SurfaceConfig
from arcana_worldsim.r6.hydrology_surface_coupling import (
    HydroConfig,
    _manning_discharge_m3_s,
    run_hydrology_scenario,
)


def _states():
    return {
        support: {
            "time_s": 0.0,
            "width_m": 100_000.0,
            "temperature_k": [280.0] * 73,
            "z_m": [0.0] * 73,
            "materials": [{"role_id": "CONTINENTAL_CRUST_REFERENCE",
                           "rho_kg_m3": 2700.0}] * 73,
        }
        for support in SUPPORTS
    }


def _identity():
    return {
        "source_result_sha256": "a" * 64,
        "t0_boundary_id": "TEST_B5_EDGE",
        "t0_boundary_length_m": 111_194.92664455874,
        "support_cells": [
            {"support_id": SUPPORTS[0], "grid_cell": [91, 28]},
            {"support_id": SUPPORTS[1], "grid_cell": [91, 29]},
        ],
    }


def _one_day_config(**kwargs):
    defaults = {
        "duration_years": 1.0 / 365.25,
        "hydrology_dt_seconds": 3600.0,
        "outlet_open": False,
        "sediment_transport_enabled": True,
        "surface_config": SurfaceConfig(
            duration_years=1.0 / 365.25,
            dt_years=1.0 / 365.25,
            initial_relief_m=(20.0, 0.0),
            prescribed_uplift_m=(0.0, 0.0),
            initial_cover_m=(5.0, 5.0),
            enable_surface_transport=False,
        ),
    }
    defaults.update(kwargs)
    return HydroConfig(**defaults)


def test_manning_discharge_increases_with_depth_and_slope():
    q0 = _manning_discharge_m3_s(0.1, 100.0, 0.001, 0.04)
    assert q0 > 0
    assert _manning_discharge_m3_s(0.2, 100.0, 0.001, 0.04) > q0
    assert _manning_discharge_m3_s(0.1, 100.0, 0.004, 0.04) > q0
    assert _manning_discharge_m3_s(0.1, 100.0, 0.0, 0.04) == 0.0


def test_no_precipitation_has_zero_water_flux_and_closed_balances():
    result = run_hydrology_scenario(
        _states(), _identity(),
        config=_one_day_config(precipitation_m_year_by_support=(0.0, 0.0)),
    )
    assert result["water_balance"]["precipitation_input_m3"] == 0.0
    assert result["water_balance"]["internal_transfer_m3"] == 0.0
    assert result["water_balance"]["outlet_export_m3"] == 0.0
    assert result["water_balance"]["residual_m3"] == pytest.approx(0.0)
    assert result["sediment_balance"]["erosion_from_cover_kg"] == 0.0


def test_precipitation_with_closed_outlet_routes_water_and_sediment_internally():
    result = run_hydrology_scenario(_states(), _identity(), config=_one_day_config())
    assert result["water_balance"]["precipitation_input_m3"] > 0
    assert result["water_balance"]["internal_transfer_m3"] > 0
    assert result["water_balance"]["outlet_export_m3"] == 0.0
    assert result["sediment_balance"]["internal_suspended_transfer_kg"] > 0
    assert result["sediment_balance"]["outlet_sediment_export_kg"] == 0.0
    assert result["water_balance"]["residual_m3"] == pytest.approx(0.0, abs=1e-3)
    assert result["sediment_balance"]["residual_kg"] == pytest.approx(0.0, abs=0.1)


def test_sediment_deposits_when_prescribed_rainfall_and_transport_capacity_fall():
    # Synthetic storm pulse followed by a dry recession; rates are specified
    # per hourly substep so this tests deposition without inventing geology.
    schedule = tuple((0.8, 0.4) if step < 6 else (0.0, 0.0) for step in range(24))
    result = run_hydrology_scenario(
        _states(), _identity(),
        config=_one_day_config(precipitation_schedule_m_year_by_support=schedule),
    )
    assert result["sediment_balance"]["internal_suspended_transfer_kg"] > 0.0
    assert result["sediment_balance"]["deposition_to_cover_kg"] > 0.0
    assert result["sediment_balance"]["residual_kg"] == pytest.approx(0.0, abs=0.1)


def test_material_id_survives_suspension_transport_deposition_and_mass_ledger():
    schedule = tuple((0.8, 0.4) if step < 6 else (0.0, 0.0) for step in range(24))
    config = _one_day_config(
        precipitation_schedule_m_year_by_support=schedule,
        initial_suspended_sediment_kg_by_support=(100.0, 0.0),
        initial_suspended_material_kg_by_support=({"SYNTHETIC_SOURCE:C028": 100.0}, {}),
    )
    result = run_hydrology_scenario(_states(), _identity(), config=config)
    balance = result["sediment_balance"]
    assert balance["deposition_to_cover_kg"] > 0.0
    assert all(abs(x) < 1e-6 for x in balance["material_mass_balance_residual_kg_by_id"].values())
    material_id = "SYNTHETIC_SOURCE:C028"
    deposited = balance["deposition_kg_by_surface_cell_and_material"]
    assert sum(row.get(material_id, 0.0) for row in deposited.values()) > 0.0
    assert balance["substrate_residual_kg"] == pytest.approx(0.0)


def test_synthetic_bedrock_detachment_enters_sediment_and_deposits_with_identity():
    duration = 1.0 / 365.25
    surface = SurfaceConfig(
        duration_years=duration, dt_years=duration,
        initial_relief_m=(20.0, 0.0), prescribed_uplift_m=(0.0, 0.0),
        initial_cover_m=(0.0, 0.0), enable_surface_transport=False,
    )
    config = HydroConfig(
        duration_years=duration, hydrology_dt_seconds=3600.0,
        precipitation_m_year_by_support=(0.0, 0.0),
        precipitation_schedule_m_year_by_support=tuple(
            (0.8, 0.4) if step < 6 else (0.0, 0.0) for step in range(24)),
        initial_substrate_mass_kg_by_support=(1.0e9, 1.0e9),
        substrate_material_id_by_support=("SYNTHETIC_ROCK:C028", "SYNTHETIC_ROCK:C029"),
        substrate_erosion_enabled=True, substrate_critical_shear_pa=0.0,
        substrate_detachment_kg_pa_s=1.0e4,
        outlet_open=False, surface_config=surface,
    )
    result = run_hydrology_scenario(_states(), _identity(), config=config)
    balance = result["sediment_balance"]
    assert balance["bedrock_erosion_kg"] > 0.0
    assert balance["deposition_to_cover_kg"] > 0.0
    assert balance["deposition_kg_by_material_id"]["SYNTHETIC_ROCK:C028"] > 0.0
    assert balance["substrate_residual_kg"] == pytest.approx(0.0, abs=1e-6)
    assert balance["residual_kg"] == pytest.approx(0.0, abs=0.1)
    assert all(abs(value) < 1e-6
               for value in balance["material_mass_balance_residual_kg_by_id"].values())
    assert all(cell["substrate_mass_kg"] >= 0 and cell["mobile_cover_mass_kg"] >= 0
               for cell in result["cells"])


def test_open_outlet_exports_water_and_active_sediment_without_rock_erosion():
    active = run_hydrology_scenario(
        _states(), _identity(), config=_one_day_config(outlet_open=True))
    inactive = run_hydrology_scenario(
        _states(), _identity(),
        config=_one_day_config(outlet_open=True, sediment_transport_enabled=False))
    assert active["water_balance"]["outlet_export_m3"] > 0
    assert active["sediment_balance"]["erosion_from_cover_kg"] > 0
    assert active["sediment_balance"]["outlet_sediment_export_kg"] > 0
    assert active["sediment_balance"]["bedrock_erosion_kg"] == 0.0
    assert inactive["sediment_balance"]["erosion_from_cover_kg"] == 0.0
    assert inactive["sediment_balance"]["outlet_sediment_export_kg"] == 0.0
    assert active["water_balance"]["residual_m3"] == pytest.approx(0.0, abs=1e-3)
    assert active["sediment_balance"]["residual_kg"] == pytest.approx(0.0, abs=0.1)
    assert active["geometry_balance"]["residual_m3"] == pytest.approx(0.0, abs=1e-3)


def test_exhausted_cover_caps_erosion_and_inverted_slope_reverses_flow():
    dry_cover = SurfaceConfig(duration_years=1.0 / 365.25,
                              dt_years=1.0 / 365.25,
                              initial_relief_m=(20.0, 0.0),
                              prescribed_uplift_m=(0.0, 0.0),
                              initial_cover_m=(0.0, 0.0),
                              enable_surface_transport=False)
    no_cover = run_hydrology_scenario(
        _states(), _identity(),
        config=_one_day_config(surface_config=dry_cover, outlet_open=True))
    assert no_cover["sediment_balance"]["erosion_from_cover_kg"] == 0.0
    assert no_cover["sediment_balance"]["final_mobile_cover_kg"] == 0.0

    inverted = SurfaceConfig(duration_years=1.0 / 365.25,
                             dt_years=1.0 / 365.25,
                             initial_relief_m=(0.0, 20.0),
                             prescribed_uplift_m=(0.0, 0.0),
                             initial_cover_m=(5.0, 5.0),
                             enable_surface_transport=False)
    reverse = run_hydrology_scenario(
        _states(), _identity(),
        config=_one_day_config(surface_config=inverted,
                               precipitation_m_year_by_support=(0.4, 0.4)))
    assert reverse["hydraulic_diagnostics"]["reverse_internal_flow_substeps"] > 0
    assert reverse["water_balance"]["residual_m3"] == pytest.approx(0.0, abs=1e-3)
