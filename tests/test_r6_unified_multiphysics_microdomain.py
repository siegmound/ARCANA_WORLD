from __future__ import annotations

from dataclasses import replace
import math

import pytest

from arcana_worldsim.r6.functional_development import NodeMaterial, ReducedState
from arcana_worldsim.r6.geological_surface_microdomain import SUPPORTS, SurfaceMicrodomainError
from arcana_worldsim.r6.unified_multiphysics_microdomain import (
    UnifiedConfig, continue_unified_microdomain, query_unified_result,
    run_experiment_matrix, run_unified_microdomain, unified_states_from_checkpoint,
    parse_unified_checkpoint, serialize_unified_checkpoint, verify_unified_checkpoint,
)
from arcana_worldsim.r6.tectonic_deep_pilot import SECONDS_PER_YEAR


def _states():
    materials = tuple(NodeMaterial(
        role_id=("CONTINENTAL_CRUST_REFERENCE" if i < 25 else "LITHOSPHERIC_MANTLE_REFERENCE"),
        k_w_m_k=3.0 if i < 25 else 4.0,
        rho_kg_m3=2800.0 if i < 25 else 3300.0,
        cp_j_kg_k=1000.0, radiogenic_w_m3=1e-6 if i < 25 else 2e-8,
    ) for i in range(73))
    z = tuple(i / 72 for i in range(73))
    t = tuple(280.0 + 1200.0 * x for x in z)
    base = ReducedState(
        time_s=0.0, initial_width_m=100_000.0, width_m=100_000.0,
        initial_crust_m=35_000.0, initial_lithosphere_m=100_000.0,
        crust_m=35_000.0, lithosphere_m=100_000.0,
        beta=1.0, accumulated_strain=0.0, crust_fraction=0.35,
        material_coordinate=z, temperature_k=t, materials=materials,
        surface_temperature_k=280.0, base_temperature_k=1480.0,
    )
    return {SUPPORTS[0]: base, SUPPORTS[1]: replace(base, width_m=101_000.0,
                                                     initial_width_m=101_000.0)}


def _source_identity():
    return {
        "source_result_sha256": "a" * 64,
        "t0_boundary_id": "SYNTHETIC_T0_EDGE",
        "t0_boundary_length_m": 111_194.92664455874,
        "support_cells": [
            {"support_id": SUPPORTS[0], "grid_cell": [91, 28]},
            {"support_id": SUPPORTS[1], "grid_cell": [91, 29]},
        ],
    }


def _one_day_config():
    dt_years = 1.0 / 365.25
    return UnifiedConfig(duration_years=dt_years, external_step_years=dt_years,
                         hydrology_dt_seconds=3600.0)


def test_shared_clock_runs_all_domains_and_closes_ledgers():
    states = _states()
    initial_payloads = {support: state.payload() for support, state in states.items()}
    result = run_unified_microdomain(states, _source_identity(), config=_one_day_config())
    assert result["schema"] == "ARCANA_R6_UNIFIED_MULTIPHYSICS_MICRODOMAIN_V1"
    assert result["configuration"]["operator_order"] == [
        "MAXWELL_MECHANICS", "THERMAL_PURE_SHEAR", "PRESCRIBED_UPLIFT_AND_SURFACE_GEOMETRY",
        "HYDROLOGY_SEDIMENT", "DEEP_SYNTHETIC_RESERVOIR",
    ]
    assert len(result["steps"]) == 1
    step = result["steps"][0]
    assert step["time_end_s"] == pytest.approx(86400.0)
    assert step["mechanics"]["energy_balance_residual_j"] == pytest.approx(0.0, abs=1e-5)
    assert all(row["substeps"] > 0 for row in step["thermal"].values())
    assert {support: state.payload() for support, state in states.items()} == initial_payloads
    assert set(result["final"]["time_s_by_support"].values()) == {86400.0}
    assert all(math.isfinite(value)
               for state in result["final"]["thermal_states"].values()
               for value in state["temperature_k"])
    assert all(value >= 0 for cell in result["final"]["surface_hydrology_cells"]
               for value in (cell["water_storage_m3"], cell["mobile_cover_mass_kg"],
                             cell["suspended_sediment_kg"]))
    assert all(value >= 0 for value in result["final"]["deep_inventory_j_by_volume"].values())
    assert result["integrated_balances"]["water"]["residual_m3"] == pytest.approx(0.0, abs=1e-3)
    assert result["integrated_balances"]["sediment"]["residual_kg"] == pytest.approx(0.0, abs=0.1)
    assert result["integrated_balances"]["geometry"]["residual_m3"] == pytest.approx(0.0, abs=1e-3)
    assert result["integrated_balances"]["deep"]["residual_j"] == pytest.approx(0.0, abs=1e-5)
    assert result["integrated_balances"]["deep"]["thermal_transfer_j"] == 0.0
    assert result["integrated_balances"]["deep"]["mechanical_work_transfer_j"] == 0.0
    deep_ids = list(result["initial"]["deep_inventory_j_by_volume"])
    previous_deep = dict(result["initial"]["deep_inventory_j_by_volume"])
    for row in result["steps"]:
        deep = row["deep"]
        flux = deep["transport_flux_0_to_1_j"]
        current = deep["inventory_j_by_material_volume"]
        assert current[deep_ids[0]] - previous_deep[deep_ids[0]] == pytest.approx(-flux, abs=1e-4)
        assert current[deep_ids[1]] - previous_deep[deep_ids[1]] == pytest.approx(flux, abs=1e-4)
        assert sum(current.values()) == pytest.approx(sum(previous_deep.values()), abs=1e-5)
        assert min(current.values()) >= 0.0
        previous_deep = current
    assert result["integrated_balances"]["mechanical"]["residual_j"] == pytest.approx(0.0, abs=1e-4)
    assert step["material_volumes"][SUPPORTS[0]][0]["material_volume_id"] != step[
        "surface_hydrology"]["surface_cells"][0]["surface_cell_id"]


def test_causal_cases_no_rain_changed_uplift_and_deep_passivity():
    matrix = run_experiment_matrix(_states(), _source_identity(), config=_one_day_config())
    wet, dry, uplift, passive = (matrix[k] for k in (
        "BASELINE", "NO_PRECIPITATION", "ALTERED_UPLIFT", "DEEP_PASSIVE"))
    assert wet["integrated_balances"]["water"]["precipitation_input_m3"] > 0
    assert dry["integrated_balances"]["water"]["precipitation_input_m3"] == 0
    assert wet["integrated_balances"]["sediment"]["erosion_from_cover_kg"] > 0
    assert dry["integrated_balances"]["sediment"]["erosion_from_cover_kg"] == 0
    assert uplift["final"]["surface_hydrology_cells"][0]["surface_elevation_m"] > wet[
        "final"]["surface_hydrology_cells"][0]["surface_elevation_m"]
    assert uplift["integrated_balances"]["water"]["outlet_export_m3"] != pytest.approx(
        wet["integrated_balances"]["water"]["outlet_export_m3"], abs=1e-6)
    assert (uplift["steps"][0]["surface_hydrology"]["hydraulic_diagnostics"]["maximum_discharge_m3_s"]
            != wet["steps"][0]["surface_hydrology"]["hydraulic_diagnostics"]["maximum_discharge_m3_s"])
    assert wet["final"]["deep_inventory_j_by_volume"] != passive["final"]["deep_inventory_j_by_volume"]
    for domain in ("thermal_state_sha256_by_support",):
        assert wet["final"][domain] == passive["final"][domain]
    assert wet["final"]["surface_hydrology_cells"] == passive["final"]["surface_hydrology_cells"]
    assert wet["steps"][0]["mechanics"] == passive["steps"][0]["mechanics"]


def test_exact_time_reader_rejects_interpolation_and_returns_domain_support():
    result = {"cases": {"X": run_unified_microdomain(
        _states(), _source_identity(), config=_one_day_config())}}
    query = query_unified_result(result, case_id="X", elapsed_years=1 / 365.25,
                                 support_id=SUPPORTS[1], domain="SURFACE_HYDROLOGY")
    assert query["value"]["support_id"] == SUPPORTS[1]
    with pytest.raises(SurfaceMicrodomainError, match="TIME_NOT_EXACTLY_STORED"):
        query_unified_result(result, case_id="X", elapsed_years=0.5 / 365.25,
                             support_id=SUPPORTS[1], domain="THERMAL")


def test_mismatched_support_clock_and_unsupported_role_fail_closed():
    states = _states()
    states[SUPPORTS[1]] = replace(states[SUPPORTS[1]], time_s=1.0)
    with pytest.raises(SurfaceMicrodomainError, match="TIME_MISMATCH"):
        run_unified_microdomain(states, _source_identity(), config=_one_day_config())

    states = _states()
    bad_materials = tuple(replace(m, role_id="UNKNOWN_ROLE") if i == 0 else m
                          for i, m in enumerate(states[SUPPORTS[0]].materials))
    states[SUPPORTS[0]] = replace(states[SUPPORTS[0]], materials=bad_materials)
    with pytest.raises(SurfaceMicrodomainError, match="UNKNOWN_MATERIAL_ROLE"):
        run_unified_microdomain(states, _source_identity(), config=_one_day_config())


def test_checkpoint_restart_one_plus_two_years_matches_continuous_three_years():
    config = UnifiedConfig(duration_years=3.0, external_step_years=1.0,
                           hydrology_dt_seconds=SECONDS_PER_YEAR / 12.0,
                           substrate_erosion_enabled=True,
                           substrate_detachment_kg_pa_s=1.0e-5)
    continuous = run_unified_microdomain(_states(), _source_identity(), config=config)
    first = run_unified_microdomain(_states(), _source_identity(), config=config, segment_years=1.0)
    assert first["continuation"]["state"]["elapsed_external_steps"] == 1
    checkpoint_copy = parse_unified_checkpoint(serialize_unified_checkpoint(first["continuation"]))
    assert unified_states_from_checkpoint(checkpoint_copy)
    restarted = continue_unified_microdomain(
        checkpoint_copy, _source_identity(), config=config, segment_years=2.0)
    assert len(restarted["steps"]) == 3
    assert [row["time_end_s"] for row in restarted["steps"]] == [
        SECONDS_PER_YEAR, 2 * SECONDS_PER_YEAR, 3 * SECONDS_PER_YEAR]
    assert restarted["final"]["thermal_state_sha256_by_support"] == continuous[
        "final"]["thermal_state_sha256_by_support"]
    assert restarted["final"]["deep_inventory_j_by_volume"] == continuous[
        "final"]["deep_inventory_j_by_volume"]
    assert restarted["final"]["surface_hydrology_cells"] == continuous[
        "final"]["surface_hydrology_cells"]
    assert restarted["integrated_balances"] == continuous["integrated_balances"]
    assert restarted["steps"] == continuous["steps"]
    assert restarted["integrated_balances"]["sediment"]["bedrock_erosion_kg"] > 0.0
    damaged = dict(first["continuation"])
    damaged["state"] = dict(damaged["state"])
    damaged["state"]["elapsed_external_steps"] = 2
    with pytest.raises(SurfaceMicrodomainError, match="CHECKPOINT_DIGEST_MISMATCH"):
        verify_unified_checkpoint(damaged)
    with pytest.raises(SurfaceMicrodomainError, match="SOURCE_IDENTITY_MISMATCH"):
        continue_unified_microdomain(first["continuation"], {**_source_identity(), "changed": True},
                                     config=config, segment_years=2.0)


def test_no_rain_has_no_hydraulic_substrate_detachment_and_material_query_is_exact():
    config = UnifiedConfig(duration_years=1.0, external_step_years=1.0,
                           hydrology_dt_seconds=SECONDS_PER_YEAR)
    result = run_unified_microdomain(_states(), _source_identity(), config=config,
                                     precipitation_m_year_by_support=(0.0, 0.0))
    assert result["integrated_balances"]["water"]["precipitation_input_m3"] == 0.0
    assert result["integrated_balances"]["sediment"]["bedrock_erosion_kg"] == 0.0
    assert result["integrated_balances"]["sediment"]["substrate_residual_kg"] == pytest.approx(0.0)
    assert all(cell["substrate_mass_kg"] >= 0 for cell in result["final"]["surface_hydrology_cells"])
    material = query_unified_result({"cases": {"X": result}}, case_id="X", elapsed_years=1.0,
                                    support_id=SUPPORTS[0], domain="MATERIAL")
    assert material["value"]["surface_state"]["support_id"] == SUPPORTS[0]
    with pytest.raises(SurfaceMicrodomainError, match="TIME_NOT_EXACTLY_STORED"):
        query_unified_result({"cases": {"X": result}}, case_id="X", elapsed_years=0.5,
                             support_id=SUPPORTS[0], domain="MATERIAL")


def test_synthetic_hydraulic_bedrock_detachment_preserves_material_and_deep_budgets():
    base = _one_day_config()
    config = UnifiedConfig(
        duration_years=base.duration_years,
        external_step_years=base.external_step_years,
        hydrology_dt_seconds=base.hydrology_dt_seconds,
        substrate_erosion_enabled=True,
        substrate_critical_shear_pa=0.0,
        substrate_detachment_kg_pa_s=1.0e4,
        outlet_open=True,
    )
    result = run_unified_microdomain(_states(), _source_identity(), config=config)
    balance = result["integrated_balances"]
    assert balance["sediment"]["bedrock_erosion_kg"] > 0.0
    assert balance["sediment"]["residual_kg"] == pytest.approx(0.0, abs=0.1)
    assert balance["sediment"]["substrate_residual_kg"] == pytest.approx(0.0, abs=0.1)
    assert balance["deep"]["residual_j"] == pytest.approx(0.0, abs=1e-5)
    assert balance["deep"]["gross_internal_transport_j"] >= abs(
        balance["deep"]["net_transport_0_to_1_j"])
    assert balance["deep"]["minimum_reservoir_stock_j"] >= 0.0
    material_id = config.substrate_material_id_by_support[0]
    assert (result["final"]["material_inventory_by_support"][SUPPORTS[0]][
        "mobile_material_mass_kg_by_id"].get(material_id, 0.0)
        + result["final"]["material_inventory_by_support"][SUPPORTS[1]][
            "mobile_material_mass_kg_by_id"].get(material_id, 0.0)
        + result["final"]["material_inventory_by_support"][SUPPORTS[0]][
            "suspended_material_mass_kg_by_id"].get(material_id, 0.0)
        + result["final"]["material_inventory_by_support"][SUPPORTS[1]][
            "suspended_material_mass_kg_by_id"].get(material_id, 0.0)
        + balance["sediment"]["outlet_export_kg_by_material_id"].get(material_id, 0.0)) > 0.0
    material_query = query_unified_result(
        {"cases": {"X": result}}, case_id="X", elapsed_years=base.duration_years,
        support_id=SUPPORTS[0], domain="MATERIAL", material_id=material_id)
    assert material_query["value"]["surface_state"]["substrate"]["material_id"] == material_id
    assert material_query["value"]["flows"]["bedrock_detachment_kg_by_material_id"][material_id] > 0.0
