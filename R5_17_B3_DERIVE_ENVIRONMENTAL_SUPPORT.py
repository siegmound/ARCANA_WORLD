#!/usr/bin/env python3
"""R5.17-B3 — derive transparent environmental-support exposures from SEALED inputs.

This runner performs the smallest native-ARCANA numeric derivation authorized by
R5_17_B3_HUMAN_ENVIRONMENTAL_WATER_SUPPORT_DESIGN.md.

It does NOT derive physical human carrying capacity, freshwater supply, settlement,
or civilization outcomes. R3.18 integral fields are converted only into explicitly
labelled duration-normalized exposure fields. R3.19 0-ka accessibility remains an
endpoint boundary. R3.20 hazard arrays are copied unchanged and retain their original
15–11 ka diagnostic semantics.
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
        "sha256": "54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70",
        "filename": "R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz",
    },
    "r319_checkpoint": {
        "sha256": "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406",
        "filename": "WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19.npz",
    },
    "r320_hazard": {
        "sha256": "4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14",
        "filename": "R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz",
    },
}

WINDOWS = {
    "full_125_to_0": 125000.0,
    "recent_120_to_0": 120000.0,
    "transport_phase1_125_to_62p5": 62500.0,
    "transport_phase2_62p5_to_0": 62500.0,
}

EXPOSURE_FIELDS = (
    "aridity_index",
    "browse_forage",
    "land_support",
    "low_forage",
    "temperature_c",
    "wetland_forage",
)

R320_GRID_FIELDS = (
    "coastal_inundation_potential_index",
    "compound_flood_hazard_index",
    "drying_hazard_index",
    "ecosystem_hydrological_shock_index",
    "hydrological_disruption_index",
    "meltwater_system_pressure_index",
    "pluvial_flood_potential_index",
    "raw_support_loss_fraction",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_input(label: str, path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{label}: file not found: {path}")
    digest = sha256_file(path)
    expected = EXPECTED[label]
    if path.name != expected["filename"]:
        raise RuntimeError(
            f"{label}: filename mismatch; expected {expected['filename']!r}, got {path.name!r}"
        )
    if digest.lower() != expected["sha256"].lower():
        raise RuntimeError(
            f"{label}: SHA256 mismatch\n"
            f"expected {expected['sha256']}\n"
            f"actual   {digest}\n"
            f"path     {path}"
        )
    return digest


def require_shape(name: str, arr: np.ndarray, shape: tuple[int, ...]) -> None:
    if arr.shape != shape:
        raise RuntimeError(f"{name}: expected shape {shape}, got {arr.shape}")
    if not np.isfinite(arr).all():
        raise RuntimeError(f"{name}: contains non-finite values")


def stats(arr: np.ndarray) -> dict[str, Any]:
    a = np.asarray(arr)
    out: dict[str, Any] = {
        "shape": list(a.shape),
        "dtype": str(a.dtype),
        "size": int(a.size),
        "finite_count": int(np.isfinite(a).sum()) if a.dtype.kind in "biufc" else None,
    }
    if a.size and a.dtype.kind in "biuf":
        out.update(
            min=float(np.min(a)),
            max=float(np.max(a)),
            mean=float(np.mean(a, dtype=np.float64)),
        )
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--r318-environment", type=Path, required=True)
    p.add_argument("--r319-checkpoint", type=Path, required=True)
    p.add_argument("--r320-hazard", type=Path, required=True)
    p.add_argument(
        "--output-npz",
        type=Path,
        default=Path("R5_17_B3_ENVIRONMENTAL_SUPPORT_EXPOSURES.npz"),
    )
    p.add_argument(
        "--output-manifest",
        type=Path,
        default=Path("R5_17_B3_ENVIRONMENTAL_SUPPORT_EXPOSURES_MANIFEST.json"),
    )
    args = p.parse_args()

    input_hashes = {
        "r318_environment": require_input("r318_environment", args.r318_environment),
        "r319_checkpoint": require_input("r319_checkpoint", args.r319_checkpoint),
        "r320_hazard": require_input("r320_hazard", args.r320_hazard),
    }

    output: dict[str, np.ndarray] = {}
    derived_stats: dict[str, Any] = {}

    with np.load(args.r318_environment, allow_pickle=False) as r318:
        for window, duration in WINDOWS.items():
            for field in EXPOSURE_FIELDS:
                src_name = f"{window}__{field}"
                if src_name not in r318.files:
                    raise RuntimeError(f"R3.18 missing required array: {src_name}")
                src = np.asarray(r318[src_name], dtype=np.float64)
                require_shape(f"R3.18::{src_name}", src, (90, 180))
                dst_name = f"{window}__{field}_duration_normalized_exposure"
                dst = src / duration
                require_shape(dst_name, dst, (90, 180))
                output[dst_name] = dst
                derived_stats[dst_name] = stats(dst)

        # Transparent phase-contrast diagnostics only; no suitability score.
        for field in EXPOSURE_FIELDS:
            p1 = output[
                f"transport_phase1_125_to_62p5__{field}_duration_normalized_exposure"
            ]
            p2 = output[
                f"transport_phase2_62p5_to_0__{field}_duration_normalized_exposure"
            ]
            delta_name = f"phase2_minus_phase1__{field}_exposure_delta"
            delta = p2 - p1
            output[delta_name] = delta
            derived_stats[delta_name] = stats(delta)

        # Numerical closure diagnostic for the integral bundle.
        closure: dict[str, float] = {}
        for field in EXPOSURE_FIELDS:
            full = np.asarray(r318[f"full_125_to_0__{field}"], dtype=np.float64)
            p1_raw = np.asarray(
                r318[f"transport_phase1_125_to_62p5__{field}"], dtype=np.float64
            )
            p2_raw = np.asarray(
                r318[f"transport_phase2_62p5_to_0__{field}"], dtype=np.float64
            )
            closure[field] = float(np.max(np.abs(full - (p1_raw + p2_raw))))

    with np.load(args.r319_checkpoint, allow_pickle=False) as r319:
        for key, shape in (("lat", (90,)), ("lon", (180,)), ("current_accessible", (90, 180))):
            if key not in r319.files:
                raise RuntimeError(f"R3.19 missing required array: {key}")
            arr = np.asarray(r319[key])
            require_shape(f"R3.19::{key}", arr, shape)
            output[f"r319_0ka__{key}"] = arr.copy()
            derived_stats[f"r319_0ka__{key}"] = stats(arr)

    with np.load(args.r320_hazard, allow_pickle=False) as r320:
        if "years_before_book" not in r320.files:
            raise RuntimeError("R3.20 missing required array: years_before_book")
        years = np.asarray(r320["years_before_book"])
        require_shape("R3.20::years_before_book", years, (80,))
        if int(years[0]) != -14950 or int(years[-1]) != -11000:
            raise RuntimeError(
                "R3.20 time coverage mismatch; expected -14950..-11000 years before book"
            )
        if not np.all(np.diff(years) == 50):
            raise RuntimeError("R3.20 cadence mismatch; expected exact 50-year increments")
        output["r320__years_before_book"] = years.copy()
        derived_stats["r320__years_before_book"] = stats(years)

        for field in R320_GRID_FIELDS:
            if field not in r320.files:
                raise RuntimeError(f"R3.20 missing required array: {field}")
            arr = np.asarray(r320[field])
            require_shape(f"R3.20::{field}", arr, (80, 90, 180))
            # Preserve original values and dtype unchanged.
            output[f"r320__{field}"] = arr.copy()
            derived_stats[f"r320__{field}"] = stats(arr)

        if "severe_flood_candidate_fraction" not in r320.files:
            raise RuntimeError("R3.20 missing severe_flood_candidate_fraction")
        severe = np.asarray(r320["severe_flood_candidate_fraction"])
        require_shape("R3.20::severe_flood_candidate_fraction", severe, (80,))
        output["r320__severe_flood_candidate_fraction"] = severe.copy()
        derived_stats["r320__severe_flood_candidate_fraction"] = stats(severe)

    output["r318__window_duration_years"] = np.asarray(
        [WINDOWS[k] for k in WINDOWS], dtype=np.float64
    )

    args.output_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output_npz, **output)
    output_sha = sha256_file(args.output_npz)

    manifest = {
        "schema": "ARCANA_R5_17_B3_ENVIRONMENTAL_SUPPORT_EXPOSURES_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B3",
        "status": "PASS_R517_B3_NATIVE_ENVIRONMENTAL_SUPPORT_EXPOSURE_DERIVATION",
        "design_authority": "R5_17_B3_HUMAN_ENVIRONMENTAL_WATER_SUPPORT_DESIGN.md",
        "input_sha256": input_hashes,
        "all_input_sha256_match": True,
        "window_duration_years": WINDOWS,
        "exposure_fields": list(EXPOSURE_FIELDS),
        "integral_closure_max_abs_error": closure,
        "output_npz": str(args.output_npz.resolve()),
        "output_npz_sha256": output_sha,
        "output_array_count": len(output),
        "arrays": derived_stats,
        "semantics": {
            "r318_outputs": "DURATION_NORMALIZED_EXPOSURES_NOT_AUTOMATICALLY_PHYSICAL_SNAPSHOTS",
            "r319_current_accessible": "EXACT_0KA_ENDPOINT_BOUNDARY_NOT_BACKPROJECTED",
            "r320_hazards": "UNCHANGED_DIAGNOSTIC_RANKING_FIELDS_15_TO_11KA_ONLY",
            "freshwater_support_materialized": False,
            "hydrological_reliability_materialized": False,
            "human_edible_productivity_materialized": False,
            "physical_K_materialized": False,
        },
        "governance": {
            "population_target_imposed": False,
            "civilization_target_imposed": False,
            "reference_population_used_as_human_population": False,
            "forage_channels_blindly_summed": False,
            "r3_19_mask_backprojected": False,
            "r3_20_hazard_extrapolated": False,
            "external_engine_execution": False,
            "new_historical_simulation": False,
            "canonical_mutation": False,
            "seal_action": False,
        },
        "next_if_pass": "R5.17-B4_BIND_FRESHWATER_ACCESS_SOURCE_OR_DECLARE_BOUNDED_WATER_GAP",
    }

    args.output_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "output_npz": str(args.output_npz.resolve()),
                "output_npz_sha256": output_sha,
                "output_manifest": str(args.output_manifest.resolve()),
                "output_array_count": len(output),
                "integral_closure_max_abs_error": closure,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
