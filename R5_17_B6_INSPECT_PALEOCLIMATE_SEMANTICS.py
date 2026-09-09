from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

EXPECTED_MODEL_SHA256 = "de2399e2b92157ee98d10458db5dcd849b557c076beeed3a648154a6c62e016f"
EXPECTED_SPATIAL_SHA256 = "a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd"

TERMS = [
    "precip", "rain", "runoff", "river", "drain", "catch", "lake", "water",
    "hydro", "soil", "snow", "ice", "evap", "infil", "recharge", "storage",
    "npp", "snapshot",
]
TERM_PATTERN = re.compile("|".join(re.escape(t) for t in TERMS), re.IGNORECASE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def numeric_stats(values: np.ndarray) -> dict[str, Any]:
    arr = np.asarray(values)
    finite = np.isfinite(arr)
    out: dict[str, Any] = {
        "count": int(arr.size),
        "finite_count": int(np.count_nonzero(finite)),
        "nonfinite_count": int(arr.size - np.count_nonzero(finite)),
    }
    if np.any(finite):
        vals = arr[finite].astype(np.float64, copy=False)
        out.update(
            min=float(np.min(vals)),
            max=float(np.max(vals)),
            mean=float(np.mean(vals)),
            std=float(np.std(vals)),
        )
    return out


def source_evidence(text: str, context_lines: int = 2) -> dict[str, Any]:
    lines = text.splitlines()
    matched = [i for i, line in enumerate(lines) if TERM_PATTERN.search(line)]

    # Merge nearby matching windows so the evidence stays bounded and readable.
    windows: list[tuple[int, int]] = []
    for idx in matched:
        start = max(0, idx - context_lines)
        end = min(len(lines), idx + context_lines + 1)
        if windows and start <= windows[-1][1]:
            windows[-1] = (windows[-1][0], max(windows[-1][1], end))
        else:
            windows.append((start, end))

    excerpts = []
    for start, end in windows[:40]:
        excerpts.append(
            {
                "start_line": start + 1,
                "end_line": end,
                "text": "\n".join(f"{i + 1}: {lines[i]}" for i in range(start, end)),
            }
        )

    lowered = text.lower()
    term_presence = {term: (term in lowered) for term in TERMS}

    return {
        "source_line_count": len(lines),
        "matching_line_count": len(matched),
        "term_presence": term_presence,
        "bounded_excerpts": excerpts,
        "excerpt_limit": 40,
        "interpretation_note": (
            "Lexical/source evidence only. Semantic promotion requires review of the recorded equations and variable definitions."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify and inspect exact R3.14 paleoclimate source semantics before any freshwater derivation."
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--spatial-snapshots", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("R5_17_B6_PALEOCLIMATE_SEMANTIC_EVIDENCE.json"),
    )
    args = parser.parse_args()

    if not args.model.is_file():
        raise FileNotFoundError(args.model)
    if not args.spatial_snapshots.is_file():
        raise FileNotFoundError(args.spatial_snapshots)

    model_sha = sha256_file(args.model)
    spatial_sha = sha256_file(args.spatial_snapshots)

    if model_sha != EXPECTED_MODEL_SHA256:
        raise RuntimeError(
            f"model.py SHA256 mismatch: expected {EXPECTED_MODEL_SHA256}, got {model_sha}"
        )
    if spatial_sha != EXPECTED_SPATIAL_SHA256:
        raise RuntimeError(
            f"spatial snapshots SHA256 mismatch: expected {EXPECTED_SPATIAL_SHA256}, got {spatial_sha}"
        )

    source_text = args.model.read_text(encoding="utf-8")

    with np.load(args.spatial_snapshots, allow_pickle=False) as payload:
        required = {
            "snapshot_year_before_book",
            "precipitation_factor_relative_book",
            "paleo_land_mask",
        }
        missing = sorted(required.difference(payload.files))
        if missing:
            raise RuntimeError(f"Missing required arrays: {missing}")

        years = np.asarray(payload["snapshot_year_before_book"], dtype=np.float64)
        precip = np.asarray(payload["precipitation_factor_relative_book"])
        land = np.asarray(payload["paleo_land_mask"]).astype(bool)

        if precip.ndim != 3 or land.shape != precip.shape:
            raise RuntimeError(
                f"Unexpected precip/land shapes: precip={precip.shape}, land={land.shape}"
            )
        if years.shape != (precip.shape[0],):
            raise RuntimeError(
                f"Snapshot chronology shape mismatch: years={years.shape}, precip={precip.shape}"
            )
        if not np.all(np.isfinite(precip)) or not np.all(np.isfinite(years)):
            raise RuntimeError("Non-finite values found in governed B6 inputs")

        per_snapshot = []
        for i, year in enumerate(years.tolist()):
            land_values = precip[i][land[i]]
            per_snapshot.append(
                {
                    "index": i,
                    "year_before_book": float(year),
                    "all_cells": numeric_stats(precip[i]),
                    "paleo_land_cells": numeric_stats(land_values),
                    "paleo_land_cell_count": int(np.count_nonzero(land[i])),
                }
            )

    semantic_source = source_evidence(source_text)

    manifest = {
        "schema": "ARCANA_R5_17_B6_PALEOCLIMATE_SEMANTIC_EVIDENCE_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6",
        "purpose": (
            "Verify exact R3.14 source/payload identity and collect bounded semantic evidence "
            "for precipitation/hydrology before any freshwater-support derivation."
        ),
        "inputs": {
            "model": {
                "path": str(args.model.resolve()),
                "sha256": model_sha,
                "sha256_matches_r314": True,
            },
            "spatial_snapshots": {
                "path": str(args.spatial_snapshots.resolve()),
                "sha256": spatial_sha,
                "sha256_matches_r314": True,
            },
        },
        "snapshot_year_before_book": [float(v) for v in years.tolist()],
        "precipitation_factor_relative_book": {
            "shape": list(precip.shape),
            "dtype": str(precip.dtype),
            "per_snapshot": per_snapshot,
        },
        "source_semantic_evidence": semantic_source,
        "freshwater_support_materialized": False,
        "runoff_materialized": False,
        "hydrological_reliability_materialized": False,
        "k_x_t_materialized": False,
        "source_executed": False,
        "new_historical_simulation": False,
        "external_engine_execution": False,
        "canonical_mutation": False,
        "status": "PASS_R517_B6_PALEOCLIMATE_SEMANTIC_EVIDENCE_CAPTURED",
        "next_if_pass": "R5.17-B6_SOURCE_SEMANTIC_ADJUDICATION_AND_MINIMUM_HYDROLOGY_DESIGN",
    }

    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
