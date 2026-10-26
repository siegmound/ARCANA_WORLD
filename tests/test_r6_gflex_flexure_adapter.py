from __future__ import annotations

import math

import pytest

from arcana_worldsim.r6.gflex_flexure_adapter import (
    GFlexParameters,
    apply_deflection_increment_to_region,
    load_pressure_from_mass_delta,
    solve_gflex_1d,
    solve_gflex_2d,
)
from arcana_worldsim.r6.regional_geological_evolution import (
    RegionalConfig,
    advance_region,
    create_synthetic_region,
)


def _benchmark_parameters(dx: float = 2_000.0) -> GFlexParameters:
    return GFlexParameters(
        grid_spacing_x_m=dx,
        young_modulus_pa=70.0e9,
        poisson_ratio=0.25,
        elastic_thickness_m=20_000.0,
        mantle_density_kg_m3=3_300.0,
        infill_density_kg_m3=0.0,
        gravity_m_s2=9.81,
        authority="SYNTHETIC_ANALYTIC_BENCHMARK",
    )


def test_real_gflex_1d_matches_independent_infinite_plate_strip_solution():
    n, dx, pressure = 601, 2_000.0, 1.0e6
    center = n // 2
    loads = [0.0] * n
    loads[center - 5:center + 6] = [pressure] * 11
    ids = [f"SYNTHETIC_TRANSECT:{i:04d}" for i in range(n)]
    params = _benchmark_parameters(dx)
    result = solve_gflex_1d(loads, ids, parameters=params, time_s=0.0,
                            provenance={"authority": "SYNTHETIC_FIXTURE_ONLY"})

    # Infinite 1-D elastic plate Green function integrated over the loaded
    # strip; the finite-difference gFlex domain is 12 flexural parameters long
    # on either side, so fixed-end effects are negligible at the load center.
    rigidity = params.young_modulus_pa * params.elastic_thickness_m ** 3 / (
        12.0 * (1.0 - params.poisson_ratio ** 2))
    foundation = ((params.mantle_density_kg_m3 - params.infill_density_kg_m3)
                  * params.gravity_m_s2)
    alpha = (4.0 * rigidity / foundation) ** 0.25
    half_width = 11 * dx / 2.0
    analytic_center = -pressure / foundation * (
        1.0 - math.exp(-half_width / alpha) * math.cos(half_width / alpha))
    actual_center = result["deflection_m"][center]
    assert actual_center < 0.0  # positive downward load -> negative/up? gFlex convention is negative downward
    assert math.isclose(actual_center, analytic_center, rel_tol=0.01, abs_tol=1e-8)
    assert max(abs(value) for value in result["deflection_m"]) > 0.0
    assert result["solver"] == "gFlex"
    assert result["version"] == "1.3.0"
    assert result["temporal_semantics"].startswith("INSTANTANEOUS")
    assert result["runtime_seconds"] >= 0.0
    assert len(result["result_identity_sha256"]) == 64


def test_gflex_linear_load_and_te_sensitivity_are_observed():
    n, center = 301, 150
    ids = [f"SYNTHETIC_SENSITIVITY:{i}" for i in range(n)]
    load = [0.0] * n
    load[center] = 1.0e6
    params = _benchmark_parameters()
    one = solve_gflex_1d(load, ids, parameters=params, time_s=0.0,
                         provenance={"fixture": "load-1"})["deflection_m"]
    two = solve_gflex_1d([2.0 * x for x in load], ids, parameters=params,
                         time_s=0.0, provenance={"fixture": "load-2"})["deflection_m"]
    thicker = GFlexParameters(**{**params.__dict__, "elastic_thickness_m": 30_000.0})
    thick_w = solve_gflex_1d(load, ids, parameters=thicker, time_s=0.0,
                             provenance={"fixture": "te-30km"})["deflection_m"]
    assert max(abs(a - 2.0 * b) for a, b in zip(two, one)) < 1e-9
    assert abs(thick_w[center]) < abs(one[center])


def test_gflex_boundary_condition_choice_changes_the_benchmark_solution():
    n, center = 201, 100
    ids = [f"SYNTHETIC_BC:{i}" for i in range(n)]
    load = [0.0] * n
    load[center] = 1.0e6
    clamped = _benchmark_parameters()
    free_end = GFlexParameters(**{**clamped.__dict__,
        "boundary_west": "0Moment0Shear"})
    a = solve_gflex_1d(load, ids, parameters=clamped, time_s=0.0,
                       provenance={"bc": "clamped"})["deflection_m"]
    b = solve_gflex_1d(load, ids, parameters=free_end, time_s=0.0,
                       provenance={"bc": "free-west"})["deflection_m"]
    assert all(math.isfinite(value) for value in (*a, *b))
    assert max(abs(x - y) for x, y in zip(a, b)) > 0.0


def test_real_gflex_2d_delta_flows_into_synthetic_surface_and_routing_once():
    base = (12.0, 8.0, 4.0, 11.0, 6.0, 0.0, 10.0, 3.0, -2.0)
    almost_flat = (0.0, 1e-5, 2e-5, 1e-5, 2e-5, 3e-5, 2e-5, 3e-5, -1e-5)
    cfg = RegionalConfig(
        duration_years=1,
        precipitation_m_year=0.0,
        initial_elevation_offsets_m_by_cell=tuple(z - b for z, b in zip(almost_flat, base)),
    )
    region = create_synthetic_region(cfg)
    region_ids = [[f"SYNTHETIC_BASIN_3X3:C{i:02d}" for i in range(r * 3, (r + 1) * 3)]
                  for r in range(3)]
    previous_targets = dict(region["drainage_targets"])

    # A derived one-alpha halo keeps the central 3x3 cell centres, spacing,
    # and IDs aligned; boundary influence remains an explicit limitation.
    n, pad = 75, 36
    ids_7 = [[f"FLEXURE_PAD:{r}:{c}" for c in range(n)] for r in range(n)]
    for r in range(3):
        for c in range(3):
            ids_7[r + pad][c + pad] = region_ids[r][c]
    params = GFlexParameters(
        grid_spacing_x_m=1_000.0,
        grid_spacing_y_m=1_000.0,
        young_modulus_pa=70.0e9,
        poisson_ratio=0.25,
        elastic_thickness_m=20_000.0,
        mantle_density_kg_m3=3_300.0,
        infill_density_kg_m3=0.0,
        gravity_m_s2=9.81,
        authority="SYNTHETIC_INTERFACE_BENCHMARK_ONLY",
    )
    # Synthetic deposition mass is converted to Pa by Δm*g/A, not by changing
    # Deep inventory or by interpreting R6 material records as lithology.
    pressure_center = load_pressure_from_mass_delta([1.0e12], [1.0e6], 9.81)[0]
    load_1 = [[0.0] * n for _ in range(n)]
    load_1[n // 2][n // 2] = pressure_center
    load_2 = [[2.0 * value for value in row] for row in load_1]
    provenance = {"authority": "SYNTHETIC_3X3_GRID_WITH_EXPLICIT_2_CELL_HALO"}
    first = solve_gflex_2d(load_1, ids_7, parameters=params, time_s=1.0,
                           provenance=provenance)
    second = solve_gflex_2d(load_2, ids_7, parameters=params, time_s=2.0,
                            provenance=provenance)
    crop = lambda result: [row[pad:pad + 3]
                           for row in result["deflection_m"][pad:pad + 3]]
    zero = [[0.0] * 3 for _ in range(3)]
    after_first = apply_deflection_increment_to_region(
        region, cell_ids=region_ids, previous_deflection_m=zero,
        current_deflection_m=crop(first), previous_time_s=0.0, current_time_s=1.0)
    after_second = apply_deflection_increment_to_region(
        after_first, cell_ids=region_ids, previous_deflection_m=crop(first),
        current_deflection_m=crop(second), previous_time_s=1.0, current_time_s=2.0)
    assert after_first["drainage_targets"] != previous_targets
    assert len(after_second["flexure_events"]) == 2
    assert after_second["flexure_events"][0]["to_time_s"] == 1.0
    for index, cell in enumerate(after_second["cells"]):
        r, c = divmod(index, 3)
        expected = region["cells"][index]["elevation_m"] + crop(second)[r][c]
        assert math.isclose(cell["elevation_m"], expected, rel_tol=0.0, abs_tol=1e-12)
        assert math.isclose(cell["bedrock_elevation_m"], expected, rel_tol=0.0, abs_tol=1e-12)
    assert after_second["source_identity"] == region["source_identity"]
    routed = advance_region(after_second, years=1, config=cfg,
                            precipitation_m_year_by_cell=[0.0] * 9)
    assert routed["records"][-1]["drainage_targets_used"] == after_second["drainage_targets"]
    assert all(abs(row["geometry_balance_residual_m"]) <= 1e-12
               for row in routed["records"][-1]["geologic_load_by_cell"])


def test_load_conversion_rejects_invalid_inputs():
    assert load_pressure_from_mass_delta([2.0, -1.0], [2.0, 1.0], 10.0) == [10.0, -10.0]
    with pytest.raises(ValueError):
        load_pressure_from_mass_delta([1.0], [0.0], 9.81)
