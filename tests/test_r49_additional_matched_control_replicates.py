from pathlib import Path
import json, math
from arcana_worldsim.scientific_engines import r49_additional_matched_control_replicates as r49
ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/r49.CFG_REL).read_text(encoding='utf-8'))

def test_parent_is_exact_r48_uncertain_branch():
    assert CFG['required_parent_status']==r49.R48_SEALED
    assert CFG['required_parent_diagnosis_class']=='MATCHED_CONTROL_EFFECT_UNCERTAIN'
    assert CFG['required_parent_next_action']=='EXECUTE_R49_ADDITIONAL_MATCHED_CONTROL_REPLICATES'
def test_authorized_case_is_j09_cdmetapop():
    a=CFG['authorized_case'];assert a['job_id']=='R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP' and a['engine']=='CDMetaPOP' and a['domain']=='population_persistence'
def test_fixed_replication_plan_is_4_plus_16_equals_20():
    e=CFG['replicate_expansion'];assert e['parent_pair_count']==4 and e['additional_pair_count']==16 and e['final_pair_count']==20 and e['rerun_parent_pairs'] is False
def test_additional_seed_indices_exact_and_unique():
    r=CFG['replicate_expansion']['additional_replicates'];assert [x['replicate_index'] for x in r]==list(range(4,20));assert len({x['seed'] for x in r})==16
def test_additional_seeds_do_not_overlap_parent_known_seeds():
    parent={55525513,66696762,413622220,72612355};new={x['seed'] for x in CFG['replicate_expansion']['additional_replicates']};assert not(parent&new)
def test_no_adaptive_stopping_or_open_ended_escalation():
    p=CFG['diagnosis_policy'];assert p['no_adaptive_stopping'] is True and p['no_automatic_further_replicate_escalation_if_uncertain'] is True
def test_no_canonical_change_or_replay():
    assert CFG['canonical_state_changed'] is False and CFG['canonical_replay_authorized'] is False and CFG['canonical_parameter_change_authorized'] is False and CFG['deep_biological_coupling'] is False and CFG['majority_vote'] is False
def test_paired_effect_formula():
    dynamic=0.94;neutral=1.02;assert math.isclose(dynamic/neutral,0.9215686274509803)
def test_direction_reuses_five_percent_band_semantics():
    assert r49.direction_ratio(0.94,1.05)==-1 and r49.direction_ratio(1.0,1.05)==0 and r49.direction_ratio(1.06,1.05)==1
def test_diagnosis_classes_exact():
    assert r49.DIAG_CLASSES==['EXPANDED_MATCHED_CONTROL_SAME_DIRECTION_ROBUST','EXPANDED_MATCHED_CONTROL_OPPOSITE_DIRECTION_ROBUST','EXPANDED_MATCHED_CONTROL_EFFECT_UNCERTAIN']
def test_dynamic_adapter_reuses_r47_semantics_and_fixed_new_seeds():
    s=(ROOT/'benchmarks/r49/cdmetapop_r49_dynamic.py').read_text(encoding='utf-8');assert "len(specs)!=16" in s and "round(k0*0.5)" in s and "linear_knots(end_ratio" in s
def test_neutral_adapter_preserves_same_start_state_and_constant_k():
    s=(ROOT/'benchmarks/r49/cdmetapop_r49_neutral.py').read_text(encoding='utf-8');assert "len(specs)!=16" in s and "kvals=[k0 for _ in climate_knots]" in s and "round(k0*0.5)" in s
def test_runner_has_prepare_only():
    assert '[switch]$PrepareOnly' in (ROOT/'run_v0_6D1_R4_9.ps1').read_text(encoding='utf-8')
def test_capture_runs_both_dynamic_and_neutral_new_arms():
    s=(ROOT/'capture_v0_6D1_R4_9_additional_matched_control.ps1').read_text(encoding='utf-8');assert 'cdmetapop_r49_dynamic.py' in s and 'cdmetapop_r49_neutral.py' in s and 'R49 J09 dynamic x16' in s and 'R49 J09 neutral x16' in s
def test_uncertain_branch_does_not_auto_add_more_replicates():
    s=(ROOT/'src/arcana_worldsim/scientific_engines/r49_additional_matched_control_replicates.py').read_text(encoding='utf-8');assert 'BUILD_R410_MATCHED_CONTROL_PRECISION_AND_ALTERNATE_EVIDENCE_CLOSURE_PLAN' in s
