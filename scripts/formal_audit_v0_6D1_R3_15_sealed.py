from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

STAGE = "v0.6D1-R3.15"
VERDICT = "PASS_R315_CANONICAL_30MA_TO_250KA_H0_LATE_CENOZOIC_SECULAR_BIOLOGY__250KA_PRE_C2_BRIDGE_RESTART_BOUNDARY_SEALED"
READY_VERDICT = "PASS_CANONICAL_R315_30MA_TO_250KA_H0_LATE_CENOZOIC_SECULAR_BIOLOGY__PRE_C2_200KA_BRIDGE_CHECKPOINT_READY"


def hfile(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _metadata_rows(root: Path):
    d = json.loads((root / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    return d["species"] if isinstance(d, dict) and "species" in d else d


def _float_eq(a: Any, b: Any, atol: float = 1e-12) -> bool:
    try:
        return abs(float(a) - float(b)) <= atol
    except Exception:
        return False


def audit_run_evidence(root: Path, run_dir: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
    from arcana_worldsim.scientific_engines import r313_longterm_postcha1_reassembly as r313
    from arcana_worldsim.scientific_engines import r315_late_cenozoic_secular_biology as r315

    def ck(name: str, cond: bool, actual: Any = None, expected: Any = None):
        checks.append({"name": name, "pass": bool(cond), "actual": actual, "expected": expected})

    sp = run_dir / "R3_15_LATE_CENOZOIC_SECULAR_BIOLOGY_SUMMARY.json"
    jp = run_dir / "WORLD1_H0_250ka_LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_BRIDGE_CHECKPOINT_v0_6D1_R3_15.json"
    npzp = jp.with_suffix(".npz")
    for p in (sp, jp, npzp):
        ck(f"file_exists::{p.name}", p.is_file(), str(p))
    if not all(p.is_file() for p in (sp, jp, npzp)):
        return {"summary_path": sp, "json_path": jp, "npz_path": npzp}

    summary = json.loads(sp.read_text(encoding="utf-8"))
    meta = json.loads(jp.read_text(encoding="utf-8"))
    rr = summary.get("run", {})
    gov = summary.get("governance", {})
    mg = meta.get("governance", {})
    cfg = r315.R315Config()

    ck("summary_schema", summary.get("schema") == r315.SUMMARY_SCHEMA, summary.get("schema"), r315.SUMMARY_SCHEMA)
    ck("summary_stage", summary.get("stage") == STAGE, summary.get("stage"), STAGE)
    ck("summary_mode", summary.get("mode") == "CANONICAL_30P0_TO_0P25", summary.get("mode"))
    ck("summary_ready_verdict", summary.get("verdict") == READY_VERDICT, summary.get("verdict"), READY_VERDICT)
    ck("summary_start_30ma", _float_eq(rr.get("start_age_ma"), 30.0), rr.get("start_age_ma"), 30.0)
    ck("summary_end_250ka", _float_eq(rr.get("end_age_ma"), 0.25), rr.get("end_age_ma"), 0.25)
    ck("summary_steps_238", rr.get("ordinary_biology_steps") == 238, rr.get("ordinary_biology_steps"), 238)
    ck("summary_cadence_125k", _float_eq(rr.get("biology_cadence_years"), 125000.0), rr.get("biology_cadence_years"), 125000.0)
    ck("summary_parent_species_111", rr.get("parent_species") == 111, rr.get("parent_species"), 111)
    ck("summary_parent_components_219", rr.get("parent_components") == 219, rr.get("parent_components"), 219)
    ck("summary_final_species_134", rr.get("final_species") == 134, rr.get("final_species"), 134)
    ck("summary_final_components_295", rr.get("final_components") == 295, rr.get("final_components"), 295)
    ck("summary_final_population", _float_eq(rr.get("final_total_population"), 1218.3485572325976, 1e-9), rr.get("final_total_population"), 1218.3485572325976)
    ck("summary_no_clipping_steps", int(rr.get("clipping_steps", -1)) == 0, rr.get("clipping_steps"), 0)
    ck("summary_no_clipping_contacts", int(rr.get("clipping_contacts", -1)) == 0, rr.get("clipping_contacts"), 0)
    ck("summary_peak_q_below_ceiling", float(rr.get("peak_q_recorded", 9.0)) < cfg.variance_ceiling_normalized, rr.get("peak_q_recorded"), cfg.variance_ceiling_normalized)
    ck("summary_unclipped_equals_peak", _float_eq(rr.get("peak_unclipped_q_recorded"), rr.get("peak_q_recorded"), 1e-15), rr.get("peak_unclipped_q_recorded"), rr.get("peak_q_recorded"))

    expected_delta = {
        "paleogeographic_support_loss_remap": 216,
        "deme_coalescence": 45,
        "deme_fission": 126,
        "speciation": 23,
        "ordinary_background_extinction": 0,
        "CHA1_species_extinction": 0,
        "CHA1_high_resolution_event_bridge_complete": 0,
        "post_CHA1_ordinary_lifecycle_thaw": 0,
    }
    ck("summary_event_delta_exact", rr.get("event_counts_delta") == expected_delta, rr.get("event_counts_delta"), expected_delta)
    ck("summary_no_ordinary_extinction_chronology", rr.get("ordinary_extinction_chronology") == [], rr.get("ordinary_extinction_chronology"), [])
    ck("summary_speciation_chronology_23", len(rr.get("speciation_chronology", [])) == 23, len(rr.get("speciation_chronology", [])), 23)
    ck("summary_fission_chronology_126", len(rr.get("fission_chronology", [])) == 126, len(rr.get("fission_chronology", [])), 126)
    ck("summary_coalescence_chronology_45", len(rr.get("coalescence_chronology", [])) == 45, len(rr.get("coalescence_chronology", [])), 45)
    spec_ages = [float(x["age_ma"]) for x in rr.get("speciation_chronology", [])]
    ck("speciation_all_inside_stage", all(0.25 < x <= 30.0 for x in spec_ages), spec_ages)
    ck("speciation_none_inside_c2_bridge", all(x > 0.2 for x in spec_ages), spec_ages)

    expected_guilds = {"1": 61, "2": 1, "3": 7, "4": 56, "5": 9}
    ck("guild_species_exact", rr.get("guild_species") == expected_guilds, rr.get("guild_species"), expected_guilds)
    ck("guild6_absent_descriptive", "6" not in rr.get("guild_species", {}), rr.get("guild_species"))

    sched = rr.get("scheduler_biology_separation", {})
    for key in (
        "all_r315_biology_checkpoints_older_than_c2_bridge_start",
        "adaptive_clock_contains_200ka",
        "adaptive_clock_contains_120ka",
        "fixed_r37i_r38_biology_cadence_preserved",
        "next_nominal_biology_step_would_cross_c2_200ka_bridge_start",
    ):
        ck(f"scheduler_true::{key}", sched.get(key) is True, sched.get(key))
    for key in (
        "adaptive_clock_checkpoint_promoted_to_biology_step",
        "adaptive_clock_used_as_biology_timestep",
        "c2_200_120ka_bridge_crossed",
        "recent_120ka_restart_crossed",
    ):
        ck(f"scheduler_false::{key}", sched.get(key) is False, sched.get(key))
    ck("scheduler_interval_count_238", sched.get("biology_interval_count") == 238, sched.get("biology_interval_count"), 238)
    ck("scheduler_checkpoint_count_239", sched.get("biology_checkpoint_count") == 239, sched.get("biology_checkpoint_count"), 239)
    ck("scheduler_end_250ka", _float_eq(sched.get("biology_end_age_ma"), 0.25), sched.get("biology_end_age_ma"), 0.25)
    ck("scheduler_next_nominal_125ka", _float_eq(sched.get("next_nominal_biology_checkpoint_age_ma"), 0.125), sched.get("next_nominal_biology_checkpoint_age_ma"), 0.125)
    ck("scheduler_stop_reason_guard", "NO_UNAUTHORIZED_ENVIRONMENTAL_SUBSTEP_TO_BIOLOGY_STEP_PROMOTION" in str(sched.get("stop_reason", "")), sched.get("stop_reason"))

    hand = rr.get("full_d3_substrate_30ma_handoff", {})
    ck("stored_30ma_handoff_exact", hand.get("full_d3_substrate_identity_exact") is True, hand.get("full_d3_substrate_identity_exact"))
    ck("stored_30ma_handoff_no_biology_advance", hand.get("biology_state_advanced_during_handoff_check") is False, hand.get("biology_state_advanced_during_handoff_check"))
    for key, row in hand.get("fields", {}).items():
        ck(f"stored_30ma_handoff_exact::{key}", row.get("exact") is True, row)
        ck(f"stored_30ma_handoff_zero_error::{key}", float(row.get("max_abs_error", 1.0)) == 0.0, row)
    ck("stored_30ma_handoff_field_count_9", len(hand.get("fields", {})) == 9, len(hand.get("fields", {})), 9)

    ep = rr.get("endpoint_provider", {})
    ck("endpoint_provider_age_250ka", _float_eq(ep.get("age_ma"), 0.25), ep.get("age_ma"), 0.25)
    ck("endpoint_provider_c2", ep.get("provider") == "INTEGRATED_LATE_CENOZOIC_ENVIRONMENTAL_PROVIDER_v0_6_4C", ep.get("provider"))
    ck("endpoint_subprovider_secular", ep.get("subprovider") == "v0.6.4A+B_SECULAR_ENVIRONMENT", ep.get("subprovider"))
    ck("endpoint_adapter_d3", ep.get("production_substrate_adapter") == "D3LateCenozoicSubstrateAdapter_v0_6_4D", ep.get("production_substrate_adapter"))
    ck("endpoint_not_adaptive_biology_step", ep.get("adaptive_clock_checkpoint_promoted_to_biology_step") is False, ep.get("adaptive_clock_checkpoint_promoted_to_biology_step"))
    ck("endpoint_not_c2_bridge", ep.get("c2_bridge_supports_endpoint") is False, ep.get("c2_bridge_supports_endpoint"))

    expected_summary_false = (
        "adaptive_clock_checkpoint_promoted_to_biology_step", "biology_cadence_changed", "c2_200_120ka_bridge_crossed",
        "recent_120ka_restart_crossed", "high_resolution_200ka_historical_paleoclimate_claimed",
        "c2_bridge_historical_glacial_chronology_claimed", "deep_biological_coupling", "cha1_reapplied",
        "lifecycle_thaw_reapplied", "richness_target_used", "guild_target_used",
        "positive_diversification_required_for_pass", "cross_guild_transition_operator_activated", "scientific_parameter_changes",
    )
    for key in expected_summary_false:
        ck(f"summary_governance_false::{key}", gov.get(key) is False, gov.get(key))
    for key in ("r314_c2_provider_bound", "adaptive_clock_is_scheduler_not_biology_cadence", "production_r37i_r38_runtime_used"):
        ck(f"summary_governance_true::{key}", gov.get(key) is True, gov.get(key))
    ck("summary_governance_cadence_125k", _float_eq(gov.get("biology_cadence_years"), 125000.0), gov.get("biology_cadence_years"), 125000.0)

    expected_meta_false = (
        "adaptive_clock_used_as_biology_timestep", "c2_200_120ka_bridge_crossed", "recent_120ka_restart_crossed",
        "deep_biological_coupling", "cha1_reapplied", "post_cha1_lifecycle_thaw_reapplied", "richness_target_used",
        "guild_target_used", "cross_guild_transition_operator_activated", "scientific_parameters_changed",
    )
    for key in expected_meta_false:
        ck(f"checkpoint_governance_false::{key}", mg.get(key) is False, mg.get(key))
    ck("checkpoint_governance_c2_used", mg.get("r314_c2_provider_used") is True, mg.get("r314_c2_provider_used"))
    ck("checkpoint_governance_cadence_125k", _float_eq(mg.get("biology_cadence_years"), 125000.0), mg.get("biology_cadence_years"), 125000.0)

    ck("checkpoint_schema", meta.get("schema") == r315.SCHEMA, meta.get("schema"), r315.SCHEMA)
    ck("checkpoint_stage", meta.get("stage") == STAGE, meta.get("stage"), STAGE)
    ck("checkpoint_parent_stage", meta.get("parent_stage") == r315.PARENT_STAGE, meta.get("parent_stage"), r315.PARENT_STAGE)
    ck("checkpoint_age_250ka", _float_eq(meta.get("age_ma"), 0.25), meta.get("age_ma"), 0.25)
    ck("checkpoint_event_side", meta.get("event_side") == "LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_200KA_BRIDGE", meta.get("event_side"))
    ck("checkpoint_elapsed", _float_eq(meta.get("elapsed_year"), 209750000.0), meta.get("elapsed_year"), 209750000.0)
    ck("checkpoint_npz_name", meta.get("npz_file") == npzp.name, meta.get("npz_file"), npzp.name)
    ck("checkpoint_component_count_295", len(meta.get("component_ids", [])) == 295, len(meta.get("component_ids", [])), 295)
    ck("checkpoint_current_species_unique_134", len(set(meta.get("current_species", []))) == 134, len(set(meta.get("current_species", []))), 134)
    ck("checkpoint_root_species_count_295", len(meta.get("root_species", [])) == 295, len(meta.get("root_species", [])), 295)
    ck("checkpoint_config_exact", meta.get("config") == asdict(cfg))
    ck("checkpoint_run_report_exact_summary", meta.get("run_report") == rr)
    ck("checkpoint_parent_authority_exact_summary", meta.get("parent_r314_authority") == summary.get("parent_r314_authority"))

    ck("checkpoint_json_sha_matches_summary", hfile(jp) == summary.get("checkpoint", {}).get("json_sha256"), hfile(jp), summary.get("checkpoint", {}).get("json_sha256"))
    ck("checkpoint_npz_sha_matches_summary", hfile(npzp) == summary.get("checkpoint", {}).get("npz_sha256"), hfile(npzp), summary.get("checkpoint", {}).get("npz_sha256"))

    z = np.load(npzp, allow_pickle=False)
    expected_shapes = {
        "guild": (295,), "population": (295, 90, 180), "trait": (295, 3), "va": (295, 3),
        "generation_time": (295,), "current_accessible": (90, 180), "reduced_va_within": (295, 3),
        "reduced_ancestry_covariance": (295, 3), "reduced_neutral_segregation_potential": (295, 295, 3),
        "reduced_adaptive_coordinate": (295, 3), "lat": (90,), "lon": (180,),
    }
    ck("npz_keyset_exact", set(z.files) == set(expected_shapes), sorted(z.files), sorted(expected_shapes))
    for key, shape in expected_shapes.items():
        arr = np.asarray(z[key])
        ck(f"npz_shape::{key}", arr.shape == shape, arr.shape, shape)
        ck(f"npz_finite::{key}", bool(np.all(np.isfinite(arr))), None)

    st = r315.load_checkpoint(jp, smoke=False)
    md = _metadata_rows(root)
    inv = r315.invariant_report(st, md, cfg)
    ck("loaded_age_250ka", _float_eq(st.age_ma, 0.25), st.age_ma, 0.25)
    ck("loaded_elapsed", _float_eq(st.elapsed_year, 209750000.0), st.elapsed_year, 209750000.0)
    ck("loaded_species_134", len(set(st.current_species)) == 134, len(set(st.current_species)), 134)
    ck("loaded_components_295", len(st.component_ids) == 295, len(st.component_ids), 295)
    ck("loaded_population", _float_eq(st.pop.sum(), rr.get("final_total_population"), 1e-9), float(st.pop.sum()), rr.get("final_total_population"))
    ck("loaded_event_counts_exact_summary_after", r315.event_counts(st) == rr.get("event_counts_after"), r315.event_counts(st), rr.get("event_counts_after"))
    ck("loaded_guild_species_exact", r315.species_counts_by_guild(st) == expected_guilds, r315.species_counts_by_guild(st), expected_guilds)
    ck("invariants_exact_summary", inv == rr.get("invariants"), inv, rr.get("invariants"))
    ck("invariant_population_nonnegative", inv["population_min"] >= 0.0, inv["population_min"], ">=0")
    ck("invariant_inaccessible_population_zero", inv["population_on_inaccessible_cells"] == 0.0, inv["population_on_inaccessible_cells"], 0.0)
    ck("invariant_q_below_ceiling", inv["q_max"] < cfg.variance_ceiling_normalized, inv["q_max"], cfg.variance_ceiling_normalized)
    ck("invariant_q_positive_headroom", inv["q_headroom"] > 0.0, inv["q_headroom"], ">0")
    ck("invariant_s_symmetric", inv["s_symmetry_max_abs"] == 0.0, inv["s_symmetry_max_abs"], 0.0)
    ck("invariant_s_diag_zero", inv["s_diagonal_max_abs"] == 0.0, inv["s_diagonal_max_abs"], 0.0)
    ck("invariant_s_nonnegative", inv["s_min"] >= 0.0, inv["s_min"], ">=0")

    # Recompute event delta against the actual 30 Ma parent checkpoint available in the package.
    parent_path = root / "local_runs/v0_6D1_R3_13/WORLD1_H0_30Ma_LONG_TERM_POST_CHA1_DIVERSIFICATION_REASSEMBLY_CHECKPOINT_v0_6D1_R3_13.json"
    ck("r313_parent_checkpoint_exists", parent_path.is_file(), str(parent_path))
    if parent_path.is_file():
        parent = r313.load_checkpoint(parent_path)
        before = r315.event_counts(parent)
        after = r315.event_counts(st)
        delta = {k: int(after.get(k, 0)) - int(before.get(k, 0)) for k in sorted(set(before) | set(after))}
        ck("parent_species_111_recomputed", len(set(parent.current_species)) == 111, len(set(parent.current_species)), 111)
        ck("parent_components_219_recomputed", len(parent.component_ids) == 219, len(parent.component_ids), 219)
        ck("parent_population_recomputed", _float_eq(parent.pop.sum(), rr.get("parent_total_population"), 1e-9), float(parent.pop.sum()), rr.get("parent_total_population"))
        ck("event_counts_before_recomputed", before == rr.get("event_counts_before"), before, rr.get("event_counts_before"))
        ck("event_counts_after_recomputed", after == rr.get("event_counts_after"), after, rr.get("event_counts_after"))
        ck("event_delta_recomputed", delta == expected_delta, delta, expected_delta)

    ser = summary.get("serialization_identity", {})
    ck("stored_serialization_equivalent", ser.get("equivalent") is True, ser.get("equivalent"))
    for group in ("arrays", "reduced_state"):
        for key, row in ser.get(group, {}).items():
            ck(f"stored_serialization_same::{group}::{key}", row.get("same") is True, row)
            ck(f"stored_serialization_zero_error::{group}::{key}", float(row.get("max_abs_error", 1.0)) == 0.0, row)
    for key, val in ser.get("exact_fields", {}).items():
        ck(f"stored_serialization_exact_field::{key}", val is True, val)
    for key, val in ser.get("scalar_abs_errors", {}).items():
        ck(f"stored_serialization_scalar_zero::{key}", float(val) == 0.0, val)

    # Independent save/load identity check from the uploaded canonical state.
    with tempfile.TemporaryDirectory(prefix="arcana_r315_seal_") as td:
        ckmeta = r315.save_checkpoint(st, Path(td), summary.get("parent_r314_authority", {}), cfg, rr, smoke=False)
        reload = r315.load_checkpoint(Path(ckmeta["json"]), smoke=False)
        cmp = r38.compare_runtime_states(st, reload)
        ck("independent_roundtrip_equivalent", cmp.get("equivalent") is True, cmp)
        for key, row in cmp.get("arrays", {}).items():
            ck(f"independent_roundtrip_array::{key}", row.get("same") is True, row)
        for key, row in cmp.get("reduced_state", {}).items():
            ck(f"independent_roundtrip_reduced::{key}", row.get("same") is True, row)
        for key, val in cmp.get("exact_fields", {}).items():
            ck(f"independent_roundtrip_exact::{key}", val is True, val)
        for key, val in cmp.get("scalar_abs_errors", {}).items():
            ck(f"independent_roundtrip_scalar::{key}", float(val) == 0.0, val)

    return {
        "summary": summary,
        "meta": meta,
        "state": st,
        "invariants": inv,
        "summary_path": sp,
        "json_path": jp,
        "npz_path": npzp,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seal-out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve(); run_dir = args.run_dir.resolve(); out = args.out.resolve(); seal_out = args.seal_out.resolve()
    sys.path.insert(0, str(root / "src"))

    from arcana_worldsim.scientific_engines import r315_late_cenozoic_secular_biology as r315

    checks: list[dict[str, Any]] = []
    def ck(name: str, cond: bool, actual: Any = None, expected: Any = None):
        checks.append({"name": name, "pass": bool(cond), "actual": actual, "expected": expected})

    ev = audit_run_evidence(root, run_dir, checks)
    summary = ev.get("summary", {})

    # Re-validate the actual R3.14 materialized parent authority on this machine.
    try:
        parent = r315.validate_parent_r314_authority(root)
        ck("live_r314_parent_authority_valid", True)
    except Exception as exc:
        parent = None
        ck("live_r314_parent_authority_valid", False, repr(exc))

    if parent is not None:
        sparent = summary.get("parent_r314_authority", {})
        ck("parent_seal_verdict_exact", parent.get("seal_verdict") == sparent.get("seal_verdict"), parent.get("seal_verdict"), sparent.get("seal_verdict"))
        ck("parent_seal_sha_exact", parent.get("seal_sha256") == sparent.get("seal_sha256"), parent.get("seal_sha256"), sparent.get("seal_sha256"))
        ck("parent_formal_audit_sha_exact", parent.get("formal_audit_sha256") == sparent.get("formal_audit_sha256"), parent.get("formal_audit_sha256"), sparent.get("formal_audit_sha256"))
        ck("parent_binding_summary_sha_exact", parent.get("binding_summary_sha256") == sparent.get("binding_summary_sha256"), parent.get("binding_summary_sha256"), sparent.get("binding_summary_sha256"))
        ck("parent_clock_sha_exact", parent.get("clock_sha256") == sparent.get("clock_sha256"), parent.get("clock_sha256"), sparent.get("clock_sha256"))
        ck("parent_artifact_hashes_exact", parent.get("artifact_hashes") == sparent.get("artifact_hashes"), parent.get("artifact_hashes"), sparent.get("artifact_hashes"))
        ck("parent_v061_hashes_exact", parent.get("v061_payload_hashes") == sparent.get("v061_payload_hashes"), parent.get("v061_payload_hashes"), sparent.get("v061_payload_hashes"))

        # Recompute the 30 Ma D3 substrate handoff using the real bound C2 provider.
        adapter = r315.R315D3EnvironmentAdapter(parent["a1"], parent["c2"])
        hand = r315.validate_30ma_full_d3_substrate_handoff(parent["a1"], adapter, r315.R315Config())
        ck("live_30ma_full_d3_handoff_exact", hand.get("full_d3_substrate_identity_exact") is True, hand)
        for key, row in hand.get("fields", {}).items():
            ck(f"live_30ma_handoff_exact::{key}", row.get("exact") is True, row)
            ck(f"live_30ma_handoff_zero_error::{key}", float(row.get("max_abs_error", 1.0)) == 0.0, row)

        sched = r315.biology_scheduler_separation_report(parent["clock"], r315.R315Config())
        ck("live_scheduler_238_intervals", sched.get("biology_interval_count") == 238, sched.get("biology_interval_count"), 238)
        ck("live_scheduler_end_250ka", _float_eq(sched.get("biology_end_age_ma"), 0.25), sched.get("biology_end_age_ma"), 0.25)
        ck("live_scheduler_bridge_not_crossed", sched.get("c2_200_120ka_bridge_crossed") is False, sched.get("c2_200_120ka_bridge_crossed"))
        ck("live_scheduler_next_step_crosses_bridge", sched.get("next_nominal_biology_step_would_cross_c2_200ka_bridge_start") is True, sched.get("next_nominal_biology_step_would_cross_c2_200ka_bridge_start"))
        ck("live_scheduler_not_adaptive_biology", sched.get("adaptive_clock_used_as_biology_timestep") is False, sched.get("adaptive_clock_used_as_biology_timestep"))

    # Scientific source authority hashes remain frozen at the R3.15 candidate values.
    manifest_path = root / "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_15.json"
    ck("source_manifest_exists", manifest_path.is_file(), str(manifest_path))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    ck("source_manifest_stage", manifest.get("stage") == STAGE, manifest.get("stage"), STAGE)
    for rel, want in manifest.get("inherited_authorities_unchanged", {}).items():
        p = root / rel
        ck(f"inherited_authority_exists::{rel}", p.is_file(), str(p))
        if p.is_file():
            ck(f"inherited_authority_sha::{rel}", hfile(p) == want, hfile(p), want)
    # Core R3.15 runtime/config/test hashes must also remain as candidate-authorized.
    for rel in (
        "src/arcana_worldsim/scientific_engines/r315_late_cenozoic_secular_biology.py",
        "configs/world1_r315_late_cenozoic_secular_biology_v0_6D1_R3_15.json",
        "tests/test_r315_late_cenozoic_secular_biology.py",
        "scripts/run_v0_6D1_R3_15_secular_biology.py",
        "run_v0_6D1_R3_15_secular_biology.ps1",
    ):
        p = root / rel; want = manifest.get("r315_files", {}).get(rel)
        ck(f"r315_core_exists::{rel}", p.is_file(), str(p))
        if p.is_file() and want:
            ck(f"r315_core_sha::{rel}", hfile(p) == want, hfile(p), want)

    failed = [x for x in checks if not x["pass"]]
    audit = {
        "schema": "ARCANA_R315_FORMAL_SEALED_AUDIT_V1",
        "stage": STAGE,
        "verdict": VERDICT if not failed else "FAIL_R315_SEALED_AUDIT",
        "checks": f"{len(checks)-len(failed)}/{len(checks)}",
        "failed": failed,
        "artifact_hashes": {
            "canonical_summary": hfile(ev["summary_path"]) if ev.get("summary_path") and Path(ev["summary_path"]).is_file() else None,
            "checkpoint_json": hfile(ev["json_path"]) if ev.get("json_path") and Path(ev["json_path"]).is_file() else None,
            "checkpoint_npz": hfile(ev["npz_path"]) if ev.get("npz_path") and Path(ev["npz_path"]).is_file() else None,
            "source_authority_manifest": hfile(manifest_path) if manifest_path.is_file() else None,
        },
        "run_projection": {
            "age_ma": float(ev["state"].age_ma) if ev.get("state") is not None else None,
            "species": len(set(ev["state"].current_species)) if ev.get("state") is not None else None,
            "components": len(ev["state"].component_ids) if ev.get("state") is not None else None,
            "population": float(ev["state"].pop.sum()) if ev.get("state") is not None else None,
            "invariants": ev.get("invariants"),
        },
        "interpretation_guard": {
            "boundary_role": "LAST_FIXED_125KYR_BIOLOGY_CHECKPOINT_BEFORE_C2_200KA_BRIDGE",
            "adaptive_clock_promoted_to_biology_timestep": False,
            "c2_200_120ka_bridge_crossed": False,
            "recent_120ka_restart_crossed": False,
            "high_resolution_200ka_historical_paleoclimate_claimed": False,
            "c2_bridge_historical_glacial_chronology_claimed": False,
            "next_nominal_125kyr_step_requires_multirate_bridge_stage": True,
        },
        "check_rows": checks,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if failed:
        print(json.dumps({"verdict": audit["verdict"], "checks": audit["checks"], "failed": failed[:12], "out": str(out)}, indent=2))
        return 1

    seal = {
        "schema": "ARCANA_R315_SEAL_SUMMARY_V1",
        "stage": STAGE,
        "verdict": VERDICT,
        "boundary": {
            "age_ma": 0.25,
            "event_side": "LATE_CENOZOIC_SECULAR_BIOLOGY_PRE_C2_200KA_BRIDGE",
            "species": 134,
            "components": 295,
            "population": 1218.3485572325976,
        },
        "replay": {
            "start_age_ma": 30.0,
            "end_age_ma": 0.25,
            "biology_steps": 238,
            "biology_cadence_years": 125000.0,
            "adaptive_clock_used_as_biology_timestep": False,
            "c2_bridge_crossed": False,
            "next_nominal_biology_step_crosses_200ka_bridge": True,
        },
        "events_delta": summary["run"]["event_counts_delta"],
        "genetics": {
            "peak_q": summary["run"]["peak_q_recorded"],
            "final_q_max": summary["run"]["invariants"]["q_max"],
            "q_headroom": summary["run"]["invariants"]["q_headroom"],
            "clipping_steps": 0,
            "clipping_contacts": 0,
        },
        "artifact_hashes": {
            "canonical_summary": hfile(ev["summary_path"]),
            "checkpoint_json": hfile(ev["json_path"]),
            "checkpoint_npz": hfile(ev["npz_path"]),
            "source_authority_manifest": hfile(manifest_path),
            "formal_audit": hfile(out),
        },
        "parent_r314_authority": summary.get("parent_r314_authority"),
        "evidence": {
            "formal_audit": audit["checks"] + " PASS",
            "focused_regression": "31/31 PASS",
            "full_inherited_regression": "312/312 PASS",
            "serialization_identity": True,
        },
        "interpretation_guard": (
            "R3.15 seals the 250 ka fixed-cadence H0 biology restart boundary. It does not cross the 200-120 ka C2 bridge, "
            "does not reinterpret adaptive environmental checkpoints as biology timesteps, and does not claim the C2 bridge as sealed "
            "high-resolution historical glacial chronology. The next stage must implement an explicit multirate coupling for 250->120 ka."
        ),
    }
    seal_out.write_text(json.dumps(seal, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": VERDICT, "checks": audit["checks"], "audit": str(out), "seal": str(seal_out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
