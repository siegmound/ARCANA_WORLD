from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

JOB_IDS = {"J14", "J18", "J21"}
MAPPING_CLASSES = ("time", "space", "population", "domain", "uncertainty")
INTEREST_TOKENS = (
    "geonomics", "static_valid", "static_validation", "parameter_manifest",
    "canonical_parameter", "mapping", "j14", "j18", "j21",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonable(v: Any) -> Any:
    if isinstance(v, Path):
        return str(v)
    return v


def walk(obj: Any, loc: str = "$") -> Iterable[tuple[str, Any]]:
    yield loc, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{loc}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{loc}[{i}]")


def flatten_strings(obj: Any) -> list[str]:
    out: list[str] = []
    for _, v in walk(obj):
        if isinstance(v, str):
            out.append(v)
    return out


def infer_job_ids(obj: Any) -> set[str]:
    ids: set[str] = set()
    for _, v in walk(obj):
        if isinstance(v, str):
            up = v.upper()
            for jid in JOB_IDS:
                if up == jid or f"{jid}_" in up or f"_{jid}" in up or f"/{jid}/" in up or f"\\{jid}\\" in up:
                    ids.add(jid)
        elif isinstance(v, dict):
            for key in ("job_id", "job", "id"):
                val = v.get(key)
                if isinstance(val, str) and val.upper() in JOB_IDS:
                    ids.add(val.upper())
    return ids


def direct_job_ids(obj: Any) -> set[str]:
    ids: set[str] = set()
    if not isinstance(obj, dict):
        return ids
    for key in ("job_id", "job", "id"):
        val = obj.get(key)
        if isinstance(val, str) and val.upper() in JOB_IDS:
            ids.add(val.upper())
    return ids


def likely_manifest(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    direct_jobs = direct_job_ids(obj)
    if not direct_jobs:
        return False
    immediate_strings = " ".join(
        v.lower() for v in obj.values() if isinstance(v, str)
    )
    keys = " ".join(str(k).lower() for k in obj.keys())
    # Job identity is mandatory. Geonomics/parameter/manifest evidence may be
    # represented either as scalar fields or structural keys.
    has_geonomics = "geonomics" in immediate_strings or "geonomics" in keys
    has_parameter_shape = "parameter" in immediate_strings or "parameter" in keys or "mapping" in keys
    has_manifest_shape = "manifest" in immediate_strings or "manifest" in keys or "static_valid" in keys or "static_validation" in keys
    return has_geonomics and has_parameter_shape and has_manifest_shape


def mapping_presence(obj: Any) -> dict[str, bool]:
    strings = [s.lower() for s in flatten_strings(obj)]
    keys: list[str] = []
    for _, v in walk(obj):
        if isinstance(v, dict):
            keys.extend(str(k).lower() for k in v.keys())
    hay = strings + keys
    result = {}
    for cls in MAPPING_CLASSES:
        result[cls] = any(
            token == cls
            or token.startswith(cls + "_")
            or token.endswith("_" + cls)
            or ("mapping" in token and cls in token)
            for token in hay
        )
    return result


def collect_static_flags(obj: Any) -> list[dict[str, Any]]:
    flags = []
    for loc, v in walk(obj):
        if isinstance(v, dict):
            for k, value in v.items():
                lk = str(k).lower()
                if "static" in lk and ("valid" in lk or "pass" in lk or "check" in lk):
                    flags.append({"location": f"{loc}.{k}", "value": value})
                elif lk in {"pass", "valid"} and "static" in loc.lower():
                    flags.append({"location": f"{loc}.{k}", "value": value})
    return flags


def expected_hash_for_key(d: dict[str, Any], key: str) -> str | None:
    stem = key[:-5] if key.lower().endswith("_path") else key
    candidates = [
        stem + "_sha256",
        stem + "_hash",
        key.replace("_path", "_sha256"),
        key.replace("path", "sha256"),
    ]
    for cand in candidates:
        val = d.get(cand)
        if isinstance(val, str):
            raw = val.lower().replace("sha256:", "").strip()
            if len(raw) == 64 and all(c in "0123456789abcdef" for c in raw):
                return raw
    return None


def resolve_path(raw: str, root: Path, json_parent: Path) -> tuple[Path | None, list[str]]:
    notes: list[str] = []
    p = Path(raw)
    if p.is_absolute():
        return (p if p.exists() else None), notes
    candidates = [root / p, json_parent / p]
    seen = set()
    unique = []
    for c in candidates:
        c = c.resolve()
        if c not in seen:
            seen.add(c)
            unique.append(c)
    existing = [c for c in unique if c.exists()]
    if len(existing) == 1:
        return existing[0], notes
    if len(existing) > 1:
        notes.append("PATH_RESOLUTION_AMBIGUITY")
        return existing[0], notes
    return None, notes


def inspect_refs(obj: Any, root: Path, json_parent: Path) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for loc, v in walk(obj):
        if not isinstance(v, dict):
            continue
        for k, raw in v.items():
            lk = str(k).lower()
            if not isinstance(raw, str):
                continue
            looks_path = lk.endswith("_path") or lk.endswith("_file") or lk in {"path", "file", "source_path", "artifact_path"}
            if not looks_path:
                continue
            if raw.startswith(("http://", "https://")):
                continue
            resolved, notes = resolve_path(raw, root, json_parent)
            rec: dict[str, Any] = {
                "location": f"{loc}.{k}",
                "raw": raw,
                "exists": resolved is not None,
                "resolved": str(resolved) if resolved else None,
                "notes": notes,
            }
            expected = expected_hash_for_key(v, str(k))
            if expected:
                rec["expected_sha256"] = expected
                if resolved and resolved.is_file():
                    actual = sha256_file(resolved)
                    rec["actual_sha256"] = actual
                    rec["hash_match"] = actual == expected
            refs.append(rec)
    return refs


def discover_jsons(root: Path) -> list[Path]:
    candidates: list[Path] = []
    output_root = root / "outputs"
    search_roots = [output_root] if output_root.exists() else [root]
    for sr in search_roots:
        for p in sr.rglob("*.json"):
            ps = str(p).lower()
            if "r4_32" in ps or "r432" in ps or "geonomics" in ps:
                candidates.append(p)
    # Also inspect recent JSONs whose text explicitly mentions R4.32/Geonomics.
    if output_root.exists():
        for p in output_root.rglob("*.json"):
            if p in candidates:
                continue
            try:
                if p.stat().st_size > 20 * 1024 * 1024:
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")[:2_000_000].lower()
            except OSError:
                continue
            if any(tok in text for tok in INTEREST_TOKENS):
                candidates.append(p)
    return sorted(set(candidates))


def main() -> int:
    root = Path(os.environ.get("ARCANA_PROJECT_ROOT", Path.cwd())).resolve()
    outdir = root / "outputs" / "v0_6D1_R4_32"
    outdir.mkdir(parents=True, exist_ok=True)
    report_path = outdir / "R4_32_R1_GEONOMICS_STATIC_VALIDATION_DIAGNOSTIC.json"

    files = discover_jsons(root)
    parse_errors: list[dict[str, str]] = []
    manifest_candidates: list[dict[str, Any]] = []
    all_static_false: list[dict[str, Any]] = []

    for p in files:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            parse_errors.append({"file": str(p.relative_to(root)), "error": repr(exc)})
            continue

        for loc, obj in walk(data):
            if not isinstance(obj, dict):
                continue
            flags = collect_static_flags(obj)
            false_flags = [f for f in flags if f.get("value") is False]
            if false_flags:
                all_static_false.append({
                    "file": str(p.relative_to(root)),
                    "location": loc,
                    "job_ids": sorted(infer_job_ids(obj)),
                    "false_static_flags": false_flags,
                })

            if likely_manifest(obj):
                jobs = direct_job_ids(obj)
                if not jobs:
                    continue
                refs = inspect_refs(obj, root, p.parent)
                mp = mapping_presence(obj)
                problems: list[str] = []
                if not all(mp.values()):
                    problems.append("MISSING_MAPPING_CLASS:" + ",".join(k for k, ok in mp.items() if not ok))
                if any(not r["exists"] for r in refs):
                    problems.append("MISSING_REFERENCED_FILE")
                if any(r.get("hash_match") is False for r in refs):
                    problems.append("HASH_MISMATCH")
                if any("PATH_RESOLUTION_AMBIGUITY" in r.get("notes", []) for r in refs):
                    problems.append("PATH_RESOLUTION_AMBIGUITY")
                if any(f.get("value") is False for f in flags):
                    problems.append("MANIFEST_STATIC_FLAG_FALSE")

                manifest_candidates.append({
                    "file": str(p.relative_to(root)),
                    "location": loc,
                    "job_ids": sorted(jobs),
                    "mapping_class_presence": mp,
                    "static_flags": flags,
                    "referenced_files": refs,
                    "problems": sorted(set(problems)),
                })

    # Keep most specific candidate per (file, job ids), preferring smaller object locations.
    dedup: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    for rec in manifest_candidates:
        key = (rec["file"], tuple(rec["job_ids"]))
        old = dedup.get(key)
        if old is None or len(rec["location"]) > len(old["location"]):
            dedup[key] = rec
    manifests = list(dedup.values())

    by_job: dict[str, list[dict[str, Any]]] = {j: [] for j in sorted(JOB_IDS)}
    for rec in manifests:
        for j in rec["job_ids"]:
            if j in by_job:
                by_job[j].append(rec)

    job_summary: dict[str, Any] = {}
    for j, recs in by_job.items():
        problems = sorted({p for rec in recs for p in rec["problems"]})
        false_flags = [f for rec in recs for f in rec["static_flags"] if f.get("value") is False]
        job_summary[j] = {
            "candidate_object_count": len(recs),
            "problems": problems,
            "false_static_flag_count": len(false_flags),
            "mapping_classes_complete_in_any_candidate": any(all(rec["mapping_class_presence"].values()) for rec in recs),
            "missing_reference_count": sum(sum(not r["exists"] for r in rec["referenced_files"]) for rec in recs),
            "hash_mismatch_count": sum(sum(r.get("hash_match") is False for r in rec["referenced_files"]) for rec in recs),
        }

    status = "DIAGNOSTIC_COMPLETE"
    report = {
        "stage": "v0.6D1-R4.32-R1",
        "status": status,
        "purpose": "DIAGNOSE_LIVE_R432_GEONOMICS_STATIC_VALIDATION_FAILURE_WITHOUT_MUTATING_CANONICAL_STATE_OR_RERUNNING_EXTERNAL_ENGINES",
        "project_root": str(root),
        "json_files_scanned": len(files),
        "json_parse_error_count": len(parse_errors),
        "parse_errors": parse_errors,
        "job_summary": job_summary,
        "manifest_candidates": manifests,
        "all_discovered_false_static_flags": all_static_false,
        "governance": {
            "external_engine_execution_performed": False,
            "target_numeric_execution_performed": False,
            "readjudication_performed": False,
            "canonical_state_changed": False,
            "failed_r432_evidence_preserved": True,
            "gate_weakening_performed": False,
        },
        "next_action": "REPAIR_ONLY_THE_DISCOVERED_R432_GEONOMICS_STATIC_VALIDATION_ROOT_CAUSE",
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("=== R4.32-R1 Geonomics static-validation diagnostic ===")
    print(json.dumps({
        "stage": report["stage"],
        "status": report["status"],
        "json_files_scanned": report["json_files_scanned"],
        "json_parse_error_count": report["json_parse_error_count"],
        "job_summary": report["job_summary"],
        "report": str(report_path.relative_to(root)),
        "governance": report["governance"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
