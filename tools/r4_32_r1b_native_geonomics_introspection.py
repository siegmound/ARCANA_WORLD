from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

STAGE = "v0.6D1-R4.32-R1B"
JOB_IDS = ("J14", "J18", "J21")
TOKENS = (
    "geonomics_parameter_manifest_static_valid_count",
    "geonomics_all_three_static_valid",
    "geonomics_exact_three_parameter_manifests",
    "parameter_manifest",
    "static_valid",
    "static_validation",
    "J14",
    "J18",
    "J21",
)
SOURCE_EXTS = {".py", ".ps1", ".md", ".txt"}
MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_JSON_BYTES = 64 * 1024 * 1024


def walk(obj: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


def scalar_text(v: Any) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float, bool)) or v is None:
        return json.dumps(v)
    return ""


def subtree_text(obj: Any, limit: int = 200_000) -> str:
    chunks: list[str] = []
    size = 0
    for _, v in walk(obj):
        if isinstance(v, dict):
            vals = [str(k) for k in v.keys()]
        else:
            t = scalar_text(v)
            vals = [t] if t else []
        for s in vals:
            size += len(s) + 1
            if size > limit:
                return " ".join(chunks)
            chunks.append(s)
    return " ".join(chunks)


def jobs_in(obj: Any) -> set[str]:
    text = subtree_text(obj).upper()
    found = set()
    for jid in JOB_IDS:
        if re.search(rf"(?<![A-Z0-9]){jid}(?![A-Z0-9])", text):
            found.add(jid)
    return found


def geonomics_in(obj: Any) -> bool:
    return "GEONOMICS" in subtree_text(obj).upper()


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def source_matches(root: Path) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    skip_parts = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules"}
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SOURCE_EXTS:
            continue
        if any(part in skip_parts for part in p.parts):
            continue
        try:
            if p.stat().st_size > MAX_TEXT_BYTES:
                continue
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        hit_lines: set[int] = set()
        lower_lines = [line.lower() for line in lines]
        for i, low in enumerate(lower_lines):
            if any(tok.lower() in low for tok in TOKENS[:6]):
                hit_lines.add(i)
        if not hit_lines:
            continue
        for i in sorted(hit_lines):
            lo, hi = max(0, i - 4), min(len(lines), i + 5)
            matches.append({
                "file": rel(p, root),
                "line": i + 1,
                "text": lines[i].strip(),
                "context": [f"{j+1:05d}: {lines[j]}" for j in range(lo, hi)],
            })
    return matches


def json_files(root: Path) -> list[Path]:
    roots = []
    out = root / "outputs"
    if out.exists():
        roots.append(out)
    roots.append(root)
    seen: set[Path] = set()
    result: list[Path] = []
    for sr in roots:
        for p in sr.rglob("*.json"):
            if p in seen:
                continue
            seen.add(p)
            try:
                if p.stat().st_size > MAX_JSON_BYTES:
                    continue
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            low = text.lower()
            name_low = str(p).lower()
            if (
                "r4_32" in name_low
                or "r432" in name_low
                or "geonomics" in name_low
                or "geonomics" in low
                or "geonomics_parameter_manifest_static_valid_count" in low
                or all(j.lower() in low for j in JOB_IDS)
            ):
                result.append(p)
    return sorted(result)


def false_like_fields(obj: Any, base_path: str = "$") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for loc, v in walk(obj, base_path):
        if not isinstance(v, dict):
            continue
        for k, val in v.items():
            lk = str(k).lower()
            interesting = any(t in lk for t in ("static", "valid", "pass", "complete", "hash", "mapping", "available", "exists"))
            falsey = val is False or (isinstance(val, str) and val.upper().startswith(("FAIL", "BLOCKED", "INVALID", "MISSING")))
            if interesting and falsey:
                out.append({"location": f"{loc}.{k}", "key": str(k), "value": val})
    return out


def compact_obj(obj: Any, max_chars: int = 16_000) -> Any:
    try:
        text = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        return repr(obj)[:max_chars]
    if len(text) <= max_chars:
        return obj
    return {"_truncated_json": text[:max_chars], "_original_chars": len(text)}


def analyze_json(root: Path, p: Path, data: Any) -> dict[str, Any]:
    job_locations: dict[str, list[str]] = {j: [] for j in JOB_IDS}
    geonomics_contexts: list[dict[str, Any]] = []
    all_three_contexts: list[dict[str, Any]] = []
    static_false: list[dict[str, Any]] = []
    count_fields: list[dict[str, Any]] = []

    # Gather scalar/key locations without requiring a fixed schema.
    for loc, obj in walk(data):
        if isinstance(obj, dict):
            for k, v in obj.items():
                lk = str(k).lower()
                if "geonomics_parameter_manifest_static_valid_count" in lk:
                    count_fields.append({"location": f"{loc}.{k}", "value": v})
                if "static_valid" in lk and v is False:
                    static_false.append({"location": f"{loc}.{k}", "value": v})
        elif isinstance(obj, str):
            up = obj.upper()
            for jid in JOB_IDS:
                if re.search(rf"(?<![A-Z0-9]){jid}(?![A-Z0-9])", up):
                    if len(job_locations[jid]) < 30:
                        job_locations[jid].append(loc)

    # Select minimal useful dict/list contexts. This deliberately permits nested
    # job identity, engine identity, and manifest fields.
    for loc, obj in walk(data):
        if not isinstance(obj, (dict, list)):
            continue
        jobs = jobs_in(obj)
        if not jobs:
            continue
        has_geo = geonomics_in(obj)
        text_low = subtree_text(obj, 80_000).lower()
        manifestish = any(t in text_low for t in ("manifest", "static_valid", "static_validation", "canonical_parameter", "parameter"))
        if has_geo and manifestish and len(geonomics_contexts) < 50:
            falses = false_like_fields(obj, loc)
            geonomics_contexts.append({
                "location": loc,
                "job_ids": sorted(jobs),
                "false_like_fields": falses[:40],
                "snapshot": compact_obj(obj),
            })
        if jobs == set(JOB_IDS) and manifestish and len(all_three_contexts) < 20:
            all_three_contexts.append({
                "location": loc,
                "geonomics_present": has_geo,
                "false_like_fields": false_like_fields(obj, loc)[:60],
                "snapshot": compact_obj(obj),
            })

    return {
        "file": rel(p, root),
        "job_token_locations": job_locations,
        "geonomics_parameter_static_valid_count_fields": count_fields,
        "explicit_static_valid_false_fields": static_false,
        "geonomics_job_manifest_contexts": geonomics_contexts,
        "all_three_job_manifest_contexts": all_three_contexts,
    }


def infer_root_cause(report: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    src = report["implementation_source_matches"]
    if not src:
        candidates.append("R432_IMPLEMENTATION_SOURCE_NOT_LOCATED_BY_CANONICAL_TOKENS")
    jsons = report["json_analysis"]
    if not jsons:
        candidates.append("NO_R432_OR_GEONOMICS_JSON_EVIDENCE_LOCATED")
    if any(a["geonomics_parameter_static_valid_count_fields"] for a in jsons):
        candidates.append("NATIVE_R432_STATIC_VALID_COUNT_EVIDENCE_LOCATED")
    false_hits = sum(len(a["explicit_static_valid_false_fields"]) for a in jsons)
    if false_hits:
        candidates.append("EXPLICIT_NATIVE_STATIC_VALID_FALSE_FIELDS_LOCATED")
    contexts = sum(len(a["geonomics_job_manifest_contexts"]) for a in jsons)
    if contexts:
        candidates.append("NATIVE_GEONOMICS_JOB_MANIFEST_CONTEXTS_LOCATED")
    return candidates


def main() -> int:
    root = Path(os.environ.get("ARCANA_PROJECT_ROOT", Path.cwd())).resolve()
    outdir = root / "outputs" / "v0_6D1_R4_32"
    outdir.mkdir(parents=True, exist_ok=True)
    report_path = outdir / "R4_32_R1B_NATIVE_GEONOMICS_STATIC_VALIDATION_INTROSPECTION.json"

    src = source_matches(root)
    parse_errors: list[dict[str, str]] = []
    analyses: list[dict[str, Any]] = []
    for p in json_files(root):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            parse_errors.append({"file": rel(p, root), "error": repr(exc)})
            continue
        analyses.append(analyze_json(root, p, data))

    report: dict[str, Any] = {
        "stage": STAGE,
        "status": "NATIVE_INTROSPECTION_COMPLETE",
        "project_root": str(root),
        "implementation_source_match_count": len(src),
        "implementation_source_matches": src,
        "json_candidate_file_count": len(analyses),
        "json_parse_error_count": len(parse_errors),
        "json_parse_errors": parse_errors,
        "json_analysis": analyses,
        "governance": {
            "external_engine_execution_performed": False,
            "target_numeric_execution_performed": False,
            "readjudication_performed": False,
            "canonical_state_changed": False,
            "failed_r432_evidence_preserved": True,
            "gate_weakening_performed": False,
            "diagnostic_only": True,
        },
    }
    report["root_cause_candidates"] = infer_root_cause(report)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Compact console output: enough to paste back, while the detailed report
    # retains full snapshots and source contexts.
    per_job = {}
    for jid in JOB_IDS:
        token_files = []
        manifest_contexts = []
        false_fields = []
        for a in analyses:
            if a["job_token_locations"][jid]:
                token_files.append(a["file"])
            for c in a["geonomics_job_manifest_contexts"]:
                if jid in c["job_ids"]:
                    manifest_contexts.append({
                        "file": a["file"],
                        "location": c["location"],
                        "false_like_fields": c["false_like_fields"],
                    })
            for f in a["explicit_static_valid_false_fields"]:
                # Associate only if the file contains the job token; detailed
                # JSON report preserves exact context for follow-up.
                if a["job_token_locations"][jid]:
                    false_fields.append({"file": a["file"], **f})
        per_job[jid] = {
            "token_file_count": len(set(token_files)),
            "manifest_context_count": len(manifest_contexts),
            "explicit_static_valid_false_count": len(false_fields),
            "manifest_contexts": manifest_contexts[:8],
        }

    console = {
        "stage": STAGE,
        "status": report["status"],
        "implementation_source_match_count": len(src),
        "implementation_source_matches": [
            {"file": m["file"], "line": m["line"], "text": m["text"]} for m in src[:30]
        ],
        "json_candidate_file_count": len(analyses),
        "json_parse_error_count": len(parse_errors),
        "per_job": per_job,
        "static_valid_count_fields": [
            {"file": a["file"], **f}
            for a in analyses for f in a["geonomics_parameter_static_valid_count_fields"]
        ][:20],
        "root_cause_candidates": report["root_cause_candidates"],
        "report": rel(report_path, root),
        "governance": report["governance"],
    }
    print("=== R4.32-R1B native Geonomics static-validation introspection ===")
    print(json.dumps(console, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
