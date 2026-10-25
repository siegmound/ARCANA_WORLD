from __future__ import annotations

from dataclasses import replace

import pytest

from arcana_worldsim.r6.functional_development import NodeMaterial, ReducedState
from arcana_worldsim.r6.geological_surface_microdomain import SUPPORTS
from arcana_worldsim.r6.regional_geological_evolution import (
    RegionalConfig, RegionalModelError, advance_region, create_synthetic_region,
    query_deep_inventory, query_material_provenance, query_materials_at_time,
    run_regional_segment, verify_regional_checkpoint, _drainage_for_elevation,
    _routing_order,
)


def _initial_states():
    materials = tuple(NodeMaterial(
        role_id="CONTINENTAL_CRUST_REFERENCE" if i < 25 else "LITHOSPHERIC_MANTLE_REFERENCE",
        k_w_m_k=3.0 if i < 25 else 4.0, rho_kg_m3=2800.0 if i < 25 else 3300.0,
        cp_j_kg_k=1000.0, radiogenic_w_m3=1e-6 if i < 25 else 2e-8)
        for i in range(73))
    z = tuple(i / 72 for i in range(73))
    t = tuple(280.0 + 1200.0 * x for x in z)
    a = ReducedState(0.0, 100_000.0, 100_000.0, 35_000.0, 100_000.0,
        35_000.0, 100_000.0, 1.0, 0.0, 0.35, z, t, materials, 280.0, 1480.0)
    return {SUPPORTS[0]: a, SUPPORTS[1]: replace(a, width_m=101_000.0,
                                                initial_width_m=101_000.0)}


def _identity():
    return {"source_result_sha256": "a" * 64,
        "t0_boundary_id": "SYNTHETIC_T0_EDGE", "t0_boundary_length_m": 111_194.92664455874,
        "support_cells": [{"support_id": SUPPORTS[0], "grid_cell": [91, 28], "plate_id": 11},
                          {"support_id": SUPPORTS[1], "grid_cell": [91, 29], "plate_id": 5}]}


def _config():
    return RegionalConfig(duration_years=3, detachment_enabled=True,
                          critical_shear_pa=0.0, detachment_kg_pa_s_m2=1e-8)


def _assert_nested_close(left, right):
    if isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            _assert_nested_close(left[key], right[key])
    elif isinstance(left, list):
        assert len(left) == len(right)
        for a, b in zip(left, right):
            _assert_nested_close(a, b)
    elif isinstance(left, float):
        assert left == pytest.approx(right, rel=2e-14, abs=1e-8)
    else:
        assert left == right


def test_regional_3_year_continuous_equals_1_plus_2_checkpoint_restart():
    states, identity, cfg = _initial_states(), _identity(), _config()
    continuous = run_regional_segment(states, identity, config=cfg, segment_years=3)
    first = run_regional_segment(states, identity, config=cfg, segment_years=1)
    restored = verify_regional_checkpoint(first["checkpoint"])
    assert restored["time_years"] == 1
    split = run_regional_segment(states, identity, config=cfg, segment_years=2,
                                 checkpoint=first["checkpoint"])
    _assert_nested_close(split["state"], continuous["state"])
    _assert_nested_close(split["subsurface_unified_result"]["final"],
                         continuous["subsurface_unified_result"]["final"])
    deep = continuous["balances"]["deep"]
    assert deep["final_inventory_j"] == pytest.approx(deep["initial_inventory_j"], abs=1e-3)
    assert deep["residual_j"] == pytest.approx(0.0, abs=1e-3)
    assert deep["source_j"] == 0.0
    assert deep["thermal_transfer_j"] == 0.0
    assert deep["mechanical_work_transfer_j"] == 0.0
    assert verify_regional_checkpoint(split["checkpoint"])["time_years"] == 3


def test_dynamic_surface_scenario_does_not_feed_back_into_subsurface_kernel():
    base = _config()
    perturbed = replace(base,
        initial_elevation_offsets_m_by_cell=(0., 0., 0., 0., 0., 0., 0., 6., 0.))
    ordinary = run_regional_segment(_initial_states(), _identity(),
                                    config=base, segment_years=3)
    changed = run_regional_segment(_initial_states(), _identity(),
                                   config=perturbed, segment_years=3)
    assert ordinary["state"]["drainage_targets"]["4"] == 7
    assert changed["state"]["drainage_targets"]["4"] == -1
    _assert_nested_close(ordinary["subsurface_unified_result"]["final"],
                         changed["subsurface_unified_result"]["final"])
    assert ordinary["balances"]["deep"] == changed["balances"]["deep"]


def test_regional_hydrology_confluence_material_provenance_and_balances():
    result = run_regional_segment(_initial_states(), _identity(), config=_config(), segment_years=1)
    state = result["state"]
    assert state["drainage_targets"]["1"] == 2
    assert state["drainage_targets"]["3"] == 4
    assert state["drainage_targets"]["2"] == 5
    assert state["drainage_targets"]["4"] == 7
    assert state["drainage_targets"]["5"] == 8
    assert state["drainage_targets"]["7"] == 8
    assert state["interfaces"][0]["routing_status"] == "BLOCKED_NO_CROSS_BOUNDARY_HYDROLOGY_LAW"
    record = state["records"][0]
    assert abs(record["water_balance_m3"]["residual"]) < 1e-6
    assert max(abs(x["residual_m3"]) for x in record["water_balance_m3"]["per_cell"]) < 1e-6
    assert abs(record["water_balance_m3"]["residual"]) <= record["water_balance_m3"]["roundoff_tolerance"]
    assert abs(record["solid_mass_balance_kg"]["residual"]) < 1e-3
    assert abs(record["solid_mass_balance_kg"]["residual"]) <= record["solid_mass_balance_kg"]["roundoff_tolerance_kg"]
    assert max(abs(x["local_residual_kg"]) for x in record["solid_mass_balance_kg"]["per_cell"]) < 1e-3
    assert all(abs(x["local_residual_kg"]) <= x["roundoff_tolerance_kg"]
               for x in record["solid_mass_balance_kg"]["per_cell"])
    assert record["solid_mass_balance_kg"]["substrate_erosion_is_internal_transfer"]
    assert state["cumulative"]["substrate_eroded_kg"] > 0
    assert any(event["kind"] == "BEDROCK_EROSION" for event in record["events"])
    assert any(event["kind"] == "DEPOSITION" for event in record["events"])
    assert any(abs(cell["elevation_m"] - 12.0) > 0 for cell in state["cells"])
    mid = "SYNTHETIC_BENCHMARK_ROCK:C00"
    assert query_material_provenance(result, mid)
    assert query_materials_at_time(result, time_year=0, cell_id=state["cells"][0]["cell_id"])[0]["deposits"] == []
    assert query_materials_at_time(result, time_year=1, cell_id=state["cells"][0]["cell_id"])
    assert query_deep_inventory(result, cell_id=state["cells"][4]["cell_id"])["deep_volume_id"].startswith(SUPPORTS[0])
    assert query_deep_inventory(result, cell_id=state["cells"][4]["cell_id"], time_year=1)["inventory_j"] > 0
    assert query_deep_inventory(result, cell_id=state["cells"][4]["cell_id"], time_year=0)["inventory_j"] == 1e12
    assert query_deep_inventory(result, cell_id=state["cells"][0]["cell_id"])["status"].startswith("UNKNOWN")


def test_checkpoint_fails_closed_on_tampering_and_unknown_time_query():
    state = create_synthetic_region(_config(), source_identity=_identity())
    result = run_regional_segment(_initial_states(), _identity(), config=_config(), segment_years=1)
    damaged = dict(result["checkpoint"])
    damaged["regional_state"] = dict(damaged["regional_state"])
    damaged["regional_state"]["time_years"] = 0
    with pytest.raises(RegionalModelError, match="CHECKPOINT_DIGEST"):
        verify_regional_checkpoint(damaged)
    with pytest.raises(RegionalModelError, match="TIME_NOT_ARCHIVED"):
        query_materials_at_time(result, time_year=2)
    assert state["cells"][0]["support_id"] is None


def test_no_rain_has_no_runoff_erosion_or_material_transfer():
    cfg = replace(_config(), precipitation_m_year=0.0)
    initial = create_synthetic_region(cfg, source_identity=_identity())
    final = advance_region(initial, years=1, config=cfg)
    assert final["cumulative"]["precipitation_m3"] == 0.0
    assert final["cumulative"]["substrate_eroded_kg"] == 0.0
    assert final["cumulative"]["sediment_export_kg"] == 0.0
    assert final["records"][0]["water_balance_m3"]["residual"] == 0.0


def test_dynamic_routing_topographic_perturbation_forms_persistent_depression():
    offsets = (0., 0., 0., 0., 0., 0., 0., 6., 0.)
    dynamic_cfg = replace(_config(), routing_mode="DYNAMIC_TOPOGRAPHY",
                          initial_elevation_offsets_m_by_cell=offsets)
    base_cfg = _config()
    base = run_regional_segment(_initial_states(), _identity(), config=base_cfg,
                                segment_years=1)
    perturbed = run_regional_segment(_initial_states(), _identity(),
                                     config=dynamic_cfg, segment_years=1)
    assert base["state"]["drainage_targets"]["4"] == 7
    assert perturbed["state"]["drainage_targets"]["4"] == -1
    assert perturbed["state"]["cells"][4]["depression_storage_m3"] > 0
    assert perturbed["state"]["cells"][4]["water_storage_m3"] >= +        perturbed["state"]["cells"][4]["depression_storage_m3"]
    assert perturbed["state"]["records"][0]["depression_storage_m3_by_cell"][
        "SYNTHETIC_BASIN_3X3:C04"] > 0
    assert perturbed["state"]["records"][0]["water_balance_m3"]["residual"] == 0
    assert perturbed["state"]["records"][0]["solid_mass_balance_kg"]["residual"] == 0
    assert perturbed["state"]["cells"][8]["deposits"] != base["state"]["cells"][8]["deposits"]


def test_dynamic_routing_rebuilds_after_uplift_but_fixed_baseline_does_not():
    uplift = (0., 0., 0., 0., 0., 0., 0., 6., 0.)
    dynamic_cfg = replace(_config(), routing_mode="DYNAMIC_TOPOGRAPHY",
                          prescribed_uplift_m_year_by_cell=uplift)
    fixed_cfg = replace(_config(), routing_mode="FIXED_BASELINE",
                        prescribed_uplift_m_year_by_cell=uplift)
    dynamic = advance_region(create_synthetic_region(dynamic_cfg, source_identity=_identity()),
                             years=1, config=dynamic_cfg)
    fixed = advance_region(create_synthetic_region(fixed_cfg, source_identity=_identity()),
                           years=1, config=fixed_cfg)
    assert dynamic["records"][0]["drainage_targets_used"]["4"] == -1
    assert fixed["records"][0]["drainage_targets_used"]["4"] == 7
    changes = [x for x in dynamic["records"][0]["events"]
               if x["kind"] == "DRAINAGE_CONNECTIVITY_CHANGED"]
    assert any(x["previous_targets"]["4"] == 7
               and x["updated_targets"]["4"] == -1 for x in changes)
    assert any(x["kind"] == "PRESCRIBED_SYNTHETIC_UPLIFT"
               for x in dynamic["records"][0]["events"])
    assert dynamic["cells"][7]["cumulative_uplift_m"] == 6.0
    assert fixed["cells"][7]["cumulative_uplift_m"] == 6.0


def test_explicit_hydraulic_cross_boundary_link_is_not_mechanics_or_deep_link():
    blocked = create_synthetic_region(_config(), source_identity=_identity())
    connected_cfg = replace(_config(), hydraulic_connectivity_edges=((4, 5),))
    connected = create_synthetic_region(connected_cfg, source_identity=_identity())
    assert blocked["drainage_targets"]["4"] == 7
    assert connected["drainage_targets"]["4"] == 5
    assert blocked["interfaces"][0]["routing_status"] == \
        "BLOCKED_NO_CROSS_BOUNDARY_HYDROLOGY_LAW"
    assert connected["interfaces"][0]["routing_status"] == \
        "EXPLICIT_EXPERIMENTAL_HYDRAULIC_CONNECTIVITY_ENABLED"
    assert connected["interfaces"][0]["mechanical_continuity"] == "UNKNOWN_NOT_INFERRED"
    assert connected["interfaces"][0]["deep_transport"] == "DISABLED"
    with pytest.raises(RegionalModelError, match="HYDRAULIC_EDGE_INVALID"):
        replace(_config(), hydraulic_connectivity_edges=((4, 8),)).validate()


def test_routing_graph_is_acyclic_and_load_is_cellwise_bookkeeping():
    config = _config()
    result = run_regional_segment(_initial_states(), _identity(), config=config,
                                  segment_years=3)
    state = result["state"]
    for record in state["records"]:
        order = _routing_order(record["drainage_targets_used"])
        assert sorted(order) == list(range(9))
    for cell, load in zip(state["cells"], state["records"][-1]["geologic_load_by_cell"]):
        assert load["cell_id"] == cell["cell_id"]
        assert load["area_m2"] == cell["area_m2"]
        assert load["deposited_kg"] == pytest.approx(cell["cumulative_deposited_kg"])
        assert load["column_equivalent_pressure_change_pa"] == pytest.approx(
            load["surface_load_change_kg"] * 9.80665 / load["area_m2"])
        assert load["pressure_authority"].startswith("BOOKKEEPING_DIAGNOSTIC")
    assert state["records"][-1]["water_balance_m3"]["residual"] == pytest.approx(0.0)
    assert state["records"][-1]["solid_mass_balance_kg"]["residual"] == pytest.approx(0.0)


def test_dynamic_routing_checkpoint_restart_preserves_depression_and_deep():
    offsets = (0., 0., 0., 0., 0., 0., 0., 6., 0.)
    cfg = replace(_config(), routing_mode="DYNAMIC_TOPOGRAPHY",
                  initial_elevation_offsets_m_by_cell=offsets)
    continuous = run_regional_segment(_initial_states(), _identity(),
                                      config=cfg, segment_years=3)
    first = run_regional_segment(_initial_states(), _identity(),
                                 config=cfg, segment_years=1)
    second = run_regional_segment(_initial_states(), _identity(),
                                  config=cfg, segment_years=2,
                                  checkpoint=first["checkpoint"])
    _assert_nested_close(second["state"], continuous["state"])
    _assert_nested_close(second["subsurface_unified_result"]["final"],
                         continuous["subsurface_unified_result"]["final"])
    assert second["state"]["cells"][4]["depression_storage_m3"] > 0
    assert second["balances"]["deep"]["residual_j"] == pytest.approx(0.0, abs=1e-3)


def test_endogenous_deposition_opens_drainage_and_integrated_restart_matches():
    offsets = (0., 0., 0., 0., 0., 0., 0., 3.0, 7.999999)
    cfg = replace(_config(), duration_years=3,
                  initial_elevation_offsets_m_by_cell=offsets)
    continuous = run_regional_segment(_initial_states(), _identity(), config=cfg,
                                      segment_years=3)
    first = run_regional_segment(_initial_states(), _identity(), config=cfg,
                                 segment_years=1)
    split = run_regional_segment(_initial_states(), _identity(), config=cfg,
                                 segment_years=2, checkpoint=first["checkpoint"])
    state = continuous["state"]
    assert state["initial_condition_events"][-1]["kind"] == \
        "INITIAL_DRAINAGE_CONNECTIVITY_DIFFERENCE_FROM_REFERENCE"
    route_changes = [e for e in state["routing_events"]
                     if e["kind"] == "DRAINAGE_CONNECTIVITY_CHANGED"]
    assert any(e["detected_at_year"] == 1 and
               e["previous_targets"]["4"] == -1 and
               e["updated_targets"]["4"] == 7 and
               e["cause"] == "EROSION_DEPOSITION_OR_UPLIFT_CHANGED_TOPOGRAPHY"
               for e in route_changes)
    assert state["records"][0]["drainage_targets_used"]["4"] == -1
    assert state["records"][0]["drainage_targets_after_geomorphology"]["4"] == 7
    assert all(cell["cumulative_uplift_m"] == 0.0 for cell in state["cells"])
    assert state["cells"][4]["deposits"]
    assert first["state"]["cells"][4]["depression_storage_m3"] > 0
    assert state["cells"][5]["depression_storage_m3"] > 0
    assert state["cells"][4]["depression_storage_m3"] == 0.0
    for record in state["records"]:
        water = record["water_balance_m3"]
        solid = record["solid_mass_balance_kg"]
        assert abs(water["residual"]) <= water["roundoff_tolerance"]
        assert all(abs(row["residual_m3"]) <= row["roundoff_tolerance_m3"]
                   for row in water["per_cell"])
        assert abs(solid["residual"]) <= solid["roundoff_tolerance_kg"]
        assert all(abs(row["local_residual_kg"]) <= row["roundoff_tolerance_kg"]
                   for row in solid["per_cell"])
    assert continuous["balances"]["deep"]["residual_j"] == pytest.approx(0.0, abs=1e-3)
    assert continuous["balances"]["deep"]["final_inventory_j"] == pytest.approx(
        continuous["balances"]["deep"]["initial_inventory_j"], abs=1e-3)
    assert continuous["balances"]["deep"]["source_j"] == 0.0
    assert continuous["balances"]["deep"]["thermal_transfer_j"] == 0.0
    assert continuous["balances"]["deep"]["mechanical_work_transfer_j"] == 0.0
    for record in state["records"]:
        for load in record["geologic_load_by_cell"]:
            assert load["geometry_balance_residual_m"] == pytest.approx(0.0, abs=1e-12)
    _assert_nested_close(split["state"], state)
    _assert_nested_close(split["subsurface_unified_result"]["final"],
                         continuous["subsurface_unified_result"]["final"])
