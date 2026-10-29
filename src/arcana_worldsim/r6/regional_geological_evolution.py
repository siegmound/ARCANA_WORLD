"""Small noncanonical 2.5D drainage/material domain with restartable history.

The 3x3 elevation, rainfall, hydraulic and detachment parameters are explicitly
synthetic. Optional R6 C028/C029 states remain separate subsurface inputs and
are advanced by the existing unified orchestrator by the calling runner.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from typing import Any, Callable, Mapping

from .geological_surface_microdomain import SUPPORTS


SCHEMA = "ARCANA_R6_REGIONAL_GEOLOGICAL_STATE_V2"
FRONTIER_CHECKPOINT_SCHEMA = "ARCANA_R6_REGIONAL_FRONTIER_CHECKPOINT_V1"
GRAVITY_M_S2 = 9.80665


class RegionalModelError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


@dataclass(frozen=True)
class RegionalConfig:
    rows: int = 3
    columns: int = 3
    cell_area_m2: float = 1_000_000.0
    duration_years: int = 3
    precipitation_m_year: float = 0.15
    evapotranspiration_fraction: float = 0.10
    infiltration_fraction: float = 0.15
    runoff_fraction: float = 0.75
    outlet_cell: int = 8
    substrate_density_kg_m3: float = 2700.0
    initial_substrate_thickness_m: float = 100.0
    detachment_enabled: bool = True
    critical_shear_pa: float = 0.05
    detachment_kg_pa_s_m2: float = 1.0e-8
    channel_width_m: float = 100.0
    manning_n: float = 0.05
    transport_fraction_per_year: float = 0.8
    deposition_fraction: float = 0.25
    routing_mode: str = "DYNAMIC_TOPOGRAPHY"
    initial_elevation_offsets_m_by_cell: tuple[float, ...] = (0.0,) * 9
    prescribed_uplift_m_year_by_cell: tuple[float, ...] = (0.0,) * 9
    hydraulic_connectivity_edges: tuple[tuple[int, int], ...] = ()

    def validate(self) -> None:
        if self.rows < 2 or self.columns < 2 or self.duration_years < 1:
            raise RegionalModelError("GRID_OR_DURATION_INVALID")
        numbers = [self.cell_area_m2, self.precipitation_m_year,
                   self.evapotranspiration_fraction, self.infiltration_fraction,
                   self.runoff_fraction, self.substrate_density_kg_m3,
                   self.initial_substrate_thickness_m, self.critical_shear_pa,
                   self.detachment_kg_pa_s_m2, self.channel_width_m,
                   self.manning_n, self.transport_fraction_per_year,
                   self.deposition_fraction]
        if any(not math.isfinite(float(x)) for x in numbers):
            raise RegionalModelError("NONFINITE_CONFIG")
        if self.routing_mode not in {"FIXED_BASELINE", "DYNAMIC_TOPOGRAPHY"}:
            raise RegionalModelError("ROUTING_MODE_INVALID")
        if (len(self.initial_elevation_offsets_m_by_cell) != self.rows * self.columns
                or len(self.prescribed_uplift_m_year_by_cell) != self.rows * self.columns
                or any(not math.isfinite(float(x)) for x in
                       (*self.initial_elevation_offsets_m_by_cell,
                        *self.prescribed_uplift_m_year_by_cell))):
            raise RegionalModelError("TOPOGRAPHY_VECTOR_INVALID")
        declared_edges = set()
        for edge in self.hydraulic_connectivity_edges:
            if len(edge) != 2 or edge[0] == edge[1]:
                raise RegionalModelError("HYDRAULIC_EDGE_INVALID")
            a, b = sorted((int(edge[0]), int(edge[1])))
            if (a < 0 or b >= self.rows * self.columns
                    or b not in _neighbors(a, self.rows, self.columns)
                    or (a, b) in declared_edges):
                raise RegionalModelError("HYDRAULIC_EDGE_INVALID")
            declared_edges.add((a, b))
        if (self.cell_area_m2 <= 0 or self.precipitation_m_year < 0
                or min(self.evapotranspiration_fraction, self.infiltration_fraction,
                       self.runoff_fraction, self.transport_fraction_per_year,
                       self.deposition_fraction) < 0
                or self.evapotranspiration_fraction + self.infiltration_fraction
                + self.runoff_fraction > 1.0 + 1e-12
                or self.substrate_density_kg_m3 <= 0
                or self.initial_substrate_thickness_m < 0
                or self.critical_shear_pa < 0 or self.detachment_kg_pa_s_m2 < 0
                or self.channel_width_m <= 0 or self.manning_n <= 0
                or self.transport_fraction_per_year > 1
                or self.deposition_fraction > 1
                or not 0 <= self.outlet_cell < self.rows * self.columns):
            raise RegionalModelError("CONFIG_OUT_OF_RANGE")


def _neighbors(index: int, rows: int, cols: int) -> list[int]:
    r, c = divmod(index, cols)
    return [rr * cols + cc for rr, cc in
            ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
            if 0 <= rr < rows and 0 <= cc < cols]


def create_synthetic_region(config: RegionalConfig = RegionalConfig(), *,
                            source_identity: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Create a sloping 3x3 test basin; no R6 elevations are implied."""
    config.validate()
    default_elev = (12., 8., 4., 11., 6., 0., 10., 3., -2.)
    if config.rows * config.columns != 9:
        raise RegionalModelError("INITIAL_TOPOGRAPHY_FIXTURE_REQUIRES_3X3")
    cells = []
    for i, base_z in enumerate(default_elev):
        z = base_z + float(config.initial_elevation_offsets_m_by_cell[i])
        cells.append({
            "cell_id": f"SYNTHETIC_BASIN_3X3:C{i:02d}", "grid_index": i,
            "support_id": ("R6G1D-R091-C028" if i == 4 else
                           "R6G1D-R091-C029" if i == 5 else None),
            "plate_id": None, "plate_boundary_status": "UNKNOWN_NOT_INFERRED",
            "elevation_m": z, "initial_elevation_m": z,
            "bedrock_elevation_m": z, "initial_bedrock_elevation_m": z,
            "substrate_thickness_m": config.initial_substrate_thickness_m,
            "area_m2": config.cell_area_m2,
            "water_storage_m3": 0.0,
            "depression_storage_m3": 0.0,
            "substrate": {"material_id": f"SYNTHETIC_BENCHMARK_ROCK:C{i:02d}",
                          "class": "SYNTHETIC_BENCHMARK", "composition": "UNKNOWN",
                          "origin_id": f"INITIAL_SUBSTRATE:C{i:02d}",
                          "density_kg_m3": config.substrate_density_kg_m3,
                          "mass_kg": config.cell_area_m2 * config.initial_substrate_thickness_m
                                     * config.substrate_density_kg_m3},
            "initial_solid_mass_kg": config.cell_area_m2 * config.initial_substrate_thickness_m
                                     * config.substrate_density_kg_m3,
            "internal_material_in_kg": 0.0, "internal_material_out_kg": 0.0,
            "mobile_kg_by_material": {}, "suspended_kg_by_material": {},
            "deposits": [], "cumulative_eroded_kg": 0.0,
            "cumulative_deposited_kg": 0.0,
            "cumulative_exported_kg": 0.0,
            "cumulative_uplift_m": 0.0,
            "cumulative_vertical_flexure_m": 0.0,
        })
    drainage: dict[str, int | None]
    source = dict(source_identity or {"status": "SYNTHETIC_FIXTURE_ONLY"})
    r6_rows = {row.get("support_id"): row for row in source.get("support_cells", [])
               if isinstance(row, Mapping)}
    r6_bindings = {}
    for cell in cells:
        support = cell.get("support_id")
        if support:
            binding = r6_rows.get(support, {})
            r6_bindings[cell["cell_id"]] = {
                "support_id": support, "r6_grid_cell": binding.get("grid_cell"),
                "plate_id": binding.get("plate_id"),
                "experimental_grid_index": cell["grid_index"],
                "mapping_status": "EXPLICIT_SYNTHETIC_MICRODOMAIN_MAP_NOT_GEOGRAPHIC_CONTINUITY",
            }
            cell["plate_id"] = binding.get("plate_id")
    drainage = _drainage_for_elevation(cells, config)
    unperturbed_cells = json.loads(_canonical(cells))
    for i, offset in enumerate(config.initial_elevation_offsets_m_by_cell):
        unperturbed_cells[i]["elevation_m"] -= float(offset)
        unperturbed_cells[i]["bedrock_elevation_m"] -= float(offset)
    unperturbed_cfg = replace(config,
        initial_elevation_offsets_m_by_cell=(0.0,) * (config.rows * config.columns))
    unperturbed_targets = _drainage_for_elevation(unperturbed_cells, unperturbed_cfg)
    explicit_edges = {tuple(sorted((int(a), int(b))))
                      for a, b in config.hydraulic_connectivity_edges}
    interfaces = []
    for cell_a, cell_b in ((4, 5),):
        connected = tuple(sorted((cell_a, cell_b))) in explicit_edges
        interfaces.append({"cell_a": cells[cell_a]["cell_id"],
            "cell_b": cells[cell_b]["cell_id"],
            "source_boundary_id": source.get("t0_boundary_id"),
            "routing_status": ("EXPLICIT_EXPERIMENTAL_HYDRAULIC_CONNECTIVITY_ENABLED"
                               if connected else "BLOCKED_NO_CROSS_BOUNDARY_HYDROLOGY_LAW"),
            "connectivity_source": ("EXPERIMENT_CONFIG_ONLY" if connected else "NONE"),
            "mechanical_continuity": "UNKNOWN_NOT_INFERRED",
            "deep_transport": "DISABLED"})
    initial_condition_events = [
        {"kind": "INITIAL_TOPOGRAPHIC_PERTURBATION",
         "cell_id": cells[i]["cell_id"], "offset_m": float(offset),
         "time_year": 0, "authority": "EXPERIMENTAL_INITIAL_CONDITION"}
        for i, offset in enumerate(config.initial_elevation_offsets_m_by_cell) if offset
    ]
    if drainage != unperturbed_targets:
        initial_condition_events.append({
            "kind": "INITIAL_DRAINAGE_CONNECTIVITY_DIFFERENCE_FROM_REFERENCE",
            "time_year": 0,
            "reference_targets": unperturbed_targets,
            "experiment_targets": drainage,
            "cause": "DECLARED_INITIAL_TOPOGRAPHY_PERTURBATION",
            "authority": "SYNTHETIC_SCENARIO_COMPARISON_NOT_GEOLOGIC_EVENT"})
    state = {
        "schema": SCHEMA, "authority": "NONCANONICAL_SYNTHETIC_3X3_BASIN",
        "time_years": 0, "config": asdict(config),
        "source_identity": source,
        "source_identity_sha256": _sha(source),
        "r6_support_mapping": r6_bindings,
        "t0_boundary_reference": {"boundary_id": source.get("t0_boundary_id"),
            "length_m": source.get("t0_boundary_length_m"),
            "ordered_plate_pair": [5, 11],
            "referenced_experimental_grid_edge": ["SYNTHETIC_BASIN_3X3:C04",
                                                   "SYNTHETIC_BASIN_3X3:C05"],
            "hydraulic_connectivity_status": interfaces[0]["routing_status"],
            "status": "T0_TOPOLOGY_REFERENCE_ONLY_NO_TEMPORAL_MECHANICS_OR_HYDROLOGY_INFERRED"},
        "routing_mode": config.routing_mode,
        "interfaces": interfaces,
        "cells": cells, "drainage_targets": drainage,
        "baseline_drainage_targets": dict(drainage),
        "unperturbed_reference_drainage_targets": dict(unperturbed_targets),
        "routing_events": [],
        "initial_condition_events": initial_condition_events,
        "material_catalog": {cell["substrate"]["material_id"]: {
            "class": "SYNTHETIC_BENCHMARK", "composition": "UNKNOWN",
            "origin_id": cell["substrate"]["origin_id"], "source_cell_id": cell["cell_id"],
            "density_kg_m3": config.substrate_density_kg_m3}
            for cell in cells},
        "initial_totals": {
            "substrate_kg": sum(x["substrate"]["mass_kg"] for x in cells),
            "mobile_kg": 0.0, "deposited_kg": 0.0, "water_m3": 0.0,
        },
        "cumulative": {"precipitation_m3": 0.0, "evapotranspiration_m3": 0.0,
                        "infiltration_m3": 0.0, "water_export_m3": 0.0,
                        "substrate_eroded_kg": 0.0, "sediment_export_kg": 0.0},
        "records": [], "snapshots": [],
    }
    state["snapshots"].append({"time_year": 0, "cells": json.loads(_canonical(cells))})
    return state


def _hydraulic_radius_m(q_m3_s: float, slope: float, config: RegionalConfig) -> float:
    """Solve rectangular-channel Manning depth by bounded bisection."""
    if q_m3_s <= 0 or slope <= 0:
        return 0.0
    lo, hi = 0.0, 100.0
    for _ in range(64):
        depth = (lo + hi) * 0.5
        area = config.channel_width_m * depth
        perimeter = config.channel_width_m + 2.0 * depth
        rh = area / perimeter if perimeter else 0.0
        q = (area * rh ** (2.0 / 3.0) * math.sqrt(slope) / config.manning_n
             if depth else 0.0)
        if q < q_m3_s:
            lo = depth
        else:
            hi = depth
    depth = (lo + hi) * 0.5
    return config.channel_width_m * depth / (config.channel_width_m + 2 * depth)


def _drainage_for_elevation(cells: list[dict[str, Any]], cfg: RegionalConfig) -> dict[str, int | None]:
    targets: dict[str, int | None] = {}
    explicit_edges = {tuple(sorted((int(a), int(b))))
                      for a, b in cfg.hydraulic_connectivity_edges}
    for i, cell in enumerate(cells):
        if i == cfg.outlet_cell:
            targets[str(i)] = None
            continue
        lower = []
        for j in _neighbors(i, cfg.rows, cfg.columns):
            other = cells[j]
            mapped_support_edge = cell.get("support_id") and other.get("support_id")
            known_same_plate = (cell.get("plate_id") is not None
                                and cell.get("plate_id") == other.get("plate_id"))
            if (mapped_support_edge and not known_same_plate
                    and tuple(sorted((i, j))) not in explicit_edges):
                continue
            if other["elevation_m"] < cell["elevation_m"]:
                lower.append(j)
        targets[str(i)] = (min(lower, key=lambda j:
            (-(cell["elevation_m"] - cells[j]["elevation_m"]), j)) if lower else -1)
    return targets


def _geologic_load(cell: Mapping[str, Any]) -> dict[str, float | str]:
    """Bookkeeping surface-load diagnostic; not an isostatic stress model."""
    material_stock = {cell["substrate"]["material_id"]: cell["substrate"]["mass_kg"]}
    source_cell_ids = {cell["substrate"]["material_id"]: [cell["cell_id"]]}
    for compartment in (cell["mobile_kg_by_material"], cell["suspended_kg_by_material"]):
        for material_id, mass in compartment.items():
            material_stock[material_id] = material_stock.get(material_id, 0.0) + mass
    for deposit in cell["deposits"]:
        material_id = deposit["material_id"]
        material_stock[material_id] = material_stock.get(material_id, 0.0) + deposit["mass_kg"]
        source_cell_ids.setdefault(material_id, []).append(deposit["source_cell_id"])
    surface_stock = (sum(cell["mobile_kg_by_material"].values())
                     + sum(cell["suspended_kg_by_material"].values())
                     + sum(row["mass_kg"] for row in cell["deposits"]))
    delta_mass = (cell["substrate"]["mass_kg"] + surface_stock
                  - cell["initial_solid_mass_kg"])
    erosion_thickness = (float(cell["cumulative_eroded_kg"])
        / (float(cell["substrate"]["density_kg_m3"]) * float(cell["area_m2"])))
    deposition_thickness = sum(float(row["mass_kg"]) /
        (float(row["density_kg_m3"]) * float(cell["area_m2"]))
        for row in cell["deposits"])
    expected_elevation = (float(cell["initial_elevation_m"])
        + float(cell["cumulative_uplift_m"])
        + float(cell.get("cumulative_vertical_flexure_m", 0.0))
        - erosion_thickness + deposition_thickness)
    geometry_residual = float(cell["elevation_m"]) - expected_elevation
    area = float(cell["area_m2"])
    return {"cell_id": cell["cell_id"], "area_m2": area,
        "substrate_eroded_kg": float(cell["cumulative_eroded_kg"]),
        "deposited_kg": float(cell["cumulative_deposited_kg"]),
        "exported_kg": float(cell["cumulative_exported_kg"]),
        "in_transit_or_stored_kg": surface_stock,
        "material_stock_kg_by_id": material_stock,
        "material_source_cell_ids_by_id": {
            key: sorted(set(value)) for key, value in source_cell_ids.items()},
        "surface_load_change_kg": delta_mass,
        "surface_elevation_m": float(cell["elevation_m"]),
        "elevation_change_due_to_uplift_m": float(cell["cumulative_uplift_m"]),
        "elevation_change_due_to_vertical_flexure_m": float(
            cell.get("cumulative_vertical_flexure_m", 0.0)),
        "elevation_change_due_to_bedrock_erosion_m": -erosion_thickness,
        "elevation_change_due_to_deposition_m": deposition_thickness,
        "geometry_balance_residual_m": geometry_residual,
        "column_equivalent_pressure_change_pa": delta_mass * GRAVITY_M_S2 / area,
        "pressure_authority": "BOOKKEEPING_DIAGNOSTIC_NOT_ISOSTATIC_OR_LITHOSTATIC_STRESS"}


def _routing_order(targets: Mapping[str, int | None]) -> list[int]:
    """Deterministic source-to-sink order; rejects any cyclic routing graph."""
    count = len(targets)
    downstream_count = [0] * count
    upstream = [[] for _ in range(count)]
    for source_text, target in targets.items():
        source = int(source_text)
        if target is not None and target >= 0:
            if target >= count or target == source:
                raise RegionalModelError("ROUTING_TARGET_INVALID")
            downstream_count[target] += 1
            upstream[source].append(target)
    ready = sorted(i for i, n in enumerate(downstream_count) if n == 0)
    order = []
    while ready:
        source = ready.pop(0)
        order.append(source)
        for target in upstream[source]:
            downstream_count[target] -= 1
            if downstream_count[target] == 0:
                ready.append(target)
                ready.sort()
    if len(order) != count:
        raise RegionalModelError("ROUTING_CYCLE_DETECTED")
    return order


def advance_region(state: Mapping[str, Any], *, years: int,
                   config: RegionalConfig | None = None,
                   precipitation_m_year_by_cell: list[float] | None = None,
                   history_consumer: Callable[[str, Mapping[str, Any]], None] | None = None) -> dict[str, Any]:
    """Advance annual routing; material flows are mass-conservative and ID preserving."""
    cfg = config or RegionalConfig(**state["config"])
    cfg.validate()
    if state.get("schema") != SCHEMA or state.get("source_identity_sha256") != _sha(state["source_identity"]):
        raise RegionalModelError("STATE_SCHEMA_OR_SOURCE_IDENTITY_INVALID")
    if years < 1 or state["time_years"] + years > cfg.duration_years:
        raise RegionalModelError("SEGMENT_DURATION_OUT_OF_RANGE")
    precip = (precipitation_m_year_by_cell if precipitation_m_year_by_cell is not None
              else [cfg.precipitation_m_year] * 9)
    if len(precip) != 9 or any(not math.isfinite(x) or x < 0 for x in precip):
        raise RegionalModelError("PRECIPITATION_VECTOR_INVALID")
    out = json.loads(_canonical(dict(state)))
    cells = out["cells"]
    out.setdefault("records", [])
    out.setdefault("snapshots", [])
    out.setdefault("routing_events", [])
    out.setdefault("initial_condition_events", [])
    all_events = []
    for _ in range(years):
        year = out["time_years"] + 1
        uplift_events = []
        for i, rate in enumerate(cfg.prescribed_uplift_m_year_by_cell):
            if rate:
                cell = cells[i]
                cell["elevation_m"] += float(rate)
                cell["bedrock_elevation_m"] += float(rate)
                cell["cumulative_uplift_m"] += float(rate)
                uplift_events.append({"kind": "PRESCRIBED_SYNTHETIC_UPLIFT",
                    "cell_id": cell["cell_id"], "uplift_m": float(rate), "time_year": year,
                    "authority": "EXPERIMENTAL_PRESCRIBED_INPUT"})
        old_targets = dict(out["drainage_targets"])
        if cfg.routing_mode == "FIXED_BASELINE":
            out["drainage_targets"] = dict(out["baseline_drainage_targets"])
        else:
            out["drainage_targets"] = _drainage_for_elevation(cells, cfg)
        route_event = None
        if out["drainage_targets"] != old_targets:
            route_event = {"kind": "DRAINAGE_CONNECTIVITY_CHANGED",
                "time_year": year, "routing_mode": cfg.routing_mode,
                "previous_targets": old_targets,
                "updated_targets": dict(out["drainage_targets"]),
                "cause": "TOPOGRAPHY_UPDATED_OR_REEVALUATED"}
            out["routing_events"].append(route_event)
            if history_consumer is not None:
                history_consumer("REGIONAL_EVENT", route_event)
        step_elevation = [float(cell["elevation_m"]) for cell in cells]
        water_before = sum(c["water_storage_m3"] for c in cells)
        water_in = et_total = infiltration_total = water_export = 0.0
        water_cell = [{"initial_storage_m3": c["water_storage_m3"], "precipitation_m3": 0.0,
                       "evapotranspiration_m3": 0.0, "infiltration_m3": 0.0,
                       "internal_in_m3": 0.0, "internal_out_m3": 0.0,
                       "outlet_export_m3": 0.0} for c in cells]
        for i, cell in enumerate(cells):
            rain = precip[i] * cell["area_m2"]
            water_cell[i]["precipitation_m3"] = rain
            cell["water_storage_m3"] += rain
            water_in += rain
            et = min(cell["water_storage_m3"], rain * cfg.evapotranspiration_fraction)
            infiltration = min(cell["water_storage_m3"] - et,
                               rain * cfg.infiltration_fraction)
            runoff = min(cell["water_storage_m3"] - et - infiltration,
                         (rain + water_cell[i]["initial_storage_m3"])
                         * cfg.runoff_fraction)
            cell["water_storage_m3"] -= et + infiltration + runoff
            et_total += et
            infiltration_total += infiltration
            water_cell[i]["evapotranspiration_m3"] = et
            water_cell[i]["infiltration_m3"] = infiltration
            cell["_runoff_m3"] = runoff
        # A deterministic topological order handles both current dynamic routes
        # and the preserved fixed baseline, independent of updated elevations.
        order = _routing_order(out["drainage_targets"])
        year_events = [*uplift_events]
        if route_event:
            year_events.append(route_event)
        for i in order:
            cell = cells[i]
            qvol = cell.pop("_runoff_m3")
            # Add routed upstream flow accumulated in this transient field.
            qvol += cell.pop("_incoming_water_m3", 0.0)
            target = out["drainage_targets"][str(i)]
            if target == -1:
                # Closed topographic depression: retain runoff rather than
                # invent an outlet or uphill route.
                cell["water_storage_m3"] += qvol
                cell["depression_storage_m3"] += qvol
                continue
            released = min(cell["depression_storage_m3"], qvol)
            cell["depression_storage_m3"] -= released
            if target is None:
                water_export += qvol
                water_cell[i]["outlet_export_m3"] += qvol
                year_events.append({"kind": "WATER_ROUTING", "source_cell_id": cell["cell_id"],
                    "destination_cell_id": "BASIN_OUTLET", "water_m3": qvol, "time_year": year})
                # Outlet exports all arriving suspended/mobile solids too.
                for compartment in (cell["mobile_kg_by_material"], cell["suspended_kg_by_material"]):
                    for mid, mass in sorted(compartment.items()):
                        if mass:
                            cell["cumulative_exported_kg"] += mass
                            out["cumulative"]["sediment_export_kg"] += mass
                            year_events.append({"kind": "SEDIMENT_EXPORT", "material_id": mid,
                                "mass_kg": mass, "source_cell_id": cell["cell_id"],
                                "destination_cell_id": "BASIN_OUTLET", "time_year": year})
                        compartment[mid] = 0.0
                continue
            drop = step_elevation[i] - step_elevation[target]
            if cfg.routing_mode == "FIXED_BASELINE" and drop <= 0:
                # Keep the legacy graph as a comparator without routing water
                # uphill when a later topographic state reverses that edge.
                cell["water_storage_m3"] += qvol
                cell["depression_storage_m3"] += qvol
                year_events.append({"kind": "FIXED_BASELINE_EDGE_CLOSED_BY_NONPOSITIVE_SLOPE",
                    "source_cell_id": cell["cell_id"],
                    "destination_cell_id": cells[target]["cell_id"],
                    "slope": drop / 1_000.0, "time_year": year,
                    "authority": "SYNTHETIC_FIXED_GRAPH_COMPARATOR"})
                continue
            slope = drop / 1_000.0
            q = qvol / 31_557_600.0
            rh = _hydraulic_radius_m(q, slope, cfg)
            tau = 1000.0 * 9.80665 * rh * slope
            eroded = 0.0
            if cfg.detachment_enabled and tau > cfg.critical_shear_pa:
                requested = (cfg.detachment_kg_pa_s_m2 * (tau - cfg.critical_shear_pa)
                             * 31_557_600.0 * cell["area_m2"])
                eroded = min(requested, cell["substrate"]["mass_kg"])
                cell["substrate"]["mass_kg"] -= eroded
                cell["cumulative_eroded_kg"] += eroded
                erosion_thickness = eroded / (cell["substrate"]["density_kg_m3"] * cell["area_m2"])
                cell["substrate_thickness_m"] -= erosion_thickness
                cell["bedrock_elevation_m"] -= erosion_thickness
                cell["elevation_m"] -= erosion_thickness
                out["cumulative"]["substrate_eroded_kg"] += eroded
                mid = cell["substrate"]["material_id"]
                cell["mobile_kg_by_material"][mid] = cell["mobile_kg_by_material"].get(mid, 0.) + eroded
                year_events.append({"kind": "BEDROCK_EROSION", "material_id": mid,
                    "origin_id": cell["substrate"]["origin_id"], "mass_kg": eroded,
                    "source_cell_id": cell["cell_id"], "destination_cell_id": cell["cell_id"],
                    "time_year": year, "process": "SYNTHETIC_BED_SHEAR_THRESHOLD_DETACHMENT"})
            mobile = cell["mobile_kg_by_material"]
            moved = {mid: mobile[mid] * cfg.transport_fraction_per_year for mid in sorted(mobile)}
            for mid in sorted(moved):
                mass = moved[mid]
                mobile[mid] -= mass
                cell["internal_material_out_kg"] += mass
                dep = mass * cfg.deposition_fraction
                remain = mass - dep
                dst = cells[target]
                dst["internal_material_in_kg"] += mass
                if dep:
                    dst["deposits"].append({"material_id": mid, "mass_kg": dep,
                        "density_kg_m3": out["material_catalog"][mid]["density_kg_m3"],
                        "source_cell_id": cell["cell_id"], "destination_cell_id": dst["cell_id"],
                        "erosion_time_year": year, "transport_time_year": year,
                        "deposition_time_year": year, "event_id": f"Y{year}:C{i:02d}->{target:02d}:{mid}"})
                    dst["cumulative_deposited_kg"] += dep
                    dst["elevation_m"] += (dep / (out["material_catalog"][mid]["density_kg_m3"]
                                                     * dst["area_m2"]))
                    year_events.append({"kind": "DEPOSITION", "material_id": mid,
                        "mass_kg": dep, "source_cell_id": cell["cell_id"],
                        "destination_cell_id": dst["cell_id"], "time_year": year})
                # Remaining load moves downstream as suspended material.
                dst["suspended_kg_by_material"][mid] = dst["suspended_kg_by_material"].get(mid, 0.) + remain
                year_events.append({"kind": "TRANSPORT", "material_id": mid,
                    "mass_kg": mass, "source_cell_id": cell["cell_id"],
                    "destination_cell_id": dst["cell_id"], "time_year": year})
            # Incoming suspended material is available for downstream transport.
            for mid, mass in sorted(cell["suspended_kg_by_material"].items()):
                cell["suspended_kg_by_material"][mid] = 0.0
                if target == cfg.outlet_cell:
                    cell["cumulative_exported_kg"] += mass
                    out["cumulative"]["sediment_export_kg"] += mass
                    year_events.append({"kind": "SEDIMENT_EXPORT", "material_id": mid,
                        "mass_kg": mass, "source_cell_id": cell["cell_id"],
                        "destination_cell_id": "BASIN_OUTLET", "time_year": year})
                else:
                    cell["internal_material_out_kg"] += mass
                    cells[target]["internal_material_in_kg"] += mass
                    cells[target]["mobile_kg_by_material"][mid] = cells[target]["mobile_kg_by_material"].get(mid, 0.) + mass
                    year_events.append({"kind": "TRANSPORT", "material_id": mid,
                        "mass_kg": mass, "source_cell_id": cell["cell_id"],
                        "destination_cell_id": cells[target]["cell_id"], "time_year": year,
                        "phase": "SUSPENDED_LOAD_ROUTING"})
            if qvol:
                cells[target]["_incoming_water_m3"] = cells[target].get("_incoming_water_m3", 0.) + qvol
                water_cell[i]["internal_out_m3"] += qvol
                water_cell[target]["internal_in_m3"] += qvol
                year_events.append({"kind": "WATER_ROUTING", "source_cell_id": cell["cell_id"],
                    "destination_cell_id": cells[target]["cell_id"], "water_m3": qvol,
                    "time_year": year})
            year_events.append({"kind": "HYDRAULIC_DIAGNOSTIC", "cell_id": cell["cell_id"],
                "runoff_m3": qvol, "slope": slope, "hydraulic_radius_m": rh,
                "bed_shear_pa": tau, "substrate_erosion_kg": eroded})
        for cell in cells:
            cell.pop("_incoming_water_m3", None)
        targets_used = dict(out["drainage_targets"])
        if cfg.routing_mode == "DYNAMIC_TOPOGRAPHY":
            updated_targets = _drainage_for_elevation(cells, cfg)
            if updated_targets != targets_used:
                geomorphic_route_event = {
                    "kind": "DRAINAGE_CONNECTIVITY_CHANGED",
                    "detected_at_year": year,
                    "effective_from_year": year + 1,
                    "routing_mode": cfg.routing_mode,
                    "previous_targets": targets_used,
                    "updated_targets": updated_targets,
                    "cause": "EROSION_DEPOSITION_OR_UPLIFT_CHANGED_TOPOGRAPHY",
                }
                year_events.append(geomorphic_route_event)
                out["routing_events"].append(geomorphic_route_event)
            out["drainage_targets"] = updated_targets
        water_after = sum(c["water_storage_m3"] for c in cells)
        out["cumulative"]["precipitation_m3"] += water_in
        out["cumulative"]["evapotranspiration_m3"] += et_total
        out["cumulative"]["infiltration_m3"] += infiltration_total
        out["cumulative"]["water_export_m3"] += water_export
        water_resid = water_before + water_in - et_total - infiltration_total - water_export - water_after
        water_roundoff = 64.0 * math.ulp(max(abs(water_before), abs(water_in), abs(water_after), 1.0))
        per_cell_water = []
        for idx, c in enumerate(cells):
            wb = water_cell[idx]
            residual = (wb["initial_storage_m3"] + wb["precipitation_m3"]
                + wb["internal_in_m3"] - wb["evapotranspiration_m3"]
                - wb["infiltration_m3"] - wb["internal_out_m3"]
                - wb["outlet_export_m3"] - c["water_storage_m3"])
            per_cell_water.append({"cell_id": c["cell_id"], **wb,
                                   "final_storage_m3": c["water_storage_m3"],
                                   "residual_m3": residual,
                                   "roundoff_tolerance_m3": 64.0 * math.ulp(max(
                                       abs(wb["initial_storage_m3"]), abs(wb["precipitation_m3"]),
                                       abs(c["water_storage_m3"]), 1.0))})
        initial_solid = out["initial_totals"]["substrate_kg"] + out["initial_totals"]["mobile_kg"] + out["initial_totals"]["deposited_kg"]
        final_solid = (sum(c["substrate"]["mass_kg"] for c in cells)
                       + sum(sum(c["mobile_kg_by_material"].values()) + sum(c["suspended_kg_by_material"].values())
                             + sum(d["mass_kg"] for d in c["deposits"]) for c in cells)
                       + out["cumulative"]["sediment_export_kg"])
        solid_resid = initial_solid - final_solid
        solid_roundoff = 64.0 * math.ulp(max(abs(initial_solid), abs(final_solid), 1.0))
        cell_balances = []
        for c in cells:
            material_stock = (c["substrate"]["mass_kg"]
                + sum(c["mobile_kg_by_material"].values())
                + sum(c["suspended_kg_by_material"].values())
                + sum(d["mass_kg"] for d in c["deposits"]))
            cell_balances.append({"cell_id": c["cell_id"],
                "initial_solid_kg": c["initial_solid_mass_kg"],
                "internal_in_kg": c["internal_material_in_kg"],
                "internal_out_kg": c["internal_material_out_kg"],
                "substrate_eroded_kg_cumulative": c["cumulative_eroded_kg"],
                "exported_kg_cumulative": c["cumulative_exported_kg"],
                "current_stock_kg": material_stock,
                "local_residual_kg": c["initial_solid_mass_kg"]
                    + c["internal_material_in_kg"] - c["internal_material_out_kg"]
                    - c["cumulative_exported_kg"] - material_stock,
                "roundoff_tolerance_kg": 64.0 * math.ulp(max(
                    abs(c["initial_solid_mass_kg"]), abs(material_stock), 1.0))})
        record = {"time_year": year, "events": year_events,
                  "drainage_targets_used": targets_used,
                  "drainage_targets_after_geomorphology": dict(out["drainage_targets"]),
                  "depression_storage_m3_by_cell": {
                      c["cell_id"]: c["depression_storage_m3"] for c in cells},
                  "geologic_load_by_cell": [_geologic_load(c) for c in cells],
                  "water_balance_m3": {"initial_storage": water_before, "precipitation": water_in,
                      "evapotranspiration": et_total, "infiltration": infiltration_total,
                      "outlet_export": water_export, "final_storage": water_after,
                      "residual": water_resid, "roundoff_tolerance": water_roundoff,
                      "per_cell": per_cell_water},
                  "solid_mass_balance_kg": {"initial_stock": initial_solid,
                      "final_including_export": final_solid, "residual": solid_resid,
                      "roundoff_tolerance_kg": solid_roundoff,
                      "substrate_erosion_is_internal_transfer": True,
                      "per_cell": cell_balances}}
        all_events.extend(year_events)
        out["records"].append(record)
        out["time_years"] = year
        snapshot = {"time_year": year, "cells": json.loads(_canonical(cells))}
        out["snapshots"].append(snapshot)
        if history_consumer is not None:
            history_consumer("REGIONAL_YEAR_RECORD", record)
            for event in year_events:
                if event is not route_event:
                    history_consumer("REGIONAL_EVENT", event)
            history_consumer("REGIONAL_SNAPSHOT", snapshot)
    return out


def seal_regional_checkpoint(state: Mapping[str, Any], *, unified_checkpoint: Mapping[str, Any] | None = None) -> dict[str, Any]:
    schema = FRONTIER_CHECKPOINT_SCHEMA if state.get("history_independent_continuation") is True else SCHEMA
    payload = {"schema": schema, "regional_state": dict(state),
               "unified_checkpoint": dict(unified_checkpoint) if unified_checkpoint else None}
    return {**payload, "checkpoint_sha256": _sha(payload)}


def verify_regional_checkpoint(checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    payload = {k: v for k, v in checkpoint.items() if k != "checkpoint_sha256"}
    schema = checkpoint.get("schema")
    if schema not in {SCHEMA, FRONTIER_CHECKPOINT_SCHEMA} or checkpoint.get("checkpoint_sha256") != _sha(payload):
        raise RegionalModelError("CHECKPOINT_DIGEST_OR_SCHEMA_INVALID")
    state = checkpoint.get("regional_state")
    if not isinstance(state, dict) or state.get("schema") != SCHEMA:
        raise RegionalModelError("CHECKPOINT_REGION_INVALID")
    if state.get("source_identity_sha256") != _sha(state.get("source_identity")):
        raise RegionalModelError("CHECKPOINT_SOURCE_BINDING_INVALID")
    if schema == FRONTIER_CHECKPOINT_SCHEMA:
        if state.get("history_independent_continuation") is not True:
            raise RegionalModelError("CHECKPOINT_FRONTIER_MODE_INVALID")
        if {"records", "snapshots", "routing_events", "initial_condition_events"}.intersection(state):
            raise RegionalModelError("CHECKPOINT_FRONTIER_CONTAINS_HISTORY")
        unified_cp = checkpoint.get("unified_checkpoint")
        if not isinstance(unified_cp, Mapping) or unified_cp.get("schema") != "ARCANA_R6_UNIFIED_MULTIPHYSICS_CHECKPOINT_V2":
            raise RegionalModelError("CHECKPOINT_UNIFIED_FRONTIER_REQUIRED")
        try:
            from .unified_multiphysics_microdomain import verify_unified_checkpoint
            unified_state = verify_unified_checkpoint(unified_cp)
        except (ValueError, TypeError, KeyError) as exc:
            raise RegionalModelError("CHECKPOINT_UNIFIED_FRONTIER_INVALID") from exc
        if unified_state.get("elapsed_external_steps") != state.get("time_years"):
            raise RegionalModelError("CHECKPOINT_FRONTIER_TIME_MISMATCH")
    return state


def query_materials_at_time(result: Mapping[str, Any], *, time_year: int,
                            cell_id: str | None = None) -> list[dict[str, Any]]:
    state = result.get("state", result)
    snapshot = next((row for row in state.get("snapshots", []) if row["time_year"] == time_year), None)
    if snapshot is None:
        raise RegionalModelError("TIME_NOT_ARCHIVED")
    cells = snapshot["cells"] if cell_id is None else [c for c in snapshot["cells"] if c["cell_id"] == cell_id]
    if cell_id is not None and not cells:
        raise RegionalModelError("CELL_NOT_FOUND")
    return [{"time_year": time_year, "cell_id": c["cell_id"],
             "substrate": c["substrate"], "mobile_kg_by_material": c["mobile_kg_by_material"],
             "suspended_kg_by_material": c["suspended_kg_by_material"], "deposits": c["deposits"]}
            for c in cells]


def query_material_provenance(result: Mapping[str, Any], material_id: str) -> list[dict[str, Any]]:
    state = result.get("state", result)
    return [event for row in state["records"] for event in row["events"]
            if event.get("material_id") == material_id]


def query_deep_inventory(result: Mapping[str, Any], *, cell_id: str,
                         time_year: int | None = None) -> dict[str, Any]:
    state = result.get("state", result)
    cell = next((c for c in state["cells"] if c["cell_id"] == cell_id), None)
    if cell is None:
        raise RegionalModelError("CELL_NOT_FOUND")
    support = cell.get("support_id")
    if support is None:
        return {"status": "UNKNOWN_NO_VERIFIED_R6_COLUMN"}
    if time_year is None:
        return result.get("subsurface_by_support", {}).get(
            support, {"status": "UNKNOWN_SUBSURFACE_SNAPSHOT"})
    cp = result.get("checkpoint", {}).get("unified_checkpoint")
    if not isinstance(cp, Mapping):
        raise RegionalModelError("UNIFIED_SUBSURFACE_CHECKPOINT_MISSING")
    from .unified_multiphysics_microdomain import verify_unified_checkpoint
    saved = verify_unified_checkpoint(cp)
    volume_id = f"{support}:DEEP:RESERVOIR:00"
    if time_year == 0:
        cfg = saved["run_identity"]["config"]
        inventory = dict(zip(SUPPORTS, cfg["deep_initial_inventory_j_by_support"]))
        return {"time_year": 0, "volume_id": volume_id, "inventory_j": inventory[support],
                "authority": "SYNTHETIC_INITIAL_DEEP_INVENTORY"}
    record = next((row for row in saved["records"]
                   if math.isclose(float(row["elapsed_years"]), float(time_year),
                                   rel_tol=0.0, abs_tol=1e-12)), None)
    if record is None:
        raise RegionalModelError("TIME_NOT_ARCHIVED")
    return {"time_year": time_year, "volume_id": volume_id,
            "inventory_j": record["deep"]["inventory_j_by_material_volume"][volume_id],
            "authority": "UNIFIED_ORCHESTRATOR_SYNTHETIC_DEEP_DIAGNOSTIC"}


def run_regional_segment(initial_states_by_support: Mapping[str, Any],
                         source_identity: Mapping[str, Any], *,
                         config: RegionalConfig = RegionalConfig(),
                         segment_years: int,
                         checkpoint: Mapping[str, Any] | None = None,
                         history_independent_continuation: bool = False,
                         history_consumer: Callable[[str, Mapping[str, Any]], None] | None = None) -> dict[str, Any]:
    """Advance surface network and the compatible R6 columns on the same clock.

    The existing unified orchestrator advances C028/C029 thermomechanics and
    Deep on the same clock. Surface cells retain explicit support mappings;
    no unimplemented surface feedback into those kernels is implied.
    """
    from .unified_multiphysics_microdomain import (
        UnifiedConfig, continue_unified_microdomain, run_unified_microdomain,
    )

    config.validate()
    if segment_years < 1 or segment_years > config.duration_years:
        raise RegionalModelError("SEGMENT_DURATION_INVALID")
    if history_independent_continuation and history_consumer is None:
        raise RegionalModelError("REGIONAL_HISTORY_CONSUMER_REQUIRED")
    unified_config = UnifiedConfig(
        duration_years=float(config.duration_years), external_step_years=1.0,
        hydrology_dt_seconds=31_557_600.0,
        opening_rate_m_year=0.01,
        prescribed_uplift_total_m_by_support=(0.1, 0.0),
        precipitation_m_year_by_support=(0.0, 0.0),
        evapotranspiration_m_year_by_support=(0.0, 0.0),
        infiltration_capacity_m_year_by_support=(0.0, 0.0),
        substrate_erosion_enabled=False,
    )
    history_configuration = {"regional_config": asdict(config),
                             "unified_config": asdict(unified_config)}
    from .int10k_history_independent import (
        CHECKPOINT_SCHEMA as HISTORY_FREE_SCHEMA,
        seal_history_independent_checkpoint, verify_history_independent_checkpoint,
    )
    history_free_checkpoint = False
    if checkpoint is not None and checkpoint.get("schema") == HISTORY_FREE_SCHEMA:
        if not history_independent_continuation:
            raise RegionalModelError("HISTORY_FREE_CHECKPOINT_REQUIRES_HISTORY_INDEPENDENT_MODE")
        checkpoint = verify_history_independent_checkpoint(
            checkpoint, source_identity=source_identity, configuration=history_configuration)
        history_free_checkpoint = True
    if checkpoint is None:
        region = create_synthetic_region(config, source_identity=source_identity)
        if history_independent_continuation and history_consumer is not None:
            history_consumer("REGIONAL_SNAPSHOT", region["snapshots"][0])
            for event in region["initial_condition_events"]:
                history_consumer("REGIONAL_EVENT", event)
        unified = run_unified_microdomain(
            initial_states_by_support, source_identity,
            config=unified_config, segment_years=float(segment_years),
            history_independent_continuation=history_independent_continuation,
            history_consumer=history_consumer)
    else:
        region = verify_regional_checkpoint(checkpoint)
        if region.get("history_independent_continuation") is True and not history_independent_continuation:
            raise RegionalModelError("REGIONAL_HISTORY_INDEPENDENT_MODE_REQUIRED")
        if region["source_identity_sha256"] != _sha(dict(source_identity)):
            raise RegionalModelError("REGIONAL_CHECKPOINT_SOURCE_MISMATCH")
        if _canonical(region["config"]) != _canonical(asdict(config)):
            raise RegionalModelError("REGIONAL_CHECKPOINT_CONFIG_MISMATCH")
        if int(region["time_years"]) + segment_years > config.duration_years:
            raise RegionalModelError("SEGMENT_EXCEEDS_PLANNED_DURATION")
        prior_unified = checkpoint.get("unified_checkpoint")
        if not isinstance(prior_unified, Mapping):
            raise RegionalModelError("UNIFIED_SUBSURFACE_CHECKPOINT_MISSING")
        unified = continue_unified_microdomain(
            prior_unified, source_identity, config=unified_config,
            segment_years=float(segment_years),
            history_independent_continuation=history_independent_continuation,
            history_consumer=history_consumer)
    region = advance_region(region, years=segment_years, config=config,
                            history_consumer=history_consumer)
    final = unified["final"]
    subsurface_by_support = {}
    for support in SUPPORTS:
        volume_id = f"{support}:DEEP:RESERVOIR:00"
        subsurface_by_support[support] = {
            "source_status": "R6_T0_HASH_VERIFIED_THEN_ADVANCED_BY_UNIFIED_ORCHESTRATOR",
            "support_id": support,
            "final_thermal_state": final["thermal_states"][support],
            "deep_volume_id": volume_id,
            "deep_inventory_j": final["deep_inventory_j_by_volume"][volume_id],
        }
    if history_independent_continuation:
        checkpoint_region = json.loads(_canonical(region))
        checkpoint_region["history_independent_continuation"] = True
        for key in ("records", "snapshots", "routing_events", "initial_condition_events"):
            checkpoint_region.pop(key, None)
        engine_checkpoint = seal_regional_checkpoint(
            checkpoint_region, unified_checkpoint=unified["continuation"])
        combined = seal_history_independent_checkpoint(
            engine_checkpoint, time_year=int(region["time_years"]),
            source_identity=source_identity, configuration=history_configuration)
    else:
        combined = seal_regional_checkpoint(region, unified_checkpoint=unified["continuation"])
    return {
        "schema": "ARCANA_R6_REGIONAL_GEOLOGICAL_RESULT_V2",
        "authority": "NONCANONICAL_EXPERIMENTAL; SURFACE FORCING SYNTHETIC",
        **({"history_output_coverage": {
            "mode": "EXTERNAL_CONSUMER" if history_independent_continuation else "LEGACY_IN_MEMORY",
            "history_free_checkpoint_input": history_free_checkpoint,
            "regional_records": [row["time_year"] for row in region.get("records", [])],
            "regional_snapshots": [row["time_year"] for row in region.get("snapshots", [])],
            "unified_steps": [row["step"] for row in unified.get("steps", [])],
        }} if history_independent_continuation else {}),
        "source_identity": dict(source_identity), "state": region,
        "subsurface_by_support": subsurface_by_support,
        "checkpoint": combined, "subsurface_unified_result": unified,
        "balances": {
            "water": region["records"][-1]["water_balance_m3"] if region["records"] else {},
            "solid_mass_kg": region["records"][-1]["solid_mass_balance_kg"] if region["records"] else {},
            "deep": unified["integrated_balances"]["deep"],
        },
        "authority_limits": [
            "The 3x3 terrain, rain, channel network, material IDs, densities and erosion parameters are synthetic.",
            "Only C028/C029 subsurface initial columns are hash-verified R6 inputs; other subsurface fields remain UNKNOWN.",
            "B5 is T0 topology only; no positive-time plate-boundary law is inferred.",
            "Surface hydrology is not fed back into the thermal, mechanical or Deep kernel.",
            "Deep transport remains the existing diagnostic synthetic reservoir and receives no energy from material changes.",
            "No lithification, chemical weathering, metamorphism or canonical history write is performed.",
        ],
    }
