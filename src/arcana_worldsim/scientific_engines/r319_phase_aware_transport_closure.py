from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence
import json

import numpy as np

from . import r38_restartable_checkpoint as r38
from . import r311_postcha1_recovery as r311
from . import r318_recent_exposure_transport_readiness as r318

STAGE = "v0.6D1-R3.19"
PARENT_STAGE = "v0.6D1-R3.18_SEALED"
START_AGE_MA = 0.125
END_AGE_MA = 0.0
TRANSPORT_BOUNDARY_AGE_MA = 0.0625
BIOLOGY_CADENCE_YEARS = 125_000.0
TRANSPORT_CADENCE_YEARS = 62_500.0
EXPECTED_BIOLOGY_STEPS = 1
EXPECTED_TRANSPORT_SUBSTEPS = 2
R318_SEALED_VERDICT = (
    "PASS_R318_120KA_TO_0_RECENT_H0_EXPOSURE_COMPLETED__"
    "125KA_BIOLOGY_PRESERVED_TRANSPORT_PHASE_READINESS_SEALED"
)
R318_READY_VERDICT = (
    "PASS_R318_120KA_TO_0_RECENT_H0_EXPOSURE_COMPLETED__"
    "125KA_BIOLOGY_PRESERVED_TRANSPORT_PHASE_OPERATOR_AUDIT_READY"
)
R318_ENVELOPE_SHA256 = "45f42200faa315ad7fe69f4fa8bcb1019c8f0c8dcb90fc2a18488bd40a9df58a"
R318_BUNDLE_SHA256 = "54172b22540b854115e82c041d4fb8dc2f0bdfbbc6784c669c145ba1db0c1a70"
R318_SUMMARY_SHA256 = "189007565f3f70c89b73e71bb4c23e9339bb392c550408a08b0d43c60f71317a"
VERDICT = (
    "PASS_CANONICAL_R319_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__"
    "0KA_NATURAL_CONTROL_BIOLOGY_CHECKPOINT_READY"
)
SCHEMA = "ARCANA_R319_WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_CHECKPOINT_V1"
SUMMARY_SCHEMA = "ARCANA_R319_H0_PRESENT_BIOLOGY_CLOSURE_SUMMARY_V1"

AVERAGED_FIELDS = r318.AVERAGED_FIELDS
_REQUIRED_GROUPS = (
    "full_125_to_0",
    "transport_phase1_125_to_62p5",
    "transport_phase2_62p5_to_0",
)


@dataclass(frozen=True)
class R319Config(r38.R38Config):
    end_age_ma: float = END_AGE_MA
    phase_aware_transport_enabled: bool = True
    phase1_transport_years: float = TRANSPORT_CADENCE_YEARS
    phase2_transport_years: float = TRANSPORT_CADENCE_YEARS
    macro_biology_years: float = BIOLOGY_CADENCE_YEARS
    support_remap_semantics: str = "R319_EXACT_ENDPOINT_TOPOLOGY_WITH_POST_TRANSPORT_RECONCILIATION"
    macro_nontransport_forcing_semantics: str = "R318_FULL_125_TO_0_TIME_AVERAGED_ENVIRONMENT"
    deep_biological_coupling: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if abs(self.end_age_ma - END_AGE_MA) > 1e-12:
            raise ValueError("R3.19 canonical endpoint is fixed at 0 ka")
        if not self.phase_aware_transport_enabled:
            raise ValueError("R3.19 requires phase-aware transport")
        if abs(self.phase1_transport_years - TRANSPORT_CADENCE_YEARS) > 1e-9 or abs(self.phase2_transport_years - TRANSPORT_CADENCE_YEARS) > 1e-9:
            raise ValueError("R3.19 preserves two 62.5 kyr transport substeps")
        if abs(self.macro_biology_years - BIOLOGY_CADENCE_YEARS) > 1e-9:
            raise ValueError("R3.19 preserves the 125 kyr biology cadence")
        if abs(float(self.transport_cadence_years) - TRANSPORT_CADENCE_YEARS) > 1e-9:
            raise ValueError("R3.19 inherited R3.8 transport cadence changed")
        if abs(float(self.biology_cadence_years) - BIOLOGY_CADENCE_YEARS) > 1e-9:
            raise ValueError("R3.19 inherited R3.8 biology cadence changed")
        if self.deep_biological_coupling:
            raise ValueError("R3.19 remains H0; Deep biological coupling must stay OFF")


def _sha256(path: Path) -> str:
    h = sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _r318_paths(root: Path) -> dict[str, Path]:
    run = Path(root) / "local_runs/v0_6D1_R3_18"
    return {
        "seal": Path(root) / "R3_18_SEAL_SUMMARY.json",
        "audit": Path(root) / "outputs/v0_6D1_R3_18/FORMAL_AUDIT_SEALED_v0_6D1_R3_18.json",
        "summary": run / "R3_18_RECENT_EXPOSURE_COMPLETION_SUMMARY.json",
        "envelope": run / "R3_18_RECENT_EXPOSURE_TRANSPORT_PHASE_READINESS_ENVELOPE.json",
        "bundle": run / "R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz",
    }


def validate_parent_r318_authority(root: Path) -> dict[str, Any]:
    root = Path(root)
    p = _r318_paths(root)
    for path in p.values():
        if not path.is_file():
            raise RuntimeError(f"R3.19 requires R3.18 SEALED evidence: missing {path}")
    seal = json.loads(p["seal"].read_text(encoding="utf-8"))
    audit = json.loads(p["audit"].read_text(encoding="utf-8"))
    summary = json.loads(p["summary"].read_text(encoding="utf-8"))
    envelope = json.loads(p["envelope"].read_text(encoding="utf-8"))
    if seal.get("stage") != "v0.6D1-R3.18" or seal.get("verdict") != R318_SEALED_VERDICT:
        raise RuntimeError("R3.18 seal verdict is not authoritative")
    if audit.get("verdict") != R318_SEALED_VERDICT or audit.get("checks") != "172/172":
        raise RuntimeError("R3.18 sealed audit is not authoritative")
    if summary.get("verdict") != R318_READY_VERDICT:
        raise RuntimeError("R3.18 canonical summary verdict mismatch")
    hashes = {
        "summary": (_sha256(p["summary"]), R318_SUMMARY_SHA256),
        "envelope": (_sha256(p["envelope"]), R318_ENVELOPE_SHA256),
        "bundle": (_sha256(p["bundle"]), R318_BUNDLE_SHA256),
    }
    for key, (got, want) in hashes.items():
        if got != want:
            raise RuntimeError(f"R3.18 canonical {key} SHA mismatch: {got} != {want}")
    if envelope.get("transport_phases", {}).get("phase_aware_transport_operator_required") is not True:
        raise RuntimeError("R3.18 did not authorize the phase-aware transport requirement")
    if float(envelope.get("full_125ka_macrostep", {}).get("integral_phase_closure_max_abs", float("inf"))) > 1e-6:
        raise RuntimeError("R3.18 transport-phase integrals do not close the 125 kyr macro exposure")
    if envelope.get("biology_state_mutated") is not False:
        raise RuntimeError("R3.18 parent biology state must remain frozen")
    parent317 = r318.validate_parent_r317_authority(root)
    bundle = r318.load_integral_bundle(p["bundle"])
    if abs(float(bundle["biology_state_age_ma"]) - START_AGE_MA) > 1e-12 or abs(float(bundle["physical_end_age_ma"]) - END_AGE_MA) > 1e-12:
        raise RuntimeError("R3.18 integral bundle endpoint metadata mismatch")
    if abs(float(bundle["transport_boundary_age_ma"]) - TRANSPORT_BOUNDARY_AGE_MA) > 1e-12:
        raise RuntimeError("R3.18 integral bundle transport boundary mismatch")
    for group in _REQUIRED_GROUPS:
        if group not in bundle["groups"] or set(bundle["groups"][group]) != set(AVERAGED_FIELDS):
            raise RuntimeError(f"R3.18 integral bundle missing governed group/fields: {group}")
    return {
        "state": parent317["state"],
        "a1": parent317["a1"],
        "c2": parent317["c2"],
        "clock": parent317["clock"],
        "bundle": bundle,
        "envelope": envelope,
        "r318_seal_sha256": _sha256(p["seal"]),
        "r318_audit_sha256": _sha256(p["audit"]),
        "r318_summary_sha256": R318_SUMMARY_SHA256,
        "r318_envelope_sha256": R318_ENVELOPE_SHA256,
        "r318_bundle_sha256": R318_BUNDLE_SHA256,
        "r317_seal_sha256": parent317["r317_seal_sha256"],
    }


def _clone_env(env: Mapping[str, Any]) -> dict[str, Any]:
    return {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in env.items()}


def _decorate_env(env: Mapping[str, Any], *, older_age_ma: float, younger_age_ma: float, role: str) -> dict[str, Any]:
    out = _clone_env(env)
    out.update({
        "age_ma": float(younger_age_ma),
        "older_ma": float(older_age_ma),
        "younger_ma": float(younger_age_ma),
        "older_index": -1,
        "younger_index": -1,
        "phase": 1.0,
        "topology": "R319_TIME_INTEGRATED_RECENT_H0_SUBSTRATE",
        "paleogeographic_history_provider": "R318_SEALED_EXPOSURE_INTEGRAL_BUNDLE",
        "biology_forcing_sample_semantics": role,
        "adaptive_clock_checkpoint_promoted_to_biology_step": False,
    })
    return out


def environments_from_r318_bundle(bundle: Mapping[str, Any]) -> tuple[dict[str, Any], tuple[dict[str, Any], dict[str, Any]]]:
    groups = bundle["groups"]
    macro = _decorate_env(
        r318.effective_environment(groups["full_125_to_0"], BIOLOGY_CADENCE_YEARS),
        older_age_ma=START_AGE_MA, younger_age_ma=END_AGE_MA,
        role="R318_FULL_125_TO_0_EFFECTIVE_FORCING_FOR_NONTRANSPORT_R38_OPERATORS",
    )
    p1 = _decorate_env(
        r318.effective_environment(groups["transport_phase1_125_to_62p5"], TRANSPORT_CADENCE_YEARS),
        older_age_ma=START_AGE_MA, younger_age_ma=TRANSPORT_BOUNDARY_AGE_MA,
        role="R318_TRANSPORT_PHASE1_125_TO_62P5_EFFECTIVE_FORCING",
    )
    p2 = _decorate_env(
        r318.effective_environment(groups["transport_phase2_62p5_to_0"], TRANSPORT_CADENCE_YEARS),
        older_age_ma=TRANSPORT_BOUNDARY_AGE_MA, younger_age_ma=END_AGE_MA,
        role="R318_TRANSPORT_PHASE2_62P5_TO_0_EFFECTIVE_FORCING",
    )
    return macro, (p1, p2)


def migration_two_phase(pop, root_species, guild, trait, metadata, lat, lon, _macro_env, dt,
                        cfg: R319Config, phase_envs: Sequence[Mapping[str, Any]], base_migration=None,
                        trace: list[dict[str, Any]] | None = None, endpoint_accessible: np.ndarray | None = None,
                        endpoint_reconciliation: dict[str, Any] | None = None):
    if abs(float(dt) - BIOLOGY_CADENCE_YEARS) > 1e-9:
        raise ValueError("R3.19 phase-aware migration is authorized only for one 125 kyr biology macrostep")
    if len(phase_envs) != EXPECTED_TRANSPORT_SUBSTEPS:
        raise ValueError("R3.19 requires exactly two transport-phase environments")
    base = base_migration or r38.r34._migration_subcycled_r3
    out = np.asarray(pop, float)
    hab = None
    for i, env in enumerate(phase_envs, start=1):
        out, hab = base(
            out, root_species, guild, trait, metadata, lat, lon, env,
            TRANSPORT_CADENCE_YEARS, cfg,
        )
        if trace is not None:
            trace.append({
                "phase_index": i,
                "dt_years": TRANSPORT_CADENCE_YEARS,
                "forcing_role": str(env.get("biology_forcing_sample_semantics", f"PHASE_{i}")),
                "population_after_phase": float(np.asarray(out, float).sum()),
            })
    if endpoint_accessible is not None:
        endpoint = np.asarray(endpoint_accessible, bool)
        phase2_access = np.asarray(phase_envs[-1]["accessible"], bool)
        if endpoint.shape != phase2_access.shape:
            raise RuntimeError("R3.19 endpoint support grid mismatch")
        out, moved = r38.r2.remap_to_land(out, phase2_access, endpoint, lat, lon)
        if endpoint_reconciliation is not None:
            endpoint_reconciliation.update({
                "applied": bool(moved > 0.0),
                "remapped_population_mass": float(moved),
                "endpoint_inaccessible_population_after": float(np.asarray(out, float)[:, ~endpoint].sum()),
            })
    return out, hab


@contextmanager
def patched_r38_phase_aware_transport(macro_env: Mapping[str, Any], phase_envs: Sequence[Mapping[str, Any]],
                                       expected_end_age_ma: float = END_AGE_MA,
                                       endpoint_accessible: np.ndarray | None = None):
    original_environment = r38.bp.environment_at
    original_migration = r38.r34._migration_subcycled_r3
    trace: list[dict[str, Any]] = []
    reconciliation: dict[str, Any] = {
        "applied": False, "remapped_population_mass": 0.0,
        "endpoint_inaccessible_population_after": 0.0,
    }
    macro_topology = _clone_env(macro_env)
    endpoint = np.asarray(endpoint_accessible, bool) if endpoint_accessible is not None else None
    if endpoint is not None:
        if "accessible" not in macro_topology or endpoint.shape != np.asarray(macro_topology["accessible"], bool).shape:
            raise RuntimeError("R3.19 endpoint topology shape mismatch")
        # Continuous forcing remains time-averaged, but the discrete accessible topology
        # is the exact state at the requested endpoint, matching the SEALED R3.8 boundary semantics.
        macro_topology["accessible"] = endpoint.copy()

    def environment_at(age_ma: float, _a1: Any, _cfg: Any) -> dict[str, Any]:
        if abs(float(age_ma) - float(expected_end_age_ma)) > 1e-12:
            raise RuntimeError("R3.19 macro effective environment is authorized only at the requested one-step endpoint")
        return _clone_env(macro_topology)

    def migration(pop, root_species, guild, trait, metadata, lat, lon, env, dt, cfg):
        return migration_two_phase(
            pop, root_species, guild, trait, metadata, lat, lon, env, dt, cfg,
            phase_envs, base_migration=original_migration, trace=trace,
            endpoint_accessible=endpoint, endpoint_reconciliation=reconciliation,
        )

    r38.bp.environment_at = environment_at
    r38.r34._migration_subcycled_r3 = migration
    try:
        yield trace, reconciliation
    finally:
        r38.r34._migration_subcycled_r3 = original_migration
        r38.bp.environment_at = original_environment


def run_phase_aware_macrostep(parent_state: r38.R38RuntimeState, a1: Any, metadata_rows: list[dict[str, Any]],
                              bundle: Mapping[str, Any], cfg: R319Config | None = None,
                              endpoint_accessible: np.ndarray | None = None):
    cfg = cfg or R319Config()
    if abs(float(parent_state.age_ma) - START_AGE_MA) > 1e-12:
        raise ValueError("R3.19 requires the exact SEALED 125 ka biology parent state")
    macro_env, phase_envs = environments_from_r318_bundle(bundle)
    st = r311._clone_state(parent_state)
    with patched_r38_phase_aware_transport(
        macro_env, phase_envs, expected_end_age_ma=END_AGE_MA, endpoint_accessible=endpoint_accessible
    ) as (trace, reconciliation):
        out, records = r38.advance_state(st, a1, metadata_rows, cfg, END_AGE_MA)
    moved = float(reconciliation.get("remapped_population_mass", 0.0))
    if moved > 0.0:
        out.topology_remap_mass += moved
        merged = False
        for ev in reversed(out.events):
            if ev.get("event") == "paleogeographic_support_loss_remap" and abs(float(ev.get("age_ma", 1.0)) - END_AGE_MA) <= 1e-12:
                ev["post_transport_endpoint_reconciliation_mass"] = moved
                ev["remapped_population_mass"] = float(ev.get("remapped_population_mass", 0.0)) + moved
                ev["semantic_status"] = "R319_EXACT_ENDPOINT_SUPPORT_RECONCILIATION_AFTER_PHASE_AWARE_TRANSPORT"
                merged = True
                break
        if not merged:
            out.events.append({
                "event": "paleogeographic_support_loss_remap", "age_ma": END_AGE_MA,
                "elapsed_year": float(out.elapsed_year), "remapped_population_mass": moved,
                "post_transport_endpoint_reconciliation_mass": moved,
                "semantic_status": "R319_EXACT_ENDPOINT_SUPPORT_RECONCILIATION_AFTER_PHASE_AWARE_TRANSPORT",
            })
    if endpoint_accessible is not None:
        out.current_accessible = np.asarray(endpoint_accessible, bool).copy()
    if len(records) != EXPECTED_BIOLOGY_STEPS:
        raise RuntimeError("R3.19 must execute exactly one 125 kyr biology step")
    if len(trace) != EXPECTED_TRANSPORT_SUBSTEPS or any(abs(float(x["dt_years"]) - TRANSPORT_CADENCE_YEARS) > 1e-9 for x in trace):
        raise RuntimeError("R3.19 transport trace does not contain exactly two 62.5 kyr substeps")
    return out, records, {
        "macro_environment": macro_env, "phase_environments": phase_envs, "transport_trace": trace,
        "endpoint_support_reconciliation": reconciliation,
    }


def constant_forcing_equivalence(parent_state: r38.R38RuntimeState, a1: Any, metadata_rows: list[dict[str, Any]],
                                 env: Mapping[str, Any], cfg: r38.R38Config, end_age_ma: float) -> dict[str, Any]:
    """Strong promotion gate: phase-aware transport must collapse to SEALED R3.8 for E1=E2=E."""
    base_parent = r311._clone_state(parent_state)
    phase_parent = r311._clone_state(parent_state)
    original_environment = r38.bp.environment_at

    def same_environment(age_ma: float, _a1: Any, _cfg: Any) -> dict[str, Any]:
        if abs(float(age_ma) - float(end_age_ma)) > 1e-12:
            raise RuntimeError("constant equivalence environment endpoint mismatch")
        return _clone_env(env)

    r38.bp.environment_at = same_environment
    try:
        baseline, baseline_records = r38.advance_state(base_parent, a1, metadata_rows, cfg, end_age_ma)
    finally:
        r38.bp.environment_at = original_environment

    with patched_r38_phase_aware_transport(
        env, (env, env), expected_end_age_ma=end_age_ma, endpoint_accessible=np.asarray(env["accessible"], bool)
    ) as (trace, reconciliation):
        phase, phase_records = r38.advance_state(phase_parent, a1, metadata_rows, cfg, end_age_ma)

    cmp = r38.compare_runtime_states(baseline, phase, atol=0.0)
    records_exact = baseline_records == phase_records
    events_exact = baseline.events == phase.events
    snapshots_exact = baseline.snapshots == phase.snapshots
    return {
        "state_bit_exact": bool(cmp.get("equivalent")),
        "state_comparison": cmp,
        "records_exact": bool(records_exact),
        "events_exact": bool(events_exact),
        "snapshots_exact": bool(snapshots_exact),
        "transport_trace": trace,
        "endpoint_support_reconciliation": reconciliation,
        "passed": bool(cmp.get("equivalent") and records_exact and events_exact and snapshots_exact and len(trace) == 2
                       and float(reconciliation.get("remapped_population_mass", 0.0)) == 0.0),
    }


def event_counts(st: r38.R38RuntimeState) -> dict[str, int]:
    return r318.r317.r316.event_counts(st)


def delta_event_counts(before: r38.R38RuntimeState, after: r38.R38RuntimeState) -> dict[str, int]:
    return r318.r317.r316.delta_event_counts(before, after)


def invariant_report(st: r38.R38RuntimeState, metadata_rows: list[dict[str, Any]], cfg: R319Config) -> dict[str, Any]:
    return r318.r317.r316.invariant_report(st, metadata_rows, cfg)


def species_counts_by_guild(st: r38.R38RuntimeState) -> dict[str, int]:
    return r318.r317.r316.species_counts_by_guild(st)


def _save_state_arrays(st: r38.R38RuntimeState, npz_path: Path) -> None:
    r318.r317.r316._save_state_arrays(st, npz_path)


def save_checkpoint(st: r38.R38RuntimeState, out_dir: Path, parent_authority: Mapping[str, Any], cfg: R319Config,
                    run_report: Mapping[str, Any]) -> dict[str, Any]:
    if abs(float(st.age_ma) - END_AGE_MA) > 1e-12:
        raise ValueError("R3.19 canonical checkpoint must be exactly 0 ka")
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stem = "WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19"
    jp = out_dir / f"{stem}.json"; npzp = out_dir / f"{stem}.npz"
    _save_state_arrays(st, npzp)
    meta = {
        "schema": SCHEMA, "stage": STAGE, "parent_stage": PARENT_STAGE,
        "age_ma": float(st.age_ma), "elapsed_year": float(st.elapsed_year),
        "event_side": "H0_PRESENT_NATURAL_CONTROL__PHASE_AWARE_TRANSPORT__DEEP_BIOLOGICAL_COUPLING_OFF",
        "parent_r318_authority": dict(parent_authority),
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
            "biology_cadence_years": BIOLOGY_CADENCE_YEARS,
            "biology_steps": EXPECTED_BIOLOGY_STEPS,
            "transport_cadence_years": TRANSPORT_CADENCE_YEARS,
            "transport_substeps": EXPECTED_TRANSPORT_SUBSTEPS,
            "phase_aware_transport": True,
            "support_remap_semantics": cfg.support_remap_semantics,
            "gene_flow_step_cadence_changed": False,
            "lifecycle_gate_cadence_changed": False,
            "adaptive_clock_used_as_biology_timestep": False,
            "deep_biological_coupling": False,
            "scientific_parameters_changed": False,
            "human_lineage_target_used": False,
        },
    }
    jp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"json": str(jp), "npz": str(npzp), "json_sha256": _sha256(jp), "npz_sha256": _sha256(npzp)}


def load_checkpoint(json_path: Path) -> r38.R38RuntimeState:
    jp = Path(json_path); m = json.loads(jp.read_text(encoding="utf-8"))
    if m.get("schema") != SCHEMA or m.get("stage") != STAGE:
        raise RuntimeError("R3.19 checkpoint metadata mismatch")
    z = np.load(jp.parent / m["npz_file"], allow_pickle=False)
    try:
        st = r38.R38RuntimeState(
            age_ma=float(m["age_ma"]), elapsed_year=float(m["elapsed_year"]), component_ids=list(m["component_ids"]),
            root_species=list(m["root_species"]), current_species=list(m["current_species"]), guild=z["guild"].astype(np.uint8),
            pop=z["population"].astype(float), trait=z["trait"].astype(float), va=z["va"].astype(float), gen=z["generation_time"].astype(float),
            registry={str(k):dict(v) for k,v in m["registry"].items()}, child_counters={str(k):int(v) for k,v in m["child_counters"].items()},
            current_accessible=z["current_accessible"].astype(bool), baselines=m["baselines"],
            ri_state={k:float(v) for k,v in r38._pair_dict_from_rows(m["ri_state"]).items()},
            clock_state={k:float(v) for k,v in r38._pair_dict_from_rows(m["clock_state"]).items()},
            ext_state=m["ext_state"], founder_state=m["founder_state"], vicariance_state=m["vicariance_state"],
            reconnection_state={k:dict(v) for k,v in r38._pair_dict_from_rows(m["reconnection_state"]).items()},
            events=list(m["events"]), snapshots=list(m["snapshots"]), founder_stats_last=list(m["founder_stats_last"]),
            gene_flow_closure=dict(m["gene_flow_closure"]), topology_remap_mass=float(m["topology_remap_mass"]),
            initial_total_population=float(m["initial_total_population"]), reduced_state=r38.ReducedGeneticLifecycleState(
                z["reduced_va_within"].astype(float), z["reduced_ancestry_covariance"].astype(float),
                z["reduced_neutral_segregation_potential"].astype(float), z["reduced_adaptive_coordinate"].astype(float),
            ),
        )
        st._lat = z["lat"].astype(float).copy(); st._lon = z["lon"].astype(float).copy()
        return st
    finally:
        z.close()


def run_single_environment_shadow(parent_state: r38.R38RuntimeState, a1: Any, metadata_rows: list[dict[str, Any]],
                                  macro_env: Mapping[str, Any], cfg: R319Config | None = None):
    cfg = cfg or R319Config()
    st = r311._clone_state(parent_state)
    original_environment = r38.bp.environment_at
    def environment_at(age_ma: float, _a1: Any, _cfg: Any) -> dict[str, Any]:
        if abs(float(age_ma) - END_AGE_MA) > 1e-12:
            raise RuntimeError("R3.19 single-environment shadow endpoint mismatch")
        return _clone_env(macro_env)
    r38.bp.environment_at = environment_at
    try:
        return r38.advance_state(st, a1, metadata_rows, cfg, END_AGE_MA)
    finally:
        r38.bp.environment_at = original_environment
