from __future__ import annotations
from pathlib import Path
import numpy as np
from arcana_worldsim.scientific_engines.nemo242_r37a import (
    canonical_r37a_b2_phases,b2_nemo_transition,render_r37a_b2_phase_ini,b2_reduced_order_deterministic_trajectory
)
from arcana_worldsim.scientific_engines.segregation_aware_admixture import qtl_segregation_potential

def test_b2_phase_schedule_is_connected_fragmented_reconnected():
    p=canonical_r37a_b2_phases()
    assert [x.name for x in p]==['CONNECTED_BURNIN','FRAGMENTED','RECONNECTED']
    assert [x.transitions for x in p]==[250,400,550]

def test_b2_transition_is_doubly_stochastic():
    for ph in canonical_r37a_b2_phases():
        m=b2_nemo_transition(ph.exchange_matrix)
        assert np.allclose(m.sum(0),1)
        assert np.allclose(m.sum(1),1)
        assert np.all(m>=0)

def test_b2_renderer_uses_exact_nemo_242_frequency_state_contract(tmp_path:Path):
    ph=canonical_r37a_b2_phases()[0]
    effects=np.array([0.01,0.02,0.03,0.04])
    freq=np.full((4,4),0.5)
    man=render_r37a_b2_phase_ini(phase=ph,effect_a=effects,allele_frequencies=freq,population_size=500,seed=123,output_dir=tmp_path,chain_id='x')
    txt=(tmp_path/'Nemo2_ARCANA_R37A_B2.ini').read_text()
    assert 'quanti_loci             4' in txt
    assert 'quanti_mutation_rate    0' in txt
    assert 'quanti_recombination_rate 0.5' in txt
    assert f'generations             {ph.transitions+1}' in txt
    assert man['nemo_required_version']=='2.4.2'
    assert not man['canonical_write_allowed']

def test_b2_deterministic_reconnection_contracts_segregation_distance():
    effects=np.array([[0.02,0.03,0.04,0.05]])
    freq=np.array([[[.2,.25,.3,.35]],[[.35,.4,.45,.5]],[[.65,.6,.55,.5]],[[.8,.75,.7,.65]]])
    s=qtl_segregation_potential(effects,freq)
    tr=b2_reduced_order_deterministic_trajectory(s)
    # fragmentation may preserve/increase relative structure, but reconnection must contract it.
    assert tr[-1]['mean_pair_S'] < tr[1]['mean_pair_S']
    assert all(not x['canonical_write_allowed'] for x in tr)
