from pathlib import Path
import hashlib,json,shutil

ROOT=Path.cwd()
REP=ROOT/"repairs/v0_6D1_R4_42_R1/replacement"
OUT=ROOT/"outputs/v0_6D1_R4_42_R1"
MODULE=Path("src/arcana_worldsim/scientific_engines/r442_geonomics_multi_transition_bounded_replay_production_queue_authorization.py")
PRE="3c331b020aa07cab54419968c19477a1db5c6da50bbd31cec3c5c65f94a0d6d9"
POST="ca499d8af63b46d432a8974e887650a4b0af1d8538e279f5ae8b2d0d7da0c166"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

active=ROOT/MODULE
if not active.exists():
    raise SystemExit("R4.42-R1 FAIL-CLOSED: active module missing")
cur=sha(active)
if cur not in (PRE,POST):
    raise SystemExit(f"R4.42-R1 FAIL-CLOSED unexpected module SHA256 {cur}")

rels=[
    MODULE,
    Path("README_R4_42.md"),
    Path("tests/test_r442_geonomics_multi_transition_bounded_replay_production_queue_authorization.py"),
    Path("configs/world1_r442_geonomics_multi_transition_bounded_replay_production_execution_queue_authorization_preflight_v0_6D1_R4_42.json"),
    Path("contracts/R4_42_GEONOMICS_MULTI_TRANSITION_BOUNDED_REPLAY_PRODUCTION_EXECUTION_QUEUE_AUTHORIZATION_PREFLIGHT_CONTRACT.json"),
    Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_42.json"),
]

OUT.mkdir(parents=True,exist_ok=True)
if cur==PRE:
    for rel in rels:
        src=ROOT/rel
        if src.exists():
            dst=OUT/"PREPATCH_SOURCE"/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
    failed=ROOT/"outputs/v0_6D1_R4_42"
    if failed.exists():
        dst=OUT/"PREPATCH_FAILED_R442_OUTPUTS"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(failed,dst)

for rel in rels:
    src=REP/rel
    dst=ROOT/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

audit={
  "stage":"v0.6D1-R4.42-R1",
  "status":"PASS_R442_R1_MULTI_STEP_CLOCK_VALIDATION_REPAIR_APPLIED",
  "prepatch_module_sha256":cur,
  "postpatch_module_sha256":sha(ROOT/MODULE),
  "root_cause":"R441_SINGLE_TRANSITION_CLOCK_HELPER_PASS_CONTRACT_REQUIRED_MINUS1_TO_0_AND_WAS_REUSED_ACROSS_R442_MULTI_TRANSITION_SEQUENCE",
  "repair":"LOCAL_R442_EXPECTED_T_MINUS1_TO_T_CLOCK_VALIDATOR_USING_ONLY_R440_AUTHORIZED_CLOCK_PRIMITIVES",
  "governance":{
    "failed_r442_evidence_preserved":True,
    "r441_sealed_source_modified":False,
    "canonical_values_modified":False,
    "autonomous_movement_introduced":False,
    "autonomous_population_dynamics_introduced":False,
    "autonomous_ageing_introduced":False,
    "default_geonomics_walk_authorized":False,
    "scientific_execution_performed":False,
    "target_numeric_execution_performed":False,
    "readjudication_performed":False,
    "canonical_state_changed":False,
    "gate_weakening_performed":False
  }
}
(OUT/"R4_42_R1_REPAIR_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
print(json.dumps(audit,indent=2))
