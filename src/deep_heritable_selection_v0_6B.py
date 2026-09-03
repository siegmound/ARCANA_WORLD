from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any, Sequence
import math
import numpy as np

from deep_d3_coupling_v0_6A import LATENT_TRAITS, MODES, phenotype_from_latent

STATUS = "PASS_HERITABLE_SELECTION_SIDECAR_CANDIDATE"

@dataclass(frozen=True)
class DeepHeritableConfig:
    mutation_variance_supply_normalized_per_myr: float = 0.002
    mutation_variance_ceiling_normalized: float = 0.05
    selection_variance_depletion_per_generation: float = 2.0e-8
    selection_pressure_ceiling: float = 4.0
    drift_individual_equivalents_per_population_unit: float = 250_000_000.0
    drift_min_effective_size: float = 500.0
    maximum_total_exchange_fraction_per_deme: float = 0.45
    trait_response_timescale_years: float = 300_000.0
    selection_gradient_epsilon_latent: float = 0.02
    selection_gradient_clip: float = 4.0
    initial_variance_floor_normalized: float = 1.0e-6
    variance_homeostasis_enabled: bool = True
    nonlinear_stabilizing_variance_depletion_per_myr_per_q: float = 0.9876543209876544

    def validate(self):
        if self.mutation_variance_supply_normalized_per_myr < 0: raise ValueError("mutation variance supply <0")
        if self.mutation_variance_ceiling_normalized <= 0: raise ValueError("variance ceiling <=0")
        if self.drift_individual_equivalents_per_population_unit <= 0: raise ValueError("invalid Ne calibration")
        if self.trait_response_timescale_years <= 0: raise ValueError("invalid trait timescale")
        if self.selection_gradient_epsilon_latent <= 0: raise ValueError("invalid epsilon")


def initialize_latent_variance_from_d3(ecological_va: np.ndarray, ecological_scales: np.ndarray,
                                       cfg: DeepHeritableConfig) -> np.ndarray:
    """Initialize Deep standing VA from existing normalized D3 standing VA.

    This transfers only a dimensionless variance scale. It does not map D3 ecological
    trait identities onto Deep trait directions and introduces no directional mean.
    """
    cfg.validate()
    va=np.maximum(np.asarray(ecological_va,dtype=float),0.0)
    sc=np.maximum(np.asarray(ecological_scales,dtype=float),1e-12)
    if va.ndim!=2 or va.shape[1]!=3 or sc.shape!=va.shape: raise ValueError("expected [deme,3]")
    q=va/(sc*sc)
    q0=np.median(q,axis=1)
    q0=np.clip(q0,cfg.initial_variance_floor_normalized,cfg.mutation_variance_ceiling_normalized)
    return np.repeat(q0[:,None],len(LATENT_TRAITS),axis=1)


def _phenotype_rows(z: np.ndarray):
    z=np.asarray(z,float)
    sig=1.0/(1.0+np.exp(-z))
    return sig[:,:5],sig[:,5],sig[:,6],sig[:,7],sig[:,8],sig[:,9]


def _window_for_rows(z: np.ndarray, bio_cfg: Mapping[str,Any], acclim: np.ndarray, remodel: np.ndarray):
    coupling,uptake,reg,tol,plastic,repair=_phenotype_rows(z)
    p=bio_cfg['tolerance_scale']; b=bio_cfg['threshold_base_load_units']
    scale=(float(p['intercept'])+float(p['heritable_tolerance'])*tol
           +float(p['persistent_remodeling'])*np.clip(remodel,0,1)
           +float(p['reversible_acclimatization_x_regulation'])*np.clip(acclim,0,1)*reg)
    return np.stack([float(b[k])*scale for k in ('L_min','L_opt','L_tol','L_injury')],axis=1)


def _maintenance_cost_rows(z: np.ndarray, bio_cfg: Mapping[str,Any]):
    coupling,uptake,reg,tol,plastic,repair=_phenotype_rows(z)
    c=bio_cfg['response']['maintenance_cost']
    return (float(c['coupling'])*np.mean(coupling*coupling,axis=1)
            +float(c['regulation'])*reg*reg+float(c['tolerance'])*tol*tol+float(c['repair'])*repair*repair)


def _viability_for_deme_cells(latent: np.ndarray, mode_opportunity_cells: np.ndarray,
                              bio_cfg: Mapping[str,Any], acclim: float=0.0, remodel: float=0.0) -> np.ndarray:
    """v0.4-equivalent viability on occupied cells.

    mode_opportunity_cells is [5,ncell] and equals A_X,a * u_X,a. This preserves
    the v0.4 separation: geological A_X is not energy; the product is formed only
    after an explicit energy field is supplied.
    """
    z=np.asarray(latent,float).reshape(1,10)
    coupling,uptake,reg,tol,plastic,repair=_phenotype_rows(z)
    w=np.asarray([float(bio_cfg['mode_load_weights'][m]) for m in MODES])
    operating=float(bio_cfg['regulation']['baseline_operating_fraction'])+float(bio_cfg['regulation']['acclimatized_operating_fraction'])*float(np.clip(acclim,0,1))
    divisor=1.0+float(bio_cfg['regulation']['load_reduction_gain'])*float(reg[0])*operating
    L=float(uptake[0])*np.sum(w[:,None]*coupling[0,:,None]*np.maximum(mode_opportunity_cells,0.0),axis=0)/divisor
    win=_window_for_rows(z,bio_cfg,np.array([acclim]),np.array([remodel]))[0]
    a,b,c,d=win
    stress=np.zeros_like(L); inj=np.zeros_like(L)
    def smooth(u):
        u=np.clip(u,0,1); return u*u*(3-2*u)
    m=(L>=b)&(L<c); u=(L-b)/max(c-b,1e-30); s=smooth(u); stress=np.where(m,float(bio_cfg['response']['stress_at_tolerance'])*s,stress)
    m=(L>=c)&(L<d); u=(L-c)/max(d-c,1e-30); stress=np.where(m,float(bio_cfg['response']['stress_at_tolerance'])+(1-float(bio_cfg['response']['stress_at_tolerance']))*u,stress); inj=np.where(m,float(bio_cfg['response']['injury_risk_at_injury_threshold_minus'])*smooth(u),inj)
    m=L>=d; u=np.maximum(L/d-1,0); stress=np.where(m,1.0,stress); inj=np.where(m,1.0-np.exp(-float(bio_cfg['response']['post_injury_exponential_steepness'])*u),inj)
    cost=float(_maintenance_cost_rows(z,bio_cfg)[0])
    V=np.exp(-float(bio_cfg['response']['viability_stress_cost'])*stress-float(bio_cfg['response']['viability_injury_cost'])*inj-cost)
    return np.clip(V,1e-300,1.0)


def deme_mean_log_viability(population: np.ndarray, mode_opportunity: np.ndarray, latent_mean: np.ndarray,
                            bio_cfg: Mapping[str,Any], acclimatization: np.ndarray|float=0.0,
                            remodeling: np.ndarray|float=0.0) -> np.ndarray:
    pop=np.maximum(np.asarray(population,float),0.0)
    opp=np.maximum(np.asarray(mode_opportunity,float),0.0)
    z=np.asarray(latent_mean,float)
    if pop.ndim!=3 or opp.shape!=(5,*pop.shape[1:]) or z.shape!=(pop.shape[0],10): raise ValueError("shape mismatch")
    acc=np.broadcast_to(np.asarray(acclimatization,float),(pop.shape[0],))
    rem=np.broadcast_to(np.asarray(remodeling,float),(pop.shape[0],))
    out=np.zeros(pop.shape[0],float)
    for d in range(pop.shape[0]):
        p=pop[d]; mask=p>0; n=float(p[mask].sum())
        if n<=0: continue
        v=_viability_for_deme_cells(z[d],opp[:,mask],bio_cfg,float(acc[d]),float(rem[d]))
        out[d]=float(np.sum(p[mask]*np.log(v))/n)
    return out


def viability_selection_gradient(population: np.ndarray, mode_opportunity: np.ndarray, latent_mean: np.ndarray,
                                 bio_cfg: Mapping[str,Any], cfg: DeepHeritableConfig,
                                 acclimatization: np.ndarray|float=0.0, remodeling: np.ndarray|float=0.0) -> np.ndarray:
    """Central finite-difference gradient of population-weighted mean log viability."""
    cfg.validate(); z=np.asarray(latent_mean,float); eps=cfg.selection_gradient_epsilon_latent
    grad=np.zeros_like(z)
    for k in range(z.shape[1]):
        zp=z.copy(); zm=z.copy(); zp[:,k]+=eps; zm[:,k]-=eps
        fp=deme_mean_log_viability(population,mode_opportunity,zp,bio_cfg,acclimatization,remodeling)
        fm=deme_mean_log_viability(population,mode_opportunity,zm,bio_cfg,acclimatization,remodeling)
        grad[:,k]=(fp-fm)/(2*eps)
    return np.clip(grad,-cfg.selection_gradient_clip,cfg.selection_gradient_clip)


def selection_response_step(latent_mean: np.ndarray, latent_va: np.ndarray, gradient: np.ndarray,
                            dt_years: float, cfg: DeepHeritableConfig,
                            relative_reproduction_rate: np.ndarray|float=1.0) -> np.ndarray:
    """D3-style variance-limited response. Mutation never appears in this mean update."""
    if dt_years<0: raise ValueError("negative dt")
    z=np.asarray(latent_mean,float); va=np.maximum(np.asarray(latent_va,float),0.0); g=np.asarray(gradient,float)
    rel=np.broadcast_to(np.asarray(relative_reproduction_rate,float),(z.shape[0],))
    tau=cfg.trait_response_timescale_years/np.maximum(rel,1e-9)
    beta=1.0-np.exp(-float(dt_years)/tau)
    gain=np.clip(va,0.0,0.25)
    return z+beta[:,None]*gain*np.clip(g,-cfg.selection_gradient_clip,cfg.selection_gradient_clip)


def advance_latent_variance(latent_va: np.ndarray, gradient: np.ndarray, population_total: np.ndarray,
                            generation_time_years: np.ndarray, dt_years: float,
                            cfg: DeepHeritableConfig) -> np.ndarray:
    """Zero-mean mutation + expected drift + selection + D3.3A long-horizon VA homeostasis.

    The default follows the final D3.3A semantics: dq/dt = mu - a*q - b*q^2,
    where b is the already-calibrated normalized stabilizing depletion coefficient.
    No term moves the latent mean.
    """
    cfg.validate(); q0=np.maximum(np.asarray(latent_va,float),0.0); gr=np.asarray(gradient,float)
    n=np.maximum(np.asarray(population_total,float),0.0); gt=np.maximum(np.asarray(generation_time_years,float),1e-9)
    if q0.shape!=gr.shape or q0.shape[0]!=len(n) or len(n)!=len(gt): raise ValueError("shape mismatch")
    ne=np.maximum(cfg.drift_min_effective_size,n*cfg.drift_individual_equivalents_per_population_unit)
    lam_drift=1.0/(2.0*ne*gt)
    pressure=np.clip(gr*gr,0.0,cfg.selection_pressure_ceiling)
    lam_sel=cfg.selection_variance_depletion_per_generation*pressure/gt[:,None]
    a=lam_sel+lam_drift[:,None]
    mu=cfg.mutation_variance_supply_normalized_per_myr/1_000_000.0
    dt=max(float(dt_years),0.0)
    if not cfg.variance_homeostasis_enabled or cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q<=0:
        e=np.exp(-a*dt); q=np.empty_like(q0); small=a<1e-30
        q[small]=q0[small]+mu*dt
        q[~small]=q0[~small]*e[~small]+(mu/a[~small])*(1.0-e[~small])
        return np.clip(q,0.0,cfg.mutation_variance_ceiling_normalized)
    b=float(cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q)/1_000_000.0
    q=np.empty_like(q0)
    for i in range(q0.shape[0]):
        for k in range(q0.shape[1]):
            ai=float(a[i,k]); disc=math.sqrt(max(ai*ai+4.0*b*mu,0.0))
            if disc<1e-30: q[i,k]=q0[i,k]; continue
            rp=(-ai+disc)/(2.0*b); rn=(-ai-disc)/(2.0*b)
            den0=float(q0[i,k]-rn); c0=0.0 if abs(den0)<1e-30 else float((q0[i,k]-rp)/den0)
            c=c0*math.exp(-disc*dt); den=1.0-c
            q[i,k]=rp if abs(den)<1e-30 else (rp-c*rn)/den
    return np.clip(q,0.0,cfg.mutation_variance_ceiling_normalized)


def gene_flow_moment_mix(latent_mean: np.ndarray, latent_va: np.ndarray, population_total: np.ndarray,
                         gene_flow: np.ndarray, intrinsic_ri: np.ndarray, root_species_index: np.ndarray,
                         cfg: DeepHeritableConfig):
    """Same conservative first/second-moment exchange semantics as D3 additive_variance."""
    z=np.asarray(latent_mean,float); v=np.maximum(np.asarray(latent_va,float),0.0); n=np.maximum(np.asarray(population_total,float),0.0)
    nd,nt=z.shape; first=n[:,None]*z; second=n[:,None]*(v+z*z); df=np.zeros_like(first); ds=np.zeros_like(second)
    edges=[]; outgoing=np.zeros(nd,float)
    for i in range(nd):
        if n[i]<=0: continue
        for j in range(i+1,nd):
            if root_species_index[i]!=root_species_index[j] or n[j]<=0: continue
            mix=float(gene_flow[i,j])*(1.0-float(intrinsic_ri[i,j]));
            if mix<=0: continue
            harmonic=2*n[i]*n[j]/max(n[i]+n[j],1e-30); x=max(0.0,mix*harmonic)
            if x<=0: continue
            edges.append((i,j,x)); outgoing[i]+=x; outgoing[j]+=x
    total=0.0
    for i,j,x0 in edges:
        si=1.0 if outgoing[i]<=0 else min(1.0,cfg.maximum_total_exchange_fraction_per_deme*n[i]/outgoing[i])
        sj=1.0 if outgoing[j]<=0 else min(1.0,cfg.maximum_total_exchange_fraction_per_deme*n[j]/outgoing[j])
        x=x0*min(si,sj); total+=x
        df[i]+=x*(z[j]-z[i]); df[j]+=x*(z[i]-z[j])
        m2i=v[i]+z[i]*z[i]; m2j=v[j]+z[j]*z[j]
        ds[i]+=x*(m2j-m2i); ds[j]+=x*(m2i-m2j)
    fn=first+df; sn=second+ds; zn=z.copy(); vn=v.copy(); alive=n>0
    zn[alive]=fn[alive]/n[alive,None]; vn[alive]=sn[alive]/n[alive,None]-zn[alive]*zn[alive]; vn=np.maximum(vn,0.0)
    return zn,vn,{"total_pair_exchange_mass":float(total),"first_moment_conservation_max_abs":float(np.max(np.abs(fn.sum(0)-first.sum(0)))) if nd else 0.0,"second_moment_conservation_max_abs":float(np.max(np.abs(sn.sum(0)-second.sum(0)))) if nd else 0.0,"edge_count":len(edges)}


def inherit_founder_moments(parent_indices: Sequence[int], founder_weights: Sequence[float],
                            latent_mean: np.ndarray, latent_va: np.ndarray):
    idx=np.asarray(parent_indices,int); w=np.maximum(np.asarray(founder_weights,float),0.0)
    if len(idx)==0 or w.shape!=(len(idx),) or float(w.sum())<=0: raise ValueError("invalid founders")
    w=w/w.sum(); z=np.asarray(latent_mean,float)[idx]; v=np.asarray(latent_va,float)[idx]
    mu=np.sum(w[:,None]*z,axis=0); second=np.sum(w[:,None]*(v+z*z),axis=0)
    return mu,np.maximum(second-mu*mu,0.0)


def species_and_deme_viability(population_total: np.ndarray, current_species_id: Sequence[str],
                               deme_log_viability: np.ndarray):
    n=np.maximum(np.asarray(population_total,float),0.0); V=np.exp(np.asarray(deme_log_viability,float))
    ids=np.asarray(current_species_id).astype(str); species={}
    for sid in sorted(set(ids.tolist())):
        ix=np.where(ids==sid)[0]; den=float(n[ix].sum()); species[sid]=1.0 if den<=0 else float(np.sum(n[ix]*V[ix])/den)
    return V,species


def deep_demographic_targets(d3_species_targets: Mapping[str,float], population_total: np.ndarray,
                             current_species_id: Sequence[str], deme_viability: np.ndarray,
                             *, deep_enabled: bool):
    """Species target and within-species deme allocation; exact D3 proportional rule if OFF."""
    n=np.maximum(np.asarray(population_total,float),0.0); ids=np.asarray(current_species_id).astype(str); v=np.clip(np.asarray(deme_viability,float),0.0,1.0)
    if n.shape!=v.shape or ids.shape!=n.shape: raise ValueError("shape mismatch")
    out=np.zeros_like(n); starget={}
    for sid,target0 in d3_species_targets.items():
        ix=np.where(ids==str(sid))[0]
        if len(ix)==0: continue
        target=float(target0); ns=float(n[ix].sum())
        if not deep_enabled:
            starget[str(sid)]=target
            if ns>0: out[ix]=target*n[ix]/ns
            continue
        sv=1.0 if ns<=0 else float(np.sum(n[ix]*v[ix])/ns); targetx=target*sv; starget[str(sid)]=targetx
        w=n[ix]*v[ix]; sw=float(w.sum())
        if sw>0: out[ix]=targetx*w/sw
    return {"species_target":starget,"deme_target":out,"deep_off_exact_bypass":not deep_enabled}


def checkpoint_payload(latent_mean,latent_va,acclimatization,remodeling,recoverable_load,injury):
    return {"deep_latent_mean":np.asarray(latent_mean,float),"deep_latent_additive_variance":np.asarray(latent_va,float),"deep_acclimatization":np.asarray(acclimatization,float),"deep_remodeling":np.asarray(remodeling,float),"deep_recoverable_load":np.asarray(recoverable_load,float),"deep_injury":np.asarray(injury,float)}

GOVERNANCE={
 "D3_source_modified":False,
 "Deep_latent_traits_inserted_into_D3_RI":False,
 "direct_Deep_speciation_operator":False,
 "directional_mutation_operator":False,
 "mutation_mean_shift":0.0,
 "drift_Ne_proxy_domain":"GENETICS_ONLY_NOT_ENERGY",
 "photo_deep_additive_share_E_th":0.05,
}
