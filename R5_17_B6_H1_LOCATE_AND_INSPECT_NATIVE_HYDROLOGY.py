from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

import numpy as np

TARGET_NAME = "channel_hydrology_state_I.npz"
PREFERRED_SUFFIX = Path(
    "local_bindings/v0_6D1_R3_14/v0_6_1_SEALED_MINIMAL/"
    "inputs/v0_5_5I_SEALED/channel_hydrology_state_I.npz"
)
KEY_FIELDS = [
    "mean_discharge_m3_s",
    "drainage_area_km2",
    "receiver_flat",
    "lake_candidate_mask",
    "depression_depth_m",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def numeric_stats(arr: np.ndarray) -> dict[str, Any]:
    a = np.asarray(arr)
    out: dict[str, Any] = {
        "shape": list(a.shape),
        "dtype": str(a.dtype),
        "count": int(a.size),
    }
    if a.dtype.kind in "biufc":
        finite = np.isfinite(a)
        out["finite_count"] = int(np.count_nonzero(finite))
        out["nonfinite_count"] = int(a.size - np.count_nonzero(finite))
        if np.any(finite):
            vals = a[finite].astype(np.float64, copy=False)
            out.update(
                min=float(np.min(vals)),
                max=float(np.max(vals)),
                mean=float(np.mean(vals)),
            )
        if a.dtype.kind == "b":
            out["true_count"] = int(np.count_nonzero(a))
    return out


def inspect_npz_bytes(data: bytes) -> dict[str, Any]:
    with np.load(io.BytesIO(data), allow_pickle=False) as payload:
        arrays = {name: numeric_stats(np.asarray(payload[name])) for name in payload.files}
        return {
            "array_count": len(payload.files),
            "array_names": sorted(payload.files),
            "key_fields_present": {name: name in payload.files for name in KEY_FIELDS},
            "arrays": arrays,
        }


def inspect_npz_path(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        data = f.read()
    return inspect_npz_bytes(data)


def direct_candidates(root: Path) -> list[Path]:
    found: list[Path] = []
    preferred = root / PREFERRED_SUFFIX
    if preferred.is_file():
        found.append(preferred.resolve())
    for p in root.rglob(TARGET_NAME):
        if ".git" in p.parts:
            continue
        rp = p.resolve()
        if rp not in found:
            found.append(rp)
    return found


def zip_candidates(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for archive in root.rglob("*.zip"):
        if ".git" in archive.parts:
            continue
        try:
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    if Path(info.filename).name != TARGET_NAME:
                        continue
                    with zf.open(info, "r") as stream:
                        data = stream.read()
                    out.append(
                        {
                            "archive": str(archive.resolve()),
                            "member": info.filename,
                            "size": int(info.file_size),
                            "sha256": sha256_bytes(data),
                            "inspection": inspect_npz_bytes(data),
                        }
                    )
        except (zipfile.BadZipFile, OSError, ValueError) as exc:
            out.append(
                {
                    "archive": str(archive.resolve()),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return out


def summarize_direct(paths: list[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in paths:
        try:
            inspection = inspect_npz_path(p)
            out.append(
                {
                    "path": str(p),
                    "size": int(p.stat().st_size),
                    "sha256": sha256_file(p),
                    "preferred_r314_relative_location": p.as_posix().endswith(PREFERRED_SUFFIX.as_posix()),
                    "inspection": inspection,
                }
            )
        except Exception as exc:  # evidence capture must retain candidate failures
            out.append(
                {
                    "path": str(p),
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return out


def unique_payload_hashes(direct: list[dict[str, Any]], zipped: list[dict[str, Any]]) -> list[str]:
    hashes = {
        item["sha256"]
        for item in [*direct, *zipped]
        if isinstance(item, dict) and isinstance(item.get("sha256"), str)
    }
    return sorted(hashes)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "R5.17-B6-H1: locate and inspect existing ARCANA channel hydrology payloads "
            "without executing historical generators or deriving new freshwater fields."
        )
    )
    parser.add_argument("--search-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("R5_17_B6_H1_NATIVE_HYDROLOGY_DISCOVERY.json"),
    )
    args = parser.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    direct = summarize_direct(direct_candidates(root))
    zipped = zip_candidates(root)
    valid_direct = [x for x in direct if "sha256" in x]
    valid_zip = [x for x in zipped if "sha256" in x]
    hashes = unique_payload_hashes(valid_direct, valid_zip)

    key_field_complete = []
    for source_class, items in (("direct", valid_direct), ("zip", valid_zip)):
        for item in items:
            present = item["inspection"]["key_fields_present"]
            if all(bool(present.get(k)) for k in KEY_FIELDS):
                key_field_complete.append(
                    {
                        "source_class": source_class,
                        "path": item.get("path"),
                        "archive": item.get("archive"),
                        "member": item.get("member"),
                        "sha256": item["sha256"],
                    }
                )

    found = bool(valid_direct or valid_zip)
    manifest = {
        "schema": "ARCANA_R5_17_B6_H1_NATIVE_HYDROLOGY_DISCOVERY_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-H1",
        "purpose": (
            "Discover and structurally inspect pre-existing ARCANA channel hydrology authority "
            "before any new hydrology provider or custom computation is authorized."
        ),
        "search_root": str(root),
        "target_name": TARGET_NAME,
        "preferred_r314_relative_path": str(PREFERRED_SUFFIX),
        "required_semantic_fields_for_followup": KEY_FIELDS,
        "direct_candidates": direct,
        "zip_candidates": zipped,
        "valid_direct_candidate_count": len(valid_direct),
        "valid_zip_candidate_count": len(valid_zip),
        "unique_payload_sha256": hashes,
        "key_field_complete_candidates": key_field_complete,
        "candidate_found": found,
        "authority_identity_adjudicated": False,
        "generator_identity_adjudicated": False,
        "freshwater_support_materialized": False,
        "new_historical_simulation": False,
        "external_engine_execution": False,
        "canonical_mutation": False,
        "status": (
            "PASS_R517_B6_H1_NATIVE_HYDROLOGY_CANDIDATES_INSPECTED"
            if found
            else "BLOCKED_R517_B6_H1_NATIVE_HYDROLOGY_PAYLOAD_NOT_FOUND"
        ),
        "next_if_pass": (
            "R5.17-B6-H2_AUTHORITY_LINEAGE_AND_GENERATOR_SEMANTIC_AUDIT"
        ),
    }

    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))

    if not found:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
