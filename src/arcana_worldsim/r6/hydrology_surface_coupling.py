"""Bounded water/sediment/surface coupling for the R6 C028/C029 microdomain.

R6 subsurface states and T0 support geometry are hash-bound inputs. Climate,
channel dimensions, roughness, infiltration, mobile-cover properties, and
sediment-capacity parameters are synthetic experiment inputs. The channel
flow uses Manning's equation; sediment capacity is an explicitly empirical
power-law sensitivity, not a calibrated production erosion model.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from .geological_surface_microdomain import (
    SUPPORTS,
    SurfaceConfig,
    SurfaceMicrodomainError,
    _surface_grid_geometry,
    load_verified_r6_initial_columns,
    run_surface_microdomain,
)


SECONDS_PER_YEAR = 31_557_600.0


@dataclass(frozen=True)
class HydroConfig:
    duration_years: float = 3.0
    hydrology_dt_seconds: float = 3600.0
    precipitation_m_year_by_support: tuple[float, float] = (0.40, 0.20)
    precipitation_schedule_m_year_by_support: tuple[tuple[float, float], ...] | None = None
    initial_water_storage_m3_by_support: tuple[float, float] = (0.0, 0.0)
    initial_suspended_sediment_kg_by_support: tuple[float, float] = (0.0, 0.0)
    initial_mobile_material_kg_by_support: tuple[Mapping[str, float], Mapping[str, float]] | None = None
    initial_suspended_material_kg_by_support: tuple[Mapping[str, float], Mapping[str, float]] | None = None
    initial_substrate_mass_kg_by_support: tuple[float, float] = (0.0, 0.0)
    substrate_material_id_by_support: tuple[str, str] = ("SYNTHETIC_SUBSTRATE_0", "SYNTHETIC_SUBSTRATE_1")
    substrate_density_kg_m3_by_support: tuple[float, float] = (2700.0, 2700.0)
    substrate_erosion_enabled: bool = False
    substrate_critical_shear_pa: float = 0.0
    substrate_detachment_kg_pa_s: float = 0.0
    water_density_kg_m3: float = 1000.0
    gravity_m_s2: float = 9.80665
    evapotranspiration_m_year_by_support: tuple[float, float] = (0.08, 0.08)
    infiltration_capacity_m_year_by_support: tuple[float, float] = (0.12, 0.12)
    manning_n: float = 0.05
    outlet_open: bool = False
    outlet_distance_m: float = 1_000.0
    outlet_drop_below_bedrock_m: float = 1.0
    sediment_transport_enabled: bool = True
    sediment_capacity_reference_kg_m3: float = 0.05
    sediment_reference_discharge_m3_s: float = 1.0
    sediment_reference_slope: float = 1.0e-3
    sediment_discharge_exponent: float = 0.5
    sediment_slope_exponent: float = 0.5
    surface_config: SurfaceConfig = SurfaceConfig(enable_surface_transport=False)

    def validate(self) -> None:
        scalar_values = (
            self.duration_years, self.hydrology_dt_seconds, self.manning_n,
            self.outlet_distance_m, self.outlet_drop_below_bedrock_m,
            self.sediment_capacity_reference_kg_m3,
            self.sediment_reference_discharge_m3_s,
            self.sediment_reference_slope, self.sediment_discharge_exponent,
            self.sediment_slope_exponent,
            self.substrate_critical_shear_pa, self.substrate_detachment_kg_pa_s,
            self.water_density_kg_m3, self.gravity_m_s2,
            *self.initial_substrate_mass_kg_by_support,
            *self.substrate_density_kg_m3_by_support,
        )
        if any(not math.isfinite(value) for value in scalar_values):
            raise SurfaceMicrodomainError("HYDRO_CONFIG_NONFINITE")
        if (self.duration_years <= 0 or self.hydrology_dt_seconds <= 0
                or self.hydrology_dt_seconds > SECONDS_PER_YEAR
                or self.manning_n <= 0 or self.outlet_distance_m <= 0
                or self.outlet_drop_below_bedrock_m < 0
                or self.sediment_capacity_reference_kg_m3 < 0
                or self.sediment_reference_discharge_m3_s <= 0
                or self.sediment_reference_slope <= 0
                or self.sediment_discharge_exponent < 0
                or self.sediment_slope_exponent < 0):
            raise SurfaceMicrodomainError("HYDRO_CONFIG_OUT_OF_RANGE")
        step_count = self.duration_years * SECONDS_PER_YEAR / self.hydrology_dt_seconds
        if not math.isclose(step_count, round(step_count), rel_tol=0.0, abs_tol=1e-8):
            raise SurfaceMicrodomainError("HYDRO_DURATION_NOT_DIVISIBLE_BY_SUBSTEP")
        if self.precipitation_schedule_m_year_by_support is not None:
            if len(self.precipitation_schedule_m_year_by_support) != round(step_count):
                raise SurfaceMicrodomainError("HYDRO_PRECIPITATION_SCHEDULE_LENGTH_MISMATCH")
            if any(len(rates) != 2 or any(not math.isfinite(x) or x < 0 for x in rates)
                   for rates in self.precipitation_schedule_m_year_by_support):
                raise SurfaceMicrodomainError("HYDRO_PRECIPITATION_SCHEDULE_INVALID")
        if not math.isclose(self.surface_config.duration_years, self.duration_years,
                            rel_tol=0.0, abs_tol=1e-12):
            raise SurfaceMicrodomainError("HYDRO_SURFACE_DURATION_MISMATCH")
        for rates in (self.precipitation_m_year_by_support,
                      self.evapotranspiration_m_year_by_support,
                      self.infiltration_capacity_m_year_by_support):
            if len(rates) != 2 or any(not math.isfinite(x) or x < 0 for x in rates):
                raise SurfaceMicrodomainError("HYDRO_RATE_PAIR_INVALID")
        for stocks in (self.initial_water_storage_m3_by_support,
                       self.initial_suspended_sediment_kg_by_support):
            if len(stocks) != 2 or any(not math.isfinite(x) or x < 0 for x in stocks):
                raise SurfaceMicrodomainError("HYDRO_INITIAL_STOCK_PAIR_INVALID")
        if (any(x < 0 for x in self.initial_substrate_mass_kg_by_support)
                or any(x <= 0 for x in self.substrate_density_kg_m3_by_support)
                or self.substrate_critical_shear_pa < 0
                or self.substrate_detachment_kg_pa_s < 0
                or self.water_density_kg_m3 <= 0 or self.gravity_m_s2 <= 0
                or len(self.substrate_material_id_by_support) != 2
                or any(not x for x in self.substrate_material_id_by_support)):
            raise SurfaceMicrodomainError("HYDRO_SUBSTRATE_CONFIG_INVALID")
        for supplied in (self.initial_mobile_material_kg_by_support,
                         self.initial_suspended_material_kg_by_support):
            if supplied is not None and (len(supplied) != 2 or any(
                    not key or not math.isfinite(float(value)) or float(value) < 0
                    for row in supplied for key, value in row.items())):
                raise SurfaceMicrodomainError("HYDRO_MATERIAL_INVENTORY_INVALID")
        self.surface_config.validate()


def _manning_discharge_m3_s(depth_m: float, width_m: float,
                            slope: float, roughness_n: float) -> float:
    """SI Manning discharge for a rectangular section, Q=A R^(2/3) sqrt(S)/n."""
    if depth_m <= 0 or width_m <= 0 or slope <= 0:
        return 0.0
    area = depth_m * width_m
    hydraulic_radius = area / (width_m + 2.0 * depth_m)
    return area * hydraulic_radius ** (2.0 / 3.0) * math.sqrt(slope) / roughness_n


def _capacity_concentration(config: HydroConfig, discharge_m3_s: float,
                            slope: float) -> float:
    if discharge_m3_s <= 0 or slope <= 0:
        return 0.0
    return (config.sediment_capacity_reference_kg_m3
            * (discharge_m3_s / config.sediment_reference_discharge_m3_s)
            ** config.sediment_discharge_exponent
            * (slope / config.sediment_reference_slope)
            ** config.sediment_slope_exponent)


def _route_sediment(
    *, donor: dict[str, Any], receiver: dict[str, Any] | None,
    water_flux_m3: float, water_before_route_m3: float,
    discharge_m3_s: float, slope: float, config: HydroConfig,
) -> tuple[float, float, dict[str, float], dict[str, float]]:
    """Route a capacity-limited mixture while preserving material IDs."""
    if not config.sediment_transport_enabled or water_flux_m3 <= 0:
        return 0.0, 0.0, {}, {}
    fraction = min(1.0, water_flux_m3 / max(water_before_route_m3, 1e-300))
    advected_by_id = {key: value * fraction
                      for key, value in donor["suspended_material_mass_kg_by_id"].items()}
    suspended_advected = sum(advected_by_id.values())
    capacity_mass = _capacity_concentration(config, discharge_m3_s, slope) * water_flux_m3
    sediment_flux = min(capacity_mass,
                        suspended_advected + donor["mobile_cover_mass_kg"])
    advected_total = min(suspended_advected, sediment_flux)
    if suspended_advected > 0.0 and advected_total < suspended_advected:
        advected_by_id = {key: value * advected_total / suspended_advected
                          for key, value in advected_by_id.items()}
    erosion = max(0.0, sediment_flux - advected_total)
    erosion = min(erosion, donor["mobile_cover_mass_kg"])
    erosion_by_id: dict[str, float] = {}
    mobile_total = donor["mobile_cover_mass_kg"]
    if erosion and mobile_total:
        for key, value in donor["mobile_material_mass_kg_by_id"].items():
            amount = erosion * value / mobile_total
            erosion_by_id[key] = amount
            donor["mobile_material_mass_kg_by_id"][key] -= amount
    flux_by_id = dict(advected_by_id)
    for key, value in erosion_by_id.items():
        flux_by_id[key] = flux_by_id.get(key, 0.0) + value
    donor["suspended_material_mass_kg_by_id"] = {
        key: value - advected_by_id.get(key, 0.0)
        for key, value in donor["suspended_material_mass_kg_by_id"].items()
    }
    donor["suspended_material_mass_kg_by_id"] = {
        key: value for key, value in donor["suspended_material_mass_kg_by_id"].items()
        if value > 0.0
    }
    donor["mobile_cover_mass_kg"] -= erosion
    donor["suspended_sediment_kg"] = sum(donor["suspended_material_mass_kg_by_id"].values())
    donor["erosion_from_cover_kg"] += erosion
    if receiver is not None:
        for key, value in flux_by_id.items():
            receiver["suspended_material_mass_kg_by_id"][key] = (
                receiver["suspended_material_mass_kg_by_id"].get(key, 0.0) + value)
        receiver["suspended_sediment_kg"] = sum(receiver["suspended_material_mass_kg_by_id"].values())
        receiver["sediment_received_kg"] += sediment_flux
    else:
        donor["sediment_export_kg"] += sediment_flux
        for key, value in flux_by_id.items():
            donor["sediment_export_by_material_kg"][key] = (
                donor["sediment_export_by_material_kg"].get(key, 0.0) + value)
    return sediment_flux, erosion, flux_by_id, erosion_by_id


def run_hydrology_scenario(
    states_by_support: Mapping[str, Mapping[str, Any]],
    source_identity: Mapping[str, Any],
    *,
    config: HydroConfig = HydroConfig(),
) -> dict[str, Any]:
    """Run a two-cell water balance and optional mobile-cover coupling."""
    config.validate()
    if set(states_by_support) != set(SUPPORTS):
        raise SurfaceMicrodomainError("HYDRO_SUPPORT_SET_MISMATCH")
    geometry, center_distance_m, edge_length_m = _surface_grid_geometry(source_identity)
    base_result = run_surface_microdomain(
        states_by_support, source_identity, config=config.surface_config)
    bedrock = [float(cell["bedrock_elevation_m"]) for cell in base_result["cells"]]
    cells: list[dict[str, Any]] = []
    for i, base_cell in enumerate(base_result["cells"]):
        cells.append({
            "surface_cell_id": base_cell["surface_cell_id"],
            "support_id": SUPPORTS[i],
            "grid_row_col": list(geometry[SUPPORTS[i]][:2]),
            "surface_area_m2": geometry[SUPPORTS[i]][2],
            "subsurface_node_id": base_cell["subsurface_node_id"],
            "subsurface_role_id": base_cell["subsurface_role_id"],
            "subsurface_temperature_k": base_cell["subsurface_temperature_k"],
            "bedrock_elevation_m": bedrock[i],
            "surface_elevation_m": float(base_cell["surface_elevation_m"]),
            "mobile_cover_thickness_m": float(base_cell["cover_thickness_m"]),
            "mobile_cover_mass_kg": float(base_cell["cover_mass_kg"]),
            "suspended_sediment_kg": float(config.initial_suspended_sediment_kg_by_support[i]),
            "mobile_material_mass_kg_by_id": {},
            "suspended_material_mass_kg_by_id": {},
            "substrate_material_id": config.substrate_material_id_by_support[i],
            "substrate_material_composition": "UNKNOWN_NOT_INFERRED_FROM_REDUCEDSTATE_ROLE",
            "substrate_material_provenance": "SYNTHETIC_BULK_BENCHMARK",
            "substrate_mass_kg": float(config.initial_substrate_mass_kg_by_support[i]),
            "substrate_density_kg_m3": float(config.substrate_density_kg_m3_by_support[i]),
            "bedrock_erosion_kg": 0.0,
            "sediment_export_by_material_kg": {},
            "material_deposition_kg_by_id": {},
            "material_internal_transfer_kg_by_id": {},
            "water_storage_m3": float(config.initial_water_storage_m3_by_support[i]),
            "precipitation_m3": 0.0,
            "evapotranspiration_m3": 0.0,
            "infiltration_m3": 0.0,
            "erosion_from_cover_kg": 0.0,
            "sediment_received_kg": 0.0,
            "sediment_export_kg": 0.0,
        })

    for i, cell in enumerate(cells):
        mobile = (dict(config.initial_mobile_material_kg_by_support[i])
                  if config.initial_mobile_material_kg_by_support is not None else
                  {f"SYNTHETIC_INITIAL_COVER:{cell['support_id']}": cell["mobile_cover_mass_kg"]})
        suspended = (dict(config.initial_suspended_material_kg_by_support[i])
                     if config.initial_suspended_material_kg_by_support is not None else
                     ({f"UNCLASSIFIED_INITIAL_SUSPENSION:{cell['support_id']}": cell["suspended_sediment_kg"]}
                      if cell["suspended_sediment_kg"] else {}))
        if not math.isclose(sum(mobile.values()), cell["mobile_cover_mass_kg"], rel_tol=1e-12,
                            abs_tol=1e-6):
            raise SurfaceMicrodomainError("HYDRO_MOBILE_MATERIAL_TOTAL_MISMATCH")
        if not math.isclose(sum(suspended.values()), cell["suspended_sediment_kg"], rel_tol=1e-12,
                            abs_tol=1e-6):
            raise SurfaceMicrodomainError("HYDRO_SUSPENDED_MATERIAL_TOTAL_MISMATCH")
        cell["mobile_material_mass_kg_by_id"] = mobile
        cell["suspended_material_mass_kg_by_id"] = suspended
    initial_mobile_by_id = [dict(cell["mobile_material_mass_kg_by_id"]) for cell in cells]
    initial_suspended_by_id = [dict(cell["suspended_material_mass_kg_by_id"]) for cell in cells]
    material_catalog: dict[str, dict[str, str]] = {}
    for cell in cells:
        material_catalog[cell["substrate_material_id"]] = {
            "composition": cell["substrate_material_composition"],
            "provenance": cell["substrate_material_provenance"],
        }
        for material_id in (*cell["mobile_material_mass_kg_by_id"],
                            *cell["suspended_material_mass_kg_by_id"]):
            material_catalog.setdefault(material_id, {
                "composition": "UNKNOWN_NOT_INFERRED",
                "provenance": "IDENTIFIED_BY_INPUT_MATERIAL_ID_ONLY",
            })

    initial_water = sum(cell["water_storage_m3"] for cell in cells)
    initial_cover = sum(cell["mobile_cover_mass_kg"] for cell in cells)
    initial_suspended = sum(cell["suspended_sediment_kg"] for cell in cells)
    total_precip = total_et = total_infiltration = 0.0
    total_internal_water = total_outlet_water = 0.0
    total_internal_sediment = total_outlet_sediment = total_erosion = total_deposition = 0.0
    total_bedrock_erosion = 0.0
    total_bedrock_erosion_by_material: dict[str, float] = {}
    total_cover_erosion_by_material: dict[str, float] = {}
    total_internal_material: dict[str, float] = {}
    total_export_material: dict[str, float] = {}
    total_internal_by_route: dict[str, float] = {}
    total_export_by_cell: dict[str, dict[str, float]] = {}
    max_discharge = 0.0
    max_bed_shear = 0.0
    limiter_substeps = 0
    reverse_flow_substeps = 0
    year_summaries: list[dict[str, Any]] = []
    annual_steps = round(SECONDS_PER_YEAR / config.hydrology_dt_seconds)
    total_steps = round(config.duration_years * annual_steps)
    outlet_elevation = bedrock[1] - config.outlet_drop_below_bedrock_m

    for step_index in range(total_steps):
        dt_s = config.hydrology_dt_seconds
        dt_years = dt_s / SECONDS_PER_YEAR
        # Atmospheric and vertical water terms are applied per cell before
        # horizontal routing. ET and infiltration are sinks, recorded separately.
        for i, cell in enumerate(cells):
            area = cell["surface_area_m2"]
            precipitation_rates = (config.precipitation_schedule_m_year_by_support[step_index]
                                   if config.precipitation_schedule_m_year_by_support is not None
                                   else config.precipitation_m_year_by_support)
            rain = precipitation_rates[i] * area * dt_years
            et_potential = config.evapotranspiration_m_year_by_support[i] * area * dt_years
            infiltration_potential = config.infiltration_capacity_m_year_by_support[i] * area * dt_years
            cell["water_storage_m3"] += rain
            cell["precipitation_m3"] += rain
            total_precip += rain
            et = min(cell["water_storage_m3"], et_potential)
            cell["water_storage_m3"] -= et
            cell["evapotranspiration_m3"] += et
            total_et += et
            infiltration = min(cell["water_storage_m3"], infiltration_potential)
            cell["water_storage_m3"] -= infiltration
            cell["infiltration_m3"] += infiltration
            total_infiltration += infiltration
            cell["mobile_cover_thickness_m"] = cell["mobile_cover_mass_kg"] / (
                config.surface_config.sediment_density_kg_m3 * area)
            cell["surface_elevation_m"] = cell["bedrock_elevation_m"] + cell["mobile_cover_thickness_m"]

        water_before_route = [cell["water_storage_m3"] for cell in cells]
        head = [cells[i]["surface_elevation_m"]
                + water_before_route[i] / cells[i]["surface_area_m2"] for i in range(2)]
        gradient = (head[0] - head[1]) / center_distance_m
        internal: tuple[int, int, float, float, float] | None = None
        if gradient != 0.0:
            donor_i, receiver_i = (0, 1) if gradient > 0 else (1, 0)
            slope = abs(gradient)
            depth = water_before_route[donor_i] / cells[donor_i]["surface_area_m2"]
            discharge = _manning_discharge_m3_s(depth, edge_length_m, slope, config.manning_n)
            requested = discharge * dt_s
            limiter = min(requested, 0.25 * water_before_route[donor_i])
            if limiter < requested - 1e-9:
                limiter_substeps += 1
            if donor_i == 1:
                reverse_flow_substeps += 1
            internal = (donor_i, receiver_i, limiter, discharge, slope)
            max_discharge = max(max_discharge, discharge)

        outlet: tuple[int, float, float, float] | None = None
        if config.outlet_open:
            i = 1
            water_depth = water_before_route[i] / cells[i]["surface_area_m2"]
            outlet_head = cells[i]["surface_elevation_m"] + water_depth
            outlet_slope = max(0.0, (outlet_head - outlet_elevation) / config.outlet_distance_m)
            discharge = _manning_discharge_m3_s(
                water_depth, edge_length_m, outlet_slope, config.manning_n)
            requested = discharge * dt_s
            limited = min(requested, 0.25 * water_before_route[i])
            if limited < requested - 1e-9:
                limiter_substeps += 1
            outlet = (i, limited, discharge, outlet_slope)
            max_discharge = max(max_discharge, discharge)

        sediment_internal = sediment_outlet = erosion_step = bedrock_erosion_step = 0.0
        material_internal_step: dict[str, float] = {}
        material_export_step: dict[str, float] = {}
        bedrock_erosion_by_id_step: dict[str, float] = {}
        if internal is not None:
            donor_i, receiver_i, volume, discharge, slope = internal
            depth = water_before_route[donor_i] / cells[donor_i]["surface_area_m2"]
            hydraulic_radius = (depth * edge_length_m / (edge_length_m + 2.0 * depth)
                                if depth > 0 else 0.0)
            shear = config.water_density_kg_m3 * config.gravity_m_s2 * hydraulic_radius * slope
            max_bed_shear = max(max_bed_shear, shear)
            cells[donor_i]["water_storage_m3"] -= volume
            cells[receiver_i]["water_storage_m3"] += volume
            total_internal_water += volume
            if config.substrate_erosion_enabled and shear > config.substrate_critical_shear_pa:
                detached = min(cells[donor_i]["substrate_mass_kg"],
                               config.substrate_detachment_kg_pa_s
                               * (shear - config.substrate_critical_shear_pa) * dt_s)
                if detached > 0:
                    material_id = cells[donor_i]["substrate_material_id"]
                    cells[donor_i]["substrate_mass_kg"] -= detached
                    cells[donor_i]["bedrock_elevation_m"] -= detached / (
                        cells[donor_i]["substrate_density_kg_m3"] * cells[donor_i]["surface_area_m2"])
                    cells[donor_i]["mobile_cover_mass_kg"] += detached
                    cells[donor_i]["mobile_material_mass_kg_by_id"][material_id] = (
                        cells[donor_i]["mobile_material_mass_kg_by_id"].get(material_id, 0.0) + detached)
                    cells[donor_i]["bedrock_erosion_kg"] += detached
                    bedrock_erosion_step += detached
                    bedrock_erosion_by_id_step[material_id] = bedrock_erosion_by_id_step.get(material_id, 0.0) + detached
            sediment_flux, erosion, flux_material, cover_erosion_material = _route_sediment(
                donor=cells[donor_i], receiver=cells[receiver_i],
                water_flux_m3=volume, water_before_route_m3=water_before_route[donor_i],
                discharge_m3_s=discharge, slope=slope, config=config,
            )
            sediment_internal += sediment_flux
            erosion_step += erosion
            for material_id, amount in flux_material.items():
                material_internal_step[material_id] = material_internal_step.get(material_id, 0.0) + amount
                route = f"{cells[donor_i]['surface_cell_id']}->{cells[receiver_i]['surface_cell_id']}|{material_id}"
                total_internal_by_route[route] = total_internal_by_route.get(route, 0.0) + amount
                cells[donor_i]["material_internal_transfer_kg_by_id"][material_id] = (
                    cells[donor_i]["material_internal_transfer_kg_by_id"].get(material_id, 0.0) + amount)
            for material_id, amount in cover_erosion_material.items():
                total_cover_erosion_by_material[material_id] = (
                    total_cover_erosion_by_material.get(material_id, 0.0) + amount)
        if outlet is not None:
            donor_i, volume, discharge, slope = outlet
            cells[donor_i]["water_storage_m3"] -= volume
            total_outlet_water += volume
            depth = water_before_route[donor_i] / cells[donor_i]["surface_area_m2"]
            hydraulic_radius = (depth * edge_length_m / (edge_length_m + 2.0 * depth)
                                if depth > 0 else 0.0)
            shear = config.water_density_kg_m3 * config.gravity_m_s2 * hydraulic_radius * slope
            max_bed_shear = max(max_bed_shear, shear)
            if config.substrate_erosion_enabled and shear > config.substrate_critical_shear_pa:
                detached = min(cells[donor_i]["substrate_mass_kg"],
                               config.substrate_detachment_kg_pa_s
                               * (shear - config.substrate_critical_shear_pa) * dt_s)
                if detached > 0:
                    material_id = cells[donor_i]["substrate_material_id"]
                    cells[donor_i]["substrate_mass_kg"] -= detached
                    cells[donor_i]["bedrock_elevation_m"] -= detached / (
                        cells[donor_i]["substrate_density_kg_m3"] * cells[donor_i]["surface_area_m2"])
                    cells[donor_i]["mobile_cover_mass_kg"] += detached
                    cells[donor_i]["mobile_material_mass_kg_by_id"][material_id] = (
                        cells[donor_i]["mobile_material_mass_kg_by_id"].get(material_id, 0.0) + detached)
                    cells[donor_i]["bedrock_erosion_kg"] += detached
                    bedrock_erosion_step += detached
                    bedrock_erosion_by_id_step[material_id] = bedrock_erosion_by_id_step.get(material_id, 0.0) + detached
            sediment_flux, erosion, flux_material, cover_erosion_material = _route_sediment(
                donor=cells[donor_i], receiver=None,
                water_flux_m3=volume, water_before_route_m3=water_before_route[donor_i],
                discharge_m3_s=discharge, slope=slope, config=config,
            )
            sediment_outlet += sediment_flux
            erosion_step += erosion
            for material_id, amount in flux_material.items():
                material_export_step[material_id] = material_export_step.get(material_id, 0.0) + amount
                export_cell = cells[donor_i]["surface_cell_id"]
                export_map = total_export_by_cell.setdefault(export_cell, {})
                export_map[material_id] = export_map.get(material_id, 0.0) + amount
            for material_id, amount in cover_erosion_material.items():
                total_cover_erosion_by_material[material_id] = (
                    total_cover_erosion_by_material.get(material_id, 0.0) + amount)

        # Excess suspension settles to the mobile cover when local capacity
        # falls. Dry-cell suspension settles completely.
        for i, cell in enumerate(cells):
            if not config.sediment_transport_enabled:
                cell["mobile_cover_thickness_m"] = cell["mobile_cover_mass_kg"] / (
                    config.surface_config.sediment_density_kg_m3 * cell["surface_area_m2"])
                cell["surface_elevation_m"] = cell["bedrock_elevation_m"] + cell["mobile_cover_thickness_m"]
                continue
            flow_q = 0.0
            flow_slope = 0.0
            if internal is not None and internal[1] == i:
                flow_q, flow_slope = internal[3], internal[4]
            if outlet is not None and outlet[0] == i:
                flow_q = max(flow_q, outlet[2])
                flow_slope = max(flow_slope, outlet[3])
            capacity_stock = (_capacity_concentration(config, flow_q, flow_slope)
                              * cell["water_storage_m3"])
            deposition = max(0.0, cell["suspended_sediment_kg"] - capacity_stock)
            suspended_before = cell["suspended_sediment_kg"]
            if deposition > 0 and suspended_before > 0:
                for material_id, value in list(cell["suspended_material_mass_kg_by_id"].items()):
                    settled = deposition * value / suspended_before
                    cell["suspended_material_mass_kg_by_id"][material_id] -= settled
                    cell["mobile_material_mass_kg_by_id"][material_id] = (
                        cell["mobile_material_mass_kg_by_id"].get(material_id, 0.0) + settled)
                    cell["material_deposition_kg_by_id"][material_id] = (
                        cell["material_deposition_kg_by_id"].get(material_id, 0.0) + settled)
                cell["suspended_material_mass_kg_by_id"] = {
                    key: value for key, value in cell["suspended_material_mass_kg_by_id"].items()
                    if value > 0.0}
            cell["suspended_sediment_kg"] -= deposition
            cell["suspended_sediment_kg"] = sum(cell["suspended_material_mass_kg_by_id"].values())
            cell["mobile_cover_mass_kg"] += deposition
            cell["mobile_cover_thickness_m"] = cell["mobile_cover_mass_kg"] / (
                config.surface_config.sediment_density_kg_m3 * cell["surface_area_m2"])
            cell["surface_elevation_m"] = cell["bedrock_elevation_m"] + cell["mobile_cover_thickness_m"]
            total_deposition += deposition

        total_internal_sediment += sediment_internal
        total_outlet_sediment += sediment_outlet
        total_erosion += erosion_step
        total_bedrock_erosion += bedrock_erosion_step
        for key, amount in bedrock_erosion_by_id_step.items():
            total_bedrock_erosion_by_material[key] = total_bedrock_erosion_by_material.get(key, 0.0) + amount
        for key, amount in material_internal_step.items():
            total_internal_material[key] = total_internal_material.get(key, 0.0) + amount
        for key, amount in material_export_step.items():
            total_export_material[key] = total_export_material.get(key, 0.0) + amount

        if (step_index + 1) % annual_steps == 0:
            year = (step_index + 1) // annual_steps
            water_end = sum(cell["water_storage_m3"] for cell in cells)
            sediment_end = sum(cell["mobile_cover_mass_kg"]
                               + cell["suspended_sediment_kg"] for cell in cells)
            year_summaries.append({
                "year": year,
                "water_storage_m3_by_support": {cell["support_id"]: cell["water_storage_m3"] for cell in cells},
                "surface_elevation_m_by_support": {cell["support_id"]: cell["surface_elevation_m"] for cell in cells},
                "mobile_cover_mass_kg_by_support": {cell["support_id"]: cell["mobile_cover_mass_kg"] for cell in cells},
                "suspended_sediment_kg_by_support": {cell["support_id"]: cell["suspended_sediment_kg"] for cell in cells},
                "water_balance_residual_m3": (initial_water + total_precip - total_et
                    - total_infiltration - total_outlet_water - water_end),
                "sediment_balance_residual_kg": (initial_cover + initial_suspended
                    + total_bedrock_erosion - sediment_end - total_outlet_sediment),
            })

    final_water = sum(cell["water_storage_m3"] for cell in cells)
    final_cover = sum(cell["mobile_cover_mass_kg"] for cell in cells)
    final_suspended = sum(cell["suspended_sediment_kg"] for cell in cells)
    initial_material_by_id: dict[str, float] = {}
    final_material_by_id: dict[str, float] = {}
    for i, cell in enumerate(cells):
        for key, value in cell["mobile_material_mass_kg_by_id"].items():
            final_material_by_id[key] = final_material_by_id.get(key, 0.0) + value
        for key, value in cell["suspended_material_mass_kg_by_id"].items():
            final_material_by_id[key] = final_material_by_id.get(key, 0.0) + value
        material_id = cell["substrate_material_id"]
        final_material_by_id[material_id] = final_material_by_id.get(material_id, 0.0) + cell["substrate_mass_kg"]
        for key, value in initial_mobile_by_id[i].items():
            initial_material_by_id[key] = initial_material_by_id.get(key, 0.0) + value
        for key, value in initial_suspended_by_id[i].items():
            initial_material_by_id[key] = initial_material_by_id.get(key, 0.0) + value
        initial_substrate_id = config.substrate_material_id_by_support[i]
        initial_material_by_id[initial_substrate_id] = initial_material_by_id.get(initial_substrate_id, 0.0) + config.initial_substrate_mass_kg_by_support[i]
    material_export_by_id = dict(total_export_material)
    material_residuals = {key: initial_material_by_id.get(key, 0.0)
                          - final_material_by_id.get(key, 0.0)
                          - material_export_by_id.get(key, 0.0)
                          for key in sorted(set(initial_material_by_id) | set(final_material_by_id)
                                            | set(material_export_by_id))}
    for key, residual in material_residuals.items():
        scale = max(initial_material_by_id.get(key, 0.0), 1.0)
        if abs(residual) > max(1e-6, 256.0 * math.ulp(scale)):
            raise SurfaceMicrodomainError(f"HYDRO_MATERIAL_IDENTITY_BUDGET_FAILED:{key}:{residual}")
    water_residual = (initial_water + total_precip - total_et - total_infiltration
                      - total_outlet_water - final_water)
    sediment_residual = (initial_cover + initial_suspended + total_bedrock_erosion - final_cover
                         - final_suspended - total_outlet_sediment)
    substrate_initial = sum(config.initial_substrate_mass_kg_by_support)
    substrate_final = sum(cell["substrate_mass_kg"] for cell in cells)
    substrate_residual = substrate_initial - substrate_final - total_bedrock_erosion
    # The ledgers sum very large cell volumes/masses. Bound roundoff in ULPs of
    # the accumulated source totals rather than using a fixed engineering
    # tolerance or a relative threshold that scales with the whole stock.
    water_roundoff_tolerance = max(1e-6, 4096.0 * math.ulp(max(total_precip, 1.0)))
    sediment_roundoff_tolerance = max(
        1e-6, 256.0 * math.ulp(max(initial_cover + initial_suspended, 1.0))
    )
    if abs(water_residual) > water_roundoff_tolerance:
        raise SurfaceMicrodomainError(
            f"HYDRO_WATER_BUDGET_FAILED:{water_residual}:{water_roundoff_tolerance}"
        )
    if abs(sediment_residual) > sediment_roundoff_tolerance:
        raise SurfaceMicrodomainError(f"HYDRO_SEDIMENT_BUDGET_FAILED:{sediment_residual}")
    substrate_roundoff_tolerance = max(1e-6, 256.0 * math.ulp(max(substrate_initial, 1.0)))
    if abs(substrate_residual) > substrate_roundoff_tolerance:
        raise SurfaceMicrodomainError(f"HYDRO_SUBSTRATE_BUDGET_FAILED:{substrate_residual}")
    if any(cell["water_storage_m3"] < -1e-8 or cell["mobile_cover_mass_kg"] < -1e-8
           or cell["suspended_sediment_kg"] < -1e-8 for cell in cells):
        raise SurfaceMicrodomainError("HYDRO_OR_SEDIMENT_NEGATIVE_STATE")

    surface_volume_initial = sum(float(config.surface_config.initial_relief_m[i]
                                       + config.surface_config.initial_cover_m[i])
                                 * cells[i]["surface_area_m2"] for i in range(2))
    surface_volume_final = sum(cell["surface_elevation_m"] * cell["surface_area_m2"] for cell in cells)
    uplift_volume = sum(config.surface_config.prescribed_uplift_m[i]
                        * cells[i]["surface_area_m2"] for i in range(2))
    rho = config.surface_config.sediment_density_kg_m3
    substrate_bulk_expansion = sum(
        total_bedrock_erosion_by_material.get(material_id, 0.0)
        * (1.0 / rho - 1.0 / config.substrate_density_kg_m3_by_support[i])
        for i, material_id in enumerate(config.substrate_material_id_by_support))
    geom_residual = (surface_volume_final - surface_volume_initial - uplift_volume
                     + (total_outlet_sediment + final_suspended - initial_suspended) / rho
                     - substrate_bulk_expansion)
    geometry_roundoff_tolerance = max(1e-6, 256.0 * math.ulp(max(surface_volume_initial, 1.0)))
    if abs(geom_residual) > geometry_roundoff_tolerance:
        raise SurfaceMicrodomainError("HYDRO_SURFACE_GEOMETRY_BUDGET_FAILED")
    return {
        "scenario_id": "OUTLET_OPEN" if config.outlet_open else "OUTLET_CLOSED",
        "configuration": {
            "duration_years": config.duration_years,
            "hydrology_dt_seconds": config.hydrology_dt_seconds,
            "hydrology_substeps": total_steps,
            "precipitation_m_year_by_support": dict(zip(SUPPORTS, config.precipitation_m_year_by_support)),
            "initial_water_storage_m3_by_support": dict(zip(SUPPORTS, config.initial_water_storage_m3_by_support)),
            "initial_suspended_sediment_kg_by_support": dict(zip(
                SUPPORTS, config.initial_suspended_sediment_kg_by_support)),
            "initial_substrate_mass_kg_by_support": dict(zip(SUPPORTS, config.initial_substrate_mass_kg_by_support)),
            "substrate_material_id_by_support": dict(zip(SUPPORTS, config.substrate_material_id_by_support)),
            "substrate_density_kg_m3_by_support": dict(zip(SUPPORTS, config.substrate_density_kg_m3_by_support)),
            "substrate_to_mobile_bulk_volume_closure": "MASS_PRESERVED; DENSITY_DIFFERENCE_CHANGES_BULK_VOLUME_AS_PACKING_DIAGNOSTIC; NOT_A_WEATHERING_OR_LITHIFICATION_LAW",
            "substrate_erosion_enabled": config.substrate_erosion_enabled,
            "substrate_erosion_law": ("m_dot=k_d*max(tau_b-tau_c,0); tau_b=rho_w*g*R_h*S"
                                      if config.substrate_erosion_enabled else "DISABLED"),
            "substrate_critical_shear_pa": config.substrate_critical_shear_pa,
            "substrate_detachment_kg_pa_s": config.substrate_detachment_kg_pa_s,
            "precipitation_schedule_m_year_by_support": (
                [dict(zip(SUPPORTS, rates)) for rates in config.precipitation_schedule_m_year_by_support]
                if config.precipitation_schedule_m_year_by_support is not None else None
            ),
            "evapotranspiration_m_year_by_support": dict(zip(SUPPORTS, config.evapotranspiration_m_year_by_support)),
            "infiltration_capacity_m_year_by_support": dict(zip(SUPPORTS, config.infiltration_capacity_m_year_by_support)),
            "manning_n": config.manning_n,
            "outlet_open": config.outlet_open,
            "outlet_distance_m": config.outlet_distance_m,
            "outlet_drop_below_bedrock_m": config.outlet_drop_below_bedrock_m,
            "sediment_transport_enabled": config.sediment_transport_enabled,
            "sediment_capacity_law": "Ccap=C0*(Q/Q0)^a*(S/S0)^b",
            "sediment_capacity_reference_kg_m3": config.sediment_capacity_reference_kg_m3,
            "sediment_reference_discharge_m3_s": config.sediment_reference_discharge_m3_s,
            "sediment_reference_slope": config.sediment_reference_slope,
            "sediment_discharge_exponent": config.sediment_discharge_exponent,
            "sediment_slope_exponent": config.sediment_slope_exponent,
            "positive_flow_fraction_cap_per_substep": 0.25,
            "surface_diffusion_in_this_run": False,
            "uplift_is_prescribed_not_inferred_from_horizontal_strain": True,
            "hydraulic_interface_status": "EXPLICIT_SYNTHETICALLY_CONNECTED_FOR_THIS_EXPERIMENT",
        },
        "source_identity": dict(source_identity),
        "source_material_link": [{
            "support_id": cell["support_id"],
            "subsurface_node_id": cell["subsurface_node_id"],
            "role_id": cell["subsurface_role_id"],
            "temperature_k": cell["subsurface_temperature_k"],
            "role_is_lithology": False,
        } for cell in cells],
        "material_catalog_by_id": material_catalog,
        "water_balance": {
            "initial_storage_m3": initial_water,
            "precipitation_input_m3": total_precip,
            "evapotranspiration_sink_m3": total_et,
            "infiltration_sink_m3": total_infiltration,
            "internal_transfer_m3": total_internal_water,
            "outlet_export_m3": total_outlet_water,
            "final_storage_m3": final_water,
            "residual_m3": water_residual,
            "roundoff_tolerance_m3": water_roundoff_tolerance,
        },
        "sediment_balance": {
            "initial_mobile_cover_kg": initial_cover,
            "initial_suspended_kg": initial_suspended,
            "initial_total_sediment_kg": initial_cover + initial_suspended,
            "erosion_from_cover_kg": total_erosion,
            "internal_suspended_transfer_kg": total_internal_sediment,
            "deposition_to_cover_kg": total_deposition,
            "outlet_sediment_export_kg": total_outlet_sediment,
            "final_mobile_cover_kg": final_cover,
            "final_suspended_kg": final_suspended,
            "residual_kg": sediment_residual,
            "roundoff_tolerance_kg": sediment_roundoff_tolerance,
            "bedrock_erosion_kg": total_bedrock_erosion,
            "bedrock_erosion_kg_by_material_id": total_bedrock_erosion_by_material,
            "erosion_from_mobile_by_material_id": total_cover_erosion_by_material,
            "initial_substrate_mass_kg": substrate_initial,
            "final_substrate_mass_kg": substrate_final,
            "substrate_residual_kg": substrate_residual,
            "substrate_roundoff_tolerance_kg": substrate_roundoff_tolerance,
            "mobile_material_mass_kg_by_id": {
                key: sum(cell["mobile_material_mass_kg_by_id"].get(key, 0.0) for cell in cells)
                for key in sorted({k for cell in cells for k in cell["mobile_material_mass_kg_by_id"]})},
            "suspended_material_mass_kg_by_id": {
                key: sum(cell["suspended_material_mass_kg_by_id"].get(key, 0.0) for cell in cells)
                for key in sorted({k for cell in cells for k in cell["suspended_material_mass_kg_by_id"]})},
            "internal_transfer_kg_by_material_id": total_internal_material,
            "internal_transport_kg_by_route_and_material": total_internal_by_route,
            "deposition_kg_by_material_id": {
                key: sum(cell["material_deposition_kg_by_id"].get(key, 0.0) for cell in cells)
                for key in sorted({k for cell in cells for k in cell["material_deposition_kg_by_id"]})},
            "outlet_export_kg_by_material_id": total_export_material,
            "outlet_export_kg_by_surface_cell_and_material": total_export_by_cell,
            "deposition_kg_by_surface_cell_and_material": {
                cell["surface_cell_id"]: dict(cell["material_deposition_kg_by_id"]) for cell in cells},
            "material_mass_balance_residual_kg_by_id": material_residuals,
            "material_initial_mass_kg_by_id": initial_material_by_id,
            "material_final_mass_kg_by_id": final_material_by_id,
        },
        "geometry_balance": {
            "initial_surface_volume_m3": surface_volume_initial,
            "final_surface_volume_m3": surface_volume_final,
            "prescribed_uplift_volume_m3": uplift_volume,
            "sediment_export_volume_m3": total_outlet_sediment / rho,
            "suspended_volume_equivalent_m3": final_suspended / rho,
            "initial_suspended_volume_equivalent_m3": initial_suspended / rho,
            "substrate_bulk_expansion_volume_m3": substrate_bulk_expansion,
            "residual_m3": geom_residual,
            "roundoff_tolerance_m3": geometry_roundoff_tolerance,
        },
        "hydraulic_diagnostics": {
            "maximum_discharge_m3_s": max_discharge,
            "maximum_bed_shear_stress_pa": max_bed_shear,
            "flow_limiter_substeps": limiter_substeps,
            "reverse_internal_flow_substeps": reverse_flow_substeps,
            "internal_water_transfer_m3": total_internal_water,
            "outlet_water_export_m3": total_outlet_water,
        },
        "cells": cells,
        "annual_states": year_summaries,
        "authority_limits": [
            "Precipitation, ET, infiltration, Manning roughness, outlet, and sediment-capacity parameters are synthetic.",
            "Manning flow is a reduced rectangular-channel approximation, not a validated catchment model.",
            "Sediment capacity is an empirical sensitivity law; no grain-size or bedload partition is represented.",
            "B5 adjacency provides T0 geometry only; hydraulic connectivity is an explicit experiment choice.",
            "T0 surface elevation payload is not bound; the surface relief and cover remain prescribed synthetic fields.",
            "Bedrock detachment is disabled by default; enabled results use an explicit synthetic threshold law, not calibrated geology.",
            "Chemical weathering and lithification are not modeled.",
            "No temperature, mechanical, or Deep feedback is modeled.",
        ],
    }


def run_experiment_suite(states_by_support: Mapping[str, Mapping[str, Any]],
                         source_identity: Mapping[str, Any]) -> dict[str, Any]:
    """Run required contrasts, a storm-recession deposition case, and diffusion reference."""
    common = dict(duration_years=3.0, hydrology_dt_seconds=3600.0,
                  precipitation_m_year_by_support=(0.40, 0.20),
                  evapotranspiration_m_year_by_support=(0.08, 0.08),
                  infiltration_capacity_m_year_by_support=(0.12, 0.12),
                  sediment_transport_enabled=True)
    scenarios = {
        "NO_PRECIPITATION": HydroConfig(
            **{**common, "precipitation_m_year_by_support": (0.0, 0.0), "outlet_open": False}),
        "PRECIPITATION_OUTLET_CLOSED": HydroConfig(**{**common, "outlet_open": False}),
        "PRECIPITATION_OUTLET_OPEN_NO_SEDIMENT": HydroConfig(
            **{**common, "outlet_open": True, "sediment_transport_enabled": False}),
        "PRECIPITATION_OUTLET_OPEN_WITH_SEDIMENT": HydroConfig(
            **{**common, "outlet_open": True, "sediment_transport_enabled": True}),
    }
    storm_duration = 24.0 * 3600.0 / SECONDS_PER_YEAR
    storm_surface = SurfaceConfig(
        duration_years=storm_duration, dt_years=storm_duration,
        enable_surface_transport=False,
    )
    scenarios["STORM_THEN_DRY_DEPOSITION"] = HydroConfig(
        duration_years=storm_duration,
        hydrology_dt_seconds=3600.0,
        precipitation_m_year_by_support=(0.0, 0.0),
        precipitation_schedule_m_year_by_support=tuple(
            (0.8, 0.4) if step < 6 else (0.0, 0.0) for step in range(24)
        ),
        evapotranspiration_m_year_by_support=(0.08, 0.08),
        infiltration_capacity_m_year_by_support=(0.12, 0.12),
        outlet_open=False,
        sediment_transport_enabled=True,
        surface_config=storm_surface,
    )
    outputs = {name: run_hydrology_scenario(states_by_support, source_identity, config=cfg)
               for name, cfg in scenarios.items()}
    diffusion_reference = run_surface_microdomain(
        states_by_support, source_identity,
        config=SurfaceConfig(duration_years=3.0, dt_years=1.0,
                             enable_surface_transport=True))
    return {
        "schema": "ARCANA_R6_COUPLED_HYDROLOGY_SURFACE_MICRODOMAIN_V1",
        "scope": "NONCANONICAL_SYNTHETIC_WATER_SEDIMENT_SURFACE_EXPERIMENT",
        "source_identity": dict(source_identity),
        "hydrology_scenarios": outputs,
        "separate_surface_diffusion_reference": diffusion_reference,
        "comparison_scope": {
            "diffusion_and_hydrologic_sediment_transport_are_run_separately": True,
            "no_double_counting": True,
            "deep_and_thermal_mechanical_states_unchanged": True,
        },
    }
