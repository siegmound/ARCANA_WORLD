from pathlib import Path
import json

root=Path.cwd()
ia=json.loads((root/"outputs/v0_6D1_R4_37/R4_37_INTEGRATED_AUDIT.json").read_text(encoding="utf-8"))
seal=json.loads((root/"outputs/v0_6D1_R4_37_SEAL/R4_37_FINAL_SEAL_AUDIT.json").read_text(encoding="utf-8"))
j21=json.loads((root/"outputs/v0_6D1_R4_37/R4_37_J21_CANONICAL_NATIVE_LAYER_BINDING_AUDIT.json").read_text(encoding="utf-8"))
j14=json.loads((root/"outputs/v0_6D1_R4_37/R4_37_J14_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json").read_text(encoding="utf-8"))
j18=json.loads((root/"outputs/v0_6D1_R4_37/R4_37_J18_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json").read_text(encoding="utf-8"))

checks={
 "r437_complete":str(ia.get("status","")).startswith("PASS_R437_") and ia.get("checks_failed")==0,
 "sealed":seal.get("verdict")=="SEALED" and seal.get("checks_failed")==0,
 "j21_149_native":j21.get("native_identity_payload_count")==149,
 "j21_2_sidecars":j21.get("canonical_physical_unit_sidecar_count")==2,
 "j21_596_bindings":j21.get("canonical_layer_binding_count")==596,
 "j21_4_replicates":j21.get("replicate_pass_count")==4,
 "no_rescale":j21.get("automatic_rescaling_performed") is False,
 "no_result_transform":j21.get("result_selected_transform_performed") is False,
 "j14_4":j14.get("replicate_pass_count")==4,
 "j18_4":j18.get("replicate_pass_count")==4,
 "j14_192_854":j14.get("canonical_branch_count")==192 and j14.get("canonical_carrier_count")==854,
 "j18_64_319":j18.get("canonical_branch_count")==64 and j18.get("canonical_carrier_count")==319,
 "no_private":j14.get("private_geonomics_mutation_api_called_by_arcana") is False and j18.get("private_geonomics_mutation_api_called_by_arcana") is False,
 "no_run":ia.get("model_run_performed_count")==0,
 "not_scientific":ia.get("scientific_engine_execution_performed") is False,
 "canonical_unchanged":ia.get("canonical_state_changed") is False,
 "not_execution_ready":ia.get("geonomics_execution_ready") is False,
 "next_r438":"BUILD_R438_" in str(ia.get("next_action","")),
}
ok=all(checks.values())
out={
 "stage":"v0.6D1-R4.37-R2",
 "status":"PASS_R437_R2_TARGETED_REPAIR_AND_R437_RESEAL_VERIFIED" if ok else "BLOCKED_R437_R2_POSTREPAIR_RESEAL_FAILURE",
 "checks":checks,
 "checks_passed":sum(checks.values()),
 "checks_total":len(checks),
 "r437_status":ia.get("status"),
 "seal_status":seal.get("status"),
 "seal_verdict":seal.get("verdict"),
 "next_action":ia.get("next_action"),
}
p=root/"outputs/v0_6D1_R4_37_R2/R4_37_R2_POSTREPAIR_RESEAL_AUDIT.json"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
raise SystemExit(0 if ok else 5)
