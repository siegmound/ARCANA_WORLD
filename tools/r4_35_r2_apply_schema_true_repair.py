from pathlib import Path
import hashlib, json, shutil
ROOT=Path.cwd(); REP=ROOT/"repairs/v0_6D1_R4_35_R2/replacement"; OUT=ROOT/"outputs/v0_6D1_R4_35_R2"
TARGETS=[
 "src/arcana_worldsim/scientific_engines/r435_geonomics_native_schema_initial_state_seed_closure.py",
 "contracts/R4_35_GEONOMICS_NATIVE_SCHEMA_MAPPING_INITIAL_STATE_ADAPTER_SEED_AUTHORITY_CLOSURE_CONTRACT.json",
 "README_R4_35.md",
 "SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_35.json",
]
EXPECTED="585000783b12d41dc8415c657ac9e44348d212959fccf46a8ef608030e372f0d"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/TARGETS[0]
if not source.exists(): raise SystemExit("R4.35-R2 FAIL-CLOSED: active source missing")
current=sha(source); replacement=sha(REP/TARGETS[0])
if current not in (EXPECTED,replacement):
    raise SystemExit(f"R4.35-R2 FAIL-CLOSED: unexpected active source SHA256 {current}")
OUT.mkdir(parents=True,exist_ok=True)
if current==EXPECTED:
    for rel in TARGETS:
        p=ROOT/rel
        if p.exists():
            dest=OUT/"PREPATCH"/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dest)
for rel in TARGETS:
    src=REP/rel; dst=ROOT/rel
    if not src.exists(): raise SystemExit(f"R4.35-R2 replacement missing: {rel}")
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
audit={"stage":"v0.6D1-R4.35-R2","status":"PASS_R435_R2_SCHEMA_TRUE_REPAIR_APPLIED",
"prepatch_source_sha256":current,"postpatch_source_sha256":sha(ROOT/TARGETS[0]),
"root_causes":[
"R43_LEDGER_IS_23_JOBS_X_4_REPLICATE_SEEDS_NOT_ONE_SCALAR_SEED_PER_JOB",
"J18_R423_TRANSLATION_SELECTS_SNAPSHOT_DEME_STATE_NOT_GENERIC_STATE_DISCOVERY",
"J18_COORDINATES_ARE_CONTINUOUS_IN_EXPLICIT_R328_90X180_GRID",
"J21_FEATURE_AXES_WERE_MISREAD_AS_X_DIMENSION",
"J21_TWO_ANCHOR_AGE_AXES_ARE_EXACT_EQUIVALENT_CANONICAL_COPIES"],
"governance":{"r43_modified":False,"r328_modified":False,"r423_modified":False,"r431_modified":False,
"canonical_state_changed":False,"external_engine_execution_performed":False,
"target_numeric_execution_performed":False,"readjudication_performed":False,
"gate_weakening_performed":False,"failed_r435_evidence_preserved":True}}
(OUT/"R4_35_R2_REPAIR_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n")
print(json.dumps(audit,indent=2))
