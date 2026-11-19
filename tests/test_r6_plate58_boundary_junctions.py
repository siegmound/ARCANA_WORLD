"""Source Euler exit compatibility; no solver or FAIR state mutation."""
import pytest

from experiments.plate58_deforming_explore_v1.boundary_junctions import (
    compare_euler_at_one_node, NUMERICAL_IDENTITY_TOL_M_YEAR,
)


def test_two_distinct_plate_euler_vectors_cannot_prescribe_one_node():
    result = compare_euler_at_one_node([0.0, 0.0], [0.0, 5e-9])
    assert result["relative_euler_speed_m_per_year"] == pytest.approx(0.157788)
    assert not result["dual_euler_dirichlet_at_single_node_compatible"]


def test_identical_vectors_are_only_kinematically_compatible():
    result = compare_euler_at_one_node([1e-9, 2e-9], [1e-9, 2e-9])
    assert result["relative_euler_speed_m_per_year"] == 0.0
    assert result["dual_euler_dirichlet_at_single_node_compatible"]


@pytest.mark.parametrize("bad", [[1.0], [float("nan"), 0.0], [float("inf"), 0.0]])
def test_invalid_velocity_rejected(bad):
    with pytest.raises(ValueError, match="INVALID_PLATE_EULER_VELOCITY"):
        compare_euler_at_one_node([0.0, 0.0], bad)


def test_numerical_tolerance_is_not_a_geological_parameter():
    assert NUMERICAL_IDENTITY_TOL_M_YEAR < 1.0e-7
