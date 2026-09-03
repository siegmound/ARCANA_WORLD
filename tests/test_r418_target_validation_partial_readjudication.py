from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r418_target_validation_partial_readjudication import _target_scalar,_provenance_is_safe,_freeze_p2

def test_target_scalar_ratio_and_delta():
    assert _target_scalar({'value':{'ratio':0.9}},'population_response_ratio')==('ratio',0.9)
    assert _target_scalar({'value':{'delta':-0.2}},'allele_frequency_gap_delta')==('delta',-0.2)

def test_r43_bridge_requires_hash_integrity():
    good={'extractor':'R43_PRE_RESULT_CANONICAL_WINDOW_DESCRIPTOR_BRIDGE','provenance':{},'hash_check':{'declared_hash_match':True,'actual_artifact_present':True,'actual_sha256_match':True}}
    bad={**good,'hash_check':{**good['hash_check'],'actual_sha256_match':False}}
    assert _provenance_is_safe(good) is True
    assert _provenance_is_safe(bad) is False

def test_generic_external_r4_provenance_rejected():
    assert _provenance_is_safe({'extractor':'GENERIC_EXPLICIT_JSON_TARGET_DESCRIPTOR','provenance':'outputs/v0_6D1_R4_3/jobs/J/result.json'}) is False

def test_freeze_p2_accounts_three_sources(tmp_path:Path):
    (tmp_path/'outputs/v0_6D1_R4_14').mkdir(parents=True); (tmp_path/'outputs/v0_6D1_R4_15').mkdir(parents=True); (tmp_path/'outputs/v0_6D1_R4_17').mkdir(parents=True)
    json.dump({'gaps':[{'window_id':'W0','domain':'d0','closure_priority':'P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION','root_cause':'x','closure_action':'a'},{'window_id':'W1','domain':'d1','closure_priority':'P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION','root_cause':'x','closure_action':'a'}]},open(tmp_path/'outputs/v0_6D1_R4_14/R4_14_EVIDENCE_GAP_CENSUS.json','w'))
    json.dump({'records':[{'window_id':'W2','domain':'d2','authorized_recovery_engine':'NEMO','resolution_status':'P0_CANDIDATE_EXHAUSTED_RECLASSIFIED_TO_P2'},{'window_id':'W3','domain':'d3','authorized_recovery_engine':'SLiM','resolution_status':'P0_CANDIDATE_EXHAUSTED_RECLASSIFIED_TO_P2'}]},open(tmp_path/'outputs/v0_6D1_R4_15/R4_15_RETAINED_RUNTIME_METRIC_RECOVERY.json','w'))
    json.dump({'records':[{'window_id':'W4','domain':'d4','engine':'NEMO','next_priority':'P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION','closure_status':'x'},{'window_id':'W5','domain':'d5','engine':'SLiM','next_priority':'P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION','closure_status':'x'}]},open(tmp_path/'outputs/v0_6D1_R4_17/R4_17_RECOVERED_METRIC_PROMOTION_CLOSURE.json','w'))
    o=_freeze_p2(tmp_path); assert o['cell_count']==6 and o['execution_authorized'] is False
