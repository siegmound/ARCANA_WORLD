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

TARGET_GENERATOR_SUFFIX = d2d3.TARGET_GENERATOR_SUFFIX
TARGET_GENERATOR_SHA256 = d2d3.TARGET_GENERATOR_SHA256
TARGET_HYDROLOGY_SUFFIX = d2d3.TARGET_HYDROLOGY_SUFFIX
TARGET_HYDROLOGY_SHA256 = d2d3.TARGET_HYDROLOGY_SHA256
TARGET_MARGIN_SUFFIX = "src/arcana_worldsim/morphogenesis/margins.py"
TARGET_MARGIN_SHA256 = "f8998f2213938eb80a2b414300c2acc6dc298bc5327a6fb081951fde136d7d52"
TARGET_MARGIN_RUNNER_NAME = d2d3.TARGET_MARGIN_RUNNER_NAME
TARGET_MARGIN_RUNNER_SHA256 = d2d3.TARGET_MARGIN_RUNNER_SHA256
TARGET_MARGIN_SEASONAL_SHA256 = d2d3.TARGET_MARGIN_BASELINE_SHA256
TARGET_I_SHORELINE_NAME = d2d3.TARGET_I_SHORELINE_NAME
TARGET_I_SHORELINE_SHA256 = d2d3.TARGET_I_SHORELINE_SHA256
TARGET_SEED = 917231


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


def serialize_native(state: Any, path: Path) -> dict[str, Any]:
    save = getattr(state, "save_npz", None)
    if not callable(save):
        raise RuntimeError(f"state {type(state)!r} has no save_npz")
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


def stage_summary(cmp: dict[str, Any]) -> dict[str, Any]:
    nonexact = []
    max_abs = 0.0
    for key, rec in (cmp.get("fields") or {}).items():
        if not rec.get("exact_array_equal", False):
            nonexact.append(key)
        v = rec.get("max_abs_difference")
        if isinstance(v, (int, float)):
            max_abs = max(max_abs, float(v))
    return {
        "schema_exact": bool(cmp.get("schema_key_set_exact")),
        "arrays_exact": bool(cmp.get("all_arrays_exact")),
        "nonexact_fields": sorted(nonexact),
        "max_abs_difference": max_abs,
        "missing_from_replay": cmp.get("missing_from_a", []),
        "missing_from_historical": cmp.get("missing_from_b", []),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=(
        "R5.17-B6-D2D5: replay the explicit historical v0.5.5F margin -> seasonal -> hydrology chain "
        "fully in memory, matching the recovered runner semantics and avoiding the artificial "
        "serialize/reload quantization introduced by D2D3/D2D4. Reconstruct I only if the historical "
        "seasonal generator is validated by the full native chain without tolerance promotion."
    ))
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--d2c1-json", type=Path, required=True)
    ap.add_argument("--d2d3-json", type=Path, required=True)
    ap.add_argument("--d2d4-json", type=Path, required=True)
    ap.add_argument("--reconstructed-output", type=Path,
                    default=Path("R5_17_B6_D2D_RECONSTRUCTED/seasonal_climate_state_I_RECONSTRUCTED.npz"))
    ap.add_argument("--output", type=Path,
                    default=Path("R5_17_B6_D2D5_FULL_IN_MEMORY_F_CHAIN_REPLAY_AND_I_RECONSTRUCTION.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    d2c1 = d2d3.load_d2c1_gate(args.d2c1_json.resolve())
    d2d3_report = json.loads(args.d2d3_json.read_text(encoding="utf-8"))
    d2d4_report = json.loads(args.d2d4_json.read_text(encoding="utf-8"))

    generators = d2d.locate_exact_suffix(root, TARGET_GENERATOR_SUFFIX, TARGET_GENERATOR_SHA256)
    hydrologies = d2d.locate_exact_suffix(root, TARGET_HYDROLOGY_SUFFIX, TARGET_HYDROLOGY_SHA256)
    margins = d2d.locate_exact_suffix(root, TARGET_MARGIN_SUFFIX, TARGET_MARGIN_SHA256)
    runners = d2d.locate_named_hash(root, TARGET_MARGIN_RUNNER_NAME, TARGET_MARGIN_RUNNER_SHA256)
    shorelines = d2d.locate_named_hash(root, TARGET_I_SHORELINE_NAME, TARGET_I_SHORELINE_SHA256)
    seasonal_targets = d2d.locate_hash(root, TARGET_MARGIN_SEASONAL_SHA256)

    result: dict[str, Any] = {
        "schema": "ARCANA_R5_17_B6_D2D5_FULL_IN_MEMORY_F_CHAIN_REPLAY_AND_I_RECONSTRUCTION_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2D5",
        "purpose": (
            "Replay the recovered v0.5.5F runner semantics exactly at the stage boundary: "
            "build_margin_morphogenesis(root, 917231) -> build_seasonal_climate(root, margin) -> "
            "build_channel_hydrology(root, margin, seasonal), keeping margin and seasonal in memory "
            "until their downstream consumers run."
        ),
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
        },
        "target_seed": TARGET_SEED,
        "historical_provenance_gap_preserved": True,
        "historical_payload_identity_claimed": False,
        "absolute_or_relative_tolerance_authorized": False,
        "ulp_tolerance_authorized": False,
        "external_provider_authorized": False,
        "freshwater_support_materialized": False,
        "canonical_mutation": False,
        "d2c1_gate": d2c1,
        "d2d3_parent_status": d2d3_report.get("status"),
        "d2d4_parent_status": d2d4_report.get("status"),
        "source_candidates": {
            "seasonal": [str(p) for p in generators],
            "hydrology": [str(p) for p in hydrologies],
            "margin": [str(p) for p in margins],
            "runner": [str(p) for p in runners],
            "i_shoreline": [str(p) for p in shorelines],
            "margin_seasonal_target": [str(p) for p in seasonal_targets],
        },
        "chain_execution": None,
        "i_reconstruction_materialized": False,
        "reconstructed_baseline": None,
    }

    prerequisites = bool(
        d2c1.get("gate_satisfied")
        and generators and hydrologies and margins and runners and shorelines and seasonal_targets
        and d2d3_report.get("margin_runner_contract", {}).get("exact_margin_to_seasonal_lineage_proved")
    )
    result["prerequisites_satisfied"] = prerequisites

    if not prerequisites:
        status = "BLOCKED_R517_B6_D2D5_PREREQUISITES_NOT_SATISFIED"
        decision = "RECOVER_EXACT_FULL_F_CHAIN_BINDING"
    else:
        generator = generators[0]
        src_root = d2d.generator_source_root(generator)
        project_root = src_root.parent
        hydrology = hydrologies[0]
        margin_src = margins[0]
        seasonal_target = seasonal_targets[0]
        historical_dir = seasonal_target.parent
        historical_margin = historical_dir / "margin_state.npz"
        historical_hydro = historical_dir / "channel_hydrology_state.npz"

        result["selected_binding"] = {
            "project_root": str(project_root),
            "src_root": str(src_root),
            "seasonal_source": str(generator),
            "seasonal_sha256": sha256_file(generator),
            "hydrology_source": str(hydrology),
            "hydrology_sha256": sha256_file(hydrology),
            "margin_source": str(margin_src),
            "margin_sha256": sha256_file(margin_src),
            "runner": str(runners[0]),
            "runner_sha256": sha256_file(runners[0]),
            "historical_margin": str(historical_margin),
            "historical_seasonal": str(seasonal_target),
            "historical_hydrology": str(historical_hydro),
        }

        if not historical_margin.is_file() or not historical_hydro.is_file():
            status = "BLOCKED_R517_B6_D2D5_HISTORICAL_CHAIN_OUTPUT_MISSING"
            decision = "RECOVER_MARGIN_OR_HYDROLOGY_OUTPUT"
        else:
            try:
                # Clear package cache once, then bind every callable from the same exact recovered src tree.
                for name in list(sys.modules):
                    if name == "arcana_worldsim" or name.startswith("arcana_worldsim."):
                        del sys.modules[name]
                margin_fn = import_exact_callable(
                    src_root, "arcana_worldsim.morphogenesis.margins", "build_margin_morphogenesis", margin_src
                )
                seasonal_fn = import_exact_callable(
                    src_root, "arcana_worldsim.finalization.seasonal", "build_seasonal_climate", generator
                )
                hydro_fn = import_exact_callable(
                    src_root, "arcana_worldsim.finalization.hydrology", "build_channel_hydrology", hydrology
                )

                with tempfile.TemporaryDirectory(prefix="arcana_r517_b6_d2d5_") as td:
                    td = Path(td)
                    replay_margin_path = td / "margin_state.npz"
                    replay_seasonal_path = td / "seasonal_climate_state.npz"
                    replay_hydro_path = td / "channel_hydrology_state.npz"

                    margin_state = margin_fn(project_root, TARGET_SEED)
                    margin_serialized = serialize_native(margin_state, replay_margin_path)

                    seasonal_state = seasonal_fn(project_root, margin_state)
                    seasonal_serialized = serialize_native(seasonal_state, replay_seasonal_path)

                    hydro_state = hydro_fn(project_root, margin_state, seasonal_state)
                    hydro_serialized = serialize_native(hydro_state, replay_hydro_path)

                    margin_cmp = d2d3.compare_npz(replay_margin_path, historical_margin)
                    seasonal_cmp = d2d3.compare_npz(replay_seasonal_path, seasonal_target)
                    hydro_cmp = d2d3.compare_npz(replay_hydro_path, historical_hydro)

                    result["chain_execution"] = {
                        "runner_semantics": [
                            "margin = build_margin_morphogenesis(root, 917231)",
                            "seasonal = build_seasonal_climate(root, margin)",
                            "hydro = build_channel_hydrology(root, margin, seasonal)",
                        ],
                        "no_intermediate_reload": True,
                        "margin_serialized": margin_serialized,
                        "seasonal_serialized": seasonal_serialized,
                        "hydrology_serialized": hydro_serialized,
                        "margin_comparison": margin_cmp,
                        "seasonal_comparison": seasonal_cmp,
                        "hydrology_comparison": hydro_cmp,
                        "margin_summary": stage_summary(margin_cmp),
                        "seasonal_summary": stage_summary(seasonal_cmp),
                        "hydrology_summary": stage_summary(hydro_cmp),
                    }

                    margin_exact = bool(margin_cmp.get("all_arrays_exact"))
                    seasonal_exact = bool(seasonal_cmp.get("all_arrays_exact"))
                    hydro_exact = bool(hydro_cmp.get("all_arrays_exact"))
                    result["full_chain_exact"] = bool(margin_exact and seasonal_exact and hydro_exact)
                    result["seasonal_and_hydrology_exact"] = bool(seasonal_exact and hydro_exact)

                    if not margin_exact:
                        status = "BLOCKED_R517_B6_D2D5_MARGIN_IN_MEMORY_REPLAY_NONEXACT"
                        decision = "RECOVER_HISTORICAL_NUMERIC_RUNTIME_OR_MARGIN_GENERATOR_LINEAGE"
                    elif not seasonal_exact:
                        status = "BLOCKED_R517_B6_D2D5_SEASONAL_IN_MEMORY_REPLAY_NONEXACT"
                        decision = "RECOVER_HISTORICAL_NUMERIC_RUNTIME_OR_SEASONAL_LINEAGE"
                    elif not hydro_exact:
                        status = "BLOCKED_R517_B6_D2D5_HYDROLOGY_IN_MEMORY_REPLAY_NONEXACT"
                        decision = "RECOVER_HISTORICAL_NUMERIC_RUNTIME_OR_HYDROLOGY_LINEAGE"
                    else:
                        i_shoreline = shorelines[0]
                        with np.load(i_shoreline, allow_pickle=False) as z:
                            elevation = np.asarray(z["elevation_m"]).copy()
                            land = np.asarray(z["effective_land_mask"]).astype(bool, copy=True)
                        if elevation.shape != land.shape:
                            raise RuntimeError(
                                f"I shoreline shape mismatch elevation={elevation.shape} land={land.shape}"
                            )
                        i_state = seasonal_fn(
                            project_root,
                            SimpleNamespace(elevation_m=elevation, land_mask=land),
                        )
                        out = args.reconstructed_output.resolve()
                        reconstructed = serialize_native(i_state, out)
                        with np.load(out, allow_pickle=False) as z:
                            reconstructed["hydrology_fields_present"] = all(
                                k in z.files for k in (
                                    "monthly_pet_mm", "monthly_precipitation_mm", "monthly_temperature_c"
                                )
                            )
                        result["i_reconstruction_materialized"] = True
                        result["reconstructed_baseline"] = reconstructed
                        status = "PASS_R517_B6_D2D5_FULL_IN_MEMORY_F_CHAIN_EXACT_AND_I_BASELINE_RECONSTRUCTED"
                        decision = "AUTHORIZE_RECONSTRUCTED_I_SEASONAL_BASELINE_FOR_D3_REPLAY_BINDING"
            except Exception as exc:
                result["execution_error"] = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(limit=20),
                }
                status = "BLOCKED_R517_B6_D2D5_FULL_CHAIN_EXECUTION_ERROR"
                decision = "RESOLVE_EXACT_FULL_CHAIN_RUNTIME_BINDING"

    result["status"] = status
    result["decision"] = decision
    result["next_if_pass"] = "R5.17-B6-D3_CANONICAL_PALEOHYDROLOGY_REPLAY_IMPLEMENTATION"
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    chain = result.get("chain_execution") or {}
    summary = {
        "status": status,
        "decision": decision,
        "prerequisites_satisfied": result.get("prerequisites_satisfied", False),
        "margin_replay_exact": (chain.get("margin_summary") or {}).get("arrays_exact"),
        "seasonal_replay_exact": (chain.get("seasonal_summary") or {}).get("arrays_exact"),
        "hydrology_replay_exact": (chain.get("hydrology_summary") or {}).get("arrays_exact"),
        "full_chain_exact": result.get("full_chain_exact", False),
        "i_reconstruction_materialized": result.get("i_reconstruction_materialized", False),
        "reconstructed_baseline_sha256": (result.get("reconstructed_baseline") or {}).get("sha256"),
        "output": str(args.output.resolve()),
    }
    print(json.dumps(summary, indent=2))
    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
