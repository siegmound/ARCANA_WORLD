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
from arcana_worldsim.scientific_engines import r317_recent_restart_sync as r317


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=ROOT / "local_runs/v0_6D1_R3_17")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    parent = r317.validate_parent_r316_authority(ROOT)
    st = parent["state"]
    a1 = parent["a1"]
    c2 = parent["c2"]
    clock = parent["clock"]
    cfg = r317.R317Config()

    before = r316.r315.r313.r312.r311._clone_state(st)
    envelope, accum = r317.build_restart_envelope(st, a1, c2, clock, cfg)
    after_cmp = r38.compare_runtime_states(before, st, atol=0.0)

    acc_path = args.out_dir / "R3_17_PENDING_125_TO_120KA_EXPOSURE_ACCUMULATOR.npz"
    acc_meta = r317.save_accumulator(accum, acc_path)
    loaded = r317.load_accumulator(acc_path)
    acc_roundtrip = (
        abs(float(loaded["duration_years"]) - r317.PENDING_YEARS) <= 1e-12
        and set(loaded["integrals"]) == set(accum)
        and all(np.array_equal(loaded["integrals"][k], np.asarray(v, float)) for k, v in accum.items())
    )

    public_parent = {k: v for k, v in parent.items() if k not in ("state", "a1", "c2", "clock")}
    envelope["parent_r316_authority"] = public_parent
    envelope["pending_exposure_artifact"] = acc_meta
    envelope["biology_parent_identity_after_envelope_build"] = after_cmp

    env_path = args.out_dir / "R3_17_120KA_DUAL_CLOCK_RESTART_ENVELOPE.json"
    env_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    env_sha = r317._sha256(env_path)

    phase = envelope["phase"]
    support = envelope["support_transition_diagnostic"]
    valid = (
        envelope["environmental_restart"]["restart_boundary_at_120ka"] is True
        and envelope["environmental_restart"]["replay_safe_boundary_continuation"] is True
        and envelope["pending_exposure"]["segment_count"] == 10
        and envelope["pending_exposure"]["all_segments_500y"] is True
        and abs(float(envelope["pending_exposure"]["duration_years"]) - 5000.0) <= 1e-9
        and envelope["biology_state_mutated"] is False
        and envelope["biology_state_relabelled_to_120ka"] is False
        and after_cmp.get("equivalent") is True
        and acc_roundtrip
        and abs(float(phase["biology_state_age_ma"]) - 0.125) <= 1e-12
        and abs(float(phase["physical_age_ma"]) - 0.120) <= 1e-12
        and abs(float(phase["remaining_to_next_full_biology_boundary_years"]) - 120000.0) <= 1e-9
        and abs(float(phase["remaining_to_next_transport_boundary_years"]) - 57500.0) <= 1e-9
        and phase["gene_flow_due_at_120ka"] is False
        and phase["transport_due_at_120ka"] is False
        and envelope["governance"]["partial_biology_step_executed"] is False
        and envelope["governance"]["scientific_parameter_changes"] is False
        and envelope["governance"]["deep_biological_coupling"] is False
    )

    verdict = r317.VERDICT if valid else "FAIL_R317_EXACT_120KA_ENVIRONMENTAL_RESTART_SYNC"
    summary = {
        "schema": r317.SUMMARY_SCHEMA,
        "stage": r317.STAGE,
        "verdict": verdict,
        "wall_seconds": time.time() - t0,
        "physical_restart_age_ma": 0.120,
        "biology_state_age_ma": 0.125,
        "biology_state_species": len(set(st.current_species)),
        "biology_state_components": len(st.component_ids),
        "biology_state_population": float(st.pop.sum()),
        "biology_state_mutated": False,
        "biology_state_identity_exact": bool(after_cmp.get("equivalent")),
        "environmental_c2_substeps_consumed": 10,
        "environmental_years_accumulated": 5000.0,
        "next_full_biology_boundary_age_ma": 0.0,
        "remaining_to_next_full_biology_boundary_years": 120000.0,
        "next_transport_boundary_age_ma": 0.0625,
        "remaining_to_next_transport_boundary_years": 57500.0,
        "support_transition_diagnostic": support,
        "artifacts": {
            "restart_envelope": str(env_path),
            "restart_envelope_sha256": env_sha,
            "pending_exposure_accumulator": str(acc_path),
            "pending_exposure_accumulator_sha256": acc_meta["sha256"],
            "accumulator_roundtrip_exact": bool(acc_roundtrip),
        },
        "parent_r316_authority": public_parent,
        "governance": envelope["governance"],
        "next_stage_constraint": {
            "r318_must_combine_pending_5k_exposure_with_120ka_to_0_exposure_before_one_full_125k_biology_step": True,
            "r318_must_not_treat_120ka_as_new_biology_cadence_origin": True,
            "r318_must_not_reapply_gene_flow_before_the_next_full_biology_boundary": True,
            "r318_must_preserve_transport_phase_with_next_boundary_at_62p5ka": True,
        },
    }
    sp = args.out_dir / "R3_17_EXACT_120KA_ENVIRONMENTAL_RESTART_SUMMARY.json"
    sp.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps({
        "stage": r317.STAGE,
        "verdict": verdict,
        "wall_seconds": summary["wall_seconds"],
        "physical_restart_age_ma": 0.120,
        "biology_state_age_ma": 0.125,
        "biology_state_mutated": False,
        "biology_state_identity_exact": bool(after_cmp.get("equivalent")),
        "species": summary["biology_state_species"],
        "components": summary["biology_state_components"],
        "population": summary["biology_state_population"],
        "c2_500y_substeps_accumulated": 10,
        "pending_environmental_years": 5000.0,
        "remaining_to_full_biology_boundary_years": 120000.0,
        "remaining_to_next_transport_boundary_years": 57500.0,
        "population_mass_on_125ka_cells_inaccessible_at_120ka": support["parent_population_mass_on_cells_inaccessible_at_120ka"],
        "partial_biology_step_executed": False,
    }, indent=2))
    print(json.dumps({
        "restart_envelope": {"path": str(env_path), "sha256": env_sha},
        "pending_exposure_accumulator": acc_meta,
        "summary": str(sp),
    }, indent=2))

    try:
        if hasattr(a1, "close"):
            a1.close()
    except Exception:
        pass
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
