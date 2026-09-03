from pathlib import Path
import json

from arcana_worldsim.scientific_engines.r412_cdmetapop_precision_comparability_diagnosis import (
    diagnose, final_seal, COMPLETE, SEALED, BLOCKED, FINDING, NEXT_DOWNGRADE, NEXT_PRECISION, AFFECTED, J09,
)


def wj(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(obj), encoding='utf-8')


def wt(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding='utf-8')


def fixture(tmp_path: Path, robust_relaxation: bool = True):
    root = tmp_path
    cfg = {
      'stage':'v0.6D1-R4.12',
      'required_parent_status':'PASS_R411_CDMETAPOP_POPULATION_METRIC_EXTRACTION_REPAIR_AND_SYMMETRIC_READJUDICATION_SEALED',
      'required_parent_next_action':'BUILD_R412_CDMETAPOP_METRIC_REPAIRED_PRECISION_AND_COMPARABILITY_DIAGNOSIS',
      'authorized_case':{'window_id':'H0_POST_CHA1_RECOVERY','domain':'population_persistence','engine':'CDMetaPOP','job_id':J09,'earliest_boundary':'R3.11_POST_CHA1'},
      'affected_frozen_cdmetapop_jobs':AFFECTED,
      'precision_policy':{'preserve_r411_readjudication_without_posthoc_reclassification':True,'automatic_additional_engine_replicates_forbidden':True,'use_frozen_r44_ratio_neutral_factor':True,'bootstrap_median_draws':1000,'bootstrap_rng_seed':41220260831,'bootstrap_is_descriptive_not_adjudicative':True},
      'comparability_policy':{'tested_metric':'population_agent_response_ratio','global_matched_control_metric_promotion_in_r412':False,'r413_if_downgrade':NEXT_DOWNGRADE},
      'canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'deep_biological_coupling':False,'majority_vote':False,'engine_execution_performed':False,
    }
    wj(root/'configs/world1_r412_cdmetapop_precision_comparability_v0_6D1_R4_12.json',cfg)
    wj(root/'outputs/v0_6D1_R4_11_SEAL/R4_11_FINAL_SEAL_AUDIT.json',{
      'status':'PASS_R411_CDMETAPOP_POPULATION_METRIC_EXTRACTION_REPAIR_AND_SYMMETRIC_READJUDICATION_SEALED',
      'next_action':cfg['required_parent_next_action']})
    wj(root/'outputs/v0_6D1_R4_11/R4_11_EXECUTION_SUMMARY.json',{
      'structural_disagreement_count_after_metric_repair':1,
      'j09_population_persistence_class_after_metric_repair':'STRUCTURAL_DISAGREEMENT',
      'corrected_matched_control_diagnosis':'R411_CORRECTED_MATCHED_CONTROL_EFFECT_UNCERTAIN'})
    rows=[]
    for i in range(20):
        neutral=(1.20 + 0.01*(i%5)) if robust_relaxation else (0.99 + 0.002*(i%5))
        pe=0.90 + 0.004*(i%10)
        if i==19: pe=0.98
        rows.append({'replicate_index':i,'seed':1000+i,'dynamic_initial':100.0,'dynamic_final':100.0*neutral*pe,'neutral_initial':100.0,'neutral_final':100.0*neutral,'dynamic_absolute_ratio':neutral*pe,'neutral_absolute_ratio':neutral,'paired_forcing_effect_ratio':pe,'initial_population_match':True})
    wj(root/'outputs/v0_6D1_R4_11/R4_11_CORRECTED_MATCHED_CONTROL_CAUSAL_EFFECT.json',{
      'stage':'v0.6D1-R4.11','pair_count':20,'paired_replicates':rows,
      'corrected_paired_effect_summary':{'n':20,'median':0.922,'q10':0.90,'q90':0.94,'min':0.90,'max':0.98},
      'arcana_causal_forcing_effect_ratio':0.9353883,'neutral_factor':1.05,
      'diagnosis_class':'R411_CORRECTED_MATCHED_CONTROL_EFFECT_UNCERTAIN'})
    cells=[{'window_id':'W','domain':f'd{i}','discordance_class':'INSUFFICIENT_EVIDENCE'} for i in range(75)]
    cells[0]={'window_id':'H0_POST_CHA1_RECOVERY','domain':'population_persistence','discordance_class':'STRUCTURAL_DISAGREEMENT'}
    ev=[
      {'window_id':'H0_POST_CHA1_RECOVERY','job_id':J09,'engine':'CDMetaPOP','domain':'population_persistence','authority_role':'PRIMARY','mapping_comparability':'NORMALIZABLE','discordance_class':'STRUCTURAL_DISAGREEMENT','reason':'OPPOSITE_DIRECTION','metric':{'name':'population_agent_response_ratio','summary':{'median':1.2}}},
      {'window_id':'H0_POST_CHA1_RECOVERY','job_id':J09,'engine':'CDMetaPOP','domain':'extinction_risk','authority_role':'PRIMARY','mapping_comparability':'NORMALIZABLE','discordance_class':'CALIBRATION_OFFSET','reason':'SCALE','metric':{'name':'population_agent_response_ratio','summary':{'median':1.2}}},
      {'window_id':'W','job_id':'OTHER','engine':'NEMO','domain':'gene_flow','authority_role':'PRIMARY','mapping_comparability':'NORMALIZABLE','discordance_class':'INSUFFICIENT_EVIDENCE','metric':None},
    ]
    wj(root/'outputs/v0_6D1_R4_11/R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json',{'stage':'v0.6D1-R4.11','cell_count':75,'class_counts':{'STRUCTURAL_DISAGREEMENT':1,'INSUFFICIENT_EVIDENCE':74},'cells':cells,'evidence_rows':ev})
    wj(root/'configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json',{'effect_policy':{'ratio_neutral_factor':1.05}})
    maps=[]
    for jid in AFFECTED:
        maps.append({'job_id':jid,'domain_mapping':[{'domain':'population_persistence','authority_role':'PRIMARY','comparability_class':'NORMALIZABLE'}]})
    wj(root/'outputs/v0_6D1_R4_3/R4_3_PER_JOB_UNIT_MAPPING.json',{'mappings':maps})
    wj(root/'outputs/v0_6D1_R4_3/jobs'/J09/'JOB_CONTRACT.json',{'engine_input':{'drivers':{'arcana_start_population_descriptor':1617.1}}})
    half="n0=max(10,int(round(k0*0.5))); row['N0']=str(n0)\n"
    for rel in ['benchmarks/r47/cdmetapop_r47.py','benchmarks/r48/cdmetapop_r48_neutral.py','benchmarks/r49/cdmetapop_r49_dynamic.py','benchmarks/r49/cdmetapop_r49_neutral.py']:
        wt(root/rel,half)
    return root


def test_robust_neutral_relaxation_confirms_comparability_finding(tmp_path):
    r=fixture(tmp_path,True);out,_=diagnose(r);assert out['status']==COMPLETE and out['finding']==FINDING and out['next_action']==NEXT_DOWNGRADE


def test_neutral_q10_above_frozen_upper_band(tmp_path):
    r=fixture(tmp_path,True);diagnose(r);d=json.load(open(r/'outputs/v0_6D1_R4_12/R4_12_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS.json'));assert d['neutral_control_class']=='NEUTRAL_CONTROL_ROBUST_UPWARD_RELAXATION' and d['neutral_absolute_response_summary']['q10']>1.05


def test_comparability_downgrade_is_proxy_only_not_canonical_change(tmp_path):
    r=fixture(tmp_path,True);diagnose(r);d=json.load(open(r/'outputs/v0_6D1_R4_12/R4_12_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS.json'));assert d['absolute_population_response_comparability'].startswith('PROXY_ONLY') and d['canonical_change_authorized'] is False


def test_r413_plan_is_symmetric_all_five(tmp_path):
    r=fixture(tmp_path,True);diagnose(r);d=json.load(open(r/'outputs/v0_6D1_R4_12/R4_12_R413_COMPARABILITY_PLAN.json'));assert d['symmetric_job_scope']==AFFECTED and d['new_engine_execution_authorized'] is False and any('ALL_FIVE' in x for x in d['actions'])


def test_parent_matrix_not_rewritten(tmp_path):
    r=fixture(tmp_path,True);p=r/'outputs/v0_6D1_R4_11/R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json';before=p.read_bytes();diagnose(r);assert p.read_bytes()==before


def test_selected_population_metric_rows_are_audited(tmp_path):
    r=fixture(tmp_path,True);diagnose(r);d=json.load(open(r/'outputs/v0_6D1_R4_12/R4_12_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS.json'));assert d['selected_row_count']==2 and {x['domain'] for x in d['selected_cdmetapop_population_response_rows']}=={'population_persistence','extinction_risk'}


def test_precision_bootstrap_is_descriptive_only(tmp_path):
    r=fixture(tmp_path,True);diagnose(r);d=json.load(open(r/'outputs/v0_6D1_R4_12/R4_12_METRIC_REPAIRED_PRECISION_AUDIT.json'));assert d['bootstrap_median']['adjudicative'] is False and d['precision_reclassification_authorized'] is False


def test_no_automatic_more_replicates(tmp_path):
    r=fixture(tmp_path,True);diagnose(r);d=json.load(open(r/'outputs/v0_6D1_R4_12/R4_12_METRIC_REPAIRED_PRECISION_AUDIT.json'));assert d['automatic_additional_engine_replicates_authorized'] is False


def test_source_audit_confirms_half_k_not_arcana_n0(tmp_path):
    r=fixture(tmp_path,True);diagnose(r);d=json.load(open(r/'outputs/v0_6D1_R4_12/R4_12_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS.json'));s=d['source_initialization_audit'];assert s['common_half_k_start_initialization'] is True and s['adapter_n0_not_initialized_from_arcana_population_descriptor'] is True


def test_stable_neutral_control_does_not_force_downgrade(tmp_path):
    r=fixture(tmp_path,False);out,_=diagnose(r);assert out['status']==COMPLETE and out['finding']!='R412_CDMETAPOP_ABSOLUTE_POPULATION_RESPONSE_NEUTRAL_INVARIANCE_FAILURE_CONFIRMED' and out['next_action']==NEXT_PRECISION


def test_missing_parent_pair_blocks(tmp_path):
    r=fixture(tmp_path,True);(r/'outputs/v0_6D1_R4_11/R4_11_CORRECTED_MATCHED_CONTROL_CAUSAL_EFFECT.json').unlink();out,_=diagnose(r);assert out['status']==BLOCKED


def test_final_seal_good_fixture(tmp_path):
    r=fixture(tmp_path,True);diagnose(r);out,checks=final_seal(r);assert out['status']==SEALED and out['verdict']=='SEALED' and out['next_action']==NEXT_DOWNGRADE and all(c.passed for c in checks)


def test_final_seal_blocks_without_diagnosis(tmp_path):
    r=fixture(tmp_path,True);out,_=final_seal(r);assert out['status']==BLOCKED
