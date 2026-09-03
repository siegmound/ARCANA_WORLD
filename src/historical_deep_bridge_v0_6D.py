from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence
import copy
import numpy as np

from deep_production_runtime_v0_6C import DeepRuntimeState

STATUS = "PASS_HISTORICAL_BRIDGE_MECHANICS_D2_LINEAGE_INHERITANCE_CHA1_PULSE_AND_REAL_D22_TO_D3_TRANSFER_CANDIDATE__EXECUTABLE_D1_D2_RUNTIME_BINDING_PENDING"

LATENT_DIM = 10

@dataclass
class HistoricalLineageSidecar:
    """Representation-independent Deep biological state keyed by biological lineage/species id.

    This is intentionally not a D3 deme state.  D1/D2 may carry species/lineage level
    states; D3 demes are created only by the post-CHA1 spatial bridge/SEALED D3 authority.
    """
    species_ids: list[str]
    latent_mean: np.ndarray
    latent_va: np.ndarray
    acclimatization: np.ndarray
    remodeling: np.ndarray
    recoverable_load: np.ndarray
    injury: np.ndarray
    schema_version: str = "v0.6D"
    provenance: list[str] | None = None

    def validate(self) -> None:
        n=len(self.species_ids)
        if len(set(self.species_ids))!=n: raise ValueError("duplicate species ids")
        if self.latent_mean.shape!=(n,LATENT_DIM) or self.latent_va.shape!=(n,LATENT_DIM):
            raise ValueError("historical latent shape mismatch")
        for x in (self.acclimatization,self.remodeling,self.recoverable_load,self.injury):
            if np.asarray(x).shape!=(n,): raise ValueError("historical physiology shape mismatch")
        if np.any(self.latent_va<0): raise ValueError("negative historical VA")
        if np.any(self.injury<0) or np.any(self.injury>1): raise ValueError("invalid injury")
        if self.provenance is not None and len(self.provenance)!=n: raise ValueError("historical provenance shape mismatch")

@dataclass
class HistoricalEnergyState:
    """Physical Deep ledger independent of D1/D2/D3 biological representation."""
    surface_background_energy_j: np.ndarray
    equilibrium_background_energy_j: np.ndarray
    photo_energy_j: np.ndarray
    photo_equilibrium_energy_j: np.ndarray
    source_buffer_j: np.ndarray
    cumulative_gross_uptake_j: np.ndarray
    cumulative_return_flow_j: np.ndarray
    cumulative_net_sink_j: np.ndarray
    cumulative_stellar_pump_j: np.ndarray

    def validate(self) -> None:
        sh=np.asarray(self.surface_background_energy_j).shape
        if len(sh)!=3 or sh[0]!=5: raise ValueError("invalid historical energy shape")
        for x in (self.equilibrium_background_energy_j,self.photo_energy_j,self.photo_equilibrium_energy_j,self.source_buffer_j):
            if np.asarray(x).shape!=sh: raise ValueError("historical energy shape mismatch")
        for x in (self.surface_background_energy_j,self.photo_energy_j,self.source_buffer_j):
            if np.any(np.asarray(x)<0): raise ValueError("negative historical Deep energy")
        for x in (self.cumulative_gross_uptake_j,self.cumulative_return_flow_j,self.cumulative_net_sink_j,self.cumulative_stellar_pump_j):
            if np.asarray(x).shape!=(5,): raise ValueError("invalid cumulative ledger shape")


def validate_d1_metadata(species_metadata: Sequence[Mapping[str,Any]], *, expected_count: int=120) -> list[str]:
    """Bind the real D1 identity surface only; never reconstruct missing D1 populations."""
    if len(species_metadata)!=expected_count:
        raise RuntimeError(f"D1 metadata count {len(species_metadata)} != {expected_count}: FAIL_CLOSED")
    ids=[]
    for row in species_metadata:
        sid=str(row.get('species_id',''))
        if not sid: raise RuntimeError("D1 species id missing: FAIL_CLOSED")
        if row.get('ancestral_status')!='initial_effective_species':
            raise RuntimeError(f"D1 {sid} not initial_effective_species: FAIL_CLOSED")
        if bool(row.get('Deep_adapted',False)):
            raise RuntimeError(f"D1 {sid} pre-labelled Deep-adapted: FAIL_CLOSED")
        ids.append(sid)
    if len(set(ids))!=len(ids): raise RuntimeError("duplicate D1 species id: FAIL_CLOSED")
    return ids


def initialize_historical_sidecar(species_ids: Sequence[str], latent_va: np.ndarray) -> HistoricalLineageSidecar:
    """Initialize means at neutral latent zero, but require externally grounded standing VA.

    v0.6D deliberately has no fallback constant VA because the mounted R2 package contains
    D1 identities but not the production D1/D2 210 Ma standing-variance state.
    """
    ids=[str(x) for x in species_ids]
    va=np.asarray(latent_va,float)
    if va.shape!=(len(ids),LATENT_DIM):
        raise RuntimeError("historical initialization requires real/derived D1 Deep VA [species,10]: FAIL_CLOSED")
    if np.any(va<0): raise RuntimeError("negative D1 Deep VA: FAIL_CLOSED")
    st=HistoricalLineageSidecar(ids,np.zeros_like(va),va.copy(),np.zeros(len(ids)),np.zeros(len(ids)),np.zeros(len(ids)),np.zeros(len(ids)),provenance=['D1_EXPLICIT']*len(ids))
    st.validate(); return st


def filter_to_authoritative_survivors(sidecar: HistoricalLineageSidecar, survivor_species_ids: Sequence[str],
                                      *, authorized_proxy_parent: Mapping[str,str]|None=None) -> HistoricalLineageSidecar:
    """D2.2 decides survivors; copy exact state by ID, with explicit structural proxy only when authorized.

    The proxy path exists for legacy D2 children whose independent trait state was not exported
    (currently HSG_025 <- HSG_003 in the real D3 bridge).  It is structural-only and is not
    authorization to label the resulting Deep state historical HX.
    """
    sidecar.validate(); surv=[str(x) for x in survivor_species_ids]; proxies={} if authorized_proxy_parent is None else {str(k):str(v) for k,v in authorized_proxy_parent.items()}
    if len(set(surv))!=len(surv): raise RuntimeError("duplicate D2.2 survivor id: FAIL_CLOSED")
    old={sid:i for i,sid in enumerate(sidecar.species_ids)}
    rows=[]; prov=[]
    source_prov=sidecar.provenance or ['UNSPECIFIED']*len(sidecar.species_ids)
    for sid in surv:
        if sid in old:
            rows.append(old[sid]); prov.append(source_prov[old[sid]])
        elif sid in proxies and proxies[sid] in old:
            rows.append(old[proxies[sid]]); prov.append(f'STRUCTURAL_PARENT_PROXY_{proxies[sid]}_FOR_{sid}_NOT_HISTORICAL_DEEP_STATE')
        else:
            raise RuntimeError(f"D2.2 survivor missing from historical sidecar: {sid}: FAIL_CLOSED")
    ix=np.asarray(rows,int)
    out=HistoricalLineageSidecar(surv,sidecar.latent_mean[ix].copy(),sidecar.latent_va[ix].copy(),sidecar.acclimatization[ix].copy(),sidecar.remodeling[ix].copy(),sidecar.recoverable_load[ix].copy(),sidecar.injury[ix].copy(),provenance=prov)
    out.validate(); return out

def energy_from_runtime(state: DeepRuntimeState) -> HistoricalEnergyState:
    state.validate()
    out=HistoricalEnergyState(state.surface_background_energy_j.copy(),state.equilibrium_background_energy_j.copy(),state.photo_energy_j.copy(),state.photo_equilibrium_energy_j.copy(),state.source_buffer_j.copy(),state.cumulative_gross_uptake_j.copy(),state.cumulative_return_flow_j.copy(),state.cumulative_net_sink_j.copy(),state.cumulative_stellar_pump_j.copy())
    out.validate(); return out


def expand_survivors_to_d3_demes(sidecar: HistoricalLineageSidecar, energy: HistoricalEnergyState,
                                   deme_seed_registry: Mapping[str,Any], *, endpoint_relative_year: float,
                                   d3_runtime_state: Mapping[str,Any]|None=None) -> DeepRuntimeState:
    """Clone each survivor's moments/physiology into D3-authorized deme seeds.

    This operation has no birth/speciation authority.  Every seed must cite one of the
    already-authoritative D2.2 survivor species.
    """
    sidecar.validate(); energy.validate()
    demes=list(deme_seed_registry.get('demes',[]))
    if not demes: raise RuntimeError("empty D3 deme seed registry: FAIL_CLOSED")
    old={sid:i for i,sid in enumerate(sidecar.species_ids)}
    ids=[]; rows=[]
    for d in demes:
        if d.get('semantic_status')!='DERIVED_INITIAL_DEME_SEED_NOT_A_SPECIES':
            raise RuntimeError("D3 seed semantics not derived-deme-only: FAIL_CLOSED")
        sid=str(d.get('species_id','')); did=str(d.get('deme_seed_id',''))
        if sid not in old: raise RuntimeError(f"D3 seed parent {sid} is not a D2.2 survivor: FAIL_CLOSED")
        if not did: raise RuntimeError("D3 seed id missing: FAIL_CLOSED")
        ids.append(did); rows.append(old[sid])
    if len(set(ids))!=len(ids): raise RuntimeError("duplicate D3 seed id: FAIL_CLOSED")
    ix=np.asarray(rows,int)
    st=DeepRuntimeState(
        deme_ids=ids,
        latent_mean=sidecar.latent_mean[ix].copy(),
        latent_va=sidecar.latent_va[ix].copy(),
        acclimatization=sidecar.acclimatization[ix].copy(),
        remodeling=sidecar.remodeling[ix].copy(),
        recoverable_load=sidecar.recoverable_load[ix].copy(),
        injury=sidecar.injury[ix].copy(),
        surface_background_energy_j=energy.surface_background_energy_j.copy(),
        equilibrium_background_energy_j=energy.equilibrium_background_energy_j.copy(),
        photo_energy_j=energy.photo_energy_j.copy(),
        photo_equilibrium_energy_j=energy.photo_equilibrium_energy_j.copy(),
        source_buffer_j=energy.source_buffer_j.copy(),
        cumulative_gross_uptake_j=energy.cumulative_gross_uptake_j.copy(),
        cumulative_return_flow_j=energy.cumulative_return_flow_j.copy(),
        cumulative_net_sink_j=energy.cumulative_net_sink_j.copy(),
        cumulative_stellar_pump_j=energy.cumulative_stellar_pump_j.copy(),
        endpoint_relative_year=float(endpoint_relative_year),
        d3_runtime_state=None if d3_runtime_state is None else copy.deepcopy(dict(d3_runtime_state)),
        schema_version='v0.6D->v0.6C',
    )
    st.validate(); return st


def verify_species_to_deme_moment_identity(sidecar: HistoricalLineageSidecar, d3_state: DeepRuntimeState,
                                            deme_seed_registry: Mapping[str,Any]) -> dict[str,float|int]:
    """Check exact parent-state cloning for every D3-derived deme seed."""
    sidecar.validate(); d3_state.validate(); old={s:i for i,s in enumerate(sidecar.species_ids)}
    dindex={d:i for i,d in enumerate(d3_state.deme_ids)}
    max_mu=max_va=max_phys=0.0
    for row in deme_seed_registry['demes']:
        i=old[str(row['species_id'])]; j=dindex[str(row['deme_seed_id'])]
        max_mu=max(max_mu,float(np.max(np.abs(sidecar.latent_mean[i]-d3_state.latent_mean[j]))))
        max_va=max(max_va,float(np.max(np.abs(sidecar.latent_va[i]-d3_state.latent_va[j]))))
        for a,b in ((sidecar.acclimatization,d3_state.acclimatization),(sidecar.remodeling,d3_state.remodeling),(sidecar.recoverable_load,d3_state.recoverable_load),(sidecar.injury,d3_state.injury)):
            max_phys=max(max_phys,abs(float(a[i])-float(b[j])))
    return {'deme_count':len(d3_state.deme_ids),'max_latent_mean_abs_error':max_mu,'max_latent_va_abs_error':max_va,'max_physiology_abs_error':max_phys}



def validate_d22_d3_reference(d1_species_ids: Sequence[str], survivor_species_ids: Sequence[str],
                               deme_seed_registry: Mapping[str,Any], bridge_audit: Mapping[str,Any],
                               *, authorized_proxy_parent: Mapping[str,str]|None=None) -> dict[str,Any]:
    """Validate the real D2.2 -> D3.0A boundary, including explicit legacy D2-child proxy provenance."""
    d1=set(map(str,d1_species_ids)); surv=[str(x) for x in survivor_species_ids]; proxies={} if authorized_proxy_parent is None else {str(k):str(v) for k,v in authorized_proxy_parent.items()}
    if len(surv)!=31 or len(set(surv))!=31: raise RuntimeError('D2.2 survivor set must contain exactly 31 unique species: FAIL_CLOSED')
    unresolved=[s for s in surv if s not in d1 and not (s in proxies and proxies[s] in d1)]
    if unresolved: raise RuntimeError(f'D2.2 survivors lack D1/proxy provenance: {unresolved}: FAIL_CLOSED')
    crit=bridge_audit.get('criteria',{}); metrics=bridge_audit.get('metrics',{})
    required={'parent_is_D2_2':True,'survivor_count_is_31':True,'no_speciation':True,'no_adaptive_radiation':True,'no_trait_evolution':True,'no_Deep':True,'deme_seeds_are_derived':True,'HSG025_proxy_provenance_explicit':True}
    for k,v in required.items():
        if crit.get(k) is not v: raise RuntimeError(f'D3.0A bridge authority criterion {k} failed: FAIL_CLOSED')
    if str(metrics.get('parent'))!='0.6.3D2.2': raise RuntimeError('D3.0A parent is not D2.2: FAIL_CLOSED')
    seed_species=[str(d.get('species_id','')) for d in deme_seed_registry.get('demes',[])]
    if set(seed_species)!=set(surv): raise RuntimeError('D3 seed species set differs from D2.2 survivor set: FAIL_CLOSED')
    if len(seed_species)!=115: raise RuntimeError('D3.0A deme seed count is not 115: FAIL_CLOSED')
    return {'D1_species_count':len(d1),'survivor_count':len(surv),'deme_seed_count':len(seed_species),'proxy_survivor_count':sum(1 for x in surv if x not in d1),'parent':'0.6.3D2.2','authority_preserved':True}

def historical_d2_runtime_gate(d2_runtime_package_present: bool, d1_population_state_present: bool,
                               d1_variance_state_present: bool) -> None:
    """Production HX must fail closed until the archived D1/D2 runtime/state is mounted."""
    missing=[]
    if not d2_runtime_package_present: missing.append('D2_RUNTIME_PACKAGE')
    if not d1_population_state_present: missing.append('D1_210MA_POPULATION_STATE')
    if not d1_variance_state_present: missing.append('D1_210MA_VARIANCE_STATE')
    if missing: raise RuntimeError('historical HX inputs missing: '+','.join(missing)+': FAIL_CLOSED')

GOVERNANCE={
    'D1_D2_reconstructed_from_summaries':False,
    'D22_survivor_authority_modified':False,
    'D3_seed_birth_authority_added':False,
    'Deep_direct_survivor_selection':False,
    'Deep_direct_speciation':False,
    'energy_reset_at_D22_D3_boundary':False,
    'photo_deep_additive_share_E_th':0.05,
    'production_HX_allowed_without_D1_D2_runtime':False,
}

# ---------------------------------------------------------------------------
# D1/D2 representation adapters. These are deliberately species/lineage level
# and do not manufacture D3 demes before the D3.0A bridge exists.
# ---------------------------------------------------------------------------

def historical_passive_pressure(
    species_population: np.ndarray,
    reference_population: np.ndarray,
    species_guild: np.ndarray,
    sidecar: HistoricalLineageSidecar,
    *,
    regulation_gain: float = 0.60,
    floor: float = 1.0e-15,
) -> dict[str, np.ndarray]:
    """Apply the v0.6A population->passive-pressure operator to D1/D2 species rasters.

    `reference_population` remains only the environmental abundance/opportunity
    normalization anchor. It is neither carrying capacity nor physical N.
    No individual-equivalent parameter enters this function.
    """
    from deep_d3_coupling_v0_6A import biological_pressure

    sidecar.validate()
    pop=np.asarray(species_population,float)
    if pop.ndim!=3 or pop.shape[0]!=len(sidecar.species_ids):
        raise ValueError("D1/D2 population must be [species,y,x] aligned with sidecar")
    guild=np.asarray(species_guild,int)
    if guild.shape!=(len(sidecar.species_ids),):
        raise ValueError("D1/D2 guild shape mismatch")
    return biological_pressure(
        pop, np.asarray(reference_population,float), guild, sidecar.latent_mean,
        acclimatization=sidecar.acclimatization,
        regulation_gain=regulation_gain, floor=floor,
    )


def reconcile_d2_authorized_lineages(
    sidecar: HistoricalLineageSidecar,
    current_species_ids: Sequence[str],
    lineage_events: Sequence[Mapping[str,Any]],
) -> HistoricalLineageSidecar:
    """Reconcile sidecar identities only from D2-authorized biological events.

    Supported birth provenance is a D2 speciation/branch event carrying an explicit
    parent and daughter. A new lineage inherits parent Deep first/second moments and
    physiology at recognition. Unknown births fail closed. Extinct lineages may be
    dropped only because the supplied D2 current-species registry no longer contains
    them. Deep never authors the registry.
    """
    sidecar.validate()
    target=[str(x) for x in current_species_ids]
    if len(set(target))!=len(target):
        raise RuntimeError("duplicate D2 current species id: FAIL_CLOSED")
    old={sid:i for i,sid in enumerate(sidecar.species_ids)}
    birth_parent: dict[str,str]={}
    for ev in lineage_events:
        # Accept only explicitly taxonomic D2 events; the caller may retain its own
        # richer event name but must supply parent/daughter provenance.
        et=str(ev.get('event_type',ev.get('type',''))).upper()
        parent=str(ev.get('parent_species_id',ev.get('parent','')))
        daughter=str(ev.get('daughter_species_id',ev.get('daughter','')))
        if daughter:
            if not parent:
                raise RuntimeError(f"D2 lineage birth {daughter} lacks parent: FAIL_CLOSED")
            if 'SPECI' not in et and 'BRANCH' not in et:
                raise RuntimeError(f"D2 lineage birth {daughter} lacks speciation/branch authority: FAIL_CLOSED")
            if daughter in birth_parent and birth_parent[daughter]!=parent:
                raise RuntimeError(f"conflicting D2 parent provenance for {daughter}: FAIL_CLOSED")
            birth_parent[daughter]=parent

    rows_mu=[]; rows_va=[]; acc=[]; rem=[]; load=[]; inj=[]; prov=[]
    source_prov=sidecar.provenance or ['UNSPECIFIED']*len(sidecar.species_ids)
    for sid in target:
        if sid in old:
            i=old[sid]
            rows_mu.append(sidecar.latent_mean[i].copy()); rows_va.append(sidecar.latent_va[i].copy())
            acc.append(float(sidecar.acclimatization[i])); rem.append(float(sidecar.remodeling[i]))
            load.append(float(sidecar.recoverable_load[i])); inj.append(float(sidecar.injury[i])); prov.append(source_prov[i])
            continue
        parent=birth_parent.get(sid)
        if parent is None or parent not in old:
            raise RuntimeError(f"unknown D2 lineage birth {sid}: FAIL_CLOSED")
        i=old[parent]
        rows_mu.append(sidecar.latent_mean[i].copy()); rows_va.append(sidecar.latent_va[i].copy())
        acc.append(float(sidecar.acclimatization[i])); rem.append(float(sidecar.remodeling[i]))
        load.append(float(sidecar.recoverable_load[i])); inj.append(float(sidecar.injury[i]))
        prov.append(f"D2_AUTHORIZED_INHERITANCE_{parent}_TO_{sid}")
    out=HistoricalLineageSidecar(
        target,np.asarray(rows_mu,float),np.asarray(rows_va,float),np.asarray(acc,float),np.asarray(rem,float),
        np.asarray(load,float),np.asarray(inj,float),provenance=prov,
    )
    out.validate(); return out


def historical_selection_variance_step(
    sidecar: HistoricalLineageSidecar,
    species_population: np.ndarray,
    mode_opportunity: np.ndarray,
    bio_cfg: Mapping[str,Any],
    *,
    dt_years: float,
    generation_time_years: np.ndarray,
    relative_reproduction_rate: np.ndarray,
    heritable_cfg: Any | None = None,
) -> tuple[HistoricalLineageSidecar, dict[str,Any]]:
    """Representation-neutral D1/D2 Deep selection + zero-mean VA dynamics.

    Requires externally grounded generation-time proxies. It never infers physical N
    or generation time from WorldSim population units. Direction of latent means comes
    only from the local viability gradient; mutation enters variance only.
    """
    from deep_heritable_selection_v0_6B import (
        DeepHeritableConfig, viability_selection_gradient, selection_response_step,
        advance_latent_variance,
    )
    sidecar.validate()
    cfg=DeepHeritableConfig() if heritable_cfg is None else heritable_cfg
    pop=np.maximum(np.asarray(species_population,float),0.0)
    if pop.ndim!=3 or pop.shape[0]!=len(sidecar.species_ids): raise ValueError("historical population shape mismatch")
    gt=np.asarray(generation_time_years,float); rr=np.asarray(relative_reproduction_rate,float)
    if gt.shape!=(len(sidecar.species_ids),) or rr.shape!=(len(sidecar.species_ids),):
        raise RuntimeError("historical selection requires explicit generation time and reproduction arrays: FAIL_CLOSED")
    if np.any(gt<=0) or np.any(rr<=0): raise RuntimeError("non-positive historical life-history proxy: FAIL_CLOSED")
    grad=viability_selection_gradient(
        pop,np.asarray(mode_opportunity,float),sidecar.latent_mean,bio_cfg,cfg,
        acclimatization=sidecar.acclimatization,remodeling=sidecar.remodeling,
    )
    z=selection_response_step(sidecar.latent_mean,sidecar.latent_va,grad,float(dt_years),cfg,relative_reproduction_rate=rr)
    totals=pop.sum(axis=(1,2))
    va=advance_latent_variance(sidecar.latent_va,grad,totals,gt,float(dt_years),cfg)
    out=HistoricalLineageSidecar(
        list(sidecar.species_ids),z,va,sidecar.acclimatization.copy(),sidecar.remodeling.copy(),
        sidecar.recoverable_load.copy(),sidecar.injury.copy(),
        provenance=None if sidecar.provenance is None else list(sidecar.provenance),
    )
    out.validate()
    return out, {
        'max_abs_selection_gradient':float(np.max(np.abs(grad))) if grad.size else 0.0,
        'max_abs_latent_mean_change':float(np.max(np.abs(z-sidecar.latent_mean))) if z.size else 0.0,
        'median_latent_va':float(np.median(va)) if va.size else 0.0,
        'mutation_mean_shift':0.0,
        'drift_individual_equivalents_domain':'GENETICS_ONLY_NOT_ENERGY',
    }


CHA1_SURFACE_TOTAL_J=1.0857344210806324e16
CHA1_TOTAL_DEEP_ENERGY_J=1.0857344210806323e17
# Exact v0.2 numerical-calibration energies are retained rather than idealized
# decimal fractions so v0.6D reproduces v0.5 materialized ledgers to roundoff.
CHA1_MODE_DEEP_ENERGY_J=np.asarray([5.428672105403162e16,2.171468842161265e16,2.171468842161265e16,7600140947564427.0,3257203263241897.0],float)
CHA1_MODE_FRACTIONS=CHA1_MODE_DEEP_ENERGY_J/CHA1_TOTAL_DEEP_ENERGY_J
CHA1_TRANSIENT_FRACTION=9.988756673941818e16/CHA1_TOTAL_DEEP_ENERGY_J
CHA1_METASTABLE_FRACTION=8685875368645059.0/CHA1_TOTAL_DEEP_ENERGY_J
CHA1_TRANSIENT_TAU_Y=30.0
CHA1_METASTABLE_TAU_Y=20_000.0


def cha1_surface_pulse_energy_by_mode(years_after_impact: float | np.ndarray) -> np.ndarray:
    """Exact v0.5 CHA-1 surface pulse provenance, excluding background/photo energy.

    Returns J with trailing mode axis [...,5]. Negative event-relative time has zero
    CHA-1 pulse. This function does not perform biological survivor selection.
    """
    t=np.asarray(years_after_impact,float)
    tp=np.maximum(t,0.0)
    decay=(CHA1_TRANSIENT_FRACTION*np.exp(-tp/CHA1_TRANSIENT_TAU_Y)
           +CHA1_METASTABLE_FRACTION*np.exp(-tp/CHA1_METASTABLE_TAU_Y))
    decay=np.where(t>=0,decay,0.0)
    return decay[...,None]*CHA1_SURFACE_TOTAL_J*CHA1_MODE_FRACTIONS


def validate_cha1_reference_against_v05(years: np.ndarray, reference_remaining_j: np.ndarray,
                                         *, atol_j: float=5.0e5, rtol: float=1.0e-9) -> dict[str,float|int]:
    """Compare exact event-time pulse to v0.5 materialized age-derived checkpoints.

    v0.5 materialization formed event time through `(66-age_ma)*1e6`, so decimal
    Ma roundoff leaves ~1e-10-relative differences at early checkpoints. v0.6D
    intentionally keeps D2.2 exact event-relative time rather than reproducing that
    age-coordinate roundoff.
    """
    y=np.asarray(years,float); ref=np.asarray(reference_remaining_j,float)
    pred=cha1_surface_pulse_energy_by_mode(y)
    if ref.shape!=pred.shape: raise ValueError("CHA1 reference shape mismatch")
    err=np.abs(pred-ref); scale=np.maximum(np.abs(ref),1.0); rel=err/scale
    if np.any((err>float(atol_j)) & (rel>float(rtol))):
        raise RuntimeError(f"CHA1 analytic pulse differs from v0.5 beyond tolerance: max_abs={float(np.max(err))} J max_rel={float(np.max(rel))}: FAIL_CLOSED")
    return {'checkpoint_count':len(y),'max_abs_error_j':float(np.max(err)),'mean_abs_error_j':float(np.mean(err)),'max_relative_error':float(np.max(rel))}


def d22_deep_extension_gate(*, d22_runtime_adapter_present: bool, continuous_hazard_hook_present: bool) -> None:
    """Prevent a summary-derived or survivor-list-derived CHA-1 HX implementation."""
    missing=[]
    if not d22_runtime_adapter_present: missing.append('D2_2_RUNTIME_ADAPTER')
    if not continuous_hazard_hook_present: missing.append('D2_2_CONTINUOUS_HAZARD_HOOK')
    if missing: raise RuntimeError('CHA1 Deep HX integration missing: '+','.join(missing)+': FAIL_CLOSED')
