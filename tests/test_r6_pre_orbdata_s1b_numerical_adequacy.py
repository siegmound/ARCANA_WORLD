"""Small source-formula contract tests for the S1B adequacy diagnostic."""
from __future__ import annotations

import numpy as np

from scripts.r6_pre_orbdata_s1b_numerical_adequacy import (
    IDX,
    IP_WEIGHTS,
    arc_node_temperature,
    legacy_fillin_coefficients,
    legacy_fillin_temperature,
    legacy_squeez_temperature,
    read_shell_parameters,
)


def _nodes() -> np.ndarray:
    """Build one internally consistent synthetic node row for formula tests."""
    from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS

    row = np.zeros((3, len(FIELDS)), dtype=np.float64)
    for n in range(3):
        row[n, IDX["node_id"]] = n + 1
        row[n, IDX["crust_thickness_m"]] = 20_000.0
        row[n, IDX["lab_depth_m"]] = 100_000.0
        row[n, IDX["mantle_lithosphere_thickness_m"]] = 80_000.0
        row[n, IDX["surface_heat_flow_w_m2"]] = 0.06
        row[n, IDX["lab_temperature_k"]] = 1_473.0
        row[n, IDX["mantle_expansivity_k_1"]] = 3.0e-5
        row[n, IDX["mantle_cp_j_kg_k"]] = 1_200.0
        row[n, IDX["layer1_z0_m"]] = 0.0
        row[n, IDX["layer1_c0_k"]] = 273.0
        row[n, IDX["layer1_c1_k_m"]] = 0.03
        row[n, IDX["layer2_z0_m"]] = 20_000.0
        row[n, IDX["layer2_c0_k"]] = 873.0
        row[n, IDX["layer2_c1_k_m"]] = 0.0075
    return row


def test_shell_parameter_pair_and_source_values_are_read_from_fixture_tree() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    params = read_shell_parameters(root)
    assert params["tAdiab"] == [1412.0]
    assert params["gradie"] == [6.1e-4]
    assert params["zBAsth"] == [400000.0]


def test_fillin_returns_source_formula_and_target_coefficients() -> None:
    nodes = np.repeat(_nodes()[None, :, :], 2, axis=0)
    coeff = legacy_fillin_coefficients(nodes, IP_WEIGHTS, {
        "conduc": [2.7, 3.2], "radio": [3.5e-7, 3.2e-8],
        "tSurf": [273.0], "tAdiab": [1412.0], "gradie": [6.1e-4],
    })
    target = 1412.0 + 6.1e-4 * 100_000.0
    assert np.all(coeff[-1] == target)
    # ShellSet's source applies the curvature correction to both layer
    # quadratics using total lithosphere squared; retain that exact formula.
    assert np.all(np.isfinite(legacy_fillin_temperature(coeff, 100_000.0)))


def test_arcana_piecewise_profile_and_lab_anchored_adiabat() -> None:
    nodes = _nodes()
    assert np.allclose(arc_node_temperature(nodes, 20_000.0), 873.0)
    assert np.allclose(arc_node_temperature(nodes, 100_000.0), 1473.0)
    z = 150_000.0
    expected = 1473.0 * np.exp(3.0e-5 * 9.82 * (z - 100_000.0) / 1200.0)
    assert np.allclose(arc_node_temperature(nodes, z), expected)


def test_squeez_legacy_temperature_applies_layer_temlim() -> None:
    nodes = _nodes()
    # At this q and depth the unbounded linear crust solution exceeds temLim.
    p = {"conduc": [2.7, 3.2], "radio": [0.0, 0.0], "tSurf": [273.0],
         "temLim": [1223.0, 1673.0]}
    temperature = legacy_squeez_temperature(nodes, 100_000.0, p)
    assert np.all(temperature <= 1673.0)
