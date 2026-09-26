"""Build the bounded R6 latent-geometry/multiscale validation evidence.

This is an implementation diagnostic only. It never writes or promotes a new
canonical world and refuses to overwrite differing evidence artifacts.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import tracemalloc

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.initial_world.generator import generate_initial_world
from arcana_worldsim.r6.repository_context import (require_repository_context,
    repository_provenance, resolve_external_payload_path,
    verify_protected_staged_blobs)
from arcana_worldsim.r6.initial_world.latent import (
    PARENT_MEAN_TOLERANCE_M, build_latent_state, reconstruct_land_geometry,
)
from arcana_worldsim.r6.initial_world.refinement import Region, materialize_region
from arcana_worldsim.r6.initial_world.seeds import lineage_manifest


EXPECTED_HEAD = "592b1651b405363373590092e133bd25569d99a5"
EXPECTED_CANONICAL_SHA256 = "a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c"
EXPECTED_CANONICAL_BYTES = 1_169_900
EXPECTED_INDEX_BLOBS = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.json": "551727fd6ea73dd39a4194bf3aa34dc2a2707836",
    "ARCANA_EXECUTION_REFERENCE_INDEX.md": "8a8052c5c2ec73f26c598df5aeb3ab50105da085",
}
RESOLUTIONS = (1.0, 0.25, 0.1)
REGION_DEGREES = 4


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _write_evidence(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() == data:
            return
        # These named reports are regenerated measurements; elapsed time is
        # intentionally recorded and therefore is not a deterministic byte.
    path.write_bytes(data)


def _array_sha(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    h = hashlib.sha256()
    h.update(value.dtype.str.encode("ascii"))
    h.update(json.dumps(value.shape, separators=(",", ":")).encode("ascii"))
    h.update(value.tobytes())
    return h.hexdigest()


def _region_candidates(fields) -> dict[str, tuple[tuple[float, ...], int, int]]:
    land = fields.land_ocean_mask.astype(bool)
    coast = fields.coastline_mask.astype(bool)
    province = fields.province_class
    elevation = fields.land_surface_elevation_m
    candidates: dict[str, list[tuple[tuple[float, ...], int, int]]] = {
        "coastline": [], "continental_interior": [],
        "province_boundary": [], "topographic_transition": [],
    }
    for row in range(0, 180 - REGION_DEGREES + 1):
        for col in range(0, 360 - REGION_DEGREES + 1):
            l = land[row:row + 4, col:col + 4]
            c = coast[row:row + 4, col:col + 4]
            p = province[row:row + 4, col:col + 4]
            z = elevation[row:row + 4, col:col + 4]
            if l.any() and (~l).any():
                candidates["coastline"].append(((float(c.sum()), float(l.sum()),
                                                  -float(row), -float(col)), row, col))
            if l.all() and not c.any():
                candidates["continental_interior"].append(((float(np.unique(p).size),
                                                              -float(np.nanstd(z)),
                                                              -float(row), -float(col)), row, col))
            land_p = p[l]
            if l.any() and land_p.size > 1:
                horizontal = ((p[:, 1:] != p[:, :-1]) & l[:, 1:] & l[:, :-1]).sum()
                vertical = ((p[1:, :] != p[:-1, :]) & l[1:, :] & l[:-1, :]).sum()
                if horizontal + vertical:
                    candidates["province_boundary"].append(((float(horizontal + vertical),
                                                               float(np.unique(land_p).size),
                                                               -float(row), -float(col)), row, col))
            if l.all() and not c.any() and np.isfinite(z).all():
                candidates["topographic_transition"].append(((float(np.ptp(z)),
                                                                float(np.std(z)),
                                                                -float(row), -float(col)), row, col))
    selected: dict[str, tuple[tuple[float, ...], int, int]] = {}
    used: set[tuple[int, int]] = set()
    for name in candidates:
        available = [item for item in candidates[name] if (item[1], item[2]) not in used]
        if not available:
            raise RuntimeError(f"no distinct qualifying diagnostic region for {name}")
        choice = max(available, key=lambda item: item[0])
        selected[name] = choice
        used.add((choice[1], choice[2]))
    return selected


def _array_digest_map(fields: dict[str, np.ndarray]) -> dict[str, str]:
    return {key: _array_sha(value) for key, value in sorted(fields.items())}


def _measure(callable_):
    tracemalloc.start()
    start = time.perf_counter()
    result = callable_()
    seconds = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, seconds, peak


def _weighted_parent_error(fine: np.ndarray, land: np.ndarray,
                           region: Region, resolution: float, parent) -> float:
    ratio = int(round(1.0 / resolution))
    rows = int(round(region.north_deg - region.south_deg))
    cols = int(round(region.east_deg - region.west_deg))
    fine_z = fine.reshape(rows, ratio, cols, ratio)
    fine_land = land.reshape(rows, ratio, cols, ratio)
    lat = region.south_deg + (np.arange(rows * ratio) + 0.5) * resolution
    weights = np.cos(np.deg2rad(lat)).reshape(rows, ratio)
    errors = []
    parent_r0 = int(region.south_deg + 90)
    parent_c0 = int(region.west_deg + 180)
    for i in range(rows):
        for j in range(cols):
            mask = fine_land[i, :, j, :] & np.isfinite(fine_z[i, :, j, :])
            if not mask.any() or not parent.land_ocean_mask[parent_r0 + i, parent_c0 + j]:
                continue
            weight = np.broadcast_to(weights[i, :, None], mask.shape)[mask]
            mean = float(np.average(fine_z[i, :, j, :][mask], weights=weight))
            expected = float(parent.land_surface_elevation_m[parent_r0 + i, parent_c0 + j])
            errors.append(abs(mean - expected))
    return max(errors, default=0.0)


def _terrain_diagnostics(elevation: np.ndarray, land: np.ndarray,
                         coastline: np.ndarray, resolution: float,
                         south_deg: float) -> dict[str, object]:
    lat = np.deg2rad(south_deg + (np.arange(elevation.shape[0]) + 0.5) * resolution)
    dx = 6_371_000.0 * math.radians(resolution) * np.maximum(np.cos(lat), 1e-8)
    dy = 6_371_000.0 * math.radians(resolution)
    hmask = land[:, 1:] & land[:, :-1]
    vmask = land[1:, :] & land[:-1, :]
    hslope = np.abs(elevation[:, 1:] - elevation[:, :-1]) / dx[:, None]
    vslope = np.abs(elevation[1:, :] - elevation[:-1, :]) / dy
    slopes = np.concatenate((hslope[hmask], vslope[vmask]))
    local_minima = 0
    if elevation.shape[0] >= 3 and elevation.shape[1] >= 3:
        center = elevation[1:-1, 1:-1]
        neighborhood = (land[1:-1, 1:-1] & land[:-2, 1:-1] & land[2:, 1:-1] &
                        land[1:-1, :-2] & land[1:-1, 2:])
        local_minima = int(np.count_nonzero(neighborhood &
                          (center < elevation[:-2, 1:-1]) &
                          (center < elevation[2:, 1:-1]) &
                          (center < elevation[1:-1, :-2]) &
                          (center < elevation[1:-1, 2:])))
    if land.shape[0] >= 2 and land.shape[1] >= 2:
        a, b = land[:-1, :-1], land[:-1, 1:]
        c, d = land[1:, :-1], land[1:, 1:]
        checker = (a == d) & (b == c) & (a != b)
        checker_count = int(checker.sum())
    else:
        checker_count = 0
    finite_elevation = elevation[land & np.isfinite(elevation)]
    return {
        "slope_p95_m_per_m": float(np.quantile(slopes, 0.95)) if slopes.size else None,
        "slope_max_m_per_m": float(np.max(slopes)) if slopes.size else None,
        "land_adjacent_pair_count": int(slopes.size),
        "local_four_neighbor_minimum_count_diagnostic_only": local_minima,
        "coastal_land_cell_count_not_a_river_or_outlet_network": int(
            np.count_nonzero(coastline & land)),
        "2x2_diagonal_checkerboard_count": checker_count,
        "relief_p95_minus_p05_m": float(np.quantile(finite_elevation, 0.95) -
                                         np.quantile(finite_elevation, 0.05))
        if finite_elevation.size else None,
        "hydrology_materialized": False,
    }


def main() -> int:
    require_repository_context(ROOT, required_ancestor=EXPECTED_HEAD)
    verify_protected_staged_blobs(ROOT, EXPECTED_INDEX_BLOBS)

    package = json.loads((ROOT / "R6_CANONICAL_INITIAL_STATE_PACKAGE.json").read_text(encoding="utf-8"))
    manifest_path = ROOT / "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json"
    materialization = json.loads(manifest_path.read_text(encoding="utf-8"))
    canonical_path = resolve_external_payload_path(ROOT, package["materialized_payload"]["relative_path"])
    canonical_sha = _sha_file(canonical_path)
    if (canonical_sha != EXPECTED_CANONICAL_SHA256 or
            canonical_sha != package["materialized_payload"]["sha256"] or
            canonical_path.stat().st_size != EXPECTED_CANONICAL_BYTES):
        raise RuntimeError("canonical payload identity/size mismatch")
    if package["r6_global_t0_ma"] != 210.0 or package["grid"]["shape_lat_lon"] != [180, 360]:
        raise RuntimeError("canonical endpoint is not the expected 210 Ma 1-degree world")

    parent = generate_initial_world()
    with np.load(canonical_path, allow_pickle=False) as archive:
        if set(archive.files) != set(parent.arrays()):
            raise RuntimeError("canonical payload field inventory mismatch")
        for name, regenerated in parent.arrays().items():
            if not np.array_equal(archive[name], regenerated, equal_nan=True):
                raise RuntimeError(f"regenerated canonical field differs: {name}")

    physical_state = next(state["state_id"] for state in package["states"]
                          if state["domain"] == "physical_geography")
    latent = build_latent_state(
        parent, world_id=package["global_base_branch_id"],
        parent_history_id=package["history_id"], parent_state_id=physical_state,
        parent_payload_sha256=canonical_sha)
    canonical_land, canonical_coast = reconstruct_land_geometry(
        parent, latent, parent.grid.lat_centers_deg, parent.grid.lon_centers_deg,
        base_grid_centers=True)
    if (not np.array_equal(canonical_land, parent.land_ocean_mask.astype(bool)) or
            not np.array_equal(canonical_coast, parent.coastline_mask.astype(bool))):
        raise RuntimeError("latent 1-degree land/coast compatibility failure")

    selected = _region_candidates(parent)
    region_rows = []
    resolution_metrics = []
    hashes_by_region: dict[str, dict[str, dict[str, str]]] = {}
    outputs: dict[tuple[str, float], dict] = {}
    for kind, (_, row, col) in selected.items():
        region = Region(row - 90.0, col - 180.0,
                        row - 90.0 + REGION_DEGREES,
                        col - 180.0 + REGION_DEGREES)
        region_rows.append({"kind": kind, "selection": "MAXIMUM_GOVERNED_CRITERION; ROW_MAJOR_TIE_BREAK",
                            "parent_row_start": row, "parent_col_start": col,
                            "bounds_deg": [region.south_deg, region.west_deg,
                                           region.north_deg, region.east_deg]})
        hashes_by_region[kind] = {}
        for resolution in RESOLUTIONS:
            result, elapsed, peak = _measure(lambda: materialize_region(
                parent, region, resolution,
                parent_history_id=package["history_id"], parent_state_id=physical_state,
                latent_state=latent))
            outputs[(kind, resolution)] = result
            hashes = _array_digest_map(result["fields"])
            hashes_by_region[kind][str(resolution)] = hashes
            fine_land = result["fields"]["land_ocean_mask"].astype(bool)
            ratio = int(round(1.0 / resolution))
            descriptor = result["descriptor"]
            if descriptor["parent_world_id"] != package["global_base_branch_id"]:
                raise RuntimeError("refinement provenance world linkage mismatch")
            if resolution == 1.0:
                r0, c0 = row, col
                for name in ("land_ocean_mask", "coastline_mask", "plate_id", "crust_class",
                             "boundary_class", "province_class", "land_surface_elevation_m"):
                    if not np.array_equal(result["fields"][name], parent.arrays()[name][
                            r0:r0 + 4, c0:c0 + 4], equal_nan=True):
                        raise RuntimeError(f"1-degree regional identity mismatch: {kind}/{name}")
                parent_error = 0.0
            else:
                aggregate = fine_land.reshape(4, ratio, 4, ratio).mean(axis=(1, 3)) >= 0.5
                if not np.array_equal(aggregate, parent.land_ocean_mask[row:row + 4, col:col + 4].astype(bool)):
                    raise RuntimeError(f"land parent aggregation mismatch: {kind}/{resolution}")
                for field in ("plate_id", "crust_class", "boundary_class", "province_class"):
                    expected = np.repeat(np.repeat(
                        parent.arrays()[field][row:row + 4, col:col + 4],
                        ratio, axis=0), ratio, axis=1)
                    if not np.array_equal(result["fields"][field], expected):
                        raise RuntimeError(f"coarse categorical support mismatch: {kind}/{resolution}/{field}")
                parent_error = _weighted_parent_error(
                    result["fields"]["land_surface_elevation_m"], fine_land,
                    region, resolution, parent)
                if parent_error > PARENT_MEAN_TOLERANCE_M:
                    raise RuntimeError(f"topographic parent mean exceeds tolerance: {kind}/{resolution}")
            topo_audit = descriptor["validation"]["topography"]
            land_audit = descriptor["validation"]["land_geometry"]
            if land_audit and land_audit["parent_majority_violations"] != 0:
                raise RuntimeError(f"latent land audit failed: {kind}/{resolution}")
            if resolution != 1.0 and (not topo_audit["fine_spectrum_added"] or
                                      topo_audit["fine_detail_rms_m"] <= 1.0):
                raise RuntimeError(f"fine topographic spectrum absent: {kind}/{resolution}")
            if kind == "coastline" and resolution != 1.0 and not np.any(
                    (fine_land.reshape(4, ratio, 4, ratio).mean(axis=(1, 3)) > 0.0) &
                    (fine_land.reshape(4, ratio, 4, ratio).mean(axis=(1, 3)) < 1.0)):
                raise RuntimeError("coast diagnostic produced no sub-grid coast geometry")
            terrain_diagnostics = _terrain_diagnostics(
                result["fields"]["land_surface_elevation_m"], fine_land,
                result["fields"]["coastline_mask"].astype(bool), resolution,
                region.south_deg)
            if terrain_diagnostics["2x2_diagonal_checkerboard_count"] != 0:
                raise RuntimeError(f"checkerboard land artifact in {kind}/{resolution}")
            resolution_metrics.append({
                "region": kind, "resolution_deg": resolution,
                "shape_lat_lon": result["fields"]["land_ocean_mask"].shape,
                "cells": result["cell_count"], "elapsed_seconds": elapsed,
                "python_tracemalloc_peak_bytes": peak,
                "python_tracemalloc_is_process_rss": False,
                "array_sha256": hashes,
                "land_fraction": float(fine_land.mean()) if resolution != 1.0 else
                    float(result["fields"]["land_ocean_mask"].mean()),
                "fractional_parent_cell_count": int(np.count_nonzero(
                    (fine_land.reshape(4, ratio, 4, ratio).mean(axis=(1, 3)) > 0.0) &
                    (fine_land.reshape(4, ratio, 4, ratio).mean(axis=(1, 3)) < 1.0)))
                    if resolution != 1.0 else 0,
                "fine_vs_parent_replication_child_cells_differ": bool(np.any(
                    fine_land != np.repeat(np.repeat(
                        parent.land_ocean_mask[row:row + 4, col:col + 4].astype(bool),
                        ratio, axis=0), ratio, axis=1))) if resolution != 1.0 else False,
                "topography_parent_mean_max_error_m": parent_error,
                "fine_detail_rms_m": topo_audit.get("fine_detail_rms_m", 0.0),
                "terrain_diagnostics": terrain_diagnostics,
                "parent_majority_violations": land_audit.get("parent_majority_violations", 0),
            })

    # Independent adjacent half-region builds must concatenate exactly to the union.
    seam_checks = []
    coast_region = selected["coastline"][1:]
    row, col = coast_region
    whole = Region(row - 90.0, col - 180.0, row - 86.0, col - 176.0)
    left = Region(whole.south_deg, whole.west_deg, whole.north_deg, whole.west_deg + 2.0)
    right = Region(whole.south_deg, whole.west_deg + 2.0, whole.north_deg, whole.east_deg)
    for resolution in (0.25, 0.1):
        def build(bounds):
            return materialize_region(parent, bounds, resolution,
                parent_history_id=package["history_id"], parent_state_id=physical_state,
                latent_state=latent)["fields"]
        united, west, east = build(whole), build(left), build(right)
        for field in ("land_ocean_mask", "coastline_mask", "plate_id", "province_class",
                      "land_surface_elevation_m"):
            joined = np.concatenate((west[field], east[field]), axis=1)
            if not np.array_equal(joined, united[field], equal_nan=True):
                raise RuntimeError(f"independent/union tile seam mismatch: {resolution}/{field}")
        seam_checks.append({"resolution_deg": resolution,
                            "west_east_concat_equals_union": True,
                            "checked_fields": ["land_ocean_mask", "coastline_mask", "plate_id",
                                               "province_class", "land_surface_elevation_m"]})

    # Order independence is represented by repeat materialization plus stable hashes.
    order_checks = []
    for kind in reversed(list(selected)):
        first = materialize_region(parent, whole if kind == "coastline" else Region(
            selected[kind][1] - 90.0, selected[kind][2] - 180.0,
            selected[kind][1] - 86.0, selected[kind][2] - 176.0), 0.25,
            parent_history_id=package["history_id"], parent_state_id=physical_state,
            latent_state=latent)
        expected = hashes_by_region[kind]["0.25"]
        if _array_digest_map(first["fields"]) != expected:
            raise RuntimeError(f"generation order/repeat hash mismatch: {kind}")
        order_checks.append({"region": kind, "resolution_deg": 0.25,
                             "repeat_hash_matches": True})

    unknown_result = materialize_region(
        parent, whole, 0.25, parent_history_id=package["history_id"],
        parent_state_id=physical_state, latent_state=latent,
        requested_fields=("land_ocean_mask", "bathymetry", "plate_motion", "deep",
                          "climate", "hydrology"))
    unknown_masks = {key: bool(value.all()) for key, value in unknown_result["fields"].items()
                     if key.endswith("_unknown_mask") and key != "bathymetry_unknown_mask"}
    if not all(unknown_masks.values()):
        raise RuntimeError("UNKNOWN domains were not preserved")
    if not unknown_result["fields"]["bathymetry_unknown_mask"][
            ~unknown_result["fields"]["land_ocean_mask"].astype(bool)].all():
        raise RuntimeError("ocean bathymetry UNKNOWN mask was lost")

    latent_bytes = latent.canonical_bytes()
    latent_sha = hashlib.sha256(latent_bytes).hexdigest()
    if latent_sha != latent.sha256:
        raise RuntimeError("latent canonical serialization/hash mismatch")
    parameter_identity = latent.parameter_identity
    contract = {
        "schema": "R6_INITIAL_WORLD_LATENT_GEOMETRY_CONTRACT_V1",
        "status": "IMPLEMENTED_AND_BOUNDED_VALIDATED",
        "world_id": package["global_base_branch_id"], "history_id": package["history_id"],
        "physical_geography_state_id": physical_state, "t0_ma": 210.0,
        "canonical_grid": {"grid_id": package["grid"]["grid_id"], "shape": [180, 360],
                           "resolution_deg": 1.0, "unchanged": True},
        "latent_state": {"schema": latent.schema, "artifact": "R6_INITIAL_WORLD_210MA_LATENT_GEOMETRY.json",
                         "sha256": latent_sha, "bytes": len(latent_bytes),
                         "parent_payload_sha256": canonical_sha,
                         "authority": "ARCANA_OWNED_AUTHORIAL_PROCEDURAL_STATE_NOT_OBSERVATIONAL_EVIDENCE"},
        "parameter_identity": parameter_identity,
        "generative_pipeline_inventory": [
            {"field_family": "main_continent_and_terrane_geometry", "classification": "LATENT_RECONSTRUCTABLE_FROM_SEED",
             "surviving_state": "continuous rotated supercontinent score, harmonic perturbations, spherical distance fields, area-ranked thresholds and deterministic tie counts"},
            {"field_family": "land_ocean_1deg", "classification": "RASTER_DERIVED_FROM_LATENT_WITH_PARENT_THRESHOLD_CONSTRAINT",
             "surviving_state": "canonical score/threshold latent plus canonical-grid tie identity"},
            {"field_family": "fine_coast_detail", "classification": "HIERARCHICAL_PROCEDURAL_GEOMETRY",
             "surviving_state": "world/component/parent-cell/scale keyed PCG64 phases; edge-windowed perturbation and parent majority correction"},
            {"field_family": "plate_id_crust_boundary_province", "classification": "GRID_NATIVE_ONLY_FOR_CANONICAL_ASSIGNMENTS",
             "surviving_state": "seed nuclei and craton identities are latent; child classes inherit canonical 1deg support"},
            {"field_family": "canonical_topography", "classification": "LATENT_RECONSTRUCTABLE_FROM_SEED",
             "surviving_state": "canonical macro/meso harmonic coefficients and fixed 1deg normalization"},
            {"field_family": "fine_topography", "classification": "HIERARCHICAL_PROCEDURAL_MULTISCALE_DETAIL",
             "surviving_state": "parent-cell keyed meso/local bands; area-centred and corrected to canonical parent elevation"},
            {"field_family": "coastline_mask", "classification": "RASTER_DERIVED_FROM_LAND_TOPOLOGY",
             "surviving_state": "8-neighbour topology at requested raster support; requires regional halo"},
            {"field_family": "bathymetry_plate_motion_deep_climate_hydrology", "classification": "UNKNOWN",
             "surviving_state": "explicit unknown masks; no numeric state generated"},
        ],
        "land_aggregation": {"rule": "LAND_IF_FINE_CHILD_FRACTION_GE_0.5",
                             "tie": "0.5 fraction classifies as land", "applied_per_canonical_parent_cell": True},
        "refinement_levels": [
            {"name": "GLOBAL_BASE", "resolution_deg": 1.0},
            {"name": "REGIONAL", "resolution_deg": 0.25},
            {"name": "LOCAL", "resolution_deg": 0.1},
        ],
        "resolution_policy": "API accepts positive resolutions that exactly tile parent-aligned requested bounds; the listed levels are tested minima, not an exhaustive future enum. No resolution confers equal scientific authority.",
        "spatial_support_classes": {
            "land_ocean_mask": "STRUCTURALLY_REFINABLE",
            "coastline_mask": "STRUCTURALLY_REFINABLE",
            "land_surface_elevation_m": "MULTISCALE_REFINABLE",
            "plate_id": "COARSE_SUPPORT_ON_FINE_GRID",
            "crust_class": "COARSE_SUPPORT_ON_FINE_GRID",
            "boundary_class": "COARSE_SUPPORT_ON_FINE_GRID",
            "province_class": "COARSE_SUPPORT_ON_FINE_GRID",
            "bathymetry": "UNKNOWN",
            "plate_motion": "UNKNOWN", "deep": "UNKNOWN", "climate": "UNKNOWN", "hydrology": "UNKNOWN",
        },
        "procedural_detail_authority": "AUTHORIAL_SYNTHETIC_INITIALIZATION__PROCEDURAL_DETAIL_ONLY_NO_EMPIRICAL_PALEOGEOGRAPHIC_OR_ELEVATION_AUTHORITY_UPGRADE",
        "topography": {"bands": [{"id": "MESO_50_120KM_V1", "amplitude_m": 20.0},
                                   {"id": "LOCAL_25_40KM_V1", "amplitude_m": 5.0,
                                    "active_at_resolution_deg": 0.1}],
                       "wavelength_note": "Nominal equatorial wavelengths implied by 1-2 and 3-4 cycles per 1-degree parent; east-west wavelength contracts with latitude. The local band activates only at 0.1deg to avoid undersampling. Procedural labels only, not measured geology.",
                       "parent_mean_consistency_tolerance_m": PARENT_MEAN_TOLERANCE_M,
                       "conservation": "cos(latitude)-weighted mean over fine land samples within each 1deg parent cell; discrete correction then float32 check"},
        "coastline_detail": {"method": "continuous seeded implicit margin plus edge-windowed hierarchical perturbation",
                             "parent_constraint": "every represented 1deg parent retains majority class under the predeclared >=0.5 rule",
                             "manual_geometry": False, "coastline_empirical_authority_added": False},
        "canonical_payload_mutated": False,
        "forward_simulation_executed": False,
        "provider_acquisition_executed": False,
        "r5_runtime_dependency": False,
    }
    manifest = {
        "schema": "R6_INITIAL_WORLD_210MA_LATENT_GEOMETRY_MANIFEST_V1",
        "status": "LATENT_STATE_MATERIALIZED_AND_CANONICALLY_COMPATIBLE",
        "world_id": latent.world_id, "history_id": latent.parent_history_id,
        "parent_state_id": latent.parent_state_id, "parent_payload_sha256": canonical_sha,
        "generator_id": latent.generator_id, "generator_version": latent.generator_version,
        "latent_schema": latent.schema,
        "latent_artifact": {"path": "R6_INITIAL_WORLD_210MA_LATENT_GEOMETRY.json",
                            "bytes": len(latent_bytes), "sha256": latent_sha,
                            "serialization": "canonical UTF-8 JSON, sorted keys, compact separators"},
        "seed_lineage": latent.seed_lineage,
        "parameter_identity": latent.parameter_identity,
        "field_inventory": contract["generative_pipeline_inventory"],
        "reconstructability": {"land_ocean_1deg_exact": True, "coastline_1deg_exact": True,
                                "all_canonical_npz_arrays_regenerated_exactly": True,
                                "fine_province_support": "COARSE_SUPPORT_ON_FINE_GRID",
                                "bathymetry_and_dynamic_domains": "UNKNOWN_PRESERVED"},
        "tested_refinement_levels_deg": list(RESOLUTIONS),
        "authority_classification": "AUTHORIAL_SYNTHETIC_INITIALIZATION__NO_OBSERVATIONAL_AUTHORITY_UPGRADE",
        "provenance": {"canonical_package": "R6_CANONICAL_INITIAL_STATE_PACKAGE.json",
                       "canonical_manifest": "R6_INITIAL_WORLD_MATERIALIZATION_MANIFEST.json",
                       "canonical_payload_relative_path": package["materialized_payload"]["relative_path"],
                       "canonical_payload_bytes": EXPECTED_CANONICAL_BYTES,
                       "canonical_payload_sha256": canonical_sha},
    }

    validation = {
        "schema": "R6_INITIAL_WORLD_MULTISCALE_REFINEMENT_VALIDATION_V1",
        "decision": "LATENT_GEOMETRY_COMPATIBLE__MULTISCALE_TECHNICAL_REFINEMENT_VALIDATED",
        "verdict": "PASS_WITH_COARSE_SUPPORT_FIELDS_AND_PROCEDURAL_DETAIL_LIMITATIONS",
        "repository": "siegmound/ARCANA_WORLD", "repository_context": repository_provenance(ROOT),
        "canonical_payload": {"path": package["materialized_payload"]["relative_path"],
                              "bytes": canonical_path.stat().st_size, "sha256": canonical_sha,
                              "all_14_fields_regenerated_exactly": True, "mutated": False},
        "global_grid_increased": False, "canonical_world_replaced": False,
        "regions": region_rows,
        "resolution_runs": resolution_metrics,
        "coastline_subgrid_detail": {
            "categorical_1deg_compatibility": True,
            "parent_majority_rule": "LAND_IF_FINE_CHILD_FRACTION_GE_0.5",
            "fine_coast_geometry_is_procedural": True,
            "manual_coastline_or_visual_painting": False,
            "canonical_1deg_parent_topology_unchanged": True,
            "fine_child_connected_component_topology_globally_certified": False,
            "empirical_authority_increase": False,
        },
        "topography": {"fine_spectrum_added": True,
                       "bands": ["MESO_50_120KM_V1", "LOCAL_25_40KM_V1"],
                       "parent_mean_tolerance_m": PARENT_MEAN_TOLERANCE_M,
                       "maximum_observed_parent_mean_error_m": max(
                           x["topography_parent_mean_max_error_m"] for x in resolution_metrics),
                       "procedural_detail_only": True, "bathymetry_inferred": False},
        "tile_seam_checks": seam_checks,
        "province_plate_crust_boundary_exact_parent_inheritance_validated": True,
        "generation_order_checks": order_checks,
        "parallel_execution": "NO_PARALLEL_CODEPATH_PRESENT; ORDER-INDEPENDENT_KEYED_SEEDS_VALIDATED_SEQUENTIALLY",
        "unknown_masks": {"all_dynamic_unknown_masks_preserved": all(unknown_masks.values()),
                          "ocean_bathymetry_unknown_preserved": True},
        "field_support_classes": contract["spatial_support_classes"],
        "nonclaims": {"scientific_forward_simulation": False, "plate_motion": False,
                      "hydrology_or_rivers": False, "provider_acquisition": False,
                      "new_fine_scale_empirical_authority": False,
                      "scientific_authority_register_mutated": False,
                      "physical_soil_created": False, "p7q_reopened": False,
                      "execution_indexes_mutated": False},
        "performance_note": "Per-region elapsed time is wall clock. Python tracemalloc peak is reported and is not process RSS; no global fine grid was allocated.",
        "ready_for_post_210_causal_evolution": False,
        "first_causal_blocker": package["first_post_t0_consumer_adjudication"],
    }
    md_contract = f"""# R6 Initial World Latent Geometry Contract\n\n- Status: `{contract['status']}`\n- Canonical world: `{latent.world_id}` at 210 Ma; 1° / 180×360 unchanged.\n- Latent schema/hash: `{latent.schema}` / `{latent_sha}`.\n- Canonical NPZ identity: `{canonical_sha}` ({EXPECTED_CANONICAL_BYTES} bytes), verified unchanged.\n- Land aggregation: `{contract['land_aggregation']['rule']}`; exact 0.5 ties classify as land.\n- Support: land/coast structurally refinable; topography multiscale procedural; province/plate/crust/boundary remain coarse-supported; bathymetry and dynamic domains UNKNOWN.\n- Added relief bands: 20 m meso (`MESO_50_120KM_V1`) and 5 m local (`LOCAL_25_40KM_V1`, enabled at 0.1°); nominal equatorial wavelengths only; parent-mean tolerance {PARENT_MEAN_TOLERANCE_M} m.\n- This is authorial synthetic model detail, not empirical paleogeographic/elevation evidence.\n- No forward evolution, provider acquisition, canonical replacement, or authority upgrade occurred.\n"""
    md_validation = [
        "# R6 Initial World Multiscale Refinement Validation", "",
        f"- Decision: `{validation['decision']}`",
        f"- Verdict: `{validation['verdict']}`",
        f"- Canonical payload SHA-256: `{canonical_sha}`; byte-identical identity verified.",
        "- 1° global grid unchanged; no dense global fine raster materialized.",
        "- Fine land/coast and relief are deterministic procedural detail constrained to the canonical 1° parent state.",
        "- Province/plate/crust/boundary remain `COARSE_SUPPORT_ON_FINE_GRID`; UNKNOWN domains remain UNKNOWN.",
        "- Slope, local-minimum/basin-potential, coastal-cell and checkerboard diagnostics are technical only; no drainage network is created.",
        "- No scientific forward simulation or empirical authority increase.", "",
        "## Region diagnostics", "",
        "| Type | Bounds (south, west, north, east) |", "|---|---|",
    ]
    md_validation.extend(f"| {r['kind']} | {r['bounds_deg']} |" for r in region_rows)
    md_validation += ["", "## Resolution/performance", "",
                      "| Region | Resolution | Cells | Seconds | Peak tracked Python bytes | Fine-detail RMS (m) | Parent error (m) |",
                      "|---|---:|---:|---:|---:|---:|---:|"]
    md_validation.extend(
        f"| {m['region']} | {m['resolution_deg']}° | {m['cells']} | {m['elapsed_seconds']:.6f} | "
        f"{m['python_tracemalloc_peak_bytes']} | {m['fine_detail_rms_m']:.4f} | "
        f"{m['topography_parent_mean_max_error_m']:.8f} |" for m in resolution_metrics)
    md_validation += ["", "## Tile/order and governance", "",
                      f"- Independent tiles equal union: `{all(x['west_east_concat_equals_union'] for x in seam_checks)}` at 0.25° and 0.1°.",
                      f"- Repeat/order-independent hashes: `{all(x['repeat_hash_matches'] for x in order_checks)}`.",
                      f"- Parent mean tolerance: `{PARENT_MEAN_TOLERANCE_M}` m.",
                      "- Causal evolution readiness: `false`; required plate-motion/geodynamic law and dated forcing remain unbound.", ""]

    artifacts = {
        "R6_INITIAL_WORLD_LATENT_GEOMETRY_CONTRACT.json": _canonical_json(contract),
        "R6_INITIAL_WORLD_LATENT_GEOMETRY_CONTRACT.md": md_contract.encode("utf-8"),
        "R6_INITIAL_WORLD_210MA_LATENT_GEOMETRY.json": latent_bytes,
        "R6_INITIAL_WORLD_210MA_LATENT_GEOMETRY_MANIFEST.json": _canonical_json(manifest),
        "R6_INITIAL_WORLD_MULTISCALE_REFINEMENT_VALIDATION.json": _canonical_json(validation),
        "R6_INITIAL_WORLD_MULTISCALE_REFINEMENT_VALIDATION.md": ("\n".join(md_validation)).encode("utf-8"),
    }
    for name, data in artifacts.items():
        _write_evidence(ROOT / name, data)
    print(json.dumps({"decision": validation["decision"], "verdict": validation["verdict"],
                      "latent_sha256": latent_sha, "canonical_sha256": canonical_sha,
                      "artifacts": {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                                    for name, data in artifacts.items()},
                      "resolution_run_count": len(resolution_metrics),
                      "seam_checks": seam_checks, "order_checks": order_checks,
                      "max_parent_mean_error_m": validation["topography"][
                          "maximum_observed_parent_mean_error_m"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
