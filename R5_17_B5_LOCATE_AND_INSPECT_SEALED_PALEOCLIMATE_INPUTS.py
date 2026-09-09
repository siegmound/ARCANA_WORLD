from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

EXPECTED = {
    "recent_paleoclimate_history.npz": "be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1",
    "paleoclimate_spatial_snapshots.npz": "a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd",
    "shoreline_state_I.npz": "f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_stream(stream) -> str:
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()


def find_direct(search_root: Path, wanted: set[str]) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in search_root.rglob("*.npz"):
        if path.name not in wanted or path.name in found:
            continue
        digest = sha256_file(path)
        if digest == EXPECTED[path.name]:
            found[path.name] = path.resolve()
            print(f"PASS direct {path.name}: {path}")
    return found


def find_in_zips(search_root: Path, missing: set[str], extract_root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not missing:
        return found
    extract_root.mkdir(parents=True, exist_ok=True)
    for archive in search_root.rglob("*.zip"):
        if not missing - found.keys():
            break
        try:
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    name = Path(info.filename).name
                    if name not in missing or name in found:
                        continue
                    with zf.open(info, "r") as stream:
                        digest = sha256_stream(stream)
                    if digest != EXPECTED[name]:
                        continue
                    target = extract_root / name
                    with zf.open(info, "r") as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)
                    if sha256_file(target) != EXPECTED[name]:
                        raise RuntimeError(f"Post-extraction SHA mismatch: {archive}!{info.filename}")
                    found[name] = target.resolve()
                    print(f"PASS zip {name}: {archive}!{info.filename}")
        except (zipfile.BadZipFile, OSError) as exc:
            print(f"SKIP unreadable zip {archive}: {exc}")
    return found


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Locate exact R3.14 v0.6.1 paleoclimate payloads by SHA256 and run the governed B5 inspector."
    )
    parser.add_argument("--search-root", type=Path, default=Path("."))
    parser.add_argument(
        "--extract-root", type=Path, default=Path(".r5_17_b5_rehydrated_inputs")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("R5_17_B5_SEALED_PALEOCLIMATE_PAYLOAD_INSPECTION.json")
    )
    args = parser.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Search root is not a directory: {root}")

    wanted = set(EXPECTED)
    found = find_direct(root, wanted)
    missing = wanted - found.keys()
    if missing:
        found.update(find_in_zips(root, missing, args.extract_root.resolve()))

    missing = wanted - found.keys()
    if missing:
        raise SystemExit(
            "BLOCKED_R517_B5_EXACT_R314_PAYLOAD_NOT_FOUND: " + ", ".join(sorted(missing))
        )

    inspector = Path(__file__).with_name("R5_17_B5_INSPECT_SEALED_PALEOCLIMATE_INPUTS.py")
    if not inspector.is_file():
        raise SystemExit(f"Missing governed B5 inspector: {inspector}")

    cmd = [
        sys.executable,
        str(inspector),
        "--recent-history", str(found["recent_paleoclimate_history.npz"]),
        "--spatial-snapshots", str(found["paleoclimate_spatial_snapshots.npz"]),
        "--shoreline-state", str(found["shoreline_state_I.npz"]),
        "--output", str(args.output),
    ]
    print("RUN:", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
