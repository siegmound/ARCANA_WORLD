from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from typing import Any
import numpy as np

import d3_additive_variance_v0_6_3D3_3A as av
import rebased_natural_control_runtime_v0_6D1_R2 as r2
import rebased_natural_control_runtime_v0_6D1_R2_1 as r21
import rebased_natural_control_runtime_v0_6D1_R3_4 as r34
import rebased_natural_control_runtime_v0_6D1_R3_5 as r35

from .segregation_aware_admixture import (
    SegregationAwareAdmixtureConfig,
    build_exchange_transition,
    segregation_aware_gene_flow_mix,
    transform_segregation_potential,
)
from .segregation_potential_lifecycle import (
    ReducedGeneticLifecycleState,
    advance_directional_selection_coordinate,
    coalesce_group_state,
    fission_clone_state,
    initialize_minimum_information_state,
    remove_deme_state,
)
from .r37e_short_shadow_replay import (
    _add_drift_to_neutral_s,
    _drift_loss_from_components,
    _normalized_q,
    _state_summary,
)

STAGE = "v0.6D1-R3.7H"
PARENT_STAGE = "v0.6D1-R3.7G"

BRANCH_K = {
    "K_LOW": 37.614,
    "K_CENTER": 38.470,
    "K_HIGH": 41.002,
}


@dataclass(frozen=True)
class R37HClosedLoopConfig(r35.R35Config):
    """Closed-loop production-binding candidate.

    Unlike R3.7E-G shadow runs, the segregation-aware VA is returned to the
    parent runtime and therefore feeds the next trait-selection step.  This is
    deliberately still a validation candidate: a full 210->150 run and review
    are required before production promotion.
    """

    start_age_ma: float = 210.0
    end_age_ma: float = 150.0
    adaptive_k_eff: float = 38.470
    branch_label: str = "K_CENTER"
    segregation_recombination_fraction_per_generation: float = 0.5
    diagnostic_smoke: bool = False

    def __post_init__(self) -> None:
        if abs(self.start_age_ma - 210.0) > 1e-12:
            raise ValueError("R3.7H starts at 210 Ma")
        if self.diagnostic_smoke:
            if not (150.0 < self.end_age_ma < 210.0):
                raise ValueError("R3.7H diagnostic smoke must stay inside 210->150 Ma")
        elif abs(self.end_age_ma - 150.0) > 1e-12:
            raise ValueError("R3.7H governed full validation window is 210->150 Ma")
        if self.branch_label not in BRANCH_K:
            raise ValueError("unknown R3.7H K branch")
        if abs(float(self.adaptive_k_eff) - BRANCH_K[self.branch_label]) > 1e-12:
            raise ValueError("branch label/K value mismatch")
        if not (0.0 <= self.segregation_recombination_fraction_per_generation <= 0.5):
            raise ValueError("invalid recombination fraction")


@dataclass
class _ClosedLoopContext:
    state: ReducedGeneticLifecycleState
    component_ids: list[str]
    root_species: list[str]
    current_species: list[str]
    generation_time: np.ndarray
    metadata: dict[str, dict]
    cfg: R37HClosedLoopConfig
    records: list[dict[str, Any]]
    coalescence_events: list[dict[str, Any]]
    pending_flow: dict[str, Any] | None = None


def _initialize_context(common, metadata_rows, cfg: R37HClosedLoopConfig) -> tuple[_ClosedLoopContext, dict[str, Any]]:
    metadata = {r["species_id"]: r for r in metadata_rows}
    root_ids = [str(x) for x in common["species_id"].tolist()]
    guild0 = common["guild_id"].astype(int)
    component_ids, root_species, _guild, _pop = r2.partition_components(
        root_ids, common["species_population"].astype(float), guild0, cfg.occupancy_floor
    )
    current_species = list(root_species)
    _trait, va, gen = r2.init_traits(root_species, metadata)
    state, initdiag = initialize_minimum_information_state(va, current_species)
    initdiag = dict(initdiag)
    initdiag["production_runtime_bound"] = True
    initdiag["binding_status"] = "CLOSED_LOOP_VALIDATION_CANDIDATE_NOT_YET_PRODUCTION_AUTHORITY"
    return _ClosedLoopContext(
        state=state,
        component_ids=list(component_ids),
        root_species=list(root_species),
        current_species=list(current_species),
        generation_time=np.asarray(gen, dtype=float),
        metadata=metadata,
        cfg=cfg,
        records=[],
        coalescence_events=[],
    ), initdiag


def _replace_tuple_item(values: tuple, index: int, value):
    out = list(values)
    out[index] = value
    return tuple(out)


def _segregation_aware_coalescence(ctx: _ClosedLoopContext, **kwargs):
    component_ids = list(kwargs["component_ids"])
    root_species = list(kwargs["root_species"])
    current_species = list(kwargs["current_species"])
    guild = np.asarray(kwargs["guild"])
    pop = np.asarray(kwargs["pop"], dtype=float)
    trait = np.asarray(kwargs["trait"], dtype=float)
    va = np.asarray(kwargs["va"], dtype=float)
    gen = np.asarray(kwargs["gen"], dtype=float)
    ri_state = dict(kwargs["ri_state"])
    clock_state = dict(kwargs["clock_state"])
    mature = kwargs["mature"]
    reconnection_state = dict(kwargs["reconnection_state"])
    founder_state = dict(kwargs["founder_state"])
    vicariance_state = dict(kwargs["vicariance_state"])
    metadata = kwargs["metadata"]
    elapsed_year = float(kwargs["elapsed_year"])
    age_ma = float(kwargs["age_ma"])
    cfg = kwargs["cfg"]

    if va.shape != ctx.state.va_within.shape or not np.allclose(va, ctx.state.va_within, atol=1e-13, rtol=0.0):
        raise RuntimeError("closed-loop VA/state mismatch before coalescence")

    groups = r34._mature_reconnection_groups(component_ids, current_species, mature)
    if not groups:
        return (
            component_ids, root_species, current_species, guild, pop, trait, va, gen,
            ri_state, clock_state, reconnection_state, founder_state, vicariance_state, []
        )

    # Preserve pre-merge group identities because indices change after each merge.
    group_ids = [[str(component_ids[i]) for i in group] for group in groups]
    events: list[dict[str, Any]] = []

    for ids0 in group_ids:
        pos = {str(x): i for i, x in enumerate(component_ids)}
        if any(x not in pos for x in ids0):
            continue
        group = [pos[x] for x in ids0]
        if len(group) < 2:
            continue
        if len({str(current_species[i]) for i in group}) != 1:
            continue
        if len({str(root_species[i]) for i in group}) != 1:
            continue
        if len({int(guild[i]) for i in group}) != 1:
            continue

        masses = np.asarray([float(pop[i].sum()) for i in group], dtype=float)
        total = float(np.sum(masses))
        if total <= 0:
            raise RuntimeError("zero-mass closed-loop coalescence")
        survivor = r34._coalescence_survivor_index(group, component_ids)
        absorbed = [i for i in group if i != survivor]
        survivor_id = str(component_ids[survivor])
        absorbed_ids = [str(component_ids[i]) for i in absorbed]

        st_new, trait_new, keep, diag = coalesce_group_state(
            ctx.state, trait, pop.sum(axis=(1, 2)), group, survivor_index=survivor
        )
        newpos = {int(old): i for i, old in enumerate(keep.tolist())}
        si = newpos[survivor]
        root_sid = str(root_species[survivor])
        q = _normalized_q(st_new.va_within[si:si+1], [root_sid], metadata, cfg.body_mass_scale)
        max_q = float(np.max(q)) if q.size else 0.0
        if max_q > float(cfg.variance_ceiling_normalized) + 1e-12:
            # Hard ceiling remains authority; do not merge if the repaired genic
            # pooling itself would violate it.
            continue

        combined_pop = np.sum(pop[group], axis=0)
        pooled_gen = float(np.average(gen[group], weights=masses))
        rr, cc = r34._merge_pair_states(
            group, survivor, component_ids, root_species, masses, ri_state, clock_state
        )

        touched_ids = {str(component_ids[i]) for i in group}
        ids_new = [component_ids[i] for i in keep]
        roots_new = [root_species[i] for i in keep]
        cur_new = [current_species[i] for i in keep]
        guild_new = guild[keep].copy()
        pop_new = pop[keep].copy(); pop_new[si] = combined_pop
        gen_new = gen[keep].copy(); gen_new[si] = pooled_gen

        rr, cc = r21._purge_pair_state(ids_new, rr, cc)
        reconnection_new = {
            k: v for k, v in reconnection_state.items()
            if k[0] not in touched_ids and k[1] not in touched_ids
        }
        vicariance_new = {k: v for k, v in vicariance_state.items() if str(k) not in touched_ids}
        founder_new = {}
        for k, v in founder_state.items():
            comps = {str(x) for x in v.get("component_ids", [])}
            if comps & touched_ids:
                continue
            founder_new[k] = v

        event = {
            "event": "deme_coalescence",
            "elapsed_year": elapsed_year,
            "age_ma": age_ma,
            "retained_component_id": survivor_id,
            "absorbed_component_ids": absorbed_ids,
            "species_id": str(current_species[survivor]),
            "root_species_id": root_sid,
            "population": total,
            "population_conservation_error": float(total - np.sum(masses)),
            "first_moment_conservation_max_abs": float(diag["first_moment_conservation_max_abs"]),
            "genic_segregation_increment": list(diag["genic_segregation_increment"]),
            "ancestry_covariance_injection": list(diag["ancestry_covariance_injection"]),
            "max_normalized_va_after_pooling": max_q,
            "reconnection_minimum_persistence_years": float(cfg.reconnection_persistence_min_years),
            "semantic_status": "SEGREGATION_AWARE_PERSISTENT_SECONDARY_CONTACT_DEME_COALESCENCE_NOT_DESPECIATION",
        }
        events.append(event)
        ctx.coalescence_events.append(event)

        ctx.state = st_new
        component_ids = ids_new
        root_species = roots_new
        current_species = cur_new
        guild = guild_new
        pop = pop_new
        trait = trait_new
        va = st_new.va_within
        gen = gen_new
        ri_state, clock_state = rr, cc
        reconnection_state = reconnection_new
        founder_state = founder_new
        vicariance_state = vicariance_new

    ctx.component_ids = list(component_ids)
    ctx.root_species = list(root_species)
    ctx.current_species = list(current_species)
    ctx.generation_time = np.asarray(gen, dtype=float).copy()

    return (
        component_ids, root_species, current_species, guild, pop, trait,
        np.asarray(ctx.state.va_within, dtype=float), gen,
        ri_state, clock_state, reconnection_state, founder_state, vicariance_state, events
    )


@contextmanager
def _closed_loop_bindings(ctx: _ClosedLoopContext):
    orig_select = r2.select_traits
    orig_gf = av.gene_flow_moment_mix
    orig_nf = av.advance_nonflow_variance
    orig_fission = r34.apply_mature_fissions_r3
    orig_coal = r34.apply_mature_coalescences_r33
    orig_ext = r21.apply_extinctions
    orig_spec = r21.maybe_speciate_founder

    def select_wrapper(trait, va, target, root_species, metadata, dt, cfg):
        if va.shape != ctx.state.va_within.shape or not np.allclose(va, ctx.state.va_within, atol=1e-13, rtol=0.0):
            raise RuntimeError("closed-loop canonical VA diverged from reduced state before selection")
        selected = orig_select(trait, va, target, root_species, metadata, dt, cfg)
        h, _diag = advance_directional_selection_coordinate(
            ctx.state.adaptive_coordinate,
            trait,
            selected,
            effective_polygenic_dimension=ctx.cfg.adaptive_k_eff,
        )
        ctx.state = ReducedGeneticLifecycleState(
            ctx.state.va_within,
            ctx.state.ancestry_covariance,
            ctx.state.neutral_segregation_potential,
            h,
        )
        return selected

    def gf_wrapper(trait, va, population_total, gene_flow, intrinsic_ri, current_species_index, av_cfg):
        if va.shape != ctx.state.va_within.shape or not np.allclose(va, ctx.state.va_within, atol=1e-13, rtol=0.0):
            raise RuntimeError("closed-loop canonical VA diverged from reduced state before gene flow")
        admix_cfg = SegregationAwareAdmixtureConfig(
            maximum_total_exchange_fraction_per_deme=av_cfg.maximum_total_exchange_fraction_per_deme,
            recombination_fraction_per_generation=ctx.cfg.segregation_recombination_fraction_per_generation,
        )
        p, pdiag = build_exchange_transition(
            population_total, gene_flow, intrinsic_ri, current_species_index, admix_cfg
        )
        z_new, v_new, c_new, _s_total_new, diag = segregation_aware_gene_flow_mix(
            trait,
            ctx.state.va_within,
            ctx.state.ancestry_covariance,
            ctx.state.total_segregation_potential,
            population_total,
            gene_flow,
            intrinsic_ri,
            current_species_index,
            ctx.generation_time,
            ctx.cfg.biology_cadence_years,
            admix_cfg,
        )
        # Mean migration remains the old authority. Evaluate it only as a closure
        # oracle; its legacy variance output is discarded.
        z_legacy, _v_legacy, _diag_legacy = orig_gf(
            trait, va, population_total, gene_flow, intrinsic_ri, current_species_index, av_cfg
        )
        mean_err = float(np.max(np.abs(z_new - z_legacy))) if z_new.size else 0.0
        if mean_err > 2e-12:
            raise RuntimeError("closed-loop mean migration diverged from R3.4 authority")
        sn = transform_segregation_potential(ctx.state.neutral_segregation_potential, p, tolerance=1e-8)
        h = p @ ctx.state.adaptive_coordinate
        ctx.state = ReducedGeneticLifecycleState(v_new, c_new, sn, h)
        ctx.pending_flow = {"mean_authority_closure_max_abs": mean_err, "transition": pdiag, **diag}
        return z_new, v_new, {
            **diag,
            "mean_authority_closure_max_abs": mean_err,
            "variance_semantics": "SEGREGATION_AWARE_WITHIN_VA_PLUS_TRANSIENT_ANCESTRY_LD",
            "production_binding_stage": STAGE,
        }

    def nf_wrapper(va, trait_before_selection, targets, populations, generation_time,
                   root_idx, root_species_ids, metadata, body_mass_scale, dt_years, av_cfg):
        if va.shape != ctx.state.va_within.shape or not np.allclose(va, ctx.state.va_within, atol=1e-13, rtol=0.0):
            raise RuntimeError("closed-loop canonical VA diverged from reduced state before nonflow")
        actual, components = orig_nf(
            va, trait_before_selection, targets, populations, generation_time,
            root_idx, root_species_ids, metadata, body_mass_scale, dt_years, av_cfg
        )
        diag_cfg = replace(
            av_cfg,
            mutation_variance_ceiling_normalized=float(ctx.cfg.diagnostic_unclipped_ceiling),
        )
        unclipped, _ = orig_nf(
            va, trait_before_selection, targets, populations, generation_time,
            root_idx, root_species_ids, metadata, body_mass_scale, dt_years, diag_cfg
        )
        ctx.generation_time = np.asarray(generation_time, dtype=float).copy()
        drift_loss = _drift_loss_from_components(
            components, ctx.root_species, ctx.metadata, body_mass_scale
        )
        sn = _add_drift_to_neutral_s(ctx.state.neutral_segregation_potential, drift_loss)
        ctx.state = ReducedGeneticLifecycleState(
            actual,
            ctx.state.ancestry_covariance,
            sn,
            ctx.state.adaptive_coordinate,
        )
        q = _normalized_q(actual, ctx.root_species, ctx.metadata, body_mass_scale)
        qu = _normalized_q(unclipped, ctx.root_species, ctx.metadata, body_mass_scale)
        step = len(ctx.records) + 1
        ctx.records.append({
            "step_index": step - 1,
            "elapsed_year": float(step * ctx.cfg.biology_cadence_years),
            "age_ma": float(ctx.cfg.start_age_ma - step * ctx.cfg.biology_cadence_years / 1e6),
            "branch_label": ctx.cfg.branch_label,
            "K_eff": float(ctx.cfg.adaptive_k_eff),
            "max_q": float(np.max(q)) if q.size else 0.0,
            "median_q": float(np.median(q)) if q.size else 0.0,
            "max_unclipped_q": float(np.max(qu)) if qu.size else 0.0,
            "clipping_count": int(np.count_nonzero(qu > ctx.cfg.variance_ceiling_normalized + 1e-15)),
            "state": _state_summary(ctx.state, ctx.root_species, ctx.current_species, ctx.metadata, ctx.cfg),
            "flow": ctx.pending_flow,
        })
        return actual, components

    def fission_wrapper(**kwargs):
        old_ids = list(kwargs["component_ids"])
        res = orig_fission(**kwargs)
        new_ids = list(res[0]); events = res[-1]
        if events:
            ids = list(old_ids)
            for event in events:
                parent = str(event["parent_component_id"])
                daughter = str(event["daughter_component_id"])
                pi = ids.index(parent)
                ctx.state, _ = fission_clone_state(ctx.state, pi)
                ids.append(daughter)
            if ids != new_ids:
                raise RuntimeError("closed-loop fission ordering mismatch")
        ctx.component_ids = new_ids
        ctx.root_species = list(res[1])
        ctx.current_species = list(res[2])
        ctx.generation_time = np.asarray(res[7], dtype=float).copy()
        if not np.allclose(np.asarray(res[6], float), ctx.state.va_within, atol=1e-13, rtol=0.0):
            raise RuntimeError("fission canonical VA diverged from reduced state")
        return res

    def coal_wrapper(**kwargs):
        return _segregation_aware_coalescence(ctx, **kwargs)

    def ext_wrapper(species_ids, **kwargs):
        old_ids = list(kwargs["component_ids"])
        res = orig_ext(species_ids, **kwargs)
        new_ids = list(res[0])
        keep_set = set(new_ids)
        removed = [i for i, x in enumerate(old_ids) if x not in keep_set]
        if removed:
            ctx.state, _ = remove_deme_state(ctx.state, removed)
        ctx.component_ids = new_ids
        ctx.root_species = list(res[1])
        ctx.current_species = list(res[2])
        ctx.generation_time = np.asarray(res[7], dtype=float).copy()
        if not np.allclose(np.asarray(res[6], float), ctx.state.va_within, atol=1e-13, rtol=0.0):
            raise RuntimeError("extinction canonical VA diverged from reduced state")
        return res

    def spec_wrapper(**kwargs):
        out = orig_spec(**kwargs)
        ctx.current_species = list(kwargs["current_species"])
        return out

    r2.select_traits = select_wrapper
    av.gene_flow_moment_mix = gf_wrapper
    av.advance_nonflow_variance = nf_wrapper
    r34.apply_mature_fissions_r3 = fission_wrapper
    r34.apply_mature_coalescences_r33 = coal_wrapper
    r21.apply_extinctions = ext_wrapper
    r21.maybe_speciate_founder = spec_wrapper
    try:
        yield
    finally:
        r2.select_traits = orig_select
        av.gene_flow_moment_mix = orig_gf
        av.advance_nonflow_variance = orig_nf
        r34.apply_mature_fissions_r3 = orig_fission
        r34.apply_mature_coalescences_r33 = orig_coal
        r21.apply_extinctions = orig_ext
        r21.maybe_speciate_founder = orig_spec


def _event_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for event in events:
        name = str(event.get("event", "UNKNOWN"))
        out[name] = out.get(name, 0) + 1
    return out


def run_closed_loop_branch(common, a1, metadata_rows, cfg: R37HClosedLoopConfig) -> dict[str, Any]:
    ctx, initdiag = _initialize_context(common, metadata_rows, cfg)
    parent_cfg = r34.R34Config(**{
        k: v for k, v in asdict(cfg).items() if k in r34.R34Config.__dataclass_fields__
    })
    with _closed_loop_bindings(ctx):
        result = r34.run(common, a1, metadata_rows, parent_cfg)

    if not np.allclose(np.asarray(result["va"], float), ctx.state.va_within, atol=1e-13, rtol=0.0):
        raise RuntimeError("final canonical VA diverged from reduced genetic state")
    if list(result["component_ids"]) != ctx.component_ids:
        raise RuntimeError("final component identity mismatch")
    if list(result["component_root_species"]) != ctx.root_species:
        raise RuntimeError("final root-species identity mismatch")
    if list(result["component_species"]) != ctx.current_species:
        raise RuntimeError("final current-species identity mismatch")

    q = _normalized_q(ctx.state.va_within, ctx.root_species, ctx.metadata, cfg.body_mass_scale)
    expected_steps = int(round((cfg.start_age_ma - cfg.end_age_ma) * 1e6 / cfg.biology_cadence_years))
    peak_q = max((float(r["max_q"]) for r in ctx.records), default=0.0)
    clipping_contacts = int(sum(int(r["clipping_count"]) for r in ctx.records))
    valid = bool(
        len(ctx.records) == expected_steps
        and clipping_contacts == 0
        and np.all(np.isfinite(result["trait"]))
        and np.all(np.isfinite(result["va"]))
        and np.all(np.isfinite(result["population"]))
        and peak_q < cfg.variance_ceiling_normalized
    )
    return {
        "schema": "ARCANA_R37H_CLOSED_LOOP_BRANCH_V1",
        "stage": STAGE,
        "parent_stage": PARENT_STAGE,
        "branch_label": cfg.branch_label,
        "K_eff": float(cfg.adaptive_k_eff),
        "config": asdict(cfg),
        "initialization": initdiag,
        "closed_loop": True,
        "valid_biology_steps": len(ctx.records) == expected_steps,
        "expected_biology_steps": expected_steps,
        "biology_steps": len(ctx.records),
        "peak_q": peak_q,
        "clipping_contacts": clipping_contacts,
        "final_q_max": float(np.max(q)) if q.size else 0.0,
        "final_q_median": float(np.median(q)) if q.size else 0.0,
        "final_state": _state_summary(ctx.state, ctx.root_species, ctx.current_species, ctx.metadata, cfg),
        "final_total_population": float(result["final_total_population"]),
        "species_count": len(result["species_ids"]),
        "component_count": len(result["component_ids"]),
        "event_counts": _event_counts(result.get("events", [])),
        "events": result.get("events", []),
        "snapshots": result.get("snapshots", []),
        "trait": np.asarray(result["trait"], float).tolist(),
        "va": np.asarray(result["va"], float).tolist(),
        "component_ids": list(result["component_ids"]),
        "component_root_species": list(result["component_root_species"]),
        "component_species": list(result["component_species"]),
        "records": ctx.records,
        "closed_loop_gate_pass": valid,
        "authority": {
            "trait_response": "R3.4_SELECT_TRAITS_UNCHANGED_BUT_NOW_CONSUMES_SEGREGATION_AWARE_WITHIN_VA",
            "mean_migration": "R3.4_MEAN_EXCHANGE_AUTHORITY_UNCHANGED",
            "variance_migration": "R3.7_SEGREGATION_AWARE_WITHIN_VA_PLUS_ANCESTRY_LD",
            "nonflow_variance": "D3.3A_MU_B_DRIFT_AND_CEILING_UNCHANGED",
            "coalescence": "R3.7A_SEGREGATION_AWARE_POOLING_WITH_R3.3_RECONNECTION_TRIGGER",
            "fission_extinction_speciation": "PARENT_LIFECYCLE_AUTHORITY_UNCHANGED",
        },
        "governance": {
            "production_candidate_only": True,
            "production_runtime_replacement_authorized": False,
            "scalar_K_eff_production_authorized": False,
            "mu_b_or_ceiling_change_authorized": False,
            "final_promotion_requires_full_three_branch_review": True,
        },
    }


def compare_closed_loop_branches(branches: dict[str, dict[str, Any]]) -> dict[str, Any]:
    required = ("K_LOW", "K_CENTER", "K_HIGH")
    if tuple(sorted(branches)) != tuple(sorted(required)):
        raise ValueError("R3.7H comparison requires LOW/CENTER/HIGH")
    for label in required:
        if branches[label]["branch_label"] != label:
            raise ValueError("branch label mismatch")

    peak = {k: float(branches[k]["peak_q"]) for k in required}
    pop = {k: float(branches[k]["final_total_population"]) for k in required}
    species = {k: int(branches[k]["species_count"]) for k in required}
    components = {k: int(branches[k]["component_count"]) for k in required}
    events = {k: branches[k]["event_counts"] for k in required}
    all_valid = all(bool(branches[k]["closed_loop_gate_pass"]) for k in required)
    no_ceiling = all(int(branches[k]["clipping_contacts"]) == 0 for k in required)
    qualitative_ceiling_coherence = len({branches[k]["clipping_contacts"] > 0 for k in required}) == 1
    return {
        "all_branches_valid": all_valid,
        "all_branches_clear_of_ceiling": no_ceiling,
        "qualitative_ceiling_coherence": qualitative_ceiling_coherence,
        "peak_q_by_branch": peak,
        "max_peak_q_spread": max(peak.values()) - min(peak.values()),
        "final_population_by_branch": pop,
        "final_population_relative_span_vs_center": (
            (max(pop.values()) - min(pop.values())) / max(abs(pop["K_CENTER"]), 1e-30)
        ),
        "species_count_by_branch": species,
        "component_count_by_branch": components,
        "event_counts_by_branch": events,
        "species_count_exactly_equal": len(set(species.values())) == 1,
        "component_count_exactly_equal": len(set(components.values())) == 1,
        "event_counts_exactly_equal": events["K_LOW"] == events["K_CENTER"] == events["K_HIGH"],
    }
