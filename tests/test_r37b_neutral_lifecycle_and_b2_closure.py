from pathlib import Path
import numpy as np

from arcana_worldsim.scientific_engines.neutral_reduced_lifecycle import (
    advance_neutral_one_generation, advance_neutral_generations,
)
from arcana_worldsim.scientific_engines.r37b_validation import analyze_r37a_b2_neutral_closure
from arcana_worldsim.scientific_engines.r37b_shadow_binding import advance_neutral_world_interval_shadow
from arcana_worldsim.scientific_engines.segregation_aware_admixture import validate_segregation_potential

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'reference_results'/'v0_6D1_R3_7A_B2'/'v0_6D1_R3_7A_B2_RESULTS.zip'


def test_one_generation_no_flow_exact_drift_transfer():
    va=np.array([[0.04],[0.04]])
    s=np.zeros((2,2,1))
    out=advance_neutral_one_generation(va,s,np.eye(2),1000.0)
    assert np.allclose(out.va_within[:,0],0.04*(1-1/2000))
    assert np.isclose(out.segregation_potential[0,1,0],2*(0.04/2000))
    assert out.diagnostics['new_drift_coefficient_introduced'] is False


def test_one_generation_migration_genic_injection_exact_two_deme():
    va=np.array([[0.03],[0.05]])
    s=np.zeros((2,2,1)); s[0,1,0]=s[1,0,0]=0.02
    p=np.array([[0.8,0.2],[0.2,0.8]])
    out=advance_neutral_one_generation(va,s,p,1e30)
    expected0=0.8*0.03+0.2*0.05+0.8*0.2*0.02
    expected1=0.2*0.03+0.8*0.05+0.2*0.8*0.02
    assert np.allclose(out.va_within[:,0],[expected0,expected1],rtol=0,atol=1e-12)


def test_multigeneration_state_remains_squared_euclidean():
    va=np.full((4,1),0.045)
    x=np.array([0.0,0.1,0.4,0.9])[:,None]
    s=((x[:,None,:]-x[None,:,:])**2)
    p=np.array([[.97,.03,0,0],[.03,.94,.03,0],[0,.03,.94,.03],[0,0,.03,.97]])
    out=advance_neutral_generations(va,s,p,500.0,250)
    diag=validate_segregation_potential(out.segregation_potential,tolerance=1e-7)
    assert diag['minimum_centered_gram_eigenvalue'] > -1e-7
    assert np.all(out.va_within>=0)


def test_world_interval_shadow_matches_one_generation_when_dt_is_one_generation():
    va=np.array([[0.04],[0.05]])
    s=np.zeros((2,2,1)); s[0,1,0]=s[1,0,0]=0.01
    p=np.array([[0.9,0.1],[0.1,0.9]])
    exact=advance_neutral_one_generation(va,s,p,1000.0)
    # D3.3A interval drift uses exp(-1/(2N)); one-generation WF uses
    # 1-1/(2N), so they differ only at O(1/N^2), by design.
    v2,s2,meta=advance_neutral_world_interval_shadow(va,s,p,np.array([1000.,1000.]),np.array([5.,5.]),5.0)
    assert np.max(np.abs(v2-exact.va_within)) < 2e-8
    assert np.max(np.abs(s2-exact.segregation_potential)) < 4e-8
    assert meta['selection_K_eff_authorized'] is False
    assert meta['canonical_write_allowed'] is False


def test_real_b2_evidence_complete_and_neutral_closure_supported():
    out=analyze_r37a_b2_neutral_closure(RAW)
    assert out['raw_evidence_status']=='NEMO_B2_EVIDENCE_COMPLETE_REVIEW_REQUIRED'
    assert out['phase_observation_count']==24
    assert out['verdict']=='PASS_NEUTRAL_S_LIFECYCLE_SUPPORTED_BY_NEMO_B2'


def test_real_b2_median_S_ratio_near_unity_without_fitted_parameter():
    out=analyze_r37a_b2_neutral_closure(RAW)
    med=out['S_observed_over_predicted']['median']
    assert 0.90 < med < 1.10
    assert out['free_calibration_parameter_fitted'] is False


def test_real_b2_VA_error_small():
    out=analyze_r37a_b2_neutral_closure(RAW)
    assert out['VA_fractional_error']['median_abs'] < 0.02
    assert out['VA_fractional_error']['maximum_abs'] < 0.05


def test_b2_does_not_authorize_selection_keff():
    out=analyze_r37a_b2_neutral_closure(RAW)
    assert out['selection_enabled_in_b2'] is False
    assert out['selection_participation_K_eff_authorized'] is False
    assert out['production_runtime_binding_authorized'] is False
