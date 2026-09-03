from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
import numpy as np
import pytest

from arcana_worldsim.scientific_engines import r317_recent_restart_sync as r317


def clock_125_120():
    # Full clock is unnecessary for the partition helper; include exact 500-y nodes.
    return {"age_ma": [0.125 - i * 0.0005 for i in range(11)]}


class FakeAdapter:
    def __init__(self, *_args, variable: bool = True, support_loss: bool = False, **_kwargs):
        self.variable = variable
        self.support_loss = support_loss

    def state_at_age(self, age):
        age = float(age)
        x = age if self.variable else 0.123
        support = np.ones((2, 3), dtype=float)
        if self.support_loss and age <= 0.120 + 1e-12:
            support[0, 0] = 0.0
        browse = np.full((2, 3), 1.0 + x)
        low = np.full((2, 3), 0.5 + 0.5 * x)
        wet = np.full((2, 3), 0.25 + 0.25 * x)
        return {
            "age_ma": age,
            "land_support": support,
            "accessible": support > 1e-9,
            "temperature_c": np.full((2, 3), 10.0 + x),
            "aridity_index": np.full((2, 3), 0.3 + 0.01 * x),
            "browse_forage": browse,
            "low_forage": low,
            "wetland_forage": wet,
            "total_edible_forage": browse + low + wet,
            "reference_population": np.full((6, 2, 3), 3.0 + x),
            "provider": "FAKE_C2",
            "subprovider": "EXACT_v0.6.1_120KA_ENDPOINT" if abs(age-0.12) < 1e-12 else "FAKE_BRIDGE",
            "authority": "v0.6.1 SEALED_PALEOCLIMATE_HISTORY" if abs(age-0.12) < 1e-12 else "FAKE",
            "restart_boundary_at_120ka": abs(age-0.12) < 1e-12,
            "replay_safe_boundary_continuation": True,
            "pre120ka_historical_glacial_chronology_claimed": False,
        }


def test_config_forbids_partial_biology_and_cadence_changes():
    c = r317.R317Config()
    assert c.advance_biology is False
    assert c.biology_cadence_years == 125000.0
    assert c.transport_cadence_years == 62500.0
    with pytest.raises(ValueError):
        r317.R317Config(advance_demography=True)
    with pytest.raises(ValueError):
        r317.R317Config(biology_cadence_years=5000.0)


def test_restart_partition_is_exact_ten_500y_intervals():
    p = r317.restart_partition(clock_125_120())
    assert p["segment_count"] == 10
    assert p["total_years"] == pytest.approx(5000.0)
    assert all(float(x["dt_years"]) == pytest.approx(500.0) for x in p["segments"])


def test_pending_exposure_integral_constant_field_closes_exactly():
    acc, diag = r317.build_pending_exposure_accumulator(FakeAdapter(variable=False), clock_125_120())
    assert diag["duration_years"] == pytest.approx(5000.0)
    assert diag["segment_count"] == 10
    # Constant temperature 10.123 integrated over exactly 5000 y.
    assert np.max(np.abs(acc["temperature_c"] - 10.123 * 5000.0)) < 1e-9
    assert diag["total_forage_average_closure_max_abs"] < 1e-14


def test_linear_exposure_trapezoid_is_exact():
    acc, _ = r317.build_pending_exposure_accumulator(FakeAdapter(variable=True), clock_125_120())
    # Mean age over 125->120 ka is 122.5 ka = 0.1225 Ma.
    want = (10.0 + 0.1225) * 5000.0
    assert np.max(np.abs(acc["temperature_c"] - want)) < 1e-9


def test_phase_report_preserves_parent_biology_grid():
    p = r317.biology_phase_report()
    assert p["physical_age_ma"] == pytest.approx(0.12)
    assert p["biology_state_age_ma"] == pytest.approx(0.125)
    assert p["elapsed_since_last_full_biology_boundary_years"] == pytest.approx(5000.0)
    assert p["remaining_to_next_full_biology_boundary_years"] == pytest.approx(120000.0)
    assert p["next_full_biology_boundary_age_ma"] == pytest.approx(0.0)
    assert p["remaining_to_next_transport_boundary_years"] == pytest.approx(57500.0)
    assert p["next_transport_boundary_age_ma"] == pytest.approx(0.0625)
    assert p["gene_flow_due_at_120ka"] is False
    assert p["transport_due_at_120ka"] is False


def test_restart_envelope_never_calls_biology_solver(monkeypatch):
    monkeypatch.setattr(r317.r316, "R316C2BridgeEnvironmentAdapter", FakeAdapter)
    monkeypatch.setattr(r317.r38, "advance_state", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("biology solver called")))
    parent = SimpleNamespace(age_ma=0.125, pop=np.ones((2, 2, 3), dtype=float))
    env, acc = r317.build_restart_envelope(parent, None, None, clock_125_120())
    assert env["biology_state_mutated"] is False
    assert env["biology_state_relabelled_to_120ka"] is False
    assert env["physical_restart_age_ma"] == pytest.approx(0.12)
    assert env["biology_state_age_ma"] == pytest.approx(0.125)
    assert env["environmental_restart"]["restart_boundary_at_120ka"] is True
    assert env["governance"]["partial_biology_step_executed"] is False
    assert set(acc) == set(r317.r316.AVERAGED_FIELDS)


def test_support_loss_is_diagnostic_not_silent_remap(monkeypatch):
    class LossAdapter(FakeAdapter):
        def __init__(self, *_a, **_k):
            super().__init__(support_loss=True)
    monkeypatch.setattr(r317.r316, "R316C2BridgeEnvironmentAdapter", LossAdapter)
    parent = SimpleNamespace(age_ma=0.125, pop=np.ones((2, 2, 3), dtype=float))
    env, _ = r317.build_restart_envelope(parent, None, None, clock_125_120())
    d = env["support_transition_diagnostic"]
    assert d["lost_accessible_cell_count_125_to_120"] == 1
    assert d["parent_population_mass_on_cells_inaccessible_at_120ka"] == pytest.approx(2.0)
    assert d["support_reconciliation_applied_in_r317"] is False


def test_accumulator_save_load_roundtrip(tmp_path):
    acc, _ = r317.build_pending_exposure_accumulator(FakeAdapter(variable=True), clock_125_120())
    p = tmp_path / "a.npz"
    meta = r317.save_accumulator(acc, p)
    got = r317.load_accumulator(p)
    assert meta["sha256"] == r317._sha256(p)
    assert got["duration_years"] == pytest.approx(5000.0)
    assert got["older_age_ma"] == pytest.approx(0.125)
    assert got["younger_age_ma"] == pytest.approx(0.12)
    for k in acc:
        assert np.array_equal(got["integrals"][k], acc[k])


def test_parent_validation_fails_closed_without_r316_seal(tmp_path):
    with pytest.raises(RuntimeError):
        r317.validate_parent_r316_authority(Path(tmp_path))
