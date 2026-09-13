from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

HEAD = "43731502aa210f0714473f0f71606eaf5f769375"
P7T_JSON = Path("R5_17_B7_A3F2_P7T_HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY.json")
P7T_MD = Path("R5_17_B7_A3F2_P7T_HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY.md")
REGISTRY = Path("R5_17_B7_A3F2_P7T_TEMPORAL_SNAPSHOT_REGISTRY.csv")
R327_NPZ = Path("outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz")
R327_CP = Path("outputs/v0_6D1_R3_27/R3_27_HUMAN_200KA_CHECKPOINT.json")
R328_NPZ = Path("outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz")
R328_CP = Path("outputs/v0_6D1_R3_28/R3_28_HUMAN_0KA_CHECKPOINT.json")
P7C = Path("R5_17_B7_A3F2_P7C_PALEO_CO2_AUTHORITY_BINDING.json")
CONTRACTS = [Path("R3_27_HOMININ_MACRO_REPLAY_CONTRACT.md"), Path("R3_28_HIGH_RESOLUTION_200KA_TO_0_CONTRACT.md"), Path("R5_17_HUMAN_SUPPORT_CAPACITY_BRIDGE_CONTRACT.md"), Path("R5_17_B7_BIOLOGICAL_FOOD_SUPPORT_CONTRACT.md")]
AGES = [200.0, 125.0, 120.0, 20.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 5.0, 0.0]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checkpoint(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    head = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    if head != HEAD:
        raise RuntimeError("ARCANA HEAD changed during P7T continuation")
    required = [R327_NPZ, R327_CP, R328_NPZ, R328_CP, P7C, *CONTRACTS]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise RuntimeError(f"missing governed input(s): {missing}")
    r327cp, r328cp = checkpoint(R327_CP), checkpoint(R328_CP)
    if r327cp.get("age_ka") != 200.0 or r327cp.get("status") != "HUMAN_200KA_MACROEVOLUTIONARY_CANDIDATE_CHECKPOINT":
        raise RuntimeError("R3.27 200 ka checkpoint semantics failed")
    if r328cp.get("age_ka") != 0.0 or r328cp.get("status") != "HUMAN_0KA_POPULATION_CHECKPOINT":
        raise RuntimeError("R3.28 0 ka checkpoint semantics failed")
    r327 = np.load(R327_NPZ, allow_pickle=False)
    r328 = np.load(R328_NPZ, allow_pickle=False)
    r328_ages = [float(x) for x in r328["snapshot_age_ka"]]
    if 200.0 not in r328_ages or 125.0 not in r328_ages or 0.0 not in r328_ages:
        raise RuntimeError("R3.28 does not contain required 200/125/0 snapshot anchors")
    if any(age not in r328_ages for age in (20.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 5.0)):
        raise RuntimeError("recent shared registry age is not present in R3.28 snapshot authority")

    rows = []
    for age in AGES:
        rows.append({"age_ka": age, "source_authorities": "R3.27/R3.28 human replay; R3.18/R3.19/R3.20 environmental authority as applicable", "climate_readiness": "PARTIAL_GOVERNED_REPLAY_OR_PROXY", "shoreline_readiness": "PARTIAL_SOURCE_SPECIFIC", "hydrology_readiness": "DIRECT_ONLY_15_TO_11KA_R3.20; OTHERWISE_SOURCE_SPECIFIC", "plant_resource_state": "RECENT_OR_PROXY_ONLY; NOT_PHYSICAL_NPP", "human_replay_relevance": "EXPLICIT_R3.28_SHARED_SNAPSHOT" if age in r328_ages else "R3.19_ENVIRONMENTAL_ENDPOINT", "BIOME4_prerequisite_readiness": "NOT_READY_PHYSICAL_CO2_SOIL_CLIMATE_INPUTS_INCOMPLETE", "Madingley_prerequisite_readiness": "NOT_READY_PHYSICAL_NPP_AND_RANGE_INPUTS_INCOMPLETE", "soil_semantics": "P7S_DECIDES_STATIC_TIME_VARYING_OR_MIXED", "CO2_semantics": "P7C_BINDS_VALUES_LATER; PHYSICAL_RECORD_COVERAGE_CHECK_ONLY"})
    with REGISTRY.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    p7c = json.loads(P7C.read_text(encoding="utf-8"))
    result = {
        "stage": "R5.17-B7-A3F2-P7T", "status": "HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY_READY", "authoritative_arcana_head": HEAD,
        "human_200ka_checkpoint": {"verified": True, "path": str(R327_NPZ), "sha256": sha(R327_NPZ), "checkpoint_path": str(R327_CP), "checkpoint_sha256": sha(R327_CP), "schema_key_evidence": sorted(r327.files), "state_shape": {k: list(r327[k].shape) for k in r327.files}, "semantic_provenance": r327cp["interpretation"], "authority_status": "GOVERNED_HUMAN_REPLAY_BOUNDARY"},
        "human_0ka_checkpoint": {"verified": True, "path": str(R328_NPZ), "sha256": sha(R328_NPZ), "checkpoint_path": str(R328_CP), "checkpoint_sha256": sha(R328_CP), "schema_key_evidence": sorted(r328.files), "state_shape": {k: list(r328[k].shape) for k in r328.files}, "semantic_provenance": r328cp["interpretation"], "authority_status": "GOVERNED_HUMAN_REPLAY_ENDPOINT"},
        "temporal_domains": {"WORLD_CONTEXT_DOMAIN": "210 Ma -> 0 ka model-relative context", "BIOLOGICAL_RESOURCE_RECONSTRUCTION_DOMAIN": "B7 remains source-heterogeneous and is not silently expanded to 210 Ma", "HUMAN_SUPPORT_OPERATIONAL_DOMAIN": "200 ka -> 0 ka"},
        "minimum_sufficient_domain": {"HUMAN_SUPPORT_START_AGE": 200.0, "HUMAN_SUPPORT_END_AGE": 0.0, "classification": "GOVERNED_HUMAN_REPLAY_BOUNDARY", "rationale": "R3.27 200 ka is the first explicit governed human-scale macro-replay checkpoint feeding R3.28; this does not claim human origins at 200 ka"},
        "candidate_anchor_adjudication": {"200": "R3.27/R3.28 human replay boundary", "125": "R3.28 explicit human replay snapshot and R3.19 biology boundary", "120": "R3.17/R3.18 exact environmental restart boundary; retained as shared environmental transition", "20": "R3.28 explicit human replay snapshot", "15": "R3.28 snapshot plus R3.20 hazard interval boundary", "14": "R3.28 snapshot plus R3.20 hazard interval", "13": "R3.28 snapshot plus R3.20 hazard interval", "12": "R3.28 snapshot plus R3.20 hazard interval", "11": "R3.28 snapshot plus R3.20 hazard interval endpoint", "10": "R3.28 explicit human replay snapshot", "5": "R3.28 explicit human replay snapshot", "0": "R3.28 explicit human replay endpoint"},
        "shared_temporal_registry": {"classification": "ADAPTIVE_TEMPORAL_SNAPSHOT_REGISTRY", "ages_ka_before_model_present": AGES, "count": len(AGES), "oldest": 200.0, "youngest": 0.0, "zero_ka_included": True, "path": str(REGISTRY), "sha256": sha(REGISTRY), "BIOME4_compatible_snapshot_count": len(AGES), "Madingley_compatible_snapshot_count": len(AGES)},
        "interpolation_contract": {"CO2": "LINEAR_INTERPOLABLE between physical observations only after P7C resolves datum/domain; no values bound by P7T", "climate": "EXACT_SNAPSHOT_OR_GOVERNED_REPLAY_SEMANTICS", "soil": "UNRESOLVED_P7S_DECIDES_STATIC_APPROXIMATION_TIME_VARYING_RECONSTRUCTED_OR_MIXED", "NPP": "computed only at selected BIOME4 snapshots after inputs close", "Madingley": "same shared snapshots unless explicit provider subgrid is justified", "human_support": "component-specific; no generic interpolation", "shoreline": "EVENT_DISCONTINUITY/explicit snapshots where topology changes", "species_ecological_state": "NOT_INTERPOLABLE generically"},
        "co2_dependency": {"BIOME4_CO2_REQUIRED_SNAPSHOT_AGES": AGES, "OLDEST_CO2_SNAPSHOT": 200.0, "YOUNGEST_CO2_SNAPSHOT": 0.0, "snapshot_count": len(AGES), "NOAA_COVERAGE_POTENTIALLY_SUFFICIENT": True, "coverage_years_bp": p7c["external_authority"]["coverage"], "values_bound": False, "datum": "not selected by P7T"},
        "soil_dependency": {"SOIL_REQUIRED_SNAPSHOT_AGES": AGES, "temporal_semantics": "UNRESOLVED_FOR_P7S", "independent_grid_prohibited": True},
        "adaptive_temporal_resolution": True,
        "decision": "HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY_READY",
        "governance": {"BIOME4_scientific_run": False, "Madingley_invoked": False, "physical_npp_materialized": False, "paleo_co2_values_bound": False, "soil_physical_state_materialized": False, "animal_resource_support_materialized": False, "human_management_used": False, "population_target_used": False, "k_x_t_materialized": False, "canonical_mutation": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED"},
        "recommended_next": "Resume existing P7C for coverage/datum adjudication, then run P7S using this exact shared registry",
    }
    P7T_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    P7T_MD.write_text("# R5.17-B7-A3F2-P7T\n\n## Decision\n\n**HUMAN_SUPPORT_TEMPORAL_SNAPSHOT_AUTHORITY_READY**. Direct inspection verifies the governed R3.27 human-scale macro-replay checkpoint at 200 ka and the governed R3.28 human replay endpoint at 0 ka. The operational human-support domain is therefore 200 ka -> 0 ka, without claiming human origins at 200 ka.\n\nThe shared `ADAPTIVE_TEMPORAL_SNAPSHOT_REGISTRY` is `200, 125, 120, 20, 15, 14, 13, 12, 11, 10, 5, 0 ka`. R3.20's 50-year 15–11 ka hazard frames remain event/hazard evidence, not automatic BIOME4 snapshots. P7C receives the same CO₂ ages, but no CO₂ values or datum are bound here; P7S must use the same registry.\n\nNo BIOME4 or Madingley run, NPP, soil, CO₂ value binding, `K(x,t)`, state/index update, staging, commit, or push occurred. `AQUATIC_MARINE_RESOURCE_SUPPORT = NOT_MATERIALIZED`.\n", encoding="utf-8")
    print(f"wrote {P7T_JSON}, {P7T_MD}, and {REGISTRY}")


if __name__ == "__main__":
    main()
