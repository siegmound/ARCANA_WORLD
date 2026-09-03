from pathlib import Path
import json

root=Path.cwd()
outdir=root/"outputs/v0_6D1_R4_36_R3"
ia=json.loads((root/"outputs/v0_6D1_R4_36/R4_36_INTEGRATED_AUDIT.json").read_text(encoding="utf-8"))
seal=json.loads((root/"outputs/v0_6D1_R4_36_SEAL/R4_36_FINAL_SEAL_AUDIT.json").read_text(encoding="utf-8"))
native=json.loads((root/"outputs/v0_6D1_R4_36/R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json").read_text(encoding="utf-8"))
payload=json.loads((root/"outputs/v0_6D1_R4_36/R4_36_EXACT_STATE_INJECTION_AND_CANONICAL_PAYLOAD_PREFLIGHT.json").read_text(encoding="utf-8"))
r2=json.loads((root/"outputs/v0_6D1_R4_36_R2/R4_36_R2_POSTREPAIR_RESEAL_AUDIT.json").read_text(encoding="utf-8"))

checks={
    "r436_integrated_complete_33_33":
        ia.get("status")=="PASS_R436_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_MODEL_CONSTRUCTION_AND_EXACT_STATE_INJECTION_PREFLIGHT_COMPLETE"
        and ia.get("checks_passed")==33 and ia.get("checks_failed")==0,
    "r436_final_seal_25_25":
        seal.get("status")=="PASS_R436_GEONOMICS_NATIVE_PARAMETER_MATERIALIZATION_MODEL_CONSTRUCTION_AND_EXACT_STATE_INJECTION_PREFLIGHT_SEALED"
        and seal.get("verdict")=="SEALED"
        and seal.get("checks_passed")==25 and seal.get("checks_failed")==0,
    "r2_meta_audit_now_verified":
        r2.get("status")=="PASS_R436_R2_SCHEMA_PROBE_REPAIR_AND_R436_RESEAL_VERIFIED",
    "r2_meta_audit_all_20_checks":
        r2.get("checks_passed")==20 and r2.get("checks_total")==20,
    "geonomics_1_4_9":
        native.get("geonomics_version")=="1.4.9",
    "native_params_12":
        native.get("native_parameter_materialized_count")==12,
    "model_construction_12":
        native.get("model_construction_pass_count")==12
        and native.get("model_construction_blocked_count")==0,
    "all_models_unrun":
        all(x.get("model_unrun_state_verified") is True for x in native.get("records") or []),
    "all_seeds_exact":
        all(x.get("model_seed_match") is True for x in native.get("records") or []),
    "all_injection_api_preflight":
        all(x.get("exact_state_injection_api_preflight_pass") is True for x in native.get("records") or []),
    "j14_192_j18_64":
        payload.get("j14_branch_count")==192 and payload.get("j18_branch_count")==64,
    "j21_151":
        payload.get("j21_canonical_layer_payload_count")==151,
    "no_exact_state_injection":
        payload.get("exact_state_injection_performed_count")==0,
    "no_model_run":
        native.get("model_run_performed_count")==0,
    "no_scientific_execution":
        native.get("scientific_execution_performed") is False,
    "no_target_numeric_execution":
        ia.get("target_numeric_execution_performed") is False,
    "no_readjudication":
        ia.get("readjudication_performed") is False,
    "canonical_unchanged":
        ia.get("canonical_state_changed") is False,
    "deep_off":
        seal.get("summary",{}).get("deep_biological_coupling") is False,
    "next_action_r437":
        ia.get("next_action")=="BUILD_R437_GEONOMICS_CANONICAL_LAYER_BINDING_AND_EXACT_STATE_INJECTION_DRY_RUN_VALIDATION",
}
ok=all(checks.values())
out={
    "stage":"v0.6D1-R4.36-R3",
    "status":"PASS_R436_R3_REPAIR_CHAIN_CLOSED_R436_AUTHORITATIVE_SEAL_PRESERVED"
             if ok else "BLOCKED_R436_R3_REPAIR_CHAIN_CLOSURE",
    "verdict":"CLOSED" if ok else "BLOCKED",
    "checks":checks,
    "checks_passed":sum(checks.values()),
    "checks_total":len(checks),
    "authoritative_stage":"v0.6D1-R4.36",
    "authoritative_stage_verdict":seal.get("verdict"),
    "r436_integrated_status":ia.get("status"),
    "r436_seal_status":seal.get("status"),
    "r436_rerun_performed_by_r3":False,
    "geonomics_execution_performed_by_r3":False,
    "canonical_state_changed_by_r3":False,
    "next_action":ia.get("next_action"),
}
outdir.mkdir(parents=True,exist_ok=True)
(outdir/"R4_36_R3_REPAIR_CHAIN_CLOSURE_AUDIT.json").write_text(
    json.dumps(out,indent=2)+"\n",encoding="utf-8"
)
print(json.dumps(out,indent=2))
raise SystemExit(0 if ok else 6)
