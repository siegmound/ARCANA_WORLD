from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

TARGET_GENERATOR_SUFFIX = "src/arcana_worldsim/finalization/seasonal.py"
TARGET_GENERATOR_SHA256 = "3ec12145617ae63e6ce9d9bd123c159525f83925f9257f1138f3490bb3e70de2"
TARGET_FUNCTION = "build_seasonal_climate"
TARGET_I_SHORELINE_NAME = "shoreline_state_I.npz"
TARGET_I_SHORELINE_SHA256 = "f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85"

KNOWN_F_BASELINES = {
    "physical_finalization": "347f07b9ff16f5c097319898c0b33b86851fc66775b9243ce0f98dce279b954f",
    "margin_morphogenesis": "1b32d97a0b4dad12f01f4c286461d6ca597c2d46a390a8801771735d972d93f6",
}

MAX_TEXT_BYTES = 4 * 1024 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def locate_exact_file(root: Path, suffix: str, expected_sha256: str) -> list[Path]:
    out: list[Path] = []
    basename = Path(suffix).name
    for p in root.rglob(basename):
        if not p.is_file() or ".git" in p.parts:
            continue
        if not norm(p).lower().endswith(suffix.lower()):
            continue
        try:
            if sha256_file(p) == expected_sha256:
                out.append(p.resolve())
        except OSError:
            continue
    return sorted(out, key=lambda p: (len(str(p)), norm(p).lower()))


def locate_hash(root: Path, expected_sha256: str, suffix: str = ".npz") -> list[Path]:
    out: list[Path] = []
    for p in root.rglob(f"*{suffix}"):
        if not p.is_file() or ".git" in p.parts:
            continue
        try:
            if sha256_file(p) == expected_sha256:
                out.append(p.resolve())
        except OSError:
            continue
    return sorted(out, key=lambda p: norm(p).lower())


def locate_named_hash(root: Path, name: str, expected_sha256: str) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob(name):
        if not p.is_file() or ".git" in p.parts:
            continue
        try:
            if sha256_file(p) == expected_sha256:
                out.append(p.resolve())
        except OSError:
            continue
    return sorted(out, key=lambda p: norm(p).lower())


def inspect_npz(path: Path) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }
    with np.load(path, allow_pickle=False) as z:
        rec["keys"] = sorted(z.files)
        rec["key_count"] = len(z.files)
        arrays: dict[str, Any] = {}
        for key in z.files:
            a = np.asarray(z[key])
            item: dict[str, Any] = {"shape": list(a.shape), "dtype": str(a.dtype)}
            if a.dtype.kind in "biufc":
                finite = np.isfinite(a)
                item["finite_count"] = int(finite.sum())
                item["total_count"] = int(a.size)
                if np.any(finite):
                    vals = a[finite].astype(np.float64, copy=False)
                    item["min"] = float(np.min(vals))
                    item["max"] = float(np.max(vals))
                    item["mean"] = float(np.mean(vals))
            arrays[key] = item
        rec["arrays"] = arrays
    return rec


def function_contract(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)
    lines = text.splitlines()

    target: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == TARGET_FUNCTION:
            target = node
            break
    if target is None:
        return {"found": False, "error": f"{TARGET_FUNCTION}_not_found"}

    args = [a.arg for a in target.args.posonlyargs + target.args.args + target.args.kwonlyargs]
    arg_attrs: dict[str, set[str]] = {a: set() for a in args}
    string_literals: set[str] = set()
    called_names: set[str] = set()
    called_attrs: set[str] = set()

    for node in ast.walk(target):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in arg_attrs:
                arg_attrs[node.value.id].add(node.attr)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.add(node.value)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                try:
                    called_attrs.add(ast.unparse(node.func))
                except Exception:
                    pass

    start = target.lineno
    end = getattr(target, "end_lineno", target.lineno)
    body_lines = lines[start - 1:end]
    relevant = []
    for i, line in enumerate(body_lines, start=start):
        ll = line.lower()
        if any(term in ll for term in (
            "temperature", "precip", "pet", "season", "lat", "lon", "elevation",
            "land", "ocean", "coast", "solar", "orbit", "month", "np.load", "np.savez"
        )):
            relevant.append({"line": i, "text": line[:1500]})

    imports = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            try:
                imports.append(ast.unparse(node))
            except Exception:
                pass

    helper_defs: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in called_names:
            helper_defs[node.name] = {
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno),
                "signature": lines[node.lineno - 1].strip(),
            }

    return {
        "found": True,
        "function": TARGET_FUNCTION,
        "line_start": start,
        "line_end": end,
        "signature": lines[start - 1].strip(),
        "arguments": args,
        "argument_attribute_usage": {k: sorted(v) for k, v in arg_attrs.items()},
        "string_literals": sorted(string_literals),
        "called_names": sorted(called_names),
        "called_attributes": sorted(called_attrs),
        "local_helper_definitions": helper_defs,
        "module_imports": imports,
        "relevant_lines": relevant[:160],
    }


def source_dependency_candidates(generator: Path, contract: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    names = set(contract.get("called_names", []))
    records: list[dict[str, Any]] = []
    parent = generator.parent
    for p in root.rglob("*.py"):
        if ".git" in p.parts:
            continue
        try:
            if p.stat().st_size > MAX_TEXT_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matched = sorted(n for n in names if re.search(rf"\bdef\s+{re.escape(n)}\s*\(", text))
        if not matched:
            continue
        records.append({
            "path": str(p.resolve()),
            "sha256": sha256_file(p),
            "defined_called_names": matched,
            "same_module_directory": p.parent == parent,
        })
    return records


def shoreline_contract_satisfied(contract: dict[str, Any], shoreline: dict[str, Any]) -> dict[str, Any]:
    attrs = set(contract.get("argument_attribute_usage", {}).get("coast_state", []))
    if not attrs:
        # Some historical versions may call the second argument "margin".
        for key, vals in contract.get("argument_attribute_usage", {}).items():
            if key not in {"project_root"}:
                attrs.update(vals)
    keys = set(shoreline.get("keys", []))
    missing = sorted(a for a in attrs if a not in keys)
    return {
        "required_coast_attributes": sorted(attrs),
        "shoreline_keys": sorted(keys),
        "missing_attributes": missing,
        "contract_satisfied_by_npz_keys": not missing,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="R5.17-B6-D2C: prepare deterministic reconstruction of the lost v0.5.5I seasonal-climate baseline from the recovered canonical ARCANA generator and authenticated I-era shoreline input. No historical source is executed.")
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("R5_17_B6_D2C_CANONICAL_SEASONAL_BASELINE_RECONSTRUCTION_PREFLIGHT.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    generators = locate_exact_file(root, TARGET_GENERATOR_SUFFIX, TARGET_GENERATOR_SHA256)
    generator = generators[0] if generators else None
    contract = function_contract(generator) if generator else {"found": False, "error": "exact_seasonal_generator_not_found"}

    shorelines = locate_named_hash(root, TARGET_I_SHORELINE_NAME, TARGET_I_SHORELINE_SHA256)
    shoreline_records = [inspect_npz(p) for p in shorelines]
    shoreline_binding = shoreline_contract_satisfied(contract, shoreline_records[0]) if shoreline_records else {
        "required_coast_attributes": [],
        "shoreline_keys": [],
        "missing_attributes": [],
        "contract_satisfied_by_npz_keys": False,
    }

    known_f = {
        name: [str(p) for p in locate_hash(root, h)]
        for name, h in KNOWN_F_BASELINES.items()
    }
    dependencies = source_dependency_candidates(generator, contract, root) if generator and contract.get("found") else []

    exact_generator_recovered = bool(generator)
    exact_i_shoreline_recovered = bool(shorelines)
    generator_contract_recovered = bool(contract.get("found"))
    shoreline_contract_ready = bool(shoreline_binding.get("contract_satisfied_by_npz_keys"))
    validation_fixture_available = any(bool(v) for v in known_f.values())

    reconstruction_preflight_ready = bool(
        exact_generator_recovered
        and exact_i_shoreline_recovered
        and generator_contract_recovered
        and shoreline_contract_ready
        and validation_fixture_available
    )

    if reconstruction_preflight_ready:
        status = "PASS_R517_B6_D2C_CANONICAL_SEASONAL_BASELINE_RECONSTRUCTION_PREFLIGHT_READY"
        decision = "AUTHORIZE_DETERMINISTIC_RECONSTRUCTION_VALIDATION_DESIGN"
    else:
        status = "BLOCKED_R517_B6_D2C_CANONICAL_SEASONAL_BASELINE_RECONSTRUCTION_PREFLIGHT_INCOMPLETE"
        decision = "RESOLVE_RECONSTRUCTION_INPUT_OR_CONTRACT_GAPS"

    result = {
        "schema": "ARCANA_R5_17_B6_D2C_CANONICAL_SEASONAL_BASELINE_RECONSTRUCTION_PREFLIGHT_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2C",
        "purpose": "Prepare a governed reconstruction of the lost v0.5.5I seasonal climate baseline from the recovered canonical ARCANA seasonal generator and authenticated I-era shoreline authority, while preserving the historical provenance gap and validating replay against surviving F-era fixtures before any I-era replay.",
        "search_root": str(root),
        "historical_provenance_gap": "Exact historical identity of seasonal_climate_state_I.npz is unrecoverable from surviving promotion/seal evidence; reconstruction must be labeled reconstructed, not recovered.",
        "target_generator_suffix": TARGET_GENERATOR_SUFFIX,
        "target_generator_sha256": TARGET_GENERATOR_SHA256,
        "generator_candidate_count": len(generators),
        "generator_candidates": [str(p) for p in generators],
        "exact_generator_recovered": exact_generator_recovered,
        "generator_contract": contract,
        "source_dependency_candidates": dependencies,
        "target_i_shoreline_name": TARGET_I_SHORELINE_NAME,
        "target_i_shoreline_sha256": TARGET_I_SHORELINE_SHA256,
        "i_shoreline_candidate_count": len(shorelines),
        "i_shoreline_candidates": shoreline_records,
        "exact_i_shoreline_recovered": exact_i_shoreline_recovered,
        "shoreline_contract_binding": shoreline_binding,
        "known_f_baseline_hashes": KNOWN_F_BASELINES,
        "known_f_baseline_locations": known_f,
        "validation_fixture_available": validation_fixture_available,
        "reconstruction_preflight_ready": reconstruction_preflight_ready,
        "decision": decision,
        "historical_source_executed": False,
        "reconstructed_baseline_materialized": False,
        "freshwater_support_materialized": False,
        "external_provider_authorized": False,
        "canonical_mutation": False,
        "status": status,
        "next_if_ready": "R5.17-B6-D2D_VALIDATE_CANONICAL_SEASONAL_GENERATOR_REPLAY_THEN_RECONSTRUCT_I_BASELINE",
    }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "decision": decision,
        "generator_candidate_count": len(generators),
        "exact_generator_recovered": exact_generator_recovered,
        "generator_contract_recovered": generator_contract_recovered,
        "i_shoreline_candidate_count": len(shorelines),
        "exact_i_shoreline_recovered": exact_i_shoreline_recovered,
        "shoreline_contract_ready": shoreline_contract_ready,
        "validation_fixture_available": validation_fixture_available,
        "reconstruction_preflight_ready": reconstruction_preflight_ready,
        "output": str(args.output.resolve()),
    }, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
