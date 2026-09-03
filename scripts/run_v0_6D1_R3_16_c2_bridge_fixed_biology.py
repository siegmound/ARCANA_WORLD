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
from arcana_worldsim.scientific_engines import r316_c2_bridge_fixed_biology as r316


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
    ap.add_argument("--out-dir", type=Path, default=ROOT / "local_runs/v0_6D1_R3_16")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    parent = r316.validate_parent_r315_authority(ROOT)
    parent_state = parent["state"]
    a1 = parent["a1"]
    if not hasattr(a1, "files"):
        raise TypeError("R3.16 canonical runtime requires A1 as an NpzFile preserving the sealed R3.8 .files contract")
    c2 = parent["c2"]
    clock = parent["clock"]
    public_parent = {k: v for k, v in parent.items() if k not in ("state", "a1", "c2", "clock")}
    md = metadata_rows()
    cfg = r316.R316Config()

    state, records, exposure, effective_env = r316.run_bridge_macrostep(parent_state, a1, md, c2, clock, cfg)
    adapter = r316.R316C2BridgeEnvironmentAdapter(a1, c2)
    refined_env = r316.one_level_refined_exposure_environment(adapter, clock)
    quadrature_refinement = r316.compare_effective_environments(effective_env, refined_env)

    # Endpoint-only is a diagnostic counterfactual, never the canonical branch.
    endpoint_env_shadow = adapter.state_at_age(r316.BIOLOGY_END_AGE_MA)
    shadow_parent = r316.r315.r313.r312.r311._clone_state(parent_state)
    with r316.patched_r38_effective_bridge_environment(endpoint_env_shadow):
        endpoint_shadow_state, _ = r38.advance_state(shadow_parent, a1, md, cfg, r316.BIOLOGY_END_AGE_MA)
    before = r316.event_counts(parent_state)
    after = r316.event_counts(state)
    delta = r316.delta_event_counts(parent_state, state)
    inv = r316.invariant_report(state, md, cfg)
    clip_steps = sum(1 for r in records if int(r.get("clipping_count", 0)) > 0)
    clip_contacts = sum(int(r.get("clipping_count", 0)) for r in records)
    peak_q = max((float(r.get("max_q", 0.0)) for r in records), default=float(inv["q_max"]))
    peak_unclipped = max((float(r.get("max_unclipped_q", 0.0)) for r in records), default=float(inv["q_max"]))
    new_events = state.events[len(parent_state.events):]

    endpoint125 = r316.R316C2BridgeEnvironmentAdapter(a1, c2).state_at_age(r316.BIOLOGY_END_AGE_MA)
    endpoint120 = r316.R316C2BridgeEnvironmentAdapter(a1, c2).state_at_age(r316.C2_BRIDGE_END_AGE_MA)

    report = {
        "start_age_ma": r316.START_AGE_MA,
        "end_age_ma": r316.BIOLOGY_END_AGE_MA,
        "ordinary_biology_steps": len(records),
        "biology_cadence_years": float(cfg.biology_cadence_years),
        "adaptive_clock_used_as_biology_timestep": False,
        "environmental_substeps_preserved_as_exposure_quadrature": True,
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
        "guild_species": r316.species_counts_by_guild(state),
        "speciation_chronology": chronology(new_events, "speciation"),
        "ordinary_extinction_chronology": chronology(new_events, "ordinary_background_extinction"),
        "fission_chronology": chronology(new_events, "deme_fission"),
        "coalescence_chronology": chronology(new_events, "deme_coalescence"),
        "exposure_coupling": exposure,
        "quadrature_refinement_diagnostic": quadrature_refinement,
        "endpoint_only_shadow": {
            "role": "NONAUTHORITATIVE_COUNTERFACTUAL_TO_MEASURE_INFORMATION_LOSS",
            "species": len(set(endpoint_shadow_state.current_species)),
            "components": len(endpoint_shadow_state.component_ids),
            "population": float(endpoint_shadow_state.pop.sum()),
            "population_difference_canonical_minus_shadow": float(state.pop.sum() - endpoint_shadow_state.pop.sum()),
            "trait_max_abs_difference": float(np.max(np.abs(state.trait-endpoint_shadow_state.trait))) if state.trait.shape == endpoint_shadow_state.trait.shape else float("inf"),
            "va_max_abs_difference": float(np.max(np.abs(state.va-endpoint_shadow_state.va))) if state.va.shape == endpoint_shadow_state.va.shape else float("inf"),
            "same_component_identity": state.component_ids == endpoint_shadow_state.component_ids,
            "same_species_identity": state.current_species == endpoint_shadow_state.current_species,
            "canonical_branch_selected": False
        },
        "effective_environment": {
            "forcing_semantics": effective_env.get("biology_forcing_sample_semantics"),
            "adaptive_clock_checkpoint_promoted_to_biology_step": effective_env.get("adaptive_clock_checkpoint_promoted_to_biology_step"),
            "environmental_substeps_preserved_as_exposure_quadrature": effective_env.get("environmental_substeps_preserved_as_exposure_quadrature"),
            "fractional_support_cells": int(np.count_nonzero((np.asarray(effective_env["land_support"]) > 1e-9) & (np.asarray(effective_env["land_support"]) < 1 - 1e-9))),
        },
        "endpoint_125ka": {
            "provider": endpoint125.get("provider"),
            "subprovider": endpoint125.get("subprovider"),
            "boundary_progress": endpoint125.get("boundary_progress"),
        },
        "endpoint_120ka_environment_only": {
            "provider": endpoint120.get("provider"),
            "subprovider": endpoint120.get("subprovider"),
            "authority": endpoint120.get("authority"),
            "boundary_progress": endpoint120.get("boundary_progress"),
            "biology_advanced_to_120ka": False,
        },
    }

    valid = (
        len(records) == r316.EXPECTED_BIOLOGY_STEPS
        and abs(float(state.age_ma) - r316.BIOLOGY_END_AGE_MA) <= 1e-12
        and exposure["c2_bridge_500y_substeps_consumed"] == r316.EXPECTED_C2_SUBSTEPS_CONSUMED
        and exposure["c2_bridge_500y_substeps_remaining_to_120ka"] == r316.EXPECTED_C2_SUBSTEPS_REMAINING
        and exposure["remainder_125_to_120ka"]["segment_count"] == r316.EXPECTED_C2_SUBSTEPS_REMAINING
        and exposure["remainder_125_to_120ka"]["biology_advanced"] is False
        and effective_env.get("adaptive_clock_checkpoint_promoted_to_biology_step") is False
        and effective_env.get("environmental_substeps_preserved_as_exposure_quadrature") is True
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
        and endpoint120.get("replay_safe_boundary_continuation") is True
    )

    checkpoint = r316.save_checkpoint(state, args.out_dir, public_parent, cfg, report)
    reloaded = r316.load_checkpoint(Path(checkpoint["json"]))
    serialization = r38.compare_runtime_states(state, reloaded)
    valid = bool(valid and serialization["equivalent"])

    verdict = r316.VERDICT if valid else "FAIL_R316_C2_BRIDGE_FIXED_BIOLOGY_COUPLING"
    summary = {
        "schema": r316.SUMMARY_SCHEMA,
        "stage": r316.STAGE,
        "mode": "CANONICAL_250_TO_125KA_ONE_FIXED_BIOLOGY_STEP_WITH_C2_EXPOSURE_QUADRATURE",
        "verdict": verdict,
        "wall_seconds": time.time() - t0,
        "parent_r315_authority": public_parent,
        "run": report,
        "checkpoint": checkpoint,
        "serialization_identity": serialization,
        "governance": {
            "r315_250ka_parent_sealed": True,
            "r314_c2_provider_bound": True,
            "adaptive_clock_is_environment_scheduler_not_biology_cadence": True,
            "adaptive_clock_checkpoint_promoted_to_biology_step": False,
            "environmental_substeps_preserved_as_exposure_quadrature": True,
            "biology_cadence_years": float(cfg.biology_cadence_years),
            "biology_cadence_changed": False,
            "gene_flow_step_cadence_changed": False,
            "lifecycle_gate_cadence_changed": False,
            "c2_bridge_start_crossed": True,
            "c2_bridge_120ka_restart_crossed_by_biology": False,
            "remaining_environmental_bridge_years": 5000.0,
            "high_resolution_200ka_historical_paleoclimate_claimed": False,
            "c2_bridge_historical_glacial_chronology_claimed": False,
            "deep_biological_coupling": False,
            "richness_target_used": False,
            "guild_target_used": False,
            "scientific_parameter_changes": False,
        },
    }
    sp = args.out_dir / "R3_16_C2_BRIDGE_FIXED_BIOLOGY_SUMMARY.json"
    sp.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps({
        "stage": r316.STAGE,
        "verdict": verdict,
        "wall_seconds": summary["wall_seconds"],
        "biology_steps": len(records),
        "biology_age_ma": float(state.age_ma),
        "species": report["final_species"],
        "components": report["final_components"],
        "population": report["final_total_population"],
        "event_counts_delta": delta,
        "peak_q": peak_q,
        "peak_unclipped_q": peak_unclipped,
        "clipping_steps": clip_steps,
        "c2_500y_substeps_consumed": exposure["c2_bridge_500y_substeps_consumed"],
        "c2_500y_substeps_remaining_to_120ka": exposure["c2_bridge_500y_substeps_remaining_to_120ka"],
        "adaptive_clock_as_biology_timestep": False,
        "biology_advanced_to_120ka": False,
    }, indent=2))
    print(json.dumps({
        "checkpoint": checkpoint,
        "serialization_identity": serialization["equivalent"],
        "summary": str(sp),
    }, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
