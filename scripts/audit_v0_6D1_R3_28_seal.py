from __future__ import annotations
from pathlib import Path
import sys,json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r328_highres_200ka_to_0 import *

def main(root:Path)->int:
 out=root/'outputs'/'v0_6D1_R3_28';seal=root/'outputs'/'v0_6D1_R3_28_SEAL';checks=[]
 def ck(n,c,d=None):checks.append({'name':n,'pass':bool(c),'detail':d})
 try:inp=validate_inputs(root);cfg=load_json(root/'configs'/'world1_r328_high_resolution_200ka_to_0_v0_6D1_R3_28.json')
 except Exception as e:inp=None;cfg={};ck('parent_and_environment_authorities_validate',False,str(e))
 if inp is not None:ck('parent_and_environment_authorities_validate',True)
 expected={'R3_28_AUDIT.md','R3_28_HIGH_RESOLUTION_REPLAY_AUTHORITY.json','R3_28_CANDIDATE_POPULATION_OUTCOMES.json','R3_28_SENSITIVITY_AND_ROBUSTNESS.json','R3_28_HUMAN_0KA_CHECKPOINT.json','R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz','R3_28_INTEGRATED_AUDIT.json','R3_28_OUTPUT_MANIFEST.json'}
 ck('output_file_set_exact',out.is_dir() and {p.name for p in out.iterdir() if p.is_file()}==expected,sorted(p.name for p in out.iterdir()) if out.is_dir() else None)
 if out.is_dir() and (out/'R3_28_OUTPUT_MANIFEST.json').is_file():
  man=load_json(out/'R3_28_OUTPUT_MANIFEST.json');ok=True
  for n,m in man.get('files',{}).items():
   p=out/n;ok &= p.is_file() and p.stat().st_size==m['bytes'] and sha256_file(p)==m['sha256']
  ck('output_manifest_closure',ok)
 else:ck('output_manifest_closure',False)
 if inp is not None and out.is_dir():
  ia=load_json(out/'R3_28_INTEGRATED_AUDIT.json');au=load_json(out/'R3_28_HIGH_RESOLUTION_REPLAY_AUTHORITY.json');co=load_json(out/'R3_28_CANDIDATE_POPULATION_OUTCOMES.json');se=load_json(out/'R3_28_SENSITIVITY_AND_ROBUSTNESS.json');cp=load_json(out/'R3_28_HUMAN_0KA_CHECKPOINT.json');z=np.load(out/'R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz',allow_pickle=False)
  ck('integrated_audit_all_pass',ia['checks_failed']==0 and ia['checks_passed']==ia['checks_total'],[ia['checks_passed'],ia['checks_total']])
  ck('authority_parent_exact',au['parent']==PARENT_PASS)
  ck('authority_candidates_exact',au['candidate_cohort']==inp['candidates'])
  ck('authority_r318_hashes_exact',all(au['r318_authority'][n]['sha256']==h and sha256_file(inp['r318'][n])==h for n,h in R318_HASHES.items()))
  ck('authority_r320_hashes_exact',all(au['r320_authority'][n]['sha256']==h and sha256_file(inp['r320'][n])==h for n,h in R320_HASHES.items()))
  ck('authority_forcing_semantics',au['recent_forcing_semantics']==cfg['recent_forcing_semantics'] and 'PHASE_INTEGRAL_CONSTRAINED' in au['recent_forcing_semantics'])
  ck('authority_cha2_direct',au['cha2_semantics']=='DIAGNOSTIC_RANKING_NOT_FLOOD_DEPTH')
  ck('authority_no_human_target',au['human_similarity_target'] is False)
  ck('authority_deep_off',au['deep_biological_coupling'] is False)
  keys={'candidate_ids','parent_member_indices','age_ka','state_variable_names','species_summary_variable_names','species_summary','contact_index','admixture_opportunity_cumulative','snapshot_age_ka','snapshot_deme_state','snapshot_active','cha2_age_ka','cha2_deme_state','cha2_active'}
  ck('npz_keys_exact',set(z.files)==keys,sorted(z.files))
  ages=build_time_axis();T=len(ages)
  ck('npz_geometry',z['species_summary'].shape==(EXPECTED_MEMBERS,2,T,8) and z['contact_index'].shape==(EXPECTED_MEMBERS,T) and z['cha2_deme_state'].shape==(EXPECTED_MEMBERS,2,80,MAX_DEMES,7),{'T':T,'species':z['species_summary'].shape,'cha2':z['cha2_deme_state'].shape})
  ck('candidate_order_exact',list(map(str,z['candidate_ids']))==inp['candidates'])
  ck('parent_member_indices_exact',np.array_equal(z['parent_member_indices'],inp['parent_member_indices']),z['parent_member_indices'].tolist())
  ck('time_axis_exact',np.array_equal(z['age_ka'],ages))
  ck('cha2_time_axis_exact',len(z['cha2_age_ka'])==80 and np.allclose(z['cha2_age_ka'],np.arange(14.95,11.0-1e-12,-.05)))
  ck('all_numeric_finite',all(np.isfinite(z[k]).all() for k in ('species_summary','contact_index','admixture_opportunity_cumulative','snapshot_deme_state','cha2_deme_state')))
  ck('population_nonnegative',np.min(z['species_summary'][...,0])>=0 and np.min(z['cha2_deme_state'][...,0])>=0)
  ck('candidate_outcomes_two_unique',len(co['candidates'])==2 and {x['species_id'] for x in co['candidates']}==set(inp['candidates']))
  ck('sensitivity_11',se['variant_count']==11 and len(se['variants'])==11)
  ck('checkpoint_age_0',cp['age_ka']==0.0)
  ck('checkpoint_subset_parent',set(cp['candidate_cohort']).issubset(set(inp['candidates'])),cp['candidate_cohort'])
  ck('checkpoint_count_consistent',cp['candidate_count']==len(cp['candidate_cohort']))
  ck('unique_identity_rule',(cp['unique_human_identity_materialized'] and cp['candidate_count']==1 and cp['unique_human_identity']==cp['candidate_cohort'][0]) or ((not cp['unique_human_identity_materialized']) and cp['unique_human_identity'] is None and cp['candidate_count']!=1),cp)
  # Independent qualification from persisted candidate metrics and frozen thresholds.
  q=cfg['qualification'];re=[]
  for x in co['candidates']:
   base=x['survival_frequency']>=q['survival_frequency_min'] and x['final_population_median']>=q['final_population_median_min'] and x['final_deme_median']>=q['final_deme_median_min'] and x['final_diversity_median']>=q['final_diversity_median_min'] and x['final_adaptive_integration_median']>=q['final_adaptive_integration_median_min'] and x['cha2_population_retention_median']>=q['cha2_population_retention_median_min']
   if base and x['sensitivity_qualification_frequency']>=q['sensitivity_frequency_min']:re.append(x['species_id'])
  ck('checkpoint_qualification_independently_recomputed',re==cp['candidate_cohort'],re)
  # Directly recompute the population-weighted CHA2 hazard from the exact R3.20 grid and persisted 50-y deme states.
  z20=inp['z20'];cha=z['cha2_deme_state'];calc=np.zeros((EXPECTED_MEMBERS,2,80),float)
  for e in range(EXPECTED_MEMBERS):
   for j in range(2):
    for k in range(80):
     pp=cha[e,j,k,:,0].astype(float);den=float(pp.sum())
     if den<=0:continue
     val=0.0
     for d in range(MAX_DEMES):
      if pp[d]<=0:continue
      rr=int(np.clip(round(float(cha[e,j,k,d,1])),0,89));cc=int(round(float(cha[e,j,k,d,2])))%180
      h=.55*float(z20['compound_flood_hazard_index'][k,rr,cc])+.30*float(z20['hydrological_disruption_index'][k,rr,cc])+.15*float(z20['raw_support_loss_fraction'][k,rr,cc]);val+=pp[d]*h
     calc[e,j,k]=val/den
  mask=(z['age_ka']<=14.95)&(z['age_ka']>=11.0);stored=z['species_summary'][:,:,mask,6].astype(float);diff=float(np.max(np.abs(calc-stored)))
  ck('cha2_50y_population_weighted_hazard_recomputed',diff<2e-6,diff)
  ck('cha2_fields_exact_80',np.array_equal(np.asarray(z20['years_before_book']),np.arange(-14950,-10999,50)))
  ck('contact_bounded',np.min(z['contact_index'])>=0 and np.max(z['contact_index'])<=1 and np.min(z['admixture_opportunity_cumulative'])>=0 and np.max(z['admixture_opportunity_cumulative'])<=1)
  ck('no_forced_replacement',cfg['contact_semantics']=='SYMMETRIC_ADMIXTURE_OPPORTUNITY_DIAGNOSTIC_NO_FORCED_REPLACEMENT')
  ck('no_direct_cb_selection',cfg['h3_cb_direct_selection'] is False)
  ck('deep_and_parents_immutable',cfg['deep_biological_coupling'] is False and all(cfg[k] is False for k in ('h0_mutation','cha2_mutation','r323_mutation','r324_mutation','r325_mutation','r326_mutation','r327_mutation')))
  ck('r318_not_misrepresented',cfg['r318_is_direct_high_resolution_timeseries'] is False)
  ck('evidence_multisource',len(au['evidence_basis'])>=5)
 else:
  for n in ['integrated_audit_all_pass','authority_parent_exact','authority_candidates_exact','authority_r318_hashes_exact','authority_r320_hashes_exact','authority_forcing_semantics','authority_cha2_direct','authority_no_human_target','authority_deep_off','npz_keys_exact','npz_geometry','candidate_order_exact','parent_member_indices_exact','time_axis_exact','cha2_time_axis_exact','all_numeric_finite','population_nonnegative','candidate_outcomes_two_unique','sensitivity_11','checkpoint_age_0','checkpoint_subset_parent','checkpoint_count_consistent','unique_identity_rule','checkpoint_qualification_independently_recomputed','cha2_50y_population_weighted_hazard_recomputed','cha2_fields_exact_80','contact_bounded','no_forced_replacement','no_direct_cb_selection','deep_and_parents_immutable','r318_not_misrepresented','evidence_multisource']:ck(n,False)
 failed=[x for x in checks if not x['pass']];status=FINAL_PASS if not failed else 'FAIL_R328_FINAL_SEAL_AUDIT';report={'stage':STAGE,'audit':'FINAL_SINGLE_STAGE_HIGH_RESOLUTION_200KA_TO_0_POPULATION_AND_CHA2_AUTHORITY_CLOSURE','status':status,'verdict':'SEALED' if not failed else 'FAIL_CLOSED','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'input_candidate_lineages':2,'human_0ka_candidate_count':None if failed else cp['candidate_count'],'human_0ka_candidate_cohort':None if failed else cp['candidate_cohort'],'unique_human_identity_materialized':False if failed else cp['unique_human_identity_materialized'],'unique_human_identity':None if failed else cp['unique_human_identity'],'cha2_direct_50y_consumed':True,'human_similarity_target':False,'deep_biological_coupling':False,'next_stage':'POPULATION_MIGRATION_SETTLEMENT_AND_CULTURAL_PRECONDITIONS' if not failed else None},'checks':checks}
 seal.mkdir(parents=True,exist_ok=True);ap=seal/'R3_28_FINAL_SEAL_AUDIT.json';write_json(ap,report);md=seal/'R3_28_FINAL_SEAL_AUDIT.md';md.write_text(f"# R3.28 Final Seal Audit\n\n- Verdict: **{report['verdict']}**\n- Checks: **{report['checks_passed']}/{report['checks_total']}**\n- Status: `{report['status']}`\n",encoding='utf-8');write_json(seal/'R3_28_FINAL_SEAL_MANIFEST.json',{'stage':STAGE,'status':'FINAL_SEAL_MANIFEST' if not failed else 'FAILED_SEAL_MANIFEST','files':{p.name:{'bytes':p.stat().st_size,'sha256':sha256_file(p)} for p in (ap,md)}});print(json.dumps(report,indent=2));return 0 if not failed else 1
if __name__=='__main__':
 root=Path(sys.argv[sys.argv.index('--root')+1]).resolve() if '--root' in sys.argv else ROOT;raise SystemExit(main(root))
