"""Deterministic Pangaea-inspired ARCANA geography generator at 210 Ma."""

from __future__ import annotations

from hashlib import sha256
from math import pi

import numpy as np

from .grid import GlobalGrid1Degree
from .model import InitialWorldFields
from .seeds import SEED_ROOT_MATERIAL, derive_seed_streams
from .topography import generate_land_elevation


def _wrap_degrees(values: np.ndarray) -> np.ndarray:
    return (values + 180.0) % 360.0 - 180.0


def _area_threshold(score: np.ndarray, area: np.ndarray, target_fraction: float,
                     eligible: np.ndarray | None = None) -> np.ndarray:
    mask = np.zeros(score.shape, dtype=bool)
    valid = np.ones(score.shape, dtype=bool) if eligible is None else eligible
    indices = np.flatnonzero(valid)
    order = np.argsort(-score.ravel()[indices], kind="stable")
    ordered = indices[order]
    cumulative = np.cumsum(area.ravel()[ordered], dtype=np.float64)
    target = target_fraction * float(area.sum())
    count = int(np.searchsorted(cumulative, target, side="left")) + 1
    mask.ravel()[ordered[:count]] = True
    return mask


def _harmonic_boundary(grid: GlobalGrid1Degree, rng: np.random.Generator,
                       terms: int = 8) -> np.ndarray:
    lat = np.deg2rad(grid.lat_centers_deg)[:, None]
    lon = np.deg2rad(grid.lon_centers_deg)[None, :]
    out = np.zeros(grid.shape, dtype=np.float64)
    for _ in range(terms):
        m = int(rng.integers(1, 7))
        n = int(rng.integers(1, 5))
        p, q = rng.uniform(0, 2 * pi, size=2)
        trig = np.sin(m * lon + p) * np.cos(n * lat + q)
        if rng.integers(0, 2):
            trig += 0.5 * np.cos((m + 1) * lon - p) * np.sin((n + 1) * lat + q)
        out += trig
    sd = float(out.std())
    if sd == 0 or not np.isfinite(sd):
        raise ValueError("coastline harmonic field is degenerate")
    return out / sd


def _connected_components(mask: np.ndarray, grid: GlobalGrid1Degree) -> list[list[tuple[int, int]]]:
    seen = np.zeros(mask.shape, dtype=bool)
    components: list[list[tuple[int, int]]] = []
    for row, col in zip(*np.nonzero(mask)):
        if seen[row, col]:
            continue
        todo = [(int(row), int(col))]
        seen[row, col] = True
        cells: list[tuple[int, int]] = []
        while todo:
            r, c = todo.pop()
            cells.append((r, c))
            for rr, cc in grid.neighbors(r, c):
                if mask[rr, cc] and not seen[rr, cc]:
                    seen[rr, cc] = True
                    todo.append((rr, cc))
        components.append(cells)
    components.sort(key=len, reverse=True)
    return components


def _land_and_coast(grid: GlobalGrid1Degree, streams: dict[str, np.random.Generator],
                    area: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    geom_rng, coast_rng = streams["continental_blocks"], streams["coastline"]
    center_lat = float(geom_rng.uniform(-5.0, 5.0))
    center_lon = float(geom_rng.uniform(-180.0, 180.0))
    angle = float(geom_rng.uniform(-0.20, 0.20))
    lat = grid.lat_centers_deg[:, None]
    lon = grid.lon_centers_deg[None, :]
    dlon = _wrap_degrees(lon - center_lon) * np.cos(np.deg2rad(center_lat))
    dlat = lat - center_lat
    x = dlon * np.cos(angle) + dlat * np.sin(angle)
    y = -dlon * np.sin(angle) + dlat * np.cos(angle)
    irregularity = _harmonic_boundary(grid, coast_rng)
    main_score = 1.0 - np.sqrt((x / 108.0) ** 2 + (y / 52.0) ** 2) + 0.14 * irregularity
    main = _area_threshold(main_score, area, 0.27)

    islands = np.zeros(grid.shape, dtype=bool)
    centers = [
        (center_lat - 5.0, center_lon - 142.0),
        (center_lat + 6.0, center_lon + 142.0),
        (67.0, center_lon - 30.0),
        (-67.0, center_lon + 45.0),
    ]
    island_rngs = [coast_rng, geom_rng, coast_rng, geom_rng]
    for ilat, ilon in zip(centers, island_rngs):
        lat0, lon0 = ilat
        distance = grid.spherical_distance_km(lat0, lon0, lat, lon)
        # A bounded low-amplitude harmonic perturbation makes each terrane non-circular.
        local_phase = float(ilon.uniform(0, 2 * pi))
        perturb = (0.035 * np.sin(np.deg2rad(lon - lon0) * 3 + local_phase) *
                   np.cos(np.deg2rad(lat - lat0) * 2 - local_phase))
        patch = _area_threshold(-distance / 1100.0 + perturb, area, 0.0075,
                                eligible=~(main | islands))
        islands |= patch
    land = main | islands
    components = _connected_components(land, grid)
    if len(components) != 5:
        raise ValueError(f"canonical geometry produced {len(components)} land components, expected 5" )
    coast = np.zeros(grid.shape, dtype=bool)
    for row, col in zip(*np.nonzero(land)):
        if any(not land[rr, cc] for rr, cc in grid.neighbors(int(row), int(col))):
            coast[row, col] = True
    detail = {
        "center_latitude_deg": center_lat,
        "center_longitude_deg": center_lon,
        "orientation_radians": angle,
        "main_component_area_fraction_target": 0.27,
        "secondary_terranes": 4,
        "each_terrane_area_fraction_target": 0.0075,
        "connected_components": len(components),
        "component_cell_counts_descending": [len(c) for c in components],
    }
    return land, coast, detail


def _plate_and_province(grid: GlobalGrid1Degree, land: np.ndarray,
                        coastline: np.ndarray,
                        streams: dict[str, np.random.Generator]) -> tuple[np.ndarray, ...]:
    plate_rng = streams["plate_mosaic"]
    block_rng = streams["continental_blocks"]
    nplates = int(plate_rng.integers(12, 19))
    plate_lat = np.rad2deg(np.arcsin(plate_rng.uniform(-1.0, 1.0, nplates)))
    plate_lon = plate_rng.uniform(-180.0, 180.0, nplates)
    latr = np.deg2rad(grid.lat_centers_deg)[:, None]
    lonr = np.deg2rad(grid.lon_centers_deg)[None, :]
    best = np.full(grid.shape, -2.0, dtype=np.float64)
    plate_id = np.zeros(grid.shape, dtype=np.int16)
    for pid, (plat, plon) in enumerate(zip(plate_lat, plate_lon)):
        platr, plonr = np.deg2rad(plat), np.deg2rad(plon)
        dot = np.sin(latr) * np.sin(platr) + np.cos(latr) * np.cos(platr) * np.cos(lonr - plonr)
        replace = dot > best
        plate_id[replace] = pid
        best[replace] = dot[replace]

    crust = np.where(land, 1, 0).astype(np.int8)  # 0 oceanic, 1 continental
    for row, col in zip(*np.nonzero(coastline)):
        crust[row, col] = 2  # transitional margin; no passive/active process claim

    # Plate-boundary cells have geometry but no kinematic class: leave UNKNOWN.
    boundary = np.ones(grid.shape, dtype=np.int8)  # 0 UNKNOWN, 1 INTERIOR
    for row in range(grid.nlat):
        for col in range(grid.nlon):
            if any(plate_id[rr, cc] != plate_id[row, col]
                   for rr, cc in grid.neighbors(row, col)):
                boundary[row, col] = 0

    main_cells = np.flatnonzero(land & ~coastline)
    ncratons = int(block_rng.integers(4, 9))
    chosen: list[int] = []
    candidate_order = block_rng.permutation(main_cells)
    for idx in candidate_order:
        row, col = grid.row_col(int(idx))
        if all(grid.spherical_distance_km(
                grid.lat_centers_deg[row], grid.lon_centers_deg[col],
                np.array([grid.lat_centers_deg[grid.row_col(c)[0]]]),
                np.array([grid.lon_centers_deg[grid.row_col(c)[1]]]))[0] >= 1400.0
               for c in chosen):
            chosen.append(int(idx))
            if len(chosen) == ncratons:
                break
    if len(chosen) != ncratons:
        raise ValueError("could not place the contract-bounded continental blocks")
    seed_rows = np.array([grid.row_col(i)[0] for i in chosen], dtype=np.int16)
    seed_cols = np.array([grid.row_col(i)[1] for i in chosen], dtype=np.int16)
    seed_lat = grid.lat_centers_deg[seed_rows]
    seed_lon = grid.lon_centers_deg[seed_cols]
    distances = np.stack([
        grid.spherical_distance_km(float(a), float(o),
                                   grid.lat_centers_deg[:, None], grid.lon_centers_deg[None, :])
        for a, o in zip(seed_lat, seed_lon)
    ], axis=0)
    nearest = np.argmin(distances, axis=0).astype(np.int8)
    nearest[~land] = -2
    province = np.full(grid.shape, -2, dtype=np.int8)  # -2 NOT_APPLICABLE; -1 UNKNOWN
    province[land] = 0  # OTHER_DESIGN
    nearest_distance = np.min(distances, axis=0)
    province[land & (nearest_distance <= 950.0)] = 1  # CRATON
    suture = np.zeros(grid.shape, dtype=bool)
    for row, col in zip(*np.nonzero(land)):
        if any(land[rr, cc] and nearest[rr, cc] != nearest[row, col]
               for rr, cc in grid.neighbors(int(row), int(col))):
            suture[row, col] = True
    province[suture] = 2  # SUTURE
    lon = np.deg2rad(grid.lon_centers_deg)[None, :]
    lat = np.deg2rad(grid.lat_centers_deg)[:, None]
    orogenic_score = np.sin(3.0 * lon + float(block_rng.uniform(0, 2*pi))) * np.cos(
        2.0 * lat + float(block_rng.uniform(0, 2*pi)))
    if suture.any():
        threshold = float(np.quantile(orogenic_score[suture], 0.55))
        province[suture & (orogenic_score >= threshold)] = 3  # OROGENIC_DESIGN
    seed_ids = tuple(grid.cell_id(int(r), int(c)) for r, c in zip(seed_rows, seed_cols))
    return plate_id, crust, boundary, province, nplates, seed_ids


def generate_initial_world(grid: GlobalGrid1Degree | None = None,
                           seed_root_material: bytes = SEED_ROOT_MATERIAL) -> InitialWorldFields:
    """Generate one R6 design state at 210 Ma; never advances time or uses A1 values."""
    grid = grid or GlobalGrid1Degree()
    streams = {s.name: s.rng() for s in derive_seed_streams(root_material=seed_root_material)}
    areas = grid.cell_areas_m2()
    land, coast, geometry = _land_and_coast(grid, streams, areas)
    plate_id, crust, boundary, province, nplates, craton_seed_cells = _plate_and_province(
        grid, land, coast, streams)
    elevation, elev_support = generate_land_elevation(
        grid, land, province, streams["land_relief"])
    area_weight = areas / areas.sum()
    land_fraction = float(area_weight[land].sum())
    components = _connected_components(land, grid)
    component_cells = [len(c) for c in components]
    component_area_fractions = [
        float(sum(areas[r, c] for r, c in component) / areas.sum())
        for component in components
    ]
    metadata = {
        "generator_id": "ARCANA_R6_SUPERCONTINENT_GENERATOR_V1",
        "generator_version": "1.0.0",
        "time_ma": 210.0,
        "seed_root_sha256": sha256(seed_root_material).hexdigest(),
        "canonical_seed": seed_root_material == SEED_ROOT_MATERIAL,
        "land_fraction_area_weighted": land_fraction,
        "ocean_fraction_area_weighted": 1.0 - land_fraction,
        "dominant_component_share_of_land": component_area_fractions[0] / land_fraction,
        "geometry_parameters": geometry,
        "plate_count": nplates,
        "continental_cratonic_block_count": len(craton_seed_cells),
        "craton_seed_cells": list(craton_seed_cells),
        "component_cell_counts_descending": component_cells,
        "component_area_fractions_of_surface_descending": component_area_fractions,
        "plate_motion": "UNKNOWN",
        "bathymetry": "UNKNOWN",
        "deep": "UNKNOWN",
        "climate": "UNKNOWN",
        "hydrology": "UNKNOWN",
        "land_elevation_authority": "AUTHORIAL_SYNTHETIC_INITIALIZATION",
        "a1_used_as_input": False,
        "forward_evolution_executed": False,
    }
    if len(component_cells) != 5 or nplates not in range(12, 19) or len(craton_seed_cells) not in range(4, 9):
        raise ValueError("generated geography violates fixed structural design")
    return InitialWorldFields(
        grid=grid, time_ma=210.0,
        land_ocean_mask=land.astype(np.uint8), coastline_mask=coast.astype(np.uint8),
        plate_id=plate_id, crust_class=crust, boundary_class=boundary,
        province_class=province, land_surface_elevation_m=elevation,
        elevation_support_mask=elev_support,
        synthetic_uncertainty_mask=elev_support.copy(),
        bathymetry_unknown_mask=(~land).astype(bool),
        plate_motion_unknown_mask=np.ones(grid.shape, dtype=bool),
        deep_unknown_mask=np.ones(grid.shape, dtype=bool),
        climate_unknown_mask=np.ones(grid.shape, dtype=bool),
        hydrology_unknown_mask=np.ones(grid.shape, dtype=bool),
        craton_seed_cells=craton_seed_cells, plate_count=nplates, metadata=metadata)
