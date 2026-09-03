from pathlib import Path
import copy, json, shutil
import pytest

from arcana_worldsim.scientific_engines.r44_discordance_adjudication import (
    CLASSES, COMPLETE, R43_COMPLETE, R43_SEALED, SEALED,
    _descriptor_target, classify_pair, adjudicate, final_seal, load_json, write_json,
)

ROOT=Path(__file__).resolve().parents[1]
CFG=load_json(ROOT/'configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json')

def test_five_classes_exact():
    assert CFG['discordance_classes']==CLASSES

def test_no_majority_vote():
    assert CFG['majority_vote'] is False
    assert 'majority' not in CFG['authority_precedence']['primary_resolution'].lower() or 'not voting' in CFG['authority_precedence']['primary_resolution'].lower()

def test_policy_is_pre_metric_and_not_result_selected():
    assert CFG['policy_freeze']['result_selected'] is False
    assert CFG['policy_freeze']['status']=='FROZEN_BEFORE_R44_NUMERICAL_METRIC_INSPECTION'

def _stats(med,q10=None,q90=None):
    return {'n':4,'mean':med,'median':med,'q10':med if q10 is None else q10,'q90':med if q90 is None else q90,'min':med,'max':med}

def test_normalizable_opposite_direction_is_structural():
    t={'kind':'ratio','value':0.7,'metric':'x','comparability':'NORMALIZABLE'}
    r=classify_pair(t,'population_response_ratio',_stats(1.3),'NORMALIZABLE',CFG)
    assert r['discordance_class']=='STRUCTURAL_DISAGREEMENT'

def test_proxy_opposite_direction_cannot_be_structural():
    t={'kind':'ratio','value':0.7,'metric':'x','comparability':'PROXY_ONLY'}
    r=classify_pair(t,'population_response_ratio',_stats(1.3),'NORMALIZABLE',CFG)
    assert r['discordance_class']=='CALIBRATION_OFFSET'

def test_same_direction_near_scale_is_concordant():
    t={'kind':'ratio','value':1.20,'metric':'x','comparability':'NORMALIZABLE'}
    r=classify_pair(t,'population_response_ratio',_stats(1.22),'NORMALIZABLE',CFG)
    assert r['discordance_class']=='CONCORDANT'

def test_same_direction_large_scale_is_calibration_offset():
    t={'kind':'ratio','value':1.10,'metric':'x','comparability':'NORMALIZABLE'}
    r=classify_pair(t,'population_response_ratio',_stats(3.0),'NORMALIZABLE',CFG)
    assert r['discordance_class']=='CALIBRATION_OFFSET'

def test_both_neutral_is_concordant():
    t={'kind':'ratio','value':1.01,'metric':'x','comparability':'NORMALIZABLE'}
    r=classify_pair(t,'population_response_ratio',_stats(0.99),'NORMALIZABLE',CFG)
    assert r['discordance_class']=='CONCORDANT'

def test_h0_population_target():
    d={'descriptor_type':'H0_SNAPSHOT_WINDOW','comparison_only_derived':{'population_ratio':0.9},'start_state':{},'comparison_target_end_state':{}}
    t=_descriptor_target(d,'population_persistence')
    assert t['kind']=='ratio' and t['value']==pytest.approx(0.9) and t['comparability']=='NORMALIZABLE'

def test_h0_range_target_is_proxy():
    d={'descriptor_type':'H0_SNAPSHOT_WINDOW','comparison_only_derived':{'component_ratio':1.2},'start_state':{},'comparison_target_end_state':{}}
    assert _descriptor_target(d,'range_occupancy')['comparability']=='PROXY_ONLY'

def test_r327_population_target():
    d={'descriptor_type':'R327_SAPIENT_MACRO_ENSEMBLE_WINDOW','comparison_only_derived':{'population_ratio_median':1.8},'start_state':{},'comparison_target_end_state':{}}
    assert _descriptor_target(d,'population_persistence')['value']==pytest.approx(1.8)

def test_r328_admixture_target():
    d={'descriptor_type':'R328_SAPIENT_HIGH_RES_ENSEMBLE_WINDOW','comparison_only_derived':{'admixture_delta':0.04},'start_state':{},'comparison_target_end_state':{}}
    t=_descriptor_target(d,'admixture'); assert t['kind']=='delta' and t['comparability']=='NORMALIZABLE'

def test_producer_divergence_target():
    d={'descriptor_type':'R334_PRODUCER_COEVOLUTION_WINDOW','comparison_only_derived':{'selective_divergence_delta':0.03},'start_state':{},'comparison_target_end_state':{}}
    t=_descriptor_target(d,'producer_divergence'); assert t['comparability']=='NORMALIZABLE'

def _copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)

def build_synthetic_parent(tmp_path: Path):
    # Copy immutable governance/materialization documents from the repository, but synthesize only R4.3 execution values.
    for rel in [
      'configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json',
      'configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json',
      'outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json',
      'outputs/v0_6D1_R4_1/R4_1_SEMANTIC_AUTHORITY_MATRIX.json',
      'outputs/v0_6D1_R4_3/R4_3_PER_JOB_UNIT_MAPPING.json',
      'outputs/v0_6D1_R4_3/R4_3_WINDOW_BASELINE_DESCRIPTORS.json',
    ]: _copy(ROOT/rel,tmp_path/rel)
    jobs=load_json(tmp_path/'outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json')['jobs']
    geos={j['job_id'] for j in jobs if j['engine']=='Geonomics'}
    rows=[]
    for j in jobs:
        tc='SEMANTIC_NONCOMPARABILITY' if j['job_id'] in geos else 'SCIENTIFIC_RESULT'
        rows.append({'job_id':j['job_id'],'engine':j['engine'],'terminal_class':tc,'status':'PASS_EVIDENCE','job_engine_identity_match':True,'seed_ledger_match':True,'canonical_write_declared_false':True,'scientific_discordance_adjudicated':False})
        nd={'stage':'v0.6D1-R4.3','job_id':j['job_id'],'engine':j['engine'],'normalized_metrics':{},'canonical_write':False}
        # Add conservative synthetic metrics only where the R4.4 policy has candidate names.
        eng=j['engine']
        if eng=='RangeShifter': nd['normalized_metrics']={'population_response_ratio':_stats(1.0),'occupancy_response_ratio':_stats(1.0)}
        elif eng=='CDMetaPOP': nd['normalized_metrics']={'population_agent_response_ratio':_stats(1.0),'patch_occupancy_response_ratio':_stats(1.0)}
        elif eng=='Madingley': nd['normalized_metrics']={'cohort_response_ratio':_stats(1.0),'autotroph_biomass_response_ratio':_stats(1.0),'heterotroph_biomass_response_ratio':_stats(1.0)}
        elif eng=='NEMO': nd['normalized_metrics']={'genetic_gap_response_ratio':_stats(1.0),'allele_frequency_gap_delta':_stats(0.0)}
        elif eng=='SLiM': nd['normalized_metrics']={'population_agent_response_ratio':_stats(1.0)}
        write_json(tmp_path/'outputs/v0_6D1_R4_3/jobs'/j['job_id']/'NORMALIZED_EVIDENCE.json',nd)
    counts={k:sum(r['terminal_class']==k for r in rows) for k in ['SCIENTIFIC_RESULT','SEMANTIC_NONCOMPARABILITY','ENGINE_EXECUTION_FAILURE','ADAPTER_FAILURE','MISSING_EVIDENCE']}
    write_json(tmp_path/'outputs/v0_6D1_R4_3/R4_3_EXECUTION_SUMMARY.json',{'stage':'v0.6D1-R4.3','status':R43_COMPLETE,'job_count':23,'terminal_counts':counts,'jobs':rows})
    write_json(tmp_path/'outputs/v0_6D1_R4_3/R4_3_COMPLETENESS_AUDIT.json',{'stage':'v0.6D1-R4.3','status':R43_COMPLETE,'checks_failed':0,'terminal_counts':counts})
    write_json(tmp_path/'outputs/v0_6D1_R4_3_SEAL/R4_3_FINAL_SEAL_AUDIT.json',{'stage':'v0.6D1-R4.3','status':R43_SEALED,'verdict':'SEALED'})
    return jobs

def test_full_adjudication_classifies_every_scope_cell(tmp_path):
    build_synthetic_parent(tmp_path)
    r,checks=adjudicate(tmp_path)
    assert r['status']==COMPLETE
    assert all(c.passed for c in checks)
    matrix=load_json(tmp_path/'outputs/v0_6D1_R4_4/R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json')
    r43=load_json(tmp_path/'configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json')
    assert matrix['cell_count']==sum(len(v) for v in r43['window_domain_scope'].values())
    assert sum(matrix['class_counts'].values())==matrix['cell_count']

def test_secondary_only_cannot_promote_domain(tmp_path):
    build_synthetic_parent(tmp_path)
    adjudicate(tmp_path)
    m=load_json(tmp_path/'outputs/v0_6D1_R4_4/R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json')
    for c in m['cells']:
        if c['primary_adjudicative_rows']==0:
            assert c['discordance_class'] not in ('CONCORDANT','CALIBRATION_OFFSET','STRUCTURAL_DISAGREEMENT')

def test_final_seal_allows_scientific_disagreement_but_not_process_failure(tmp_path):
    build_synthetic_parent(tmp_path)
    adjudicate(tmp_path)
    out,checks=final_seal(tmp_path)
    assert out['status']==SEALED and out['verdict']=='SEALED'
    assert all(c.passed for c in checks)

def test_r44_never_authorizes_replay_or_canonical_write(tmp_path):
    build_synthetic_parent(tmp_path); adjudicate(tmp_path); final_seal(tmp_path)
    s=load_json(tmp_path/'outputs/v0_6D1_R4_4/R4_4_ADJUDICATION_SUMMARY.json')
    assert s['canonical_state_changed'] is False
    assert s['replay_authorized'] is False
    assert s['scientific_agreement_claimed'] is False
