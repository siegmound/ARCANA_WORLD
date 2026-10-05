"""Static requirements tests for B6N7; no solver or propagation is run."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts/R6_MINIMUM_EVOLVABLE_RIFT_MODEL_REQUIREMENTS_V1.json"
MATRIX_PATH = ROOT / "contracts/R6_MINIMUM_RIFT_MODEL_B6N4R1_BLOCKER_MATRIX_V1.json"
B6N5_PATH = ROOT / "docs/arcana/qualifications/R6_B6N5_ATTESTATION.json"
B6N6_PATH = ROOT / "docs/arcana/qualifications/R6_B6N6_ATTESTATION.json"


def load():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8")), json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def test_exact_transition_time_is_not_required_in_advance():
    contract, _ = load()
    assert contract["scope"]["no_exact_future_transition_time_required"] is True
    assert "Exact future crossing time is not a required model input" in contract["runtime_predicate_contract"][0]["crossing"]


def test_evolved_state_is_distinct_from_diagnostics_forcings_and_predicates():
    contract, _ = load()
    assert contract["minimum_interface"]["evolved_state_requirement"]["required"] is True
    assert "distinct from kinematic diagnostics, forcing, parameters, predicates" in contract["minimum_interface"]["evolved_state_requirement"]["state_vs_diagnostic"]
    assert contract["minimum_interface"]["forcing_inputs"][0]["role"] == "CONDITIONAL_GOVERNED_KINEMATIC_FORCING"


def test_predicate_crossing_does_not_invent_topology_or_transition_result():
    contract, _ = load()
    assert "PREDICATE != EVENT != TRANSITION APPLICATION" in contract["minimum_interface"]["predicate_outputs"]["semantics"]
    assert all(row["automatic_transition_application"] is False for row in contract["runtime_predicate_contract"])


def test_all_four_b6n4r1_blockers_have_runtime_observables_and_predicates():
    contract, matrix = load()
    expected = {"GENERIC_TOPOLOGY_EVENT_COVERAGE", "NEXT_RIFT_PROCESS_EVOLUTION", "PLATE_INTERFACE_EVENT_PREDICATES", "SUPPORT_MEMBERSHIP_VALIDITY"}
    assert {row["blocker"] for row in contract["b6n4r1_blocker_matrix"]} == expected
    assert {row["b6n4r1_blocker"] for row in matrix["rows"]} == expected
    assert all(row["required_observables"] and row["predicate_family"] for row in matrix["rows"])


def test_one_shared_state_does_not_claim_one_common_authority():
    contract, matrix = load()
    assert "a common authority is not presumed" in matrix["nonclosure_rule"]
    assert "a common authority is not presumed" in contract["b6n4r1_blocker_matrix"][0]["dependency"]


def test_mechanics_is_not_silently_required_or_claimed_unnecessary():
    contract, _ = load()
    assert contract["lowest_sufficient_tier_decision"]["mechanics"] == "NOT_PROVEN_REQUIRED"
    tier2 = next(row for row in contract["model_tiers"] if row["tier"] == "TIER_2_REDUCED_ORDER_RIFT_PROCESS_MODEL")
    assert "may qualify only if its scientific basis" in tier2["mechanics_required"]


def test_authority_classes_remain_distinct():
    contract, _ = load()
    classes = {row["authority_class"] for row in contract["authority_requirements"]}
    assert {"EXISTING_ARCANA_MODEL_AUTHORITY", "DETERMINISTIC_DERIVATION", "AUTHORIAL_MODEL_DECISION", "EXTERNAL_SCIENTIFIC_MODEL_OR_LITERATURE_CALIBRATION", "EXTERNAL_DATA_PROVIDER", "MECHANICAL_MODEL_AUTHORITY", "UNKNOWN_PENDING_TARGETED_MODEL_RESEARCH_AND_AUTHORIAL_DECISION"} <= classes


def test_refinement_cannot_compensate_for_absent_model_variables():
    contract, _ = load()
    assert contract["scope"]["does_not_authorize"]
    assert contract["minimum_interface"]["evolved_state_requirement"]["required"] is True
    assert contract["lowest_sufficient_tier_decision"]["external_research"].startswith("REQUIRED_BEFORE_SCIENTIFIC_MODEL_SELECTION")


def test_local_rift_scope_is_allowed_but_dependency_buffer_must_be_proven():
    contract, _ = load()
    assert "active local spatial scope and proven dependency/buffer scope" in contract["minimum_interface"]["initialization_inputs"]
    assert "dependency buffer" in contract["runtime_predicate_contract"][1]["scope"]


def test_replay_requirements_cover_model_forcing_state_predicates_and_refinement():
    contract, _ = load()
    replay = set(contract["replay_minimum"])
    assert {"model/version identity/hash", "initial process state and support identity", "ordered forcing references", "predicate definitions and versions", "numerical method/configuration and accepted/rejected steps", "local spatial scope and dependency/buffer proof", "refinement decisions"} <= replay


def test_existing_rigid_kinematics_does_not_imply_extension_or_boundary_type():
    contract, _ = load()
    forcing = contract["minimum_interface"]["forcing_inputs"][0]
    assert forcing["conditionally_governed"] is True
    assert forcing["usable_for_current_forward_propagation"] is False
    assert "not physical extension" in forcing["derivable_from_existing_authority"]
    relative = next(row for row in contract["candidate_quantity_adjudication"] if row["concept"] == "relative_plate_displacement_or_velocity")
    assert "extension polarity" in relative["cannot_establish"]


def test_coupling_scope_does_not_expand_to_full_world_history():
    contract, _ = load()
    couplings = {row["domain"]: row["classification"] for row in contract["coupling_scope"]}
    assert couplings["tectonic_geometry_and_topology"] == "REQUIRED_FOR_RIFT_EVOLUTION"
    assert couplings["climate"] == "DOWNSTREAM_ONLY"
    assert couplings["Deep"] == "UNKNOWN"


def test_candidate_quantities_are_adjudicated_not_adopted_automatically():
    contract, _ = load()
    candidates = {row["concept"]: row for row in contract["candidate_quantity_adjudication"]}
    assert candidates["relative_extension_or_extension_rate"]["current_status"] == "UNKNOWN_NOT_GOVERNED"
    assert candidates["accumulated_extension_or_opening_displacement"]["current_status"] == "NOT_SELECTED"
    assert candidates["crustal_thickness_or_thinning_state"]["minimum_required"].startswith("Not required merely")


def test_every_candidate_quantity_answers_all_ten_requirement_dimensions():
    contract, _ = load()
    required = {"why_needed", "current_blockers", "quantity_kind", "authority", "derivable_from_existing_plate_kinematics", "mechanics_required", "external_scientific_calibration_required", "scope", "uncertainty", "runtime_consumers"}
    rows = contract["candidate_quantity_adjudication"]
    assert rows
    assert all(required <= set(row["assessment"]) for row in rows)


def test_tier_comparison_identifies_reduced_order_candidate_without_selecting_provider():
    contract, _ = load()
    tiers = {row["tier"]: row for row in contract["model_tiers"]}
    assert tiers["TIER_0_EXISTING_RIGID_KINEMATICS"]["status"] == "INSUFFICIENT"
    assert tiers["TIER_1_PURE_KINEMATIC_EXTENSION"]["status"] == "NOT_SUFFICIENT_ALONE"
    assert tiers["TIER_2_REDUCED_ORDER_RIFT_PROCESS_MODEL"]["status"].startswith("LOWEST_REQUIREMENTS_TIER")
    assert tiers["TIER_4_FULL_MECHANICAL_GEODYNAMIC_MODEL"]["status"] == "NOT_PROVEN_NECESSARY; NOT_SELECTED"
    assert contract["lowest_sufficient_tier_decision"]["provider_selected"] is False


def test_current_b6n5_blocker_and_b6n6_authority_are_preserved():
    contract, _ = load()
    b5 = json.loads(B6N5_PATH.read_text(encoding="utf-8"))
    b6 = json.loads(B6N6_PATH.read_text(encoding="utf-8"))
    assert b5["verdict"] == "BLOCKED_B6N5_INSUFFICIENT_STRUCTURAL_TRANSITION_AUTHORITY"
    assert b5["structural_transition_authority"]["next_structural_transition_predicate"] == "UNKNOWN_NOT_GOVERNED"
    assert b6["verdict"] == "PASS_B6N6_ADAPTIVE_PROPAGATION_STATE_EXTRACTION_ARCHITECTURE"
    assert contract["qualified_context"]["current_process_state"] == "RIFT_PROCESS_ACTIVE"


def test_no_dt2_canonical_or_execution_authority_is_created():
    contract, _ = load()
    gates = contract["authorization_gates"]
    assert all(value is False for value in gates.values())
    assert contract["status"] == "REQUIREMENTS_DEFINED_MODEL_NOT_SELECTED_OR_QUALIFIED"


def test_contract_does_not_select_equations_coefficients_thresholds_or_provider():
    contract, _ = load()
    assert contract["scope"]["no_equation_coefficient_or_threshold_selected"] is True
    assert contract["lowest_sufficient_tier_decision"]["provider_selected"] is False
    assert contract["lowest_sufficient_tier_decision"]["numerical_calibration_performed"] is False


def test_matrix_explicitly_preserves_nonclosure_and_separate_authority():
    _, matrix = load()
    assert matrix["status"] == "REQUIREMENTS_TRACEABILITY_MATRIX_NOT_BLOCKER_CLOSURE"
    assert "does not claim the blockers are closed" in matrix["nonclosure_rule"]
    assert all(row["authority_note"] for row in matrix["rows"])
