from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.si1_bandwidth import (  # noqa: E402
    _edge_table,
    _ksize,
    _spherical_geometry,
    parse_shellset_feg,
    validate_runtime_package,
)


def _tiny_feg(path: Path) -> None:
    path.write_text(
        "fixture\n"
        "4 4 0 100000 T\n"
        "1 179.0 0.0 0 0\n"
        "2 -179.0 0.0 0 0\n"
        "3 179.0 1.0 0 0\n"
        "4 -179.0 1.0 0 0\n"
        "2\n"
        "1 1 2 3\n"
        "2 2 4 3\n"
        "0\n",
        encoding="ascii",
        newline="\n",
    )


def test_feg_shellset_record_framing_and_connectivity(tmp_path: Path) -> None:
    feg = tmp_path / "tiny.feg"
    _tiny_feg(feg)
    parsed = parse_shellset_feg(feg)
    assert parsed["num_nodes"] == 4
    assert parsed["num_elements"] == 2
    assert parsed["num_faults"] == 0
    assert parsed["triangles_1based"].tolist() == [[1, 2, 3], [2, 4, 3]]


def test_ksize_matches_shellset_node_and_dof_formula() -> None:
    triangles = np.array([[1, 2, 3], [2, 4, 3]], dtype=np.int64)
    edges, _ = _edge_table(triangles)
    result = _ksize(4, triangles, edges)
    assert result["maximum_node_id_difference"] == 2
    assert result["lower_node_bandwidth"] == 2
    assert result["upper_node_bandwidth"] == 2
    assert result["nLB"] == result["nUB"] == 5
    assert result["nCodiagonals"] == 5
    assert result["nRank"] == 8
    assert result["nKRows"] == 16
    assert result["matrix_bytes"] == 1024


def test_dateline_jump_is_geometric_not_topological_error(tmp_path: Path) -> None:
    feg = tmp_path / "tiny.feg"
    _tiny_feg(feg)
    parsed = parse_shellset_feg(feg)
    edges, incidence = _edge_table(parsed["triangles_1based"])
    geometry = _spherical_geometry(
        parsed["coordinates_lon_lat_deg"], parsed["triangles_1based"], edges
    )
    assert all(count == 1 or count == 2 for count in incidence.values())
    assert geometry["dateline_crossing_edge_count_by_raw_longitude_jump_gt_180_deg"] == 3
    assert geometry["edge_angular_distance_rad"]["maximum"] < np.deg2rad(3.0)


def test_runtime_package_requires_sequential_node_identity(tmp_path: Path) -> None:
    package = tmp_path / "runtime.dat"
    package.write_text("schema id 3\n1 0\n2 0\n3 0\n", encoding="ascii")
    result = validate_runtime_package(package, 3, field_count=2)
    assert result["sequential_node_identity"] is True
    package.write_text("schema id 3\n1 0\n3 0\n2 0\n", encoding="ascii")
    with pytest.raises(ValueError, match="binds node"):
        validate_runtime_package(package, 3, field_count=2)


def test_runtime_package_rejects_wrong_record_width(tmp_path: Path) -> None:
    package = tmp_path / "runtime.dat"
    package.write_text("schema id 2\n1 0\n2 0\n", encoding="ascii")
    with pytest.raises(ValueError, match="expected 3"):
        validate_runtime_package(package, 2, field_count=3)
