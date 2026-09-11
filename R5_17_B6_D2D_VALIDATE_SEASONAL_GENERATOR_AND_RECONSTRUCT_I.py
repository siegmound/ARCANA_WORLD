from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

TARGET_GENERATOR_SUFFIX = "src/arcana_worldsim/finalization/seasonal.py"
TARGET_GENERATOR_SHA256 = "3ec12145617ae63e6ce9d9bd123c159525f83925f9257f1138f3490bb3e70de2"
TARGET_I_SHORELINE_NAME = "shoreline_state_I.npz"
TARGET_I_SHORELINE_SHA256 = "f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85"

KNOWN_F_BASELINES = {
    "physical_finalization": "347f07b9ff16f5c097319898c0b33b86851fc66775b9243ce0f98dce279b954f",
    "margin_morphogenesis": "1b32d97a0b4dad12f01f4c286461d6ca597c2d46a390a8801771735d972d93f6",
}

REQUIRED_FIELDS = (
    "monthly_temperature_c",
    "monthly_precipitation_mm",
    "monthly_pet_mm",
)

MAX_F_COAST_CANDIDATES_PER_BASELINE = 32


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(path: Path | str) -> str:
    return str(path).replace("\\", "/")


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
    return sorted(out, key=lambda p: norm(p).lower())


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
    return sorted(out, key=lambda p: norm(p).lower())


def load_coast_candidate(path: Path) -> tuple[SimpleNamespace, str]:
    with np.load(path, allow_pickle=False) as z:
        if "elevation_m" not in z.files:
            raise KeyError("elevation_m")
        if "land_mask" in z.files:
            land_key = "land_mask"
        elif "effective_land_mask" in z.files:
            land_key = "effective_land_mask"
        else:
            raise KeyError("land_mask/effective_land_mask")
        elevation = np.asarray(z["elevation_m"]).copy()
        land = np.asarray(z[land_key]).astype(bool, copy=True)
    if elevation.shape != land.shape:
        raise ValueError(f"shape mismatch elevation={elevation.shape} land={land.shape}")
    return SimpleNamespace(elevation_m=elevation, land_mask=land), land_key


def project_root_for_payload(path: Path) -> Path | None:
    resolved = path.resolve()
    for parent in resolved.parents:
        try:
            rel = resolved.relative_to(parent)
        except ValueError:
            continue
        if rel.parts and rel.parts[0] == "outputs":
            return parent
        if (parent / "outputs").is_dir() and "outputs" in rel.parts:
            return parent
    return None


def candidate_npz_paths(project_root: Path, baseline_path: Path) -> list[Path]:
    weighted: list[tuple[int, str, Path]] = []
    baseline_stage_dir = baseline_path.parent.resolve()
    for p in project_root.rglob("*.npz"):
        if not p.is_file() or p.resolve() == baseline_path.resolve() or ".git" in p.parts:
            continue
        low = norm(p).lower()
        if "v0_5_5i_sealed" in low or p.name.lower() == TARGET_I_SHORELINE_NAME.lower():
            continue
        tokens = ("shoreline", "coast", "margin", "physical_finalization")
        if not any(t in low for t in tokens):
            continue
        try:
            with np.load(p, allow_pickle=False) as z:
                keys = set(z.files)
                if "elevation_m" not in keys:
                    continue
                if not ({"land_mask", "effective_land_mask"} & keys):
                    continue
        except Exception:
            continue

        score = 100
        if p.parent.resolve() == baseline_stage_dir:
            score -= 60
        if "shoreline" in p.name.lower() or "coast" in p.name.lower():
            score -= 20
        if "physical_finalization" in low:
            score -= 10
        if "margin_morphogenesis" in low:
            score -= 8
        weighted.append((score, norm(p).lower(), p.resolve()))

    weighted.sort()
    return [p for _, _, p in weighted[:MAX_F_COAST_CANDIDATES_PER_BASELINE]]


def generator_source_root(generator: Path) -> Path:
    # .../src/arcana_worldsim/finalization/seasonal.py -> .../src
    if len(generator.parents) < 3:
        raise RuntimeError(f"unexpected generator path: {generator}")
    src = generator.parents[2]
    if src.name != "src":
        raise RuntimeError(f"cannot infer src root from generator path: {generator}")
    return src


def import_exact_generator(generator: Path):
    src = generator_source_root(generator)
    sys.path.insert(0, str(src))
    try:
        for name in list(sys.modules):
            if name == "arcana_worldsim" or name.startswith("arcana_worldsim."):
                del sys.modules[name]
        module = importlib.import_module("arcana_worldsim.finalization.seasonal")
        module_path = Path(inspect.getsourcefile(module) or "").resolve()
        if module_path != generator.resolve():
            raise RuntimeError(f"import resolved wrong module: {module_path} != {generator}")
        fn = getattr(module, "build_seasonal_climate")
        return fn
    except Exception:
        if sys.path and sys.path[0] == str(src):
            sys.path.pop(0)
        raise


def invoke_generator(fn, project_root: Path, coast_state: SimpleNamespace):
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    required = [
        p for p in params
        if p.default is inspect._empty
        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
    ]
    if len(required) > 2:
        raise RuntimeError(f"unsupported generator signature: {sig}")

    kwargs: dict[str, Any] = {}
    positional: list[Any] = []
    for p in params:
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        name = p.name.lower()
        if name in {"project_root", "root", "project"}:
            value = project_root
        elif name in {"coast_state", "coast", "margin", "shoreline", "state"}:
            value = coast_state
        elif p.default is not inspect._empty:
            continue
        else:
            raise RuntimeError(f"cannot bind required generator parameter {p.name!r} in {sig}")

        if p.kind == p.KEYWORD_ONLY:
            kwargs[p.name] = value
        else:
            positional.append(value)

    return fn(*positional, **kwargs)


def state_mapping(state: Any) -> dict[str, np.ndarray]:
    if isinstance(state, dict):
        raw = state
    elif hasattr(state, "_asdict"):
        raw = state._asdict()
    elif hasattr(state, "__dict__"):
        raw = vars(state)
    else:
        raw = {}
        for key in REQUIRED_FIELDS:
            if hasattr(state, key):
                raw[key] = getattr(state, key)

    out: dict[str, np.ndarray] = {}
    for key, value in raw.items():
        if str(key).startswith("_"):
            continue
        if isinstance(value, np.ndarray):
            out[str(key)] = np.asarray(value)
        elif np.isscalar(value) and not isinstance(value, (str, bytes)):
            out[str(key)] = np.asarray(value)
    return out


def compare_state_to_npz(state: Any, baseline_path: Path) -> dict[str, Any]:
    mapping = state_mapping(state)
    result: dict[str, Any] = {
        "baseline_path": str(baseline_path),
        "baseline_sha256": sha256_file(baseline_path),
        "state_keys": sorted(mapping),
        "fields": {},
    }
    all_schema_keys_present = True
    all_exact = True
    required_exact = True

    with np.load(baseline_path, allow_pickle=False) as z:
        baseline_keys = sorted(z.files)
        result["baseline_keys"] = baseline_keys
        result["schema_key_set_exact"] = set(baseline_keys) == set(mapping)
        for key in baseline_keys:
            if key not in mapping:
                result["fields"][key] = {"present_in_state": False}
                all_schema_keys_present = False
                all_exact = False
                if key in REQUIRED_FIELDS:
                    required_exact = False
                continue

            a = np.asarray(mapping[key])
            b = np.asarray(z[key])
            rec: dict[str, Any] = {
                "present_in_state": True,
                "state_shape": list(a.shape),
                "baseline_shape": list(b.shape),
                "state_dtype": str(a.dtype),
                "baseline_dtype": str(b.dtype),
            }
            if a.shape != b.shape:
                rec["exact_array_equal"] = False
                all_exact = False
                if key in REQUIRED_FIELDS:
                    required_exact = False
            else:
                exact = bool(np.array_equal(a, b, equal_nan=True))
                rec["exact_array_equal"] = exact
                if a.dtype.kind in "biufc" and b.dtype.kind in "biufc":
                    af = a.astype(np.float64, copy=False)
                    bf = b.astype(np.float64, copy=False)
                    valid = np.isfinite(af) & np.isfinite(bf)
                    if np.any(valid):
                        delta = np.abs(af[valid] - bf[valid])
                        rec["max_abs_difference"] = float(np.max(delta))
                        rec["mean_abs_difference"] = float(np.mean(delta))
                if not exact:
                    all_exact = False
                    if key in REQUIRED_FIELDS:
                        required_exact = False
            result["fields"][key] = rec

    for key in REQUIRED_FIELDS:
        if key not in result["fields"]:
            result["fields"][key] = {"present_in_baseline": False}
            required_exact = False
            all_exact = False

    result["all_baseline_schema_keys_present_in_state"] = all_schema_keys_present
    result["all_baseline_fields_exact"] = all_exact and all_schema_keys_present
    result["required_fields_exact"] = required_exact
    return result


def save_reconstructed_from_schema(state: Any, schema_source: Path, output: Path) -> dict[str, Any]:
    mapping = state_mapping(state)
    with np.load(schema_source, allow_pickle=False) as z:
        schema_keys = sorted(z.files)

    missing = [k for k in schema_keys if k not in mapping]
    if missing:
        raise RuntimeError(f"generator state missing schema keys required by validated F baseline: {missing}")

    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, **{k: np.asarray(mapping[k]) for k in schema_keys})
    return {
        "path": str(output.resolve()),
        "sha256": sha256_file(output),
        "size_bytes": output.stat().st_size,
        "schema_keys": schema_keys,
        "required_fields_present": all(k in schema_keys for k in REQUIRED_FIELDS),
    }


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
        "adapter_authorized": data.get("adapter_authorized"),
        "mapping": data.get("adapter_mapping"),
        "gate_satisfied": ok,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "R5.17-B6-D2D: validate the exact recovered canonical seasonal generator against "
            "a surviving F-era seasonal baseline using an automatically discovered F-era coast "
            "fixture; only after exact replay, reconstruct the lost I-era seasonal baseline from "
            "the authenticated shoreline_state_I through the D2C1-authorized interface adapter."
        )
    )
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument(
        "--d2c1-json",
        type=Path,
        default=Path("R5_17_B6_D2C1_SHORELINE_LAND_MASK_ADAPTER_ADJUDICATION.json"),
    )
    ap.add_argument(
        "--reconstructed-output",
        type=Path,
        default=Path("R5_17_B6_D2D_RECONSTRUCTED/seasonal_climate_state_I_RECONSTRUCTED.npz"),
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("R5_17_B6_D2D_SEASONAL_GENERATOR_REPLAY_AND_I_RECONSTRUCTION.json"),
    )
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    d2c1 = load_d2c1_gate(args.d2c1_json.resolve()) if args.d2c1_json.is_file() else {
        "path": str(args.d2c1_json.resolve()),
        "gate_satisfied": False,
        "error": "D2C1 adjudication JSON missing",
    }

    generators = locate_exact_suffix(root, TARGET_GENERATOR_SUFFIX, TARGET_GENERATOR_SHA256)
    shorelines = locate_named_hash(root, TARGET_I_SHORELINE_NAME, TARGET_I_SHORELINE_SHA256)
    baseline_paths = {
        name: locate_hash(root, h)
        for name, h in KNOWN_F_BASELINES.items()
    }

    result: dict[str, Any] = {
        "schema": "ARCANA_R5_17_B6_D2D_SEASONAL_GENERATOR_REPLAY_AND_I_RECONSTRUCTION_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2D",
        "purpose": (
            "Validate the recovered canonical seasonal generator against a surviving F-era "
            "baseline before reconstructing the historically lost I-era seasonal baseline. "
            "The reconstructed payload is a new governed artifact and is never claimed to be "
            "the original lost seasonal_climate_state_I.npz."
        ),
        "search_root": str(root),
        "historical_provenance_gap_preserved": True,
        "target_generator_sha256": TARGET_GENERATOR_SHA256,
        "generator_candidates": [str(p) for p in generators],
        "exact_generator_recovered": bool(generators),
        "target_i_shoreline_sha256": TARGET_I_SHORELINE_SHA256,
        "i_shoreline_candidates": [str(p) for p in shorelines],
        "exact_i_shoreline_recovered": bool(shorelines),
        "d2c1_gate": d2c1,
        "known_f_baseline_hashes": KNOWN_F_BASELINES,
        "known_f_baseline_locations": {
            k: [str(p) for p in v] for k, v in baseline_paths.items()
        },
        "validation_attempts": [],
        "f_fixture_exact_replay_validated": False,
        "validated_f_fixture": None,
        "i_reconstruction_materialized": False,
        "reconstructed_baseline": None,
        "external_provider_authorized": False,
        "freshwater_support_materialized": False,
        "canonical_mutation": False,
    }

    if not d2c1.get("gate_satisfied"):
        status = "BLOCKED_R517_B6_D2D_D2C1_ADAPTER_GATE_NOT_SATISFIED"
        decision = "DO_NOT_EXECUTE_SEASONAL_RECONSTRUCTION"
    elif not generators:
        status = "BLOCKED_R517_B6_D2D_EXACT_SEASONAL_GENERATOR_NOT_RECOVERED"
        decision = "RECOVER_EXACT_GENERATOR"
    elif not shorelines:
        status = "BLOCKED_R517_B6_D2D_AUTHENTICATED_I_SHORELINE_NOT_RECOVERED"
        decision = "RECOVER_AUTHENTICATED_I_SHORELINE"
    elif not any(baseline_paths.values()):
        status = "BLOCKED_R517_B6_D2D_NO_SURVIVING_F_BASELINE_FIXTURE"
        decision = "RECOVER_F_VALIDATION_FIXTURE"
    else:
        generator = generators[0]
        generator_project_root = generator_source_root(generator).parent
        result["selected_generator"] = str(generator)
        result["selected_generator_project_root"] = str(generator_project_root)

        try:
            fn = import_exact_generator(generator)
            result["generator_signature"] = str(inspect.signature(fn))
        except Exception as exc:
            result["generator_import_error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(limit=12),
            }
            fn = None

        validated: dict[str, Any] | None = None

        if fn is not None:
            for baseline_kind in ("physical_finalization", "margin_morphogenesis"):
                for baseline in baseline_paths.get(baseline_kind, []):
                    project_root = project_root_for_payload(baseline)
                    if project_root is None:
                        result["validation_attempts"].append({
                            "baseline_kind": baseline_kind,
                            "baseline_path": str(baseline),
                            "baseline_sha256": sha256_file(baseline),
                            "status": "SKIP_PROJECT_ROOT_NOT_INFERRED",
                        })
                        continue

                    coast_candidates = candidate_npz_paths(project_root, baseline)
                    if not coast_candidates:
                        result["validation_attempts"].append({
                            "baseline_kind": baseline_kind,
                            "baseline_path": str(baseline),
                            "baseline_sha256": sha256_file(baseline),
                            "project_root": str(project_root),
                            "status": "NO_F_COAST_CANDIDATES",
                        })
                        continue

                    for coast_path in coast_candidates:
                        attempt: dict[str, Any] = {
                            "baseline_kind": baseline_kind,
                            "baseline_path": str(baseline),
                            "baseline_sha256": sha256_file(baseline),
                            "project_root": str(project_root),
                            "coast_candidate_path": str(coast_path),
                            "coast_candidate_sha256": sha256_file(coast_path),
                        }
                        try:
                            coast, land_key = load_coast_candidate(coast_path)
                            attempt["land_mask_source_key"] = land_key
                            state = invoke_generator(fn, generator_project_root, coast)
                            cmp = compare_state_to_npz(state, baseline)
                            attempt["comparison"] = cmp
                            attempt["status"] = (
                                "EXACT_REPLAY"
                                if cmp.get("all_baseline_fields_exact")
                                else "NON_EXACT_REPLAY"
                            )
                            result["validation_attempts"].append(attempt)
                            if cmp.get("all_baseline_fields_exact"):
                                validated = {
                                    "baseline_kind": baseline_kind,
                                    "baseline_path": str(baseline),
                                    "baseline_sha256": sha256_file(baseline),
                                    "coast_input_path": str(coast_path),
                                    "coast_input_sha256": sha256_file(coast_path),
                                    "land_mask_source_key": land_key,
                                    "comparison": cmp,
                                }
                                break
                        except Exception as exc:
                            attempt["status"] = "EXECUTION_ERROR"
                            attempt["error"] = {
                                "type": type(exc).__name__,
                                "message": str(exc),
                                "traceback": traceback.format_exc(limit=8),
                            }
                            result["validation_attempts"].append(attempt)
                    if validated:
                        break
                if validated:
                    break

        result["f_fixture_exact_replay_validated"] = bool(validated)
        result["validated_f_fixture"] = validated

        if not validated:
            if fn is None:
                status = "BLOCKED_R517_B6_D2D_CANONICAL_GENERATOR_IMPORT_FAILED"
                decision = "RESOLVE_EXACT_GENERATOR_RUNTIME_BINDING"
            else:
                status = "BLOCKED_R517_B6_D2D_NO_EXACT_F_REPLAY_FIXTURE_VALIDATED"
                decision = "ADJUDICATE_F_FIXTURE_BINDING_BEFORE_I_RECONSTRUCTION"
        else:
            try:
                i_shoreline = shorelines[0]
                with np.load(i_shoreline, allow_pickle=False) as z:
                    elevation = np.asarray(z["elevation_m"]).copy()
                    land = np.asarray(z["effective_land_mask"]).astype(bool, copy=True)
                if elevation.shape != land.shape:
                    raise RuntimeError(
                        f"I shoreline shape mismatch elevation={elevation.shape} land={land.shape}"
                    )

                i_coast = SimpleNamespace(elevation_m=elevation, land_mask=land)
                i_state = invoke_generator(fn, generator_project_root, i_coast)
                reconstructed = save_reconstructed_from_schema(
                    i_state,
                    Path(validated["baseline_path"]),
                    args.reconstructed_output.resolve(),
                )

                with np.load(args.reconstructed_output.resolve(), allow_pickle=False) as z:
                    reconstructed["array_shapes"] = {
                        k: list(np.asarray(z[k]).shape) for k in z.files
                    }
                    reconstructed["array_dtypes"] = {
                        k: str(np.asarray(z[k]).dtype) for k in z.files
                    }
                    reconstructed["all_finite_required_fields"] = all(
                        np.isfinite(np.asarray(z[k])).all()
                        for k in REQUIRED_FIELDS
                        if k in z.files
                    )

                result["i_reconstruction_materialized"] = True
                result["reconstructed_baseline"] = reconstructed
                status = "PASS_R517_B6_D2D_CANONICAL_SEASONAL_GENERATOR_VALIDATED_AND_I_BASELINE_RECONSTRUCTED"
                decision = "AUTHORIZE_RECONSTRUCTED_I_SEASONAL_BASELINE_FOR_D3_REPLAY_BINDING"
            except Exception as exc:
                result["i_reconstruction_error"] = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(limit=12),
                }
                status = "BLOCKED_R517_B6_D2D_F_REPLAY_VALIDATED_BUT_I_RECONSTRUCTION_FAILED"
                decision = "RESOLVE_I_RECONSTRUCTION_RUNTIME_ERROR"

    result["decision"] = decision
    result["status"] = status
    result["next_if_pass"] = "R5.17-B6-D3_CANONICAL_PALEOHYDROLOGY_REPLAY_IMPLEMENTATION"
    result["historical_source_executed"] = bool(result["validation_attempts"])
    result["historical_payload_identity_claimed"] = False

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "status": status,
        "decision": decision,
        "exact_generator_recovered": result["exact_generator_recovered"],
        "exact_i_shoreline_recovered": result["exact_i_shoreline_recovered"],
        "d2c1_gate_satisfied": result["d2c1_gate"].get("gate_satisfied", False),
        "surviving_f_baseline_count": sum(len(v) for v in baseline_paths.values()),
        "validation_attempt_count": len(result["validation_attempts"]),
        "f_fixture_exact_replay_validated": result["f_fixture_exact_replay_validated"],
        "validated_f_baseline_sha256": (
            (result["validated_f_fixture"] or {}).get("baseline_sha256")
        ),
        "validated_f_coast_input_sha256": (
            (result["validated_f_fixture"] or {}).get("coast_input_sha256")
        ),
        "i_reconstruction_materialized": result["i_reconstruction_materialized"],
        "reconstructed_baseline_sha256": (
            (result["reconstructed_baseline"] or {}).get("sha256")
        ),
        "output": str(args.output.resolve()),
    }
    print(json.dumps(summary, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
