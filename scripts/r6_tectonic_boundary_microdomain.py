from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.tectonic_boundary_microdomain import (  # noqa: E402
    run_boundary_microdomain,
)

DEFAULT_ARCHIVE = Path(r"F:\corsiiiuu\Magistrale\Arcana\ENG10K_LUNA_ANALYSIS\ENG10K_ARCHIVE_ec79bf89_01.tar.gz")
DEFAULT_EXTERNAL_ROOT = Path(r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES")
DEFAULT_OUTPUT = ROOT / "outputs/r6_experimental_multiphysics/TECTONIC_BOUNDARY_MICRODOMAIN_20261025_01"


def _write_exclusive(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def main() -> int:
    parser = argparse.ArgumentParser(description="Short noncanonical T0-bound two-column mechanical microdomain")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--external-root", type=Path, default=DEFAULT_EXTERNAL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    allowed_root = (ROOT / "outputs/r6_experimental_multiphysics").resolve()
    if allowed_root not in output_dir.parents:
        raise SystemExit("output directory must be a new child under outputs/r6_experimental_multiphysics")
    if output_dir.exists():
        raise SystemExit(f"output directory already exists: {output_dir}")
    result = run_boundary_microdomain(ROOT, args.external_root, args.archive)
    payload = (json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    result_hash = hashlib.sha256(payload).hexdigest()
    output_dir.mkdir(parents=False, exist_ok=False)
    _write_exclusive(output_dir / "RESULT.json", payload)
    sidecar = f"{result_hash}  RESULT.json\n".encode("ascii")
    _write_exclusive(output_dir / "RESULT.json.sha256", sidecar)
    manifest = {
        "schema": "ARCANA_TECTONIC_BOUNDARY_MICRODOMAIN_MANIFEST_V1",
        "result": {"path": "RESULT.json", "size_bytes": len(payload), "sha256": result_hash},
        "sidecar_sha256": hashlib.sha256(sidecar).hexdigest(),
        "manifest_self_hash": None,
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    _write_exclusive(output_dir / "MANIFEST.json", manifest_bytes)
    print(json.dumps({"output_dir": str(output_dir), "result_sha256": result_hash,
                      "result_bytes": len(payload), "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest()},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
