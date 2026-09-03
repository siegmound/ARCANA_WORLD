from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import math
import re

STAGE = "v0.6D1-R4.10"
R49_SEALED = "PASS_R49_ADDITIONAL_MATCHED_CONTROL_REPLICATES_AND_CAUSAL_DIRECTION_RESOLUTION_SEALED"
R49_UNCERTAIN = "EXPANDED_MATCHED_CONTROL_EFFECT_UNCERTAIN"
COMPLETE = "PASS_R410_MATCHED_CONTROL_PRECISION_ALTERNATE_EVIDENCE_AND_POPULATION_METRIC_INTEGRITY_AUDIT_COMPLETE"
SEALED = "PASS_R410_MATCHED_CONTROL_PRECISION_ALTERNATE_EVIDENCE_AND_POPULATION_METRIC_INTEGRITY_AUDIT_SEALED"
BLOCKED = "BLOCKED_R410_PARENT_OR_EVIDENCE_INTEGRITY_AUDIT_FAILURE"
FINDING = "R43_R49_CDMETAPOP_POPULATION_METRIC_FILENAME_SELECTOR_COLLISION_CONFIRMED"
NEXT = "BUILD_R411_CDMETAPOP_POPULATION_METRIC_EXTRACTION_REPAIR_AND_SYMMETRIC_READJUDICATION"

CFG_REL = Path("configs/world1_r410_matched_control_precision_alternate_evidence_v0_6D1_R4_10.json")
R49_SEAL_REL = Path("outputs/v0_6D1_R4_9_SEAL/R4_9_FINAL_SEAL_AUDIT.json")
R49_DIAG_REL = Path("outputs/v0_6D1_R4_9/R4_9_CAUSAL_DIRECTION_RESOLUTION.json")
R49_PAIR_REL = Path("outputs/v0_6D1_R4_9/R4_9_EXPANDED_PAIRED_CAUSAL_EFFECT.json")
R44_CFG_REL = Path("configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json")
R47_MATRIX_REL = Path("outputs/v0_6D1_R4_7/R4_7_CDMETAPOP_READJUDICATED_MATRIX.json")
R47_RAW_REL = Path("outputs/v0_6D1_R4_7/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/RAW_EVIDENCE.json")
R47_PROFILE_REL = Path("outputs/v0_6D1_R4_7/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/REPAIR_PROFILE.json")
OUT_REL = Path("outputs/v0_6D1_R4_10")
SEAL_REL = Path("outputs/v0_6D1_R4_10_SEAL/R4_10_FINAL_SEAL_AUDIT.json")

ADAPTER_RELS = [
    Path("benchmarks/r43/cdmetapop_r43.py"),
    Path("benchmarks/r47/cdmetapop_r47.py"),
    Path("benchmarks/r48/cdmetapop_r48_neutral.py"),
    Path("benchmarks/r49/cdmetapop_r49_dynamic.py"),
    Path("benchmarks/r49/cdmetapop_r49_neutral.py"),
]
CDM_POST_REL = Path(".arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_PostProcess.py")
CDM_EXAMPLES_REL = Path(".arcana_engines/CDMetaPOP-3.08/example_files")

@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: Any = None
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "pass": bool(self.passed), "detail": self.detail}

def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

def finite(x: Any) -> float | None:
    try: v = float(x)
    except (TypeError, ValueError): return None
    return v if math.isfinite(v) else None

def strict_individual_output_name(name: str) -> bool:
    return re.fullmatch(r"ind-?\d+\.csv", name, flags=re.IGNORECASE) is not None

def broad_selector_source_detected(text: str) -> bool:
    compact = text.replace('"', "'")
    return "'ind' in p.name.lower()" in compact or "'ind' in p.name.lower" in compact

def copied_input_collision_names(example_root: Path) -> list[str]:
    if not example_root.exists(): return []
    out=[]
    for p in example_root.rglob("*.csv"):
        if "ind" in p.name.lower() and not strict_individual_output_name(p.name):
            out.append(p.relative_to(example_root).as_posix())
    return sorted(out)

def _paired_values(pair: dict[str,Any]) -> list[float]:
    vals=[]
    for row in pair.get("paired_replicates",[]):
        v=finite(row.get("paired_forcing_effect_ratio")) if isinstance(row,dict) else None
        if v is not None: vals.append(v)
    return vals

def _runtime_summary_inventory(root: Path) -> dict[str,Any]:
    # Existing runtime work is evidence, not a required parent contract. We inventory it
    # to determine whether R4.11 can repair by re-extraction without engine reruns.
    bases={
      "R47_DYNAMIC_J09": root/"outputs/v0_6D1_R4_7/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP",
      "R48_NEUTRAL_J09": root/"outputs/v0_6D1_R4_8/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP",
      "R49_ADDITIONAL_J09": root/"outputs/v0_6D1_R4_9/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP",
    }
    inv={}
    for label,b in bases.items():
        files=sorted(p.relative_to(b).as_posix() for p in b.rglob("summary_popAllTime.csv")) if b.exists() else []
        inv[label]={"base":str(b.relative_to(root)) if b.exists() else str(b),"summary_popAllTime_count":len(files),"examples":files[:8]}
    # All five R4.7 CDMetaPOP jobs are required for symmetric re-extraction.
    r47root=root/"outputs/v0_6D1_R4_7/jobs"
    five=[]
    if r47root.exists():
        for d in sorted(r47root.glob("R42_J*_CDMETAPOP")):
            files=list(d.rglob("summary_popAllTime.csv"))
            five.append({"job_id":d.name,"summary_popAllTime_count":len(files)})
    inv["R47_ALL_CDMETAPOP_JOBS"]={"jobs":five,"job_count":len(five),"jobs_with_summary":sum(x["summary_popAllTime_count"]>0 for x in five)}
    return inv

def _primary_context(matrix: dict[str,Any], authorized: dict[str,Any]) -> dict[str,Any]:
    rows=[]
    for r in matrix.get("evidence_rows",[]):
        if not isinstance(r,dict): continue
        if r.get("window_id")==authorized["window_id"] and r.get("domain")==authorized["domain"]:
            rows.append({k:r.get(k) for k in ["engine","job_id","authority_role","mapping_comparability","discordance_class","reason","target_direction","external_direction"]})
    return {"window_id":authorized["window_id"],"domain":authorized["domain"],"rows":rows,
            "primary_rows":[r for r in rows if r.get("authority_role")=="PRIMARY"],
            "majority_vote":False,
            "interpretation":"Context only. R4.10 does not combine authority rows by vote or promote a new canonical conclusion."}

def audit(root: Path) -> tuple[dict[str,Any], list[Check]]:
    cfg=load_json(root/CFG_REL)
    parent=load_json(root/R49_SEAL_REL) if (root/R49_SEAL_REL).exists() else {}
    diag=load_json(root/R49_DIAG_REL) if (root/R49_DIAG_REL).exists() else {}
    pair=load_json(root/R49_PAIR_REL) if (root/R49_PAIR_REL).exists() else {}
    r44cfg=load_json(root/R44_CFG_REL) if (root/R44_CFG_REL).exists() else {}
    matrix=load_json(root/R47_MATRIX_REL) if (root/R47_MATRIX_REL).exists() else {}
    raw47=load_json(root/R47_RAW_REL) if (root/R47_RAW_REL).exists() else {}

    adapter_sources={}
    broad=[]
    for rel in ADAPTER_RELS:
        p=root/rel
        text=p.read_text(encoding="utf-8-sig") if p.exists() else ""
        hit=broad_selector_source_detected(text)
        adapter_sources[str(rel)]={"present":p.exists(),"broad_ind_substring_selector_detected":hit}
        if hit: broad.append(str(rel))

    collisions=copied_input_collision_names(root/CDM_EXAMPLES_REL)
    post_text=(root/CDM_POST_REL).read_text(encoding="utf-8-sig",errors="replace") if (root/CDM_POST_REL).exists() else ""
    summary_supported="summary_popAllTime.csv" in post_text and "N_Initial" in post_text

    vals=_paired_values(pair)
    neutral=finite((pair.get("neutral_factor")))
    if neutral is None: neutral=finite((r44cfg.get("effect_policy") or {}).get("ratio_neutral_factor"))
    low=(1.0/neutral) if neutral and neutral>0 else None
    high=neutral
    counts={"below_lower":0,"inside_neutral":0,"above_upper":0}
    if low is not None and high is not None:
        for v in vals:
            if v<low: counts["below_lower"]+=1
            elif v>high: counts["above_upper"]+=1
            else: counts["inside_neutral"]+=1
    ps=pair.get("cdmetapop_expanded_paired_forcing_effect") or {}
    arc=finite(pair.get("arcana_causal_forcing_effect_ratio"))
    med=finite(ps.get("median"))
    q90=finite(ps.get("q90"))

    # The adapters set N0 to at least 10 per initialized patch. A reported total initial
    # population below 10 cannot be the full initialized population and is a strong
    # integrity signal even before opening runtime work.
    reported_initials=[]
    for row in pair.get("paired_replicates",[]):
        if isinstance(row,dict):
            v=finite(row.get("dynamic_initial"))
            if v is not None: reported_initials.append(v)
    impossible_small=bool(reported_initials) and max(reported_initials)<10.0

    finding_confirmed=(len(broad)>=1 and len(collisions)>=1 and summary_supported and impossible_small)
    runtime_inventory=_runtime_summary_inventory(root)
    authorized=cfg["authorized_case"]
    context=_primary_context(matrix,authorized)

    checks=[
      Check("parent_r49_seal_present",(root/R49_SEAL_REL).exists(),str(R49_SEAL_REL)),
      Check("parent_r49_sealed",parent.get("status")==R49_SEALED,parent.get("status")),
      Check("parent_r49_diagnosis_uncertain",diag.get("diagnosis_class")==R49_UNCERTAIN,diag.get("diagnosis_class")),
      Check("parent_next_action_matches_r410",parent.get("next_action")==cfg["required_parent_next_action"],parent.get("next_action")),
      Check("parent_exact_20_pairs",len(vals)==20,len(vals)),
      Check("r410_does_not_posthoc_reclassify_r49",cfg["precision_policy"]["preserve_r49_diagnosis_without_posthoc_reclassification"] is True),
      Check("automatic_further_replicates_forbidden",cfg["precision_policy"]["automatic_additional_replicates_forbidden"] is True),
      Check("all_cdmetapop_population_adapter_sources_present",all(v["present"] for v in adapter_sources.values()),adapter_sources),
      Check("broad_ind_filename_selector_detected",len(broad)>=1,broad),
      Check("copied_input_filename_collision_exists",len(collisions)>=1,collisions),
      Check("cdmetapop_summary_population_tracking_supported",summary_supported,str(CDM_POST_REL)),
      Check("r49_reported_initial_population_is_incompatible_with_adapter_min_n0",impossible_small,reported_initials[:20]),
      Check("population_metric_selector_collision_finding_confirmed",finding_confirmed,FINDING if finding_confirmed else None),
      Check("historical_evidence_preserved_not_deleted",cfg["cdmetapop_population_metric_integrity_policy"]["historical_invalid_metrics_preserved_but_not_promoted"] is True),
      Check("r411_reextract_before_rerun",cfg["r411_closure_policy"]["reextract_existing_runtime_outputs_before_any_rerun"] is True),
      Check("r411_symmetric_five_job_repair",cfg["r411_closure_policy"]["repair_applies_symmetrically_to_all_five_cdmetapop_jobs"] is True),
      Check("canonical_state_unchanged",cfg["canonical_state_changed"] is False),
      Check("canonical_replay_not_authorized",cfg["canonical_replay_authorized"] is False),
      Check("canonical_parameter_change_not_authorized",cfg["canonical_parameter_change_authorized"] is False),
      Check("deep_off",cfg["deep_biological_coupling"] is False),
      Check("majority_vote_forbidden",cfg["majority_vote"] is False),
    ]

    precision={
      "stage":STAGE,
      "parent_diagnosis_preserved":diag.get("diagnosis_class"),
      "n":len(vals),
      "arcana_causal_forcing_effect_ratio":arc,
      "cdmetapop_paired_summary":ps,
      "neutral_factor":neutral,
      "neutral_band":[low,high] if low is not None and high is not None else None,
      "descriptive_pair_counts":counts,
      "median_minus_arcana":(med-arc) if med is not None and arc is not None else None,
      "median_distance_below_neutral_lower_edge":(low-med) if med is not None and low is not None else None,
      "q90_minus_neutral_lower_edge":(q90-low) if q90 is not None and low is not None else None,
      "precision_reclassification_authorized":False,
      "reason":"R4.9 remains historically SEALED as uncertain. R4.10 discovered a population-metric extraction integrity defect, so more replicate precision on the old metric is not admissible before extraction repair."
    }
    integrity={
      "stage":STAGE,
      "finding":FINDING if finding_confirmed else "NOT_CONFIRMED",
      "finding_confirmed":finding_confirmed,
      "adapter_source_audit":adapter_sources,
      "collision_input_files":collisions,
      "strict_allowed_individual_output_regex":cfg["cdmetapop_population_metric_integrity_policy"]["strict_individual_filename_regex"],
      "preferred_repair_artifact":"summary_popAllTime.csv",
      "preferred_repair_field":"N_Initial",
      "reported_r49_dynamic_initial_populations":reported_initials,
      "runtime_summary_inventory":runtime_inventory,
      "raw_r47_adapter_status":raw47.get("adapter_status"),
      "impact":{
        "r43_r47_absolute_population_response_ratio":"NOT_ADMISSIBLE_FOR_NEW_ADJUDICATION_UNTIL_REEXTRACTED",
        "r48_r49_paired_effect":"PRESERVE_AS_HISTORICAL_DIAGNOSTIC_BUT_REBUILD_FROM_REPAIRED_TRACKING",
        "r47_structural_disagreement":"PRESERVE_HISTORICALLY_BUT_DO_NOT_USE_TO_AUTHORIZE_CANONICAL_REPLAY",
        "canonical_state":"UNCHANGED"
      }
    }
    plan={
      "stage":STAGE,
      "status":"R411_PLAN_FROZEN" if finding_confirmed else "R411_PLAN_BLOCKED_PENDING_INTEGRITY_FINDING",
      "next_stage":"v0.6D1-R4.11",
      "actions":[
        "IMPLEMENT_STRICT_CDMETAPOP_POPULATION_TRACKING_EXTRACTOR_FROM_SUMMARY_POPALLTIME_N_INITIAL",
        "REEXTRACT_ALL_FIVE_R47_CDMETAPOP_JOB_POPULATION_METRICS_FROM_EXISTING_RUNTIME_WORK_WHERE_AVAILABLE",
        "REEXTRACT_R48_AND_R49_J09_DYNAMIC_NEUTRAL_ARMS_FROM_EXISTING_RUNTIME_WORK_WHERE_AVAILABLE",
        "RERUN_ONLY_MISSING_ARMS_IF_REQUIRED_RUNTIME_SUMMARY_ARTIFACTS_ARE_ABSENT",
        "REBUILD_NORMALIZED_CDMETAPOP_POPULATION_RESPONSE_EVIDENCE_WITH_SAME_LIFECYCLE_PHASE_START_END",
        "REBUILD_J09_MATCHED_CAUSAL_EFFECT_WITH_REPAIRED_POPULATION_TRACKING",
        "READJUDICATE_ALL_FIVE_CDMETAPOP_ROWS_WITH_FROZEN_R44_POLICY",
        "PRESERVE_ALL_R43_R49_ORIGINAL_EVIDENCE_AS_HISTORICAL_NEGATIVE_AND_REPAIR_PROVENANCE"
      ],
      "new_thresholds":False,
      "new_replicates_automatically_authorized":False,
      "canonical_replay_authorized":False,
      "canonical_parameter_change_authorized":False,
      "canonical_state_changed":False,
      "majority_vote":False
    }
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    audit_out={"stage":STAGE,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"finding":integrity["finding"],"parent_r49_diagnosis_preserved":diag.get("diagnosis_class"),"canonical_state_changed":False,"next_action":NEXT if status==COMPLETE else "REPAIR_R410_EVIDENCE_INTEGRITY_AUDIT"}
    write_json(root/OUT_REL/"R4_10_MATCHED_CONTROL_PRECISION_AUDIT.json",precision)
    write_json(root/OUT_REL/"R4_10_CDMETAPOP_POPULATION_METRIC_INTEGRITY_AUDIT.json",integrity)
    write_json(root/OUT_REL/"R4_10_PRIMARY_AUTHORITY_CONTEXT.json",context)
    write_json(root/OUT_REL/"R4_10_ALTERNATE_EVIDENCE_CLOSURE_PLAN.json",plan)
    write_json(root/OUT_REL/"R4_10_INTEGRATED_AUDIT.json",audit_out)
    return audit_out,checks

def final_seal(root: Path) -> tuple[dict[str,Any],list[Check]]:
    cfg=load_json(root/CFG_REL)
    parent=load_json(root/R49_SEAL_REL) if (root/R49_SEAL_REL).exists() else {}
    audit=load_json(root/OUT_REL/"R4_10_INTEGRATED_AUDIT.json") if (root/OUT_REL/"R4_10_INTEGRATED_AUDIT.json").exists() else {}
    integ=load_json(root/OUT_REL/"R4_10_CDMETAPOP_POPULATION_METRIC_INTEGRITY_AUDIT.json") if (root/OUT_REL/"R4_10_CDMETAPOP_POPULATION_METRIC_INTEGRITY_AUDIT.json").exists() else {}
    plan=load_json(root/OUT_REL/"R4_10_ALTERNATE_EVIDENCE_CLOSURE_PLAN.json") if (root/OUT_REL/"R4_10_ALTERNATE_EVIDENCE_CLOSURE_PLAN.json").exists() else {}
    precision=load_json(root/OUT_REL/"R4_10_MATCHED_CONTROL_PRECISION_AUDIT.json") if (root/OUT_REL/"R4_10_MATCHED_CONTROL_PRECISION_AUDIT.json").exists() else {}
    checks=[
      Check("parent_r49_sealed",parent.get("status")==R49_SEALED,parent.get("status")),
      Check("r410_audit_complete",audit.get("status")==COMPLETE,audit.get("status")),
      Check("r410_zero_process_failures",audit.get("checks_failed")==0,audit.get("checks_failed")),
      Check("population_metric_selector_collision_confirmed",integ.get("finding")==FINDING,integ.get("finding")),
      Check("r49_uncertain_diagnosis_preserved",precision.get("parent_diagnosis_preserved")==R49_UNCERTAIN,precision.get("parent_diagnosis_preserved")),
      Check("precision_does_not_reclassify",precision.get("precision_reclassification_authorized") is False),
      Check("r411_plan_frozen",plan.get("status")=="R411_PLAN_FROZEN",plan.get("status")),
      Check("no_automatic_more_replicates",plan.get("new_replicates_automatically_authorized") is False),
      Check("canonical_state_unchanged",plan.get("canonical_state_changed") is False),
      Check("canonical_replay_not_authorized",plan.get("canonical_replay_authorized") is False),
      Check("canonical_parameter_change_not_authorized",plan.get("canonical_parameter_change_authorized") is False),
      Check("deep_off",cfg.get("deep_biological_coupling") is False),
      Check("next_action_present",audit.get("next_action")==NEXT,audit.get("next_action")),
    ]
    ok=all(c.passed for c in checks)
    out={"stage":STAGE,"audit":"FINAL_MATCHED_CONTROL_PRECISION_ALTERNATE_EVIDENCE_AND_CDMETAPOP_POPULATION_METRIC_INTEGRITY_AUDIT","status":SEALED if ok else BLOCKED,"verdict":"SEALED" if ok else "BLOCKED","checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"summary":{"finding":integ.get("finding"),"parent_r49_diagnosis_preserved":precision.get("parent_diagnosis_preserved"),"r411_plan_status":plan.get("status"),"canonical_state_changed":False,"canonical_replay_authorized":False,"canonical_parameter_change_authorized":False,"deep_biological_coupling":False,"next_action":audit.get("next_action")},"next_action":audit.get("next_action")}
    write_json(root/SEAL_REL,out)
    return out,checks
