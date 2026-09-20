from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGE = "R5.17-B7-A3F2-P7Q-PRE5J"
PRE5I = ROOT / "R5_17_B7_A3F2_P7Q_PRE5I_ADJUDICATION.json"
REGISTER = ROOT / "ARCANA_WORLDSIM_SCIENTIFIC_AUTHORITY_REGISTER.json"


def write_json(name: str, value: dict) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_preflight() -> tuple[dict, dict]:
    if not PRE5I.exists() or not REGISTER.exists():
        raise RuntimeError("BLOCKED_P7Q_PRE5J_PRE5I_AUTHORITY_OR_REGISTER_UNAVAILABLE")
    pre5i = json.loads(PRE5I.read_text(encoding="utf-8"))
    if pre5i.get("decision") != "AUTHORIZE_P7Q_PRE5J_RESIDUAL_REGOLITH_PROCESS_AUTHORITY_COMPLETION_GATE":
        raise RuntimeError("BLOCKED_P7Q_PRE5J_PRE5I_AUTHORITY_DRIFT")
    if pre5i.get("verdict") != "PASS_P7Q_PRE5I_STATIC_BEDROCK_EXPOSURE_MATERIALIZATION_ADJUDICATED":
        raise RuntimeError("BLOCKED_P7Q_PRE5J_PRE5I_AUTHORITY_DRIFT")
    if any(pre5i.get(k) != 0 for k in ("bedrock_exposed_assigned", "residual_regolith_assigned", "saprolite_assigned")):
        raise RuntimeError("BLOCKED_P7Q_PRE5J_UNAUTHORIZED_CLASSIFICATION_EXECUTED")
    return pre5i, json.loads(REGISTER.read_text(encoding="utf-8"))


def main() -> int:
    pre5i, register = require_preflight()
    domains = {d["domain_id"]: d for d in register["domains"]}
    authority_preflight = {
        "weathering": {"status": domains["WEATHERING"]["authority_status"], "disposition": domains["WEATHERING"]["reuse_disposition"]},
        "erosion": {"status": "MISSING", "disposition": "REQUIRES_TARGETED_RECOVERY", "basis": "No governed EROSION domain in the register."},
        "geomorphology": {"status": "MISSING", "disposition": "REQUIRES_TARGETED_RECOVERY"},
        "sediment_transport": {"status": "MISSING", "disposition": "REQUIRES_TARGETED_RECOVERY"},
        "regolith": {"status": domains["REGOLITH"]["authority_status"], "disposition": domains["REGOLITH"]["reuse_disposition"]},
        "surface_geology": {"status": "INSUFFICIENT", "disposition": "REQUIRES_TARGETED_RECOVERY", "basis": "GEOLOGY and LITHOLOGY are absent after audit."},
        "soil_parent_material": {"status": "INSUFFICIENT", "disposition": "REQUIRES_TARGETED_RECOVERY", "basis": "PARENT_MATERIAL and SOIL_PHYSICAL are absent after audit."},
        "landform": {"status": "MISSING", "disposition": "REQUIRES_TARGETED_RECOVERY"},
        "topography": {"status": domains["TOPOGRAPHY"]["authority_status"], "disposition": domains["TOPOGRAPHY"]["reuse_disposition"]},
    }
    sources = [
        {
            "id": "GUM_2018",
            "citation": "Börker et al. 2018",
            "paper_doi": "10.1002/2017GC007273",
            "dataset_doi": "10.1594/PANGAEA.884822",
            "urls": ["https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2017GC007273", "https://doi.pangaea.de/10.1594/PANGAEA.884822"],
            "semantic_role": "transported/unconsolidated sediment genetic and depositional preemption",
            "direct_or_modeled": "compiled mapped polygons and gridded derivative",
            "genetic_authority": "PARTIAL",
            "process_authority": "INSUFFICIENT",
            "transport_deposition_authority": "SUFFICIENT_FOR_MAPPED_PRESENCE_ONLY",
            "spatial_resolution": "polygon database; 0.5 degree gridded product",
            "coverage": "mapped ice-free land; incomplete white areas",
            "license": "CC-BY-3.0",
            "temporal_semantics": "present surface inventory with mapped sediment ages where available",
            "ceiling": "Mapped sediment presence/type can preempt residual eligibility; absence or white area is unknown, not bedrock or in-situ evidence.",
        },
        {
            "id": "PELLETIER_2016",
            "citation": "Pelletier et al. 2016",
            "paper_doi": "10.1002/2015MS000526",
            "dataset_doi": "10.3334/ORNLDAAC/1304",
            "urls": ["https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2015MS000526", "https://daac.ornl.gov/SOILS/guides/global_regolith.html"],
            "semantic_role": "modeled thickness and landform/process partition",
            "direct_or_modeled": "modeled global gridded averages using topography, climate, geology and observations",
            "genetic_authority": "INSUFFICIENT_ALONE",
            "structural_authority": "PARTIAL",
            "process_authority": "PARTIAL",
            "landform_authority": "PARTIAL",
            "spatial_resolution": "30 arcsec, approximately 1 km",
            "coverage": "global terrestrial land surface partitioned into upland hillslope, upland valley bottom and lowland",
            "temporal_semantics": "long-term geological-process framing; not a 200 ka to 0 ka state reconstruction",
            "ceiling": "Positive intact-regolith thickness plus upland-hillslope membership does not establish residual/in-situ genetic origin; useful as structural/process context only.",
        },
        {
            "id": "MARTIN_LAMB_2025",
            "citation": "Martin and Lamb 2025",
            "paper_doi": "10.1130/G53289.1",
            "dataset_doi": "10.6084/m9.figshare.28432280",
            "urls": ["https://doi.org/10.1130/G53289.1", "https://doi.org/10.6084/m9.figshare.28432280", "https://mapsof.rocks/source-to-sink/"],
            "semantic_role": "global long-timescale sediment source/bypass/sink process-domain conditioner",
            "class_vocabulary": ["source", "bypass", "sink", "unclassified_residual"],
            "direct_or_modeled": "harmonized interpreted and remotely sensed global products",
            "genetic_authority": "INSUFFICIENT_ALONE",
            "process_authority": "PARTIAL",
            "transport_deposition_authority": "PARTIAL",
            "spatial_resolution": "250 m; 12,000 by 12,000 pixel tiles",
            "projection": "Equal Earth projected CRS; exact EPSG/artifact metadata must be bound during PRE5K",
            "coverage": "global map; approximately 0.3% of non-Antarctic land unclassified; Antarctica not mapped in the paper",
            "license": "NOT_ESTABLISHED_FROM_REVIEWED_OFFICIAL_PAGES; verify during acquisition",
            "temporal_semantics": "long-timescale modern geomorphic process domain, not paleo-state persistence",
            "ceiling": "Source/bypass/sink can condition transport/process eligibility; it cannot independently establish weathering in place or residual genetic identity.",
            "dependency_note": "The published method uses Pelletier upland/lowland classifications and other products; not an independent vote against Pelletier.",
        },
        {
            "id": "SHANGGUAN_2017",
            "citation": "Shangguan et al. 2017",
            "paper_doi": "10.1002/2016MS000686",
            "urls": ["https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2016MS000686"],
            "semantic_role": "structural depth-to-bedrock and R-horizon context",
            "direct_or_modeled": "global spatial predictions from profiles, boreholes and pseudo-observations",
            "genetic_authority": "INSUFFICIENT",
            "structural_authority": "PARTIAL",
            "process_authority": "INSUFFICIENT",
            "spatial_resolution": "250 m products",
            "coverage": "global modeled maps with heterogeneous observations",
            "temporal_semantics": "present endpoint",
            "ceiling": "DTB/R-horizon evidence does not distinguish residual from transported or saprolitic material; DTB=0 supports exposed-bedrock structural evidence only under PRE5I contract.",
        },
        {
            "id": "GLIM_2012",
            "citation": "Hartmann and Moosdorf 2012",
            "paper_doi": "10.1029/2012GC004370",
            "urls": ["https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2012GC004370"],
            "semantic_role": "surface lithology conditioner",
            "direct_or_modeled": "compiled global lithological map",
            "genetic_authority": "INSUFFICIENT",
            "structural_authority": "PARTIAL",
            "process_authority": "INSUFFICIENT",
            "spatial_resolution": "global lithology map; provider-specific native grid",
            "coverage": "global mapped surface lithology with heterogeneous source quality",
            "temporal_semantics": "present surface lithology",
            "ceiling": "May modify compatibility/confidence after eligibility is established; cannot create residual identity.",
        },
    ]
    dependency = [
        {"source": "GUM_2018", "parents": ["regional geological maps", "GLiM_2012 fallback in some regions"], "children": ["PRE5J transported preemption"], "independence_class": "compiled mapped evidence"},
        {"source": "PELLETIER_2016", "parents": ["topography", "climate", "geology", "observations"], "children": ["MARTIN_LAMB_2025"], "independence_class": "modeled process/landform evidence"},
        {"source": "MARTIN_LAMB_2025", "parents": ["Pelletier upland/lowland", "GUM", "Nyberg and Howell", "HydroLAKES", "shoreline/remote sensing"], "children": ["future residual eligibility conditioner"], "independence_class": "derived dependent process-domain evidence; not an independent vote"},
        {"source": "SHANGGUAN_2017", "parents": ["soil profiles", "boreholes", "pseudo-observations", "GLiM context"], "children": ["PRE5I structural gate"], "independence_class": "modeled structural evidence"},
        {"source": "GLIM_2012", "parents": ["global geological map sources"], "children": ["GUM fallback", "lithologic compatibility conditioner"], "independence_class": "compiled lithology context"},
        {"source": "ARCANA_WEATHERING", "parents": ["Scientific Authority Register"], "children": ["future process compatibility only"], "independence_class": "proxy-only governed ARCANA authority"},
        {"source": "ARCANA_EROSION", "parents": [], "children": [], "independence_class": "missing; no vote"},
    ]
    rule = {
        "rule_id": "PRE5J_FUTURE_RESIDUAL_REGOLITH_ELIGIBILITY_V1",
        "status": "DESIGN_ONLY_NOT_EXECUTED",
        "ordered_logic": ["terrestrial_scope", "GUM_transported_preemption", "Martin_Lamb_or_other_process_domain_conditioner", "Pelletier_structural_regolith_context", "GLiM_lithology_compatibility", "contradiction_and_uncertainty", "residual_eligibility_or_abstention"],
        "necessary_conditions": ["transported_material_absent_with_absence_explicitly_distinguished_from_unknown", "process_domain_supports_long_term_material_production_or_weathering_in_place", "structural_regolith_evidence_present", "no_contrary_depositional_evidence"],
        "prohibited_shortcuts": ["positive_thickness_implies_residual", "upland_implies_residual", "source_domain_implies_residual", "positive_DTB_implies_residual", "lithology_implies_residual", "GUM_NODATA_implies_in_situ"],
        "dependency_policy": "Pelletier and Martin/Lamb are dependent and cannot be counted as independent corroboration.",
        "classification_executed": False,
        "residual_assignments": 0,
        "saprolite_assignments": 0,
    }
    adjudication = {
        "stage": STAGE,
        "decision": "AUTHORIZE_P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_GATE",
        "verdict": "PASS_P7Q_PRE5J_RESIDUAL_PROCESS_AUTHORITY_COMPLETION_ADJUDICATED",
        "status": "COMPLETE__RESIDUAL_PROCESS_AUTHORITY_FEASIBLE__CLASSIFICATION_NOT_EXECUTED",
        "next_action": "P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_GATE",
        "authority_preflight": authority_preflight,
        "provider_candidates_researched": [s["id"] for s in sources],
        "martin_lamb_usable": True,
        "martin_lamb_use": "process-domain conditioner only; acquisition and exact CRS/license binding required",
        "pelletier_sufficient_for_genetic_residual": False,
        "pelletier_martin_dependency_prevents_independent_corroboration": True,
        "residual_classifier_feasible_in_principle": True,
        "additional_provider_acquisition_required": True,
        "saprolite_classification": "NOT_AUTHORIZED",
        "residual_assignments": 0,
        "saprolite_assignments": 0,
        "classifier_executed": False,
        "parent_state_assignments": 0,
        "P7Q_reopened": False,
        "scientific_authority_register_mutated": False,
        "pre5i_authority_sha256": pre5i.get("static_candidate_sha256"),
        "research_scope": "geological-present/long-term-modern-process endpoint authority only; no 200 ka to 0 ka reconstruction",
    }
    write_json("R5_17_B7_A3F2_P7Q_PRE5J_PROCESS_AUTHORITY_CONTRACT.json", {"stage": STAGE, "scope": "authority adjudication only", "classification_executed": False, "materialization_executed": False, "parent_state_mutations": 0, "GUM_absence_is_abstention": True, "Pelletier_positive_thickness_is_not_genetic_identity": True, "Martin_Lamb_is_process_conditioner_only": True, "saprolite_authorized": False, "next_gate": adjudication["next_action"]})
    write_json("R5_17_B7_A3F2_P7Q_PRE5J_PROVIDER_SOURCE_AUDIT.json", {"stage": STAGE, "sources": sources, "official_source_research_completed": True})
    write_json("R5_17_B7_A3F2_P7Q_PRE5J_EVIDENCE_DEPENDENCY_MATRIX.json", {"stage": STAGE, "nodes": dependency, "majority_vote_allowed": False})
    write_json("R5_17_B7_A3F2_P7Q_PRE5J_RESIDUAL_SEMANTIC_RULE_REGISTRY.json", rule)
    write_json("R5_17_B7_A3F2_P7Q_PRE5J_SAPROLITE_AUTHORITY_AUDIT.json", {"stage": STAGE, "classification": "NOT_AUTHORIZED", "assigned": 0, "sufficient_process_semantics_found": False, "depth_threshold_created": False, "reason": "Reviewed providers do not establish saprolite/deep-weathering genetic identity at global cell level."})
    write_json("R5_17_B7_A3F2_P7Q_PRE5J_ADJUDICATION.json", adjudication)
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5J_ADJUDICATION.md").write_text("""# R5.17-B7-A3F2-P7Q-PRE5J

Decision: `AUTHORIZE_P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_GATE`

Verdict: `PASS_P7Q_PRE5J_RESIDUAL_PROCESS_AUTHORITY_COMPLETION_ADJUDICATED`

PRE5J is an authority and process-semantics gate only. No parent-state record was reclassified and no classifier was executed. GUM is a transported/unconsolidated-sediment preemption authority, but GUM absence is abstention. Pelletier supplies modeled thickness and landform/process context, not genetic residual identity. Martin/Lamb supplies a 250 m source/bypass/sink process-domain conditioner, but its upland/lowland basis depends on Pelletier and it is not an independent vote. Shangguan supplies structural DTB context; GLiM supplies lithology context. Saprolite remains unauthorized.

The residual classifier is feasible in principle as a conjunctive, dependency-aware rule, but the Martin/Lamb artifact and exact source metadata must be acquired and bound in PRE5K before any classification gate. PRE5J assignments are zero and P7Q remains suspended.
""", encoding="utf-8")
    state = (ROOT / "ARCANA_WORLD_CURRENT_STATE.md").read_text(encoding="utf-8")
    replacements = {
        "LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-PRE5I": "LATEST_COMPLETED_INTERNAL_STEP: R5.17-B7-A3F2-P7Q-PRE5J",
        "LATEST_INTERNAL_VERDICT: PASS_P7Q_PRE5I_STATIC_BEDROCK_EXPOSURE_MATERIALIZATION_ADJUDICATED": "LATEST_INTERNAL_VERDICT: PASS_P7Q_PRE5J_RESIDUAL_PROCESS_AUTHORITY_COMPLETION_ADJUDICATED",
        "NEXT_ACTION: P7Q_PRE5J_RESIDUAL_REGOLITH_PROCESS_AUTHORITY_COMPLETION_GATE": "NEXT_ACTION: P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_GATE",
    }
    for old, new in replacements.items():
        if old not in state:
            raise RuntimeError(f"BLOCKED_P7Q_PRE5J_CURRENT_STATE_EXPECTATION_MISSING: {old}")
        state = state.replace(old, new, 1)
    state = state.replace("ACTIVE_SUBPHASE_STATUS: A3_IN_PROGRESS__P7Q_PRE5I_COMPLETE__BEDROCK_ONLY__RESIDUAL_UNAUTHORIZED", "ACTIVE_SUBPHASE_STATUS: A3_IN_PROGRESS__P7Q_PRE5J_COMPLETE__RESIDUAL_PROCESS_AUTHORITY_ACQUISITION_REQUIRED", 1)
    marker = "P7Q_PRE5I_INITIAL_BLOCKER: BLOCKED_P7Q_PRE5I_WINDOWED_RASTER_READER_UNAVAILABLE__RESOLVED_BY_APPROVED_RASTERIO_RUNTIME\n"
    if marker in state and "P7Q_PRE5J_STATUS:" not in state:
        state = state.replace(marker, marker + "P7Q_PRE5J_STATUS: COMPLETE__RESIDUAL_PROCESS_AUTHORITY_FEASIBLE__CLASSIFICATION_NOT_EXECUTED\nP7Q_PRE5J_DECISION: AUTHORIZE_P7Q_PRE5K_RESIDUAL_PROCESS_PROVIDER_ACQUISITION_AND_BINDING_GATE\n", 1)
    (ROOT / "ARCANA_WORLD_CURRENT_STATE.md").write_text(state, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
