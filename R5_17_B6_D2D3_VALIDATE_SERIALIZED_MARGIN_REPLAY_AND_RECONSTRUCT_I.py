from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import platform
import re
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any

import numpy as np

import R5_17_B6_D2D_VALIDATE_SEASONAL_GENERATOR_AND_RECONSTRUCT_I as d2d

TARGET_GENERATOR_SUFFIX = "src/arcana_worldsim/finalization/seasonal.py"
TARGET_GENERATOR_SHA256 = "3ec12145617ae63e6ce9d9bd123c159525f83925f9257f1138f3490bb3e70de2"
TARGET_HYDROLOGY_SUFFIX = "src/arcana_worldsim/finalization/hydrology.py"
TARGET_HYDROLOGY_SHA256 = "29c808bd889d3f0c6e5390775d8751f68b9c9dd2cb5bab1736d6ad6cc6486351"
TARGET_MARGIN_RUNNER_NAME = "run_margin_morphogenesis.py"
TARGET_MARGIN_RUNNER_SHA256 = "028f2c4c423a3eabc849cb50804b5e64ab239bb4752540bc14197353fafb3453"
TARGET_MARGIN_BASELINE_SHA256 = "1b32d97a0b4dad12f01f4c286461d6ca597c2d46a390a8801771735d972d93f6"
TARGET_I_SHORELINE_NAME = "shoreline_state_I.npz"
TARGET_I_SHORELINE_SHA256 = "f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85"
TARGET_HYDROLOGY_FUNCTION = "build_channel_hydrology"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def locate_named_hash(root: Path, name: str, expected_sha: str) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob(name):
        if not p.is_file() or ".git" in p.parts:
            continue
        try:
            if sha256_file(p) == expected_sha:
                out.append(p.resolve())
        except OSError:
            continue
    return sorted(out, key=lambda p: (len(str(p)), norm(p).lower()))


def locate_exact_suffix(root: Path, suffix: str, expected_sha: str) -> list[Path]:
    out: list[Path] = []
    base = Path(suffix).name
    for p in root.rglob(base):
        if not p.is_file() or ".git" in p.parts:
            continue
        if not norm(p).lower().endswith(suffix.lower()):
            continue
        try:
            if sha256_file(p) == expected_sha:
                out.append(p.resolve())
        except OSError:
            continue
    return sorted(out, key=lambda p: (len(str(p)), norm(p).lower()))


def locate_hash(root: Path, expected_sha: str) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*.npz"):
        if not p.is_file() or ".git" in p.parts:
            continue
        try:
            if sha256_file(p) == expected_sha:
                out.append(p.resolve())
        except OSError:
            continue
    return sorted(out, key=lambda p: (len(str(p)), norm(p).lower()))


def exact_array_equal(a: np.ndarray, b: np.ndarray) -> bool:
    if a.shape != b.shape:
        return False
    if a.dtype.kind in "fc" and b.dtype.kind in "fc":
        return bool(np.array_equal(a, b, equal_nan=True))
    return bool(np.array_equal(a, b))


def compare_npz(a_path: Path, b_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "a_path": str(a_path.resolve()),
        "a_sha256": sha256_file(a_path),
        "b_path": str(b_path.resolve()),
        "b_sha256": sha256_file(b_path),
        "fields": {},
    }
    with np.load(a_path, allow_pickle=False) as za, np.load(b_path, allow_pickle=False) as zb:
        a_keys = sorted(za.files)
        b_keys = sorted(zb.files)
        result["a_keys"] = a_keys
        result["b_keys"] = b_keys
        result["schema_key_set_exact"] = a_keys == b_keys
        all_exact = a_keys == b_keys
        common = sorted(set(a_keys) & set(b_keys))
        max_abs = 0.0
        numeric_difference_seen = False
        for key in common:
            a = np.asarray(za[key])
            b = np.asarray(zb[key])
            exact = exact_array_equal(a, b)
            rec: dict[str, Any] = {
                "a_shape": list(a.shape),
                "b_shape": list(b.shape),
                "a_dtype": str(a.dtype),
                "b_dtype": str(b.dtype),
                "exact_array_equal": exact,
            }
            if a.shape == b.shape and a.dtype.kind in "biufc" and b.dtype.kind in "biufc":
                af = a.astype(np.float64, copy=False)
                bf = b.astype(np.float64, copy=False)
                valid = np.isfinite(af) & np.isfinite(bf)
                if np.any(valid):
                    delta = np.abs(af[valid] - bf[valid])
                    rec["max_abs_difference"] = float(np.max(delta))
                    rec["mean_abs_difference"] = float(np.mean(delta))
                    max_abs = max(max_abs, rec["max_abs_difference"])
                    if rec["max_abs_difference"] != 0.0:
                        numeric_difference_seen = True
            result["fields"][key] = rec
            if not exact:
                all_exact = False
        result["missing_from_a"] = sorted(set(b_keys) - set(a_keys))
        result["missing_from_b"] = sorted(set(a_keys) - set(b_keys))
        result["all_arrays_exact"] = bool(all_exact)
        result["max_abs_difference_any_numeric_field"] = max_abs if numeric_difference_seen else 0.0
    return result


def load_d2c1_gate(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    ok = bool(
        data.get("adapter_authorized")
        and data.get("target_shoreline_sha256") == TARGET_I_SHORELINE_SHA256
        and data.get("target_generator_sha256") == TARGET_GENERATOR_SHA256
        and data.get("adapter_mapping", {}).get("land_mask") == "effective_land_mask"
        and data.get("adapter_mapping", {}).get("elevation_m") == "elevation_m"
    )
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "status": data.get("status"),
        "decision": data.get("decision"),
        "adapter_mapping": data.get("adapter_mapping"),
        "gate_satisfied": ok,
    }


def load_d2d2_margin_fixture(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    candidates = []
    for rec in data.get("attempt_diagnostics", []):
        if rec.get("baseline_kind") != "margin_morphogenesis":
            continue
        if not rec.get("stage_aligned_pair"):
            continue
        baseline_path = Path(rec.get("baseline_path", ""))
        coast_path = Path(rec.get("coast_candidate_path", ""))
        if baseline_path.is_file() and coast_path.is_file():
            candidates.append((rec, baseline_path.resolve(), coast_path.resolve()))
    if len(candidates) != 1:
        return {
            "gate_satisfied": False,
            "candidate_count": len(candidates),
            "error": "expected exactly one surviving stage-aligned margin fixture",
        }
    rec, baseline_path, coast_path = candidates[0]
    return {
        "gate_satisfied": sha256_file(baseline_path) == TARGET_MARGIN_BASELINE_SHA256,
        "candidate_count": 1,
        "baseline_path": str(baseline_path),
        "baseline_sha256": sha256_file(baseline_path),
        "margin_state_path": str(coast_path),
        "margin_state_sha256": sha256_file(coast_path),
        "source_attempt_index": rec.get("attempt_index"),
        "source_classification": (rec.get("diagnostics") or {}).get("classification"),
    }


def margin_runner_contract(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    normalized = re.sub(r"\s+", "", text)
    build_call = "seasonal=build_seasonal_climate(root,margin)" in normalized
    save_call = 'seasonal.save_npz(out/"seasonal_climate_state.npz")' in normalized or "seasonal.save_npz(out/'seasonal_climate_state.npz')" in normalized
    margin_build = "margin=build_margin_morphogenesis(root,args.seed)" in normalized
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "margin_build_call_found": margin_build,
        "seasonal_build_call_found": build_call,
        "seasonal_save_call_found": save_call,
        "exact_margin_to_seasonal_lineage_proved": bool(margin_build and build_call and save_call),
    }


def hydrology_seasonal_contract(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)
    target: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == TARGET_HYDROLOGY_FUNCTION:
            target = node
            break
    if target is None:
        return {"found": False, "seasonal_attributes": []}

    seasonal_names: set[str] = set()
    positional = [a.arg for a in target.args.posonlyargs + target.args.args + target.args.kwonlyargs]
    for name in positional:
        if "season" in name.lower() or "climat" in name.lower():
            seasonal_names.add(name)
    if not seasonal_names and len(positional) >= 3:
        seasonal_names.add(positional[2])

    attrs: set[str] = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in seasonal_names:
            attrs.add(node.attr)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2:
            base, attr = node.args[0], node.args[1]
            if isinstance(base, ast.Name) and base.id in seasonal_names and isinstance(attr, ast.Constant) and isinstance(attr.value, str):
                attrs.add(attr.value)

    return {
        "found": True,
        "function": TARGET_HYDROLOGY_FUNCTION,
        "signature": ast.unparse(target.args) if hasattr(ast, "unparse") else None,
        "seasonal_argument_names": sorted(seasonal_names),
        "seasonal_attributes": sorted(attrs),
        "line_start": target.lineno,
        "line_end": getattr(target, "end_lineno", target.lineno),
    }


def serialize_state_native(state: Any, output: Path) -> dict[str, Any]:
    save = getattr(state, "save_npz", None)
    if not callable(save):
        raise RuntimeError(f"returned state type {type(state)!r} has no callable save_npz")
    output.parent.mkdir(parents=True, exist_ok=True)
    sig = inspect.signature(save)
    save(output)
    if not output.is_file():
        raise RuntimeError(f"native save_npz did not materialize {output}")
    with np.load(output, allow_pickle=False) as z:
        keys = sorted(z.files)
        arrays = {
            k: {"shape": list(np.asarray(z[k]).shape), "dtype": str(np.asarray(z[k]).dtype)}
            for k in keys
        }
    return {
        "state_type": f"{type(state).__module__}.{type(state).__name__}",
        "save_npz_signature": str(sig),
        "path": str(output.resolve()),
        "sha256": sha256_file(output),
        "keys": keys,
        "arrays": arrays,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "R5.17-B6-D2D3: validate the exact canonical seasonal generator against its explicit "
            "historical margin-morphogenesis lineage using the state's native save_npz semantics; "
            "if and only if the serialized margin replay is exact, reconstruct the lost I-era "
            "seasonal baseline through the D2C1-authorized shoreline adapter."
        )
    )
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--d2d2-json", type=Path, required=True)
    ap.add_argument("--d2c1-json", type=Path, required=True)
    ap.add_argument(
        "--reconstructed-output",
        type=Path,
        default=Path("R5_17_B6_D2D_RECONSTRUCTED/seasonal_climate_state_I_RECONSTRUCTED.npz"),
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("R5_17_B6_D2D3_SERIALIZED_MARGIN_REPLAY_AND_I_RECONSTRUCTION.json"),
    )
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    result: dict[str, Any] = {
        "schema": "ARCANA_R5_17_B6_D2D3_SERIALIZED_MARGIN_REPLAY_AND_I_RECONSTRUCTION_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2D3",
        "purpose": (
            "Validate build_seasonal_climate using the explicit historical margin_state -> "
            "build_seasonal_climate -> SeasonalClimateState.save_npz -> margin seasonal payload "
            "lineage. Runtime-object schema/dtype differences are not treated as payload "
            "differences; the native serialized NPZ is compared directly."
        ),
        "historical_provenance_gap_preserved": True,
        "tolerance_authorized": False,
        "external_provider_authorized": False,
        "freshwater_support_materialized": False,
        "canonical_mutation": False,
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
        },
    }

    d2c1 = load_d2c1_gate(args.d2c1_json.resolve()) if args.d2c1_json.is_file() else {"gate_satisfied": False, "error": "D2C1 JSON missing"}
    margin_fixture = load_d2d2_margin_fixture(args.d2d2_json.resolve()) if args.d2d2_json.is_file() else {"gate_satisfied": False, "error": "D2D2 JSON missing"}
    result["d2c1_gate"] = d2c1
    result["margin_fixture_gate"] = margin_fixture

    generators = locate_exact_suffix(root, TARGET_GENERATOR_SUFFIX, TARGET_GENERATOR_SHA256)
    hydrologies = locate_exact_suffix(root, TARGET_HYDROLOGY_SUFFIX, TARGET_HYDROLOGY_SHA256)
    runners = locate_named_hash(root, TARGET_MARGIN_RUNNER_NAME, TARGET_MARGIN_RUNNER_SHA256)
    shorelines = locate_named_hash(root, TARGET_I_SHORELINE_NAME, TARGET_I_SHORELINE_SHA256)

    result["generator_candidates"] = [str(p) for p in generators]
    result["hydrology_candidates"] = [str(p) for p in hydrologies]
    result["margin_runner_candidates"] = [str(p) for p in runners]
    result["i_shoreline_candidates"] = [str(p) for p in shorelines]

    runner_contract = margin_runner_contract(runners[0]) if runners else {"exact_margin_to_seasonal_lineage_proved": False}
    hydro_contract = hydrology_seasonal_contract(hydrologies[0]) if hydrologies else {"found": False, "seasonal_attributes": []}
    result["margin_runner_contract"] = runner_contract
    result["hydrology_seasonal_contract"] = hydro_contract

    status: str
    decision: str

    if not d2c1.get("gate_satisfied"):
        status = "BLOCKED_R517_B6_D2D3_D2C1_ADAPTER_GATE_NOT_SATISFIED"
        decision = "DO_NOT_RECONSTRUCT_I"
    elif not margin_fixture.get("gate_satisfied"):
        status = "BLOCKED_R517_B6_D2D3_MARGIN_FIXTURE_NOT_ADJUDICATED"
        decision = "RECOVER_EXPLICIT_MARGIN_REPLAY_FIXTURE"
    elif not generators:
        status = "BLOCKED_R517_B6_D2D3_EXACT_GENERATOR_NOT_RECOVERED"
        decision = "RECOVER_EXACT_GENERATOR"
    elif not runners or not runner_contract.get("exact_margin_to_seasonal_lineage_proved"):
        status = "BLOCKED_R517_B6_D2D3_EXPLICIT_MARGIN_RUNNER_LINEAGE_NOT_PROVED"
        decision = "RECOVER_MARGIN_RUNNER_LINEAGE"
    elif not hydrologies or not hydro_contract.get("found"):
        status = "BLOCKED_R517_B6_D2D3_EXACT_HYDROLOGY_CONSUMER_NOT_RECOVERED"
        decision = "RECOVER_EXACT_HYDROLOGY_CONSUMER"
    elif not shorelines:
        status = "BLOCKED_R517_B6_D2D3_AUTHENTICATED_I_SHORELINE_NOT_RECOVERED"
        decision = "RECOVER_AUTHENTICATED_I_SHORELINE"
    else:
        generator = generators[0]
        project_root = d2d.generator_source_root(generator).parent
        margin_state_path = Path(margin_fixture["margin_state_path"])
        margin_baseline_path = Path(margin_fixture["baseline_path"])
        result["selected_generator"] = str(generator)
        result["selected_project_root"] = str(project_root)

        try:
            fn = d2d.import_exact_generator(generator)
            margin_state, margin_land_key = d2d.load_coast_candidate(margin_state_path)
            margin_replay_state = d2d.invoke_generator(fn, project_root, margin_state)
            result["margin_land_mask_source_key"] = margin_land_key

            with tempfile.TemporaryDirectory(prefix="arcana_r517_b6_d2d3_") as td:
                serialized_margin = Path(td) / "seasonal_climate_state.npz"
                native_save = serialize_state_native(margin_replay_state, serialized_margin)
                serialized_cmp = compare_npz(serialized_margin, margin_baseline_path)
                result["margin_native_serialization"] = native_save
                result["margin_serialized_replay_comparison"] = serialized_cmp

                consumed = set(hydro_contract.get("seasonal_attributes", []))
                baseline_keys = set(serialized_cmp.get("b_keys", []))
                serialized_keys = set(serialized_cmp.get("a_keys", []))
                consumed_present_in_serialized = sorted(consumed & serialized_keys)
                consumed_missing_from_serialized = sorted(consumed - serialized_keys)
                consumed_missing_from_baseline = sorted(consumed - baseline_keys)
                consumed_field_exactness: dict[str, Any] = {}
                all_consumed_exact = True
                for key in sorted(consumed):
                    rec = (serialized_cmp.get("fields") or {}).get(key)
                    exact = bool(rec and rec.get("exact_array_equal"))
                    consumed_field_exactness[key] = {
                        "present_in_serialized": key in serialized_keys,
                        "present_in_baseline": key in baseline_keys,
                        "exact_array_equal": exact,
                        "max_abs_difference": rec.get("max_abs_difference") if rec else None,
                    }
                    if not exact:
                        all_consumed_exact = False

                result["hydrology_consumed_field_validation"] = {
                    "consumed_fields": sorted(consumed),
                    "present_in_serialized": consumed_present_in_serialized,
                    "missing_from_serialized": consumed_missing_from_serialized,
                    "missing_from_baseline": consumed_missing_from_baseline,
                    "fields": consumed_field_exactness,
                    "all_consumed_fields_exact": all_consumed_exact,
                }

                full_serialized_exact = bool(serialized_cmp.get("schema_key_set_exact") and serialized_cmp.get("all_arrays_exact"))
                result["serialized_margin_replay_exact"] = full_serialized_exact

                if not full_serialized_exact:
                    status = "BLOCKED_R517_B6_D2D3_SERIALIZED_MARGIN_REPLAY_NONEXACT"
                    decision = "INSPECT_NATIVE_SERIALIZED_DIFFERENCES_WITHOUT_TOLERANCE_PROMOTION"
                elif consumed and not all_consumed_exact:
                    status = "BLOCKED_R517_B6_D2D3_HYDROLOGY_CONSUMED_FIELDS_NOT_EXACT"
                    decision = "DO_NOT_RECONSTRUCT_I_UNTIL_DOWNSTREAM_INPUT_REPLAY_EXACT"
                else:
                    i_shoreline = shorelines[0]
                    with np.load(i_shoreline, allow_pickle=False) as z:
                        elevation = np.asarray(z["elevation_m"]).copy()
                        land = np.asarray(z["effective_land_mask"]).astype(bool, copy=True)
                    if elevation.shape != land.shape:
                        raise RuntimeError(f"I shoreline shape mismatch elevation={elevation.shape} land={land.shape}")

                    from types import SimpleNamespace

                    i_coast = SimpleNamespace(elevation_m=elevation, land_mask=land)
                    i_state = d2d.invoke_generator(fn, project_root, i_coast)
                    reconstructed = serialize_state_native(i_state, args.reconstructed_output.resolve())

                    with np.load(args.reconstructed_output.resolve(), allow_pickle=False) as zi:
                        i_keys = set(zi.files)
                        reconstructed["hydrology_consumed_fields"] = sorted(consumed)
                        reconstructed["hydrology_consumed_fields_present"] = sorted(consumed & i_keys)
                        reconstructed["hydrology_consumed_fields_missing"] = sorted(consumed - i_keys)
                        reconstructed["all_hydrology_consumed_fields_present"] = not bool(consumed - i_keys)
                        reconstructed["all_finite_hydrology_consumed_numeric_fields"] = all(
                            np.isfinite(np.asarray(zi[k])).all()
                            for k in consumed
                            if k in zi.files and np.asarray(zi[k]).dtype.kind in "biufc"
                        )

                    if not reconstructed["all_hydrology_consumed_fields_present"]:
                        try:
                            args.reconstructed_output.resolve().unlink()
                        except OSError:
                            pass
                        status = "BLOCKED_R517_B6_D2D3_I_RECONSTRUCTION_MISSING_HYDROLOGY_FIELDS"
                        decision = "DO_NOT_BIND_RECONSTRUCTED_I_TO_D3"
                        result["i_reconstruction_materialized"] = False
                    else:
                        result["i_reconstruction_materialized"] = True
                        result["reconstructed_baseline"] = reconstructed
                        status = "PASS_R517_B6_D2D3_SERIALIZED_MARGIN_REPLAY_EXACT_AND_I_BASELINE_RECONSTRUCTED"
                        decision = "AUTHORIZE_RECONSTRUCTED_I_SEASONAL_BASELINE_FOR_D3_REPLAY_BINDING"

        except Exception as exc:
            result["execution_error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(limit=16),
            }
            status = "BLOCKED_R517_B6_D2D3_EXECUTION_ERROR"
            decision = "RESOLVE_RUNTIME_OR_NATIVE_SERIALIZATION_ERROR"

    result.setdefault("serialized_margin_replay_exact", False)
    result.setdefault("i_reconstruction_materialized", False)
    result.setdefault("reconstructed_baseline", None)
    result["status"] = status
    result["decision"] = decision
    result["historical_payload_identity_claimed"] = False
    result["next_if_pass"] = "R5.17-B6-D3_CANONICAL_PALEOHYDROLOGY_REPLAY_IMPLEMENTATION"

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "status": status,
        "decision": decision,
        "d2c1_gate_satisfied": d2c1.get("gate_satisfied", False),
        "margin_fixture_gate_satisfied": margin_fixture.get("gate_satisfied", False),
        "exact_margin_runner_lineage_proved": runner_contract.get("exact_margin_to_seasonal_lineage_proved", False),
        "hydrology_contract_found": hydro_contract.get("found", False),
        "hydrology_consumed_fields": hydro_contract.get("seasonal_attributes", []),
        "serialized_margin_replay_exact": result.get("serialized_margin_replay_exact", False),
        "all_hydrology_consumed_fields_exact": (result.get("hydrology_consumed_field_validation") or {}).get("all_consumed_fields_exact"),
        "i_reconstruction_materialized": result.get("i_reconstruction_materialized", False),
        "reconstructed_baseline_sha256": (result.get("reconstructed_baseline") or {}).get("sha256"),
        "output": str(args.output.resolve()),
    }
    print(json.dumps(summary, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
