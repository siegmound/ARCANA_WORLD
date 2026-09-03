import pickle
import numpy as np
import pytest
from deep_production_runtime_v0_6C import *
from deep_heritable_selection_v0_6B import DeepHeritableConfig

BIO={
 'mode_load_weights':{'E':1.0,'th':0.7,'p':0.5,'I':0.2,'N':0.1},
 'regulation':{'baseline_operating_fraction':0.4,'acclimatized_operating_fraction':0.6,'load_reduction_gain':0.6},
 'tolerance_scale':{'intercept':0.5,'heritable_tolerance':1.0,'persistent_remodeling':0.4,'reversible_acclimatization_x_regulation':0.3},
 'threshold_base_load_units':{'L_min':0.01,'L_opt':0.02,'L_tol':0.04,'L_injury':0.08},
 'response':{'post_optimum_stimulus_floor_at_tolerance':0.2,'stress_at_tolerance':0.4,'injury_risk_at_injury_threshold_minus':0.8,'post_injury_exponential_steepness':2.0,'maintenance_cost':{'coupling':0.002,'regulation':0.001,'tolerance':0.001,'repair':0.001},'viability_stress_cost':1.0,'viability_injury_cost':2.0},
 'state_dynamics':{'acclimatization_tau_on_year':0.5,'acclimatization_tau_off_year':1.0,'recoverable_load_tau_year':3.0,'structural_remodeling_max_rate_per_year':0.08,'structural_atrophy_tau_year':20.0,'injury_repair_tau_year':5.0},
}

def toy(n=2):
    pop=np.ones((n,2,3)); opp=np.full((5,2,3),0.03); z=np.zeros((n,10)); x=np.zeros(n)
    return pop,opp,z,x

def test_physiology_zero_dt_exact_identity():
    pop,opp,z,x=toy(); a=np.array([.2,.4]); r=np.array([.1,.3]); q=np.array([.02,.05]); i=np.array([.01,.2])
    o=physiology_macrostep(pop,opp,z,BIO,a,r,q,i,0.0,DeepRuntimeConfig())
    assert np.array_equal(o['acclimatization'],a) and np.array_equal(o['remodeling'],r)
    assert np.array_equal(o['recoverable_load'],q) and np.array_equal(o['injury'],i)

def test_physiology_25k_is_bounded_and_converges_without_euler_overshoot():
    pop,opp,z,x=toy(); opp*=4
    o=physiology_macrostep(pop,opp,z,BIO,x,x,x,x,25_000.0,DeepRuntimeConfig())
    assert o['converged'] and o['iterations']<=128
    assert np.all((o['acclimatization']>=0)&(o['acclimatization']<=1))
    assert np.all((o['remodeling']>=0)&(o['remodeling']<=1))
    assert np.all((o['injury']>=0)&(o['injury']<=1))
    assert np.all(o['recoverable_load']>=0)

def test_long_macrostep_is_stable_under_step_split():
    pop,opp,z,x=toy(1); opp*=2.0; cfg=DeepRuntimeConfig(physiology_fixed_point_tolerance=1e-10)
    one=physiology_macrostep(pop,opp,z,BIO,x,x,x,x,1000.0,cfg)
    h=physiology_macrostep(pop,opp,z,BIO,x,x,x,x,500.0,cfg)
    two=physiology_macrostep(pop,opp,z,BIO,h['acclimatization'],h['remodeling'],h['recoverable_load'],h['injury'],500.0,cfg)
    for k in ('acclimatization','remodeling','recoverable_load','injury'):
        assert np.max(np.abs(one[k]-two[k]))<2e-5

def test_checkpoint_roundtrip_and_fingerprint_fail_closed():
    eq=np.ones((5,2,3))*10; fr={'equilibrium_background_energy_j':eq,'photo_equilibrium_energy_j':eq*.01,'source_buffer_j':eq*100}
    st=initialize_runtime_state(['a','b'],np.ones((2,3))*.01,np.ones((2,3)),fr,1.0,DeepHeritableConfig())
    pay=runtime_checkpoint_payload(st,{'d3':'abc','deep':'def'}); blob=pickle.dumps(pay); got=restore_runtime_checkpoint(pickle.loads(blob),{'d3':'abc','deep':'def'})
    assert np.array_equal(got.latent_mean,st.latent_mean) and got.deme_ids==st.deme_ids
    with pytest.raises(RuntimeError): restore_runtime_checkpoint(pay,{'d3':'WRONG','deep':'def'})

def test_fission_inheritance_and_extinction_drop():
    eq=np.ones((5,2,3))*10; fr={'equilibrium_background_energy_j':eq,'photo_equilibrium_energy_j':eq*.01,'source_buffer_j':eq*100}
    st=initialize_runtime_state(['a','b'],np.ones((2,3))*.01,np.ones((2,3)),fr,1.0,DeepHeritableConfig()); st.latent_mean[0,0]=0.7; st.injury[0]=.2
    out=reconcile_deme_state(st,['a','a_F01'],[{'parent_deme_id':'a','daughter_deme_id':'a_F01'}])
    assert out.deme_ids==['a','a_F01'] and out.latent_mean[1,0]==.7 and out.injury[1]==.2
    assert 'b' not in out.deme_ids

def test_unknown_birth_without_d3_fission_fails_closed():
    eq=np.ones((5,2,3)); fr={'equilibrium_background_energy_j':eq,'photo_equilibrium_energy_j':eq*.01,'source_buffer_j':eq*100}
    st=initialize_runtime_state(['a'],np.ones((1,3))*.01,np.ones((1,3)),fr,1.0,DeepHeritableConfig())
    with pytest.raises(RuntimeError): reconcile_deme_state(st,['a','x'],[])

def test_historical_binder_rejects_non_210_and_non_d3_object():
    with pytest.raises(RuntimeError): bind_historical_210ma(object(),physical_age_ma=66.0)
    with pytest.raises(RuntimeError): bind_historical_210ma(object(),physical_age_ma=210.0)

def test_effective_opportunity_tracks_depletion_and_photo_separately():
    eq=np.ones((5,2,3))*10; peq=np.zeros_like(eq); peq[:2]=2
    fr={'A_X':np.ones_like(eq),'u_base_dfeu':np.ones(5),'photo_u_dfeu':np.array([.2,.2,0,0,0]),'equilibrium_background_energy_j':eq,'photo_equilibrium_energy_j':peq,'source_buffer_j':eq*10}
    st=initialize_runtime_state(['a'],np.ones((1,3))*.01,np.ones((1,3)),fr,0.0,DeepHeritableConfig()); st.surface_background_energy_j*=.5
    o=effective_mode_opportunity(st,fr)
    assert np.allclose(o[0],.7) and np.allclose(o[2],.5)

def test_area_weights_close():
    w=area_weights_from_lat(np.linspace(-89,89,90),180); assert abs(float(w.sum())-1)<1e-14 and np.all(w>=0)
