from __future__ import annotations

from dataclasses import asdict, dataclass, field
from collections import defaultdict
from pathlib import Path
import json, math
import numpy as np

from . import diversification_adequacy as da
from . import diversity_recovery as dr
from . import dynamic_demes as dd
from . import additive_variance as av
from . import trophic_mode as tm

STATUS = "PASS_BACKGROUND_EXTINCTION_ORDINARY_TURNOVER_CALIBRATION_CANDIDATE"


@dataclass(frozen=True)
class OrdinaryTurnoverConfig(da.DiversificationAdequacyConfig):
    # D3.2D deterministic ordinary-extinction authority. There is deliberately
    # no global random extinction rate. A lineage must remain persistently below
    # a life-history viability floor while showing ecological/range/density
    # failure and no material demographic recovery.
    background_species_extinction_enabled: bool = True
    ordinary_extinction_check_interval_years: float = 500_000.0
    ordinary_extinction_minimum_persistence_years: float = 2_000_000.0
    ordinary_extinction_founder_floor_fraction: float = 0.05
    ordinary_extinction_max_opportunity_ratio: float = 0.15
    ordinary_extinction_max_range_ratio: float = 0.10
    ordinary_extinction_max_density_ratio: float = 0.15
    ordinary_extinction_max_population_ratio_to_episode_start: float = 0.90
    ordinary_extinction_recovery_reset_factor: float = 1.25
    ordinary_extinction_minimum_species_age_years: float = 2_000_000.0
    ordinary_extinction_remove_all_demes_atomically: bool = True

    # D3.3B functional-guild reassignment at taxonomic birth.  The calibrated
    # scope addresses the long-horizon blocker demonstrated in D3.3: a vacant
    # apex functional tier could never be reoccupied because daughters inherited
    # parent guild_id unconditionally. Cross-trophic-mode evolution remains OFF
    # because no independent heritable trophic-mode axis exists yet.
    functional_guild_transition_enabled: bool = False
    functional_guild_transition_at_speciation_only: bool = True
    functional_guild_cross_trophic_transitions_enabled: bool = False
    functional_guild_apex_reoccupation_enabled: bool = True
    functional_guild_apex_source_guild_id: int = 5
    functional_guild_apex_target_guild_id: int = 6
    functional_guild_apex_requires_vacancy: bool = True
    functional_guild_apex_min_body_rank: float = 0.75
    functional_guild_apex_min_resource_affinity: float = 0.65
    functional_guild_apex_resource_sigma: float = 0.75
    functional_guild_apex_min_capacity_founder_multiple: float = 2.0
    functional_guild_apex_capacity_reconstruction_enabled: bool = True
    functional_guild_apex_capacity_pre_cha1_min_age_ma: float = 66.0

    # D3.3B2.0 latent heritable trophic-mode state. This stage intentionally
    # does not let tau alter habitat, guild identity, speciation authority, or
    # carrying/opportunity accounting. It only establishes the quantitative-
    # genetic state needed for a later cross-trophic functional authority.
    trophic_mode_enabled: bool = False
    # OFF in B2.0: existing forage and prey fields are not yet expressed in a
    # common cross-trophic energetic/opportunity currency. Enabling a mean
    # response before that calibration would create an arbitrary omnivory drift.
    trophic_mode_environmental_selection_enabled: bool = False
    trophic_mode_scale: float = 0.50
    trophic_mode_initial_plant_anchor: float = 0.02
    trophic_mode_initial_animal_anchor: float = 0.98
    trophic_mode_initial_normalized_va: float = 0.012
    trophic_mode_response_timescale_years: float = 500_000.0
    trophic_mode_gene_flow_reference_step_years: float = 25_000.0
    trophic_mode_mutation_variance_supply_normalized_per_myr: float = 0.001
    trophic_mode_variance_ceiling_normalized: float = 0.05
    trophic_mode_baseline_stabilizing_variance_depletion_per_generation: float = 0.0
    trophic_mode_nonlinear_stabilizing_variance_depletion_per_myr_per_q: float = 0.4938271604938272
    trophic_mode_selection_variance_depletion_per_generation: float = 2.0e-8
    trophic_mode_selection_pressure_ceiling: float = 4.0
    # D3.3B2.1 common cross-trophic opportunity currency.  This uses current
    # forage converted into contemporaneous reference-herbivore support units and
    # current realized herbivore abundance as prey in the same WorldSim units.
    # It is not physical joules and does not turn A1 carrying_capacity into N.
    trophic_mode_common_currency_enabled: bool = False
    trophic_mode_common_support_floor_fraction: float = 0.05
    trophic_mode_log_opportunity_clip: float = 4.0
    trophic_mode_specialization_barrier_log_ratio: float = 1.5
    trophic_mode_selection_signal_clip: float = 6.0
    trophic_mode_selection_signal_scale: float = 1.0
    trophic_mode_selection_internal_max_step_years: float = 25_000.0
    # D3.3B2.2: tau becomes ecological routing authority but still cannot
    # authorize guild reassignment or speciation. Both plant and prey channels
    # are evaluated continuously in the B2.1 common support currency.
    trophic_mode_continuous_resource_routing_enabled: bool = False

    # D3.3B2.3: cross-trophic functional reassignment remains strictly bound to
    # an independently-authorized taxonomic birth.  tau does not create species
    # and there is no global/random guild-transition rate.  Current functional
    # guilds, rather than immutable root guilds, define the herbivore prey pool;
    # the focal species is excluded from its own prey opportunity (cannibalism is
    # not an authority in this layer).
    trophic_mode_cross_guild_transition_authority_enabled: bool = False
    trophic_mode_current_functional_prey_field_enabled: bool = False
    trophic_mode_exclude_same_species_from_prey_opportunity: bool = False
    cross_trophic_min_dominant_routing_share: float = 0.75
    cross_trophic_min_realized_resource_share: float = 0.75
    cross_trophic_min_target_capacity_founder_multiple: float = 2.0
    cross_trophic_plant_to_animal_target_guild_id: int = 5
    cross_trophic_allow_plant_to_animal: bool = True
    cross_trophic_allow_animal_to_plant: bool = True
    cross_trophic_direct_plant_to_apex_enabled: bool = False


@dataclass
class OrdinaryTurnoverResult(da.DiversificationAdequacyResult):
    extinction_events: list[dict]
    extinction_persistence_state: dict
    extinction_stats: dict
    functional_guild_transition_events: list[dict] = field(default_factory=list)
    functional_guild_stats: dict = field(default_factory=dict)
    endpoint_trophic_mode: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=float))
    endpoint_trophic_mode_variance: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=float))
    endpoint_trophic_mode_target: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=float))
    trophic_mode_stats: dict = field(default_factory=dict)


def _read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_config(path: Path) -> OrdinaryTurnoverConfig:
    raw = _read_json(path)
    fields = OrdinaryTurnoverConfig.__dataclass_fields__
    return OrdinaryTurnoverConfig(**{k: raw[k] for k in fields if k in raw})


def _species_indices(current_species, sid: str):
    return np.asarray([i for i, x in enumerate(current_species) if x == sid], dtype=np.int32)


def _occupied_cells(pop, indices, occupancy_floor: float) -> int:
    if len(indices) == 0:
        return 0
    return int(np.count_nonzero(np.sum(pop[indices], axis=0) > occupancy_floor))


def _ensure_extinction_baselines(pop, current_species, registry, cfg: OrdinaryTurnoverConfig, relative_year: float):
    for sid in sorted(set(current_species)):
        idx = _species_indices(current_species, sid)
        n = float(pop[idx].sum())
        occ = _occupied_cells(pop, idx, cfg.occupancy_floor)
        row = registry[sid]
        row.setdefault("ordinary_extinction_baseline_population", n)
        row.setdefault("ordinary_extinction_baseline_occupied_cells", max(occ, 1))
        row.setdefault("ordinary_extinction_baseline_relative_year", float(relative_year))
        row.setdefault("ordinary_extinction_baseline_semantics", "EXTANT_SPECIES_REFERENCE_RESET_AT_TAXONOMIC_BIRTH_NOT_A_GLOBAL_EXTINCTION_RATE")


def _reset_extinction_baselines_after_births(registry, births, pop, current_species, cfg, relative_year):
    if not births:
        return
    for e in births:
        for sid in (e["parent_species_id"], e["daughter_species_id"]):
            idx = _species_indices(current_species, sid)
            if len(idx) == 0:
                continue
            row = registry[sid]
            row["ordinary_extinction_baseline_population"] = float(pop[idx].sum())
            row["ordinary_extinction_baseline_occupied_cells"] = max(_occupied_cells(pop, idx, cfg.occupancy_floor), 1)
            row["ordinary_extinction_baseline_relative_year"] = float(relative_year)
            row["ordinary_extinction_baseline_semantics"] = "RESET_AT_SPECIATION_TO_AVOID_TREATING_RANGE_PARTITION_AS_EXTINCTION_DECLINE"


def _root_sid_for_species(sid, current_species, root_idx, root_species_ids):
    idx = _species_indices(current_species, sid)
    if len(idx) == 0:
        raise KeyError(sid)
    return root_species_ids[int(root_idx[int(idx[0])])]


def _species_generation_time(indices, pop, generation_time):
    w = pop[indices].sum(axis=(1, 2))
    if float(w.sum()) > 0:
        return float(np.average(generation_time[indices], weights=w))
    return float(np.mean(generation_time[indices]))


def _species_extinction_metrics(*, sid, pop, current_species, root_idx, root_species_ids, generation_time,
                                metadata, registry, opportunity, relative_year, cfg):
    idx = _species_indices(current_species, sid)
    n = float(pop[idx].sum())
    occ = _occupied_cells(pop, idx, cfg.occupancy_floor)
    gt = _species_generation_time(idx, pop, generation_time)
    root_sid = root_species_ids[int(root_idx[int(idx[0])])]
    founder_min = da._founder_life_history_min_population(root_sid, gt, metadata, cfg)
    row = registry[sid]
    base_n = max(float(row.get("ordinary_extinction_baseline_population", n)), 1e-15)
    base_occ = max(float(row.get("ordinary_extinction_baseline_occupied_cells", max(occ, 1))), 1.0)
    base_opp = max(float(row.get("ecological_baseline_opportunity", max(opportunity.get(sid, 0.0), 1e-15))), 1e-15)
    pop_to_founder = n / max(founder_min, 1e-15)
    population_ratio = n / base_n
    range_ratio = occ / base_occ
    opportunity_ratio = float(opportunity.get(sid, 0.0)) / base_opp
    density_ratio = population_ratio / max(range_ratio, 1e-12)
    birth_raw = row.get("birth_relative_year")
    if birth_raw is None:
        birth_raw = row.get("ordinary_extinction_baseline_relative_year", 5_000_000.0)
    birth = float(birth_raw)
    species_age = max(0.0, float(relative_year) - birth)
    low_population = pop_to_founder <= float(cfg.ordinary_extinction_founder_floor_fraction)
    ecological_failure = (
        opportunity_ratio <= float(cfg.ordinary_extinction_max_opportunity_ratio)
        or range_ratio <= float(cfg.ordinary_extinction_max_range_ratio)
        or density_ratio <= float(cfg.ordinary_extinction_max_density_ratio)
    )
    old_enough = species_age + 1e-9 >= float(cfg.ordinary_extinction_minimum_species_age_years)
    return {
        "species_id": sid,
        "root_species_id": root_sid,
        "population": n,
        "occupied_cells": occ,
        "generation_time_proxy_years": gt,
        "founder_minimum_population": founder_min,
        "population_to_founder_floor": pop_to_founder,
        "population_ratio_to_extinction_baseline": population_ratio,
        "range_ratio_to_extinction_baseline": range_ratio,
        "opportunity_ratio_to_ecological_baseline": opportunity_ratio,
        "density_ratio_to_extinction_baseline": density_ratio,
        "species_age_years": species_age,
        "low_population": bool(low_population),
        "ecological_or_range_failure": bool(ecological_failure),
        "old_enough": bool(old_enough),
        "stress_predicate": bool(low_population and ecological_failure and old_enough),
    }


def _update_extinction_persistence(*, pop, current_species, root_idx, root_species_ids, generation_time,
                                   metadata, registry, opportunity, relative_year, state, cfg):
    new_state = {str(k): dict(v) for k, v in state.items()}
    mature = []
    rows = []
    extant = set(current_species)
    for sid in list(new_state):
        if sid not in extant:
            new_state.pop(sid, None)
    for sid in sorted(extant):
        m = _species_extinction_metrics(
            sid=sid, pop=pop, current_species=current_species, root_idx=root_idx,
            root_species_ids=root_species_ids, generation_time=generation_time,
            metadata=metadata, registry=registry, opportunity=opportunity,
            relative_year=relative_year, cfg=cfg,
        )
        if not m["stress_predicate"]:
            new_state.pop(sid, None)
            rows.append({**m, "continuous_stress_years": 0.0, "mature": False, "reset_reason": "STRESS_PREDICATE_FALSE"})
            continue
        st = new_state.get(sid)
        if st is None:
            st = {
                "start_relative_year": float(relative_year),
                "last_relative_year": float(relative_year),
                "first_population": float(m["population"]),
                "minimum_population": float(m["population"]),
                "continuous_stress_years": 0.0,
            }
        else:
            min_seen = min(float(st.get("minimum_population", m["population"])), float(m["population"]))
            # A substantial rebound starts a new stress episode even if the
            # lineage remains below the conservative floor.
            if float(m["population"]) > min_seen * float(cfg.ordinary_extinction_recovery_reset_factor):
                st = {
                    "start_relative_year": float(relative_year),
                    "last_relative_year": float(relative_year),
                    "first_population": float(m["population"]),
                    "minimum_population": float(m["population"]),
                    "continuous_stress_years": 0.0,
                }
            else:
                st["last_relative_year"] = float(relative_year)
                st["minimum_population"] = min_seen
                st["continuous_stress_years"] = float(relative_year) - float(st["start_relative_year"])
        new_state[sid] = st
        decline_ratio = float(m["population"]) / max(float(st["first_population"]), 1e-15)
        persistent = float(st["continuous_stress_years"]) + 1e-9 >= float(cfg.ordinary_extinction_minimum_persistence_years)
        nonrecovering = decline_ratio <= float(cfg.ordinary_extinction_max_population_ratio_to_episode_start)
        is_mature = bool(persistent and nonrecovering)
        row = {**m, **st, "episode_population_ratio": decline_ratio, "persistent": bool(persistent), "nonrecovering": bool(nonrecovering), "mature": is_mature}
        rows.append(row)
        if is_mature:
            mature.append(row)
    return new_state, mature, rows


def _remove_extinct_species(*, extinct_rows, deme_ids, current_species, root_idx, deme_guild, pop, trait, va,
                            resource_trait, resource_va, generation_time, ecological_ri, genomic_ri, clock,
                            registry, relative_year, cfg):
    extinct_ids = sorted({r["species_id"] for r in extinct_rows})
    if not extinct_ids:
        return (deme_ids, current_species, root_idx, deme_guild, pop, trait, va, resource_trait, resource_va,
                generation_time, ecological_ri, genomic_ri, clock, [], np.ones(len(deme_ids), dtype=bool))
    if not cfg.ordinary_extinction_remove_all_demes_atomically:
        raise ValueError("D3.2D requires atomic species-level deme removal")
    keep = np.asarray([sid not in set(extinct_ids) for sid in current_species], dtype=bool)
    events = []
    for r in extinct_rows:
        sid = r["species_id"]
        idx = [i for i, x in enumerate(current_species) if x == sid]
        removed_demes = [deme_ids[i] for i in idx]
        ev = {
            "event": "ordinary_background_extinction",
            "species_id": sid,
            "root_species_id": r["root_species_id"],
            "relative_year": float(relative_year),
            "age_ma": float(66.0 - relative_year / 1_000_000.0),
            "removed_deme_ids": removed_demes,
            "population_immediately_before_extinction": float(r["population"]),
            "occupied_cells_immediately_before_extinction": int(r["occupied_cells"]),
            "continuous_stress_years": float(r["continuous_stress_years"]),
            "population_to_founder_floor": float(r["population_to_founder_floor"]),
            "opportunity_ratio_to_ecological_baseline": float(r["opportunity_ratio_to_ecological_baseline"]),
            "range_ratio_to_extinction_baseline": float(r["range_ratio_to_extinction_baseline"]),
            "density_ratio_to_extinction_baseline": float(r["density_ratio_to_extinction_baseline"]),
            "episode_population_ratio": float(r["episode_population_ratio"]),
            "authority": "PERSISTENT_DETERMINISTIC_NONVIABILITY_GATE_NO_GLOBAL_RANDOM_EXTINCTION_RATE",
        }
        events.append(ev)
        rr = registry[sid]
        rr["extinct"] = True
        rr["extinction_relative_year"] = float(relative_year)
        rr["extinction_age_ma"] = ev["age_ma"]
        rr["extinction_cause"] = "ORDINARY_BACKGROUND_TURNOVER_PERSISTENT_NONVIABILITY"
        rr["extinction_event"] = ev
    ix = np.where(keep)[0]
    ecological_ri = ecological_ri[np.ix_(ix, ix)]
    genomic_ri = genomic_ri[np.ix_(ix, ix)]
    clock = clock[np.ix_(ix, ix)]
    return (
        [x for i, x in enumerate(deme_ids) if keep[i]],
        [x for i, x in enumerate(current_species) if keep[i]],
        root_idx[keep], deme_guild[keep], pop[keep], trait[keep], va[keep], resource_trait[keep], resource_va[keep],
        generation_time[keep], ecological_ri, genomic_ri, clock, events, keep,
    )



def _apex_resource_centroid(metadata: dict) -> np.ndarray:
    rows=[m for m in metadata.values() if int(m.get("guild_id",-1))==6]
    if not rows:
        return np.zeros(2,dtype=float)
    return np.mean(np.stack([da._initial_resource_pref(m) for m in rows]),axis=0)


def _rank01(values: dict[str,float]) -> dict[str,float]:
    if not values:return {}
    uniq=sorted(set(float(v) for v in values.values()))
    if len(uniq)==1:return {k:1.0 for k in values}
    pos={v:i/(len(uniq)-1) for i,v in enumerate(uniq)}
    return {k:float(pos[float(v)]) for k,v in values.items()}


def _pre_cha1_apex_to_herbivore_ratio(a1, cfg) -> float:
    ages=np.asarray(a1["age_ma"],dtype=float)
    pop=np.asarray(a1["population"],dtype=float)
    mask=ages+1e-12>=float(cfg.functional_guild_apex_capacity_pre_cha1_min_age_ma)
    if not np.any(mask):
        raise ValueError("D3.3B apex capacity reconstruction has no pre-CHA1 reference frames")
    herb=pop[mask,:4].sum(axis=(1,2,3)); apex=pop[mask,5].sum(axis=(1,2))
    ratios=np.divide(apex,herb,out=np.zeros_like(apex),where=herb>1e-15)
    ratios=ratios[np.isfinite(ratios)&(ratios>0)]
    if not len(ratios):
        raise ValueError("D3.3B cannot derive positive apex/herbivore capacity ratio")
    # D3.3B1 uses the conservative lower envelope of observed pre-CHA1
    # apex/herbivore reference ratios. This is intentionally not a median:
    # the B1 release gate was calibrated against the minimum positive frame.
    return float(np.min(ratios))


def _reconstructed_apex_reference_field(a1, sub, cfg):
    """Return the cellwise achievable apex reference field under B1 accounting.

    The conservative pre-CHA1 lower-envelope target is *not* added on top of
    the predator reference budget.  Only the increment above the legacy target
    field is requested, and that increment is transferred cell-by-cell from
    source guild 5, capped by the source capacity available in each cell.
    """
    ratio=_pre_cha1_apex_to_herbivore_ratio(a1,cfg)
    rp=np.asarray(sub["reference_population"],dtype=float)
    source_i=int(cfg.functional_guild_apex_source_guild_id)-1
    target_i=int(cfg.functional_guild_apex_target_guild_id)-1
    herb=rp[:4].sum(axis=0)
    desired=herb*ratio
    target_before=rp[target_i]
    source_before=rp[source_i]
    requested=np.maximum(desired-target_before,0.0)
    transferred=np.minimum(requested,source_before)
    target_after=target_before+transferred
    return target_after,ratio


def _apex_capacity_transfer_accounting(a1, sub, cfg):
    rp=np.asarray(sub["reference_population"],dtype=float)
    source_i=int(cfg.functional_guild_apex_source_guild_id)-1
    target_i=int(cfg.functional_guild_apex_target_guild_id)-1
    target_after,ratio=_reconstructed_apex_reference_field(a1,sub,cfg)
    source_before=rp[source_i]
    target_before=rp[target_i]
    transferred=np.maximum(target_after-target_before,0.0)
    source_after=source_before-transferred
    # Sum the combined cellwise budget in the same order before/after. Since
    # each cell receives exactly the amount removed from the source tier, the
    # arrays are bitwise equal and the conservation error is exactly 0.0.
    before=float((source_before+target_before).sum())
    after=float((source_after+target_after).sum())
    return {
        "ratio":float(ratio),
        "target_after_field":target_after,
        "source_after_field":source_after,
        "source_capacity_before":float(source_before.sum()),
        "source_capacity_after":float(source_after.sum()),
        "target_capacity_before":float(target_before.sum()),
        "target_capacity_after":float(target_after.sum()),
        "capacity_transferred_source_to_target":float(transferred.sum()),
        "combined_predator_capacity_before":before,
        "combined_predator_capacity_after":after,
        "combined_predator_capacity_conservation_error":float(after-before),
    }


def _functionalize_substrate_if_reoccupied(sub, a1, current_species, registry, cfg):
    if not (cfg.functional_guild_transition_enabled and cfg.functional_guild_apex_capacity_reconstruction_enabled):
        return sub
    active=False
    for sid in set(current_species):
        row=registry.get(sid,{})
        if bool(row.get("functional_apex_reoccupation_lineage",False)) and int(row.get("guild_id",-1))==int(cfg.functional_guild_apex_target_guild_id):
            active=True;break
    if not active:return sub
    acc=_apex_capacity_transfer_accounting(a1,sub,cfg)
    source_i=int(cfg.functional_guild_apex_source_guild_id)-1
    target_i=int(cfg.functional_guild_apex_target_guild_id)-1
    out=dict(sub); rp=np.asarray(sub["reference_population"],dtype=float).copy()
    rp[source_i]=acc["source_after_field"]; rp[target_i]=acc["target_after_field"]; out["reference_population"]=rp
    out["functional_apex_capacity_reconstruction_active"]=True
    out["functional_apex_to_herbivore_capacity_ratio"]=acc["ratio"]
    out["functional_apex_capacity_accounting_semantics"]="CONSERVATIVE_PRE_CHA1_LOWER_ENVELOPE_PLUS_CELLWISE_GUILD5_TO_GUILD6_CAPACITY_TRANSFER"
    out["functional_apex_capacity_transferred_source_to_target"]=acc["capacity_transferred_source_to_target"]
    out["functional_apex_combined_predator_capacity_conservation_error"]=acc["combined_predator_capacity_conservation_error"]
    return out


def _species_profile(sid,pop,trait,resource_trait,current_species,deme_guild,cfg):
    idx=np.asarray([i for i,x in enumerate(current_species) if x==sid],dtype=np.int32)
    if not len(idx):raise KeyError(sid)
    w=pop[idx].sum(axis=(1,2)); n=float(w.sum())
    if n>0:
        body=float(np.average(trait[idx,2],weights=w)); rz=np.average(resource_trait[idx],axis=0,weights=w).astype(float)
    else:
        body=float(np.mean(trait[idx,2])); rz=np.mean(resource_trait[idx],axis=0).astype(float)
    return {"species_id":sid,"indices":idx,"guild_id":int(deme_guild[idx[0]]),"population":n,"occupied_cells":_occupied_cells(pop,idx,cfg.occupancy_floor),"relative_log_body_mass":body,"resource_trait":rz}


def _inherit_functional_flags_after_births(registry,births):
    for e in births:
        p=registry[e["parent_species_id"]]; c=registry[e["daughter_species_id"]]
        if p.get("functional_apex_reoccupation_lineage"):
            c["functional_apex_reoccupation_lineage"]=True
            c["functional_apex_capacity_semantics"]=p.get("functional_apex_capacity_semantics","PRE_CHA1_TROPHIC_CAPACITY_RECONSTRUCTION")
            c.setdefault("ancestral_guild_id",int(p.get("ancestral_guild_id",p.get("guild_id",6))))
        # Preserve trophic functional ancestry without forcing the daughter's
        # present role.  A later animal->plant return can therefore recover the
        # most recent plant functional guild rather than choosing arbitrarily.
        if p.get("cross_trophic_origin_plant_guild_id") is not None:
            c["cross_trophic_origin_plant_guild_id"]=int(p["cross_trophic_origin_plant_guild_id"])
        if p.get("cross_trophic_functional_reassignment_lineage"):
            c["cross_trophic_functional_reassignment_lineage"]=True


def _maybe_reassign_birth_functional_guild(*, births,pop,trait,resource_trait,current_species,deme_guild,root_idx,root_species_ids,generation_time,metadata,registry,a1,sub,relative_year,cfg):
    if not (cfg.functional_guild_transition_enabled and cfg.functional_guild_transition_at_speciation_only and cfg.functional_guild_apex_reoccupation_enabled and births):
        return []
    source=int(cfg.functional_guild_apex_source_guild_id); target=int(cfg.functional_guild_apex_target_guild_id)
    target_present=any(int(deme_guild[i])==target for i in range(len(deme_guild)))
    if cfg.functional_guild_apex_requires_vacancy and target_present:
        return []
    predator_ids=sorted({sid for sid,g in zip(current_species,deme_guild) if int(g) in (source,target)})
    profiles={sid:_species_profile(sid,pop,trait,resource_trait,current_species,deme_guild,cfg) for sid in predator_ids}
    body_rank=_rank01({sid:p["relative_log_body_mass"] for sid,p in profiles.items()})
    center=_apex_resource_centroid(metadata); sigma=max(float(cfg.functional_guild_apex_resource_sigma),1e-12)
    cap_acc=_apex_capacity_transfer_accounting(a1,sub,cfg); cap_field=cap_acc["target_after_field"]; cap_ratio=cap_acc["ratio"]; target_capacity=float(cap_acc["target_capacity_after"])
    candidates=[]
    for e in births:
        if e.get("cross_trophic_functional_reassignment_event"):
            continue
        child=e["daughter_species_id"]; parent=e["parent_species_id"]
        if child not in profiles:continue
        if int(profiles[child]["guild_id"])!=source:continue
        p=profiles[child]; root_sid=root_species_ids[int(root_idx[int(p["indices"][0])])]
        gt=float(np.average(generation_time[p["indices"]],weights=np.maximum(pop[p["indices"]].sum(axis=(1,2)),1e-15)))
        founder_min=da._founder_life_history_min_population(root_sid,gt,metadata,cfg)
        d=float(np.linalg.norm((p["resource_trait"]-center)/max(float(cfg.resource_niche_scale),1e-12)))
        affinity=float(math.exp(-0.5*(d/sigma)**2))
        founder_gate=bool(e.get("founder_viability",{}).get("gate_ready",False))
        checks={
            "target_guild_vacant":bool(not target_present or not cfg.functional_guild_apex_requires_vacancy),
            "parent_is_source_guild":int(registry[parent].get("guild_id",source))==source,
            "speciation_founder_gate_ready":founder_gate,
            "predator_body_rank":body_rank.get(child,0.0)+1e-15>=float(cfg.functional_guild_apex_min_body_rank),
            "apex_resource_affinity":affinity+1e-15>=float(cfg.functional_guild_apex_min_resource_affinity),
            "target_capacity_viable":target_capacity+1e-15>=float(cfg.functional_guild_apex_min_capacity_founder_multiple)*founder_min,
        }
        score=0.5*body_rank.get(child,0.0)+0.5*affinity
        candidates.append({"birth":e,"child":child,"parent":parent,"profile":p,"founder_min":founder_min,"body_rank":body_rank.get(child,0.0),"affinity":affinity,"resource_distance":d,"target_capacity":target_capacity,"capacity_ratio":cap_ratio,"score":score,"checks":checks,"eligible":all(checks.values())})
    eligible=[x for x in candidates if x["eligible"]]
    if not eligible:return []
    eligible.sort(key=lambda x:(-float(x["score"]),str(x["child"])))
    x=eligible[0]; child=x["child"]; idx=x["profile"]["indices"]
    deme_guild[idx]=np.uint8(target)
    rr=registry[child]; rr.setdefault("ancestral_guild_id",source); rr["guild_id"]=target; rr["current_functional_guild_id"]=target; rr["functional_apex_reoccupation_lineage"]=True; rr["functional_apex_capacity_semantics"]="PRE_CHA1_MINIMUM_POSITIVE_APEX_TO_HERBIVORE_RATIO_WITH_CELLWISE_SOURCE_TO_TARGET_TRANSFER"
    ev={
        "event":"functional_guild_transition_at_speciation", "species_id":child,"parent_species_id":x["parent"],
        "relative_year":float(relative_year),
        "age_ma":float(sub.get("age_ma",66.0-relative_year/1_000_000.0)),
        "physical_age_ma":float(sub.get("age_ma",66.0-relative_year/1_000_000.0)),
        "relative_clock_age_ma":float(66.0-relative_year/1_000_000.0),
        "physical_hold_active":bool(sub.get("physical_hold_active",False)),
        "physical_time_semantics":"CONTROLLED_STATIC_PHYSICAL_HOLD_NOT_NATURAL_HISTORY_CANON" if bool(sub.get("physical_hold_active",False)) else "NATURAL_HISTORY_PHYSICAL_PROVIDER",
        "source_guild_id":source,"target_guild_id":target,"transition_type":"VACANT_APEX_ECOSPACE_REOCCUPATION_AT_TAXONOMIC_BIRTH",
        "body_rank_among_extant_predators":float(x["body_rank"]),"apex_resource_affinity":float(x["affinity"]),
        "resource_distance_to_apex_centroid_normalized":float(x["resource_distance"]),"target_apex_capacity_population_units":float(x["target_capacity"]),
        "target_capacity_to_founder_minimum":float(x["target_capacity"]/max(x["founder_min"],1e-15)),
        "pre_cha1_apex_to_herbivore_capacity_ratio":float(x["capacity_ratio"]),"functional_score":float(x["score"]),
        "capacity_accounting_semantics":"CONSERVATIVE_PRE_CHA1_LOWER_ENVELOPE_PLUS_CELLWISE_GUILD5_TO_GUILD6_CAPACITY_TRANSFER",
        "source_capacity_before":float(cap_acc["source_capacity_before"]),"source_capacity_after":float(cap_acc["source_capacity_after"]),
        "target_capacity_before":float(cap_acc["target_capacity_before"]),"target_capacity_after":float(cap_acc["target_capacity_after"]),
        "capacity_transferred_source_to_target":float(cap_acc["capacity_transferred_source_to_target"]),
        "combined_predator_capacity_before":float(cap_acc["combined_predator_capacity_before"]),
        "combined_predator_capacity_after":float(cap_acc["combined_predator_capacity_after"]),
        "combined_predator_capacity_conservation_error":float(cap_acc["combined_predator_capacity_conservation_error"]),
        "authority":"FOUNDER_PERSISTENT_SPECIATION_PLUS_STATE_DERIVED_FUNCTIONAL_ROLE_NO_AUTHOR_SELECTED_WINNER",
        "cross_trophic_transition":False,
    }
    rr.setdefault("functional_guild_transition_history",[]).append(dict(ev)); x["birth"]["functional_guild_transition_event"]=dict(ev)
    return [ev]


def _plant_guild_archetypes(metadata: dict, cfg):
    """D1 plant-guild centroids in existing quantitative phenotype space.

    This is only a fallback for an ancestrally animal lineage with no prior plant
    guild in its transition history.  It does not select a named lineage or infer
    morphology.  The target is the nearest existing plant functional archetype in
    body-mass + plant-resource phenotype space.
    """
    rows={g:[] for g in range(1,5)}
    all_body=[]
    for sid,m in metadata.items():
        g=int(m.get("guild_id",-1))
        if 1 <= g <= 4:
            body=float(m["relative_log_body_mass"])
            rz=np.asarray(da._initial_resource_pref(m),dtype=float)
            rows[g].append((body,rz))
            all_body.append(body)
    body_scale=max(float(np.std(all_body)),0.15) if all_body else 1.0
    out={}
    for g,vals in rows.items():
        if not vals:
            continue
        out[g]={
            "body":float(np.mean([x[0] for x in vals])),
            "resource":np.mean(np.stack([x[1] for x in vals]),axis=0),
        }
    return out,body_scale


def _nearest_plant_guild(profile: dict, metadata: dict, cfg) -> tuple[int,float]:
    archetypes,body_scale=_plant_guild_archetypes(metadata,cfg)
    if not archetypes:
        raise ValueError("B2.3 cannot derive a plant functional archetype from D1 metadata")
    scored=[]
    for g,a in archetypes.items():
        db=(float(profile["relative_log_body_mass"])-float(a["body"]))/body_scale
        dr=np.linalg.norm((np.asarray(profile["resource_trait"],float)-np.asarray(a["resource"],float))/max(float(cfg.resource_niche_scale),1e-12))
        d=math.sqrt(db*db+dr*dr)
        scored.append((float(d),int(g)))
    scored.sort(key=lambda x:(x[0],x[1]))
    return scored[0][1],scored[0][0]


def _weighted_species_scalar(values, indices, pop):
    idx=np.asarray(indices,dtype=int)
    vals=np.asarray(values,dtype=float)[idx]
    w=np.asarray(pop,dtype=float)[idx].sum(axis=(1,2))
    good=np.isfinite(vals)
    if not np.any(good):
        return float("nan")
    vals=vals[good]; w=w[good]
    return float(np.average(vals,weights=w)) if float(w.sum())>0 else float(np.mean(vals))


def _cross_trophic_target_capacity(target_guild, pop, deme_guild, sub):
    ref=np.asarray(sub["reference_population"],dtype=float)
    g=int(target_guild)
    base=float(ref[g-1].sum())
    if g >= 5:
        herb_total=float(sum(float(pop[i].sum()) for i in range(len(pop)) if int(deme_guild[i]) <= 4))
        ref_herb=float(ref[:4].sum())
        base*=float(np.clip(herb_total/max(ref_herb,1e-15),0.0,1.5))
    return max(base,0.0)


def _maybe_reassign_cross_trophic_births(*, births,pop,trait,resource_trait,trophic_mode,current_species,deme_guild,
                                          root_idx,root_species_ids,generation_time,metadata,registry,
                                          species_guild,sub,relative_year,cfg):
    """B2.3 speciation-bound cross-trophic functional reassignment.

    Taxonomic birth is a hard prerequisite.  The daughter must already satisfy
    the ordinary speciation/founder gate, display a dominant opposite trophic
    phenotype, *and* realize that opposite resource channel in its occupied
    distribution.  No transition probability or rate exists.
    """
    if not (bool(getattr(cfg,"functional_guild_cross_trophic_transitions_enabled",False))
            and bool(getattr(cfg,"trophic_mode_cross_guild_transition_authority_enabled",False))
            and bool(getattr(cfg,"functional_guild_transition_at_speciation_only",True))
            and births):
        return []
    if not (cfg.trophic_mode_enabled and cfg.trophic_mode_common_currency_enabled and cfg.trophic_mode_continuous_resource_routing_enabled):
        raise ValueError("B2.3 cross-trophic authority requires B2.0+B2.1+B2.2 trophic layers")
    if bool(getattr(cfg,"cross_trophic_direct_plant_to_apex_enabled",False)):
        raise ValueError("B2.3 forbids direct plant-to-apex authority")

    routing=da._trophic_routing_weight(trophic_mode,cfg)
    realized=da._realized_trophic_animal_share(
        pop,resource_trait,root_idx,root_species_ids,species_guild,sub,cfg,trophic_mode,
        current_species=current_species,current_guild=deme_guild)
    min_dom=float(cfg.cross_trophic_min_dominant_routing_share)
    min_real=float(cfg.cross_trophic_min_realized_resource_share)
    target_mult=float(cfg.cross_trophic_min_target_capacity_founder_multiple)
    events=[]

    for e in births:
        child=str(e["daughter_species_id"]); parent=str(e["parent_species_id"])
        idx=_species_indices(current_species,child)
        if len(idx)==0:
            continue
        profile=_species_profile(child,pop,trait,resource_trait,current_species,deme_guild,cfg)
        source=int(profile["guild_id"])
        mean_routing=_weighted_species_scalar(routing,idx,pop)
        mean_realized=_weighted_species_scalar(realized,idx,pop)
        if not (np.isfinite(mean_routing) and np.isfinite(mean_realized)):
            continue

        direction=None; target=None; archetype_distance=None; target_rule=None
        if source <= 4 and bool(cfg.cross_trophic_allow_plant_to_animal):
            if mean_routing + 1e-15 >= min_dom and mean_realized + 1e-15 >= min_real:
                target=int(cfg.cross_trophic_plant_to_animal_target_guild_id)
                if target == int(cfg.functional_guild_apex_target_guild_id):
                    raise ValueError("B2.3 direct plant-to-apex transition is forbidden")
                if target != int(cfg.functional_guild_apex_source_guild_id):
                    raise ValueError("B2.3 plant-to-animal target must be base predator guild 5")
                direction="PLANT_TO_ANIMAL"
                target_rule="BASE_PREDATOR_FUNCTIONAL_TIER_AFTER_PHENOTYPIC_CROSSING"
        elif source >= 5 and bool(cfg.cross_trophic_allow_animal_to_plant):
            plant_share=1.0-mean_routing; plant_realized=1.0-mean_realized
            if plant_share + 1e-15 >= min_dom and plant_realized + 1e-15 >= min_real:
                origin=registry.get(parent,{}).get("cross_trophic_origin_plant_guild_id")
                if origin is not None and 1 <= int(origin) <= 4:
                    target=int(origin); archetype_distance=0.0
                    target_rule="MOST_RECENT_ANCESTRAL_PLANT_FUNCTIONAL_GUILD"
                else:
                    target,archetype_distance=_nearest_plant_guild(profile,metadata,cfg)
                    target_rule="NEAREST_D1_PLANT_FUNCTIONAL_ARCHETYPE_IN_BODY_PLUS_RESOURCE_PHENOTYPE_SPACE"
                direction="ANIMAL_TO_PLANT"
        if direction is None:
            continue

        root_sid=root_species_ids[int(root_idx[int(idx[0])])]
        w=np.maximum(pop[idx].sum(axis=(1,2)),1e-15)
        gt=float(np.average(generation_time[idx],weights=w))
        founder_min=da._founder_life_history_min_population(root_sid,gt,metadata,cfg)
        target_capacity=_cross_trophic_target_capacity(target,pop,deme_guild,sub)
        founder_gate=bool(e.get("founder_viability",{}).get("gate_ready",False))
        parent_g=int(registry.get(parent,{}).get("guild_id",source))
        parent_opposite=bool((direction=="PLANT_TO_ANIMAL" and parent_g<=4) or (direction=="ANIMAL_TO_PLANT" and parent_g>=5))
        checks={
            "speciation_founder_gate_ready":founder_gate,
            "parent_in_source_trophic_mode":parent_opposite,
            "dominant_target_trophic_phenotype":bool(mean_routing+1e-15>=min_dom) if direction=="PLANT_TO_ANIMAL" else bool((1.0-mean_routing)+1e-15>=min_dom),
            "dominant_realized_target_resource_use":bool(mean_realized+1e-15>=min_real) if direction=="PLANT_TO_ANIMAL" else bool((1.0-mean_realized)+1e-15>=min_real),
            "target_capacity_viable":target_capacity+1e-15>=target_mult*founder_min,
            "target_is_not_direct_apex":bool(not(direction=="PLANT_TO_ANIMAL" and target==int(cfg.functional_guild_apex_target_guild_id))),
        }
        if not all(checks.values()):
            continue

        # Reassignment changes only the daughter's functional guild.  Total guild
        # reference capacity is not increased; subsequent demography reallocates
        # the already-existing target-guild opportunity among extant species.
        deme_guild[idx]=np.uint8(target)
        rr=registry[child]
        rr.setdefault("pre_cross_trophic_guild_id",source)
        rr["guild_id"]=int(target)
        rr["current_functional_guild_id"]=int(target)
        rr["cross_trophic_functional_reassignment_lineage"]=True
        if direction=="PLANT_TO_ANIMAL":
            rr["cross_trophic_origin_plant_guild_id"]=int(source)
            rr["trophic_functional_mode"]="ANIMAL"
        else:
            rr["trophic_functional_mode"]="PLANT"
            if rr.get("functional_apex_reoccupation_lineage"):
                rr["descends_from_apex_reoccupation_lineage"]=True
                rr["functional_apex_reoccupation_lineage"]=False
        ev={
            "event":"cross_trophic_functional_reassignment_at_speciation",
            "species_id":child,"parent_species_id":parent,
            "relative_year":float(relative_year),
            "age_ma":float(sub.get("age_ma",66.0-relative_year/1_000_000.0)),
            "physical_age_ma":float(sub.get("age_ma",66.0-relative_year/1_000_000.0)),
            "relative_clock_age_ma":float(66.0-relative_year/1_000_000.0),
            "physical_hold_active":bool(sub.get("physical_hold_active",False)),
            "physical_time_semantics":"CONTROLLED_STATIC_PHYSICAL_HOLD_NOT_NATURAL_HISTORY_CANON" if bool(sub.get("physical_hold_active",False)) else "NATURAL_HISTORY_PHYSICAL_PROVIDER",
            "source_guild_id":int(source),"target_guild_id":int(target),
            "transition_type":direction,
            "daughter_mean_trophic_mode":_weighted_species_scalar(trophic_mode,idx,pop),
            "daughter_mean_target_routing_share":float(mean_routing if direction=="PLANT_TO_ANIMAL" else 1.0-mean_routing),
            "daughter_mean_realized_target_resource_share":float(mean_realized if direction=="PLANT_TO_ANIMAL" else 1.0-mean_realized),
            "minimum_dominant_routing_share":min_dom,
            "minimum_realized_resource_share":min_real,
            "target_guild_selection_rule":target_rule,
            "target_plant_archetype_distance":None if archetype_distance is None else float(archetype_distance),
            "target_capacity_population_units":float(target_capacity),
            "target_capacity_to_founder_minimum":float(target_capacity/max(founder_min,1e-15)),
            "capacity_accounting_semantics":"FIXED_EXISTING_GUILD_REFERENCE_OPPORTUNITY_REALLOCATED_NO_CAPACITY_ADDITION",
            "authority":"INDEPENDENT_FOUNDER_PERSISTENT_SPECIATION_PLUS_HERITABLE_TROPHIC_PHENOTYPE_PLUS_REALIZED_RESOURCE_USE_NO_TRANSITION_RATE_NO_AUTHOR_SELECTED_WINNER",
            "cross_trophic_transition":True,
            "direct_plant_to_apex":False,
            "checks":checks,
        }
        rr.setdefault("functional_guild_transition_history",[]).append(dict(ev))
        e["cross_trophic_functional_reassignment_event"]=dict(ev)
        events.append(ev)
    return events

def _clean_auxiliary_states(vicariance_state, founder_state, extinction_state, current_species, deme_ids):
    dset = set(deme_ids); sset = set(current_species)
    vs = {k: v for k, v in vicariance_state.items() if k in dset}
    fs = {}
    for k, v in founder_state.items():
        sid = str(k).split("|", 1)[0]
        if sid in sset:
            fs[k] = v
    es = {k: v for k, v in extinction_state.items() if k in sset}
    return vs, fs, es


def run(
    root: Path,
    cfg: OrdinaryTurnoverConfig,
    initial_result: OrdinaryTurnoverResult | da.DiversificationAdequacyResult | None = None,
    *,
    allow_d33_stability_extension: bool = False,
) -> OrdinaryTurnoverResult:
    # D3.2D remains calibration-scoped to +5..+20 Myr by default. D3.3 may
    # explicitly extend the already-calibrated dynamics for a controlled
    # long-horizon stability experiment. This runtime switch changes only the
    # allowed temporal envelope; it does not alter any biological parameter.
    max_relative_year = 70_000_000.0 if allow_d33_stability_extension else 20_000_000.0
    if cfg.start_relative_year < 5_000_000.0 - 1e-9 or cfg.end_relative_year > max_relative_year + 1e-9 or cfg.end_relative_year <= cfg.start_relative_year:
        scope = "D3.3 stability extension (+5 to +70 Myr)" if allow_d33_stability_extension else "D3.2D calibration replay (+5 to +20 Myr)"
        raise ValueError(f"Replay outside allowed runtime scope: {scope}")
    data = dr._load_inputs(root, cfg)
    p = data["parent"]; root_species_ids = p["root_species_id"].tolist(); metadata = data["metadata"]; species_guild = data["baseline"]["guild_id"].astype(np.uint8)
    if initial_result is None:
        if not math.isclose(cfg.start_relative_year, 5_000_000.0, abs_tol=1e-9):
            raise ValueError("A continuation after +5 Myr requires initial_result")
        deme_ids = p["deme_id"].tolist(); current_species = p["current_species_id"].tolist(); root_idx = p["root_species_index"].astype(np.int32).copy(); deme_guild = p["guild_id"].astype(np.uint8).copy()
        lat = p["lat"].astype(float); lon = p["lon"].astype(float); pop = p["endpoint_population"].astype(float).copy(); trait = p["endpoint_trait"].astype(float).copy(); va = p["endpoint_additive_variance"].astype(float).copy(); gen = p["generation_time_proxy_years"].astype(float).copy()
        eco_ri = p["endpoint_intrinsic_RI"].astype(float).copy(); genomic_ri = np.zeros_like(eco_ri); clock = p["endpoint_isolation_clock_generations"].astype(float).copy(); resource_trait, resource_va = da.initialize_resource_state(root_idx, root_species_ids, metadata, cfg)
        if cfg.trophic_mode_enabled:
            trophic_mode, trophic_mode_va = tm.initialize_state(deme_guild, cfg)
        else:
            trophic_mode = np.full(len(deme_ids), np.nan, dtype=float); trophic_mode_va = np.zeros(len(deme_ids), dtype=float)
        trophic_mode_target = np.full(len(deme_ids), np.nan, dtype=float)
        registry = {r["species_id"]: dict(r) for r in data["parent_registry"]}
        extinction_state = {}
        inherited_extinctions = []
    else:
        if not math.isclose(float(initial_result.snapshot_relative_year[-1]), cfg.start_relative_year, abs_tol=1e-6):
            raise ValueError("Continuation start does not match initial_result endpoint")
        deme_ids = list(initial_result.deme_ids); current_species = list(initial_result.current_species_id); root_idx = initial_result.root_species_index.astype(np.int32).copy(); deme_guild = initial_result.guild_id.astype(np.uint8).copy()
        lat = initial_result.lat.astype(float).copy(); lon = initial_result.lon.astype(float).copy(); pop = initial_result.endpoint_population.astype(float).copy(); trait = initial_result.endpoint_trait.astype(float).copy(); va = initial_result.endpoint_additive_variance.astype(float).copy(); resource_trait = initial_result.endpoint_resource_trait.astype(float).copy(); resource_va = initial_result.endpoint_resource_variance.astype(float).copy(); gen = initial_result.generation_time_proxy_years.astype(float).copy()
        eco_ri = initial_result.endpoint_ecological_ri.astype(float).copy(); genomic_ri = initial_result.endpoint_genomic_ri.astype(float).copy(); clock = initial_result.endpoint_isolation_clock_generations.astype(float).copy(); registry = {r["species_id"]: dict(r) for r in initial_result.species_registry}
        inherited_tau = np.asarray(getattr(initial_result, "endpoint_trophic_mode", np.empty(0)), dtype=float)
        inherited_tau_va = np.asarray(getattr(initial_result, "endpoint_trophic_mode_variance", np.empty(0)), dtype=float)
        if cfg.trophic_mode_enabled and len(inherited_tau) == len(deme_ids) and np.all(np.isfinite(inherited_tau)):
            trophic_mode = inherited_tau.copy(); trophic_mode_va = inherited_tau_va.copy()
        elif cfg.trophic_mode_enabled:
            trophic_mode, trophic_mode_va = tm.initialize_state(deme_guild, cfg)
        else:
            trophic_mode = np.full(len(deme_ids), np.nan, dtype=float); trophic_mode_va = np.zeros(len(deme_ids), dtype=float)
        trophic_mode_target = np.asarray(getattr(initial_result, "endpoint_trophic_mode_target", np.full(len(deme_ids), np.nan)), dtype=float).copy()
        if len(trophic_mode_target) != len(deme_ids): trophic_mode_target = np.full(len(deme_ids), np.nan, dtype=float)
        extinction_state = {str(k): dict(v) for k, v in getattr(initial_result, "extinction_persistence_state", {}).items()}
    counters = da._child_counters(registry)
    # Event histories are part of the checkpointed state/provenance. They do not
    # affect dynamics, but they must survive aligned runtime segmentation so the
    # final artifact contains the same cumulative history as a monolithic replay.
    births = [] if initial_result is None else list(getattr(initial_result, "speciation_events", []))
    fissions = [] if initial_result is None else list(getattr(initial_result, "deme_fission_events", []))
    extinctions = [] if initial_result is None else list(getattr(initial_result, "extinction_events", []))
    guild_transitions = [] if initial_result is None else list(getattr(initial_result, "functional_guild_transition_events", []))
    old_gstats = {} if initial_result is None else dict(getattr(initial_result, "functional_guild_stats", {}))
    guild_stats = {
        "birth_checkpoints_with_transition_evaluation": int(old_gstats.get("birth_checkpoints_with_transition_evaluation", 0)),
        "birth_checkpoints_with_cross_trophic_evaluation": int(old_gstats.get("birth_checkpoints_with_cross_trophic_evaluation", 0)),
        "transition_event_count": int(old_gstats.get("transition_event_count", 0)),
        "cross_trophic_transition_event_count": int(old_gstats.get("cross_trophic_transition_event_count", 0)),
        "cross_trophic_direction_counts": dict(old_gstats.get("cross_trophic_direction_counts", {})),
        "cross_trophic_transition_species_ids": list(old_gstats.get("cross_trophic_transition_species_ids", [])),
        "reoccupied_target_guild_ids": list(old_gstats.get("reoccupied_target_guild_ids", [])),
        "transition_species_ids": list(old_gstats.get("transition_species_ids", [])),
    }
    old_tstats = {} if initial_result is None else dict(getattr(initial_result, "trophic_mode_stats", {}))
    trophic_stats = {
        "enabled": bool(cfg.trophic_mode_enabled),
        "integration_steps": int(old_tstats.get("integration_steps", 0)),
        "gene_flow_first_moment_max_abs": float(old_tstats.get("gene_flow_first_moment_max_abs", 0.0)),
        "gene_flow_second_moment_max_abs": float(old_tstats.get("gene_flow_second_moment_max_abs", 0.0)),
        "minimum_tau_seen": float(old_tstats.get("minimum_tau_seen", np.nan)),
        "maximum_tau_seen": float(old_tstats.get("maximum_tau_seen", np.nan)),
        "maximum_normalized_va_seen": float(old_tstats.get("maximum_normalized_va_seen", 0.0)),
        "minimum_log_opportunity_ratio_seen": float(old_tstats.get("minimum_log_opportunity_ratio_seen", np.nan)),
        "maximum_log_opportunity_ratio_seen": float(old_tstats.get("maximum_log_opportunity_ratio_seen", np.nan)),
        "maximum_abs_selection_signal_seen": float(old_tstats.get("maximum_abs_selection_signal_seen", 0.0)),
        "common_currency_semantics": "REFERENCE_EQUIVALENT_HERBIVORE_SUPPORT_NOT_PHYSICAL_JOULES" if cfg.trophic_mode_common_currency_enabled else "DISABLED",
        "guild_transition_authority_from_tau": bool(getattr(cfg,"trophic_mode_cross_guild_transition_authority_enabled",False)),
    }
    vicariance_state = {} if initial_result is None else {str(k): dict(v) for k, v in getattr(initial_result, "vicariance_persistence_state", {}).items()}
    old_vstats = {} if initial_result is None else dict(getattr(initial_result, "vicariance_calibration_stats", {}))
    vic_unique = set(old_vstats.get("unique_candidate_demes", []))
    vic_stats = {"fission_check_count": int(old_vstats.get("fission_check_count", 0)), "candidate_deme_observations": int(old_vstats.get("candidate_deme_observations", 0)), "reconnection_reset_count": int(old_vstats.get("reconnection_reset_count", 0)), "mature_candidate_observations": int(old_vstats.get("mature_candidate_observations", 0)), "max_continuous_persistence_years": float(old_vstats.get("max_continuous_persistence_years", 0.0))}
    founder_state = {} if initial_result is None else {str(k): dict(v) for k, v in getattr(initial_result, "founder_viability_state", {}).items()}
    old_fstats = {} if initial_result is None else dict(getattr(initial_result, "founder_viability_stats", {}))
    founder_stats = {"gate_checkpoint_count": int(old_fstats.get("gate_checkpoint_count", 0)), "structurally_isolated_component_observations": int(old_fstats.get("structurally_isolated_component_observations", 0)), "mature_viable_component_observations": int(old_fstats.get("mature_viable_component_observations", 0)), "legacy_5pct_failed_but_founder_passed": int(old_fstats.get("legacy_5pct_failed_but_founder_passed", 0)), "unique_candidate_keys": list(old_fstats.get("unique_candidate_keys", []))}
    founder_unique = set(founder_stats["unique_candidate_keys"])
    old_estats = {} if initial_result is None else dict(getattr(initial_result, "extinction_stats", {}))
    extinction_stats = {
        "checkpoint_count": int(old_estats.get("checkpoint_count", 0)),
        "stress_observations": int(old_estats.get("stress_observations", 0)),
        "mature_nonviability_observations": int(old_estats.get("mature_nonviability_observations", 0)),
        "recovery_reset_count": int(old_estats.get("recovery_reset_count", 0)),
        "extinction_event_count": int(old_estats.get("extinction_event_count", 0)),
        "unique_stressed_species": list(old_estats.get("unique_stressed_species", [])),
    }
    stressed_unique = set(extinction_stats["unique_stressed_species"])
    startpop = float(pop.sum()); start_rich = len(set(current_species)); start_demes = len(deme_ids)
    steps = int(round((cfg.end_relative_year - cfg.start_relative_year) / cfg.dt_years)); snap = max(1, int(round(cfg.snapshot_interval_years / cfg.dt_years))); fiss = max(1, int(round(cfg.deme_fission_check_interval_years / cfg.dt_years))); graph_every = max(1, int(round(cfg.pair_graph_refresh_interval_years / cfg.dt_years))); ext_every = max(1, int(round(cfg.ordinary_extinction_check_interval_years / cfg.dt_years)))
    snapshots = [cfg.start_relative_year]; richness = [start_rich]; totals = [startpop]; rows = []
    max_niche_distance = 0.; max_genomic_ri = 0.; max_total_ri = 0.; G = contact = None
    sub_init = da._substrate_for_cfg(data["a1"], cfg.start_relative_year, cfg)
    sub_init = _functionalize_substrate_if_reoccupied(sub_init, data["a1"], current_species, registry, cfg)
    hab_init, _, _ = da._habitats_and_resource_targets(pop, trait, resource_trait, root_idx, root_species_ids, species_guild, metadata, sub_init, cfg, trophic_mode=trophic_mode, current_species=current_species, current_guild=deme_guild)
    da._ensure_species_ecological_baselines(pop, hab_init, current_species, deme_guild, registry, sub_init, cfg)
    _ensure_extinction_baselines(pop, current_species, registry, cfg, cfg.start_relative_year)

    for step in range(1, steps + 1):
        t = cfg.start_relative_year + step * cfg.dt_years; sub = da._substrate_for_cfg(data["a1"], t, cfg)
        sub = _functionalize_substrate_if_reoccupied(sub, data["a1"], current_species, registry, cfg)
        habitat, resource_targets, permeability = da._habitats_and_resource_targets(pop, trait, resource_trait, root_idx, root_species_ids, species_guild, metadata, sub, cfg, trophic_mode=trophic_mode, current_species=current_species, current_guild=deme_guild)
        pop = da._migration_with_permeability(pop, habitat, permeability, root_idx, root_species_ids, metadata, lat, lon, sub, cfg.dt_years, cfg)
        habitat, resource_targets, permeability = da._habitats_and_resource_targets(pop, trait, resource_trait, root_idx, root_species_ids, species_guild, metadata, sub, cfg, trophic_mode=trophic_mode, current_species=current_species, current_guild=deme_guild)
        if cfg.current_species_demography_enabled:
            pop, species_opp = da._current_species_demography(pop, habitat, current_species, root_idx, root_species_ids, deme_guild, metadata, registry, sub, cfg.dt_years, cfg)
        else:
            init_total, init_opp = dr._reconstruct_d31_demography_baseline(data, cfg); pop = da.ar._demography(pop, habitat, root_idx, root_species_ids, species_guild, metadata, init_total, init_opp, sub, cfg.dt_years); species_opp = da._species_opportunity(habitat, current_species, deme_guild, sub)
        if G is None or step % graph_every == 1:
            G, contact, _ = da._pair_metrics_extended(pop, trait, resource_trait, root_idx, root_species_ids, metadata, lat, lon, permeability, cfg)
        td = da._trait_distance_extended(trait, resource_trait, root_idx, root_species_ids, metadata, cfg); total_ri = da._combined_ri(eco_ri, genomic_ri)
        targets = dd._selection_targets(pop, sub["temperature_c"], sub["aridity_index"]); trait_before = trait.copy(); selected = dd._selection_update(trait, va, targets, root_idx, root_species_ids, metadata, cfg.dt_years, cfg.dynamic_cfg())
        demetot = pop.sum(axis=(1, 2)); trait, va, _ = av.gene_flow_moment_mix(selected, va, demetot, G, total_ri, root_idx, cfg.variance_cfg()); va, _ = av.advance_nonflow_variance(va, trait_before, targets, demetot, gen, root_idx, root_species_ids, metadata, cfg.body_mass_scale, cfg.dt_years, cfg.variance_cfg())
        if cfg.resource_niche_enabled:
            rz_before = resource_trait.copy(); rz_sel = da._resource_selection_update(resource_trait, resource_va, resource_targets, root_idx, root_species_ids, metadata, cfg.dt_years, cfg); resource_trait, resource_va, _ = av.gene_flow_moment_mix(rz_sel, resource_va, demetot, G, total_ri, root_idx, cfg.variance_cfg()); resource_va = da._advance_resource_variance(resource_va, rz_before, resource_targets, demetot, gen, cfg.dt_years, cfg)
        if cfg.trophic_mode_enabled:
            tau_before = trophic_mode.copy()
            trophic_selection_state = np.full(len(trophic_mode), np.nan, dtype=float)
            if cfg.trophic_mode_environmental_selection_enabled:
                if cfg.trophic_mode_common_currency_enabled:
                    plant_support, animal_support, log_ratio, animal_share, currency_diag = tm.common_opportunity_currency(
                        pop, root_idx, root_species_ids, species_guild, sub, cfg,
                        current_species=current_species, current_guild=deme_guild
                    )
                    trophic_mode_target = animal_share  # diagnostic only; never used as a direct optimum in B2.1
                    trophic_selection_state = tm.directional_selection_signal(trophic_mode, log_ratio, cfg)
                    tau_selected = tm.selection_update(trophic_mode, trophic_mode_va, log_ratio, root_idx, root_species_ids, metadata, cfg.dt_years, cfg)
                    finite_lr = log_ratio[np.isfinite(log_ratio)]
                    if finite_lr.size:
                        lmn=float(np.min(finite_lr)); lmx=float(np.max(finite_lr))
                        trophic_stats["minimum_log_opportunity_ratio_seen"] = lmn if not np.isfinite(trophic_stats["minimum_log_opportunity_ratio_seen"]) else min(trophic_stats["minimum_log_opportunity_ratio_seen"], lmn)
                        trophic_stats["maximum_log_opportunity_ratio_seen"] = lmx if not np.isfinite(trophic_stats["maximum_log_opportunity_ratio_seen"]) else max(trophic_stats["maximum_log_opportunity_ratio_seen"], lmx)
                    finite_sig = trophic_selection_state[np.isfinite(trophic_selection_state)]
                    if finite_sig.size:
                        trophic_stats["maximum_abs_selection_signal_seen"] = max(trophic_stats["maximum_abs_selection_signal_seen"], float(np.max(np.abs(finite_sig))))
                    trophic_stats["last_currency_diagnostics"] = currency_diag
                else:
                    trophic_mode_target = tm.opportunity_targets(pop, root_idx, root_species_ids, species_guild, sub, cfg)
                    tau_selected = tm.selection_update(trophic_mode, trophic_mode_va, trophic_mode_target, root_idx, root_species_ids, metadata, cfg.dt_years, cfg)
                    trophic_selection_state = trophic_mode_target
            else:
                trophic_mode_target = np.full(len(trophic_mode), np.nan, dtype=float)
                tau_selected = trophic_mode.copy()
            trophic_G = tm.time_scaled_gene_flow_matrix(G, total_ri, cfg.dt_years, cfg.trophic_mode_gene_flow_reference_step_years)
            tau_mix, tau_va_mix, tau_flow_diag = av.gene_flow_moment_mix(tau_selected[:, None], trophic_mode_va[:, None], demetot, trophic_G, total_ri, root_idx, cfg.variance_cfg())
            trophic_mode = np.clip(tau_mix[:, 0], 0.0, 1.0)
            trophic_mode_va = tm.advance_variance(tau_va_mix[:, 0], tau_before, trophic_selection_state, demetot, gen, cfg.dt_years, cfg)
            trophic_stats["integration_steps"] += 1
            trophic_stats["gene_flow_first_moment_max_abs"] = max(trophic_stats["gene_flow_first_moment_max_abs"], abs(float(tau_flow_diag["first_moment_conservation_max_abs"])))
            trophic_stats["gene_flow_second_moment_max_abs"] = max(trophic_stats["gene_flow_second_moment_max_abs"], abs(float(tau_flow_diag["second_moment_conservation_max_abs"])))
            finite_tau = trophic_mode[np.isfinite(trophic_mode)]
            if finite_tau.size:
                mn=float(np.min(finite_tau)); mx=float(np.max(finite_tau))
                trophic_stats["minimum_tau_seen"] = mn if not np.isfinite(trophic_stats["minimum_tau_seen"]) else min(trophic_stats["minimum_tau_seen"], mn)
                trophic_stats["maximum_tau_seen"] = mx if not np.isfinite(trophic_stats["maximum_tau_seen"]) else max(trophic_stats["maximum_tau_seen"], mx)
                trophic_stats["maximum_normalized_va_seen"] = max(trophic_stats["maximum_normalized_va_seen"], float(np.max(trophic_mode_va / max(cfg.trophic_mode_scale**2,1e-30))))
        td = da._trait_distance_extended(trait, resource_trait, root_idx, root_species_ids, metadata, cfg); eco_ri, genomic_ri, clock = da._advance_pair_channels(eco_ri, genomic_ri, clock, contact, td, gen, root_idx, cfg.dt_years, cfg); total_ri = da._combined_ri(eco_ri, genomic_ri)

        if step % fiss == 0:
            effective_connectivity = da._effective_barrier_connectivity(habitat, permeability, cfg)
            before_vicariance = {str(k): dict(v) for k, v in vicariance_state.items()}
            vicariance_state, mature = da._update_vicariance_persistence(deme_ids, root_idx, pop, effective_connectivity, t, vicariance_state, cfg)
            vic_stats["fission_check_count"] += 1; vic_stats["candidate_deme_observations"] += len(vicariance_state); vic_stats["reconnection_reset_count"] += len(set(before_vicariance) - set(vicariance_state)); vic_stats["mature_candidate_observations"] += len(mature); vic_unique.update(vicariance_state)
            if vicariance_state:
                vic_stats["max_continuous_persistence_years"] = max(vic_stats["max_continuous_persistence_years"], max(float(v.get("continuous_persistence_years", 0.0)) for v in vicariance_state.values()))
            if cfg.transient_vicariance_fission_enabled and mature:
                mature_ids = set(mature)
                pre_fission_trophic = {str(did): (float(trophic_mode[i]), float(trophic_mode_va[i]), float(trophic_mode_target[i])) for i,did in enumerate(deme_ids)}
                (deme_ids, root_idx, deme_guild, current_species, pop, trait, va, resource_trait, resource_va, gen, eco_ri, genomic_ri, clock, newf) = da._fission_with_connectivity(deme_ids, root_idx, deme_guild, current_species, pop, trait, va, resource_trait, resource_va, gen, eco_ri, genomic_ri, clock, t, lat, lon, effective_connectivity, cfg, mature_ids, mature)
                if cfg.trophic_mode_enabled and newf:
                    parent_for_child = {str(e["daughter_deme_id"]): str(e["parent_deme_id"]) for e in newf}
                    vals=[]
                    for did in deme_ids:
                        key=str(did); src=key if key in pre_fission_trophic else parent_for_child[key]
                        vals.append(pre_fission_trophic[src])
                    trophic_mode=np.asarray([v[0] for v in vals],float); trophic_mode_va=np.asarray([v[1] for v in vals],float); trophic_mode_target=np.asarray([v[2] for v in vals],float)
                for e in newf:
                    e["root_species_id"] = root_species_ids[int(root_idx[deme_ids.index(e["daughter_deme_id"])])]
                if newf:
                    split_parents = {str(e["parent_deme_id"]) for e in newf}; vicariance_state = {k: v for k, v in vicariance_state.items() if k not in split_parents}
                fissions.extend(newf)
                if newf:
                    G, contact, _ = da._pair_metrics_extended(pop, trait, resource_trait, root_idx, root_species_ids, metadata, lat, lon, permeability, cfg); td = da._trait_distance_extended(trait, resource_trait, root_idx, root_species_ids, metadata, cfg); total_ri = da._combined_ri(eco_ri, genomic_ri)

        # Ordinary background extinction is evaluated at an absolute-time grid.
        # It is deliberately checked before speciation so a newly born daughter
        # cannot be created and removed at the same checkpoint.
        if cfg.background_species_extinction_enabled and step % ext_every == 0:
            extinction_stats["checkpoint_count"] += 1
            habitat, _, permeability = da._habitats_and_resource_targets(pop, trait, resource_trait, root_idx, root_species_ids, species_guild, metadata, sub, cfg, trophic_mode=trophic_mode, current_species=current_species, current_guild=deme_guild)
            species_opp = da._species_opportunity(habitat, current_species, deme_guild, sub)
            before_keys = set(extinction_state)
            extinction_state, mature_ext, extinction_rows = _update_extinction_persistence(
                pop=pop, current_species=current_species, root_idx=root_idx, root_species_ids=root_species_ids,
                generation_time=gen, metadata=metadata, registry=registry, opportunity=species_opp,
                relative_year=t, state=extinction_state, cfg=cfg)
            stress_rows = [r for r in extinction_rows if r.get("stress_predicate")]
            extinction_stats["stress_observations"] += len(stress_rows); extinction_stats["mature_nonviability_observations"] += len(mature_ext); stressed_unique.update(r["species_id"] for r in stress_rows)
            extinction_stats["recovery_reset_count"] += len(before_keys - set(extinction_state))
            if mature_ext:
                (deme_ids, current_species, root_idx, deme_guild, pop, trait, va, resource_trait, resource_va, gen, eco_ri, genomic_ri, clock, newe, keep) = _remove_extinct_species(
                    extinct_rows=mature_ext, deme_ids=deme_ids, current_species=current_species, root_idx=root_idx,
                    deme_guild=deme_guild, pop=pop, trait=trait, va=va, resource_trait=resource_trait,
                    resource_va=resource_va, generation_time=gen, ecological_ri=eco_ri, genomic_ri=genomic_ri,
                    clock=clock, registry=registry, relative_year=t, cfg=cfg)
                if cfg.trophic_mode_enabled:
                    trophic_mode = trophic_mode[keep]; trophic_mode_va = trophic_mode_va[keep]; trophic_mode_target = trophic_mode_target[keep]
                extinctions.extend(newe); extinction_stats["extinction_event_count"] += len(newe)
                for e in newe:
                    extinction_state.pop(e["species_id"], None)
                vicariance_state, founder_state, extinction_state = _clean_auxiliary_states(vicariance_state, founder_state, extinction_state, current_species, deme_ids)
                # All deme-indexed graph state must be regenerated after atomic removal.
                habitat, resource_targets, permeability = da._habitats_and_resource_targets(pop, trait, resource_trait, root_idx, root_species_ids, species_guild, metadata, sub, cfg, trophic_mode=trophic_mode, current_species=current_species, current_guild=deme_guild)
                G, contact, _ = da._pair_metrics_extended(pop, trait, resource_trait, root_idx, root_species_ids, metadata, lat, lon, permeability, cfg); td = da._trait_distance_extended(trait, resource_trait, root_idx, root_species_ids, metadata, cfg); total_ri = da._combined_ri(eco_ri, genomic_ri)

        if cfg.speciation_enabled and step % snap == 0:
            founder_stats["gate_checkpoint_count"] += 1
            if cfg.founder_viability_enabled:
                newb, founder_state, founder_rows = da._maybe_speciate_founder(current_species, root_idx, root_species_ids, deme_ids, pop, trait, va, resource_va, gen, metadata, contact, td, total_ri, clock, registry, counters, t, founder_state, cfg)
                founder_stats["structurally_isolated_component_observations"] += len(founder_rows)
                for rr in founder_rows:
                    founder_unique.add(rr["key"])
                    if rr["founder_viability"]["gate_ready"]:
                        founder_stats["mature_viable_component_observations"] += 1
                        if rr["legacy_branch_fraction"] < 0.05:
                            founder_stats["legacy_5pct_failed_but_founder_passed"] += 1
            else:
                newb = da.ar._maybe_speciate(current_species, root_idx, root_species_ids, deme_ids, pop, contact, td, total_ri, clock, registry, counters, t); founder_rows = []
            _inherit_functional_flags_after_births(registry, newb)
            # Record inherited quantitative state before any functional role is
            # reassigned.  The taxonomic birth remains independently authorized.
            if cfg.trophic_mode_enabled and newb:
                for ev in newb:
                    idx=np.asarray([i for i,x in enumerate(current_species) if x==ev["daughter_species_id"]],dtype=int)
                    w=pop[idx].sum(axis=(1,2)) if len(idx) else np.asarray([],float)
                    if len(idx):
                        if float(w.sum())>0:
                            mean_tau=float(np.average(trophic_mode[idx],weights=w)); mean_va=float(np.average(trophic_mode_va[idx],weights=w))
                        else:
                            mean_tau=float(np.mean(trophic_mode[idx])); mean_va=float(np.mean(trophic_mode_va[idx]))
                        ev["daughter_trophic_mode_at_birth"]=mean_tau; ev["daughter_trophic_mode_variance_at_birth"]=mean_va
                        ev["trophic_mode_birth_semantics"]="INHERITED_DEME_QUANTITATIVE_STATE_TAXONOMIC_BIRTH_PRECEDES_FUNCTIONAL_REASSIGNMENT"
                        registry[ev["daughter_species_id"]]["trophic_mode_at_birth"]=mean_tau
                        registry[ev["daughter_species_id"]]["trophic_mode_variance_at_birth"]=mean_va

            crossg=[]
            if newb and bool(getattr(cfg,"trophic_mode_cross_guild_transition_authority_enabled",False)):
                guild_stats["birth_checkpoints_with_cross_trophic_evaluation"] += 1
                crossg=_maybe_reassign_cross_trophic_births(
                    births=newb,pop=pop,trait=trait,resource_trait=resource_trait,trophic_mode=trophic_mode,
                    current_species=current_species,deme_guild=deme_guild,root_idx=root_idx,root_species_ids=root_species_ids,
                    generation_time=gen,metadata=metadata,registry=registry,species_guild=species_guild,sub=sub,
                    relative_year=t,cfg=cfg)
                if crossg:
                    guild_transitions.extend(crossg); guild_stats["transition_event_count"] += len(crossg)
                    guild_stats["cross_trophic_transition_event_count"] += len(crossg)
                    guild_stats["cross_trophic_transition_species_ids"] = sorted(set(guild_stats["cross_trophic_transition_species_ids"]) | {str(e["species_id"]) for e in crossg})
                    for e in crossg:
                        d=str(e["transition_type"]); guild_stats["cross_trophic_direction_counts"][d]=int(guild_stats["cross_trophic_direction_counts"].get(d,0))+1
                    guild_stats["reoccupied_target_guild_ids"] = sorted(set(guild_stats["reoccupied_target_guild_ids"]) | {int(e["target_guild_id"]) for e in crossg})
                    guild_stats["transition_species_ids"] = sorted(set(guild_stats["transition_species_ids"]) | {str(e["species_id"]) for e in crossg})

            # B1 apex authority is evaluated after B2.3, but explicitly skips a
            # daughter that crossed trophic mode at this same birth.  Therefore a
            # plant lineage can only reach guild 6 after a later independent
            # speciation event: direct plant->apex remains impossible.
            if cfg.functional_guild_transition_enabled and newb:
                guild_stats["birth_checkpoints_with_transition_evaluation"] += 1
                newg = _maybe_reassign_birth_functional_guild(
                    births=newb, pop=pop, trait=trait, resource_trait=resource_trait, current_species=current_species,
                    deme_guild=deme_guild, root_idx=root_idx, root_species_ids=root_species_ids, generation_time=gen,
                    metadata=metadata, registry=registry, a1=data["a1"], sub=sub, relative_year=t, cfg=cfg)
                if newg:
                    guild_transitions.extend(newg); guild_stats["transition_event_count"] += len(newg)
                    guild_stats["reoccupied_target_guild_ids"] = sorted(set(guild_stats["reoccupied_target_guild_ids"]) | {int(e["target_guild_id"]) for e in newg})
                    guild_stats["transition_species_ids"] = sorted(set(guild_stats["transition_species_ids"]) | {str(e["species_id"]) for e in newg})
                    sub = _functionalize_substrate_if_reoccupied(sub, data["a1"], current_species, registry, cfg)
            da._split_ecological_baseline_after_births(registry, newb, habitat, current_species, deme_guild, sub, cfg)
            _reset_extinction_baselines_after_births(registry, newb, pop, current_species, cfg, t)
            births.extend(newb)

        if step % snap == 0 or step == steps:
            snapshots.append(t); richness.append(len(set(current_species))); totals.append(float(pop.sum()))
            mask = np.triu(root_idx[:, None] == root_idx[None, :], 1)
            if np.any(mask):
                max_niche_distance = max(max_niche_distance, float(np.max(td[mask]))); max_genomic_ri = max(max_genomic_ri, float(np.max(genomic_ri[mask]))); max_total_ri = max(max_total_ri, float(np.max(total_ri[mask])))
            rows.append({"relative_year": float(t), "age_ma": float(sub["age_ma"]), "species_richness": len(set(current_species)), "deme_count": len(deme_ids), "total_population": float(pop.sum()), "speciation_events_cumulative": len(births), "extinction_events_cumulative": len(extinctions), "fission_events_cumulative": len(fissions), "functional_guild_transition_events_cumulative": len(guild_transitions), "max_trait_distance": float(np.max(td[mask])) if np.any(mask) else 0., "max_genomic_RI": float(np.max(genomic_ri[mask])) if np.any(mask) else 0., "max_total_RI": float(np.max(total_ri[mask])) if np.any(mask) else 0.})

    G, contact, td = da._pair_metrics_extended(pop, trait, resource_trait, root_idx, root_species_ids, metadata, lat, lon, permeability, cfg); total_ri = da._combined_ri(eco_ri, genomic_ri)
    final_species = sorted(set(current_species)); diversified = defaultdict(int)
    for sid in final_species:
        diversified[registry[sid]["root_species_id"]] += 1
    extinction_stats["unique_stressed_species"] = sorted(stressed_unique)
    d33b_active = bool(cfg.functional_guild_transition_enabled)
    if bool(getattr(cfg,"trophic_mode_cross_guild_transition_authority_enabled",False)):
        layer_status = "PASS_D3_3B2_3_SPECIATION_BOUND_CROSS_TROPHIC_FUNCTIONAL_REASSIGNMENT_CALIBRATION_CANDIDATE"
        layer_version = "v0.6.3D3.3B2.3"
        layer_parent = "v0.6.3D3.3B2.2"
    elif cfg.trophic_mode_enabled and cfg.trophic_mode_common_currency_enabled and cfg.trophic_mode_continuous_resource_routing_enabled:
        layer_status = "PASS_D3_3B2_2_CONTINUOUS_TROPHIC_RESOURCE_ROUTING_PHENOTYPE_ECOLOGY_COUPLING_CALIBRATION_CANDIDATE"
        layer_version = "v0.6.3D3.3B2.2"
        layer_parent = "v0.6.3D3.3B2.1"
    elif cfg.trophic_mode_enabled and cfg.trophic_mode_common_currency_enabled:
        layer_status = "PASS_D3_3B2_1_COMMON_TROPHIC_OPPORTUNITY_DIRECTIONAL_SELECTION_CALIBRATION_CANDIDATE"
        layer_version = "v0.6.3D3.3B2.1"
        layer_parent = "v0.6.3D3.3B2.0"
    elif cfg.trophic_mode_enabled:
        layer_status = "PASS_D3_3B2_0_HERITABLE_TROPHIC_MODE_QUANTITATIVE_GENETICS_CANDIDATE"
        layer_version = "v0.6.3D3.3B2.0"
        layer_parent = "v0.6.3D3.3B1"
    elif d33b_active:
        layer_status = "PASS_FUNCTIONAL_GUILD_TRANSITION_ECOSPACE_REOCCUPATION_CALIBRATION_CANDIDATE"
        layer_version = "v0.6.3D3.3B1"
        layer_parent = "v0.6.3D3.3A"
    else:
        layer_status = STATUS
        layer_version = "v0.6.3D3.2D"
        layer_parent = "v0.6.3D3.2C"
    diag = {
        "status": layer_status,
        "version": layer_version,
        "parent": layer_parent,
        "config": asdict(cfg), "segment_start_relative_year": float(cfg.start_relative_year), "segment_end_relative_year": float(cfg.end_relative_year),
        "initial_species_richness": start_rich, "final_species_richness": len(final_species),
        "new_speciation_event_count": len(births), "new_background_extinction_event_count": len(extinctions),
        "functional_guild_transition_event_count": len(guild_transitions), "functional_guild_stats": guild_stats,
        "functional_guild_transition_authority": "TAXONOMIC_BIRTH_PLUS_FOUNDER_PERSISTENCE_PLUS_STATE_DERIVED_FUNCTIONAL_ROLE_NO_TRANSITION_RATE_NO_AUTHOR_SELECTED_WINNER" if cfg.functional_guild_transition_enabled else "DISABLED",
        "initial_deme_count": start_demes, "final_deme_count": len(deme_ids), "new_deme_fission_event_count": len(fissions),
        "initial_total_population": startpop, "final_total_population": float(pop.sum()),
        "background_extinction_authority": "PERSISTENT_DETERMINISTIC_NONVIABILITY_GATE_NO_GLOBAL_RANDOM_RATE",
        "ordinary_extinction_stats": extinction_stats,
        "extinct_species_ids": [e["species_id"] for e in extinctions],
        "resource_niche_axes": 2, "genomic_isolation_channel": "STATEFUL_NON_ECOLOGICAL_INCOMPATIBILITY_CHANNEL",
        "trophic_mode_enabled": bool(cfg.trophic_mode_enabled),
        "trophic_mode_semantics": ("BOUNDED_HERITABLE_PLANT_TO_ANIMAL_RESOURCE_ACQUISITION_PROPENSITY_WITH_SPECIATION_BOUND_FUNCTIONAL_AUTHORITY" if bool(getattr(cfg,"trophic_mode_cross_guild_transition_authority_enabled",False)) else "BOUNDED_HERITABLE_PLANT_TO_ANIMAL_RESOURCE_ACQUISITION_PROPENSITY_NO_GUILD_AUTHORITY") if cfg.trophic_mode_enabled else "DISABLED",
        "trophic_mode_mutation_mean_shift": False,
        "trophic_mode_environmental_selection_enabled": bool(cfg.trophic_mode_environmental_selection_enabled),
        "trophic_mode_common_currency_enabled": bool(cfg.trophic_mode_common_currency_enabled),
        "trophic_mode_common_currency_semantics": "CURRENT_FORAGE_CONVERTED_TO_CONTEMPORANEOUS_REFERENCE_HERBIVORE_SUPPORT_VS_REALIZED_HERBIVORE_PREY_SUPPORT_NOT_PHYSICAL_JOULES_NOT_K" if cfg.trophic_mode_common_currency_enabled else "DISABLED",
        "trophic_mode_environmental_selection_status": "COMMON_CURRENCY_PLUS_SPECIALIZATION_BARRIER_DIRECTIONAL_SELECTION_ENABLED" if cfg.trophic_mode_environmental_selection_enabled and cfg.trophic_mode_common_currency_enabled else ("PENDING_COMMON_CROSS_TROPHIC_ENERGY_OPPORTUNITY_CURRENCY" if cfg.trophic_mode_enabled and not cfg.trophic_mode_environmental_selection_enabled else ("LEGACY_DIAGNOSTIC_TARGET_ENABLED" if cfg.trophic_mode_environmental_selection_enabled else "DISABLED")),
        "trophic_mode_direct_A_over_A_plus_P_target_authority": False,
        "trophic_mode_cross_guild_transition_authority": bool(getattr(cfg,"trophic_mode_cross_guild_transition_authority_enabled",False)),
        "trophic_mode_cross_guild_transition_semantics": "ONLY_AT_INDEPENDENTLY_AUTHORIZED_SPECIATION_BIRTH_REQUIRES_DOMINANT_PHENOTYPE_PLUS_REALIZED_RESOURCE_USE_NO_RATE" if bool(getattr(cfg,"trophic_mode_cross_guild_transition_authority_enabled",False)) else "DISABLED",
        "trophic_mode_current_functional_prey_field_enabled": bool(getattr(cfg,"trophic_mode_current_functional_prey_field_enabled",False)),
        "trophic_mode_same_species_prey_excluded": bool(getattr(cfg,"trophic_mode_exclude_same_species_from_prey_opportunity",False)),
        "direct_plant_to_apex_transition_authority": bool(getattr(cfg,"cross_trophic_direct_plant_to_apex_enabled",False)),
        "trophic_mode_continuous_resource_routing_enabled": bool(cfg.trophic_mode_continuous_resource_routing_enabled),
        "trophic_mode_resource_routing_semantics": "TAU_CONVEX_BLEND_OF_CALIBRATED_PLANT_AND_PREY_SPATIAL_SUITABILITY_COMMON_CURRENCY_CONTROLS_DIRECTION_NOT_HABITAT_SCALE" if cfg.trophic_mode_continuous_resource_routing_enabled else "LEGACY_GUILD_SELECTED_CHANNEL",
        "trophic_mode_stats": trophic_stats,
        "demography_authority": "CURRENT_EXTANT_SPECIES_WITH_CAPACITY_RELEASE_AFTER_EXTINCTION",
        "founder_viability_authority": "LIFE_HISTORY_PERSISTENCE_EFFECTIVE_SIZE_GENETIC_VARIANCE_SPATIAL_SUPPORT",
        "paleogeographic_history_authority": "D3.2C_ENDPOINT_AND_AREA_CONSTRAINED_EVENT_RECONSTRUCTION",
        "diversified_root_lineages": {k: v for k, v in diversified.items() if v > 1},
        "snapshot_rows": rows,
        "species_fusion_enabled": False, "Deep_adaptation_enabled": False, "dragon_lineage_selection_enabled": False,
        "sapience_enabled": False, "civilization_enabled": False, "author_selected_winner_enabled": False,
        "global_speciation_rate": None, "global_radiation_boost": False, "global_extinction_rate": None,
        "interpretation": "D3.3B2.3 allows cross-trophic functional reassignment only for an independently born viable daughter whose heritable trophic phenotype and realized resource use already support the opposite trophic mode. No guild-transition rate, named winner, or direct plant-to-apex shortcut exists."
    }
    base_result = OrdinaryTurnoverResult(
        root_species_ids, final_species, deme_ids, list(current_species), root_idx, deme_guild, lat, lon,
        np.asarray(snapshots), np.asarray(richness, np.int32), np.asarray(totals), pop, trait, va, resource_trait, resource_va, gen,
        eco_ri, genomic_ri, total_ri, clock, contact, td, [registry[k] for k in sorted(registry)], births, fissions,
        {str(k): dict(v) for k, v in vicariance_state.items()}, {**vic_stats, "unique_candidate_demes": sorted(vic_unique)},
        {str(k): dict(v) for k, v in founder_state.items()}, {**founder_stats, "unique_candidate_keys": sorted(founder_unique)}, diag,
        extinctions, {str(k): dict(v) for k, v in extinction_state.items()}, extinction_stats,
        guild_transitions, guild_stats,
        trophic_mode, trophic_mode_va, trophic_mode_target, trophic_stats,
    )
    return base_result


def write_outputs(root: Path, result: OrdinaryTurnoverResult):
    out = Path(root) / "outputs/hybrid1/ordinary_turnover_v0_6_3D3_2D"; out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "ordinary_turnover_state.npz",
        root_species_id=np.asarray(result.root_species_ids), final_species_id=np.asarray(result.final_species_ids),
        deme_id=np.asarray(result.deme_ids), current_species_id=np.asarray(result.current_species_id),
        root_species_index=result.root_species_index, guild_id=result.guild_id, lat=result.lat.astype(np.float32), lon=result.lon.astype(np.float32),
        snapshot_relative_year=result.snapshot_relative_year, species_richness_history=result.species_richness_history,
        total_population_history=result.total_population_history, endpoint_population=result.endpoint_population,
        endpoint_trait=result.endpoint_trait, endpoint_additive_variance=result.endpoint_additive_variance,
        endpoint_resource_trait=result.endpoint_resource_trait, endpoint_resource_variance=result.endpoint_resource_variance,
        generation_time_proxy_years=result.generation_time_proxy_years, endpoint_ecological_RI=result.endpoint_ecological_ri,
        endpoint_genomic_RI=result.endpoint_genomic_ri, endpoint_intrinsic_RI=result.endpoint_intrinsic_RI,
        endpoint_isolation_clock_generations=result.endpoint_isolation_clock_generations,
        endpoint_contact_connectivity=result.endpoint_contact_connectivity, endpoint_trait_distance=result.endpoint_trait_distance,
        endpoint_trophic_mode=result.endpoint_trophic_mode, endpoint_trophic_mode_variance=result.endpoint_trophic_mode_variance,
        endpoint_trophic_mode_target=result.endpoint_trophic_mode_target)
    (out / "ordinary_turnover_diagnostics.json").write_text(json.dumps(result.diagnostics, indent=2, sort_keys=True), encoding="utf-8")
    (out / "speciation_events_5_20myr.json").write_text(json.dumps({"events": result.speciation_events}, indent=2, sort_keys=True), encoding="utf-8")
    (out / "background_extinction_events_5_20myr.json").write_text(json.dumps({"events": result.extinction_events}, indent=2, sort_keys=True), encoding="utf-8")
    (out / "deme_fission_events_5_20myr.json").write_text(json.dumps({"events": result.deme_fission_events}, indent=2, sort_keys=True), encoding="utf-8")
    (out / "species_registry.json").write_text(json.dumps({"species": result.species_registry}, indent=2, sort_keys=True), encoding="utf-8")
    (out / "extinction_persistence_state.json").write_text(json.dumps({"timers": result.extinction_persistence_state}, indent=2, sort_keys=True), encoding="utf-8")
    (out / "ordinary_extinction_stats.json").write_text(json.dumps(result.extinction_stats, indent=2, sort_keys=True), encoding="utf-8")
    (out / "vicariance_persistence_state.json").write_text(json.dumps({"timers": result.vicariance_persistence_state}, indent=2, sort_keys=True), encoding="utf-8")
    (out / "founder_viability_state.json").write_text(json.dumps({"timers": result.founder_viability_state}, indent=2, sort_keys=True), encoding="utf-8")
    return out


def synthetic_controls(cfg: OrdinaryTurnoverConfig):
    # Direct persistence-state controls on a stylized species. These validate
    # semantics independently of the D3.2C replay.
    def episode(values, check=500_000.0):
        state={}; matured=[]
        # Synthetic rows use the same update logic after replacing metric source.
        for t, stress, n in values:
            sid="X"
            if not stress:
                state.pop(sid,None); continue
            st=state.get(sid)
            if st is None:
                st={"start_relative_year":t,"last_relative_year":t,"first_population":n,"minimum_population":n,"continuous_stress_years":0.0}
            else:
                min_seen=min(st["minimum_population"],n)
                if n>min_seen*cfg.ordinary_extinction_recovery_reset_factor:
                    st={"start_relative_year":t,"last_relative_year":t,"first_population":n,"minimum_population":n,"continuous_stress_years":0.0}
                else:
                    st["last_relative_year"]=t;st["minimum_population"]=min_seen;st["continuous_stress_years"]=t-st["start_relative_year"]
            state[sid]=st
            if st["continuous_stress_years"]+1e-9>=cfg.ordinary_extinction_minimum_persistence_years and n/max(st["first_population"],1e-15)<=cfg.ordinary_extinction_max_population_ratio_to_episode_start:
                matured.append(t)
        return matured,state
    transient=[(0,True,1.0),(500_000,True,0.8),(1_000_000,False,1.1),(1_500_000,False,1.2),(2_000_000,False,1.2)]
    persistent=[(0,True,1.0),(500_000,True,0.8),(1_000_000,True,0.7),(1_500_000,True,0.65),(2_000_000,True,0.6)]
    stable_low=[(0,True,1.0),(500_000,True,1.0),(1_000_000,True,1.0),(1_500_000,True,1.0),(2_000_000,True,1.0)]
    rebound=[(0,True,1.0),(500_000,True,0.7),(1_000_000,True,0.6),(1_500_000,True,0.9),(2_000_000,True,0.85),(2_500_000,True,0.8)]
    p1,_=episode(transient); p2,_=episode(persistent); p3,_=episode(stable_low); p4,s4=episode(rebound)
    # Resolution independence of elapsed-time maturity.
    persistent_250=[(t,True,1.0-0.4*(t/2_000_000.0)) for t in np.arange(0,2_000_000.0+1,250_000.0)]
    p5,_=episode(persistent_250,250_000.0)
    return {
        "transient_mature_times":p1,"persistent_mature_times":p2,"stable_low_mature_times":p3,"rebound_mature_times":p4,
        "persistent_250k_mature_times":p5,
        "checks":{
            "transient_stress_recovers_no_extinction":len(p1)==0,
            "persistent_decline_matures_at_2myr":bool(p2 and math.isclose(p2[0],2_000_000.0,abs_tol=1e-9)),
            "stable_low_without_decline_not_deleted":len(p3)==0,
            "material_rebound_resets_episode":len(p4)==0,
            "elapsed_time_not_frame_count":bool(p5 and math.isclose(p5[0],2_000_000.0,abs_tol=1e-9)),
        }
    }
