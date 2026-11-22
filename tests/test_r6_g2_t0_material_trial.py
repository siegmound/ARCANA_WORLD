"""Original-T0 material/fluid exploratory screening: synthetic laws ONLY."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from experiments.plate58_deforming_explore_v1 import g2_t0_material_trial as m


def brittle():
    return {
        'kind':'CONTINUUM_3D_DRUCKER_PRAGER',
        'pressure_convention':'ASPECT_RHEOLOGY_DP_3D_6P',
        'stress_output':'ASPECT_CONTINUUM_J2_EQUIVALENT_PA',
        'authority':m.AUTHORITY,
        'source':{'authority':'EXTERNAL_CANDIDATE_NOT_ORIGINAL_T0',
                  'reference':'SYNTHETIC_UNIT_TEST_NOT_LAB_SOURCE'},
        'cohesion_pa':2e7, 'friction_angle_deg':25.,
        'valid_temperature_k':[250.,1100.],
        'valid_effective_pressure_pa':[0.,1.2e9],
        'valid_strain_rate_s_inv':[1e-18,1e-8],
    }


def creep():
    return {
        'kind':'DISLOCATION_CREEP_POWER_LAW',
        'stress_convention':'TRIAXIAL_DIFFERENTIAL_STRESS_PA',
        'authority':m.AUTHORITY,
        'source':{'authority':'EXTERNAL_LAB_CALIBRATION_CANDIDATE_UNVERIFIED',
                  'source_sha256':'1'*64,
                  'reference':'SYNTHETIC_UNIT_TEST_NOT_MEASURED_DATA'},
        'A_pa_minus_n_s_inv':1e-20,'n':3.,'E_j_mol':200000.,'V_m3_mol':1e-6,
        'water_exponent':0., 'water_fugacity_pa':None,
        'reference_fugacity_pa':None,
        'valid_temperature_k':[250.,1100.],
        'valid_confining_pressure_pa':[0.,1.2e9],
        'valid_strain_rate_s_inv':[1e-18,1e-8],
    }


def candidate():
    return {
        'authority':m.AUTHORITY,'authorial_exploration_selected':True,
        'physical_rock_identity_ratified':False,
        'authorial_record':'SYNTHETIC_UNIT_TEST_NOT_AUTHOR_RATIFICATION',
        'bulk_oxide_hypothesis_id':'OX_SYNTHETIC',
        'phase_assemblage_hypothesis':'QUARTZ_FELDSPAR_TEST_NOT_T0',
        'hydration_hypothesis':'WATER_TEST_CONDITIONAL',
        'conditions':{
            'authority':'AUTHORIAL_CONDITIONAL_UNOBSERVED',
            'surface_pressure_is_observed':False,
            'pore_pressure_is_observed':False,
            'independently_qualified_fault_normal':False,
            'surface_total_pressure_pa':1e8,
            'surface_pore_pressure_pa':1e7,
            'moho_pore_pressure_pa':2e8,
            'biot_coefficient':0.7,
            'strain_rate_s_inv':1e-13,
        },
        'continuum_brittle':brittle(),
        'triaxial_ductile':creep(),
    }


def source_node():
    pt={'conditional_moho_delta_overburden_pa':8e8,
        'exact_PRE_temperature_bounds_k':{'crust':[280.,780.]},
        'pore_pressure_pa':None,'fault_normal_pressure_pa':None,
        'constitutive_law_assigned':False}
    cold={'source_node_lithology':None,'model_regime_assignment':'UNDETERMINED'}
    return pt,cold


def fail(fn,tag):
    with pytest.raises(m.MaterialTrialError,match=tag):fn()


def test_pressure_brittle_continuum_positive():
    assert m.continuum_dp_strength_pa(1e8,brittle(),temperature_k=300,strain_rate_s_inv=1e-13)>0


def test_frictional_strength_increases_with_effective_pressure():
    a=m.continuum_dp_strength_pa(2e8,brittle(),temperature_k=300,strain_rate_s_inv=1e-13)
    b=m.continuum_dp_strength_pa(6e8,brittle(),temperature_k=300,strain_rate_s_inv=1e-13)
    assert a<b


def test_synthetic_noncanonical_laws_compute_distinct_stress_conventions():
    pt,cold=source_node()
    q=m.evaluate_candidate_node(pt,cold,candidate())
    assert q['all_three_lab_T_P_rate_ranges_cover_conditional_column'] is True
    assert q['actual_pore_pressure_verified'] is False
    assert q['physical_T1'] is None
    assert q['candidate_triaxial_diff_creep_strength_pa_min_max'][0]>0
    assert q['no_comparison_between_distinct_stress_invariants'] is True


def test_arrhenius_temperature_decreases_candidate_stress():
    x=m.creep_differential_stress_pa(creep(),T_k=350,pressure_pa=1e8,rate_s_inv=1e-13)
    y=m.creep_differential_stress_pa(creep(),T_k=650,pressure_pa=1e8,rate_s_inv=1e-13)
    assert y<x


def test_creep_strain_rate_increases_strength():
    x=m.creep_differential_stress_pa(creep(),T_k=550,pressure_pa=1e8,rate_s_inv=1e-14)
    y=m.creep_differential_stress_pa(creep(),T_k=550,pressure_pa=1e8,rate_s_inv=1e-12)
    assert x<y


def test_creep_pressure_increases_strength_for_positive_activation_volume():
    x=m.creep_differential_stress_pa(creep(),T_k=550,pressure_pa=1e8,rate_s_inv=1e-13)
    y=m.creep_differential_stress_pa(creep(),T_k=550,pressure_pa=8e8,rate_s_inv=1e-13)
    assert x<y


@pytest.mark.parametrize('alter,error',[ 
    ('no_auth','MATERIAL_EXPLICIT_NONCANONICAL'),
    ('promote_rock','MATERIAL_EXPLICIT_NONCANONICAL'),
    ('no_author_record','MATERIAL_EXPLICIT_NONCANONICAL'),
    ('no_phase','MATERIAL_EXPLICIT_NONCANONICAL'),
    ('no_hydration','MATERIAL_EXPLICIT_NONCANONICAL'),
    ('claim_pressure_observed','MATERIAL_UNQUALIFIED_PHYSICAL_PRESSURE'),
    ('claim_pore_observed','MATERIAL_UNQUALIFIED_PHYSICAL_PRESSURE'),
    ('claim_fault_pressure','MATERIAL_UNQUALIFIED_PHYSICAL_PRESSURE'),
    ('no_surface_pressure','MATERIAL_NONFINITE_EXPLICIT_SURFACE_P'),
    ('pore_exceeds_surface','MATERIAL_PORE_EXCEEDS'),
    ('negative_pore','MATERIAL_VALUE_OUTSIDE_EXPLICIT_SURFACE_PORE'),
    ('negative_biot','MATERIAL_VALUE_OUTSIDE_EXPLICIT_BIOT'),
    ('rate_zero','MATERIAL_VALUE_OUTSIDE_EXPLICIT_STRAIN_RATE'),
    ('GT95_for_cold','MATERIAL_FULL_COLD_CRUST_LAB_T_NOT_COVERED'),
    ('creep_T_limit','MATERIAL_FULL_COLD_CRUST_LAB_T_NOT_COVERED'),
    ('creep_P_limit','MATERIAL_FULL_COLD_CRUST_LAB_P_NOT_COVERED'),
    ('creep_rate_limit','MATERIAL_FULL_COLD_CRUST_LAB_RATE_NOT_COVERED'),
    ('invalid_creep_invariant','MATERIAL_CREEP_STRESS_CONVENTION_INVALID'),
    ('invalid_dp_invariant','MATERIAL_BRITTLE_CONVENTION_INVALID'),
    ('fake_lab_data_source','MATERIAL_CREEP_INDEPENDENT_MEASURED_DATA'),
    ('fabricated_fault_pressure','MATERIAL_SOURCE_ALREADY_HAS_UNVERIFIED_AUTHORITY'),
    ('fabricated_real_lithology','MATERIAL_SOURCE_ALREADY_HAS_UNVERIFIED_AUTHORITY'),
])
def test_explicit_trial_fail_closed(alter,error):
    pt,cold=source_node();x=candidate()
    if alter=='no_auth': x['authorial_exploration_selected']=False
    if alter=='promote_rock': x['physical_rock_identity_ratified']=True
    if alter=='no_author_record': x['authorial_record']='x'
    if alter=='no_phase': x['phase_assemblage_hypothesis']=None
    if alter=='no_hydration': x['hydration_hypothesis']=None
    if alter=='claim_pressure_observed': x['conditions']['surface_pressure_is_observed']=True
    if alter=='claim_pore_observed': x['conditions']['pore_pressure_is_observed']=True
    if alter=='claim_fault_pressure': x['conditions']['independently_qualified_fault_normal']=True
    if alter=='no_surface_pressure': x['conditions']['surface_total_pressure_pa']=None
    if alter=='pore_exceeds_surface': x['conditions']['surface_pore_pressure_pa']=2e8
    if alter=='negative_pore': x['conditions']['surface_pore_pressure_pa']=-1
    if alter=='negative_biot': x['conditions']['biot_coefficient']=-.2
    if alter=='rate_zero': x['conditions']['strain_rate_s_inv']=0
    if alter=='GT95_for_cold': x['continuum_brittle']['valid_temperature_k']=[1173.15,1373.15]
    if alter=='creep_T_limit': x['triaxial_ductile']['valid_temperature_k']=[500,1100]
    if alter=='creep_P_limit': x['triaxial_ductile']['valid_confining_pressure_pa']=[0,2e8]
    if alter=='creep_rate_limit': x['triaxial_ductile']['valid_strain_rate_s_inv']=[1e-10,1e-9]
    if alter=='invalid_creep_invariant': x['triaxial_ductile']['stress_convention']='ASPECT_J2_INVARIANT'
    if alter=='invalid_dp_invariant': x['continuum_brittle']['pressure_convention']='ASPECT_LEGACY_VISCOPLASTIC_3D_2P'
    if alter=='fake_lab_data_source': x['triaxial_ductile']['source']['source_sha256']='missing'
    if alter=='fabricated_fault_pressure': pt['fault_normal_pressure_pa']=1e8
    if alter=='fabricated_real_lithology': cold['source_node_lithology']='GRANITE'
    fail(lambda:m.evaluate_candidate_node(pt,cold,x),error)


@pytest.mark.parametrize('kind',[ 
    'GT95_CREEP_LOWER_THAN_T0','CREEP_PRESSURE_TOO_HIGH',
    'BRITTLE_EFFECTIVE_P_OUTSIDE','BRITTLE_STRAIN_RATE_OUTSIDE',
    'NEGATIVE_COHESION','CREEP_WATER_NOT_CONSTRAINED',
    'OVERFLOW_CREEP','BRITTLE_UNKNOWN_SOURCE',
])
def test_individual_law_invalidity(kind):
    b=brittle();c=creep()
    if kind=='GT95_CREEP_LOWER_THAN_T0':
        fail(lambda:m.creep_differential_stress_pa(c,T_k=1200,pressure_pa=2e8,rate_s_inv=1e-13),'MATERIAL_CREEP_OUTSIDE_LAB_DOMAIN')
    if kind=='CREEP_PRESSURE_TOO_HIGH':
        fail(lambda:m.creep_differential_stress_pa(c,T_k=500,pressure_pa=2e9,rate_s_inv=1e-13),'MATERIAL_CREEP_OUTSIDE_LAB_DOMAIN')
    if kind=='BRITTLE_EFFECTIVE_P_OUTSIDE':
        fail(lambda:m.continuum_dp_strength_pa(1.5e9,b,temperature_k=300,strain_rate_s_inv=1e-13),'MATERIAL_BRITTLE_OUTSIDE_LAB_DOMAIN')
    if kind=='BRITTLE_STRAIN_RATE_OUTSIDE':
        fail(lambda:m.continuum_dp_strength_pa(1e8,b,temperature_k=300,strain_rate_s_inv=1e-4),'MATERIAL_BRITTLE_OUTSIDE_LAB_DOMAIN')
    if kind=='NEGATIVE_COHESION':
        b['cohesion_pa']=-1
        fail(lambda:m.review_brittle_law(b),'MATERIAL_VALUE_OUTSIDE_COHESION')
    if kind=='CREEP_WATER_NOT_CONSTRAINED':
        c['water_exponent']=1
        fail(lambda:m.review_creep_law(c),'MATERIAL_NONFINITE_WATER_FUGACITY')
    if kind=='OVERFLOW_CREEP':
        c['A_pa_minus_n_s_inv']=1e-300;c['n']=1;c['E_j_mol']=1e9
        fail(lambda:m.creep_differential_stress_pa(c,T_k=280,pressure_pa=1e9,rate_s_inv=1e-13),'MATERIAL_CREEP_NUMERIC_OVERFLOW')
    if kind=='BRITTLE_UNKNOWN_SOURCE':
        b['source']['reference']='x'
        fail(lambda:m.review_brittle_law(b),'MATERIAL_BRITTLE_LAB_PROVENANCE_REQUIRED')


def fake_source(extent):
    ids=list(range(1,(extent+1)**2+1))
    nodes={str(n):{
        'exact_PRE_temperature_bounds_k':{'crust':[280.,780.]},
        'conditional_moho_delta_overburden_pa':8e8}
        for n in ids}
    pt={'original_parent_node_order':ids,'original_T0_source_nodes':nodes}
    cold={'extent_cells':extent,'source_parent_ids':ids,
          'original_T0_source_nodes':{str(n):{} for n in ids},
          'source_original_FEG_sha256':'f'*64,
          'source_original_PRE_sha256':'e'*64,
          'source_actual_local_triple_plate_junctions':(
              [] if extent==8 else [{'parent_node_id':34587,
                                       'incident_plates':[5,8,11]}])}
    return cold,pt


def test_unselected_template_source_81_289_exact_parent_ids():
    for n in (8,16):
        cold,pt=fake_source(n)
        t=m.template_for_source(cold,pt)
        assert t['unselected_source_template_not_executable'] is True
        assert len(t['material_assignment_by_original_parent'])==(n+1)**2
        assert all(x is None for x in t['material_assignment_by_original_parent'].values())
        assert t['physical_T1'] is None
    assert t['shared_parent_nodes_not_side_resolved_rock_materials'] is True


@pytest.mark.parametrize('change',['different_ids','missing_cold_node','missing_pt_node','wrong_extent'])
def test_template_fails_closed_on_original_parent_drift(change):
    c,pt=fake_source(8)
    if change=='different_ids':pt['original_parent_node_order'][-1]=123456
    if change=='missing_cold_node':del c['original_T0_source_nodes']['1']
    if change=='missing_pt_node':del pt['original_T0_source_nodes']['1']
    if change=='wrong_extent':c['extent_cells']=12
    fail(lambda:m.template_for_source(c,pt),'MATERIAL_COLD_PT_EXACT_SOURCE_IDS_MISMATCH')


def synthetic_reports():
    objects={}
    for n in (8,16):
        c,pt=fake_source(n)
        t=m.template_for_source(c,pt)
        t['source_cold_report_sha256']='d'*64
        t['source_PT_report_sha256']='b'*64
        objects[f'MATERIAL_{n}X{n}_UNSELECTED.json']=t
    objects['AUDIT.json']={
        'schema':'ARCANA_R6_G2_T0_MATERIAL_TRIAL_SOURCE_AUDIT_V1',
        'source_8x8_material_assignments':0,'source_16x16_material_assignments':0,
        'source_pore_pressure_assignments':0,
        'qualified_cold_T_P_rate_constitutive_laws':0,
        'physical_mineral_phases_selected':0,'physical_T1':None,
        'mechanical_solve_authorized':False,'HistoryStore_modified':False,
        'D_024':'ACTIVE','WORLD_HISTORY_PRODUCTION_AUTHORIZED':False}
    return objects


def test_write_once_off_repo_and_integrity(tmp_path):
    objs=synthetic_reports()
    root=tmp_path/'repo';root.mkdir()
    target=tmp_path/'external'
    m.write_once(root,target,objs)
    assert (target/'MANIFEST.json').is_file()
    dig=json.loads((target/'MANIFEST.json').read_text())
    assert all(m.sha(target/name)==value for name,value in dig['files'].items())
    fail(lambda:m.write_once(root,target,objs),'MATERIAL_OUTPUT_INSIDE_REPOSITORY_OR_ALREADY_EXISTS')
    fail(lambda:m.write_once(root,root/'internal',objs),'MATERIAL_OUTPUT_INSIDE_REPOSITORY_OR_ALREADY_EXISTS')


@pytest.mark.parametrize('change',[ 'one_assigned_node','fake_phase','fake_pore',
                                    'pretend_authorial','fake_law','fake_material_audit'])
def test_write_once_refuses_forged_source_material_authority(tmp_path,change):
    root=tmp_path/'repo';root.mkdir()
    objs=synthetic_reports()
    a=objs['MATERIAL_8X8_UNSELECTED.json']
    if change=='one_assigned_node':a['material_assignment_by_original_parent']['1']='GRANITE'
    elif change=='fake_phase':a['nodewise_conditional_PT_reference']['1']['actual_rock_phase']='QUARTZ'
    elif change=='fake_pore':a['nodewise_conditional_PT_reference']['1']['actual_pore_pressure_pa']=0.
    elif change=='pretend_authorial':a['authorial_selection_confirmed']=True
    elif change=='fake_law':a['hypothetical_lab_law_registry']=['LAB_IS_PHYSICAL']
    elif change=='fake_material_audit':objs['AUDIT.json']['qualified_cold_T_P_rate_constitutive_laws']=1
    fail(lambda:m.write_once(root,tmp_path/'out',objs),
         'MATERIAL_UNSELECTED|MATERIAL_SOURCE_AUDIT')
    assert not (tmp_path/'out').exists()


def test_manifest_rejects_byte_tamper(tmp_path):
    source=tmp_path/'archive';source.mkdir()
    name='AUDIT.json';(source/name).write_text('{"x":1}')
    original=m.sha(source/name)
    (source/'MANIFEST.json').write_text(json.dumps({'schema':'S','files':{name:original},
        'physical_T1':None,'HistoryStore_modified':False,
        'D_024':'ACTIVE','WORLD_HISTORY_PRODUCTION_AUTHORIZED':False}))
    m.manifest(source,'S',(name,))
    (source/name).write_text('{"x":2}')
    fail(lambda:m.manifest(source,'S',(name,)),'MATERIAL_EVIDENCE_SHA_INVALID')


def test_water_exponent_requires_explicit_fluid_fugacity_and_is_numerically_effective():
    c=creep();c['water_exponent']=1.;c['water_fugacity_pa']=2e7
    c['reference_fugacity_pa']=1e7
    stress_wet=m.creep_differential_stress_pa(c,T_k=500,pressure_pa=1e8,rate_s_inv=1e-13)
    c['water_fugacity_pa']=1e7
    stress_ref=m.creep_differential_stress_pa(c,T_k=500,pressure_pa=1e8,rate_s_inv=1e-13)
    assert stress_wet<stress_ref


def test_water_zero_exponent_rejects_hidden_positive_fugacity():
    c=creep();c['water_fugacity_pa']=1e7
    fail(lambda:m.review_creep_law(c),'MATERIAL_WATER_FUGACITY_AMBIGUOUS')


def test_unselected_scenario_and_mechanical_gate_remain_false():
    c,p=fake_source(8);t=m.template_for_source(c,p)
    assert t['physical_G2_material_assignments']==0
    assert t['mechanical_solve_authorized'] is False
    assert t['WORLD_HISTORY_PRODUCTION_AUTHORIZED'] is False


def test_trial_does_not_claim_actual_fault_strength():
    pt,cold=source_node();out=m.evaluate_candidate_node(pt,cold,candidate())
    assert out['physical_fault_slip_law'] is None
    assert out['actual_brittle_ductile_transition_depth_m'] is None
    assert out['natural_material_identity_verified'] is False


def synthetic_original_fair_context(monkeypatch,tmp_path):
    """Synthetic SHA-valid report fixtures; NEVER observational ARCANA evidence."""
    import sys
    from types import ModuleType
    root=tmp_path/'repository';root.mkdir()
    cold_folder=tmp_path/'cold';cold_folder.mkdir()
    pt_folder=tmp_path/'pt';pt_folder.mkdir()
    colds=[];pts=[]
    for extent in (8,16):
        cold,pt=fake_source(extent)
        cold['source_original_packet_sha256']=str(extent)*64
        cold['source_original_FEG_sha256']='f'*64
        cold['source_original_PRE_sha256']='e'*64
        cold.update({'original_T0_source_nodes':{str(n):{} for n in cold['source_parent_ids']}})
        cold_file=cold_folder/f'REGION_{extent}X{extent}_COLD_CRUST.json'
        pt_file=pt_folder/f'REGION_{extent}X{extent}_SOURCE_PT.json'
        cold_file.write_text(json.dumps(cold))
        pt_file.write_text(json.dumps(pt))
        colds.append(cold);pts.append(pt)
    cold_a={'test_only':True};pt_a={'test_only':True}
    (cold_folder/'AUDIT.json').write_text(json.dumps(cold_a))
    (pt_folder/'AUDIT.json').write_text(json.dumps(pt_a))
    (cold_folder/'MANIFEST.json').write_text(json.dumps({
        'schema':'ARCANA_R6_T0_COLD_CRUST_REGIME_MANIFEST_V1',
        'files':{f:m.sha(cold_folder/f) for f in m.COLD_FILES},
        'physical_T1':None,'D_024':'ACTIVE','HistoryStore_modified':False,
        'WORLD_HISTORY_PRODUCTION_AUTHORIZED':False,
    }))
    (pt_folder/'MANIFEST.json').write_text('{}')
    mod_c=ModuleType('experiments.plate58_deforming_explore_v1.g2_g3_t0_cold_crust_regime')
    mod_p=ModuleType('experiments.plate58_deforming_explore_v1.g2_g3_t0_lithostatic_pt_reference')
    mod_h=ModuleType('experiments.plate58_deforming_explore_v1.g2_g3_source_to_coupled_handoff')
    mod_i=ModuleType('experiments.plate58_deforming_explore_v1.g2_g3_physical_source_packet')
    mod_c.build=lambda **kwargs:(colds[0],colds[1],cold_a)
    mod_c._load_original_pt=lambda folder:({},[
        json.loads((Path(folder)/f'REGION_{n}X{n}_SOURCE_PT.json').read_text())
        for n in (8,16)],json.loads((Path(folder)/'AUDIT.json').read_text()))
    mod_p.build=lambda *args:(pts[0],pts[1],pt_a)
    mod_h.load_packet=lambda path,n:({},None,{'evidence_manifest_sha256':str(n)*64})
    mod_i.verify_cross_extent_provider_chain=lambda a,b:None
    for mod in (mod_c,mod_p,mod_h,mod_i):monkeypatch.setitem(sys.modules,mod.__name__,mod)
    # In the combined FAIR regression the real cold/P-T modules may already
    # be cached as package attributes: replace both import lookup paths.
    import experiments.plate58_deforming_explore_v1 as package
    monkeypatch.setattr(package,'g2_g3_t0_cold_crust_regime',mod_c,raising=False)
    monkeypatch.setattr(package,'g2_g3_t0_lithostatic_pt_reference',mod_p,raising=False)
    return {'repo_root':root,'packet8':tmp_path/'packet8',
            'packet16':tmp_path/'packet16','handoff':tmp_path/'handoff',
            'pt_folder':pt_folder,'cold_folder':cold_folder}


def test_full_source_handoff_build_with_sha_and_original_ids(monkeypatch,tmp_path):
    kw=synthetic_original_fair_context(monkeypatch,tmp_path)
    a,b,audit=m.build(**kw)
    assert set(a['material_assignment_by_original_parent'])==set(map(str,range(1,82)))
    assert len(b['material_assignment_by_original_parent'])==289
    assert audit['source_16x16_material_assignments']==0
    assert audit['mechanical_solve_authorized'] is False
    m.write_once(kw['repo_root'],tmp_path/'out',dict(zip(m.FILES,(a,b,audit))))
    assert (tmp_path/'out'/'MANIFEST.json').is_file()


def test_valid_sha_but_substituted_cold_source_rejected(monkeypatch,tmp_path):
    kw=synthetic_original_fair_context(monkeypatch,tmp_path)
    folder=kw['cold_folder'];path=folder/'REGION_8X8_COLD_CRUST.json'
    row=json.loads(path.read_text());row['forged']='rock assignment';path.write_text(json.dumps(row))
    mani=json.loads((folder/'MANIFEST.json').read_text())
    mani['files'][path.name]=m.sha(path)
    (folder/'MANIFEST.json').write_text(json.dumps(mani))
    fail(lambda:m.build(**kw),'MATERIAL_COLD_SOURCE_REPLAY_MISMATCH')


def test_substituted_original_pt_pressure_rejected(monkeypatch,tmp_path):
    kw=synthetic_original_fair_context(monkeypatch,tmp_path)
    path=kw['pt_folder']/'REGION_8X8_SOURCE_PT.json'
    row=json.loads(path.read_text());row['original_T0_source_nodes']['1'][
        'conditional_moho_delta_overburden_pa']=9e9
    path.write_text(json.dumps(row))
    fail(lambda:m.build(**kw),'MATERIAL_PT_SOURCE_REPLAY_MISMATCH')


def synthetic_oxide_report(tmp_path):
    folder=tmp_path/'oxide';folder.mkdir()
    report={'schema':'ARCANA_R6_T0_BULK_COMPOSITION_CANDIDATE_REPORT_V1',
            'physically_ratified_T0_composition_cell_count':0,
            'physical_T0_bulk_chemistry':None,
            'physical_T0_mineral_phases':None,
            'mechanical_solve_authorized':False,'physical_T1':None,'D_024':'ACTIVE',
            'experimental_recipe_records':[{'id':'OX_SYNTHETIC',
               'oxide_mass_wt_percent':{'SiO2':60.,'FeO*':40.}}],
            'experimental_mass_mixture_records':[]}
    rp=folder/'REPORT.json';rp.write_text(json.dumps(report))
    mani={'schema':'ARCANA_R6_T0_BULK_COMPOSITION_HYPOTHESIS_MANIFEST_V1',
          'files':{'REPORT.json':m.sha(rp)},
          'no_canonical_promotion':True,'no_physical_materialization':True,
          'no_mechanical_solve':True,'no_T1':True,'no_world_history':True}
    (folder/'MANIFEST.json').write_text(json.dumps(mani))
    return folder


def test_original_oxide_candidate_sha_reference_does_not_infer_mineral_phase(tmp_path):
    folder=synthetic_oxide_report(tmp_path)
    r=m.verified_bulk_oxide_candidate(folder,'OX_SYNTHETIC')
    assert r['oxide_subset_wt_percent']['SiO2']==60.
    assert r['physical_phase_assemblage_from_oxides'] is None
    assert r['original_T0_region_placement_proven'] is False


@pytest.mark.parametrize('change',['report_byte','manifest_auth','forge_real_chemistry','missing_oxide'])
def test_oxide_scenario_provenance_fail_closed(tmp_path,change):
    folder=synthetic_oxide_report(tmp_path)
    if change=='report_byte':
        (folder/'REPORT.json').write_text('{}')
    elif change=='manifest_auth':
        path=folder/'MANIFEST.json';d=json.loads(path.read_text())
        d['no_canonical_promotion']=False;path.write_text(json.dumps(d))
    elif change=='forge_real_chemistry':
        path=folder/'REPORT.json';d=json.loads(path.read_text())
        d['physical_T0_mineral_phases']=['GRANITE'];path.write_text(json.dumps(d))
        p=folder/'MANIFEST.json';x=json.loads(p.read_text())
        x['files']['REPORT.json']=m.sha(path);p.write_text(json.dumps(x))
    fail(lambda:m.verified_bulk_oxide_candidate(folder,
         'UNKNOWN' if change=='missing_oxide' else 'OX_SYNTHETIC'),
         'MATERIAL_BULK_OXIDE')


def prepared_full_region(tmp_path):
    cold,pt=fake_source(8)
    template=m.template_for_source(cold,pt)
    template['source_cold_report_sha256']='d'*64
    template['source_PT_report_sha256']='b'*64
    for i in template['source_parent_ids']:
        key=str(i)
        pt['original_T0_source_nodes'][key].update({
            'pore_pressure_pa':None,'fault_normal_pressure_pa':None,
            'constitutive_law_assigned':False})
        cold['original_T0_source_nodes'][key].update({
            'source_node_lithology':None,'model_regime_assignment':'UNDETERMINED'})
    source={str(n):candidate() for n in template['source_parent_ids']}
    return template,pt,cold,source


def test_81_original_nodes_authored_candidate_trial_remains_noncanonical(tmp_path):
    folder=synthetic_oxide_report(tmp_path)
    template,pt,cold,source=prepared_full_region(tmp_path)
    r=m.evaluate_authored_region_trial(template,pt,cold,source,
        oxide_folder=folder,record_id='SYNTHETIC_UNIT_TEST_NOT_AUTHOR_RATIFICATION')
    assert len(r['hypothetical_material_strength_by_original_parent'])==81
    assert r['natural_ARCANA_mineralogy_or_fluid_state_ratified'] is False
    assert r['source_fault_side_materials_qualified'] is False
    assert r['physical_T1'] is None
    assert r['validated_laboratory_dataset_bytes_independently_inspected'] is False
    assert list(r['verified_bulk_oxide_candidates_not_mineral_phases'])==['OX_SYNTHETIC']


@pytest.mark.parametrize('change',['missing_node','extra_node','wrong_record','wrong_region','source_mismatch'])
def test_original_source_material_trial_requires_explicit_81_parent_coverage(tmp_path,change):
    folder=synthetic_oxide_report(tmp_path)
    t,pt,cold,x=prepared_full_region(tmp_path)
    if change=='missing_node':del x['1']
    elif change=='extra_node':x['999']=candidate()
    elif change=='wrong_record':x['1']['authorial_record']='BAD'
    elif change=='wrong_region':t['extent_cells']=16
    elif change=='source_mismatch':pt['original_parent_node_order'][0]=999
    fail(lambda:m.evaluate_authored_region_trial(t,pt,cold,x,oxide_folder=folder,
         record_id='SYNTHETIC_UNIT_TEST_NOT_AUTHOR_RATIFICATION'),
         'MATERIAL_TRIAL|MATERIAL_UNSELECTED')
