from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED_MODEL_SHA256 = "de2399e2b92157ee98d10458db5dcd849b557c076beeed3a648154a6c62e016f"
EXPECTED_SPATIAL_SHA256 = "a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate_paths(root: Path, filename: str, preferred: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []

    for rel in preferred:
        p = root / rel
        if p.is_file():
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                out.append(rp)

    for p in root.rglob(filename):
        if ".git" in p.parts:
            continue
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)

    return out


def locate_exact(label: str, candidates: list[Path], expected_sha: str) -> Path:
    inspected: list[tuple[str, str]] = []
    for p in candidates:
        digest = sha256_file(p)
        inspected.append((str(p), digest))
        if digest == expected_sha:
            print(f"PASS {label}: {p}")
            print(f"SHA256 {digest}")
            return p

    details = "\n".join(f"  {path}\n    {digest}" for path, digest in inspected[:20])
    raise RuntimeError(
        f"Exact {label} not found. Expected SHA256 {expected_sha}.\n"
        f"Candidates inspected: {len(inspected)}\n{details}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Locate exact R3.14-frozen paleoclimate model/spatial payload by SHA256 "
            "and run the R5.17-B6 semantic inspector."
        )
    )
    parser.add_argument("--search-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--inspector",
        type=Path,
        default=Path("R5_17_B6_INSPECT_PALEOCLIMATE_SEMANTICS.py"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("R5_17_B6_PALEOCLIMATE_SEMANTIC_EVIDENCE.json"),
    )
    args = parser.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    inspector = args.inspector.resolve()
    if not inspector.is_file():
        raise FileNotFoundError(f"Missing B6 inspector: {inspector}")

    model_candidates = candidate_paths(
        root,
        "model.py",
        [
            Path("local_bindings/v0_6D1_R3_14/v0_6_1_SEALED_MINIMAL/src/arcana_worldsim/paleoclimate/model.py"),
        ],
    )
    spatial_candidates = candidate_paths(
        root,
        "paleoclimate_spatial_snapshots.npz",
        [
            Path("local_bindings/v0_6D1_R3_14/v0_6_1_SEALED_MINIMAL/outputs/hybrid1/paleoclimate_v0_6_1/paleoclimate_spatial_snapshots.npz"),
        ],
    )

    model = locate_exact("R3.14 model.py", model_candidates, EXPECTED_MODEL_SHA256)
    spatial = locate_exact(
        "R3.14 paleoclimate_spatial_snapshots.npz",
        spatial_candidates,
        EXPECTED_SPATIAL_SHA256,
    )

    cmd = [
        sys.executable,
        str(inspector),
        "--model",
        str(model),
        "--spatial-snapshots",
        str(spatial),
        "--output",
        str(args.output.resolve()),
    ]
    print("Running B6 semantic inspector (source read only; source is not executed)...")
    subprocess.run(cmd, check=True)
    print(f"PASS B6 semantic inspector output: {args.output.resolve()}")


if __name__ == "__main__":
    main()
