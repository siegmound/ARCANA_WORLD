"""Pure numerical and boundary-ownership tests; no FAIR inputs or physical solve."""
import numpy as np
import pytest

from experiments.global_t0_kinematic_baseline_v1.benchmark import (
    BenchmarkError, make_plate_views, rotate_xyz, spherical_area_sr,
    shared_plate_nodes, unit_xyz, save_checkpoint,
)


def test_rotation_direct_vs_one_hundred_annual_steps():
    x = unit_xyz([[10, -80], [-20, 170], [45, 60]])
    w = np.array([1e-8, -7e-9, 2e-9])
    direct = rotate_xyz(x, w, 100)
    y = x.copy()
    for _ in range(100):
        y = rotate_xyz(y, w, 1)
    assert np.max(np.abs(y-direct)) < 2e-13
    assert np.max(np.abs(np.linalg.norm(y, axis=1)-1)) < 2e-13


def test_spherical_triangle_area_rigid_invariant():
    x = unit_xyz([[10, 20], [10, 21], [11, 21]])
    f = np.array([[0, 1, 2]])
    w = [2e-8, 4e-9, -1e-8]
    assert spherical_area_sr(x, f)[0] > 0
    assert abs(spherical_area_sr(x, f)[0]-
               spherical_area_sr(rotate_xyz(x, w, 1000), f)[0]) < 1e-14


def test_shared_source_node_keeps_distinct_plate_views():
    x = unit_xyz([[10, 20], [11, 20], [10, 21]])
    views = {i: {"ids": np.array([0, 1], dtype=int), "source_xyz": x[:2]}
             for i in range(12)}
    pairs = shared_plate_nodes(views)
    assert len(pairs) == 66
    p = rotate_xyz(x[:2], [1e-8, 0, 0], 100)
    q = rotate_xyz(x[:2], [0, 1e-8, 0], 100)
    assert np.max(np.abs(p-q)) > 1e-8
    assert np.array_equal(views[0]["source_xyz"], views[1]["source_xyz"])


def test_checkpoint_readback(tmp_path):
    v = {i: {"ids": np.array([0, 3], dtype=int)} for i in range(12)}
    xyz = {i: unit_xyz([[0, 0], [1, 2]]) for i in range(12)}
    rec, loaded = save_checkpoint(tmp_path, 50, v, xyz)
    assert rec["byte_size"] > 1000
    assert rec["sha256"]
    assert all(np.array_equal(loaded[p], xyz[p]) for p in range(12))


@pytest.mark.parametrize("omega,years", [
    ([0, 0, float("nan")], 100), ([0, 0, 1e-8], -1)
])
def test_rotation_rejects_invalid(omega, years):
    with pytest.raises(BenchmarkError, match="ROTATION_INPUT_INVALID"):
        rotate_xyz([[1, 0, 0]], omega, years)


def test_plate_local_views_preserve_shared_source_identity():
    xyz = unit_xyz([[10, 20], [10, 21], [11, 21], [11, 20]])
    faces = np.array([[1, 2, 3], [1, 3, 4]], dtype=int)
    plates = np.array([5, 8])
    views = make_plate_views(faces, plates, xyz, (5, 8))
    assert np.array_equal(views[5]["ids"], np.array([0, 1, 2]))
    assert np.array_equal(views[8]["ids"], np.array([0, 2, 3]))
    assert len(views[5]["triangles"]) == 1
    assert len(views[8]["triangles"]) == 1
    a = rotate_xyz(views[5]["source_xyz"], [0, 0, 1e-8], 100)
    b = rotate_xyz(views[8]["source_xyz"], [0, 0, -1e-8], 100)
    assert np.linalg.norm(a[0]-b[0]) > 1e-6
    assert np.array_equal(views[5]["ids"][[0, 2]], views[8]["ids"][[0, 1]])
