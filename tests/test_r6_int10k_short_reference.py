from __future__ import annotations

from dataclasses import replace
import pytest

from arcana_worldsim.r6.functional_development import NodeMaterial, ReducedState
from arcana_worldsim.r6.geological_surface_microdomain import SUPPORTS
from arcana_worldsim.r6.int10k_short_reference import (
    ShortReferenceConfig, ShortReferenceError, _validate_regional_coverage,
    compare_reference, run_short_reference,
)
from arcana_worldsim.r6.regional_geological_evolution import RegionalConfig


def _states():
    materials = tuple(NodeMaterial(
        role_id="CONTINENTAL_CRUST_REFERENCE" if i < 25 else "LITHOSPHERIC_MANTLE_REFERENCE",
        k_w_m_k=3.0 if i < 25 else 4.0,
        rho_kg_m3=2800.0 if i < 25 else 3300.0,
        cp_j_kg_k=1000.0,
        radiogenic_w_m3=1e-6 if i < 25 else 2e-8)
        for i in range(73))
    z = tuple(i / 72 for i in range(73))
    temperatures = tuple(280.0 + 1200.0 * x for x in z)
    base = ReducedState(0.0, 100_000.0, 100_000.0, 35_000.0,
                        100_000.0, 35_000.0, 100_000.0, 1.0, 0.0, 0.35,
                        z, temperatures, materials, 280.0, 1480.0)
    return {SUPPORTS[0]: base,
            SUPPORTS[1]: replace(base, width_m=101_000.0,
                                 initial_width_m=101_000.0)}


def _identity():
    return {
        "source_result_sha256": "a" * 64,
        "t0_boundary_id": "SYNTHETIC_T0_EDGE",
        "t0_boundary_length_m": 111_194.92664455874,
        "support_cells": [
            {"support_id": SUPPORTS[0], "grid_cell": [91, 28], "plate_id": 11},
            {"support_id": SUPPORTS[1], "grid_cell": [91, 29], "plate_id": 5},
        ],
    }


@pytest.mark.parametrize("years,split", [(3, 1), (10, 5)])
def test_reference_direct_equals_checkpoint_split(years, split):
    out = run_short_reference(_states(), _identity(),
                              config=ShortReferenceConfig(years, split))
    assert out["status"] == "PASS_SHORT_REFERENCE_IN_MEMORY_PARITY"
    assert out["direct"]["regional_state"]["time_years"] == years
    for trajectory in (out["direct"], out["split"]):
        state = trajectory["regional_state"]
        assert [row["time_year"] for row in state["records"]] == list(range(1, years + 1))
        assert [row["time_year"] for row in state["snapshots"]] == list(range(0, years + 1))


def test_regional_coverage_accepts_records_and_snapshots_with_initial_state():
    state = {
        "time_years": 3,
        "records": [{"time_year": year} for year in (1, 2, 3)],
        "snapshots": [{"time_year": year} for year in (0, 1, 2, 3)],
    }
    _validate_regional_coverage(state, 3)


@pytest.mark.parametrize("field,years", [
    ("records", [1, 3]),                  # missing annual record
    ("records", [1, 2, 2, 3]),            # duplicate annual record
    ("records", [2, 1, 3]),               # out-of-order annual record
    ("snapshots", [1, 2, 3]),             # missing year-zero initial snapshot
    ("snapshots", [0, 1, 1, 2, 3]),       # duplicate snapshot
    ("snapshots", [0, 2, 1, 3]),           # out-of-order snapshot
])
def test_regional_coverage_rejects_missing_duplicate_or_out_of_order_years(field, years):
    state = {
        "time_years": 3,
        "records": [{"time_year": year} for year in (1, 2, 3)],
        "snapshots": [{"time_year": year} for year in (0, 1, 2, 3)],
    }
    state[field] = [{"time_year": year} for year in years]
    with pytest.raises(ShortReferenceError, match="SHORT_REFERENCE_COVERAGE_INVALID"):
        _validate_regional_coverage(state, 3)


@pytest.mark.parametrize("time_years", [2, 4])
def test_regional_coverage_rejects_wrong_terminal_year(time_years):
    state = {
        "time_years": time_years,
        "records": [{"time_year": year} for year in (1, 2, 3)],
        "snapshots": [{"time_year": year} for year in (0, 1, 2, 3)],
    }
    with pytest.raises(ShortReferenceError, match="SHORT_REFERENCE_COVERAGE_INVALID"):
        _validate_regional_coverage(state, 3)


@pytest.mark.parametrize("years,split", [(2, 1), (11, 1), (3, 0), (3, 3)])
def test_invalid_plan_fails_closed(years, split):
    with pytest.raises(ShortReferenceError):
        ShortReferenceConfig(years, split).validate()


def test_plan_drift_fails_closed():
    with pytest.raises(ShortReferenceError, match="PLANNED_DURATION_MISMATCH"):
        run_short_reference(_states(), _identity(),
                            config=ShortReferenceConfig(3, 1),
                            regional_config=RegionalConfig(duration_years=10))


def test_numeric_event_schema_and_finite_fail_closed():
    with pytest.raises(ShortReferenceError, match="NONFINITE"):
        compare_reference([float("nan")], [float("nan")])
    with pytest.raises(ShortReferenceError, match="REFERENCE_MISMATCH"):
        compare_reference({"events": ["a"]}, {"events": ["b"]})
    with pytest.raises(ShortReferenceError, match="REFERENCE_KEY_MISMATCH"):
        compare_reference({"a": 1}, {"b": 1})
    with pytest.raises(ShortReferenceError, match="REFERENCE_NUMERIC_MISMATCH"):
        compare_reference({"temperature_k": 400.0}, {"temperature_k": 401.0})
