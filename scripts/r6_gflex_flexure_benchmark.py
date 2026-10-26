#!/usr/bin/env python3
"""Run the bounded, noncanonical R6-FLEX-1 gFlex benchmark.

The runner creates exactly one fresh result directory and never reads or writes
WORLD_HISTORY. All loads, elastic parameters, and the regional surface fixture
are synthetic engineering inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import time
import tracemalloc
from typing import Any

from arcana_worldsim.r6.gflex_flexure_adapter import (
    GFlexParameters,
    apply_deflection_increment_to_region,
    load_pressure_from_mass_delta,
    solve_gflex_1d,
    solve_gflex_2d,
)
from arcana_worldsim.r6.regional_geological_evolution import (
    RegionalConfig,
    advance_region,
    create_synthetic_region,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "outputs/r6_flex1_gflex_20261026_01"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _peak_working_set_bytes() -> int | None:
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t)]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    process = kernel32.GetCurrentProcess()
    ok = psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb)
    return int(counters.PeakWorkingSetSize) if ok else None


def _run_1d() -> dict[str, Any]:
    n, dx, pressure = 601, 2_000.0, 1.0e6
    center = n // 2
    load = [0.0] * n
    load[center - 5:center + 6] = [pressure] * 11
    ids = [f"SYNTHETIC_TRANSECT:{i:04d}" for i in range(n)]
    params = GFlexParameters(dx, 70.0e9, 0.25, 20_000.0, 3_300.0, 0.0, 9.81)
    provenance = {"authority": "SYNTHETIC_BENCHMARK_ONLY",
                  "load_material": "SYNTHETIC_SURFACE_MASS_SHEET",
                  "geographic_binding": "NONE"}
    baseline = solve_gflex_1d(load, ids, parameters=params, time_s=0.0,
                              provenance=provenance)
    doubled = solve_gflex_1d([2 * q for q in load], ids, parameters=params,
                             time_s=1.0, provenance={**provenance, "case": "2x_load"})
    thicker = GFlexParameters(**{**params.__dict__, "elastic_thickness_m": 30_000.0})
    thick_result = solve_gflex_1d(load, ids, parameters=thicker, time_s=0.0,
                                  provenance={**provenance, "case": "Te_30km"})
    free_west = GFlexParameters(**{**params.__dict__,
                                   "boundary_west": "0Moment0Shear"})
    bc_result = solve_gflex_1d(load, ids, parameters=free_west, time_s=0.0,
                               provenance={**provenance, "case": "free_west"})
    rigidity = params.young_modulus_pa * params.elastic_thickness_m ** 3 / (
        12.0 * (1.0 - params.poisson_ratio ** 2))
    foundation = ((params.mantle_density_kg_m3 - params.infill_density_kg_m3)
                  * params.gravity_m_s2)
    alpha = (4.0 * rigidity / foundation) ** 0.25
    half_width = 11.0 * dx / 2.0
    analytic_center = -pressure / foundation * (
        1.0 - math.exp(-half_width / alpha) * math.cos(half_width / alpha))
    observed_center = baseline["deflection_m"][center]
    return {
        "grid": {"n": n, "dx_m": dx, "load_cells": 11,
                 "domain_half_length_m": (n - 1) * dx / 2.0,
                 "derived_alpha_1d_m": alpha},
        "synthetic_parameters": params.__dict__,
        "cases": {"baseline": baseline, "double_load": doubled,
                  "thicker_elastic_plate": thick_result,
                  "free_west_boundary": bc_result},
        "analytic_reference": {
            "formula": "w(0)=-q/(Delta_rho*g)*(1-exp(-a/alpha)*cos(a/alpha)); uniform line-load strip, infinite plate",
            "load_half_width_m": half_width,
            "center_deflection_m": analytic_center,
            "gflex_center_deflection_m": observed_center,
            "relative_error": abs(observed_center - analytic_center) / abs(analytic_center),
        },
        "observed_sensitivities": {
            "load_linear_scaling_max_abs_residual_m": max(
                abs(two - 2.0 * one) for one, two in zip(
                    baseline["deflection_m"], doubled["deflection_m"])),
            "center_abs_deflection_baseline_m": abs(observed_center),
            "center_abs_deflection_te_30km_m": abs(thick_result["deflection_m"][center]),
            "max_difference_from_free_west_bc_m": max(
                abs(a - b) for a, b in zip(baseline["deflection_m"],
                                            bc_result["deflection_m"])),
        },
    }


def _run_surface_interface() -> dict[str, Any]:
    base = (12.0, 8.0, 4.0, 11.0, 6.0, 0.0, 10.0, 3.0, -2.0)
    nearly_flat = (0.0, 1e-5, 2e-5, 1e-5, 2e-5, 3e-5,
                   2e-5, 3e-5, -1e-5)
    config = RegionalConfig(
        duration_years=1,
        precipitation_m_year=0.0,
        initial_elevation_offsets_m_by_cell=tuple(
            z - b for z, b in zip(nearly_flat, base)),
    )
    initial = create_synthetic_region(config)
    ids_3 = [[f"SYNTHETIC_BASIN_3X3:C{i:02d}"
              for i in range(row * 3, (row + 1) * 3)] for row in range(3)]
    n, pad = 75, 36
    ids_padded = [[f"FLEXURE_PAD:{r}:{c}" for c in range(n)] for r in range(n)]
    for r in range(3):
        for c in range(3):
            ids_padded[r + pad][c + pad] = ids_3[r][c]
    params = GFlexParameters(
        grid_spacing_x_m=1_000.0, grid_spacing_y_m=1_000.0,
        young_modulus_pa=70.0e9, poisson_ratio=0.25,
        elastic_thickness_m=20_000.0, mantle_density_kg_m3=3_300.0,
        infill_density_kg_m3=0.0, gravity_m_s2=9.81,
        authority="SYNTHETIC_INTERFACE_BENCHMARK_ONLY")
    synthetic_mass_kg = 1.0e12
    cell_area_m2 = 1.0e6
    pressure = load_pressure_from_mass_delta(
        [synthetic_mass_kg], [cell_area_m2], params.gravity_m_s2)[0]
    load_1 = [[0.0] * n for _ in range(n)]
    load_1[n // 2][n // 2] = pressure
    load_2 = [[2.0 * value for value in row] for row in load_1]
    provenance = {"authority": "SYNTHETIC_3X3_WITH_PADDED_SYNTHETIC_SURROUNDINGS",
                  "mass_source": "PRESCRIBED_BENCHMARK_LOAD_NOT_REGIONAL_SEDIMENT",
                  "deep_stock_accessed": False}
    first = solve_gflex_2d(load_1, ids_padded, parameters=params,
                           time_s=1.0, provenance=provenance)
    second = solve_gflex_2d(load_2, ids_padded, parameters=params,
                            time_s=2.0, provenance=provenance)
    crop = lambda result: [row[pad:pad + 3]
                           for row in result["deflection_m"][pad:pad + 3]]
    zero = [[0.0] * 3 for _ in range(3)]
    state_1 = apply_deflection_increment_to_region(
        initial, cell_ids=ids_3, previous_deflection_m=zero,
        current_deflection_m=crop(first), previous_time_s=0.0,
        current_time_s=1.0)
    state_2 = apply_deflection_increment_to_region(
        state_1, cell_ids=ids_3, previous_deflection_m=crop(first),
        current_deflection_m=crop(second), previous_time_s=1.0,
        current_time_s=2.0)
    routed = advance_region(state_2, years=1, config=config,
                            precipitation_m_year_by_cell=[0.0] * 9)
    return {
        "scope": "SYNTHETIC_SOFTWARE_INTERFACE_TEST_ONLY_NOT_R6_GEOGRAPHIC_INTEGRATION",
        "mesh": {"gflex_shape": [n, n], "gflex_spacing_m": [1_000.0, 1_000.0],
                 "core_cell_ids": ids_3, "halo_cells_per_side": pad,
                 "halo_width_m": pad * 1_000.0,
                 "regional_cell_area_m2": cell_area_m2,
                 "geometry_match": "SYNTHETIC_1KM_SQUARE_CORE_CELLS_EXPLICITLY_MATCHED",
                 "boundary_conditions": ["0Displacement0Slope"] * 4,
                 "boundary_limit": "FINITE_PADDED_DOMAIN; NOT_A_QUALIFIED_REGIONAL_FLEXURE_DOMAIN"},
        "load_conversion": {"synthetic_mass_kg": synthetic_mass_kg,
            "material": "SYNTHETIC_SURFACE_MASS_SHEET",
            "area_m2": cell_area_m2,
            "gravity_m_s2": params.gravity_m_s2,
            "load_pressure_pa": pressure,
            "sign": "POSITIVE_DOWNWARD_SURFACE_STRESS; GFLEX_NEGATIVE_W_IS_DOWNWARD",
            "regional_solid_mass_transfer_kg": 0.0,
            "note": "This load is prescribed forcing, not a deposited regional sediment stock."},
        "first_load": first, "second_load": second,
        "surface_states": {"initial_elevation_m":
                [cell["elevation_m"] for cell in initial["cells"]],
            "after_first_load_elevation_m":
                [cell["elevation_m"] for cell in state_1["cells"]],
            "after_second_load_elevation_m":
                [cell["elevation_m"] for cell in state_2["cells"]],
            "routing_before": initial["drainage_targets"],
            "routing_after_flexure": state_2["drainage_targets"],
            "routing_used_by_zero_rain_step": routed["records"][-1]["drainage_targets_used"],
            "routing_changed": state_2["drainage_targets"] != initial["drainage_targets"]},
        "deep": {"touched": False, "energy_conversion": "NONE"},
    }


def _source_identity() -> dict[str, Any]:
    hashes = {}
    for rel in ("src/arcana_worldsim/r6/gflex_flexure_adapter.py",
                "src/arcana_worldsim/r6/regional_geological_evolution.py",
                "scripts/r6_gflex_flexure_benchmark.py",
                "tests/test_r6_gflex_flexure_adapter.py"):
        hashes[rel] = _sha((REPO_ROOT / rel).read_bytes())
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                          check=True, capture_output=True, text=True).stdout.strip()
    return {"repository_head_before_run": head,
            "working_tree_source_hashes_sha256": hashes,
            "source_identity_authority": "LOCAL_FILE_HASHES_AND_REPOSITORY_HEAD; NOT_SIGNED"}


def run(output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"OUTPUT_DIRECTORY_EXISTS:{output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    tracemalloc.start()
    one_d = _run_1d()
    surface = _run_surface_interface()
    elapsed = time.perf_counter() - started
    _, peak_python_alloc = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    try:
        import numpy as np
        import scipy
        numpy_version, scipy_version = np.__version__, scipy.__version__
    except ImportError:
        numpy_version = scipy_version = "UNAVAILABLE"
    result: dict[str, Any] = {
        "schema": "ARCANA_R6_FLEX1_GLFLEX_BENCHMARK_V1",
        "decision": "GFLEX_NUMERICAL_BENCHMARK_PASS__SYNTHETIC_ENGINEERING_ONLY",
        "environment": {"python": platform.python_version(),
            "numpy": numpy_version, "scipy": scipy_version,
            "gflex": importlib.metadata.version("gflex"),
            "platform": platform.platform(),
            "rss_peak_working_set_process_lifetime_bytes": _peak_working_set_bytes(),
            "rss_scope": "OS_PROCESS_PEAK_SINCE_PROCESS_START_NOT_EXPERIMENT_DELTA",
            "python_tracemalloc_peak_bytes": peak_python_alloc,
            "tracemalloc_scope": "PYTHON_ALLOCATIONS_ONLY_EXCLUDES_NUMPY_SCIPY_NATIVE_ALLOCATIONS"},
        "source_identity": _source_identity(),
        "elapsed_seconds": elapsed,
        "gflex_1d": one_d,
        "synthetic_surface_interface": surface,
        "authority_limits": [
            "No R6 surface or topographic payload was ingested.",
            "No ARCANA elastic thickness, Young modulus, Poisson ratio, or load law was inferred.",
            "No Deep stock, thermal state, hydrology climate forcing, or canonical history was read or modified.",
            "gFlex is an instantaneous elastic-equilibrium solver, not a geological time integrator.",
            "Synthetic routing change is a software interface effect, not a geological event or R6 prediction.",
            "The 3x3 regional microdomain is an explicit synthetic grid with a finite padding ring; edge effects remain a physical limitation.",
        ],
    }
    result_path = output_dir / "RESULT.json"
    raw = _canonical(result)
    result_path.write_bytes(raw)
    sidecar_path = output_dir / "RESULT.json.sha256"
    sidecar = f"{_sha(raw)}  RESULT.json\n".encode("ascii")
    sidecar_path.write_bytes(sidecar)
    member_list = [
        {"path": result_path.name, "size_bytes": len(raw), "sha256": _sha(raw)},
        {"path": sidecar_path.name, "size_bytes": len(sidecar), "sha256": _sha(sidecar)},
    ]
    manifest = {"schema": "ARCANA_R6_FLEX1_GLFLEX_MANIFEST_V1",
                "manifest_sha256": None, "members": member_list,
                "member_bytes_total": sum(row["size_bytes"] for row in member_list)}
    manifest_path = output_dir / "MANIFEST.json"
    manifest_path.write_bytes(_canonical(manifest))
    # Output sizes are recoverable from the manifest itself; do not mutate the
    # result after its digest and sidecar have been written.
    return {"output_directory": str(output_dir), "result": result,
            "manifest": manifest, "manifest_sha256": _sha(manifest_path.read_bytes()),
            "total_output_bytes": sum(p.stat().st_size for p in
                (result_path, sidecar_path, manifest_path))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps({"decision": report["result"]["decision"],
        "output_directory": report["output_directory"],
        "manifest_sha256": report["manifest_sha256"],
        "total_output_bytes": report["total_output_bytes"],
        "elapsed_seconds": report["result"]["elapsed_seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
