"""Versioned, seed-reconstructable latent geometry for the R6 210 Ma world.

This is authorial procedural state, not paleogeographic observation.  The
canonical parent raster remains a compatibility constraint and support record;
continuous geometry is reconstructed from its original named RNG streams.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import cos, pi, sin
from typing import Any

import numpy as np

from .grid import GlobalGrid1Degree
from .model import InitialWorldFields
from .seeds import SEED_ROOT_MATERIAL, derive_seed_streams, lineage_manifest


LATENT_SCHEMA = "R6_INITIAL_GEOMETRY_LATENT_STATE_V1"
PARENT_MEAN_TOLERANCE_M = 0.05  # float32 output-rounding allowance after discrete conservation


@dataclass(frozen=True, slots=True)
class HarmonicTerm:
    longitude_wave: int
    latitude_wave: int
    longitude_phase_rad: float
    latitude_phase_rad: float
    sign: float
    boundary_extra_term: bool


@dataclass(frozen=True, slots=True)
class ThresholdRule:
    value: float
    equal_value_selected_count: int
    target_surface_fraction: float


@dataclass(frozen=True, slots=True)
class TerraneLatent:
    center_latitude_deg: float
    center_longitude_deg: float
    perturbation_phase_rad: float
    threshold: ThresholdRule


@dataclass(frozen=True, slots=True)
class R6InitialGeometryLatentState:
    schema: str
    world_id: str
    parent_history_id: str
    parent_state_id: str
    parent_payload_sha256: str
    generator_id: str
    generator_version: str
    seed_lineage: dict[str, Any]
    parameter_identity: dict[str, Any]
    geometry_center_latitude_deg: float
    geometry_center_longitude_deg: float
    geometry_orientation_radians: float
    coastline_terms: tuple[HarmonicTerm, ...]
    coastline_normalization: float
    main_land_threshold: ThresholdRule
    terranes: tuple[TerraneLatent, ...]
    plate_nuclei_lat_lon_deg: tuple[tuple[float, float], ...]
    craton_seed_cell_ids: tuple[str, ...]
    categorical_parent_support: str
    topography_terms_macro: tuple[HarmonicTerm, ...]
    topography_terms_meso: tuple[HarmonicTerm, ...]
    topography_macro_normalization: float
    topography_meso_normalization: float
    topography_process: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        obj = asdict(self)
        obj["coastline_terms"] = [asdict(t) for t in self.coastline_terms]
        obj["terranes"] = [
            {**asdict(t), "threshold": asdict(t.threshold)} for t in self.terranes]
        obj["main_land_threshold"] = asdict(self.main_land_threshold)
        obj["topography_terms_macro"] = [asdict(t) for t in self.topography_terms_macro]
        obj["topography_terms_meso"] = [asdict(t) for t in self.topography_terms_meso]
        return obj

    def canonical_bytes(self) -> bytes:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")

    @property
    def sha256(self) -> str:
        return sha256(self.canonical_bytes()).hexdigest()


def _score_threshold(score: np.ndarray, area: np.ndarray, target_fraction: float,
                     eligible: np.ndarray | None = None) -> ThresholdRule:
    valid = np.ones(score.shape, dtype=bool) if eligible is None else eligible
    indices = np.flatnonzero(valid)
    ordered = indices[np.argsort(-score.ravel()[indices], kind="stable")]
    cumulative = np.cumsum(area.ravel()[ordered], dtype=np.float64)
    target = target_fraction * float(area.sum())
    count = int(np.searchsorted(cumulative, target, side="left")) + 1
    threshold = float(score.ravel()[ordered[count - 1]])
    greater_count = int(np.count_nonzero(valid & (score > threshold)))
    return ThresholdRule(threshold, count - greater_count, target_fraction)


def _wrap_degrees(values: np.ndarray) -> np.ndarray:
    return (values + 180.0) % 360.0 - 180.0


def _distance_km(lat1: float, lon1: float, lat2: np.ndarray,
                 lon2: np.ndarray) -> np.ndarray:
    lat1r, lon1r = np.deg2rad(lat1), np.deg2rad(lon1)
    lat2r, lon2r = np.deg2rad(lat2), np.deg2rad(lon2)
    dlat = lat2r - lat1r
    dlon = (lon2r - lon1r + pi) % (2 * pi) - pi
    h = np.sin(dlat / 2) ** 2 + cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2) ** 2
    return 2 * 6_371_000.0 * np.arcsin(np.sqrt(np.clip(h, 0, 1))) / 1000.0


def _draw_boundary(rng: np.random.Generator) -> tuple[HarmonicTerm, ...]:
    terms = []
    for _ in range(8):
        m = int(rng.integers(1, 7))
        n = int(rng.integers(1, 5))
        p, q = rng.uniform(0, 2 * pi, size=2)
        extra = bool(rng.integers(0, 2))
        terms.append(HarmonicTerm(m, n, float(p), float(q), 1.0, extra))
    return tuple(terms)


def _draw_relief_terms(rng: np.random.Generator, count: int, max_lon: int,
                       max_lat: int) -> tuple[HarmonicTerm, ...]:
    terms = []
    for _ in range(count):
        m = int(rng.integers(1, max_lon + 1))
        n = int(rng.integers(1, max_lat + 1))
        p, q = rng.uniform(0, 2 * pi, size=2)
        sign = -1.0 if rng.integers(0, 2) else 1.0
        terms.append(HarmonicTerm(m, n, float(p), float(q), sign, False))
    return tuple(terms)


def _boundary_field_raw(lat: np.ndarray, lon: np.ndarray,
                        terms: tuple[HarmonicTerm, ...]) -> np.ndarray:
    latr = np.deg2rad(lat)[:, None]
    lonr = np.deg2rad(lon)[None, :]
    out = np.zeros((len(lat), len(lon)), dtype=np.float64)
    for t in terms:
        trig = np.sin(t.longitude_wave * lonr + t.longitude_phase_rad) * np.cos(
            t.latitude_wave * latr + t.latitude_phase_rad)
        if t.boundary_extra_term:
            trig += 0.5 * np.cos((t.longitude_wave + 1) * lonr - t.longitude_phase_rad) * np.sin(
                (t.latitude_wave + 1) * latr + t.latitude_phase_rad)
        out += t.sign * trig
    return out


def _boundary_field(lat: np.ndarray, lon: np.ndarray,
                    terms: tuple[HarmonicTerm, ...], normalization: float) -> np.ndarray:
    if not np.isfinite(normalization) or normalization <= 0:
        raise ValueError("invalid latent coastline normalization")
    return _boundary_field_raw(lat, lon, terms) / normalization


def _apply_threshold(score: np.ndarray, rule: ThresholdRule,
                     flat_index: np.ndarray, eligible: np.ndarray | None = None
                     ) -> np.ndarray:
    valid = np.ones(score.shape, dtype=bool) if eligible is None else eligible
    result = valid & (score > rule.value)
    tied = np.flatnonzero(valid & (score == rule.value))
    if rule.equal_value_selected_count:
        tied = tied[np.argsort(flat_index.ravel()[tied], kind="stable")]
        result.ravel()[tied[:rule.equal_value_selected_count]] = True
    return result


def reconstruct_land_geometry(parent: InitialWorldFields,
                              latent: R6InitialGeometryLatentState,
                              lat: np.ndarray, lon: np.ndarray,
                              *, base_grid_centers: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate seeded implicit land field; categorical ties retain parent order."""
    lat = np.asarray(lat, dtype=np.float64)
    lon = np.asarray(lon, dtype=np.float64)
    center_lat = latent.geometry_center_latitude_deg
    center_lon = latent.geometry_center_longitude_deg
    angle = latent.geometry_orientation_radians
    dlon = _wrap_degrees(lon[None, :] - center_lon) * cos(np.deg2rad(center_lat))
    dlat = lat[:, None] - center_lat
    x = dlon * cos(angle) + dlat * sin(angle)
    y = -dlon * sin(angle) + dlat * cos(angle)
    irregularity = _boundary_field(lat, lon, latent.coastline_terms,
                                   latent.coastline_normalization)
    score = 1.0 - np.sqrt((x / 108.0) ** 2 + (y / 52.0) ** 2) + 0.14 * irregularity
    if base_grid_centers:
        rr = np.rint(lat + 89.5).astype(np.int64)
        cc = np.rint(lon + 179.5).astype(np.int64)
        flat_index = rr[:, None] * parent.grid.nlon + cc[None, :]
    else:
        flat_index = np.arange(score.size, dtype=np.int64).reshape(score.shape)
    land = _apply_threshold(score, latent.main_land_threshold, flat_index)
    for index, terrane in enumerate(latent.terranes):
        distance = _distance_km(terrane.center_latitude_deg,
                                terrane.center_longitude_deg,
                                lat[:, None], lon[None, :])
        perturb = (0.035 * np.sin(np.deg2rad(lon[None, :] - terrane.center_longitude_deg) * 3 +
                                  terrane.perturbation_phase_rad) *
                   np.cos(np.deg2rad(lat[:, None] - terrane.center_latitude_deg) * 2 -
                          terrane.perturbation_phase_rad))
        island_score = -distance / 1100.0 + perturb
        land |= _apply_threshold(island_score, terrane.threshold, flat_index, ~land)
    coastline = np.zeros(land.shape, dtype=bool)
    # The caller may replace this with a supplied parent topology at fine
    # resolution; this native topology is for aligned 1-degree validation.
    for row, col in zip(*np.nonzero(land)):
        for dr in (-1, 0, 1):
            rr = row + dr
            if not 0 <= rr < land.shape[0]:
                continue
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                cc = (col + dc) % land.shape[1]
                if not land[rr, cc]:
                    coastline[row, col] = True
                    break
            if coastline[row, col]:
                break
    return land, coastline


def _continuous_land_margin(lat: np.ndarray, lon: np.ndarray,
                            latent: R6InitialGeometryLatentState) -> np.ndarray:
    lat = np.asarray(lat, dtype=np.float64)
    lon = np.asarray(lon, dtype=np.float64)
    dlon = _wrap_degrees(lon[None, :] - latent.geometry_center_longitude_deg) * cos(
        np.deg2rad(latent.geometry_center_latitude_deg))
    dlat = lat[:, None] - latent.geometry_center_latitude_deg
    angle = latent.geometry_orientation_radians
    x = dlon * cos(angle) + dlat * sin(angle)
    y = -dlon * sin(angle) + dlat * cos(angle)
    main = (1.0 - np.sqrt((x / 108.0) ** 2 + (y / 52.0) ** 2) +
            0.14 * _boundary_field(lat, lon, latent.coastline_terms,
                                   latent.coastline_normalization) -
            latent.main_land_threshold.value)
    margin = main
    for terrane in latent.terranes:
        distance = _distance_km(terrane.center_latitude_deg,
                                terrane.center_longitude_deg,
                                lat[:, None], lon[None, :])
        perturb = (0.035 * np.sin(np.deg2rad(lon[None, :] - terrane.center_longitude_deg) * 3 +
                                  terrane.perturbation_phase_rad) *
                   np.cos(np.deg2rad(lat[:, None] - terrane.center_latitude_deg) * 2 -
                          terrane.perturbation_phase_rad))
        margin = np.maximum(margin, -distance / 1100.0 + perturb - terrane.threshold.value)
    return margin


def _hierarchical_rng(latent: R6InitialGeometryLatentState, component: str,
                      row: int, col: int, level: str) -> np.random.Generator:
    material = (bytes.fromhex(latent.seed_lineage["root_digest_sha256"]) + b"\0" +
                latent.world_id.encode("utf-8") + b"\0" + component.encode("utf-8") +
                b"\0" + level.encode("utf-8") + b"\0" +
                f"R{row:03d}C{col:03d}".encode("ascii"))
    seed = int.from_bytes(sha256(material).digest()[:16], "big")
    return np.random.Generator(np.random.PCG64(seed))


def _windowed_noise(u: np.ndarray, v: np.ndarray, parameters: tuple[float, ...]
                    ) -> np.ndarray:
    kx, ky, px, py = parameters
    envelope = np.sin(pi * u) ** 2 * np.sin(pi * v) ** 2
    return envelope * np.sin(2 * pi * kx * u + px) * np.sin(2 * pi * ky * v + py)


def _fine_parameters(latent: R6InitialGeometryLatentState, row: int, col: int,
                     component: str) -> tuple[tuple[float, ...], tuple[float, ...]]:
    meso_rng = _hierarchical_rng(latent, component, row, col, "MESO_50_120KM_V1")
    local_rng = _hierarchical_rng(latent, component, row, col, "LOCAL_25_40KM_V1")
    meso = (float(meso_rng.uniform(1.0, 2.0)), float(meso_rng.uniform(1.0, 2.0)),
            float(meso_rng.uniform(0, 2*pi)), float(meso_rng.uniform(0, 2*pi)))
    local = (float(local_rng.uniform(3.0, 4.0)), float(local_rng.uniform(3.0, 4.0)),
             float(local_rng.uniform(0, 2*pi)), float(local_rng.uniform(0, 2*pi)))
    return meso, local


def _coastal_cell(parent: InitialWorldFields, row: int, col: int) -> bool:
    land = parent.land_ocean_mask.astype(bool)
    here = land[row, col]
    return any(land[rr, cc] != here for rr, cc in parent.grid.neighbors(row, col))


def _area_weights(latitudes: np.ndarray, quadrature_weights: np.ndarray) -> np.ndarray:
    return quadrature_weights[:, None] * np.cos(np.deg2rad(latitudes))[:, None] * quadrature_weights[None, :]


def _materialize_latent_land_core(parent: InitialWorldFields,
                                  latent: R6InitialGeometryLatentState,
                                  lat_centers: np.ndarray,
                                  lon_centers: np.ndarray,
                                  resolution_deg: float
                                  ) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Rasterize the continuous coastline field plus tile-stable coastal detail.

    Every fine parent cell is constrained to retain the canonical 1-degree
    land/ocean majority.  The added detail is procedural design texture only.
    """
    lat_centers = np.asarray(lat_centers, dtype=np.float64)
    lon_centers = np.asarray(lon_centers, dtype=np.float64)
    rows = np.clip(np.floor(lat_centers + 90).astype(np.int64), 0, 179)
    cols = np.clip(np.floor(lon_centers + 180).astype(np.int64), 0, 359)
    rr = np.broadcast_to(rows[:, None], (len(rows), len(cols)))
    cc = np.broadcast_to(cols[None, :], (len(rows), len(cols)))
    if resolution_deg == 1.0:
        land, _ = reconstruct_land_geometry(parent, latent, lat_centers, lon_centers,
                                            base_grid_centers=True)
        return land, _coastline_from_region(land, rows, cols, parent), {
            "subgrid_geometry_applied": False,
            "parent_majority_violations": 0,
            "detail_authority": "NONE_AT_GLOBAL_BASE",
        }
    margin = _continuous_land_margin(lat_centers, lon_centers, latent)
    detail_meso = np.zeros(margin.shape, dtype=np.float64)
    detail_local = np.zeros(margin.shape, dtype=np.float64)
    local_geometry_amplitude = 0.0005 if resolution_deg <= 0.1 + 1e-12 else 0.0
    coarse = parent.land_ocean_mask.astype(bool)
    qnodes, qweights = np.polynomial.legendre.leggauss(24)
    qnodes = (qnodes + 1.0) * 0.5
    qweights = qweights * 0.5
    diagnostics: dict[tuple[int, int], tuple[float, tuple[float, ...], tuple[float, ...]]] = {}
    for row, col in sorted(set(zip(rr.ravel().tolist(), cc.ravel().tolist()))):
        if not _coastal_cell(parent, row, col):
            continue
        meso_par, local_par = _fine_parameters(latent, row, col, "coastline")
        qlat = row - 90.0 + qnodes
        qlon = col - 180.0 + qnodes
        qmargin = _continuous_land_margin(qlat, qlon, latent)
        uu, vv = np.meshgrid(qnodes, qnodes, indexing="ij")
        qscore = (qmargin + 0.0015 * _windowed_noise(uu, vv, meso_par) +
                  local_geometry_amplitude * _windowed_noise(uu, vv, local_par))
        weights = _area_weights(qlat, qweights)
        weights = weights / weights.sum()
        base_land_fraction = float(weights[qscore >= 0].sum())
        target = (max(0.55, base_land_fraction) if coarse[row, col]
                  else min(0.45, base_land_fraction))
        window = np.sin(pi * uu) ** 2 * np.sin(pi * vv) ** 2
        low, high = -2.0, 2.0
        for _ in range(48):
            shift = (low + high) * 0.5
            fraction = float(weights[qscore + shift * window >= 0].sum())
            if fraction < target:
                low = shift
            else:
                high = shift
        diagnostics[(row, col)] = ((low + high) * 0.5, meso_par, local_par)
    for row, col in diagnostics:
        mask = (rr == row) & (cc == col)
        u = lat_centers[:, None] + 90.0 - row
        v = lon_centers[None, :] + 180.0 - col
        window = np.sin(pi * u) ** 2 * np.sin(pi * v) ** 2
        _, meso_par, local_par = diagnostics[(row, col)]
        detail_meso[mask] = (_windowed_noise(u, v, meso_par)[mask] * 0.0015)
        detail_local[mask] = (_windowed_noise(u, v, local_par)[mask] *
                              local_geometry_amplitude)
        # The shift is a support constraint, tapered to zero at parent edges.
        margin[mask] += diagnostics[(row, col)][0] * window[mask]
    fine_score = margin + detail_meso + detail_local
    support_corrections = 0
    # Enforce the predeclared categorical aggregation rule exactly on the
    # requested children. The correction is a smooth, edge-zero parent support
    # constraint, not a hand-authored coastline or a new category threshold.
    for row, col in sorted(set(zip(rr.ravel().tolist(), cc.ravel().tolist()))):
        mask = (rr == row) & (cc == col)
        parent_land = coarse[row, col]
        values = fine_score[mask].copy()
        u = lat_centers[:, None] + 90.0 - row
        v = lon_centers[None, :] + 180.0 - col
        window = (np.sin(pi * u) ** 2 * np.sin(pi * v) ** 2)[mask]
        needed = int((values >= 0).sum())
        required = (values.size + 1) // 2
        allowed_ocean = (values.size - 1) // 2
        violation = needed < required if parent_land else needed > allowed_ocean
        if not violation:
            continue
        low, high = -2.0, 2.0
        for _ in range(48):
            shift = (low + high) * 0.5
            count = int(np.count_nonzero(values + shift * window >= 0))
            if count < required:
                low = shift
            else:
                high = shift
        selected_shift = (low + high) * 0.5
        if not parent_land:
            low, high = -2.0, 2.0
            for _ in range(48):
                shift = (low + high) * 0.5
                count = int(np.count_nonzero(values + shift * window >= 0))
                if count <= allowed_ocean:
                    low = shift
                else:
                    high = shift
            selected_shift = (low + high) * 0.5
        fine_score[mask] += selected_shift * window
        support_corrections += 1
    fine_land = fine_score >= 0
    # Verify parent majority on the actual requested raster.
    violations = 0
    for row, col in sorted(set(zip(rr.ravel().tolist(), cc.ravel().tolist()))):
        child = fine_land[(rr == row) & (cc == col)]
        if child.size and ((child.mean() >= 0.5) != coarse[row, col]):
            violations += 1
    return fine_land, _coastline_from_region(fine_land, rows, cols, parent), {
        "subgrid_geometry_applied": True,
        "hierarchical_spatial_seeds": True,
        "parent_majority_violations": violations,
        "parent_land_class_rule": "LAND_IF_FINE_AREA_FRACTION_GE_0.5",
        "coastal_cells_refined": len(diagnostics),
        "parent_support_corrections": support_corrections,
        "detail_authority": "PROCEDURAL_MODEL_DETAIL_ONLY",
    }


def materialize_latent_land_region(parent: InitialWorldFields,
                                   latent: R6InitialGeometryLatentState,
                                   lat_centers: np.ndarray,
                                   lon_centers: np.ndarray,
                                   resolution_deg: float
                                   ) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Render a region with a one-cell halo for independently stable coasts."""
    lat_centers = np.asarray(lat_centers, dtype=np.float64)
    lon_centers = np.asarray(lon_centers, dtype=np.float64)
    if resolution_deg == 1.0:
        land = parent.land_ocean_mask[
            np.ix_(np.clip(np.floor(lat_centers + 90).astype(int), 0, 179),
                   np.clip(np.floor(lon_centers + 180).astype(int), 0, 359))].astype(bool)
        coast = parent.coastline_mask[
            np.ix_(np.clip(np.floor(lat_centers + 90).astype(int), 0, 179),
                   np.clip(np.floor(lon_centers + 180).astype(int), 0, 359))].astype(bool)
        return land, coast, {"subgrid_geometry_applied": False,
                             "parent_majority_violations": 0,
                             "detail_authority": "NONE_AT_GLOBAL_BASE"}
    halo = int(round(1.0 / resolution_deg))
    lat_ext = np.concatenate((lat_centers[0] - np.arange(halo, 0, -1) * resolution_deg,
                              lat_centers,
                              lat_centers[-1] + np.arange(1, halo + 1) * resolution_deg))
    lon_ext = np.concatenate((lon_centers[0] - np.arange(halo, 0, -1) * resolution_deg,
                              lon_centers,
                              lon_centers[-1] + np.arange(1, halo + 1) * resolution_deg))
    if lat_ext[0] < -90 or lat_ext[-1] > 90:
        raise ValueError("regional latent refinement requires a full one-degree halo from the poles")
    land_ext, _, audit = _materialize_latent_land_core(
        parent, latent, lat_ext, lon_ext, resolution_deg)
    coast_ext = np.zeros(land_ext.shape, dtype=bool)
    for i in range(1, land_ext.shape[0] - 1):
        for j in range(1, land_ext.shape[1] - 1):
            around = land_ext[i - 1:i + 2, j - 1:j + 2]
            coast_ext[i, j] = np.any(around != land_ext[i, j])
    land_core = land_ext[halo:-halo, halo:-halo]
    coast_core = coast_ext[halo:-halo, halo:-halo]
    rows = np.clip(np.floor(lat_centers + 90).astype(np.int64), 0, 179)
    cols = np.clip(np.floor(lon_centers + 180).astype(np.int64), 0, 359)
    rr = np.broadcast_to(rows[:, None], land_core.shape)
    cc = np.broadcast_to(cols[None, :], land_core.shape)
    violations = 0
    for row, col in sorted(set(zip(rr.ravel().tolist(), cc.ravel().tolist()))):
        child = land_core[(rr == row) & (cc == col)]
        if child.size and ((child.mean() >= 0.5) != bool(parent.land_ocean_mask[row, col])):
            violations += 1
    audit["parent_majority_violations"] = violations
    return land_core, coast_core, audit


def _coastline_from_region(land: np.ndarray, rows: np.ndarray, cols: np.ndarray,
                           parent: InitialWorldFields) -> np.ndarray:
    # Caller-provided halo is used by regional materialization.  For this
    # function, regional outer rows/columns are conservatively marked as edge
    # support only when the adjacent global parent exists.
    out = np.zeros(land.shape, dtype=bool)
    for i in range(land.shape[0]):
        for j in range(land.shape[1]):
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    ni, nj = i + di, j + dj
                    if 0 <= ni < land.shape[0] and 0 <= nj < land.shape[1]:
                        if land[ni, nj] != land[i, j]:
                            out[i, j] = True
                            break
                if out[i, j]:
                    break
    return out


def _relief_field(lat: np.ndarray, lon: np.ndarray,
                  terms_macro: tuple[HarmonicTerm, ...],
                  terms_meso: tuple[HarmonicTerm, ...],
                  macro_norm: float, meso_norm: float,
                  province: np.ndarray) -> np.ndarray:
    macro = _boundary_field(lat, lon, terms_macro, macro_norm)
    meso = _boundary_field(lat, lon, terms_meso, meso_norm)
    return np.clip(900.0 + 520.0 * macro + 170.0 * meso +
                   np.where(province == 3, 1500.0, 0.0), 25.0, 8000.0)


def materialize_latent_topography_region(
        parent: InitialWorldFields, latent: R6InitialGeometryLatentState,
        lat_centers: np.ndarray, lon_centers: np.ndarray,
        fine_land: np.ndarray, resolution_deg: float
        ) -> tuple[np.ndarray, dict[str, Any]]:
    """Add deterministic 20–100 km and 1–20 km terrain process detail.

    Fine detail is zero at 1-degree cell edges and area-centred per parent cell.
    Its status is procedural authorial model detail, not paleotopographic data.
    """
    lat_centers = np.asarray(lat_centers, dtype=np.float64)
    lon_centers = np.asarray(lon_centers, dtype=np.float64)
    land = np.asarray(fine_land, dtype=bool)
    rows = np.clip(np.floor(lat_centers + 90).astype(np.int64), 0, 179)
    cols = np.clip(np.floor(lon_centers + 180).astype(np.int64), 0, 359)
    rr = np.broadcast_to(rows[:, None], land.shape)
    cc = np.broadcast_to(cols[None, :], land.shape)
    if resolution_deg == 1.0:
        elevation = parent.land_surface_elevation_m[np.ix_(rows, cols)].copy()
        return elevation, {"fine_spectrum_added": False, "parent_mean_max_error_m": 0.0}

    out = np.full(land.shape, np.nan, dtype=np.float64)
    qnodes, qweights = np.polynomial.legendre.leggauss(24)
    qnodes = (qnodes + 1.0) * 0.5
    qweights = qweights * 0.5
    detail_sum_squares = 0.0
    detail_count = 0
    local_amplitude = 5.0 if resolution_deg <= 0.1 + 1e-12 else 0.0
    for row, col in sorted(set(zip(rr.ravel().tolist(), cc.ravel().tolist()))):
        selected = (rr == row) & (cc == col) & land
        if not selected.any():
            continue
        meso_par, local_par = _fine_parameters(latent, row, col, "topography")
        u = lat_centers[:, None] + 90.0 - row
        v = lon_centers[None, :] + 180.0 - col
        meso_noise = _windowed_noise(u, v, meso_par)
        local_noise = _windowed_noise(u, v, local_par)
        province = parent.province_class[np.ix_(np.array([row]), np.array([col]))]
        fine_base = _relief_field(lat_centers, lon_centers,
                                  latent.topography_terms_macro,
                                  latent.topography_terms_meso,
                                  latent.topography_macro_normalization,
                                  latent.topography_meso_normalization,
                                  province)
        qlat = row - 90.0 + qnodes
        qlon = col - 180.0 + qnodes
        qprovince = np.full((len(qnodes), len(qnodes)), int(province[0, 0]), dtype=np.int8)
        qbase = _relief_field(qlat, qlon,
                              latent.topography_terms_macro,
                              latent.topography_terms_meso,
                              latent.topography_macro_normalization,
                              latent.topography_meso_normalization,
                              qprovince)
        uu, vv = np.meshgrid(qnodes, qnodes, indexing="ij")
        qland, _, _ = materialize_latent_land_region(
            parent, latent, qlat, qlon, resolution_deg)
        qweights2d = _area_weights(qlat, qweights)
        support = qland & np.isfinite(qbase)
        if support.any():
            qnoise_meso = 20.0 * _windowed_noise(uu, vv, meso_par)
            qnoise_local = local_amplitude * _windowed_noise(uu, vv, local_par)
            mean_base = float((qweights2d[support] * qbase[support]).sum() /
                              qweights2d[support].sum())
            mean_noise = float((qweights2d[support] *
                                 (qnoise_meso[support] + qnoise_local[support])).sum() /
                               qweights2d[support].sum())
        else:
            mean_base, mean_noise = float(np.nanmean(qbase)), 0.0
        target = float(parent.land_surface_elevation_m[row, col])
        correction_base = target - mean_base if parent.land_ocean_mask[row, col] else 0.0
        correction_noise = -mean_noise if parent.land_ocean_mask[row, col] else 0.0
        detail = 20.0 * meso_noise + local_amplitude * local_noise + correction_noise
        values = fine_base + correction_base + detail
        values = np.clip(values, 0.0, 8000.0)
        out[selected] = values[selected]
        detail_sum_squares += float(np.square(detail[selected]).sum())
        detail_count += int(selected.sum())
    # Enforce the requested grid's area-weighted parent-cell constraint after
    # sampling, so 0.25/0.1 outputs conserve the same parent mean despite
    # different quadrature of the procedural fine-scale spectrum.
    lat_grid = np.broadcast_to(lat_centers[:, None], land.shape)
    for row, col in sorted(set(zip(rr.ravel().tolist(), cc.ravel().tolist()))):
        selected = (rr == row) & (cc == col) & land
        if not selected.any() or not parent.land_ocean_mask[row, col]:
            continue
        weights = np.cos(np.deg2rad(lat_grid[selected]))
        target = float(parent.land_surface_elevation_m[row, col])
        current = float(np.average(out[selected], weights=weights))
        out[selected] += target - current
    if np.nanmin(out) < 0 or np.nanmax(out) > 8000:
        raise ValueError("parent-conservative refinement exceeded authorized elevation domain")
    out32 = out.astype(np.float32)
    errors32 = []
    for row, col in sorted(set(zip(rr.ravel().tolist(), cc.ravel().tolist()))):
        selected = (rr == row) & (cc == col) & land
        if selected.any() and parent.land_ocean_mask[row, col]:
            weights = np.cos(np.deg2rad(lat_grid[selected]))
            target = float(parent.land_surface_elevation_m[row, col])
            errors32.append(abs(float(np.average(out32[selected], weights=weights)) - target))
    return out32, {
        "fine_spectrum_added": True,
        "bands": (["MESO_50_120KM_V1", "LOCAL_25_40KM_V1"] if
                  resolution_deg <= 0.1 + 1e-12 else ["MESO_50_120KM_V1"]),
        "band_amplitudes_m": {"meso": 20.0,
                              "local": 5.0 if resolution_deg <= 0.1 + 1e-12 else 0.0},
        "fine_detail_rms_m": float(np.sqrt(detail_sum_squares / max(1, detail_count))),
        "parent_mean_tolerance_m": PARENT_MEAN_TOLERANCE_M,
        "parent_mean_max_error_m": max(errors32, default=0.0),
    }


def build_latent_state(parent: InitialWorldFields, *, world_id: str,
                       parent_history_id: str, parent_state_id: str,
                       parent_payload_sha256: str) -> R6InitialGeometryLatentState:
    """Recover immutable coefficients/thresholds from governed named streams."""
    if parent.time_ma != 210.0 or not parent.metadata.get("canonical_seed"):
        raise ValueError("latent reconstruction requires canonical R6 t0 and seed lineage")
    streams = {s.name: s.rng() for s in derive_seed_streams()}
    geom_rng, coast_rng = streams["continental_blocks"], streams["coastline"]
    center_lat = float(geom_rng.uniform(-5.0, 5.0))
    center_lon = float(geom_rng.uniform(-180.0, 180.0))
    angle = float(geom_rng.uniform(-0.20, 0.20))
    coastline_terms = _draw_boundary(coast_rng)
    # Retain the current 1-degree field's exact global normalization.
    norm = float(_boundary_field_raw(parent.grid.lat_centers_deg,
                                     parent.grid.lon_centers_deg,
                                     coastline_terms).std())
    lat = parent.grid.lat_centers_deg[:, None]
    lon = parent.grid.lon_centers_deg[None, :]
    areas = parent.grid.cell_areas_m2()
    dlon = _wrap_degrees(lon - center_lon) * cos(np.deg2rad(center_lat))
    dlat = lat - center_lat
    x = dlon * cos(angle) + dlat * sin(angle)
    y = -dlon * sin(angle) + dlat * cos(angle)
    main_score = 1 - np.sqrt((x / 108.0) ** 2 + (y / 52.0) ** 2) + 0.14 * _boundary_field(
        parent.grid.lat_centers_deg, parent.grid.lon_centers_deg, coastline_terms, norm)
    main_rule = _score_threshold(main_score, areas, 0.27)
    main = _apply_threshold(main_score, main_rule,
                            np.arange(parent.grid.cell_count).reshape(parent.grid.shape))

    centers = ((center_lat - 5.0, center_lon - 142.0),
               (center_lat + 6.0, center_lon + 142.0),
               (67.0, center_lon - 30.0), (-67.0, center_lon + 45.0))
    phases = (float(coast_rng.uniform(0, 2*pi)), float(geom_rng.uniform(0, 2*pi)),
              float(coast_rng.uniform(0, 2*pi)), float(geom_rng.uniform(0, 2*pi)))
    terranes = []
    occupied = main.copy()
    for (lat0, lon0), phase in zip(centers, phases):
        distance = parent.grid.spherical_distance_km(lat0, lon0, lat, lon)
        perturb = (0.035 * np.sin(np.deg2rad(lon - lon0) * 3 + phase) *
                   np.cos(np.deg2rad(lat - lat0) * 2 - phase))
        island_score = -distance / 1100.0 + perturb
        rule = _score_threshold(island_score, areas, 0.0075, ~occupied)
        occupied |= _apply_threshold(island_score, rule,
                                     np.arange(parent.grid.cell_count).reshape(parent.grid.shape),
                                     ~occupied)
        terranes.append(TerraneLatent(lat0, lon0, phase, rule))

    plate_rng = streams["plate_mosaic"]
    nplates = int(plate_rng.integers(12, 19))
    plate_lat = np.rad2deg(np.arcsin(plate_rng.uniform(-1.0, 1.0, nplates)))
    plate_lon = plate_rng.uniform(-180.0, 180.0, nplates)
    nuclei = tuple((float(a), float(o)) for a, o in zip(plate_lat, plate_lon))

    relief_rng = streams["land_relief"]
    macro_terms = _draw_relief_terms(relief_rng, 14, 7, 5)
    meso_terms = _draw_relief_terms(relief_rng, 12, 16, 10)
    macro_norm = float(_boundary_field_raw(parent.grid.lat_centers_deg,
                                          parent.grid.lon_centers_deg,
                                          macro_terms).std())
    meso_norm = float(_boundary_field_raw(parent.grid.lat_centers_deg,
                                          parent.grid.lon_centers_deg,
                                          meso_terms).std())

    return R6InitialGeometryLatentState(
        schema=LATENT_SCHEMA, world_id=world_id,
        parent_history_id=parent_history_id, parent_state_id=parent_state_id,
        parent_payload_sha256=parent_payload_sha256,
        generator_id=str(parent.metadata["generator_id"]),
        generator_version=str(parent.metadata["generator_version"]),
        seed_lineage=lineage_manifest(),
        parameter_identity={
            "geometry": {"main_axes_deg": [108.0, 52.0],
                         "main_area_fraction": 0.27,
                         "coastline_harmonic_terms": 8,
                         "terrane_count": 4,
                         "terrane_area_fraction": 0.0075,
                         "terrane_distance_scale_km": 1100.0,
                         "fine_coastal_detail_score_amplitudes": {
                             "meso": 0.0015, "local": 0.0005,
                             "local_active_at_resolution_deg": 0.1},
                         "fine_support_aggregation": "LAND_IF_FINE_CHILD_FRACTION_GE_0.5",
                         "support_correction_window": "SIN2_PI_U_TIMES_SIN2_PI_V_ZERO_AT_PARENT_EDGES",
                         "fine_topography_bands": [
                             {"id": "MESO_50_120KM_V1", "cycles_per_parent_cell": [1, 2],
                              "amplitude_m": 20.0},
                             {"id": "LOCAL_25_40KM_V1", "cycles_per_parent_cell": [3, 4],
                              "amplitude_m": 5.0}],
                         "topography_aggregation": "COS_LATITUDE_WEIGHTED_PARENT_MEAN_CONSTRAINED",
                         "parent_mean_tolerance_m": PARENT_MEAN_TOLERANCE_M},
            "parent_grid": parent.grid.metadata(),
            "parameter_source": "versioned_generator_source_and_generator_contract",
        },
        geometry_center_latitude_deg=center_lat,
        geometry_center_longitude_deg=center_lon,
        geometry_orientation_radians=angle,
        coastline_terms=coastline_terms,
        coastline_normalization=norm,
        main_land_threshold=main_rule,
        terranes=tuple(terranes),
        plate_nuclei_lat_lon_deg=nuclei,
        craton_seed_cell_ids=tuple(parent.metadata["craton_seed_cells"]),
        categorical_parent_support="EXACT_CANONICAL_1DEG_CLASSIFICATION_CONSTRAINT",
        topography_terms_macro=macro_terms,
        topography_terms_meso=meso_terms,
        topography_macro_normalization=macro_norm,
        topography_meso_normalization=meso_norm,
        topography_process={
            "base_macro_process": "seed-reconstructable global harmonic V1",
            "fine_detail_seed_namespace": "WORLD_ID/COMPONENT_ID/SPATIAL_LEVEL/GLOBAL_PARENT_CELL",
            "regional_refinement_bands": [
                {"name": "MESO_50_120KM_V1", "cycles_per_parent_cell": [1, 2], "nominal_equatorial_wavelength_km": [55.6, 111.2], "amplitude_m": 20.0, "authority": "PROCEDURAL_MODEL_DETAIL"},
                {"name": "LOCAL_25_40KM_V1", "cycles_per_parent_cell": [3, 4], "nominal_equatorial_wavelength_km": [27.8, 37.1], "amplitude_m": 5.0, "activation_resolution_deg": 0.1, "authority": "PROCEDURAL_MODEL_DETAIL"}],
            "parent_mean_tolerance_m": PARENT_MEAN_TOLERANCE_M,
            "unknown_bathymetry_remains_unknown": True,
        },
    )
