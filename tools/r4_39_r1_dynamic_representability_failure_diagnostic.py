from pathlib import Path
import json
from collections import Counter, defaultdict

ROOT=Path.cwd()
SRC=ROOT/"outputs/v0_6D1_R4_39"
OUT=ROOT/"outputs/v0_6D1_R4_39_R1"

PAYLOAD=SRC/"R4_39_J21_DYNAMIC_CANONICAL_PAYLOAD_AUTHORITY.json"
DYNAMIC=SRC/"R4_39_J21_NATIVE_DYNAMIC_LAYER_CHANGER_PREFLIGHT.json"
AUDIT=SRC/"R4_39_INTEGRATED_AUDIT.json"
TIME=SRC/"R4_39_EXACT_ORDINAL_TIME_MAPPING.json"
DYN_GATE=SRC/"R4_39_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GATE.json"

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

missing=[str(p.relative_to(ROOT)) for p in (PAYLOAD,DYNAMIC,AUDIT,TIME,DYN_GATE) if not p.exists()]
if missing:
    raise SystemExit("R4.39-R1 FAIL-CLOSED missing prior evidence: "+", ".join(missing))

payload=load(PAYLOAD); dynamic=load(DYNAMIC); audit=load(AUDIT); time=load(TIME); dyn_gate=load(DYN_GATE)

bad=[]
bad_by_var=Counter()
bad_by_age=Counter()
bad_by_family=Counter()
for rec in payload.get("native_identity_records") or []:
    for st in rec.get("states") or []:
        if st.get("native_range_0_1") is True:
            continue
        row={
            "native_layer_name":rec.get("native_layer_name"),
            "layer_family":rec.get("layer_family"),
            "variable_name":rec.get("variable_name"),
            "taxon_id":rec.get("taxon_id"),
            "anchor_index":st.get("anchor_index"),
            "age_ka":st.get("age_ka"),
            "sha256":st.get("sha256"),
            "finite":st.get("finite"),
            "min":st.get("min"),
            "max":st.get("max"),
            "native_range_0_1":st.get("native_range_0_1"),
        }
        bad.append(row)
        bad_by_var[str(row["variable_name"])]+=1
        bad_by_age[str(row["age_ka"])]+=1
        bad_by_family[str(row["layer_family"])]+=1

# summarize candidate fields: which variables were identity-native at initial anchor
# but later leave range. This is evidence only; no repair classification is made here.
field_groups=defaultdict(list)
for row in bad:
    key=(row["layer_family"],row["variable_name"],row["taxon_id"])
    field_groups[key].append(row)
field_summaries=[]
for (family,var,taxon),rows in sorted(field_groups.items(), key=lambda x:(str(x[0][0]),str(x[0][1]),str(x[0][2]))):
    field_summaries.append({
        "layer_family":family,
        "variable_name":var,
        "taxon_id":taxon,
        "bad_anchor_count":len(rows),
        "bad_age_ka":[r["age_ka"] for r in rows],
        "global_min_across_bad_states":min(r["min"] for r in rows if r["min"] is not None),
        "global_max_across_bad_states":max(r["max"] for r in rows if r["max"] is not None),
        "all_bad_states_finite":all(r["finite"] is True for r in rows),
    })

report={
    "stage":"v0.6D1-R4.39-R1",
    "status":"PASS_R439_R1_DYNAMIC_REPRESENTABILITY_FAILURE_DIAGNOSTIC_CAPTURED",
    "source_r439_status":audit.get("status"),
    "diagnostic_only":True,
    "scientific_claim":False,
    "j21_dynamic_payload":{
        "status":payload.get("status"),
        "native_identity_layer_count":payload.get("native_identity_layer_count"),
        "anchor_state_count":len(payload.get("anchor_age_ka") or []),
        "native_identity_anchor_state_count":payload.get("native_identity_anchor_state_count"),
        "future_exact_change_target_count":payload.get("future_exact_change_target_count"),
        "bad_state_count":len(bad),
        "bad_field_count":len(field_summaries),
        "bad_by_variable":dict(bad_by_var),
        "bad_by_age_ka":dict(bad_by_age),
        "bad_by_family":dict(bad_by_family),
        "field_summaries":field_summaries,
        "bad_states":bad,
    },
    "j21_dynamic_model_preflight":{
        "status":dynamic.get("status"),
        "replicate_count":dynamic.get("replicate_count"),
        "replicate_pass_count":dynamic.get("replicate_pass_count"),
        "model_run_performed_count":dynamic.get("model_run_performed_count"),
        "records":dynamic.get("records"),
    },
    "time_mapping_status":time.get("status"),
    "carrier_dynamics_gate_status":dyn_gate.get("status"),
    "governance":{
        "r439_outputs_modified":False,
        "geonomics_execution_performed":False,
        "model_construction_performed":False,
        "changer_executed":False,
        "canonical_values_modified":False,
        "automatic_rescaling_performed":False,
        "clipping_performed":False,
        "result_selected_transform_performed":False,
        "readjudication_performed":False,
        "canonical_state_changed":False,
        "gate_weakening_performed":False,
    },
    "next_action":"BUILD_R439_R2_REPRESENTABILITY_AUTHORITY_REPAIR_FROM_LIVE_DYNAMIC_RANGE_EVIDENCE"
}
OUT.mkdir(parents=True,exist_ok=True)
p=OUT/"R4_39_R1_DYNAMIC_REPRESENTABILITY_FAILURE_DIAGNOSTIC.json"
p.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2,ensure_ascii=False))
