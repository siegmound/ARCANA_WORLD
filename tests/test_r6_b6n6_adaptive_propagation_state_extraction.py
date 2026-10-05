"""Static contract checks for B6N6; no simulation or canonical-store writes."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROPAGATION_PATH = ROOT / "contracts/R6_ADAPTIVE_PROPAGATION_CANDIDATE_TRAJECTORY_V1.json"
EXTRACTION_PATH = ROOT / "contracts/R6_SIGNIFICANT_STATE_EXTRACTION_RECONSTRUCTION_V1.json"
B6N5_PATH = ROOT / "docs/arcana/qualifications/R6_B6N5_ATTESTATION.json"


def load_contracts():
    return json.loads(PROPAGATION_PATH.read_text(encoding="utf-8")), json.loads(
        EXTRACTION_PATH.read_text(encoding="utf-8")
    )


def test_temporal_concepts_separate_internal_dt_and_persistent_interval():
    prop, _ = load_contracts()
    concepts = prop["temporal_concepts"]
    assert concepts["INTERNAL_DT"]["persistent_record_interval"] is False
    assert concepts["PERSISTENT_STATE_INTERVAL"]["selected_before_propagation"] is False
    assert concepts["PERSISTENT_STATE_INTERVAL"]["emerges_after_extraction"] is True
    assert concepts["invariant"] == "INTERNAL_DT != PERSISTENT_STATE_INTERVAL"


def test_candidate_samples_are_temporary_noncanonical():
    prop, _ = load_contracts()
    assert "not DomainState records and not canonical states" in prop["candidate_trajectory"]["samples"]
    assert prop["candidate_trajectory"]["discard_permitted_after"]


def test_adaptive_dt_is_capped_by_authority_bound():
    prop, _ = load_contracts()
    assert "never exceed" in prop["adaptive_controller"]["upper_bound_rule"]
    assert "Do not invent a physical constant" in prop["adaptive_controller"]["unbound_threshold_behavior"]


def test_refinable_and_irreducible_unknowns_have_different_actions():
    prop, _ = load_contracts()
    unknown = prop["uncertainty_taxonomy"]
    assert "REFINE_TIME" in unknown["TEMPORAL_RESOLUTION_UNKNOWN"]["permitted_actions"]
    assert "REQUEST_NEW_MODEL_OR_AUTHORITY" in unknown["MODEL_AUTHORITY_UNKNOWN"]["permitted_actions"]
    assert "REFINE_TIME" not in unknown["MODEL_AUTHORITY_UNKNOWN"]["permitted_actions"]
    assert prop["authority_and_refinement_rule"]["no_infinite_refinement_for_authority_unknown"] is True


def test_event_bracketing_refines_interval_without_fabricated_exact_time():
    prop, _ = load_contracts()
    detection = prop["event_detection"]
    assert "[tA,tB]" in detection["workflow"][0]
    assert "Never fabricate a point time" in detection["exact_event_time"]


def test_local_refinement_isolated_and_dependency_scoped():
    prop, _ = load_contracts()
    local = prop["local_refinement"]
    assert "parent checkpoint" in local["required_bindings"]
    assert "replay recipe" in local["required_bindings"]
    assert "does not recompute or mutate the global parent" in local["isolation_rule"]


def test_extraction_occurs_after_trajectory_resolution():
    _, ext = load_contracts()
    assert ext["extraction_order"][0].startswith("resolve required")
    assert ext["extraction_order"].index("select mandatory causal/event/uncertainty boundaries") < ext["extraction_order"].index("retain only required persistent states/checkpoints and replay closure")


def test_insignificant_intermediate_samples_can_be_omitted():
    _, ext = load_contracts()
    assert "Intermediate numerical samples are omitted" in ext["compression"]["rule"]
    assert "minimum persistent causal set" in ext["compression"]["minimum_representation"]


def test_mandatory_event_and_causal_boundaries_cannot_be_compressed():
    _, ext = load_contracts()
    required = ext["mandatory_boundaries"]
    assert "governed event boundaries" in required
    assert "PRE_EVENT and POST_EVENT states when causal event semantics require them" in required
    assert "uncertainty boundaries required to prevent UNKNOWN from being compressed into a known value" in required


def test_replay_metadata_survives_sample_compression():
    prop, ext = load_contracts()
    assert "base checkpoint identity" in prop["candidate_trajectory"]["minimum_replay_metadata"]
    assert "refinement decisions and parent/child scope bindings" in prop["candidate_trajectory"]["minimum_replay_metadata"]
    assert "expected extracted state and payload identities" in prop["candidate_trajectory"]["minimum_replay_metadata"]
    assert "expected output state and payload identities" in ext["replay_closure"]["reuse_existing_recipe_fields"]


def test_failed_candidate_cannot_change_canonical_world_history():
    prop, ext = load_contracts()
    assert "canonical WORLD_HISTORY remains unchanged" in prop["canonicalization"]["failure_behavior"]
    assert "No partial visibility" in ext["canonical_publication"]["failure"]


def test_publication_uses_existing_atomic_store_transactions():
    prop, ext = load_contracts()
    assert "HistoryStore.append_transaction" in prop["canonicalization"]["transaction_mechanism"]
    assert "append_refinement_transaction" in ext["canonical_publication"]["publication"]


def test_event_can_persist_without_state_and_is_not_erased_by_no_state():
    prop, ext = load_contracts()
    assert prop["event_detection"]["event_without_state"].startswith("Permitted")
    assert "NO NEW STATE never deletes" in ext["event_ledger"]["no_state_rule"]


def test_b6n5_rift_gap_is_preserved_and_not_refinable():
    prop, _ = load_contracts()
    b6n5 = json.loads(B6N5_PATH.read_text(encoding="utf-8"))
    assert b6n5["structural_transition_authority"]["next_structural_transition_predicate"] == "UNKNOWN_NOT_GOVERNED"
    assert b6n5["structural_transition_authority"]["common_causal_authority_proven"] is False
    assert prop["current_rift_architecture_check"]["current_b6n5_status"] == "MODEL_AUTHORITY_GAP_NOT_SOLVED_BY_ADAPTIVE_RESOLUTION"
    assert prop["current_rift_architecture_check"]["preserve_b6n5"]["mechanics_necessity"] == "NOT_PROVEN"


def test_b6n5_temporal_values_keep_their_existing_meaning():
    prop, _ = load_contracts()
    preserved = prop["current_rift_architecture_check"]["preserve_b6n5"]
    assert preserved["consumed_pre_activation_horizon_years"] == 27123.405156307464
    assert preserved["model_scope_revalidation_horizon_years"] == 8214.051909111062
    assert preserved["revalidation_horizon_is_event_bound"] is False


def test_no_execution_or_canonical_authorization_is_introduced():
    prop, ext = load_contracts()
    for gates in (prop["authorization_gates"], ext["authorization_gates"]):
        assert gates["SECOND_DT_SELECTED"] is False
        assert gates["T2_CREATED"] is False
        assert gates["B6O_authorized"] is False
        assert gates["mechanics_executed"] is False
        assert gates["forward_propagation_executed"] is False
        assert gates["topology_transition_executed"] is False
        assert gates["canonical_world_history_modified"] is False


def test_architecture_reuses_existing_replay_refinement_retention_and_event_policy():
    prop, ext = load_contracts()
    assert "src/arcana_worldsim/r6/replay.py" in prop["scope"]["reuses"]
    assert "src/arcana_worldsim/r6/refinement.py" in prop["scope"]["reuses"]
    assert ext["reuses"]["minimal_state_contract"].endswith("MinimalStateContract")
    assert ext["reuses"]["event_significance_policy"].endswith("V1.json")
