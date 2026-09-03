from pathlib import Path
import hashlib, json, shutil

ROOT=Path.cwd()
REP=ROOT/"repairs/v0_6D1_R4_36_R1/replacement"
OUT=ROOT/"outputs/v0_6D1_R4_36_R1"
EXPECTED_RUNNER_SHA="cee21b79f621cab8c02373e9ace5eff0a6e2b9dbbf2d80b87cf11c6f9cfdda46"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

active=ROOT/"run_v0_6D1_R4_36.ps1"
replacement=REP/"run_v0_6D1_R4_36.ps1"
if not active.exists() or not replacement.exists():
    raise SystemExit("R4.36-R1 FAIL-CLOSED: runner missing")

current=sha(active)
replacement_sha=sha(replacement)
if current not in (EXPECTED_RUNNER_SHA,replacement_sha):
    raise SystemExit(f"R4.36-R1 FAIL-CLOSED: unexpected active runner SHA256 {current}")

OUT.mkdir(parents=True,exist_ok=True)
if current == EXPECTED_RUNNER_SHA:
    for rel in ["run_v0_6D1_R4_36.ps1","SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_36.json"]:
        src=ROOT/rel
        if src.exists():
            dst=OUT/"PREPATCH"/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)

for rel in ["run_v0_6D1_R4_36.ps1","SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_36.json"]:
    src=REP/rel
    dst=ROOT/rel
    shutil.copy2(src,dst)

audit={
 "stage":"v0.6D1-R4.36-R1",
 "status":"PASS_R436_R1_GOVERNED_WSL_HOST_RUNTIME_BRIDGE_REPAIR_APPLIED",
 "prepatch_runner_sha256":current,
 "postpatch_runner_sha256":sha(ROOT/"run_v0_6D1_R4_36.ps1"),
 "root_cause":"R436_WINDOWS_PROJECT_PYTHON_CANNOT_IMPORT_GOVERNED_GEONOMICS_RUNTIME_INSTALLED_IN_R40_WSL_CONDA_ENV",
 "repair":"ROUTE_ONLY_R436_GEONOMICS_IMPORT_AND_MODEL_CONSTRUCTION_BUILD_THROUGH_EXISTING_R40_WINDOWS_TO_WSL_RUNTIME_BOUNDARY",
 "governance":{
   "geonomics_reinstalled":False,
   "new_environment_created":False,
   "r435_modified":False,
   "r40_runtime_identity_modified":False,
   "native_parameter_semantics_modified":False,
   "seed_authority_modified":False,
   "canonical_payload_modified":False,
   "scientific_execution_performed":False,
   "target_numeric_execution_performed":False,
   "readjudication_performed":False,
   "canonical_state_changed":False,
   "gate_weakening_performed":False,
   "failed_r436_evidence_preserved":True
 }
}
(OUT/"R4_36_R1_REPAIR_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
print(json.dumps(audit,indent=2))
