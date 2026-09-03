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
from arcana_worldsim.scientific_engines import r311_postcha1_recovery as r311


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



def _classify_speciation_origin(parent_state, new_events: list[dict]) -> dict:
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
            "classification": "MATCHED_PRE_CHA1_FOUNDER_CARRYOVER" if matched else "NOT_MATCHED_TO_INITIAL_PRE_CHA1_FOUNDER_STATE",
            "causal_note": (
                "Founder structural candidate existed before CHA-1; frozen 500 kyr was not credited to persistence."
                if matched else
                "Not an initial founder-state carryover. This is compatible with post-CHA1 initiation but is not by itself proof of empty-niche causation."
            ),
        })
    return {
        "initial_pre_cha1_founder_candidates": len(parent_state.founder_state),
        "matched_pre_cha1_carryover_speciations": sum(r["classification"] == "MATCHED_PRE_CHA1_FOUNDER_CARRYOVER" for r in rows),
        "not_matched_to_initial_pre_cha1_founder_state": sum(r["classification"] != "MATCHED_PRE_CHA1_FOUNDER_CARRYOVER" for r in rows),
        "rows": rows,
        "interpretation_guard": "NOT_MATCHED is not equivalent to proven CHA1-caused adaptive radiation; causality requires later H0/HX or counterfactual analysis.",
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=ROOT / "local_runs/v0_6D1_R3_11")
    ap.add_argument("--smoke", action="store_true", help="Run only 65.5 -> 65.0 Ma (4 biology steps).")
    args = ap.parse_args()
    out = args.out_dir; out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    parent = r311.validate_parent_r310_authority(ROOT)
    parent_state = parent["state"]
    a1 = np.load(ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz", allow_pickle=False)
    rows = _metadata_rows()
    cfg = r311.R311Config()
    end_age = r311.SMOKE_END_AGE_MA if args.smoke else r311.END_AGE_MA

    state, records, thaw = r311.run_recovery(parent_state, a1, rows, cfg, end_age_ma=end_age)
    inv = r311.invariant_report(state, rows, cfg)
    before_counts = r311.event_counts(parent_state)
    after_counts = r311.event_counts(state)
    delta = r311.delta_event_counts(parent_state, state)
    clipping_steps = sum(1 for r in records if int(r.get("clipping_count", 0)) > 0)
    clipping_contacts = sum(int(r.get("clipping_count", 0)) for r in records)
    peak_record_q = max((float(r.get("max_q", 0.0)) for r in records), default=inv["q_max"])
    peak_unclipped_q = max((float(r.get("max_unclipped_q", 0.0)) for r in records), default=inv["q_max"])

    new_events = state.events[len(parent_state.events):]
    speciation_origin = _classify_speciation_origin(parent_state, new_events)

    run_report = {
        "start_age_ma": r311.START_AGE_MA,
        "end_age_ma": float(end_age),
        "ordinary_biology_steps": len(records),
        "parent_species": len(set(parent_state.current_species)),
        "parent_components": len(parent_state.component_ids),
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
        "first_speciation_age_ma": next((e.get("age_ma") for e in state.events[len(parent_state.events):] if e.get("event") == "speciation"), None),
        "first_ordinary_extinction_age_ma": next((e.get("age_ma") for e in state.events[len(parent_state.events):] if e.get("event") == "ordinary_background_extinction"), None),
        "speciation_chronology": _event_chronology(new_events, "speciation"),
        "speciation_origin_diagnostic": speciation_origin,
        "ordinary_extinction_chronology": _event_chronology(new_events, "ordinary_background_extinction"),
        "fission_chronology": _event_chronology(new_events, "deme_fission"),
        "coalescence_chronology": _event_chronology(new_events, "deme_coalescence"),
    }

    expected_steps = r311.EXPECTED_SMOKE_STEPS if args.smoke else r311.EXPECTED_STEPS
    valid_common = bool(
        len(records) == expected_steps
        and abs(state.age_ma - end_age) <= 1e-12
        and len(set(parent_state.current_species)) == r311.PARENT_SPECIES
        and len(parent_state.component_ids) == r311.PARENT_COMPONENTS
        and delta["CHA1_species_extinction"] == 0
        and delta["CHA1_high_resolution_event_bridge_complete"] == 0
        and delta["post_CHA1_ordinary_lifecycle_thaw"] == 1
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
    checkpoint = None
    serialization = None
    if args.smoke:
        checkpoint = r311.save_smoke_checkpoint(state, out, cfg, thaw)
        reloaded = r311.load_recovery_checkpoint(Path(checkpoint["json"]), smoke=True)
        serialization = r38.compare_runtime_states(state, reloaded)
        valid = bool(valid_common and serialization["equivalent"])
        verdict = "PASS_R311_POST_CHA1_RECOVERY_SMOKE__ORDINARY_LIFECYCLE_RESTART_VALID" if valid else "FAIL_R311_SMOKE"
    else:
        checkpoint = r311.save_recovery_checkpoint(state, out, parent_public, cfg, thaw, run_report)
        reloaded = r311.load_recovery_checkpoint(Path(checkpoint["json"]), smoke=False)
        serialization = r38.compare_runtime_states(state, reloaded)
        valid = bool(valid_common and serialization["equivalent"])
        verdict = (
            "PASS_CANONICAL_POST_CHA1_65P5_TO_61_H0_RECOVERY__ORDINARY_ADAPTIVE_RADIATION_RESTART__61MA_CHECKPOINT_READY"
            if valid else "FAIL_R311_POST_CHA1_RECOVERY"
        )

    summary = {
        "schema": r311.SUMMARY_SCHEMA,
        "stage": r311.STAGE,
        "mode": "SMOKE_65P5_TO_65P0" if args.smoke else "CANONICAL_65P5_TO_61P0",
        "verdict": verdict,
        "wall_seconds": time.time() - t0,
        "parent_r310_authority": parent_public,
        "lifecycle_thaw": thaw,
        "run": run_report,
        "checkpoint": checkpoint,
        "serialization_identity": serialization,
        "governance": {
            "cha1_already_applied": True,
            "cha1_reapplied": False,
            "deep_biological_coupling": False,
            "ordinary_lifecycle_reenabled": True,
            "ordinary_speciation_enabled": True,
            "ordinary_background_extinction_enabled": True,
            "persistent_vicariance_fission_enabled": True,
            "persistent_reconnection_coalescence_enabled": True,
            "post_cha1_radiation_multiplier_used": False,
            "old_d31_50kyr_solver_used": False,
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
    sp = out / ("R3_11_SMOKE_SUMMARY.json" if args.smoke else "R3_11_POST_CHA1_RECOVERY_SUMMARY.json")
    sp.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    compact = {
        "stage": summary["stage"], "mode": summary["mode"], "verdict": verdict,
        "wall_seconds": summary["wall_seconds"], "biology_steps": len(records),
        "age_ma": state.age_ma, "species": run_report["final_species"], "components": run_report["final_components"],
        "population": run_report["final_total_population"], "event_counts_delta": delta,
        "peak_q": peak_record_q, "peak_unclipped_q": peak_unclipped_q,
        "clipping_steps": clipping_steps,
    }
    print(json.dumps(compact, indent=2))
    print(json.dumps({"checkpoint": checkpoint, "serialization_identity": serialization["equivalent"], "summary": str(sp)}, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
