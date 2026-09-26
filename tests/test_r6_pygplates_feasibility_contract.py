import importlib.util
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "arcana_worldsim" / "r6" / "pygplates_feasibility" / "spike.py"
SPEC = importlib.util.spec_from_file_location("r6_pygplates_feasibility", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_feasibility_module_is_lazy_and_noncanonical():
    import sys

    assert "pygplates" not in sys.modules
    assert MODULE.FIXTURE_ID == "R6_SYNTHETIC_DEFORMING_NETWORK_V1"
    assert MODULE.RECONSTRUCTION_TIME_MA == 5.0


def test_missing_runtime_fails_explicitly(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "pygplates":
            raise ImportError("test runtime unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    try:
        MODULE.run_spike()
    except RuntimeError as exc:
        assert str(exc) == "PYGPLATES_RUNTIME_UNAVAILABLE"
    else:
        raise AssertionError("missing pyGPlates runtime did not fail explicitly")


def test_network_sections_name_topological_geometry_type_explicitly():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "create"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "GpmlTopologicalSection"
    ]
    assert calls
    assert all(
        any(keyword.arg == "topological_geometry_type" for keyword in call.keywords)
        and len(call.args) == 1
        for call in calls
    )


def test_rotation_sequence_uses_gpml_time_samples_and_irregular_sampling():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "create_total_reconstruction_sequence"
    ]
    assert len(calls) == 1
    call = calls[0]
    assert len(call.args) == 3
    assert isinstance(call.args[0], ast.Constant) and call.args[0].value == 0
    assert isinstance(call.args[1], ast.Name) and call.args[1].id == "plate_id"
    assert isinstance(call.args[2], ast.Name) and call.args[2].id == "sampling"

    source = SCRIPT.read_text(encoding="utf-8")
    assert "pygplates.GpmlTimeSample(" in source
    assert "pygplates.GpmlFiniteRotation(" in source
    assert "pygplates.GpmlIrregularSampling(samples)" in source
    assert "[(0.0, pygplates.FiniteRotation" not in source


def test_resolved_boundary_is_used_as_polygon_and_location_classes_are_reported():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get_resolved_boundary"
    ]
    assert len(calls) == 1
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get_resolved_geometry"
        for node in ast.walk(tree)
    )

    source = SCRIPT.read_text(encoding="utf-8")
    assert "resolved_boundary.get_points()" in source
    assert "resolved_boundary.is_point_in_polygon(point)" in source
    assert "network.get_point_location(point)" in source
    assert "location.located_in_resolved_network() is not None" in source
    assert "location.located_in_resolved_network_deforming_region() is not None" in source
    assert "location.located_in_resolved_network_rigid_block() is not None" in source


def test_canonical_state_and_forward_evolution_guards_remain_false():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    guarded_values = {
        node.keys[index].value: node.values[index]
        for node in ast.walk(tree)
        if isinstance(node, ast.Dict)
        for index, key in enumerate(node.keys)
        if isinstance(key, ast.Constant)
        and key.value in {"canonical_state_changed", "forward_evolution_executed"}
    }
    assert set(guarded_values) == {"canonical_state_changed", "forward_evolution_executed"}
    assert all(isinstance(value, ast.Constant) and value.value is False for value in guarded_values.values())
