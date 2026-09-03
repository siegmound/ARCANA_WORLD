from pathlib import Path
import numpy as np

from arcana_worldsim.scientific_engines.nemo242_r37c import R37CSelectionProtocol, r37c_exchange_matrix
from arcana_worldsim.scientific_engines.nemo242_r37c_r1 import (
    R37C_R1_STAGE,
    R37C_R1_SELECTED_LCE,
    R37C_R1_SELECTION_FITNESS_MODEL,
    render_r37c_r1_phase_ini,
    selection_efficacy_metrics,
)


def _effects_freq():
    effects=np.linspace(0.005,0.02,8)
    freq=np.full((4,8),0.5)
    return effects,freq


def test_r1_identity_and_parent_protocol_reuse():
    assert R37C_R1_STAGE=='v0.6D1-R3.7C-R1'
    assert R37C_R1_SELECTED_LCE=='breed_selection_disperse'
    assert R37C_R1_SELECTION_FITNESS_MODEL=='absolute'
    p=R37CSelectionProtocol()
    assert p.selection_variances==(1.0,4.0)
    assert (p.burnin_transitions,p.selected_transitions,p.reconnect_transitions)==(200,300,400)


def test_selected_renderer_uses_composite_selection_and_absolute_fitness(tmp_path:Path):
    effects,freq=_effects_freq()
    m=render_r37c_r1_phase_ini(
        phase='FRAGMENTED_DIVERGENT_SELECTION',transitions=10,effect_a=effects,allele_frequencies=freq,
        population_size=500,seed=123,output_dir=tmp_path,chain_id='x',selection_enabled=True,
        selection_variance=1.0,optimum_amplitude=0.6,exchange_matrix=r37c_exchange_matrix('FRAGMENTED_DIVERGENT_SELECTION'),
    )
    txt=(tmp_path/'Nemo2_ARCANA_R37C_R1.ini').read_text()
    assert 'breed_selection_disperse    2' in txt
    assert 'viability_selection' not in txt
    # Matrix parameter is inherited from the breed_disperse base implementation.
    assert 'breed_disperse_matrix' in txt
    assert 'selection_trait         quant' in txt
    assert 'selection_model         gaussian' in txt
    assert 'selection_fitness_model absolute' in txt
    assert 'selection_trait_dimension 1' in txt
    assert 'selection_variance      1' in txt
    assert 'selection_local_optima' in txt
    assert m['stage']==R37C_R1_STAGE
    assert m['selected_lifecycle_event']=='breed_selection_disperse'
    assert m['selection_fitness_model']=='absolute'
    assert m['production_selection_mapping_authorized'] is False


def test_neutral_renderer_remains_plain_breed_disperse(tmp_path:Path):
    effects,freq=_effects_freq()
    m=render_r37c_r1_phase_ini(
        phase='FRAGMENTED_MATCHED_NEUTRAL',transitions=10,effect_a=effects,allele_frequencies=freq,
        population_size=500,seed=123,output_dir=tmp_path,chain_id='x',selection_enabled=False,
        selection_variance=None,optimum_amplitude=0.6,exchange_matrix=r37c_exchange_matrix('FRAGMENTED_MATCHED_NEUTRAL'),
    )
    txt=(tmp_path/'Nemo2_ARCANA_R37C_R1.ini').read_text()
    assert 'breed_disperse              2' in txt
    assert 'breed_selection_disperse' not in txt
    assert 'viability_selection' not in txt
    assert 'selection_model' not in txt
    assert m['selection_enabled'] is False


def test_selected_renderer_rejects_missing_strength(tmp_path:Path):
    effects,freq=_effects_freq()
    try:
        render_r37c_r1_phase_ini(
            phase='FRAGMENTED_DIVERGENT_SELECTION',transitions=10,effect_a=effects,allele_frequencies=freq,
            population_size=500,seed=123,output_dir=tmp_path,chain_id='x',selection_enabled=True,
            selection_variance=None,optimum_amplitude=0.6,exchange_matrix=r37c_exchange_matrix('FRAGMENTED_DIVERGENT_SELECTION'),
        )
    except ValueError:
        pass
    else:
        raise AssertionError('selected phase must fail closed without selection variance')


def test_efficacy_gate_rejects_exact_selected_neutral_identity():
    effects,freq=_effects_freq()
    out=selection_efficacy_metrics(effects,freq,freq.copy())
    assert out['selected_neutral_frequency_state_exactly_identical'] is True
    assert out['max_abs_allele_frequency_delta']==0
    assert out['adaptive_trait_divergence']==0
    assert out['adaptive_cross_group_S']==0
    assert out['selection_efficacy_gate_pass'] is False


def test_efficacy_gate_accepts_directionally_divergent_selected_state():
    effects,freq=_effects_freq()
    sel=freq.copy()
    # Move left demes toward negative trait values and right demes toward positive values.
    sel[0:2,:]-=0.05
    sel[2:4,:]+=0.05
    out=selection_efficacy_metrics(effects,sel,freq)
    assert out['selected_neutral_frequency_state_exactly_identical'] is False
    assert out['max_abs_allele_frequency_delta']>0
    assert out['adaptive_trait_divergence']>0
    assert out['adaptive_cross_group_S']>0
    assert out['selection_efficacy_gate_pass'] is True


def test_efficacy_gate_rejects_wrong_direction_even_if_states_differ():
    effects,freq=_effects_freq()
    sel=freq.copy()
    sel[0:2,:]+=0.05
    sel[2:4,:]-=0.05
    out=selection_efficacy_metrics(effects,sel,freq)
    assert out['max_abs_allele_frequency_delta']>0
    assert out['adaptive_trait_divergence']<0
    assert out['selection_efficacy_gate_pass'] is False


def test_efficacy_gate_is_numerical_liveness_not_calibration_threshold():
    effects,freq=_effects_freq()
    sel=freq.copy()
    sel[0:2,:]-=1e-8
    sel[2:4,:]+=1e-8
    out=selection_efficacy_metrics(effects,sel,freq,numerical_tol=1e-12)
    assert out['selection_efficacy_gate_pass'] is True
    assert out['gate_semantics']=='NUMERICAL_LIVENESS_ONLY__NOT_EFFECT_SIZE_CALIBRATION'


def test_r1_runner_has_fail_closed_suite_efficacy_status():
    root=Path(__file__).resolve().parents[1]
    txt=(root/'scripts'/'run_nemo_r37c_r1_selection_chain.py').read_text()
    assert 'INVALID_SELECTION_ORACLE_SELECTION_EFFICACY_GATE_FAILED' in txt
    assert 'selection_efficacy_pass_count' in txt
    assert "status='NEMO_SELECTION_EVIDENCE_COMPLETE_REVIEW_REQUIRED'" in txt
    assert 'render_r37c_r1_phase_ini' in txt
