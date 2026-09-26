"""Bounded synthetic t0 land relief; no erosion or temporal evolution."""

from __future__ import annotations

import numpy as np

from .grid import GlobalGrid1Degree


def _harmonic_field(grid: GlobalGrid1Degree, rng: np.random.Generator,
                    terms: int, max_lon_wave: int, max_lat_wave: int) -> np.ndarray:
    lat = np.deg2rad(grid.lat_centers_deg)[:, None]
    lon = np.deg2rad(grid.lon_centers_deg)[None, :]
    field = np.zeros(grid.shape, dtype=np.float64)
    for _ in range(terms):
        m = int(rng.integers(1, max_lon_wave + 1))
        n = int(rng.integers(1, max_lat_wave + 1))
        phase_lon, phase_lat = rng.uniform(0, 2 * np.pi, size=2)
        sign = -1.0 if rng.integers(0, 2) else 1.0
        field += sign * np.sin(m * lon + phase_lon) * np.cos(n * lat + phase_lat)
    sd = float(field.std())
    if sd == 0 or not np.isfinite(sd):
        raise ValueError("relief harmonic field is degenerate")
    return field / sd


def generate_land_elevation(grid: GlobalGrid1Degree, land: np.ndarray,
                            province: np.ndarray,
                            rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Return elevation and supported-land mask; ocean is NaN plus false mask."""
    macro = _harmonic_field(grid, rng, terms=14, max_lon_wave=7, max_lat_wave=5)
    meso = _harmonic_field(grid, rng, terms=12, max_lon_wave=16, max_lat_wave=10)
    # Every active scale is evaluated directly at native 1-degree cell centers.
    raw = 900.0 + 520.0 * macro + 170.0 * meso
    raw += np.where(province == 3, 1500.0, 0.0)  # designed orogenic province only
    # Smooth positive floor avoids a sea-level cliff; it is an authored t0 field.
    elevation = np.clip(raw, 25.0, 8000.0).astype(np.float32)
    elevation[~land] = np.nan
    return elevation, land.astype(np.bool_, copy=True)
