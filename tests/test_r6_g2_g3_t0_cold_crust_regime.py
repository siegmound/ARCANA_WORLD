"""Synthetic-only unit verification for original T0 cold crust diagnostic mathematics.

No synthetic source is treated as actual ARCANA lithology or fault stress.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PATH=Path(__file__).resolve().parents[1]/'experiments/plate58_deforming_explore_v1/g2_g3_t0_cold_crust_regime.py'
spec=importlib.util.spec_from_file_location('test_cold_crust',PATH)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def pre(*,H=1000.,c0=300.,c1=0.,c2=0.,c3=0.,rho=2750.):
    return {'layer1_z0_m':0.,'layer1_z1_m':H,'layer1_c0_k':c0,
            'layer1_c1_k_m':c1,'layer1_c2_k_m2':c2,
            'layer1_c3_k_m3':c3,'crust_thickness_m':H,
            'crust_density_kg_m3':rho}


def pt(p,g=9.82):
    return {'constitutive_law_assigned':False,
            'actual_vertical_stress_pa':None,'effective_pressure_pa':None,
            'pore_pressure_pa':None,'fault_normal_pressure_pa':None,
            'conditional_moho_delta_overburden_pa':p['crust_density_kg_m3']*g*p['crust_thickness_m'],
            'exact_PRE_temperature_bounds_k':{'crust':[min(p['layer1_c0_k'],p['layer1_c0_k']+p['layer1_c1_k_m']*p['crust_thickness_m']),
                                                      max(p['layer1_c0_k'],p['layer1_c0_k']+p['layer1_c1_k_m']*p['crust_thickness_m'])]},
            'terrestrial_GT95_lab_temperature_only_coverage':{'crust':{
                'temperature_only_some_overlap':False,
                'temperature_only_full_layer_covered':False}}}


@pytest.mark.parametrize('c0,c1,expected',[
  (300.,0.,[]), (523.15,0.,[[0.,1000.]]), (623.15,0.,[[0.,1000.]]),
  (573.15,0.,[[0.,1000.]]), (650.,0.,[]), (522.,0.,[]),
  (500.,.2,[[115.75,615.75]]), (520.,.15,[[21.,687.6666666666666]]),
  (623.,-.2,[[0.,499.25]]), (800.,-.3,[[589.5,922.8333333333334]]),
  (500.,.02315,[]), (700.,-.08,[[960.625,1000.]]), (523.15,.1,[[0.,1000.]]),
  (623.15,-.1,[[0.,1000.]])
])
def test_constant_and_linear_temperature_windows(c0,c1,expected):
    got=m.temperature_window_segments(pre(c0=c0,c1=c1))
    assert len(got)==len(expected)
    for row,target in zip(got,expected):
        assert row==pytest.approx(target,abs=1e-4)


def test_nonmonotone_cubic_two_disjoint_intervals():
    # T(t)=500 + 640t - 640t², peak 660 K at t=.5, edges 500 K.
    p=pre(c0=500.,c1=.64,c2=-.00064)
    seg=m.temperature_window_segments(p)
    assert len(seg)==2
    assert 0<seg[0][0]<seg[0][1]<500
    assert 500<seg[1][0]<seg[1][1]<1000
    for a,b in seg:
        assert 523.15-1e-6<=m._at(m._poly(p),(a+b)/(2*1000))<=623.15+1e-6


def test_cubic_interior_extremum_all_below_context_window():
    p=pre(c0=400.,c1=.1,c2=-.0001)
    assert m.temperature_window_segments(p)==[]


def test_temperature_interval_touch_at_local_max_no_positive_width():
    p=pre(c0=400.,c1=.5,c2=-.0005)  # peak 525 at middle; window at 525 only
    assert m.temperature_window_segments(p,(525.,550.))==[]


@pytest.mark.parametrize('change',[
    'no_density','bad_density','bad_thickness','bad_layer_extent',
    'negative_temperature','nonfinite_coefficient','nonzero_surface',
])
def test_invalid_source_pre_fails_closed(change):
    p=pre()
    if change=='no_density':del p['crust_density_kg_m3']
    elif change=='bad_density':p['crust_density_kg_m3']=0.
    elif change=='bad_thickness':p['crust_thickness_m']=-1.
    elif change=='bad_layer_extent':p['layer1_z1_m']=500.
    elif change=='negative_temperature':p['layer1_c0_k']=-1.
    elif change=='nonfinite_coefficient':p['layer1_c3_k_m3']=float('nan')
    elif change=='nonzero_surface':p['layer1_z0_m']=1.
    with pytest.raises(m.ColdCrustInputError):
        m.temperature_window_segments(p)


@pytest.mark.parametrize('window',[(700.,600.),(500.,500.),[0.,600.],
                                   [500.,float('nan')],(500.,600.,700.)])
def test_invalid_earth_window_fails_closed(window):
    with pytest.raises(m.ColdCrustInputError):
        m.temperature_window_segments(pre(),window)


@pytest.mark.parametrize('pressure,expected',[
    (1e8,85e6),(2e8,170e6),(3e8,230e6),(1.7e9,1.07e9)])
def test_byerlee_curve(pressure,expected):
    assert m.byerlee_reference_shear_pa(pressure,earth_analogue_only=True)==pytest.approx(expected)


@pytest.mark.parametrize('pressure,permit',[(None,True),(0.,True),(-1.,True),
                                           (float('nan'),True),(2e9,True),
                                           (1e8,False)])
def test_byerlee_no_implicit_earth_to_arcana(pressure,permit):
    with pytest.raises(m.ColdCrustInputError):
        m.byerlee_reference_shear_pa(pressure,earth_analogue_only=permit)


def test_evaluate_column_requires_null_true_pressure_and_material():
    p=pre(c0=500.,c1=.2);node=pt(p)
    r=m.evaluate_column(p,node,gravity_m_s2=9.82)
    assert r['earth_BPT_temperature_intersects_crust_by_positive_width']
    assert r['source_node_lithology'] is None
    assert r['source_pore_pressure_pa'] is None
    assert r['source_effective_fault_normal_stress_pa'] is None
    assert r['selected_brittle_law'] is None and r['selected_ductile_law'] is None
    assert r['model_regime_assignment']=='UNDETERMINED'
    span=r['earth_quartz_rich_BPT_temperature_only_intervals'][0]
    assert span['conditional_delta_sigma_v_pa_interval']==pytest.approx(
        [2750*9.82*z for z in span['depth_interval_m']])


@pytest.mark.parametrize('attack',[
    'effective_pressure_pa','pore_pressure_pa','fault_normal_pressure_pa',
    'actual_vertical_stress_pa','constitutive_law_assigned',
    'conditional_moho_delta_overburden_pa'
])
def test_evaluate_column_rejects_unauthorized_source_pressure(attack):
    p=pre(c0=500.,c1=.2);n=pt(p)
    n[attack]=True if attack=='constitutive_law_assigned' else 5.0
    with pytest.raises(m.ColdCrustInputError):m.evaluate_column(p,n,gravity_m_s2=9.82)


def test_evaluate_column_rejects_zero_gravity():
    p=pre();n=pt(p)
    with pytest.raises(m.ColdCrustInputError):m.evaluate_column(p,n,gravity_m_s2=0.)


def test_write_once_manifest_and_nocanon(tmp_path):
    root=tmp_path/'repo';root.mkdir()
    out=tmp_path/'external'
    docs={name:{'physical_T1':None,'mechanical_solve_authorized':False,
                'HistoryStore_modified':False,'D_024':'ACTIVE',
                'source_pt_manifest_sha256':'a'*64} for name in m.FILES}
    man=m.write_once(root,out,docs)
    assert man['no_solver_run'] and man['physical_T1'] is None
    assert set(man['files'])==set(m.FILES)
    for name,digest in man['files'].items():
        assert hashlib.sha256((out/name).read_bytes()).hexdigest()==digest
    with pytest.raises(m.ColdCrustInputError):m.write_once(root,out,docs)
    with pytest.raises(m.ColdCrustInputError):m.write_once(root,root/'child',docs)


def test_write_once_rejects_physical_authority(tmp_path):
    docs={name:{'physical_T1':None,'mechanical_solve_authorized':False,
                'HistoryStore_modified':False,'D_024':'ACTIVE'} for name in m.FILES}
    docs['AUDIT.json']['physical_T1']=42
    with pytest.raises(m.ColdCrustInputError):m.write_once(tmp_path,tmp_path.parent/'new',docs)


def test_original_PT_reopen_sha_and_rulestate(tmp_path):
    folder=tmp_path/'PT';folder.mkdir()
    bodies={'REGION_8X8_SOURCE_PT.json':{'original_T0_source_nodes':{'1':{}}},
            'REGION_16X16_SOURCE_PT.json':{'original_T0_source_nodes':{'1':{}}},
            'AUDIT.json':{'mechanical_solve_authorized':False,'physical_T1':None,
                          'D_024':'ACTIVE','physical_G2_material_law_or_rock_selected':False}}
    for name,obj in bodies.items(): (folder/name).write_text(json.dumps(obj)+'\n')
    manifest={'schema':'ARCANA_R6_G2_G3_CONDITIONAL_PT_REFERENCE_MANIFEST_V1',
             'no_solver_run':True,'physical_T1':None,'HistoryStore_modified':False,
             'D_024':'ACTIVE','WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,
             'files':{name:m.sha256(folder/name) for name in bodies}}
    (folder/'MANIFEST.json').write_text(json.dumps(manifest))
    a,b,c=m._load_original_pt(folder)
    assert len(b)==2 and c==bodies['AUDIT.json']
    (folder/'AUDIT.json').write_text('{}')
    with pytest.raises(m.ColdCrustInputError,match='HASH_DRIFT'):
        m._load_original_pt(folder)


def test_original_PT_reopen_blocks_promoted_solve(tmp_path):
    folder=tmp_path/'PT';folder.mkdir()
    bodies={name:{} for name in m.SOURCE_PT_FILES}
    for name,obj in bodies.items():(folder/name).write_text(json.dumps(obj))
    manifest={'schema':'ARCANA_R6_G2_G3_CONDITIONAL_PT_REFERENCE_MANIFEST_V1',
             'no_solver_run':False,'physical_T1':None,'HistoryStore_modified':False,
             'D_024':'ACTIVE','WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,
             'files':{name:m.sha256(folder/name) for name in bodies}}
    (folder/'MANIFEST.json').write_text(json.dumps(manifest))
    with pytest.raises(m.ColdCrustInputError,match='MANIFEST_NOT_FAIR_SCOPE'):
        m._load_original_pt(folder)
