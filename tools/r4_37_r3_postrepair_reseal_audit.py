from pathlib import Path
import json
root=Path.cwd()
ia=json.loads((root/"outputs/v0_6D1_R4_37/R4_37_INTEGRATED_AUDIT.json").read_text(encoding="utf-8"))
seal=json.loads((root/"outputs/v0_6D1_R4_37_SEAL/R4_37_FINAL_SEAL_AUDIT.json").read_text(encoding="utf-8"))
j21=json.loads((root/"outputs/v0_6D1_R4_37/R4_37_J21_CANONICAL_NATIVE_LAYER_BINDING_AUDIT.json").read_text(encoding="utf-8"))
j14=json.loads((root/"outputs/v0_6D1_R4_37/R4_37_J14_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json").read_text(encoding="utf-8"))
j18=json.loads((root/"outputs/v0_6D1_R4_37/R4_37_J18_EXACT_STATE_PUBLIC_API_DRY_RUN_AUDIT.json").read_text(encoding="utf-8"))
checks={
 "complete":str(ia.get("status","")).startswith("PASS_R437_") and ia.get("checks_failed")==0,
 "sealed":seal.get("verdict")=="SEALED" and seal.get("checks_failed")==0,
 "j21_596":j21.get("canonical_layer_binding_count")==596 and j21.get("replicate_pass_count")==4,
 "j21_149_plus_2":j21.get("native_identity_payload_count")==149 and j21.get("canonical_physical_unit_sidecar_count")==2,
 "j14_4":j14.get("replicate_pass_count")==4,
 "j18_4":j18.get("replicate_pass_count")==4,
 "j14_coords":j14.get("all_coordinates_native_representable") is True,
 "j18_coords":j18.get("all_coordinates_native_representable") is True,
 "j14_api_incompatible":j14.get("public_api_exact_state_injection_compatible") is False and j14.get("public_api_incompatibility_frozen") is True,
 "j18_api_incompatible":j18.get("public_api_exact_state_injection_compatible") is False and j18.get("public_api_incompatibility_frozen") is True,
 "no_public_mutation":j14.get("public_model_add_individuals_called_count")==0 and j18.get("public_model_add_individuals_called_count")==0,
 "no_private":j14.get("private_geonomics_mutation_api_called_by_arcana") is False and j18.get("private_geonomics_mutation_api_called_by_arcana") is False,
 "no_run":ia.get("model_run_performed_count")==0,
 "no_scientific":ia.get("scientific_engine_execution_performed") is False,
 "canonical_unchanged":ia.get("canonical_state_changed") is False,
 "not_ready":ia.get("geonomics_execution_ready") is False,
 "next_r438":"BUILD_R438_" in str(ia.get("next_action","")),
}
ok=all(checks.values())
out={
 "stage":"v0.6D1-R4.37-R3",
 "status":"PASS_R437_R3_VALIDATION_CLOSURE_AND_R437_RESEAL_VERIFIED" if ok else "BLOCKED_R437_R3_POSTREPAIR_RESEAL_FAILURE",
 "checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),
 "r437_status":ia.get("status"),"seal_status":seal.get("status"),"seal_verdict":seal.get("verdict"),
 "next_action":ia.get("next_action"),
}
p=root/"outputs/v0_6D1_R4_37_R3/R4_37_R3_POSTREPAIR_RESEAL_AUDIT.json"
p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
raise SystemExit(0 if ok else 5)
