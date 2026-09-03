from __future__ import annotations

import numpy as np
import pytest

from arcana_worldsim.late_cenozoic import cha2_hydrological_hazard as r320
from arcana_worldsim.late_cenozoic.cha2_nested_50y import _canonical_freshwater_pulse


class FakeProvider:
    def __init__(self, timing_shift=0):
        self.timing_shift = int(timing_shift)

    def supports_year(self, year):
        y = int(year)
        return -15000 <= y <= -9000 and y % 50 == 0

    def state_at_year(self, year):
        y = int(year)
        center = -12900 + self.timing_shift
        g = np.exp(-0.5 * ((y - center) / 550.0) ** 2)
        fw = 0.196 * np.exp(-0.5 * ((y - center) / 210.0) ** 2)
        m = 1.0 - 0.60 * g
        gt = -1.5 * g
        lat_delta = np.asarray([0.2, 0.4, -2.5, -5.0])[:, None] * g
        temp = 10.0 + np.broadcast_to(lat_delta, (4, 6))
        # Lower index means drier in the existing biology mapping.
        aridity = np.ones((4, 6)) * (1.0 + 0.18 * np.sin((y + 15000) / 500.0))
        wet = np.ones((4, 6)) * (1.0 + 0.12 * np.sin((y + 14950) / 500.0))
        land = np.ones((4, 6))
        if y >= -12000:
            land[0, 0] = 0.85
        total = np.ones((4, 6)) * (2.0 + 0.1 * np.cos((y + 15000) / 400.0))
        return {
            "freshwater_forcing_sv": float(fw),
            "overturning_strength": float(m),
            "global_temperature_anomaly_c": float(gt),
            "temperature_c": temp,
            "land_support": land,
            "aridity_index": aridity,
            "wetland_forage": wet,
            "total_edible_forage": total,
            "sea_level_anomaly_m": float(-40 + (y + 15000) / 1000.0),
        }


class LowOrderScalarDelayedFullRecoveryProvider:
    """YD-like regional event with weak low-order global scalar and late 90% recovery.

    This regression encodes the exact audit distinction repaired in R3.20-R1:
    strong-event exit occurs before the nested core ends, while 90% circulation
    recovery occurs later on an exact 100-y sealed-style anchor.
    """

    def supports_year(self, year):
        y = int(year)
        if -15000 <= y <= -11000 and y % 50 == 0:
            return True
        return -10900 <= y <= -9000 and y % 100 == 0

    def state_at_year(self, year):
        y = int(year)
        # Baseline near 1.0, rapid collapse near 12.85 ka, exit from <80%
        # suppression near 11.5 ka, but 90% recovery only after the 15-11 ka core.
        if y <= -12850:
            collapse = np.exp(-0.5 * ((y + 12850.0) / 300.0) ** 2)
            m = 1.0 - 0.62 * collapse
        else:
            m = 1.0 - 0.62 * np.exp(-(y + 12850.0) / 1200.0)
        fw = 0.202 * np.exp(-0.5 * ((y + 12900.0) / 210.0) ** 2)
        # Deliberately weak low-order scalar response; this is not an
        # area-weighted global-mean temperature reconstruction.
        gt = -0.10 * np.exp(-0.5 * ((y + 12750.0) / 500.0) ** 2)
        g = np.exp(-0.5 * ((y + 12850.0) / 520.0) ** 2)
        lat_delta = np.asarray([0.2, 0.4, -2.8, -5.0])[:, None] * g
        temp = 10.0 + np.broadcast_to(lat_delta, (4, 6))
        aridity = np.ones((4, 6))
        wet = np.ones((4, 6))
        land = np.ones((4, 6))
        total = np.ones((4, 6)) * 2.0
        return {
            "freshwater_forcing_sv": float(fw),
            "overturning_strength": float(m),
            "global_temperature_anomaly_c": float(gt),
            "temperature_c": temp,
            "land_support": land,
            "aridity_index": aridity,
            "wetland_forage": wet,
            "total_edible_forage": total,
            "sea_level_anomaly_m": -30.0,
        }


def a1_fixture():
    return {"lat": np.asarray([-60.0, 10.0, 50.0, 70.0])}


def test_canonical_cha2_freshwater_peak_already_yd_class():
    t = np.arange(-15000, -10999, 1, dtype=float)
    v = _canonical_freshwater_pulse(t)
    i = int(np.argmax(v))
    assert -13000 <= t[i] <= -12800
    assert 0.18 <= float(v[i]) <= 0.21


def test_r320_governance_forbids_narrative_calibration():
    c = r320.HydrologicalHazardConfig()
    assert c.human_population_used is False
    assert c.flood_myth_target_used is False
    assert c.religion_target_used is False
    assert c.impact_origin_required is False
    with pytest.raises(ValueError):
        r320.HydrologicalHazardConfig(flood_myth_target_used=True)
    with pytest.raises(ValueError):
        r320.HydrologicalHazardConfig(impact_origin_required=True)


def test_magnitude_classifier_accepts_yd_class_synthetic_event():
    out = r320.audit_younger_dryas_class_magnitude(FakeProvider(), a1_fixture())
    assert out["passed"] is True
    assert out["classification"] == "YOUNGER_DRYAS_CLASS"
    assert out["metrics"]["freshwater_peak_sv"] > 0.15
    assert out["metrics"]["minimum_overturning_fraction_of_baseline"] < 0.65
    assert out["metrics"]["maximum_northern_local_cooling_c"] >= 2.0
    assert out["governance"]["human_population_used"] is False


def test_magnitude_classifier_fails_closed_on_wrong_timing():
    out = r320.audit_younger_dryas_class_magnitude(FakeProvider(timing_shift=1700), a1_fixture())
    assert out["passed"] is False
    assert out["classification"] == "OUTSIDE_YOUNGER_DRYAS_CLASS_ENVELOPE"
    assert not out["checks"]["freshwater_peak_timing"] or not out["checks"]["overturning_minimum_timing"]


def test_hazard_snapshot_is_bounded_and_population_free():
    out = r320.hydrological_hazard_snapshot(FakeProvider(), a1_fixture(), -12900)
    for key in (
        "pluvial_flood_potential_index", "coastal_inundation_potential_index",
        "compound_flood_hazard_index", "drying_hazard_index",
        "ecosystem_hydrological_shock_index", "hydrological_disruption_index",
    ):
        a = np.asarray(out[key])
        assert np.all(np.isfinite(a))
        assert np.min(a) >= 0.0
        assert np.max(a) <= 1.0
    assert out["human_population_used"] is False
    assert out["settlement_target_used"] is False
    assert out["flood_myth_target_used"] is False
    assert out["religion_target_used"] is False


def test_coastal_support_loss_is_explicit_raw_physics_signal():
    p = FakeProvider()
    out = r320.hydrological_hazard_snapshot(p, a1_fixture(), -12000)
    raw = np.asarray(out["raw_support_loss_fraction"])
    assert raw[0, 0] > 0.0
    assert np.asarray(out["coastal_inundation_potential_index"])[0, 0] > 0.0


def test_timeseries_is_exact_50y_core_and_has_no_human_target():
    out = r320.build_hazard_timeseries(FakeProvider(), a1_fixture())
    years = np.asarray(out["years_before_book"])
    assert years[0] == -14950 and years[-1] == -11000
    assert np.all(np.diff(years) == 50)
    assert len(years) == 80
    assert out["governance"]["hazard_indices_are_diagnostic_rankings_not_flood_depths"] is True
    assert out["governance"]["human_population_used"] is False
    for arr in out["fields"].values():
        assert arr.shape == (80, 4, 6)


def test_reference_envelope_encodes_youngerdryas_class_not_exact_earth_copy():
    e = r320.YoungerDryasClassEnvelope()
    assert e.principal_peak_older_year <= -12900 <= e.principal_peak_younger_year
    assert e.min_freshwater_peak_sv < 0.196 < e.max_freshwater_peak_sv
    assert e.min_strong_suppression_years < e.max_strong_suppression_years
    assert e.max_northern_local_cooling_c >= 10.0


def test_r320_r1_weak_low_order_global_scalar_is_diagnostic_not_false_fail():
    out = r320.audit_younger_dryas_class_magnitude(
        LowOrderScalarDelayedFullRecoveryProvider(), a1_fixture()
    )
    assert out["passed"] is True
    assert out["checks"]["global_state_cooling_direction"] is True
    assert "global_cooling_magnitude" not in out["checks"]
    assert out["metrics"]["maximum_global_state_cooling_c_diagnostic"] < 0.20
    assert out["governance"]["global_temperature_scalar_magnitude_is_hard_gate"] is False


def test_r320_r1_event_exit_is_distinct_from_90pct_full_recovery():
    out = r320.audit_younger_dryas_class_magnitude(
        LowOrderScalarDelayedFullRecoveryProvider(), a1_fixture()
    )
    assert out["checks"]["event_exit_detected"] is True
    assert out["checks"]["northern_cooling_timing"] is True
    assert out["metrics"]["event_exit_year_before_book"] <= -11000
    assert "event_exit_timing" not in out["checks"]
    # 90% recovery is diagnostic and may occur after the nested 15-11 ka core.
    full = out["metrics"]["full_recovery_year_before_book_diagnostic"]
    assert full is None or full > -11000
    assert out["governance"]["full_90pct_overturning_recovery_is_hard_gate"] is False


def test_r320_r1_parent_seal_schema_uses_formal_audit_checks():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    audit_src = (root / "scripts/formal_audit_v0_6D1_R3_20_candidate.py").read_text(encoding="utf-8")
    run_src = (root / "scripts/run_v0_6D1_R3_20_cha2_yd_hydrological_hazard.py").read_text(encoding="utf-8")
    verifier = (root / "verify_v0_6D1_R3_20_patch.ps1").read_text(encoding="utf-8")
    assert "formal_audit_checks" in audit_src
    assert "formal_audit_checks" in run_src
    assert "formal_audit_checks" in verifier
    assert "s.get('formal_audit_checks', s.get('checks'))" in audit_src
    assert 'seal.get("formal_audit_checks", seal.get("checks"))' in run_src
    assert "$seal.formal_audit_checks" in verifier
