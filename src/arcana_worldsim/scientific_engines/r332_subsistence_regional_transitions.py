from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib,json
import numpy as np

STAGE='v0.6D1-R3.32'
PARENT_STAGE='v0.6D1-R3.31'
PARENT_PASS='PASS_R331_LATE_PLEISTOCENE_TO_HOLOCENE_CULTURAL_TECHNOLOGICAL_ECOLOGY_TRANSMISSION_RETENTION_AND_TECHNICAL_REPERTOIRE_SEALED'
CANDIDATE_PASS='PASS_R332_SUBSISTENCE_INTENSIFICATION_REGIONAL_CULTURAL_LINEAGES_AND_HOLOCENE_TRANSITIONS_CANDIDATE'
FINAL_PASS='PASS_R332_SUBSISTENCE_INTENSIFICATION_REGIONAL_CULTURAL_LINEAGES_MANAGED_RESOURCE_TRANSITIONS_AND_HOLOCENE_READINESS_SEALED'
EXPECTED_PARENT_CHECKS=29
EXPECTED_CANDIDATES=['RPT_010_D02','RPT_009_D02']
EXPECTED_MEMBERS=32
SUB_NAMES=['high_return_capture_systems','broad_spectrum_foraging','plant_resource_processing_intensity','aquatic_resource_exploitation','delayed_return_storage_buffering','landscape_resource_management','seasonal_scheduling_and_logistics','cooperative_provisioning_specialization']
ECO_NAMES=['broad_spectrum_index','subsistence_intensification','delayed_return_economy_potential','managed_resource_intensity','settlement_commitment','regional_differentiation','regional_continuity','food_production_transition_readiness','subsistence_resilience','interlineage_subsistence_exchange']
REGION_NAMES=['represented_people','represented_camps','grid_row','grid_col','regional_lineage_code','subsistence_profile_mean','subsistence_intensification','managed_resource_readiness','tech_access','regional_continuity']

EVIDENCE={
 'BROAD_SPECTRUM_REVIEW':{'source':'Stiner 2001 Thirty years on the Broad Spectrum Revolution','pmcid':'PMC34611','use':'diet breadth and intensification can expand before food production and should not be equated with agriculture'},
 'AGRICULTURAL_ORIGINS_CAUTION':{'source':'Gremillion et al. 2014 Particularism and theory in agricultural origins','pmcid':'PMC4035987','use':'broad-spectrum change and optimal-foraging mechanisms are regionally variable and not a single universal transition'},
 'LAND_USE_INTENSIFICATION':{'source':'Ellis et al. 2013 Used planet: a global history','pmcid':'PMC3657770','use':'late-Pleistocene foragers can intensify land and resource use before agriculture'},
 'PUNCTUATED_SUBSISTENCE':{'source':'Weitzel & Codding 2015 Toward a theory of punctuated subsistence change','pmcid':'PMC4534222','use':'landscape management, storage and decreased mobility may precondition but do not guarantee food production'},
 'PROTRACTED_DOMESTICATION':{'source':'Fuller et al. 2017 Geographic mosaics and changing rates of cereal domestication','pmcid':'PMC5665816','use':'domestication is protracted, geographically mosaic and cannot be represented as an instantaneous threshold'},
 'MULTIREGIONAL_CULTIVATION':{'source':'Arranz-Otaegui et al./Riehl-related 2016 regional diversity in early cultivation','pmcid':'PMC5150421','use':'cultivation and domestication trajectories vary regionally and can proceed in parallel'},
 'SEDENTISM_BEFORE_DOMESTICATION':{'source':'Fuller et al. 2014 Convergent evolution and parallelism in plant domestication','pmcid':'PMC4035951','use':'sedentism or persistent sites can predate morphological domestication'},
 'DOMESTICATION_PROCESS_REVIEW':{'source':'Kantar et al. 2018 Genomic approaches for studying crop evolution','pmcid':'PMC6151037','use':'domestication should be treated as a prolonged evolutionary process with gene flow and multiple stages'},
 'STORAGE_RISK_BUFFERING':{'source':'Rowley-Conwy & Zvelebil, storage by prehistoric hunter-gatherers','doi':'10.1017/CBO9780511521218.004','use':'storage is a risk-buffering strategy and not synonymous with agriculture'}
}

class R332GateError(RuntimeError):pass

def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def load_json(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def _close_manifest(d:Path,name:str)->None:
 p=d/name
 if not p.is_file():raise R332GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file() or fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:raise R332GateError(f'Manifest closure failure {fp}')

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root);r31=root/'outputs'/'v0_6D1_R3_31';s31=root/'outputs'/'v0_6D1_R3_31_SEAL';r30=root/'outputs'/'v0_6D1_R3_30'
 for d in (r31,s31,r30):
  if not d.is_dir():raise R332GateError(f'Missing required directory {d}')
 a31=load_json(s31/'R3_31_FINAL_SEAL_AUDIT.json')
 if a31.get('stage')!=PARENT_STAGE or a31.get('status')!=PARENT_PASS or a31.get('verdict')!='SEALED' or a31.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a31.get('checks_failed')!=0:raise R332GateError('R3.31 seal mismatch')
 _close_manifest(r31,'R3_31_OUTPUT_MANIFEST.json');_close_manifest(r30,'R3_30_OUTPUT_MANIFEST.json')
 cp=load_json(r31/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_CHECKPOINT.json')
 if cp.get('candidate_cohort')!=EXPECTED_CANDIDATES or cp.get('unique_human_identity_materialized') is not False:raise R332GateError('R3.31 cohort mismatch')
 z31=np.load(r31/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz',allow_pickle=False);g31=np.load(r31/'R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz',allow_pickle=False);g30=np.load(r30/'R3_30_WEIGHTED_GROUP_ABM.npz',allow_pickle=False)
 if list(map(str,z31['candidate_ids']))!=EXPECTED_CANDIDATES or z31['technology_domain_stock'].shape!=(32,2,175,8):raise R332GateError('R3.31 geometry mismatch')
 sel=np.where(np.asarray(z31['age_ka'],float)<=20.0+1e-12)[0]
 if len(sel)!=145 or float(z31['age_ka'][sel[0]])!=20.0 or float(z31['age_ka'][sel[-1]])!=0.0:raise R332GateError('R3.32 time window mismatch')
 anchor_sel=np.where(np.asarray(g31['anchor_age_ka'],float)<=20.0+1e-12)[0]
 return {'root':root,'r31':r31,'r30':r30,'a31':a31,'z31':z31,'g31':g31,'g30':g30,'sel':sel,'anchor_sel':anchor_sel}

def _norm(x:np.ndarray)->np.ndarray:
 x=np.asarray(x,float);lo=np.nanmin(x);hi=np.nanmax(x);return np.clip((x-lo)/max(hi-lo,1e-12),0,1)

def _affordances(inp:dict[str,Any])->np.ndarray:
 z=inp['z31'];sel=inp['sel'];tech=np.asarray(z['technology_domain_stock'][:,:,sel,:],float);eco=np.asarray(z['cultural_technological_ecology'][:,:,sel,:],float);en=list(map(str,z['ecology_variable_names']));ei={n:i for i,n in enumerate(en)}
 tool=tech[...,0];comp=tech[...,1];food=tech[...,2];therm=tech[...,3];shel=tech[...,4];logi=tech[...,5];stor=tech[...,6];coop=tech[...,7]
 tr=eco[...,ei['transmission_fidelity']];innov=eco[...,ei['innovation_opportunity']];ret=eco[...,ei['retention_support']];res=eco[...,ei['technical_resilience']];buffer=eco[...,ei['niche_buffering']];spec=eco[...,ei['specialization_potential']];diff=eco[...,ei['interlineage_diffusion_opportunity']]
 A=[]
 A.append(.30*tool+.18*comp+.18*logi+.14*coop+.10*res+.10*innov)
 A.append(.21*food+.16*tool+.16*logi+.12*stor+.12*buffer+.12*innov+.11*tr)
 A.append(.36*food+.18*stor+.14*tool+.12*tr+.10*res+.10*buffer)
 A.append(.25*logi+.18*tool+.15*coop+.12*therm+.10*buffer+.10*innov+.10*diff)
 A.append(.34*stor+.18*shel+.15*food+.12*ret+.11*buffer+.10*tr)
 A.append(.20*food+.18*stor+.14*shel+.12*coop+.12*innov+.12*res+.12*buffer)
 A.append(.27*logi+.16*stor+.15*tool+.13*coop+.12*tr+.09*buffer+.08*res)
 A.append(.31*coop+.18*comp+.15*tr+.12*spec+.10*logi+.08*ret+.06*innov)
 return np.clip(np.stack(A,axis=-1),0,1)

def replay_subsistence(inp:dict[str,Any],cfg:dict[str,Any],rate_mult:float=1.0,threshold_offset:float=0.0)->dict[str,np.ndarray]:
 z=inp['z31'];sel=inp['sel'];age=np.asarray(z['age_ka'][sel],float);A=_affordances(inp);tech=np.asarray(z['technology_domain_stock'][:,:,sel,:],float);eco31=np.asarray(z['cultural_technological_ecology'][:,:,sel,:],float);en=list(map(str,z['ecology_variable_names']));ei={n:i for i,n in enumerate(en)}
 n,m,T,D=A.shape;stock=np.zeros((n,m,T,D),float);stock[:,:,0,:]=np.clip(.05+.34*A[:,:,0,:],0,1)
 ir=float(cfg['intensification_rate_per_kyr'])*rate_mult;lr=float(cfg['loss_rate_per_kyr']);mr=float(cfg['management_feedback_rate_per_kyr']);dr=float(cfg['regional_diffusion_rate_per_kyr'])
 for t in range(1,T):
  dt=max(float(age[t-1]-age[t]),0);prev=stock[:,:,t-1,:];res=eco31[:,:,t,ei['technical_resilience']];tr=eco31[:,:,t,ei['transmission_fidelity']];diff=eco31[:,:,t,ei['interlineage_diffusion_opportunity']]
  intens=ir*dt*A[:,:,t,:]*(.45+.55*res[:,:,None])*(1-prev)
  mg=mr*dt*np.maximum(prev[...,4:6].mean(axis=-1)-.28,0)[:,:,None]*A[:,:,t,:]*(1-prev)
  loss=lr*dt*(.55-.30*tr[:,:,None])*(.65+.35*(1-res[:,:,None]))*prev
  transfer=np.zeros_like(prev)
  for j in range(2):
   gap=np.maximum(prev[:,1-j,:]-prev[:,j,:],0);transfer[:,j,:]=dr*dt*diff[:,j,None]*gap
  stock[:,:,t,:]=np.clip(prev+intens+mg+transfer-loss,float(cfg['stock_floor']),float(cfg['stock_ceiling']))
 broad=np.mean(stock[...,[1,2,3]],axis=-1);intens=np.mean(stock,axis=-1);delay=np.mean(stock[...,[4,6]],axis=-1);managed=np.mean(stock[...,[2,4,5]],axis=-1)
 settle=np.clip(.45*delay+.30*stock[...,5]+.25*tech[...,4],0,1)
 # regional differentiation is cross-lineage-independent and measures member-level domain specialization within each lineage.
 domstd=np.std(stock,axis=-1);regdiff=np.clip(.55*domstd/.20+.45*(1-eco31[...,ei['interlineage_diffusion_opportunity']]),0,1)
 regcont=np.clip(.35*eco31[...,ei['retention_support']]+.35*eco31[...,ei['transmission_fidelity']]+.30*eco31[...,ei['technical_resilience']],0,1)
 readiness=np.clip(.24*managed+.20*delay+.16*settle+.14*stock[...,6]+.14*regcont+.12*broad,0,1)
 resil=np.clip(.45*eco31[...,ei['technical_resilience']]+.30*delay+.25*broad,0,1);exchange=np.clip(eco31[...,ei['interlineage_diffusion_opportunity']]*(.5+.5*intens),0,1)
 eco=np.stack([broad,intens,delay,managed,settle,regdiff,regcont,readiness,resil,exchange],axis=-1)
 thr=np.clip(float(cfg['transition_pocket_threshold'])+threshold_offset,0,1);cont=float(cfg['transition_pocket_min_continuity'])
 pockets=((readiness>=thr)&(regcont>=cont)).astype(np.uint8)
 return {'age':age,'stock':stock,'eco':eco,'pockets':pockets}

def build_regional_anchors(inp:dict[str,Any],rep:dict[str,np.ndarray])->dict[str,np.ndarray]:
 g31=inp['g31'];g30=inp['g30'];asel=inp['anchor_sel'];ages=np.asarray(g31['anchor_age_ka'][asel],float);state31=np.asarray(g31['group_state'][:,:,asel,:,:],float);active=np.asarray(g31['group_active'][:,:,asel,:],np.uint8);state30=np.asarray(g30['agent_state'][:,:,asel,:,:],float);names30=list(map(str,g30['agent_variable_names']));i30={n:i for i,n in enumerate(names30)};names31=list(map(str,g31['group_variable_names']));i31={n:i for i,n in enumerate(names31)}
 n,m,A,G=active.shape;out=np.zeros((n,m,A,G,len(REGION_NAMES)),float)
 # exact time index mapping to R3.32 age axis
 for ai,age in enumerate(ages):
  ti=int(np.where(np.isclose(rep['age'],age,atol=1e-12))[0][0])
  for mi in range(n):
   for cj in range(m):
    for gj in range(G):
     if not active[mi,cj,ai,gj]:continue
     deme=int(round(state30[mi,cj,ai,gj,i30['deme_index']]))
     represented=state31[mi,cj,ai,gj,i31['represented_people']];camps=state31[mi,cj,ai,gj,i31['represented_camps']];tech=state31[mi,cj,ai,gj,i31['tech_access']]
     sub=rep['stock'][mi,cj,ti];ec=rep['eco'][mi,cj,ti]
     out[mi,cj,ai,gj]=[represented,camps,state30[mi,cj,ai,gj,i30['grid_row']],state30[mi,cj,ai,gj,i30['grid_col']],deme+1,float(np.mean(sub)),ec[1],ec[7],tech,ec[6]]
 return {'age':ages,'state':out,'active':active}

def summarize(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],regional:dict[str,np.ndarray])->tuple[dict[str,Any],dict[str,Any]]:
 outcomes=[]
 for j,sid in enumerate(EXPECTED_CANDIDATES):
  f=rep['eco'][:,j,-1,:];p=rep['pockets'][:,j,-1]
  outcomes.append({'species_id':sid,'final_subsistence_intensification_median':float(np.median(f[:,1])),'final_broad_spectrum_median':float(np.median(f[:,0])),'final_managed_resource_intensity_median':float(np.median(f[:,3])),'final_transition_readiness_median':float(np.median(f[:,7])),'final_transition_pocket_frequency':float(np.mean(p)),'final_regional_continuity_median':float(np.median(f[:,6])),'interpretation':'SUBSISTENCE_AND_MANAGEMENT_TRANSITION_POTENTIAL_NOT_AGRICULTURE_OR_DOMESTICATION'})
 variants=[]
 for rm in cfg['sensitivity_rate_multipliers']:
  for off in cfg['sensitivity_threshold_offsets']:
   r=replay_subsistence(inp,cfg,float(rm),float(off));variants.append({'rate_multiplier':rm,'threshold_offset':off,'transition_pocket_frequency':[float(np.mean(r['pockets'][:,j,-1])) for j in range(2)]})
 sens={'stage':STAGE,'status':'SUBSISTENCE_TRANSITION_SENSITIVITY','variant_count':len(variants),'selection_gate':False,'candidate_retention':EXPECTED_CANDIDATES,'variants':variants}
 return {'stage':STAGE,'status':'SUBSISTENCE_REGIONAL_TRANSITION_OUTCOMES','candidate_lineages':EXPECTED_CANDIDATES,'lineages':outcomes,'agriculture_materialized':False,'domesticated_species_materialized':False,'named_culture_materialized':False,'unique_human_identity_materialized':False},sens

def _audit(inp,cfg,rep,regional,outcomes,sens):
 checks=[]
 def ck(n,c,d=None):checks.append({'name':n,'pass':bool(c),'detail':d})
 ck('parent_r331_sealed',inp['a31']['status']==PARENT_PASS);ck('candidate_order_exact',list(map(str,inp['z31']['candidate_ids']))==EXPECTED_CANDIDATES);ck('member_count_exact',rep['stock'].shape[0]==32);ck('time_window_exact',len(rep['age'])==145 and rep['age'][0]==20 and rep['age'][-1]==0);ck('subsistence_domains_exact',SUB_NAMES==list(cfg['subsistence_domains']));ck('stock_geometry',rep['stock'].shape==(32,2,145,8),rep['stock'].shape);ck('ecology_geometry',rep['eco'].shape==(32,2,145,10),rep['eco'].shape);ck('all_numeric_finite',np.isfinite(rep['stock']).all() and np.isfinite(rep['eco']).all() and np.isfinite(regional['state']).all());ck('stock_bounded',np.min(rep['stock'])>=0 and np.max(rep['stock'])<=1);ck('ecology_bounded',np.min(rep['eco'])>=0 and np.max(rep['eco'])<=1);ck('pockets_binary',set(np.unique(rep['pockets'])).issubset({0,1}));ck('regional_anchor_geometry',regional['state'].shape==(32,2,9,48,10),regional['state'].shape);ck('regional_active_parent_subset',regional['active'].shape==(32,2,9,48));ck('regional_codes_bounded',np.min(regional['state'][...,4])>=0 and np.max(regional['state'][...,4])<=6);ck('sensitivity_25_variants',sens['variant_count']==25);ck('sensitivity_not_selection_gate',sens['selection_gate'] is False);ck('both_lineages_retained',sens['candidate_retention']==EXPECTED_CANDIDATES);ck('agriculture_not_materialized',cfg['agriculture_materialized'] is False and outcomes['agriculture_materialized'] is False);ck('domesticated_species_not_materialized',cfg['domesticated_species_materialized'] is False and outcomes['domesticated_species_materialized'] is False);ck('regional_lineages_not_named_cultures',cfg['named_culture_materialized'] is False);ck('no_language_religion_city_state',cfg['language_materialized'] is False and cfg['religion_materialized'] is False and cfg['city_state_materialized'] is False);ck('no_unique_human_identity',cfg['unique_human_identity_materialized'] is False);ck('deep_off',cfg['deep_biological_coupling'] is False);ck('no_human_similarity_target',cfg['human_similarity_target'] is False);ck('evidence_multisource',len(EVIDENCE)>=8)
 failed=[x for x in checks if not x['pass']];return {'stage':STAGE,'audit':'INTEGRATED_SUBSISTENCE_INTENSIFICATION_REGIONAL_CULTURAL_LINEAGES_AND_HOLOCENE_TRANSITIONS','status':CANDIDATE_PASS if not failed else 'FAIL_R332_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'checks':checks,'summary':{'candidate_lineages':2,'ensemble_members':32,'time_states':145,'subsistence_domains':8,'regional_anchor_states':9,'agriculture_materialized':False,'domesticated_species_materialized':False,'named_culture_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False}}

def build_outputs(inp,cfg,rep,regional,outcomes,sens,out:Path):
 out.mkdir(parents=True,exist_ok=True)
 authority={'stage':STAGE,'status':'SUBSISTENCE_REGIONAL_TRANSITION_AUTHORITY','parent':PARENT_PASS,'candidate_cohort':EXPECTED_CANDIDATES,'time_window_ka':[20.0,0.0],'subsistence_domains':SUB_NAMES,'regional_cultural_lineage_semantics':'OPAQUE_DEME_TRACKED_REGIONAL_CULTURAL_CONTINUITY_NOT_NAMED_CULTURE_ETHNICITY_OR_LANGUAGE','transition_semantics':'MANAGED_RESOURCE_AND_FOOD_PRODUCTION_READINESS_NOT_AGRICULTURE_OR_DOMESTICATION','agriculture_materialized':False,'domesticated_species_materialized':False,'named_culture_materialized':False,'language_materialized':False,'religion_materialized':False,'city_state_materialized':False,'ethnicity_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False,'evidence_basis':EVIDENCE,'dynamics':{k:cfg[k] for k in ['intensification_rate_per_kyr','loss_rate_per_kyr','management_feedback_rate_per_kyr','regional_diffusion_rate_per_kyr','broad_spectrum_operational_threshold','management_readiness_threshold','transition_pocket_threshold','transition_pocket_min_continuity']}}
 write_json(out/'R3_32_SUBSISTENCE_REGIONAL_TRANSITION_AUTHORITY.json',authority);write_json(out/'R3_32_LINEAGE_SUBSISTENCE_OUTCOMES.json',outcomes);write_json(out/'R3_32_SENSITIVITY_AND_ROBUSTNESS.json',sens)
 np.savez_compressed(out/'R3_32_SUBSISTENCE_AND_TRANSITION_REPLAY.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z31']['parent_member_indices'],age_ka=rep['age'],subsistence_domain_names=np.array(SUB_NAMES),subsistence_domain_stock=rep['stock'],ecology_variable_names=np.array(ECO_NAMES),subsistence_transition_ecology=rep['eco'],transition_pocket=rep['pockets'])
 np.savez_compressed(out/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z31']['parent_member_indices'],anchor_age_ka=regional['age'],regional_variable_names=np.array(REGION_NAMES),regional_state=regional['state'],regional_active=regional['active'])
 cp={'stage':STAGE,'status':'SUBSISTENCE_REGIONAL_TRANSITION_CHECKPOINT_0KA','age_ka':0.0,'candidate_cohort':EXPECTED_CANDIDATES,'candidate_count':2,'regional_lineages_materialized':True,'regional_lineages_named_cultures':False,'managed_resource_transition_pockets_materialized':True,'agriculture_materialized':False,'domesticated_species_materialized':False,'named_culture_materialized':False,'language_materialized':False,'religion_materialized':False,'city_state_materialized':False,'unique_human_identity_materialized':False,'unique_human_identity':None};write_json(out/'R3_32_SUBSISTENCE_REGIONAL_TRANSITION_CHECKPOINT.json',cp)
 audit=_audit(inp,cfg,rep,regional,outcomes,sens);write_json(out/'R3_32_INTEGRATED_AUDIT.json',audit);(out/'R3_32_AUDIT.md').write_text(f"# R3.32 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n",encoding='utf-8');return audit

def write_manifest(out:Path,status:str)->None:
 files={}
 for p in sorted(out.iterdir()):
  if p.name=='R3_32_OUTPUT_MANIFEST.json' or not p.is_file():continue
  files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_32_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
