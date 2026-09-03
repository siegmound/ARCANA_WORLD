from pathlib import Path
import json, shutil
from arcana_worldsim.scientific_engines.r414_evidence_gap_closure import build, final_seal, _root_cause

SRC=Path(__file__).resolve().parents[1]

def w(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')

def prep(tmp:Path):
    for rel in [
        'configs/world1_r414_evidence_gap_closure_v0_6D1_R4_14.json',
        'configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json',
        'outputs/v0_6D1_R4_3/R4_3_PER_JOB_UNIT_MAPPING.json',
        'outputs/v0_6D1_R4_1/R4_1_SEMANTIC_AUTHORITY_MATRIX.json',
        'outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json',
    ]:
        d=tmp/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SRC/rel,d)
    w(tmp/'outputs/v0_6D1_R4_13_SEAL/R4_13_FINAL_SEAL_AUDIT.json',{'status':'PASS_R413_CDMETAPOP_ABSOLUTE_RESPONSE_COMPARABILITY_DOWNGRADE_AND_READJUDICATION_SEALED'})
    w(tmp/'outputs/v0_6D1_R4_13/R4_13_EXECUTION_SUMMARY.json',{'next_action':'BUILD_R414_MULTI_ENGINE_EVIDENCE_GAP_CLOSURE_AND_TARGETED_ADAPTER_ENHANCEMENT'})
    cfg=json.loads((SRC/'configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json').read_text())
    cells=[]
    for wid,domains in cfg['window_domain_scope'].items():
        for d in domains:
            cells.append({'window_id':wid,'domain':d,'discordance_class':'INSUFFICIENT_EVIDENCE','reason':'NO_PRIMARY_NORMALIZABLE_RESULT_TARGET_PAIR'})
    assert len(cells)==75
    for i in range(4): cells[i]['discordance_class']='CONCORDANT';cells[i]['reason']='TEST_RESOLVED'
    gaps=[c for c in cells if c['discordance_class']=='INSUFFICIENT_EVIDENCE']
    assert len(gaps)==71
    # Give the first gap a NEMO primary row with an adjudicative target but missing normalized metric.
    g=gaps[0]
    rows=[{'window_id':g['window_id'],'domain':g['domain'],'job_id':'R42_J10_H0_POST_CHA1_RECOVERY_NEMO','engine':'NEMO','authority_role':'PRIMARY','mapping_comparability':'NORMALIZABLE','discordance_class':'INSUFFICIENT_EVIDENCE','reason':'NO_R43_NORMALIZED_RESULT_METRIC_FOR_DOMAIN','metric':None,'target':{'comparability':'NORMALIZABLE','kind':'delta','value':0.1}}]
    # A Geonomics semantic-noncomparability cell.
    gg=gaps[1];gg['discordance_class']='SEMANTICALLY_NONCOMPARABLE'
    rows.append({'window_id':gg['window_id'],'domain':gg['domain'],'job_id':'R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS','engine':'Geonomics','authority_role':'PRIMARY','mapping_comparability':'NORMALIZABLE','discordance_class':'SEMANTICALLY_NONCOMPARABLE','reason':'R43_ENGINE_JOB_SEMANTIC_NONCOMPARABILITY','metric':None,'target':{'comparability':'NORMALIZABLE','kind':'delta','value':0.1}})
    # Preserve exact class accounting 70 insufficient + 1 semantic = 71 gaps.
    counts={'CONCORDANT':4,'CALIBRATION_OFFSET':0,'STRUCTURAL_DISAGREEMENT':0,'SEMANTICALLY_NONCOMPARABLE':1,'INSUFFICIENT_EVIDENCE':70}
    w(tmp/'outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json',{'cell_count':75,'class_counts':counts,'cells':cells,'evidence_rows':rows})
    # retained NEMO evidence signal
    rp=tmp/'outputs/v0_6D1_R4_3/jobs/R42_J10_H0_POST_CHA1_RECOVERY_NEMO/runtime_work/rep_000';rp.mkdir(parents=True,exist_ok=True)
    (rp/'r43_nemo_1.qfreq').write_text('x\n',encoding='utf-8');(rp/'R43.ini').write_text('x\n',encoding='utf-8')

def test_root_causes():
    assert _root_cause([])=='NO_PRIMARY_AUTHORITY_JOB_IN_FROZEN_WINDOW'
    r={'discordance_class':'INSUFFICIENT_EVIDENCE','target':{'comparability':'NORMALIZABLE'},'mapping_comparability':'NORMALIZABLE','reason':'NO_R43_NORMALIZED_RESULT_METRIC_FOR_DOMAIN'}
    assert _root_cause([r])=='PRIMARY_NORMALIZED_METRIC_MISSING'
    r2={'discordance_class':'SEMANTICALLY_NONCOMPARABLE','target':None,'mapping_comparability':'NORMALIZABLE'}
    assert _root_cause([r2])=='PRIMARY_ENGINE_SEMANTIC_NONCOMPARABILITY'

def test_build_and_seal(tmp_path):
    prep(tmp_path)
    out,checks=build(tmp_path)
    assert out['status']=='PASS_R414_MULTI_ENGINE_EVIDENCE_GAP_CENSUS_AND_TARGETED_ADAPTER_ENHANCEMENT_PLAN_COMPLETE'
    assert out['gap_count']==71
    assert out['retained_reextraction_candidate_cell_count']>=1
    assert out['next_action']=='BUILD_R415_RETAINED_RUNTIME_METRIC_RECOVERY_AND_TARGET_SEMANTIC_MATERIALIZATION'
    census=json.loads((tmp_path/'outputs/v0_6D1_R4_14/R4_14_EVIDENCE_GAP_CENSUS.json').read_text())
    assert census['root_cause_counts']['PRIMARY_NORMALIZED_METRIC_MISSING']>=1
    plan=json.loads((tmp_path/'outputs/v0_6D1_R4_14/R4_14_TARGETED_ADAPTER_ENHANCEMENT_PLAN.json').read_text())
    assert plan['r42_frozen_registry_modified'] is False
    assert plan['engine_execution_authorized_in_r414'] is False
    seal,_=final_seal(tmp_path)
    assert seal['verdict']=='SEALED'

def test_parent_structural_blocks(tmp_path):
    prep(tmp_path)
    p=tmp_path/'outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json'
    d=json.loads(p.read_text());d['class_counts']['STRUCTURAL_DISAGREEMENT']=1;w(p,d)
    out,_=build(tmp_path)
    assert out['status'].startswith('BLOCKED_')

def test_no_runtime_hit_defers_metric_missing_to_rerun(tmp_path):
    prep(tmp_path)
    shutil.rmtree(tmp_path/'outputs/v0_6D1_R4_3/jobs/R42_J10_H0_POST_CHA1_RECOVERY_NEMO/runtime_work')
    out,_=build(tmp_path)
    census=json.loads((tmp_path/'outputs/v0_6D1_R4_14/R4_14_EVIDENCE_GAP_CENSUS.json').read_text())
    x=next(g for g in census['gaps'] if g['root_cause']=='PRIMARY_NORMALIZED_METRIC_MISSING')
    assert x['closure_priority']=='P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION'

def test_root_cause_no_target():
    r={'discordance_class':'INSUFFICIENT_EVIDENCE','target':None,'mapping_comparability':'NORMALIZABLE'}
    assert _root_cause([r])=='NO_ARCANA_DECLARED_TARGET'

def test_root_cause_proxy_target():
    r={'discordance_class':'INSUFFICIENT_EVIDENCE','target':{'comparability':'PROXY_ONLY'},'mapping_comparability':'NORMALIZABLE'}
    assert _root_cause([r])=='ARCANA_TARGET_NONADJUDICATIVE_PROXY_OR_NONCOMPARABLE'

def test_root_cause_proxy_mapping():
    r={'discordance_class':'INSUFFICIENT_EVIDENCE','target':{'comparability':'NORMALIZABLE'},'mapping_comparability':'PROXY_ONLY'}
    assert _root_cause([r])=='PRIMARY_MAPPING_NONADJUDICATIVE_PROXY_ONLY'

def test_gap_outputs_are_noncanonical(tmp_path):
    prep(tmp_path);out,_=build(tmp_path)
    census=json.loads((tmp_path/'outputs/v0_6D1_R4_14/R4_14_EVIDENCE_GAP_CENSUS.json').read_text())
    assert all(g['canonical_change_authorized'] is False for g in census['gaps'])
    assert all(g['engine_rerun_authorized_in_r414'] is False for g in census['gaps'])

def test_plan_preserves_r42_freeze(tmp_path):
    prep(tmp_path);build(tmp_path)
    plan=json.loads((tmp_path/'outputs/v0_6D1_R4_14/R4_14_TARGETED_ADAPTER_ENHANCEMENT_PLAN.json').read_text())
    assert plan['r42_frozen_registry_modified'] is False
    assert plan['extension_jobs_deferred_new_namespace_only']

def test_capability_audit_detects_nemo_retained_files(tmp_path):
    prep(tmp_path);build(tmp_path)
    cap=json.loads((tmp_path/'outputs/v0_6D1_R4_14/R4_14_RETAINED_EVIDENCE_CAPABILITY_AUDIT.json').read_text())
    assert cap['engine_capability_audit']['NEMO']['retained_artifact_hit_count']>=2

def test_seal_requires_frozen_plan(tmp_path):
    prep(tmp_path);build(tmp_path)
    p=tmp_path/'outputs/v0_6D1_R4_14/R4_14_TARGETED_ADAPTER_ENHANCEMENT_PLAN.json';d=json.loads(p.read_text());d['status']='BROKEN';w(p,d)
    seal,_=final_seal(tmp_path)
    assert seal['verdict']=='BLOCKED'

def test_class_gap_accounting_fixed(tmp_path):
    prep(tmp_path);out,_=build(tmp_path)
    assert sum(out['root_cause_counts'].values())==71
    assert sum(out['closure_priority_counts'].values())==71
