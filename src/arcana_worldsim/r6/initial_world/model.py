"""Typed in-memory representation of the single R6 physical t0 state."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .grid import GlobalGrid1Degree


@dataclass(frozen=True, slots=True)
class InitialWorldFields:
    grid: GlobalGrid1Degree
    time_ma: float
    land_ocean_mask: np.ndarray
    coastline_mask: np.ndarray
    plate_id: np.ndarray
    crust_class: np.ndarray
    boundary_class: np.ndarray
    province_class: np.ndarray
    land_surface_elevation_m: np.ndarray
    elevation_support_mask: np.ndarray
    synthetic_uncertainty_mask: np.ndarray
    bathymetry_unknown_mask: np.ndarray
    plate_motion_unknown_mask: np.ndarray
    deep_unknown_mask: np.ndarray
    climate_unknown_mask: np.ndarray
    hydrology_unknown_mask: np.ndarray
    craton_seed_cells: tuple[str, ...]
    plate_count: int
    metadata: dict[str, object]

    def arrays(self) -> dict[str, np.ndarray]:
        return {
            "land_ocean_mask": self.land_ocean_mask,
            "coastline_mask": self.coastline_mask,
            "plate_id": self.plate_id,
            "crust_class": self.crust_class,
            "boundary_class": self.boundary_class,
            "province_class": self.province_class,
            "land_surface_elevation_m": self.land_surface_elevation_m,
            "elevation_support_mask": self.elevation_support_mask,
            "synthetic_uncertainty_mask": self.synthetic_uncertainty_mask,
            "bathymetry_unknown_mask": self.bathymetry_unknown_mask,
            "plate_motion_unknown_mask": self.plate_motion_unknown_mask,
            "deep_unknown_mask": self.deep_unknown_mask,
            "climate_unknown_mask": self.climate_unknown_mask,
            "hydrology_unknown_mask": self.hydrology_unknown_mask,
        }
