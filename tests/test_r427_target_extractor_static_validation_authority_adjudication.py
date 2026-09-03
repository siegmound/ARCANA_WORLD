from pathlib import Path
import hashlib
import json

from arcana_worldsim.scientific_engines.r427_target_extractor_static_validation_authority_adjudication import (
    inspect_source_schema,
    static_validate_extractors,
    adjudicate_target_design_authorities,
    adjudicate_j14_authority_request,
)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_json_static_schema_inspection_never_returns_numeric_values(tmp_path: Path):
    p=tmp_path/'x.json'; p.write_text('{"a":{"b":123},"rows":[{"c":4}]}',encoding='utf-8')
    o=inspect_source_schema(p,'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR')
    assert 'a.b' in o['schema_paths']
    assert 'rows[].c' in o['schema_paths']
    assert '123' not in json.dumps(o)


def test_44_extractors_static_validate_but_selector_stays_deferred_without_parent_frozen_selector(tmp_path: Path):
    records=[]
    for i in range(44):
        p=tmp_path/'outputs'/f'v0_6D1_R3_{i}'/'canonical.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('{"exact":{"value":1}}',encoding='utf-8')
        records.append({
            'window_id':f'W{i}','domain':'connectivity','implementation_class':'READ_ONLY_CANONICAL_TARGET_EXTRACTOR',
            'selector_policy':'EXACT_SELECTOR_ONLY_NO_FUZZY_NO_FALLBACK','selector_binding_status':'PENDING_EXPLICIT_R427_STATIC_SELECTOR_BINDING',
            'source_bindings':[{'source':str(p),'binding_eligible':True,'expected_sha256':_sha(p),'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'}],
        })
    records.append({'window_id':'S','domain':'population_persistence','implementation_class':'REJECTION_CAUSE_ONLY_SEMANTIC_REPAIR_AUDIT','failed_validation_keys_frozen':['eligible_primary_row_count'],'numeric_value_change_authorized':False,'mapping_class_upgrade_authorized':False})
    o=static_validate_extractors(tmp_path,{'records':records})
    assert o['canonical_extractor_static_valid_count']==44
    assert o['canonical_extractor_selector_authorized_count']==0
    assert o['canonical_extractor_selector_deferred_count']==44
    assert o['semantic_repair_review_authorized_count']==1


def test_parent_frozen_exact_selector_can_be_statically_authorized(tmp_path: Path):
    p=tmp_path/'x.json'; p.write_text('{"exact":{"value":1}}',encoding='utf-8')
    rec={'window_id':'W','domain':'connectivity','implementation_class':'READ_ONLY_CANONICAL_TARGET_EXTRACTOR','selector_policy':'EXACT_SELECTOR_ONLY_NO_FUZZY_NO_FALLBACK','selector_binding_status':'PENDING_EXPLICIT_R427_STATIC_SELECTOR_BINDING','frozen_exact_selector':'exact.value','source_bindings':[{'source':str(p),'binding_eligible':True,'expected_sha256':_sha(p),'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'}]}
    o=static_validate_extractors(tmp_path,{'records':[rec]})
    assert o['records'][0]['selector_execution_authorized_in_r427'] is True


def _design_request(i:int,domain:str='range_shift_rate'):
    return {
        'window_id':f'W{i}','domain':domain,'request_status':'FROZEN_PENDING_R427_AUTHORITY_ADJUDICATION',
        'scientific_construct':'X','required_canonical_observables':['A','B','C'],'permitted_unit_families':['U'],
        'forbidden_shortcuts':['BAD'],'required_governance':['PRE_RESULT_DEFINITION','CANONICAL_SOURCE_AUTHORITY','EXPLICIT_TEMPORAL_BASIS','EXPLICIT_SPATIAL_POPULATION_BASIS','EXPLICIT_UNCERTAINTY_OR_AGGREGATION','HASH_BOUND_PROVENANCE'],
        'external_engine_result_may_define_target':False,'result_selected_transform_authorized':False,'numeric_target_definition_authorized_in_r426':False,
    }


def test_12_target_design_requests_can_be_approved_only_for_definition_implementation():
    req=[_design_request(i,'range_shift_rate' if i<5 else 'founder_persistence') for i in range(12)]
    o=adjudicate_target_design_authorities({'requests':req})
    assert o['request_count']==12
    assert o['approved_for_definition_implementation_count']==12
    assert o['numeric_target_materialization_authorized_count']==0
    assert all(r['numeric_target_materialization_authorized_in_r428_by_r427'] is False for r in o['records'])


def test_incomplete_target_design_request_is_deferred_not_implicitly_filled():
    r=_design_request(0); r['required_canonical_observables']=[]
    o=adjudicate_target_design_authorities({'requests':[r]})
    assert o['approved_for_definition_implementation_count']==0
    assert o['deferred_for_spec_repair_count']==1


def _j14():
    return {
        'authority_request_frozen':True,'job_id':'R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS','request_kind':'NEW_ENGINE_INDEPENDENT_CANONICAL_SPATIAL_REPLAY_AUTHORITY',
        'required_temporal_support':{'start_age_ma':3.0,'end_age_ka':200.0,'time_indexed':True},
        'required_spatial_support':['EXPLICIT_LAT_LON_OR_GRID_ROW_COL','TIME_INDEXED_POPULATION_OR_DEME_STATE','EXPLICIT_CANONICAL_SPATIAL_SUPPORT_IDENTITY'],
        'required_authority_properties':['ARCANA_ENGINE_INDEPENDENT','FORWARD_OR_EXPLICITLY_AUTHORIZED_RECONSTRUCTION_FROM_CANONICAL_PROVIDERS','R3_27_MACRO_TRAJECTORY_AGGREGATE_INVARIANT_AUDIT','PALEOGEOGRAPHIC_AND_ENVIRONMENTAL_PROVIDER_PROVENANCE','HASH_BOUND_INPUT_OUTPUT_PROVENANCE','SEALED_BEFORE_ANY_GEONOMICS_EXECUTION'],
        'forbidden_shortcuts':['SYNTHESIZE_3MA_COORDINATES_FROM_R3_27_SCALARS','BACKWARD_INTERPOLATE_FROM_R3_15_250KA','BACKWARD_EXTRAPOLATE_FROM_R3_28_200KA','USE_GEONOMICS_DEFAULT_MODEL_AS_CANONICAL_AUTHORITY','USE_EXTERNAL_ENGINE_RESULTS_TO_DEFINE_CANONICAL_SPATIAL_STATE','MUTATE_R4_2_J14_WINDOW_OR_JOB_ID','EXECUTE_J18_J21_AS_SUBSTITUTE_FOR_FULL_SHARED_GEONOMICS_SCOPE'],
        'new_namespace_required_if_authority_is_later_approved':True,'canonical_replay_authorized_in_r426':False,'geonomics_execution_authorized_in_r426':False,'r42_j14_mutation_authorized':False,'parent_existing_sealed_authority_candidate_count':0,
    }


def test_j14_request_approves_only_implementation_preflight_not_replay_or_geonomics():
    o=adjudicate_j14_authority_request(_j14())
    assert o['spatial_authority_implementation_preflight_authorized_in_r428'] is True
    assert o['canonical_spatial_replay_execution_authorized_in_r427'] is False
    assert o['canonical_spatial_replay_execution_authorized_in_r428_by_r427'] is False
    assert o['geonomics_execution_authorized_in_r427'] is False


def test_j14_missing_shortcut_guard_defers_fail_closed():
    r=_j14(); r['forbidden_shortcuts']=r['forbidden_shortcuts'][:-1]
    o=adjudicate_j14_authority_request(r)
    assert o['spatial_authority_implementation_preflight_authorized_in_r428'] is False
    assert o['adjudication']=='DEFERRED_SPATIAL_AUTHORITY_SPEC_REPAIR_REQUIRED'
