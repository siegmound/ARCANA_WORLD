from __future__ import annotations

from dataclasses import replace

import pytest

from arcana_worldsim.r6.deep_geological_physics_pilot import (
    PilotConfig, ReducedStateNodeMapping, RoleModalParameters,
    map_reduced_state_material_nodes, run_canon_guided_pilot,
)
from test_r6_tectonic_deep_pilot import _state


ROLE_MODAL = (
    RoleModalParameters("CRUST", 0.6, 0.3, 0.05),
    RoleModalParameters("MANTLE", 0.8, 0.2, 0.08),
)


def _mapping(state):
    return ReducedStateNodeMapping(
        support_id="R6G1D-R091-C029", trajectory_id="DIRECT-TEST-C029",
        sequence=7, state_payload_sha256="a" * 64,
        mapping_id="TWO_ADJACENT_NODE_INTERFACE_TEST", node_indices=(25, 26),
    )


def _setup(state=None, modal=ROLE_MODAL, zeta=(0.4, 0.7)):
    state = state or _state()
    identity = _mapping(state)
    mapped = map_reduced_state_material_nodes(
        state, identity=identity, modal_parameters_by_role=modal,
    )
    cells = mapped.deep_cells(inventory_j=(100.0, 20.0), zeta=zeta, a_x=(0.5, 0.8))
    return state, identity, mapped, cells


def test_reduced_state_materials_are_mapped_with_distinct_provenance_and_heat_diagnostic():
    state, identity, mapped, cells = _setup()
    rows = mapped.mapping_payload["samples"]
    assert mapped.mapping_payload["support_id"] == identity.support_id
    assert mapped.mapping_payload["trajectory_id"] == identity.trajectory_id
    assert [row["node_index_zero_based"] for row in rows] == [25, 26]
    assert [row["material_role_id"] for row in rows] == ["CRUST", "MANTLE"]
    for position, (idx, row) in enumerate(zip((25, 26), rows)):
        material = state.materials[idx]
        assert row["rho_kg_m3"] == material.rho_kg_m3
        assert row["cp_j_kg_k"] == material.cp_j_kg_k
        assert row["k_w_m_k"] == material.k_w_m_k
        assert row["radiogenic_w_m3"] == material.radiogenic_w_m3
        assert row["temperature_k"] == state.temperature_k[idx]
        assert row["material_coordinate_xi"] == state.material_coordinate[idx]
        assert row["coordinate_z_m"] == state.material_coordinate[idx] * state.lithosphere_m
        assert row["cell_id"] == cells[position].cell_id

    diag = mapped.interface_thermal_diagnostics
    left, right = state.materials[25], state.materials[26]
    dz = (state.material_coordinate[26] - state.material_coordinate[25]) * state.lithosphere_m
    z_left = state.material_coordinate[25] * state.lithosphere_m
    z_right = state.material_coordinate[26] * state.lithosphere_m
    resistance_area = (state.crust_m - z_left) / left.k_w_m_k + (z_right - state.crust_m) / right.k_w_m_k
    expected = -state.width_m * (state.temperature_k[26] - state.temperature_k[25]) / resistance_area
    assert diag["conductive_flux_0_to_1_w"] == pytest.approx(expected)
    assert diag["material_boundary_z_m"] == state.crust_m
    assert diag["radiogenic_power_is_deep_source"] is False
    assert diag["diagnostic"].endswith("NOT_A_DEEP_SOURCE")
    assert len(set(c.cell_id for c in cells)) == 2


def test_deformation_keeps_node_roles_and_cell_ids_but_updates_coordinates_and_state_identity():
    state, identity, mapped, cells = _setup()
    result = run_canon_guided_pilot(
        state, geology=mapped.geology, deep_cells=cells,
        config=PilotConfig(duration_years=3.0, step_years=1.0),
        material_mapping=identity, modal_parameters_by_role=ROLE_MODAL,
    )
    snapshots = result["reduced_state_material_mappings"]
    assert [s["sequence"] for s in snapshots] == [7, 8, 9, 10]
    assert len({sample["cell_id"] for sample in snapshots[-1]["samples"]}) == 2
    assert [r["material_role_id"] for r in snapshots[0]["samples"]] == ["CRUST", "MANTLE"]
    assert [r["material_role_id"] for r in snapshots[-1]["samples"]] == ["CRUST", "MANTLE"]
    assert snapshots[-1]["samples"][1]["coordinate_z_m"] != snapshots[0]["samples"][1]["coordinate_z_m"]
    assert snapshots[-1]["state_payload_sha256"] != snapshots[0]["state_payload_sha256"]
    for row in result["records"]:
        assert row["interface_thermal_diagnostics"]["radiogenic_power_is_deep_source"] is False
        assert row["energy_balance_residual_j"] == pytest.approx(0.0, abs=1e-12)
        assert row["geological_source_j_by_cell"] == [0.0, 0.0]
    assert result["energy_ledgers"]["material_to_deep_conversion_j"] == 0.0
    assert sum(result["energy_ledgers"]["final_inventory_j_by_cell"]) == pytest.approx(120.0)
    assert result["energy_ledgers"]["balance_residual_j"] == pytest.approx(0.0, abs=1e-12)


def test_thermal_conductivity_change_affects_flux_diagnostic_not_deep_transport():
    state, identity, mapped, cells = _setup()
    materials = list(state.materials)
    materials[25] = replace(materials[25], k_w_m_k=7.0)
    altered_state = replace(state, materials=tuple(materials))
    altered_mapping = map_reduced_state_material_nodes(
        altered_state, identity=identity, modal_parameters_by_role=ROLE_MODAL,
    )
    altered_cells = altered_mapping.deep_cells(inventory_j=(100.0, 20.0), zeta=(0.4, 0.7), a_x=(0.5, 0.8))
    base_run = run_canon_guided_pilot(state, geology=mapped.geology, deep_cells=cells,
        material_mapping=identity, modal_parameters_by_role=ROLE_MODAL)
    altered_run = run_canon_guided_pilot(altered_state, geology=altered_mapping.geology,
        deep_cells=altered_cells, material_mapping=identity, modal_parameters_by_role=ROLE_MODAL)
    assert mapped.interface_thermal_diagnostics["conductive_flux_0_to_1_w"] != altered_mapping.interface_thermal_diagnostics["conductive_flux_0_to_1_w"]
    assert base_run["energy_ledgers"]["final_inventory_j_by_cell"] == altered_run["energy_ledgers"]["final_inventory_j_by_cell"]


def test_structural_access_perturbation_changes_accessible_diagnostic_only():
    state, identity, mapped, cells = _setup()
    base = run_canon_guided_pilot(state, geology=mapped.geology, deep_cells=cells,
        material_mapping=identity, modal_parameters_by_role=ROLE_MODAL)
    perturbed = run_canon_guided_pilot(state, geology=mapped.geology, deep_cells=cells,
        material_mapping=identity, modal_parameters_by_role=ROLE_MODAL,
        structure_accessibility_perturbation=(0.0, 0.15))
    assert base["energy_ledgers"]["final_inventory_j_by_cell"] == perturbed["energy_ledgers"]["final_inventory_j_by_cell"]
    assert base["energy_ledgers"]["accessible_free_inventory_j_by_cell"] != perturbed["energy_ledgers"]["accessible_free_inventory_j_by_cell"]


def test_missing_role_configuration_or_nonadjacent_nodes_fail_closed():
    state = _state()
    identity = _mapping(state)
    with pytest.raises(ValueError, match="SYNTHETIC_MODAL_PARAMETERS_MISSING_FOR_ROLE"):
        map_reduced_state_material_nodes(state, identity=identity, modal_parameters_by_role=ROLE_MODAL[:1])
    bad = replace(identity, node_indices=(26, 25))
    with pytest.raises(ValueError, match="ORDERED_INTERIOR_NODES"):
        map_reduced_state_material_nodes(state, identity=bad, modal_parameters_by_role=ROLE_MODAL)
