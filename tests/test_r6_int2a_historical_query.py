from __future__ import annotations

import json
from pathlib import Path

import pytest

from r6_int2a_historical_query import (
    AuditError,
    _validate_int1d_provenance,
    build_analysis,
    inspect_interval,
    load_sources,
    _reject_output_overlap,
    physical_refinement_request,
    query,
    write_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
R4 = ROOT / "outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04"
INT1D = ROOT / "outputs/r6_functional_development/INT1D_TF2B_5_11_R094C025_C026_20261014_02"


@pytest.fixture(scope="module")
def sources():
    return load_sources(R4, INT1D)


def _tiny_source():
    rows = []
    for i, t in enumerate((0.0, 2.0, 5.0)):
        rows.append({"elapsed_years": t, "record_type": "DIAGNOSTIC_SAMPLE" if i < 2 else "ENDPOINT_STATE",
                     "support_id": "S", "width_m": 10.0 + 2.0 * t, "crust_m": 3.0,
                     "lithosphere_m": 20.0, "beta": 1.0, "accumulated_strain": 0.0,
                     "temperature_k": [100.0 + t, 200.0 + 2.0 * t],
                     "z_m": [0.0, 20.0], "material_coordinate": [0.0, 1.0]})
    return {"experiment": "SYNTHETIC_TEST", "source_commit": "TEST_ONLY", "source_identity_sha256": "UNKNOWN",
            "manifest_sha256": "TEST_ONLY", "run_result_sha256": "TEST_ONLY", "sample_artifact_sha256": "TEST_ONLY",
            "boundary_id": "TEST_ONLY", "resolution_fraction": 0.5, "sampling": "TEST_ONLY",
            "rows": {"S": rows}, "supports": ["S"]}


def test_actual_r4_and_int1d_bundles_are_pinned_and_reconciled(sources):
    assert sources["R4"]["manifest_sha256"] == "191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236"
    assert sources["INT1D"]["manifest_sha256"] == "0cf3faedc6984bed7f479312a2038385ec03040c2fead5cee5b150def39bc571"
    assert [len(sources[x]["rows"][sources[x]["supports"][0]]) for x in ("R4", "INT1D")] == [4, 9]
    assert sources["R4"]["source_commit"] == "91fc83d50ec15d8bb9b826926ac2f2dc859281e8"
    assert sources["INT1D"]["source_commit"] == "3fa149b7639f59c934a4d722acb388eacc4c9628"


def test_exact_hit_rejects_nonexact_and_unknown_inputs(sources):
    src = sources["R4"]
    sup = src["supports"][0]
    t = src["rows"][sup][1]["elapsed_years"]
    answer = query(src, support_id=sup, elapsed_years=t, field="width_m", mode="EXACT_OBSERVED")
    assert answer["observed"] is True and answer["value"] == src["rows"][sup][1]["width_m"]
    assert answer["source_manifest_sha256"] == src["manifest_sha256"]
    with pytest.raises(AuditError, match="EXACT_OBSERVATION_NOT_FOUND"):
        query(src, support_id=sup, elapsed_years=t + 1e-8, field="width_m", mode="EXACT_OBSERVED")
    with pytest.raises(AuditError, match="UNKNOWN_SUPPORT"):
        query(src, support_id="MISSING", elapsed_years=t, field="width_m", mode="EXACT_OBSERVED")
    with pytest.raises(AuditError, match="UNSUPPORTED_NUMERIC_FIELD"):
        query(src, support_id=sup, elapsed_years=t, field="materials", mode="EXACT_OBSERVED")


def test_bracket_and_reconstruction_use_irregular_observed_times():
    src = _tiny_source()
    bracket = query(src, support_id="S", elapsed_years=3.0, field="width_m", mode="BRACKET")
    assert bracket["left"]["elapsed_years"] == 2.0
    assert bracket["right"]["elapsed_years"] == 5.0
    assert bracket["left"]["value"] == 14.0 and bracket["right"]["value"] == 20.0
    reconstructed = query(src, support_id="S", elapsed_years=3.0,
                           field="width_m", mode="DIAGNOSTIC_RECONSTRUCTION")
    assert reconstructed["observed"] is False and reconstructed["value"] == 16.0
    assert reconstructed["interpolation_method"] == "PIECEWISE_LINEAR_TIME"
    with pytest.raises(AuditError, match="TIME_IS_OBSERVED"):
        query(src, support_id="S", elapsed_years=2.0, field="width_m", mode="BRACKET")


def test_profile_reconstruction_is_same_index_and_material_coordinates():
    src = _tiny_source()
    answer = query(src, support_id="S", elapsed_years=3.0,
                   field="temperature_k", mode="DIAGNOSTIC_RECONSTRUCTION")
    assert answer["value"] == [103.0, 206.0]
    assert answer["material_coordinate"] == [0.0, 1.0]
    assert answer["canonical_state"] is False
    src["rows"]["S"][2]["material_coordinate"] = [0.0, 0.9]
    with pytest.raises(AuditError, match="MATERIAL_COORDINATE_SUPPORT_MISMATCH"):
        query(src, support_id="S", elapsed_years=3.0,
              field="temperature_k", mode="DIAGNOSTIC_RECONSTRUCTION")


@pytest.mark.parametrize("time", [float("nan"), float("inf"), -1.0, 6.0])
def test_nonfinite_negative_and_out_of_range_rejected(time):
    with pytest.raises(AuditError):
        query(_tiny_source(), support_id="S", elapsed_years=time,
              field="width_m", mode="EXACT_OBSERVED")


def test_material_coordinate_is_observed_only_and_interval_is_retrieval():
    src = _tiny_source()
    with pytest.raises(AuditError, match="FIELD_NOT_RECONSTRUCTABLE"):
        query(src, support_id="S", elapsed_years=3.0,
              field="material_coordinate", mode="DIAGNOSTIC_RECONSTRUCTION")
    interval = inspect_interval(src, support_id="S", start_years=1.0, end_years=4.0)
    assert [x["elapsed_years"] for x in interval["observations"]] == [2.0]
    assert interval["physical_computation_performed"] is False


def test_physical_refinement_returns_blockers_without_computation():
    result = physical_refinement_request(_tiny_source(), support_id="S", requested_years=2.0)
    assert result["status"] == "PHYSICAL_REFINEMENT_NOT_EXECUTED"
    assert result["resolution_or_step_size"] == "UNKNOWN_NOT_SELECTED"
    assert "SEPARATE_EXECUTION_AUTHORIZATION" in result["missing_dependencies"]
    assert result["physical_computation_performed"] is False


def test_int1d_provenance_tampering_fails_closed(sources):
    docs = dict(sources["INT1D"]["documents"])
    docs["RUN_RESULT.json"] = dict(docs["RUN_RESULT.json"], checkpoint_commit="0" * 40)
    with pytest.raises(AuditError, match="INT1D_RUN_PROVENANCE_MISMATCH"):
        _validate_int1d_provenance(docs)
    docs = dict(sources["INT1D"]["documents"])
    tampered = dict(docs["DIAGNOSTIC_NUMERICAL_SAMPLES.json"])
    tampered["selected_boundary_id"] = "R6BND-TAMPERED"
    docs["DIAGNOSTIC_NUMERICAL_SAMPLES.json"] = tampered
    with pytest.raises(AuditError, match="INT1D_SAMPLE_IDENTITY_MISMATCH"):
        _validate_int1d_provenance(docs)


def test_missing_bundle_path_rejected():
    with pytest.raises(AuditError):
        load_sources(R4 / "missing", INT1D)


def test_output_may_not_overlap_immutable_source_bundles(tmp_path):
    with pytest.raises(AuditError, match="OUTPUT_INPUT_PATH_OVERLAP"):
        _reject_output_overlap(R4 / "new-child", R4)
    with pytest.raises(AuditError, match="OUTPUT_INPUT_PATH_OVERLAP"):
        _reject_output_overlap(tmp_path, tmp_path.parent)


def test_analysis_output_manifest_sidecar_and_readback_are_deterministic(tmp_path, sources):
    result = build_analysis(R4, INT1D)
    first = tmp_path / "one"
    second = tmp_path / "two"
    identity_one = write_bundle(first, result)
    identity_two = write_bundle(second, result)
    assert identity_one == identity_two
    bytes_one = (first / "INT2A_QUERY_RESULTS.json").read_bytes()
    assert bytes_one == (second / "INT2A_QUERY_RESULTS.json").read_bytes()
    manifest = json.loads((first / "INT2A_OUTPUT_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["files"]["INT2A_QUERY_RESULTS.json"]["sha256"] == identity_one["result_sha256"]
    assert (first / "INT2A_OUTPUT_MANIFEST.json.sha256").read_text().split()[0] == identity_one["manifest_sha256"]
    assert result["decision"] == "INT2A_OFFLINE_HISTORICAL_QUERY_RECONSTRUCTION_EVIDENCED__B0_EXECUTABLE_BINDING_NOT_QUALIFIED"
    with pytest.raises(AuditError, match="OUTPUT_DIRECTORY_ALREADY_EXISTS"):
        write_bundle(first, result)


def test_analysis_reports_temporal_inspection_physical_request_and_retention(sources):
    result = build_analysis(R4, INT1D)
    assert "int1d_temporal_inspection_200_to_400" in result["query_examples"]
    assert "int1d_physical_refinement_request" in result["query_examples"]
    assert result["query_examples"]["int1d_physical_refinement_request"]["physical_computation_performed"] is False
    for key in ("R4", "INT1D"):
        retention = result["retention_and_answerability"][key]
        assert retention["support_series_identical_within_experiment"] is True
        assert retention["strategies"][0]["exact_answerable_count"] == retention["strategies"][0]["observed_sample_count"]
        assert retention["strategies"][1]["bracket_answerable_omitted_count"] == retention["strategies"][1]["omitted_sample_count"]
