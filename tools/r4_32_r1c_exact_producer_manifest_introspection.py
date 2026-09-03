from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

STAGE = "v0.6D1-R4.32-R1C"
JOBS = ("J14", "J18", "J21")
R432_HINTS = (
    "geonomics_parameter_manifest_static_valid_count",
    "geonomics_all_three_static_valid",
    "geonomics_exact_three_parameter_manifests",
    "geonomics",
    "parameter_manifest",
    "canonical_parameter",
    "static_valid",
)
INTEREST_KEYS = (
    "static", "valid", "mapping", "time", "space", "population", "domain",
    "uncertainty", "hash", "sha", "source", "artifact", "path", "file",
    "authority", "exists", "available", "complete", "reason", "status",
)
EXTS = (".json", ".npz", ".npy", ".csv", ".parquet", ".pkl", ".pickle", ".txt", ".md")


def rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def walk(obj: Any, path: str = "$"):
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


def compact(obj: Any, max_chars: int = 40000):
    try:
        s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        return repr(obj)[:max_chars]
    if len(s) <= max_chars:
        return obj
    return {"_truncated": s[:max_chars], "_original_chars": len(s)}


def contains_job(obj: Any, job: str) -> bool:
    try:
        s = json.dumps(obj, ensure_ascii=False).upper()
    except Exception:
        s = repr(obj).upper()
    return re.search(rf"(?<![A-Z0-9]){job}(?![A-Z0-9])", s) is not None


def manifestish(obj: Any) -> bool:
    try:
        s = json.dumps(obj, ensure_ascii=False).lower()
    except Exception:
        s = repr(obj).lower()
    return any(t in s for t in ("manifest", "canonical_parameter", "static_valid", "mapping_class", "geonomics"))


def focused_fields(obj: Any, base="$"):
    rows = []
    for loc, v in walk(obj, base):
        if isinstance(v, dict):
            for k, val in v.items():
                lk = str(k).lower()
                if any(t in lk for t in INTEREST_KEYS):
                    if isinstance(val, (str, int, float, bool)) or val is None:
                        rows.append({"location": f"{loc}.{k}", "key": str(k), "value": val})
    return rows


def source_candidates(root: Path):
    roots = [
        root / "src" / "arcana_worldsim" / "scientific_engines",
        root / "scripts",
        root / "tests",
    ]
    out = []
    for sr in roots:
        if not sr.exists():
            continue
        for p in sr.rglob("*.py"):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            low = text.lower()
            score = 0
            if "geonomics_parameter_manifest_static_valid_count" in low:
                score += 100
            if "r432" in p.name.lower() or "r4_32" in p.name.lower():
                score += 50
            if "geonomics" in low:
                score += 20
            if "parameter_manifest" in low or "canonical_parameter" in low:
                score += 20
            if "static_valid" in low:
                score += 10
            if all(j.lower() in low for j in JOBS):
                score += 20
            if score:
                out.append((score, p, text))
    return sorted(out, key=lambda x: (-x[0], str(x[1])))


def exact_source_introspection(root: Path):
    result = []
    for score, p, text in source_candidates(root)[:20]:
        lines = text.splitlines()
        hits = []
        for i, line in enumerate(lines):
            low = line.lower()
            if (
                "geonomics_parameter_manifest_static_valid_count" in low
                or "geonomics_all_three_static_valid" in low
                or "geonomics_exact_three_parameter_manifests" in low
                or ("static_valid" in low and "geonomics" in text.lower())
                or ("mapping" in low and "geonomics" in text.lower())
                or any(j.lower() in low for j in JOBS)
            ):
                lo, hi = max(0, i - 5), min(len(lines), i + 6)
                hits.append({
                    "line": i + 1,
                    "text": line.strip(),
                    "context": [f"{n+1:05d}: {lines[n]}" for n in range(lo, hi)],
                })

        functions = []
        literals = []
        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    seg = ast.get_source_segment(text, node) or ""
                    low = seg.lower()
                    if any(h in low for h in R432_HINTS) and (
                        "geonomics" in low or any(j.lower() in low for j in JOBS)
                    ):
                        functions.append({
                            "name": node.name,
                            "start_line": node.lineno,
                            "end_line": getattr(node, "end_lineno", None),
                            "source": seg[:50000],
                        })
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    s = node.value.replace("\\", "/")
                    if any(s.lower().endswith(ext) for ext in EXTS) and (
                        "r3" in s.lower() or "r4" in s.lower() or "output" in s.lower()
                    ):
                        literals.append(node.value)
        except SyntaxError as exc:
            functions.append({"ast_error": repr(exc)})

        result.append({
            "score": score,
            "file": rel(p, root),
            "hits": hits[:80],
            "relevant_functions": functions[:20],
            "path_literals": sorted(set(literals))[:100],
        })
    return result


def resolve_literal(root: Path, literal: str):
    raw = literal.strip()
    p = Path(raw)
    candidates = []
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.extend([root / p, root / raw.replace("\\", "/")])
    # Also case-insensitive filename lookup if exact relative path fails.
    existing = []
    for c in candidates:
        try:
            if c.exists() and c.is_file():
                existing.append(c.resolve())
        except OSError:
            pass
    dedup = []
    seen = set()
    for e in existing:
        if str(e).lower() not in seen:
            seen.add(str(e).lower())
            dedup.append(e)
    return [{
        "path": rel(e, root),
        "exists": True,
        "size": e.stat().st_size,
        "sha256": sha256(e),
    } for e in dedup]


def inspect_r432_outputs(root: Path):
    outdir = root / "outputs" / "v0_6D1_R4_32"
    files = []
    jobs = {j: [] for j in JOBS}
    if not outdir.exists():
        return {"output_dir_exists": False, "files": [], "per_job": jobs}
    for p in sorted(outdir.rglob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            files.append({"file": rel(p, root), "parse_error": repr(exc)})
            continue

        all_fields = focused_fields(data)
        geo = "geonomics" in json.dumps(data, ensure_ascii=False).lower()
        entry = {
            "file": rel(p, root),
            "top_level_keys": list(data.keys()) if isinstance(data, dict) else None,
            "geonomics_present": geo,
            "focused_fields": all_fields[:250],
        }
        if geo or "manifest" in p.name.lower() or "parameter" in p.name.lower():
            entry["snapshot"] = compact(data, 50000)
        files.append(entry)

        for job in JOBS:
            if not contains_job(data, job):
                continue
            contexts = []
            for loc, obj in walk(data):
                if isinstance(obj, (dict, list)) and contains_job(obj, job) and manifestish(obj):
                    contexts.append({
                        "location": loc,
                        "focused_fields": focused_fields(obj, loc)[:150],
                        "snapshot": compact(obj, 30000),
                    })
                    if len(contexts) >= 12:
                        break
            jobs[job].append({"file": rel(p, root), "contexts": contexts})
    return {"output_dir_exists": True, "files": files, "per_job": jobs}


def literal_integrity(root: Path, sources):
    literals = []
    for s in sources:
        for lit in s.get("path_literals", []):
            literals.append((s["file"], lit))
    rows = []
    seen = set()
    for src, lit in literals:
        key = (src, lit)
        if key in seen:
            continue
        seen.add(key)
        resolved = resolve_literal(root, lit)
        rows.append({
            "source_file": src,
            "literal": lit,
            "resolved": resolved,
            "exists": bool(resolved),
        })
    return rows


def identify_likely_failures(output_info):
    findings = []
    for job, entries in output_info["per_job"].items():
        for e in entries:
            for c in e["contexts"]:
                for f in c["focused_fields"]:
                    k = f["key"].lower()
                    v = f["value"]
                    bad = (
                        v is False
                        or (isinstance(v, str) and v.upper().startswith(("FAIL", "BLOCKED", "INVALID", "MISSING")))
                    )
                    if bad and any(t in k for t in ("static", "valid", "mapping", "hash", "exists", "available", "complete")):
                        findings.append({
                            "job": job,
                            "file": e["file"],
                            "location": f["location"],
                            "key": f["key"],
                            "value": v,
                        })
    # dedupe
    dedup = []
    seen = set()
    for r in findings:
        key = (r["job"], r["file"], r["location"], repr(r["value"]))
        if key not in seen:
            seen.add(key)
            dedup.append(r)
    return dedup[:200]


def main():
    root = Path(os.environ.get("ARCANA_PROJECT_ROOT", Path.cwd())).resolve()
    outdir = root / "outputs" / "v0_6D1_R4_32"
    outdir.mkdir(parents=True, exist_ok=True)
    report_path = outdir / "R4_32_R1C_EXACT_PRODUCER_AND_MANIFEST_CAUSE_INTROSPECTION.json"

    sources = exact_source_introspection(root)
    outputs = inspect_r432_outputs(root)
    paths = literal_integrity(root, sources)
    failures = identify_likely_failures(outputs)

    report = {
        "stage": STAGE,
        "status": "EXACT_PRODUCER_AND_MANIFEST_INTROSPECTION_COMPLETE",
        "project_root": str(root),
        "producer_source_candidates": sources,
        "r432_outputs": outputs,
        "literal_path_integrity": paths,
        "likely_r432_manifest_failures": failures,
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
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Console is intentionally narrow and exact.
    console_sources = []
    for s in sources[:6]:
        console_sources.append({
            "score": s["score"],
            "file": s["file"],
            "critical_hits": [
                {"line": h["line"], "text": h["text"]}
                for h in s["hits"]
                if any(t in h["text"].lower() for t in (
                    "static_valid", "geonomics_parameter_manifest_static_valid_count",
                    "mapping", "j14", "j18", "j21"
                ))
            ][:40],
            "relevant_function_names": [f.get("name") for f in s["relevant_functions"] if f.get("name")],
            "path_literals": s["path_literals"][:40],
        })

    per_job = {}
    for job, entries in outputs["per_job"].items():
        compact_entries = []
        for e in entries[:8]:
            compact_entries.append({
                "file": e["file"],
                "contexts": [
                    {
                        "location": c["location"],
                        "focused_fields": c["focused_fields"][:60],
                    }
                    for c in e["contexts"][:4]
                ],
            })
        per_job[job] = compact_entries

    console = {
        "stage": STAGE,
        "status": report["status"],
        "producer_source_candidates": console_sources,
        "r432_output_json_count": len(outputs["files"]),
        "per_job_exact_r432_contexts": per_job,
        "likely_r432_manifest_failures": failures,
        "missing_literal_paths": [r for r in paths if not r["exists"]][:100],
        "report": rel(report_path, root),
        "governance": report["governance"],
    }
    print("=== R4.32-R1C exact producer + manifest cause introspection ===")
    print(json.dumps(console, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
