from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from arcana_worldsim.r6.hierarchical_refinement import (
    CHILD_GRID_MODEL,
    canonical_parent_order,
    refinement_request_id,
    subdivide_parent_cells,
)


def test_parent_order_and_child_geometry_follow_canonical_grid_bounds():
    parents = ("R6G1D-R015-C355", "R6G1D-R015-C354")
    cells = subdivide_parent_cells(parent_cell_ids=parents, subdivision_factor=2,
                                   request_scope="fixture:boundary-support")
    assert len(cells) == 8
    assert tuple(cell.parent_cell_id for cell in cells[:4]) == (parents[1],) * 4
    assert [(cell.child_row, cell.child_column) for cell in cells[:4]] == [
        (0, 0), (0, 1), (1, 0), (1, 1)]
    first = cells[0]
    assert (first.south_deg, first.north_deg) == (-75.0, -74.5)
    assert (first.west_deg, first.east_deg) == (174.0, 174.5)
    assert all(cell.request_id == first.request_id for cell in cells)
    assert all(cell.to_dict()["scientific_values_created"] is False for cell in cells)
    assert canonical_parent_order(parents) == ("R6G1D-R015-C354", "R6G1D-R015-C355")
    assert CHILD_GRID_MODEL == "R6_HIERARCHICAL_PARENT_CELL_SUBDIVISION_V1"


def test_longitude_seam_and_polar_bounds_inherit_parent_grid_conventions():
    cells = subdivide_parent_cells(parent_cell_ids=("R6G1D-R000-C000", "R6G1D-R179-C359"),
                                   subdivision_factor=2, request_scope="fixture:edges")
    assert (cells[0].south_deg, cells[0].north_deg,
            cells[0].west_deg, cells[0].east_deg) == (-90.0, -89.5, -180.0, -179.5)
    last_parent = cells[-1]
    assert (last_parent.south_deg, last_parent.north_deg,
            last_parent.west_deg, last_parent.east_deg) == (89.5, 90.0, 179.5, 180.0)


def test_request_and_child_identity_are_deterministic_and_request_scoped():
    args = {"parent_cell_ids": ("R6G1D-R000-C000",), "subdivision_factor": 2,
            "request_scope": "fixture:repeat"}
    first = subdivide_parent_cells(**args)
    second = subdivide_parent_cells(**args)
    other_request = subdivide_parent_cells(**{**args, "request_scope": "fixture:other"})
    assert first == second
    assert tuple(row.cell_id for row in first) != tuple(row.cell_id for row in other_request)
    assert len({row.cell_id for row in first}) == 4


@pytest.mark.parametrize("parent_ids,factor,scope", [
    ((), 2, "empty"),
    (("R6G1D-R180-C000",), 2, "bad-row"),
    (("R6G1D-R000-C360",), 2, "bad-column"),
    (("R6G1D-R000-C000",), 1, "too-coarse"),
    (("R6G1D-R000-C000",), True, "bool-is-not-an-int"),
])
def test_invalid_grid_requests_fail_closed(parent_ids, factor, scope):
    with pytest.raises(ValueError):
        subdivide_parent_cells(parent_cell_ids=parent_ids, subdivision_factor=factor,
                               request_scope=scope)


def test_request_identity_uses_canonical_parent_order():
    forward = refinement_request_id(parent_cell_ids=("R6G1D-R000-C001", "R6G1D-R000-C000"),
                                    subdivision_factor=2, request_scope="same")
    reverse = refinement_request_id(parent_cell_ids=("R6G1D-R000-C000", "R6G1D-R000-C001"),
                                    subdivision_factor=2, request_scope="same")
    assert forward == reverse


def test_frozen_contract_has_request_scoped_support_only_semantics():
    contract = json.loads((Path(__file__).resolve().parents[1] /
        "contracts/R6_HIERARCHICAL_PARENT_CELL_SUBDIVISION_V1.json").read_text(encoding="utf-8"))
    assert contract["model"] == CHILD_GRID_MODEL
    assert contract["scope"] == "EXPLICIT_REQUEST_PARENT_CELL_SET_ONLY"
    assert contract["subdivision_factor"]["global_default"] is None
    assert contract["subdivision_factor"]["minimum_integer"] == 2
    assert contract["authority_limit"]["defines_scientific_field_values"] is False
    assert contract["authority_limit"]["physical_resolution_promotion"] is False


def test_test_git_environment_only_cleans_child_environment(monkeypatch):
    from _git_test_env import isolated_git_environment

    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", "fixture-object-store")
    monkeypatch.setenv("GIT_ALTERNATE_OBJECT_DIRECTORIES", "fixture-alternates")
    child = isolated_git_environment()
    assert "GIT_OBJECT_DIRECTORY" not in child
    assert "GIT_ALTERNATE_OBJECT_DIRECTORIES" not in child
    assert os.environ["GIT_OBJECT_DIRECTORY"] == "fixture-object-store"
    assert os.environ["GIT_ALTERNATE_OBJECT_DIRECTORIES"] == "fixture-alternates"


def test_runner_status_parser_preserves_porcelain_leading_status_column():
    from scripts.r6_b6m_r1d_refinement_checkpoint_child_cells import (
        EXPECTED_WORKTREE_PATHS,
        _unrelated_worktree_paths,
    )

    allowed = sorted(EXPECTED_WORKTREE_PATHS)[:2]
    status = f" M {allowed[0]}\n?? {allowed[1]}"
    assert _unrelated_worktree_paths(status) == []
    assert _unrelated_worktree_paths(" M unrelated.py") == ["unrelated.py"]


def test_runner_compares_frozen_record_sequences_to_json_sequences():
    from scripts.r6_b6m_r1d_refinement_checkpoint_child_cells import _plain_json_value

    frozen = {"parent_cell_ids": ("cell-a", "cell-b"),
              "nested": {"child_ids": ("child-1", "child-2")}}
    request = {"parent_cell_ids": ["cell-a", "cell-b"],
               "nested": {"child_ids": ["child-1", "child-2"]}}
    assert _plain_json_value(frozen) == request
