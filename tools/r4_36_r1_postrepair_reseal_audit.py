from pathlib import Path
import json

root=Path.cwd()
ia=json.loads((root/"outputs/v0_6D1_R4_36/R4_36_INTEGRATED_AUDIT.json").read_text(encoding="utf-8"))
seal=json.loads((root/"outputs/v0_6D1_R4_36_SEAL/R4_36_FINAL_SEAL_AUDIT.json").read_text(encoding="utf-8"))
native=json.loads((root/"outputs/v0_6D1_R4_36/R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json").read_text(encoding="utf-8"))
bridge=json.loads((root/"outputs/v0_6D1_R4_36/R4_36_R1_HOST_RUNTIME_BRIDGE_PREFLIGHT.json").read_text(encoding="utf-8"))

checks={
 "bridge_149": bridge.get("geonomics_version")=="1.4.9",
 "bridge_no_reinstall": bridge.get("reinstall_performed") is False and bridge.get("new_environment_created") is False,
 "integrated_33_33": ia.get("checks_passed")==33 and ia.get("checks_failed")==0,
 "r436_complete": str(ia.get("status","")).startswith("PASS_R436_"),
 "final_seal_25_25": seal.get("checks_passed")==25 and seal.get("checks_failed")==0,
 "sealed": seal.get("verdict")=="SEALED",
 "native_12": native.get("native_parameter_materialized_count")==12,
 "construct_12": native.get("model_construction_pass_count")==12 and native.get("model_construction_blocked_count")==0,
 "version_149": native.get("geonomics_version")=="1.4.9",
 "unrun_12": all(r.get("model_unrun_state_verified") is True for r in native.get("records") or []),
 "seed_match_12": all(r.get("model_seed_match") is True for r in native.get("records") or []),
 "no_model_run": native.get("model_run_performed_count")==0,
 "no_scientific_execution": native.get("scientific_execution_performed") is False,
 "canonical_unchanged": ia.get("canonical_state_changed") is False,
 "next_r437": "BUILD_R437_" in str(ia.get("next_action","")),
}
ok=all(checks.values())
out={
 "stage":"v0.6D1-R4.36-R1",
 "status":"PASS_R436_R1_HOST_RUNTIME_REPAIR_AND_R436_RESEAL_VERIFIED" if ok else "BLOCKED_R436_R1_POSTREPAIR_RESEAL_FAILURE",
 "checks":checks,
 "checks_passed":sum(checks.values()),
 "checks_total":len(checks),
 "r436_status":ia.get("status"),
 "seal_status":seal.get("status"),
 "seal_verdict":seal.get("verdict"),
 "native_parameter_materialized_count":native.get("native_parameter_materialized_count"),
 "model_construction_pass_count":native.get("model_construction_pass_count"),
 "next_action":ia.get("next_action"),
}
p=root/"outputs/v0_6D1_R4_36_R1/R4_36_R1_POSTREPAIR_RESEAL_AUDIT.json"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
raise SystemExit(0 if ok else 5)
