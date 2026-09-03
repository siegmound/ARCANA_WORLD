import json
from pathlib import Path
import numpy as np

from arcana_worldsim.scientific_engines.r430_target_materialization_selector_gap_j14_execution import (
    apply_frozen_transform,
    read_exact_selector,
    close_selector_gaps,
    materialize_authorized_targets,
)


def test_identity_scalar_only():
    d,v,_=apply_frozen_transform(3.25,'IDENTITY')
    assert d=='MATERIALIZED' and v==3.25
    d,v,_=apply_frozen_transform([1.0,2.0],'IDENTITY')
    assert d=='DEFERRED_IDENTITY_REQUIRES_SCALAR_SELECTOR_VALUE' and v is None


def test_endpoint_ratio_and_delta_are_exact_1d_only():
    d,v,_=apply_frozen_transform([2.0,4.0],'END_OVER_START')
    assert d=='MATERIALIZED' and v==2.0
    d,v,_=apply_frozen_transform([2.0,5.0],'END_MINUS_START_OR_EXPLICIT_ENDPOINT')
    assert d=='MATERIALIZED' and v==3.0
    d,v,_=apply_frozen_transform([[1.0,2.0],[3.0,4.0]],'END_OVER_START')
    assert d.startswith('DEFERRED_') and v is None


def test_unbound_semantic_dependency_never_executes():
    d,v,reason=apply_frozen_transform(3.0,'NORMALIZE_BY_FROZEN_SUPPORT_DENOMINATOR')
    assert d=='DEFERRED_FROZEN_TRANSFORM_HAS_UNBOUND_SEMANTIC_DEPENDENCY'
    assert v is None and 'SUPPORT_DENOMINATOR' in reason


def test_exact_readers(tmp_path: Path):
    jp=tmp_path/'x.json'; jp.write_text(json.dumps({'a':{'b':2.5}}),encoding='utf-8')
    assert read_exact_selector(jp,'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR','a.b')==2.5
    npz=tmp_path/'x.npz'; np.savez_compressed(npz,foo=np.asarray([1.0,3.0]))
    assert np.allclose(read_exact_selector(npz,'READ_ONLY_NPZ_DESCRIPTOR_EXTRACTOR','foo'),[1,3])
    cp=tmp_path/'x.csv'; cp.write_text('foo,bar\n1,2\n3,4\n',encoding='utf-8')
    assert np.allclose(read_exact_selector(cp,'READ_ONLY_TABULAR_DESCRIPTOR_EXTRACTOR','foo'),[1,3])


def test_materialization_requires_unique_hash_bound_source(tmp_path: Path):
    p=tmp_path/'canon.json'; p.write_text(json.dumps({'metric':4.0}),encoding='utf-8')
    import hashlib
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    ps={'records':[{'window_id':'W','domain':'connectivity','selector_authorized':True,'selector_authority_disposition':'AUTHORIZED','frozen_selector':'metric','frozen_transform_id':'IDENTITY','frozen_authority_class':'DIRECT_CANDIDATE'}]}
    r428={'records':[{'window_id':'W','domain':'connectivity','source_packets':[{'source':str(p),'expected_sha256':h,'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'}]}]}
    prot={'records':[{'window_id':'W','domain':'connectivity','protocol':{'canonical_quantity':'x'}}]}
    out=materialize_authorized_targets(tmp_path,ps,r428,prot)
    assert out['numeric_target_materialized_count']==1
    assert out['source_integrity_blocked_count']==0
    assert out['records'][0]['numeric_value']==4.0
    assert out['records'][0]['adjudicative_in_r430'] is False


def test_selector_gap_routes_validated_design_authority():
    ps={'records':[
      {'window_id':'W1','domain':'range_shift_rate','selector_authorized':False,'selector_authority_disposition':'DEFERRED_NO_EXACT_PRE_RESULT_SELECTOR_RULE_MATCH'},
      {'window_id':'W2','domain':'connectivity','selector_authorized':False,'selector_authority_disposition':'DEFERRED_AMBIGUOUS_MULTIPLE_EXACT_PRE_RESULT_SELECTOR_RULE_MATCHES'}]}
    design={'records':[{'window_id':'W1','domain':'range_shift_rate','implementation_validation_pass':True}]}
    out=close_selector_gaps(ps,design)
    assert out['record_count']==2
    assert out['records'][0]['closure_status']=='ROUTED_TO_VALIDATED_TARGET_DESIGN_OBSERVABLE_BINDING_AUTHORITY'
    assert out['records'][1]['closure_status']=='AMBIGUOUS_EXACT_SELECTOR_RULE_AUTHORITY_GAP_FROZEN'
    assert out['selector_auto_authorized_count']==0



def test_r430_r1_unrelated_parent_packet_drift_does_not_veto_unique_exact_binding(tmp_path: Path):
    import hashlib
    good=tmp_path/'good.json'; good.write_text(json.dumps({'metric':4.0}),encoding='utf-8')
    h=hashlib.sha256(good.read_bytes()).hexdigest()
    missing=tmp_path/'missing.json'
    ps={'records':[{'window_id':'W','domain':'connectivity','selector_authorized':True,'selector_authority_disposition':'AUTHORIZED','frozen_selector':'metric','frozen_transform_id':'IDENTITY','frozen_authority_class':'DIRECT_CANDIDATE'}]}
    r428={'records':[{'window_id':'W','domain':'connectivity','source_packets':[
      {'source':str(good),'expected_sha256':h,'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'},
      {'source':str(missing),'expected_sha256':'0'*64,'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'}]}]}
    prot={'records':[{'window_id':'W','domain':'connectivity','protocol':{'canonical_quantity':'x'}}]}
    out=materialize_authorized_targets(tmp_path,ps,r428,prot)
    rec=out['records'][0]
    assert out['numeric_target_materialized_count']==1
    assert out['source_integrity_blocked_count']==0
    assert rec['numeric_value']==4.0
    assert rec['nonbinding_parent_source_packet_drift_count']==1


def test_r430_r2_zero_exact_binding_with_some_hash_valid_parent_is_deferred_authority_gap(tmp_path: Path):
    import hashlib
    other=tmp_path/'other.json'; other.write_text(json.dumps({'other':4.0}),encoding='utf-8')
    h=hashlib.sha256(other.read_bytes()).hexdigest()
    missing=tmp_path/'missing.json'
    ps={'records':[{'window_id':'W','domain':'connectivity','selector_authorized':True,'selector_authority_disposition':'AUTHORIZED','frozen_selector':'metric','frozen_transform_id':'IDENTITY','frozen_authority_class':'DIRECT_CANDIDATE'}]}
    r428={'records':[{'window_id':'W','domain':'connectivity','source_packets':[
      {'source':str(other),'expected_sha256':h,'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'},
      {'source':str(missing),'expected_sha256':'0'*64,'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'}]}]}
    prot={'records':[{'window_id':'W','domain':'connectivity','protocol':{'canonical_quantity':'x'}}]}
    out=materialize_authorized_targets(tmp_path,ps,r428,prot)
    assert out['numeric_target_materialized_count']==0
    assert out['source_integrity_blocked_count']==0
    assert out['semantic_dependency_or_source_ambiguity_deferred_count']==1
    rec=out['records'][0]
    assert rec['materialization_disposition']=='DEFERRED_AUTHORIZED_SELECTOR_SOURCE_BINDING_AUTHORITY_NOT_FROZEN_BY_R429'
    assert rec['hash_valid_parent_source_packet_count']==1
    assert rec['nonbinding_parent_source_packet_drift_count']==1


def test_r430_r2_all_parent_source_integrity_failure_remains_fail_closed(tmp_path: Path):
    missing1=tmp_path/'missing1.json'; missing2=tmp_path/'missing2.json'
    ps={'records':[{'window_id':'W','domain':'connectivity','selector_authorized':True,'selector_authority_disposition':'AUTHORIZED','frozen_selector':'metric','frozen_transform_id':'IDENTITY','frozen_authority_class':'DIRECT_CANDIDATE'}]}
    r428={'records':[{'window_id':'W','domain':'connectivity','source_packets':[
      {'source':str(missing1),'expected_sha256':'0'*64,'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'},
      {'source':str(missing2),'expected_sha256':'1'*64,'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'}]}]}
    prot={'records':[{'window_id':'W','domain':'connectivity','protocol':{'canonical_quantity':'x'}}]}
    out=materialize_authorized_targets(tmp_path,ps,r428,prot)
    assert out['numeric_target_materialized_count']==0
    assert out['source_integrity_blocked_count']==1
    rec=out['records'][0]
    assert rec['materialization_disposition']=='BLOCKED_AUTHORIZED_SELECTOR_ALL_PARENT_SOURCES_FAIL_INTEGRITY'
    assert rec['hash_valid_parent_source_packet_count']==0


def test_r430_r1_multiple_exact_valid_sources_remain_deferred(tmp_path: Path):
    import hashlib
    packets=[]
    for name,val in [('a',4.0),('b',4.0)]:
        p=tmp_path/f'{name}.json'; p.write_text(json.dumps({'metric':val}),encoding='utf-8')
        packets.append({'source':str(p),'expected_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'})
    ps={'records':[{'window_id':'W','domain':'connectivity','selector_authorized':True,'selector_authority_disposition':'AUTHORIZED','frozen_selector':'metric','frozen_transform_id':'IDENTITY','frozen_authority_class':'DIRECT_CANDIDATE'}]}
    r428={'records':[{'window_id':'W','domain':'connectivity','source_packets':packets}]}
    prot={'records':[{'window_id':'W','domain':'connectivity','protocol':{'canonical_quantity':'x'}}]}
    out=materialize_authorized_targets(tmp_path,ps,r428,prot)
    assert out['source_integrity_blocked_count']==0
    assert out['numeric_target_materialized_count']==0
    assert out['semantic_dependency_or_source_ambiguity_deferred_count']==1
    assert out['records'][0]['materialization_disposition']=='DEFERRED_AMBIGUOUS_MULTIPLE_HASH_VALID_SOURCES_FOR_AUTHORIZED_SELECTOR'
