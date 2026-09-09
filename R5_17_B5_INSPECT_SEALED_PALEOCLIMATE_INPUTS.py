from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np


EXPECTED = {
    "recent_paleoclimate_history": {
        "filename": "recent_paleoclimate_history.npz",
        "sha256": "be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1",
    },
    "paleoclimate_spatial_snapshots": {
        "filename": "paleoclimate_spatial_snapshots.npz",
        "sha256": "a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd",
    },
    "shoreline_state_I": {
        "filename": "shoreline_state_I.npz",
        "sha256": "f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85",
    },
}

HYDROLOGY_NAME_PATTERN = re.compile(
    r"precip|rain|moist|runoff|river|drain|catch|lake|water|hydro|soil|snow|ice|evap|arid|wet",
    re.IGNORECASE,
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    return value


def inspect_array(array: np.ndarray) -> dict[str, Any]:
    out: dict[str, Any] = {
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "size": int(array.size),
    }

    if array.dtype.kind in "biufc":
        finite = np.isfinite(array)
        out["finite_count"] = int(np.count_nonzero(finite))
        out["nonfinite_count"] = int(array.size - np.count_nonzero(finite))

        if np.any(finite):
            vals = array[finite]
            if array.dtype.kind == "c":
                abs_vals = np.abs(vals)
                out["abs_min"] = float(np.min(abs_vals))
                out["abs_max"] = float(np.max(abs_vals))
            else:
                out["min"] = scalar(np.min(vals))
                out["max"] = scalar(np.max(vals))
                out["mean"] = float(np.mean(vals, dtype=np.float64))

        if array.dtype.kind in "biu":
            out["nonzero_count"] = int(np.count_nonzero(array))
    else:
        out["numeric_interpretation"] = "NOT_PERFORMED"

    return out


def inspect_npz(label: str, path: Path) -> dict[str, Any]:
    expected = EXPECTED[label]
    if not path.is_file():
        raise FileNotFoundError(f"Missing {label}: {path}")

    digest = sha256_file(path)
    if digest != expected["sha256"]:
        raise RuntimeError(
            f"SHA256 mismatch for {label}: expected {expected['sha256']}, got {digest}"
        )

    arrays: dict[str, Any] = {}
    blocked_keys: list[str] = []
    with np.load(path, allow_pickle=False) as payload:
        keys = list(payload.files)
        for key in keys:
            try:
                arrays[key] = inspect_array(np.asarray(payload[key]))
            except ValueError as exc:
                blocked_keys.append(key)
                arrays[key] = {
                    "inspection_status": "BLOCKED_WITH_ALLOW_PICKLE_FALSE",
                    "error": str(exc),
                }

    lexical_candidates = sorted(k for k in arrays if HYDROLOGY_NAME_PATTERN.search(k))

    return {
        "label": label,
        "source_path": str(path.resolve()),
        "filename": path.name,
        "filename_matches_expected": path.name == expected["filename"],
        "sha256": digest,
        "sha256_matches_r314_authority": True,
        "array_count": len(arrays),
        "arrays": arrays,
        "blocked_allow_pickle_false_keys": blocked_keys,
        "hydrology_lexical_candidate_keys": lexical_candidates,
        "candidate_key_note": (
            "Lexical name matching only. Presence in this list does not authorize freshwater semantics."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Hash-validate and structurally inspect exact R3.14-bound v0.6.1 "
            "paleoclimate payloads before any R5.17 freshwater derivation."
        )
    )
    parser.add_argument("--recent-history", required=True, type=Path)
    parser.add_argument("--spatial-snapshots", required=True, type=Path)
    parser.add_argument("--shoreline-state", required=True, type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("R5_17_B5_SEALED_PALEOCLIMATE_PAYLOAD_INSPECTION.json"),
    )
    args = parser.parse_args()

    inputs = {
        "recent_paleoclimate_history": inspect_npz(
            "recent_paleoclimate_history", args.recent_history
        ),
        "paleoclimate_spatial_snapshots": inspect_npz(
            "paleoclimate_spatial_snapshots", args.spatial_snapshots
        ),
        "shoreline_state_I": inspect_npz("shoreline_state_I", args.shoreline_state),
    }

    all_hashes = all(v["sha256_matches_r314_authority"] for v in inputs.values())
    blocked = {
        label: value["blocked_allow_pickle_false_keys"]
        for label, value in inputs.items()
        if value["blocked_allow_pickle_false_keys"]
    }

    manifest = {
        "schema": "ARCANA_R5_17_B5_SEALED_PALEOCLIMATE_PAYLOAD_INSPECTION_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B5",
        "purpose": (
            "Inspect exact R3.14-bound paleoclimate payload structure before deciding "
            "whether a native freshwater-support derivation has sufficient physical inputs."
        ),
        "r314_authority": (
            "CANONICAL_LATE_CENOZOIC_PROVIDER_BINDING_ADAPTIVE_CLOCK_RESTART_CONTRACT_v0_6D1_R3_14.md"
        ),
        "all_sha256_match": all_hashes,
        "allow_pickle": False,
        "blocked_allow_pickle_false": blocked,
        "inputs": inputs,
        "scientific_interpretation_performed": False,
        "freshwater_support_materialized": False,
        "k_x_t_materialized": False,
        "new_historical_simulation": False,
        "external_engine_execution": False,
        "canonical_mutation": False,
        "status": (
            "PASS_R517_B5_SEALED_PALEOCLIMATE_PAYLOAD_HASH_AND_SCHEMA_INSPECTION"
            if all_hashes and not blocked
            else "BLOCKED_R517_B5_PAYLOAD_SCHEMA_REQUIRES_TARGETED_REVIEW"
        ),
        "next_if_pass": (
            "R5.17-B6_FRESHWATER_PHYSICAL_INPUT_SEMANTIC_BINDING_AND_DERIVATION_DESIGN"
        ),
    }

    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
