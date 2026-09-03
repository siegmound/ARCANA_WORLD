import numpy as np
from arcana_worldsim.state_query import r51_structure as s


def test_reconstruct_components_is_nested_under_fixed_thresholds():
    mass=np.zeros((5,6),float)
    mass[1,1]=1; mass[1,2]=2; mass[2,2]=3; mass[3,4]=4; mass[3,5]=5
    land=np.ones_like(mass)
    comps=s._reconstruct_components(mass,land)
    qs=list(s.THRESHOLDS)
    for i in range(1,len(qs)):
        prev=set().union(*comps[qs[i-1]]) if comps[qs[i-1]] else set()
        cur=set().union(*comps[qs[i]]) if comps[qs[i]] else set()
        assert cur <= prev


def test_family_tracking_survives_all_thresholds_for_peak_cell():
    mass=np.zeros((6,6),float)
    # one connected gradient; maximum cell must survive every quantile
    vals=[1,2,3,4,5,6,7,8]
    cells=[(2,1),(2,2),(2,3),(2,4),(3,4),(3,3),(3,2),(3,1)]
    for v,(r,c) in zip(vals,cells): mass[r,c]=v
    fams,_=s._build_families_for_candidate('X',mass,np.ones_like(mass))
    assert any(f['survives_all_thresholds'] for f in fams)
    assert all(f['highest_threshold_quantile'] in s.THRESHOLDS for f in fams)


def test_engine_gate_ready_defers_rangeshifter_to_r52():
    p={'A':{'all_threshold_family_count':1},'B':{'all_threshold_family_count':2}}
    d=s.adjudicate_engine_use(p,('A','B'))
    assert d['closure_readiness']=='READY_FOR_R51_SEAL_NO_NEW_EXTERNAL_ENGINE_REQUIRED'
    assert d['engine_adjudication']['new_external_engine_execution_authorized_in_r51'] is False
    assert d['engine_adjudication']['RangeShifter']['action']=='DEFER_NEW_EXECUTION_TO_R5_2_TARGETED_CORRIDOR_VALIDATION'


def test_engine_gate_internal_gap_does_not_use_external_engine_as_repair():
    p={'A':{'all_threshold_family_count':1},'B':{'all_threshold_family_count':0}}
    d=s.adjudicate_engine_use(p,('A','B'))
    assert d['closure_readiness']=='R51_INTERNAL_SPATIAL_METHOD_REFINEMENT_REQUIRED_BEFORE_SEAL'
    assert d['engine_adjudication']['RangeShifter']['action']=='DO_NOT_RUN_FOR_R51_METHOD_REPAIR'
    assert d['engine_adjudication']['new_external_engine_execution_required_for_r51_closure'] is False


def test_longest_true_run_is_sample_based_not_continuous_claim():
    x=np.array([False,True,True,False,True,True,True,False])
    assert s._longest_true_run(x)==3
