from pathlib import Path
import hashlib, json, shutil

ROOT=Path.cwd()
OUT=ROOT/"outputs/v0_6D1_R4_36_R3"
ACTIVE=ROOT/"tools/r4_36_r2_postrepair_reseal_audit.py"
REPLACEMENT=ROOT/"repairs/v0_6D1_R4_36_R3/replacement/tools/r4_36_r2_postrepair_reseal_audit.py"
EXPECTED_BROKEN_SHA="848627b69ec2c4a678bc09373223e8945b3d8f8a99cbd9e381c720c0a786f5b6"
EXPECTED_FIXED_SHA="42338f13571d57b540c91ebaa39c91c9c67d5e1c15867d8e000bc7148f60d421"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

if not ACTIVE.exists() or not REPLACEMENT.exists():
    raise SystemExit("R4.36-R3 FAIL-CLOSED: postrepair audit helper missing")

current=sha(ACTIVE)
replacement_sha=sha(REPLACEMENT)
if current not in (EXPECTED_BROKEN_SHA, EXPECTED_FIXED_SHA):
    raise SystemExit(
        f"R4.36-R3 FAIL-CLOSED: unexpected postrepair helper SHA256 {current}"
    )

OUT.mkdir(parents=True,exist_ok=True)
if current == EXPECTED_BROKEN_SHA:
    dst=OUT/"PREPATCH/tools/r4_36_r2_postrepair_reseal_audit.py"
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ACTIVE,dst)

shutil.copy2(REPLACEMENT,ACTIVE)

audit={
    "stage":"v0.6D1-R4.36-R3",
    "status":"PASS_R436_R3_POSTREPAIR_AUDIT_SYNTAX_FIX_APPLIED",
    "prepatch_helper_sha256":current,
    "postpatch_helper_sha256":sha(ACTIVE),
    "root_cause":"R436_R2_META_AUDIT_CODEGEN_LEFT_DOUBLE_LITERAL_BRACES_CHECKS_AND_OUT_CAUSING_SET_OF_DICT_TYPEERROR",
    "repair":"ONLY_CORRECT_DOUBLE_LITERAL_BRACES_IN_POSTREPAIR_META_AUDIT",
    "scientific_stage_r436_rerun_required":False,
    "governance":{
        "r436_integrated_outputs_modified":False,
        "r436_final_seal_modified":False,
        "geonomics_execution_performed":False,
        "native_parameter_files_regenerated":False,
        "model_construction_repeated":False,
        "exact_state_injection_performed":False,
        "scientific_execution_performed":False,
        "target_numeric_execution_performed":False,
        "readjudication_performed":False,
        "canonical_state_changed":False,
        "gate_weakening_performed":False,
        "failed_r436_r2_meta_audit_evidence_preserved":True
    }
}
(OUT/"R4_36_R3_REPAIR_AUDIT.json").write_text(
    json.dumps(audit,indent=2)+"\n",encoding="utf-8"
)
print(json.dumps(audit,indent=2))
