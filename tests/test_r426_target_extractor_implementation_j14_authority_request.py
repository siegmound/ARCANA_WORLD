from pathlib import Path
import hashlib
import json
import numpy as np

from arcana_worldsim.scientific_engines.r426_target_extractor_implementation_j14_authority_request import (
    build_extractor_implementation_registry,
    build_target_design_authority_requests,
    build_j14_new_spatial_authority_request,
    extract_exact,
)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_exact_selector_reader_has_no_fuzzy_fallback(tmp_path: Path):
    p=tmp_path/'x.json'; p.write_text('{"exact":{"value":3}}',encoding='utf-8')
    assert extract_exact(p,'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR','exact.value') == 3
    try:
        extract_exact(p,'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR','value')
    except KeyError:
        pass
    else:
        raise AssertionError('fuzzy fallback must not occur')


def test_exact_npz_and_tabular_readers(tmp_path: Path):
    p=tmp_path/'x.npz'; np.savez(p, foo=np.array([1.,2.]))
    assert extract_exact(p,'READ_ONLY_NPZ_DESCRIPTOR_EXTRACTOR','foo').shape == (2,)
    t=tmp_path/'x.tsv'; t.write_text('a\tb\n1\t2\n',encoding='utf-8')
    assert extract_exact(t,'READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR','b') == ['2']


def test_44_1_12_2_implementation_accounting_and_hash_binding(tmp_path: Path):
    records=[]
    for i in range(44):
        p=tmp_path/'outputs'/f'v0_6D1_R3_{i}'/'canonical.json'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('{"x":1}',encoding='utf-8')
        records.append({'window_id':f'W{i}','domain':'connectivity','preflight_disposition':'READY_FOR_READ_ONLY_CANONICAL_EXTRACTOR_IMPLEMENTATION','candidate_sources':[{'source':str(p),'eligible':True,'sha256':_sha(p),'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'}]})
    records.append({'window_id':'S','domain':'population_persistence','preflight_disposition':'READY_FOR_REJECTION_CAUSE_ONLY_SEMANTIC_REPAIR_AUDIT','failed_validation_keys':['eligible_primary_row_count'],'failed_validation_fields':{'eligible_primary_row_count':0}})
    for i in range(5): records.append({'window_id':f'R{i}','domain':'range_shift_rate','preflight_disposition':'DEFERRED_NEW_TARGET_DESIGN_AUTHORITY_REQUIRED'})
    for i in range(7): records.append({'window_id':f'F{i}','domain':'founder_persistence','preflight_disposition':'DEFERRED_NEW_TARGET_DESIGN_AUTHORITY_REQUIRED'})
    for i in range(2): records.append({'window_id':f'P{i}','domain':'admixture','preflight_disposition':'CONTEXT_ONLY_PROXY_PRESERVED'})
    o=build_extractor_implementation_registry(tmp_path,{'records':records})
    assert o['record_count']==59
    assert o['canonical_extractor_implementation_count']==44
    assert o['canonical_extractor_hash_verified_ready_count']==44
    assert o['semantic_repair_audit_implementation_count']==1
    assert o['new_target_design_authority_deferred_count']==12
    assert o['context_only_proxy_count']==2


def test_hash_drift_fails_closed_for_canonical_binding(tmp_path: Path):
    p=tmp_path/'outputs'/'v0_6D1_R3_1'/'x.json'; p.parent.mkdir(parents=True); p.write_text('{"x":1}',encoding='utf-8')
    rec={'window_id':'W','domain':'connectivity','preflight_disposition':'READY_FOR_READ_ONLY_CANONICAL_EXTRACTOR_IMPLEMENTATION','candidate_sources':[{'source':str(p),'eligible':True,'sha256':'0'*64,'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'}]}
    o=build_extractor_implementation_registry(tmp_path,{'records':[rec]})
    r=o['records'][0]
    assert r['implementation_ready'] is False
    assert r['source_bindings'][0]['reason']=='SOURCE_HASH_DRIFT_AFTER_R425_FREEZE'


def test_target_design_requests_only_two_frozen_constructs():
    records=[]
    for i in range(5): records.append({'window_id':f'R{i}','domain':'range_shift_rate','preflight_disposition':'DEFERRED_NEW_TARGET_DESIGN_AUTHORITY_REQUIRED'})
    for i in range(7): records.append({'window_id':f'F{i}','domain':'founder_persistence','preflight_disposition':'DEFERRED_NEW_TARGET_DESIGN_AUTHORITY_REQUIRED'})
    o=build_target_design_authority_requests({'records':records})
    assert o['request_count']==12
    assert o['status']=='R426_TARGET_DESIGN_AUTHORITY_REQUESTS_FROZEN'
    assert all(r['numeric_target_definition_authorized_in_r426'] is False for r in o['requests'])


def test_j14_request_freezes_new_authority_without_authorizing_replay():
    d={'candidate_file_count':271,'exact_3ma_spatial_candidate_count':0,'sealed_existing_authority_candidate_count':0,'existing_sealed_authority_found':False,'j14_spatial_authority_gap_open_after_discovery':True}
    o=build_j14_new_spatial_authority_request(d)
    assert o['authority_request_frozen'] is True
    assert o['canonical_replay_authorized_in_r426'] is False
    assert o['geonomics_execution_authorized_in_r426'] is False
    assert o['required_temporal_support']['start_age_ma']==3.0
    assert 'BACKWARD_EXTRAPOLATE_FROM_R3_28_200KA' in o['forbidden_shortcuts']
