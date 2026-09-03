from __future__ import annotations

from dataclasses import asdict, dataclass
from collections import defaultdict
from pathlib import Path
import json, math
import numpy as np

from . import dynamic_demes as dd
from . import speciation_gate as sg
from . import additive_variance as av
from . import adaptive_radiation as ar
from . import diversity_recovery as dr
from . import paleogeographic_history as pgh

STATUS = "PASS_FOUNDER_LINEAGE_VIABILITY_PHYSICAL_BARRIER_ADEQUACY_CALIBRATION_CANDIDATE"

PLANT_BASIS = np.asarray([[-1.0, -0.5773502692], [1.0, -0.5773502692], [0.0, 1.1547005384]], dtype=float)
PREY_BASIS = np.asarray([[-0.7071067812, -0.7071067812], [0.7071067812, -0.7071067812], [-0.7071067812, 0.7071067812], [0.7071067812, 0.7071067812]], dtype=float)

@dataclass(frozen=True)
class DiversificationAdequacyConfig(dr.DiversityRecoveryConfig):
    # Resource-niche evolution. Coordinates are dimensionless barycentric/simplex embeddings.
    resource_niche_enabled: bool = True
    resource_niche_scale: float = 0.75
    resource_match_sigma: float = 0.85
    resource_trait_response_timescale_years: float = 500_000.0
    resource_initial_normalized_va: float = 0.012
    resource_mutation_variance_supply_per_myr: float = 0.001
    resource_variance_ceiling: float = 0.05
    resource_variance_homeostasis_enabled: bool = False
    resource_mutation_supply_generation_scaled: bool = False
    resource_mutation_supply_reference_generation_years: float = 5.0
    resource_baseline_stabilizing_variance_depletion_per_generation: float = 0.0
    resource_nonlinear_stabilizing_variance_depletion_per_myr_per_q: float = 0.0
    resource_selection_variance_depletion_per_generation: float = 2.0e-8

    # Genomic incompatibility is independent of ecological trait divergence.
    genomic_isolation_enabled: bool = True
    genomic_ri_build_rate_per_generation: float = 5.0e-7
    genomic_ri_decay_rate_per_generation: float = 2.0e-6

    # Daughter/current-species ecological autonomy.
    current_species_demography_enabled: bool = True
    species_opportunity_floor: float = 1e-9

    # Physical connectivity calibration for interpolated terrestrial support.
    transient_vicariance_enabled: bool = True
    transient_vicariance_fission_enabled: bool = False
    # A transient barrier only becomes a persistent demographic split after it
    # has been observed continuously for this biological/geographic duration.
    # This timer is independent of integration dt and is reset by reconnection.
    vicariance_persistence_min_years: float = 1_000_000.0
    vicariance_persistence_reset_on_reconnection: bool = True
    connectivity_land_support_threshold: float = 0.25
    connectivity_softness: float = 0.10
    pair_graph_refresh_interval_years: float = 250_000.0

    # D3.2C endpoint-constrained paleogeographic barrier-history reconstruction.
    paleogeographic_event_reconstruction_enabled: bool = False
    paleogeographic_event_older_ma: float = 60.0
    paleogeographic_event_younger_ma: float = 30.0
    paleogeographic_event_phase_min: float = 0.05
    paleogeographic_event_phase_max: float = 0.95
    paleogeographic_event_transition_width_years: float = 1_000_000.0

    # D3.2B founder-lineage viability.  The former global 5% parent fraction is
    # retained only as a diagnostic; birth authority is life-history-aware and
    # requires continuous demographic persistence of the isolated component.
    founder_viability_enabled: bool = True
    founder_minimum_persistence_years: float = 1_000_000.0
    founder_base_minimum_population_units: float = 0.05
    founder_generation_reference_years: float = 5.0
    founder_reproduction_reference: float = 1.0
    founder_minimum_effective_size_proxy: float = 500.0
    founder_minimum_normalized_additive_variance: float = 0.005
    founder_minimum_occupied_cells: int = 10
    founder_maximum_persistent_decline_fraction: float = 0.50
    founder_reset_on_reconnection: bool = True

    # D3.2B physical-barrier adequacy.  Permanent-deme fission is evaluated on
    # effective connectivity, not land support alone: a geometric corridor that
    # is nearly unusable habitat can function as a species-specific barrier.
    habitat_barrier_enabled: bool = True
    habitat_connectivity_power: float = 0.50
    effective_connectivity_core_threshold: float = 0.20

    # D3.2B calibration replay is deliberately bounded to the same 5-20 Myr window.
    dt_years: float = 50_000.0
    snapshot_interval_years: float = 500_000.0
    deme_fission_check_interval_years: float = 500_000.0

@dataclass
class DiversificationAdequacyResult:
    root_species_ids: list[str]
    final_species_ids: list[str]
    deme_ids: list[str]
    current_species_id: list[str]
    root_species_index: np.ndarray
    guild_id: np.ndarray
    lat: np.ndarray
    lon: np.ndarray
    snapshot_relative_year: np.ndarray
    species_richness_history: np.ndarray
    total_population_history: np.ndarray
    endpoint_population: np.ndarray
    endpoint_trait: np.ndarray
    endpoint_additive_variance: np.ndarray
    endpoint_resource_trait: np.ndarray
    endpoint_resource_variance: np.ndarray
    generation_time_proxy_years: np.ndarray
    endpoint_ecological_ri: np.ndarray
    endpoint_genomic_ri: np.ndarray
    endpoint_intrinsic_RI: np.ndarray
    endpoint_isolation_clock_generations: np.ndarray
    endpoint_contact_connectivity: np.ndarray
    endpoint_trait_distance: np.ndarray
    species_registry: list[dict]
    speciation_events: list[dict]
    deme_fission_events: list[dict]
    vicariance_persistence_state: dict
    vicariance_calibration_stats: dict
    founder_viability_state: dict
    founder_viability_stats: dict
    diagnostics: dict


def _read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_config(path: Path) -> DiversificationAdequacyConfig:
    raw = _read_json(path)
    fields = DiversificationAdequacyConfig.__dataclass_fields__
    return DiversificationAdequacyConfig(**{k: raw[k] for k in fields if k in raw})


def _initial_resource_pref(meta: dict) -> np.ndarray:
    g = int(meta["guild_id"])
    w = meta.get("diet_weights", {})
    if g <= 4:
        if g == 1:
            v = np.asarray([1/3, 1/3, 1/3], dtype=float)
        elif g == 2:
            v = np.asarray([1.0, 0.0, 0.0], dtype=float)
        elif g == 3:
            v = np.asarray([0.0, 1.0, 0.0], dtype=float)
        else:
            v = np.asarray([float(w.get("browse", 0.0)), float(w.get("low", 0.0)), float(w.get("wetland", 0.0))], dtype=float)
            if v.sum() <= 0: v[:] = 1/3
        v /= v.sum()
        return v @ PLANT_BASIS
    v = np.asarray([
        float(w.get("small_herbivore", 0.0)), float(w.get("low_feeder", 0.0)),
        float(w.get("reptiloid", 0.0)), float(w.get("browser", 0.0)),
    ], dtype=float)
    if v.sum() <= 0: v[:] = 0.25
    v /= v.sum()
    return v @ PREY_BASIS


def initialize_resource_state(root_idx, root_species_ids, metadata, cfg):
    z = np.zeros((len(root_idx), 2), dtype=float)
    v = np.full((len(root_idx), 2), cfg.resource_initial_normalized_va * cfg.resource_niche_scale**2, dtype=float)
    for i, si in enumerate(root_idx):
        z[i] = _initial_resource_pref(metadata[root_species_ids[int(si)]])
    return z, v


def _connectivity_permeability(land_support: np.ndarray, cfg: DiversificationAdequacyConfig):
    if not cfg.transient_vicariance_enabled:
        return np.where(land_support > 1e-9, 1.0, 0.0)
    x = (np.asarray(land_support, dtype=float) - cfg.connectivity_land_support_threshold) / max(cfg.connectivity_softness, 1e-9)
    # smooth logistic permeability; threshold=0.25 is the 0.5 permeability point.
    p = 1.0 / (1.0 + np.exp(-x))
    p[land_support <= 1e-9] = 0.0
    return p


def _normalize_channels(channels, land_support):
    out=[]
    for arr in channels:
        out.append(ar._normalize_resource(np.maximum(arr,0.0), land_support))
    return np.stack(out)


def _resource_fields(sp, species_guild, sub):
    plants = _normalize_channels([sub["browse_forage"], sub["low_forage"], sub["wetland_forage"]], sub["land_support"])
    prey = np.zeros((4,) + sub["land_support"].shape, dtype=float)
    for gi in range(1,5):
        idx = np.where(species_guild == gi)[0]
        if len(idx): prey[gi-1] = sp[idx].sum(axis=0)
    prey = _normalize_channels(list(prey), sub["land_support"])
    return plants, prey


def _coord_field(channels: np.ndarray, basis: np.ndarray):
    den = channels.sum(axis=0)
    coord = np.zeros((2,) + den.shape, dtype=float)
    good = den > 1e-15
    for k in range(channels.shape[0]):
        frac = np.divide(channels[k], den, out=np.zeros_like(den), where=good)
        coord[0] += frac * basis[k,0]
        coord[1] += frac * basis[k,1]
    return coord, den


def _trophic_routing_weight(tau, cfg):
    """Map the calibrated B2 anchors exactly to pure channels, continuously."""
    a=float(getattr(cfg,"trophic_mode_initial_plant_anchor",0.02)); b=float(getattr(cfg,"trophic_mode_initial_animal_anchor",0.98))
    return np.clip((np.asarray(tau,dtype=float)-a)/max(b-a,1e-12),0.0,1.0)


def _current_functional_prey_raw(pop, current_species, current_guild):
    """Raw prey channels from current functional guilds, not immutable roots."""
    shape=np.asarray(pop[0],dtype=float).shape
    total=np.zeros((4,)+shape,dtype=float)
    by_species={}
    for i in range(len(pop)):
        g=int(current_guild[i])
        if 1 <= g <= 4:
            q=np.maximum(np.asarray(pop[i],dtype=float),0.0)
            total[g-1]+=q
            sid=str(current_species[i])
            if sid not in by_species:
                by_species[sid]=np.zeros_like(total)
            by_species[sid][g-1]+=q
    return total, by_species

def _prey_coord_mag_for_focal(raw_total, by_species, focal_sid, land_support, exclude_self):
    raw=np.asarray(raw_total,dtype=float)
    if exclude_self and focal_sid is not None:
        raw=np.maximum(raw-np.asarray(by_species.get(str(focal_sid),0.0),dtype=float),0.0)
    prey=_normalize_channels(list(raw),land_support)
    return _coord_field(prey, PREY_BASIS)

def _habitats_and_resource_targets(pop, trait, resource_trait, root_idx, root_species_ids, species_guild, metadata, sub, cfg, trophic_mode=None, current_species=None, current_guild=None):
    nspecies=len(root_species_ids)
    sp=ar._root_species_population(pop, root_idx, nspecies)
    plants, prey = _resource_fields(sp, species_guild, sub)
    plant_coord, plant_mag_legacy = _coord_field(plants, PLANT_BASIS)
    prey_coord, prey_mag_legacy = _coord_field(prey, PREY_BASIS)
    continuous=bool(getattr(cfg,"trophic_mode_continuous_resource_routing_enabled",False)) and trophic_mode is not None
    use_current_prey=bool(getattr(cfg,"trophic_mode_current_functional_prey_field_enabled",False)) and current_species is not None and current_guild is not None and len(current_species)==len(pop) and len(current_guild)==len(pop)
    exclude_self=bool(getattr(cfg,"trophic_mode_exclude_same_species_from_prey_opportunity",False)) and use_current_prey
    raw_prey=prey_by_species=None
    prey_cache={}
    if use_current_prey:
        raw_prey,prey_by_species=_current_functional_prey_raw(pop,current_species,current_guild)
    plant_mag, prey_mag = plant_mag_legacy, prey_mag_legacy
    routing=_trophic_routing_weight(trophic_mode,cfg) if continuous else None
    out=np.zeros_like(pop)
    targets=np.full((len(pop),2), np.nan, dtype=float)
    permeability=_connectivity_permeability(sub["land_support"],cfg)
    for di,si0 in enumerate(root_idx):
        si=int(si0); sid=root_species_ids[si]; meta=metadata[sid]; g=int(species_guild[si])
        climate=dd._climate_suitability(meta, trait[di], sub["temperature_c"], sub["aridity_index"], sub["accessible"], cfg.habitat_floor)
        if continuous:
            w=float(routing[di])
            local_prey_coord,local_prey_mag=prey_coord,prey_mag_legacy
            if use_current_prey:
                focal=str(current_species[di]) if exclude_self else "__GLOBAL__"
                if focal not in prey_cache:
                    prey_cache[focal]=_prey_coord_mag_for_focal(raw_prey,prey_by_species,None if focal=="__GLOBAL__" else focal,sub["land_support"],exclude_self)
                local_prey_coord,local_prey_mag=prey_cache[focal]
            d2p=(plant_coord[0]-resource_trait[di,0])**2+(plant_coord[1]-resource_trait[di,1])**2
            d2a=(local_prey_coord[0]-resource_trait[di,0])**2+(local_prey_coord[1]-resource_trait[di,1])**2
            mp=np.exp(-0.5*d2p/max(cfg.resource_match_sigma**2,1e-12))
            ma=np.exp(-0.5*d2a/max(cfg.resource_match_sigma**2,1e-12))
            cp=(1.0-w)*np.maximum(plant_mag_legacy,0.0)*mp
            ca=w*np.maximum(local_prey_mag,0.0)*ma
            support=cp+ca  # convex routing: no double-counted resource bonus
            den=cp+ca
            coord=np.zeros_like(plant_coord)
            good=den>1e-15
            coord[0]=np.divide(cp*plant_coord[0]+ca*local_prey_coord[0],den,out=plant_coord[0].copy(),where=good)
            coord[1]=np.divide(cp*plant_coord[1]+ca*local_prey_coord[1],den,out=plant_coord[1].copy(),where=good)
            q=climate*np.maximum(support,cfg.habitat_floor)*np.maximum(sub["land_support"],1e-9)
        else:
            if g <= 4:
                coord, mag = plant_coord, plant_mag
            else:
                coord, mag = prey_coord, prey_mag
            d2=(coord[0]-resource_trait[di,0])**2+(coord[1]-resource_trait[di,1])**2
            match=np.exp(-0.5*d2/max(cfg.resource_match_sigma**2,1e-12))
            q=climate*np.maximum(mag,cfg.habitat_floor)*match*np.maximum(sub["land_support"],1e-9)
        q[~sub["accessible"]]=0.0
        m=float(q.max())
        if m>0:q/=m
        out[di]=q
        p=pop[di]; n=float(p.sum())
        if n>0:
            targets[di,0]=float(np.sum(p*coord[0])/n)
            targets[di,1]=float(np.sum(p*coord[1])/n)
    return out, targets, permeability

def _realized_trophic_animal_share(pop, resource_trait, root_idx, root_species_ids, species_guild, sub, cfg, trophic_mode, current_species=None, current_guild=None):
    """Population-weighted realized animal-channel share under B2.2 routing.

    This is resource-use evidence for B2.3.  It uses exactly the B2.2 convex
    channel contributions and, when enabled, the same current-guild/self-prey
    corrections as habitat routing.
    """
    nspecies=len(root_species_ids)
    sp=ar._root_species_population(pop,root_idx,nspecies)
    plants,prey=_resource_fields(sp,species_guild,sub)
    plant_coord,plant_mag=_coord_field(plants,PLANT_BASIS)
    prey_coord,prey_mag=_coord_field(prey,PREY_BASIS)
    use_current=bool(getattr(cfg,"trophic_mode_current_functional_prey_field_enabled",False)) and current_species is not None and current_guild is not None and len(current_species)==len(pop)
    exclude_self=bool(getattr(cfg,"trophic_mode_exclude_same_species_from_prey_opportunity",False)) and use_current
    raw=by=None; cache={}
    if use_current:
        raw,by=_current_functional_prey_raw(pop,current_species,current_guild)
    routing=_trophic_routing_weight(trophic_mode,cfg)
    out=np.full(len(pop),np.nan,dtype=float)
    for i in range(len(pop)):
        pc,pm=prey_coord,prey_mag
        if use_current:
            key=str(current_species[i]) if exclude_self else "__GLOBAL__"
            if key not in cache:
                cache[key]=_prey_coord_mag_for_focal(raw,by,None if key=="__GLOBAL__" else key,sub["land_support"],exclude_self)
            pc,pm=cache[key]
        d2p=(plant_coord[0]-resource_trait[i,0])**2+(plant_coord[1]-resource_trait[i,1])**2
        d2a=(pc[0]-resource_trait[i,0])**2+(pc[1]-resource_trait[i,1])**2
        mp=np.exp(-0.5*d2p/max(cfg.resource_match_sigma**2,1e-12))
        ma=np.exp(-0.5*d2a/max(cfg.resource_match_sigma**2,1e-12))
        w=float(routing[i])
        cp=(1.0-w)*np.maximum(plant_mag,0.0)*mp
        ca=w*np.maximum(pm,0.0)*ma
        p=np.maximum(np.asarray(pop[i],dtype=float),0.0)
        pu=float(np.sum(p*cp)); au=float(np.sum(p*ca))
        if pu+au>1e-30:
            out[i]=au/(pu+au)
    return out


def _resource_selection_update(z, va, targets, root_idx, root_species_ids, metadata, dt, cfg):
    out=z.copy()
    for di,si0 in enumerate(root_idx):
        if not np.all(np.isfinite(targets[di])): continue
        sid=root_species_ids[int(si0)]
        rel=max(float(metadata[sid]["relative_reproduction_rate"]),1e-6)
        beta=1.0-math.exp(-dt/max(cfg.resource_trait_response_timescale_years/rel,1e-9))
        gain=np.clip(va[di]/max(cfg.resource_niche_scale**2,1e-12),0.0,0.25)
        out[di]+=beta*gain*(targets[di]-out[di])
    return out


def _advance_resource_variance(va, z_before, targets, populations, generation_time, dt, cfg):
    out=np.asarray(va,float).copy(); legacy_mu=cfg.resource_mutation_variance_supply_per_myr/1e6
    s2=max(cfg.resource_niche_scale**2,1e-12)
    for i in range(len(out)):
        q=out[i]/s2; gt=max(float(generation_time[i]),1e-9)
        pressure=np.zeros(2)
        if np.all(np.isfinite(targets[i])): pressure=((targets[i]-z_before[i])/cfg.resource_niche_scale)**2
        pressure=np.clip(pressure,0.0,4.0)
        ls=cfg.resource_selection_variance_depletion_per_generation*pressure/gt
        if cfg.resource_variance_homeostasis_enabled and cfg.resource_mutation_supply_generation_scaled:
            mu=legacy_mu*max(float(cfg.resource_mutation_supply_reference_generation_years),1e-9)/gt
        else:
            mu=legacy_mu
        if cfg.resource_variance_homeostasis_enabled:
            lb=max(float(cfg.resource_baseline_stabilizing_variance_depletion_per_generation),0.0)/gt
            b=max(float(cfg.resource_nonlinear_stabilizing_variance_depletion_per_myr_per_q),0.0)/1e6
        else:
            lb=0.0; b=0.0
        ne=max(cfg.drift_min_effective_size,max(float(populations[i]),0.0)*cfg.drift_individual_equivalents_per_population_unit)
        ld=np.full(2,1.0/max(2*ne*gt,1e-30))
        lam=ls+ld+lb; ret=np.exp(-lam*dt)
        if b<=0.0:
            qn=np.where(lam<1e-18,q+mu*dt,q*ret+(mu/np.maximum(lam,1e-30))*(1-ret))
        else:
            qn=np.empty_like(q)
            for ti in range(len(q)):
                a=float(lam[ti]); disc=math.sqrt(max(a*a+4*b*mu,0.0))
                if disc<1e-24: qn[ti]=q[ti]; continue
                rp=(-a+disc)/(2*b); rn=(-a-disc)/(2*b)
                den0=float(q[ti]-rn); c0=0.0 if abs(den0)<1e-30 else float((q[ti]-rp)/den0)
                c=c0*math.exp(-disc*dt); den=1-c
                qn[ti]=rp if abs(den)<1e-30 else (rp-c*rn)/den
        out[i]=np.clip(qn,0.0,cfg.resource_variance_ceiling)*s2
    return out


def _migration_with_permeability(pop, habitat, permeability, root_idx, root_species_ids, metadata, lat, lon, sub, dt, cfg):
    # Transport uses habitat * permeability so interpolated low-support corridors are not permanently fully open.
    edge=dd._median_land_edge_km(lat,lon,sub["accessible"]); out=np.zeros_like(pop)
    qhab=habitat*np.maximum(permeability,1e-12)
    for di,si0 in enumerate(root_idx):
        sid=root_species_ids[int(si0)]
        f=dd._migration_fraction(float(metadata[sid]["dispersal_scale_km"]),edge,dt,cfg.dynamic_cfg())
        moved=dd._transport_once(pop[di],qhab[di]); q=(1-f)*pop[di]+f*moved
        q[sub["land_support"]<=1e-9]=0.0
        before=float(pop[di].sum()); after=float(q.sum())
        if before>0 and after>0:q*=before/after
        elif before>0 and after<=0:q=pop[di].copy()
        out[di]=q
    return out


def _species_opportunity(habitat, current_species, deme_guild, sub):
    # Potential opportunity of each extant species is max suitability across its demes, avoiding a bonus for deme count.
    species=sorted(set(current_species)); out={}
    for sid in species:
        idx=[i for i,x in enumerate(current_species) if x==sid]
        g=int(deme_guild[idx[0]])
        h=np.max(habitat[idx],axis=0)
        out[sid]=float(np.sum(h*np.maximum(sub["reference_population"][g-1],0.0)))
    return out


def _ensure_species_ecological_baselines(pop, habitat, current_species, deme_guild, registry, sub, cfg):
    totals=pop.sum(axis=(1,2)); spop={}
    for i,sid in enumerate(current_species): spop[sid]=spop.get(sid,0.0)+float(totals[i])
    opp=_species_opportunity(habitat,current_species,deme_guild,sub)
    for sid in spop:
        row=registry[sid]
        row.setdefault("ecological_baseline_population", float(spop[sid]))
        row.setdefault("ecological_baseline_opportunity", float(max(opp[sid],cfg.species_opportunity_floor)))
        row.setdefault("ecological_baseline_semantics", "SPECIES_LEVEL_CAPACITY_ANCHOR_SPLIT_CONSERVATIVELY_AT_SPECIATION")
    return opp


def _current_species_demography(pop, habitat, current_species, root_idx, root_species_ids, deme_guild, metadata, registry, sub, dt, cfg):
    """Species-level demographic autonomy without abundance-positive feedback.

    Each extant species has a conserved baseline capacity anchor. Initial roots
    inherit their +5 Myr population/opportunity. At a species birth the parent's
    anchor is split in exact proportion to parent/daughter population. Subsequent
    target changes are driven by relative ecological opportunity, not by current
    abundance, so a daughter gets no free equal-share bonus and a common species
    does not win merely because it is already common.
    """
    out=pop.copy(); totals=pop.sum(axis=(1,2)); spop={}
    for i,sid in enumerate(current_species): spop[sid]=spop.get(sid,0.0)+float(totals[i])
    opp=_species_opportunity(habitat,current_species,deme_guild,sub)
    by_g=defaultdict(list)
    for sid in sorted(spop): by_g[int(deme_guild[current_species.index(sid)])].append(sid)
    targets={}
    herb_total=float(sum(spop[s] for g in range(1,5) for s in by_g.get(g,[]))); ref_herb=float(sub["reference_population"][:4].sum())
    for g,sids in by_g.items():
        guild_target=float(sub["reference_population"][g-1].sum())
        if g>=5:guild_target*=float(np.clip(herb_total/max(ref_herb,1e-15),0.0,1.5))
        w=[]
        for sid in sids:
            row=registry[sid]
            bpop=max(float(row.get("ecological_baseline_population",spop[sid])),cfg.species_opportunity_floor)
            bopp=max(float(row.get("ecological_baseline_opportunity",opp[sid])),cfg.species_opportunity_floor)
            w.append(bpop*np.clip(float(opp[sid])/bopp,1e-3,1e3))
        w=np.asarray(w,dtype=float)
        if not np.any(w>0):w=np.ones(len(sids))
        w/=w.sum()
        for sid,x in zip(sids,guild_target*w):targets[sid]=float(x)
    for sid in sorted(spop):
        idx=[i for i,x in enumerate(current_species) if x==sid]; root_sid=root_species_ids[int(root_idx[idx[0]])]; g=int(deme_guild[idx[0]])
        tau=dd.DEFAULT_DEMOGRAPHIC_TAU_YR[g]/max(float(metadata[root_sid]["relative_reproduction_rate"]),1e-6); a=1-math.exp(-dt/max(tau,1e-9)); cur=spop[sid]; new=max(0.0,cur+a*(targets[sid]-cur)); out[idx]*=new/max(cur,1e-15)
    return out,opp


def _split_ecological_baseline_after_births(registry, births, habitat, current_species, deme_guild, sub, cfg):
    if not births:return
    opp=_species_opportunity(habitat,current_species,deme_guild,sub)
    for e in births:
        parent=e["parent_species_id"]; child=e["daughter_species_id"]
        total=float(e["daughter_population"]+e["parent_remainder_population"]); frac=float(e["daughter_population"])/max(total,1e-15)
        prow=registry[parent]; old=max(float(prow.get("ecological_baseline_population",total)),cfg.species_opportunity_floor)
        child_base=old*frac; parent_base=old-child_base
        prow["ecological_baseline_population"]=float(parent_base); prow["ecological_baseline_opportunity"]=float(max(opp.get(parent,1.0),cfg.species_opportunity_floor))
        crow=registry[child]; crow["ecological_baseline_population"]=float(child_base); crow["ecological_baseline_opportunity"]=float(max(opp.get(child,1.0),cfg.species_opportunity_floor)); crow["ecological_baseline_semantics"]="SPLIT_FROM_PARENT_AT_BIRTH_NO_FREE_DAUGHTER_CAPACITY"

def _pair_metrics_extended(pop, trait, resource_trait, root_idx, root_species_ids, metadata, lat, lon, permeability, cfg):
    """Vectorized spatial contact graph plus extended trait distance.

    Spatial overlap is computed root-lineage by root-lineage using NumPy
    broadcasting. This is mathematically equivalent to the pair loop but avoids
    a Python raster reduction for every pair.
    """
    nd=len(root_idx); G=np.zeros((nd,nd),dtype=float); contact=np.zeros_like(G)
    masked=np.asarray(pop,dtype=float)*permeability[None,:,:]
    # Precompute unit-sphere centroids from the same masked support used for contact.
    latr=np.deg2rad(np.asarray(lat,dtype=float))[:,None]
    lonr=np.deg2rad(np.asarray(lon,dtype=float))[None,:]
    coslat=np.cos(latr); xfield=coslat*np.cos(lonr); yfield=coslat*np.sin(lonr); zfield=np.sin(latr)*np.ones_like(lonr)
    for si,sid in enumerate(root_species_ids):
        idx=np.where(root_idx==si)[0]
        if len(idx)<2: continue
        P=masked[idx].reshape(len(idx),-1)
        n=P.sum(axis=1)
        # Pair overlap normalized by the smaller deme mass.
        mins=np.minimum(P[:,None,:],P[None,:,:]).sum(axis=2)
        denom=np.minimum(n[:,None],n[None,:])
        ov=np.divide(mins,denom,out=np.zeros_like(mins),where=denom>1e-15)
        # Spherical centroid for each deme; fallback to unmasked population if needed.
        coords=[]
        for local,di in enumerate(idx):
            if n[local]>1e-15:
                q=masked[di]; nn=float(q.sum())
                xv=float(np.sum(q*xfield)/nn); yv=float(np.sum(q*yfield)/nn); zv=float(np.sum(q*zfield)/nn)
                norm=max(math.sqrt(xv*xv+yv*yv+zv*zv),1e-15); xv/=norm; yv/=norm; zv/=norm
                la=math.degrees(math.asin(np.clip(zv,-1,1))); lo=math.degrees(math.atan2(yv,xv)); coords.append((la,lo))
            else: coords.append(dd._weighted_centroid(lat,lon,pop[di]))
        la=np.deg2rad(np.asarray([c[0] for c in coords])); lo=np.deg2rad(np.asarray([c[1] for c in coords]))
        dla=la[:,None]-la[None,:]; dlo=lo[:,None]-lo[None,:]
        aa=np.sin(dla/2)**2+np.cos(la[:,None])*np.cos(la[None,:])*np.sin(dlo/2)**2
        dist=6371.0088*2*np.arcsin(np.sqrt(np.clip(aa,0,1)))
        ds=max(float(metadata[sid]["dispersal_scale_km"]),1e-9)
        g=np.clip(cfg.gene_flow_ceiling_per_step*ov*np.exp(-dist/(4*ds)),0.0,cfg.gene_flow_ceiling_per_step)
        np.fill_diagonal(g,0.0)
        G[np.ix_(idx,idx)]=g
        contact[np.ix_(idx,idx)]=np.clip(g/max(cfg.gene_flow_ceiling_per_step,1e-15),0.0,1.0)
    td=_trait_distance_extended(trait,resource_trait,root_idx,root_species_ids,metadata,cfg)
    return G,contact,td

def _trait_distance_extended(trait, resource_trait, root_idx, root_species_ids, metadata, cfg):
    nd=len(root_idx); td=np.zeros((nd,nd),dtype=float)
    for si,sid in enumerate(root_species_ids):
        idx=np.where(root_idx==si)[0]; meta=metadata[sid]
        ts=max(float(meta["thermal_niche_sigma_c"]),1e-6); ds=max(float(meta["aridity_niche_sigma"])/1.55,1e-4); ms=max(cfg.body_mass_scale,1e-6)
        for a in range(len(idx)):
            i=int(idx[a])
            for b in range(a+1,len(idx)):
                j=int(idx[b])
                base=[(trait[i,0]-trait[j,0])/ts,(trait[i,1]-trait[j,1])/ds,(trait[i,2]-trait[j,2])/ms]
                if cfg.resource_niche_enabled:
                    base.extend([(resource_trait[i,0]-resource_trait[j,0])/cfg.resource_niche_scale,(resource_trait[i,1]-resource_trait[j,1])/cfg.resource_niche_scale])
                d=np.asarray(base,dtype=float)
                td[i,j]=td[j,i]=float(np.sqrt(np.sum(d*d)))
    return td

def _combined_ri(ecological_ri, genomic_ri):
    return 1.0-(1.0-np.clip(ecological_ri,0,1))*(1.0-np.clip(genomic_ri,0,1))


def _advance_pair_channels(ecological_ri, genomic_ri, clock, contact, td, generation_time, root_idx, dt, cfg):
    re=ecological_ri.copy(); rg=genomic_ri.copy(); ck=clock.copy(); nd=len(root_idx); gate=sg.SpeciationGateConfig()
    for i in range(nd):
        for j in range(i+1,nd):
            if root_idx[i]!=root_idx[j]:continue
            dg=dt/max(float(generation_time[i]),float(generation_time[j]),1e-9)
            total0=1-(1-re[i,j])*(1-rg[i,j]); e0=sg.effective_exchange_pressure(contact[i,j],total0)
            drive=sg.ecological_isolation_drive(td[i,j],gate)
            ae=gate.ri_build_rate_per_generation*drive*(1-e0); be=gate.ri_decay_rate_per_generation*e0
            if ae+be>0:
                eq=ae/(ae+be); re1=eq+(re[i,j]-eq)*math.exp(-(ae+be)*dg)
            else: re1=re[i,j]
            if cfg.genomic_isolation_enabled:
                ag=cfg.genomic_ri_build_rate_per_generation*(1-e0); bg=cfg.genomic_ri_decay_rate_per_generation*e0
                if ag+bg>0:
                    eq=ag/(ag+bg); rg1=eq+(rg[i,j]-eq)*math.exp(-(ag+bg)*dg)
                else: rg1=rg[i,j]
            else:
                rg1=0.0
            re1=float(np.clip(re1,0,1)); rg1=float(np.clip(rg1,0,1)); total1=1-(1-re1)*(1-rg1)
            e1=sg.effective_exchange_pressure(contact[i,j],total1); em=0.5*(e0+e1)
            ck1=max(0.0,float(ck[i,j])+((1-em)**2-gate.isolation_reconnection_erosion*em)*dg)
            re[i,j]=re[j,i]=re1; rg[i,j]=rg[j,i]=rg1; ck[i,j]=ck[j,i]=ck1
    return re,rg,ck




def _effective_barrier_connectivity(habitat: np.ndarray, permeability: np.ndarray, cfg: DiversificationAdequacyConfig):
    """Species-specific effective connectivity for persistent-vicariance checks.

    The physical land-support permeability remains authoritative.  Habitat only
    acts as an additional filter: a nominal land bridge whose suitability is
    persistently near zero can be a real barrier for one lineage while remaining
    traversable for another.  No new geography is invented.
    """
    p=np.asarray(permeability,dtype=float)
    if not cfg.habitat_barrier_enabled:
        return np.broadcast_to(p,(len(habitat),)+p.shape).copy()
    h=np.clip(np.asarray(habitat,dtype=float),0.0,1.0)
    return p[None,:,:] * np.power(h,max(float(cfg.habitat_connectivity_power),0.0))


def _founder_life_history_min_population(root_sid: str, generation_time_years: float, metadata: dict,
                                          cfg: DiversificationAdequacyConfig) -> float:
    """Life-history-scaled minimum founder abundance in WorldSim units.

    This is deliberately not an individual count.  Longer-generation and slower-
    reproducing lineages require a larger persistent founder component.  The
    absolute scale is a calibrated WorldSim proxy and is sensitivity-tested.
    """
    meta=metadata[root_sid]
    gt=max(float(generation_time_years),1e-9)
    rr=max(float(meta.get("relative_reproduction_rate",1.0)),1e-9)
    return float(cfg.founder_base_minimum_population_units
                 * math.sqrt(gt/max(cfg.founder_generation_reference_years,1e-9))
                 * math.sqrt(max(cfg.founder_reproduction_reference,1e-9)/rr))


def _founder_normalized_variance(indices, totals, va, resource_va, root_idx, root_species_ids, metadata, cfg):
    if len(indices)==0:
        return 0.0
    w=np.asarray(totals[indices],dtype=float)
    if float(w.sum())<=0:
        return 0.0
    vals=[]
    for di in indices:
        sid=root_species_ids[int(root_idx[di])]; meta=metadata[sid]
        scales=np.asarray([
            max(float(meta["thermal_niche_sigma_c"]),1e-6),
            max(float(meta["aridity_niche_sigma"])/1.55,1e-4),
            max(float(cfg.body_mass_scale),1e-6),
        ])
        q=np.asarray(va[di],dtype=float)/(scales*scales)
        if cfg.resource_niche_enabled:
            rq=np.asarray(resource_va[di],dtype=float)/max(cfg.resource_niche_scale**2,1e-12)
            vals.append(float(np.mean(np.concatenate([q,rq]))))
        else:
            vals.append(float(np.mean(q)))
    return float(np.average(np.asarray(vals),weights=w))


def _founder_viability_checks(*, candidate, complement, totals, pop, va, resource_va, generation_time,
                              root_idx, root_species_ids, metadata, persistence_row, cfg):
    branch_pop=float(totals[candidate].sum()); comp_pop=float(totals[complement].sum())
    sid=root_species_ids[int(root_idx[candidate[0]])]
    w=np.asarray(totals[candidate],dtype=float)
    gt=float(np.average(generation_time[candidate],weights=w)) if float(w.sum())>0 else float(np.mean(generation_time[candidate]))
    min_pop=_founder_life_history_min_population(sid,gt,metadata,cfg)
    comp_w=np.asarray(totals[complement],dtype=float)
    comp_gt=float(np.average(generation_time[complement],weights=comp_w)) if float(comp_w.sum())>0 else gt
    comp_min=_founder_life_history_min_population(sid,comp_gt,metadata,cfg)
    ne_proxy=branch_pop*float(cfg.drift_individual_equivalents_per_population_unit)
    q=_founder_normalized_variance(candidate,totals,va,resource_va,root_idx,root_species_ids,metadata,cfg)
    occ=int(np.count_nonzero(np.sum(pop[candidate],axis=0)>cfg.occupancy_floor))
    first=max(float(persistence_row.get("first_population",branch_pop)),1e-15)
    min_seen=float(persistence_row.get("minimum_population",branch_pop))
    decline=min_seen/first
    checks={
        "founder_persistence": float(persistence_row.get("continuous_persistence_years",0.0))+1e-9 >= float(cfg.founder_minimum_persistence_years),
        "founder_life_history_population": branch_pop+1e-15 >= min_pop,
        "complement_life_history_population": comp_pop+1e-15 >= comp_min,
        "founder_effective_size_proxy": ne_proxy+1e-9 >= float(cfg.founder_minimum_effective_size_proxy),
        "founder_genetic_variance": q+1e-15 >= float(cfg.founder_minimum_normalized_additive_variance),
        "founder_spatial_support": occ >= int(cfg.founder_minimum_occupied_cells),
        "founder_no_persistent_collapse": decline+1e-15 >= float(cfg.founder_maximum_persistent_decline_fraction),
    }
    return {
        "gate_ready":bool(all(checks.values())),"checks":checks,
        "branch_population":branch_pop,"complement_population":comp_pop,
        "life_history_minimum_population":min_pop,"complement_minimum_population":comp_min,
        "effective_size_proxy":ne_proxy,"normalized_additive_variance":q,
        "occupied_cells":occ,"minimum_to_first_population_ratio":decline,
        "generation_time_proxy_years":gt,
    }


def _founder_component_key(species_id: str, indices, deme_ids):
    return str(species_id)+"|"+";".join(sorted(str(deme_ids[i]) for i in indices))


def _maybe_speciate_founder(current_species, root_idx, root_species_ids, deme_ids, pop, trait, va,
                            resource_va, generation_time, metadata, contact, td, intrinsic_ri,
                            isolation_clock, registry, child_counters, relative_year, founder_state, cfg):
    """D3.2B component-level birth authority with persistent founder viability.

    Structural reproductive isolation remains D3.0C-authoritative.  The old 5%
    global fraction is not used as birth authority here; it is exported only as
    a diagnostic.  A reproductively isolated component must also demonstrate
    persistent, life-history-scaled demographic viability.
    """
    totals=pop.sum(axis=(1,2)); events=[]; active={}; stats=[]
    extant=sorted(set(current_species))
    gate_cfg=sg.SpeciationGateConfig(minimum_branch_population_fraction=0.0,
                                     minimum_complement_population_fraction=0.0,
                                     minimum_absolute_population=0.0)
    for sid in extant:
        indices=np.array([i for i,x in enumerate(current_species) if x==sid],dtype=int)
        if len(indices)<2: continue
        comps=ar._reproductive_components(indices,contact,td,intrinsic_ri,isolation_clock)
        if len(comps)<2: continue
        comps.sort(key=lambda c:(-float(totals[c].sum()),[deme_ids[i] for i in c]))
        candidate=list(comps[1]); complement=[i for i in indices if i not in candidate]
        branch_pop=float(totals[candidate].sum()); complement_pop=float(totals[complement].sum()); species_pop=branch_pop+complement_pop
        cross=[{"isolation_clock_generations":float(isolation_clock[i,j]),"intrinsic_RI":float(intrinsic_ri[i,j]),
                "trait_distance":float(td[i,j]),"contact_connectivity":float(contact[i,j])}
               for i in candidate for j in complement]
        structural=sg.evaluate_branch_gate(cross_pair_states=cross,branch_population=branch_pop,
                                           complement_population=complement_pop,species_population=species_pop,cfg=gate_cfg)
        if not structural["gate_ready"]: continue
        key=_founder_component_key(sid,candidate,deme_ids); old=(founder_state or {}).get(key)
        if old is None:
            row={"species_id":sid,"deme_ids":[deme_ids[i] for i in candidate],"first_seen_relative_year":float(relative_year),
                 "last_seen_relative_year":float(relative_year),"continuous_persistence_years":0.0,
                 "first_population":branch_pop,"minimum_population":branch_pop,"maximum_population":branch_pop,"last_population":branch_pop}
        else:
            delta=max(0.0,float(relative_year)-float(old.get("last_seen_relative_year",relative_year)))
            row=dict(old); row["last_seen_relative_year"]=float(relative_year); row["continuous_persistence_years"]=float(old.get("continuous_persistence_years",0.0))+delta
            row["minimum_population"]=min(float(old.get("minimum_population",branch_pop)),branch_pop); row["maximum_population"]=max(float(old.get("maximum_population",branch_pop)),branch_pop); row["last_population"]=branch_pop
        active[key]=row
        fv=_founder_viability_checks(candidate=candidate,complement=complement,totals=totals,pop=pop,va=va,resource_va=resource_va,
                                     generation_time=generation_time,root_idx=root_idx,root_species_ids=root_species_ids,metadata=metadata,
                                     persistence_row=row,cfg=cfg)
        stats.append({"key":key,"species_id":sid,"deme_ids":[deme_ids[i] for i in candidate],"structural_gate":structural,"founder_viability":fv,
                      "legacy_branch_fraction":branch_pop/max(species_pop,1e-15)})
        if not fv["gate_ready"]: continue
        root_sid=registry[sid]["root_species_id"]; child_counters[root_sid]+=1; child=ar._species_child_id(root_sid,child_counters[root_sid])
        for i in candidate: current_species[i]=child
        registry[child]={"species_id":child,"parent_species_id":sid,"root_species_id":root_sid,"guild_id":int(registry[sid]["guild_id"]),
                         "birth_relative_year":float(relative_year),"birth_age_ma":float(66.0-relative_year/1_000_000.0),
                         "member_demes_at_birth":[deme_ids[i] for i in candidate],"birth_population":branch_pop,
                         "founder_viability_semantics":"LIFE_HISTORY_PERSISTENCE_EFFECTIVE_SIZE_VARIANCE_SUPPORT","semantic_status":"EMERGENT_SPECIES_OBJECT"}
        events.append({"event":"speciation","relative_year":float(relative_year),"age_ma":float(66.0-relative_year/1_000_000.0),
                       "parent_species_id":sid,"daughter_species_id":child,"root_species_id":root_sid,
                       "daughter_deme_ids":[deme_ids[i] for i in candidate],"daughter_population":branch_pop,
                       "parent_remainder_population":complement_pop,"structural_gate":structural,"founder_viability":fv,
                       "legacy_5pct_branch_fraction_pass":bool(branch_pop/max(species_pop,1e-15)>=0.05),"population_conservation_error":0.0})
        # Once promoted, its candidate timer must not remain active under the old species ID.
        active.pop(key,None)
    if cfg.founder_reset_on_reconnection:
        new_state=active
    else:
        new_state={**(founder_state or {}),**active}
    return events,new_state,stats

def _significant_vicariance_components(di, pop, root_idx, connectivity_surface, cfg):
    """Return significant disconnected components for one deme.

    Components are diagnostic demographic fragments, not species.  The core
    support threshold is inherited from the permeability model; population on
    low-permeability bridge cells does not by itself make the core connected.
    """
    p=np.asarray(pop[di],dtype=float); total=float(p.sum())
    if total<=cfg.deme_fission_min_absolute_population:
        return []
    cs=np.asarray(connectivity_surface,dtype=float)
    if cs.ndim==3:
        cs=cs[di]
    core=cs>=float(cfg.effective_connectivity_core_threshold)
    comps=dd._components((p>cfg.occupancy_floor)&core)
    if len(comps)<2:
        return []
    rows=[]
    for cells in comps:
        mass=float(sum(float(p[i,j]) for i,j in cells))
        rows.append((mass,cells))
    rows.sort(key=lambda x:-x[0])
    root_total=float(pop[root_idx==root_idx[di]].sum())
    return [x for x in rows
            if x[0]>=cfg.deme_fission_min_absolute_population
            and x[0]/max(total,1e-15)>=cfg.deme_fission_min_component_fraction
            and x[0]/max(root_total,1e-15)>=cfg.deme_fission_min_root_species_fraction]


def _update_vicariance_persistence(deme_ids, root_idx, pop, connectivity_surface, relative_year, state, cfg):
    """Update continuous-fragmentation timers and return mature parent demes.

    First detection starts a timer at zero.  Only uninterrupted observations at
    successive fission checkpoints accumulate time.  Reconnection removes the
    timer, so a short-lived interpolated coastline cannot become a persistent
    deme split merely by appearing in one frame.
    """
    prev={str(k):dict(v) for k,v in (state or {}).items()}
    now={}; mature={}; active=set()
    max_gap=max(float(cfg.deme_fission_check_interval_years)*1.01, float(cfg.dt_years)*1.01)
    for di,did in enumerate(deme_ids):
        sig=_significant_vicariance_components(di,pop,root_idx,connectivity_surface,cfg)
        if len(sig)<2:
            continue
        active.add(str(did))
        old=prev.get(str(did))
        if old is None or float(relative_year)-float(old.get('last_seen_relative_year',relative_year))>max_gap:
            row={
                'first_seen_relative_year':float(relative_year),
                'last_seen_relative_year':float(relative_year),
                'continuous_persistence_years':0.0,
                'significant_component_count':int(len(sig)),
            }
        else:
            delta=max(0.0,float(relative_year)-float(old.get('last_seen_relative_year',relative_year)))
            row={
                'first_seen_relative_year':float(old.get('first_seen_relative_year',relative_year)),
                'last_seen_relative_year':float(relative_year),
                'continuous_persistence_years':float(old.get('continuous_persistence_years',0.0))+delta,
                'significant_component_count':int(len(sig)),
            }
        row['largest_component_fraction']=float(sig[0][0]/max(float(pop[di].sum()),1e-15))
        row['secondary_component_fraction']=float(sig[1][0]/max(float(pop[di].sum()),1e-15))
        now[str(did)]=row
        if row['continuous_persistence_years']+1e-9>=float(cfg.vicariance_persistence_min_years):
            mature[str(did)]=dict(row)
    # If reset-on-reconnection is disabled, retain inactive timers but do not
    # accumulate them.  The calibrated candidate keeps the reset enabled.
    if not cfg.vicariance_persistence_reset_on_reconnection:
        for did,row in prev.items():
            if did not in active and did in deme_ids:
                now[did]=row
    return now,mature


def _fission_with_connectivity(deme_ids, root_idx, deme_guild, current_species, pop, trait, va, resource_trait, resource_va, generation_time,
                              eco_ri, genomic_ri, clock, relative_year, lat, lon, connectivity_surface, cfg, eligible_parent_ids=None, persistence_meta=None):
    # Reuse D3.1A semantics, but connected components are defined on stable/permeable terrestrial support.
    old_n=len(deme_ids); additions=[]; counters=defaultdict(int); eligible=set(eligible_parent_ids or deme_ids); persistence_meta=persistence_meta or {}
    for did in deme_ids:
        if "_F" in did:
            stem,_,tail=did.rpartition("_F")
            if tail.isdigit():counters[stem]=max(counters[stem],int(tail))
    for di in range(old_n):
        if str(deme_ids[di]) not in eligible:continue
        p=pop[di]; total=float(p.sum())
        sig=_significant_vicariance_components(di,pop,root_idx,connectivity_surface,cfg)
        if len(sig)<2:continue
        retain=np.ones_like(p,dtype=bool)
        for _,cells in sig[1:]:
            for a,b in cells:retain[a,b]=False
        original=pop[di].copy(); pop[di]=np.where(retain,original,0.0); pdid=deme_ids[di]
        for rank,(mass,cells) in enumerate(sig[1:],1):
            q=np.zeros_like(p)
            for a,b in cells:q[a,b]=original[a,b]
            counters[pdid]+=1; nid=f"{pdid}_F{counters[pdid]:02d}"
            additions.append((di,nid,q,float(q.sum()),rank,dd._weighted_centroid(lat,lon,q)))
    if not additions:
        return (deme_ids,root_idx,deme_guild,current_species,pop,trait,va,resource_trait,resource_va,generation_time,eco_ri,genomic_ri,clock,[])
    newids=list(deme_ids); nr=list(root_idx.astype(int)); ng=list(deme_guild.astype(int)); ns=list(current_species)
    npop=[x.copy() for x in pop]; nz=[x.copy() for x in trait]; nv=[x.copy() for x in va]; rz=[x.copy() for x in resource_trait]; rv=[x.copy() for x in resource_va]; ngen=list(generation_time)
    nnew=old_n+len(additions); nre=ar._copy_expand_square(eco_ri,nnew); nrg=ar._copy_expand_square(genomic_ri,nnew); nck=ar._copy_expand_square(clock,nnew); events=[]
    for k,(parent,nid,q,mass,rank,cent) in enumerate(additions):
        ni=old_n+k; newids.append(nid); nr.append(int(root_idx[parent])); ng.append(int(deme_guild[parent])); ns.append(str(current_species[parent])); npop.append(q); nz.append(trait[parent].copy()); nv.append(va[parent].copy()); rz.append(resource_trait[parent].copy()); rv.append(resource_va[parent].copy()); ngen.append(float(generation_time[parent]))
        for j in range(old_n):
            if j==parent:continue
            if root_idx[j]==root_idx[parent]:
                nre[ni,j]=nre[j,ni]=eco_ri[parent,j]; nrg[ni,j]=nrg[j,ni]=genomic_ri[parent,j]; nck[ni,j]=nck[j,ni]=clock[parent,j]
        pm=persistence_meta.get(str(deme_ids[parent]),{})
        events.append({"event":"deme_fission","relative_year":float(relative_year),"parent_deme_id":deme_ids[parent],"daughter_deme_id":nid,"species_id_at_fission":str(current_species[parent]),"population":mass,"centroid_lat_deg":float(cent[0]),"centroid_lon_deg":float(cent[1]),"vicariance_first_seen_relative_year":float(pm.get("first_seen_relative_year",relative_year)),"vicariance_continuous_persistence_years":float(pm.get("continuous_persistence_years",0.0)),"vicariance_persistence_threshold_years":float(cfg.vicariance_persistence_min_years),"semantic_status":"PERSISTENT_VICARIANCE_DEMOGRAPHIC_FRAGMENT_NOT_SPECIES"})
    return (newids,np.asarray(nr,np.int32),np.asarray(ng,np.uint8),ns,np.stack(npop),np.stack(nz),np.stack(nv),np.stack(rz),np.stack(rv),np.asarray(ngen,float),nre,nrg,nck,events)


def _child_counters(registry):
    return dr._child_counters_from_registry(registry)


def _substrate_for_cfg(a1, relative_year: float, cfg: DiversificationAdequacyConfig):
    if getattr(cfg, "paleogeographic_event_reconstruction_enabled", False):
        return pgh.reconstructed_substrate(
            a1, relative_year, dr._piecewise_substrate,
            older_ma=float(cfg.paleogeographic_event_older_ma),
            younger_ma=float(cfg.paleogeographic_event_younger_ma),
            phase_min=float(cfg.paleogeographic_event_phase_min),
            phase_max=float(cfg.paleogeographic_event_phase_max),
            transition_width_years=float(cfg.paleogeographic_event_transition_width_years),
        )
    return dr._piecewise_substrate(a1, relative_year)


def run(root: Path, cfg: DiversificationAdequacyConfig, initial_result: DiversificationAdequacyResult | None = None) -> DiversificationAdequacyResult:
    if cfg.start_relative_year < 5_000_000.0-1e-9 or cfg.end_relative_year>20_000_000.0+1e-9 or cfg.end_relative_year<=cfg.start_relative_year:
        raise ValueError("D3.2B calibration replay must remain within +5 to +20 Myr")
    data=dr._load_inputs(root,cfg); p=data["parent"]; root_species_ids=p["root_species_id"].tolist(); metadata=data["metadata"]; species_guild=data["baseline"]["guild_id"].astype(np.uint8)
    if initial_result is None:
        if not math.isclose(cfg.start_relative_year,5_000_000.0,abs_tol=1e-9):
            raise ValueError("A continuation after +5 Myr requires initial_result")
        deme_ids=p["deme_id"].tolist(); current_species=p["current_species_id"].tolist(); root_idx=p["root_species_index"].astype(np.int32).copy(); deme_guild=p["guild_id"].astype(np.uint8).copy()
        lat=p["lat"].astype(float); lon=p["lon"].astype(float); pop=p["endpoint_population"].astype(float).copy(); trait=p["endpoint_trait"].astype(float).copy(); va=p["endpoint_additive_variance"].astype(float).copy(); gen=p["generation_time_proxy_years"].astype(float).copy()
        eco_ri=p["endpoint_intrinsic_RI"].astype(float).copy(); genomic_ri=np.zeros_like(eco_ri); clock=p["endpoint_isolation_clock_generations"].astype(float).copy(); resource_trait,resource_va=initialize_resource_state(root_idx,root_species_ids,metadata,cfg)
        registry={r["species_id"]:dict(r) for r in data["parent_registry"]}
    else:
        if not math.isclose(float(initial_result.snapshot_relative_year[-1]),cfg.start_relative_year,abs_tol=1e-6):
            raise ValueError("Continuation start does not match initial_result endpoint")
        deme_ids=list(initial_result.deme_ids); current_species=list(initial_result.current_species_id); root_idx=initial_result.root_species_index.astype(np.int32).copy(); deme_guild=initial_result.guild_id.astype(np.uint8).copy()
        lat=initial_result.lat.astype(float).copy(); lon=initial_result.lon.astype(float).copy(); pop=initial_result.endpoint_population.astype(float).copy(); trait=initial_result.endpoint_trait.astype(float).copy(); va=initial_result.endpoint_additive_variance.astype(float).copy(); resource_trait=initial_result.endpoint_resource_trait.astype(float).copy(); resource_va=initial_result.endpoint_resource_variance.astype(float).copy(); gen=initial_result.generation_time_proxy_years.astype(float).copy()
        eco_ri=initial_result.endpoint_ecological_ri.astype(float).copy(); genomic_ri=initial_result.endpoint_genomic_ri.astype(float).copy(); clock=initial_result.endpoint_isolation_clock_generations.astype(float).copy(); registry={r["species_id"]:dict(r) for r in initial_result.species_registry}
    counters=_child_counters(registry); births=[]; fissions=[]
    vicariance_state={} if initial_result is None else {str(k):dict(v) for k,v in getattr(initial_result,"vicariance_persistence_state",{}).items()}
    old_vstats={} if initial_result is None else dict(getattr(initial_result,"vicariance_calibration_stats",{}))
    vic_unique=set(old_vstats.get("unique_candidate_demes",[]))
    vic_stats={
        "fission_check_count":int(old_vstats.get("fission_check_count",0)),
        "candidate_deme_observations":int(old_vstats.get("candidate_deme_observations",0)),
        "reconnection_reset_count":int(old_vstats.get("reconnection_reset_count",0)),
        "mature_candidate_observations":int(old_vstats.get("mature_candidate_observations",0)),
        "max_continuous_persistence_years":float(old_vstats.get("max_continuous_persistence_years",0.0)),
    }
    founder_state={} if initial_result is None else {str(k):dict(v) for k,v in getattr(initial_result,"founder_viability_state",{}).items()}
    old_fstats={} if initial_result is None else dict(getattr(initial_result,"founder_viability_stats",{}))
    founder_stats={
        "gate_checkpoint_count":int(old_fstats.get("gate_checkpoint_count",0)),
        "structurally_isolated_component_observations":int(old_fstats.get("structurally_isolated_component_observations",0)),
        "mature_viable_component_observations":int(old_fstats.get("mature_viable_component_observations",0)),
        "legacy_5pct_failed_but_founder_passed":int(old_fstats.get("legacy_5pct_failed_but_founder_passed",0)),
        "unique_candidate_keys":list(old_fstats.get("unique_candidate_keys",[])),
    }
    founder_unique=set(founder_stats["unique_candidate_keys"])
    startpop=float(pop.sum()); start_rich=len(set(current_species)); start_demes=len(deme_ids)
    steps=int(round((cfg.end_relative_year-cfg.start_relative_year)/cfg.dt_years)); snap=max(1,int(round(cfg.snapshot_interval_years/cfg.dt_years))); fiss=max(1,int(round(cfg.deme_fission_check_interval_years/cfg.dt_years))); graph_every=max(1,int(round(cfg.pair_graph_refresh_interval_years/cfg.dt_years)))
    snapshots=[cfg.start_relative_year]; richness=[start_rich]; totals=[startpop]; rows=[]
    max_niche_distance=0.; max_genomic_ri=0.; max_total_ri=0.; G=contact=None
    # Establish or preserve species-level ecological capacity anchors at the segment start.
    sub_init=_substrate_for_cfg(data["a1"],cfg.start_relative_year,cfg)
    hab_init,_,_=_habitats_and_resource_targets(pop,trait,resource_trait,root_idx,root_species_ids,species_guild,metadata,sub_init,cfg)
    _ensure_species_ecological_baselines(pop,hab_init,current_species,deme_guild,registry,sub_init,cfg)
    for step in range(1,steps+1):
        t=cfg.start_relative_year+step*cfg.dt_years; sub=_substrate_for_cfg(data["a1"],t,cfg)
        habitat,resource_targets,permeability=_habitats_and_resource_targets(pop,trait,resource_trait,root_idx,root_species_ids,species_guild,metadata,sub,cfg)
        pop=_migration_with_permeability(pop,habitat,permeability,root_idx,root_species_ids,metadata,lat,lon,sub,cfg.dt_years,cfg)
        habitat,resource_targets,permeability=_habitats_and_resource_targets(pop,trait,resource_trait,root_idx,root_species_ids,species_guild,metadata,sub,cfg)
        if cfg.current_species_demography_enabled: pop, species_opp=_current_species_demography(pop,habitat,current_species,root_idx,root_species_ids,deme_guild,metadata,registry,sub,cfg.dt_years,cfg)
        else:
            init_total,init_opp=dr._reconstruct_d31_demography_baseline(data,cfg); pop=ar._demography(pop,habitat,root_idx,root_species_ids,species_guild,metadata,init_total,init_opp,sub,cfg.dt_years)
        if G is None or step % graph_every == 1:
            G,contact,_=_pair_metrics_extended(pop,trait,resource_trait,root_idx,root_species_ids,metadata,lat,lon,permeability,cfg)
        td=_trait_distance_extended(trait,resource_trait,root_idx,root_species_ids,metadata,cfg)
        total_ri=_combined_ri(eco_ri,genomic_ri)
        targets=dd._selection_targets(pop,sub["temperature_c"],sub["aridity_index"]); trait_before=trait.copy(); selected=dd._selection_update(trait,va,targets,root_idx,root_species_ids,metadata,cfg.dt_years,cfg.dynamic_cfg())
        demetot=pop.sum(axis=(1,2)); trait,va,_=av.gene_flow_moment_mix(selected,va,demetot,G,total_ri,root_idx,cfg.variance_cfg()); va,_=av.advance_nonflow_variance(va,trait_before,targets,demetot,gen,root_idx,root_species_ids,metadata,cfg.body_mass_scale,cfg.dt_years,cfg.variance_cfg())
        if cfg.resource_niche_enabled:
            rz_before=resource_trait.copy(); rz_sel=_resource_selection_update(resource_trait,resource_va,resource_targets,root_idx,root_species_ids,metadata,cfg.dt_years,cfg); resource_trait,resource_va,_=av.gene_flow_moment_mix(rz_sel,resource_va,demetot,G,total_ri,root_idx,cfg.variance_cfg()); resource_va=_advance_resource_variance(resource_va,rz_before,resource_targets,demetot,gen,cfg.dt_years,cfg)
        td=_trait_distance_extended(trait,resource_trait,root_idx,root_species_ids,metadata,cfg)
        eco_ri,genomic_ri,clock=_advance_pair_channels(eco_ri,genomic_ri,clock,contact,td,gen,root_idx,cfg.dt_years,cfg); total_ri=_combined_ri(eco_ri,genomic_ri)
        if step%fiss==0:
            effective_connectivity=_effective_barrier_connectivity(habitat,permeability,cfg)
            before_vicariance={str(k):dict(v) for k,v in vicariance_state.items()}
            vicariance_state,mature=_update_vicariance_persistence(deme_ids,root_idx,pop,effective_connectivity,t,vicariance_state,cfg)
            vic_stats["fission_check_count"]+=1
            vic_stats["candidate_deme_observations"]+=len(vicariance_state)
            vic_stats["reconnection_reset_count"]+=len(set(before_vicariance)-set(vicariance_state))
            vic_stats["mature_candidate_observations"]+=len(mature)
            vic_unique.update(vicariance_state)
            if vicariance_state:
                vic_stats["max_continuous_persistence_years"]=max(vic_stats["max_continuous_persistence_years"],max(float(v.get("continuous_persistence_years",0.0)) for v in vicariance_state.values()))
            if cfg.transient_vicariance_fission_enabled and mature:
                mature_ids=set(mature)
                (deme_ids,root_idx,deme_guild,current_species,pop,trait,va,resource_trait,resource_va,gen,eco_ri,genomic_ri,clock,newf)=_fission_with_connectivity(deme_ids,root_idx,deme_guild,current_species,pop,trait,va,resource_trait,resource_va,gen,eco_ri,genomic_ri,clock,t,lat,lon,effective_connectivity,cfg,mature_ids,mature)
                for e in newf:
                    e["root_species_id"]=root_species_ids[int(root_idx[deme_ids.index(e["daughter_deme_id"])])]
                if newf:
                    split_parents={str(e["parent_deme_id"]) for e in newf}
                    vicariance_state={k:v for k,v in vicariance_state.items() if k not in split_parents}
                fissions.extend(newf)
                if newf:
                    G,contact,_=_pair_metrics_extended(pop,trait,resource_trait,root_idx,root_species_ids,metadata,lat,lon,permeability,cfg); td=_trait_distance_extended(trait,resource_trait,root_idx,root_species_ids,metadata,cfg); total_ri=_combined_ri(eco_ri,genomic_ri)
        if cfg.speciation_enabled and step%snap==0:
            founder_stats["gate_checkpoint_count"]+=1
            if cfg.founder_viability_enabled:
                newb,founder_state,founder_rows=_maybe_speciate_founder(
                    current_species,root_idx,root_species_ids,deme_ids,pop,trait,va,resource_va,gen,metadata,
                    contact,td,total_ri,clock,registry,counters,t,founder_state,cfg)
                founder_stats["structurally_isolated_component_observations"]+=len(founder_rows)
                for rr in founder_rows:
                    founder_unique.add(rr["key"])
                    if rr["founder_viability"]["gate_ready"]:
                        founder_stats["mature_viable_component_observations"]+=1
                        if rr["legacy_branch_fraction"]<0.05:
                            founder_stats["legacy_5pct_failed_but_founder_passed"]+=1
            else:
                newb=ar._maybe_speciate(current_species,root_idx,root_species_ids,deme_ids,pop,contact,td,total_ri,clock,registry,counters,t)
                founder_rows=[]
            _split_ecological_baseline_after_births(registry,newb,habitat,current_species,deme_guild,sub,cfg)
            births.extend(newb)
        if step%snap==0 or step==steps:
            snapshots.append(t); richness.append(len(set(current_species))); totals.append(float(pop.sum()));
            mask=np.triu(root_idx[:,None]==root_idx[None,:],1)
            if np.any(mask):
                max_niche_distance=max(max_niche_distance,float(np.max(td[mask]))); max_genomic_ri=max(max_genomic_ri,float(np.max(genomic_ri[mask]))); max_total_ri=max(max_total_ri,float(np.max(total_ri[mask])))
            rows.append({"relative_year":float(t),"age_ma":float(sub["age_ma"]),"species_richness":len(set(current_species)),"deme_count":len(deme_ids),"total_population":float(pop.sum()),"speciation_events_cumulative":len(births),"fission_events_cumulative":len(fissions),"max_trait_distance":float(np.max(td[mask])) if np.any(mask) else 0.,"max_genomic_RI":float(np.max(genomic_ri[mask])) if np.any(mask) else 0.,"max_total_RI":float(np.max(total_ri[mask])) if np.any(mask) else 0.})
    G,contact,td=_pair_metrics_extended(pop,trait,resource_trait,root_idx,root_species_ids,metadata,lat,lon,permeability,cfg); total_ri=_combined_ri(eco_ri,genomic_ri)
    final_species=sorted(set(current_species)); diversified=defaultdict(int)
    for sid in final_species: diversified[registry[sid]["root_species_id"]]+=1
    diag={"status":STATUS,"config":asdict(cfg),"parent":"v0.6.3D3.1A","segment_start_relative_year":float(cfg.start_relative_year),"segment_end_relative_year":float(cfg.end_relative_year),"control_comparison_parent":"v0.6.3D3.2A","initial_species_richness":start_rich,"final_species_richness":len(final_species),"new_speciation_event_count":len(births),"initial_deme_count":start_demes,"final_deme_count":len(deme_ids),"new_deme_fission_event_count":len(fissions),"initial_total_population":startpop,"final_total_population":float(pop.sum()),"resource_niche_axes":2,"resource_niche_semantics":"HERITABLE_LOCAL_RESOURCE_COMPOSITION_AXES_NOT_AUTHORIAL_PROFESSIONS_OR_NARRATIVE_TRAITS","genomic_isolation_channel":"STATEFUL_NON_ECOLOGICAL_INCOMPATIBILITY_CHANNEL","demography_authority":"CURRENT_EXTANT_SPECIES_WITH_NO_AUTOMATIC_DAUGHTER_BONUS","transient_vicariance_authority":"LAND_SUPPORT_X_SPECIES_HABITAT_EFFECTIVE_CONNECTIVITY_DERIVED_FROM_EXISTING_PHYSICAL_PROVIDER","transient_vicariance_fission_authority":"OFF_PENDING_PERSISTENCE_CALIBRATION" if not cfg.transient_vicariance_fission_enabled else "ON_WITH_CONTINUOUS_PERSISTENCE_GATE","vicariance_persistence_min_years":float(cfg.vicariance_persistence_min_years),"active_vicariance_persistence_timers_at_endpoint":len(vicariance_state),"vicariance_calibration_stats":{**vic_stats,"unique_candidate_demes":sorted(vic_unique)},"founder_viability_authority":"LIFE_HISTORY_PERSISTENCE_EFFECTIVE_SIZE_GENETIC_VARIANCE_SPATIAL_SUPPORT","founder_viability_stats":{**founder_stats,"unique_candidate_keys":sorted(founder_unique)},"legacy_global_5pct_branch_fraction_birth_authority":False,"max_extended_trait_distance":max_niche_distance,"max_genomic_RI":max_genomic_ri,"max_total_RI":max_total_ri,"diversified_root_lineages":{k:v for k,v in diversified.items() if v>1},"snapshot_rows":rows,"Deep_adaptation_enabled":False,"dragon_lineage_selection_enabled":False,"sapience_enabled":False,"civilization_enabled":False,"author_selected_winner_enabled":False,"global_speciation_rate":None,"global_radiation_boost":False,"interpretation":"D3.2B calibrates founder-lineage persistence/viability and species-specific effective physical-habitat barriers. Earth analogues constrain mechanism behavior but do not prescribe target richness."}
    return DiversificationAdequacyResult(root_species_ids,final_species,deme_ids,list(current_species),root_idx,deme_guild,lat,lon,np.asarray(snapshots),np.asarray(richness,np.int32),np.asarray(totals),pop,trait,va,resource_trait,resource_va,gen,eco_ri,genomic_ri,total_ri,clock,contact,td,[registry[k] for k in sorted(registry)],births,fissions,{str(k):dict(v) for k,v in vicariance_state.items()},{**vic_stats,"unique_candidate_demes":sorted(vic_unique)},{str(k):dict(v) for k,v in founder_state.items()},{**founder_stats,"unique_candidate_keys":sorted(founder_unique)},diag)


def write_outputs(root: Path, result: DiversificationAdequacyResult):
    out=Path(root)/"outputs/hybrid1/diversification_adequacy_v0_6_3D3_2A"; out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/"diversification_adequacy_state.npz",root_species_id=np.asarray(result.root_species_ids),final_species_id=np.asarray(result.final_species_ids),deme_id=np.asarray(result.deme_ids),current_species_id=np.asarray(result.current_species_id),root_species_index=result.root_species_index,guild_id=result.guild_id,lat=result.lat.astype(np.float32),lon=result.lon.astype(np.float32),snapshot_relative_year=result.snapshot_relative_year,species_richness_history=result.species_richness_history,total_population_history=result.total_population_history,endpoint_population=result.endpoint_population,endpoint_trait=result.endpoint_trait,endpoint_additive_variance=result.endpoint_additive_variance,endpoint_resource_trait=result.endpoint_resource_trait,endpoint_resource_variance=result.endpoint_resource_variance,generation_time_proxy_years=result.generation_time_proxy_years,endpoint_ecological_RI=result.endpoint_ecological_ri,endpoint_genomic_RI=result.endpoint_genomic_ri,endpoint_intrinsic_RI=result.endpoint_intrinsic_RI,endpoint_isolation_clock_generations=result.endpoint_isolation_clock_generations,endpoint_contact_connectivity=result.endpoint_contact_connectivity,endpoint_trait_distance=result.endpoint_trait_distance)
    (out/"diversification_adequacy_diagnostics.json").write_text(json.dumps(result.diagnostics,indent=2,sort_keys=True),encoding="utf-8")
    (out/"speciation_events_5_20myr.json").write_text(json.dumps({"events":result.speciation_events},indent=2,sort_keys=True),encoding="utf-8")
    (out/"deme_fission_events_5_20myr.json").write_text(json.dumps({"events":result.deme_fission_events},indent=2,sort_keys=True),encoding="utf-8")
    (out/"species_registry.json").write_text(json.dumps({"species":result.species_registry},indent=2,sort_keys=True),encoding="utf-8")
    (out/"vicariance_persistence_state.json").write_text(json.dumps({"timers":result.vicariance_persistence_state},indent=2,sort_keys=True),encoding="utf-8")
    (out/"vicariance_calibration_stats.json").write_text(json.dumps(result.vicariance_calibration_stats,indent=2,sort_keys=True),encoding="utf-8")
    (out/"founder_viability_state.json").write_text(json.dumps({"timers":result.founder_viability_state},indent=2,sort_keys=True),encoding="utf-8")
    (out/"founder_viability_stats.json").write_text(json.dumps(result.founder_viability_stats,indent=2,sort_keys=True),encoding="utf-8")
    return out

# --- synthetic calibration controls ---
def synthetic_controls(cfg: DiversificationAdequacyConfig):
    # Resource niche: differing resources diverge; same target does not.
    z=np.array([[0.,0.],[0.,0.]]); v=np.full((2,2),cfg.resource_initial_normalized_va*cfg.resource_niche_scale**2); targ=np.array([[-0.8,0.0],[0.8,0.0]])
    ids=[0,0]; roots=["X"]; md={"X":{"relative_reproduction_rate":1.0}}; zz=z.copy()
    for _ in range(20): zz=_resource_selection_update(zz,v,targ,np.array(ids),roots,md,100_000.,cfg)
    resource_div=float(np.linalg.norm(zz[0]-zz[1]))
    zsame=np.array([[0.,0.],[0.,0.]])
    for _ in range(20): zsame=_resource_selection_update(zsame,v,np.zeros((2,2)),np.array(ids),roots,md,100_000.,cfg)
    # Genomic channel: long isolation builds RI; short isolation doesn't; contact erodes.
    re=np.zeros((2,2)); rg=np.zeros((2,2)); ck=np.zeros((2,2)); c=np.zeros((2,2)); td=np.zeros((2,2)); gt=np.array([5.,5.]); ridx=np.array([0,0])
    for _ in range(20): re,rg,ck=_advance_pair_channels(re,rg,ck,c,td,gt,ridx,250_000.,cfg)
    long_iso=float(rg[0,1])
    re2=np.zeros((2,2)); rg2=np.zeros((2,2)); ck2=np.zeros((2,2))
    re2,rg2,ck2=_advance_pair_channels(re2,rg2,ck2,c,td,gt,ridx,250_000.,cfg); short_iso=float(rg2[0,1])
    c1=np.zeros((2,2)); c1[0,1]=c1[1,0]=1.0
    for _ in range(10): re,rg,ck=_advance_pair_channels(re,rg,ck,c1,td,gt,ridx,250_000.,cfg)
    after_contact=float(rg[0,1])
    # Vicariance permeability monotonicity.
    ls=np.array([[0.1,0.25,0.5,1.0]]); perm=_connectivity_permeability(ls,cfg)[0]
    # Persistence gate: a transient split must reset, while uninterrupted
    # fragmentation matures exactly by biological/geographic elapsed time.
    vcfg=cfg
    vp=np.array([[[0.0,1.0,0.5,1.0,0.0]]],dtype=float)
    vr=np.array([0],dtype=np.int32); vids=["X_P001"]
    split_perm=np.array([[1.0,1.0,0.0,1.0,1.0]],dtype=float)
    open_perm=np.ones((1,5),dtype=float)
    st,m0=_update_vicariance_persistence(vids,vr,vp,split_perm,0.0,{},vcfg)
    st,m1=_update_vicariance_persistence(vids,vr,vp,split_perm,500_000.0,st,vcfg)
    st_reset,mreset=_update_vicariance_persistence(vids,vr,vp,open_perm,1_000_000.0,st,vcfg)
    st2,_=_update_vicariance_persistence(vids,vr,vp,split_perm,0.0,{},vcfg)
    st2,_=_update_vicariance_persistence(vids,vr,vp,split_perm,500_000.0,st2,vcfg)
    st2,mmature=_update_vicariance_persistence(vids,vr,vp,split_perm,1_000_000.0,st2,vcfg)
    return {"resource_divergence_after_2myr":resource_div,"resource_same_target_shift":float(np.max(np.abs(zsame))),"genomic_RI_after_5myr_at_5yr_generation":long_iso,"genomic_RI_after_0_25myr_at_5yr_generation":short_iso,"genomic_RI_after_secondary_contact":after_contact,"permeability_0_10_0_25_0_50_1_00":perm.tolist(),"vicariance_persistence_transient_matures":bool(m0 or m1 or mreset),"vicariance_persistence_reset_timer_count":len(st_reset),"vicariance_persistence_mature_after_1myr":bool(mmature),"checks":{"resource_diverges":resource_div>0.05,"same_resource_no_directional_shift":float(np.max(np.abs(zsame)))<1e-12,"short_genomic_isolation_not_species_level":short_iso<0.1,"long_genomic_isolation_material":long_iso>0.3,"secondary_contact_erodes_genomic_RI":after_contact<long_iso,"permeability_monotonic":bool(np.all(np.diff(perm)>0)),"transient_vicariance_does_not_mature":not bool(m0 or m1 or mreset),"reconnection_resets_vicariance_timer":len(st_reset)==0,"persistent_vicariance_matures":bool(mmature)}}
