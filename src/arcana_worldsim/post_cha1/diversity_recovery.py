from __future__ import annotations

from dataclasses import asdict, dataclass
from collections import defaultdict
from pathlib import Path
import json
import math

import numpy as np

from . import dynamic_demes as dd
from . import speciation_gate as sg
from . import additive_variance as av
from . import adaptive_radiation as ar

STATUS = "PASS_POST_CHA1_DIVERSITY_RECOVERY_5_TO_20MYR_CANDIDATE"


@dataclass(frozen=True)
class DiversityRecoveryConfig:
    seed: int = 917231
    start_relative_year: float = 5_000_000.0
    end_relative_year: float = 20_000_000.0
    dt_years: float = 100_000.0
    snapshot_interval_years: float = 500_000.0
    deme_fission_check_interval_years: float = 500_000.0
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
    variance_homeostasis_enabled: bool = False
    mutation_supply_generation_scaled: bool = False
    mutation_supply_reference_generation_years: float = 5.0
    baseline_stabilizing_variance_depletion_per_generation: float = 0.0
    nonlinear_stabilizing_variance_depletion_per_myr_per_q: float = 0.0
    selection_variance_depletion_per_generation: float = 2.0e-8
    selection_pressure_ceiling: float = 4.0
    drift_individual_equivalents_per_population_unit: float = 250_000_000.0
    drift_min_effective_size: float = 500.0
    maximum_total_exchange_fraction_per_deme: float = 0.45
    deme_fission_min_component_fraction: float = 0.02
    deme_fission_min_absolute_population: float = 0.01
    deme_fission_min_root_species_fraction: float = 0.01
    speciation_enabled: bool = True
    species_fusion_enabled: bool = False
    background_species_extinction_enabled: bool = False
    Deep_adaptation_enabled: bool = False
    dragon_lineage_selection_enabled: bool = False
    sapience_enabled: bool = False
    civilization_enabled: bool = False
    author_selected_winner_enabled: bool = False
    physical_provider: str = "PIECEWISE_LINEAR_INTERPOLATION_ACROSS_MATERIALIZED_C2_2_REBASED_A1_FRAMES"
    terrestrial_support_semantics: str = "FRACTIONAL_INTERPOLATED_SUPPORT_NOT_LITERAL_SUBGRID_COASTLINE"

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

    def variance_cfg(self) -> av.AdditiveVarianceConfig:
        return av.AdditiveVarianceConfig(
            mutation_variance_supply_normalized_per_myr=self.mutation_variance_supply_normalized_per_myr,
            mutation_variance_ceiling_normalized=self.mutation_variance_ceiling_normalized,
            variance_homeostasis_enabled=self.variance_homeostasis_enabled,
            mutation_supply_generation_scaled=self.mutation_supply_generation_scaled,
            mutation_supply_reference_generation_years=self.mutation_supply_reference_generation_years,
            baseline_stabilizing_variance_depletion_per_generation=self.baseline_stabilizing_variance_depletion_per_generation,
            nonlinear_stabilizing_variance_depletion_per_myr_per_q=self.nonlinear_stabilizing_variance_depletion_per_myr_per_q,
            selection_variance_depletion_per_generation=self.selection_variance_depletion_per_generation,
            selection_pressure_ceiling=self.selection_pressure_ceiling,
            drift_individual_equivalents_per_population_unit=self.drift_individual_equivalents_per_population_unit,
            drift_min_effective_size=self.drift_min_effective_size,
            maximum_total_exchange_fraction_per_deme=self.maximum_total_exchange_fraction_per_deme,
        )


@dataclass
class DiversityRecoveryResult:
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


def load_config(path: Path) -> DiversityRecoveryConfig:
    raw = _read_json(path)
    fields = DiversityRecoveryConfig.__dataclass_fields__
    return DiversityRecoveryConfig(**{k: raw[k] for k in fields if k in raw})


def _load_metadata(path: Path):
    rows = _read_json(path)
    if isinstance(rows, dict) and "species" in rows:
        rows = rows["species"]
    md = {r["species_id"]: r for r in rows}
    # Preserve the explicit D2 child proxy already carried through D3.1A.
    if "HSG_025" not in md and "HSG_003" in md:
        md["HSG_025"] = dict(md["HSG_003"])
        md["HSG_025"]["species_id"] = "HSG_025"
        md["HSG_025"]["trait_provenance"] = "PARENT_PROXY_HSG_003_D2_CHILD_TRAITS_NOT_EXPORTED"
    return md


def _load_inputs(root: Path, cfg: DiversityRecoveryConfig):
    parent_diag = _read_json(root / "inputs/D3_1A_PARENT/adaptive_radiation_diagnostics.json")
    if parent_diag.get("status") != "PASS_ADDITIVE_GENETIC_VARIANCE_DYNAMICS_RECOVERY_CALIBRATION_CANDIDATE":
        raise ValueError("D3.2 requires the passing D3.1A endpoint")
    if not math.isclose(float(parent_diag.get("end_physical_age_ma", -1)), 61.0, abs_tol=1e-9):
        raise ValueError("D3.1A parent must end at physical age 61 Ma")

    parent = np.load(root / "inputs/D3_1A_PARENT/adaptive_radiation_state.npz", allow_pickle=False)
    a1 = np.load(root / "inputs/A1_REFERENCE/fauna_baseline_state_A1.npz", allow_pickle=False)
    metadata = _load_metadata(root / "inputs/D1_METADATA/species_metadata.json")
    gate_cfg = _read_json(root / "inputs/D3_0C_GATE/speciation_gate_v0_6_3D3_0C.json")
    baseline = np.load(root / "inputs/D3_0A_BASELINE/post_cha1_spatial_bridge_state.npz", allow_pickle=False)
    seed_registry = _read_json(root / "inputs/D3_0A_BASELINE/deme_seed_registry.json")
    bridge_diag = _read_json(root / "inputs/D3_0A_BASELINE/spatial_bridge_diagnostics.json")
    parent_registry = _read_json(root / "inputs/D3_1A_PARENT/species_registry.json")["species"]
    inherited_speciation_events = _read_json(root / "inputs/D3_1A_PARENT/speciation_events.json")["events"]
    inherited_fission_events = _read_json(root / "inputs/D3_1A_PARENT/deme_fission_events.json")["events"]

    required = {
        "minimum_effective_isolation_generations": 50_000.0,
        "minimum_intrinsic_RI": 0.65,
        "minimum_trait_distance": 1.0,
        "maximum_effective_exchange_pressure": 0.25,
    }
    for k, v in required.items():
        if not math.isclose(float(gate_cfg[k]), v, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"Unexpected D3.0C gate calibration for {k}")

    return {
        "parent_diag": parent_diag,
        "parent": parent,
        "a1": a1,
        "metadata": metadata,
        "gate_cfg": gate_cfg,
        "baseline": baseline,
        "seed_registry": seed_registry,
        "bridge_diag": bridge_diag,
        "parent_registry": parent_registry,
        "inherited_speciation_events": inherited_speciation_events,
        "inherited_fission_events": inherited_fission_events,
    }


def _piecewise_substrate(a1, relative_year: float, residual_temp_anomaly_c: float = 0.0):
    age = 66.0 - float(relative_year) / 1_000_000.0
    ages = np.asarray(a1["age_ma"], dtype=float)
    if age < float(np.min(ages)) - 1e-9 or age > float(np.max(ages)) + 1e-9:
        raise ValueError(f"Physical age {age} Ma outside materialized A1 frame range")

    exact = np.where(np.isclose(ages, age, atol=1e-12))[0]
    if len(exact):
        hi = lo = int(exact[0])
        alpha = 0.0
    else:
        older = np.where(ages > age)[0]
        younger = np.where(ages < age)[0]
        if not len(older) or not len(younger):
            raise ValueError(f"Cannot bracket physical age {age} Ma")
        hi = int(older[-1])       # nearest older frame because ages descend
        lo = int(younger[0])     # nearest younger frame
        a_hi = float(ages[hi])
        a_lo = float(ages[lo])
        alpha = (a_hi - age) / max(a_hi - a_lo, 1e-15)

    def lerp(key: str):
        if hi == lo:
            return np.asarray(a1[key][hi], dtype=float).copy()
        return (1.0 - alpha) * np.asarray(a1[key][hi], dtype=float) + alpha * np.asarray(a1[key][lo], dtype=float)

    land_support = np.clip(lerp("land_mask"), 0.0, 1.0)
    accessible = land_support > 1e-9
    anomaly = float(residual_temp_anomaly_c) * math.exp(-max(relative_year - 500_000.0, 0.0) / 150_000.0)
    return {
        "age_ma": float(age),
        "frame_older_ma": float(ages[hi]),
        "frame_younger_ma": float(ages[lo]),
        "frame_alpha": float(alpha),
        "land_support": land_support,
        "accessible": accessible,
        "temperature_c": lerp("temperature_c") + anomaly,
        "aridity_index": lerp("aridity_index"),
        "browse_forage": lerp("browse_forage"),
        "low_forage": lerp("low_forage"),
        "wetland_forage": lerp("wetland_forage"),
        "total_edible_forage": lerp("total_edible_forage"),
        "reference_population": lerp("population"),
    }


def _reconstruct_d31_demography_baseline(data, cfg: DiversityRecoveryConfig):
    pz = data["baseline"]
    root_species_ids = pz["species_id"].tolist()
    lat = pz["lat"].astype(float)
    lon = pz["lon"].astype(float)
    species_guild = pz["guild_id"].astype(np.uint8)
    deme_ids, root_idx, _, pop, _ = dd._partition_parent_into_demes(
        root_species_ids,
        pz["endpoint_population_500kyr"].astype(float),
        data["seed_registry"],
        lat,
        lon,
        cfg.occupancy_floor,
    )
    trait, _, _, _ = dd._deme_trait_initialization(root_idx, root_species_ids, data["metadata"])
    residual = float(data["bridge_diag"].get("endpoint_temperature_anomaly_c", 0.0))
    sub = _piecewise_substrate(data["a1"], 500_000.0, residual)
    hab = ar._habitats(pop, trait, root_idx, root_species_ids, species_guild, data["metadata"], sub, cfg)
    initial_root_total = ar._root_species_population(pop, root_idx, len(root_species_ids)).sum(axis=(1, 2))
    initial_opportunity = ar._opportunity(hab, root_idx, species_guild, sub, len(root_species_ids))
    return initial_root_total, initial_opportunity


def _child_counters_from_registry(registry: dict[str, dict]):
    counters = defaultdict(int)
    for sid, row in registry.items():
        root = row.get("root_species_id", sid)
        marker = f"{root}_D"
        if sid.startswith(marker):
            tail = sid[len(marker):]
            if tail.isdigit():
                counters[root] = max(counters[root], int(tail))
    return counters



def _pair_metrics_fast(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg):
    """Numerically equivalent to D3.1A pair metrics with cached deme totals/centroids."""
    nd = len(root_idx)
    G = np.zeros((nd, nd), dtype=float)
    contact = np.zeros((nd, nd), dtype=float)
    td = np.zeros((nd, nd), dtype=float)
    totals = pop.sum(axis=(1, 2))
    centroids = [dd._weighted_centroid(lat, lon, pop[i]) if totals[i] > 0 else (float('nan'), float('nan')) for i in range(nd)]
    dcfg = cfg.dynamic_cfg()
    for si, sid in enumerate(root_species_ids):
        idx = np.where(root_idx == si)[0]
        if len(idx) < 2:
            continue
        meta = metadata[sid]
        ds = float(meta["dispersal_scale_km"])
        tscale = max(float(meta["thermal_niche_sigma_c"]), 1e-6)
        dscale = max(float(meta["aridity_niche_sigma"]) / 1.55, 1e-4)
        mscale = max(float(dcfg.body_mass_scale), 1e-6)
        for a in range(len(idx)):
            i = int(idx[a])
            ni = float(totals[i])
            if ni <= 0:
                continue
            for b in range(a + 1, len(idx)):
                j = int(idx[b])
                nj = float(totals[j])
                if nj <= 0:
                    continue
                overlap = float(np.minimum(pop[i], pop[j]).sum() / max(min(ni, nj), 1e-15))
                ci, cj = centroids[i], centroids[j]
                dist = float(dd._great_circle_km(ci[0], ci[1], cj[0], cj[1]))
                decay = math.exp(-dist / max(4.0 * ds, 1e-9))
                g = float(np.clip(dcfg.gene_flow_ceiling_per_step * overlap * decay, 0.0, dcfg.gene_flow_ceiling_per_step))
                G[i, j] = G[j, i] = g
                contact[i, j] = contact[j, i] = sg.contact_connectivity_from_d30b_gene_flow(g)
                dz0 = (trait[i, 0] - trait[j, 0]) / tscale
                dz1 = (trait[i, 1] - trait[j, 1]) / dscale
                dz2 = (trait[i, 2] - trait[j, 2]) / mscale
                x = float(math.sqrt(dz0 * dz0 + dz1 * dz1 + dz2 * dz2))
                td[i, j] = td[j, i] = x
    return G, contact, td


def _trait_distance_only(trait, root_idx, root_species_ids, metadata, cfg):
    nd = len(root_idx)
    td = np.zeros((nd, nd), dtype=float)
    for si, sid in enumerate(root_species_ids):
        idx = np.where(root_idx == si)[0]
        if len(idx) < 2:
            continue
        meta = metadata[sid]
        tscale = max(float(meta["thermal_niche_sigma_c"]), 1e-6)
        dscale = max(float(meta["aridity_niche_sigma"]) / 1.55, 1e-4)
        mscale = max(float(cfg.body_mass_scale), 1e-6)
        for a in range(len(idx)):
            i = int(idx[a])
            for b in range(a + 1, len(idx)):
                j = int(idx[b])
                dz0 = (trait[i, 0] - trait[j, 0]) / tscale
                dz1 = (trait[i, 1] - trait[j, 1]) / dscale
                dz2 = (trait[i, 2] - trait[j, 2]) / mscale
                x = float(math.sqrt(dz0 * dz0 + dz1 * dz1 + dz2 * dz2))
                td[i, j] = td[j, i] = x
    return td

def _pair_gate_counts(root_idx, contact, td, ri, clock):
    counts = {
        "pairs": 0,
        "clock_ge_50k": 0,
        "ri_ge_065": 0,
        "td_ge_1": 0,
        "exchange_le_025": 0,
        "all_pair_isolation_conditions": 0,
    }
    n = len(root_idx)
    for i in range(n):
        for j in range(i + 1, n):
            if root_idx[i] != root_idx[j]:
                continue
            counts["pairs"] += 1
            e = sg.effective_exchange_pressure(contact[i, j], ri[i, j])
            c = clock[i, j] >= 50_000.0
            r = ri[i, j] >= 0.65
            t = td[i, j] >= 1.0
            x = e <= 0.25
            counts["clock_ge_50k"] += int(c)
            counts["ri_ge_065"] += int(r)
            counts["td_ge_1"] += int(t)
            counts["exchange_le_025"] += int(x)
            counts["all_pair_isolation_conditions"] += int(c and r and t and x)
    return counts


def run(root: Path, cfg: DiversityRecoveryConfig) -> DiversityRecoveryResult:
    if not math.isclose(cfg.start_relative_year, 5_000_000.0, abs_tol=1e-9):
        raise ValueError("D3.2 must continue from the D3.1A +5 Myr endpoint")
    if cfg.end_relative_year > 20_000_000.0 + 1e-9:
        raise ValueError("D3.2 candidate is bounded to +20 Myr")
    if cfg.dt_years <= 0 or cfg.end_relative_year <= cfg.start_relative_year:
        raise ValueError("Invalid D3.2 time window")
    nsteps_float = (cfg.end_relative_year - cfg.start_relative_year) / cfg.dt_years
    if abs(nsteps_float - round(nsteps_float)) > 1e-9:
        raise ValueError("D3.2 duration must be an integer number of timesteps")
    forbidden = [cfg.species_fusion_enabled, cfg.background_species_extinction_enabled,
                 cfg.Deep_adaptation_enabled, cfg.dragon_lineage_selection_enabled,
                 cfg.sapience_enabled, cfg.civilization_enabled, cfg.author_selected_winner_enabled]
    if any(forbidden):
        raise ValueError("Forbidden D3.2 scope switch enabled")

    data = _load_inputs(root, cfg)
    p = data["parent"]
    root_species_ids = p["root_species_id"].tolist()
    metadata = data["metadata"]
    deme_ids = p["deme_id"].tolist()
    current_species = p["current_species_id"].tolist()
    root_idx = p["root_species_index"].astype(np.int32).copy()
    deme_guild = p["guild_id"].astype(np.uint8).copy()
    species_guild = data["baseline"]["guild_id"].astype(np.uint8)
    lat = p["lat"].astype(float)
    lon = p["lon"].astype(float)
    pop = p["endpoint_population"].astype(float).copy()
    trait = p["endpoint_trait"].astype(float).copy()
    va = p["endpoint_additive_variance"].astype(float).copy()
    generation_time = p["generation_time_proxy_years"].astype(float).copy()
    intrinsic_ri = p["endpoint_intrinsic_RI"].astype(float).copy()
    isolation_clock = p["endpoint_isolation_clock_generations"].astype(float).copy()

    registry = {r["species_id"]: dict(r) for r in data["parent_registry"]}
    child_counters = _child_counters_from_registry(registry)
    new_speciation_events = []
    new_fission_events = []

    initial_root_total, initial_opportunity = _reconstruct_d31_demography_baseline(data, cfg)
    parent_start_population = float(pop.sum())
    parent_start_richness = len(set(current_species))
    parent_start_demes = len(deme_ids)

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

    G, contact, td = _pair_metrics_fast(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg)
    m0 = ar._snapshot_metrics(pop, trait, root_idx, current_species, contact, td, intrinsic_ri, isolation_clock, cfg.occupancy_floor)
    snapshot_times = [cfg.start_relative_year]
    metrics = [m0]
    start_sub = _piecewise_substrate(data["a1"], cfg.start_relative_year)
    snapshot_rows = [{
        "relative_year": cfg.start_relative_year,
        "age_ma": start_sub["age_ma"],
        "frame_older_ma": start_sub["frame_older_ma"],
        "frame_younger_ma": start_sub["frame_younger_ma"],
        "frame_alpha": start_sub["frame_alpha"],
        "deme_count": len(deme_ids),
        **m0,
    }]

    steps = int(round(nsteps_float))
    snap_every = max(1, int(round(cfg.snapshot_interval_years / cfg.dt_years)))
    fiss_every = max(1, int(round(cfg.deme_fission_check_interval_years / cfg.dt_years)))

    for step in range(1, steps + 1):
        relative_year = cfg.start_relative_year + step * cfg.dt_years
        sub = _piecewise_substrate(data["a1"], relative_year)

        habitat = ar._habitats(pop, trait, root_idx, root_species_ids, species_guild, metadata, sub, cfg)
        pop = ar._migration(pop, habitat, root_idx, root_species_ids, metadata, lat, lon, sub, cfg.dt_years, cfg)
        habitat = ar._habitats(pop, trait, root_idx, root_species_ids, species_guild, metadata, sub, cfg)
        pop = ar._demography(
            pop, habitat, root_idx, root_species_ids, species_guild, metadata,
            initial_root_total, initial_opportunity, sub, cfg.dt_years,
        )

        G, contact, td = _pair_metrics_fast(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg)
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

        td = _trait_distance_only(trait, root_idx, root_species_ids, metadata, cfg)
        intrinsic_ri, isolation_clock = ar._advance_pair_state(
            intrinsic_ri, isolation_clock, contact, td, generation_time, root_idx, cfg.dt_years
        )

        if step % fiss_every == 0:
            (
                deme_ids, root_idx, deme_guild, current_species, pop, trait, va,
                generation_time, intrinsic_ri, isolation_clock, fissions,
            ) = ar._fission_demes(
                deme_ids, root_idx, deme_guild, current_species, pop, trait, va,
                generation_time, intrinsic_ri, isolation_clock, relative_year,
                lat, lon, cfg,
            )
            for row in fissions:
                row["root_species_id"] = root_species_ids[int(root_idx[deme_ids.index(row["daughter_deme_id"])])]
            new_fission_events.extend(fissions)
            if fissions:
                G, contact, td = _pair_metrics_fast(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg)

        if cfg.speciation_enabled and step % snap_every == 0:
            births = ar._maybe_speciate(
                current_species, root_idx, root_species_ids, deme_ids, pop,
                contact, td, intrinsic_ri, isolation_clock,
                registry, child_counters, relative_year,
            )
            new_speciation_events.extend(births)

        if step % snap_every == 0 or step == steps:
            sm = ar._snapshot_metrics(
                pop, trait, root_idx, current_species, contact, td,
                intrinsic_ri, isolation_clock, cfg.occupancy_floor,
            )
            snapshot_times.append(relative_year)
            metrics.append(sm)
            snapshot_rows.append({
                "relative_year": float(relative_year),
                "age_ma": float(sub["age_ma"]),
                "frame_older_ma": float(sub["frame_older_ma"]),
                "frame_younger_ma": float(sub["frame_younger_ma"]),
                "frame_alpha": float(sub["frame_alpha"]),
                "deme_count": len(deme_ids),
                **sm,
            })

    G, contact, td = _pair_metrics_fast(pop, trait, root_idx, root_species_ids, metadata, lat, lon, cfg)
    final_species_ids = sorted(set(current_species))
    final_root_total = ar._root_species_population(pop, root_idx, len(root_species_ids)).sum(axis=(1, 2))
    final_variance_summary = av.normalized_variance_summary(
        va, root_idx, root_species_ids, metadata, cfg.body_mass_scale
    )
    max_norm_va = float(final_variance_summary["max"])
    gate_counts = _pair_gate_counts(root_idx, contact, td, intrinsic_ri, isolation_clock)

    lineage_species_counts = defaultdict(int)
    for sid in final_species_ids:
        lineage_species_counts[registry[sid]["root_species_id"]] += 1
    diversified_roots = {k: v for k, v in lineage_species_counts.items() if v > 1}
    birth_times = [float(e["relative_year"]) for e in new_speciation_events]

    diagnostics = {
        "status": STATUS,
        "config": asdict(cfg),
        "parent_status": data["parent_diag"]["status"],
        "continuation_semantics": "EXACT_D3_1A_ENDPOINT_STATE_NO_RESET_OF_DEMES_TRAITS_VA_RI_OR_ISOLATION_CLOCK",
        "start_relative_year": cfg.start_relative_year,
        "end_relative_year": cfg.end_relative_year,
        "start_physical_age_ma": 61.0,
        "end_physical_age_ma": 46.0,
        "physical_provider": cfg.physical_provider,
        "materialized_physical_frames_crossed_ma": [60.0],
        "physical_interpolation_brackets_used": sorted({(r["frame_older_ma"], r["frame_younger_ma"]) for r in snapshot_rows}, reverse=True),
        "initial_species_richness": parent_start_richness,
        "final_species_richness": len(final_species_ids),
        "new_speciation_event_count": len(new_speciation_events),
        "cumulative_speciation_event_count": len(data["inherited_speciation_events"]) + len(new_speciation_events),
        "initial_deme_count": parent_start_demes,
        "final_deme_count": len(deme_ids),
        "new_deme_fission_event_count": len(new_fission_events),
        "cumulative_deme_fission_event_count": len(data["inherited_fission_events"]) + len(new_fission_events),
        "initial_total_population": parent_start_population,
        "final_total_population": float(pop.sum()),
        "relative_total_population_change": float((pop.sum() - parent_start_population) / max(parent_start_population, 1e-15)),
        "final_root_lineage_population_total": float(final_root_total.sum()),
        "initial_normalized_additive_variance_summary": initial_variance_summary,
        "final_normalized_additive_variance_summary": final_variance_summary,
        "max_normalized_additive_variance": max_norm_va,
        "variance_budget": variance_budget,
        "pair_gate_counts": gate_counts,
        "diversified_root_lineage_count": len(diversified_roots),
        "diversified_root_lineages": dict(sorted(diversified_roots.items())),
        "first_new_speciation_relative_year": min(birth_times) if birth_times else None,
        "last_new_speciation_relative_year": max(birth_times) if birth_times else None,
        "background_species_extinction_enabled": False,
        "species_fusion_enabled": False,
        "Deep_adaptation_enabled": False,
        "dragon_lineage_selection_enabled": False,
        "sapience_enabled": False,
        "civilization_enabled": False,
        "author_selected_winner_enabled": False,
        "HSG_025_trait_provenance": metadata["HSG_025"].get("trait_provenance"),
        "snapshot_rows": snapshot_rows,
        "interpretation": (
            "D3.2 measures emergent post-CHA1 taxonomic diversification from +5 to +20 Myr. "
            "No global radiation boost, preferred lineage, background extinction, Deep adaptation, or narrative winner authority is active."
        ),
    }

    return DiversityRecoveryResult(
        root_species_ids=root_species_ids,
        final_species_ids=final_species_ids,
        deme_ids=deme_ids,
        current_species_id=list(current_species),
        root_species_index=root_idx,
        guild_id=deme_guild,
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
        speciation_events=new_speciation_events,
        deme_fission_events=new_fission_events,
        diagnostics=diagnostics,
    )


def write_outputs(root: Path, result: DiversityRecoveryResult):
    out = root / "outputs/hybrid1/diversity_recovery_v0_6_3D3_2"
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out / "diversity_recovery_state.npz",
        root_species_id=np.asarray(result.root_species_ids),
        final_species_id=np.asarray(result.final_species_ids),
        deme_id=np.asarray(result.deme_ids),
        current_species_id=np.asarray(result.current_species_id),
        root_species_index=result.root_species_index,
        guild_id=result.guild_id,
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
    (out / "diversity_recovery_diagnostics.json").write_text(
        json.dumps(result.diagnostics, indent=2, sort_keys=True), encoding="utf-8"
    )
    (out / "species_registry.json").write_text(
        json.dumps({"species": result.species_registry}, indent=2, sort_keys=True), encoding="utf-8"
    )
    (out / "speciation_events_5_20myr.json").write_text(
        json.dumps({"events": result.speciation_events}, indent=2, sort_keys=True), encoding="utf-8"
    )
    (out / "deme_fission_events_5_20myr.json").write_text(
        json.dumps({"events": result.deme_fission_events}, indent=2, sort_keys=True), encoding="utf-8"
    )
    return out
