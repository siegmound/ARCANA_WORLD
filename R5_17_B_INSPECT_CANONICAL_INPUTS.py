#!/usr/bin/env python3
"""R5.17-B2 — inspect exact SEALED local payloads before support-layer derivation.

This tool performs no historical simulation and no canonical mutation. It validates
local payload SHA256 values against SEALED repository authority, opens NPZ payloads
with allow_pickle=False, records keys/shapes/dtypes/finite statistics, and writes a
machine-readable inspection manifest suitable for repository import.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

EXPECTED = {
    "r318_environment": {
        "filename": "R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz",
        "sha256": "54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70",
        "authority": "outputs/v0_6D1_R3_18/FORMAL_AUDIT_SEALED_v0_6D1_R3_18.json",
    },
    "r319_checkpoint": {
        "filename": "WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19.npz",
        "sha256": "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406",
        "authority": "outputs/v0_6D1_R3_19/FORMAL_AUDIT_SEALED_v0_6D1_R3_19.json",
    },
    "r320_hazard": {
        "filename": "R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz",
        "sha256": "4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14",
        "authority": "outputs/v0_6D1_R3_20/FORMAL_AUDIT_SEALED_v0_6D1_R3_20.json",
    },
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def scalar(v: Any) -> Any:
    if isinstance(v, np.generic):
        return v.item()
    return v


def inspect_array(arr: np.ndarray) -> dict[str, Any]:
    row: dict[str, Any] = {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "size": int(arr.size),
    }

    if arr.dtype.kind in "biufc":
        finite = np.isfinite(arr)
        row["finite_count"] = int(finite.sum())
        row["nonfinite_count"] = int(arr.size - finite.sum())
        if finite.any():
            vals = arr[finite]
            if arr.dtype.kind == "c":
                mags = np.abs(vals)
                row["abs_min"] = scalar(mags.min())
                row["abs_max"] = scalar(mags.max())
            else:
                row["min"] = scalar(vals.min())
                row["max"] = scalar(vals.max())
                row["mean"] = scalar(vals.mean(dtype=np.float64))
        if arr.dtype.kind in "biu":
            row["nonzero_count"] = int(np.count_nonzero(arr))
    else:
        row["statistics"] = "NON_NUMERIC_NOT_INTERPRETED"

    return row


def inspect_npz(label: str, path: Path) -> dict[str, Any]:
    expected = EXPECTED[label]
    if not path.is_file():
        raise FileNotFoundError(f"{label}: file not found: {path}")

    digest = sha256_file(path)
    if digest.lower() != expected["sha256"].lower():
        raise RuntimeError(
            f"{label}: SHA256 mismatch\n"
            f"expected {expected['sha256']}\n"
            f"actual   {digest}\n"
            f"path     {path}"
        )

    arrays: dict[str, Any] = {}
    with np.load(path, allow_pickle=False) as z:
        for key in sorted(z.files):
            arrays[key] = inspect_array(np.asarray(z[key]))

    return {
        "label": label,
        "source_path": str(path.resolve()),
        "filename": path.name,
        "filename_matches_expected": path.name == expected["filename"],
        "sha256": digest,
        "sha256_matches_sealed_authority": True,
        "sealed_authority": expected["authority"],
        "array_count": len(arrays),
        "arrays": arrays,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--r318-environment", type=Path, required=True)
    p.add_argument("--r319-checkpoint", type=Path, required=True)
    p.add_argument("--r320-hazard", type=Path, required=True)
    p.add_argument(
        "--output",
        type=Path,
        default=Path("R5_17_B_LOCAL_CANONICAL_PAYLOAD_INSPECTION.json"),
    )
    args = p.parse_args()

    inputs = {
        "r318_environment": inspect_npz("r318_environment", args.r318_environment),
        "r319_checkpoint": inspect_npz("r319_checkpoint", args.r319_checkpoint),
        "r320_hazard": inspect_npz("r320_hazard", args.r320_hazard),
    }

    manifest = {
        "schema": "ARCANA_R5_17_B_LOCAL_CANONICAL_PAYLOAD_INSPECTION_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B2",
        "purpose": "Hash-validate and structurally inspect SEALED local payloads before any human-support derivation.",
        "inputs": inputs,
        "all_sha256_match": all(
            row["sha256_matches_sealed_authority"] for row in inputs.values()
        ),
        "new_historical_simulation": False,
        "external_engine_execution": False,
        "canonical_mutation": False,
        "scientific_interpretation_performed": False,
        "status": "PASS_R517_B2_LOCAL_CANONICAL_PAYLOAD_HASH_AND_SCHEMA_INSPECTION",
        "next_if_pass": "R5.17-B3_HUMAN_ENVIRONMENTAL_AND_WATER_SUPPORT_DERIVATION_DESIGN",
    }

    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": manifest["status"],
        "output": str(args.output.resolve()),
        "arrays": {k: v["array_count"] for k, v in inputs.items()},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
