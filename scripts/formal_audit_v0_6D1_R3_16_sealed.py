from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

import numpy as np

STAGE = "v0.6D1-R3.16"
READY_VERDICT = "PASS_CANONICAL_R316_250_TO_125KA_H0_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY__125KA_PRE_120KA_RESTART_CHECKPOINT_READY"
SEALED_VERDICT = "PASS_R316_CANONICAL_250_TO_125KA_H0_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY__125KA_PRE_120KA_RESTART_BOUNDARY_SEALED"
CHECKPOINT_JSON_SHA256 = "aaf0bab510b4bcb5fbf77707ad66201515342cf8eb25b687e8f15952d2afca32"
CHECKPOINT_NPZ_SHA256 = "de0ef549d2fc74f1546e320b3fc3e0bc2f7ca7cbf5ebac464976494ad4055593"
EXPECTED_POP = 1217.8946033288662
EXPECTED_PEAK_Q = 0.047631033446597144


def hfile(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def f_eq(a: Any, b: Any, atol: float = 1e-12) -> bool:
    try:
        return abs(float(a) - float(b)) <= atol
    except Exception:
        return False


def metadata_rows(root: Path) -> list[dict[str, Any]]:
    d = json.loads((root / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    return d["species"] if isinstance(d, dict) and "species" in d else d


def nested_max_abs(a: Mapping[str, Any], b: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, float]:
    out: dict[str, float] = {}
    for k in keys:
        aa = np.asarray(a[k], dtype=float); bb = np.asarray(b[k], dtype=float)
        if aa.shape != bb.shape:
            out[k] = float("inf")
        else:
            out[k] = float(np.max(np.abs(aa - bb))) if aa.size else 0.0
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seal-out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve(); run_dir = args.run_dir.resolve(); out = args.out.resolve(); seal_out = args.seal_out.resolve()
    sys.path.insert(0, str(root / "src"))

    from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
    from arcana_worldsim.scientific_engines import r316_c2_bridge_fixed_biology as r316

    checks: list[dict[str, Any]] = []
    def ck(name: str, cond: bool, actual: Any = None, expected: Any = None):
        checks.append({"name": name, "pass": bool(cond), "actual": actual, "expected": expected})

    sp = run_dir / "R3_16_C2_BRIDGE_FIXED_BIOLOGY_SUMMARY.json"
    jp = run_dir / "WORLD1_H0_125ka_C2_EXPOSURE_PRESERVING_FIXED_BIOLOGY_PRE_120KA_RESTART_CHECKPOINT_v0_6D1_R3_16.json"
    npzp = jp.with_suffix(".npz")
    for p in (sp, jp, npzp): ck(f"file_exists::{p.name}", p.is_file(), str(p))
    if not all(p.is_file() for p in (sp, jp, npzp)):
        failed = [x for x in checks if not x["pass"]]
        audit = {"schema":"ARCANA_R316_FORMAL_SEALED_AUDIT_V1","stage":STAGE,"verdict":"FAIL_R316_SEALED_AUDIT","checks":f"{len(checks)-len(failed)}/{len(checks)}","failed":failed,"check_rows":checks}
        out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(audit, indent=2), encoding="utf-8")
        print(json.dumps({"verdict":audit["verdict"],"checks":audit["checks"],"audit":str(out)}, indent=2)); return 2

    summary = json.loads(sp.read_text(encoding="utf-8")); meta = json.loads(jp.read_text(encoding="utf-8"))
    rr = summary.get("run", {}); gov = summary.get("governance", {}); mg = meta.get("governance", {})
    cfg = r316.R316Config()

    # Canonical artifact identity from the user's completed run.
    ck("checkpoint_json_sha", hfile(jp) == CHECKPOINT_JSON_SHA256, hfile(jp), CHECKPOINT_JSON_SHA256)
    ck("checkpoint_npz_sha", hfile(npzp) == CHECKPOINT_NPZ_SHA256, hfile(npzp), CHECKPOINT_NPZ_SHA256)
    ck("summary_stage", summary.get("stage") == STAGE, summary.get("stage"), STAGE)
    ck("summary_schema", summary.get("schema") == r316.SUMMARY_SCHEMA, summary.get("schema"), r316.SUMMARY_SCHEMA)
    ck("summary_mode", summary.get("mode") == "CANONICAL_250_TO_125KA_ONE_FIXED_BIOLOGY_STEP_WITH_C2_EXPOSURE_QUADRATURE", summary.get("mode"))
    ck("summary_ready_verdict", summary.get("verdict") == READY_VERDICT, summary.get("verdict"), READY_VERDICT)
    ck("serialization_equivalent_stored", summary.get("serialization_identity", {}).get("equivalent") is True, summary.get("serialization_identity", {}).get("equivalent"))

    # Run projection.
    ck("run_start_250ka", f_eq(rr.get("start_age_ma"), 0.25), rr.get("start_age_ma"), 0.25)
    ck("run_end_125ka", f_eq(rr.get("end_age_ma"), 0.125), rr.get("end_age_ma"), 0.125)
    ck("one_biology_step", rr.get("ordinary_biology_steps") == 1, rr.get("ordinary_biology_steps"), 1)
    ck("biology_cadence_125k", f_eq(rr.get("biology_cadence_years"), 125000.0), rr.get("biology_cadence_years"), 125000.0)
    ck("parent_species_134", rr.get("parent_species") == 134, rr.get("parent_species"), 134)
    ck("parent_components_295", rr.get("parent_components") == 295, rr.get("parent_components"), 295)
    ck("final_species_134", rr.get("final_species") == 134, rr.get("final_species"), 134)
    ck("final_components_295", rr.get("final_components") == 295, rr.get("final_components"), 295)
    ck("final_population_exact", f_eq(rr.get("final_total_population"), EXPECTED_POP, 1e-9), rr.get("final_total_population"), EXPECTED_POP)
    ck("peak_q_exact_console", f_eq(rr.get("peak_q_recorded"), EXPECTED_PEAK_Q, 1e-15), rr.get("peak_q_recorded"), EXPECTED_PEAK_Q)
    ck("peak_unclipped_exact_console", f_eq(rr.get("peak_unclipped_q_recorded"), EXPECTED_PEAK_Q, 1e-15), rr.get("peak_unclipped_q_recorded"), EXPECTED_PEAK_Q)
    ck("no_clipping_steps", int(rr.get("clipping_steps", -1)) == 0, rr.get("clipping_steps"), 0)
    ck("no_clipping_contacts", int(rr.get("clipping_contacts", -1)) == 0, rr.get("clipping_contacts"), 0)
    expected_delta = {
        "paleogeographic_support_loss_remap":0,"deme_coalescence":0,"deme_fission":0,"speciation":0,
        "ordinary_background_extinction":0,"CHA1_species_extinction":0,"CHA1_high_resolution_event_bridge_complete":0,
        "post_CHA1_ordinary_lifecycle_thaw":0,
    }
    ck("event_delta_all_zero", rr.get("event_counts_delta") == expected_delta, rr.get("event_counts_delta"), expected_delta)
    for key in ("speciation_chronology","ordinary_extinction_chronology","fission_chronology","coalescence_chronology"):
        ck(f"no_new_events::{key}", rr.get(key) == [], rr.get(key), [])

    # Exposure semantics.
    ex = rr.get("exposure_coupling", {}); part = ex.get("partition", {}); rem = ex.get("remainder_125_to_120ka", {})
    ck("exposure_total_125k", f_eq(part.get("total_years"), 125000.0, 1e-6), part.get("total_years"), 125000.0)
    ck("c2_substeps_consumed_150", ex.get("c2_bridge_500y_substeps_consumed") == 150, ex.get("c2_bridge_500y_substeps_consumed"), 150)
    ck("c2_substeps_total_160", ex.get("c2_bridge_500y_substeps_total") == 160, ex.get("c2_bridge_500y_substeps_total"), 160)
    ck("c2_substeps_remaining_10", ex.get("c2_bridge_500y_substeps_remaining_to_120ka") == 10, ex.get("c2_bridge_500y_substeps_remaining_to_120ka"), 10)
    ck("remainder_segment_count_10", rem.get("segment_count") == 10, rem.get("segment_count"), 10)
    ck("remainder_total_5000y", f_eq(rem.get("total_years"), 5000.0, 1e-6), rem.get("total_years"), 5000.0)
    ck("remainder_biology_frozen", rem.get("biology_advanced") is False, rem.get("biology_advanced"))
    ck("adaptive_clock_not_biology_step", ex.get("adaptive_clock_as_biology_timestep") is False, ex.get("adaptive_clock_as_biology_timestep"))
    ck("biology_macrostep_125k", f_eq(ex.get("biology_macrostep_years"), 125000.0), ex.get("biology_macrostep_years"), 125000.0)
    e120 = ex.get("exact_120ka_environment_endpoint", {})
    ck("120ka_environment_replay_safe", e120.get("replay_safe_boundary_continuation") is True, e120.get("replay_safe_boundary_continuation"))
    ck("120ka_biology_not_advanced", e120.get("biology_advanced_to_120ka") is False, e120.get("biology_advanced_to_120ka"))

    eff = rr.get("effective_environment", {})
    ck("effective_forcing_semantics", eff.get("forcing_semantics") == "TIME_WEIGHTED_ENVIRONMENT_EXPOSURE_ON_ONE_FIXED_125KYR_BIOLOGY_MACROSTEP", eff.get("forcing_semantics"))
    ck("effective_not_promoted_checkpoint", eff.get("adaptive_clock_checkpoint_promoted_to_biology_step") is False, eff.get("adaptive_clock_checkpoint_promoted_to_biology_step"))
    ck("effective_substeps_preserved", eff.get("environmental_substeps_preserved_as_exposure_quadrature") is True, eff.get("environmental_substeps_preserved_as_exposure_quadrature"))

    qdiag = rr.get("quadrature_refinement_diagnostic", {})
    ck("quadrature_role_diagnostic_only", qdiag.get("role") == "DIAGNOSTIC_QUADRATURE_REFINEMENT_NOT_A_NEW_AUTHORITY", qdiag.get("role"))
    ck("quadrature_global_error_finite", math.isfinite(float(qdiag.get("global_max_abs_error", float("inf")))), qdiag.get("global_max_abs_error"))
    shadow = rr.get("endpoint_only_shadow", {})
    ck("shadow_role_non_authoritative", shadow.get("role") == "NONAUTHORITATIVE_COUNTERFACTUAL_TO_MEASURE_INFORMATION_LOSS", shadow.get("role"))
    ck("shadow_not_selected", shadow.get("canonical_branch_selected") is False, shadow.get("canonical_branch_selected"))

    # Governance in both summary and checkpoint metadata.
    summary_true = ("r315_250ka_parent_sealed","r314_c2_provider_bound","adaptive_clock_is_environment_scheduler_not_biology_cadence","environmental_substeps_preserved_as_exposure_quadrature","c2_bridge_start_crossed")
    for key in summary_true: ck(f"summary_governance_true::{key}", gov.get(key) is True, gov.get(key))
    summary_false = ("adaptive_clock_checkpoint_promoted_to_biology_step","biology_cadence_changed","gene_flow_step_cadence_changed","lifecycle_gate_cadence_changed","c2_bridge_120ka_restart_crossed_by_biology","high_resolution_200ka_historical_paleoclimate_claimed","c2_bridge_historical_glacial_chronology_claimed","deep_biological_coupling","richness_target_used","guild_target_used","scientific_parameter_changes")
    for key in summary_false: ck(f"summary_governance_false::{key}", gov.get(key) is False, gov.get(key))
    ck("summary_remaining_5000y", f_eq(gov.get("remaining_environmental_bridge_years"),5000.0), gov.get("remaining_environmental_bridge_years"),5000.0)
    ck("summary_cadence_125k", f_eq(gov.get("biology_cadence_years"),125000.0), gov.get("biology_cadence_years"),125000.0)
    meta_false = ("adaptive_clock_used_as_biology_timestep","gene_flow_step_cadence_changed","lifecycle_gate_cadence_changed","biology_advanced_to_120ka","deep_biological_coupling","scientific_parameters_changed")
    for key in meta_false: ck(f"checkpoint_governance_false::{key}", mg.get(key) is False, mg.get(key))
    ck("checkpoint_governance_biology_steps_1", mg.get("biology_steps") == 1, mg.get("biology_steps"),1)
    ck("checkpoint_governance_substeps_150", mg.get("c2_500y_substeps_consumed") == 150, mg.get("c2_500y_substeps_consumed"),150)
    ck("checkpoint_governance_remaining_10", mg.get("c2_500y_substeps_remaining_to_120ka") == 10, mg.get("c2_500y_substeps_remaining_to_120ka"),10)
    ck("checkpoint_governance_exposure_preserved", mg.get("environmental_substeps_preserved_as_exposure_quadrature") is True, mg.get("environmental_substeps_preserved_as_exposure_quadrature"))

    # Load the restart state and independently re-evaluate invariant closure.
    st = r316.load_checkpoint(jp)
    md = metadata_rows(root)
    inv = r316.invariant_report(st, md, cfg)
    ck("checkpoint_age_125ka", f_eq(st.age_ma,0.125), st.age_ma,0.125)
    ck("checkpoint_species_134", len(set(st.current_species)) == 134, len(set(st.current_species)),134)
    ck("checkpoint_components_295", len(st.component_ids) == 295, len(st.component_ids),295)
    ck("checkpoint_population_exact", f_eq(float(st.pop.sum()),EXPECTED_POP,1e-9), float(st.pop.sum()),EXPECTED_POP)
    ck("population_min_nonnegative", float(inv["population_min"]) >= -1e-14, inv["population_min"])
    ck("population_inaccessible_zero", abs(float(inv["population_on_inaccessible_cells"])) <= 1e-12, inv["population_on_inaccessible_cells"])
    ck("q_below_ceiling", float(inv["q_max"]) <= float(cfg.variance_ceiling_normalized)+1e-12, inv["q_max"], cfg.variance_ceiling_normalized)
    ck("S_symmetric", float(inv["s_symmetry_max_abs"]) <= 2e-12, inv["s_symmetry_max_abs"])
    ck("S_diagonal_zero", float(inv["s_diagonal_max_abs"]) <= 2e-12, inv["s_diagonal_max_abs"])
    ck("S_nonnegative", float(inv["s_min"]) >= -2e-12, inv["s_min"])
    for arr_name, arr in (
        ("population",st.pop),("trait",st.trait),("va",st.va),("generation_time",st.gen),
        ("reduced_va_within",st.reduced_state.va_within),("reduced_ancestry_covariance",st.reduced_state.ancestry_covariance),
        ("reduced_neutral_segregation_potential",st.reduced_state.neutral_segregation_potential),("reduced_adaptive_coordinate",st.reduced_state.adaptive_coordinate),
    ):
        ck(f"finite::{arr_name}", bool(np.isfinite(np.asarray(arr,dtype=float)).all()))

    # Independent serialization cycle from the completed canonical state.
    parent_public = summary.get("parent_r315_authority", {})
    with tempfile.TemporaryDirectory(prefix="arcana_r316_seal_") as td:
        saved = r316.save_checkpoint(st, Path(td), parent_public, cfg, rr)
        reload = r316.load_checkpoint(Path(saved["json"]))
        cmp = r38.compare_runtime_states(st, reload)
        ck("independent_roundtrip_equivalent", cmp.get("equivalent") is True, cmp.get("equivalent"))
        for group in ("arrays","reduced_state"):
            for key,row in cmp.get(group,{}).items(): ck(f"roundtrip_same::{group}::{key}", row.get("same") is True, row)
        for key,val in cmp.get("exact_fields",{}).items(): ck(f"roundtrip_exact::{key}", val is True, val)
        for key,val in cmp.get("scalar_abs_errors",{}).items(): ck(f"roundtrip_scalar_zero::{key}", float(val) == 0.0, val)

    # Validate the full live parent authority and independently replay the one macro-step.
    parent = None; a1 = None
    try:
        parent = r316.validate_parent_r315_authority(root); a1 = parent["a1"]
        ck("live_parent_r315_and_r314_authority_valid", True)
    except Exception as exc:
        ck("live_parent_r315_and_r314_authority_valid", False, repr(exc))

    replay_cmp = None; live_exposure = None; live_refinement = None
    if parent is not None:
        stored_parent = summary.get("parent_r315_authority", {})
        for key in ("r315_seal_sha256","r315_audit_sha256","r315_summary_sha256","checkpoint_json_sha256","checkpoint_npz_sha256","r314_seal_sha256","r314_clock_sha256"):
            ck(f"parent_authority_exact::{key}", parent.get(key) == stored_parent.get(key), parent.get(key), stored_parent.get(key))
        try:
            replay_state, replay_records, live_exposure, live_effective = r316.run_bridge_macrostep(parent["state"], a1, md, parent["c2"], parent["clock"], cfg)
            replay_cmp = r38.compare_runtime_states(st, replay_state)
            ck("independent_macrostep_replay_equivalent", replay_cmp.get("equivalent") is True, replay_cmp.get("equivalent"))
            ck("independent_macrostep_one_record", len(replay_records) == 1, len(replay_records),1)
            ck("independent_macrostep_age_125ka", f_eq(replay_state.age_ma,0.125), replay_state.age_ma,0.125)
            ck("independent_macrostep_substeps_150", live_exposure.get("c2_bridge_500y_substeps_consumed") == 150, live_exposure.get("c2_bridge_500y_substeps_consumed"),150)
            ck("independent_macrostep_remaining_10", live_exposure.get("c2_bridge_500y_substeps_remaining_to_120ka") == 10, live_exposure.get("c2_bridge_500y_substeps_remaining_to_120ka"),10)
            ck("independent_macrostep_remainder_frozen", live_exposure.get("remainder_125_to_120ka",{}).get("biology_advanced") is False, live_exposure.get("remainder_125_to_120ka",{}).get("biology_advanced"))
            ck("independent_macrostep_120ka_replay_safe", live_exposure.get("exact_120ka_environment_endpoint",{}).get("replay_safe_boundary_continuation") is True, live_exposure.get("exact_120ka_environment_endpoint",{}))
            # Recompute quadrature refinement from live C2; it must be finite and diagnostic-only.
            adapter = r316.R316C2BridgeEnvironmentAdapter(a1, parent["c2"])
            refined = r316.one_level_refined_exposure_environment(adapter, parent["clock"])
            live_refinement = r316.compare_effective_environments(live_effective, refined)
            ck("live_quadrature_refinement_finite", math.isfinite(float(live_refinement["global_max_abs_error"])), live_refinement["global_max_abs_error"])
            # Stored and live partition topology must agree exactly.
            ck("live_partition_segment_count_exact", live_exposure["partition"]["segment_count"] == part.get("segment_count"), live_exposure["partition"]["segment_count"], part.get("segment_count"))
            ck("live_partition_c2_count_exact", live_exposure["partition"]["c2_bridge_segment_count"] == part.get("c2_bridge_segment_count"), live_exposure["partition"]["c2_bridge_segment_count"], part.get("c2_bridge_segment_count"))
            ck("live_partition_nodes_exact", np.array_equal(np.asarray(live_exposure["partition"]["nodes_age_ma"],float), np.asarray(part.get("nodes_age_ma",[]),float)))
        except Exception as exc:
            ck("independent_macrostep_replay_completed", False, repr(exc))
        finally:
            try:
                if a1 is not None and hasattr(a1,"close"): a1.close()
            except Exception:
                pass

    # Source authority/repair governance: no silent code drift after the successful canonical run.
    manifest_path = root / "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_16.json"
    ck("source_manifest_exists", manifest_path.is_file(), str(manifest_path))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    ck("source_manifest_stage", manifest.get("stage") == STAGE, manifest.get("stage"),STAGE)
    ck("source_manifest_no_science_change", manifest.get("scientific_parameter_changes") is False, manifest.get("scientific_parameter_changes"))
    ck("source_manifest_no_biology_cadence_change", manifest.get("biology_cadence_changes") is False, manifest.get("biology_cadence_changes"))
    for repair in ("R1_WINDOWS_BASETEMP","R2_BRIDGE_ADAPTER_SCOPE","R3_RUNTIME_A1_NPZFILE"):
        ck(f"repair_declared::{repair}", repair in manifest.get("r316_repairs",{}), manifest.get("r316_repairs",{}))
    for rel,want in manifest.get("inherited_authorities_unchanged",{}).items():
        p=root/rel; ck(f"authority_exists::{rel}",p.is_file(),str(p));
        if p.is_file(): ck(f"authority_sha::{rel}",hfile(p)==want,hfile(p),want)
    for rel,want in manifest.get("r316_files",{}).items():
        p=root/rel; ck(f"r316_file_exists::{rel}",p.is_file(),str(p));
        if p.is_file(): ck(f"r316_file_sha::{rel}",hfile(p)==want,hfile(p),want)

    failed = [x for x in checks if not x["pass"]]
    audit = {
        "schema":"ARCANA_R316_FORMAL_SEALED_AUDIT_V1",
        "stage":STAGE,
        "verdict":SEALED_VERDICT if not failed else "FAIL_R316_SEALED_AUDIT",
        "checks":f"{len(checks)-len(failed)}/{len(checks)}",
        "failed":failed,
        "artifact_hashes":{
            "canonical_summary":hfile(sp),"checkpoint_json":hfile(jp),"checkpoint_npz":hfile(npzp),
            "source_authority_manifest":hfile(manifest_path) if manifest_path.is_file() else None,
        },
        "boundary":{
            "age_ma":float(st.age_ma),"species":len(set(st.current_species)),"components":len(st.component_ids),"population":float(st.pop.sum()),
            "q_max":float(inv["q_max"]),"q_headroom":float(cfg.variance_ceiling_normalized-float(inv["q_max"])),
        },
        "multirate_closure":{
            "biology_steps":1,"biology_cadence_years":125000.0,"c2_500y_substeps_consumed":150,
            "c2_500y_substeps_remaining_to_120ka":10,"remaining_environmental_bridge_years":5000.0,
            "adaptive_clock_as_biology_timestep":False,"biology_advanced_to_120ka":False,
        },
        "independent_replay":{
            "state_equivalent": bool(replay_cmp and replay_cmp.get("equivalent") is True),
            "quadrature_refinement_global_max_abs_error": None if live_refinement is None else float(live_refinement["global_max_abs_error"]),
        },
        "interpretation_guard":{
            "exact_120ka_biology_claimed":False,"c2_historical_glacial_chronology_claimed":False,
            "high_resolution_200ka_historical_paleoclimate_claimed":False,"endpoint_only_shadow_is_authority":False,
            "deep_biological_coupling":False,
        },
        "repairs_sealed_as_non_scientific":["R1_WINDOWS_BASETEMP","R2_BRIDGE_ADAPTER_SCOPE","R3_RUNTIME_A1_NPZFILE"],
        "check_rows":checks,
    }
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(audit,indent=2),encoding="utf-8")

    seal = {
        "schema":"ARCANA_R316_SEAL_SUMMARY_V1","stage":STAGE,"verdict":audit["verdict"],"checks":audit["checks"],
        "parent_stage":"v0.6D1-R3.15_SEALED",
        "boundary":audit["boundary"],"multirate_closure":audit["multirate_closure"],"interpretation_guard":audit["interpretation_guard"],
        "artifact_hashes":audit["artifact_hashes"],"formal_audit_sha256":hfile(out),
        "next_stage":"v0.6D1-R3.17 — 125->120 ka Exact Recent-Restart Biological Synchronization",
    }
    seal_out.write_text(json.dumps(seal,indent=2),encoding="utf-8")
    print(json.dumps({"verdict":audit["verdict"],"checks":audit["checks"],"audit":str(out),"seal":str(seal_out)},indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
