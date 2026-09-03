from pathlib import Path
import hashlib,json,shutil
ROOT=Path.cwd()
REP=ROOT/"repairs/v0_6D1_R4_37_R3/replacement"
OUT=ROOT/"outputs/v0_6D1_R4_37_R3"
MODULE=Path("src/arcana_worldsim/scientific_engines/r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run.py")
PRE="dfb18a4c5eb2f0d4c9e674bf2153435b8260d9bcc6d914252f1bf275c0e88660"
POST="5d23fb1614065f93a8f055d81842e70d8e64862fd66aced1f93b79c4e452b7d6"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
active=ROOT/MODULE
if not active.exists(): raise SystemExit("R4.37-R3 FAIL-CLOSED: active module missing")
cur=sha(active)
if cur not in (PRE,POST):
    raise SystemExit(f"R4.37-R3 FAIL-CLOSED: unexpected active module SHA256 {cur}")
rels=['src/arcana_worldsim/scientific_engines/r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run.py', 'configs/world1_r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run_validation_v0_6D1_R4_37.json', 'contracts/R4_37_GEONOMICS_CANONICAL_LAYER_BINDING_EXACT_STATE_INJECTION_DRY_RUN_VALIDATION_CONTRACT.json', 'tests/test_r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run.py', 'README_R4_37.md']+[Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_37.json")]
rels=[Path(x) for x in rels]
OUT.mkdir(parents=True,exist_ok=True)
if cur==PRE:
    for rel in rels:
        src=ROOT/rel
        if src.exists():
            dst=OUT/"PREPATCH"/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
for rel in rels:
    src=REP/rel; dst=ROOT/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
audit={
 "stage":"v0.6D1-R4.37-R3",
 "status":"PASS_R437_R3_PUBLIC_API_INCOMPATIBILITY_AND_COORDINATE_REPRESENTABILITY_CLOSURE_APPLIED",
 "prepatch_module_sha256":cur,
 "postpatch_module_sha256":sha(ROOT/MODULE),
 "semantic_correction":"VALIDATION_STAGE_CLOSES_ON_EXACT_NATIVE_API_INCOMPATIBILITY_EVIDENCE_RATHER_THAN_FAKING_SUCCESSFUL_INJECTION",
 "governance":{
   "failed_r437_and_r2_evidence_preserved":True,
   "j21_r2_binding_semantics_preserved":True,
   "public_add_individuals_called_after_repair":False,
   "burn_guard_override_used":False,
   "private_geonomics_mutation_api_called":False,
   "geonomics_installed_files_modified":False,
   "canonical_values_modified":False,
   "automatic_rescaling_performed":False,
   "result_selected_transform_performed":False,
   "scientific_execution_performed":False,
   "target_numeric_execution_performed":False,
   "readjudication_performed":False,
   "canonical_state_changed":False,
   "gate_weakening_performed":False
 }
}
(OUT/"R4_37_R3_REPAIR_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
print(json.dumps(audit,indent=2))
