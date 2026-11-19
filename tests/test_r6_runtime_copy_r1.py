"""Compare the opt-in runtime copier to the untouched JSON roundtrip oracle."""
import json
import math
import random

import pytest

from arcana_worldsim.r6.regional_geological_evolution import (
    _canonical, _clone_canonical_json, _project_validated_history_free_frontier,
    advance_region, create_synthetic_region, RegionalConfig,
)


def reference(value):
    return json.loads(_canonical(value))


@pytest.mark.parametrize("value", [
    {"z": [-0.0, 1e-300, 1e300, True, None], "a": {"é": "地質"}},
    {"b": (1, 2), "a": 3}, {1: "integer-key"},
    {"mass": 10**700}, {"shared": []}, ["😀"],
])
def test_copier_matches_normalization_order_and_bytes(value):
    expected = reference(value)
    actual = _clone_canonical_json(value)
    assert _canonical(actual) == _canonical(expected)
    assert list(actual) == list(expected)
    if isinstance(actual, dict):
        assert actual is not value


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -math.inf, object(), "\ud800"])
def test_copier_preserves_invalid_value_failure(invalid):
    with pytest.raises((ValueError, TypeError, UnicodeError)) as expected:
        reference({"value": invalid})
    with pytest.raises(type(expected.value)):
        _clone_canonical_json({"value": invalid})


def test_cycle_rejected_and_shared_references_detached_per_occurrence():
    cyclic = []
    cyclic.append(cyclic)
    with pytest.raises(ValueError):
        _clone_canonical_json(cyclic)
    shared = {"nested": [1]}
    actual = _clone_canonical_json([shared, shared])
    actual[0]["nested"].append(2)
    assert actual[1] == shared == {"nested": [1]}


def test_deep_and_random_json_values_match_reference():
    rng = random.Random(71370)
    def value(depth):
        if depth == 0:
            return rng.choice([None, False, True, rng.uniform(-1e100, 1e100),
                               rng.randrange(-10**20, 10**20), "東京", "a\nb"])
        if rng.randrange(2):
            return [value(depth - 1) for _ in range(4)]
        return {key: value(depth - 1) for key in ("z", "a", "é")}
    for _ in range(30):
        row = value(4)
        assert _canonical(_clone_canonical_json(row)) == _canonical(reference(row))
    deep = []
    for _ in range(80):
        deep = [deep]
    assert _clone_canonical_json(deep) == reference(deep)


@pytest.mark.parametrize("field", ["records", "snapshots", "routing_events", "initial_condition_events"])
def test_candidate_projection_rejects_excluded_cycles(field):
    cyclic = []
    cyclic.append(cyclic)
    with pytest.raises(ValueError):
        _project_validated_history_free_frontier(
            {"cells": [], field: cyclic}, runtime_copy_optimization=True)


@pytest.mark.parametrize("field", ["records", "snapshots", "routing_events", "initial_condition_events"])
@pytest.mark.parametrize("invalid", [math.nan, math.inf, object()])
def test_candidate_projection_still_validates_excluded_history(field, invalid):
    with pytest.raises((ValueError, TypeError)):
        _project_validated_history_free_frontier(
            {"cells": [], field: [{"value": invalid}]}, runtime_copy_optimization=True)


def test_candidate_annual_snapshots_and_frontier_are_exact_and_detached():
    cfg = RegionalConfig(duration_years=10)
    state = create_synthetic_region(cfg, source_identity={"test": "runtime-r1"})
    before = _canonical(state)
    baseline = advance_region(state, years=10, config=cfg)
    candidate = advance_region(state, years=10, config=cfg, runtime_copy_optimization=True)
    assert _canonical(candidate) == _canonical(baseline)
    assert _canonical(state) == before
    frontier = _project_validated_history_free_frontier(candidate, runtime_copy_optimization=True)
    assert not {"records", "snapshots", "routing_events", "initial_condition_events"}.intersection(frontier)
    saved = _canonical(candidate)
    frontier["cells"][0]["mobile_kg_by_material"].clear()
    assert _canonical(candidate) == saved
    candidate["snapshots"][-1]["cells"][0]["elevation_m"] = -1
    assert candidate["cells"][0]["elevation_m"] != -1
