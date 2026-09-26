"""Pure t0 geometry/kinematic fixtures; no physical transition is exercised."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "r6_bind_shared_boundary_topology_contact.py"
SPEC = importlib.util.spec_from_file_location("r6_shared_boundary", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize(("dv", "normal", "expected"), [
    ([2.0, 0.0, 0.0], [1.0, 0.0, 0.0], (2.0, 0.0)),
    ([-2.0, 0.0, 0.0], [1.0, 0.0, 0.0], (-2.0, 0.0)),
    ([0.0, 3.0, 0.0], [1.0, 0.0, 0.0], (0.0, 3.0)),
    ([2.0, 3.0, 0.0], [1.0, 0.0, 0.0], (2.0, 3.0)),
])
def test_relative_motion_components(dv, normal, expected):
    got = MODULE.decompose_relative_velocity(np.array(dv), np.array(normal), np.array([0.0, 1.0, 0.0]))
    assert got == pytest.approx(expected)


def test_reversing_plate_pair_preserves_opening_and_reverses_signed_slip_if_tangent_fixed():
    dv = np.array([2.0, 3.0, 0.0])
    n_ab = np.array([1.0, 0.0, 0.0])
    tangent = np.array([0.0, 1.0, 0.0])
    ab = MODULE.decompose_relative_velocity(dv, n_ab, tangent)
    # Swap A/B and use the corresponding B-to-A normal. Keep the grid tangent.
    ba = MODULE.decompose_relative_velocity(-dv, -n_ab, tangent)
    assert ba[0] == pytest.approx(ab[0])
    assert ba[1] == pytest.approx(-ab[1])


def test_reversing_boundary_parameterization_preserves_physical_components():
    dv = np.array([2.0, 3.0, 0.0])
    ab = MODULE.decompose_relative_velocity(dv, np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]))
    reversed_parameterization = MODULE.decompose_relative_velocity(dv, np.array([1.0, 0.0, 0.0]), np.array([0.0, -1.0, 0.0]))
    assert reversed_parameterization[0] == pytest.approx(ab[0])
    assert reversed_parameterization[1] == pytest.approx(-ab[1])


def test_grid_vertex_identity_wraps_dateline_and_collapses_poles():
    assert MODULE.vertex_key(45, 360) == MODULE.vertex_key(45, 0)
    assert MODULE.vertex_key(0, 17) == MODULE.vertex_key(0, 271) == "SOUTH_POLE"
    assert MODULE.vertex_key(180, 17) == MODULE.vertex_key(180, 271) == "NORTH_POLE"


def test_invalid_nonorthogonal_local_frame_rejected():
    with pytest.raises(ValueError, match="orthogonal"):
        MODULE.decompose_relative_velocity(np.ones(3), np.array([1.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
