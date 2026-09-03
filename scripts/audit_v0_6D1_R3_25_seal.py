from __future__ import annotations
from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from arcana_worldsim.scientific_engines.r325_h2_detailed_biology import *
from arcana_worldsim.scientific_engines.r325_h2_detailed_biology import _module_ensemble, _hypothesis_ensemble, _select_metrics, _consensus_order
PASS='PASS_R325_H2_DETAILED_CANDIDATE_BIOLOGY_EMBODIMENT_FEASIBILITY_AND_H3_PRIORITY_COHORT_SEALED'
def sha(p):return sha256_file(p)
def js(p):return load_json(p)
def main(root:Path)->int:
 out=root/'outputs'/'v0_6D1_R3_25';seal=root/'outputs'/'v0_6D1_R3_25_SEAL';checks=[]
 def ck(n,c,d=None):checks.append({'name':n,'pass':bool(c),'detail':d})
 try: inp=validate_inputs(root)
 except Exception as e: inp=None;ck('parent_authorities_validate',False,str(e))
 if inp is not None: ck('parent_authorities_validate',True)
 expected={'R3_25_AUDIT.md','R3_25_H2_CANDIDATE_DOSSIERS.json','R3_25_H2_DETAILED_BIOLOGY_CRITERIA_AUTHORITY.json','R3_25_H2_DIAGNOSTIC_ARRAYS.npz','R3_25_H2_SENSITIVITY_AND_ROBUSTNESS.json','R3_25_H3_PRIORITY_COHORT.json','R3_25_INTEGRATED_AUDIT.json','R3_25_OUTPUT_MANIFEST.json'}
 ck('output_file_set_exact',out.is_dir() and {p.name for p in out.iterdir() if p.is_file()}==expected,sorted(p.name for p in out.iterdir() if p.is_file()) if out.is_dir() else None)
 if out.is_dir() and (out/'R3_25_OUTPUT_MANIFEST.json').is_file():
  man=js(out/'R3_25_OUTPUT_MANIFEST.json');ok=True
  for n,m in man.get('files',{}).items():
   p=out/n;ok &= p.is_file() and p.stat().st_size==m.get('bytes') and sha(p)==m.get('sha256')
  ck('output_manifest_closure',ok and man.get('stage')==STAGE)
 else: ck('output_manifest_closure',False)
 if inp is not None and out.is_dir():
  crit=js(out/'R3_25_H2_DETAILED_BIOLOGY_CRITERIA_AUTHORITY.json');dos=js(out/'R3_25_H2_CANDIDATE_DOSSIERS.json');coh=js(out/'R3_25_H3_PRIORITY_COHORT.json');sens=js(out/'R3_25_H2_SENSITIVITY_AND_ROBUSTNESS.json');ia=js(out/'R3_25_INTEGRATED_AUDIT.json');z=np.load(out/'R3_25_H2_DIAGNOSTIC_ARRAYS.npz',allow_pickle=False)
  ck('integrated_audit_29_of_29',ia.get('checks_passed')==29 and ia.get('checks_total')==29 and ia.get('checks_failed')==0)
  ck('criteria_no_human_or_bodyplan_target',crit.get('human_similarity_target') is False and crit.get('missing_anatomy_rule')=='NO_UNIQUE_BODY_PLAN_OR_ORGAN_GEOMETRY_INFERRED')
  ck('criteria_modules_exact',crit.get('modules')==MODULES)
  ck('criteria_hypotheses_exact',crit.get('embodiment_hypotheses')==HYPOTHESES)
  ck('criteria_reptile_evidence',all(x in crit.get('evidence_basis',{}) for x in ['REPTILE_LEARNING_2021','REPTILE_COGNITION_2024','REPTILE_SOCIALITY_2017','REPTILE_LIFE_HISTORY_2005']))
  rows=dos.get('candidates',[]);ids=[x['species_id'] for x in rows];ck('dossiers_12_unique',len(rows)==12 and len(set(ids))==12 and ids==inp['candidates'])
  ck('all_dossier_guild4_current_outcome',all(x['guild_id']==4 for x in rows))
  ck('genetic_background_semantics',all('NOT_FUNCTIONAL_VA_OR_GCOV' in x['reduced_genetic_background']['semantic_warning'] for x in rows))
  priority=coh.get('priority_cohort',[]);ck('priority_6_unique_subset',len(priority)==6 and len(set(priority))==6 and set(priority).issubset(set(ids)),priority)
  ck('priority_not_human_identity',coh.get('absolute_human_ready_claim') is False and 'NOT_HUMAN_IDENTITY' in coh.get('interpretation',''))
  ck('sensitivity_14',sens.get('variant_count')==14 and len(sens.get('variants',[]))==14)
  ck('sensitivity_cohorts_6_unique',all(len(v['priority_cohort'])==6 and len(set(v['priority_cohort']))==6 for v in sens['variants']))
  ck('npz_keys_exact',set(z.files)=={'candidate_ids','module_names','embodiment_hypothesis_names','rate_regime','module_percentile_ensemble','embodiment_hypothesis_ensemble'})
  ck('npz_geometry',z['module_percentile_ensemble'].shape==(96,12,8) and z['embodiment_hypothesis_ensemble'].shape==(96,12,6))
  ck('npz_orders_exact',list(map(str,z['candidate_ids']))==inp['candidates'] and list(map(str,z['module_names']))==list(MODULES) and list(map(str,z['embodiment_hypothesis_names']))==list(HYPOTHESES))
  # independent recompute from parent R3.23
  pz=inp['pz'];_,M,_=_module_ensemble(np.asarray(pz['species_mean_z_ensemble'],float),list(map(str,pz['trait_ids'])));hn,H=_hypothesis_ensemble(M,list(MODULES));si={s:i for i,s in enumerate(map(str,pz['species_ids']))};ix=[si[s] for s in inp['candidates']];Mc=M[:,ix,:];Hc=H[:,ix,:]
  ck('module_arrays_recomputed_exact',np.max(np.abs(Mc-z['module_percentile_ensemble']))<=1e-15,float(np.max(np.abs(Mc-z['module_percentile_ensemble']))))
  ck('hypothesis_arrays_recomputed_exact',np.max(np.abs(Hc-z['embodiment_hypothesis_ensemble']))<=1e-15,float(np.max(np.abs(Hc-z['embodiment_hypothesis_ensemble']))))
  h1rows={str(r['species_id']):r for r in inp['short']['candidates']};h1f=np.asarray([float(h1rows[s]['selection_frequency_across_sensitivity_variants']) for s in inp['candidates']]);names,metrics=_select_metrics(Mc,Hc,np.asarray(pz['rate_regime']).astype(str),h1f);order,*_=_consensus_order(inp['candidates'],metrics)
  ck('priority_order_independently_recomputed',order==coh.get('priority_order'),order)
  ck('priority_cohort_independently_recomputed',order[:6]==priority,order[:6])
  # independent sensitivity rebuild
  rr=np.asarray(pz['rate_regime']).astype(str);variants=[('BASELINE',order[:6])]
  for mi,mn in enumerate(MODULES):
   n,m=_select_metrics(Mc,Hc,rr,h1f,module_subset=[i for i in range(8) if i!=mi]);o,*_=_consensus_order(inp['candidates'],m);variants.append((f'LEAVE_ONE_MODULE_OUT::{mn}',o[:6]))
  for rg in sorted(set(rr.tolist())):
   n,m=_select_metrics(Mc,Hc,rr,h1f,member_mask=(rr==rg));o,*_=_consensus_order(inp['candidates'],m);variants.append((f'RATE_REGIME_ONLY::{rg}',o[:6]))
  n,m=_select_metrics(Mc,Hc,rr,h1f,include_h1=False);o,*_=_consensus_order(inp['candidates'],m);variants.append(('NO_H1_SENSITIVITY_DIAGNOSTIC',o[:6]));om={k:v.copy() for k,v in metrics.items() if k not in {'embodiment_hypothesis_breadth','embodiment_worst_regime_floor'}};om['best_embodiment_hypothesis']=np.max(np.median(Hc,axis=0),axis=1);o,*_=_consensus_order(inp['candidates'],om);variants.append(('EMBODIMENT_ASSUMPTION::BEST_AVAILABLE_HYPOTHESIS',o[:6]))
  obs=[(v['variant'],v['priority_cohort']) for v in sens['variants']];ck('sensitivity_independently_recomputed',obs==variants)
  ck('deep_h0_cha2_r323_r324_immutable',crit.get('deep_biological_coupling') is False and crit.get('h0_mutated') is False and crit.get('cha2_mutated') is False and crit.get('r323_mutated') is False and crit.get('r324_mutated') is False)
  ck('no_functional_va_gcov_materialized',all('functional_va' not in k.lower() and 'functional_gcov' not in k.lower() for k in z.files))
 else:
  for n in ['integrated_audit_29_of_29','criteria_no_human_or_bodyplan_target','criteria_modules_exact','criteria_hypotheses_exact','criteria_reptile_evidence','dossiers_12_unique','all_dossier_guild4_current_outcome','genetic_background_semantics','priority_6_unique_subset','priority_not_human_identity','sensitivity_14','sensitivity_cohorts_6_unique','npz_keys_exact','npz_geometry','npz_orders_exact','module_arrays_recomputed_exact','hypothesis_arrays_recomputed_exact','priority_order_independently_recomputed','priority_cohort_independently_recomputed','sensitivity_independently_recomputed','deep_h0_cha2_r323_r324_immutable','no_functional_va_gcov_materialized']:ck(n,False)
 failed=[x for x in checks if not x['pass']];report={'stage':STAGE,'audit':'FINAL_SINGLE_STAGE_H2_DETAILED_BIOLOGY_AND_H3_PRIORITY_AUTHORITY_CLOSURE','status':PASS if not failed else 'FAIL_R325_FINAL_SEAL_AUDIT','verdict':'SEALED' if not failed else 'FAIL_CLOSED','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'h1_candidates':12,'h3_priority_cohort_size':6,'priority_cohort':priority if 'priority' in locals() else [],'human_similarity_target':False,'unique_human_body_plan_target':False,'deep_biological_coupling':False,'h0_mutated':False,'cha2_mutated':False,'r323_mutated':False,'r324_mutated':False},'checks':checks}
 seal.mkdir(parents=True,exist_ok=True);ap=seal/'R3_25_FINAL_SEAL_AUDIT.json';write_json(ap,report);md=seal/'R3_25_FINAL_SEAL_AUDIT.md';md.write_text(f"# R3.25 Final Seal Audit\n\n- Verdict: **{report['verdict']}**\n- Checks: **{report['checks_passed']}/{report['checks_total']}**\n- Status: `{report['status']}`\n",encoding='utf-8');write_json(seal/'R3_25_FINAL_SEAL_MANIFEST.json',{'stage':STAGE,'status':'FINAL_SEAL_MANIFEST' if not failed else 'FAILED_SEAL_MANIFEST','files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [ap,md]}});print(json.dumps(report,indent=2));return 0 if not failed else 1
if __name__=='__main__':
 root=Path(sys.argv[sys.argv.index('--root')+1]).resolve() if '--root' in sys.argv else ROOT;raise SystemExit(main(root))
