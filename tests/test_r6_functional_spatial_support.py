from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import numpy as np
import pytest

from arcana_worldsim.r6.functional_development import (
    NodeMaterial, T0Profile, initial_reduced_state, pure_shear_thermal_step,
    state_from_payload,
)
from arcana_worldsim.r6.functional_spatial_support import (
    SpatialSupportError, audit_pair_5_11, classify_signed_extension,
    exact_face_plate_lookup, incident_cells, signed_boundary_velocity,
)

ROOT = Path(__file__).resolve().parents[1]


def test_cell_to_plate_join_is_complete_unique_and_insertion_order_independent():
    rows = [0, 0, 1, 1]
    columns = [0, 1, 0, 1]
    plates = [5, 11, 5, 11]
    first = exact_face_plate_lookup(rows, columns, plates, rows=2, columns=2)
    shuffled = exact_face_plate_lookup(rows[::-1], columns[::-1], plates[::-1], rows=2, columns=2)
    assert first == shuffled
    with pytest.raises(SpatialSupportError, match="INCOMPLETE"):
        exact_face_plate_lookup(rows[:3], columns[:3], plates[:3], rows=2, columns=2)
    with pytest.raises(SpatialSupportError, match="DUPLICATE"):
        exact_face_plate_lookup([0, 0, 1, 1], [0, 0, 0, 1], plates, rows=2, columns=2)


def test_canonical_edge_incident_cells_and_polar_unknown_fail_closed():
    assert incident_cells(5, 359, "EAST", rows=10, columns=360).second == (5, 0)
    assert incident_cells(5, 9, "NORTH", rows=10, columns=10).second == (6, 9)
    with pytest.raises(SpatialSupportError, match="POLAR"):
        incident_cells(9, 9, "NORTH", rows=10, columns=10)


def test_plate_side_assignment_unknowns_and_signed_extension_states():
    rates = {5: (0.0, 0.0, 1.0e-8), 11: (0.0, 0.0, -1.0e-8)}
    opening = signed_boundary_velocity(row=89, column=30, axis="EAST",
        first_plate=11, second_plate=5, plate_a=5, plate_b=11,
        euler_rad_per_year=rates, radius_m=6_371_000.0)["signed_opening_m_per_year"]
    flipped = signed_boundary_velocity(row=89, column=30, axis="EAST",
        first_plate=11, second_plate=5, plate_a=5, plate_b=11,
        euler_rad_per_year={5: rates[11], 11: rates[5]}, radius_m=6_371_000.0)["signed_opening_m_per_year"]
    assert opening > 0
    assert flipped == pytest.approx(-opening)
    assert classify_signed_extension(opening, 1e-9) == "EXTENSION"
    assert classify_signed_extension(0.0, 1e-9) == "ZERO_WITHIN_GOVERNED_TOLERANCE"
    assert classify_signed_extension(-opening, 1e-9) == "COMPRESSION"
    with pytest.raises(SpatialSupportError, match="PLATE_SIDE"):
        signed_boundary_velocity(row=89, column=30, axis="EAST",
            first_plate=7, second_plate=11, plate_a=5, plate_b=11,
            euler_rad_per_year=rates, radius_m=6_371_000.0)
    with pytest.raises(SpatialSupportError, match="UNKNOWN"):
        signed_boundary_velocity(row=89, column=30, axis="EAST",
            first_plate=5, second_plate=11, plate_a=5, plate_b=11,
            euler_rad_per_year={5: rates[5]}, radius_m=6_371_000.0)


@pytest.fixture(scope="module")
def real_pair_mapping():
    branch = subprocess.check_output(["git", "-C", str(ROOT), "branch", "--show-current"], text=True).strip()
    return audit_pair_5_11(ROOT, expected_branch=branch)


def test_real_partition_exactly_matches_pair_side_plate_and_crust_authority(real_pair_mapping):
    result = real_pair_mapping
    assert result["mapping_join"]["parent_cells"] == 64_800
    assert result["all_15_edges_classified"] is True
    assert len(result["edge_matrix"]) == 15
    for edge in result["edge_matrix"]:
        assert edge["PLATE_MAPPING"] == "PASS_EXACT_PARTITION_JOIN"
        assert edge["MATERIAL_ADMISSIBILITY"] == "PASS_B6N8N_ADMITTED"
        assert edge["THERMAL_AVAILABILITY"] == "PASS_AUTHORED_T0_CONTINENTAL_PROFILE_INPUTS"
        sides = edge["sides_plate_a_then_plate_b"]
        assert [side["plate_id"] for side in sides] == [5, 11]
        assert [side["parent_crust_class"] for side in sides] == [1, 1]
        assert all(side["parent_crust_class_semantics"] == "CONTINENTAL" for side in sides)
        assert all(side["physical_crust_domain_id"] in {2, 3, 4, 5, 6} for side in sides)
        assert all(side["support_id"].startswith("R6G1D-R") for side in sides)


def test_real_pair_selection_is_deterministic_and_uses_distinct_two_sided_profiles(real_pair_mapping):
    result = real_pair_mapping
    assert result["pair_event_census"]["eligibility"] == "ELIGIBLE_QUIESCENT"
    eligible = [row for row in result["edge_matrix"] if row["SECTION_ELIGIBILITY"] == "ELIGIBLE"]
    assert len(eligible) == 8
    ordered = sorted(eligible, key=lambda item: (item["parent_grid_edge"]["row"],
        item["parent_grid_edge"]["column"], item["parent_grid_edge"]["axis"], item["boundary_id"]))
    assert result["selected_boundary_id"] == ordered[(len(ordered) - 1) // 2]["boundary_id"]
    selected = next(row for row in result["edge_matrix"] if row["boundary_id"] == result["selected_boundary_id"])
    sides = selected["sides_plate_a_then_plate_b"]
    assert [side["plate_id"] for side in sides] == [5, 11]
    assert [side["t0_profile"]["support_lineage"]["native_column"] for side in sides] == ["29", "28"]
    assert sides[0]["t0_profile"]["temperature_k"] == sides[1]["t0_profile"]["temperature_k"]
    assert sides[0]["support_id"] != sides[1]["support_id"]
    assert sides[0]["t0_profile"]["scenario_id"] == sides[1]["t0_profile"]["scenario_id"]
    assert selected["junction_adjacent"] is False
    assert selected["signed_Ux_m_per_year"] > 0
    assert selected["Euler_census_abs_difference_m_per_year"] <= 1e-12


def test_restart_replay_is_deterministic_and_extension_only_kernel_rejects_compression():
    material = NodeMaterial("TEST_ROLE", 1.0, 1.0, 1.0, 0.0)
    profile = T0Profile("FIXTURE", "FIXTURE", "FIXTURE_ONLY", 1.0, 2.0,
        280.0, 282.0, 0.0, (0.0, 1.0, 2.0), (280.0, 281.0, 282.0),
        (material, material, material), ("FIXTURE_CRUST", "FIXTURE_MANTLE"), {})
    initial = initial_reduced_state(profile, initial_width_m=100.0)
    full, _ = pure_shear_thermal_step(initial, duration_s=1.0,
        extension_velocity_m_s=1e-9, maximum_kinematic_fraction_per_substep=0.0005)
    replay, _ = pure_shear_thermal_step(initial, duration_s=1.0,
        extension_velocity_m_s=1e-9, maximum_kinematic_fraction_per_substep=0.0005)
    assert full.payload() == replay.payload()
    first, _ = pure_shear_thermal_step(initial, duration_s=0.5,
        extension_velocity_m_s=1e-9, maximum_kinematic_fraction_per_substep=0.0005)
    reopened = state_from_payload(first.payload())
    second, _ = pure_shear_thermal_step(reopened, duration_s=0.5,
        extension_velocity_m_s=1e-9, maximum_kinematic_fraction_per_substep=0.0005)
    assert max(abs(a - b) for a, b in zip(full.temperature_k, second.temperature_k)) <= 1e-10
    assert all(np.isfinite(second.temperature_k))
    with pytest.raises(ValueError, match="COMPRESSION_NOT_ADMISSIBLE"):
        pure_shear_thermal_step(initial, duration_s=1.0, extension_velocity_m_s=-1e-9)


def test_development_path_does_not_import_or_publish_world_history():
    module_path = ROOT / "src/arcana_worldsim/r6/functional_spatial_support.py"
    runner_path = ROOT / "scripts/r6_functional_development_t_f2b.py"
    for path in (module_path, runner_path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {alias.name for node in ast.walk(tree)
                    if isinstance(node, ast.Import) for alias in node.names}
        imported.update(node.module or "" for node in ast.walk(tree)
                        if isinstance(node, ast.ImportFrom))
        assert not any("store" in name.lower() or "world_history" in name.lower()
                       for name in imported)
    text = runner_path.read_text(encoding="utf-8")
    assert '"world_history_mutated": False' in text
    assert '"canonical_publication": False' in text
