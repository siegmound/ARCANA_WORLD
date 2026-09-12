from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MD_OUT = ROOT / "ARCANA_EXECUTION_REFERENCE_INDEX.md"
JSON_OUT = ROOT / "ARCANA_EXECUTION_REFERENCE_INDEX.json"

SELF_EXCLUDED = {
    "ARCANA_EXECUTION_REFERENCE_INDEX.md",
    "ARCANA_EXECUTION_REFERENCE_INDEX.json",
}


def run_git(*args: str) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return cp.stdout


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate_paths() -> list[str]:
    # Index only repository-authoritative paths: already tracked or staged in
    # the index. Untracked scratch/reconstruction residue is intentionally
    # excluded so the index never points at local-only files.
    cached = set(run_git("ls-files").splitlines())
    return sorted(cached - SELF_EXCLUDED)


def is_reference_surface(path: str) -> bool:
    p = path.replace("\\", "/")
    name = Path(p).name
    upper = name.upper()
    suffix = Path(p).suffix.lower()

    if p.startswith(".git/"):
        return False

    if upper.startswith("README"):
        return True

    if suffix == ".ps1":
        return True

    if any(
        token in upper
        for token in (
            "STATUS",
            "CONTRACT",
            "AUDIT",
            "SUMMARY",
            "MANIFEST",
            "AUTHORITY",
            "HANDOFF",
            "PROTOCOL",
            "PREFLIGHT",
            "EVIDENCE",
            "SEAL",
            "RECONCILIATION",
            "RECOVERY",
        )
    ):
        return True

    if p.startswith("configs/") and suffix == ".json":
        return True

    if re.search(r"(?i)^R5_17_B[67]_", p) and suffix in {".json", ".md", ".py", ".ps1"}:
        return True

    if p.startswith("benchmarks/") and suffix in {
        ".py", ".ps1", ".sh", ".r", ".ini"
    }:
        return True

    if suffix == ".py":
        if re.search(r"(?i)(^|/)(R[345][_-]\d+|run_|capture_|check_)", p):
            return True
        if "scientific_engines" in p:
            return True

    if p in {
        "SIMULATION_RESULTS/SEMANTIC_CATALOG.md",
        "ARCANA_WORLD_CURRENT_STATE.md",
    }:
        return True

    return False


def category(path: str) -> str:
    p = path.replace("\\", "/")
    name = Path(p).name
    upper = name.upper()
    suffix = Path(p).suffix.lower()

    if p == "ARCANA_WORLD_CURRENT_STATE.md":
        return "CURRENT_STATE"
    if p == "SIMULATION_RESULTS/SEMANTIC_CATALOG.md":
        return "SEMANTIC_CATALOG"
    if upper.startswith("README"):
        return "README"
    if suffix == ".ps1":
        return "POWERSHELL_RUNNER"
    if "CONTRACT" in upper or "PROTOCOL" in upper:
        return "CONTRACT_PROTOCOL"
    if "AUDIT" in upper:
        return "AUDIT"
    if "STATUS" in upper:
        return "STATUS"
    if "HANDOFF" in upper:
        return "HANDOFF"
    if "AUTHORITY" in upper and suffix == ".json":
        return "AUTHORITY_JSON"
    if "MANIFEST" in upper:
        return "MANIFEST"
    if "SUMMARY" in upper:
        return "RESULT_SUMMARY"
    if p.startswith("configs/"):
        return "CONFIG"
    if p.startswith("benchmarks/"):
        return "BENCHMARK_EXECUTOR"
    if suffix == ".py":
        return "PYTHON_RUNNER_SOURCE"
    return "REFERENCE"


def normalize_stage(raw: str) -> str:
    return raw.replace("_", ".").replace("-", ".")


def stage_key(path: str) -> str:
    text = path.replace("\\", "/")

    patterns = [
        r"(?i)R5[_-]17[_-]B\d+(?:[_-][A-Z]\d+[A-Z0-9]*)?",
        r"(?i)R5[_-]\d+(?:[_-][A-Z]\d+[A-Z0-9]*)?",
        r"(?i)R4[_-]\d+(?:[_-]R\d+[A-Z0-9]*)?",
        r"(?i)R3[_-]\d+[A-Z]?(?:[_-]R\d+[A-Z0-9]*)?",
    ]

    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return normalize_stage(m.group(0).upper())

    version = re.search(r"(?i)v0[_-]6D1(?:[_-]R\d+[A-Z0-9_]*)?", text)
    if version:
        return normalize_stage(version.group(0).upper())

    return "UNSCOPED"


def title_from_file(path: Path) -> str:
    if path.suffix.lower() not in {
        ".md", ".txt", ".ps1", ".py", ".json", ".r", ".sh", ".ini"
    }:
        return ""

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return ""

    for line in text.splitlines()[:80]:
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped.startswith("## "):
            return stripped[3:].strip()

    return ""


def git_blob_oid(path: str) -> str | None:
    try:
        out = run_git("ls-files", "-s", "--", path).strip()
    except subprocess.CalledProcessError:
        return None

    if not out:
        return None

    first = out.splitlines()[0].split()
    if len(first) >= 2:
        return first[1]

    return None


def build_record(path_str: str) -> dict[str, Any]:
    path = ROOT / path_str
    stat = path.stat()

    return {
        "path": path_str.replace("\\", "/"),
        "stage": stage_key(path_str),
        "category": category(path_str),
        "title": title_from_file(path),
        "extension": path.suffix.lower(),
        "size_bytes": stat.st_size,
        "git_blob_oid": git_blob_oid(path_str),
        "sha256": sha256_file(path),
    }


def md_escape(value: str) -> str:
    return (
        value.replace("|", r"\|")
        .replace("\n", " ")
        .strip()
    )


def main() -> int:
    head = run_git("rev-parse", "HEAD").strip()
    now = datetime.now(timezone.utc).isoformat()

    paths = [
        p
        for p in candidate_paths()
        if is_reference_surface(p)
        and (ROOT / p).is_file()
    ]

    records = [build_record(p) for p in paths]
    records.sort(
        key=lambda r: (
            r["stage"],
            r["category"],
            r["path"],
        )
    )

    category_counts = Counter(r["category"] for r in records)
    stage_counts = Counter(r["stage"] for r in records)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["stage"]].append(record)

    payload = {
        "schema": "ARCANA_EXECUTION_REFERENCE_INDEX_V1",
        "generated_utc": now,
        "repository_head": head,
        "purpose": (
            "Reusable lookup surface for README/status/contracts/audits, "
            "execution runners, configs, manifests and result summaries "
            "that may be required by future replay/regression tests."
        ),
        "record_count": len(records),
        "category_counts": dict(sorted(category_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "records": records,
    }

    JSON_OUT.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    lines: list[str] = []
    lines.append("# ARCANA Execution & Reference Index")
    lines.append("")
    lines.append(
        "Machine-readable companion: `ARCANA_EXECUTION_REFERENCE_INDEX.json`."
    )
    lines.append("")
    lines.append(f"- Repository HEAD at generation: `{head}`")
    lines.append(f"- Generated UTC: `{now}`")
    lines.append(f"- Indexed reference files: **{len(records)}**")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "This index links historical documentation and execution surfaces "
        "that may be needed for future replay, regression, provenance or "
        "semantic tests. It intentionally indexes README/status/contracts/"
        "audits together with PowerShell/Python runners, configs, manifests "
        "and compact result summaries."
    )
    lines.append("")
    lines.append(
        "The index is navigational evidence only. It does not promote an "
        "indexed file to scientific or canonical authority."
    )
    lines.append("")
    lines.append("## Category counts")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---:|")
    for key, value in sorted(category_counts.items()):
        lines.append(f"| {md_escape(key)} | {value} |")
    lines.append("")
    lines.append("## Stage index")
    lines.append("")

    for stage in sorted(grouped):
        lines.append(f"### {stage}")
        lines.append("")
        lines.append("| Kind | Path | Title | Git blob | SHA256 |")
        lines.append("|---|---|---|---|---|")

        for r in grouped[stage]:
            blob = r["git_blob_oid"] or "UNTRACKED_AT_GENERATION"
            title = r["title"] or ""
            lines.append(
                "| "
                + md_escape(r["category"])
                + " | `"
                + r["path"]
                + "` | "
                + md_escape(title)
                + " | `"
                + blob
                + "` | `"
                + r["sha256"]
                + "` |"
            )

        lines.append("")

    lines.append("## Regeneration")
    lines.append("")
    lines.append(
        "Run `python tools/build_arcana_execution_reference_index.py` "
        "from the repository root after adding significant new execution "
        "or reference surfaces."
    )
    lines.append("")

    MD_OUT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "PASS_ARCANA_EXECUTION_REFERENCE_INDEX_BUILT",
                "repository_head": head,
                "record_count": len(records),
                "markdown": str(MD_OUT),
                "json": str(JSON_OUT),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
