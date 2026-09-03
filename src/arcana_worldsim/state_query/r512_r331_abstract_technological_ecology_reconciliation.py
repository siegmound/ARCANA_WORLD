from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json
import numpy as np

STAGE='v0.6D1-R5.12'
OUT_REL=Path('outputs/v0_6D1_R5_12')
TARGET_COHORT=('RPT_010_D02','RPT_009_D02')
FINAL_STATUS='PASS_R512_R511_TO_R331_ABSTRACT_CULTURAL_TECHNOLOGICAL_ECOLOGY_RECONCILIATION_CANDIDATE'
EXPECTED_MEMBERS=32
EXPECTED_TIME_STATES=175
EXPECTED_ANCHORS=11
EXPECTED_TECH_DOMAINS=('portable_toolkit_systems','composite_tool_systems','food_processing_and_extraction','thermal_environmental_control','shelter_and_site_engineering','transport_and_logistical_systems','storage_and_resource_buffering','cooperative_specialization_systems')
EXPECTED_ECOLOGY=('transmission_fidelity','innovation_opportunity','retention_support','repertoire_breadth','technical_resilience','niche_buffering','specialization_potential','interlineage_diffusion_opportunity','innovation_flux_equivalent','loss_flux_equivalent')
EXPECTED_GROUP=('represented_people','represented_camps','tech_access','repertoire_breadth','technical_resilience','specialization_access','innovation_support','interlineage_transfer_access')

# Exact R5.11 source authority from the distributed post-R5.10 overlay.
EXPECTED_R511_SOURCE_MANIFEST_SHA256='375da474df1e75f583c7ab175aa60f0d5758b9c837a3f6860dec672b23fbccdb'
EXPECTED_R511_SOURCE_MODULE_SHA256='54f8eac3033b87c76e7f903dc67586b7cb7fc8cf83bb8183bae9082f6029bcda'
EXPECTED_R511_CONFIG_SHA256='e07a46fa65caf03707a0bd708987b8b22337742372de2dad93b10c9baee730b6'
EXPECTED_R511_CONTRACT_SHA256='f8265e07a375728ca2b164801b560c206c7502afdb94faa69c35d97c5778f8f4'

# Immutable sealed R3.31 authority.
EXPECTED_R331_FINAL_SEAL_AUDIT_SHA256='43a92d8e269b85010ba43dec093b78b61ea644f132b34e4a78ae5ae521048dfe'
EXPECTED_R331_FINAL_SEAL_MANIFEST_SHA256='c76249f5c68a3c118951bb6a91d5d04eb6a77cbd5bf0bb0b8fb2a34e81f5b2ed'
EXPECTED_R331_OUTPUT_MANIFEST_SHA256='a6543d2ca5a7555c4363222663fc818d23e83fec3d6df30029df4bab5d7c678e'
EXPECTED_R331_REPLAY_SHA256='9f5ddb0fd1356ea681b72b52329e6804eb7ef47a269f923ba684486d5afaf941'
EXPECTED_R331_GROUP_SHA256='fde0f7d954d55a606481834c0cce6e4bf4ebb340db059e88e94cd851633af0cd'
EXPECTED_R331_AUTHORITY_SHA256='e83314a98da9ecc86635847e5a9ccea058d29366fc3c259e9a7731ccc8796778'
EXPECTED_R331_CHECKPOINT_SHA256='a804f388c2e656e4abec9fc1fb55cdb710824b686526a1780cfd67cec95fabf8'
EXPECTED_R331_OUTCOMES_SHA256='b0bd863936b41ea8b4775b697a83a312e4cf55451b0cb8e4edcba975fc4834ef'
EXPECTED_R331_SENSITIVITY_SHA256='41cd8505650868a32d139e6760bb610df773275bd06928d7468cfe089cfec153'
EXPECTED_R331_AUDIT_SHA256='65f615eacc2740307cc8ef134dbc301adb152f85be083d8c789f0cf62142686b'
EXPECTED_R331_SOURCE_MANIFEST_SHA256='45bf4bb0d738463647df1114cc1f13ea66ab8404651a6052fecede52becbaeed'
EXPECTED_R331_SOURCE_MODULE_SHA256='db4c0bafcdfbf830f8119fb8ec61456fd5005412d464e315e36870104bc340f7'
EXPECTED_R331_CONFIG_SHA256='deb154bb2fea19d01c4cf443316d5bb075b9d437c680674ea35f882b1a547736'
EXPECTED_R331_CONTRACT_SHA256='45f0be8c401f737aacabe91bea6310684259b267915d485e2c63a24b5f757e1a'
EXPECTED_R329_REPLAY_SHA256='bbdde55933575153a88e570e3dc5709b38a09f696ffc2777c28299fc3cd3112a'
EXPECTED_R330_CENSUS_SHA256='f890169abce22641dddf95d82ff34d641c9bbde1362cd15e13cb0a8f34e6a919'
EXPECTED_R330_GROUP_SHA256='ede3b7ad301ce3e6b51cd3c8f4e70ff2392a43e50695b676b56912191d51cd57'

R511_OUT=Path('outputs/v0_6D1_R5_11')
R511_MANIFEST=R511_OUT/'R5_11_OUTPUT_MANIFEST.json'
R511_AUDIT=R511_OUT/'R5_11_INTEGRATED_RECONCILIATION.json'
R511_HANDOFF=R511_OUT/'R5_11_0KA_CENSUS_GROUP_RECONCILED_HANDOFF.json'
R511_BINDING=R511_OUT/'R5_11_PARENT_AUTHORITY_BINDING.json'
R511_SOURCE_MANIFEST=Path('SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_11.json')
R511_SOURCE_MODULE=Path('src/arcana_worldsim/state_query/r511_r330_census_group_reconciliation.py')
R511_CONFIG=Path('configs/world1_r511_r330_census_group_reconciliation_v0_6D1_R5_11.json')
R511_CONTRACT=Path('R5_11_R510_R330_CENSUS_GROUP_ABM_RECONCILIATION_CONTRACT.md')

R329_REPLAY=Path('outputs/v0_6D1_R3_29/R3_29_COMMUNITY_NETWORK_REPLAY.npz')
R330_CENSUS=Path('outputs/v0_6D1_R3_30/R3_30_CENSUS_AND_GROUP_TIMESERIES.npz')
R330_GROUP=Path('outputs/v0_6D1_R3_30/R3_30_WEIGHTED_GROUP_ABM.npz')
R331_OUT=Path('outputs/v0_6D1_R3_31')
R331_SEAL_OUT=Path('outputs/v0_6D1_R3_31_SEAL')
R331_REPLAY=R331_OUT/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz'
R331_GROUP=R331_OUT/'R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz'
R331_AUTHORITY=R331_OUT/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_AUTHORITY.json'
R331_CHECKPOINT=R331_OUT/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_CHECKPOINT.json'
R331_OUTCOMES=R331_OUT/'R3_31_LINEAGE_TECHNOLOGICAL_ECOLOGY_OUTCOMES.json'
R331_SENSITIVITY=R331_OUT/'R3_31_SENSITIVITY_AND_ROBUSTNESS.json'
R331_AUDIT=R331_OUT/'R3_31_INTEGRATED_AUDIT.json'
R331_OUTPUT_MANIFEST=R331_OUT/'R3_31_OUTPUT_MANIFEST.json'
R331_SEAL_AUDIT=R331_SEAL_OUT/'R3_31_FINAL_SEAL_AUDIT.json'
R331_SEAL_MANIFEST=R331_SEAL_OUT/'R3_31_FINAL_SEAL_MANIFEST.json'
R331_SOURCE_MANIFEST=Path('SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_31.json')
R331_SOURCE_MODULE=Path('src/arcana_worldsim/scientific_engines/r331_cultural_technological_ecology.py')
R331_CONFIG=Path('configs/world1_r331_cultural_technological_ecology_v0_6D1_R3_31.json')
R331_CONTRACT=Path('R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_CONTRACT.md')

R512_CONFIG=Path('configs/world1_r512_r331_abstract_technological_ecology_reconciliation_v0_6D1_R5_12.json')

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

def _source_manifest_integrity(root:Path,rel:Path)->bool:
 try:
  m=load_json(root/rel)
  for n,x in (m.get('files') or {}).items():
   p=root/n
   if not p.is_file() or p.stat().st_size!=int(x.get('bytes',-1)) or sha256_file(p)!=x.get('sha256'):return False
  return True
 except Exception:return False

def validate_parent_authority(root:Path)->dict[str,Any]:
 root=Path(root).resolve();checks={}
 required=[R511_MANIFEST,R511_AUDIT,R511_HANDOFF,R511_BINDING,R511_SOURCE_MANIFEST,R511_SOURCE_MODULE,R511_CONFIG,R511_CONTRACT,R329_REPLAY,R330_CENSUS,R330_GROUP,R331_REPLAY,R331_GROUP,R331_AUTHORITY,R331_CHECKPOINT,R331_OUTCOMES,R331_SENSITIVITY,R331_AUDIT,R331_OUTPUT_MANIFEST,R331_SEAL_AUDIT,R331_SEAL_MANIFEST,R331_SOURCE_MANIFEST,R331_SOURCE_MODULE,R331_CONFIG,R331_CONTRACT]
 for rel in required:checks[f'present::{rel.as_posix()}']=(root/rel).is_file()
 try:
  ok,_=_manifest_integrity(root/R511_OUT,root/R511_MANIFEST);a=load_json(root/R511_AUDIT);h=load_json(root/R511_HANDOFF)
  checks['r511_output_manifest_integrity']=ok
  checks['r511_candidate_semantics']=(a.get('status')=='PASS_R511_R510_TO_R330_CENSUS_GROUP_ABM_RECONCILIATION_CANDIDATE' and a.get('scientific_candidate_eligible') is True and int(a.get('checks_passed',-1))==36 and int(a.get('checks_total',-1))==36 and not(a.get('failed') or []))
  checks['r511_handoff_exact']=(h.get('status')=='R511_RECONCILED_CENSUS_EQUIVALENT_WEIGHTED_GROUP_HANDOFF_0KA' and float(h.get('age_ka',-1))==0.0 and tuple(h.get('candidate_cohort') or [])==TARGET_COHORT and int(h.get('candidate_count',-1))==2 and h.get('unique_human_identity') is None and h.get('unique_human_identity_materialized') is False and h.get('literal_absolute_census_materialized') is False and h.get('person_level_abm_materialized') is False and h.get('ready_for_r331_reconciliation') is True and h.get('downstream_r331_auto_authorized') is False)
  checks['r511_source_manifest_exact_hash']=sha256_file(root/R511_SOURCE_MANIFEST)==EXPECTED_R511_SOURCE_MANIFEST_SHA256
  checks['r511_source_module_exact_hash']=sha256_file(root/R511_SOURCE_MODULE)==EXPECTED_R511_SOURCE_MODULE_SHA256
  checks['r511_config_exact_hash']=sha256_file(root/R511_CONFIG)==EXPECTED_R511_CONFIG_SHA256
  checks['r511_contract_exact_hash']=sha256_file(root/R511_CONTRACT)==EXPECTED_R511_CONTRACT_SHA256
 except Exception:
  for k in ['r511_output_manifest_integrity','r511_candidate_semantics','r511_handoff_exact','r511_source_manifest_exact_hash','r511_source_module_exact_hash','r511_config_exact_hash','r511_contract_exact_hash']:checks[k]=False
 try:
  seal=load_json(root/R331_SEAL_AUDIT);sm=load_json(root/R331_SEAL_MANIFEST);ia=load_json(root/R331_AUDIT)
  checks['r331_final_seal_audit_exact_hash']=sha256_file(root/R331_SEAL_AUDIT)==EXPECTED_R331_FINAL_SEAL_AUDIT_SHA256
  checks['r331_final_seal_manifest_exact_hash']=sha256_file(root/R331_SEAL_MANIFEST)==EXPECTED_R331_FINAL_SEAL_MANIFEST_SHA256
  checks['r331_final_seal_manifest_binds_audit']=(((sm.get('files') or {}).get('R3_31_FINAL_SEAL_AUDIT.json') or {}).get('sha256')==EXPECTED_R331_FINAL_SEAL_AUDIT_SHA256)
  checks['r331_final_seal_semantics']=(seal.get('verdict')=='SEALED' and seal.get('status')=='PASS_R331_LATE_PLEISTOCENE_TO_HOLOCENE_CULTURAL_TECHNOLOGICAL_ECOLOGY_TRANSMISSION_RETENTION_AND_TECHNICAL_REPERTOIRE_SEALED' and int(seal.get('checks_passed',-1))==29 and int(seal.get('checks_failed',-1))==0)
  checks['r331_integrated_audit_semantics']=(ia.get('status')=='PASS_R331_CULTURAL_TECHNOLOGICAL_ECOLOGY_CANDIDATE' and int(ia.get('checks_passed',-1))==27 and int(ia.get('checks_total',-1))==27 and int(ia.get('checks_failed',-1))==0)
  checks['r331_output_manifest_exact_hash']=sha256_file(root/R331_OUTPUT_MANIFEST)==EXPECTED_R331_OUTPUT_MANIFEST_SHA256
  ok,_=_manifest_integrity(root/R331_OUT,root/R331_OUTPUT_MANIFEST);checks['r331_output_manifest_integrity']=ok
  exact={R331_REPLAY:EXPECTED_R331_REPLAY_SHA256,R331_GROUP:EXPECTED_R331_GROUP_SHA256,R331_AUTHORITY:EXPECTED_R331_AUTHORITY_SHA256,R331_CHECKPOINT:EXPECTED_R331_CHECKPOINT_SHA256,R331_OUTCOMES:EXPECTED_R331_OUTCOMES_SHA256,R331_SENSITIVITY:EXPECTED_R331_SENSITIVITY_SHA256,R331_AUDIT:EXPECTED_R331_AUDIT_SHA256,R329_REPLAY:EXPECTED_R329_REPLAY_SHA256,R330_CENSUS:EXPECTED_R330_CENSUS_SHA256,R330_GROUP:EXPECTED_R330_GROUP_SHA256}
  checks['r331_and_parent_artifact_hashes_exact']=all((root/p).is_file() and sha256_file(root/p)==v for p,v in exact.items())
  checks['r331_source_manifest_exact_hash']=sha256_file(root/R331_SOURCE_MANIFEST)==EXPECTED_R331_SOURCE_MANIFEST_SHA256
  checks['r331_source_manifest_integrity']=_source_manifest_integrity(root,R331_SOURCE_MANIFEST)
  checks['r331_source_module_exact_hash']=sha256_file(root/R331_SOURCE_MODULE)==EXPECTED_R331_SOURCE_MODULE_SHA256
  checks['r331_config_exact_hash']=sha256_file(root/R331_CONFIG)==EXPECTED_R331_CONFIG_SHA256
  checks['r331_contract_exact_hash']=sha256_file(root/R331_CONTRACT)==EXPECTED_R331_CONTRACT_SHA256
 except Exception:
  for k in ['r331_final_seal_audit_exact_hash','r331_final_seal_manifest_exact_hash','r331_final_seal_manifest_binds_audit','r331_final_seal_semantics','r331_integrated_audit_semantics','r331_output_manifest_exact_hash','r331_output_manifest_integrity','r331_and_parent_artifact_hashes_exact','r331_source_manifest_exact_hash','r331_source_manifest_integrity','r331_source_module_exact_hash','r331_config_exact_hash','r331_contract_exact_hash']:checks[k]=False
 checks={k:bool(v) for k,v in checks.items()};failed=[k for k,v in checks.items() if not v]
 return {'stage':STAGE,'status':'PASS_R512_IMMUTABLE_R511_R331_PARENT_AUTHORITY' if not failed else 'BLOCKED_R512_PARENT_AUTHORITY','pass':not failed,'checks_passed':len(checks)-len(failed),'checks_total':len(checks),'failed':failed,'checks':checks}

def reconcile(root:Path)->dict[str,Any]:
 root=Path(root).resolve();out=root/OUT_REL;cfg=load_json(root/R512_CONFIG);parent=validate_parent_authority(root);checks={'parent_authority_pass':parent['pass']}
 try:
  from arcana_worldsim.scientific_engines import r331_cultural_technological_ecology as r331
  h511=load_json(root/R511_HANDOFF);cfg331=load_json(root/R331_CONFIG);auth=load_json(root/R331_AUTHORITY);cp=load_json(root/R331_CHECKPOINT);outcomes=load_json(root/R331_OUTCOMES);sens=load_json(root/R331_SENSITIVITY)
  z29=np.load(root/R329_REPLAY,allow_pickle=False);z30=np.load(root/R330_CENSUS,allow_pickle=False);g30=np.load(root/R330_GROUP,allow_pickle=False);z31=np.load(root/R331_REPLAY,allow_pickle=False);g31=np.load(root/R331_GROUP,allow_pickle=False)
  inp={'z29':z29,'z30':z30,'g30':g30};re=r331.replay_technology(inp,cfg331);rg=r331.build_group_anchors(inp,re)
  ids=tuple(map(str,z31['candidate_ids']));members=np.asarray(z31['parent_member_indices']);age=np.asarray(z31['age_ka']);stock=np.asarray(z31['technology_domain_stock']);eco=np.asarray(z31['cultural_technological_ecology']);tn=tuple(map(str,z31['technology_domain_names']));en=tuple(map(str,z31['ecology_variable_names']));gn=tuple(map(str,g31['group_variable_names']));G=np.asarray(g31['group_state']);GA=np.asarray(g31['group_active'])
  A30=np.asarray(g30['agent_state']);AA30=np.asarray(g30['agent_active']);a_names=list(map(str,g30['agent_variable_names']));ai={n:i for i,n in enumerate(a_names)}
  stock_err=float(np.max(np.abs(re['domain_stock']-stock)));eco_err=float(np.max(np.abs(re['ecology']-eco)));group_err=float(np.max(np.abs(rg['group_state']-G)))
  checks.update({
   'config_target_cohort_exact':tuple(cfg.get('target_cohort') or [])==TARGET_COHORT,
   'r511_handoff_two_lineage_exact':tuple(h511.get('candidate_cohort') or [])==TARGET_COHORT and h511.get('unique_human_identity_materialized') is False,
   'r331_candidate_order_exact':ids==TARGET_COHORT,
   'r331_parent_member_indices_exact':np.array_equal(members,np.asarray(z30['parent_member_indices'])) and len(members)==EXPECTED_MEMBERS,
   'r331_age_axis_exact_r330':np.array_equal(age,np.asarray(z30['age_ka'])) and len(age)==EXPECTED_TIME_STATES,
   'r331_technology_domain_names_exact':tn==EXPECTED_TECH_DOMAINS and tuple(cfg331.get('technology_domains') or [])==EXPECTED_TECH_DOMAINS,
   'r331_domain_stock_geometry_exact':stock.shape==(32,2,175,8),
   'r331_ecology_names_exact':en==EXPECTED_ECOLOGY,
   'r331_ecology_geometry_exact':eco.shape==(32,2,175,10),
   'r331_group_anchor_axis_exact_r330':np.array_equal(np.asarray(g31['anchor_age_ka']),np.asarray(g30['anchor_age_ka'])) and len(g31['anchor_age_ka'])==EXPECTED_ANCHORS,
   'r331_group_variable_names_exact':gn==EXPECTED_GROUP,
   'r331_group_geometry_exact':G.shape==(32,2,11,48,8),
   'r331_group_active_exact_parent':np.array_equal(GA,AA30),
   'r331_group_represented_people_exact_parent':np.array_equal(G[...,0],A30[...,ai['represented_people']]),
   'r331_group_represented_camps_exact_parent':np.array_equal(G[...,1],A30[...,ai['represented_camps']]),
   'r331_deterministic_domain_stock_replay_exact':stock_err==0.0 and np.array_equal(re['domain_stock'],stock),
   'r331_deterministic_ecology_replay_exact':eco_err==0.0 and np.array_equal(re['ecology'],eco),
   'r331_deterministic_group_anchor_replay_exact':group_err==0.0 and np.array_equal(rg['group_state'],G) and np.array_equal(rg['group_active'],GA),
   'r331_all_numeric_finite':np.isfinite(stock).all() and np.isfinite(eco).all() and np.isfinite(G).all(),
   'r331_domain_stock_bounded':float(np.min(stock))>=0.0 and float(np.max(stock))<=1.0,
   'r331_ecology_bounded_and_flux_nonnegative':float(np.min(eco[...,:8]))>=0.0 and float(np.max(eco[...,:8]))<=1.0 and float(np.min(eco[...,8:]))>=0.0,
   'r331_frozen_dynamics_exact':auth.get('dynamics')=={'cross_lineage_transfer_rate_per_kyr':0.018,'innovation_rate_per_kyr':0.055,'loss_rate_per_kyr':0.032,'repertoire_operational_threshold':0.4},
   'r331_frozen_dynamics_not_historical_truth':cfg.get('r331_rates_historical_truth') is False,
   'r331_sensitivity_25_no_selection_gate':int(sens.get('variant_count',-1))==25 and len(sens.get('variants') or [])==25 and sens.get('selection_gate') is False,
   'r331_both_lineages_retained_under_sensitivity':tuple(sens.get('candidate_retention') or [])==TARGET_COHORT,
   'r331_outcomes_remain_abstract':tuple(outcomes.get('candidate_lineages') or [])==TARGET_COHORT and all(x.get('interpretation')=='ABSTRACT_FUNCTIONAL_TECHNOLOGICAL_ECOLOGY_NOT_SPECIFIC_ARTIFACT_INVENTORY' for x in outcomes.get('lineages') or []),
   'r331_checkpoint_two_lineages_no_unique_identity':tuple(cp.get('candidate_cohort') or [])==TARGET_COHORT and int(cp.get('candidate_count',-1))==2 and cp.get('unique_human_identity') is None and cp.get('unique_human_identity_materialized') is False,
   'r331_technology_semantics_abstract_not_specific':auth.get('technology_semantics')=='ABSTRACT_FUNCTIONAL_TECHNOLOGY_DOMAIN_STOCK_NOT_SPECIFIC_ARCHAEOLOGICAL_ARTIFACT' and cfg.get('r331_technology_stocks_specific_artifacts') is False,
   'r331_culture_semantics_not_named':auth.get('culture_semantics')=='TRANSMISSION_RETENTION_AND_CUMULATION_ECOLOGY_NOT_NAMED_CULTURE_OR_LANGUAGE',
   'r331_no_specific_artifact_or_named_invention':auth.get('specific_artifact_materialized') is False and cfg.get('r331_named_inventions_materialized') is False and cfg.get('r331_invention_dates_materialized') is False,
   'r331_no_language_religion_agriculture_city_state':all(auth.get(k) is False for k in ('language_materialized','religion_materialized','agriculture_materialized','city_state_materialized')),
   'r331_no_ethnicity_named_culture':auth.get('ethnicity_materialized') is False and auth.get('named_culture_materialized') is False,
   'r331_no_unique_human_identity':auth.get('unique_human_identity_materialized') is False,
   'r331_interlineage_diffusion_not_realized_history':cfg.get('r331_diffusion_realized_history') is False and 'interlineage_diffusion_opportunity' in en and 'interlineage_transfer_access' in gn,
   'r331_evidence_basis_inherited_not_revalidated_here':cfg.get('r331_evidence_basis_revalidated_in_r512') is False and len(auth.get('evidence_basis') or {})==8,
   'no_new_external_engine_execution':cfg.get('external_engine_execution') is False,
   'r331_not_scientifically_rerun_or_mutated':cfg.get('rerun_r331_scientific_stage') is False and cfg.get('deterministic_formula_revalidation') is True and sha256_file(root/R331_REPLAY)==EXPECTED_R331_REPLAY_SHA256 and sha256_file(root/R331_GROUP)==EXPECTED_R331_GROUP_SHA256,
   'numeric_historical_truth_not_claimed':cfg.get('numeric_historical_truth_claimed') is False,
   'canonical_state_unchanged':cfg.get('canonical_state_changed') is False,
   'derived_refinement_not_promoted':cfg.get('derived_refinement_promoted_to_canon') is False,
   'deep_biological_coupling_off':cfg.get('deep_biological_coupling') is False and auth.get('deep_biological_coupling') is False,
   'downstream_r332_not_auto_authorized':cfg.get('auto_authorize_downstream_r332') is False,
  })
 except Exception as exc:
  checks['reconciliation_exception_free']=False;checks['exception_detail']=False
 checks={k:bool(v) for k,v in checks.items()};failed=[k for k,v in checks.items() if not v]
 out.mkdir(parents=True,exist_ok=True)
 utility={'stage':STAGE,'status':'PASS_R512_RUNTIME_UTILITY_REVIEW_NO_NEW_ENGINE_REQUIRED','new_external_engine_execution_performed':False,'decision':'NO_NEW_ENGINE_OR_R331_SCIENTIFIC_RERUN_REQUIRED','reason':'R3.31 is already SEALED and its deterministic ARCANA-native functional technological-ecology transformation can be exactly revalidated from immutable R3.29/R3.30 parents.','considered':{'SLiM_5_2':'NOT_RERUN_NO_NEW_ANCESTRY_QUESTION','NEMO_2_4_2':'NOT_RERUN_NO_NEW_GENE_FLOW_QUESTION','CDMetaPOP_3_08':'NOT_RERUN_NO_NEW_PERSISTENCE_QUESTION','RangeShiftR_3_0_1':'NOT_RERUN_NO_NEW_CORRIDOR_QUESTION','new_cultural_ABM_runtime':'NOT_REQUIRED_R331_IS_DETERMINISTIC_ARCANA_NATIVE_FUNCTIONAL_ECOLOGY'}}
 write_json(out/'R5_12_RUNTIME_UTILITY_REVIEW.json',utility)
 binding={'stage':STAGE,'status':'R512_PARENT_AUTHORITY_BINDING','r511_output_manifest_sha256':sha256_file(root/R511_MANIFEST) if (root/R511_MANIFEST).is_file() else None,'r511_handoff_sha256':sha256_file(root/R511_HANDOFF) if (root/R511_HANDOFF).is_file() else None,'r331_final_seal_audit_sha256':sha256_file(root/R331_SEAL_AUDIT) if (root/R331_SEAL_AUDIT).is_file() else None,'r331_output_manifest_sha256':sha256_file(root/R331_OUTPUT_MANIFEST) if (root/R331_OUTPUT_MANIFEST).is_file() else None,'r331_replay_sha256':sha256_file(root/R331_REPLAY) if (root/R331_REPLAY).is_file() else None,'r331_group_anchor_sha256':sha256_file(root/R331_GROUP) if (root/R331_GROUP).is_file() else None,'r329_replay_sha256':sha256_file(root/R329_REPLAY) if (root/R329_REPLAY).is_file() else None,'r330_census_sha256':sha256_file(root/R330_CENSUS) if (root/R330_CENSUS).is_file() else None,'r330_group_sha256':sha256_file(root/R330_GROUP) if (root/R330_GROUP).is_file() else None,'binding_semantics':'R511_RECONCILED_0KA_CENSUS_GROUP_HANDOFF_PLUS_IMMUTABLE_SEALED_R331_ABSTRACT_TECHNOLOGICAL_ECOLOGY_AND_EXACT_R329_R330_PARENTS'}
 write_json(out/'R5_12_PARENT_AUTHORITY_BINDING.json',binding)
 alignment={'stage':STAGE,'status':'PASS_R512_R331_EXACT_DETERMINISTIC_REPLAY_ALIGNMENT' if not failed else 'BLOCKED_R512_R331_REPLAY_ALIGNMENT','candidate_cohort':list(TARGET_COHORT),'ensemble_members':32,'time_states':175,'technology_domains':8,'ecology_fields':10,'group_anchor_states':11,'group_agents_per_lineage_member':48,'domain_stock_max_abs_error':locals().get('stock_err',None),'ecology_max_abs_error':locals().get('eco_err',None),'group_anchor_max_abs_error':locals().get('group_err',None),'semantics':'EXACT_IN_MEMORY_REVALIDATION_OF_FROZEN_R331_FORMULAS_WITHOUT_REWRITING_OR_SCIENTIFICALLY_RERUNNING_R331'}
 write_json(out/'R5_12_R331_DETERMINISTIC_REPLAY_ALIGNMENT.json',alignment)
 classification={'stage':STAGE,'status':'R512_R331_ABSTRACT_TECHNOLOGICAL_ECOLOGY_CLASSIFICATION','technology_domains':list(EXPECTED_TECH_DOMAINS),'classification':'ABSTRACT_FUNCTIONAL_REPERTOIRE_STOCKS_NOT_SPECIFIC_ARTIFACTS_NAMED_INVENTIONS_OR_ARCHAEOLOGICAL_INDUSTRIES','frozen_dynamics':auth.get('dynamics') if 'auth' in locals() else None,'dynamics_classification':'SEALED_LEGACY_DIAGNOSTIC_MODEL_HYPERPARAMETERS_NOT_MEASURED_HISTORICAL_RATES_OR_CANONICAL_NUMERIC_TRUTH','ecology_fields':list(EXPECTED_ECOLOGY),'ecology_classification':'ABSTRACT_TRANSMISSION_RETENTION_CUMULATION_AND_RESILIENCE_DIAGNOSTICS','group_fields':list(EXPECTED_GROUP),'group_classification':'WEIGHTED_GROUP_ACCESS_DIAGNOSTICS_NOT_PERSON_LEVEL_TECHNOLOGY_INVENTORIES_OR_OBSERVED_CAMP_TECHNOLOGIES','diffusion_semantics':'INTERLINEAGE_DIFFUSION_OPPORTUNITY_AND_TRANSFER_ACCESS_ARE_MODEL_OPPORTUNITY_FIELDS_NOT_REALIZED_HISTORICAL_BORROWING_GENE_FLOW_OR_ANCESTRY','evidence_basis_status':'INHERITED_FROM_SEALED_R331_NOT_REVALIDATED_BY_R512'}
 write_json(out/'R5_12_R331_ABSTRACT_TECHNOLOGY_CLASSIFICATION.json',classification)
 handoff={'stage':STAGE,'status':'R512_RECONCILED_ABSTRACT_TECHNOLOGICAL_ECOLOGY_HANDOFF_0KA','age_ka':0.0,'candidate_cohort':list(TARGET_COHORT),'candidate_count':2,'unique_human_identity':None,'unique_human_identity_materialized':False,'abstract_technological_ecology_layer_available':True,'technology_domain_count':8,'technology_domains':list(EXPECTED_TECH_DOMAINS),'specific_artifact_inventory_materialized':False,'named_invention_materialized':False,'historical_invention_date_materialized':False,'named_culture_materialized':False,'language_materialized':False,'religion_materialized':False,'agriculture_materialized':False,'city_state_materialized':False,'ethnicity_materialized':False,'literal_historical_cultural_transfer_materialized':False,'source_r511_handoff_sha256':sha256_file(root/R511_HANDOFF) if (root/R511_HANDOFF).is_file() else None,'source_r331_final_seal_audit_sha256':sha256_file(root/R331_SEAL_AUDIT) if (root/R331_SEAL_AUDIT).is_file() else None,'source_r331_replay_sha256':sha256_file(root/R331_REPLAY) if (root/R331_REPLAY).is_file() else None,'ready_for_r332_reconciliation':not failed,'downstream_r332_auto_authorized':False}
 write_json(out/'R5_12_0KA_ABSTRACT_TECHNOLOGICAL_ECOLOGY_RECONCILED_HANDOFF.json',handoff)
 audit={'stage':STAGE,'status':FINAL_STATUS if not failed else 'BLOCKED_R512_R511_TO_R331_RECONCILIATION','scientific_candidate_eligible':not failed,'checks_passed':len(checks)-len(failed),'checks_total':len(checks),'failed':failed,'checks':checks,'summary':{'target_cohort':list(TARGET_COHORT),'r331_time_states':175,'r331_ensemble_members':32,'r331_technology_domains':8,'r331_group_anchor_states':11,'exact_deterministic_revalidation_performed':True,'specific_artifact_materialized':False,'named_invention_materialized':False,'named_culture_materialized':False,'final_human_species_identity_materialized':False,'new_external_engine_execution_performed':False,'r331_scientific_rerun_performed':False,'numeric_historical_truth_claimed':False,'canonical_state_changed':False,'derived_refinement_promoted_to_canon':False,'deep_biological_coupling':False},'recommended_next_action':'RECONCILE_SEALED_R332_SUBSISTENCE_INTENSIFICATION_REGIONAL_CULTURAL_LINEAGES_AND_HOLOCENE_TRANSITION_READINESS_AGAINST_R512_HANDOFF_BEFORE_ACCEPTING_DOWNSTREAM_SUBSISTENCE_HISTORY'}
 write_json(out/'R5_12_INTEGRATED_RECONCILIATION.json',audit)
 names=['R5_12_RUNTIME_UTILITY_REVIEW.json','R5_12_PARENT_AUTHORITY_BINDING.json','R5_12_R331_DETERMINISTIC_REPLAY_ALIGNMENT.json','R5_12_R331_ABSTRACT_TECHNOLOGY_CLASSIFICATION.json','R5_12_0KA_ABSTRACT_TECHNOLOGICAL_ECOLOGY_RECONCILED_HANDOFF.json','R5_12_INTEGRATED_RECONCILIATION.json']
 write_json(out/'R5_12_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':audit['status'],'files':{n:{'bytes':(out/n).stat().st_size,'sha256':sha256_file(out/n)} for n in names}})
 return audit
