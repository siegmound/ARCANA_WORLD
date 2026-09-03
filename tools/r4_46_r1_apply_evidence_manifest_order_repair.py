from pathlib import Path
import hashlib, json, shutil

ROOT=Path.cwd()
REP=ROOT/"repairs/v0_6D1_R4_46_R1/replacement"
OUT=ROOT/"outputs/v0_6D1_R4_46_R1"
MODULE=Path("src/arcana_worldsim/scientific_engines/r446_geonomics_first_governed_revalidation_cohort_execution_evidence_capture.py")
PRE="846b1c7d621bb4aa5c48787441b831e4303c2ee166d2f64e5a192249a5c4b423"
POST="5b17d1ee8ef3cb18741764557d8534e72045983edf0109790876a5b9f7f3ecdb"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

active=ROOT/MODULE
if not active.exists():
    raise SystemExit("R4.46-R1 FAIL-CLOSED: active R4.46 module missing")
cur=sha(active)
if cur not in (PRE,POST):
    raise SystemExit(f"R4.46-R1 FAIL-CLOSED unexpected module SHA256 {cur}")

OUT.mkdir(parents=True,exist_ok=True)

if cur==PRE:
    # Preserve original failed scientific execution evidence and failed integrated audit.
    for rel in [
        Path("outputs/v0_6D1_R4_46"),
        Path("outputs/v0_6D1_R4_46_SEAL"),
    ]:
        src=ROOT/rel
        if src.exists():
            dst=OUT/"PREPATCH_FAILED_EVIDENCE"/rel
            if dst.exists():
                shutil.rmtree(dst)
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copytree(src,dst)
    for rel in [
        MODULE,
        Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_46.json"),
    ]:
        src=ROOT/rel
        if src.exists():
            dst=OUT/"PREPATCH_SOURCE"/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)

for rel in [
    MODULE,
    Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_46.json"),
]:
    src=REP/rel
    dst=ROOT/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)

audit={
  "stage":"v0.6D1-R4.46-R1",
  "status":"PASS_R446_R1_EVIDENCE_MANIFEST_METRIC_ID_ORDER_REPAIR_APPLIED",
  "prepatch_module_sha256":cur,
  "postpatch_module_sha256":sha(ROOT/MODULE),
  "root_cause":"R446_EVIDENCE_MANIFEST_SORTED_ACTUAL_METRIC_IDS_BUT_COMPARED_AGAINST_NONCANONICALLY_ORDERED_HARD_CODED_LIST",
  "repair":"COMPARE_SORTED_ACTUAL_METRIC_IDS_TO_SORTED_EXACT_FIVE_AUTHORIZED_METRIC_IDS",
  "governance":{
    "failed_r446_evidence_preserved":True,
    "scientific_execution_rerun_performed":False,
    "scientific_evidence_values_modified":False,
    "metric_records_modified":False,
    "metric_ids_added_or_removed":False,
    "numeric_thresholds_added":False,
    "automatic_scientific_pass_fail_added":False,
    "readjudication_performed":False,
    "canonical_state_changed":False,
    "gate_weakening_performed":False
  }
}
(OUT/"R4_46_R1_REPAIR_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
print(json.dumps(audit,indent=2))
