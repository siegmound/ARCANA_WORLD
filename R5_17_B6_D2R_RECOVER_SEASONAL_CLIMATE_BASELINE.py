from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

TARGET_EXACT_NAME = "seasonal_climate_state_I.npz"
ALT_NAME_PATTERNS = (
    re.compile(r"seasonal.*climate.*\.npz$", re.IGNORECASE),
    re.compile(r"climate.*seasonal.*\.npz$", re.IGNORECASE),
    re.compile(r"seasonal_climate_state\.npz$", re.IGNORECASE),
)
FINALIZATION_SUFFIX = "src/arcana_worldsim/finalization/hydrology.py"
FINALIZATION_SHA256 = "29c808bd889d3f0c6e5390775d8751f68b9c9dd2cb5bab1736d6ad6cc6486351"
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".ps1", ".yaml", ".yml", ".toml"}
MAX_TEXT_BYTES = 4 * 1024 * 1024
MAX_NPZ_BYTES = 1024 * 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(path: Path) -> str:
    return str(path).replace("\\", "/")


def locate_exact_finalization(root: Path) -> Path | None:
    matches: list[Path] = []
    for path in root.rglob("hydrology.py"):
        if ".git" in path.parts:
            continue
        if not norm(path).lower().endswith(FINALIZATION_SUFFIX.lower()):
            continue
        try:
            if sha256_file(path) == FINALIZATION_SHA256:
                matches.append(path.resolve())
        except OSError:
            continue
    if not matches:
        return None
    return sorted(matches, key=lambda p: (len(str(p)), str(p).lower()))[0]


def extract_seasonal_contract(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text)
    target: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "build_channel_hydrology":
            target = node
            break
    if target is None:
        return {"found": False, "error": "build_channel_hydrology_not_found"}

    seasonal_attrs: set[str] = set()
    seasonal_keys: set[str] = set()
    string_literals: set[str] = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "seasonal":
            seasonal_attrs.add(node.attr)
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "seasonal":
            sl = node.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                seasonal_keys.add(sl.value)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.add(node.value)

    lines = text.splitlines()
    start = target.lineno
    end = getattr(target, "end_lineno", target.lineno)
    excerpts: list[dict[str, Any]] = []
    for i in range(start - 1, end):
        line = lines[i]
        ll = line.lower()
        if "seasonal" in ll or any(k.lower() in ll for k in seasonal_attrs | seasonal_keys):
            excerpts.append({"line": i + 1, "text": line[:1200]})

    return {
        "found": True,
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "seasonal_attribute_requirements": sorted(seasonal_attrs),
        "seasonal_indexed_key_requirements": sorted(seasonal_keys),
        "string_literals": sorted(string_literals),
        "seasonal_excerpts": excerpts[:120],
    }


def name_is_candidate(name: str) -> bool:
    base = Path(name).name
    if base.lower() == TARGET_EXACT_NAME.lower():
        return True
    return any(p.search(base) for p in ALT_NAME_PATTERNS)


def inspect_npz_bytes(data: bytes) -> dict[str, Any]:
    try:
        import numpy as np
        with np.load(io.BytesIO(data), allow_pickle=False) as z:
            arrays: dict[str, Any] = {}
            for key in z.files:
                a = z[key]
                arrays[key] = {
                    "shape": list(a.shape),
                    "dtype": str(a.dtype),
                }
            return {
                "ok": True,
                "keys": sorted(z.files),
                "key_count": len(z.files),
                "arrays": arrays,
            }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def inspect_npz_file(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_NPZ_BYTES:
            return {"ok": False, "inspection_skipped": "file_too_large"}
        data = path.read_bytes()
        return inspect_npz_bytes(data)
    except OSError as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def direct_candidates(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in root.rglob("*.npz"):
        if ".git" in path.parts or not name_is_candidate(path.name):
            continue
        try:
            rec = {
                "source_class": "direct",
                "path": str(path.resolve()),
                "basename": path.name,
                "exact_target_name": path.name.lower() == TARGET_EXACT_NAME.lower(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "npz": inspect_npz_file(path),
            }
            out.append(rec)
        except OSError:
            continue
    return out


def zip_candidates(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for archive in root.rglob("*.zip"):
        if ".git" in archive.parts:
            continue
        try:
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    if not name_is_candidate(info.filename):
                        continue
                    rec: dict[str, Any] = {
                        "source_class": "zip",
                        "archive": str(archive.resolve()),
                        "member": info.filename,
                        "basename": Path(info.filename).name,
                        "exact_target_name": Path(info.filename).name.lower() == TARGET_EXACT_NAME.lower(),
                        "size_bytes": info.file_size,
                    }
                    if info.file_size <= MAX_NPZ_BYTES:
                        with zf.open(info, "r") as stream:
                            data = stream.read()
                        rec["sha256"] = sha256_bytes(data)
                        rec["npz"] = inspect_npz_bytes(data)
                    else:
                        rec["npz"] = {"ok": False, "inspection_skipped": "member_too_large"}
                    out.append(rec)
        except (zipfile.BadZipFile, OSError):
            continue
    return out


def text_references(root: Path, required_terms: set[str]) -> list[dict[str, Any]]:
    needles = {
        TARGET_EXACT_NAME.lower(),
        "seasonal_climate_state".lower(),
        "seasonal climate",
        "build_channel_hydrology",
        *{t.lower() for t in required_terms},
    }
    out: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_TEXT_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits = []
        for i, line in enumerate(text.splitlines(), start=1):
            ll = line.lower()
            matched = sorted(n for n in needles if n in ll)
            if matched:
                hits.append({"line": i, "terms": matched, "text": line[:1200]})
                if len(hits) >= 100:
                    break
        if hits:
            out.append({"path": str(path.resolve()), "sha256": sha256_file(path), "hits": hits})
    return out


def zip_text_references(root: Path, required_terms: set[str]) -> list[dict[str, Any]]:
    needles = {
        TARGET_EXACT_NAME.lower(),
        "seasonal_climate_state".lower(),
        "build_channel_hydrology",
        *{t.lower() for t in required_terms},
    }
    out: list[dict[str, Any]] = []
    for archive in root.rglob("*.zip"):
        if ".git" in archive.parts:
            continue
        try:
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    suffix = Path(info.filename).suffix.lower()
                    if suffix not in TEXT_SUFFIXES or info.file_size > MAX_TEXT_BYTES:
                        continue
                    name_lower = info.filename.lower()
                    if not ("climate" in name_lower or "hydro" in name_lower or "manifest" in name_lower or "seal" in name_lower):
                        continue
                    with zf.open(info, "r") as stream:
                        text = stream.read().decode("utf-8", errors="replace")
                    hits = []
                    for i, line in enumerate(text.splitlines(), start=1):
                        ll = line.lower()
                        matched = sorted(n for n in needles if n in ll)
                        if matched:
                            hits.append({"line": i, "terms": matched, "text": line[:1200]})
                            if len(hits) >= 100:
                                break
                    if hits:
                        out.append({
                            "archive": str(archive.resolve()),
                            "member": info.filename,
                            "sha256": sha256_bytes(text.encode("utf-8")),
                            "hits": hits,
                        })
        except (zipfile.BadZipFile, OSError):
            continue
    return out


def candidate_satisfies(rec: dict[str, Any], required: set[str]) -> bool:
    npz = rec.get("npz", {})
    keys = set(npz.get("keys", [])) if npz.get("ok") else set()
    return bool(required) and required.issubset(keys)


def main() -> None:
    ap = argparse.ArgumentParser(description="R5.17-B6-D2R: recover the missing canonical seasonal climate baseline or a governed schema-compatible lineage before paleohydrology replay.")
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("R5_17_B6_D2R_SEASONAL_CLIMATE_BASELINE_RECOVERY.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    finalization = locate_exact_finalization(root)
    contract = extract_seasonal_contract(finalization) if finalization else {
        "found": False,
        "error": "exact_finalization_hydrology_source_not_found",
    }
    required = set(contract.get("seasonal_indexed_key_requirements", [])) | set(contract.get("seasonal_attribute_requirements", []))

    direct = direct_candidates(root)
    zipped = zip_candidates(root)
    candidates = [*direct, *zipped]
    exact = [c for c in candidates if c.get("exact_target_name")]
    compatible = [c for c in candidates if candidate_satisfies(c, required)]
    refs = text_references(root, required)
    zip_refs = zip_text_references(root, required)

    exact_schema_compatible = [c for c in exact if candidate_satisfies(c, required)]
    alternate_schema_compatible = [c for c in compatible if not c.get("exact_target_name")]

    if exact_schema_compatible:
        status = "PASS_R517_B6_D2R_EXACT_SEASONAL_CLIMATE_BASELINE_RECOVERED"
        decision = "BIND_EXACT_RECOVERED_BASELINE"
        replay_ready = True
    elif alternate_schema_compatible:
        status = "PASS_R517_B6_D2R_SCHEMA_COMPATIBLE_SEASONAL_CLIMATE_CANDIDATE_RECOVERED_IDENTITY_PENDING"
        decision = "ADJUDICATE_ALTERNATE_BASELINE_IDENTITY_BEFORE_REPLAY"
        replay_ready = False
    elif contract.get("found") and (refs or zip_refs):
        status = "PASS_R517_B6_D2R_BASELINE_GENERATOR_OR_REFERENCE_LINEAGE_RECOVERED_PAYLOAD_ABSENT"
        decision = "DESIGN_CANONICAL_BASELINE_RECONSTRUCTION"
        replay_ready = False
    else:
        status = "BLOCKED_R517_B6_D2R_SEASONAL_CLIMATE_BASELINE_AND_LINEAGE_NOT_RECOVERED"
        decision = "TARGETED_CLIMATE_BASELINE_PROVENANCE_GAP"
        replay_ready = False

    result = {
        "schema": "ARCANA_R5_17_B6_D2R_SEASONAL_CLIMATE_BASELINE_RECOVERY_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2R",
        "purpose": "Resolve the sole D2 replay-input gap by recovering the exact seasonal climate baseline, a schema-compatible governed candidate, or its generator/reference lineage without executing historical simulation.",
        "search_root": str(root),
        "target_exact_name": TARGET_EXACT_NAME,
        "exact_finalization_source": str(finalization) if finalization else None,
        "seasonal_contract": contract,
        "required_seasonal_fields": sorted(required),
        "direct_candidate_count": len(direct),
        "zip_candidate_count": len(zipped),
        "exact_name_candidate_count": len(exact),
        "exact_schema_compatible_candidate_count": len(exact_schema_compatible),
        "alternate_schema_compatible_candidate_count": len(alternate_schema_compatible),
        "direct_candidates": direct,
        "zip_candidates": zipped,
        "exact_schema_compatible_candidates": exact_schema_compatible,
        "alternate_schema_compatible_candidates": alternate_schema_compatible,
        "text_reference_file_count": len(refs),
        "zip_text_reference_count": len(zip_refs),
        "text_references": refs,
        "zip_text_references": zip_refs,
        "decision": decision,
        "replay_execution_ready_from_d2r": replay_ready,
        "historical_source_executed": False,
        "external_provider_authorized": False,
        "freshwater_support_materialized": False,
        "canonical_mutation": False,
        "status": status,
        "next_if_exact": "R5.17-B6-D3_CANONICAL_PALEOHYDROLOGY_REPLAY_IMPLEMENTATION",
        "next_if_alternate": "R5.17-B6-D2A_ALTERNATE_SEASONAL_BASELINE_IDENTITY_ADJUDICATION",
        "next_if_lineage_only": "R5.17-B6-D2B_CANONICAL_SEASONAL_BASELINE_RECONSTRUCTION_DESIGN",
    }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "decision": decision,
        "required_seasonal_fields": sorted(required),
        "direct_candidate_count": len(direct),
        "zip_candidate_count": len(zipped),
        "exact_name_candidate_count": len(exact),
        "exact_schema_compatible_candidate_count": len(exact_schema_compatible),
        "alternate_schema_compatible_candidate_count": len(alternate_schema_compatible),
        "text_reference_file_count": len(refs),
        "zip_text_reference_count": len(zip_refs),
        "replay_execution_ready_from_d2r": replay_ready,
        "output": str(args.output.resolve()),
    }, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
