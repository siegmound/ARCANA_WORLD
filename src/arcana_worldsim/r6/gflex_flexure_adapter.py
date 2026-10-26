"""Narrow optional adapter for the external gFlex elastic-plate solver.

This adapter preserves the distinction between an instantaneous flexure solve
and an R6 surface evolution. It deliberately imports gFlex/NumPy lazily so the
rest of the R6 package remains usable without this optional dependency.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import importlib.metadata
import json
import math
import time
from typing import Any, Sequence


class FlexureAdapterError(ValueError):
    pass


def _canonical_sha(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class GFlexParameters:
    """Explicit SI parameters; benchmark values carry no ARCANA authority."""

    grid_spacing_x_m: float
    young_modulus_pa: float
    poisson_ratio: float
    elastic_thickness_m: float
    mantle_density_kg_m3: float
    infill_density_kg_m3: float
    gravity_m_s2: float
    boundary_west: str = "0Displacement0Slope"
    boundary_east: str = "0Displacement0Slope"
    grid_spacing_y_m: float | None = None
    boundary_north: str = "0Displacement0Slope"
    boundary_south: str = "0Displacement0Slope"
    authority: str = "SYNTHETIC_BENCHMARK_PARAMETERS"

    def validate(self, *, dimension: int) -> None:
        vals = (self.grid_spacing_x_m, self.young_modulus_pa,
                self.poisson_ratio, self.elastic_thickness_m,
                self.mantle_density_kg_m3, self.infill_density_kg_m3,
                self.gravity_m_s2)
        if any(not math.isfinite(float(v)) for v in vals):
            raise FlexureAdapterError("PARAMETER_NONFINITE")
        if (self.grid_spacing_x_m <= 0 or self.young_modulus_pa <= 0
                or not -1.0 < self.poisson_ratio < 0.5
                or self.elastic_thickness_m <= 0
                or self.mantle_density_kg_m3 <= self.infill_density_kg_m3
                or self.infill_density_kg_m3 < 0 or self.gravity_m_s2 <= 0):
            raise FlexureAdapterError("PARAMETER_OUT_OF_RANGE")
        if dimension == 2 and (self.grid_spacing_y_m is None
                or not math.isfinite(float(self.grid_spacing_y_m))
                or self.grid_spacing_y_m <= 0):
            raise FlexureAdapterError("Y_GRID_SPACING_REQUIRED")
        if not self.authority:
            raise FlexureAdapterError("PARAMETER_AUTHORITY_REQUIRED")


def load_pressure_from_mass_delta(mass_delta_kg: Sequence[float],
                                  area_m2: Sequence[float],
                                  gravity_m_s2: float) -> list[float]:
    """Convert a signed surface mass change to stress: Δq = Δm g / A [Pa]."""
    if (len(mass_delta_kg) != len(area_m2) or not mass_delta_kg
            or not math.isfinite(gravity_m_s2) or gravity_m_s2 <= 0):
        raise FlexureAdapterError("LOAD_SHAPE_OR_GRAVITY_INVALID")
    out = []
    for mass, area in zip(mass_delta_kg, area_m2):
        if not math.isfinite(float(mass)) or not math.isfinite(float(area)) or area <= 0:
            raise FlexureAdapterError("LOAD_MASS_OR_AREA_INVALID")
        out.append(float(mass) * gravity_m_s2 / float(area))
    return out


def _gflex(required_version: str):
    try:
        version = importlib.metadata.version("gflex")
        import gflex
        import numpy as np
    except (ImportError, importlib.metadata.PackageNotFoundError) as exc:
        raise FlexureAdapterError("GFLEX_NUMPY_OR_SCIPY_UNAVAILABLE") from exc
    if version != required_version:
        raise FlexureAdapterError(f"GFLEX_VERSION_MISMATCH:{version}")
    return gflex, np, version


def solve_gflex_1d(load_pa: Sequence[float], sample_ids: Sequence[str], *,
                   parameters: GFlexParameters, time_s: float,
                   provenance: dict[str, Any], required_version: str = "1.3.0") -> dict[str, Any]:
    """Run actual gFlex F1D FD solve and return deflection [m] and provenance."""
    parameters.validate(dimension=1)
    if (len(load_pa) != len(sample_ids) or len(load_pa) < 5
            or not math.isfinite(time_s) or time_s < 0
            or any(not isinstance(x, str) or not x for x in sample_ids)
            or len(set(sample_ids)) != len(sample_ids)
            or not isinstance(provenance, dict) or not provenance):
        raise FlexureAdapterError("MESH_TIME_OR_PROVENANCE_INVALID")
    gflex, np, version = _gflex(required_version)
    load = np.asarray(load_pa, dtype=float)
    if not np.isfinite(load).all():
        raise FlexureAdapterError("LOAD_NONFINITE")
    flex = gflex.F1D()
    _configure_solver(flex, parameters, load, dimension=1)
    started = time.perf_counter()
    initialized = False
    try:
        flex.initialize()
        initialized = True
        flex.run()
        elapsed = time.perf_counter() - started
        displacement = np.asarray(flex.w, dtype=float).copy()
    finally:
        if initialized:
            flex.finalize()
    if displacement.shape != load.shape or not np.isfinite(displacement).all():
        raise FlexureAdapterError("GFLEX_OUTPUT_INVALID")
    return _result(displacement.tolist(), [list(sample_ids)], load.tolist(), parameters,
                   time_s, provenance, version, elapsed, "F1D")


def solve_gflex_2d(load_pa: Sequence[Sequence[float]], cell_ids: Sequence[Sequence[str]], *,
                   parameters: GFlexParameters, time_s: float,
                   provenance: dict[str, Any], required_version: str = "1.3.0") -> dict[str, Any]:
    """Run actual gFlex F2D FD solve on an explicitly matching synthetic mesh."""
    parameters.validate(dimension=2)
    rows = [list(row) for row in load_pa]
    ids = [list(row) for row in cell_ids]
    if (len(rows) < 5 or any(len(row) != len(rows[0]) for row in rows)
            or len(ids) != len(rows) or any(len(row) != len(rows[0]) for row in ids)
            or len(ids[0]) < 5 or any(not isinstance(x, str) or not x for row in ids for x in row)
            or len({x for row in ids for x in row}) != len(ids) * len(ids[0])
            or not math.isfinite(time_s) or time_s < 0
            or not isinstance(provenance, dict) or not provenance):
        raise FlexureAdapterError("MESH_TIME_OR_PROVENANCE_INVALID")
    gflex, np, version = _gflex(required_version)
    load = np.asarray(rows, dtype=float)
    if not np.isfinite(load).all():
        raise FlexureAdapterError("LOAD_NONFINITE")
    flex = gflex.F2D()
    _configure_solver(flex, parameters, load, dimension=2)
    started = time.perf_counter()
    initialized = False
    try:
        flex.initialize()
        initialized = True
        flex.run()
        elapsed = time.perf_counter() - started
        displacement = np.asarray(flex.w, dtype=float).copy()
    finally:
        if initialized:
            flex.finalize()
    if displacement.shape != load.shape or not np.isfinite(displacement).all():
        raise FlexureAdapterError("GFLEX_OUTPUT_INVALID")
    return _result(displacement.tolist(), ids, load.tolist(), parameters,
                   time_s, provenance, version, elapsed, "F2D")


def _configure_solver(flex: Any, parameters: GFlexParameters, load: Any,
                      *, dimension: int) -> None:
    # gFlex 1.3.0's programmatic API uses these legacy capitalized names.
    flex.Method = "FD"
    flex.Solver = "direct"
    flex.g = parameters.gravity_m_s2
    flex.E = parameters.young_modulus_pa
    flex.nu = parameters.poisson_ratio
    flex.rho_m = parameters.mantle_density_kg_m3
    flex.rho_fill = parameters.infill_density_kg_m3
    flex.Te = parameters.elastic_thickness_m
    flex.qs = load.copy()
    flex.dx = parameters.grid_spacing_x_m
    flex.BC_W = parameters.boundary_west
    flex.BC_E = parameters.boundary_east
    flex.Quiet = True
    flex.Verbose = False
    flex.Debug = False
    if dimension == 2:
        flex.dy = parameters.grid_spacing_y_m
        flex.BC_N = parameters.boundary_north
        flex.BC_S = parameters.boundary_south


def _result(displacement: list, ids: list[list[str]], load: list,
            params: GFlexParameters, time_s: float, provenance: dict,
            version: str, elapsed_s: float, solver_kind: str) -> dict[str, Any]:
    shape = [len(ids[0])] if solver_kind == "F1D" else [len(ids), len(ids[0])]
    mesh = {"dimension": solver_kind, "cell_or_sample_ids": ids,
            "shape": shape,
            "grid_spacing_x_m": params.grid_spacing_x_m,
            "grid_spacing_y_m": params.grid_spacing_y_m}
    payload = {"solver": "gFlex", "version": version, "solver_kind": solver_kind,
        "time_s": time_s, "parameters": asdict(params), "mesh": mesh,
        "load_pa": load, "deflection_m": displacement, "provenance": provenance}
    return {**payload, "mesh_identity_sha256": _canonical_sha(mesh),
        "configuration_identity_sha256": _canonical_sha({"parameters": asdict(params),
            "solver": "gFlex", "version": version, "solver_kind": solver_kind}),
        "result_identity_sha256": _canonical_sha(payload), "runtime_seconds": elapsed_s,
        "temporal_semantics": "INSTANTANEOUS_ELASTIC_EQUILIBRIUM; NOT_A_TIME_INTEGRATOR"}


def apply_deflection_increment_to_region(region_state: dict[str, Any], *,
                                         cell_ids: Sequence[Sequence[str]],
                                         previous_deflection_m: Sequence[Sequence[float]],
                                         current_deflection_m: Sequence[Sequence[float]],
                                         previous_time_s: float,
                                         current_time_s: float) -> dict[str, Any]:
    """Apply Δw once to a matching synthetic region's bedrock and surface.

    The test-only regional grid must have exactly the cell IDs supplied by the
    gFlex grid. This function does not apply to an R6 geographic mesh.
    """
    import copy
    from .regional_geological_evolution import RegionalConfig, _drainage_for_elevation
    ids = [x for row in cell_ids for x in row]
    if (len(cell_ids) != 3 or any(len(row) != 3 for row in cell_ids)
            or len(previous_deflection_m) != 3
            or any(len(row) != 3 for row in previous_deflection_m)
            or len(current_deflection_m) != 3
            or any(len(row) != 3 for row in current_deflection_m)):
        raise FlexureAdapterError("REGION_GRID_MUST_BE_3X3")
    prev = [float(x) for row in previous_deflection_m for x in row]
    curr = [float(x) for row in current_deflection_m for x in row]
    cells = region_state.get("cells")
    if (region_state.get("authority") != "NONCANONICAL_SYNTHETIC_3X3_BASIN"
            or not isinstance(cells, list) or len(ids) != len(cells)
            or ids != [cell["cell_id"] for cell in cells]
            or len(prev) != len(ids) or len(curr) != len(ids)
            or any(not math.isfinite(x) for x in (*prev, *curr))
            or not math.isfinite(previous_time_s) or not math.isfinite(current_time_s)
            or previous_time_s < 0 or current_time_s <= previous_time_s):
        raise FlexureAdapterError("REGION_MESH_BINDING_INVALID")
    updated = copy.deepcopy(region_state)
    applied = []
    for cell, old, new in zip(updated["cells"], prev, curr):
        delta = new - old
        cell["elevation_m"] += delta
        cell["bedrock_elevation_m"] += delta
        cell["cumulative_vertical_flexure_m"] += delta
        applied.append(delta)
    cfg = RegionalConfig(**updated["config"])
    updated["drainage_targets"] = _drainage_for_elevation(updated["cells"], cfg)
    updated.setdefault("flexure_events", []).append({
        "kind": "SYNTHETIC_GFLEX_VERTICAL_INCREMENT",
        "from_time_s": previous_time_s, "to_time_s": current_time_s,
        "delta_deflection_m_by_cell": dict(zip(ids, applied)),
        "authority": "EXPERIMENTAL_INTERFACE_ONLY_NOT_R6_OR_GEOLOGIC_AUTHORITY"})
    return updated
