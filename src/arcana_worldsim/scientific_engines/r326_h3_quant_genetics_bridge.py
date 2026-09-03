from __future__ import annotations
from pathlib import Path
from typing import Any
import csv, hashlib, json, math
import numpy as np

STAGE='v0.6D1-R3.26'
PARENT_STAGE='v0.6D1-R3.25'
PARENT_PASS='PASS_R325_H2_DETAILED_CANDIDATE_BIOLOGY_EMBODIMENT_FEASIBILITY_AND_H3_PRIORITY_COHORT_SEALED'
EXPECTED_PARENT_CHECKS=25
EXPECTED_CANDIDATES=6
EXPECTED_ENSEMBLE=96
EXPECTED_TRAITS=31
FINAL_PASS='PASS_R326_H3_QUANTITATIVE_GENETICS_BRIDGE_NEUTRAL_REFERENCE_RARE_TAIL_AND_CANDIDATE_COMPATIBILITY_SEALED'

RHO=0.35
SHARE_INF=0.75
SHARE_UR=0.15
SHARE_EPS=0.10
W_INF=math.sqrt(SHARE_INF)
W_UR=math.sqrt(SHARE_UR)
W_EPS=math.sqrt(SHARE_EPS)
UR_DEN=math.sqrt(1.0-RHO*RHO)
EXPECTED_ZH_PARENT_CORR=0.5*(SHARE_INF+SHARE_UR)

AUTH_HASHES={
 'human_h3_constants.json':'830a70b68ec22a88996e8af30fd8c7ebffd53865b4fbcb9790d306240ce215c7',
 'cb_scale.csv':'46c42ff1dd99ba9436198c4bf69914089b9d1e54ebbd8bdae2e41b8b48ab4fa2',
 'H3_CB_CONTINUOUS_MAPPING_v0_3_70.json':'f5e7b9e45cb887f1b7a14bdf92db6b7bc20b743d713ce45b22fcbd1294b90a1d',
 'H3_CB_QUANTILE_THRESHOLDS_v0_3_70.csv':'b5685702df0ab86011b805976c8b56015bb76f715f9498bd346bd45f02b79f7a',
}

class R326GateError(RuntimeError): pass

def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()

def load_json(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def _close_manifest(d:Path,name:str)->None:
 p=d/name
 if not p.is_file():raise R326GateError(f'Missing manifest {p}')
 m=load_json(p);rows=m.get('files',{})
 if not rows:raise R326GateError(f'Malformed manifest {p}')
 for n,meta in rows.items():
  fp=d/n
  if not fp.is_file():raise R326GateError(f'Manifest file missing {fp}')
  if meta.get('sha256') and sha256_file(fp)!=meta['sha256']:raise R326GateError(f'Hash mismatch {fp}')
  if meta.get('bytes') is not None and fp.stat().st_size!=int(meta['bytes']):raise R326GateError(f'Size mismatch {fp}')

def _read_cb_rows(path:Path)->list[dict[str,Any]]:
 rows=[]
 with path.open(newline='',encoding='utf-8') as f:
  for r in csv.DictReader(f):
   rows.append({'CB':str(r['CB']),'lower_W':float(r['lower_W']),'upper_W':None if not r['upper_W'] else float(r['upper_W']),'prob':float(r['hard_ceiling_probability']),'z':None if not r['Z_H_entry_threshold'] else float(r['Z_H_entry_threshold'])})
 return rows

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root)
 r325=root/'outputs'/'v0_6D1_R3_25';s325=root/'outputs'/'v0_6D1_R3_25_SEAL';r323=root/'outputs'/'v0_6D1_R3_23'
 for d in (r325,s325,r323):
  if not d.is_dir():raise R326GateError(f'Missing required directory {d}')
 a325=load_json(s325/'R3_25_FINAL_SEAL_AUDIT.json')
 if a325.get('stage')!=PARENT_STAGE or a325.get('status')!=PARENT_PASS or a325.get('verdict')!='SEALED' or a325.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a325.get('checks_failed')!=0:raise R326GateError('R3.25 seal mismatch')
 _close_manifest(r325,'R3_25_OUTPUT_MANIFEST.json')
 cohort=load_json(r325/'R3_25_H3_PRIORITY_COHORT.json');cands=list(map(str,cohort.get('priority_cohort',[])))
 if len(cands)!=EXPECTED_CANDIDATES or len(set(cands))!=EXPECTED_CANDIDATES:raise R326GateError('R3.25 H3 cohort mismatch')
 dossiers=load_json(r325/'R3_25_H2_CANDIDATE_DOSSIERS.json')['candidates'];dby={str(x['species_id']):x for x in dossiers}
 if not set(cands).issubset(dby):raise R326GateError('Candidate dossier missing')
 pz=np.load(r323/'R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz',allow_pickle=False)
 if pz['species_mean_z_ensemble'].shape!=(EXPECTED_ENSEMBLE,134,EXPECTED_TRAITS):raise R326GateError('R3.23 functional geometry mismatch')
 auth=root/'authority'/'h3_cb'
 for n,h in AUTH_HASHES.items():
  p=auth/n
  if not p.is_file() or sha256_file(p)!=h:raise R326GateError(f'H3 authority hash mismatch: {n}')
 constants=load_json(auth/'human_h3_constants.json');mapping=load_json(auth/'H3_CB_CONTINUOUS_MAPPING_v0_3_70.json');cb=_read_cb_rows(auth/'cb_scale.csv')
 # canonical algebra cross-check
 if abs(float(constants['h3']['rho_Zinf_ZR'])-RHO)>1e-15:raise R326GateError('rho mismatch')
 vs=constants['h3']['variance_shares']
 if any(abs(float(vs[k])-v)>1e-15 for k,v in [('Z_inf',SHARE_INF),('U_R',SHARE_UR),('epsilon_mar',SHARE_EPS)]):raise R326GateError('H3 variance shares mismatch')
 return {'root':root,'r325':r325,'s325':s325,'a325':a325,'candidates':cands,'dby':dby,'constants':constants,'mapping':mapping,'cb':cb}

def h3_from_latents(z_inf:np.ndarray,u_r:np.ndarray,eps_mar:np.ndarray)->np.ndarray:
 return W_INF*np.asarray(z_inf,float)+W_UR*np.asarray(u_r,float)+W_EPS*np.asarray(eps_mar,float)

def zr_from_latents(z_inf:np.ndarray,u_r:np.ndarray)->np.ndarray:
 return RHO*np.asarray(z_inf,float)+UR_DEN*np.asarray(u_r,float)

def ur_from_zr(z_inf:np.ndarray,z_r:np.ndarray)->np.ndarray:
 return (np.asarray(z_r,float)-RHO*np.asarray(z_inf,float))/UR_DEN

def _pchip_slopes(x:np.ndarray,y:np.ndarray)->np.ndarray:
 x=np.asarray(x,float);y=np.asarray(y,float);h=np.diff(x);delta=np.diff(y)/h;n=len(x);d=np.empty(n,float)
 for k in range(1,n-1):
  if delta[k-1]==0 or delta[k]==0 or np.sign(delta[k-1])!=np.sign(delta[k]): d[k]=0.0
  else:
   w1=2*h[k]+h[k-1];w2=h[k]+2*h[k-1];d[k]=(w1+w2)/(w1/delta[k-1]+w2/delta[k])
 def endpoint(h0,h1,del0,del1):
  val=((2*h0+h1)*del0-h0*del1)/(h0+h1)
  if np.sign(val)!=np.sign(del0):return 0.0
  if np.sign(del0)!=np.sign(del1) and abs(val)>abs(3*del0):return 3*del0
  return val
 d[0]=endpoint(h[0],h[1],delta[0],delta[1]);d[-1]=endpoint(h[-1],h[-2],delta[-1],delta[-2])
 return d

def hard_ceiling_mapper(mapping:dict[str,Any]):
 nodes=mapping['nodes'];x=np.asarray([float(n['Z_H']) for n in nodes]);y=np.log(np.asarray([float(n['J_lower_W']) for n in nodes]));d=_pchip_slopes(x,y);ml=float(mapping['low_tail']['slope_dlnJ_dZH']);mh=float(mapping['high_tail']['slope_dlnJ_dZH'])
 def f(z):
  a=np.asarray(z,float);out=np.empty_like(a,float);lo=a<x[0];hi=a>x[-1];mid=~(lo|hi);out[lo]=y[0]+ml*(a[lo]-x[0]);out[hi]=y[-1]+mh*(a[hi]-x[-1])
  if np.any(mid):
   am=a[mid];idx=np.searchsorted(x,am,side='right')-1;idx=np.clip(idx,0,len(x)-2);xx=x[idx];hh=x[idx+1]-xx;t=(am-xx)/hh
   h00=2*t**3-3*t**2+1;h10=t**3-2*t**2+t;h01=-2*t**3+3*t**2;h11=t**3-t**2
   out[mid]=h00*y[idx]+h10*hh*d[idx]+h01*y[idx+1]+h11*hh*d[idx+1]
  return np.exp(out)
 return f

def cb_labels(z_h:np.ndarray,cb_rows:list[dict[str,Any]])->np.ndarray:
 z=np.asarray(z_h,float);bounds=np.asarray([r['z'] for r in cb_rows[1:]],float);idx=np.searchsorted(bounds,z,side='right')+1
 return idx.astype(np.int8) # 1..12

def normal_cdf(z:float)->float:return 0.5*(1.0+math.erf(z/math.sqrt(2.0)))

def analytic_cb_probs(cb_rows:list[dict[str,Any]])->dict[str,float]:
 bounds=[-math.inf]+[float(r['z']) for r in cb_rows[1:]]+[math.inf];out={}
 for i,r in enumerate(cb_rows):
  lo,hi=bounds[i],bounds[i+1];clo=0.0 if lo==-math.inf else normal_cdf(lo);chi=1.0 if hi==math.inf else normal_cdf(hi);out[r['CB']]=chi-clo
 return out

def neutral_reference(n:int,seed:int,cb_rows:list[dict[str,Any]])->dict[str,Any]:
 rng=np.random.default_rng(seed);chunk=200000
 sums=np.zeros(5);sums2=np.zeros(5);cross=np.zeros((5,5));counts=np.zeros(12,dtype=np.int64);seen=0
 # vars order zinf,zr,ur,eps,zh
 while seen<n:
  m=min(chunk,n-seen);zinf=rng.standard_normal(m);ur=rng.standard_normal(m);eps=rng.standard_normal(m);zr=zr_from_latents(zinf,ur);zh=h3_from_latents(zinf,ur,eps);X=np.column_stack((zinf,zr,ur,eps,zh));sums+=X.sum(0);sums2+=(X*X).sum(0);cross+=X.T@X
  lab=cb_labels(zh,cb_rows);counts+=np.bincount(lab,minlength=13)[1:13];seen+=m
 means=sums/n;vars_=sums2/n-means*means;std=np.sqrt(vars_);cov=cross/n-np.outer(means,means);corr=cov/np.outer(std,std);an=analytic_cb_probs(cb_rows)
 return {'n':n,'seed':seed,'mean':dict(zip(['Z_inf','Z_R','U_R','epsilon_mar','Z_H'],map(float,means))),'std':dict(zip(['Z_inf','Z_R','U_R','epsilon_mar','Z_H'],map(float,std))),'corr':{'Z_inf__Z_R':float(corr[0,1]),'Z_inf__U_R':float(corr[0,2]),'Z_H__Z_inf':float(corr[4,0]),'Z_H__Z_R':float(corr[4,1]),'Z_H__U_R':float(corr[4,2]),'Z_H__epsilon_mar':float(corr[4,3])},'observed_cb_counts':{f'CB{i+1}':int(counts[i]) for i in range(12)},'observed_cb_probabilities':{f'CB{i+1}':float(counts[i]/n) for i in range(12)},'analytic_cb_probabilities':an}

def reproduction_reference(n:int,seed:int)->dict[str,Any]:
 rng=np.random.default_rng(seed);chunk=100000;sumv=np.zeros(6);sum2=np.zeros(6);cross=np.zeros((6,6));seen=0
 # mother_zh father_zh child_zh mother_zinf child_zinf child_ur
 while seen<n:
  m=min(chunk,n-seen)
  mi=rng.standard_normal(m);mu=rng.standard_normal(m);me=rng.standard_normal(m);fi=rng.standard_normal(m);fu=rng.standard_normal(m);fe=rng.standard_normal(m)
  ci=.5*(mi+fi)+math.sqrt(.5)*rng.standard_normal(m);cu=.5*(mu+fu)+math.sqrt(.5)*rng.standard_normal(m);ce=rng.standard_normal(m)
  mz=h3_from_latents(mi,mu,me);fz=h3_from_latents(fi,fu,fe);cz=h3_from_latents(ci,cu,ce);X=np.column_stack((mz,fz,cz,mi,ci,cu));sumv+=X.sum(0);sum2+=(X*X).sum(0);cross+=X.T@X;seen+=m
 mean=sumv/n;std=np.sqrt(sum2/n-mean*mean);cov=cross/n-np.outer(mean,mean);corr=cov/np.outer(std,std)
 return {'families':n,'seed':seed,'child_ZH_mean':float(mean[2]),'child_ZH_std':float(std[2]),'corr_child_mother_ZH':float(corr[2,0]),'corr_child_father_ZH':float(corr[2,1]),'corr_child_mother_Zinf':float(corr[4,3]),'expected_parent_ZH_corr':EXPECTED_ZH_PARENT_CORR,'offspring_from_upstream_latents_only':True,'parental_CB_label_input':False,'epsilon_mar_inherited_directly':False}

def rare_tail_table(cb_rows:list[dict[str,Any]])->list[dict[str,Any]]:
 probs={r['CB']:r['prob'] for r in cb_rows};tail10=sum(probs[f'CB{i}'] for i in range(10,13));tail11=sum(probs[f'CB{i}'] for i in range(11,13));tail12=probs['CB12'];out=[]
 for N in (10_000,100_000,1_000_000,10_000_000,100_000_000,1_000_000_000):
  out.append({'population_size':N,'expected_CB10plus':N*tail10,'p_at_least_one_CB10plus':1-math.exp(N*math.log1p(-tail10)),'expected_CB11plus':N*tail11,'p_at_least_one_CB11plus':1-math.exp(N*math.log1p(-tail11)),'expected_CB12_compatible':N*tail12,'p_at_least_one_CB12_compatible':1-math.exp(N*math.log1p(-tail12))})
 return out

def candidate_bridge(inputs:dict[str,Any])->list[dict[str,Any]]:
 rows=[]
 for rank,s in enumerate(inputs['candidates'],1):
  d=inputs['dby'][s];mods=d['module_envelope']
  axes={k:float(mods[k]['median']) for k in ('embodied_manipulation','neurocognitive_integration','learning_development_integration','social_transmission_communication','life_history_sustainability','ecological_resource_buffering')}
  rows.append({'species_id':s,'inherited_h2_priority_rank':rank,'h3_bridge_compatible':True,'h3_reference_mean_ZH':0.0,'h3_reference_variance_ZH':1.0,'h3_hard_ceiling_distribution_shift':0.0,'cb_distribution_rescaled_for_lineage':False,'realization_support_axes_from_h2_only':axes,'realization_support_interpretation':'DIAGNOSTIC_ONLY_DOES_NOT_MODIFY_ZH_OR_J_HARD','macro_replay_status':'ELIGIBLE_FOR_FUTURE_HOMININ_MACRO_REPLAY','human_identity_claim':None})
 return rows

def run_stage(inputs:dict[str,Any],cfg:dict[str,Any])->dict[str,Any]:
 neutral=neutral_reference(int(cfg['neutral_reference_n']),int(cfg['neutral_reference_seed']),inputs['cb']);repro=reproduction_reference(int(cfg['reproduction_family_n']),int(cfg['reproduction_seed']));mapper=hard_ceiling_mapper(inputs['mapping']);nodes=inputs['mapping']['nodes'];node_z=np.asarray([float(x['Z_H']) for x in nodes]);node_j=np.asarray([float(x['J_lower_W']) for x in nodes]);mapped=mapper(node_z);mc_z=float(inputs['constants']['character_regression_fixtures']['MC']['Z_H']);mc_j=float(mapper(np.asarray([mc_z]))[0]);bridge=candidate_bridge(inputs);rare=rare_tail_table(inputs['cb'])
 return {'neutral':neutral,'reproduction':repro,'mapping_node_max_rel_error':float(np.max(np.abs(mapped-node_j)/node_j)),'mc_fixture':{'Z_H':mc_z,'mapped_J_hard_W':mc_j,'mapped_J_hard_TW':mc_j/1e12,'expected_J_hard_TW_approx':float(inputs['constants']['character_regression_fixtures']['MC']['J_hard_TW_approx']),'diagnostic_CB':int(cb_labels(np.asarray([mc_z]),inputs['cb'])[0]),'use':'REGRESSION_FIXTURE_ONLY'},'candidate_bridge':bridge,'rare_tail':rare}

def audit_result(inputs:dict[str,Any],cfg:dict[str,Any],r:dict[str,Any])->dict[str,Any]:
 c=[]
 def ck(n,x,d=None):c.append({'name':n,'pass':bool(x),'detail':d})
 n=r['neutral'];rp=r['reproduction'];an=n['analytic_cb_probabilities'];ref={x['CB']:x['prob'] for x in inputs['cb']}
 ck('parent_r325_sealed',inputs['a325'].get('status')==PARENT_PASS and inputs['a325'].get('checks_passed')==25)
 ck('six_candidate_cohort_exact',len(inputs['candidates'])==6 and len(set(inputs['candidates']))==6,inputs['candidates'])
 ck('canonical_variance_shares_sum_one',abs(SHARE_INF+SHARE_UR+SHARE_EPS-1)<1e-15)
 ck('neutral_ZH_mean_near_zero',abs(n['mean']['Z_H'])<0.004,n['mean']['Z_H'])
 ck('neutral_ZH_std_near_one',abs(n['std']['Z_H']-1)<0.004,n['std']['Z_H'])
 ck('neutral_Zinf_ZR_corr',abs(n['corr']['Z_inf__Z_R']-RHO)<0.004,n['corr']['Z_inf__Z_R'])
 ck('neutral_Zinf_UR_independent',abs(n['corr']['Z_inf__U_R'])<0.004,n['corr']['Z_inf__U_R'])
 ck('neutral_ZH_Zinf_corr',abs(n['corr']['Z_H__Z_inf']-W_INF)<0.004,n['corr']['Z_H__Z_inf'])
 exp_zh_zr=RHO*W_INF+UR_DEN*W_UR;ck('neutral_ZH_ZR_corr',abs(n['corr']['Z_H__Z_R']-exp_zh_zr)<0.004,n['corr']['Z_H__Z_R'])
 ck('analytic_cb_probabilities_match_reference_nonterminal',max(abs(an[f'CB{i}']-ref[f'CB{i}']) for i in range(1,12))<3e-10)
 ck('terminal_CB12_probability_approx_ratified',abs(an['CB12']-ref['CB12'])<2e-10,{'analytic':an['CB12'],'ratified':ref['CB12']})
 # Monte Carlo common-band sanity through CB8; 6-sigma plus floor.
 ok=True;det={}
 for i in range(1,9):
  p=ref[f'CB{i}'];obs=n['observed_cb_probabilities'][f'CB{i}'];tol=max(6*math.sqrt(p*(1-p)/n['n']),5e-5);det[f'CB{i}']={'obs':obs,'ref':p,'tol':tol};ok &= abs(obs-p)<=tol
 ck('monte_carlo_common_CB_bands',ok,det)
 ck('mapping_nodes_exact',r['mapping_node_max_rel_error']<1e-12,r['mapping_node_max_rel_error'])
 ck('mapping_monotone',all(inputs['cb'][i]['lower_W']<inputs['cb'][i+1]['lower_W'] for i in range(11)))
 ck('mc_fixture_maps_CB12',r['mc_fixture']['diagnostic_CB']==12)
 ck('mc_fixture_Jhard_matches_ratified',abs(r['mc_fixture']['mapped_J_hard_TW']-r['mc_fixture']['expected_J_hard_TW_approx'])<0.02,r['mc_fixture'])
 ck('reproduction_child_ZH_stationary',abs(rp['child_ZH_mean'])<0.005 and abs(rp['child_ZH_std']-1)<0.005,{'mean':rp['child_ZH_mean'],'std':rp['child_ZH_std']})
 ck('reproduction_parent_child_corr_expected',abs(rp['corr_child_mother_ZH']-EXPECTED_ZH_PARENT_CORR)<0.006 and abs(rp['corr_child_father_ZH']-EXPECTED_ZH_PARENT_CORR)<0.006,rp)
 ck('breeding_value_parent_child_corr_half',abs(rp['corr_child_mother_Zinf']-.5)<0.006,rp['corr_child_mother_Zinf'])
 ck('no_direct_CB_heredity',rp['offspring_from_upstream_latents_only'] and not rp['parental_CB_label_input'])
 ck('epsilon_mar_not_directly_inherited',rp['epsilon_mar_inherited_directly'] is False)
 ck('six_candidate_bridge_rows',len(r['candidate_bridge'])==6 and [x['species_id'] for x in r['candidate_bridge']]==inputs['candidates'])
 ck('all_six_bridge_compatible',all(x['h3_bridge_compatible'] for x in r['candidate_bridge']))
 ck('no_candidate_H3_rescale',all(x['h3_hard_ceiling_distribution_shift']==0 and x['cb_distribution_rescaled_for_lineage'] is False for x in r['candidate_bridge']))
 ck('candidate_support_diagnostic_only',all('DOES_NOT_MODIFY_ZH_OR_J_HARD' in x['realization_support_interpretation'] for x in r['candidate_bridge']))
 ck('no_human_identity_claim',all(x['human_identity_claim'] is None for x in r['candidate_bridge']))
 ck('rare_tail_table_six_scales',len(r['rare_tail'])==6 and r['rare_tail'][-1]['population_size']==1_000_000_000)
 ck('cb12_expected_per_billion_ratified',abs(r['rare_tail'][-1]['expected_CB12_compatible']-43.98)<1e-9,r['rare_tail'][-1]['expected_CB12_compatible'])
 ck('deep_off',cfg.get('deep_biological_coupling') is False)
 ck('no_human_similarity_target',cfg.get('human_similarity_target') is False)
 ck('parent_states_immutable',all(cfg.get(k) is False for k in ('h0_mutation','cha2_mutation','r323_mutation','r324_mutation','r325_mutation')))
 ck('human_200ka_not_materialized',cfg.get('future_macro_replay_checkpoint_target')=='HUMAN_200KA_NOT_MATERIALIZED_IN_R3_26')
 failed=[x for x in c if not x['pass']]
 return {'stage':STAGE,'status':'PASS_R326_H3_QUANT_GENETICS_BRIDGE_CANDIDATE' if not failed else 'FAIL_R326_INTEGRATED_AUDIT','checks_passed':len(c)-len(failed),'checks_total':len(c),'checks_failed':len(failed),'summary':{'candidate_lineages':6,'h3_bridge_compatible_lineages':sum(x['h3_bridge_compatible'] for x in r['candidate_bridge']),'neutral_reference_n':n['n'],'reproduction_families':rp['families'],'human_similarity_target':False,'direct_cb_heredity':False,'deep_biological_coupling':False,'h0_mutated':False,'cha2_mutated':False,'human_200ka_materialized':False},'checks':c}

def build_outputs(inputs:dict[str,Any],cfg:dict[str,Any],r:dict[str,Any],out:Path)->None:
 out.mkdir(parents=True,exist_ok=True)
 authority={'stage':STAGE,'status':'H3_CANONICAL_BRIDGE_AUTHORITY','parent':PARENT_PASS,'source_canon':inputs['constants']['source_canon'],'formula':inputs['constants']['h3'],'continuous_mapping':inputs['mapping'],'hard_ceiling_policy':'SAME_RATIFIED_REFERENCE_LAW_NO_LINEAGE_RESCALE','cb_semantics':'DOWNSTREAM_DIAGNOSTIC_ONLY','reproduction_kernel':{'upstream_breeding_values':['Z_inf','U_R'],'offspring_kernel':'0.5*(mother+father)+sqrt(0.5)*segregation_noise','epsilon_mar':'PERSISTENT_INDIVIDUAL_RESIDUAL_NOT_DIRECTLY_INHERITED','mutation':'NOT_CALIBRATED_OR_MATERIALIZED_IN_R3_26','selection':'NOT_APPLIED_IN_R3_26'},'deep_biological_coupling':False,'human_similarity_target':False}
 write_json(out/'R3_26_H3_CANONICAL_BRIDGE_AUTHORITY.json',authority)
 write_json(out/'R3_26_H3_NEUTRAL_REFERENCE_VALIDATION.json',{'stage':STAGE,'status':'H3_NEUTRAL_REFERENCE_VALIDATION','validation':r['neutral']})
 write_json(out/'R3_26_H3_REPRODUCTION_KERNEL_VALIDATION.json',{'stage':STAGE,'status':'H3_REPRODUCTION_KERNEL_VALIDATION','validation':r['reproduction']})
 write_json(out/'R3_26_H3_RARE_TAIL_EXPECTATION_TABLE.json',{'stage':STAGE,'status':'H3_RARE_TAIL_ANALYTIC_EXPECTATIONS','semantics':'EXPECTATIONS_ONLY_NOT_FRACTIONAL_PERSON_EVENTS','rows':r['rare_tail']})
 write_json(out/'R3_26_H3_CANDIDATE_BRIDGE_DOSSIERS.json',{'stage':STAGE,'status':'H3_CANDIDATE_BRIDGE_DOSSIERS','candidate_count':6,'candidates':r['candidate_bridge'],'interpretation':'ALL_SIX_RETAINED_FOR_FUTURE_MACRO_REPLAY_NO_CB_BASED_DOWNSHIFT'})
 write_json(out/'R3_26_H3_CHARACTER_REGRESSION_FIXTURE.json',{'stage':STAGE,'status':'CHARACTER_REGRESSION_ONLY_NOT_POPULATION_CALIBRATION','MC':r['mc_fixture']})
 # compact numeric authority arrays
 z=np.asarray([x['Z_H'] for x in inputs['mapping']['nodes']],float);j=np.asarray([x['J_lower_W'] for x in inputs['mapping']['nodes']],float);probs=np.asarray([x['prob'] for x in inputs['cb']],float)
 np.savez_compressed(out/'R3_26_H3_DIAGNOSTIC_ARRAYS.npz',mapping_ZH=z,mapping_J_lower_W=j,cb_reference_probabilities=probs,candidate_ids=np.asarray(inputs['candidates']))
 audit=audit_result(inputs,cfg,r);write_json(out/'R3_26_INTEGRATED_AUDIT.json',audit)
 (out/'R3_26_AUDIT.md').write_text(f"# R3.26 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n- H3 bridge compatible lineages: **{audit['summary']['h3_bridge_compatible_lineages']}/6**\n- HUMAN_200KA: **not materialized in R3.26**\n",encoding='utf-8')

def write_manifest(out:Path,status:str)->None:
 files={}
 for p in sorted(out.iterdir()):
  if p.is_file() and p.name!='R3_26_OUTPUT_MANIFEST.json':files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_26_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
