from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json, math
import numpy as np

STAGE='v0.6D1-R3.28'
PARENT_STAGE='v0.6D1-R3.27'
PARENT_PASS='PASS_R327_HOMININ_MACRO_EVOLUTION_REPLAY_TO_200KA_ROBUSTNESS_AND_HUMAN_200KA_CHECKPOINT_SEALED'
EXPECTED_PARENT_CHECKS=28
EXPECTED_CANDIDATES=2
EXPECTED_MEMBERS=32
MAX_DEMES=6
CANDIDATE_PASS='PASS_R328_HIGH_RESOLUTION_200KA_TO_0_REPLAY_CANDIDATE'
FINAL_PASS='PASS_R328_HIGH_RESOLUTION_200KA_TO_0_POPULATION_STRUCTURE_MIGRATION_ADMIXTURE_CHA2_EXPOSURE_AND_HUMAN_0KA_CHECKPOINT_SEALED'
STATE_NAMES=['population_proxy','grid_row','grid_col','local_suitability','genetic_diversity_proxy','adaptive_integration','lineage0_ancestry_fraction']

R318_HASHES={
 'R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz':'54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70',
 'R3_18_RECENT_EXPOSURE_COMPLETION_SUMMARY.json':'189007565f3f70c89b73e71bb4c23e9339bb392c550408a08b0d43c60f71317a',
}
R320_HASHES={
 'R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz':'4319f6464f96014e372e241a9c4b8d801bc945124153a3c9cef6dd25fcb5fb14',
 'R3_20_CHA2_YD_MAGNITUDE_AND_HYDROLOGICAL_HAZARD_SUMMARY.json':'ab5abbe28bccab3df2d18384ff9563e71d82af4d6a59a4e5484ab5c2b5116cab',
}

EVIDENCE={
 'WEAKLY_STRUCTURED_STEM_2023':{'source':'Ragsdale et al. 2023 Nature','doi':'10.1038/s41586-023-06055-y','use':'persistent weak population structure and gene flow are admissible, avoiding a forced single isolated origin'},
 'LATE_PLEISTOCENE_CLIMATE_DISPERSAL_2016':{'source':'Timmermann & Friedrich 2016 Nature','doi':'10.1038/nature19365','use':'climate and sea-level variability may gate dispersal corridors over 125 ka without prescribing a human route'},
 'DEEP_AFRICAN_STRUCTURE_2022':{'source':'Lipson et al. 2022 Nature','doi':'10.1038/s41586-022-04430-9','use':'regional structure and limited long-range gene flow are plausible terminal-Pleistocene outcomes'},
 'LATE_PLEISTOCENE_RETICULATION_2022':{'source':'Harvati & Ackermann 2022 Nature Ecology & Evolution','doi':'10.1038/s41559-022-01875-z','use':'repeated contact/admixture among distinct hominin lineages is admissible and must not be replaced by a strict replacement model'},
 'ORIGINS_COMPLEXITY_2021':{'source':'Bergstrom et al. 2021 Nature','doi':'10.1038/s41586-021-03244-5','use':'no single time/place of final modern ancestry is imposed; multiple evolutionary histories remain admissible'},
}

class R328GateError(RuntimeError): pass

def sha256_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def load_json(p:Path)->Any:return json.loads(p.read_text(encoding='utf-8'))
def write_json(p:Path,o:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def _close_manifest(d:Path,name:str)->None:
 p=d/name
 if not p.is_file():raise R328GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file():raise R328GateError(f'Manifest file missing {fp}')
  if fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:raise R328GateError(f'Manifest closure failure {fp}')

def _discover_exact(root:Path,name:str,expected_hash:str)->Path:
 candidates=[
  root/'local_runs'/'v0_6D1_R3_18'/name,root/'local_runs'/'v0_6D1_R3_20'/name,
  root/'outputs'/'v0_6D1_R3_18'/name,root/'outputs'/'v0_6D1_R3_20'/name,
  root/name,
 ]
 for p in candidates:
  if p.is_file() and sha256_file(p)==expected_hash:return p
 for base in (root/'local_runs',root/'outputs'):
  if base.is_dir():
   for p in base.rglob(name):
    if p.is_file() and sha256_file(p)==expected_hash:return p
 raise R328GateError(f'Could not discover exact sealed artifact {name} / {expected_hash}')

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root)
 r321=root/'outputs'/'v0_6D1_R3_21';r327=root/'outputs'/'v0_6D1_R3_27';s327=root/'outputs'/'v0_6D1_R3_27_SEAL'
 for d in (r321,r327,s327):
  if not d.is_dir():raise R328GateError(f'Missing required directory {d}')
 a327=load_json(s327/'R3_27_FINAL_SEAL_AUDIT.json')
 if a327.get('stage')!=PARENT_STAGE or a327.get('status')!=PARENT_PASS or a327.get('verdict')!='SEALED' or a327.get('checks_passed')!=EXPECTED_PARENT_CHECKS or a327.get('checks_failed')!=0:raise R328GateError('R3.27 seal mismatch')
 _close_manifest(r327,'R3_27_OUTPUT_MANIFEST.json')
 cp=load_json(r327/'R3_27_HUMAN_200KA_CHECKPOINT.json');cands=list(map(str,cp['candidate_cohort']))
 if cands!=['RPT_010_D02','RPT_009_D02'] or cp.get('candidate_count')!=2 or cp.get('unique_human_identity_materialized') is not False:raise R328GateError('R3.27 HUMAN_200KA checkpoint mismatch')
 z27=np.load(r327/'R3_27_MACRO_REPLAY_TRAJECTORIES.npz',allow_pickle=False);ids=list(map(str,z27['candidate_ids']));idx=[ids.index(s) for s in cands]
 member_indices=np.arange(0,96,3,dtype=int);state200=np.asarray(z27['state'][member_indices][:,idx,-1,:],float)
 if state200.shape!=(32,2,8):raise R328GateError('R3.27 200ka stratified state geometry mismatch')
 lineages=load_json(r321/'R3_21_PRESENT_LINEAGE_REGISTRY.json')['lineages'];lby={str(x['species_id']):x for x in lineages}
 comps=load_json(r321/'R3_21_PRESENT_COMPONENT_REGISTRY.json')['components'];cby={s:[x for x in comps if str(x['species_id'])==s] for s in cands}
 if not all(s in lby and len(cby[s])>0 for s in cands):raise R328GateError('R3.21 spatial lineage support missing')
 r318={n:_discover_exact(root,n,h) for n,h in R318_HASHES.items()};r320={n:_discover_exact(root,n,h) for n,h in R320_HASHES.items()}
 z18f=np.load(r318['R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz'],allow_pickle=False);need18=[f'{p}__{f}' for p in ('transport_phase1_125_to_62p5','transport_phase2_62p5_to_0') for f in ('land_support','temperature_c','aridity_index','browse_forage','low_forage','wetland_forage')];z18={k:np.asarray(z18f[k]) for k in need18};z18f.close()
 z20f=np.load(r320['R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz'],allow_pickle=False);need20=['years_before_book','compound_flood_hazard_index','hydrological_disruption_index','raw_support_loss_fraction'];z20={k:np.asarray(z20f[k]) for k in need20};z20f.close()
 if z20['compound_flood_hazard_index'].shape!=(80,90,180):raise R328GateError('R3.20 CHA2 hazard geometry mismatch')
 if z18['transport_phase1_125_to_62p5__temperature_c'].shape!=(90,180):raise R328GateError('R3.18 exposure geometry mismatch')
 return {'root':root,'a327':a327,'candidates':cands,'state200':state200,'parent_member_indices':member_indices,'lby':lby,'cby':cby,'z18':z18,'z20':z20,'r318':r318,'r320':r320}

def build_time_axis()->np.ndarray:
 # ka before book, descending. CHA2 14.95-11.00 ka is exact 50-y resolution.
 a=np.arange(200.0,125.0-1e-12,-2.5)
 b=np.arange(124.0,20.0-1e-12,-1.0)
 c=np.arange(19.75,15.0-1e-12,-.25)
 d=np.arange(14950,10999,-50,dtype=float)/1000.0
 e=np.arange(10.75,-1e-12,-.25)
 out=np.concatenate([a,b,c,d,e])
 if abs(out[0]-200)>1e-12 or abs(out[-1])>1e-12 or len(np.unique(out))!=len(out):raise R328GateError('Time axis construction failure')
 return out

def _phase_maps(z18:Any,phase:int)->dict[str,np.ndarray]:
 pref='transport_phase1_125_to_62p5' if phase==1 else 'transport_phase2_62p5_to_0';yrs=62500.0
 land=np.asarray(z18[f'{pref}__land_support'],float)/yrs;temp=np.asarray(z18[f'{pref}__temperature_c'],float)/yrs;arid=np.asarray(z18[f'{pref}__aridity_index'],float)/yrs
 forage=sum(np.asarray(z18[f'{pref}__{f}'],float) for f in ('browse_forage','low_forage','wetland_forage'))/yrs
 q=np.quantile(forage[land>.2],.99) if np.any(land>.2) else np.quantile(forage,.99);forage=np.clip(forage/max(q,1e-12),0,1.5)
 return {'land':np.clip(land,0,1),'temp':temp,'arid':np.clip(arid,0,8),'forage':forage}

def _candidate_ecology(inp:dict[str,Any])->dict[str,dict[str,float]]:
 out={}
 for s in inp['candidates']:
  cs=inp['cby'][s];w=np.asarray([max(float(x['population_total']),1e-12) for x in cs]);w=w/w.sum();traits=np.asarray([x['legacy_ecological_trait_vector'] for x in cs],float)
  out[s]={'thermal_optimum':float(np.sum(w*traits[:,0])),'drought_tolerance':float(np.sum(w*traits[:,1])),'body_coordinate':float(np.sum(w*traits[:,2])),'generation_time':float(inp['lby'][s]['population_weighted_generation_time_proxy_years'])}
 return out

def _spatial_seeds(inp:dict[str,Any],s:str,n:int,rng:np.random.Generator)->tuple[np.ndarray,np.ndarray]:
 cs=inp['cby'][s];weights=np.asarray([max(float(x['population_total']),1e-12) for x in cs],float);weights/=weights.sum();rows=[];cols=[]
 for d in range(n):
  k=int(rng.choice(len(cs),p=weights));g=cs[k]['range_grid_summary'];r=float(g['population_weighted_row']);c=float(g['population_weighted_col'])
  r+=rng.normal(0,max(1,(g['occupied_row_minmax'][1]-g['occupied_row_minmax'][0])/12));c+=rng.normal(0,max(1,(g['occupied_col_minmax'][1]-g['occupied_col_minmax'][0])/12))
  rows.append(np.clip(r,0,89));cols.append(c%180)
 return np.asarray(rows),np.asarray(cols)

def _global_forcing(age_ka:float,e:int,seed:int)->tuple[float,float,float]:
 # Common-per-replicate orbital/millennial proxy. It downscales sealed exposure integrals, never replaces them as authority.
 phase=(seed+7919*e)%10000/10000*2*math.pi
 orbital=.58*math.sin(2*math.pi*age_ka/100+phase)+.32*math.sin(2*math.pi*age_ka/41+phase/3)+.10*math.sin(2*math.pi*age_ka/23+phase/7)
 glacial=.5+.5*math.sin(2*math.pi*(age_ka-18)/96+phase/5)
 temp_delta=-4.2*glacial+1.4*orbital
 arid_mult=np.clip(1.0+.30*glacial-.12*orbital,.65,1.55)
 corridor=np.clip(.58-.18*glacial+.18*orbital,.08,1.0)
 return float(temp_delta),float(arid_mult),float(corridor)

def _suitability(maps:dict[str,np.ndarray],r:float,c:float,eco:dict[str,float],td:float,am:float)->float:
 rr=int(np.clip(round(r),0,89));cc=int(round(c))%180
 land=float(maps['land'][rr,cc]);temp=float(maps['temp'][rr,cc])+td;arid=float(maps['arid'][rr,cc])*am;forage=float(maps['forage'][rr,cc])
 ts=math.exp(-((temp-eco['thermal_optimum'])/14.0)**2);tol=.45+2.4*eco['drought_tolerance'];ds=math.exp(-(max(0.0,arid-tol)/1.7)**2)
 return float(np.clip(.34*land+.24*ts+.16*ds+.26*np.clip(forage,0,1),0,1))

def _cha2_index(z20:Any,age_ka:float,r:float,c:float)->tuple[float,float,float]:
 if age_ka>14.9500001 or age_ka<10.9999999:return 0.0,0.0,0.0
 years=-int(round(age_ka*1000));ys=np.asarray(z20['years_before_book'],int);k=int(np.argmin(np.abs(ys-years)))
 rr=int(np.clip(round(r),0,89));cc=int(round(c))%180
 return float(z20['compound_flood_hazard_index'][k,rr,cc]),float(z20['hydrological_disruption_index'][k,rr,cc]),float(z20['raw_support_loss_fraction'][k,rr,cc])

def replay(inp:dict[str,Any],cfg:dict[str,Any])->dict[str,Any]:
 ages=build_time_axis();T=len(ages);n=EXPECTED_MEMBERS;nc=2;nd=MAX_DEMES;nv=len(STATE_NAMES);state=np.zeros((n,nc,T,nd,nv),dtype=np.float32);active=np.zeros((n,nc,T,nd),dtype=np.uint8)
 species_summary=np.zeros((n,nc,T,8),dtype=np.float32); # N, active demes, spread, diversity, integration, admixture, hazard, displacement
 maps1=_phase_maps(inp['z18'],1);maps2=_phase_maps(inp['z18'],2);eco=_candidate_ecology(inp);z20=inp['z20'];seed=int(cfg['seed'])
 var27=['effective_population','deme_count','ecological_breadth','cumulative_buffering','dispersal_capacity','developmental_investment','genetic_diversity_proxy','adaptive_integration'];vix={v:i for i,v in enumerate(var27)}
 for e in range(n):
  for j,s in enumerate(inp['candidates']):
   rng=np.random.default_rng(seed+10007*e+997*j);x0=inp['state200'][e,j];N0=max(500.0,float(x0[vix['effective_population']]));n0=int(np.clip(round(x0[vix['deme_count']]),2,nd));rows,cols=_spatial_seeds(inp,s,n0,rng);p=rng.dirichlet(np.full(n0,1.3))*N0
   curN=np.zeros(nd);curR=np.zeros(nd);curC=np.zeros(nd);div=np.zeros(nd);integ=np.zeros(nd);anc=np.full(nd,1.0 if j==0 else 0.0);curN[:n0]=p;curR[:n0]=rows;curC[:n0]=cols;div[:n0]=np.clip(float(x0[vix['genetic_diversity_proxy']]),.02,1);integ[:n0]=np.clip(float(x0[vix['adaptive_integration']]),0,1)
   for t,age in enumerate(ages):
    dt_kyr=(ages[t-1]-age) if t>0 else 0.0;maps=maps1 if age>62.5 else maps2;td,am,corr=_global_forcing(float(age),e,seed)
    if t>0:
     # local movement + demographic update
     for d in range(nd):
      if curN[d]<1:continue
      step=max(.4,min(2.3,.55+1.8*float(x0[vix['dispersal_capacity']])))*math.sqrt(max(dt_kyr,.05))
      suit0=_suitability(maps,curR[d],curC[d],eco[s],td,am);ang=rng.uniform(0,2*math.pi);mag=step*(.25+.75*(1-suit0));nr=np.clip(curR[d]+mag*math.sin(ang),0,89);nc=(curC[d]+mag*math.cos(ang))%180;suit1=_suitability(maps,nr,nc,eco[s],td,am)
      if suit1>=suit0 or rng.random()<.12:curR[d],curC[d],suit=nr,nc,suit1
      else:suit=suit0
      h,hd,loss=_cha2_index(z20,float(age),curR[d],curC[d]);haz=.55*h+.30*hd+.15*loss
      # conservative interpretation: hazard is an index, not flood depth. Effects are displacement/support shocks, not calibrated mortality.
      shock=np.clip(1.0-haz*(.018+.020*(1-float(x0[vix['cumulative_buffering']]))),.90,1.0);baseK=N0/max(n0,1)*(1.10+.95*suit)*(1+.55*float(x0[vix['ecological_breadth']]))
      r_kyr=.022+.030*float(x0[vix['developmental_investment']]);grow=math.exp(r_kyr*dt_kyr*(1-curN[d]/max(baseK,1)));curN[d]=max(0.0,curN[d]*grow*shock*math.exp(rng.normal(0,.018*math.sqrt(max(dt_kyr,.05)))))
      div[d]=np.clip(div[d]*(1-.0008*dt_kyr/max(math.sqrt(curN[d]/1000+1),1))+.00012*dt_kyr*corr,0.01,1);integ[d]=np.clip(integ[d]+.0014*dt_kyr*(suit-integ[d])+.0005*dt_kyr*float(x0[vix['developmental_investment']]),0,1)
      if haz>.12:
       # displacement one extra local move toward better neighboring suitability
       curR[d]=np.clip(curR[d]+np.sign(45-curR[d])*.35*step*haz,0,89);curC[d]=(curC[d]+rng.normal(0,.25*step*haz))%180
     # migration among demes of same lineage
     for a in range(nd):
      if curN[a]<10:continue
      for b in range(a+1,nd):
       if curN[b]<10:continue
       dc=abs(curC[a]-curC[b]);dc=min(dc,180-dc);dist=math.hypot(curR[a]-curR[b],dc);m=.012*dt_kyr*corr*math.exp(-dist/20)*float(x0[vix['dispersal_capacity']]);m=min(m,.08)
       if m>0:
        pool=curN[a]+curN[b];target=pool/2;curN[a]=(1-m)*curN[a]+m*target;curN[b]=(1-m)*curN[b]+m*target;aa=(anc[a]+anc[b])/2;anc[a]=(1-m)*anc[a]+m*aa;anc[b]=(1-m)*anc[b]+m*aa
     # extinction/colonization bookkeeping within fixed maximum deme slots
     for d in range(nd):
      if curN[d]<8:curN[d]=0
     active_idx=np.where(curN>=40)[0]
     empty=np.where(curN<1)[0]
     if len(active_idx)>0 and len(empty)>0 and np.sum(curN)>2500:
      src=int(active_idx[np.argmax(curN[active_idx])]);colon_prob=np.clip(.006*dt_kyr*corr*float(x0[vix['dispersal_capacity']]),0,.12)
      if curN[src]>900 and rng.random()<colon_prob:
       d=int(empty[0]);frac=.035;curN[d]=curN[src]*frac;curN[src]*=(1-frac);curR[d]=np.clip(curR[src]+rng.normal(0,4),0,89);curC[d]=(curC[src]+rng.normal(0,6))%180;div[d]=div[src]*.96;integ[d]=integ[src];anc[d]=anc[src]
    # persist deme state
    haznum=0.0;dispnum=0.0;tot=max(np.sum(curN),1e-12)
    for d in range(nd):
     suit=_suitability(maps,curR[d],curC[d],eco[s],td,am) if curN[d]>0 else 0.0;h,hd,loss=_cha2_index(z20,float(age),curR[d],curC[d]) if curN[d]>0 else (0,0,0);haz=.55*h+.30*hd+.15*loss;haznum+=curN[d]*haz;dispnum+=curN[d]*(1-math.exp(-2*haz))
     state[e,j,t,d]=[curN[d],curR[d],curC[d],suit,div[d],integ[d],anc[d]];active[e,j,t,d]=1 if curN[d]>=40 else 0
    ai=np.where(curN>=40)[0];spread=0.0
    if len(ai)>=2:
     rr=curR[ai];cc=curC[ai];spread=float(np.sqrt(np.var(rr)+np.var(cc)))
    w=curN/tot;own_anc=float(np.sum(w*(anc if j==0 else 1-anc)));species_summary[e,j,t]=[np.sum(curN),len(ai),spread,np.sum(w*div),np.sum(w*integ),1-own_anc,haznum/tot,dispnum/tot]
  # cross-lineage contact/admixture after each candidate update, applied to ancestry only at matching time state and propagated forward next step through cur arrays is intentionally NOT done here;
  # contact is summarized independently below from persisted positions to avoid asymmetric update ordering.
 # derive symmetric contact/admixture diagnostic from co-occurrence, not direct genetic replacement
 contact=np.zeros((n,T),dtype=np.float32);admx=np.zeros((n,T),dtype=np.float32)
 for e in range(n):
  cumulative=0.0
  for t in range(T):
   p0=state[e,0,t,:,0].astype(float);p1=state[e,1,t,:,0].astype(float);den=max(float(p0.sum()+p1.sum()),1e-12);m0=p0>=40;m1=p1>=40
   if np.any(m0) and np.any(m1):
    r0=state[e,0,t,m0,1].astype(float)[:,None];r1=state[e,1,t,m1,1].astype(float)[None,:];c0=state[e,0,t,m0,2].astype(float)[:,None];c1=state[e,1,t,m1,2].astype(float)[None,:];dc=np.abs(c0-c1);dc=np.minimum(dc,180-dc);dist=np.sqrt((r0-r1)**2+dc**2);weights=np.sqrt(p0[m0,None]*p1[None,m1]);num=float(np.sum(np.where(dist<10,weights*np.exp(-dist/5),0.0)))
   else:num=0.0
   c=np.clip(num/den,0,1);contact[e,t]=c;dt=(ages[t-1]-ages[t]) if t>0 else 0;cumulative=1-(1-cumulative)*math.exp(-.0035*c*dt);admx[e,t]=np.clip(cumulative,0,1)
 return {'age_ka':ages,'state':state,'active':active,'species_summary':species_summary,'contact_index':contact,'admixture_opportunity_cumulative':admx}

def summarize(inp:dict[str,Any],cfg:dict[str,Any],r:dict[str,Any])->dict[str,Any]:
 S=r['species_summary'];ages=r['age_ka'];c=inp['candidates'];q=cfg['qualification'];hazmask=(ages<=14.95)&(ages>=11.0);out=[]
 for j,s in enumerate(c):
  final=S[:,j,-1];N=final[:,0];dem=final[:,1];spread=final[:,2];div=final[:,3];integ=final[:,4];surv=N>=q['survival_population_min'];haz=np.max(S[:,j,hazmask,6],axis=1);disp=np.max(S[:,j,hazmask,7],axis=1);pre_idx=int(np.argmin(np.abs(ages-15.0)));post_idx=int(np.argmin(np.abs(ages-10.75)));ret=np.divide(S[:,j,post_idx,0],np.maximum(S[:,j,pre_idx,0],1),out=np.zeros_like(N),where=S[:,j,pre_idx,0]>0)
  metrics={'species_id':s,'survival_frequency':float(np.mean(surv)),'final_population_median':float(np.median(N)),'final_deme_median':float(np.median(dem)),'final_spatial_spread_median':float(np.median(spread)),'final_diversity_median':float(np.median(div)),'final_adaptive_integration_median':float(np.median(integ)),'cha2_peak_population_weighted_hazard_median':float(np.median(haz)),'cha2_peak_displacement_pressure_median':float(np.median(disp)),'cha2_population_retention_median':float(np.median(ret))}
  gates={'survival':metrics['survival_frequency']>=q['survival_frequency_min'],'population':metrics['final_population_median']>=q['final_population_median_min'],'demes':metrics['final_deme_median']>=q['final_deme_median_min'],'diversity':metrics['final_diversity_median']>=q['final_diversity_median_min'],'integration':metrics['final_adaptive_integration_median']>=q['final_adaptive_integration_median_min'],'cha2_retention':metrics['cha2_population_retention_median']>=q['cha2_population_retention_median_min']}
  metrics['baseline_gate_pass']=gates;metrics['baseline_qualified']=all(gates.values());out.append(metrics)
 # precommitted sensitivity: baseline, leave-one-gate-out, stricter/looser demography, no-CHA2 gate, and regime-free bootstrap-like even/odd ensemble halves
 gate_names=['survival','population','demes','diversity','integration','cha2_retention'];variants=[]
 variants.append({'variant':'BASELINE','qualified':[x['species_id'] for x in out if x['baseline_qualified']]})
 for g in gate_names:variants.append({'variant':f'LEAVE_ONE_GATE_OUT::{g}','qualified':[x['species_id'] for x in out if all(v for k,v in x['baseline_gate_pass'].items() if k!=g)]})
 for label,mult in [('DEMOGRAPHY_LOOSER',.85),('DEMOGRAPHY_STRICTER',1.15)]:
  qq=[]
  for x in out:
   g=x['baseline_gate_pass'].copy();g['population']=x['final_population_median']>=q['final_population_median_min']*mult;g['demes']=x['final_deme_median']>=max(2,q['final_deme_median_min']+(1 if mult>1 else -1));
   if all(g.values()):qq.append(x['species_id'])
  variants.append({'variant':label,'qualified':qq})
 # halves use same gates recomputed from raw summaries
 for label,mask in [('ENSEMBLE_HALF_EVEN',np.arange(EXPECTED_MEMBERS)%2==0),('ENSEMBLE_HALF_ODD',np.arange(EXPECTED_MEMBERS)%2==1)]:
  qq=[]
  for j,s in enumerate(c):
   f=S[mask,j,-1];pre=S[mask,j,int(np.argmin(np.abs(ages-15.0))),0];post=S[mask,j,int(np.argmin(np.abs(ages-10.75))),0];ret=np.median(post/np.maximum(pre,1));gg=[np.mean(f[:,0]>=q['survival_population_min'])>=q['survival_frequency_min'],np.median(f[:,0])>=q['final_population_median_min'],np.median(f[:,1])>=q['final_deme_median_min'],np.median(f[:,3])>=q['final_diversity_median_min'],np.median(f[:,4])>=q['final_adaptive_integration_median_min'],ret>=q['cha2_population_retention_median_min']]
   if all(gg):qq.append(s)
  variants.append({'variant':label,'qualified':qq})
 freq={s:sum(s in v['qualified'] for v in variants)/len(variants) for s in c}
 for x in out:x['sensitivity_qualification_frequency']=float(freq[x['species_id']]);x['human_0ka_checkpoint_qualified']=bool(x['baseline_qualified'] and freq[x['species_id']]>=q['sensitivity_frequency_min'])
 cohort=[x['species_id'] for x in out if x['human_0ka_checkpoint_qualified']]
 # unique identity is only allowed if one lineage alone qualifies robustly. No head-to-head score can override a two-lineage cohort.
 unique=cohort[0] if len(cohort)==1 else None
 return {'candidate_metrics':out,'sensitivity':variants,'frequency':freq,'qualified_cohort':cohort,'unique_human_identity':unique,'contact_final_median':float(np.median(r['contact_index'][:,-1])),'admixture_opportunity_final_median':float(np.median(r['admixture_opportunity_cumulative'][:,-1]))}

def audit_result(inp,cfg,r,s):
 checks=[]
 def ck(n,x,d=None):checks.append({'name':n,'pass':bool(x),'detail':d})
 ages=r['age_ka'];S=r['species_summary'];state=r['state'];z20=inp['z20']
 ck('parent_r327_sealed',inp['a327'].get('status')==PARENT_PASS and inp['a327'].get('checks_passed')==28)
 ck('two_candidates_exact',inp['candidates']==['RPT_010_D02','RPT_009_D02'],inp['candidates'])
 ck('time_axis_200ka_to_0',abs(float(ages[0])-200)<1e-12 and abs(float(ages[-1]))<1e-12)
 h=ages[(ages<=14.95)&(ages>=11.0)];ck('cha2_axis_exact_80_states',len(h)==80 and np.allclose(np.diff(h),-.05),[len(h),float(h[0]),float(h[-1])])
 ck('state_geometry',state.shape==(EXPECTED_MEMBERS,2,len(ages),MAX_DEMES,7),state.shape)
 ck('summary_geometry',S.shape==(EXPECTED_MEMBERS,2,len(ages),8),S.shape)
 ck('all_numeric_finite',np.isfinite(state).all() and np.isfinite(S).all())
 ck('population_nonnegative',np.min(state[...,0])>=0)
 ck('grid_bounds',np.min(state[...,1])>=0 and np.max(state[...,1])<=89 and np.min(state[...,2])>=0 and np.max(state[...,2])<180)
 ck('bounded_latent_indices',np.min(state[...,3:])>=0 and np.max(state[...,3:])<=1)
 ck('r318_exact_hashes',all(sha256_file(inp['r318'][n])==h for n,h in R318_HASHES.items()))
 ck('r320_exact_hashes',all(sha256_file(inp['r320'][n])==h for n,h in R320_HASHES.items()))
 ck('cha2_direct_field_geometry',z20['compound_flood_hazard_index'].shape==(80,90,180))
 ck('forcing_semantics_phase_constrained',cfg['recent_forcing_semantics']=='R318_SEALED_PHASE_INTEGRAL_CONSTRAINED_DOWNSCALING_WITH_DIRECT_R320_CHA2_50Y_HAZARD')
 ck('no_false_direct_r318_timeseries_claim',cfg['r318_is_direct_high_resolution_timeseries'] is False)
 ck('no_human_similarity_target',cfg['human_similarity_target'] is False)
 ck('deep_off',cfg['deep_biological_coupling'] is False)
 ck('parents_immutable',all(cfg[k] is False for k in ('h0_mutation','cha2_mutation','r323_mutation','r324_mutation','r325_mutation','r326_mutation','r327_mutation')))
 ck('no_direct_cb_selection',cfg['h3_cb_direct_selection'] is False)
 ck('two_candidate_metrics',len(s['candidate_metrics'])==2 and {x['species_id'] for x in s['candidate_metrics']}==set(inp['candidates']))
 ck('sensitivity_11_variants',len(s['sensitivity'])==11,len(s['sensitivity']))
 ck('human_0ka_subset',set(s['qualified_cohort']).issubset(set(inp['candidates'])),s['qualified_cohort'])
 ck('unique_identity_rule',s['unique_human_identity'] is None if len(s['qualified_cohort'])!=1 else s['unique_human_identity']==s['qualified_cohort'][0])
 ck('cha2_hazard_is_diagnostic_index',cfg['cha2_hazard_semantics']=='DIAGNOSTIC_RANKING_NOT_FLOOD_DEPTH')
 ck('admixture_not_replacement_assumption',cfg['contact_semantics']=='SYMMETRIC_ADMIXTURE_OPPORTUNITY_DIAGNOSTIC_NO_FORCED_REPLACEMENT')
 ck('evidence_multisource',len(EVIDENCE)>=5)
 ck('final_population_exists',all(x['final_population_median']>0 for x in s['candidate_metrics']))
 ck('checkpoint_not_required_unique',cfg['human_0ka_semantics']=='ROBUST_POPULATION_CHECKPOINT_COHORT_UNIQUE_IDENTITY_ONLY_IF_SINGLE_LINEAGE_QUALIFIES')
 failed=[x for x in checks if not x['pass']]
 return {'stage':STAGE,'status':CANDIDATE_PASS if not failed else 'FAIL_R328_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'summary':{'candidate_lineages':2,'ensemble_members':EXPECTED_MEMBERS,'time_states':len(ages),'human_0ka_candidate_count':len(s['qualified_cohort']),'human_0ka_candidate_cohort':s['qualified_cohort'],'unique_human_identity_materialized':s['unique_human_identity'] is not None,'unique_human_identity':s['unique_human_identity'],'cha2_direct_50y_consumed':True,'human_similarity_target':False,'deep_biological_coupling':False},'checks':checks}

def run_stage(inp,cfg):
 r=replay(inp,cfg);s=summarize(inp,cfg,r);return r,s

def build_outputs(inp,cfg,r,s,out:Path):
 out.mkdir(parents=True,exist_ok=True)
 authority={'stage':STAGE,'status':'HIGH_RESOLUTION_200KA_TO_0_REPLAY_AUTHORITY','parent':PARENT_PASS,'candidate_cohort':inp['candidates'],'time_resolution':{'200_to_125ka_kyr':2.5,'124_to_20ka_kyr':1.0,'19p75_to_15ka_kyr':.25,'cha2_14p95_to_11ka_kyr':.05,'10p75_to_0ka_kyr':.25},'spatial_state':'MAX_6_DEMES_PER_LINEAGE_ON_90x180_GRID','recent_forcing_semantics':cfg['recent_forcing_semantics'],'r318_authority':{n:{'path':str(inp['r318'][n]),'sha256':R318_HASHES[n]} for n in R318_HASHES},'r320_authority':{n:{'path':str(inp['r320'][n]),'sha256':R320_HASHES[n]} for n in R320_HASHES},'cha2_semantics':cfg['cha2_hazard_semantics'],'contact_semantics':cfg['contact_semantics'],'spatial_prior_semantics':'R321_PRESENT_LINEAGE_RANGE_SUMMARIES_USED_ONLY_AS_SEALED_LINEAGE_HABITAT_COORDINATE_ENVELOPE_NOT_AS_OBSERVED_200KA_HUMAN_LOCATION','evidence_basis':EVIDENCE,'human_similarity_target':False,'deep_biological_coupling':False,'h3_cb_direct_selection':False}
 write_json(out/'R3_28_HIGH_RESOLUTION_REPLAY_AUTHORITY.json',authority)
 write_json(out/'R3_28_CANDIDATE_POPULATION_OUTCOMES.json',{'stage':STAGE,'status':'HIGH_RESOLUTION_CANDIDATE_OUTCOMES','candidates':s['candidate_metrics'],'contact_final_median':s['contact_final_median'],'admixture_opportunity_final_median':s['admixture_opportunity_final_median']})
 write_json(out/'R3_28_SENSITIVITY_AND_ROBUSTNESS.json',{'stage':STAGE,'status':'HIGH_RESOLUTION_SENSITIVITY_COMPLETE','variant_count':len(s['sensitivity']),'qualification_frequency':s['frequency'],'variants':s['sensitivity']})
 write_json(out/'R3_28_HUMAN_0KA_CHECKPOINT.json',{'stage':STAGE,'status':'HUMAN_0KA_POPULATION_CHECKPOINT','age_ka':0.0,'candidate_count':len(s['qualified_cohort']),'candidate_cohort':s['qualified_cohort'],'unique_human_identity_materialized':s['unique_human_identity'] is not None,'unique_human_identity':s['unique_human_identity'],'interpretation':'ROBUST_HIGH_RESOLUTION_POPULATION_COHORT_AT_0KA;_UNIQUE_IDENTITY_ONLY_IF_SINGLE_LINEAGE_QUALIFIES'})
 # selected compact snapshots for downstream mapping plus full species trajectories
 snap_ages=np.asarray([200,125,100,75,50,30,20,15,14,13,12,11,10,5,0],float);snap_idx=np.asarray([int(np.argmin(np.abs(r['age_ka']-a))) for a in snap_ages])
 cha_mask=(r['age_ka']<=14.95)&(r['age_ka']>=11.0)
 np.savez_compressed(out/'R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz',candidate_ids=np.asarray(inp['candidates']),parent_member_indices=np.asarray(inp['parent_member_indices']),age_ka=r['age_ka'],state_variable_names=np.asarray(STATE_NAMES),species_summary_variable_names=np.asarray(['population_proxy','active_demes','spatial_spread','genetic_diversity_proxy','adaptive_integration','admixture_fraction_proxy','cha2_population_weighted_hazard','cha2_displacement_pressure']),species_summary=r['species_summary'],contact_index=r['contact_index'],admixture_opportunity_cumulative=r['admixture_opportunity_cumulative'],snapshot_age_ka=snap_ages,snapshot_deme_state=r['state'][:,:,snap_idx,:,:],snapshot_active=r['active'][:,:,snap_idx,:],cha2_age_ka=r['age_ka'][cha_mask],cha2_deme_state=r['state'][:,:,cha_mask,:,:],cha2_active=r['active'][:,:,cha_mask,:])
 audit=audit_result(inp,cfg,r,s);write_json(out/'R3_28_INTEGRATED_AUDIT.json',audit)
 (out/'R3_28_AUDIT.md').write_text(f"# R3.28 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n- HUMAN_0KA cohort: `{', '.join(s['qualified_cohort']) if s['qualified_cohort'] else 'NONE'}`\n- Unique identity: `{s['unique_human_identity']}`\n- CHA-2: direct 50-y hazard fields consumed.\n",encoding='utf-8')

def write_manifest(out:Path,status:str):
 files={}
 for p in sorted(out.iterdir()):
  if p.is_file() and p.name!='R3_28_OUTPUT_MANIFEST.json':files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_28_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
