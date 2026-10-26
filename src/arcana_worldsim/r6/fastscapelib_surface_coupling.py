"""Synthetic Fastscapelib SPL -> R6 regional material/hydrology coupling.

This adapter uses a declared 6x6 node raster that maps by exact 2x2 node
control-volume blocks to the existing synthetic R6 3x3 basin. It is not a
mapping to R6 geography. SPL is the sole bedrock-detachment operator in this
experiment; R6 regional routing owns subsequent water/material transport.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

import numpy as np

from .regional_geological_evolution import (
    RegionalConfig,
    advance_region,
    create_synthetic_region,
)


SCHEMA = "ARCANA_R6_SURF2_FASTSCAPELIB_R6_COUPLING_V1"
RASTER_N = 6
RASTER_SPACING_M = 500.0
GROUP_NODES_PER_AXIS = 2
REGION_CELLS = 3
SUBSTRATE_RHO_KG_M3 = 2700.0
SYNTHETIC_SPL_K = 2.0e-4
SYNTHETIC_MATERIAL_PREFIX = "SYNTHETIC_SURF2_BEDROCK"


class SurfaceCouplingError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def raster_to_region_mapping(*, spacing_m: float = RASTER_SPACING_M) -> dict[str, Any]:
    """Return exact node-control-area assignment: each 2x2 block is 1 km²."""
    if not math.isfinite(spacing_m) or spacing_m <= 0:
        raise SurfaceCouplingError("RASTER_SPACING_INVALID")
    import fastscapelib as fs

    grid = fs.RasterGrid(
        [RASTER_N, RASTER_N], [spacing_m, spacing_m],
        [fs.NodeStatus.CORE, fs.NodeStatus.CORE,
         fs.NodeStatus.FIXED_VALUE, fs.NodeStatus.CORE],
    )
    node_areas = np.asarray(grid.nodes_areas(), dtype=np.float64)
    if node_areas.shape != (RASTER_N, RASTER_N) or not np.isfinite(node_areas).all():
        raise SurfaceCouplingError("FASTSCAPE_NODE_AREA_INVALID")
    cells = []
    for rr in range(REGION_CELLS):
        for cc in range(REGION_CELLS):
            r0, c0 = rr * GROUP_NODES_PER_AXIS, cc * GROUP_NODES_PER_AXIS
            indices = [(r, c) for r in range(r0, r0 + GROUP_NODES_PER_AXIS)
                       for c in range(c0, c0 + GROUP_NODES_PER_AXIS)]
            area = float(sum(node_areas[r, c] for r, c in indices))
            expected = (GROUP_NODES_PER_AXIS * spacing_m) ** 2
            if not math.isclose(area, expected, rel_tol=0.0, abs_tol=1e-9):
                raise SurfaceCouplingError("RASTER_REGION_AREA_MAPPING_NOT_EXACT")
            cells.append({
                "region_cell_index": rr * REGION_CELLS + cc,
                "region_cell_id": f"SYNTHETIC_BASIN_3X3:C{rr * REGION_CELLS + cc:02d}",
                "area_m2": area,
                "raster_nodes": [
                    {"node_id": f"SYNTHETIC_RASTER:R{r:02d}:C{c:02d}",
                     "row": r, "column": c, "control_area_m2": float(node_areas[r, c])}
                    for r, c in indices
                ],
            })
    return {
        "scheme": "SYNTHETIC_2X2_NODE_CONTROL_AREAS_TO_ONE_R6_REGION_CELL",
        "raster_shape": [RASTER_N, RASTER_N],
        "raster_spacing_m": [spacing_m, spacing_m],
        "raster_area_sum_m2": float(node_areas.sum()),
        "region_shape": [REGION_CELLS, REGION_CELLS],
        "region_cell_center_spacing_m": [2 * spacing_m, 2 * spacing_m],
        "cells": cells,
        "mapping_authority": "EXPLICIT_SYNTHETIC_EXPERIMENT_ONLY_NOT_R6_GEOGRAPHY",
    }


def _coarsen_height(elevation: np.ndarray, mapping: Mapping[str, Any]) -> list[float]:
    return [
        sum(float(elevation[node["row"], node["column"]]) * node["control_area_m2"]
            for node in cell["raster_nodes"]) / float(cell["area_m2"])
        for cell in mapping["cells"]
    ]


def _make_region(initial_fine: np.ndarray, mapping: Mapping[str, Any], *,
                 duration_years: int, precipitation_m_year: float) -> tuple[dict[str, Any], RegionalConfig]:
    from .regional_geological_evolution import _drainage_for_elevation

    initial_coarse = _coarsen_height(initial_fine, mapping)
    default_z = (12.0, 8.0, 4.0, 11.0, 6.0, 0.0, 10.0, 3.0, -2.0)
    config = RegionalConfig(
        cell_area_m2=float(mapping["cells"][0]["area_m2"]),
        duration_years=duration_years,
        precipitation_m_year=precipitation_m_year,
        detachment_enabled=False,
        substrate_density_kg_m3=SUBSTRATE_RHO_KG_M3,
        initial_substrate_thickness_m=100.0,
        routing_mode="DYNAMIC_TOPOGRAPHY",
        initial_elevation_offsets_m_by_cell=tuple(
            initial_coarse[i] - default_z[i] for i in range(9)),
    )
    identity = {
        "status": "SYNTHETIC_FIXTURE_ONLY",
        "surface_schema": SCHEMA,
        "mapping_sha256": _sha(mapping),
        "raster_spacing_m": RASTER_SPACING_M,
        "r6_surface_engine": "regional_geological_evolution.advance_region",
        "spl_engine": "Fastscapelib.Python.SPLEroder",
        "material_identity": "SYNTHETIC_BULK_BEDROCK_PER_REGION_CELL",
    }
    region = create_synthetic_region(config, source_identity=identity)
    # The initial R6 snapshot is already the area-conservative raster projection.
    for i, cell in enumerate(region["cells"]):
        cell["area_m2"] = float(mapping["cells"][i]["area_m2"])
        mass = cell["area_m2"] * cell["substrate_thickness_m"] * SUBSTRATE_RHO_KG_M3
        cell["substrate"]["mass_kg"] = mass
        cell["initial_solid_mass_kg"] = mass
        cell["substrate"]["density_kg_m3"] = SUBSTRATE_RHO_KG_M3
        region["snapshots"][0]["cells"][i]["area_m2"] = cell["area_m2"]
    region["initial_totals"]["substrate_kg"] = sum(
        cell["substrate"]["mass_kg"] for cell in region["cells"])
    region["source_identity_sha256"] = _sha(region["source_identity"])
    region["drainage_targets"] = _drainage_for_elevation(region["cells"], config)
    region["baseline_drainage_targets"] = dict(region["drainage_targets"])
    region["snapshots"][0]["cells"] = json.loads(_canonical(region["cells"]))
    return region, config


def _fastscape_basins(elevation: np.ndarray, spacing_m: float) -> list[list[int]]:
    import fastscapelib as fs

    grid = fs.RasterGrid(
        list(elevation.shape), [spacing_m, spacing_m],
        [fs.NodeStatus.CORE, fs.NodeStatus.CORE,
         fs.NodeStatus.FIXED_VALUE, fs.NodeStatus.CORE],
    )
    graph = fs.FlowGraph(grid, [fs.SingleFlowRouter()])
    graph.update_routes(elevation)
    return np.asarray(graph.basins(), dtype=np.int64).tolist()


def _solid_stock_by_cell(region: Mapping[str, Any]) -> list[float]:
    return [
        float(cell["substrate"]["mass_kg"])
        + sum(float(v) for v in cell["mobile_kg_by_material"].values())
        + sum(float(v) for v in cell["suspended_kg_by_material"].values())
        + sum(float(row["mass_kg"]) for row in cell["deposits"])
        for cell in region["cells"]
    ]


def _apply_spl_material_transfer(region: dict[str, Any], mapping: Mapping[str, Any],
                                 fine_before: np.ndarray, fine_after: np.ndarray,
                                 node_areas: np.ndarray, *, year: int) -> dict[str, Any]:
    lowered = fine_before - fine_after
    if not np.isfinite(lowered).all() or np.any(lowered < -1e-12):
        raise SurfaceCouplingError("SPL_LOWERING_INVALID")
    per_cell = []
    for cell_map in mapping["cells"]:
        idx = int(cell_map["region_cell_index"])
        cell = region["cells"][idx]
        volume = sum(max(0.0, float(lowered[node["row"], node["column"]]))
                     * float(node_areas[node["row"], node["column"]])
                     for node in cell_map["raster_nodes"])
        mass = volume * SUBSTRATE_RHO_KG_M3
        stock = float(cell["substrate"]["mass_kg"])
        if not math.isfinite(mass) or mass < 0 or mass > stock + 1e-8:
            raise SurfaceCouplingError("SPL_EROSION_EXCEEDS_AVAILABLE_SUBSTRATE")
        mass = min(mass, stock)
        if mass:
            cell["substrate"]["mass_kg"] = stock - mass
            cell["cumulative_eroded_kg"] += mass
            cell["substrate_thickness_m"] = (
                float(cell["substrate"]["mass_kg"])
                / (float(cell["substrate"]["density_kg_m3"]) * float(cell["area_m2"])))
            material_id = str(cell["substrate"]["material_id"])
            cell["mobile_kg_by_material"][material_id] = (
                float(cell["mobile_kg_by_material"].get(material_id, 0.0)) + mass)
            region["cumulative"]["substrate_eroded_kg"] += mass
        mapped_z = sum(float(fine_after[node["row"], node["column"]])
                       * float(node["control_area_m2"])
                       for node in cell_map["raster_nodes"]) / float(cell_map["area_m2"])
        # Fastscapelib evolves bedrock only. Keep R6's already deposited
        # material above it when rebuilding the regional surface at each step.
        cell["bedrock_elevation_m"] = mapped_z
        deposited_thickness = sum(
            float(row["mass_kg"])
            / (float(row["density_kg_m3"]) * float(cell["area_m2"]))
            for row in cell["deposits"]
        )
        cell["elevation_m"] = mapped_z + deposited_thickness
        per_cell.append({
            "cell_id": cell["cell_id"], "material_id": cell["substrate"]["material_id"],
            "volume_removed_m3": volume, "mass_transferred_to_mobile_kg": mass,
            "substrate_mass_after_spl_kg": float(cell["substrate"]["mass_kg"]),
            "mapped_bedrock_elevation_m": mapped_z,
            "preserved_deposit_thickness_m": deposited_thickness,
            "mapped_surface_elevation_m": float(cell["elevation_m"]),
            "time_year": year,
        })
    total_volume = sum(row["volume_removed_m3"] for row in per_cell)
    total_mass = sum(row["mass_transferred_to_mobile_kg"] for row in per_cell)
    if not math.isclose(total_mass, total_volume * SUBSTRATE_RHO_KG_M3,
                        rel_tol=2e-15, abs_tol=1e-7):
        raise SurfaceCouplingError("SPL_VOLUME_TO_MASS_CONVERSION_FAILED")
    return {
        "kind": "SPL_BEDROCK_TO_R6_MOBILE_SEDIMENT",
        "time_year": year,
        "equation": "dm = max(z_before-z_after,0) * Fastscapelib_node_control_area * synthetic_bulk_density",
        "density_kg_m3": SUBSTRATE_RHO_KG_M3,
        "total_volume_m3": total_volume,
        "total_mass_kg": total_mass,
        "cell_transfers": per_cell,
        "material_authority": "SYNTHETIC_BULK_BENCHMARK_NOT_LITHOLOGY",
    }


def seal_coupling_checkpoint(*, region: Mapping[str, Any],
                             fine_bedrock_m: np.ndarray,
                             mapping: Mapping[str, Any],
                             config_identity: Mapping[str, Any]) -> dict[str, Any]:
    body = {
        "schema": SCHEMA,
        "region_state": json.loads(_canonical(region)),
        "fine_bedrock_m": np.asarray(fine_bedrock_m, dtype=np.float64).tolist(),
        "mapping": dict(mapping),
        "mapping_sha256": _sha(mapping),
        "config_identity": dict(config_identity),
    }
    return {**body, "checkpoint_sha256": _sha(body),
            "checkpoint_authority": "INTEGRITY_ONLY_SYNTHETIC_ENGINEERING_STATE"}


def verify_coupling_checkpoint(checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    body = {key: value for key, value in checkpoint.items()
            if key not in {"checkpoint_sha256", "checkpoint_authority"}}
    if (checkpoint.get("schema") != SCHEMA
            or checkpoint.get("checkpoint_sha256") != _sha(body)
            or checkpoint.get("mapping_sha256") != _sha(checkpoint.get("mapping"))):
        raise SurfaceCouplingError("COUPLING_CHECKPOINT_INVALID")
    state = checkpoint.get("region_state")
    fine = np.asarray(checkpoint.get("fine_bedrock_m"), dtype=np.float64)
    if (not isinstance(state, dict) or not np.isfinite(fine).all()
            or fine.shape != (RASTER_N, RASTER_N)
            or state.get("source_identity_sha256") != _sha(state.get("source_identity"))):
        raise SurfaceCouplingError("COUPLING_CHECKPOINT_STATE_INVALID")
    if state.get("time_years", 0) < 0:
        raise SurfaceCouplingError("COUPLING_CHECKPOINT_TIME_INVALID")
    return json.loads(_canonical(checkpoint))


def run_coupled_segment(*, years: int = 2, planned_years: int | None = None,
                        k_coef: float = SYNTHETIC_SPL_K,
                        precipitation_m_year: float = 0.15,
                        checkpoint: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run one operator-split annual SPL→R6 routing/material segment."""
    if (not isinstance(years, int) or years < 1 or not math.isfinite(k_coef)
            or k_coef < 0 or not math.isfinite(precipitation_m_year)
            or precipitation_m_year < 0):
        raise SurfaceCouplingError("COUPLING_CONFIG_INVALID")
    planned_years = years if planned_years is None else planned_years
    if not isinstance(planned_years, int) or planned_years < years:
        raise SurfaceCouplingError("COUPLING_PLANNED_DURATION_INVALID")
    import fastscapelib as fs
    from .gflex_flexure_adapter import load_pressure_from_mass_delta
    from scripts.r6_fastscapelib_landscape_benchmark import synthetic_initial_topography

    if fs.__version__ != "0.3.0":
        raise SurfaceCouplingError("FASTSCAPELIB_VERSION_MISMATCH")
    mapping = raster_to_region_mapping()
    from .regional_geological_evolution import _drainage_for_elevation

    if checkpoint is None:
        initial_fine, _, _ = synthetic_initial_topography(
            n=RASTER_N, spacing_m=RASTER_SPACING_M)
        region, config = _make_region(initial_fine, mapping,
            duration_years=planned_years, precipitation_m_year=precipitation_m_year)
        fine = initial_fine.copy()
        config_identity = {
            "years_total": planned_years, "spl_k_coef_per_year": k_coef,
            "spl_m": 0.5, "spl_n": 1.0, "spl_dt_years": 1.0,
            "r6_annual_precipitation_m_year": precipitation_m_year,
            "r6_detachment_enabled": False,
            "substrate_density_kg_m3": SUBSTRATE_RHO_KG_M3,
            "synthetic_mapping_sha256": _sha(mapping),
            "time_coupling": "ONE_OPERATOR_SPLIT_EXTERNAL_YEAR; SPL_DT=1 YEAR; R6_REGIONAL_HYDROLOGY=1 ANNUAL STEP",
        }
        offset = 0
    else:
        cp = verify_coupling_checkpoint(checkpoint)
        if cp["mapping_sha256"] != _sha(mapping):
            raise SurfaceCouplingError("COUPLING_CHECKPOINT_MAPPING_MISMATCH")
        region = cp["region_state"]
        config = RegionalConfig(**region["config"])
        config_identity = dict(cp["config_identity"])
        if (not math.isclose(float(config_identity["spl_k_coef_per_year"]), k_coef)
                or not math.isclose(float(config_identity["r6_annual_precipitation_m_year"]),
                                    precipitation_m_year)):
            raise SurfaceCouplingError("COUPLING_CHECKPOINT_CONFIG_MISMATCH")
        fine = np.asarray(cp["fine_bedrock_m"], dtype=np.float64)
        offset = int(region["time_years"])
        if offset + years > int(config_identity["years_total"]):
            raise SurfaceCouplingError("COUPLING_SEGMENT_EXCEEDS_PLANNED_DURATION")
    grid = fs.RasterGrid(
        [RASTER_N, RASTER_N], [RASTER_SPACING_M, RASTER_SPACING_M],
        [fs.NodeStatus.CORE, fs.NodeStatus.CORE,
         fs.NodeStatus.FIXED_VALUE, fs.NodeStatus.CORE],
    )
    node_areas = np.asarray(grid.nodes_areas(), dtype=np.float64)
    before_stocks = _solid_stock_by_cell(region)
    series = []
    for local_step in range(years):
        year = offset + local_step + 1
        fine_before = fine.copy()
        fastscape_result = __import__(
            "scripts.r6_fastscapelib_landscape_benchmark", fromlist=["run_landscape"]
        ).run_landscape(k_coef=k_coef, steps=1, initial_elevation=fine,
                        dt_years=1.0, spacing_m=RASTER_SPACING_M)
        fine = np.asarray(fastscape_result["elevation_m"], dtype=np.float64)
        if not np.array_equal(fine[-1, :], fine_before[-1, :]):
            raise SurfaceCouplingError("SPL_FIXED_BASELEVEL_CHANGED")
        basins_before = _fastscape_basins(fine_before, RASTER_SPACING_M)
        basins_after = _fastscape_basins(fine, RASTER_SPACING_M)
        transfer = _apply_spl_material_transfer(region, mapping, fine_before,
                                                 fine, node_areas, year=year)
        pre_hydro_targets = dict(region["drainage_targets"])
        region["drainage_targets"] = _drainage_for_elevation(region["cells"], config)
        # Restore old targets so advance_region records the change and uses the
        # newly recomputed graph for this annual hydrology step.
        recomputed_targets = dict(region["drainage_targets"])
        region["drainage_targets"] = pre_hydro_targets
        next_region = advance_region(region, years=1, config=config,
            precipitation_m_year_by_cell=[precipitation_m_year] * 9)
        record = next_region["records"][-1]
        record["events"].insert(0, transfer)
        region = next_region
        slope_deltas = []
        for r in range(RASTER_N):
            for c in range(RASTER_N):
                for rr, cc in ((r + 1, c), (r, c + 1)):
                    if rr < RASTER_N and cc < RASTER_N:
                        before_slope = (fine_before[r, c] - fine_before[rr, cc]) / RASTER_SPACING_M
                        after_slope = (fine[r, c] - fine[rr, cc]) / RASTER_SPACING_M
                        slope_deltas.append(abs(float(after_slope - before_slope)))
        series.append({
            "time_year": year,
            "spl": {**transfer,
                    "max_lowering_m": float(np.max(fine_before - fine)),
                    "fastscapelib_final_basin_map_changed": basins_before != basins_after,
                    "max_adjacent_slope_change": max(slope_deltas, default=0.0)},
            "r6_hydrology": record,
            "r6_recomputed_surface_route_targets": recomputed_targets,
            "r6_route_targets_before_step": pre_hydro_targets,
            "r6_route_targets_used": record["drainage_targets_used"],
        })
    final_stocks = _solid_stock_by_cell(region)
    delta_stock = [after - before for before, after in zip(before_stocks, final_stocks)]
    load_pa = load_pressure_from_mass_delta(
        delta_stock, [float(cell["area_m2"]) for cell in region["cells"]],
        gravity_m_s2=9.80665)
    solid_residuals = [float(row["solid_mass_balance_kg"]["residual"])
                       for row in region["records"][-years:]]
    water_residuals = [float(row["water_balance_m3"]["residual"])
                       for row in region["records"][-years:]]
    cp = seal_coupling_checkpoint(region=region, fine_bedrock_m=fine,
                                  mapping=mapping, config_identity=config_identity)
    return {
        "schema": SCHEMA,
        "decision": "SURF2_COUPLED_EXPERIMENT_PASS_SYNTHETIC_ONLY",
        "scope": "SYNTHETIC_ENGINEERING_ONLY",
        "time_years": {"start": offset, "end": int(region["time_years"]),
                       "steps": years, "operator_split": config_identity["time_coupling"]},
        "mapping": mapping,
        "configuration": config_identity,
        "initial": {"fine_bedrock_m": (np.asarray(
            checkpoint["fine_bedrock_m"], dtype=np.float64).tolist()
            if checkpoint is not None else synthetic_initial_topography(
                n=RASTER_N, spacing_m=RASTER_SPACING_M)[0].tolist()),
            "regional_solid_stock_kg_by_cell": before_stocks},
        "steps": series,
        "final": {
            "fine_bedrock_m": fine.tolist(),
            "regional_cells": region["cells"],
            "regional_solid_stock_kg_by_cell": final_stocks,
            "regional_surface_route_targets": region["drainage_targets"],
            "substrate_mass_kg": sum(float(c["substrate"]["mass_kg"])
                                     for c in region["cells"]),
            "mobile_sediment_kg": sum(sum(map(float, c["mobile_kg_by_material"].values()))
                                      for c in region["cells"]),
            "suspended_sediment_kg": sum(sum(map(float, c["suspended_kg_by_material"].values()))
                                         for c in region["cells"]),
            "deposited_sediment_kg": sum(sum(float(d["mass_kg"]) for d in c["deposits"])
                                         for c in region["cells"]),
            "exported_sediment_kg": float(region["cumulative"]["sediment_export_kg"]),
            "water_storage_m3": sum(float(c["water_storage_m3"]) for c in region["cells"]),
            "cumulative_water_terms": dict(region["cumulative"]),
            "deep_state": "NOT_MODIFIED_NO_DEEP_EXCHANGE_LAW",
        },
        "balances": {
            "solid_mass_residual_kg_by_year": solid_residuals,
            "water_residual_m3_by_year": water_residuals,
            "SPL_mass_transfer_identity_residual_kg": (
                sum(x["spl"]["total_mass_kg"] for x in series)
                - sum(x["spl"]["total_volume_m3"] for x in series)
                * SUBSTRATE_RHO_KG_M3),
            "all_material_stocks_nonnegative": all(
                v >= -1e-9 for cell in region["cells"]
                for v in [cell["substrate"]["mass_kg"],
                          *cell["mobile_kg_by_material"].values(),
                          *cell["suspended_kg_by_material"].values(),
                          *(d["mass_kg"] for d in cell["deposits"])]),
            "gflex_candidate_load_delta_pa_by_cell": load_pa,
            "gflex_status": "LOAD_DIAGNOSTIC_ONLY_NO_GFlex_SOLVE_OR_Te_ASSIGNED",
        },
        "regional_state": region,
        "continuation_checkpoint": cp,
        "authority_limits": [
            "All terrain, rainfall, bulk material and SPL K are synthetic; no ARCANA regional data or litology was used.",
            "Fastscapelib SPL and R6 hydrology are sequential operator-split processes on a declared synthetic mapping; no 500-year-to-hour conversion is assumed.",
            "SPL has no cover shielding, sediment transport or deposition. Its eroded bedrock mass is explicitly transferred to R6 mobile material using synthetic density.",
            "Fastscapelib D8 basins and R6 regional routing are different operators; the R6 annual router is recomputed on the remapped post-incision topography.",
            "The load diagnostic is derived from R6 solid-stock change, not elevation; it is not passed to gFlex in this run.",
            "No Deep energy, thermal, mechanical, scientific or canonical state is promoted.",
        ],
    }


def continue_coupled_segment(checkpoint: Mapping[str, Any], *, years: int,
                             k_coef: float = SYNTHETIC_SPL_K,
                             precipitation_m_year: float = 0.15) -> dict[str, Any]:
    cp = verify_coupling_checkpoint(checkpoint)
    return run_coupled_segment(years=years, k_coef=k_coef,
                               precipitation_m_year=precipitation_m_year,
                               checkpoint=cp)
