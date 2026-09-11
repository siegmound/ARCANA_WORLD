from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

TARGET_RELATIVE_SUFFIXES = (
    "src/arcana_worldsim/surface/hydrology.py",
    "src/arcana_worldsim/climate/water_balance.py",
    "src/arcana_worldsim/finalization/hydrology.py",
)
TARGET_PAYLOAD = "channel_hydrology_state_I.npz"
SEMANTIC_TERMS = (
    "mean_discharge_m3_s",
    "drainage_area_km2",
    "receiver_flat",
    "lake_candidate_mask",
    "depression_depth_m",
    "precip",
    "rain",
    "evap",
    "evapotrans",
    "runoff",
    "infil",
    "recharge",
    "storage",
    "soil",
    "route",
    "discharge",
    "water_balance",
    "np.savez",
    "savez_compressed",
)
MAX_FILE_BYTES = 2 * 1024 * 1024
EXCERPT_RADIUS = 4
MAX_EXCERPTS = 80


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalized(path: Path) -> str:
    return str(path).replace("\\", "/")


def source_excerpts(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    matched_lines: set[int] = set()
    for i, line in enumerate(lines):
        lower = line.lower()
        if any(term.lower() in lower for term in SEMANTIC_TERMS):
            matched_lines.add(i)
    windows: list[tuple[int, int]] = []
    for i in sorted(matched_lines):
        start = max(0, i - EXCERPT_RADIUS)
        end = min(len(lines), i + EXCERPT_RADIUS + 1)
        if windows and start <= windows[-1][1]:
            windows[-1] = (windows[-1][0], max(windows[-1][1], end))
        else:
            windows.append((start, end))
    records: list[dict[str, Any]] = []
    for start, end in windows[:MAX_EXCERPTS]:
        records.append({
            "start_line": start + 1,
            "end_line": end,
            "text": "\n".join(f"{j+1}: {lines[j]}" for j in range(start, end)),
        })
    return records


def term_presence(text: str) -> dict[str, bool]:
    lower = text.lower()
    return {term: term.lower() in lower for term in SEMANTIC_TERMS}


def assignment_hits(text: str) -> list[str]:
    out: list[str] = []
    patterns = (
        r"mean_discharge_m3_s\s*=",
        r"runoff[^\n]*=",
        r"evap[^\n]*=",
        r"infil[^\n]*=",
        r"recharge[^\n]*=",
        r"storage[^\n]*=",
        r"route_[A-Za-z0-9_]*\(",
        r"_route_[A-Za-z0-9_]*\(",
        r"np\.savez(?:_compressed)?\(",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            line = text.count("\n", 0, match.start()) + 1
            snippet = text.splitlines()[line - 1].strip()
            out.append(f"L{line}: {snippet[:500]}")
    return out[:120]


def inspect_source(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }
    if path.stat().st_size > MAX_FILE_BYTES:
        record["read_skipped"] = "file_too_large"
        return record
    text = path.read_text(encoding="utf-8", errors="replace")
    record["line_count"] = len(text.splitlines())
    record["term_presence"] = term_presence(text)
    record["assignment_hits"] = assignment_hits(text)
    record["target_payload_literal_present"] = TARGET_PAYLOAD.lower() in text.lower()
    record["excerpts"] = source_excerpts(text)
    return record


def discover_targets(root: Path) -> list[Path]:
    records: list[Path] = []
    for path in root.rglob("*.py"):
        if ".git" in path.parts:
            continue
        p = normalized(path).lower()
        if any(p.endswith(suffix.lower()) for suffix in TARGET_RELATIVE_SUFFIXES):
            records.append(path)
    return sorted(records, key=lambda p: normalized(p).lower())


def discover_export_references(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    needles = (
        TARGET_PAYLOAD.lower(),
        "mean_discharge_m3_s",
        "savez",
        "physical_finalization",
        "v0_5_5i_sealed",
    )
    for path in root.rglob("*.py"):
        if ".git" in path.parts:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lower = text.lower()
        if not any(n in lower for n in needles):
            continue
        hits: list[dict[str, Any]] = []
        for i, line in enumerate(text.splitlines(), start=1):
            ll = line.lower()
            matched = [n for n in needles if n in ll]
            if matched:
                hits.append({"line": i, "terms": matched, "text": line[:1000]})
                if len(hits) >= 80:
                    break
        if hits:
            records.append({
                "path": str(path.resolve()),
                "sha256": sha256_file(path),
                "hits": hits,
            })
    return records


def classify(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_suffix: dict[str, list[dict[str, Any]]] = {suffix: [] for suffix in TARGET_RELATIVE_SUFFIXES}
    for record in records:
        rp = record["path"].replace("\\", "/").lower()
        for suffix in TARGET_RELATIVE_SUFFIXES:
            if rp.endswith(suffix.lower()):
                by_suffix[suffix].append(record)

    def any_term(suffix: str, term: str) -> bool:
        return any(r.get("term_presence", {}).get(term, False) for r in by_suffix[suffix])

    structural = (
        any_term(TARGET_RELATIVE_SUFFIXES[0], "receiver_flat")
        and any_term(TARGET_RELATIVE_SUFFIXES[0], "drainage_area_km2")
        and any_term(TARGET_RELATIVE_SUFFIXES[0], "depression_depth_m")
    )
    wb_terms = ("precip", "evap", "runoff", "storage", "soil", "route")
    water_balance_signal_count = sum(any_term(TARGET_RELATIVE_SUFFIXES[1], t) for t in wb_terms)
    water_balance = water_balance_signal_count >= 3
    finalized_discharge = any_term(TARGET_RELATIVE_SUFFIXES[2], "mean_discharge_m3_s")

    hashes_by_suffix = {
        suffix: sorted({r.get("sha256") for r in group if r.get("sha256")})
        for suffix, group in by_suffix.items()
    }

    return {
        "structural_hydrology_semantics_recovered": structural,
        "water_balance_semantics_recovered": water_balance,
        "water_balance_signal_count": water_balance_signal_count,
        "finalized_mean_discharge_semantics_recovered": finalized_discharge,
        "hashes_by_relative_suffix": hashes_by_suffix,
        "target_class_counts": {suffix: len(group) for suffix, group in by_suffix.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="R5.17-B6-H3: semantic audit of recovered native ARCANA hydrology generator lineage; historical source is never executed.")
    parser.add_argument("--search-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("R5_17_B6_H3_NATIVE_HYDROLOGY_GENERATOR_SEMANTICS.json"))
    args = parser.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    targets = discover_targets(root)
    inspected = [inspect_source(path) for path in targets]
    export_refs = discover_export_references(root)
    adjudication = classify(inspected)

    if (
        adjudication["structural_hydrology_semantics_recovered"]
        and adjudication["water_balance_semantics_recovered"]
        and adjudication["finalized_mean_discharge_semantics_recovered"]
    ):
        status = "PASS_R517_B6_H3_NATIVE_HYDROLOGY_GENERATOR_SEMANTICS_RECOVERED"
    else:
        status = "BLOCKED_R517_B6_H3_NATIVE_HYDROLOGY_GENERATOR_SEMANTICS_INCOMPLETE"

    result = {
        "schema": "ARCANA_R5_17_B6_H3_NATIVE_HYDROLOGY_GENERATOR_SEMANTICS_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-H3",
        "purpose": "Determine whether recovered ARCANA source already contains structural hydrology, climatic water-balance, and finalized mean-discharge semantics before any external provider is authorized.",
        "search_root": str(root),
        "target_sources": list(TARGET_RELATIVE_SUFFIXES),
        "target_payload": TARGET_PAYLOAD,
        "source_candidate_count": len(inspected),
        "sources": inspected,
        "export_reference_file_count": len(export_refs),
        "export_references": export_refs,
        "semantic_adjudication": adjudication,
        "payload_materialized": False,
        "payload_authority_identity_adjudicated": False,
        "exact_v0_5_5I_generator_identity_adjudicated": False,
        "reuse_canonical_arcana_authorized": False,
        "external_provider_authorized": False,
        "source_executed": False,
        "new_historical_simulation": False,
        "canonical_mutation": False,
        "status": status,
        "next_if_pass": "R5.17-B6-H4_EXACT_V055I_EXPORT_LINEAGE_AND_PHYSICAL_SUFFICIENCY_ADJUDICATION",
        "next_if_blocked": "R5.17-B6_SCIENTIFIC_ENGINE_SUITABILITY_ADJUDICATION_WITH_NATIVE_SEMANTIC_GAP_RECORDED",
    }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "source_candidate_count": len(inspected),
        "export_reference_file_count": len(export_refs),
        **adjudication,
        "output": str(args.output.resolve()),
    }, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
