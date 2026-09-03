from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.scientific_engines import r38_restartable_checkpoint as r38
from arcana_worldsim.scientific_engines import r310_cha1_highres_bridge as r310
from arcana_worldsim.scientific_engines.r39_precha1_continuation import R39Config


def _rows_from_metadata(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    return d["species"] if isinstance(d, dict) and "species" in d else d


def _write_timeseries(path: Path, schedule: np.ndarray, hazard_rows: list[dict]) -> None:
    forcing = r310.physical_forcing(schedule)
    post_mask = schedule >= 0.0
    post_times = schedule[post_mask]
    food = r310.foodweb_states(post_times)
    food_full = np.ones((len(schedule), 4), dtype=float)
    food_full[post_mask] = food
    ext = sorted(float(r["extinction_time_year"]) for r in hazard_rows if r["extinction_time_year"] is not None)
    initial_species = len(hazard_rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "index", "relative_year", "absolute_age_ma", "PAR_fraction", "temperature_anomaly_c",
            "NPP_multiplier", "extinction_pressure_index", "atmospheric_CO2_ppm",
            "plant_state", "herbivore_state", "mesopredator_state", "apex_state", "alive_species",
        ])
        for i, t in enumerate(schedule):
            extinct_by_t = 0 if t < 0 else int(np.searchsorted(ext, float(t), side="right"))
            w.writerow([
                i, float(t), 66.0 - float(t) / 1e6,
                float(forcing["par_fraction"][i]), float(forcing["temperature_anomaly_c"][i]),
                float(forcing["npp_multiplier"][i]), float(forcing["extinction_pressure_index"][i]),
                float(forcing["atmospheric_co2_ppm"][i]),
                float(food_full[i, 0]), float(food_full[i, 1]), float(food_full[i, 2]), float(food_full[i, 3]),
                initial_species - extinct_by_t,
            ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=ROOT / "local_runs" / "v0_6D1_R3_10")
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    parent = r310.validate_parent_r39_authority(ROOT)
    a1 = np.load(ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz", allow_pickle=False)
    metadata_rows = _rows_from_metadata(ROOT / "references/v0_6D1_R3/D1_SPECIES_METADATA.json")
    cfg = r310.R310Config()

    state, event_report = r310.run_event_bridge(parent["state"], a1, metadata_rows, cfg)
    checkpoint = r310.save_postcha1_checkpoint(state, out, {
        k: v for k, v in parent.items() if k != "state"
    }, cfg, event_report)
    reloaded = r310.load_postcha1_checkpoint(Path(checkpoint["json"]))
    serialization = r38.compare_runtime_states(state, reloaded)

    # Determinism witness: hazard construction repeated independently.
    h2 = r310.build_species_hazard_table(parent["state"], a1, metadata_rows, cfg)
    hazard_identity = r310.deterministic_hazard_identity(event_report["hazard_table"], h2)

    anchor_audit = r310.physical_anchor_audit()
    q = r38._normalized_q(
        state.reduced_state.va_within,
        state.root_species,
        {r["species_id"]: r for r in metadata_rows},
        R39Config().body_mass_scale,
    )
    pre_species = int(event_report["preimpact_species"])
    survivors = int(event_report["postimpact_survivor_species"])
    extinct = int(event_report["direct_cha1_extinctions"])

    valid = bool(
        pre_species == 305
        and survivors + extinct == pre_species
        and abs(state.age_ma - r310.POST_EVENT_AGE_MA) <= 1e-12
        and event_report["reporting_checkpoints"] == r310.REPORTING_CHECKPOINTS
        and event_report["extinction_time"]["all_within_20_year_acute_window"]
        and serialization["equivalent"]
        and hazard_identity
        and anchor_audit["impact_exact"]
        and max(anchor_audit["max_relative_error_by_field"].values(), default=0.0) <= 2e-12
        and event_report["ordinary_speciation_events_during_bridge"] == 0
        and event_report["adaptive_radiation_events_during_bridge"] == 0
        and event_report["deep_biological_coupling"] is False
        and event_report["impact_distance_mortality_enabled"] is False
        and float(np.min(state.pop)) >= -1e-14
        and float(np.max(q)) <= 0.08 + 1e-12
    )

    diagnostics_path = out / "R3_10_CHA1_SPECIES_DIAGNOSTICS.json"
    diagnostics_path.write_text(json.dumps(event_report["hazard_table"], indent=2), encoding="utf-8")
    extinction_path = out / "R3_10_CHA1_EXTINCTION_EVENTS.json"
    extinction_path.write_text(json.dumps([
        e for e in state.events if e.get("event") == "CHA1_species_extinction"
    ], indent=2), encoding="utf-8")
    timeseries_path = out / "R3_10_CHA1_PHYSICAL_FOODWEB_TIMESERIES.csv"
    _write_timeseries(timeseries_path, r310.reporting_schedule(), event_report["hazard_table"])
    anchor_path = out / "R3_10_CHA1_PHYSICAL_ANCHOR_AUDIT.json"
    anchor_path.write_text(json.dumps(anchor_audit, indent=2), encoding="utf-8")

    summary = {
        "schema": r310.SUMMARY_SCHEMA,
        "stage": r310.STAGE,
        "verdict": (
            "PASS_REBASED_CHA1_HIGH_RES_EVENT_BRIDGE__65P5MA_POST_CHA1_RESTART_READY__"
            "HISTORICAL_D22_SOURCE_NOT_CLAIMED_BIT_IDENTICAL"
            if valid else "FAIL_R310_CHA1_EVENT_BRIDGE"
        ),
        "wall_seconds": time.time() - t0,
        "parent_r39_authority": {k: v for k, v in parent.items() if k != "state"},
        "age_ma": state.age_ma,
        "event_side": "POST_CHA1_500KY",
        "reporting_checkpoints": event_report["reporting_checkpoints"],
        "preimpact_species": pre_species,
        "direct_cha1_extinctions": extinct,
        "postimpact_survivor_species": survivors,
        "extinction_fraction": event_report["extinction_fraction"],
        "extinction_time": event_report["extinction_time"],
        "guilds": event_report["guilds"],
        "preimpact_total_population": event_report["preimpact_total_population"],
        "postevent_total_population": event_report["postevent_total_population"],
        "population_recovery": event_report["population_recovery"],
        "foodweb_minimum": event_report["foodweb_minimum"],
        "foodweb_endpoint": event_report["foodweb_endpoint"],
        "physical_endpoint": event_report["physical_endpoint"],
        "q_max_postevent": float(np.max(q)) if q.size else 0.0,
        "q_ceiling": 0.08,
        "q_headroom_postevent": 0.08 - (float(np.max(q)) if q.size else 0.0),
        "component_count_postevent": len(state.component_ids),
        "serialization_identity": serialization,
        "hazard_repeat_identity": hazard_identity,
        "physical_anchor_audit": anchor_audit,
        "checkpoint": checkpoint,
        "artifacts": {
            "species_diagnostics": str(diagnostics_path),
            "extinction_events": str(extinction_path),
            "physical_foodweb_timeseries": str(timeseries_path),
            "physical_anchor_audit": str(anchor_path),
        },
        "governance": {
            "cha1_applied": True,
            "deep_biological_coupling": False,
            "ordinary_125kyr_crossing_used": False,
            "historical_D22_survivor_ids_used_as_lookup": False,
            "historical_D22_solver_bit_identity_claimed": False,
            "rebased_event_provider_authorized_for_candidate": valid,
            "ordinary_speciation_inside_event": False,
            "adaptive_radiation_inside_event": False,
            "mu_changed": False,
            "b_changed": False,
            "q_ceiling_changed": False,
            "scalar_K_eff_physical_constant_authorized": False,
            "next_restart_boundary_age_ma": 65.5,
        },
    }
    summary_path = out / "R3_10_CHA1_EVENT_BRIDGE_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    compact = {
        "stage": summary["stage"],
        "verdict": summary["verdict"],
        "wall_seconds": summary["wall_seconds"],
        "age_ma": summary["age_ma"],
        "event_side": summary["event_side"],
        "preimpact_species": pre_species,
        "direct_cha1_extinctions": extinct,
        "postimpact_survivor_species": survivors,
        "extinction_fraction": summary["extinction_fraction"],
        "extinction_time": summary["extinction_time"],
        "component_count_postevent": summary["component_count_postevent"],
        "q_max_postevent": summary["q_max_postevent"],
    }
    print(json.dumps(compact, indent=2))
    print(json.dumps({
        "checkpoint": checkpoint,
        "serialization_identity": serialization["equivalent"],
        "hazard_repeat_identity": hazard_identity,
        "summary": str(summary_path),
    }, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
