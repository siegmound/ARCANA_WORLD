from __future__ import annotations

from typing import Any
import numpy as np

from .segregation_aware_admixture import transform_segregation_potential, validate_segregation_potential
from .segregation_potential_lifecycle import drift_retention_factor


def advance_neutral_world_interval_shadow(
    va_within_before_flow: np.ndarray,
    segregation_potential_before_flow: np.ndarray,
    interval_transition: np.ndarray,
    effective_size: np.ndarray,
    generation_time_years: np.ndarray,
    dt_years: float,
) -> tuple[np.ndarray,np.ndarray,dict[str,Any]]:
    """Non-canonical World-1 interval shadow update for neutral VA/S.

    This mirrors the *existing* WorldSim operator granularity rather than the
    generation-scale B2 protocol: one finite-step migration transition is
    applied first, then the already-authoritative D3.3A exponential drift loss
    over `dt_years`.  It is a shadow diagnostic only.

    Directional-selection movement in latent genetic space is deliberately not
    included because R3.7B has no dynamic NEMO authorization for K_eff.  The
    function therefore cannot authorize canonical writes or replace the R3.5
    runtime yet.
    """
    v=np.asarray(va_within_before_flow,float)
    s=np.asarray(segregation_potential_before_flow,float)
    p=np.asarray(interval_transition,float)
    ne=np.asarray(effective_size,float)
    gt=np.asarray(generation_time_years,float)
    if v.ndim!=2 or s.shape!=(v.shape[0],v.shape[0],v.shape[1]):
        raise ValueError('VA/S shape mismatch')
    n,t=v.shape
    if p.shape!=(n,n) or np.min(p)<-1e-12 or not np.allclose(p.sum(axis=1),1.0,atol=1e-12,rtol=0):
        raise ValueError('interval transition must be row stochastic')
    if ne.shape!=(n,) or gt.shape!=(n,) or np.any(ne<=0) or np.any(gt<=0) or dt_years<0:
        raise ValueError('invalid Ne/generation-time/dt')
    validate_segregation_potential(s,tolerance=1e-8)

    genic=0.5*np.einsum('ij,ik,jkt->it',p,p,s,optimize=True)
    va_mix=p@v+genic
    s_mix=transform_segregation_potential(s,p,tolerance=1e-8)
    retention=drift_retention_factor(ne,gt,float(dt_years))
    loss=va_mix*(1.0-retention[:,None])
    va_out=np.maximum(va_mix-loss,0.0)
    s_out=s_mix.copy()
    for ti in range(t):
        inc=loss[:,ti,None]+loss[None,:,ti]
        np.fill_diagonal(inc,0.0)
        s_out[:,:,ti]+=inc
    validate_segregation_potential(s_out,tolerance=1e-7)
    return va_out,s_out,{
        'semantic_status':'R3_7B_NEUTRAL_WORLD_INTERVAL_SHADOW_ONLY',
        'migration_genic_injection_total':np.sum(genic,axis=0).tolist(),
        'drift_va_loss_total':np.sum(loss,axis=0).tolist(),
        'drift_authority':'D3_3A_EXPONENTIAL_RETENTION_REUSED',
        'selection_latent_displacement_included':False,
        'selection_K_eff_authorized':False,
        'canonical_write_allowed':False,
        'production_runtime_replacement_authorized':False,
    }
