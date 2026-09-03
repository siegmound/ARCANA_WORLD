from pathlib import Path
import json
root=Path.cwd()
ia=json.loads((root/"outputs/v0_6D1_R4_35/R4_35_INTEGRATED_AUDIT.json").read_text())
seal=json.loads((root/"outputs/v0_6D1_R4_35_SEAL/R4_35_FINAL_SEAL_AUDIT.json").read_text())
cl=json.loads((root/"outputs/v0_6D1_R4_35/R4_35_GEONOMICS_NATIVE_SCHEMA_INITIAL_STATE_SEED_AUTHORITY_CLOSURE.json").read_text())
checks={
"integrated_34_34":ia.get("checks_passed")==34 and ia.get("checks_failed")==0,
"r435_complete":str(ia.get("status","")).startswith("PASS_R435_"),
"final_seal_24_24":seal.get("checks_passed")==24 and seal.get("checks_failed")==0,
"sealed":seal.get("verdict")=="SEALED",
"exact_19_closed":cl.get("record_count")==19 and cl.get("terminally_closed_gap_count")==19 and cl.get("blocked_gap_count")==0,
"three_job_closures":cl.get("job_closure_pass_count")==3,
"23x4_seed_vectors":cl.get("seed_authority",{}).get("exact_23_job_replicate_seed_vectors") is True,
"all_92_seeds_unique":cl.get("seed_authority",{}).get("all_92_replicate_seeds_globally_unique") is True,
"three_geonomics_seed_vectors":cl.get("seed_authority",{}).get("geonomics_three_exact_replicate_seed_vectors") is True,
"native_params_zero":cl.get("native_geonomics_params_materialized_count")==0,
"make_model_false":cl.get("gnx_make_model_performed") is False,
"execution_false":cl.get("geonomics_execution_performed") is False,
"canonical_unchanged":cl.get("canonical_state_changed") is False,
"next_r436":"BUILD_R436_" in str(ia.get("next_action",""))}
ok=all(checks.values())
out={"stage":"v0.6D1-R4.35-R2",
"status":"PASS_R435_R2_REPAIR_AND_R435_RESEAL_VERIFIED" if ok else "BLOCKED_R435_R2_POSTREPAIR_RESEAL_FAILURE",
"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),
"r435_status":ia.get("status"),"seal_status":seal.get("status"),"seal_verdict":seal.get("verdict"),
"terminally_closed_gap_count":cl.get("terminally_closed_gap_count"),"next_action":ia.get("next_action")}
p=root/"outputs/v0_6D1_R4_35_R2/R4_35_R2_POSTREPAIR_RESEAL_AUDIT.json"
p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
raise SystemExit(0 if ok else 5)
