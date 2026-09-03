from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json
import numpy as np

STAGE='v0.6D1-R5.13'
OUT_REL=Path('outputs/v0_6D1_R5_13')
TARGET_COHORT=('RPT_010_D02','RPT_009_D02')
FINAL_STATUS='PASS_R513_R512_TO_R332_SUBSISTENCE_REGIONAL_READINESS_RECONCILIATION_CANDIDATE'
EXPECTED_MEMBERS=32
EXPECTED_TIME_STATES=145
EXPECTED_ANCHORS=9
EXPECTED_GROUP_AGENTS=48
EXPECTED_SUBSISTENCE_DOMAINS=(
 'high_return_capture_systems','broad_spectrum_foraging','plant_resource_processing_intensity','aquatic_resource_exploitation',
 'delayed_return_storage_buffering','landscape_resource_management','seasonal_scheduling_and_logistics','cooperative_provisioning_specialization')
EXPECTED_ECOLOGY=(
 'broad_spectrum_index','subsistence_intensification','delayed_return_economy_potential','managed_resource_intensity',
 'settlement_commitment','regional_differentiation','regional_continuity','food_production_transition_readiness',
 'subsistence_resilience','interlineage_subsistence_exchange')
EXPECTED_REGIONAL=(
 'represented_people','represented_camps','grid_row','grid_col','regional_lineage_code','subsistence_profile_mean',
 'subsistence_intensification','managed_resource_readiness','tech_access','regional_continuity')
EXPECTED_DYNAMICS={
 'broad_spectrum_operational_threshold':0.42,
 'intensification_rate_per_kyr':0.06,
 'loss_rate_per_kyr':0.028,
 'management_feedback_rate_per_kyr':0.034,
 'management_readiness_threshold':0.48,
 'regional_diffusion_rate_per_kyr':0.02,
 'transition_pocket_min_continuity':0.45,
 'transition_pocket_threshold':0.52,
}

# Exact distributed R5.12 source authority.
EXPECTED_R512_SOURCE_MANIFEST_SHA256='73118c1b6e15516fae296413cd5102a065ef820ee1e63dea0198fd2b09935529'
EXPECTED_R512_SOURCE_MODULE_SHA256='6e757c564ceec17ccb4c4d3d44562dd6e2f418f355ed23a305abf0c53d0f72d6'
EXPECTED_R512_CONFIG_SHA256='e0b785610b693e94cd805ba469ece187b3745960a9d15a4ef40de60b96d358d9'
EXPECTED_R512_CONTRACT_SHA256='870091f5ebc8dccd6d40c97d22e5099fbe7087a27bf6443096d66b4f03aa38ba'

# Immutable sealed R3.32 authority and artifacts.
EXPECTED_R332_FINAL_SEAL_AUDIT_SHA256='d37f45f9bb50ecb9f65ee861a233644f2696009f92103556445f2f9ed75defb3'
EXPECTED_R332_FINAL_SEAL_MANIFEST_SHA256='8f34da4fd8e99134173a229c1f0679611582b352fdcc20b23dd9c3e1b8a350c6'
EXPECTED_R332_OUTPUT_MANIFEST_SHA256='589dbb14867d53594f53e9b256b26a5d87410608b50e98abdd68ca8d9a1a3816'
EXPECTED_R332_REPLAY_SHA256='77c9296953b44a3cd1e1b90a7c07e89f6b6fe6b33010be1083cfcb2364b5639a'
EXPECTED_R332_REGIONAL_SHA256='dfad48a7cdb85580fe81b6aa69cd68ca87cff17e9da491252c044b9a76ce7fd1'
EXPECTED_R332_AUTHORITY_SHA256='36e38c6650692044da6f8c3043c2af226c862f114fe819a09025420709bbd316'
EXPECTED_R332_CHECKPOINT_SHA256='99a7f1027a780d204c9957212b5753fee8a5417feda1ad4b8b0419275eca083b'
EXPECTED_R332_OUTCOMES_SHA256='0dd6dc53600f14adc29e6fb9377218115e55d4fa575b7d424e2765f67995ee43'
EXPECTED_R332_SENSITIVITY_SHA256='6a7a5fcb6b092577477a898828cdf054725328d12cc5fc160d59b7de741bfb96'
EXPECTED_R332_AUDIT_SHA256='57a50e94fe9c39a43b1af6b2e29434bad4ec7b5f417894deac585551f3e4edb5'
EXPECTED_R332_SOURCE_MANIFEST_SHA256='4eecc5d2068c2eacf849c48fdaa38bef51bea4bd1225f18ea5583c96bc4da284'
EXPECTED_R332_SOURCE_MODULE_SHA256='6f7f94952c7971b40defed04a0ec4eba22860026cb16514c810ce74600c5dee6'
EXPECTED_R332_CONFIG_SHA256='231272b25de65c8748e86d4f7f251f202a4090b6088d82cdbc8e7baa062db868'
EXPECTED_R332_CONTRACT_SHA256='d53bc7920bd5c54ae94329f82f57339542190f60aafc2745cbdfd944159b8365'
EXPECTED_R333_CONTRACT_SHA256='8e18685646441c0e3e32d759c7c338e52df7ed9564a9133ecb533b12ae3c98cd'

# Exact R3.32 parent arrays used for deterministic revalidation.
EXPECTED_R331_REPLAY_SHA256='9f5ddb0fd1356ea681b72b52329e6804eb7ef47a269f923ba684486d5afaf941'
EXPECTED_R331_GROUP_SHA256='fde0f7d954d55a606481834c0cce6e4bf4ebb340db059e88e94cd851633af0cd'
EXPECTED_R330_GROUP_SHA256='ede3b7ad301ce3e6b51cd3c8f4e70ff2392a43e50695b676b56912191d51cd57'

R512_OUT=Path('outputs/v0_6D1_R5_12')
R512_MANIFEST=R512_OUT/'R5_12_OUTPUT_MANIFEST.json'
R512_AUDIT=R512_OUT/'R5_12_INTEGRATED_RECONCILIATION.json'
R512_HANDOFF=R512_OUT/'R5_12_0KA_ABSTRACT_TECHNOLOGICAL_ECOLOGY_RECONCILED_HANDOFF.json'
R512_BINDING=R512_OUT/'R5_12_PARENT_AUTHORITY_BINDING.json'
R512_SOURCE_MANIFEST=Path('SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_12.json')
R512_SOURCE_MODULE=Path('src/arcana_worldsim/state_query/r512_r331_abstract_technological_ecology_reconciliation.py')
R512_CONFIG=Path('configs/world1_r512_r331_abstract_technological_ecology_reconciliation_v0_6D1_R5_12.json')
R512_CONTRACT=Path('R5_12_R511_R331_ABSTRACT_CULTURAL_TECHNOLOGICAL_ECOLOGY_RECONCILIATION_CONTRACT.md')

R330_GROUP=Path('outputs/v0_6D1_R3_30/R3_30_WEIGHTED_GROUP_ABM.npz')
R331_OUT=Path('outputs/v0_6D1_R3_31')
R331_REPLAY=R331_OUT/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz'
R331_GROUP=R331_OUT/'R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz'
R332_OUT=Path('outputs/v0_6D1_R3_32')
R332_SEAL_OUT=Path('outputs/v0_6D1_R3_32_SEAL')
R332_REPLAY=R332_OUT/'R3_32_SUBSISTENCE_AND_TRANSITION_REPLAY.npz'
R332_REGIONAL=R332_OUT/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz'
R332_AUTHORITY=R332_OUT/'R3_32_SUBSISTENCE_REGIONAL_TRANSITION_AUTHORITY.json'
R332_CHECKPOINT=R332_OUT/'R3_32_SUBSISTENCE_REGIONAL_TRANSITION_CHECKPOINT.json'
R332_OUTCOMES=R332_OUT/'R3_32_LINEAGE_SUBSISTENCE_OUTCOMES.json'
R332_SENSITIVITY=R332_OUT/'R3_32_SENSITIVITY_AND_ROBUSTNESS.json'
R332_AUDIT=R332_OUT/'R3_32_INTEGRATED_AUDIT.json'
R332_OUTPUT_MANIFEST=R332_OUT/'R3_32_OUTPUT_MANIFEST.json'
R332_SEAL_AUDIT=R332_SEAL_OUT/'R3_32_FINAL_SEAL_AUDIT.json'
R332_SEAL_MANIFEST=R332_SEAL_OUT/'R3_32_FINAL_SEAL_MANIFEST.json'
R332_SOURCE_MANIFEST=Path('SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_32.json')
R332_SOURCE_MODULE=Path('src/arcana_worldsim/scientific_engines/r332_subsistence_regional_transitions.py')
R332_CONFIG=Path('configs/world1_r332_subsistence_regional_transitions_v0_6D1_R3_32.json')
R332_CONTRACT=Path('R3_32_SUBSISTENCE_REGIONAL_TRANSITIONS_CONTRACT.md')
R333_CONTRACT=Path('R3_33_HOLOCENE_ENVIRONMENT_DOMESTICATION_CONTRACT.md')
R513_CONFIG=Path('configs/world1_r513_r332_subsistence_regional_readiness_reconciliation_v0_6D1_R5_13.json')


def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def load_json(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def _manifest_integrity(base:Path,manifest:Path)->tuple[bool,list[str]]:
 try:m=load_json(manifest)
 except Exception:return False,['manifest_unreadable']
 bad=[]
 for n,x in (m.get('files') or {}).items():
  p=base/n
  if not p.is_file() or p.stat().st_size!=int(x.get('bytes',-1)) or sha256_file(p)!=x.get('sha256'):bad.append(n)
 return not bad,bad

def validate_parent_authority(root:Path)->dict[str,Any]:
 root=Path(root).resolve();checks={}
 required=[
  R512_MANIFEST,R512_AUDIT,R512_HANDOFF,R512_BINDING,R512_SOURCE_MANIFEST,R512_SOURCE_MODULE,R512_CONFIG,R512_CONTRACT,
  R330_GROUP,R331_REPLAY,R331_GROUP,R332_REPLAY,R332_REGIONAL,R332_AUTHORITY,R332_CHECKPOINT,R332_OUTCOMES,R332_SENSITIVITY,
  R332_AUDIT,R332_OUTPUT_MANIFEST,R332_SEAL_AUDIT,R332_SEAL_MANIFEST,R332_SOURCE_MANIFEST,R332_SOURCE_MODULE,R332_CONFIG,R332_CONTRACT,R333_CONTRACT]
 for rel in required:checks[f'present::{rel.as_posix()}']=(root/rel).is_file()
 try:
  ok,_=_manifest_integrity(root/R512_OUT,root/R512_MANIFEST);a=load_json(root/R512_AUDIT);h=load_json(root/R512_HANDOFF)
  checks['r512_output_manifest_integrity']=ok
  checks['r512_candidate_semantics']=(a.get('status')=='PASS_R512_R511_TO_R331_ABSTRACT_CULTURAL_TECHNOLOGICAL_ECOLOGY_RECONCILIATION_CANDIDATE' and a.get('scientific_candidate_eligible') is True and int(a.get('checks_passed',-1))==43 and int(a.get('checks_total',-1))==43 and not(a.get('failed') or []))
  checks['r512_handoff_exact']=(h.get('status')=='R512_RECONCILED_ABSTRACT_TECHNOLOGICAL_ECOLOGY_HANDOFF_0KA' and float(h.get('age_ka',-1))==0.0 and tuple(h.get('candidate_cohort') or [])==TARGET_COHORT and int(h.get('candidate_count',-1))==2 and h.get('unique_human_identity') is None and h.get('unique_human_identity_materialized') is False and h.get('abstract_technological_ecology_layer_available') is True and h.get('specific_artifact_inventory_materialized') is False and h.get('agriculture_materialized') is False and h.get('ready_for_r332_reconciliation') is True and h.get('downstream_r332_auto_authorized') is False)
  checks['r512_source_manifest_exact_hash']=sha256_file(root/R512_SOURCE_MANIFEST)==EXPECTED_R512_SOURCE_MANIFEST_SHA256
  checks['r512_source_module_exact_hash']=sha256_file(root/R512_SOURCE_MODULE)==EXPECTED_R512_SOURCE_MODULE_SHA256
  checks['r512_config_exact_hash']=sha256_file(root/R512_CONFIG)==EXPECTED_R512_CONFIG_SHA256
  checks['r512_contract_exact_hash']=sha256_file(root/R512_CONTRACT)==EXPECTED_R512_CONTRACT_SHA256
 except Exception:
  for k in ['r512_output_manifest_integrity','r512_candidate_semantics','r512_handoff_exact','r512_source_manifest_exact_hash','r512_source_module_exact_hash','r512_config_exact_hash','r512_contract_exact_hash']:checks[k]=False
 try:
  seal=load_json(root/R332_SEAL_AUDIT);sm=load_json(root/R332_SEAL_MANIFEST);ia=load_json(root/R332_AUDIT)
  checks['r332_final_seal_audit_exact_hash']=sha256_file(root/R332_SEAL_AUDIT)==EXPECTED_R332_FINAL_SEAL_AUDIT_SHA256
  checks['r332_final_seal_manifest_exact_hash']=sha256_file(root/R332_SEAL_MANIFEST)==EXPECTED_R332_FINAL_SEAL_MANIFEST_SHA256
  checks['r332_final_seal_manifest_binds_audit']=(((sm.get('files') or {}).get('R3_32_FINAL_SEAL_AUDIT.json') or {}).get('sha256')==EXPECTED_R332_FINAL_SEAL_AUDIT_SHA256)
  checks['r332_final_seal_semantics']=(seal.get('verdict')=='SEALED' and seal.get('status')=='PASS_R332_SUBSISTENCE_INTENSIFICATION_REGIONAL_CULTURAL_LINEAGES_MANAGED_RESOURCE_TRANSITIONS_AND_HOLOCENE_READINESS_SEALED' and int(seal.get('checks_passed',-1))==30 and int(seal.get('checks_failed',-1))==0)
  checks['r332_integrated_audit_semantics']=(ia.get('status')=='PASS_R332_SUBSISTENCE_INTENSIFICATION_REGIONAL_CULTURAL_LINEAGES_AND_HOLOCENE_TRANSITIONS_CANDIDATE' and int(ia.get('checks_passed',-1))==25 and int(ia.get('checks_total',-1))==25 and int(ia.get('checks_failed',-1))==0)
  checks['r332_output_manifest_exact_hash']=sha256_file(root/R332_OUTPUT_MANIFEST)==EXPECTED_R332_OUTPUT_MANIFEST_SHA256
  ok,_=_manifest_integrity(root/R332_OUT,root/R332_OUTPUT_MANIFEST);checks['r332_output_manifest_integrity']=ok
  exact={
   R332_REPLAY:EXPECTED_R332_REPLAY_SHA256,R332_REGIONAL:EXPECTED_R332_REGIONAL_SHA256,R332_AUTHORITY:EXPECTED_R332_AUTHORITY_SHA256,
   R332_CHECKPOINT:EXPECTED_R332_CHECKPOINT_SHA256,R332_OUTCOMES:EXPECTED_R332_OUTCOMES_SHA256,R332_SENSITIVITY:EXPECTED_R332_SENSITIVITY_SHA256,R332_AUDIT:EXPECTED_R332_AUDIT_SHA256,
   R331_REPLAY:EXPECTED_R331_REPLAY_SHA256,R331_GROUP:EXPECTED_R331_GROUP_SHA256,R330_GROUP:EXPECTED_R330_GROUP_SHA256}
  checks['r332_and_parent_artifact_hashes_exact']=all(sha256_file(root/p)==x for p,x in exact.items())
  checks['r332_source_manifest_exact_hash']=sha256_file(root/R332_SOURCE_MANIFEST)==EXPECTED_R332_SOURCE_MANIFEST_SHA256
  checks['r332_source_module_exact_hash']=sha256_file(root/R332_SOURCE_MODULE)==EXPECTED_R332_SOURCE_MODULE_SHA256
  checks['r332_config_exact_hash']=sha256_file(root/R332_CONFIG)==EXPECTED_R332_CONFIG_SHA256
  checks['r332_contract_exact_hash']=sha256_file(root/R332_CONTRACT)==EXPECTED_R332_CONTRACT_SHA256
  checks['r333_contract_exact_hash']=sha256_file(root/R333_CONTRACT)==EXPECTED_R333_CONTRACT_SHA256
 except Exception:
  for k in ['r332_final_seal_audit_exact_hash','r332_final_seal_manifest_exact_hash','r332_final_seal_manifest_binds_audit','r332_final_seal_semantics','r332_integrated_audit_semantics','r332_output_manifest_exact_hash','r332_output_manifest_integrity','r332_and_parent_artifact_hashes_exact','r332_source_manifest_exact_hash','r332_source_module_exact_hash','r332_config_exact_hash','r332_contract_exact_hash','r333_contract_exact_hash']:checks[k]=False
 checks={k:bool(v) for k,v in checks.items()};failed=[k for k,v in checks.items() if not v]
 return {'stage':STAGE,'status':'PASS_R513_IMMUTABLE_R512_R332_PARENT_AUTHORITY' if not failed else 'BLOCKED_R513_PARENT_AUTHORITY','pass':not failed,'checks_passed':len(checks)-len(failed),'checks_total':len(checks),'failed':failed,'checks':checks}


def reconcile(root:Path)->dict[str,Any]:
 root=Path(root).resolve();out=root/OUT_REL;cfg=load_json(root/R513_CONFIG);parent=validate_parent_authority(root);checks={'parent_authority_pass':parent['pass']}
 try:
  from arcana_worldsim.scientific_engines import r332_subsistence_regional_transitions as r332
  h512=load_json(root/R512_HANDOFF);cfg332=load_json(root/R332_CONFIG);auth=load_json(root/R332_AUTHORITY);cp=load_json(root/R332_CHECKPOINT);outcomes=load_json(root/R332_OUTCOMES);sens=load_json(root/R332_SENSITIVITY)
  z31=np.load(root/R331_REPLAY,allow_pickle=False);g31=np.load(root/R331_GROUP,allow_pickle=False);g30=np.load(root/R330_GROUP,allow_pickle=False)
  z32=np.load(root/R332_REPLAY,allow_pickle=False);rg32=np.load(root/R332_REGIONAL,allow_pickle=False)
  sel=np.where(np.asarray(z31['age_ka'],float)<=20.0+1e-12)[0];asel=np.where(np.asarray(g31['anchor_age_ka'],float)<=20.0+1e-12)[0]
  inp={'z31':z31,'g31':g31,'g30':g30,'sel':sel,'anchor_sel':asel}
  rereplay=r332.replay_subsistence(inp,cfg332);reregional=r332.build_regional_anchors(inp,rereplay)
  ids=tuple(map(str,z32['candidate_ids']));members=np.asarray(z32['parent_member_indices']);age=np.asarray(z32['age_ka']);sn=tuple(map(str,z32['subsistence_domain_names']));stock=np.asarray(z32['subsistence_domain_stock']);en=tuple(map(str,z32['ecology_variable_names']));eco=np.asarray(z32['subsistence_transition_ecology']);pockets=np.asarray(z32['transition_pocket'])
  rids=tuple(map(str,rg32['candidate_ids']));rmem=np.asarray(rg32['parent_member_indices']);rage=np.asarray(rg32['anchor_age_ka']);rn=tuple(map(str,rg32['regional_variable_names']));rstate=np.asarray(rg32['regional_state']);ractive=np.asarray(rg32['regional_active'])
  stock_err=float(np.max(np.abs(rereplay['stock']-stock)));eco_err=float(np.max(np.abs(rereplay['eco']-eco)));pocket_err=int(np.max(np.abs(rereplay['pockets'].astype(int)-pockets.astype(int))));regional_err=float(np.max(np.abs(reregional['state']-rstate)))
  favorable=[v for v in sens.get('variants') or [] if any(float(x)>0 for x in (v.get('transition_pocket_frequency') or []))]
  checks.update({
   'config_target_cohort_exact':tuple(cfg.get('target_cohort') or [])==TARGET_COHORT,
   'r512_handoff_two_lineage_exact':tuple(h512.get('candidate_cohort') or [])==TARGET_COHORT and h512.get('unique_human_identity_materialized') is False and h512.get('abstract_technological_ecology_layer_available') is True,
   'r332_candidate_order_exact':ids==TARGET_COHORT and rids==TARGET_COHORT,
   'r332_parent_member_indices_exact':np.array_equal(members,np.asarray(z31['parent_member_indices'])) and np.array_equal(rmem,members) and len(members)==EXPECTED_MEMBERS,
   'r332_age_axis_exact_r331_subset_20ka_to_0':np.array_equal(age,np.asarray(z31['age_ka'])[sel]) and len(age)==EXPECTED_TIME_STATES and float(age[0])==20.0 and float(age[-1])==0.0,
   'r332_subsistence_domain_names_exact':sn==EXPECTED_SUBSISTENCE_DOMAINS and tuple(cfg332.get('subsistence_domains') or [])==EXPECTED_SUBSISTENCE_DOMAINS,
   'r332_stock_geometry_exact':stock.shape==(32,2,145,8),
   'r332_ecology_names_exact':en==EXPECTED_ECOLOGY,
   'r332_ecology_geometry_exact':eco.shape==(32,2,145,10),
   'r332_transition_pocket_geometry_binary':pockets.shape==(32,2,145) and set(np.unique(pockets)).issubset({0,1}),
   'r332_regional_anchor_axis_exact_r331_subset':np.array_equal(rage,np.asarray(g31['anchor_age_ka'])[asel]) and len(rage)==EXPECTED_ANCHORS,
   'r332_regional_variable_names_exact':rn==EXPECTED_REGIONAL,
   'r332_regional_geometry_exact':rstate.shape==(32,2,9,48,10) and ractive.shape==(32,2,9,48),
   'r332_regional_active_exact_parent_subset':np.array_equal(ractive,np.asarray(g31['group_active'])[:,:,asel,:]),
   'r332_deterministic_stock_replay_exact':stock_err==0.0 and np.array_equal(rereplay['stock'],stock),
   'r332_deterministic_ecology_replay_exact':eco_err==0.0 and np.array_equal(rereplay['eco'],eco),
   'r332_deterministic_transition_pockets_exact':pocket_err==0 and np.array_equal(rereplay['pockets'],pockets),
   'r332_deterministic_regional_anchor_replay_exact':regional_err==0.0 and np.array_equal(reregional['state'],rstate) and np.array_equal(reregional['active'],ractive),
   'r332_all_numeric_finite':np.isfinite(stock).all() and np.isfinite(eco).all() and np.isfinite(rstate).all(),
   'r332_stock_and_ecology_bounded':float(np.min(stock))>=0.0 and float(np.max(stock))<=1.0 and float(np.min(eco))>=0.0 and float(np.max(eco))<=1.0,
   'r332_regional_codes_opaque_integer_bounded':np.all(np.isclose(rstate[...,4],np.round(rstate[...,4]))) and float(np.min(rstate[...,4]))>=0.0 and float(np.max(rstate[...,4]))<=6.0,
   'r332_frozen_dynamics_exact':auth.get('dynamics')==EXPECTED_DYNAMICS,
   'r332_frozen_dynamics_not_historical_truth':cfg.get('r332_rates_and_thresholds_historical_truth') is False,
   'r332_transition_semantics_readiness_only':auth.get('transition_semantics')=='MANAGED_RESOURCE_AND_FOOD_PRODUCTION_READINESS_NOT_AGRICULTURE_OR_DOMESTICATION' and cfg.get('r332_transition_pocket_realized_food_production') is False and cfg.get('r332_transition_pocket_agriculture') is False,
   'r332_regional_lineage_semantics_opaque_not_identity':auth.get('regional_cultural_lineage_semantics')=='OPAQUE_DEME_TRACKED_REGIONAL_CULTURAL_CONTINUITY_NOT_NAMED_CULTURE_ETHNICITY_OR_LANGUAGE' and cfg.get('r332_regional_lineage_codes_named_cultures_or_ethnicities') is False,
   'r332_interlineage_exchange_not_realized_history':cfg.get('r332_interlineage_exchange_realized_history') is False and 'interlineage_subsistence_exchange' in en,
   'r332_sensitivity_25_no_selection_gate':int(sens.get('variant_count',-1))==25 and len(sens.get('variants') or [])==25 and sens.get('selection_gate') is False,
   'r332_both_lineages_retained_under_sensitivity':tuple(sens.get('candidate_retention') or [])==TARGET_COHORT,
   'r332_favorable_sensitivity_variant_not_identity_gate':len(favorable)==1 and favorable[0].get('rate_multiplier')==1.2 and favorable[0].get('threshold_offset')==-0.06 and favorable[0].get('transition_pocket_frequency')==[0.03125,0.0] and sens.get('selection_gate') is False,
   'r332_outcomes_remain_transition_potential':tuple(outcomes.get('candidate_lineages') or [])==TARGET_COHORT and all(x.get('interpretation')=='SUBSISTENCE_AND_MANAGEMENT_TRANSITION_POTENTIAL_NOT_AGRICULTURE_OR_DOMESTICATION' for x in outcomes.get('lineages') or []),
   'r332_checkpoint_two_lineages_no_unique_identity':tuple(cp.get('candidate_cohort') or [])==TARGET_COHORT and int(cp.get('candidate_count',-1))==2 and cp.get('unique_human_identity') is None and cp.get('unique_human_identity_materialized') is False,
   'r332_checkpoint_pockets_and_regional_codes_not_literal_history':cp.get('managed_resource_transition_pockets_materialized') is True and cp.get('regional_lineages_materialized') is True and cp.get('regional_lineages_named_cultures') is False,
   'r332_no_agriculture_or_domesticated_species':auth.get('agriculture_materialized') is False and auth.get('domesticated_species_materialized') is False and cp.get('agriculture_materialized') is False and cp.get('domesticated_species_materialized') is False,
   'r332_no_named_culture_language_religion_city_state_ethnicity':all(auth.get(k) is False for k in ('named_culture_materialized','language_materialized','religion_materialized','city_state_materialized','ethnicity_materialized')),
   'r332_no_unique_human_identity':auth.get('unique_human_identity_materialized') is False,
   'r332_evidence_basis_inherited_not_revalidated_here':cfg.get('r332_evidence_basis_revalidated_in_r513') is False and len(auth.get('evidence_basis') or {})==9,
   'no_new_external_engine_execution':cfg.get('external_engine_execution') is False,
   'r332_not_scientifically_rerun_or_mutated':cfg.get('rerun_r332_scientific_stage') is False and cfg.get('deterministic_formula_revalidation') is True and sha256_file(root/R332_REPLAY)==EXPECTED_R332_REPLAY_SHA256 and sha256_file(root/R332_REGIONAL)==EXPECTED_R332_REGIONAL_SHA256,
   'numeric_historical_truth_not_claimed':cfg.get('numeric_historical_truth_claimed') is False,
   'canonical_state_unchanged':cfg.get('canonical_state_changed') is False,
   'derived_refinement_not_promoted':cfg.get('derived_refinement_promoted_to_canon') is False,
   'deep_biological_coupling_off':cfg.get('deep_biological_coupling') is False and auth.get('deep_biological_coupling') is False,
   'downstream_r333_not_auto_authorized':cfg.get('auto_authorize_downstream_r333') is False,
  })
 except Exception:
  checks['reconciliation_exception_free']=False
 checks={k:bool(v) for k,v in checks.items()};failed=[k for k,v in checks.items() if not v]
 out.mkdir(parents=True,exist_ok=True)
 utility={'stage':STAGE,'status':'PASS_R513_RUNTIME_UTILITY_REVIEW_NO_NEW_ENGINE_REQUIRED','new_external_engine_execution_performed':False,'decision':'NO_NEW_ENGINE_OR_R332_SCIENTIFIC_RERUN_REQUIRED','reason':'R3.32 is already SEALED and is a deterministic ARCANA-native transformation of immutable R3.31/R3.30 arrays; R5.13 can exactly revalidate it in memory.','considered':{'SLiM_5_2':'NOT_RERUN_NO_NEW_ANCESTRY_QUESTION','NEMO_2_4_2':'NOT_RERUN_NO_NEW_GENE_FLOW_QUESTION','CDMetaPOP_3_08':'NOT_RERUN_NO_NEW_DEMOGRAPHIC_PERSISTENCE_QUESTION','RangeShiftR_3_0_1':'NOT_RERUN_NO_NEW_CORRIDOR_QUESTION','new_subsistence_ABM_runtime':'NOT_REQUIRED_R332_IS_DETERMINISTIC_ARCANA_NATIVE_READINESS_ECOLOGY'}}
 write_json(out/'R5_13_RUNTIME_UTILITY_REVIEW.json',utility)
 binding={'stage':STAGE,'status':'R513_PARENT_AUTHORITY_BINDING','r512_output_manifest_sha256':sha256_file(root/R512_MANIFEST) if (root/R512_MANIFEST).is_file() else None,'r512_handoff_sha256':sha256_file(root/R512_HANDOFF) if (root/R512_HANDOFF).is_file() else None,'r332_final_seal_audit_sha256':sha256_file(root/R332_SEAL_AUDIT) if (root/R332_SEAL_AUDIT).is_file() else None,'r332_output_manifest_sha256':sha256_file(root/R332_OUTPUT_MANIFEST) if (root/R332_OUTPUT_MANIFEST).is_file() else None,'r332_replay_sha256':sha256_file(root/R332_REPLAY) if (root/R332_REPLAY).is_file() else None,'r332_regional_anchor_sha256':sha256_file(root/R332_REGIONAL) if (root/R332_REGIONAL).is_file() else None,'r331_replay_sha256':sha256_file(root/R331_REPLAY) if (root/R331_REPLAY).is_file() else None,'r331_group_sha256':sha256_file(root/R331_GROUP) if (root/R331_GROUP).is_file() else None,'r330_group_sha256':sha256_file(root/R330_GROUP) if (root/R330_GROUP).is_file() else None,'binding_semantics':'R512_RECONCILED_0KA_ABSTRACT_TECHNOLOGICAL_ECOLOGY_HANDOFF_PLUS_IMMUTABLE_SEALED_R332_AND_EXACT_R331_R330_PARENTS'}
 write_json(out/'R5_13_PARENT_AUTHORITY_BINDING.json',binding)
 alignment={'stage':STAGE,'status':'PASS_R513_R332_EXACT_DETERMINISTIC_REPLAY_ALIGNMENT' if not failed else 'BLOCKED_R513_R332_REPLAY_ALIGNMENT','candidate_cohort':list(TARGET_COHORT),'ensemble_members':32,'time_states':145,'subsistence_domains':8,'ecology_fields':10,'regional_anchor_states':9,'group_agents_per_lineage_member':48,'stock_max_abs_error':locals().get('stock_err',None),'ecology_max_abs_error':locals().get('eco_err',None),'transition_pocket_max_abs_error':locals().get('pocket_err',None),'regional_anchor_max_abs_error':locals().get('regional_err',None),'semantics':'EXACT_IN_MEMORY_REVALIDATION_OF_FROZEN_R332_FORMULAS_WITHOUT_REWRITING_OR_SCIENTIFICALLY_RERUNNING_R332'}
 write_json(out/'R5_13_R332_DETERMINISTIC_REPLAY_ALIGNMENT.json',alignment)
 classification={'stage':STAGE,'status':'R513_R332_SUBSISTENCE_REGIONAL_READINESS_CLASSIFICATION','subsistence_domains':list(EXPECTED_SUBSISTENCE_DOMAINS),'subsistence_classification':'ABSTRACT_FUNCTIONAL_SUBSISTENCE_AND_MANAGEMENT_STOCKS_NOT_LITERAL_ARCHAEOLOGICAL_SUBSISTENCE_INVENTORIES','frozen_dynamics':auth.get('dynamics') if 'auth' in locals() else None,'dynamics_classification':'SEALED_LEGACY_DIAGNOSTIC_MODEL_HYPERPARAMETERS_NOT_MEASURED_HISTORICAL_RATES_DATES_OR_CANONICAL_NUMERIC_TRUTH','transition_pocket_semantics':'READINESS_DIAGNOSTIC_ONLY_NOT_REALIZED_FOOD_PRODUCTION_CULTIVATION_DOMESTICATION_OR_AGRICULTURE','regional_lineage_semantics':'OPAQUE_DEME_TRACKED_CONTINUITY_CODES_NOT_NAMED_CULTURES_ETHNICITIES_LANGUAGES_PEOPLES_OR_ARCHAEOLOGICAL_TRADITIONS','interlineage_exchange_semantics':'MODEL_OPPORTUNITY_FIELD_NOT_REALIZED_HISTORICAL_CULTURAL_TRANSFER_GENE_FLOW_OR_ANCESTRY','sensitivity_semantics':'ROBUSTNESS_DIAGNOSTIC_ONLY_NO_SELECTION_GATE; FAVORABLE_VARIANT_DOES_NOT_SELECT_A_LINEAGE_OR_TRANSITION_HISTORY','evidence_basis_status':'INHERITED_FROM_SEALED_R332_NOT_REVALIDATED_BY_R513'}
 write_json(out/'R5_13_R332_SUBSISTENCE_READINESS_CLASSIFICATION.json',classification)
 handoff={'stage':STAGE,'status':'R513_RECONCILED_SUBSISTENCE_REGIONAL_READINESS_HANDOFF_0KA','age_ka':0.0,'candidate_cohort':list(TARGET_COHORT),'candidate_count':2,'unique_human_identity':None,'unique_human_identity_materialized':False,'abstract_subsistence_readiness_layer_available':True,'subsistence_domain_count':8,'subsistence_domains':list(EXPECTED_SUBSISTENCE_DOMAINS),'regional_continuity_codes_available':True,'regional_continuity_codes_named_cultures':False,'managed_resource_transition_pockets_available':True,'transition_pockets_realized_food_production':False,'agriculture_materialized':False,'cultivation_materialized_as_realized_history':False,'domesticated_species_materialized':False,'named_culture_materialized':False,'ethnicity_materialized':False,'language_materialized':False,'religion_materialized':False,'city_state_materialized':False,'literal_historical_cultural_transfer_materialized':False,'source_r512_handoff_sha256':sha256_file(root/R512_HANDOFF) if (root/R512_HANDOFF).is_file() else None,'source_r332_final_seal_audit_sha256':sha256_file(root/R332_SEAL_AUDIT) if (root/R332_SEAL_AUDIT).is_file() else None,'source_r332_replay_sha256':sha256_file(root/R332_REPLAY) if (root/R332_REPLAY).is_file() else None,'ready_for_r333_reconciliation':not failed,'downstream_r333_auto_authorized':False}
 write_json(out/'R5_13_0KA_SUBSISTENCE_REGIONAL_READINESS_RECONCILED_HANDOFF.json',handoff)
 audit={'stage':STAGE,'status':FINAL_STATUS if not failed else 'BLOCKED_R513_R512_TO_R332_RECONCILIATION','scientific_candidate_eligible':not failed,'checks_passed':len(checks)-len(failed),'checks_total':len(checks),'failed':failed,'checks':checks,'summary':{'target_cohort':list(TARGET_COHORT),'r332_time_states':145,'r332_ensemble_members':32,'r332_subsistence_domains':8,'r332_regional_anchor_states':9,'exact_deterministic_revalidation_performed':True,'managed_resource_transition_pockets_available':True,'transition_pockets_realized_food_production':False,'regional_continuity_codes_available':True,'named_culture_materialized':False,'agriculture_materialized':False,'domesticated_species_materialized':False,'final_human_species_identity_materialized':False,'new_external_engine_execution_performed':False,'r332_scientific_rerun_performed':False,'numeric_historical_truth_claimed':False,'canonical_state_changed':False,'derived_refinement_promoted_to_canon':False,'deep_biological_coupling':False},'recommended_next_action':'RECONCILE_SEALED_R333_HOLOCENE_ENVIRONMENT_ECOLOGICAL_PARTNERS_DOMESTICATION_TRAJECTORIES_AND_FOOD_PRODUCTION_EMERGENCE_AGAINST_R513_HANDOFF_BEFORE_ACCEPTING_REALIZED_DOMESTICATION_OR_FOOD_PRODUCTION_HISTORY'}
 write_json(out/'R5_13_INTEGRATED_RECONCILIATION.json',audit)
 names=['R5_13_RUNTIME_UTILITY_REVIEW.json','R5_13_PARENT_AUTHORITY_BINDING.json','R5_13_R332_DETERMINISTIC_REPLAY_ALIGNMENT.json','R5_13_R332_SUBSISTENCE_READINESS_CLASSIFICATION.json','R5_13_0KA_SUBSISTENCE_REGIONAL_READINESS_RECONCILED_HANDOFF.json','R5_13_INTEGRATED_RECONCILIATION.json']
 write_json(out/'R5_13_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':audit['status'],'files':{n:{'bytes':(out/n).stat().st_size,'sha256':sha256_file(out/n)} for n in names}})
 return audit
