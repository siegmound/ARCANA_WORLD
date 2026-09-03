from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.scientific_engines.r321_present_lineage_registry import (  # noqa: E402
    EXPECTED_R319_JSON_SHA256,
    EXPECTED_R319_NPZ_SHA256,
    R321Config,
    R321GateError,
    materialize_r321,
    sha256_file,
)


def _discover_by_hash(root: Path, suffix: str, expected: str) -> Path | None:
    # R3.19 artifacts may live either in outputs/ or local_runs/. Search the
    # canonical stage directories first, then their parent trees. Exact SHA-256
    # remains the authority, so discovery cannot silently select the wrong file.
    preferred = [
        root / "local_runs" / "v0_6D1_R3_19",
        root / "outputs" / "v0_6D1_R3_19",
        root / "local_runs",
        root / "outputs",
        root,
    ]
    seen: set[Path] = set()

    def scan(base: Path, *, recursive: bool, name_filtered: bool) -> Path | None:
        if not base.exists():
            return None
        iterator = base.rglob(f"*{suffix}") if recursive else base.glob(f"*{suffix}")
        for p in iterator:
            try:
                rp = p.resolve()
            except OSError:
                rp = p
            if rp in seen or not p.is_file():
                continue
            seen.add(rp)
            if name_filtered:
                name = p.name.lower()
                if "r3_19" not in name and "0ka" not in name and "checkpoint" not in name:
                    continue
            try:
                if sha256_file(p) == expected:
                    return p
            except OSError:
                continue
        return None

    # Fast pass: likely checkpoint names in the normal R3.19 storage trees.
    for base in preferred[:-1]:
        hit = scan(base, recursive=True, name_filtered=True)
        if hit is not None:
            return hit

    # Root-level canonical artifacts are common in this repository.
    hit = scan(root, recursive=False, name_filtered=True)
    if hit is not None:
        return hit

    # Conservative fallback: exact-hash scan without filename assumptions, but
    # only inside local_runs/ and outputs/ to avoid crawling .venv/source trees.
    for base in (root / "local_runs", root / "outputs"):
        hit = scan(base, recursive=True, name_filtered=False)
        if hit is not None:
            return hit
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="ARCANA WorldSim R3.21 read-only present-lineage registry")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--checkpoint-json", type=Path)
    ap.add_argument("--checkpoint-npz", type=Path)
    ap.add_argument("--output-dir", type=Path)
    ns = ap.parse_args()
    root = ns.root.resolve()
    cj = ns.checkpoint_json or _discover_by_hash(root, ".json", EXPECTED_R319_JSON_SHA256)
    cn = ns.checkpoint_npz or _discover_by_hash(root, ".npz", EXPECTED_R319_NPZ_SHA256)
    out = ns.output_dir or (root / "outputs" / "v0_6D1_R3_21")
    if cj is None or cn is None:
        raise SystemExit(
            "Could not auto-discover the exact SEALED R3.19 checkpoint pair. "
            "Pass --checkpoint-json and --checkpoint-npz explicitly."
        )
    try:
        closure = materialize_r321(cj, cn, out, R321Config())
    except R321GateError as exc:
        print(json.dumps({"stage": "v0.6D1-R3.21", "status": "FAIL_CLOSED", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps({"stage": "v0.6D1-R3.21", "status": closure["status"], "output_dir": str(out), "summary": closure}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
