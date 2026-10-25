"""Dependency-free tests for regional surface routing and its restart state."""
from dataclasses import replace

import pytest

from arcana_worldsim.r6.regional_geological_evolution import (
    RegionalConfig, RegionalModelError, _routing_order, advance_region,
    create_synthetic_region, seal_regional_checkpoint,
    verify_regional_checkpoint,
)


IDENTITY = {
    "status": "SYNTHETIC_FIXTURE_ONLY",
    "t0_boundary_id": "SYNTHETIC_T0_EDGE",
    "support_cells": [
        {"support_id": "R6G1D-R091-C028", "plate_id": 11},
        {"support_id": "R6G1D-R091-C029", "plate_id": 5},
    ],
}


def test_fixed_and_dynamic_start_from_the_observed_baseline_network():
    fixed = RegionalConfig(duration_years=3, routing_mode="FIXED_BASELINE")
    dynamic = replace(fixed, routing_mode="DYNAMIC_TOPOGRAPHY")
    expected = {"0": 1, "1": 2, "2": 5, "3": 4, "4": 7,
                "5": 8, "6": 7, "7": 8, "8": None}
    assert create_synthetic_region(fixed, source_identity=IDENTITY)[
        "baseline_drainage_targets"] == expected
    assert create_synthetic_region(dynamic, source_identity=IDENTITY)[
        "drainage_targets"] == expected
    a = advance_region(create_synthetic_region(fixed, source_identity=IDENTITY),
                      years=1, config=fixed)
    b = advance_region(create_synthetic_region(dynamic, source_identity=IDENTITY),
                      years=1, config=dynamic)
    assert a["records"][0]["drainage_targets_used"] == expected
    assert b["records"][0]["drainage_targets_used"] == expected


def test_topographic_perturbation_changes_route_and_accumulates_water():
    base = RegionalConfig(duration_years=3)
    offsets = (0., 0., 0., 0., 0., 0., 0., 6., 0.)
    perturbed = replace(base, initial_elevation_offsets_m_by_cell=offsets)
    a = advance_region(create_synthetic_region(base, source_identity=IDENTITY),
                       years=1, config=base)
    b = advance_region(create_synthetic_region(perturbed, source_identity=IDENTITY),
                       years=1, config=perturbed)
    assert a["records"][0]["drainage_targets_used"]["4"] == 7
    assert b["records"][0]["drainage_targets_used"]["4"] == -1
    assert b["unperturbed_reference_drainage_targets"]["4"] == 7
    assert any(event["kind"] == "INITIAL_DRAINAGE_CONNECTIVITY_DIFFERENCE_FROM_REFERENCE"
               for event in b["initial_condition_events"])
    sink = b["cells"][4]
    assert sink["depression_storage_m3"] > 0
    assert sink["water_storage_m3"] >= sink["depression_storage_m3"]
    assert b["records"][0]["water_balance_m3"]["residual"] == pytest.approx(0.0)
    solid = b["records"][0]["solid_mass_balance_kg"]
    assert abs(solid["residual"]) <= solid["roundoff_tolerance_kg"]
    assert all(abs(row["local_residual_kg"]) <= row["roundoff_tolerance_kg"]
               for row in solid["per_cell"])
    water = b["records"][0]["water_balance_m3"]
    assert all(abs(row["residual_m3"]) <= row["roundoff_tolerance_m3"]
               for row in water["per_cell"])
    assert b["cells"][8]["deposits"] != a["cells"][8]["deposits"]


def test_uplift_rebuilds_dynamic_route_and_fixed_mode_keeps_baseline():
    uplift = (0., 0., 0., 0., 0., 0., 0., 6., 0.)
    dynamic = RegionalConfig(duration_years=3,
        prescribed_uplift_m_year_by_cell=uplift)
    fixed = replace(dynamic, routing_mode="FIXED_BASELINE")
    dyn = advance_region(create_synthetic_region(dynamic, source_identity=IDENTITY),
                         years=1, config=dynamic)
    fix = advance_region(create_synthetic_region(fixed, source_identity=IDENTITY),
                         years=1, config=fixed)
    assert dyn["records"][0]["drainage_targets_used"]["4"] == -1
    assert fix["records"][0]["drainage_targets_used"]["4"] == 7
    assert any(event["kind"] == "DRAINAGE_CONNECTIVITY_CHANGED"
               and event["updated_targets"]["4"] == -1
               for event in dyn["records"][0]["events"])
    assert dyn["cells"][7]["cumulative_uplift_m"] == 6.0
    assert fix["cells"][4]["water_storage_m3"] > 0
    assert not any(event.get("kind") == "WATER_ROUTING"
                   and event.get("source_cell_id") == "SYNTHETIC_BASIN_3X3:C04"
                   and event.get("destination_cell_id") == "SYNTHETIC_BASIN_3X3:C07"
                   for event in fix["records"][0]["events"])


def test_b5_hydrology_needs_explicit_surface_edge_only():
    blocked = create_synthetic_region(RegionalConfig(), source_identity=IDENTITY)
    connected_cfg = replace(RegionalConfig(), hydraulic_connectivity_edges=((4, 5),))
    connected = create_synthetic_region(connected_cfg, source_identity=IDENTITY)
    assert blocked["drainage_targets"]["4"] == 7
    assert connected["drainage_targets"]["4"] == 5
    interface = connected["interfaces"][0]
    assert interface["mechanical_continuity"] == "UNKNOWN_NOT_INFERRED"
    assert interface["deep_transport"] == "DISABLED"
    with pytest.raises(RegionalModelError, match="HYDRAULIC_EDGE_INVALID"):
        replace(RegionalConfig(), hydraulic_connectivity_edges=((4, 8),)).validate()


def test_route_is_acyclic_and_region_checkpoint_restart_preserves_sink_stock():
    offsets = (0., 0., 0., 0., 0., 0., 0., 6., 0.)
    config = RegionalConfig(duration_years=3,
        initial_elevation_offsets_m_by_cell=offsets)
    initial = create_synthetic_region(config, source_identity=IDENTITY)
    continuous = advance_region(initial, years=3, config=config)
    first = advance_region(initial, years=1, config=config)
    checkpoint = seal_regional_checkpoint(first)
    resumed = advance_region(verify_regional_checkpoint(checkpoint), years=2,
                             config=config)
    assert resumed == continuous
    assert resumed["cells"][4]["depression_storage_m3"] > 0
    for record in resumed["records"]:
        assert sorted(_routing_order(record["drainage_targets_used"])) == list(range(9))
    for cell, load in zip(resumed["cells"],
                          resumed["records"][-1]["geologic_load_by_cell"]):
        assert load["cell_id"] == cell["cell_id"]
        assert load["area_m2"] == cell["area_m2"]
        assert load["deposited_kg"] == pytest.approx(cell["cumulative_deposited_kg"])
        assert load["column_equivalent_pressure_change_pa"] == pytest.approx(
            load["surface_load_change_kg"] * 9.80665 / load["area_m2"])
