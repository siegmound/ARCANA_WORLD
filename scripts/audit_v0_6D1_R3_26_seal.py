from __future__ import annotations
from pathlib import Path
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r326_h3_quant_genetics_bridge import *

def main(root:Path)->int:
 out=root/'outputs'/'v0_6D1_R3_26';seal=root/'outputs'/'v0_6D1_R3_26_SEAL';checks=[]
 def ck(n,c,d=None):checks.append({'name':n,'pass':bool(c),'detail':d})
 try:inp=validate_inputs(root);cfg=load_json(root/'configs'/'world1_r326_h3_quant_genetics_bridge_v0_6D1_R3_26.json')
 except Exception as e:inp=None;cfg={};ck('parent_and_authorities_validate',False,str(e))
 if inp is not None:ck('parent_and_authorities_validate',True)
 expected={'R3_26_AUDIT.md','R3_26_H3_CANONICAL_BRIDGE_AUTHORITY.json','R3_26_H3_NEUTRAL_REFERENCE_VALIDATION.json','R3_26_H3_REPRODUCTION_KERNEL_VALIDATION.json','R3_26_H3_RARE_TAIL_EXPECTATION_TABLE.json','R3_26_H3_CANDIDATE_BRIDGE_DOSSIERS.json','R3_26_H3_CHARACTER_REGRESSION_FIXTURE.json','R3_26_H3_DIAGNOSTIC_ARRAYS.npz','R3_26_INTEGRATED_AUDIT.json','R3_26_OUTPUT_MANIFEST.json'}
 ck('output_file_set_exact',out.is_dir() and {p.name for p in out.iterdir() if p.is_file()}==expected,sorted(p.name for p in out.iterdir() if p.is_file()) if out.is_dir() else None)
 if out.is_dir() and (out/'R3_26_OUTPUT_MANIFEST.json').is_file():
  man=load_json(out/'R3_26_OUTPUT_MANIFEST.json');ok=True
  for n,m in man.get('files',{}).items():
   p=out/n;ok &= p.is_file() and p.stat().st_size==m.get('bytes') and sha256_file(p)==m.get('sha256')
  ck('output_manifest_closure',ok and man.get('stage')==STAGE)
 else:ck('output_manifest_closure',False)
 if inp is not None and out.is_dir():
  ia=load_json(out/'R3_26_INTEGRATED_AUDIT.json');auth=load_json(out/'R3_26_H3_CANONICAL_BRIDGE_AUTHORITY.json');neu=load_json(out/'R3_26_H3_NEUTRAL_REFERENCE_VALIDATION.json')['validation'];rep=load_json(out/'R3_26_H3_REPRODUCTION_KERNEL_VALIDATION.json')['validation'];rare=load_json(out/'R3_26_H3_RARE_TAIL_EXPECTATION_TABLE.json');dos=load_json(out/'R3_26_H3_CANDIDATE_BRIDGE_DOSSIERS.json');mc=load_json(out/'R3_26_H3_CHARACTER_REGRESSION_FIXTURE.json')['MC'];z=np.load(out/'R3_26_H3_DIAGNOSTIC_ARRAYS.npz',allow_pickle=False)
  ck('integrated_audit_all_pass',ia.get('checks_failed')==0 and ia.get('checks_passed')==ia.get('checks_total'),[ia.get('checks_passed'),ia.get('checks_total')])
  ck('canonical_formula_exact',auth['formula']['formula']=='Z_H = sqrt(0.75)*Z_inf + sqrt(0.15)*U_R + sqrt(0.10)*epsilon_mar')
  ck('canonical_rho_exact',abs(float(auth['formula']['rho_Zinf_ZR'])-.35)<1e-15)
  ck('cb_downstream_only',auth.get('cb_semantics')=='DOWNSTREAM_DIAGNOSTIC_ONLY')
  ck('no_lineage_rescale',auth.get('hard_ceiling_policy')=='SAME_RATIFIED_REFERENCE_LAW_NO_LINEAGE_RESCALE')
  ck('neutral_reference_geometry',neu.get('n')==1_000_000 and len(neu.get('observed_cb_counts',{}))==12)
  ck('neutral_ZH_reference',abs(neu['mean']['Z_H'])<.004 and abs(neu['std']['Z_H']-1)<.004,{'mean':neu['mean']['Z_H'],'std':neu['std']['Z_H']})
  ck('neutral_correlation_structure',abs(neu['corr']['Z_inf__Z_R']-.35)<.004 and abs(neu['corr']['Z_inf__U_R'])<.004)
  ck('reproduction_upstream_only',rep.get('offspring_from_upstream_latents_only') is True and rep.get('parental_CB_label_input') is False)
  ck('reproduction_parent_child_ZH',abs(rep['corr_child_mother_ZH']-.45)<.006 and abs(rep['corr_child_father_ZH']-.45)<.006,rep)
  ck('epsilon_not_directly_inherited',rep.get('epsilon_mar_inherited_directly') is False)
  rows=dos.get('candidates',[]);ck('six_candidates_exact',[x['species_id'] for x in rows]==inp['candidates'])
  ck('all_six_retained',len(rows)==6 and all(x['h3_bridge_compatible'] for x in rows))
  ck('candidate_hard_distribution_unshifted',all(x['h3_hard_ceiling_distribution_shift']==0 and not x['cb_distribution_rescaled_for_lineage'] for x in rows))
  ck('candidate_realization_support_separate',all('DOES_NOT_MODIFY_ZH_OR_J_HARD' in x['realization_support_interpretation'] for x in rows))
  ck('no_human_identity_claim',all(x['human_identity_claim'] is None for x in rows))
  ck('rare_tail_expectation_not_person_events',rare.get('semantics')=='EXPECTATIONS_ONLY_NOT_FRACTIONAL_PERSON_EVENTS')
  ck('rare_tail_billion_cb12',abs(rare['rows'][-1]['expected_CB12_compatible']-43.98)<1e-9)
  ck('mc_character_fixture_only',mc.get('use')=='REGRESSION_FIXTURE_ONLY' and mc.get('diagnostic_CB')==12)
  ck('mc_mapping_value',abs(mc['mapped_J_hard_TW']-133.59)<.02,mc['mapped_J_hard_TW'])
  ck('diagnostic_npz_keys_exact',set(z.files)=={'mapping_ZH','mapping_J_lower_W','cb_reference_probabilities','candidate_ids'})
  ck('diagnostic_candidate_order_exact',list(map(str,z['candidate_ids']))==inp['candidates'])
  ck('mapping_nodes_recompute_exact',np.allclose(z['mapping_ZH'],np.asarray([x['Z_H'] for x in inp['mapping']['nodes']],float),rtol=0,atol=0) and np.allclose(z['mapping_J_lower_W'],np.asarray([x['J_lower_W'] for x in inp['mapping']['nodes']],float),rtol=0,atol=0))
  ck('reference_probs_exact',np.allclose(z['cb_reference_probabilities'],np.asarray([x['prob'] for x in inp['cb']],float),rtol=0,atol=0))
  # independent algebra recheck on fixed fixture
  zi=np.array([-1.2,0.,.7,2.1]);ur=np.array([.4,-.5,1.3,-.7]);ep=np.array([.2,.1,-1.1,.9]);zr=zr_from_latents(zi,ur);ur2=ur_from_zr(zi,zr);zh=h3_from_latents(zi,ur,ep)
  ck('h3_algebra_roundtrip',np.max(np.abs(ur-ur2))<1e-15,float(np.max(np.abs(ur-ur2))))
  ck('h3_variance_weight_identity',abs(W_INF**2+W_UR**2+W_EPS**2-1)<1e-15)
  mapper=hard_ceiling_mapper(inp['mapping']);grid=np.linspace(-5,6,10001);jg=mapper(grid);ck('continuous_mapping_strict_monotone',np.all(np.diff(jg)>0))
  ck('deep_and_parent_immutable',cfg.get('deep_biological_coupling') is False and all(cfg.get(k) is False for k in ('h0_mutation','cha2_mutation','r323_mutation','r324_mutation','r325_mutation')))
  ck('human_200ka_not_materialized',ia['summary'].get('human_200ka_materialized') is False)
 else:
  for n in ['integrated_audit_all_pass','canonical_formula_exact','canonical_rho_exact','cb_downstream_only','no_lineage_rescale','neutral_reference_geometry','neutral_ZH_reference','neutral_correlation_structure','reproduction_upstream_only','reproduction_parent_child_ZH','epsilon_not_directly_inherited','six_candidates_exact','all_six_retained','candidate_hard_distribution_unshifted','candidate_realization_support_separate','no_human_identity_claim','rare_tail_expectation_not_person_events','rare_tail_billion_cb12','mc_character_fixture_only','mc_mapping_value','diagnostic_npz_keys_exact','diagnostic_candidate_order_exact','mapping_nodes_recompute_exact','reference_probs_exact','h3_algebra_roundtrip','h3_variance_weight_identity','continuous_mapping_strict_monotone','deep_and_parent_immutable','human_200ka_not_materialized']:ck(n,False)
 failed=[x for x in checks if not x['pass']];report={'stage':STAGE,'audit':'FINAL_SINGLE_STAGE_H3_QUANT_GENETICS_BRIDGE_AUTHORITY_CLOSURE','status':FINAL_PASS if not failed else 'FAIL_R326_FINAL_SEAL_AUDIT','verdict':'SEALED' if not failed else 'FAIL_CLOSED','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'h3_candidate_lineages':6,'h3_bridge_compatible_lineages':6 if not failed else None,'direct_cb_heredity':False,'human_similarity_target':False,'deep_biological_coupling':False,'human_200ka_materialized':False,'next_stage':'HOMININ_MACRO_EVOLUTION_REPLAY_TO_200KA'},'checks':checks}
 seal.mkdir(parents=True,exist_ok=True);ap=seal/'R3_26_FINAL_SEAL_AUDIT.json';write_json(ap,report);md=seal/'R3_26_FINAL_SEAL_AUDIT.md';md.write_text(f"# R3.26 Final Seal Audit\n\n- Verdict: **{report['verdict']}**\n- Checks: **{report['checks_passed']}/{report['checks_total']}**\n- Status: `{report['status']}`\n",encoding='utf-8');write_json(seal/'R3_26_FINAL_SEAL_MANIFEST.json',{'stage':STAGE,'status':'FINAL_SEAL_MANIFEST' if not failed else 'FAILED_SEAL_MANIFEST','files':{p.name:{'bytes':p.stat().st_size,'sha256':sha256_file(p)} for p in (ap,md)}});print(json.dumps(report,indent=2));return 0 if not failed else 1
if __name__=='__main__':
 root=Path(sys.argv[sys.argv.index('--root')+1]).resolve() if '--root' in sys.argv else ROOT;raise SystemExit(main(root))
