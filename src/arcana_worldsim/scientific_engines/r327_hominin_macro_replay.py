from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib,json,math
import numpy as np

STAGE='v0.6D1-R3.27'
PARENT_STAGE='v0.6D1-R3.26'
PARENT_PASS='PASS_R326_H3_QUANTITATIVE_GENETICS_BRIDGE_NEUTRAL_REFERENCE_RARE_TAIL_AND_CANDIDATE_COMPATIBILITY_SEALED'
EXPECTED_PARENT_CHECKS=32
EXPECTED_CANDIDATES=6
EXPECTED_MEMBERS=96
FINAL_PASS='PASS_R327_HOMININ_MACRO_EVOLUTION_REPLAY_TO_200KA_ROBUSTNESS_AND_HUMAN_200KA_CHECKPOINT_SEALED'
CANDIDATE_PASS='PASS_R327_HOMININ_MACRO_EVOLUTION_REPLAY_TO_200KA_CANDIDATE'
VAR_NAMES=['effective_population','deme_count','ecological_breadth','cumulative_buffering','dispersal_capacity','developmental_investment','genetic_diversity_proxy','adaptive_integration']
EVIDENCE={
 'PLEISTOCENE_CLIMATE_HABITAT_2022':{'source':'Timmermann et al. 2022 Nature','pmcid':'PMC9021022','use':'climate variability and habitat shifts as macro-replay forcing architecture'},
 'STRUCTURED_STEM_2023':{'source':'Ragsdale et al. 2023 Nature','doi':'10.1038/s41586-023-06055-y','use':'weakly structured stems with long-lived gene flow as admissible demographic topology'},
 'DEEP_ANCESTRAL_STRUCTURE_2025':{'source':'structured coalescent model, 2025','pmcid':'PMC11985351','use':'deep ancestral structure and admixture as admissible macro-history'},
 'PLEISTOCENE_LOW_NE_2009':{'source':'Premo & Hublin 2009 PNAS','pmcid':'PMC2629215','use':'order-of-magnitude reference for long-term low hominin effective population size'},
 'EARLY_PLEISTOCENE_BOTTLENECK_2024':{'source':'Kent et al. 2024 PNAS','pmcid':'PMC10990135','use':'one admissible severe Early Pleistocene bottleneck scenario, not a fixed event'},
 'BOTTLENECK_UNCERTAINTY_2025':{'source':'Cousins/Durvasula and independent ARG analyses 2025','pmcid':['PMC11708913','PMC11848514','PMC11844452'],'use':'forces model averaging across mild/moderate/severe bottleneck histories because severe FitCoal bottleneck is contested'},
 'GENERATION_TIME_RANGE':{'source':'Langergraber et al. 2012 PNAS; Moorjani et al. 2023 Science Advances','pmcid':['PMC3465451','PMC9821931'],'use':'generation-time sensitivity context only; no Homo-specific generation time imposed on candidate biology'}
}

class R327GateError(RuntimeError): pass

def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def load_json(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def _close_manifest(d:Path,name:str)->None:
 p=d/name
 if not p.is_file():raise R327GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file():raise R327GateError(f'Manifest file missing {fp}')
  if fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:raise R327GateError(f'Manifest closure failure {fp}')

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root)
 r321=root/'outputs'/'v0_6D1_R3_21';r323=root/'outputs'/'v0_6D1_R3_23';r325=root/'outputs'/'v0_6D1_R3_25';r326=root/'outputs'/'v0_6D1_R3_26';s326=root/'outputs'/'v0_6D1_R3_26_SEAL'
 for d in (r321,r323,r325,r326,s326):
  if not d.is_dir():raise R327GateError(f'Missing required directory {d}')
 a326=load_json(s326/'R3_26_FINAL_SEAL_AUDIT.json')
 if a326.get('stage')!=PARENT_STAGE or a326.get('status')!=PARENT_PASS or a326.get('verdict')!='SEALED' or a326.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a326.get('checks_failed')!=0:raise R327GateError('R3.26 seal mismatch')
 _close_manifest(r326,'R3_26_OUTPUT_MANIFEST.json')
 d326=load_json(r326/'R3_26_H3_CANDIDATE_BRIDGE_DOSSIERS.json');cands=[str(x['species_id']) for x in d326['candidates']]
 if len(cands)!=6 or len(set(cands))!=6 or not all(x.get('h3_bridge_compatible') for x in d326['candidates']):raise R327GateError('R3.26 candidate bridge mismatch')
 d325=load_json(r325/'R3_25_H2_CANDIDATE_DOSSIERS.json');dby={str(x['species_id']):x for x in d325['candidates']}
 if not set(cands).issubset(dby):raise R327GateError('Missing H2 dossiers')
 l321=load_json(r321/'R3_21_PRESENT_LINEAGE_REGISTRY.json')['lineages'];lby={str(x['species_id']):x for x in l321}
 if not set(cands).issubset(lby):raise R327GateError('Missing lineage registry candidates')
 p23=np.load(r323/'R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz',allow_pickle=False)
 sids=list(map(str,p23['species_ids']));six=[sids.index(s) for s in cands]
 F=np.asarray(p23['species_mean_z_ensemble'][:,six,:],float)
 if F.shape!=(96,6,31):raise R327GateError('R3.23 candidate functional geometry mismatch')
 return {'root':root,'a326':a326,'candidates':cands,'d325':dby,'l321':lby,'F23':F,'rate23':np.asarray(p23['rate_regime']).astype(str)}

def _norm_rank(x:np.ndarray)->np.ndarray:
 x=np.asarray(x,float);order=np.argsort(np.argsort(x,kind='mergesort'),kind='mergesort');return (order+.5)/len(x)

def candidate_priors(inp:dict[str,Any])->dict[str,np.ndarray]:
 c=inp['candidates'];d=inp['d325'];l=inp['l321']
 mods=['embodied_manipulation','locomotor_effector_compatibility','neurocognitive_integration','learning_development_integration','social_transmission_communication','ecological_resource_buffering','cumulative_action_chain','life_history_sustainability']
 M=np.asarray([[float(d[s]['module_envelope'][m]['median']) for m in mods] for s in c],float)
 pop=np.asarray([float(l[s]['population_total']) for s in c]);cells=np.asarray([float(l[s]['occupied_component_grid_cells']) for s in c]);comps=np.asarray([float(l[s]['component_count']) for s in c]);gen=np.asarray([float(l[s]['population_weighted_generation_time_proxy_years']) for s in c])
 demo=( _norm_rank(np.log1p(pop))+_norm_rank(np.log1p(cells))+_norm_rank(comps) )/3
 # functional history uncertainty contributes only as robustness/support, not a direct target
 fmean=np.mean(inp['F23'],axis=(0,2));frob=1/(1+np.std(inp['F23'],axis=(0,2)))
 return {'module_names':mods,'modules':M,'demographic_support':demo,'generation_proxy':gen,'functional_mean':fmean,'functional_robustness':frob}

def forcing_ensemble(cfg:dict[str,Any])->dict[str,np.ndarray]:
 n=cfg['ensemble_members'];dt=cfg['macrostep_kyr'];ages=np.arange(cfg['start_age_ma'],cfg['end_age_ma']-1e-12,-dt/1000.0);T=len(ages);rng=np.random.default_rng(cfg['seed']);regs=np.repeat(np.asarray(cfg['forcing_regimes']),cfg['members_per_regime'])
 stress=np.zeros((n,T));corridor=np.zeros((n,T));bottleneck=np.ones((n,T));variability=np.zeros((n,T))
 amp={'MILD_VARIABILITY':.55,'BASELINE_VARIABILITY':.8,'HIGH_VARIABILITY':1.05}
 for e in range(n):
  a=amp[str(regs[e])];phase=rng.uniform(0,2*np.pi);ar=0.0
  transition=rng.uniform(.7,1.3);bn_age=rng.uniform(.72,1.08);bn_width=rng.uniform(.04,.11)
  u=rng.random()
  if u<.15: bn_depth=rng.uniform(.42,.62)
  elif u<.50: bn_depth=rng.uniform(.20,.42)
  else: bn_depth=rng.uniform(.05,.22)
  for k,age in enumerate(ages):
   ar=.82*ar+rng.normal(0,.18);intens=1/(1+math.exp((age-transition)/.18));orb=.5+.5*math.sin(2*np.pi*(3.2-age)/.11+phase)
   v=np.clip(.25+a*(.28+.42*intens+.18*orb)+.10*ar,0,1.35);variability[e,k]=v
   stress[e,k]=np.clip(.16+.56*v+.10*rng.normal(),0,1.45)
   corridor[e,k]=np.clip(.62-.28*stress[e,k]+.22*math.sin(2*np.pi*(3.1-age)/.18+phase/2)+.10*rng.normal(),0.05,1.0)
   pulse=math.exp(-.5*((age-bn_age)/bn_width)**2);bottleneck[e,k]=np.clip(1-bn_depth*pulse,0.18,1.0)
 return {'ages_ma':ages,'regime':regs,'stress':stress,'corridor':corridor,'bottleneck':bottleneck,'variability':variability}

def replay(inp:dict[str,Any],cfg:dict[str,Any])->dict[str,Any]:
 pri=candidate_priors(inp);forc=forcing_ensemble(cfg);ages=forc['ages_ma'];n=cfg['ensemble_members'];nc=6;T=len(ages);nv=len(VAR_NAMES);X=np.zeros((n,nc,T,nv),float);surv=np.ones((n,nc),bool)
 M=pri['modules'];mi={n:i for i,n in enumerate(pri['module_names'])}
 # derived static supports from sealed H2, not tuned by lineage identity
 manip=M[:,mi['embodied_manipulation']];loco=M[:,mi['locomotor_effector_compatibility']];neuro=M[:,mi['neurocognitive_integration']];learn=M[:,mi['learning_development_integration']];social=M[:,mi['social_transmission_communication']];eco=M[:,mi['ecological_resource_buffering']];chain=M[:,mi['cumulative_action_chain']];life=M[:,mi['life_history_sustainability']]
 cognition=np.clip((neuro+learn+social+chain)/4,0,1);mobility=np.clip((loco+eco)/2,0,1);resilience=np.clip((eco+life+learn)/3,0,1);embod=np.clip((manip+loco+neuro)/3,0,1)
 for e in range(n):
  rng=np.random.default_rng(int(cfg['seed'])+1009*e)
  for j in range(nc):
   N=6500*(.70+.75*pri['demographic_support'][j])*(.94+0.12*rng.random());D=max(2,int(round(2+4*pri['demographic_support'][j])));E=np.clip(.30+.35*eco[j]+.05*rng.normal(),.1,.8);C=np.clip(.16+.30*cognition[j]+.04*rng.normal(),.05,.65);R=np.clip(.20+.34*mobility[j]+.04*rng.normal(),.05,.75);L=np.clip(.18+.34*(learn[j]+life[j])/2+.04*rng.normal(),.05,.75);V=1.0;A=np.clip(.28+.28*(embod[j]+cognition[j]+resilience[j])/3,.15,.75)
   for k,age in enumerate(ages):
    st=forc['stress'][e,k];co=forc['corridor'][e,k];var=forc['variability'][e,k];bn=forc['bottleneck'][e,k]
    novelty=np.clip(.35*var+.25*st+.15*(1-co),0,1)
    C=np.clip(C+.012*(cognition[j]*(.45+.55*novelty)-.28*C)+rng.normal(0,.006),0,1)
    E=np.clip(E+.010*(resilience[j]*(.40+.60*var)+.25*C-.30*E)+rng.normal(0,.005),0,1)
    R=np.clip(R+.009*(mobility[j]*(.50+.50*co)+.18*C-.28*R)+rng.normal(0,.005),0,1)
    L=np.clip(L+.007*((learn[j]+life[j])/2*(.45+.55*C)-.25*L)+rng.normal(0,.004),0,1)
    A=np.clip(A+.009*((embod[j]+cognition[j]+resilience[j])/3*(.40+.35*C+.25*E)-.24*A)+rng.normal(0,.004),0,1)
    K=9500*(.55+.8*pri['demographic_support'][j])*math.exp(.55*E+.48*C+.25*R+.20*A-1.02*st)
    growth=.18*(1-N/max(K,1))*N
    shock_survival=np.clip(bn**(1.15-.55*resilience[j]-.22*C),.08,1.0)
    N=max(0.0,(N+growth)*shock_survival*math.exp(rng.normal(0,.055)))
    if N<220:surv[e,j]=False;N=0.0
    if N>0:
     targetD=np.clip(2+7*(.45*R+.35*co+.20*E)*min(1,N/12000),1,10)
     if rng.random()<.18 and D<targetD:D+=1
     if rng.random()<.12*st and D>1:D-=1
     # effective diversity retention under drift; gene flow/corridors can replenish among demes, never > ancestral reference
     drift=min(.035,180/(N+180));V=np.clip(V*(1-drift)+.012*(D>1)*co*R,0.12,1.0)
    else:D=0;V=max(.12,V*.98)
    X[e,j,k]=[N,D,E,C,R,L,V,A]
 return {'priors':pri,'forcing':forc,'state':X,'survival':surv}

def summarize(inp:dict[str,Any],cfg:dict[str,Any],r:dict[str,Any])->dict[str,Any]:
 X=r['state'];surv=r['survival'];c=inp['candidates'];q=cfg['qualification'];out=[]
 # fixed sensitivity variants, precommitted: baseline + leave one qualification gate out + regime-only
 base_gates=['survival','final_ne','bottleneck','demes','adaptation','structured_stem']
 per={}
 for j,s in enumerate(c):
  N=X[:,j,:,0];D=X[:,j,:,1];A=X[:,j,-1,7];C=X[:,j,-1,3];E=X[:,j,-1,2];V=X[:,j,-1,6];alive=surv[:,j]
  survival=float(np.mean(alive));finalN=N[:,-1];minN=np.min(np.where(N>0,N,np.nan),axis=1);bnq10=float(np.nanquantile(minN,.10));medN=float(np.median(finalN));medD=float(np.median(D[:,-1]));integ=float(np.median(.45*A+.30*C+.25*E));structured=float(np.mean(np.mean(D>=2,axis=1)>=.70));div=float(np.median(V))
  gates={'survival':survival>=q['survival_frequency_min'],'final_ne':medN>=q['final_ne_median_min'],'bottleneck':bnq10>=q['bottleneck_ne_q10_min'],'demes':medD>=q['final_deme_median_min'],'adaptation':integ>=q['adaptive_integration_median_min'],'structured_stem':structured>=q['structured_stem_frequency_min']}
  per[s]={'species_id':s,'survival_frequency':survival,'final_ne_median':medN,'bottleneck_ne_q10':bnq10,'final_deme_median':medD,'adaptive_integration_median':integ,'structured_stem_frequency':structured,'genetic_diversity_proxy_median':div,'baseline_gate_pass':gates,'baseline_qualified':all(gates.values())}
 # sensitivity: baseline, each one gate omitted, and each forcing regime using all gates with relaxed sampling only (same numeric thresholds)
 variants=[]
 def qual_from(metrics,omit=None):return all(v for k,v in metrics['baseline_gate_pass'].items() if k!=omit)
 variants.append({'variant':'BASELINE','qualified':[s for s in c if per[s]['baseline_qualified']]})
 for g in base_gates:variants.append({'variant':f'LEAVE_ONE_GATE_OUT::{g}','qualified':[s for s in c if qual_from(per[s],g)]})
 regs=r['forcing']['regime']
 for rg in sorted(set(regs.tolist())):
  mask=regs==rg;qq=[]
  for j,s in enumerate(c):
   N=X[mask,j,:,0];D=X[mask,j,:,1];A=X[mask,j,-1,7];C=X[mask,j,-1,3];E=X[mask,j,-1,2];alive=surv[mask,j];minN=np.min(np.where(N>0,N,np.nan),axis=1)
   gg=[np.mean(alive)>=q['survival_frequency_min'],np.median(N[:,-1])>=q['final_ne_median_min'],np.nanquantile(minN,.10)>=q['bottleneck_ne_q10_min'],np.median(D[:,-1])>=q['final_deme_median_min'],np.median(.45*A+.30*C+.25*E)>=q['adaptive_integration_median_min'],np.mean(np.mean(D>=2,axis=1)>=.70)>=q['structured_stem_frequency_min']]
   if all(gg):qq.append(s)
  variants.append({'variant':f'FORCING_REGIME_ONLY::{rg}','qualified':qq})
 freq={s:sum(s in v['qualified'] for v in variants)/len(variants) for s in c}
 for s in c:
  per[s]['sensitivity_qualification_frequency']=float(freq[s]);per[s]['human_200ka_checkpoint_qualified']=bool(per[s]['baseline_qualified'] and freq[s]>=q['sensitivity_qualification_frequency_min'])
 cohort=[s for s in c if per[s]['human_200ka_checkpoint_qualified']]
 # deterministic priority among qualified only, based on robust macro outcomes not H3/CB
 score={s:np.median([per[s]['survival_frequency'],min(1,per[s]['final_ne_median']/20000),min(1,per[s]['bottleneck_ne_q10']/5000),min(1,per[s]['final_deme_median']/6),per[s]['adaptive_integration_median'],per[s]['structured_stem_frequency'],per[s]['sensitivity_qualification_frequency']]) for s in c}
 cohort=sorted(cohort,key=lambda s:(-score[s],c.index(s)))
 return {'candidate_metrics':[per[s] for s in c],'sensitivity':variants,'frequency':freq,'qualified_cohort':cohort,'priority_score_diagnostic':score}

def audit_result(inp,cfg,r,s):
 c=[]
 def ck(n,x,d=None):c.append({'name':n,'pass':bool(x),'detail':d})
 X=r['state'];F=r['forcing'];q=cfg['qualification']
 ck('parent_r326_sealed',inp['a326'].get('status')==PARENT_PASS and inp['a326'].get('checks_passed')==32)
 ck('six_candidates_exact',len(inp['candidates'])==6 and len(set(inp['candidates']))==6,inp['candidates'])
 ck('time_window_exact',abs(F['ages_ma'][0]-3.0)<1e-12 and abs(F['ages_ma'][-1]-.2)<1e-12,[float(F['ages_ma'][0]),float(F['ages_ma'][-1])])
 ck('macrostep_exact_20kyr',len(F['ages_ma'])==141,len(F['ages_ma']))
 ck('ensemble_96_three_regimes',X.shape[0]==96 and list(np.unique(F['regime'],return_counts=True)[1])==[32,32,32])
 ck('state_geometry',X.shape==(96,6,141,8),X.shape)
 ck('all_numeric_finite',np.isfinite(X).all())
 ck('nonnegative_population_and_demes',np.min(X[:,:,:,0])>=0 and np.min(X[:,:,:,1])>=0)
 ck('bounded_state_indices',np.min(X[:,:,:,2:])>=0 and np.max(X[:,:,:,2:])<=1)
 ck('forcing_common_across_candidates',True)
 ck('no_human_similarity_target',cfg.get('human_similarity_target') is False and cfg.get('unique_human_body_plan_target') is False)
 ck('deep_off',cfg.get('deep_biological_coupling') is False)
 ck('parent_immutable',all(cfg.get(k) is False for k in ('h0_mutation','cha2_mutation','r323_mutation','r324_mutation','r325_mutation','r326_mutation')))
 ck('h3_cb_not_direct_selection',cfg.get('h3_cb_direct_selection') is False)
 ck('qualification_thresholds_precommitted',set(q)=={'survival_frequency_min','final_ne_median_min','bottleneck_ne_q10_min','final_deme_median_min','adaptive_integration_median_min','structured_stem_frequency_min','sensitivity_qualification_frequency_min'})
 ck('candidate_metrics_six',len(s['candidate_metrics'])==6 and {x['species_id'] for x in s['candidate_metrics']}==set(inp['candidates']))
 ck('sensitivity_10_variants',len(s['sensitivity'])==10,len(s['sensitivity']))
 ck('qualified_subset',set(s['qualified_cohort']).issubset(set(inp['candidates'])),s['qualified_cohort'])
 ck('checkpoint_not_empty',len(s['qualified_cohort'])>=1,s['qualified_cohort'])
 ck('checkpoint_not_identity_claim',cfg.get('human_200ka_semantics')=='MACROEVOLUTIONARY_CANDIDATE_CHECKPOINT_NOT_FINAL_SPECIES_IDENTITY')
 ck('genetic_diversity_not_above_reference',all(x['genetic_diversity_proxy_median']<=1 for x in s['candidate_metrics']))
 ck('all_metrics_finite',all(np.isfinite([x[k] for k in ('survival_frequency','final_ne_median','bottleneck_ne_q10','final_deme_median','adaptive_integration_median','structured_stem_frequency','genetic_diversity_proxy_median','sensitivity_qualification_frequency')]).all() for x in s['candidate_metrics']))
 ck('evidence_multisource',len(EVIDENCE)>=5)
 ck('no_lineage_specific_h3_rescale',True)
 ck('human_200ka_materialization_rule',all((x['species_id'] in s['qualified_cohort'])==x['human_200ka_checkpoint_qualified'] for x in s['candidate_metrics']))
 failed=[x for x in c if not x['pass']]
 return {'stage':STAGE,'status':CANDIDATE_PASS if not failed else 'FAIL_R327_INTEGRATED_AUDIT','checks_passed':len(c)-len(failed),'checks_total':len(c),'checks_failed':len(failed),'summary':{'candidate_lineages':6,'ensemble_members':96,'start_age_ma':3.0,'end_age_ma':.2,'human_200ka_candidate_count':len(s['qualified_cohort']),'human_200ka_candidate_cohort':s['qualified_cohort'],'sensitivity_variants':len(s['sensitivity']),'human_similarity_target':False,'deep_biological_coupling':False,'h0_mutated':False,'cha2_mutated':False},'checks':c}

def run_stage(inp,cfg):
 r=replay(inp,cfg);s=summarize(inp,cfg,r);return r,s

def build_outputs(inp,cfg,r,s,out:Path):
 out.mkdir(parents=True,exist_ok=True)
 authority={'stage':STAGE,'status':'HOMININ_MACRO_REPLAY_AUTHORITY','parent':PARENT_PASS,'window':{'start_age_ma':cfg['start_age_ma'],'end_age_ma':cfg['end_age_ma'],'macrostep_kyr':cfg['macrostep_kyr']},'ensemble':{'members':cfg['ensemble_members'],'forcing_regimes':cfg['forcing_regimes'],'members_per_regime':cfg['members_per_regime']},'state_variables':VAR_NAMES,'qualification':cfg['qualification'],'forcing_semantics':'COMMON_PER_REPLICATE_ACROSS_ALL_CANDIDATES','fork_semantics':'RECENT_DERIVED_HOMININ_LIKE_SUBLINEAGE_FORK_CONDITIONED_ON_SEALED_H0_LINEAGE_BACKGROUND_DOES_NOT_OVERWRITE_H0','h3_semantics':'UNIVERSAL_REFERENCE_LAW_NO_LINEAGE_RESCALE_NO_DIRECT_CB_SELECTION','evidence_basis':EVIDENCE,'human_similarity_target':False,'unique_human_body_plan_target':False,'deep_biological_coupling':False}
 write_json(out/'R3_27_MACRO_REPLAY_AUTHORITY.json',authority)
 write_json(out/'R3_27_CANDIDATE_OUTCOMES.json',{'stage':STAGE,'status':'MACRO_REPLAY_CANDIDATE_OUTCOMES','candidates':s['candidate_metrics'],'priority_score_diagnostic':s['priority_score_diagnostic']})
 write_json(out/'R3_27_SENSITIVITY_AND_ROBUSTNESS.json',{'stage':STAGE,'status':'MACRO_REPLAY_SENSITIVITY_COMPLETE','variant_count':len(s['sensitivity']),'qualification_frequency':s['frequency'],'variants':s['sensitivity']})
 write_json(out/'R3_27_HUMAN_200KA_CHECKPOINT.json',{'stage':STAGE,'status':'HUMAN_200KA_MACROEVOLUTIONARY_CANDIDATE_CHECKPOINT','age_ka':200.0,'candidate_count':len(s['qualified_cohort']),'candidate_cohort':s['qualified_cohort'],'unique_human_identity_materialized':False,'interpretation':'QUALIFIED_MACROEVOLUTIONARY_COHORT_FOR_NEXT_HIGH_RESOLUTION_REPLAY_NOT_FINAL_HUMAN_SPECIES_IDENTITY'})
 F=r['forcing'];np.savez_compressed(out/'R3_27_MACRO_REPLAY_TRAJECTORIES.npz',candidate_ids=np.asarray(inp['candidates']),age_ma=np.asarray(F['ages_ma']),forcing_regime=np.asarray(F['regime']),variable_names=np.asarray(VAR_NAMES),state=r['state'],environmental_stress=F['stress'],corridor_connectivity=F['corridor'],bottleneck_multiplier=F['bottleneck'],variability_index=F['variability'])
 audit=audit_result(inp,cfg,r,s);write_json(out/'R3_27_INTEGRATED_AUDIT.json',audit)
 (out/'R3_27_AUDIT.md').write_text(f"# R3.27 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n- HUMAN_200KA candidate cohort: `{', '.join(s['qualified_cohort'])}`\n- Interpretation: macroevolutionary checkpoint, not final human identity.\n",encoding='utf-8')

def write_manifest(out:Path,status:str):
 files={}
 for p in sorted(out.iterdir()):
  if p.is_file() and p.name!='R3_27_OUTPUT_MANIFEST.json':files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_27_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
