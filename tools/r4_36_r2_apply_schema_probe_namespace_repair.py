from pathlib import Path
import hashlib, json, shutil

ROOT=Path.cwd()
REP=ROOT/"repairs/v0_6D1_R4_36_R2/replacement"
OUT=ROOT/"outputs/v0_6D1_R4_36_R2"
MODULE=Path("src/arcana_worldsim/scientific_engines/r436_geonomics_native_parameter_model_construction_injection_preflight.py")
EXPECTED_PREPATCH_MODULE_SHA="5ca7574b6ed88f7b5b9cae1c12622bddb36c859ff6bd7fd7101a023931cb24f1"
EXPECTED_R1_RUNNER_SHA="6bd672d2110ee36fa489582937f8918a12ef9c1ff31eeb8bb2d1c84a576bdad9"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

active_module=ROOT/MODULE
active_runner=ROOT/"run_v0_6D1_R4_36.ps1"
replacement_module=REP/MODULE
if not active_module.exists() or not active_runner.exists() or not replacement_module.exists():
    raise SystemExit("R4.36-R2 FAIL-CLOSED: required file missing")

current_module=sha(active_module)
new_module=sha(replacement_module)
if current_module not in (EXPECTED_PREPATCH_MODULE_SHA,new_module):
    raise SystemExit(f"R4.36-R2 FAIL-CLOSED: unexpected active module SHA256 {current_module}")
if sha(active_runner) != EXPECTED_R1_RUNNER_SHA:
    raise SystemExit(
        "R4.36-R2 FAIL-CLOSED: R4.36-R1 governed WSL runtime bridge runner is not active"
    )

OUT.mkdir(parents=True,exist_ok=True)
if current_module == EXPECTED_PREPATCH_MODULE_SHA:
    for rel in [MODULE,Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_36.json")]:
        src=ROOT/rel
        if src.exists():
            dst=OUT/"PREPATCH"/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)

for rel in [MODULE,Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_36.json")]:
    src=REP/rel
    dst=ROOT/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

audit={
  "stage":"v0.6D1-R4.36-R2",
  "status":"PASS_R436_R2_GEONOMICS_DEFINED_LAYER_SCHEMA_PROBE_NAMESPACE_REPAIR_APPLIED",
  "prepatch_module_sha256":current_module,
  "postpatch_module_sha256":sha(ROOT/MODULE),
  "active_r1_runner_sha256":sha(active_runner),
  "root_cause":"GEONOMICS_1_4_9_DEFINED_LAYER_GENERATOR_EMITS_NP_ONES_WITHOUT_SELF_CONTAINED_NUMPY_IMPORT_IN_SCHEMA_PROBE_FILE",
  "repair":"CONTROLLED_NUMPY_NAMESPACE_ONLY_WHEN_READING_NON_SCIENTIFIC_INSTALLED_RUNTIME_SCHEMA_PROBE",
  "strict_arcana_native_parameter_import_path_unchanged":True,
  "governance":{
    "geonomics_modified":False,
    "geonomics_reinstalled":False,
    "runtime_identity_modified":False,
    "r435_modified":False,
    "seed_authority_modified":False,
    "canonical_payload_modified":False,
    "native_parameter_scientific_semantics_modified":False,
    "scientific_execution_performed":False,
    "target_numeric_execution_performed":False,
    "readjudication_performed":False,
    "canonical_state_changed":False,
    "gate_weakening_performed":False,
    "failed_r436_evidence_preserved":True
  }
}
(OUT/"R4_36_R2_REPAIR_AUDIT.json").write_text(
    json.dumps(audit,indent=2)+"\n",encoding="utf-8"
)
print(json.dumps(audit,indent=2))
