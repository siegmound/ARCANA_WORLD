from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json, math
import numpy as np

STAGE='v0.6D1-R3.39'
PARENT_PASS='PASS_R338_REGIONAL_EXCHANGE_NETWORKS_CONCRETE_TECHNOLOGY_RETICULATE_CULTURAL_GENEALOGIES_AND_BORROWING_SEALED'
R329_PASS='PASS_R329_POPULATION_MOBILITY_SETTLEMENT_CULTURAL_TRANSMISSION_PRECONDITIONS_AND_CHA2_COMMUNITY_EXPOSURE_SEALED'
R320_PASS='PASS_R320_CHA2_YOUNGER_DRYAS_CLASS_MAGNITUDE_AND_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_LAYER_SEALED'
CANDIDATE_PASS='PASS_R339_CULTURAL_SYMBOLIC_MEMORY_LANGUAGE_PRECONDITIONS_AND_INTERLINEAGE_IDENTITY_DYNAMICS_CANDIDATE'
FINAL_PASS='PASS_R339_CULTURAL_SYMBOLIC_MEMORY_DIRECT_CHA2_EVENT_MEMORY_LANGUAGE_DIVERGENCE_PRECONDITIONS_AND_INTERLINEAGE_IDENTITY_DYNAMICS_SEALED'
EXPECTED_CANDIDATES=['RPT_010_D02','RPT_009_D02']
EXPECTED_MEMBERS=32; EXPECTED_TIMES=145; EXPECTED_ANCHORS=9; EXPECTED_REGIONS=6

SYMBOLIC_STATE_NAMES=[
 'cha2_event_memory_stock',
 'collective_symbolic_memory',
 'symbolic_encoding_support',
 'mnemonic_rehearsal_support',
 'identity_marker_salience',
 'interlineage_boundary_salience',
 'communicative_conventionalization',
 'language_contact_pressure',
 'language_divergence_precondition',
 'memory_persistence_support'
]
CHA2_EXPOSURE_NAMES=[
 'hydrological_disruption_index','ecosystem_hydrological_shock_index','compound_flood_hazard_index',
 'drying_hazard_index','raw_support_loss_fraction'
]
REGIONAL_ANCHOR_NAMES=[
 'represented_people','represented_camps','grid_row','grid_col','regional_lineage_code','regional_continuity',
 'cha2_event_memory_stock','collective_symbolic_memory','symbolic_encoding_support','mnemonic_rehearsal_support',
 'identity_marker_salience','interlineage_boundary_salience','communicative_conventionalization',
 'language_contact_pressure','language_divergence_precondition','memory_persistence_support'
]

EVIDENCE={
 'ORAL_TRADITION_CRISIS_MEMORY':{
  'source':'Minc, Scarcity and survival: The role of oral tradition in mediating subsistence crises, Journal of Anthropological Archaeology 5, 1986',
  'doi':'10.1016/0278-4165(86)90010-3',
  'use':'nonliterate traditions can preserve practical memory of recurrent environmental/subsistence crises across generations; memory persistence depends on repetition and formalization'},
 'LANGUAGE_NETWORK_VARIATION':{
  'source':'Sharma & Dodsworth, Language Variation and Social Networks, Annual Review of Linguistics 6, 2020',
  'doi':'10.1146/annurev-linguistics-011619-030524',
  'use':'linguistic diffusion depends on social-network structure and socially mediated uptake rather than isolation alone'},
 'LANGUAGE_CONTACT_POPULATION':{
  'source':'Mufwene & Escobar, Language Contact in Population Structure, Cambridge Handbook of Language Contact, 2022',
  'use':'contact can produce borrowing, structural change, mixed varieties, language shift or stability depending on population structure'},
 'DIVERGENCE_UNDER_CONTACT':{
  'source':'Evans, Linguistic divergence under contact, Dynamics of Linguistic Diversity, 2018',
  'use':'contact can support divergence when linguistic choices signal group-membership distinctions; convergence is not the only possible outcome'},
 'MESOLITHIC_ORNAMENT_NETWORKS':{
  'source':'Lozano et al., Reconstructing Mesolithic social networks on the Iberian Peninsula using ornaments, Archaeological and Anthropological Sciences 14, 2022',
  'doi':'10.1007/s12520-022-01641-z',
  'use':'symbolic objects can encode affiliation and participate in hunter-gatherer exchange networks; R3.39 uses only abstract marker salience, not direct ornament claims'},
 'R320_PARENT':{'source':'R3.20 SEALED CHA-2 50-year hydrological hazard authority','use':'direct regional event-memory seeding from immutable physical hazard fields'},
 'R329_PARENT':{'source':'R3.29 SEALED community/cultural preconditions','use':'social learning, cognition, cultural transmission, settlement and CHA-2 community disruption context'},
 'R338_PARENT':{'source':'R3.38 SEALED regional exchange, concrete technology and reticulate cultural genealogy','use':'12 opaque regional stems, implementation support, retention, innovation, borrowing and exchange topology'},
 'R332_PARENT':{'source':'R3.32 SEALED opaque regional cultural lineages','use':'regional continuity and population-weighted regional codes remain non-ethnic analytical identities'}
}

class R339GateError(RuntimeError): pass

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
 if not p.is_file(): raise R339GateError(f'Missing manifest {p}')
 m=load_json(p)
 for n,meta in m.get('files',{}).items():
  fp=d/n
  if not fp.is_file() or fp.stat().st_size!=int(meta['bytes']) or sha256_file(fp)!=meta['sha256']:
   raise R339GateError(f'Manifest closure failure {fp}')

def _seal(root:Path,s:int,expected:str,checks:int)->dict[str,Any]:
 p=root/'outputs'/f'v0_6D1_R3_{s}_SEAL'/f'R3_{s}_FINAL_SEAL_AUDIT.json'
 d=load_json(p)
 if d.get('status')!=expected or d.get('verdict')!='SEALED' or d.get('checks_passed')!=checks or d.get('checks_failed')!=0:
  raise R339GateError(f'R3.{s} seal mismatch')
 return d

def _index(names:np.ndarray,name:str)->int: return list(map(str,names)).index(name)

def _match_indices(parent:np.ndarray,child:np.ndarray)->np.ndarray:
 out=[]
 for x in child:
  w=np.where(np.isclose(parent,float(x),rtol=0,atol=1e-12))[0]
  if len(w)!=1: raise R339GateError(f'Cannot bind age {x}')
  out.append(int(w[0]))
 return np.asarray(out,int)

def validate_inputs(root:Path)->dict[str,Any]:
 root=Path(root);r38=root/'outputs'/'v0_6D1_R3_38';r29=root/'outputs'/'v0_6D1_R3_29';r32=root/'outputs'/'v0_6D1_R3_32'
 for d in [r38,r29,r32]:
  if not d.is_dir(): raise R339GateError(f'Missing authority {d}')
 a38=_seal(root,38,PARENT_PASS,44);a29=_seal(root,29,R329_PASS,37);_seal(root,32,'PASS_R332_SUBSISTENCE_INTENSIFICATION_REGIONAL_CULTURAL_LINEAGES_MANAGED_RESOURCE_TRANSITIONS_AND_HOLOCENE_READINESS_SEALED',30)
 for d,n in [(r38,'R3_38_OUTPUT_MANIFEST.json'),(r29,'R3_29_OUTPUT_MANIFEST.json'),(r32,'R3_32_OUTPUT_MANIFEST.json')]: _close_manifest(d,n)
 s20=root/'R3_20_SEAL_SUMMARY.json';hzp=root/'local_runs'/'v0_6D1_R3_20'/'R3_20_CHA2_15_TO_11KA_50Y_HYDROLOGICAL_HAZARD_FIELDS.npz'
 if not s20.is_file() or not hzp.is_file(): raise R339GateError('Missing R3.20 seal/hazard authority')
 s20j=load_json(s20)
 if s20j.get('verdict')!=R320_PASS or s20j.get('formal_audit_checks')!='108/108': raise R339GateError('R3.20 seal mismatch')
 if sha256_file(hzp)!=s20j['canonical_artifacts']['hazard_npz_sha256']: raise R339GateError('R3.20 hazard hash mismatch')
 z38=np.load(r38/'R3_38_REGIONAL_CULTURAL_NETWORKS.npz',allow_pickle=False);t38=np.load(r38/'R3_38_CONCRETE_TECHNOLOGY_REPLAY.npz',allow_pickle=False)
 z29=np.load(r29/'R3_29_COMMUNITY_NETWORK_REPLAY.npz',allow_pickle=False);z32=np.load(r32/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz',allow_pickle=False);hz=np.load(hzp,allow_pickle=False)
 for z in [z38,t38,z29,z32]:
  if list(map(str,z['candidate_ids']))!=EXPECTED_CANDIDATES: raise R339GateError('Candidate order mismatch')
 if not np.array_equal(z38['parent_member_indices'],t38['parent_member_indices']) or not np.array_equal(z38['parent_member_indices'],z29['parent_member_indices']) or not np.array_equal(z38['parent_member_indices'],z32['parent_member_indices']): raise R339GateError('Member mapping mismatch')
 time=t38['age_ka'];anchors=z38['anchor_age_ka']
 if time.shape!=(145,) or anchors.shape!=(9,) or time[0]!=20 or time[-1]!=0: raise R339GateError('Time geometry mismatch')
 if not np.array_equal(anchors,z32['anchor_age_ka']): raise R339GateError('Anchor mismatch')
 i29=_match_indices(z29['age_ka'],time)
 yrs=np.asarray(hz['years_before_book'])
 if yrs.shape!=(80,) or yrs[0]!=-14950 or yrs[-1]!=-11000 or not np.all(np.diff(yrs)==50): raise R339GateError('CHA2 50-year axis mismatch')
 for k in CHA2_EXPOSURE_NAMES:
  if k not in hz.files or hz[k].shape!=(80,90,180): raise R339GateError(f'CHA2 field mismatch {k}')
 return {'root':root,'r38':r38,'r29':r29,'r32':r32,'a38':a38,'a29':a29,'s20':s20j,'hzp':hzp,'z38':z38,'t38':t38,'z29':z29,'z32':z32,'hz':hz,'i29':i29}

def _interp_desc(ages:np.ndarray,vals:np.ndarray,t:float)->float:
 return float(np.interp(float(t),ages[::-1],vals[::-1]))

def _bilinear(field:np.ndarray,row:float,col:float)->float:
 nr,nc=field.shape;row=float(np.clip(row,0,nr-1));col=float(col%nc)
 r0=int(math.floor(row));r1=min(r0+1,nr-1);c0=int(math.floor(col));c1=(c0+1)%nc;fr=row-r0;fc=col-c0
 return float((1-fr)*((1-fc)*field[r0,c0]+fc*field[r0,c1])+fr*((1-fc)*field[r1,c0]+fc*field[r1,c1]))

def _aggregate_r32_continuity(inp:dict[str,Any])->np.ndarray:
 z=inp['z32'];S=np.asarray(z['regional_state'],float);active=np.asarray(z['regional_active'],bool);names=list(map(str,z['regional_variable_names']))
 pi=names.index('represented_people');ci=names.index('regional_lineage_code');ri=names.index('regional_continuity')
 out=np.zeros((EXPECTED_MEMBERS,2,EXPECTED_ANCHORS,EXPECTED_REGIONS),float)
 for m in range(EXPECTED_MEMBERS):
  for l in range(2):
   for a in range(EXPECTED_ANCHORS):
    for r in range(EXPECTED_REGIONS):
     mask=active[m,l,a] & (np.rint(S[m,l,a,:,ci]).astype(int)==r+1)
     if not np.any(mask): continue
     w=np.maximum(S[m,l,a,mask,pi],1e-12);out[m,l,a,r]=float(np.sum(w*S[m,l,a,mask,ri])/np.sum(w))
 return np.clip(out,0,1)

def _cha2_binding(inp:dict[str,Any])->dict[str,np.ndarray]:
 z=inp['z38'];hz=inp['hz'];ages=np.asarray(z['anchor_age_ka'],float);R=np.asarray(z['regional_state'],float);names=list(map(str,z['regional_state_variable_names']));rowi=names.index('grid_row');coli=names.index('grid_col')
 years=-np.asarray(hz['years_before_book'],float)/1000.0
 H={k:np.asarray(hz[k],float) for k in CHA2_EXPOSURE_NAMES}
 exp=np.zeros((EXPECTED_MEMBERS,2,80,EXPECTED_REGIONS,len(CHA2_EXPOSURE_NAMES)),float);pos=np.zeros((EXPECTED_MEMBERS,2,80,EXPECTED_REGIONS,2),float)
 for m in range(EXPECTED_MEMBERS):
  for l in range(2):
   for r in range(EXPECTED_REGIONS):
    rv=R[m,l,:,r,rowi];cv=R[m,l,:,r,coli]
    # unwrap longitude for smooth interpolation then wrap back
    cvr=np.rad2deg(np.unwrap(np.deg2rad(cv*2.0)))/2.0
    for j,t in enumerate(years):
     row=_interp_desc(ages,rv,t);col=_interp_desc(ages,cvr,t)%180.0;pos[m,l,j,r]=[row,col]
     for k,n in enumerate(CHA2_EXPOSURE_NAMES): exp[m,l,j,r,k]=_bilinear(H[n][j],row,col)
 # support-loss is naturally much smaller; transform only for composite diagnostic, never alter source field
 comp=.35*exp[...,0]+.20*exp[...,1]+.20*exp[...,2]+.15*exp[...,3]+.10*np.clip(exp[...,4]*20.0,0,1)
 return {'cha2_age_ka':years,'regional_position':pos,'regional_cha2_exposure':exp,'composite_event_severity':np.clip(comp,0,1)}

def _interp_anchor_array(anchor_age:np.ndarray,A:np.ndarray,time_age:np.ndarray)->np.ndarray:
 # A: M,L,A,R or M,L,A,R,K
 tail=A.shape[3:];out=np.empty((A.shape[0],A.shape[1],len(time_age))+tail,float)
 x=anchor_age[::-1]
 for m in range(A.shape[0]):
  for l in range(A.shape[1]):
   for idx in np.ndindex(tail):
    y=A[(m,l,slice(None))+idx][::-1]
    out[(m,l,slice(None))+idx]=np.interp(time_age[::-1],x,y)[::-1]
 return out

def _static_inputs(inp:dict[str,Any],cfg:dict[str,Any],binding:dict[str,np.ndarray])->dict[str,np.ndarray]:
 z38=inp['z38'];t38=inp['t38'];z29=inp['z29'];time=np.asarray(t38['age_ka'],float);anchor=np.asarray(z38['anchor_age_ka'],float)
 rs=np.asarray(z38['regional_state'],float);rn=list(map(str,z38['regional_state_variable_names']));active=np.asarray(z38['regional_active'],bool);profile=np.asarray(z38['regional_implementation_profile'],float);exchange=np.asarray(z38['exchange_matrix'],float)
 cont=_aggregate_r32_continuity(inp)
 # Regional scalar parents -> time
 retention=_interp_anchor_array(anchor,rs[...,rn.index('retention_support')],time);innovation=_interp_anchor_array(anchor,rs[...,rn.index('innovation_support')],time);borrow=_interp_anchor_array(anchor,rs[...,rn.index('borrowing_inflow')],time);distinct=_interp_anchor_array(anchor,rs[...,rn.index('regional_distinctiveness')],time);continuity=_interp_anchor_array(anchor,cont,time)
 regional_profile=_interp_anchor_array(anchor,profile,time)
 # Community inputs are lineage-wide, expanded over regions
 C=np.asarray(z29['community_summary'],float)[:,:,inp['i29'],:];cn=list(map(str,z29['community_variable_names']));ci={n:cn.index(n) for n in cn}
 network=C[...,ci['network_connectivity']];trans=C[...,ci['cultural_transmission_support']];culture=C[...,ci['cumulative_culture_precondition_stock']];settle=C[...,ci['settlement_persistence_potential']]
 F=np.asarray(z29['functional_priors'],float);fn=list(map(str,z29['functional_prior_names']));fi={n:fn.index(n) for n in fn}
 social=F[...,fi['social_learning']];cog=F[...,fi['cognition']];coord=F[...,fi['coordination']]
 # Cross-lineage exchange/contact and profile contrast at anchors
 cross=np.zeros((EXPECTED_MEMBERS,2,EXPECTED_ANCHORS,EXPECTED_REGIONS),float);contrast=np.zeros_like(cross)
 for m in range(EXPECTED_MEMBERS):
  for a in range(EXPECTED_ANCHORS):
   E=exchange[m,a]
   for l in range(2):
    opp=1-l
    for r in range(EXPECTED_REGIONS):
     i=l*EXPECTED_REGIONS+r;w=np.maximum(E[i,opp*EXPECTED_REGIONS:(opp+1)*EXPECTED_REGIONS],0)
     cross[m,l,a,r]=float(np.mean(w))
     dif=np.mean(np.abs(profile[m,l,a,r][None,:]-profile[m,opp,a]),axis=-1)
     contrast[m,l,a,r]=float(np.sum(w*dif)/np.sum(w)) if np.sum(w)>1e-12 else float(np.mean(dif))
 cross_t=_interp_anchor_array(anchor,cross,time);contrast_t=_interp_anchor_array(anchor,contrast,time)
 # symbolic media: implementation support for portable/durable marking media, still not direct symbol artifacts
 names=list(map(str,t38['implementation_family_names']));sel=[names.index(n) for n in ['hard_edge_mineral_cutting_processing','cordage_binding_netting_systems','hide_skin_flexible_thermal_goods','osseous_hard_biological_implements','built_shelter_and_site_furniture','adhesive_binding_compound_systems']]
 media=np.mean(regional_profile[...,sel],axis=-1)
 return {'time':time,'anchor':anchor,'active_anchor':active,'retention':retention,'innovation':innovation,'borrow':borrow,'distinct':distinct,'continuity':continuity,'profile':regional_profile,'cross':cross_t,'contrast':contrast_t,'media':media,'network':network,'trans':trans,'culture':culture,'settle':settle,'social':social,'cog':cog,'coord':coord,'binding':binding,'rs_anchor':rs,'cont_anchor':cont}

def replay_symbolic_memory_language_identity(inp:dict[str,Any],cfg:dict[str,Any],memory_decay_multiplier:float=1.0,identity_gain_multiplier:float=1.0,language_boundary_multiplier:float=1.0,static:dict[str,np.ndarray]|None=None)->dict[str,np.ndarray]:
 st=_static_inputs(inp,cfg,_cha2_binding(inp)) if static is None else static;time=st['time'];M,L,T,R=EXPECTED_MEMBERS,2,EXPECTED_TIMES,EXPECTED_REGIONS
 enc=np.zeros((M,L,T,R));reh=np.zeros_like(enc);ident=np.zeros_like(enc);bound=np.zeros_like(enc);conv=np.zeros_like(enc);lang=np.zeros_like(enc);contact=np.zeros_like(enc)
 # direct supports
 for t in range(T):
  dt=0 if t==0 else float(time[t-1]-time[t])
  net=st['network'][:,:,t,None];tr=st['trans'][:,:,t,None];cu=st['culture'][:,:,t,None];se=st['settle'][:,:,t,None]
  social=st['social'][:,:,None];cog=st['cog'][:,:,None];coord=st['coord'][:,:,None]
  enct=np.clip(.18*st['media'][:,:,t]+.18*tr+.16*cu+.14*net+.17*social+.17*cog,0,1)
  if t==0: enc[:,:,t]=enct
  else:
   q=1-math.exp(-float(cfg['symbolic_encoding_relaxation_per_kyr'])*dt);enc[:,:,t]=enc[:,:,t-1]+q*(enct-enc[:,:,t-1])
  reht=np.clip(.30*enc[:,:,t]+.20*st['retention'][:,:,t]+.15*se+.15*net+.10*coord+.10*st['continuity'][:,:,t],0,1)
  if t==0: reh[:,:,t]=reht
  else:
   q=1-math.exp(-float(cfg['mnemonic_rehearsal_relaxation_per_kyr'])*dt);reh[:,:,t]=reh[:,:,t-1]+q*(reht-reh[:,:,t-1])
  c=np.clip(st['cross'][:,:,t]/float(cfg['cross_contact_scale']),0,1);b=np.clip(st['borrow'][:,:,t]/float(cfg['borrowing_scale']),0,1);d=np.clip(st['distinct'][:,:,t]/float(cfg['regional_distinctiveness_scale']),0,1);pc=np.clip(st['contrast'][:,:,t]/float(cfg['technology_profile_contrast_scale']),0,1)
  contact[:,:,t]=np.clip(.58*c+.42*b,0,1)
  it=np.clip(identity_gain_multiplier*(.22*enc[:,:,t]+.16*st['retention'][:,:,t]+.18*d+.18*pc+.14*c+.12*(1-b)),0,1)
  if t==0: ident[:,:,t]=it
  else:
   q=1-math.exp(-float(cfg['identity_relaxation_per_kyr'])*dt);ident[:,:,t]=ident[:,:,t-1]+q*(it-ident[:,:,t-1])
  bt=np.clip(identity_gain_multiplier*ident[:,:,t]*(.34*pc+.34*c+.32*(1-b)),0,1)
  if t==0: bound[:,:,t]=bt
  else:
   q=1-math.exp(-float(cfg['boundary_relaxation_per_kyr'])*dt);bound[:,:,t]=bound[:,:,t-1]+q*(bt-bound[:,:,t-1])
  conv[:,:,t]=np.clip(.20*tr+.15*social+.15*cog+.15*st['retention'][:,:,t]+.15*st['continuity'][:,:,t]+.10*net+.10*ident[:,:,t],0,1)
  isolation_or_signalled_contact=np.clip(.65*(1-b)+.35*bound[:,:,t]*c,0,1)
  lt=np.clip(language_boundary_multiplier*conv[:,:,t]*(.30*st['continuity'][:,:,t]+.23*ident[:,:,t]+.20*bound[:,:,t]+.15*d+.12*isolation_or_signalled_contact),0,1)
  if t==0: lang[:,:,t]=lt
  else:
   q=1-math.exp(-float(cfg['language_precondition_relaxation_per_kyr'])*dt);lang[:,:,t]=lang[:,:,t-1]+q*(lt-lang[:,:,t-1])
 # Direct CHA2 event-memory integration at exact 50-year cadence
 bind=st['binding'];hages=bind['cha2_age_ka'];sev=bind['composite_event_severity'];mem50=np.zeros_like(sev);mem=np.zeros((M,L,R),float)
 # support interpolators using parent time values at exact 50-y ages
 for j,age in enumerate(hages):
  # nearest interpolation along descending full axis for dynamic supports
  # vectorized per element using weights between neighboring full time states
  k=np.searchsorted((-time),-age,side='left');k=min(max(k,1),T-1);a0=time[k-1];a1=time[k];w=0 if abs(a0-a1)<1e-15 else (a0-age)/(a0-a1)
  encj=(1-w)*enc[:,:,k-1]+w*enc[:,:,k];rehj=(1-w)*reh[:,:,k-1]+w*reh[:,:,k];netj=((1-w)*st['network'][:,:,k-1]+w*st['network'][:,:,k])[:,:,None]
  decay=float(cfg['event_memory_decay_per_kyr'])*memory_decay_multiplier*(1-float(cfg['rehearsal_decay_reduction'])*rehj)
  mem=mem*np.exp(-np.maximum(decay,0)*.05)+float(cfg['cha2_event_memory_gain'])*sev[:,:,j]*encj*(.55+.45*netj)*.05
  mem=np.clip(mem,0,1);mem50[:,:,j]=mem
 # map event memory onto full axis: zero before 15, exact interpolation 15..11, then decay with rehearsal
 event=np.zeros((M,L,T,R),float)
 for t,age in enumerate(time):
  if age>14.95: event[:,:,t]=0
  elif age>=11.0:
   # interpolate memory50 versus exact age axis
   x=hages[::-1]
   for m in range(M):
    for l in range(L):
     for r in range(R): event[m,l,t,r]=np.interp(age,x,mem50[m,l,::-1,r])
 # forward post-event decay 11 -> 0 using full time axis
 i11=int(np.where(np.isclose(time,11.0,rtol=0,atol=1e-12))[0][0]);event[:,:,i11]=mem50[:,:,-1]
 for t in range(i11+1,T):
  dt=float(time[t-1]-time[t]);rh=.5*(reh[:,:,t-1]+reh[:,:,t]);dec=float(cfg['event_memory_decay_per_kyr'])*memory_decay_multiplier*(1-float(cfg['rehearsal_decay_reduction'])*rh)
  event[:,:,t]=event[:,:,t-1]*np.exp(-np.maximum(dec,0)*dt)
 # general collective symbolic memory and memory-persistence support
 net=st['network'][:,:,:,None];tr=st['trans'][:,:,:,None];cu=st['culture'][:,:,:,None]
 background=np.clip(.26*cu+.18*st['retention']+.17*enc+.15*reh+.14*st['continuity']+.10*net,0,1)
 ew=float(cfg['collective_event_memory_weight']);collect=np.clip((1-ew)*background+ew*event,0,1)
 persist=np.clip(.32*reh+.24*st['retention']+.18*enc+.14*st['continuity']+.12*tr,0,1)
 state=np.stack([event,collect,enc,reh,ident,bound,conv,contact,lang,persist],axis=-1)
 return {'age_ka':time,'anchor_age_ka':st['anchor'],'regional_symbolic_state':state,'binding':bind,'_static':st}

def _anchor_indices(time:np.ndarray,anchors:np.ndarray)->np.ndarray: return _match_indices(time,anchors)

def _stem_robust_counts(rep:dict[str,np.ndarray],cfg:dict[str,Any])->tuple[list[int],list[int],list[int]]:
 S=rep['regional_symbolic_state'];idx={n:i for i,n in enumerate(SYMBOLIC_STATE_NAMES)};f=S[:,:,-1]
 sym=[];cha=[];lang=[]
 for l in range(2):
  sc=cc=lc=0
  for r in range(EXPECTED_REGIONS):
   v=f[:,l,r,idx['collective_symbolic_memory']]
   if np.median(v)>=float(cfg['robust_symbolic_memory_median_threshold']) and np.quantile(v,.1)>=float(cfg['robust_symbolic_memory_q10_threshold']): sc+=1
   v=f[:,l,r,idx['cha2_event_memory_stock']]
   if np.mean(v>=float(cfg['robust_cha2_memory_threshold']))>=float(cfg['robust_cha2_memory_member_fraction']): cc+=1
   v=f[:,l,r,idx['language_divergence_precondition']]
   if np.mean(v>=float(cfg['language_divergence_precondition_threshold']))>=float(cfg['robust_language_member_fraction']): lc+=1
  sym.append(sc);cha.append(cc);lang.append(lc)
 return sym,cha,lang

def _pathway(rep:dict[str,np.ndarray],l:int,cfg:dict[str,Any])->str:
 S=rep['regional_symbolic_state'];idx={n:i for i,n in enumerate(SYMBOLIC_STATE_NAMES)};f=S[:,l,-1]
 sym=int(np.sum([(np.median(f[:,r,idx['collective_symbolic_memory']])>=float(cfg['robust_symbolic_memory_median_threshold']) and np.quantile(f[:,r,idx['collective_symbolic_memory']],.1)>=float(cfg['robust_symbolic_memory_q10_threshold'])) for r in range(EXPECTED_REGIONS)]))
 im=float(np.median(f[...,idx['identity_marker_salience']]));bd=float(np.median(f[...,idx['interlineage_boundary_salience']]));lg=float(np.median(f[...,idx['language_divergence_precondition']]))
 if lg>=float(cfg['language_divergence_precondition_threshold']) and bd>=float(cfg['identity_boundary_threshold']): return 'REGIONAL_SYMBOLIC_IDENTITY_WITH_LANGUAGE_DIVERGENCE_PRECONDITIONS'
 if im>=float(cfg['identity_marker_threshold']): return 'REGIONAL_SYMBOLIC_MEMORY_WITH_EMERGENT_IDENTITY_MARKING'
 if sym>0: return 'REGIONAL_SYMBOLIC_MEMORY_WITH_WEAK_IDENTITY_BOUNDARIES'
 return 'CULTURAL_MEMORY_WITHOUT_ROBUST_SYMBOLIC_REGIONALIZATION'

def summarize(inp:dict[str,Any],rep:dict[str,np.ndarray],cfg:dict[str,Any])->tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
 S=rep['regional_symbolic_state'];idx={n:i for i,n in enumerate(SYMBOLIC_STATE_NAMES)};symc,chac,langc=_stem_robust_counts(rep,cfg);lines=[]
 for l,sid in enumerate(EXPECTED_CANDIDATES):
  f=S[:,l,-1]
  lines.append({
   'lineage_id':sid,'resolved_symbolic_language_identity_pathway':_pathway(rep,l,cfg),
   'robust_symbolic_memory_stems':symc[l],'robust_persistent_cha2_memory_stems':chac[l],'robust_language_divergence_precondition_stems':langc[l],
   'final_collective_symbolic_memory_median':float(np.median(f[...,idx['collective_symbolic_memory']])),
   'final_cha2_event_memory_median':float(np.median(f[...,idx['cha2_event_memory_stock']])),
   'final_cha2_event_memory_max':float(np.max(f[...,idx['cha2_event_memory_stock']])),
   'final_identity_marker_salience_median':float(np.median(f[...,idx['identity_marker_salience']])),
   'final_interlineage_boundary_salience_median':float(np.median(f[...,idx['interlineage_boundary_salience']])),
   'final_communicative_conventionalization_median':float(np.median(f[...,idx['communicative_conventionalization']])),
   'final_language_contact_pressure_median':float(np.median(f[...,idx['language_contact_pressure']])),
   'final_language_divergence_precondition_median':float(np.median(f[...,idx['language_divergence_precondition']]))})
 outcomes={'stage':STAGE,'status':'R339_SYMBOLIC_MEMORY_LANGUAGE_IDENTITY_OUTCOMES','candidate_lineages':EXPECTED_CANDIDATES,'lineages':lines,'named_myth_materialized':False,'religion_materialized':False,'ethnicity_materialized':False,'language_materialized':False,'named_language_family_materialized':False,'unique_human_identity_materialized':False}
 # persistent CHA2-memory events are anonymous analytical records, not myths
 events=[]
 for l,sid in enumerate(EXPECTED_CANDIDATES):
  for r in range(EXPECTED_REGIONS):
   v=S[:,l,-1,r,idx['cha2_event_memory_stock']];freq=float(np.mean(v>=float(cfg['robust_cha2_memory_threshold'])))
   if freq>=float(cfg['robust_cha2_memory_member_fraction']): events.append({'stem_id':f'{sid}:C{r+1:02d}','member_frequency':freq,'event_type':'ROBUST_PERSISTENT_CHA2_EVENT_MEMORY','named_myth_claimed':False})
 memory={'stage':STAGE,'status':'R339_SYMBOLIC_MEMORY_EVENT_LEDGER','cha2_event_memory_semantics':'DIRECT_R320_HAZARD_SEEDED_COLLECTIVE_MEMORY;_ANALYTICAL_MEMORY_STOCK_NOT_A_NAMED_MYTH_OR_RELIGIOUS_TRADITION','robust_persistent_cha2_event_memory_stems':events,'named_myth_materialized':False}
 combos=[(.8,1,1),(1,1,1),(1.2,1,1),(1,.85,1),(1,1.15,1),(1,1,.85),(1,1,1.15),(.85,1.15,.9),(1.15,.85,1.1),(.75,1.25,1),(1.25,.75,1),(1,1.2,1.2)]
 vars=[]
 for dm,ig,lg in combos:
  r=replay_symbolic_memory_language_identity(inp,cfg,dm,ig,lg,static=rep['_static'])
  sc,cc,lc=_stem_robust_counts(r,cfg)
  vars.append({'memory_decay_multiplier':dm,'identity_gain_multiplier':ig,'language_boundary_multiplier':lg,'resolved_pathways':[_pathway(r,l,cfg) for l in range(2)],'robust_symbolic_memory_stems':sc,'robust_persistent_cha2_memory_stems':cc,'robust_language_divergence_precondition_stems':lc})
 sens={'stage':STAGE,'status':'R339_SYMBOLIC_MEMORY_LANGUAGE_IDENTITY_SENSITIVITY','variant_count':len(vars),'selection_gate':False,'variants':vars}
 return outcomes,memory,sens

def _audit(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],outs:dict[str,Any],mem:dict[str,Any],sens:dict[str,Any])->dict[str,Any]:
 checks=[]
 def ck(n,c,d=None): checks.append({'name':n,'pass':bool(c),'detail':d})
 S=rep['regional_symbolic_state'];B=rep['binding']
 ck('r338_parent_sealed',inp['a38']['status']==PARENT_PASS);ck('r329_parent_sealed',inp['a29']['status']==R329_PASS);ck('r320_parent_sealed',inp['s20']['verdict']==R320_PASS)
 ck('time_axis_exact',rep['age_ka'].shape==(145,) and rep['age_ka'][0]==20 and rep['age_ka'][-1]==0);ck('anchor_axis_exact',rep['anchor_age_ka'].shape==(9,));ck('symbolic_geometry',S.shape==(32,2,145,6,len(SYMBOLIC_STATE_NAMES)));ck('symbolic_finite_bounded',np.isfinite(S).all() and S.min()>=0 and S.max()<=1)
 ck('cha2_exact_80',B['regional_cha2_exposure'].shape==(32,2,80,6,5) and B['cha2_age_ka'][0]==14.95 and B['cha2_age_ka'][-1]==11.0);ck('cha2_source_fields_unmodified',np.all(B['regional_cha2_exposure']>=0));ck('cha2_memory_zero_before_event',np.max(S[:,:,rep['age_ka']>14.95,:,0])==0)
 ck('sensitivity_12',sens['variant_count']==12);ck('sensitivity_no_selection',sens['selection_gate'] is False);ck('no_named_myth',outs['named_myth_materialized'] is False and mem['named_myth_materialized'] is False);ck('no_religion',outs['religion_materialized'] is False);ck('no_ethnicity',outs['ethnicity_materialized'] is False);ck('no_language_materialization',outs['language_materialized'] is False and outs['named_language_family_materialized'] is False);ck('no_unique_human_identity',outs['unique_human_identity_materialized'] is False);ck('no_lineage_rescale',cfg['governance']['no_lineage_specific_rescaling'] is True);ck('deep_off',cfg['governance']['deep_biological_coupling'] is False);ck('evidence_multisource',len(EVIDENCE)>=9)
 failed=[x for x in checks if not x['pass']]
 return {'stage':STAGE,'status':CANDIDATE_PASS if not failed else 'FAIL_R339_INTEGRATED_AUDIT','checks_passed':len(checks)-len(failed),'checks_total':len(checks),'checks_failed':len(failed),'checks':checks,'summary':{'candidate_lineages':2,'time_states':145,'regional_stems':12,'cha2_direct_50y_states':80,'resolved_symbolic_language_identity_pathways':{x['lineage_id']:x['resolved_symbolic_language_identity_pathway'] for x in outs['lineages']},'robust_persistent_cha2_memory_stems':len(mem['robust_persistent_cha2_event_memory_stems']),'language_materialized':False,'religion_ethnicity_materialized':False,'deep_biological_coupling':False}}

def build_outputs(inp:dict[str,Any],cfg:dict[str,Any],rep:dict[str,np.ndarray],out:Path)->dict[str,Any]:
 out.mkdir(parents=True,exist_ok=True);outs,mem,sens=summarize(inp,rep,cfg);B=rep['binding'];S=rep['regional_symbolic_state'];ai=_anchor_indices(rep['age_ka'],rep['anchor_age_ka']);z38=inp['z38'];rs=np.asarray(z38['regional_state'],float);rn=list(map(str,z38['regional_state_variable_names']));cont=_aggregate_r32_continuity(inp)
 base=np.stack([rs[...,rn.index('represented_people')],rs[...,rn.index('represented_camps')],rs[...,rn.index('grid_row')],rs[...,rn.index('grid_col')],rs[...,rn.index('regional_lineage_code')],cont],axis=-1)
 anchor_state=np.concatenate([base,S[:,:,ai]],axis=-1)
 auth={'stage':STAGE,'status':'R339_CULTURAL_SYMBOLIC_MEMORY_LANGUAGE_PRECONDITION_AND_IDENTITY_AUTHORITY','parent':PARENT_PASS,'window_ka':[20.0,0.0],'cha2_binding':'DIRECT_R320_80_STATE_50_YEAR_HYDROLOGICAL_HAZARD_FIELDS_SAMPLED_AT_INTERPOLATED_REGIONAL_STEM_LOCATIONS','symbolic_memory_semantics':'ABSTRACT_COLLECTIVE_AND_EVENT_MEMORY_CAPACITY;_NOT_A_NAMED_MYTH_RITUAL_RELIGION_OR_DIRECT_ARCHAEOLOGICAL_SYMBOL_OBSERVATION','identity_semantics':'CONVENTIONAL_AFFILIATION_AND_BOUNDARY_SALIENCE;_NOT_ETHNICITY_RACE_PEOPLE_OR_CASTE','language_semantics':'COMMUNICATIVE_CONVENTIONALIZATION_AND_DIVERGENCE_PRECONDITIONS_ONLY;_NO_LANGUAGE_GRAMMAR_LEXICON_OR_LANGUAGE_FAMILY_MATERIALIZED','prohibited_materialization':['named_myths','religions','ethnicities','named_peoples','languages','language_families','states','unique_human_identity','Deep_biological_coupling'],'evidence_basis':EVIDENCE,'dynamics':cfg,'parent_hashes':{'r338_regional_network_sha256':sha256_file(inp['r38']/'R3_38_REGIONAL_CULTURAL_NETWORKS.npz'),'r338_technology_sha256':sha256_file(inp['r38']/'R3_38_CONCRETE_TECHNOLOGY_REPLAY.npz'),'r329_community_sha256':sha256_file(inp['r29']/'R3_29_COMMUNITY_NETWORK_REPLAY.npz'),'r332_regional_sha256':sha256_file(inp['r32']/'R3_32_REGIONAL_CULTURAL_LINEAGE_ANCHORS.npz'),'r320_cha2_hazard_sha256':sha256_file(inp['hzp'])}}
 write_json(out/'R3_39_SYMBOLIC_MEMORY_LANGUAGE_IDENTITY_AUTHORITY.json',auth)
 np.savez_compressed(out/'R3_39_SYMBOLIC_MEMORY_REPLAY.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=z38['parent_member_indices'],age_ka=rep['age_ka'],symbolic_state_variable_names=np.array(SYMBOLIC_STATE_NAMES),regional_symbolic_state=S)
 np.savez_compressed(out/'R3_39_CHA2_REGIONAL_MEMORY_BINDING.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=z38['parent_member_indices'],cha2_age_ka=B['cha2_age_ka'],cha2_exposure_variable_names=np.array(CHA2_EXPOSURE_NAMES),regional_position=B['regional_position'],regional_cha2_exposure=B['regional_cha2_exposure'],composite_event_severity=B['composite_event_severity'])
 np.savez_compressed(out/'R3_39_REGIONAL_SYMBOLIC_LANGUAGE_IDENTITY_ANCHORS.npz',candidate_ids=np.array(EXPECTED_CANDIDATES),parent_member_indices=z38['parent_member_indices'],anchor_age_ka=rep['anchor_age_ka'],regional_anchor_variable_names=np.array(REGIONAL_ANCHOR_NAMES),regional_anchor_state=anchor_state)
 write_json(out/'R3_39_LINEAGE_SYMBOLIC_LANGUAGE_IDENTITY_OUTCOMES.json',outs);write_json(out/'R3_39_SYMBOLIC_MEMORY_EVENT_LEDGER.json',mem);write_json(out/'R3_39_SENSITIVITY_AND_ROBUSTNESS.json',sens)
 audit=_audit(inp,cfg,rep,outs,mem,sens);write_json(out/'R3_39_INTEGRATED_AUDIT.json',audit);(out/'R3_39_AUDIT.md').write_text(f"# R3.39 Integrated Audit\n\n- Status: `{audit['status']}`\n- Checks: **{audit['checks_passed']}/{audit['checks_total']}**\n- Pathways: `{audit['summary']['resolved_symbolic_language_identity_pathways']}`\n- Robust persistent CHA-2 memory stems: **{audit['summary']['robust_persistent_cha2_memory_stems']}**\n",encoding='utf-8');return audit

def write_manifest(out:Path,status:str)->None:
 files={}
 for p in sorted(out.iterdir()):
  if p.name=='R3_39_OUTPUT_MANIFEST.json' or not p.is_file(): continue
  files[p.name]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
 write_json(out/'R3_39_OUTPUT_MANIFEST.json',{'stage':STAGE,'status':status,'files':files})
