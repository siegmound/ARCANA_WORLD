from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("fastscapelib")

from src.arcana_worldsim.r6.fastscapelib_surface_coupling import (  # noqa: E402
    SurfaceCouplingError,
    continue_coupled_segment,
    raster_to_region_mapping,
    run_coupled_segment,
    verify_coupling_checkpoint,
)


def test_spl_erosion_transfers_substrate_mass_to_r6_and_updates_hydrology():
    result = run_coupled_segment(years=2, k_coef=2.0e-4, precipitation_m_year=0.15)
    transfers = [step["spl"] for step in result["steps"]]
    assert sum(row["total_mass_kg"] for row in transfers) > 0
    assert all(row["max_adjacent_slope_change"] > 0 for row in transfers)
    for record, residual in zip(result["regional_state"]["records"],
                                result["balances"]["solid_mass_residual_kg_by_year"]):
        assert abs(residual) <= record["solid_mass_balance_kg"]["roundoff_tolerance_kg"]
    assert all(abs(value) <= record["water_balance_m3"]["roundoff_tolerance"]
               for record, value in zip(result["regional_state"]["records"],
                                        result["balances"]["water_residual_m3_by_year"]))
    for record in result["regional_state"]["records"]:
        for cell in record["geologic_load_by_cell"]:
            scale = max(1.0, abs(cell["surface_elevation_m"]))
            assert abs(cell["geometry_balance_residual_m"]) <= (
                64 * np.finfo(np.float64).eps * scale)
    assert abs(result["balances"]["SPL_mass_transfer_identity_residual_kg"]) < 1e-6
    assert result["balances"]["all_material_stocks_nonnegative"]
    assert result["final"]["substrate_mass_kg"] < sum(result["initial"]["regional_solid_stock_kg_by_cell"])
    assert result["final"]["deep_state"] == "NOT_MODIFIED_NO_DEEP_EXCHANGE_LAW"
    assert len(result["final"]["regional_surface_route_targets"]) == 9
    assert result["regional_state"]["routing_events"]


def test_zero_erosion_control_leaves_solid_inventory_unchanged():
    result = run_coupled_segment(years=2, k_coef=0.0, precipitation_m_year=0.15)
    assert all(step["spl"]["total_mass_kg"] == 0 for step in result["steps"])
    assert result["final"]["regional_solid_stock_kg_by_cell"] == result["initial"]["regional_solid_stock_kg_by_cell"]
    assert all(abs(value) < 1e-6 for value in result["balances"]["water_residual_m3_by_year"])
    assert result["regional_state"]["routing_events"] == []


def test_area_mapping_is_complete_nonoverlapping_and_exact():
    mapping = raster_to_region_mapping()
    nodes = [(item["row"], item["column"])
             for cell in mapping["cells"] for item in cell["raster_nodes"]]
    assert len(nodes) == len(set(nodes)) == 36
    assert sorted(nodes) == [(r, c) for r in range(6) for c in range(6)]
    assert sum(cell["area_m2"] for cell in mapping["cells"]) == mapping["raster_area_sum_m2"]
    assert all(cell["area_m2"] == 1_000_000.0 for cell in mapping["cells"])


def test_checkpoint_restart_matches_continuous_and_rejects_tampering():
    continuous = run_coupled_segment(years=2, planned_years=2)
    first = run_coupled_segment(years=1, planned_years=2)
    checkpoint = verify_coupling_checkpoint(first["continuation_checkpoint"])
    resumed = continue_coupled_segment(checkpoint, years=1)
    assert continuous["regional_state"] == resumed["regional_state"]
    np.testing.assert_array_equal(continuous["final"]["fine_bedrock_m"], resumed["final"]["fine_bedrock_m"])
    corrupted = dict(checkpoint)
    corrupted["fine_bedrock_m"] = [[0.0] * 6 for _ in range(6)]
    with pytest.raises(SurfaceCouplingError, match="COUPLING_CHECKPOINT_INVALID"):
        verify_coupling_checkpoint(corrupted)
