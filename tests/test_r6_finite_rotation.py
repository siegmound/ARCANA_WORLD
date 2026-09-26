import json
import math

import pytest

from arcana_worldsim.r6.finite_rotation import (
    rotate_points_constant_euler,
    rotate_vector_constant_euler,
)


def test_exact_quarter_turn_about_z():
    result = rotate_vector_constant_euler((1, 0, 0), (0, 0, 1), math.pi / 2)
    assert result == pytest.approx((0, 1, 0), abs=2e-15)


def test_zero_motion_and_zero_duration_are_identity():
    point = (0.25, -0.5, math.sqrt(0.6875))
    assert rotate_vector_constant_euler(point, (0, 0, 0), 9.0) == point
    assert rotate_vector_constant_euler(point, (1, 2, 3), 0.0) == point


def test_finite_rotation_preserves_spherical_norm_and_reverses():
    point = (0.3, 0.4, math.sqrt(0.75))
    omega = (1.2e-8, -2.0e-8, 0.7e-8)
    moved = rotate_vector_constant_euler(point, omega, 27123.0)
    restored = rotate_vector_constant_euler(moved, tuple(-x for x in omega), 27123.0)
    assert math.sqrt(sum(x * x for x in moved)) == pytest.approx(1.0, abs=2e-15)
    assert restored == pytest.approx(point, abs=3e-15)


def test_spherical_triangle_fixture_preserves_edge_geometry_and_orientation():
    triangle = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    omega = (1.2e-8, -2.0e-8, 0.7e-8)
    moved = rotate_points_constant_euler(triangle, omega, 27123.0)
    dot = lambda a, b: sum(x * y for x, y in zip(a, b))
    triple = lambda a, b, c: dot(a, (b[1] * c[2] - b[2] * c[1],
                                      b[2] * c[0] - b[0] * c[2],
                                      b[0] * c[1] - b[1] * c[0]))
    for i, j in ((0, 1), (1, 2), (2, 0)):
        assert dot(moved[i], moved[j]) == pytest.approx(dot(triangle[i], triangle[j]), abs=3e-15)
    assert triple(*moved) == pytest.approx(triple(*triangle), abs=3e-15)


def test_one_rotation_equals_two_half_rotations_within_roundoff():
    points = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    omega = (1.2e-8, -2.0e-8, 0.7e-8)
    full = rotate_points_constant_euler(points, omega, 27123.0)
    half = rotate_points_constant_euler(points, omega, 13561.5)
    halves = rotate_points_constant_euler(half, omega, 13561.5)
    for actual, split in zip(full, halves):
        assert actual == pytest.approx(split, abs=3e-15)


def test_synthetic_checkpoint_reload_replays_identically():
    fixture = {"points": [[1.0, 0.0, 0.0], [0.0, 0.6, 0.8]],
               "omega_rad_per_year": [1.2e-8, -2.0e-8, 0.7e-8],
               "step_years": 27123.0}
    uninterrupted = rotate_points_constant_euler(
        fixture["points"], fixture["omega_rad_per_year"], fixture["step_years"])
    checkpoint_bytes = json.dumps(fixture, sort_keys=True, separators=(",", ":")).encode()
    reloaded = json.loads(checkpoint_bytes)
    resumed = rotate_points_constant_euler(
        reloaded["points"], reloaded["omega_rad_per_year"], reloaded["step_years"])
    assert resumed == uninterrupted


@pytest.mark.parametrize("vector,omega,dt", [
    ((1, 2), (0, 0, 0), 1), ((1, 0, 0), (0, float("nan"), 0), 1),
    ((1, 0, 0), (0, 0, 1), -1), ((1, 0, 0), (0, 0, 1), float("inf")),
])
def test_invalid_rotation_inputs_fail_closed(vector, omega, dt):
    with pytest.raises(ValueError):
        rotate_vector_constant_euler(vector, omega, dt)
