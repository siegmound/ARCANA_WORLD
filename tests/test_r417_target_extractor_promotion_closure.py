from pathlib import Path
import json
from arcana_worldsim.scientific_engines import r417_target_extractor_promotion_closure as r

def test_metric_proxy_closes_nonadjudicative():
    x=r.metric_terminal_disposition({'window_id':'W','domain':'population_persistence','engine':'CDMetaPOP','recovery_class':'x','disposition':{'promotion_gate':'PROXY_ONLY_BY_R412_NEUTRAL_INVARIANCE_FAILURE','reason':'x'}})
    assert x['promotion_performed'] is False
    assert x['closure_status']=='CLOSED_NONADJUDICATIVE_PROXY_ONLY'

def test_r43_additive_variance_bridge(tmp_path:Path):
    cfg={'r43_descriptor_domain_bridges':{'additive_variance':{'allowed_descriptor_types':['H0_SNAPSHOT_WINDOW'],'value_path':'comparison_only_derived.normalized_va_delta','source_semantics':'x','unit_basis':'dimensionless','candidate_comparability':'NORMALIZABLE_CANDIDATE'}}}
    d={'windows':{'W':{'descriptor_type':'H0_SNAPSHOT_WINDOW','comparison_only_derived':{'normalized_va_delta':0.1},'target':{'start':2,'end':1,'unit':'Ma'},'selected_frozen_artifact':{'hash_match':True}}}}
    x=r._r43_bridge(cfg,d,'W','additive_variance',tmp_path)
    assert x and x['value']==0.1 and x['candidate_comparability']=='NORMALIZABLE_CANDIDATE'

def test_proxy_bridge_never_adjudicative(tmp_path:Path):
    cfg={'r43_descriptor_domain_bridges':{'admixture':{'R328_SAPIENT_HIGH_RES_ENSEMBLE_WINDOW':{'value_path':'comparison_only_derived.admixture_delta','source_semantics':'proxy','unit_basis':'x','candidate_comparability':'PROXY_ONLY'}}}}
    d={'windows':{'W':{'descriptor_type':'R328_SAPIENT_HIGH_RES_ENSEMBLE_WINDOW','comparison_only_derived':{'admixture_delta':0.2},'target':{},'selected_frozen_artifact':{'hash_match':True}}}}
    rec={'window_id':'W','domain':'admixture','candidate_artifact_hits':[],'protocol_status':'x'}
    x=r.target_record(tmp_path,cfg,d,rec)
    assert x['materialization_status']=='TARGET_MATERIALIZED_PROXY_ONLY_NONADJUDICATIVE'
    assert x['adjudicative_target_authorized'] is False

def test_filename_hit_without_descriptor_not_materialized(tmp_path:Path):
    p=tmp_path/'outputs'/'admixture_result.json';p.parent.mkdir();p.write_text(json.dumps({'value':0.9}))
    rec={'window_id':'W','domain':'admixture','candidate_artifact_hits':['outputs/admixture_result.json'],'protocol_status':'x'}
    x=r.target_record(tmp_path,{}, {'windows':{}}, rec)
    assert x['materialized_target'] is None
    assert x['materialization_status']=='SOURCE_CANDIDATES_INSPECTED_NO_STRICT_TARGET_MATERIALIZED'

def test_explicit_json_descriptor_can_materialize(tmp_path:Path):
    p=tmp_path/'outputs'/'x.json';p.parent.mkdir();p.write_text(json.dumps({'canonical_target':{'domain':'biomass','value':3.0,'unit_basis':'kg','temporal_basis':'end','spatial_population_basis':'guild A','transform':'identity','provenance':'canon','comparability':'DIRECT_CANDIDATE'}}))
    rec={'window_id':'W','domain':'biomass','candidate_artifact_hits':['outputs/x.json'],'protocol_status':'x'}
    x=r.target_record(tmp_path,{}, {'windows':{}}, rec)
    assert x['materialized_target']['value']==3.0
    assert x['candidate_comparability']=='DIRECT_CANDIDATE'
    assert x['adjudicative_target_authorized'] is False
