import importlib.util
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
