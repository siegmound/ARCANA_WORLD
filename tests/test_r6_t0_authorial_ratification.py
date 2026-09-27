import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ratification_manifest_is_explicit_and_not_canonical():
    manifest = json.loads((ROOT / "R6_T0_AUTHORIAL_RATIFICATION_B_PANGAEA_LIKE_LATE_TRIASSIC.json").read_text())
    assert manifest["authorial_candidate_id"] == "B_PANGAEA_LIKE_LATE_TRIASSIC_v2"
    assert manifest["authorial_status"] == "RATIFIED_FOR_T0_MATERIALIZATION"
    assert manifest["canonical_status"] == "CANDIDATE_UNTIL_MATERIALIZATION_VALIDATION"
    assert len(manifest["primitive_selections"]) == 4
    assert manifest["macrostate"]["major_low_latitude_marine_embayment"] == "OPTIONAL_SECONDARY_MORPHOLOGY"
    assert manifest["supersedes"] == "R6_T0_AUTHORIAL_RATIFICATION_ACCEPTED__GEOGRAPHY_REVISION_REQUIRED"
    assert manifest["authorization_boundary"]["dt_or_t1"] is False


def test_v2_compatibility_audit_passes_without_requiring_embayment():
    audit = json.loads((ROOT / "R6_T0_B_PANGAEA_LIKE_COMPATIBILITY_AUDIT.json").read_text())
    geo = audit["macro_geography"]
    assert 0.85 <= geo["largest_component_fraction_of_total_land"] <= 0.95
    assert geo["largest_component_equator_crossing"] is True
    assert audit["ocean_architecture"]["ocean_component_count"] == 1
    assert audit["ocean_architecture"]["inward_embayment_gate"] == "NOT_REQUIRED_BY_V2"
    assert audit["principal_decision"] == "CANONICAL_T0_GEOGRAPHY_COMPATIBLE"
    assert audit["superseded_decision"] == "R6_T0_AUTHORIAL_RATIFICATION_ACCEPTED__GEOGRAPHY_REVISION_REQUIRED"
