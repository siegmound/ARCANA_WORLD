import json
from pathlib import Path
from arcana_worldsim.scientific_engines.r42_historical_materialization import build_jobs, build_mapping_contract, load_json

def cfg():
    return load_json(Path(__file__).parents[1]/'configs/world1_r42_historical_window_materialization_v0_6D1_R4_2.json')

def test_exact_windows(): assert len(cfg()['windows'])==7
def test_exact_jobs(): assert len(build_jobs(cfg()))==23
def test_job_ids_unique():
    j=build_jobs(cfg()); assert len({x['job_id'] for x in j})==23
def test_no_result_selection(): assert all(not x['result_selected'] for x in build_jobs(cfg()))
def test_no_canonical_writes(): assert all(not x['canonical_write'] for x in build_jobs(cfg()))
def test_no_majority_vote(): assert cfg()['materialization_policy']['majority_vote'] is False
def test_no_historical_execution_in_r42(): assert cfg()['materialization_policy']['historical_execution_in_r42'] is False
def test_five_discordance_classes(): assert set(cfg()['discordance_classes'])=={'CONCORDANT','CALIBRATION_OFFSET','STRUCTURAL_DISAGREEMENT','SEMANTICALLY_NONCOMPARABLE','INSUFFICIENT_EVIDENCE'}
def test_fifteen_domains(): assert len(cfg()['comparison_domains'])==15
def test_mapping_contract_frozen(): assert build_mapping_contract(cfg(),build_jobs(cfg()))['status']=='FROZEN_PRE_RESULT'
def test_range_semantics_explicit(): assert 'SINGLE_REP_POSITIVE_ABUNDANCE' in build_mapping_contract(cfg(),build_jobs(cfg()))['semantics']['range_occupancy_mapping']
def test_all_jobs_have_mapping_fields(): assert all(len(x['required_mapping_fields'])==5 for x in build_jobs(cfg()))
def test_window_boundaries_unique(): assert len({x['earliest_replay_boundary'] for x in cfg()['windows']})==7
def test_deep_off(): assert cfg()['deep_biological_coupling'] is False
def test_owner_arcana(): assert cfg()['canonical_state_owner']=='ARCANA_WorldSim'
def test_no_auto_promotion(): assert cfg()['automatic_external_evidence_promotion'] is False
