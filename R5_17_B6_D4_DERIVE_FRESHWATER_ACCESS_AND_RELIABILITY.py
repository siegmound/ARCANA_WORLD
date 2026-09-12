from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.ndimage import distance_transform_edt

import R5_17_B6_D2D_VALIDATE_SEASONAL_GENERATOR_AND_RECONSTRUCT_I as d2d
import R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY as d3

EXPECTED_SNAPSHOT_YEARS = np.array([-21000.0, -14000.0, -12900.0, -12000.0, 0.0], dtype=float)
TARGET_I_SHORELINE_NAME = d3.TARGET_I_SHORELINE_NAME
TARGET_I_SHORELINE_SHA256 = d3.TARGET_I_SHORELINE_SHA256
TARGET_PALEO_SPATIAL_SHA256 = d3.TARGET_PALEO_SPATIAL_SHA256

REQUIRED_HYDRO_FIELDS = (
    "annual_runoff_mm_yr",
    "mean_discharge_m3_s",
    "minimum_month_discharge_m3_s",
    "maximum_month_discharge_m3_s",
    "discharge_seasonality_cv",
    "channel_mask",
    "perennial_channel_mask",
    "seasonal_channel_mask",
    "lake_candidate_mask",
    "lat",
    "lon",
    "resolution_deg",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def finite_stats(arr: np.ndarray, mask: np.ndarray | None = None) -> dict[str, Any]:
    a = np.asarray(arr)
    valid = np.isfinite(a)
    if mask is not None:
        valid &= np.asarray(mask, dtype=bool)
    vals = a[valid]
    if vals.size == 0:
        return {"count": 0, "min": None, "max": None, "mean": None, "p50": None, "p95": None}
    vals64 = vals.astype(np.float64, copy=False)
    return {
        "count": int(vals64.size),
        "min": float(np.min(vals64)),
        "max": float(np.max(vals64)),
        "mean": float(np.mean(vals64)),
        "p50": float(np.percentile(vals64, 50)),
        "p95": float(np.percentile(vals64, 95)),
    }


def periodic_grid_distance_km(source_mask: np.ndarray, lat: np.ndarray, resolution_deg: float) -> tuple[np.ndarray, int]:
    """ARCANA/R3.14-compatible periodic-longitude proximity approximation.

    This is geometric proximity on the raster, not travel time, route cost, or guaranteed human access.
    """
    src = np.asarray(source_mask, dtype=bool)
    if src.ndim != 2:
        raise ValueError(f"source mask must be 2D, got {src.shape}")
    source_count = int(np.count_nonzero(src))
    if source_count == 0:
        return np.full(src.shape, np.nan, dtype=np.float32), 0
    tiled = np.concatenate((src, src, src), axis=1)
    dcell = distance_transform_edt(~tiled)[:, src.shape[1]:2 * src.shape[1]]
    dy_km = 111.195 * float(resolution_deg)
    coslat = np.maximum(np.cos(np.deg2rad(np.asarray(lat, dtype=float)))[:, None], 0.08)
    dkm = dcell * dy_km * np.sqrt(coslat)
    return dkm.astype(np.float32), source_count


def load_hydrology(path: Path, expected_sha: str | None = None) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_sha = sha256_file(path)
    if expected_sha and actual_sha.lower() != expected_sha.lower():
        raise RuntimeError(f"hydrology hash mismatch for {path}: {actual_sha} != {expected_sha}")
    with np.load(path, allow_pickle=False) as z:
        missing = sorted(set(REQUIRED_HYDRO_FIELDS) - set(z.files))
        if missing:
            raise RuntimeError(f"hydrology payload {path} missing required fields {missing}")
        payload = {k: np.asarray(z[k]).copy() for k in REQUIRED_HYDRO_FIELDS}
    payload["path"] = str(path.resolve())
    payload["sha256"] = actual_sha
    return payload


def low_flow_fraction(minimum_q: np.ndarray, mean_q: np.ndarray) -> np.ndarray:
    qmin = np.asarray(minimum_q, dtype=np.float64)
    qmean = np.asarray(mean_q, dtype=np.float64)
    if qmin.shape != qmean.shape:
        raise RuntimeError("minimum/mean discharge shape mismatch")
    if np.any(~np.isfinite(qmin)) or np.any(~np.isfinite(qmean)):
        raise RuntimeError("minimum/mean discharge contains non-finite values")
    if np.any(qmin < 0.0) or np.any(qmean < 0.0):
        raise RuntimeError("negative discharge encountered")
    if np.any(qmin > qmean):
        bad = int(np.count_nonzero(qmin > qmean))
        raise RuntimeError(f"minimum_month_discharge exceeds mean_discharge in {bad} cells")
    out = np.zeros(qmean.shape, dtype=np.float32)
    positive = qmean > 0.0
    out[positive] = (qmin[positive] / qmean[positive]).astype(np.float32)
    return out


def derive_state(hy: dict[str, Any], land_mask: np.ndarray) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    land = np.asarray(land_mask, dtype=bool)
    lat = np.asarray(hy["lat"], dtype=float)
    lon = np.asarray(hy["lon"], dtype=float)
    resolution = float(np.asarray(hy["resolution_deg"]).reshape(()))
    grid_shape = land.shape
    if lat.shape != (grid_shape[0],) or lon.shape != (grid_shape[1],):
        raise RuntimeError(f"lat/lon shape mismatch: lat={lat.shape} lon={lon.shape} grid={grid_shape}")

    channel = np.asarray(hy["channel_mask"]).astype(bool)
    perennial = np.asarray(hy["perennial_channel_mask"]).astype(bool)
    seasonal = np.asarray(hy["seasonal_channel_mask"]).astype(bool)
    lake = np.asarray(hy["lake_candidate_mask"]).astype(bool)
    for name, arr in (("channel", channel), ("perennial", perennial), ("seasonal", seasonal), ("lake", lake)):
        if arr.shape != grid_shape:
            raise RuntimeError(f"{name} mask shape {arr.shape} != {grid_shape}")

    d_perennial, n_perennial = periodic_grid_distance_km(perennial, lat, resolution)
    d_channel, n_channel = periodic_grid_distance_km(channel, lat, resolution)
    d_lake, n_lake = periodic_grid_distance_km(lake, lat, resolution)
    source_union = perennial | lake
    d_reliable_candidate, n_union = periodic_grid_distance_km(source_union, lat, resolution)

    for arr in (d_perennial, d_channel, d_lake, d_reliable_candidate):
        arr[~land] = np.nan

    low = low_flow_fraction(hy["minimum_month_discharge_m3_s"], hy["mean_discharge_m3_s"])
    low[~land] = np.nan

    derived = {
        "distance_to_perennial_channel_km": d_perennial,
        "distance_to_any_channel_km": d_channel,
        "distance_to_lake_candidate_km": d_lake,
        "distance_to_perennial_or_lake_candidate_km": d_reliable_candidate,
        "low_flow_fraction_minimum_over_mean": low,
        "land_mask": land.astype(np.uint8),
        "perennial_channel_mask": perennial.astype(np.uint8),
        "channel_mask": channel.astype(np.uint8),
        "lake_candidate_mask": lake.astype(np.uint8),
    }

    report = {
        "hydrology_path": hy["path"],
        "hydrology_sha256": hy["sha256"],
        "resolution_deg": resolution,
        "land_cell_count": int(np.count_nonzero(land)),
        "source_counts": {
            "perennial_channel": n_perennial,
            "any_channel": n_channel,
            "lake_candidate": n_lake,
            "perennial_or_lake_candidate": n_union,
        },
        "land_stats": {
            "distance_to_perennial_channel_km": finite_stats(d_perennial, land),
            "distance_to_any_channel_km": finite_stats(d_channel, land),
            "distance_to_lake_candidate_km": finite_stats(d_lake, land),
            "distance_to_perennial_or_lake_candidate_km": finite_stats(d_reliable_candidate, land),
            "low_flow_fraction_minimum_over_mean": finite_stats(low, land),
            "annual_runoff_mm_yr": finite_stats(np.asarray(hy["annual_runoff_mm_yr"]), land),
            "mean_discharge_m3_s": finite_stats(np.asarray(hy["mean_discharge_m3_s"]), land),
            "discharge_seasonality_cv": finite_stats(np.asarray(hy["discharge_seasonality_cv"]), land),
        },
    }
    return derived, report


def safe_persistence(mask_stack: np.ndarray, land_stack: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mask = np.asarray(mask_stack, dtype=bool)
    land = np.asarray(land_stack, dtype=bool)
    if mask.shape != land.shape:
        raise RuntimeError("persistence mask/land stack shape mismatch")
    denom = np.sum(land, axis=0, dtype=np.int16)
    numer = np.sum(mask & land, axis=0, dtype=np.int16)
    frac = np.full(denom.shape, np.nan, dtype=np.float32)
    valid = denom > 0
    frac[valid] = (numer[valid] / denom[valid]).astype(np.float32)
    return frac, denom.astype(np.uint8)


def mean_across_land_snapshots(values: np.ndarray, land_stack: np.ndarray) -> np.ndarray:
    a = np.asarray(values, dtype=np.float64)
    land = np.asarray(land_stack, dtype=bool)
    valid = land & np.isfinite(a)
    count = np.sum(valid, axis=0)
    total = np.sum(np.where(valid, a, 0.0), axis=0)
    out = np.full(count.shape, np.nan, dtype=np.float32)
    ok = count > 0
    out[ok] = (total[ok] / count[ok]).astype(np.float32)
    return out


def validate_bundle(path: Path, grid_shape: tuple[int, int], snapshot_count: int) -> dict[str, Any]:
    required = {
        "lat", "lon", "resolution_deg", "snapshot_year_before_book",
        "book_land_mask", "book_distance_to_perennial_channel_km",
        "book_distance_to_any_channel_km", "book_distance_to_lake_candidate_km",
        "book_distance_to_perennial_or_lake_candidate_km",
        "book_low_flow_fraction_minimum_over_mean",
        "snapshot_land_mask", "snapshot_distance_to_perennial_channel_km",
        "snapshot_distance_to_any_channel_km", "snapshot_distance_to_lake_candidate_km",
        "snapshot_distance_to_perennial_or_lake_candidate_km",
        "snapshot_low_flow_fraction_minimum_over_mean",
        "perennial_channel_persistence_fraction", "any_channel_persistence_fraction",
        "lake_candidate_persistence_fraction", "perennial_or_lake_candidate_persistence_fraction",
        "land_snapshot_count", "mean_distance_to_perennial_or_lake_candidate_km_across_land_snapshots",
    }
    report: dict[str, Any] = {"path": str(path.resolve()), "sha256": sha256_file(path)}
    with np.load(path, allow_pickle=False) as z:
        missing = sorted(required - set(z.files))
        report["missing_required_fields"] = missing
        if missing:
            report["valid"] = False
            return report
        expected_snapshot_shape = (snapshot_count,) + grid_shape
        checks = {
            "book_grid_shape": np.asarray(z["book_land_mask"]).shape == grid_shape,
            "snapshot_grid_shape": np.asarray(z["snapshot_land_mask"]).shape == expected_snapshot_shape,
            "snapshot_year_count": np.asarray(z["snapshot_year_before_book"]).shape == (snapshot_count,),
        }
        for key in (
            "book_distance_to_perennial_channel_km",
            "book_distance_to_any_channel_km",
            "book_distance_to_lake_candidate_km",
            "book_distance_to_perennial_or_lake_candidate_km",
            "book_low_flow_fraction_minimum_over_mean",
            "perennial_channel_persistence_fraction",
            "any_channel_persistence_fraction",
            "lake_candidate_persistence_fraction",
            "perennial_or_lake_candidate_persistence_fraction",
            "mean_distance_to_perennial_or_lake_candidate_km_across_land_snapshots",
        ):
            checks[f"shape_{key}"] = np.asarray(z[key]).shape == grid_shape
        for key in (
            "snapshot_distance_to_perennial_channel_km",
            "snapshot_distance_to_any_channel_km",
            "snapshot_distance_to_lake_candidate_km",
            "snapshot_distance_to_perennial_or_lake_candidate_km",
            "snapshot_low_flow_fraction_minimum_over_mean",
        ):
            checks[f"shape_{key}"] = np.asarray(z[key]).shape == expected_snapshot_shape

        range_ok = True
        for key in (
            "book_low_flow_fraction_minimum_over_mean",
            "perennial_channel_persistence_fraction",
            "any_channel_persistence_fraction",
            "lake_candidate_persistence_fraction",
            "perennial_or_lake_candidate_persistence_fraction",
        ):
            a = np.asarray(z[key], dtype=float)
            finite = np.isfinite(a)
            if np.any(finite):
                range_ok = range_ok and bool(np.all((a[finite] >= 0.0) & (a[finite] <= 1.0)))
        a = np.asarray(z["snapshot_low_flow_fraction_minimum_over_mean"], dtype=float)
        finite = np.isfinite(a)
        if np.any(finite):
            range_ok = range_ok and bool(np.all((a[finite] >= 0.0) & (a[finite] <= 1.0)))
        checks["ratio_and_persistence_ranges_0_1"] = bool(range_ok)

        distance_ok = True
        for key in [k for k in z.files if "distance_to_" in k]:
            a = np.asarray(z[key], dtype=float)
            finite = np.isfinite(a)
            if np.any(finite):
                distance_ok = distance_ok and bool(np.all(a[finite] >= 0.0))
        checks["distance_nonnegative"] = bool(distance_ok)
        report["checks"] = checks
        report["valid"] = bool(all(checks.values()))
        report["keys"] = sorted(z.files)
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=(
        "R5.17-B6-D4: derive transparent freshwater-access and hydrological-reliability axes from the "
        "governed D3R book-era and five-snapshot paleohydrology states. No opaque water score, safe-yield "
        "claim, persons/cell calibration, external provider, or K(x,t) is introduced."
    ))
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--d3r-json", type=Path, required=True)
    ap.add_argument("--bundle-output", type=Path,
                    default=Path("R5_17_B6_D4_DERIVED/freshwater_support_reliability_bundle.npz"))
    ap.add_argument("--output", type=Path,
                    default=Path("R5_17_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    d3r = json.loads(args.d3r_json.read_text(encoding="utf-8")) if args.d3r_json.is_file() else {}
    result: dict[str, Any] = {
        "schema": "ARCANA_R5_17_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D4",
        "purpose": (
            "Translate governed physical paleohydrology into inspectable human-facing freshwater proximity "
            "and reliability axes while keeping raw hydrological evidence separate and avoiding a single "
            "opaque freshwater/civilization score."
        ),
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
        },
        "scientific_engine_suitability": {
            "scientific_question": "derive cell-level freshwater proximity and snapshot-sampled reliability from governed ARCANA physical hydrology",
            "existing_arcana_authority": {
                "candidates": ["R5.17-B6-D3R reconstructed book and snapshot channel hydrology"],
                "exact_identity_verified": True,
                "semantics_sufficient_as_physical_derivation_basis": True,
                "decision": "REUSE_CANONICAL_ARCANA_AS_INPUT_AUTHORITY",
            },
            "existing_validated_engines": {
                "candidates": ["NEMO", "Geonomics", "SLiM", "tskit/msprime/pyslim", "CDMetaPOP", "RangeShiftR"],
                "selected": None,
                "decision": "NOT_APPLICABLE_TO_TRANSPARENT_SURFACE_WATER_PROXIMITY_AND_PERSISTENCE_TRANSFORM",
            },
            "new_specialist_tools": {"selected": None, "audit_required": False},
            "selected_provider": {
                "name": "ARCANA minimum transparent derived-layer transform",
                "role": "EVIDENCE_PROVIDER_ONLY",
                "runtime_identity": f"Python {platform.python_version()} / NumPy {np.__version__} / SciPy {scipy.__version__}",
                "justification": "The missing operation is raster proximity/persistence transformation, not a missing hydrological process model.",
            },
            "decision_class": "MINIMUM_CUSTOM_IMPLEMENTATION",
            "minimum_custom_scope": "periodic-grid source proximity, low-flow ratio, and five-snapshot persistence only",
        },
        "semantic_contract": {
            "freshwater_support": (
                "A multi-axis surface-water support evidence bundle: physical distance to perennial channels, any channels, "
                "lake candidates, and perennial-or-lake candidates, retaining D3R runoff/discharge payloads by provenance. "
                "It is not safe yield, potable-water volume, irrigation capacity, or persons/cell."
            ),
            "hydrological_reliability": (
                "Within-state minimum/mean discharge ratio plus cross-snapshot source persistence. Persistence is sampled only "
                "at the five governed paleoclimate snapshots and is not continuous-time reliability."
            ),
            "distance_semantics": "R3.14-compatible periodic-longitude raster proximity approximation; not route/travel cost.",
            "lake_semantics": "lake_candidate_mask remains a candidate-waterbody indicator and is never promoted to guaranteed permanent freshwater.",
        },
        "d3r_parent_status": d3r.get("status"),
        "historical_payload_identity_claimed": False,
        "external_provider_authorized": False,
        "canonical_mutation": False,
        "population_target_imposed": False,
        "civilization_target_imposed": False,
        "k_materialized": False,
        "freshwater_support_materialized": False,
        "hydrological_reliability_materialized": False,
    }

    prerequisites = bool(
        d3r.get("status") == "PASS_R517_B6_D3R_CANONICAL_PALEOHYDROLOGY_REPLAY_MATERIALIZED"
        and d3r.get("paleohydrology_materialized") is True
        and d3r.get("freshwater_support_materialized") is False
        and d3r.get("hydrological_reliability_materialized") is False
        and (d3r.get("book_hydrology") or {}).get("validation", {}).get("physical_checks_pass") is True
        and d3r.get("all_snapshot_validations_pass") is True
        and int(d3r.get("snapshot_count", 0)) == 5
    )
    result["prerequisites_satisfied"] = prerequisites
    if not prerequisites:
        status = "BLOCKED_R517_B6_D4_D3R_GATE_NOT_SATISFIED"
        decision = "RETURN_TO_D3R_PALEOHYDROLOGY_AUTHORITY"
    else:
        try:
            shorelines = d2d.locate_named_hash(root, TARGET_I_SHORELINE_NAME, TARGET_I_SHORELINE_SHA256)
            spatial = d2d.locate_hash(root, TARGET_PALEO_SPATIAL_SHA256)
            if not shorelines or not spatial:
                raise RuntimeError("exact shoreline I or paleoclimate spatial authority missing")
            shoreline_path = shorelines[0]
            spatial_path = spatial[0]

            book_rec = d3r["book_hydrology"]["serialized"]
            book_path = Path(book_rec["path"])
            book = load_hydrology(book_path, book_rec.get("sha256"))

            snapshot_recs = sorted(d3r.get("snapshot_results", []), key=lambda r: int(r["snapshot_index"]))
            years = np.array([float(r["snapshot_year_before_book"]) for r in snapshot_recs], dtype=float)
            if years.shape != EXPECTED_SNAPSHOT_YEARS.shape or not np.array_equal(years, EXPECTED_SNAPSHOT_YEARS):
                raise RuntimeError(f"unexpected snapshot chronology {years.tolist()}")
            snapshots = [load_hydrology(Path(r["serialized"]["path"]), r["serialized"].get("sha256")) for r in snapshot_recs]

            with np.load(shoreline_path, allow_pickle=False) as sh:
                book_land = np.asarray(sh["effective_land_mask"]).astype(bool)
                shoreline_lat = np.asarray(sh["lat"], dtype=float)
                shoreline_lon = np.asarray(sh["lon"], dtype=float)
                shoreline_res = float(np.asarray(sh["resolution_deg"]).reshape(()))
            with np.load(spatial_path, allow_pickle=False) as sp:
                spatial_years = np.asarray(sp["snapshot_year_before_book"], dtype=float)
                paleo_land = np.asarray(sp["paleo_land_mask"]).astype(bool)
            if not np.array_equal(spatial_years, years):
                raise RuntimeError("D3R snapshot chronology differs from exact paleoclimate spatial payload")

            grid_shape = book_land.shape
            if paleo_land.shape != (5,) + grid_shape:
                raise RuntimeError(f"paleo land stack shape {paleo_land.shape} != {(5,) + grid_shape}")
            if not np.array_equal(np.asarray(book["lat"], dtype=float), shoreline_lat):
                raise RuntimeError("book hydrology latitude grid differs from shoreline I")
            if not np.array_equal(np.asarray(book["lon"], dtype=float), shoreline_lon):
                raise RuntimeError("book hydrology longitude grid differs from shoreline I")
            if float(np.asarray(book["resolution_deg"]).reshape(())) != shoreline_res:
                raise RuntimeError("book hydrology resolution differs from shoreline I")

            book_derived, book_report = derive_state(book, book_land)
            snapshot_derived: list[dict[str, np.ndarray]] = []
            snapshot_reports: list[dict[str, Any]] = []
            for i, (hy, land) in enumerate(zip(snapshots, paleo_land)):
                der, rep = derive_state(hy, land)
                rep["snapshot_index"] = i
                rep["snapshot_year_before_book"] = float(years[i])
                snapshot_derived.append(der)
                snapshot_reports.append(rep)

            land_stack = np.stack([d["land_mask"].astype(bool) for d in snapshot_derived], axis=0)
            perennial_stack = np.stack([d["perennial_channel_mask"].astype(bool) for d in snapshot_derived], axis=0)
            channel_stack = np.stack([d["channel_mask"].astype(bool) for d in snapshot_derived], axis=0)
            lake_stack = np.stack([d["lake_candidate_mask"].astype(bool) for d in snapshot_derived], axis=0)
            source_union_stack = perennial_stack | lake_stack

            perennial_persist, land_count = safe_persistence(perennial_stack, land_stack)
            channel_persist, land_count_2 = safe_persistence(channel_stack, land_stack)
            lake_persist, land_count_3 = safe_persistence(lake_stack, land_stack)
            union_persist, land_count_4 = safe_persistence(source_union_stack, land_stack)
            if not (np.array_equal(land_count, land_count_2) and np.array_equal(land_count, land_count_3) and np.array_equal(land_count, land_count_4)):
                raise RuntimeError("internal land-snapshot denominator mismatch")

            snap_d_per = np.stack([d["distance_to_perennial_channel_km"] for d in snapshot_derived], axis=0)
            snap_d_any = np.stack([d["distance_to_any_channel_km"] for d in snapshot_derived], axis=0)
            snap_d_lake = np.stack([d["distance_to_lake_candidate_km"] for d in snapshot_derived], axis=0)
            snap_d_union = np.stack([d["distance_to_perennial_or_lake_candidate_km"] for d in snapshot_derived], axis=0)
            snap_low = np.stack([d["low_flow_fraction_minimum_over_mean"] for d in snapshot_derived], axis=0)
            mean_d_union = mean_across_land_snapshots(snap_d_union, land_stack)

            bundle_path = args.bundle_output.resolve()
            bundle_path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(
                bundle_path,
                lat=shoreline_lat.astype(np.float64),
                lon=shoreline_lon.astype(np.float64),
                resolution_deg=np.asarray(shoreline_res, dtype=np.float64),
                snapshot_year_before_book=years.astype(np.float64),
                book_land_mask=book_derived["land_mask"],
                book_distance_to_perennial_channel_km=book_derived["distance_to_perennial_channel_km"],
                book_distance_to_any_channel_km=book_derived["distance_to_any_channel_km"],
                book_distance_to_lake_candidate_km=book_derived["distance_to_lake_candidate_km"],
                book_distance_to_perennial_or_lake_candidate_km=book_derived["distance_to_perennial_or_lake_candidate_km"],
                book_low_flow_fraction_minimum_over_mean=book_derived["low_flow_fraction_minimum_over_mean"],
                snapshot_land_mask=land_stack.astype(np.uint8),
                snapshot_distance_to_perennial_channel_km=snap_d_per.astype(np.float32),
                snapshot_distance_to_any_channel_km=snap_d_any.astype(np.float32),
                snapshot_distance_to_lake_candidate_km=snap_d_lake.astype(np.float32),
                snapshot_distance_to_perennial_or_lake_candidate_km=snap_d_union.astype(np.float32),
                snapshot_low_flow_fraction_minimum_over_mean=snap_low.astype(np.float32),
                perennial_channel_persistence_fraction=perennial_persist,
                any_channel_persistence_fraction=channel_persist,
                lake_candidate_persistence_fraction=lake_persist,
                perennial_or_lake_candidate_persistence_fraction=union_persist,
                land_snapshot_count=land_count,
                mean_distance_to_perennial_or_lake_candidate_km_across_land_snapshots=mean_d_union,
            )

            validation = validate_bundle(bundle_path, grid_shape, 5)
            result["input_authority"] = {
                "shoreline_I": {"path": str(shoreline_path), "sha256": sha256_file(shoreline_path)},
                "paleoclimate_spatial": {"path": str(spatial_path), "sha256": sha256_file(spatial_path)},
                "book_hydrology": {"path": book["path"], "sha256": book["sha256"]},
                "snapshot_hydrology": [
                    {"year_before_book": float(years[i]), "path": snapshots[i]["path"], "sha256": snapshots[i]["sha256"]}
                    for i in range(5)
                ],
            }
            result["book_derivation"] = book_report
            result["snapshot_derivations"] = snapshot_reports
            result["cross_snapshot_reliability"] = {
                "sampling_semantics": "five governed paleoclimate snapshots only; irregular chronology; not continuous-time probability",
                "land_snapshot_count_stats": finite_stats(land_count.astype(float)),
                "perennial_channel_persistence_fraction_stats": finite_stats(perennial_persist),
                "any_channel_persistence_fraction_stats": finite_stats(channel_persist),
                "lake_candidate_persistence_fraction_stats": finite_stats(lake_persist),
                "perennial_or_lake_candidate_persistence_fraction_stats": finite_stats(union_persist),
                "mean_distance_to_perennial_or_lake_candidate_km_stats": finite_stats(mean_d_union),
            }
            result["derived_bundle"] = {
                "path": str(bundle_path),
                "sha256": sha256_file(bundle_path),
                "size_bytes": bundle_path.stat().st_size,
                "validation": validation,
            }

            if not validation.get("valid"):
                status = "BLOCKED_R517_B6_D4_DERIVED_BUNDLE_VALIDATION_FAILED"
                decision = "INSPECT_FRESHWATER_SUPPORT_RELIABILITY_BUNDLE"
            else:
                result["freshwater_support_materialized"] = True
                result["hydrological_reliability_materialized"] = True
                status = "PASS_R517_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY_MATERIALIZED"
                decision = "AUTHORIZE_B6_NEXT_ENVIRONMENTAL_WATER_SUPPORT_INTEGRATION"
        except Exception as exc:
            import traceback
            result["execution_error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(limit=24),
            }
            status = "BLOCKED_R517_B6_D4_EXECUTION_ERROR"
            decision = "RESOLVE_D4_DERIVATION_RUNTIME_OR_INPUT_BINDING"

    result["status"] = status
    result["decision"] = decision
    result["next_if_pass"] = "R5.17-B6_ENVIRONMENTAL_WATER_SUPPORT_INTEGRATION_REVIEW"
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "status": status,
        "decision": decision,
        "prerequisites_satisfied": result.get("prerequisites_satisfied", False),
        "freshwater_support_materialized": result.get("freshwater_support_materialized", False),
        "hydrological_reliability_materialized": result.get("hydrological_reliability_materialized", False),
        "k_materialized": result.get("k_materialized", False),
        "external_provider_authorized": result.get("external_provider_authorized", False),
        "bundle_sha256": (result.get("derived_bundle") or {}).get("sha256"),
        "output": str(args.output.resolve()),
    }
    print(json.dumps(summary, indent=2))
    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
