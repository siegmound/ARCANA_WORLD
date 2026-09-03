from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib, json, math
import numpy as np

from deep_d3_coupling_v0_6A import (
    MODES, PassiveUptakeConfig, biological_pressure, local_passive_uptake_rate_per_year,
    analytic_replenished_component_step,
)
from deep_heritable_selection_v0_6B import (
    DeepHeritableConfig, initialize_latent_variance_from_d3,
    deme_mean_log_viability, viability_selection_gradient, selection_response_step,
    advance_latent_variance, gene_flow_moment_mix,
)

STATUS = "PASS_DEEP_PRODUCTION_RUNTIME_AND_PHYSIOLOGY_CLOSURE_CANDIDATE"

@dataclass(frozen=True)
class DeepRuntimeConfig:
    deep_enabled: bool = True
    photo_additive_share_E_th: float = 0.05
    return_flow_fraction: float = 0.50
    restore_time_years: tuple[float,...] = (80.0,120.0,100.0,250.0,500.0)
    physiology_fixed_point_tolerance: float = 1e-11
    physiology_fixed_point_max_iterations: int = 128
    physiology_long_step_tau_multiple: float = 10.0

    def validate(self) -> None:
        if not 0.0 <= self.photo_additive_share_E_th <= 1.0: raise ValueError("invalid photo share")
        if not 0.0 <= self.return_flow_fraction <= 1.0: raise ValueError("invalid return fraction")
        if len(self.restore_time_years)!=5 or any(x<=0 for x in self.restore_time_years): raise ValueError("invalid restore times")
        if self.physiology_fixed_point_tolerance<=0 or self.physiology_fixed_point_max_iterations<1: raise ValueError("invalid physiology solver")

@dataclass
class DeepRuntimeState:
    deme_ids: list[str]
    latent_mean: np.ndarray
    latent_va: np.ndarray
    acclimatization: np.ndarray
    remodeling: np.ndarray
    recoverable_load: np.ndarray
    injury: np.ndarray
    surface_background_energy_j: np.ndarray
    equilibrium_background_energy_j: np.ndarray
    photo_energy_j: np.ndarray
    photo_equilibrium_energy_j: np.ndarray
    source_buffer_j: np.ndarray
    cumulative_gross_uptake_j: np.ndarray
    cumulative_return_flow_j: np.ndarray
    cumulative_net_sink_j: np.ndarray
    cumulative_stellar_pump_j: np.ndarray
    endpoint_relative_year: float
    d3_runtime_state: dict[str,Any] | None = None
    schema_version: str = "v0.6C"

    def validate(self) -> None:
        n=len(self.deme_ids)
        if self.latent_mean.shape!=(n,10) or self.latent_va.shape!=(n,10): raise ValueError("latent state shape mismatch")
        for x in (self.acclimatization,self.remodeling,self.recoverable_load,self.injury):
            if np.asarray(x).shape!=(n,): raise ValueError("physiology state shape mismatch")
        sh=self.surface_background_energy_j.shape
        if len(sh)!=3 or sh[0]!=5 or self.equilibrium_background_energy_j.shape!=sh or self.photo_energy_j.shape!=sh or self.photo_equilibrium_energy_j.shape!=sh or self.source_buffer_j.shape!=sh: raise ValueError("energy state shape mismatch")
        if np.any(self.surface_background_energy_j<0) or np.any(self.photo_energy_j<0) or np.any(self.source_buffer_j<0): raise ValueError("negative Deep energy")


def _sigmoid_rows(z: np.ndarray):
    s=1.0/(1.0+np.exp(-np.asarray(z,float)))
    return s[:,:5],s[:,5],s[:,6],s[:,7],s[:,8],s[:,9]


def _interface_summary_one(pop: np.ndarray, mode_opportunity: np.ndarray, latent: np.ndarray,
                           bio_cfg: Mapping[str,Any], acclim: float, remodel: float) -> dict[str,float]:
    p=np.maximum(np.asarray(pop,float),0.0); mask=p>0; den=float(p[mask].sum())
    coupling,uptake,reg,tol,plastic,repair=_sigmoid_rows(np.asarray(latent,float).reshape(1,10))
    tc=bio_cfg['tolerance_scale']; b=bio_cfg['threshold_base_load_units']
    scale=(float(tc['intercept'])+float(tc['heritable_tolerance'])*tol[0]+float(tc['persistent_remodeling'])*np.clip(remodel,0,1)+float(tc['reversible_acclimatization_x_regulation'])*np.clip(acclim,0,1)*reg[0])
    win=np.asarray([float(b[k])*scale for k in ('L_min','L_opt','L_tol','L_injury')],float)
    if den<=0: return {'L_X':0.0,'adaptive_stimulus':0.0,'stress':0.0,'injury_risk':0.0,'L_min':win[0],'L_opt':win[1],'L_tol':win[2],'L_injury':win[3]}
    w=np.asarray([float(bio_cfg['mode_load_weights'][m]) for m in MODES])
    operating=float(bio_cfg['regulation']['baseline_operating_fraction'])+float(bio_cfg['regulation']['acclimatized_operating_fraction'])*np.clip(acclim,0,1)
    divisor=1.0+float(bio_cfg['regulation']['load_reduction_gain'])*reg[0]*operating
    L=uptake[0]*np.sum(w[:,None]*coupling[0,:,None]*np.maximum(mode_opportunity[:,mask],0.0),axis=0)/divisor
    a,o,tolw,injw=win
    stim=np.zeros_like(L); stress=np.zeros_like(L); inj=np.zeros_like(L)
    def smooth(u):
        u=np.clip(u,0,1); return u*u*(3-2*u)
    m=(L>=a)&(L<o); u=(L-a)/max(o-a,1e-30); stim=np.where(m,smooth(u),stim)
    m=(L>=o)&(L<tolw); u=(L-o)/max(tolw-o,1e-30); s=smooth(u); stim=np.where(m,1-(1-float(bio_cfg['response']['post_optimum_stimulus_floor_at_tolerance']))*s,stim); stress=np.where(m,float(bio_cfg['response']['stress_at_tolerance'])*s,stress)
    m=(L>=tolw)&(L<injw); u=(L-tolw)/max(injw-tolw,1e-30); stim=np.where(m,float(bio_cfg['response']['post_optimum_stimulus_floor_at_tolerance'])*(1-u),stim); stress=np.where(m,float(bio_cfg['response']['stress_at_tolerance'])+(1-float(bio_cfg['response']['stress_at_tolerance']))*u,stress); inj=np.where(m,float(bio_cfg['response']['injury_risk_at_injury_threshold_minus'])*smooth(u),inj)
    m=L>=injw; u=np.maximum(L/injw-1,0); stress=np.where(m,1.0,stress); inj=np.where(m,1-np.exp(-float(bio_cfg['response']['post_injury_exponential_steepness'])*u),inj)
    wt=p[mask]/den
    return {'L_X':float(np.sum(wt*L)),'adaptive_stimulus':float(np.sum(wt*stim)),'stress':float(np.sum(wt*stress)),'injury_risk':float(np.sum(wt*inj)),'L_min':float(a),'L_opt':float(o),'L_tol':float(tolw),'L_injury':float(injw)}


def _frozen_exact_physiology(initial: np.ndarray, iface: Mapping[str,float], latent: np.ndarray,
                             bio_cfg: Mapping[str,Any], dt_years: float) -> np.ndarray:
    acc0,rem0,rec0,inj0=map(float,initial); dyn=bio_cfg['state_dynamics']; _,_,_,_,plastic,repair=_sigmoid_rows(np.asarray(latent,float).reshape(1,10)); plastic=float(plastic[0]); repair=float(repair[0])
    target_acc=float(np.clip((iface['L_X']-iface['L_min'])/max(iface['L_tol']-iface['L_min'],1e-30),0,1))
    tau_acc=float(dyn['acclimatization_tau_on_year'] if target_acc>acc0 else dyn['acclimatization_tau_off_year'])
    acc=target_acc+(acc0-target_acc)*math.exp(-dt_years/max(tau_acc,1e-30))
    rec_target=float(iface['stress']*iface['L_X']); tau_rec=float(dyn['recoverable_load_tau_year']); rec=rec_target+(rec0-rec_target)*math.exp(-dt_years/max(tau_rec,1e-30))
    kd=float(dyn['structural_remodeling_max_rate_per_year'])*plastic*float(iface['adaptive_stimulus']); ka=(1.0/max(float(dyn['structural_atrophy_tau_year']),1e-30)) if iface['adaptive_stimulus']<0.05 else 0.0; kr=kd+ka
    if kr>1e-30:
        req=kd/kr; rem=req+(rem0-req)*math.exp(-kr*dt_years)
    else: rem=rem0
    damage=float(iface['injury_risk'])*(1.0-0.7*repair); krep=repair/max(float(dyn['injury_repair_tau_year']),1e-30)
    if krep>1e-30:
        ieq=damage/krep; inj=ieq+(inj0-ieq)*math.exp(-krep*dt_years)
    else: inj=inj0+damage*dt_years
    return np.asarray([np.clip(acc,0,1),np.clip(rem,0,1),max(rec,0.0),np.clip(inj,0,1)],float)


def physiology_macrostep(population: np.ndarray, mode_opportunity: np.ndarray, latent_mean: np.ndarray,
                         bio_cfg: Mapping[str,Any], acclimatization: np.ndarray, remodeling: np.ndarray,
                         recoverable_load: np.ndarray, injury: np.ndarray, dt_years: float,
                         cfg: DeepRuntimeConfig) -> dict[str,Any]:
    """Macrostep-stable v0.4 physiology closure by analytic frozen-coefficient Picard solve.

    For long steps (>=10x the longest physiology timescale) the interface is solved at the
    endpoint, giving the self-consistent asymptotic state rather than Euler overshoot.
    For shorter steps a midpoint interface is used. No v0.4 biological coefficient changes.
    """
    cfg.validate(); pop=np.asarray(population,float); z=np.asarray(latent_mean,float); n=pop.shape[0]
    if z.shape!=(n,10): raise ValueError('latent shape mismatch')
    initial=np.stack([acclimatization,remodeling,recoverable_load,injury],axis=1).astype(float)
    if dt_years==0: return {'acclimatization':initial[:,0].copy(),'remodeling':initial[:,1].copy(),'recoverable_load':initial[:,2].copy(),'injury':initial[:,3].copy(),'iterations':0,'converged':True}
    dyn=bio_cfg['state_dynamics']; longest=max(float(dyn[k]) for k in ('acclimatization_tau_on_year','acclimatization_tau_off_year','recoverable_load_tau_year','structural_atrophy_tau_year','injury_repair_tau_year'))
    guess=initial.copy(); converged=False
    for it in range(1,cfg.physiology_fixed_point_max_iterations+1):
        eval_state=guess if dt_years>=cfg.physiology_long_step_tau_multiple*longest else 0.5*(initial+guess)
        nxt=np.empty_like(guess)
        for d in range(n):
            iface=_interface_summary_one(pop[d],mode_opportunity,z[d],bio_cfg,float(eval_state[d,0]),float(eval_state[d,1]))
            nxt[d]=_frozen_exact_physiology(initial[d],iface,z[d],bio_cfg,float(dt_years))
        err=float(np.max(np.abs(nxt-guess))) if nxt.size else 0.0
        guess=nxt
        if err<=cfg.physiology_fixed_point_tolerance:
            converged=True; break
    if not converged: raise RuntimeError('physiology macrostep fixed-point did not converge: FAIL_CLOSED')
    return {'acclimatization':guess[:,0],'remodeling':guess[:,1],'recoverable_load':guess[:,2],'injury':guess[:,3],'iterations':it,'converged':True}


def area_weights_from_lat(lat_deg: np.ndarray, nlon: int) -> np.ndarray:
    lat=np.asarray(lat_deg,float); w=np.maximum(np.cos(np.deg2rad(lat)),0.0)[:,None]*np.ones((1,int(nlon)))
    s=float(w.sum())
    if s<=0: raise ValueError('invalid latitude area weights')
    return w/s

class V05DeepFieldProvider:
    """Read-only v0.5/v0.3 field adapter. Geological keyframes use older-frame ZOH."""
    def __init__(self, deep_root: Path, *, photo_share: float=0.05):
        self.root=Path(deep_root); self.photo_share=float(photo_share)
        self.geo=np.load(self.root/'outputs/v0_3/DEEP_GEOLOGICAL_TRANSPORT_KEYFRAMES_210_0Ma_v0_3.npz',allow_pickle=False)
        self.eng=np.load(self.root/'outputs/v0_5/WORLD1_TIME_RESOLVED_DEEP_FREE_ENERGY_KEYFRAMES_v0_5.npz',allow_pickle=False)
        self.cal=json.loads((self.root/'outputs/v0_5/WORLD1_DEEP_FREE_ENERGY_CALIBRATION_v0_5.json').read_text())
        self.j_per_dfeu=float(self.cal['cha1_reference']['joule_per_global_dfeu'])
        self.total_per_mode=float(self.cal['background_total_reservoir_j']['E'])
        self.lat=np.asarray(self.eng['lat'],float); self.lon=np.asarray(self.eng['lon'],float); self.area=area_weights_from_lat(self.lat,len(self.lon))
    def _idx(self, age_ma: float) -> int:
        ages=np.asarray(self.eng['age_ma'],float)
        # Older-frame ZOH: choose nearest materialized age >= requested age; book edge clamps to 0.
        cand=np.where(ages>=float(age_ma)-1e-9)[0]
        return int(cand[np.argmin(ages[cand]-float(age_ma))]) if len(cand) else int(np.argmin(ages))
    def frame(self, age_ma: float) -> dict[str,np.ndarray|float|int]:
        i=self._idx(age_ma); u=np.asarray(self.eng['free_energy_excess_DFEU'][i],float).copy(); u[:2]*=(1.0+self.photo_share)
        ccar=np.stack([np.asarray(self.geo[f'C_car_{m}'][i],float) for m in MODES]); zeta=np.stack([np.asarray(self.geo[f'zeta_{m}'][i],float) for m in MODES]); ax=np.stack([np.asarray(self.geo[f'A_X_{m}'][i],float) for m in MODES])
        u_base=np.asarray(self.eng['free_energy_excess_DFEU'][i],float).copy()
        photo_u=np.zeros(5,float); photo_u[:2]=self.photo_share*u_base[:2]
        global_base=u_base*self.j_per_dfeu; eq_base=global_base[:,None,None]*self.area[None,:,:]
        eq_photo=(photo_u*self.j_per_dfeu)[:,None,None]*self.area[None,:,:]
        deep_global=np.maximum(self.total_per_mode-global_base,0.0); buf=deep_global[:,None,None]*self.area[None,:,:]
        return {'keyframe_index':i,'keyframe_age_ma':float(self.eng['age_ma'][i]),'u_base_dfeu':u_base,'photo_u_dfeu':photo_u,'C_car':ccar,'zeta':zeta,'A_X':ax,'mode_opportunity_equilibrium':ax*(u_base+photo_u)[:,None,None],'equilibrium_background_energy_j':eq_base,'photo_equilibrium_energy_j':eq_photo,'source_buffer_j':buf}


def initialize_runtime_state(deme_ids: Sequence[str], ecological_va: np.ndarray, ecological_scales: np.ndarray,
                             provider_frame: Mapping[str,Any], relative_year: float,
                             heritable_cfg: DeepHeritableConfig) -> DeepRuntimeState:
    ids=[str(x) for x in deme_ids]; q=initialize_latent_variance_from_d3(ecological_va,ecological_scales,heritable_cfg); eq=np.asarray(provider_frame['equilibrium_background_energy_j'],float); peq=np.asarray(provider_frame['photo_equilibrium_energy_j'],float); buf=np.asarray(provider_frame['source_buffer_j'],float)
    st=DeepRuntimeState(ids,np.zeros((len(ids),10)),q,np.zeros(len(ids)),np.zeros(len(ids)),np.zeros(len(ids)),np.zeros(len(ids)),eq.copy(),eq.copy(),peq.copy(),peq.copy(),buf.copy(),np.zeros(5),np.zeros(5),np.zeros(5),np.zeros(5),float(relative_year),None)
    st.validate(); return st


def reconcile_deme_state(state: DeepRuntimeState, new_deme_ids: Sequence[str], new_fission_events: Sequence[Mapping[str,Any]]) -> DeepRuntimeState:
    """Preserve surviving demes; clone parent moments/physiology into D3-authorized fission daughters."""
    state.validate(); old={d:i for i,d in enumerate(state.deme_ids)}; parent_for={str(e['daughter_deme_id']):str(e['parent_deme_id']) for e in new_fission_events}
    rows=[]
    for did0 in new_deme_ids:
        did=str(did0)
        if did in old: rows.append(old[did])
        elif did in parent_for and parent_for[did] in old: rows.append(old[parent_for[did]])
        else: raise RuntimeError(f'new D3 deme {did} has no authorized fission parent: FAIL_CLOSED')
    ix=np.asarray(rows,int)
    out=DeepRuntimeState([str(x) for x in new_deme_ids],state.latent_mean[ix].copy(),state.latent_va[ix].copy(),state.acclimatization[ix].copy(),state.remodeling[ix].copy(),state.recoverable_load[ix].copy(),state.injury[ix].copy(),state.surface_background_energy_j.copy(),state.equilibrium_background_energy_j.copy(),state.photo_energy_j.copy(),state.photo_equilibrium_energy_j.copy(),state.source_buffer_j.copy(),state.cumulative_gross_uptake_j.copy(),state.cumulative_return_flow_j.copy(),state.cumulative_net_sink_j.copy(),state.cumulative_stellar_pump_j.copy(),state.endpoint_relative_year,state.d3_runtime_state,state.schema_version)
    out.validate(); return out


def runtime_checkpoint_payload(state: DeepRuntimeState, source_fingerprint: Mapping[str,str]) -> dict[str,Any]:
    state.validate(); return {'schema':'ARCANA_DEEP_RUNTIME_CHECKPOINT_v0_6C','source_fingerprint':dict(source_fingerprint),'deep_state':state}

def restore_runtime_checkpoint(payload: Mapping[str,Any], expected_source_fingerprint: Mapping[str,str]) -> DeepRuntimeState:
    if payload.get('schema')!='ARCANA_DEEP_RUNTIME_CHECKPOINT_v0_6C': raise RuntimeError('unsupported Deep checkpoint schema: FAIL_CLOSED')
    if dict(payload.get('source_fingerprint',{}))!=dict(expected_source_fingerprint): raise RuntimeError('Deep checkpoint source fingerprint mismatch: FAIL_CLOSED')
    st=payload.get('deep_state')
    if not isinstance(st,DeepRuntimeState): raise RuntimeError('missing Deep runtime state: FAIL_CLOSED')
    st.validate(); return st


def bind_historical_210ma(d3_result: Any, *, physical_age_ma: float) -> None:
    if not math.isclose(float(physical_age_ma),210.0,abs_tol=1e-9): raise RuntimeError('historical HX initialization requires true 210 Ma D3 checkpoint: FAIL_CLOSED')
    required=('deme_ids','endpoint_population','endpoint_trait','endpoint_additive_variance','current_species_id')
    if any(not hasattr(d3_result,k) for k in required): raise RuntimeError('210 Ma object is not a D3 demographic checkpoint: FAIL_CLOSED')
    if np.asarray(d3_result.endpoint_population).ndim!=3: raise RuntimeError('210 Ma D3 checkpoint population raster missing: FAIL_CLOSED')


def _deep_demography_patch(original, deme_viability: np.ndarray):
    v=np.clip(np.asarray(deme_viability,float),0.0,1.0)
    def wrapped(pop, habitat, current_species, root_idx, root_species_ids, deme_guild, metadata, registry, sub, dt, cfg):
        base,opp=original(pop,habitat,current_species,root_idx,root_species_ids,deme_guild,metadata,registry,sub,dt,cfg)
        if len(v)!=len(current_species): raise RuntimeError('Deep viability/deme ordering mismatch: FAIL_CLOSED')
        n=np.asarray(pop,float).sum((1,2)); nb=np.asarray(base,float).sum((1,2)); out=np.asarray(pop,float).copy(); ids=np.asarray(current_species).astype(str)
        for sid in sorted(set(ids.tolist())):
            ix=np.where(ids==sid)[0]; cur=float(n[ix].sum()); bnew=float(nb[ix].sum())
            if cur<=0: continue
            root_sid=root_species_ids[int(root_idx[int(ix[0])])]; g=int(deme_guild[int(ix[0])])
            from arcana_worldsim.post_cha1 import dynamic_demes as dd
            tau=dd.DEFAULT_DEMOGRAPHIC_TAU_YR[g]/max(float(metadata[root_sid]['relative_reproduction_rate']),1e-6); a=1-math.exp(-float(dt)/max(tau,1e-9))
            target=cur if a<=1e-30 else cur+(bnew-cur)/a
            sv=float(np.sum(n[ix]*v[ix])/cur); tx=target*sv
            w=n[ix]*v[ix]; sw=float(w.sum()); td=(tx*w/sw) if sw>0 else np.zeros(len(ix))
            nd=n[ix]+a*(td-n[ix]); nd=np.maximum(nd,0.0)
            for j,x in enumerate(ix): out[x]*=float(nd[j])/max(float(n[x]),1e-15)
        return out,opp
    return wrapped


def run_d3_one_step(root: Path, cfg: Any, initial_result: Any, adapter: Any, *, end_relative_year: float,
                     d3_runtime_state: Mapping[str,Any]|None, deep_enabled: bool, deme_viability: np.ndarray|None=None):
    """One governed D3 step. Deep-OFF path is an exact unpatched D3 call."""
    from arcana_worldsim.post_cha1 import diversification_adequacy as da
    from arcana_worldsim.production_replay.orchestrator import run_variable_step, AbsoluteCadencePolicy
    start=float(initial_result.snapshot_relative_year[-1]); dt=float(end_relative_year)-start
    run_cfg=replace(cfg,start_relative_year=start,end_relative_year=float(end_relative_year),dt_years=dt)
    old_sub=da._substrate_for_cfg; old_dem=da._current_species_demography
    da._substrate_for_cfg=adapter.for_d3
    if deep_enabled:
        if deme_viability is None: raise ValueError('Deep-enabled step requires viability')
        da._current_species_demography=_deep_demography_patch(old_dem,deme_viability)
    try:
        result,rstate=run_variable_step(Path(root),run_cfg,initial_result,step_schedule=[(float(end_relative_year),dt)],cadence=AbsoluteCadencePolicy(),initial_pair_graph=None if d3_runtime_state is None else d3_runtime_state.get('pair_graph'),initial_contact_probability=None if d3_runtime_state is None else d3_runtime_state.get('contact_probability'),return_runtime_state=True,allow_d33_stability_extension=True)
    finally:
        da._substrate_for_cfg=old_sub; da._current_species_demography=old_dem
    return result,rstate

GOVERNANCE={
    'D3_source_modified':False,
    'runtime_patch_restored_required':True,
    'direct_Deep_speciation_operator':False,
    'Deep_latent_traits_inserted_into_D3_RI':False,
    'directional_mutation_operator':False,
    'photo_deep_additive_share_E_th':0.05,
    'historical_210Ma_proxy_allowed':False,
}

def effective_mode_opportunity(state: DeepRuntimeState, frame: Mapping[str,Any]) -> np.ndarray:
    """A_X times the currently remaining (background + photo) DFEU-equivalent energy."""
    ax=np.asarray(frame['A_X'],float); u0=np.asarray(frame['u_base_dfeu'],float); up=np.asarray(frame['photo_u_dfeu'],float)
    eb=np.asarray(frame['equilibrium_background_energy_j'],float); ep=np.asarray(frame['photo_equilibrium_energy_j'],float)
    rb=np.divide(state.surface_background_energy_j,eb,out=np.zeros_like(eb),where=eb>0)
    rp=np.divide(state.photo_energy_j,ep,out=np.zeros_like(ep),where=ep>0)
    ueff=u0[:,None,None]*rb+up[:,None,None]*rp
    return ax*ueff


def _reconcile_rows(old_ids: Sequence[str], new_ids: Sequence[str], rows: np.ndarray, fissions: Sequence[Mapping[str,Any]]) -> np.ndarray:
    old={str(d):i for i,d in enumerate(old_ids)}; pfor={str(e['daughter_deme_id']):str(e['parent_deme_id']) for e in fissions}; out=[]
    for d0 in new_ids:
        d=str(d0)
        if d in old: out.append(rows[old[d]])
        elif d in pfor and pfor[d] in old: out.append(rows[old[pfor[d]]])
        else: raise RuntimeError(f'cannot inherit row for new D3 deme {d}: FAIL_CLOSED')
    return np.asarray(out,float)


def _energy_ledger_step(state: DeepRuntimeState, frame: Mapping[str,Any], population: np.ndarray,
                        reference_population: np.ndarray, guild_id: np.ndarray, dt_years: float,
                        runtime_cfg: DeepRuntimeConfig, passive_cfg: PassiveUptakeConfig) -> tuple[np.ndarray,dict[str,Any]]:
    # New geological keyframe changes equilibrium targets, not actual stored energy instantaneously.
    state.equilibrium_background_energy_j=np.asarray(frame['equilibrium_background_energy_j'],float).copy()
    state.photo_equilibrium_energy_j=np.asarray(frame['photo_equilibrium_energy_j'],float).copy()
    # The finite deep source buffer is actual state. Do not reset it on keyframe transitions.
    opp0=effective_mode_opportunity(state,frame)
    pressure=biological_pressure(population,reference_population,guild_id,state.latent_mean,acclimatization=state.acclimatization)
    tau=np.asarray(runtime_cfg.restore_time_years,float)
    lam=local_passive_uptake_rate_per_year(pressure['mode_site_saturation'],np.asarray(frame['C_car'],float),np.asarray(frame['zeta'],float),tau,passive_cfg)
    bg=analytic_replenished_component_step(state.surface_background_energy_j,state.equilibrium_background_energy_j,tau[:,None,None],lam,dt_years,return_flow_fraction=runtime_cfg.return_flow_fraction,finite_source_buffer_j=state.source_buffer_j)
    ph=analytic_replenished_component_step(state.photo_energy_j,state.photo_equilibrium_energy_j,tau[:,None,None],lam,dt_years,return_flow_fraction=runtime_cfg.return_flow_fraction,finite_source_buffer_j=None)
    state.surface_background_energy_j=bg['surface_energy_after_j']; state.photo_energy_j=ph['surface_energy_after_j']; state.source_buffer_j=bg['source_buffer_after_j']
    gross=np.sum(bg['gross_uptake_j']+ph['gross_uptake_j'],axis=(1,2)); ret=np.sum(bg['return_flow_j']+ph['return_flow_j'],axis=(1,2)); net=np.sum(bg['net_biological_sink_j']+ph['net_biological_sink_j'],axis=(1,2)); stellar=np.sum(ph['source_restore_input_j'],axis=(1,2))
    state.cumulative_gross_uptake_j+=gross; state.cumulative_return_flow_j+=ret; state.cumulative_net_sink_j+=net; state.cumulative_stellar_pump_j+=stellar
    max_close=max(float(np.max(np.abs(bg['closure_error_j']))),float(np.max(np.abs(ph['closure_error_j']))))
    opp1=effective_mode_opportunity(state,frame); opp_mid=0.5*(opp0+opp1)
    return opp_mid,{'lambda_gross_max_per_year':float(np.max(lam)),'energy_closure_max_abs_j':max_close,'gross_uptake_j_by_mode':gross.tolist(),'net_sink_j_by_mode':net.tolist(),'stellar_pump_j_by_mode':stellar.tolist()}


def advance_deep_coupled_one_step(root: Path, d3_cfg: Any, initial_result: Any, adapter: Any,
                                  deep_provider: V05DeepFieldProvider, state: DeepRuntimeState,
                                  bio_cfg: Mapping[str,Any], ecological_scales: np.ndarray,
                                  *, end_relative_year: float, runtime_cfg: DeepRuntimeConfig=DeepRuntimeConfig(),
                                  passive_cfg: PassiveUptakeConfig=PassiveUptakeConfig(),
                                  heritable_cfg: DeepHeritableConfig=DeepHeritableConfig()) -> tuple[Any,DeepRuntimeState,dict[str,Any]]:
    """One production step integrating v0.6A energy + v0.6B genetics around SEALED D3.

    Deep OFF is a hard exact bypass: no energy, physiology, genetics or demography patch is evaluated.
    Deep ON order is: local energy/physiology/viability -> D3 demographic patch -> D3 governed step ->
    D3-authorized deme inheritance -> Deep selection/gene-flow/VA update.
    """
    runtime_cfg.validate(); state.validate(); start=float(initial_result.snapshot_relative_year[-1]); dt=float(end_relative_year)-start
    if dt<=0: raise ValueError('nonpositive runtime step')
    if state.deme_ids!=[str(x) for x in initial_result.deme_ids]: raise RuntimeError('Deep/D3 deme ordering mismatch: FAIL_CLOSED')
    if not runtime_cfg.deep_enabled:
        old_f=len(getattr(initial_result,'deme_fission_events',[])); old_ids=list(state.deme_ids)
        res,rs=run_d3_one_step(root,d3_cfg,initial_result,adapter,end_relative_year=end_relative_year,d3_runtime_state=state.d3_runtime_state,deep_enabled=False)
        newf=list(getattr(res,'deme_fission_events',[]))[old_f:]
        if [str(x) for x in res.deme_ids] != old_ids:
            state=reconcile_deme_state(state,res.deme_ids,newf)
        state.endpoint_relative_year=float(end_relative_year); state.d3_runtime_state=rs
        return res,state,{'deep_enabled':False,'exact_bypass':True,'new_fissions_inherited':len(newf)}
    age_start=66.0-start/1e6; frame=deep_provider.frame(age_start)
    sub=adapter.state_at_age(age_start); ref=np.asarray(sub['reference_population'],float)
    opp,ediag=_energy_ledger_step(state,frame,np.asarray(initial_result.endpoint_population,float),ref,np.asarray(initial_result.guild_id,int),dt,runtime_cfg,passive_cfg)
    phys=physiology_macrostep(np.asarray(initial_result.endpoint_population,float),opp,state.latent_mean,bio_cfg,state.acclimatization,state.remodeling,state.recoverable_load,state.injury,dt,runtime_cfg)
    state.acclimatization=phys['acclimatization']; state.remodeling=phys['remodeling']; state.recoverable_load=phys['recoverable_load']; state.injury=phys['injury']
    logv=deme_mean_log_viability(initial_result.endpoint_population,opp,state.latent_mean,bio_cfg,state.acclimatization,state.remodeling); viability=np.exp(logv)
    grad=viability_selection_gradient(initial_result.endpoint_population,opp,state.latent_mean,bio_cfg,heritable_cfg,state.acclimatization,state.remodeling)
    zsel=selection_response_step(state.latent_mean,state.latent_va,grad,dt,heritable_cfg)
    # Make selected means the pre-event state so an authorized fission daughter inherits them.
    state.latent_mean=zsel
    old_f=len(getattr(initial_result,'deme_fission_events',[]))
    res,rs=run_d3_one_step(root,d3_cfg,initial_result,adapter,end_relative_year=end_relative_year,d3_runtime_state=state.d3_runtime_state,deep_enabled=True,deme_viability=viability)
    newf=list(getattr(res,'deme_fission_events',[]))[old_f:]
    old_ids=list(state.deme_ids); state=reconcile_deme_state(state,res.deme_ids,newf); grad2=_reconcile_rows(old_ids,res.deme_ids,grad,newf)
    n=np.asarray(res.endpoint_population,float).sum((1,2)); zflow,vflow,gdiag=gene_flow_moment_mix(state.latent_mean,state.latent_va,n,np.asarray(res.endpoint_contact_connectivity,float),np.asarray(res.endpoint_intrinsic_RI,float),np.asarray(res.root_species_index,int),heritable_cfg)
    state.latent_mean=zflow
    state.latent_va=advance_latent_variance(vflow,grad2,n,np.asarray(res.generation_time_proxy_years,float),dt,heritable_cfg)
    state.endpoint_relative_year=float(end_relative_year); state.d3_runtime_state=rs
    diag={'deep_enabled':True,'age_start_ma':age_start,'deep_keyframe_age_ma':frame['keyframe_age_ma'],'physiology_iterations':int(phys['iterations']),'viability_min':float(np.min(viability)),'viability_mean':float(np.mean(viability)),'gradient_max_abs':float(np.max(np.abs(grad))),'gene_flow_first_moment_closure':gdiag['first_moment_conservation_max_abs'],'gene_flow_second_moment_closure':gdiag['second_moment_conservation_max_abs'],'new_fissions_inherited':len(newf),**ediag}
    return res,state,diag
