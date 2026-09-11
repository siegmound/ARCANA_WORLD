from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

TARGET_SHORELINE_NAME = "shoreline_state_I.npz"
TARGET_SHORELINE_SHA256 = "f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85"
TARGET_GENERATOR_SUFFIX = "src/arcana_worldsim/finalization/seasonal.py"
TARGET_GENERATOR_SHA256 = "3ec12145617ae63e6ce9d9bd123c159525f83925f9257f1138f3490bb3e70de2"
PALEOCLIMATE_SUFFIX = "src/arcana_worldsim/paleoclimate/model.py"
PALEOCLIMATE_SHA256 = "de2399e2b92157ee98d10458db5dcd849b557c076beeed3a648154a6c62e016f"
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".ps1", ".yaml", ".yml", ".toml"}
MAX_TEXT_BYTES = 4 * 1024 * 1024


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
            pass
    return sorted(out, key=lambda p: (len(str(p)), norm(p).lower()))


def locate_exact_named(root: Path, name: str, expected_sha: str) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob(name):
        if not p.is_file() or ".git" in p.parts:
            continue
        try:
            if sha256_file(p) == expected_sha:
                out.append(p.resolve())
        except OSError:
            pass
    return sorted(out, key=lambda p: norm(p).lower())


def inspect_shoreline(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as z:
        keys = sorted(z.files)
        rec: dict[str, Any] = {
            "path": str(path),
            "sha256": sha256_file(path),
            "keys": keys,
            "key_count": len(keys),
        }
        for key in ("effective_land_mask", "land_mask", "ocean_mask", "land_fraction", "elevation_m"):
            if key not in z.files:
                continue
            a = np.asarray(z[key])
            item: dict[str, Any] = {"shape": list(a.shape), "dtype": str(a.dtype)}
            if a.dtype.kind in "biufc":
                finite = np.isfinite(a)
                item["finite_count"] = int(finite.sum())
                item["total_count"] = int(a.size)
                if finite.any():
                    vals = a[finite].astype(np.float64, copy=False)
                    item["min"] = float(vals.min())
                    item["max"] = float(vals.max())
                    item["mean"] = float(vals.mean())
            rec[key] = item

        if "effective_land_mask" in z.files and "ocean_mask" in z.files:
            land = np.asarray(z["effective_land_mask"]).astype(bool)
            ocean = np.asarray(z["ocean_mask"]).astype(bool)
            rec["effective_land_vs_ocean"] = {
                "same_shape": land.shape == ocean.shape,
                "overlap_true_count": int(np.count_nonzero(land & ocean)) if land.shape == ocean.shape else None,
                "partition_mismatch_count": int(np.count_nonzero(land != ~ocean)) if land.shape == ocean.shape else None,
            }
    return rec


def source_hits(path: Path, terms: tuple[str, ...]) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    out: list[dict[str, Any]] = []
    for i, line in enumerate(lines, start=1):
        ll = line.lower()
        matched = [t for t in terms if t.lower() in ll]
        if not matched:
            continue
        lo = max(1, i - 3)
        hi = min(len(lines), i + 3)
        out.append({
            "line": i,
            "terms": matched,
            "excerpt": "\n".join(f"{j}: {lines[j-1]}" for j in range(lo, hi + 1))[:5000],
        })
    return out[:120]


def historical_alias_references(root: Path) -> list[dict[str, Any]]:
    needles = (
        "effective_land_mask",
        "land_mask",
        "shoreline_state_I.npz",
        "CoastOceanState",
        "coast_state",
    )
    out: list[dict[str, Any]] = []
    for p in root.rglob("*"):
        if not p.is_file() or ".git" in p.parts or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        # Exclude the current R5.17 audit family so it cannot prove itself.
        if p.name.startswith("R5_17_B6_") or p.name == "ARCANA_WORLD_CURRENT_STATE.md":
            continue
        try:
            if p.stat().st_size > MAX_TEXT_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        low = text.lower()
        if "effective_land_mask" not in low:
            continue
        hits = source_hits(p, needles)
        if hits:
            out.append({"path": str(p.resolve()), "sha256": sha256_file(p), "hits": hits})
    return out


def has_explicit_alias_evidence(records: list[dict[str, Any]]) -> bool:
    patterns = (
        r"land_mask\s*=\s*.*effective_land_mask",
        r"[\"']land_mask[\"']\s*:\s*.*effective_land_mask",
        r"effective_land_mask.*(?:is|as|used as|serves as).*land_mask",
        r"land\s*=\s*.*[\"']effective_land_mask[\"']",
    )
    for record in records:
        for hit in record.get("hits", []):
            text = hit.get("excerpt", "")
            if any(re.search(p, text, flags=re.IGNORECASE | re.DOTALL) for p in patterns):
                return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="R5.17-B6-D2C1: adjudicate whether authenticated shoreline_state_I.effective_land_mask may be exposed as the canonical seasonal generator's coast_state.land_mask without inventing geometry.")
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("R5_17_B6_D2C1_SHORELINE_LAND_MASK_ADAPTER_ADJUDICATION.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    shorelines = locate_exact_named(root, TARGET_SHORELINE_NAME, TARGET_SHORELINE_SHA256)
    shoreline = inspect_shoreline(shorelines[0]) if shorelines else None

    generators = locate_exact_suffix(root, TARGET_GENERATOR_SUFFIX, TARGET_GENERATOR_SHA256)
    paleos = locate_exact_suffix(root, PALEOCLIMATE_SUFFIX, PALEOCLIMATE_SHA256)

    generator_hits = source_hits(generators[0], ("coast_state.land_mask", "coast_state.elevation_m", "land_mask", "elevation_m")) if generators else []
    paleo_hits = source_hits(paleos[0], ("effective_land_mask", "land_mask", "shoreline_state_I.npz")) if paleos else []
    historical_refs = historical_alias_references(root)

    exact_shoreline = bool(shorelines)
    exact_generator = bool(generators)
    exact_paleo = bool(paleos)
    has_effective = bool(shoreline and "effective_land_mask" in shoreline.get("keys", []))
    has_elevation = bool(shoreline and "elevation_m" in shoreline.get("keys", []))
    no_raw_land = bool(shoreline and "land_mask" not in shoreline.get("keys", []))

    partition = (shoreline or {}).get("effective_land_vs_ocean", {})
    coherent_partition = bool(
        partition.get("same_shape")
        and partition.get("overlap_true_count") == 0
        and partition.get("partition_mismatch_count") == 0
    )

    paleo_consumes_effective = any("effective_land_mask" in h.get("excerpt", "") for h in paleo_hits)
    explicit_alias = has_explicit_alias_evidence(historical_refs)

    # Strong authorization can come either from an explicit historical alias assignment,
    # or from the exact sealed shoreline's effective_land_mask being the only terrestrial
    # boolean mask, complementing ocean_mask exactly, while the exact R3.14 consumer uses
    # effective_land_mask as its land geometry. This is an interface adapter, not a new field.
    adapter_authorized = bool(
        exact_shoreline
        and exact_generator
        and exact_paleo
        and has_effective
        and has_elevation
        and no_raw_land
        and coherent_partition
        and paleo_consumes_effective
        and (explicit_alias or coherent_partition)
    )

    if adapter_authorized:
        status = "PASS_R517_B6_D2C1_SHORELINE_LAND_MASK_ADAPTER_AUTHORIZED"
        decision = "EXPOSE_EFFECTIVE_LAND_MASK_AS_COAST_STATE_LAND_MASK"
    else:
        status = "BLOCKED_R517_B6_D2C1_SHORELINE_LAND_MASK_ADAPTER_NOT_ADJUDICATED"
        decision = "DO_NOT_RECONSTRUCT_SEASONAL_BASELINE_UNTIL_LAND_MASK_SEMANTICS_RESOLVED"

    result = {
        "schema": "ARCANA_R5_17_B6_D2C1_SHORELINE_LAND_MASK_ADAPTER_ADJUDICATION_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2C1",
        "purpose": "Resolve the sole D2C shoreline interface mismatch without fabricating geometry by adjudicating whether the authenticated I-era effective_land_mask is the canonical land-mask semantic required by build_seasonal_climate.",
        "search_root": str(root),
        "target_shoreline_sha256": TARGET_SHORELINE_SHA256,
        "target_generator_sha256": TARGET_GENERATOR_SHA256,
        "target_paleoclimate_sha256": PALEOCLIMATE_SHA256,
        "exact_shoreline_recovered": exact_shoreline,
        "exact_generator_recovered": exact_generator,
        "exact_paleoclimate_consumer_recovered": exact_paleo,
        "shoreline": shoreline,
        "generator_hits": generator_hits,
        "paleoclimate_hits": paleo_hits,
        "historical_alias_reference_count": len(historical_refs),
        "historical_alias_references": historical_refs[:40],
        "effective_land_mask_present": has_effective,
        "elevation_m_present": has_elevation,
        "raw_land_mask_absent": no_raw_land,
        "effective_land_mask_complements_ocean_mask": coherent_partition,
        "paleoclimate_consumer_uses_effective_land_mask": paleo_consumes_effective,
        "explicit_historical_alias_assignment_found": explicit_alias,
        "adapter_mapping": {"land_mask": "effective_land_mask", "elevation_m": "elevation_m"} if adapter_authorized else None,
        "adapter_authorized": adapter_authorized,
        "adapter_semantics": "Interface-only mapping over the authenticated shoreline payload; no cells or physical values are created or changed." if adapter_authorized else None,
        "decision": decision,
        "historical_source_executed": False,
        "reconstructed_baseline_materialized": False,
        "freshwater_support_materialized": False,
        "external_provider_authorized": False,
        "canonical_mutation": False,
        "status": status,
        "next_if_pass": "R5.17-B6-D2D_VALIDATE_SEASONAL_GENERATOR_ON_F_FIXTURE_THEN_RECONSTRUCT_I_BASELINE",
    }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "decision": decision,
        "exact_shoreline_recovered": exact_shoreline,
        "exact_generator_recovered": exact_generator,
        "exact_paleoclimate_consumer_recovered": exact_paleo,
        "effective_land_mask_present": has_effective,
        "raw_land_mask_absent": no_raw_land,
        "effective_land_mask_complements_ocean_mask": coherent_partition,
        "paleoclimate_consumer_uses_effective_land_mask": paleo_consumes_effective,
        "explicit_historical_alias_assignment_found": explicit_alias,
        "historical_alias_reference_count": len(historical_refs),
        "adapter_authorized": adapter_authorized,
        "output": str(args.output.resolve()),
    }, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
