from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import hashlib
import json

import numpy as np

from . import r38_restartable_checkpoint as r38
from . import r311_postcha1_recovery as r311
from .segregation_potential_lifecycle import ReducedGeneticLifecycleState

STAGE = "v0.6D1-R3.12"
PARENT_STAGE = "v0.6D1-R3.11_SEALED"
SCHEMA = "ARCANA_R312_WORLD1_H0_POST_CHA1_20MY_DIVERSITY_RECOVERY_CHECKPOINT_V1"
SMOKE_SCHEMA = "ARCANA_R312_SMOKE_CHECKPOINT_V1"
SUMMARY_SCHEMA = "ARCANA_R312_POST_CHA1_H0_DIVERSITY_RECOVERY_V1"

IMPACT_AGE_MA = 66.0
START_AGE_MA = 61.0
END_AGE_MA = 46.0
SMOKE_END_AGE_MA = 60.5
EXPECTED_STEPS = 120
EXPECTED_SMOKE_STEPS = 4

PARENT_SPECIES = 95
PARENT_COMPONENTS = 236
PRE_CHA1_SPECIES_REFERENCE = 305
POST_CHA1_500KY_SPECIES_REFERENCE = 93
DIRECT_CHA1_SPECIES_LOSS_REFERENCE = 212


@dataclass(frozen=True)
class R312Config(r38.R38Config):
    end_age_ma: float = END_AGE_MA

    # Governance / observational semantics only.  No scientific operator is changed.
    recovery_observation_start_age_ma: float = START_AGE_MA
    recovery_horizon_myr_after_impact: float = 20.0
    diversity_recovery_semantics: str = (
        "OBSERVE_ORDINARY_R37I_R38_DIVERSIFICATION_AND_EXTINCTION_WITHOUT_RICHNESS_TARGET_OR_RADIATION_MULTIPLIER"
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        if abs(self.recovery_observation_start_age_ma - START_AGE_MA) > 1e-12:
            raise ValueError("R3.12 canonical parent boundary remains 61.0 Ma")
        if abs(self.recovery_horizon_myr_after_impact - 20.0) > 1e-12:
            raise ValueError("R3.12 canonical diversity-recovery horizon remains +20 Myr after CHA-1")
        if abs(self.end_age_ma - END_AGE_MA) > 1e-12:
            raise ValueError("R3.12 canonical production endpoint is 46.0 Ma (+20 Myr after CHA-1)")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_parent_r311_authority(root: Path) -> dict[str, Any]:
    root = Path(root)
    d = root / "references" / "v0_6D1_R3_11"
    summary_path = d / "R3_11_POST_CHA1_RECOVERY_SUMMARY.json"
    checkpoint_path = d / "WORLD1_H0_61Ma_POST_CHA1_5MY_RECOVERY_CHECKPOINT_v0_6D1_R3_11.json"
    npz_path = checkpoint_path.with_suffix(".npz")
    seal_path = d / "R3_11_SEAL_SUMMARY.json"
    for p in (summary_path, checkpoint_path, npz_path, seal_path):
        if not p.exists():
            raise RuntimeError(f"R3.12 requires materialized R3.11 SEALED evidence: missing {p.name}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if not str(summary.get("verdict", "")).startswith("PASS_CANONICAL_POST_CHA1_65P5_TO_61_H0_RECOVERY"):
        raise RuntimeError("R3.11 parent run verdict is not authoritative")
    if not str(seal.get("verdict", "")).endswith("61MA_RESTART_BOUNDARY_SEALED"):
        raise RuntimeError("R3.11 parent seal verdict is not authoritative")
    boundary = seal.get("boundary", {})
    if abs(float(boundary.get("age_ma", -1.0)) - START_AGE_MA) > 1e-12:
        raise RuntimeError("R3.11 parent boundary age mismatch")
    if boundary.get("event_side") != "POST_CHA1_5MY_RECOVERY":
        raise RuntimeError("R3.11 parent event-side mismatch")
    if int(boundary.get("species", -1)) != PARENT_SPECIES or int(boundary.get("components", -1)) != PARENT_COMPONENTS:
        raise RuntimeError("R3.11 parent cardinality mismatch")

    hashes = seal.get("hashes", {})
    expected_s = str(hashes.get("summary", ""))
    expected_j = str(hashes.get("checkpoint_json", ""))
    expected_n = str(hashes.get("checkpoint_npz", ""))
    if _sha256(summary_path) != expected_s:
        raise RuntimeError("R3.11 parent summary hash mismatch")
    if _sha256(checkpoint_path) != expected_j or _sha256(npz_path) != expected_n:
        raise RuntimeError("R3.11 parent checkpoint hash mismatch")

    st = r311.load_recovery_checkpoint(checkpoint_path, smoke=False)
    if abs(st.age_ma - START_AGE_MA) > 1e-12 or abs(st.elapsed_year - 149_000_000.0) > 1e-6:
        raise RuntimeError("R3.11 parent chronology mismatch")
    if len(set(st.current_species)) != PARENT_SPECIES or len(st.component_ids) != PARENT_COMPONENTS:
        raise RuntimeError("R3.11 loaded state cardinality mismatch")
    counts = r311.event_counts(st)
    if counts["CHA1_species_extinction"] != DIRECT_CHA1_SPECIES_LOSS_REFERENCE:
        raise RuntimeError("R3.11 parent lost CHA-1 extinction authority")
    if counts["CHA1_high_resolution_event_bridge_complete"] != 1:
        raise RuntimeError("R3.11 parent must contain exactly one completed CHA-1 bridge")
    if counts["post_CHA1_ordinary_lifecycle_thaw"] != 1:
        raise RuntimeError("R3.11 parent must contain exactly one lifecycle thaw")

    return {
        "state": st,
        "checkpoint_json": str(checkpoint_path.relative_to(root)),
        "checkpoint_npz": str(npz_path.relative_to(root)),
        "checkpoint_json_sha256": expected_j,
        "checkpoint_npz_sha256": expected_n,
        "summary_sha256": expected_s,
        "seal_summary_sha256": _sha256(seal_path),
        "seal_verdict": str(seal.get("verdict")),
    }


def run_diversity_recovery(
    parent_state: r38.R38RuntimeState,
    a1: np.lib.npyio.NpzFile,
    metadata_rows: list[dict[str, Any]],
    cfg: R312Config | None = None,
    end_age_ma: float = END_AGE_MA,
) -> tuple[r38.R38RuntimeState, list[dict[str, Any]]]:
    cfg = cfg or R312Config()
    if abs(parent_state.age_ma - START_AGE_MA) > 1e-12:
        raise ValueError("R3.12 must start from the exact 61.0 Ma R3.11 boundary")
    if end_age_ma > START_AGE_MA - cfg.biology_cadence_years / 1e6 + 1e-12:
        raise ValueError("R3.12 continuation must include at least one ordinary biology step")
    if end_age_ma < END_AGE_MA - 1e-12:
        raise ValueError("R3.12 may not run beyond the canonical +20 Myr recovery boundary")
    # No thaw here. R3.11 already re-enabled ordinary lifecycle exactly once.
    st = r311._clone_state(parent_state)
    out, records = r38.advance_state(st, a1, metadata_rows, cfg, float(end_age_ma))
    return out, records


def event_counts(st: r38.R38RuntimeState) -> dict[str, int]:
    return r311.event_counts(st)


def delta_event_counts(before: r38.R38RuntimeState, after: r38.R38RuntimeState) -> dict[str, int]:
    return r311.delta_event_counts(before, after)


def species_counts_by_guild(st: r38.R38RuntimeState) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for sid, gid in zip(st.current_species, np.asarray(st.guild, dtype=int).tolist()):
        sid = str(sid); gid = int(gid)
        if sid in mapping and mapping[sid] != gid:
            raise RuntimeError(f"species {sid} spans inconsistent guild ids")
        mapping[sid] = gid
    out: dict[str, int] = {}
    for gid in sorted(set(mapping.values())):
        out[str(gid)] = sum(v == gid for v in mapping.values())
    return out


def root_lineage_profile(st: r38.R38RuntimeState) -> dict[str, Any]:
    active: dict[str, set[str]] = {}
    for root, current in zip(st.root_species, st.current_species):
        active.setdefault(str(root), set()).add(str(current))
    counts = sorted((len(v) for v in active.values()), reverse=True)
    return {
        "active_root_lineages": len(active),
        "root_lineages_with_multiple_current_species": sum(c > 1 for c in counts),
        "max_current_species_per_root_lineage": max(counts) if counts else 0,
        "mean_current_species_per_root_lineage": float(np.mean(counts)) if counts else 0.0,
    }


def diversity_recovery_report(
    parent_state: r38.R38RuntimeState,
    final_state: r38.R38RuntimeState,
    preimpact_guild_counts: dict[str, int] | None = None,
    immediate_postimpact_guild_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    parent_species = len(set(parent_state.current_species))
    final_species = len(set(final_state.current_species))
    net_since_immediate = final_species - POST_CHA1_500KY_SPECIES_REFERENCE
    net_since_r311 = final_species - parent_species
    lost = DIRECT_CHA1_SPECIES_LOSS_REFERENCE
    parent_guild = species_counts_by_guild(parent_state)
    final_guild = species_counts_by_guild(final_state)

    guild_rows: dict[str, Any] = {}
    keys = sorted(set(parent_guild) | set(final_guild) | set(preimpact_guild_counts or {}) | set(immediate_postimpact_guild_counts or {}), key=int)
    for gid in keys:
        pre = None if preimpact_guild_counts is None else int(preimpact_guild_counts.get(gid, 0))
        post = None if immediate_postimpact_guild_counts is None else int(immediate_postimpact_guild_counts.get(gid, 0))
        p61 = int(parent_guild.get(gid, 0))
        fin = int(final_guild.get(gid, 0))
        row: dict[str, Any] = {
            "pre_CHA1_species": pre,
            "post_CHA1_500ky_species": post,
            "species_at_61Ma": p61,
            "species_at_end": fin,
            "net_change_61Ma_to_end": fin - p61,
        }
        if pre is not None and pre > 0:
            row["fraction_of_pre_CHA1_richness_at_end"] = fin / pre
        if pre is not None and post is not None and pre > post:
            row["fraction_of_CHA1_guild_loss_recovered_by_end"] = (fin - post) / (pre - post)
        guild_rows[gid] = row

    return {
        "reference_only_not_acceptance_targets": True,
        "pre_CHA1_species_reference": PRE_CHA1_SPECIES_REFERENCE,
        "post_CHA1_500ky_species_reference": POST_CHA1_500KY_SPECIES_REFERENCE,
        "R3_11_61Ma_species": parent_species,
        "final_species": final_species,
        "net_species_recovered_since_post_CHA1_500ky": net_since_immediate,
        "net_species_change_since_R3_11_61Ma": net_since_r311,
        "fraction_of_direct_CHA1_species_loss_recovered": net_since_immediate / lost,
        "fraction_of_pre_CHA1_species_richness_present": final_species / PRE_CHA1_SPECIES_REFERENCE,
        "guild_richness": guild_rows,
        "root_lineages_parent": root_lineage_profile(parent_state),
        "root_lineages_final": root_lineage_profile(final_state),
        "interpretation_guard": (
            "These are descriptive recovery metrics only. No richness level, positive net diversification, or Earth analogue value is required for PASS."
        ),
    }


def classify_speciation_origin_from_r311_boundary(parent_state: r38.R38RuntimeState, new_events: list[dict[str, Any]]) -> dict[str, Any]:
    carry = set()
    for row in parent_state.founder_state.values():
        carry.add((str(row.get("species_id")), tuple(sorted(str(x) for x in row.get("component_ids", [])))))
    rows = []
    for e in new_events:
        if e.get("event") != "speciation":
            continue
        sig = (str(e.get("parent_species_id")), tuple(sorted(str(x) for x in e.get("daughter_component_ids", []))))
        matched = sig in carry
        rows.append({
            "age_ma": e.get("age_ma"),
            "parent_species_id": e.get("parent_species_id"),
            "daughter_species_id": e.get("daughter_species_id"),
            "classification": "MATCHED_R311_BOUNDARY_FOUNDER_CARRYOVER" if matched else "NOT_MATCHED_TO_R311_BOUNDARY_FOUNDER_STATE",
            "causal_note": (
                "Founder candidate was already active at the 61 Ma R3.11 boundary."
                if matched else
                "Candidate is not matched to the founder state present at 61 Ma; this is not by itself proof of CHA-1 empty-niche causation."
            ),
        })
    return {
        "founder_candidates_at_61Ma": len(parent_state.founder_state),
        "matched_61Ma_founder_carryover_speciations": sum(r["classification"].startswith("MATCHED") for r in rows),
        "not_matched_to_61Ma_founder_state": sum(not r["classification"].startswith("MATCHED") for r in rows),
        "rows": rows,
        "interpretation_guard": "Speciation provenance is structural timing evidence, not a causal attribution to CHA-1.",
    }


def invariant_report(st: r38.R38RuntimeState, metadata_rows: list[dict[str, Any]], cfg: R312Config) -> dict[str, Any]:
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


def save_diversity_checkpoint(
    st: r38.R38RuntimeState,
    out_dir: Path,
    parent_authority: dict[str, Any],
    cfg: R312Config,
    run_report: dict[str, Any],
) -> dict[str, Any]:
    if abs(st.age_ma - END_AGE_MA) > 1e-12:
        raise ValueError("canonical R3.12 checkpoint must be exactly 46.0 Ma")
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stem = "WORLD1_H0_46Ma_POST_CHA1_20MY_DIVERSITY_RECOVERY_CHECKPOINT_v0_6D1_R3_12"
    jp = out_dir / f"{stem}.json"; npzp = out_dir / f"{stem}.npz"
    _save_state_arrays(st, npzp)
    meta = {
        "schema": SCHEMA,
        "stage": STAGE,
        "parent_stage": PARENT_STAGE,
        "age_ma": float(st.age_ma),
        "event_side": "POST_CHA1_20MY_DIVERSITY_RECOVERY",
        "elapsed_year": float(st.elapsed_year),
        "parent_r311_authority": parent_authority,
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
            "post_cha1_lifecycle_thaw_reapplied": False,
            "deep_biological_coupling": False,
            "ordinary_lifecycle_continued": True,
            "post_cha1_radiation_multiplier_used": False,
            "richness_target_used": False,
            "earth_analogue_target_used": False,
            "r37i_r38_production_runtime_reused": True,
            "mu_changed": False,
            "b_changed": False,
            "q_ceiling_changed": False,
            "scalar_k_physical_constant_authorized": False,
        },
    }
    jp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"json": str(jp), "npz": str(npzp), "json_sha256": _sha256(jp), "npz_sha256": _sha256(npzp)}


def save_smoke_checkpoint(st: r38.R38RuntimeState, out_dir: Path, cfg: R312Config) -> dict[str, Any]:
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"WORLD1_H0_{str(st.age_ma).replace('.', 'P')}Ma_R3_12_SMOKE_CHECKPOINT"
    jp = out_dir / f"{stem}.json"; npzp = out_dir / f"{stem}.npz"
    _save_state_arrays(st, npzp)
    meta = {
        "schema": SMOKE_SCHEMA, "stage": STAGE,
        "age_ma": float(st.age_ma), "elapsed_year": float(st.elapsed_year),
        "component_ids": st.component_ids, "root_species": st.root_species, "current_species": st.current_species,
        "registry": st.registry, "child_counters": st.child_counters, "baselines": st.baselines,
        "ri_state": r38._pair_dict_rows(st.ri_state), "clock_state": r38._pair_dict_rows(st.clock_state),
        "ext_state": st.ext_state, "founder_state": st.founder_state, "vicariance_state": st.vicariance_state,
        "reconnection_state": r38._pair_dict_rows(st.reconnection_state), "events": r38._jsonable(st.events),
        "snapshots": r38._jsonable(st.snapshots), "founder_stats_last": r38._jsonable(st.founder_stats_last),
        "gene_flow_closure": r38._jsonable(st.gene_flow_closure), "topology_remap_mass": st.topology_remap_mass,
        "initial_total_population": st.initial_total_population, "config": asdict(cfg), "npz_file": npzp.name,
    }
    jp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"json": str(jp), "npz": str(npzp), "json_sha256": _sha256(jp), "npz_sha256": _sha256(npzp)}


def load_diversity_checkpoint(json_path: Path, smoke: bool = False) -> r38.R38RuntimeState:
    jp = Path(json_path); m = json.loads(jp.read_text(encoding="utf-8"))
    expected = SMOKE_SCHEMA if smoke else SCHEMA
    if m.get("schema") != expected or m.get("stage") != STAGE:
        raise RuntimeError("R3.12 checkpoint metadata mismatch")
    if not smoke and (abs(float(m["age_ma"]) - END_AGE_MA) > 1e-12 or m.get("event_side") != "POST_CHA1_20MY_DIVERSITY_RECOVERY"):
        raise RuntimeError("R3.12 canonical checkpoint boundary mismatch")
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
