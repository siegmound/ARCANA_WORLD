from __future__ import annotations

from dataclasses import dataclass, asdict
from collections import defaultdict
import math
import numpy as np

import rebased_natural_control_runtime_v0_6D1_R2 as r2
import rebased_natural_control_runtime_v0_6D1_R2_1 as r21
import rebased_deep_time_barrier_provider_v0_6D1_R3 as bp
import d3_additive_variance_v0_6_3D3_3A as av
from arcana_worldsim.post_cha1 import diversification_adequacy as d3b

R3_STAGE_ID = "v0.6D1-R3.2"
R3_SCOPE = "REBASED_NATURAL_CONTROL_BARRIER_COUPLED_TRANSPORT_GENE_FLOW_AND_VARIANCE_CLOSURE"
R3_DEEP_BIOLOGICAL_COUPLING_ENABLED = False


@dataclass(frozen=True)
class R3Config(r21.R21Config):
    start_age_ma: float = 210.0
    end_age_ma: float = 180.0
    macrostep_years: float = 500_000.0
    biology_cadence_years: float = 125_000.0
    transport_cadence_years: float = 62_500.0
    dt_years: float = 125_000.0
    snapshot_interval_years: float = 1_000_000.0

    # D3.2C paleogeographic event-history authority.
    barrier_phase_min: float = 0.05
    barrier_phase_max: float = 0.95
    barrier_transition_width_years: float = 1_000_000.0
    connectivity_land_support_threshold: float = 0.25
    connectivity_softness: float = 0.10

    # D3.2B effective barrier connectivity calibration.
    habitat_connectivity_power: float = 0.50
    effective_connectivity_core_threshold: float = 0.20
    persistent_vicariance_fission_enabled: bool = True
    vicariance_persistence_min_years: float = 2_000_000.0




def _variance_cfg_d3_3a(cfg: R3Config) -> av.AdditiveVarianceConfig:
    """Exact D3.3A additive-variance/homeostasis authority reused by R3.1."""
    return av.AdditiveVarianceConfig(
        mutation_variance_supply_normalized_per_myr=cfg.mutation_variance_supply_normalized_per_myr,
        mutation_variance_ceiling_normalized=cfg.variance_ceiling_normalized,
        variance_homeostasis_enabled=True,
        mutation_supply_generation_scaled=False,
        mutation_supply_reference_generation_years=5.0,
        baseline_stabilizing_variance_depletion_per_generation=0.0,
        nonlinear_stabilizing_variance_depletion_per_myr_per_q=cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q,
        selection_variance_depletion_per_generation=cfg.selection_variance_depletion_per_generation,
        selection_pressure_ceiling=4.0,
        drift_individual_equivalents_per_population_unit=cfg.drift_individual_equivalents_per_population_unit,
        drift_min_effective_size=cfg.drift_min_effective_size,
        maximum_total_exchange_fraction_per_deme=0.45,
    )


def _root_index(root_species: list[str]) -> tuple[np.ndarray, list[str]]:
    ids = sorted(set(str(x) for x in root_species))
    pos = {sid: i for i, sid in enumerate(ids)}
    return np.asarray([pos[str(s)] for s in root_species], dtype=np.int32), ids


def _d3_barrier_transport_cfg(cfg: R3Config) -> d3b.DiversificationAdequacyConfig:
    """Reuse the SEALED D3.2B transport/contact calibration without changing constants."""
    return d3b.DiversificationAdequacyConfig(
        migration_reference_years=cfg.migration_reference_years,
        migration_fraction_ceiling=cfg.migration_fraction_ceiling,
        gene_flow_ceiling_per_step=cfg.gene_flow_ceiling_per_step,
        body_mass_scale=cfg.body_mass_scale,
        resource_niche_enabled=False,
        habitat_connectivity_power=cfg.habitat_connectivity_power,
        effective_connectivity_core_threshold=cfg.effective_connectivity_core_threshold,
        vicariance_persistence_min_years=cfg.vicariance_persistence_min_years,
        deme_fission_check_interval_years=cfg.deme_fission_check_interval_years,
        deme_fission_min_component_fraction=cfg.deme_fission_min_component_fraction,
        deme_fission_min_absolute_population=cfg.deme_fission_min_absolute_population,
        deme_fission_min_root_species_fraction=cfg.deme_fission_min_root_species_fraction,
    )

def barrier_cfg(cfg: R3Config) -> bp.BarrierHistoryConfig:
    return bp.BarrierHistoryConfig(
        phase_min=cfg.barrier_phase_min,
        phase_max=cfg.barrier_phase_max,
        transition_width_years=cfg.barrier_transition_width_years,
        accessibility_floor=cfg.occupancy_floor,
        connectivity_land_support_threshold=cfg.connectivity_land_support_threshold,
        connectivity_softness=cfg.connectivity_softness,
        habitat_connectivity_power=cfg.habitat_connectivity_power,
        effective_connectivity_core_threshold=cfg.effective_connectivity_core_threshold,
    )


def validate_r3(cfg: R3Config, a1) -> None:
    r21.validate_cadence(cfg)
    bp.validate_a1(a1)
    ages = np.asarray(a1["age_ma"], dtype=float)
    if cfg.start_age_ma > float(ages[0]) + 1e-12 or cfg.end_age_ma < float(ages[-1]) - 1e-12:
        raise ValueError("R3 interval must stay inside A1 reference ages")
    if not (0.0 <= cfg.barrier_phase_min < cfg.barrier_phase_max <= 1.0):
        raise ValueError("invalid barrier phase envelope")
    if cfg.connectivity_softness <= 0:
        raise ValueError("connectivity_softness must be >0")
    if not (0 < cfg.effective_connectivity_core_threshold < 1):
        raise ValueError("invalid effective connectivity core threshold")


def _normalize_resource_support(arr: np.ndarray, support: np.ndarray) -> np.ndarray:
    a = np.maximum(np.asarray(arr, dtype=float), 0.0) * np.asarray(support, dtype=float)
    vals = a[support > 1e-9]
    pos = vals[vals > 0]
    scale = float(np.percentile(pos, 95)) if pos.size else 1.0
    return np.clip(a / max(scale, 1e-15), 0.0, 1.0)


def _normalize_batch_support(arr: np.ndarray, support: np.ndarray) -> np.ndarray:
    a = np.asarray(arr, dtype=float)
    out = np.zeros_like(a)
    for i in range(len(a)):
        out[i] = _normalize_resource_support(a[i], support)
    return out


def habitats_r3(comp_species, guild, trait, pop, metadata, env, cfg: R3Config):
    nd = len(pop)
    support = np.asarray(env["land_support"], dtype=float)
    accessible = np.asarray(env["accessible"], dtype=bool)
    temp = np.asarray(env["temperature_c"], dtype=float)
    arid = np.asarray(env["aridity_index"], dtype=float)
    ts = np.array([max(metadata[s]["thermal_niche_sigma_c"], 1e-9) for s in comp_species])[:, None, None]
    ars = np.array([max(metadata[s]["aridity_niche_sigma"], 1e-9) for s in comp_species])[:, None, None]
    ao = (1.55 * (1 - np.clip(trait[:, 1], 0, 1)))[:, None, None]
    to = trait[:, 0, None, None]
    clim = np.exp(-0.5 * ((temp[None] - to) / ts) ** 2 - 0.5 * ((arid[None] - ao) / ars) ** 2)
    clim[:, ~accessible] = 0.0
    clim[:, accessible] = np.maximum(clim[:, accessible], cfg.habitat_floor)

    res = np.zeros_like(clim)
    rtot = _normalize_resource_support(env["total_edible_forage"], support)
    rb = _normalize_resource_support(env["browse_forage"], support)
    rl = _normalize_resource_support(env["low_forage"], support)
    guild = np.asarray(guild, int)
    res[guild == 1] = rtot
    res[guild == 2] = rb
    res[guild == 3] = rl

    ix = np.where(guild == 4)[0]
    if len(ix):
        wb = np.array([metadata[comp_species[i]].get("diet_weights", {}).get("browse", 0) for i in ix])[:, None, None]
        wl = np.array([metadata[comp_species[i]].get("diet_weights", {}).get("low", 0) for i in ix])[:, None, None]
        ww = np.array([metadata[comp_species[i]].get("diet_weights", {}).get("wetland", 0) for i in ix])[:, None, None]
        raw = wb * env["browse_forage"] + wl * env["low_forage"] + ww * env["wetland_forage"]
        res[ix] = _normalize_batch_support(raw, support)

    guildmaps = np.zeros((4,) + support.shape, dtype=float)
    for g in range(1, 5):
        guildmaps[g - 1] = pop[guild == g].sum(axis=0)
    ix = np.where(guild >= 5)[0]
    if len(ix):
        W = np.zeros((len(ix), 4), dtype=float)
        for a, i in enumerate(ix):
            for key, w in metadata[comp_species[i]].get("diet_weights", {}).items():
                pg = r2.PREY_KEY_TO_GUILD.get(key)
                if pg:
                    W[a, pg - 1] = float(w)
        raw = (W @ guildmaps.reshape(4, -1)).reshape(len(ix), *support.shape)
        res[ix] = _normalize_batch_support(raw, support)

    q = clim * np.maximum(res, cfg.habitat_floor) * np.maximum(support[None, :, :], 1e-9)
    q[:, ~accessible] = 0.0
    mx = q.reshape(nd, -1).max(axis=1)
    good = mx > 0
    q[good] /= mx[good, None, None]
    return q



def _migration_subcycled_r3(pop, root_species, guild, trait, metadata, lat, lon, env, dt, cfg: R3Config):
    """D3.2B barrier-coupled migration on the R2.1 absolute transport cadence."""
    n = int(round(dt / cfg.transport_cadence_years))
    if n < 1 or not r21._is_multiple(dt, cfg.transport_cadence_years):
        raise ValueError("biology step must contain an integer number of transport substeps")
    out = pop
    hab = None
    permeability = bp.connectivity_permeability(env["land_support"], barrier_cfg(cfg))
    for _ in range(n):
        hab = habitats_r3(root_species, guild, trait, out, metadata, env, cfg)
        root_idx, root_species_ids = _root_index(root_species)
        out = d3b._migration_with_permeability(
            out, hab, permeability, root_idx, root_species_ids, metadata, lat, lon, env,
            cfg.transport_cadence_years, _d3_barrier_transport_cfg(cfg)
        )
    hab = habitats_r3(root_species, guild, trait, out, metadata, env, cfg)
    return out, hab


def _pair_metrics_barrier_coupled(pop, trait, root_species, metadata, lat, lon, env, cfg: R3Config):
    """Use the SEALED D3.2B permeability-masked contact/gene-flow geometry."""
    root_idx, root_ids = _root_index(root_species)
    permeability = bp.connectivity_permeability(env["land_support"], barrier_cfg(cfg))
    resource_dummy = np.zeros((len(trait), 2), dtype=float)
    G, contact, td = d3b._pair_metrics_extended(
        pop, trait, resource_dummy, root_idx, root_ids, metadata, lat, lon,
        permeability, _d3_barrier_transport_cfg(cfg)
    )
    return G, contact, td


def _significant_fragments_conn(di: int, pop: np.ndarray, connectivity: np.ndarray,
                                root_species: list[str], cfg: R3Config):
    p = np.asarray(pop[di], dtype=float)
    total = float(p.sum())
    if total <= cfg.deme_fission_min_absolute_population:
        return []
    cs = np.asarray(connectivity[di] if connectivity.ndim == 3 else connectivity, dtype=float)
    core = cs >= float(cfg.effective_connectivity_core_threshold)
    lab, n = r2._components_wrap((p > cfg.occupancy_floor) & core)
    if n < 2:
        return []
    rows = []
    for k in range(1, n + 1):
        q = np.where(lab == k, p, 0.0)
        rows.append((float(q.sum()), q))
    rows.sort(key=lambda x: -x[0])
    root_total = float(pop[r21._root_component_indices(root_species, root_species[di])].sum())
    return [x for x in rows if x[0] >= cfg.deme_fission_min_absolute_population
            and x[0] / max(total, 1e-15) >= cfg.deme_fission_min_component_fraction
            and x[0] / max(root_total, 1e-15) >= cfg.deme_fission_min_root_species_fraction]


def update_vicariance_persistence_r3(component_ids, pop, connectivity, root_species,
                                      elapsed_year, state, cfg: R3Config):
    """Event-driven persistent-vicariance timer for a rebased initial state.

    D3.2B's calibrated persistence/fragment thresholds remain unchanged.  The
    only R3 adaptation is state initialization: fragmentation already present at
    the first observation of a 210 Ma component is legacy structure, not a new
    paleogeographic event.  Such a component is disarmed until it reconnects;
    thereafter a new connected->fragmented transition can start the ordinary
    D3.2B persistence clock.  Components initially connected are armed at once.
    """
    prev = {str(k): dict(v) for k, v in state.items()}
    now, mature = {}, {}
    max_gap = cfg.deme_fission_check_interval_years * 1.01
    known = set(component_ids)
    for di, did0 in enumerate(component_ids):
        did = str(did0)
        sig = _significant_fragments_conn(di, pop, connectivity, root_species, cfg)
        fragmented = len(sig) >= 2
        old = prev.get(did)
        if old is None:
            # Baseline observation: do not reinterpret pre-existing 210 Ma
            # ecological fragmentation as an event that happened after t=0.
            now[did] = {
                "armed_after_connected_state": bool(not fragmented),
                "baseline_fragmented": bool(fragmented),
                "fragmented_now": bool(fragmented),
                "first_seen_elapsed_year": None,
                "last_seen_elapsed_year": float(elapsed_year),
                "continuous_persistence_years": 0.0,
                "significant_component_count": int(len(sig)),
                "largest_component_fraction": float(sig[0][0] / max(float(pop[di].sum()),1e-15)) if fragmented else 1.0,
                "secondary_component_fraction": float(sig[1][0] / max(float(pop[di].sum()),1e-15)) if fragmented else 0.0,
            }
            continue

        armed = bool(old.get("armed_after_connected_state", False))
        if not fragmented:
            # A connected observation arms future event detection and clears any
            # incomplete fragmentation episode.
            now[did] = {
                "armed_after_connected_state": True,
                "baseline_fragmented": bool(old.get("baseline_fragmented", False)),
                "fragmented_now": False,
                "first_seen_elapsed_year": None,
                "last_seen_elapsed_year": float(elapsed_year),
                "continuous_persistence_years": 0.0,
                "significant_component_count": 1,
                "largest_component_fraction": 1.0,
                "secondary_component_fraction": 0.0,
            }
            continue

        # Still fragmented.  If this lineage has never been observed connected,
        # it remains legacy structure and cannot mature into a new fission.
        if not armed:
            row = dict(old)
            row.update({
                "fragmented_now": True,
                "last_seen_elapsed_year": float(elapsed_year),
                "continuous_persistence_years": 0.0,
                "significant_component_count": int(len(sig)),
                "largest_component_fraction": float(sig[0][0] / max(float(pop[di].sum()),1e-15)),
                "secondary_component_fraction": float(sig[1][0] / max(float(pop[di].sum()),1e-15)),
            })
            now[did] = row
            continue

        contiguous = (
            bool(old.get("fragmented_now", False))
            and float(elapsed_year) - float(old.get("last_seen_elapsed_year", elapsed_year)) <= max_gap
            and old.get("first_seen_elapsed_year") is not None
        )
        if contiguous:
            delta = max(0.0, float(elapsed_year) - float(old.get("last_seen_elapsed_year", elapsed_year)))
            first = float(old["first_seen_elapsed_year"])
            persistence = float(old.get("continuous_persistence_years", 0.0)) + delta
        else:
            first = float(elapsed_year)
            persistence = 0.0
        row = {
            "armed_after_connected_state": True,
            "baseline_fragmented": bool(old.get("baseline_fragmented", False)),
            "fragmented_now": True,
            "first_seen_elapsed_year": first,
            "last_seen_elapsed_year": float(elapsed_year),
            "continuous_persistence_years": persistence,
            "significant_component_count": int(len(sig)),
            "largest_component_fraction": float(sig[0][0] / max(float(pop[di].sum()),1e-15)),
            "secondary_component_fraction": float(sig[1][0] / max(float(pop[di].sum()),1e-15)),
        }
        now[did] = row
        if persistence + 1e-9 >= cfg.vicariance_persistence_min_years:
            mature[did] = dict(row)

    # Preserve state for known components only; removed/extinct component IDs do
    # not carry timers into unrelated future lineages.
    return {k:v for k,v in now.items() if k in known}, mature


def apply_mature_fissions_r3(*, component_ids, root_species, current_species, guild, pop, trait, va, gen,
                              connectivity, lat, lon, ri_state, clock_state, mature, persistence,
                              elapsed_year, age_ma, cfg: R3Config):
    if not mature:
        return component_ids, root_species, current_species, guild, pop, trait, va, gen, ri_state, clock_state, []
    before_ids = list(component_ids)
    before_root = list(root_species)
    counters = defaultdict(int)
    for did in component_ids:
        if "_F" in did:
            stem, _, tail = did.rpartition("_F")
            if tail.isdigit():
                counters[stem] = max(counters[stem], int(tail))
    additions = []
    for di, did in enumerate(before_ids):
        if did not in mature:
            continue
        sig = _significant_fragments_conn(di, pop, connectivity, root_species, cfg)
        if len(sig) < 2:
            continue
        retained = pop[di].copy()
        for _, q in sig[1:]:
            retained[q > 0] = 0.0
        pop[di] = retained
        for rank, (mass, q) in enumerate(sig[1:], 1):
            counters[did] += 1
            nid = f"{did}_F{counters[did]:02d}"
            additions.append((di, nid, q.copy(), float(mass), rank))
    if not additions:
        return component_ids, root_species, current_species, guild, pop, trait, va, gen, ri_state, clock_state, []
    ids = list(component_ids); roots = list(root_species); cur = list(current_species)
    gs = list(np.asarray(guild, int)); pops = [x.copy() for x in pop]; trs = [x.copy() for x in trait]
    vas = [x.copy() for x in va]; gens = list(np.asarray(gen, float)); events = []
    for parent, nid, q, mass, rank in additions:
        ids.append(nid); roots.append(root_species[parent]); cur.append(current_species[parent]); gs.append(int(guild[parent]))
        pops.append(q); trs.append(trait[parent].copy()); vas.append(va[parent].copy()); gens.append(float(gen[parent]))
        r21._clone_pair_state_after_fission(before_ids[parent], nid, before_ids, before_root, parent, ri_state, clock_state)
        cent = r2.weighted_centroid(lat, lon, q)
        pm = persistence.get(before_ids[parent], {})
        events.append({
            "event": "deme_fission", "elapsed_year": float(elapsed_year), "age_ma": float(age_ma),
            "parent_component_id": before_ids[parent], "daughter_component_id": nid,
            "species_id_at_fission": current_species[parent], "root_species_id": root_species[parent],
            "population": mass, "component_rank": rank,
            "centroid_lat_deg": float(cent[0]), "centroid_lon_deg": float(cent[1]),
            "vicariance_first_seen_elapsed_year": float(pm.get("first_seen_elapsed_year", elapsed_year)),
            "vicariance_continuous_persistence_years": float(pm.get("continuous_persistence_years", 0.0)),
            "semantic_status": "D3_2C_EVENT_HISTORY_BOUND_PERSISTENT_VICARIANCE_DEMOGRAPHIC_FRAGMENT_NOT_SPECIES",
        })
    return (ids, roots, cur, np.asarray(gs, np.uint8), np.stack(pops), np.stack(trs), np.stack(vas),
            np.asarray(gens), ri_state, clock_state, events)


def run(common, a1, metadata_rows, cfg: R3Config):
    validate_r3(cfg, a1)
    metadata = {r["species_id"]: r for r in metadata_rows}
    root_ids = [str(x) for x in common["species_id"].tolist()]
    guild0 = common["guild_id"].astype(int)
    component_ids, root_species, guild, pop = r2.partition_components(
        root_ids, common["species_population"].astype(float), guild0, cfg.occupancy_floor)
    current_species = list(root_species)
    trait, va, gen = r2.init_traits(root_species, metadata)
    registry, child_counters = r21._initialize_registry(root_ids, guild0)
    lat = common["lat"].astype(float); lon = common["lon"].astype(float)
    bcfg = barrier_cfg(cfg)
    env0 = bp.environment_at(cfg.start_age_ma, a1, bcfg)
    current_accessible = env0["accessible"].copy()
    hab = habitats_r3(root_species, guild, trait, pop, metadata, env0, cfg)
    baselines = r21._initial_baselines(pop, current_species, hab, guild, env0, cfg.occupancy_floor)
    ri_state = {}; clock_state = {}; ext_state = {}; founder_state = {}; vicariance_state = {}
    events = []; snapshots = []; founder_stats_last = []
    gene_flow_closure = {"first_moment_conservation_max_abs": 0.0, "second_moment_conservation_max_abs": 0.0}
    topology_remap_mass = 0.0
    initial_total = float(pop.sum())
    duration = (cfg.start_age_ma - cfg.end_age_ma) * 1e6
    nmacro = int(round(duration / cfg.macrostep_years))
    nbio_per_macro = int(round(cfg.macrostep_years / cfg.biology_cadence_years))
    elapsed = 0.0

    snapshots.append({"age_ma": cfg.start_age_ma, "elapsed_myr": 0.0,
                      "species_richness": len(set(current_species)), "component_count": len(component_ids),
                      "total_population": float(pop.sum()), "speciation_events_cumulative": 0,
                      "extinction_events_cumulative": 0, "fission_events_cumulative": 0,
                      "barrier_bracket": [env0["older_ma"], env0["younger_ma"]],
                      "fractional_support_cells": int(np.count_nonzero((env0["land_support"] > 1e-9) & (env0["land_support"] < 1-1e-9)))})

    for _macro in range(nmacro):
        for _ in range(nbio_per_macro):
            elapsed += cfg.biology_cadence_years
            age = cfg.start_age_ma - elapsed / 1e6
            env = bp.environment_at(age, a1, bcfg)
            if not np.array_equal(env["accessible"], current_accessible):
                pop, moved = r2.remap_to_land(pop, current_accessible, env["accessible"], lat, lon)
                topology_remap_mass += moved
                current_accessible = env["accessible"].copy()
                if moved > 0:
                    events.append({"event": "paleogeographic_support_loss_remap", "age_ma": float(age),
                                   "elapsed_year": float(elapsed), "remapped_population_mass": float(moved),
                                   "semantic_status": "D3_2C_EVENT_RECONSTRUCTED_CONSERVATIVE_SUPPORT_REMAP"})

            hab = habitats_r3(root_species, guild, trait, pop, metadata, env, cfg)
            opportunity = r21._current_opportunities(hab, current_species, guild, env)
            targets = r21._demography_targets(pop, current_species, guild, registry, baselines, opportunity, env)
            pop = r21._apply_demography(pop, current_species, registry, metadata, targets, cfg.biology_cadence_years)
            pop, hab = _migration_subcycled_r3(pop, root_species, guild, trait, metadata, lat, lon, env,
                                               cfg.biology_cadence_years, cfg)

            # D3.3A semantic ordering (reused, not re-derived):
            # 1) compute contact/gene-flow geometry on the pre-selection state;
            # 2) selection updates means;
            # 3) gene flow conservatively mixes first/second moments with the
            #    original 45% aggregate exchange cap;
            # 4) Riccati homeostasis is the final VA operator, so the hard
            #    normalized ceiling remains a true hard ceiling.
            G_pre, _, _ = _pair_metrics_barrier_coupled(pop, trait, root_species, metadata, lat, lon, env, cfg)
            target = r2.selection_targets(pop, env["temperature_c"], env["aridity_index"])
            tr_before = trait.copy()
            selected = r2.select_traits(trait, va, target, root_species, metadata, cfg.biology_cadence_years, cfg)
            totals = pop.sum(axis=(1, 2))
            ri_before, _ = r21.pair_state_matrices(component_ids, root_species, ri_state, clock_state)
            root_idx, root_ids = _root_index(root_species)
            trait, va, gene_flow_closure = av.gene_flow_moment_mix(
                selected, va, totals, G_pre, ri_before, root_idx, _variance_cfg_d3_3a(cfg)
            )
            va, _variance_components = av.advance_nonflow_variance(
                va, tr_before, target, totals, gen, root_idx, root_ids, metadata,
                cfg.body_mass_scale, cfg.biology_cadence_years, _variance_cfg_d3_3a(cfg)
            )

            G, contact, td = _pair_metrics_barrier_coupled(pop, trait, root_species, metadata, lat, lon, env, cfg)
            ri_state, clock_state, ri, clock = r21.advance_pair_states(
                component_ids, root_species, gen, contact, td, ri_state, clock_state,
                cfg.biology_cadence_years, cfg)

            if cfg.persistent_vicariance_fission_enabled and r21._is_multiple(elapsed, cfg.deme_fission_check_interval_years):
                conn = bp.effective_barrier_connectivity(hab, env["land_support"], bcfg)
                vicariance_state, mature = update_vicariance_persistence_r3(
                    component_ids, pop, conn, root_species, elapsed, vicariance_state, cfg)
                if mature:
                    (component_ids, root_species, current_species, guild, pop, trait, va, gen,
                     ri_state, clock_state, fissions) = apply_mature_fissions_r3(
                        component_ids=component_ids, root_species=root_species, current_species=current_species,
                        guild=guild, pop=pop, trait=trait, va=va, gen=gen, connectivity=conn,
                        lat=lat, lon=lon, ri_state=ri_state, clock_state=clock_state, mature=mature,
                        persistence=vicariance_state, elapsed_year=elapsed, age_ma=age, cfg=cfg)
                    if fissions:
                        events.extend(fissions)
                        for e in fissions:
                            vicariance_state.pop(e["parent_component_id"], None)
                        hab = habitats_r3(root_species, guild, trait, pop, metadata, env, cfg)
                        G, contact, td = _pair_metrics_barrier_coupled(pop, trait, root_species, metadata, lat, lon, env, cfg)
                        ri, clock = r21.pair_state_matrices(component_ids, root_species, ri_state, clock_state)

            if r21._is_multiple(elapsed, cfg.ordinary_extinction_check_interval_years):
                opportunity = r21._current_opportunities(hab, current_species, guild, env)
                mature_ext, ext_state, _ = r21.ordinary_extinction_update(
                    current_species=current_species, root_species=root_species, component_ids=component_ids,
                    pop=pop, gen=gen, metadata=metadata, registry=registry, baselines=baselines,
                    opportunity=opportunity, elapsed_year=elapsed, ext_state=ext_state, cfg=cfg)
                if mature_ext:
                    (component_ids, root_species, current_species, guild, pop, trait, va, gen,
                     ri_state, clock_state, ext_events) = r21.apply_extinctions(
                        mature_ext, component_ids=component_ids, root_species=root_species,
                        current_species=current_species, guild=guild, pop=pop, trait=trait, va=va, gen=gen,
                        registry=registry, elapsed_year=elapsed, age_ma=age,
                        ri_state=ri_state, clock_state=clock_state)
                    events.extend(ext_events)
                    for sid in mature_ext:
                        ext_state.pop(sid, None)
                    hab = habitats_r3(root_species, guild, trait, pop, metadata, env, cfg)
                    G, contact, td = _pair_metrics_barrier_coupled(pop, trait, root_species, metadata, lat, lon, env, cfg)
                    ri, clock = r21.pair_state_matrices(component_ids, root_species, ri_state, clock_state)

            if r21._is_multiple(elapsed, cfg.speciation_check_interval_years):
                births, founder_state, founder_stats_last = r21.maybe_speciate_founder(
                    current_species=current_species, root_species=root_species, component_ids=component_ids,
                    pop=pop, va=va, gen=gen, metadata=metadata, contact=contact, td=td, ri=ri, clock=clock,
                    registry=registry, child_counters=child_counters, elapsed_year=elapsed, age_ma=age,
                    founder_state=founder_state, cfg=cfg)
                if births:
                    events.extend(births)
                    hab = habitats_r3(root_species, guild, trait, pop, metadata, env, cfg)
                    touched = sorted({e["parent_species_id"] for e in births} | {e["daughter_species_id"] for e in births})
                    r21._reset_species_baselines(touched, pop=pop, current_species=current_species, hab=hab, guild=guild,
                                                 env=env, baselines=baselines, elapsed_year=elapsed,
                                                 occupancy_floor=cfg.occupancy_floor)
                    for sid in touched:
                        ext_state.pop(sid, None)

            if r21._is_multiple(elapsed, cfg.snapshot_interval_years) or abs(elapsed - duration) < 1e-6:
                qnorm = []
                for i, root_sid in enumerate(root_species):
                    m = metadata[root_sid]
                    sc = np.asarray([m["thermal_niche_sigma_c"], max(m["aridity_niche_sigma"] / 1.55, 1e-4), cfg.body_mass_scale])
                    qnorm.extend((va[i] / (sc * sc)).tolist())
                snapshots.append({
                    "age_ma": float(age), "elapsed_myr": elapsed / 1e6,
                    "species_richness": len(set(current_species)), "component_count": len(component_ids),
                    "total_population": float(pop.sum()),
                    "median_normalized_va": float(np.median(qnorm)) if qnorm else 0.0,
                    "max_intrinsic_ri": float(np.max(ri)) if ri.size else 0.0,
                    "max_isolation_clock_generations": float(np.max(clock)) if clock.size else 0.0,
                    "speciation_events_cumulative": sum(1 for e in events if e["event"] == "speciation"),
                    "extinction_events_cumulative": sum(1 for e in events if e["event"] == "ordinary_background_extinction"),
                    "fission_events_cumulative": sum(1 for e in events if e["event"] == "deme_fission"),
                    "barrier_bracket": [env["older_ma"], env["younger_ma"]],
                    "fractional_support_cells": int(np.count_nonzero((env["land_support"] > 1e-9) & (env["land_support"] < 1-1e-9))),
                })

    env_end = bp.environment_at(cfg.end_age_ma, a1, bcfg)
    hab_end = habitats_r3(root_species, guild, trait, pop, metadata, env_end, cfg)
    G, contact, td = _pair_metrics_barrier_coupled(pop, trait, root_species, metadata, lat, lon, env, cfg)
    ri, clock = r21.pair_state_matrices(component_ids, root_species, ri_state, clock_state)
    gate_diag = r21._gate_diagnostics(current_species, component_ids, pop, contact, td, ri, clock, cfg)
    return {
        "stage": R3_STAGE_ID, "config": asdict(cfg), "initial_total_population": initial_total,
        "final_total_population": float(pop.sum()), "root_species_ids": sorted(set(root_species)),
        "species_ids": sorted(set(current_species)), "component_ids": list(component_ids),
        "component_root_species": list(root_species), "component_species": list(current_species),
        "component_guild": guild, "population": pop, "trait": trait, "va": va,
        "generation_time": gen, "ri": ri, "clock": clock, "contact": contact, "trait_distance": td,
        "registry": [registry[k] for k in sorted(registry)], "events": events, "snapshots": snapshots,
        "founder_state": founder_state, "vicariance_state": vicariance_state, "extinction_state": ext_state,
        "founder_stats_last": founder_stats_last, "gate_diagnostics": gate_diag,
        "gene_flow_closure": gene_flow_closure, "topology_remap_mass": topology_remap_mass,
        "barrier_history": bp.build_all_transition_schedules(a1, bcfg)["summary"],
        "authority": {
            "paleogeographic_event_provider": "D3.2C_SOURCE_REUSED_BYTE_FOR_BYTE_AND_GENERALIZED_OVER_ALL_A1_BRACKETS",
            "paleogeographic_source_sha256": "5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730",
            "barrier_effective_connectivity": "D3.2B_PERMEABILITY_X_HABITAT_POWER_SEMANTICS",
            "barrier_coupled_migration": "D3.2B_MIGRATION_WITH_PERMEABILITY_SOURCE_REUSED",
            "barrier_coupled_gene_flow": "D3.2B_PAIR_METRICS_EXTENDED_PERMEABILITY_MASK_SOURCE_REUSED",
            "d3_2b_diversification_source_sha256": "9c2338cd8904bd6f9972c253be375384f6ec57193b4e3f5acf404f1ef2f344b2",
            "persistent_vicariance_fission_enabled": bool(cfg.persistent_vicariance_fission_enabled),
            "speciation_structural_gate": "D3.0C_SEALED_SOURCE_REUSED",
            "ordinary_extinction": "D3.2D_PERSISTENT_DETERMINISTIC_NONVIABILITY_SEMANTICS",
            "global_speciation_rate": None, "global_extinction_rate": None,
            "Deep_biological_coupling": False,
        },
    }
