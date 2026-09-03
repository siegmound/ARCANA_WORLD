from pathlib import Path
import json

root=Path.cwd()
ia=json.loads((root/"outputs/v0_6D1_R4_39/R4_39_INTEGRATED_AUDIT.json").read_text(encoding="utf-8"))
seal=json.loads((root/"outputs/v0_6D1_R4_39_SEAL/R4_39_FINAL_SEAL_AUDIT.json").read_text(encoding="utf-8"))
sem=json.loads((root/"outputs/v0_6D1_R4_39/R4_39_R333_DYNAMIC_REPRESENTABILITY_SEMANTIC_AUTHORITY.json").read_text(encoding="utf-8"))
pay=json.loads((root/"outputs/v0_6D1_R4_39/R4_39_J21_DYNAMIC_CANONICAL_PAYLOAD_AUTHORITY.json").read_text(encoding="utf-8"))
dyn=json.loads((root/"outputs/v0_6D1_R4_39/R4_39_J21_NATIVE_DYNAMIC_LAYER_CHANGER_PREFLIGHT.json").read_text(encoding="utf-8"))
gate=json.loads((root/"outputs/v0_6D1_R4_39/R4_39_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GATE.json").read_text(encoding="utf-8"))

checks={
 "complete":str(ia.get("status","")).startswith("PASS_R439_") and ia.get("checks_failed")==0,
 "sealed":seal.get("verdict")=="SEALED" and seal.get("checks_failed")==0,
 "r333_semantics":sem.get("pass") is True and sem.get("checks_passed")==sem.get("checks_total"),
 "dynamic_147":pay.get("native_identity_layer_count")==147,
 "sidecars_4":pay.get("canonical_dynamic_sidecar_count")==4,
 "static_history_149_plus_2":pay.get("r437_static_initial_native_layer_count")==149 and pay.get("r437_static_initial_sidecar_count")==2,
 "states_1323":pay.get("native_identity_anchor_state_count")==1323,
 "targets_1176":pay.get("future_exact_change_target_count")==1176,
 "all_native_0_1":pay.get("all_native_states_finite_and_0_1") is True,
 "no_scale_clip_transform":pay.get("automatic_rescaling_performed") is False and pay.get("clipping_performed") is False and pay.get("result_selected_transform_performed") is False,
 "dynamic_replicates_4":dyn.get("replicate_pass_count")==4,
 "compiled_4704":dyn.get("compiled_exact_change_target_count_all_replicates")==4704,
 "sidecars_not_in_changer":dyn.get("dynamic_sidecars_in_changer") is False,
 "two_static_bound_layers_removed":dyn.get("r437_bound_layers_removed_before_dynamic_model_construction")==2,
 "changer_not_executed":dyn.get("changer_make_change_called") is False,
 "carrier_gap_frozen":gate.get("status")=="R439_NONLITERAL_CARRIER_DYNAMICS_AUTHORITY_GAP_FROZEN",
 "no_run":ia.get("model_run_performed_count")==0,
 "not_ready":ia.get("geonomics_execution_ready") is False,
 "no_scientific":ia.get("scientific_engine_execution_performed") is False,
 "canonical_unchanged":ia.get("canonical_state_changed") is False,
 "next_r440":"BUILD_R440_" in str(ia.get("next_action","")),
}
ok=all(checks.values())
out={
 "stage":"v0.6D1-R4.39-R2",
 "status":"PASS_R439_R2_SOURCE_SEMANTIC_REPAIR_AND_R439_RESEAL_VERIFIED" if ok else "BLOCKED_R439_R2_POSTREPAIR_RESEAL_FAILURE",
 "checks":checks,
 "checks_passed":sum(checks.values()),
 "checks_total":len(checks),
 "r439_status":ia.get("status"),
 "seal_status":seal.get("status"),
 "seal_verdict":seal.get("verdict"),
 "next_action":ia.get("next_action"),
}
p=root/"outputs/v0_6D1_R4_39_R2/R4_39_R2_POSTREPAIR_RESEAL_AUDIT.json"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
raise SystemExit(0 if ok else 5)
