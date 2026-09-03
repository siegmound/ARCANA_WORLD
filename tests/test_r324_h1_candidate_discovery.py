import numpy as np
from arcana_worldsim.scientific_engines.r324_h1_candidate_discovery import (
    CORE_AXES, SHORTLIST_N, THRESHOLD_GRID, percentile_rank_members, pareto_front_mask,
    _axis_scores, _average_rank_desc, selection_diagnostics, criteria_authority, TRAITS
)

def test_core_axis_count_and_nonempty():
    assert len(CORE_AXES)==7
    assert all(CORE_AXES.values())

def test_h2_reproductive_output_not_monotone_gate():
    assert 'H2_reproductive_output_rate' not in CORE_AXES['life_history_learning_support']

def test_no_homo_similarity_target():
    a=criteria_authority()
    assert a['human_similarity_target'] is False
    assert a['h1_functional_readiness_target'] is True
    assert a['backpropagation_to_r323'] is False

def test_no_single_readiness_score():
    assert criteria_authority()['candidate_selection']['no_single_readiness_score'] is True

def test_percentile_rank_members_bounds_and_order():
    x=np.array([[1.,2.,3.],[3.,1.,2.]])
    p=percentile_rank_members(x)
    assert np.all((p>0)&(p<1))
    assert p[0,0]<p[0,1]<p[0,2]

def test_percentile_rank_ties_average():
    x=np.array([[1.,1.,2.,3.]])
    p=percentile_rank_members(x)
    assert p[0,0]==p[0,1]

def test_pareto_front_simple():
    v=np.array([[1.,1.],[2.,2.],[3.,0.]])
    f=pareto_front_mask(v)
    assert f.tolist()==[False,True,True]

def test_average_rank_desc():
    r=_average_rank_desc(np.array([5.,2.,5.]))
    assert r[0]==r[2]==1.5 and r[1]==3.0

def test_axis_score_geometry():
    rng=np.random.default_rng(1)
    F=rng.normal(size=(5,8,31))
    names,a=_axis_scores(F,TRAITS,CORE_AXES)
    assert len(names)==7 and a.shape==(5,8,7)
    assert np.all((a>0)&(a<1))

def test_selection_diagnostics_deterministic_order():
    rng=np.random.default_rng(2)
    core=rng.random((12,20,7))*0.98+0.01
    t=rng.random((12,20))*0.98+0.01
    q=rng.random((12,20))*0.98+0.01
    rr=np.array(['A']*4+['B']*4+['C']*4)
    ids=[f'S{i:02d}' for i in range(20)]
    a=selection_diagnostics(core,t,q,rr,ids)
    b=selection_diagnostics(core,t,q,rr,ids)
    assert a['order_species']==b['order_species']
    assert len(set(a['order_species']))==20

def test_threshold_grid_is_sensitivity_grid():
    assert THRESHOLD_GRID==(0.30,0.35,0.40,0.45,0.50)
    assert criteria_authority()['candidate_selection']['no_absolute_pass_fail_human_threshold'] is True

def test_shortlist_size_precommitted():
    assert SHORTLIST_N==12
