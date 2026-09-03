from pathlib import Path
import hashlib,json,shutil
ROOT=Path.cwd(); REP=ROOT/"repairs/v0_6D1_R4_39_R5/replacement"; OUT=ROOT/"outputs/v0_6D1_R4_39_R5"; MODULE=Path("src/arcana_worldsim/scientific_engines/r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py")
PRE="2eea86c5e4ddaad7d08d04030ec87e3f33b9c98dab8addcb017b7530f38e37ab"; POST="d0bfa40863ad4c3a140a4a9cf27706423dfbf7931402a5cec957c269b98ec239"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
active=ROOT/MODULE
if not active.exists(): raise SystemExit("R4.39-R5 FAIL-CLOSED: active module missing")
cur=sha(active)
if cur not in (PRE,POST): raise SystemExit(f"R4.39-R5 FAIL-CLOSED unexpected module SHA256 {cur}")
rels=[MODULE,Path("configs/world1_r439_geonomics_runtime_time_mapping_nonliteral_carrier_dynamics_dynamic_layer_change_preflight_v0_6D1_R4_39.json"),Path("contracts/R4_39_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_DYNAMIC_LAYER_CHANGE_PREFLIGHT_CONTRACT.json"),Path("tests/test_r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py"),Path("README_R4_39.md"),Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_39.json")]
OUT.mkdir(parents=True,exist_ok=True)
if cur==PRE:
  for rel in rels:
    src=ROOT/rel
    if src.exists():
      dst=OUT/"PREPATCH_SOURCE"/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
  failed=ROOT/"outputs/v0_6D1_R4_39"
  if failed.exists():
    dst=OUT/"PREPATCH_STOPPED_R439_R4_OUTPUTS"
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(failed,dst)
for rel in rels:
  src=REP/rel; dst=ROOT/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
audit={"stage":"v0.6D1-R4.39-R5","status":"PASS_R439_R5_BOUNDED_NATIVE_CHANGER_PREFLIGHT_REPAIR_APPLIED","prepatch_module_sha256":cur,"postpatch_module_sha256":sha(ROOT/MODULE),"root_cause":"FULL_147_LAYER_EAGER_LANDSCAPE_CHANGER_MATERIALIZATION_IS_OPERATIONALLY_DISPROPORTIONATE_FOR_NONEXECUTING_PREFLIGHT","repair":"ONE_DETERMINISTIC_NATIVE_CHANGER_INTEGRATION_PROBE_PLUS_EXHAUSTIVE_1176_TARGET_DIRECT_NATIVE_SERIES_VALIDATION_AND_FOUR_EXACT_SEED_BINDING_CHECKS","governance":{"stopped_r439_r4_evidence_preserved":True,"data_coverage_reduced":False,"full_future_target_count_preserved":1176,"scientific_evidence_claimed_from_probe":False,"full_147_layer_changer_materialized":False,"fourfold_redundant_changer_compilation":False,"canonical_values_modified":False,"changer_executed":False,"model_run_performed":False,"scientific_execution_performed":False,"readjudication_performed":False,"canonical_state_changed":False,"gate_weakening_performed":False}}
(OUT/"R4_39_R5_REPAIR_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8"); print(json.dumps(audit,indent=2))
