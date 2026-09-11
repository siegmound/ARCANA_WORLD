from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

TARGET_PAYLOAD = "channel_hydrology_state_I.npz"
TARGET_LINEAGE = "v0_5_5I_SEALED"

EXPECTED_SOURCES = {
    "src/arcana_worldsim/surface/hydrology.py": "34584d0e8a8696b26e4026aad28f362850b7e9b98bb7754cc5cab8e4d282ff42",
    "src/arcana_worldsim/regional/hydrology.py": "e32d766e3e700dd2da22adda3c09b0327e503d1ab9df663eb1c23e6730832b87",
    "src/arcana_worldsim/climate/water_balance.py": "23090416ef8234d43689171241d80d8ca2609882455bd30761de30301e5bfb61",
    "src/arcana_worldsim/finalization/hydrology.py": "29c808bd889d3f0c6e5390775d8751f68b9c9dd2cb5bab1736d6ad6cc6486351",
}

TEXT_SUFFIXES = {".py", ".json", ".md", ".ps1", ".txt", ".yaml", ".yml", ".toml"}
MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_HITS_PER_FILE = 120
EXCERPT_RADIUS = 5

PHYSICAL_TERMS = (
    "precip",
    "rain",
    "evapotrans",
    "evap",
    "infiltration",
    "groundwater_return",
    "cryo_storage",
    "surplus",
    "runoff",
    "runoff_volume_m3_yr",
    "monthly_runoff_mm",
    "annual_runoff_mm_yr",
    "storage",
    "route",
    "receiver_flat",
    "drainage_area_km2",
    "lake_candidate_mask",
    "depression_depth_m",
    "mean_discharge_m3_s",
    "m3_s",
    "m3_yr",
    "mm_yr",
    "mm_month",
    "31557600",
    "365.25",
)

LINK_TERMS = (
    TARGET_PAYLOAD,
    TARGET_LINEAGE,
    "mean_discharge_m3_s",
    "physical_finalization",
    "finalization/hydrology.py",
    "climate/water_balance.py",
    "savez",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def excerpt_records(text: str, needles: tuple[str, ...]) -> list[dict[str, Any]]:
    lines = text.splitlines()
    hits: list[int] = []
    for idx, line in enumerate(lines):
        lower = line.lower()
        if any(n.lower() in lower for n in needles):
            hits.append(idx)
    windows: list[tuple[int, int]] = []
    for idx in hits:
        start = max(0, idx - EXCERPT_RADIUS)
        end = min(len(lines), idx + EXCERPT_RADIUS + 1)
        if windows and start <= windows[-1][1]:
            windows[-1] = (windows[-1][0], max(windows[-1][1], end))
        else:
            windows.append((start, end))
    out: list[dict[str, Any]] = []
    for start, end in windows[:MAX_HITS_PER_FILE]:
        out.append({
            "start_line": start + 1,
            "end_line": end,
            "text": "\n".join(f"{i+1}: {lines[i]}" for i in range(start, end)),
        })
    return out


def term_presence(text: str, terms: tuple[str, ...]) -> dict[str, bool]:
    low = text.lower()
    return {term: term.lower() in low for term in terms}


def locate_exact_sources(root: Path) -> dict[str, list[dict[str, Any]]]:
    found: dict[str, list[dict[str, Any]]] = {suffix: [] for suffix in EXPECTED_SOURCES}
    for path in root.rglob("*.py"):
        if ".git" in path.parts:
            continue
        p = norm(path).lower()
        matched_suffix = next((s for s in EXPECTED_SOURCES if p.endswith(s.lower())), None)
        if not matched_suffix:
            continue
        try:
            digest = sha256_file(path)
            text = read_text(path) if path.stat().st_size <= MAX_TEXT_BYTES else ""
        except OSError:
            continue
        found[matched_suffix].append({
            "path": str(path.resolve()),
            "sha256": digest,
            "matches_expected_sha256": digest == EXPECTED_SOURCES[matched_suffix],
            "term_presence": term_presence(text, PHYSICAL_TERMS) if text else {},
            "physical_excerpts": excerpt_records(text, PHYSICAL_TERMS) if text else [],
        })
    return found


def source_roots(exact_sources: dict[str, list[dict[str, Any]]]) -> list[Path]:
    roots: set[Path] = set()
    marker = "/src/arcana_worldsim/"
    for records in exact_sources.values():
        for rec in records:
            if not rec.get("matches_expected_sha256"):
                continue
            p = norm(rec["path"])
            pos = p.lower().find(marker)
            if pos > 0:
                roots.add(Path(p[:pos]))
    return sorted(roots, key=lambda p: norm(p).lower())


def scan_direct_links(package_roots: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in package_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            key = str(path.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            try:
                if path.stat().st_size > MAX_TEXT_BYTES:
                    continue
                text = read_text(path)
            except OSError:
                continue
            low = text.lower()
            matched = [term for term in LINK_TERMS if term.lower() in low]
            if not matched:
                continue
            records.append({
                "path": str(path.resolve()),
                "sha256": sha256_file(path),
                "matched_terms": matched,
                "excerpts": excerpt_records(text, tuple(matched)),
            })
    return records


def scan_zip_links(root: Path) -> list[dict[str, Any]]:
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
                    lname = info.filename.lower()
                    if not any(x in lname for x in ("hydro", "manifest", "seal", "final", "export", "water_balance")):
                        continue
                    with zf.open(info, "r") as stream:
                        data = stream.read()
                    text = data.decode("utf-8", errors="replace")
                    low = text.lower()
                    matched = [term for term in LINK_TERMS if term.lower() in low]
                    if not matched:
                        continue
                    records.append({
                        "archive": str(archive.resolve()),
                        "member": info.filename,
                        "sha256": sha256_bytes(data),
                        "matched_terms": matched,
                        "excerpts": excerpt_records(text, tuple(matched)),
                    })
        except (zipfile.BadZipFile, OSError):
            continue
    return records


def inspect_physical_chain(exact_sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    exact = {
        suffix: [r for r in records if r.get("matches_expected_sha256")]
        for suffix, records in exact_sources.items()
    }

    def any_term(suffix: str, term: str) -> bool:
        return any(r.get("term_presence", {}).get(term, False) for r in exact[suffix])

    surface = "src/arcana_worldsim/surface/hydrology.py"
    regional = "src/arcana_worldsim/regional/hydrology.py"
    water = "src/arcana_worldsim/climate/water_balance.py"
    final = "src/arcana_worldsim/finalization/hydrology.py"

    structural_chain = (
        any_term(surface, "receiver_flat")
        and any_term(surface, "depression_depth_m")
        and any_term(regional, "drainage_area_km2")
        and any_term(final, "lake_candidate_mask")
    )

    water_signals = {
        "precipitation": any_term(water, "precip") or any_term(water, "rain"),
        "evapotranspiration": any_term(water, "evapotrans") or any_term(water, "evap"),
        "infiltration": any_term(water, "infiltration"),
        "groundwater_return": any_term(water, "groundwater_return"),
        "cryo_storage": any_term(water, "cryo_storage"),
        "runoff": any_term(water, "runoff"),
        "routing": any_term(water, "route") and any_term(water, "receiver_flat"),
        "storage": any_term(water, "storage"),
    }

    finalized = {
        "monthly_runoff": any_term(final, "monthly_runoff_mm"),
        "annual_runoff": any_term(final, "annual_runoff_mm_yr"),
        "mean_discharge": any_term(final, "mean_discharge_m3_s"),
        "drainage_area": any_term(final, "drainage_area_km2"),
        "lake_mask": any_term(final, "lake_candidate_mask"),
    }

    unit_signals = {
        "runoff_volume_m3_yr": any_term(water, "runoff_volume_m3_yr") or any_term(final, "runoff_volume_m3_yr"),
        "annual_runoff_mm_yr": any_term(final, "annual_runoff_mm_yr"),
        "mean_discharge_m3_s": any_term(final, "mean_discharge_m3_s"),
        "seconds_per_year_literal": any_term(final, "31557600") or any_term(final, "365.25"),
    }

    full_water_balance = all(
        water_signals[k]
        for k in ("precipitation", "evapotranspiration", "infiltration", "runoff", "routing")
    )
    reliability_supporting_semantics = (
        water_signals["storage"]
        or water_signals["groundwater_return"]
        or water_signals["cryo_storage"]
    )
    finalized_discharge = finalized["annual_runoff"] and finalized["mean_discharge"]
    units_recovered = (
        unit_signals["annual_runoff_mm_yr"]
        and unit_signals["mean_discharge_m3_s"]
    )

    all_expected_source_hashes_recovered = all(bool(exact[s]) for s in EXPECTED_SOURCES)
    physical_chain_evidence_complete = (
        all_expected_source_hashes_recovered
        and structural_chain
        and full_water_balance
        and finalized_discharge
        and units_recovered
    )

    return {
        "structural_chain_recovered": structural_chain,
        "water_balance_signals": water_signals,
        "full_water_balance_chain_recovered": full_water_balance,
        "reliability_supporting_semantics_recovered": reliability_supporting_semantics,
        "finalization_signals": finalized,
        "unit_signals": unit_signals,
        "finalized_discharge_chain_recovered": finalized_discharge,
        "units_semantics_recovered": units_recovered,
        "all_expected_source_hashes_recovered": all_expected_source_hashes_recovered,
        "physical_chain_evidence_complete": physical_chain_evidence_complete,
        "physical_sufficiency_adjudicated": False,
        "physical_sufficiency_reason": (
            "Source/hash/equation/unit evidence may be complete, but scientific sufficiency requires explicit review of the recovered formulas, parameter assumptions, calibration scope, and temporal applicability."
        ),
    }


def link_classification(records: list[dict[str, Any]]) -> dict[str, Any]:
    exact_payload_refs = []
    lineage_refs = []
    for rec in records:
        terms = {str(t).lower() for t in rec.get("matched_terms", [])}
        if TARGET_PAYLOAD.lower() in terms:
            exact_payload_refs.append(rec)
        if TARGET_LINEAGE.lower() in terms:
            lineage_refs.append(rec)

    strong_links = []
    for rec in exact_payload_refs:
        terms = {str(t).lower() for t in rec.get("matched_terms", [])}
        if "mean_discharge_m3_s" in terms or "savez" in terms or TARGET_LINEAGE.lower() in terms:
            strong_links.append(rec)

    return {
        "exact_payload_reference_count": len(exact_payload_refs),
        "lineage_reference_count": len(lineage_refs),
        "strong_export_link_count": len(strong_links),
        "exact_payload_references": exact_payload_refs,
        "strong_export_links": strong_links,
        "exact_export_lineage_recovered": bool(strong_links),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "R5.17-B6-H4: capture exact-source, export-lineage, equation and unit evidence for native ARCANA hydrology. "
            "Historical source is not executed and scientific sufficiency is not auto-promoted from lexical evidence."
        )
    )
    parser.add_argument("--search-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("R5_17_B6_H4_EXACT_EXPORT_AND_PHYSICAL_SUFFICIENCY.json"))
    args = parser.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    exact_sources = locate_exact_sources(root)
    roots = source_roots(exact_sources)
    direct_links = scan_direct_links(roots)
    zip_links = scan_zip_links(root)
    all_links = [*direct_links, *zip_links]

    physical = inspect_physical_chain(exact_sources)
    links = link_classification(all_links)

    exact_generator_identity_adjudicated = (
        physical["all_expected_source_hashes_recovered"]
        and links["exact_export_lineage_recovered"]
    )

    if exact_generator_identity_adjudicated and physical["physical_chain_evidence_complete"]:
        status = "PASS_R517_B6_H4_EXPORT_LINEAGE_AND_PHYSICAL_EVIDENCE_CAPTURED"
    elif physical["physical_chain_evidence_complete"]:
        status = "PARTIAL_R517_B6_H4_PHYSICAL_EVIDENCE_CAPTURED_EXACT_V055I_EXPORT_LINK_NOT_ADJUDICATED"
    else:
        status = "BLOCKED_R517_B6_H4_NATIVE_HYDROLOGY_PHYSICAL_EVIDENCE_INCOMPLETE"

    result = {
        "schema": "ARCANA_R5_17_B6_H4_EXACT_EXPORT_AND_PHYSICAL_EVIDENCE_V2",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-H4",
        "purpose": "Capture exact export-lineage and physical equation/unit evidence for recovered ARCANA hydrology before a separate scientific-sufficiency and engine-suitability adjudication.",
        "search_root": str(root),
        "target_payload": TARGET_PAYLOAD,
        "target_lineage": TARGET_LINEAGE,
        "expected_source_hashes": EXPECTED_SOURCES,
        "exact_source_candidates": exact_sources,
        "matching_source_roots": [str(p) for p in roots],
        "direct_link_evidence": direct_links,
        "zip_link_evidence": zip_links,
        "physical_semantics": physical,
        "export_lineage": links,
        "exact_v0_5_5I_generator_identity_adjudicated": exact_generator_identity_adjudicated,
        "reuse_canonical_arcana_candidate": physical["physical_chain_evidence_complete"],
        "reuse_canonical_arcana_authorized": False,
        "external_provider_authorized": False,
        "freshwater_support_materialized": False,
        "hydrological_reliability_materialized": False,
        "source_executed": False,
        "new_historical_simulation": False,
        "canonical_mutation": False,
        "status": status,
        "next_if_pass": "R5.17-B6-H5_SCIENTIFIC_SUFFICIENCY_AND_ENGINE_SUITABILITY_ADJUDICATION",
        "next_if_partial": "R5.17-B6-H5_SCIENTIFIC_SUFFICIENCY_AND_ENGINE_SUITABILITY_WITH_EXPORT_PROVENANCE_GAP_RECORDED",
        "next_if_blocked": "R5.17-B6_SCIENTIFIC_ENGINE_SUITABILITY_WITH_NATIVE_PHYSICAL_GAP_RECORDED",
    }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "matching_source_root_count": len(roots),
        "direct_link_evidence_count": len(direct_links),
        "zip_link_evidence_count": len(zip_links),
        "all_expected_source_hashes_recovered": physical["all_expected_source_hashes_recovered"],
        "structural_chain_recovered": physical["structural_chain_recovered"],
        "full_water_balance_chain_recovered": physical["full_water_balance_chain_recovered"],
        "reliability_supporting_semantics_recovered": physical["reliability_supporting_semantics_recovered"],
        "finalized_discharge_chain_recovered": physical["finalized_discharge_chain_recovered"],
        "units_semantics_recovered": physical["units_semantics_recovered"],
        "physical_chain_evidence_complete": physical["physical_chain_evidence_complete"],
        "physical_sufficiency_adjudicated": physical["physical_sufficiency_adjudicated"],
        "exact_payload_reference_count": links["exact_payload_reference_count"],
        "strong_export_link_count": links["strong_export_link_count"],
        "exact_export_lineage_recovered": links["exact_export_lineage_recovered"],
        "exact_v0_5_5I_generator_identity_adjudicated": exact_generator_identity_adjudicated,
        "output": str(args.output.resolve()),
    }, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
