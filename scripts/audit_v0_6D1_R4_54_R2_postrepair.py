from pathlib import Path
import json
root=Path.cwd()
a=json.loads((root/"outputs/v0_6D1_R4_54/R4_54_INTEGRATED_AUDIT.json").read_text())
s=json.loads((root/"outputs/v0_6D1_R4_54_SEAL/R4_54_FINAL_SEAL_AUDIT.json").read_text())
checks={
 "r454_complete":str(a.get("status","")).startswith("PASS_R454_"),
 "r454_sealed":s.get("verdict")=="SEALED",
 "all_five_dry_runs_pass":
   len(a.get("engine_dry_run_results",{}))==5 and
   all(x.get("pass") is True for x in a.get("engine_dry_run_results",{}).values()),
 "nemo_pass":a.get("engine_dry_run_results",{}).get("NEMO",{}).get("pass") is True,
 "slim_pass":a.get("engine_dry_run_results",{}).get("SLiM",{}).get("pass") is True,
 "seed_injection_validated":a.get("exact_seed_injection_dry_run_validated") is True,
 "readout_extraction_validated":a.get("readout_extraction_dry_run_validated") is True,
 "scientific_execution_authorized":a.get("scientific_execution_authorized") is True,
 "dry_run_not_scientific_evidence":a.get("dry_run_is_scientific_evidence") is False,
 "historical_scientific_execution_not_performed":
   a.get("scientific_engine_execution_performed") is False,
 "canonical_unchanged":a.get("canonical_state_changed") is False,
 "next_r455":
   a.get("next_action")=="BUILD_R455_NON_GEONOMICS_80_STREAM_SCIENTIFIC_EXECUTION_AND_EVIDENCE_CAPTURE",
}
ok=all(checks.values())
out={
 "stage":"v0.6D1-R4.54-R2",
 "status":"PASS_R454_R2_NEMO_SLIM_REPAIR_AND_R454_RESEAL_VERIFIED" if ok else "BLOCKED_R454_R2_POSTREPAIR_VERIFICATION",
 "checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),
 "r454_status":a.get("status"),"seal_status":s.get("status"),"seal_verdict":s.get("verdict"),
 "next_action":a.get("next_action")
}
p=root/"outputs/v0_6D1_R4_54_R2/R4_54_R2_POSTREPAIR_RESEAL_AUDIT.json"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
raise SystemExit(0 if ok else 5)
