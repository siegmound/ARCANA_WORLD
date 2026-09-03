from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
import numpy as np
import pytest

from arcana_worldsim.scientific_engines import r318_recent_exposure_transport_readiness as r318


def fake_clock():
    # Deliberately omit 62.5 ka; R3.18 must insert the exact transport boundary.
    ages = [0.120, 0.115, 0.110, 0.105, 0.100, 0.095, 0.090, 0.085, 0.080,
            0.075, 0.070, 0.065, 0.060, 0.055, 0.050, 0.045, 0.040, 0.035,
            0.030, 0.025, 0.020, 0.015, 0.010, 0.005, 0.0]
    return {"age_ma": np.asarray(ages, float)}


class FakeC2:
    def supports_age(self, age):
        y = round(float(age) * 1_000_000)
        return -1e-12 <= float(age) <= 0.250 + 1e-12 and abs(float(age) * 1_000_000 - y) < 1e-7


class FakeAdapter:
    def __init__(self, *_a, variable=True, support_changes=True, **_k):
        self.variable = variable
        self.support_changes = support_changes

    def state_at_age(self, age):
        age = float(age)
        x = age if self.variable else 0.05
        support = np.ones((2, 3), dtype=float)
        if self.support_changes and age <= 0.0625 + 1e-12:
            support[0, 0] = 0.0
        if self.support_changes and age <= 1e-12:
            support[1, 2] = 0.0
        browse = np.full((2, 3), 1.0 + x)
        low = np.full((2, 3), 0.5 + 0.5*x)
        wet = np.full((2, 3), 0.25 + 0.25*x)
        return {
            "age_ma": age,
            "land_support": support,
            "accessible": support > 1e-9,
            "temperature_c": np.full((2,3), 10.0+x),
            "aridity_index": np.full((2,3), 0.3+0.01*x),
            "browse_forage": browse,
            "low_forage": low,
            "wetland_forage": wet,
            "total_edible_forage": browse+low+wet,
            "reference_population": np.full((2,2,3),3.0+x),
        }


def pending_constant(value_age=0.1225):
    state = FakeAdapter(variable=True, support_changes=False).state_at_age(value_age)
    ints = {k: np.asarray(state[k], float) * 5000.0 for k in r318.AVERAGED_FIELDS}
    return {"duration_years":5000.0,"older_age_ma":0.125,"younger_age_ma":0.120,"integrals":ints}


def test_config_preserves_cadences_and_freezes_biology():
    c=r318.R318Config()
    assert c.biology_state_age_ma == pytest.approx(.125)
    assert c.transport_boundary_age_ma == pytest.approx(.0625)
    assert c.biology_cadence_years == pytest.approx(125000.0)
    assert c.transport_cadence_years == pytest.approx(62500.0)
    assert not c.advance_biology and not c.advance_transport
    with pytest.raises(ValueError): r318.R318Config(advance_transport=True)
    with pytest.raises(ValueError): r318.R318Config(transport_cadence_years=500.0)


def test_recent_partition_inserts_exact_62p5ka_boundary():
    p=r318.recent_partition(fake_clock())
    assert p["total_years"] == pytest.approx(120000.0)
    assert p["contains_62p5ka_transport_boundary"] is True
    assert any(abs(x-.0625)<1e-12 for x in p["nodes_age_ma"])


def test_constant_recent_integral_closes_exactly(monkeypatch):
    a=FakeAdapter(variable=False,support_changes=False)
    p=r318.recent_partition(fake_clock())
    integ,diag=r318.integrate_partition(a,p)
    assert diag["duration_years"] == pytest.approx(120000.0)
    assert np.max(np.abs(integ["temperature_c"] - 10.05*120000.0)) < 1e-6


def test_full_integral_equals_two_transport_phases(monkeypatch):
    monkeypatch.setattr(r318,"D3LateCenozoicSubstrateAdapter",FakeAdapter)
    parent=SimpleNamespace(age_ma=.125,pop=np.ones((2,2,3)),current_accessible=np.ones((2,3),bool))
    env,groups=r318.build_recent_exposure_readiness(parent,None,FakeC2(),fake_clock(),pending_constant())
    assert env["full_125ka_macrostep"]["integral_phase_closure_max_abs"] < 1e-6
    for k in r318.AVERAGED_FIELDS:
        want=groups["transport_phase1_125_to_62p5"][k]+groups["transport_phase2_62p5_to_0"][k]
        assert np.max(np.abs(groups["full_125_to_0"][k]-want)) < 1e-6


def test_variable_transport_phases_are_not_collapsed(monkeypatch):
    monkeypatch.setattr(r318,"D3LateCenozoicSubstrateAdapter",FakeAdapter)
    parent=SimpleNamespace(age_ma=.125,pop=np.ones((2,2,3)),current_accessible=np.ones((2,3),bool))
    env,_=r318.build_recent_exposure_readiness(parent,None,FakeC2(),fake_clock(),pending_constant())
    d=env["transport_phases"]["effective_environment_divergence"]
    assert d["roundoff_equivalent_all_fields"] is False
    assert env["transport_phases"]["phase_aware_transport_operator_required"] is True


def test_constant_transport_phases_can_be_exact(monkeypatch):
    class ConstAdapter(FakeAdapter):
        def __init__(self,*a,**k): super().__init__(*a,variable=False,support_changes=False,**k)
    monkeypatch.setattr(r318,"D3LateCenozoicSubstrateAdapter",ConstAdapter)
    state=ConstAdapter().state_at_age(.05)
    pending={"duration_years":5000.0,"integrals":{k:np.asarray(state[k],float)*5000.0 for k in r318.AVERAGED_FIELDS}}
    parent=SimpleNamespace(age_ma=.125,pop=np.ones((2,2,3)),current_accessible=np.ones((2,3),bool))
    env,_=r318.build_recent_exposure_readiness(parent,None,FakeC2(),fake_clock(),pending)
    assert env["transport_phases"]["effective_environment_divergence"]["roundoff_equivalent_all_fields"] is True
    assert env["transport_phases"]["phase_aware_transport_operator_required"] is False


def test_support_change_is_diagnostic_and_no_remap(monkeypatch):
    monkeypatch.setattr(r318,"D3LateCenozoicSubstrateAdapter",FakeAdapter)
    parent=SimpleNamespace(age_ma=.125,pop=np.ones((2,2,3)),current_accessible=np.ones((2,3),bool))
    env,_=r318.build_recent_exposure_readiness(parent,None,FakeC2(),fake_clock(),pending_constant())
    assert env["support_diagnostics"]["120_to_62p5"]["lost_accessible_cell_count"] == 1
    assert env["support_diagnostics"]["62p5_to_0"]["lost_accessible_cell_count"] == 1
    assert env["governance"]["support_remap_applied"] is False
    assert env["governance"]["production_biology_closure_authorized_in_r318"] is False


def test_build_never_calls_biology_solver(monkeypatch):
    monkeypatch.setattr(r318,"D3LateCenozoicSubstrateAdapter",FakeAdapter)
    monkeypatch.setattr(r318.r38,"advance_state",lambda *_a,**_k: (_ for _ in ()).throw(AssertionError("biology called")))
    parent=SimpleNamespace(age_ma=.125,pop=np.ones((2,2,3)),current_accessible=np.ones((2,3),bool))
    env,_=r318.build_recent_exposure_readiness(parent,None,FakeC2(),fake_clock(),pending_constant())
    assert env["biology_state_mutated"] is False
    assert env["biology_state_relabelled_to_0ka"] is False


def test_bundle_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(r318,"D3LateCenozoicSubstrateAdapter",FakeAdapter)
    parent=SimpleNamespace(age_ma=.125,pop=np.ones((2,2,3)),current_accessible=np.ones((2,3),bool))
    _,groups=r318.build_recent_exposure_readiness(parent,None,FakeC2(),fake_clock(),pending_constant())
    p=tmp_path/"bundle.npz"
    meta=r318.save_integral_bundle(groups,p)
    got=r318.load_integral_bundle(p)
    assert meta["sha256"] == r318._sha256(p)
    assert got["biology_state_age_ma"] == pytest.approx(.125)
    assert got["transport_boundary_age_ma"] == pytest.approx(.0625)
    assert set(got["groups"]) == set(groups)
    for g in groups:
        for k in groups[g]: assert np.array_equal(got["groups"][g][k],groups[g][k])


def test_parent_validation_fails_closed_without_r317_seal(tmp_path):
    with pytest.raises(RuntimeError): r318.validate_parent_r317_authority(Path(tmp_path))
