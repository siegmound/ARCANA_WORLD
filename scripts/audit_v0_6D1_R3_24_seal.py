from __future__ import annotations
from pathlib import Path
import hashlib, json, sys
import numpy as np

STAGE='v0.6D1-R3.24'
PASS='PASS_R324_H1_FUNCTIONAL_READINESS_CANDIDATE_DISCOVERY_ROBUSTNESS_AND_NON_TELEOLOGICAL_SHORTLIST_SEALED'
PARENT='PASS_R323_COMPARATIVE_FUNCTIONAL_PRIOR_CALIBRATION_ANCESTRAL_ENSEMBLE_AND_H0_CONDITIONED_PHYLOGENETIC_FUNCTIONAL_REPLAY_SEALED'
TRAITS=[
'M1_effector_independence','M2_force_precision_span','M3_workspace_control','M4_sensorimotor_feedback',
'L1_locomotor_mode_breadth','L2_substrate_breadth','L3_transition_control','L4_effector_locomotor_decoupling',
'C1_working_memory','C2_inhibitory_control','C3_relational_integration','C4_causal_model_depth',
'P1_acquisition_efficiency','P2_retention_stability','P3_cross_context_transfer','P4_developmental_plasticity',
'S1_social_tolerance','S2_coordination_capacity','S3_social_learning_fidelity','S4_communication_bandwidth',
'D1_resource_breadth','D2_digestive_processing_breadth','D3_resource_switching',
'H1_maturation_duration','H2_reproductive_output_rate','H3_parental_investment','H4_adult_survival_horizon',
'G1_habitat_breadth','G2_climatic_tolerance_breadth','G3_disturbance_resilience','G4_colonization_breadth']
AXES={
'manipulative_control':['M1_effector_independence','M2_force_precision_span','M3_workspace_control','M4_sensorimotor_feedback'],
'locomotor_effector_interface':['L3_transition_control','L4_effector_locomotor_decoupling'],
'executive_causal_cognition':['C1_working_memory','C2_inhibitory_control','C3_relational_integration','C4_causal_model_depth'],
'learning_flexibility':['P1_acquisition_efficiency','P2_retention_stability','P3_cross_context_transfer','P4_developmental_plasticity'],
'social_transmission':['S1_social_tolerance','S2_coordination_capacity','S3_social_learning_fidelity','S4_communication_bandwidth'],
'life_history_learning_support':['H1_maturation_duration','H3_parental_investment','H4_adult_survival_horizon'],
'ecological_dietary_flexibility':['D1_resource_breadth','D2_digestive_processing_breadth','D3_resource_switching','G1_habitat_breadth','G2_climatic_tolerance_breadth','G3_disturbance_resilience','G4_colonization_breadth']}
GRID=(.30,.35,.40,.45,.50)
N=12

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
 return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,o): p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def pct(x):
 x=np.asarray(x,float); m,n=x.shape; out=np.empty_like(x)
 for k in range(m):
  vals=x[k]; order=np.argsort(vals,kind='mergesort'); ranks=np.empty(n,float); i=0
  while i<n:
   j=i+1
   while j<n and vals[order[j]]==vals[order[i]]: j+=1
   ranks[order[i:j]]=0.5*((i+1)+j); i=j
  out[k]=(ranks-.5)/n
 return out
def axis(F,method='geomean', subset=None):
 ix={t:i for i,t in enumerate(TRAITS)}; names=list(AXES) if subset is None else subset; rows=[]
 for name in names:
  P=np.stack([pct(F[:,:,ix[t]]) for t in AXES[name]],axis=-1)
  rows.append(np.exp(np.mean(np.log(np.clip(P,1e-12,1.0)),axis=-1)) if method=='geomean' else np.quantile(P,.25,axis=-1))
 return names,np.stack(rows,axis=-1)
def front(v):
 n=v.shape[0]; f=np.ones(n,bool)
 for i in range(n):
  ge=np.all(v>=v[i],axis=1); gt=np.any(v>v[i],axis=1)
  if np.any(ge&gt): f[i]=False
 return f
def rankdesc(v):
 v=np.asarray(v,float); n=len(v); order=np.argsort(-v,kind='mergesort'); r=np.empty(n,float); i=0
 while i<n:
  j=i+1
  while j<n and v[order[j]]==v[order[i]]: j+=1
  r[order[i:j]]=0.5*((i+1)+j); i=j
 return r
def select(core,tp,qp,rr,sids,mask=None,axis_idx=None,derived=True):
 if mask is None: mask=np.ones(core.shape[0],bool)
 c=core[mask];t=tp[mask];q=qp[mask];r=np.asarray(rr)[mask]
 if axis_idx is None: axis_idx=list(range(c.shape[2]))
 c=c[:,:,axis_idx]; balance=np.min(np.median(c,axis=0),axis=1)
 hits=np.zeros((len(c),len(sids)),bool)
 for m in range(len(c)):
  dims=c[m] if not derived else np.concatenate([c[m],t[m,:,None],q[m,:,None]],axis=1)
  hits[m]=front(dims)
 crr=[];drr=[];frr=[]
 for rg in sorted(set(map(str,r.tolist()))):
  rm=np.asarray([str(x)==rg for x in r],bool)
  crr.append(np.min(np.median(c[rm],axis=0),axis=1));drr.append(np.minimum(np.median(t[rm],axis=0),np.median(q[rm],axis=0)));frr.append(hits[rm].mean(0))
 support=np.mean(np.stack([(c>=g).mean(0) for g in GRID],axis=0),axis=0)
 metrics={'core_balance':balance,'core_regime_floor':np.min(np.stack(crr),axis=0),'core_threshold_floor_robustness':np.min(support,axis=1),'pareto_front1_probability':hits.mean(0),'pareto_regime_floor':np.min(np.stack(frr),axis=0)}
 if derived:
  metrics['derived_median_floor']=np.minimum(np.median(t,axis=0),np.median(q,axis=0)); metrics['derived_regime_floor']=np.min(np.stack(drr),axis=0)
 names=list(metrics); ranks=np.column_stack([rankdesc(metrics[n]) for n in names]); med=np.median(ranks,axis=1); mean=ranks.mean(1)
 order=sorted(range(len(sids)),key=lambda i:(float(med[i]),float(mean[i]),sids[i]))
 return [sids[i] for i in order],metrics,ranks,med,mean

def main(root:Path)->int:
 out=root/'outputs'/'v0_6D1_R3_24'; seal=root/'outputs'/'v0_6D1_R3_24_SEAL'; parent=root/'outputs'/'v0_6D1_R3_23'; pseal=root/'outputs'/'v0_6D1_R3_23_SEAL'
 checks=[]
 def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
 pa=pseal/'R3_23_FINAL_SEAL_AUDIT.json'; pm=pseal/'R3_23_FINAL_SEAL_MANIFEST.json'
 ck('parent_seal_present',pa.is_file() and pm.is_file())
 if pa.is_file() and pm.is_file():
  a=js(pa);ck('parent_r323_exact',a.get('stage')=='v0.6D1-R3.23' and a.get('status')==PARENT and a.get('verdict')=='SEALED');ck('parent_48_of_48',a.get('checks_passed')==48 and a.get('checks_total')==48 and a.get('checks_failed')==0)
  m=js(pm);ok=True
  for n,meta in m.get('files',{}).items():
   p=pseal/n;ok &= p.is_file() and p.stat().st_size==meta.get('bytes') and sha(p)==meta.get('sha256')
  ck('parent_seal_manifest_closure',ok)
 else:
  ck('parent_r323_exact',False);ck('parent_48_of_48',False);ck('parent_seal_manifest_closure',False)
 expected={'R3_24_AUDIT.md','R3_24_H1_CANDIDATE_SHORTLIST.json','R3_24_H1_DIAGNOSTIC_ARRAYS.npz','R3_24_H1_DISCOVERY_CRITERIA_AUTHORITY.json','R3_24_INTEGRATED_AUDIT.json','R3_24_OUTPUT_MANIFEST.json','R3_24_SENSITIVITY_AND_ROBUSTNESS.json','R3_24_SPECIES_DIAGNOSTICS.json'}
 ck('output_dir_and_file_set_exact',out.is_dir() and {p.name for p in out.iterdir() if p.is_file()}==expected, sorted(p.name for p in out.iterdir() if p.is_file()) if out.is_dir() else None)
 man=js(out/'R3_24_OUTPUT_MANIFEST.json');mok=True
 for n,meta in man.get('files',{}).items():
  p=out/n;mok &= p.is_file() and p.stat().st_size==meta.get('bytes') and sha(p)==meta.get('sha256')
 ck('output_manifest_closure',mok and man.get('stage')==STAGE)
 crit=js(out/'R3_24_H1_DISCOVERY_CRITERIA_AUTHORITY.json'); diag=js(out/'R3_24_SPECIES_DIAGNOSTICS.json'); short=js(out/'R3_24_H1_CANDIDATE_SHORTLIST.json'); sens=js(out/'R3_24_SENSITIVITY_AND_ROBUSTNESS.json'); ia=js(out/'R3_24_INTEGRATED_AUDIT.json')
 ck('integrated_audit_28_of_28',ia.get('checks_passed')==28 and ia.get('checks_total')==28 and ia.get('checks_failed')==0 and all(x.get('pass') for x in ia.get('checks',[])))
 ck('criteria_target_semantics',crit.get('human_similarity_target') is False and crit.get('h1_functional_readiness_target') is True and crit.get('backpropagation_to_r323') is False)
 ck('criteria_no_single_score',crit.get('candidate_selection',{}).get('no_single_readiness_score') is True and crit.get('candidate_selection',{}).get('no_absolute_pass_fail_human_threshold') is True)
 ck('criteria_axes_exact',crit.get('core_axes')==AXES)
 ck('criteria_h2_excluded',crit.get('excluded_monotone_life_history_trait',{}).get('trait_id')=='H2_reproductive_output_rate')
 ck('criteria_evidence_multisource',len(crit.get('evidence_basis',{}))>=4)
 rows=diag.get('species',[]); sids=[r.get('species_id') for r in rows]
 ck('species_diagnostics_134_unique',len(rows)==134 and len(set(sids))==134)
 ck('no_absolute_human_scores',all(r.get('absolute_human_ready') is None and r.get('human_similarity_score') is None for r in rows))
 cand=short.get('candidate_order',[])
 ck('shortlist_12_unique_subset',len(cand)==12 and len(set(cand))==12 and set(cand).issubset(set(sids)),cand)
 ck('shortlist_rank_sequence', [r.get('shortlist_rank') for r in short.get('candidates',[])]==list(range(1,13)))
 ck('shortlist_interpretation_not_identity',short.get('absolute_human_ready_claim') is False and 'NOT_DECLARATION_OF_HUMAN_IDENTITY' in short.get('interpretation',''))
 ck('sensitivity_13_variants',sens.get('variant_count')==13 and len(sens.get('variants',[]))==13)
 ck('sensitivity_each_shortlist_12_unique',all(len(v.get('shortlist',[]))==12 and len(set(v.get('shortlist',[])))==12 for v in sens.get('variants',[])))
 # Independent numerical rebuild from SEALED parent.
 pz=np.load(parent/'R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz',allow_pickle=False); rz=np.load(out/'R3_24_H1_DIAGNOSTIC_ARRAYS.npz',allow_pickle=False); ps=js(parent/'R3_23_PRESENT_FUNCTIONAL_SUMMARY.json')
 Fsp=pz['species_mean_z_ensemble'];Fcomp=pz['functional_mean_z_ensemble'];T=pz['tool_use_potential_ensemble'];Q=pz['environmental_problem_solving_ensemble'];rr=np.asarray(pz['rate_regime']).astype(str);psids=list(map(str,pz['species_ids']));cids=list(map(str,pz['component_ids']))
 ck('parent_npz_geometry',Fsp.shape==(96,134,31) and Fcomp.shape==(96,295,31) and T.shape==(96,295) and Q.shape==(96,295))
 ck('diagnostic_npz_keys_exact',set(rz.files)=={'species_ids','axis_names','rate_regime','core_axis_percentile_ensemble','tool_use_species_ensemble','problem_solving_species_ensemble','tool_use_percentile_ensemble','problem_solving_percentile_ensemble'})
 ck('diagnostic_orders_exact',list(map(str,rz['species_ids']))==psids and list(map(str,rz['axis_names']))==list(AXES) and list(map(str,rz['rate_regime']))==list(rr))
 _,core=axis(Fsp);ck('core_axes_recomputed_exact',np.max(np.abs(core-rz['core_axis_percentile_ensemble']))<=1e-15,float(np.max(np.abs(core-rz['core_axis_percentile_ensemble']))))
 # independent component->species T/Q aggregation
 cr={str(r['component_id']):r for r in ps['components']}; by={s:[] for s in psids}
 for i,cid in enumerate(cids): by[str(cr[cid]['species_id'])].append(i)
 Ts=np.zeros((96,134));Qs=np.zeros((96,134))
 for si,sid in enumerate(psids):
  inds=by[sid];w=np.asarray([float(cr[cids[i]]['population_total']) for i in inds]);w=w/w.sum() if w.sum()>0 else np.ones(len(inds))/len(inds);Ts[:,si]=np.sum(T[:,inds]*w[None,:],axis=1);Qs[:,si]=np.sum(Q[:,inds]*w[None,:],axis=1)
 ck('species_derived_recomputed_exact',np.max(np.abs(Ts-rz['tool_use_species_ensemble']))<=1e-15 and np.max(np.abs(Qs-rz['problem_solving_species_ensemble']))<=1e-15,{'T':float(np.max(np.abs(Ts-rz['tool_use_species_ensemble']))),'Q':float(np.max(np.abs(Qs-rz['problem_solving_species_ensemble'])))})
 tp=pct(Ts);qp=pct(Qs);ck('derived_percentiles_recomputed_exact',np.max(np.abs(tp-rz['tool_use_percentile_ensemble']))<=1e-15 and np.max(np.abs(qp-rz['problem_solving_percentile_ensemble']))<=1e-15)
 order,metrics,ranks,med,mean=select(core,tp,qp,rr,psids);ck('baseline_candidate_order_independently_recomputed',order[:12]==cand,order[:12])
 # independent sensitivity reconstruction
 variants=[('BASELINE',order[:12])]
 for ai,n in enumerate(AXES): variants.append((f'LEAVE_ONE_AXIS_OUT::{n}',select(core,tp,qp,rr,psids,axis_idx=[i for i in range(7) if i!=ai])[0][:12]))
 for rg in sorted(set(rr.tolist())): variants.append((f'RATE_REGIME_ONLY::{rg}',select(core,tp,qp,rr,psids,mask=(rr==rg))[0][:12]))
 _,q25=axis(Fsp,'q25');variants.append(('AXIS_AGGREGATION::Q25',select(q25,tp,qp,rr,psids)[0][:12]));variants.append(('PRIMITIVE_ONLY_NO_TQ',select(core,tp,qp,rr,psids,derived=False)[0][:12]))
 observed=[(v['variant'],v['shortlist']) for v in sens['variants']];ck('sensitivity_variants_independently_recomputed',observed==variants)
 counts={s:0 for s in psids}
 for n,sl in variants:
  for s in sl: counts[s]+=1
 freq={s:counts[s]/len(variants) for s in psids};obsf=sens.get('selection_frequency',{});ck('sensitivity_frequency_recomputed',all(abs(float(obsf[s])-freq[s])<=1e-15 for s in psids))
 # candidate diagnostic rows must match independently rebuilt consensus fields.
 rowby={r['species_id']:r for r in rows}; metric_names=list(metrics)
 diag_ok=True;maxd=0.0
 for i,s in enumerate(psids):
  r=rowby[s]
  for j,n in enumerate(metric_names):
   maxd=max(maxd,abs(float(r['diagnostics'][n])-float(metrics[n][i])),abs(float(r['diagnostic_ranks'][n])-float(ranks[i,j])))
  maxd=max(maxd,abs(float(r['consensus_median_diagnostic_rank'])-float(med[i])),abs(float(r['consensus_mean_diagnostic_rank'])-float(mean[i])))
  diag_ok &= maxd<=1e-12
 ck('species_diagnostic_consensus_recomputed',diag_ok,maxd)
 # lead component ownership
 lead_ok=True
 for r in short['candidates']:
  sid=r['species_id']
  for lc in r['component_heterogeneity']['lead_components']:
   lead_ok &= str(cr[lc['component_id']]['species_id'])==sid
 ck('lead_components_belong_to_candidate_species',lead_ok)
 ck('deep_h0_cha2_parent_immutable',ps.get('governance',{}).get('deep_biological_coupling') is False and ps.get('governance',{}).get('h0_mutated') is False and ps.get('governance',{}).get('cha2_mutated') is False)
 failed=[x for x in checks if not x['pass']]
 report={'stage':STAGE,'audit':'FINAL_SINGLE_STAGE_H1_DISCOVERY_AND_ROBUSTNESS_AUTHORITY_CLOSURE','status':PASS if not failed else 'FAIL_R324_FINAL_SEAL_AUDIT','verdict':'SEALED' if not failed else 'FAIL_CLOSED','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'shortlist_size':12,'candidate_order':cand,'sensitivity_variants':13,'human_similarity_target':False,'h1_functional_readiness_target':True,'deep_biological_coupling':False,'h0_mutated':False,'cha2_mutated':False,'r323_functional_state_mutated':False},'checks':checks}
 seal.mkdir(parents=True,exist_ok=True);ap=seal/'R3_24_FINAL_SEAL_AUDIT.json';write(ap,report);md=seal/'R3_24_FINAL_SEAL_AUDIT.md';md.write_text(f"# R3.24 Final Seal Audit\n\n- Verdict: **{report['verdict']}**\n- Checks: **{report['checks_passed']}/{report['checks_total']}**\n- Status: `{report['status']}`\n",encoding='utf-8');files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [ap,md]};write(seal/'R3_24_FINAL_SEAL_MANIFEST.json',{'stage':STAGE,'status':'FINAL_SEAL_MANIFEST' if not failed else 'FAILED_SEAL_MANIFEST','files':files})
 print(json.dumps(report,indent=2));return 0 if not failed else 1
if __name__=='__main__':
 root=Path(sys.argv[sys.argv.index('--root')+1]).resolve() if '--root' in sys.argv else Path(__file__).resolve().parents[1]
 raise SystemExit(main(root))
