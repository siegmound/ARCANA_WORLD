from pathlib import Path
import hashlib,json,shutil

ROOT=Path.cwd()
REP=ROOT/"repairs/v0_6D1_R4_37_R2/replacement"
OUT=ROOT/"outputs/v0_6D1_R4_37_R2"
MODULE=Path("src/arcana_worldsim/scientific_engines/r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run.py")
EXPECTED_PREPATCH_SHA="18b5ab398e74298d0e6a7cf8586832fae51c8b2c7428704bb20943b86de0d3cf"
EXPECTED_POSTPATCH_SHA="dfb18a4c5eb2f0d4c9e674bf2153435b8260d9bcc6d914252f1bf275c0e88660"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

active=ROOT/MODULE
replacement=REP/MODULE
if not active.exists() or not replacement.exists():
    raise SystemExit("R4.37-R2 FAIL-CLOSED: required module missing")
current=sha(active)
if current not in (EXPECTED_PREPATCH_SHA,EXPECTED_POSTPATCH_SHA):
    raise SystemExit(f"R4.37-R2 FAIL-CLOSED: unexpected active R4.37 module SHA256 {current}")

OUT.mkdir(parents=True,exist_ok=True)
rels=[
    MODULE,
    Path("configs/world1_r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run_validation_v0_6D1_R4_37.json"),
    Path("contracts/R4_37_GEONOMICS_CANONICAL_LAYER_BINDING_EXACT_STATE_INJECTION_DRY_RUN_VALIDATION_CONTRACT.json"),
    Path("tests/test_r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run.py"),
    Path("README_R4_37.md"),
    Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_37.json"),
]
if current==EXPECTED_PREPATCH_SHA:
    for rel in rels:
        src=ROOT/rel
        if src.exists():
            dst=OUT/"PREPATCH"/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)

for rel in rels:
    src=REP/rel
    dst=ROOT/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

audit={
 "stage":"v0.6D1-R4.37-R2",
 "status":"PASS_R437_R2_NATIVE_REPRESENTABILITY_AND_PUBLIC_API_COMPAT_REPAIR_APPLIED",
 "prepatch_module_sha256":current,
 "postpatch_module_sha256":sha(ROOT/MODULE),
 "root_causes":[
   "J21_TWO_CANONICAL_PHYSICAL_UNIT_FIELDS_NOT_VALID_GEONOMICS_LAYER_RAST_DOMAIN",
   "GEONOMICS_1_4_9_Model_add_individuals_REFERENCES_UNDEFINED_species_SYMBOL"
 ],
 "repair":[
   "BIND_149_IDENTITY_NATIVE_LAYERS_AND_PRESERVE_2_PHYSICAL_UNIT_HASH_BOUND_SIDECARS_WITHOUT_SCALING",
   "TEMPORARY_IN_PROCESS_PUBLIC_WRAPPER_SYMBOL_COMPAT_SHIM_FOR_DISPOSABLE_MECHANICAL_DRY_RUN"
 ],
 "governance":{
   "failed_r437_evidence_preserved":True,
   "r437_r1_diagnostic_preserved":True,
   "canonical_values_modified":False,
   "automatic_rescaling_performed":False,
   "result_selected_transform_performed":False,
   "geonomics_installed_files_modified":False,
   "arcana_private_geonomics_mutation_api_authorized":False,
   "scientific_execution_performed":False,
   "target_numeric_execution_performed":False,
   "readjudication_performed":False,
   "canonical_state_changed":False,
   "gate_weakening_performed":False
 }
}
(OUT/"R4_37_R2_REPAIR_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
print(json.dumps(audit,indent=2))
