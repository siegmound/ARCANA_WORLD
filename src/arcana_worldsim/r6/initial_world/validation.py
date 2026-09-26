"""Fail-closed checks and diagnostic metrics for a generated R6 t0 state."""

from __future__ import annotations

from math import pi
from typing import Any

import numpy as np

from .generator import _connected_components
from .model import InitialWorldFields


def _longitude_span(lons: np.ndarray) -> float:
    vals = np.sort(np.unique(np.mod(lons, 360.0)))
    if len(vals) < 2:
        return 0.0
    gaps = np.diff(np.r_[vals, vals[0] + 360.0])
    return float(360.0 - gaps.max())


def _neighbor_slope_metrics(fields: InitialWorldFields) -> dict[str, float]:
    grid = fields.grid
    land = fields.land_ocean_mask.astype(bool)
    elevation = fields.land_surface_elevation_m.astype(np.float64)
    differences: list[float] = []
    slopes: list[float] = []
    for row, col in zip(*np.nonzero(land)):
        row, col = int(row), int(col)
        for rr, cc in ((row + 1, col), (row, (col + 1) % grid.nlon)):
            if rr >= grid.nlat or not land[rr, cc]:
                continue
            lat1, lat2 = np.deg2rad(grid.lat_centers_deg[[row, rr]])
            dlon = np.deg2rad(1.0)
            dlat = abs(float(lat2 - lat1))
            mean_lat = (lat1 + lat2) / 2
            distance = grid.radius_m * np.hypot(dlat, np.cos(mean_lat) * dlon)
            diff = abs(float(elevation[row, col] - elevation[rr, cc]))
            differences.append(diff)
            slopes.append(diff / distance)
    if not slopes:
        return {"neighbor_pair_count": 0, "slope_p50": 0.0, "slope_p95": 0.0,
                "slope_p99": 0.0, "slope_max": 0.0, "elevation_difference_p99_m": 0.0}
    a = np.asarray(slopes)
    d = np.asarray(differences)
    return {
        "neighbor_pair_count": int(len(a)),
        "slope_p50": float(np.quantile(a, 0.50)),
        "slope_p95": float(np.quantile(a, 0.95)),
        "slope_p99": float(np.quantile(a, 0.99)),
        "slope_max": float(a.max()),
        "elevation_difference_p99_m": float(np.quantile(d, 0.99)),
    }


def validate_initial_world(fields: InitialWorldFields) -> dict[str, Any]:
    grid = fields.grid
    areas = grid.cell_areas_m2()
    land = fields.land_ocean_mask.astype(bool)
    coast = fields.coastline_mask.astype(bool)
    failures: list[str] = []
    if fields.time_ma != 210.0:
        failures.append("t0_not_exactly_210_Ma")
    if any(a.shape != grid.shape for a in fields.arrays().values()):
        failures.append("array_shape_mismatch")
    global_area = float(areas.sum())
    expected_area = 4.0 * pi * grid.radius_m**2
    area_rel_error = abs(global_area - expected_area) / expected_area
    if area_rel_error > 1e-10:
        failures.append("spherical_cell_area_closure_failed")
    land_fraction = float(areas[land].sum() / global_area)
    ocean_fraction = 1.0 - land_fraction
    if not 0.25 <= land_fraction <= 0.35:
        failures.append("land_fraction_outside_contract")
    if not 0.65 <= ocean_fraction <= 0.75:
        failures.append("ocean_fraction_outside_contract")

    components = _connected_components(land, grid)
    component_area = [float(sum(areas[r, c] for r, c in comp) / global_area)
                      for comp in components]
    dominant_share = component_area[0] / land_fraction if component_area else 0.0
    if not 0.80 <= dominant_share <= 0.95:
        failures.append("dominant_supercontinent_share_outside_contract")
    if len(components) - 1 > 5:
        failures.append("detached_major_components_exceed_contract")
    dominant = np.zeros(grid.shape, dtype=bool)
    if components:
        for r, c in components[0]:
            dominant[r, c] = True
    rows, cols = np.nonzero(dominant)
    if not rows.size:
        failures.append("dominant_supercontinent_missing")
        centroid_lat = 0.0
        lat_span = lon_span = 0.0
    else:
        centroid_lat = float(np.average(grid.lat_centers_deg[rows], weights=areas[rows, cols]))
        lat_span = float(grid.lat_centers_deg[rows].max() - grid.lat_centers_deg[rows].min() + 1.0)
        lon_span = _longitude_span(grid.lon_centers_deg[cols]) + 1.0
        if not np.any(grid.lat_centers_deg[rows] < 0) or not np.any(grid.lat_centers_deg[rows] > 0):
            failures.append("dominant_component_does_not_cross_equator")
        if not -15.0 <= centroid_lat <= 15.0:
            failures.append("dominant_component_centroid_latitude_outside_contract")
        if lon_span < 120.0:
            failures.append("dominant_component_longitudinal_span_below_contract")
        if lat_span < 60.0:
            failures.append("dominant_component_latitudinal_span_below_contract")

    if np.any(coast & ~land):
        failures.append("coastline_mask_contains_ocean_cells")
    if not coast.any():
        failures.append("coastline_missing")
    if np.any(fields.elevation_support_mask != land):
        failures.append("land_elevation_support_mask_mismatch")
    elevation = fields.land_surface_elevation_m
    if not np.isfinite(elevation[land]).all():
        failures.append("nonfinite_supported_land_elevation")
    if np.any((elevation[land] < 0.0) | (elevation[land] > 8000.0)):
        failures.append("land_elevation_outside_contract")
    if np.any(~np.isnan(elevation[~land])):
        failures.append("numeric_elevation_present_on_ocean")
    if np.any(fields.synthetic_uncertainty_mask != land):
        failures.append("synthetic_uncertainty_mask_mismatch")

    if fields.plate_count not in range(12, 19):
        failures.append("plate_count_outside_design_range")
    if len(fields.craton_seed_cells) not in range(4, 9):
        failures.append("cratonic_block_count_outside_design_range")
    if np.any((fields.plate_id < 0) | (fields.plate_id >= fields.plate_count)):
        failures.append("plate_id_outside_registry")
    if not set(np.unique(fields.province_class)).issubset({-2, 0, 1, 2, 3}):
        failures.append("unknown_province_code")
    if np.any(fields.province_class[land] < 0) or np.any(fields.province_class[~land] != -2):
        failures.append("province_support_semantics_invalid")
    if not np.isin(fields.crust_class, [0, 1, 2]).all():
        failures.append("crust_class_code_invalid")
    if np.any(fields.crust_class[land & ~coast] != 1) or np.any(fields.crust_class[~land] != 0):
        failures.append("crust_class_land_ocean_binding_invalid")

    if not np.all(fields.bathymetry_unknown_mask == ~land):
        failures.append("bathymetry_unknown_mask_invalid")
    for name in ("plate_motion_unknown_mask", "deep_unknown_mask", "climate_unknown_mask",
                 "hydrology_unknown_mask"):
        if not np.all(getattr(fields, name)):
            failures.append(f"{name}_not_preserved")

    slope = _neighbor_slope_metrics(fields)
    shoreline_outlet_cells = int(np.count_nonzero(coast))
    # No flow routing/sink filling occurs: sinks and slopes are diagnostics only.
    local_sink_count = 0
    for row, col in zip(*np.nonzero(land)):
        neighbors = [(rr, cc) for rr, cc in grid.neighbors(int(row), int(col)) if land[rr, cc]]
        if neighbors and all(elevation[row, col] <= elevation[rr, cc] for rr, cc in neighbors):
            local_sink_count += 1

    province_counts = {
        "OTHER_DESIGN": int(np.count_nonzero(fields.province_class == 0)),
        "CRATON": int(np.count_nonzero(fields.province_class == 1)),
        "SUTURE": int(np.count_nonzero(fields.province_class == 2)),
        "OROGENIC_DESIGN": int(np.count_nonzero(fields.province_class == 3)),
    }
    coast_edge_changes = int(np.count_nonzero(
        land != np.roll(land, 1, axis=1)) + np.count_nonzero(land[1:, :] != land[:-1, :]))
    # Ellipse/anisotropy and coastline measures are reported as diagnostics; no
    # empirical fit or post-result threshold is introduced by this validator.
    dominant_cov = np.cov(np.vstack((
        (grid.lon_centers_deg[cols] if cols.size else np.array([0.0])),
        (grid.lat_centers_deg[rows] if rows.size else np.array([0.0])))))
    eigenvalues = np.linalg.eigvalsh(dominant_cov)
    asymmetry_ratio = float(eigenvalues[-1] / max(eigenvalues[0], 1e-12))
    drainage_ready = (not failures and shoreline_outlet_cells > 0 and
                      np.all(fields.elevation_support_mask[land]))
    status = "FAIL" if failures else "PASS_WITH_UNKNOWN"
    return {
        "schema": "R6_INITIAL_WORLD_VALIDATION_V1",
        "result": status,
        "failures": failures,
        "t0_ma": fields.time_ma,
        "grid_id": grid.grid_id,
        "grid_shape": list(grid.shape),
        "cell_count": grid.cell_count,
        "global_area_m2": global_area,
        "area_relative_error": area_rel_error,
        "land_fraction_area_weighted": land_fraction,
        "ocean_fraction_area_weighted": ocean_fraction,
        "connected_land_component_count": len(components),
        "component_area_fraction_surface_descending": component_area,
        "dominant_component_share_of_land": dominant_share,
        "dominant_component_centroid_latitude_deg": centroid_lat,
        "dominant_component_latitudinal_span_deg": lat_span,
        "dominant_component_longitudinal_span_deg": lon_span,
        "coastline_edge_transition_count": coast_edge_changes,
        "coastline_cell_count": shoreline_outlet_cells,
        "land_shape_covariance_eigenvalue_ratio_diagnostic": asymmetry_ratio,
        "plate_count": fields.plate_count,
        "craton_count": len(fields.craton_seed_cells),
        "province_cell_counts_including_ocean_n_a": province_counts,
        "land_elevation_min_m": float(np.min(elevation[land])),
        "land_elevation_max_m": float(np.max(elevation[land])),
        "land_elevation_mean_m": float(np.mean(elevation[land])),
        "land_elevation_std_m": float(np.std(elevation[land])),
        "land_elevation_quantiles_m": {
            "p05": float(np.quantile(elevation[land], 0.05)),
            "p50": float(np.quantile(elevation[land], 0.50)),
            "p95": float(np.quantile(elevation[land], 0.95)),
            "p99": float(np.quantile(elevation[land], 0.99)),
        },
        "slope_metrics_diagnostic_only": slope,
        "local_sink_count_diagnostic_only": local_sink_count,
        "drainage_ready_terrain_support": "PASS" if drainage_ready else "FAIL",
        "drainage_interpretation": "Complete land elevations, connected land components and coastal outlets are present; no hydrological flow network, discharge, erosion, depression filling or sink correction was executed.",
        "unknown_masks_preserved": True,
        "unknown_domain_list": ["plate_motion", "bathymetry", "deep", "climate", "hydrology"],
        "categorical_interpolation": False,
        "spatial_resampling": False,
        "a1_runtime_dependency": False,
        "simulation1_trajectory_reused": False,
        "r5_runtime_dependency": False,
        "scientific_forward_simulation_executed": False,
    }
