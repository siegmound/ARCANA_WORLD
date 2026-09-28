"""Deterministic noncanonical B_PANGAEA_LATE_TRIASSIC_v2 T0 materializer."""
from __future__ import annotations

import hashlib
import heapq
import io
import json
import math
import zipfile
from pathlib import Path
from typing import Any

import numpy as np

from arcana_worldsim.r6.repository_context import resolve_external_payload_path

R = 6_371_000.0
ROWS, COLS = 180, 360
GEO_SHA = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
PARTITION_SHA = "a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab"
KIN_SHA = "50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4"
MESH_SHA = "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad"
REALIZATION_ID = "B_PANGAEA_LIKE_LATE_TRIASSIC_v2"
BASE_FIELD_PACKAGE_SHA256 = "39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e"
AGE_FIELD_SHA256 = "aed3d311296947aad0f4cc041cfbb1b2784763704b23b1a3e746d2079a607dc2"
OCEAN_RESIDUAL_SHA256 = "315078fc021637823399a8a96272dcfc69d7746a3098064042119d7453755cfc"
LAND_ELEVATION_SHA256 = "79b8a50159c5f74b94a0e0f4d856336a829c9e1d1cf9ee145ba0daac97f96c45"
GDH1_MODEL_ID = "GDH1_STEIN_STEIN_1992_WATER_LOADED_AGE_DEPTH_V1"

DOMAIN_IDS = {
    "NORMAL_OCEANIC": 1,
    "TRANSITIONAL_MARGIN": 2,
    "EXTENDED_CONTINENTAL": 3,
    "NORMAL_CONTINENTAL": 4,
    "STABLE_CONTINENTAL": 5,
    "OROGENIC_THICKENED": 6,
}
THERMAL_IDS = {"COLD_STABLE": 1, "NORMAL": 2, "HOT_EXTENDED": 3}
THICKNESS_KM = {1: 6.5, 2: 25.0, 3: 28.0, 4: 35.0, 5: 40.0, 6: 50.0}
HEAT_FLOW_MW_M2 = {1: 45.0, 2: 60.0, 3: 85.0}
LITHOSPHERE_KM = {1: 200.0, 2: 135.0, 3: 80.0}


def _json(root: Path, name: str) -> dict[str, Any]:
    return json.loads((root / name).read_text(encoding="utf-8"))


def _cell_area() -> np.ndarray:
    edge = np.deg2rad(np.arange(-90.0, 91.0))
    bands = R * R * math.radians(1.0) * (np.sin(edge[1:]) - np.sin(edge[:-1]))
    return np.broadcast_to(bands[:, None], (ROWS, COLS))


def _neighbors(row: int, col: int, support: np.ndarray):
    for dr in (-1, 0, 1):
        rr = row + dr
        if rr < 0 or rr >= ROWS:
            continue
        for dc in (-1, 0, 1):
            if dr == dc == 0:
                continue
            cc = (col + dc) % COLS
            if support[rr, cc]:
                yield rr, cc
    if row in (0, ROWS - 1):
        for cc in np.flatnonzero(support[row]):
            if int(cc) != col:
                yield row, int(cc)


def _step_m(r1: int, c1: int, r2: int, c2: int) -> float:
    lat1, lat2 = math.radians(r1 - 89.5), math.radians(r2 - 89.5)
    dlat = lat2 - lat1
    dlon = math.radians(((c2 - c1 + 180) % 360) - 180)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(max(0.0, h))))


def _distance_field(support: np.ndarray, seeds: dict[tuple[int, int], float]) -> tuple[np.ndarray, np.ndarray]:
    """Shortest spherical grid distance and nearest seed score, deterministic ties."""
    dist = np.full((ROWS, COLS), np.inf, dtype=np.float64)
    score = np.zeros((ROWS, COLS), dtype=np.float64)
    source_id = np.full((ROWS, COLS), np.iinfo(np.int32).max, dtype=np.int32)
    queue: list[tuple[float, int, int, int, float]] = []
    for source_no, ((row, col), strength) in enumerate(sorted(seeds.items())):
        dist[row, col] = 0.0
        score[row, col] = strength
        source_id[row, col] = source_no
        heapq.heappush(queue, (0.0, source_no, row, col, strength))
    while queue:
        distance, sid, row, col, strength = heapq.heappop(queue)
        if distance != dist[row, col] or sid != source_id[row, col]:
            continue
        for rr, cc in _neighbors(row, col, support):
            candidate = distance + _step_m(row, col, rr, cc)
            if candidate < dist[rr, cc] - 1e-8 or (
                    abs(candidate - dist[rr, cc]) <= 1e-8 and sid < source_id[rr, cc]):
                dist[rr, cc] = candidate
                score[rr, cc] = strength
                source_id[rr, cc] = sid
                heapq.heappush(queue, (candidate, sid, rr, cc, strength))
    return dist, score


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(weights[order])
    return float(values[order[np.searchsorted(cumulative, cumulative[-1] / 2.0, side="left")]])


def _edge_cells(row: int, col: int, axis: int) -> tuple[tuple[int, int], tuple[int, int]]:
    if axis == 0:
        return (row, col), (row, (col + 1) % COLS)
    return (row, col), (row + 1, col)


def _low_frequency_residual(ocean: np.ndarray, area: np.ndarray) -> tuple[np.ndarray, dict]:
    seed_bytes = hashlib.sha256(REALIZATION_ID.encode("utf-8")).digest()
    seed = int.from_bytes(seed_bytes[:16], "big")
    rng = np.random.default_rng(seed)
    lat = np.deg2rad(np.arange(-89.5, 90.0, 1.0))
    lon = np.deg2rad(np.arange(-179.5, 180.0, 1.0))
    xyz = np.stack(np.broadcast_arrays(
        np.cos(lat)[:, None] * np.cos(lon)[None, :],
        np.cos(lat)[:, None] * np.sin(lon)[None, :],
        np.sin(lat)[:, None] + np.zeros((1, COLS))), axis=-1).reshape(-1, 3)
    modes = 32
    directions = rng.normal(size=(modes, 3))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    wavelengths_km = rng.uniform(1200.0, 2500.0, size=modes)
    phases = rng.uniform(0.0, 2 * math.pi, size=modes)
    raw = np.zeros(ROWS * COLS, dtype=np.float64)
    for direction, wavelength, phase in zip(directions, wavelengths_km, phases):
        angular_distance = np.arccos(np.clip(xyz @ direction, -1.0, 1.0))
        raw += np.cos((R / 1000.0) * angular_distance * 2 * math.pi / wavelength + phase)
    raw = raw.reshape(ROWS, COLS)
    weights = area[ocean]
    samples = raw[ocean]

    def centered_clipped(scale: float) -> np.ndarray:
        lo, hi = -5000.0, 5000.0
        for _ in range(48):
            offset = (lo + hi) / 2.0
            mean = float(np.average(np.clip(scale * samples + offset, -1200.0, 1200.0), weights=weights))
            if mean > 0:
                hi = offset
            else:
                lo = offset
        return np.clip(scale * samples + (lo + hi) / 2.0, -1200.0, 1200.0)

    lo, hi = 0.0, 10_000.0
    for _ in range(56):
        scale = (lo + hi) / 2.0
        values = centered_clipped(scale)
        rms = math.sqrt(float(np.average(values * values, weights=weights)))
        if rms < 500.0:
            lo = scale
        else:
            hi = scale
    values = centered_clipped((lo + hi) / 2.0)
    residual = np.full((ROWS, COLS), np.nan, dtype=np.float64)
    residual[ocean] = values
    evidence = {
        "generator": "SUM_OF_32_SEEDED_GEODESIC_RADIAL_MODES",
        "seed_derivation": "first 128 SHA256 bits of UTF-8 authorial_realization_id, unsigned big-endian",
        "seed_uint128_hex": hex(seed),
        "mode_count": modes,
        "mode_wavelength_min_km": float(wavelengths_km.min()),
        "mode_wavelength_max_km": float(wavelengths_km.max()),
        "target_rms_m": 500.0,
        "observed_area_weighted_ocean_rms_m": math.sqrt(float(np.average(values * values, weights=weights))),
        "observed_area_weighted_ocean_mean_m": float(np.average(values, weights=weights)),
        "observed_hard_cap_abs_m": float(np.max(np.abs(values))),
        "field_sha256": _array_sha256(residual),
    }
    return residual, evidence


def _array_sha256(array: np.ndarray) -> str:
    array = np.asarray(array)
    canonical = np.ascontiguousarray(array.astype(array.dtype.newbyteorder("<"), copy=False))
    digest = hashlib.sha256()
    digest.update(str(canonical.dtype).encode())
    digest.update(json.dumps(list(canonical.shape), separators=(",", ":")).encode())
    digest.update(canonical.tobytes())
    return digest.hexdigest()


def gdh1_water_loaded_depth_m(age_ma: np.ndarray) -> np.ndarray:
    """Stein & Stein (1992) GDH1 water-loaded basement depth, positive down.

    Nonfinite ages remain UNKNOWN (NaN). The function does not classify
    geographic support; callers must apply it only to governed ocean cells.
    """
    age = np.asarray(age_ma, dtype=np.float64)
    if np.any(np.isfinite(age) & (age < 0.0)):
        raise ValueError("GDH1 age must be nonnegative on known support")
    depth = np.full(age.shape, np.nan, dtype=np.float64)
    young = np.isfinite(age) & (age < 20.0)
    old = np.isfinite(age) & ~young
    depth[young] = 2600.0 + 365.0 * np.sqrt(age[young])
    depth[old] = 5651.0 - 2473.0 * np.exp(-0.0278 * age[old])
    return depth


def compose_ocean_surface(
    age_ma: np.ndarray,
    ocean_residual_m: np.ndarray,
    canonical_land_elevation_m: np.ndarray,
    ocean_support: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return thermal component, total surface and ocean UNKNOWN mask."""
    age = np.asarray(age_ma, dtype=np.float64)
    residual = np.asarray(ocean_residual_m, dtype=np.float64)
    land_surface = np.asarray(canonical_land_elevation_m, dtype=np.float64)
    ocean = np.asarray(ocean_support, dtype=bool)
    if not (age.shape == residual.shape == land_surface.shape == ocean.shape):
        raise ValueError("age, residual, land elevation and support shapes must match")
    if not np.isfinite(land_surface[~ocean]).all():
        raise ValueError("canonical land elevation must be known across land support")
    depth = gdh1_water_loaded_depth_m(np.where(ocean, age, np.nan))
    thermal = np.full(age.shape, np.nan, dtype=np.float64)
    known = ocean & np.isfinite(depth)
    thermal[known] = -depth[known]
    total = np.full(age.shape, np.nan, dtype=np.float64)
    total[~ocean] = land_surface[~ocean]
    compose = known & np.isfinite(residual)
    total[compose] = thermal[compose] + residual[compose]
    unknown = ocean & ~np.isfinite(total)
    return thermal, total, unknown


def close_ocean_surface(root: str | Path) -> dict[str, Any]:
    """Create a versioned GDH1 surface package from the immutable B-v2 package."""
    root = Path(root).resolve()
    baseline = _json(root, "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json")
    source_path = root / baseline["field_package_path"]
    source_bytes = source_path.read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    if source_sha != BASE_FIELD_PACKAGE_SHA256 or baseline["field_package_sha256"] != BASE_FIELD_PACKAGE_SHA256:
        raise ValueError("the governed B-v2 parent package identity is not the expected baseline")
    with np.load(io.BytesIO(source_bytes), allow_pickle=False) as archive:
        fields = {name: archive[name].copy() for name in archive.files}
    original_hashes = {name: _array_sha256(value) for name, value in fields.items()}
    expected = {
        "oceanic_lithosphere_age_ma": AGE_FIELD_SHA256,
        "ocean_surface_authorial_residual_m": OCEAN_RESIDUAL_SHA256,
        "canonical_land_surface_elevation_m": LAND_ELEVATION_SHA256,
    }
    for name, digest in expected.items():
        if original_hashes.get(name) != digest or baseline["normalized_field_hashes"].get(name) != digest:
            raise ValueError(f"governed parent component identity mismatch: {name}")
    ocean = fields["physical_crust_domain_id"] == DOMAIN_IDS["NORMAL_OCEANIC"]
    if int(np.count_nonzero(ocean)) != 50_542:
        raise ValueError("governed ocean support changed")
    age = np.asarray(fields["oceanic_lithosphere_age_ma"], dtype=np.float64)
    residual = np.asarray(fields["ocean_surface_authorial_residual_m"], dtype=np.float64)
    land_surface = np.asarray(fields["canonical_land_surface_elevation_m"], dtype=np.float64)
    thermal, total, unknown = compose_ocean_surface(age, residual, land_surface, ocean)
    if np.any(np.isfinite(thermal[~ocean])) or not np.array_equal(
            total[~ocean], land_surface[~ocean]):
        raise ValueError("surface composition changed land or applied ocean physics off support")
    known_ocean = ocean & ~unknown
    if not known_ocean.any():
        raise ValueError("GDH1 produced no known ocean elevation cells")
    if np.any(total[known_ocean] >= 0.0):
        raise ValueError("composed ocean surface reaches the zero-datum land threshold")
    fields["ocean_thermal_isostatic_elevation_m"] = thermal
    fields["total_surface_elevation_m"] = total
    fields["unknown_total_ocean_elevation_mask"] = unknown

    package_name = "R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE_SURFACE_CLOSED.npz"
    package_path = root / package_name
    package_sha = _write_deterministic_npz(package_path, fields)
    field_hashes = {name: _array_sha256(value) for name, value in fields.items()}
    area = _cell_area()
    vals = total[known_ocean]
    weights = area[known_ocean]
    order = np.argsort(vals, kind="stable")
    cumulative = np.cumsum(weights[order])
    median = float(vals[order[np.searchsorted(cumulative, cumulative[-1] / 2.0, side="left")]])
    residual_mean = float(np.average(residual[known_ocean], weights=weights))
    residual_rms = math.sqrt(float(np.average(residual[known_ocean] ** 2, weights=weights)))
    residual_cap = float(np.max(np.abs(residual[known_ocean])))
    at20_left = 2600.0 + 365.0 * math.sqrt(20.0)
    at20_right = 5651.0 - 2473.0 * math.exp(-0.0278 * 20.0)
    # The age transform itself is immutable; only its derived consequence is added.
    ages_probe = np.linspace(0.0, 160.0, 16001)
    depths_probe = gdh1_water_loaded_depth_m(ages_probe)
    if np.any(np.diff(depths_probe) < 0.0):
        raise ValueError("GDH1 subsidence must be monotone over the ARCANA age range")
    closure = {
        "schema": "R6_T0_B_PANGAEA_LIKE_V2_OCEAN_SURFACE_CLOSURE_V1",
        "decision": "R6_T0_OCEAN_THERMAL_ISOSTATIC_SURFACE_MATERIALIZED__ORBDATA_INPUT_GAPS_REMAIN",
        "realization_id": REALIZATION_ID,
        "authority": {
            "thermal_component": "SPECIALIST_DERIVED_T0",
            "authorial_residual": "AUTHORIAL_T0_PRIMITIVE",
            "total_surface": "SPECIALIST_DERIVED_T0",
            "model_coefficients": "SPECIALIST_MODEL_CONFIGURATION/PUBLISHED_EARTH_ANALOGUE_PHYSICAL_MODEL",
            "earth_observation_imported": False,
            "canonical_geography_mutated": False,
            "orbdata_generated_bathymetry": False,
        },
        "model_configuration": {
            "model_id": GDH1_MODEL_ID, "version": "1.0.0",
            "citation": "Stein, C.A. & Stein, S. (1992), Nature 359, 123-128, doi:10.1038/359123a0",
            "source_url": "https://doi.org/10.1038/359123a0",
            "selection_rationale": ["Published age-depth relation with water-loaded basement depth.",
                                    "GDH1-family choice is coherent with the pinned OrbData5 oceanic 95 km plate-thickness reference; OrbData itself does not generate this elevation.",
                                    "Only the published law is applied to ARCANA's governed synthetic age field; no Earth bathymetry or observations are imported."],
            "age_units": "Ma", "depth_units": "m positive downward",
            "elevation_units": "m positive upward relative to the existing R6 zero datum",
            "water_loading": "The published GDH1 water-loaded basement-depth relation is applied directly; no additional correction.",
            "coefficients": {"young_branch": {"age_lt_ma": 20, "base_depth_m": 2600, "sqrt_age_coefficient_m_per_sqrt_ma": 365},
                             "old_branch": {"age_gte_ma": 20, "asymptotic_depth_m": 5651, "amplitude_m": 2473, "decay_per_ma": 0.0278}},
            "branch_at_20_ma": {"young_limit_depth_m": at20_left, "old_branch_depth_m": at20_right,
                                "discontinuity_old_minus_young_m": at20_right - at20_left},
        },
        "model_form_uncertainty": {
            "axis": "OCEAN_PLATE_COOLING_MODEL_FORM", "primary": "GDH1_COMPATIBLE_REFERENCE",
            "comparator": "REVISED_PLATE_MODEL_FAMILY", "candidate_ensemble_generated": False,
            "disposition": "Retain GDH1 as the selected T0 reference; record comparator for a later sensitivity study, do not substitute its Earth best fit or average models into ARCANA.",
            "reference_literature": {"doi": "10.1029/2024JB029890", "published": 2025,
                                     "reported_plate_thickness_km": "approximately 105 +/- 10 (analytical) and 96 +/- 10 (detailed), as cited in the governed task input",
                                     "reported_mantle_temperature_c": "approximately 1326 +/- 50, as cited in the governed task input",
                                     "ridge_depth_km": "2.5 +/- 0.3; general published reference, not imported as ARCANA observation"},
        },
        "parent": {"manifest_path": "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST.json",
                   "field_package_path": baseline["field_package_path"],
                   "field_package_sha256": source_sha,
                   "realization_manifest_sha256": baseline["realization_manifest_sha256"]},
        "materialized": {"field_package_path": package_name, "field_package_sha256": package_sha,
                         "normalized_field_hashes": field_hashes},
        "component_lineage": {
            "unchanged_parent_field_hashes": {name: digest for name, digest in original_hashes.items()
                                                if name != "unknown_total_ocean_elevation_mask"},
            "unknown_mask": {"name": "unknown_total_ocean_elevation_mask",
                             "parent_sha256": original_hashes["unknown_total_ocean_elevation_mask"],
                             "new_sha256": field_hashes["unknown_total_ocean_elevation_mask"],
                             "meaning": "ocean cells whose composed total elevation remains UNKNOWN"},
            "age_field": {"name": "oceanic_lithosphere_age_ma", "sha256_before_after": [AGE_FIELD_SHA256, field_hashes["oceanic_lithosphere_age_ma"]]},
            "thermal_component": {"name": "ocean_thermal_isostatic_elevation_m", "sha256": field_hashes["ocean_thermal_isostatic_elevation_m"], "formula": "-GDH1_water_loaded_depth(age_ma)"},
            "authorial_residual": {"name": "ocean_surface_authorial_residual_m", "sha256_before_after": [OCEAN_RESIDUAL_SHA256, field_hashes["ocean_surface_authorial_residual_m"]]},
            "land_component": {"name": "canonical_land_surface_elevation_m", "sha256_before_after": [LAND_ELEVATION_SHA256, field_hashes["canonical_land_surface_elevation_m"]]},
            "total_surface": {"name": "total_surface_elevation_m", "sha256": field_hashes["total_surface_elevation_m"], "ocean_formula": "thermal_component + authorial_residual", "land_formula": "exactly canonical_land_surface_elevation_m"},
        },
        "statistics": {
            "ocean_cells": int(ocean.sum()), "known_ocean_elevation_cells": int(known_ocean.sum()),
            "unknown_ocean_elevation_cells": int(unknown.sum()), "ocean_coverage_fraction": float(known_ocean.sum() / ocean.sum()),
            "thermal_elevation_min_m": float(np.min(thermal[known_ocean])), "thermal_elevation_max_m": float(np.max(thermal[known_ocean])),
            "total_ocean_elevation_min_m": float(np.min(vals)), "total_ocean_elevation_max_m": float(np.max(vals)),
            "total_ocean_area_weighted_mean_m": float(np.average(vals, weights=weights)),
            "total_ocean_area_weighted_median_m": median,
            "total_ocean_depth_min_m": float(np.min(-vals)), "total_ocean_depth_max_m": float(np.max(-vals)),
            "age_depth_monotone_0_160_ma": True,
            "residual_area_weighted_mean_m": residual_mean, "residual_area_weighted_rms_m": residual_rms,
            "residual_hard_cap_abs_m": residual_cap,
            "ocean_cells_at_or_above_zero_datum": int(np.count_nonzero(total[known_ocean] >= 0.0)),
        },
        "pre_orbdata_impact": {
            "complete_ocean_elevation_component_materialized": bool(known_ocean[ocean].all()),
            "PRE_ORBDATA_ready": False,
            "remaining_gates": ["global heat-flow routing and qArray policy", "aArray export and coast-classification qualification",
                                "cArray export", "continental mantle thickness sArray interoperability",
                                "OrbData material/thermal configuration", "FEG nodal materialization and zero-elevation interface qualification"],
        },
        "governance": {"age_regenerated": False, "authorial_residual_regenerated": False,
                       "canonical_land_elevation_changed": False, "canonical_geography_changed": False,
                       "canonical_promoted": False, "orbdata_executed": False, "shellset_mechanics_executed": False,
                       "forward_evolution": False, "dt_selected": False, "t1_created": False},
    }
    closure["closure_manifest_sha256"] = hashlib.sha256(
        json.dumps(closure, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return closure


def _write_deterministic_npz(path: Path, arrays: dict[str, np.ndarray]) -> str:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(arrays):
            buffer = io.BytesIO()
            np.save(buffer, np.asarray(arrays[name]), allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o600 << 16
            archive.writestr(info, buffer.getvalue())
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(root: str | Path) -> dict[str, Any]:
    root = Path(root).resolve()
    geo_manifest = _json(root, "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json")
    vector_manifest = _json(root, "R6_T0_VECTOR_PLATE_PARTITION_MANIFEST.json")
    kin = _json(root, "R6_SHARED_BOUNDARY_T0_KINEMATIC_CENSUS.json")
    branches = _json(root, "R6_T0_CANONICAL_BOUNDARY_BRANCH_REGISTRY.json")
    ratification = _json(root, "R6_T0_AUTHORIAL_RATIFICATION_B_PANGAEA_LIKE_LATE_TRIASSIC.json")
    if ratification["authorial_candidate_id"] != REALIZATION_ID:
        raise ValueError("B-v2 ratification identity mismatch")

    geo_path = resolve_external_payload_path(root, geo_manifest["payload"]["relative_path"])
    vector_path = resolve_external_payload_path(root, vector_manifest["payload"]["path"])
    geo_sha = hashlib.sha256(geo_path.read_bytes()).hexdigest()
    vector_sha = hashlib.sha256(vector_path.read_bytes()).hexdigest()
    if geo_sha != GEO_SHA or vector_sha != PARTITION_SHA or kin["canonical_kinematics_sha256"] != KIN_SHA:
        raise ValueError("canonical geography/vector/kinematics identity check failed")
    with np.load(geo_path, allow_pickle=False) as archive:
        geography = {name: archive[name].copy() for name in archive.files}
    with np.load(vector_path, allow_pickle=False) as archive:
        vector = {name: archive[name].copy() for name in archive.files}

    land = geography["land_ocean_mask"].astype(bool)
    ocean = ~land
    area = _cell_area()
    if land.shape != (ROWS, COLS) or int(land.sum()) != 14_258:
        raise ValueError("canonical land/ocean support differs from audited identity")

    kin_by_edge = {
        (int(row["parent_grid_edge"]["row"]), int(row["parent_grid_edge"]["column"]),
         0 if row["parent_grid_edge"]["axis"] == "EAST" else 1): row
        for row in kin["segments"]
    }
    if len(kin_by_edge) != 1_983:
        raise ValueError("canonical boundary kinematics do not cover all 1,983 edges")
    edge_rows = vector["boundary_edge_row"].astype(int)
    edge_cols = vector["boundary_edge_col"].astype(int)
    edge_axis = vector["boundary_edge_axis"].astype(int)
    conv_score = np.zeros((ROWS, COLS), dtype=np.float64)
    ext_score = np.zeros((ROWS, COLS), dtype=np.float64)
    plate_boundary_support = np.zeros((ROWS, COLS), dtype=bool)
    ocean_source_candidates: dict[str, list[tuple[tuple[int, int], tuple[int, int]]]] = {}
    edge_to_boundary: dict[tuple[int, int, int], str] = {}
    for index, (row, col, axis) in enumerate(zip(edge_rows, edge_cols, edge_axis)):
        record = kin_by_edge[(int(row), int(col), int(axis))]
        boundary_id = record["boundary_id"]
        edge_to_boundary[(int(row), int(col), int(axis))] = boundary_id
        left, right = _edge_cells(int(row), int(col), int(axis))
        for rr, cc in (left, right):
            if rr < ROWS:
                plate_boundary_support[rr, cc] = True
        signed = float(record["relative_normal_velocity_m_per_year"])
        length = float(record["length_m"])
        for cell, support_code in ((left, int(vector["boundary_crust_a"][index])),
                                   (right, int(vector["boundary_crust_b"][index]))):
            rr, cc = cell
            if rr >= ROWS or not land[rr, cc]:
                continue
            if signed < 0:
                conv_score[rr, cc] += abs(signed) * length
            elif signed > 0:
                ext_score[rr, cc] += signed * length
        if signed > 0 and ocean[left] and ocean[right]:
            ocean_source_candidates.setdefault(boundary_id, []).append((left, right))

    branch_by_id = {edge: branch for branch in branches["branches"]
                    for edge in branch["ordered_canonical_boundary_segment_ids"]}
    candidate_ids = set(ocean_source_candidates)
    candidate_branches: dict[str, list[str]] = {}
    for boundary_id in candidate_ids:
        branch = branch_by_id.get(boundary_id)
        if branch:
            candidate_branches.setdefault(branch["canonical_branch_id"], []).append(boundary_id)
    branch_lengths = {}
    length_by_id = {str(row["boundary_id"]): float(row["length_m"]) for row in kin["segments"]}
    for branch_id, boundary_ids in candidate_branches.items():
        branch_lengths[branch_id] = sum(length_by_id[item] for item in boundary_ids)
    if not branch_lengths:
        raise ValueError("no oceanic positive-normal boundary candidate exists for age initialization")
    selected_branch_id = min(branch_lengths, key=lambda key: (-branch_lengths[key], key))
    selected_source_ids = sorted(candidate_branches[selected_branch_id])
    age_seeds: dict[tuple[int, int], float] = {}
    for boundary_id in selected_source_ids:
        for cell_pair in ocean_source_candidates[boundary_id]:
            for cell in cell_pair:
                age_seeds[cell] = 1.0
    distance, _ = _distance_field(ocean, age_seeds)
    ocean_distance = distance[ocean]
    if not np.isfinite(ocean_distance).all():
        raise ValueError("selected spreading-source set does not cover the connected ocean support")
    median_distance = _weighted_median(ocean_distance, area[ocean])
    max_distance = float(ocean_distance.max())
    if median_distance <= 0 or max_distance <= median_distance:
        raise ValueError("age distance field cannot satisfy the ratified median/range")
    exponent = math.log(70.0 / 160.0) / math.log(median_distance / max_distance)
    age = np.full((ROWS, COLS), np.nan, dtype=np.float64)
    age[ocean] = 160.0 * np.power(distance[ocean] / max_distance, exponent)
    age_evidence = {
        "source_selection": "longest canonical branch among ocean/ocean edges with positive normal kinematic demand; stable ID tie-break",
        "candidate_oceanic_divergent_boundary_segments": len(candidate_ids),
        "selected_source_branch_id": selected_branch_id,
        "selected_source_boundary_ids": selected_source_ids,
        "selected_source_support_cells": len(age_seeds),
        "age_generation": "monotone_power_transform_of_shortest_spherical_grid_distance; no constant spreading-rate claim",
        "power_exponent": exponent,
        "age_min_ma": float(np.nanmin(age)),
        "age_max_ma": float(np.nanmax(age)),
        "area_weighted_ocean_median_ma": _weighted_median(age[ocean], area[ocean]),
        "age_sha256": _array_sha256(age),
    }
    if age_evidence["age_min_ma"] < 0 or age_evidence["age_max_ma"] > 160.0 + 1e-9 or abs(age_evidence["area_weighted_ocean_median_ma"] - 70.0) > 1e-8:
        raise ValueError("generated ocean age field violates ratified bounds/median")

    # Boundary/coast support initializes coherent classes; rank domains are
    # selected from the ratified soft envelopes, not from legacy province tags.
    land_cells = list(zip(*np.where(land)))
    cont_area = float(area[land].sum())
    ext_support = land & (ext_score > 0)
    conv_support = land & (conv_score > 0)
    # Kinematic scores are propagated over their connected land support by a
    # shortest-path distance field. Scores decay only by rank ordering; no
    # physical width or fixed distance threshold is asserted.
    ext_seeds = {(int(r), int(c)): float(ext_score[r, c]) for r, c in zip(*np.where(ext_support))}
    conv_seeds = {(int(r), int(c)): float(conv_score[r, c]) for r, c in zip(*np.where(conv_support))}
    ext_distance, ext_strength = _distance_field(land, ext_seeds) if ext_seeds else (np.full((ROWS, COLS), np.inf), np.zeros((ROWS, COLS)))
    conv_distance, conv_strength = _distance_field(land, conv_seeds) if conv_seeds else (np.full((ROWS, COLS), np.inf), np.zeros((ROWS, COLS)))
    boundary_seeds = {**ext_seeds, **conv_seeds}
    quiet_distance, _ = _distance_field(land, boundary_seeds) if boundary_seeds else (np.zeros((ROWS, COLS)), np.zeros((ROWS, COLS)))

    # A ranked, spatially coherent T0 realization uses central values of the
    # soft area envelopes as target shares. Spherical area and stable cell-ID
    # tie breaks make membership deterministic.
    thermal_id = np.zeros((ROWS, COLS), dtype=np.uint8)
    thermal_id[ocean] = 0
    hot_share, cold_share = 0.10, 0.55
    land_flat = np.flatnonzero(land.ravel())
    areas = area.ravel()[land_flat]
    ext_distance_flat = ext_distance.ravel()[land_flat]
    ext_strength_flat = ext_strength.ravel()[land_flat]
    hot_rank = np.lexsort((land_flat, ext_distance_flat, -ext_strength_flat))
    hot_target = hot_share * cont_area
    hot_selected = np.zeros(len(land_flat), dtype=bool)
    hot_selected[hot_rank] = True
    cumulative = np.cumsum(areas[hot_rank])
    hot_count = int(np.searchsorted(cumulative, hot_target, side="left") + 1)
    hot_selected[:] = False
    hot_selected[hot_rank[:hot_count]] = True

    remaining = np.flatnonzero(~hot_selected)
    quiet_flat = quiet_distance.ravel()[land_flat[remaining]]
    cold_rank_local = np.lexsort((land_flat[remaining], -quiet_flat))
    cold_target = cold_share * cont_area
    cold_count = int(np.searchsorted(np.cumsum(areas[remaining][cold_rank_local]), cold_target, side="left") + 1)
    cold_selected = np.zeros(len(land_flat), dtype=bool)
    cold_selected[remaining[cold_rank_local[:cold_count]]] = True
    thermal_id.ravel()[land_flat[hot_selected]] = THERMAL_IDS["HOT_EXTENDED"]
    thermal_id.ravel()[land_flat[cold_selected]] = THERMAL_IDS["COLD_STABLE"]
    thermal_id.ravel()[land_flat[~hot_selected & ~cold_selected]] = THERMAL_IDS["NORMAL"]

    # Physical crust classes use coastline transition support, boundary demand,
    # and the coherent stable/hot ranking. Province/suture design tags are not read.
    crust_id = np.zeros((ROWS, COLS), dtype=np.uint8)
    crust_id[ocean] = DOMAIN_IDS["NORMAL_OCEANIC"]
    coast = geography["coastline_mask"].astype(bool)
    transition = land & coast & plate_boundary_support
    crust_id[transition] = DOMAIN_IDS["TRANSITIONAL_MARGIN"]
    interior = land & ~transition
    ext_cont = interior & (thermal_id == THERMAL_IDS["HOT_EXTENDED"])
    orogenic = interior & ~ext_cont & (conv_score > ext_score) & (conv_score > 0)
    stable = interior & ~ext_cont & ~orogenic & (thermal_id == THERMAL_IDS["COLD_STABLE"])
    crust_id[ext_cont] = DOMAIN_IDS["EXTENDED_CONTINENTAL"]
    crust_id[orogenic] = DOMAIN_IDS["OROGENIC_THICKENED"]
    crust_id[stable] = DOMAIN_IDS["STABLE_CONTINENTAL"]
    crust_id[interior & (crust_id == 0)] = DOMAIN_IDS["NORMAL_CONTINENTAL"]
    thickness = np.zeros((ROWS, COLS), dtype=np.float64)
    for domain_id, value in THICKNESS_KM.items():
        thickness[crust_id == domain_id] = value * 1000.0
    if np.any(crust_id == 0) or np.any(thickness <= 0):
        raise ValueError("crust domain/thickness coverage is incomplete")

    heat_flow = np.full((ROWS, COLS), np.nan, dtype=np.float64)
    lithosphere_thickness = np.full((ROWS, COLS), np.nan, dtype=np.float64)
    for thermal, q in HEAT_FLOW_MW_M2.items():
        mask = land & (thermal_id == thermal)
        heat_flow[mask] = q * 1e-3
        lithosphere_thickness[mask] = LITHOSPHERE_KM[thermal] * 1000.0
    residual, residual_evidence = _low_frequency_residual(ocean, area)
    elevation_land = geography["land_surface_elevation_m"].astype(np.float64)
    total_elevation = np.full((ROWS, COLS), np.nan, dtype=np.float64)
    total_elevation[land] = elevation_land[land]
    # The age-derived ocean thermal/isostatic depth remains pending, so residual
    # bathymetry is kept as its own authored component and never mislabeled total.

    fields = {
        "oceanic_lithosphere_age_ma": age,
        "ocean_surface_authorial_residual_m": residual,
        "physical_crust_domain_id": crust_id,
        "crustal_thickness_m": thickness,
        "continental_thermal_domain_id": thermal_id,
        "continental_reference_surface_heat_flow_w_m2": heat_flow,
        "continental_reference_lithosphere_thickness_m": lithosphere_thickness,
        "canonical_land_surface_elevation_m": total_elevation,
        "unknown_total_ocean_elevation_mask": ocean.copy(),
    }
    field_path = root / "R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz"
    field_sha = _write_deterministic_npz(field_path, fields)
    field_hashes = {name: _array_sha256(value) for name, value in fields.items()}
    domain_counts = {name: int(np.count_nonzero(crust_id == code)) for name, code in DOMAIN_IDS.items()}
    thermal_area = {name: float(area[land & (thermal_id == code)].sum() / cont_area)
                    for name, code in THERMAL_IDS.items()}
    pending = [
        "ocean thermal profile and age-derived heat flow",
        "ocean thermal lithosphere thickness",
        "thermal/isostatic ocean bathymetry component and complete ocean surface",
        "continental geotherm profiles and model-derived heat flow beyond ratified references",
        "chemical density anomaly",
        "cooling curvature",
    ]
    manifest = {
        "schema": "R6_T0_B_PANGAEA_LIKE_V2_REALIZATION_MANIFEST_V1",
        "authorial_realization_id": REALIZATION_ID,
        "authorial_status": "RATIFIED_FOR_T0_MATERIALIZATION",
        "canonical_status": "CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION",
        "canonical_parent_hashes": {"physical_geography": geo_sha, "vector_partition": vector_sha,
                                    "kinematics": KIN_SHA},
        "mesh_hash": MESH_SHA,
        "field_package_path": field_path.name,
        "field_package_sha256": field_sha,
        "normalized_field_hashes": field_hashes,
        "derived_fields": {
            "crust_domains_and_thickness": {"status": "MATERIALIZED", "domain_ids": DOMAIN_IDS,
                                             "thickness_m": {str(k): v for k, v in THICKNESS_KM.items()}},
            "continental_thermal_reference_state": {"status": "MATERIALIZED", "domain_ids": THERMAL_IDS,
                "area_fraction": thermal_area, "heat_flow_w_m2": {str(k): v * 1e-3 for k, v in HEAT_FLOW_MW_M2.items()},
                "lithosphere_thickness_m": {str(k): v * 1000 for k, v in LITHOSPHERE_KM.items()}},
            "oceanic_age": {"status": "MATERIALIZED", **age_evidence},
            "ocean_authorial_residual_bathymetry": {"status": "MATERIALIZED_COMPONENT_ONLY", **residual_evidence},
            "total_surface_elevation": {"status": "PENDING_SPECIALIST_RUNTIME", "land_support_retained": True,
                                         "ocean_thermal_isostatic_component_missing": True},
        },
        "kinematic_support": {
            "convergent_boundary_demand_segments": kin["normal_sign_counts"]["CONVERGENT"],
            "divergent_boundary_demand_segments": kin["normal_sign_counts"]["DIVERGENT"],
            "boundary_process_classes_assigned": False,
            "selected_spreading_source_segments": len(selected_source_ids),
            "selected_spreading_source_branch": selected_branch_id,
        },
        "physical_crust_domain_counts_cells": domain_counts,
        "thermal_domain_area_fractions": thermal_area,
        "materialized_physical_field_families": 7,
        "pending_specialist_fields": pending,
        "reference_physical_parameters": {"families": 11, "canonical_values": {"gravity_m_s2": 9.82, "radius_m": 6371000},
            "resolved": 2, "candidate_configurations": 0, "unselected": 9},
        "rheology": {"parameter_families": 13, "candidate_configurations": 0,
                      "status": "UNSELECTED_MODEL_CONFIGURATION; NUMERIC_PARENT_RANGES_NOT_AVAILABLE"},
        "feg": {"mesh_sha256": MESH_SHA, "node_count": 64442, "triangle_count": 128880,
                "pre_orbdata_generated": False,
                "status": "PENDING_COMPLETE_OCEAN_ELEVATION_AND_GLOBAL_HEAT_FLOW"},
        "runtime_manifest": {"template": "R6_SHELLSET_T0_RUNTIME_INPUT_MANIFEST_TEMPLATE.json",
                             "candidate_status": "INCOMPLETE_TEMPLATE; runtime_authorized=false"},
        "governance": {"earth_geometry_imported": False, "canonical_payload_mutated": False,
                       "canonical_t0_promoted": False, "shellset_mechanics_executed": False,
                       "orbdata_executed": False, "forward_evolution_executed": False,
                       "dt_or_t1_created": False},
    }
    manifest["realization_manifest_sha256"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return manifest
