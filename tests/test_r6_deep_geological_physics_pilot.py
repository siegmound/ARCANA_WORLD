from __future__ import annotations

import math

import pytest

from arcana_worldsim.r6.deep_geological_physics_pilot import (
    DeepCell, GeologyState, ModalMaterial, PilotConfig, run_canon_guided_pilot,
)
from test_r6_tectonic_deep_pilot import _state


def _inputs(*, zeta=(0.4, 0.7), source=0.0, loss=0.0, coupling=(0.6, 0.8)):
    geology = tuple(GeologyState(
        f"cell-{i}", ModalMaterial(f"material-{i}", 2800.0 + 500 * i,
                                   1000.0 + 200 * i, 2.5 + 0.8 * i,
                                   coupling[i], 0.3 if i == 0 else 0.2,
                                   0.05 + 0.03 * i), 0.0, "synthetic-T0")
        for i in range(2))
    cells = (
        DeepCell("cell-0", 100.0, 0.0, zeta[0], 0.5,
                 geological_source_w=source, loss_rate_per_year=loss),
        DeepCell("cell-1", 20.0, 0.0, zeta[1], 0.8),
    )
    return geology, cells


def test_two_cell_ledger_closes_and_transfers_are_equal_opposite():
    geology, cells = _inputs()
    result = run_canon_guided_pilot(_state(), geology=geology, deep_cells=cells)
    ledger = result["energy_ledgers"]
    assert ledger["material_to_deep_conversion_j"] == 0.0
    assert ledger["solar_energy_j"] == 0.0
    assert ledger["balance_residual_j"] == pytest.approx(0.0, abs=1e-12)
    for row in result["records"]:
        assert row["transport_flux_0_to_1_j"] != 0.0
        assert row["transport_fraction_this_step"] <= 0.5
        assert row["energy_balance_residual_j"] == pytest.approx(0.0, abs=1e-12)
    assert all(math.isfinite(v) and v >= 0 for v in ledger["final_inventory_j_by_cell"])


def test_modal_response_changes_transport_without_thermal_conductivity_proxy():
    geology, cells = _inputs()
    baseline = run_canon_guided_pilot(_state(), geology=geology, deep_cells=cells)
    changed = list(geology)
    changed[1] = GeologyState("cell-1", ModalMaterial("material-1", 3300, 1200, 3.3,
        0.1, 1.1, 0.2), 0.0, "synthetic-T0")
    altered = run_canon_guided_pilot(_state(), geology=tuple(changed), deep_cells=cells)
    assert baseline["energy_ledgers"]["final_inventory_j_by_cell"] != altered["energy_ledgers"]["final_inventory_j_by_cell"]
    assert geology[1].material.thermal_conductivity_w_m_k == changed[1].material.thermal_conductivity_w_m_k


def test_accessibility_and_structure_change_diagnostic_not_deep_stock():
    geology, cells = _inputs()
    base = run_canon_guided_pilot(_state(), geology=geology, deep_cells=cells)
    low_access = run_canon_guided_pilot(_state(), geology=geology,
        deep_cells=_inputs(zeta=(0.4, 0.1))[1])
    no_extension = run_canon_guided_pilot(_state(), geology=geology, deep_cells=cells,
        config=PilotConfig(extension_velocity_m_per_year=0.0))
    assert base["energy_ledgers"]["final_inventory_j_by_cell"] == low_access["energy_ledgers"]["final_inventory_j_by_cell"]
    assert base["energy_ledgers"]["accessible_free_inventory_j_by_cell"] != low_access["energy_ledgers"]["accessible_free_inventory_j_by_cell"]
    assert base["energy_ledgers"]["final_inventory_j_by_cell"] == no_extension["energy_ledgers"]["final_inventory_j_by_cell"]
    assert base["energy_ledgers"]["accessible_free_inventory_j_by_cell"] != no_extension["energy_ledgers"]["accessible_free_inventory_j_by_cell"]


def test_mobility_source_and_loss_each_have_expected_separate_effects():
    geology, cells = _inputs()
    low = run_canon_guided_pilot(_state(), geology=geology, deep_cells=cells,
        config=PilotConfig(mobility_per_year=0.01))
    high = run_canon_guided_pilot(_state(), geology=geology, deep_cells=cells,
        config=PilotConfig(mobility_per_year=0.2))
    isolated = run_canon_guided_pilot(_state(), geology=geology, deep_cells=cells,
        config=PilotConfig(mobility_per_year=0.0))
    sourced_inputs = _inputs(source=1e-6)
    sourced = run_canon_guided_pilot(_state(), geology=sourced_inputs[0], deep_cells=sourced_inputs[1])
    lossy_inputs = _inputs(loss=0.05)
    lossy = run_canon_guided_pilot(_state(), geology=lossy_inputs[0], deep_cells=lossy_inputs[1])
    assert low["energy_ledgers"]["final_inventory_j_by_cell"] != high["energy_ledgers"]["final_inventory_j_by_cell"]
    assert isolated["energy_ledgers"]["final_inventory_j_by_cell"] == [100.0, 20.0]
    assert all(row["transport_flux_0_to_1_j"] == 0.0 for row in isolated["records"])
    assert sourced["energy_ledgers"]["geological_source_j"] > 0
    assert sourced["energy_ledgers"]["final_inventory_j_by_cell"] != list((100.0, 20.0))
    assert lossy["energy_ledgers"]["losses_j"] > 0
    assert lossy["energy_ledgers"]["balance_residual_j"] == pytest.approx(0.0, abs=1e-12)


def test_zero_inventory_without_sources_does_not_recharge_and_solar_requires_source():
    geology, cells = _inputs()
    empty = tuple(DeepCell(c.cell_id, 0.0, 0.0, c.accessibility_zeta,
                           c.geological_accessibility_a_x) for c in cells)
    result = run_canon_guided_pilot(_state(), geology=geology, deep_cells=empty)
    assert result["energy_ledgers"]["final_inventory_j_by_cell"] == [0.0, 0.0]
    with pytest.raises(ValueError, match="SOLAR_SOURCE_REQUIRES_EXPLICIT"):
        run_canon_guided_pilot(_state(), geology=geology, deep_cells=cells,
            config=PilotConfig(solar_source_enabled=True))
    solar = run_canon_guided_pilot(_state(), geology=geology, deep_cells=empty,
        config=PilotConfig(solar_source_enabled=True, solar_flux_w=2.0))
    assert solar["energy_ledgers"]["solar_energy_j"] > 0
    assert solar["energy_ledgers"]["balance_residual_j"] == pytest.approx(0.0, abs=1e-8)


def test_incompatible_cell_identity_and_unqualified_modal_inputs_fail_closed():
    geology, cells = _inputs()
    bad = (GeologyState("other", geology[1].material, 0.0, "synthetic-T0"), geology[1])
    with pytest.raises(ValueError, match="CELL_ID_BINDING_MISMATCH"):
        run_canon_guided_pilot(_state(), geology=bad, deep_cells=cells)
    invalid_material = ModalMaterial("m", 2800, 1000, 2.5, 0.2, 0.1, 0.0,
                                     modal_parameter_authority="MEASURED")
    with pytest.raises(ValueError, match="UNQUALIFIED_MODAL_AUTHORITY"):
        invalid_material.validate()
