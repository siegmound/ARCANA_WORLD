from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
import json

import numpy as np

from arcana_worldsim.late_cenozoic.cha2_nested_50y import IntegratedLateCenozoicProviderC1
from arcana_worldsim.late_cenozoic.late_pleistocene_boundary import IntegratedLateCenozoicProviderC2
from arcana_worldsim.late_cenozoic.production_interface import D3LateCenozoicSubstrateAdapter

from . import r38_restartable_checkpoint as r38
from . import r313_longterm_postcha1_reassembly as r313
from . import r314_late_cenozoic_binding as r314

STAGE = "v0.6D1-R3.15"
PARENT_STAGE = "v0.6D1-R3.14_SEALED"
START_AGE_MA = 30.0
END_AGE_MA = 0.25
SMOKE_END_AGE_MA = 29.5
C2_BRIDGE_START_AGE_MA = 0.2
C2_RECENT_RESTART_AGE_MA = 0.12
EXPECTED_STEPS = 238
EXPECTED_SMOKE_STEPS = 4
SCHEMA = "ARCANA_R315_250KA_PRE_C2_BRIDGE_CHECKPOINT_V1"
SMOKE_SCHEMA = "ARCANA_R315_SECULAR_BIOLOGY_SMOKE_CHECKPOINT_V1"
SUMMARY_SCHEMA = "ARCANA_R315_LATE_CENOZOIC_SECULAR_BIOLOGY_REPLAY_V1"


@dataclass(frozen=True)
class R315Config(r38.R38Config):
    end_age_ma: float = END_AGE_MA
    late_cenozoic_secular_start_age_ma: float = START_AGE_MA
    pre_c2_bridge_biology_boundary_age_ma: float = END_AGE_MA
    c2_bridge_start_age_ma: float = C2_BRIDGE_START_AGE_MA
    recent_restart_age_ma: float = C2_RECENT_RESTART_AGE_MA
    fixed_biology_cadence_preserved: bool = True
    adaptive_clock_used_as_biology_timestep: bool = False
    endpoint_environment_sampling_semantics: str = (
        "R38_EXISTING_ENDPOINT_ENVIRONMENT_SAMPLE_ON_FIXED_125KYR_BIOLOGY_CADENCE"
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        if abs(self.end_age_ma - END_AGE_MA) > 1e-12:
            raise ValueError("R3.15 canonical endpoint is fixed at 250 ka")
        if abs(self.late_cenozoic_secular_start_age_ma - START_AGE_MA) > 1e-12:
            raise ValueError("R3.15 starts from the R3.14 30 Ma biology boundary")
        if abs(self.pre_c2_bridge_biology_boundary_age_ma - END_AGE_MA) > 1e-12:
            raise ValueError("R3.15 pre-C2 bridge biology boundary must remain 250 ka")
        if abs(self.c2_bridge_start_age_ma - C2_BRIDGE_START_AGE_MA) > 1e-12:
            raise ValueError("R3.15 C2 bridge start authority remains 200 ka")
        if abs(self.recent_restart_age_ma - C2_RECENT_RESTART_AGE_MA) > 1e-12:
            raise ValueError("R3.15 recent restart authority remains 120 ka")
        if not self.fixed_biology_cadence_preserved or self.adaptive_clock_used_as_biology_timestep:
            raise ValueError("R3.15 must preserve 125 kyr biology cadence and keep adaptive clock separate")


def _sha256(path: Path) -> str:
    h = sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _required_r314_paths(root: Path) -> dict[str, Path]:
    bind = Path(root) / "local_bindings/v0_6D1_R3_14"
    return {
        "seal": Path(root) / "R3_14_SEAL_SUMMARY.json",
        "formal_audit": Path(root) / "outputs/v0_6D1_R3_14/FORMAL_AUDIT_SEALED_v0_6D1_R3_14.json",
        "binding_summary": bind / "R3_14_LATE_CENOZOIC_BINDING_SUMMARY.json",
        "clock": bind / "R3_14_ADAPTIVE_CLOCK_C2_30Ma_TO_BOOK.json",
        "sealed_root": bind / "v0_6_1_SEALED_MINIMAL",
        "b1": bind / "v0_6_4B1/exact_120ka_A1_boundary_state.npz",
        "b2": bind / "v0_6_4B2/relative_eustatic_shoreline_anomaly_120ka_A1.npz",
        "r313_checkpoint": Path(root) / "local_runs/v0_6D1_R3_13/WORLD1_H0_30Ma_LONG_TERM_POST_CHA1_DIVERSIFICATION_REASSEMBLY_CHECKPOINT_v0_6D1_R3_13.json",
    }


def validate_parent_r314_authority(root: Path) -> dict[str, Any]:
    root = Path(root)
    p = _required_r314_paths(root)
    for key, path in p.items():
        if key == "sealed_root":
            if not path.is_dir():
                raise RuntimeError(f"R3.15 requires R3.14 materialized sealed root: {path}")
        elif not path.is_file():
            raise RuntimeError(f"R3.15 requires R3.14 SEALED evidence: missing {path}")

    seal = json.loads(p["seal"].read_text(encoding="utf-8"))
    audit = json.loads(p["formal_audit"].read_text(encoding="utf-8"))
    summary = json.loads(p["binding_summary"].read_text(encoding="utf-8"))
    clock_disk = json.loads(p["clock"].read_text(encoding="utf-8"))

    expected_verdict = "PASS_R314_LATE_CENOZOIC_PROVIDER_C2_AND_ADAPTIVE_CLOCK_BOUND__30MA_H0_BIOLOGY_RESTART_BOUNDARY_SEALED"
    if seal.get("stage") != "v0.6D1-R3.14" or seal.get("verdict") != expected_verdict:
        raise RuntimeError("R3.14 seal verdict is not authoritative")
    if audit.get("verdict") != expected_verdict or audit.get("checks") != "129/129":
        raise RuntimeError("R3.14 formal sealed audit is not authoritative")
    boundary = seal.get("boundary", {})
    if abs(float(boundary.get("age_ma", -1.0)) - START_AGE_MA) > 1e-12:
        raise RuntimeError("R3.14 biology restart boundary is not 30 Ma")
    if boundary.get("event_side") != "LATE_CENOZOIC_C2_PROVIDER_BOUND__BIOLOGY_NOT_ADVANCED":
        raise RuntimeError("R3.14 boundary semantics mismatch")
    if int(boundary.get("species", -1)) != 111 or int(boundary.get("components", -1)) != 219:
        raise RuntimeError("R3.14 boundary cardinality mismatch")
    if not bool(seal.get("adaptive_clock", {}).get("production_replay_ready")):
        raise RuntimeError("R3.14 adaptive clock is not production replay ready")
    if seal.get("adaptive_clock", {}).get("production_replay_ready_scope") != "COARSE_NATURAL_HISTORY_30MA_TO_BOOK_WITH_C2_BOUNDARY_CONTINUATION":
        raise RuntimeError("R3.14 adaptive clock scope mismatch")

    hashes = seal.get("artifact_hashes", {})
    checks = {
        "binding_summary": p["binding_summary"],
        "adaptive_clock_json": p["clock"],
        "B1_boundary_npz": p["b1"],
        "B2_boundary_npz": p["b2"],
        "formal_audit": p["formal_audit"],
    }
    actual_hashes = {}
    for key, path in checks.items():
        got = _sha256(path); actual_hashes[key] = got
        want = hashes.get(key)
        if want and got != want:
            raise RuntimeError(f"R3.14 {key} SHA mismatch: {got} != {want}")

    vproof = r314.b1.verify_v061_sealed_root(p["sealed_root"])
    if vproof != r314.EXPECTED_V061_SHA256:
        raise RuntimeError("R3.14 materialized v0.6.1 payload hash binding changed")

    a1 = r314.load_a1(root)
    c2, clock = r314.build_bound_provider_and_clock(a1, p["sealed_root"], p["b1"], p["b2"])
    if not isinstance(c2, IntegratedLateCenozoicProviderC2) or not isinstance(c2.parent, IntegratedLateCenozoicProviderC1):
        raise RuntimeError("R3.14 C2->C1 binding type guard failed")
    cs = r314.summarize_clock(clock)
    val = cs["validation"]
    if val.get("status") != "PASS" or not val.get("production_replay_ready"):
        raise RuntimeError("R3.14 rebuilt clock is not production-ready")
    if val.get("high_resolution_200ka_historical_paleoclimate_sealed") is not False:
        raise RuntimeError("R3.15 must preserve the R3.14 high-resolution paleoclimate non-claim")
    if val.get("c2_bridge_is_historical_glacial_chronology") is not False:
        raise RuntimeError("R3.15 must preserve the R3.14 C2 historical-chronology non-claim")

    rebuilt_payload = {
        "status": clock["status"],
        "age_ma": [float(x) for x in np.asarray(clock["age_ma"]).tolist()],
        "model_seconds": [int(x) for x in np.asarray(clock["model_seconds"]).tolist()],
        "intervals": list(clock["intervals"]),
        "validation": clock["validation"],
    }
    if rebuilt_payload != clock_disk:
        raise RuntimeError("R3.14 adaptive clock disk serialization does not match rebuilt authority")
    if summary.get("adaptive_clock") != cs:
        raise RuntimeError("R3.14 binding summary clock does not match rebuilt authority")

    state = r313.load_checkpoint(p["r313_checkpoint"], smoke=False)
    if abs(float(state.age_ma) - START_AGE_MA) > 1e-12:
        raise RuntimeError("R3.14 biology state is not the R3.13 30 Ma checkpoint")
    if len(set(state.current_species)) != 111 or len(state.component_ids) != 219:
        raise RuntimeError("R3.14 biology state cardinality drifted from R3.13")
    if abs(float(state.pop.sum()) - float(boundary.get("population"))) > 1e-9:
        raise RuntimeError("R3.14 biology population does not match sealed boundary")

    return {
        "state": state,
        "a1": a1,
        "c2": c2,
        "clock": clock,
        "seal_verdict": expected_verdict,
        "seal_sha256": _sha256(p["seal"]),
        "formal_audit_sha256": _sha256(p["formal_audit"]),
        "artifact_hashes": actual_hashes,
        "v061_payload_hashes": dict(vproof),
        "binding_summary_sha256": _sha256(p["binding_summary"]),
        "clock_sha256": _sha256(p["clock"]),
    }


class R315D3EnvironmentAdapter:
    """R3.14 C2 -> exact D3 substrate schema, without changing biology cadence."""

    def __init__(self, a1: Mapping[str, Any], c2: IntegratedLateCenozoicProviderC2):
        self.a1 = a1
        self.c2 = c2
        self.d3 = D3LateCenozoicSubstrateAdapter(a1, c2)

    def state_at_age(self, age_ma: float) -> dict[str, Any]:
        age = float(age_ma)
        if age < END_AGE_MA - 1e-12 or age > START_AGE_MA + 1e-12:
            raise ValueError("R3.15 adapter is scoped to 30 Ma -> 250 ka only")
        if age <= C2_BRIDGE_START_AGE_MA + 1e-12:
            raise ValueError("R3.15 forbids entering the C2 200->120 ka bridge")
        out = dict(self.d3.state_at_age(age))
        # R3.8 snapshots expect bracket labels. C2 is a continuous governed
        # provider here, so the biological forcing sample is its exact age state.
        out.update({
            "older_ma": age,
            "younger_ma": age,
            "older_index": -1,
            "younger_index": -1,
            "phase": 0.0,
            "topology": "R314_C2_LATE_CENOZOIC_SECULAR_PROVIDER",
            "paleogeographic_history_provider": "R314_C2_BOUND_LATE_CENOZOIC_PROVIDER",
            "biology_forcing_sample_semantics": "ENDPOINT_STATE_ON_FIXED_125KYR_R38_CADENCE",
            "adaptive_clock_checkpoint_promoted_to_biology_step": False,
        })
        return out


@contextmanager
def patched_r38_late_cenozoic_environment(adapter: R315D3EnvironmentAdapter):
    original = r38.bp.environment_at

    def bound_environment_at(age_ma: float, a1: Any, cfg: Any) -> dict[str, Any]:
        return adapter.state_at_age(float(age_ma))

    r38.bp.environment_at = bound_environment_at
    try:
        yield
    finally:
        r38.bp.environment_at = original


def validate_30ma_full_d3_substrate_handoff(a1: Mapping[str, Any], adapter: R315D3EnvironmentAdapter,
                                             cfg: R315Config | None = None) -> dict[str, Any]:
    cfg = cfg or R315Config()
    old = r38.bp.environment_at(30.0, a1, r38.r34.barrier_cfg(cfg))
    new = adapter.state_at_age(30.0)
    fields = (
        "land_support", "accessible", "temperature_c", "aridity_index",
        "browse_forage", "low_forage", "wetland_forage", "total_edible_forage",
        "reference_population",
    )
    rows = {}
    exact = True
    for key in fields:
        aa = np.asarray(old[key]); bb = np.asarray(new[key])
        same = aa.shape == bb.shape and np.array_equal(aa, bb)
        err = 0.0 if same else (float(np.max(np.abs(aa.astype(float) - bb.astype(float)))) if aa.shape == bb.shape else float("inf"))
        rows[key] = {"exact": bool(same), "max_abs_error": err}
        exact &= bool(same)
    return {
        "age_ma": 30.0,
        "full_d3_substrate_identity_exact": bool(exact),
        "fields": rows,
        "biology_state_advanced_during_handoff_check": False,
    }


def biology_scheduler_separation_report(clock: Mapping[str, Any], cfg: R315Config | None = None) -> dict[str, Any]:
    cfg = cfg or R315Config()
    cadence_ma = float(cfg.biology_cadence_years) / 1e6
    steps = int(round((START_AGE_MA - END_AGE_MA) / cadence_ma))
    ages = START_AGE_MA - np.arange(steps + 1, dtype=float) * cadence_ma
    if abs(float(ages[-1]) - END_AGE_MA) > 1e-12:
        raise RuntimeError("R3.15 biology boundary arithmetic drift")
    c2_ages = np.asarray(clock["age_ma"], dtype=float)
    contains_200 = bool(np.any(np.isclose(c2_ages, C2_BRIDGE_START_AGE_MA, atol=1e-12, rtol=0)))
    contains_120 = bool(np.any(np.isclose(c2_ages, C2_RECENT_RESTART_AGE_MA, atol=1e-12, rtol=0)))
    next_age = END_AGE_MA - cadence_ma
    return {
        "biology_cadence_years": float(cfg.biology_cadence_years),
        "biology_interval_count": int(steps),
        "biology_checkpoint_count": int(steps + 1),
        "biology_start_age_ma": START_AGE_MA,
        "biology_end_age_ma": END_AGE_MA,
        "all_r315_biology_checkpoints_older_than_c2_bridge_start": bool(np.all(ages > C2_BRIDGE_START_AGE_MA + 1e-12)),
        "adaptive_clock_contains_200ka": contains_200,
        "adaptive_clock_contains_120ka": contains_120,
        "adaptive_clock_checkpoint_promoted_to_biology_step": False,
        "adaptive_clock_used_as_biology_timestep": False,
        "fixed_r37i_r38_biology_cadence_preserved": True,
        "c2_200_120ka_bridge_crossed": False,
        "recent_120ka_restart_crossed": False,
        "next_nominal_biology_checkpoint_age_ma": float(next_age),
        "next_nominal_biology_step_would_cross_c2_200ka_bridge_start": bool(END_AGE_MA > C2_BRIDGE_START_AGE_MA > next_age),
        "stop_reason": (
            "250KA_IS_LAST_125KYR_BIOLOGY_BOUNDARY_BEFORE_200KA_C2_BRIDGE; "
            "NO_UNAUTHORIZED_ENVIRONMENTAL_SUBSTEP_TO_BIOLOGY_STEP_PROMOTION"
        ),
    }


def run_secular_biology(parent_state: r38.R38RuntimeState, a1: Mapping[str, Any], metadata_rows: list[dict[str, Any]],
                         c2: IntegratedLateCenozoicProviderC2,
                         cfg: R315Config | None = None, end_age_ma: float = END_AGE_MA):
    cfg = cfg or R315Config()
    if abs(float(parent_state.age_ma) - START_AGE_MA) > 1e-12:
        raise ValueError("R3.15 must start from the exact R3.14/R3.13 30 Ma biology state")
    if end_age_ma < END_AGE_MA - 1e-12:
        raise ValueError("R3.15 may not cross the 250 ka pre-C2 bridge biology boundary")
    if end_age_ma <= C2_BRIDGE_START_AGE_MA + 1e-12:
        raise ValueError("R3.15 may not enter the C2 200->120 ka bridge")
    remaining = (START_AGE_MA - float(end_age_ma)) * 1e6
    n = int(round(remaining / cfg.biology_cadence_years))
    if n < 1 or abs(n * cfg.biology_cadence_years - remaining) > 1e-6:
        raise ValueError("R3.15 endpoint must lie on the existing 125 kyr biology cadence")
    st = r313.r312.r311._clone_state(parent_state)
    adapter = R315D3EnvironmentAdapter(a1, c2)
    with patched_r38_late_cenozoic_environment(adapter):
        return r38.advance_state(st, a1, metadata_rows, cfg, float(end_age_ma))


def event_counts(st):
    return r313.event_counts(st)


def delta_event_counts(before, after):
    return r313.delta_event_counts(before, after)


def invariant_report(st, metadata_rows, cfg):
    return r313.invariant_report(st, metadata_rows, cfg)


def species_counts_by_guild(st):
    return r313.species_counts_by_guild(st)


def _save_state_arrays(st: r38.R38RuntimeState, npz_path: Path) -> None:
    np.savez_compressed(
        npz_path,
        guild=st.guild, population=st.pop, trait=st.trait, va=st.va, generation_time=st.gen,
        current_accessible=st.current_accessible.astype(np.uint8), reduced_va_within=st.reduced_state.va_within,
        reduced_ancestry_covariance=st.reduced_state.ancestry_covariance,
        reduced_neutral_segregation_potential=st.reduced_state.neutral_segregation_potential,
        reduced_adaptive_coordinate=st.reduced_state.adaptive_coordinate,
        lat=np.asarray(st._lat, float), lon=np.asarray(st._lon, float),
    )


def save_checkpoint(st: r38.R38RuntimeState, out_dir: Path, parent_authority: dict[str, Any], cfg: R315Config,
                    run_report: dict[str, Any], smoke: bool = False) -> dict[str, Any]:
    expected_age = SMOKE_END_AGE_MA if smoke else END_AGE_MA
    if abs(float(st.age_ma) - expected_age) > 1e-12:
        raise ValueError("R3.15 checkpoint age mismatch")
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    if smoke:
        stem = "WORLD1_H0_29P5Ma_R3_15_LATE_CENOZOIC_SECULAR_SMOKE_CHECKPOINT"
        schema = SMOKE_SCHEMA; event_side = "R3_15_SECULAR_SMOKE"
    else:
        stem = "WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15"
        schema = SCHEMA; event_side = "LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_200KA_BRIDGE"
    jp = out_dir / f"{stem}.json"; npzp = out_dir / f"{stem}.npz"
    _save_state_arrays(st, npzp)
    meta = {
        "schema": schema, "stage": STAGE, "parent_stage": PARENT_STAGE,
        "age_ma": float(st.age_ma), "elapsed_year": float(st.elapsed_year), "event_side": event_side,
        "parent_r314_authority": parent_authority,
        "component_ids": st.component_ids, "root_species": st.root_species, "current_species": st.current_species,
        "registry": st.registry, "child_counters": st.child_counters, "baselines": st.baselines,
        "ri_state": r38._pair_dict_rows(st.ri_state), "clock_state": r38._pair_dict_rows(st.clock_state),
        "ext_state": st.ext_state, "founder_state": st.founder_state, "vicariance_state": st.vicariance_state,
        "reconnection_state": r38._pair_dict_rows(st.reconnection_state), "events": r38._jsonable(st.events),
        "snapshots": r38._jsonable(st.snapshots), "founder_stats_last": r38._jsonable(st.founder_stats_last),
        "gene_flow_closure": r38._jsonable(st.gene_flow_closure), "topology_remap_mass": st.topology_remap_mass,
        "initial_total_population": st.initial_total_population, "config": asdict(cfg), "run_report": run_report,
        "npz_file": npzp.name,
        "governance": {
            "r314_c2_provider_used": True,
            "adaptive_clock_used_as_biology_timestep": False,
            "biology_cadence_years": float(cfg.biology_cadence_years),
            "c2_200_120ka_bridge_crossed": False,
            "recent_120ka_restart_crossed": False,
            "deep_biological_coupling": False,
            "cha1_reapplied": False,
            "post_cha1_lifecycle_thaw_reapplied": False,
            "richness_target_used": False,
            "guild_target_used": False,
            "cross_guild_transition_operator_activated": False,
            "scientific_parameters_changed": False,
        },
    }
    jp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"json": str(jp), "npz": str(npzp), "json_sha256": _sha256(jp), "npz_sha256": _sha256(npzp)}


def load_checkpoint(json_path: Path, smoke: bool = False) -> r38.R38RuntimeState:
    jp = Path(json_path); m = json.loads(jp.read_text(encoding="utf-8"))
    expected_schema = SMOKE_SCHEMA if smoke else SCHEMA
    expected_age = SMOKE_END_AGE_MA if smoke else END_AGE_MA
    if m.get("schema") != expected_schema or m.get("stage") != STAGE:
        raise RuntimeError("R3.15 checkpoint metadata mismatch")
    if abs(float(m.get("age_ma", -1.0)) - expected_age) > 1e-12:
        raise RuntimeError("R3.15 checkpoint boundary mismatch")
    z = np.load(jp.parent / m["npz_file"], allow_pickle=False)
    st = r38.R38RuntimeState(
        age_ma=float(m["age_ma"]), elapsed_year=float(m["elapsed_year"]), component_ids=list(m["component_ids"]),
        root_species=list(m["root_species"]), current_species=list(m["current_species"]), guild=z["guild"].astype(np.uint8),
        pop=z["population"].astype(float), trait=z["trait"].astype(float), va=z["va"].astype(float), gen=z["generation_time"].astype(float),
        registry={str(k): dict(v) for k, v in m["registry"].items()}, child_counters={str(k): int(v) for k, v in m["child_counters"].items()},
        current_accessible=z["current_accessible"].astype(bool), baselines=m["baselines"],
        ri_state={k: float(v) for k, v in r38._pair_dict_from_rows(m["ri_state"]).items()},
        clock_state={k: float(v) for k, v in r38._pair_dict_from_rows(m["clock_state"]).items()},
        ext_state=m["ext_state"], founder_state=m["founder_state"], vicariance_state=m["vicariance_state"],
        reconnection_state={k: dict(v) for k, v in r38._pair_dict_from_rows(m["reconnection_state"]).items()},
        events=list(m["events"]), snapshots=list(m["snapshots"]), founder_stats_last=list(m["founder_stats_last"]),
        gene_flow_closure=dict(m["gene_flow_closure"]), topology_remap_mass=float(m["topology_remap_mass"]),
        initial_total_population=float(m["initial_total_population"]),
        reduced_state=r38.ReducedGeneticLifecycleState(
            z["reduced_va_within"].astype(float), z["reduced_ancestry_covariance"].astype(float),
            z["reduced_neutral_segregation_potential"].astype(float), z["reduced_adaptive_coordinate"].astype(float),
        ),
    )
    st._lat = z["lat"].astype(float); st._lon = z["lon"].astype(float)
    return st
