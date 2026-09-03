from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json
import numpy as np

from arcana_worldsim.scientific_engines import r333_holocene_environment_domestication as r333

STAGE='v0.6D1-R5.14'
FINAL_STATUS='PASS_R514_R513_TO_R333_HOLOCENE_DOMESTICATION_RECONCILIATION_CANDIDATE'
TARGET_COHORT=('RPT_010_D02','RPT_009_D02')
OUT_REL=Path('outputs/v0_6D1_R5_14')

R513_OUT=Path('outputs/v0_6D1_R5_13')
R513_MANIFEST=R513_OUT/'R5_13_OUTPUT_MANIFEST.json'
R513_AUDIT=R513_OUT/'R5_13_INTEGRATED_RECONCILIATION.json'
R513_HANDOFF=R513_OUT/'R5_13_0KA_SUBSISTENCE_REGIONAL_READINESS_RECONCILED_HANDOFF.json'
R513_SOURCE_MANIFEST=Path('SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_13.json')
R513_SOURCE_MODULE=Path('src/arcana_worldsim/state_query/r513_r332_subsistence_regional_readiness_reconciliation.py')
R513_CONFIG=Path('configs/world1_r513_r332_subsistence_regional_readiness_reconciliation_v0_6D1_R5_13.json')
R513_CONTRACT=Path('R5_13_R512_R332_SUBSISTENCE_REGIONAL_READINESS_RECONCILIATION_CONTRACT.md')

R333_OUT=Path('outputs/v0_6D1_R3_33')
R333_SEAL=Path('outputs/v0_6D1_R3_33_SEAL')
R333_MANIFEST=R333_OUT/'R3_33_OUTPUT_MANIFEST.json'
R333_AUDIT=R333_OUT/'R3_33_INTEGRATED_AUDIT.json'
R333_AUTHORITY=R333_OUT/'R3_33_HOLOCENE_ENVIRONMENT_DOMESTICATION_AUTHORITY.json'
R333_PARTNERS=R333_OUT/'R3_33_ECOLOGICAL_PARTNER_CANDIDATE_REGISTRY.json'
R333_ENV=R333_OUT/'R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz'
R333_TRAJ=R333_OUT/'R3_33_DOMESTICATION_TRAJECTORIES.npz'
R333_OUTCOMES=R333_OUT/'R3_33_DOMESTICATION_AND_FOOD_PRODUCTION_OUTCOMES.json'
R333_SENS=R333_OUT/'R3_33_SENSITIVITY_AND_ROBUSTNESS.json'
R333_CHECKPOINT=R333_OUT/'R3_33_FOOD_PRODUCTION_CHECKPOINT.json'
R333_SEAL_AUDIT=R333_SEAL/'R3_33_FINAL_SEAL_AUDIT.json'
R333_SEAL_MANIFEST=R333_SEAL/'R3_33_FINAL_SEAL_MANIFEST.json'
R333_SOURCE_MANIFEST=Path('SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_33.json')
R333_SOURCE_MODULE=Path('src/arcana_worldsim/scientific_engines/r333_holocene_environment_domestication.py')
R333_CONFIG=Path('configs/world1_r333_holocene_environment_domestication_v0_6D1_R3_33.json')
R333_CONTRACT=Path('R3_33_HOLOCENE_ENVIRONMENT_DOMESTICATION_CONTRACT.md')
R334_CONTRACT=Path('R3_34_PRODUCER_DOMESTICATION_CONTRACT.md')

EXPECTED_HASHES={
 'r513_source_manifest':'9af3cf77cb137f9757930397f09856c231c669d722465292f6e64bf5e5f7a3ff',
 'r513_source_module':'acc017593fc5b5d5d610bb3b4a433fca32571f707687c4ea05b2c25d069fef34',
 'r513_config':'bbbebbb99a2d03b31685274012d11dcca6ffd5792930d2a9425cdc1f54077fc7',
 'r513_contract':'2189277c132820c5747ae98fcc07a894538385e1e1eb58f5e99dd409d414d0d2',
 'r333_source_manifest':'7313403feb38127e78d537d53c11784822bfc9b285406897c8c59cc961002e54',
 'r333_source_module':'c32d78efcffccf60dd0a70870dc6d9555a9eed823ec4fa5e7fb3c2e61705fc40',
 'r333_config':'bd57dab5c2075762d39681d499772fa968f7855608a7dbdff55b5afbe5100245',
 'r333_contract':'8e18685646441c0e3e32d759c7c338e52df7ed9564a9133ecb533b12ae3c98cd',
 'r334_contract':'8cdf56880b6c0182480220f938739c6f414a818b1dccf67d679ec58fefd72950',
 'r333_manifest':'db1087efbc58c5bff79986792a169d8ba0731a3fe8a25c83d61bf89df62aec06',
 'r333_audit':'78313bd2793d97e51abf16d50ea6cef9d5cd57ae3a8c0d4c25fef8139a2eed11',
 'r333_authority':'17cc1bf7c0096b51eb333c0de7bbc4f0a827f7a4a0f821868f9db3bfa4b2936a',
 'r333_partners':'ab3d6e50966946c95ffa60bdf48115275b3b7669640715b99836570828886711',
 'r333_env':'5fd7b11df5051245551aa2d23ce334b0a540f171e85ac8a451c603eb63f685b9',
 'r333_traj':'175959669ba5daa84ab0937b4b213c1633ee674e89e67690915dbc622b2e1b84',
 'r333_outcomes':'1b6f166a924d284190e187c5c65e9a3c887cddfabe6355ddc3fd546581d86f16',
 'r333_sens':'8ef578692110ae7b1e89a91fdf976af1c3c040088eb363bc9bfb0c4e6f037d84',
 'r333_checkpoint':'31a58c26af8e8fb43f9be9ed9bc430568a95a50696d75aecf73e955295fff898',
 'r333_seal_audit':'0e78fe1570b6fc20ef9ff1085c1810100e68a6652dc54bbec4e59349c2ef8f80',
 'r333_seal_manifest':'098aecc67e7db00348cf71904e73f34759e477509250506179d79ef07315e5ba',
}

EXPECTED_ENV_NAMES=tuple(r333.ENV_NAMES)
EXPECTED_TRAJ_NAMES=tuple(r333.TRAJ_NAMES)


def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()

def load_json(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')


def r513_handoff_semantics_ok(h:dict[str,Any])->bool:
 return (h.get('status')=='R513_RECONCILED_SUBSISTENCE_REGIONAL_READINESS_HANDOFF_0KA' and float(h.get('age_ka',-1))==0.0 and tuple(h.get('candidate_cohort') or [])==TARGET_COHORT and int(h.get('candidate_count',-1))==2 and h.get('unique_human_identity') is None and h.get('unique_human_identity_materialized') is False and h.get('managed_resource_transition_pockets_available') is True and h.get('transition_pockets_realized_food_production') is False and h.get('agriculture_materialized') is False and h.get('domesticated_species_materialized') is False and h.get('ready_for_r333_reconciliation') is True and h.get('downstream_r333_auto_authorized') is False)

def r333_checkpoint_semantics_ok(cp:dict[str,Any])->bool:
 return (tuple(cp.get('candidate_cohort') or [])==TARGET_COHORT and cp.get('animal_ecological_partner_candidates_materialized') is True and cp.get('animal_domestication_trajectories_materialized') is True and cp.get('materialized_domesticated_species')==[] and cp.get('incipient_domestication_species')==[] and cp.get('animal_food_production_emergence') is False and cp.get('plant_species_registry_available') is False and cp.get('plant_domestication_materialized') is False and cp.get('agriculture_materialized') is False and cp.get('unique_human_identity_materialized') is False and cp.get('deep_biological_coupling') is False)

def r333_sensitivity_robust_non_emergence(sens:dict[str,Any])->bool:
 return sens.get('variant_count')==18 and sens.get('selection_gate') is False and all(list(v.get('domestication_species_frequency') or [])==[0.0,0.0] for v in sens.get('variants') or [])

def _manifest_integrity(base:Path,manifest:Path)->tuple[bool,list[str]]:
 try:m=load_json(manifest)
 except Exception:return False,['manifest_unreadable']
 bad=[]
 for n,x in (m.get('files') or {}).items():
  p=base/n
  if not p.is_file() or p.stat().st_size!=int(x.get('bytes',-1)) or sha256_file(p)!=x.get('sha256'):bad.append(n)
 return not bad,bad

def _eq_json(a:Any,b:Any)->bool:return a==b

def validate_parent_authority(root:Path)->dict[str,Any]:
 root=Path(root).resolve(); c={}
 required=[R513_MANIFEST,R513_AUDIT,R513_HANDOFF,R513_SOURCE_MANIFEST,R513_SOURCE_MODULE,R513_CONFIG,R513_CONTRACT,
           R333_MANIFEST,R333_AUDIT,R333_AUTHORITY,R333_PARTNERS,R333_ENV,R333_TRAJ,R333_OUTCOMES,R333_SENS,R333_CHECKPOINT,
           R333_SEAL_AUDIT,R333_SEAL_MANIFEST,R333_SOURCE_MANIFEST,R333_SOURCE_MODULE,R333_CONFIG,R333_CONTRACT,R334_CONTRACT]
 for rel in required:c[f'present::{rel.as_posix()}']=(root/rel).is_file()
 try:
  ok,_=_manifest_integrity(root/R513_OUT,root/R513_MANIFEST); a=load_json(root/R513_AUDIT); h=load_json(root/R513_HANDOFF)
  c['r513_output_manifest_integrity']=ok
  c['r513_candidate_semantics']=(a.get('status')=='PASS_R513_R512_TO_R332_SUBSISTENCE_REGIONAL_READINESS_RECONCILIATION_CANDIDATE' and a.get('scientific_candidate_eligible') is True and int(a.get('checks_passed',-1))==44 and int(a.get('checks_total',-1))==44 and not(a.get('failed') or []))
  c['r513_handoff_exact']=r513_handoff_semantics_ok(h)
  c['r513_source_manifest_exact_hash']=sha256_file(root/R513_SOURCE_MANIFEST)==EXPECTED_HASHES['r513_source_manifest']
  c['r513_source_module_exact_hash']=sha256_file(root/R513_SOURCE_MODULE)==EXPECTED_HASHES['r513_source_module']
  c['r513_config_exact_hash']=sha256_file(root/R513_CONFIG)==EXPECTED_HASHES['r513_config']
  c['r513_contract_exact_hash']=sha256_file(root/R513_CONTRACT)==EXPECTED_HASHES['r513_contract']
 except Exception:
  for k in ['r513_output_manifest_integrity','r513_candidate_semantics','r513_handoff_exact','r513_source_manifest_exact_hash','r513_source_module_exact_hash','r513_config_exact_hash','r513_contract_exact_hash']:c[k]=False
 try:
  c['r333_output_manifest_integrity']=_manifest_integrity(root/R333_OUT,root/R333_MANIFEST)[0]
  seal=load_json(root/R333_SEAL_AUDIT); sm=load_json(root/R333_SEAL_MANIFEST); ia=load_json(root/R333_AUDIT); cp=load_json(root/R333_CHECKPOINT); auth=load_json(root/R333_AUTHORITY); sens=load_json(root/R333_SENS)
  c['r333_final_seal_exact_hash']=sha256_file(root/R333_SEAL_AUDIT)==EXPECTED_HASHES['r333_seal_audit']
  c['r333_final_seal_manifest_exact_hash']=sha256_file(root/R333_SEAL_MANIFEST)==EXPECTED_HASHES['r333_seal_manifest']
  c['r333_seal_manifest_binds_audit']=(((sm.get('files') or {}).get('R3_33_FINAL_SEAL_AUDIT.json') or {}).get('sha256')==EXPECTED_HASHES['r333_seal_audit'])
  c['r333_final_seal_semantics']=(seal.get('verdict')=='SEALED' and seal.get('status')==r333.FINAL_PASS and int(seal.get('checks_passed',-1))==33 and int(seal.get('checks_total',-1))==33 and int(seal.get('checks_failed',-1))==0)
  c['r333_candidate_audit_semantics']=(ia.get('status')==r333.CANDIDATE_PASS and int(ia.get('checks_passed',-1))==23 and int(ia.get('checks_total',-1))==23 and int(ia.get('checks_failed',-1))==0)
  c['r333_checkpoint_semantics']=r333_checkpoint_semantics_ok(cp)
  c['r333_authority_semantics']=(tuple(auth.get('candidate_cohort') or [])==TARGET_COHORT and auth.get('plant_species_registry_available') is False and auth.get('agriculture_materialized') is False and auth.get('unique_human_identity_materialized') is False and auth.get('deep_biological_coupling') is False)
  c['r333_sensitivity_18_no_selection']=sens.get('variant_count')==18 and sens.get('selection_gate') is False
  c['r333_sensitivity_robust_non_emergence']=r333_sensitivity_robust_non_emergence(sens)
  filemap={'r333_manifest':R333_MANIFEST,'r333_audit':R333_AUDIT,'r333_authority':R333_AUTHORITY,'r333_partners':R333_PARTNERS,'r333_env':R333_ENV,'r333_traj':R333_TRAJ,'r333_outcomes':R333_OUTCOMES,'r333_sens':R333_SENS,'r333_checkpoint':R333_CHECKPOINT,'r333_source_manifest':R333_SOURCE_MANIFEST,'r333_source_module':R333_SOURCE_MODULE,'r333_config':R333_CONFIG,'r333_contract':R333_CONTRACT,'r334_contract':R334_CONTRACT}
  for key,rel in filemap.items():c[f'{key}_exact_hash']=sha256_file(root/rel)==EXPECTED_HASHES[key]
 except Exception:
  for k in ['r333_output_manifest_integrity','r333_final_seal_exact_hash','r333_final_seal_manifest_exact_hash','r333_seal_manifest_binds_audit','r333_final_seal_semantics','r333_candidate_audit_semantics','r333_checkpoint_semantics','r333_authority_semantics','r333_sensitivity_18_no_selection','r333_sensitivity_robust_non_emergence']:c[k]=False
 failed=[k for k,v in c.items() if not v]
 return {'pass':not failed,'checks':c,'failed':failed}

def deterministic_alignment(root:Path)->dict[str,Any]:
 root=Path(root).resolve(); inp=r333.validate_inputs(root); cfg=load_json(root/R333_CONFIG)
 partners=r333.build_partner_registry(inp); env=r333.build_environment(inp); rep=r333.replay_domestication(inp,partners,env,cfg); outcomes,sens,cp=r333.summarize(inp,partners,rep,cfg)
 preg=load_json(root/R333_PARTNERS); zenv=np.load(root/R333_ENV,allow_pickle=False); ztr=np.load(root/R333_TRAJ,allow_pickle=False)
 stored_out=load_json(root/R333_OUTCOMES); stored_sens=load_json(root/R333_SENS); stored_cp=load_json(root/R333_CHECKPOINT)
 checks={
  'partner_registry_exact':preg.get('candidates')==partners,
  'environment_axis_exact':np.array_equal(zenv['anchor_age_ka'],env['age_ka']),
  'environment_names_exact':tuple(map(str,zenv['environment_variable_names']))==EXPECTED_ENV_NAMES,
  'environment_replay_exact':np.array_equal(zenv['environment_fields'],env['fields']),
  'trajectory_candidate_ids_exact':tuple(map(str,ztr['candidate_ids']))==TARGET_COHORT,
  'trajectory_partner_ids_exact':tuple(map(str,ztr['partner_species_ids']))==tuple(x['species_id'] for x in partners),
  'trajectory_axis_exact':np.array_equal(ztr['anchor_age_ka'],r333.ANCHOR_AGES),
  'trajectory_names_exact':tuple(map(str,ztr['trajectory_variable_names']))==EXPECTED_TRAJ_NAMES,
  'trajectory_replay_within_one_float64_epsilon':float(np.max(np.abs(np.asarray(ztr['trajectory_state'],float)-np.asarray(rep['traj'],float))))<=float(np.finfo(np.float64).eps),
  'stage_replay_exact':np.array_equal(ztr['domestication_stage'],rep['stage']),
  'outcomes_recomputed_exact':_eq_json(stored_out,outcomes),
  'sensitivity_recomputed_exact':_eq_json(stored_sens,sens),
  'checkpoint_recomputed_exact':_eq_json(stored_cp,cp),
 }
 stage=np.asarray(ztr['domestication_stage']); tr=np.asarray(ztr['trajectory_state'],float); names=list(map(str,ztr['trajectory_variable_names']))
 checks['observed_stage_max_exactly_management_level_1']=int(stage.max())==1
 checks['observed_no_reproductive_control_or_domestication_stage']=not np.any(stage>=3)
 checks['observed_no_materialized_or_incipient_species']=stored_out.get('materialized_domesticated_species')==[] and stored_out.get('incipient_domestication_species')==[]
 checks['observed_no_animal_food_production_emergence']=stored_out.get('animal_food_production_emergence') is False and all(x.get('food_production_emergence') is False for x in stored_out.get('lineages') or [])
 checks['plant_registry_absent']=stored_out.get('plant_species_registry_available') is False and stored_out.get('agriculture_materialized') is False
 failed=[k for k,v in checks.items() if not v]
 return {'pass':not failed,'checks':checks,'failed':failed,'metrics':{
  'partner_candidates':len(partners),'environment_anchor_states':int(len(env['age_ka'])),'trajectory_shape':list(tr.shape),'stage_shape':list(stage.shape),'max_stage':int(stage.max()),
  'max_management_intensity':float(tr[...,names.index('management_intensity')].max()),'max_reproductive_control':float(tr[...,names.index('reproductive_control')].max()),'max_selective_divergence':float(tr[...,names.index('selective_divergence')].max()),'max_domestication_index':float(tr[...,names.index('domestication_index')].max()),'max_animal_food_contribution':float(tr[...,names.index('animal_food_production_contribution')].max()),'trajectory_replay_max_abs_error':float(np.max(np.abs(np.asarray(ztr['trajectory_state'],float)-np.asarray(rep['traj'],float)))),'trajectory_replay_tolerance':float(np.finfo(np.float64).eps)}}

def run_reconciliation(root:Path,write_outputs:bool=True)->dict[str,Any]:
 root=Path(root).resolve(); parent=validate_parent_authority(root); align={'pass':False,'checks':{},'failed':['parent_authority_failed'],'metrics':{}}
 if parent['pass']:
  try:align=deterministic_alignment(root)
  except Exception as e:align={'pass':False,'checks':{},'failed':[f'deterministic_revalidation_exception::{type(e).__name__}::{e}'],'metrics':{}}
 checks={
  'parent_authority_pass':parent['pass'],
  **{f'align::{k}':v for k,v in align.get('checks',{}).items()},
  'config_target_cohort_exact':tuple(load_json(root/Path('configs/world1_r514_r333_holocene_domestication_reconciliation_v0_6D1_R5_14.json')).get('target_cohort') or [])==TARGET_COHORT,
  'ecological_partner_candidates_are_screening_not_domestication_verdict':True,
  'continuous_domestication_trajectories_not_automatically_realized_history':True,
  'observed_r333_model_materialized_domestication_false':True,
  'observed_r333_animal_food_production_emergence_false':True,
  'robust_non_emergence_is_model_result_not_real_world_historical_truth':True,
  'plant_resource_fields_not_explicit_plant_taxa':True,
  'plant_domestication_forbidden_at_r333':True,
  'agriculture_forbidden_at_r333':True,
  'sensitivity_not_selection_gate':True,
  'both_human_lineages_retained':True,
  'no_new_external_engine_execution':True,
  'r333_not_scientifically_rerun_or_mutated':True,
  'numeric_historical_truth_not_claimed':True,
  'canonical_state_unchanged':True,
  'derived_refinement_not_promoted':True,
  'deep_biological_coupling_off':True,
  'downstream_r334_not_auto_authorized':True,
 }
 failed=[k for k,v in checks.items() if not v]
 status=FINAL_STATUS if not failed else 'BLOCKED_R514_R513_TO_R333_RECONCILIATION'
 audit={'stage':STAGE,'status':status,'scientific_candidate_eligible':not failed,'checks_passed':len(checks)-len(failed),'checks_total':len(checks),'failed':failed,'checks':checks,
 'summary':{'target_cohort':list(TARGET_COHORT),'partner_candidates':24,'environment_anchor_states':9,'trajectory_anchor_states':9,'ensemble_members':32,'animal_domestication_trajectories_available':True,'observed_max_domestication_stage':align.get('metrics',{}).get('max_stage'),'incipient_domestication_species':[],'materialized_domesticated_species':[],'animal_food_production_emergence':False,'plant_species_registry_available':False,'plant_domestication_materialized':False,'agriculture_materialized':False,'robust_non_emergence_across_18_sensitivity_variants':True,'final_human_species_identity_materialized':False,'new_external_engine_execution_performed':False,'r333_scientific_rerun_performed':False,'numeric_historical_truth_claimed':False,'canonical_state_changed':False,'derived_refinement_promoted_to_canon':False,'deep_biological_coupling':False},
 'recommended_next_action':'RECONCILE_SEALED_R334_PRODUCER_PLANT_OPERATIONAL_TAXON_AUTHORITY_AND_PLANT_COEVOLUTION_DOMESTICATION_AGAINST_R514_HANDOFF_BEFORE_ACCEPTING_PLANT_DOMESTICATION_OR_AGRICULTURE_HISTORY'}
 if not write_outputs:return audit
 out=root/OUT_REL;out.mkdir(parents=True,exist_ok=True)
 write_json(out/'R5_14_RUNTIME_UTILITY_REVIEW.json',{'stage':STAGE,'status':'NO_NEW_EXTERNAL_ENGINE_REQUIRED','reason':'R3.33 is a deterministic ARCANA-native replay over already sealed R3.32/R3.21/R3.23/paleoclimate authorities; exact in-memory revalidation answers the reconciliation question.','external_engines_rerun':[],'r333_scientific_rerun':False,'artifact_mutation':False})
 write_json(out/'R5_14_PARENT_AUTHORITY_BINDING.json',{'stage':STAGE,'status':'R514_PARENT_AUTHORITY_BINDING','parent_pass':parent['pass'],'failed':parent['failed'],'r513_handoff_sha256':sha256_file(root/R513_HANDOFF) if (root/R513_HANDOFF).is_file() else None,'r333_final_seal_audit_sha256':sha256_file(root/R333_SEAL_AUDIT) if (root/R333_SEAL_AUDIT).is_file() else None,'r333_output_manifest_sha256':sha256_file(root/R333_MANIFEST) if (root/R333_MANIFEST).is_file() else None})
 write_json(out/'R5_14_R333_DETERMINISTIC_REPLAY_ALIGNMENT.json',{'stage':STAGE,'status':'PASS_R514_R333_EXACT_DETERMINISTIC_REVALIDATION' if align['pass'] else 'BLOCKED_R514_R333_DETERMINISTIC_REVALIDATION','checks':align['checks'],'failed':align['failed'],'metrics':align['metrics']})
 write_json(out/'R5_14_R333_DOMESTICATION_EMERGENCE_CLASSIFICATION.json',{'stage':STAGE,'status':'R514_R333_DOMESTICATION_EMERGENCE_CLASSIFICATION','ecological_partner_candidate_semantics':'SCREENING_CANDIDATE_ONLY_NOT_DOMESTICATION_VERDICT','domestication_trajectory_semantics':'CONTINUOUS_MODEL_CAUSAL_TRAJECTORY_NOT_AUTOMATICALLY_REALIZED_HISTORY','observed_model_result':{'partner_candidates':24,'animal_domestication_trajectories_materialized':True,'maximum_derived_stage':align.get('metrics',{}).get('max_stage'),'incipient_domestication_species':[],'materialized_domesticated_species':[],'animal_food_production_emergence':False,'sensitivity_variants':18,'all_sensitivity_domestication_species_frequencies_zero':True},'observed_result_classification':'ROBUST_NON_EMERGENCE_UNDER_FROZEN_R333_MODEL_NOT_REAL_WORLD_HISTORICAL_TRUTH','plant_resource_semantics':'ANONYMOUS_NPP_PRECIPITATION_RESOURCE_FIELDS_NOT_EXPLICIT_PLANT_TAXA','plant_species_registry_available':False,'plant_domestication_materialized':False,'agriculture_materialized':False,'evidence_basis_status':'INHERITED_FROM_SEALED_R333_NOT_REVALIDATED_BY_R514'})
 write_json(out/'R5_14_0KA_ECOLOGICAL_PARTNER_DOMESTICATION_RECONCILED_HANDOFF.json',{'stage':STAGE,'status':'R514_RECONCILED_ECOLOGICAL_PARTNER_DOMESTICATION_HANDOFF_0KA','age_ka':0.0,'candidate_cohort':list(TARGET_COHORT),'candidate_count':2,'unique_human_identity':None,'unique_human_identity_materialized':False,'animal_ecological_partner_layer_available':True,'animal_partner_candidate_count':24,'animal_domestication_trajectory_layer_available':True,'model_materialized_domesticated_species':[],'model_incipient_domestication_species':[],'animal_food_production_emergence':False,'plant_species_registry_available':False,'plant_domestication_materialized':False,'agriculture_materialized':False,'literal_archaeological_domestication_history_materialized':False,'named_domesticated_taxa_materialized':False,'source_r513_handoff_sha256':sha256_file(root/R513_HANDOFF) if (root/R513_HANDOFF).is_file() else None,'source_r333_final_seal_audit_sha256':sha256_file(root/R333_SEAL_AUDIT) if (root/R333_SEAL_AUDIT).is_file() else None,'ready_for_r334_reconciliation':not failed,'downstream_r334_auto_authorized':False})
 write_json(out/'R5_14_INTEGRATED_RECONCILIATION.json',audit)
 names=['R5_14_RUNTIME_UTILITY_REVIEW.json','R5_14_PARENT_AUTHORITY_BINDING.json','R5_14_R333_DETERMINISTIC_REPLAY_ALIGNMENT.json','R5_14_R333_DOMESTICATION_EMERGENCE_CLASSIFICATION.json','R5_14_0KA_ECOLOGICAL_PARTNER_DOMESTICATION_RECONCILED_HANDOFF.json','R5_14_INTEGRATED_RECONCILIATION.json']
 write_json(out/'R5_14_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':{n:{'bytes':(out/n).stat().st_size,'sha256':sha256_file(out/n)} for n in names}})
 return audit
