from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
import tracemalloc
from typing import Any

from arcana_worldsim.r6.functional_development import NodeMaterial, ReducedState
from arcana_worldsim.r6.geological_surface_microdomain import (
    SUPPORTS, load_verified_r6_initial_columns,
)
from arcana_worldsim.r6.unified_multiphysics_microdomain import (
    UnifiedConfig, continue_unified_microdomain, parse_unified_checkpoint,
    run_experiment_matrix, run_unified_microdomain, serialize_unified_checkpoint,
    unified_states_from_checkpoint, verify_unified_checkpoint,
)


DEFAULT_SOURCE = Path("outputs/r6_experimental_multiphysics/MATERIAL_RHEOLOGY_PROVIDER_20261025_03")
DEFAULT_OUTPUT = Path("outputs/r6_experimental_multiphysics/UNIFIED_MULTIPHYSICS_MICRODOMAIN_20261025_01")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _state_from_payload(payload: dict[str, Any]) -> ReducedState:
    return ReducedState(
        time_s=float(payload["time_s"]), initial_width_m=float(payload["initial_width_m"]),
        width_m=float(payload["width_m"]), initial_crust_m=float(payload["initial_crust_m"]),
        initial_lithosphere_m=float(payload["initial_lithosphere_m"]), crust_m=float(payload["crust_m"]),
        lithosphere_m=float(payload["lithosphere_m"]), beta=float(payload["beta"]),
        accumulated_strain=float(payload["accumulated_strain"]),
        crust_fraction=float(payload["crust_fraction"]),
        material_coordinate=tuple(float(x) for x in payload["material_coordinate"]),
        temperature_k=tuple(float(x) for x in payload["temperature_k"]),
        materials=tuple(NodeMaterial(**row) for row in payload["materials"]),
        surface_temperature_k=float(payload["surface_temperature_k"]),
        base_temperature_k=float(payload["base_temperature_k"]),
    )


def run(source_dir: Path, output_dir: Path, *, checkpoint_input: Path | None = None,
        segment_years: float | None = None) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {output_dir}")
    started = time.perf_counter()
    tracemalloc.start()
    payloads, source_identity = load_verified_r6_initial_columns(source_dir)
    config = UnifiedConfig()
    if checkpoint_input is not None:
        if segment_years is None:
            raise ValueError("--checkpoint-in requires --segment-years")
        checkpoint_payload = json.loads(checkpoint_input.read_text(encoding="utf-8"))
        if isinstance(checkpoint_payload, dict) and "cases" in checkpoint_payload:
            checkpoint_payload = checkpoint_payload["cases"]["BASELINE"]["continuation"]
        checkpoint = parse_unified_checkpoint(_canonical(checkpoint_payload))
        saved = verify_unified_checkpoint(checkpoint)
        if _canonical(saved["source_identity"]) != _canonical(source_identity):
            raise ValueError("checkpoint source identity differs from reverified source input")
        case = continue_unified_microdomain(
            checkpoint, source_identity, config=config, segment_years=segment_years)
        matrix = {"BASELINE": case}
        input_binding = "CONTINUATION_FROM_SHA256_CHECKED_CHECKPOINT_AND_REVERIFIED_SOURCE_IDENTITY"
    else:
        states = {support: _state_from_payload(payloads[support]) for support in SUPPORTS}
        if segment_years is None:
            matrix = run_experiment_matrix(states, source_identity, config=config)
            input_binding = "INITIAL_STATES_REHYDRATED_FROM_HASH_VERIFIED_PAYLOADS"
        else:
            matrix = {"BASELINE": run_unified_microdomain(
                states, source_identity, config=config, segment_years=segment_years)}
            input_binding = "INITIAL_STATES_REHYDRATED_FROM_HASH_VERIFIED_PAYLOADS_PARTIAL_SEGMENT"
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    compute_elapsed = time.perf_counter() - started
    result = {
        "schema": "ARCANA_R6_UNIFIED_MULTIPHYSICS_RESULT_V1",
        "source_identity": source_identity,
        "configuration": {
            "duration_years": config.duration_years,
            "external_step_years": config.external_step_years,
            "hydrology_dt_seconds": config.hydrology_dt_seconds,
            "segment_years": segment_years,
            "input_binding": input_binding,
        },
        "cases": matrix,
        "measurements": {
            "compute_elapsed_seconds_including_source_verification_and_cases": compute_elapsed,
            "python_tracemalloc_peak_bytes": peak,
            "rss_measured": False,
        },
    }
    write_started = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=False)
    payload = _canonical(result)
    digest = hashlib.sha256(payload).hexdigest()
    sidecar = f"{digest}  RESULT.json\n".encode("ascii")
    (output_dir / "RESULT.json").write_bytes(payload)
    (output_dir / "RESULT.json.sha256").write_bytes(sidecar)
    checkpoint_bytes = serialize_unified_checkpoint(matrix["BASELINE"]["continuation"])
    checkpoint_digest = hashlib.sha256(checkpoint_bytes).hexdigest()
    checkpoint_sidecar = f"{checkpoint_digest}  BASELINE_CONTINUATION.json\n".encode("ascii")
    (output_dir / "BASELINE_CONTINUATION.json").write_bytes(checkpoint_bytes)
    (output_dir / "BASELINE_CONTINUATION.json.sha256").write_bytes(checkpoint_sidecar)
    manifest = {
        "schema": "ARCANA_R6_UNIFIED_MULTIPHYSICS_MANIFEST_V1",
        "result": {"path": "RESULT.json", "size_bytes": len(payload), "sha256": digest},
        "sidecar": {"path": "RESULT.json.sha256", "size_bytes": len(sidecar),
                    "sha256": hashlib.sha256(sidecar).hexdigest()},
        "continuation_checkpoint": {
            "path": "BASELINE_CONTINUATION.json", "size_bytes": len(checkpoint_bytes),
            "sha256": checkpoint_digest,
        },
        "continuation_checkpoint_sidecar": {
            "path": "BASELINE_CONTINUATION.json.sha256", "size_bytes": len(checkpoint_sidecar),
            "sha256": hashlib.sha256(checkpoint_sidecar).hexdigest(),
        },
        "completion": "ALL_DECLARED_CASES_COMPLETED_BEFORE_MANIFEST_WRITE",
    }
    manifest_bytes = _canonical(manifest)
    (output_dir / "MANIFEST.json").write_bytes(manifest_bytes)
    write_elapsed = time.perf_counter() - write_started
    output_bytes = sum(path.stat().st_size for path in output_dir.iterdir() if path.is_file())
    return {"output_dir": str(output_dir), "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "output_bytes": output_bytes,
            "measurements": {**result["measurements"],
                             "serialization_and_write_seconds": write_elapsed,
                             "total_elapsed_seconds": time.perf_counter() - started},
            "result": result}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a short shared-clock noncanonical ARCANA multiphysics microdomain")
    parser.add_argument("--source-result-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checkpoint-in", type=Path,
                        help="verified continuation JSON or a prior RESULT.json containing BASELINE.continuation")
    parser.add_argument("--segment-years", type=float,
                        help="number of planned external years to advance; the run configuration remains fixed")
    args = parser.parse_args()
    try:
        outcome = run(args.source_result_dir, args.output_dir,
                      checkpoint_input=args.checkpoint_in, segment_years=args.segment_years)
    except Exception as exc:
        parser.exit(2, f"unified multiphysics run failed closed: {type(exc).__name__}: {exc}\n")
    summary = {}
    for name, case in outcome["result"]["cases"].items():
        summary[name] = {
            "steps": len(case["steps"]),
            "end_time_s": case["final"]["time_s_by_support"],
            "water_residual_m3": case["integrated_balances"]["water"]["residual_m3"],
            "sediment_residual_kg": case["integrated_balances"]["sediment"]["residual_kg"],
            "geometry_residual_m3": case["integrated_balances"]["geometry"]["residual_m3"],
            "deep_residual_j": case["integrated_balances"]["deep"]["residual_j"],
        }
    print(json.dumps({"status": "UNIFIED_MULTIPHYSICS_MICRODOMAIN_COMPLETE",
                      "output_dir": outcome["output_dir"],
                      "manifest_sha256": outcome["manifest_sha256"],
                      "output_bytes": outcome["output_bytes"],
                      "measurements": outcome["measurements"],
                      "case_summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
