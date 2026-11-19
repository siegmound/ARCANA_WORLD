"""CREATED_NOT_RUN. Independent manufactured P1 oracles, no ARCANA data."""
from fractions import Fraction as F
import json
import math
import os
from pathlib import Path
import sys
import time

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments"))
from hr2_p1.model import Mesh, Parameters, Integrator, finite_volume_step, spherical_mesh
from hr2_p1.manufactured import (RADIUS_M, KAPPA_M2_YEAR, SPATIAL_END_YEAR,
    SPATIAL_MESHES, cell_average_mode, continuum_heights, errors, new_case,
    semidiscrete_latitude_heights)


def receipt(name, value):
    root = os.environ.get("HR2_P1_QUAL_OUTPUT")
    if root:
        path = Path(root) / name
        with path.open("x") as f:
            json.dump(value, f, indent=2)
            f.write("\n")


def test_independent_rational_2x2_local_patch():
    # Oracle hand calculation: areas=(1,2,3,4), h=(1,2,3,4), conductances
    # (1,2,3,4) on faces01,02,13,23. dt=1/10 gives signed transfers
    # (-1/10,-2/5,-3/5,-2/5), V_new=(3/2,9/2,9,15), total30.
    mesh = Mesh([1, 2, 3, 4], [0, 0, 1, 2], [1, 2, 3, 3],
                [1, 2, 3, 4], [1, 1, 1, 1], {"kind": "LOCAL_2X2_RATIONAL_ORACLE"})
    volumes = np.array([1., 4., 9., 16.])
    expected_transfer = [F(-1, 10), F(-2, 5), F(-3, 5), F(-2, 5)]
    expected = [F(3, 2), F(9, 2), F(9), F(15)]
    actual, diag, transfers = finite_volume_step(mesh, volumes, 1., .1)
    np.testing.assert_allclose(transfers, list(map(float, expected_transfer)), rtol=0, atol=2e-15)
    np.testing.assert_allclose(actual, list(map(float, expected)), rtol=0, atol=2e-14)
    assert math.fsum(map(float, actual)) == 30 and diag["external_polar_flux_m3"] == 0
    assert mesh.step_limit(1.) == float(F(1, 6))
    assert np.array_equal(volumes, [1, 4, 9, 16])  # Ownership: input untouched.
    with pytest.raises(ValueError, match="GUARD"):
        finite_volume_step(mesh, volumes, 1., .2)


@pytest.mark.parametrize("width,height", SPATIAL_MESHES)
def test_actual_spherical_geometry_faces_seam_and_poles(width, height):
    mesh = spherical_mesh(width, height, RADIUS_M)
    assert len(mesh.areas) == width * height
    assert len(mesh.first) == width * height + width * (height - 1)
    assert (mesh.lengths > 0).all() and (mesh.distances > 0).all()
    assert math.isclose(math.fsum(map(float, mesh.areas)), 4 * math.pi * RADIUS_M**2,
                        rel_tol=64 * np.finfo(float).eps)
    pairs = {tuple(sorted((int(i), int(j)))) for i, j in zip(mesh.first, mesh.second)}
    assert len(pairs) == len(mesh.first)
    for row in range(height):
        assert tuple(sorted((row * width, row * width + width - 1))) in pairs
    # No manufactured polar clique: pole-row non-edge endpoints cannot exchange.
    assert (0, width // 2) not in pairs
    assert all(0 <= i < width * height and 0 <= j < width * height for i, j in pairs)


@pytest.mark.parametrize("mode", ["latitude", "longitude"])
def test_16x8_fluxes_conservation_nonnegativity_and_constant_state(mode):
    case = new_case(16, 8, 1., mode)
    case.start_window(1.)
    initial = case.initial_volume
    maximum_guard = 0.
    while case.window is not None:
        row = case.step()
        maximum_guard = max(maximum_guard, row["guard_ratio"])
        assert row["external_polar_flux_m3"] == 0
        assert row["minimum_volume_m3"] >= 0
        assert abs(math.fsum(map(float, case.volumes)) - initial) <= case.cumulative_roundoff_bound
    assert maximum_guard <= 1
    constant = new_case(16, 8, 1., "constant")
    original = constant.volumes.copy()
    constant.start_window(1.)
    constant.finish_window()
    assert np.array_equal(constant.volumes, original)
    # A longitude-varying field produces a genuine seam flux, not a wall.
    other = new_case(16, 8, 1., "longitude")
    _, _, transfer = finite_volume_step(other.mesh, other.volumes, KAPPA_M2_YEAR,
                                        other.mesh.step_limit(KAPPA_M2_YEAR) / 2)
    seam = np.arange(15, 128, 16)
    assert np.isfinite(transfer[seam]).all()
    # The cell-average cosine field is symmetric about lambda=+/-pi, hence zero
    # flux exactly on the seam up to roundoff; shift a perturbation to test crossing.
    changed = other.volumes.copy()
    changed[15] += other.mesh.areas[15]
    _, _, crossed = finite_volume_step(other.mesh, changed, KAPPA_M2_YEAR,
                                      other.mesh.step_limit(KAPPA_M2_YEAR) / 2)
    assert crossed[15] > 0


def test_positive_spike_and_declared_mass():
    mesh = spherical_mesh(16, 8, RADIUS_M)
    h = np.zeros(128)
    h[0] = 1.
    case = Integrator(mesh, Parameters(KAPPA_M2_YEAR, 1., 2500.), h,
                      {"family": "DECLARED_TEST_SPIKE"})
    case.start_window(1.)
    case.finish_window()
    assert (case.volumes >= 0).all()
    volume = math.fsum(map(float, case.volumes))
    # Mass derives only from the explicitly declared uniform test density.
    assert abs(2500. * volume - 2500. * case.initial_volume) <= (
        2500. * case.cumulative_roundoff_bound + 16 * math.ulp(2500. * case.initial_volume))


def test_zero_diffusivity_and_negative_or_nonfinite_inputs():
    mesh = spherical_mesh(16, 8, RADIUS_M)
    old = mesh.areas * 8.
    actual, row, _ = finite_volume_step(mesh, old, 0., 1.)
    assert np.array_equal(actual, old) and row["step_limit_year"] is None
    for value in [-1., math.nan, math.inf]:
        bad = old.copy()
        bad[0] = value
        with pytest.raises(ValueError):
            finite_volume_step(mesh, bad, 1., .01)
    with pytest.raises(ValueError):
        finite_volume_step(mesh, old, -1., .01)
    with pytest.raises(ValueError):
        finite_volume_step(mesh, old, True, .01)
    with pytest.raises(ValueError):
        finite_volume_step(mesh, old, 1., True)


def test_invalid_geometry_and_parameter_admission():
    with pytest.raises(ValueError):
        spherical_mesh(16, 9, RADIUS_M)
    with pytest.raises(ValueError):
        Mesh([1, 1], [0.5], [1], [1], [1], {})
    with pytest.raises(ValueError):
        Mesh([1, 1], [0, 1], [1, 0], [1, 1], [1, 1], {})
    for rho in [0., -1., math.nan, True]:
        with pytest.raises(ValueError):
            Parameters(1., 1., rho).validate()


def test_rejected_schedule_does_not_mutate_accepted_state():
    case = new_case(16, 8, 1.)
    before = case.checkpoint()
    with pytest.raises(ValueError, match="UNSTABLE"):
        case.start_window(1., substeps=1)
    assert case.checkpoint() == before


def test_predeclared_temporal_convergence_isolated_from_spatial_error():
    reference = semidiscrete_latitude_heights(16, 8, 1.)
    probe = new_case(16, 8, 1.)
    minimum = math.ceil(1. / probe.mesh.step_limit(KAPPA_M2_YEAR))
    rows = []
    for factor in [1, 2, 4]:
        case = new_case(16, 8, 1.)
        case.start_window(1., substeps=minimum * factor)
        started = time.perf_counter()
        case.finish_window()
        rows.append({"substeps": minimum * factor, "dt_year": 1 / (minimum * factor),
                     "kernel_service_wall_s_including_checks": time.perf_counter() - started,
                     **errors(case.heights(), reference, case.mesh.areas),
                     "volume_residual_m3": math.fsum(map(float, case.volumes)) - case.initial_volume,
                     "volume_roundoff_bound_m3": case.cumulative_roundoff_bound})
    orders = [math.log(rows[i]["L2_m"] / rows[i+1]["L2_m"], 2) for i in range(2)]
    receipt("TEMPORAL_CONVERGENCE.json", {"rows": rows, "orders_L2": orders,
            "oracle": "analytic exact-in-time same-mesh latitude mode"})
    assert all(.9 <= order <= 1.2 for order in orders)


@pytest.mark.parametrize("mode", ["latitude", "longitude"])
def test_predeclared_fixed_time_spatial_convergence_to_256x128(mode):
    rows = []
    for width, height in SPATIAL_MESHES:
        case = new_case(width, height, SPATIAL_END_YEAR, mode)
        case.start_window(SPATIAL_END_YEAR)
        count = case.window["substeps"]
        started = time.perf_counter()
        case.finish_window()
        wall = time.perf_counter() - started
        reference = continuum_heights(width, height, SPATIAL_END_YEAR, mode)
        error = errors(case.heights(), reference, case.mesh.areas)
        half = new_case(width, height, SPATIAL_END_YEAR, mode)
        half.start_window(SPATIAL_END_YEAR, substeps=2 * count)
        half.finish_window()
        time_difference = errors(case.heights(), half.heights(), case.mesh.areas)["L2_m"]
        rows.append({"width": width, "height": height, "end_year": SPATIAL_END_YEAR,
                     "accepted_steps": count, **error, "half_dt_L2_difference_m": time_difference,
                     "kernel_service_wall_s_including_checks": wall,
                     "accepted_faces_per_s_including_checks": len(case.mesh.first) * count / wall,
                     "dt_histogram_hex_years": case.dt_histogram,
                     "volume_residual_m3": math.fsum(map(float, case.volumes)) - case.initial_volume,
                     "volume_roundoff_bound_m3": case.cumulative_roundoff_bound,
                     "minimum_height_m": float(case.heights().min())})
    orders = {key: [math.log(rows[i][key] / rows[i+1][key], 2) for i in range(4)]
              for key in ["L1_m", "L2_m", "Linf_m"]}
    receipt("SPATIAL_CONVERGENCE_" + mode + ".json", {"rows": rows, "orders": orders,
            "oracle": "area-averaged continuum mode, fixed physical end time"})
    assert all(row["half_dt_L2_difference_m"] <= .05 * row["L2_m"] for row in rows)
    assert all(p >= 1.5 for p in orders["L1_m"] + orders["L2_m"])
    assert all(p >= 1.5 for p in orders["Linf_m"])
