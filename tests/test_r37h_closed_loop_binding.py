import numpy as np
import pytest
from arcana_worldsim.scientific_engines.r37h_closed_loop_binding import (
    BRANCH_K, R37HClosedLoopConfig, compare_closed_loop_branches
)


def test_full_window_and_cadence():
    cfg=R37HClosedLoopConfig()
    assert cfg.start_age_ma == 210.0 and cfg.end_age_ma == 150.0
    assert round((cfg.start_age_ma-cfg.end_age_ma)*1e6/cfg.biology_cadence_years) == 480


def test_branch_values_are_exact_r37d_envelope():
    assert BRANCH_K == {"K_LOW":37.614,"K_CENTER":38.470,"K_HIGH":41.002}
    for label,k in BRANCH_K.items():
        cfg=R37HClosedLoopConfig(branch_label=label,adaptive_k_eff=k)
        assert cfg.adaptive_k_eff == pytest.approx(k)


def test_branch_label_value_mismatch_rejected():
    with pytest.raises(ValueError):
        R37HClosedLoopConfig(branch_label="K_LOW",adaptive_k_eff=38.470)


def test_authority_parameters_unchanged():
    cfg=R37HClosedLoopConfig()
    assert cfg.variance_ceiling_normalized == pytest.approx(0.08)
    assert cfg.mutation_variance_supply_normalized_per_myr == pytest.approx(0.002)
    assert cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q == pytest.approx(0.9876543209876544)
    assert cfg.biology_cadence_years == pytest.approx(125000.0)
    assert cfg.transport_cadence_years == pytest.approx(62500.0)


def test_recombination_remains_reference_reservoir_parameter():
    assert R37HClosedLoopConfig().segregation_recombination_fraction_per_generation == pytest.approx(0.5)


def test_smoke_window_allowed_but_noncanonical_full_window_rejected():
    assert R37HClosedLoopConfig(end_age_ma=209.0,diagnostic_smoke=True).diagnostic_smoke
    with pytest.raises(ValueError):
        R37HClosedLoopConfig(end_age_ma=160.0)


def _fake(label,peak,pop,species,components,event_counts):
    return {"branch_label":label,"peak_q":peak,"final_total_population":pop,"species_count":species,
            "component_count":components,"event_counts":event_counts,"closed_loop_gate_pass":True,"clipping_contacts":0}


def test_comparison_reports_macro_divergence_without_fitted_threshold():
    branches={
        "K_LOW":_fake("K_LOW",.04,100,3,4,{"deme_fission":1}),
        "K_CENTER":_fake("K_CENTER",.041,101,3,5,{"deme_fission":2}),
        "K_HIGH":_fake("K_HIGH",.039,102,4,5,{"deme_fission":2}),
    }
    out=compare_closed_loop_branches(branches)
    assert out["all_branches_valid"] and out["all_branches_clear_of_ceiling"]
    assert not out["species_count_exactly_equal"]
    assert not out["component_count_exactly_equal"]
    assert not out["event_counts_exactly_equal"]
    assert out["max_peak_q_spread"] == pytest.approx(.002)


def test_comparison_requires_all_three_branches():
    with pytest.raises(ValueError):
        compare_closed_loop_branches({"K_CENTER":_fake("K_CENTER",.04,1,1,1,{})})
