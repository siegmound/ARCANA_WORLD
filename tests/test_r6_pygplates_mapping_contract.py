"""Pure-Python contracts for canonical mapping; no pygplates result is faked."""
from __future__ import annotations

import ast
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

from arcana_worldsim.r6.pygplates_mapping.contracts import (
    governance_flags,
    validate_mapping_inventory,
)
from arcana_worldsim.r6.pygplates_mapping.adapter import (
    _boundary_endpoints,
    load_mapping_input,
)
from arcana_worldsim.r6.pygplates_mapping.diagnostics import build_report


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "r6_pygplates_canonical_mapping.py"


def _inventory_fixture():
    faces = 64800
    edges = 1983
    arrays = {
        "face_row": np.zeros(faces, dtype=np.uint8),
        "face_col": np.zeros(faces, dtype=np.uint16),
        "face_plate_id": np.tile(np.arange(12, dtype=np.int16), faces // 12),
        "face_vertex_latlon_deg": np.zeros((faces, 5, 2), dtype=np.float64),
        "boundary_plate_a": np.zeros(edges, dtype=np.int16),
        "boundary_plate_b": np.ones(edges, dtype=np.int16),
        "boundary_edge_row": np.zeros(edges, dtype=np.uint8),
        "boundary_edge_col": np.zeros(edges, dtype=np.uint16),
        "boundary_edge_axis": np.zeros(edges, dtype=np.uint8),
        "boundary_length_m": np.ones(edges, dtype=np.float64),
    }
    census = {
        "junction_count": 20,
        "junctions": [
            {"junction_id": f"J{i}", "vertex_id": f"GRID_VERTEX:{i}:0",
             "incident_plate_ids": [0, 1, 2], "degree": 3}
            for i in range(20)
        ],
    }
    manifest = {
        "schema": "R6_T0_VECTOR_PLATE_PARTITION_V1",
        "topology": {"plate_count": 12, "positive_length_boundary_edge_count": edges},
    }
    return manifest, arrays, census


def test_inventory_contract_accepts_manifested_t0_cardinalities():
    manifest, arrays, census = _inventory_fixture()
    assert validate_mapping_inventory(manifest, arrays, census) == {
        "face_count": 64800,
        "plate_count": 12,
        "boundary_segment_count": 1983,
        "junction_count": 20,
    }


def test_inventory_contract_rejects_inconsistent_edge_data():
    manifest, arrays, census = _inventory_fixture()
    arrays["boundary_edge_row"] = arrays["boundary_edge_row"][:-1]
    with pytest.raises(ValueError, match="inconsistent lengths"):
        validate_mapping_inventory(manifest, arrays, census)


def test_canonical_partition_loads_read_only_through_r6_payload_resolver():
    data = load_mapping_input(ROOT)
    assert data.inventory == {
        "face_count": 64800,
        "plate_count": 12,
        "boundary_segment_count": 1983,
        "junction_count": 20,
    }
    assert all(not array.flags.writeable for array in data.arrays.values())


def test_grid_edge_geometry_uses_manifested_vertex_support():
    assert _boundary_endpoints(30, 40, 0) == [(-60.0, -139.0), (-59.0, -139.0)]
    assert _boundary_endpoints(30, 40, 1) == [(-59.0, -140.0), (-59.0, -139.0)]
    assert _boundary_endpoints(30, 359, 1) == [(-59.0, 179.0), (-59.0, -180.0)]


def test_governance_guards_forbid_state_or_time_changes():
    assert all(value is False for value in governance_flags().values())


def test_cli_keeps_pygplates_import_lazy_and_declares_noncanonical_output():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported = [
        node for node in tree.body
        if isinstance(node, ast.Import) and any(alias.name == "pygplates" for alias in node.names)
    ]
    assert not imported
    source = SCRIPT.read_text(encoding="utf-8")
    assert "PYGPLATES_RUNTIME_UNAVAILABLE" in source
    diagnostic = (ROOT / "src" / "arcana_worldsim" / "r6" / "pygplates_mapping" / "diagnostics.py").read_text(encoding="utf-8")
    assert "NONCANONICAL_FEASIBILITY_DIAGNOSTIC" in diagnostic


def test_unavailable_runtime_report_fails_without_claiming_mapping_success():
    manifest, arrays, census = _inventory_fixture()
    data = SimpleNamespace(
        manifest={**manifest, "time_ma": 210.0,
                  "payload": {"path": "read-only synthetic fixture", "bytes": 1, "sha256": "a" * 64}},
        arrays=arrays,
        junction_census=census,
        inventory={"face_count": 64800, "plate_count": 12,
                   "boundary_segment_count": 1983, "junction_count": 20},
    )
    report = build_report(data, None, None, "PYGPLATES_RUNTIME_UNAVAILABLE")
    assert report["status"] == "FAIL"
    assert report["mapping"]["rigid_blocks_supported"] is None
    assert report["mapping"]["deforming_region_supported"] is None
    assert report["canonical_state_changed"] is False
    assert report["forward_evolution"] is False
