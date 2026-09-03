from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

STAGE = "v0.6D1-R3.22"
PARENT_STAGE = "v0.6D1-R3.21"
PARENT_PASS = "PASS_R321_H0_PRESENT_LINEAGE_REGISTRY_HISTORICAL_CLOSURE_AND_FUNCTIONAL_PHENOTYPE_FORK_READINESS_SEALED"
PASS = "PASS_R322_GENERIC_FUNCTIONAL_PHENOTYPE_SPECIFICATION_TRADEOFF_GOVERNANCE_AND_REPLAY_INTERFACE_SEALED"
R319_JSON_SHA = "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71"
R319_NPZ_SHA = "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406"
EXPECTED_PARENT_CHECKS = 43
EXPECTED_CANDIDATE_CHECKS = 34
EXPECTED_SPECIES = 134
EXPECTED_COMPONENTS = 295

EXPECTED_FILES = {
    "R3_22_FUNCTIONAL_PHENOTYPE_SPECIFICATION.json",
    "R3_22_PRIMITIVE_TRAIT_CATALOG.json",
    "R3_22_DERIVED_CAPABILITY_GRAPH.json",
    "R3_22_CONSTRAINT_AND_TRADEOFF_GOVERNANCE.json",
    "R3_22_REPLAY_STATE_INTERFACE.json",
    "R3_22_EMPIRICAL_CALIBRATION_REQUIREMENTS.json",
    "R3_22_AUDIT_SUMMARY.json",
    "R3_22_AUDIT.md",
    "R3_22_OUTPUT_MANIFEST.json",
}

EXPECTED_DOMAINS = [
    "manipulative_capability",
    "locomotor_flexibility",
    "cognitive_capacity",
    "learning_plasticity",
    "sociality",
    "dietary_flexibility",
    "life_history",
    "ecological_generalism",
    "tool_use_potential",
    "environmental_problem_solving_capability",
]

EXPECTED_TRAITS = [
    ("M1_effector_independence", "manipulative_capability"),
    ("M2_force_precision_span", "manipulative_capability"),
    ("M3_workspace_control", "manipulative_capability"),
    ("M4_sensorimotor_feedback", "manipulative_capability"),
    ("L1_locomotor_mode_breadth", "locomotor_flexibility"),
    ("L2_substrate_breadth", "locomotor_flexibility"),
    ("L3_transition_control", "locomotor_flexibility"),
    ("L4_effector_locomotor_decoupling", "locomotor_flexibility"),
    ("C1_working_memory", "cognitive_capacity"),
    ("C2_inhibitory_control", "cognitive_capacity"),
    ("C3_relational_integration", "cognitive_capacity"),
    ("C4_causal_model_depth", "cognitive_capacity"),
    ("P1_acquisition_efficiency", "learning_plasticity"),
    ("P2_retention_stability", "learning_plasticity"),
    ("P3_cross_context_transfer", "learning_plasticity"),
    ("P4_developmental_plasticity", "learning_plasticity"),
    ("S1_social_tolerance", "sociality"),
    ("S2_coordination_capacity", "sociality"),
    ("S3_social_learning_fidelity", "sociality"),
    ("S4_communication_bandwidth", "sociality"),
    ("D1_resource_breadth", "dietary_flexibility"),
    ("D2_digestive_processing_breadth", "dietary_flexibility"),
    ("D3_resource_switching", "dietary_flexibility"),
    ("H1_maturation_duration", "life_history"),
    ("H2_reproductive_output_rate", "life_history"),
    ("H3_parental_investment", "life_history"),
    ("H4_adult_survival_horizon", "life_history"),
    ("G1_habitat_breadth", "ecological_generalism"),
    ("G2_climatic_tolerance_breadth", "ecological_generalism"),
    ("G3_disturbance_resilience", "ecological_generalism"),
    ("G4_colonization_breadth", "ecological_generalism"),
]
EXPECTED_DERIVED = ["T_tool_use_potential", "Q_environmental_problem_solving"]
EXPECTED_CONSTRAINTS = [
    "K_NEURAL_ENERGETIC_BUDGET",
    "K_OFFSPRING_NUMBER_INVESTMENT",
    "K_SHARED_EFFECTOR_FUNCTION",
    "K_DIET_BREADTH_SPECIALIST_EFFICIENCY",
    "K_ECOLOGICAL_BREADTH_SPECIALIZATION",
    "K_SOCIALITY_DENSITY_COST",
    "K_DEVELOPMENT_LEARNING_WINDOW",
]
EXPECTED_ARRAYS = {
    "functional_applicability_code": ["n_component", "n_functional_trait"],
    "functional_mean_z": ["n_component", "n_functional_trait"],
    "functional_va": ["n_component", "n_functional_trait"],
    "functional_gcov": ["n_component", "n_functional_trait", "n_functional_trait"],
    "functional_plasticity_beta": ["n_component", "n_functional_trait", "n_environment_driver"],
}
EXPECTED_APPLICABILITY = ["ACTIVE", "STRUCTURAL_ZERO", "NOT_APPLICABLE", "UNKNOWN"]
EXPECTED_CALIBRATION_REQUIREMENTS = [
    "USE_COMPARATIVE_MULTI_TAXON_DATA_WHERE_AVAILABLE",
    "CORRECT_PHYLOGENETIC_NON_INDEPENDENCE",
    "CORRECT_BODY_SIZE_AND_METABOLIC_ALLOMETRY_WHERE_RELEVANT",
    "REPRESENT_MEASUREMENT_UNCERTAINTY_AND_PROXY_UNCERTAINTY",
    "KEEP_RAW_OBSERVABLES_SEPARATE_FROM_LATENT_FUNCTIONAL_COORDINATES",
    "VALIDATE_PROXY_CONCORDANCE_WITH_HELD_OUT_TAXA_OR_DATASETS",
    "ESTIMATE_HERITABILITY_OR_ADDITIVE_VARIANCE_FROM_EMPIRICAL_EVIDENCE;_DO_NOT_AUTHOR-ASSIGN",
    "ESTIMATE_GENETIC_COVARIANCE_OR_USE_A_DOCUMENTED_CONSERVATIVE_ZERO-CROSS-COVARIANCE_BASELINE_ONLY_AFTER_AUDIT",
    "CALIBRATE_METABOLIC_ECOLOGICAL_COSTS_IN_PHYSICAL_OR_DEMOGRAPHIC_CURRENCY",
    "NO_SINGLE_SPECIES_OR_HUMAN_ANCHOR_DEFINES_THE_SCALE",
    "DEEP_NOETIC_EXPOSURE_MUST_NOT_ENTER_THE_CALIBRATION_OR_FUNCTIONAL_TRAIT_DYNAMICS",
    "NO_HUMAN_READINESS_SAPIENCE_CIVILIZATION_OR_TOOL_USE_TARGET_IS_USED_TO_FIT_PRIMARY_TRAITS",
]
EXPECTED_PER_TRAIT_FIELDS = [
    "empirical_source_set",
    "observable_to_latent_mapping",
    "uncertainty_model",
    "heritability_or_va_model",
    "cost_model_if_non_negligible",
    "validation_result",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_parent_authority(seal_dir: Path) -> tuple[dict[str, Any], list[tuple[str, bool, Any]]]:
    audit_path = seal_dir / "R3_21_FINAL_SEAL_AUDIT.json"
    manifest_path = seal_dir / "R3_21_FINAL_SEAL_MANIFEST.json"
    local: list[tuple[str, bool, Any]] = []
    local.append(("parent_seal_audit_present", audit_path.is_file(), str(audit_path)))
    local.append(("parent_seal_manifest_present", manifest_path.is_file(), str(manifest_path)))
    if not audit_path.is_file() or not manifest_path.is_file():
        return {}, local

    audit = load_json(audit_path)
    local.append(("parent_stage_exact", audit.get("stage") == PARENT_STAGE, audit.get("stage")))
    local.append(("parent_verdict_exact", audit.get("status") == PARENT_PASS and audit.get("verdict") == "SEALED", audit.get("status")))
    local.append(("parent_43_of_43", audit.get("checks_passed") == EXPECTED_PARENT_CHECKS and audit.get("checks_total") == EXPECTED_PARENT_CHECKS and audit.get("checks_failed") == 0, [audit.get("checks_passed"), audit.get("checks_total"), audit.get("checks_failed")]))
    source = audit.get("source_checkpoint", {})
    local.append(("parent_r319_provenance_exact", source.get("json_sha256") == R319_JSON_SHA and source.get("npz_sha256") == R319_NPZ_SHA, source))

    manifest = load_json(manifest_path)
    rows = manifest.get("files", {})
    closure: dict[str, bool] = {}
    ok = bool(rows)
    for name, meta in rows.items():
        p = seal_dir / name
        good = (
            isinstance(meta, dict)
            and p.is_file()
            and sha256_file(p) == meta.get("sha256")
            and p.stat().st_size == meta.get("bytes")
        )
        closure[name] = good
        ok &= good
    local.append(("parent_seal_manifest_hash_size_closure", ok, closure))

    parent = {
        "stage": PARENT_STAGE,
        "status": PARENT_PASS,
        "verdict": "SEALED",
        "checks_passed": EXPECTED_PARENT_CHECKS,
        "source_checkpoint": {"json_sha256": R319_JSON_SHA, "npz_sha256": R319_NPZ_SHA},
        "seal_audit_sha256": sha256_file(audit_path),
        "seal_manifest_sha256": sha256_file(manifest_path),
    }
    return parent, local


def audit(root: Path, out: Path, parent_seal_dir: Path) -> tuple[dict[str, Any], bool]:
    checks: list[dict[str, Any]] = []
    def check(name: str, cond: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    parent, parent_checks = canonical_parent_authority(parent_seal_dir)
    for name, cond, detail in parent_checks:
        check(name, cond, detail)

    check("output_dir_exists", out.is_dir(), str(out))
    actual_files = {p.name for p in out.iterdir() if p.is_file()} if out.is_dir() else set()
    check("output_file_set_exact", actual_files == EXPECTED_FILES, {"missing": sorted(EXPECTED_FILES - actual_files), "unexpected": sorted(actual_files - EXPECTED_FILES)})
    if not out.is_dir() or not EXPECTED_FILES <= actual_files:
        passed = sum(1 for c in checks if c["pass"])
        report = {
            "stage": STAGE, "audit": "FINAL_SEAL_INDEPENDENT_SPECIFICATION_CLOSURE",
            "status": "FAIL_R322_FINAL_SEAL_AUDIT", "verdict": "FAIL_CLOSED",
            "checks_passed": passed, "checks_total": len(checks), "checks_failed": len(checks) - passed,
            "checks": checks,
        }
        return report, False

    manifest = load_json(out / "R3_22_OUTPUT_MANIFEST.json")
    rows = manifest.get("files", {})
    expected_manifest_names = EXPECTED_FILES - {"R3_22_OUTPUT_MANIFEST.json"}
    closure: dict[str, bool] = {}
    closure_ok = set(rows) == expected_manifest_names
    for name in sorted(expected_manifest_names):
        meta = rows.get(name, {})
        p = out / name
        good = p.is_file() and sha256_file(p) == meta.get("sha256") and p.stat().st_size == meta.get("bytes")
        closure[name] = good
        closure_ok &= good
    check("output_manifest_hash_size_closure", closure_ok, closure)
    check("output_manifest_stage_status", manifest.get("stage") == STAGE and manifest.get("status") == "CANDIDATE_OUTPUT_MANIFEST", [manifest.get("stage"), manifest.get("status")])
    check("output_manifest_parent_authority_exact", bool(parent) and manifest.get("parent_authority") == parent)

    spec = load_json(out / "R3_22_FUNCTIONAL_PHENOTYPE_SPECIFICATION.json")
    traits_doc = load_json(out / "R3_22_PRIMITIVE_TRAIT_CATALOG.json")
    derived_doc = load_json(out / "R3_22_DERIVED_CAPABILITY_GRAPH.json")
    constraints = load_json(out / "R3_22_CONSTRAINT_AND_TRADEOFF_GOVERNANCE.json")
    replay = load_json(out / "R3_22_REPLAY_STATE_INTERFACE.json")
    calibration = load_json(out / "R3_22_EMPIRICAL_CALIBRATION_REQUIREMENTS.json")
    candidate_audit = load_json(out / "R3_22_AUDIT_SUMMARY.json")

    docs = [spec, traits_doc, derived_doc, constraints, replay, calibration, candidate_audit]
    check("all_json_stage_exact", all(d.get("stage") == STAGE for d in docs), [d.get("stage") for d in docs])
    check("spec_parent_authority_exact", bool(parent) and spec.get("parent_authority") == parent)
    check("spec_parent_counts_exact", spec.get("present_species_parent") == EXPECTED_SPECIES and spec.get("present_components_parent") == EXPECTED_COMPONENTS)
    check("spec_scope_generic_no_human", spec.get("scope") == "GENERIC_ALL_LINEAGES_NO_HUMAN_TARGET" and spec.get("human_target") is False)
    check("spec_deep_off_no_biology", spec.get("deep_biological_coupling") is False and spec.get("new_biology_executed") is False)
    check("spec_values_unmaterialized", spec.get("values_materialized") is False and spec.get("status") == "CANDIDATE_SPECIFICATION_ONLY_NO_PHENOTYPE_VALUES")
    check("state_granularity_component", spec.get("state_granularity") == "COMPONENT_PRIMARY_SPECIES_SUMMARY_DERIVED")

    domains = spec.get("domains", [])
    domain_names = [d.get("domain") for d in domains]
    check("ten_domains_exact_order", domain_names == EXPECTED_DOMAINS, domain_names)
    check("domain_counts_exact", spec.get("domain_count") == 10 and spec.get("primitive_trait_count") == 31 and spec.get("derived_capability_count") == 2)
    primary_domains = domains[:8]
    derived_domains = domains[8:]
    check("domain_kinds_exact", all(d.get("kind") == "PRIMARY_VECTOR" for d in primary_domains) and all(d.get("kind") == "DERIVED_CONTEXTUAL" for d in derived_domains))
    check("no_domain_scalar_scores", all(d.get("domain_scalar_score") is None for d in domains))
    check("no_global_human_or_fitness_ranking", all(d.get("ranking_status") == "NO_GLOBAL_FITNESS_OR_HUMAN_SIMILARITY_RANKING" for d in domains))

    traits = traits_doc.get("traits", [])
    trait_pairs = [(t.get("trait_id"), t.get("domain")) for t in traits]
    trait_ids = [x[0] for x in trait_pairs]
    check("trait_catalog_status_and_count", traits_doc.get("status") == "SCHEMA_AND_SEMANTICS_ONLY" and traits_doc.get("trait_count") == 31 and len(traits) == 31)
    check("trait_order_and_domain_assignment_exact", trait_pairs == EXPECTED_TRAITS, trait_pairs)
    check("trait_ids_unique", len(set(trait_ids)) == 31)
    check("trait_state_level_component", all(t.get("state_level") == "COMPONENT" and t.get("species_summary") == "POPULATION_WEIGHTED_DERIVED_ONLY" for t in traits))
    check("trait_role_exact", all(t.get("role") == "PRIMARY_EVOLVABLE_FUNCTIONAL_TRAIT" for t in traits))
    check("trait_context_dependent_fitness", all(t.get("latent_coordinate", {}).get("fitness_direction") == "CONTEXT_DEPENDENT" for t in traits))
    check("trait_scale_not_human_anchored", all(t.get("latent_coordinate", {}).get("calibration_anchor") == "MULTI_TAXON_EMPIRICAL_REFERENCE_NOT_HUMAN_ANCHOR" for t in traits))
    check("trait_empirical_observables_nonempty", all(isinstance(t.get("empirical_observables"), list) and len(t.get("empirical_observables")) >= 1 for t in traits))
    null_fields = ("applicability_state", "initial_value", "ancestral_value", "heritability", "additive_variance", "genetic_covariance", "plasticity", "selection_optimum", "metabolic_ecological_cost")
    check("all_primary_quantitative_values_null", all(all(t.get(k) is None for k in null_fields) for t in traits))
    check("all_traits_require_calibration", all(t.get("calibration_status") == "UNMATERIALIZED_EMPIRICAL_CALIBRATION_REQUIRED" for t in traits))
    forbidden_tokens = ("human", "sapience", "civilization", "readiness", "chosen")
    check("trait_ids_non_anthropocentric", not any(tok in " ".join(trait_ids).lower() for tok in forbidden_tokens))

    # Domain membership must be an exact partition of the 31 primary traits.
    domain_trait_concat: list[str] = []
    for d in primary_domains:
        domain_trait_concat.extend(d.get("primitive_trait_ids", []))
    check("primary_domain_trait_partition_exact", domain_trait_concat == trait_ids and len(set(domain_trait_concat)) == 31)
    check("derived_domains_have_no_primary_traits", all(d.get("primitive_trait_ids") == [] for d in derived_domains))

    derived = derived_doc.get("capabilities", [])
    derived_ids = [d.get("capability_id") for d in derived]
    check("derived_catalog_status_count_exact", derived_doc.get("status") == "DEPENDENCY_GRAPH_ONLY_NO_VALUES" and derived_doc.get("capability_count") == 2 and len(derived) == 2)
    check("derived_ids_exact", derived_ids == EXPECTED_DERIVED, derived_ids)
    check("derived_not_direct_state_or_selection", all(d.get("direct_genetic_state") is False and d.get("direct_selection_state") is False for d in derived))
    check("derived_values_and_aggregation_null", all(d.get("value") is None and d.get("aggregation_function") is None and d.get("aggregation_status") == "UNDEFINED_UNTIL_EMPIRICAL_CALIBRATION" for d in derived))
    dep_ok = True
    dep_detail: dict[str, list[str]] = {}
    valid_trait_ids = set(trait_ids)
    for d in derived:
        deps = d.get("required_dependencies", [])
        dep_detail[str(d.get("capability_id"))] = deps
        dep_ok &= bool(deps) and len(deps) == len(set(deps))
        dep_ok &= all((x in valid_trait_ids) or str(x).startswith("ENV_") for x in deps)
        dep_ok &= any(str(x).startswith("ENV_") for x in deps)
    check("derived_dependencies_valid_and_contextual", dep_ok, dep_detail)
    check("derived_domain_membership_exact", derived_domains[0].get("derived_capability_ids") == [EXPECTED_DERIVED[0]] and derived_domains[1].get("derived_capability_ids") == [EXPECTED_DERIVED[1]])

    edges = constraints.get("constraint_edges", [])
    constraint_ids = [e.get("constraint_id") for e in edges]
    check("constraint_governance_status", constraints.get("status") == "STRUCTURE_DEFINED_NUMERICS_UNMATERIALIZED")
    check("seven_constraint_edges_exact", constraint_ids == EXPECTED_CONSTRAINTS, constraint_ids)
    check("constraint_numeric_strengths_null", all(e.get("numeric_strength") is None for e in edges))
    check("constraint_calibration_required", all(e.get("status") == "EMPIRICAL_CALIBRATION_REQUIRED" for e in edges))
    check("constraint_trait_refs_valid", all(all(x in valid_trait_ids for x in e.get("traits", [])) for e in edges))
    check("direct_cross_trait_numeric_correlations_null", constraints.get("direct_cross_trait_numeric_correlations") is None)

    check("replay_state_level_and_counts", replay.get("state_level") == "COMPONENT" and replay.get("component_count_parent") == 295 and replay.get("primitive_trait_count") == 31)
    check("replay_trait_order_exact", replay.get("primitive_trait_order") == trait_ids)
    applicability = replay.get("applicability_model", {})
    check("applicability_states_exact", applicability.get("states") == EXPECTED_APPLICABILITY)
    check("applicability_not_materialized", applicability.get("materialized_in_r3_22") is False)
    check("not_applicable_cannot_drift_activate", applicability.get("continuous_drift_can_activate_not_applicable_trait") is False)
    check("activation_requires_governed_innovation", applicability.get("activation_requires") == "SEPARATELY_GOVERNED_MORPHOLOGICAL_OR_FUNCTIONAL_INNOVATION_EVENT")

    arrays = replay.get("future_state_arrays", {})
    check("future_array_names_exact", set(arrays) == set(EXPECTED_ARRAYS), sorted(arrays))
    check("future_array_shapes_exact", all(arrays.get(k, {}).get("shape") == shape for k, shape in EXPECTED_ARRAYS.items()), {k: arrays.get(k, {}).get("shape") for k in EXPECTED_ARRAYS})
    check("future_arrays_unmaterialized", all(arrays.get(k, {}).get("materialized_in_r3_22") is False for k in EXPECTED_ARRAYS))
    gcov_constraints = arrays.get("functional_gcov", {}).get("constraints", [])
    check("future_gcov_symmetric_psd", "SYMMETRIC_ACTIVE_SUBMATRIX" in gcov_constraints and "POSITIVE_SEMIDEFINITE_ACTIVE_SUBMATRIX" in gcov_constraints)
    check("future_va_nonnegative", "FINITE_AND_NONNEGATIVE_WHERE_ACTIVE" in arrays.get("functional_va", {}).get("constraints", []))
    check("expression_parameters_null", replay.get("expression_model", {}).get("numeric_parameters") is None and replay.get("expression_model", {}).get("status") == "FORM_DEFINED_PARAMETERS_UNCALIBRATED")
    check("evolution_parameters_null", replay.get("evolution_model_family", {}).get("numeric_parameters") is None and replay.get("evolution_model_family", {}).get("status") == "FORM_DEFINED_PARAMETERS_UNCALIBRATED")
    check("species_aggregation_no_single_scalar", replay.get("species_aggregation", {}).get("single_species_scalar_forbidden") is True)
    check("derived_capabilities_not_direct_genetic", replay.get("derived_capabilities") == EXPECTED_DERIVED and replay.get("derived_capabilities_are_direct_genetic_state") is False)
    check("r319_reduced_state_preserved_separately", replay.get("existing_r319_reduced_ecological_state_repurposed") is False)
    check("cross_covariance_not_invented", replay.get("cross_covariance_with_existing_three_ecological_traits") is None and replay.get("cross_covariance_status") == "FORBIDDEN_TO_INVENT_REQUIRES_LATER_EMPIRICAL_CALIBRATION")
    check("replay_deep_off_no_human", replay.get("deep_biological_coupling") == "OFF" and replay.get("human_target") is False)

    check("calibration_status_blocks_materialization", calibration.get("status") == "REQUIRED_BEFORE_ANY_FUNCTIONAL_VALUES_OR_REPLAY")
    check("calibration_trait_count_exact", calibration.get("trait_count") == 31)
    check("calibration_requirements_exact", calibration.get("requirements") == EXPECTED_CALIBRATION_REQUIREMENTS)
    check("calibration_per_trait_fields_exact", calibration.get("required_per_trait_fields_before_materialization") == EXPECTED_PER_TRAIT_FIELDS)
    check("calibrated_values_null", calibration.get("calibrated_values") is None)

    check("candidate_audit_status_34_of_34", candidate_audit.get("status") == "PASS_R322_GENERIC_FUNCTIONAL_PHENOTYPE_SPECIFICATION_CANDIDATE" and candidate_audit.get("checks_passed") == 34 and candidate_audit.get("checks_total") == 34 and candidate_audit.get("checks_failed") == 0)
    candidate_checks = candidate_audit.get("checks", [])
    check("candidate_audit_all_checks_true_unique", len(candidate_checks) == 34 and len({c.get("name") for c in candidate_checks}) == 34 and all(c.get("pass") is True for c in candidate_checks))

    failed = [c for c in checks if not c["pass"]]
    report = {
        "stage": STAGE,
        "audit": "FINAL_SEAL_INDEPENDENT_SPECIFICATION_CLOSURE",
        "status": PASS if not failed else "FAIL_R322_FINAL_SEAL_AUDIT",
        "verdict": "SEALED" if not failed else "FAIL_CLOSED",
        "parent_authority": parent,
        "summary": {
            "domains": len(domains),
            "primitive_traits": len(traits),
            "derived_capabilities": len(derived),
            "constraint_edges": len(edges),
            "future_state_arrays_materialized": False if arrays else None,
            "phenotype_values_materialized": False,
            "new_biology_executed": False,
            "human_target": False,
            "deep_biological_coupling": False,
        },
        "checks_passed": len(checks) - len(failed),
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "checks": checks,
    }
    return report, not failed


def write_report(report: dict[str, Any], seal_dir: Path) -> None:
    seal_dir.mkdir(parents=True, exist_ok=True)
    audit_json = seal_dir / "R3_22_FINAL_SEAL_AUDIT.json"
    audit_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# v0.6D1-R3.22 — Final Seal Audit",
        "",
        f"- status: `{report['status']}`",
        f"- verdict: `{report['verdict']}`",
        f"- checks: `{report['checks_passed']}/{report['checks_total']} PASS`",
        f"- failed: `{report['checks_failed']}`",
        "",
        "This is a read-only seal of the generic functional-phenotype specification.",
        "No phenotype values are materialized, no biology is executed, Deep remains OFF, and no human target is introduced.",
    ]
    (seal_dir / "R3_22_FINAL_SEAL_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {"stage": STAGE, "files": {}}
    for p in sorted(seal_dir.iterdir()):
        if p.is_file() and p.name != "R3_22_FINAL_SEAL_MANIFEST.json":
            manifest["files"][p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    (seal_dir / "R3_22_FINAL_SEAL_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--output-dir", type=Path)
    ap.add_argument("--parent-seal-dir", type=Path)
    ap.add_argument("--seal-dir", type=Path)
    ns = ap.parse_args()
    root = ns.root.resolve()
    out = (ns.output_dir or (root / "outputs" / "v0_6D1_R3_22")).resolve()
    parent_seal_dir = (ns.parent_seal_dir or (root / "outputs" / "v0_6D1_R3_21_SEAL")).resolve()
    seal_dir = (ns.seal_dir or (root / "outputs" / "v0_6D1_R3_22_SEAL")).resolve()
    try:
        report, ok = audit(root, out, parent_seal_dir)
        write_report(report, seal_dir)
        print(json.dumps(report, indent=2))
        return 0 if ok else 3
    except Exception as exc:
        print(json.dumps({"stage": STAGE, "status": "FAIL_CLOSED", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
