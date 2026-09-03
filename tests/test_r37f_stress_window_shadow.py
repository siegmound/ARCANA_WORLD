import pytest
from arcana_worldsim.scientific_engines.r37f_stress_window_shadow_replay import (
    R37FStressWindowConfig,
    _k_sensitivity_diagnostics,
    _legacy_clip_diagnostics,
)


def test_governed_window_crosses_historical_legacy_clip_onset():
    cfg = R37FStressWindowConfig()
    assert cfg.start_age_ma == 210.0
    assert cfg.end_age_ma == 188.0
    assert round((cfg.start_age_ma-cfg.end_age_ma)*1e6/cfg.biology_cadence_years) == 176
    assert cfg.end_age_ma < 191.25 < cfg.start_age_ma


def test_non_governed_full_window_rejected():
    with pytest.raises(ValueError):
        R37FStressWindowConfig(end_age_ma=190.0)


def test_diagnostic_window_allowed_but_cannot_reach_below_full_end():
    assert R37FStressWindowConfig(end_age_ma=209.0, diagnostic_smoke=True).diagnostic_smoke
    with pytest.raises(ValueError):
        R37FStressWindowConfig(end_age_ma=187.0, diagnostic_smoke=True)


def test_parent_K_envelope_is_preserved():
    cfg = R37FStressWindowConfig()
    assert cfg.envelope.values() == (37.614, 38.470, 41.002)


def test_authority_parameters_are_not_recalibrated():
    cfg = R37FStressWindowConfig()
    assert cfg.variance_ceiling_normalized == pytest.approx(0.08)
    assert cfg.biology_cadence_years == pytest.approx(125000.0)
    assert cfg.transport_cadence_years == pytest.approx(62500.0)
    assert cfg.mutation_variance_supply_normalized_per_myr == pytest.approx(0.002)
    assert cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q == pytest.approx(0.9876543209876544)


def test_legacy_clip_diagnostics_extracts_first_and_last_age():
    fake = {"r35_telemetry": [
        {"step_index": 0, "age_ma": 192.0, "homeostasis_clipping_count": 0},
        {"step_index": 1, "age_ma": 191.875, "homeostasis_clipping_count": 2},
        {"step_index": 2, "age_ma": 191.75, "homeostasis_clipping_count": 1},
    ]}
    d = _legacy_clip_diagnostics(fake)
    assert d["legacy_clipping_reproduced"] is True
    assert d["steps_with_clipping"] == 2
    assert d["total_clipped_reservoir_step_contacts"] == 3
    assert d["first_clipping_age_ma"] == pytest.approx(191.875)
    assert d["last_clipping_age_ma"] == pytest.approx(191.75)


def test_k_sensitivity_reports_nonzero_genetic_spread_when_q_is_equal():
    def row(age, vals):
        variants = {}
        for label, s, h in zip(("K_LOW","K_CENTER","K_HIGH"), vals, (0.12,0.11,0.10)):
            variants[label] = {"state": {
                "max_normalized_va": 0.03,
                "median_normalized_va": 0.02,
                "p99_normalized_va": 0.029,
                "same_species_S_max": s,
                "same_species_S_median": s/10,
                "ancestry_abs_total": s/100,
                "adaptive_coordinate_abs_max": h,
            }}
        return {"age_ma": age, "variants": variants}
    d = _k_sensitivity_diagnostics([row(209.0,(0.3,0.29,0.28))])
    assert d["max_normalized_va"]["maximum_absolute_envelope_spread"] == 0.0
    assert d["same_species_S_max"]["maximum_absolute_envelope_spread"] > 0.0
    assert d["adaptive_coordinate_abs_max"]["maximum_absolute_envelope_spread"] > 0.0


def test_shadow_recombination_is_reference_only():
    cfg = R37FStressWindowConfig()
    assert cfg.shadow_recombination_fraction_per_generation == pytest.approx(0.5)
