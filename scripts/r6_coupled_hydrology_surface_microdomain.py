from __future__ import annotations

import argparse
import hashlib
import json
import time
import tracemalloc
from pathlib import Path
from typing import Any

from arcana_worldsim.r6.geological_surface_microdomain import load_verified_r6_initial_columns
from arcana_worldsim.r6.hydrology_surface_coupling import run_experiment_suite


DEFAULT_SOURCE = Path("outputs/r6_experimental_multiphysics/MATERIAL_RHEOLOGY_PROVIDER_20261025_03")
DEFAULT_OUTPUT = Path("outputs/r6_experimental_multiphysics/COUPLED_HYDROLOGY_SURFACE_20261025_01")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def run(source_dir: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence: {output_dir}")
    started = time.perf_counter()
    tracemalloc.start()
    states, source_identity = load_verified_r6_initial_columns(source_dir)
    result = run_experiment_suite(states, source_identity)
    result["measurements"] = {
        "elapsed_seconds_before_serialization": time.perf_counter() - started,
        "python_tracemalloc_peak_bytes": tracemalloc.get_traced_memory()[1],
        "rss_measured": False,
    }
    tracemalloc.stop()

    output_dir.mkdir(parents=True, exist_ok=False)
    payload = _canonical(result)
    digest = hashlib.sha256(payload).hexdigest()
    result_path = output_dir / "RESULT.json"
    sidecar_path = output_dir / "RESULT.json.sha256"
    result_path.write_bytes(payload)
    sidecar = f"{digest}  RESULT.json\n".encode("ascii")
    sidecar_path.write_bytes(sidecar)
    manifest = {
        "schema": "ARCANA_R6_COUPLED_HYDROLOGY_SURFACE_MANIFEST_V1",
        "manifest_self_hash": None,
        "result": {"path": "RESULT.json", "size_bytes": len(payload), "sha256": digest},
        "sidecar": {"path": "RESULT.json.sha256", "size_bytes": len(sidecar),
                    "sha256": hashlib.sha256(sidecar).hexdigest()},
    }
    manifest_path = output_dir / "MANIFEST.json"
    manifest_path.write_bytes(_canonical(manifest))
    return {"result": result, "manifest": manifest,
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a short noncanonical R6 hydrology/surface microdomain")
    parser.add_argument("--source-result-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        outcome = run(args.source_result_dir, args.output_dir)
    except Exception as exc:
        parser.exit(2, f"coupled hydrology/surface experiment failed closed: {type(exc).__name__}: {exc}\n")
    cases = outcome["result"]["hydrology_scenarios"]
    print(json.dumps({
        "status": "NONCANONICAL_HYDROLOGY_SURFACE_EXPERIMENT_COMPLETE",
        "output_dir": str(args.output_dir),
        "manifest_sha256": outcome["manifest_sha256"],
        "elapsed_seconds": outcome["result"]["measurements"]["elapsed_seconds_before_serialization"],
        "scenario_summary": {
            name: {
                "water_residual_m3": case["water_balance"]["residual_m3"],
                "sediment_residual_kg": case["sediment_balance"]["residual_kg"],
                "outlet_water_m3": case["water_balance"]["outlet_export_m3"],
                "outlet_sediment_kg": case["sediment_balance"]["outlet_sediment_export_kg"],
            } for name, case in cases.items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
