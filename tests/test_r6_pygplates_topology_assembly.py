"""Pure-Python governance and source contracts for P2.2."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from arcana_worldsim.r6.pygplates_topology.contracts import (
    governance_flags,
    validate_topology_input,
)
from arcana_worldsim.r6.pygplates_topology.diagnostics import runtime_unavailable_report
from arcana_worldsim.r6.pygplates_mapping.adapter import load_mapping_input
from arcana_worldsim.r6.pygplates_topology.adapter import _plate_boundary_rings

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "src/arcana_worldsim/r6/pygplates_topology/adapter.py"
SCRIPT = ROOT / "scripts/r6_pygplates_topology_assembly.py"


def _data():
    census = {"junctions": [
        {"junction_id": f"J{i:02d}", "vertex_id": f"GRID_VERTEX:{i}:0",
         "incident_plate_ids": [0, 1, 2], "degree": 3}
        for i in range(20)
    ]}
    return SimpleNamespace(
        inventory={"plate_count": 12, "face_count": 64800,
                   "boundary_segment_count": 1983, "junction_count": 20},
        junction_census=census,
        manifest={"payload": {"sha256": "a" * 64}},
        arrays={
            "face_row": [0] * 64800,
            "face_col": list(range(64800)),
            "face_plate_id": [index % 12 for index in range(64800)],
            "boundary_edge_row": [0] * 1983,
            "boundary_edge_col": list(range(1983)),
            "boundary_edge_axis": [0] * 1983,
            "boundary_plate_a": [0] * 1983,
            "boundary_plate_b": [1] * 1983,
        },
    )


def test_inventory_and_degree_three_junction_contract():
    assert validate_topology_input(_data()) == {
        "plate_count": 12, "face_count": 64800,
        "boundary_segment_count": 1983, "junction_count": 20,
    }


def test_contract_rejects_wrong_junction_degree():
    data = _data()
    data.junction_census["junctions"][0]["degree"] = 4
    with pytest.raises(ValueError, match="non-degree-3"):
        validate_topology_input(data)


def test_canonical_partition_traces_to_twelve_closed_plate_rings():
    data = load_mapping_input(ROOT)
    rings = _plate_boundary_rings(data)
    assert len(rings) == 12
    assert all(len(plate_rings) == 1 for plate_rings in rings.values())
    assert all(ring[0] == ring[-1] for plate_rings in rings.values() for ring in plate_rings)


def test_governance_guards_forbid_physical_or_canonical_changes():
    assert all(value is False for value in governance_flags().values())


def test_network_section_uses_explicit_network_type_and_no_motion_assignment():
    tree = ast.parse(ADAPTER.read_text(encoding="utf-8"))
    creates = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
               and isinstance(node.func, ast.Attribute)
               and node.func.attr == "create"
               and isinstance(node.func.value, ast.Attribute)
               and node.func.value.attr == "GpmlTopologicalSection"]
    assert len(creates) == 1
    assert any(keyword.arg == "topological_geometry_type" for keyword in creates[0].keywords)
    adapter_source = ADAPTER.read_text(encoding="utf-8")
    assert "set_reconstruction_plate_id" not in adapter_source
    assert "create_total_reconstruction_sequence" not in adapter_source


def test_cli_imports_runtime_lazily_and_unavailable_is_failure():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    top_level_pygplates_imports = [
        node for node in tree.body
        if isinstance(node, ast.Import) and any(alias.name == "pygplates" for alias in node.names)
    ]
    assert not top_level_pygplates_imports
    report = runtime_unavailable_report(_data(), "PYGPLATES_RUNTIME_UNAVAILABLE")
    assert report["status"] == "FAIL"
    assert report["decision"] == "PYGPLATES_RUNTIME_UNAVAILABLE"
    assert report["network_created"] is False
