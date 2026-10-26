#!/usr/bin/env python3
"""Run a tiny synthetic Fastscapelib-SPL to ARCANA-R6 coupling experiment."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys
import time
import tracemalloc
from typing import Any

import numpy as np

from src.arcana_worldsim.r6.fastscapelib_surface_coupling import (
    SYNTHETIC_SPL_K,
    continue_coupled_segment,
    run_coupled_segment,
    verify_coupling_checkpoint,
)
from src.arcana_worldsim.r6.regional_geological_evolution import _sha as _r6_sha


DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "outputs/r6_surf2_fastscapelib_20261026_01"


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _source_identity() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    members = [
        "scripts/r6_surf2_fastscapelib_r6_coupling.py",
        "tests/test_r6_surf2_fastscapelib_r6_coupling.py",
        "src/arcana_worldsim/r6/fastscapelib_surface_coupling.py",
        "scripts/r6_fastscapelib_landscape_benchmark.py",
        "src/arcana_worldsim/r6/regional_geological_evolution.py",
        "src/arcana_worldsim/r6/gflex_flexure_adapter.py",
    ]
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        head = "UNKNOWN_GIT_HEAD"
    return {"repository_head_before_run": head,
            "source_sha256": {name: _sha_bytes((root / name).read_bytes()) for name in members},
            "identity_semantics": "LOCAL_COMMIT_AND_FILE_HASHES_NOT_SIGNED"}


def run_experiment(*, output_dir: Path, years: int = 2,
                   k_coef: float = SYNTHETIC_SPL_K,
                   precipitation_m_year: float = 0.15) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"OUTPUT_DIRECTORY_EXISTS:{output_dir}")
    if years < 1:
        raise ValueError("YEARS_MUST_BE_POSITIVE")
    import fastscapelib
    if importlib.metadata.version("fastscapelib") != "0.3.0":
        raise RuntimeError("FASTSCAPELIB_VERSION_MISMATCH")

    tracemalloc.start()
    started = time.perf_counter()
    control = run_coupled_segment(years=years, planned_years=years,
                                  k_coef=0.0,
                                  precipitation_m_year=precipitation_m_year)
    coupled = run_coupled_segment(years=years, planned_years=years,
                                  k_coef=k_coef,
                                  precipitation_m_year=precipitation_m_year)
    first = run_coupled_segment(years=1, planned_years=years, k_coef=k_coef,
                                precipitation_m_year=precipitation_m_year)
    checkpoint = verify_coupling_checkpoint(first["continuation_checkpoint"])
    resumed = continue_coupled_segment(checkpoint, years=years - 1,
                                       k_coef=k_coef,
                                       precipitation_m_year=precipitation_m_year)
    restart_same = (_canonical(coupled["regional_state"])
                    == _canonical(resumed["regional_state"])
                    and _canonical(coupled["final"]["fine_bedrock_m"])
                    == _canonical(resumed["final"]["fine_bedrock_m"]))
    restart_diff = float(np.max(np.abs(
        np.asarray(coupled["final"]["fine_bedrock_m"])
        - np.asarray(resumed["final"]["fine_bedrock_m"]))))
    elapsed = time.perf_counter() - started
    _, python_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Reuse the already-reviewed process-lifetime RSS helper from LAND-1.
    from scripts.r6_fastscapelib_landscape_benchmark import _peak_working_set_bytes

    source = _source_identity()
    report = {
        "schema": "ARCANA_R6_SURF2_FASTSCAPELIB_R6_RUN_V1",
        "decision": "SURF2_COUPLED_EXPERIMENT_PASS_SYNTHETIC_ONLY",
        "source_identity": source,
        "environment": {"python": platform.python_version(),
                        "numpy": np.__version__,
                        "fastscapelib": fastscapelib.__version__,
                        "peak_process_working_set_bytes": _peak_working_set_bytes(),
                        "working_set_semantics": "PROCESS_LIFETIME_PEAK_NOT_EXPERIMENT_DELTA",
                        "python_tracemalloc_peak_bytes": python_peak,
                        "tracemalloc_semantics": "PYTHON_ALLOCATIONS_ONLY"},
        "configuration": {"years": years, "SPL_K_per_year": k_coef,
                          "SPL_m": 0.5, "SPL_n": 1.0,
                          "SPL_dt_years": 1.0,
                          "R6_annual_precipitation_m_year": precipitation_m_year,
                          "R6_substrate_detachment": "DISABLED_TO_PREVENT_DOUBLE_COUNTING",
                          "synthetic_density_kg_m3": 2700.0,
                          "scope": "SYNTHETIC_ENGINEERING_ONLY"},
        "elapsed_seconds": elapsed,
        "restart": {"continuous_vs_1_plus_rest": restart_same,
                    "fine_bedrock_max_abs_difference_m": restart_diff,
                    "checkpoint_sha256": checkpoint["checkpoint_sha256"],
                    "checkpoint_claim": "INTEGRITY_ONLY_NOT_AUTHENTICATED"},
        "no_erosion_control": control,
        "spl_enabled_coupled_case": coupled,
        "authority_limits": coupled["authority_limits"],
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    result_path = output_dir / "RESULT.json"
    result_raw = _canonical(report)
    result_path.write_bytes(result_raw)
    sidecar_raw = f"{_sha_bytes(result_raw)}  RESULT.json\n".encode("ascii")
    (output_dir / "RESULT.json.sha256").write_bytes(sidecar_raw)
    members = []
    for path in (result_path, output_dir / "RESULT.json.sha256"):
        raw = path.read_bytes()
        members.append({"path": path.name, "bytes": len(raw), "sha256": _sha_bytes(raw)})
    manifest = {"schema": "ARCANA_R6_SURF2_MANIFEST_V1", "manifest_sha256": None,
                "members": members, "member_bytes_total": sum(x["bytes"] for x in members)}
    manifest_raw = _canonical(manifest)
    (output_dir / "MANIFEST.json").write_bytes(manifest_raw)
    return {"report": report, "manifest_sha256": _sha_bytes(manifest_raw),
            "output_bytes": sum((output_dir / name).stat().st_size for name in
                                 ("RESULT.json", "RESULT.json.sha256", "MANIFEST.json"))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--years", type=int, default=2)
    args = parser.parse_args()
    result = run_experiment(output_dir=args.output, years=args.years)
    print(json.dumps({"decision": result["report"]["decision"],
                      "output_directory": str(args.output),
                      "manifest_sha256": result["manifest_sha256"],
                      "output_bytes": result["output_bytes"],
                      "elapsed_seconds": result["report"]["elapsed_seconds"],
                      "restart": result["report"]["restart"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
