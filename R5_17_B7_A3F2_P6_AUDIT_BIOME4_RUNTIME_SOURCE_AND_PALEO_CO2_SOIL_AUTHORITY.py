from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HEAD = "3e4bf704021f2205ca1fdb3c3fe102b78304ed0a"
P5 = Path("R5_17_B7_A3F2_P5_PHYSICAL_NPP_PROVIDER_ADJUDICATION.json")
OUT_JSON = Path("R5_17_B7_A3F2_P6_BIOME4_RUNTIME_SOURCE_AND_PALEO_CO2_SOIL_AUTHORITY_RECOVERY.json")
OUT_MD = Path("R5_17_B7_A3F2_P6_BIOME4_RUNTIME_SOURCE_AND_PALEO_CO2_SOIL_AUTHORITY_RECOVERY.md")

AUTHORITY_PATHS = {
    "p5": P5,
    "suitability_gate": Path("SCIENTIFIC_ENGINE_SUITABILITY_GATE.md"),
    "b7_contract": Path("R5_17_B7_BIOLOGICAL_FOOD_SUPPORT_CONTRACT.md"),
    "madingley_runtime_audit": Path("R5_17_B7_A3F2_P3_MADINGLEY_RUNTIME_AND_INPUT_BINDING_AUDIT.json"),
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source(root: Path, path: Path, role: str, tracked: set[str]) -> dict:
    full = root / path
    if not full.is_file():
        return {"path": path.as_posix(), "role": role, "available": False}
    return {"path": path.as_posix(), "role": role, "available": True, "tracked": path.as_posix() in tracked, "size_bytes": full.stat().st_size, "sha256": sha(full), "git_blob_oid": git("hash-object", "--", path.as_posix())}


def main() -> int:
    root = Path(__file__).resolve().parent
    if git("rev-parse", "HEAD") != HEAD:
        raise RuntimeError("repository HEAD changed during P6 gate")
    p5 = json.loads((root / P5).read_text(encoding="utf-8-sig"))
    if p5.get("provider_decision") != "INTRODUCE_BIOME4_PROVIDER":
        raise RuntimeError("P5 provider decision mismatch")
    if p5.get("implementation_disposition") != "PROVIDER_SELECTED_INPUT_RECOVERY_REQUIRED":
        raise RuntimeError("P5 disposition mismatch")
    tracked = set(git("ls-files").splitlines())
    result = {
        "stage": "R5.17-B7-A3F2-P6",
        "status": "P6_GATE_COMPLETE_BLOCKED_INPUT_AUTHORITY_RECOVERY_REQUIRED",
        "repository": {"head": HEAD, "branch": git("branch", "--show-current")},
        "parent": {"stage": "R5.17-B7-A3F2-P5", "decision": p5["provider_decision"], "disposition": p5["implementation_disposition"]},
        "selected_provider": "BIOME4",
        "temporal_strategy": "INDEPENDENT_ECOLOGICAL_OPPORTUNITY_SNAPSHOTS",
        "authority_recovery_gate": {
            "biome4_runtime_source": {"runtime_identity_verified": False, "exact_version_pinned": False, "source_provenance_recovered": False, "license_provenance_recovered": False, "status": "MISSING"},
            "paleo_co2": {"physical_authority_present": False, "required_snapshot_coverage": False, "units_and_provenance_verified": False, "constant_hold_or_silent_fill": False, "status": "MISSING"},
            "soil": {"physical_authority_present": False, "water_holding_capacity_present": False, "hydraulic_or_percolation_properties_present": False, "units_and_provenance_verified": False, "status": "MISSING"},
        },
        "recovered_authority": {"p5_crosswalk": "BIOME4 selected, but exact runtime/source and required physical inputs remain unresolved", "arcana_climate_and_hydrology": "proxy or non-equivalent for BIOME4 physical paleo input requirements", "a1_forage_and_r333_r334": "trophic/resource proxies, not physical NPP, CO2, or soil authority"},
        "provider_suitability_decision": "BLOCKED_MISSING_BIOME4_RUNTIME_SOURCE_AND_INPUT_AUTHORITIES",
        "production_pilot_authorized": False,
        "physical_npp_materialized": False,
        "normalized_proxy_rescaling_authorized": False,
        "required_next_inputs": ["exact BIOME4 runtime/version/source/license authority", "governed physical paleo-CO2 authority covering each authorized snapshot", "governed physical soil water-holding and hydraulic/percolation authority", "provider-compatible units, missing-value, uncertainty, and provenance contracts"],
        "governance": {"BIOME4_invoked": False, "Madingley_invoked": False, "animal_resource_support_materialized": False, "historical_species_range_materialized": False, "historical_abundance_materialized": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED", "human_management_used": False, "population_target_used": False, "k_x_t_materialized": False, "canonical_mutation": False},
        "sources": {key: source(root, path, key, tracked) for key, path in AUTHORITY_PATHS.items()},
        "method": "Repository-local authority inventory with exact-file SHA256 and Git blob registration; no interpolation, extrapolation, proxy rescaling, external provider invocation, or physical-NPP synthesis.",
        "recommended_next_operation": "R5.17-B7-A3F2-P7 BIOME4 INPUT AUTHORITY RECOVERY OR SCIENTIFIC RE-ADJUDICATION",
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text("# R5.17-B7-A3F2-P6\n\n## Decision\n\n**BLOCKED_MISSING_BIOME4_RUNTIME_SOURCE_AND_INPUT_AUTHORITIES**. BIOME4 remains selected, but the exact governed runtime/source/license, physical paleo-CO2 authority, and physical soil water/hydraulic authority are not recovered for the independent ecological opportunity snapshots.\n\nExisting ARCANA climate, hydrology, forage, and resource surfaces remain proxies or non-equivalents and are not silently promoted to BIOME4 physical inputs. No provider run, proxy rescaling, interpolation, extrapolation, production pilot, or physical NPP materialization is authorized.\n\n`AQUATIC_MARINE_RESOURCE_SUPPORT = NOT_MATERIALIZED`.\n", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
