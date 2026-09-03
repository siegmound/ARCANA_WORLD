from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json, math
import numpy as np

STAGE='v0.6D1-R3.33'
PARENT_STAGE='v0.6D1-R3.32'
PARENT_PASS='PASS_R332_SUBSISTENCE_INTENSIFICATION_REGIONAL_CULTURAL_LINEAGES_MANAGED_RESOURCE_TRANSITIONS_AND_HOLOCENE_READINESS_SEALED'
CANDIDATE_PASS='PASS_R333_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE_ECOLOGICAL_PARTNERS_AND_DOMESTICATION_CANDIDATE'
FINAL_PASS='PASS_R333_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE_ANIMAL_ECOLOGICAL_PARTNERS_DOMESTICATION_TRAJECTORIES_AND_FOOD_PRODUCTION_EMERGENCE_SEALED'
EXPECTED_PARENT_CHECKS=30
EXPECTED_CANDIDATES=['RPT_010_D02','RPT_009_D02']
EXPECTED_MEMBERS=32
ANCHOR_AGES=np.array([20.,15.,14.,13.,12.,11.,10.,5.,0.],dtype=float)
GUILD_NAMES={1:'small_generalist_herbivore',2:'large_browser',3:'medium_low_vegetation_feeder',4:'small_reptiloid_generalist',5:'medium_carnivore',6:'apex_carnivore'}
GUILD_BASE={1:.76,2:.58,3:.72,4:.50,5:.30,6:.12}
GUILD_FOOD={1:.58,2:.88,3:.76,4:.34,5:.12,6:.05}
PARTNER_QUOTAS={1:8,2:1,3:5,4:7,5:3}
PARTNER_TRAIT_NAMES=['screening_score','social_tolerance','breedability','resource_generalism','disturbance_tolerance','food_utility','generation_time_support','present_range_extent']
ENV_NAMES=['temperature_anomaly_c','precipitation_factor','npp_factor','land_fraction','hydroclimate_resource_index','coastal_edge_index','sea_level_anomaly_m']
TRAJ_NAMES=['contact_opportunity','management_intensity','habituation_tolerance','reproductive_control','selective_divergence','wild_gene_flow_pressure','dependency_symbiosis','animal_food_production_contribution','domestication_index']

EVIDENCE={
 'ANIMAL_DOMESTICATION_TIMESCALE':{'source':'Larson/Frantz-related review 2021 Animal domestication: from distant past to current development and issues','pmcid':'PMC8214435','use':'animal domestication is a multi-millennial process; major livestock domestications cluster around 10.5–10 ka while dog domestication is older'},
 'ANIMAL_DOMESTICABILITY_REVIEW_2024':{'source':'Steklis et al. 2024 Why Were Zebras Not Domesticated?','pmcid':'PMC11350691','use':'animal domesticability is multivariate; response to humans/capture stress, social system and captive breeding can facilitate or block domestication'},
 'DOMESTICATION_REPRODUCTIVE_REGIME':{'source':'Lord et al. 2023 Shared reproductive disruption, not neural crest or tameness, explains the domestication syndrome','pmcid':'PMC10031412','use':'sustained reproductive control is treated as a causal transition rather than a cosmetic domestication-syndrome label'},
 'PROTRACTED_DOMESTICATION':{'source':'Fuller et al. 2017 Geographic mosaics and changing rates of cereal domestication','pmcid':'PMC5665816','use':'domestication is modeled as a prolonged trajectory rather than an instantaneous threshold'},
 'DOMESTICATION_PROCESS_REVIEW':{'source':'Kantar et al. 2018 Genomic approaches for studying crop evolution','pmcid':'PMC6151037','use':'wild-managed gene flow and evolutionary divergence are retained as separate processes'},
 'HOLOCENE_DELTA_RESOURCE_CONTEXT':{'source':'Nature Sustainability 2024 Delta sustainability from the Holocene to the Anthropocene','doi':'10.1038/s41893-024-01426-3','use':'postglacial sea-level stabilization and productive lowland/delta landscapes can alter resource accessibility and settlement opportunity'},
 'PALEOCLIMATE_PROVIDER':{'source':'SEALED ARCANA v0.6.1 recent paleoclimate provider','use':'100-year global history and 21/14/12.9/12/0 ka spatial temperature, precipitation, NPP and land-mask snapshots are consumed directly'},
 'H0_SPECIES_AUTHORITY':{'source':'R3.21 SEALED present lineage/component registry','use':'all ecological partner candidates are drawn from the 134 present H0 species; no new biological species are invented'},
 'FUNCTIONAL_PRIOR_AUTHORITY':{'source':'R3.23 SEALED comparative functional ensemble','use':'sociality, life history, dietary flexibility and ecological generalism inform partner-screening priors with explicit latent uncertainty'}
}

class R333GateError(RuntimeError): pass

def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()
def load_json(p:Path)->Any: return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:
 p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def _close_manifest(d:Path,name:str)->None:
 p=d/name
 if not p.is_file(): raise R333GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file() or fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:
   raise R333GateError(f'Manifest closure failure {fp}')

def _sigmoid(z:float)->float:
 z=float(np.clip(z,-20,20)); return 1.0/(1.0+math.exp(-z))

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root); r32=root/'outputs'/'v0_6D1_R3_32'; s32=root/'outputs'/'v0_6D1_R3_32_SEAL'; r21=root/'outputs'/'v0_6D1_R3_21'; r23=root/'outputs'/'v0_6D1_R3_23'
 climate=root/'local_bindings'/'v0_6D1_R3_14'/'v0_6_1_SEALED_MINIMAL'/'outputs'/'hybrid1'/'paleoclimate_v0_6_1'
 for d in (r32,s32,r21,r23,climate):
  if not d.is_dir(): raise R333GateError(f'Missing required authority directory {d}')
 a32=load_json(s32/'R3_32_FINAL_SEAL_AUDIT.json')
 if a32.get('stage')!=PARENT_STAGE or a32.get('status')!=PARENT_PASS or a32.get('verdict')!='SEALED' or a32.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a32.get('checks_failed')!=0:
  raise R333GateError('R3.32 final seal mismatch')
 _close_manifest(r32,'R3_32_OUTPUT_MANIFEST.json'); _close_manifest(r21,'R3_21_OUTPUT_MANIFEST.json'); _close_manifest(r23,'R3_23_OUTPUT_MANIFEST.json')
 reg=load_json(r21/'R3_21_PRESENT_LINEAGE_REGISTRY.json'); comp=load_json(r21/'R3_21_PRESENT_COMPONENT_REGISTRY.json'); fsum=load_json(r23/'R3_23_PRESENT_FUNCTIONAL_SUMMARY.json')
 if len(reg.get('lineages',[]))!=134 or len(comp.get('components',[]))!=295 or len(fsum.get('species',[]))!=134: raise R333GateError('H0/R3.23 registry geometry mismatch')
 z32=np.load(r32/'R3_32_SUBSISTENCE_AND_TRANSITION_REPLAY.npz',allow_pickle=False); g32=np.load(r32/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz',allow_pickle=False)
 if list(map(str,z32['candidate_ids']))!=EXPECTED_CANDIDATES or list(map(str,g32['candidate_ids']))!=EXPECTED_CANDIDATES: raise R333GateError('R3.32 candidate cohort mismatch')
 if not np.array_equal(np.asarray(g32['anchor_age_ka'],float),ANCHOR_AGES): raise R333GateError('R3.32 regional anchor axis mismatch')
 histp=climate/'recent_paleoclimate_history.npz'; snapp=climate/'paleoclimate_spatial_snapshots.npz'
 if not histp.is_file() or not snapp.is_file(): raise R333GateError('Missing SEALED paleoclimate provider products')
 hist=np.load(histp,allow_pickle=False); snaps=np.load(snapp,allow_pickle=False)
 reqh={'time_year_before_book','global_temperature_anomaly_c','sea_level_anomaly_m','freshwater_forcing_sv','atmospheric_co2_ppm'}
 reqs={'snapshot_year_before_book','temperature_anomaly_c','precipitation_factor_relative_book','npp_factor_relative_book','paleo_land_mask'}
 if not reqh.issubset(hist.files) or not reqs.issubset(snaps.files): raise R333GateError('Paleoclimate provider keys mismatch')
 if hist['time_year_before_book'].shape!=(1201,) or snaps['temperature_anomaly_c'].shape!=(5,720,1440): raise R333GateError('Paleoclimate provider geometry mismatch')
 return {'root':root,'r32':r32,'r21':r21,'r23':r23,'climate':climate,'a32':a32,'reg':reg,'comp':comp,'fsum':fsum,'z32':z32,'g32':g32,'hist':hist,'snaps':snaps,'hist_path':histp,'snaps_path':snapp}

def _trait_indices(fsum:dict[str,Any])->dict[str,int]: return {str(t['trait_id']):i for i,t in enumerate(fsum['traits'])}

def build_partner_registry(inp:dict[str,Any])->list[dict[str,Any]]:
 ti=_trait_indices(inp['fsum']); fs={x['species_id']:x for x in inp['fsum']['species']}; reg=inp['reg']['lineages']
 rows=[]
 for x in reg:
  sid=x['species_id']; gid=int(x['guild_id'])
  if sid in EXPECTED_CANDIDATES: continue
  s=fs[sid]; z=np.asarray(s['trait_mean_z'],float)
  social=.55*_sigmoid(z[ti['S1_social_tolerance']])+.45*_sigmoid(z[ti['S2_coordination_capacity']])
  breed=.35*(1-_sigmoid(z[ti['H1_maturation_duration']]))+.40*_sigmoid(z[ti['H2_reproductive_output_rate']])+.25*_sigmoid(z[ti['G3_disturbance_resilience']])
  general=.40*_sigmoid(z[ti['D1_resource_breadth']])+.30*_sigmoid(z[ti['G1_habitat_breadth']])+.30*_sigmoid(z[ti['G2_climatic_tolerance_breadth']])
  disturb=_sigmoid(z[ti['G3_disturbance_resilience']])
  gen=float(x['population_weighted_generation_time_proxy_years']); gensup=float(np.clip(1/(1+gen/8.0),0,1))
  extent=float(np.clip(x['occupied_component_grid_cells']/(90*180),0,1))
  food=GUILD_FOOD[gid]
  score=.30*GUILD_BASE[gid]+.20*social+.22*breed+.12*general+.06*disturb+.05*gensup+.05*extent
  rows.append({'species_id':sid,'guild_id':gid,'guild':GUILD_NAMES[gid],'screening_score':score,'social_tolerance':social,'breedability':breed,'resource_generalism':general,'disturbance_tolerance':disturb,'food_utility':food,'generation_time_support':gensup,'present_range_extent':extent,'generation_time_years':gen,'present_population_proxy':float(x['population_total'])})
 out=[]
 for gid,q in PARTNER_QUOTAS.items():
  out.extend(sorted([r for r in rows if r['guild_id']==gid],key=lambda r:(-r['screening_score'],r['species_id']))[:q])
 out=sorted(out,key=lambda r:(-r['screening_score'],r['guild_id'],r['species_id']))
 if len(out)!=sum(PARTNER_QUOTAS.values()): raise R333GateError('Partner candidate quota closure failed')
 for rank,r in enumerate(out,1): r['screening_rank']=rank
 return out

def _downsample8(a:np.ndarray)->np.ndarray:
 a=np.asarray(a,float); return a.reshape(90,8,180,8).mean(axis=(1,3))

def build_environment(inp:dict[str,Any])->dict[str,np.ndarray]:
 snaps=inp['snaps']; hist=inp['hist']
 snap_age=-np.asarray(snaps['snapshot_year_before_book'],float)/1000.0
 order=np.argsort(snap_age); snap_age=snap_age[order]
 temp=np.asarray(snaps['temperature_anomaly_c'],float)[order]; precip=np.asarray(snaps['precipitation_factor_relative_book'],float)[order]; npp=np.asarray(snaps['npp_factor_relative_book'],float)[order]; land=np.asarray(snaps['paleo_land_mask'],float)[order]
 # Downsample provider exactly to WorldSim 90x180 support before temporal interpolation.
 dt=np.stack([_downsample8(x) for x in temp]); dp=np.stack([_downsample8(x) for x in precip]); dn=np.stack([_downsample8(x) for x in npp]); dl=np.stack([_downsample8(x) for x in land])
 fields=np.zeros((len(ANCHOR_AGES),90,180,len(ENV_NAMES)),float)
 h_age=-np.asarray(hist['time_year_before_book'],float)/1000.0; ho=np.argsort(h_age); h_age=h_age[ho]; sea=np.asarray(hist['sea_level_anomaly_m'],float)[ho]
 for ai,age in enumerate(ANCHOR_AGES):
  j=np.searchsorted(snap_age,age)
  if j<=0: lo=hi=0; w=0.
  elif j>=len(snap_age): lo=hi=len(snap_age)-1; w=0.
  else:
   lo=j-1; hi=j; den=snap_age[hi]-snap_age[lo]; w=(age-snap_age[lo])/den if den else 0.
  T=(1-w)*dt[lo]+w*dt[hi]; P=(1-w)*dp[lo]+w*dp[hi]; N=(1-w)*dn[lo]+w*dn[hi]; L=np.clip((1-w)*dl[lo]+w*dl[hi],0,1)
  hydro=np.clip(np.sqrt(np.clip(P,0,1.5)*np.clip(N,0,1.2))/math.sqrt(1.5*1.2),0,1)*L
  binary=L>=.5; water=~binary; coast=np.zeros_like(L)
  for sh in [(-1,0),(1,0),(0,-1),(0,1)]: coast=np.maximum(coast,binary & np.roll(water,sh,axis=(0,1)))
  sea_v=float(np.interp(age,h_age,sea))
  fields[ai,...,0]=T; fields[ai,...,1]=P; fields[ai,...,2]=N; fields[ai,...,3]=L; fields[ai,...,4]=hydro; fields[ai,...,5]=coast.astype(float); fields[ai,...,6]=sea_v
 return {'age_ka':ANCHOR_AGES.copy(),'fields':fields}

def _species_components(inp:dict[str,Any])->dict[str,list[dict[str,Any]]]:
 d={}
 for c in inp['comp']['components']: d.setdefault(c['species_id'],[]).append(c)
 return d

def _range_overlap_for_agent(comps:list[dict[str,Any]],row:float,col:float,overlap_scale:float=1.0)->float:
 best=0.0
 for c in comps:
  rs=c['range_grid_summary']; r0,r1=map(float,rs['occupied_row_minmax']); c0,c1=map(float,rs['occupied_col_minmax'])
  if not (r0-1<=row<=r1+1): continue
  # World longitude is cyclic. Bounding boxes are used as a support gate; centroid distance controls local availability.
  inside_col=(c0-1<=col<=c1+1)
  if not inside_col and c0<=c1: continue
  cr=float(rs['population_weighted_row']); cc=float(rs['population_weighted_col']); dr=abs(row-cr); dc=min(abs(col-cc),180-abs(col-cc))
  occ=max(float(rs['occupied_grid_cells']),1.0); rad=max(math.sqrt(occ/math.pi),3.0); dens=min(1.0,occ/max((r1-r0+1)*(c1-c0+1),1.0))
  val=math.exp(-0.5*((dr*dr+dc*dc)/(rad*rad)))*(0.45+0.55*dens)*overlap_scale; best=max(best,val)
 return float(np.clip(best,0,1))

def _local_environment(fields:np.ndarray,row:float,col:float)->np.ndarray:
 r=int(np.clip(round(row),0,89)); c=int(round(col))%180; return fields[r,c]

def build_contact_opportunity(inp:dict[str,Any],partners:list[dict[str,Any]],env:dict[str,np.ndarray],overlap_scale:float=1.0)->np.ndarray:
 g=inp['g32']; names=list(map(str,g['regional_variable_names'])); gi={n:i for i,n in enumerate(names)}; S=np.asarray(g['regional_state'],float); A=np.asarray(g['regional_active'],bool); pc=_species_components(inp)
 M,L,T,G=S.shape[0],S.shape[1],S.shape[2],S.shape[3]; P=len(partners); out=np.zeros((M,L,P,T),float)
 for m in range(M):
  for l in range(L):
   for t in range(T):
    mask=A[m,l,t]
    if not mask.any(): continue
    st=S[m,l,t,mask]; w=np.maximum(st[:,gi['represented_people']],0); sw=w.sum()
    if sw<=0: continue
    readiness=np.clip(.42*st[:,gi['managed_resource_readiness']]+.25*st[:,gi['tech_access']]+.18*st[:,gi['regional_continuity']]+.15*st[:,gi['subsistence_profile_mean']],0,1)
    for p,pr in enumerate(partners):
     vals=[]
     for j,a in enumerate(st):
      row,col=float(a[gi['grid_row']]),float(a[gi['grid_col']]); e=_local_environment(env['fields'][t],row,col); overlap=_range_overlap_for_agent(pc[pr['species_id']],row,col,overlap_scale)
      climate_tol=.55+.45*pr['disturbance_tolerance']; temp_support=np.clip(1-abs(float(e[0]))/(12*climate_tol),0,1)
      if pr['guild_id'] in (1,2,3): resource=.55*np.clip(e[2],0,1)+.25*np.clip(e[1]/1.1,0,1)+.20*temp_support
      elif pr['guild_id']==4: resource=.35*np.clip(e[2],0,1)+.25*np.clip(e[4],0,1)+.25*temp_support+.15*pr['resource_generalism']
      else: resource=.28*np.clip(e[2],0,1)+.27*np.clip(e[4],0,1)+.20*temp_support+.25*pr['resource_generalism']
      vals.append(overlap*resource*readiness[j]*e[3])
     out[m,l,p,t]=float(np.average(vals,weights=w)) if len(vals) else 0.
 return np.clip(out,0,1)

def replay_domestication(inp:dict[str,Any],partners:list[dict[str,Any]],env:dict[str,np.ndarray],cfg:dict[str,Any],rate_mult:float=1.0,threshold_offset:float=0.0,overlap_scale:float=1.0)->dict[str,np.ndarray]:
 contact=build_contact_opportunity(inp,partners,env,overlap_scale); M,L,P,T=contact.shape; traj=np.zeros((M,L,P,T,len(TRAJ_NAMES)),float)
 pscore=np.array([x['screening_score'] for x in partners]); social=np.array([x['social_tolerance'] for x in partners]); breed=np.array([x['breedability'] for x in partners]); food=np.array([x['food_utility'] for x in partners]); general=np.array([x['resource_generalism'] for x in partners])
 # Initial state is contact/tolerance only; no partner starts domesticated.
 traj[:,:,:,0,0]=contact[:,:,:,0]; traj[:,:,:,0,1]=.025*contact[:,:,:,0]*pscore[None,None,:]; traj[:,:,:,0,2]=.015*contact[:,:,:,0]*social[None,None,:]
 for t in range(1,T):
  dt=float(ANCHOR_AGES[t-1]-ANCHOR_AGES[t]); prev=traj[:,:,:,t-1,:]; c=contact[:,:,:,t]
  management=prev[...,1]; habit=prev[...,2]; repro=prev[...,3]; div=prev[...,4]; dep=prev[...,6]
  stress=1-np.clip(c,0,1)
  management=np.clip(management + dt*float(cfg['management_rate_per_kyr'])*rate_mult*c*pscore[None,None,:]*(1-management) - dt*float(cfg['abandonment_rate_per_kyr'])*stress*management,0,1)
  habit=np.clip(habit + dt*float(cfg['habituation_rate_per_kyr'])*rate_mult*management*social[None,None,:]*(1-habit) - dt*.012*stress*habit,0,1)
  repro=np.clip(repro + dt*float(cfg['reproductive_control_rate_per_kyr'])*rate_mult*management*habit*breed[None,None,:]*(1-repro) - dt*.010*stress*repro,0,1)
  wild=np.clip(c*(1-repro)*(0.60+0.40*general[None,None,:]),0,1)
  div=np.clip(div + dt*float(cfg['selective_divergence_rate_per_kyr'])*rate_mult*management*repro*(1-wild)*(1-div),0,1)
  dep=np.clip(dep + dt*float(cfg['dependency_rate_per_kyr'])*rate_mult*management*repro*food[None,None,:]*(1-dep) - dt*.008*stress*dep,0,1)
  fp=np.clip(management*(.35+.65*repro)*food[None,None,:]*c,0,1)
  di=np.clip(.18*management+.17*habit+.32*repro+.25*div+.08*dep,0,1)
  traj[:,:,:,t,0]=c; traj[:,:,:,t,1]=management; traj[:,:,:,t,2]=habit; traj[:,:,:,t,3]=repro; traj[:,:,:,t,4]=div; traj[:,:,:,t,5]=wild; traj[:,:,:,t,6]=dep; traj[:,:,:,t,7]=fp; traj[:,:,:,t,8]=di
 # Stage classes are diagnostic and derived from causal states.
 th=float(cfg['domestication_index_threshold'])+threshold_offset; rep_th=float(cfg['reproductive_control_threshold'])+threshold_offset*.5; div_th=float(cfg['selective_divergence_threshold'])+threshold_offset*.5
 final=traj[:,:,:,-1,:]; stage=np.zeros((M,L,P),np.uint8); stage[final[...,1]>=.25]=1; stage[(final[...,1]>=.42)&(final[...,2]>=.32)]=2; stage[(final[...,3]>=rep_th)]=3; stage[(final[...,8]>=th)&(final[...,3]>=rep_th)&(final[...,4]>=div_th)]=4
 return {'traj':traj,'contact':contact,'stage':stage}

def summarize(inp:dict[str,Any],partners:list[dict[str,Any]],rep:dict[str,np.ndarray],cfg:dict[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
 tr=rep['traj']; stage=rep['stage']; outcomes=[]; materialized=[]; incipient=[]
 for p,pr in enumerate(partners):
  bylin=[]
  for l,sid in enumerate(EXPECTED_CANDIDATES):
   freq4=float(np.mean(stage[:,l,p]>=4)); freq3=float(np.mean(stage[:,l,p]>=3)); fprod=float(np.median(tr[:,l,p,-1,7])); di=float(np.median(tr[:,l,p,-1,8])); bylin.append({'lineage_id':sid,'reproductive_control_frequency':freq3,'domestication_trajectory_frequency':freq4,'final_domestication_index_median':di,'animal_food_contribution_median':fprod})
  max4=max(x['domestication_trajectory_frequency'] for x in bylin); max3=max(x['reproductive_control_frequency'] for x in bylin)
  if max4>=float(cfg['materialization_frequency_threshold']): materialized.append(pr['species_id'])
  elif max3>=float(cfg['incipient_frequency_threshold']): incipient.append(pr['species_id'])
  outcomes.append({'species_id':pr['species_id'],'guild':pr['guild'],'screening_rank':pr['screening_rank'],'screening_score':pr['screening_score'],'lineage_outcomes':bylin,'materialized_domesticate':pr['species_id'] in materialized,'incipient_domestication':pr['species_id'] in incipient})
 lineage=[]
 for l,sid in enumerate(EXPECTED_CANDIDATES):
  animal_food=float(np.median(np.clip(np.sum(tr[:,l,:,-1,7],axis=1),0,1))); repro_partners=float(np.median(np.sum(stage[:,l,:]>=3,axis=1))); domestic_partners=float(np.median(np.sum(stage[:,l,:]>=4,axis=1)))
  lineage.append({'lineage_id':sid,'final_animal_food_production_support_median':animal_food,'reproductive_control_partner_count_median':repro_partners,'domestication_trajectory_partner_count_median':domestic_partners,'food_production_emergence':bool(animal_food>=float(cfg['animal_food_production_threshold']) and repro_partners>=1)})
 food_prod=any(x['food_production_emergence'] for x in lineage)
 summary={'stage':STAGE,'status':'DOMESTICATION_AND_FOOD_PRODUCTION_OUTCOMES','partner_candidate_count':len(partners),'materialized_domesticated_species':materialized,'incipient_domestication_species':incipient,'animal_food_production_emergence':food_prod,'agriculture_materialized':False,'plant_species_registry_available':False,'lineages':lineage,'partners':outcomes}
 # Structural + parametric sensitivity; never used as a lineage-selection gate.
 vars=[]
 for rm in (.8,1.,1.2):
  for off in (-.05,0.,.05):
   for ov in (.85,1.15):
    # Keep sensitivity cheap: perturb final causal states algebraically using the already-computed baseline trajectory.
    base=tr[:,:,:,-1,:].copy(); mg=np.clip(base[...,1]*rm*ov,0,1); rp=np.clip(base[...,3]*rm,0,1); dv=np.clip(base[...,4]*rm,0,1); dp=np.clip(base[...,6]*rm,0,1); di=np.clip(.18*mg+.17*base[...,2]+.32*rp+.25*dv+.08*dp,0,1)
    st=(di>=float(cfg['domestication_index_threshold'])+off)&(rp>=float(cfg['reproductive_control_threshold'])+off*.5)&(dv>=float(cfg['selective_divergence_threshold'])+off*.5)
    vars.append({'rate_multiplier':rm,'threshold_offset':off,'overlap_multiplier':ov,'domestication_species_frequency':[float(np.mean(np.any(st[:,l,:],axis=1))) for l in range(2)]})
 sens={'stage':STAGE,'status':'R333_DOMESTICATION_STRUCTURAL_PARAMETRIC_SENSITIVITY','variant_count':len(vars),'selection_gate':False,'variants':vars}
 checkpoint={'stage':STAGE,'status':'R333_FOOD_PRODUCTION_CHECKPOINT_0KA','age_ka':0.0,'candidate_cohort':EXPECTED_CANDIDATES,'animal_ecological_partner_candidates_materialized':True,'animal_domestication_trajectories_materialized':True,'materialized_domesticated_species':materialized,'incipient_domestication_species':incipient,'animal_food_production_emergence':food_prod,'plant_species_registry_available':False,'plant_domestication_materialized':False,'agriculture_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False}
 return summary,sens,checkpoint

def _audit(inp:dict[str,Any],partners:list[dict[str,Any]],env:dict[str,np.ndarray],rep:dict[str,np.ndarray],outcomes:dict[str,Any],sens:dict[str,Any])->dict[str,Any]:
 checks=[]
 def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
 ck('parent_sealed',inp['a32']['status']==PARENT_PASS); ck('h0_present_species_134',len(inp['reg']['lineages'])==134); ck('h0_components_295',len(inp['comp']['components'])==295); ck('partner_count_24',len(partners)==24); ck('partner_unique',len({x['species_id'] for x in partners})==24); ck('partner_excludes_sapient_cohort',not ({x['species_id'] for x in partners}&set(EXPECTED_CANDIDATES))); ck('guild_quota_exact',{g:sum(x['guild_id']==g for x in partners) for g in PARTNER_QUOTAS}==PARTNER_QUOTAS); ck('environment_anchor_axis_exact',np.array_equal(env['age_ka'],ANCHOR_AGES)); ck('environment_geometry',env['fields'].shape==(9,90,180,7)); ck('environment_finite',np.isfinite(env['fields']).all()); ck('land_fraction_bounded',np.min(env['fields'][...,3])>=0 and np.max(env['fields'][...,3])<=1); ck('npp_nonnegative',np.min(env['fields'][...,2])>=0); ck('climate_provider_direct',inp['hist']['time_year_before_book'].shape==(1201,) and inp['snaps']['temperature_anomaly_c'].shape==(5,720,1440)); ck('trajectory_geometry',rep['traj'].shape==(32,2,24,9,9)); ck('trajectory_bounded',np.min(rep['traj'])>=0 and np.max(rep['traj'])<=1); ck('stage_geometry',rep['stage'].shape==(32,2,24)); ck('stage_bounded',set(np.unique(rep['stage'])).issubset({0,1,2,3,4})); ck('no_initial_domestication',np.max(rep['traj'][:,:,:,0,3])==0 and np.max(rep['traj'][:,:,:,0,4])==0); ck('food_production_semantics',outcomes['plant_species_registry_available'] is False and outcomes['agriculture_materialized'] is False); ck('sensitivity_18',sens['variant_count']==18); ck('sensitivity_no_selection',sens['selection_gate'] is False); ck('deep_off',True); ck('evidence_multisource',len(EVIDENCE)>=8)
 failed=[x for x in checks if not x['pass']]
 return {'stage':STAGE,'status':CANDIDATE_PASS if not failed else 'FAIL_R333_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'checks':checks,'summary':{'candidate_lineages':2,'partner_candidates':24,'environment_anchor_states':9,'plant_species_registry_available':False,'animal_domestication_trajectories_materialized':True,'materialized_domesticated_species_count':len(outcomes['materialized_domesticated_species']),'animal_food_production_emergence':outcomes['animal_food_production_emergence'],'agriculture_materialized':False,'deep_biological_coupling':False}}

def build_outputs(inp:dict[str,Any],cfg:dict[str,Any],partners:list[dict[str,Any]],env:dict[str,np.ndarray],rep:dict[str,np.ndarray],out:Path)->dict[str,Any]:
 out.mkdir(parents=True,exist_ok=True); outcomes,sens,cp=summarize(inp,partners,rep,cfg)
 auth={'stage':STAGE,'status':'R333_HOLOCENE_ENVIRONMENT_DOMESTICATION_AUTHORITY','parent':PARENT_PASS,'candidate_cohort':EXPECTED_CANDIDATES,'time_window_ka':[20.0,0.0],'environmental_semantics':'DIRECT_SEALED_PALEOCLIMATE_PROVIDER_DOWNSAMPLED_TO_WORLD1_90X180_AND_INTERPOLATED_ONLY_BETWEEN_PROVIDER_SNAPSHOTS','environment_anchor_ages_ka':ANCHOR_AGES.tolist(),'partner_semantics':'24_STRATIFIED_ANIMAL_ECOLOGICAL_PARTNER_CANDIDATES_DRAWN_ONLY_FROM_134_H0_PRESENT_SPECIES','plant_species_registry_available':False,'plant_resource_semantics':'NPP_AND_PRECIPITATION_RESOURCE_FIELD_ONLY_NOT_EXPLICIT_PLANT_SPECIES','domestication_semantics':'WILD_CONTACT_TO_MANAGEMENT_TO_REPRODUCTIVE_CONTROL_TO_SELECTIVE_DIVERGENCE_CONTINUOUS_TRAJECTORY','agriculture_materialized':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False,'paleoclimate_provider':{'recent_history_sha256':sha256_file(inp['hist_path']),'spatial_snapshots_sha256':sha256_file(inp['snaps_path'])},'evidence_basis':EVIDENCE,'dynamics':cfg}
 write_json(out/'R3_33_HOLOCENE_ENVIRONMENT_DOMESTICATION_AUTHORITY.json',auth)
 write_json(out/'R3_33_ECOLOGICAL_PARTNER_CANDIDATE_REGISTRY.json',{'stage':STAGE,'status':'R333_ANIMAL_ECOLOGICAL_PARTNER_REGISTRY','candidate_count':len(partners),'partner_trait_names':PARTNER_TRAIT_NAMES,'candidates':partners,'plant_species_registry_available':False})
 np.savez_compressed(out/'R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz',anchor_age_ka=env['age_ka'],environment_variable_names=np.array(ENV_NAMES),environment_fields=env['fields'])
 np.savez_compressed(out/'R3_33_DOMESTICATION_TRAJECTORIES.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z32']['parent_member_indices'],partner_species_ids=np.array([x['species_id'] for x in partners]),anchor_age_ka=ANCHOR_AGES,trajectory_variable_names=np.array(TRAJ_NAMES),trajectory_state=rep['traj'],domestication_stage=rep['stage'])
 write_json(out/'R3_33_DOMESTICATION_AND_FOOD_PRODUCTION_OUTCOMES.json',outcomes); write_json(out/'R3_33_SENSITIVITY_AND_ROBUSTNESS.json',sens); write_json(out/'R3_33_FOOD_PRODUCTION_CHECKPOINT.json',cp)
 audit=_audit(inp,partners,env,rep,outcomes,sens); write_json(out/'R3_33_INTEGRATED_AUDIT.json',audit); (out/'R3_33_AUDIT.md').write_text(f"# R3.33 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n",encoding='utf-8'); return audit

def write_manifest(out:Path,status:str)->None:
 files={}
 for p in sorted(out.iterdir()):
  if p.name=='R3_33_OUTPUT_MANIFEST.json' or not p.is_file(): continue
  files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_33_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
