from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import numpy as np

import rebased_natural_control_runtime_v0_6D1_R2 as r2
import rebased_natural_control_runtime_v0_6D1_R2_1 as r21
import rebased_natural_control_runtime_v0_6D1_R3_4 as r34
import rebased_natural_control_runtime_v0_6D1_R3_5 as r35
import rebased_deep_time_barrier_provider_v0_6D1_R3 as bp

from .r37h_closed_loop_binding import (
    BRANCH_K,
    _ClosedLoopContext,
    _closed_loop_bindings,
    _event_counts,
    _normalized_q,
)
from .segregation_potential_lifecycle import (
    ReducedGeneticLifecycleState,
    initialize_minimum_information_state,
)

STAGE = "v0.6D1-R3.8"
PARENT_STAGE = "v0.6D1-R3.7I"
CHECKPOINT_SCHEMA = "ARCANA_R38_CANONICAL_150MA_CHECKPOINT_V1"
RUNTIME_SCHEMA = "ARCANA_R38_RESTARTABLE_RUNTIME_STATE_V1"
NOMINAL_K = BRANCH_K["K_CENTER"]
ORIGIN_AGE_MA = 210.0
CHECKPOINT_AGE_MA = 150.0


@dataclass(frozen=True)
class R38Config(r35.R35Config):
    start_age_ma: float = ORIGIN_AGE_MA
    end_age_ma: float = 149.0
    adaptive_k_eff: float = NOMINAL_K
    branch_label: str = "K_CENTER"
    segregation_recombination_fraction_per_generation: float = 0.5

    def __post_init__(self) -> None:
        if abs(self.start_age_ma - ORIGIN_AGE_MA) > 1e-12:
            raise ValueError("R3.8 origin remains 210 Ma")
        if not (0.0 <= self.end_age_ma < ORIGIN_AGE_MA):
            raise ValueError("invalid R3.8 end age")
        if self.branch_label != "K_CENTER" or abs(self.adaptive_k_eff - NOMINAL_K) > 1e-12:
            raise ValueError("R3.8 canonical branch is the sealed K_CENTER operational reference")
        if not (0.0 <= self.segregation_recombination_fraction_per_generation <= 0.5):
            raise ValueError("invalid recombination fraction")


@dataclass
class R38RuntimeState:
    age_ma: float
    elapsed_year: float
    component_ids: list[str]
    root_species: list[str]
    current_species: list[str]
    guild: np.ndarray
    pop: np.ndarray
    trait: np.ndarray
    va: np.ndarray
    gen: np.ndarray
    registry: dict[str, dict]
    child_counters: dict[str, int]
    current_accessible: np.ndarray
    baselines: dict[str, dict]
    ri_state: dict[tuple[str, str], float]
    clock_state: dict[tuple[str, str], float]
    ext_state: dict[str, dict]
    founder_state: dict[str, dict]
    vicariance_state: dict[str, dict]
    reconnection_state: dict[tuple[str, str], dict]
    events: list[dict]
    snapshots: list[dict]
    founder_stats_last: list[dict]
    gene_flow_closure: dict[str, Any]
    topology_remap_mass: float
    initial_total_population: float
    reduced_state: ReducedGeneticLifecycleState


def _jsonable(x: Any) -> Any:
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def _pair_dict_rows(d: dict[tuple[str, str], Any]) -> list[dict[str, Any]]:
    rows = []
    for (a, b), value in sorted(d.items()):
        rows.append({"a": str(a), "b": str(b), "value": _jsonable(value)})
    return rows


def _pair_dict_from_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str], Any]:
    return {(str(r["a"]), str(r["b"])): r["value"] for r in rows}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def initialize_210ma_state(common, a1, metadata_rows, cfg: R38Config) -> R38RuntimeState:
    r34.validate_r3(cfg, a1)
    metadata = {r["species_id"]: r for r in metadata_rows}
    root_ids = [str(x) for x in common["species_id"].tolist()]
    guild0 = common["guild_id"].astype(int)
    component_ids, root_species, guild, pop = r2.partition_components(
        root_ids, common["species_population"].astype(float), guild0, cfg.occupancy_floor
    )
    current_species = list(root_species)
    trait, va, gen = r2.init_traits(root_species, metadata)
    registry, child_counters = r21._initialize_registry(root_ids, guild0)
    bcfg = r34.barrier_cfg(cfg)
    env0 = bp.environment_at(ORIGIN_AGE_MA, a1, bcfg)
    hab = r34.habitats_r3(root_species, guild, trait, pop, metadata, env0, cfg)
    baselines = r21._initial_baselines(pop, current_species, hab, guild, env0, cfg.occupancy_floor)
    reduced, _ = initialize_minimum_information_state(va, current_species)
    snapshots = [{
        "age_ma": ORIGIN_AGE_MA,
        "elapsed_myr": 0.0,
        "species_richness": len(set(current_species)),
        "component_count": len(component_ids),
        "total_population": float(pop.sum()),
        "speciation_events_cumulative": 0,
        "extinction_events_cumulative": 0,
        "fission_events_cumulative": 0,
        "coalescence_events_cumulative": 0,
        "barrier_bracket": [env0["older_ma"], env0["younger_ma"]],
        "fractional_support_cells": int(np.count_nonzero((env0["land_support"] > 1e-9) & (env0["land_support"] < 1-1e-9))),
    }]
    out = R38RuntimeState(
        age_ma=ORIGIN_AGE_MA,
        elapsed_year=0.0,
        component_ids=list(component_ids),
        root_species=list(root_species),
        current_species=list(current_species),
        guild=np.asarray(guild, np.uint8),
        pop=np.asarray(pop, float),
        trait=np.asarray(trait, float),
        va=np.asarray(va, float),
        gen=np.asarray(gen, float),
        registry={str(k): dict(v) for k, v in registry.items()},
        child_counters=dict(child_counters),
        current_accessible=np.asarray(env0["accessible"], bool).copy(),
        baselines=json.loads(json.dumps(_jsonable(baselines))),
        ri_state={}, clock_state={}, ext_state={}, founder_state={}, vicariance_state={}, reconnection_state={},
        events=[], snapshots=snapshots, founder_stats_last=[],
        gene_flow_closure={"first_moment_conservation_max_abs": 0.0, "second_moment_conservation_max_abs": 0.0},
        topology_remap_mass=0.0,
        initial_total_population=float(pop.sum()),
        reduced_state=reduced,
    )
    out._lat = common["lat"].astype(float).copy(); out._lon = common["lon"].astype(float).copy()
    return out


def _context_for_state(st: R38RuntimeState, metadata: dict[str, dict], cfg: R38Config) -> _ClosedLoopContext:
    completed = int(round(st.elapsed_year / cfg.biology_cadence_years))
    # R3.7H wrappers derive the absolute age from record count. Placeholder
    # records preserve the original 210 Ma clock without serializing diagnostic history.
    return _ClosedLoopContext(
        state=st.reduced_state,
        component_ids=list(st.component_ids),
        root_species=list(st.root_species),
        current_species=list(st.current_species),
        generation_time=np.asarray(st.gen, float).copy(),
        metadata=metadata,
        cfg=cfg,
        records=[{} for _ in range(completed)],
        coalescence_events=[],
    )


def advance_state(st: R38RuntimeState, a1, metadata_rows, cfg: R38Config, end_age_ma: float) -> tuple[R38RuntimeState, list[dict[str, Any]]]:
    if end_age_ma >= st.age_ma - 1e-12:
        raise ValueError("R3.8 continuation must move forward in time toward lower Ma")
    if end_age_ma < cfg.end_age_ma - 1e-12:
        raise ValueError("requested end age is outside configured R3.8 horizon")
    metadata = {r["species_id"]: r for r in metadata_rows}
    lat = np.asarray(a1["lat"], float) if "lat" in a1.files else None
    lon = np.asarray(a1["lon"], float) if "lon" in a1.files else None
    # The authoritative grid coordinates live in common state, not A1.  They are
    # attached by the caller as private attributes when using this low-level API.
    if not hasattr(st, "_lat") or not hasattr(st, "_lon"):
        raise RuntimeError("R3.8 runtime state missing static grid coordinates")
    lat = np.asarray(st._lat, float); lon = np.asarray(st._lon, float)
    bcfg = r34.barrier_cfg(cfg)
    ctx = _context_for_state(st, metadata, cfg)
    record_offset = len(ctx.records)

    component_ids = list(st.component_ids); root_species = list(st.root_species); current_species = list(st.current_species)
    guild = np.asarray(st.guild, np.uint8).copy(); pop = np.asarray(st.pop, float).copy()
    trait = np.asarray(st.trait, float).copy(); va = np.asarray(st.va, float).copy(); gen = np.asarray(st.gen, float).copy()
    registry = {str(k): dict(v) for k, v in st.registry.items()}; child_counters = defaultdict(int, st.child_counters)
    current_accessible = np.asarray(st.current_accessible, bool).copy()
    baselines = json.loads(json.dumps(_jsonable(st.baselines)))
    ri_state = dict(st.ri_state); clock_state = dict(st.clock_state); ext_state = json.loads(json.dumps(_jsonable(st.ext_state)))
    founder_state = json.loads(json.dumps(_jsonable(st.founder_state))); vicariance_state = json.loads(json.dumps(_jsonable(st.vicariance_state)))
    reconnection_state = {tuple(k): dict(v) for k, v in st.reconnection_state.items()}
    events = list(st.events); snapshots = list(st.snapshots); founder_stats_last = list(st.founder_stats_last)
    gene_flow_closure = dict(st.gene_flow_closure); topology_remap_mass = float(st.topology_remap_mass)
    elapsed = float(st.elapsed_year)

    target_elapsed = (ORIGIN_AGE_MA - float(end_age_ma)) * 1e6
    remaining = target_elapsed - elapsed
    nsteps = int(round(remaining / cfg.biology_cadence_years))
    if nsteps < 1 or abs(nsteps * cfg.biology_cadence_years - remaining) > 1e-6:
        raise ValueError("R3.8 end age must lie on the 125 kyr biology cadence")

    with _closed_loop_bindings(ctx):
        for _ in range(nsteps):
            elapsed += cfg.biology_cadence_years
            age = ORIGIN_AGE_MA - elapsed / 1e6
            env = bp.environment_at(age, a1, bcfg)
            if not np.array_equal(env["accessible"], current_accessible):
                pop, moved = r2.remap_to_land(pop, current_accessible, env["accessible"], lat, lon)
                topology_remap_mass += moved
                current_accessible = env["accessible"].copy()
                if moved > 0:
                    events.append({"event": "paleogeographic_support_loss_remap", "age_ma": float(age),
                                   "elapsed_year": float(elapsed), "remapped_population_mass": float(moved),
                                   "semantic_status": "D3_2C_EVENT_RECONSTRUCTED_CONSERVATIVE_SUPPORT_REMAP"})

            hab = r34.habitats_r3(root_species, guild, trait, pop, metadata, env, cfg)
            opportunity = r21._current_opportunities(hab, current_species, guild, env)
            targets = r21._demography_targets(pop, current_species, guild, registry, baselines, opportunity, env)
            pop = r21._apply_demography(pop, current_species, registry, metadata, targets, cfg.biology_cadence_years)
            pop, hab = r34._migration_subcycled_r3(pop, root_species, guild, trait, metadata, lat, lon, env,
                                                   cfg.biology_cadence_years, cfg)

            G_pre, _, _ = r34._pair_metrics_barrier_coupled(pop, trait, root_species, current_species, metadata, lat, lon, env, cfg)
            target = r2.selection_targets(pop, env["temperature_c"], env["aridity_index"])
            tr_before = trait.copy()
            selected = r2.select_traits(trait, va, target, root_species, metadata, cfg.biology_cadence_years, cfg)
            totals = pop.sum(axis=(1, 2))
            ri_before, _ = r21.pair_state_matrices(component_ids, current_species, ri_state, clock_state)
            root_idx, root_ids = r34._root_index(root_species)
            current_idx, _ = r34._root_index(current_species)
            trait, va, gene_flow_closure = r34.av.gene_flow_moment_mix(
                selected, va, totals, G_pre, ri_before, current_idx, r34._variance_cfg_d3_3a(cfg)
            )
            va, _ = r34.av.advance_nonflow_variance(
                va, tr_before, target, totals, gen, root_idx, root_ids, metadata,
                cfg.body_mass_scale, cfg.biology_cadence_years, r34._variance_cfg_d3_3a(cfg)
            )

            G, contact, td = r34._pair_metrics_barrier_coupled(pop, trait, root_species, current_species, metadata, lat, lon, env, cfg)
            ri_state, clock_state, ri, clock = r21.advance_pair_states(
                component_ids, current_species, gen, contact, td, ri_state, clock_state,
                cfg.biology_cadence_years, cfg)

            if cfg.persistent_reconnection_coalescence_enabled and r21._is_multiple(elapsed, cfg.reconnection_check_interval_years):
                reconnection_state, mature_reconnections = r34.update_reconnection_persistence_r33(
                    component_ids, current_species, contact, ri, clock, elapsed, reconnection_state, cfg)
                if mature_reconnections:
                    (component_ids, root_species, current_species, guild, pop, trait, va, gen,
                     ri_state, clock_state, reconnection_state, founder_state, vicariance_state,
                     coalescences) = r34.apply_mature_coalescences_r33(
                        component_ids=component_ids, root_species=root_species, current_species=current_species,
                        guild=guild, pop=pop, trait=trait, va=va, gen=gen,
                        ri_state=ri_state, clock_state=clock_state, mature=mature_reconnections,
                        reconnection_state=reconnection_state, founder_state=founder_state,
                        vicariance_state=vicariance_state, metadata=metadata,
                        elapsed_year=elapsed, age_ma=age, cfg=cfg)
                    if coalescences:
                        events.extend(coalescences)
                        hab = r34.habitats_r3(root_species, guild, trait, pop, metadata, env, cfg)
                        G, contact, td = r34._pair_metrics_barrier_coupled(pop, trait, root_species, current_species, metadata, lat, lon, env, cfg)
                        ri, clock = r21.pair_state_matrices(component_ids, current_species, ri_state, clock_state)

            if cfg.persistent_vicariance_fission_enabled and r21._is_multiple(elapsed, cfg.deme_fission_check_interval_years):
                conn = bp.effective_barrier_connectivity(hab, env["land_support"], bcfg)
                vicariance_state, mature = r34.update_vicariance_persistence_r3(
                    component_ids, pop, conn, root_species, elapsed, vicariance_state, cfg)
                if mature:
                    (component_ids, root_species, current_species, guild, pop, trait, va, gen,
                     ri_state, clock_state, fissions) = r34.apply_mature_fissions_r3(
                        component_ids=component_ids, root_species=root_species, current_species=current_species,
                        guild=guild, pop=pop, trait=trait, va=va, gen=gen, connectivity=conn,
                        lat=lat, lon=lon, ri_state=ri_state, clock_state=clock_state, mature=mature,
                        persistence=vicariance_state, elapsed_year=elapsed, age_ma=age, cfg=cfg)
                    if fissions:
                        events.extend(fissions)
                        for e in fissions:
                            vicariance_state.pop(e["parent_component_id"], None)
                        hab = r34.habitats_r3(root_species, guild, trait, pop, metadata, env, cfg)
                        G, contact, td = r34._pair_metrics_barrier_coupled(pop, trait, root_species, current_species, metadata, lat, lon, env, cfg)
                        ri, clock = r21.pair_state_matrices(component_ids, current_species, ri_state, clock_state)

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
                    hab = r34.habitats_r3(root_species, guild, trait, pop, metadata, env, cfg)
                    G, contact, td = r34._pair_metrics_barrier_coupled(pop, trait, root_species, current_species, metadata, lat, lon, env, cfg)
                    ri, clock = r21.pair_state_matrices(component_ids, current_species, ri_state, clock_state)

            if r21._is_multiple(elapsed, cfg.speciation_check_interval_years):
                births, founder_state, founder_stats_last = r21.maybe_speciate_founder(
                    current_species=current_species, root_species=root_species, component_ids=component_ids,
                    pop=pop, va=va, gen=gen, metadata=metadata, contact=contact, td=td, ri=ri, clock=clock,
                    registry=registry, child_counters=child_counters, elapsed_year=elapsed, age_ma=age,
                    founder_state=founder_state, cfg=cfg)
                if births:
                    events.extend(births)
                    hab = r34.habitats_r3(root_species, guild, trait, pop, metadata, env, cfg)
                    touched = sorted({e["parent_species_id"] for e in births} | {e["daughter_species_id"] for e in births})
                    r21._reset_species_baselines(touched, pop=pop, current_species=current_species, hab=hab, guild=guild,
                                                 env=env, baselines=baselines, elapsed_year=elapsed,
                                                 occupancy_floor=cfg.occupancy_floor)
                    for sid in touched:
                        ext_state.pop(sid, None)

            if r21._is_multiple(elapsed, cfg.snapshot_interval_years) or abs(age - end_age_ma) < 1e-9:
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
                    "coalescence_events_cumulative": sum(1 for e in events if e["event"] == "deme_coalescence"),
                    "barrier_bracket": [env["older_ma"], env["younger_ma"]],
                    "fractional_support_cells": int(np.count_nonzero((env["land_support"] > 1e-9) & (env["land_support"] < 1-1e-9))),
                })

    if not np.allclose(va, ctx.state.va_within, atol=1e-13, rtol=0.0):
        raise RuntimeError("R3.8 canonical VA diverged from reduced state")
    if list(component_ids) != ctx.component_ids or list(root_species) != ctx.root_species or list(current_species) != ctx.current_species:
        raise RuntimeError("R3.8 lifecycle identity diverged from reduced-state binding")

    out = R38RuntimeState(
        age_ma=float(end_age_ma), elapsed_year=float(target_elapsed),
        component_ids=list(component_ids), root_species=list(root_species), current_species=list(current_species),
        guild=np.asarray(guild, np.uint8), pop=np.asarray(pop, float), trait=np.asarray(trait, float),
        va=np.asarray(va, float), gen=np.asarray(gen, float), registry={str(k): dict(v) for k, v in registry.items()},
        child_counters=dict(child_counters), current_accessible=np.asarray(current_accessible, bool), baselines=baselines,
        ri_state=dict(ri_state), clock_state=dict(clock_state), ext_state=ext_state, founder_state=founder_state,
        vicariance_state=vicariance_state, reconnection_state=reconnection_state, events=events, snapshots=snapshots,
        founder_stats_last=founder_stats_last, gene_flow_closure=gene_flow_closure,
        topology_remap_mass=topology_remap_mass, initial_total_population=st.initial_total_population,
        reduced_state=ctx.state,
    )
    out._lat = lat.copy(); out._lon = lon.copy()
    return out, ctx.records[record_offset:]


def state_projection(st: R38RuntimeState, metadata_rows, cfg: R38Config) -> dict[str, Any]:
    metadata = {r["species_id"]: r for r in metadata_rows}
    q = _normalized_q(st.reduced_state.va_within, st.root_species, metadata, cfg.body_mass_scale)
    return {
        "age_ma": float(st.age_ma),
        "elapsed_year": float(st.elapsed_year),
        "final_total_population": float(st.pop.sum()),
        "species_count": len(set(st.current_species)),
        "component_count": len(st.component_ids),
        "event_counts": _event_counts(st.events),
        "q_max": float(np.max(q)) if q.size else 0.0,
        "q_median": float(np.median(q)) if q.size else 0.0,
        "component_ids": list(st.component_ids),
        "component_root_species": list(st.root_species),
        "component_species": list(st.current_species),
        "trait": st.trait.tolist(),
        "va": st.va.tolist(),
        "generation_time": st.gen.tolist(),
    }



def save_runtime_state(st: R38RuntimeState, json_path: Path, cfg: R38Config, seal_sha256: str, schema: str = RUNTIME_SCHEMA) -> dict[str, Any]:
    json_path = Path(json_path); json_path.parent.mkdir(parents=True, exist_ok=True)
    npz_path = json_path.with_suffix(".npz")
    np.savez_compressed(
        npz_path, guild=st.guild, population=st.pop, trait=st.trait, va=st.va, generation_time=st.gen,
        current_accessible=st.current_accessible.astype(np.uint8), reduced_va_within=st.reduced_state.va_within,
        reduced_ancestry_covariance=st.reduced_state.ancestry_covariance,
        reduced_neutral_segregation_potential=st.reduced_state.neutral_segregation_potential,
        reduced_adaptive_coordinate=st.reduced_state.adaptive_coordinate, lat=np.asarray(st._lat,float), lon=np.asarray(st._lon,float),
    )
    meta={
        "schema": schema, "stage": STAGE, "parent_stage": PARENT_STAGE, "age_ma": st.age_ma, "elapsed_year": st.elapsed_year,
        "canonical_runtime_seal_sha256": seal_sha256,
        "nominal_reduced_order_reference": {"label":"K_CENTER","K_eff":NOMINAL_K,"semantic_role":"OPERATIONAL_REDUCED_ORDER_COORDINATE_REFERENCE_NOT_PHYSICAL_CONSTANT"},
        "component_ids":st.component_ids,"root_species":st.root_species,"current_species":st.current_species,
        "registry":st.registry,"child_counters":st.child_counters,"baselines":st.baselines,
        "ri_state":_pair_dict_rows(st.ri_state),"clock_state":_pair_dict_rows(st.clock_state),
        "ext_state":st.ext_state,"founder_state":st.founder_state,"vicariance_state":st.vicariance_state,
        "reconnection_state":_pair_dict_rows(st.reconnection_state),"events":_jsonable(st.events),"snapshots":_jsonable(st.snapshots),
        "founder_stats_last":_jsonable(st.founder_stats_last),"gene_flow_closure":_jsonable(st.gene_flow_closure),
        "topology_remap_mass":st.topology_remap_mass,"initial_total_population":st.initial_total_population,
        "config":asdict(cfg),"npz_file":npz_path.name,
    }
    json_path.write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return {"json":str(json_path),"npz":str(npz_path),"json_sha256":_sha256(json_path),"npz_sha256":_sha256(npz_path)}


def load_runtime_state(json_path: Path, expected_schema: str | None = None) -> R38RuntimeState:
    json_path=Path(json_path); meta=json.loads(json_path.read_text(encoding="utf-8"))
    if expected_schema is not None and meta.get("schema") != expected_schema:
        raise RuntimeError("R3.8 runtime-state schema mismatch")
    if meta.get("stage") != STAGE:
        raise RuntimeError("R3.8 runtime-state stage mismatch")
    z=np.load(json_path.parent/meta["npz_file"],allow_pickle=False)
    st=R38RuntimeState(
        age_ma=float(meta["age_ma"]),elapsed_year=float(meta["elapsed_year"]),component_ids=list(meta["component_ids"]),
        root_species=list(meta["root_species"]),current_species=list(meta["current_species"]),guild=z["guild"].astype(np.uint8),
        pop=z["population"].astype(float),trait=z["trait"].astype(float),va=z["va"].astype(float),gen=z["generation_time"].astype(float),
        registry={str(k):dict(v) for k,v in meta["registry"].items()},child_counters={str(k):int(v) for k,v in meta["child_counters"].items()},
        current_accessible=z["current_accessible"].astype(bool),baselines=meta["baselines"],
        ri_state={k:float(v) for k,v in _pair_dict_from_rows(meta["ri_state"]).items()},clock_state={k:float(v) for k,v in _pair_dict_from_rows(meta["clock_state"]).items()},
        ext_state=meta["ext_state"],founder_state=meta["founder_state"],vicariance_state=meta["vicariance_state"],
        reconnection_state={k:dict(v) for k,v in _pair_dict_from_rows(meta["reconnection_state"]).items()},
        events=list(meta["events"]),snapshots=list(meta["snapshots"]),founder_stats_last=list(meta["founder_stats_last"]),
        gene_flow_closure=dict(meta["gene_flow_closure"]),topology_remap_mass=float(meta["topology_remap_mass"]),
        initial_total_population=float(meta["initial_total_population"]),reduced_state=ReducedGeneticLifecycleState(
            z["reduced_va_within"].astype(float),z["reduced_ancestry_covariance"].astype(float),z["reduced_neutral_segregation_potential"].astype(float),z["reduced_adaptive_coordinate"].astype(float)),
    )
    st._lat=z["lat"].astype(float); st._lon=z["lon"].astype(float); return st


def compare_runtime_states(a: R38RuntimeState, b: R38RuntimeState, atol: float = 2e-12) -> dict[str, Any]:
    arr_names=("guild","pop","trait","va","gen","current_accessible")
    arrays={}; ok=True
    for name in arr_names:
        aa=np.asarray(getattr(a,name)); bb=np.asarray(getattr(b,name)); shape=aa.shape==bb.shape
        if aa.dtype==bool or bb.dtype==bool or np.issubdtype(aa.dtype,np.integer):
            same=shape and np.array_equal(aa,bb); err=0.0 if same else float("inf")
        else:
            err=float(np.max(np.abs(aa-bb))) if shape and aa.size else (0.0 if shape else float("inf")); same=shape and err<=atol
        arrays[name]={"same":bool(same),"max_abs_error":err}; ok &= bool(same)
    red={};
    for name in ("va_within","ancestry_covariance","neutral_segregation_potential","adaptive_coordinate"):
        aa=np.asarray(getattr(a.reduced_state,name)); bb=np.asarray(getattr(b.reduced_state,name)); shape=aa.shape==bb.shape
        err=float(np.max(np.abs(aa-bb))) if shape and aa.size else (0.0 if shape else float("inf")); same=shape and err<=atol
        red[name]={"same":bool(same),"max_abs_error":err}; ok &= bool(same)
    exact_fields=("component_ids","root_species","current_species","registry","child_counters","baselines","ri_state","clock_state","ext_state","founder_state","vicariance_state","reconnection_state","events","snapshots","founder_stats_last","gene_flow_closure")
    exact={name:getattr(a,name)==getattr(b,name) for name in exact_fields}
    ok &= all(exact.values())
    scalar={"age_ma":abs(a.age_ma-b.age_ma),"elapsed_year":abs(a.elapsed_year-b.elapsed_year),"topology_remap_mass":abs(a.topology_remap_mass-b.topology_remap_mass),"initial_total_population":abs(a.initial_total_population-b.initial_total_population)}
    ok &= all(v<=atol for v in scalar.values())
    return {"equivalent":bool(ok),"arrays":arrays,"reduced_state":red,"exact_fields":exact,"scalar_abs_errors":scalar,"atol":atol}

def save_checkpoint(st: R38RuntimeState, out_dir: Path, seal_sha256: str, cfg: R38Config) -> dict[str, Any]:
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    if abs(st.age_ma-CHECKPOINT_AGE_MA)>1e-12:
        raise ValueError("canonical R3.8 checkpoint must be materialized at exactly 150 Ma")
    stem="WORLD1_150Ma_CANONICAL_CONTINUATION_CHECKPOINT_v0_6D1_R3_8"
    return save_runtime_state(st,out_dir/f"{stem}.json",cfg,seal_sha256,CHECKPOINT_SCHEMA)


def load_checkpoint(json_path: Path) -> R38RuntimeState:
    st=load_runtime_state(json_path,CHECKPOINT_SCHEMA)
    if abs(st.age_ma-CHECKPOINT_AGE_MA)>1e-12:
        raise RuntimeError("R3.8 canonical checkpoint age mismatch")
    return st


def compare_projections(a: dict[str, Any], b: dict[str, Any], atol: float = 2e-11) -> dict[str, Any]:
    scalar_keys = ("age_ma", "elapsed_year", "final_total_population", "species_count", "component_count", "q_max", "q_median")
    scalars = {}
    ok = True
    for k in scalar_keys:
        av, bv = a[k], b[k]
        if isinstance(av, (int, np.integer)) and isinstance(bv, (int, np.integer)):
            same = int(av) == int(bv); err = 0.0 if same else float("inf")
        else:
            err = abs(float(av)-float(bv)); same = err <= atol
        scalars[k] = {"same": bool(same), "abs_error": err}; ok &= bool(same)
    identities = {}
    for k in ("component_ids", "component_root_species", "component_species", "event_counts"):
        same = a[k] == b[k]; identities[k] = bool(same); ok &= bool(same)
    arrays = {}
    for k in ("trait", "va", "generation_time"):
        aa=np.asarray(a[k],float); bb=np.asarray(b[k],float)
        shape_same=aa.shape==bb.shape
        err=float(np.max(np.abs(aa-bb))) if shape_same and aa.size else (0.0 if shape_same else float("inf"))
        same=shape_same and err<=atol; arrays[k]={"same":bool(same),"max_abs_error":err}; ok &= bool(same)
    return {"equivalent": bool(ok), "scalars": scalars, "identities": identities, "arrays": arrays, "atol": atol}


def compare_to_r37h_center_reference(st: R38RuntimeState, reference: dict[str, Any], metadata_rows, cfg: R38Config, atol: float = 2e-11) -> dict[str, Any]:
    proj = state_projection(st, metadata_rows, cfg)
    expected = {
        "age_ma": 150.0,
        "elapsed_year": 60_000_000.0,
        "final_total_population": float(reference["final_total_population"]),
        "species_count": int(reference["species_count"]),
        "component_count": int(reference["component_count"]),
        "event_counts": reference["event_counts"],
        "q_max": float(reference["final_q_max"]),
        "q_median": float(reference["final_q_median"]),
        "component_ids": reference["component_ids"],
        "component_root_species": reference["component_root_species"],
        "component_species": reference["component_species"],
        "trait": reference["trait"],
        "va": reference["va"],
        # generation_time was not exposed by the sealed R3.7H evidence payload;
        # it is covered by the R3.8 serialization/restart identity test instead.
        "generation_time": proj["generation_time"],
    }
    cmp = compare_projections(proj, expected, atol=atol)
    cmp["reference_semantics"] = "SEALED_R37H_K_CENTER_EXPOSED_STATE_EQUIVALENCE__HIDDEN_RESTART_STATE_COVERED_BY_R38_RESTART_IDENTITY"
    return cmp
