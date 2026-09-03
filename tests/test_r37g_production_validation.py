import pytest
from arcana_worldsim.scientific_engines.r37g_production_validation import R37GProductionValidationConfig


def test_governed_validation_window_is_210_to_150():
    cfg = R37GProductionValidationConfig()
    assert cfg.start_age_ma == 210.0
    assert cfg.end_age_ma == 150.0
    assert round((cfg.start_age_ma-cfg.end_age_ma)*1e6/cfg.biology_cadence_years) == 480


def test_non_governed_full_window_rejected():
    with pytest.raises(ValueError):
        R37GProductionValidationConfig(end_age_ma=160.0)


def test_diagnostic_smoke_allowed_only_inside_validation_window():
    assert R37GProductionValidationConfig(end_age_ma=209.0, diagnostic_smoke=True).diagnostic_smoke
    with pytest.raises(ValueError):
        R37GProductionValidationConfig(end_age_ma=149.0, diagnostic_smoke=True)


def test_k_envelope_preserved_and_center_is_not_singleton():
    cfg = R37GProductionValidationConfig()
    assert cfg.envelope.values() == (37.614, 38.470, 41.002)
    assert cfg.adaptive_k_low < cfg.adaptive_k_center < cfg.adaptive_k_high


def test_authority_parameters_remain_unchanged():
    cfg = R37GProductionValidationConfig()
    assert cfg.variance_ceiling_normalized == pytest.approx(0.08)
    assert cfg.mutation_variance_supply_normalized_per_myr == pytest.approx(0.002)
    assert cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q == pytest.approx(0.9876543209876544)
    assert cfg.biology_cadence_years == pytest.approx(125000.0)
    assert cfg.transport_cadence_years == pytest.approx(62500.0)


def test_shadow_recombination_remains_reference_architecture():
    cfg = R37GProductionValidationConfig()
    assert cfg.shadow_recombination_fraction_per_generation == pytest.approx(0.5)
