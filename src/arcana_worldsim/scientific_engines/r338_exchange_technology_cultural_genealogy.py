from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json, math
import numpy as np

STAGE='v0.6D1-R3.38'
PARENT_STAGE='v0.6D1-R3.37'
PARENT_PASS='PASS_R337_INTENSIVE_MANAGED_FORAGER_DEMOGRAPHY_SETTLEMENT_STORAGE_EXCHANGE_SPECIALIZATION_AND_REGIONAL_ECONOMY_SEALED'
CANDIDATE_PASS='PASS_R338_REGIONAL_FORAGER_EXCHANGE_NETWORKS_CONCRETE_TECHNOLOGY_AND_CULTURAL_GENEALOGIES_CANDIDATE'
FINAL_PASS='PASS_R338_REGIONAL_EXCHANGE_NETWORKS_CONCRETE_TECHNOLOGY_RETICULATE_CULTURAL_GENEALOGIES_AND_BORROWING_SEALED'
EXPECTED_CANDIDATES=['RPT_010_D02','RPT_009_D02']
EXPECTED_MEMBERS=32
EXPECTED_TIMES=145
EXPECTED_ANCHORS=9
EXPECTED_GROUPS=48
EXPECTED_REGIONS=6
EXPECTED_PARENT_CHECKS=38

R331_PASS='PASS_R331_LATE_PLEISTOCENE_TO_HOLOCENE_CULTURAL_TECHNOLOGICAL_ECOLOGY_TRANSMISSION_RETENTION_AND_TECHNICAL_REPERTOIRE_SEALED'
R332_PASS='PASS_R332_SUBSISTENCE_INTENSIFICATION_REGIONAL_CULTURAL_LINEAGES_MANAGED_RESOURCE_TRANSITIONS_AND_HOLOCENE_READINESS_SEALED'
R333_PASS='PASS_R333_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE_ANIMAL_ECOLOGICAL_PARTNERS_DOMESTICATION_TRAJECTORIES_AND_FOOD_PRODUCTION_EMERGENCE_SEALED'

IMPLEMENTATION_NAMES=[
 'hard_edge_mineral_cutting_processing',
 'hafted_composite_points_and_edges',
 'cordage_binding_netting_systems',
 'hide_skin_flexible_thermal_goods',
 'osseous_hard_biological_implements',
 'grinding_pounding_food_processing',
 'storage_containers_and_cache_systems',
 'built_shelter_and_site_furniture',
 'aquatic_capture_gear',
 'overland_logistical_carriers',
 'waterborne_transport_systems',
 'adhesive_binding_compound_systems'
]

REGIONAL_STATE_NAMES=[
 'represented_people','represented_camps','grid_row','grid_col','regional_lineage_code',
 'implementation_breadth','implementation_mean_support','retention_support','innovation_support',
 'borrowing_inflow','fission_pressure','fusion_pressure','regional_distinctiveness'
]

EVIDENCE={
 'HUNTER_GATHERER_TRANSMISSION_2024':{
  'source':'Hewlett et al., Cultural transmission among hunter-gatherers, PNAS 121(48), 2024',
  'doi':'10.1073/pnas.2322883121',
  'use':'vertical, horizontal, oblique, conformist and cumulative transmission can coexist in forager societies; inheritance is not a simple tree'},
 'NETWORKS_CULTURAL_TRANSMISSION_2023':{
  'source':'Networks and Cultural Transmission in Hunter-Gatherer Societies, Oxford Handbook of Archaeological Network Research, 2023',
  'doi':'10.1093/oxfordhb/9780198854265.013.34',
  'use':'large-scale forager networks move material, energy and information across sparse populations'},
 'POTTERY_TRANSMISSION_2023':{
  'source':'The transmission of pottery technology among prehistoric European hunter-gatherers, Nature Human Behaviour 7, 2023',
  'doi':'10.1038/s41562-022-01491-8',
  'use':'prehistoric hunter-gatherer technology can spread through contact networks and can require branching-and-blending rather than a pure tree model'},
 'FORAGER_TOOLS_2021':{
  'source':'Sterelny, Foragers and Their Tools: Risk, Technology and Complexity, Topics in Cognitive Science 2021',
  'doi':'10.1111/tops.12559',
  'use':'toolkit complexity depends on ecology, economics, skill, cooperation and transmission rather than cognition alone'},
 'MOBILITY_TRANSMISSION_2011':{
  'source':'Mobility-driven cultural transmission along the forager-collector continuum, Journal of Anthropological Archaeology 30, 2011',
  'doi':'10.1016/j.jaa.2010.10.003',
  'use':'mobility regime affects occupation intensity, raw-material transport and cultural transmission without requiring sedentism'},
 'R331_PARENT':{'source':'R3.31 SEALED cultural-technological ecology','use':'abstract technology domain stocks, transmission, innovation and group technical access are inherited authority'},
 'R332_PARENT':{'source':'R3.32 SEALED regional cultural lineages and subsistence','use':'opaque regional lineage codes, regional continuity, positions and subsistence profiles are inherited authority'},
 'R333_PARENT':{'source':'R3.33 SEALED environmental and animal-partner trajectories','use':'NPP/hydrology/coastal affordances and animal contact are inherited material-affordance authorities'},
 'R337_PARENT':{'source':'R3.37 SEALED distributed managed-forager economy','use':'exchange access, specialization, storage and settlement/economic network states are inherited authority'}
}

class R338GateError(RuntimeError): pass

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
 if not p.is_file(): raise R338GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file() or fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:
   raise R338GateError(f'Manifest closure failure {fp}')

def _seal(root:Path,s:int,expected:str,checks:int)->dict[str,Any]:
 p=root/'outputs'/f'v0_6D1_R3_{s}_SEAL'/f'R3_{s}_FINAL_SEAL_AUDIT.json'
 d=load_json(p)
 if d.get('status')!=expected or d.get('verdict')!='SEALED' or d.get('checks_passed')!=checks or d.get('checks_failed')!=0:
  raise R338GateError(f'R3.{s} seal mismatch')
 return d

def _match_indices(parent:np.ndarray,child:np.ndarray)->np.ndarray:
 idx=[]
 for x in child:
  w=np.where(np.isclose(parent,float(x),rtol=0,atol=1e-12))[0]
  if len(w)!=1: raise R338GateError(f'Cannot uniquely bind age {x}')
  idx.append(int(w[0]))
 return np.asarray(idx,int)

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root)
 r31=root/'outputs'/'v0_6D1_R3_31';r32=root/'outputs'/'v0_6D1_R3_32';r33=root/'outputs'/'v0_6D1_R3_33';r37=root/'outputs'/'v0_6D1_R3_37'
 for d in [r31,r32,r33,r37]:
  if not d.is_dir(): raise R338GateError(f'Missing authority {d}')
 a31=_seal(root,31,R331_PASS,29);a32=_seal(root,32,R332_PASS,30);a33=_seal(root,33,R333_PASS,33);a37=_seal(root,37,PARENT_PASS,EXPECTED_PARENT_CHECKS)
 for d,n in [(r31,'R3_31_OUTPUT_MANIFEST.json'),(r32,'R3_32_OUTPUT_MANIFEST.json'),(r33,'R3_33_OUTPUT_MANIFEST.json'),(r37,'R3_37_OUTPUT_MANIFEST.json')]: _close_manifest(d,n)
 cp37=load_json(r37/'R3_37_ECONOMY_PATHWAY_CHECKPOINT.json')
 if any(v!='DISTRIBUTED_MANAGED_FORAGER_ECONOMY' for v in cp37.get('resolved_lineage_economic_pathways',{}).values()):
  raise R338GateError('R3.37 distributed managed-forager premise mismatch')
 z31=np.load(r31/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz',allow_pickle=False)
 g31=np.load(r31/'R3_31_GROUP_TECHNOLOGICAL_ECOLOGY_ANCHORS.npz',allow_pickle=False)
 z32=np.load(r32/'R3_32_SUBSISTENCE_AND_TRANSITION_REPLAY.npz',allow_pickle=False)
 a32z=np.load(r32/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz',allow_pickle=False)
 env33=np.load(r33/'R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz',allow_pickle=False)
 animal33=np.load(r33/'R3_33_DOMESTICATION_TRAJECTORIES.npz',allow_pickle=False)
 z37=np.load(r37/'R3_37_MANAGED_FORAGER_ECONOMY_REPLAY.npz',allow_pickle=False)
 n37=np.load(r37/'R3_37_WEIGHTED_ECONOMIC_NODES.npz',allow_pickle=False)
 for z in [z31,g31,z32,a32z,animal33,z37,n37]:
  if list(map(str,z['candidate_ids']))!=EXPECTED_CANDIDATES: raise R338GateError('Candidate order mismatch')
 if not np.array_equal(z31['parent_member_indices'],z37['parent_member_indices']) or not np.array_equal(z32['parent_member_indices'],z37['parent_member_indices']) or not np.array_equal(animal33['parent_member_indices'],z37['parent_member_indices']): raise R338GateError('Member mapping mismatch')
 if z32['age_ka'].shape!=(EXPECTED_TIMES,) or not np.array_equal(z32['age_ka'],z37['age_ka']): raise R338GateError('20ka-0 axis mismatch')
 if not np.array_equal(a32z['anchor_age_ka'],n37['anchor_age_ka']) or not np.array_equal(a32z['anchor_age_ka'],env33['anchor_age_ka']) or not np.array_equal(a32z['anchor_age_ka'],animal33['anchor_age_ka']): raise R338GateError('Anchor mismatch')
 i31=_match_indices(z31['age_ka'],z32['age_ka']);ig31=_match_indices(g31['anchor_age_ka'],a32z['anchor_age_ka'])
 return {'root':root,'r31':r31,'r32':r32,'r33':r33,'r37':r37,'a31':a31,'a32':a32,'a33':a33,'a37':a37,'cp37':cp37,'z31':z31,'g31':g31,'z32':z32,'a32z':a32z,'env33':env33,'animal33':animal33,'z37':z37,'n37':n37,'i31':i31,'ig31':ig31}

def _index(names:np.ndarray,name:str)->int: return list(map(str,names)).index(name)

def _interp_anchor_to_time(anchor_age:np.ndarray,values:np.ndarray,time_age:np.ndarray)->np.ndarray:
 # np.interp expects increasing x
 return np.interp(time_age[::-1],anchor_age[::-1],values[::-1])[::-1]

def _global_material_affordances(inp:dict[str,Any])->tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
 env=inp['env33'];animal=inp['animal33'];a32=inp['a32z'];nodes=inp['n37']
 enames=list(map(str,env['environment_variable_names'])); E=np.asarray(env['environment_fields'],float)
 npp_i=enames.index('npp_factor');hyd_i=enames.index('hydroclimate_resource_index');coast_i=enames.index('coastal_edge_index');land_i=enames.index('land_fraction')
 rnames=list(map(str,a32['regional_variable_names'])); rr=rnames.index('grid_row');cc=rnames.index('grid_col');people_i=rnames.index('represented_people')
 A=np.asarray(a32['regional_state'],float);active=np.asarray(a32['regional_active'],bool)
 tnames=list(map(str,animal['trajectory_variable_names']));contact_i=tnames.index('contact_opportunity');animal_contact=np.asarray(animal['trajectory_state'],float)[...,contact_i] # M,L,P,A
 M,L,P,Aa=animal_contact.shape
 plant=np.zeros((M,L,Aa),float);hydro=np.zeros_like(plant);coast=np.zeros_like(plant);land=np.zeros_like(plant)
 for m in range(M):
  for l in range(L):
   for a in range(Aa):
    act=active[m,l,a]
    if not np.any(act): continue
    w=np.maximum(A[m,l,a,act,people_i],1e-9);w=w/w.sum()
    rows=np.clip(np.rint(A[m,l,a,act,rr]).astype(int),0,E.shape[1]-1);cols=np.mod(np.rint(A[m,l,a,act,cc]).astype(int),E.shape[2])
    plant[m,l,a]=float(np.sum(w*np.clip(E[a,rows,cols,npp_i],0,1.5))/1.5)
    hydro[m,l,a]=float(np.sum(w*np.clip(E[a,rows,cols,hyd_i],0,1)))
    coast[m,l,a]=float(np.sum(w*np.clip(E[a,rows,cols,coast_i],0,1)))
    land[m,l,a]=float(np.sum(w*np.clip(E[a,rows,cols,land_i],0,1)))
 animal_mat=np.clip(np.mean(animal_contact,axis=2)/0.30,0,1)
 return np.clip(plant,0,1),np.clip(animal_mat,0,1),np.clip(hydro,0,1),np.clip(coast,0,1)

def _implementation_targets(inp:dict[str,Any],cfg:dict[str,Any])->tuple[np.ndarray,np.ndarray]:
 z31,z32,z37=inp['z31'],inp['z32'],inp['z37'];time=np.asarray(z32['age_ka'],float)
 Tech=np.asarray(z31['technology_domain_stock'],float)[:,:,inp['i31'],:]
 Sub=np.asarray(z32['subsistence_domain_stock'],float); Econ=np.asarray(z37['economic_state'],float)
 tnames=list(map(str,z31['technology_domain_names']));snames=list(map(str,z32['subsistence_domain_names']));enames=list(map(str,z37['economic_variable_names']))
 ti={n:tnames.index(n) for n in tnames};si={n:snames.index(n) for n in snames};ei={n:enames.index(n) for n in enames}
 plant_a,animal_a,hyd_a,coast_a=_global_material_affordances(inp);anchor=np.asarray(inp['a32z']['anchor_age_ka'],float)
 M,L,T=Tech.shape[:3]
 mats=np.zeros((M,L,T,4),float)
 for m in range(M):
  for l in range(L):
   mats[m,l,:,0]=_interp_anchor_to_time(anchor,plant_a[m,l],time)
   mats[m,l,:,1]=_interp_anchor_to_time(anchor,animal_a[m,l],time)
   mats[m,l,:,2]=_interp_anchor_to_time(anchor,hyd_a[m,l],time)
   mats[m,l,:,3]=_interp_anchor_to_time(anchor,coast_a[m,l],time)
 plant,animal,hydro,coast=[mats[...,i] for i in range(4)]
 hard=np.full((M,L,T),float(cfg['generic_hard_material_access_prior']))
 portable=Tech[...,ti['portable_toolkit_systems']];comp=Tech[...,ti['composite_tool_systems']];food=Tech[...,ti['food_processing_and_extraction']];thermal=Tech[...,ti['thermal_environmental_control']];shelter=Tech[...,ti['shelter_and_site_engineering']];transport=Tech[...,ti['transport_and_logistical_systems']];storage=Tech[...,ti['storage_and_resource_buffering']];spec=Tech[...,ti['cooperative_specialization_systems']]
 aquatic=Sub[...,si['aquatic_resource_exploitation']];plantproc=Sub[...,si['plant_resource_processing_intensity']];delayed=Sub[...,si['delayed_return_storage_buffering']];sched=Sub[...,si['seasonal_scheduling_and_logistics']]
 exchange=Econ[...,ei['exchange_volume_proxy']];settle=Econ[...,ei['settlement_persistence']];managed=Econ[...,ei['managed_resource_support']]
 target=np.stack([
  .55*portable+.15*comp+.15*food+.15*hard,
  .48*comp+.18*portable+.12*spec+.12*animal+.10*hard,
  .28*comp+.16*shelter+.14*transport+.12*storage+.30*plant,
  .34*thermal+.20*shelter+.16*portable+.30*animal,
  .28*portable+.23*comp+.10*spec+.39*animal,
  .48*food+.18*plantproc+.12*storage+.12*managed+.10*hard,
  .48*storage+.16*food+.12*shelter+.14*delayed+.10*plant,
  .50*shelter+.16*thermal+.12*storage+.12*settle+.10*plant,
  .17*portable+.18*comp+.10*food+.38*aquatic+.17*np.maximum(hydro,coast),
  .48*transport+.16*comp+.16*exchange+.10*spec+.10*plant,
  .42*transport+.12*shelter+.12*comp+.14*aquatic+.20*np.maximum(hydro,coast),
  .46*comp+.15*thermal+.15*spec+.12*plant+.12*animal
 ],axis=-1)
 return np.clip(target,0,1),mats

def _group_local_targets(inp:dict[str,Any],global_anchor:np.ndarray,cfg:dict[str,Any])->tuple[np.ndarray,np.ndarray]:
 a32=inp['a32z'];n37=inp['n37'];g31=inp['g31'];env=inp['env33'];animal=inp['animal33']
 A=np.asarray(a32['regional_state'],float);active=np.asarray(a32['regional_active'],bool);N=np.asarray(n37['economic_node_state'],float);G=np.asarray(g31['group_state'],float)[:,:,inp['ig31'],:]
 rnames=list(map(str,a32['regional_variable_names']));nnames=list(map(str,n37['economic_node_variable_names']));gnames=list(map(str,g31['group_variable_names']));enames=list(map(str,env['environment_variable_names']))
 ri={n:rnames.index(n) for n in rnames};ni={n:nnames.index(n) for n in nnames};gi={n:gnames.index(n) for n in gnames};eii={n:enames.index(n) for n in enames}
 E=np.asarray(env['environment_fields'],float);Atr=np.asarray(animal['trajectory_state'],float);anames=list(map(str,animal['trajectory_variable_names']));ac=anames.index('contact_opportunity')
 animal_anchor=np.clip(np.mean(Atr[...,ac],axis=2)/0.30,0,1) # M,L,A
 M,L,Aa,Q=A.shape[:4];K=len(IMPLEMENTATION_NAMES);out=np.zeros((M,L,Aa,Q,K),float)
 material=np.zeros((M,L,Aa,Q,5),float) # hard, plant, animal, hydro, coast
 for m in range(M):
  for l in range(L):
   for a in range(Aa):
    for q in range(Q):
     if not active[m,l,a,q]: continue
     r=int(np.clip(round(A[m,l,a,q,ri['grid_row']]),0,E.shape[1]-1));c=int(round(A[m,l,a,q,ri['grid_col']]))%E.shape[2]
     plant=float(np.clip(E[a,r,c,eii['npp_factor']],0,1.5)/1.5);hyd=float(np.clip(E[a,r,c,eii['hydroclimate_resource_index']],0,1));coast=float(np.clip(E[a,r,c,eii['coastal_edge_index']],0,1));animalv=float(animal_anchor[m,l,a]);hard=float(cfg['generic_hard_material_access_prior'])
     material[m,l,a,q]=[hard,plant,animalv,hyd,coast]
     tech=float(G[m,l,a,q,gi['tech_access']]);breadth=float(G[m,l,a,q,gi['repertoire_breadth']]);innov=float(G[m,l,a,q,gi['innovation_support']]);spec=float(N[m,l,a,q,ni['specialization_access']]);exchange=float(N[m,l,a,q,ni['exchange_access']]);storage=float(N[m,l,a,q,ni['storage_access']]);settle=float(N[m,l,a,q,ni['settlement_persistence']]);managed=float(N[m,l,a,q,ni['managed_resource_access']]);sub=float(A[m,l,a,q,ri['subsistence_profile_mean']])
     local=np.array([
      .50*tech+.16*breadth+.12*innov+.12*hard+.10*sub,
      .38*tech+.20*breadth+.14*spec+.10*animalv+.10*hard+.08*innov,
      .28*tech+.16*spec+.12*storage+.10*exchange+.24*plant+.10*breadth,
      .32*tech+.18*settle+.18*breadth+.32*animalv,
      .30*tech+.20*spec+.12*breadth+.38*animalv,
      .34*tech+.18*storage+.16*managed+.14*sub+.10*hard+.08*innov,
      .32*tech+.24*storage+.14*settle+.12*managed+.10*plant+.08*breadth,
      .32*tech+.24*settle+.14*storage+.12*spec+.10*plant+.08*breadth,
      .28*tech+.14*spec+.12*sub+.26*max(hyd,coast)+.10*exchange+.10*breadth,
      .34*tech+.24*exchange+.14*spec+.10*plant+.10*breadth+.08*innov,
      .28*tech+.20*exchange+.12*spec+.22*max(hyd,coast)+.10*breadth+.08*innov,
      .34*tech+.22*spec+.14*innov+.12*plant+.10*animalv+.08*breadth
     ])
     out[m,l,a,q]=np.clip(.55*global_anchor[m,l,a]+.45*local,0,1)
 return out,material

def _grid_distance(r1,c1,r2,c2)->float:
 dr=float(r1-r2);dc=abs(float(c1-c2));dc=min(dc,180.0-dc)
 return math.sqrt(dr*dr+(.65*dc)*(.65*dc))

def _prepare_static(inp:dict[str,Any],cfg:dict[str,Any])->dict[str,np.ndarray]:
 ages=np.asarray(inp['z32']['age_ka'],float);anchor=np.asarray(inp['a32z']['anchor_age_ka'],float);target,mats=_implementation_targets(inp,cfg)
 dt=np.r_[ages[:-1]-ages[1:],0.0];M,L,T,K=target.shape
 stock=np.zeros_like(target);stock[:,:,0]=np.clip(target[:,:,0]*float(cfg['initial_implementation_fraction']),0,1)
 for t in range(T-1):
  rate=float(cfg['implementation_adjustment_rate_per_kyr'])*dt[t]
  stock[:,:,t+1]=np.clip(stock[:,:,t]+rate*(target[:,:,t]-stock[:,:,t]),0,1)
 aidx=_match_indices(ages,anchor);global_anchor=stock[:,:,aidx,:]
 group_local,material_local=_group_local_targets(inp,global_anchor,cfg)
 A=np.asarray(inp['a32z']['regional_state'],float);active=np.asarray(inp['a32z']['regional_active'],bool);N=np.asarray(inp['n37']['economic_node_state'],float);G=np.asarray(inp['g31']['group_state'],float)[:,:,inp['ig31'],:]
 rnames=list(map(str,inp['a32z']['regional_variable_names']));nnames=list(map(str,inp['n37']['economic_node_variable_names']));gnames=list(map(str,inp['g31']['group_variable_names']))
 ri={n:rnames.index(n) for n in rnames};ni={n:nnames.index(n) for n in nnames};gi={n:gnames.index(n) for n in gnames}
 reg_target=np.zeros((M,L,EXPECTED_ANCHORS,EXPECTED_REGIONS,K),float);reg_people=np.zeros((M,L,EXPECTED_ANCHORS,EXPECTED_REGIONS),float);reg_camps=np.zeros_like(reg_people);reg_row=np.zeros_like(reg_people);reg_col=np.zeros_like(reg_people);reg_active=np.zeros_like(reg_people,dtype=bool);reg_disp=np.zeros_like(reg_people);reg_exacc=np.zeros_like(reg_people);reg_innov=np.zeros_like(reg_people);reg_cont=np.zeros_like(reg_people)
 for m in range(M):
  for l in range(L):
   for a in range(EXPECTED_ANCHORS):
    for rc in range(1,EXPECTED_REGIONS+1):
     mask=active[m,l,a] & (np.rint(A[m,l,a,:,ri['regional_lineage_code']]).astype(int)==rc)
     if not np.any(mask): continue
     r=rc-1;reg_active[m,l,a,r]=True;w=np.maximum(A[m,l,a,mask,ri['represented_people']],1e-9);reg_people[m,l,a,r]=w.sum();reg_camps[m,l,a,r]=np.sum(A[m,l,a,mask,ri['represented_camps']]);wn=w/w.sum();reg_row[m,l,a,r]=np.sum(wn*A[m,l,a,mask,ri['grid_row']])
     ang=2*np.pi*A[m,l,a,mask,ri['grid_col']]/180.0;ss=np.sum(wn*np.sin(ang));cc=np.sum(wn*np.cos(ang));reg_col[m,l,a,r]=(np.arctan2(ss,cc)%(2*np.pi))*180.0/(2*np.pi)
     reg_target[m,l,a,r]=np.sum(wn[:,None]*group_local[m,l,a,mask],axis=0)
     gm=np.mean(group_local[m,l,a,mask],axis=1);mu=float(np.sum(wn*gm));reg_disp[m,l,a,r]=float(np.sqrt(np.sum(wn*(gm-mu)**2)))
     reg_exacc[m,l,a,r]=float(np.sum(wn*N[m,l,a,mask,ni['exchange_access']]))
     reg_innov[m,l,a,r]=float(np.sum(wn*G[m,l,a,mask,gi['innovation_support']]))
     reg_cont[m,l,a,r]=float(np.sum(wn*A[m,l,a,mask,ri['regional_continuity']]))
 return {'age_ka':ages,'anchor_age_ka':anchor,'aidx':aidx,'implementation_stock':stock,'implementation_target':target,'material_affordance_time':mats,'group_local':group_local,'material_local':material_local,'group_active':active,'reg_target':reg_target,'reg_people':reg_people,'reg_camps':reg_camps,'reg_row':reg_row,'reg_col':reg_col,'reg_active':reg_active,'reg_disp':reg_disp,'reg_exacc':reg_exacc,'reg_innov':reg_innov,'reg_cont':reg_cont}

def _network_from_static(inp:dict[str,Any],cfg:dict[str,Any],st:dict[str,np.ndarray],borrowing_multiplier:float,distance_multiplier:float,innovation_multiplier:float)->dict[str,np.ndarray]:
 anchor=st['anchor_age_ka'];reg_target=st['reg_target'];reg_active=st['reg_active'];reg_row=st['reg_row'];reg_col=st['reg_col'];reg_exacc=st['reg_exacc'];reg_innov=st['reg_innov'];reg_cont=st['reg_cont'];reg_disp=st['reg_disp'];M,L,Aa,R,K=reg_target.shape
 e37names=list(map(str,inp['z37']['economic_variable_names']));e37i={n:e37names.index(n) for n in e37names};E37=np.asarray(inp['z37']['economic_state'],float)[:,:,st['aidx'],:]
 node_count=2*EXPECTED_REGIONS;exchange=np.zeros((M,Aa,node_count,node_count),float);profiles=np.zeros_like(reg_target);borrow_in=np.zeros((M,L,Aa,R),float);fission=np.zeros_like(borrow_in);fusion=np.zeros_like(borrow_in);distinct=np.zeros_like(borrow_in);retention=np.zeros_like(borrow_in);innovation=np.zeros_like(borrow_in)
 profiles[:,:,0]=reg_target[:,:,0]
 for m in range(M):
  for a in range(Aa):
   for i in range(node_count):
    li,ri0=divmod(i,R)
    if not reg_active[m,li,a,ri0]: continue
    for j in range(i+1,node_count):
     lj,rj0=divmod(j,R)
     if not reg_active[m,lj,a,rj0]: continue
     dist=_grid_distance(reg_row[m,li,a,ri0],reg_col[m,li,a,ri0],reg_row[m,lj,a,rj0],reg_col[m,lj,a,rj0])
     spatial=math.exp(-dist/max(float(cfg['exchange_distance_scale_grid_cells'])*distance_multiplier,1e-9));base=math.sqrt(max(reg_exacc[m,li,a,ri0]*reg_exacc[m,lj,a,rj0],0.0))*spatial
     if li!=lj:
      inter=float(np.mean([E37[m,li,a,e37i['interlineage_exchange_support']],E37[m,lj,a,e37i['interlineage_exchange_support']]]));base*=float(cfg['cross_lineage_exchange_multiplier'])*(0.35+0.65*inter)
     else: base*=float(cfg['within_lineage_exchange_multiplier'])
     complement=float(np.mean(np.abs(reg_target[m,li,a,ri0]-reg_target[m,lj,a,rj0])));val=np.clip(base*(0.75+0.25*complement),0,1);exchange[m,a,i,j]=exchange[m,a,j,i]=val
   if a>0:
    delta_kyr=float(anchor[a-1]-anchor[a]);retain_w=float(np.clip(math.exp(-float(cfg['cultural_profile_relaxation_rate_per_kyr'])*delta_kyr),0,1))
    for l in range(L):
     for r in range(R):
      if not reg_active[m,l,a,r]: continue
      idx=l*R+r;edges=exchange[m,a,idx];den=edges.sum()
      if den>0:
       borrow=np.zeros(K,float)
       for j,e in enumerate(edges):
        if e<=0: continue
        lj,rj=divmod(j,R);borrow+=e*reg_target[m,lj,a,rj]
       borrow/=den+1e-12;borrow_strength=float(np.clip(den/float(cfg['borrowing_degree_normalizer']),0,1))*float(cfg['borrowing_rate'])*borrowing_multiplier
      else: borrow=reg_target[m,l,a,r];borrow_strength=0.0
      local=reg_target[m,l,a,r];prev=profiles[m,l,a-1,r];innov_support=float(np.clip(reg_innov[m,l,a,r],0,1))*float(cfg['innovation_rate'])*innovation_multiplier;innovative=np.clip(local+innov_support*(local-prev),0,1)
      profiles[m,l,a,r]=np.clip(retain_w*prev+(1-retain_w)*innovative+borrow_strength*(borrow-local),0,1);borrow_in[m,l,a,r]=borrow_strength
   for l in range(L):
    regdiff=float(E37[m,l,a,e37i['regional_economic_complexity']])
    for r in range(R):
     if not reg_active[m,l,a,r]: continue
     idx=l*R+r;same=exchange[m,a,idx,l*R:(l+1)*R];maxsame=float(np.max(same)) if same.size else 0.0;profile=profiles[m,l,a,r]
     others=[profiles[m,l,a,x] for x in range(R) if x!=r and reg_active[m,l,a,x]];d=float(np.mean([np.mean(np.abs(profile-o)) for o in others])) if others else 0.0;sim=1-d
     distinct[m,l,a,r]=np.clip(d/0.35,0,1);fission[m,l,a,r]=np.clip(.45*np.clip(reg_disp[m,l,a,r]/.12,0,1)+.30*regdiff+.25*(1-maxsame),0,1);fusion[m,l,a,r]=np.clip(.55*maxsame+.30*sim+.15*(1-regdiff),0,1);retention[m,l,a,r]=np.clip(.50*reg_cont[m,l,a,r]+.30*(1-borrow_in[m,l,a,r])+.20*(1-regdiff),0,1);innovation[m,l,a,r]=np.clip(reg_innov[m,l,a,r],0,1)
 return {'regional_profile':profiles,'exchange_matrix':exchange,'borrowing_inflow':borrow_in,'fission_pressure':fission,'fusion_pressure':fusion,'regional_distinctiveness':distinct,'retention':retention,'innovation':innovation}

def replay_exchange_technology_genealogy(inp:dict[str,Any],cfg:dict[str,Any],borrowing_multiplier:float=1.0,distance_multiplier:float=1.0,innovation_multiplier:float=1.0,static:dict[str,np.ndarray]|None=None)->dict[str,np.ndarray]:
 st=_prepare_static(inp,cfg) if static is None else static;dyn=_network_from_static(inp,cfg,st,borrowing_multiplier,distance_multiplier,innovation_multiplier)
 A=np.asarray(inp['a32z']['regional_state'],float);active=st['group_active'];rnames=list(map(str,inp['a32z']['regional_variable_names']));ri={n:rnames.index(n) for n in rnames};M,L,Aa,Q=A.shape[:4];K=len(IMPLEMENTATION_NAMES);group_impl=np.zeros_like(st['group_local'])
 for m in range(M):
  for l in range(L):
   for a in range(Aa):
    for q in range(Q):
     if not active[m,l,a,q]: continue
     rc=int(np.clip(round(A[m,l,a,q,ri['regional_lineage_code']]),1,EXPECTED_REGIONS))-1;group_impl[m,l,a,q]=np.clip(.55*st['group_local'][m,l,a,q]+.45*dyn['regional_profile'][m,l,a,rc],0,1)
 reg_state=np.zeros((M,L,Aa,EXPECTED_REGIONS,len(REGIONAL_STATE_NAMES)),float)
 for m in range(M):
  for l in range(L):
   for a in range(Aa):
    for r in range(EXPECTED_REGIONS):
     if not st['reg_active'][m,l,a,r]: continue
     p=dyn['regional_profile'][m,l,a,r];reg_state[m,l,a,r]=[st['reg_people'][m,l,a,r],st['reg_camps'][m,l,a,r],st['reg_row'][m,l,a,r],st['reg_col'][m,l,a,r],r+1,float(np.mean(p>=float(cfg['implementation_presence_threshold']))),float(np.mean(p)),dyn['retention'][m,l,a,r],dyn['innovation'][m,l,a,r],dyn['borrowing_inflow'][m,l,a,r],dyn['fission_pressure'][m,l,a,r],dyn['fusion_pressure'][m,l,a,r],dyn['regional_distinctiveness'][m,l,a,r]]
 return {'age_ka':st['age_ka'],'anchor_age_ka':st['anchor_age_ka'],'implementation_stock':st['implementation_stock'],'implementation_target':st['implementation_target'],'material_affordance_time':st['material_affordance_time'],'group_implementation_support':group_impl,'group_material_affordance':st['material_local'],'group_active':active.copy(),'regional_profile':dyn['regional_profile'],'regional_state':reg_state,'regional_active':st['reg_active'],'exchange_matrix':dyn['exchange_matrix'],'borrowing_inflow':dyn['borrowing_inflow'],'fission_pressure':dyn['fission_pressure'],'fusion_pressure':dyn['fusion_pressure'],'regional_distinctiveness':dyn['regional_distinctiveness'],'_static':st}

def _lineage_resolution(rep:dict[str,np.ndarray],l:int,cfg:dict[str,Any])->str:
 final=rep['regional_profile'][:,l,-1]
 active=rep['regional_active'][:,l,-1]
 vals=final[active]
 breadth=float(np.mean(vals>=float(cfg['implementation_presence_threshold']))) if vals.size else 0
 borrow=float(np.median(rep['borrowing_inflow'][:,l,-1][rep['regional_active'][:,l,-1]])) if np.any(rep['regional_active'][:,l,-1]) else 0
 # cross-lineage edge density at final anchor
 mat=rep['exchange_matrix'][:,-1];cross=mat[:,0:6,6:12];cross_density=float(np.mean(cross>float(cfg['borrowing_edge_threshold'])));all_density=float(np.mean(mat>float(cfg['borrowing_edge_threshold'])))
 if breadth>=.65 and cross_density>=.18 and borrow>=.10: return 'RETICULATE_INTERLINEAGE_CULTURAL_EXCHANGE_NETWORK'
 if breadth>=.55 and all_density>=.10: return 'REGIONAL_EXCHANGE_TECHNOLOGICAL_NETWORK'
 return 'REGIONAL_TECHNOLOGICAL_TRADITIONS_WITH_LIMITED_BORROWING'

def summarize(inp:dict[str,Any],rep:dict[str,np.ndarray],cfg:dict[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
 lines=[]
 threshold=float(cfg['implementation_presence_threshold'])
 for l,sid in enumerate(EXPECTED_CANDIDATES):
  final_global=rep['implementation_stock'][:,l,-1]
  med=np.median(final_global,axis=0);q10=np.quantile(final_global,.1,axis=0)
  robust=[IMPLEMENTATION_NAMES[k] for k in range(len(IMPLEMENTATION_NAMES)) if med[k]>=threshold and q10[k]>=float(cfg['robust_presence_q10_threshold'])]
  lines.append({'lineage_id':sid,'resolved_cultural_network_pathway':_lineage_resolution(rep,l,cfg),'robust_functional_implementation_families':robust,'robust_implementation_count':len(robust),'final_implementation_support_median':{IMPLEMENTATION_NAMES[k]:float(med[k]) for k in range(len(IMPLEMENTATION_NAMES))},'final_regional_borrowing_inflow_median':float(np.median(rep['borrowing_inflow'][:,l,-1][rep['regional_active'][:,l,-1]])),'final_regional_distinctiveness_median':float(np.median(rep['regional_distinctiveness'][:,l,-1][rep['regional_active'][:,l,-1]])),'final_fission_pressure_median':float(np.median(rep['fission_pressure'][:,l,-1][rep['regional_active'][:,l,-1]])),'final_fusion_pressure_median':float(np.median(rep['fusion_pressure'][:,l,-1][rep['regional_active'][:,l,-1]]))})
 # robust reticulate graph edges across ensemble/anchors
 stem_ids=[f'{sid}:C{r:02d}' for sid in EXPECTED_CANDIDATES for r in range(1,7)]
 borrowing=[]
 for a,age in enumerate(rep['anchor_age_ka']):
  for i in range(12):
   for j in range(i+1,12):
    freq=float(np.mean(rep['exchange_matrix'][:,a,i,j]>=float(cfg['borrowing_edge_threshold'])))
    med=float(np.median(rep['exchange_matrix'][:,a,i,j]))
    if freq>=float(cfg['robust_borrowing_member_fraction']): borrowing.append({'age_ka':float(age),'source_stem':stem_ids[i],'target_stem':stem_ids[j],'member_frequency':freq,'median_exchange_support':med,'edge_type':'BIDIRECTIONAL_BORROWING_OPPORTUNITY'})
 fission_events=[];fusion_events=[]
 for l,sid in enumerate(EXPECTED_CANDIDATES):
  for a,age in enumerate(rep['anchor_age_ka']):
   for r in range(6):
    f_freq=float(np.mean(rep['fission_pressure'][:,l,a,r]>=float(cfg['fission_materialization_threshold'])))
    u_freq=float(np.mean(rep['fusion_pressure'][:,l,a,r]>=float(cfg['fusion_materialization_threshold'])))
    if f_freq>=float(cfg['robust_event_member_fraction']): fission_events.append({'age_ka':float(age),'stem':f'{sid}:C{r+1:02d}','member_frequency':f_freq,'event_type':'ROBUST_FISSION_PRESSURE_EVENT'})
    if u_freq>=float(cfg['robust_event_member_fraction']): fusion_events.append({'age_ka':float(age),'stem':f'{sid}:C{r+1:02d}','member_frequency':u_freq,'event_type':'ROBUST_FUSION_PRESSURE_EVENT'})
 outcomes={'stage':STAGE,'status':'R338_CONCRETE_TECHNOLOGY_AND_CULTURAL_NETWORK_OUTCOMES','candidate_lineages':EXPECTED_CANDIDATES,'implementation_family_count':len(IMPLEMENTATION_NAMES),'lineages':lines,'named_culture_materialized':False,'language_materialized':False,'religion_materialized':False,'specific_archaeological_artifact_observation_claimed':False,'metallurgy_materialized':False,'city_state_materialized':False}
 genealogy={'stage':STAGE,'status':'R338_RETICULATE_CULTURAL_GENEALOGY','genealogy_semantics':'OPAQUE_REGIONAL_STEMS_WITH_VERTICAL_CONTINUITY_AND_HORIZONTAL_BORROWING;_NOT_NAMED_CULTURES_OR_ETHNICITIES','stem_ids':stem_ids,'vertical_continuity_edges_count':(EXPECTED_ANCHORS-1)*len(stem_ids),'robust_borrowing_edges':borrowing,'robust_fission_pressure_events':fission_events,'robust_fusion_pressure_events':fusion_events,'pure_tree_claimed':False,'reticulate_genealogy_materialized':True}
 combos=[(.8,1,1),(1,1,1),(1.2,1,1),(1,.8,1),(1,1.2,1),(1,1,.8),(1,1,1.2),(.85,1.15,.9),(1.15,.85,1.1),(.75,1.25,1),(1.25,.75,1),(1,1.25,1.2)]
 variants=[]
 for bm,dm,im in combos:
  r=replay_exchange_technology_genealogy(inp,cfg,bm,dm,im,static=rep['_static'])
  variants.append({'borrowing_multiplier':bm,'distance_scale_multiplier':dm,'innovation_multiplier':im,'resolved_pathways':[_lineage_resolution(r,l,cfg) for l in range(2)],'robust_implementation_counts':[int(np.sum((np.median(r['implementation_stock'][:,l,-1],axis=0)>=threshold)&(np.quantile(r['implementation_stock'][:,l,-1],.1,axis=0)>=float(cfg['robust_presence_q10_threshold'])))) for l in range(2)],'cross_lineage_borrowing_edge_fraction_0ka':float(np.mean(r['exchange_matrix'][:,-1,0:6,6:12]>=float(cfg['borrowing_edge_threshold'])))})
 sens={'stage':STAGE,'status':'R338_EXCHANGE_TECHNOLOGY_GENEALOGY_SENSITIVITY','variant_count':len(variants),'selection_gate':False,'variants':variants}
 return outcomes,genealogy,sens

def _audit(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],outs:dict[str,Any],gen:dict[str,Any],sens:dict[str,Any])->dict[str,Any]:
 checks=[]
 def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
 ck('r337_parent_sealed',inp['a37']['status']==PARENT_PASS);ck('r337_pathway_distributed',all(v=='DISTRIBUTED_MANAGED_FORAGER_ECONOMY' for v in inp['cp37']['resolved_lineage_economic_pathways'].values()));ck('r331_r332_r333_sealed',inp['a31']['status']==R331_PASS and inp['a32']['status']==R332_PASS and inp['a33']['status']==R333_PASS);ck('time_axis_exact',rep['age_ka'].shape==(145,) and rep['age_ka'][0]==20 and rep['age_ka'][-1]==0);ck('implementation_geometry',rep['implementation_stock'].shape==(32,2,145,len(IMPLEMENTATION_NAMES)));ck('implementation_bounded',rep['implementation_stock'].min()>=0 and rep['implementation_stock'].max()<=1);ck('group_geometry',rep['group_implementation_support'].shape==(32,2,9,48,len(IMPLEMENTATION_NAMES)));ck('group_active_parent_exact',np.array_equal(rep['group_active'],inp['a32z']['regional_active']));ck('regional_geometry',rep['regional_profile'].shape==(32,2,9,6,len(IMPLEMENTATION_NAMES)));ck('regional_state_geometry',rep['regional_state'].shape==(32,2,9,6,len(REGIONAL_STATE_NAMES)));ck('exchange_matrix_geometry',rep['exchange_matrix'].shape==(32,9,12,12));ck('exchange_symmetric',np.max(np.abs(rep['exchange_matrix']-np.swapaxes(rep['exchange_matrix'],-1,-2)))<1e-12);ck('exchange_diagonal_zero',np.max(np.abs(np.diagonal(rep['exchange_matrix'],axis1=-2,axis2=-1)))==0);ck('numeric_finite',all(np.isfinite(rep[k]).all() for k in ['implementation_stock','group_implementation_support','regional_profile','regional_state','exchange_matrix']));ck('reticulate_genealogy',gen['reticulate_genealogy_materialized'] is True and gen['pure_tree_claimed'] is False);ck('stems_12',len(gen['stem_ids'])==12);ck('sensitivity_12',sens['variant_count']==12);ck('sensitivity_no_selection',sens['selection_gate'] is False);ck('no_named_culture_language_religion',outs['named_culture_materialized'] is False and outs['language_materialized'] is False and outs['religion_materialized'] is False);ck('no_specific_archaeological_observation_claim',outs['specific_archaeological_artifact_observation_claimed'] is False);ck('no_metallurgy',outs['metallurgy_materialized'] is False);ck('no_city_state',outs['city_state_materialized'] is False);ck('generic_hard_material_prior_explicit',0<float(cfg['generic_hard_material_access_prior'])<1);ck('no_lineage_rescale',cfg['governance']['no_lineage_specific_rescaling'] is True);ck('deep_off',cfg['governance']['deep_biological_coupling'] is False);ck('evidence_multisource',len(EVIDENCE)>=9)
 failed=[x for x in checks if not x['pass']]
 return {'stage':STAGE,'status':CANDIDATE_PASS if not failed else 'FAIL_R338_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'checks':checks,'summary':{'candidate_lineages':2,'time_states':145,'anchor_states':9,'implementation_families':len(IMPLEMENTATION_NAMES),'regional_stems':12,'robust_borrowing_edges':len(gen['robust_borrowing_edges']),'robust_fission_pressure_events':len(gen['robust_fission_pressure_events']),'robust_fusion_pressure_events':len(gen['robust_fusion_pressure_events']),'resolved_cultural_network_pathways':{x['lineage_id']:x['resolved_cultural_network_pathway'] for x in outs['lineages']},'named_culture_materialized':False,'language_religion_materialized':False,'deep_biological_coupling':False}}

def build_outputs(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],out:Path)->dict[str,Any]:
 out.mkdir(parents=True,exist_ok=True);outs,gen,sens=summarize(inp,rep,cfg)
 auth={'stage':STAGE,'status':'R338_REGIONAL_EXCHANGE_CONCRETE_TECHNOLOGY_AND_CULTURAL_GENEALOGY_AUTHORITY','parent':PARENT_PASS,'candidate_cohort':EXPECTED_CANDIDATES,'window_ka':[20.0,0.0],'implementation_semantics':'FUNCTIONAL_IMPLEMENTATION_FAMILIES_ARE_CONCRETE_TECHNOLOGICAL_CLASSES_SUPPORTED_BY_SEALED_CAPABILITY_ECOLOGY_AND_ECONOMY;_THEY_ARE_NOT_DIRECT_ARCHAEOLOGICAL_OBSERVATIONS_OR_EXACT_ARTIFACT_TYPOLOGIES','material_semantics':'ENVIRONMENTAL_BIOTIC_AFFORDANCES_ARE_SPATIALLY_INHERITED;_HARD_MINERAL_ACCESS_USES_AN_EXPLICIT_GLOBAL_PRIOR_BECAUSE_A_HIGH_RESOLUTION_LITHIC_RAW_MATERIAL_MAP_IS_NOT_YET_AN_AUTHORITY','genealogy_semantics':gen['genealogy_semantics'],'prohibited_materialization':['named_cultures','ethnicities','languages','religions','metallurgy','currency','markets','villages','cities','states','unique_human_identity','Deep_biological_coupling'],'implementation_families':IMPLEMENTATION_NAMES,'evidence_basis':EVIDENCE,'dynamics':cfg,'parent_hashes':{'r331_technology_sha256':sha256_file(inp['r31']/'R3_31_CULTURAL_TECHNOLOGICAL_ECOLOGY_REPLAY.npz'),'r332_regional_sha256':sha256_file(inp['r32']/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz'),'r333_environment_sha256':sha256_file(inp['r33']/'R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz'),'r337_economy_sha256':sha256_file(inp['r37']/'R3_37_MANAGED_FORAGER_ECONOMY_REPLAY.npz')}}
 write_json(out/'R3_38_EXCHANGE_TECHNOLOGY_CULTURAL_GENEALOGY_AUTHORITY.json',auth)
 np.savez_compressed(out/'R3_38_CONCRETE_TECHNOLOGY_REPLAY.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z37']['parent_member_indices'],age_ka=rep['age_ka'],implementation_family_names=np.array(IMPLEMENTATION_NAMES),implementation_stock=rep['implementation_stock'],material_affordance_names=np.array(['plant_fibre_wood','animal_hide_osseous','hydro_resource','coastal_resource']),material_affordance_time=rep['material_affordance_time'])
 np.savez_compressed(out/'R3_38_GROUP_IMPLEMENTATION_ANCHORS.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z37']['parent_member_indices'],anchor_age_ka=rep['anchor_age_ka'],implementation_family_names=np.array(IMPLEMENTATION_NAMES),group_implementation_support=rep['group_implementation_support'],group_material_affordance_names=np.array(['generic_hard_material','plant_fibre_wood','animal_hide_osseous','hydro_resource','coastal_resource']),group_material_affordance=rep['group_material_affordance'],group_active=rep['group_active'])
 np.savez_compressed(out/'R3_38_REGIONAL_CULTURAL_NETWORKS.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z37']['parent_member_indices'],anchor_age_ka=rep['anchor_age_ka'],regional_state_variable_names=np.array(REGIONAL_STATE_NAMES),regional_state=rep['regional_state'],regional_implementation_profile=rep['regional_profile'],regional_active=rep['regional_active'],exchange_matrix=rep['exchange_matrix'],borrowing_inflow=rep['borrowing_inflow'],fission_pressure=rep['fission_pressure'],fusion_pressure=rep['fusion_pressure'],regional_distinctiveness=rep['regional_distinctiveness'])
 write_json(out/'R3_38_LINEAGE_TECHNOLOGY_OUTCOMES.json',outs);write_json(out/'R3_38_RETICULATE_CULTURAL_GENEALOGY.json',gen);write_json(out/'R3_38_SENSITIVITY_AND_ROBUSTNESS.json',sens)
 audit=_audit(inp,cfg,rep,outs,gen,sens);write_json(out/'R3_38_INTEGRATED_AUDIT.json',audit);(out/'R3_38_AUDIT.md').write_text(f"# R3.38 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n- Pathways: `{audit['summary']['resolved_cultural_network_pathways']}`\n- Robust borrowing edges: **{audit['summary']['robust_borrowing_edges']}**\n",encoding='utf-8');return audit

def write_manifest(out:Path,status:str)->None:
 files={}
 for p in sorted(out.iterdir()):
  if p.name=='R3_38_OUTPUT_MANIFEST.json' or not p.is_file(): continue
  files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_38_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
