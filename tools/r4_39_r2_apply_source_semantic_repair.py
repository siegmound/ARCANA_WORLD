from pathlib import Path
import hashlib,json,shutil

ROOT=Path.cwd()
REP=ROOT/"repairs/v0_6D1_R4_39_R2/replacement"
OUT=ROOT/"outputs/v0_6D1_R4_39_R2"
MODULE=Path("src/arcana_worldsim/scientific_engines/r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py")
PRE="07000cc2fd933dc6878643dedf23869190984879ac56c7dd614fabd12090a232"
POST="6b3edb4c80fc53741f6f6086e71185f4b844762d158356896bd97dc0568f8e2c"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

active=ROOT/MODULE
if not active.exists():
    raise SystemExit("R4.39-R2 FAIL-CLOSED: active module missing")
cur=sha(active)
if cur not in (PRE,POST):
    raise SystemExit(f"R4.39-R2 FAIL-CLOSED unexpected active module SHA256 {cur}")

rels=[Path(x) for x in ['src/arcana_worldsim/scientific_engines/r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py', 'configs/world1_r439_geonomics_runtime_time_mapping_nonliteral_carrier_dynamics_dynamic_layer_change_preflight_v0_6D1_R4_39.json', 'contracts/R4_39_GEONOMICS_RUNTIME_TIME_MAPPING_NONLITERAL_CARRIER_DYNAMICS_DYNAMIC_LAYER_CHANGE_PREFLIGHT_CONTRACT.json', 'tests/test_r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py', 'README_R4_39.md']]
rels.append(Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_39.json"))

OUT.mkdir(parents=True,exist_ok=True)
if cur==PRE:
    for rel in rels:
        src=ROOT/rel
        if src.exists():
            dst=OUT/"PREPATCH_SOURCE"/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)

    failed_out=ROOT/"outputs/v0_6D1_R4_39"
    if failed_out.exists():
        dst=OUT/"PREPATCH_FAILED_R439_OUTPUTS"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(failed_out,dst)

for rel in rels:
    src=REP/rel
    dst=ROOT/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

r333=ROOT/"src/arcana_worldsim/scientific_engines/r333_holocene_environment_domestication.py"
r333_sha=sha(r333) if r333.exists() else None
if r333_sha!="c32d78efcffccf60dd0a70870dc6d9555a9eed823ec4fa5e7fb3c2e61705fc40":
    raise SystemExit(f"R4.39-R2 FAIL-CLOSED R3.33 source SHA mismatch {r333_sha}")

audit={
  "stage":"v0.6D1-R4.39-R2",
  "status":"PASS_R439_R2_R333_SOURCE_SEMANTIC_DYNAMIC_REPRESENTABILITY_REPAIR_APPLIED",
  "prepatch_module_sha256":cur,
  "postpatch_module_sha256":sha(ROOT/MODULE),
  "r333_source_sha256":r333_sha,
  "root_cause":"R437_STATIC_INITIAL_0_1_REPRESENTABILITY_WAS_INCORRECTLY_PROMOTED_TO_R439_FULL_TRAJECTORY_DOMAIN_AUTHORITY_FOR_PRECIPITATION_AND_NPP_RELATIVE_FACTORS",
  "repair":"REFINE_DYNAMIC_PARTITION_FROM_SEALED_R333_SOURCE_SEMANTICS_TO_147_NATIVE_PLUS_4_SIDECARS_AND_REMOVE_TWO_R437_BOUND_RELATIVE_FACTOR_LAYERS_BEFORE_DYNAMIC_MODEL_CONSTRUCTION",
  "governance":{
    "failed_r439_evidence_preserved":True,
    "r439_r1_diagnostic_preserved":True,
    "r437_seal_modified":False,
    "r437_static_initial_596_binding_evidence_preserved":True,
    "canonical_values_modified":False,
    "epsilon_tolerance_introduced":False,
    "automatic_rescaling_performed":False,
    "clipping_performed":False,
    "result_selected_transform_performed":False,
    "live_bad_minmax_used_as_transform":False,
    "scientific_execution_performed":False,
    "target_numeric_execution_performed":False,
    "readjudication_performed":False,
    "canonical_state_changed":False,
    "gate_weakening_performed":False
  }
}
(OUT/"R4_39_R2_REPAIR_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
print(json.dumps(audit,indent=2))
