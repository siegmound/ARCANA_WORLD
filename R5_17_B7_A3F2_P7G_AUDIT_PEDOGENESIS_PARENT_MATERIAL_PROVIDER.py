from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HEAD = "43731502aa210f0714473f0f71606eaf5f769375"
P7S = Path("R5_17_B7_A3F2_P7S_PHYSICAL_SOIL_AND_PEDOTRANSFER_AUTHORITY.json")
P7T = Path("R5_17_B7_A3F2_P7T_HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY.json")
P7C = Path("R5_17_B7_A3F2_P7C_PALEO_CO2_AUTHORITY_BINDING.json")
P7G_JSON = Path("R5_17_B7_A3F2_P7G_PEDOGENESIS_PARENT_MATERIAL_PROVIDER.json")
P7G_MD = Path("R5_17_B7_A3F2_P7G_PEDOGENESIS_PARENT_MATERIAL_PROVIDER.md")
LOCAL = [Path("R5_17_HUMAN_SUPPORT_CAPACITY_BRIDGE_CONTRACT.md"), Path("R5_17_B7_BIOLOGICAL_FOOD_SUPPORT_CONTRACT.md"), Path("R3_27_HOMININ_MACRO_REPLAY_CONTRACT.md"), Path("R3_28_HIGH_RESOLUTION_200KA_TO_0_CONTRACT.md")]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    current = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    if current != HEAD:
        raise RuntimeError("ARCANA HEAD changed during P7G")
    required = [P7S, P7T, P7C, *LOCAL]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise RuntimeError(f"missing P7G input(s): {missing}")
    p7s = json.loads(P7S.read_text(encoding="utf-8"))
    p7t = json.loads(P7T.read_text(encoding="utf-8"))
    p7c = json.loads(P7C.read_text(encoding="utf-8"))
    result = {
        "stage": "R5.17-B7-A3F2-P7G",
        "parent_head": HEAD,
        "p7s_parent_decision": p7s["decision"],
        "temporal_parent": {"p7t_decision": p7t["decision"], "domain": p7t["temporal_domains"]["HUMAN_SUPPORT_OPERATIONAL_DOMAIN"], "snapshot_ages_ka": p7t["p7t_temporal_authority"]["snapshot_ages_ka"] if "p7t_temporal_authority" in p7t else p7t["shared_temporal_registry"]["ages_ka_before_model_present"]},
        "p7c_co2_parent": {"decision": p7c["decision"], "bound": p7c["governance"]["PALEO_CO2_AUTHORITY_BOUND"]},
        "arcana_parent_material_authority": {"level": "E_INSUFFICIENT", "status": "BLOCKED", "finding": "No governed physical parent-material/regolith profile is available for initializing a world-scale soil provider", "direct_lithology": False, "direct_sediment_composition": False, "direct_regolith_depth": False, "direct_vertical_profile": False},
        "arcana_regolith_authority": {"status": "ABSENT", "physical_regolith_state": False, "weathering_state": False, "grain_size": False, "mineralogy": False, "profile_depth": False},
        "arcana_texture_authority": {"sand_percent": False, "silt_percent": False, "clay_percent": False, "status": "ABSENT"},
        "recovered_upstream_fields": {
            "elevation_topography": {"support": "SATISFIED_DIRECT_OR_GOVERNED_PARENT", "meaning": "canonical elevation/land geometry; not soil depth or texture"},
            "land_sea_shoreline": {"support": "SATISFIED_GOVERNED_DERIVATION", "meaning": "land/accessibility and shoreline endpoint support; not parent material"},
            "hydrology": {"support": "PROXY_PRESENT_NOT_AUTHORIZED", "meaning": "palaeohydrology/freshwater and hazard fields; not Ksat or WHC"},
            "climate": {"support": "PROXY_PRESENT_NOT_AUTHORIZED", "meaning": "temperature/precipitation environmental forcing; not soil texture/profile"},
            "erosion_deposition": {"support": "PROXY_PRESENT_NOT_AUTHORIZED", "meaning": "erosion-related model variables exist in replay semantics but no physical sediment budget/profile"},
            "lithology_parent_material": {"support": "MISSING", "meaning": "no governed material classes, mineral composition, or grain-size state"},
        },
        "non_equivalence_rules": ["bedrock/lithology != soil texture", "geological class != sand/silt/clay fractions", "sediment presence != complete physical regolith profile", "weathering indication != quantitative pedogenic state", "elevation/slope != soil depth"],
        "provider_input_contracts": {
            "SoilGen3.8.2": {"runtime": "Pascal/FreePascal Lazarus; exact local binding absent", "spatial_dimensionality": "1-D soil pedon/profile", "capability": "pedogenesis from an initialized soil or parent material under boundary conditions", "initial_state": "requires a defined initial soil/parent material, layer/profile properties and hydraulic/chemical parameters; exact release input file not locally recovered", "boundary_conditions": ["climate", "water/solute flow", "vegetation/organic inputs", "erosion/deposition where configured"], "outputs": ["profile properties including texture/mineral/organic and bulk-density-related states"], "limitation": "published evaluations report bulk-density limitations; model output presence does not establish authority quality", "source": "https://zenodo.org/records/17414404"},
            "LORICA_ChronoLorica_HydroLorica": {"runtime": "source/runtime not locally bound", "spatial_dimensionality": "raster soilscape evolution", "capability": "evolve pre-defined soil layers/material under relief, lithology and geomorphic/pedogenic processes", "initial_state": ["DEM", "initial soil layers", "texture/material composition", "bulk-density relation or PTF", "boundary/process parameters"], "boundary_conditions": ["relief/overland routing", "erosion/deposition", "climate/hydrology depending variant"], "outputs": ["dynamic layer thickness/composition and soilscape state"], "limitation": "not shown to construct missing ARCANA initial physical profile from synthetic geography alone", "source": "https://www.uibk.ac.at/en/geography/geosoil/modelling/"},
            "SaLEM": {"runtime": "not locally bound", "spatial_dimensionality": "GIS/regolith landscape model", "capability": "lithologically differentiated regolith depth/parent-material evolution", "initial_state": ["site DEM", "geological/lithological model", "initial conditions"], "boundary_conditions": ["periglacial palaeoclimate", "weathering", "erosion", "transport/sedimentation"], "domain_restriction": "specialized periglacial/temperate Northern German case-study setting; not universal ARCANA world provider", "limitation": "does not remove the need for governed initial geological/material state", "source": "https://doi.org/10.5194/gmd-2017-218"},
        },
        "provider_arcana_crosswalk": {
            "SoilGen3.8.2": {"initial_parent_material": "MISSING", "physical_texture": "MISSING", "profile_layers": "MISSING", "climate": "PROXY_PRESENT_NOT_AUTHORIZED", "hydrology": "PROXY_PRESENT_NOT_AUTHORIZED", "world_scale": "BLOCKED_PARENT_STATE"},
            "LORICA_family": {"DEM": "SATISFIED_DIRECT_OR_GOVERNED_PARENT", "lithology": "MISSING", "initial_texture/material": "MISSING", "initial_layers": "MISSING", "erosion/deposition": "PROXY_PRESENT_NOT_AUTHORIZED", "world_scale": "BLOCKED_PARENT_STATE"},
            "SaLEM": {"DEM": "SATISFIED_DIRECT_OR_GOVERNED_PARENT", "geological_model": "MISSING", "lithology": "MISSING", "periglacial_domain": "DOMAIN_RESTRICTED", "world_scale": "DOMAIN_RESTRICTED"},
        },
        "governed_derivations": [],
        "missing_inputs": ["physical parent-material class/composition", "sand/silt/clay or equivalent grain-size state", "initial regolith/soil depth", "vertical layer boundaries", "bulk density/porosity", "mineralogy/carbonate/chemistry as provider requires", "world-scale regime-specific boundary conditions", "land-exposure and soil-development initial conditions"],
        "domain_restrictions": {"SoilGen": "1-D profile/pedon; not by itself a world-scale parent-state generator", "LORICA_family": "soilscape evolution requires initialized physical layers/material", "SaLEM": "periglacial and site/regional specialization; cannot be promoted globally", "global_provider": "no single evaluated provider is globally ready from current ARCANA authority; regime dispatch may be necessary but is not authorized here"},
        "world_scale_assessment": {"spatial_heterogeneity": "not initialized", "multiple_climate_regimes": "boundary proxies exist but physical soil state absent", "multiple_geomorphic_regimes": "not represented as physical parent classes", "long_temporal_trajectories": "temporal registry exists but soil initial state absent", "tiling_reproducibility": "not assessable before provider/input binding", "conclusion": "provider-family/regime dispatch may be necessary; no dispatch authorized"},
        "soilgen_assessment": {"SOILGEN_PEDOGENESIS_CAPABILITY": "CONDITIONALLY_FEASIBLE", "SOILGEN_PARENT_STATE_CREATION_CAPABILITY": "NOT_ESTABLISHED_FROM_CURRENT_AUTHORITY", "bulk_density_caveat": True, "executed": False},
        "lorica_family_assessment": {"capability": "CONDITIONALLY_FEASIBLE_AFTER_INITIAL_PROFILE", "can_create_missing_arcana_profile": False, "executed": False},
        "regolith_provider_assessment": {"SaLEM": "DOMAIN_RESTRICTED_AND_BLOCKED_MISSING_GEOLOGICAL_INITIAL_STATE", "specialist_provider_path": "POTENTIALLY_RELEVANT_BUT_NOT_INITIALIZABLE_FROM_CURRENT_AUTHORITY", "executed": False},
        "rosetta3": {"downstream": True, "texture_generation": False, "executed": False},
        "primary_scientific_decision": "BLOCKED_PARENT_MATERIAL_AUTHORITY_INSUFFICIENT",
        "recommended_next_operation": "TARGETED_PARENT_MATERIAL_AUTHORITY_RECOVERY_FOR_SYNTHETIC_WORLD_REGIMES",
        "governance": {"SoilGen_executed": False, "LORICA_executed": False, "ChronoLorica_executed": False, "HydroLorica_executed": False, "SaLEM_executed": False, "Rosetta3_executed": False, "BIOME4_scientific_run": False, "soil_arrays_materialized": False, "parent_material_arrays_materialized": False, "physical_NPP_materialized": False, "Madingley_invoked": False, "animal_resource_support_materialized": False, "K_x_t_materialized": False, "canonical_mutation": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED"},
    }
    P7G_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    P7G_MD.write_text("# R5.17-B7-A3F2-P7G\n\n## Decision\n\n**BLOCKED_PARENT_MATERIAL_AUTHORITY_INSUFFICIENT**. ARCANA has governed elevation/land geometry and environmental/hydrological proxies, but no physical lithology/material composition, grain-size fractions, regolith depth, bulk density, or initial vertical profile. Those non-equivalent fields are not translated into soil by this gate.\n\nSoilGen3.8.2 can evolve an initialized 1-D soil/parent profile but is not shown to create ARCANA's missing parent state. LORICA-family models evolve initialized soilscape layers and material. SaLEM is a specialized periglacial/site-regional regolith model and is not a universal world provider. Rosetta3 remains downstream of physical texture/profile authority.\n\nNo provider was run and no soil or parent-material arrays were materialized. Recommended next operation: `TARGETED_PARENT_MATERIAL_AUTHORITY_RECOVERY_FOR_SYNTHETIC_WORLD_REGIMES`.\n", encoding="utf-8")
    print(f"wrote {P7G_JSON} and {P7G_MD}")


if __name__ == "__main__":
    main()
