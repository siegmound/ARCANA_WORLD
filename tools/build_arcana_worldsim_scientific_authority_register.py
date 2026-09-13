"""Build the governed ARCANA WorldSim scientific-authority register.

This audit inventories only authority already evidenced in the repository.
It deliberately neither creates scientific state nor changes provider choices.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "ARCANA_WORLDSIM_SCIENTIFIC_AUTHORITY_REGISTER.json"
OUT_MD = ROOT / "ARCANA_WORLDSIM_SCIENTIFIC_AUTHORITY_REGISTER.md"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_records(paths: list[str]) -> list[dict]:
    records = []
    for raw in paths:
        path = ROOT / raw
        records.append({
            "path": raw,
            "present": path.is_file(),
            "sha256": digest(path) if path.is_file() else None,
        })
    return records


def domain(
    domain_id: str, status: str, origin_stage: str, authority_class: list[str],
    producer: str, artifacts: list[str], variables: list[str], spatial: str,
    temporal: str, meaning: str, ceiling: list[str], excludes: list[str],
    reuse: str, *, superseded_by: str | None = None, adjudicated_by: list[str] | None = None,
    consumers: list[str] | None = None,
) -> dict:
    evidence = source_records(artifacts)
    return {
        "domain_id": domain_id,
        "status": status,
        "origin_stage": origin_stage,
        "authority_class": authority_class,
        "producer_provider": producer,
        "source_artifacts": [x["path"] for x in evidence],
        "source_hashes": {x["path"]: x["sha256"] for x in evidence},
        "source_presence": {x["path"]: x["present"] for x in evidence},
        "variables": variables,
        "spatial_support": spatial,
        "temporal_support": temporal,
        "semantic_meaning": meaning,
        "SEMANTIC_CEILING": ceiling,
        "DOES_NOT_SUPPORT": excludes,
        "current_reuse_status": reuse,
        "superseded_by": superseded_by,
        "adjudicated_by": adjudicated_by or [],
        "downstream_consumers": consumers or [],
    }


def main() -> None:
    a1 = "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"
    d32c = "outputs/v0_6D1_R3/PALEOGEOGRAPHIC_EVENT_CATALOG_ALL_A1_v0_6D1_R3.json"
    climate = "local_bindings/v0_6D1_R3_14/v0_6_1_SEALED_MINIMAL/outputs/hybrid1/paleoclimate_v0_6_1/recent_paleoclimate_history.npz"
    hydro = "R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY.json"
    flora = "R5_17_B7_A3_PLANT_MATERIALIZATION_AND_WILD_FAUNA_AUTHORITY_CENSUS.json"
    fauna = "outputs/v0_6D1_R3_21/R3_21_PRESENT_LINEAGE_REGISTRY.json"
    p7ar = "R5_17_B7_A3F2_P7AR_TARGETED_PARENT_MATERIAL_AUTHORITY_RECOVERY.json"
    p7nc1r = "R5_17_B7_A3F2_P7NC1R_LEGACY_GEOLOGIC_TECTONIC_AUTHORITY_RECOVERY.json"
    entries = [
        domain("PALEOGEOGRAPHY", "CONFIRMED", "A1 / D3.2C", ["CONFIRMED_LEGACY_AUTHORITY"], "A1 endpoint reference plus D3.2C adapter", [a1, d32c], ["age_ma", "land_mask", "plate_code"], "90x180 global grid", "11 endpoints, 210–0 Ma; bracketed transitions", "Endpoint-constrained land/ocean geography.", ["land/ocean endpoint state", "derived transition organization"], ["lithology", "crustal composition", "parent material"], "REUSE_CANONICAL_ARCANA", adjudicated_by=[p7nc1r], consumers=["B6 shoreline adapter", "P7Q if opened"]),
        domain("PLATE_KINEMATICS", "CONFIRMED", "A1 / D3.2C", ["CONFIRMED_LEGACY_AUTHORITY"], "A1 plate-code field and D3.2C event reconstruction", [a1, d32c, p7nc1r], ["plate_code", "transition event clusters"], "90x180 global grid", "210–0 Ma, 11 endpoints; 10 brackets", "Discrete endpoint-constrained plate/cell identity and paleogeographic organization.", ["plate/cell identity", "endpoint-constrained transitions", "210–0 Ma kinematic scaffold"], ["formal rotation/topology model", "lithology", "crustal composition", "mineralogy", "parent material"], "REUSE_CANONICAL_ARCANA", consumers=["P7NC1R", "future conditioned geological gate"]),
        domain("SHORELINE_LAND_OCEAN", "CONFIRMED", "A1 / R3.14 / B6-D2C1", ["CONFIRMED_LEGACY_AUTHORITY", "RECOVERED_REPLAY_AUTHORITY"], "A1 land mask and canonical shoreline binding", [a1, "R5_17_B6_D2C1_SHORELINE_LAND_MASK_ADAPTER_ADJUDICATION.json"], ["land_mask", "shoreline state"], "Global A1 grid; recent binding", "210–0 Ma endpoints; recent detailed binding", "Land/ocean and shoreline support for governed adapters.", ["shoreline/accessibility condition"], ["physical geology", "coastal sediment composition", "parent material"], "REUSE_CANONICAL_ARCANA", consumers=["B6 hydrology", "P7 parent-material gates"]),
        domain("CLIMATE", "CONFIRMED", "R3.14 / A1", ["CONFIRMED_LEGACY_AUTHORITY"], "R3.14 sealed paleoclimate binding", [climate, a1], ["temperature_c", "aridity_index"], "A1 global grid; R3.14 spatial snapshots", "A1 210–0 Ma; recent paleoclimate history", "Governed climate and environmental forcing.", ["climatic forcing and diagnostics"], ["lithology", "physical soil", "freshwater access without hydrology replay"], "REUSE_CANONICAL_ARCANA", consumers=["B6", "B7"]),
        domain("PALEOCLIMATE", "CONFIRMED", "R3.14", ["CONFIRMED_LEGACY_AUTHORITY"], "R3.14 sealed paleoclimate provider binding", [climate], ["recent paleoclimate history", "spatial snapshots"], "Recent spatial snapshots", "Late-Cenozoic governed history", "Sealed recent paleoclimate authority.", ["recent paleoclimate history"], ["physical NPP", "soil state", "bedrock"], "REUSE_CANONICAL_ARCANA", consumers=["B6", "P7N/P7NC conditioning"]),
        domain("HYDROLOGY", "CONFIRMED", "Original lineage recovered in B6", ["CONFIRMED_ORIGINAL_AUTHORITY", "RECOVERED_REPLAY_AUTHORITY"], "Native hydrology generator; B6 canonical replay", [hydro, "R5_17_B6_H3_NATIVE_HYDROLOGY_GENERATOR_SEMANTICS.json"], ["paleohydrological dynamics", "replay diagnostics"], "Governed ARCANA spatial support", "B6 replay temporal domain", "Canonical paleohydrological process/replay authority.", ["paleohydrological reconstruction"], ["soil hydraulic parameters", "geological substrate"], "REUSE_CANONICAL_ARCANA", consumers=["B6 freshwater", "P7 conditioning"]),
        domain("PALEOHYDROLOGY", "CONFIRMED", "R5.17-B6-D3", ["RECOVERED_REPLAY_AUTHORITY"], "B6 canonical paleohydrology replay", [hydro], ["paleohydrology fields"], "Governed replay grid", "B6 authorized temporal domain", "Materialized canonical paleohydrology replay.", ["replayed hydrological state"], ["physical soil", "lithology"], "REUSE_CANONICAL_ARCANA", consumers=["FRESHWATER"]),
        domain("FRESHWATER", "CONFIRMED", "R5.17-B6-D4", ["LATER_DERIVED_AUTHORITY"], "B6 freshwater access/reliability derivation", ["R5_17_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY.json"], ["freshwater access", "hydrological reliability"], "Governed B6 support grid", "B6 temporal domain", "Materialized freshwater-support and reliability state.", ["freshwater support", "hydrological reliability"], ["soil moisture", "Ksat", "physical soil parameters"], "REUSE_CANONICAL_ARCANA", consumers=["human-support bridge"]),
        domain("HYDROLOGICAL_HAZARD", "CONFIRMED", "R3.20", ["CONFIRMED_ORIGINAL_AUTHORITY"], "R3.20 CHA-2 hydrological-hazard layer", ["local_runs/v0_6D1_R3_20/R3_20_CHA2_YD_MAGNITUDE_AND_HYDROLOGICAL_HAZARD_SUMMARY.json"], ["hazard indices"], "R3.20 local run grid", "15–11 ka interval", "Diagnostic/ranking hydrological hazard state.", ["hazard ranking"], ["flood depth", "guaranteed inundation", "freshwater supply"], "REUSE_CANONICAL_ARCANA"),
        domain("FLORA", "CONFIRMED", "R5.17-B7-A3", ["LATER_DERIVED_AUTHORITY"], "B7-A3 plant materialization", [flora], ["plant trophic materialization"], "Governed biological spatial support", "B7-A3 authorized domain", "Plant ecological/trophic authority.", ["plant trophic support"], ["physical NPP", "physical soil"], "REUSE_CANONICAL_ARCANA", consumers=["B7 food-support work"]),
        domain("VEGETATION", "CONFIRMED", "A1 / B7-A3", ["CONFIRMED_LEGACY_AUTHORITY", "LATER_DERIVED_AUTHORITY"], "A1 forage fields and B7-A3", [a1, flora], ["browse_forage", "low_forage", "wetland_forage", "total_edible_forage"], "90x180 global grid", "210–0 Ma endpoints; B7 refinement", "Ecological vegetation/forage support.", ["ecological/forage support"], ["physical NPP", "soil profile"], "REUSE_CANONICAL_ARCANA"),
        domain("PLANT_ECOLOGY", "CONFIRMED", "R5.17-B7-A3", ["LATER_DERIVED_AUTHORITY"], "B7-A3 plant authority", [flora], ["plant support state"], "Governed biological support", "B7-A3 domain", "Plant ecological state.", ["plant ecological support"], ["physical NPP", "edaphic process state"], "REUSE_CANONICAL_ARCANA"),
        domain("PLANT_TROPHIC_SUPPORT", "CONFIRMED", "R5.17-B7-A3.1/A3.2", ["LATER_DERIVED_AUTHORITY"], "B7-A3 materialization and refinement", [flora], ["trophic plant support"], "Governed biological support", "B7-A3 domain", "Completed plant trophic materialization/refinement.", ["plant trophic resource support"], ["animal biomass", "physical NPP", "human harvest"], "REUSE_CANONICAL_ARCANA"),
        domain("FAUNA", "CONFIRMED", "R3.21 / B7-A3 census", ["CONFIRMED_LEGACY_AUTHORITY", "LATER_DERIVED_AUTHORITY"], "R3.21 lineage registry and B7-A3 census", [fauna, flora], ["present lineages", "component census"], "Registry rather than full historical range grid", "Historical closure plus present registry", "Biological/ecological lineage and component authority.", ["lineage and component identity"], ["exact historical range for every species", "exact historical abundance"], "REUSE_CANONICAL_ARCANA", consumers=["A3F2"]),
        domain("ANIMAL_ECOLOGY", "CONFIRMED", "R3.21", ["CONFIRMED_LEGACY_AUTHORITY"], "R3.21 functional phenotype interface", ["outputs/v0_6D1_R3_21/R3_21_FUNCTIONAL_PHENOTYPE_FORK_INTERFACE.json"], ["functional phenotype interface"], "Registry/interface support", "R3.21 closure", "Functional/phenotype evidence for extant lineage components.", ["ecological/functional traits"], ["spatial abundance", "historical range reconstruction"], "REUSE_CANONICAL_ARCANA"),
        domain("BIODIVERSITY", "CONFIRMED", "R3.21", ["CONFIRMED_LEGACY_AUTHORITY"], "R3.21 present lineage registry", [fauna], ["lineage registry"], "Registry support", "Present and closure support", "Governed lineage biodiversity inventory.", ["lineage existence/identity"], ["abundance", "cell occupancy"], "REUSE_CANONICAL_ARCANA"),
        domain("SPECIES_EVOLUTION", "CONFIRMED", "R3.21", ["CONFIRMED_LEGACY_AUTHORITY"], "R3.21 historical lineage closure", ["outputs/v0_6D1_R3_21/R3_21_HISTORICAL_LINEAGE_CLOSURE.json"], ["origination/termination closure"], "Lineage registry support", "Historical lineage intervals", "Lineage temporal continuity authority.", ["existence intervals"], ["range", "population size"], "REUSE_CANONICAL_ARCANA"),
        domain("SPECIES_REGISTRY", "CONFIRMED", "R3.21", ["CONFIRMED_LEGACY_AUTHORITY"], "R3.21 present component registry", [fauna, "outputs/v0_6D1_R3_21/R3_21_PRESENT_COMPONENT_REGISTRY.json"], ["species", "components"], "Registry support", "Present endpoint plus historical closure", "Species/component identity registry.", ["identity continuity"], ["historical occupancy", "abundance"], "REUSE_CANONICAL_ARCANA"),
        domain("NPP_PRODUCTIVITY", "PROXY_ONLY", "A1 / P4", ["DERIVED_PROXY_ONLY"], "A1 normalized forage/NPP proxy", [a1, "R5_17_B7_A3F2_P4_PHYSICAL_NPP_AUTHORITY_RECOVERY.json"], ["normalized NPP proxy"], "A1 90x180 grid", "A1 endpoints", "Normalized productivity proxy only.", ["relative/normalized productivity proxy"], ["physical NPP", "mass/area/time NPP", "BIOME4 production output"], "DO_NOT_REUSE_AS_PHYSICAL_NPP"),
        domain("GEOLOGY", "ABSENT", "P7AR / P7NC1R", ["ABSENT_AFTER_EXHAUSTIVE_RECOVERY"], "Targeted authority recovery", [p7ar, p7nc1r], [], "None recovered", "None recovered", "No governed physical geology authority was recovered.", [], ["lithology", "geological province", "crustal state", "parent material"], "TARGETED_RECOVERY_COMPLETE"),
        domain("LITHOLOGY", "ABSENT", "P7AR", ["ABSENT_AFTER_EXHAUSTIVE_RECOVERY"], "P7AR targeted recovery", [p7ar], [], "None", "None", "No governed lithology occurrence authority.", [], ["bedrock lithology", "mineralogy", "grain-size"], "TARGETED_RECOVERY_COMPLETE"),
        domain("CRUSTAL_STATE", "UNRESOLVED", "P7NC1R", ["UNRESOLVED"], "P7NC1R legacy tectonic recovery", [p7nc1r], ["plate_code only"], "Endpoint grid identity only", "210–0 Ma endpoints", "Kinematic constraint exists; crustal composition/domain authority was not recovered.", ["kinematic conditioning only"], ["crustal composition", "crustal domain state"], "TARGETED_RECOVERY_COMPLETE"),
        domain("PARENT_MATERIAL", "ABSENT", "P7AR", ["ABSENT_AFTER_EXHAUSTIVE_RECOVERY"], "P7AR targeted recovery", [p7ar], [], "None", "None", "Physical parent-material authority absent after exhaustive recovery.", [], ["texture", "regolith depth", "bulk density", "mineralogy", "vertical profile"], "TARGETED_RECOVERY_COMPLETE"),
        domain("REGOLITH", "ABSENT", "P7AR / P7G", ["ABSENT_AFTER_EXHAUSTIVE_RECOVERY"], "P7AR recovery and P7G adjudication", [p7ar, "R5_17_B7_A3F2_P7G_PEDOGENESIS_PARENT_MATERIAL_PROVIDER.json"], [], "None", "None", "No regolith depth or physical profile authority.", [], ["regolith depth", "vertical profile", "bulk density"], "TARGETED_RECOVERY_COMPLETE"),
        domain("SOIL_PHYSICAL", "ABSENT", "P7S", ["NOT_MATERIALIZED"], "P7S physical-soil authority gate", ["R5_17_B7_A3F2_P7S_PHYSICAL_SOIL_AND_PEDOTRANSFER_AUTHORITY.json"], [], "None", "None", "No physical soil/pedotransfer input authority.", [], ["texture", "porosity", "bulk density", "hydraulic properties"], "TARGETED_RECOVERY_COMPLETE"),
        domain("SOIL_CARBON", "PROXY_ONLY", "P7AR", ["DERIVED_PROXY_ONLY"], "ARCANA weathering/carbon proxy lineage", [p7ar], ["weathering/carbon proxy"], "As documented in P7AR", "As documented in P7AR", "Proxy/process state, not physical soil carbon.", ["proxy/process conditioning"], ["physical soil carbon stock", "soil profile"], "DO_NOT_REUSE_AS_PHYSICAL_SOIL"),
        domain("WEATHERING", "PROXY_ONLY", "P7AR", ["DERIVED_PROXY_ONLY"], "ARCANA weathering state", [p7ar], ["WEATHERING_STATE"], "As documented in P7AR", "As documented in P7AR", "Weathering state is proxy-only.", ["process/proxy signal"], ["lithology", "parent material", "mineralogy"], "DO_NOT_REUSE_AS_GEOLOGY"),
        domain("BARRIERS", "CONFIRMED", "D3.2C", ["CONFIRMED_LEGACY_AUTHORITY"], "D3.2C barrier-history adapter", [d32c], ["land/ocean transition clusters"], "90x180 global grid", "210–0 Ma bracketed history", "Endpoint-constrained barrier history.", ["barrier/topology transitions"], ["geological provinces", "material transport provenance"], "REUSE_CANONICAL_ARCANA"),
        domain("CONNECTIVITY", "CONFIRMED", "D3.2C", ["CONFIRMED_LEGACY_AUTHORITY"], "D3.2C paleogeographic connectivity scaffold", [d32c], ["transition clusters", "plate/cell identity"], "90x180 global grid", "210–0 Ma bracketed history", "Paleogeographic connectivity scaffold only.", ["geographic connectivity conditioning"], ["genetic connectivity output", "species dispersal realization"], "REUSE_CANONICAL_ARCANA"),
        domain("MARINE_AQUATIC_STATE", "NOT_MATERIALIZED", "B7 governance", ["NOT_MATERIALIZED"], "B7 authority census", [flora], [], "None", "None", "Aquatic/marine resource support has not been materialized.", [], ["marine/aquatic biological resource support"], "DO_NOT_INFER"),
        domain("TOPOGRAPHY", "CONFIRMED", "ARCANA terrain lineage; P7G inventory", ["CONFIRMED_LEGACY_AUTHORITY"], "ARCANA elevation/topography state", ["R5_17_B7_A3F2_P7G_PEDOGENESIS_PARENT_MATERIAL_PROVIDER.json"], ["elevation/topography"], "Governed terrain support as documented by P7G", "Applicable inherited snapshot domain", "Topographic conditioning state.", ["elevation/topography conditioning"], ["lithology", "bedrock", "soil physical state"], "REUSE_CANONICAL_ARCANA"),
        domain("RELIEF", "CONFIRMED", "ARCANA terrain lineage; P7G inventory", ["CONFIRMED_LEGACY_AUTHORITY"], "ARCANA elevation/topography state", ["R5_17_B7_A3F2_P7G_PEDOGENESIS_PARENT_MATERIAL_PROVIDER.json"], ["relief/elevation conditioning"], "Governed terrain support as documented by P7G", "Applicable inherited snapshot domain", "Terrain-relief conditioning state.", ["terrain conditioning"], ["lithology", "regolith", "soil profile"], "REUSE_CANONICAL_ARCANA"),
        domain("ENVIRONMENTAL_INTEGRALS", "CONFIRMED", "R3.18", ["CONFIRMED_ORIGINAL_AUTHORITY"], "R3.18 exposure-completion transport-phase authority", ["local_runs/v0_6D1_R3_18/R3_18_RECENT_EXPOSURE_COMPLETION_SUMMARY.json"], ["integrated exposure fields", "transport phases"], "Recent R3.18 support", "125 ka–0", "Integrated environmental exposures.", ["environmental exposure integrals"], ["physical population", "carrying capacity", "soil or geology"], "REUSE_CANONICAL_ARCANA"),
    ]
    document = {
        "record_id": "ARCANA_WORLDSIM_SCIENTIFIC_AUTHORITY_REGISTER",
        "title": "ARCANA WorldSim Scientific Authority Register",
        "purpose": "Persistent cross-cutting inventory of existing scientific authority. It is a governance register, not a scientific generator.",
        "governance_rule": [
            "Before declaring a scientific authority absent, consult this register.",
            "Inspect registered producer/provenance and respect its semantic ceiling.",
            "Perform targeted recovery only when the relevant entry is UNRESOLVED.",
            "Do not infer absence from ARCANA_WORLD_CURRENT_STATE.md alone.",
        ],
        "p7q_status": "SUSPENDED_PENDING_REGISTER_REVIEW",
        "domain_count": len(entries),
        "domains": entries,
        "governance": {"new_science_created": False, "provider_selection_reopened": False, "missing_state_inferred": False, "current_state_modified": False, "canonical_mutation": False},
    }
    OUT_JSON.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# ARCANA WorldSim Scientific Authority Register", "", "Governed cross-cutting authority inventory. It records only evidenced state and its semantic ceiling; it does not create science.", "", "## Mandatory gate", "", *[f"{i + 1}. {rule}" for i, rule in enumerate(document["governance_rule"])], "", "## Domain inventory", "", "| Domain | Status | Authority class | Semantic ceiling |", "|---|---|---|---|"]
    for item in entries:
        lines.append(f"| {item['domain_id']} | {item['status']} | {', '.join(item['authority_class'])} | {'; '.join(item['SEMANTIC_CEILING']) or 'none'} |")
    lines += ["", "## P7Q", "", "P7Q is suspended pending review. The register confirms a reusable paleogeographic/kinematic scaffold, while physical geology, lithology, parent material, regolith, and physical soil remain unavailable or unresolved as explicitly stated in their entries.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_JSON.name} ({len(entries)} domains)")
    print(f"wrote {OUT_MD.name}")


if __name__ == "__main__":
    main()
