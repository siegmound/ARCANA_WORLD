from pathlib import Path
import json

root=Path.cwd()
ia=json.loads((root/"outputs/v0_6D1_R4_42/R4_42_INTEGRATED_AUDIT.json").read_text(encoding="utf-8"))
seal=json.loads((root/"outputs/v0_6D1_R4_42_SEAL/R4_42_FINAL_SEAL_AUDIT.json").read_text(encoding="utf-8"))

checks={
 "complete":str(ia.get("status","")).startswith("PASS_R442_") and ia.get("checks_failed")==0,
 "sealed":seal.get("verdict")=="SEALED" and seal.get("checks_failed")==0,
 "j14_4":ia.get("j14_replicate_pass_count")==4,
 "j14_560":ia.get("j14_transition_pass_count")==560,
 "j18_4":ia.get("j18_replicate_pass_count")==4,
 "j18_56":ia.get("j18_transition_pass_count")==56,
 "j21_4":ia.get("j21_replicate_pass_count")==4,
 "j21_32":ia.get("j21_transition_pass_count")==32,
 "total_648":ia.get("bounded_transition_validation_count")==648,
 "production_queue_authorized":ia.get("production_execution_queue_authorized") is True,
 "arcana_queue_only":ia.get("authorized_queue")=="ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE",
 "default_queue_forbidden":ia.get("default_geonomics_queue_authorized") is False,
 "scientific_not_authorized":ia.get("scientific_execution_authorized") is False,
 "not_ready":ia.get("geonomics_execution_ready") is False,
 "canonical_unchanged":ia.get("canonical_state_changed") is False,
 "next_r443":"BUILD_R443_" in str(ia.get("next_action","")),
}
ok=all(checks.values())
out={
 "stage":"v0.6D1-R4.42-R1",
 "status":"PASS_R442_R1_MULTI_STEP_CLOCK_REPAIR_AND_R442_RESEAL_VERIFIED" if ok else "BLOCKED_R442_R1_POSTREPAIR_RESEAL_FAILURE",
 "checks":checks,
 "checks_passed":sum(checks.values()),
 "checks_total":len(checks),
 "r442_status":ia.get("status"),
 "seal_status":seal.get("status"),
 "seal_verdict":seal.get("verdict"),
 "next_action":ia.get("next_action"),
}
p=root/"outputs/v0_6D1_R4_42_R1/R4_42_R1_POSTREPAIR_RESEAL_AUDIT.json"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out,indent=2))
raise SystemExit(0 if ok else 5)
