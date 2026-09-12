from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HEAD = "cfc5f26bb0965e87f8a43ea29ad6e27b4d43d021"
OUT_JSON = Path("R5_17_B7_A3F2_P5_PHYSICAL_NPP_PROVIDER_ADJUDICATION.json")
OUT_MD = Path("R5_17_B7_A3F2_P5_PHYSICAL_NPP_PROVIDER_ADJUDICATION.md")
AUTH = {
    "p4": Path("R5_17_B7_A3F2_P4_PHYSICAL_NPP_AUTHORITY_RECOVERY.json"),
    "p3": Path("R5_17_B7_A3F2_P3_MADINGLEY_RUNTIME_AND_INPUT_BINDING_AUDIT.json"),
    "b7_contract": Path("R5_17_B7_BIOLOGICAL_FOOD_SUPPORT_CONTRACT.md"),
    "suitability_gate": Path("SCIENTIFIC_ENGINE_SUITABILITY_GATE.md"),
    "a1": Path("references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"),
    "r333": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz"),
    "r334": Path("SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz"),
    "madingley_runner": Path("benchmarks/r43/madingley_r43.R"),
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source(root: Path, path: Path, role: str) -> dict:
    p = root / path
    if not p.is_file():
        return {"path": path.as_posix(), "role": role, "available": False}
    return {"path": path.as_posix(), "role": role, "available": True, "tracked": path.as_posix() in set(git("ls-files").splitlines()), "size_bytes": p.stat().st_size, "sha256": sha(p)}


def main() -> int:
    root = Path(__file__).resolve().parent
    if git("rev-parse", "HEAD") != HEAD:
        raise RuntimeError("repository HEAD changed during P5 audit")
    p4 = load(root / AUTH["p4"])
    if p4["decision"] != "BLOCKED_ONLY_NORMALIZED_PROXY_EXISTS":
        raise RuntimeError("P4 parent decision mismatch")
    sources = {k: source(root, v, k) for k, v in AUTH.items()}
    result = {
        "stage": "R5.17-B7-A3F2-P5",
        "status": "P5_GATE_COMPLETE_BIOME4_SELECTED_INPUT_RECOVERY_REQUIRED",
        "repository": {"head": HEAD, "branch": git("branch", "--show-current")},
        "sources": sources,
        "parent_p4_decision": p4["decision"],
        "exact_npp_requirement": {"quantity": "physical terrestrial net primary productivity", "units": "provider-compatible carbon mass per area per time, e.g. gC m^-2 yr^-1 or gC m^-2 month^-1 only after exact provider compatibility is verified", "area_basis": "physical land-cell area, not equal-area assumption", "time_basis": "12 monthly layers for Madingley input contract", "spatial_semantics": "terrestrial land-only provider grid with latitude/cell-area and time-slice provenance", "temporal_semantics": "physical NPP conditional on governed paleoenvironment; not realized ARCANA species history", "missing_values": "explicit mask/uncertainty; no silent zero fill", "land_behavior": "ocean cells excluded by governed land/realm mask"},
        "candidate_providers": ["BIOME4", "LPJ-GUESS", "CASA-class light-use-efficiency model", "BIOME-BGC/other process model", "MINIMUM_CUSTOM_ARCANA"],
        "biome4_audit": {"identity": "BIOME4 equilibrium terrestrial biogeography/productivity model; exact runtime/version/source/license not recovered in repository", "physical_npp_fit": "CONDITIONAL_MATCH: process-based NPP candidate, units/runtime must be pinned", "temporal_fit": "STRONG_FOR_INDEPENDENT_ECOLOGICAL_OPPORTUNITY_SNAPSHOTS", "spatial_fit": "CONDITIONAL: requires area-aware ARCANA adapter", "pft_representation": "functional plant types, species-independent", "equilibrium": "potential/equilibrium productivity conditional on climate/soil/CO2, not exact historical vegetation", "co2": "required and not yet governed through required paleo interval", "water_balance": "requires soil water holding/hydraulic properties", "required_inputs": ["monthly temperature", "monthly precipitation", "monthly sunshine/cloud cover", "soil water holding capacity", "soil hydraulic/percolation property", "atmospheric CO2", "latitude", "optional minimum temperature", "optional elevation"], "overall": "leading candidate, not pilot-ready"},
        "lpj_guess_audit": {"physical_npp_fit": "STRONG_IN_PRINCIPLE", "temporal_fit": "TRANSIENT_CAPABLE_BUT_EXCEEDS_CURRENT_SNAPSHOT_NEED", "spatial_fit": "CONDITIONAL_AREA_AWARE_ADAPTER", "inputs": ["monthly climate", "CO2", "soil", "PFT", "often nitrogen/biogeochemical state"], "spinup": "substantial equilibrium/spin-up and path-dependence burden", "species_independence": "PFT-level in principle", "runtime_reproducibility": "exact current ARCANA runtime not recovered", "adjudication": "not preferred over BIOME4 because added transient/soil/nitrogen burden is not justified by B7 snapshot target"},
        "casa_audit": {"physical_npp_fit": "CONDITIONAL", "temporal_fit": "SNAPSHOT_COMPATIBLE_IF_INPUTS_EXIST", "spatial_fit": "CONDITIONAL", "inputs": ["solar radiation", "FPAR/APAR or vegetation-cover equivalent", "temperature", "water stress", "soil/land cover"], "arcana_coverage": "FPAR/APAR/NDVI equivalent not established; using simulated resource abundance would be circular", "adjudication": "not selected"},
        "other_provider_audit": {"BIOME-BGC": "potentially physical but greater parameter/soil/biogeochemistry burden; no exact ARCANA runtime authority recovered", "minimum_custom_arcana": "rejected as first choice because custom trophic/productivity approximation is less defensible than established process-based specialist evidence"},
        "required_temporal_domain": {"deep_time_context_domain": "A1 canonical anchor context 210 Ma to 0 Ma", "human_support_required_domain": "B7 natural biological opportunity domain; exact human-support contribution window is not separately narrowed by the contract", "madingley_required_domain": "future independent snapshot anchors selected from governed ARCANA environments; do not assume continuous 210 Ma to 0 run", "strategy": "INDEPENDENT_ECOLOGICAL_OPPORTUNITY_SNAPSHOTS"},
        "arcana_input_crosswalk": {"monthly_temperature": "PROXY_ONLY: exact physical monthly paleo climate binding not closed", "monthly_precipitation": "PROXY_ONLY: precipitation is not soil water/hydraulic authority", "monthly_sunshine_cloud": "MISSING", "soil_water_holding_capacity": "MISSING", "soil_hydraulic_conductivity_percolation": "MISSING", "atmospheric_co2": "MISSING_FOR_REQUIRED_PALEO_DOMAIN", "latitude": "DEFENSIBLE_TRANSFORMATION from ARCANA grid coordinate", "elevation": "MISSING_IF_REQUIRED", "land_sea_mask": "PROXY_ONLY until time-slice provider adapter is approved", "a1_forage": "PROXY_ONLY and not NPP", "r333_r334": "PROXY_ONLY/recent-domain; not silently backprojectable"},
        "paleo_co2_authority": {"status": "MISSING", "physical_concentration": False, "partial_coverage": False, "constant_hold": False, "next_requirement": "independent governed paleo-CO2 source or provider gate"},
        "soil_authority": {"status": "MISSING", "physical_soil_properties": False, "available_non_equivalents": ["B6 freshwater support", "hydrological reliability", "precipitation", "geology/substrate"], "non_equivalence_rule": "none of these establishes field capacity, wilting point, soil depth, texture, hydraulic conductivity or percolation", "next_requirement": "specialist soil/pedogenesis authority or explicit provider-specific soil gate"},
        "comparative_matrix": {"BIOME4": {"physical_NPP_semantics": "conditional strong", "paleo_applicability": "conditional", "snapshot_fit": "strong", "climate_fit": "proxy/incomplete", "soil_fit": "missing", "CO2_fit": "missing", "spatial_fit": "adapter required", "species_independence": "strong", "runtime": "not pinned", "cost": "moderate per-cell/snapshot", "adapter": "moderate", "validation": "available after inputs close"}, "LPJ-GUESS": {"physical_NPP_semantics": "strong", "paleo_applicability": "conditional", "snapshot_fit": "moderate", "climate_fit": "incomplete", "soil_fit": "missing", "CO2_fit": "missing", "spatial_fit": "adapter required", "species_independence": "PFT-level", "runtime": "not pinned", "cost": "high", "adapter": "high", "validation": "possible but spinup-sensitive"}, "CASA": {"physical_NPP_semantics": "conditional", "paleo_applicability": "weak/conditional", "snapshot_fit": "moderate", "climate_fit": "incomplete", "soil_fit": "missing", "CO2_fit": "model-dependent", "spatial_fit": "adapter required", "species_independence": "strong", "runtime": "not recovered", "cost": "moderate", "adapter": "high due FPAR", "validation": "circularity risk"}},
        "selected_provider": "BIOME4",
        "provider_decision": "INTRODUCE_BIOME4_PROVIDER",
        "implementation_disposition": "PROVIDER_SELECTED_INPUT_RECOVERY_REQUIRED",
        "remaining_conditions": ["pin exact BIOME4 runtime/version/source/license", "recover physical paleo CO2", "recover physical soil water/hydraulic properties", "close monthly climate and sunshine/cloud crosswalk", "approve area-aware 90x180 snapshot adapter", "define uncertainty/missing-value semantics", "pre-register validation against held-out governed evidence"],
        "governance": {"physical_npp_materialized": False, "normalized_proxy_rescaled": False, "Madingley_invoked": False, "BIOME4_invoked": False, "LPJ_GUESS_invoked": False, "CASA_invoked": False, "animal_resource_support_materialized": False, "human_management_used": False, "population_target_used": False, "k_x_t_materialized": False, "canonical_mutation": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED"},
        "recommended_next_operation": "R5.17-B7-A3F2-P6 BIOME4 RUNTIME/SOURCE AND PALEO-CO2/SOIL AUTHORITY RECOVERY GATE"
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text("""# R5.17-B7-A3F2-P5\n\n## Decision\n\n**INTRODUCE_BIOME4_PROVIDER**, with `PROVIDER_SELECTED_INPUT_RECOVERY_REQUIRED`. BIOME4 is the earliest scientifically aligned candidate for physical terrestrial NPP under B7's `INDEPENDENT_ECOLOGICAL_OPPORTUNITY_SNAPSHOTS` interpretation. Its output would be potential/equilibrium productivity conditional on a governed paleoenvironment, not exact realized historical vegetation or ARCANA species history.\n\nThe gate is not pilot-ready. Physical paleo-CO2, soil water-holding capacity, soil hydraulic/percolation properties, monthly sunshine/cloud inputs, exact runtime/source pinning, and the area-aware spatial adapter remain unresolved. LPJ-GUESS is more transient and parameter-intensive than B7 currently requires; CASA has unresolved FPAR/solar inputs and circularity risk.\n\nNo NPP provider ran, no physical NPP was materialized, no normalized proxy was rescaled, no Madingley or resource run occurred, and no current-state/index/staging/commit/push operation occurred. `AQUATIC_MARINE_RESOURCE_SUPPORT = NOT_MATERIALIZED`.\n\nRecommended next operation: **R5.17-B7-A3F2-P6 BIOME4 RUNTIME/SOURCE AND PALEO-CO2/SOIL AUTHORITY RECOVERY GATE**.\n""", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
