from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.integrated_geological_microdomain import (  # noqa: E402
    run_integrated_microdomain,
)
from arcana_worldsim.r6 import deep_geological_physics_pilot, functional_development  # noqa: E402
from arcana_worldsim.r6 import integrated_geological_microdomain  # noqa: E402
from arcana_worldsim.r6 import tectonic_deep_pilot  # noqa: E402

DEFAULT_ARCHIVE = Path(r"F:\corsiiiuu\Magistrale\Arcana\ENG10K_LUNA_ANALYSIS\ENG10K_ARCHIVE_ec79bf89_01.tar.gz")
DEFAULT_OUTPUT = ROOT / "outputs/r6_experimental_multiphysics/INTEGRATED_GEOLOGICAL_MICRODOMAIN_20261025_03"


def _write_exclusive(path: Path, payload: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _implementation_identity() -> dict[str, object]:
    sources = {
        "microdomain": Path(integrated_geological_microdomain.__file__),
        "runner": Path(__file__),
        "reduced_thermal_kernel": Path(functional_development.__file__),
        "deep_modal_operators": Path(deep_geological_physics_pilot.__file__),
        "archive_state_adapter": Path(tectonic_deep_pilot.__file__),
    }
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout.strip()
    return {"repository_head": head,
            "repository_state": "WORKTREE_MAY_CONTAIN_PREEXISTING_UNRELATED_CHANGES",
            "source_sha256": {name: _sha256_file(path) for name, path in sources.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run short noncanonical two-column ENG10K microdomain pilot")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--years", type=float, default=3.0)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    allowed_root = (ROOT / "outputs/r6_experimental_multiphysics").resolve()
    if allowed_root not in output_dir.parents:
        raise SystemExit("output directory must be a new child under outputs/r6_experimental_multiphysics")
    if output_dir.exists():
        raise SystemExit(f"output directory already exists: {output_dir}")

    result = run_integrated_microdomain(str(args.archive), duration_years=args.years)
    result["implementation_identity"] = _implementation_identity()
    result_bytes = (json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    result_hash = hashlib.sha256(result_bytes).hexdigest()
    output_dir.mkdir(parents=False, exist_ok=False)
    result_path = output_dir / "RESULT.json"
    _write_exclusive(result_path, result_bytes)
    sidecar_bytes = f"{result_hash}  RESULT.json\n".encode("ascii")
    _write_exclusive(output_dir / "RESULT.json.sha256", sidecar_bytes)
    manifest = {
        "schema": "ARCANA_INTEGRATED_GEOLOGICAL_MICRODOMAIN_MANIFEST_V1",
        "scope": result["scope"],
        "archive_sha256": result["source_archive"]["sha256"],
        "artifacts": [{"path": "RESULT.json", "size_bytes": len(result_bytes), "sha256": result_hash}],
        "sidecar": {"path": "RESULT.json.sha256", "size_bytes": len(sidecar_bytes),
                    "sha256": hashlib.sha256(sidecar_bytes).hexdigest()},
        "manifest_self_hash": None,
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
    _write_exclusive(output_dir / "MANIFEST.json", manifest_bytes)
    print(json.dumps({"output_dir": str(output_dir), "result_sha256": result_hash,
                      "result_bytes": len(result_bytes), "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest()},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
