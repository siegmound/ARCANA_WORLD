from pathlib import Path
import shutil
import pytest

from arcana_worldsim.scientific_engines.r45_causal_diagnosis import (
    COMPLETE, SEALED, R44_SEALED, R44_COMPLETE, DIAG_CLASSES,
    load_json, write_json, robust_quantile_direction, diagnose_structural_row, diagnose, final_seal,
)

ROOT=Path(__file__).resolve().parents[1]
CFG=load_json(ROOT/'configs/world1_r45_causal_diagnosis_v0_6D1_R4_5.json')

def _stats(med,q10,q90,n=4):
    return {'n':n,'mean':med,'median':med,'q10':q10,'q90':q90,'min':q10,'max':q90}

def test_policy_pre_result_and_no_majority_vote():
    assert CFG['policy_freeze']['result_selected'] is False
    assert CFG['majority_vote'] is False
    assert CFG['canonical_replay_authorized'] is False

def test_diag_classes_exact():
    assert CFG['structural_diagnosis_classes']==DIAG_CLASSES

def test_ratio_robust_positive_quantiles():
    d,r=robust_quantile_direction('population_response_ratio',_stats(1.3,1.2,1.4),CFG)
    assert d==1 and 'POSITIVE' in r

def test_ratio_robust_negative_quantiles():
    d,r=robust_quantile_direction('population_response_ratio',_stats(.7,.6,.8),CFG)
    assert d==-1 and 'NEGATIVE' in r

def test_ratio_overlap_is_not_robust():
    d,r=robust_quantile_direction('population_response_ratio',_stats(1.2,.99,1.4),CFG)
    assert d is None and 'CROSSES' in r

def test_delta_robust_positive_quantiles():
    d,_=robust_quantile_direction('allele_frequency_gap_delta',_stats(.1,.05,.15),CFG)
    assert d==1

def _structural_row(q10=1.2,q90=1.4,n=4):
    return {
      'window_id':'H0_POST_CHA1_RECOVERY','domain':'population_persistence','job_id':'R42_J08_TEST','engine':'RangeShifter',
      'authority_role':'PRIMARY','mapping_comparability':'NORMALIZABLE','discordance_class':'STRUCTURAL_DISAGREEMENT',
      'target_direction':-1,'external_direction':1,
      'target':{'kind':'ratio','value':.8,'metric':'ARCANA_total_population_ratio','comparability':'NORMALIZABLE'},
      'metric':{'name':'population_response_ratio','summary':_stats(1.3,q10,q90,n)},
    }

def test_structural_row_robust_gate():
    d=diagnose_structural_row(_structural_row(),CFG)
    assert d['diagnosis_class']=='ROBUST_PRIMARY_STRUCTURAL_DISAGREEMENT'
    assert d['diagnostic_counterfactual_authorized'] is True

def test_structural_row_uncertainty_overlap_blocks():
    d=diagnose_structural_row(_structural_row(.99,1.4),CFG)
    assert d['diagnosis_class']=='STRUCTURAL_CANDIDATE_UNCERTAINTY_OVERLAP'
    assert d['diagnostic_counterfactual_authorized'] is False

def test_structural_row_insufficient_replicates_blocks():
    d=diagnose_structural_row(_structural_row(n=3),CFG)
    assert d['diagnosis_class']=='STRUCTURAL_CANDIDATE_INSUFFICIENT_REPLICATES'

def _copy(rel,tmp):
    s=ROOT/rel; d=tmp/rel; d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(s,d)

def build_parent(tmp: Path, robust=True):
    _copy('configs/world1_r45_causal_diagnosis_v0_6D1_R4_5.json',tmp)
    # Authority files required for R3.11 causal trace.
    for rel in [
      'CANONICAL_POST_CHA1_H0_RECOVERY_ADAPTIVE_RADIATION_RESTART_CONTRACT_v0_6D1_R3_11.md',
      'configs/world1_r311_postcha1_recovery_v0_6D1_R3_11.json',
      'src/arcana_worldsim/scientific_engines/r311_postcha1_recovery.py',
      'src/arcana_worldsim/scientific_engines/r38_restartable_checkpoint.py',
      'src/d3_additive_variance_v0_6_3D3_3A.py',
    ]: _copy(rel,tmp)
    write_json(tmp/'outputs/v0_6D1_R4_4_SEAL/R4_4_FINAL_SEAL_AUDIT.json',{'stage':'v0.6D1-R4.4','status':R44_SEALED,'verdict':'SEALED'})
    write_json(tmp/'outputs/v0_6D1_R4_4/R4_4_INTEGRATED_AUDIT.json',{'stage':'v0.6D1-R4.4','status':R44_COMPLETE,'checks_failed':0})
    sr=_structural_row(1.2 if robust else .99,1.4)
    offset={
      'window_id':'H0_PRE_CHA1','domain':'population_persistence','job_id':'JX','engine':'Madingley','authority_role':'PRIMARY',
      'mapping_comparability':'NORMALIZABLE','discordance_class':'CALIBRATION_OFFSET','reason':'SAME_DIRECTION_DIFFERENT_EFFECT_SCALE_COMPRESSED_RUNTIME',
      'target_direction':1,'external_direction':1,'target':{'kind':'ratio','value':1.1,'comparability':'NORMALIZABLE'},
      'metric':{'name':'cohort_response_ratio','summary':_stats(3.0,2.5,3.5)}
    }
    gaprow={'window_id':'SAPIENT_3MA_TO_200KA','domain':'ancestry','job_id':'JG','engine':'SLiM','authority_role':'PRIMARY','mapping_comparability':'NORMALIZABLE','discordance_class':'INSUFFICIENT_EVIDENCE','reason':'NO_R43_NORMALIZED_RESULT_METRIC_FOR_DOMAIN','target':{'kind':'delta','value':.1,'comparability':'NORMALIZABLE'},'metric':None}
    semrow={'window_id':'SAPIENT_200KA_TO_0','domain':'connectivity','job_id':'JGE','engine':'Geonomics','authority_role':'PRIMARY','mapping_comparability':'NONCOMPARABLE','discordance_class':'SEMANTICALLY_NONCOMPARABLE','reason':'R43_ENGINE_JOB_SEMANTIC_NONCOMPARABILITY','target':None,'metric':None}
    cells=[
      {'window_id':'H0_POST_CHA1_RECOVERY','domain':'population_persistence','discordance_class':'STRUCTURAL_DISAGREEMENT','earliest_affected_authority_candidate':'R3.11_POST_CHA1'},
      {'window_id':'H0_PRE_CHA1','domain':'population_persistence','discordance_class':'CALIBRATION_OFFSET','earliest_affected_authority_candidate':None},
      {'window_id':'SAPIENT_3MA_TO_200KA','domain':'ancestry','discordance_class':'INSUFFICIENT_EVIDENCE','earliest_affected_authority_candidate':None},
      {'window_id':'SAPIENT_200KA_TO_0','domain':'connectivity','discordance_class':'SEMANTICALLY_NONCOMPARABLE','earliest_affected_authority_candidate':None},
    ]
    write_json(tmp/'outputs/v0_6D1_R4_4/R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json',{'stage':'v0.6D1-R4.4','status':R44_COMPLETE,'cell_count':4,'class_counts':{'CONCORDANT':0,'CALIBRATION_OFFSET':1,'STRUCTURAL_DISAGREEMENT':1,'SEMANTICALLY_NONCOMPARABLE':1,'INSUFFICIENT_EVIDENCE':1},'cells':cells,'evidence_rows':[sr,offset,gaprow,semrow]})
    write_json(tmp/'outputs/v0_6D1_R4_4/R4_4_ADJUDICATION_SUMMARY.json',{'stage':'v0.6D1-R4.4','status':R44_COMPLETE,'earliest_affected_authority_candidate':'R3.11_POST_CHA1','canonical_state_changed':False})

def test_full_diagnosis_robust_structural_authorizes_only_counterfactual(tmp_path):
    build_parent(tmp_path,True)
    out,checks=diagnose(tmp_path)
    assert out['status']==COMPLETE and all(c.passed for c in checks)
    d=load_json(tmp_path/'outputs/v0_6D1_R4_5/R4_5_STRUCTURAL_DISAGREEMENT_DIAGNOSIS.json')
    g=load_json(tmp_path/'outputs/v0_6D1_R4_5/R4_5_REPLAY_AUTHORIZATION_GATE.json')
    assert d['robust_structural_cell_count']==1
    assert g['diagnostic_counterfactual_authorized'] is True
    assert g['canonical_replay_authorized'] is False
    assert 'R3_11_POST_CHA1' in g['next_action']

def test_uncertain_structural_routes_to_replicate_closure(tmp_path):
    build_parent(tmp_path,False)
    out,_=diagnose(tmp_path)
    g=load_json(tmp_path/'outputs/v0_6D1_R4_5/R4_5_REPLAY_AUTHORIZATION_GATE.json')
    assert out['status']==COMPLETE
    assert g['diagnostic_counterfactual_authorized'] is False
    assert g['next_action']=='EXECUTE_R46_TARGETED_PRIMARY_REPLICATE_ROBUSTNESS_CLOSURE'

def test_gap_plan_preserves_semantic_and_metric_gaps(tmp_path):
    build_parent(tmp_path,True); diagnose(tmp_path)
    g=load_json(tmp_path/'outputs/v0_6D1_R4_5/R4_5_EVIDENCE_GAP_CLOSURE_PLAN.json')
    assert g['count']==2
    assert g['closure_type_counts']['R43_NORMALIZED_METRIC_ADAPTER_REQUIRED']==1
    assert g['closure_type_counts']['SEMANTIC_ADAPTER_REQUIRED']==1

def test_offsets_never_auto_recalibrate(tmp_path):
    build_parent(tmp_path,True); diagnose(tmp_path)
    o=load_json(tmp_path/'outputs/v0_6D1_R4_5/R4_5_CALIBRATION_OFFSET_REGISTER.json')
    assert o['count']==1 and o['automatic_recalibration_authorized'] is False
    assert all(x['parameter_change_authorized'] is False for x in o['offsets'])

def test_r311_trace_lists_frozen_constants_and_present_sources(tmp_path):
    build_parent(tmp_path,True); diagnose(tmp_path)
    t=load_json(tmp_path/'outputs/v0_6D1_R4_5/R4_5_EARLIEST_AUTHORITY_TRACE.json')['traces'][0]
    assert t['boundary']=='R3.11_POST_CHA1'
    assert not t['authority_files_missing']
    assert 'q_ceiling=0.08' in t['r311_causal_surface']['scientific_constants_frozen']

def test_final_seal_passes_for_robust_diagnosis_without_canonical_replay(tmp_path):
    build_parent(tmp_path,True); diagnose(tmp_path)
    out,checks=final_seal(tmp_path)
    assert out['status']==SEALED and out['verdict']=='SEALED' and all(c.passed for c in checks)
    assert out['summary']['canonical_replay_authorized'] is False

def test_missing_authority_file_fails_closed(tmp_path):
    build_parent(tmp_path,True)
    (tmp_path/'src/d3_additive_variance_v0_6_3D3_3A.py').unlink()
    out,checks=diagnose(tmp_path)
    assert out['status'].startswith('BLOCKED_')
    assert not next(c for c in checks if c.name=='all_structural_boundaries_trace_to_present_authority_files').passed
