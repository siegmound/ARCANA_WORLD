from __future__ import annotations
import argparse, json
from pathlib import Path

J14="R42_J14_SAPIENT_3MA_TO_200KA_GEONOMICS"
J18="R42_J18_SAPIENT_200KA_TO_0_GEONOMICS"
J21="R42_J21_PRODUCER_20KA_TO_0_GEONOMICS"

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); a=ap.parse_args()
    root=Path(a.root).resolve()
    gp=load(root/"outputs/v0_6D1_R4_32/R4_32_GEONOMICS_CANONICAL_PARAMETER_MATERIALIZATION_REGISTRY.json")
    ia=load(root/"outputs/v0_6D1_R4_32/R4_32_INTEGRATED_AUDIT.json")
    seal=load(root/"outputs/v0_6D1_R4_32_SEAL/R4_32_FINAL_SEAL_AUDIT.json")
    rec={r.get("job_id"):r for r in gp.get("records") or []}
    checks={
      "exact_three_records": gp.get("record_count")==3 and set(rec)=={J14,J18,J21},
      "all_three_static_valid": gp.get("static_valid_count")==3 and all(rec[j].get("static_parameter_manifest_valid") is True for j in (J14,J18,J21)),
      "j18_profile_indirection_recorded": bool(rec[J18].get("r423_profile_path")) and rec[J18].get("r423_binding_materialized") is True,
      "j21_profile_indirection_recorded": bool(rec[J21].get("r423_profile_path")) and rec[J21].get("r423_binding_materialized") is True,
      "j18_source_hash_match": all(s.get("hash_match") is True for s in rec[J18].get("sources") or []),
      "j21_two_source_hash_matches": len(rec[J21].get("sources") or [])==2 and all(s.get("hash_match") is True for s in rec[J21].get("sources") or []),
      "integrated_29_29": ia.get("checks_passed")==29 and ia.get("checks_failed")==0,
      "r432_complete": str(ia.get("status","")).startswith("PASS_R432_"),
      "r432_final_sealed": seal.get("verdict")=="SEALED" and str(seal.get("status","")).endswith("_SEALED"),
      "runtime_parameter_compiled_zero": gp.get("runtime_parameter_compiled_count")==0,
      "geonomics_execution_not_ready": gp.get("geonomics_execution_ready_count")==0,
      "external_engine_execution_not_authorized": gp.get("external_engine_execution_authorized") is False,
      "canonical_state_unchanged": ia.get("canonical_state_changed") is False,
      "no_readjudication": ia.get("readjudication_performed") is False,
    }
    ok=all(checks.values())
    out={
      "stage":"v0.6D1-R4.32-R2",
      "status":"PASS_R432_R2_REPAIR_AND_R432_RESEAL_VERIFIED" if ok else "BLOCKED_R432_R2_POSTREPAIR_RESEAL_FAILURE",
      "checks":checks,
      "checks_passed":sum(checks.values()),"checks_total":len(checks),
      "geonomics_static_valid_count":gp.get("static_valid_count"),
      "r432_status":ia.get("status"),"r432_seal_status":seal.get("status"),"r432_seal_verdict":seal.get("verdict"),
      "next_action":ia.get("next_action"),
    }
    p=root/"outputs/v0_6D1_R4_32_R2/R4_32_R2_POSTREPAIR_RESEAL_AUDIT.json"
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2))
    raise SystemExit(0 if ok else 3)
if __name__=="__main__": main()
