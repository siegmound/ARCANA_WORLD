from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

from arcana_worldsim.r6.pre_orbdata_heat_flow import HWR2
from arcana_worldsim.r6.pre_orbdata_runtime_package import (
    DATA_NAME, FIELDS, MANIFEST_NAME, MODE, RuntimeNode, _temperature,
    _flux, validate_column,
)
from arcana_worldsim.r6.pre_orbdata_thermal_column import (
    LayerMaterial, continental_column, ocean_column,
)


def test_fixed_polynomial_conversion_preserves_continental_column():
    column = continental_column(q_surface=0.06, crust_m=35_000, total_lithosphere_m=135_000)
    layer1, layer2 = validate_column(column, 0.06, 280.0, 2.5, 3.3)
    assert layer1[2] == 0.0
    assert layer2[2] == 0.0
    assert _temperature(layer1, 0.0) == pytest.approx(280.0, abs=1e-10)
    assert _flux(layer1, 0.0, 2.5) == pytest.approx(0.06, abs=1e-12)
    assert _temperature(layer1, column.crust_m) == pytest.approx(column.moho_temperature_k, abs=2e-7)
    assert _temperature(layer2, column.crust_m) == pytest.approx(column.moho_temperature_k, abs=2e-7)
    assert _flux(layer1, column.crust_m, 2.5) == pytest.approx(column.moho_flux_w_m2, abs=2e-12)
    assert _flux(layer2, column.crust_m, 3.3) == pytest.approx(column.moho_flux_w_m2, abs=2e-12)
    assert _temperature(layer2, column.lab_m) == pytest.approx(column.lab_temperature_k, abs=2e-7)
    assert _flux(layer2, column.lab_m, 3.3) == pytest.approx(column.lab_flux_w_m2, abs=2e-12)


def test_fixed_polynomial_conversion_preserves_ocean_profile():
    model = HWR2()
    q = model.flux(50.0)
    column = ocean_column(age_ma=50.0, crust_m=6500.0, q_surface=q, model=model)
    p1, p2 = validate_column(column, q, 280.0, 2.2, 3.3)
    assert _temperature(p1, 0.0) == pytest.approx(280.0, abs=2e-7)
    assert _flux(p1, 0.0, 2.2) == pytest.approx(q, abs=2e-12)
    assert _temperature(p1, column.crust_m) == pytest.approx(_temperature(p2, column.crust_m), abs=2e-7)
    assert _flux(p1, column.crust_m, 2.2) == pytest.approx(_flux(p2, column.crust_m, 3.3), abs=2e-12)
    assert _temperature(p2, column.lab_m) == pytest.approx(column.lab_temperature_k, abs=2e-7)
    assert _flux(p2, column.lab_m, 3.3) == pytest.approx(column.lab_flux_w_m2, abs=2e-12)


def test_ridge_keeps_physical_age_zero_and_uses_positive_derived_age(monkeypatch):
    model = HWR2()
    observed = []
    original = HWR2._exponents

    def observe(self, age):
        observed.append(age)
        return original(self, age)

    monkeypatch.setattr(HWR2, "_exponents", observe)
    column = ocean_column(age_ma=0.0, crust_m=6500.0, q_surface=0.3, ridge=True, model=model)
    assert column.age_ma == 0.0
    assert column.q_surface_w_m2 == 0.3
    assert column.effective_age_ma is not None and column.effective_age_ma > 0
    assert observed and all(age > 0 for age in observed)


def test_runtime_record_format_is_finite_and_fixed_width():
    assert len(FIELDS) == 51
    values = [1] + [0.0] * (len(FIELDS) - 1)
    line = RuntimeNode(tuple(values)).line()
    assert len(line.split()) == len(FIELDS)
    assert line.startswith("1 0.00000000000000000e+00")
    assert "nan" not in line.lower() and "inf" not in line.lower()
    with pytest.raises(ValueError, match="NONFINITE"):
        RuntimeNode(tuple([1] + [float("nan")] * (len(FIELDS) - 1))).line()


def test_materialized_package_covers_all_nodes_with_owner_bound_state():
    # Inspect the actual deterministic package; no ShellSet process is invoked.
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    data = (root / DATA_NAME).read_bytes()
    projection = json.loads((root / "R6_PRE_ORBDATA_HEAT_FLOW_FEG_PROJECTION_V1.json").read_text(encoding="utf-8"))
    assert manifest["node_count"] == manifest["known_count"] == 64_442
    assert manifest["invalid_count"] == 0
    assert manifest["mixed_physical_support_count"] == 2697
    assert hashlib.sha256(data).hexdigest() == manifest["runtime_data_sha256"]
    assert data.startswith(f"{MODE} arcana_worldsim.r6.shellset_owner_bound_runtime.v1 64442\n".encode())
    lines = data.decode("ascii").splitlines()
    records = [line.split() for line in lines[1:]]
    assert len(records) == 64_442
    assert all(len(row) == len(FIELDS) for row in records)
    assert all(row[0] == str(index) for index, row in enumerate(records, 1))
    assert all(all(math.isfinite(float(x)) for x in row) for row in records)
    mixed_nodes = 0
    branch_counts = {1: 0, 2: 0, 3: 0}
    field = {name: i for i, name in enumerate(FIELDS)}
    cell_q = projection["cell_heat_flow_w_m2"]
    source = projection["cell_owner_source_fields"]
    for index, (record, lineage) in enumerate(zip(records, projection["lineage"]), 1):
        node = {key: float(record[pos]) for key, pos in field.items() if key != "node_id"}
        assert int(node["owner_row"]) == lineage["numerical_owner_cell_row_col"][0]
        assert int(node["owner_column"]) == lineage["numerical_owner_cell_row_col"][1]
        assert node["owner_domain_id"] == lineage["numerical_owner_domain_id"]
        assert node["surface_heat_flow_w_m2"] == projection["heat_flow_w_m2"][index - 1]
        assert node["surface_heat_flow_w_m2"] == cell_q[int(node["owner_row"])][int(node["owner_column"])]
        assert int(node["runtime_branch_code"]) == {
            "CONTINENTAL_AUTHORED_REFERENCE": 1,
            "GOVERNED_RIDGE_BOUNDARY": 2,
            "AUTHORIZED_POSITIVE_AGE_OCEAN": 3,
        }[lineage["numerical_owner_runtime_branch"]]
        assert int(node["mixed_support"]) == int(lineage["mixed_physical_support"])
        assert node["incident_domain_mask"] == sum(1 << (int(v)-1) for v in lineage["incident_physical_domain_ids"])
        branch = int(node["runtime_branch_code"])
        branch_counts[branch] += 1
        mixed_nodes += int(node["mixed_support"])
        row, col = int(node["owner_row"]), int(node["owner_column"])
        assert int(node["material_configuration_code"]) == 1
        assert int(node["crust_material_code"]) in (1, 2)
        assert int(node["mantle_material_code"]) == 1
        if branch == 2:
            assert node["physical_age_present"] == 1 and node["physical_age_ma"] == 0.0
            assert node["surface_heat_flow_w_m2"] == 0.3
            assert node["effective_age_present"] == 1 and node["effective_age_ma"] > 0
        elif branch == 3:
            assert node["physical_age_present"] == 1
            assert node["physical_age_ma"] == source["oceanic_lithosphere_age_ma"][row][col]
        else:
            assert node["physical_age_present"] == 0
            assert node["crust_thickness_m"] + node["mantle_lithosphere_thickness_m"] == pytest.approx(
                source["continental_reference_lithosphere_thickness_m"][row][col], abs=1e-8)
        assert node["layer1_z0_m"] == pytest.approx(0.0, abs=1e-10)
        assert node["layer1_z1_m"] == pytest.approx(node["crust_thickness_m"], abs=1e-8)
        assert node["layer2_z0_m"] == pytest.approx(node["crust_thickness_m"], abs=1e-8)
        assert node["layer2_z1_m"] == pytest.approx(node["lab_depth_m"], abs=1e-8)
        assert node["lab_depth_m"] == pytest.approx(node["crust_thickness_m"] + node["mantle_lithosphere_thickness_m"], abs=1e-8)
        p1 = (node["layer1_z0_m"],node["layer1_z1_m"],node["layer1_c3_k_m3"],node["layer1_c2_k_m2"],node["layer1_c1_k_m"],node["layer1_c0_k"])
        p2 = (node["layer2_z0_m"],node["layer2_z1_m"],node["layer2_c3_k_m3"],node["layer2_c2_k_m2"],node["layer2_c1_k_m"],node["layer2_c0_k"])
        assert _temperature(p1,node["crust_thickness_m"]) == pytest.approx(node["moho_temperature_k"],abs=2e-7)
        assert _temperature(p2,node["crust_thickness_m"]) == pytest.approx(node["moho_temperature_k"],abs=2e-7)
        assert _flux(p1, node["crust_thickness_m"], node["crust_conductivity_w_m_k"]) == pytest.approx(node["moho_flux_w_m2"],abs=2e-12)
        assert _flux(p2, node["crust_thickness_m"], node["mantle_conductivity_w_m_k"]) == pytest.approx(node["moho_flux_w_m2"],abs=2e-12)
        assert _temperature(p2,node["lab_depth_m"]) == pytest.approx(node["lab_temperature_k"],abs=2e-7)
        assert _flux(p2,node["lab_depth_m"],node["mantle_conductivity_w_m_k"]) == pytest.approx(node["lab_flux_w_m2"],abs=2e-12)
    assert mixed_nodes == manifest["mixed_physical_support_count"] == 2697
    assert branch_counts == {1: 14258, 2: 108, 3: 50076}
    assert manifest["preserved_gates"]["PRE_ORBDATA_ready"] is False
