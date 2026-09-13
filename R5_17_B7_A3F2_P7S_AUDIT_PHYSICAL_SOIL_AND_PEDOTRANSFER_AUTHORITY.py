from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HEAD = "43731502aa210f0714473f0f71606eaf5f769375"
P7T = Path("R5_17_B7_A3F2_P7T_HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY.json")
P7C = Path("R5_17_B7_A3F2_P7C_PALEO_CO2_AUTHORITY_BINDING.json")
REGISTRY = Path("R5_17_B7_A3F2_P7T_TEMPORAL_SNAPSHOT_REGISTRY.csv")
BIOME4 = Path(".arcana_engines/BIOME4")
DRIVER = BIOME4 / "biome4driver.f90"
MODEL = BIOME4 / "biome4.f"
README = BIOME4 / "README.md"
SMOKE = Path(".arcana_engines/BIOME4_runtime/smoke/smoke_soil.cdl")
OUT_JSON = Path("R5_17_B7_A3F2_P7S_PHYSICAL_SOIL_AND_PEDOTRANSFER_AUTHORITY.json")
OUT_MD = Path("R5_17_B7_A3F2_P7S_PHYSICAL_SOIL_AND_PEDOTRANSFER_AUTHORITY.md")
AGES = [200.0, 125.0, 120.0, 20.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 5.0, 0.0]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    current = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    if current != HEAD:
        raise RuntimeError("ARCANA HEAD changed during P7S")
    required = [P7T, P7C, REGISTRY, DRIVER, MODEL, README, SMOKE]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise RuntimeError(f"missing P7S authority input(s): {missing}")
    p7t = json.loads(P7T.read_text(encoding="utf-8"))
    p7c = json.loads(P7C.read_text(encoding="utf-8"))
    if p7t["decision"] != "HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY_READY" or p7t["shared_temporal_registry"]["ages_ka_before_model_present"] != AGES:
        raise RuntimeError("P7T registry is not the governed 12-age authority")
    source = {str(p): {"sha256": sha(p), "size_bytes": p.stat().st_size} for p in [DRIVER, MODEL, README, SMOKE]}
    result = {
        "stage": "R5.17-B7-A3F2-P7S",
        "parent_head": HEAD,
        "p7t_temporal_authority": {"decision": p7t["decision"], "domain": "200 ka -> 0 ka", "snapshot_ages_ka": AGES, "snapshot_count": 12, "registry_path": str(REGISTRY), "registry_sha256": sha(REGISTRY)},
        "p7c_co2_authority": {"decision": p7c["decision"], "bound": p7c["governance"]["PALEO_CO2_AUTHORITY_BOUND"], "values_not_recomputed": True},
        "biome4_soil_contract": {"source_repository": "jedokaplan/BIOME4", "source_commit": "4ad9dff37eed339fce88c0fa5802757f86a3ef44", "layer_count": 6, "dz": {"units": "cm", "evidence": "smoke_soil.cdl dz:units = cm"}, "whc": {"layer_units": "mm/cm", "aggregated_units": "mm", "evidence": "biome4driver.f90 input(43:44) sums whc * dz; source comment says input whc are in mm/cm"}, "ksat": {"layer_units": "mm/hr", "aggregated_units": "mm/hr", "evidence": "biome4driver.f90 input(41:42) weighted means; source comments identify Ksat as mm/h"}, "vertical_aggregation": {"upper": "layers 1:3", "lower": "layers 4:6", "Ksat": "depth-weighted mean per zone", "WHC": "depth-integrated sum per zone"}, "source_evidence": source},
        "biome4_whc_semantics": {"source_label": "volumetric whc / soil water holding capacity", "resolved_semantics": "AVAILABLE_WATER_HOLDING_CAPACITY / PLANT_AVAILABLE_WATER_STORAGE", "field_capacity": "part of the available-water interpretation; exact pressure convention not recovered in pinned source", "plant_available_water": True, "total_pore_space": False, "exact_model_quantity": "AVAILABLE_WATER_HOLDING_CAPACITY", "basis": ["Kaplan et al. 2003, DOI 10.1029/2002JD002559: BIOME4 uses soil texture and soil depth to determine water holding capacity and percolation", "BIOME4-linked literature describes the whole-soil-column quantity as available water-holding capacity", "pinned driver integrates per-layer whc by depth into the top and lower soil stores"], "caveat": "historical texture-class derivation and exact field-capacity/wilting-point pressure conventions remain unrecovered"},
        "arcana_soil_authority_inventory": {"direct_physical_soil_authority": {"status": "ABSENT", "paths_checked": ["ARCANA_EXECUTION_REFERENCE_INDEX.json", "R5_17_B7_A3F2_P5_PHYSICAL_NPP_PROVIDER_ADJUDICATION.json", "R5_17_B7_A3F2_P6_BIOME4_RUNTIME_SOURCE_AND_PALEO_CO2_SOIL_AUTHORITY_RECOVERY.json", "R5_17_B7_BIOLOGICAL_FOOD_SUPPORT_CONTRACT.md"], "finding": "no governed dz/whc/Ksat arrays or physical soil profiles"}, "texture_authority": "ABSENT", "bulk_density_authority": "ABSENT", "soil_depth_profile_authority": "ABSENT", "hydraulic_authority": "ABSENT", "non_equivalents_not_promoted": ["geology/bedrock", "precipitation", "runoff/freshwater support", "wetland forage", "aridity", "erosion potential", "terrain roughness"]},
        "authority_levels": {"A_DIRECT_BIOME4_EQUIVALENT": {"status": "0 governed cells", "fraction": 0.0}, "B_DIRECT_HYDRAULIC_STATE": {"status": "0 governed cells", "fraction": 0.0}, "C_PEDOTRANSFER_READY": {"status": "0 governed cells; sand/silt/clay and bulk density absent", "fraction": 0.0}, "D_PEDOGENESIS_READY": {"status": "not demonstrated; parent-material/history inputs are not sufficient as a governed soil model", "fraction": 0.0}, "E_INSUFFICIENT": {"status": "all ARCANA target cells/snapshots remain at insufficient authority", "fraction": 1.0}, "strongest_available_level": "E"},
        "vertical_profile_status": {"classification": "NO_VERTICAL_PROFILE_AUTHORITY", "native_layered_profile": False, "derivable_layered_profile": False, "static_profile_approximation_candidate": False, "six_layer_duplication_authorized": False, "reason": "no physical soil layer depths/properties exist in ARCANA"},
        "temporal_soil_semantics": {"shared_snapshot_ages_ka": AGES, "strategy": "UNRESOLVED", "allowed_options": ["TIME_VARYING_RECONSTRUCTED", "STATIC_PHYSICAL_PROFILE", "PIECEWISE_TIME_VARYING", "MIXED_BY_REGION"], "independent_grid_prohibited": True, "materialization": "not performed"},
        "new_land_handling": {"land_exposure_age": "NOT_MATERIALIZED", "soil_development_eligibility": "REQUIRES_PEDOGENESIS_GATE", "mature_soil_instant_inheritance": False, "newly_exposed_cells": "must not inherit mature present soil without authority"},
        "pedotransfer_candidate": {"provider": "Rosetta3", "scientific_reference": "Zhang & Schaap 2017, Journal of Hydrology 547:39-53, DOI 10.1016/j.jhydrol.2017.01.004", "runtime_source": "USDA-ARS usda-ars-ussl/rosetta-soil candidate only", "applicability": "NOT_APPLICABLE", "reason": "required ARCANA texture and optional bulk-density inputs are absent", "inputs": ["sand", "silt", "clay", "optional bulk density", "optional retention points"], "outputs": ["theta_r", "theta_s", "alpha", "n", "Ksat", "K0", "L"], "uncertainty": "would retain mean/uncertainty if later eligible", "unit_crosswalk": "candidate only: Rosetta Ksat cm/day -> BIOME4 mm/hr by 10/24 after runtime contract verification", "invoked": False},
        "pedogenesis_requirement": {"required": True, "decision": "PEDOGENESIS_PROVIDER_REQUIRED", "minimum_inputs_missing": ["parent material/grain size", "physical texture", "weathering duration", "drainage", "erosion/deposition", "vegetation/organic inputs", "vertical profile"], "custom_geology_to_texture_lookup": False, "provider_warning": "Rosetta3 is downstream of physical texture/profile authority; SoilGen or another pedogenesis model cannot be assumed to supply missing initial parent-material/soil conditions"},
        "spatial_resolution": {"target_grid": "90 x 180 if/when shared BIOME4 adapter is authorized", "source_grid": "none", "land_mask": "none bound by P7S", "resampling": False, "layer_count": 6, "snapshot_count": 12},
        "soil_authority_bound": False,
        "soil_materialization_method_defined": False,
        "soil_authority_bound": False,
        "soil_materialization_method_defined": True,
        "decision": "PEDOGENESIS_PROVIDER_REQUIRED",
        "recommended_next_operation": "R5.17-B7-A3F2-P7G PEDOGENESIS / PARENT-MATERIAL PROVIDER ADJUDICATION",
        "governance": {"BIOME4_runtime_ready": True, "BIOME4_scientific_run": False, "PALEO_CO2_AUTHORITY_BOUND": True, "physical_npp_materialized": False, "soil_physical_state_materialized": False, "Madingley_invoked": False, "animal_resource_support_materialized": False, "human_management_used": False, "population_target_used": False, "k_x_t_materialized": False, "canonical_mutation": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED"},
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text("# R5.17-B7-A3F2-P7S\n\n## Decision\n\n**PEDOGENESIS_PROVIDER_REQUIRED**. The pinned BIOME4 source and Kaplan et al. (2003, DOI 10.1029/2002JD002559) support interpreting BIOME4 WHC as available water-holding capacity / plant-available water storage, not total pore space. The exact historical texture-class derivation and pressure conventions remain caveats.\n\nARCANA remains Level E: no governed direct physical soil arrays, texture, bulk density, soil depth/profile, or hydraulic state exist. Existing geology, climate, hydrology, forage, and resource proxies are not promoted to soil. Rosetta3 is not applicable because it is downstream of physical texture/profile authority; a pedogenesis provider must first be adjudicated and may itself require governed parent-material and initial soil conditions.\n\nThe exact P7T 12-age registry is preserved for future P8 construction. No soil arrays were materialized. No BIOME4 scientific run, physical NPP, Madingley, animal resource support, `K(x,t)`, state/index update, staging, commit, or push occurred. `AQUATIC_MARINE_RESOURCE_SUPPORT = NOT_MATERIALIZED`.\n", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}")


if __name__ == "__main__":
    main()
