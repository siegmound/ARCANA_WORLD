from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

TARGET_NAME = "seasonal_climate_state_I.npz"
TARGET_DIR = "v0_5_5I_SEALED"
PHYSICAL_HASH = "347f07b9ff16f5c097319898c0b33b86851fc66775b9243ce0f98dce279b954f"
MARGIN_HASH = "1b32d97a0b4dad12f01f4c286461d6ca597c2d46a390a8801771735d972d93f6"
REQUIRED_FIELDS = (
    "monthly_temperature_c",
    "monthly_precipitation_mm",
    "monthly_pet_mm",
)
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".ps1", ".yaml", ".yml", ".toml"}
MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_HITS_PER_FILE = 120


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def locate_hash(root: Path, expected: str) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*.npz"):
        if ".git" in p.parts:
            continue
        try:
            if sha256_file(p) == expected:
                out.append(p.resolve())
        except OSError:
            continue
    return sorted(out, key=lambda p: norm(p).lower())


def array_stats(a: np.ndarray) -> dict[str, Any]:
    arr = np.asarray(a)
    rec: dict[str, Any] = {"shape": list(arr.shape), "dtype": str(arr.dtype)}
    if arr.dtype.kind in "biufc":
        finite = np.isfinite(arr)
        rec["finite_count"] = int(finite.sum())
        rec["total_count"] = int(arr.size)
        if np.any(finite):
            vals = arr[finite].astype(np.float64, copy=False)
            rec.update({
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals)),
            })
    return rec


def inspect_candidate(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as z:
        keys = sorted(z.files)
        arrays = {k: array_stats(z[k]) for k in keys}
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "keys": keys,
        "key_count": len(keys),
        "required_fields_present": all(k in keys for k in REQUIRED_FIELDS),
        "arrays": arrays,
    }


def compare_required(a_path: Path, b_path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    with np.load(a_path, allow_pickle=False) as za, np.load(b_path, allow_pickle=False) as zb:
        for key in REQUIRED_FIELDS:
            if key not in za.files or key not in zb.files:
                out[key] = {"comparable": False, "reason": "missing_required_field"}
                continue
            a = np.asarray(za[key])
            b = np.asarray(zb[key])
            if a.shape != b.shape:
                out[key] = {"comparable": False, "shape_a": list(a.shape), "shape_b": list(b.shape)}
                continue
            af = a.astype(np.float64, copy=False)
            bf = b.astype(np.float64, copy=False)
            valid = np.isfinite(af) & np.isfinite(bf)
            diff = af - bf
            valid_diff = diff[valid]
            out[key] = {
                "comparable": True,
                "shape": list(a.shape),
                "exact_array_equal": bool(np.array_equal(a, b, equal_nan=True)),
                "finite_overlap_count": int(valid.sum()),
                "differing_element_count": int(np.count_nonzero((a != b) & ~(np.isnan(af) & np.isnan(bf)))) if a.dtype.kind in "fc" or b.dtype.kind in "fc" else int(np.count_nonzero(a != b)),
                "max_abs_difference": float(np.max(np.abs(valid_diff))) if valid_diff.size else None,
                "mean_abs_difference": float(np.mean(np.abs(valid_diff))) if valid_diff.size else None,
            }
    return out


def text_hits(root: Path) -> list[dict[str, Any]]:
    needles = (
        TARGET_NAME,
        TARGET_DIR,
        PHYSICAL_HASH,
        MARGIN_HASH,
        "outputs/hybrid1/physical_finalization/seasonal_climate_state.npz",
        "outputs/hybrid1/margin_morphogenesis/seasonal_climate_state.npz",
        "build_seasonal_climate",
        "seasonal_climate_state.npz",
        "Copy-Item",
        "copyfile",
        "shutil.copy",
        "run_margin_morphogenesis",
    )
    records: list[dict[str, Any]] = []
    for p in root.rglob("*"):
        if not p.is_file() or ".git" in p.parts or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if p.stat().st_size > MAX_TEXT_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits: list[dict[str, Any]] = []
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            ll = line.lower()
            matched = [n for n in needles if n.lower() in ll]
            if matched:
                lo = max(1, i - 2)
                hi = min(len(lines), i + 2)
                excerpt = "\n".join(f"{j}: {lines[j-1]}" for j in range(lo, hi + 1))
                hits.append({"line": i, "terms": matched, "excerpt": excerpt[:5000]})
                if len(hits) >= MAX_HITS_PER_FILE:
                    break
        if hits:
            records.append({"path": str(p.resolve()), "sha256": sha256_file(p), "hits": hits})
    return records


def record_text(record: dict[str, Any]) -> str:
    chunks = [record.get("path", "")]
    for h in record.get("hits", []):
        chunks.append(h.get("excerpt", ""))
    return "\n".join(chunks).lower()


def bridge_records(refs: list[dict[str, Any]], candidate_hash: str, candidate_kind: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    source_phrase = (
        "outputs/hybrid1/physical_finalization/seasonal_climate_state.npz"
        if candidate_kind == "physical_finalization"
        else "outputs/hybrid1/margin_morphogenesis/seasonal_climate_state.npz"
    )
    for r in refs:
        text = record_text(r)
        target = TARGET_NAME.lower() in text or TARGET_DIR.lower() in text
        source = candidate_hash.lower() in text or source_phrase.lower() in text
        copy_semantics = any(x in text for x in ("copy-item", "copyfile", "shutil.copy", "copy(", "staging", "package", "sealed", "manifest"))
        if target and source and copy_semantics:
            out.append(r)
    return out


def classify_lineage(refs: list[dict[str, Any]]) -> dict[str, Any]:
    physical_parent_refs: list[dict[str, Any]] = []
    margin_rerun_refs: list[dict[str, Any]] = []
    for r in refs:
        text = record_text(r)
        if (
            "physical_finalization/seasonal_climate_state.npz" in text
            and ("margin_morphogenesis" in text or "run_margin_morphogenesis" in text)
        ):
            physical_parent_refs.append(r)
        if (
            "build_seasonal_climate" in text
            and "margin" in text
            and "seasonal_climate_state.npz" in text
        ):
            margin_rerun_refs.append(r)
    return {
        "physical_finalization_parent_reference_count": len(physical_parent_refs),
        "margin_morphogenesis_rerun_reference_count": len(margin_rerun_refs),
        "physical_finalization_parent_references": physical_parent_refs[:20],
        "margin_morphogenesis_rerun_references": margin_rerun_refs[:20],
        "parent_child_lineage_recovered": bool(physical_parent_refs and margin_rerun_refs),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="R5.17-B6-D2A: adjudicate which recovered alternate seasonal-climate payload, if any, is the exact v0.5.5I baseline; schema compatibility alone is insufficient.")
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("R5_17_B6_D2A_SEASONAL_BASELINE_IDENTITY_ADJUDICATION.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    physical_paths = locate_hash(root, PHYSICAL_HASH)
    margin_paths = locate_hash(root, MARGIN_HASH)
    physical = [inspect_candidate(p) for p in physical_paths]
    margin = [inspect_candidate(p) for p in margin_paths]
    refs = text_hits(root)
    lineage = classify_lineage(refs)

    physical_bridges = bridge_records(refs, PHYSICAL_HASH, "physical_finalization")
    margin_bridges = bridge_records(refs, MARGIN_HASH, "margin_morphogenesis")

    comparison: dict[str, Any] = {}
    if physical_paths and margin_paths:
        comparison = compare_required(physical_paths[0], margin_paths[0])

    both_schema_compatible = bool(
        physical and margin
        and all(x.get("required_fields_present") for x in physical)
        and all(x.get("required_fields_present") for x in margin)
    )
    candidates_distinct = bool(physical_paths and margin_paths and PHYSICAL_HASH != MARGIN_HASH)

    authorized_hash: str | None = None
    authorized_path: str | None = None
    exact_identity = False
    decision: str
    status: str

    # Exact identity requires a documentary source-to-v0.5.5I bridge for one candidate
    # and no conflicting bridge for the other. Directory/stage names alone are not enough.
    if physical_bridges and not margin_bridges:
        authorized_hash = PHYSICAL_HASH
        authorized_path = str(physical_paths[0]) if physical_paths else None
        exact_identity = True
        decision = "BIND_PHYSICAL_FINALIZATION_AS_EXACT_V055I_SEASONAL_BASELINE"
        status = "PASS_R517_B6_D2A_EXACT_SEASONAL_BASELINE_IDENTITY_ADJUDICATED"
    elif margin_bridges and not physical_bridges:
        authorized_hash = MARGIN_HASH
        authorized_path = str(margin_paths[0]) if margin_paths else None
        exact_identity = True
        decision = "BIND_MARGIN_MORPHOGENESIS_AS_EXACT_V055I_SEASONAL_BASELINE"
        status = "PASS_R517_B6_D2A_EXACT_SEASONAL_BASELINE_IDENTITY_ADJUDICATED"
    elif lineage["parent_child_lineage_recovered"] and both_schema_compatible and candidates_distinct:
        decision = "PARENT_CHILD_LINEAGE_ADJUDICATED_BUT_V055I_PROMOTION_IDENTITY_UNRESOLVED"
        status = "PASS_R517_B6_D2A_PARENT_CHILD_LINEAGE_ADJUDICATED_IDENTITY_STILL_UNRESOLVED"
    else:
        decision = "ALTERNATE_BASELINE_IDENTITY_AMBIGUOUS"
        status = "BLOCKED_R517_B6_D2A_ALTERNATE_BASELINE_IDENTITY_AMBIGUOUS"

    result = {
        "schema": "ARCANA_R5_17_B6_D2A_SEASONAL_BASELINE_IDENTITY_ADJUDICATION_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2A",
        "purpose": "Adjudicate the exact identity of recovered schema-compatible seasonal climate candidates against the lost v0.5.5I seasonal baseline using documentary promotion/copy evidence and explicit parent-child lineage, without executing historical simulation.",
        "search_root": str(root),
        "target_v055i_payload": f"inputs/{TARGET_DIR}/{TARGET_NAME}",
        "required_fields": list(REQUIRED_FIELDS),
        "physical_finalization_candidate_hash": PHYSICAL_HASH,
        "margin_morphogenesis_candidate_hash": MARGIN_HASH,
        "physical_finalization_candidates": physical,
        "margin_morphogenesis_candidates": margin,
        "candidate_required_field_comparison": comparison,
        "both_candidates_schema_compatible": both_schema_compatible,
        "candidates_hash_distinct": candidates_distinct,
        "text_reference_file_count": len(refs),
        "lineage": lineage,
        "physical_finalization_to_v055i_bridge_count": len(physical_bridges),
        "margin_morphogenesis_to_v055i_bridge_count": len(margin_bridges),
        "physical_finalization_to_v055i_bridges": physical_bridges[:20],
        "margin_morphogenesis_to_v055i_bridges": margin_bridges[:20],
        "exact_v055i_seasonal_baseline_identity_adjudicated": exact_identity,
        "authorized_baseline_sha256": authorized_hash,
        "authorized_baseline_path": authorized_path,
        "replay_execution_ready_from_d2a": exact_identity,
        "decision": decision,
        "historical_source_executed": False,
        "external_provider_authorized": False,
        "freshwater_support_materialized": False,
        "canonical_mutation": False,
        "status": status,
        "next_if_exact": "R5.17-B6-D3_CANONICAL_PALEOHYDROLOGY_REPLAY_IMPLEMENTATION",
        "next_if_lineage_only": "R5.17-B6-D2B_RECOVER_V055I_SEASONAL_PROMOTION_OR_RECONSTRUCTION_AUTHORITY",
    }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "decision": decision,
        "physical_finalization_candidate_count": len(physical),
        "margin_morphogenesis_candidate_count": len(margin),
        "both_candidates_schema_compatible": both_schema_compatible,
        "candidates_hash_distinct": candidates_distinct,
        "parent_child_lineage_recovered": lineage["parent_child_lineage_recovered"],
        "physical_finalization_to_v055i_bridge_count": len(physical_bridges),
        "margin_morphogenesis_to_v055i_bridge_count": len(margin_bridges),
        "exact_v055i_seasonal_baseline_identity_adjudicated": exact_identity,
        "authorized_baseline_sha256": authorized_hash,
        "authorized_baseline_path": authorized_path,
        "replay_execution_ready_from_d2a": exact_identity,
        "output": str(args.output.resolve()),
    }, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
