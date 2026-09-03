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
from arcana_worldsim.scientific_engines import r318_recent_exposure_transport_readiness as r318


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=ROOT / "local_runs/v0_6D1_R3_18")
    args=ap.parse_args(); args.out_dir.mkdir(parents=True, exist_ok=True)
    t0=time.time()

    parent=r318.validate_parent_r317_authority(ROOT)
    st=parent["state"]; a1=parent["a1"]; c2=parent["c2"]; clock=parent["clock"]; pending=parent["pending"]
    before=r311._clone_state(st)
    envelope, integrals=r318.build_recent_exposure_readiness(st,a1,c2,clock,pending,r318.R318Config())
    cmp=r38.compare_runtime_states(before,st,atol=0.0)

    bundle_path=args.out_dir / "R3_18_125KA_TO_0_EXPOSURE_AND_TRANSPORT_PHASES.npz"
    bundle_meta=r318.save_integral_bundle(integrals,bundle_path)
    loaded=r318.load_integral_bundle(bundle_path)
    bundle_roundtrip=(
        abs(float(loaded["biology_state_age_ma"])-0.125)<=1e-12
        and abs(float(loaded["transport_boundary_age_ma"])-0.0625)<=1e-12
        and set(loaded["groups"])==set(integrals)
        and all(np.array_equal(loaded["groups"][g][k],np.asarray(v,float))
                for g,fields in integrals.items() for k,v in fields.items())
    )

    public_parent={k:v for k,v in parent.items() if k not in ("state","a1","c2","clock","pending")}
    envelope["parent_r317_authority"]=public_parent
    envelope["integral_bundle_artifact"]=bundle_meta
    envelope["biology_parent_identity_after_r318_build"]=cmp

    ep=args.out_dir / "R3_18_RECENT_EXPOSURE_TRANSPORT_PHASE_READINESS_ENVELOPE.json"
    ep.write_text(json.dumps(envelope,indent=2),encoding="utf-8")
    esha=r318._sha256(ep)

    phase= envelope["transport_phases"]
    closure=float(envelope["full_125ka_macrostep"]["integral_phase_closure_max_abs"])
    valid=(
        cmp.get("equivalent") is True
        and envelope["biology_state_mutated"] is False
        and envelope["biology_state_relabelled_to_0ka"] is False
        and abs(float(envelope["recent_exposure"]["duration_years"])-120000.0)<=1e-6
        and envelope["recent_exposure"]["contains_62p5ka_transport_boundary"] is True
        and abs(float(phase["phase1"]["duration_years"])-62500.0)<=1e-9
        and abs(float(phase["phase2"]["duration_years"])-62500.0)<=1e-9
        and closure <= 1e-6
        and bundle_roundtrip
        and envelope["governance"]["biology_advanced"] is False
        and envelope["governance"]["transport_advanced"] is False
        and envelope["governance"]["production_biology_closure_authorized_in_r318"] is False
        and envelope["governance"]["scientific_parameter_changes"] is False
        and envelope["governance"]["deep_biological_coupling"] is False
    )
    verdict=r318.VERDICT if valid else "FAIL_R318_RECENT_EXPOSURE_TRANSPORT_READINESS"
    summary={
        "schema":r318.SUMMARY_SCHEMA,
        "stage":r318.STAGE,
        "verdict":verdict,
        "wall_seconds":time.time()-t0,
        "physical_start_age_ma":0.120,
        "physical_end_age_ma":0.0,
        "biology_state_age_ma":0.125,
        "biology_state_identity_exact":bool(cmp.get("equivalent")),
        "species":len(set(st.current_species)),
        "components":len(st.component_ids),
        "population":float(st.pop.sum()),
        "recent_environmental_years_integrated":120000.0,
        "r317_pending_environmental_years_inherited":5000.0,
        "full_macrostep_environmental_years":125000.0,
        "transport_boundary_age_ma":0.0625,
        "transport_phase_years":[62500.0,62500.0],
        "transport_phase_environment_roundoff_equivalent":bool(phase["effective_environment_divergence"]["roundoff_equivalent_all_fields"]),
        "phase_aware_transport_operator_required":bool(phase["phase_aware_transport_operator_required"]),
        "integral_phase_closure_max_abs":closure,
        "support_diagnostics":envelope["support_diagnostics"],
        "parent_population_endpoint_inaccessible_mass":envelope["parent_population_endpoint_inaccessible_mass"],
        "biology_advanced":False,
        "transport_advanced":False,
        "production_biology_closure_authorized_in_r318":False,
        "artifacts":{
            "readiness_envelope":str(ep),
            "readiness_envelope_sha256":esha,
            "integral_bundle":str(bundle_path),
            "integral_bundle_sha256":bundle_meta["sha256"],
            "bundle_roundtrip_exact":bool(bundle_roundtrip),
        },
        "parent_r317_authority":public_parent,
        "next_stage_constraint":envelope["next_stage_requirement"],
    }
    sp=args.out_dir / "R3_18_RECENT_EXPOSURE_COMPLETION_SUMMARY.json"
    sp.write_text(json.dumps(summary,indent=2),encoding="utf-8")

    print(json.dumps({
        "stage":r318.STAGE,"verdict":verdict,"wall_seconds":summary["wall_seconds"],
        "physical_end_age_ma":0.0,"biology_state_age_ma":0.125,
        "biology_state_identity_exact":bool(cmp.get("equivalent")),
        "species":summary["species"],"components":summary["components"],"population":summary["population"],
        "recent_environmental_years_integrated":120000.0,
        "full_macrostep_environmental_years":125000.0,
        "transport_boundary_age_ma":0.0625,
        "transport_phase_years":[62500.0,62500.0],
        "phase_aware_transport_operator_required":summary["phase_aware_transport_operator_required"],
        "transport_phase_environment_global_max_abs_difference":phase["effective_environment_divergence"]["global_max_abs_difference"],
        "integral_phase_closure_max_abs":closure,
        "population_mass_inaccessible_at_62p5ka":envelope["parent_population_endpoint_inaccessible_mass"]["at_62p5ka"],
        "population_mass_inaccessible_at_0ka":envelope["parent_population_endpoint_inaccessible_mass"]["at_0ka"],
        "biology_advanced":False,"transport_advanced":False,
    },indent=2))
    print(json.dumps({"readiness_envelope":{"path":str(ep),"sha256":esha},"integral_bundle":bundle_meta,"summary":str(sp)},indent=2))
    try:
        if hasattr(a1,"close"): a1.close()
    except Exception: pass
    return 0 if valid else 2

if __name__=="__main__": raise SystemExit(main())
