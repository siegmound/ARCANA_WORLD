from __future__ import annotations

from dataclasses import dataclass, asdict
from collections import defaultdict
import math
from typing import Any

import numpy as np
from scipy.sparse import csr_array
from scipy.sparse.csgraph import connected_components

import rebased_natural_control_runtime_v0_6D1_R2 as r2
import d3_speciation_gate_v0_6_3D3_0C as sg

R21_STAGE_ID = "v0.6D1-R2.1"
R21_SCOPE = "GOVERNED_SPECIATION_EXTINCTION_ACTUATOR_AND_INTERNAL_CADENCE_CLOSURE"
R21_SPECIATION_BIRTH_ACTUATOR_AUTHORIZED = True
R21_DEEP_BIOLOGICAL_COUPLING_ENABLED = False
R21_GLOBAL_SPECIATION_RATE = None
R21_GLOBAL_EXTINCTION_RATE = None


@dataclass(frozen=True)
class R21Config(r2.R2Config):
    # External chunking can change checkpoint/output grouping only. Biology is
    # always advanced on the absolute internal cadence below.
    dt_years: float = 125_000.0  # compatibility alias = biology cadence
    macrostep_years: float = 500_000.0
    biology_cadence_years: float = 125_000.0
    transport_cadence_years: float = 62_500.0
    snapshot_interval_years: float = 1_000_000.0

    # D3.1A / D3.2B demographic-fragment semantics. The actuator is implemented
    # and tested, but remains OFF in the R2.1 210->180 production pilot because
    # that pilot has only two paleogeographic keyframes (210/180 Ma). R3 may turn
    # it ON once the full deep-time barrier-history provider is bound.
    persistent_vicariance_fission_enabled: bool = False
    deme_fission_check_interval_years: float = 500_000.0
    deme_fission_min_component_fraction: float = 0.02
    deme_fission_min_absolute_population: float = 0.01
    deme_fission_min_root_species_fraction: float = 0.01
    vicariance_persistence_min_years: float = 2_000_000.0
    vicariance_persistence_reset_on_reconnection: bool = True
    habitat_connectivity_power: float = 0.50
    effective_connectivity_core_threshold: float = 0.05

    # D3.2B founder-lineage viability. No resource-niche axis is invented in R2.1.
    founder_minimum_persistence_years: float = 1_000_000.0
    founder_base_minimum_population_units: float = 0.075
    founder_generation_reference_years: float = 5.0
    founder_reproduction_reference: float = 1.0
    founder_minimum_effective_size_proxy: float = 500.0
    founder_minimum_normalized_additive_variance: float = 0.005
    founder_minimum_occupied_cells: int = 10
    founder_maximum_persistent_decline_fraction: float = 0.50
    founder_reset_on_reconnection: bool = True


def _is_multiple(a: float, b: float, tol: float = 1e-9) -> bool:
    if b <= 0:
        return False
    x = a / b
    return abs(x - round(x)) <= tol * max(1.0, abs(x))


def validate_cadence(cfg: R21Config) -> None:
    vals = [cfg.macrostep_years, cfg.biology_cadence_years, cfg.transport_cadence_years,
            cfg.speciation_check_interval_years, cfg.ordinary_extinction_check_interval_years,
            cfg.deme_fission_check_interval_years, cfg.snapshot_interval_years]
    if any(float(x) <= 0 for x in vals):
        raise ValueError("all cadences must be positive")
    if not _is_multiple(cfg.macrostep_years, cfg.biology_cadence_years):
        raise ValueError("macrostep_years must be an integer multiple of biology_cadence_years")
    if not _is_multiple(cfg.biology_cadence_years, cfg.transport_cadence_years):
        raise ValueError("biology_cadence_years must be an integer multiple of transport_cadence_years")
    for x, name in [
        (cfg.speciation_check_interval_years, "speciation_check_interval_years"),
        (cfg.ordinary_extinction_check_interval_years, "ordinary_extinction_check_interval_years"),
        (cfg.deme_fission_check_interval_years, "deme_fission_check_interval_years"),
        (cfg.snapshot_interval_years, "snapshot_interval_years"),
    ]:
        if not _is_multiple(x, cfg.biology_cadence_years):
            raise ValueError(f"{name} must be an integer multiple of biology_cadence_years")
    duration = (cfg.start_age_ma - cfg.end_age_ma) * 1e6
    if duration <= 0 or not _is_multiple(duration, cfg.biology_cadence_years):
        raise ValueError("simulation duration must be a positive integer multiple of biology cadence")
    if not _is_multiple(duration, cfg.macrostep_years):
        raise ValueError("simulation duration must be an integer number of external macrosteps")


def _pair_key(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


def _root_metadata(root_species: list[str], metadata: dict[str, dict], i: int) -> dict:
    return metadata[root_species[i]]


def _species_component_indices(current_species: list[str], sid: str) -> np.ndarray:
    return np.asarray([i for i, x in enumerate(current_species) if x == sid], dtype=np.int32)


def _root_component_indices(root_species: list[str], root_sid: str) -> np.ndarray:
    return np.asarray([i for i, x in enumerate(root_species) if x == root_sid], dtype=np.int32)


def _current_opportunities(hab: np.ndarray, current_species: list[str], guild: np.ndarray, env: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for sid in sorted(set(current_species)):
        idx = _species_component_indices(current_species, sid)
        if len(idx) == 0:
            continue
        g = int(guild[int(idx[0])])
        h = np.max(hab[idx], axis=0)
        out[sid] = float(np.sum(h * np.maximum(env["reference_population"][g - 1], 0.0)))
    return out


def _occupied_cells(pop: np.ndarray, idx: np.ndarray, floor: float) -> int:
    if len(idx) == 0:
        return 0
    return int(np.count_nonzero(pop[idx].sum(axis=0) > floor))


def _species_totals(pop: np.ndarray, current_species: list[str]) -> dict[str, float]:
    totals = pop.sum(axis=(1, 2))
    return {sid: float(totals[_species_component_indices(current_species, sid)].sum())
            for sid in sorted(set(current_species))}


def _species_generation_time(pop: np.ndarray, gen: np.ndarray, idx: np.ndarray) -> float:
    w = pop[idx].sum(axis=(1, 2))
    if float(w.sum()) > 0:
        return float(np.average(gen[idx], weights=w))
    return float(np.mean(gen[idx]))


def _initialize_registry(root_ids: list[str], guild0: np.ndarray) -> tuple[dict[str, dict], defaultdict[str, int]]:
    registry = {}
    for sid, g in zip(root_ids, guild0):
        registry[str(sid)] = {
            "species_id": str(sid),
            "parent_species_id": None,
            "root_species_id": str(sid),
            "guild_id": int(g),
            "birth_elapsed_year": 0.0,
            "birth_age_ma": None,
            "semantic_status": "REBASED_210MA_ANCESTRAL_SPECIES",
        }
    return registry, defaultdict(int)


def _reset_species_baselines(species_ids: list[str], *, pop: np.ndarray, current_species: list[str],
                             hab: np.ndarray, guild: np.ndarray, env: dict, baselines: dict,
                             elapsed_year: float, occupancy_floor: float) -> None:
    opp = _current_opportunities(hab, current_species, guild, env)
    for sid in species_ids:
        idx = _species_component_indices(current_species, sid)
        if len(idx) == 0:
            continue
        baselines["population"][sid] = float(pop[idx].sum())
        baselines["occupied_cells"][sid] = max(_occupied_cells(pop, idx, occupancy_floor), 1)
        baselines["opportunity"][sid] = max(float(opp.get(sid, 0.0)), 1e-15)
        baselines["elapsed_year"][sid] = float(elapsed_year)


def _initial_baselines(pop: np.ndarray, current_species: list[str], hab: np.ndarray, guild: np.ndarray,
                       env: dict, occupancy_floor: float) -> dict:
    d = {"population": {}, "occupied_cells": {}, "opportunity": {}, "elapsed_year": {}}
    _reset_species_baselines(sorted(set(current_species)), pop=pop, current_species=current_species,
                             hab=hab, guild=guild, env=env, baselines=d, elapsed_year=0.0,
                             occupancy_floor=occupancy_floor)
    return d


def _demography_targets(pop: np.ndarray, current_species: list[str], guild: np.ndarray,
                        registry: dict[str, dict], baselines: dict, opportunity: dict[str, float], env: dict) -> dict[str, float]:
    sp_tot = _species_totals(pop, current_species)
    by_g: dict[int, list[str]] = {g: [] for g in range(1, 7)}
    for sid in sorted(sp_tot):
        by_g[int(registry[sid]["guild_id"])].append(sid)
    prey_cur = sum(sp_tot[s] for g in range(1, 5) for s in by_g[g])
    prey_ref = float(env["reference_population"][:4].sum())
    targets: dict[str, float] = {}
    for g, sids in by_g.items():
        if not sids:
            continue
        gt = float(env["reference_population"][g - 1].sum())
        if g >= 5:
            gt *= float(np.clip(prey_cur / max(prey_ref, 1e-15), 0.0, 1.5))
        w = np.asarray([
            max(float(baselines["population"].get(s, sp_tot[s])), 1e-15)
            * np.clip(float(opportunity.get(s, 0.0)) / max(float(baselines["opportunity"].get(s, 1e-15)), 1e-15), 1e-3, 1e3)
            for s in sids
        ], dtype=float)
        w = w / w.sum() if float(w.sum()) > 0 else np.ones(len(sids), dtype=float) / len(sids)
        for sid, x in zip(sids, gt * w):
            targets[sid] = float(x)
    return targets


def _apply_demography(pop: np.ndarray, current_species: list[str], registry: dict[str, dict], metadata: dict[str, dict],
                       targets: dict[str, float], dt: float) -> np.ndarray:
    out = pop.copy()
    sp_tot = _species_totals(out, current_species)
    for sid in sorted(sp_tot):
        idx = _species_component_indices(current_species, sid)
        root_sid = str(registry[sid]["root_species_id"])
        g = int(registry[sid]["guild_id"])
        tau = r2.GUILD_TAU[g] / max(float(metadata[root_sid]["relative_reproduction_rate"]), 1e-6)
        a = 1.0 - math.exp(-dt / tau)
        old = float(sp_tot[sid])
        new = max(0.0, old + a * (float(targets[sid]) - old))
        if old > 0:
            out[idx] *= new / old
    return out


def _migration_subcycled(pop: np.ndarray, root_species: list[str], guild: np.ndarray, trait: np.ndarray,
                          metadata: dict[str, dict], lat: np.ndarray, lon: np.ndarray, env: dict,
                          dt: float, cfg: R21Config) -> tuple[np.ndarray, np.ndarray]:
    n = int(round(dt / cfg.transport_cadence_years))
    if n < 1 or not _is_multiple(dt, cfg.transport_cadence_years):
        raise ValueError("biology step must contain an integer number of transport substeps")
    out = pop
    hab = None
    for _ in range(n):
        hab = r2.habitats(root_species, guild, trait, out, metadata, env)
        out = r2.migration(out, hab, root_species, metadata, lat, lon, env["land"], cfg.transport_cadence_years, cfg)
    hab = r2.habitats(root_species, guild, trait, out, metadata, env)
    return out, hab


def pair_metrics_root(pop: np.ndarray, trait: np.ndarray, root_species: list[str], metadata: dict[str, dict],
                      lat: np.ndarray, lon: np.ndarray, cfg: R21Config) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = len(pop)
    G = np.zeros((n, n), dtype=float)
    contact = np.zeros_like(G)
    td = np.zeros_like(G)
    totals = pop.sum(axis=(1, 2))
    for root_sid in sorted(set(root_species)):
        idx = _root_component_indices(root_species, root_sid)
        if len(idx) < 2:
            continue
        m = metadata[root_sid]
        ds = max(float(m["dispersal_scale_km"]), 1e-9)
        ts = max(float(m["thermal_niche_sigma_c"]), 1e-6)
        ars = max(float(m["aridity_niche_sigma"]) / 1.55, 1e-4)
        cents = [r2.weighted_centroid(lat, lon, pop[int(i)]) for i in idx]
        for aa in range(len(idx)):
            i = int(idx[aa])
            for bb in range(aa + 1, len(idx)):
                j = int(idx[bb])
                ov = float(np.minimum(pop[i], pop[j]).sum() / max(min(float(totals[i]), float(totals[j])), 1e-15))
                dist = r2.gc_km(cents[aa], cents[bb])
                g = float(np.clip(cfg.gene_flow_ceiling_per_step * ov * math.exp(-dist / (4.0 * ds)), 0.0, cfg.gene_flow_ceiling_per_step))
                G[i, j] = G[j, i] = g
                contact[i, j] = contact[j, i] = g / max(cfg.gene_flow_ceiling_per_step, 1e-15)
                dz = np.asarray([
                    (trait[i, 0] - trait[j, 0]) / ts,
                    (trait[i, 1] - trait[j, 1]) / ars,
                    (trait[i, 2] - trait[j, 2]) / cfg.body_mass_scale,
                ])
                td[i, j] = td[j, i] = float(np.sqrt(np.sum(dz * dz)))
    return G, contact, td


def pair_state_matrices(component_ids: list[str], root_species: list[str], ri_state: dict, clock_state: dict) -> tuple[np.ndarray, np.ndarray]:
    n = len(component_ids)
    ri = np.zeros((n, n), dtype=float)
    clock = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            if root_species[i] != root_species[j]:
                continue
            k = _pair_key(component_ids[i], component_ids[j])
            ri[i, j] = ri[j, i] = float(ri_state.get(k, 0.0))
            clock[i, j] = clock[j, i] = float(clock_state.get(k, 0.0))
    return ri, clock


def advance_pair_states(component_ids: list[str], root_species: list[str], gen: np.ndarray,
                        contact: np.ndarray, td: np.ndarray, ri_state: dict, clock_state: dict,
                        dt: float, cfg: R21Config) -> tuple[dict, dict, np.ndarray, np.ndarray]:
    gate_cfg = sg.SpeciationGateConfig(
        gene_flow_contact_ceiling=cfg.gene_flow_ceiling_per_step,
        trait_drive_onset=cfg.trait_drive_onset,
        trait_drive_saturation=cfg.trait_drive_saturation,
        ri_build_rate_per_generation=cfg.ri_build_rate_per_generation,
        ri_decay_rate_per_generation=cfg.ri_decay_rate_per_generation,
        isolation_reconnection_erosion=cfg.isolation_reconnection_erosion,
        minimum_effective_isolation_generations=cfg.minimum_effective_isolation_generations,
        minimum_intrinsic_RI=cfg.minimum_intrinsic_ri,
        minimum_trait_distance=cfg.minimum_trait_distance,
        maximum_effective_exchange_pressure=cfg.maximum_effective_exchange_pressure,
        minimum_branch_population_fraction=cfg.minimum_branch_population_fraction,
        minimum_complement_population_fraction=cfg.minimum_complement_population_fraction,
        minimum_absolute_population=cfg.minimum_absolute_population,
    )
    new_ri = dict(ri_state)
    new_clock = dict(clock_state)
    n = len(component_ids)
    for i in range(n):
        for j in range(i + 1, n):
            if root_species[i] != root_species[j]:
                continue
            k = _pair_key(component_ids[i], component_ids[j])
            dg = dt / max(float(gen[i]), float(gen[j]), 1e-9)
            st = sg.advance_pair_state(float(new_ri.get(k, 0.0)), float(new_clock.get(k, 0.0)),
                                       dg, float(contact[i, j]), float(td[i, j]), gate_cfg)
            new_ri[k] = float(st["intrinsic_RI"])
            new_clock[k] = float(st["isolation_clock_generations"])
    ri, clock = pair_state_matrices(component_ids, root_species, new_ri, new_clock)
    return new_ri, new_clock, ri, clock


def gene_flow_mix_root(trait: np.ndarray, va: np.ndarray, totals: np.ndarray, G: np.ndarray,
                       ri: np.ndarray, root_species: list[str]) -> tuple[np.ndarray, np.ndarray, dict]:
    tr0 = trait.copy()
    m20 = va + trait * trait
    dtr = np.zeros_like(trait)
    dm2 = np.zeros_like(trait)
    first_before = np.sum(totals[:, None] * tr0, axis=0)
    second_before = np.sum(totals[:, None] * m20, axis=0)
    for i in range(len(trait)):
        ni = float(totals[i])
        if ni <= 0:
            continue
        for j in range(i + 1, len(trait)):
            if root_species[i] != root_species[j]:
                continue
            nj = float(totals[j])
            if nj <= 0:
                continue
            mix = float(G[i, j]) * (1.0 - float(np.clip(ri[i, j], 0.0, 1.0)))
            if mix <= 0:
                continue
            exchange = mix * 2.0 * ni * nj / (ni + nj)
            dtr[i] += (exchange / ni) * (tr0[j] - tr0[i])
            dtr[j] += (exchange / nj) * (tr0[i] - tr0[j])
            dm2[i] += (exchange / ni) * (m20[j] - m20[i])
            dm2[j] += (exchange / nj) * (m20[i] - m20[j])
    tn = tr0 + dtr
    m2n = m20 + dm2
    vn = np.maximum(m2n - tn * tn, 0.0)
    first_after = np.sum(totals[:, None] * tn, axis=0)
    second_after = np.sum(totals[:, None] * m2n, axis=0)
    return tn, vn, {
        "first_moment_conservation_max_abs": float(np.max(np.abs(first_after - first_before))),
        "second_moment_conservation_max_abs": float(np.max(np.abs(second_after - second_before))),
    }


def reproductive_components_scipy(indices: np.ndarray, contact: np.ndarray, td: np.ndarray,
                                  ri: np.ndarray, clock: np.ndarray, cfg: R21Config) -> list[list[int]]:
    """D3.1A reproductive-component semantics, SciPy graph backend."""
    idx = np.asarray(indices, dtype=np.int32)
    n = len(idx)
    if n == 0:
        return []
    rows = list(range(n))
    cols = list(range(n))
    data = [1] * n
    for a in range(n):
        i = int(idx[a])
        for b in range(a + 1, n):
            j = int(idx[b])
            e = sg.effective_exchange_pressure(float(contact[i, j]), float(ri[i, j]))
            isolated = (
                float(clock[i, j]) >= cfg.minimum_effective_isolation_generations
                and float(ri[i, j]) >= cfg.minimum_intrinsic_ri
                and float(td[i, j]) >= cfg.minimum_trait_distance
                and e <= cfg.maximum_effective_exchange_pressure
            )
            if not isolated:
                rows.extend([a, b]); cols.extend([b, a]); data.extend([1, 1])
    graph = csr_array((data, (rows, cols)), shape=(n, n), dtype=np.uint8)
    nc, labels = connected_components(graph, directed=False, return_labels=True)
    out = []
    for lab in range(int(nc)):
        out.append(sorted(int(idx[k]) for k in np.where(labels == lab)[0]))
    return out


def _founder_life_history_min_population(root_sid: str, generation_time_years: float,
                                         metadata: dict[str, dict], cfg: R21Config) -> float:
    m = metadata[root_sid]
    gt = max(float(generation_time_years), 1e-9)
    rr = max(float(m.get("relative_reproduction_rate", 1.0)), 1e-9)
    return float(cfg.founder_base_minimum_population_units
                 * math.sqrt(gt / max(cfg.founder_generation_reference_years, 1e-9))
                 * math.sqrt(max(cfg.founder_reproduction_reference, 1e-9) / rr))


def _founder_normalized_variance(candidate: list[int], totals: np.ndarray, va: np.ndarray,
                                 root_species: list[str], metadata: dict[str, dict], cfg: R21Config) -> float:
    if not candidate:
        return 0.0
    w = totals[candidate]
    if float(w.sum()) <= 0:
        return 0.0
    vals = []
    for i in candidate:
        m = metadata[root_species[i]]
        scales = np.asarray([
            max(float(m["thermal_niche_sigma_c"]), 1e-6),
            max(float(m["aridity_niche_sigma"]) / 1.55, 1e-4),
            max(float(cfg.body_mass_scale), 1e-6),
        ])
        vals.append(float(np.mean(va[i] / (scales * scales))))
    return float(np.average(np.asarray(vals), weights=w))


def _founder_component_key(sid: str, candidate: list[int], component_ids: list[str]) -> str:
    return str(sid) + "|" + ";".join(sorted(str(component_ids[i]) for i in candidate))


def maybe_speciate_founder(*, current_species: list[str], root_species: list[str], component_ids: list[str],
                           pop: np.ndarray, va: np.ndarray, gen: np.ndarray, metadata: dict[str, dict],
                           contact: np.ndarray, td: np.ndarray, ri: np.ndarray, clock: np.ndarray,
                           registry: dict[str, dict], child_counters: defaultdict[str, int], elapsed_year: float,
                           age_ma: float, founder_state: dict, cfg: R21Config) -> tuple[list[dict], dict, list[dict]]:
    totals = pop.sum(axis=(1, 2))
    events: list[dict] = []
    active: dict[str, dict] = {}
    stats: list[dict] = []
    gate_cfg = sg.SpeciationGateConfig(
        gene_flow_contact_ceiling=cfg.gene_flow_ceiling_per_step,
        trait_drive_onset=cfg.trait_drive_onset,
        trait_drive_saturation=cfg.trait_drive_saturation,
        ri_build_rate_per_generation=cfg.ri_build_rate_per_generation,
        ri_decay_rate_per_generation=cfg.ri_decay_rate_per_generation,
        isolation_reconnection_erosion=cfg.isolation_reconnection_erosion,
        minimum_effective_isolation_generations=cfg.minimum_effective_isolation_generations,
        minimum_intrinsic_RI=cfg.minimum_intrinsic_ri,
        minimum_trait_distance=cfg.minimum_trait_distance,
        maximum_effective_exchange_pressure=cfg.maximum_effective_exchange_pressure,
        minimum_branch_population_fraction=0.0,
        minimum_complement_population_fraction=0.0,
        minimum_absolute_population=0.0,
    )
    for sid in sorted(set(current_species)):
        indices = _species_component_indices(current_species, sid)
        if len(indices) < 2:
            continue
        comps = reproductive_components_scipy(indices, contact, td, ri, clock, cfg)
        if len(comps) < 2:
            continue
        comps.sort(key=lambda c: (-float(totals[c].sum()), [component_ids[i] for i in c]))
        candidate = list(comps[1])
        complement = [int(i) for i in indices if int(i) not in candidate]
        branch_pop = float(totals[candidate].sum())
        comp_pop = float(totals[complement].sum())
        cross = [{
            "isolation_clock_generations": float(clock[i, j]),
            "intrinsic_RI": float(ri[i, j]),
            "trait_distance": float(td[i, j]),
            "contact_connectivity": float(contact[i, j]),
        } for i in candidate for j in complement]
        structural = sg.evaluate_branch_gate(cross_pair_states=cross, branch_population=branch_pop,
                                             complement_population=comp_pop, species_population=branch_pop + comp_pop,
                                             cfg=gate_cfg)
        if not structural["gate_ready"]:
            continue
        key = _founder_component_key(sid, candidate, component_ids)
        old = founder_state.get(key)
        if old is None:
            row = {
                "species_id": sid,
                "component_ids": [component_ids[i] for i in candidate],
                "first_seen_elapsed_year": float(elapsed_year),
                "last_seen_elapsed_year": float(elapsed_year),
                "continuous_persistence_years": 0.0,
                "first_population": branch_pop,
                "minimum_population": branch_pop,
                "maximum_population": branch_pop,
                "last_population": branch_pop,
            }
        else:
            delta = max(0.0, float(elapsed_year) - float(old.get("last_seen_elapsed_year", elapsed_year)))
            row = dict(old)
            row["last_seen_elapsed_year"] = float(elapsed_year)
            row["continuous_persistence_years"] = float(old.get("continuous_persistence_years", 0.0)) + delta
            row["minimum_population"] = min(float(old.get("minimum_population", branch_pop)), branch_pop)
            row["maximum_population"] = max(float(old.get("maximum_population", branch_pop)), branch_pop)
            row["last_population"] = branch_pop
        active[key] = row

        root_sid = str(registry[sid]["root_species_id"])
        w = totals[candidate]
        gt = float(np.average(gen[candidate], weights=w)) if float(w.sum()) > 0 else float(np.mean(gen[candidate]))
        comp_w = totals[complement]
        comp_gt = float(np.average(gen[complement], weights=comp_w)) if float(comp_w.sum()) > 0 else gt
        min_pop = _founder_life_history_min_population(root_sid, gt, metadata, cfg)
        comp_min = _founder_life_history_min_population(root_sid, comp_gt, metadata, cfg)
        ne = branch_pop * cfg.drift_individual_equivalents_per_population_unit
        q = _founder_normalized_variance(candidate, totals, va, root_species, metadata, cfg)
        occ = int(np.count_nonzero(pop[candidate].sum(axis=0) > cfg.occupancy_floor))
        first = max(float(row.get("first_population", branch_pop)), 1e-15)
        decline = float(row.get("minimum_population", branch_pop)) / first
        checks = {
            "founder_persistence": float(row["continuous_persistence_years"]) + 1e-9 >= cfg.founder_minimum_persistence_years,
            "founder_life_history_population": branch_pop + 1e-15 >= min_pop,
            "complement_life_history_population": comp_pop + 1e-15 >= comp_min,
            "founder_effective_size_proxy": ne + 1e-9 >= cfg.founder_minimum_effective_size_proxy,
            "founder_genetic_variance": q + 1e-15 >= cfg.founder_minimum_normalized_additive_variance,
            "founder_spatial_support": occ >= cfg.founder_minimum_occupied_cells,
            "founder_no_persistent_collapse": decline + 1e-15 >= cfg.founder_maximum_persistent_decline_fraction,
        }
        founder = {
            "gate_ready": bool(all(checks.values())), "checks": checks,
            "branch_population": branch_pop, "complement_population": comp_pop,
            "life_history_minimum_population": min_pop, "complement_minimum_population": comp_min,
            "effective_size_proxy": ne, "normalized_additive_variance": q,
            "occupied_cells": occ, "minimum_to_first_population_ratio": decline,
            "generation_time_proxy_years": gt,
        }
        stats.append({"key": key, "species_id": sid, "structural_gate": structural, "founder_viability": founder})
        if not founder["gate_ready"]:
            continue
        child_counters[root_sid] += 1
        child = f"{root_sid}_D{child_counters[root_sid]:02d}"
        while child in registry:
            child_counters[root_sid] += 1
            child = f"{root_sid}_D{child_counters[root_sid]:02d}"
        for i in candidate:
            current_species[i] = child
        registry[child] = {
            "species_id": child, "parent_species_id": sid, "root_species_id": root_sid,
            "guild_id": int(registry[sid]["guild_id"]), "birth_elapsed_year": float(elapsed_year),
            "birth_age_ma": float(age_ma), "member_components_at_birth": [component_ids[i] for i in candidate],
            "birth_population": branch_pop,
            "founder_viability_semantics": "D3_2B_LIFE_HISTORY_PERSISTENCE_EFFECTIVE_SIZE_VARIANCE_SUPPORT",
            "semantic_status": "EMERGENT_SPECIES_OBJECT",
        }
        events.append({
            "event": "speciation", "elapsed_year": float(elapsed_year), "age_ma": float(age_ma),
            "parent_species_id": sid, "daughter_species_id": child, "root_species_id": root_sid,
            "daughter_component_ids": [component_ids[i] for i in candidate], "daughter_population": branch_pop,
            "parent_remainder_population": comp_pop, "structural_gate": structural, "founder_viability": founder,
            "population_conservation_error": 0.0,
            "authority": "D3_0C_STRUCTURAL_GATE_PLUS_D3_2B_FOUNDER_VIABILITY",
        })
        active.pop(key, None)
    if cfg.founder_reset_on_reconnection:
        new_state = active
    else:
        new_state = {**founder_state, **active}
    return events, new_state, stats


def _significant_fragments(di: int, pop: np.ndarray, hab: np.ndarray, root_species: list[str], cfg: R21Config):
    p = pop[di]
    total = float(p.sum())
    if total <= cfg.deme_fission_min_absolute_population:
        return []
    core = np.power(np.clip(hab[di], 0.0, 1.0), cfg.habitat_connectivity_power) >= cfg.effective_connectivity_core_threshold
    lab, n = r2._components_wrap((p > cfg.occupancy_floor) & core)
    if n < 2:
        return []
    rows = []
    for k in range(1, n + 1):
        q = np.where(lab == k, p, 0.0)
        rows.append((float(q.sum()), q))
    rows.sort(key=lambda x: -x[0])
    root_total = float(pop[_root_component_indices(root_species, root_species[di])].sum())
    return [x for x in rows if x[0] >= cfg.deme_fission_min_absolute_population
            and x[0] / max(total, 1e-15) >= cfg.deme_fission_min_component_fraction
            and x[0] / max(root_total, 1e-15) >= cfg.deme_fission_min_root_species_fraction]


def update_vicariance_persistence(component_ids: list[str], pop: np.ndarray, hab: np.ndarray,
                                  root_species: list[str], elapsed_year: float, state: dict,
                                  cfg: R21Config) -> tuple[dict, dict]:
    prev = {str(k): dict(v) for k, v in state.items()}
    now, mature = {}, {}
    max_gap = cfg.deme_fission_check_interval_years * 1.01
    active = set()
    for di, did in enumerate(component_ids):
        sig = _significant_fragments(di, pop, hab, root_species, cfg)
        if len(sig) < 2:
            continue
        active.add(str(did))
        old = prev.get(str(did))
        if old is None or elapsed_year - float(old.get("last_seen_elapsed_year", elapsed_year)) > max_gap:
            row = {"first_seen_elapsed_year": float(elapsed_year), "last_seen_elapsed_year": float(elapsed_year),
                   "continuous_persistence_years": 0.0, "significant_component_count": int(len(sig))}
        else:
            delta = max(0.0, elapsed_year - float(old.get("last_seen_elapsed_year", elapsed_year)))
            row = {"first_seen_elapsed_year": float(old.get("first_seen_elapsed_year", elapsed_year)),
                   "last_seen_elapsed_year": float(elapsed_year),
                   "continuous_persistence_years": float(old.get("continuous_persistence_years", 0.0)) + delta,
                   "significant_component_count": int(len(sig))}
        row["largest_component_fraction"] = float(sig[0][0] / max(float(pop[di].sum()), 1e-15))
        row["secondary_component_fraction"] = float(sig[1][0] / max(float(pop[di].sum()), 1e-15))
        now[str(did)] = row
        if row["continuous_persistence_years"] + 1e-9 >= cfg.vicariance_persistence_min_years:
            mature[str(did)] = dict(row)
    if not cfg.vicariance_persistence_reset_on_reconnection:
        for did, row in prev.items():
            if did not in active and did in component_ids:
                now[did] = row
    return now, mature


def _clone_pair_state_after_fission(parent_id: str, child_id: str, component_ids_before: list[str],
                                    root_species_before: list[str], parent_index: int,
                                    ri_state: dict, clock_state: dict) -> None:
    for j, other in enumerate(component_ids_before):
        if j == parent_index or root_species_before[j] != root_species_before[parent_index]:
            continue
        oldk = _pair_key(parent_id, other)
        newk = _pair_key(child_id, other)
        ri_state[newk] = float(ri_state.get(oldk, 0.0))
        clock_state[newk] = float(clock_state.get(oldk, 0.0))
    ri_state[_pair_key(parent_id, child_id)] = 0.0
    clock_state[_pair_key(parent_id, child_id)] = 0.0


def apply_mature_fissions(*, component_ids: list[str], root_species: list[str], current_species: list[str],
                          guild: np.ndarray, pop: np.ndarray, trait: np.ndarray, va: np.ndarray, gen: np.ndarray,
                          hab: np.ndarray, lat: np.ndarray, lon: np.ndarray, ri_state: dict, clock_state: dict,
                          mature: dict, persistence: dict, elapsed_year: float, age_ma: float, cfg: R21Config):
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
        sig = _significant_fragments(di, pop, hab, root_species, cfg)
        if len(sig) < 2:
            continue
        original = pop[di].copy()
        retained = original.copy()
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
    gs = list(guild.astype(int)); pops = [x.copy() for x in pop]; trs = [x.copy() for x in trait]
    vas = [x.copy() for x in va]; gens = list(gen.astype(float)); events = []
    for parent, nid, q, mass, rank in additions:
        ids.append(nid); roots.append(root_species[parent]); cur.append(current_species[parent]); gs.append(int(guild[parent]))
        pops.append(q); trs.append(trait[parent].copy()); vas.append(va[parent].copy()); gens.append(float(gen[parent]))
        _clone_pair_state_after_fission(before_ids[parent], nid, before_ids, before_root, parent, ri_state, clock_state)
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
            "semantic_status": "PERSISTENT_VICARIANCE_DEMOGRAPHIC_FRAGMENT_NOT_SPECIES",
        })
    return ids, roots, cur, np.asarray(gs, np.uint8), np.stack(pops), np.stack(trs), np.stack(vas), np.asarray(gens), ri_state, clock_state, events


def _purge_pair_state(component_ids: list[str], ri_state: dict, clock_state: dict) -> tuple[dict, dict]:
    keep = set(component_ids)
    return ({k: v for k, v in ri_state.items() if k[0] in keep and k[1] in keep},
            {k: v for k, v in clock_state.items() if k[0] in keep and k[1] in keep})


def ordinary_extinction_update(*, current_species: list[str], root_species: list[str], component_ids: list[str],
                               pop: np.ndarray, gen: np.ndarray, metadata: dict[str, dict], registry: dict[str, dict],
                               baselines: dict, opportunity: dict[str, float], elapsed_year: float, ext_state: dict,
                               cfg: R21Config) -> tuple[list[str], dict, list[dict]]:
    new_state = {str(k): dict(v) for k, v in ext_state.items()}
    extant = set(current_species)
    for sid in list(new_state):
        if sid not in extant:
            new_state.pop(sid, None)
    mature = []
    rows = []
    for sid in sorted(extant):
        idx = _species_component_indices(current_species, sid)
        n = float(pop[idx].sum())
        occ = _occupied_cells(pop, idx, cfg.occupancy_floor)
        gt = _species_generation_time(pop, gen, idx)
        root_sid = str(registry[sid]["root_species_id"])
        founder_min = _founder_life_history_min_population(root_sid, gt, metadata, cfg)
        base_n = max(float(baselines["population"].get(sid, n)), 1e-15)
        base_occ = max(float(baselines["occupied_cells"].get(sid, max(occ, 1))), 1.0)
        base_opp = max(float(baselines["opportunity"].get(sid, max(opportunity.get(sid, 0.0), 1e-15))), 1e-15)
        pop_to_founder = n / max(founder_min, 1e-15)
        pr = n / base_n
        rr = occ / base_occ
        oratio = float(opportunity.get(sid, 0.0)) / base_opp
        density = pr / max(rr, 1e-12)
        birth = float(registry[sid].get("birth_elapsed_year", baselines["elapsed_year"].get(sid, 0.0)))
        age = max(0.0, elapsed_year - birth)
        stress = (pop_to_founder <= cfg.ordinary_extinction_founder_floor_fraction
                  and (oratio <= cfg.ordinary_extinction_max_opportunity_ratio
                       or rr <= cfg.ordinary_extinction_max_range_ratio
                       or density <= cfg.ordinary_extinction_max_density_ratio)
                  and age + 1e-9 >= cfg.ordinary_extinction_minimum_species_age_years)
        if not stress:
            new_state.pop(sid, None)
            continue
        st = new_state.get(sid)
        if st is None:
            st = {"start_elapsed_year": float(elapsed_year), "first_population": n,
                  "minimum_population": n, "continuous_stress_years": 0.0}
        else:
            mn = min(float(st.get("minimum_population", n)), n)
            if n > mn * cfg.ordinary_extinction_recovery_reset_factor:
                st = {"start_elapsed_year": float(elapsed_year), "first_population": n,
                      "minimum_population": n, "continuous_stress_years": 0.0}
            else:
                st["minimum_population"] = mn
                st["continuous_stress_years"] = float(elapsed_year) - float(st["start_elapsed_year"])
        new_state[sid] = st
        decline = n / max(float(st["first_population"]), 1e-15)
        persistent = float(st["continuous_stress_years"]) + 1e-9 >= cfg.ordinary_extinction_minimum_persistence_years
        if persistent and decline <= cfg.ordinary_extinction_max_population_ratio_to_episode_start:
            mature.append(sid)
        rows.append({"species_id": sid, "population": n, "persistent": persistent, "decline_ratio": decline})
    return mature, new_state, rows


def apply_extinctions(species_ids: list[str], *, component_ids: list[str], root_species: list[str],
                      current_species: list[str], guild: np.ndarray, pop: np.ndarray, trait: np.ndarray,
                      va: np.ndarray, gen: np.ndarray, registry: dict[str, dict], elapsed_year: float,
                      age_ma: float, ri_state: dict, clock_state: dict):
    if not species_ids:
        return component_ids, root_species, current_species, guild, pop, trait, va, gen, ri_state, clock_state, []
    events = []
    removed = set(species_ids)
    for sid in sorted(removed):
        idx = _species_component_indices(current_species, sid)
        events.append({"event": "ordinary_background_extinction", "species_id": sid,
                       "root_species_id": registry[sid]["root_species_id"], "elapsed_year": float(elapsed_year),
                       "age_ma": float(age_ma), "population": float(pop[idx].sum()),
                       "authority": "D3_2D_STYLE_PERSISTENT_DETERMINISTIC_NONVIABILITY_GATE_NO_GLOBAL_RANDOM_EXTINCTION_RATE"})
        registry[sid]["extinct_elapsed_year"] = float(elapsed_year)
        registry[sid]["extinct_age_ma"] = float(age_ma)
    keep = np.asarray([sid not in removed for sid in current_species], dtype=bool)
    ids = [x for i, x in enumerate(component_ids) if keep[i]]
    roots = [x for i, x in enumerate(root_species) if keep[i]]
    cur = [x for i, x in enumerate(current_species) if keep[i]]
    gs = guild[keep]; pp = pop[keep]; tt = trait[keep]; vv = va[keep]; gg = gen[keep]
    ri_state, clock_state = _purge_pair_state(ids, ri_state, clock_state)
    return ids, roots, cur, gs, pp, tt, vv, gg, ri_state, clock_state, events


def _gate_diagnostics(current_species: list[str], component_ids: list[str], pop: np.ndarray,
                      contact: np.ndarray, td: np.ndarray, ri: np.ndarray, clock: np.ndarray,
                      cfg: R21Config) -> dict:
    totals = pop.sum(axis=(1, 2))
    candidates = 0
    structural_ready = 0
    for sid in sorted(set(current_species)):
        idx = _species_component_indices(current_species, sid)
        if len(idx) < 2:
            continue
        comps = reproductive_components_scipy(idx, contact, td, ri, clock, cfg)
        if len(comps) < 2:
            continue
        candidates += 1
        comps.sort(key=lambda c: (-float(totals[c].sum()), [component_ids[i] for i in c]))
        cand = comps[1]; comp = [int(i) for i in idx if int(i) not in cand]
        cross = [{"isolation_clock_generations": float(clock[i, j]), "intrinsic_RI": float(ri[i, j]),
                  "trait_distance": float(td[i, j]), "contact_connectivity": float(contact[i, j])}
                 for i in cand for j in comp]
        gate = sg.evaluate_branch_gate(cross_pair_states=cross, branch_population=float(totals[cand].sum()),
                                       complement_population=float(totals[comp].sum()),
                                       species_population=float(totals[idx].sum()),
                                       cfg=sg.SpeciationGateConfig(
                                           minimum_branch_population_fraction=0.0,
                                           minimum_complement_population_fraction=0.0,
                                           minimum_absolute_population=0.0))
        if gate["gate_ready"]:
            structural_ready += 1
    return {"reproductively_disconnected_species_count": candidates,
            "structural_speciation_ready_species_count": structural_ready}


def run(common, a1, metadata_rows, cfg: R21Config):
    validate_cadence(cfg)
    metadata = {r["species_id"]: r for r in metadata_rows}
    root_ids = [str(x) for x in common["species_id"].tolist()]
    guild0 = common["guild_id"].astype(int)
    component_ids, root_species, guild, pop = r2.partition_components(
        root_ids, common["species_population"].astype(float), guild0, cfg.occupancy_floor)
    current_species = list(root_species)
    trait, va, gen = r2.init_traits(root_species, metadata)
    registry, child_counters = _initialize_registry(root_ids, guild0)
    lat = common["lat"].astype(float); lon = common["lon"].astype(float)
    env0 = r2.environment_at(cfg.start_age_ma, a1, cfg.topology_switch_age_ma)
    current_land = env0["land"].copy()
    hab = r2.habitats(root_species, guild, trait, pop, metadata, env0)
    baselines = _initial_baselines(pop, current_species, hab, guild, env0, cfg.occupancy_floor)
    ri_state: dict[tuple[str, str], float] = {}
    clock_state: dict[tuple[str, str], float] = {}
    ext_state: dict[str, dict] = {}
    founder_state: dict[str, dict] = {}
    vicariance_state: dict[str, dict] = {}
    events: list[dict] = []
    snapshots: list[dict] = []
    founder_stats_last: list[dict] = []
    gene_flow_closure = {"first_moment_conservation_max_abs": 0.0, "second_moment_conservation_max_abs": 0.0}
    topology_remap_mass = 0.0
    initial_total = float(pop.sum())

    duration = (cfg.start_age_ma - cfg.end_age_ma) * 1e6
    nmacro = int(round(duration / cfg.macrostep_years))
    nbio_per_macro = int(round(cfg.macrostep_years / cfg.biology_cadence_years))
    elapsed = 0.0

    # Initial snapshot.
    snapshots.append({"age_ma": cfg.start_age_ma, "elapsed_myr": 0.0,
                      "species_richness": len(set(current_species)), "component_count": len(component_ids),
                      "total_population": float(pop.sum()), "speciation_events_cumulative": 0,
                      "extinction_events_cumulative": 0, "fission_events_cumulative": 0,
                      "topology": env0["topology"]})

    for macro in range(nmacro):
        for _ in range(nbio_per_macro):
            elapsed += cfg.biology_cadence_years
            age = cfg.start_age_ma - elapsed / 1e6
            env = r2.environment_at(age, a1, cfg.topology_switch_age_ma)
            if not np.array_equal(env["land"], current_land):
                pop, moved = r2.remap_to_land(pop, current_land, env["land"], lat, lon)
                topology_remap_mass += moved
                current_land = env["land"].copy()
                events.append({"event": "topology_support_switch", "age_ma": float(age),
                               "elapsed_year": float(elapsed), "remapped_population_mass": float(moved),
                               "semantic_status": "CONSERVATIVE_DISCRETE_SUPPORT_REMAP"})

            hab = r2.habitats(root_species, guild, trait, pop, metadata, env)
            opportunity = _current_opportunities(hab, current_species, guild, env)
            targets = _demography_targets(pop, current_species, guild, registry, baselines, opportunity, env)
            pop = _apply_demography(pop, current_species, registry, metadata, targets, cfg.biology_cadence_years)
            pop, hab = _migration_subcycled(pop, root_species, guild, trait, metadata, lat, lon, env,
                                            cfg.biology_cadence_years, cfg)

            # Selection and VA remain root-lineage trait machinery; taxonomic birth
            # does not create a new arbitrary niche parameter vector.
            target = r2.selection_targets(pop, env["temperature_c"], env["aridity_index"])
            tr_before = trait.copy()
            trait = r2.select_traits(trait, va, target, root_species, metadata, cfg.biology_cadence_years, cfg)
            totals = pop.sum(axis=(1, 2))
            va = r2.update_va(va, tr_before, target, totals, gen, root_species, metadata,
                              cfg.biology_cadence_years, cfg)

            G, contact, td = pair_metrics_root(pop, trait, root_species, metadata, lat, lon, cfg)
            ri_before, _ = pair_state_matrices(component_ids, root_species, ri_state, clock_state)
            trait, va, gene_flow_closure = gene_flow_mix_root(trait, va, totals, G, ri_before, root_species)
            ri_state, clock_state, ri, clock = advance_pair_states(component_ids, root_species, gen, contact, td,
                                                                   ri_state, clock_state,
                                                                   cfg.biology_cadence_years, cfg)

            # Persistent demographic fragmentation first, as in D3.2B/D3.2D.
            # Fail closed in the two-keyframe R2.1 pilot: the actuator is only
            # active when explicitly authorized by a resolved barrier-history provider.
            if cfg.persistent_vicariance_fission_enabled and _is_multiple(elapsed, cfg.deme_fission_check_interval_years):
                vicariance_state, mature = update_vicariance_persistence(component_ids, pop, hab, root_species,
                                                                          elapsed, vicariance_state, cfg)
                if mature:
                    (component_ids, root_species, current_species, guild, pop, trait, va, gen,
                     ri_state, clock_state, fissions) = apply_mature_fissions(
                        component_ids=component_ids, root_species=root_species, current_species=current_species,
                        guild=guild, pop=pop, trait=trait, va=va, gen=gen, hab=hab, lat=lat, lon=lon,
                        ri_state=ri_state, clock_state=clock_state, mature=mature,
                        persistence=vicariance_state, elapsed_year=elapsed, age_ma=age, cfg=cfg)
                    if fissions:
                        events.extend(fissions)
                        for e in fissions:
                            vicariance_state.pop(e["parent_component_id"], None)
                        hab = r2.habitats(root_species, guild, trait, pop, metadata, env)
                        G, contact, td = pair_metrics_root(pop, trait, root_species, metadata, lat, lon, cfg)
                        ri, clock = pair_state_matrices(component_ids, root_species, ri_state, clock_state)

            # D3.2D-style deterministic ordinary extinction before speciation.
            if _is_multiple(elapsed, cfg.ordinary_extinction_check_interval_years):
                opportunity = _current_opportunities(hab, current_species, guild, env)
                mature_ext, ext_state, _ = ordinary_extinction_update(
                    current_species=current_species, root_species=root_species, component_ids=component_ids,
                    pop=pop, gen=gen, metadata=metadata, registry=registry, baselines=baselines,
                    opportunity=opportunity, elapsed_year=elapsed, ext_state=ext_state, cfg=cfg)
                if mature_ext:
                    (component_ids, root_species, current_species, guild, pop, trait, va, gen,
                     ri_state, clock_state, ext_events) = apply_extinctions(
                        mature_ext, component_ids=component_ids, root_species=root_species,
                        current_species=current_species, guild=guild, pop=pop, trait=trait, va=va, gen=gen,
                        registry=registry, elapsed_year=elapsed, age_ma=age,
                        ri_state=ri_state, clock_state=clock_state)
                    events.extend(ext_events)
                    for sid in mature_ext:
                        ext_state.pop(sid, None)
                    hab = r2.habitats(root_species, guild, trait, pop, metadata, env)
                    G, contact, td = pair_metrics_root(pop, trait, root_species, metadata, lat, lon, cfg)
                    ri, clock = pair_state_matrices(component_ids, root_species, ri_state, clock_state)

            # D3.0C structural authority + D3.2B founder viability.
            if _is_multiple(elapsed, cfg.speciation_check_interval_years):
                births, founder_state, founder_stats_last = maybe_speciate_founder(
                    current_species=current_species, root_species=root_species, component_ids=component_ids,
                    pop=pop, va=va, gen=gen, metadata=metadata, contact=contact, td=td, ri=ri, clock=clock,
                    registry=registry, child_counters=child_counters, elapsed_year=elapsed, age_ma=age,
                    founder_state=founder_state, cfg=cfg)
                if births:
                    events.extend(births)
                    hab = r2.habitats(root_species, guild, trait, pop, metadata, env)
                    touched = sorted({e["parent_species_id"] for e in births} | {e["daughter_species_id"] for e in births})
                    _reset_species_baselines(touched, pop=pop, current_species=current_species, hab=hab, guild=guild,
                                             env=env, baselines=baselines, elapsed_year=elapsed,
                                             occupancy_floor=cfg.occupancy_floor)
                    for sid in touched:
                        ext_state.pop(sid, None)

            if _is_multiple(elapsed, cfg.snapshot_interval_years) or abs(elapsed - duration) < 1e-6:
                species = sorted(set(current_species))
                qnorm = []
                for i, root_sid in enumerate(root_species):
                    m = metadata[root_sid]
                    sc = np.asarray([m["thermal_niche_sigma_c"], max(m["aridity_niche_sigma"] / 1.55, 1e-4), cfg.body_mass_scale])
                    qnorm.extend((va[i] / (sc * sc)).tolist())
                spec_count = sum(1 for e in events if e["event"] == "speciation")
                ext_count = sum(1 for e in events if e["event"] == "ordinary_background_extinction")
                fis_count = sum(1 for e in events if e["event"] == "deme_fission")
                snapshots.append({"age_ma": float(age), "elapsed_myr": elapsed / 1e6,
                                  "species_richness": len(species), "component_count": len(component_ids),
                                  "total_population": float(pop.sum()),
                                  "median_normalized_va": float(np.median(qnorm)) if qnorm else 0.0,
                                  "max_intrinsic_ri": float(np.max(ri)) if ri.size else 0.0,
                                  "max_isolation_clock_generations": float(np.max(clock)) if clock.size else 0.0,
                                  "speciation_events_cumulative": spec_count,
                                  "extinction_events_cumulative": ext_count,
                                  "fission_events_cumulative": fis_count,
                                  "topology": env["topology"]})

    env_end = r2.environment_at(cfg.end_age_ma, a1, cfg.topology_switch_age_ma)
    hab_end = r2.habitats(root_species, guild, trait, pop, metadata, env_end)
    G, contact, td = pair_metrics_root(pop, trait, root_species, metadata, lat, lon, cfg)
    ri, clock = pair_state_matrices(component_ids, root_species, ri_state, clock_state)
    gate_diag = _gate_diagnostics(current_species, component_ids, pop, contact, td, ri, clock, cfg)
    return {
        "stage": R21_STAGE_ID, "config": asdict(cfg), "initial_total_population": initial_total,
        "final_total_population": float(pop.sum()), "root_species_ids": sorted(set(root_species)),
        "species_ids": sorted(set(current_species)), "component_ids": list(component_ids),
        "component_root_species": list(root_species), "component_species": list(current_species),
        "component_guild": guild, "population": pop, "trait": trait, "va": va,
        "generation_time": gen, "ri": ri, "clock": clock, "contact": contact, "trait_distance": td,
        "registry": [registry[k] for k in sorted(registry)], "events": events, "snapshots": snapshots,
        "founder_state": founder_state, "vicariance_state": vicariance_state, "extinction_state": ext_state,
        "founder_stats_last": founder_stats_last, "gate_diagnostics": gate_diag,
        "gene_flow_closure": gene_flow_closure, "topology_remap_mass": topology_remap_mass,
        "cadence_authority": {
            "macrostep_years": cfg.macrostep_years,
            "biology_cadence_years": cfg.biology_cadence_years,
            "transport_cadence_years": cfg.transport_cadence_years,
            "macrostep_changes_biology": False,
        },
        "authority": {
            "speciation_structural_gate": "D3.0C_SEALED_SOURCE_REUSED",
            "founder_viability": "D3.2B_CALIBRATED_THRESHOLDS_REUSED",
            "ordinary_extinction": "D3.2D_PERSISTENT_DETERMINISTIC_NONVIABILITY_SEMANTICS",
            "persistent_vicariance_fission_enabled": bool(cfg.persistent_vicariance_fission_enabled),
            "fission_activation_rule": "OFF_IN_TWO_KEYFRAME_R2_1_PILOT__ENABLE_ONLY_WITH_RESOLVED_BARRIER_HISTORY",
            "reproductive_components_backend": "SCIPY_SPARSE_CSGRAPH_CONNECTED_COMPONENTS",
            "raster_components_backend": "SCIPY_NDIMAGE_LABEL_WITH_LONGITUDE_SEAM_UNION",
            "global_speciation_rate": None, "global_extinction_rate": None,
            "named_winner_selection": False, "Deep_biological_coupling": False,
        },
    }
