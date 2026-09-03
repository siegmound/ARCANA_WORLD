from pathlib import Path
import json
import numpy as np

from arcana_worldsim.scientific_engines.r37d_selection_closure import (
    AdaptiveSelectionShadowEnvelope,
    analyze_r37c_r1_selection_evidence,
    geometric_adaptive_participation,
    shadow_adaptive_selection_envelope,
)
from arcana_worldsim.scientific_engines.segregation_potential_lifecycle import ReducedGeneticLifecycleState

ROOT=Path(__file__).resolve().parents[1]
EVID=ROOT/'evidence'/'v0_6D1_R3_7C_R1_SELECTION_RESULTS.zip'


def test_geometric_participation_exact_and_bounded():
    a=np.array([1.0,2.0,0.5])
    ctl=np.full((4,3),0.5)
    sel=ctl.copy()
    sel[0:2]-=np.array([0.1,0.05,0.02])
    sel[2:4]+=np.array([0.1,0.05,0.02])
    g=geometric_adaptive_participation(a,sel,ctl)
    assert g['adaptive_trait_divergence'] > 0
    assert g['geometric_adaptive_S'] > 0
    assert 0 < g['geometric_K_eff'] <= 3.0 + 1e-12


def test_full_r37c_r1_evidence_closure():
    r=analyze_r37c_r1_selection_evidence(EVID)
    assert r['chain_count']==16
    assert r['verdict'].startswith('PASS_DIRECTIONAL_SELECTION_EVIDENCE_CLOSURE')
    assert r['governance']['scalar_K_eff_production_authorized'] is False
    assert r['governance']['high_N_shadow_envelope_authorized'] is True


def test_aggregate_deltaS_estimator_is_not_geometric_participation():
    r=analyze_r37c_r1_selection_evidence(EVID)
    assert r['aggregate_deltaS_K_eff_diagnostic']['maximum'] > 64.0
    assert r['geometric_K_eff_all']['maximum'] <= 64.0 + 1e-12
    assert r['inference_correction']['cauchy_bound_loci']==64


def test_high_n_dynamic_selection_participation_is_tight_but_not_production_scalar():
    r=analyze_r37c_r1_selection_evidence(EVID)
    n2=r['by_population_size']['2000']
    assert n2['cv'] < 0.05
    env=r['high_N_dynamic_selection_shadow_envelope']
    assert env['minimum'] <= env['center_median'] <= env['maximum']
    assert 37.0 < env['minimum'] < 39.0
    assert 38.0 < env['center_median'] < 39.0
    assert 40.0 < env['maximum'] < 42.0


def test_finite_n_sensitivity_is_detected_but_not_mapped_to_worldsim_population():
    r=analyze_r37c_r1_selection_evidence(EVID)
    pe=r['paired_effects']['N_2000_minus_500']
    assert pe['mean'] > 20.0
    assert pe['exact_two_sided_signflip_p'] <= 0.01
    assert r['governance']['direct_WorldSim_N_to_NEMO_N_mapping_authorized'] is False


def test_selection_variance_not_systematic_in_geometric_participation():
    r=analyze_r37c_r1_selection_evidence(EVID)
    pe=r['paired_effects']['selection_variance_4_minus_1']
    assert abs(pe['mean']) < 2.0
    assert pe['exact_two_sided_signflip_p'] > 0.1


def test_reconnection_erodes_most_geometric_adaptive_displacement():
    r=analyze_r37c_r1_selection_evidence(EVID)
    ret=r['reconnection_geometric_S_retention']
    assert 0.02 <= ret['minimum']
    assert ret['median'] < 0.05
    assert ret['maximum'] < 0.10


def test_shadow_envelope_is_monotone_and_noncanonical():
    state=ReducedGeneticLifecycleState(
        va_within=np.full((2,1),0.045),
        ancestry_covariance=np.zeros((2,1)),
        neutral_segregation_potential=np.zeros((2,2,1)),
        adaptive_coordinate=np.zeros((2,1)),
    )
    env=AdaptiveSelectionShadowEnvelope(37.6,38.47,41.0)
    z0=np.zeros((2,1)); z1=np.array([[-0.2],[0.2]])
    out,diag=shadow_adaptive_selection_envelope(state,z0,z1,env)
    s_low=out['K_LOW'].total_segregation_potential[0,1,0]
    s_ctr=out['K_CENTER'].total_segregation_potential[0,1,0]
    s_hi=out['K_HIGH'].total_segregation_potential[0,1,0]
    assert s_low > s_ctr > s_hi > 0
    assert diag['governance']['canonical_write_allowed'] is False
    assert diag['governance']['production_runtime_replacement_authorized'] is False
