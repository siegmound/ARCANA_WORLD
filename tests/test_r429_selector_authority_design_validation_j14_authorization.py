import json
from pathlib import Path
import numpy as np

from arcana_worldsim.scientific_engines.r429_selector_authority_design_validation_j14_authorization import (
    recover_exact_inventory, build_schemaless_closure, freeze_selector_authorities,
    validate_target_design_implementations, authorize_j14,
)
from arcana_worldsim.scientific_engines.r429_j14_spatial_authority_replay import (
    maximum_entropy_seed, advance_minimum_displacement, validate_authority_inputs,
)


def test_exact_inventory_json_dict_only(tmp_path):
    p=tmp_path/'x.json'; p.write_text(json.dumps({'a':{'total_population':[1,2]},'b':3}),encoding='utf-8')
    inv=recover_exact_inventory(p,'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR')
    assert inv==['a.total_population','b']


def test_selector_freeze_uses_exact_or_unique_leaf_only():
    parent={'records':[{
        'window_id':'W','domain':'population_persistence','selector_authority_preflight_disposition':'READY_EXACT_SCHEMA_INVENTORY_AND_PROTOCOL',
        'exact_schema_inventory':['summary.total_population'],
    }] + [{
        'window_id':f'W{i}','domain':'connectivity','selector_authority_preflight_disposition':'READY_EXACT_SCHEMA_INVENTORY_AND_PROTOCOL',
        'exact_schema_inventory':['not_connectivity'],
    } for i in range(43)]}
    cfg={'exact_selector_authority_catalog':{
        'population_persistence':[{'selector':'total_population','transform_id':'END_OVER_START','authority_class':'NORMALIZABLE_CANDIDATE'}],
        'connectivity':[{'selector':'corridor_connectivity','transform_id':'IDENTITY','authority_class':'DIRECT_CANDIDATE'}],
    }}
    o=freeze_selector_authorities(parent,{'records':[]},cfg)
    assert o['record_count']==44
    assert o['selector_authorized_count']==1
    r=o['records'][0]
    assert r['frozen_selector']=='summary.total_population'
    assert r['fuzzy_matching_used'] is False and r['synonym_fallback_used'] is False


def test_ambiguous_exact_leaf_match_defers():
    parent={'records':[{'window_id':'W','domain':'connectivity','selector_authority_preflight_disposition':'READY_EXACT_SCHEMA_INVENTORY_AND_PROTOCOL','exact_schema_inventory':['a.corridor_connectivity','b.corridor_connectivity']}]}
    cfg={'exact_selector_authority_catalog':{'connectivity':[{'selector':'corridor_connectivity','transform_id':'IDENTITY','authority_class':'DIRECT_CANDIDATE'}]}}
    o=freeze_selector_authorities(parent,{'records':[]},cfg)
    assert o['selector_authorized_count']==0
    assert 'AMBIGUOUS' in o['records'][0]['selector_authority_disposition']


def test_schemaless_closure_does_not_synthesize_selector(tmp_path):
    p=tmp_path/'x.json'; p.write_text('[{"x":1}]',encoding='utf-8')
    import hashlib
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    parent={'records':[{'window_id':f'W{i}','domain':'connectivity','selector_authority_preflight_disposition':'DEFERRED_NO_EXACT_SCHEMA_SELECTOR_INVENTORY','source_packets':[{'source':str(p),'expected_sha256':h,'parser_family':'READ_ONLY_JSON_DESCRIPTOR_EXTRACTOR'}]} for i in range(6)]}
    o=build_schemaless_closure(tmp_path,parent)
    assert o['record_count']==6
    assert o['inventory_recovered_count']==0
    assert o['authority_gap_frozen_count']==6
    assert all(r['selector_synthesis_authorized'] is False for r in o['records'])


def test_target_design_validation_requires_exact_parent_definition():
    req={'window_id':'W','domain':'range_shift_rate','scientific_construct':'C','required_canonical_observables':['A','B','C'],'permitted_unit_families':['U'],'required_governance':['G'],'forbidden_shortcuts':['X']}
    impl={'records':[{**req,'authority_definition_implemented':True,'numeric_target_materialization_authorized_in_r428':False,'external_engine_result_may_define_target':False,'result_selected_transform_authorized':False}]}
    requests={'requests':[req]}
    adj={'records':[{'window_id':'W','domain':'range_shift_rate','authority_definition_implementation_authorized_in_r428':True}]}
    o=validate_target_design_implementations(impl,requests,adj)
    assert o['validated_count']==1
    assert o['numeric_target_materialization_authorized_count']==0


def _make_j14_inputs(root:Path):
    (root/'outputs/v0_6D1_R3_27').mkdir(parents=True,exist_ok=True)
    (root/'outputs/v0_6D1_R3_27_SEAL').mkdir(parents=True,exist_ok=True)
    (root/'references/v0_6D1_R3').mkdir(parents=True,exist_ok=True)
    (root/'src/arcana_worldsim/late_cenozoic').mkdir(parents=True,exist_ok=True)
    (root/'src/arcana_worldsim/post_cha1').mkdir(parents=True,exist_ok=True)
    ages=np.linspace(3.0,0.2,141)
    vars=np.array(['effective_population','deme_count','ecological_breadth','cumulative_buffering','dispersal_capacity','developmental_investment','genetic_diversity_proxy','adaptive_integration'])
    cands=np.array(['RPT_010_D02','RPT_009_D02'])
    state=np.ones((96,2,141,8),dtype=float); state[...,0]=8000; state[...,1]=4
    np.savez(root/'outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz',candidate_ids=cands,age_ma=ages,variable_names=vars,state=state)
    (root/'outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_AUTHORITY.json').write_text(json.dumps({'window':{'start_age_ma':3.0,'end_age_ma':0.2}}),encoding='utf-8')
    (root/'outputs/v0_6D1_R3_27/R3_27_HUMAN_200KA_CHECKPOINT.json').write_text(json.dumps({'candidate_cohort':['RPT_010_D02','RPT_009_D02']}),encoding='utf-8')
    (root/'outputs/v0_6D1_R3_27_SEAL/R3_27_FINAL_SEAL_AUDIT.json').write_text(json.dumps({'status':'PASS_R327_TEST_SEALED','verdict':'SEALED'}),encoding='utf-8')
    aages=np.array([30.0,0.0]); lat=np.arange(90); lon=np.arange(180); land=np.ones((2,90,180),dtype=np.uint8); plate=np.ones_like(land)
    np.savez(root/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz',age_ma=aages,lat=lat,lon=lon,land_mask=land,plate_code=plate)
    (root/'src/arcana_worldsim/late_cenozoic/paleogeography.py').write_text('PROVIDER="PLATE_CORE_CONSTRAINED_ENDPOINT_EVENT_RECONSTRUCTION_A1"\ndef physical_paleogeography_state(a1,age_ma): pass\n',encoding='utf-8')
    (root/'src/arcana_worldsim/post_cha1/paleogeographic_history.py').write_text('STATUS="PLATE_CORE_CONSTRAINED_ENDPOINT_EVENT_RECONSTRUCTION"\n',encoding='utf-8')


def test_j14_static_input_authorization_is_engine_independent(tmp_path):
    _make_j14_inputs(tmp_path)
    v=validate_authority_inputs(tmp_path)
    assert v['ready'] is True
    cfg={
      'j14_authority_algorithm':{
        'name':'MINIMUM_DISPLACEMENT_MAXIMUM_ENTROPY_SPATIALIZATION','initialization':'MAXIMUM_ENTROPY_OVER_AGE_MATCHED_CANONICAL_LAND_SUPPORT',
        'persistence':'KEEP_PRIOR_DEME_CELL_WHILE_CANONICALLY_ACCESSIBLE','support_loss':'MINIMUM_GRID_DISTANCE_REMAP_TO_ACCESSIBLE_SUPPORT',
        'deme_fission':'DETERMINISTIC_FARTHEST_POINT_ADDITION_ON_ACCESSIBLE_SUPPORT','deme_contraction':'DETERMINISTIC_LOWEST_SEPARATION_REMOVAL',
        'population_allocation':'MAXIMUM_ENTROPY_EQUAL_SHARE_OF_R327_EFFECTIVE_POPULATION','future_spatial_anchor_usage':'FORBIDDEN_IN_CONSTRUCTION','external_engine_usage':'FORBIDDEN'},
      'r42_j14_mutation_forbidden':True,'geonomics_execution_authorized':False,'j14_replay_construction_may_not_use_r315_or_r328_spatial_coordinates':True
    }
    parent={'implementation_preflight_ready':True,'r42_j14_mutation_authorized':False}
    o=authorize_j14(tmp_path,parent,cfg)
    assert o['canonical_spatial_replay_execution_authorized_in_r430'] is True
    assert o['geonomics_execution_authorized_in_r430_by_r429'] is False
    assert len(o['input_hash_freeze'])>=7


def test_spatialization_is_deterministic_and_land_constrained():
    support=np.zeros((5,8),float); support[1:4,1:7]=1
    a=maximum_entropy_seed(support,4,123)
    b=maximum_entropy_seed(support,4,123)
    assert a==b and len(a)==4
    assert all(support[r,c]>0 for r,c in a)
    support2=support.copy(); support2[a[0]]=0
    c=advance_minimum_displacement(a,support2,3,456)
    assert len(c)==3
    assert all(support2[r,c0]>0 for r,c0 in c)
