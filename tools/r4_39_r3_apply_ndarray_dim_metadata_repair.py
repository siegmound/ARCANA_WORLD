from pathlib import Path
import hashlib,json,shutil

ROOT=Path.cwd()
REP=ROOT/"repairs/v0_6D1_R4_39_R3/replacement"
OUT=ROOT/"outputs/v0_6D1_R4_39_R3"
MODULE=Path("src/arcana_worldsim/scientific_engines/r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py")
PRE="6b3edb4c80fc53741f6f6086e71185f4b844762d158356896bd97dc0568f8e2c"
POST="ab2bc731d30f21114993360113c271bf2431bc7bb576a89875617c6ec9171f99"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
active=ROOT/MODULE
if not active.exists(): raise SystemExit("R4.39-R3 FAIL-CLOSED: active module missing")
cur=sha(active)
if cur not in (PRE,POST): raise SystemExit(f"R4.39-R3 FAIL-CLOSED unexpected active module SHA256 {cur}")
rels=[Path(x) for x in ['src/arcana_worldsim/scientific_engines/r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py', 'configs/world1_r439_geonomics_runtime_time_mapping_nonliteral_carrier_dynamics_dynamic_layer_change_preflight_v0_6D1_R4_39.json', 'contracts/R4_39_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_DYNAMIC_LAYER_CHANGE_PREFLIGHT_CONTRACT.json', 'tests/test_r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py', 'README_R4_39.md']]
rels.append(Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_39.json"))
OUT.mkdir(parents=True,exist_ok=True)
if cur==PRE:
    for rel in rels:
        src=ROOT/rel
        if src.exists():
            dst=OUT/"PREPATCH_SOURCE"/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    failed=ROOT/"outputs/v0_6D1_R4_39"
    if failed.exists():
        dst=OUT/"PREPATCH_FAILED_R439_R2_OUTPUTS"
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(failed,dst)
for rel in rels:
    src=REP/rel; dst=ROOT/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
audit={
 "stage":"v0.6D1-R4.39-R3",
 "status":"PASS_R439_R3_GEONOMICS_NDARRAY_CHANGE_DIM_METADATA_COMPAT_REPAIR_APPLIED",
 "prepatch_module_sha256":cur,
 "postpatch_module_sha256":sha(ROOT/MODULE),
 "root_cause":"GEONOMICS_1_4_9_NDARRAY_CHANGE_RASTER_REPORTS_NUMPY_YX_SHAPE_AS_LAYER_DIM_METADATA_BUT_LANDSCAPE_DIM_IS_XY",
 "repair":"TEMPORARILY_ADAPT_ONLY_RETURNED_CHANGE_RASTER_DIM_METADATA_YX_TO_XY_DURING_CHANGER_COMPILATION_WITHOUT_TRANSPOSING_OR_MODIFYING_CANONICAL_RASTERS",
 "governance":{
   "failed_r439_r2_evidence_preserved":True,
   "r439_r1_diagnostic_preserved":True,
   "r439_r2_r333_semantics_preserved":True,
   "r437_static_binding_evidence_preserved":True,
   "canonical_values_modified":False,
   "raster_transpose_performed":False,
   "automatic_rescaling_performed":False,
   "clipping_performed":False,
   "result_selected_transform_performed":False,
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
(OUT/"R4_39_R3_REPAIR_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
print(json.dumps(audit,indent=2))
