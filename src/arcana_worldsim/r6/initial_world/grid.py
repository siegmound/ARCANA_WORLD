"""Canonical 1-degree spherical cell grid for the R6 initial world."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin

import numpy as np


@dataclass(frozen=True, slots=True)
class GlobalGrid1Degree:
    """180x360 global cell grid; row 0 is southernmost, columns wrap eastward."""

    grid_id: str = "R6_GLOBAL_GEOGRAPHY_1DEG_V1"
    radius_m: float = 6_371_000.0
    nlat: int = 180
    nlon: int = 360

    def __post_init__(self) -> None:
        if (self.grid_id != "R6_GLOBAL_GEOGRAPHY_1DEG_V1" or
                self.nlat != 180 or self.nlon != 360 or self.radius_m != 6_371_000.0):
            raise ValueError("grid parameters differ from the frozen R6 1-degree contract")

    @property
    def lat_bounds_deg(self) -> np.ndarray:
        return np.linspace(-90.0, 90.0, self.nlat + 1, dtype=np.float64)

    @property
    def lon_bounds_deg(self) -> np.ndarray:
        return np.linspace(-180.0, 180.0, self.nlon + 1, dtype=np.float64)

    @property
    def lat_centers_deg(self) -> np.ndarray:
        return (self.lat_bounds_deg[:-1] + self.lat_bounds_deg[1:]) * 0.5

    @property
    def lon_centers_deg(self) -> np.ndarray:
        return (self.lon_bounds_deg[:-1] + self.lon_bounds_deg[1:]) * 0.5

    @property
    def shape(self) -> tuple[int, int]:
        return self.nlat, self.nlon

    @property
    def cell_count(self) -> int:
        return self.nlat * self.nlon

    def cell_id(self, row: int, col: int) -> str:
        if not (0 <= row < self.nlat and 0 <= col < self.nlon):
            raise IndexError("cell row/column outside R6 grid")
        return f"R6G1D-R{row:03d}-C{col:03d}"

    def cell_index(self, row: int, col: int) -> int:
        if not (0 <= row < self.nlat and 0 <= col < self.nlon):
            raise IndexError("cell row/column outside R6 grid")
        return row * self.nlon + col

    def row_col(self, index: int) -> tuple[int, int]:
        if not (0 <= index < self.cell_count):
            raise IndexError("cell index outside R6 grid")
        return divmod(index, self.nlon)

    def neighbors(self, row: int, col: int) -> tuple[tuple[int, int], ...]:
        """Return unique 8-neighbours; longitude wraps and each polar cap closes."""
        if not (0 <= row < self.nlat and 0 <= col < self.nlon):
            raise IndexError("cell row/column outside R6 grid")
        result = set()
        for dr in (-1, 0, 1):
            rr = row + dr
            if rr < 0 or rr >= self.nlat:
                continue
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                result.add((rr, (col + dc) % self.nlon))
        if row == 0 or row == self.nlat - 1:
            result.update((row, c) for c in range(self.nlon) if c != col)
        return tuple(sorted(result))

    def cell_areas_m2(self) -> np.ndarray:
        lat = np.deg2rad(self.lat_bounds_deg)
        delta_lon = 2.0 * pi / self.nlon
        row_areas = self.radius_m**2 * delta_lon * (np.sin(lat[1:]) - np.sin(lat[:-1]))
        return np.broadcast_to(row_areas[:, None], self.shape).copy()

    def spherical_distance_km(self, lat1_deg: float, lon1_deg: float,
                              lat2_deg: np.ndarray, lon2_deg: np.ndarray) -> np.ndarray:
        lat1, lon1 = np.deg2rad(lat1_deg), np.deg2rad(lon1_deg)
        lat2r, lon2r = np.deg2rad(lat2_deg), np.deg2rad(lon2_deg)
        dlat = lat2r - lat1
        dlon = (lon2r - lon1 + pi) % (2 * pi) - pi
        h = np.sin(dlat / 2) ** 2 + cos(lat1) * np.cos(lat2r) * np.sin(dlon / 2) ** 2
        return (2 * self.radius_m * np.arcsin(np.sqrt(np.clip(h, 0.0, 1.0)))) / 1000.0

    def metadata(self) -> dict[str, object]:
        return {
            "grid_id": self.grid_id,
            "crs": "EPSG:4326 coordinate semantics; spherical metrics",
            "shape_lat_lon": list(self.shape),
            "row_order": "SOUTH_TO_NORTH",
            "column_order": "WEST_TO_EAST_WITH_PERIODIC_LONGITUDE",
            "latitude_bounds_deg": [-90.0, 90.0],
            "latitude_centers_first_last_deg": [-89.5, 89.5],
            "longitude_bounds_deg": [-180.0, 180.0],
            "longitude_centers_first_last_deg": [-179.5, 179.5],
            "cell_id_pattern": "R6G1D-R{row:03d}-C{column:03d}",
            "nominal_cell_size_deg": [1.0, 1.0],
            "radius_m": self.radius_m,
            "cell_area_formula": "R^2 * delta_lon_rad * (sin(north_lat_rad) - sin(south_lat_rad))",
            "pole_policy": "All cells in each terminal latitude row are mutually adjacent at the shared polar point.",
        }
