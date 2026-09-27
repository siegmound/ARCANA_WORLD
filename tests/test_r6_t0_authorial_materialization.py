import json
from pathlib import Path

from arcana_worldsim.r6.t0_materialization import build_artifacts, render_markdown

ROOT = Path(__file__).resolve().parents[1]


def test_preflight_preserves_null_authorial_choices_and_blocks_fake_outputs():
    candidates, report = build_artifacts(ROOT)
    assert len(candidates["candidate_envelopes"][0]["primitive_selections"]) == 4
    assert candidates["candidate_realizations"] == []
    assert all(row["selected_value"] is None
               for row in candidates["candidate_envelopes"][0]["primitive_selections"])
    assert report["principal_decision"] == "R6_T0_MATERIALIZATION_PARTIAL__AUTHORIAL_VALUES_REQUIRED"
    assert report["materialized_fields"]["new_physical_field_families"] == 0
    assert report["PRE_ORBDATA_outputs"]["fegs_generated"] == 0
    assert report["SHELLS_READY_outputs"]["fegs_generated"] == 0
    assert report["governance"]["canonical_state_changed"] is False


def test_preflight_reports_parent_counts_parameter_families_and_mesh_hash():
    _, report = build_artifacts(ROOT)
    assert report["authorial_candidate_set"]["authorial_primitive_families"] == 4
    assert report["scientific_uncertainty_axes"]["count"] == 5
    assert report["reference_parameter_candidates"]["reference_physical_parameter_families"] == 11
    assert report["reference_parameter_candidates"]["reference_parameters_resolved"] == 2
    assert report["rheology_configuration_set"]["rheology_parameter_families"] == 13
    assert report["parent_state"]["numerical_mesh_sha256"] == (
        "6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad")
    assert report["parent_state"]["boundary_segments"] == 1_983


def test_preflight_report_is_deterministic_and_markdown_has_decision():
    first_candidate, first_report = build_artifacts(ROOT)
    second_candidate, second_report = build_artifacts(ROOT)
    assert json.dumps(first_candidate, sort_keys=True) == json.dumps(second_candidate, sort_keys=True)
    assert json.dumps(first_report, sort_keys=True) == json.dumps(second_report, sort_keys=True)
    assert first_report["replay_validation"]["same_inputs_same_artifact"] is True
    assert first_report["replay_validation"]["scientific_materialization_replayed"] is False
    assert first_report["principal_decision"] in render_markdown(first_report)
