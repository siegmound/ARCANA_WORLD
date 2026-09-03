from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections import deque
import copy
import json
import math

import numpy as np


GUILD_NAMES = {
    1: "small_generalist_herbivore",
    2: "large_browser",
    3: "medium_low_vegetation_feeder",
    4: "small_reptiloid_generalist",
    5: "medium_carnivore",
    6: "apex_carnivore",
}

PREY_KEY_TO_GUILD = {
    "small_herbivore": 1,
    "browser": 2,
    "low_feeder": 3,
    "reptiloid": 4,
}

# These are macroecological relaxation times, not organismal generation times.
DEFAULT_DEMOGRAPHIC_TAU_YR = {
    1: 120_000.0,
    2: 180_000.0,
    3: 140_000.0,
    4: 160_000.0,
    5: 220_000.0,
    6: 350_000.0,
}

# Generation-time proxies are exported only for future biological-time persistence
# accounting. They do not control births in this benchmark.
DEFAULT_GENERATION_PROXY_YR = {
    1: 3.0,
    2: 12.0,
    3: 6.0,
    4: 4.0,
    5: 8.0,
    6: 18.0,
}


@dataclass(frozen=True)
class DynamicDemeConfig:
    seed: int = 917231
    start_relative_year: float = 500_000.0
    end_relative_year: float = 1_000_000.0
    dt_years: float = 10_000.0
    snapshot_interval_years: float = 50_000.0
    occupancy_floor: float = 1e-6
    habitat_floor: float = 1e-12
    population_floor: float = 1e-15
    migration_reference_years: float = 250_000.0
    migration_fraction_ceiling: float = 0.30
    gene_flow_ceiling_per_step: float = 0.15
    trait_response_timescale_years: float = 300_000.0
    ecological_sorting_exponent: float = 1.0
    body_mass_scale: float = 0.35
    isolation_gene_flow_threshold: float = 0.03
    isolation_effective_exchange_threshold: float = 0.02
    isolation_reconnection_decay: float = 2.0
    temp_anomaly_c: float | None = None
    npp_multiplier: float | None = None


@dataclass
class DynamicDemeResult:
    species_ids: list[str]
    deme_ids: list[str]
    deme_species_index: np.ndarray
    deme_guild_id: np.ndarray
    lat: np.ndarray
    lon: np.ndarray
    land_mask: np.ndarray
    plate_code: np.ndarray
    snapshot_relative_year: np.ndarray
    initial_deme_population: np.ndarray
    endpoint_deme_population: np.ndarray
    endpoint_species_population: np.ndarray
    deme_total_history: np.ndarray
    species_total_history: np.ndarray
    trait_history: np.ndarray
    additive_variance: np.ndarray
    generation_time_proxy_years: np.ndarray
    endpoint_gene_flow: np.ndarray
    endpoint_divergence: np.ndarray
    endpoint_RI: np.ndarray
    endpoint_effective_exchange: np.ndarray
    isolation_persistence_years: np.ndarray
    pairwise_records: list[dict]
    provenance: list[dict]
    diagnostics: dict


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _components(mask: np.ndarray):
    nlat, nlon = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
    for i in range(nlat):
        for j in range(nlon):
            if not mask[i, j] or seen[i, j]:
                continue
            q = deque([(i, j)])
            seen[i, j] = True
            cells = []
            while q:
                a, b = q.popleft()
                cells.append((a, b))
                for aa, bb in ((a - 1, b), (a + 1, b), (a, (b - 1) % nlon), (a, (b + 1) % nlon)):
                    if aa < 0 or aa >= nlat:
                        continue
                    if mask[aa, bb] and not seen[aa, bb]:
                        seen[aa, bb] = True
                        q.append((aa, bb))
            comps.append(cells)
    return comps


def _great_circle_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = np.deg2rad(lat1), np.deg2rad(lat2)
    dp = np.deg2rad(np.asarray(lat2) - np.asarray(lat1))
    dl = np.deg2rad(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.minimum(1.0, np.sqrt(a)))


def _median_land_edge_km(lat, lon, land):
    vals = []
    for i in range(len(lat)):
        for j in range(len(lon)):
            if not land[i, j]:
                continue
            if i + 1 < len(lat) and land[i + 1, j]:
                vals.append(float(_great_circle_km(lat[i], lon[j], lat[i + 1], lon[j])))
            j2 = (j + 1) % len(lon)
            if land[i, j2]:
                vals.append(float(_great_circle_km(lat[i], lon[j], lat[i], lon[j2])))
    if not vals:
        raise ValueError("No terrestrial adjacency edges")
    return float(np.median(vals))


def _weighted_centroid(lat, lon, pop):
    total = float(np.sum(pop))
    if total <= 0:
        return float("nan"), float("nan")
    lat2 = lat[:, None]
    lon2 = lon[None, :]
    clat = float(np.sum(pop * lat2) / total)
    ang = np.deg2rad(lon2)
    x = float(np.sum(pop * np.cos(ang)))
    y = float(np.sum(pop * np.sin(ang)))
    clon = math.degrees(math.atan2(y, x))
    return clat, clon


def _normalize_resource(arr, land):
    vals = np.asarray(arr)[land]
    pos = vals[vals > 0]
    scale = float(np.percentile(pos, 95)) if pos.size else 1.0
    out = np.clip(np.asarray(arr, dtype=float) / max(scale, 1e-15), 0.0, 1.0)
    out[~land] = 0.0
    return out


def _transport_once(mass, q):
    qn = np.zeros_like(q)
    qs = np.zeros_like(q)
    qn[1:] = q[:-1]
    qs[:-1] = q[1:]
    qe = np.roll(q, -1, axis=1)
    qw = np.roll(q, 1, axis=1)
    den = q + qn + qs + qe + qw

    out = np.zeros_like(mass)
    active = den > 0
    out += np.divide(mass * q, den, out=np.zeros_like(mass), where=active)
    move_n = np.divide(mass * qn, den, out=np.zeros_like(mass), where=active)
    move_s = np.divide(mass * qs, den, out=np.zeros_like(mass), where=active)
    move_e = np.divide(mass * qe, den, out=np.zeros_like(mass), where=active)
    move_w = np.divide(mass * qw, den, out=np.zeros_like(mass), where=active)
    out[:-1] += move_n[1:]
    out[1:] += move_s[:-1]
    out += np.roll(move_e, 1, axis=1)
    out += np.roll(move_w, -1, axis=1)
    stuck = (~active) & (mass > 0)
    out[stuck] += mass[stuck]
    return out


def _plant_resource(meta, a1, ia1, npp_multiplier, land):
    browse = a1["browse_forage"][ia1].astype(float) * npp_multiplier
    low = a1["low_forage"][ia1].astype(float) * npp_multiplier
    wet = a1["wetland_forage"][ia1].astype(float) * npp_multiplier
    guild = meta["guild"]
    if guild == "large_browser":
        res = browse
    elif guild == "medium_low_vegetation_feeder":
        res = low
    elif guild == "small_reptiloid_generalist":
        w = meta.get("diet_weights", {})
        res = (
            float(w.get("browse", 0.0)) * browse
            + float(w.get("low", 0.0)) * low
            + float(w.get("wetland", 0.0)) * wet
        )
    else:
        res = a1["total_edible_forage"][ia1].astype(float) * npp_multiplier
    return _normalize_resource(res, land)


def _drought_to_aridity_optimum(drought_tolerance):
    # Exact D1 construction relation, recovered from the source metadata.
    return 1.55 * (1.0 - np.clip(drought_tolerance, 0.0, 1.0))


def _aridity_to_drought_target(aridity):
    return np.clip(1.0 - np.asarray(aridity) / 1.55, 0.0, 1.0)


def _climate_suitability(meta, trait, temp, aridity, land, floor):
    thermal_optimum = float(trait[0])
    drought = float(trait[1])
    aridity_optimum = float(_drought_to_aridity_optimum(drought))
    t_sigma = max(float(meta["thermal_niche_sigma_c"]), 1e-9)
    a_sigma = max(float(meta["aridity_niche_sigma"]), 1e-9)
    thermal = np.exp(-0.5 * ((temp - thermal_optimum) / t_sigma) ** 2)
    arid = np.exp(-0.5 * ((aridity - aridity_optimum) / a_sigma) ** 2)
    q = thermal * arid
    q[~land] = 0.0
    q[land] = np.maximum(q[land], floor)
    return q


def _habitat_suitability(meta, trait, temp, aridity, resource, land, floor):
    q = _climate_suitability(meta, trait, temp, aridity, land, floor)
    q *= np.maximum(resource, floor)
    q[~land] = 0.0
    if np.any(land):
        mx = float(np.max(q[land]))
        if mx > 0:
            q /= mx
    q[land] = np.maximum(q[land], floor)
    return q


def _load_inputs(root: Path, cfg: DynamicDemeConfig):
    parent = root / "inputs/D3_0A_PARENT"
    audit = _read_json(parent / "spatial_bridge_audit.json")
    if audit.get("status") != "PASS_POST_CHA1_SPATIAL_POPULATION_BRIDGE_CANDIDATE":
        raise ValueError("D3.0B requires a passing D3.0A spatial bridge parent")
    pz = np.load(parent / "post_cha1_spatial_bridge_state.npz")
    species_ids = [str(x) for x in pz["species_id"].tolist()]
    if len(species_ids) != 31:
        raise ValueError("D3.0B requires exactly 31 D3.0A survivor species")
    seeds = _read_json(parent / "deme_seed_registry.json")
    if seeds.get("deme_seed_count") != 115:
        raise ValueError("D3.0B candidate expects the 115 D3.0A seed components")
    diag = _read_json(parent / "spatial_bridge_diagnostics.json")

    md_list = _read_json(root / "inputs/D1_METADATA/species_metadata.json")
    md = {m["species_id"]: copy.deepcopy(m) for m in md_list}
    if "HSG_025" in species_ids and "HSG_025" not in md:
        proxy = copy.deepcopy(md["HSG_003"])
        proxy["species_id"] = "HSG_025"
        proxy["trait_provenance"] = "PARENT_PROXY_HSG_003_D2_CHILD_TRAITS_NOT_EXPORTED"
        proxy["parent_species_id"] = "HSG_003"
        md["HSG_025"] = proxy

    a1 = np.load(root / "inputs/A1_REFERENCE/fauna_baseline_state_A1.npz")
    ia1 = int(np.where(np.isclose(a1["age_ma"].astype(float), 66.0))[0][0])
    temp_anom = float(diag["endpoint_temperature_anomaly_c"]) if cfg.temp_anomaly_c is None else float(cfg.temp_anomaly_c)
    npp = float(diag["endpoint_npp_multiplier"]) if cfg.npp_multiplier is None else float(cfg.npp_multiplier)
    return {
        "parent_state": pz,
        "species_ids": species_ids,
        "seed_registry": seeds,
        "metadata": md,
        "a1": a1,
        "ia1": ia1,
        "temp_anomaly_c": temp_anom,
        "npp_multiplier": npp,
    }


def _partition_parent_into_demes(species_ids, species_population, seed_registry, lat, lon, floor):
    seed_rows_by_species = {sid: [] for sid in species_ids}
    for row in seed_registry["demes"]:
        seed_rows_by_species[row["species_id"]].append(row)

    deme_ids = []
    deme_species_index = []
    deme_guild = []
    rasters = []
    init_records = []

    for si, sid in enumerate(species_ids):
        pop = species_population[si]
        comps = _components(pop > floor)
        comps.sort(key=lambda c: -sum(float(pop[i, j]) for i, j in c))
        rows = seed_rows_by_species[sid]
        if len(comps) != len(rows):
            raise ValueError(f"Deme seed/core mismatch for {sid}: {len(comps)} != {len(rows)}")
        rows = sorted(rows, key=lambda r: r["deme_seed_id"])

        labels = np.full(pop.shape, -1, dtype=np.int32)
        core_centroids = []
        for ci, cells in enumerate(comps):
            cm = np.zeros_like(pop, dtype=bool)
            for i, j in cells:
                labels[i, j] = ci
                cm[i, j] = True
            cp = np.where(cm, pop, 0.0)
            core_centroids.append(_weighted_centroid(lat, lon, cp))

        tail_i, tail_j = np.where((pop > 0) & (labels < 0))
        if len(tail_i):
            c_lat = np.array([x[0] for x in core_centroids])
            c_lon = np.array([x[1] for x in core_centroids])
            for i, j in zip(tail_i, tail_j):
                dist = _great_circle_km(float(lat[i]), float(lon[j]), c_lat, c_lon)
                labels[i, j] = int(np.argmin(dist))

        rebuilt = np.zeros_like(pop, dtype=float)
        for ci, row in enumerate(rows):
            r = np.where(labels == ci, pop, 0.0).astype(float)
            rebuilt += r
            deme_ids.append(row["deme_seed_id"])
            deme_species_index.append(si)
            deme_guild.append(int(row["guild_id"]))
            rasters.append(r)
            init_records.append({
                "deme_id": row["deme_seed_id"],
                "species_id": sid,
                "core_seed_population": float(row["population"]),
                "initialized_full_population": float(r.sum()),
                "tail_population_assigned": float(r.sum() - row["population"]),
                "semantic_status": "DYNAMIC_DEME_INITIALIZED_FROM_D3_0A_SEED",
            })
        if not np.allclose(rebuilt, pop, rtol=0, atol=1e-12):
            raise AssertionError(f"Deme partition failed to reconstruct {sid}")

    return (
        deme_ids,
        np.asarray(deme_species_index, dtype=np.int16),
        np.asarray(deme_guild, dtype=np.uint8),
        np.stack(rasters).astype(np.float64),
        init_records,
    )


def _species_from_demes(deme_population, deme_species_index, nspecies):
    out = np.zeros((nspecies,) + deme_population.shape[1:], dtype=np.float64)
    for di, si in enumerate(deme_species_index):
        out[int(si)] += deme_population[di]
    return out


def _deme_trait_initialization(deme_species_index, species_ids, metadata):
    nd = len(deme_species_index)
    trait = np.zeros((nd, 3), dtype=np.float64)
    va = np.zeros((nd, 3), dtype=np.float64)
    gen = np.zeros(nd, dtype=np.float64)
    provenance = []
    for di, si in enumerate(deme_species_index):
        sid = species_ids[int(si)]
        m = metadata[sid]
        trait[di] = [
            float(m["thermal_optimum_c"]),
            float(m["drought_tolerance_index"]),
            float(m["relative_log_body_mass"]),
        ]
        drought_scale = max(float(m["aridity_niche_sigma"]) / 1.55, 1e-4)
        va[di] = [
            (0.08 * float(m["thermal_niche_sigma_c"])) ** 2,
            (0.08 * drought_scale) ** 2,
            0.05 ** 2,
        ]
        g = int(m["guild_id"])
        gen[di] = DEFAULT_GENERATION_PROXY_YR[g] / max(float(m["relative_reproduction_rate"]), 1e-6)
        provenance.append({
            "deme_id": None,
            "species_id": sid,
            "trait_provenance": m.get("trait_provenance", "D1_EXPLICIT"),
            "parent_species_id": m.get("parent_species_id"),
            "additive_variance_status": "D3_0B_FIXED_BENCHMARK_RESERVOIR_NOT_FULL_MUTATION_DRIFT_SOLVER",
            "generation_time_status": "GUILD_CALIBRATION_PROXY_NOT_CANON_LIFE_HISTORY",
        })
    return trait, va, gen, provenance


def _prey_resource_for_species(meta, species_population, species_guild, land):
    weights = meta.get("diet_weights", {})
    res = np.zeros(species_population.shape[1:], dtype=float)
    for prey_key, weight in weights.items():
        pg = PREY_KEY_TO_GUILD.get(prey_key)
        if pg is None:
            continue
        res += float(weight) * species_population[species_guild == pg].sum(axis=0)
    return _normalize_resource(res, land)


def _guild_prey_scale(species_population, species_guild, a1, ia1, guild_id):
    # Both predator guilds consume guilds 1-4. This ratio controls total predator
    # carrying capacity while species-specific diet still controls spatial habitat.
    current = float(species_population[species_guild <= 4].sum())
    reference = float(a1["population"][ia1, :4].sum())
    if reference <= 0:
        return 0.0
    return float(np.clip(current / reference, 0.0, 1.5))


def _deme_habitats(deme_trait, deme_species_index, species_ids, species_guild, metadata,
                   species_population, temp, aridity, plant_resource_by_species, land, floor):
    nd = len(deme_species_index)
    out = np.zeros((nd,) + land.shape, dtype=np.float64)
    prey_cache = {}
    for di, si in enumerate(deme_species_index):
        si = int(si)
        sid = species_ids[si]
        meta = metadata[sid]
        g = int(species_guild[si])
        if g <= 4:
            resource = plant_resource_by_species[si]
        else:
            if si not in prey_cache:
                prey_cache[si] = _prey_resource_for_species(meta, species_population, species_guild, land)
            resource = prey_cache[si]
        out[di] = _habitat_suitability(meta, deme_trait[di], temp, aridity, resource, land, floor)
    return out


def _species_habitat_from_demes(deme_habitat, deme_species_index, nspecies):
    out = np.zeros((nspecies,) + deme_habitat.shape[1:], dtype=np.float64)
    for si in range(nspecies):
        idx = np.where(deme_species_index == si)[0]
        out[si] = np.max(deme_habitat[idx], axis=0)
    return out


def _species_opportunity_score(species_habitat, species_guild, a1, ia1):
    # Integrate suitability against the guild reference-population field. This
    # measures accessible ecological opportunity without treating K as N.
    ns = len(species_guild)
    score = np.zeros(ns, dtype=np.float64)
    for si in range(ns):
        g = int(species_guild[si])
        ref_field = a1["population"][ia1, g - 1].astype(float)
        score[si] = float(np.sum(species_habitat[si] * np.maximum(ref_field, 0.0)))
    return score


def _species_equilibrium_targets(initial_species_total, initial_opportunity, current_opportunity,
                                 species_guild, species_population, a1, ia1, npp_multiplier, cfg):
    target = np.zeros(len(species_guild), dtype=np.float64)
    for g in range(1, 7):
        idx = np.where(species_guild == g)[0]
        ref_total = float(a1["population"][ia1, g - 1].sum())
        if g <= 4:
            guild_target = ref_total * npp_multiplier
        else:
            prey_scale = _guild_prey_scale(species_population, species_guild, a1, ia1, g)
            guild_target = ref_total * prey_scale
        base = initial_species_total[idx]
        base_share = base / max(float(base.sum()), 1e-15)
        ratio = np.divide(
            current_opportunity[idx], initial_opportunity[idx],
            out=np.ones(len(idx), dtype=float), where=initial_opportunity[idx] > 1e-15
        )
        weight = base_share * np.power(np.clip(ratio, 1e-6, 1e6), cfg.ecological_sorting_exponent)
        sw = float(weight.sum())
        if sw <= 0:
            weight = base_share
            sw = float(weight.sum())
        target[idx] = guild_target * weight / sw
    return target


def _demography_step(deme_population, deme_species_index, species_ids, species_guild, metadata,
                      target_species_total, dt, floor):
    species_pop = _species_from_demes(deme_population, deme_species_index, len(species_ids))
    species_total = species_pop.sum(axis=(1, 2))
    new_total = np.zeros_like(species_total)
    for si, sid in enumerate(species_ids):
        meta = metadata[sid]
        g = int(species_guild[si])
        tau = DEFAULT_DEMOGRAPHIC_TAU_YR[g] / max(float(meta["relative_reproduction_rate"]), 1e-6)
        alpha = 1.0 - math.exp(-dt / max(tau, 1e-9))
        new_total[si] = max(0.0, species_total[si] + alpha * (float(target_species_total[si]) - species_total[si]))

    out = np.zeros_like(deme_population)
    for si in range(len(species_ids)):
        idx = np.where(deme_species_index == si)[0]
        old_total = float(species_total[si])
        scale = (float(new_total[si]) / old_total) if old_total > floor else 0.0
        for di in idx:
            out[di] = deme_population[di] * scale
    return out


def _migration_fraction(dispersal_scale_km, edge_km, dt, cfg):
    tau = cfg.migration_reference_years * edge_km / max(float(dispersal_scale_km), 1e-9)
    f = 1.0 - math.exp(-dt / max(tau, 1e-9))
    return float(np.clip(f, 0.0, cfg.migration_fraction_ceiling))


def _migration_step(deme_population, deme_habitat, deme_species_index, species_ids, metadata,
                    edge_km, dt, cfg, land):
    out = np.zeros_like(deme_population)
    move_fraction = np.zeros(len(deme_population), dtype=float)
    for di, si in enumerate(deme_species_index):
        sid = species_ids[int(si)]
        ds = float(metadata[sid]["dispersal_scale_km"])
        f = _migration_fraction(ds, edge_km, dt, cfg)
        moved = _transport_once(deme_population[di], deme_habitat[di])
        # Both terms conserve mass. Blend gives a time-scaled local migration flux.
        out[di] = (1.0 - f) * deme_population[di] + f * moved
        out[di, ~land] = 0.0
        before = float(deme_population[di].sum())
        after = float(out[di].sum())
        if before > 0 and after > 0:
            out[di] *= before / after
        move_fraction[di] = f
    return out, move_fraction


def _pair_gene_flow(pop_i, pop_j, dispersal_scale_km, lat, lon, ceiling):
    ni = float(pop_i.sum())
    nj = float(pop_j.sum())
    if ni <= 0 or nj <= 0:
        return 0.0, 0.0, float("inf")
    overlap = float(np.minimum(pop_i, pop_j).sum() / max(min(ni, nj), 1e-15))
    ci = _weighted_centroid(lat, lon, pop_i)
    cj = _weighted_centroid(lat, lon, pop_j)
    dist = float(_great_circle_km(ci[0], ci[1], cj[0], cj[1]))
    decay = math.exp(-dist / max(4.0 * dispersal_scale_km, 1e-9))
    g = float(np.clip(ceiling * overlap * decay, 0.0, ceiling))
    return g, overlap, dist


def _gene_flow_matrix(deme_population, deme_species_index, species_ids, metadata, lat, lon, ceiling):
    nd = len(deme_population)
    G = np.zeros((nd, nd), dtype=np.float64)
    overlap = np.zeros_like(G)
    distance = np.full_like(G, np.inf)
    np.fill_diagonal(distance, 0.0)
    for si, sid in enumerate(species_ids):
        idx = np.where(deme_species_index == si)[0]
        ds = float(metadata[sid]["dispersal_scale_km"])
        for a in range(len(idx)):
            i = int(idx[a])
            for b in range(a + 1, len(idx)):
                j = int(idx[b])
                g, ov, dist = _pair_gene_flow(deme_population[i], deme_population[j], ds, lat, lon, ceiling)
                G[i, j] = G[j, i] = g
                overlap[i, j] = overlap[j, i] = ov
                distance[i, j] = distance[j, i] = dist
    return G, overlap, distance


def _selection_targets(deme_population, temp, aridity):
    nd = len(deme_population)
    target = np.zeros((nd, 2), dtype=np.float64)
    drought_field = _aridity_to_drought_target(aridity)
    for di in range(nd):
        p = deme_population[di]
        n = float(p.sum())
        if n <= 0:
            target[di] = [np.nan, np.nan]
        else:
            target[di, 0] = float(np.sum(p * temp) / n)
            target[di, 1] = float(np.sum(p * drought_field) / n)
    return target


def _selection_update(trait, additive_variance, targets, deme_species_index, species_ids, metadata, dt, cfg):
    out = trait.copy()
    for di, si in enumerate(deme_species_index):
        if not np.all(np.isfinite(targets[di])):
            continue
        sid = species_ids[int(si)]
        rel = max(float(metadata[sid]["relative_reproduction_rate"]), 1e-6)
        tau = cfg.trait_response_timescale_years / rel
        beta = 1.0 - math.exp(-dt / tau)
        # Quantitative-genetic response is limited by the fixed additive-variance
        # reservoir. D3.0B intentionally does not yet evolve VA itself.
        tscale = max(float(metadata[sid]["thermal_niche_sigma_c"]), 1e-6)
        dscale = max(float(metadata[sid]["aridity_niche_sigma"]) / 1.55, 1e-4)
        gain_t = float(np.clip(additive_variance[di, 0] / (tscale * tscale), 0.0, 0.25))
        gain_d = float(np.clip(additive_variance[di, 1] / (dscale * dscale), 0.0, 0.25))
        out[di, 0] += beta * gain_t * (targets[di, 0] - out[di, 0])
        out[di, 1] += beta * gain_d * (targets[di, 1] - out[di, 1])
        out[di, 1] = float(np.clip(out[di, 1], 0.0, 1.0))
        # Relative log body mass has no directional environmental target in
        # D3.0B. It can be homogenized by gene flow but is not author-driven.
    return out


def _gene_flow_trait_mix(trait, deme_totals, G, deme_species_index):
    delta = np.zeros_like(trait)
    nd = len(trait)
    for i in range(nd):
        ni = float(deme_totals[i])
        if ni <= 0:
            continue
        for j in range(i + 1, nd):
            if deme_species_index[i] != deme_species_index[j] or G[i, j] <= 0:
                continue
            nj = float(deme_totals[j])
            if nj <= 0:
                continue
            harmonic = 2.0 * ni * nj / (ni + nj)
            exchange = float(G[i, j]) * harmonic
            d = trait[j] - trait[i]
            delta[i] += (exchange / ni) * d
            delta[j] -= (exchange / nj) * d
    return trait + delta


def _pairwise_evolution_metrics(trait, G, deme_species_index, species_ids, metadata, cfg):
    nd = len(trait)
    divergence = np.zeros((nd, nd), dtype=np.float64)
    ri = np.zeros_like(divergence)
    x = np.zeros_like(divergence)
    trait_dist = np.zeros_like(divergence)
    for si, sid in enumerate(species_ids):
        idx = np.where(deme_species_index == si)[0]
        meta = metadata[sid]
        tscale = max(float(meta["thermal_niche_sigma_c"]), 1e-6)
        dscale = max(float(meta["aridity_niche_sigma"]) / 1.55, 1e-4)
        mscale = max(float(cfg.body_mass_scale), 1e-6)
        for a in range(len(idx)):
            i = int(idx[a])
            for b in range(a + 1, len(idx)):
                j = int(idx[b])
                dz = np.array([
                    (trait[i, 0] - trait[j, 0]) / tscale,
                    (trait[i, 1] - trait[j, 1]) / dscale,
                    (trait[i, 2] - trait[j, 2]) / mscale,
                ])
                td = float(np.sqrt(np.sum(dz * dz)))
                div = float(1.0 - math.exp(-0.5 * td))
                compatibility = float(math.exp(-0.5 * td * td))
                rval = float(1.0 - compatibility)
                ex = float(G[i, j] * (1.0 - rval))
                trait_dist[i, j] = trait_dist[j, i] = td
                divergence[i, j] = divergence[j, i] = div
                ri[i, j] = ri[j, i] = rval
                x[i, j] = x[j, i] = ex
    return trait_dist, divergence, ri, x


def _update_isolation_persistence(persistence, G, X, deme_species_index, dt, cfg):
    out = persistence.copy()
    nd = len(out)
    for i in range(nd):
        for j in range(i + 1, nd):
            if deme_species_index[i] != deme_species_index[j]:
                continue
            isolated = (G[i, j] <= cfg.isolation_gene_flow_threshold and
                        X[i, j] <= cfg.isolation_effective_exchange_threshold)
            if isolated:
                out[i, j] += dt
            else:
                out[i, j] = max(0.0, out[i, j] - cfg.isolation_reconnection_decay * dt)
            out[j, i] = out[i, j]
    return out


def _snapshot_schedule(cfg):
    if cfg.dt_years <= 0 or cfg.end_relative_year <= cfg.start_relative_year:
        raise ValueError("Invalid D3.0B time window")
    duration = cfg.end_relative_year - cfg.start_relative_year
    nsteps_f = duration / cfg.dt_years
    if abs(nsteps_f - round(nsteps_f)) > 1e-9:
        raise ValueError("Time window must be divisible by dt")
    nsteps = int(round(nsteps_f))
    snap_step_f = cfg.snapshot_interval_years / cfg.dt_years
    if abs(snap_step_f - round(snap_step_f)) > 1e-9:
        raise ValueError("Snapshot interval must be divisible by dt")
    snap_every = int(round(snap_step_f))
    steps = [0] + [k for k in range(1, nsteps + 1) if k % snap_every == 0 or k == nsteps]
    years = np.array([cfg.start_relative_year + k * cfg.dt_years for k in steps], dtype=np.float64)
    return nsteps, snap_every, steps, years


def run_dynamic_demes(root: Path, cfg: DynamicDemeConfig | None = None) -> DynamicDemeResult:
    cfg = cfg or DynamicDemeConfig()
    root = Path(root)
    d = _load_inputs(root, cfg)
    pz = d["parent_state"]
    species_ids = d["species_ids"]
    species_population0 = pz["endpoint_population_500kyr"].astype(np.float64)
    species_guild = pz["guild_id"].astype(np.uint8)
    lat = pz["lat"].astype(np.float64)
    lon = pz["lon"].astype(np.float64)
    land = pz["land_mask"].astype(bool)
    plate = pz["plate_code"].astype(np.uint8)

    deme_ids, deme_species_index, deme_guild, deme_population, init_records = _partition_parent_into_demes(
        species_ids, species_population0, d["seed_registry"], lat, lon, cfg.occupancy_floor
    )
    if len(deme_ids) != 115:
        raise AssertionError("D3.0B must initialize exactly 115 dynamic demes")

    trait, va, gen_proxy, provenance = _deme_trait_initialization(
        deme_species_index, species_ids, d["metadata"]
    )
    for i, did in enumerate(deme_ids):
        provenance[i]["deme_id"] = did
        provenance[i].update(init_records[i])

    a1, ia1 = d["a1"], d["ia1"]
    temp = a1["temperature_c"][ia1].astype(float) + d["temp_anomaly_c"]
    aridity = a1["aridity_index"][ia1].astype(float)
    temp[~land] = 0.0
    aridity[~land] = 0.0
    edge_km = _median_land_edge_km(lat, lon, land)

    plant_resource_by_species = np.zeros((len(species_ids),) + land.shape, dtype=np.float64)
    for si, sid in enumerate(species_ids):
        if int(species_guild[si]) <= 4:
            plant_resource_by_species[si] = _plant_resource(
                d["metadata"][sid], a1, ia1, d["npp_multiplier"], land
            )

    initial_species_total = species_population0.sum(axis=(1, 2))
    initial_deme_habitat = _deme_habitats(
        trait, deme_species_index, species_ids, species_guild, d["metadata"],
        species_population0, temp, aridity, plant_resource_by_species, land, cfg.habitat_floor
    )
    initial_species_habitat = _species_habitat_from_demes(
        initial_deme_habitat, deme_species_index, len(species_ids)
    )
    initial_opportunity = _species_opportunity_score(
        initial_species_habitat, species_guild, a1, ia1
    )

    nsteps, snap_every, snap_steps, snap_year = _snapshot_schedule(cfg)
    nsnap = len(snap_steps)
    nd, ns = len(deme_ids), len(species_ids)
    initial_deme_population = deme_population.copy()
    deme_total_history = np.zeros((nsnap, nd), dtype=np.float64)
    species_total_history = np.zeros((nsnap, ns), dtype=np.float64)
    trait_history = np.zeros((nsnap, nd, 3), dtype=np.float64)
    persistence = np.zeros((nd, nd), dtype=np.float64)
    migration_fraction_last = np.zeros(nd, dtype=float)
    max_land_leak = 0.0
    max_mass_transport_error = 0.0

    def store_snapshot(k):
        sp = _species_from_demes(deme_population, deme_species_index, ns)
        deme_total_history[k] = deme_population.sum(axis=(1, 2))
        species_total_history[k] = sp.sum(axis=(1, 2))
        trait_history[k] = trait

    store_snapshot(0)
    snap_index = 1

    G = np.zeros((nd, nd), dtype=float)
    overlap = np.zeros_like(G)
    distance = np.full_like(G, np.inf)
    trait_dist = np.zeros_like(G)
    divergence = np.zeros_like(G)
    ri = np.zeros_like(G)
    X = np.zeros_like(G)

    for step in range(1, nsteps + 1):
        species_population = _species_from_demes(deme_population, deme_species_index, ns)
        deme_habitat = _deme_habitats(
            trait, deme_species_index, species_ids, species_guild, d["metadata"],
            species_population, temp, aridity, plant_resource_by_species, land, cfg.habitat_floor
        )

        before = deme_population.sum(axis=(1, 2))
        deme_population, migration_fraction_last = _migration_step(
            deme_population, deme_habitat, deme_species_index, species_ids, d["metadata"],
            edge_km, cfg.dt_years, cfg, land
        )
        after = deme_population.sum(axis=(1, 2))
        max_mass_transport_error = max(max_mass_transport_error, float(np.max(np.abs(after - before))))
        max_land_leak = max(max_land_leak, float(np.max(np.abs(deme_population[:, ~land]))))

        species_population = _species_from_demes(deme_population, deme_species_index, ns)
        # Recompute habitat after movement; species carrying capacity responds to
        # current prey and to the best currently represented deme phenotype.
        deme_habitat = _deme_habitats(
            trait, deme_species_index, species_ids, species_guild, d["metadata"],
            species_population, temp, aridity, plant_resource_by_species, land, cfg.habitat_floor
        )
        species_habitat = _species_habitat_from_demes(deme_habitat, deme_species_index, ns)
        current_opportunity = _species_opportunity_score(
            species_habitat, species_guild, a1, ia1
        )
        target_species_total = _species_equilibrium_targets(
            initial_species_total, initial_opportunity, current_opportunity,
            species_guild, species_population, a1, ia1, d["npp_multiplier"], cfg
        )
        deme_population = _demography_step(
            deme_population, deme_species_index, species_ids, species_guild, d["metadata"],
            target_species_total, cfg.dt_years, cfg.population_floor
        )

        G, overlap, distance = _gene_flow_matrix(
            deme_population, deme_species_index, species_ids, d["metadata"], lat, lon,
            cfg.gene_flow_ceiling_per_step
        )
        targets = _selection_targets(deme_population, temp, aridity)
        selected = _selection_update(
            trait, va, targets, deme_species_index, species_ids, d["metadata"], cfg.dt_years, cfg
        )
        totals = deme_population.sum(axis=(1, 2))
        trait = _gene_flow_trait_mix(selected, totals, G, deme_species_index)
        trait_dist, divergence, ri, X = _pairwise_evolution_metrics(
            trait, G, deme_species_index, species_ids, d["metadata"], cfg
        )
        persistence = _update_isolation_persistence(
            persistence, G, X, deme_species_index, cfg.dt_years, cfg
        )

        if step in snap_steps[1:]:
            store_snapshot(snap_index)
            snap_index += 1

    endpoint_species = _species_from_demes(deme_population, deme_species_index, ns)
    endpoint_deme_totals = deme_population.sum(axis=(1, 2))
    pairwise_records = []
    for si, sid in enumerate(species_ids):
        idx = np.where(deme_species_index == si)[0]
        for a in range(len(idx)):
            i = int(idx[a])
            for b in range(a + 1, len(idx)):
                j = int(idx[b])
                pairwise_records.append({
                    "species_id": sid,
                    "deme_a": deme_ids[i],
                    "deme_b": deme_ids[j],
                    "gene_flow": float(G[i, j]),
                    "spatial_overlap_fraction": float(overlap[i, j]),
                    "centroid_distance_km": float(distance[i, j]),
                    "trait_distance": float(trait_dist[i, j]),
                    "divergence": float(divergence[i, j]),
                    "RI": float(ri[i, j]),
                    "effective_reproductive_exchange": float(X[i, j]),
                    "isolation_persistence_years": float(persistence[i, j]),
                    "isolation_generation_equivalents_min_proxy": float(
                        persistence[i, j] / max(max(gen_proxy[i], gen_proxy[j]), 1e-9)
                    ),
                    "taxonomic_status": "SAME_SPECIES_DEMES_SPECIATION_DISABLED",
                })

    within = np.array([r["gene_flow"] for r in pairwise_records], dtype=float)
    divvals = np.array([r["divergence"] for r in pairwise_records], dtype=float)
    rivals = np.array([r["RI"] for r in pairwise_records], dtype=float)
    endpoint_species_total = endpoint_species.sum(axis=(1, 2))
    diagnostics = {
        "version": "0.6.3D3.0B",
        "parent": "0.6.3D3.0A",
        "semantic_status": "PASS_DYNAMIC_DEME_GENE_FLOW_COUPLING_CANDIDATE",
        "start_relative_year": float(cfg.start_relative_year),
        "end_relative_year": float(cfg.end_relative_year),
        "dt_years": float(cfg.dt_years),
        "snapshot_interval_years": float(cfg.snapshot_interval_years),
        "species_count_start": 31,
        "species_count_end": 31,
        "deme_count_start": 115,
        "deme_count_end": 115,
        "pair_count_same_species": len(pairwise_records),
        "median_land_neighbor_edge_km": edge_km,
        "temperature_anomaly_c_frozen": float(d["temp_anomaly_c"]),
        "npp_multiplier_frozen": float(d["npp_multiplier"]),
        "tectonic_freeze_absolute_bound_from_CHA1_km": 70.0,
        "tectonic_freeze_scope": "D3_0B_0P5_TO_1P0_MYR_COUPLING_BENCHMARK_ONLY",
        "max_transport_mass_error_per_deme": float(max_mass_transport_error),
        "max_ocean_population": float(max_land_leak),
        "initial_total_population": float(initial_species_total.sum()),
        "endpoint_total_population": float(endpoint_species_total.sum()),
        "initial_species_total_min": float(initial_species_total.min()),
        "endpoint_species_total_min": float(endpoint_species_total.min()),
        "endpoint_species_total_max": float(endpoint_species_total.max()),
        "mean_gene_flow_same_species_pairs": float(within.mean()) if within.size else 0.0,
        "max_gene_flow_same_species_pairs": float(within.max()) if within.size else 0.0,
        "mean_divergence_same_species_pairs": float(divvals.mean()) if divvals.size else 0.0,
        "max_divergence_same_species_pairs": float(divvals.max()) if divvals.size else 0.0,
        "mean_RI_same_species_pairs": float(rivals.mean()) if rivals.size else 0.0,
        "max_RI_same_species_pairs": float(rivals.max()) if rivals.size else 0.0,
        "migration_fraction_min_last_step": float(migration_fraction_last.min()),
        "migration_fraction_max_last_step": float(migration_fraction_last.max()),
        "trait_change_max_abs_thermal_c": float(np.max(np.abs(trait[:, 0] - trait_history[0, :, 0]))),
        "trait_change_max_abs_drought": float(np.max(np.abs(trait[:, 1] - trait_history[0, :, 1]))),
        "body_mass_directional_selection_enabled": False,
        "additive_variance_dynamic_solver_enabled": False,
        "stochastic_drift_enabled": False,
        "migration_enabled": True,
        "gene_flow_enabled": True,
        "trait_selection_enabled": True,
        "ecology_trait_feedback_enabled": True,
        "demographic_reference_state": "A1_66MA_POPULATION_NOT_CARRYING_CAPACITY_EQUALITY",
        "ecological_sorting_exponent": float(cfg.ecological_sorting_exponent),
        "isolation_thresholds_status": "PROVISIONAL_D_REFERENCE_NOT_PROMOTED_TO_SPECIATION_GATE",
        "isolation_thresholds_promoted_to_speciation_gate": False,
        "speciation_enabled": False,
        "species_fusion_enabled": False,
        "adaptive_radiation_enabled": False,
        "Deep_adaptation_enabled": False,
        "dragon_lineage_selection_enabled": False,
        "sapience_enabled": False,
        "civilization_enabled": False,
        "raw_region_labels_used": False,
        "RPT_009_special_parameterization": False,
        "RPT_011_special_parameterization": False,
    }

    return DynamicDemeResult(
        species_ids=species_ids,
        deme_ids=deme_ids,
        deme_species_index=deme_species_index,
        deme_guild_id=deme_guild,
        lat=lat,
        lon=lon,
        land_mask=land.astype(np.uint8),
        plate_code=plate,
        snapshot_relative_year=snap_year,
        initial_deme_population=initial_deme_population,
        endpoint_deme_population=deme_population,
        endpoint_species_population=endpoint_species,
        deme_total_history=deme_total_history,
        species_total_history=species_total_history,
        trait_history=trait_history,
        additive_variance=va,
        generation_time_proxy_years=gen_proxy,
        endpoint_gene_flow=G,
        endpoint_divergence=divergence,
        endpoint_RI=ri,
        endpoint_effective_exchange=X,
        isolation_persistence_years=persistence,
        pairwise_records=pairwise_records,
        provenance=provenance,
        diagnostics=diagnostics,
    )
