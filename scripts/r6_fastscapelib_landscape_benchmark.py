#!/usr/bin/env python3
"""Small, noncanonical Fastscapelib bedrock-incision benchmark for R6.

Fastscapelib 0.3.0 is an optional external dependency. The experiment uses a
fully synthetic raster and reports topographic lowering; it does not model
sediment transport, deposition, water balance, or ARCANA geographic support.
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
import sys
import time
import tracemalloc
from typing import Any


EXPECTED_FASTSCAPELIB = "0.3.0"
N = 61
SPACING_M = 1_000.0
DT_YEARS = 500.0
N_STEPS = 20
AREA_EXPONENT = 0.5
SLOPE_EXPONENT = 1.0
BASE_K = 2.0e-5
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "outputs/r6_land1_fastscapelib_20261026_01"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _peak_working_set_bytes() -> int | None:
    if os.name != "nt":
        try:
            import resource
            value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            return int(value if sys.platform == "darwin" else value * 1024)
        except (ImportError, OSError, ValueError):
            return None
    try:
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
        if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(),
                                          ctypes.byref(counters), counters.cb):
            return None
        return int(counters.PeakWorkingSetSize)
    except (AttributeError, OSError, ValueError):
        return None


def synthetic_initial_topography(n: int = N, spacing_m: float = SPACING_M):
    """Return deterministic synthetic relief [m] and its fixed base boundary."""
    import numpy as np
    if n < 5 or not math.isfinite(spacing_m) or spacing_m <= 0:
        raise ValueError("GRID_SIZE_OR_SPACING_INVALID")
    row, col = np.mgrid[0:n, 0:n]
    northing_m = (n - 1 - row) * spacing_m
    easting_m = (col - (n - 1) / 2.0) * spacing_m
    relief = (0.012 * northing_m
              + 180.0 * np.exp(-((easting_m / 10_000.0) ** 2
                                 + ((northing_m - 30_000.0) / 18_000.0) ** 2) / 2.0))
    relief[-1, :] = 0.0
    return relief.astype(np.float64), row, col


def run_landscape(*, k_coef: float = BASE_K, steps: int = N_STEPS,
                  initial_elevation=None, dt_years: float = DT_YEARS,
                  spacing_m: float = SPACING_M) -> dict[str, Any]:
    """Evolve synthetic bedrock elevation with Fastscapelib's 2-D SPL solver.

    Returns a height field and per-run diagnostics. The erosion volume is an
    elevation-lowering diagnostic (sum(dz * nodal_area)), not a sediment
    inventory or a claim of conserved sediment delivery/deposition.
    """
    import numpy as np
    import fastscapelib as fs

    if importlib.metadata.version("fastscapelib") != EXPECTED_FASTSCAPELIB:
        raise RuntimeError("FASTSCAPELIB_VERSION_MISMATCH")
    if (not math.isfinite(k_coef) or k_coef < 0 or steps < 0
            or not math.isfinite(dt_years) or dt_years <= 0
            or not math.isfinite(spacing_m) or spacing_m <= 0):
        raise ValueError("EROSION_CONFIGURATION_INVALID")
    if initial_elevation is None:
        initial, _, _ = synthetic_initial_topography(spacing_m=spacing_m)
    else:
        initial = np.asarray(initial_elevation, dtype=np.float64).copy()
        if initial.ndim != 2 or min(initial.shape) < 5 or not np.isfinite(initial).all():
            raise ValueError("CHECKPOINT_TOPOGRAPHY_INVALID")
    ny, nx = initial.shape
    grid = fs.RasterGrid(
        [ny, nx], [spacing_m, spacing_m],
        [fs.NodeStatus.CORE, fs.NodeStatus.CORE,
         fs.NodeStatus.FIXED_VALUE, fs.NodeStatus.CORE])
    flow_graph = fs.FlowGraph(grid, [fs.SingleFlowRouter()])
    eroder = fs.SPLEroder(flow_graph, k_coef=k_coef,
                          area_exp=AREA_EXPONENT, slope_exp=SLOPE_EXPONENT,
                          tolerance=1.0e-5)
    elevation = initial.copy()
    node_areas = np.asarray(grid.nodes_areas(), dtype=np.float64)
    if node_areas.shape != elevation.shape or not np.isfinite(node_areas).all():
        raise RuntimeError("FASTSCAPELIB_NODE_AREAS_INVALID")
    max_step_lowering_m = 0.0
    max_corrections = 0
    step_diagnostics = []
    for step in range(steps):
        # Rebuild routes from the current relief every step; don't assume a
        # fixed drainage graph while erosion changes the surface.
        flow_graph.update_routes(elevation)
        drainage_area_m2 = np.asarray(flow_graph.accumulate(1.0), dtype=np.float64)
        if drainage_area_m2.shape != elevation.shape or not np.isfinite(drainage_area_m2).all():
            raise RuntimeError("FASTSCAPELIB_DRAINAGE_AREA_INVALID")
        lowering = np.asarray(eroder.erode(elevation, drainage_area_m2, dt_years),
                              dtype=np.float64)
        if (lowering.shape != elevation.shape or not np.isfinite(lowering).all()
                or np.any(lowering < 0.0)):
            raise RuntimeError("FASTSCAPELIB_SPL_OUTPUT_INVALID")
        elevation = elevation - lowering
        if not np.array_equal(elevation[-1, :], initial[-1, :]):
            raise RuntimeError("FIXED_BASELEVEL_BOUNDARY_CHANGED")
        max_step_lowering_m = max(max_step_lowering_m, float(np.max(lowering)))
        max_corrections += int(eroder.n_corr)
        step_diagnostics.append({
            "step": step + 1,
            "elapsed_model_time_years": (step + 1) * dt_years,
            "max_lowering_m": float(np.max(lowering)),
            "lowered_node_count": int(np.count_nonzero(lowering)),
            "eroder_slope_correction_node_count": int(eroder.n_corr),
        })
    # Last graph is the routing of the pre-final surface. Recompute for the
    # output state before reporting drainage diagnostics.
    flow_graph.update_routes(elevation)
    final_drainage_area = np.asarray(flow_graph.accumulate(1.0), dtype=np.float64)
    dz = initial - elevation
    erosion_volume_diagnostic_m3 = float(np.sum(dz * node_areas))
    if not np.isfinite(elevation).all() or erosion_volume_diagnostic_m3 < -1.0e-9:
        raise RuntimeError("LANDSCAPE_FINAL_STATE_INVALID")
    return {
        "elevation_m": elevation,
        "initial_elevation_m": initial,
        "drainage_area_m2": final_drainage_area,
        "diagnostics": {
            "grid_shape": [ny, nx],
            "grid_spacing_m": [spacing_m, spacing_m],
            "domain_span_m": [(nx - 1) * spacing_m, (ny - 1) * spacing_m],
            "fixed_baselevel": "BOTTOM_ROW_FIXED_VALUE; OTHER_EDGES_CORE",
            "router": "SingleFlowRouter; routes recomputed each time step",
            "eroder": "SPLEroder; implicit stream-power bedrock incision",
            "steps": steps,
            "dt_years": dt_years,
            "elapsed_model_time_years": steps * dt_years,
            "k_coef": k_coef,
            "area_exponent": AREA_EXPONENT,
            "slope_exponent": SLOPE_EXPONENT,
            "max_step_lowering_m": max_step_lowering_m,
            "max_total_lowering_m": float(np.max(dz)),
            "lowered_nodes": int(np.count_nonzero(dz > 0.0)),
            "final_relief_range_m": [float(np.min(elevation)), float(np.max(elevation))],
            "max_drainage_area_m2": float(np.max(final_drainage_area)),
            "eroder_correction_count_total": max_corrections,
            "topographic_lowering_volume_diagnostic_m3": erosion_volume_diagnostic_m3,
            "volume_semantics": "DIAGNOSTIC_HEIGHT_INTEGRAL_NOT_A_TRACKED_SEDIMENT_MASS_OR_EXPORT",
            "deposition_supported": False,
        },
        "step_diagnostics": step_diagnostics,
    }


def _source_identity() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    tracked = [
        "scripts/r6_fastscapelib_landscape_benchmark.py",
        "tests/test_r6_fastscapelib_landscape_benchmark.py",
        "src/arcana_worldsim/r6/geological_surface_microdomain.py",
        "src/arcana_worldsim/r6/regional_geological_evolution.py",
        "src/arcana_worldsim/r6/hydrology_surface_coupling.py",
        "src/arcana_worldsim/r6/gflex_flexure_adapter.py",
    ]
    hashes = {rel: _sha((root / rel).read_bytes()) for rel in tracked}
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        head = "UNKNOWN_GIT_HEAD"
    return {"repository_head_before_run": head,
            "source_sha256": hashes,
            "identity_authority": "LOCAL_GIT_HEAD_AND_FILE_HASHES_NOT_SIGNED"}


def run_benchmark(output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"OUTPUT_DIRECTORY_EXISTS:{output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)
    import numpy as np
    import fastscapelib

    if fastscapelib.__version__ != EXPECTED_FASTSCAPELIB:
        raise RuntimeError("FASTSCAPELIB_VERSION_MISMATCH")
    initial, _, _ = synthetic_initial_topography()
    cases = {}
    tracemalloc.start()
    started = time.perf_counter()
    for label, k in (("half_k", BASE_K / 2), ("baseline", BASE_K),
                     ("double_k", BASE_K * 2)):
        result = run_landscape(k_coef=k, initial_elevation=initial)
        cases[label] = {
            "k_coef": k,
            "diagnostics": result["diagnostics"],
            "final_elevation_m": result["elevation_m"].tolist(),
            "final_drainage_area_m2": result["drainage_area_m2"].tolist(),
            "step_diagnostics": result["step_diagnostics"],
        }
    baseline = run_landscape(k_coef=BASE_K, initial_elevation=initial)
    reproducibility_exact = bool(np.array_equal(
        baseline["elevation_m"], np.asarray(cases["baseline"]["final_elevation_m"])))
    first = run_landscape(k_coef=BASE_K, steps=N_STEPS // 2,
                          initial_elevation=initial)
    continued = run_landscape(k_coef=BASE_K, steps=N_STEPS - N_STEPS // 2,
                              initial_elevation=first["elevation_m"])
    restart_max_abs_diff_m = float(np.max(np.abs(
        continued["elevation_m"] - baseline["elevation_m"])))
    elapsed = time.perf_counter() - started
    _, py_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    report = {
        "schema": "ARCANA_R6_LAND1_FASTSCAPELIB_BENCHMARK_V1",
        "decision": "FASTSCAPELIB_SYNTHETIC_SPL_BENCHMARK_PASS__NO_ARCANA_GEOLOGY_CLAIM",
        "source_identity": _source_identity(),
        "environment": {"python": platform.python_version(),
                        "numpy": np.__version__,
                        "fastscapelib": fastscapelib.__version__,
                        "peak_process_working_set_bytes": _peak_working_set_bytes(),
                        "working_set_semantics": "PROCESS_LIFETIME_PEAK_NOT_RUN_DELTA",
                        "python_tracemalloc_peak_bytes": py_peak,
                        "tracemalloc_semantics": "PYTHON_ALLOCATIONS_ONLY"},
        "synthetic_experiment": {
            "topography": "0.012 north-south planar slope plus 180 m Gaussian dome; bottom row fixed at 0 m",
            "grid_ids": {"scheme": "FASTSCAPELIB_SYNTHETIC_RASTER_NODE_ROW_COL",
                         "shape": [N, N], "coordinate_units": "m",
                         "node_id_format": "SYNTHETIC_RASTER:R{row:03d}:C{col:03d}",
                         "origin": "southwest corner; spacing 1000 m"},
            "process": "bedrock channel incision via stream power; no uplift, no water-balance state, no sediment storage/transport/deposition",
            "parameters": {"dt_years": DT_YEARS, "steps": N_STEPS,
                           "K_values": [BASE_K / 2, BASE_K, BASE_K * 2],
                           "m_area_exp": AREA_EXPONENT, "n_slope_exp": SLOPE_EXPONENT,
                           "K_authority": "SYNTHETIC_BENCHMARK_PARAMETER_NOT_CALIBRATED_FOR_ARCANA",
                           "boundary": "BOTTOM_ROW_FIXED_VALUE; other boundaries CORE"},
            "initial_elevation_m": initial.tolist(),
            "cases": cases,
            "repeat_run_bitwise_equal": reproducibility_exact,
            "continuous_vs_10_plus_10_restart_max_abs_difference_m": restart_max_abs_diff_m,
            "restart_scope": "ELEVATION_ONLY_STATE; router_and_eroder_reconstructed_from_exact_parameters",
            "elapsed_benchmark_seconds": elapsed,
            "volume_and_mass": "Topographic lowering integral is diagnostic; Fastscapelib Python SPL does not provide a tracked sediment inventory or deposition in this API.",
        },
        "authority_limits": [
            "All coordinates, topography, parameters, and material labels are synthetic; no R6 geodata or material identities were ingested.",
            "Fastscapelib 0.3.0 SPL erodes bedrock elevation but does not track sediment mass through storage, transport, export, or deposition.",
            "No equivalence to R6 hydrology or geological surface models is asserted; equations, state variables and boundary treatment differ.",
            "No coupling to gFlex was executed; only a separate adapter contract is proposed in the report.",
            "No physical or canonical ARCANA history authority is produced.",
        ],
    }
    raw = _canonical(report)
    result_path = output_dir / "RESULT.json"
    result_path.write_bytes(raw)
    sidecar = f"{_sha(raw)}  RESULT.json\n".encode("ascii")
    sidecar_path = output_dir / "RESULT.json.sha256"
    sidecar_path.write_bytes(sidecar)
    members = [{"path": result_path.name, "bytes": len(raw), "sha256": _sha(raw)},
               {"path": sidecar_path.name, "bytes": len(sidecar), "sha256": _sha(sidecar)}]
    manifest = {"schema": "ARCANA_R6_LAND1_FASTSCAPELIB_MANIFEST_V1",
                "manifest_sha256": None, "members": members,
                "member_bytes_total": sum(member["bytes"] for member in members)}
    manifest_path = output_dir / "MANIFEST.json"
    manifest_path.write_bytes(_canonical(manifest))
    return {"result": report, "manifest": manifest,
            "manifest_sha256": _sha(manifest_path.read_bytes()),
            "output_bytes": sum(p.stat().st_size for p in
                                 (result_path, sidecar_path, manifest_path))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run_benchmark(args.output)
    print(json.dumps({"decision": result["result"]["decision"],
                      "output_directory": str(args.output),
                      "manifest_sha256": result["manifest_sha256"],
                      "output_bytes": result["output_bytes"],
                      "elapsed_benchmark_seconds": result["result"]["synthetic_experiment"]["elapsed_benchmark_seconds"],
                      "repeat_run_bitwise_equal": result["result"]["synthetic_experiment"]["repeat_run_bitwise_equal"],
                      "restart_max_abs_difference_m": result["result"]["synthetic_experiment"]["continuous_vs_10_plus_10_restart_max_abs_difference_m"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
