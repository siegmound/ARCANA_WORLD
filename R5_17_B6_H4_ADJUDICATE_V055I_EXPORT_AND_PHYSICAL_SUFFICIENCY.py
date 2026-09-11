from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

TARGET_PAYLOAD = "channel_hydrology_state_I.npz"
TARGET_INPUT_DIR = "v0_5_5I_SEALED"
TARGET_HASHES = {
    "surface_hydrology": "34584d0e8a8696b26e4026aad28f362850b7e9b98bb7754cc5cab8e4d282ff42",
    "regional_hydrology": "e32d766e3e700dd2da22adda3c09b0327e503d1ab9df663eb1c23e6730832b87",
    "water_balance": "23090416ef8234d43689171241d80d8ca2609882455bd30761de30301e5bfb61",
    "finalization_hydrology": "29c808bd889d3f0c6e5390775d8751f68b9c9dd2cb5bab1736d6ad6cc6486351",
}
TARGET_SUFFIXES = {
    "surface_hydrology": "src/arcana_worldsim/surface/hydrology.py",
    "regional_hydrology": "src/arcana_worldsim/regional/hydrology.py",
    "water_balance": "src/arcana_worldsim/climate/water_balance.py",
    "finalization_hydrology": "src/arcana_worldsim/finalization/hydrology.py",
}
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".ps1", ".yaml", ".yml", ".toml"}
MAX_FILE_BYTES = 4 * 1024 * 1024

PHYSICAL_TERMS = (
    "precip", "rain", "evap", "evapotrans", "infil", "groundwater",
    "runoff", "storage", "cryo", "snow", "ice", "route", "discharge",
    "mean_discharge_m3_s", "monthly_runoff_mm", "annual_runoff_mm_yr",
    "runoff_volume_m3_yr", "drainage_area_km2", "receiver_flat",
    "lake_candidate_mask", "depression_depth_m",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(path: Path) -> str:
    return str(path).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def locate_target_sources(root: Path) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {k: [] for k in TARGET_SUFFIXES}
    for path in root.rglob("*.py"):
        if ".git" in path.parts:
            continue
        np = norm(path).lower()
        for key, suffix in TARGET_SUFFIXES.items():
            if np.endswith(suffix.lower()):
                sha = sha256_file(path)
                out[key].append({
                    "path": str(path.resolve()),
                    "sha256": sha,
                    "matches_expected_hash": sha == TARGET_HASHES[key],
                })
    return out


def line_hits(text: str, needles: tuple[str, ...], limit: int = 120) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        ll = line.lower()
        matched = [n for n in needles if n.lower() in ll]
        if matched:
            hits.append({"line": i, "terms": matched, "text": line[:1200]})
            if len(hits) >= limit:
                break
    return hits


def discover_export_lineage(root: Path) -> list[dict[str, Any]]:
    needles = (
        TARGET_PAYLOAD,
        TARGET_INPUT_DIR,
        "physical_finalization",
        "finalization.hydrology",
        "mean_discharge_m3_s",
        "savez",
        "savez_compressed",
    )
    records: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            text = read_text(path)
        except OSError:
            continue
        hits = line_hits(text, needles)
        if hits:
            records.append({
                "path": str(path.resolve()),
                "sha256": sha256_file(path),
                "hits": hits,
                "contains_target_payload_literal": TARGET_PAYLOAD.lower() in text.lower(),
                "contains_target_input_dir_literal": TARGET_INPUT_DIR.lower() in text.lower(),
            })
    return records


def inspect_physical_model(root: Path) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    by_key = locate_target_sources(root)
    for key, group in by_key.items():
        exact = [g for g in group if g["matches_expected_hash"]]
        records: list[dict[str, Any]] = []
        for item in exact:
            path = Path(item["path"])
            text = read_text(path)
            presence = {term: term.lower() in text.lower() for term in PHYSICAL_TERMS}
            equations = []
            patterns = (
                r"effective_runoff_fraction\s*=.*",
                r"runoff\s*=.*",
                r"surplus\s*=.*",
                r".*groundwater.*=.*",
                r".*cryo.*=.*",
                r".*storage.*=.*",
                r".*discharge.*=.*",
                r"mean_discharge_m3_s\s*=.*",
                r".*31557600.*",
                r".*365\.25.*",
            )
            for i, line in enumerate(text.splitlines(), start=1):
                if any(re.search(p, line, flags=re.IGNORECASE) for p in patterns):
                    equations.append({"line": i, "text": line.strip()[:1200]})
                    if len(equations) >= 100:
                        break
            records.append({**item, "term_presence": presence, "equation_hits": equations})
        evidence[key] = records
    return evidence


def any_presence(records: list[dict[str, Any]], term: str) -> bool:
    return any(r.get("term_presence", {}).get(term, False) for r in records)


def adjudicate(sources: dict[str, list[dict[str, Any]]], exports: list[dict[str, Any]]) -> dict[str, Any]:
    all_hashes_exact = all(any(r.get("matches_expected_hash") for r in sources[k]) for k in TARGET_HASHES)

    wb = sources["water_balance"]
    fin = sources["finalization_hydrology"]
    surf = sources["surface_hydrology"]
    reg = sources["regional_hydrology"]

    water_balance_components = {
        "precipitation": any_presence(wb, "precip") or any_presence(wb, "rain"),
        "evapotranspiration": any_presence(wb, "evapotrans") or any_presence(wb, "evap"),
        "infiltration": any_presence(wb, "infil"),
        "groundwater_return": any_presence(wb, "groundwater"),
        "storage": any_presence(wb, "storage"),
        "cryo_storage": any_presence(wb, "cryo") or any_presence(wb, "snow") or any_presence(wb, "ice"),
        "runoff": any_presence(wb, "runoff"),
        "network_routing": any_presence(wb, "route") and any_presence(wb, "receiver_flat"),
    }
    discharge_components = {
        "mean_discharge_m3_s": any_presence(fin, "mean_discharge_m3_s"),
        "runoff_volume_m3_yr": any_presence(fin, "runoff_volume_m3_yr") or any_presence(wb, "runoff_volume_m3_yr"),
        "runoff_depth": any_presence(fin, "annual_runoff_mm_yr") or any_presence(fin, "monthly_runoff_mm"),
        "drainage_area": any_presence(fin, "drainage_area_km2") or any_presence(reg, "drainage_area_km2"),
    }
    structural_components = {
        "receiver_network": any_presence(surf, "receiver_flat") or any_presence(reg, "receiver_flat"),
        "depressions": any_presence(surf, "depression_depth_m") or any_presence(reg, "depression_depth_m"),
        "lakes": any_presence(reg, "lake_candidate_mask") or any_presence(fin, "lake_candidate_mask"),
        "drainage_area": discharge_components["drainage_area"],
    }

    payload_literal_refs = [r for r in exports if r.get("contains_target_payload_literal")]
    v055i_refs = [r for r in exports if r.get("contains_target_input_dir_literal")]
    direct_bridge_refs = [
        r for r in exports
        if r.get("contains_target_payload_literal") and r.get("contains_target_input_dir_literal")
    ]

    physical_water_balance_sufficient = all(water_balance_components.values())
    discharge_semantics_sufficient = all(discharge_components.values())
    structural_semantics_sufficient = all(structural_components.values())

    # Exact generator identity requires documentary/export evidence that bridges the
    # recovered generator lineage to the named v0.5.5I payload, not merely matching semantics.
    exact_generator_identity_adjudicated = bool(direct_bridge_refs) and all_hashes_exact

    reuse_canonical_arcana_authorized = (
        all_hashes_exact
        and physical_water_balance_sufficient
        and discharge_semantics_sufficient
        and structural_semantics_sufficient
    )

    if reuse_canonical_arcana_authorized and exact_generator_identity_adjudicated:
        status = "PASS_R517_B6_H4_V055I_EXPORT_LINEAGE_AND_PHYSICAL_SUFFICIENCY_ADJUDICATED"
        decision = "REUSE_CANONICAL_ARCANA"
    elif reuse_canonical_arcana_authorized:
        status = "PASS_R517_B6_H4_PHYSICAL_SUFFICIENCY_RECOVERED_WITH_EXACT_V055I_EXPORT_IDENTITY_GAP"
        decision = "REUSE_CANONICAL_ARCANA_WITH_PROVENANCE_GAP_RECORDED"
    else:
        status = "BLOCKED_R517_B6_H4_NATIVE_HYDROLOGY_PHYSICAL_SUFFICIENCY_INCOMPLETE"
        decision = "SCIENTIFIC_ENGINE_SUITABILITY_GATE_REQUIRED"

    return {
        "all_expected_generator_hashes_recovered": all_hashes_exact,
        "water_balance_components": water_balance_components,
        "discharge_components": discharge_components,
        "structural_components": structural_components,
        "physical_water_balance_sufficient": physical_water_balance_sufficient,
        "discharge_semantics_sufficient": discharge_semantics_sufficient,
        "structural_semantics_sufficient": structural_semantics_sufficient,
        "target_payload_literal_reference_count": len(payload_literal_refs),
        "v055i_reference_count": len(v055i_refs),
        "direct_v055i_payload_bridge_reference_count": len(direct_bridge_refs),
        "exact_v0_5_5I_generator_identity_adjudicated": exact_generator_identity_adjudicated,
        "reuse_canonical_arcana_authorized": reuse_canonical_arcana_authorized,
        "external_provider_authorized": False,
        "decision": decision,
        "status": status,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="R5.17-B6-H4: adjudicate exact v0.5.5I export lineage and physical sufficiency of recovered native ARCANA hydrology without executing historical code.")
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("R5_17_B6_H4_V055I_EXPORT_AND_PHYSICAL_SUFFICIENCY.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    sources = inspect_physical_model(root)
    exports = discover_export_lineage(root)
    adjudication = adjudicate(sources, exports)

    result = {
        "schema": "ARCANA_R5_17_B6_H4_V055I_EXPORT_AND_PHYSICAL_SUFFICIENCY_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-H4",
        "purpose": "Adjudicate whether recovered native ARCANA hydrology is physically sufficient for freshwater-support derivation and whether its exact export lineage to v0_5_5I_SEALED/channel_hydrology_state_I.npz is documentary-recoverable.",
        "search_root": str(root),
        "target_payload": TARGET_PAYLOAD,
        "target_input_dir": TARGET_INPUT_DIR,
        "expected_generator_hashes": TARGET_HASHES,
        "source_evidence": sources,
        "export_reference_file_count": len(exports),
        "export_references": exports,
        "adjudication": adjudication,
        "payload_materialized": False,
        "source_executed": False,
        "new_historical_simulation": False,
        "canonical_mutation": False,
        "freshwater_support_materialized": False,
        "status": adjudication["status"],
        "next_if_full_pass": "R5.17-B6_HYDROLOGY_BINDING_DECISION_AND_FRESHWATER_DERIVATION_DESIGN",
        "next_if_provenance_gap_only": "R5.17-B6_RECORD_V055I_PROVENANCE_GAP_AND_REUSE_NATIVE_ARCANA_HYDROLOGY",
        "next_if_blocked": "R5.17-B6_SCIENTIFIC_ENGINE_SUITABILITY_ADJUDICATION",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps({
        "status": adjudication["status"],
        "decision": adjudication["decision"],
        "all_expected_generator_hashes_recovered": adjudication["all_expected_generator_hashes_recovered"],
        "physical_water_balance_sufficient": adjudication["physical_water_balance_sufficient"],
        "discharge_semantics_sufficient": adjudication["discharge_semantics_sufficient"],
        "structural_semantics_sufficient": adjudication["structural_semantics_sufficient"],
        "target_payload_literal_reference_count": adjudication["target_payload_literal_reference_count"],
        "v055i_reference_count": adjudication["v055i_reference_count"],
        "direct_v055i_payload_bridge_reference_count": adjudication["direct_v055i_payload_bridge_reference_count"],
        "exact_v0_5_5I_generator_identity_adjudicated": adjudication["exact_v0_5_5I_generator_identity_adjudicated"],
        "reuse_canonical_arcana_authorized": adjudication["reuse_canonical_arcana_authorized"],
        "output": str(args.output.resolve()),
    }, indent=2))

    if adjudication["status"].startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
