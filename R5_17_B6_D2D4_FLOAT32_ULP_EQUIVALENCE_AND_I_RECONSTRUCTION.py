from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

import R5_17_B6_D2D_VALIDATE_SEASONAL_GENERATOR_AND_RECONSTRUCT_I as d2d
import R5_17_B6_D2D3_VALIDATE_SERIALIZED_MARGIN_REPLAY_AND_RECONSTRUCT_I as d2d3

TARGET_GENERATOR_SUFFIX = d2d3.TARGET_GENERATOR_SUFFIX
TARGET_GENERATOR_SHA256 = d2d3.TARGET_GENERATOR_SHA256
TARGET_I_SHORELINE_NAME = d2d3.TARGET_I_SHORELINE_NAME
TARGET_I_SHORELINE_SHA256 = d2d3.TARGET_I_SHORELINE_SHA256
HYDROLOGY_FIELDS = (
    "monthly_pet_mm",
    "monthly_precipitation_mm",
    "monthly_temperature_c",
)
MAX_FLOAT32_ULP = 2


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ordered_float32_bits(a: np.ndarray) -> np.ndarray:
    x = np.ascontiguousarray(a, dtype=np.float32)
    u = x.view(np.uint32)
    sign = (u & np.uint32(0x80000000)) != 0
    return np.where(sign, np.bitwise_not(u), u | np.uint32(0x80000000)).astype(np.uint64)


def float32_ulp_report(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "a_shape": list(a.shape),
        "b_shape": list(b.shape),
        "a_dtype": str(a.dtype),
        "b_dtype": str(b.dtype),
        "shape_exact": a.shape == b.shape,
        "dtype_exact": a.dtype == b.dtype,
    }
    if a.shape != b.shape:
        rec.update({"eligible": False, "reason": "shape_mismatch"})
        return rec
    if a.dtype != np.dtype("float32") or b.dtype != np.dtype("float32"):
        rec.update({"eligible": False, "reason": "not_float32"})
        return rec

    a_nan = np.isnan(a)
    b_nan = np.isnan(b)
    a_posinf = np.isposinf(a)
    b_posinf = np.isposinf(b)
    a_neginf = np.isneginf(a)
    b_neginf = np.isneginf(b)
    special_masks_exact = bool(
        np.array_equal(a_nan, b_nan)
        and np.array_equal(a_posinf, b_posinf)
        and np.array_equal(a_neginf, b_neginf)
    )
    finite = np.isfinite(a) & np.isfinite(b)
    exact = bool(np.array_equal(a, b, equal_nan=True))
    rec["special_value_masks_exact"] = special_masks_exact
    rec["exact_array_equal"] = exact
    rec["element_count"] = int(a.size)

    if not special_masks_exact:
        rec.update({"eligible": False, "reason": "special_value_mask_mismatch"})
        return rec

    if np.any(finite):
        af = a[finite]
        bf = b[finite]
        oa = ordered_float32_bits(af)
        ob = ordered_float32_bits(bf)
        ulp = np.where(oa >= ob, oa - ob, ob - oa)
        delta = np.abs(af.astype(np.float64) - bf.astype(np.float64))
        neq = af != bf
        nonzero_ulp = ulp[neq]
        rec["finite_count"] = int(af.size)
        rec["differing_finite_count"] = int(np.count_nonzero(neq))
        rec["differing_fraction"] = float(np.count_nonzero(neq) / af.size)
        rec["max_abs_difference"] = float(np.max(delta))
        rec["mean_abs_difference"] = float(np.mean(delta))
        denom = np.maximum(np.maximum(np.abs(af.astype(np.float64)), np.abs(bf.astype(np.float64))), 1e-30)
        rel = delta / denom
        rec["max_relative_difference"] = float(np.max(rel))
        rec["mean_relative_difference"] = float(np.mean(rel))
        rec["max_ulp_distance"] = int(np.max(ulp))
        if nonzero_ulp.size:
            rec["nonzero_ulp_percentiles"] = {
                "p50": float(np.percentile(nonzero_ulp, 50)),
                "p95": float(np.percentile(nonzero_ulp, 95)),
                "p99": float(np.percentile(nonzero_ulp, 99)),
                "p100": float(np.max(nonzero_ulp)),
            }
        else:
            rec["nonzero_ulp_percentiles"] = {"p50": 0.0, "p95": 0.0, "p99": 0.0, "p100": 0.0}
    else:
        rec.update({
            "finite_count": 0,
            "differing_finite_count": 0,
            "differing_fraction": 0.0,
            "max_abs_difference": 0.0,
            "mean_abs_difference": 0.0,
            "max_relative_difference": 0.0,
            "mean_relative_difference": 0.0,
            "max_ulp_distance": 0,
            "nonzero_ulp_percentiles": {"p50": 0.0, "p95": 0.0, "p99": 0.0, "p100": 0.0},
        })

    rec["eligible"] = True
    rec["within_2_ulp"] = bool(rec["max_ulp_distance"] <= MAX_FLOAT32_ULP)
    return rec


def scan_runtime_provenance(project_root: Path) -> list[dict[str, Any]]:
    names = {
        "pyproject.toml", "requirements.txt", "requirements-dev.txt", "requirements-dev.in",
        "environment.yml", "environment.yaml", "conda-lock.yml", "poetry.lock", "uv.lock",
        "Pipfile", "Pipfile.lock", "README.md", "recovery_provenance.json",
    }
    patterns = [
        re.compile(r"numpy\s*(?:==|~=|>=|<=|>|<)\s*([0-9][0-9A-Za-z_.+-]*)", re.I),
        re.compile(r'"numpy(?:_version)?"\s*:\s*"([^"]+)"', re.I),
        re.compile(r"numpy(?:_version)?\s*[=:]\s*([0-9][0-9A-Za-z_.+-]*)", re.I),
        re.compile(r"python(?:_version)?\s*[=:]\s*([0-9][0-9A-Za-z_.+-]*)", re.I),
    ]
    out: list[dict[str, Any]] = []
    seen = 0
    for p in project_root.rglob("*"):
        if seen >= 5000:
            break
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.name not in names and p.suffix.lower() not in {".md", ".json", ".txt", ".toml", ".yml", ".yaml", ".lock"}:
            continue
        try:
            if p.stat().st_size > 2_000_000:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        seen += 1
        hits: list[str] = []
        for pat in patterns:
            for m in pat.finditer(text):
                hits.append(m.group(0)[:300])
                if len(hits) >= 20:
                    break
            if len(hits) >= 20:
                break
        if hits:
            out.append({"path": str(p.resolve()), "sha256": sha256_file(p), "hits": hits})
        if len(out) >= 30:
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=(
        "R5.17-B6-D2D4: adjudicate the non-bitwise serialized margin replay in IEEE-754 float32 ULPs. "
        "Only if every hydrology-consumed seasonal field has identical schema/special-value masks and "
        "is within 2 ULP is the replay classified as cross-runtime numerically equivalent and the lost "
        "I-era seasonal baseline reconstructed through the already-authorized D2C1 adapter."
    ))
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--d2d2-json", type=Path, required=True)
    ap.add_argument("--d2d3-json", type=Path, required=True)
    ap.add_argument("--d2c1-json", type=Path, required=True)
    ap.add_argument("--reconstructed-output", type=Path,
                    default=Path("R5_17_B6_D2D_RECONSTRUCTED/seasonal_climate_state_I_RECONSTRUCTED.npz"))
    ap.add_argument("--output", type=Path,
                    default=Path("R5_17_B6_D2D4_FLOAT32_ULP_EQUIVALENCE_AND_I_RECONSTRUCTION.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    d2d3_report = json.loads(args.d2d3_json.read_text(encoding="utf-8"))
    d2c1 = d2d3.load_d2c1_gate(args.d2c1_json.resolve())
    margin_fixture = d2d3.load_d2d2_margin_fixture(args.d2d2_json.resolve())

    result: dict[str, Any] = {
        "schema": "ARCANA_R5_17_B6_D2D4_FLOAT32_ULP_EQUIVALENCE_AND_I_RECONSTRUCTION_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2D4",
        "purpose": "Resolve the remaining serialized F replay discrepancy using exact float32 ULP distance rather than arbitrary absolute/relative tolerances; reconstruct I only if the hydrology-consumed interface is within the strict cross-runtime equivalence bound.",
        "runtime": {"python_executable": sys.executable, "python_version": platform.python_version(), "numpy_version": np.__version__},
        "equivalence_rule": {
            "numeric_type": "IEEE-754 binary32 / numpy.float32",
            "required_shape_identity": True,
            "required_dtype_identity": True,
            "required_special_value_mask_identity": True,
            "max_ulp_distance": MAX_FLOAT32_ULP,
            "absolute_tolerance": None,
            "relative_tolerance": None,
            "scope": list(HYDROLOGY_FIELDS),
        },
        "absolute_or_relative_tolerance_authorized": False,
        "historical_provenance_gap_preserved": True,
        "historical_payload_identity_claimed": False,
        "external_provider_authorized": False,
        "freshwater_support_materialized": False,
        "canonical_mutation": False,
        "d2c1_gate": d2c1,
        "margin_fixture_gate": margin_fixture,
        "d2d3_parent_status": d2d3_report.get("status"),
        "d2d3_serialized_margin_replay_exact": d2d3_report.get("serialized_margin_replay_exact"),
        "hydrology_field_ulp_validation": {"fields": {}, "all_fields_within_bound": False},
        "runtime_ulp_equivalence_authorized": False,
        "i_reconstruction_materialized": False,
        "reconstructed_baseline": None,
    }

    prerequisites = bool(
        d2c1.get("gate_satisfied")
        and margin_fixture.get("gate_satisfied")
        and d2d3_report.get("margin_runner_contract", {}).get("exact_margin_to_seasonal_lineage_proved")
        and d2d3_report.get("hydrology_seasonal_contract", {}).get("found")
        and sorted(d2d3_report.get("hydrology_seasonal_contract", {}).get("seasonal_attributes", [])) == sorted(HYDROLOGY_FIELDS)
    )
    result["prerequisites_satisfied"] = prerequisites

    if not prerequisites:
        status = "BLOCKED_R517_B6_D2D4_PREREQUISITES_NOT_SATISFIED"
        decision = "RETURN_TO_D2D3_CONTRACT_VALIDATION"
    else:
        generators = d2d.locate_exact_suffix(root, TARGET_GENERATOR_SUFFIX, TARGET_GENERATOR_SHA256)
        shorelines = d2d.locate_named_hash(root, TARGET_I_SHORELINE_NAME, TARGET_I_SHORELINE_SHA256)
        result["generator_candidates"] = [str(p) for p in generators]
        result["i_shoreline_candidates"] = [str(p) for p in shorelines]
        if not generators or not shorelines:
            status = "BLOCKED_R517_B6_D2D4_EXACT_SOURCE_OR_I_SHORELINE_MISSING"
            decision = "RECOVER_EXACT_SOURCE_BINDING"
        else:
            generator = generators[0]
            project_root = d2d.generator_source_root(generator).parent
            result["selected_generator"] = str(generator)
            result["selected_generator_sha256"] = sha256_file(generator)
            result["generator_project_root"] = str(project_root)
            result["runtime_provenance_hits"] = scan_runtime_provenance(project_root)

            fn = d2d.import_exact_generator(generator)
            margin_path = Path(margin_fixture["margin_state_path"])
            baseline_path = Path(margin_fixture["baseline_path"])
            margin_state, margin_land_key = d2d.load_coast_candidate(margin_path)
            result["margin_land_mask_source_key"] = margin_land_key

            with tempfile.TemporaryDirectory(prefix="arcana_r517_b6_d2d4_") as td:
                replay_path = Path(td) / "seasonal_climate_state.npz"
                replay_state = d2d.invoke_generator(fn, project_root, margin_state)
                result["margin_native_serialization"] = d2d3.serialize_state_native(replay_state, replay_path)

                all_ok = True
                with np.load(replay_path, allow_pickle=False) as za, np.load(baseline_path, allow_pickle=False) as zb:
                    for field in HYDROLOGY_FIELDS:
                        if field not in za.files or field not in zb.files:
                            rep = {"eligible": False, "reason": "field_missing"}
                        else:
                            rep = float32_ulp_report(np.asarray(za[field]), np.asarray(zb[field]))
                        result["hydrology_field_ulp_validation"]["fields"][field] = rep
                        if not rep.get("eligible") or not rep.get("within_2_ulp"):
                            all_ok = False

                result["hydrology_field_ulp_validation"]["all_fields_within_bound"] = all_ok
                result["hydrology_field_ulp_validation"]["max_observed_ulp"] = max(
                    (rec.get("max_ulp_distance", 2**63 - 1) for rec in result["hydrology_field_ulp_validation"]["fields"].values()),
                    default=2**63 - 1,
                )

                if not all_ok:
                    status = "BLOCKED_R517_B6_D2D4_HYDROLOGY_ULP_EQUIVALENCE_NOT_PROVED"
                    decision = "RECOVER_HISTORICAL_NUMERIC_RUNTIME_OR_REEVALUATE_GENERATOR_LINEAGE"
                else:
                    result["runtime_ulp_equivalence_authorized"] = True
                    i_shoreline = shorelines[0]
                    with np.load(i_shoreline, allow_pickle=False) as z:
                        elevation = np.asarray(z["elevation_m"]).copy()
                        land = np.asarray(z["effective_land_mask"]).astype(bool, copy=True)
                    if elevation.shape != land.shape:
                        raise RuntimeError(f"I shoreline shape mismatch elevation={elevation.shape} land={land.shape}")
                    i_state = d2d.invoke_generator(fn, project_root, SimpleNamespace(elevation_m=elevation, land_mask=land))
                    out = args.reconstructed_output.resolve()
                    serialized = d2d3.serialize_state_native(i_state, out)
                    with np.load(out, allow_pickle=False) as z:
                        serialized["hydrology_fields_present"] = all(k in z.files for k in HYDROLOGY_FIELDS)
                        serialized["hydrology_field_shapes"] = {k: list(np.asarray(z[k]).shape) for k in HYDROLOGY_FIELDS if k in z.files}
                        serialized["hydrology_field_dtypes"] = {k: str(np.asarray(z[k]).dtype) for k in HYDROLOGY_FIELDS if k in z.files}
                        serialized["hydrology_fields_all_finite"] = all(np.isfinite(np.asarray(z[k])).all() for k in HYDROLOGY_FIELDS if k in z.files)
                    result["i_reconstruction_materialized"] = True
                    result["reconstructed_baseline"] = serialized
                    status = "PASS_R517_B6_D2D4_HYDROLOGY_RUNTIME_EQUIVALENT_AND_I_BASELINE_RECONSTRUCTED"
                    decision = "AUTHORIZE_RECONSTRUCTED_I_SEASONAL_BASELINE_FOR_D3_CANONICAL_PALEOHYDROLOGY_REPLAY"

    result["status"] = status
    result["decision"] = decision
    result["next_if_pass"] = "R5.17-B6-D3_CANONICAL_PALEOHYDROLOGY_REPLAY_IMPLEMENTATION"
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps({
        "status": status,
        "decision": decision,
        "prerequisites_satisfied": result.get("prerequisites_satisfied", False),
        "runtime_ulp_equivalence_authorized": result.get("runtime_ulp_equivalence_authorized", False),
        "max_observed_ulp": result.get("hydrology_field_ulp_validation", {}).get("max_observed_ulp"),
        "i_reconstruction_materialized": result.get("i_reconstruction_materialized", False),
        "reconstructed_baseline_sha256": (result.get("reconstructed_baseline") or {}).get("sha256"),
        "output": str(args.output.resolve()),
    }, indent=2))
    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
