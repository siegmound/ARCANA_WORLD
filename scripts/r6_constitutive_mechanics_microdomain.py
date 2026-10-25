from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.constitutive_mechanics_microdomain import (  # noqa: E402
    _RssSampler, run_constitutive_microdomain,
)
from arcana_worldsim.r6.tectonic_boundary_microdomain import (  # noqa: E402
    boundary_view_cache_default_path,
)

DEFAULT_ARCHIVE = Path(r"F:\corsiiiuu\Magistrale\Arcana\ENG10K_LUNA_ANALYSIS\ENG10K_ARCHIVE_ec79bf89_01.tar.gz")
DEFAULT_EXTERNAL_ROOT = Path(r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES")
DEFAULT_OUTPUT = ROOT / "outputs/r6_experimental_multiphysics/MATERIAL_RHEOLOGY_PROVIDER_20261025_01"


def _write_exclusive(path: Path, data: bytes) -> float:
    started = perf_counter()
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return perf_counter() - started


def main() -> int:
    parser = argparse.ArgumentParser(description="Short synthetic layered-continuum C028/C029 mechanics pilot")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--external-root", type=Path, default=DEFAULT_EXTERNAL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--boundary-view-cache", type=Path, default=None)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    allowed = (ROOT / "outputs/r6_experimental_multiphysics").resolve()
    if allowed not in output.parents or output.exists():
        raise SystemExit("OUTPUT_PATH_MUST_BE_NEW_CHILD_OF_EXPERIMENTAL_ROOT")
    output.parent.mkdir(parents=True, exist_ok=True)
    cache = args.boundary_view_cache or boundary_view_cache_default_path(ROOT)
    with _RssSampler() as sampler:
        result = run_constitutive_microdomain(
            ROOT, args.external_root, args.archive,
            boundary_view_cache_path=cache)
        if cache.is_file():
            result["boundary_view_cache"]["sha256"] = hashlib.sha256(cache.read_bytes()).hexdigest()
        serial_start = perf_counter()
        result_bytes = (json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False,
                                   allow_nan=False) + "\n").encode("utf-8")
        serial_seconds = perf_counter() - serial_start
        result_sha = hashlib.sha256(result_bytes).hexdigest()
        output.mkdir(parents=False, exist_ok=False)
        result_write_s = _write_exclusive(output / "RESULT.json", result_bytes)
        sidecar = f"{result_sha}  RESULT.json\n".encode("ascii")
        sidecar_write_s = _write_exclusive(output / "RESULT.json.sha256", sidecar)
        rss_snapshot = sampler.summary()
        manifest = {
            "schema": "ARCANA_CONSTITUTIVE_MECHANICS_MANIFEST_V1",
            "result": {"path": "RESULT.json", "size_bytes": len(result_bytes), "sha256": result_sha},
            "sidecar": {"path": "RESULT.json.sha256", "size_bytes": len(sidecar),
                        "sha256": hashlib.sha256(sidecar).hexdigest()},
            "measurement": {"serialization_seconds": serial_seconds,
                            "result_write_and_fsync_seconds": result_write_s,
                            "sidecar_write_and_fsync_seconds": sidecar_write_s,
                            "process_rss_through_sidecar": rss_snapshot},
            "manifest_self_hash": None,
        }
        manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode("utf-8")
        manifest_write_s = _write_exclusive(output / "MANIFEST.json", manifest_bytes)
        total_bytes = sum(p.stat().st_size for p in output.iterdir() if p.is_file())
        print(json.dumps({"output_dir": str(output), "result_sha256": result_sha,
                          "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                          "output_bytes_total": total_bytes,
                          "manifest_write_and_fsync_seconds": manifest_write_s,
                          "process_rss_after_manifest": sampler.summary()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
