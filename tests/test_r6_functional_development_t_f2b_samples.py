from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "r6_functional_development_t_f2b",
    ROOT / "scripts/r6_functional_development_t_f2b.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_RUNNER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RUNNER)


def _samples(times: list[float]) -> tuple[list[dict[str, object]], dict[str, object]]:
    final: dict[str, object] = {
        "time_s": times[-1], "elapsed_years": 1.0, "width_m": 101.0,
        "crust_m": 10.0, "lithosphere_m": 20.0, "beta": 1.01,
        "accumulated_strain": 0.01, "material_coordinate": [0.0, 0.5, 1.0],
        "temperature_k": [280.0, 290.0, 300.0],
    }
    rows: list[dict[str, object]] = [
        {"time_s": value, "marker": position} for position, value in enumerate(times)
    ]
    rows[-1].update(final)
    rows[-1]["z_m"] = [0.0, 10.0, 20.0]
    return rows, final


def test_actual_runner_sample_validation_accepts_three_increasing_times():
    records, final = _samples([0.0, 0.25, 0.75])
    _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)


@pytest.mark.parametrize("times", ([0.0, 0.25, 0.25], [0.0, 0.75, 0.5]))
def test_actual_runner_sample_validation_rejects_duplicate_and_decreasing_times(times):
    records, final = _samples(list(times))
    with pytest.raises(RuntimeError, match="DIAGNOSTIC_SAMPLE_TIME_SEQUENCE_INVALID"):
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)


@pytest.mark.parametrize("records", ([], None, [{}], [None],
                                      [{"time_s": 0.0}, {"other": 1}]))
def test_actual_runner_sample_validation_rejects_empty_or_malformed_sequences(records):
    _, final = _samples([0.0, 0.5, 1.0])
    with pytest.raises(RuntimeError, match="DIAGNOSTIC_SAMPLE_TIME_SEQUENCE_INVALID"):
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)


@pytest.mark.parametrize("bad_time", (math.nan, math.inf, -math.inf, "0.5", True))
def test_actual_runner_sample_validation_rejects_nonfinite_or_nonnumeric_times(bad_time):
    records, final = _samples([0.0, 0.5, 1.0])
    records[1]["time_s"] = bad_time
    with pytest.raises(RuntimeError, match="DIAGNOSTIC_SAMPLE_TIME_SEQUENCE_INVALID"):
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)


def test_actual_runner_sample_validation_rejects_endpoint_state_mismatch():
    records, final = _samples([0.0, 0.5, 1.0])
    records[-1]["temperature_k"] = [280.0, 290.0, 301.0]
    with pytest.raises(RuntimeError, match="DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH"):
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)


def test_actual_runner_sample_validation_rejects_endpoint_depth_mismatch():
    records, final = _samples([0.0, 0.5, 1.0])
    records[-1]["z_m"] = [0.0, 10.0, 21.0]
    with pytest.raises(RuntimeError, match="DIAGNOSTIC_SAMPLE_ENDPOINT_MISMATCH"):
        _RUNNER._validate_diagnostic_sample_sequence("fixture", records, final, 0)
