"""Non-canonical, query-driven regional materialization of R6 t0 geometry.

With a bound latent state, land/coast geometry and terrain receive deterministic
procedural sub-grid structure. Province/plate/crust classes retain 1-degree
parent support; no field is promoted to observational authority by resolution.
"""

from __future__ import annotations

from hashlib import sha256
import json
from dataclasses import dataclass
from math import pi
from time import perf_counter
from typing import Any

import numpy as np

from .grid import GlobalGrid1Degree
from .model import InitialWorldFields
from .seeds import SEED_ROOT_MATERIAL, derive_seed_streams
from .latent import (R6InitialGeometryLatentState, materialize_latent_land_region,
                     materialize_latent_topography_region)


REFINEMENT_PARAMETER_IDENTITY: dict[str, Any] = {
    "generator": "ARCANA_R6_SUPERCONTINENT_GENERATOR_V1",
    "geometry": {
        "main_component_axes_deg": [108.0, 52.0],
        "main_center_latitude_range_deg": [-5.0, 5.0],
        "main_center_longitude_range_deg": [-180.0, 180.0],
        "main_orientation_range_radians": [-0.20, 0.20],
        "main_component_harmonic_amplitude": 0.14,
        "main_component_target_surface_fraction": 0.27,
        "coastline_harmonic_terms": 8,
        "coastline_longitude_waves": [1, 6],
        "coastline_latitude_waves": [1, 4],
        "secondary_terrane_count": 4,
        "secondary_terrane_layout": "seed-relative offsets plus fixed polar anchors",
        "secondary_terrane_distance_scale_km": 1100.0,
        "secondary_terrane_perturbation_amplitude": 0.035,
        "secondary_terrane_perturbation_waves_lon_lat": [3, 2],
        "secondary_terrane_target_surface_fraction": 0.0075,
    },
    "provinces": {
        "plate_count_range_inclusive": [12, 18],
        "craton_count_range_inclusive": [4, 8],
        "craton_minimum_separation_km": 1400.0,
        "craton_radius_km": 950.0,
        "orogenic_design_waves_lon_lat": [3, 2],
        "orogenic_design_suture_quantile": 0.55,
    },
    "topography": {
        "macro_harmonic_terms": 14,
        "macro_longitude_waves": [1, 7],
        "macro_latitude_waves": [1, 5],
        "meso_harmonic_terms": 12,
        "meso_longitude_waves": [1, 16],
        "meso_latitude_waves": [1, 10],
        "base_m": 900.0,
        "macro_amplitude_m": 520.0,
        "meso_amplitude_m": 170.0,
        "orogenic_design_offset_m": 1500.0,
        "clip_m": [25.0, 8000.0],
        "normalization_grid": "R6_GLOBAL_GEOGRAPHY_1DEG_V1",
    },
}


def _parameter_identity() -> dict[str, Any]:
    encoded = json.dumps(REFINEMENT_PARAMETER_IDENTITY, sort_keys=True,
                         separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {"id": "ARCANA_R6_SUPERCONTINENT_GENERATOR_V1_PARAMETERS_V1",
            "sha256": sha256(encoded).hexdigest(),
            "values": REFINEMENT_PARAMETER_IDENTITY}


@dataclass(frozen=True, slots=True)
class Region:
    """Non-wrapping geographic cell-edge bounds in degrees."""

    south_deg: float
    west_deg: float
    north_deg: float
    east_deg: float


def _harmonic_terms(rng: np.random.Generator, terms: int,
                    max_lon_wave: int, max_lat_wave: int
                    ) -> tuple[tuple[int, int, float, float, float], ...]:
    result = []
    for _ in range(terms):
        m = int(rng.integers(1, max_lon_wave + 1))
        n = int(rng.integers(1, max_lat_wave + 1))
        phase_lon, phase_lat = rng.uniform(0, 2 * np.pi, size=2)
        sign = -1.0 if rng.integers(0, 2) else 1.0
        result.append((m, n, float(phase_lon), float(phase_lat), sign))
    return tuple(result)


def _coordinates(region: Region, resolution_deg: float) -> tuple[np.ndarray, np.ndarray]:
    vals = (region.south_deg, region.west_deg, region.north_deg, region.east_deg,
            resolution_deg)
    if not all(np.isfinite(v) for v in vals):
        raise ValueError("region and resolution must be finite")
    if resolution_deg <= 0 or region.south_deg < -90 or region.north_deg > 90:
        raise ValueError("invalid region or resolution")
    if not (-180 <= region.west_deg < region.east_deg <= 180 and
            region.south_deg < region.north_deg):
        raise ValueError("region bounds must be ordered and non-wrapping")
    ny = (region.north_deg - region.south_deg) / resolution_deg
    nx = (region.east_deg - region.west_deg) / resolution_deg
    if (not np.isclose(ny, round(ny), atol=1e-10) or
            not np.isclose(nx, round(nx), atol=1e-10)):
        raise ValueError("resolution must divide both region extents exactly")
    # Parent-cell alignment ensures unambiguous categorical support inheritance.
    edges = (region.south_deg + 90, region.north_deg + 90,
             region.west_deg + 180, region.east_deg + 180)
    if any(not np.isclose(v, round(v), atol=1e-10) for v in edges):
        raise ValueError("region bounds must align to 1-degree parent cell edges")
    lat = region.south_deg + (np.arange(round(ny)) + 0.5) * resolution_deg
    lon = region.west_deg + (np.arange(round(nx)) + 0.5) * resolution_deg
    return lat.astype(np.float64), lon.astype(np.float64)


def _parent_indices(lat: np.ndarray, lon: np.ndarray
                    ) -> tuple[np.ndarray, np.ndarray]:
    # At 1 degree this is exact parent identity; at finer resolutions this is
    # coarse-support inheritance, never a claim of refined categorical detail.
    rows = np.floor((lat + 90.0)[:, None] - 1e-12).astype(np.int64)
    cols = np.floor((lon + 180.0)[None, :] - 1e-12).astype(np.int64)
    rows = np.clip(rows, 0, 179)
    cols = np.clip(cols, 0, 359)
    return np.broadcast_arrays(rows, cols)


def _terrain_process(parent: InitialWorldFields, lat: np.ndarray, lon: np.ndarray,
                     land: np.ndarray, province: np.ndarray) -> np.ndarray:
    streams = {s.name: s.rng() for s in derive_seed_streams(
        root_material=SEED_ROOT_MATERIAL)}
    rng = streams["land_relief"]
    macro_terms = _harmonic_terms(rng, 14, 7, 5)
    meso_terms = _harmonic_terms(rng, 12, 16, 10)
    # Preserve the normalization used by the canonical 180x360 realization.
    base_lat = parent.grid.lat_centers_deg
    base_lon = parent.grid.lon_centers_deg
    # Recompute the canonical-grid normalization from the seeded process, not
    # from a region-sized window, so independently requested tiles agree.
    def raw(latitudes: np.ndarray, longitudes: np.ndarray,
            terms: tuple[tuple[int, int, float, float, float], ...]) -> np.ndarray:
        latr = np.deg2rad(latitudes)[:, None]
        lonr = np.deg2rad(longitudes)[None, :]
        value = np.zeros((len(latitudes), len(longitudes)), dtype=np.float64)
        for m, n, phase_lon, phase_lat, sign in terms:
            value += sign * np.sin(m * lonr + phase_lon) * np.cos(n * latr + phase_lat)
        return value

    macro_sd = float(raw(base_lat, base_lon, macro_terms).std())
    meso_sd = float(raw(base_lat, base_lon, meso_terms).std())
    if not np.isfinite(macro_sd + meso_sd) or min(macro_sd, meso_sd) <= 0:
        raise ValueError("canonical terrain normalization is invalid")
    macro = raw(lat, lon, macro_terms) / macro_sd
    meso = raw(lat, lon, meso_terms) / meso_sd
    elevation = 900.0 + 520.0 * macro + 170.0 * meso
    elevation += np.where(province == 3, 1500.0, 0.0)
    elevation = np.clip(elevation, 25.0, 8000.0).astype(np.float32)
    elevation[~land] = np.nan
    return elevation


def materialize_region(parent: InitialWorldFields, region: Region,
                       resolution_deg: float, *, parent_history_id: str,
                       parent_state_id: str,
                       latent_state: R6InitialGeometryLatentState | None = None,
                       requested_fields: tuple[str, ...] = (
                           "land_ocean_mask", "coastline_mask", "plate_id", "crust_class",
                           "boundary_class", "province_class", "land_surface_elevation_m"),
                       refinement_reason: str = "NON_CANONICAL_REGENERABILITY_DIAGNOSTIC"
                       ) -> dict[str, Any]:
    """Create a bounded derived branch; never mutates/promotes the parent.

    Land/ocean and province values are inherited with coarse parent support.
    Terrain is evaluated from the seed-derived global harmonic process at the
    requested cell centers (not sampled/interpolated from the parent raster).
    """
    if parent.time_ma != 210.0 or parent.metadata.get("canonical_seed") is not True:
        raise ValueError("refinement requires the canonical 210 Ma seed lineage")
    allowed = {"land_ocean_mask", "coastline_mask", "plate_id", "crust_class",
               "boundary_class", "province_class", "land_surface_elevation_m",
               "bathymetry", "plate_motion", "deep", "climate", "hydrology"}
    if not requested_fields or not set(requested_fields) <= allowed:
        raise ValueError("requested fields must be a non-empty subset of known R6 fields")
    start = perf_counter()
    lat, lon = _coordinates(region, resolution_deg)
    if latent_state is not None and resolution_deg > 1.0:
        raise ValueError("refinement resolution must be 1 degree or finer")
    if latent_state is not None and (
            latent_state.parent_history_id != parent_history_id or
            latent_state.parent_state_id != parent_state_id):
        raise ValueError("latent state parent linkage differs from the refinement request")
    rows, cols = _parent_indices(lat, lon)
    indices = (rows, cols)
    latent_land_audit: dict[str, Any] | None = None
    latent_topography_audit: dict[str, Any] | None = None
    if latent_state is not None:
        fine_land, fine_coast, latent_land_audit = materialize_latent_land_region(
            parent, latent_state, lat, lon, resolution_deg)
    else:
        fine_land = parent.land_ocean_mask[indices].astype(bool)
        fine_coast = parent.coastline_mask[indices].astype(bool)
    parent_fields = {
        "land_ocean_mask": fine_land.astype(np.uint8),
        "coastline_mask": fine_coast.astype(np.uint8),
        "plate_id": parent.plate_id[indices].copy(),
        "crust_class": parent.crust_class[indices].copy(),
        "boundary_class": parent.boundary_class[indices].copy(),
        "province_class": parent.province_class[indices].copy(),
        "land_surface_elevation_m": None,
    }
    land = fine_land
    province = parent_fields["province_class"]
    if "land_surface_elevation_m" in requested_fields:
        if latent_state is not None:
            parent_fields["land_surface_elevation_m"], latent_topography_audit = (
                materialize_latent_topography_region(
                    parent, latent_state, lat, lon, land, resolution_deg))
        else:
            parent_fields["land_surface_elevation_m"] = _terrain_process(
                parent, lat, lon, land, province)
    unknown = {
        "bathymetry": np.broadcast_to(~land, land.shape).copy(),
        "plate_motion": np.ones(land.shape, dtype=bool),
        "deep": np.ones(land.shape, dtype=bool),
        "climate": np.ones(land.shape, dtype=bool),
        "hydrology": np.ones(land.shape, dtype=bool),
    }
    selected = {name: parent_fields[name] for name in requested_fields
                if name in parent_fields}
    if {"land_ocean_mask", "land_surface_elevation_m"} & set(requested_fields):
        selected["elevation_support_mask"] = land.copy()
    selected.update({f"{name}_unknown_mask": unknown[name]
                    for name in requested_fields if name in unknown})
    elapsed = perf_counter() - start
    descriptor = {
        "schema": "R6_DERIVED_REFINEMENT_DESCRIPTOR_V1",
        "classification": "DERIVED_REFINEMENT_BRANCH",
        "parent_history_id": parent_history_id,
        "parent_state_id": parent_state_id,
        "parent_world_id": latent_state.world_id if latent_state is not None else None,
        "parent_time_ma": parent.time_ma,
        "region_cell_edge_bounds_deg": {
            "south": region.south_deg, "west": region.west_deg,
            "north": region.north_deg, "east": region.east_deg,
        },
        "target_resolution_deg": resolution_deg,
        "shape_lat_lon": [len(lat), len(lon)],
        "requested_fields": list(requested_fields),
        "generator_id": parent.metadata["generator_id"],
        "generator_version": parent.metadata["generator_version"],
        "parameter_identity": _parameter_identity(),
        "latent_geometry_sha256": latent_state.sha256 if latent_state is not None else None,
        "latent_geometry_schema": latent_state.schema if latent_state is not None else None,
        "seed_lineage": {
            "strategy_id": "ARCANA_R6_INITIAL_WORLD_SEED_LINEAGE_V1",
            "root_digest_sha256": parent.metadata["seed_root_sha256"],
            "global_process": "NAMED_SEMANTIC_HARMONIC_STREAMS",
            "hierarchical_process": "SHA256_KEYED_BY_ROOT_WORLD_COMPONENT_PARENT_CELL_AND_SCALE__PCG64_FIRST_128_BITS",
        },
        "boundary_condition_source": "CANONICAL_LATENT_GEOMETRY_AND_PARENT_CELL_CONSTRAINTS; analytic fields globally anchored; regional topology uses a one-parent-cell halo",
        "support_authority_inherited": "AUTHORIAL_SYNTHETIC_INITIALIZATION; land/coast are structurally refined while geological classes retain 1-degree parent support",
        "provenance": {
            "canonical_world_id": latent_state.world_id if latent_state is not None else None,
            "canonical_history_id": parent_history_id,
            "canonical_state_id": parent_state_id,
            "canonical_parent_payload_sha256": (
                latent_state.parent_payload_sha256 if latent_state is not None else None),
            "latent_geometry_sha256": latent_state.sha256 if latent_state is not None else None,
            "generator_parameter_identity_sha256": _parameter_identity()["sha256"],
            "refinement_branch_only": True,
        },
        "field_resolution_classes": {
            "land_ocean_mask": "STRUCTURALLY_REFINABLE" if latent_state is not None else "COARSE_ONLY",
            "coastline_mask": "STRUCTURALLY_REFINABLE" if latent_state is not None else "COARSE_ONLY",
            "plate_id": "COARSE_SUPPORT_ON_FINE_GRID",
            "crust_class": "COARSE_SUPPORT_ON_FINE_GRID",
            "boundary_class": "COARSE_SUPPORT_ON_FINE_GRID",
            "province_class": "COARSE_SUPPORT_ON_FINE_GRID",
            "land_surface_elevation_m": (
                "MULTISCALE_REFINABLE" if latent_topography_audit and
                latent_topography_audit.get("fine_spectrum_added") else
                "STRUCTURALLY_REFINABLE" if latent_state is not None else
                "COARSE_ONLY"),
            "unknown_domains": "UNKNOWN_PRESERVED",
        },
        "validation": {"land_geometry": latent_land_audit,
                       "topography": latent_topography_audit},
        "refinement_reason": refinement_reason,
        "promotion": "NONE__NON_CANONICAL_DIAGNOSTIC_BRANCH",
        "forward_simulation": False,
    }
    return {
        "descriptor": descriptor,
        "latitude_centers_deg": lat,
        "longitude_centers_deg": lon,
        "fields": selected,
        "elapsed_seconds": elapsed,
        "cell_count": int(len(lat) * len(lon)),
    }
