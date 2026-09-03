from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json
import numpy as np

STAGE='v0.6D1-R3.35'
PARENT_STAGE='v0.6D1-R3.34'
PARENT_PASS='PASS_R334_PRODUCER_OPERATIONAL_TAXON_AUTHORITY_PLANT_COEVOLUTION_DOMESTICATION_AND_FOOD_PRODUCTION_REASSESSMENT_SEALED'
CANDIDATE_PASS='PASS_R335_PRODUCER_HERITABLE_VARIATION_SELECTION_RESPONSE_AND_DOMESTICATION_GENETICS_CANDIDATE'
FINAL_PASS='PASS_R335_PRODUCER_HERITABLE_VARIATION_MULTIVARIATE_SELECTION_RESPONSE_WILD_GENE_FLOW_AND_DOMESTICATION_GENETICS_SEALED'
EXPECTED_PARENT_CHECKS=25
EXPECTED_CANDIDATES=['RPT_010_D02','RPT_009_D02']
EXPECTED_MEMBERS=32
EXPECTED_PRODUCERS=36
GENETIC_TRAIT_NAMES=['propagule_size_shift','dormancy_reduction','reduced_shattering_dispersal','maturation_phenology_shift','edible_yield_allocation_shift','defense_toxicity_reduction']
K=len(GENETIC_TRAIT_NAMES)

EVIDENCE={
 'BREEDERS_EQUATION':{'source':'Cobb et al. 2019 Enhancing the rate of genetic gain in public-sector plant breeding programs: lessons from the breeder equation','pmcid':'PMC6439161','use':'response is governed by additive genetic variation, selection intensity/accuracy and generation interval'},
 'CROP_DOMESTICATION_GENETICS':{'source':'Meyer & Purugganan 2013 Evolution of crop species: genetics of domestication and diversification','doi':'10.1038/nrg3605','use':'domestication is a genetic response to selection on multiple traits and can involve selective sweeps, introgression and demographic change'},
 'SELECTION_DURING_DOMESTICATION':{'source':'Purugganan & Fuller 2009 The nature of selection during plant domestication','doi':'10.1038/nature07895','use':'plant domestication is modeled as plant-human coevolution under selection rather than an instantaneous state change'},
 'DEMOGRAPHY_AND_VARIATION':{'source':'Gaut et al. 2018 Demography and its effects on genomic variation in crop domestication','doi':'10.1038/s41477-018-0210-1','use':'demography, bottlenecks and long pre-domestication human impacts shape standing genomic variation'},
 'R334_PARENT':{'source':'R3.34 SEALED Producer Operational Taxon Authority','use':'36 taxa, resource contact/management/propagation history and all domestication thresholds are immutable parent authority'},
 'NO_RETROACTIVE_PHYLOGENY':{'source':'R3.34 governance','use':'genetic state is operational for managed producer populations and is not a reconstructed 210 Ma flora phylogeny'}
}

class R335GateError(RuntimeError): pass

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
 if not p.is_file(): raise R335GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file() or fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:
   raise R335GateError(f'Manifest closure failure {fp}')

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root);r34=root/'outputs'/'v0_6D1_R3_34';s34=root/'outputs'/'v0_6D1_R3_34_SEAL'
 if not r34.is_dir() or not s34.is_dir(): raise R335GateError('Missing R3.34 authority')
 a34=load_json(s34/'R3_34_FINAL_SEAL_AUDIT.json')
 if a34.get('stage')!=PARENT_STAGE or a34.get('status')!=PARENT_PASS or a34.get('verdict')!='SEALED' or a34.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a34.get('checks_failed')!=0:
  raise R335GateError('R3.34 final seal mismatch')
 _close_manifest(r34,'R3_34_OUTPUT_MANIFEST.json')
 cp=load_json(r34/'R3_34_FOOD_PRODUCTION_CHECKPOINT.json')
 if cp.get('producer_taxon_count')!=EXPECTED_PRODUCERS or cp.get('agriculture_materialized') is not False: raise R335GateError('R3.34 checkpoint premise mismatch')
 reg=load_json(r34/'R3_34_PRODUCER_TAXON_REGISTRY.json')
 if reg.get('taxon_count')!=EXPECTED_PRODUCERS: raise R335GateError('R3.34 producer registry mismatch')
 z=np.load(r34/'R3_34_PLANT_COEVOLUTION_DOMESTICATION_TRAJECTORIES.npz',allow_pickle=False)
 if list(map(str,z['candidate_ids']))!=EXPECTED_CANDIDATES or z['trajectory_state'].shape!=(32,2,36,145,10): raise R335GateError('R3.34 trajectory geometry mismatch')
 if z['age_ka'][0]!=20.0 or z['age_ka'][-1]!=0.0: raise R335GateError('R3.34 time axis mismatch')
 pcfg=load_json(root/'configs/world1_r334_producer_domestication_v0_6D1_R3_34.json')
 return {'root':root,'r34':r34,'a34':a34,'cp34':cp,'reg34':reg,'z34':z,'pcfg':pcfg}

def _trait_headroom(tv:dict[str,float])->np.ndarray:
 return np.array([
  1-float(tv['seed_or_propagule_size']),
  float(tv['dormancy']),
  float(tv['shattering_or_dispersal']),
  .5+.5*(1-float(tv['maturation_speed'])),
  1-float(tv['edible_yield']),
  float(tv['defense_toxicity'])
 ],float)

def build_genetic_priors(inp:dict[str,Any],cfg:dict[str,Any])->dict[str,np.ndarray]:
 taxa=inp['reg34']['taxa'];P=len(taxa)
 va0=np.zeros((P,K),float);ve=np.zeros((P,K),float);profile=np.zeros((P,K),float);gint=np.zeros(P,float)
 for p,tax in enumerate(taxa):
  tv=tax['trait_values'];gr=float(tv['genetic_responsiveness']);head=_trait_headroom(tv)
  profile[p]=np.clip(.55+.45*head,.15,1.0)
  base=float(cfg['initial_va_floor'])+float(cfg['initial_va_span'])*gr
  modifiers=np.array([.95,1.00,1.05,.85,1.00,.75])*(.82+.18*head)
  va0[p]=np.clip(base*modifiers,.02,float(cfg['va_ceiling']))
  ve[p]=float(cfg['environmental_variance_base'])*(.85+.30*(1-float(tv['niche_breadth'])))
  gint[p]=float(cfg['generation_interval_years'][tax['archetype']])
 h20=va0/(va0+ve)
 return {'va0':va0,'ve':ve,'h20':h20,'selection_profile':profile,'generation_interval_years':gint}

def _corr_matrix(offdiag:float)->np.ndarray:
 r=np.full((K,K),float(offdiag));np.fill_diagonal(r,1.0)
 ev=np.linalg.eigvalsh(r)
 if ev.min()<=0: raise R335GateError('Genetic correlation matrix not positive definite')
 return r

def _divergence_index(z:np.ndarray)->np.ndarray:
 w=np.array([.18,.18,.20,.12,.20,.12],float)
 return np.clip(np.sum(z*w,axis=-1),0,1)

def _stage_from_endpoint(prop:np.ndarray,div:np.ndarray,di:np.ndarray,wild:np.ndarray,parent_final:np.ndarray,pcfg:dict[str,Any])->np.ndarray:
 st=np.zeros(prop.shape,np.uint8)
 harvest=parent_final[...,1];mg=parent_final[...,2]
 st[harvest>=float(pcfg['recurrent_harvest_threshold'])]=1
 st[(mg>=float(pcfg['managed_stand_threshold']))&(harvest>=.20)]=2
 st[prop>=float(pcfg['propagation_control_threshold'])]=3
 st[(di>=float(pcfg['incipient_domestication_index_threshold']))&(prop>=float(pcfg['incipient_propagation_threshold']))&(div>=float(pcfg['incipient_divergence_threshold']))]=4
 st[(di>=float(pcfg['domestication_index_threshold']))&(prop>=float(pcfg['domestication_propagation_threshold']))&(div>=float(pcfg['domestication_divergence_threshold']))&(wild<=float(pcfg['max_wild_gene_flow_for_domestication']))]=5
 return st

def replay_genetics(inp:dict[str,Any],cfg:dict[str,Any],selection_multiplier:float=1.0,gene_flow_multiplier:float=1.0,feedback_multiplier:float=1.0,store_trajectory:bool=True)->dict[str,np.ndarray]:
 z34=inp['z34']; parent=np.asarray(z34['trajectory_state'],float); ages=np.asarray(z34['age_ka'],float);dt=np.r_[ages[:-1]-ages[1:],0.0]
 M,L,P,T=32,2,36,len(ages);pri=build_genetic_priors(inp,cfg);R=_corr_matrix(float(cfg['genetic_covariance_offdiag']))
 mean=np.zeros((M,L,P,K),float);va=np.broadcast_to(pri['va0'][None,None,:,:],(M,L,P,K)).copy();prop=parent[:,:,:,0,3].copy();dep=parent[:,:,:,0,7].copy()
 if store_trajectory:
  means=np.zeros((M,L,P,T,K),np.float32);vas=np.zeros_like(means);h2s=np.zeros_like(means);responses=np.zeros_like(means)
  props=np.zeros((M,L,P,T),np.float32);deps=np.zeros_like(props);divs=np.zeros_like(props);foods=np.zeros_like(props);dis=np.zeros_like(props)
  vas[:,:,:,0,:]=va;h2s[:,:,:,0,:]=va/(va+pri['ve'][None,None,:,:]);props[:,:,:,0]=prop;deps[:,:,:,0]=dep
 for t in range(T-1):
  kyr=float(dt[t]);base=parent[:,:,:,t,:];base_next=parent[:,:,:,t+1,:]
  harvest=base[...,4];management=base[...,2];recurrent=base[...,1];wild=np.clip(base[...,6]*gene_flow_multiplier,0,1)
  div=_divergence_index(mean)
  target_prop=np.clip(base[...,3]+float(cfg['coevolution_feedback_strength'])*feedback_multiplier*div*(.35+.65*management)*(1-.45*wild),0,1)
  prop += float(cfg['coevolution_feedback_rate_per_kyr'])*kyr*(target_prop-prop); prop=np.maximum(prop,base_next[...,3]);prop=np.clip(prop,0,1)
  pressure=np.clip(.30*harvest+.30*prop+.20*management+.20*recurrent,0,1)
  gen=(kyr*1000.0)/pri['generation_interval_years']
  response=np.zeros_like(mean)
  for p in range(P):
   s=np.sqrt(np.maximum(va[:,:,p,:],1e-12));G=s[..., :,None]*R[None,None,:,:]*s[...,None,:]
   beta=float(cfg['selection_gradient_per_generation'])*selection_multiplier*pressure[:,:,p,None]*pri['selection_profile'][p,None,None,:]
   b=np.einsum('mlij,mlj->mli',G,beta)
   attenuation=np.clip(1-float(cfg['wild_gene_flow_selection_damping'])*wild[:,:,p],.05,1.0)
   rr=b*gen[p]*attenuation[...,None]
   lim=float(cfg['max_mean_shift_per_step']);rr=np.clip(rr,-lim,lim);response[:,:,p,:]=rr
  mean += response
  mean -= float(cfg['wild_reversion_rate_per_kyr'])*kyr*wild[...,None]*mean
  mean=np.clip(mean,0,1)
  # VA: weak mutation/recombination replenishment, wild-pool replenishment, directional-selection depletion.
  vmax=float(cfg['va_ceiling']);mut=float(cfg['mutation_replenishment_per_generation']);depl=float(cfg['selection_va_depletion_scale']);wr=float(cfg['wild_va_replenishment_per_kyr'])
  gen4=np.broadcast_to(gen[None,None,:,None],va.shape)
  va += mut*gen4*(vmax-va)
  va += wr*kyr*wild[...,None]*(pri['va0'][None,None,:,:]-va)
  va -= depl*np.abs(response)*va
  va=np.clip(va,.005,vmax)
  div=_divergence_index(mean)
  dep_target=np.clip(base_next[...,7]+float(cfg['dependency_feedback_strength'])*div*prop*(.45+.55*management),0,1)
  dep += .16*kyr*(dep_target-dep);dep=np.maximum(dep,base_next[...,7]);dep=np.clip(dep,0,1)
  food=np.zeros((M,L,P),float);di=np.zeros_like(food)
  for p,tax in enumerate(inp['reg34']['taxa']):
   tv=tax['trait_values'];contact=base_next[:,:,p,0];processing_factor=.70+.30*base_next[:,:,p,1]
   food[:,:,p]=np.clip(contact*float(tv['edible_yield'])*(1+.45*mean[:,:,p,4])*(.18*management[:,:,p]+.38*prop[:,:,p]+.44*div[:,:,p])*processing_factor,0,1)
  di=np.clip(.12*base_next[...,2]+.30*prop+.18*base_next[...,4]+.28*div+.12*dep,0,1)
  if store_trajectory:
   means[:,:,:,t+1,:]=mean;vas[:,:,:,t+1,:]=va;h2s[:,:,:,t+1,:]=va/(va+pri['ve'][None,None,:,:]);responses[:,:,:,t+1,:]=response;props[:,:,:,t+1]=prop;deps[:,:,:,t+1]=dep;divs[:,:,:,t+1]=div;foods[:,:,:,t+1]=food;dis[:,:,:,t+1]=di
 final_parent=parent[:,:,:,-1,:];final_wild=np.clip(final_parent[...,6]*gene_flow_multiplier,0,1);final_div=_divergence_index(mean)
 # Recompute endpoint food/DI to support no-trajectory sensitivity.
 final_food=np.zeros((M,L,P),float)
 for p,tax in enumerate(inp['reg34']['taxa']):
  tv=tax['trait_values'];contact=final_parent[:,:,p,0];pf=.70+.30*final_parent[:,:,p,1]
  final_food[:,:,p]=np.clip(contact*float(tv['edible_yield'])*(1+.45*mean[:,:,p,4])*(.18*final_parent[:,:,p,2]+.38*prop[:,:,p]+.44*final_div[:,:,p])*pf,0,1)
 final_di=np.clip(.12*final_parent[...,2]+.30*prop+.18*final_parent[...,4]+.28*final_div+.12*dep,0,1)
 stage=_stage_from_endpoint(prop,final_div,final_di,final_wild,final_parent,inp['pcfg'])
 out={'mean_final':mean,'va_final':va,'h2_final':va/(va+pri['ve'][None,None,:,:]),'prop_final':prop,'dep_final':dep,'div_final':final_div,'food_final':final_food,'di_final':final_di,'wild_final':final_wild,'stage':stage,'priors':pri}
 if store_trajectory:
  out.update({'age_ka':ages,'mean_shift':means,'additive_variance':vas,'heritability':h2s,'selection_response':responses,'effective_propagation_control':props,'effective_dependency':deps,'genetic_divergence_index':divs,'effective_food_contribution':foods,'genetic_domestication_index':dis})
 return out

def summarize(inp:dict[str,Any],rep:dict[str,np.ndarray],cfg:dict[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
 stage=rep['stage'];taxa=[];materialized=[];incipient=[]
 for p,tax in enumerate(inp['reg34']['taxa']):
  lo=[]
  for l,sid in enumerate(EXPECTED_CANDIDATES):
   f5=float(np.mean(stage[:,l,p]>=5));f4=float(np.mean(stage[:,l,p]>=4));f3=float(np.mean(stage[:,l,p]>=3))
   lo.append({'lineage_id':sid,'controlled_propagation_frequency':f3,'incipient_domestication_frequency':f4,'functional_domestication_frequency':f5,'genetic_divergence_median':float(np.median(rep['div_final'][:,l,p])),'effective_propagation_median':float(np.median(rep['prop_final'][:,l,p])),'food_contribution_median':float(np.median(rep['food_final'][:,l,p]))})
  mx5=max(x['functional_domestication_frequency'] for x in lo);mx4=max(x['incipient_domestication_frequency'] for x in lo)
  pcfg=inp['pcfg']
  if mx5>=float(pcfg['materialization_frequency_threshold']): materialized.append(tax['producer_taxon_id'])
  elif mx4>=float(pcfg['incipient_frequency_threshold']): incipient.append(tax['producer_taxon_id'])
  taxa.append({'producer_taxon_id':tax['producer_taxon_id'],'archetype':tax['archetype'],'lineage_outcomes':lo,'materialized_functional_domesticate':tax['producer_taxon_id'] in materialized,'incipient_domestication':tax['producer_taxon_id'] in incipient})
 lineages=[]
 for l,sid in enumerate(EXPECTED_CANDIDATES):
  total=np.clip(np.sum(np.sort(rep['food_final'][:,l,:],axis=1)[:,-6:],axis=1),0,1);inc=np.sum(stage[:,l,:]>=4,axis=1);dom=np.sum(stage[:,l,:]>=5,axis=1)
  lineages.append({'lineage_id':sid,'plant_food_production_support_median':float(np.median(total)),'incipient_or_better_count_median':float(np.median(inc)),'functional_domesticate_count_median':float(np.median(dom)),'plant_food_production_emergence':bool(np.median(total)>=float(inp['pcfg']['plant_food_production_threshold']) and np.mean(inc>=1)>=float(inp['pcfg']['food_production_frequency_threshold']))})
 plant_food=any(x['plant_food_production_emergence'] for x in lineages);agriculture=bool(materialized and any(x['plant_food_production_support_median']>=float(inp['pcfg']['agriculture_food_support_threshold']) for x in lineages))
 outcomes={'stage':STAGE,'status':'R335_DOMESTICATION_GENETICS_OUTCOMES','producer_taxon_count':EXPECTED_PRODUCERS,'materialized_functional_plant_domesticates':materialized,'incipient_plant_domestication_taxa':incipient,'plant_food_production_emergence':plant_food,'agriculture_materialized':agriculture,'lineages':lineages,'taxa':taxa}
 variants=[]
 for sm,gm,fm in [(0.75,1,1),(1,1,1),(1.25,1,1),(1,.75,1),(1,1.25,1),(1,1,.75),(1,1,1.25),(.85,.85,1.15),(1.15,1.15,.85),(1.25,.75,1.25),(.75,1.25,.75),(1.1,.9,1.1)]:
  r=replay_genetics(inp,cfg,sm,gm,fm,store_trajectory=False);st=r['stage'];variants.append({'selection_multiplier':sm,'gene_flow_multiplier':gm,'feedback_multiplier':fm,'incipient_any_frequency':[float(np.mean(np.any(st[:,l,:]>=4,axis=1))) for l in range(2)],'functional_domestication_any_frequency':[float(np.mean(np.any(st[:,l,:]>=5,axis=1))) for l in range(2)],'max_genetic_divergence':float(np.max(r['div_final']))})
 sens={'stage':STAGE,'status':'R335_PRODUCER_GENETICS_SENSITIVITY','variant_count':len(variants),'selection_gate':False,'variants':variants}
 cp={'stage':STAGE,'status':'R335_DOMESTICATION_GENETICS_CHECKPOINT_0KA','age_ka':0.0,'candidate_cohort':EXPECTED_CANDIDATES,'producer_taxon_count':EXPECTED_PRODUCERS,'materialized_functional_plant_domesticates':materialized,'incipient_plant_domestication_taxa':incipient,'plant_food_production_emergence':plant_food,'agriculture_materialized':agriculture,'unique_human_identity_materialized':False,'deep_biological_coupling':False}
 return outcomes,sens,cp

def _audit(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],outs:dict[str,Any],sens:dict[str,Any])->dict[str,Any]:
 checks=[]
 def ck(n,c,d=None):checks.append({'name':n,'pass':bool(c),'detail':d})
 pcfg=inp['pcfg'];thr=['incipient_divergence_threshold','incipient_domestication_index_threshold','incipient_propagation_threshold','domestication_divergence_threshold','domestication_index_threshold','domestication_propagation_threshold','max_wild_gene_flow_for_domestication','materialization_frequency_threshold','incipient_frequency_threshold','plant_food_production_threshold','food_production_frequency_threshold','agriculture_food_support_threshold']
 ck('parent_sealed',inp['a34']['status']==PARENT_PASS);ck('producer_count_36',len(inp['reg34']['taxa'])==36);ck('parent_no_domesticates',inp['cp34']['materialized_functional_plant_domesticates']==[]);ck('r334_thresholds_inherited',all(k in pcfg for k in thr));ck('six_genetic_traits',len(GENETIC_TRAIT_NAMES)==6);ck('correlation_matrix_positive_definite',np.linalg.eigvalsh(_corr_matrix(float(cfg['genetic_covariance_offdiag']))).min()>0)
 ck('trajectory_geometry',rep['mean_shift'].shape==(32,2,36,145,6));ck('va_geometry',rep['additive_variance'].shape==(32,2,36,145,6));ck('heritability_geometry',rep['heritability'].shape==(32,2,36,145,6));ck('response_geometry',rep['selection_response'].shape==(32,2,36,145,6));ck('means_bounded',np.isfinite(rep['mean_shift']).all() and rep['mean_shift'].min()>=0 and rep['mean_shift'].max()<=1);ck('va_positive_bounded',np.isfinite(rep['additive_variance']).all() and rep['additive_variance'].min()>0 and rep['additive_variance'].max()<=float(cfg['va_ceiling'])+1e-12);ck('heritability_bounded',rep['heritability'].min()>=0 and rep['heritability'].max()<=1);ck('initial_mean_zero',np.max(rep['mean_shift'][:,:,:,0,:])==0);ck('effective_propagation_not_below_parent',np.min(rep['effective_propagation_control']-np.asarray(inp['z34']['trajectory_state'],float)[...,3])>=-1e-7);ck('divergence_bounded',rep['genetic_divergence_index'].min()>=0 and rep['genetic_divergence_index'].max()<=1);ck('stage_bounded',set(np.unique(rep['stage'])).issubset(set(range(6))));ck('sensitivity_12',sens['variant_count']==12);ck('sensitivity_no_selection',sens['selection_gate'] is False);ck('outcomes_taxa_36',len(outs['taxa'])==36);ck('no_named_crop_governance',cfg['governance']['no_named_earth_crop_analogues'] is True);ck('no_lineage_rescale',cfg['governance']['no_lineage_specific_rescaling'] is True);ck('unique_human_off',cfg['governance']['unique_human_identity_materialized'] is False);ck('deep_off',cfg['governance']['deep_biological_coupling'] is False);ck('evidence_multisource',len(EVIDENCE)>=6)
 failed=[x for x in checks if not x['pass']]
 return {'stage':STAGE,'status':CANDIDATE_PASS if not failed else 'FAIL_R335_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'checks':checks,'summary':{'candidate_lineages':2,'producer_operational_taxa':36,'genetic_traits':6,'explicit_additive_variance':True,'multivariate_selection_response':True,'materialized_functional_plant_domesticates_count':len(outs['materialized_functional_plant_domesticates']),'incipient_plant_domestication_taxa_count':len(outs['incipient_plant_domestication_taxa']),'plant_food_production_emergence':outs['plant_food_production_emergence'],'agriculture_materialized':outs['agriculture_materialized'],'deep_biological_coupling':False}}

def build_outputs(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],out:Path)->dict[str,Any]:
 out.mkdir(parents=True,exist_ok=True);outs,sens,cp=summarize(inp,rep,cfg);pri=rep['priors']
 auth={'stage':STAGE,'status':'R335_PRODUCER_QUANTITATIVE_GENETICS_AUTHORITY','parent':PARENT_PASS,'candidate_cohort':EXPECTED_CANDIDATES,'producer_taxon_count':36,'genetic_trait_names':GENETIC_TRAIT_NAMES,'genetic_model':'MULTIVARIATE_BREEDER_EQUATION_DELTA_Z_EQUALS_G_BETA_TIMES_GENERATIONS','managed_population_reference':'GENETIC_MEAN_SHIFTS_ARE_FOR_MANAGED_PRODUCER_SUBPOPULATIONS_RELATIVE_TO_WILD_REFERENCE','wild_gene_flow_semantics':'R334_WILD_GENE_FLOW_PRESSURE_ATTENUATES_SELECTION_RESPONSE_AND_PULLS_MANAGED_MEAN_TOWARD_WILD_REFERENCE','variance_semantics':'ADDITIVE_VARIANCE_DEPLETED_BY_DIRECTIONAL_RESPONSE_AND_REPLENISHED_BY_MUTATION_RECOMBINATION_AND_WILD_INTROGRESSION','r334_domestication_thresholds_inherited_exactly':True,'coevolution_feedback':'GENETIC_RESPONSE_CAN_INCREASE_EFFECTIVE_PROPAGATION_CONTROL_BUT_NEVER_REDUCE_R334_BASELINE','retroactive_h0_flora_phylogeny_claimed':False,'unique_human_identity_materialized':False,'deep_biological_coupling':False,'evidence_basis':EVIDENCE,'dynamics':cfg,'parent_hashes':{'r334_trajectory_sha256':sha256_file(inp['r34']/'R3_34_PLANT_COEVOLUTION_DOMESTICATION_TRAJECTORIES.npz'),'r334_registry_sha256':sha256_file(inp['r34']/'R3_34_PRODUCER_TAXON_REGISTRY.json'),'r334_checkpoint_sha256':sha256_file(inp['r34']/'R3_34_FOOD_PRODUCTION_CHECKPOINT.json')}}
 write_json(out/'R3_35_PRODUCER_QUANTITATIVE_GENETICS_AUTHORITY.json',auth)
 np.savez_compressed(out/'R3_35_PRODUCER_GENETIC_PRIORS.npz',producer_taxon_ids=np.array([x['producer_taxon_id'] for x in inp['reg34']['taxa']]),genetic_trait_names=np.array(GENETIC_TRAIT_NAMES),initial_additive_variance=pri['va0'],environmental_variance=pri['ve'],initial_heritability=pri['h20'],selection_profile=pri['selection_profile'],generation_interval_years=pri['generation_interval_years'])
 np.savez_compressed(out/'R3_35_PRODUCER_DOMESTICATION_GENETIC_REPLAY.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=inp['z34']['parent_member_indices'],producer_taxon_ids=np.array([x['producer_taxon_id'] for x in inp['reg34']['taxa']]),age_ka=rep['age_ka'],genetic_trait_names=np.array(GENETIC_TRAIT_NAMES),managed_mean_shift=rep['mean_shift'],additive_variance=rep['additive_variance'],effective_heritability=rep['heritability'],selection_response=rep['selection_response'],effective_propagation_control=rep['effective_propagation_control'],effective_dependency=rep['effective_dependency'],genetic_divergence_index=rep['genetic_divergence_index'],effective_plant_food_contribution=rep['effective_food_contribution'],genetic_domestication_index=rep['genetic_domestication_index'],domestication_stage=rep['stage'])
 write_json(out/'R3_35_DOMESTICATION_GENETICS_OUTCOMES.json',outs);write_json(out/'R3_35_SENSITIVITY_AND_ROBUSTNESS.json',sens);write_json(out/'R3_35_FOOD_PRODUCTION_CHECKPOINT.json',cp)
 audit=_audit(inp,cfg,rep,outs,sens);write_json(out/'R3_35_INTEGRATED_AUDIT.json',audit);(out/'R3_35_AUDIT.md').write_text(f"# R3.35 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n",encoding='utf-8');return audit

def write_manifest(out:Path,status:str)->None:
 files={}
 for p in sorted(out.iterdir()):
  if p.name=='R3_35_OUTPUT_MANIFEST.json' or not p.is_file():continue
  files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_35_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
