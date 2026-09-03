from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest

from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r315_late_cenozoic_secular_biology as r315
from arcana_worldsim.scientific_engines import r316_c2_bridge_fixed_biology as r316


def bridge_clock():
    bridge = [0.2 - i * 0.0005 for i in range(161)]
    return {"age_ma": [30.0, 2.0, 0.2] + bridge[1:] + [0.0]}


class FakeAdapter:
    def __init__(self, variable=False):
        self.variable = variable
    def state_at_age(self, age):
        x = float(age) if self.variable else 2.0
        support = np.full((2, 3), 0.8 if not self.variable else 0.5 + 0.1 * float(age))
        browse = np.full((2, 3), 1.0 + 0.2 * x)
        low = np.full((2, 3), 0.5 + 0.1 * x)
        wet = np.full((2, 3), 0.25 + 0.05 * x)
        return {
            "land_support": support,
            "temperature_c": np.full((2, 3), 10.0 + x),
            "aridity_index": np.full((2, 3), 0.3 + 0.01 * x),
            "browse_forage": browse,
            "low_forage": low,
            "wetland_forage": wet,
            "total_edible_forage": browse + low + wet,
            "reference_population": np.full((6, 2, 3), 3.0 + x),
            "provider": "FAKE",
            "subprovider": "FAKE",
            "authority": "FAKE",
            "replay_safe_boundary_continuation": True,
        }


def metadata_rows(root: Path):
    data = json.loads((root / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    return data["species"] if isinstance(data, dict) and "species" in data else data


def test_config_preserves_fixed_biology_semantics():
    c = r316.R316Config()
    assert c.biology_cadence_years == 125000.0
    assert c.adaptive_clock_used_as_biology_timestep is False
    assert c.gene_flow_step_cadence_changed is False
    assert c.lifecycle_gate_cadence_changed is False
    with pytest.raises(ValueError):
        r316.R316Config(end_age_ma=0.12)


def test_exposure_partition_consumes_exactly_150_c2_500y_segments():
    p = r316.exposure_partition(bridge_clock())
    assert p["total_years"] == pytest.approx(125000.0)
    assert p["c2_bridge_segment_count"] == 150
    assert p["segment_count"] == 151
    c2 = [x for x in p["segments"] if x["domain"] == "C2_200_120KA_BRIDGE"]
    assert len(c2) == 150
    assert all(x["dt_years"] == pytest.approx(500.0) for x in c2)


def test_remainder_is_exactly_ten_500y_segments():
    r = r316.remaining_125_to_120_partition(bridge_clock())
    assert r["segment_count"] == 10
    assert r["total_years"] == pytest.approx(5000.0)
    assert r["biology_advanced"] is False


def test_constant_environment_exposure_is_exact_identity():
    avg, d = r316.effective_environment_from_exposure(FakeAdapter(variable=False), bridge_clock())
    endpoint = FakeAdapter(variable=False).state_at_age(0.125)
    for key in r316.AVERAGED_FIELDS:
        assert np.array_equal(np.asarray(avg[key]), np.asarray(endpoint[key]))
    assert np.array_equal(avg["total_edible_forage"], endpoint["total_edible_forage"])
    assert np.all(avg["accessible"])
    assert d["c2_bridge_500y_substeps_consumed"] == 150
    assert d["c2_bridge_500y_substeps_remaining_to_120ka"] == 10
    assert d["adaptive_clock_as_biology_timestep"] is False
    assert d["environmental_information_discarded_by_endpoint_only_sampling"] is False


def test_linear_exposure_uses_time_integral_not_endpoint_only():
    avg, d = r316.effective_environment_from_exposure(FakeAdapter(variable=True), bridge_clock())
    # For a linearly varying field, trapezoid integration is exact. Mean age over
    # 250->125 ka is 187.5 ka = 0.1875 Ma.
    want = 10.0 + 0.1875
    assert np.max(np.abs(avg["temperature_c"] - want)) < 1e-12
    assert d["environmental_information_discarded_by_endpoint_only_sampling"] is True
    assert d["endpoint_difference"]["temperature_c"]["max_abs_effective_vs_endpoint"] > 0.0


def test_effective_environment_total_forage_closure():
    avg, _ = r316.effective_environment_from_exposure(FakeAdapter(variable=True), bridge_clock())
    assert np.allclose(
        avg["total_edible_forage"],
        avg["browse_forage"] + avg["low_forage"] + avg["wetland_forage"],
        atol=0.0, rtol=0.0,
    )
    assert np.min(avg["land_support"]) >= 0.0
    assert np.max(avg["land_support"]) <= 1.0


def test_effective_bridge_patch_is_single_macro_boundary_only():
    avg, _ = r316.effective_environment_from_exposure(FakeAdapter(variable=False), bridge_clock())
    with r316.patched_r38_effective_bridge_environment(avg):
        got = r38.bp.environment_at(0.125, None, None)
        assert got["adaptive_clock_checkpoint_promoted_to_biology_step"] is False
        with pytest.raises(RuntimeError):
            r38.bp.environment_at(0.1245, None, None)


def test_parent_validation_fails_closed_without_r315_seal(tmp_path):
    with pytest.raises(RuntimeError):
        r316.validate_parent_r315_authority(tmp_path)


def test_constant_forcing_wrapper_does_not_change_r38_solver_result():
    root = Path(__file__).resolve().parents[1]
    jp = root / "local_runs/v0_6D1_R3_15/WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.json"
    if not jp.is_file():
        pytest.skip("R3.15 local checkpoint fixture unavailable")
    parent = r315.load_checkpoint(jp)
    a1 = np.load(root / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz", allow_pickle=False)
    md = metadata_rows(root)
    cfg = r316.R316Config()
    # Existing R3 provider endpoint state is used only as a regression fixture.
    env = r38.bp.environment_at(0.125, a1, r38.r34.barrier_cfg(cfg))
    a = r315.r313.r312.r311._clone_state(parent)
    b = r315.r313.r312.r311._clone_state(parent)
    direct, _ = r38.advance_state(a, a1, md, cfg, 0.125)
    with r316.patched_r38_effective_bridge_environment(env):
        wrapped, _ = r38.advance_state(b, a1, md, cfg, 0.125)
    cmp = r38.compare_runtime_states(direct, wrapped, atol=0.0)
    assert cmp["equivalent"] is True


def test_r316_bridge_adapter_extends_scope_without_relaxing_r315_guard():
    class FakeD3:
        def state_at_age(self, age):
            x = float(age)
            z = np.ones((2, 3), dtype=float)
            return {
                "age_ma": x,
                "land_support": z.copy(),
                "temperature_c": z.copy(),
                "aridity_index": z.copy(),
                "browse_forage": z.copy(),
                "low_forage": z.copy(),
                "wetland_forage": z.copy(),
                "total_edible_forage": 3.0*z,
                "reference_population": np.ones((6, 2, 3), dtype=float),
            }

    a = object.__new__(r316.R316C2BridgeEnvironmentAdapter)
    a.a1 = None
    a.c2 = None
    a.d3 = FakeD3()
    assert a.state_at_age(0.25)["age_ma"] == pytest.approx(0.25)
    assert a.state_at_age(0.125)["age_ma"] == pytest.approx(0.125)
    assert a.state_at_age(0.12)["age_ma"] == pytest.approx(0.12)
    with pytest.raises(ValueError):
        a.state_at_age(0.1195)
    with pytest.raises(ValueError):
        a.state_at_age(0.2505)

    # R3.15 authority remains intentionally narrower and is not modified.
    old = object.__new__(r315.R315D3EnvironmentAdapter)
    old.a1 = None
    old.c2 = None
    old.d3 = FakeD3()
    with pytest.raises(ValueError):
        old.state_at_age(0.20)


def test_runtime_a1_loader_preserves_r38_npzfile_contract(tmp_path):
    ref = tmp_path / r316.A1_RUNTIME_RELATIVE_PATH
    ref.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        ref,
        age_ma=np.asarray([30.0, 0.0]),
        lat=np.asarray([-1.0, 1.0]),
        lon=np.asarray([0.0, 2.0, 4.0]),
        population=np.zeros((2, 6, 2, 3), dtype=float),
    )
    z = r316._load_r38_runtime_a1(tmp_path)
    try:
        assert hasattr(z, "files")
        assert {"age_ma", "lat", "lon", "population"}.issubset(set(z.files))
        # This is the exact concrete operation that failed in the Windows
        # canonical run when a plain dict was passed to R3.8.
        assert "lat" in z.files
        assert np.array_equal(np.asarray(z["lat"]), np.asarray([-1.0, 1.0]))
    finally:
        z.close()
