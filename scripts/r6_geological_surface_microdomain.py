from __future__ import annotations

import argparse
import hashlib
import json
import time
import tracemalloc
from pathlib import Path
from typing import Any

from arcana_worldsim.r6.geological_surface_microdomain import (
    SurfaceConfig,
    load_verified_r6_initial_columns,
    run_surface_microdomain,
    write_result,
)


DEFAULT_SOURCE = Path("outputs/r6_experimental_multiphysics/MATERIAL_RHEOLOGY_PROVIDER_20261025_03")
DEFAULT_OUTPUT = Path("outputs/r6_experimental_multiphysics/GEOLOGICAL_SURFACE_MICRODOMAIN_20261025_01")


def _current_rss_bytes() -> int | None:
    try:
        import psutil  # optional observation only; not a runtime dependency
        return int(psutil.Process().memory_info().rss)
    except (ImportError, OSError):
        return None


def run(source_dir: Path, output_dir: Path) -> dict[str, Any]:
    started = time.perf_counter()
    rss_start = _current_rss_bytes()
    tracemalloc.start()
    states, identity = load_verified_r6_initial_columns(source_dir)
    result = run_surface_microdomain(states, identity)
    rss_end = _current_rss_bytes()
    result["measurements"] = {
        "elapsed_seconds_before_serialization": time.perf_counter() - started,
        "python_tracemalloc_peak_bytes": tracemalloc.get_traced_memory()[1],
        "process_rss_start_bytes": rss_start,
        "process_rss_end_bytes": rss_end,
        "process_rss_observation_available": rss_start is not None and rss_end is not None,
        "process_rss_method": "PSUTIL_INSTANTANEOUS" if rss_start is not None and rss_end is not None
        else "UNAVAILABLE_PSUTIL_NOT_INSTALLED",
        "process_rss_peak_measured": False,
    }
    tracemalloc.stop()
    manifest = write_result(result, output_dir)
    return {"result": result, "manifest": manifest,
            "result_sha256": manifest["result"]["sha256"],
            "manifest_sha256": hashlib.sha256(
                (output_dir / "MANIFEST.json").read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a short noncanonical R6 geological surface microdomain")
    parser.add_argument("--source-result-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        written = run(args.source_result_dir, args.output_dir)
    except Exception as exc:
        parser.exit(2, f"surface microdomain failed closed: {type(exc).__name__}: {exc}\n")
    print(json.dumps({
        "status": "NONCANONICAL_SURFACE_MICRODOMAIN_COMPLETE",
        "output_dir": str(args.output_dir),
        "result_sha256": written["result_sha256"],
        "manifest_sha256": written["manifest_sha256"],
        "elapsed_seconds": written["result"]["measurements"]["elapsed_seconds_before_serialization"],
        "mass_balance_residual_kg": written["result"]["mass_balance_residual_kg"],
        "surface_volume_change_m3": (written["result"]["final_surface_volume_m3"]
                                      - written["result"]["initial_surface_volume_m3"]),
        "steps": len(written["result"]["steps"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
