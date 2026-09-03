from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import math, json, hashlib
import numpy as np
from scipy import ndimage

# ARCANA WorldSim v0.6D1-R2
# Rebased Natural-Control Deep-Time Runtime, 210 -> 180 Ma pilot.
# Deep biological coupling is OFF in this stage.
# IMPORTANT: this stage computes RI/isolation diagnostics but does NOT materialize
# speciation births. That actuator is explicitly deferred because no pair is ready
# in the validated 210->180 Ma H0 pilot. No random speciation/extinction rates exist.
R2_STAGE_ID = "v0.6D1-R2"
R2_SCOPE = "REBASED_NATURAL_CONTROL_210_180_MACROEVOLUTION_PILOT"
R2_SPECIATION_BIRTH_ACTUATOR_AUTHORIZED = False
R2_DEEP_BIOLOGICAL_COUPLING_ENABLED = False

GUILD_TAU={1:120000.,2:180000.,3:140000.,4:160000.,5:220000.,6:350000.}
GEN_PROXY={1:3.,2:12.,3:6.,4:4.,5:8.,6:18.}
PREY_KEY_TO_GUILD={'small_herbivore':1,'browser':2,'low_feeder':3,'reptiloid':4}
_EDGE_CACHE={}

@dataclass(frozen=True)
class R2Config:
    start_age_ma: float=210.0
    end_age_ma: float=180.0
    dt_years: float=250000.0
    snapshot_interval_years: float=1000000.0
    topology_switch_age_ma: float=195.0
    occupancy_floor: float=1e-9
    habitat_floor: float=1e-12
    migration_reference_years: float=250000.0
    migration_fraction_ceiling: float=0.30
    gene_flow_ceiling_per_step: float=0.15
    trait_response_timescale_years: float=300000.0
    body_mass_scale: float=0.35
    mutation_variance_supply_normalized_per_myr: float=0.002
    variance_ceiling_normalized: float=0.05
    nonlinear_stabilizing_variance_depletion_per_myr_per_q: float=0.9876543209876544
    selection_variance_depletion_per_generation: float=2e-8
    drift_individual_equivalents_per_population_unit: float=250000000.0
    drift_min_effective_size: float=500.0
    speciation_check_interval_years: float=500000.0
    ordinary_extinction_check_interval_years: float=500000.0
    ordinary_extinction_minimum_persistence_years: float=2000000.0
    ordinary_extinction_founder_floor_fraction: float=0.05
    ordinary_extinction_max_opportunity_ratio: float=0.15
    ordinary_extinction_max_range_ratio: float=0.10
    ordinary_extinction_max_density_ratio: float=0.15
    ordinary_extinction_max_population_ratio_to_episode_start: float=0.90
    ordinary_extinction_recovery_reset_factor: float=1.25
    ordinary_extinction_minimum_species_age_years: float=2000000.0
    minimum_effective_isolation_generations: float=50000.0
    minimum_intrinsic_ri: float=0.65
    minimum_trait_distance: float=1.0
    maximum_effective_exchange_pressure: float=0.25
    minimum_branch_population_fraction: float=0.05
    minimum_complement_population_fraction: float=0.05
    minimum_absolute_population: float=0.01
    ri_build_rate_per_generation: float=2e-5
    ri_decay_rate_per_generation: float=5e-5
    isolation_reconnection_erosion: float=1.0
    trait_drive_onset: float=0.50
    trait_drive_saturation: float=1.50
    seed: int=917231


def _components_wrap(mask):
    # scipy label + union labels that touch across longitude seam.
    st=np.array([[0,1,0],[1,1,1],[0,1,0]],dtype=np.uint8)
    lab,n=ndimage.label(mask,structure=st)
    if n<=1:return lab,n
    parent=list(range(n+1))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        if a and b:
            ra,rb=find(int(a)),find(int(b))
            if ra!=rb: parent[rb]=ra
    for i in range(mask.shape[0]):
        if mask[i,0] and mask[i,-1]: union(lab[i,0],lab[i,-1])
    roots={}
    out=np.zeros_like(lab)
    k=0
    for old in range(1,n+1):
        r=find(old)
        if r not in roots:k+=1;roots[r]=k
        out[lab==old]=roots[r]
    return out,k

def weighted_centroid(lat,lon,p):
    n=float(p.sum())
    if n<=0:return (float('nan'),float('nan'))
    la=float(np.sum(p*lat[:,None])/n)
    ang=np.deg2rad(lon)[None,:]
    x=float(np.sum(p*np.cos(ang)));y=float(np.sum(p*np.sin(ang)))
    return la, math.degrees(math.atan2(y,x))

def gc_km(a,b):
    la1,lo1=a;la2,lo2=b
    p1,p2=math.radians(la1),math.radians(la2)
    dp=p2-p1;dl=math.radians(lo2-lo1)
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 12742.0176*math.asin(min(1.0,math.sqrt(max(h,0.0))))

def normalize_resource(arr,land):
    a=np.maximum(np.asarray(arr,float),0.0)
    pos=a[land & (a>0)]
    scale=float(np.percentile(pos,95)) if pos.size else 1.0
    out=np.clip(a/max(scale,1e-15),0,1);out[~land]=0
    return out

def transport_once(mass,q):
    qn=np.zeros_like(q);qs=np.zeros_like(q);qn[1:]=q[:-1];qs[:-1]=q[1:]
    qe=np.roll(q,-1,axis=1);qw=np.roll(q,1,axis=1);den=q+qn+qs+qe+qw
    out=np.divide(mass*q,den,out=np.zeros_like(mass),where=den>0)
    mn=np.divide(mass*qn,den,out=np.zeros_like(mass),where=den>0)
    ms=np.divide(mass*qs,den,out=np.zeros_like(mass),where=den>0)
    me=np.divide(mass*qe,den,out=np.zeros_like(mass),where=den>0)
    mw=np.divide(mass*qw,den,out=np.zeros_like(mass),where=den>0)
    out[:-1]+=mn[1:];out[1:]+=ms[:-1];out+=np.roll(me,1,axis=1);out+=np.roll(mw,-1,axis=1)
    stuck=(den<=0)&(mass>0);out[stuck]+=mass[stuck]
    return out

def median_edge_km(lat,lon,land):
    key=(land.shape, hash(land.tobytes()))
    if key in _EDGE_CACHE:return _EDGE_CACHE[key]
    vals=[]
    inds=np.argwhere(land)
    for i,j in inds[::max(1,len(inds)//2000)]:
        if i+1<len(lat) and land[i+1,j]:vals.append(gc_km((lat[i],lon[j]),(lat[i+1],lon[j])))
        j2=(j+1)%len(lon)
        if land[i,j2]:vals.append(gc_km((lat[i],lon[j]),(lat[i],lon[j2])))
    v=float(np.median(vals)) if vals else 200.0;_EDGE_CACHE[key]=v;return v

def environment_at(age,a1,switch_age=195.0):
    ages=a1['age_ma'].astype(float); i0=int(np.where(np.isclose(ages,210))[0][0]);i1=int(np.where(np.isclose(ages,180))[0][0])
    f=np.clip((210.0-age)/30.0,0,1)
    old=age>switch_age
    land=np.asarray(a1['land_mask'][i0 if old else i1],bool)
    plate=np.asarray(a1['plate_code'][i0 if old else i1],np.uint8)
    out={'age_ma':age,'land':land,'plate':plate,'phase':f,'topology':'210Ma' if old else '180Ma'}
    for k in ['temperature_c','aridity_index','browse_forage','low_forage','wetland_forage','total_edible_forage']:
        v=(1-f)*a1[k][i0].astype(float)+f*a1[k][i1].astype(float);v[~land]=0;out[k]=v
    # population/capacity reference: interpolate spatial field, mask topology, rescale to interpolated global totals per guild
    for src,name in [('population','reference_population'),('carrying_capacity','reference_capacity')]:
        arr=(1-f)*a1[src][i0].astype(float)+f*a1[src][i1].astype(float)
        target=(1-f)*a1[src][i0].sum(axis=(1,2)).astype(float)+f*a1[src][i1].sum(axis=(1,2)).astype(float)
        arr[:,~land]=0
        for g in range(6):
            s=float(arr[g].sum())
            if s>0: arr[g]*=float(target[g])/s
        out[name]=arr
    return out

def partition_components(species_ids,species_pop,guild_ids,occ=1e-9):
    ids=[];sp=[];guild=[];pops=[]
    for si,sid in enumerate(species_ids):
        p=species_pop[si]; lab,n=_components_wrap(p>occ)
        rows=[]
        for k in range(1,n+1):
            q=np.where(lab==k,p,0.0);rows.append((float(q.sum()),q))
        rows.sort(key=lambda x:-x[0])
        if not rows:rows=[(float(p.sum()),p.copy())]
        else:
            covered=np.sum([q for _,q in rows],axis=0)
            tail=p-covered
            rows[0]=(rows[0][0]+float(tail.sum()), rows[0][1]+tail)
        rebuilt=np.zeros_like(p)
        for ci,(m,q) in enumerate(rows,1):
            ids.append(f'{sid}_C{ci:03d}');sp.append(sid);guild.append(int(guild_ids[si]));pops.append(q);rebuilt+=q
        if not np.allclose(rebuilt,p,rtol=0,atol=1e-12):raise RuntimeError('component partition failed')
    return ids,sp,np.asarray(guild,np.uint8),np.stack(pops)

def init_traits(component_species,metadata):
    tr=np.zeros((len(component_species),3));va=np.zeros_like(tr);gen=np.zeros(len(tr))
    for i,sid in enumerate(component_species):
        m=metadata[sid]; tr[i]=[m['thermal_optimum_c'],m['drought_tolerance_index'],m['relative_log_body_mass']]
        ds=max(m['aridity_niche_sigma']/1.55,1e-4)
        va[i]=[(0.08*m['thermal_niche_sigma_c'])**2,(0.08*ds)**2,0.05**2]
        gen[i]=GEN_PROXY[m['guild_id']]/max(m['relative_reproduction_rate'],1e-6)
    return tr,va,gen

def climate_suit(m,tr,temp,arid,land,floor):
    ao=1.55*(1-np.clip(tr[1],0,1));ts=max(m['thermal_niche_sigma_c'],1e-9);a=max(m['aridity_niche_sigma'],1e-9)
    q=np.exp(-.5*((temp-tr[0])/ts)**2-.5*((arid-ao)/a)**2);q[~land]=0;q[land]=np.maximum(q[land],floor);return q

def resource_field(m,g,env,species_pop_by_id,guild_by_id,land):
    if g==2:return normalize_resource(env['browse_forage'],land)
    if g==3:return normalize_resource(env['low_forage'],land)
    if g==4:
        w=m.get('diet_weights',{});r=w.get('browse',0)*env['browse_forage']+w.get('low',0)*env['low_forage']+w.get('wetland',0)*env['wetland_forage'];return normalize_resource(r,land)
    if g==1:return normalize_resource(env['total_edible_forage'],land)
    w=m.get('diet_weights',{});r=np.zeros_like(env['temperature_c'])
    for key,ww in w.items():
        pg=PREY_KEY_TO_GUILD.get(key)
        if pg:
            for sid,p in species_pop_by_id.items():
                if guild_by_id[sid]==pg:r+=float(ww)*p
    return normalize_resource(r,land)

def _normalize_batch(arr,land):
    a=np.maximum(np.asarray(arr,float),0.0); out=np.zeros_like(a)
    for i in range(len(a)):
        pos=a[i][land & (a[i]>0)]; scale=float(np.percentile(pos,95)) if pos.size else 1.0; out[i]=np.clip(a[i]/max(scale,1e-15),0,1); out[i,~land]=0
    return out

def habitats(comp_species,guild,trait,pop,metadata,env):
    nd=len(pop); land=env['land']; temp=env['temperature_c']; arid=env['aridity_index']
    ts=np.array([max(metadata[s]['thermal_niche_sigma_c'],1e-9) for s in comp_species])[:,None,None]; ars=np.array([max(metadata[s]['aridity_niche_sigma'],1e-9) for s in comp_species])[:,None,None]; ao=(1.55*(1-np.clip(trait[:,1],0,1)))[:,None,None]; to=trait[:,0,None,None]
    clim=np.exp(-.5*((temp[None]-to)/ts)**2-.5*((arid[None]-ao)/ars)**2);clim[:,~land]=0;clim[:,land]=np.maximum(clim[:,land],1e-12)
    res=np.zeros_like(clim);rtot=normalize_resource(env['total_edible_forage'],land);rb=normalize_resource(env['browse_forage'],land);rl=normalize_resource(env['low_forage'],land)
    guild=np.asarray(guild,int);res[guild==1]=rtot;res[guild==2]=rb;res[guild==3]=rl
    ix=np.where(guild==4)[0]
    if len(ix):
        wb=np.array([metadata[comp_species[i]].get('diet_weights',{}).get('browse',0) for i in ix])[:,None,None];wl=np.array([metadata[comp_species[i]].get('diet_weights',{}).get('low',0) for i in ix])[:,None,None];ww=np.array([metadata[comp_species[i]].get('diet_weights',{}).get('wetland',0) for i in ix])[:,None,None];raw=wb*env['browse_forage']+wl*env['low_forage']+ww*env['wetland_forage'];res[ix]=_normalize_batch(raw,land)
    guildmaps=np.zeros((4,*land.shape));
    for g in range(1,5):guildmaps[g-1]=pop[guild==g].sum(axis=0)
    ix=np.where(guild>=5)[0]
    if len(ix):
        W=np.zeros((len(ix),4))
        for a,i in enumerate(ix):
            for key,w in metadata[comp_species[i]].get('diet_weights',{}).items():
                pg=PREY_KEY_TO_GUILD.get(key)
                if pg:W[a,pg-1]=float(w)
        raw=(W@guildmaps.reshape(4,-1)).reshape(len(ix),*land.shape);res[ix]=_normalize_batch(raw,land)
    q=clim*np.maximum(res,1e-12);mx=q.reshape(nd,-1).max(axis=1);good=mx>0;q[good]/=mx[good,None,None];q[:,~land]=0;return q

def opportunities(hab,comp_species,guild,env):
    # species max habitat across components * guild reference population
    out={}
    for sid in sorted(set(comp_species)):
        idx=[i for i,x in enumerate(comp_species) if x==sid];g=int(guild[idx[0]]);h=np.max(hab[idx],axis=0);out[sid]=float(np.sum(h*np.maximum(env['reference_population'][g-1],0)))
    return out

def _transport_batch(mass,q):
    qn=np.zeros_like(q);qs=np.zeros_like(q);qn[:,1:]=q[:,:-1];qs[:,:-1]=q[:,1:];qe=np.roll(q,-1,axis=2);qw=np.roll(q,1,axis=2);den=q+qn+qs+qe+qw
    out=np.divide(mass*q,den,out=np.zeros_like(mass),where=den>0);mn=np.divide(mass*qn,den,out=np.zeros_like(mass),where=den>0);ms=np.divide(mass*qs,den,out=np.zeros_like(mass),where=den>0);me=np.divide(mass*qe,den,out=np.zeros_like(mass),where=den>0);mw=np.divide(mass*qw,den,out=np.zeros_like(mass),where=den>0)
    out[:,:-1]+=mn[:,1:];out[:,1:]+=ms[:,:-1];out+=np.roll(me,1,axis=2);out+=np.roll(mw,-1,axis=2);stuck=(den<=0)&(mass>0);out[stuck]+=mass[stuck];return out

def migration(pop,hab,comp_species,metadata,lat,lon,land,dt,cfg):
    edge=median_edge_km(lat,lon,land); ds=np.array([metadata[s]['dispersal_scale_km'] for s in comp_species],float);tau=cfg.migration_reference_years*edge/np.maximum(ds,1e-9);f=np.clip(1-np.exp(-dt/np.maximum(tau,1e-9)),0,cfg.migration_fraction_ceiling)
    moved=_transport_batch(pop,hab);out=(1-f[:,None,None])*pop+f[:,None,None]*moved;out[:,~land]=0;before=pop.sum(axis=(1,2));after=out.sum(axis=(1,2));scale=np.divide(before,after,out=np.ones_like(before),where=after>0);out*=scale[:,None,None];return out

def selection_targets(pop,temp,arid):
    d=np.clip(1-np.asarray(arid)/1.55,0,1);n=pop.sum(axis=(1,2));tt=np.sum(pop*temp[None],axis=(1,2));dd=np.sum(pop*d[None],axis=(1,2));out=np.full((len(pop),2),np.nan);good=n>0;out[good,0]=tt[good]/n[good];out[good,1]=dd[good]/n[good];return out

def select_traits(tr,va,target,comp_species,metadata,dt,cfg):
    out=tr.copy()
    for i,sid in enumerate(comp_species):
        if not np.all(np.isfinite(target[i])):continue
        m=metadata[sid];rel=max(m['relative_reproduction_rate'],1e-6);beta=1-math.exp(-dt/(cfg.trait_response_timescale_years/rel));ts=max(m['thermal_niche_sigma_c'],1e-6);ds=max(m['aridity_niche_sigma']/1.55,1e-4)
        gt=np.clip(va[i,0]/ts**2,0,.25);gd=np.clip(va[i,1]/ds**2,0,.25);out[i,0]+=beta*gt*(target[i,0]-out[i,0]);out[i,1]+=beta*gd*(target[i,1]-out[i,1]);out[i,1]=np.clip(out[i,1],0,1)
    return out

def update_va(va,tr_before,target,pop_tot,gen,comp_species,metadata,dt,cfg):
    out=va.copy();mu=cfg.mutation_variance_supply_normalized_per_myr/1e6;b=cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q/1e6
    for i,sid in enumerate(comp_species):
        m=metadata[sid];sc=np.array([max(m['thermal_niche_sigma_c'],1e-6),max(m['aridity_niche_sigma']/1.55,1e-4),cfg.body_mass_scale]);q=va[i]/sc**2
        pressure=np.zeros(3)
        if np.all(np.isfinite(target[i])):pressure[:2]=((target[i]-tr_before[i,:2])/sc[:2])**2
        pressure=np.clip(pressure,0,4);ls=cfg.selection_variance_depletion_per_generation*pressure/max(gen[i],1e-9);ne=max(cfg.drift_min_effective_size,max(pop_tot[i],0)*cfg.drift_individual_equivalents_per_population_unit);ld=np.full(3,1/max(2*ne*gen[i],1e-30));lam=ls+ld
        qn=np.empty_like(q)
        for j in range(3):
            a=float(lam[j]);disc=math.sqrt(max(a*a+4*b*mu,0));rp=(-a+disc)/(2*b);rn=(-a-disc)/(2*b);den0=q[j]-rn;c0=0 if abs(den0)<1e-30 else (q[j]-rp)/den0;c=c0*math.exp(-disc*dt);den=1-c;qn[j]=rp if abs(den)<1e-30 else (rp-c*rn)/den
        out[i]=np.clip(qn,0,cfg.variance_ceiling_normalized)*sc**2
    return out

def pair_metrics(pop,tr,comp_species,metadata,lat,lon,cfg):
    n=len(pop);G=np.zeros((n,n));contact=np.zeros_like(G);td=np.zeros_like(G)
    totals=pop.sum(axis=(1,2))
    for sid in sorted(set(comp_species)):
        idx=[i for i,x in enumerate(comp_species) if x==sid]
        if len(idx)<2:continue
        m=metadata[sid];ds=max(m['dispersal_scale_km'],1e-9);ts=max(m['thermal_niche_sigma_c'],1e-6);ars=max(m['aridity_niche_sigma']/1.55,1e-4)
        cents=[weighted_centroid(lat,lon,pop[i]) for i in idx]
        for aa in range(len(idx)):
            i=idx[aa]
            for bb in range(aa+1,len(idx)):
                j=idx[bb];ov=float(np.minimum(pop[i],pop[j]).sum()/max(min(totals[i],totals[j]),1e-15));dist=gc_km(cents[aa],cents[bb]);g=float(np.clip(cfg.gene_flow_ceiling_per_step*ov*math.exp(-dist/(4*ds)),0,cfg.gene_flow_ceiling_per_step));G[i,j]=G[j,i]=g;contact[i,j]=contact[j,i]=g/cfg.gene_flow_ceiling_per_step
                dz=np.array([(tr[i,0]-tr[j,0])/ts,(tr[i,1]-tr[j,1])/ars,(tr[i,2]-tr[j,2])/cfg.body_mass_scale]);td[i,j]=td[j,i]=float(np.sqrt(np.sum(dz*dz)))
    return G,contact,td

def gene_flow_mix(tr,va,tot,G,comp_species):
    # first and second moment conservative mixing, sequential small G approximation from D3 semantics
    tr0=tr.copy();va0=va.copy();dtr=np.zeros_like(tr);dm2=np.zeros_like(tr)
    m2=va+tr*tr
    for i in range(len(tr)):
        ni=float(tot[i]);
        if ni<=0:continue
        for j in range(i+1,len(tr)):
            if comp_species[i]!=comp_species[j] or G[i,j]<=0:continue
            nj=float(tot[j]);
            if nj<=0:continue
            ex=float(G[i,j])*2*ni*nj/(ni+nj)
            dtr[i]+=(ex/ni)*(tr0[j]-tr0[i]);dtr[j]+=(ex/nj)*(tr0[i]-tr0[j]);dm2[i]+=(ex/ni)*(m2[j]-m2[i]);dm2[j]+=(ex/nj)*(m2[i]-m2[j])
    tn=tr+dtr;m2n=m2+dm2;vn=np.maximum(m2n-tn*tn,0);return tn,vn

def eco_drive(td,cfg):return float(np.clip((td-cfg.trait_drive_onset)/max(cfg.trait_drive_saturation-cfg.trait_drive_onset,1e-15),0,1))
def advance_pair(ri,clock,dg,p,td,cfg):
    e0=p*(1-ri);a=cfg.ri_build_rate_per_generation*eco_drive(td,cfg)*(1-e0);b=cfg.ri_decay_rate_per_generation*e0
    if (a+b)>0 and dg>0:r=a/(a+b)+(ri-a/(a+b))*math.exp(-(a+b)*dg)
    else:r=ri
    r=float(np.clip(r,0,1));e1=p*(1-r);em=.5*(e0+e1);cl=max(0,clock+((1-em)**2-cfg.isolation_reconnection_erosion*em)*dg);return r,cl,e1

def remap_to_land(pop,old_land,new_land,lat,lon):
    if np.array_equal(old_land,new_land):return pop,0.0
    lost=old_land & ~new_land;newidx=np.argwhere(new_land)
    if not np.any(lost):return pop,0.0
    # nearest new land via 3d unit sphere cKDTree
    from scipy.spatial import cKDTree
    def xyz(ii,jj):
        la=np.deg2rad(lat[ii]);lo=np.deg2rad(lon[jj]);return np.stack([np.cos(la)*np.cos(lo),np.cos(la)*np.sin(lo),np.sin(la)],axis=-1)
    tree=cKDTree(xyz(newidx[:,0],newidx[:,1]));li,lj=np.where(lost);_,ix=tree.query(xyz(li,lj),k=1);dest=newidx[ix]
    out=pop.copy();moved=0.0
    for d in range(len(pop)):
        vals=out[d,li,lj].copy();moved+=float(vals.sum());out[d,li,lj]=0
        np.add.at(out[d],(dest[:,0],dest[:,1]),vals)
        out[d,~new_land]=0
    return out,moved

def run(common,a1,metadata,cfg):
    ids=[str(x) for x in common['species_id'].tolist()];guild0=common['guild_id'].astype(int);md={r['species_id']:r for r in metadata}
    comp_ids,comp_sp,guild,pop=partition_components(ids,common['species_population'].astype(float),guild0,cfg.occupancy_floor);tr,va,gen=init_traits(comp_sp,md)
    lat=common['lat'].astype(float);lon=common['lon'].astype(float);old_land=environment_at(210,a1,cfg.topology_switch_age_ma)['land'];current_land=old_land.copy()
    # registry/baselines
    env0=environment_at(210,a1,cfg.topology_switch_age_ma);hab=habitats(comp_sp,guild,tr,pop,md,env0);opp0=opportunities(hab,comp_sp,guild,env0);base_pop={sid:float(sum(pop[i].sum() for i,x in enumerate(comp_sp) if x==sid)) for sid in set(comp_sp)};base_occ={sid:int(np.count_nonzero(np.sum([pop[i] for i,x in enumerate(comp_sp) if x==sid],axis=0)>cfg.occupancy_floor)) for sid in set(comp_sp)};base_opp={k:max(v,1e-15) for k,v in opp0.items()};birth={sid:0.0 for sid in set(comp_sp)}
    ri={};clock={};ext_state={};events=[];snaps=[]
    dur=(cfg.start_age_ma-cfg.end_age_ma)*1e6;nsteps=int(round(dur/cfg.dt_years));snap_every=max(1,int(round(cfg.snapshot_interval_years/cfg.dt_years)))
    initial_total=float(pop.sum());topology_remap_mass=0.0
    for step in range(nsteps+1):
        t=step*cfg.dt_years;age=cfg.start_age_ma-t/1e6;env=environment_at(age,a1,cfg.topology_switch_age_ma)
        if step>0 and not np.array_equal(env['land'],current_land):
            pop,mv=remap_to_land(pop,current_land,env['land'],lat,lon);topology_remap_mass+=mv;current_land=env['land'].copy();events.append({'event':'topology_support_switch','age_ma':age,'remapped_population_mass':mv})
        hab=habitats(comp_sp,guild,tr,pop,md,env);opp=opportunities(hab,comp_sp,guild,env)
        if step>0:
            # species demography targets; A1 reference abundance anchors, not K
            totals=pop.sum(axis=(1,2));sp_tot={sid:float(sum(totals[i] for i,x in enumerate(comp_sp) if x==sid)) for sid in set(comp_sp)}
            by_g={g:[] for g in range(1,7)}
            for sid in sorted(sp_tot):by_g[int(md[sid]['guild_id'])].append(sid)
            targets={}
            prey_cur=sum(sp_tot[s] for g in range(1,5) for s in by_g[g]);prey_ref=float(env['reference_population'][:4].sum())
            for g,sids in by_g.items():
                gt=float(env['reference_population'][g-1].sum());
                if g>=5:gt*=float(np.clip(prey_cur/max(prey_ref,1e-15),0,1.5))
                w=np.array([base_pop[s]*np.clip(opp[s]/base_opp[s],1e-3,1e3) for s in sids],float);w=w/w.sum() if w.sum()>0 else np.ones(len(sids))/len(sids)
                for sid,x in zip(sids,gt*w):targets[sid]=float(x)
            for sid in sorted(sp_tot):
                idx=[i for i,x in enumerate(comp_sp) if x==sid];g=int(md[sid]['guild_id']);tau=GUILD_TAU[g]/max(md[sid]['relative_reproduction_rate'],1e-6);a=1-math.exp(-cfg.dt_years/tau);new=max(0,sp_tot[sid]+a*(targets[sid]-sp_tot[sid]));sc=new/max(sp_tot[sid],1e-15);pop[idx]*=sc
            # migration
            pop=migration(pop,hab,comp_sp,md,lat,lon,env['land'],cfg.dt_years,cfg)
            # selection and VA
            tar=selection_targets(pop,env['temperature_c'],env['aridity_index']);trb=tr.copy();tr=select_traits(tr,va,tar,comp_sp,md,cfg.dt_years,cfg);tot=pop.sum(axis=(1,2));va=update_va(va,trb,tar,tot,gen,comp_sp,md,cfg.dt_years,cfg)
            # pair gene flow and isolation
            G,contact,td=pair_metrics(pop,tr,comp_sp,md,lat,lon,cfg);tr,va=gene_flow_mix(tr,va,tot,G,comp_sp)
            for sid in sorted(set(comp_sp)):
                idx=[i for i,x in enumerate(comp_sp) if x==sid]
                for aa in range(len(idx)):
                    i=idx[aa]
                    for bb in range(aa+1,len(idx)):
                        j=idx[bb];key=tuple(sorted((comp_ids[i],comp_ids[j])));r,c=ri.get(key,0.0),clock.get(key,0.0);dg=cfg.dt_years/max(gen[i],gen[j],1e-9);r,c,e=advance_pair(r,c,dg,float(contact[i,j]),float(td[i,j]),cfg);ri[key]=r;clock[key]=c
            # deterministic ordinary extinction gate
            if abs((t/cfg.ordinary_extinction_check_interval_years)-round(t/cfg.ordinary_extinction_check_interval_years))<1e-9:
                species=list(sorted(set(comp_sp)));to_ext=[]
                for sid in species:
                    idx=[i for i,x in enumerate(comp_sp) if x==sid];n=float(pop[idx].sum());occ=int(np.count_nonzero(pop[idx].sum(axis=0)>cfg.occupancy_floor));g=int(md[sid]['guild_id']);gt=float(np.average(gen[idx],weights=np.maximum(pop[idx].sum(axis=(1,2)),1e-15)));found=.075*math.sqrt(gt/5)*math.sqrt(1/max(md[sid]['relative_reproduction_rate'],1e-9));pr=n/max(base_pop[sid],1e-15);rr=occ/max(base_occ[sid],1);oratio=opp[sid]/base_opp[sid];dr=pr/max(rr,1e-12);stress=(n/max(found,1e-15)<=cfg.ordinary_extinction_founder_floor_fraction and (oratio<=cfg.ordinary_extinction_max_opportunity_ratio or rr<=cfg.ordinary_extinction_max_range_ratio or dr<=cfg.ordinary_extinction_max_density_ratio) and t-birth[sid]>=cfg.ordinary_extinction_minimum_species_age_years)
                    if not stress: ext_state.pop(sid,None);continue
                    st=ext_state.get(sid)
                    if st is None:st={'start':t,'first':n,'min':n}
                    else:
                        mn=min(st['min'],n)
                        if n>mn*cfg.ordinary_extinction_recovery_reset_factor:st={'start':t,'first':n,'min':n}
                        else:st['min']=mn
                    ext_state[sid]=st;pers=t-st['start'];decl=n/max(st['first'],1e-15)
                    if pers>=cfg.ordinary_extinction_minimum_persistence_years and decl<=cfg.ordinary_extinction_max_population_ratio_to_episode_start:to_ext.append(sid)
                for sid in to_ext:
                    idx=[i for i,x in enumerate(comp_sp) if x==sid];events.append({'event':'ordinary_background_extinction','species_id':sid,'age_ma':age,'population':float(pop[idx].sum()),'authority':'PERSISTENT_DETERMINISTIC_NONVIABILITY_GATE_NO_GLOBAL_RANDOM_EXTINCTION_RATE'});keep=np.array([x!=sid for x in comp_sp]);comp_ids=[x for i,x in enumerate(comp_ids) if keep[i]];comp_sp=[x for i,x in enumerate(comp_sp) if keep[i]];guild=guild[keep];pop=pop[keep];tr=tr[keep];va=va[keep];gen=gen[keep];ext_state.pop(sid,None)
        if step%snap_every==0 or step==nsteps:
            totals=pop.sum(axis=(1,2));species=sorted(set(comp_sp));spv={sid:float(sum(totals[i] for i,x in enumerate(comp_sp) if x==sid)) for sid in species};qnorm=[]
            for i,sid in enumerate(comp_sp):m=md[sid];sc=np.array([m['thermal_niche_sigma_c'],max(m['aridity_niche_sigma']/1.55,1e-4),cfg.body_mass_scale]);qnorm.extend((va[i]/sc**2).tolist())
            snaps.append({'age_ma':age,'elapsed_myr':t/1e6,'species_richness':len(species),'component_count':len(comp_sp),'total_population':float(pop.sum()),'median_species_population':float(np.median(list(spv.values()))),'median_normalized_va':float(np.median(qnorm)),'max_intrinsic_ri':float(max(ri.values()) if ri else 0),'max_isolation_clock_generations':float(max(clock.values()) if clock else 0),'event_count':len(events),'topology':env['topology']})
    return {'config':asdict(cfg),'initial_total_population':initial_total,'final_total_population':float(pop.sum()),'species_ids':sorted(set(comp_sp)),'component_ids':comp_ids,'component_species':comp_sp,'component_guild':guild,'population':pop,'trait':tr,'va':va,'generation_time':gen,'ri':ri,'clock':clock,'events':events,'snapshots':snaps,'topology_remap_mass':topology_remap_mass}

if __name__=='__main__':
    import argparse,time
    ap=argparse.ArgumentParser();ap.add_argument('--common',required=True);ap.add_argument('--a1',required=True);ap.add_argument('--meta',required=True);ap.add_argument('--dt',type=float,default=250000);ap.add_argument('--switch',type=float,default=195);ap.add_argument('--out',required=True);args=ap.parse_args()
    common=np.load(args.common,allow_pickle=False);a1=np.load(args.a1,allow_pickle=False);metadata=json.load(open(args.meta));cfg=R2Config(dt_years=args.dt,topology_switch_age_ma=args.switch);t=time.time();r=run(common,a1,metadata,cfg);print('elapsed',time.time()-t,'final',r['final_total_population'],len(r['species_ids']),len(r['component_ids']),len(r['events']));
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(out, population=r['population'],trait=r['trait'],va=r['va'],generation_time=r['generation_time'],component_id=np.asarray(r['component_ids'],dtype='U40'),component_species=np.asarray(r['component_species'],dtype='U40'),component_guild=r['component_guild'])
    js={k:v for k,v in r.items() if k not in {'population','trait','va','generation_time'}};json.dump(js,open(out.with_suffix('.json'),'w'),indent=2,default=lambda o:o.tolist() if hasattr(o,'tolist') else (float(o) if isinstance(o,(np.floating,np.integer)) else str(o)))
