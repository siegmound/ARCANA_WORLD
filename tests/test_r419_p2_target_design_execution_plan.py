from arcana_worldsim.scientific_engines.r419_p2_target_design_execution_plan import _infer_engine,_p2_mechanism,build_target_plan

def test_geonomics_inferred_from_action():
    e,b=_infer_engine({'closure_action':'GEONOMICS_ARCANA_LANDSCAPE_ADAPTER_REQUIRED'},[]);assert e=='Geonomics' and b=='CLOSURE_ACTION_ENGINE_BINDING'

def test_unique_primary_engine_inference():
    e,b=_infer_engine({'window_id':'W','domain':'d'},[{'window_id':'W','domain':'d','authority_role':'PRIMARY','engine':'SLiM'}]);assert e=='SLiM'

def test_p2_mechanisms():
    assert _p2_mechanism({'source_stage':'R4.15-R1'})=='OUTPUT_METRIC_EXTRACTION_OR_RUNTIME_BINDING_ENHANCEMENT'
    assert _p2_mechanism({'source_stage':'R4.17'})=='DOMAIN_METRIC_SEMANTIC_ADAPTER_OR_MATCHED_PROTOCOL_ENHANCEMENT'

def test_target_backlog_57_plus_2_proxy():
    records=[]
    for i in range(44): records.append({'window_id':f'W{i}','domain':'d','candidate_source_count':1,'materialization_status':'SOURCE_CANDIDATES_INSPECTED_NO_STRICT_TARGET_MATERIALIZED'})
    for i in range(12): records.append({'window_id':f'N{i}','domain':'d','candidate_source_count':0,'materialization_status':'NO_CANONICAL_SOURCE_CANDIDATE_TARGET_DESIGN_GAP'})
    records.append({'window_id':'R','domain':'d','candidate_source_count':1,'materialization_status':'MATERIALIZED','candidate_comparability':'DIRECT_CANDIDATE','materialized_target':{}})
    records += [{'window_id':'P1','domain':'d','candidate_source_count':1,'materialization_status':'MATERIALIZED','candidate_comparability':'PROXY_ONLY','materialized_target':{}},{'window_id':'P2','domain':'d','candidate_source_count':1,'materialization_status':'MATERIALIZED','candidate_comparability':'PROXY_ONLY','materialized_target':{}}]
    val={'records':[{'window_id':'R','domain':'d','validation_status':'REJECTED_REMAINS_NONADJUDICATIVE','reason':'x'}]}
    o=build_target_plan({'records':records},val);assert o['total_p1_records']==59 and o['active_target_design_or_semantic_repair_count']==57 and o['context_only_proxy_count']==2
