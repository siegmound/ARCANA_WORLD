"""Explicit artificial coefficients and independent continuum expectations.

None of these values is taken from, or assigned to, ARCANA global T0 fields.
"""
import math
import numpy as np

from .model import Integrator, Parameters, spherical_mesh, require

RADIUS_M = 6_371_000.0
KAPPA_M2_YEAR = 405_896_410_000.0  # R^2 * 0.01/year, deliberately artificial.
MEAN_HEIGHT_M = 8.0
AMPLITUDE_M = 1.0
DECLARED_TEST_DENSITY_KG_M3 = 2500.0
SPATIAL_END_YEAR = 0.0001  # Fixed across meshes; not a geological horizon.
SPATIAL_MESHES = ((16, 8), (32, 16), (64, 32), (128, 64), (256, 128))


def cell_average_mode(width, height, mode):
    """Analytic area averages of degree-one spherical harmonics.

    Derived by integrating the continuum field with measure cos(phi)dphi dlambda,
    independently of face conductances or the numerical update implementation.
    """
    phi = np.linspace(-math.pi / 2, math.pi / 2, height + 1)
    lam = np.linspace(-math.pi, math.pi, width + 1)
    if mode == "constant":
        return np.zeros(width * height, dtype="<f8")
    if mode == "latitude":
        average = (np.sin(phi[:-1]) + np.sin(phi[1:])) / 2
        return np.repeat(average, width)
    require(mode == "longitude", "MANUFACTURED_MODE_UNKNOWN")
    integral_phi = np.diff(phi / 2 + np.sin(2 * phi) / 4)
    mean_phi = integral_phi / np.diff(np.sin(phi))
    mean_lam = np.diff(np.sin(lam)) / (2 * math.pi / width)
    return (mean_phi[:, None] * mean_lam[None, :]).astype("<f8").ravel()


def continuum_heights(width, height, year, mode="latitude"):
    amplitude = AMPLITUDE_M * math.exp(-2 * KAPPA_M2_YEAR * year / RADIUS_M**2)
    return MEAN_HEIGHT_M + amplitude * cell_average_mode(width, height, mode)


def semidiscrete_latitude_heights(width, height, year):
    """Exact-in-time discrete latitude-mode oracle, not the continuum oracle.

    Analytic stencil identity on uniform latitude bands gives decay rate
    2*kappa/R^2 * sin(dphi)/dphi. It isolates temporal error at a fixed mesh.
    This identity is NOT used to manufacture measured spatial convergence.
    """
    dphi = math.pi / height
    rate = 2 * KAPPA_M2_YEAR / RADIUS_M**2 * math.sin(dphi) / dphi
    return MEAN_HEIGHT_M + AMPLITUDE_M * math.exp(-rate * year) * cell_average_mode(
        width, height, "latitude")


def new_case(width=16, height=8, planned_end_year=10.0, mode="latitude", *, density=None):
    mesh = spherical_mesh(width, height, RADIUS_M)
    parameters = Parameters(KAPPA_M2_YEAR, float(planned_end_year), density)
    return Integrator(mesh, parameters, continuum_heights(width, height, 0, mode),
                      {"family": "DECLARED_ARTIFICIAL_DEGREE_ONE_CELL_AVERAGE",
                       "mode": mode, "mean_height_m": MEAN_HEIGHT_M,
                       "amplitude_m": AMPLITUDE_M,
                       "parameter_authority": "TEST_ONLY_NOT_GEOLOGICAL_CALIBRATION",
                       "R6_T0_inputs_used": False})


def errors(actual, expected, areas):
    delta = np.asarray(actual) - np.asarray(expected)
    weights = np.asarray(areas) / math.fsum(map(float, areas))
    return {"L1_m": math.fsum(map(float, weights * np.abs(delta))),
            "L2_m": math.sqrt(math.fsum(map(float, weights * delta * delta))),
            "Linf_m": float(np.max(np.abs(delta)))}


def advance_annual(case, target_year):
    """Annual observation windows fix the same internal schedule in split arms."""
    require(type(target_year) is int and 0 < target_year <= 10,
            "P1_QUALIFICATION_ONLY_1_TO_10_MODEL_YEARS")
    rows = case.finish_window() if case.window is not None else []
    require(case.year == int(case.year), "ANNUAL_CONTINUATION_NEEDS_WINDOW_BOUNDARY")
    for year in range(int(case.year) + 1, target_year + 1):
        case.start_window(float(year))
        rows.extend(case.finish_window())
    return rows
