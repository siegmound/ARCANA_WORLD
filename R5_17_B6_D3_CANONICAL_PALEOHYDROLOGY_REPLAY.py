from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import platform
import sys
import tempfile
import traceback
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

import R5_17_B6_D2D_VALIDATE_SEASONAL_GENERATOR_AND_RECONSTRUCT_I as d2d
import R5_17_B6_D2D3_VALIDATE_SERIALIZED_MARGIN_REPLAY_AND_RECONSTRUCT_I as d2d3
import R5_17_B6_D2D5_FULL_IN_MEMORY_F_CHAIN_REPLAY_AND_I_RECONSTRUCTION as d2d5

TARGET_I_SHORELINE_NAME = d2d3.TARGET_I_SHORELINE_NAME
TARGET_I_SHORELINE_SHA256 = d2d3.TARGET_I_SHORELINE_SHA256
TARGET_SEASONAL_SUFFIX = d2d3.TARGET_GENERATOR_SUFFIX
TARGET_SEASONAL_SHA256 = d2d3.TARGET_GENERATOR_SHA256
TARGET_HYDROLOGY_SUFFIX = d2d3.TARGET_HYDROLOGY_SUFFIX
TARGET_HYDROLOGY_SHA256 = d2d3.TARGET_HYDROLOGY_SHA256
TARGET_PALEO_SPATIAL_SHA256 = "a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd"
TARGET_RECENT_HISTORY_SHA256 = "be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1"
REQUIRED_HYDROLOGY_FIELDS = (
    "mean_discharge_m3_s",
    "drainage_area_km2",
    "receiver_flat",
    "lake_candidate_mask",
    "depression_depth_m",
)
PET_TEMP_COEFFICIENT = 0.018
PET_LOG_FACTOR_CLIP = 0.18
PET_MIN_MM = 0.1


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def import_exact_callable(src_root: Path, module_name: str, callable_name: str, expected_path: Path):
    sys.path.insert(0, str(src_root))
    try:
        module = importlib.import_module(module_name)
        module_path = Path(inspect.getsourcefile(module) or "").resolve()
        if module_path != expected_path.resolve():
            raise RuntimeError(f"wrong module binding: {module_path} != {expected_path.resolve()}")
        fn = getattr(module, callable_name)
        if not callable(fn):
            raise TypeError(f"{module_name}.{callable_name} is not callable")
        return fn
    finally:
        if sys.path and sys.path[0] == str(src_root):
            sys.path.pop(0)


def exact_array_equal(a: np.ndarray, b: np.ndarray) -> bool:
    if a.shape != b.shape or a.dtype != b.dtype:
        return False
    if a.dtype.kind in "fc":
        return bool(np.array_equal(a, b, equal_nan=True))
    return bool(np.array_equal(a, b))


def compare_npz_exact(a_path: Path, b_path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "a_path": str(a_path.resolve()),
        "a_sha256": sha256_file(a_path),
        "b_path": str(b_path.resolve()),
        "b_sha256": sha256_file(b_path),
        "fields": {},
    }
    with np.load(a_path, allow_pickle=False) as za, np.load(b_path, allow_pickle=False) as zb:
        ak = sorted(za.files)
        bk = sorted(zb.files)
        out["schema_exact"] = ak == bk
        out["missing_from_a"] = sorted(set(bk) - set(ak))
        out["missing_from_b"] = sorted(set(ak) - set(bk))
        all_exact = ak == bk
        for key in sorted(set(ak) & set(bk)):
            a = np.asarray(za[key])
            b = np.asarray(zb[key])
            exact = exact_array_equal(a, b)
            rec: dict[str, Any] = {
                "a_shape": list(a.shape),
                "b_shape": list(b.shape),
                "a_dtype": str(a.dtype),
                "b_dtype": str(b.dtype),
                "exact": exact,
            }
            if a.shape == b.shape and a.dtype.kind in "biufc" and b.dtype.kind in "biufc":
                af = a.astype(np.float64, copy=False)
                bf = b.astype(np.float64, copy=False)
                finite = np.isfinite(af) & np.isfinite(bf)
                if np.any(finite):
                    delta = np.abs(af[finite] - bf[finite])
                    rec["max_abs_difference"] = float(np.max(delta))
            out["fields"][key] = rec
            all_exact = all_exact and exact
        out["all_arrays_exact"] = bool(all_exact)
    return out


def serialize_native(state: Any, path: Path) -> dict[str, Any]:
    save = getattr(state, "save_npz", None)
    if not callable(save):
        raise RuntimeError(f"state {type(state)!r} has no callable save_npz")
    path.parent.mkdir(parents=True, exist_ok=True)
    save(path)
    if not path.is_file():
        raise RuntimeError(f"save_npz did not create {path}")
    with np.load(path, allow_pickle=False) as z:
        return {
            "path": str(path.resolve()),
            "sha256": sha256_file(path),
            "state_type": f"{type(state).__module__}.{type(state).__name__}",
            "keys": sorted(z.files),
            "arrays": {
                k: {"shape": list(np.asarray(z[k]).shape), "dtype": str(np.asarray(z[k]).dtype)}
                for k in sorted(z.files)
            },
        }


def validate_hydrology_payload(path: Path, grid_shape: tuple[int, int]) -> dict[str, Any]:
    report: dict[str, Any] = {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "required_fields": list(REQUIRED_HYDROLOGY_FIELDS),
        "fields": {},
        "required_fields_present": False,
        "physical_checks_pass": False,
    }
    with np.load(path, allow_pickle=False) as z:
        keys = set(z.files)
        report["keys"] = sorted(keys)
        missing = sorted(set(REQUIRED_HYDROLOGY_FIELDS) - keys)
        report["missing_required_fields"] = missing
        report["required_fields_present"] = not missing
        if missing:
            return report

        q = np.asarray(z["mean_discharge_m3_s"])
        area = np.asarray(z["drainage_area_km2"])
        recv = np.asarray(z["receiver_flat"])
        lake = np.asarray(z["lake_candidate_mask"])
        dep = np.asarray(z["depression_depth_m"])

        for name, arr in (("mean_discharge_m3_s", q), ("drainage_area_km2", area),
                          ("receiver_flat", recv), ("lake_candidate_mask", lake),
                          ("depression_depth_m", dep)):
            rec: dict[str, Any] = {"shape": list(arr.shape), "dtype": str(arr.dtype)}
            if arr.dtype.kind in "fiu":
                finite = np.isfinite(arr.astype(np.float64, copy=False))
                rec["all_finite"] = bool(np.all(finite))
                if np.any(finite):
                    vals = arr.astype(np.float64, copy=False)[finite]
                    rec["min"] = float(np.min(vals))
                    rec["max"] = float(np.max(vals))
            report["fields"][name] = rec

        grid_n = int(grid_shape[0] * grid_shape[1])
        q_ok = q.shape == grid_shape and np.isfinite(q).all() and float(np.min(q)) >= 0.0
        area_ok = area.shape == grid_shape and np.isfinite(area).all() and float(np.min(area)) >= 0.0
        dep_ok = dep.shape == grid_shape and np.isfinite(dep).all() and float(np.min(dep)) >= 0.0
        lake_ok = lake.shape == grid_shape and (
            lake.dtype.kind == "b" or np.all((lake == 0) | (lake == 1))
        )
        recv_flat = recv.reshape(-1)
        recv_ok = recv_flat.size == grid_n and recv.dtype.kind in "iu" and bool(
            np.all((recv_flat >= -1) & (recv_flat < grid_n))
        )
        report["checks"] = {
            "mean_discharge_nonnegative_grid": bool(q_ok),
            "drainage_area_nonnegative_grid": bool(area_ok),
            "depression_depth_nonnegative_grid": bool(dep_ok),
            "lake_candidate_mask_binary_grid": bool(lake_ok),
            "receiver_flat_index_domain_valid": bool(recv_ok),
        }
        report["physical_checks_pass"] = bool(all(report["checks"].values()))
    return report


def make_snapshot_seasonal(book_state: Any, temperature_anomaly: np.ndarray,
                           precipitation_factor: np.ndarray) -> SimpleNamespace:
    mt0 = np.asarray(book_state.monthly_temperature_c, dtype=float)
    mp0 = np.asarray(book_state.monthly_precipitation_mm, dtype=float)
    pet0 = np.asarray(book_state.monthly_pet_mm, dtype=float)
    dt = np.asarray(temperature_anomaly, dtype=float)
    pf = np.asarray(precipitation_factor, dtype=float)
    if mt0.ndim != 3 or mp0.shape != mt0.shape or pet0.shape != mt0.shape:
        raise RuntimeError("unexpected book seasonal monthly-array schema")
    if dt.shape != mt0.shape[1:] or pf.shape != mt0.shape[1:]:
        raise RuntimeError(f"snapshot climate shape mismatch dt={dt.shape} pf={pf.shape} grid={mt0.shape[1:]}")

    mt = mt0 + dt[None, :, :]
    mp = np.maximum(mp0 * pf[None, :, :], 0.0)
    pet_factor = np.exp(np.clip(PET_TEMP_COEFFICIENT * dt, -PET_LOG_FACTOR_CLIP, PET_LOG_FACTOR_CLIP))
    pet = np.maximum(pet0 * pet_factor[None, :, :], PET_MIN_MM)
    return SimpleNamespace(
        monthly_temperature_c=mt,
        monthly_precipitation_mm=mp,
        monthly_pet_mm=pet,
    )


def load_d2d5_gate(path: Path, reconstructed_seasonal: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rec = data.get("reconstructed_baseline") or {}
    actual_sha = sha256_file(reconstructed_seasonal) if reconstructed_seasonal.is_file() else None
    ok = bool(
        data.get("status") == "PASS_R517_B6_D2D5_FULL_IN_MEMORY_F_CHAIN_EXACT_AND_I_BASELINE_RECONSTRUCTED"
        and data.get("full_chain_exact") is True
        and data.get("i_reconstruction_materialized") is True
        and data.get("absolute_or_relative_tolerance_authorized") is False
        and data.get("ulp_tolerance_authorized") is False
        and data.get("historical_payload_identity_claimed") is False
        and reconstructed_seasonal.is_file()
        and rec.get("sha256") == actual_sha
    )
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "status": data.get("status"),
        "full_chain_exact": data.get("full_chain_exact"),
        "reconstructed_seasonal_reported_sha256": rec.get("sha256"),
        "reconstructed_seasonal_actual_sha256": actual_sha,
        "gate_satisfied": ok,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=(
        "R5.17-B6-D3: materialize the reconstructed book-era channel-hydrology baseline and five "
        "canonical paleoclimate-snapshot hydrology states using the exact ARCANA seasonal/hydrology "
        "lineage validated bitwise by D2D5. No external hydrology provider and no human-support/K "
        "field is introduced."
    ))
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--d2d5-json", type=Path, required=True)
    ap.add_argument("--reconstructed-seasonal", type=Path, required=True)
    ap.add_argument("--reconstructed-dir", type=Path,
                    default=Path("R5_17_B6_D3_RECONSTRUCTED"))
    ap.add_argument("--output", type=Path,
                    default=Path("R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    reconstructed_seasonal = args.reconstructed_seasonal.resolve()
    out_dir = args.reconstructed_dir.resolve()

    result: dict[str, Any] = {
        "schema": "ARCANA_R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D3",
        "purpose": (
            "Reuse the exact governed ARCANA v0.5.5F seasonal/hydrology lineage, already validated "
            "bitwise by D2D5, to reconstruct the book-era I hydrology baseline and five physical "
            "paleoclimate snapshot hydrology states."
        ),
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
        },
        "pet_snapshot_binding": {
            "source_semantics": "exact seasonal.py PET temperature-response law reused for temporal anomaly composition",
            "coefficient_per_c": PET_TEMP_COEFFICIENT,
            "log_factor_clip": [-PET_LOG_FACTOR_CLIP, PET_LOG_FACTOR_CLIP],
            "minimum_monthly_pet_mm": PET_MIN_MM,
        },
        "historical_provenance_gap_preserved": True,
        "historical_payload_identity_claimed": False,
        "external_provider_authorized": False,
        "canonical_mutation": False,
        "freshwater_support_materialized": False,
        "hydrological_reliability_materialized": False,
        "paleohydrology_materialized": False,
        "snapshot_results": [],
    }

    d2d5_gate = load_d2d5_gate(args.d2d5_json.resolve(), reconstructed_seasonal)
    result["d2d5_gate"] = d2d5_gate

    shorelines = d2d.locate_named_hash(root, TARGET_I_SHORELINE_NAME, TARGET_I_SHORELINE_SHA256)
    seasonals = d2d.locate_exact_suffix(root, TARGET_SEASONAL_SUFFIX, TARGET_SEASONAL_SHA256)
    hydrologies = d2d.locate_exact_suffix(root, TARGET_HYDROLOGY_SUFFIX, TARGET_HYDROLOGY_SHA256)
    spatial = d2d.locate_hash(root, TARGET_PALEO_SPATIAL_SHA256)
    recent = d2d.locate_hash(root, TARGET_RECENT_HISTORY_SHA256)

    result["source_candidates"] = {
        "i_shoreline": [str(p) for p in shorelines],
        "seasonal_source": [str(p) for p in seasonals],
        "hydrology_source": [str(p) for p in hydrologies],
        "paleoclimate_spatial": [str(p) for p in spatial],
        "recent_history": [str(p) for p in recent],
    }

    prerequisites = bool(d2d5_gate.get("gate_satisfied") and shorelines and seasonals and hydrologies and spatial and recent)
    result["prerequisites_satisfied"] = prerequisites
    if not prerequisites:
        status = "BLOCKED_R517_B6_D3_PREREQUISITES_NOT_SATISFIED"
        decision = "RESTORE_D2D5_OR_EXACT_PALEOHYDROLOGY_INPUT_BINDING"
    else:
        seasonal_src = seasonals[0]
        src_root = d2d.generator_source_root(seasonal_src)
        project_root = src_root.parent
        hydrology_src = hydrologies[0]
        shoreline_path = shorelines[0]
        spatial_path = spatial[0]
        recent_path = recent[0]
        result["selected_binding"] = {
            "project_root": str(project_root),
            "seasonal_source": str(seasonal_src),
            "seasonal_sha256": sha256_file(seasonal_src),
            "hydrology_source": str(hydrology_src),
            "hydrology_sha256": sha256_file(hydrology_src),
            "shoreline_I": str(shoreline_path),
            "shoreline_I_sha256": sha256_file(shoreline_path),
            "paleoclimate_spatial": str(spatial_path),
            "paleoclimate_spatial_sha256": sha256_file(spatial_path),
            "recent_history": str(recent_path),
            "recent_history_sha256": sha256_file(recent_path),
        }

        try:
            for name in list(sys.modules):
                if name == "arcana_worldsim" or name.startswith("arcana_worldsim."):
                    del sys.modules[name]
            seasonal_fn = import_exact_callable(
                src_root, "arcana_worldsim.finalization.seasonal", "build_seasonal_climate", seasonal_src
            )
            hydro_fn = import_exact_callable(
                src_root, "arcana_worldsim.finalization.hydrology", "build_channel_hydrology", hydrology_src
            )

            with np.load(shoreline_path, allow_pickle=False) as sh:
                elevation = np.asarray(sh["elevation_m"], dtype=float).copy()
                effective_land = np.asarray(sh["effective_land_mask"]).astype(bool, copy=True)
                grid_shape = elevation.shape
            i_coast = SimpleNamespace(elevation_m=elevation, land_mask=effective_land)
            book_seasonal_state = seasonal_fn(project_root, i_coast)

            out_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="arcana_r517_b6_d3_") as td:
                temp_seasonal = Path(td) / "seasonal_I_replay.npz"
                serialize_native(book_seasonal_state, temp_seasonal)
                seasonal_cmp = compare_npz_exact(temp_seasonal, reconstructed_seasonal)
                result["reconstructed_seasonal_binding_check"] = seasonal_cmp
                if not seasonal_cmp.get("all_arrays_exact"):
                    status = "BLOCKED_R517_B6_D3_RECONSTRUCTED_SEASONAL_BINDING_NONEXACT"
                    decision = "RETURN_TO_D2D5_RECONSTRUCTED_SEASONAL_AUTHORITY"
                else:
                    book_hydro_state = hydro_fn(project_root, i_coast, book_seasonal_state)
                    book_hydro_path = out_dir / "channel_hydrology_state_I_RECONSTRUCTED.npz"
                    book_serialized = serialize_native(book_hydro_state, book_hydro_path)
                    book_validation = validate_hydrology_payload(book_hydro_path, grid_shape)
                    result["book_hydrology"] = {
                        "serialized": book_serialized,
                        "validation": book_validation,
                    }
                    if not (book_validation.get("required_fields_present") and book_validation.get("physical_checks_pass")):
                        status = "BLOCKED_R517_B6_D3_BOOK_HYDROLOGY_VALIDATION_FAILED"
                        decision = "INSPECT_RECONSTRUCTED_I_HYDROLOGY_PAYLOAD"
                    else:
                        with np.load(spatial_path, allow_pickle=False) as sp, np.load(recent_path, allow_pickle=False) as rh:
                            required_sp = {
                                "snapshot_year_before_book", "temperature_anomaly_c",
                                "precipitation_factor_relative_book", "paleo_land_mask",
                            }
                            if not required_sp.issubset(set(sp.files)):
                                raise RuntimeError(f"paleoclimate spatial payload missing {sorted(required_sp - set(sp.files))}")
                            years = np.asarray(sp["snapshot_year_before_book"], dtype=float)
                            temp_anom = np.asarray(sp["temperature_anomaly_c"], dtype=float)
                            precip_factor = np.asarray(sp["precipitation_factor_relative_book"], dtype=float)
                            paleo_land = np.asarray(sp["paleo_land_mask"]).astype(bool)
                            rt = np.asarray(rh["time_year_before_book"], dtype=float)
                            rsea = np.asarray(rh["sea_level_anomaly_m"], dtype=float)

                        if years.ndim != 1 or temp_anom.shape[0] != years.size or precip_factor.shape[0] != years.size or paleo_land.shape[0] != years.size:
                            raise RuntimeError("paleoclimate snapshot leading dimension mismatch")
                        if temp_anom.shape[1:] != grid_shape or precip_factor.shape[1:] != grid_shape or paleo_land.shape[1:] != grid_shape:
                            raise RuntimeError("paleoclimate snapshot grid mismatch")

                        all_snapshots_ok = True
                        for k, year in enumerate(years):
                            ridx = int(np.argmin(np.abs(rt - year)))
                            time_delta = float(abs(rt[ridx] - year))
                            if time_delta > 50.000001:
                                raise RuntimeError(f"no recent-history sea-level match within 50 years for snapshot {year}")
                            sea_level = float(rsea[ridx])
                            coast = SimpleNamespace(
                                elevation_m=elevation - sea_level,
                                land_mask=paleo_land[k].copy(),
                            )
                            snapshot_seasonal = make_snapshot_seasonal(
                                book_seasonal_state, temp_anom[k], precip_factor[k]
                            )
                            hydro_state = hydro_fn(project_root, coast, snapshot_seasonal)
                            label = f"m{int(abs(round(year))):06d}ybp" if year < 0 else f"p{int(round(year)):06d}y"
                            path = out_dir / f"channel_hydrology_state_{label}_RECONSTRUCTED.npz"
                            serialized = serialize_native(hydro_state, path)
                            validation = validate_hydrology_payload(path, grid_shape)
                            land_from_elevation = coast.elevation_m > 0.0
                            coast_consistency = bool(np.array_equal(land_from_elevation, coast.land_mask))
                            rec = {
                                "snapshot_index": int(k),
                                "snapshot_year_before_book": float(year),
                                "recent_history_time_year_before_book": float(rt[ridx]),
                                "recent_history_time_delta_year": time_delta,
                                "sea_level_anomaly_m": sea_level,
                                "temperature_anomaly_min_c": float(np.min(temp_anom[k])),
                                "temperature_anomaly_max_c": float(np.max(temp_anom[k])),
                                "precipitation_factor_min": float(np.min(precip_factor[k])),
                                "precipitation_factor_max": float(np.max(precip_factor[k])),
                                "coast_land_mask_matches_shifted_elevation_gt_zero": coast_consistency,
                                "serialized": serialized,
                                "validation": validation,
                            }
                            result["snapshot_results"].append(rec)
                            all_snapshots_ok = all_snapshots_ok and bool(
                                validation.get("required_fields_present")
                                and validation.get("physical_checks_pass")
                                and coast_consistency
                            )

                        result["snapshot_count"] = int(len(result["snapshot_results"]))
                        result["all_snapshot_validations_pass"] = bool(all_snapshots_ok)
                        if not all_snapshots_ok or len(result["snapshot_results"]) != int(years.size):
                            status = "BLOCKED_R517_B6_D3_PALEOHYDROLOGY_SNAPSHOT_VALIDATION_FAILED"
                            decision = "INSPECT_SNAPSHOT_COAST_OR_HYDROLOGY_OUTPUT"
                        else:
                            result["paleohydrology_materialized"] = True
                            status = "PASS_R517_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY_MATERIALIZED"
                            decision = "AUTHORIZE_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY_DERIVATION"
        except Exception as exc:
            result["execution_error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(limit=24),
            }
            status = "BLOCKED_R517_B6_D3_EXECUTION_ERROR"
            decision = "RESOLVE_CANONICAL_PALEOHYDROLOGY_REPLAY_RUNTIME"

    result["status"] = status
    result["decision"] = decision
    result["next_if_pass"] = "R5.17-B6-D4_FRESHWATER_ACCESS_AND_RELIABILITY_DERIVATION"
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "status": status,
        "decision": decision,
        "prerequisites_satisfied": result.get("prerequisites_satisfied", False),
        "reconstructed_seasonal_exact": (result.get("reconstructed_seasonal_binding_check") or {}).get("all_arrays_exact"),
        "book_hydrology_valid": bool((result.get("book_hydrology") or {}).get("validation", {}).get("physical_checks_pass")),
        "snapshot_count": result.get("snapshot_count", 0),
        "all_snapshot_validations_pass": result.get("all_snapshot_validations_pass", False),
        "paleohydrology_materialized": result.get("paleohydrology_materialized", False),
        "freshwater_support_materialized": result.get("freshwater_support_materialized", False),
        "output": str(args.output.resolve()),
    }
    print(json.dumps(summary, indent=2))
    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
