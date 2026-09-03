from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcana_worldsim.scientific_engines.r322_functional_phenotype_spec import (
    audit_documents,
    build_all,
    derived_capabilities,
    primitive_trait_catalog,
    replay_interface,
)


def fake_parent():
    return {
        "stage": "v0.6D1-R3.21",
        "status": "PASS_R321_H0_PRESENT_LINEAGE_REGISTRY_HISTORICAL_CLOSURE_AND_FUNCTIONAL_PHENOTYPE_FORK_READINESS_SEALED",
        "verdict": "SEALED",
        "checks_passed": 43,
        "source_checkpoint": {
            "json_sha256": "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71",
            "npz_sha256": "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406",
        },
        "seal_audit_sha256": "x",
        "seal_manifest_sha256": "y",
    }


def test_catalog_has_exact_31_unique_primary_traits():
    traits = primitive_trait_catalog()
    ids = [x["trait_id"] for x in traits]
    assert len(traits) == 31
    assert len(ids) == len(set(ids))
    assert all(x["role"] == "PRIMARY_EVOLVABLE_FUNCTIONAL_TRAIT" for x in traits)


def test_all_primary_state_is_component_level_and_unmaterialized():
    for t in primitive_trait_catalog():
        assert t["state_level"] == "COMPONENT"
        assert t["applicability_state"] is None
        assert t["initial_value"] is None
        assert t["ancestral_value"] is None
        assert t["heritability"] is None
        assert t["genetic_covariance"] is None
        assert t["metabolic_ecological_cost"] is None


def test_no_trait_id_is_human_targeted():
    ids = " ".join(t["trait_id"] for t in primitive_trait_catalog()).lower()
    for token in ("human", "sapience", "civilization", "readiness", "chosen"):
        assert token not in ids


def test_derived_capabilities_not_direct_genetic_traits():
    caps = derived_capabilities()
    assert {x["capability_id"] for x in caps} == {"T_tool_use_potential", "Q_environmental_problem_solving"}
    assert all(x["direct_genetic_state"] is False for x in caps)
    assert all(x["direct_selection_state"] is False for x in caps)
    assert all(x["aggregation_function"] is None for x in caps)


def test_replay_state_uses_full_g_matrix_and_keeps_r319_separate():
    traits = primitive_trait_catalog()
    replay = replay_interface(traits, derived_capabilities())
    assert replay["future_state_arrays"]["functional_gcov"]["shape"] == ["n_component", "n_functional_trait", "n_functional_trait"]
    assert "POSITIVE_SEMIDEFINITE_ACTIVE_SUBMATRIX" in replay["future_state_arrays"]["functional_gcov"]["constraints"]
    assert replay["applicability_model"]["continuous_drift_can_activate_not_applicable_trait"] is False
    assert replay["existing_r319_reduced_ecological_state_repurposed"] is False
    assert replay["cross_covariance_with_existing_three_ecological_traits"] is None


def test_species_summary_is_derived_not_primary_state():
    replay = replay_interface(primitive_trait_catalog(), derived_capabilities())
    assert replay["state_level"] == "COMPONENT"
    assert replay["species_aggregation"]["single_species_scalar_forbidden"] is True


def test_full_audit_passes():
    docs = build_all(fake_parent())
    audit = audit_documents(docs)
    assert audit["checks_failed"] == 0, [x for x in audit["checks"] if not x["pass"]]
    assert audit["checks_passed"] == audit["checks_total"]


def test_exact_ten_domains_and_two_derived_domains():
    docs = build_all(fake_parent())
    domains = docs["specification"]["domains"]
    assert len(domains) == 10
    assert sum(d["kind"] == "DERIVED_CONTEXTUAL" for d in domains) == 2
    assert all(d["domain_scalar_score"] is None for d in domains)


def test_deep_off_and_no_human_target():
    docs = build_all(fake_parent())
    assert docs["specification"]["deep_biological_coupling"] is False
    assert docs["specification"]["human_target"] is False
    assert docs["replay"]["deep_biological_coupling"] == "OFF"
    assert docs["replay"]["human_target"] is False


def test_constraint_numeric_strengths_are_unmaterialized():
    docs = build_all(fake_parent())
    assert docs["constraints"]["direct_cross_trait_numeric_correlations"] is None
    assert all(e["numeric_strength"] is None for e in docs["constraints"]["constraint_edges"])


def test_calibration_must_precede_values_or_replay():
    docs = build_all(fake_parent())
    c = docs["calibration"]
    assert c["status"] == "REQUIRED_BEFORE_ANY_FUNCTIONAL_VALUES_OR_REPLAY"
    assert c["calibrated_values"] is None


def test_documents_are_json_serializable_deterministically():
    docs = build_all(fake_parent())
    a = json.dumps(docs, sort_keys=True)
    b = json.dumps(build_all(fake_parent()), sort_keys=True)
    assert a == b
