from __future__ import annotations
from pathlib import Path
import json, math

from arcana_worldsim.scientific_engines import r47_cdmetapop_forcing_parity as r47

ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/r47.CFG_REL).read_text(encoding='utf-8'))

def _contract(drivers=None):
    return {
      'frozen_parent_job':{'job_id':'J'},
      'engine_input':{
        'drivers':drivers or {
          'normalized_habitat_fraction_start':0.4,
          'normalized_habitat_fraction_end':0.5,
          'normalized_environment_change':-0.1,
        },
        'replicates':[{'replicate_index':0,'seed':11},{'replicate_index':1,'seed':22}],
      },
    }

def test_stage_and_parent_contract():
    assert CFG['stage']=='v0.6D1-R4.7'
    assert CFG['required_parent_status']==r47.R46_SEALED
    assert CFG['required_parent_finding']=='R43_CDMETAPOP_POPULATION_PERSISTENCE_DYNAMIC_FORCING_COVERAGE_GAP_CONFIRMED'

def test_exact_five_symmetric_jobs():
    ids=CFG['affected_frozen_jobs']
    assert len(ids)==5 and len(set(ids))==5
    assert ids==[
      'R42_J03_H0_DEEP_TIME_BACKGROUND_CDMETAPOP',
      'R42_J06_H0_PRE_CHA1_CDMETAPOP',
      'R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP',
      'R42_J15_SAPIENT_3MA_TO_200KA_CDMETAPOP',
      'R42_J20_SAPIENT_200KA_TO_0_CDMETAPOP']

def test_policy_is_not_result_selected_and_no_canonical_change():
    assert CFG['policy_freeze']['result_selected'] is False
    assert CFG['canonical_state_changed'] is False
    assert CFG['canonical_replay_authorized'] is False
    assert CFG['canonical_parameter_change_authorized'] is False
    assert CFG['majority_vote'] is False
    assert CFG['deep_biological_coupling'] is False

def test_h0_support_uses_exogenous_a1_reference_population_not_comparison_target():
    desc={'descriptor_type':'H0_SNAPSHOT_WINDOW','exogenous_physical_forcing':{'source':'x.npz','sha256':'abc','start':{'mean_population':100.0},'end':{'mean_population':93.0}}}
    p=r47._support_profile(CFG,_contract(),desc)
    assert p['forcing_source']=='A1_EXOGENOUS_REFERENCE_POPULATION_RATIO'
    assert math.isclose(p['raw_end_support_ratio'],0.93)
    assert p['comparison_target_used'] is False

def test_non_h0_support_uses_frozen_driver_relative_support():
    desc={'descriptor_type':'R327_SAPIENT_MACRO_ENSEMBLE_WINDOW'}
    p=r47._support_profile(CFG,_contract(),desc)
    assert p['forcing_source']=='FROZEN_R43_HABITAT_X_ENVIRONMENT_RELATIVE_SUPPORT'
    assert math.isclose(p['raw_end_support_ratio'],(0.5/0.4)*0.9)

def test_fixed_safety_bound_is_fail_safe_not_result_selected():
    c=_contract({'normalized_habitat_fraction_start':0.1,'normalized_habitat_fraction_end':0.9,'normalized_environment_change':1.0})
    p=r47._support_profile(CFG,c,{'descriptor_type':'R327_SAPIENT_MACRO_ENSEMBLE_WINDOW'})
    assert p['raw_end_support_ratio']>4.0
    assert p['bounded_end_support_ratio']==4.0
    assert p['safety_bound_active'] is True

def test_pinned_cdmetapop_source_supports_dynamic_k_through_cdclimate():
    cap=r47._cdmetapop_source_capability(ROOT)
    assert cap['dynamic_k_supported'] is True
    assert all(cap['checks'].values())
    assert cap['source_tree_modified'] is False

def test_r47_adapter_uses_dynamic_k_and_does_not_pipe_n0():
    s=(ROOT/'benchmarks/r47/cdmetapop_r47.py').read_text(encoding='utf-8')
    assert "row['K']='|'.join" in s
    assert "row['N0']=str(" in s
    assert "row['N0']='|'.join" not in s
    assert "comparison_target_used':False" in s
    assert "cdclimgentime" in s

def test_r47_adapter_preserves_exact_cdmetapop_pin():
    s=(ROOT/'benchmarks/r47/cdmetapop_r47.py').read_text(encoding='utf-8')
    assert "3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118" in s
    assert "git','-C',str(repo),'rev-parse','HEAD'" in s

def test_terminal_and_seed_guards():
    c=_contract(); raw={'adapter_status':'PASS','replicates':[{'replicate_index':0,'seed':11,'status':'PASS'},{'replicate_index':1,'seed':22,'status':'PASS'}]}
    assert r47._terminal_for_raw(raw,c)[0]=='SCIENTIFIC_RESULT'
    assert r47._seed_match(raw,c) is True
    raw['replicates'][1]['seed']=23
    assert r47._seed_match(raw,c) is False

def test_readjudication_reuses_r44_classifier_not_new_thresholds():
    s=(ROOT/'src/arcana_worldsim/scientific_engines/r47_cdmetapop_forcing_parity.py').read_text(encoding='utf-8')
    assert 'r44.classify_pair' in s
    assert 'R44_CFG_REL' in s
    assert 'domain_metric_candidates' not in CFG

def test_runner_has_prepare_and_single_job_repair_modes():
    s=(ROOT/'run_v0_6D1_R4_7.ps1').read_text(encoding='utf-8')
    assert '[switch]$PrepareOnly' in s
    assert '[string]$JobId' in s
    assert 'capture_v0_6D1_R4_7_cdmetapop_jobs.ps1' in s

def test_bridge_writes_new_namespace_and_never_overwrites_r43():
    s=(ROOT/'capture_v0_6D1_R4_7_cdmetapop_jobs.ps1').read_text(encoding='utf-8')
    assert 'outputs\\v0_6D1_R4_7' in s
    assert 'outputs\\v0_6D1_R4_3\\jobs' in s
    assert 'benchmarks/r47/cdmetapop_r47.py' in s
    assert 'Remove-Item -Force $Contract' not in s

def test_r47_seal_can_report_structural_result_without_auto_replay():
    s=(ROOT/'src/arcana_worldsim/scientific_engines/r47_cdmetapop_forcing_parity.py').read_text(encoding='utf-8')
    assert 'BUILD_R48_POST_CDMETAPOP_REPAIR_STRUCTURAL_CAUSAL_DIAGNOSIS' in s
    assert 'canonical_replay_authorized":False' in s or 'canonical_replay_authorized\":False' in s
