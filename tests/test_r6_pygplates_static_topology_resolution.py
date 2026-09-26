"""Pure-Python contracts for the static pyGPlates topology resolution probe."""
from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

from arcana_worldsim.r6.pygplates_mapping.adapter import load_mapping_input
from arcana_worldsim.r6.pygplates_topology.adapter import ordered_boundary_sections
from arcana_worldsim.r6.pygplates_topology.contracts import governance_flags
from arcana_worldsim.r6.pygplates_topology.static_resolution import (
    PYGPLATES_DIAGNOSTIC_EPOCH,
    _base_report,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/r6_pygplates_static_topology_resolution.py"
RESOLUTION = ROOT / "src/arcana_worldsim/r6/pygplates_topology/static_resolution.py"


def test_canonical_boundary_features_are_shared_by_two_oppositely_oriented_plate_rings():
    data = load_mapping_input(ROOT)
    sections = ordered_boundary_sections(data)
    assert len(sections) == 12
    references = defaultdict(list)
    for plate_id, ring in sections.items():
        assert ring
        for ref in ring:
            references[ref["boundary_index"]].append((plate_id, ref["reverse_order"]))
    assert len(references) == 1983
    assert all(len(refs) == 2 for refs in references.values())
    assert all({flag for _, flag in refs} == {False, True} for refs in references.values())


def test_report_separates_arcana_time_from_pyGplates_solver_epoch():
    data = load_mapping_input(ROOT)
    report = _base_report(data)
    assert report["arcana_time_ma"] == 210.0
    assert report["pygplates_diagnostic_epoch"] == 0.0
    assert report["exact_curve_semantics"].startswith("UNBOUND")
    assert PYGPLATES_DIAGNOSTIC_EPOCH == 0.0


def test_governance_flags_keep_dynamics_and_canonical_state_off():
    assert all(value is False for value in governance_flags().values())


def test_resolution_source_uses_empty_rotation_model_and_single_epoch_only():
    tree = ast.parse(RESOLUTION.read_text(encoding="utf-8"))
    rotation_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Attribute)
                      and node.func.attr == "RotationModel"]
    assert len(rotation_calls) == 1
    assert len(rotation_calls[0].args) == 1
    assert isinstance(rotation_calls[0].args[0], ast.List)
    assert rotation_calls[0].args[0].elts == []
    assert "TopologicalModel" in RESOLUTION.read_text(encoding="utf-8")
    source = RESOLUTION.read_text(encoding="utf-8")
    snapshot_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Attribute)
                      and node.func.attr == "topological_snapshot"]
    assert len(snapshot_calls) == 2
    assert all(len(call.args) == 1 and isinstance(call.args[0], ast.Name)
               and call.args[0].id == "PYGPLATES_DIAGNOSTIC_EPOCH" for call in snapshot_calls)
    assert "create_total_reconstruction_sequence" not in source
    assert "get_point_velocities" not in source
    assert "get_point_strain_rates" not in source


def test_cli_imports_pygplates_lazily():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    top_level_imports = [node for node in tree.body
                         if isinstance(node, ast.Import)
                         and any(alias.name == "pygplates" for alias in node.names)]
    assert not top_level_imports
