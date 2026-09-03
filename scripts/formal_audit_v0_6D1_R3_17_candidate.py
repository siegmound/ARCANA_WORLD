from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

STAGE = "v0.6D1-R3.17"
VERDICT = "PASS_R317_CANDIDATE_FORMAL_AUDIT__READY_FOR_LOCAL_EXACT_120KA_ENVIRONMENTAL_RESTART"


def hfile(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class FakeAdapter:
    def __init__(self, *_a, **_k):
        pass
    def state_at_age(self, age):
        age = float(age)
        support = np.ones((2, 3), dtype=float)
        browse = np.full((2, 3), 1.0 + age)
        low = np.full((2, 3), 0.5 + 0.5*age)
        wet = np.full((2, 3), 0.25 + 0.25*age)
        return {
            "age_ma": age, "land_support": support, "accessible": support > 1e-9,
            "temperature_c": np.full((2,3),10.0+age),
            "aridity_index": np.full((2,3),0.3+0.01*age),
            "browse_forage": browse, "low_forage": low, "wetland_forage": wet,
            "total_edible_forage": browse+low+wet,
            "reference_population": np.full((6,2,3),3.0+age),
            "provider":"FAKE_C2", "subprovider":"EXACT_v0.6.1_120KA_ENDPOINT" if abs(age-.12)<1e-12 else "FAKE",
            "authority":"v0.6.1 SEALED_PALEOCLIMATE_HISTORY" if abs(age-.12)<1e-12 else "FAKE",
            "restart_boundary_at_120ka": abs(age-.12)<1e-12,
            "replay_safe_boundary_continuation": True,
            "pre120ka_historical_glacial_chronology_claimed": False,
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve(); out = args.out.resolve()
    sys.path.insert(0, str(root / "src"))
    from arcana_worldsim.scientific_engines import r317_recent_restart_sync as r317

    checks: list[dict[str, Any]] = []
    def ck(name: str, cond: bool, actual: Any = None, expected: Any = None):
        checks.append({"name":name,"pass":bool(cond),"actual":actual,"expected":expected})

    cfg = r317.R317Config()
    constants = {
        "start_physical_age_ma": (cfg.start_physical_age_ma, 0.125),
        "restart_physical_age_ma": (cfg.restart_physical_age_ma, 0.120),
        "biology_state_age_ma": (cfg.biology_state_age_ma, 0.125),
        "biology_cadence_years": (cfg.biology_cadence_years, 125000.0),
        "transport_cadence_years": (cfg.transport_cadence_years, 62500.0),
        "lifecycle_check_interval_years": (cfg.lifecycle_check_interval_years, 500000.0),
    }
    for k,(a,b) in constants.items(): ck(f"config::{k}", abs(float(a)-float(b)) <= 1e-12, a,b)
    for k in ("advance_biology","advance_transport","advance_gene_flow","advance_lifecycle_gates","advance_pair_clocks","advance_demography","advance_selection","advance_variance","deep_biological_coupling"):
        ck(f"config_false::{k}", getattr(cfg,k) is False, getattr(cfg,k), False)

    phase = r317.biology_phase_report()
    expected_phase = {
        "physical_age_ma":0.120,"biology_state_age_ma":0.125,
        "elapsed_since_last_full_biology_boundary_years":5000.0,
        "remaining_to_next_full_biology_boundary_years":120000.0,
        "next_full_biology_boundary_age_ma":0.0,
        "elapsed_since_last_transport_boundary_years":5000.0,
        "remaining_to_next_transport_boundary_years":57500.0,
        "next_transport_boundary_age_ma":0.0625,
    }
    for k,b in expected_phase.items(): ck(f"phase::{k}", abs(float(phase[k])-b) <= 1e-12, phase[k],b)
    for k in ("gene_flow_due_at_120ka","transport_due_at_120ka","lifecycle_gate_due_at_120ka","speciation_gate_due_at_120ka","extinction_gate_due_at_120ka","pair_clock_advanced_to_120ka","demography_advanced_to_120ka","selection_advanced_to_120ka","variance_advanced_to_120ka"):
        ck(f"phase_false::{k}", phase[k] is False, phase[k], False)

    clock={"age_ma":[0.125-i*0.0005 for i in range(11)]}
    part=r317.restart_partition(clock)
    ck("partition_segments_10",part["segment_count"]==10,part["segment_count"],10)
    ck("partition_years_5000",abs(float(part["total_years"])-5000.0)<=1e-9,part["total_years"],5000.0)
    for i,row in enumerate(part["segments"]):
        ck(f"partition_dt500::{i}",abs(float(row["dt_years"])-500.0)<=1e-9,row["dt_years"],500.0)
        ck(f"partition_order::{i}",float(row["older_age_ma"])>float(row["younger_age_ma"]),row)

    adapter=FakeAdapter()
    acc,diag=r317.build_pending_exposure_accumulator(adapter,clock)
    ck("exposure_duration",diag["duration_years"]==5000.0,diag["duration_years"],5000.0)
    ck("exposure_segments",diag["segment_count"]==10,diag["segment_count"],10)
    ck("exposure_nodes",diag["node_count"]==11,diag["node_count"],11)
    ck("exposure_all_500",diag["all_segments_500y"] is True,diag["all_segments_500y"])
    ck("forage_closure",float(diag["total_forage_average_closure_max_abs"])<1e-12,diag["total_forage_average_closure_max_abs"])
    ck("endpoint_forage_closure",float(diag["endpoint_total_forage_closure_max_abs"])<1e-12,diag["endpoint_total_forage_closure_max_abs"])
    for k in r317.r316.AVERAGED_FIELDS:
        a=np.asarray(acc[k],float)
        ck(f"acc_field_exists::{k}",k in acc)
        ck(f"acc_field_finite::{k}",bool(np.isfinite(a).all()))
        ck(f"acc_field_shape::{k}",a.shape==np.asarray(adapter.state_at_age(.125)[k]).shape,a.shape,np.asarray(adapter.state_at_age(.125)[k]).shape)
    mean_temp=np.asarray(acc["temperature_c"])/5000.0
    ck("linear_trapezoid_mean_temperature",float(np.max(np.abs(mean_temp-(10.0+0.1225))))<1e-12,float(np.max(np.abs(mean_temp-(10.0+0.1225)))))

    # Build the full envelope while replacing the concrete adapter only inside this audit.
    orig_adapter=r317.r316.R316C2BridgeEnvironmentAdapter
    r317.r316.R316C2BridgeEnvironmentAdapter=FakeAdapter
    try:
        parent=SimpleNamespace(age_ma=.125,pop=np.ones((2,2,3),float))
        env,acc2=r317.build_restart_envelope(parent,None,None,clock,cfg)
    finally:
        r317.r316.R316C2BridgeEnvironmentAdapter=orig_adapter
    ck("envelope_schema",env["schema"]==r317.ENVELOPE_SCHEMA,env["schema"],r317.ENVELOPE_SCHEMA)
    ck("envelope_physical_120",env["physical_restart_age_ma"]==.120,env["physical_restart_age_ma"],.120)
    ck("envelope_biology_125",env["biology_state_age_ma"]==.125,env["biology_state_age_ma"],.125)
    ck("envelope_not_mutated",env["biology_state_mutated"] is False,env["biology_state_mutated"])
    ck("envelope_not_relabelled",env["biology_state_relabelled_to_120ka"] is False,env["biology_state_relabelled_to_120ka"])
    ck("endpoint_restart_true",env["environmental_restart"]["restart_boundary_at_120ka"] is True,env["environmental_restart"])
    ck("endpoint_replay_safe",env["environmental_restart"]["replay_safe_boundary_continuation"] is True,env["environmental_restart"])
    for k in ("biology_cadence_changed","transport_cadence_changed","gene_flow_step_cadence_changed","lifecycle_gate_cadence_changed","partial_biology_step_executed","adaptive_clock_used_as_biology_timestep","deep_biological_coupling","scientific_parameter_changes","richness_target_used","human_lineage_target_used"):
        ck(f"envelope_governance_false::{k}",env["governance"][k] is False,env["governance"][k])
    ck("envelope_exposure_accumulated",env["governance"]["environmental_exposure_accumulated_without_biology_update"] is True,env["governance"]["environmental_exposure_accumulated_without_biology_update"])
    ck("accumulator_key_identity",set(acc2)==set(r317.r316.AVERAGED_FIELDS),sorted(acc2))

    # Static source gate: R3.17 module itself must not invoke production biology operators.
    srcp=root/"src/arcana_worldsim/scientific_engines/r317_recent_restart_sync.py"
    text=srcp.read_text(encoding="utf-8")
    forbidden=("r38.advance_state(","_apply_demography(","_migration_subcycled_r3(","select_traits(","gene_flow_moment_mix(","advance_nonflow_variance(","advance_pair_states(","maybe_speciate_founder(","ordinary_extinction_update(","apply_mature_fissions_r3(","apply_mature_coalescences_r33(")
    for token in forbidden: ck(f"source_forbidden_absent::{token}",token not in text,token if token in text else None)
    required=("PENDING_FIRST_5KYR_OF_THE_125KA_TO_0KA_SEALED_BIOLOGY_MACROSTEP","DUAL_CLOCK_RESTART_ENVIRONMENT_AT_120KA_WITH_SEALED_BIOLOGY_STATE_CARRIED_FROM_125KA","biology_state_relabelled_to_120ka")
    for token in required: ck(f"source_required_present::{token[:36]}",token in text)

    # Source authority manifest closes inherited code hashes.
    mp=root/"SOURCE_AUTHORITY_MANIFEST_v0_6D1_R3_17.json"
    ck("manifest_exists",mp.is_file(),str(mp))
    manifest=json.loads(mp.read_text(encoding="utf-8")) if mp.is_file() else {}
    ck("manifest_stage",manifest.get("stage")==STAGE,manifest.get("stage"),STAGE)
    ck("manifest_science_unchanged",manifest.get("scientific_parameter_changes") is False,manifest.get("scientific_parameter_changes"))
    ck("manifest_biology_cadence_unchanged",manifest.get("biology_cadence_changes") is False,manifest.get("biology_cadence_changes"))
    for rel,want in manifest.get("inherited_authorities_unchanged",{}).items():
        p=root/rel; ck(f"authority_exists::{rel}",p.is_file(),str(p))
        if p.is_file(): ck(f"authority_sha::{rel}",hfile(p)==want,hfile(p),want)
    for rel,want in manifest.get("r317_files",{}).items():
        p=root/rel; ck(f"r317_exists::{rel}",p.is_file(),str(p))
        if p.is_file(): ck(f"r317_sha::{rel}",hfile(p)==want,hfile(p),want)

    failed=[x for x in checks if not x["pass"]]
    audit={
        "schema":"ARCANA_R317_FORMAL_CANDIDATE_AUDIT_V1",
        "stage":STAGE,
        "verdict":VERDICT if not failed else "FAIL_R317_CANDIDATE_FORMAL_AUDIT",
        "checks":f"{len(checks)-len(failed)}/{len(checks)}",
        "failed":failed,
        "decision":"EXACT_120KA_ENVIRONMENT_RESTART_WITH_DEFERRED_BIOLOGY_PHASE",
        "biology_state_age_ma":0.125,
        "physical_restart_age_ma":0.120,
        "pending_environment_years":5000.0,
        "next_biology_boundary_age_ma":0.0,
        "next_transport_boundary_age_ma":0.0625,
        "partial_biology_step_authorized":False,
        "scientific_parameter_changes":False,
        "deep_biological_coupling":False,
        "source_manifest_sha256":hfile(mp) if mp.is_file() else None,
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(audit,indent=2),encoding="utf-8")
    print(json.dumps({"verdict":audit["verdict"],"checks":audit["checks"],"out":str(out)},indent=2))
    return 0 if not failed else 1

if __name__=="__main__":
    raise SystemExit(main())
