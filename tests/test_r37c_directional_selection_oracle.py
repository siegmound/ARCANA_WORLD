from pathlib import Path
import numpy as np

from arcana_worldsim.scientific_engines.nemo242_r37c import (
    R37CSelectionProtocol, r37c_exchange_matrix, r37c_nemo_transition,
    r37c_local_optima, render_r37c_phase_ini,
)


def _effects_freq():
    effects=np.linspace(0.005,0.02,8)
    freq=np.full((4,8),0.5)
    return effects,freq


def test_protocol_has_two_selection_strengths_and_three_phase_geometry():
    p=R37CSelectionProtocol()
    assert p.selection_variances==(1.0,4.0)
    assert p.burnin_transitions==200 and p.selected_transitions==300 and p.reconnect_transitions==400
    assert np.allclose(r37c_exchange_matrix('COMMON_BURNIN',p),r37c_exchange_matrix('RECONNECTED_RELAXED',p))
    frag=r37c_exchange_matrix('FRAGMENTED_DIVERGENT_SELECTION',p)
    assert frag[1,2]==0 and frag[0,1]>0 and frag[2,3]>0


def test_nemo_transition_is_symmetric_doubly_stochastic():
    p=r37c_nemo_transition(r37c_exchange_matrix('COMMON_BURNIN'))
    assert np.allclose(p,p.T)
    assert np.allclose(p.sum(axis=0),1)
    assert np.allclose(p.sum(axis=1),1)


def test_local_optima_are_divergent_and_balanced():
    x=r37c_local_optima(0.6)
    assert x.shape==(4,1)
    assert np.allclose(x[:,0],[-0.6,-0.6,0.6,0.6])
    assert np.isclose(np.mean(x),0)


def test_selected_renderer_uses_verified_nemo_gaussian_selection_syntax(tmp_path:Path):
    effects,freq=_effects_freq()
    m=render_r37c_phase_ini(
        phase='FRAGMENTED_DIVERGENT_SELECTION',transitions=10,effect_a=effects,allele_frequencies=freq,
        population_size=500,seed=123,output_dir=tmp_path,chain_id='x',selection_enabled=True,
        selection_variance=1.0,optimum_amplitude=0.6,exchange_matrix=r37c_exchange_matrix('FRAGMENTED_DIVERGENT_SELECTION'),
    )
    txt=(tmp_path/'Nemo2_ARCANA_R37C.ini').read_text()
    assert 'viability_selection     2' in txt
    assert 'selection_trait         quant' in txt
    assert 'selection_model         gaussian' in txt
    assert 'selection_fitness_model relative_local' in txt
    assert 'selection_trait_dimension 1' in txt
    assert 'selection_variance      1' in txt
    assert 'selection_local_optima' in txt
    assert '{-0.59999999999999998}' in txt and '{0.59999999999999998}' in txt
    assert m['selection_enabled'] is True and m['production_selection_mapping_authorized'] is False


def test_neutral_renderer_contains_no_selection_event_or_parameters(tmp_path:Path):
    effects,freq=_effects_freq()
    render_r37c_phase_ini(
        phase='FRAGMENTED_MATCHED_NEUTRAL',transitions=10,effect_a=effects,allele_frequencies=freq,
        population_size=500,seed=123,output_dir=tmp_path,chain_id='x',selection_enabled=False,
        selection_variance=None,optimum_amplitude=0.6,exchange_matrix=r37c_exchange_matrix('FRAGMENTED_MATCHED_NEUTRAL'),
    )
    txt=(tmp_path/'Nemo2_ARCANA_R37C.ini').read_text()
    assert 'viability_selection' not in txt
    assert 'selection_model' not in txt
    assert 'breed_disperse          2' in txt


def test_renderer_allows_fixed_alleles_at_phase_boundaries(tmp_path:Path):
    effects,freq=_effects_freq(); freq[0,0]=0; freq[1,1]=1
    render_r37c_phase_ini(
        phase='RECONNECTED_RELAXED',transitions=10,effect_a=effects,allele_frequencies=freq,
        population_size=500,seed=123,output_dir=tmp_path,chain_id='x',selection_enabled=False,
        selection_variance=None,optimum_amplitude=0.6,exchange_matrix=r37c_exchange_matrix('RECONNECTED_RELAXED'),
    )
    assert (tmp_path/'Nemo2_ARCANA_R37C.ini').exists()


def test_selection_renderer_rejects_missing_strength(tmp_path:Path):
    effects,freq=_effects_freq()
    try:
        render_r37c_phase_ini(
            phase='FRAGMENTED_DIVERGENT_SELECTION',transitions=10,effect_a=effects,allele_frequencies=freq,
            population_size=500,seed=123,output_dir=tmp_path,chain_id='x',selection_enabled=True,
            selection_variance=None,optimum_amplitude=0.6,exchange_matrix=r37c_exchange_matrix('FRAGMENTED_DIVERGENT_SELECTION'),
        )
    except ValueError:
        pass
    else:
        raise AssertionError('selected phase must fail closed without selection variance')

def test_synthetic_evidence_recovers_known_keff(tmp_path:Path):
    import json, zipfile
    from arcana_worldsim.scientific_engines.r37c_validation import analyze_r37c_selection_evidence
    base='selection_variance_1/N_500/rep_000/axis_0/'
    effects='trait_local_index\tarcana_trait_axis\tlocus\tadditive_effect_a\n0\t0\t0\t1\n0\t0\t1\t1\n'
    def qfreq(left,right):
        lines=['pop trait locus allele g10']
        for pop,p in [(1,left),(2,left),(3,right),(4,right)]:
            for locus in (1,2):
                lines.append(f'{pop} 1 {locus} 1 {p}')
        return '\n'.join(lines)+'\n'
    selected_frag='selected/phase_01_FRAGMENTED_DIVERGENT_SELECTION/selected.qfreq'
    neutral_frag='neutral/phase_01_FRAGMENTED_MATCHED_NEUTRAL/neutral.qfreq'
    selected_rec='selected/phase_02_RECONNECTED_RELAXED/selected_rec.qfreq'
    neutral_rec='neutral/phase_02_RECONNECTED_RELAXED/neutral_rec.qfreq'
    rec={
        'status':'ENGINE_COMPLETED_SELECTION_CHAIN','population_size':500,'replicate':0,'axis':0,'selection_variance':1.0,
        'selected_branch':{'fragmented':{'qfreq_relpath':selected_frag},'reconnected':{'qfreq_relpath':selected_rec}},
        'neutral_branch':{'fragmented':{'qfreq_relpath':neutral_frag},'reconnected':{'qfreq_relpath':neutral_rec}},
    }
    suite={'status':'NEMO_SELECTION_EVIDENCE_COMPLETE_REVIEW_REQUIRED','records':[rec]}
    zpath=tmp_path/'synthetic.zip'
    with zipfile.ZipFile(zpath,'w') as z:
        z.writestr('R3_7C_NEMO_SELECTION_SUITE_SUMMARY.json',json.dumps(suite))
        z.writestr(base+'qtl/qtl_effects.tsv',effects)
        z.writestr(base+selected_frag,qfreq(.4,.6))
        z.writestr(base+neutral_frag,qfreq(.5,.5))
        z.writestr(base+selected_rec,qfreq(.45,.55))
        z.writestr(base+neutral_rec,qfreq(.5,.5))
    out=analyze_r37c_selection_evidence(zpath)
    assert out['verdict']=='PASS_SELECTION_ORACLE_EVIDENCE_COMPLETE__K_EFF_RULE_REVIEW_REQUIRED'
    assert np.isclose(out['K_eff']['median'],2.0,rtol=0,atol=1e-12)
    assert np.isclose(out['reconnection_adaptive_S_retention']['median'],0.25,rtol=0,atol=1e-12)
    assert out['scalar_K_eff_authorized'] is False
