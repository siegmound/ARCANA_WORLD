from pathlib import Path
import hashlib,json,shutil

ROOT=Path.cwd()
REP=ROOT/"repairs/v0_6D1_R4_39_R4/replacement"
OUT=ROOT/"outputs/v0_6D1_R4_39_R4"
MODULE=Path("src/arcana_worldsim/scientific_engines/r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py")
PRE="ab2bc731d30f21114993360113c271bf2431bc7bb576a89875617c6ec9171f99"
POST="310f23aadbbf4887e0576efd04ab579eafa49fd0dd38ea39a9f1ffe320099b23"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

active=ROOT/MODULE
if not active.exists():
    raise SystemExit("R4.39-R4 FAIL-CLOSED: active module missing")
cur=sha(active)
if cur not in (PRE,POST):
    raise SystemExit(f"R4.39-R4 FAIL-CLOSED unexpected active module SHA256 {cur}")

rels=[
    MODULE, Path("configs/world1_r439_geonomics_runtime_time_mapping_nonliteral_carrier_dynamics_dynamic_layer_change_preflight_v0_6D1_R4_39.json"), Path("contracts/R4_39_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_DYNAMIC_LAYER_CHANGE_PREFLIGHT_CONTRACT.json"), Path("tests/test_r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py"),
    Path("README_R4_39.md"), Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_39.json")
]
OUT.mkdir(parents=True,exist_ok=True)

if cur==PRE:
    for rel in rels:
        src=ROOT/rel
        if src.exists():
            dst=OUT/"PREPATCH_SOURCE"/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
    failed=ROOT/"outputs/v0_6D1_R4_39"
    if failed.exists():
        dst=OUT/"PREPATCH_FAILED_R439_R3_OUTPUTS"
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(failed,dst)

for rel in rels:
    src=REP/rel
    dst=ROOT/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

audit={
 "stage":"v0.6D1-R4.39-R4",
 "status":"PASS_R439_R4_GEONOMICS_LYR_SERIES_TIMESTEP_RASTER_TUPLE_COMPAT_REPAIR_APPLIED",
 "prepatch_module_sha256":cur,
 "postpatch_module_sha256":sha(ROOT/MODULE),
 "root_cause":"R439_R3_ADAPTER_MISTOOK_GEONOMICS_MAKE_LYR_SERIES_LIST_OF_TIMESTEP_RASTER_TUPLES_FOR_LIST_OF_BARE_RASTERS",
 "repair":"VALIDATE_STEP_0_TIMESTEP_AND_STEP_1_NDARRAY_SHAPE_WHILE_ONLY_REPAIRING_RETURNED_DIM_METADATA",
 "governance":{
   "failed_r439_r3_evidence_preserved":True,
   "r439_r2_source_semantics_preserved":True,
   "canonical_values_modified":False,
   "timestep_labels_modified":False,
   "raster_transpose_performed":False,
   "raster_values_modified":False,
   "geonomics_installed_files_modified":False,
   "changer_executed":False,
   "model_run_performed":False,
   "scientific_execution_performed":False,
   "target_numeric_execution_performed":False,
   "readjudication_performed":False,
   "canonical_state_changed":False,
   "gate_weakening_performed":False
 }
}
(OUT/"R4_39_R4_REPAIR_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
print(json.dumps(audit,indent=2))
