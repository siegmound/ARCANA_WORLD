from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import hashlib
import json

import numpy as np

import rebased_deep_time_barrier_provider_v0_6D1_R3 as bp
import rebased_natural_control_runtime_v0_6D1_R3_4 as r34
from arcana_worldsim.late_cenozoic.environment import late_cenozoic_environment_state

from . import r38_restartable_checkpoint as r38
from . import r312_postcha1_diversity_recovery as r312
from .segregation_potential_lifecycle import ReducedGeneticLifecycleState

STAGE = "v0.6D1-R3.13"
PARENT_STAGE = "v0.6D1-R3.12_SEALED"
SCHEMA = "ARCANA_R313_WORLD1_H0_30MA_LONGTERM_POST_CHA1_REASSEMBLY_CHECKPOINT_V1"
SMOKE_SCHEMA = "ARCANA_R313_SMOKE_CHECKPOINT_V1"
SUMMARY_SCHEMA = "ARCANA_R313_LONGTERM_POST_CHA1_REASSEMBLY_V1"

IMPACT_AGE_MA = 66.0
START_AGE_MA = 46.0
END_AGE_MA = 30.0
SMOKE_END_AGE_MA = 45.5
EXPECTED_STEPS = 128
EXPECTED_SMOKE_STEPS = 4
PARENT_SPECIES = 104
PARENT_COMPONENTS = 223
DIRECT_CHA1_SPECIES_LOSS_REFERENCE = 212


@dataclass(frozen=True)
class R313Config(r38.R38Config):
    end_age_ma: float = END_AGE_MA
    longterm_reassembly_start_age_ma: float = START_AGE_MA
    late_cenozoic_handoff_age_ma: float = END_AGE_MA
    reassembly_semantics: str = (
        "OBSERVE_ORDINARY_R37I_R38_LONG_HORIZON_DIVERSIFICATION_AND_ECOLOGICAL_REASSEMBLY_"
        "WITHOUT_RICHNESS_TARGET_GUILD_TARGET_OR_CROSS_GUILD_INSERTION"
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        if abs(self.longterm_reassembly_start_age_ma - START_AGE_MA) > 1e-12:
            raise ValueError("R3.13 canonical parent boundary remains 46.0 Ma")
        if abs(self.late_cenozoic_handoff_age_ma - END_AGE_MA) > 1e-12:
            raise ValueError("R3.13 canonical late-Cenozoic handoff remains 30.0 Ma")
        if abs(self.end_age_ma - END_AGE_MA) > 1e-12:
            raise ValueError("R3.13 canonical production endpoint is 30.0 Ma")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_parent_r312_authority(root: Path) -> dict[str, Any]:
    root = Path(root)
    seal_path = root / "R3_12_SEAL_SUMMARY.json"
    summary_path = root / "local_runs/v0_6D1_R3_12/R3_12_POST_CHA1_DIVERSITY_RECOVERY_SUMMARY.json"
    checkpoint_path = root / "local_runs/v0_6D1_R3_12/WORLD1_H0_46Ma_POST_CHA1_20MY_DIVERSITY_RECOVERY_CHECKPOINT_v0_6D1_R3_12.json"
    npz_path = checkpoint_path.with_suffix(".npz")
    for p in (seal_path, summary_path, checkpoint_path, npz_path):
        if not p.exists():
            raise RuntimeError(f"R3.13 requires materialized R3.12 SEALED evidence: missing {p}")

    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if seal.get("stage") != "v0.6D1-R3.12" or not str(seal.get("verdict", "")).endswith("46MA_RESTART_BOUNDARY_SEALED"):
        raise RuntimeError("R3.12 seal verdict is not authoritative")
    if not str(summary.get("verdict", "")).startswith("PASS_CANONICAL_POST_CHA1_61_TO_46_H0_DIVERSITY_RECOVERY"):
        raise RuntimeError("R3.12 parent run verdict is not authoritative")
    boundary = seal.get("boundary", {})
    if abs(float(boundary.get("age_ma", -1.0)) - START_AGE_MA) > 1e-12:
        raise RuntimeError("R3.12 boundary age mismatch")
    if boundary.get("event_side") != "POST_CHA1_20MY_DIVERSITY_RECOVERY":
        raise RuntimeError("R3.12 boundary event-side mismatch")
    if int(boundary.get("species", -1)) != PARENT_SPECIES or int(boundary.get("components", -1)) != PARENT_COMPONENTS:
        raise RuntimeError("R3.12 parent cardinality mismatch")

    hashes = seal.get("hashes", {})
    expected_s = str(hashes.get("summary", ""))
    expected_j = str(hashes.get("checkpoint_json", ""))
    expected_n = str(hashes.get("checkpoint_npz", ""))
    if _sha256(summary_path) != expected_s:
        raise RuntimeError("R3.12 summary hash mismatch")
    if _sha256(checkpoint_path) != expected_j or _sha256(npz_path) != expected_n:
        raise RuntimeError("R3.12 checkpoint hash mismatch")

    st = r312.load_diversity_checkpoint(checkpoint_path, smoke=False)
    if abs(st.age_ma - START_AGE_MA) > 1e-12 or abs(st.elapsed_year - 164_000_000.0) > 1e-6:
        raise RuntimeError("R3.12 chronology mismatch")
    if len(set(st.current_species)) != PARENT_SPECIES or len(st.component_ids) != PARENT_COMPONENTS:
        raise RuntimeError("R3.12 loaded state cardinality mismatch")
    counts = r312.event_counts(st)
    if counts["CHA1_species_extinction"] != DIRECT_CHA1_SPECIES_LOSS_REFERENCE:
        raise RuntimeError("R3.12 lost CHA-1 extinction authority")
    if counts["CHA1_high_resolution_event_bridge_complete"] != 1:
        raise RuntimeError("R3.12 must contain exactly one completed CHA-1 bridge")
    if counts["post_CHA1_ordinary_lifecycle_thaw"] != 1:
        raise RuntimeError("R3.12 must contain exactly one lifecycle thaw")

    return {
        "state": st,
        "seal_verdict": str(seal.get("verdict")),
        "seal_summary_sha256": _sha256(seal_path),
        "summary_sha256": expected_s,
        "checkpoint_json": str(checkpoint_path.relative_to(root)),
        "checkpoint_npz": str(npz_path.relative_to(root)),
        "checkpoint_json_sha256": expected_j,
        "checkpoint_npz_sha256": expected_n,
    }


def run_longterm_reassembly(parent_state: r38.R38RuntimeState, a1, metadata_rows: list[dict[str, Any]],
                            cfg: R313Config | None = None, end_age_ma: float = END_AGE_MA):
    cfg = cfg or R313Config()
    if abs(parent_state.age_ma - START_AGE_MA) > 1e-12:
        raise ValueError("R3.13 must start from exact 46.0 Ma R3.12 SEALED boundary")
    if end_age_ma > START_AGE_MA - cfg.biology_cadence_years / 1e6 + 1e-12:
        raise ValueError("R3.13 must include at least one ordinary biology step")
    if end_age_ma < END_AGE_MA - 1e-12:
        raise ValueError("R3.13 may not cross the 30 Ma late-Cenozoic handoff boundary")
    st = r312.r311._clone_state(parent_state)
    return r38.advance_state(st, a1, metadata_rows, cfg, float(end_age_ma))


def event_counts(st):
    return r312.event_counts(st)


def delta_event_counts(before, after):
    return r312.delta_event_counts(before, after)


def species_counts_by_guild(st):
    return r312.species_counts_by_guild(st)


def root_lineage_profile(st):
    return r312.root_lineage_profile(st)


def invariant_report(st, metadata_rows, cfg):
    return r312.invariant_report(st, metadata_rows, cfg)


def _guild_population(st: r38.R38RuntimeState) -> dict[str, float]:
    out: dict[str, float] = {}
    for gid in sorted(set(np.asarray(st.guild, dtype=int).tolist())):
        out[str(gid)] = float(st.pop[np.asarray(st.guild, dtype=int) == gid].sum())
    return out


def _guild_components(st: r38.R38RuntimeState) -> dict[str, int]:
    out: dict[str, int] = {}
    g = np.asarray(st.guild, dtype=int)
    for gid in sorted(set(g.tolist())):
        out[str(gid)] = int(np.count_nonzero(g == gid))
    return out


def ecological_reassembly_report(parent_state: r38.R38RuntimeState, final_state: r38.R38RuntimeState) -> dict[str, Any]:
    ps = species_counts_by_guild(parent_state); fs = species_counts_by_guild(final_state)
    pp = _guild_population(parent_state); fp = _guild_population(final_state)
    pc = _guild_components(parent_state); fc = _guild_components(final_state)
    gids = sorted(set(str(i) for i in range(1, 7)) | set(ps) | set(fs) | set(pp) | set(fp) | set(pc) | set(fc), key=int)
    guilds = {}
    for gid in gids:
        guilds[gid] = {
            "species_at_46Ma": int(ps.get(gid, 0)),
            "species_at_end": int(fs.get(gid, 0)),
            "net_species_change": int(fs.get(gid, 0) - ps.get(gid, 0)),
            "components_at_46Ma": int(pc.get(gid, 0)),
            "components_at_end": int(fc.get(gid, 0)),
            "population_at_46Ma": float(pp.get(gid, 0.0)),
            "population_at_end": float(fp.get(gid, 0.0)),
        }
    start_absent = sorted([int(g) for g in gids if int(ps.get(g, 0)) == 0])
    end_absent = sorted([int(g) for g in gids if int(fs.get(g, 0)) == 0])
    return {
        "descriptive_not_acceptance_target": True,
        "guilds": guilds,
        "active_guild_count_at_46Ma": sum(int(ps.get(g, 0)) > 0 for g in gids),
        "active_guild_count_at_end": sum(int(fs.get(g, 0)) > 0 for g in gids),
        "guilds_absent_at_46Ma": start_absent,
        "guilds_absent_at_end": end_absent,
        "root_lineages_at_46Ma": root_lineage_profile(parent_state),
        "root_lineages_at_end": root_lineage_profile(final_state),
        "cross_guild_recreation_authorized": False,
        "cross_guild_guard": (
            "R3.7I/R3.8 speciation inherits parent guild_id. R3.13 does not activate the separate historical trophic-mode/cross-guild operator; "
            "therefore an already absent guild is not expected to reappear in this stage. This is an inherited model-scope fact, not a recovery target."
        ),
    }


def classify_speciation_origin_from_r312_boundary(parent_state, new_events: list[dict[str, Any]]) -> dict[str, Any]:
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
            "age_ma": e.get("age_ma"), "parent_species_id": e.get("parent_species_id"),
            "daughter_species_id": e.get("daughter_species_id"),
            "classification": "MATCHED_R312_BOUNDARY_FOUNDER_CARRYOVER" if matched else "NOT_MATCHED_TO_R312_BOUNDARY_FOUNDER_STATE",
        })
    return {
        "founder_candidates_at_46Ma": len(parent_state.founder_state),
        "matched_46Ma_founder_carryover_speciations": sum(r["classification"].startswith("MATCHED") for r in rows),
        "not_matched_to_46Ma_founder_state": sum(not r["classification"].startswith("MATCHED") for r in rows),
        "rows": rows,
        "interpretation_guard": "Boundary-founder matching is timing provenance only; it is not a causal attribution to CHA-1 or to ecological opportunity.",
    }


def validate_30ma_environment_handoff(a1, cfg: R313Config | None = None) -> dict[str, Any]:
    cfg = cfg or R313Config()
    old = bp.environment_at(END_AGE_MA, a1, r34.barrier_cfg(cfg))
    late = late_cenozoic_environment_state(a1, END_AGE_MA)
    fields = ("land_support", "temperature_c", "aridity_index", "browse_forage", "low_forage", "wetland_forage", "total_edible_forage")
    diffs = {}
    exact = True
    for k in fields:
        a = np.asarray(old[k]); b = np.asarray(late[k])
        err = float(np.max(np.abs(a - b))) if a.size else 0.0
        same = bool(np.array_equal(a, b))
        diffs[k] = {"exact": same, "max_abs_error": err}
        exact = exact and same
    return {
        "age_ma": END_AGE_MA,
        "environmental_endpoint_identity_exact": bool(exact),
        "fields": diffs,
        "current_provider": str(old.get("paleogeographic_history_provider", "R3_BARRIER_PROVIDER")),
        "next_provider_source": "arcana_worldsim.late_cenozoic.environment.late_cenozoic_environment_state",
        "next_provider_domain_starts_at_30Ma": True,
        "biology_switched_in_r313": False,
        "interpretation": "R3.13 stops at the exact common 30 Ma environmental endpoint. The late-Cenozoic provider is not activated inside R3.13.",
    }


def _save_state_arrays(st, npzp: Path) -> None:
    np.savez_compressed(
        npzp, guild=st.guild, population=st.pop, trait=st.trait, va=st.va,
        generation_time=st.gen, current_accessible=st.current_accessible.astype(np.uint8),
        reduced_va_within=st.reduced_state.va_within,
        reduced_ancestry_covariance=st.reduced_state.ancestry_covariance,
        reduced_neutral_segregation_potential=st.reduced_state.neutral_segregation_potential,
        reduced_adaptive_coordinate=st.reduced_state.adaptive_coordinate,
        lat=np.asarray(st._lat, dtype=float), lon=np.asarray(st._lon, dtype=float),
    )


def _metadata(st, cfg, parent_authority, run_report, schema, event_side, npz_name):
    return {
        "schema": schema, "stage": STAGE, "parent_stage": PARENT_STAGE,
        "age_ma": float(st.age_ma), "event_side": event_side, "elapsed_year": float(st.elapsed_year),
        "parent_r312_authority": parent_authority,
        "nominal_reduced_order_reference": {"label": "K_CENTER", "K_eff": r38.NOMINAL_K, "semantic_role": "OPERATIONAL_REDUCED_ORDER_COORDINATE_REFERENCE_NOT_PHYSICAL_CONSTANT"},
        "component_ids": st.component_ids, "root_species": st.root_species, "current_species": st.current_species,
        "registry": st.registry, "child_counters": st.child_counters, "baselines": st.baselines,
        "ri_state": r38._pair_dict_rows(st.ri_state), "clock_state": r38._pair_dict_rows(st.clock_state),
        "ext_state": st.ext_state, "founder_state": st.founder_state, "vicariance_state": st.vicariance_state,
        "reconnection_state": r38._pair_dict_rows(st.reconnection_state), "events": r38._jsonable(st.events),
        "snapshots": r38._jsonable(st.snapshots), "founder_stats_last": r38._jsonable(st.founder_stats_last),
        "gene_flow_closure": r38._jsonable(st.gene_flow_closure), "topology_remap_mass": st.topology_remap_mass,
        "initial_total_population": st.initial_total_population, "config": asdict(cfg), "run_report": run_report,
        "npz_file": npz_name,
        "governance": {
            "cha1_already_applied": True, "cha1_reapplied": False, "post_cha1_lifecycle_thaw_reapplied": False,
            "deep_biological_coupling": False, "ordinary_lifecycle_continued": True,
            "post_cha1_radiation_multiplier_used": False, "richness_target_used": False, "guild_target_used": False,
            "cross_guild_transition_operator_activated": False, "late_cenozoic_provider_activated_inside_stage": False,
            "r37i_r38_production_runtime_reused": True, "mu_changed": False, "b_changed": False,
            "q_ceiling_changed": False, "scalar_k_physical_constant_authorized": False,
        },
    }


def save_checkpoint(st, out_dir: Path, parent_authority: dict[str, Any], cfg: R313Config, run_report: dict[str, Any], smoke: bool = False):
    if not smoke and abs(st.age_ma - END_AGE_MA) > 1e-12:
        raise ValueError("canonical R3.13 checkpoint must be exactly 30.0 Ma")
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    if smoke:
        stem = f"WORLD1_H0_{str(st.age_ma).replace('.', 'P')}Ma_R3_13_SMOKE_CHECKPOINT"
        schema = SMOKE_SCHEMA; event_side = "R3_13_SMOKE"
    else:
        stem = "WORLD1_H0_30Ma_LONG_TERM_POST_CHA1_DIVERSIFICATION_REASSEMBLY_CHECKPOINT_v0_6D1_R3_13"
        schema = SCHEMA; event_side = "POST_CHA1_36MY_LONG_TERM_REASSEMBLY"
    jp = out_dir / f"{stem}.json"; npzp = out_dir / f"{stem}.npz"
    _save_state_arrays(st, npzp)
    meta = _metadata(st, cfg, parent_authority, run_report, schema, event_side, npzp.name)
    jp.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"json": str(jp), "npz": str(npzp), "json_sha256": _sha256(jp), "npz_sha256": _sha256(npzp)}


def load_checkpoint(json_path: Path, smoke: bool = False):
    jp = Path(json_path); m = json.loads(jp.read_text(encoding="utf-8"))
    expected = SMOKE_SCHEMA if smoke else SCHEMA
    if m.get("schema") != expected or m.get("stage") != STAGE:
        raise RuntimeError("R3.13 checkpoint metadata mismatch")
    if not smoke and (abs(float(m["age_ma"]) - END_AGE_MA) > 1e-12 or m.get("event_side") != "POST_CHA1_36MY_LONG_TERM_REASSEMBLY"):
        raise RuntimeError("R3.13 canonical checkpoint boundary mismatch")
    z = np.load(jp.parent / m["npz_file"], allow_pickle=False)
    st = r38.R38RuntimeState(
        age_ma=float(m["age_ma"]), elapsed_year=float(m["elapsed_year"]), component_ids=list(m["component_ids"]),
        root_species=list(m["root_species"]), current_species=list(m["current_species"]), guild=z["guild"].astype(np.uint8),
        pop=z["population"].astype(float), trait=z["trait"].astype(float), va=z["va"].astype(float),
        gen=z["generation_time"].astype(float), registry={str(k): dict(v) for k, v in m["registry"].items()},
        child_counters={str(k): int(v) for k, v in m["child_counters"].items()}, current_accessible=z["current_accessible"].astype(bool),
        baselines=m["baselines"], ri_state={k: float(v) for k, v in r38._pair_dict_from_rows(m["ri_state"]).items()},
        clock_state={k: float(v) for k, v in r38._pair_dict_from_rows(m["clock_state"]).items()}, ext_state=m["ext_state"],
        founder_state=m["founder_state"], vicariance_state=m["vicariance_state"],
        reconnection_state={k: dict(v) for k, v in r38._pair_dict_from_rows(m["reconnection_state"]).items()},
        events=list(m["events"]), snapshots=list(m["snapshots"]), founder_stats_last=list(m["founder_stats_last"]),
        gene_flow_closure=dict(m["gene_flow_closure"]), topology_remap_mass=float(m["topology_remap_mass"]),
        initial_total_population=float(m["initial_total_population"]),
        reduced_state=ReducedGeneticLifecycleState(z["reduced_va_within"].astype(float), z["reduced_ancestry_covariance"].astype(float),
            z["reduced_neutral_segregation_potential"].astype(float), z["reduced_adaptive_coordinate"].astype(float)),
    )
    st._lat = z["lat"].astype(float); st._lon = z["lon"].astype(float)
    return st
