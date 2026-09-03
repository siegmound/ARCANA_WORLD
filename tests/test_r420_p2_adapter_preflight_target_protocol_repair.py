from pathlib import Path
from arcana_worldsim.scientific_engines.r420_p2_adapter_preflight_target_protocol_repair import engine_enhancement_contract,_repair_target_record,discover_adapter_sources,build_target_repairs

def test_engine_contracts_fail_closed_semantics():
    c=engine_enhancement_contract('CDMetaPOP','x','population_persistence');assert any('PROXY_ONLY' in x for x in c['requirements'])
    n=engine_enhancement_contract('NEMO','x','additive_variance');assert 'heterozygosity == additive_variance' in n['forbidden']
    s=engine_enhancement_contract('SLiM','x','ancestry');assert 'diversity == ancestry' in s['forbidden']
    g=engine_enhancement_contract('Geonomics','x','connectivity');assert 'ARCANA_LANDSCAPE_BINDING_LAYER'==g['implementation_family']

def test_target_design_gap_does_not_invent_number():
    r=_repair_target_record({'window_id':'W','domain':'d','backlog_class':'NEW_CANONICAL_TARGET_DESIGN_REQUIRED','priority':'P1_TARGET_DESIGN'});assert r['numeric_target_materialized_in_r420'] is False and 'NO_NUMERIC_TARGET_INVENTED' in r['repair_disposition']

def test_rejected_target_does_not_authorize_numeric_change():
    r=_repair_target_record({'window_id':'W','domain':'d','backlog_class':'MATERIALIZED_TARGET_OR_PRIMARY_METRIC_SEMANTIC_REPAIR_REQUIRED','r418_failed_validation_fields':{'temporal_basis_matches_window':False}});assert r['numeric_value_change_authorized'] is False and 'temporal_basis_matches_window' in r['failed_validation_keys']

def test_target_accounting_57_2():
    rs=[]
    for i in range(44):rs.append({'window_id':f'E{i}','domain':'d','backlog_class':'CANONICAL_TARGET_EXTRACTOR_OR_EXPLICIT_DESCRIPTOR_REQUIRED','priority':'P1_TARGET_EXTRACTOR_REPAIR'})
    for i in range(12):rs.append({'window_id':f'N{i}','domain':'d','backlog_class':'NEW_CANONICAL_TARGET_DESIGN_REQUIRED','priority':'P1_TARGET_DESIGN'})
    rs.append({'window_id':'R','domain':'d','backlog_class':'MATERIALIZED_TARGET_OR_PRIMARY_METRIC_SEMANTIC_REPAIR_REQUIRED','priority':'P1_SEMANTIC_REPAIR'})
    rs += [{'window_id':'P1','domain':'d','backlog_class':'CONTEXT_ONLY_PROXY_PRESERVE','priority':'P4'},{'window_id':'P2','domain':'d','backlog_class':'CONTEXT_ONLY_PROXY_PRESERVE','priority':'P4'}]
    o=build_target_repairs({'records':rs});assert o['record_count']==59 and o['active_repair_count']==57 and o['context_only_proxy_count']==2

def test_adapter_discovery_uses_engine_token(tmp_path:Path):
    p=tmp_path/'benchmarks'/'r43';p.mkdir(parents=True);f=p/'nemo_r43.py';f.write_text('# NEMO adapter\n',encoding='utf-8');hits=discover_adapter_sources(tmp_path,'NEMO');assert len(hits)==1 and hits[0]['path'].endswith('nemo_r43.py')
