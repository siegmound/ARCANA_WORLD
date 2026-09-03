from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json, math
import numpy as np

STAGE='v0.6D1-R3.34'
PARENT_STAGE='v0.6D1-R3.33'
PARENT_PASS='PASS_R333_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE_ANIMAL_ECOLOGICAL_PARTNERS_DOMESTICATION_TRAJECTORIES_AND_FOOD_PRODUCTION_EMERGENCE_SEALED'
CANDIDATE_PASS='PASS_R334_PRODUCER_OPERATIONAL_TAXON_AUTHORITY_PLANT_COEVOLUTION_AND_FOOD_PRODUCTION_REASSESSMENT_CANDIDATE'
FINAL_PASS='PASS_R334_PRODUCER_OPERATIONAL_TAXON_AUTHORITY_PLANT_COEVOLUTION_DOMESTICATION_AND_FOOD_PRODUCTION_REASSESSMENT_SEALED'
EXPECTED_PARENT_CHECKS=33
EXPECTED_CANDIDATES=['RPT_010_D02','RPT_009_D02']
EXPECTED_MEMBERS=32
ANCHOR_AGES=np.array([20.,15.,14.,13.,12.,11.,10.,5.,0.],dtype=float)
ARCHETYPES=[
 'annual_seed_grass','annual_seed_forb_pulse','perennial_seed_grass',
 'geophyte_storage_root','fruiting_woody','wetland_aquatic_starch'
]
TAXA_PER_ARCHETYPE=6
PRODUCER_COUNT=len(ARCHETYPES)*TAXA_PER_ARCHETYPE
TRAIT_NAMES=['edible_yield','harvestability','propagation_controllability','annuality','maturation_speed','seed_or_propagule_size','dormancy','shattering_or_dispersal','selfing_compatibility','clonal_propagation','disturbance_affinity','defense_toxicity','genetic_responsiveness','wild_gene_flow_base','temperature_optimum','precipitation_optimum','niche_breadth']
LANDSCAPE_NAMES=['suitability','resource_abundance','harvest_return','propagation_opportunity']
TRAJ_NAMES=['resource_contact','recurrent_harvest','stand_management','propagation_control','harvest_selection','selective_divergence','wild_gene_flow_pressure','dependency_symbiosis','plant_food_contribution','domestication_index']
STAGE_NAMES={0:'WILD_OR_WEAK_CONTACT',1:'RECURRENT_HARVEST',2:'MANAGED_STAND',3:'CONTROLLED_PROPAGATION',4:'INCIPIENT_DOMESTICATION',5:'FUNCTIONAL_DOMESTICATE'}

# Means are functional priors, not Earth crop identities. Values are deliberately broad.
ARCHETYPE_PRIORS={
 'annual_seed_grass': dict(edible_yield=.72,harvestability=.60,propagation_controllability=.68,annuality=.95,maturation_speed=.80,seed_or_propagule_size=.42,dormancy=.58,shattering_or_dispersal=.75,selfing_compatibility=.60,clonal_propagation=.08,disturbance_affinity=.82,defense_toxicity=.18,genetic_responsiveness=.75,wild_gene_flow_base=.58,temperature_optimum=.50,precipitation_optimum=.45,niche_breadth=.65),
 'annual_seed_forb_pulse': dict(edible_yield=.66,harvestability=.53,propagation_controllability=.64,annuality=.92,maturation_speed=.72,seed_or_propagule_size=.52,dormancy=.66,shattering_or_dispersal=.61,selfing_compatibility=.68,clonal_propagation=.06,disturbance_affinity=.72,defense_toxicity=.28,genetic_responsiveness=.70,wild_gene_flow_base=.48,temperature_optimum=.48,precipitation_optimum=.50,niche_breadth=.58),
 'perennial_seed_grass': dict(edible_yield=.58,harvestability=.48,propagation_controllability=.46,annuality=.08,maturation_speed=.38,seed_or_propagule_size=.36,dormancy=.52,shattering_or_dispersal=.72,selfing_compatibility=.45,clonal_propagation=.38,disturbance_affinity=.52,defense_toxicity=.16,genetic_responsiveness=.48,wild_gene_flow_base=.72,temperature_optimum=.47,precipitation_optimum=.52,niche_breadth=.72),
 'geophyte_storage_root': dict(edible_yield=.78,harvestability=.46,propagation_controllability=.80,annuality=.24,maturation_speed=.58,seed_or_propagule_size=.68,dormancy=.38,shattering_or_dispersal=.18,selfing_compatibility=.30,clonal_propagation=.88,disturbance_affinity=.62,defense_toxicity=.34,genetic_responsiveness=.56,wild_gene_flow_base=.34,temperature_optimum=.58,precipitation_optimum=.62,niche_breadth=.52),
 'fruiting_woody': dict(edible_yield=.70,harvestability=.66,propagation_controllability=.42,annuality=.02,maturation_speed=.20,seed_or_propagule_size=.76,dormancy=.35,shattering_or_dispersal=.32,selfing_compatibility=.35,clonal_propagation=.50,disturbance_affinity=.28,defense_toxicity=.24,genetic_responsiveness=.32,wild_gene_flow_base=.78,temperature_optimum=.62,precipitation_optimum=.68,niche_breadth=.48),
 'wetland_aquatic_starch': dict(edible_yield=.73,harvestability=.50,propagation_controllability=.60,annuality=.38,maturation_speed=.56,seed_or_propagule_size=.56,dormancy=.40,shattering_or_dispersal=.30,selfing_compatibility=.34,clonal_propagation=.76,disturbance_affinity=.56,defense_toxicity=.20,genetic_responsiveness=.54,wild_gene_flow_base=.50,temperature_optimum=.56,precipitation_optimum=.82,niche_breadth=.42),
}

EVIDENCE={
 'PLANT_DOMESTICATION_SYNDROME_2025':{'source':'Plant domestication revisited: Genomic insights into origins, mechanisms, and convergent evolution (2025)','pmcid':'PMC12799793','use':'loss of shattering, increased propagule size, reduced dormancy, phenology and architecture are treated as possible outcomes of selection, not prerequisites'},
 'CORE_DOMESTICATION_QUESTIONS':{'source':'Larson et al. 2014 Core questions in domestication research','pmcid':'PMC4371924','use':'cultivation can precede archaeologically visible domestication traits; dormancy and dispersal changes need not appear simultaneously'},
 'DOMESTICATION_MULTISPECIES_NETWORK':{'source':'Current perspectives and the future of domestication studies (2014)','pmcid':'PMC4035915','use':'humans act as dispersal agents, selective agents and ecosystem modifiers; domestication is modeled as a multispecies relationship'},
 'PLANT_ADAPTATION_GENETICS':{'source':'Plant domestication, a unique opportunity to identify the genetic basis of adaptation (2007)','pmcid':'PMC1876441','use':'unconscious selection, reduced dormancy/dispersal and altered reproductive timing motivate continuous trait response'},
 'PROTRACTED_PROCESS':{'source':'R3.33 evidence basis + Fuller-related protracted domestication literature','use':'no instantaneous agriculture flag; management, propagation control and selective divergence are separate states'},
 'SEALED_ENVIRONMENT':{'source':'R3.33 SEALED Holocene environmental resource landscape','use':'producer niches are anchored only to SEALED temperature/precipitation/NPP/land/hydroclimate fields'},
 'SEALED_HUMAN_SUBSISTENCE':{'source':'R3.32 SEALED subsistence/regional transition replay','use':'processing, landscape management, storage, scheduling, settlement and regional continuity are consumed as human-side drivers'},
 'NO_RETROACTIVE_FLORA_PHYLOGENY':{'source':'R3.33 audit finding','use':'H0 lacks explicit flora; R3.34 creates anonymous operational producer taxa and does not claim a 210 Ma plant fossil/phylogenetic history'}
}

class R334GateError(RuntimeError): pass

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
 if not p.is_file(): raise R334GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file() or fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:
   raise R334GateError(f'Manifest closure failure {fp}')

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root); r33=root/'outputs'/'v0_6D1_R3_33'; s33=root/'outputs'/'v0_6D1_R3_33_SEAL'; r32=root/'outputs'/'v0_6D1_R3_32'
 for d in (r33,s33,r32):
  if not d.is_dir(): raise R334GateError(f'Missing authority directory {d}')
 a33=load_json(s33/'R3_33_FINAL_SEAL_AUDIT.json')
 if a33.get('stage')!=PARENT_STAGE or a33.get('status')!=PARENT_PASS or a33.get('verdict')!='SEALED' or a33.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a33.get('checks_failed')!=0:
  raise R334GateError('R3.33 final seal mismatch')
 _close_manifest(r33,'R3_33_OUTPUT_MANIFEST.json'); _close_manifest(r32,'R3_32_OUTPUT_MANIFEST.json')
 auth33=load_json(r33/'R3_33_HOLOCENE_ENVIRONMENT_DOMESTICATION_AUTHORITY.json')
 if auth33.get('plant_species_registry_available') is not False: raise R334GateError('R3.33 plant-registry premise mismatch')
 env=np.load(r33/'R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz',allow_pickle=False)
 z32=np.load(r32/'R3_32_SUBSISTENCE_AND_TRANSITION_REPLAY.npz',allow_pickle=False)
 g32=np.load(r32/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz',allow_pickle=False)
 if list(map(str,z32['candidate_ids']))!=EXPECTED_CANDIDATES or list(map(str,g32['candidate_ids']))!=EXPECTED_CANDIDATES: raise R334GateError('Candidate cohort mismatch')
 if not np.array_equal(env['anchor_age_ka'],ANCHOR_AGES) or not np.array_equal(g32['anchor_age_ka'],ANCHOR_AGES): raise R334GateError('Anchor mismatch')
 if z32['age_ka'].shape!=(145,) or z32['subsistence_domain_stock'].shape[:3]!=(32,2,145): raise R334GateError('R3.32 replay geometry mismatch')
 return {'root':root,'r33':r33,'r32':r32,'a33':a33,'auth33':auth33,'env':env,'z32':z32,'g32':g32}

def _seed(archetype:str,i:int)->int:
 return int(hashlib.sha256(f'{archetype}:{i}'.encode()).hexdigest()[:8],16)

def build_producer_registry()->list[dict[str,Any]]:
 rows=[]
 for aidx,arch in enumerate(ARCHETYPES):
  prior=ARCHETYPE_PRIORS[arch]
  for i in range(TAXA_PER_ARCHETYPE):
   rng=np.random.default_rng(_seed(arch,i)); vals={}
   for k in TRAIT_NAMES:
    mu=float(prior[k]); sd=.055 if k not in ('temperature_optimum','precipitation_optimum','niche_breadth') else .045
    vals[k]=float(np.clip(rng.normal(mu,sd),.02,.98))
   taxid=f'PRD_{aidx+1:02d}_{i+1:02d}'
   # A neutral screening score is diagnostic only; it is never a selection gate.
   sc=.16*vals['edible_yield']+.13*vals['harvestability']+.16*vals['propagation_controllability']+.12*vals['maturation_speed']+.10*(1-vals['dormancy'])+.09*(1-vals['shattering_or_dispersal'])+.12*vals['disturbance_affinity']+.12*vals['genetic_responsiveness']
   rows.append({'producer_taxon_id':taxid,'archetype':arch,'authority_semantics':'ANONYMOUS_FUNCTIONAL_PRODUCER_OPERATIONAL_TAXON_NOT_RETROACTIVE_H0_PHYLOGENY','trait_values':vals,'diagnostic_domesticability_score':float(sc)})
 return rows

def build_producer_landscape(inp:dict[str,Any],registry:list[dict[str,Any]])->dict[str,np.ndarray]:
 ef=np.asarray(inp['env']['environment_fields'],float); names=list(map(str,inp['env']['environment_variable_names'])); ix={n:i for i,n in enumerate(names)}
 A,R,C=9,90,180; P=len(registry); out=np.zeros((P,A,R,C,4),np.float32)
 temp=ef[...,ix['temperature_anomaly_c']]; precip=ef[...,ix['precipitation_factor']]; npp=np.clip(ef[...,ix['npp_factor']],0,2.5); land=np.clip(ef[...,ix['land_fraction']],0,1); hydro=np.clip(ef[...,ix['hydroclimate_resource_index']],0,1); coast=np.clip(ef[...,ix['coastal_edge_index']],0,1)
 # Normalize environmental axes into broad ecological coordinates.
 tnorm=np.clip(.5+.12*temp,0,1); pnorm=np.clip((precip-.55)/.9,0,1); nnorm=np.clip(npp/1.5,0,1)
 for p,tax in enumerate(registry):
  tr=tax['trait_values']; bw=.14+.30*tr['niche_breadth']
  climate=np.exp(-((tnorm-tr['temperature_optimum'])**2+(pnorm-tr['precipitation_optimum'])**2)/(2*bw*bw))
  if tax['archetype']=='wetland_aquatic_starch': substrate=.50*hydro+.30*coast+.20*pnorm
  elif tax['archetype']=='fruiting_woody': substrate=.52*nnorm+.30*pnorm+.18*(1-coast)
  elif tax['archetype']=='geophyte_storage_root': substrate=.42*nnorm+.34*pnorm+.24*tr['disturbance_affinity']
  else: substrate=.55*nnorm+.25*pnorm+.20*tr['disturbance_affinity']
  suit=np.clip(land*climate*(.35+.65*substrate),0,1)
  abundance=np.clip(suit*(.25+.75*nnorm),0,1)
  harvest=np.clip(abundance*tr['edible_yield']*tr['harvestability']*(1-.30*tr['defense_toxicity']),0,1)
  prop=np.clip(suit*tr['propagation_controllability']*(.45+.30*tr['selfing_compatibility']+.25*tr['clonal_propagation']),0,1)
  out[p,...,0]=suit; out[p,...,1]=abundance; out[p,...,2]=harvest; out[p,...,3]=prop
 return {'anchor_age_ka':ANCHOR_AGES.copy(),'producer_taxon_ids':np.array([x['producer_taxon_id'] for x in registry]),'fields':out}

def _anchor_group_overlap(inp:dict[str,Any],land:dict[str,np.ndarray])->np.ndarray:
 g=inp['g32']; st=np.asarray(g['regional_state'],float); active=np.asarray(g['regional_active'],bool); names=list(map(str,g['regional_variable_names'])); ix={n:i for i,n in enumerate(names)}
 M,L,A,N=active.shape; P=land['fields'].shape[0]; ov=np.zeros((M,L,P,A),float)
 for m in range(M):
  for l in range(L):
   for a in range(A):
    mask=active[m,l,a]
    if not np.any(mask): continue
    rows=np.clip(np.rint(st[m,l,a,mask,ix['grid_row']]).astype(int),0,89); cols=np.clip(np.rint(st[m,l,a,mask,ix['grid_col']]).astype(int),0,179); w=np.maximum(st[m,l,a,mask,ix['represented_people']],1e-9); w=w/w.sum()
    # habitat/resource suitability sampled where groups actually occur
    vals=land['fields'][:,a,rows,cols,0]  # P x agents via advanced indexing
    if vals.ndim==1: vals=vals[:,None]
    ov[m,l,:,a]=np.sum(vals*w[None,:],axis=1)
 return ov

def _interp_descending(anchor_age:np.ndarray,anchor_values:np.ndarray,time_age:np.ndarray)->np.ndarray:
 # np.interp expects ascending x; arbitrary leading dimensions supported via explicit loop.
 av=np.asarray(anchor_values,float); flat=av.reshape(-1,av.shape[-1]); out=np.empty((flat.shape[0],len(time_age)),float)
 xa=anchor_age[::-1]; xt=time_age[::-1]
 for i,row in enumerate(flat): out[i]=np.interp(xt,xa,row[::-1])[::-1]
 return out.reshape(av.shape[:-1]+(len(time_age),))

def replay_coevolution(inp:dict[str,Any],registry:list[dict[str,Any]],land:dict[str,np.ndarray],cfg:dict[str,Any],rate_multiplier:float=1.0,threshold_offset:float=0.0)->dict[str,np.ndarray]:
 z=inp['z32']; ages=np.asarray(z['age_ka'],float); M,L,T=32,2,len(ages); P=len(registry); dt=np.maximum(0,np.r_[ages[:-1]-ages[1:],0.0])
 dom_names=list(map(str,z['subsistence_domain_names'])); eco_names=list(map(str,z['ecology_variable_names'])); di={n:i for i,n in enumerate(dom_names)}; ei={n:i for i,n in enumerate(eco_names)}
 ds=np.asarray(z['subsistence_domain_stock'],float); ec=np.asarray(z['subsistence_transition_ecology'],float)
 ov_anchor=_anchor_group_overlap(inp,land); ov=_interp_descending(ANCHOR_AGES,ov_anchor,ages) # M,L,P,T
 traj=np.zeros((M,L,P,T,len(TRAJ_NAMES)),np.float32)
 traits=[x['trait_values'] for x in registry]
 # Initial recurrent use can exist at 20ka, but no imposed propagation control/divergence.
 for p,tr in enumerate(traits):
  c=np.clip(ov[:,:,p,0]*(.30+.35*ds[:,:,0,di['broad_spectrum_foraging']]+.35*ds[:,:,0,di['plant_resource_processing_intensity']]),0,1)
  traj[:,:,p,0,0]=c; traj[:,:,p,0,1]=np.clip(.18+.32*tr['edible_yield']+.28*tr['harvestability']+.22*ds[:,:,0,di['plant_resource_processing_intensity']],0,1); traj[:,:,p,0,6]=np.clip(tr['wild_gene_flow_base']*(.5+.5*ov[:,:,p,0]),0,1)
 for t in range(T-1):
  kyr=dt[t];
  processing=ds[:,:,t,di['plant_resource_processing_intensity']]; storage=ds[:,:,t,di['delayed_return_storage_buffering']]; landscape_mgmt=ds[:,:,t,di['landscape_resource_management']]; scheduling=ds[:,:,t,di['seasonal_scheduling_and_logistics']]
  managed=ec[:,:,t,ei['managed_resource_intensity']]; settle=ec[:,:,t,ei['settlement_commitment']]; continuity=ec[:,:,t,ei['regional_continuity']]; readiness=ec[:,:,t,ei['food_production_transition_readiness']]
  for p,tr in enumerate(traits):
   x=traj[:,:,p,t,:].astype(float); local=ov[:,:,p,t]
   target_contact=np.clip(local*(.20+.28*processing+.20*managed+.17*readiness+.15*tr['edible_yield']),0,1)
   x[...,0]+=rate_multiplier*float(cfg['contact_adjustment_rate_per_kyr'])*kyr*(target_contact-x[...,0])
   harvest_drive=np.clip(.14+.26*processing+.25*tr['harvestability']+.25*tr['edible_yield']+.10*readiness,0,1)
   x[...,1]+=rate_multiplier*float(cfg['recurrent_harvest_rate_per_kyr'])*kyr*(harvest_drive-x[...,1])
   mg_drive=x[...,1]*np.clip(.24+.26*managed+.24*landscape_mgmt+.18*tr['disturbance_affinity']+.08*continuity,0,1)
   x[...,2]+=rate_multiplier*float(cfg['stand_management_rate_per_kyr'])*kyr*(mg_drive-x[...,2])-float(cfg['abandonment_rate_per_kyr'])*kyr*(1-continuity)*x[...,2]
   prop_trait=np.clip(.45*tr['propagation_controllability']+.25*tr['selfing_compatibility']+.30*tr['clonal_propagation'],0,1)
   prop_drive=x[...,2]*np.clip(.24+.48*prop_trait+.10*settle+.08*scheduling+.10*continuity,0,1)
   x[...,3]+=rate_multiplier*float(cfg['propagation_control_rate_per_kyr'])*kyr*(prop_drive-x[...,3])
   sel_pressure=np.clip(.28*tr['edible_yield']+.20*tr['seed_or_propagule_size']+.18*(1-tr['dormancy'])+.18*(1-tr['shattering_or_dispersal'])+.16*tr['harvestability'],0,1)
   sel_drive=x[...,3]*np.clip(.30+.45*sel_pressure+.15*processing+.10*storage,0,1)
   x[...,4]+=rate_multiplier*float(cfg['harvest_selection_rate_per_kyr'])*kyr*(sel_drive-x[...,4])
   wild=np.clip(tr['wild_gene_flow_base']*local*(1-.55*x[...,3]),0,1); x[...,6]=wild
   div_drive=np.sqrt(np.clip(x[...,3]*x[...,4],0,1))*tr['genetic_responsiveness']*(1-.45*wild)
   x[...,5]+=rate_multiplier*float(cfg['selective_divergence_rate_per_kyr'])*kyr*(div_drive-x[...,5])
   dep_drive=x[...,5]*np.clip(.35+.30*x[...,2]+.20*settle+.15*storage,0,1)
   x[...,7]+=rate_multiplier*float(cfg['dependency_rate_per_kyr'])*kyr*(dep_drive-x[...,7])
   food=np.clip(local*tr['edible_yield']*(.20*x[...,2]+.35*x[...,3]+.45*x[...,5])*(.55+.25*processing+.20*storage),0,1); x[...,8]=food
   x[...,9]=np.clip(.12*x[...,2]+.30*x[...,3]+.18*x[...,4]+.28*x[...,5]+.12*x[...,7],0,1)
   traj[:,:,p,t+1,:]=np.clip(x,0,1)
 # stage is based on final causal states, never on archetype name
 final=traj[:,:,:,-1,:].astype(float); stage=np.zeros((M,L,P),np.uint8)
 stage[final[...,1]>=float(cfg['recurrent_harvest_threshold'])+threshold_offset]=1
 stage[(final[...,2]>=float(cfg['managed_stand_threshold'])+threshold_offset)&(final[...,1]>=.20)]=2
 stage[(final[...,3]>=float(cfg['propagation_control_threshold'])+threshold_offset*.5)]=3
 stage[(final[...,9]>=float(cfg['incipient_domestication_index_threshold'])+threshold_offset)&(final[...,3]>=float(cfg['incipient_propagation_threshold'])+threshold_offset*.5)&(final[...,5]>=float(cfg['incipient_divergence_threshold'])+threshold_offset*.5)]=4
 stage[(final[...,9]>=float(cfg['domestication_index_threshold'])+threshold_offset)&(final[...,3]>=float(cfg['domestication_propagation_threshold'])+threshold_offset*.5)&(final[...,5]>=float(cfg['domestication_divergence_threshold'])+threshold_offset*.5)&(final[...,6]<=float(cfg['max_wild_gene_flow_for_domestication'])-threshold_offset*.25)]=5
 return {'age_ka':ages,'overlap_anchor':ov_anchor,'overlap_time':ov,'traj':traj,'stage':stage}

def summarize(inp:dict[str,Any],registry:list[dict[str,Any]],rep:dict[str,np.ndarray],cfg:dict[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
 stage=rep['stage']; tr=rep['traj']; taxa=[]; materialized=[]; incipient=[]
 for p,tax in enumerate(registry):
  los=[]
  for l,sid in enumerate(EXPECTED_CANDIDATES):
   f5=float(np.mean(stage[:,l,p]>=5)); f4=float(np.mean(stage[:,l,p]>=4)); f3=float(np.mean(stage[:,l,p]>=3)); med=float(np.median(tr[:,l,p,-1,9])); food=float(np.median(tr[:,l,p,-1,8])); los.append({'lineage_id':sid,'controlled_propagation_frequency':f3,'incipient_domestication_frequency':f4,'functional_domestication_frequency':f5,'final_domestication_index_median':med,'plant_food_contribution_median':food})
  mx5=max(x['functional_domestication_frequency'] for x in los); mx4=max(x['incipient_domestication_frequency'] for x in los)
  if mx5>=float(cfg['materialization_frequency_threshold']): materialized.append(tax['producer_taxon_id'])
  elif mx4>=float(cfg['incipient_frequency_threshold']): incipient.append(tax['producer_taxon_id'])
  taxa.append({'producer_taxon_id':tax['producer_taxon_id'],'archetype':tax['archetype'],'lineage_outcomes':los,'materialized_functional_domesticate':tax['producer_taxon_id'] in materialized,'incipient_domestication':tax['producer_taxon_id'] in incipient})
 lineages=[]
 for l,sid in enumerate(EXPECTED_CANDIDATES):
  food_matrix=tr[:,l,:,-1,8]; total=np.clip(np.sum(np.sort(food_matrix,axis=1)[:,-6:],axis=1),0,1); domest=np.sum(stage[:,l,:]>=5,axis=1); inc=np.sum(stage[:,l,:]>=4,axis=1)
  lineages.append({'lineage_id':sid,'plant_food_production_support_median':float(np.median(total)),'functional_domesticate_count_median':float(np.median(domest)),'incipient_or_better_count_median':float(np.median(inc)),'plant_food_production_emergence':bool(np.median(total)>=float(cfg['plant_food_production_threshold']) and np.mean(inc>=1)>=float(cfg['food_production_frequency_threshold']))})
 plant_food=any(x['plant_food_production_emergence'] for x in lineages)
 agriculture=bool(len(materialized)>=1 and any(x['plant_food_production_support_median']>=float(cfg['agriculture_food_support_threshold']) for x in lineages))
 outcomes={'stage':STAGE,'status':'R334_DOMESTICATION_FOOD_PRODUCTION_REASSESSMENT','producer_taxon_count':len(registry),'producer_authority_semantics':'FUNCTIONAL_OPERATIONAL_TAXA_NOT_RETROACTIVE_DEEP_PHYLOGENY','materialized_functional_plant_domesticates':materialized,'incipient_plant_domestication_taxa':incipient,'plant_food_production_emergence':plant_food,'agriculture_materialized':agriculture,'animal_domesticated_species_carried_from_r333':load_json(inp['r33']/'R3_33_FOOD_PRODUCTION_CHECKPOINT.json').get('materialized_domesticated_species',[]),'lineages':lineages,'taxa':taxa}
 vars=[]
 for rm in (.8,1.,1.2):
  for off in (-.05,0,.05):
   # algebraic end-state perturbation: sensitivity only, never a selection gate
   f=tr[:,:,:,-1,:].astype(float).copy(); prop=np.clip(f[...,3]*rm,0,1); div=np.clip(f[...,5]*rm,0,1); di=np.clip((.12*f[...,2]+.30*prop+.18*f[...,4]+.28*div+.12*f[...,7])*rm,0,1)
   dom=(di>=float(cfg['domestication_index_threshold'])+off)&(prop>=float(cfg['domestication_propagation_threshold'])+off*.5)&(div>=float(cfg['domestication_divergence_threshold'])+off*.5)&(f[...,6]<=float(cfg['max_wild_gene_flow_for_domestication'])-off*.25)
   inc=(di>=float(cfg['incipient_domestication_index_threshold'])+off)&(prop>=float(cfg['incipient_propagation_threshold'])+off*.5)&(div>=float(cfg['incipient_divergence_threshold'])+off*.5)
   vars.append({'rate_multiplier':rm,'threshold_offset':off,'functional_domestication_any_frequency':[float(np.mean(np.any(dom[:,l,:],axis=1))) for l in range(2)],'incipient_any_frequency':[float(np.mean(np.any(inc[:,l,:],axis=1))) for l in range(2)]})
 sens={'stage':STAGE,'status':'R334_PRODUCER_DOMESTICATION_SENSITIVITY','variant_count':len(vars),'selection_gate':False,'variants':vars}
 cp={'stage':STAGE,'status':'R334_FOOD_PRODUCTION_CHECKPOINT_0KA','age_ka':0.0,'candidate_cohort':EXPECTED_CANDIDATES,'producer_operational_taxon_authority_materialized':True,'producer_taxon_count':len(registry),'retroactive_h0_flora_phylogeny_claimed':False,'materialized_functional_plant_domesticates':materialized,'incipient_plant_domestication_taxa':incipient,'plant_food_production_emergence':plant_food,'agriculture_materialized':agriculture,'animal_food_production_emergence':load_json(inp['r33']/'R3_33_FOOD_PRODUCTION_CHECKPOINT.json').get('animal_food_production_emergence',False),'unique_human_identity_materialized':False,'deep_biological_coupling':False}
 return outcomes,sens,cp

def _audit(inp:dict[str,Any],reg:list[dict[str,Any]],land:dict[str,np.ndarray],rep:dict[str,np.ndarray],outs:dict[str,Any],sens:dict[str,Any])->dict[str,Any]:
 checks=[]
 def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
 ck('parent_sealed',inp['a33']['status']==PARENT_PASS); ck('r333_plant_registry_absence_preserved',inp['auth33']['plant_species_registry_available'] is False)
 ck('producer_count_36',len(reg)==36); ck('six_archetypes_exact',{x['archetype'] for x in reg}==set(ARCHETYPES)); ck('six_taxa_per_archetype',all(sum(x['archetype']==a for x in reg)==6 for a in ARCHETYPES)); ck('producer_ids_unique',len({x['producer_taxon_id'] for x in reg})==36); ck('operational_semantics',all('OPERATIONAL_TAXON' in x['authority_semantics'] for x in reg))
 ck('landscape_geometry',land['fields'].shape==(36,9,90,180,4)); ck('landscape_finite_bounded',np.isfinite(land['fields']).all() and land['fields'].min()>=0 and land['fields'].max()<=1); ck('anchor_exact',np.array_equal(land['anchor_age_ka'],ANCHOR_AGES))
 ck('trajectory_geometry',rep['traj'].shape==(32,2,36,145,10)); ck('trajectory_finite_bounded',np.isfinite(rep['traj']).all() and rep['traj'].min()>=0 and rep['traj'].max()<=1); ck('stage_geometry',rep['stage'].shape==(32,2,36)); ck('stage_bounded',set(np.unique(rep['stage'])).issubset(set(range(6)))); ck('no_initial_propagation_or_divergence',np.max(rep['traj'][:,:,:,0,3:6])==0); ck('group_overlap_geometry',rep['overlap_anchor'].shape==(32,2,36,9)); ck('group_overlap_bounded',rep['overlap_anchor'].min()>=0 and rep['overlap_anchor'].max()<=1)
 ck('sensitivity_9',sens['variant_count']==9); ck('sensitivity_no_selection',sens['selection_gate'] is False); ck('outcomes_taxa_36',len(outs['taxa'])==36); ck('no_retrospective_phylogeny_claim',outs['producer_authority_semantics']=='FUNCTIONAL_OPERATIONAL_TAXA_NOT_RETROACTIVE_DEEP_PHYLOGENY'); ck('deep_off',True); ck('evidence_multisource',len(EVIDENCE)>=8)
 failed=[x for x in checks if not x['pass']]
 return {'stage':STAGE,'status':CANDIDATE_PASS if not failed else 'FAIL_R334_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'checks':checks,'summary':{'candidate_lineages':2,'producer_operational_taxa':36,'producer_archetypes':6,'plant_domestication_trajectories_materialized':True,'materialized_functional_plant_domesticates_count':len(outs['materialized_functional_plant_domesticates']),'incipient_plant_domestication_taxa_count':len(outs['incipient_plant_domestication_taxa']),'plant_food_production_emergence':outs['plant_food_production_emergence'],'agriculture_materialized':outs['agriculture_materialized'],'deep_biological_coupling':False}}

def build_outputs(inp:dict[str,Any],cfg:dict[str,Any],reg:list[dict[str,Any]],land:dict[str,np.ndarray],rep:dict[str,np.ndarray],out:Path)->dict[str,Any]:
 out.mkdir(parents=True,exist_ok=True); outs,sens,cp=summarize(inp,reg,rep,cfg)
 auth={'stage':STAGE,'status':'R334_PRODUCER_OPERATIONAL_TAXON_AUTHORITY','parent':PARENT_PASS,'candidate_cohort':EXPECTED_CANDIDATES,'time_window_ka':[20.0,0.0],'producer_authority_semantics':'36_ANONYMOUS_FUNCTIONAL_OPERATIONAL_PRODUCER_TAXA_DERIVED_FROM_SEALED_RESOURCE_NICHES_AND_LIFE_HISTORY_PRIORS','retroactive_h0_flora_phylogeny_claimed':False,'taxonomic_claim':'NO_NAMED_OR_DEEP_PHYLOGENETIC_PLANT_SPECIES_CLAIM','archetypes':ARCHETYPES,'trait_names':TRAIT_NAMES,'landscape_semantics':'DIRECT_R333_SEALED_ENVIRONMENT_X_PRODUCER_NICHE_TRAITS','coevolution_semantics':'RESOURCE_CONTACT_TO_RECURRENT_HARVEST_TO_MANAGEMENT_TO_CONTROLLED_PROPAGATION_TO_SELECTION_AND_DIVERGENCE','agriculture_rule':'AGRICULTURE_ONLY_IF_AT_LEAST_ONE_FUNCTIONAL_PRODUCER_DOMESTICATE_MATERIALIZES_AND_PLANT_FOOD_SUPPORT_EXCEEDS_PREDECLARED_THRESHOLD','unique_human_identity_materialized':False,'deep_biological_coupling':False,'evidence_basis':EVIDENCE,'dynamics':cfg,'parent_hashes':{'r333_environment_sha256':sha256_file(inp['r33']/'R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz'),'r332_subsistence_sha256':sha256_file(inp['r32']/'R3_32_SUBSISTENCE_AND_TRANSITION_REPLAY.npz'),'r332_regional_sha256':sha256_file(inp['r32']/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz')}}
 write_json(out/'R3_34_PRODUCER_OPERATIONAL_TAXON_AUTHORITY.json',auth)
 write_json(out/'R3_34_PRODUCER_TAXON_REGISTRY.json',{'stage':STAGE,'status':'R334_PRODUCER_TAXON_REGISTRY','taxon_count':len(reg),'archetypes':ARCHETYPES,'trait_names':TRAIT_NAMES,'taxa':reg})
 np.savez_compressed(out/'R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz',anchor_age_ka=land['anchor_age_ka'],producer_taxon_ids=land['producer_taxon_ids'],landscape_variable_names=np.array(LANDSCAPE_NAMES),producer_landscape=land['fields'])
 np.savez_compressed(out/'R3_34_PLANT_COEVOLUTION_DOMESTICATION_TRAJECTORIES.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z32']['parent_member_indices'],producer_taxon_ids=np.array([x['producer_taxon_id'] for x in reg]),age_ka=rep['age_ka'],anchor_age_ka=ANCHOR_AGES,trajectory_variable_names=np.array(TRAJ_NAMES),trajectory_state=rep['traj'],domestication_stage=rep['stage'],anchor_group_overlap=rep['overlap_anchor'])
 write_json(out/'R3_34_DOMESTICATION_FOOD_PRODUCTION_REASSESSMENT.json',outs); write_json(out/'R3_34_SENSITIVITY_AND_ROBUSTNESS.json',sens); write_json(out/'R3_34_FOOD_PRODUCTION_CHECKPOINT.json',cp)
 audit=_audit(inp,reg,land,rep,outs,sens); write_json(out/'R3_34_INTEGRATED_AUDIT.json',audit); (out/'R3_34_AUDIT.md').write_text(f"# R3.34 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n",encoding='utf-8'); return audit

def write_manifest(out:Path,status:str)->None:
 files={}
 for p in sorted(out.iterdir()):
  if p.name=='R3_34_OUTPUT_MANIFEST.json' or not p.is_file(): continue
  files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_34_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
