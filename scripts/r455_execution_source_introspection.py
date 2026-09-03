from __future__ import annotations

from pathlib import Path
from typing import Any
import ast
import hashlib
import json
import re
import sys

STAGE = "R455_PREBUILD_EXECUTION_SOURCE_INTROSPECTION"
EXPECTED_PLAN_SHA = "f4804e9aabf2f009c9581012a136865b9cdb2e688d416f48d6a50be840dff7e6"
EXPECTED_REGISTRY_SHA = "f39bb36251a95f2d9e310113a9286608d72188374d7d9bc73fe90aa697e5d380"

R454 = Path("outputs/v0_6D1_R4_54/R4_54_INTEGRATED_AUDIT.json")
R454_SEAL = Path("outputs/v0_6D1_R4_54_SEAL/R4_54_FINAL_SEAL_AUDIT.json")
R454_R3 = Path("outputs/v0_6D1_R4_54_R3/R4_54_R3_POSTREPAIR_RESEAL_AUDIT.json")
R452_PLAN = Path("outputs/v0_6D1_R4_52/R4_52_NON_GEONOMICS_EXECUTION_PLAN.json")
R453_REGISTRY = Path(
    "outputs/v0_6D1_R4_53/"
    "R4_53_NON_GEONOMICS_EXECUTION_READOUT_AUTHORITY_REGISTRY.json"
)
R42_MATRIX = Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")
OUT = Path(
    "outputs/v0_6D1_R4_55_PREBUILD_INTROSPECTION/"
    "R4_55_EXECUTION_SOURCE_INTROSPECTION.json"
)

ENGINE_ORDER = ["Madingley", "RangeShifter", "CDMetaPOP", "NEMO", "SLiM"]

SOURCE_GLOBS = [
    "src/arcana_worldsim/scientific_engines/r43*.py",
    "src/arcana_worldsim/scientific_engines/r44*.py",
    "src/arcana_worldsim/scientific_engines/r45*.py",
    "src/arcana_worldsim/scientific_engines/r46*.py",
    "src/arcana_worldsim/scientific_engines/r47*.py",
    "src/arcana_worldsim/scientific_engines/r4[0-2][0-9]*.py",
    "benchmarks/r43/**/*",
    "benchmarks/r47/**/*",
    "benchmarks/r421/**/*",
    "benchmarks/r422/**/*",
    "run_v0_6D1_R4_3*.ps1",
    "capture_v0_6D1_R4_3*.ps1",
    "run_v0_6D1_R4_7*.ps1",
    "capture_v0_6D1_R4_7*.ps1",
    "run_v0_6D1_R4_21*.ps1",
    "capture_v0_6D1_R4_21*.ps1",
    "run_v0_6D1_R4_22*.ps1",
    "capture_v0_6D1_R4_22*.ps1",
]

KEY_RE = re.compile(
    r"(seed|adapter|command|config|profile|runtime|artifact|source|mapping|"
    r"metric|input|output|window|engine|baseline|contract|raw|normal)",
    re.I,
)

FUNC_RE = re.compile(
    r"(execute|run|adapter|contract|seed|material|profile|raw|normal|"
    r"evidence|engine|invoke|capture)",
    re.I,
)

LINE_RE = re.compile(
    r"(subprocess|runpy|argparse|sys\.argv|conda|wsl|Rscript|nemo|slim|"
    r"CDMetaPOP|RangeShift|Madingley|adapter|JOB_CONTRACT|RAW_EVIDENCE|"
    r"NORMALIZED_EVIDENCE|seed)",
    re.I,
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _compact(value: Any, depth: int = 0) -> Any:
    if depth > 3:
        if isinstance(value, dict):
            return {"__dict_keys__": sorted(map(str, value.keys()))[:50]}
        if isinstance(value, list):
            return {"__list_len__": len(value)}
        return str(value)[:300]

    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if KEY_RE.search(str(k)):
                out[str(k)] = _compact(v, depth + 1)
        return out
    if isinstance(value, list):
        if len(value) <= 12:
            return [_compact(v, depth + 1) for v in value]
        return {
            "__list_len__": len(value),
            "head": [_compact(v, depth + 1) for v in value[:4]],
            "tail": [_compact(v, depth + 1) for v in value[-2:]],
        }
    if isinstance(value, str):
        return value if len(value) <= 500 else value[:500] + "...<truncated>"
    return value


def _function_signature(node: ast.AST) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ""
    parts = []
    args = list(node.args.posonlyargs) + list(node.args.args)
    defaults = [None] * (len(args) - len(node.args.defaults)) + list(node.args.defaults)
    for a, d in zip(args, defaults):
        text = a.arg
        if d is not None:
            try:
                text += "=" + ast.unparse(d)
            except Exception:
                text += "=..."
        parts.append(text)
    if node.args.vararg:
        parts.append("*" + node.args.vararg.arg)
    for a, d in zip(node.args.kwonlyargs, node.args.kw_defaults):
        text = a.arg
        if d is not None:
            try:
                text += "=" + ast.unparse(d)
            except Exception:
                text += "=..."
        parts.append(text)
    if node.args.kwarg:
        parts.append("**" + node.args.kwarg.arg)
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}{node.name}({', '.join(parts)})"


def _compact_literal(value: Any, depth: int = 0) -> Any:
    """Bound a literal while preserving mapping keys such as engine names."""
    if depth > 4:
        if isinstance(value, dict):
            return {"__dict_len__": len(value)}
        if isinstance(value, (list, tuple)):
            return {"__sequence_len__": len(value)}
        return str(value)[:300]

    if isinstance(value, dict):
        items = list(value.items())
        out = {}
        for k, v in items[:100]:
            out[str(k)] = _compact_literal(v, depth + 1)
        if len(items) > 100:
            out["__truncated_dict_items__"] = len(items) - 100
        return out

    if isinstance(value, (list, tuple)):
        seq = list(value)
        if len(seq) <= 30:
            return [_compact_literal(v, depth + 1) for v in seq]
        return {
            "__sequence_len__": len(seq),
            "head": [_compact_literal(v, depth + 1) for v in seq[:10]],
            "tail": [_compact_literal(v, depth + 1) for v in seq[-3:]],
        }

    if isinstance(value, str):
        return value if len(value) <= 800 else value[:800] + "...<truncated>"
    if isinstance(value, (int, float, bool, type(None))):
        return value
    return str(value)[:300]


def _safe_literal(node: ast.AST) -> Any:
    try:
        v = ast.literal_eval(node)
    except Exception:
        return None
    if isinstance(v, (dict, list, tuple, str, int, float, bool, type(None))):
        return _compact_literal(v)
    return None


def inspect_python(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rec: dict[str, Any] = {
        "parse_ok": False,
        "functions": [],
        "literal_bindings": {},
        "relevant_lines": [],
        "main_guard_present": 'if __name__ == "__main__"' in text
            or "if __name__=='__main__'" in text,
    }
    try:
        tree = ast.parse(text)
        rec["parse_ok"] = True
    except Exception as exc:
        rec["parse_error"] = repr(exc)
        return rec

    lines = text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and FUNC_RE.search(node.name):
            item = {
                "name": node.name,
                "signature": _function_signature(node),
                "start_line": int(node.lineno),
                "end_line": int(getattr(node, "end_lineno", node.lineno)),
            }
            # Include a bounded source excerpt, enough to recover CLI/dispatch shape.
            start = max(0, node.lineno - 1)
            end = min(len(lines), start + 80)
            item["source_excerpt"] = "\n".join(
                f"{i+1:05d}: {lines[i]}" for i in range(start, end)
            )
            rec["functions"].append(item)

        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = []
            value = None
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            else:
                targets = [node.target]
                value = node.value
            if value is None:
                continue
            literal = _safe_literal(value)
            if literal is None:
                continue
            for target in targets:
                if isinstance(target, ast.Name) and (
                    target.id.isupper()
                    or target.id in {
                        "ADAPTER_PATHS", "CANDIDATES", "ENGINE_COMMANDS",
                        "ENGINE_CONFIGS", "GEONOMICS_JOBS",
                    }
                ):
                    rec["literal_bindings"][target.id] = literal

    for i, line in enumerate(lines, 1):
        if LINE_RE.search(line):
            rec["relevant_lines"].append({"line": i, "text": line[:1200]})
            if len(rec["relevant_lines"]) >= 250:
                break

    rec["functions"] = rec["functions"][:100]
    return rec


def inspect_text_source(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines, 1):
        if LINE_RE.search(line):
            hits.append({"line": i, "text": line[:1200]})
            if len(hits) >= 300:
                break
    return {"relevant_lines": hits}


def source_candidates(root: Path) -> list[Path]:
    found = set()
    for pat in SOURCE_GLOBS:
        for p in root.glob(pat):
            if p.is_file():
                found.add(p.resolve())
    return sorted(found, key=lambda p: str(p).lower())


def inspect_sources(root: Path) -> list[dict[str, Any]]:
    out = []
    for p in source_candidates(root):
        rel = p.relative_to(root).as_posix()
        rec = {
            "path": rel,
            "sha256": sha256(p),
            "bytes": p.stat().st_size,
            "suffix": p.suffix.lower(),
        }
        if p.suffix.lower() == ".py":
            rec["inspection"] = inspect_python(p)
        elif p.suffix.lower() in {".ps1", ".sh", ".r"}:
            rec["inspection"] = inspect_text_source(p)
        else:
            # Only hash and path binary/other files.
            rec["inspection"] = {}
        out.append(rec)
    return out


def contract_summary(root: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for job in plan["jobs"]:
        jid = str(job["job_id"])
        p = root / "outputs/v0_6D1_R4_3/jobs" / jid / "JOB_CONTRACT.json"
        rec = {
            "job_id": jid,
            "engine": job["engine"],
            "window_id": job["window_id"],
            "path": p.relative_to(root).as_posix(),
            "present": p.exists(),
            "r452_frozen_seeds": job["frozen_seeds"],
            "r452_r42_job_record_sha256": job["r42_job_record_sha256"],
        }
        if p.exists():
            try:
                obj = load(p)
                rec.update({
                    "sha256": sha256(p),
                    "top_level_keys": sorted(map(str, obj.keys())) if isinstance(obj, dict) else [],
                    "relevant_contract_fields": _compact(obj),
                })
            except Exception as exc:
                rec["parse_error"] = repr(exc)
        rows.append(rec)
    return rows


def candidate_adapter_paths(source_records: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    out = {e: [] for e in ENGINE_ORDER}
    engine_terms = {
        "Madingley": re.compile(r"madingley", re.I),
        "RangeShifter": re.compile(r"range.?shift", re.I),
        "CDMetaPOP": re.compile(r"cdmeta", re.I),
        "NEMO": re.compile(r"nemo", re.I),
        "SLiM": re.compile(r"slim", re.I),
    }
    for rec in source_records:
        path = rec["path"]
        inspection = rec.get("inspection") or {}
        hay = path + "\n"
        hay += "\n".join(
            x.get("text", "") for x in inspection.get("relevant_lines", [])
        )
        hay += "\n" + json.dumps(inspection.get("literal_bindings", {}), ensure_ascii=False)
        for engine, rx in engine_terms.items():
            if rx.search(hay):
                out[engine].append({"path": path, "sha256": rec["sha256"]})
    return out


def main() -> int:
    root = Path.cwd().resolve()

    required = [R454, R454_SEAL, R454_R3, R452_PLAN, R453_REGISTRY, R42_MATRIX]
    missing = [p.as_posix() for p in required if not (root / p).exists()]
    if missing:
        print(json.dumps({
            "stage": STAGE,
            "status": "BLOCKED_R455_PREBUILD_REQUIRED_AUTHORITY_MISSING",
            "missing": missing,
        }, indent=2))
        return 2

    r454 = load(root / R454)
    r454_seal = load(root / R454_SEAL)
    r454_r3 = load(root / R454_R3)
    plan = load(root / R452_PLAN)
    registry = load(root / R453_REGISTRY)
    matrix = load(root / R42_MATRIX)

    authority_checks = {
        "r454_complete_32_32":
            r454.get("checks_passed") == 32
            and r454.get("checks_failed") == 0
            and str(r454.get("status", "")).startswith("PASS_R454_"),
        "r454_sealed_21_21":
            r454_seal.get("verdict") == "SEALED"
            and r454_seal.get("checks_passed") == 21,
        "r454_r3_postrepair_12_12":
            r454_r3.get("checks_passed") == 12
            and str(r454_r3.get("status", "")).startswith("PASS_R454_R3_"),
        "r454_80_stream_authorization":
            r454.get("scientific_execution_authorized") is True
            and r454.get("planned_scientific_stream_count") == 80,
        "r452_plan_sha_exact":
            plan.get("plan_sha256") == EXPECTED_PLAN_SHA,
        "r453_registry_sha_exact":
            registry.get("registry_sha256") == EXPECTED_REGISTRY_SHA,
        "r42_exact_23":
            matrix.get("job_count") == 23 and len(matrix.get("jobs") or []) == 23,
        "r452_exact_20_non_geonomics_jobs":
            len(plan.get("jobs") or []) == 20
            and all(j.get("engine") in ENGINE_ORDER for j in plan.get("jobs") or []),
        "r452_four_seeds_per_job":
            all(len(j.get("frozen_seeds") or []) == 4 for j in plan.get("jobs") or []),
    }

    contracts = contract_summary(root, plan)
    sources = inspect_sources(root)
    adapter_candidates = candidate_adapter_paths(sources)

    contract_counts = {
        "present": sum(r["present"] for r in contracts),
        "missing": sum(not r["present"] for r in contracts),
        "parse_errors": sum("parse_error" in r for r in contracts),
    }

    engine_source_counts = {
        engine: len(rows) for engine, rows in adapter_candidates.items()
    }

    result = {
        "stage": STAGE,
        "status": (
            "PASS_R455_PREBUILD_EXECUTION_SOURCE_INTROSPECTION_COMPLETE"
            if all(authority_checks.values())
            else "BLOCKED_R455_PREBUILD_PARENT_AUTHORITY_FAILURE"
        ),
        "scientific_evidence": False,
        "engine_execution_performed": False,
        "historical_scientific_execution_performed": False,
        "canonical_state_changed": False,
        "purpose": (
            "Recover exact local current historical-adapter/contract invocation "
            "surfaces before constructing R4.55; this helper is not R4.55."
        ),
        "authority_checks": authority_checks,
        "authority_checks_passed": sum(authority_checks.values()),
        "authority_checks_total": len(authority_checks),
        "r452_plan_sha256": plan.get("plan_sha256"),
        "r453_registry_sha256": registry.get("registry_sha256"),
        "job_count": len(plan.get("jobs") or []),
        "planned_stream_count": sum(len(j.get("frozen_seeds") or []) for j in plan.get("jobs") or []),
        "job_contract_summary": {
            "counts": contract_counts,
            "records": contracts,
        },
        "source_candidate_summary": {
            "source_file_count": len(sources),
            "engine_candidate_counts": engine_source_counts,
            "engine_candidates": adapter_candidates,
        },
        "source_records": sources,
        "next_build_requirement": {
            "all_20_r43_contracts_present": contract_counts["present"] == 20,
            "zero_contract_parse_errors": contract_counts["parse_errors"] == 0,
            "all_five_engines_have_local_execution_source_candidates":
                all(engine_source_counts[e] > 0 for e in ENGINE_ORDER),
            "note": (
                "These are necessary prebuild conditions only. R4.55 must still "
                "bind exact functions/CLI/schema and fail closed before any engine "
                "if an invocation surface remains ambiguous."
            ),
        },
    }

    out = root / OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    compact = {
        "stage": STAGE,
        "status": result["status"],
        "authority_checks": f"{sum(authority_checks.values())}/{len(authority_checks)}",
        "job_contracts": contract_counts,
        "source_file_count": len(sources),
        "engine_source_candidate_counts": engine_source_counts,
        "planned_stream_count": result["planned_stream_count"],
        "output": OUT.as_posix(),
        "next_build_requirement": result["next_build_requirement"],
    }
    print(json.dumps(compact, indent=2, ensure_ascii=False))
    return 0 if all(authority_checks.values()) else 3


if __name__ == "__main__":
    raise SystemExit(main())
