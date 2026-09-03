from __future__ import annotations
from pathlib import Path
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r327_hominin_macro_replay import *
def main(root:Path)->int:
 out=root/'outputs'/'v0_6D1_R3_27';seal=root/'outputs'/'v0_6D1_R3_27_SEAL';checks=[]
 def ck(n,c,d=None):checks.append({'name':n,'pass':bool(c),'detail':d})
 try:inp=validate_inputs(root);cfg=load_json(root/'configs'/'world1_r327_hominin_macro_replay_to_200ka_v0_6D1_R3_27.json')
 except Exception as e:inp=None;cfg={};ck('parent_authorities_validate',False,str(e))
 if inp is not None:ck('parent_authorities_validate',True)
 expected={'R3_27_AUDIT.md','R3_27_MACRO_REPLAY_AUTHORITY.json','R3_27_CANDIDATE_OUTCOMES.json','R3_27_SENSITIVITY_AND_ROBUSTNESS.json','R3_27_HUMAN_200KA_CHECKPOINT.json','R3_27_MACRO_REPLAY_TRAJECTORIES.npz','R3_27_INTEGRATED_AUDIT.json','R3_27_OUTPUT_MANIFEST.json'}
 ck('output_file_set_exact',out.is_dir() and {p.name for p in out.iterdir() if p.is_file()}==expected,sorted(p.name for p in out.iterdir()) if out.is_dir() else None)
 if out.is_dir() and (out/'R3_27_OUTPUT_MANIFEST.json').is_file():
  man=load_json(out/'R3_27_OUTPUT_MANIFEST.json');ok=True
  for n,m in man.get('files',{}).items():
   p=out/n;ok &= p.is_file() and p.stat().st_size==m['bytes'] and sha256_file(p)==m['sha256']
  ck('output_manifest_closure',ok)
 else:ck('output_manifest_closure',False)
 if inp is not None and out.is_dir():
  ia=load_json(out/'R3_27_INTEGRATED_AUDIT.json');au=load_json(out/'R3_27_MACRO_REPLAY_AUTHORITY.json');co=load_json(out/'R3_27_CANDIDATE_OUTCOMES.json');se=load_json(out/'R3_27_SENSITIVITY_AND_ROBUSTNESS.json');cp=load_json(out/'R3_27_HUMAN_200KA_CHECKPOINT.json');z=np.load(out/'R3_27_MACRO_REPLAY_TRAJECTORIES.npz',allow_pickle=False)
  ck('integrated_audit_all_pass',ia['checks_failed']==0 and ia['checks_passed']==ia['checks_total'],[ia['checks_passed'],ia['checks_total']])
  ck('authority_parent_exact',au['parent']==PARENT_PASS)
  ck('authority_window_exact',au['window']=={'start_age_ma':3.0,'end_age_ma':.2,'macrostep_kyr':20.0})
  ck('authority_no_human_bodyplan_target',au['human_similarity_target'] is False and au['unique_human_body_plan_target'] is False)
  ck('authority_deep_off',au['deep_biological_coupling'] is False)
  ck('authority_common_forcing',au['forcing_semantics']=='COMMON_PER_REPLICATE_ACROSS_ALL_CANDIDATES')
  ck('authority_fork_does_not_overwrite_h0','DOES_NOT_OVERWRITE_H0' in au['fork_semantics'])
  ck('authority_h3_no_rescale','NO_LINEAGE_RESCALE' in au['h3_semantics'] and 'NO_DIRECT_CB_SELECTION' in au['h3_semantics'])
  ck('npz_keys_exact',set(z.files)=={'candidate_ids','age_ma','forcing_regime','variable_names','state','environmental_stress','corridor_connectivity','bottleneck_multiplier','variability_index'})
  ck('npz_geometry',z['state'].shape==(96,6,141,8) and z['environmental_stress'].shape==(96,141))
  ck('candidate_order_exact',list(map(str,z['candidate_ids']))==inp['candidates'])
  ck('time_axis_exact',abs(float(z['age_ma'][0])-3)<1e-12 and abs(float(z['age_ma'][-1])-.2)<1e-12 and len(z['age_ma'])==141)
  ck('all_numeric_finite',np.isfinite(z['state']).all() and np.isfinite(z['environmental_stress']).all())
  ck('population_nonnegative',np.min(z['state'][:,:,:,0])>=0)
  ck('bounded_indices',np.min(z['state'][:,:,:,2:])>=0 and np.max(z['state'][:,:,:,2:])<=1)
  ck('outcomes_six_unique',len(co['candidates'])==6 and len({x['species_id'] for x in co['candidates']})==6)
  ck('sensitivity_10_variants',se['variant_count']==10 and len(se['variants'])==10)
  ck('checkpoint_age_200ka',cp['age_ka']==200.0)
  ck('checkpoint_candidate_count_consistent',cp['candidate_count']==len(cp['candidate_cohort']) and cp['candidate_count']>=1)
  ck('checkpoint_subset_parent',set(cp['candidate_cohort']).issubset(set(inp['candidates'])),cp['candidate_cohort'])
  ck('checkpoint_not_final_identity',cp['unique_human_identity_materialized'] is False and 'NOT_FINAL_HUMAN_SPECIES_IDENTITY' in cp['interpretation'])
  # independent qualification recompute from persisted outcome metrics and frozen thresholds
  q=cfg['qualification'];re=[]
  for x in co['candidates']:
   base=x['survival_frequency']>=q['survival_frequency_min'] and x['final_ne_median']>=q['final_ne_median_min'] and x['bottleneck_ne_q10']>=q['bottleneck_ne_q10_min'] and x['final_deme_median']>=q['final_deme_median_min'] and x['adaptive_integration_median']>=q['adaptive_integration_median_min'] and x['structured_stem_frequency']>=q['structured_stem_frequency_min']
   if base and x['sensitivity_qualification_frequency']>=q['sensitivity_qualification_frequency_min']:re.append(x['species_id'])
  ck('checkpoint_qualification_independently_recomputed',set(re)==set(cp['candidate_cohort']),re)
  ck('no_direct_cb_selection',cfg['h3_cb_direct_selection'] is False)
  ck('deep_h0_cha2_parents_immutable',cfg['deep_biological_coupling'] is False and all(cfg[k] is False for k in ('h0_mutation','cha2_mutation','r323_mutation','r324_mutation','r325_mutation','r326_mutation')))
  ck('evidence_multisource',len(au['evidence_basis'])>=5)
 else:
  for n in ['integrated_audit_all_pass','authority_parent_exact','authority_window_exact','authority_no_human_bodyplan_target','authority_deep_off','authority_common_forcing','authority_fork_does_not_overwrite_h0','authority_h3_no_rescale','npz_keys_exact','npz_geometry','candidate_order_exact','time_axis_exact','all_numeric_finite','population_nonnegative','bounded_indices','outcomes_six_unique','sensitivity_10_variants','checkpoint_age_200ka','checkpoint_candidate_count_consistent','checkpoint_subset_parent','checkpoint_not_final_identity','checkpoint_qualification_independently_recomputed','no_direct_cb_selection','deep_h0_cha2_parents_immutable','evidence_multisource']:ck(n,False)
 failed=[x for x in checks if not x['pass']];report={'stage':STAGE,'audit':'FINAL_SINGLE_STAGE_HOMININ_MACRO_REPLAY_TO_200KA_AUTHORITY_CLOSURE','status':FINAL_PASS if not failed else 'FAIL_R327_FINAL_SEAL_AUDIT','verdict':'SEALED' if not failed else 'FAIL_CLOSED','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'input_candidate_lineages':6,'human_200ka_candidate_count':None if failed else cp['candidate_count'],'human_200ka_candidate_cohort':None if failed else cp['candidate_cohort'],'unique_human_identity_materialized':False,'human_similarity_target':False,'deep_biological_coupling':False,'next_stage':'HIGH_RESOLUTION_200KA_TO_0_REPLAY'},'checks':checks}
 seal.mkdir(parents=True,exist_ok=True);ap=seal/'R3_27_FINAL_SEAL_AUDIT.json';write_json(ap,report);md=seal/'R3_27_FINAL_SEAL_AUDIT.md';md.write_text(f"# R3.27 Final Seal Audit\n\n- Verdict: **{report['verdict']}**\n- Checks: **{report['checks_passed']}/{report['checks_total']}**\n- Status: `{report['status']}`\n",encoding='utf-8');write_json(seal/'R3_27_FINAL_SEAL_MANIFEST.json',{'stage':STAGE,'status':'FINAL_SEAL_MANIFEST' if not failed else 'FAILED_SEAL_MANIFEST','files':{p.name:{'bytes':p.stat().st_size,'sha256':sha256_file(p)} for p in (ap,md)}});print(json.dumps(report,indent=2));return 0 if not failed else 1
if __name__=='__main__':
 root=Path(sys.argv[sys.argv.index('--root')+1]).resolve() if '--root' in sys.argv else ROOT;raise SystemExit(main(root))
