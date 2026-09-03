from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import math

STAGE = "v0.6D1-R3.22"
PARENT_STAGE = "v0.6D1-R3.21"
PARENT_PASS = "PASS_R321_H0_PRESENT_LINEAGE_REGISTRY_HISTORICAL_CLOSURE_AND_FUNCTIONAL_PHENOTYPE_FORK_READINESS_SEALED"
EXPECTED_R319_JSON_SHA256 = "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71"
EXPECTED_R319_NPZ_SHA256 = "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406"
EXPECTED_PRESENT_SPECIES = 134
EXPECTED_PRESENT_COMPONENTS = 295
EXPECTED_PARENT_CHECKS = 43


class R322GateError(RuntimeError):
    """Fail-closed governance/specification error for R3.22."""


@dataclass(frozen=True)
class R322Config:
    require_parent_seal_manifest_closure: bool = True
    require_exact_parent_counts: bool = True


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_parent_seal(seal_dir: Path, cfg: R322Config = R322Config()) -> dict[str, Any]:
    seal_dir = Path(seal_dir)
    audit_path = seal_dir / "R3_21_FINAL_SEAL_AUDIT.json"
    manifest_path = seal_dir / "R3_21_FINAL_SEAL_MANIFEST.json"
    if not audit_path.is_file():
        raise R322GateError(f"Missing R3.21 final seal audit: {audit_path}")
    if cfg.require_parent_seal_manifest_closure and not manifest_path.is_file():
        raise R322GateError(f"Missing R3.21 final seal manifest: {manifest_path}")

    audit = load_json(audit_path)
    if audit.get("stage") != PARENT_STAGE:
        raise R322GateError(f"Parent stage mismatch: {audit.get('stage')}")
    if audit.get("status") != PARENT_PASS or audit.get("verdict") != "SEALED":
        raise R322GateError("R3.21 parent is not SEALED with the expected verdict")
    if int(audit.get("checks_passed", -1)) != EXPECTED_PARENT_CHECKS:
        raise R322GateError("R3.21 parent checks_passed mismatch")
    if int(audit.get("checks_total", -1)) != EXPECTED_PARENT_CHECKS:
        raise R322GateError("R3.21 parent checks_total mismatch")
    if int(audit.get("checks_failed", -1)) != 0:
        raise R322GateError("R3.21 parent reports failed checks")

    source = audit.get("source_checkpoint", {})
    if source.get("json_sha256") != EXPECTED_R319_JSON_SHA256:
        raise R322GateError("R3.21 parent R3.19 JSON provenance mismatch")
    if source.get("npz_sha256") != EXPECTED_R319_NPZ_SHA256:
        raise R322GateError("R3.21 parent R3.19 NPZ provenance mismatch")

    if cfg.require_parent_seal_manifest_closure:
        manifest = load_json(manifest_path)
        rows = manifest.get("files", manifest)
        if not isinstance(rows, dict) or not rows:
            raise R322GateError("R3.21 seal manifest is empty or malformed")
        for name, meta in rows.items():
            if not isinstance(meta, dict):
                continue
            p = seal_dir / name
            if not p.is_file():
                raise R322GateError(f"R3.21 seal manifest file missing: {name}")
            expected_sha = meta.get("sha256")
            expected_bytes = meta.get("bytes")
            if expected_sha is not None and sha256_file(p) != expected_sha:
                raise R322GateError(f"R3.21 seal manifest hash mismatch: {name}")
            if expected_bytes is not None and p.stat().st_size != int(expected_bytes):
                raise R322GateError(f"R3.21 seal manifest size mismatch: {name}")

    return {
        "stage": PARENT_STAGE,
        "status": PARENT_PASS,
        "verdict": "SEALED",
        "checks_passed": EXPECTED_PARENT_CHECKS,
        "source_checkpoint": {
            "json_sha256": EXPECTED_R319_JSON_SHA256,
            "npz_sha256": EXPECTED_R319_NPZ_SHA256,
        },
        "seal_audit_sha256": sha256_file(audit_path),
        "seal_manifest_sha256": sha256_file(manifest_path) if manifest_path.is_file() else None,
    }


def _trait(
    trait_id: str,
    domain: str,
    label: str,
    definition: str,
    empirical_observables: list[str],
    transform_family: str = "EMPIRICAL_MONOTONE_LATENT_CALIBRATION",
) -> dict[str, Any]:
    return {
        "trait_id": trait_id,
        "domain": domain,
        "role": "PRIMARY_EVOLVABLE_FUNCTIONAL_TRAIT",
        "label": label,
        "definition": definition,
        "state_level": "COMPONENT",
        "species_summary": "POPULATION_WEIGHTED_DERIVED_ONLY",
        "latent_coordinate": {
            "symbol": f"z_{trait_id}",
            "space": "REAL",
            "orientation": "HIGHER_MEANS_MORE_OF_NAMED_FUNCTION_NOT_HIGHER_FITNESS",
            "fitness_direction": "CONTEXT_DEPENDENT",
            "calibration_anchor": "MULTI_TAXON_EMPIRICAL_REFERENCE_NOT_HUMAN_ANCHOR",
            "transform_family": transform_family,
        },
        "empirical_observables": empirical_observables,
        "applicability_state": None,
        "applicability_rule": "ARCHITECTURE_AND_ECOLOGY_DETERMINED_NOT_AUTHOR_ASSIGNED",
        "initial_value": None,
        "ancestral_value": None,
        "heritability": None,
        "additive_variance": None,
        "genetic_covariance": None,
        "plasticity": None,
        "selection_optimum": None,
        "metabolic_ecological_cost": None,
        "calibration_status": "UNMATERIALIZED_EMPIRICAL_CALIBRATION_REQUIRED",
    }


def primitive_trait_catalog() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    add = rows.append

    # Manipulative capability: generic control of effectors and object/environment interaction.
    add(_trait("M1_effector_independence", "manipulative_capability", "Effector independence",
               "Degree to which one or more effectors can be controlled independently rather than only as a coupled locomotor/feeding unit.",
               ["independently controllable effector count", "motor fractionation", "bilateral/asymmetric control tasks"]))
    add(_trait("M2_force_precision_span", "manipulative_capability", "Force precision span",
               "Range over which an organism can modulate effector force while retaining stable control.",
               ["minimum controlled force", "maximum controlled force", "force coefficient of variation"]))
    add(_trait("M3_workspace_control", "manipulative_capability", "Reachable workspace control",
               "Fraction and geometric diversity of reachable near-body space in which controlled manipulation can be performed.",
               ["reachable workspace", "orientation repertoire", "target-placement accuracy"]))
    add(_trait("M4_sensorimotor_feedback", "manipulative_capability", "Sensorimotor feedback resolution",
               "Resolution and latency of proprioceptive/tactile or analogous feedback available for closed-loop effector control.",
               ["proprioceptive discrimination", "tactile/spatial discrimination", "closed-loop correction latency"]))

    # Locomotor flexibility: breadth and switching among movement solutions, not speed ranking.
    add(_trait("L1_locomotor_mode_breadth", "locomotor_flexibility", "Locomotor mode breadth",
               "Number and functional separation of locomotor modes that can be deployed without developmental re-specialization.",
               ["mode repertoire", "mode-specific performance", "mode switching frequency"]))
    add(_trait("L2_substrate_breadth", "locomotor_flexibility", "Substrate breadth",
               "Breadth of physical substrates on which locomotion remains viable.",
               ["substrate occupancy", "performance across substrate classes", "failure threshold by substrate"]))
    add(_trait("L3_transition_control", "locomotor_flexibility", "Locomotor transition control",
               "Ability to transition between locomotor states, postures, or substrates while maintaining stability and control.",
               ["transition success rate", "recovery from perturbation", "postural transition cost"]))
    add(_trait("L4_effector_locomotor_decoupling", "locomotor_flexibility", "Effector-locomotor decoupling",
               "Degree to which primary manipulative effectors can be used without simultaneously providing indispensable locomotor support.",
               ["locomotor load on manipulators", "manipulation during locomotion", "alternative support structures"]))

    # Cognition: process-level axes rather than a single intelligence scalar.
    add(_trait("C1_working_memory", "cognitive_capacity", "Working-memory integration",
               "Amount and persistence of task-relevant state that can be actively integrated during behavior.",
               ["delayed response span", "multi-item retention", "interference resistance"]))
    add(_trait("C2_inhibitory_control", "cognitive_capacity", "Inhibitory control",
               "Capacity to suppress a prepotent action when current evidence favors an alternative response.",
               ["detour tasks", "reversal inhibition", "delay-of-response tasks"]))
    add(_trait("C3_relational_integration", "cognitive_capacity", "Relational integration",
               "Capacity to combine multiple relations or cues into a joint behavioral decision.",
               ["transitive/relational tasks", "multi-cue integration", "hierarchical discrimination"]))
    add(_trait("C4_causal_model_depth", "cognitive_capacity", "Causal model depth",
               "Depth to which action-outcome dependencies can be represented beyond immediate associative regularities.",
               ["causal intervention tasks", "mechanism-sensitive transfer", "multi-step action-outcome planning"]))

    # Learning/plasticity.
    add(_trait("P1_acquisition_efficiency", "learning_plasticity", "Learning acquisition efficiency",
               "Rate at which reliable behavior is acquired from repeated evidence after correcting for exposure and motivation.",
               ["trials to criterion", "learning curve slope", "error reduction rate"]))
    add(_trait("P2_retention_stability", "learning_plasticity", "Retention stability",
               "Persistence of learned behavior or information across ecologically relevant delays.",
               ["retention half-life", "delayed recall", "relearning savings"]))
    add(_trait("P3_cross_context_transfer", "learning_plasticity", "Cross-context transfer",
               "Degree to which learned structure transfers to novel contexts rather than remaining stimulus-bound.",
               ["transfer task performance", "novel stimulus generalization", "rule reuse"]))
    add(_trait("P4_developmental_plasticity", "learning_plasticity", "Developmental behavioral plasticity",
               "Breadth of persistent behavioral phenotype change produced by developmental experience within viable limits.",
               ["reaction-norm breadth", "developmental experience effects", "reversible vs persistent plasticity"]))

    # Sociality.
    add(_trait("S1_social_tolerance", "sociality", "Social tolerance",
               "Tolerance of conspecific proximity and resource sharing before conflict costs dominate.",
               ["association tolerance", "resource-sharing tolerance", "aggression threshold"]))
    add(_trait("S2_coordination_capacity", "sociality", "Coordination capacity",
               "Ability of multiple individuals to coordinate complementary or synchronized actions toward an outcome.",
               ["joint-action success", "role differentiation", "synchronization accuracy"]))
    add(_trait("S3_social_learning_fidelity", "sociality", "Social learning fidelity",
               "Reliability with which behavior or information is acquired from conspecific observation or interaction.",
               ["demonstrator-observer transfer", "copying fidelity", "social-vs-individual learning differential"]))
    add(_trait("S4_communication_bandwidth", "sociality", "Communication repertoire bandwidth",
               "Information-bearing diversity and discriminability of signals used in ecologically relevant communication.",
               ["signal repertoire", "context discriminability", "receiver response specificity"]))

    # Dietary flexibility.
    add(_trait("D1_resource_breadth", "dietary_flexibility", "Trophic resource breadth",
               "Breadth of nutritionally viable resource classes used across space and time.",
               ["diet diversity", "resource class occupancy", "realized trophic niche breadth"]))
    add(_trait("D2_digestive_processing_breadth", "dietary_flexibility", "Digestive processing breadth",
               "Breadth of resource chemistries and structures that can be processed at viable energetic return.",
               ["digestive efficiency across foods", "toxin/fiber tolerance", "assimilation breadth"]))
    add(_trait("D3_resource_switching", "dietary_flexibility", "Resource switching flexibility",
               "Ability to switch diet composition as relative resource availability changes without catastrophic fitness loss.",
               ["seasonal diet shift", "functional response breadth", "switching lag"]))

    # Life history. Physical positive variables will use log-family empirical transforms before latent standardization.
    add(_trait("H1_maturation_duration", "life_history", "Maturation duration",
               "Time from birth/hatching/germination-equivalent to functional reproductive maturity.",
               ["age/time to maturity"], "EMPIRICAL_LOG_POSITIVE_THEN_LATENT_STANDARDIZATION"))
    add(_trait("H2_reproductive_output_rate", "life_history", "Reproductive output rate",
               "Rate of viable offspring production under non-catastrophic conditions, corrected for organism scale and life cycle.",
               ["viable offspring per time", "clutch/litter frequency", "reproductive interval"], "EMPIRICAL_LOG_POSITIVE_THEN_LATENT_STANDARDIZATION"))
    add(_trait("H3_parental_investment", "life_history", "Parental investment",
               "Per-offspring energetic, protective, provisioning, or instructional investment before independent survival.",
               ["provisioning energy", "care duration", "protection/instruction effort"], "EMPIRICAL_LOG1P_THEN_LATENT_STANDARDIZATION"))
    add(_trait("H4_adult_survival_horizon", "life_history", "Adult survival horizon",
               "Characteristic adult survival timescale under ordinary ecological mortality rather than exceptional captive lifespan.",
               ["adult survival curve", "expected adult lifespan", "senescence schedule"], "EMPIRICAL_LOG_POSITIVE_THEN_LATENT_STANDARDIZATION"))

    # Ecological generalism.
    add(_trait("G1_habitat_breadth", "ecological_generalism", "Habitat breadth",
               "Breadth of structurally distinct habitat classes supporting positive long-term population growth.",
               ["realized habitat occupancy", "habitat-specific growth", "niche breadth"]))
    add(_trait("G2_climatic_tolerance_breadth", "ecological_generalism", "Climatic tolerance breadth",
               "Breadth of climatic conditions over which populations remain demographically viable.",
               ["thermal performance breadth", "hydric tolerance breadth", "climate occupancy envelope"]))
    add(_trait("G3_disturbance_resilience", "ecological_generalism", "Disturbance resilience",
               "Ability to retain or recover demographic function after non-terminal environmental perturbation.",
               ["recovery time", "post-disturbance growth", "persistence probability"]))
    add(_trait("G4_colonization_breadth", "ecological_generalism", "Colonization breadth",
               "Breadth of accessible environments in which dispersers can establish self-sustaining populations.",
               ["establishment success", "dispersal-to-establishment ratio", "novel habitat colonization"]))

    return rows


def derived_capabilities() -> list[dict[str, Any]]:
    return [
        {
            "capability_id": "T_tool_use_potential",
            "domain": "tool_use_potential",
            "role": "DERIVED_CONTEXTUAL_CAPABILITY_NOT_DIRECTLY_HERITABLE_STATE",
            "definition": "Potential for object-mediated alteration of the environment given manipulative control, causal/relational cognition, learning, sensorimotor feedback, and locally available object affordances.",
            "required_dependencies": [
                "M1_effector_independence", "M2_force_precision_span", "M3_workspace_control",
                "M4_sensorimotor_feedback", "C3_relational_integration", "C4_causal_model_depth",
                "P1_acquisition_efficiency", "P3_cross_context_transfer",
                "ENV_object_affordance_opportunity",
            ],
            "direct_selection_state": False,
            "direct_genetic_state": False,
            "aggregation_function": None,
            "aggregation_status": "UNDEFINED_UNTIL_EMPIRICAL_CALIBRATION",
            "value": None,
        },
        {
            "capability_id": "Q_environmental_problem_solving",
            "domain": "environmental_problem_solving_capability",
            "role": "DERIVED_CONTEXTUAL_CAPABILITY_NOT_DIRECTLY_HERITABLE_STATE",
            "definition": "Capacity to discover effective behavior under ecological novelty by combining cognitive integration, learning, behavioral plasticity, sensorimotor exploration, and environmental opportunity.",
            "required_dependencies": [
                "C1_working_memory", "C2_inhibitory_control", "C3_relational_integration", "C4_causal_model_depth",
                "P1_acquisition_efficiency", "P2_retention_stability", "P3_cross_context_transfer", "P4_developmental_plasticity",
                "L2_substrate_breadth", "M4_sensorimotor_feedback", "ENV_novelty_problem_opportunity",
            ],
            "direct_selection_state": False,
            "direct_genetic_state": False,
            "aggregation_function": None,
            "aggregation_status": "UNDEFINED_UNTIL_EMPIRICAL_CALIBRATION",
            "value": None,
        },
    ]


def domain_catalog(traits: list[dict[str, Any]], derived: list[dict[str, Any]]) -> list[dict[str, Any]]:
    domains = [
        ("manipulative_capability", "PRIMARY_VECTOR"),
        ("locomotor_flexibility", "PRIMARY_VECTOR"),
        ("cognitive_capacity", "PRIMARY_VECTOR"),
        ("learning_plasticity", "PRIMARY_VECTOR"),
        ("sociality", "PRIMARY_VECTOR"),
        ("dietary_flexibility", "PRIMARY_VECTOR"),
        ("life_history", "PRIMARY_VECTOR"),
        ("ecological_generalism", "PRIMARY_VECTOR"),
        ("tool_use_potential", "DERIVED_CONTEXTUAL"),
        ("environmental_problem_solving_capability", "DERIVED_CONTEXTUAL"),
    ]
    out = []
    for domain, kind in domains:
        trait_ids = [t["trait_id"] for t in traits if t["domain"] == domain]
        capability_ids = [d["capability_id"] for d in derived if d["domain"] == domain]
        out.append({
            "domain": domain,
            "kind": kind,
            "primitive_trait_ids": trait_ids,
            "derived_capability_ids": capability_ids,
            "domain_scalar_score": None,
            "ranking_status": "NO_GLOBAL_FITNESS_OR_HUMAN_SIMILARITY_RANKING",
        })
    return out


def constraint_governance(traits: list[dict[str, Any]]) -> dict[str, Any]:
    ids = {t["trait_id"] for t in traits}
    edges = [
        {
            "constraint_id": "K_NEURAL_ENERGETIC_BUDGET",
            "class": "METABOLIC_ALLOCATION_COST",
            "traits": ["C1_working_memory", "C2_inhibitory_control", "C3_relational_integration", "C4_causal_model_depth",
                       "P1_acquisition_efficiency", "P2_retention_stability", "P3_cross_context_transfer",
                       "S3_social_learning_fidelity", "S4_communication_bandwidth"],
            "sign": "COST_INCREASES_WITH_COMBINED_EXPRESSION",
            "numeric_strength": None,
            "status": "EMPIRICAL_CALIBRATION_REQUIRED",
        },
        {
            "constraint_id": "K_OFFSPRING_NUMBER_INVESTMENT",
            "class": "FINITE_REPRODUCTIVE_BUDGET_FRONTIER",
            "traits": ["H2_reproductive_output_rate", "H3_parental_investment"],
            "sign": "CONDITIONAL_NEGATIVE_FEASIBLE_SET_COUPLING",
            "numeric_strength": None,
            "status": "EMPIRICAL_CALIBRATION_REQUIRED",
        },
        {
            "constraint_id": "K_SHARED_EFFECTOR_FUNCTION",
            "class": "MORPHOLOGICAL_SHARED_STRUCTURE_CONSTRAINT",
            "traits": ["M1_effector_independence", "M3_workspace_control", "L4_effector_locomotor_decoupling"],
            "sign": "MORPHOLOGY_DEPENDENT_NOT_UNIVERSALLY_NEGATIVE",
            "numeric_strength": None,
            "status": "EMPIRICAL_CALIBRATION_REQUIRED",
        },
        {
            "constraint_id": "K_DIET_BREADTH_SPECIALIST_EFFICIENCY",
            "class": "GENERALIST_SPECIALIST_FRONTIER",
            "traits": ["D1_resource_breadth", "D2_digestive_processing_breadth", "D3_resource_switching"],
            "sign": "ENVIRONMENT_DEPENDENT_FRONTIER",
            "numeric_strength": None,
            "status": "EMPIRICAL_CALIBRATION_REQUIRED",
        },
        {
            "constraint_id": "K_ECOLOGICAL_BREADTH_SPECIALIZATION",
            "class": "GENERALIST_SPECIALIST_FRONTIER",
            "traits": ["G1_habitat_breadth", "G2_climatic_tolerance_breadth", "G4_colonization_breadth"],
            "sign": "ENVIRONMENT_DEPENDENT_FRONTIER",
            "numeric_strength": None,
            "status": "EMPIRICAL_CALIBRATION_REQUIRED",
        },
        {
            "constraint_id": "K_SOCIALITY_DENSITY_COST",
            "class": "ECOLOGICAL_SOCIAL_COST",
            "traits": ["S1_social_tolerance", "S2_coordination_capacity", "S3_social_learning_fidelity", "S4_communication_bandwidth"],
            "sign": "BENEFIT_AND_COST_BOTH_CONTEXT_DEPENDENT",
            "numeric_strength": None,
            "status": "EMPIRICAL_CALIBRATION_REQUIRED",
        },
        {
            "constraint_id": "K_DEVELOPMENT_LEARNING_WINDOW",
            "class": "DEVELOPMENTAL_TIME_ALLOCATION",
            "traits": ["H1_maturation_duration", "P4_developmental_plasticity", "P1_acquisition_efficiency"],
            "sign": "MECHANISTIC_LINK_SIGN_NOT_FIXED_A_PRIORI",
            "numeric_strength": None,
            "status": "EMPIRICAL_CALIBRATION_REQUIRED",
        },
    ]
    assert all(set(e["traits"]) <= ids for e in edges)
    return {
        "stage": STAGE,
        "principles": [
            "NO_TRAIT_IS_MONOTONICALLY_BETTER_IN_ALL_ENVIRONMENTS",
            "NO_NUMERIC_GENETIC_CORRELATION_IS_AUTHOR_ASSIGNED_IN_R3_22",
            "MECHANISTIC_CONSTRAINTS_DEFINE_WHAT_MUST_BE_CALIBRATED_NOT_THEIR MAGNITUDES".replace(" ", "_"),
            "GENETIC_COVARIANCE_MUST_BE_EMPIRICALLY_ESTIMATED_AND_POSITIVE_SEMIDEFINITE",
            "METABOLIC_AND_ECOLOGICAL_COSTS_ENTER FITNESS_DOWNSTREAM_NOT_AS HUMAN TARGETS".replace(" ", "_"),
        ],
        "constraint_edges": edges,
        "direct_cross_trait_numeric_correlations": None,
        "status": "STRUCTURE_DEFINED_NUMERICS_UNMATERIALIZED",
    }


def replay_interface(traits: list[dict[str, Any]], derived: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(traits)
    return {
        "stage": STAGE,
        "state_level": "COMPONENT",
        "component_count_parent": EXPECTED_PRESENT_COMPONENTS,
        "primitive_trait_count": n,
        "primitive_trait_order": [t["trait_id"] for t in traits],
        "applicability_model": {
            "states": ["ACTIVE", "STRUCTURAL_ZERO", "NOT_APPLICABLE", "UNKNOWN"],
            "authority": "MORPHOLOGICAL_LIFE_HISTORY_ARCHITECTURE_PLUS_EMPIRICAL_CALIBRATION",
            "continuous_drift_can_activate_not_applicable_trait": False,
            "activation_requires": "SEPARATELY_GOVERNED_MORPHOLOGICAL_OR_FUNCTIONAL_INNOVATION_EVENT",
            "materialized_in_r3_22": False,
        },
        "future_state_arrays": {
            "functional_applicability_code": {
                "shape": ["n_component", "n_functional_trait"],
                "dtype": "uint8_or_enum",
                "constraints": ["VALID_ENUM_ONLY"],
                "materialized_in_r3_22": False,
            },
            "functional_mean_z": {
                "shape": ["n_component", "n_functional_trait"],
                "dtype": "float64",
                "materialized_in_r3_22": False,
                "semantics": "population mean latent genetic-functional coordinate",
            },
            "functional_va": {
                "shape": ["n_component", "n_functional_trait"],
                "dtype": "float64",
                "constraints": ["FINITE_AND_NONNEGATIVE_WHERE_ACTIVE"],
                "materialized_in_r3_22": False,
            },
            "functional_gcov": {
                "shape": ["n_component", "n_functional_trait", "n_functional_trait"],
                "dtype": "float64",
                "constraints": ["FINITE_WHERE_ACTIVE", "SYMMETRIC_ACTIVE_SUBMATRIX", "POSITIVE_SEMIDEFINITE_ACTIVE_SUBMATRIX"],
                "materialized_in_r3_22": False,
            },
            "functional_plasticity_beta": {
                "shape": ["n_component", "n_functional_trait", "n_environment_driver"],
                "dtype": "float64",
                "constraints": ["FINITE_WHERE_ACTIVE"],
                "materialized_in_r3_22": False,
            },
        },
        "expression_model": {
            "equation": "z_expressed = z_genetic_mean + B_plasticity @ E_centered + developmental_residual",
            "numeric_parameters": None,
            "status": "FORM_DEFINED_PARAMETERS_UNCALIBRATED",
        },
        "evolution_model_family": {
            "equation": "delta_z = G_functional @ beta_selection + gene_flow + drift + mutation_input",
            "time_base": "GENERATIONS_WITH_WORLD_CLOCK_CONVERSION",
            "numeric_parameters": None,
            "status": "FORM_DEFINED_PARAMETERS_UNCALIBRATED",
        },
        "species_aggregation": {
            "mean": "POPULATION_WEIGHTED_COMPONENT_MEAN_OVER_ACTIVE_APPLICABLE_COMPONENTS",
            "variance": "WITHIN_AND_BETWEEN_COMPONENT_DECOMPOSITION_OVER_ACTIVE_APPLICABLE_COMPONENTS",
            "single_species_scalar_forbidden": True,
        },
        "derived_capabilities": [d["capability_id"] for d in derived],
        "derived_capabilities_are_direct_genetic_state": False,
        "existing_r319_reduced_ecological_state_repurposed": False,
        "cross_covariance_with_existing_three_ecological_traits": None,
        "cross_covariance_status": "FORBIDDEN_TO_INVENT_REQUIRES_LATER_EMPIRICAL_CALIBRATION",
        "deep_biological_coupling": "OFF",
        "human_target": False,
    }


def calibration_requirements(traits: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "stage": STAGE,
        "status": "REQUIRED_BEFORE_ANY_FUNCTIONAL_VALUES_OR_REPLAY",
        "trait_count": len(traits),
        "requirements": [
            "USE_COMPARATIVE_MULTI_TAXON_DATA_WHERE_AVAILABLE",
            "CORRECT_PHYLOGENETIC_NON_INDEPENDENCE",
            "CORRECT_BODY_SIZE_AND_METABOLIC_ALLOMETRY_WHERE_RELEVANT",
            "REPRESENT_MEASUREMENT_UNCERTAINTY_AND_PROXY_UNCERTAINTY",
            "KEEP_RAW_OBSERVABLES_SEPARATE_FROM_LATENT_FUNCTIONAL_COORDINATES",
            "VALIDATE_PROXY_CONCORDANCE_WITH_HELD_OUT_TAXA_OR_DATASETS",
            "ESTIMATE_HERITABILITY_OR_ADDITIVE_VARIANCE_FROM EMPIRICAL EVIDENCE; DO NOT AUTHOR-ASSIGN".replace(" ", "_"),
            "ESTIMATE_GENETIC_COVARIANCE_OR USE A DOCUMENTED CONSERVATIVE ZERO-CROSS-COVARIANCE BASELINE ONLY AFTER AUDIT".replace(" ", "_"),
            "CALIBRATE_METABOLIC_ECOLOGICAL_COSTS_IN PHYSICAL OR DEMOGRAPHIC CURRENCY".replace(" ", "_"),
            "NO_SINGLE_SPECIES_OR_HUMAN_ANCHOR_DEFINES THE SCALE".replace(" ", "_"),
            "DEEP_NOETIC_EXPOSURE_MUST_NOT ENTER THE CALIBRATION OR FUNCTIONAL TRAIT DYNAMICS".replace(" ", "_"),
            "NO_HUMAN_READINESS_SAPIENCE_CIVILIZATION_OR_TOOL_USE_TARGET_IS USED TO FIT PRIMARY TRAITS".replace(" ", "_"),
        ],
        "required_per_trait_fields_before_materialization": [
            "empirical_source_set",
            "observable_to_latent_mapping",
            "uncertainty_model",
            "heritability_or_va_model",
            "cost_model_if_non_negligible",
            "validation_result",
        ],
        "calibrated_values": None,
    }


def specification(parent: dict[str, Any]) -> dict[str, Any]:
    traits = primitive_trait_catalog()
    derived = derived_capabilities()
    domains = domain_catalog(traits, derived)
    return {
        "stage": STAGE,
        "title": "Generic Functional Phenotype State-Space Specification, Trade-Off Governance & Replay Interface",
        "status": "CANDIDATE_SPECIFICATION_ONLY_NO_PHENOTYPE_VALUES",
        "parent_authority": parent,
        "scope": "GENERIC_ALL_LINEAGES_NO_HUMAN_TARGET",
        "present_species_parent": EXPECTED_PRESENT_SPECIES,
        "present_components_parent": EXPECTED_PRESENT_COMPONENTS,
        "state_granularity": "COMPONENT_PRIMARY_SPECIES_SUMMARY_DERIVED",
        "domain_count": len(domains),
        "primitive_trait_count": len(traits),
        "derived_capability_count": len(derived),
        "domains": domains,
        "primary_state_principles": [
            "MULTIVARIATE_NOT_SINGLE_INTELLIGENCE_AXIS",
            "CONTEXT_DEPENDENT_FITNESS",
            "NO_GLOBAL_CAPABILITY_RANKING",
            "NO_HUMAN_SIMILARITY_SCORE",
            "NO_SAPIENCE_OR_CIVILIZATION_TARGET",
            "DERIVED_TOOL_USE_AND_PROBLEM_SOLVING_ARE_NOT_DIRECT_GENETIC_STATE",
            "TRAIT_APPLICABILITY_IS_SEPARATE_FROM_TRAIT_MAGNITUDE",
            "NOT_APPLICABLE_TRAITS_CANNOT_APPEAR_BY_CONTINUOUS_DRIFT_ALONE",
            "EXISTING_R319_THREE_TRAIT_REDUCED_STATE_IS_PRESERVED_SEPARATELY",
            "DEEP_BIOLOGICAL_COUPLING_OFF",
        ],
        "values_materialized": False,
        "new_biology_executed": False,
        "human_target": False,
        "deep_biological_coupling": False,
    }


def build_all(parent: dict[str, Any]) -> dict[str, Any]:
    traits = primitive_trait_catalog()
    derived = derived_capabilities()
    return {
        "specification": specification(parent),
        "traits": {
            "stage": STAGE,
            "status": "SCHEMA_AND_SEMANTICS_ONLY",
            "trait_count": len(traits),
            "traits": traits,
        },
        "derived": {
            "stage": STAGE,
            "status": "DEPENDENCY_GRAPH_ONLY_NO_VALUES",
            "capability_count": len(derived),
            "capabilities": derived,
        },
        "constraints": constraint_governance(traits),
        "replay": replay_interface(traits, derived),
        "calibration": calibration_requirements(traits),
    }


def audit_documents(docs: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, cond: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    spec = docs["specification"]
    traits_doc = docs["traits"]
    derived_doc = docs["derived"]
    constraints = docs["constraints"]
    replay = docs["replay"]
    calibration = docs["calibration"]
    traits = traits_doc["traits"]
    derived = derived_doc["capabilities"]
    ids = [t["trait_id"] for t in traits]
    domains = [d["domain"] for d in spec["domains"]]

    expected_domains = [
        "manipulative_capability", "locomotor_flexibility", "cognitive_capacity", "learning_plasticity",
        "sociality", "dietary_flexibility", "life_history", "ecological_generalism",
        "tool_use_potential", "environmental_problem_solving_capability",
    ]

    check("stage_exact", spec.get("stage") == STAGE)
    check("parent_sealed", spec.get("parent_authority", {}).get("status") == PARENT_PASS)
    check("parent_43_of_43", spec.get("parent_authority", {}).get("checks_passed") == 43)
    check("parent_r319_json_provenance", spec.get("parent_authority", {}).get("source_checkpoint", {}).get("json_sha256") == EXPECTED_R319_JSON_SHA256)
    check("parent_r319_npz_provenance", spec.get("parent_authority", {}).get("source_checkpoint", {}).get("npz_sha256") == EXPECTED_R319_NPZ_SHA256)
    check("parent_counts_exact", spec.get("present_species_parent") == 134 and spec.get("present_components_parent") == 295)
    check("ten_reserved_domains_exact", domains == expected_domains, domains)
    check("primitive_trait_count_31", len(traits) == 31, len(traits))
    check("primitive_trait_ids_unique", len(ids) == len(set(ids)))
    check("all_primary_component_level", all(t.get("state_level") == "COMPONENT" for t in traits))
    check("all_primary_values_null", all(t.get("initial_value") is None and t.get("ancestral_value") is None for t in traits))
    check("all_applicability_unmaterialized", all(t.get("applicability_state") is None for t in traits))
    check("heritability_unmaterialized", all(t.get("heritability") is None for t in traits))
    check("costs_unmaterialized", all(t.get("metabolic_ecological_cost") is None for t in traits))
    check("context_dependent_fitness_all_traits", all(t.get("latent_coordinate", {}).get("fitness_direction") == "CONTEXT_DEPENDENT" for t in traits))
    check("derived_capability_count_2", len(derived) == 2)
    check("derived_not_direct_genetic_state", all(d.get("direct_genetic_state") is False for d in derived))
    check("derived_not_direct_selection_state", all(d.get("direct_selection_state") is False for d in derived))
    check("derived_values_null", all(d.get("value") is None and d.get("aggregation_function") is None for d in derived))
    check("no_global_domain_scores", all(d.get("domain_scalar_score") is None for d in spec["domains"]))
    check("no_human_target", spec.get("human_target") is False and replay.get("human_target") is False)
    check("deep_off", spec.get("deep_biological_coupling") is False and replay.get("deep_biological_coupling") == "OFF")
    check("no_new_biology", spec.get("new_biology_executed") is False)
    check("existing_reduced_state_not_repurposed", replay.get("existing_r319_reduced_ecological_state_repurposed") is False)
    check("cross_covariance_not_invented", replay.get("cross_covariance_with_existing_three_ecological_traits") is None)
    arrays = replay.get("future_state_arrays", {})
    check("future_state_not_materialized", arrays and all(x.get("materialized_in_r3_22") is False for x in arrays.values()))
    check("applicability_gate_present", replay.get("applicability_model", {}).get("continuous_drift_can_activate_not_applicable_trait") is False)
    check("future_gcov_psd", "POSITIVE_SEMIDEFINITE_ACTIVE_SUBMATRIX" in arrays.get("functional_gcov", {}).get("constraints", []))
    check("species_summary_derived_only", replay.get("species_aggregation", {}).get("single_species_scalar_forbidden") is True)
    check("constraint_numerics_null", all(e.get("numeric_strength") is None for e in constraints.get("constraint_edges", [])))
    check("no_numeric_cross_trait_correlations", constraints.get("direct_cross_trait_numeric_correlations") is None)
    check("calibration_required_before_materialization", calibration.get("status") == "REQUIRED_BEFORE_ANY_FUNCTIONAL_VALUES_OR_REPLAY")
    check("calibrated_values_null", calibration.get("calibrated_values") is None)

    forbidden_trait_tokens = ("human", "sapience", "civilization", "readiness", "chosen")
    lowered_ids = " ".join(ids).lower()
    check("trait_ids_non_anthropocentric", not any(tok in lowered_ids for tok in forbidden_trait_tokens))

    failed = [c for c in checks if not c["pass"]]
    return {
        "stage": STAGE,
        "audit": "GENERIC_FUNCTIONAL_PHENOTYPE_SPECIFICATION_CLOSURE",
        "status": "PASS_R322_GENERIC_FUNCTIONAL_PHENOTYPE_SPECIFICATION_CANDIDATE" if not failed else "FAIL_R322_SPECIFICATION_AUDIT",
        "checks_passed": len(checks) - len(failed),
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "checks": checks,
    }
