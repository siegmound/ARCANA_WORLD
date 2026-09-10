from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

TARGET_SEAL = "AUTHORIAL_SEAL_v0_6_1.json"
TARGET_SEAL_SHA256 = "d097f83ce53fb298689c63458dfa1012d26b3983254ccf25085b91f882e55a2a"
TARGET_PAYLOAD = "channel_hydrology_state_I.npz"
TERMS = (
    "channel_hydrology_state_I",
    "mean_discharge_m3_s",
    "drainage_area_km2",
    "receiver_flat",
    "lake_candidate_mask",
    "depression_depth_m",
    "v0_5_5I_SEALED",
)
TEXT_SUFFIXES = {".json", ".md", ".py", ".ps1", ".txt", ".yaml", ".yml", ".toml"}
MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_HITS_PER_FILE = 80


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text_hits(text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        lower = line.lower()
        matched = [term for term in TERMS if term.lower() in lower]
        if matched:
            hits.append({"line": i, "terms": matched, "text": line[:1000]})
            if len(hits) >= MAX_HITS_PER_FILE:
                break
    return hits


def json_semantic_hits(obj: Any, path: str = "$") -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_path = f"{path}.{key}"
            key_lower = str(key).lower()
            matched = [term for term in TERMS if term.lower() in key_lower]
            if matched:
                hits.append({"json_path": key_path, "terms": matched, "value_preview": str(value)[:1000]})
            hits.extend(json_semantic_hits(value, key_path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(json_semantic_hits(value, f"{path}[{idx}]"))
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        value_text = str(obj)
        lower = value_text.lower()
        matched = [term for term in TERMS if term.lower() in lower]
        if matched:
            hits.append({"json_path": path, "terms": matched, "value_preview": value_text[:1000]})
    return hits


def inspect_seal_bytes(data: bytes, location: dict[str, Any]) -> dict[str, Any]:
    record = dict(location)
    record["sha256"] = sha256_bytes(data)
    record["sha256_matches_r314"] = record["sha256"] == TARGET_SEAL_SHA256
    try:
        obj = json.loads(data.decode("utf-8"))
        record["json_parse_ok"] = True
        record["semantic_hits"] = json_semantic_hits(obj)
    except Exception as exc:
        record["json_parse_ok"] = False
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["semantic_hits"] = []
    return record


def locate_seals(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in root.rglob(TARGET_SEAL):
        if ".git" in path.parts:
            continue
        try:
            records.append(inspect_seal_bytes(path.read_bytes(), {"source_class": "direct", "path": str(path.resolve())}))
        except OSError as exc:
            records.append({"source_class": "direct", "path": str(path), "error": f"{type(exc).__name__}: {exc}"})
    for archive in root.rglob("*.zip"):
        if ".git" in archive.parts:
            continue
        try:
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    if Path(info.filename).name != TARGET_SEAL:
                        continue
                    with zf.open(info, "r") as stream:
                        data = stream.read()
                    records.append(inspect_seal_bytes(data, {"source_class": "zip", "archive": str(archive.resolve()), "member": info.filename}))
        except (zipfile.BadZipFile, OSError) as exc:
            records.append({"source_class": "zip", "archive": str(archive.resolve()), "error": f"{type(exc).__name__}: {exc}"})
    return records


def scan_text_files(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_TEXT_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            hits = text_hits(text)
            if hits:
                records.append({"path": str(path.resolve()), "sha256": sha256_file(path), "hits": hits})
        except OSError:
            continue
    return records


def scan_zip_text(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for archive in root.rglob("*.zip"):
        if ".git" in archive.parts:
            continue
        try:
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    member = Path(info.filename)
                    if member.suffix.lower() not in TEXT_SUFFIXES or info.file_size > MAX_TEXT_BYTES:
                        continue
                    lower_name = info.filename.lower()
                    name_relevant = any(term.lower() in lower_name for term in TERMS) or "hydro" in lower_name
                    if not name_relevant and info.file_size > 2 * 1024 * 1024:
                        continue
                    with zf.open(info, "r") as stream:
                        data = stream.read()
                    text = data.decode("utf-8", errors="replace")
                    hits = text_hits(text)
                    if hits:
                        records.append({
                            "archive": str(archive.resolve()),
                            "member": info.filename,
                            "sha256": sha256_bytes(data),
                            "hits": hits,
                        })
        except (zipfile.BadZipFile, OSError):
            continue
    return records


def likely_generator(record: dict[str, Any]) -> bool:
    name = (record.get("path") or record.get("member") or "").replace("\\", "/").lower()
    suffix = Path(name).suffix.lower()
    if suffix not in {".py", ".ps1"}:
        return False
    if "r5_17_b6_" in name:
        return False
    if name.endswith("/src/arcana_worldsim/paleoclimate/model.py"):
        return False
    terms = {t for hit in record.get("hits", []) for t in hit.get("terms", [])}
    physical = {
        "mean_discharge_m3_s",
        "drainage_area_km2",
        "receiver_flat",
        "lake_candidate_mask",
        "depression_depth_m",
    }
    return bool(terms & physical)


def main() -> None:
    parser = argparse.ArgumentParser(description="R5.17-B6-H2: recover v0.6.1/v0.5.5I native hydrology provenance without executing historical code.")
    parser.add_argument("--search-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("R5_17_B6_H2_NATIVE_HYDROLOGY_PROVENANCE.json"))
    args = parser.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    seals = locate_seals(root)
    exact_seals = [x for x in seals if x.get("sha256_matches_r314") is True]
    direct_text = scan_text_files(root)
    zip_text = scan_zip_text(root)
    all_text = [*direct_text, *zip_text]
    generators = [x for x in all_text if likely_generator(x)]
    seal_hits = [hit for seal in exact_seals for hit in seal.get("semantic_hits", [])]

    if exact_seals and (seal_hits or generators):
        status = "PASS_R517_B6_H2_NATIVE_HYDROLOGY_PROVENANCE_EVIDENCE_CAPTURED"
    elif exact_seals:
        status = "BLOCKED_R517_B6_H2_EXACT_V061_SEAL_HAS_NO_RECOVERED_HYDROLOGY_PROVENANCE"
    else:
        status = "BLOCKED_R517_B6_H2_EXACT_V061_SEAL_NOT_FOUND"

    manifest = {
        "schema": "ARCANA_R5_17_B6_H2_NATIVE_HYDROLOGY_PROVENANCE_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-H2",
        "purpose": "Recover documentary provenance and possible generator evidence for the missing v0.5.5I channel hydrology dependency before provider selection.",
        "search_root": str(root),
        "target_payload": TARGET_PAYLOAD,
        "target_seal": TARGET_SEAL,
        "target_seal_sha256": TARGET_SEAL_SHA256,
        "exact_seal_count": len(exact_seals),
        "seal_candidates": seals,
        "exact_seal_hydrology_reference_count": len(seal_hits),
        "exact_seal_hydrology_references": seal_hits,
        "text_reference_file_count": len(all_text),
        "text_references": all_text,
        "generator_candidate_count": len(generators),
        "generator_candidates": generators,
        "payload_materialized": False,
        "payload_authority_identity_adjudicated": False,
        "generator_identity_adjudicated": False,
        "reuse_canonical_arcana_authorized": False,
        "external_provider_authorized": False,
        "freshwater_support_materialized": False,
        "new_historical_simulation": False,
        "source_executed": False,
        "canonical_mutation": False,
        "status": status,
        "next_if_evidence_found": "R5.17-B6-H3_NATIVE_HYDROLOGY_GENERATOR_SEMANTIC_ADJUDICATION",
        "next_if_blocked": "R5.17-B6_SCIENTIFIC_ENGINE_SUITABILITY_ADJUDICATION_WITH_NATIVE_PROVENANCE_GAP_RECORDED",
    }
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "exact_seal_count": len(exact_seals),
        "exact_seal_hydrology_reference_count": len(seal_hits),
        "text_reference_file_count": len(all_text),
        "generator_candidate_count": len(generators),
        "output": str(args.output.resolve()),
    }, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
