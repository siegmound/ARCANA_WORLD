from pathlib import Path
import json
import numpy as np

from arcana_worldsim.scientific_engines.r431_target_semantic_authority_j14_validation import (
    validate_target_attempts,
    freeze_target_authority_closure,
    freeze_semantic_repair_closure,
    _deferred_gap_class,
)


def test_source_identity_deferred_class_is_explicit():
    c,n=_deferred_gap_class('DEFERRED_AUTHORIZED_SELECTOR_SOURCE_BINDING_AUTHORITY_NOT_FROZEN_BY_R429')
    assert c=='SOURCE_IDENTITY_AUTHORITY_GAP_FROZEN'
    assert n=='R432_EXPLICIT_SOURCE_IDENTITY_AUTHORITY_FREEZE'


def test_transform_dependency_deferred_class_is_explicit():
    c,n=_deferred_gap_class('DEFERRED_FROZEN_TRANSFORM_HAS_UNBOUND_SEMANTIC_DEPENDENCY')
    assert c=='TRANSFORM_SEMANTIC_DEPENDENCY_AUTHORITY_GAP_FROZEN'
    assert 'TRANSFORM_SEMANTIC_DEPENDENCY' in n


def test_five_all_deferred_are_terminal_without_numeric_execution():
    parent={'records':[]}
    for i in range(5):
        parent['records'].append({
            'window_id':f'W{i}','domain':'x',
            'materialization_disposition':'DEFERRED_AUTHORIZED_SELECTOR_SOURCE_BINDING_AUTHORITY_NOT_FROZEN_BY_R429',
            'numeric_target_materialized':False,'numeric_value':None,'source_integrity_blocked':False,
            'adjudicative_in_r430':False,
        })
    out=validate_target_attempts(parent)
    assert out['status']=='R431_TARGET_ATTEMPT_SEMANTIC_VALIDATION_COMPLETE'
    assert out['parent_materialized_count']==0
    assert out['parent_deferred_count']==5
    assert out['deferred_authority_gap_count']==5
    assert out['source_integrity_blocked_count']==0
    assert out['adjudicative_promotion_count']==0


def test_materialized_candidate_requires_protocol_and_pre_result_guards():
    parent={'records':[{
        'window_id':'W','domain':'x','materialization_disposition':'MATERIALIZED',
        'numeric_target_materialized':True,'numeric_value':1.25,'source_integrity_blocked':False,
        'frozen_selector':'m','frozen_transform_id':'IDENTITY','domain_protocol':{'canonical_quantity':'x'},
        'external_engine_result_used_to_define_target':False,'result_selected_transform_used':False,
        'adjudicative_in_r430':False,
    }]}
    # fill to exact stage count with four safe deferred records
    for i in range(4):
        parent['records'].append({'window_id':f'D{i}','domain':'x','materialization_disposition':'DEFERRED_FROZEN_TRANSFORM_HAS_UNBOUND_SEMANTIC_DEPENDENCY','numeric_target_materialized':False,'numeric_value':None,'source_integrity_blocked':False,'adjudicative_in_r430':False})
    out=validate_target_attempts(parent)
    assert out['materialized_semantic_valid_count']==1
    assert out['adjudicative_promotion_count']==0


def test_parent_block_remains_fail_closed():
    parent={'records':[]}
    for i in range(5):
        parent['records'].append({'window_id':f'W{i}','domain':'x','materialization_disposition':'BLOCKED_X' if i==0 else 'DEFERRED_X','numeric_target_materialized':False,'numeric_value':None,'source_integrity_blocked':i==0,'adjudicative_in_r430':False})
    out=validate_target_attempts(parent)
    assert out['status'].startswith('BLOCKED_')
    assert out['source_integrity_blocked_count']==1


def test_authority_closure_reconciles_57():
    target={'records':[{'window_id':f'T{i}','domain':'x','parent_numeric_target_materialized':False,'authority_gap_class':'SOURCE_IDENTITY_AUTHORITY_GAP_FROZEN','terminal_validation_pass':True,'next_priority':'R432_X'} for i in range(5)]}
    gaps={'records':[{'window_id':f'G{i}','domain':'x','closure_status':'NO_EXACT_PRE_RESULT_SELECTOR_RULE_AUTHORITY_GAP_FROZEN'} for i in range(39)]}
    design={'records':[{'window_id':f'D{i}','domain':'range_shift_rate','implementation_validation_pass':True,'validation_status':'VALIDATED_PRE_RESULT_NONNUMERIC_TARGET_AUTHORITY_DEFINITION'} for i in range(12)]}
    sem={'records':[{'window_id':'S','domain':'population_persistence','numeric_value_changed':False,'mapping_class_changed':False,'readjudication_performed':False}]}
    out=freeze_target_authority_closure(target,gaps,design,sem)
    assert out['status']=='R431_TARGET_AUTHORITY_CLOSURE_REGISTRY_FROZEN'
    assert out['active_target_repair_accounting_count']==57
    assert out['target_design_observable_binding_authorized_count']==12
    assert out['primary_mapping_authority_definition_authorized_count']==1
    assert out['numeric_target_execution_authorized_count']==0


def test_semantic_repair_closure_never_mutates():
    parent={'records':[{'window_id':'SAPIENT_3MA_TO_200KA','domain':'population_persistence','eligible_primary_row_count_under_existing_frozen_mapping':0,'numeric_value_changed':False,'mapping_class_changed':False,'readjudication_performed':False,'review_status':'NO_EXISTING_FROZEN_PRIMARY_MAPPING_ELIGIBILITY_REMAINS_DEFERRED'}]}
    out=freeze_semantic_repair_closure(parent)
    assert out['status']=='R431_SEMANTIC_REPAIR_AUTHORITY_CLOSURE_FROZEN'
    assert out['records'][0]['closure_status']=='PRIMARY_MAPPING_AUTHORITY_GAP_FROZEN'
    assert out['records'][0]['authority_definition_implementation_authorized_in_r432'] is True
