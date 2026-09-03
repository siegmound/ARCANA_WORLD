from pathlib import Path
import json

ROOT = Path.cwd()
OUT = ROOT / "outputs/v0_6D1_R4_37_R1"
R437 = ROOT / "outputs/v0_6D1_R4_37"

J21 = R437 / "R4_37_J21_CANONICAL_NATIVE_LAYER_BINDING_AUDIT.json"
J14 = R437 / "R4_37_J14_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json"
J18 = R437 / "R4_37_J18_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json"
IA = R437 / "R4_37_INTEGRATED_AUDIT.json"

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

missing=[str(p.relative_to(ROOT)) for p in (J21,J14,J18,IA) if not p.exists()]
if missing:
    raise SystemExit("R4.37-R1 FAIL-CLOSED: missing prior R4.37 evidence: " + ", ".join(missing))

j21=load(J21); j14=load(J14); j18=load(J18); ia=load(IA)

range_rows=(j21.get("range_audit") or {}).get("records") or []
bad_range=[]
for r in range_rows:
    ok=(r.get("hash_match") is True and r.get("finite") is True and r.get("range_0_1") is True)
    if not ok:
        bad_range.append({
            "payload_file":r.get("payload_file"),
            "payload_sha256":r.get("payload_sha256"),
            "hash_match":r.get("hash_match"),
            "finite":r.get("finite"),
            "min":r.get("min"),
            "max":r.get("max"),
            "range_0_1":r.get("range_0_1"),
        })

def failures(d):
    out=[]
    for r in d.get("records") or []:
        if r.get("pass") is True:
            continue
        item={
            "replicate_index":r.get("replicate_index"),
            "frozen_seed":r.get("frozen_seed"),
            "model_seed_match":r.get("model_seed_match"),
            "model_unrun_before_dry_run":r.get("model_unrun_before_dry_run"),
            "error":r.get("error"),
        }
        dry=r.get("dry_run")
        if isinstance(dry,dict):
            item["dry_run_summary"]={
                k:dry.get(k) for k in (
                    "pass","error","probe_count","branch_count",
                    "expected_total_carrier_count","observed_added_carrier_count",
                    "coordinate_mismatch_count","max_abs_coordinate_error",
                    "model_unrun_after_dry_run","burned_flag_restored",
                )
            }
            bad_branches=[
                {
                    "branch_index":b.get("branch_index"),
                    "expected_carrier_count":b.get("expected_carrier_count"),
                    "observed_added_carrier_count":b.get("observed_added_carrier_count"),
                    "coordinate_mismatch_count":b.get("coordinate_mismatch_count"),
                    "expected_coordinate_digest":b.get("expected_coordinate_digest"),
                    "observed_coordinate_digest":b.get("observed_coordinate_digest"),
                }
                for b in (dry.get("branch_results") or [])
                if b.get("pass") is not True
            ]
            item["first_10_failed_branches"]=bad_branches[:10]
            item["failed_branch_count"]=len(bad_branches)
        out.append(item)
    return out

j14f=failures(j14)
j18f=failures(j18)

report={
    "stage":"v0.6D1-R4.37-R1",
    "status":"PASS_R437_R1_LIVE_FAILURE_DETAIL_DIAGNOSTIC_CAPTURED",
    "source_r437_status":ia.get("status"),
    "scientific_claim":False,
    "diagnostic_only":True,
    "j21":{
        "status":j21.get("status"),
        "range_record_count":len(range_rows),
        "out_of_native_range_or_invalid_count":len(bad_range),
        "bad_records":bad_range,
        "automatic_rescaling_performed":j21.get("automatic_rescaling_performed"),
        "cross_layer_numeric_fusion_performed":j21.get("cross_layer_numeric_fusion_performed"),
        "replicate_count":j21.get("replicate_count"),
        "replicate_pass_count":j21.get("replicate_pass_count"),
    },
    "j14":{
        "status":j14.get("status"),
        "replicate_count":j14.get("replicate_count"),
        "replicate_pass_count":j14.get("replicate_pass_count"),
        "failures":j14f,
    },
    "j18":{
        "status":j18.get("status"),
        "replicate_count":j18.get("replicate_count"),
        "replicate_pass_count":j18.get("replicate_pass_count"),
        "failures":j18f,
    },
    "governance":{
        "r437_outputs_modified":False,
        "geonomics_execution_performed":False,
        "model_construction_performed":False,
        "payload_values_modified":False,
        "automatic_rescaling_performed":False,
        "target_numeric_execution_performed":False,
        "readjudication_performed":False,
        "canonical_state_changed":False,
        "gate_weakening_performed":False,
    },
    "next_action":"BUILD_R437_R2_TARGETED_REPAIR_FROM_LIVE_FAILURE_DETAIL"
}

OUT.mkdir(parents=True,exist_ok=True)
p=OUT/"R4_37_R1_LIVE_FAILURE_DETAIL_DIAGNOSTIC.json"
p.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2,ensure_ascii=False))
