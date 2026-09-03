from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from typing import Any
import copy
import numpy as np

import d3_additive_variance_v0_6_3D3_3A as av
import rebased_natural_control_runtime_v0_6D1_R2 as r2
import rebased_natural_control_runtime_v0_6D1_R2_1 as r21
import rebased_natural_control_runtime_v0_6D1_R3_4 as r34
import rebased_natural_control_runtime_v0_6D1_R3_5 as r35

from .r37d_selection_closure import AdaptiveSelectionShadowEnvelope
from .segregation_aware_admixture import (
    SegregationAwareAdmixtureConfig,
    build_exchange_transition,
    segregation_aware_gene_flow_mix,
    transform_segregation_potential,
    validate_segregation_potential,
)
from .segregation_potential_lifecycle import (
    ReducedGeneticLifecycleState,
    advance_directional_selection_coordinate,
    coalesce_group_state,
    fission_clone_state,
    initialize_minimum_information_state,
    remove_deme_state,
)

STAGE = "v0.6D1-R3.7E"
PARENT_STAGE = "v0.6D1-R3.7D"


@dataclass(frozen=True)
class R37EShortShadowConfig(r35.R35Config):
    start_age_ma: float = 210.0
    end_age_ma: float = 205.0
    adaptive_k_low: float = 37.614
    adaptive_k_center: float = 38.470
    adaptive_k_high: float = 41.002
    shadow_recombination_fraction_per_generation: float = 0.5
    diagnostic_smoke: bool = False

    def __post_init__(self) -> None:
        if abs(self.start_age_ma - 210.0) > 1e-12:
            raise ValueError("R3.7E starts at 210 Ma")
        if self.diagnostic_smoke:
            if not (205.0 <= self.end_age_ma < 210.0):
                raise ValueError("R3.7E diagnostic smoke must stay within 210->205 Ma")
        elif abs(self.end_age_ma - 205.0) > 1e-12:
            raise ValueError("R3.7E governed full short window is 210->205 Ma")
        if not (0 < self.adaptive_k_low <= self.adaptive_k_center <= self.adaptive_k_high):
            raise ValueError("invalid R3.7D K envelope")
        if not (0 <= self.shadow_recombination_fraction_per_generation <= 0.5):
            raise ValueError("invalid shadow recombination fraction")

    @property
    def envelope(self) -> AdaptiveSelectionShadowEnvelope:
        return AdaptiveSelectionShadowEnvelope(
            self.adaptive_k_low, self.adaptive_k_center, self.adaptive_k_high
        )


@dataclass
class _ShadowContext:
    states: dict[str, ReducedGeneticLifecycleState]
    k_values: dict[str, float]
    component_ids: list[str]
    current_species: list[str]
    generation_time: np.ndarray
    metadata: dict[str, dict]
    root_species: list[str]
    cfg: R37EShortShadowConfig
    records: list[dict[str, Any]]
    pending_selection: dict[str, Any] | None = None
    pending_flow: dict[str, Any] | None = None


def _normalized_q(va: np.ndarray, root_species: list[str], metadata: dict[str, dict], body_mass_scale: float) -> np.ndarray:
    rows=[]
    for i,sid in enumerate(root_species):
        sc=av.trait_scales(metadata[str(sid)],body_mass_scale)
        rows.append(av.normalize_variance(va[i],sc))
    return np.asarray(rows,float)


def _same_species_s_values(state: ReducedGeneticLifecycleState, current_species: list[str]) -> np.ndarray:
    s=state.total_segregation_potential
    vals=[]
    for i in range(state.deme_count):
        for j in range(i+1,state.deme_count):
            if str(current_species[i])==str(current_species[j]):
                vals.extend(s[i,j].tolist())
    return np.asarray(vals,float)


def _state_summary(state: ReducedGeneticLifecycleState, root_species: list[str], current_species: list[str], metadata: dict[str,dict], cfg: R37EShortShadowConfig) -> dict[str,Any]:
    q=_normalized_q(state.va_within,root_species,metadata,cfg.body_mass_scale)
    sv=_same_species_s_values(state,current_species)
    return {
        "deme_count":state.deme_count,
        "max_normalized_va":float(np.max(q)) if q.size else 0.0,
        "median_normalized_va":float(np.median(q)) if q.size else 0.0,
        "p99_normalized_va":float(np.quantile(q,0.99)) if q.size else 0.0,
        "count_ge_99pct_ceiling":int(np.count_nonzero(q >= cfg.telemetry_near_ceiling_fraction*cfg.variance_ceiling_normalized-1e-15)),
        "count_ge_ceiling":int(np.count_nonzero(q >= cfg.variance_ceiling_normalized-1e-15)),
        "same_species_S_max":float(np.max(sv)) if sv.size else 0.0,
        "same_species_S_median":float(np.median(sv)) if sv.size else 0.0,
        "ancestry_abs_total":float(np.sum(np.abs(state.ancestry_covariance))),
        "adaptive_coordinate_abs_max":float(np.max(np.abs(state.adaptive_coordinate))) if state.adaptive_coordinate.size else 0.0,
    }


def _initialize_context(common, metadata_rows, cfg:R37EShortShadowConfig) -> tuple[_ShadowContext,dict[str,Any]]:
    metadata={r["species_id"]:r for r in metadata_rows}
    root_ids=[str(x) for x in common["species_id"].tolist()]
    guild0=common["guild_id"].astype(int)
    component_ids,root_species,_guild,_pop=r2.partition_components(
        root_ids,common["species_population"].astype(float),guild0,cfg.occupancy_floor
    )
    current_species=list(root_species)
    _trait,va,gen=r2.init_traits(root_species,metadata)
    state,initdiag=initialize_minimum_information_state(va,current_species)
    labels=("K_LOW","K_CENTER","K_HIGH")
    kvals=dict(zip(labels,cfg.envelope.values()))
    states={k:state for k in labels}
    ctx=_ShadowContext(states,kvals,list(component_ids),list(current_species),np.asarray(gen,float),metadata,list(root_species),cfg,[])
    return ctx,initdiag


def _drift_loss_from_components(components:list[dict[str,Any]], root_species:list[str], metadata:dict[str,dict], body_mass_scale:float) -> np.ndarray:
    loss=[]
    for row,sid in zip(components,root_species):
        sc=av.trait_scales(metadata[str(sid)],body_mass_scale)
        qsel=np.asarray(row["q_after_selection"],float)
        qdr=np.asarray(row["q_after_drift"],float)
        loss.append(av.denormalize_variance(np.maximum(qsel-qdr,0.0),sc))
    return np.asarray(loss,float)


def _add_drift_to_neutral_s(sn:np.ndarray,loss:np.ndarray)->np.ndarray:
    out=np.asarray(sn,float).copy()
    for t in range(loss.shape[1]):
        inc=loss[:,t,None]+loss[None,:,t]
        np.fill_diagonal(inc,0.0)
        out[:,:,t]+=inc
    validate_segregation_potential(out,tolerance=1e-7)
    return out


def _parity(core_a:dict[str,Any],core_b:dict[str,Any])->dict[str,Any]:
    arr_keys=("population","trait","va","generation_time","ri","clock","contact","trait_distance")
    arr={}
    ok=True
    for k in arr_keys:
        a=np.asarray(core_a[k]); b=np.asarray(core_b[k])
        same=a.shape==b.shape and np.array_equal(a,b)
        arr[k]=bool(same); ok &= bool(same)
    list_keys=("component_ids","component_root_species","component_species","species_ids")
    lists={k: list(core_a[k])==list(core_b[k]) for k in list_keys}
    ok &= all(lists.values())
    events=core_a.get("events",[])==core_b.get("events",[])
    ok &= events
    return {"bit_exact_core_arrays":arr,"exact_identity_lists":lists,"events_exact":events,"all_core_parity":bool(ok)}


@contextmanager
def _shadow_bindings(ctx:_ShadowContext):
    orig_select=r2.select_traits
    orig_gf=av.gene_flow_moment_mix
    orig_nf=av.advance_nonflow_variance
    orig_fission=r34.apply_mature_fissions_r3
    orig_coal=r34.apply_mature_coalescences_r33
    orig_ext=r21.apply_extinctions
    orig_spec=r21.maybe_speciate_founder

    def select_wrapper(trait,va,target,root_species,metadata,dt,cfg):
        selected=orig_select(trait,va,target,root_species,metadata,dt,cfg)
        if len(ctx.component_ids)!=len(trait):
            raise RuntimeError("shadow/component dimension drift before selection")
        for label,k in ctx.k_values.items():
            st=ctx.states[label]
            h,diag=advance_directional_selection_coordinate(st.adaptive_coordinate,trait,selected,effective_polygenic_dimension=k)
            ctx.states[label]=ReducedGeneticLifecycleState(st.va_within,st.ancestry_covariance,st.neutral_segregation_potential,h)
        ctx.pending_selection={"trait_before":np.asarray(trait,float).copy(),"trait_selected":np.asarray(selected,float).copy()}
        return selected

    def gf_wrapper(trait,va,population_total,gene_flow,intrinsic_ri,current_species_index,av_cfg):
        zprod,vprod,diagprod=orig_gf(trait,va,population_total,gene_flow,intrinsic_ri,current_species_index,av_cfg)
        admix_cfg=SegregationAwareAdmixtureConfig(
            maximum_total_exchange_fraction_per_deme=av_cfg.maximum_total_exchange_fraction_per_deme,
            recombination_fraction_per_generation=ctx.cfg.shadow_recombination_fraction_per_generation,
        )
        p,pdiag=build_exchange_transition(population_total,gene_flow,intrinsic_ri,current_species_index,admix_cfg)
        flow_rows={}
        for label in ctx.k_values:
            st=ctx.states[label]
            zsh,vsh,csh,_stot,sd=segregation_aware_gene_flow_mix(
                trait,st.va_within,st.ancestry_covariance,st.total_segregation_potential,
                population_total,gene_flow,intrinsic_ri,current_species_index,ctx.generation_time,
                ctx.cfg.biology_cadence_years,admix_cfg,
            )
            if not np.allclose(zsh,zprod,atol=2e-12,rtol=0):
                raise RuntimeError("shadow mean migration diverged from D3.3A authority")
            sn=transform_segregation_potential(st.neutral_segregation_potential,p,tolerance=1e-8)
            h=p@st.adaptive_coordinate
            ctx.states[label]=ReducedGeneticLifecycleState(vsh,csh,sn,h)
            flow_rows[label]={"mean_closure_max_abs":float(np.max(np.abs(zsh-zprod))),**sd}
        ctx.pending_flow={"transition_shape":list(p.shape),"transition_diag":pdiag,"variants":flow_rows}
        return zprod,vprod,diagprod

    def nf_wrapper(va,trait_before_selection,targets,populations,generation_time,root_idx,root_species_ids,metadata,body_mass_scale,dt_years,av_cfg):
        prod,prodcomp=orig_nf(va,trait_before_selection,targets,populations,generation_time,root_idx,root_species_ids,metadata,body_mass_scale,dt_years,av_cfg)
        ctx.generation_time=np.asarray(generation_time,float).copy()
        variants={}
        for label in ctx.k_values:
            st=ctx.states[label]
            sout,comp=orig_nf(st.va_within,trait_before_selection,targets,populations,generation_time,root_idx,root_species_ids,metadata,body_mass_scale,dt_years,av_cfg)
            diagcfg=replace(av_cfg,mutation_variance_ceiling_normalized=float(ctx.cfg.diagnostic_unclipped_ceiling))
            sunclip,_=orig_nf(st.va_within,trait_before_selection,targets,populations,generation_time,root_idx,root_species_ids,metadata,body_mass_scale,dt_years,diagcfg)
            drift_loss=_drift_loss_from_components(comp,ctx.root_species,ctx.metadata,body_mass_scale)
            sn=_add_drift_to_neutral_s(st.neutral_segregation_potential,drift_loss)
            st2=ReducedGeneticLifecycleState(sout,st.ancestry_covariance,sn,st.adaptive_coordinate)
            ctx.states[label]=st2
            q=_normalized_q(sout,ctx.root_species,ctx.metadata,body_mass_scale)
            qu=_normalized_q(sunclip,ctx.root_species,ctx.metadata,body_mass_scale)
            variants[label]={
                "K_eff":ctx.k_values[label],
                "max_q":float(np.max(q)) if q.size else 0.0,
                "max_unclipped_q":float(np.max(qu)) if qu.size else 0.0,
                "clipping_count":int(np.count_nonzero(qu>ctx.cfg.variance_ceiling_normalized+1e-15)),
                "drift_va_loss_total":np.sum(drift_loss,axis=0).tolist(),
                "state":_state_summary(st2,ctx.root_species,ctx.current_species,ctx.metadata,ctx.cfg),
            }
        step=len(ctx.records)+1
        rec={
            "step_index":step-1,
            "elapsed_year":float(step*ctx.cfg.biology_cadence_years),
            "age_ma":float(ctx.cfg.start_age_ma-step*ctx.cfg.biology_cadence_years/1e6),
            "component_count_before_lifecycle":len(ctx.component_ids),
            "variants":variants,
            "flow":ctx.pending_flow,
        }
        ctx.records.append(rec)
        return prod,prodcomp

    def fission_wrapper(**kwargs):
        old_ids=list(kwargs["component_ids"])
        res=orig_fission(**kwargs)
        new_ids=list(res[0]); events=res[-1]
        if events:
            ids=list(old_ids)
            for e in events:
                parent=str(e["parent_component_id"]); daughter=str(e["daughter_component_id"])
                pi=ids.index(parent)
                for label in ctx.k_values:
                    ctx.states[label],_=fission_clone_state(ctx.states[label],pi)
                ids.append(daughter)
            if ids!=new_ids:
                raise RuntimeError("shadow fission ordering mismatch")
        ctx.component_ids=new_ids; ctx.root_species=list(res[1]); ctx.current_species=list(res[2]); ctx.generation_time=np.asarray(res[7],float).copy()
        return res

    def coal_wrapper(**kwargs):
        old_ids=list(kwargs["component_ids"])
        res=orig_coal(**kwargs)
        events=res[-1]
        if events:
            ids=list(old_ids)
            z=np.asarray(kwargs["trait"],float).copy()
            mass=np.asarray(kwargs["pop"],float).sum(axis=(1,2))
            for e in events:
                gids=[str(e["retained_component_id"]),*map(str,e["absorbed_component_ids"])]
                idx=[ids.index(x) for x in gids]
                survivor=ids.index(str(e["retained_component_id"]))
                keep_ref=None; zout_ref=None
                for label in ctx.k_values:
                    st,zout,keep,_=coalesce_group_state(ctx.states[label],z,mass,idx,survivor_index=survivor)
                    ctx.states[label]=st
                    if keep_ref is None: keep_ref=keep; zout_ref=zout
                total=float(np.sum(mass[idx])); newmass=mass[keep_ref].copy(); newpos={int(old):i for i,old in enumerate(keep_ref.tolist())}; newmass[newpos[survivor]]=total
                ids=[ids[i] for i in keep_ref]; z=zout_ref; mass=newmass
            if ids!=list(res[0]):
                raise RuntimeError("shadow coalescence ordering mismatch")
        ctx.component_ids=list(res[0]); ctx.root_species=list(res[1]); ctx.current_species=list(res[2]); ctx.generation_time=np.asarray(res[7],float).copy()
        return res

    def ext_wrapper(species_ids,**kwargs):
        old_ids=list(kwargs["component_ids"])
        res=orig_ext(species_ids,**kwargs)
        new_ids=list(res[0])
        removed=[i for i,x in enumerate(old_ids) if x not in set(new_ids)]
        if removed:
            for label in ctx.k_values:
                ctx.states[label],_=remove_deme_state(ctx.states[label],removed)
        ctx.component_ids=new_ids; ctx.root_species=list(res[1]); ctx.current_species=list(res[2]); ctx.generation_time=np.asarray(res[7],float).copy()
        return res

    def spec_wrapper(**kwargs):
        out=orig_spec(**kwargs)
        ctx.current_species=list(kwargs["current_species"])
        return out

    r2.select_traits=select_wrapper
    av.gene_flow_moment_mix=gf_wrapper
    av.advance_nonflow_variance=nf_wrapper
    r34.apply_mature_fissions_r3=fission_wrapper
    r34.apply_mature_coalescences_r33=coal_wrapper
    r21.apply_extinctions=ext_wrapper
    r21.maybe_speciate_founder=spec_wrapper
    try:
        yield
    finally:
        r2.select_traits=orig_select
        av.gene_flow_moment_mix=orig_gf
        av.advance_nonflow_variance=orig_nf
        r34.apply_mature_fissions_r3=orig_fission
        r34.apply_mature_coalescences_r33=orig_coal
        r21.apply_extinctions=orig_ext
        r21.maybe_speciate_founder=orig_spec


def _summarize_shadow(ctx:_ShadowContext,canonical:dict[str,Any]) -> dict[str,Any]:
    variants={label:_state_summary(st,ctx.root_species,ctx.current_species,ctx.metadata,ctx.cfg) for label,st in ctx.states.items()}
    qmax={label:[r["variants"][label]["max_q"] for r in ctx.records] for label in ctx.k_values}
    clip={label:sum(r["variants"][label]["clipping_count"] for r in ctx.records) for label in ctx.k_values}
    spread=[]
    for r in ctx.records:
        vals=[r["variants"][x]["max_q"] for x in ("K_LOW","K_CENTER","K_HIGH")]
        spread.append(max(vals)-min(vals))
    event_counts={}
    for e in canonical.get("events",[]): event_counts[e["event"]]=event_counts.get(e["event"],0)+1
    return {
        "window":{"start_age_ma":ctx.cfg.start_age_ma,"end_age_ma":ctx.cfg.end_age_ma,"biology_steps":len(ctx.records)},
        "K_envelope":{"K_LOW":ctx.k_values["K_LOW"],"K_CENTER":ctx.k_values["K_CENTER"],"K_HIGH":ctx.k_values["K_HIGH"]},
        "final_variants":variants,
        "trajectory_max_q":{"peak_by_variant":{k:max(v) if v else 0.0 for k,v in qmax.items()},"maximum_absolute_K_envelope_spread":max(spread) if spread else 0.0},
        "ceiling_contacts_by_variant":clip,
        "canonical_event_counts":event_counts,
        "component_count_final":len(ctx.component_ids),
        "species_count_final":len(set(ctx.current_species)),
        "governance":{
            "shadow_only":True,"canonical_write_allowed":False,"production_runtime_replacement_authorized":False,
            "scalar_K_eff_production_authorized":False,"direct_WorldSim_N_to_NEMO_N_mapping_authorized":False,
            "mu_b_or_ceiling_change_authorized":False,
            "recombination_fraction_is_reference_shadow_architecture_not_world1_constant":True,
        },
    }


def run_short_world1_shadow(common,a1,metadata_rows,cfg:R37EShortShadowConfig=R37EShortShadowConfig()) -> dict[str,Any]:
    # First run: untouched R3.5 is the canonical reference and supplies its own headroom telemetry.
    canonical=r35.run(common,a1,metadata_rows,cfg)
    ctx,initdiag=_initialize_context(common,metadata_rows,cfg)
    # Second run: exact R3.4 parent dynamics with observation-only shadow hooks.
    parent_cfg=r34.R34Config(**{k:v for k,v in asdict(cfg).items() if k in r34.R34Config.__dataclass_fields__})
    with _shadow_bindings(ctx):
        observed=r34.run(common,a1,metadata_rows,parent_cfg)
    parity=_parity(canonical,observed)
    if not parity["all_core_parity"]:
        raise RuntimeError("R3.7E shadow bindings changed canonical R3.5/R3.4 scientific state")
    summary=_summarize_shadow(ctx,canonical)
    legacy_peak=float(canonical["r35_headroom_summary"]["peak_after_homeostasis_q"])
    shadow_peaks={k:float(v) for k,v in summary["trajectory_max_q"]["peak_by_variant"].items()}
    no_clip=all(v==0 for v in summary["ceiling_contacts_by_variant"].values())
    valid_steps=(len(ctx.records)==int(round((cfg.start_age_ma-cfg.end_age_ma)*1e6/cfg.biology_cadence_years)))
    verdict=(
        "PASS_SHORT_WORLD1_ADAPTIVE_GENETIC_SHADOW_REPLAY__K_ENVELOPE_NO_QUALITATIVE_HEADROOM_DIVERGENCE__PRODUCTION_BINDING_NOT_YET_AUTHORIZED"
        if no_clip and valid_steps else
        "REVIEW_SHORT_WORLD1_ADAPTIVE_GENETIC_SHADOW_REPLAY"
    )
    return {
        "schema":"ARCANA_R37E_SHORT_WORLD1_ADAPTIVE_GENETIC_SHADOW_REPLAY_V1",
        "stage":STAGE,"parent_stage":PARENT_STAGE,"verdict":verdict,
        "config":asdict(cfg),"initialization":initdiag,"canonical_parity":parity,
        "canonical_r35_headroom":canonical["r35_headroom_summary"],
        "canonical_final":{"population":canonical["final_total_population"],"species_count":len(canonical["species_ids"]),"component_count":len(canonical["component_ids"])},
        "legacy_peak_q":legacy_peak,"shadow_peak_q":shadow_peaks,
        "shadow":summary,"records":ctx.records,
        "authority":{
            "trait_response":"R3.5/R3.4_EXISTING_SELECTION_AUTHORITY_UNCHANGED",
            "migration":"R3.4_CURRENT_SPECIES_BOUND_GENE_FLOW_AND_45PCT_CAP_UNCHANGED",
            "nonflow_variance":"D3.3A_MU_B_DRIFT_AND_CEILING_UNCHANGED",
            "deme_lifecycle":"R3.3/R3.2C_PARENT_EVENTS_ONLY",
            "adaptive_participation":"R3.7D_HIGH_N_SHADOW_ENVELOPE",
        },
    }
