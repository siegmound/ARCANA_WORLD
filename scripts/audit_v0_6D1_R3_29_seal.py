from __future__ import annotations
from pathlib import Path
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r329_population_settlement_culture import *

def main(root:Path)->int:
 out=root/'outputs'/'v0_6D1_R3_29';seal=root/'outputs'/'v0_6D1_R3_29_SEAL';checks=[]
 def ck(n,c,d=None):checks.append({'name':n,'pass':bool(c),'detail':d})
 try:
  inp=validate_inputs(root);cfg=load_json(root/'configs'/'world1_r329_population_settlement_cultural_preconditions_v0_6D1_R3_29.json');ck('parent_authorities_validate',True)
 except Exception as e:inp=None;cfg={};ck('parent_authorities_validate',False,str(e))
 expected={'R3_29_AUDIT.md','R3_29_COMMUNITY_PRECONDITION_AUTHORITY.json','R3_29_COMMUNITY_PRECONDITION_CHECKPOINT.json','R3_29_COMMUNITY_NETWORK_REPLAY.npz','R3_29_INTEGRATED_AUDIT.json','R3_29_LINEAGE_COMMUNITY_OUTCOMES.json','R3_29_OUTPUT_MANIFEST.json','R3_29_SENSITIVITY_AND_ROBUSTNESS.json'}
 ck('output_file_set_exact',out.is_dir() and {p.name for p in out.iterdir() if p.is_file()}==expected,sorted(p.name for p in out.iterdir()) if out.is_dir() else None)
 man=None
 if out.is_dir() and (out/'R3_29_OUTPUT_MANIFEST.json').is_file():
  man=load_json(out/'R3_29_OUTPUT_MANIFEST.json');ok=True
  for n,m in man.get('files',{}).items():
   p=out/n;ok &= p.is_file() and p.stat().st_size==m['bytes'] and sha256_file(p)==m['sha256']
  ck('output_manifest_closure',ok)
 else:ck('output_manifest_closure',False)
 if inp is not None and out.is_dir():
  au=load_json(out/'R3_29_COMMUNITY_PRECONDITION_AUTHORITY.json');ia=load_json(out/'R3_29_INTEGRATED_AUDIT.json');oc=load_json(out/'R3_29_LINEAGE_COMMUNITY_OUTCOMES.json');se=load_json(out/'R3_29_SENSITIVITY_AND_ROBUSTNESS.json');cp=load_json(out/'R3_29_COMMUNITY_PRECONDITION_CHECKPOINT.json');z=np.load(out/'R3_29_COMMUNITY_NETWORK_REPLAY.npz',allow_pickle=False)
  ck('integrated_audit_all_pass',ia['checks_failed']==0 and ia['checks_passed']==ia['checks_total'],[ia['checks_passed'],ia['checks_total']])
  ck('authority_parent_exact',au['parent']==PARENT_PASS)
  ck('authority_candidate_cohort_exact',au['candidate_cohort']==EXPECTED_CANDIDATES)
  ck('authority_time_window_exact',au['time_window_ka']==[50.0,0.0])
  ck('authority_population_proxy_not_census','NOT_LITERAL_CENSUS' in au['population_semantics'])
  ck('authority_preconditions_only','PRECONDITIONS' in au['culture_semantics'] and 'NOT_LANGUAGE' in au['culture_semantics'])
  ck('authority_spatial_anchor_semantics','EXPLICIT_DEME_SNAPSHOT_ANCHORS_ONLY' in au['spatial_semantics'])
  ck('authority_cha2_parent_direct','R328_DIRECT_50Y' in au['cha2_semantics'])
  ck('authority_deep_off',au['deep_biological_coupling'] is False)
  ck('authority_no_human_target',au['human_similarity_target'] is False and au['unique_human_identity_materialized'] is False)
  keys={'candidate_ids','parent_member_indices','age_ka','community_variable_names','community_summary','functional_prior_names','functional_priors','anchor_age_ka','community_anchor_variable_names','community_anchor_state','community_anchor_active'}
  ck('npz_keys_exact',set(z.files)==keys,sorted(z.files))
  age=np.asarray(z['age_ka'],float);X=np.asarray(z['community_summary'],float);A=np.asarray(z['community_anchor_state'],float)
  ck('candidate_order_exact',list(map(str,z['candidate_ids']))==EXPECTED_CANDIDATES)
  ck('parent_member_indices_exact',np.array_equal(z['parent_member_indices'],inp['parent_member_indices']))
  ck('time_window_exact',age[0]==50.0 and age[-1]==0.0 and np.all(np.isin(age,np.asarray(inp['z28']['age_ka'],float))))
  ck('community_geometry',X.shape==(32,2,len(age),10),X.shape)
  ck('anchor_geometry',A.shape[0]==32 and A.shape[1]==2 and A.shape[3]==6 and A.shape[-1]==7,A.shape)
  ck('all_numeric_finite',np.isfinite(X).all() and np.isfinite(A).all())
  ck('community_bounded_0_1',np.min(X)>=0 and np.max(X)<=1,[float(np.min(X)),float(np.max(X))])
  ck('anchor_indices_bounded',np.min(A[...,3:])>=0 and np.max(A[...,3:])<=1)
  # independent deterministic full recomputation from SEALED parents
  rr=run_stage(inp,cfg);maxdiff=float(np.max(np.abs(np.asarray(rr['community_summary'],float)-X)));adiff=float(np.max(np.abs(np.asarray(rr['community_anchor_state'],float)-A)))
  ck('community_timeseries_recomputed',maxdiff<2e-7,maxdiff)
  ck('community_anchors_recomputed',adiff<2e-7,adiff)
  oo,ss=evaluate(inp,cfg,rr)
  ck('outcomes_recomputed_exact',oo==oc)
  ck('sensitivity_recomputed_exact',ss==se)
  ck('sensitivity_11',se['variant_count']==11 and len(se['variants'])==11)
  ck('checkpoint_age_0',cp['age_ka']==0.0)
  ck('checkpoint_cohort_exact',cp['candidate_cohort']==oc['community_precondition_cohort'] and cp['candidate_count']==len(cp['candidate_cohort']),cp['candidate_cohort'])
  ck('baseline_capable_lineages_retained',cp['candidate_cohort']==[x['species_id'] for x in oc['candidates'] if x['baseline_qualified']],cp['candidate_cohort'])
  ck('robust_priority_is_diagnostic_subset',set(oc['robust_priority_cohort']).issubset(set(cp['candidate_cohort'])),oc['robust_priority_cohort'])
  ck('checkpoint_no_unique_identity',cp['unique_human_identity_materialized'] is False and cp['unique_human_identity'] is None)
  ck('no_culture_identity_artifacts',all(cp[k] is False for k in ('language_materialized','religion_materialized','agriculture_materialized','city_state_materialized')))
  ck('no_absolute_census_or_camp_counts',cfg['absolute_census_calibration_materialized'] is False and cfg['absolute_camp_headcounts_materialized'] is False)
  ck('no_parent_mutation',all(cfg[k] is False for k in ('h0_mutation','cha2_mutation','r323_mutation','r328_mutation')))
  ck('deep_off_and_no_human_similarity',cfg['deep_biological_coupling'] is False and cfg['human_similarity_target'] is False)
  ck('evidence_multisource',len(au['evidence_basis'])>=5)
 else:
  for n in ['integrated_audit_all_pass','authority_parent_exact','authority_candidate_cohort_exact','authority_time_window_exact','authority_population_proxy_not_census','authority_preconditions_only','authority_spatial_anchor_semantics','authority_cha2_parent_direct','authority_deep_off','authority_no_human_target','npz_keys_exact','candidate_order_exact','parent_member_indices_exact','time_window_exact','community_geometry','anchor_geometry','all_numeric_finite','community_bounded_0_1','anchor_indices_bounded','community_timeseries_recomputed','community_anchors_recomputed','outcomes_recomputed_exact','sensitivity_recomputed_exact','sensitivity_11','checkpoint_age_0','checkpoint_cohort_exact','baseline_capable_lineages_retained','robust_priority_is_diagnostic_subset','checkpoint_no_unique_identity','no_culture_identity_artifacts','no_absolute_census_or_camp_counts','no_parent_mutation','deep_off_and_no_human_similarity','evidence_multisource']:ck(n,False)
 failed=[x for x in checks if not x['pass']];status=FINAL_PASS if not failed else 'FAIL_R329_FINAL_SEAL_AUDIT';report={'stage':STAGE,'audit':'FINAL_SINGLE_STAGE_POPULATION_MOBILITY_SETTLEMENT_AND_CULTURAL_PRECONDITION_AUTHORITY_CLOSURE','status':status,'verdict':'SEALED' if not failed else 'FAIL_CLOSED','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'input_candidate_lineages':2,'community_precondition_count':None if failed else cp['candidate_count'],'community_precondition_cohort':None if failed else cp['candidate_cohort'],'robust_priority_cohort':None if failed else oc['robust_priority_cohort'],'unique_human_identity_materialized':False,'language_religion_agriculture_city_materialized':False,'absolute_census_materialized':False,'deep_biological_coupling':False,'next_stage':'CENSUS_CALIBRATION_GROUP_ABM_AND_LATE_PLEISTOCENE_COMMUNITY_HISTORY' if not failed else None},'checks':checks}
 seal.mkdir(parents=True,exist_ok=True);ap=seal/'R3_29_FINAL_SEAL_AUDIT.json';write_json(ap,report);md=seal/'R3_29_FINAL_SEAL_AUDIT.md';md.write_text(f"# R3.29 Final Seal Audit\n\n- Verdict: **{report['verdict']}**\n- Checks: **{report['checks_passed']}/{report['checks_total']}**\n- Status: `{report['status']}`\n",encoding='utf-8');write_json(seal/'R3_29_FINAL_SEAL_MANIFEST.json',{'stage':STAGE,'status':'FINAL_SEAL_MANIFEST' if not failed else 'FAILED_SEAL_MANIFEST','files':{p.name:{'bytes':p.stat().st_size,'sha256':sha256_file(p)} for p in (ap,md)}});print(json.dumps(report,indent=2));return 0 if not failed else 1
if __name__=='__main__':
 root=Path(sys.argv[sys.argv.index('--root')+1]).resolve() if '--root' in sys.argv else ROOT;raise SystemExit(main(root))
