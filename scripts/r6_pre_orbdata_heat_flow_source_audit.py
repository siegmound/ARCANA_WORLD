#!/usr/bin/env python3
"""Read-only extraction of qualified ShellSet heat-flow source evidence.

This utility never builds or runs ShellSet. It verifies the exact FAIR checkout
identity before reading any source or parameter files, then writes evidence
reports into the ARCANA working directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Iterable


EXPECTED_BRANCH = "arcana-r6-runtime-capacity"
EXPECTED_COMMIT = "62fd474f229b2676fd9d39c5def45137d22d2481"
EXPECTED_EXECUTABLE_SHA256 = "4c0044fe4332184d63408960a2237d4edb7da891b71f74b82bd1d5a83b27e918"
EXPECTED_PATCH_SHA256 = "e844d78462442a7580469969da8641de9a0992c2a2ee7df0d2f36d6193d3eeb2"

TERMS = (
    "heatFl", "dQdTdA", "needQ", "qArray", "qLim0", "dQL_dE", "qLim1",
    "ageMa", "alphaT", "conduc", "TSurf", "temLim", "TAsthK", "TADIAB",
    "GRADIE", "ZBASTH", "delta_rho_limit",
)
EVIDENCE_CATEGORY_SCHEMA = {
    "WORLD_HISTORY_PHYSICAL_INPUT": {
        "supported_facts": [
            "ARCANA requires surface heat flow or an authorized source with provenance; current candidate manifest has no bound heat-flow artifact.",
            "The oceanic age field is an ARCANA physical input only on its governed ocean support; halo extension does not create authority.",
        ],
        "symbol_assignments": [],
    },
    "SPECIALIST_MODEL_CONFIGURATION": {
        "supported_facts": [
            "The current thermomechanical contract places alphaT, conductivity, surface/reference temperatures, temperature limits, and geotherm controls in specialist configuration; values remain unset.",
        ],
        "symbol_assignments": [],
    },
    "NUMERICAL_GUARD_OR_LIMIT": {"supported_facts": [], "symbol_assignments": []},
    "DERIVED_ORBDATA_STATE": {
        "supported_facts": [
            "The governed ARCANA patch passes nodal heat-flow state through Assign as INOUT and writes it back; exact qualified-source precedence awaits extraction.",
        ],
        "symbol_assignments": [],
    },
    "UNRESOLVED_PENDING_SOURCE_ADJUDICATION": {
        "symbols": list(TERMS),
        "note": "No symbol is automatically assigned to a scientific category from text matches. Adjudicate source excerpts, call order, and parameter bindings after qualified checkout verification.",
    },
}
TEXT_SUFFIXES = {
    ".f", ".for", ".f90", ".f95", ".f03", ".f08", ".inc", ".h",
    ".txt", ".in", ".dat", ".par", ".cfg", ".nml", ".nam",
}
CONTEXT_LINES = 3
MAX_EXCERPTS_PER_TERM = 80
READER_OR_CALL_RE = re.compile(
    r"\b(?:read|call|open|namelist|getreal|getint|getlogical|getchar|getstring|"
    r"getparameter|listvarnames|listvarvalues|parameter)\b",
    re.IGNORECASE,
)


def verify_checkout(root: Path) -> dict[str, str]:
    """Fail closed on any checkout other than the qualified FAIR source."""
    def git_value(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args], check=False, capture_output=True, text=True
        )
        if result.returncode:
            raise ValueError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout.strip()

    branch = git_value("branch", "--show-current")
    commit = git_value("rev-parse", "HEAD")
    git_root = Path(git_value("rev-parse", "--show-toplevel")).resolve()
    if git_root != root.resolve():
        raise ValueError(f"--shellset-root must be the checkout root {git_root}, got {root.resolve()}")
    if branch != EXPECTED_BRANCH:
        raise ValueError(f"unqualified ShellSet branch {branch!r}; expected {EXPECTED_BRANCH!r}")
    if commit != EXPECTED_COMMIT:
        raise ValueError(f"unqualified ShellSet commit {commit}; expected {EXPECTED_COMMIT}")
    return {"branch": branch, "commit": commit}


def ensure_output_outside_source(source_root: Path, output_paths: Iterable[Path]) -> None:
    source = source_root.resolve()
    for output in output_paths:
        resolved = output.resolve()
        if resolved == source or source in resolved.parents:
            raise ValueError(f"refusing to write audit output inside ShellSet checkout: {resolved}")


def iter_text_files(root: Path) -> list[Path]:
    """Return only existing regular tracked text files from the checkout index."""
    root = root.resolve()
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if result.returncode:
        message = os.fsdecode(result.stderr).strip()
        raise ValueError(f"git ls-files -z failed: {message}")

    tracked_paths = [os.fsdecode(item) for item in result.stdout.split(b"\0") if item]
    selected: list[tuple[str, Path]] = []
    for relative_name in tracked_paths:
        candidate = root / Path(relative_name)
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"tracked path resolves outside ShellSet checkout: {relative_name}") from exc
        try:
            mode = candidate.lstat().st_mode
        except OSError as exc:
            raise ValueError(f"tracked path is missing: {relative_name}") from exc
        if not stat.S_ISREG(mode) or not resolved.is_file():
            raise ValueError(f"tracked path is missing or not a regular file: {relative_name}")
        if Path(relative_name).suffix.lower() in TEXT_SUFFIXES:
            selected.append((relative_name, candidate))
    return [path for _, path in sorted(selected, key=lambda entry: entry[0])]


def read_tracked_text_files(root: Path, tracked_text_files: Iterable[Path]) -> dict[Path, str]:
    """Read committed HEAD blobs, never untracked or dirty worktree contents."""
    root = root.resolve()
    contents: dict[Path, str] = {}
    for path in tracked_text_files:
        relative_name = path.relative_to(root).as_posix()
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"HEAD:{relative_name}"],
            check=False,
            capture_output=True,
        )
        if result.returncode:
            message = os.fsdecode(result.stderr).strip()
            raise ValueError(f"cannot read tracked HEAD blob {relative_name}: {message}")
        contents[path] = result.stdout.decode("utf-8", errors="replace")
    return contents


def source_file_authority_record(tracked_text_files_scanned: int) -> dict[str, object]:
    return {
        "method": "GIT_TRACKED_FILES_ONLY",
        "command": "git ls-files -z",
        "untracked_files_scanned": False,
        "tracked_text_files_scanned": tracked_text_files_scanned,
        "content_source": "verified HEAD blobs via git show HEAD:<tracked-path>",
    }


def extract_contexts(root: Path, tracked_text_files: Iterable[Path] | None = None, source_texts: dict[Path, str] | None = None) -> dict[str, list[dict[str, object]]]:
    """Return bounded, line-numbered contexts from source/parameter text only."""
    excerpts: dict[str, list[dict[str, object]]] = {term: [] for term in TERMS}
    terms_folded = {term: term.casefold() for term in TERMS}
    paths = iter_text_files(root) if tracked_text_files is None else tracked_text_files
    for path in paths:
        if source_texts is None:
            source_text = read_tracked_text_files(root, [path])[path]
        else:
            source_text = source_texts[path]
        lines = source_text.splitlines()
        for index, line in enumerate(lines):
            folded = line.casefold()
            for term, needle in terms_folded.items():
                if needle not in folded or len(excerpts[term]) >= MAX_EXCERPTS_PER_TERM:
                    continue
                start = max(0, index - CONTEXT_LINES)
                stop = min(len(lines), index + CONTEXT_LINES + 1)
                excerpts[term].append({
                    "path": path.relative_to(root).as_posix(),
                    "line": index + 1,
                    "context_start_line": start + 1,
                    "context": lines[start:stop],
                })
    return excerpts


def extract_binding_and_callsite_contexts(root: Path, tracked_text_files: Iterable[Path] | None = None, source_texts: dict[Path, str] | None = None) -> list[dict[str, object]]:
    """Capture parameter-reader/binding and call lines near audited symbols."""
    excerpts: list[dict[str, object]] = []
    needles = tuple(term.casefold() for term in TERMS)
    paths = iter_text_files(root) if tracked_text_files is None else tracked_text_files
    for path in paths:
        if source_texts is None:
            source_text = read_tracked_text_files(root, [path])[path]
        else:
            source_text = source_texts[path]
        lines = source_text.splitlines()
        for index, line in enumerate(lines):
            if not READER_OR_CALL_RE.search(line):
                continue
            nearby_start, nearby_stop = max(0, index - 6), min(len(lines), index + 7)
            nearby = "\n".join(lines[nearby_start:nearby_stop]).casefold()
            matched = [term for term, needle in zip(TERMS, needles) if needle in nearby]
            if not matched:
                continue
            start, stop = max(0, index - 4), min(len(lines), index + 5)
            excerpts.append({
                "path": path.relative_to(root).as_posix(),
                "line": index + 1,
                "matched_symbols_in_neighborhood": matched,
                "context_start_line": start + 1,
                "context": lines[start:stop],
            })
            if len(excerpts) >= 300:
                return excerpts
    return excerpts


def build_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# R6 PRE_ORBDATA heat-flow source audit",
        "",
        f"**Decision:** `{payload['decision']}`",
        "",
        "This is source evidence extraction only. It does not choose values, run OrbData/SHELLS, or close the PRE_ORBDATA gate.",
        "",
        "## Qualified source identity",
        "",
        f"- Branch: `{payload['source_identity']['branch']}`",
        f"- Commit: `{payload['source_identity']['commit']}`",
        f"- Expected executable SHA-256 (identity reference; executable not read): `{payload['qualified_executable_sha256']}`",
        f"- Governed patch SHA-256: `{payload['governed_patch_sha256']}`",
        f"- Source-file authority: `{payload['source_file_authority']['method']}` via `{payload['source_file_authority']['command']}`; tracked text files scanned: {payload['source_file_authority']['tracked_text_files_scanned']}; untracked files scanned: false",
        f"- Content source: `{payload['source_file_authority']['content_source']}`",
        "",
        "## Evidence category scaffold",
        "",
        "No source symbol is automatically assigned to a category; the initial item list remains unresolved until contextual source and parameter binding are reviewed.",
        "",
        "| Evidence category | Supported context | Symbol assignments |",
        "|---|---|---|",
    ]
    for category, record in payload["evidence_categories"].items():
        facts = record.get("supported_facts", [])
        context = " ".join(facts) if facts else "Pending source adjudication"
        symbols = ", ".join(record.get("symbol_assignments", record.get("symbols", []))) or "None"
        lines.append(f"| `{category}` | {context} | {symbols} |")
    lines.extend([
        "",
        "## Required excerpts",
        "",
    ])
    excerpts = payload["source_excerpts"]
    for term, hits in excerpts.items():
        lines.extend([f"### `{term}`", ""])
        if not hits:
            lines.extend(["No occurrence found in scanned source/parameter text.", ""])
            continue
        for hit in hits:
            lines.append(f"`{hit['path']}:{hit['line']}`")
            lines.append("```text")
            lines.extend(hit["context"])
            lines.extend(["```", ""])
    lines.extend(["## Parameter readers, bindings and call sites", ""])
    binding_hits = payload["parameter_binding_and_callsite_excerpts"]
    if not binding_hits:
        lines.extend(["No nearby reader/binding/call excerpts found; inspect symbol matches and qualified source manually.", ""])
    for hit in binding_hits:
        lines.append(f"`{hit['path']}:{hit['line']}`; nearby symbols: {', '.join(hit['matched_symbols_in_neighborhood'])}")
        lines.append("```text")
        lines.extend(hit["context"])
        lines.extend(["```", ""])
    lines.extend([
        "## Interpretation status",
        "",
        "Excerpts must be adjudicated against call order, parameter binding and active runtime path. Automated matches do not establish scientific semantics.",
        "",
        "Preserved gates: `PRE_ORBDATA_ready=false`; `t0_orbdata_executed=false`; `shellset_mechanics_authorized=false`; `dt_selected=false`; `t1_created=false`; `forward_evolution_authorized=false`.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shellset-root", required=True, type=Path)
    parser.add_argument("--json-out", type=Path, default=Path("R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_EXTRACTION_FAIR.json"))
    parser.add_argument("--markdown-out", type=Path, default=Path("R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_EXTRACTION_FAIR.md"))
    args = parser.parse_args(argv)
    root = args.shellset_root.resolve()
    try:
        identity = verify_checkout(root)
        ensure_output_outside_source(root, (args.json_out, args.markdown_out))
        tracked_text_files = iter_text_files(root)
        source_texts = read_tracked_text_files(root, tracked_text_files)
    except (OSError, ValueError) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2

    payload: dict[str, object] = {
        "schema": "R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_AUDIT_V1",
        "decision": "R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_AUDIT_SOURCE_EXTRACTED_PENDING_ADJUDICATION",
        "evidence_categories": EVIDENCE_CATEGORY_SCHEMA,
        "source_identity": identity,
        "qualified_executable_sha256": EXPECTED_EXECUTABLE_SHA256,
        "governed_patch_sha256": EXPECTED_PATCH_SHA256,
        "source_root": str(root),
        "source_file_authority": source_file_authority_record(len(source_texts)),
        "source_excerpts": extract_contexts(root, tracked_text_files, source_texts),
        "parameter_binding_and_callsite_excerpts": extract_binding_and_callsite_contexts(root, tracked_text_files, source_texts),
        "interpretation": "Automated contextual matches only; manual source/control-flow and parameter-binding reconciliation remains required.",
        "gates": {
            "pre_orbdata_ready": False,
            "t0_orbdata_executed": False,
            "shellset_mechanics_authorized": False,
            "dt_selected": False,
            "t1_created": False,
            "forward_evolution_authorized": False,
        },
    }
    args.json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(build_markdown(payload), encoding="utf-8")
    print(payload["decision"])
    print(f"JSON={args.json_out}")
    print(f"MARKDOWN={args.markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
