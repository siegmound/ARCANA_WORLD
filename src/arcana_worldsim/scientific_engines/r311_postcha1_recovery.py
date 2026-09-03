from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import copy
import hashlib
import json

import numpy as np

from . import r38_restartable_checkpoint as r38
from . import r310_cha1_highres_bridge as r310
from .segregation_potential_lifecycle import ReducedGeneticLifecycleState

STAGE = "v0.6D1-R3.11"
PARENT_STAGE = "v0.6D1-R3.10_SEALED"
SCHEMA = "ARCANA_R311_WORLD1_H0_POST_CHA1_5MY_RECOVERY_CHECKPOINT_V1"
SUMMARY_SCHEMA = "ARCANA_R311_POST_CHA1_H0_RECOVERY_ADAPTIVE_RADIATION_RESTART_V1"
START_AGE_MA = 65.5
END_AGE_MA = 61.0
SMOKE_END_AGE_MA = 65.0
IMPACT_AGE_MA = 66.0
FROZEN_INTERVAL_YEARS = 500_000.0
EXPECTED_STEPS = 36
EXPECTED_SMOKE_STEPS = 4
PARENT_SPECIES = 93
PARENT_COMPONENTS = 207


@dataclass(frozen=True)
class R311Config(r38.R38Config):
    end_age_ma: float = END_AGE_MA

    # Governance-only fields. No scientific operator is changed.
    post_cha1_restart_age_ma: float = START_AGE_MA
    cha1_frozen_lifecycle_interval_years: float = FROZEN_INTERVAL_YEARS
    adaptive_radiation_semantics: str = (
        "ORDINARY_R37I_R38_FISSION_RI_FOUNDER_SPECIATION_REENABLED_NO_POST_CHA1_MULTIPLIER"
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        if abs(self.post_cha1_restart_age_ma - START_AGE_MA) > 1e-12:
            raise ValueError("R3.11 canonical restart remains 65.5 Ma")
        if abs(self.cha1_frozen_lifecycle_interval_years - FROZEN_INTERVAL_YEARS) > 1e-9:
            raise ValueError("R3.11 must preserve the exact 500 kyr R3.10 frozen lifecycle interval")
        if abs(self.end_age_ma - END_AGE_MA) > 1e-12:
            raise ValueError("R3.11 canonical production endpoint is 61.0 Ma (+5 Myr after CHA-1)")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _clone_state(st: r38.R38RuntimeState) -> r38.R38RuntimeState:
    out = r38.R38RuntimeState(
        age_ma=float(st.age_ma),
        elapsed_year=float(st.elapsed_year),
        component_ids=list(st.component_ids),
        root_species=list(st.root_species),
        current_species=list(st.current_species),
        guild=np.asarray(st.guild, dtype=np.uint8).copy(),
        pop=np.asarray(st.pop, dtype=float).copy(),
        trait=np.asarray(st.trait, dtype=float).copy(),
        va=np.asarray(st.va, dtype=float).copy(),
        gen=np.asarray(st.gen, dtype=float).copy(),
        registry=copy.deepcopy(st.registry),
        child_counters=dict(st.child_counters),
        current_accessible=np.asarray(st.current_accessible, dtype=bool).copy(),
        baselines=copy.deepcopy(st.baselines),
        ri_state=dict(st.ri_state),
        clock_state=dict(st.clock_state),
        ext_state=copy.deepcopy(st.ext_state),
        founder_state=copy.deepcopy(st.founder_state),
        vicariance_state=copy.deepcopy(st.vicariance_state),
        reconnection_state=copy.deepcopy(st.reconnection_state),
        events=copy.deepcopy(st.events),
        snapshots=copy.deepcopy(st.snapshots),
        founder_stats_last=copy.deepcopy(st.founder_stats_last),
        gene_flow_closure=copy.deepcopy(st.gene_flow_closure),
        topology_remap_mass=float(st.topology_remap_mass),
        initial_total_population=float(st.initial_total_population),
        reduced_state=type(st.reduced_state)(
            np.asarray(st.reduced_state.va_within, dtype=float).copy(),
            np.asarray(st.reduced_state.ancestry_covariance, dtype=float).copy(),
            np.asarray(st.reduced_state.neutral_segregation_potential, dtype=float).copy(),
            np.asarray(st.reduced_state.adaptive_coordinate, dtype=float).copy(),
        ),
    )
    out._lat = np.asarray(st._lat, dtype=float).copy()
    out._lon = np.asarray(st._lon, dtype=float).copy()
    return out


def validate_parent_r310_authority(root: Path) -> dict[str, Any]:
    root = Path(root)
    d = root / "references" / "v0_6D1_R3_10"
    summary_path = d / "R3_10_CHA1_EVENT_BRIDGE_SUMMARY.json"
    checkpoint_path = d / "WORLD1_H0_65P5Ma_POST_CHA1_500KY_CANONICAL_CHECKPOINT_v0_6D1_R3_10.json"
    npz_path = checkpoint_path.with_suffix(".npz")
    if not summary_path.exists() or not checkpoint_path.exists() or not npz_path.exists():
        raise RuntimeError("R3.11 requires materialized R3.10 SEALED checkpoint evidence")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not str(summary.get("verdict", "")).startswith("PASS_REBASED_CHA1_HIGH_RES_EVENT_BRIDGE"):
        raise RuntimeError("R3.10 parent verdict is not authoritative")
    if summary.get("event_side") != "POST_CHA1_500KY" or abs(float(summary.get("age_ma", -1)) - START_AGE_MA) > 1e-12:
        raise RuntimeError("R3.10 parent boundary mismatch")
    cp = summary.get("checkpoint", {})
    expected_j = str(cp.get("json_sha256", ""))
    expected_n = str(cp.get("npz_sha256", ""))
    if _sha256(checkpoint_path) != expected_j or _sha256(npz_path) != expected_n:
        raise RuntimeError("R3.10 parent checkpoint hash mismatch")
    st = r310.load_postcha1_checkpoint(checkpoint_path)
    if len(set(st.current_species)) != PARENT_SPECIES or len(st.component_ids) != PARENT_COMPONENTS:
        raise RuntimeError("R3.10 parent species/component cardinality mismatch")
    if abs(st.age_ma - START_AGE_MA) > 1e-12 or abs(st.elapsed_year - 144_500_000.0) > 1e-6:
        raise RuntimeError("R3.10 parent chronology mismatch")
    return {
        "state": st,
        "checkpoint_json": str(checkpoint_path.relative_to(root)),
        "checkpoint_npz": str(npz_path.relative_to(root)),
        "checkpoint_json_sha256": expected_j,
        "checkpoint_npz_sha256": expected_n,
        "summary_sha256": _sha256(summary_path),
    }


def thaw_lifecycle_timers(
    parent_state: r38.R38RuntimeState,
    frozen_interval_years: float = FROZEN_INTERVAL_YEARS,
) -> tuple[r38.R38RuntimeState, dict[str, Any]]:
    """Thaw absolute-time lifecycle records without crediting the frozen CHA-1 interval.

    R3.10 advances physical elapsed time from 144.0 to 144.5 Myr while ordinary
    founder/vicariance/reconnection/extinction lifecycle updates are OFF.  Those
    registries store absolute timestamps.  If they are resumed unchanged, the
    first 500-kyr cadence check would interpret the frozen interval as ordinary
    persistence.  We therefore move only the *last/update origin* timestamps to
    the 65.5-Ma thaw boundary while preserving accumulated persistence values.
    """
    st = _clone_state(parent_state)
    if abs(st.age_ma - START_AGE_MA) > 1e-12:
        raise RuntimeError("R3.11 lifecycle thaw requires exact 65.5 Ma parent")
    preimpact_elapsed = float(st.elapsed_year - frozen_interval_years)
    if abs(preimpact_elapsed - 144_000_000.0) > 1e-6:
        raise RuntimeError("R3.11 frozen interval chronology mismatch")

    diag: dict[str, Any] = {
        "frozen_interval_years": float(frozen_interval_years),
        "preimpact_last_ordinary_elapsed_year": preimpact_elapsed,
        "thaw_elapsed_year": float(st.elapsed_year),
        "shifted": {"founder": 0, "vicariance": 0, "reconnection": 0, "ordinary_extinction": 0},
        "max_existing_last_seen_elapsed_year": None,
        "persistence_values_changed": False,
    }
    existing_last: list[float] = []

    for row in st.founder_state.values():
        if row.get("last_seen_elapsed_year") is not None:
            old = float(row["last_seen_elapsed_year"])
            existing_last.append(old)
            if old > preimpact_elapsed + 1e-6:
                raise RuntimeError("founder state already contains post-impact ordinary lifecycle time")
            row["last_seen_elapsed_year"] = float(st.elapsed_year)
            diag["shifted"]["founder"] += 1

    for row in st.vicariance_state.values():
        if row.get("last_seen_elapsed_year") is not None:
            old = float(row["last_seen_elapsed_year"])
            existing_last.append(old)
            if old > preimpact_elapsed + 1e-6:
                raise RuntimeError("vicariance state already contains post-impact ordinary lifecycle time")
            row["last_seen_elapsed_year"] = float(st.elapsed_year)
            diag["shifted"]["vicariance"] += 1

    for row in st.reconnection_state.values():
        if row.get("last_seen_elapsed_year") is not None:
            old = float(row["last_seen_elapsed_year"])
            existing_last.append(old)
            if old > preimpact_elapsed + 1e-6:
                raise RuntimeError("reconnection state already contains post-impact ordinary lifecycle time")
            row["last_seen_elapsed_year"] = float(st.elapsed_year)
            diag["shifted"]["reconnection"] += 1

    # The current canonical R3.10 branch has no active ordinary-extinction
    # episode, but handle this state generically.  Its persistence is derived
    # from elapsed-start rather than a last_seen delta, so shift the episode
    # origin by the frozen duration.
    for row in st.ext_state.values():
        if row.get("start_elapsed_year") is not None:
            old = float(row["start_elapsed_year"])
            if old > preimpact_elapsed + 1e-6:
                raise RuntimeError("ordinary-extinction state already starts post impact")
            row["start_elapsed_year"] = old + float(frozen_interval_years)
            if row.get("last_seen_elapsed_year") is not None:
                row["last_seen_elapsed_year"] = float(st.elapsed_year)
            diag["shifted"]["ordinary_extinction"] += 1

    diag["max_existing_last_seen_elapsed_year"] = max(existing_last) if existing_last else None
    st.events.append({
        "event": "post_CHA1_ordinary_lifecycle_thaw",
        "age_ma": START_AGE_MA,
        "elapsed_year": float(st.elapsed_year),
        "frozen_interval_years": float(frozen_interval_years),
        "semantic_status": "TEMPORAL_RESTART_ADAPTER_NO_SCIENTIFIC_PARAMETER_CHANGE",
        "shifted_records": dict(diag["shifted"]),
    })
    return st, diag


def event_counts(st: r38.R38RuntimeState) -> dict[str, int]:
    names = [str(e.get("event", "")) for e in st.events]
    keys = (
        "paleogeographic_support_loss_remap",
        "deme_coalescence",
        "deme_fission",
        "speciation",
        "ordinary_background_extinction",
        "CHA1_species_extinction",
        "CHA1_high_resolution_event_bridge_complete",
        "post_CHA1_ordinary_lifecycle_thaw",
    )
    return {k: names.count(k) for k in keys}


def delta_event_counts(before: r38.R38RuntimeState, after: r38.R38RuntimeState) -> dict[str, int]:
    a = event_counts(before)
    b = event_counts(after)
    return {k: int(b.get(k, 0) - a.get(k, 0)) for k in b}


def run_recovery(
    parent_state: r38.R38RuntimeState,
    a1: np.lib.npyio.NpzFile,
    metadata_rows: list[dict[str, Any]],
    cfg: R311Config | None = None,
    end_age_ma: float = END_AGE_MA,
) -> tuple[r38.R38RuntimeState, list[dict[str, Any]], dict[str, Any]]:
    cfg = cfg or R311Config()
    if end_age_ma > START_AGE_MA - cfg.biology_cadence_years / 1e6 + 1e-12:
        raise ValueError("R3.11 continuation must include at least one ordinary biology step")
    if end_age_ma < END_AGE_MA - 1e-12:
        raise ValueError("R3.11 may not run beyond the canonical +5 Myr recovery boundary")
    st, thaw = thaw_lifecycle_timers(parent_state, cfg.cha1_frozen_lifecycle_interval_years)
    out, records = r38.advance_state(st, a1, metadata_rows, cfg, float(end_age_ma))
    return out, records, thaw


def _save_state_arrays(st: r38.R38RuntimeState, npzp: Path) -> None:
    np.savez_compressed(
        npzp,
        guild=st.guild,
        population=st.pop,
        trait=st.trait,
        va=st.va,
        generation_time=st.gen,
        current_accessible=st.current_accessible.astype(np.uint8),
        reduced_va_within=st.reduced_state.va_within,
        reduced_ancestry_covariance=st.reduced_state.ancestry_covariance,
        reduced_neutral_segregation_potential=st.reduced_state.neutral_segregation_potential,
        reduced_adaptive_coordinate=st.reduced_state.adaptive_coordinate,
        lat=np.asarray(st._lat, dtype=float),
        lon=np.asarray(st._lon, dtype=float),
    )


def save_recovery_checkpoint(
    st: r38.R38RuntimeState,
    out_dir: Path,
    parent_authority: dict[str, Any],
    cfg: R311Config,
    thaw_report: dict[str, Any],
    run_report: dict[str, Any],
) -> dict[str, Any]:
    if abs(st.age_ma - END_AGE_MA) > 1e-12:
        raise ValueError("canonical R3.11 checkpoint must be exactly 61.0 Ma")
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stem = "WORLD1_H0_61Ma_POST_CHA1_5MY_RECOVERY_CHECKPOINT_v0_6D1_R3_11"
    jp = out_dir / f"{stem}.json"; npzp = out_dir / f"{stem}.npz"
    _save_state_arrays(st, npzp)
    meta = {
        "schema": SCHEMA,
        "stage": STAGE,
        "parent_stage": PARENT_STAGE,
        "age_ma": float(st.age_ma),
        "event_side": "POST_CHA1_5MY_RECOVERY",
        "elapsed_year": float(st.elapsed_year),
        "parent_r310_authority": parent_authority,
        "lifecycle_thaw": thaw_report,
        "nominal_reduced_order_reference": {
            "label": "K_CENTER",
            "K_eff": r38.NOMINAL_K,
            "semantic_role": "OPERATIONAL_REDUCED_ORDER_COORDINATE_REFERENCE_NOT_PHYSICAL_CONSTANT",
        },
        "component_ids": st.component_ids,
        "root_species": st.root_species,
        "current_species": st.current_species,
        "registry": st.registry,
        "child_counters": st.child_counters,
        "baselines": st.baselines,
        "ri_state": r38._pair_dict_rows(st.ri_state),
        "clock_state": r38._pair_dict_rows(st.clock_state),
        "ext_state": st.ext_state,
        "founder_state": st.founder_state,
        "vicariance_state": st.vicariance_state,
        "reconnection_state": r38._pair_dict_rows(st.reconnection_state),
        "events": r38._jsonable(st.events),
        "snapshots": r38._jsonable(st.snapshots),
        "founder_stats_last": r38._jsonable(st.founder_stats_last),
        "gene_flow_closure": r38._jsonable(st.gene_flow_closure),
        "topology_remap_mass": st.topology_remap_mass,
        "initial_total_population": st.initial_total_population,
        "config": asdict(cfg),
        "run_report": run_report,
        "npz_file": npzp.name,
        "governance": {
            "cha1_already_applied": True,
            "cha1_reapplied": False,
            "deep_biological_coupling": False,
            "ordinary_lifecycle_reenabled": True,
            "post_cha1_radiation_multiplier_used": False,
            "old_d31_solver_reactivated": False,
            "r37i_r38_production_runtime_reused": True,
            "mu_changed": False,
            "b_changed": False,
            "q_ceiling_changed": False,
            "scalar_k_physical_constant_authorized": False,
        },
    }
    jp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"json": str(jp), "npz": str(npzp), "json_sha256": _sha256(jp), "npz_sha256": _sha256(npzp)}


def save_smoke_checkpoint(
    st: r38.R38RuntimeState,
    out_dir: Path,
    cfg: R311Config,
    thaw_report: dict[str, Any],
) -> dict[str, Any]:
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"WORLD1_H0_{str(st.age_ma).replace('.', 'P')}Ma_R3_11_SMOKE_CHECKPOINT"
    jp = out_dir / f"{stem}.json"; npzp = out_dir / f"{stem}.npz"
    _save_state_arrays(st, npzp)
    meta = {
        "schema": "ARCANA_R311_SMOKE_CHECKPOINT_V1",
        "stage": STAGE,
        "age_ma": float(st.age_ma), "elapsed_year": float(st.elapsed_year),
        "component_ids": st.component_ids, "root_species": st.root_species, "current_species": st.current_species,
        "registry": st.registry, "child_counters": st.child_counters, "baselines": st.baselines,
        "ri_state": r38._pair_dict_rows(st.ri_state), "clock_state": r38._pair_dict_rows(st.clock_state),
        "ext_state": st.ext_state, "founder_state": st.founder_state, "vicariance_state": st.vicariance_state,
        "reconnection_state": r38._pair_dict_rows(st.reconnection_state), "events": r38._jsonable(st.events),
        "snapshots": r38._jsonable(st.snapshots), "founder_stats_last": r38._jsonable(st.founder_stats_last),
        "gene_flow_closure": r38._jsonable(st.gene_flow_closure), "topology_remap_mass": st.topology_remap_mass,
        "initial_total_population": st.initial_total_population, "config": asdict(cfg), "lifecycle_thaw": thaw_report,
        "npz_file": npzp.name,
    }
    jp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"json": str(jp), "npz": str(npzp), "json_sha256": _sha256(jp), "npz_sha256": _sha256(npzp)}


def load_recovery_checkpoint(json_path: Path, smoke: bool = False) -> r38.R38RuntimeState:
    jp = Path(json_path); m = json.loads(jp.read_text(encoding="utf-8"))
    expected = "ARCANA_R311_SMOKE_CHECKPOINT_V1" if smoke else SCHEMA
    if m.get("schema") != expected or m.get("stage") != STAGE:
        raise RuntimeError("R3.11 checkpoint metadata mismatch")
    if not smoke and (abs(float(m["age_ma"]) - END_AGE_MA) > 1e-12 or m.get("event_side") != "POST_CHA1_5MY_RECOVERY"):
        raise RuntimeError("R3.11 canonical checkpoint boundary mismatch")
    z = np.load(jp.parent / m["npz_file"], allow_pickle=False)
    st = r38.R38RuntimeState(
        age_ma=float(m["age_ma"]), elapsed_year=float(m["elapsed_year"]),
        component_ids=list(m["component_ids"]), root_species=list(m["root_species"]), current_species=list(m["current_species"]),
        guild=z["guild"].astype(np.uint8), pop=z["population"].astype(float), trait=z["trait"].astype(float),
        va=z["va"].astype(float), gen=z["generation_time"].astype(float),
        registry={str(k): dict(v) for k, v in m["registry"].items()}, child_counters={str(k): int(v) for k, v in m["child_counters"].items()},
        current_accessible=z["current_accessible"].astype(bool), baselines=m["baselines"],
        ri_state={k: float(v) for k, v in r38._pair_dict_from_rows(m["ri_state"]).items()},
        clock_state={k: float(v) for k, v in r38._pair_dict_from_rows(m["clock_state"]).items()},
        ext_state=m["ext_state"], founder_state=m["founder_state"], vicariance_state=m["vicariance_state"],
        reconnection_state={k: dict(v) for k, v in r38._pair_dict_from_rows(m["reconnection_state"]).items()},
        events=list(m["events"]), snapshots=list(m["snapshots"]), founder_stats_last=list(m["founder_stats_last"]),
        gene_flow_closure=dict(m["gene_flow_closure"]), topology_remap_mass=float(m["topology_remap_mass"]),
        initial_total_population=float(m["initial_total_population"]),
        reduced_state=ReducedGeneticLifecycleState(
            z["reduced_va_within"].astype(float), z["reduced_ancestry_covariance"].astype(float),
            z["reduced_neutral_segregation_potential"].astype(float), z["reduced_adaptive_coordinate"].astype(float),
        ),
    )
    st._lat = z["lat"].astype(float); st._lon = z["lon"].astype(float)
    return st


def invariant_report(st: r38.R38RuntimeState, metadata_rows: list[dict[str, Any]], cfg: R311Config) -> dict[str, Any]:
    md = {r["species_id"]: r for r in metadata_rows}
    q = r38._normalized_q(st.reduced_state.va_within, st.root_species, md, cfg.body_mass_scale)
    s = np.asarray(st.reduced_state.neutral_segregation_potential, dtype=float)
    return {
        "population_min": float(np.min(st.pop)) if st.pop.size else 0.0,
        "population_on_inaccessible_cells": float(np.sum(st.pop[:, ~st.current_accessible])) if st.pop.size else 0.0,
        "q_max": float(np.max(q)) if q.size else 0.0,
        "q_median": float(np.median(q)) if q.size else 0.0,
        "q_ceiling": float(cfg.variance_ceiling_normalized),
        "q_headroom": float(cfg.variance_ceiling_normalized - (float(np.max(q)) if q.size else 0.0)),
        "s_symmetry_max_abs": float(np.max(np.abs(s - np.swapaxes(s, 0, 1)))) if s.size else 0.0,
        "s_diagonal_max_abs": float(np.max(np.abs(np.diagonal(s, axis1=0, axis2=1)))) if s.size else 0.0,
        "s_min": float(np.min(s)) if s.size else 0.0,
    }
