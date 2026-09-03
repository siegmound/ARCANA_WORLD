from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json
import numpy as np

STAGE='v0.6D1-R3.31'
PARENT_STAGE='v0.6D1-R3.30'
PARENT_PASS='PASS_R330_CENSUS_EQUIVALENT_CALIBRATION_WEIGHTED_GROUP_ABM_LATE_PLEISTOCENE_COMMUNITY_HISTORY_AND_CHA2_GROUP_EXPOSURE_SEALED'
CANDIDATE_PASS='PASS_R331_CULTURAL_TECHNOLOGICAL_ECOLOGY_CANDIDATE'
FINAL_PASS='PASS_R331_LATE_PLEISTOCENE_TO_HOLOCENE_CULTURAL_TECHNOLOGICAL_ECOLOGY_TRANSMISSION_RETENTION_AND_TECHNICAL_REPERTOIRE_SEALED'
EXPECTED_PARENT_CHECKS=27
EXPECTED_CANDIDATES=['RPT_010_D02','RPT_009_D02']
EXPECTED_MEMBERS=32
TECH_NAMES=['portable_toolkit_systems','composite_tool_systems','food_processing_and_extraction','thermal_environmental_control','shelter_and_site_engineering','transport_and_logistical_systems','storage_and_resource_buffering','cooperative_specialization_systems']
ECO_NAMES=['transmission_fidelity','innovation_opportunity','retention_support','repertoire_breadth','technical_resilience','niche_buffering','specialization_potential','interlineage_diffusion_opportunity','innovation_flux_equivalent','loss_flux_equivalent']
GROUP_NAMES=['represented_people','represented_camps','tech_access','repertoire_breadth','technical_resilience','specialization_access','innovation_support','interlineage_transfer_access']

EVIDENCE={
 'HG_TRANSMISSION_2024':{'source':'Hewlett et al. 2024 Cultural transmission among hunter-gatherers','pmcid':'PMC11621818','use':'multiple transmission modes conserve traits and support cumulative culture without requiring named cultural identities'},
 'CUMULATIVE_CULTURE_FORAGING_NICHE_2021':{'source':'Miguel et al. 2021 The origins of human cumulative culture','pmcid':'PMC8666907','use':'multilevel mobile social networks, between-camp connectivity, network memory, recombination and specialization support cumulative culture'},
 'NETWORK_ARCHITECTURE_CCE_2021':{'source':'Derex & Mesoudi related network architecture review/model','pmcid':'PMC7944107','use':'population structure and transmission mechanism jointly control accumulation, diffusion and loss'},
 'DEMOGRAPHY_CCE_CAUTION_2012':{'source':'Vaesen 2012 Cumulative Cultural Evolution and Demography','pmcid':'PMC3404092','use':'demography modulates cultural accumulation but simple critical-threshold claims require robustness testing'},
 'COMPLEXITY_DEMOGRAPHY_CAUTION_2014':{'source':'Vaesen et al. 2014 Complexity and Demographic Explanations','pmcid':'PMC4105626','use':'technology complexity cannot be reduced to population size alone'},
 'HG_TECH_ECOLOGY_2018':{'source':'Tallavaara et al./Hamilton et al. hunter-gatherer ecology review','pmcid':'PMC5819456','use':'technology alters ecological constraints; forager density and ecology provide context for technical repertoires'},
 'HG_NETWORK_HIERARCHY_2009':{'source':'Hamilton et al. 2009 Proc R Soc B','pmcid':'PMC2706200','use':'nested fission-fusion networks support information movement across residential and regional scales'},
 'POTTERY_TRANSMISSION_HG_2022':{'source':'Dolbunova et al. 2022 Nature Human Behaviour','doi':'10.1038/s41562-022-01491-8','use':'hunter-gatherer technologies can spread through super-regional cultural transmission networks before agriculture or urbanism'}
}

class R331GateError(RuntimeError):pass

def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load_json(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def _close_manifest(d:Path,name:str)->None:
 p=d/name
 if not p.is_file():raise R331GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file() or fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:raise R331GateError(f'Manifest closure failure {fp}')

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root);r30=root/'outputs'/'v0_6D1_R3_30';s30=root/'outputs'/'v0_6D1_R3_30_SEAL';r29=root/'outputs'/'v0_6D1_R3_29';r23=root/'outputs'/'v0_6D1_R3_23'
 for d in (r30,s30,r29,r23):
  if not d.is_dir():raise R331GateError(f'Missing required directory {d}')
 a30=load_json(s30/'R3_30_FINAL_SEAL_AUDIT.json')
 if a30.get('stage')!=PARENT_STAGE or a30.get('status')!=PARENT_PASS or a30.get('verdict')!='SEALED' or a30.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a30.get('checks_failed')!=0:raise R331GateError('R3.30 seal mismatch')
 _close_manifest(r30,'R3_30_OUTPUT_MANIFEST.json');_close_manifest(r29,'R3_29_OUTPUT_MANIFEST.json');_close_manifest(r23,'R3_23_OUTPUT_MANIFEST.json')
 cp=load_json(r30/'R3_30_COMMUNITY_HISTORY_CHECKPOINT.json')
 if cp.get('candidate_cohort')!=EXPECTED_CANDIDATES or cp.get('unique_human_identity_materialized') is not False:raise R331GateError('R3.30 cohort mismatch')
 z30=np.load(r30/'R3_30_CENSUS_AND_GROUP_TIMESERIES.npz',allow_pickle=False);g30=np.load(r30/'R3_30_WEIGHTED_GROUP_ABM.npz',allow_pickle=False);z29=np.load(r29/'R3_29_COMMUNITY_NETWORK_REPLAY.npz',allow_pickle=False);z23=np.load(r23/'R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz',allow_pickle=False)
 if list(map(str,z30['candidate_ids']))!=EXPECTED_CANDIDATES or z30['census_group_series'].shape[:2]!=(32,2):raise R331GateError('R3.30 geometry mismatch')
 if not np.array_equal(z30['age_ka'],z29['age_ka']):raise R331GateError('R3.29/R3.30 time mismatch')
 # R3.23 candidate order contains both lineages; derive species indices for the same 32 parent members.
 s23=list(map(str,z23['species_ids']));ix23=[s23.index(x) for x in EXPECTED_CANDIDATES]
 return {'root':root,'r30':r30,'r29':r29,'r23':r23,'a30':a30,'z30':z30,'g30':g30,'z29':z29,'z23':z23,'ix23':ix23}

def _functional_priors(inp:dict[str,Any])->np.ndarray:
 z29=inp['z29'];return np.asarray(z29['functional_priors'],float)

def _domain_affordances(inp:dict[str,Any])->np.ndarray:
 z29=inp['z29'];C=np.asarray(z29['community_summary'],float);names=list(map(str,z29['community_variable_names']));ix={n:i for i,n in enumerate(names)};F=_functional_priors(inp);fn=list(map(str,z29['functional_prior_names']));fi={n:i for i,n in enumerate(fn)}
 mob=C[...,ix['residential_mobility_index']];agg=C[...,ix['aggregation_potential']];net=C[...,ix['network_connectivity']];tr=C[...,ix['cultural_transmission_support']];stock=C[...,ix['cumulative_culture_precondition_stock']];sett=C[...,ix['settlement_persistence_potential']];stress=C[...,ix['resource_stress_proxy']]
 social=F[:,:,fi['social_learning']][:,:,None];coord=F[:,:,fi['coordination']][:,:,None];flex=F[:,:,fi['flexibility']][:,:,None];dev=F[:,:,fi['development']][:,:,None];cog=F[:,:,fi['cognition']][:,:,None]
 A=[]
 A.append(.23*cog+.20*flex+.22*mob+.15*tr+.10*net+.10*stock)
 A.append(.30*cog+.20*social+.16*coord+.15*tr+.10*net+.09*stock)
 A.append(.24*flex+.18*cog+.18*stress+.16*stock+.12*sett+.12*tr)
 A.append(.20*cog+.22*stress+.18*stock+.14*sett+.12*flex+.14*tr)
 A.append(.18*coord+.17*cog+.22*sett+.16*stress+.14*stock+.13*net)
 A.append(.24*cog+.19*mob+.20*net+.14*coord+.13*stock+.10*tr)
 A.append(.20*cog+.24*sett+.19*stress+.10*net+.17*stock+.10*tr)
 A.append(.25*coord+.18*social+.21*net+.12*dev+.13*stock+.11*tr)
 return np.clip(np.stack(A,axis=-1),0,1)

def replay_technology(inp:dict[str,Any],cfg:dict[str,Any],rate_mult:float=1.0,loss_mult:float=1.0)->dict[str,np.ndarray]:
 z29=inp['z29'];z30=inp['z30'];age=np.asarray(z30['age_ka'],float);C=np.asarray(z29['community_summary'],float);cn=list(map(str,z29['community_variable_names']));ci={n:i for i,n in enumerate(cn)};census=np.asarray(z30['census_group_series'][...,0],float);groups=np.asarray(z30['census_group_series'][...,2],float);A=_domain_affordances(inp);n,m,T,D=A.shape
 F=_functional_priors(inp);fn=list(map(str,z29['functional_prior_names']));fi={n:i for i,n in enumerate(fn)}
 stock=np.zeros((n,m,T,D),float)
 base_culture=C[:,:,0,ci['cumulative_culture_precondition_stock']]
 stock[:,:,0,:]=np.clip(.06+.27*base_culture[:,:,None]+.18*A[:,:,0,:],0,1)
 innovation_flux=np.zeros((n,m,T),float);loss_flux=np.zeros((n,m,T),float)
 ir=float(cfg['innovation_rate_per_kyr'])*rate_mult;lr=float(cfg['loss_rate_per_kyr'])*loss_mult;xr=float(cfg['cross_lineage_transfer_rate_per_kyr'])
 # Relative demographic support is log-scaled within the full ensemble, not a hard threshold.
 lpop=np.log1p(census);pmin=float(np.min(lpop));pmax=float(np.max(lpop));pdem=(lpop-pmin)/max(pmax-pmin,1e-12)
 for t in range(1,T):
  dt=max(float(age[t-1]-age[t]),0.0)
  prev=stock[:,:,t-1,:]
  tr=C[:,:,t,ci['cultural_transmission_support']];net=C[:,:,t,ci['network_connectivity']];stress=C[:,:,t,ci['resource_stress_proxy']];dis=C[:,:,t,ci['cha2_community_disruption']];ex=C[:,:,t,ci['interlineage_exchange_opportunity']];cult=C[:,:,t,ci['cumulative_culture_precondition_stock']]
  retention=np.clip(.20+.30*tr+.20*net+.18*cult+.12*(1-stress),0,1)
  innovation=ir*dt*A[:,:,t,:]*(.35+.65*tr[:,:,None])*(.45+.55*net[:,:,None])*(.55+.45*pdem[:,:,t,None])*(1-prev)
  loss=lr*dt*(.25+.45*stress[:,:,None]+.65*dis[:,:,None]+.25*(1-net[:,:,None]))*(1-.55*retention[:,:,None])*prev
  transfer=np.zeros_like(prev)
  # Same symmetric opportunity field; only positive gaps diffuse, preventing forced homogenization.
  for j in range(2):
   o=1-j;gap=np.maximum(prev[:,o,:]-prev[:,j,:],0);transfer[:,j,:]=xr*dt*ex[:,j,None]*net[:,j,None]*gap
  cur=np.clip(prev+innovation+transfer-loss,float(cfg['stock_floor']),float(cfg['stock_ceiling']))
  stock[:,:,t,:]=cur
  innovation_flux[:,:,t]=np.sum(np.maximum(cur-prev,0),axis=-1)*groups[:,:,t]
  loss_flux[:,:,t]=np.sum(np.maximum(prev-cur,0),axis=-1)*groups[:,:,t]
 # ecology metrics
 tr=C[...,ci['cultural_transmission_support']];net=C[...,ci['network_connectivity']];stress=C[...,ci['resource_stress_proxy']];dis=C[...,ci['cha2_community_disruption']];ex=C[...,ci['interlineage_exchange_opportunity']];mob=C[...,ci['residential_mobility_index']];agg=C[...,ci['aggregation_potential']]
 social=F[:,:,fi['social_learning']][:,:,None];cog=F[:,:,fi['cognition']][:,:,None];flex=F[:,:,fi['flexibility']][:,:,None];coord=F[:,:,fi['coordination']][:,:,None]
 fidelity=np.clip(.35*tr+.25*social+.22*net+.10*agg+.08*(1-stress),0,1)
 innovopp=np.clip(.28*cog+.22*flex+.18*net+.14*mob+.10*stress+.08*tr,0,1)
 retain=np.clip(.34*fidelity+.22*net+.18*(1-stress)+.16*(1-dis)+.10*agg,0,1)
 breadth=np.mean(stock>=float(cfg['repertoire_operational_threshold']),axis=-1)
 resilience=np.clip(np.mean(stock,axis=-1)*(.45+.30*retain+.25*(1-stress)),0,1)
 buffering=np.mean(stock[..., [2,3,4,6]],axis=-1)
 specialization=np.clip(.35*stock[...,7]+.25*stock[...,1]+.20*coord+.20*net,0,1)
 diffusion=np.clip(ex*net*.5*(stock[...,0]+stock[...,5]),0,1)
 eco=np.stack([fidelity,innovopp,retain,breadth,resilience,buffering,specialization,diffusion,innovation_flux,loss_flux],axis=-1)
 return {'age_ka':age,'domain_stock':stock,'ecology':eco,'affordance':A}

def build_group_anchors(inp:dict[str,Any],tech:dict[str,np.ndarray])->dict[str,np.ndarray]:
 g=inp['g30'];ages=np.asarray(g['anchor_age_ka'],float);A=np.asarray(g['agent_state'],float);active=np.asarray(g['agent_active'],np.uint8);av=list(map(str,g['agent_variable_names']));ai={n:i for i,n in enumerate(av)};time=tech['age_ka'];stock=tech['domain_stock'];eco=tech['ecology'];out=np.zeros((32,2,len(ages),48,len(GROUP_NAMES)),float)
 for k,a in enumerate(ages):
  ti=int(np.where(np.isclose(time,a,atol=1e-10))[0][0])
  for e in range(32):
   for j in range(2):
    tech_mean=float(np.mean(stock[e,j,ti]));breadth=float(eco[e,j,ti,ECO_NAMES.index('repertoire_breadth')]);res=float(eco[e,j,ti,ECO_NAMES.index('technical_resilience')]);spec=float(eco[e,j,ti,ECO_NAMES.index('specialization_potential')]);innov=float(eco[e,j,ti,ECO_NAMES.index('innovation_opportunity')]);diff=float(eco[e,j,ti,ECO_NAMES.index('interlineage_diffusion_opportunity')])
    for q in range(48):
     if not active[e,j,k,q]:continue
     net=float(A[e,j,k,q,ai['network_access']]);cult=float(A[e,j,k,q,ai['culture_stock']]);stress=float(A[e,j,k,q,ai['resource_stress']]);x=float(A[e,j,k,q,ai['interlineage_exchange']])
     access=np.clip(tech_mean*(.55+.25*net+.20*cult),0,1);rb=np.clip(breadth*(.65+.20*net+.15*cult),0,1);rr=np.clip(res*(.70+.20*net+.10*(1-stress)),0,1);sp=np.clip(spec*(.70+.20*net+.10*cult),0,1);iv=np.clip(innov*(.60+.25*net+.15*cult),0,1);tx=np.clip(diff*(.5+.5*x)*(.6+.4*net),0,1)
     out[e,j,k,q]=[A[e,j,k,q,ai['represented_people']],A[e,j,k,q,ai['represented_camps']],access,rb,rr,sp,iv,tx]
 return {'anchor_age_ka':ages,'group_state':out,'group_active':active.copy()}

def summarize(inp:dict[str,Any],cfg:dict[str,Any],tech:dict[str,np.ndarray],groups:dict[str,np.ndarray])->tuple[dict[str,Any],dict[str,Any]]:
 age=tech['age_ka'];S=tech['domain_stock'];E=tech['ecology'];out=[]
 for j,sid in enumerate(EXPECTED_CANDIDATES):
  final=np.mean(S[:,j,-1,:],axis=1);breadth=E[:,j,-1,ECO_NAMES.index('repertoire_breadth')];res=E[:,j,-1,ECO_NAMES.index('technical_resilience')];buf=E[:,j,-1,ECO_NAMES.index('niche_buffering')]
  out.append({'species_id':sid,'final_domain_stock_mean_median':float(np.median(final)),'final_domain_stock_mean_q10_q90':[float(x) for x in np.quantile(final,[.1,.9])],'final_repertoire_breadth_median':float(np.median(breadth)),'final_technical_resilience_median':float(np.median(res)),'final_niche_buffering_median':float(np.median(buf)),'interpretation':'ABSTRACT_FUNCTIONAL_TECHNOLOGICAL_ECOLOGY_NOT_SPECIFIC_ARTIFACT_INVENTORY'})
 outcomes={'stage':STAGE,'status':'CULTURAL_TECHNOLOGICAL_ECOLOGY_OUTCOMES','candidate_lineages':EXPECTED_CANDIDATES,'lineages':out,'named_culture_materialized':False,'specific_artifact_materialized':False,'unique_human_identity_materialized':False}
 # 25 sensitivity combinations, diagnostic only. Reuse mean final stocks rather than selecting a lineage.
 variants=[]
 for rm in cfg['sensitivity_rate_multipliers']:
  for lm in cfg['sensitivity_loss_multipliers']:
   t=replay_technology(inp,cfg,float(rm),float(lm));v=[]
   for j,sid in enumerate(EXPECTED_CANDIDATES):
    v.append({'species_id':sid,'final_stock_median':float(np.median(np.mean(t['domain_stock'][:,j,-1,:],axis=-1))),'final_breadth_median':float(np.median(t['ecology'][:,j,-1,ECO_NAMES.index('repertoire_breadth')]))})
   variants.append({'innovation_rate_multiplier':rm,'loss_rate_multiplier':lm,'lineages':v})
 sens={'stage':STAGE,'status':'CULTURAL_TECHNOLOGICAL_ECOLOGY_SENSITIVITY','variant_count':len(variants),'selection_gate':False,'candidate_retention':EXPECTED_CANDIDATES,'variants':variants}
 return outcomes,sens

def integrated_audit(inp:dict[str,Any],cfg:dict[str,Any],tech:dict[str,np.ndarray],groups:dict[str,np.ndarray],outcomes:dict[str,Any],sens:dict[str,Any])->dict[str,Any]:
 checks=[]
 def ck(n,c,d=None):checks.append({'name':n,'pass':bool(c),'detail':d})
 S=tech['domain_stock'];E=tech['ecology'];G=groups['group_state'];GA=groups['group_active']
 ck('parent_r330_sealed',inp['a30']['status']==PARENT_PASS)
 ck('candidate_order_exact',list(map(str,inp['z30']['candidate_ids']))==EXPECTED_CANDIDATES)
 ck('member_count_exact',S.shape[0]==EXPECTED_MEMBERS)
 ck('time_axis_exact',np.array_equal(tech['age_ka'],inp['z30']['age_ka']))
 ck('technology_domains_exact',cfg['technology_domains']==TECH_NAMES)
 ck('domain_stock_geometry',S.shape==(32,2,175,8),S.shape)
 ck('ecology_geometry',E.shape==(32,2,175,10),E.shape)
 ck('all_numeric_finite',np.isfinite(S).all() and np.isfinite(E).all() and np.isfinite(G).all())
 ck('domain_stock_bounded',np.min(S)>=0 and np.max(S)<=1,[float(np.min(S)),float(np.max(S))])
 ck('bounded_ecology_fields',np.min(E[...,:8])>=0 and np.max(E[...,:8])<=1)
 ck('flux_nonnegative',np.min(E[...,8:])>=0)
 ck('group_anchor_geometry',G.shape==(32,2,11,48,8),G.shape)
 ck('group_active_exact_parent',np.array_equal(GA,inp['g30']['agent_active']))
 ck('group_people_camps_preserved',np.max(np.abs(G[...,0]-inp['g30']['agent_state'][...,0]))<1e-10 and np.max(np.abs(G[...,1]-inp['g30']['agent_state'][...,1]))<1e-10)
 ck('group_tech_metrics_bounded',np.min(G[...,2:])>=0 and np.max(G[...,2:])<=1)
 ck('sensitivity_25_variants',sens['variant_count']==25)
 ck('sensitivity_not_selection_gate',sens['selection_gate'] is False)
 ck('both_lineages_retained',sens['candidate_retention']==EXPECTED_CANDIDATES)
 ck('technology_semantics_abstract',cfg['technology_semantics'].startswith('ABSTRACT_'))
 ck('culture_semantics_not_named',cfg['culture_semantics'].endswith('NOT_NAMED_CULTURE_OR_LANGUAGE'))
 ck('specific_artifact_not_materialized',cfg['specific_artifact_materialized'] is False)
 ck('no_language_religion_agriculture_city',all(cfg[k] is False for k in ('language_materialized','religion_materialized','agriculture_materialized','city_state_materialized')))
 ck('no_ethnicity_named_culture',cfg['ethnicity_materialized'] is False and cfg['named_culture_materialized'] is False)
 ck('no_unique_human_identity',cfg['unique_human_identity_materialized'] is False)
 ck('deep_off',cfg['deep_biological_coupling'] is False)
 ck('parent_immutable',all(cfg[k] is False for k in ('h0_mutation','cha2_mutation','r328_mutation','r329_mutation','r330_mutation')))
 ck('evidence_multisource',len(EVIDENCE)>=8)
 failed=[x for x in checks if not x['pass']]
 return {'stage':STAGE,'audit':'INTEGRATED_LATE_PLEISTOCENE_TO_HOLOCENE_CULTURAL_TECHNOLOGICAL_ECOLOGY','status':CANDIDATE_PASS if not failed else 'FAIL_R331_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'candidate_lineages':2,'ensemble_members':32,'time_states':175,'technology_domains':8,'group_anchor_states':11,'named_culture_materialized':False,'specific_artifact_materialized':False,'agriculture_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False},'checks':checks}

def build_outputs(inp:dict[str,Any],cfg:dict[str,Any],tech:dict[str,np.ndarray],groups:dict[str,np.ndarray],outcomes:dict[str,Any],sens:dict[str,Any],out:Path)->dict[str,Any]:
 out.mkdir(parents=True,exist_ok=True)
 auth={'stage':STAGE,'status':'CULTURAL_TECHNOLOGICAL_ECOLOGY_AUTHORITY','parent':PARENT_PASS,'candidate_cohort':EXPECTED_CANDIDATES,'time_window_ka':[50.0,0.0],'technology_domains':TECH_NAMES,'technology_semantics':cfg['technology_semantics'],'culture_semantics':cfg['culture_semantics'],'dynamics':{'innovation_rate_per_kyr':cfg['innovation_rate_per_kyr'],'loss_rate_per_kyr':cfg['loss_rate_per_kyr'],'cross_lineage_transfer_rate_per_kyr':cfg['cross_lineage_transfer_rate_per_kyr'],'repertoire_operational_threshold':cfg['repertoire_operational_threshold']},'specific_artifact_materialized':False,'language_materialized':False,'religion_materialized':False,'agriculture_materialized':False,'city_state_materialized':False,'ethnicity_materialized':False,'named_culture_materialized':False,'unique_human_identity_materialized':False,'human_similarity_target':False,'deep_biological_coupling':False,'evidence_basis':EVIDENCE}
 write_json(out/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_AUTHORITY.json',auth);write_json(out/'R3_31_LINEAGE_TECHNOLOGICAL_ECOLOGY_OUTCOMES.json',outcomes);write_json(out/'R3_31_SENSITIVITY_AND_ROBUSTNESS.json',sens)
 np.savez_compressed(out/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz',candidate_ids=np.asarray(EXPECTED_CANDIDATES),parent_member_indices=np.asarray(inp['z30']['parent_member_indices']),age_ka=tech['age_ka'],technology_domain_names=np.asarray(TECH_NAMES),technology_domain_stock=tech['domain_stock'],ecology_variable_names=np.asarray(ECO_NAMES),cultural_technological_ecology=tech['ecology'])
 np.savez_compressed(out/'R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz',candidate_ids=np.asarray(EXPECTED_CANDIDATES),parent_member_indices=np.asarray(inp['z30']['parent_member_indices']),anchor_age_ka=groups['anchor_age_ka'],group_variable_names=np.asarray(GROUP_NAMES),group_state=groups['group_state'],group_active=groups['group_active'])
 audit=integrated_audit(inp,cfg,tech,groups,outcomes,sens);write_json(out/'R3_31_INTEGRATED_AUDIT.json',audit)
 cp={'stage':STAGE,'status':'CULTURAL_TECHNOLOGICAL_ECOLOGY_CHECKPOINT_0KA','age_ka':0.0,'candidate_cohort':EXPECTED_CANDIDATES,'candidate_count':2,'technology_domains_materialized':TECH_NAMES,'specific_artifact_materialized':False,'named_culture_materialized':False,'language_materialized':False,'religion_materialized':False,'agriculture_materialized':False,'city_state_materialized':False,'unique_human_identity':None,'unique_human_identity_materialized':False}
 write_json(out/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_CHECKPOINT.json',cp)
 (out/'R3_31_AUDIT.md').write_text(f"# R3.31 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n- Abstract technology domains: **8**\n- Specific artifact claims: **NO**\n- Named cultures/languages/religions/agriculture/states: **NO**\n",encoding='utf-8')
 return audit

def write_manifest(out:Path,status:str)->None:
 names=['R3_31_AUDIT.md','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_AUTHORITY.json','R3_31_LINEAGE_TECHNOLOGICAL_ECOLOGY_OUTCOMES.json','R3_31_SENSITIVITY_AND_ROBUSTNESS.json','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz','R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz','R3_31_INTEGRATED_AUDIT.json','R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_CHECKPOINT.json']
 write_json(out/'R3_31_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':{n:{'bytes':(out/n).stat().st_size,'sha256':sha256_file(out/n)} for n in names}})
