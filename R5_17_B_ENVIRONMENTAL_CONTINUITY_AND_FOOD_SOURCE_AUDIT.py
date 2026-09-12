#!/usr/bin/env python3
"""R5.17 — recover B3 continuity and audit ecological/food source authorities.

This runner does four things without promoting any new human-support semantics:

1. Reconstruct the missing B3 environmental-support NPZ from the exact tracked B3
   implementation and exact catalogued R3.18/R3.19/R3.20 parents, storing the
   result under an explicit RECONSTRUCTED path.
2. Compare the reconstructed B3 manifest against the tracked B3 manifest and
   preserve the distinction between semantic reconstruction and historical byte
   identity.
3. Inspect the exact catalogued R3.33 Holocene environmental resource landscape
   and R3.34 producer resource landscape as candidate parents for later
   BIOLOGICAL_FOOD_SUPPORT derivation.
4. Census marine-resource evidence in the default simulation-results catalogue.

It does NOT materialize BIOLOGICAL_FOOD_SUPPORT, MARINE_SUPPORT, climate
suitability, agriculture, or K(x,t).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path, PureWindowsPath
from typing import Any

import numpy as np

R333_SHA = "5fd7b11df5051245551aa2d23ce334b0a540f171e85ac8a451c603eb63f685b9"
R334_SHA = "31f5954b846be3cb4a6bb14afb2ae19e7cccafd47c90719a1434e9058bc35d86"
R314_SNAPSHOT_SHA = "a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd"

MARINE_TERMS = (
    "marine",
    "fish",
    "fishery",
    "pelagic",
    "benthic",
    "shellfish",
    "coastal productivity",
    "coastal_productivity",
    "marine biomass",
    "marine_biomass",
)

FOOD_KEY_TERMS = (
    "food",
    "edible",
    "yield",
    "harvest",
    "producer",
    "resource",
    "forage",
    "npp",
    "biomass",
    "productivity",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def record_path(repo: Path, record: dict[str, Any]) -> Path:
    raw = record.get("ConsolidatedPath")
    if not raw:
        raise RuntimeError(f"Manifest record lacks ConsolidatedPath: {record}")
    parts = PureWindowsPath(str(raw)).parts
    return repo / "SIMULATION_RESULTS" / Path(*parts)


def find_unique_by_sha(records: list[dict[str, Any]], digest: str) -> dict[str, Any]:
    matches = [r for r in records if str(r.get("SHA256", "")).lower() == digest.lower()]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one manifest record for SHA {digest}; got {len(matches)}")
    return matches[0]


def verify_manifest_record(repo: Path, record: dict[str, Any]) -> dict[str, Any]:
    path = record_path(repo, record)
    expected = str(record.get("SHA256", "")).lower()
    if not path.is_file():
        raise FileNotFoundError(f"Catalogue payload missing: {path}")
    actual = sha256_file(path)
    if actual.lower() != expected:
        raise RuntimeError(
            f"Catalogue payload hash mismatch for {path}\nexpected={expected}\nactual={actual}"
        )
    return {
        "path": str(path.resolve()),
        "sha256": actual,
        "filename": record.get("FileName"),
        "stage": record.get("Stage"),
        "authority_status": record.get("AuthorityStatus"),
        "semantic_status": record.get("SemanticStatus"),
        "semantic_class": record.get("SemanticClass"),
        "primary_use": record.get("PrimaryUse"),
        "forbidden_interpretations": record.get("ForbiddenInterpretations"),
    }


def numeric_stats(arr: np.ndarray) -> dict[str, Any]:
    a = np.asarray(arr)
    out: dict[str, Any] = {
        "shape": list(a.shape),
        "dtype": str(a.dtype),
        "size": int(a.size),
    }
    if a.dtype.kind in "biufc":
        finite = np.isfinite(a)
        out["finite_count"] = int(finite.sum())
        if a.size and finite.any():
            af = a[finite]
            out["min"] = float(np.min(af))
            out["max"] = float(np.max(af))
            out["mean"] = float(np.mean(af, dtype=np.float64))
    return out


def safe_small_values(arr: np.ndarray, limit: int = 128) -> list[Any] | None:
    a = np.asarray(arr)
    if a.size > limit:
        return None
    if a.dtype.kind not in "USbiuf":
        return None
    values: list[Any] = []
    for value in a.reshape(-1).tolist():
        if isinstance(value, np.generic):
            value = value.item()
        values.append(value)
    return values


def inspect_npz(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "arrays": {},
        "food_relevant_keys": [],
    }
    with np.load(path, allow_pickle=False) as z:
        result["keys"] = list(z.files)
        for key in z.files:
            arr = np.asarray(z[key])
            info = numeric_stats(arr)
            values = safe_small_values(arr)
            if values is not None:
                info["values"] = values
            result["arrays"][key] = info
            lower = key.lower()
            if any(term in lower for term in FOOD_KEY_TERMS):
                result["food_relevant_keys"].append(key)
    return result


def compare_b3_manifests(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []

    if expected.get("input_sha256") != actual.get("input_sha256"):
        mismatches.append({"field": "input_sha256", "expected": expected.get("input_sha256"), "actual": actual.get("input_sha256")})

    if expected.get("output_array_count") != actual.get("output_array_count"):
        mismatches.append({"field": "output_array_count", "expected": expected.get("output_array_count"), "actual": actual.get("output_array_count")})

    expected_arrays = expected.get("arrays", {})
    actual_arrays = actual.get("arrays", {})

    if set(expected_arrays) != set(actual_arrays):
        mismatches.append({
            "field": "array_key_set",
            "missing_from_reconstructed": sorted(set(expected_arrays) - set(actual_arrays)),
            "extra_in_reconstructed": sorted(set(actual_arrays) - set(expected_arrays)),
        })

    fields = ("shape", "dtype", "size", "finite_count", "min", "max", "mean")
    for key in sorted(set(expected_arrays) & set(actual_arrays)):
        e = expected_arrays[key]
        a = actual_arrays[key]
        for field in fields:
            if e.get(field) != a.get(field):
                mismatches.append({
                    "array": key,
                    "field": field,
                    "expected": e.get(field),
                    "actual": a.get(field),
                })

    if expected.get("integral_closure_max_abs_error") != actual.get("integral_closure_max_abs_error"):
        mismatches.append({
            "field": "integral_closure_max_abs_error",
            "expected": expected.get("integral_closure_max_abs_error"),
            "actual": actual.get("integral_closure_max_abs_error"),
        })

    return {
        "semantic_manifest_exact": not mismatches,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def reconstruct_b3(repo: Path, catalogue: list[dict[str, Any]], tracked_manifest: dict[str, Any]) -> dict[str, Any]:
    input_hashes = tracked_manifest["input_sha256"]
    labels = {
        "r318_environment": input_hashes["r318_environment"],
        "r319_checkpoint": input_hashes["r319_checkpoint"],
        "r320_hazard": input_hashes["r320_hazard"],
    }

    resolved: dict[str, dict[str, Any]] = {}
    for label, digest in labels.items():
        record = find_unique_by_sha(catalogue, digest)
        resolved[label] = verify_manifest_record(repo, record)

    out_dir = repo / "R5_17_B3_RECONSTRUCTED"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_npz = out_dir / "R5_17_B3_ENVIRONMENTAL_SUPPORT_EXPOSURES_RECONSTRUCTED.npz"
    output_manifest = out_dir / "R5_17_B3_ENVIRONMENTAL_SUPPORT_EXPOSURES_RECONSTRUCTED_MANIFEST.json"

    runner = repo / "R5_17_B3_DERIVE_ENVIRONMENTAL_SUPPORT.py"
    if not runner.is_file():
        raise FileNotFoundError(f"Tracked B3 runner missing: {runner}")

    cmd = [
        sys.executable,
        str(runner),
        "--r318-environment", resolved["r318_environment"]["path"],
        "--r319-checkpoint", resolved["r319_checkpoint"]["path"],
        "--r320-hazard", resolved["r320_hazard"]["path"],
        "--output-npz", str(output_npz),
        "--output-manifest", str(output_manifest),
    ]

    completed = subprocess.run(cmd, cwd=repo, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "B3 reconstruction runner failed\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )

    reconstructed_manifest = load_json(output_manifest)
    manifest_compare = compare_b3_manifests(tracked_manifest, reconstructed_manifest)
    reconstructed_sha = sha256_file(output_npz)
    historical_sha = str(tracked_manifest.get("output_npz_sha256", ""))

    return {
        "parents": resolved,
        "runner": str(runner.resolve()),
        "runner_stdout": completed.stdout,
        "reconstructed_npz": str(output_npz.resolve()),
        "reconstructed_manifest": str(output_manifest.resolve()),
        "reconstructed_npz_sha256": reconstructed_sha,
        "tracked_historical_npz_sha256": historical_sha,
        "historical_byte_identity_recovered": bool(historical_sha and reconstructed_sha.lower() == historical_sha.lower()),
        "semantic_manifest_comparison": manifest_compare,
        "reconstruction_usable": bool(manifest_compare["semantic_manifest_exact"]),
        "historical_payload_identity_claimed": False,
    }


def marine_catalogue_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for record in records:
        text = " ".join(str(record.get(k, "")) for k in (
            "Stage", "FileName", "OriginalRelativePath", "ConsolidatedPath",
            "Contents", "SemanticClass", "PrimaryUse", "ForbiddenInterpretations",
        )).lower()
        hits = sorted({term for term in MARINE_TERMS if term in text})
        if hits:
            out.append({
                "stage": record.get("Stage"),
                "file_name": record.get("FileName"),
                "sha256": record.get("SHA256"),
                "consolidated_path": record.get("ConsolidatedPath"),
                "authority_status": record.get("AuthorityStatus"),
                "semantic_status": record.get("SemanticStatus"),
                "semantic_class": record.get("SemanticClass"),
                "primary_use": record.get("PrimaryUse"),
                "hits": hits,
            })
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("R5_17_B_ENVIRONMENTAL_CONTINUITY_AND_FOOD_SOURCE_AUDIT.json"),
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    catalogue_path = repo / "SIMULATION_RESULTS" / "MANIFEST.json"
    tracked_b3_manifest_path = repo / "R5_17_B3_ENVIRONMENTAL_SUPPORT_EXPOSURES_MANIFEST.json"

    if not catalogue_path.is_file():
        raise FileNotFoundError(f"Simulation result catalogue missing: {catalogue_path}")
    if not tracked_b3_manifest_path.is_file():
        raise FileNotFoundError(f"Tracked B3 manifest missing: {tracked_b3_manifest_path}")

    catalogue = load_json(catalogue_path)
    tracked_b3_manifest = load_json(tracked_b3_manifest_path)

    b3 = reconstruct_b3(repo, catalogue, tracked_b3_manifest)

    r333_record = find_unique_by_sha(catalogue, R333_SHA)
    r334_record = find_unique_by_sha(catalogue, R334_SHA)
    r314_record = find_unique_by_sha(catalogue, R314_SNAPSHOT_SHA)

    r333_binding = verify_manifest_record(repo, r333_record)
    r334_binding = verify_manifest_record(repo, r334_record)
    r314_binding = verify_manifest_record(repo, r314_record)

    r333 = inspect_npz(Path(r333_binding["path"]))
    r334 = inspect_npz(Path(r334_binding["path"]))
    r314 = inspect_npz(Path(r314_binding["path"]))

    marine = marine_catalogue_candidates(catalogue)

    r333_names = r333.get("arrays", {}).get("environment_variable_names", {}).get("values")
    r334_food_keys = r334.get("food_relevant_keys", [])
    r314_has_npp = "npp_factor_relative_book" in r314.get("keys", [])

    decision = {
        "b3_continuity": (
            "RECONSTRUCTED_AND_MANIFEST_VERIFIED"
            if b3["reconstruction_usable"]
            else "BLOCKED_RECONSTRUCTION_NOT_MANIFEST_EQUIVALENT"
        ),
        "r333_role": "SEALED_ENVIRONMENTAL_RESOURCE_PARENT_ONLY_NOT_DIRECT_HUMAN_FOOD_OR_K",
        "r334_role": (
            "AUDIT_PRODUCER_RESOURCE_FIELDS_FOR_WILD_FOOD_OPPORTUNITY_DERIVATION"
            if r334_food_keys
            else "INSPECT_PRODUCER_RESOURCE_SCHEMA_BEFORE_ANY_FOOD_PROMOTION"
        ),
        "r314_npp_modulation_available": bool(r314_has_npp),
        "marine_support": (
            "AUDIT_EXISTING_MARINE_CANDIDATES"
            if marine
            else "EXPLICITLY_UNRESOLVED_NO_CATALOGUED_MARINE_RESOURCE_AUTHORITY_FOUND"
        ),
        "next_action": (
            "DESIGN_R517_B_BIOLOGICAL_FOOD_SUPPORT_FROM_SEALED_R333_R334_ONLY_AFTER_"
            "R334_RESOURCE_SCHEMA_AND_EXOGENEITY_AUDIT"
        ),
    }

    status = (
        "PASS_R517_B_ENVIRONMENTAL_CONTINUITY_RECOVERED_AND_FOOD_SOURCE_AUDIT_CAPTURED"
        if b3["reconstruction_usable"]
        else "BLOCKED_R517_B_B3_CONTINUITY_RECONSTRUCTION_MISMATCH"
    )

    result = {
        "schema": "ARCANA_R5_17_B_ENVIRONMENTAL_CONTINUITY_AND_FOOD_SOURCE_AUDIT_V1",
        "status": status,
        "decision": decision,
        "b3_continuity": b3,
        "r333_environmental_resource_landscape": {
            "binding": r333_binding,
            "inspection": r333,
            "expected_environment_channels": r333_names,
        },
        "r334_producer_resource_landscape": {
            "binding": r334_binding,
            "inspection": r334,
            "food_relevant_keys": r334_food_keys,
        },
        "r314_paleoclimate_snapshots": {
            "binding": r314_binding,
            "inspection": r314,
            "npp_factor_relative_book_present": bool(r314_has_npp),
        },
        "marine_resource_catalogue_candidates": marine,
        "marine_resource_candidate_count": len(marine),
        "governance": {
            "scientific_promotion_performed": False,
            "biological_food_support_materialized": False,
            "marine_support_materialized": False,
            "climate_suitability_materialized": False,
            "K_materialized": False,
            "external_engine_executed": False,
            "canonical_mutation": False,
            "historical_b3_payload_identity_claimed": False,
        },
    }

    output = args.output
    if not output.is_absolute():
        output = repo / output
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": status,
        "b3_reconstruction_usable": b3["reconstruction_usable"],
        "b3_historical_byte_identity_recovered": b3["historical_byte_identity_recovered"],
        "r333_hash_exact": r333["sha256"].lower() == R333_SHA,
        "r333_environment_channels": r333_names,
        "r334_hash_exact": r334["sha256"].lower() == R334_SHA,
        "r334_keys": r334.get("keys", []),
        "r334_food_relevant_keys": r334_food_keys,
        "r314_npp_factor_present": r314_has_npp,
        "marine_resource_candidate_count": len(marine),
        "output": str(output.resolve()),
    }, indent=2))

    return 0 if status.startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
