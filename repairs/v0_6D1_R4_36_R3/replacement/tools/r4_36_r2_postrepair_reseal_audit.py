from pathlib import Path
import json
root=Path.cwd()
ia=json.loads((root/"outputs/v0_6D1_R4_36/R4_36_INTEGRATED_AUDIT.json").read_text(encoding="utf-8"))
seal=json.loads((root/"outputs/v0_6D1_R4_36_SEAL/R4_36_FINAL_SEAL_AUDIT.json").read_text(encoding="utf-8"))
native=json.loads((root/"outputs/v0_6D1_R4_36/R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json").read_text(encoding="utf-8"))
payload=json.loads((root/"outputs/v0_6D1_R4_36/R4_36_EXACT_STATE_INJECTION_AND_CANONICAL_PAYLOAD_PREFLIGHT.json").read_text(encoding="utf-8"))

adapter=native.get("schema_evidence",{}).get("schema_probe_namespace_adapter",{})
checks={
 "integrated_33_33": ia.get("checks_passed")==33 and ia.get("checks_failed")==0,
 "r436_complete": str(ia.get("status","")).startswith("PASS_R436_"),
 "final_seal_25_25": seal.get("checks_passed")==25 and seal.get("checks_failed")==0,
 "sealed": seal.get("verdict")=="SEALED",
 "version_149": native.get("geonomics_version")=="1.4.9",
 "probe_namespace_repair_recorded": adapter.get("controlled_np_namespace_injected") is True,
 "probe_non_scientific": native.get("schema_evidence",{}).get("scientific_evidence") is False,
 "native_12": native.get("native_parameter_materialized_count")==12,
 "construct_12": native.get("model_construction_pass_count")==12 and native.get("model_construction_blocked_count")==0,
 "unrun_12": all(r.get("model_unrun_state_verified") is True for r in native.get("records") or []),
 "seed_match_12": all(r.get("model_seed_match") is True for r in native.get("records") or []),
 "injection_api_12": all(r.get("exact_state_injection_api_preflight_pass") is True for r in native.get("records") or []),
 "j14_192": payload.get("j14_branch_count")==192,
 "j18_64": payload.get("j18_branch_count")==64,
 "j21_151": payload.get("j21_canonical_layer_payload_count")==151,
 "no_injection": payload.get("exact_state_injection_performed_count")==0,
 "no_model_run": native.get("model_run_performed_count")==0,
 "no_scientific_execution": native.get("scientific_execution_performed") is False,
 "canonical_unchanged": ia.get("canonical_state_changed") is False,
 "next_r437": "BUILD_R437_" in str(ia.get("next_action","")),
}
ok=all(checks.values())
out={
 "stage":"v0.6D1-R4.36-R2",
 "status":"PASS_R436_R2_SCHEMA_PROBE_REPAIR_AND_R436_RESEAL_VERIFIED" if ok else "BLOCKED_R436_R2_POSTREPAIR_RESEAL_FAILURE",
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
p=root/"outputs/v0_6D1_R4_36_R2/R4_36_R2_POSTREPAIR_RESEAL_AUDIT.json"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
raise SystemExit(0 if ok else 5)
