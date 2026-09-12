from __future__ import annotations

import argparse
import ast
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
import R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY as d3

TARGET_I_SHORELINE_NAME = d3.TARGET_I_SHORELINE_NAME
TARGET_I_SHORELINE_SHA256 = d3.TARGET_I_SHORELINE_SHA256
TARGET_SEASONAL_SUFFIX = d3.TARGET_SEASONAL_SUFFIX
TARGET_SEASONAL_SHA256 = d3.TARGET_SEASONAL_SHA256
TARGET_HYDROLOGY_SUFFIX = d3.TARGET_HYDROLOGY_SUFFIX
TARGET_HYDROLOGY_SHA256 = d3.TARGET_HYDROLOGY_SHA256
TARGET_PALEO_SPATIAL_SHA256 = d3.TARGET_PALEO_SPATIAL_SHA256
TARGET_RECENT_HISTORY_SHA256 = d3.TARGET_RECENT_HISTORY_SHA256
REQUIRED_HYDROLOGY_FIELDS = d3.REQUIRED_HYDROLOGY_FIELDS

AUTHORIZED_ALIASES = {
    "land_mask": "effective_land_mask",
}


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


def coast_contract_from_ast(path: Path, function_name: str = "build_channel_hydrology") -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)
    fn: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            fn = node
            break
    if fn is None:
        return {"found": False, "coast_argument_names": [], "coast_attributes": []}

    args = [a.arg for a in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs]
    coast_names = {n for n in args if "coast" in n.lower() or "margin" in n.lower() or "shore" in n.lower()}
    if not coast_names and len(args) >= 2:
        coast_names.add(args[1])

    attrs: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in coast_names:
            attrs.add(node.attr)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2:
            base, attr = node.args[0], node.args[1]
            if isinstance(base, ast.Name) and base.id in coast_names and isinstance(attr, ast.Constant) and isinstance(attr.value, str):
                attrs.add(attr.value)

    return {
        "found": True,
        "function": function_name,
        "signature": ast.unparse(fn.args) if hasattr(ast, "unparse") else None,
        "coast_argument_names": sorted(coast_names),
        "coast_attributes": sorted(attrs),
        "line_start": fn.lineno,
        "line_end": getattr(fn, "end_lineno", fn.lineno),
    }


def build_shoreline_adapter(shoreline_path: Path, contract: dict[str, Any]) -> tuple[SimpleNamespace | None, dict[str, Any]]:
    with np.load(shoreline_path, allow_pickle=False) as z:
        keys = set(z.files)
        mapping: dict[str, str] = {}
        missing: list[str] = []
        payload: dict[str, Any] = {}

        for attr in contract.get("coast_attributes", []):
            if attr in keys:
                source = attr
            elif attr in AUTHORIZED_ALIASES and AUTHORIZED_ALIASES[attr] in keys:
                source = AUTHORIZED_ALIASES[attr]
            else:
                missing.append(attr)
                continue
            arr = np.asarray(z[source]).copy()
            if attr.endswith("mask") or attr in {"land_mask", "ocean_mask"}:
                arr = arr.astype(bool, copy=False)
            payload[attr] = arr
            mapping[attr] = source

        # These two are independently required by the already validated seasonal generator.
        if "elevation_m" not in payload:
            if "elevation_m" in keys:
                payload["elevation_m"] = np.asarray(z["elevation_m"], dtype=float).copy()
                mapping["elevation_m"] = "elevation_m"
            else:
                missing.append("elevation_m")
        if "land_mask" not in payload:
            if "effective_land_mask" in keys:
                payload["land_mask"] = np.asarray(z["effective_land_mask"]).astype(bool, copy=True)
                mapping["land_mask"] = "effective_land_mask"
            else:
                missing.append("land_mask")

        report = {
            "shoreline_path": str(shoreline_path.resolve()),
            "shoreline_sha256": sha256_file(shoreline_path),
            "shoreline_keys": sorted(keys),
            "required_coast_attributes": contract.get("coast_attributes", []),
            "mapping": mapping,
            "authorized_aliases": AUTHORIZED_ALIASES,
            "missing_required_attributes": sorted(set(missing)),
            "adapter_ready": not missing,
        }
        return (SimpleNamespace(**payload) if not missing else None), report


def transformed_snapshot_coast(base: SimpleNamespace, elevation: np.ndarray, land_mask: np.ndarray) -> SimpleNamespace:
    payload = dict(vars(base))
    payload["elevation_m"] = np.asarray(elevation, dtype=float)
    payload["land_mask"] = np.asarray(land_mask, dtype=bool)
    # Keep directly represented complement coherent if the consumer asks for it.
    if "ocean_mask" in payload:
        payload["ocean_mask"] = ~payload["land_mask"]
    return SimpleNamespace(**payload)


def main() -> None:
    ap = argparse.ArgumentParser(description=(
        "R5.17-B6-D3R: resolve the exact build_channel_hydrology coast-state interface from source AST, "
        "bind it to authenticated shoreline_state_I fields using only direct same-name fields plus the "
        "D2C1-authorized land_mask <- effective_land_mask alias, then rerun the D3 paleohydrology replay."
    ))
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--d2d5-json", type=Path, required=True)
    ap.add_argument("--d3-json", type=Path, required=True)
    ap.add_argument("--reconstructed-seasonal", type=Path, required=True)
    ap.add_argument("--reconstructed-dir", type=Path, default=Path("R5_17_B6_D3_RECONSTRUCTED"))
    ap.add_argument("--output", type=Path, default=Path("R5_17_B6_D3R_I_COAST_CONTRACT_AND_REPLAY.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    reconstructed_seasonal = args.reconstructed_seasonal.resolve()
    out_dir = args.reconstructed_dir.resolve()
    d3_parent = json.loads(args.d3_json.read_text(encoding="utf-8")) if args.d3_json.is_file() else {}

    result: dict[str, Any] = {
        "schema": "ARCANA_R5_17_B6_D3R_I_COAST_CONTRACT_AND_REPLAY_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D3R",
        "purpose": "Repair only the I shoreline -> build_channel_hydrology interface binding after D3 execution failure; no scientific law, source hash, provider, or tolerance changes.",
        "runtime": {"python_executable": sys.executable, "python_version": platform.python_version(), "numpy_version": np.__version__},
        "d3_parent_status": d3_parent.get("status"),
        "d3_parent_execution_error": d3_parent.get("execution_error"),
        "historical_provenance_gap_preserved": True,
        "historical_payload_identity_claimed": False,
        "external_provider_authorized": False,
        "canonical_mutation": False,
        "freshwater_support_materialized": False,
        "hydrological_reliability_materialized": False,
        "paleohydrology_materialized": False,
        "snapshot_results": [],
    }

    gate = d3.load_d2d5_gate(args.d2d5_json.resolve(), reconstructed_seasonal)
    result["d2d5_gate"] = gate
    shorelines = d2d.locate_named_hash(root, TARGET_I_SHORELINE_NAME, TARGET_I_SHORELINE_SHA256)
    seasonals = d2d.locate_exact_suffix(root, TARGET_SEASONAL_SUFFIX, TARGET_SEASONAL_SHA256)
    hydrologies = d2d.locate_exact_suffix(root, TARGET_HYDROLOGY_SUFFIX, TARGET_HYDROLOGY_SHA256)
    spatial = d2d.locate_hash(root, TARGET_PALEO_SPATIAL_SHA256)
    recent = d2d.locate_hash(root, TARGET_RECENT_HISTORY_SHA256)

    prerequisites = bool(gate.get("gate_satisfied") and shorelines and seasonals and hydrologies and spatial and recent)
    result["prerequisites_satisfied"] = prerequisites
    if not prerequisites:
        status = "BLOCKED_R517_B6_D3R_PREREQUISITES_NOT_SATISFIED"
        decision = "RESTORE_D2D5_OR_EXACT_D3_INPUT_BINDING"
    else:
        seasonal_src = seasonals[0]
        hydro_src = hydrologies[0]
        shoreline = shorelines[0]
        spatial_path = spatial[0]
        recent_path = recent[0]
        src_root = d2d.generator_source_root(seasonal_src)
        project_root = src_root.parent

        contract = coast_contract_from_ast(hydro_src)
        result["hydrology_coast_contract"] = contract
        coast, adapter = build_shoreline_adapter(shoreline, contract)
        result["shoreline_adapter"] = adapter

        if not contract.get("found"):
            status = "BLOCKED_R517_B6_D3R_HYDROLOGY_COAST_CONTRACT_NOT_FOUND"
            decision = "INSPECT_EXACT_HYDROLOGY_SOURCE"
        elif coast is None:
            status = "BLOCKED_R517_B6_D3R_SHORELINE_CANNOT_SATISFY_HYDROLOGY_COAST_CONTRACT"
            decision = "RECOVER_OR_ADJUDICATE_MISSING_I_COAST_ATTRIBUTES"
        else:
            try:
                for name in list(sys.modules):
                    if name == "arcana_worldsim" or name.startswith("arcana_worldsim."):
                        del sys.modules[name]
                seasonal_fn = import_exact_callable(src_root, "arcana_worldsim.finalization.seasonal", "build_seasonal_climate", seasonal_src)
                hydro_fn = import_exact_callable(src_root, "arcana_worldsim.finalization.hydrology", "build_channel_hydrology", hydro_src)

                book_seasonal = seasonal_fn(project_root, coast)
                with tempfile.TemporaryDirectory(prefix="arcana_r517_b6_d3r_") as td:
                    temp_seasonal = Path(td) / "seasonal_I_replay.npz"
                    d3.serialize_native(book_seasonal, temp_seasonal)
                    cmp = d3.compare_npz_exact(temp_seasonal, reconstructed_seasonal)
                    result["reconstructed_seasonal_binding_check"] = cmp
                    if not cmp.get("all_arrays_exact"):
                        status = "BLOCKED_R517_B6_D3R_RECONSTRUCTED_SEASONAL_BINDING_NONEXACT"
                        decision = "RETURN_TO_D2D5_RECONSTRUCTED_SEASONAL_AUTHORITY"
                    else:
                        book_hydro = hydro_fn(project_root, coast, book_seasonal)
                        out_dir.mkdir(parents=True, exist_ok=True)
                        book_path = out_dir / "channel_hydrology_state_I_RECONSTRUCTED.npz"
                        book_serialized = d3.serialize_native(book_hydro, book_path)
                        grid_shape = np.asarray(vars(coast)["elevation_m"]).shape
                        book_validation = d3.validate_hydrology_payload(book_path, grid_shape)
                        result["book_hydrology"] = {"serialized": book_serialized, "validation": book_validation}

                        if not (book_validation.get("required_fields_present") and book_validation.get("physical_checks_pass")):
                            status = "BLOCKED_R517_B6_D3R_BOOK_HYDROLOGY_VALIDATION_FAILED"
                            decision = "INSPECT_RECONSTRUCTED_I_HYDROLOGY_PAYLOAD"
                        else:
                            with np.load(spatial_path, allow_pickle=False) as sp, np.load(recent_path, allow_pickle=False) as rh:
                                years = np.asarray(sp["snapshot_year_before_book"], dtype=float)
                                temp_anom = np.asarray(sp["temperature_anomaly_c"], dtype=float)
                                precip_factor = np.asarray(sp["precipitation_factor_relative_book"], dtype=float)
                                paleo_land = np.asarray(sp["paleo_land_mask"]).astype(bool)
                                rt = np.asarray(rh["time_year_before_book"], dtype=float)
                                rsea = np.asarray(rh["sea_level_anomaly_m"], dtype=float)

                            elevation0 = np.asarray(vars(coast)["elevation_m"], dtype=float)
                            all_ok = True
                            for k, year in enumerate(years):
                                ridx = int(np.argmin(np.abs(rt - year)))
                                time_delta = float(abs(rt[ridx] - year))
                                if time_delta > 50.000001:
                                    raise RuntimeError(f"no recent-history sea-level match within 50 years for snapshot {year}")
                                sea_level = float(rsea[ridx])
                                snapshot_coast = transformed_snapshot_coast(coast, elevation0 - sea_level, paleo_land[k])
                                snapshot_seasonal = d3.make_snapshot_seasonal(book_seasonal, temp_anom[k], precip_factor[k])
                                hydro = hydro_fn(project_root, snapshot_coast, snapshot_seasonal)
                                label = f"m{int(abs(round(year))):06d}ybp" if year < 0 else f"p{int(round(year)):06d}y"
                                path = out_dir / f"channel_hydrology_state_{label}_RECONSTRUCTED.npz"
                                serialized = d3.serialize_native(hydro, path)
                                validation = d3.validate_hydrology_payload(path, grid_shape)
                                land_from_elevation = np.asarray(vars(snapshot_coast)["elevation_m"]) > 0.0
                                coast_consistency = bool(np.array_equal(land_from_elevation, np.asarray(vars(snapshot_coast)["land_mask"])))
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
                                all_ok = all_ok and bool(validation.get("required_fields_present") and validation.get("physical_checks_pass") and coast_consistency)

                            result["snapshot_count"] = len(result["snapshot_results"])
                            result["all_snapshot_validations_pass"] = bool(all_ok)
                            if not all_ok or len(result["snapshot_results"]) != len(years):
                                status = "BLOCKED_R517_B6_D3R_PALEOHYDROLOGY_SNAPSHOT_VALIDATION_FAILED"
                                decision = "INSPECT_SNAPSHOT_COAST_OR_HYDROLOGY_OUTPUT"
                            else:
                                result["paleohydrology_materialized"] = True
                                status = "PASS_R517_B6_D3R_CANONICAL_PALEOHYDROLOGY_REPLAY_MATERIALIZED"
                                decision = "AUTHORIZE_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY_DERIVATION"
            except Exception as exc:
                result["execution_error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(limit=30)}
                status = "BLOCKED_R517_B6_D3R_EXECUTION_ERROR"
                decision = "INSPECT_EXACT_D3R_EXECUTION_ERROR"

    result["status"] = status
    result["decision"] = decision
    result["next_if_pass"] = "R5.17-B6-D4_FRESHWATER_ACCESS_AND_RELIABILITY_DERIVATION"
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "status": status,
        "decision": decision,
        "prerequisites_satisfied": result.get("prerequisites_satisfied", False),
        "coast_contract_attributes": (result.get("hydrology_coast_contract") or {}).get("coast_attributes", []),
        "missing_coast_attributes": (result.get("shoreline_adapter") or {}).get("missing_required_attributes", []),
        "adapter_ready": (result.get("shoreline_adapter") or {}).get("adapter_ready", False),
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
