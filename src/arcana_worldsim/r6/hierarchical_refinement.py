"""Request-scoped child-cell geometry for the governed R6 parent grid.

This module defines spatial identity and support only. It deliberately has no
field-value interpolation or scientific provider behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .identity import content_hash
from .initial_world.grid import GlobalGrid1Degree

CHILD_GRID_MODEL = "R6_HIERARCHICAL_PARENT_CELL_SUBDIVISION_V1"
PARENT_GRID_ID = "R6_GLOBAL_GEOGRAPHY_1DEG_V1"
_CELL_RE = re.compile(r"^R6G1D-R(?P<row>\d{3})-C(?P<col>\d{3})$")


@dataclass(frozen=True, slots=True)
class ChildCell:
    cell_id: str
    parent_cell_id: str
    request_id: str
    subdivision_factor: int
    child_row: int
    child_column: int
    south_deg: float
    north_deg: float
    west_deg: float
    east_deg: float

    def to_dict(self) -> dict[str, object]:
        return {
            "cell_id": self.cell_id,
            "parent_cell_id": self.parent_cell_id,
            "request_id": self.request_id,
            "subdivision_factor": self.subdivision_factor,
            "child_row": self.child_row,
            "child_column": self.child_column,
            "bounds_deg": {
                "south": self.south_deg, "north": self.north_deg,
                "west": self.west_deg, "east": self.east_deg,
            },
            "authority_class": "DERIVED_REFINEMENT_GRID_SUPPORT_ONLY",
            "scientific_values_created": False,
        }


def canonical_parent_order(cell_ids: Iterable[str]) -> tuple[str, ...]:
    """Validate and order parent cell IDs by the frozen row/column convention."""
    grid = GlobalGrid1Degree()
    indexed: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    for cell_id in cell_ids:
        match = _CELL_RE.fullmatch(cell_id)
        if match is None:
            raise ValueError(f"invalid R6 parent cell ID: {cell_id!r}")
        row, col = int(match["row"]), int(match["col"])
        if not (0 <= row < grid.nlat and 0 <= col < grid.nlon):
            raise ValueError(f"parent cell ID is outside the frozen grid: {cell_id!r}")
        if cell_id in seen:
            raise ValueError(f"duplicate parent cell ID: {cell_id!r}")
        seen.add(cell_id)
        indexed.append((row, col, cell_id))
    return tuple(item[2] for item in sorted(indexed))


def refinement_request_id(*, parent_cell_ids: Iterable[str], subdivision_factor: int,
                          request_scope: str) -> str:
    if isinstance(subdivision_factor, bool) or not isinstance(subdivision_factor, int) or subdivision_factor < 2:
        raise ValueError("subdivision_factor must be an integer >= 2")
    if not request_scope:
        raise ValueError("request_scope is required")
    body = {
        "model": CHILD_GRID_MODEL,
        "parent_grid_id": PARENT_GRID_ID,
        "parent_cell_ids": list(canonical_parent_order(parent_cell_ids)),
        "subdivision_factor": subdivision_factor,
        "request_scope": request_scope,
    }
    return "r6refinementrequest_" + content_hash(body)


def subdivide_parent_cells(*, parent_cell_ids: Iterable[str], subdivision_factor: int,
                           request_scope: str) -> tuple[ChildCell, ...]:
    """Return request-local child geometry in parent,row,column order."""
    parents = canonical_parent_order(parent_cell_ids)
    if not parents:
        raise ValueError("at least one parent cell is required")
    request_id = refinement_request_id(parent_cell_ids=parents,
        subdivision_factor=subdivision_factor, request_scope=request_scope)
    grid = GlobalGrid1Degree()
    lat = grid.lat_bounds_deg
    lon = grid.lon_bounds_deg
    result: list[ChildCell] = []
    for parent in parents:
        match = _CELL_RE.fullmatch(parent)
        assert match is not None
        row, col = int(match["row"]), int(match["col"])
        south, north = float(lat[row]), float(lat[row + 1])
        west, east = float(lon[col]), float(lon[col + 1])
        lat_step = (north - south) / subdivision_factor
        lon_step = (east - west) / subdivision_factor
        for child_row in range(subdivision_factor):
            child_south = south + child_row * lat_step
            child_north = south + (child_row + 1) * lat_step
            for child_column in range(subdivision_factor):
                child_west = west + child_column * lon_step
                child_east = west + (child_column + 1) * lon_step
                identity = {
                    "model": CHILD_GRID_MODEL,
                    "parent_cell_id": parent,
                    "subdivision_factor": subdivision_factor,
                    "child_row": child_row,
                    "child_column": child_column,
                    "request_id": request_id,
                }
                cell_id = "r6child_" + content_hash(identity)
                result.append(ChildCell(cell_id, parent, request_id,
                    subdivision_factor, child_row, child_column,
                    child_south, child_north, child_west, child_east))
    return tuple(result)
