from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = 50568
TARGET_SHA = "3b139c494c2714bba5bbeecce426bb33bbcda6d7acbb5188471c9fa172ef9e28"
STAGE = "R5.17-B7-A3F2-P7Q-PRE5H"

REQUIRED = [
    "ARCANA_WORLD_CURRENT_STATE.md",
    "ARCANA_WORLDSIM_SCIENTIFIC_AUTHORITY_REGISTER.json",
    "R5_17_B7_A3F2_P7Q_PRE4_TEMPORAL_PARENT_STATE_RULE_REGISTRY.json",
    "R5_17_B7_A3F2_P7Q_PRE5C_SR_STATIC_STATE_AUDIT.json",
    "R5_17_B7_A3F2_P7Q_PRE5D_PROVIDER_REQUIREMENT_MATRIX.json",
    "R5_17_B7_A3F2_P7Q_PRE5E_CLASS_FEASIBILITY_MATRIX.json",
    "R5_17_B7_A3F2_P7Q_PRE5F_PROVIDER_DEPENDENCY_RECONCILIATION.json",
    "R5_17_B7_A3F2_P7Q_PRE5G_SOURCE_BINDING_MANIFEST.json",
    "R5_17_B7_A3F2_P7Q_PRE5G_RASTER_METADATA_AUDIT.json",
    "R5_17_B7_A3F2_P7Q_PRE5G_GRID_ALIGNMENT_CONTRACT.json",
    "R5_17_B7_A3F2_P7Q_PRE5G_TARGET_COVERAGE_AUDIT.json",
    "R5_17_B7_A3F2_P7Q_PRE5G_PROVIDER_DEPENDENCY_AND_PRECEDENCE.json",
    "R5_17_B7_A3F2_P7Q_PRE5G_ADJUDICATION.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> None:
    missing = [name for name in REQUIRED if not (ROOT / name).exists()]
    if missing:
        raise FileNotFoundError(missing)
    sources = {name: {"sha256": sha256(ROOT / name), "bytes": (ROOT / name).stat().st_size}
               for name in REQUIRED if name.endswith(".json")}
    current_state = (ROOT / "ARCANA_WORLD_CURRENT_STATE.md").read_text(encoding="utf-8")
    pre5g = load_json("R5_17_B7_A3F2_P7Q_PRE5G_ADJUDICATION.json")
    target = pre5g["target"]
    if target["direct_target_cells"] != TARGET or target["ordered_cell_id_sha256"] != TARGET_SHA:
        raise ValueError("PRE5G target cohort drift")

    source_audit = {
        "stage": STAGE,
        "research_scope": "targeted publisher/provider documentation; no new provider acquisition",
        "sources": [
            {"id": "SHANGGUAN_2017", "doi": "10.1002/2016MS000686",
             "url": "https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2016MS000686",
             "findings": ["BDTICM is absolute DTB in cm", "BDRICM is censored DTB/R-horizon evidence within 0-200 cm", "BDRLOG is probability of R-horizon occurrence within 0-200 cm", "rock outcrop is defined as DTB=0", "positive-DTB exposure cutoff is not published or calibrated here"]},
            {"id": "PELLETIER_2016", "doi": "10.1002/2015MS000526",
             "url": "https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2015MS000526",
             "findings": ["soil, intact-regolith and sedimentary-deposit thicknesses are modeled structural layers above bedrock", "products are estimated using topography, climate and geology inputs", "the products do not provide genetic parent-material labels"]},
            {"id": "GLIM_HARTMANN_MOOSDORF_2012", "doi": "10.1029/2012GC004370",
             "url": "https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2012GC004370",
             "findings": ["GLiM represents surface lithological classes and subclasses", "mapped units are heterogeneous and uncertain", "GLiM cannot independently determine exposure state or deep weathering"]},
        ],
        "interpretation": "publisher semantics are used; no majority vote and no threshold is inferred from provider availability",
    }

    threshold_registry = {
        "stage": STAGE,
        "thresholds": [
            {"threshold_id": "BEDROCK_EXPOSED_DTB_ZERO", "target_branch": "BEDROCK_EXPOSED", "source_variable": "BDTICM", "operator": "==", "value": 0, "unit": "cm", "scientific_role": "exact surface-DTB semantic boundary", "source_reference": "10.1002/2016MS000686", "source_support_type": "PUBLISHED_SEMANTIC_DEFINITION", "calibration_status": "NOT_REQUIRED_FOR_BOUNDARY", "authorization_status": "AUTHORIZED_EXACT_SEMANTIC_BOUNDARY", "notes": "Modeled surface-DTB evidence only; still requires eligibility and no transported-material preemption."},
            {"threshold_id": "BEDROCK_EXPOSED_POSITIVE_DTB", "target_branch": "BEDROCK_EXPOSED", "source_variable": "BDTICM", "operator": "<=", "value": None, "unit": "cm", "scientific_role": "wider exposure cutoff", "source_reference": "10.1002/2016MS000686", "source_support_type": "NO_PUBLISHED_CALIBRATION", "calibration_status": "MISSING", "authorization_status": "BLOCKED_MISSING_CALIBRATION", "notes": "10/25/50/200 cm cutoffs are explicitly not authorized."},
            {"threshold_id": "RESIDUAL_REGOLITH_POSITIVE_THICKNESS", "target_branch": "RESIDUAL_REGOLITH", "source_variable": "INTACT_REGOLITH_THICKNESS", "operator": ">", "value": 0, "unit": "m", "scientific_role": "candidate structural presence rule", "source_reference": "10.1002/2015MS000526", "source_support_type": "STRUCTURAL_PROVIDER_ONLY", "calibration_status": "NOT_A_CLASS_LABEL", "authorization_status": "REJECTED_ARBITRARY", "notes": "Positive modeled thickness does not establish residual/in-situ genetic identity."},
            {"threshold_id": "SAPROLITE_DEEP_WEATHERING", "target_branch": "SAPROLITE_OR_DEEP_WEATHERING", "source_variable": "INTACT_REGOLITH_THICKNESS", "operator": ">", "value": None, "unit": "m", "scientific_role": "candidate deep-weathering rule", "source_reference": "10.1002/2015MS000526", "source_support_type": "INSUFFICIENT_WEATHERING_SPECIFICITY", "calibration_status": "MISSING", "authorization_status": "NOT_APPLICABLE", "notes": "No thickness value is authorized to identify saprolite."},
        ],
        "active_numeric_threshold_count": 0,
        "authorized_exact_boundary_count": 1,
        "policy": "prefer abstention over unsupported cutoff",
    }

    contract = {
        "stage": STAGE,
        "classifier_contract_created": True,
        "classifier_executed": False,
        "eligible_input_cohort": {"direct_target_cells": TARGET, "target_identity_sha256": TARGET_SHA, "unknown_material_expansion": False},
        "precedence_rules": ["GUM-supported transported/material states preempt classifier", "classifier runs only after land eligibility and preemption checks", "GLiM cannot override material-state precedence"],
        "required_evidence_fields": ["land_state", "existing_material_state", "BDTICM_cm", "provider_availability", "source_quality", "nodata_mask"],
        "optional_conditioning_fields": ["GLiM_surface_lithology_conditioner", "BDRICM_censored_R_horizon", "BDRLOG_R_horizon_probability", "Pelletier_structural_thicknesses"],
        "missing_provider_behavior": "ABSTAIN_OR_REDUCED_EVIDENCE_ONLY__MISSING_IS_NOT_NEGATIVE",
        "bedrock_exposed_rule": "eligible land AND no transported-material preemption AND BDTICM_cm == 0 AND valid source evidence; otherwise UNKNOWN_MATERIAL",
        "bedrock_exposed_support_class": "CONDITIONAL_STRUCTURAL_SUPPORT",
        "residual_regolith_rule": "NOT_AUTHORIZED_UNTIL_INDEPENDENT_WEATHERING_AND_EROSION_AUTHORITIES_ARE_SUFFICIENT; otherwise UNKNOWN_MATERIAL",
        "saprolite_disposition": "NOT_AUTHORIZED",
        "provider_dependency_restrictions": ["no majority voting", "Shangguan and Pelletier are modeled/derived evidence", "GLiM is conditioner only", "provider families are not independent votes"],
        "output_vocabulary": ["BEDROCK_EXPOSED", "RESIDUAL_REGOLITH", "SAPROLITE_OR_DEEP_WEATHERING", "UNKNOWN_MATERIAL"],
        "provenance_requirements": ["provider id and version", "source variable and unit", "valid/nodata mask", "precedence decision", "abstention reason", "deterministic contract version"],
        "determinism_requirements": ["fixed cohort and identity hash", "fixed precedence order", "no interpolation or resampling in classifier", "same inputs produce byte-equivalent decision records"],
    }

    dependencies = {
        "stage": STAGE,
        "evidence_roles": {
            "Shangguan_BDTICM": "conditional_structural_support_for_exact_DTB_zero",
            "Shangguan_BDRICM": "censored_R_horizon_context_only",
            "Shangguan_BDRLOG": "R_horizon_probability_context_only_not_exposure_probability",
            "Pelletier": "structural_thickness_evidence_only",
            "GLiM": "surface_lithology_conditioner_only",
            "GUM": "eligibility_and_precedence_authority",
            "ARCANA_weathering": "INSUFFICIENT_FOR_POSITIVE_RESIDUAL_RULE",
            "ARCANA_erosion": "PARTIAL__NOT_SUFFICIENT_FOR_POSITIVE_RESIDUAL_RULE",
        },
        "weathering_authority": "INSUFFICIENT",
        "erosion_authority": "PARTIAL",
        "independent_evidence_vote_count": "NOT_USED",
        "transported_material_precedence": "REQUIRED__GUM_SUPPORTED_STATES_PREEMPT",
        "missing_provider_behavior": "ABSTAIN_OR_REDUCED_EVIDENCE_ONLY",
    }

    adjudication = {
        "stage": STAGE,
        "decision": "AUTHORIZE_P7Q_PRE5I_STATIC_RESIDUAL_BEDROCK_CLASSIFIER_MATERIALIZATION_GATE",
        "verdict": "PASS_P7Q_PRE5H_RESIDUAL_BEDROCK_CLASSIFIER_CONTRACT_AND_THRESHOLDS_ADJUDICATED",
        "status": "COMPLETE__CLASSIFIER_CONTRACT_ADJUDICATED__NO_CLASSIFICATION",
        "next_action": "P7Q_PRE5I_STATIC_RESIDUAL_BEDROCK_CLASSIFIER_MATERIALIZATION_GATE",
        "direct_target_cells": TARGET,
        "target_identity_sha256": TARGET_SHA,
        "classified_cells": 0,
        "bedrock_exposed_assigned": 0,
        "residual_regolith_assigned": 0,
        "saprolite_assigned": 0,
        "classifier_executed": False,
        "thresholds_active": False,
        "canonical_parent_created": False,
        "physical_soil_created": False,
        "temporal_reconstruction": False,
        "new_simulation": False,
        "P7Q_reopened": False,
        "provider_values_resampled": False,
        "provider_values_aggregated": False,
        "material_crosswalk_performed": False,
        "scientific_authority_register_mutated": False,
        "authority_register_preflight": {"present": True, "sha256": sha256(ROOT / "ARCANA_WORLDSIM_SCIENTIFIC_AUTHORITY_REGISTER.json"), "mutation": False},
        "authority_chain": REQUIRED,
        "sources_consulted": source_audit["sources"],
        "weathering_authority": "INSUFFICIENT",
        "erosion_authority": "PARTIAL",
        "saprolite_classification": "NOT_AUTHORIZED",
        "abstention_required": True,
        "input_evidence": sources,
        "p7q_state": "SUSPENDED_PENDING_EXPLICIT_P7Q_REAUTHORIZATION",
    }

    outputs = {
        "R5_17_B7_A3F2_P7Q_PRE5H_CLASSIFIER_CONTRACT.json": contract,
        "R5_17_B7_A3F2_P7Q_PRE5H_THRESHOLD_REGISTRY.json": threshold_registry,
        "R5_17_B7_A3F2_P7Q_PRE5H_EVIDENCE_DEPENDENCY_MATRIX.json": dependencies,
        "R5_17_B7_A3F2_P7Q_PRE5H_SCIENTIFIC_SOURCE_AUDIT.json": source_audit,
        "R5_17_B7_A3F2_P7Q_PRE5H_ADJUDICATION.json": adjudication,
    }
    for name, payload in outputs.items():
        (ROOT / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md = f"""# {STAGE}\n\n## Decision\n\n`{adjudication['decision']}`\n\n## Verdict\n\n`{adjudication['verdict']}`\n\nPRE5H defines and adjudicates a deterministic future classifier contract only. It does not execute classification, reopen P7Q, create a raster, or create a 50,568-cell payload.\n\n### Evidence disposition\n\n- BEDROCK_EXPOSED: exact semantic boundary `BDTICM == 0 cm` only; no positive-DTB cutoff authorized.\n- RESIDUAL_REGOLITH: no positive rule authorized from Pelletier thickness alone; weathering authority is `INSUFFICIENT` and erosion authority is `PARTIAL`.\n- SAPROLITE_OR_DEEP_WEATHERING: `NOT_AUTHORIZED`.\n- GLiM: surface lithology conditioner only.\n- Missing providers: abstain or reduced evidence only; absence is not negative evidence.\n- Transported GUM-supported material states retain precedence.\n\n### No classification\n\n`classified_cells = 0`; `bedrock_exposed_assigned = 0`; `residual_regolith_assigned = 0`; `saprolite_assigned = 0`; `thresholds_active = false`.\n\nNext action: `{adjudication['next_action']}`. PRE5I was not executed.\n"""
    (ROOT / "R5_17_B7_A3F2_P7Q_PRE5H_ADJUDICATION.md").write_text(md, encoding="utf-8")
    print(json.dumps(adjudication, indent=2))


if __name__ == "__main__":
    main()
