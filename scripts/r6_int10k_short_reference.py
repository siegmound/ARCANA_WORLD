"""Run a bounded INT10K E1 legacy reference using only qualified original inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
from time import perf_counter

from arcana_worldsim.r6.geological_surface_microdomain import (
    SUPPORTS, load_verified_r6_initial_columns,
)
from arcana_worldsim.r6.int10k_short_reference import (
    ShortReferenceConfig, run_short_reference,
)
from arcana_worldsim.r6.unified_multiphysics_microdomain import _state_from_payload


SOURCE_HASHES = {
    "RESULT.json": "24f492ad9861a25369af42b513eb1a971007ef11571f6dc5ab5140729cc10fd5",
    "MANIFEST.json": "a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21",
    "RESULT.json.sha256": "8eab8b24f21088e3de82254f3d4929c61a7ed8a341593e3a4cbbafcc4bca2ce0",
}


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def main() -> int:
    ap = argparse.ArgumentParser(description="SHORT 3/10y reference; NO 10000y")
    ap.add_argument("--input-dir", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--years", required=True, type=int, choices=(3, 10))
    ap.add_argument("--split-at", required=True, type=int)
    args = ap.parse_args()
    case = ShortReferenceConfig(years=args.years, split_at=args.split_at)
    case.validate()

    src = args.input_dir.resolve(strict=True)
    out = args.output_dir.resolve()
    if (out.exists() or out == src or src in out.parents or
            "ARCANA_WORLD_EVIDENCE" not in out.parts):
        ap.error("OUTPUT_NOT_NEW_EXTERNAL_EVIDENCE_DIRECTORY")
    input_before = {name: _digest(src / name) for name in SOURCE_HASHES}
    if input_before != SOURCE_HASHES:
        ap.error("ORIGINAL_INPUT_HASH_MISMATCH")
    payloads, identity = load_verified_r6_initial_columns(src)
    states = {support: _state_from_payload(payloads[support]) for support in SUPPORTS}

    started = perf_counter()
    result = run_short_reference(states, identity, config=case)
    elapsed = perf_counter() - started
    if {name: _digest(src / name) for name in SOURCE_HASHES} != input_before:
        ap.error("ORIGINAL_INPUTS_CHANGED_DURING_REFERENCE")
    # No evidence directory is created until all numerical/identity comparisons PASS.
    out.mkdir(parents=True, exist_ok=False)
    _write_new(out / "RESULT.json", _json_bytes(result))
    summary = {
        "schema": "ARCANA_R6_INT10K_SHORT_REFERENCE_REPORT_V1",
        "status": "PASS_SHORT_REFERENCE_PARITY",
        "source_identity": identity,
        "source_file_sha256": input_before,
        "planned_years": case.years,
        "split_at_year": case.split_at,
        "result_sha256": _digest(out / "RESULT.json"),
        "wall_seconds_including_reference_calls": elapsed,
        "rss_peak_process_bytes_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "rss_is_not_process_tree_measurement": True,
        "external_solver_executed": False,
        "world_history_production_authorized": False,
        "arcana_forward_authorized": False,
    }
    _write_new(out / "REPORT.json", _json_bytes(summary))
    manifest = {
        "schema": "ARCANA_R6_INT10K_SHORT_REFERENCE_MANIFEST_V1",
        "completion": "ALL_COMPARISONS_PASS",
        "members": [{"path": name, "sha256": _digest(out / name),
                     "byte_length": (out / name).stat().st_size}
                    for name in ("RESULT.json", "REPORT.json")],
    }
    _write_new(out / "MANIFEST.json", _json_bytes(manifest))
    print(json.dumps({"status": summary["status"], "output": str(out),
                      "years": case.years, "split_at": case.split_at,
                      "manifest_sha256": _digest(out / "MANIFEST.json"),
                      "wall_seconds": elapsed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
