from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json
import numpy as np

STAGE='v0.6D1-R3.37'
PARENT_STAGE='v0.6D1-R3.36'
PARENT_PASS='PASS_R336_PRODUCER_DOMESTICATION_SELECTION_ECOLOGY_RESOURCE_PERSISTENCE_WILD_GENE_FLOW_CLOSURE_AND_FORAGER_VS_FOOD_PRODUCTION_PATHWAY_RESOLUTION_SEALED'
CANDIDATE_PASS='PASS_R337_INTENSIVE_MANAGED_FORAGER_DEMOGRAPHY_SETTLEMENT_AND_EXCHANGE_ECONOMY_CANDIDATE'
FINAL_PASS='PASS_R337_INTENSIVE_MANAGED_FORAGER_DEMOGRAPHY_SETTLEMENT_STORAGE_EXCHANGE_SPECIALIZATION_AND_REGIONAL_ECONOMY_SEALED'
EXPECTED_CANDIDATES=['RPT_010_D02','RPT_009_D02']
EXPECTED_MEMBERS=32
EXPECTED_TIMES=145
EXPECTED_ANCHORS=9
EXPECTED_AGENTS=48
EXPECTED_PARENT_CHECKS=32

R330_PASS='PASS_R330_CENSUS_EQUIVALENT_CALIBRATION_WEIGHTED_GROUP_ABM_LATE_PLEISTOCENE_COMMUNITY_HISTORY_AND_CHA2_GROUP_EXPOSURE_SEALED'
R331_PASS='PASS_R331_LATE_PLEISTOCENE_TO_HOLOCENE_CULTURAL_TECHNOLOGICAL_ECOLOGY_TRANSMISSION_RETENTION_AND_TECHNICAL_REPERTOIRE_SEALED'
R332_PASS='PASS_R332_SUBSISTENCE_INTENSIFICATION_REGIONAL_CULTURAL_LINEAGES_MANAGED_RESOURCE_TRANSITIONS_AND_HOLOCENE_READINESS_SEALED'

ECON_NAMES=[
 'managed_resource_support','resource_predictability','storage_buffer_capacity','resource_surplus_buffer',
 'settlement_persistence','persistent_central_place_potential','economic_network_connectivity','exchange_volume_proxy',
 'cooperative_specialization','redistribution_potential','resource_control_asymmetry_pressure','demographic_support_index',
 'regional_economic_complexity','interlineage_exchange_support'
]
NODE_NAMES=[
 'represented_people','represented_camps','grid_row','grid_col','managed_resource_access','storage_access',
 'settlement_persistence','central_place_potential','exchange_access','specialization_access',
 'redistribution_potential','resource_control_asymmetry_pressure'
]

EVIDENCE={
 'MESOLITHIC_MOBILITY_SEDENTISM_2025':{
  'source':'Holst, Hunter-Gatherer Mobility and Sedentism, Oxford Handbook of Mesolithic Europe (2025)',
  'doi':'10.1093/oxfordhb/9780198853657.013.30',
  'use':'reduced residential mobility can coexist with individual mobility, managed territories, storage and long-distance exchange'},
 'STORAGE_HUNTER_GATHERERS':{
  'source':'Morgan, Caching your savings: small-scale storage in European prehistory (2011)',
  'doi':'10.1016/j.jaa.2010.12.005',
  'use':'storage is possible in mobile and semi-sedentary forager systems and must not be equated automatically with farming'},
 'COMPLEX_FORAGER_STORAGE':{
  'source':'Testart et al., The Significance of Food Storage Among Hunter-Gatherers (1982)',
  'doi':'10.1086/202894',
  'use':'predictable seasonal resources and storage can support higher density, sedentism and socioeconomic complexity without agriculture'},
 'FORAGING_NETWORKS':{
  'source':'Hunter-gatherer foraging networks promote information transmission (2021)',
  'pmcid':'PMC8692955',
  'use':'central-place foraging and intermediate mobility can increase network efficiency and information exchange'},
 'SOCIAL_NETWORK_MOBILITY':{
  'source':'Social networks and information: Non-utilitarian mobility among hunter-gatherers (2006)',
  'doi':'10.1016/j.jaa.2005.11.004',
  'use':'mobility maintains risk-buffering information and exchange networks, so settlement persistence does not imply network collapse'},
 'R330_PARENT':{'source':'R3.30 SEALED census-equivalent and weighted group ABM','use':'census-equivalent, group counts, network counts, locations and organization modes are inherited authority'},
 'R331_PARENT':{'source':'R3.31 SEALED cultural-technological ecology','use':'storage, transport/logistics, shelter/site engineering and specialization capacities are inherited authority'},
 'R332_PARENT':{'source':'R3.32 SEALED subsistence/regional transitions','use':'delayed-return economy, settlement commitment, regional continuity/differentiation and subsistence resilience are inherited authority'},
 'R336_PARENT':{'source':'R3.36 SEALED intensive managed-forager pathway','use':'managed producer support, patch persistence and no-agriculture pathway are immutable parent authority'}
}

class R337GateError(RuntimeError): pass

def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()

def load_json(p:Path)->Any: return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def _close_manifest(d:Path,name:str)->None:
 p=d/name
 if not p.is_file(): raise R337GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file() or fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:
   raise R337GateError(f'Manifest closure failure {fp}')

def _seal(root:Path,s:int,expected:str,checks:int)->dict[str,Any]:
 p=root/'outputs'/f'v0_6D1_R3_{s}_SEAL'/f'R3_{s}_FINAL_SEAL_AUDIT.json'
 d=load_json(p)
 if d.get('status')!=expected or d.get('verdict')!='SEALED' or d.get('checks_passed')!=checks or d.get('checks_failed')!=0:
  raise R337GateError(f'R3.{s} seal mismatch')
 return d

def _match_indices(parent:np.ndarray,child:np.ndarray)->np.ndarray:
 idx=[]
 for x in child:
  w=np.where(np.isclose(parent,float(x),rtol=0,atol=1e-12))[0]
  if len(w)!=1: raise R337GateError(f'Cannot uniquely bind age {x}')
  idx.append(int(w[0]))
 return np.asarray(idx,int)

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root)
 r30=root/'outputs'/'v0_6D1_R3_30';r31=root/'outputs'/'v0_6D1_R3_31';r32=root/'outputs'/'v0_6D1_R3_32';r36=root/'outputs'/'v0_6D1_R3_36';s36=root/'outputs'/'v0_6D1_R3_36_SEAL'
 for d in [r30,r31,r32,r36,s36]:
  if not d.is_dir(): raise R337GateError(f'Missing authority {d}')
 a30=_seal(root,30,R330_PASS,27);a31=_seal(root,31,R331_PASS,29);a32=_seal(root,32,R332_PASS,30);a36=_seal(root,36,PARENT_PASS,EXPECTED_PARENT_CHECKS)
 for d,n in [(r30,'R3_30_OUTPUT_MANIFEST.json'),(r31,'R3_31_OUTPUT_MANIFEST.json'),(r32,'R3_32_OUTPUT_MANIFEST.json'),(r36,'R3_36_OUTPUT_MANIFEST.json')]: _close_manifest(d,n)
 cp36=load_json(r36/'R3_36_PATHWAY_RESOLUTION_CHECKPOINT.json')
 if cp36.get('resolved_pathway')!='INTENSIVE_MANAGED_FORAGER_PATHWAY' or cp36.get('agriculture_materialized') is not False:
  raise R337GateError('R3.36 pathway premise mismatch')
 z30=np.load(r30/'R3_30_CENSUS_AND_GROUP_TIMESERIES.npz',allow_pickle=False)
 a30z=np.load(r30/'R3_30_WEIGHTED_GROUP_ABM.npz',allow_pickle=False)
 z31=np.load(r31/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz',allow_pickle=False)
 a31z=np.load(r31/'R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz',allow_pickle=False)
 z32=np.load(r32/'R3_32_SUBSISTENCE_AND_TRANSITION_REPLAY.npz',allow_pickle=False)
 a32z=np.load(r32/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz',allow_pickle=False)
 z36=np.load(r36/'R3_36_DOMESTICATION_SELECTION_ECOLOGY_REPLAY.npz',allow_pickle=False)
 for z in [z30,a30z,z31,a31z,z32,a32z,z36]:
  if list(map(str,z['candidate_ids']))!=EXPECTED_CANDIDATES: raise R337GateError('Candidate order mismatch')
 if not np.array_equal(z32['parent_member_indices'],z36['parent_member_indices']): raise R337GateError('Member mapping R3.32/R3.36 mismatch')
 if not np.array_equal(z30['parent_member_indices'],z36['parent_member_indices']) or not np.array_equal(z31['parent_member_indices'],z36['parent_member_indices']): raise R337GateError('Member mapping mismatch')
 if z32['age_ka'].shape!=(EXPECTED_TIMES,) or not np.array_equal(z32['age_ka'],z36['age_ka']): raise R337GateError('20ka-0 axis mismatch')
 i30=_match_indices(z30['age_ka'],z32['age_ka']); i31=_match_indices(z31['age_ka'],z32['age_ka'])
 ia30=_match_indices(a30z['anchor_age_ka'],a32z['anchor_age_ka']);ia31=_match_indices(a31z['anchor_age_ka'],a32z['anchor_age_ka'])
 if a32z['anchor_age_ka'].shape!=(EXPECTED_ANCHORS,): raise R337GateError('Anchor geometry mismatch')
 return {'root':root,'r30':r30,'r31':r31,'r32':r32,'r36':r36,'a30':a30,'a31':a31,'a32':a32,'a36':a36,'cp36':cp36,'z30':z30,'a30z':a30z,'z31':z31,'a31z':a31z,'z32':z32,'a32z':a32z,'z36':z36,'i30':i30,'i31':i31,'ia30':ia30,'ia31':ia31}

def _weighted_resource_drivers(z36:Any)->tuple[np.ndarray,np.ndarray,np.ndarray]:
 food=np.asarray(z36['effective_plant_food_contribution'],float) # M,L,P,T
 rp=np.asarray(z36['resource_persistence'],float)
 patch=np.asarray(z36['managed_patch_persistence'],float)
 M,L,P,T=food.shape
 managed=np.zeros((M,L,T),float);predict=np.zeros_like(managed);patch_support=np.zeros_like(managed)
 for t in range(T):
  w=food[:,:,:,t]
  managed[:,:,t]=np.clip(np.sort(w,axis=2)[:,:,-6:].sum(axis=2),0,1)
  denom=w.sum(axis=2)+1e-12
  predict[:,:,t]=np.clip((w*rp[:,:,:,t]).sum(axis=2)/denom,0,1)
  patch_support[:,:,t]=np.clip((w*patch[:,:,:,t]).sum(axis=2)/denom,0,1)
 return managed,predict,patch_support

def replay_managed_forager_economy(inp:dict[str,Any],cfg:dict[str,Any],storage_multiplier:float=1.0,exchange_multiplier:float=1.0,settlement_multiplier:float=1.0,store_nodes:bool=True)->dict[str,np.ndarray]:
 z30,z31,z32,z36=inp['z30'],inp['z31'],inp['z32'],inp['z36'];ages=np.asarray(z32['age_ka'],float);dt=np.r_[ages[:-1]-ages[1:],0.0]
 C=np.asarray(z30['census_group_series'],float)[:,:,inp['i30'],:];Tech=np.asarray(z31['technology_domain_stock'],float)[:,:,inp['i31'],:];E31=np.asarray(z31['cultural_technological_ecology'],float)[:,:,inp['i31'],:];Sub=np.asarray(z32['subsistence_domain_stock'],float);E32=np.asarray(z32['subsistence_transition_ecology'],float)
 managed,predict,patch_support=_weighted_resource_drivers(z36)
 M,L,T=managed.shape
 # inherited driver arrays
 group_count=np.maximum(C[...,2],1e-9);active_network=np.maximum(C[...,3],0);regional_network=np.maximum(C[...,4],0)
 network=np.clip(.5*np.clip((active_network/group_count)/.35,0,1)+.5*np.clip((regional_network/(active_network+1e-9))/.45,0,1),0,1)
 storage_input=np.clip((.28*Tech[...,6]+.25*Sub[...,4]+.22*E32[...,2]+.15*managed+.10*predict)*storage_multiplier,0,1)
 logistics=np.clip(.45*Tech[...,5]+.35*Sub[...,6]+.20*network,0,1)
 coop_base=np.clip(.38*Tech[...,7]+.28*Sub[...,7]+.34*E31[...,6],0,1)
 settle_base=E32[...,4];regional_diff=E32[...,5];regional_cont=E32[...,6];resilience=E32[...,8]
 storage=np.zeros((M,L,T),float);surplus=np.zeros_like(storage);settle=np.zeros_like(storage);exchange=np.zeros_like(storage);special=np.zeros_like(storage);redis=np.zeros_like(storage);demo=np.zeros_like(storage)
 storage[:,:,0]=storage_input[:,:,0]
 surplus[:,:,0]=np.clip(.32*managed[:,:,0]+.22*predict[:,:,0]+.24*storage[:,:,0]+.22*resilience[:,:,0],0,1)
 settle[:,:,0]=np.clip((.22*Tech[:,:,0,4]+.22*storage[:,:,0]+.18*settle_base[:,:,0]+.14*regional_cont[:,:,0]+.14*predict[:,:,0]+.10*managed[:,:,0])*settlement_multiplier,0,1)
 exchange[:,:,0]=np.clip((.28*network[:,:,0]+.20*logistics[:,:,0]+.16*regional_diff[:,:,0]+.16*surplus[:,:,0]+.12*E31[:,:,0,7]+.08*E32[:,:,0,9])*exchange_multiplier,0,1)
 special[:,:,0]=np.clip(.45*coop_base[:,:,0]+.22*surplus[:,:,0]+.18*settle[:,:,0]+.15*exchange[:,:,0],0,1)
 redis[:,:,0]=np.clip(.30*storage[:,:,0]+.24*exchange[:,:,0]+.20*special[:,:,0]+.16*settle[:,:,0]+.10*surplus[:,:,0],0,1)
 demo[:,:,0]=np.clip(.25*surplus[:,:,0]+.20*resilience[:,:,0]+.18*settle[:,:,0]+.18*network[:,:,0]+.19*predict[:,:,0],0,1)
 for t in range(T-1):
  kyr=float(dt[t])
  storage[:,:,t+1]=np.clip(storage[:,:,t]+float(cfg['storage_state_adjustment_rate_per_kyr'])*kyr*(storage_input[:,:,t+1]-storage[:,:,t]),0,1)
  sur_target=np.clip(.32*managed[:,:,t+1]+.22*predict[:,:,t+1]+.24*storage[:,:,t+1]+.22*resilience[:,:,t+1],0,1)
  surplus[:,:,t+1]=np.clip(surplus[:,:,t]+.16*kyr*(sur_target-surplus[:,:,t]),0,1)
  set_target=np.clip((.22*Tech[:,:,t+1,4]+.22*storage[:,:,t+1]+.18*settle_base[:,:,t+1]+.14*regional_cont[:,:,t+1]+.14*predict[:,:,t+1]+.10*managed[:,:,t+1])*settlement_multiplier,0,1)
  settle[:,:,t+1]=np.clip(settle[:,:,t]+float(cfg['settlement_state_adjustment_rate_per_kyr'])*kyr*(set_target-settle[:,:,t]),0,1)
  ex_target=np.clip((.28*network[:,:,t+1]+.20*logistics[:,:,t+1]+.16*regional_diff[:,:,t+1]+.16*surplus[:,:,t+1]+.12*E31[:,:,t+1,7]+.08*E32[:,:,t+1,9])*exchange_multiplier,0,1)
  exchange[:,:,t+1]=np.clip(exchange[:,:,t]+float(cfg['exchange_state_adjustment_rate_per_kyr'])*kyr*(ex_target-exchange[:,:,t]),0,1)
  sp_target=np.clip(.45*coop_base[:,:,t+1]+.22*surplus[:,:,t+1]+.18*settle[:,:,t+1]+.15*exchange[:,:,t+1],0,1)
  special[:,:,t+1]=np.clip(special[:,:,t]+float(cfg['specialization_state_adjustment_rate_per_kyr'])*kyr*(sp_target-special[:,:,t]),0,1)
  rd_target=np.clip(.30*storage[:,:,t+1]+.24*exchange[:,:,t+1]+.20*special[:,:,t+1]+.16*settle[:,:,t+1]+.10*surplus[:,:,t+1],0,1)
  redis[:,:,t+1]=np.clip(redis[:,:,t]+float(cfg['redistribution_state_adjustment_rate_per_kyr'])*kyr*(rd_target-redis[:,:,t]),0,1)
  dm_target=np.clip(.25*surplus[:,:,t+1]+.20*resilience[:,:,t+1]+.18*settle[:,:,t+1]+.18*network[:,:,t+1]+.19*predict[:,:,t+1],0,1)
  demo[:,:,t+1]=np.clip(demo[:,:,t]+float(cfg['demographic_support_adjustment_rate_per_kyr'])*kyr*(dm_target-demo[:,:,t]),0,1)
 central=np.clip(.32*settle+.24*storage+.18*surplus+.14*network+.12*regional_cont,0,1)
 asym=np.clip(.25*storage+.22*redis+.18*settle+.18*surplus+.17*special,0,1)
 complexity=np.clip(.18*storage+.18*surplus+.18*settle+.18*exchange+.16*special+.12*redis,0,1)
 # conservative interlineage exchange: requires both within-lineage exchange systems plus inherited cross-lineage opportunity.
 inherited_cross=np.maximum(E31[...,7],E32[...,9]);shared=np.minimum(exchange[:,0,:],exchange[:,1,:]);cross=np.zeros_like(exchange)
 cross_shared=np.clip(.25*shared+.75*inherited_cross.mean(axis=1),0,1)
 cross[:,0,:]=cross_shared;cross[:,1,:]=cross_shared
 # Downstream census-equivalent posterior: parent R3.30 is never overwritten.
 lo=float(cfg['economy_census_multiplier_min']);hi=float(cfg['economy_census_multiplier_max']);mult=np.ones_like(demo)
 for t in range(T-1):
  target=np.clip(lo+(hi-lo)*demo[:,:,t+1],lo,hi)
  mult[:,:,t+1]=np.clip(mult[:,:,t]+float(cfg['demographic_support_adjustment_rate_per_kyr'])*float(dt[t])*(target-mult[:,:,t]),lo,hi)
 parent_census=C[...,0];econ_census=parent_census*mult
 econ_groups=C[...,2]*mult;mean_group=np.divide(econ_census,econ_groups,out=np.zeros_like(econ_census),where=econ_groups>0)
 econ=np.stack([managed,predict,storage,surplus,settle,central,network,exchange,special,redis,asym,demo,complexity,cross],axis=-1)
 out={'age_ka':ages,'economic_state':econ,'economy_census_multiplier':mult,'economy_coupled_census_equivalent':econ_census,'economy_coupled_group_count_equivalent':econ_groups,'economy_coupled_group_mean_size':mean_group,'parent_census_equivalent':parent_census,'managed_patch_food_weighted':patch_support}
 if store_nodes: out.update(build_economic_nodes(inp,out,cfg))
 return out

def build_economic_nodes(inp:dict[str,Any],rep:dict[str,np.ndarray],cfg:dict[str,Any])->dict[str,np.ndarray]:
 a32=inp['a32z'];a30=inp['a30z'];a31=inp['a31z'];ages=np.asarray(a32['anchor_age_ka'],float);tidx=_match_indices(rep['age_ka'],ages)
 reg=np.asarray(a32['regional_state'],float);active=np.asarray(a32['regional_active'],np.uint8);g30=np.asarray(a30['agent_state'],float)[:,:,inp['ia30'],:,:];g31=np.asarray(a31['group_state'],float)[:,:,inp['ia31'],:,:]
 M,L,A,N=active.shape;nodes=np.zeros((M,L,A,N,len(NODE_NAMES)),float)
 for ai,ti in enumerate(tidx):
  econ=rep['economic_state'][:,:,ti,:]
  for m in range(M):
   for l in range(L):
    for n in np.where(active[m,l,ai]>0)[0]:
     represented_people=float(reg[m,l,ai,n,0]);represented_camps=float(reg[m,l,ai,n,1]);row=float(reg[m,l,ai,n,2]);col=float(reg[m,l,ai,n,3]);subint=float(reg[m,l,ai,n,6]);managed_read=float(reg[m,l,ai,n,7]);tech_access=float(reg[m,l,ai,n,8]);continuity=float(reg[m,l,ai,n,9]);network_access=float(g30[m,l,ai,n,7]);mode=float(g30[m,l,ai,n,6]);group_spec=float(g31[m,l,ai,n,5])
     mode_persist={0.0:.72,1.0:.92,2.0:1.10}.get(mode,1.0)
     managed_access=np.clip(econ[m,l,0]*(.55+.45*managed_read),0,1);storage_access=np.clip(econ[m,l,2]*(.55+.45*tech_access),0,1)
     settle_access=np.clip(econ[m,l,4]*(.60+.40*continuity)*mode_persist,0,1);central=np.clip(econ[m,l,5]*(.55+.45*continuity)*mode_persist,0,1)
     exchange=np.clip(econ[m,l,7]*(.55+.25*network_access+.20*tech_access),0,1);spec=np.clip(econ[m,l,8]*(.55+.25*group_spec+.20*subint),0,1);redis=np.clip(econ[m,l,9]*(.60+.20*storage_access+.20*exchange),0,1);asym=np.clip(econ[m,l,10]*(.65+.20*central+.15*redis),0,1)
     nodes[m,l,ai,n]=[represented_people,represented_camps,row,col,managed_access,storage_access,settle_access,central,exchange,spec,redis,asym]
 return {'anchor_age_ka':ages,'economic_node_state':nodes,'economic_node_active':active.copy()}

def _pathway_for_lineage(rep:dict[str,np.ndarray],l:int,cfg:dict[str,Any])->str:
 x=rep['economic_state'][:,l,-1,:]
 central=float(np.median(x[:,5]));exchange=float(np.median(x[:,7]));complexity=float(np.median(x[:,12]));network=float(np.median(x[:,6]))
 if complexity>=float(cfg['regional_complexity_threshold']) and central>=float(cfg['central_place_threshold']) and exchange>=float(cfg['exchange_economy_threshold']): return 'REGIONAL_COMPLEX_FORAGER_ECONOMY'
 if central>=float(cfg['central_place_threshold']): return 'PERSISTENT_CENTRAL_PLACE_FORAGER_ECONOMY'
 if exchange>=float(cfg['exchange_economy_threshold']) and network>=.50: return 'SEASONALLY_AGGREGATED_EXCHANGE_ECONOMY'
 return 'DISTRIBUTED_MANAGED_FORAGER_ECONOMY'

def summarize(inp:dict[str,Any],rep:dict[str,np.ndarray],cfg:dict[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
 lines=[]
 for l,sid in enumerate(EXPECTED_CANDIDATES):
  x=rep['economic_state'][:,l,-1,:];nodes=rep['economic_node_state'][:,l,-1,:,:];act=rep['economic_node_active'][:,l,-1,:].astype(bool)
  node_central=nodes[...,7][act];node_exchange=nodes[...,8][act]
  lines.append({'lineage_id':sid,'resolved_economic_pathway':_pathway_for_lineage(rep,l,cfg),'economy_coupled_census_0ka_median':float(np.median(rep['economy_coupled_census_equivalent'][:,l,-1])),'economy_coupled_census_0ka_q10_q90':[float(q) for q in np.quantile(rep['economy_coupled_census_equivalent'][:,l,-1],[.1,.9])],'managed_resource_support_median':float(np.median(x[:,0])),'storage_buffer_capacity_median':float(np.median(x[:,2])),'resource_surplus_buffer_median':float(np.median(x[:,3])),'settlement_persistence_median':float(np.median(x[:,4])),'persistent_central_place_potential_median':float(np.median(x[:,5])),'exchange_volume_proxy_median':float(np.median(x[:,7])),'cooperative_specialization_median':float(np.median(x[:,8])),'redistribution_potential_median':float(np.median(x[:,9])),'resource_control_asymmetry_pressure_median':float(np.median(x[:,10])),'regional_economic_complexity_median':float(np.median(x[:,12])),'active_node_central_place_potential_median':float(np.median(node_central)) if node_central.size else 0.0,'active_node_exchange_access_median':float(np.median(node_exchange)) if node_exchange.size else 0.0})
 outcomes={'stage':STAGE,'status':'R337_MANAGED_FORAGER_ECONOMY_OUTCOMES','candidate_lineages':EXPECTED_CANDIDATES,'agriculture_materialized':False,'village_city_state_materialized':False,'class_hierarchy_materialized':False,'currency_market_materialized':False,'lineages':lines}
 combos=[(.8,1,1),(1,1,1),(1.2,1,1),(1,.8,1),(1,1.2,1),(1,1,.8),(1,1,1.2),(.85,1.15,.9),(1.15,.85,1.1),(.9,.9,1.15),(1.1,1.1,.85),(.75,1.25,1.0),(1.25,.75,1.0),(1.0,1.25,1.2),(1.0,.75,.8)]
 variants=[]
 for sm,em,sem in combos:
  r=replay_managed_forager_economy(inp,cfg,sm,em,sem,store_nodes=False)
  variants.append({'storage_multiplier':sm,'exchange_multiplier':em,'settlement_multiplier':sem,'resolved_pathways':[_pathway_for_lineage(r,l,cfg) for l in range(2)],'median_census_0ka':[float(np.median(r['economy_coupled_census_equivalent'][:,l,-1])) for l in range(2)],'median_central_place_potential':[float(np.median(r['economic_state'][:,l,-1,5])) for l in range(2)],'median_exchange_volume_proxy':[float(np.median(r['economic_state'][:,l,-1,7])) for l in range(2)],'median_regional_complexity':[float(np.median(r['economic_state'][:,l,-1,12])) for l in range(2)]})
 sens={'stage':STAGE,'status':'R337_ECONOMY_SENSITIVITY','variant_count':len(variants),'selection_gate':False,'variants':variants}
 cohort_pathways=[x['resolved_economic_pathway'] for x in lines]
 cp={'stage':STAGE,'status':'R337_MANAGED_FORAGER_ECONOMY_CHECKPOINT_0KA','age_ka':0.0,'candidate_cohort':EXPECTED_CANDIDATES,'resolved_lineage_economic_pathways':dict(zip(EXPECTED_CANDIDATES,cohort_pathways)),'agriculture_materialized':False,'domesticated_species_materialized':False,'village_materialized':False,'city_state_materialized':False,'class_hierarchy_materialized':False,'currency_market_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False}
 return outcomes,sens,cp

def _audit(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],outs:dict[str,Any],sens:dict[str,Any])->dict[str,Any]:
 checks=[]
 def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
 ck('r336_parent_sealed',inp['a36']['status']==PARENT_PASS);ck('r336_pathway_exact',inp['cp36']['resolved_pathway']=='INTENSIVE_MANAGED_FORAGER_PATHWAY');ck('r330_r331_r332_authorities_sealed',inp['a30']['status']==R330_PASS and inp['a31']['status']==R331_PASS and inp['a32']['status']==R332_PASS);ck('time_axis_145',rep['age_ka'].shape==(145,));ck('candidate_member_mapping_exact',np.array_equal(inp['z36']['parent_member_indices'],inp['z32']['parent_member_indices']));ck('economic_geometry',rep['economic_state'].shape==(32,2,145,len(ECON_NAMES)));ck('census_geometry',rep['economy_coupled_census_equivalent'].shape==(32,2,145));ck('nodes_geometry',rep['economic_node_state'].shape==(32,2,9,48,len(NODE_NAMES)));ck('node_active_exact_parent',np.array_equal(rep['economic_node_active'],inp['a32z']['regional_active']));ck('all_numeric_finite',np.isfinite(rep['economic_state']).all() and np.isfinite(rep['economy_coupled_census_equivalent']).all());ck('economic_indices_bounded',rep['economic_state'].min()>=0 and rep['economic_state'].max()<=1);ck('census_positive',(rep['economy_coupled_census_equivalent']>=0).all());ck('census_parent_anchor_exact',np.max(np.abs(rep['economy_coupled_census_equivalent'][:,:,0]-rep['parent_census_equivalent'][:,:,0]))<1e-9);ck('census_multiplier_bounded',rep['economy_census_multiplier'].min()>=float(cfg['economy_census_multiplier_min'])-1e-12 and rep['economy_census_multiplier'].max()<=float(cfg['economy_census_multiplier_max'])+1e-12);ck('group_census_closure',np.max(np.abs(rep['economy_coupled_group_count_equivalent']*rep['economy_coupled_group_mean_size']-rep['economy_coupled_census_equivalent']))<1e-8);ck('sensitivity_15',sens['variant_count']==15);ck('sensitivity_no_selection',sens['selection_gate'] is False);ck('pathway_enum',all(x['resolved_economic_pathway'] in {'DISTRIBUTED_MANAGED_FORAGER_ECONOMY','SEASONALLY_AGGREGATED_EXCHANGE_ECONOMY','PERSISTENT_CENTRAL_PLACE_FORAGER_ECONOMY','REGIONAL_COMPLEX_FORAGER_ECONOMY'} for x in outs['lineages']));ck('no_agriculture',outs['agriculture_materialized'] is False);ck('no_village_city_state',outs['village_city_state_materialized'] is False);ck('no_class_hierarchy',outs['class_hierarchy_materialized'] is False);ck('no_currency_market',outs['currency_market_materialized'] is False);ck('no_lineage_rescale',cfg['governance']['no_lineage_specific_rescaling'] is True);ck('deep_off',cfg['governance']['deep_biological_coupling'] is False);ck('evidence_multisource',len(EVIDENCE)>=9)
 failed=[x for x in checks if not x['pass']]
 return {'stage':STAGE,'status':CANDIDATE_PASS if not failed else 'FAIL_R337_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'checks':checks,'summary':{'candidate_lineages':2,'time_states':145,'economic_variables':len(ECON_NAMES),'economic_anchor_states':9,'weighted_economic_nodes_max_per_lineage_member':48,'resolved_economic_pathways':{x['lineage_id']:x['resolved_economic_pathway'] for x in outs['lineages']},'agriculture_materialized':False,'village_city_state_materialized':False,'class_hierarchy_materialized':False,'deep_biological_coupling':False}}

def build_outputs(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],out:Path)->dict[str,Any]:
 out.mkdir(parents=True,exist_ok=True);outs,sens,cp=summarize(inp,rep,cfg)
 auth={'stage':STAGE,'status':'R337_INTENSIVE_MANAGED_FORAGER_ECONOMY_AUTHORITY','parent':PARENT_PASS,'required_parent_pathway':'INTENSIVE_MANAGED_FORAGER_PATHWAY','candidate_cohort':EXPECTED_CANDIDATES,'window_ka':[20.0,0.0],'economy_semantics':'DIMENSIONLESS_ECONOMIC_CAPACITY_AND_PRESSURE_STATES_DERIVED_FROM_SEALED_CENSUS_GROUP_TECHNOLOGY_SUBSISTENCE_AND_MANAGED_RESOURCE_AUTHORITIES','census_semantics':'ECONOMY_COUPLED_CENSUS_EQUIVALENT_IS_A_BOUNDED_DOWNSTREAM_POSTERIOR_AND_NOT_AN_ARCHAEOLOGICAL_HEADCOUNT_OBSERVATION','settlement_semantics':'PERSISTENT_CENTRAL_PLACE_POTENTIAL_IS_NOT_A_VILLAGE_TOWN_OR_CITY','surplus_semantics':'RESOURCE_SURPLUS_BUFFER_IS_A_BUFFERING_CAPACITY_INDEX_NOT_LITERAL_STORED_CALORIES','inequality_semantics':'RESOURCE_CONTROL_ASYMMETRY_PRESSURE_IS_DIAGNOSTIC_ONLY_AND_NEVER_MATERIALIZED_SOCIAL_CLASS_OR_HIERARCHY','agriculture_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False,'evidence_basis':EVIDENCE,'dynamics':cfg,'parent_hashes':{'r330_census_sha256':sha256_file(inp['r30']/'R3_30_CENSUS_AND_GROUP_TIMESERIES.npz'),'r331_technology_sha256':sha256_file(inp['r31']/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz'),'r332_subsistence_sha256':sha256_file(inp['r32']/'R3_32_SUBSISTENCE_AND_TRANSITION_REPLAY.npz'),'r336_replay_sha256':sha256_file(inp['r36']/'R3_36_DOMESTICATION_SELECTION_ECOLOGY_REPLAY.npz')}}
 write_json(out/'R3_37_MANAGED_FORAGER_ECONOMY_AUTHORITY.json',auth)
 np.savez_compressed(out/'R3_37_MANAGED_FORAGER_ECONOMY_REPLAY.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z36']['parent_member_indices'],age_ka=rep['age_ka'],economic_variable_names=np.array(ECON_NAMES),economic_state=rep['economic_state'],economy_census_multiplier=rep['economy_census_multiplier'],economy_coupled_census_equivalent=rep['economy_coupled_census_equivalent'],economy_coupled_group_count_equivalent=rep['economy_coupled_group_count_equivalent'],economy_coupled_group_mean_size=rep['economy_coupled_group_mean_size'],parent_census_equivalent=rep['parent_census_equivalent'])
 np.savez_compressed(out/'R3_37_WEIGHTED_ECONOMIC_NODES.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z36']['parent_member_indices'],anchor_age_ka=rep['anchor_age_ka'],economic_node_variable_names=np.array(NODE_NAMES),economic_node_state=rep['economic_node_state'],economic_node_active=rep['economic_node_active'])
 write_json(out/'R3_37_LINEAGE_ECONOMY_OUTCOMES.json',outs);write_json(out/'R3_37_SENSITIVITY_AND_ROBUSTNESS.json',sens);write_json(out/'R3_37_ECONOMY_PATHWAY_CHECKPOINT.json',cp)
 audit=_audit(inp,cfg,rep,outs,sens);write_json(out/'R3_37_INTEGRATED_AUDIT.json',audit);(out/'R3_37_AUDIT.md').write_text(f"# R3.37 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n- Pathways: `{audit['summary']['resolved_economic_pathways']}`\n",encoding='utf-8');return audit

def write_manifest(out:Path,status:str)->None:
 files={}
 for p in sorted(out.iterdir()):
  if p.name=='R3_37_OUTPUT_MANIFEST.json' or not p.is_file(): continue
  files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_37_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
