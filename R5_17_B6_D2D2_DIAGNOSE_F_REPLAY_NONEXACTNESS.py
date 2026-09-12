from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "monthly_temperature_c",
    "monthly_precipitation_mm",
    "monthly_pet_mm",
)
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".ps1", ".yaml", ".yml", ".toml"}
MAX_TEXT_BYTES = 8 * 1024 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def field_diagnostics(cmp: dict[str, Any]) -> dict[str, Any]:
    fields = cmp.get("fields", {}) or {}
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    shape_mismatch: list[str] = []
    nonexact: list[str] = []
    required_nonexact: list[str] = []
    max_abs_values: list[float] = []
    required_max_abs_values: list[float] = []

    for key, rec in sorted(fields.items()):
        present = bool(rec.get("present_in_state", rec.get("present_in_baseline", True)))
        exact = rec.get("exact_array_equal")
        state_shape = rec.get("state_shape")
        baseline_shape = rec.get("baseline_shape")
        max_abs = rec.get("max_abs_difference")
        mean_abs = rec.get("mean_abs_difference")
        required = key in REQUIRED_FIELDS

        if not present:
            missing.append(key)
        if state_shape is not None and baseline_shape is not None and state_shape != baseline_shape:
            shape_mismatch.append(key)
        if exact is False:
            nonexact.append(key)
            if required:
                required_nonexact.append(key)
        if isinstance(max_abs, (int, float)):
            max_abs_values.append(float(max_abs))
            if required:
                required_max_abs_values.append(float(max_abs))

        rows.append({
            "field": key,
            "required": required,
            "present_in_state": present,
            "state_shape": state_shape,
            "baseline_shape": baseline_shape,
            "state_dtype": rec.get("state_dtype"),
            "baseline_dtype": rec.get("baseline_dtype"),
            "exact_array_equal": exact,
            "max_abs_difference": max_abs,
            "mean_abs_difference": mean_abs,
        })

    schema_exact = bool(cmp.get("schema_key_set_exact"))
    all_keys_present = bool(cmp.get("all_baseline_schema_keys_present_in_state"))
    required_exact = bool(cmp.get("required_fields_exact"))

    if missing or shape_mismatch or not all_keys_present:
        classification = "SCHEMA_OR_SHAPE_NONEXACTNESS"
    elif not nonexact:
        classification = "EXACT"
    else:
        req_max = max(required_max_abs_values) if required_max_abs_values else None
        overall_max = max(max_abs_values) if max_abs_values else None
        reference = req_max if req_max is not None else overall_max
        if reference is None:
            classification = "NONEXACT_WITHOUT_NUMERIC_DELTA"
        elif reference <= 1e-12:
            classification = "NUMERIC_NONEXACT_LE_1E-12"
        elif reference <= 1e-9:
            classification = "NUMERIC_NONEXACT_LE_1E-9"
        elif reference <= 1e-6:
            classification = "NUMERIC_NONEXACT_LE_1E-6"
        else:
            classification = "MATERIAL_NUMERIC_NONEXACTNESS"

    return {
        "schema_key_set_exact": schema_exact,
        "all_baseline_schema_keys_present_in_state": all_keys_present,
        "required_fields_exact": required_exact,
        "missing_fields": missing,
        "shape_mismatch_fields": shape_mismatch,
        "nonexact_fields": nonexact,
        "required_nonexact_fields": required_nonexact,
        "max_abs_difference_any_field": max(max_abs_values) if max_abs_values else None,
        "max_abs_difference_required_fields": max(required_max_abs_values) if required_max_abs_values else None,
        "classification": classification,
        "fields": rows,
    }


def stage_aligned(baseline_kind: str, coast_path: str) -> bool:
    low = norm(coast_path).lower()
    return baseline_kind.lower() in low


def historical_pairing_evidence(root: Path, attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    coast_names = sorted({Path(a.get("coast_candidate_path", "")).name for a in attempts if a.get("coast_candidate_path")})
    stage_terms = sorted({str(a.get("baseline_kind", "")) for a in attempts if a.get("baseline_kind")})
    out: list[dict[str, Any]] = []

    for p in root.rglob("*"):
        if not p.is_file() or ".git" in p.parts or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if p.name.startswith("R5_17_B6_") or p.name == "ARCANA_WORLD_CURRENT_STATE.md":
            continue
        try:
            if p.stat().st_size > MAX_TEXT_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        low = text.lower()
        if "seasonal_climate_state.npz" not in low and "build_seasonal_climate" not in low:
            continue

        matched_coasts = [n for n in coast_names if n and n.lower() in low]
        matched_stages = [s for s in stage_terms if s and s.lower() in low]
        if not matched_coasts and not matched_stages:
            continue

        lines = text.splitlines()
        hits: list[dict[str, Any]] = []
        needles = ["seasonal_climate_state.npz", "build_seasonal_climate", *matched_coasts, *matched_stages]
        for i, line in enumerate(lines, start=1):
            ll = line.lower()
            matched = [n for n in needles if n.lower() in ll]
            if not matched:
                continue
            lo = max(1, i - 4)
            hi = min(len(lines), i + 4)
            hits.append({
                "line": i,
                "terms": matched,
                "excerpt": "\n".join(f"{j}: {lines[j-1]}" for j in range(lo, hi + 1))[:6000],
            })
            if len(hits) >= 40:
                break

        if hits:
            out.append({
                "path": str(p.resolve()),
                "sha256": sha256_file(p),
                "matched_coast_names": matched_coasts,
                "matched_stage_terms": matched_stages,
                "hits": hits,
            })
    return out


def inspect_generator(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"found": False, "path": str(path)}
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)
    lines = text.splitlines()
    target = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "build_seasonal_climate":
            target = node
            break
    if target is None:
        return {"found": False, "path": str(path), "sha256": sha256_file(path)}

    relevant: list[dict[str, Any]] = []
    project_root_refs = 0
    for node in ast.walk(target):
        if isinstance(node, ast.Name) and node.id == "project_root":
            project_root_refs += 1
    start = target.lineno
    end = getattr(target, "end_lineno", start)
    for i in range(start, end + 1):
        line = lines[i - 1]
        ll = line.lower()
        if any(t in ll for t in ("project_root", "coast_state", "temperature", "precip", "pet", "return", "load", "save")):
            relevant.append({"line": i, "text": line[:1800]})
    return {
        "found": True,
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "signature": lines[start - 1].strip(),
        "project_root_reference_count_in_function_ast": project_root_refs,
        "relevant_lines": relevant[:160],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Diagnose why R5.17-B6-D2D F-era seasonal replay is non-exact. This step is read-only: it does not authorize tolerances or reconstruct the I baseline.")
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--d2d-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("R5_17_B6_D2D2_F_REPLAY_NONEXACTNESS_DIAGNOSTICS.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    d2d_path = args.d2d_json.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    if not d2d_path.is_file():
        raise FileNotFoundError(d2d_path)

    d2d = json.loads(d2d_path.read_text(encoding="utf-8"))
    attempts = d2d.get("validation_attempts", []) or []
    diagnostics: list[dict[str, Any]] = []

    for idx, attempt in enumerate(attempts):
        cmp = attempt.get("comparison") or {}
        diag = field_diagnostics(cmp) if cmp else {
            "classification": "NO_COMPARISON_AVAILABLE",
            "fields": [],
        }
        baseline_kind = str(attempt.get("baseline_kind", ""))
        coast_path = str(attempt.get("coast_candidate_path", ""))
        diagnostics.append({
            "attempt_index": idx,
            "status": attempt.get("status"),
            "baseline_kind": baseline_kind,
            "baseline_path": attempt.get("baseline_path"),
            "baseline_sha256": attempt.get("baseline_sha256"),
            "coast_candidate_path": coast_path,
            "coast_candidate_sha256": attempt.get("coast_candidate_sha256"),
            "land_mask_source_key": attempt.get("land_mask_source_key"),
            "stage_aligned_pair": stage_aligned(baseline_kind, coast_path),
            "diagnostics": diag,
            "execution_error": attempt.get("error"),
        })

    def rank_key(rec: dict[str, Any]) -> tuple[Any, ...]:
        d = rec["diagnostics"]
        mx = d.get("max_abs_difference_required_fields")
        if mx is None:
            mx = float("inf")
        return (
            0 if rec.get("stage_aligned_pair") else 1,
            0 if d.get("all_baseline_schema_keys_present_in_state") else 1,
            len(d.get("required_nonexact_fields", [])),
            float(mx),
            rec["attempt_index"],
        )

    ranked = sorted(diagnostics, key=rank_key)
    pairing_evidence = historical_pairing_evidence(root, attempts)

    generator_path_raw = d2d.get("selected_generator")
    generator = inspect_generator(Path(generator_path_raw)) if generator_path_raw else {"found": False, "path": None}

    classifications = sorted({r["diagnostics"].get("classification") for r in diagnostics})
    stage_aligned_count = sum(bool(r.get("stage_aligned_pair")) for r in diagnostics)
    exact_count = sum(r["diagnostics"].get("classification") == "EXACT" for r in diagnostics)

    if not attempts:
        status = "BLOCKED_R517_B6_D2D2_NO_D2D_VALIDATION_ATTEMPTS_TO_DIAGNOSE"
        decision = "RETURN_TO_D2D_RUNTIME_OR_FIXTURE_DISCOVERY"
    elif exact_count:
        status = "PASS_R517_B6_D2D2_EXACT_REPLAY_PRESENT_IN_DIAGNOSTICS"
        decision = "REVIEW_D2D_EXACT_REPLAY_SELECTION_LOGIC"
    else:
        status = "PASS_R517_B6_D2D2_F_REPLAY_NONEXACTNESS_DIAGNOSTICS_CAPTURED"
        decision = "ADJUDICATE_STAGE_ALIGNED_FIXTURE_AND_NUMERIC_DIFFERENCE_WITHOUT_TOLERANCE_PROMOTION"

    result = {
        "schema": "ARCANA_R5_17_B6_D2D2_F_REPLAY_NONEXACTNESS_DIAGNOSTICS_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2D2",
        "purpose": "Diagnose D2D F-era non-exact replay before any tolerance or reconstructed-baseline authorization. Distinguish schema/shape mismatch from numerical divergence and recover historical stage-to-coast pairing evidence.",
        "search_root": str(root),
        "d2d_json": str(d2d_path),
        "d2d_json_sha256": sha256_file(d2d_path),
        "d2d_status": d2d.get("status"),
        "validation_attempt_count": len(attempts),
        "stage_aligned_attempt_count": stage_aligned_count,
        "exact_attempt_count": exact_count,
        "classifications_present": classifications,
        "attempt_diagnostics": diagnostics,
        "ranked_attempt_indices": [r["attempt_index"] for r in ranked],
        "best_diagnostic_attempt": ranked[0] if ranked else None,
        "historical_pairing_evidence_count": len(pairing_evidence),
        "historical_pairing_evidence": pairing_evidence[:60],
        "generator_inspection": generator,
        "tolerance_authorized": False,
        "i_reconstruction_authorized": False,
        "i_reconstruction_materialized": False,
        "external_provider_authorized": False,
        "canonical_mutation": False,
        "decision": decision,
        "status": status,
        "next_if_pass": "R5.17-B6-D2D3_ADJUDICATE_F_REPLAY_DIFFERENCE_OR_HISTORICAL_RUNTIME_BINDING",
    }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "decision": decision,
        "validation_attempt_count": len(attempts),
        "stage_aligned_attempt_count": stage_aligned_count,
        "classifications_present": classifications,
        "best_attempt_index": (ranked[0]["attempt_index"] if ranked else None),
        "best_attempt_baseline_kind": (ranked[0]["baseline_kind"] if ranked else None),
        "best_attempt_stage_aligned": (ranked[0]["stage_aligned_pair"] if ranked else None),
        "best_attempt_classification": (ranked[0]["diagnostics"].get("classification") if ranked else None),
        "best_attempt_required_max_abs_difference": (ranked[0]["diagnostics"].get("max_abs_difference_required_fields") if ranked else None),
        "historical_pairing_evidence_count": len(pairing_evidence),
        "generator_project_root_reference_count": generator.get("project_root_reference_count_in_function_ast"),
        "output": str(args.output.resolve()),
    }, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
