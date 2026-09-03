from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import math

import numpy as np

from . import dynamic_demes as dd
from . import speciation_gate as sg
from . import additive_variance as av

STATUS = "PASS_ADDITIVE_GENETIC_VARIANCE_DYNAMICS_RECOVERY_CALIBRATION_CANDIDATE"


@dataclass(frozen=True)
class AdaptiveRadiationConfig:
    seed: int = 917231
    start_relative_year: float = 500_000.0
    end_relative_year: float = 5_000_000.0
    dt_years: float = 50_000.0
    snapshot_interval_years: float = 250_000.0
    occupancy_floor: float = 1e-6
    habitat_floor: float = 1e-12
    population_floor: float = 1e-15
    migration_reference_years: float = 250_000.0
    migration_fraction_ceiling: float = 0.30
    gene_flow_ceiling_per_step: float = 0.15
    trait_response_timescale_years: float = 300_000.0
    body_mass_scale: float = 0.35
    mutation_variance_supply_normalized_per_myr: float = 0.002
    mutation_variance_ceiling_normalized: float = 0.05
    selection_variance_depletion_per_generation: float = 2.0e-6
    selection_pressure_ceiling: float = 4.0
    drift_individual_equivalents_per_population_unit: float = 250_000.0
    drift_min_effective_size: float = 500.0
    maximum_total_exchange_fraction_per_deme: float = 0.45
    deme_fission_check_interval_years: float = 250_000.0
    deme_fission_min_component_fraction: float = 0.02
    deme_fission_min_absolute_population: float = 0.01
    deme_fission_min_root_species_fraction: float = 0.01
    speciation_enabled: bool = True
    species_fusion_enabled: bool = False
    Deep_adaptation_enabled: bool = False
    dragon_lineage_selection_enabled: bool = False
    sapience_enabled: bool = False
    civilization_enabled: bool = False
    author_selected_winner_enabled: bool = False


    def variance_cfg(self) -> av.AdditiveVarianceConfig:
        return av.AdditiveVarianceConfig(
            mutation_variance_supply_normalized_per_myr=self.mutation_variance_supply_normalized_per_myr,
            mutation_variance_ceiling_normalized=self.mutation_variance_ceiling_normalized,
            selection_variance_depletion_per_generation=self.selection_variance_depletion_per_generation,
            selection_pressure_ceiling=self.selection_pressure_ceiling,
            drift_individual_equivalents_per_population_unit=self.drift_individual_equivalents_per_population_unit,
            drift_min_effective_size=self.drift_min_effective_size,
            maximum_total_exchange_fraction_per_deme=self.maximum_total_exchange_fraction_per_deme,
        )

    def dynamic_cfg(self) -> dd.DynamicDemeConfig:
        return dd.DynamicDemeConfig(
            seed=self.seed,
            start_relative_year=self.start_relative_year,
            end_relative_year=self.end_relative_year,
            dt_years=self.dt_years,
            snapshot_interval_years=self.snapshot_interval_years,
            occupancy_floor=self.occupancy_floor,
            habitat_floor=self.habitat_floor,
            population_floor=self.population_floor,
            migration_reference_years=self.migration_reference_years,
            migration_fraction_ceiling=self.migration_fraction_ceiling,
            gene_flow_ceiling_per_step=self.gene_flow_ceiling_per_step,
            trait_response_timescale_years=self.trait_response_timescale_years,
            body_mass_scale=self.body_mass_scale,
        )


@dataclass
class AdaptiveRadiationResult:
    root_species_ids: list[str]
    final_species_ids: list[str]
    deme_ids: list[str]
    current_species_id: list[str]
    root_species_index: np.ndarray
    deme_guild_id: np.ndarray
    lat: np.ndarray
    lon: np.ndarray
    snapshot_relative_year: np.ndarray
    species_richness_history: np.ndarray
    total_population_history: np.ndarray
    occupied_cell_history: np.ndarray
    max_trait_distance_history: np.ndarray
    max_intrinsic_RI_history: np.ndarray
    max_isolation_clock_history: np.ndarray
    endpoint_population: np.ndarray
    endpoint_trait: np.ndarray
    endpoint_additive_variance: np.ndarray
    generation_time_proxy_years: np.ndarray
    endpoint_intrinsic_RI: np.ndarray
    endpoint_isolation_clock_generations: np.ndarray
    endpoint_contact_connectivity: np.ndarray
    endpoint_trait_distance: np.ndarray
    species_registry: list[dict]
    speciation_events: list[dict]
    deme_fission_events: list[dict]
    diagnostics: dict


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_config(path: Path) -> AdaptiveRadiationConfig:
    raw = _read_json(path)
    fields = AdaptiveRadiationConfig.__dataclass_fields__
    return AdaptiveRadiationConfig(**{k: raw[k] for k in fields if k in raw})


def _load_inputs(root: Path, cfg: AdaptiveRadiationConfig):
    d = dd._load_inputs(root, cfg.dynamic_cfg())
    gate_cfg = _read_json(root / "inputs/D3_0C_GATE/speciation_gate_v0_6_3D3_0C.json")
    if gate_cfg.get("version") != "0.6.3D3.0C":
        raise ValueError("D3.1 requires the calibrated D3.0C gate")
    required = {
        "minimum_effective_isolation_generations": 50_000.0,
        "minimum_intrinsic_RI": 0.65,
        "minimum_trait_distance": 1.0,
        "maximum_effective_exchange_pressure": 0.25,
    }
    for k, v in required.items():
        if not math.isclose(float(gate_cfg[k]), v, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"Unexpected D3.0C gate calibration for {k}")
    return d, gate_cfg


def _frame_pair(a1):
    ages = a1["age_ma"].astype(float)
    i66 = int(np.where(np.isclose(ages, 66.0))[0][0])
    i60 = int(np.where(np.isclose(ages, 60.0))[0][0])
    return i66, i60


def _substrate(a1, relative_year: float, residual_temp_anomaly_c: float):
    # The D3.1 replay lies between 65.5 and 61 Ma. We therefore interpolate
    # only between the existing materialized 66 and 60 Ma C2.2-rebased A1 frames.
    i66, i60 = _frame_pair(a1)
    age_ma = 66.0 - relative_year / 1_000_000.0
    alpha = float(np.clip((66.0 - age_ma) / 6.0, 0.0, 1.0))

    def lerp(key: str):
        return ((1.0 - alpha) * a1[key][i66].astype(float) + alpha * a1[key][i60].astype(float))

    land_support = np.clip(lerp("land_mask"), 0.0, 1.0)
    accessible = land_support > 1e-9
    # D3.0A ends after CHA-1 thermal recovery. Preserve its tiny residual and
    # let it decay; this is not a new catastrophe forcing.
    anomaly = float(residual_temp_anomaly_c) * math.exp(
        -max(relative_year - 500_000.0, 0.0) / 150_000.0
    )
    return {
        "age_ma": age_ma,
        "alpha_66_to_60": alpha,
        "land_support": land_support,
        "accessible": accessible,
        "temperature_c": lerp("temperature_c") + anomaly,
        "aridity_index": lerp("aridity_index"),
        "browse_forage": lerp("browse_forage"),
        "low_forage": lerp("low_forage"),
        "wetland_forage": lerp("wetland_forage"),
        "total_edible_forage": lerp("total_edible_forage"),
        "reference_population": lerp("population"),
        "plate_code_66": a1["plate_code"][i66].astype(np.uint8),
        "plate_code_60": a1["plate_code"][i60].astype(np.uint8),
    }


def _normalize_resource(arr, land_support):
    arr = np.maximum(arr, 0.0) * land_support
    vals = arr[land_support > 1e-9]
    pos = vals[vals > 0]
    scale = float(np.percentile(pos, 95)) if pos.size else 1.0
    return np.clip(arr / max(scale, 1e-15), 0.0, 1.0)


def _plant_resource(meta, sub):
    guild = meta["guild"]
    if guild == "large_browser":
        r = sub["browse_forage"]
    elif guild == "medium_low_vegetation_feeder":
        r = sub["low_forage"]
    elif guild == "small_reptiloid_generalist":
        w = meta.get("diet_weights", {})
        r = (
            float(w.get("browse", 0.0)) * sub["browse_forage"]
            + float(w.get("low", 0.0)) * sub["low_forage"]
            + float(w.get("wetland", 0.0)) * sub["wetland_forage"]
        )
    else:
        r = sub["total_edible_forage"]
    return _normalize_resource(r, sub["land_support"])


def _root_species_population(pop, root_idx, nspecies):
    return dd._species_from_demes(pop, root_idx, nspecies)


def _habitats(pop, trait, root_idx, root_species_ids, species_guild, metadata, sub, cfg):
    nspecies = len(root_species_ids)
    sp = _root_species_population(pop, root_idx, nspecies)
    plant = [None] * nspecies
    for si, sid in enumerate(root_species_ids):
        if int(species_guild[si]) <= 4:
            plant[si] = _plant_resource(metadata[sid], sub)

    out = np.zeros_like(pop)
    prey_cache = {}
    for di, si0 in enumerate(root_idx):
        si = int(si0)
        sid = root_species_ids[si]
        meta = metadata[sid]
        g = int(species_guild[si])
        climate = dd._climate_suitability(
            meta,
            trait[di],
            sub["temperature_c"],
            sub["aridity_index"],
            sub["accessible"],
            cfg.habitat_floor,
        )
        if g <= 4:
            resource = plant[si]
        else:
            if si not in prey_cache:
                prey_cache[si] = dd._prey_resource_for_species(
                    meta, sp, species_guild, sub["accessible"]
                )
            resource = prey_cache[si]
        q = climate * np.maximum(resource, cfg.habitat_floor) * np.maximum(sub["land_support"], 1e-9)
        q[~sub["accessible"]] = 0.0
        m = float(q.max())
        if m > 0:
            q /= m
        out[di] = q
    return out


def _opportunity(habitat, root_idx, species_guild, sub, nspecies):
    sh = dd._species_habitat_from_demes(habitat, root_idx, nspecies)
    out = np.zeros(nspecies, dtype=float)
    for si, g in enumerate(species_guild):
        out[si] = float(np.sum(sh[si] * np.maximum(sub["reference_population"][int(g) - 1], 0.0)))
    return out


def _migration(pop, habitat, root_idx, root_species_ids, metadata, lat, lon, sub, dt, cfg):
    edge = dd._median_land_edge_km(lat, lon, sub["accessible"])
    out = np.zeros_like(pop)
    for di, si0 in enumerate(root_idx):
        sid = root_species_ids[int(si0)]
        f = dd._migration_fraction(float(metadata[sid]["dispersal_scale_km"]), edge, dt, cfg.dynamic_cfg())
        moved = dd._transport_once(pop[di], habitat[di])
        q = (1.0 - f) * pop[di] + f * moved
        q[~sub["accessible"]] = 0.0
        before = float(pop[di].sum())
        after = float(q.sum())
        # The provider's terrestrial support remains nonzero throughout this
        # interval for any 66/60 Ma transitional cell, so this rescaling only
        # removes numerical leakage to permanent ocean cells.
        if before > 0 and after > 0:
            q *= before / after
        out[di] = q
    return out


def _demography(pop, habitat, root_idx, root_species_ids, species_guild, metadata,
                initial_root_total, initial_opportunity, sub, dt):
    nspecies = len(root_species_ids)
    sp = _root_species_population(pop, root_idx, nspecies)
    current = sp.sum(axis=(1, 2))
    opp = _opportunity(habitat, root_idx, species_guild, sub, nspecies)
    target = np.zeros(nspecies, dtype=float)

    for g in range(1, 7):
        idx = np.where(species_guild == g)[0]
        guild_target = float(sub["reference_population"][g - 1].sum())
        if g >= 5:
            cur_prey = float(sp[species_guild <= 4].sum())
            ref_prey = float(sub["reference_population"][:4].sum())
            guild_target *= float(np.clip(cur_prey / max(ref_prey, 1e-15), 0.0, 1.5))
        base = initial_root_total[idx]
        share = base / max(float(base.sum()), 1e-15)
        ratio = np.divide(
            opp[idx], initial_opportunity[idx], out=np.ones(len(idx), dtype=float),
            where=initial_opportunity[idx] > 1e-15,
        )
        w = share * np.clip(ratio, 1e-6, 1e6)
        w /= max(float(w.sum()), 1e-15)
        target[idx] = guild_target * w

    new_total = np.zeros_like(current)
    for si, sid in enumerate(root_species_ids):
        g = int(species_guild[si])
        tau = dd.DEFAULT_DEMOGRAPHIC_TAU_YR[g] / max(float(metadata[sid]["relative_reproduction_rate"]), 1e-6)
        a = 1.0 - math.exp(-dt / tau)
        new_total[si] = max(0.0, current[si] + a * (target[si] - current[si]))

    out = pop.copy()
    for si in range(nspecies):
        idx = np.where(root_idx == si)[0]
        scale = float(new_total[si] / max(current[si], 1e-15))
        out[idx] *= scale
    return out


def _variance_supply(va, root_idx, root_species_ids, metadata, dt, cfg):
    if cfg.mutation_variance_supply_normalized_per_myr <= 0:
        return va
    out = va.copy()
    dcfg = cfg.dynamic_cfg()
    for di, si0 in enumerate(root_idx):
        sid = root_species_ids[int(si0)]
        meta = metadata[sid]
        scales = np.array([
            max(float(meta["thermal_niche_sigma_c"]), 1e-6),
            max(float(meta["aridity_niche_sigma"]) / 1.55, 1e-4),
            max(float(dcfg.body_mass_scale), 1e-6),
        ])
        q = out[di] / (scales * scales)
        q += cfg.mutation_variance_supply_normalized_per_myr * (dt / 1_000_000.0)
        q = np.clip(q, 0.0, cfg.mutation_variance_ceiling_normalized)
        out[di] = q * scales * scales
    return out


def _pair_metrics(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg):
    nd = len(root_idx)
    G = np.zeros((nd, nd), dtype=float)
    contact = np.zeros((nd, nd), dtype=float)
    td = np.zeros((nd, nd), dtype=float)
    dcfg = cfg.dynamic_cfg()
    for si, sid in enumerate(root_species_ids):
        idx = np.where(root_idx == si)[0]
        meta = metadata[sid]
        ds = float(meta["dispersal_scale_km"])
        tscale = max(float(meta["thermal_niche_sigma_c"]), 1e-6)
        dscale = max(float(meta["aridity_niche_sigma"]) / 1.55, 1e-4)
        mscale = max(float(dcfg.body_mass_scale), 1e-6)
        for a in range(len(idx)):
            i = int(idx[a])
            for b in range(a + 1, len(idx)):
                j = int(idx[b])
                g, _, _ = dd._pair_gene_flow(pop[i], pop[j], ds, lat, lon, dcfg.gene_flow_ceiling_per_step)
                G[i, j] = G[j, i] = g
                p = sg.contact_connectivity_from_d30b_gene_flow(g)
                contact[i, j] = contact[j, i] = p
                dz = np.array([
                    (trait[i, 0] - trait[j, 0]) / tscale,
                    (trait[i, 1] - trait[j, 1]) / dscale,
                    (trait[i, 2] - trait[j, 2]) / mscale,
                ])
                x = float(np.sqrt(np.sum(dz * dz)))
                td[i, j] = td[j, i] = x
    return G, contact, td


def _trait_mix(trait, pop, G, intrinsic_ri, root_idx):
    # Species identity itself never switches exchange off. Sister species can
    # remain in secondary contact; only intrinsic RI reduces effective exchange.
    out = trait.copy()
    delta = np.zeros_like(out)
    totals = pop.sum(axis=(1, 2))
    nd = len(root_idx)
    for i in range(nd):
        ni = float(totals[i])
        if ni <= 0:
            continue
        for j in range(i + 1, nd):
            if root_idx[i] != root_idx[j]:
                continue
            nj = float(totals[j])
            if nj <= 0:
                continue
            mix = float(G[i, j] * (1.0 - intrinsic_ri[i, j]))
            if mix <= 0:
                continue
            harmonic = 2.0 * ni * nj / (ni + nj)
            exchange = mix * harmonic
            dz = out[j] - out[i]
            delta[i] += (exchange / ni) * dz
            delta[j] -= (exchange / nj) * dz
    return out + delta


def _advance_pair_state(intrinsic_ri, isolation_clock, contact, td, generation_time, root_idx, dt):
    ri = intrinsic_ri.copy()
    clock = isolation_clock.copy()
    nd = len(root_idx)
    for i in range(nd):
        for j in range(i + 1, nd):
            if root_idx[i] != root_idx[j]:
                continue
            delta_generations = dt / max(float(generation_time[i]), float(generation_time[j]), 1e-9)
            st = sg.advance_pair_state(
                ri[i, j], clock[i, j], delta_generations, contact[i, j], td[i, j]
            )
            ri[i, j] = ri[j, i] = float(st["intrinsic_RI"])
            clock[i, j] = clock[j, i] = float(st["isolation_clock_generations"])
    return ri, clock


def _copy_expand_square(old, new_n):
    out = np.zeros((new_n, new_n), dtype=float)
    n = old.shape[0]
    out[:n, :n] = old
    return out


def _fission_demes(deme_ids, root_idx, deme_guild, current_species, pop, trait, va, generation_time,
                   intrinsic_ri, isolation_clock, relative_year, lat, lon, cfg):
    old_n = len(deme_ids)
    additions = []
    counters = defaultdict(int)
    for did in deme_ids:
        if "_F" in did:
            stem, _, tail = did.rpartition("_F")
            if tail.isdigit():
                counters[stem] = max(counters[stem], int(tail))

    for di in range(old_n):
        p = pop[di]
        total = float(p.sum())
        if total <= cfg.deme_fission_min_absolute_population:
            continue
        comps = dd._components(p > cfg.occupancy_floor)
        if len(comps) < 2:
            continue
        comp_rows = []
        for cells in comps:
            mass = float(sum(float(p[i, j]) for i, j in cells))
            comp_rows.append((mass, cells))
        comp_rows.sort(key=lambda x: -x[0])
        root_total = float(pop[root_idx == root_idx[di]].sum())
        significant = [
            x for x in comp_rows
            if x[0] >= cfg.deme_fission_min_absolute_population
            and x[0] / total >= cfg.deme_fission_min_component_fraction
            and x[0] / max(root_total, 1e-15) >= cfg.deme_fission_min_root_species_fraction
        ]
        if len(significant) < 2:
            continue
        # Largest component remains in the existing deme. Small insignificant
        # tails remain with it and are explicitly below the fission threshold.
        retained_mask = np.ones_like(p, dtype=bool)
        for _, cells in significant[1:]:
            for i, j in cells:
                retained_mask[i, j] = False
        original = pop[di].copy()
        pop[di] = np.where(retained_mask, original, 0.0)
        parent_did = deme_ids[di]
        for rank, (mass, cells) in enumerate(significant[1:], start=1):
            q = np.zeros_like(p)
            for i, j in cells:
                q[i, j] = original[i, j]
            counters[parent_did] += 1
            suffix = counters[parent_did]
            nid = f"{parent_did}_F{suffix:02d}"
            additions.append({
                "parent_index": di,
                "deme_id": nid,
                "population": q,
                "population_total": float(q.sum()),
                "component_rank": rank,
                "event_relative_year": float(relative_year),
                "centroid": dd._weighted_centroid(lat, lon, q),
            })

    if not additions:
        return (deme_ids, root_idx, deme_guild, current_species, pop, trait, va,
                generation_time, intrinsic_ri, isolation_clock, [])

    new_ids = list(deme_ids)
    new_root = list(root_idx.astype(int))
    new_guild = list(deme_guild.astype(int))
    new_species = list(current_species)
    new_pop = [x.copy() for x in pop]
    new_trait = [x.copy() for x in trait]
    new_va = [x.copy() for x in va]
    new_gen = list(generation_time.astype(float))

    nnew = old_n + len(additions)
    new_ri = _copy_expand_square(intrinsic_ri, nnew)
    new_clock = _copy_expand_square(isolation_clock, nnew)
    event_rows = []
    for k, add in enumerate(additions):
        parent = int(add["parent_index"])
        ni = old_n + k
        new_ids.append(add["deme_id"])
        new_root.append(int(root_idx[parent]))
        new_guild.append(int(deme_guild[parent]))
        new_species.append(str(current_species[parent]))
        new_pop.append(add["population"])
        new_trait.append(trait[parent].copy())
        new_va.append(va[parent].copy())
        new_gen.append(float(generation_time[parent]))
        # New component inherits the parent's historical relationship to all
        # other demes in the same root lineage. Parent<->new begins at zero,
        # because they were one deme until this fragmentation event.
        for j in range(old_n):
            if j == parent:
                continue
            if root_idx[j] == root_idx[parent]:
                new_ri[ni, j] = new_ri[j, ni] = intrinsic_ri[parent, j]
                new_clock[ni, j] = new_clock[j, ni] = isolation_clock[parent, j]
        for kk in range(k):
            other_i = old_n + kk
            other_parent = int(additions[kk]["parent_index"])
            if other_parent == parent:
                new_ri[ni, other_i] = new_ri[other_i, ni] = 0.0
                new_clock[ni, other_i] = new_clock[other_i, ni] = 0.0
            elif root_idx[other_parent] == root_idx[parent]:
                new_ri[ni, other_i] = new_ri[other_i, ni] = intrinsic_ri[parent, other_parent]
                new_clock[ni, other_i] = new_clock[other_i, ni] = isolation_clock[parent, other_parent]
        event_rows.append({
            "event": "deme_fission",
            "relative_year": add["event_relative_year"],
            "parent_deme_id": deme_ids[parent],
            "daughter_deme_id": add["deme_id"],
            "species_id_at_fission": str(current_species[parent]),
            "root_species_id": None,
            "population": add["population_total"],
            "centroid_lat_deg": float(add["centroid"][0]),
            "centroid_lon_deg": float(add["centroid"][1]),
            "semantic_status": "DEMOGRAPHIC_FRAGMENT_NOT_SPECIES",
        })

    return (
        new_ids,
        np.asarray(new_root, dtype=np.int32),
        np.asarray(new_guild, dtype=np.uint8),
        new_species,
        np.stack(new_pop),
        np.stack(new_trait),
        np.stack(new_va),
        np.asarray(new_gen, dtype=float),
        new_ri,
        new_clock,
        event_rows,
    )


def _reproductive_components(indices, contact, td, intrinsic_ri, isolation_clock):
    indices = list(map(int, indices))
    adj = {i: set() for i in indices}
    for a in range(len(indices)):
        i = indices[a]
        for b in range(a + 1, len(indices)):
            j = indices[b]
            e = sg.effective_exchange_pressure(contact[i, j], intrinsic_ri[i, j])
            isolated = (
                isolation_clock[i, j] >= 50_000.0
                and intrinsic_ri[i, j] >= 0.65
                and td[i, j] >= 1.0
                and e <= 0.25
            )
            if not isolated:
                adj[i].add(j)
                adj[j].add(i)
    out = []
    seen = set()
    for i in indices:
        if i in seen:
            continue
        stack = [i]
        seen.add(i)
        comp = []
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in sorted(adj[u]):
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        out.append(sorted(comp))
    return out


def _species_child_id(root_sid: str, counter: int):
    return f"{root_sid}_D{counter:02d}"


def _maybe_speciate(current_species, root_idx, root_species_ids, deme_ids, pop, contact, td,
                     intrinsic_ri, isolation_clock, registry, child_counters, relative_year):
    totals = pop.sum(axis=(1, 2))
    events = []
    # Snapshot the extant set so a child born in this pass cannot immediately
    # branch again at the same model time.
    extant = sorted(set(current_species))
    for sid in extant:
        indices = np.array([i for i, x in enumerate(current_species) if x == sid], dtype=int)
        if len(indices) < 2:
            continue
        comps = _reproductive_components(indices, contact, td, intrinsic_ri, isolation_clock)
        if len(comps) < 2:
            continue
        comps.sort(key=lambda c: (-float(totals[c].sum()), [deme_ids[i] for i in c]))
        parent_comp = comps[0]
        # One daughter maximum per extant species per gate checkpoint. Use the
        # largest remaining component; no narrative/geographic preference enters.
        candidate = comps[1]
        complement = [i for i in indices if i not in candidate]
        branch_pop = float(totals[candidate].sum())
        complement_pop = float(totals[complement].sum())
        species_pop = branch_pop + complement_pop
        cross = []
        for i in candidate:
            for j in complement:
                cross.append({
                    "isolation_clock_generations": float(isolation_clock[i, j]),
                    "intrinsic_RI": float(intrinsic_ri[i, j]),
                    "trait_distance": float(td[i, j]),
                    "contact_connectivity": float(contact[i, j]),
                })
        gate = sg.evaluate_branch_gate(
            cross_pair_states=cross,
            branch_population=branch_pop,
            complement_population=complement_pop,
            species_population=species_pop,
        )
        if not gate["gate_ready"]:
            continue
        root_sid = registry[sid]["root_species_id"]
        child_counters[root_sid] += 1
        child = _species_child_id(root_sid, child_counters[root_sid])
        for i in candidate:
            current_species[i] = child
        registry[child] = {
            "species_id": child,
            "parent_species_id": sid,
            "root_species_id": root_sid,
            "guild_id": int(registry[sid]["guild_id"]),
            "birth_relative_year": float(relative_year),
            "birth_age_ma": float(66.0 - relative_year / 1_000_000.0),
            "member_demes_at_birth": [deme_ids[i] for i in candidate],
            "birth_population": branch_pop,
            "semantic_status": "EMERGENT_SPECIES_OBJECT",
        }
        events.append({
            "event": "speciation",
            "relative_year": float(relative_year),
            "age_ma": float(66.0 - relative_year / 1_000_000.0),
            "parent_species_id": sid,
            "daughter_species_id": child,
            "root_species_id": root_sid,
            "daughter_deme_ids": [deme_ids[i] for i in candidate],
            "daughter_population": branch_pop,
            "parent_remainder_population": complement_pop,
            "gate": gate,
            "population_conservation_error": 0.0,
        })
    return events


def _snapshot_metrics(pop, trait, root_idx, current_species, contact, td, ri, clock, occupancy_floor):
    occupied = int(np.count_nonzero(pop > occupancy_floor))
    mask = np.triu(root_idx[:, None] == root_idx[None, :], 1)
    if np.any(mask):
        max_td = float(np.max(td[mask]))
        max_ri = float(np.max(ri[mask]))
        max_clock = float(np.max(clock[mask]))
        max_contact = float(np.max(contact[mask]))
    else:
        max_td = max_ri = max_clock = max_contact = 0.0
    return {
        "species_richness": len(set(current_species)),
        "total_population": float(pop.sum()),
        "occupied_deme_cells": occupied,
        "max_trait_distance": max_td,
        "max_intrinsic_RI": max_ri,
        "max_isolation_clock_generations": max_clock,
        "max_contact_connectivity": max_contact,
    }


def run(root: Path, cfg: AdaptiveRadiationConfig) -> AdaptiveRadiationResult:
    if cfg.start_relative_year != 500_000.0:
        raise ValueError("D3.1A must start from the D3.0A +500 kyr endpoint")
    if cfg.end_relative_year > 5_000_000.0 + 1e-9:
        raise ValueError("D3.1A is bounded to the +0.5 to +5 Myr calibration replay")
    if cfg.dt_years <= 0 or cfg.end_relative_year <= cfg.start_relative_year:
        raise ValueError("Invalid D3.1A time window")
    nsteps_float = (cfg.end_relative_year - cfg.start_relative_year) / cfg.dt_years
    if abs(nsteps_float - round(nsteps_float)) > 1e-9:
        raise ValueError("D3.1A duration must be an integer number of timesteps")
    if cfg.species_fusion_enabled or cfg.Deep_adaptation_enabled or cfg.dragon_lineage_selection_enabled:
        raise ValueError("Forbidden D3.1A scope switch enabled")

    d, gate_cfg = _load_inputs(root, cfg)
    pz = d["parent_state"]
    root_species_ids = d["species_ids"]
    metadata = d["metadata"]
    species_guild = pz["guild_id"].astype(np.uint8)
    lat = pz["lat"].astype(float)
    lon = pz["lon"].astype(float)

    deme_ids, root_idx, deme_guild, pop, _ = dd._partition_parent_into_demes(
        root_species_ids,
        pz["endpoint_population_500kyr"].astype(float),
        d["seed_registry"],
        lat,
        lon,
        cfg.occupancy_floor,
    )
    trait, va, generation_time, provenance = dd._deme_trait_initialization(
        root_idx, root_species_ids, metadata
    )
    current_species = [root_species_ids[int(si)] for si in root_idx]
    intrinsic_ri = np.zeros((len(deme_ids), len(deme_ids)), dtype=float)
    isolation_clock = np.zeros_like(intrinsic_ri)

    registry = {}
    for si, sid in enumerate(root_species_ids):
        registry[sid] = {
            "species_id": sid,
            "parent_species_id": metadata[sid].get("parent_species_id"),
            "root_species_id": sid,
            "guild_id": int(species_guild[si]),
            "birth_relative_year": None,
            "birth_age_ma": None,
            "semantic_status": "INHERITED_D2_2_SURVIVOR_SPECIES_PREEXISTING_D3_1",
            "trait_provenance": metadata[sid].get("trait_provenance", "D1_EXPLICIT"),
        }
    child_counters = defaultdict(int)
    speciation_events = []
    fission_events = []
    initial_variance_summary = av.normalized_variance_summary(
        va, root_idx, root_species_ids, metadata, cfg.body_mass_scale
    )
    variance_budget = {
        "selection_loss_q_sum": 0.0,
        "drift_loss_q_sum": 0.0,
        "mutation_gain_q_sum": 0.0,
        "gene_flow_first_moment_error_max": 0.0,
        "gene_flow_second_moment_error_max": 0.0,
        "gene_flow_total_pair_exchange_mass": 0.0,
    }

    sub0 = _substrate(d["a1"], cfg.start_relative_year, d["temp_anomaly_c"])
    hab0 = _habitats(pop, trait, root_idx, root_species_ids, species_guild, metadata, sub0, cfg)
    initial_root_total = _root_species_population(pop, root_idx, len(root_species_ids)).sum(axis=(1, 2))
    initial_opportunity = _opportunity(hab0, root_idx, species_guild, sub0, len(root_species_ids))
    parent_species_totals = pz["endpoint_species_total"].astype(float)
    init_partition_error = float(np.max(np.abs(initial_root_total - parent_species_totals)))

    snapshot_times = [cfg.start_relative_year]
    G, contact, td = _pair_metrics(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg)
    m0 = _snapshot_metrics(pop, trait, root_idx, current_species, contact, td, intrinsic_ri, isolation_clock, cfg.occupancy_floor)
    metrics = [m0]
    snapshot_rows = [{"relative_year": cfg.start_relative_year, "age_ma": 65.5, **m0}]

    steps = int(round(nsteps_float))
    snap_every = max(1, int(round(cfg.snapshot_interval_years / cfg.dt_years)))
    fiss_every = max(1, int(round(cfg.deme_fission_check_interval_years / cfg.dt_years)))

    for step in range(1, steps + 1):
        relative_year = cfg.start_relative_year + step * cfg.dt_years
        sub = _substrate(d["a1"], relative_year, d["temp_anomaly_c"])

        habitat = _habitats(pop, trait, root_idx, root_species_ids, species_guild, metadata, sub, cfg)
        pop = _migration(pop, habitat, root_idx, root_species_ids, metadata, lat, lon, sub, cfg.dt_years, cfg)
        habitat = _habitats(pop, trait, root_idx, root_species_ids, species_guild, metadata, sub, cfg)
        pop = _demography(
            pop, habitat, root_idx, root_species_ids, species_guild, metadata,
            initial_root_total, initial_opportunity, sub, cfg.dt_years,
        )

        G, contact, td = _pair_metrics(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg)
        targets = dd._selection_targets(pop, sub["temperature_c"], sub["aridity_index"])
        trait_before_selection = trait.copy()
        selected = dd._selection_update(
            trait, va, targets, root_idx, root_species_ids, metadata, cfg.dt_years, cfg.dynamic_cfg()
        )
        deme_totals = pop.sum(axis=(1, 2))
        trait, va, flow_var_diag = av.gene_flow_moment_mix(
            selected, va, deme_totals, G, intrinsic_ri, root_idx, cfg.variance_cfg()
        )
        va, variance_components = av.advance_nonflow_variance(
            va, trait_before_selection, targets, deme_totals, generation_time, root_idx,
            root_species_ids, metadata, cfg.body_mass_scale, cfg.dt_years, cfg.variance_cfg()
        )
        variance_budget["gene_flow_first_moment_error_max"] = max(
            variance_budget["gene_flow_first_moment_error_max"],
            float(flow_var_diag["first_moment_conservation_max_abs"]),
        )
        variance_budget["gene_flow_second_moment_error_max"] = max(
            variance_budget["gene_flow_second_moment_error_max"],
            float(flow_var_diag["second_moment_conservation_max_abs"]),
        )
        variance_budget["gene_flow_total_pair_exchange_mass"] += float(flow_var_diag["total_pair_exchange_mass"])
        for row in variance_components:
            qb = np.asarray(row["q_before"], dtype=float)
            qs = np.asarray(row["q_after_selection"], dtype=float)
            qd = np.asarray(row["q_after_drift"], dtype=float)
            qm = np.asarray(row["q_after_mutation"], dtype=float)
            variance_budget["selection_loss_q_sum"] += float(np.maximum(qb - qs, 0.0).sum())
            variance_budget["drift_loss_q_sum"] += float(np.maximum(qs - qd, 0.0).sum())
            variance_budget["mutation_gain_q_sum"] += float(np.maximum(qm - qd, 0.0).sum())

        # Recompute pair geometry after trait evolution, then advance the D3.0C
        # stateful RI and biological-time clock.
        G, contact, td = _pair_metrics(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg)
        intrinsic_ri, isolation_clock = _advance_pair_state(
            intrinsic_ri, isolation_clock, contact, td, generation_time, root_idx, cfg.dt_years
        )

        # Dynamic deme topology is demographic bookkeeping, not species birth.
        if step % fiss_every == 0:
            (
                deme_ids, root_idx, deme_guild, current_species, pop, trait, va,
                generation_time, intrinsic_ri, isolation_clock, new_fissions,
            ) = _fission_demes(
                deme_ids, root_idx, deme_guild, current_species, pop, trait, va,
                generation_time, intrinsic_ri, isolation_clock, relative_year,
                lat, lon, cfg,
            )
            for row in new_fissions:
                row["root_species_id"] = root_species_ids[int(root_idx[deme_ids.index(row["daughter_deme_id"])])]
            fission_events.extend(new_fissions)
            if new_fissions:
                G, contact, td = _pair_metrics(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg)

        # Species birth is evaluated only at materialized snapshot cadence, not
        # on every numerical step. Persistence itself is measured continuously
        # in generations, so this does not recreate a frame-count gate.
        if cfg.speciation_enabled and step % snap_every == 0:
            new_events = _maybe_speciate(
                current_species, root_idx, root_species_ids, deme_ids, pop,
                contact, td, intrinsic_ri, isolation_clock,
                registry, child_counters, relative_year,
            )
            speciation_events.extend(new_events)

        if step % snap_every == 0 or step == steps:
            sm = _snapshot_metrics(
                pop, trait, root_idx, current_species, contact, td,
                intrinsic_ri, isolation_clock, cfg.occupancy_floor,
            )
            snapshot_times.append(relative_year)
            metrics.append(sm)
            snapshot_rows.append({
                "relative_year": float(relative_year),
                "age_ma": float(sub["age_ma"]),
                "alpha_66_to_60": float(sub["alpha_66_to_60"]),
                "deme_count": len(deme_ids),
                **sm,
            })

    final_species_ids = sorted(set(current_species))
    # Endpoint diagnostics after all possible fission/speciation changes.
    G, contact, td = _pair_metrics(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg)
    final_root_total = _root_species_population(pop, root_idx, len(root_species_ids)).sum(axis=(1, 2))
    max_norm_va = 0.0
    for di, si0 in enumerate(root_idx):
        sid = root_species_ids[int(si0)]
        meta = metadata[sid]
        scales = np.array([
            max(float(meta["thermal_niche_sigma_c"]), 1e-6),
            max(float(meta["aridity_niche_sigma"]) / 1.55, 1e-4),
            cfg.body_mass_scale,
        ])
        max_norm_va = max(max_norm_va, float(np.max(va[di] / (scales * scales))))

    final_variance_summary = av.normalized_variance_summary(
        va, root_idx, root_species_ids, metadata, cfg.body_mass_scale
    )
    diagnostics = {
        "status": STATUS,
        "config": asdict(cfg),
        "root_survivor_species_count": len(root_species_ids),
        "initial_species_richness": 31,
        "final_species_richness": len(final_species_ids),
        "speciation_event_count": len(speciation_events),
        "initial_deme_count": 115,
        "final_deme_count": len(deme_ids),
        "deme_fission_event_count": len(fission_events),
        "initial_partition_max_abs_error": init_partition_error,
        "initial_total_population": float(parent_species_totals.sum()),
        "final_total_population": float(pop.sum()),
        "relative_total_population_change": float((pop.sum() - parent_species_totals.sum()) / parent_species_totals.sum()),
        "final_root_lineage_population_total": float(final_root_total.sum()),
        "max_normalized_additive_variance": max_norm_va,
        "initial_normalized_additive_variance_summary": initial_variance_summary,
        "final_normalized_additive_variance_summary": final_variance_summary,
        "variance_budget": variance_budget,
        "mutation_supply_directional_mean_shift": 0.0,
        "additive_variance_dynamic_solver_enabled": True,
        "variance_semantics_recovered_from_v0_6_3C": ["selection_depletion", "genetic_drift_depletion", "gene_flow_moment_mixing", "undirected_mutation_supply"],
        "variance_coefficients_status": "RECALIBRATED_CANDIDATE_ORIGINAL_V0_6_3C_SOURCE_NOT_RECOVERED",
        "physical_provider": "INTERPOLATED_A1_C2_2_REBASED_66_TO_60_MA",
        "start_physical_age_ma": 65.5,
        "end_physical_age_ma": float(66.0 - cfg.end_relative_year / 1_000_000.0),
        "species_identity_changes_ecology": False,
        "species_identity_forces_gene_flow_zero": False,
        "species_fusion_enabled": False,
        "Deep_adaptation_enabled": False,
        "dragon_lineage_selection_enabled": False,
        "sapience_enabled": False,
        "civilization_enabled": False,
        "author_selected_winner_enabled": False,
        "HSG_025_trait_provenance": metadata["HSG_025"].get("trait_provenance"),
        "snapshot_rows": snapshot_rows,
        "gate_calibration": gate_cfg,
        "interpretation": (
            "Species richness is an emergent output. Zero births is a valid replay result; "
            "D3.1 must not tune parameters merely to manufacture adaptive radiation."
        ),
    }

    return AdaptiveRadiationResult(
        root_species_ids=root_species_ids,
        final_species_ids=final_species_ids,
        deme_ids=deme_ids,
        current_species_id=list(current_species),
        root_species_index=root_idx,
        deme_guild_id=deme_guild,
        lat=lat,
        lon=lon,
        snapshot_relative_year=np.asarray(snapshot_times, dtype=float),
        species_richness_history=np.asarray([m["species_richness"] for m in metrics], dtype=np.int32),
        total_population_history=np.asarray([m["total_population"] for m in metrics], dtype=float),
        occupied_cell_history=np.asarray([m["occupied_deme_cells"] for m in metrics], dtype=np.int64),
        max_trait_distance_history=np.asarray([m["max_trait_distance"] for m in metrics], dtype=float),
        max_intrinsic_RI_history=np.asarray([m["max_intrinsic_RI"] for m in metrics], dtype=float),
        max_isolation_clock_history=np.asarray([m["max_isolation_clock_generations"] for m in metrics], dtype=float),
        endpoint_population=pop,
        endpoint_trait=trait,
        endpoint_additive_variance=va,
        generation_time_proxy_years=generation_time,
        endpoint_intrinsic_RI=intrinsic_ri,
        endpoint_isolation_clock_generations=isolation_clock,
        endpoint_contact_connectivity=contact,
        endpoint_trait_distance=td,
        species_registry=[registry[k] for k in sorted(registry)],
        speciation_events=speciation_events,
        deme_fission_events=fission_events,
        diagnostics=diagnostics,
    )


def write_outputs(root: Path, result: AdaptiveRadiationResult):
    out = root / "outputs/hybrid1/additive_variance_dynamics_v0_6_3D3_1A"
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out / "adaptive_radiation_state.npz",
        root_species_id=np.asarray(result.root_species_ids),
        final_species_id=np.asarray(result.final_species_ids),
        deme_id=np.asarray(result.deme_ids),
        current_species_id=np.asarray(result.current_species_id),
        root_species_index=result.root_species_index,
        guild_id=result.deme_guild_id,
        lat=result.lat.astype(np.float32),
        lon=result.lon.astype(np.float32),
        snapshot_relative_year=result.snapshot_relative_year,
        species_richness_history=result.species_richness_history,
        total_population_history=result.total_population_history,
        occupied_cell_history=result.occupied_cell_history,
        max_trait_distance_history=result.max_trait_distance_history,
        max_intrinsic_RI_history=result.max_intrinsic_RI_history,
        max_isolation_clock_history=result.max_isolation_clock_history,
        endpoint_population=result.endpoint_population,
        endpoint_trait=result.endpoint_trait,
        endpoint_additive_variance=result.endpoint_additive_variance,
        generation_time_proxy_years=result.generation_time_proxy_years,
        endpoint_intrinsic_RI=result.endpoint_intrinsic_RI,
        endpoint_isolation_clock_generations=result.endpoint_isolation_clock_generations,
        endpoint_contact_connectivity=result.endpoint_contact_connectivity,
        endpoint_trait_distance=result.endpoint_trait_distance,
    )
    (out / "adaptive_radiation_diagnostics.json").write_text(
        json.dumps(result.diagnostics, indent=2, sort_keys=True), encoding="utf-8"
    )
    (out / "species_registry.json").write_text(
        json.dumps({"species": result.species_registry}, indent=2, sort_keys=True), encoding="utf-8"
    )
    (out / "speciation_events.json").write_text(
        json.dumps({"events": result.speciation_events}, indent=2, sort_keys=True), encoding="utf-8"
    )
    (out / "deme_fission_events.json").write_text(
        json.dumps({"events": result.deme_fission_events}, indent=2, sort_keys=True), encoding="utf-8"
    )
    return out


def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
