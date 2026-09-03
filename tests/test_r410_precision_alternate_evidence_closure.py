from pathlib import Path
import json
import pytest

from arcana_worldsim.scientific_engines.r410_precision_alternate_evidence_closure import (
    audit, final_seal, strict_individual_output_name, broad_selector_source_detected,
    copied_input_collision_names, COMPLETE, SEALED, BLOCKED, FINDING, NEXT,
)

def wj(p:Path,obj):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj),encoding='utf-8')

def wt(p:Path,text:str):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')

def fixture(tmp_path:Path):
    root=tmp_path
    cfg={
      'stage':'v0.6D1-R4.10','required_parent_next_action':'BUILD_R410_MATCHED_CONTROL_PRECISION_AND_ALTERNATE_EVIDENCE_CLOSURE_PLAN',
      'canonical_state_changed':False,'canonical_replay_authorized':False,'canonical_parameter_change_authorized':False,'deep_biological_coupling':False,'majority_vote':False,
      'authorized_case':{'window_id':'H0_POST_CHA1_RECOVERY','domain':'population_persistence','engine':'CDMetaPOP','job_id':'R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP','earliest_boundary':'R3.11_POST_CHA1'},
      'precision_policy':{'preserve_r49_diagnosis_without_posthoc_reclassification':True,'automatic_additional_replicates_forbidden':True},
      'cdmetapop_population_metric_integrity_policy':{'strict_individual_filename_regex':'^ind-?[0-9]+\\.csv$','historical_invalid_metrics_preserved_but_not_promoted':True},
      'r411_closure_policy':{'reextract_existing_runtime_outputs_before_any_rerun':True,'repair_applies_symmetrically_to_all_five_cdmetapop_jobs':True}
    }
    wj(root/'configs/world1_r410_matched_control_precision_alternate_evidence_v0_6D1_R4_10.json',cfg)
    wj(root/'outputs/v0_6D1_R4_9_SEAL/R4_9_FINAL_SEAL_AUDIT.json',{'status':'PASS_R49_ADDITIONAL_MATCHED_CONTROL_REPLICATES_AND_CAUSAL_DIRECTION_RESOLUTION_SEALED','next_action':cfg['required_parent_next_action']})
    wj(root/'outputs/v0_6D1_R4_9/R4_9_CAUSAL_DIRECTION_RESOLUTION.json',{'diagnosis_class':'EXPANDED_MATCHED_CONTROL_EFFECT_UNCERTAIN'})
    vals=[.90,.91,.92,.93,.94,.95,.96,.97,.92,.93,.94,.91,.89,.98,.93,.92,.94,.90,.99,1.00]
    paired=[{'replicate_index':i,'seed':100+i,'dynamic_initial':2.0,'neutral_initial':2.0,'paired_forcing_effect_ratio':v} for i,v in enumerate(vals)]
    wj(root/'outputs/v0_6D1_R4_9/R4_9_EXPANDED_PAIRED_CAUSAL_EFFECT.json',{'neutral_factor':1.05,'arcana_causal_forcing_effect_ratio':.935,'cdmetapop_expanded_paired_forcing_effect':{'n':20,'median':.935,'q10':.90,'q90':.98},'paired_replicates':paired})
    wj(root/'configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json',{'effect_policy':{'ratio_neutral_factor':1.05}})
    wj(root/'outputs/v0_6D1_R4_7/R4_7_CDMETAPOP_READJUDICATED_MATRIX.json',{'evidence_rows':[{'window_id':'H0_POST_CHA1_RECOVERY','domain':'population_persistence','engine':'CDMetaPOP','job_id':'R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP','authority_role':'PRIMARY','mapping_comparability':'NORMALIZABLE','discordance_class':'STRUCTURAL_DISAGREEMENT','reason':'x','target_direction':-1,'external_direction':1},{'window_id':'H0_POST_CHA1_RECOVERY','domain':'population_persistence','engine':'RangeShifter','job_id':'J08','authority_role':'PRIMARY','mapping_comparability':'NORMALIZABLE','discordance_class':'CALIBRATION_OFFSET','reason':'y','target_direction':-1,'external_direction':0}]})
    wj(root/'outputs/v0_6D1_R4_7/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/RAW_EVIDENCE.json',{'adapter_status':'PASS'})
    selector="indfiles=sorted([p for p in rw.rglob('*.csv') if 'ind' in p.name.lower()],key=generation_key)\n"
    for rel in ['benchmarks/r43/cdmetapop_r43.py','benchmarks/r47/cdmetapop_r47.py','benchmarks/r48/cdmetapop_r48_neutral.py','benchmarks/r49/cdmetapop_r49_dynamic.py','benchmarks/r49/cdmetapop_r49_neutral.py']:
        wt(root/rel,selector)
    wt(root/'.arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_PostProcess.py',"open('summary_popAllTime.csv','w')\nheader=['N_Initial']\n")
    wt(root/'.arcana_engines/CDMetaPOP-3.08/example_files/genes/yytype_hindex0.csv','a,b\n1,2\n3,4\n')
    wt(root/'.arcana_engines/CDMetaPOP-3.08/example_files/genes/wildtype_hindex1.csv','a,b\n1,2\n')
    return root

def test_strict_individual_name_accepts_outputs():
    assert strict_individual_output_name('ind-1.csv') and strict_individual_output_name('ind0.csv') and strict_individual_output_name('IND12.CSV')

def test_strict_individual_name_rejects_sample_and_hindex():
    assert not strict_individual_output_name('indSample4.csv') and not strict_individual_output_name('yytype_hindex0.csv')

def test_broad_selector_detected():
    assert broad_selector_source_detected("if 'ind' in p.name.lower()")

def test_collision_inventory_detects_hindex(tmp_path):
    r=fixture(tmp_path); names=copied_input_collision_names(r/'.arcana_engines/CDMetaPOP-3.08/example_files'); assert any('hindex0.csv' in x for x in names)

def test_good_fixture_audit_complete(tmp_path):
    r=fixture(tmp_path); out,checks=audit(r); assert out['status']==COMPLETE and out['checks_failed']==0 and out['finding']==FINDING

def test_precision_preserves_parent_uncertain(tmp_path):
    r=fixture(tmp_path); audit(r); d=json.load(open(r/'outputs/v0_6D1_R4_10/R4_10_MATCHED_CONTROL_PRECISION_AUDIT.json')); assert d['parent_diagnosis_preserved']=='EXPANDED_MATCHED_CONTROL_EFFECT_UNCERTAIN' and d['precision_reclassification_authorized'] is False

def test_precision_counts_20_pairs(tmp_path):
    r=fixture(tmp_path); audit(r); d=json.load(open(r/'outputs/v0_6D1_R4_10/R4_10_MATCHED_CONTROL_PRECISION_AUDIT.json')); assert d['n']==20 and sum(d['descriptive_pair_counts'].values())==20

def test_integrity_impact_blocks_old_metric_promotion(tmp_path):
    r=fixture(tmp_path); audit(r); d=json.load(open(r/'outputs/v0_6D1_R4_10/R4_10_CDMETAPOP_POPULATION_METRIC_INTEGRITY_AUDIT.json')); assert d['impact']['r43_r47_absolute_population_response_ratio'].startswith('NOT_ADMISSIBLE')

def test_plan_is_symmetric_and_no_replay(tmp_path):
    r=fixture(tmp_path); audit(r); d=json.load(open(r/'outputs/v0_6D1_R4_10/R4_10_ALTERNATE_EVIDENCE_CLOSURE_PLAN.json')); assert d['status']=='R411_PLAN_FROZEN' and d['canonical_replay_authorized'] is False and any('ALL_FIVE' in x for x in d['actions'])

def test_primary_context_no_vote(tmp_path):
    r=fixture(tmp_path); audit(r); d=json.load(open(r/'outputs/v0_6D1_R4_10/R4_10_PRIMARY_AUTHORITY_CONTEXT.json')); assert len(d['primary_rows'])==2 and d['majority_vote'] is False

def test_missing_collision_blocks(tmp_path):
    r=fixture(tmp_path); (r/'.arcana_engines/CDMetaPOP-3.08/example_files/genes/yytype_hindex0.csv').unlink(); (r/'.arcana_engines/CDMetaPOP-3.08/example_files/genes/wildtype_hindex1.csv').unlink(); out,_=audit(r); assert out['status']==BLOCKED

def test_fixed_selector_no_longer_confirms_bug(tmp_path):
    r=fixture(tmp_path); fixed="indfiles=[p for p in rw.rglob('ind*.csv') if strict_individual_output_name(p.name)]\n"; wt(r/'benchmarks/r43/cdmetapop_r43.py',fixed); wt(r/'benchmarks/r47/cdmetapop_r47.py',fixed); wt(r/'benchmarks/r48/cdmetapop_r48_neutral.py',fixed); wt(r/'benchmarks/r49/cdmetapop_r49_dynamic.py',fixed); wt(r/'benchmarks/r49/cdmetapop_r49_neutral.py',fixed); out,_=audit(r); assert out['status']==BLOCKED

def test_non_tiny_reported_initials_block_integrity_finding(tmp_path):
    r=fixture(tmp_path); p=r/'outputs/v0_6D1_R4_9/R4_9_EXPANDED_PAIRED_CAUSAL_EFFECT.json'; d=json.load(open(p)); [x.update(dynamic_initial=100.0,neutral_initial=100.0) for x in d['paired_replicates']]; wj(p,d); out,_=audit(r); assert out['status']==BLOCKED

def test_final_seal_good_fixture(tmp_path):
    r=fixture(tmp_path); audit(r); out,checks=final_seal(r); assert out['status']==SEALED and out['verdict']=='SEALED' and out['next_action']==NEXT and all(c.passed for c in checks)

def test_final_seal_blocks_without_audit(tmp_path):
    r=fixture(tmp_path); out,_=final_seal(r); assert out['status']==BLOCKED
