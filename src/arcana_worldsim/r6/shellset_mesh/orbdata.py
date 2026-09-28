"""Deterministic ARCANA-to-OrbData grids (numerical support only)."""
from __future__ import annotations

import hashlib
import heapq
import json
from pathlib import Path
from typing import Any

import numpy as np

GRID_SHAPE = (180, 360)  # south-to-north rows, west-to-east columns


def _sha(array: np.ndarray) -> str:
    a = np.asarray(array)
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _nearest_extension(values: np.ndarray, support: np.ndarray) -> np.ndarray:
    """Multi-source geodesic Dijkstra over periodic 8-neighbor cell centers."""
    nr, nc = values.shape
    all_sources = np.flatnonzero(support)
    if not len(all_sources):
        raise ValueError("nearest extension requires nonempty physical support")
    boundary = []
    for cell in all_sources.tolist():
        row, col = divmod(cell, nc)
        if any(0 <= row + dr < nr and not support[row + dr, (col + dc) % nc]
               for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)):
            boundary.append(cell)
    source_cells = np.asarray(boundary or all_sources.tolist(), dtype=np.int64)
    dist = np.full(nr * nc, np.inf, dtype=np.float64)
    source = np.full(nr * nc, nr * nc, dtype=np.int64)
    queue: list[tuple[float, int, int]] = []
    for cell in source_cells.tolist():
        dist[cell] = 0.0
        source[cell] = cell
        heapq.heappush(queue, (0.0, cell, cell))
    neighbors = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))
    while queue:
        distance, source_id, cell = heapq.heappop(queue)
        if distance != dist[cell] or source_id != source[cell]:
            continue
        row, col = divmod(cell, nc)
        lat1 = np.radians(-89.5 + row)
        lon1 = np.radians(-179.5 + col)
        for dr, dc in neighbors:
            r2 = row + dr
            if not 0 <= r2 < nr:
                continue
            c2 = (col + dc) % nc
            lat2 = np.radians(-89.5 + r2)
            lon2 = np.radians(-179.5 + c2)
            dlat, dlon = lat2 - lat1, (lon2 - lon1 + np.pi) % (2 * np.pi) - np.pi
            edge = 2.0 * np.arcsin(np.sqrt(np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2))
            target = r2 * nc + c2
            candidate = distance + float(edge)
            # Queue order is (distance, source flat ID, cell ID), so the first
            # equal-distance source wins deterministically without duplicate tie waves.
            if candidate < dist[target] - 1e-14:
                dist[target], source[target] = candidate, source_id
                heapq.heappush(queue, (candidate, source_id, target))
    extended = np.asarray(values).ravel()[source].reshape(values.shape).copy()
    extended[support] = np.asarray(values)[support]
    return extended


def make_orbdata_grids(fields: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Build source fields and 1-cell interpolation halos for a 180x360 package.

    Serialized axes add one halo cell at every edge: x=-180.5..180.5,
    y=-90.5..90.5. Rows are written north-to-south as OrbData indexes from y2.
    """
    required = {"oceanic_lithosphere_age_ma", "crustal_thickness_m",
                "physical_crust_domain_id", "continental_reference_lithosphere_thickness_m"}
    if not required <= fields.keys():
        raise ValueError(f"field package missing {sorted(required - fields.keys())}")
    age = np.asarray(fields["oceanic_lithosphere_age_ma"], dtype=np.float64)
    crust_m = np.asarray(fields["crustal_thickness_m"], dtype=np.float64)
    domain = np.asarray(fields["physical_crust_domain_id"], dtype=np.int32)
    mantle_m = np.asarray(fields["continental_reference_lithosphere_thickness_m"], dtype=np.float64)
    if any(a.shape != GRID_SHAPE for a in (age, crust_m, domain, mantle_m)):
        raise ValueError("OrbData adapter requires the governed 180x360 support")
    if not np.all(np.isfinite(age)) or not np.all(np.isfinite(crust_m)) or not np.all(np.isfinite(mantle_m)):
        raise ValueError("grid exporter requires finite package values")
    ocean = domain == 1
    land = ~ocean
    if not np.any(ocean) or not np.any(land) or np.any(domain < 1):
        raise ValueError("physical_crust_domain_id must identify ocean=1 and land classes >=2")
    age_physical = ocean
    age_extended = _nearest_extension(age, ocean)
    mantle_extended = _nearest_extension(mantle_m, land)
    # Wrap longitude and duplicate polar edge rows; these cells are numerical halos.
    def halo(a: np.ndarray) -> np.ndarray:
        p = np.pad(a, ((1, 1), (0, 0)), mode="edge")
        return np.pad(p, ((0, 0), (1, 1)), mode="wrap")
    grids = {
        "aArray": halo(age_extended),
        "cArray": halo(crust_m / 1000.0),
        "arcana_domain": halo(domain),
        "arcana_cont_mantle_thickness_m": halo(mantle_extended),
    }
    halo_mask = halo(~ocean)
    mantle_halo_mask = halo(ocean)
    lineage = {
        "schema": "R6_T0_ORBDATA_GRID_EXPORT_V1",
        "classification": "NUMERICAL_INTERPOLATION_HALO_ONLY",
        "source_hashes": {k: _sha(np.asarray(fields[k])) for k in sorted(required)},
        "grids": {k: {"shape": list(v.shape), "sha256": _sha(v)} for k, v in grids.items()},
        "aArray": {"source": "oceanic_lithosphere_age_ma", "units": "Ma",
                   "physical_support_mask_sha256": _sha(age_physical), "halo_mask_sha256": _sha(halo_mask),
                   "halo_method": "multi-source 8-neighbor geodesic Dijkstra on periodic cell centers; stable flat-index tie break"},
        "cArray": {"source": "crustal_thickness_m", "units": "km",
                   "conversion": "metres / 1000; OrbData multiplies cArray by 1000"},
        "domain": {"source": "physical_crust_domain_id", "ocean_class": 1,
                   "continental_classes": "2..6 per governed package; never inferred from age or plate id"},
        "continental_mantle_thickness": {"source": "continental_reference_lithosphere_thickness_m",
                   "units": "m", "halo_mask_sha256": _sha(mantle_halo_mask),
                   "transfer": "direct explicit input; no sArray or delta_ts encoding"},
        "grid": {"source_shape": list(GRID_SHAPE), "output_shape": [182, 362],
                 "physical_cell_centers": "lon=-179.5..179.5, lat=-89.5..89.5",
                 "header": {"nX": 362, "nY": 182, "x1": -180.5, "dx": 1, "x2": 180.5,
                            "y1": -90.5, "dy": 1, "y2": 90.5},
                 "file_row_order": "north-to-south; NumPy source arrays south-to-north",
                 "longitude_halo": "periodic wrap", "latitude_halo": "duplicate polar-adjacent edge row"},
        "replay_identity": None,
    }
    lineage["replay_identity"] = hashlib.sha256(json.dumps(lineage, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return grids, lineage


def write_orbdata_grids(fields: dict[str, np.ndarray], output_dir: str | Path) -> dict[str, Any]:
    grids, lineage = make_orbdata_grids(fields)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    names = {"aArray": "age.grd", "cArray": "crust_thickness.grd",
             "arcana_domain": "ARCANA_DOMAIN.grd",
             "arcana_cont_mantle_thickness_m": "ARCANA_CONT_MANTLE_THICKNESS_M.grd"}
    for key, grid in grids.items():
        with (root / names[key]).open("w", encoding="ascii", newline="\n") as stream:
            # OrbData5 reads coordinate bounds only; dimensions are derived from them.
            stream.write("-180.5 1 180.5\n-90.5 1 90.5\n")
            np.savetxt(stream, grid[::-1], fmt="%.12g")
    (root / "orbdata_grid_lineage.json").write_text(json.dumps(lineage, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lineage
