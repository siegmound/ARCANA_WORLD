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
from arcana_worldsim.scientific_engines import r315_late_cenozoic_secular_biology as r315


def metadata_rows() -> list[dict]:
    data = json.loads((ROOT / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    return data["species"] if isinstance(data, dict) and "species" in data else data


def chronology(events: list[dict], event_name: str) -> list[dict]:
    keys = (
        "age_ma", "elapsed_year", "species_id", "parent_species_id", "daughter_species_id",
        "parent_component_id", "daughter_component_id", "retained_component_id", "absorbed_component_ids",
    )
    return [{k: e.get(k) for k in keys if k in e} for e in events if e.get("event") == event_name]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=ROOT / "local_runs/v0_6D1_R3_15")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    parent = r315.validate_parent_r314_authority(ROOT)
    parent_state = parent["state"]
    c2 = parent["c2"]
    clock = parent["clock"]
    public_parent = {k: v for k, v in parent.items() if k not in ("state", "a1", "c2", "clock")}

    a1 = np.load(ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz", allow_pickle=False)
    md = metadata_rows()
    cfg = r315.R315Config()
    adapter = r315.R315D3EnvironmentAdapter(a1, c2)
    handoff = r315.validate_30ma_full_d3_substrate_handoff(a1, adapter, cfg)
    scheduler = r315.biology_scheduler_separation_report(clock, cfg)
    if not handoff["full_d3_substrate_identity_exact"]:
        raise RuntimeError("R3.15 full D3 substrate is not exactly continuous at 30 Ma")
    if not scheduler["all_r315_biology_checkpoints_older_than_c2_bridge_start"]:
        raise RuntimeError("R3.15 biology grid would enter the C2 bridge")

    end_age = r315.SMOKE_END_AGE_MA if args.smoke else r315.END_AGE_MA
    state, records = r315.run_secular_biology(parent_state, a1, md, c2, cfg, end_age)

    before = r315.event_counts(parent_state)
    after = r315.event_counts(state)
    delta = r315.delta_event_counts(parent_state, state)
    inv = r315.invariant_report(state, md, cfg)
    clip_steps = sum(1 for r in records if int(r.get("clipping_count", 0)) > 0)
    clip_contacts = sum(int(r.get("clipping_count", 0)) for r in records)
    peak_q = max((float(r.get("max_q", 0.0)) for r in records), default=float(inv["q_max"]))
    peak_unclipped = max((float(r.get("max_unclipped_q", 0.0)) for r in records), default=float(inv["q_max"]))
    new_events = state.events[len(parent_state.events):]
    final_adapter_state = adapter.state_at_age(float(end_age))

    report = {
        "start_age_ma": r315.START_AGE_MA,
        "end_age_ma": float(end_age),
        "ordinary_biology_steps": len(records),
        "biology_cadence_years": float(cfg.biology_cadence_years),
        "adaptive_clock_used_as_biology_timestep": False,
        "parent_species": len(set(parent_state.current_species)),
        "parent_components": len(parent_state.component_ids),
        "parent_total_population": float(parent_state.pop.sum()),
        "final_species": len(set(state.current_species)),
        "final_components": len(state.component_ids),
        "final_total_population": float(state.pop.sum()),
        "event_counts_before": before,
        "event_counts_after": after,
        "event_counts_delta": delta,
        "peak_q_recorded": peak_q,
        "peak_unclipped_q_recorded": peak_unclipped,
        "clipping_steps": clip_steps,
        "clipping_contacts": clip_contacts,
        "invariants": inv,
        "guild_species": r315.species_counts_by_guild(state),
        "speciation_chronology": chronology(new_events, "speciation"),
        "ordinary_extinction_chronology": chronology(new_events, "ordinary_background_extinction"),
        "fission_chronology": chronology(new_events, "deme_fission"),
        "coalescence_chronology": chronology(new_events, "deme_coalescence"),
        "full_d3_substrate_30ma_handoff": handoff,
        "scheduler_biology_separation": scheduler,
        "endpoint_provider": {
            "age_ma": float(end_age),
            "provider": final_adapter_state.get("provider"),
            "subprovider": final_adapter_state.get("subprovider"),
            "production_substrate_adapter": final_adapter_state.get("production_substrate_adapter"),
            "adaptive_clock_checkpoint_promoted_to_biology_step": final_adapter_state.get("adaptive_clock_checkpoint_promoted_to_biology_step"),
            "biology_forcing_sample_semantics": final_adapter_state.get("biology_forcing_sample_semantics"),
            "c2_bridge_supports_endpoint": bool(c2.bridge.supports_age(float(end_age))),
        },
    }

    expected_steps = r315.EXPECTED_SMOKE_STEPS if args.smoke else r315.EXPECTED_STEPS
    valid = (
        len(records) == expected_steps
        and abs(float(state.age_ma) - float(end_age)) <= 1e-12
        and delta["CHA1_species_extinction"] == 0
        and delta["CHA1_high_resolution_event_bridge_complete"] == 0
        and delta["post_CHA1_ordinary_lifecycle_thaw"] == 0
        and after["CHA1_species_extinction"] == 212
        and after["CHA1_high_resolution_event_bridge_complete"] == 1
        and after["post_CHA1_ordinary_lifecycle_thaw"] == 1
        and float(inv["population_min"]) >= -1e-14
        and abs(float(inv["population_on_inaccessible_cells"])) <= 1e-12
        and float(inv["q_max"]) <= float(cfg.variance_ceiling_normalized) + 1e-12
        and float(inv["s_symmetry_max_abs"]) <= 2e-12
        and float(inv["s_diagonal_max_abs"]) <= 2e-12
        and float(inv["s_min"]) >= -2e-12
        and clip_steps == 0
        and clip_contacts == 0
        and handoff["full_d3_substrate_identity_exact"] is True
        and scheduler["adaptive_clock_used_as_biology_timestep"] is False
        and scheduler["c2_200_120ka_bridge_crossed"] is False
        and scheduler["recent_120ka_restart_crossed"] is False
        and final_adapter_state.get("adaptive_clock_checkpoint_promoted_to_biology_step") is False
        and not c2.bridge.supports_age(float(end_age))
    )

    checkpoint = r315.save_checkpoint(state, args.out_dir, public_parent, cfg, report, smoke=args.smoke)
    reloaded = r315.load_checkpoint(Path(checkpoint["json"]), smoke=args.smoke)
    serialization = r38.compare_runtime_states(state, reloaded)
    valid = bool(valid and serialization["equivalent"])

    if args.smoke:
        verdict = (
            "PASS_R315_LATE_CENOZOIC_SECULAR_BIOLOGY_SMOKE__C2_SUBSTRATE_FIXED_125KYR_CADENCE_VALID"
            if valid else "FAIL_R315_SECULAR_BIOLOGY_SMOKE"
        )
        mode = "SMOKE_30P0_TO_29P5"
        summary_name = "R3_15_SECULAR_BIOLOGY_SMOKE_SUMMARY.json"
    else:
        verdict = (
            "PASS_CANONICAL_R315_30MA_TO_250KA_H0_LATE_CENOZOIC_SECULAR_BIOLOGY__PRE_C2_200KA_BRIDGE_CHECKPOINT_READY"
            if valid else "FAIL_R315_30MA_TO_250KA_SECULAR_BIOLOGY"
        )
        mode = "CANONICAL_30P0_TO_0P25"
        summary_name = "R3_15_LATE_CENOZOIC_SECULAR_BIOLOGY_SUMMARY.json"

    summary = {
        "schema": r315.SUMMARY_SCHEMA,
        "stage": r315.STAGE,
        "mode": mode,
        "verdict": verdict,
        "wall_seconds": time.time() - t0,
        "parent_r314_authority": public_parent,
        "run": report,
        "checkpoint": checkpoint,
        "serialization_identity": serialization,
        "governance": {
            "r314_c2_provider_bound": True,
            "adaptive_clock_is_scheduler_not_biology_cadence": True,
            "adaptive_clock_checkpoint_promoted_to_biology_step": False,
            "biology_cadence_years": float(cfg.biology_cadence_years),
            "biology_cadence_changed": False,
            "c2_200_120ka_bridge_crossed": False,
            "recent_120ka_restart_crossed": False,
            "high_resolution_200ka_historical_paleoclimate_claimed": False,
            "c2_bridge_historical_glacial_chronology_claimed": False,
            "deep_biological_coupling": False,
            "cha1_reapplied": False,
            "lifecycle_thaw_reapplied": False,
            "richness_target_used": False,
            "guild_target_used": False,
            "positive_diversification_required_for_pass": False,
            "cross_guild_transition_operator_activated": False,
            "production_r37i_r38_runtime_used": True,
            "scientific_parameter_changes": False,
        },
    }
    sp = args.out_dir / summary_name
    sp.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps({
        "stage": r315.STAGE,
        "mode": mode,
        "verdict": verdict,
        "wall_seconds": summary["wall_seconds"],
        "biology_steps": len(records),
        "age_ma": float(state.age_ma),
        "species": report["final_species"],
        "components": report["final_components"],
        "population": report["final_total_population"],
        "event_counts_delta": delta,
        "peak_q": peak_q,
        "peak_unclipped_q": peak_unclipped,
        "clipping_steps": clip_steps,
        "adaptive_clock_as_biology_timestep": False,
        "c2_bridge_crossed": False,
        "next_nominal_biology_step_crosses_200ka_bridge": scheduler["next_nominal_biology_step_would_cross_c2_200ka_bridge_start"],
    }, indent=2))
    print(json.dumps({
        "checkpoint": checkpoint,
        "serialization_identity": serialization["equivalent"],
        "summary": str(sp),
    }, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
