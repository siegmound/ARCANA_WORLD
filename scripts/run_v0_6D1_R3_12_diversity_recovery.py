from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r312_postcha1_diversity_recovery as r312


def _metadata_rows() -> list[dict]:
    d = json.loads((ROOT / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    return d["species"] if isinstance(d, dict) and "species" in d else d


def _event_chronology(events: list[dict], name: str) -> list[dict]:
    out = []
    for e in events:
        if e.get("event") == name:
            out.append({k: e.get(k) for k in (
                "age_ma", "elapsed_year", "species_id", "parent_species_id", "daughter_species_id",
                "parent_component_id", "daughter_component_id", "retained_component_id", "absorbed_component_ids",
            ) if k in e})
    return out


def _historical_guild_references() -> tuple[dict[str, int], dict[str, int]]:
    p = ROOT / "references/v0_6D1_R3_10/R3_10_CHA1_EVENT_BRIDGE_SUMMARY.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    pre = {str(k): int(v["initial_species"]) for k, v in d["guilds"].items()}
    post = {str(k): int(v["survivors"]) for k, v in d["guilds"].items()}
    return pre, post


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=ROOT / "local_runs/v0_6D1_R3_12")
    ap.add_argument("--smoke", action="store_true", help="Run only 61.0 -> 60.5 Ma (4 biology steps).")
    args = ap.parse_args()
    out = args.out_dir; out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    parent = r312.validate_parent_r311_authority(ROOT)
    parent_state = parent["state"]
    a1 = np.load(ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz", allow_pickle=False)
    rows = _metadata_rows()
    cfg = r312.R312Config()
    end_age = r312.SMOKE_END_AGE_MA if args.smoke else r312.END_AGE_MA

    state, records = r312.run_diversity_recovery(parent_state, a1, rows, cfg, end_age_ma=end_age)
    inv = r312.invariant_report(state, rows, cfg)
    before_counts = r312.event_counts(parent_state)
    after_counts = r312.event_counts(state)
    delta = r312.delta_event_counts(parent_state, state)
    clipping_steps = sum(1 for r in records if int(r.get("clipping_count", 0)) > 0)
    clipping_contacts = sum(int(r.get("clipping_count", 0)) for r in records)
    peak_record_q = max((float(r.get("max_q", 0.0)) for r in records), default=inv["q_max"])
    peak_unclipped_q = max((float(r.get("max_unclipped_q", 0.0)) for r in records), default=inv["q_max"])

    new_events = state.events[len(parent_state.events):]
    pre_guild, post_guild = _historical_guild_references()
    recovery = r312.diversity_recovery_report(parent_state, state, pre_guild, post_guild)
    speciation_origin = r312.classify_speciation_origin_from_r311_boundary(parent_state, new_events)

    run_report = {
        "start_age_ma": r312.START_AGE_MA,
        "end_age_ma": float(end_age),
        "ordinary_biology_steps": len(records),
        "parent_species": len(set(parent_state.current_species)),
        "parent_components": len(parent_state.component_ids),
        "parent_total_population": float(parent_state.pop.sum()),
        "final_species": len(set(state.current_species)),
        "final_components": len(state.component_ids),
        "final_total_population": float(state.pop.sum()),
        "event_counts_before": before_counts,
        "event_counts_after": after_counts,
        "event_counts_delta": delta,
        "peak_q_recorded": peak_record_q,
        "peak_unclipped_q_recorded": peak_unclipped_q,
        "clipping_steps": clipping_steps,
        "clipping_contacts": clipping_contacts,
        "invariants": inv,
        "diversity_recovery": recovery,
        "speciation_origin_diagnostic": speciation_origin,
        "speciation_chronology": _event_chronology(new_events, "speciation"),
        "ordinary_extinction_chronology": _event_chronology(new_events, "ordinary_background_extinction"),
        "fission_chronology": _event_chronology(new_events, "deme_fission"),
        "coalescence_chronology": _event_chronology(new_events, "deme_coalescence"),
        "first_speciation_age_ma": next((e.get("age_ma") for e in new_events if e.get("event") == "speciation"), None),
        "first_ordinary_extinction_age_ma": next((e.get("age_ma") for e in new_events if e.get("event") == "ordinary_background_extinction"), None),
    }

    expected_steps = r312.EXPECTED_SMOKE_STEPS if args.smoke else r312.EXPECTED_STEPS
    valid_common = bool(
        len(records) == expected_steps
        and abs(state.age_ma - end_age) <= 1e-12
        and len(set(parent_state.current_species)) == r312.PARENT_SPECIES
        and len(parent_state.component_ids) == r312.PARENT_COMPONENTS
        and delta["CHA1_species_extinction"] == 0
        and delta["CHA1_high_resolution_event_bridge_complete"] == 0
        and delta["post_CHA1_ordinary_lifecycle_thaw"] == 0
        and after_counts["CHA1_species_extinction"] == r312.DIRECT_CHA1_SPECIES_LOSS_REFERENCE
        and after_counts["CHA1_high_resolution_event_bridge_complete"] == 1
        and after_counts["post_CHA1_ordinary_lifecycle_thaw"] == 1
        and inv["population_min"] >= -1e-14
        and abs(inv["population_on_inaccessible_cells"]) <= 1e-12
        and inv["q_max"] <= cfg.variance_ceiling_normalized + 1e-12
        and inv["s_symmetry_max_abs"] <= 2e-12
        and inv["s_diagonal_max_abs"] <= 2e-12
        and inv["s_min"] >= -2e-12
        and clipping_steps == 0
        and clipping_contacts == 0
    )

    parent_public = {k: v for k, v in parent.items() if k != "state"}
    if args.smoke:
        checkpoint = r312.save_smoke_checkpoint(state, out, cfg)
        reloaded = r312.load_diversity_checkpoint(Path(checkpoint["json"]), smoke=True)
        serialization = r38.compare_runtime_states(state, reloaded)
        valid = bool(valid_common and serialization["equivalent"])
        verdict = "PASS_R312_DIVERSITY_RECOVERY_SMOKE__ORDINARY_CONTINUATION_VALID" if valid else "FAIL_R312_SMOKE"
    else:
        checkpoint = r312.save_diversity_checkpoint(state, out, parent_public, cfg, run_report)
        reloaded = r312.load_diversity_checkpoint(Path(checkpoint["json"]), smoke=False)
        serialization = r38.compare_runtime_states(state, reloaded)
        valid = bool(valid_common and serialization["equivalent"])
        verdict = (
            "PASS_CANONICAL_POST_CHA1_61_TO_46_H0_DIVERSITY_RECOVERY_OBSERVATION__46MA_CHECKPOINT_READY"
            if valid else "FAIL_R312_POST_CHA1_DIVERSITY_RECOVERY"
        )

    summary = {
        "schema": r312.SUMMARY_SCHEMA,
        "stage": r312.STAGE,
        "mode": "SMOKE_61P0_TO_60P5" if args.smoke else "CANONICAL_61P0_TO_46P0",
        "verdict": verdict,
        "wall_seconds": time.time() - t0,
        "parent_r311_authority": parent_public,
        "run": run_report,
        "checkpoint": checkpoint,
        "serialization_identity": serialization,
        "governance": {
            "cha1_already_applied": True,
            "cha1_reapplied": False,
            "lifecycle_thaw_reapplied": False,
            "deep_biological_coupling": False,
            "ordinary_lifecycle_continued": True,
            "ordinary_speciation_enabled": True,
            "ordinary_background_extinction_enabled": True,
            "persistent_vicariance_fission_enabled": True,
            "persistent_reconnection_coalescence_enabled": True,
            "post_cha1_radiation_multiplier_used": False,
            "richness_target_used": False,
            "positive_diversification_required_for_pass": False,
            "earth_analogue_target_used": False,
            "production_r37i_r38_runtime_used": True,
            "biology_cadence_years": cfg.biology_cadence_years,
            "speciation_check_interval_years": cfg.speciation_check_interval_years,
            "founder_minimum_persistence_years": cfg.founder_minimum_persistence_years,
            "vicariance_persistence_min_years": cfg.vicariance_persistence_min_years,
            "reconnection_persistence_min_years": cfg.reconnection_persistence_min_years,
            "mu_changed": False,
            "b_changed": False,
            "q_ceiling_changed": False,
            "K_center_reinterpreted_as_physical_constant": False,
        },
    }
    sp = out / ("R3_12_SMOKE_SUMMARY.json" if args.smoke else "R3_12_POST_CHA1_DIVERSITY_RECOVERY_SUMMARY.json")
    sp.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    compact = {
        "stage": summary["stage"], "mode": summary["mode"], "verdict": verdict,
        "wall_seconds": summary["wall_seconds"], "biology_steps": len(records), "age_ma": state.age_ma,
        "species": run_report["final_species"], "components": run_report["final_components"],
        "population": run_report["final_total_population"], "event_counts_delta": delta,
        "peak_q": peak_record_q, "peak_unclipped_q": peak_unclipped_q, "clipping_steps": clipping_steps,
        "fraction_of_direct_CHA1_species_loss_recovered": recovery["fraction_of_direct_CHA1_species_loss_recovered"],
        "fraction_of_pre_CHA1_species_richness_present": recovery["fraction_of_pre_CHA1_species_richness_present"],
    }
    print(json.dumps(compact, indent=2))
    print(json.dumps({"checkpoint": checkpoint, "serialization_identity": serialization["equivalent"], "summary": str(sp)}, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
