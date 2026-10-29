"""Capture complete E1 short-reference records and real split checkpoint."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))

from arcana_worldsim.r6.geological_surface_microdomain import (
    SUPPORTS, load_verified_r6_initial_columns,
)
from arcana_worldsim.r6.int10k_full_history_oracle import (
    capture_full_history_oracle, write_new_oracle_bundle,
)
from arcana_worldsim.r6.int10k_short_reference import (
    ShortReferenceConfig, verify_source_bundle,
)
from arcana_worldsim.r6.unified_multiphysics_microdomain import _state_from_payload


SOURCE_HASHES = {
    "RESULT.json": "24f492ad9861a25369af42b513eb1a971007ef11571f6dc5ab5140729cc10fd5",
    "MANIFEST.json": "a1e72a3f541d1c75809cc724c9723332303e90aa775a2c92bc0acc11a240bc21",
    "RESULT.json.sha256": "8eab8b24f21088e3de82254f3d4929c61a7ed8a341593e3a4cbbafcc4bca2ce0",
}
IMPLEMENTATION_PATHS = (
    "scripts/r6_int10k_full_history_oracle.py",
    "src/arcana_worldsim/r6/int10k_full_history_oracle.py",
    "src/arcana_worldsim/r6/int10k_short_reference.py",
    "src/arcana_worldsim/r6/regional_geological_evolution.py",
    "src/arcana_worldsim/r6/unified_multiphysics_microdomain.py",
    "src/arcana_worldsim/r6/functional_development.py",
    "src/arcana_worldsim/r6/material_rheology_provider.py",
    "src/arcana_worldsim/r6/geological_surface_microdomain.py",
)


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture complete full-history E1 oracle; only 3/10 years")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--years", required=True, type=int, choices=(3, 10))
    parser.add_argument("--split-at", required=True, type=int)
    args = parser.parse_args()
    config = ShortReferenceConfig(args.years, args.split_at)
    config.validate()

    source = args.input_dir.resolve(strict=True)
    destination = args.output_dir.resolve()
    repository = REPOSITORY
    if (destination.exists() or destination == source or source in destination.parents
            or destination in source.parents or repository == destination
            or repository in destination.parents):
        parser.error("OUTPUT_MUST_BE_NEW_EXTERNAL_EVIDENCE_DIRECTORY")
    before = verify_source_bundle(source, SOURCE_HASHES)
    payloads, source_identity = load_verified_r6_initial_columns(source)
    if set(payloads) != set(SUPPORTS):
        parser.error("E0_SUPPORT_SET_MISMATCH")
    states = {support: _state_from_payload(payloads[support]) for support in SUPPORTS}
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository,
                                check=True, capture_output=True, text=True).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain=v1", "--",
                                 *IMPLEMENTATION_PATHS], cwd=repository,
                                check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        commit = None
        status = "UNKNOWN"
    implementation_hashes = {
        relative: _digest(repository / relative) for relative in IMPLEMENTATION_PATHS
    }
    started = time.perf_counter()
    oracle = capture_full_history_oracle(
        states, source_identity, config=config, implementation_commit=commit,
        implementation_source_sha256=implementation_hashes,
        implementation_worktree_dirty=bool(status.strip()) if status != "UNKNOWN" else None)
    elapsed = time.perf_counter() - started
    if verify_source_bundle(source, SOURCE_HASHES) != before:
        parser.error("E0_INPUTS_CHANGED_DURING_CAPTURE")
    report = {
        "schema": "FULL_HISTORY_ORACLE_RUN_REPORT_V1",
        "status": oracle["status"], "classification": oracle["classification"],
        "source_commit": commit, "source_identity": source_identity,
        "implementation_source_sha256": implementation_hashes,
        "tracked_implementation_changes_present": status.strip() if status != "UNKNOWN" else None,
        "source_sha256": before, "oracle_sha256": oracle["integrity"]["canonical_body_sha256"],
        "years": args.years, "split_at": args.split_at,
        "capture_wall_seconds_excluding_output_write": elapsed,
        "python": sys.version, "numpy": _numpy_version(),
        "source_inputs_rechecked": True,
        "world_history_production_authorized": False,
        "geodyn_2b_arcana_forward_authorized": False,
    }
    bundle = write_new_oracle_bundle(oracle, destination, report=report)
    print(json.dumps({**report, "manifest_sha256": bundle["manifest_sha256"],
                      "output_bytes": bundle["output_bytes"]}, indent=2))
    return 0


def _numpy_version() -> str | None:
    try:
        import numpy
    except ImportError:
        return None
    return str(numpy.__version__)


if __name__ == "__main__":
    raise SystemExit(main())
