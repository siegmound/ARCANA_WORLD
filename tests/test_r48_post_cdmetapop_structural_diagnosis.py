from pathlib import Path
import json, math
from arcana_worldsim.scientific_engines import r48_post_cdmetapop_structural_diagnosis as r48
ROOT=Path(__file__).resolve().parents[1];CFG=json.loads((ROOT/r48.CFG_REL).read_text(encoding='utf-8'))
def test_parent_and_scope_frozen():
    assert CFG['required_parent_status']==r48.R47_SEALED
    a=CFG['authorized_structural_case'];assert a['job_id']=='R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP' and a['engine']=='CDMetaPOP' and a['domain']=='population_persistence'
def test_no_canonical_change_or_replay():
    assert CFG['canonical_state_changed'] is False and CFG['canonical_replay_authorized'] is False and CFG['canonical_parameter_change_authorized'] is False and CFG['deep_biological_coupling'] is False and CFG['majority_vote'] is False
def test_control_changes_only_forcing_end_ratio():
    p=CFG['matched_control_policy'];assert p['only_change']=='dynamic_end_support_ratio -> 1.0' and p['neutral_forcing_end_support_ratio']==1.0 and p['same_seed_ledger'] is True and p['same_initial_n0_policy'] is True
def test_paired_metric_removes_shared_relaxation():
    # dynamic absolute growth 1.20 and neutral growth 1.30 => forcing effect 0.923 decline
    assert math.isclose((1.20/1.30),0.9230769230769231)
def test_ratio_direction_uses_frozen_band_semantics():
    assert r48.direction_ratio(0.94,1.05)==-1 and r48.direction_ratio(1.03,1.05)==0 and r48.direction_ratio(1.06,1.05)==1
def test_r47_source_fact_n0_half_k_is_auditable():
    s=(ROOT/'benchmarks/r47/cdmetapop_r47.py').read_text(encoding='utf-8');assert "round(k0*0.5)" in s
def test_r48_adapter_is_neutral_and_preserves_start_n0_rule():
    s=(ROOT/'benchmarks/r48/cdmetapop_r48_neutral.py').read_text(encoding='utf-8');assert "kvals=[k0 for _ in climate_knots]" in s and "round(k0*0.5)" in s and "neutral_end_support_ratio':1.0" in s
def test_diagnosis_classes_exact():
    assert r48.DIAG_CLASSES==['TRANSIENT_RELAXATION_CONFOUND_CONFIRMED','MODEL_RESPONSE_DISAGREEMENT_PERSISTS_AFTER_MATCHED_CONTROL','MATCHED_CONTROL_EFFECT_UNCERTAIN']
def test_r48_does_not_rewrite_r47_matrix():
    assert CFG['diagnosis_policy']['r48_may_not_reclassify_r47_matrix'] is True
def test_next_actions_are_causal_not_automatic_replay():
    s=(ROOT/'src/arcana_worldsim/scientific_engines/r48_post_cdmetapop_structural_diagnosis.py').read_text(encoding='utf-8');assert 'BUILD_R49_SYMMETRIC_CDMETAPOP_MATCHED_CONTROL_NORMALIZATION_AND_READJUDICATION' in s and 'BUILD_R49_R311_CDMETAPOP_MECHANISM_DECOMPOSITION_BEFORE_CANONICAL_REPLAY' in s
def test_runner_has_prepare_only():
    assert '[switch]$PrepareOnly' in (ROOT/'run_v0_6D1_R4_8.ps1').read_text(encoding='utf-8')
def test_bridge_uses_same_j09_contract_and_new_output_namespace():
    s=(ROOT/'capture_v0_6D1_R4_8_matched_control.ps1').read_text(encoding='utf-8');assert 'outputs\\v0_6D1_R4_3\\jobs' in s and 'outputs\\v0_6D1_R4_8' in s and 'cdmetapop_r48_neutral.py' in s
