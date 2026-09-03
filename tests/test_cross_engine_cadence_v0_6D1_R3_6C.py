from __future__ import annotations
import numpy as np
import pytest

from arcana_worldsim.scientific_engines import (
    CadenceNormalizationSpec,
    arcana_offdiag_to_stochastic,
    stochastic_interval_to_subinterval,
    interval_exchange_to_nemo_generation,
    edge_hazard_substep_exchange,
    simulate_arcana_cadence_probe,
    build_three_way_reference_plan,
    canonical_r36b_scenarios, embeddable_reference_exchange_from_edge_targets,
)


def test_locked_equilibrium_is_exact_qstar():
    s = CadenceNormalizationSpec()
    assert abs(np.sqrt(s.mutation_q_per_myr / s.nonlinear_b_per_myr_per_q) - 0.045) < 1e-15
    assert s.substeps == 5


def test_arcana_exchange_to_stochastic_adds_self_retention():
    g = np.array([[0.0, 0.05], [0.05, 0.0]])
    d = arcana_offdiag_to_stochastic(g)
    assert np.allclose(d, [[0.95, 0.05], [0.05, 0.95]])
    assert np.allclose(d.sum(axis=1), 1.0)


def test_markov_subinterval_composes_back_to_125k():
    g = np.array([[0.0, 0.05], [0.05, 0.0]])
    d = arcana_offdiag_to_stochastic(g)
    sub = stochastic_interval_to_subinterval(d, 125000.0, 25000.0)
    assert np.allclose(np.linalg.matrix_power(sub, 5), d, atol=1e-10, rtol=0.0)


def test_nemo_generation_probability_is_not_arcana_125k_probability():
    g = np.array([[0.0, 0.05], [0.05, 0.0]])
    pergen = interval_exchange_to_nemo_generation(g, 125000.0, 5.0)
    assert pergen[0,1] < 1e-5
    assert pergen[0,1] > 0
    assert not np.isclose(pergen[0,1], 0.05)
    assert np.allclose(pergen.sum(axis=1), 1.0)


def test_edge_hazard_conversion_preserves_symmetry_and_avoids_raw_repeat():
    g = np.array([[0.0, 0.05], [0.05, 0.0]])
    sub = edge_hazard_substep_exchange(g, 5)
    assert np.allclose(sub, sub.T)
    assert 0 < sub[0,1] < 0.05
    assert abs((1.0-sub[0,1])**5 - (1.0-0.05)) < 1e-12


def test_three_way_plan_has_locked_governance_and_cadence_normalized_nemo():
    s = canonical_r36b_scenarios(n_individuals=200)[1]
    p = build_three_way_reference_plan(s)
    assert p["authority"]["canonical_write_allowed"] is False
    assert p["authority"]["automatic_calibration_allowed"] is False
    assert p["checks"]["nemo_rows_sum_one"] is True
    pergen = np.asarray(p["nemo_per_generation_stochastic_matrix"])
    assert pergen[0,1] < 1e-5


def test_arcana_125k_vs_5x25k_probe_is_finite_and_nonbinding():
    s = canonical_r36b_scenarios(n_individuals=2000)[1]
    a = simulate_arcana_cadence_probe(s, macrosteps=8, substeps_per_macrostep=1)
    b = simulate_arcana_cadence_probe(s, macrosteps=8, substeps_per_macrostep=5, rate_normalize_exchange=True)
    assert np.isfinite(a["final_max_q"]) and np.isfinite(b["final_max_q"])
    assert a["final_max_q"] < 1.0 and b["final_max_q"] < 1.0
    assert a["locks"] == b["locks"]


def test_naive_25k_raw_repeat_is_distinct_diagnostic_not_authorized_mapping():
    s = canonical_r36b_scenarios(n_individuals=2000)[1]
    good = simulate_arcana_cadence_probe(s, macrosteps=4, substeps_per_macrostep=5, rate_normalize_exchange=True)
    raw = simulate_arcana_cadence_probe(s, macrosteps=4, substeps_per_macrostep=5, rate_normalize_exchange=False)
    assert abs(good["final_max_q"] - raw["final_max_q"]) > 1e-6


def test_multiphase_scenario_requires_phase_scoped_plan():
    s = canonical_r36b_scenarios(n_individuals=200)[2]
    with pytest.raises(ValueError, match="single-phase"):
        build_three_way_reference_plan(s)


def test_high_stress_r36b_matrix_is_rejected_for_exact_markov_cadence_but_new_embeddable_reference_can_be_built():
    s = canonical_r36b_scenarios(n_individuals=200)[3]
    with pytest.raises(ValueError, match="not embeddable"):
        interval_exchange_to_nemo_generation(s.phases[0].exchange_matrix, 125000.0, 5.0)
    g2 = embeddable_reference_exchange_from_edge_targets(s.phases[0].exchange_matrix, 125000.0)
    pergen = interval_exchange_to_nemo_generation(g2, 125000.0, 5.0)
    assert np.allclose(pergen.sum(axis=1), 1.0, atol=1e-12)
    assert np.min(pergen) >= -1e-12
