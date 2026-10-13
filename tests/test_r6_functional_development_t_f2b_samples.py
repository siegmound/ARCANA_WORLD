from __future__ import annotations

import importlib.util
import json
import math
from dataclasses import replace
from pathlib import Path

import pytest

from arcana_worldsim.r6.functional_development import NodeMaterial, ReducedState
from arcana_worldsim.r6.int0a_pipeline import SECONDS_PER_YEAR, _diagnostic_sample_record


ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "r6_functional_development_t_f2b",
    ROOT / "scripts/r6_functional_development_t_f2b.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_RUNNER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RUNNER)


def _state(time_s: float = SECONDS_PER_YEAR) -> ReducedState:
    material = NodeMaterial("fixture-crust", 2.5, 2800.0, 900.0, 0.0)
    return ReducedState(
        time_s=time_s, initial_width_m=100.0, width_m=101.0,
        initial_crust_m=10.0, initial_lithosphere_m=20.0,
        crust_m=10.0, lithosphere_m=20.0, beta=1.01,
        accumulated_strain=0.01, crust_fraction=0.5,
        material_coordinate=(0.0, 0.5, 1.0),
        temperature_k=(280.0, 290.0, 300.0), materials=(material, material, material),
        surface_temperature_k=280.0, base_temperature_k=300.0,
    )


def _samples(times: list[float]) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows = [_diagnostic_sample_record("fixture", _state(value),
                                      complete_state=index == len(times) - 1)
            for index, value in enumerate(times)]
    return rows, _state(times[-1]).payload()


def test_actual_runner_accepts_payload_from_same_reduced_state_and_reproduces_old_failure():
    state = _state()
    final = state.payload()
    endpoint = _diagnostic_sample_record("fixture", state, complete_state=True)

    # The old validator required this derived field in ReducedState.payload(),
    # where it never existed. This reproduces the prior schema mismatch.
    assert "elapsed_years" not in final
    assert endpoint["elapsed_years"] == state.time_s / SECONDS_PER_YEAR
    old_fields = ("time_s", "elapsed_years", "width_m", "crust_m", "lithosphere_m",
                  "beta", "accumulated_strain", "material_coordinate", "temperature_k")
    first_old_mismatch = next(
        field for field in old_fields
        if field not in endpoint or field not in final or endpoint[field] != final[field]
    )
    assert first_old_mismatch == "elapsed_years"

    _RUNNER._validate_diagnostic_sample_sequence(
        "fixture", [_diagnostic_sample_record("fixture", _state(0.0)), endpoint], final, 0)


def test_actual_runner_sample_validation_accepts_three_increasing_times():
    records, final = _samples([0.0, 0.25 * SECONDS_PER_YEAR, SECONDS_PER_YEAR])
    _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)


@pytest.mark.parametrize("times", (
    [0.0, 0.25 * SECONDS_PER_YEAR, 0.25 * SECONDS_PER_YEAR],
    [0.0, 0.75 * SECONDS_PER_YEAR, 0.5 * SECONDS_PER_YEAR],
))
def test_actual_runner_rejects_duplicate_and_decreasing_times(times):
    records, final = _samples(times)
    with pytest.raises(RuntimeError, match="DIAGNOSTIC_SAMPLE_TIME_SEQUENCE_INVALID"):
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)


@pytest.mark.parametrize("records", ([], None, [{}], [None], [{"time_s": 0.0}]))
def test_actual_runner_rejects_empty_or_malformed_sequences(records):
    _, final = _samples([0.0, 0.5 * SECONDS_PER_YEAR, SECONDS_PER_YEAR])
    with pytest.raises(RuntimeError):
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)


@pytest.mark.parametrize("bad_time", (math.nan, math.inf, -math.inf, "0.5", True))
def test_actual_runner_rejects_nonfinite_or_nonnumeric_times(bad_time):
    records, final = _samples([0.0, 0.5 * SECONDS_PER_YEAR, SECONDS_PER_YEAR])
    records[1]["time_s"] = bad_time
    with pytest.raises(RuntimeError, match="DIAGNOSTIC_SAMPLE_TIME_SEQUENCE_INVALID"):
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)


def test_actual_runner_rejects_wrong_support_and_array_cardinality():
    records, final = _samples([0.0, 0.5 * SECONDS_PER_YEAR, SECONDS_PER_YEAR])
    records[1]["support_id"] = "other-support"
    with pytest.raises(RuntimeError, match="DIAGNOSTIC_SAMPLE_SUPPORT_ID_INVALID"):
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)
    records, final = _samples([0.0, 0.5 * SECONDS_PER_YEAR, SECONDS_PER_YEAR])
    records[-1]["temperature_k"] = [280.0, 290.0]
    with pytest.raises(RuntimeError, match="DIAGNOSTIC_SAMPLE_ARRAY_CARDINALITY_INVALID"):
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)


@pytest.mark.parametrize("field", (
    "time_s", "initial_width_m", "width_m", "initial_crust_m", "initial_lithosphere_m",
    "crust_m", "lithosphere_m", "beta", "accumulated_strain", "area_m2",
    "crust_fraction", "material_coordinate", "z_m", "temperature_k", "materials",
    "surface_temperature_k", "base_temperature_k",
))
def test_actual_runner_rejects_each_governed_endpoint_state_field(field):
    records, final = _samples([0.0, 0.5 * SECONDS_PER_YEAR, SECONDS_PER_YEAR])
    observed = records[-1][field]
    if isinstance(observed, list):
        changed = list(observed)
        changed[0] = {"changed": True} if field == "materials" else 999.0
    elif isinstance(observed, (int, float)):
        changed = observed + 1.0
    else:
        changed = "altered"
    records[-1][field] = changed
    if field == "time_s":
        records[-1]["elapsed_years"] = changed / SECONDS_PER_YEAR
    elif field == "lithosphere_m":
        records[-1]["z_m"] = [x * changed for x in records[-1]["material_coordinate"]]
    elif field == "material_coordinate":
        records[-1]["z_m"] = [x * records[-1]["lithosphere_m"] for x in changed]
    with pytest.raises(_RUNNER.DiagnosticSampleValidationError) as caught:
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)
    assert caught.value.field == field


def test_actual_runner_rejects_derived_elapsed_and_depth_mismatches():
    records, final = _samples([0.0, 0.5 * SECONDS_PER_YEAR, SECONDS_PER_YEAR])
    records[-1]["elapsed_years"] = 1.0000000000000002
    with pytest.raises(_RUNNER.DiagnosticSampleValidationError) as caught:
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)
    assert caught.value.field == "elapsed_years"
    records, final = _samples([0.0, 0.5 * SECONDS_PER_YEAR, SECONDS_PER_YEAR])
    records[-1]["z_m"] = [0.0, 10.0, 21.0]
    with pytest.raises(_RUNNER.DiagnosticSampleValidationError) as caught:
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)
    assert caught.value.field == "z_m"


def test_actual_runner_rejects_final_state_from_another_resolution():
    records, _ = _samples([0.0, 0.5 * SECONDS_PER_YEAR, SECONDS_PER_YEAR])
    other_resolution = replace(_state(), temperature_k=(280.0, 290.0, 301.0))
    with pytest.raises(_RUNNER.DiagnosticSampleValidationError) as caught:
        _RUNNER._validate_diagnostic_sample_sequence(
            "fixture", records, other_resolution.payload(), 0)
    assert caught.value.field == "temperature_k"


def test_failure_diagnostic_is_explicit_nontrajectory_and_contains_numeric_identity():
    records, final = _samples([0.0, 0.5 * SECONDS_PER_YEAR, SECONDS_PER_YEAR])
    records[-1]["width_m"] += 0.25
    with pytest.raises(_RUNNER.DiagnosticSampleValidationError) as caught:
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)
    diagnostic = caught.value.diagnostic_record(
        source_identity={"head": "synthetic"}, configuration_identity={"resolution": "fixture"},
        exit_code=1, stop_classification="NATURAL_EXIT_NONZERO")
    assert diagnostic["classification"] == "NONCANONICAL_FAILURE_DIAGNOSTIC_NOT_TRAJECTORY"
    assert diagnostic["support_id"] == "fixture"
    assert diagnostic["validation_phase"] == "ENDPOINT"
    assert diagnostic["first_mismatching_field"] == "width_m"
    assert diagnostic["expected"]["float_hex"] != diagnostic["observed"]["float_hex"]
    assert diagnostic["difference"]["absolute_difference"] == 0.25
    assert diagnostic["difference"]["relative_difference_to_expected"] > 0.0
    assert diagnostic["exit_code"] == 1


def test_failure_diagnostic_summarizes_nonfinite_values_as_strict_json():
    failure = _RUNNER.DiagnosticSampleValidationError(
        "fixture", 0, "temperature_k", math.nan, math.inf)
    record = failure.diagnostic_record(exit_code=1, stop_classification="NATURAL_EXIT_NONZERO")
    encoded = json.dumps(record, allow_nan=False)
    assert '"finite": false' in encoded
    assert record["difference"]["status"] == "NONFINITE"
