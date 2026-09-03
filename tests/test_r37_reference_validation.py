from pathlib import Path
from arcana_worldsim.scientific_engines.r37_validation import analyze_r37_reference_closure

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'reference_results'/'v0_6D1_R3_6D_RAW_RESULTS.zip'
R36E=ROOT/'reference_results'/'R3_6E_CAUSAL_INFERENCE.json'

def result():
    return analyze_r37_reference_closure(RAW,R36E)

def test_reference_closure_verdict_passes():
    assert result()['verdict'].startswith('PASS_SEGREGATION_AWARE_OPERATOR_REFERENCE_CLOSURE')

def test_r37_matches_analytic_qtl():
    r=result()
    assert r['max_relative_error_vs_analytic'] < 1e-8

def test_legacy_inflation_removed_without_scalar():
    r=result()
    assert r['minimum_legacy_over_repaired_factor'] > 100

def test_free_recombination_reference_removes_transient_covariance():
    assert result()['maximum_ancestry_post_over_pre'] < 1e-3

def test_governance_remains_fail_closed():
    r=result()
    assert not r['canonical_write_allowed']
    assert not r['production_runtime_binding_allowed']
    assert not r['mu_b_change_authorized']
    assert not r['ceiling_change_authorized']
    assert not r['state_initialization_authorized']
    assert not r['state_evolution_authorized']
