from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

EXPECTED_SOURCE_HASHES = {
    "src/arcana_worldsim/surface/hydrology.py": "34584d0e8a8696b26e4026aad28f362850b7e9b98bb7754cc5cab8e4d282ff42",
    "src/arcana_worldsim/regional/hydrology.py": "e32d766e3e700dd2da22adda3c09b0327e503d1ab9df663eb1c23e6730832b87",
    "src/arcana_worldsim/climate/water_balance.py": "23090416ef8234d43689171241d80d8ca2609882455bd30761de30301e5bfb61",
    "src/arcana_worldsim/finalization/hydrology.py": "29c808bd889d3f0c6e5390775d8751f68b9c9dd2cb5bab1736d6ad6cc6486351",
}

PALEO_SNAPSHOT_NAME = "paleoclimate_spatial_snapshots.npz"
PALEO_SNAPSHOT_SHA256 = "a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd"
SHORELINE_NAME = "shoreline_state_I.npz"
SHORELINE_SHA256 = "f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85"
SEASONAL_CLIMATE_NAME = "seasonal_climate_state_I.npz"

TARGET_FUNCTIONS = {
    "src/arcana_worldsim/climate/water_balance.py": "build_climatic_hydrology",
    "src/arcana_worldsim/finalization/hydrology.py": "build_channel_hydrology",
}

MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_CANDIDATES_PER_NAME = 80


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(path: Path) -> str:
    return str(path).replace("\\", "/")


def locate_exact_sources(root: Path) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {k: [] for k in EXPECTED_SOURCE_HASHES}
    for path in root.rglob("*.py"):
        if ".git" in path.parts:
            continue
        np = norm(path).lower()
        for suffix, expected in EXPECTED_SOURCE_HASHES.items():
            if np.endswith(suffix.lower()):
                try:
                    if sha256_file(path) == expected:
                        found[suffix].append(path.resolve())
                except OSError:
                    pass
    return found


def function_contract(path: Path, function_name: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)
    lines = text.splitlines()
    target: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            target = node
            break
    if target is None:
        return {"function": function_name, "found": False}

    args = [a.arg for a in target.args.posonlyargs + target.args.args + target.args.kwonlyargs]
    if target.args.vararg:
        args.append("*" + target.args.vararg.arg)
    if target.args.kwarg:
        args.append("**" + target.args.kwarg.arg)

    attr_usage: dict[str, set[str]] = {a.lstrip("*"): set() for a in args}
    npz_literals: set[str] = set()
    string_literals: set[str] = set()

    for node in ast.walk(target):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            base = node.value.id
            if base in attr_usage:
                attr_usage[base].add(node.attr)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            string_literals.add(value)
            if value.lower().endswith(".npz"):
                npz_literals.add(value)

    start = target.lineno
    end = getattr(target, "end_lineno", target.lineno)
    body = "\n".join(lines[start - 1:end])
    indexed_keys = sorted(set(re.findall(r"\[\s*[\"']([^\"']+)[\"']\s*\]", body)))
    path_fragments = sorted(set(re.findall(r"[\"']([^\"']*(?:inputs|outputs)[^\"']*)[\"']", body, flags=re.IGNORECASE)))

    return {
        "function": function_name,
        "found": True,
        "line_start": start,
        "line_end": end,
        "signature": lines[start - 1].strip(),
        "arguments": args,
        "argument_attribute_usage": {k: sorted(v) for k, v in attr_usage.items()},
        "indexed_keys": indexed_keys,
        "npz_literals": sorted(npz_literals),
        "path_fragments": path_fragments,
        "relevant_equation_lines": [
            {"line": i, "text": line.strip()[:1200]}
            for i, line in enumerate(lines[start - 1:end], start=start)
            if any(term in line.lower() for term in (
                "precip", "pet", "aet", "evap", "infil", "groundwater", "storage",
                "cryo", "runoff", "route", "discharge", "31557600", "365.25",
            ))
        ][:120],
    }


def discover_named_files(root: Path, name: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in root.rglob(name):
        if ".git" in path.parts or not path.is_file():
            continue
        try:
            out.append({
                "path": str(path.resolve()),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            })
        except OSError:
            continue
        if len(out) >= MAX_CANDIDATES_PER_NAME:
            break
    return out


def inspect_npz_keys(path: Path) -> dict[str, Any]:
    try:
        import numpy as np
        with np.load(path, allow_pickle=False) as z:
            return {"ok": True, "keys": sorted(z.files), "key_count": len(z.files)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def enrich_npz(records: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for item in records:
        rec = dict(item)
        if len(enriched) < limit:
            rec["npz"] = inspect_npz_keys(Path(item["path"]))
        else:
            rec["npz"] = {"ok": False, "inspection_skipped": "candidate_limit"}
        enriched.append(rec)
    return enriched


def main() -> None:
    ap = argparse.ArgumentParser(description="R5.17-B6-D2: bind exact canonical hydrology callable requirements to locally materialized paleoclimate/baseline inputs before executing any replay.")
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("R5_17_B6_D2_CANONICAL_PALEOHYDROLOGY_INPUT_BINDING.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    located = locate_exact_sources(root)
    representatives = {
        suffix: sorted(paths, key=lambda p: (len(str(p)), str(p).lower()))[0]
        for suffix, paths in located.items() if paths
    }
    exact_sources_complete = len(representatives) == len(EXPECTED_SOURCE_HASHES)

    contracts: dict[str, Any] = {}
    for suffix, function_name in TARGET_FUNCTIONS.items():
        path = representatives.get(suffix)
        contracts[suffix] = function_contract(path, function_name) if path else {
            "function": function_name,
            "found": False,
            "error": "exact_source_not_found",
        }

    paleo = enrich_npz(discover_named_files(root, PALEO_SNAPSHOT_NAME))
    shoreline = enrich_npz(discover_named_files(root, SHORELINE_NAME))
    seasonal = enrich_npz(discover_named_files(root, SEASONAL_CLIMATE_NAME))

    exact_paleo = [x for x in paleo if x.get("sha256") == PALEO_SNAPSHOT_SHA256]
    exact_shoreline = [x for x in shoreline if x.get("sha256") == SHORELINE_SHA256]

    all_contracts_found = all(c.get("found") for c in contracts.values())
    baseline_seasonal_found = bool(seasonal)
    exact_paleo_found = bool(exact_paleo)
    exact_shoreline_found = bool(exact_shoreline)

    replay_execution_ready = bool(
        exact_sources_complete
        and all_contracts_found
        and exact_paleo_found
        and exact_shoreline_found
        and baseline_seasonal_found
    )

    unresolved: list[str] = []
    if not exact_sources_complete:
        unresolved.append("exact_canonical_generator_sources")
    if not all_contracts_found:
        unresolved.append("canonical_callable_contracts")
    if not exact_paleo_found:
        unresolved.append("exact_paleoclimate_spatial_snapshots")
    if not exact_shoreline_found:
        unresolved.append("exact_book_era_shoreline")
    if not baseline_seasonal_found:
        unresolved.append("seasonal_climate_state_I_baseline")

    evidence_captured = bool(exact_sources_complete and all_contracts_found and exact_paleo_found)
    status = (
        "PASS_R517_B6_D2_CANONICAL_PALEOHYDROLOGY_INPUT_BINDING_READY"
        if replay_execution_ready else
        "PASS_R517_B6_D2_INPUT_BINDING_EVIDENCE_CAPTURED_WITH_UNRESOLVED_INPUTS"
        if evidence_captured else
        "BLOCKED_R517_B6_D2_CANONICAL_PALEOHYDROLOGY_INPUT_BINDING_INCOMPLETE"
    )

    result = {
        "schema": "ARCANA_R5_17_B6_D2_CANONICAL_PALEOHYDROLOGY_INPUT_BINDING_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2",
        "purpose": "Bind the adjudicated canonical ARCANA hydrology callable contract to exact paleoclimate and locally materialized baseline input payloads before any time-varying hydrology replay is executed.",
        "search_root": str(root),
        "expected_source_hashes": EXPECTED_SOURCE_HASHES,
        "source_candidate_counts": {k: len(v) for k, v in located.items()},
        "representative_source_paths": {k: str(v) for k, v in representatives.items()},
        "exact_sources_complete": exact_sources_complete,
        "callable_contracts": contracts,
        "paleoclimate_spatial_snapshot_candidates": paleo,
        "exact_paleoclimate_snapshot_sha256": PALEO_SNAPSHOT_SHA256,
        "exact_paleoclimate_snapshot_found": exact_paleo_found,
        "shoreline_candidates": shoreline,
        "exact_book_era_shoreline_sha256": SHORELINE_SHA256,
        "exact_book_era_shoreline_found": exact_shoreline_found,
        "seasonal_climate_candidates": seasonal,
        "seasonal_climate_baseline_found": baseline_seasonal_found,
        "replay_execution_ready": replay_execution_ready,
        "unresolved_inputs": unresolved,
        "reuse_canonical_arcana": True,
        "external_provider_authorized": False,
        "historical_source_executed": False,
        "freshwater_support_materialized": False,
        "canonical_mutation": False,
        "status": status,
        "next_if_ready": "R5.17-B6-D3_CANONICAL_PALEOHYDROLOGY_REPLAY_IMPLEMENTATION",
        "next_if_unresolved": "R5.17-B6-D2R_RESOLVE_EXACT_BASELINE_INPUT_BINDINGS",
    }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "exact_sources_complete": exact_sources_complete,
        "all_callable_contracts_found": all_contracts_found,
        "exact_paleoclimate_snapshot_found": exact_paleo_found,
        "exact_book_era_shoreline_found": exact_shoreline_found,
        "seasonal_climate_baseline_found": baseline_seasonal_found,
        "seasonal_climate_candidate_count": len(seasonal),
        "replay_execution_ready": replay_execution_ready,
        "unresolved_inputs": unresolved,
        "output": str(args.output.resolve()),
    }, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
