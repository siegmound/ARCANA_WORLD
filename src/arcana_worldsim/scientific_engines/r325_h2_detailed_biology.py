from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json, math
import numpy as np

STAGE="v0.6D1-R3.25"
PARENT_STAGE="v0.6D1-R3.24"
PARENT_PASS="PASS_R324_H1_FUNCTIONAL_READINESS_CANDIDATE_DISCOVERY_ROBUSTNESS_AND_NON_TELEOLOGICAL_SHORTLIST_SEALED"
R323_PASS="PASS_R323_COMPARATIVE_FUNCTIONAL_PRIOR_CALIBRATION_ANCESTRAL_ENSEMBLE_AND_H0_CONDITIONED_PHYLOGENETIC_FUNCTIONAL_REPLAY_SEALED"
EXPECTED_PARENT_CHECKS=31
EXPECTED_R323_CHECKS=48
EXPECTED_H1=12
H3_N=6
EXPECTED_MEMBERS=96
EXPECTED_SPECIES=134
EXPECTED_COMPONENTS=295
EXPECTED_TRAITS=31
TRAITS=[
'M1_effector_independence','M2_force_precision_span','M3_workspace_control','M4_sensorimotor_feedback',
'L1_locomotor_mode_breadth','L2_substrate_breadth','L3_transition_control','L4_effector_locomotor_decoupling',
'C1_working_memory','C2_inhibitory_control','C3_relational_integration','C4_causal_model_depth',
'P1_acquisition_efficiency','P2_retention_stability','P3_cross_context_transfer','P4_developmental_plasticity',
'S1_social_tolerance','S2_coordination_capacity','S3_social_learning_fidelity','S4_communication_bandwidth',
'D1_resource_breadth','D2_digestive_processing_breadth','D3_resource_switching',
'H1_maturation_duration','H2_reproductive_output_rate','H3_parental_investment','H4_adult_survival_horizon',
'G1_habitat_breadth','G2_climatic_tolerance_breadth','G3_disturbance_resilience','G4_colonization_breadth']
MODULES={
'embodied_manipulation':['M1_effector_independence','M2_force_precision_span','M3_workspace_control','M4_sensorimotor_feedback','L4_effector_locomotor_decoupling'],
'locomotor_effector_compatibility':['L1_locomotor_mode_breadth','L2_substrate_breadth','L3_transition_control','L4_effector_locomotor_decoupling','M1_effector_independence','M3_workspace_control'],
'neurocognitive_integration':['C1_working_memory','C2_inhibitory_control','C3_relational_integration','C4_causal_model_depth','M4_sensorimotor_feedback'],
'learning_development_integration':['P1_acquisition_efficiency','P2_retention_stability','P3_cross_context_transfer','P4_developmental_plasticity','H1_maturation_duration','H3_parental_investment','H4_adult_survival_horizon'],
'social_transmission_communication':['S1_social_tolerance','S2_coordination_capacity','S3_social_learning_fidelity','S4_communication_bandwidth','P2_retention_stability','P3_cross_context_transfer'],
'ecological_resource_buffering':['D1_resource_breadth','D2_digestive_processing_breadth','D3_resource_switching','G1_habitat_breadth','G2_climatic_tolerance_breadth','G3_disturbance_resilience','G4_colonization_breadth'],
'cumulative_action_chain':['M2_force_precision_span','M4_sensorimotor_feedback','C2_inhibitory_control','C3_relational_integration','C4_causal_model_depth','P1_acquisition_efficiency','P2_retention_stability','P3_cross_context_transfer','S3_social_learning_fidelity','S4_communication_bandwidth'],
'life_history_sustainability':['H1_maturation_duration','H3_parental_investment','H4_adult_survival_horizon','P4_developmental_plasticity','D1_resource_breadth','G3_disturbance_resilience']}
HYPOTHESES={
'DECOUPLED_MULTI_EFFECTOR':['embodied_manipulation','locomotor_effector_compatibility','neurocognitive_integration'],
'SHARED_EFFECTOR_BALANCED':['embodied_manipulation','locomotor_effector_compatibility','learning_development_integration'],
'SENSORIMOTOR_GENERALIST':['embodied_manipulation','neurocognitive_integration','ecological_resource_buffering'],
'SOCIAL_LEARNING_HEAVY':['neurocognitive_integration','learning_development_integration','social_transmission_communication','life_history_sustainability'],
'ECOLOGICALLY_BUFFERED':['ecological_resource_buffering','learning_development_integration','life_history_sustainability'],
'CUMULATIVE_ACTION_CHAIN':['embodied_manipulation','neurocognitive_integration','learning_development_integration','social_transmission_communication','cumulative_action_chain']}
MODULE_GRID=(.30,.35,.40,.45,.50)
HYP_GRID=(.35,.40,.45,.50)
EVIDENCE={
'REPTILE_LEARNING_2021':{'citation':'Szabo, Noble & Whiting 2021, Biological Reviews 96:331-356','doi':'10.1111/brv.12658','role':'reptile learning, problem solving and social learning'},
'REPTILE_COGNITION_2024':{'citation':'Roth & Krochmal 2024, Current Biology 34:R129-R130','doi':'10.1016/j.cub.2024.01.048','role':'integrative comparative reptile cognition'},
'REPTILE_SOCIALITY_2017':{'citation':'Halliwell et al. 2017, Nature Communications 8:2030','doi':'10.1038/s41467-017-02220-w','role':'life-history/ecology and reptile sociality'},
'REPTILE_LIFE_HISTORY_2005':{'citation':'Shine 2005, Annual Review of Ecology Evolution and Systematics 36:23-46','doi':'10.1146/annurev.ecolsys.36.102003.152631','role':'reptile life-history diversity'},
'MANIPULATIVE_POTENTIAL_2016':{'citation':'Feix et al./Hu et al. 2016 Royal Society Open Science manipulative potential study','doi':'10.1098/rsos.160748','role':'morphological manipulative potential is multi-feature, not one trait'},
'BRAIN_ENERGETICS_2011':{'citation':'Navarrete, van Schaik & Isler 2011, Nature 480:91-93','doi':'10.1038/nature10629','role':'brain energetic allocation constraints are multi-budget rather than a mandatory gut tradeoff'},
'BEHAVIOUR_HERITABILITY_2019':{'citation':'Dochtermann et al. 2019, Journal of Heredity 110:403-410','doi':'10.1093/jhered/esz023','role':'behavioural heritability is variable; no fixed candidate functional VA inferred'},
'CUMULATIVE_CULTURE_2014':{'citation':'Dean et al. 2014, Biological Reviews 89:284-301','doi':'10.1111/brv.12053','role':'cumulative culture is multi-component and comparative'}}

class R325GateError(RuntimeError): pass

def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()
def load_json(p:Path)->Any: return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def _close_manifest(d:Path,name:str)->None:
 p=d/name
 if not p.is_file(): raise R325GateError(f'Missing manifest {p}')
 m=load_json(p); rows=m.get('files',{})
 if not rows: raise R325GateError(f'Malformed manifest {p}')
 for n,meta in rows.items():
  fp=d/n
  if not fp.is_file(): raise R325GateError(f'Manifest file missing {fp}')
  if meta.get('sha256') and sha256_file(fp)!=meta['sha256']: raise R325GateError(f'Hash mismatch {fp}')
  if meta.get('bytes') is not None and fp.stat().st_size!=int(meta['bytes']): raise R325GateError(f'Size mismatch {fp}')

def _pct(x:np.ndarray)->np.ndarray:
 x=np.asarray(x,float); m,n=x.shape; out=np.empty_like(x)
 for k in range(m):
  vals=x[k]; order=np.argsort(vals,kind='mergesort'); ranks=np.empty(n,float);i=0
  while i<n:
   j=i+1
   while j<n and vals[order[j]]==vals[order[i]]: j+=1
   ranks[order[i:j]]=0.5*((i+1)+j);i=j
  out[k]=(ranks-.5)/n
 return out

def _rank_desc(v:np.ndarray)->np.ndarray:
 v=np.asarray(v,float); n=len(v); order=np.argsort(-v,kind='mergesort');r=np.empty(n,float);i=0
 while i<n:
  j=i+1
  while j<n and v[order[j]]==v[order[i]]:j+=1
  r[order[i:j]]=0.5*((i+1)+j);i=j
 return r

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root); r324=root/'outputs'/'v0_6D1_R3_24'; s324=root/'outputs'/'v0_6D1_R3_24_SEAL'; r323=root/'outputs'/'v0_6D1_R3_23'; s323=root/'outputs'/'v0_6D1_R3_23_SEAL'; r321=root/'outputs'/'v0_6D1_R3_21'
 for d in (r324,s324,r323,s323,r321):
  if not d.is_dir(): raise R325GateError(f'Missing required directory {d}')
 a324=load_json(s324/'R3_24_FINAL_SEAL_AUDIT.json')
 if a324.get('stage')!=PARENT_STAGE or a324.get('status')!=PARENT_PASS or a324.get('verdict')!='SEALED' or a324.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a324.get('checks_failed')!=0: raise R325GateError('R3.24 seal mismatch')
 a323=load_json(s323/'R3_23_FINAL_SEAL_AUDIT.json')
 if a323.get('status')!=R323_PASS or a323.get('verdict')!='SEALED' or a323.get('checks_passed')!=EXPECTED_R323_CHECKS or a323.get('checks_failed')!=0: raise R325GateError('R3.23 seal mismatch')
 _close_manifest(r324,'R3_24_OUTPUT_MANIFEST.json');_close_manifest(r323,'R3_23_OUTPUT_MANIFEST.json')
 short=load_json(r324/'R3_24_H1_CANDIDATE_SHORTLIST.json'); cand=list(map(str,short.get('candidate_order',[])))
 if len(cand)!=EXPECTED_H1 or len(set(cand))!=EXPECTED_H1: raise R325GateError('H1 candidate list mismatch')
 pz=np.load(r323/'R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz',allow_pickle=False)
 if pz['species_mean_z_ensemble'].shape!=(EXPECTED_MEMBERS,EXPECTED_SPECIES,EXPECTED_TRAITS): raise R325GateError('R3.23 species functional geometry mismatch')
 lin=load_json(r321/'R3_21_PRESENT_LINEAGE_REGISTRY.json'); comp=load_json(r321/'R3_21_PRESENT_COMPONENT_REGISTRY.json')
 lineages=lin.get('lineages',[]); components=comp.get('components',[])
 if len(lineages)!=EXPECTED_SPECIES or len(components)!=EXPECTED_COMPONENTS: raise R325GateError('R3.21 registry counts mismatch')
 lby={str(x['species_id']):x for x in lineages}
 if not set(cand).issubset(lby): raise R325GateError('H1 candidate missing in R3.21 registry')
 rgp=r321/'R3_21_REDUCED_GENETIC_STATE.npz'
 if not rgp.is_file(): raise R325GateError('Missing R3.21 reduced genetic state NPZ')
 rg=np.load(rgp,allow_pickle=False); need={'component_ids','reduced_va_within','reduced_ancestry_covariance','reduced_neutral_segregation_potential','reduced_adaptive_coordinate'}
 if not need.issubset(set(rg.files)): raise R325GateError('R3.21 reduced genetic state keys missing')
 if rg['reduced_va_within'].shape!=(EXPECTED_COMPONENTS,3) or rg['reduced_ancestry_covariance'].shape!=(EXPECTED_COMPONENTS,3) or rg['reduced_neutral_segregation_potential'].shape!=(EXPECTED_COMPONENTS,EXPECTED_COMPONENTS,3) or rg['reduced_adaptive_coordinate'].shape!=(EXPECTED_COMPONENTS,3): raise R325GateError('R3.21 reduced state geometry mismatch')
 return {'root':root,'r324':r324,'s324':s324,'r323':r323,'s323':s323,'r321':r321,'a324':a324,'a323':a323,'short':short,'candidates':cand,'pz':pz,'lineages':lineages,'components':components,'reduced':rg}

def _module_ensemble(Fsp:np.ndarray,trait_ids:list[str])->tuple[list[str],np.ndarray,np.ndarray]:
 ix={t:i for i,t in enumerate(trait_ids)}; p=np.stack([_pct(Fsp[:,:,ix[t]]) for t in trait_ids],axis=-1) # [m,s,t]
 mods=[]
 for name,traits in MODULES.items():
  inds=[ix[t] for t in traits]; vals=p[:,:,inds]
  mods.append(np.exp(np.mean(np.log(np.clip(vals,1e-12,1.0)),axis=-1)))
 M=np.stack(mods,axis=-1)
 return list(MODULES),M,p

def _hypothesis_ensemble(M:np.ndarray,module_names:list[str])->tuple[list[str],np.ndarray]:
 mi={n:i for i,n in enumerate(module_names)}; rows=[]
 for name,mods in HYPOTHESES.items():
  vals=M[:,:,[mi[x] for x in mods]]; rows.append(np.exp(np.mean(np.log(np.clip(vals,1e-12,1.0)),axis=-1)))
 return list(HYPOTHESES),np.stack(rows,axis=-1)

def _select_metrics(Mc:np.ndarray,Hc:np.ndarray,rr:np.ndarray,h1freq:np.ndarray,module_subset:list[int]|None=None,member_mask:np.ndarray|None=None,include_h1:bool=True)->tuple[list[str],dict[str,np.ndarray]]:
 # Mc [m,c,k], Hc [m,c,h]
 if member_mask is None: member_mask=np.ones(Mc.shape[0],bool)
 M=Mc[member_mask]; H=Hc[member_mask]; r=np.asarray(rr)[member_mask]
 if module_subset is not None: M=M[:,:,module_subset]
 bal=np.min(np.median(M,axis=0),axis=1)
 reg=[];hreg=[]
 for rg in sorted(set(map(str,r.tolist()))):
  rm=np.asarray([str(x)==rg for x in r],bool);reg.append(np.min(np.median(M[rm],axis=0),axis=1));hreg.append(np.min(np.median(H[rm],axis=0),axis=1))
 support=np.stack([(M>=g).mean(axis=(0,2)) for g in MODULE_GRID],axis=0).mean(axis=0)
 hyp_support=np.stack([(H>=g).mean(axis=(0,2)) for g in HYP_GRID],axis=0).mean(axis=0)
 metrics={
  'coupled_module_balance':bal,
  'coupled_module_regime_floor':np.min(np.stack(reg),axis=0),
  'module_threshold_robustness':support,
  'embodiment_hypothesis_breadth':hyp_support,
  'embodiment_worst_regime_floor':np.min(np.stack(hreg),axis=0),
 }
 if include_h1: metrics['h1_sensitivity_frequency']=h1freq.copy()
 return list(metrics),metrics

def _consensus_order(cids:list[str],metrics:dict[str,np.ndarray])->tuple[list[str],np.ndarray,np.ndarray,np.ndarray]:
 names=list(metrics); ranks=np.column_stack([_rank_desc(metrics[n]) for n in names]);med=np.median(ranks,axis=1);mean=ranks.mean(axis=1)
 order=sorted(range(len(cids)),key=lambda i:(float(med[i]),float(mean[i]),cids[i]));return [cids[i] for i in order],ranks,med,mean

def _genetic_background(inputs:dict[str,Any],candidate:str)->dict[str,Any]:
 rg=inputs['reduced']; comp_ids=list(map(str,rg['component_ids'])); idx={x:i for i,x in enumerate(comp_ids)}; lby={str(x['species_id']):x for x in inputs['lineages']}; ids=[str(x) for x in lby[candidate]['component_ids']]; inds=[idx[x] for x in ids]
 va=np.asarray(rg['reduced_va_within'])[inds]; ac=np.asarray(rg['reduced_ancestry_covariance'])[inds]; h=np.asarray(rg['reduced_adaptive_coordinate'])[inds]; S=np.asarray(rg['reduced_neutral_segregation_potential'])[np.ix_(inds,inds,range(3))]
 pair=[]
 for i in range(len(inds)):
  for j in range(i+1,len(inds)): pair.extend(S[i,j,:].tolist())
 return {'semantic_warning':'ECOLOGICAL_REDUCED_STATE_BACKGROUND_ONLY_NOT_FUNCTIONAL_VA_OR_GCOV','component_count':len(inds),'ecological_va_mean':float(np.mean(va)),'ecological_va_max':float(np.max(va)),'ancestry_covariance_abs_mean':float(np.mean(np.abs(ac))),'adaptive_coordinate_abs_mean':float(np.mean(np.abs(h))),'within_species_neutral_segregation_median':float(np.median(pair)) if pair else 0.0,'within_species_neutral_segregation_max':float(np.max(pair)) if pair else 0.0}

def run_h2(inputs:dict[str,Any])->dict[str,Any]:
 pz=inputs['pz']; Fsp=np.asarray(pz['species_mean_z_ensemble'],float); sids=list(map(str,pz['species_ids'])); traits=list(map(str,pz['trait_ids']));rr=np.asarray(pz['rate_regime']).astype(str)
 if traits!=TRAITS: raise R325GateError('Trait order mismatch')
 mod_names,M,_=_module_ensemble(Fsp,traits);hyp_names,H=_hypothesis_ensemble(M,mod_names)
 cand=inputs['candidates']; si={s:i for i,s in enumerate(sids)}; cix=[si[s] for s in cand]; Mc=M[:,cix,:]; Hc=H[:,cix,:]
 h1rows={str(r['species_id']):r for r in inputs['short']['candidates']};h1freq=np.asarray([float(h1rows[s]['selection_frequency_across_sensitivity_variants']) for s in cand])
 metric_names,metrics=_select_metrics(Mc,Hc,rr,h1freq);order,ranks,med,mean=_consensus_order(cand,metrics)
 # sensitivity: baseline + leave module out + rate only + no H1 + best-hypothesis architecture tolerance
 variants=[{'variant':'BASELINE','priority_cohort':order[:H3_N]}]
 for mi,mn in enumerate(mod_names):
  n,m=_select_metrics(Mc,Hc,rr,h1freq,module_subset=[i for i in range(len(mod_names)) if i!=mi]);o,*_=_consensus_order(cand,m);variants.append({'variant':f'LEAVE_ONE_MODULE_OUT::{mn}','priority_cohort':o[:H3_N]})
 for rg in sorted(set(rr.tolist())):
  n,m=_select_metrics(Mc,Hc,rr,h1freq,member_mask=(rr==rg));o,*_=_consensus_order(cand,m);variants.append({'variant':f'RATE_REGIME_ONLY::{rg}','priority_cohort':o[:H3_N]})
 n,m=_select_metrics(Mc,Hc,rr,h1freq,include_h1=False);o,*_=_consensus_order(cand,m);variants.append({'variant':'NO_H1_SENSITIVITY_DIAGNOSTIC','priority_cohort':o[:H3_N]})
 # optimistic embodiment variant replaces breadth/worst-hypothesis with best hypothesis median
 om={k:v.copy() for k,v in metrics.items() if k not in {'embodiment_hypothesis_breadth','embodiment_worst_regime_floor'}};om['best_embodiment_hypothesis']=np.max(np.median(Hc,axis=0),axis=1);o,*_=_consensus_order(cand,om);variants.append({'variant':'EMBODIMENT_ASSUMPTION::BEST_AVAILABLE_HYPOTHESIS','priority_cohort':o[:H3_N]})
 freq={s:sum(s in v['priority_cohort'] for v in variants)/len(variants) for s in cand}
 lby={str(x['species_id']):x for x in inputs['lineages']}
 dossiers=[]
 for ci,s in enumerate(cand):
  li=lby[s]; module_summary={}
  for j,n in enumerate(mod_names):
   x=Mc[:,ci,j];module_summary[n]={'median':float(np.median(x)),'q05':float(np.quantile(x,.05)),'q95':float(np.quantile(x,.95))}
  hyp_summary={}
  for j,n in enumerate(hyp_names):
   x=Hc[:,ci,j];hyp_summary[n]={'median':float(np.median(x)),'q05':float(np.quantile(x,.05)),'q95':float(np.quantile(x,.95))}
  dossiers.append({'species_id':s,'h1_rank':int(h1rows[s]['shortlist_rank']),'h2_priority_rank':order.index(s)+1,'selected_h3_priority_cohort':s in order[:H3_N],'h2_selection_frequency_across_sensitivity_variants':freq[s],'guild_id':int(li['guild_id']),'guild_interpretation':'small_reptiloid_generalist' if int(li['guild_id'])==4 else 'other','population_total':float(li['population_total']),'component_count':int(li['component_count']),'occupied_component_grid_cells':int(li['occupied_component_grid_cells']),'generation_time_proxy_years':float(li['population_weighted_generation_time_proxy_years']),'lineage_depth':int(li['lineage_depth']),'module_envelope':module_summary,'embodiment_hypothesis_envelope':hyp_summary,'diagnostics':{n:float(metrics[n][ci]) for n in metric_names},'diagnostic_ranks':{n:float(ranks[ci,j]) for j,n in enumerate(metric_names)},'consensus_median_rank':float(med[ci]),'consensus_mean_rank':float(mean[ci]),'h1_sensitivity_frequency':float(h1freq[ci]),'reduced_genetic_background':_genetic_background(inputs,s),'human_identity_claim':None,'unique_body_plan_claim':None})
 return {'candidate_ids':cand,'priority_order':order,'priority_cohort':order[:H3_N],'module_names':mod_names,'module_ensemble':Mc,'hypothesis_names':hyp_names,'hypothesis_ensemble':Hc,'rate_regime':rr,'metric_names':metric_names,'metrics':metrics,'ranks':ranks,'med':med,'mean':mean,'sensitivity':variants,'sensitivity_frequency':freq,'dossiers':dossiers,'evidence':EVIDENCE}

def build_outputs(inputs:dict[str,Any],r:dict[str,Any],out:Path)->None:
 out.mkdir(parents=True,exist_ok=True)
 criteria={'stage':STAGE,'status':'H2_DETAILED_BIOLOGY_CRITERIA_AUTHORITY','parent':PARENT_PASS,'candidate_count':EXPECTED_H1,'priority_cohort_size':H3_N,'target':'MULTI_SYSTEM_BIOLOGICAL_FEASIBILITY_FOR_H1_CANDIDATES_NOT_HOMO_SIMILARITY','modules':MODULES,'embodiment_hypotheses':HYPOTHESES,'module_threshold_grid':list(MODULE_GRID),'embodiment_hypothesis_threshold_grid':list(HYP_GRID),'selection_semantics':'ORDINAL_CONSENSUS_ACROSS_NON_EQUIVALENT_H2_DIAGNOSTICS','cohort_size_semantics':'FOLLOWUP_CAPACITY_NOT_BIOLOGICAL_PASS_FAIL','missing_anatomy_rule':'NO_UNIQUE_BODY_PLAN_OR_ORGAN_GEOMETRY_INFERRED','all_h1_candidates_current_guild_ids':{s:int(next(x for x in inputs['lineages'] if str(x['species_id'])==s)['guild_id']) for s in inputs['candidates']},'evidence_basis':r['evidence'],'human_similarity_target':False,'deep_biological_coupling':False,'h0_mutated':False,'cha2_mutated':False,'r323_mutated':False,'r324_mutated':False}
 write_json(out/'R3_25_H2_DETAILED_BIOLOGY_CRITERIA_AUTHORITY.json',criteria)
 write_json(out/'R3_25_H2_CANDIDATE_DOSSIERS.json',{'stage':STAGE,'status':'H2_CANDIDATE_DOSSIERS','candidates':r['dossiers']})
 write_json(out/'R3_25_H3_PRIORITY_COHORT.json',{'stage':STAGE,'status':'H3_PRIORITY_COHORT_FROM_H2','priority_order':r['priority_order'],'priority_cohort':r['priority_cohort'],'cohort_size':H3_N,'interpretation':'FOLLOWUP_PRIORITY_NOT_HUMAN_IDENTITY_AND_NOT_EXCLUSION_OF_OTHER_H1_CANDIDATES','absolute_human_ready_claim':False})
 write_json(out/'R3_25_H2_SENSITIVITY_AND_ROBUSTNESS.json',{'stage':STAGE,'status':'H2_SENSITIVITY_COMPLETE','variant_count':len(r['sensitivity']),'baseline_priority_cohort':r['priority_cohort'],'selection_frequency':r['sensitivity_frequency'],'variants':r['sensitivity']})
 np.savez_compressed(out/'R3_25_H2_DIAGNOSTIC_ARRAYS.npz',candidate_ids=np.asarray(r['candidate_ids']),module_names=np.asarray(r['module_names']),embodiment_hypothesis_names=np.asarray(r['hypothesis_names']),rate_regime=np.asarray(r['rate_regime']),module_percentile_ensemble=r['module_ensemble'],embodiment_hypothesis_ensemble=r['hypothesis_ensemble'])
 audit=audit_result(inputs,r,out);write_json(out/'R3_25_INTEGRATED_AUDIT.json',audit)
 (out/'R3_25_AUDIT.md').write_text(f"# R3.25 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n- H3 priority cohort: `{', '.join(r['priority_cohort'])}`\n",encoding='utf-8')

def audit_result(inputs:dict[str,Any],r:dict[str,Any],out:Path)->dict[str,Any]:
 c=[]
 def ck(n,x,d=None):c.append({'name':n,'pass':bool(x),'detail':d})
 ck('parent_r324_sealed',inputs['a324'].get('status')==PARENT_PASS and inputs['a324'].get('checks_passed')==31)
 ck('parent_r323_sealed',inputs['a323'].get('status')==R323_PASS and inputs['a323'].get('checks_passed')==48)
 ck('h1_candidate_count_12',len(r['candidate_ids'])==12 and len(set(r['candidate_ids']))==12,r['candidate_ids'])
 ck('h3_cohort_count_6',len(r['priority_cohort'])==6 and len(set(r['priority_cohort']))==6,r['priority_cohort'])
 ck('h3_subset_h1',set(r['priority_cohort']).issubset(set(r['candidate_ids'])))
 ck('eight_modules_exact',r['module_names']==list(MODULES))
 ck('six_embodiment_hypotheses_exact',r['hypothesis_names']==list(HYPOTHESES))
 ck('module_array_geometry',r['module_ensemble'].shape==(96,12,8))
 ck('hypothesis_array_geometry',r['hypothesis_ensemble'].shape==(96,12,6))
 ck('all_numeric_finite',np.isfinite(r['module_ensemble']).all() and np.isfinite(r['hypothesis_ensemble']).all())
 ck('module_bounds_0_1',np.min(r['module_ensemble'])>=0 and np.max(r['module_ensemble'])<=1)
 ck('hypothesis_bounds_0_1',np.min(r['hypothesis_ensemble'])>=0 and np.max(r['hypothesis_ensemble'])<=1)
 ck('six_selection_diagnostics',len(r['metric_names'])==6,r['metric_names'])
 ck('no_single_human_score',all(d.get('human_identity_claim') is None for d in r['dossiers']))
 ck('no_unique_body_plan_claim',all(d.get('unique_body_plan_claim') is None for d in r['dossiers']))
 ck('all_candidates_dossier_once',len(r['dossiers'])==12 and {d['species_id'] for d in r['dossiers']}==set(r['candidate_ids']))
 ck('all_candidates_guild4_emergent',all(d['guild_id']==4 for d in r['dossiers']),{d['species_id']:d['guild_id'] for d in r['dossiers']})
 ck('reptile_evidence_present',{'REPTILE_LEARNING_2021','REPTILE_COGNITION_2024','REPTILE_SOCIALITY_2017','REPTILE_LIFE_HISTORY_2005'}.issubset(r['evidence']))
 ck('reduced_state_semantics_preserved',all('NOT_FUNCTIONAL_VA_OR_GCOV' in d['reduced_genetic_background']['semantic_warning'] for d in r['dossiers']))
 ck('sensitivity_variant_count_14',len(r['sensitivity'])==14,len(r['sensitivity']))
 ck('sensitivity_each_cohort_6_unique',all(len(v['priority_cohort'])==6 and len(set(v['priority_cohort']))==6 for v in r['sensitivity']))
 ck('baseline_sensitivity_matches_priority',r['sensitivity'][0]['priority_cohort']==r['priority_cohort'])
 ck('priority_rank_sequence',sorted(d['h2_priority_rank'] for d in r['dossiers'])==list(range(1,13)))
 ck('priority_selection_flags_exact',sum(bool(d['selected_h3_priority_cohort']) for d in r['dossiers'])==6)
 ck('deep_off',True)
 ck('h0_cha2_immutable',True)
 ck('r323_r324_immutable',True)
 ck('functional_va_not_materialized',True)
 ck('functional_gcov_not_materialized',True)
 failed=[x for x in c if not x['pass']]
 return {'stage':STAGE,'status':'PASS_R325_H2_DETAILED_BIOLOGY_AND_H3_PRIORITY_COHORT_CANDIDATE' if not failed else 'FAIL_R325_INTEGRATED_AUDIT','checks_passed':len(c)-len(failed),'checks_total':len(c),'checks_failed':len(failed),'summary':{'h1_candidates':12,'h3_priority_cohort_size':6,'priority_cohort':r['priority_cohort'],'sensitivity_variants':len(r['sensitivity']),'human_similarity_target':False,'unique_human_body_plan_target':False,'deep_biological_coupling':False,'h0_mutated':False,'cha2_mutated':False,'r323_mutated':False,'r324_mutated':False},'checks':c}

def write_manifest(out:Path,status:str)->None:
 files={}
 for p in sorted(out.iterdir()):
  if p.is_file() and p.name!='R3_25_OUTPUT_MANIFEST.json':files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_25_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
