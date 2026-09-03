from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .environment import RecentBoundaryState

STATUS = "PASS_EXACT_SEALED_120KA_SPATIAL_BOUNDARY_CONSERVATIVE_REMAP_CANDIDATE"
AUTHORITY = "v0.6.1 SEALED_PALEOCLIMATE_HISTORY"
TARGET_YEAR = -120_000.0
TARGET_AGE_MA = 0.12

EXPECTED = {
    "authorial_seal": "d097f83ce53fb298689c63458dfa1012d26b3983254ccf25085b91f882e55a2a",
    "model_py": "de2399e2b92157ee98d10458db5dcd849b557c076beeed3a648154a6c62e016f",
    "recent_history": "be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1",
    "spatial_snapshots": "a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd",
    "shoreline": "f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85",
}


def _sha(path: Path) -> str:
    h = sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_v061_sealed_root(root: Path) -> dict[str, str]:
    root = Path(root)
    paths = {
        "authorial_seal": root / "AUTHORIAL_SEAL_v0_6_1.json",
        "model_py": root / "src/arcana_worldsim/paleoclimate/model.py",
        "recent_history": root / "outputs/hybrid1/paleoclimate_v0_6_1/recent_paleoclimate_history.npz",
        "spatial_snapshots": root / "outputs/hybrid1/paleoclimate_v0_6_1/paleoclimate_spatial_snapshots.npz",
        "shoreline": root / "inputs/v0_5_5I_SEALED/shoreline_state_I.npz",
    }
    got = {}
    for key, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        got[key] = _sha(path)
        if got[key] != EXPECTED[key]:
            raise ValueError(f"sealed v0.6.1 {key} SHA256 mismatch: {got[key]}")
    return got


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50.0, 50.0)))


def _periodic_distance_cells_to_true(mask: np.ndarray) -> np.ndarray:
    # Exact algorithm used by sealed v0.6.1. scipy is required only when
    # re-materializing the boundary from the original sealed package.
    try:
        from scipy.ndimage import distance_transform_edt
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("scipy>=1.12 is required only for sealed-boundary rematerialization") from exc
    mask = np.asarray(mask, dtype=bool)
    tiled = np.concatenate((mask, mask, mask), axis=1)
    d = distance_transform_edt(~tiled)
    nlon = mask.shape[1]
    return d[:, nlon:2*nlon]


def reconstruct_v061_spatial_at_year(root: Path, year_before_book: float) -> dict[str, Any]:
    """Evaluate the sealed v0.6.1 spatial equations at any exact history checkpoint.

    This is a generalization of the output-time filter only; equations and
    constants are copied verbatim from sealed v0.6.1 `_spatial_snapshots`.
    """
    verify_v061_sealed_root(root)
    root = Path(root)
    h = np.load(root / "outputs/hybrid1/paleoclimate_v0_6_1/recent_paleoclimate_history.npz", allow_pickle=False)
    t = np.asarray(h["time_year_before_book"], dtype=float)
    hit = np.where(np.isclose(t, float(year_before_book), atol=1e-9, rtol=0))[0]
    if hit.size != 1:
        raise ValueError(f"sealed history has no exact checkpoint at {year_before_book}")
    i = int(hit[0])

    sh = np.load(root / "inputs/v0_5_5I_SEALED/shoreline_state_I.npz", allow_pickle=False)
    lat = np.asarray(sh["lat"], dtype=float)
    lon = np.asarray(sh["lon"], dtype=float)
    z = np.asarray(sh["elevation_m"], dtype=float)
    book_ocean = sh["ocean_mask"].astype(bool)

    dcell = _periodic_distance_cells_to_true(book_ocean)
    dy_km = 111.195 * 0.25
    coslat = np.maximum(np.cos(np.deg2rad(lat))[:, None], 0.08)
    distance_ocean_km = dcell * dy_km * np.sqrt(coslat)
    ocean_influence = np.exp(-distance_ocean_km / 900.0)

    lat2 = lat[:, None]
    abs_lat = np.abs(lat2)
    polar_amp = 1.0 + 0.55 * (abs_lat / 90.0) ** 1.5
    north_overturning_zone = _sigmoid((lat2 - 28.0) / 6.0) * _sigmoid((79.0 - lat2) / 7.0)
    south_compensation_zone = _sigmoid((-lat2 - 32.0) / 9.0) * _sigmoid((72.0 + lat2) / 8.0)

    summer = h["summer_ablation_forcing_index"]
    m = h["overturning_strength"]
    global_t = h["global_temperature_anomaly_c"]
    sea = h["sea_level_anomaly_m"]

    yd = np.clip((1.0 - m[i]) / 0.65, 0.0, 1.25)
    circulation_anom = (
        -5.5 * yd * north_overturning_zone * (0.35 + 0.65 * ocean_influence)
        + 0.45 * yd * south_compensation_zone
    )
    orbital_regional = 0.35 * (summer[i] - summer[-1]) * (abs_lat / 90.0) ** 1.2
    dt_local = global_t[i] * polar_amp + circulation_anom + orbital_regional

    pf = np.exp(0.035 * dt_local)
    pf *= 1.0 - 0.27 * yd * north_overturning_zone + 0.08 * yd * south_compensation_zone
    pf = np.clip(pf, 0.45, 1.45)
    nf = np.clip(np.exp(-np.abs(dt_local) / 12.0) * (pf ** 0.45), 0.05, 1.35)
    land = (z > sea[i]).astype(np.uint8)

    return {
        "year_before_book": float(t[i]),
        "atmospheric_co2_ppm": float(h["atmospheric_co2_ppm"][i]),
        "global_temperature_anomaly_c": float(global_t[i]),
        "sea_level_anomaly_m": float(sea[i]),
        "overturning_strength": float(m[i]),
        "summer_ablation_forcing_index": float(summer[i]),
        "lat": lat,
        "lon": lon,
        "temperature_anomaly_c": dt_local.astype(np.float32),
        "precipitation_factor_relative_book": pf.astype(np.float32),
        "npp_factor_relative_book": nf.astype(np.float32),
        "paleo_land_mask": land,
        "authority": AUTHORITY,
        "reconstruction_semantics": "SEALED_EQUATIONS_EXACT_HISTORY_CHECKPOINT_OUTPUT_FILTER_GENERALIZATION",
    }


def verify_generalizer_against_materialized_snapshot(root: Path, year_before_book: float = -21_000.0) -> dict[str, Any]:
    calc = reconstruct_v061_spatial_at_year(root, year_before_book)
    s = np.load(Path(root) / "outputs/hybrid1/paleoclimate_v0_6_1/paleoclimate_spatial_snapshots.npz", allow_pickle=False)
    years = np.asarray(s["snapshot_year_before_book"], dtype=float)
    hit = np.where(np.isclose(years, year_before_book))[0]
    if hit.size != 1:
        raise ValueError("requested equivalence checkpoint is not materialized in sealed snapshots")
    i = int(hit[0])
    mapping = {
        "temperature_anomaly_c": "temperature_anomaly_c",
        "precipitation_factor_relative_book": "precipitation_factor_relative_book",
        "npp_factor_relative_book": "npp_factor_relative_book",
        "paleo_land_mask": "paleo_land_mask",
    }
    fields = {}
    all_exact = True
    for ck, sk in mapping.items():
        a, b = np.asarray(calc[ck]), np.asarray(s[sk][i])
        exact = bool(np.array_equal(a, b))
        fields[ck] = {"bit_exact": exact, "max_abs_delta": float(np.max(np.abs(a.astype(float) - b.astype(float))))}
        all_exact &= exact
    return {"checkpoint_year": float(year_before_book), "all_fields_bit_exact": all_exact, "fields": fields}


def _regular_grid_edges(centers: np.ndarray) -> np.ndarray:
    centers = np.asarray(centers, dtype=float)
    d = np.diff(centers)
    if centers.ndim != 1 or d.size == 0 or not np.allclose(d, d[0], atol=1e-12, rtol=0):
        raise ValueError("grid centers must be regular 1-D")
    step = float(d[0])
    return np.concatenate(([centers[0] - step / 2.0], centers + step / 2.0))


def conservative_nested_remap(field: np.ndarray, src_lat: np.ndarray, src_lon: np.ndarray,
                              dst_lat: np.ndarray, dst_lon: np.ndarray) -> np.ndarray:
    """Area-weighted conservative remap for exactly nested regular lat/lon grids."""
    f = np.asarray(field, dtype=float)
    src_lat = np.asarray(src_lat, dtype=float); src_lon = np.asarray(src_lon, dtype=float)
    dst_lat = np.asarray(dst_lat, dtype=float); dst_lon = np.asarray(dst_lon, dtype=float)
    if f.shape != (src_lat.size, src_lon.size):
        raise ValueError("field shape does not match source grid")
    fy = src_lat.size // dst_lat.size; fx = src_lon.size // dst_lon.size
    if fy * dst_lat.size != src_lat.size or fx * dst_lon.size != src_lon.size:
        raise ValueError("source grid is not integer-nested in destination grid")
    se_y = _regular_grid_edges(src_lat); de_y = _regular_grid_edges(dst_lat)
    se_x = _regular_grid_edges(src_lon); de_x = _regular_grid_edges(dst_lon)
    if not (np.allclose(se_y[::fy], de_y, atol=1e-10) and np.allclose(se_x[::fx], de_x, atol=1e-10)):
        raise ValueError("source/destination cell edges are not exactly nested")
    # Exact spherical latitude-band area factor; longitude widths are uniform.
    wlat = np.sin(np.deg2rad(se_y[1:])) - np.sin(np.deg2rad(se_y[:-1]))
    blocks = f.reshape(dst_lat.size, fy, dst_lon.size, fx)
    w = wlat.reshape(dst_lat.size, fy, 1, 1)
    return (blocks * w).sum(axis=(1, 3)) / (w.sum(axis=(1, 3)) * fx)


def remap_exact_120ka_to_a1(a1: Mapping[str, Any], spatial: Mapping[str, Any]) -> dict[str, Any]:
    src_lat = np.asarray(spatial["lat"], float); src_lon = np.asarray(spatial["lon"], float)
    dst_lat = np.asarray(a1["lat"], float); dst_lon = np.asarray(a1["lon"], float)
    keys = ("temperature_anomaly_c", "precipitation_factor_relative_book", "npp_factor_relative_book", "paleo_land_mask")
    out = {k: conservative_nested_remap(np.asarray(spatial[k], float), src_lat, src_lon, dst_lat, dst_lon) for k in keys}
    out.update({"lat": dst_lat, "lon": dst_lon, "year_before_book": TARGET_YEAR, "age_ma": TARGET_AGE_MA,
                "atmospheric_co2_ppm": float(spatial["atmospheric_co2_ppm"]),
                "global_temperature_anomaly_c": float(spatial["global_temperature_anomaly_c"]),
                "sea_level_anomaly_m": float(spatial["sea_level_anomaly_m"]),
                "overturning_strength": float(spatial["overturning_strength"]),
                "summer_ablation_forcing_index": float(spatial["summer_ablation_forcing_index"])})
    return out


def boundary_state_from_remapped_120ka(a1: Mapping[str, Any], remapped: Mapping[str, Any],
                                       history_sha256: str, spatial_sha256: str) -> RecentBoundaryState:
    ages = np.asarray(a1["age_ma"], dtype=float)
    i0 = int(np.where(np.isclose(ages, 0.0))[0][0])
    t0 = np.asarray(a1["temperature_c"][i0], dtype=float)
    a0 = np.asarray(a1["aridity_index"][i0], dtype=float)
    b0 = np.asarray(a1["browse_forage"][i0], dtype=float)
    l0 = np.asarray(a1["low_forage"][i0], dtype=float)
    w0 = np.asarray(a1["wetland_forage"][i0], dtype=float)
    dt = np.asarray(remapped["temperature_anomaly_c"], dtype=float)
    precip = np.asarray(remapped["precipitation_factor_relative_book"], dtype=float)
    npp = np.maximum(np.asarray(remapped["npp_factor_relative_book"], dtype=float), 0.0)
    land = np.clip(np.asarray(remapped["paleo_land_mask"], dtype=float), 0.0, 1.0)
    pet = np.exp(0.045 * dt)
    aridity = np.clip(a0 * np.maximum(precip, 0.0) / np.maximum(pet, 1e-8), 0.0, 3.0)
    browse = b0 * npp * land; low = l0 * npp * land; wet = w0 * npp * land
    return RecentBoundaryState(
        age_ma=TARGET_AGE_MA,
        atmospheric_co2_ppm=float(remapped["atmospheric_co2_ppm"]),
        temperature_c=t0 + dt,
        aridity_index=aridity,
        browse_forage=browse,
        low_forage=low,
        wetland_forage=wet,
        total_edible_forage=browse + low + wet,
        paleo_land_mask=land,
        source_history_sha256=history_sha256,
        source_spatial_sha256=spatial_sha256,
        exact_payload_verified=True,
        provenance="EXACT_SEALED_V0_6_1_120KA_SPATIAL_RECONSTRUCTION_AREA_CONSERVATIVE_8x8_REMAP",
    )


def load_materialized_a1_boundary(path: Path, history_sha256: str = EXPECTED["recent_history"],
                                  spatial_sha256: str = EXPECTED["spatial_snapshots"]) -> RecentBoundaryState:
    z = np.load(Path(path), allow_pickle=False)
    required = ("age_ma","atmospheric_co2_ppm","temperature_c","aridity_index","browse_forage","low_forage","wetland_forage","total_edible_forage","paleo_land_fraction")
    missing=[k for k in required if k not in z.files]
    if missing: raise KeyError(f"materialized B1 boundary missing fields: {missing}")
    if abs(float(np.asarray(z["age_ma"]).reshape(-1)[0])-TARGET_AGE_MA)>1e-12:
        raise ValueError("materialized boundary is not the 120 ka checkpoint")
    return RecentBoundaryState(
        age_ma=TARGET_AGE_MA,
        atmospheric_co2_ppm=float(np.asarray(z["atmospheric_co2_ppm"]).reshape(-1)[0]),
        temperature_c=np.asarray(z["temperature_c"],float), aridity_index=np.asarray(z["aridity_index"],float),
        browse_forage=np.asarray(z["browse_forage"],float), low_forage=np.asarray(z["low_forage"],float),
        wetland_forage=np.asarray(z["wetland_forage"],float), total_edible_forage=np.asarray(z["total_edible_forage"],float),
        paleo_land_mask=np.asarray(z["paleo_land_fraction"],float),
        source_history_sha256=history_sha256, source_spatial_sha256=spatial_sha256,
        exact_payload_verified=True,
        provenance="MATERIALIZED_v0_6_4B1_EXACT_SEALED_EQUATION_120KA_BOUNDARY_CONSERVATIVE_REMAP",
    )
