from pathlib import Path
from arcana_worldsim.scientific_engines.r421_p2_static_validation_reexecution_authorization import (
    _candidate_static_audit,_geonomics_binding_audit,expected_jobs_by_engine,validate_target_repairs,build_authorization
)

def test_candidate_adapters_static_guards_present():
    root=Path('.').resolve()
    for eng in ('NEMO','SLiM','CDMetaPOP','Geonomics'):
        r=_candidate_static_audit(root,eng)
        assert r['present'] and r['python_syntax_ok'] and r['required_tokens_ok'] and r['forbidden_tokens_absent'],r

def test_expected_jobs_by_engine_deduplicates_by_engine():
    r=expected_jobs_by_engine({'jobs':[{'engine':'NEMO','job_id':'B'},{'engine':'NEMO','job_id':'A'},{'engine':'SLiM','job_id':'C'}]})
    assert r=={'NEMO':['A','B'],'SLiM':['C']}

def test_geonomics_without_explicit_profiles_is_deferred(tmp_path:Path):
    a=_geonomics_binding_audit(tmp_path,['J1','J2'])
    assert a['all_profiles_valid'] is False and a['valid_profile_count']==0 and a['scalar_descriptor_synthesis_forbidden'] is True

def test_target_repair_static_accounting_57_2():
    rows=[]
    for i in range(44): rows.append({'window_id':f'E{i}','domain':'d','repair_disposition':'CANONICAL_DESCRIPTOR_EXTRACTOR_SPEC_FROZEN','required_fields':['a','b','c','d','e','f','g'],'external_result_may_define_target':False,'numeric_target_materialized_in_r420':False})
    for i in range(12): rows.append({'window_id':f'N{i}','domain':'d','repair_disposition':'TARGET_DESIGN_REQUIREMENTS_FROZEN_NO_NUMERIC_TARGET_INVENTED','required_fields':['a','b','c','d','e','f','g'],'external_result_may_define_target':False,'numeric_target_materialized_in_r420':False})
    rows.append({'window_id':'R','domain':'d','repair_disposition':'R418_REJECTION_CAUSE_PRESERVED_AND_REPAIR_SPEC_FROZEN','numeric_value_change_authorized':False,'external_result_may_define_target':False})
    rows += [{'window_id':'P1','domain':'d','repair_disposition':'CONTEXT_ONLY_PROXY_PRESERVED'},{'window_id':'P2','domain':'d','repair_disposition':'CONTEXT_ONLY_PROXY_PRESERVED'}]
    o=validate_target_repairs({'records':rows})
    assert o['record_count']==59 and o['active_count']==57 and o['context_only_count']==2 and o['active_static_validation_pass_count']==57

def test_partial_authorization_routes_to_combined_r422_branch():
    p2={'engine_families':[{'engine':'NEMO','static_validation_pass':True,'expected_frozen_job_ids':['J1']},{'engine':'Geonomics','static_validation_pass':False,'expected_frozen_job_ids':['J2']} ]}
    r42={'jobs':[{'engine':'NEMO','job_id':'J1'},{'engine':'Geonomics','job_id':'J2'}]}
    o=build_authorization(p2,{},r42)
    assert o['authorized_engine_families']==['NEMO'] and o['deferred_engine_families']==['Geonomics']
    assert o['next_action']=='BUILD_R422_AUTHORIZED_P2_SYMMETRIC_REEXECUTION_AND_DEFERRED_IMPLEMENTATION_COMPLETION'
