from pathlib import Path
import json
from arcana_worldsim.scientific_engines.r432_target_authority_binding_geonomics_static import build_target_binding,_packet_current

def test_packet_current_exact_selector_and_hash(tmp_path:Path):
 p=tmp_path/'x.json'; p.write_text('{"a":1}')
 import hashlib
 h=hashlib.sha256(p.read_bytes()).hexdigest(); r=_packet_current(tmp_path,{'source':'x.json','expected_sha256':h,'exact_schema_inventory':['a'],'static_schema_valid':True},'a')
 assert r['hash_match'] and r['contains_frozen_selector']

def test_packet_current_drift_fails(tmp_path:Path):
 p=tmp_path/'x.json'; p.write_text('{}'); r=_packet_current(tmp_path,{'source':'x.json','expected_sha256':'0'*64,'exact_schema_inventory':['a'],'static_schema_valid':True},'a')
 assert not r['hash_match']

def test_no_numeric_or_result_selected_binding_tokens():
 import inspect,arcana_worldsim.scientific_engines.r432_target_authority_binding_geonomics_static as m
 s=inspect.getsource(m)
 assert 'numeric_target_execution_authorized_in_r432' in s
 assert 'result_selected_binding_used' in s

def test_geonomics_jobs_exact_three():
 import arcana_worldsim.scientific_engines.r432_target_authority_binding_geonomics_static as m
 assert {m.J14,m.J18,m.J21}=={'R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS','R42_J18_SAPIENT_200KA_TO_0_GEONOMICS','R42_J21_PRODUCER_20KA_TO_0_GEONOMICS'}

def test_next_stage_is_runtime_compilation_preflight():
 import arcana_worldsim.scientific_engines.r432_target_authority_binding_geonomics_static as m
 assert 'RUNTIME_PARAMETER_COMPILATION_PREFLIGHT' in m.NEXT
