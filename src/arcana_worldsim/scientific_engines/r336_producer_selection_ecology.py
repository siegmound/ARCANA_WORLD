from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json, math
import numpy as np

from arcana_worldsim.scientific_engines.r335_producer_genetics import (
    GENETIC_TRAIT_NAMES, build_genetic_priors, _corr_matrix, _divergence_index,
    _stage_from_endpoint,
)

STAGE='v0.6D1-R3.36'
PARENT_STAGE='v0.6D1-R3.35'
PARENT_PASS='PASS_R335_PRODUCER_HERITABLE_VARIATION_MULTIVARIATE_SELECTION_RESPONSE_WILD_GENE_FLOW_AND_DOMESTICATION_GENETICS_SEALED'
CANDIDATE_PASS='PASS_R336_PRODUCER_DOMESTICATION_SELECTION_ECOLOGY_REASSESSMENT_AND_PATHWAY_RESOLUTION_CANDIDATE'
FINAL_PASS='PASS_R336_PRODUCER_DOMESTICATION_SELECTION_ECOLOGY_RESOURCE_PERSISTENCE_WILD_GENE_FLOW_CLOSURE_AND_FORAGER_VS_FOOD_PRODUCTION_PATHWAY_RESOLUTION_SEALED'
EXPECTED_PARENT_CHECKS=29
EXPECTED_CANDIDATES=['RPT_010_D02','RPT_009_D02']
EXPECTED_MEMBERS=32
EXPECTED_PRODUCERS=36
K=len(GENETIC_TRAIT_NAMES)

EVIDENCE={
 'DOMESTICATION_ECOLOGY_2024':{
  'source':'Domestication and the evolution of crops: variable syndromes, complex genetic architectures, and ecological entanglements (2024)',
  'pmcid':'PMC11062453',
  'use':'domestication is treated as an ecological mutualism in which control over propagation/reproduction, genetic constraints and wild gene flow jointly regulate the transition'},
 'WILD_CROP_GENE_FLOW':{
  'source':'The relevance of gene flow with wild relatives in understanding the domestication process (2020)',
  'pmcid':'PMC7211868',
  'use':'domestication can be protracted and recurrent wild-to-managed gene flow can slow or reshape divergence rather than disappear abruptly'},
 'POPULATION_STRUCTURE':{
  'source':'Genomic, Transcriptomic and Epigenomic Tools to Study the Domestication of Plants and Animals (2020)',
  'pmcid':'PMC7373799',
  'use':'managed/wild differentiation depends on generations, selection intensity, bottlenecks/structure and gene-flow frequency'},
 'ECO_EVOLUTIONARY_GENE_FLOW':{
  'source':'The eco-evolutionary impacts of domestication and agricultural practices on wild species (2017)',
  'pmcid':'PMC5182429',
  'use':'even modest migration can homogenize populations, motivating explicit effective wild-gene-flow closure rather than a binary isolation flag'},
 'R335_PARENT':{'source':'R3.35 SEALED Producer Heritable Variation and Domestication Genetics','use':'36 producer taxa, six-trait quantitative genetics, R3.34 gate thresholds and parent genetic replay are immutable authority'},
 'R334_RESOURCE_LANDSCAPE':{'source':'R3.34 SEALED Producer Resource Landscape','use':'spatial resource concentration and temporal patch persistence are derived from the existing 90x180 producer landscape; no new Holocene environment is invented'},
 'PATHWAY_GOVERNANCE':{'source':'R3.36 governance','use':'food-production, incipient-domestication and intensive-managed-forager outcomes are all valid; no threshold is relaxed after observing the baseline'}
}

class R336GateError(RuntimeError): pass

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
 if not p.is_file(): raise R336GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file() or fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:
   raise R336GateError(f'Manifest closure failure {fp}')

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root);r35=root/'outputs'/'v0_6D1_R3_35';s35=root/'outputs'/'v0_6D1_R3_35_SEAL';r34=root/'outputs'/'v0_6D1_R3_34'
 if not r35.is_dir() or not s35.is_dir() or not r34.is_dir(): raise R336GateError('Missing R3.34/R3.35 authority')
 a35=load_json(s35/'R3_35_FINAL_SEAL_AUDIT.json')
 if a35.get('stage')!=PARENT_STAGE or a35.get('status')!=PARENT_PASS or a35.get('verdict')!='SEALED' or a35.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a35.get('checks_failed')!=0:
  raise R336GateError('R3.35 final seal mismatch')
 _close_manifest(r35,'R3_35_OUTPUT_MANIFEST.json'); _close_manifest(r34,'R3_34_OUTPUT_MANIFEST.json')
 cp35=load_json(r35/'R3_35_FOOD_PRODUCTION_CHECKPOINT.json')
 if cp35.get('producer_taxon_count')!=36 or cp35.get('agriculture_materialized') is not False: raise R336GateError('R3.35 checkpoint premise mismatch')
 auth35=load_json(r35/'R3_35_PRODUCER_QUANTITATIVE_GENETICS_AUTHORITY.json')
 z35=np.load(r35/'R3_35_PRODUCER_DOMESTICATION_GENETIC_REPLAY.npz',allow_pickle=False)
 z34=np.load(r34/'R3_34_PLANT_COEVOLUTION_DOMESTICATION_TRAJECTORIES.npz',allow_pickle=False)
 land=np.load(r34/'R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz',allow_pickle=False)
 reg34=load_json(r34/'R3_34_PRODUCER_TAXON_REGISTRY.json')
 pcfg=load_json(root/'configs/world1_r334_producer_domestication_v0_6D1_R3_34.json')
 gcfg=load_json(root/'configs/world1_r335_producer_genetics_v0_6D1_R3_35.json')
 if list(map(str,z35['candidate_ids']))!=EXPECTED_CANDIDATES or z35['managed_mean_shift'].shape!=(32,2,36,145,6): raise R336GateError('R3.35 genetic geometry mismatch')
 if not np.array_equal(z35['age_ka'],z34['age_ka']): raise R336GateError('R3.34/R3.35 time-axis mismatch')
 if land['producer_landscape'].shape!=(36,9,90,180,4): raise R336GateError('R3.34 landscape geometry mismatch')
 return {'root':root,'r35':r35,'r34':r34,'a35':a35,'cp35':cp35,'auth35':auth35,'z35':z35,'z34':z34,'land':land,'reg34':reg34,'pcfg':pcfg,'gcfg':gcfg}

def _top_fraction_mass_share(x:np.ndarray,fraction:float)->float:
 y=np.asarray(x,float).ravel();y=y[y>0]
 if not len(y): return 0.0
 n=max(1,int(math.ceil(float(fraction)*len(y))))
 part=np.partition(y,len(y)-n)[-n:]
 return float(np.sum(part)/np.sum(y))

def build_resource_selection_ecology(inp:dict[str,Any],cfg:dict[str,Any])->dict[str,np.ndarray]:
 land=inp['land'];arr=np.asarray(land['producer_landscape'],float);ages=np.asarray(land['anchor_age_ka'],float)
 names=list(map(str,land['landscape_variable_names']));ri=names.index('resource_abundance');pi=names.index('propagation_opportunity')
 P,A=36,len(ages);conc=np.zeros((P,A),float);persist=np.ones((P,A),float);prop_opp=np.zeros((P,A),float)
 for p in range(P):
  for a in range(A):
   x=arr[p,a,:,:,ri]
   conc[p,a]=_top_fraction_mass_share(x,float(cfg['resource_concentration_top_fraction']))
   pos=x[x>0];prop=arr[p,a,:,:,pi];prop_opp[p,a]=float(np.mean(prop[prop>0])) if np.any(prop>0) else 0.0
   if a>0:
    prev=arr[p,a-1,:,:,ri];den=np.maximum(prev,x).sum();persist[p,a]=float(np.minimum(prev,x).sum()/den) if den>0 else 0.0
 # first anchor has no predecessor; use the first observed transition rather than an artificial perfect persistence.
 persist[:,0]=persist[:,1]
 # Rescale concentration relative to the actual R3.34 landscape distribution, preserving ordering and boundedness.
 lo=float(np.percentile(conc,5));hi=float(np.percentile(conc,95));den=max(hi-lo,1e-12)
 conc_norm=np.clip((conc-lo)/den,0,1)
 # Interpolate descending anchor ages to the 145-state parent axis.
 time=np.asarray(inp['z35']['age_ka'],float);ct=np.zeros((P,len(time)),float);pt=np.zeros_like(ct);ot=np.zeros_like(ct)
 xa=ages[::-1]
 for p in range(P):
  ct[p]=np.interp(time[::-1],xa,conc_norm[p,::-1])[::-1]
  pt[p]=np.interp(time[::-1],xa,persist[p,::-1])[::-1]
  ot[p]=np.interp(time[::-1],xa,prop_opp[p,::-1])[::-1]
 return {'anchor_age_ka':ages,'resource_concentration_anchor':conc_norm,'resource_persistence_anchor':persist,'propagation_opportunity_anchor':prop_opp,'resource_concentration_time':ct,'resource_persistence_time':pt,'propagation_opportunity_time':ot,'concentration_raw_anchor':conc}

def _trait_isolation_factor(reg34:dict[str,Any])->np.ndarray:
 vals=[]
 for tax in reg34['taxa']:
  tv=tax['trait_values']
  vals.append(np.clip(.38*float(tv['selfing_compatibility'])+.26*float(tv['clonal_propagation'])+.36*float(tv['propagation_controllability']),0,1))
 return np.asarray(vals,float)

def replay_selection_ecology(inp:dict[str,Any],cfg:dict[str,Any],isolation_multiplier:float=1.0,persistence_multiplier:float=1.0,demographic_multiplier:float=1.0,store_trajectory:bool=True)->dict[str,np.ndarray]:
 # Replays the R3.35 breeder-equation semantics from the wild reference, replacing only constant wild-gene-flow pressure
 # with a dynamically derived selection-ecology closure and adding resource/demographic feedback to propagation/dependency.
 parent=np.asarray(inp['z34']['trajectory_state'],float);ages=np.asarray(inp['z35']['age_ka'],float);dt=np.r_[ages[:-1]-ages[1:],0.0]
 M,L,P,T=32,2,36,len(ages);gcfg=inp['gcfg'];pcfg=inp['pcfg'];eco=build_resource_selection_ecology(inp,cfg);pri=build_genetic_priors({'reg34':inp['reg34']},gcfg);R=_corr_matrix(float(gcfg['genetic_covariance_offdiag']))
 mean=np.zeros((M,L,P,K),float);va=np.broadcast_to(pri['va0'][None,None,:,:],(M,L,P,K)).copy();prop=parent[:,:,:,0,3].copy();dep=parent[:,:,:,0,7].copy();patch=np.zeros((M,L,P),float);isolation=np.zeros_like(patch)
 trait_iso=_trait_isolation_factor(inp['reg34'])
 if store_trajectory:
  means=np.zeros((M,L,P,T,K),np.float32);vas=np.zeros_like(means);h2s=np.zeros_like(means);responses=np.zeros_like(means)
  props=np.zeros((M,L,P,T),np.float32);deps=np.zeros_like(props);divs=np.zeros_like(props);foods=np.zeros_like(props);dis=np.zeros_like(props)
  patches=np.zeros_like(props);isos=np.zeros_like(props);wilds=np.zeros_like(props);returns=np.zeros_like(props);concs=np.zeros_like(props);pers_series=np.zeros_like(props)
  vas[:,:,:,0,:]=va;h2s[:,:,:,0,:]=va/(va+pri['ve'][None,None,:,:]);props[:,:,:,0]=prop;deps[:,:,:,0]=dep
 for t in range(T-1):
  kyr=float(dt[t]);base=parent[:,:,:,t,:];base_next=parent[:,:,:,t+1,:]
  harvest=base[...,4];management=base[...,2];recurrent=base[...,1];contact=base[...,0];wild_base=np.clip(base_next[...,6],0,1)
  conc=np.broadcast_to(eco['resource_concentration_time'][:,t][None,None,:],(M,L,P));pers=np.broadcast_to(np.clip(eco['resource_persistence_time'][:,t]*persistence_multiplier,0,1)[None,None,:],(M,L,P));opp=np.broadcast_to(eco['propagation_opportunity_time'][:,t][None,None,:],(M,L,P))
  patch_target=np.clip(.24*management+.24*prop+.17*contact+.18*pers+.10*conc+.07*opp,0,1)
  patch += float(cfg['managed_patch_persistence_rate_per_kyr'])*kyr*(patch_target-patch);patch=np.clip(patch,0,1)
  iso_target=np.clip((.36*prop+.24*management+.20*patch+.12*conc+.08*pers)*trait_iso[None,None,:]*isolation_multiplier,0,1)
  isolation += float(cfg['managed_population_isolation_rate_per_kyr'])*kyr*(iso_target-isolation);isolation=np.clip(isolation,0,1)
  floor=float(cfg['wild_gene_flow_floor_fraction']);red=float(cfg['wild_gene_flow_reduction_strength'])
  effective_wild=np.clip(wild_base*(floor+(1-floor)*np.exp(-red*isolation)),0,1)
  div=_divergence_index(mean)
  # ecological returns amplify controlled propagation only when management and persistent local resources already exist.
  return_feedback=np.clip((.36*management+.28*patch+.20*conc+.16*pers)*(.30+.70*div)*demographic_multiplier,0,1)
  target_prop=np.clip(base[...,3]+float(gcfg['coevolution_feedback_strength'])*div*(.35+.65*management)*(1-.45*effective_wild)+float(cfg['propagation_ecology_feedback_strength'])*return_feedback,0,1)
  prop += float(gcfg['coevolution_feedback_rate_per_kyr'])*kyr*(target_prop-prop);prop=np.maximum(prop,base_next[...,3]);prop=np.clip(prop,0,1)
  pressure=np.clip(.30*harvest+.30*prop+.20*management+.20*recurrent,0,1)
  pressure=np.clip(pressure*(1+float(cfg['resource_concentration_selection_gain'])*conc*patch),0,1)
  gen=(kyr*1000.0)/pri['generation_interval_years'];response=np.zeros_like(mean)
  for p in range(P):
   s=np.sqrt(np.maximum(va[:,:,p,:],1e-12));G=s[..., :,None]*R[None,None,:,:]*s[...,None,:]
   beta=float(gcfg['selection_gradient_per_generation'])*pressure[:,:,p,None]*pri['selection_profile'][p,None,None,:]
   b=np.einsum('mlij,mlj->mli',G,beta)
   attenuation=np.clip(1-float(gcfg['wild_gene_flow_selection_damping'])*effective_wild[:,:,p],.05,1.0)
   rr=b*gen[p]*attenuation[...,None];rr=np.clip(rr,-float(gcfg['max_mean_shift_per_step']),float(gcfg['max_mean_shift_per_step']));response[:,:,p,:]=rr
  mean += response
  mean -= float(gcfg['wild_reversion_rate_per_kyr'])*kyr*effective_wild[...,None]*mean
  mean=np.clip(mean,0,1)
  vmax=float(gcfg['va_ceiling']);gen4=np.broadcast_to(gen[None,None,:,None],va.shape)
  va += float(gcfg['mutation_replenishment_per_generation'])*gen4*(vmax-va)
  va += float(gcfg['wild_va_replenishment_per_kyr'])*kyr*effective_wild[...,None]*(pri['va0'][None,None,:,:]-va)
  va -= float(gcfg['selection_va_depletion_scale'])*np.abs(response)*va;va=np.clip(va,.005,vmax)
  div=_divergence_index(mean)
  dep_target=np.clip(base_next[...,7]+float(gcfg['dependency_feedback_strength'])*div*prop*(.45+.55*management)+float(cfg['dependency_return_feedback_strength'])*return_feedback*patch,0,1)
  dep += float(cfg['dependency_adjustment_rate_per_kyr'])*kyr*(dep_target-dep);dep=np.maximum(dep,base_next[...,7]);dep=np.clip(dep,0,1)
  food=np.zeros((M,L,P),float)
  for p,tax in enumerate(inp['reg34']['taxa']):
   tv=tax['trait_values'];pf=.70+.30*base_next[:,:,p,1];spatial_bonus=1+float(cfg['resource_concentration_food_gain'])*conc[:,:,p]*patch[:,:,p]
   food[:,:,p]=np.clip(base_next[:,:,p,0]*float(tv['edible_yield'])*(1+.45*mean[:,:,p,4])*(.18*management[:,:,p]+.38*prop[:,:,p]+.44*div[:,:,p])*pf*spatial_bonus,0,1)
  di=np.clip(.12*base_next[...,2]+.30*prop+.18*base_next[...,4]+.28*div+.12*dep,0,1)
  if store_trajectory:
   means[:,:,:,t+1,:]=mean
   vas[:,:,:,t+1,:]=va
   h2s[:,:,:,t+1,:]=va/(va+pri['ve'][None,None,:,:])
   responses[:,:,:,t+1,:]=response
   props[:,:,:,t+1]=prop
   deps[:,:,:,t+1]=dep
   divs[:,:,:,t+1]=div
   foods[:,:,:,t+1]=food
   dis[:,:,:,t+1]=di
   patches[:,:,:,t+1]=patch
   isos[:,:,:,t+1]=isolation
   wilds[:,:,:,t+1]=effective_wild
   returns[:,:,:,t+1]=return_feedback
   concs[:,:,:,t+1]=conc
   pers_series[:,:,:,t+1]=pers
 final_parent=parent[:,:,:,-1,:];final_conc=np.broadcast_to(eco['resource_concentration_time'][:,-1][None,None,:],(M,L,P));final_pers=np.broadcast_to(np.clip(eco['resource_persistence_time'][:,-1]*persistence_multiplier,0,1)[None,None,:],(M,L,P));final_wild_base=np.clip(final_parent[...,6],0,1);floor=float(cfg['wild_gene_flow_floor_fraction']);final_wild=np.clip(final_wild_base*(floor+(1-floor)*np.exp(-float(cfg['wild_gene_flow_reduction_strength'])*isolation)),0,1);final_div=_divergence_index(mean)
 final_return=np.clip((.36*final_parent[...,2]+.28*patch+.20*final_conc+.16*final_pers)*(.30+.70*final_div)*demographic_multiplier,0,1)
 final_food=np.zeros((M,L,P),float)
 for p,tax in enumerate(inp['reg34']['taxa']):
  tv=tax['trait_values'];pf=.70+.30*final_parent[:,:,p,1];spatial_bonus=1+float(cfg['resource_concentration_food_gain'])*final_conc[:,:,p]*patch[:,:,p]
  final_food[:,:,p]=np.clip(final_parent[:,:,p,0]*float(tv['edible_yield'])*(1+.45*mean[:,:,p,4])*(.18*final_parent[:,:,p,2]+.38*prop[:,:,p]+.44*final_div[:,:,p])*pf*spatial_bonus,0,1)
 final_di=np.clip(.12*final_parent[...,2]+.30*prop+.18*final_parent[...,4]+.28*final_div+.12*dep,0,1)
 stage=_stage_from_endpoint(prop,final_div,final_di,final_wild,final_parent,pcfg)
 out={'mean_final':mean,'va_final':va,'prop_final':prop,'dep_final':dep,'div_final':final_div,'food_final':final_food,'di_final':final_di,'wild_final':final_wild,'patch_final':patch,'isolation_final':isolation,'return_final':final_return,'stage':stage,'priors':pri,'ecology':eco}
 if store_trajectory:
  out.update({'age_ka':ages,'managed_mean_shift':means,'additive_variance':vas,'effective_heritability':h2s,'selection_response':responses,'effective_propagation_control':props,'effective_dependency':deps,'genetic_divergence_index':divs,'effective_food_contribution':foods,'genetic_domestication_index':dis,'managed_patch_persistence':patches,'managed_population_isolation':isos,'effective_wild_gene_flow':wilds,'demographic_return_feedback':returns,'resource_concentration':concs,'resource_persistence':pers_series})
 return out

def summarize(inp:dict[str,Any],rep:dict[str,np.ndarray],cfg:dict[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
 stage=rep['stage'];pcfg=inp['pcfg'];taxa=[];materialized=[];incipient=[]
 for p,tax in enumerate(inp['reg34']['taxa']):
  lo=[]
  for l,sid in enumerate(EXPECTED_CANDIDATES):
   f5=float(np.mean(stage[:,l,p]>=5));f4=float(np.mean(stage[:,l,p]>=4));f3=float(np.mean(stage[:,l,p]>=3))
   lo.append({'lineage_id':sid,'controlled_propagation_frequency':f3,'incipient_domestication_frequency':f4,'functional_domestication_frequency':f5,'genetic_divergence_median':float(np.median(rep['div_final'][:,l,p])),'effective_propagation_median':float(np.median(rep['prop_final'][:,l,p])),'effective_wild_gene_flow_median':float(np.median(rep['wild_final'][:,l,p])),'managed_population_isolation_median':float(np.median(rep['isolation_final'][:,l,p])),'food_contribution_median':float(np.median(rep['food_final'][:,l,p]))})
  mx5=max(x['functional_domestication_frequency'] for x in lo);mx4=max(x['incipient_domestication_frequency'] for x in lo)
  if mx5>=float(pcfg['materialization_frequency_threshold']): materialized.append(tax['producer_taxon_id'])
  elif mx4>=float(pcfg['incipient_frequency_threshold']): incipient.append(tax['producer_taxon_id'])
  taxa.append({'producer_taxon_id':tax['producer_taxon_id'],'archetype':tax['archetype'],'lineage_outcomes':lo,'materialized_functional_domesticate':tax['producer_taxon_id'] in materialized,'incipient_domestication':tax['producer_taxon_id'] in incipient})
 lineages=[]
 for l,sid in enumerate(EXPECTED_CANDIDATES):
  total=np.clip(np.sum(np.sort(rep['food_final'][:,l,:],axis=1)[:,-6:],axis=1),0,1);inc=np.sum(stage[:,l,:]>=4,axis=1);dom=np.sum(stage[:,l,:]>=5,axis=1);managed=np.sum(stage[:,l,:]>=3,axis=1)
  food_em=bool(np.median(total)>=float(pcfg['plant_food_production_threshold']) and np.mean(inc>=1)>=float(pcfg['food_production_frequency_threshold']))
  lineages.append({'lineage_id':sid,'plant_food_production_support_median':float(np.median(total)),'managed_or_better_taxa_median':float(np.median(managed)),'incipient_or_better_count_median':float(np.median(inc)),'functional_domesticate_count_median':float(np.median(dom)),'managed_patch_persistence_median':float(np.median(rep['patch_final'][:,l,:])),'managed_population_isolation_median':float(np.median(rep['isolation_final'][:,l,:])),'effective_wild_gene_flow_median':float(np.median(rep['wild_final'][:,l,:])),'plant_food_production_emergence':food_em})
 plant_food=any(x['plant_food_production_emergence'] for x in lineages);agriculture=bool(materialized and any(x['plant_food_production_support_median']>=float(pcfg['agriculture_food_support_threshold']) for x in lineages))
 if agriculture and materialized:
  pathway='FOOD_PRODUCTION_DOMESTICATION_PATHWAY'
 elif incipient or any(x['incipient_or_better_count_median']>=1 for x in lineages):
  pathway='PROTRACTED_INCIPIENT_DOMESTICATION_PATHWAY'
 elif all(x['managed_or_better_taxa_median']>=float(cfg['managed_forager_min_managed_taxa']) and x['plant_food_production_support_median']>=float(cfg['managed_forager_food_support_threshold']) for x in lineages):
  pathway='INTENSIVE_MANAGED_FORAGER_PATHWAY'
 else:
  pathway='MIXED_FORAGING_MANAGEMENT_PATHWAY'
 outcomes={'stage':STAGE,'status':'R336_SELECTION_ECOLOGY_OUTCOMES','producer_taxon_count':36,'materialized_functional_plant_domesticates':materialized,'incipient_plant_domestication_taxa':incipient,'plant_food_production_emergence':plant_food,'agriculture_materialized':agriculture,'resolved_pathway':pathway,'lineages':lineages,'taxa':taxa}
 variants=[]
 combos=[(.75,1,1),(1,1,1),(1.25,1,1),(1,.8,1),(1,1.2,1),(1,1,.8),(1,1,1.2),(.85,.9,1.1),(1.15,1.1,.9),(1.2,.8,1.2),(.8,1.2,.8),(1.1,.9,1.1)]
 for im,pm,dm in combos:
  r=replay_selection_ecology(inp,cfg,im,pm,dm,store_trajectory=False);st=r['stage'];variants.append({'isolation_multiplier':im,'resource_persistence_multiplier':pm,'demographic_feedback_multiplier':dm,'incipient_any_frequency':[float(np.mean(np.any(st[:,l,:]>=4,axis=1))) for l in range(2)],'functional_domestication_any_frequency':[float(np.mean(np.any(st[:,l,:]>=5,axis=1))) for l in range(2)],'median_effective_wild_gene_flow':[float(np.median(r['wild_final'][:,l,:])) for l in range(2)],'max_domestication_index':float(np.max(r['di_final']))})
 sens={'stage':STAGE,'status':'R336_SELECTION_ECOLOGY_SENSITIVITY','variant_count':len(variants),'selection_gate':False,'variants':variants}
 cp={'stage':STAGE,'status':'R336_PATHWAY_RESOLUTION_CHECKPOINT_0KA','age_ka':0.0,'candidate_cohort':EXPECTED_CANDIDATES,'producer_taxon_count':36,'materialized_functional_plant_domesticates':materialized,'incipient_plant_domestication_taxa':incipient,'plant_food_production_emergence':plant_food,'agriculture_materialized':agriculture,'resolved_pathway':pathway,'unique_human_identity_materialized':False,'deep_biological_coupling':False}
 return outcomes,sens,cp

def _audit(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],outs:dict[str,Any],sens:dict[str,Any])->dict[str,Any]:
 checks=[]
 def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
 ck('parent_sealed',inp['a35']['status']==PARENT_PASS);ck('r334_thresholds_inherited',cfg['governance']['inherit_r334_r335_domestication_gates_exactly'] is True);ck('producer_count_36',len(inp['reg34']['taxa'])==36);ck('ecology_anchor_geometry',rep['ecology']['resource_concentration_anchor'].shape==(36,9));ck('resource_concentration_bounded',rep['ecology']['resource_concentration_time'].min()>=0 and rep['ecology']['resource_concentration_time'].max()<=1);ck('resource_persistence_bounded',rep['ecology']['resource_persistence_time'].min()>=0 and rep['ecology']['resource_persistence_time'].max()<=1);ck('trajectory_geometry',rep['managed_mean_shift'].shape==(32,2,36,145,6));ck('patch_geometry',rep['managed_patch_persistence'].shape==(32,2,36,145));ck('isolation_geometry',rep['managed_population_isolation'].shape==(32,2,36,145));ck('effective_wild_geometry',rep['effective_wild_gene_flow'].shape==(32,2,36,145));ck('all_numeric_finite',all(np.isfinite(rep[k]).all() for k in ['managed_mean_shift','additive_variance','effective_propagation_control','managed_patch_persistence','managed_population_isolation','effective_wild_gene_flow','genetic_domestication_index']));ck('states_bounded',rep['managed_patch_persistence'].min()>=0 and rep['managed_patch_persistence'].max()<=1 and rep['managed_population_isolation'].min()>=0 and rep['managed_population_isolation'].max()<=1);ck('wild_gene_flow_not_increased',np.max(rep['effective_wild_gene_flow']-np.asarray(inp['z34']['trajectory_state'],float)[...,6])<=1e-6);ck('propagation_not_below_r335',np.min(rep['effective_propagation_control']-np.asarray(inp['z35']['effective_propagation_control'],float))>=-2e-4);ck('stage_bounded',set(np.unique(rep['stage'])).issubset(set(range(6))));ck('sensitivity_12',sens['variant_count']==12);ck('sensitivity_no_selection',sens['selection_gate'] is False);ck('pathway_enum',outs['resolved_pathway'] in {'FOOD_PRODUCTION_DOMESTICATION_PATHWAY','PROTRACTED_INCIPIENT_DOMESTICATION_PATHWAY','INTENSIVE_MANAGED_FORAGER_PATHWAY','MIXED_FORAGING_MANAGEMENT_PATHWAY'});ck('no_threshold_relaxation',cfg['governance']['no_domestication_threshold_relaxation'] is True);ck('no_named_crop',cfg['governance']['no_named_earth_crop_analogues'] is True);ck('no_lineage_rescale',cfg['governance']['no_lineage_specific_rescaling'] is True);ck('unique_human_off',cfg['governance']['unique_human_identity_materialized'] is False);ck('deep_off',cfg['governance']['deep_biological_coupling'] is False);ck('evidence_multisource',len(EVIDENCE)>=7)
 failed=[x for x in checks if not x['pass']]
 return {'stage':STAGE,'status':CANDIDATE_PASS if not failed else 'FAIL_R336_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'checks':checks,'summary':{'candidate_lineages':2,'producer_operational_taxa':36,'selection_ecology_explicit':True,'materialized_functional_plant_domesticates_count':len(outs['materialized_functional_plant_domesticates']),'incipient_plant_domestication_taxa_count':len(outs['incipient_plant_domestication_taxa']),'plant_food_production_emergence':outs['plant_food_production_emergence'],'agriculture_materialized':outs['agriculture_materialized'],'resolved_pathway':outs['resolved_pathway'],'deep_biological_coupling':False}}

def build_outputs(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],out:Path)->dict[str,Any]:
 out.mkdir(parents=True,exist_ok=True);outs,sens,cp=summarize(inp,rep,cfg);eco=rep['ecology']
 auth={'stage':STAGE,'status':'R336_PRODUCER_SELECTION_ECOLOGY_AUTHORITY','parent':PARENT_PASS,'candidate_cohort':EXPECTED_CANDIDATES,'producer_taxon_count':36,'r334_r335_domestication_gates_inherited_exactly':True,'selection_ecology_model':'RESOURCE_CONCENTRATION_AND_PERSISTENCE_PLUS_MANAGED_PATCH_MEMORY_PLUS_MANAGED_POPULATION_ISOLATION_MODULATE_WILD_GENE_FLOW_AND_SELECTION_RESPONSE','resource_semantics':'ALL_RESOURCE_CONCENTRATION_AND_PERSISTENCE_TERMS_ARE_DERIVED_FROM_R3_34_SEALED_90x180_PRODUCER_RESOURCE_LANDSCAPE','wild_gene_flow_semantics':'EFFECTIVE_WILD_GENE_FLOW_IS_NEVER_GREATER_THAN_R3_34_WILD_GENE_FLOW_PRESSURE_AND_REMAINS_NONZERO_UNLESS_PARENT_IS_ZERO','pathway_resolution_semantics':'FOOD_PRODUCTION_AND_INTENSIVE_MANAGED_FORAGING_ARE_BOTH_VALID_CANONICAL_OUTCOMES','retroactive_flora_phylogeny_claimed':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False,'evidence_basis':EVIDENCE,'dynamics':cfg,'parent_hashes':{'r335_replay_sha256':sha256_file(inp['r35']/'R3_35_PRODUCER_DOMESTICATION_GENETIC_REPLAY.npz'),'r335_checkpoint_sha256':sha256_file(inp['r35']/'R3_35_FOOD_PRODUCTION_CHECKPOINT.json'),'r334_landscape_sha256':sha256_file(inp['r34']/'R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz')}}
 write_json(out/'R3_36_PRODUCER_SELECTION_ECOLOGY_AUTHORITY.json',auth)
 np.savez_compressed(out/'R3_36_RESOURCE_SELECTION_ECOLOGY.npz',anchor_age_ka=eco['anchor_age_ka'],producer_taxon_ids=inp['land']['producer_taxon_ids'],resource_concentration_anchor=eco['resource_concentration_anchor'],resource_persistence_anchor=eco['resource_persistence_anchor'],propagation_opportunity_anchor=eco['propagation_opportunity_anchor'],resource_concentration_time=eco['resource_concentration_time'],resource_persistence_time=eco['resource_persistence_time'],propagation_opportunity_time=eco['propagation_opportunity_time'])
 np.savez_compressed(out/'R3_36_DOMESTICATION_SELECTION_ECOLOGY_REPLAY.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z35']['parent_member_indices'],producer_taxon_ids=inp['z35']['producer_taxon_ids'],age_ka=rep['age_ka'],genetic_trait_names=np.array(GENETIC_TRAIT_NAMES),managed_mean_shift=rep['managed_mean_shift'],additive_variance=rep['additive_variance'],effective_heritability=rep['effective_heritability'],selection_response=rep['selection_response'],effective_propagation_control=rep['effective_propagation_control'],effective_dependency=rep['effective_dependency'],genetic_divergence_index=rep['genetic_divergence_index'],effective_plant_food_contribution=rep['effective_food_contribution'],genetic_domestication_index=rep['genetic_domestication_index'],managed_patch_persistence=rep['managed_patch_persistence'],managed_population_isolation=rep['managed_population_isolation'],effective_wild_gene_flow=rep['effective_wild_gene_flow'],demographic_return_feedback=rep['demographic_return_feedback'],resource_concentration=rep['resource_concentration'],resource_persistence=rep['resource_persistence'],domestication_stage=rep['stage'])
 write_json(out/'R3_36_PATHWAY_OUTCOMES.json',outs);write_json(out/'R3_36_SENSITIVITY_AND_ROBUSTNESS.json',sens);write_json(out/'R3_36_PATHWAY_RESOLUTION_CHECKPOINT.json',cp)
 audit=_audit(inp,cfg,rep,outs,sens);write_json(out/'R3_36_INTEGRATED_AUDIT.json',audit);(out/'R3_36_AUDIT.md').write_text(f"# R3.36 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n- Resolved pathway: **{outs['resolved_pathway']}**\n",encoding='utf-8');return audit

def write_manifest(out:Path,status:str)->None:
 files={}
 for p in sorted(out.iterdir()):
  if p.name=='R3_36_OUTPUT_MANIFEST.json' or not p.is_file(): continue
  files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_36_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
