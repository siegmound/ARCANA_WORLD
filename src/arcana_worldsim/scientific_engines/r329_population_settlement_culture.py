from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json, math
import numpy as np

STAGE='v0.6D1-R3.29'
PARENT_STAGE='v0.6D1-R3.28'
PARENT_PASS='PASS_R328_HIGH_RESOLUTION_200KA_TO_0_POPULATION_STRUCTURE_MIGRATION_ADMIXTURE_CHA2_EXPOSURE_AND_HUMAN_0KA_CHECKPOINT_SEALED'
EXPECTED_PARENT_CHECKS=35
EXPECTED_MEMBERS=32
EXPECTED_CANDIDATES=['RPT_010_D02','RPT_009_D02']
CANDIDATE_PASS='PASS_R329_POPULATION_MOBILITY_SETTLEMENT_AND_CULTURAL_PRECONDITIONS_CANDIDATE'
FINAL_PASS='PASS_R329_POPULATION_MOBILITY_SETTLEMENT_CULTURAL_TRANSMISSION_PRECONDITIONS_AND_CHA2_COMMUNITY_EXPOSURE_SEALED'

TIME_NAMES=['population_support_norm','residential_mobility_index','aggregation_potential','network_connectivity','cultural_transmission_support','cumulative_culture_precondition_stock','settlement_persistence_potential','resource_stress_proxy','interlineage_exchange_opportunity','cha2_community_disruption']
ANCHOR_NAMES=['population_proxy','grid_row','grid_col','community_viability','mobility_pressure','settlement_persistence_potential','network_access_proxy']

EVIDENCE={
 'HG_NETWORK_HIERARCHY_2009':{'source':'Hamilton et al. 2009 Proc R Soc B','pmcid':'PMC2706200','use':'hunter-gatherer organization is nested and fission-fusion rather than one fixed group size'},
 'HG_CULTURAL_TRANSMISSION_2024':{'source':'Hewlett et al. 2024 PNAS/PMC','pmcid':'PMC11621818','use':'small intimate camps and seasonal aggregation strongly structure cultural transmission'},
 'VILLAGE_SCALAR_STRESS_2023':{'source':'Dunbar et al. 2023 Phil Trans R Soc B/PMC','pmcid':'PMC10426039','use':'larger persistent settlements incur coordination/resource/conflict costs; persistence is not monotonic in size'},
 'CUMULATIVE_CULTURE_DEMOGRAPHY_2012':{'source':'Vaesen 2012 PLoS One','pmcid':'PMC3404092','use':'demography can condition cultural accumulation but simple hard demographic thresholds are not treated as universal'},
 'LATE_GLACIAL_NETWORKS_2021':{'source':'Romano et al. 2021 Phil Trans R Soc B/PMC','pmcid':'PMC8666909','use':'Palaeolithic regional networks and aggregation can be reconstructed as spatially distributed band systems'},
}

class R329GateError(RuntimeError): pass

def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def load_json(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def sigmoid(x:np.ndarray|float)->np.ndarray|float:return 1.0/(1.0+np.exp(-np.clip(x,-20,20)))

def _close_manifest(d:Path,name:str)->None:
 p=d/name
 if not p.is_file():raise R329GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file():raise R329GateError(f'Manifest file missing {fp}')
  if fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:raise R329GateError(f'Manifest closure failure {fp}')

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root);r328=root/'outputs'/'v0_6D1_R3_28';s328=root/'outputs'/'v0_6D1_R3_28_SEAL';r323=root/'outputs'/'v0_6D1_R3_23';s323=root/'outputs'/'v0_6D1_R3_23_SEAL'
 for d in (r328,s328,r323,s323):
  if not d.is_dir():raise R329GateError(f'Missing required directory {d}')
 a328=load_json(s328/'R3_28_FINAL_SEAL_AUDIT.json')
 if a328.get('stage')!=PARENT_STAGE or a328.get('status')!=PARENT_PASS or a328.get('verdict')!='SEALED' or a328.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a328.get('checks_failed')!=0:raise R329GateError('R3.28 final seal mismatch')
 _close_manifest(r328,'R3_28_OUTPUT_MANIFEST.json')
 cp=load_json(r328/'R3_28_HUMAN_0KA_CHECKPOINT.json')
 if cp.get('candidate_cohort')!=EXPECTED_CANDIDATES or cp.get('candidate_count')!=2 or cp.get('unique_human_identity_materialized') is not False:raise R329GateError('R3.28 HUMAN_0KA checkpoint mismatch')
 a323=load_json(s323/'R3_23_FINAL_SEAL_AUDIT.json')
 if a323.get('stage')!='v0.6D1-R3.23' or a323.get('verdict')!='SEALED' or a323.get('checks_passed')!=48 or a323.get('checks_failed')!=0:raise R329GateError('R3.23 final seal mismatch')
 _close_manifest(r323,'R3_23_OUTPUT_MANIFEST.json')
 z28=np.load(r328/'R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz',allow_pickle=False)
 ids28=list(map(str,z28['candidate_ids']))
 if ids28!=EXPECTED_CANDIDATES or z28['species_summary'].shape[0]!=EXPECTED_MEMBERS:raise R329GateError('R3.28 geometry mismatch')
 z23=np.load(r323/'R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz',allow_pickle=False)
 ids23=list(map(str,z23['species_ids']));idx23=[ids23.index(s) for s in EXPECTED_CANDIDATES];pidx=np.asarray(z28['parent_member_indices'],int)
 if len(pidx)!=EXPECTED_MEMBERS or np.max(pidx)>=z23['species_mean_z_ensemble'].shape[0]:raise R329GateError('Parent member mapping mismatch')
 traits=list(map(str,z23['trait_ids']));need=['L1_locomotor_mode_breadth','L2_substrate_breadth','L3_transition_control','C1_working_memory','C2_inhibitory_control','C3_relational_integration','C4_causal_model_depth','P1_acquisition_efficiency','P2_retention_stability','P3_cross_context_transfer','P4_developmental_plasticity','S1_social_tolerance','S2_coordination_capacity','S3_social_learning_fidelity','S4_communication_bandwidth','D1_resource_breadth','D3_resource_switching','H1_maturation_duration','H3_parental_investment','H4_adult_survival_horizon','G1_habitat_breadth','G2_climatic_tolerance_breadth','G3_disturbance_resilience','G4_colonization_breadth']
 if not all(t in traits for t in need):raise R329GateError('R3.23 functional trait dependency missing')
 F=np.asarray(z23['species_mean_z_ensemble'][pidx][:,idx23,:],float)
 return {'root':root,'a328':a328,'a323':a323,'z28':z28,'F':F,'traits':traits,'candidate_ids':EXPECTED_CANDIDATES,'parent_member_indices':pidx}

def _trait_axis(inp:dict[str,Any],names:list[str])->np.ndarray:
 ix=[inp['traits'].index(n) for n in names];return np.mean(inp['F'][...,ix],axis=-1)

def functional_priors(inp:dict[str,Any])->dict[str,np.ndarray]:
 # Latent functional state -> bounded behavioral/organizational precondition axes.
 social_learning=sigmoid(_trait_axis(inp,['S3_social_learning_fidelity','S4_communication_bandwidth','P1_acquisition_efficiency','P2_retention_stability','P3_cross_context_transfer','C1_working_memory','C3_relational_integration'])/1.6)
 coordination=sigmoid(_trait_axis(inp,['S1_social_tolerance','S2_coordination_capacity','C2_inhibitory_control','S4_communication_bandwidth'])/1.5)
 mobility=sigmoid(_trait_axis(inp,['L1_locomotor_mode_breadth','L2_substrate_breadth','L3_transition_control','G4_colonization_breadth'])/1.6)
 flexibility=sigmoid(_trait_axis(inp,['D1_resource_breadth','D3_resource_switching','G1_habitat_breadth','G2_climatic_tolerance_breadth','G3_disturbance_resilience','G4_colonization_breadth'])/1.7)
 development=sigmoid(_trait_axis(inp,['H1_maturation_duration','H3_parental_investment','H4_adult_survival_horizon','P4_developmental_plasticity'])/1.6)
 cognition=sigmoid(_trait_axis(inp,['C1_working_memory','C2_inhibitory_control','C3_relational_integration','C4_causal_model_depth'])/1.5)
 return {'social_learning':social_learning,'coordination':coordination,'mobility':mobility,'flexibility':flexibility,'development':development,'cognition':cognition}

def run_stage(inp:dict[str,Any],cfg:dict[str,Any])->dict[str,np.ndarray]:
 z=inp['z28'];ages=np.asarray(z['age_ka'],float);mask=ages<=float(cfg['start_age_ka'])+1e-12;age=ages[mask];S=np.asarray(z['species_summary'][:,:,mask,:],float);contact=np.asarray(z['contact_index'][:,mask],float)
 pri=functional_priors(inp);n,m,T=S.shape[:3]
 out=np.zeros((n,m,T,len(TIME_NAMES)),dtype=np.float32)
 # Global normalization is fixed from the parent cohort, not tuned per lineage.
 N=np.maximum(S[...,0],0);logN=np.log1p(N);nlo,nhi=np.quantile(logN,[.05,.95]);Nnorm=np.clip((logN-nlo)/max(nhi-nlo,1e-9),0,1)
 dem=np.clip(S[...,1]/6.0,0,1);spread=np.maximum(S[...,2],0);spnorm=np.clip(spread/30.0,0,1);div=np.clip(S[...,3],0,1);integ=np.clip(S[...,4],0,1);admix=np.clip(S[...,5],0,1);haz=np.clip(S[...,6],0,1);disp=np.clip(S[...,7],0,1)
 # Population trend: stress when support contracts; no literal resource quantity is claimed.
 growth=np.ones_like(N)
 growth[:,:,1:]=np.clip(N[:,:,1:]/np.maximum(N[:,:,:-1],1.0),0,2)
 contraction=np.clip(1-growth,0,1)
 stock=np.zeros((n,m),float)
 dt=np.empty(T,float);dt[:-1]=np.maximum(age[:-1]-age[1:],.05);dt[-1]=dt[-2] if T>1 else .25
 for t in range(T):
  # shared ancestry/contact increases exchange opportunity but never forces cultural merging.
  exch=np.clip(contact[:,t,None]*np.sqrt(pri['coordination']*pri['social_learning'])*(0.55+0.45*admix[:,:,t]),0,1)
  stress=np.clip(.34*contraction[:,:,t]+.26*(1-integ[:,:,t])+.18*(1-div[:,:,t])+.12*haz[:,:,t]+.10*disp[:,:,t],0,1)
  network=np.clip((.34*pri['coordination']+.30*pri['social_learning']+.18*dem[:,:,t]+.10*Nnorm[:,:,t]+.08*exch)*(1-.25*stress),0,1)
  aggregation=np.clip((.32*network+.25*Nnorm[:,:,t]+.18*dem[:,:,t]+.15*pri['flexibility']+.10*(1-stress))*(.85+.15*(1-spnorm[:,:,t])),0,1)
  mobility_idx=np.clip(.44*pri['mobility']+.22*spnorm[:,:,t]+.20*stress+.14*pri['flexibility']-.20*aggregation,0,1)
  transmission=np.clip(.30*pri['social_learning']+.20*pri['development']+.16*pri['cognition']+.16*network+.10*div[:,:,t]+.08*(1-stress),0,1)
  settlement=np.clip(.30*aggregation+.22*network+.18*(1-mobility_idx)+.14*Nnorm[:,:,t]+.10*integ[:,:,t]+.06*(1-stress),0,1)
  # A bounded cumulative-precondition stock; this is not technology count or a culture label.
  gain=transmission*network*(.45+.55*Nnorm[:,:,t])*(.55+.45*pri['development'])
  loss=np.clip(.28*stress+.18*(1-network)+.12*mobility_idx*stress,0,1)
  k=float(cfg['culture_stock_rate_per_kyr'])*dt[t]
  stock=np.clip(stock + k*(gain*(1-stock)-loss*stock),0,1)
  out[:,:,t,0]=Nnorm[:,:,t];out[:,:,t,1]=mobility_idx;out[:,:,t,2]=aggregation;out[:,:,t,3]=network;out[:,:,t,4]=transmission;out[:,:,t,5]=stock;out[:,:,t,6]=settlement;out[:,:,t,7]=stress;out[:,:,t,8]=exch;out[:,:,t,9]=np.clip(.55*haz[:,:,t]+.45*disp[:,:,t],0,1)
 # Spatial anchor layer is only constructed where R3.28 has explicit deme snapshots.
 sa=np.asarray(z['snapshot_age_ka'],float);smask=sa<=float(cfg['start_age_ka'])+1e-12;sage=sa[smask];D=np.asarray(z['snapshot_deme_state'][:,:,smask,:,:],float);A=np.asarray(z['snapshot_active'][:,:,smask,:],bool);anchor=np.zeros(D.shape[:-1]+(len(ANCHOR_NAMES),),dtype=np.float32);anchor[...,0:3]=D[...,0:3]
 # map snapshot times to community time series
 tidx=[int(np.argmin(np.abs(age-x))) for x in sage]
 for q,t in enumerate(tidx):
  for e in range(n):
   for j in range(m):
    active=A[e,j,q];pop=np.maximum(D[e,j,q,:,0],0);den=max(pop[active].sum(),1.0)
    # Deme viability combines local suitability with lineage-level adaptive/cultural support.
    viability=np.clip(.55*D[e,j,q,:,3]+.20*D[e,j,q,:,5]+.15*out[e,j,t,3]+.10*out[e,j,t,4],0,1)
    mobility_pressure=np.clip(out[e,j,t,1]+.35*(1-viability),0,1)
    settle=np.clip(.55*out[e,j,t,6]+.45*viability-.20*mobility_pressure*out[e,j,t,7],0,1)
    # Network access is relative to within-lineage population share and regional network connectivity.
    share=np.zeros_like(pop);share[active]=pop[active]/den
    access=np.clip(.65*out[e,j,t,3]+.35*np.sqrt(share),0,1)
    anchor[e,j,q,:,3]=np.where(active,viability,0);anchor[e,j,q,:,4]=np.where(active,mobility_pressure,0);anchor[e,j,q,:,5]=np.where(active,settle,0);anchor[e,j,q,:,6]=np.where(active,access,0)
 return {'age_ka':age,'community_summary':out,'functional_prior_names':np.asarray(list(pri.keys())),'functional_priors':np.stack([pri[k] for k in pri],axis=-1).astype(np.float32),'anchor_age_ka':sage,'community_anchor_state':anchor,'community_anchor_active':A.astype(np.uint8)}

def evaluate(inp:dict[str,Any],cfg:dict[str,Any],r:dict[str,np.ndarray])->tuple[dict[str,Any],dict[str,Any]]:
 X=r['community_summary'];q=cfg['qualification'];cands=[]
 for j,s in enumerate(inp['candidate_ids']):
  final=X[:,j,-1,:];cha=r['age_ka'];cm=(cha<=14.95)&(cha>=11.0);pre_idx=int(np.argmin(np.abs(cha-15.0)));post_idx=int(np.argmin(np.abs(cha-10.75)))
  metrics={'species_id':s,'final_network_connectivity_median':float(np.median(final[:,3])),'final_cultural_transmission_support_median':float(np.median(final[:,4])),'final_cumulative_precondition_stock_median':float(np.median(final[:,5])),'final_settlement_persistence_median':float(np.median(final[:,6])),'final_residential_mobility_median':float(np.median(final[:,1])),'cha2_community_disruption_peak_median':float(np.median(np.max(X[:,j,cm,9],axis=1))) if np.any(cm) else 0.0,'cha2_culture_stock_retention_median':float(np.median(X[:,j,post_idx,5]/np.maximum(X[:,j,pre_idx,5],1e-6)))}
  gates={'network':metrics['final_network_connectivity_median']>=q['network_min'],'transmission':metrics['final_cultural_transmission_support_median']>=q['transmission_min'],'culture_stock':metrics['final_cumulative_precondition_stock_median']>=q['culture_stock_min'],'settlement':metrics['final_settlement_persistence_median']>=q['settlement_min'],'cha2_retention':metrics['cha2_culture_stock_retention_median']>=q['cha2_stock_retention_min']}
  metrics['baseline_gate_pass']=gates;metrics['baseline_qualified']=all(gates.values());cands.append(metrics)
 variants=[]
 for v in cfg['sensitivity_multipliers']:
  cohort=[]
  for x in cands:
   ok=x['final_network_connectivity_median']>=q['network_min']*v and x['final_cultural_transmission_support_median']>=q['transmission_min']*v and x['final_cumulative_precondition_stock_median']>=q['culture_stock_min']*v and x['final_settlement_persistence_median']>=q['settlement_min']*v and x['cha2_culture_stock_retention_median']>=q['cha2_stock_retention_min']/max(v,1e-9)
   if ok:cohort.append(x['species_id'])
  variants.append({'multiplier':v,'cohort':cohort})
 for x in cands:
  x['sensitivity_qualification_frequency']=sum(x['species_id'] in v['cohort'] for v in variants)/len(variants)
  x['community_precondition_qualified']=x['baseline_qualified']
  x['robust_priority_qualified']=x['baseline_qualified'] and x['sensitivity_qualification_frequency']>=q['sensitivity_frequency_min']
 cohort=[x['species_id'] for x in cands if x['community_precondition_qualified']]
 robust=[x['species_id'] for x in cands if x['robust_priority_qualified']]
 borderline=[x['species_id'] for x in cands if x['community_precondition_qualified'] and not x['robust_priority_qualified']]
 outcomes={'stage':STAGE,'status':'POPULATION_SETTLEMENT_CULTURAL_PRECONDITION_OUTCOMES','candidates':cands,'community_precondition_cohort':cohort,'community_precondition_count':len(cohort),'robust_priority_cohort':robust,'borderline_retained_cohort':borderline,'unique_cultural_human_identity_materialized':False,'interpretation':'PRECONDITIONS_ONLY;_BASELINE_CAPABLE_LINEAGES_RETAINED;_SENSITIVITY_USED_AS_PRIORITY_NOT_EXTINCTION_OR_IDENTITY_GATE'}
 sensitivity={'stage':STAGE,'status':'SENSITIVITY_AND_ROBUSTNESS','variant_count':len(variants),'variants':variants}
 return outcomes,sensitivity

def integrated_audit(inp:dict[str,Any],cfg:dict[str,Any],r:dict[str,np.ndarray],outcomes:dict[str,Any],sens:dict[str,Any])->dict[str,Any]:
 checks=[]
 def ck(n,c,d=None):checks.append({'name':n,'pass':bool(c),'detail':d})
 X=r['community_summary'];age=r['age_ka'];A=r['community_anchor_state']
 ck('parent_r328_sealed',inp['a328']['status']==PARENT_PASS)
 ck('r323_functional_parent_sealed',inp['a323']['verdict']=='SEALED')
 ck('candidate_cohort_exact',inp['candidate_ids']==EXPECTED_CANDIDATES)
 ck('member_count_exact',X.shape[0]==EXPECTED_MEMBERS)
 ck('time_window_50ka_to_0',abs(age[0]-50)<1e-12 and abs(age[-1])<1e-12)
 ck('time_subset_parent_exact',np.all(np.isin(age,np.asarray(inp['z28']['age_ka'],float))))
 ck('community_geometry',X.shape==(32,2,len(age),len(TIME_NAMES)),X.shape)
 ck('all_indices_finite',np.isfinite(X).all() and np.isfinite(A).all())
 ck('bounded_indices',np.min(X)>=0 and np.max(X)<=1 and np.min(A[...,3:])>=0 and np.max(A[...,3:])<=1,[float(np.min(X)),float(np.max(X))])
 ck('spatial_anchor_geometry',A.shape[0]==32 and A.shape[1]==2 and A.shape[3]==6 and A.shape[-1]==len(ANCHOR_NAMES),A.shape)
 ck('spatial_anchor_parent_positions_exact',np.max(np.abs(A[...,:3]-np.asarray(inp['z28']['snapshot_deme_state'][:,:,np.asarray(inp['z28']['snapshot_age_ka'])<=50,:,:3],float)))<1e-5)
 ck('functional_priors_from_r323_only',r['functional_priors'].shape==(32,2,6))
 ck('no_literal_census_materialized',cfg['absolute_census_calibration_materialized'] is False)
 ck('no_literal_camp_headcounts_materialized',cfg['absolute_camp_headcounts_materialized'] is False)
 ck('preconditions_not_culture_identity',cfg['language_materialized'] is False and cfg['religion_materialized'] is False and cfg['agriculture_materialized'] is False and cfg['city_state_materialized'] is False)
 ck('no_unique_human_identity',cfg['unique_human_identity_materialized'] is False)
 ck('deep_off',cfg['deep_biological_coupling'] is False)
 ck('parents_immutable',all(cfg[k] is False for k in ('h0_mutation','cha2_mutation','r323_mutation','r328_mutation')))
 ck('cha2_inherited_from_direct_parent',cfg['cha2_exposure_source']=='R328_DIRECT_50Y_POPULATION_WEIGHTED_HAZARD_AND_DISPLACEMENT')
 ck('sensitivity_count',sens['variant_count']==len(cfg['sensitivity_multipliers']))
 ck('outcomes_two_unique',len(outcomes['candidates'])==2 and {x['species_id'] for x in outcomes['candidates']}==set(EXPECTED_CANDIDATES))
 ck('cohort_subset_parent',set(outcomes['community_precondition_cohort']).issubset(set(EXPECTED_CANDIDATES)),outcomes['community_precondition_cohort'])
 ck('no_forced_single_lineage',outcomes['unique_cultural_human_identity_materialized'] is False)
 ck('evidence_multisource',len(EVIDENCE)>=5)
 failed=[x for x in checks if not x['pass']]
 return {'stage':STAGE,'audit':'INTEGRATED_POPULATION_MOBILITY_SETTLEMENT_AND_CULTURAL_PRECONDITIONS','status':CANDIDATE_PASS if not failed else 'FAIL_R329_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'candidate_lineages':2,'ensemble_members':32,'time_states':len(age),'community_precondition_cohort':outcomes['community_precondition_cohort'],'robust_priority_cohort':outcomes['robust_priority_cohort'],'cultural_identity_materialized':False,'absolute_census_materialized':False,'deep_biological_coupling':False},'checks':checks}

def build_outputs(inp:dict[str,Any],cfg:dict[str,Any],r:dict[str,np.ndarray],outcomes:dict[str,Any],sens:dict[str,Any],out:Path)->None:
 out.mkdir(parents=True,exist_ok=True)
 authority={'stage':STAGE,'status':'POPULATION_MOBILITY_SETTLEMENT_AND_CULTURAL_PRECONDITIONS_AUTHORITY','parent':PARENT_PASS,'candidate_cohort':inp['candidate_ids'],'time_window_ka':[50.0,0.0],'state_semantics':'DIMENSIONLESS_COMMUNITY_AND_CULTURAL_PRECONDITION_INDICES_CONDITIONED_ON_R328_POPULATION_REPLAY','spatial_semantics':'R328_EXPLICIT_DEME_SNAPSHOT_ANCHORS_ONLY_NO_INVENTED_CONTINUOUS_DEME_PATHS','population_semantics':'R328_POPULATION_PROXY_NOT_LITERAL_CENSUS','settlement_semantics':'PERSISTENCE_POTENTIAL_NOT_ARCHAEOLOGICALLY_OBSERVED_SETTLEMENT','culture_semantics':'TRANSMISSION_AND_CUMULATION_PRECONDITIONS_NOT_LANGUAGE_RELIGION_TECHNOLOGY_OR_CULTURAL_IDENTITY','cha2_semantics':'INHERITED_FROM_R328_DIRECT_50Y_POPULATION_WEIGHTED_HAZARD_AND_DISPLACEMENT','deep_biological_coupling':False,'human_similarity_target':False,'unique_human_identity_materialized':False,'evidence_basis':EVIDENCE}
 write_json(out/'R3_29_COMMUNITY_PRECONDITION_AUTHORITY.json',authority);write_json(out/'R3_29_LINEAGE_COMMUNITY_OUTCOMES.json',outcomes);write_json(out/'R3_29_SENSITIVITY_AND_ROBUSTNESS.json',sens)
 np.savez_compressed(out/'R3_29_COMMUNITY_NETWORK_REPLAY.npz',candidate_ids=np.asarray(inp['candidate_ids']),parent_member_indices=inp['parent_member_indices'],age_ka=r['age_ka'],community_variable_names=np.asarray(TIME_NAMES),community_summary=r['community_summary'],functional_prior_names=r['functional_prior_names'],functional_priors=r['functional_priors'],anchor_age_ka=r['anchor_age_ka'],community_anchor_variable_names=np.asarray(ANCHOR_NAMES),community_anchor_state=r['community_anchor_state'],community_anchor_active=r['community_anchor_active'])
 audit=integrated_audit(inp,cfg,r,outcomes,sens);write_json(out/'R3_29_INTEGRATED_AUDIT.json',audit);write_json(out/'R3_29_COMMUNITY_PRECONDITION_CHECKPOINT.json',{'stage':STAGE,'status':'COMMUNITY_AND_CULTURAL_PRECONDITION_CHECKPOINT_0KA','age_ka':0.0,'candidate_cohort':outcomes['community_precondition_cohort'],'candidate_count':len(outcomes['community_precondition_cohort']),'unique_human_identity':None,'unique_human_identity_materialized':False,'language_materialized':False,'religion_materialized':False,'agriculture_materialized':False,'city_state_materialized':False})
 (out/'R3_29_AUDIT.md').write_text(f"# R3.29 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n- Cultural identity materialized: **NO**\n",encoding='utf-8')

def write_manifest(out:Path,status:str)->None:
 names=['R3_29_AUDIT.md','R3_29_COMMUNITY_PRECONDITION_AUTHORITY.json','R3_29_COMMUNITY_PRECONDITION_CHECKPOINT.json','R3_29_COMMUNITY_NETWORK_REPLAY.npz','R3_29_INTEGRATED_AUDIT.json','R3_29_LINEAGE_COMMUNITY_OUTCOMES.json','R3_29_SENSITIVITY_AND_ROBUSTNESS.json']
 write_json(out/'R3_29_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':{n:{'bytes':(out/n).stat().st_size,'sha256':sha256_file(out/n)} for n in names}})
