from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HEAD = "d8cbc619c8bdd3340fc174d651dbb671ba642ac0"
OUT_JSON = Path("R5_17_B7_A3F2_P3_MADINGLEY_RUNTIME_AND_INPUT_BINDING_AUDIT.json")
OUT_MD = Path("R5_17_B7_A3F2_P3_MADINGLEY_RUNTIME_AND_INPUT_BINDING_AUDIT.md")
AUTH = {
    "p2": Path("R5_17_B7_A3F2_P2_MACROECOLOGICAL_RESOURCE_PROVIDER_ADJUDICATION.json"),
    "runtime": Path("outputs/v0_6D1_R4_3/R4_3_RUNTIME_IDENTITY_EVIDENCE.json"),
    "job_audit": Path("outputs/v0_6D1_R4_3/jobs/R42_J07_H0_POST_CHA1_RECOVERY_MADINGLEY/JOB_AUDIT.json"),
    "job_contract": Path("outputs/v0_6D1_R4_3/jobs/R42_J07_H0_POST_CHA1_RECOVERY_MADINGLEY/JOB_CONTRACT.json"),
    "normalized": Path("outputs/v0_6D1_R4_3/jobs/R42_J07_H0_POST_CHA1_RECOVERY_MADINGLEY/NORMALIZED_EVIDENCE.json"),
    "runner": Path("benchmarks/r43/madingley_r43.R"),
    "microbenchmark": Path("outputs/v0_6D1_R4_1/R4_1_ENGINE_MICROBENCHMARK_REPORT.json"),
    "functional": Path("outputs/v0_6D1_R3_23/R3_23_PRESENT_FUNCTIONAL_SUMMARY.json"),
    "lineage": Path("outputs/v0_6D1_R3_21/R3_21_PRESENT_LINEAGE_REGISTRY.json"),
    "a1": Path("references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"),
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source(root: Path, path: Path, role: str) -> dict[str, Any]:
    absolute = root / path
    if not absolute.is_file():
        return {"path": path.as_posix(), "role": role, "available": False}
    return {"path": path.as_posix(), "role": role, "available": True, "size_bytes": absolute.stat().st_size, "sha256": sha(absolute), "git_blob_oid": git("hash-object", "--", path.as_posix())}


def main() -> int:
    root = Path(__file__).resolve().parent
    if git("rev-parse", "HEAD") != HEAD:
        raise RuntimeError("unexpected repository HEAD")
    runtime = load(root / AUTH["runtime"])
    audit = load(root / AUTH["job_audit"])
    normalized = load(root / AUTH["normalized"])
    micro = load(root / AUTH["microbenchmark"])
    if runtime["engines"][2]["confirmed_version"] != "MadingleyR-1.0.6__CPP-2.02":
        raise RuntimeError("recovered Madingley runtime identity mismatch")
    if audit["engine"] != "Madingley" or audit["status"] != "PASS_EVIDENCE":
        raise RuntimeError("prior Madingley evidence is not a governed PASS_EVIDENCE record")
    inputs = [
        {"name": "realm_classification", "units": "provider-native categorical; metadata not recovered", "dimensions": "1-degree spatial grid", "spatial": "provider 1-degree Earth grid", "temporal": "static per run", "required": True, "normalization": "provider default"},
        {"name": "land_mask", "units": "provider-native mask; metadata not recovered", "dimensions": "1-degree spatial grid", "spatial": "provider 1-degree Earth grid", "temporal": "static per run", "required": True, "normalization": "provider default"},
        {"name": "hanpp", "units": "provider-native; prior evidence says no HANPP applied", "dimensions": "1-degree spatial grid", "spatial": "provider grid", "temporal": "static per run", "required": True, "normalization": "default/no-HANPP path"},
        {"name": "available_water_capacity", "units": "provider-native; exact unit metadata not recovered", "dimensions": "1-degree spatial grid", "spatial": "provider grid", "temporal": "static per run", "required": True, "normalization": "provider default"},
        {"name": "Ecto_max / Endo_C_max / Endo_H_max / Endo_O_max", "units": "functional-group parameter units; exact metadata not recovered", "dimensions": "1-degree spatial grid", "spatial": "provider grid", "temporal": "static per run", "required": True, "normalization": "provider functional-group defaults"},
        {"name": "terrestrial_net_primary_productivity", "units": "provider physical NPP input units required; prior ARCANA adapter used normalized proxy", "dimensions": "12 monthly rasters x provider grid", "spatial": "provider 1-degree grid", "temporal": "monthly climatology per run", "required": True, "normalization": "prior runner multiplied by normalized boundary factor; not acceptable for B7 authority"},
        {"name": "near-surface_temperature", "units": "provider temperature units; exact metadata not recovered", "dimensions": "12 monthly rasters x provider grid", "spatial": "provider 1-degree grid", "temporal": "monthly climatology per run", "required": True, "normalization": "provider default"},
        {"name": "precipitation", "units": "provider precipitation units; exact metadata not recovered", "dimensions": "12 monthly rasters x provider grid", "spatial": "provider 1-degree grid", "temporal": "monthly climatology per run", "required": True, "normalization": "provider default; relative precipitation cannot substitute freshwater"},
        {"name": "ground_frost_frequency", "units": "provider-native frequency; exact metadata not recovered", "dimensions": "12 monthly rasters x provider grid", "spatial": "provider 1-degree grid", "temporal": "monthly climatology per run", "required": True, "normalization": "provider default"},
        {"name": "diurnal_temperature_range", "units": "provider temperature-range units; exact metadata not recovered", "dimensions": "12 monthly rasters x provider grid", "spatial": "provider 1-degree grid", "temporal": "monthly climatology per run", "required": True, "normalization": "provider default"},
    ]
    crosswalk = {x["name"]: {"classification": "MISSING" if x["name"] == "terrestrial_net_primary_productivity" else "PROXY_ONLY", "authority": "none sufficient for exact provider semantics", "reason": "current governed A1/R3.33/R3.34 quantities do not establish the required provider-native physical monthly input"} for x in inputs}
    crosswalk["land_mask"] = {"classification": "PROXY_ONLY", "authority": "A1 paleogeographic reference exists", "reason": "not yet transformed to provider grid with time-slice provenance and shoreline semantics"}
    crosswalk["realm_classification"] = {"classification": "MISSING", "authority": "none exact", "reason": "terrestrial provider realm categories are not bound to ARCANA paleogeography"}
    result = {
        "stage": "R5.17-B7-A3F2-P3",
        "status": "P3_AUDIT_COMPLETE_BLOCKED_MISSING_PHYSICAL_NPP_AUTHORITY",
        "repository": {"head": HEAD, "branch": git("branch", "--show-current")},
        "runtime_identity": {"provider": "Madingley", "package": "MadingleyR", "version": "1.0.6", "backend": "MadingleyCPP 2.02", "confirmed_identity": "MadingleyR-1.0.6__CPP-2.02", "r_runtime": "PowerShell -> WSL conda:arcana-r40-r/Rscript+runtime-libs", "library_path": "/home/jose/miniforge3/envs/arcana-r40-r/lib/R/library/MadingleyR", "compiler_dependency": "compiled C++ backend; compiler build identity not separately recovered", "license_status": "not adjudicated in this tranche", "previous_success": {"runtime_identity_status": runtime["engines"][2]["status"], "microbenchmark_version": micro["benchmarks"][5]["confirmed_version"], "job_status": audit["status"], "successful_replicates": audit["successful_replicates"], "canonical_write": audit["canonical_write"]}},
        "runtime_smoke_test": {"status": "PASS_PRIOR_NONSCIENTIFIC_IDENTITY_EVIDENCE", "performed_now": False, "evidence": "prior runtime identity returned MadingleyR 1.0.6 and C++ 2.02 with returncode 0; prior R4.1 microbenchmark and R4.3 evidence also passed", "scientific_evidence": False, "production_run": False},
        "exact_provider_input_contract": inputs,
        "arcana_input_crosswalk": crosswalk,
        "npp_adjudication": {"result": "C_ONLY_NORMALIZED_PROXY_EXISTS_PHYSICAL_NPP_MISSING", "physical_productivity_authority_exists": False, "defensible_transformation_exists": False, "normalized_proxy_exists": True, "fail_closed": True, "prohibition": "do not rescale 0..1 forage/normalized NPP into physical productivity units"},
        "spatial_adapter": {"arcana": "90x180 lat/lon, changing land/sea and latitude-dependent cell area", "provider": "1-degree Earth grid; prior spatial semantics were non-ARCANA", "compatible_now": False, "minimum_contract": ["area-aware remapping", "cell identity/latitude/cell area retention", "time-indexed land/sea and shoreline masks", "terrestrial realm validity", "environmental field units preserved", "time-slice provenance and uncertainty masks"], "executed": False},
        "temporal_strategy": {"decision": "INDEPENDENT_ECOLOGICAL_OPPORTUNITY_SNAPSHOTS", "reason": "governed anchors do not support a continuous transient provider state; snapshots can be conditional on each governed paleoenvironment", "meaning": "equilibrium/opportunity conditional on governed environment, not exact realized historical fauna", "available_domains": ["A1 anchors 210 Ma to 0 Ma", "R3.33/R3.34 recent 20 ka to 0 ka"], "no_silent_interpolation": True},
        "initialization_spinup": {"species_origin_required": False, "standard_cohort_initialization": "possible only as generic provider initial condition after input closure", "spinup": "possible in principle but would estimate ecological opportunity, not historical realized state", "sensitivity": "must be tested in future pilot; not run now", "warm_start": "not required for independent snapshots; required only if transient path dependence is later chosen"},
        "authorized_output_semantics": {"minimal_future_output": "terrestrial heterotroph biomass/opportunity state with cohort/trophic descriptors where provider-native", "potential": ["functional cohort abundance", "heterotroph biomass", "trophic-group composition", "environment-conditioned opportunity response"], "forbidden": ["human-edible fraction", "calories", "hunting yield", "harvest return", "population support", "K(x,t)"]},
        "pilot_decision": "BLOCKED_MISSING_PHYSICAL_NPP_AUTHORITY",
        "remaining_conditions": ["recover or independently authorize physical monthly NPP authority", "complete all required provider input units and semantics", "approve area-aware ARCANA-to-provider adapter", "bind time-slice land/sea/shoreline provenance", "complete runtime/compiler/license audit", "define initialization/spinup sensitivity protocol", "keep output below human exploitation and K(x,t)"],
        "governance": {"human_management_used": False, "population_target_used": False, "k_x_t_materialized": False, "canonical_mutation": False, "historical_species_range_materialized": False, "historical_abundance_materialized": False, "production_madingley_run": False, "animal_resource_support_materialized": False, "Madingley_invoked": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED"},
        "next_operation": "Recover/adjudicate physical monthly NPP and complete the required ARCANA input/spatial adapter audit; only then reopen the Madingley pilot gate."
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text("""# R5.17-B7-A3F2-P3\n\n## Decision\n\n**BLOCKED_MISSING_PHYSICAL_NPP_AUTHORITY**. The exact recovered provider is MadingleyR 1.0.6 with MadingleyCPP 2.02. Its required contract includes a 1-degree grid, land/realm masks, water capacity, functional-group fields, and 12 monthly layers for NPP, temperature, precipitation, frost, and diurnal temperature range.\n\nPrior ARCANA evidence confirms successful runtime identity and non-canonical runs, but the prior adapter used normalized NPP response and non-ARCANA geography. Current ARCANA authorities provide only proxy-level or incomplete bindings; normalized NPP must not be rescaled into physical productivity.\n\nThe defensible future interpretation is **INDEPENDENT_ECOLOGICAL_OPPORTUNITY_SNAPSHOTS**, conditional on governed paleoenvironmental anchors, not exact historical fauna. A generic cohort/spin-up strategy may avoid fabricated species origins, but it is not yet authorized.\n\nNo production provider run, species-range reconstruction, biomass/resource materialization, current-state/index update, staging, commit, or push occurred. `AQUATIC_MARINE_RESOURCE_SUPPORT = NOT_MATERIALIZED`.\n""", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
