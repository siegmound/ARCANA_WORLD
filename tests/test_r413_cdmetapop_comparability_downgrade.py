from pathlib import Path
import json

from arcana_worldsim.scientific_engines.r413_cdmetapop_comparability_downgrade import (
    readjudicate, final_seal, COMPLETE, SEALED, BLOCKED, R412_FINDING,
    NEXT_GAPS, AFFECTED, METRIC, J09,
)


def wj(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(obj), encoding='utf-8')


def fixture(tmp_path: Path):
    root = tmp_path
    cfg = {
      'stage':'v0.6D1-R4.13',
      'required_parent_status':'PASS_R412_CDMETAPOP_METRIC_REPAIRED_PRECISION_AND_COMPARABILITY_DIAGNOSIS_SEALED',
      'required_parent_finding':R412_FINDING,
      'required_parent_plan_status':'R413_COMPARABILITY_DOWNGRADE_PLAN_FROZEN',
      'affected_frozen_cdmetapop_jobs':AFFECTED,
      'comparability_override':{'engine':'CDMetaPOP','metric_name':METRIC,'from':['DIRECT','NORMALIZABLE'],'to':'PROXY_ONLY','reason':'R412_NEUTRAL_INVARIANCE_FAILURE_CONFIRMED','parent_r43_mapping_files_are_not_modified':True,'parent_r411_matrix_is_not_modified':True,'matched_control_global_metric_promotion':False},
      'readjudication_policy':{'reuse_frozen_r44_policy_exactly':True,'reuse_frozen_five_discordance_classes':True,'proxy_only_rows_are_contextual_not_adjudicative':True,'proxy_only_cannot_establish_structural_disagreement':True,'majority_vote':False},
      'completion_policy':{'all_75_cells_must_be_readjudicated':True,'no_engine_execution':True,'no_canonical_replay':True,'no_canonical_parameter_change':True},
      'canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'deep_biological_coupling':False,'majority_vote':False,'engine_execution_performed':False,
    }
    wj(root/'configs/world1_r413_cdmetapop_comparability_downgrade_v0_6D1_R4_13.json',cfg)
    wj(root/'outputs/v0_6D1_R4_12_SEAL/R4_12_FINAL_SEAL_AUDIT.json',{'status':cfg['required_parent_status'],'next_action':'BUILD_R413_CDMETAPOP_ABSOLUTE_RESPONSE_COMPARABILITY_DOWNGRADE_AND_READJUDICATION'})
    wj(root/'outputs/v0_6D1_R4_12/R4_12_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS.json',{'finding':R412_FINDING,'absolute_population_response_comparability':'PROXY_ONLY_PENDING_MATCHED_CONTROL_SEMANTIC_PROTOCOL'})
    wj(root/'outputs/v0_6D1_R4_12/R4_12_R413_COMPARABILITY_PLAN.json',{'status':'R413_COMPARABILITY_DOWNGRADE_PLAN_FROZEN','symmetric_job_scope':AFFECTED,'metric_scope':METRIC})
    # Frozen policy dependencies used by the R4.7 cell recomputation helper.
    wj(root/'configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json',{
      'effect_policy':{'ratio_neutral_factor':1.05,'delta_neutral_abs':0.02,'concordant_ratio_factor':1.5,'calibration_ratio_factor':4.0},
      'replay_boundary_order':['H0_210MA','R3.9_PRE_CHA1','R3.11_POST_CHA1','R3.14_LATE_CENOZOIC','R3.27','R3.28','R3.34']})
    # Exactly 75 cells: target cell + 74 deliberately under-evidenced domains in same window.
    domains=['population_persistence']+[f'd{i}' for i in range(74)]
    wj(root/'configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json',{'window_domain_scope':{'H0_POST_CHA1_RECOVERY':domains}})
    jobs=[]
    for jid in AFFECTED:
        jobs.append({'job_id':jid,'window_id':'H0_POST_CHA1_RECOVERY','engine':'CDMetaPOP','earliest_replay_boundary':'R3.11_POST_CHA1'})
    jobs.append({'job_id':'R42_OTHER_NEMO','window_id':'H0_POST_CHA1_RECOVERY','engine':'NEMO','earliest_replay_boundary':'R3.11_POST_CHA1'})
    wj(root/'outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json',{'jobs':jobs})

    target={'kind':'ratio','value':0.93,'comparability':'NORMALIZABLE'}
    rows=[]
    # One selected absolute-population row in every frozen CDMetaPOP job; J09 is primary structural.
    for i,jid in enumerate(AFFECTED):
        role='PRIMARY' if jid==J09 else 'SECONDARY'
        ext=1.20 if jid==J09 else 1.10
        rows.append({'stage':'v0.6D1-R4.11','window_id':'H0_POST_CHA1_RECOVERY','job_id':jid,'engine':'CDMetaPOP','domain':'population_persistence','authority_role':role,'mapping_comparability':'NORMALIZABLE','parent_terminal_class':'SCIENTIFIC_RESULT','majority_vote':False,'canonical_write':False,'discordance_class':'STRUCTURAL_DISAGREEMENT' if jid==J09 else 'CALIBRATION_OFFSET','reason':'OLD','metric':{'name':METRIC,'summary':{'median':ext,'q10':ext-0.02,'q90':ext+0.02}},'target':target})
    # Unaffected primary evidence row for another domain is copied verbatim.
    rows.append({'stage':'v0.6D1-R4.11','window_id':'H0_POST_CHA1_RECOVERY','job_id':'R42_OTHER_NEMO','engine':'NEMO','domain':'d0','authority_role':'PRIMARY','mapping_comparability':'NORMALIZABLE','parent_terminal_class':'SCIENTIFIC_RESULT','majority_vote':False,'canonical_write':False,'discordance_class':'CALIBRATION_OFFSET','reason':'KEEP_ME','metric':{'name':'genetic_gap_response_ratio','summary':{'median':1.2}},'target':{'kind':'ratio','value':1.1,'comparability':'NORMALIZABLE'}})
    # Parent cells are historical only; new cells are recomputed from rows.
    cells=[]
    for d in domains:
        if d=='population_persistence':
            cells.append({'window_id':'H0_POST_CHA1_RECOVERY','domain':d,'discordance_class':'STRUCTURAL_DISAGREEMENT','reason':'OLD','primary_adjudicative_rows':1,'majority_vote':False})
        elif d=='d0':
            cells.append({'window_id':'H0_POST_CHA1_RECOVERY','domain':d,'discordance_class':'CALIBRATION_OFFSET','reason':'OLD','primary_adjudicative_rows':1,'majority_vote':False})
        else:
            cells.append({'window_id':'H0_POST_CHA1_RECOVERY','domain':d,'discordance_class':'INSUFFICIENT_EVIDENCE','reason':'OLD','primary_adjudicative_rows':0,'majority_vote':False})
    wj(root/'outputs/v0_6D1_R4_11/R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json',{'stage':'v0.6D1-R4.11','cell_count':75,'class_counts':{'CONCORDANT':0,'CALIBRATION_OFFSET':1,'STRUCTURAL_DISAGREEMENT':1,'SEMANTICALLY_NONCOMPARABLE':0,'INSUFFICIENT_EVIDENCE':73},'cells':cells,'evidence_rows':rows})
    return root


def test_downgrade_all_five_selected_cdmetapop_rows(tmp_path):
    r=fixture(tmp_path);out,_=readjudicate(r);assert out['status']==COMPLETE
    reg=json.load(open(r/'outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_OVERRIDE_REGISTRY.json'))
    assert reg['override_count']==5 and {x['job_id'] for x in reg['overrides']}==set(AFFECTED)


def test_proxy_rows_are_not_structural_after_reclassification(tmp_path):
    r=fixture(tmp_path);readjudicate(r);m=json.load(open(r/'outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json'))
    rows=[x for x in m['evidence_rows'] if x.get('engine')=='CDMetaPOP' and (x.get('metric') or {}).get('name')==METRIC]
    assert all(x['mapping_comparability']=='PROXY_ONLY' for x in rows)
    assert all(x['discordance_class']!='STRUCTURAL_DISAGREEMENT' for x in rows)


def test_j09_structural_cell_loses_proxy_only_primary_adjudication(tmp_path):
    r=fixture(tmp_path);readjudicate(r);m=json.load(open(r/'outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json'))
    c=[x for x in m['cells'] if x['domain']=='population_persistence'][0]
    assert c['discordance_class']=='INSUFFICIENT_EVIDENCE' and c['primary_adjudicative_rows']==0


def test_unaffected_nemo_row_is_preserved(tmp_path):
    r=fixture(tmp_path);before=json.load(open(r/'outputs/v0_6D1_R4_11/R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json'))['evidence_rows'][-1]
    readjudicate(r);after=json.load(open(r/'outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json'))['evidence_rows'][-1]
    assert before==after


def test_parent_matrix_bytes_not_modified(tmp_path):
    r=fixture(tmp_path);p=r/'outputs/v0_6D1_R4_11/R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json';b=p.read_bytes();readjudicate(r);assert p.read_bytes()==b


def test_exact_75_cells_and_frozen_classes(tmp_path):
    r=fixture(tmp_path);readjudicate(r);m=json.load(open(r/'outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json'))
    assert m['cell_count']==75 and sum(m['class_counts'].values())==75


def test_structural_count_drops_in_fixture(tmp_path):
    r=fixture(tmp_path);readjudicate(r);s=json.load(open(r/'outputs/v0_6D1_R4_13/R4_13_EXECUTION_SUMMARY.json'))
    assert s['structural_disagreement_count_after_comparability_downgrade']==0


def test_gap_route_selected_after_structural_removed(tmp_path):
    r=fixture(tmp_path);out,_=readjudicate(r);assert out['next_action']==NEXT_GAPS


def test_matched_control_is_not_promoted(tmp_path):
    r=fixture(tmp_path);readjudicate(r);reg=json.load(open(r/'outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_OVERRIDE_REGISTRY.json'));assert reg['matched_control_global_metric_promoted'] is False


def test_no_engine_or_canonical_change(tmp_path):
    r=fixture(tmp_path);readjudicate(r);s=json.load(open(r/'outputs/v0_6D1_R4_13/R4_13_EXECUTION_SUMMARY.json'));assert s['engine_execution_performed'] is False and s['canonical_state_changed'] is False and s['canonical_replay_authorized'] is False


def test_blocks_if_parent_finding_missing(tmp_path):
    r=fixture(tmp_path);wj(r/'outputs/v0_6D1_R4_12/R4_12_ABSOLUTE_RESPONSE_COMPARABILITY_DIAGNOSIS.json',{'finding':'OTHER','absolute_population_response_comparability':'PROXY_ONLY'});out,_=readjudicate(r);assert out['status']==BLOCKED


def test_blocks_if_parent_matrix_not_75(tmp_path):
    r=fixture(tmp_path);p=r/'outputs/v0_6D1_R4_11/R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json';d=json.load(open(p));d['cell_count']=74;wj(p,d);out,_=readjudicate(r);assert out['status']==BLOCKED


def test_final_seal_good_fixture(tmp_path):
    r=fixture(tmp_path);readjudicate(r);out,checks=final_seal(r);assert out['status']==SEALED and out['verdict']=='SEALED' and all(c.passed for c in checks)


def test_final_seal_blocks_without_readjudication(tmp_path):
    r=fixture(tmp_path);out,_=final_seal(r);assert out['status']==BLOCKED
