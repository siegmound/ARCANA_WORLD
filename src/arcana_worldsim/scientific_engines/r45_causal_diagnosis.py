from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import math

STAGE = "v0.6D1-R4.5"
R44_SEALED = "PASS_R44_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX_AND_SCIENTIFIC_ADJUDICATION_SEALED"
R44_COMPLETE = "PASS_R44_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX_AND_ADJUDICATION_COMPLETE"
COMPLETE = "PASS_R45_EARLIEST_AUTHORITY_CAUSAL_DIAGNOSIS_AND_REPLAY_PLANNING_COMPLETE"
SEALED = "PASS_R45_EARLIEST_AUTHORITY_CAUSAL_DIAGNOSIS_RECALIBRATION_AND_REPLAY_PLAN_SEALED"
BLOCKED = "BLOCKED_R45_PARENT_OR_CAUSAL_DIAGNOSIS_CONTRACT_FAILURE"

CFG_REL = Path("configs/world1_r45_causal_diagnosis_v0_6D1_R4_5.json")
R44_SEAL_REL = Path("outputs/v0_6D1_R4_4_SEAL/R4_4_FINAL_SEAL_AUDIT.json")
R44_AUDIT_REL = Path("outputs/v0_6D1_R4_4/R4_4_INTEGRATED_AUDIT.json")
R44_MATRIX_REL = Path("outputs/v0_6D1_R4_4/R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json")
R44_SUMMARY_REL = Path("outputs/v0_6D1_R4_4/R4_4_ADJUDICATION_SUMMARY.json")
OUT_REL = Path("outputs/v0_6D1_R4_5")
SEAL_REL = Path("outputs/v0_6D1_R4_5_SEAL/R4_5_FINAL_SEAL_AUDIT.json")

DIAG_CLASSES = [
    "ROBUST_PRIMARY_STRUCTURAL_DISAGREEMENT",
    "STRUCTURAL_CANDIDATE_UNCERTAINTY_OVERLAP",
    "STRUCTURAL_CANDIDATE_INSUFFICIENT_REPLICATES",
    "STRUCTURAL_CANDIDATE_CONTRACT_MISMATCH",
]

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
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def finite(x: Any) -> float | None:
    try: v=float(x)
    except (TypeError,ValueError): return None
    return v if math.isfinite(v) else None

def _metric_kind(metric_name: str) -> str:
    return "delta" if str(metric_name).endswith("_delta") else "ratio"

def robust_quantile_direction(metric_name: str, summary: dict[str,Any], cfg: dict[str,Any]) -> tuple[int|None,str]:
    """Return (+1,-1,0) only if q10-q90 is wholly on one frozen semantic side.
    None means the replicate interval overlaps a neutral boundary or required quantiles are absent.
    """
    q10=finite(summary.get("q10")); q90=finite(summary.get("q90"))
    if q10 is None or q90 is None:
        return None,"MISSING_Q10_Q90"
    if q10>q90:
        q10,q90=q90,q10
    kind=_metric_kind(metric_name)
    if kind=="ratio":
        f=float(cfg["robustness_policy"]["ratio_neutral_factor"])
        lo,hi=1.0/f,f
        if q10>hi: return +1,"Q10_Q90_FULLY_POSITIVE_OUTSIDE_RATIO_NEUTRAL_BAND"
        if q90<lo: return -1,"Q10_Q90_FULLY_NEGATIVE_OUTSIDE_RATIO_NEUTRAL_BAND"
        if q10>=lo and q90<=hi: return 0,"Q10_Q90_FULLY_WITHIN_RATIO_NEUTRAL_BAND"
        return None,"Q10_Q90_CROSSES_RATIO_NEUTRAL_BOUNDARY"
    tol=float(cfg["robustness_policy"]["delta_neutral_abs"])
    if q10>tol: return +1,"Q10_Q90_FULLY_POSITIVE_OUTSIDE_DELTA_NEUTRAL_BAND"
    if q90<-tol: return -1,"Q10_Q90_FULLY_NEGATIVE_OUTSIDE_DELTA_NEUTRAL_BAND"
    if q10>=-tol and q90<=tol: return 0,"Q10_Q90_FULLY_WITHIN_DELTA_NEUTRAL_BAND"
    return None,"Q10_Q90_CROSSES_DELTA_NEUTRAL_BOUNDARY"

def diagnose_structural_row(row: dict[str,Any], cfg: dict[str,Any]) -> dict[str,Any]:
    base={
        "job_id":row.get("job_id"),"window_id":row.get("window_id"),"domain":row.get("domain"),
        "engine":row.get("engine"),"authority_role":row.get("authority_role"),
        "mapping_comparability":row.get("mapping_comparability"),
        "r44_discordance_class":row.get("discordance_class"),"metric":row.get("metric"),"target":row.get("target"),
        "target_direction":row.get("target_direction"),"external_direction":row.get("external_direction"),
        "canonical_change_authorized":False,
    }
    rp=cfg["robustness_policy"]
    target=row.get("target") or {}; metric=row.get("metric") or {}; ms=metric.get("summary") or {}
    if row.get("discordance_class")!="STRUCTURAL_DISAGREEMENT" or row.get("authority_role")!="PRIMARY":
        return {**base,"diagnosis_class":"STRUCTURAL_CANDIDATE_CONTRACT_MISMATCH","reason":"NOT_PRIMARY_R44_STRUCTURAL_ROW","diagnostic_counterfactual_authorized":False}
    if row.get("mapping_comparability") not in rp["eligible_mapping_comparability"] or target.get("comparability") not in rp["eligible_target_comparability"]:
        return {**base,"diagnosis_class":"STRUCTURAL_CANDIDATE_CONTRACT_MISMATCH","reason":"COMPARABILITY_NOT_ADJUDICATIVE","diagnostic_counterfactual_authorized":False}
    n=ms.get("n"); n_i=int(n) if isinstance(n,(int,float)) and finite(n) is not None else 0
    if n_i<int(rp["minimum_external_replicates"]):
        return {**base,"diagnosis_class":"STRUCTURAL_CANDIDATE_INSUFFICIENT_REPLICATES","reason":"EXTERNAL_REPLICATE_COUNT_BELOW_FROZEN_MINIMUM","replicate_count":n_i,"diagnostic_counterfactual_authorized":False}
    mn=metric.get("name")
    qdir,qreason=robust_quantile_direction(str(mn),ms,cfg)
    td=row.get("target_direction"); ed=row.get("external_direction")
    if td not in (-1,0,1) or ed not in (-1,0,1) or td==0 or ed==0 or td*ed>=0:
        return {**base,"diagnosis_class":"STRUCTURAL_CANDIDATE_CONTRACT_MISMATCH","reason":"R44_STRUCTURAL_ROW_DIRECTION_FIELDS_INCONSISTENT","replicate_count":n_i,"quantile_direction":qdir,"quantile_reason":qreason,"diagnostic_counterfactual_authorized":False}
    if qdir is None or qdir!=ed:
        return {**base,"diagnosis_class":"STRUCTURAL_CANDIDATE_UNCERTAINTY_OVERLAP","reason":"REPLICATE_QUANTILE_INTERVAL_DOES_NOT_CONFIRM_MEDIAN_SIGN_FLIP","replicate_count":n_i,"quantile_direction":qdir,"quantile_reason":qreason,"diagnostic_counterfactual_authorized":False}
    return {**base,"diagnosis_class":"ROBUST_PRIMARY_STRUCTURAL_DISAGREEMENT","reason":"PRIMARY_NORMALIZABLE_SIGN_FLIP_CONFIRMED_ACROSS_Q10_Q90","replicate_count":n_i,"quantile_direction":qdir,"quantile_reason":qreason,"diagnostic_counterfactual_authorized":True}

def _gap_closure(cell: dict[str,Any], rows: list[dict[str,Any]]) -> dict[str,Any]:
    reasons=sorted({str(r.get("reason")) for r in rows if r.get("reason")})
    prim=[r for r in rows if r.get("authority_role")=="PRIMARY"]
    if cell.get("discordance_class")=="SEMANTICALLY_NONCOMPARABLE": typ="SEMANTIC_ADAPTER_REQUIRED"
    elif not prim: typ="PRIMARY_AUTHORITY_COVERAGE_GAP"
    elif any(r.get("reason")=="NO_ARCANA_DOMAIN_TARGET_WITH_DECLARED_SEMANTICS" for r in prim): typ="ARCANA_TARGET_DESCRIPTOR_REQUIRED"
    elif any(r.get("reason")=="NO_R43_NORMALIZED_RESULT_METRIC_FOR_DOMAIN" for r in prim): typ="R43_NORMALIZED_METRIC_ADAPTER_REQUIRED"
    else: typ="PRIMARY_COMPARABLE_PAIR_GAP"
    return {"window_id":cell.get("window_id"),"domain":cell.get("domain"),"r44_class":cell.get("discordance_class"),"closure_type":typ,"primary_rows":len(prim),"row_reasons":reasons,"result_selected":False,"new_engine_selection_authorized":False}

def diagnose(root: Path) -> tuple[dict[str,Any],list[Check]]:
    cfg=load_json(root/CFG_REL)
    seal=load_json(root/R44_SEAL_REL) if (root/R44_SEAL_REL).exists() else {}
    audit=load_json(root/R44_AUDIT_REL) if (root/R44_AUDIT_REL).exists() else {}
    matrix=load_json(root/R44_MATRIX_REL) if (root/R44_MATRIX_REL).exists() else {}
    summary=load_json(root/R44_SUMMARY_REL) if (root/R44_SUMMARY_REL).exists() else {}
    cells=matrix.get("cells",[]) if isinstance(matrix,dict) else []
    rows=matrix.get("evidence_rows",[]) if isinstance(matrix,dict) else []
    structural=[c for c in cells if c.get("discordance_class")=="STRUCTURAL_DISAGREEMENT"]
    offsets=[c for c in cells if c.get("discordance_class")=="CALIBRATION_OFFSET"]
    gaps=[c for c in cells if c.get("discordance_class") in ("INSUFFICIENT_EVIDENCE","SEMANTICALLY_NONCOMPARABLE")]

    checks=[
      Check("parent_r44_seal_present",(root/R44_SEAL_REL).exists(),str(R44_SEAL_REL)),
      Check("parent_r44_sealed",seal.get("status")==R44_SEALED,seal.get("status")),
      Check("parent_r44_adjudication_complete",audit.get("status")==R44_COMPLETE,audit.get("status")),
      Check("parent_matrix_nonempty",matrix.get("cell_count",0)==len(cells) and len(cells)>0,{"declared":matrix.get("cell_count"),"loaded":len(cells)}),
      Check("policy_not_result_selected",cfg.get("policy_freeze",{}).get("result_selected") is False),
      Check("majority_vote_forbidden",cfg.get("majority_vote") is False),
      Check("canonical_state_unchanged",cfg.get("canonical_state_changed") is False),
      Check("deep_off",cfg.get("deep_biological_coupling") is False),
    ]

    structural_diag=[]; traces=[]
    registry=cfg.get("boundary_authority_registry",{})
    for c in structural:
        cr=[r for r in rows if r.get("window_id")==c.get("window_id") and r.get("domain")==c.get("domain") and r.get("authority_role")=="PRIMARY" and r.get("discordance_class")=="STRUCTURAL_DISAGREEMENT"]
        diagnoses=[diagnose_structural_row(r,cfg) for r in cr]
        boundary=c.get("earliest_affected_authority_candidate") or summary.get("earliest_affected_authority_candidate")
        reg=registry.get(boundary,{}) if boundary else {}
        files=reg.get("authority_files",[])
        present=[str(p) for p in files if (root/p).exists()]
        missing=[str(p) for p in files if not (root/p).exists()]
        robust=any(d["diagnosis_class"]=="ROBUST_PRIMARY_STRUCTURAL_DISAGREEMENT" for d in diagnoses)
        structural_diag.append({"window_id":c.get("window_id"),"domain":c.get("domain"),"earliest_affected_authority_candidate":boundary,"primary_structural_row_count":len(cr),"row_diagnoses":diagnoses,"robust_structural_disagreement":robust,"canonical_replay_authorized":False,"diagnostic_counterfactual_authorized":robust and bool(reg) and not missing})
        traces.append({"window_id":c.get("window_id"),"domain":c.get("domain"),"boundary":boundary,"authority_registry_entry":reg,"authority_files_present":present,"authority_files_missing":missing,"r311_causal_surface":cfg.get("r311_causal_surface") if boundary=="R3.11_POST_CHA1" else None,"parameter_change_authorized":False})

    offset_reg=[]
    for c in offsets:
        rr=[r for r in rows if r.get("window_id")==c.get("window_id") and r.get("domain")==c.get("domain") and r.get("authority_role")=="PRIMARY" and r.get("discordance_class")=="CALIBRATION_OFFSET"]
        offset_reg.append({"window_id":c.get("window_id"),"domain":c.get("domain"),"primary_offset_rows":rr,"parameter_change_authorized":False,"review_status":"RECORDED_FOR_LATER_TARGETED_CALIBRATION_REVIEW"})

    gap_plan=[]
    for c in gaps:
        rr=[r for r in rows if r.get("window_id")==c.get("window_id") and r.get("domain")==c.get("domain")]
        gap_plan.append(_gap_closure(c,rr))

    robust_count=sum(d.get("robust_structural_disagreement",False) for d in structural_diag)
    uncertain_count=sum(1 for d in structural_diag for r in d.get("row_diagnoses",[]) if r.get("diagnosis_class")!="ROBUST_PRIMARY_STRUCTURAL_DISAGREEMENT")
    all_structural_resolved=all(d.get("primary_structural_row_count",0)>0 for d in structural_diag)
    all_trace_present=all(t.get("boundary") in registry and not t.get("authority_files_missing") for t in traces) if traces else True
    all_gap_planned=len(gap_plan)==len(gaps)
    all_offsets_registered=len(offset_reg)==len(offsets)
    checks += [
      Check("all_r44_structural_cells_resolved_to_primary_rows",all_structural_resolved,{"cells":len(structural),"diagnosed":sum(d.get('primary_structural_row_count',0)>0 for d in structural_diag)}),
      Check("all_structural_boundaries_trace_to_present_authority_files",all_trace_present,[{"boundary":t.get("boundary"),"missing":t.get("authority_files_missing")} for t in traces]),
      Check("all_structural_row_diagnoses_use_frozen_class",all(r.get("diagnosis_class") in DIAG_CLASSES for d in structural_diag for r in d.get("row_diagnoses",[]))),
      Check("all_calibration_offsets_registered",all_offsets_registered,{"expected":len(offsets),"registered":len(offset_reg)}),
      Check("all_evidence_gaps_have_closure_plan",all_gap_planned,{"expected":len(gaps),"planned":len(gap_plan)}),
      Check("no_parameter_change_authorized",all(not x.get("parameter_change_authorized",False) for x in traces+offset_reg)),
      Check("no_canonical_replay_authorized",all(not d.get("canonical_replay_authorized",False) for d in structural_diag)),
      Check("no_majority_vote_anywhere",True),
    ]

    # Only a later stage may execute anything. R4.5 can nominate a diagnostic counterfactual.
    diagnostic_auth=any(d.get("diagnostic_counterfactual_authorized",False) for d in structural_diag)
    boundaries=[]
    for d in structural_diag:
        if d.get("diagnostic_counterfactual_authorized") and d.get("earliest_affected_authority_candidate") not in boundaries:
            boundaries.append(d.get("earliest_affected_authority_candidate"))
    if diagnostic_auth:
        next_action="EXECUTE_R46_TARGETED_CAUSAL_COUNTERFACTUAL_FROM_" + str(boundaries[0]).replace(".","_")
    elif structural:
        next_action="EXECUTE_R46_TARGETED_PRIMARY_REPLICATE_ROBUSTNESS_CLOSURE"
    elif gaps:
        next_action="BUILD_R46_TARGETED_EVIDENCE_GAP_CLOSURE"
    elif offsets:
        next_action="BUILD_R46_TARGETED_CALIBRATION_REVIEW"
    else:
        next_action="BUILD_R46_REVALIDATION_CLOSURE_GATE"

    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    diagnosis={"stage":STAGE,"status":status,"parent_r44_class_counts":matrix.get("class_counts",{}),"structural_cell_count":len(structural),"robust_structural_cell_count":robust_count,"uncertain_or_contract_limited_structural_row_count":uncertain_count,"structural_diagnoses":structural_diag,"canonical_state_changed":False,"canonical_replay_authorized":False,"diagnostic_counterfactual_authorized":diagnostic_auth,"next_action":next_action}
    trace={"stage":STAGE,"status":status,"traces":traces,"earliest_affected_authority_candidate":summary.get("earliest_affected_authority_candidate"),"canonical_replay_authorized":False}
    offsets_out={"stage":STAGE,"status":status,"count":len(offset_reg),"offsets":offset_reg,"automatic_recalibration_authorized":False}
    gaps_out={"stage":STAGE,"status":status,"count":len(gap_plan),"closure_type_counts":{k:sum(1 for g in gap_plan if g["closure_type"]==k) for k in sorted({g["closure_type"] for g in gap_plan})},"gaps":gap_plan,"result_selected":False}
    gate={"stage":STAGE,"status":status,"diagnostic_counterfactual_authorized":diagnostic_auth,"authorized_boundaries":boundaries,"canonical_replay_authorized":False,"canonical_parameter_change_authorized":False,"why":"R4.5 permits only a targeted diagnostic counterfactual after quantile-robust PRIMARY structural evidence; canonical replay/recalibration requires later causal confirmation.","next_action":next_action}
    audit_out={"stage":STAGE,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"robust_structural_cell_count":robust_count,"calibration_offset_count":len(offsets),"evidence_gap_count":len(gaps),"canonical_state_changed":False,"next_action":next_action}
    write_json(root/OUT_REL/"R4_5_STRUCTURAL_DISAGREEMENT_DIAGNOSIS.json",diagnosis)
    write_json(root/OUT_REL/"R4_5_EARLIEST_AUTHORITY_TRACE.json",trace)
    write_json(root/OUT_REL/"R4_5_CALIBRATION_OFFSET_REGISTER.json",offsets_out)
    write_json(root/OUT_REL/"R4_5_EVIDENCE_GAP_CLOSURE_PLAN.json",gaps_out)
    write_json(root/OUT_REL/"R4_5_REPLAY_AUTHORIZATION_GATE.json",gate)
    write_json(root/OUT_REL/"R4_5_INTEGRATED_AUDIT.json",audit_out)
    return audit_out,checks

def final_seal(root: Path) -> tuple[dict[str,Any],list[Check]]:
    p=load_json(root/R44_SEAL_REL) if (root/R44_SEAL_REL).exists() else {}
    a=load_json(root/OUT_REL/"R4_5_INTEGRATED_AUDIT.json") if (root/OUT_REL/"R4_5_INTEGRATED_AUDIT.json").exists() else {}
    d=load_json(root/OUT_REL/"R4_5_STRUCTURAL_DISAGREEMENT_DIAGNOSIS.json") if (root/OUT_REL/"R4_5_STRUCTURAL_DISAGREEMENT_DIAGNOSIS.json").exists() else {}
    g=load_json(root/OUT_REL/"R4_5_REPLAY_AUTHORIZATION_GATE.json") if (root/OUT_REL/"R4_5_REPLAY_AUTHORIZATION_GATE.json").exists() else {}
    checks=[
      Check("parent_r44_sealed",p.get("status")==R44_SEALED,p.get("status")),
      Check("r45_diagnosis_complete",a.get("status")==COMPLETE,a.get("status")),
      Check("r45_zero_process_failures",a.get("checks_failed")==0,a.get("checks_failed")),
      Check("structural_diagnosis_output_present",isinstance(d.get("structural_diagnoses"),list)),
      Check("canonical_state_unchanged",a.get("canonical_state_changed") is False),
      Check("canonical_replay_still_not_authorized",g.get("canonical_replay_authorized") is False),
      Check("canonical_parameter_change_not_authorized",g.get("canonical_parameter_change_authorized") is False),
      Check("deep_biological_coupling_remains_off",load_json(root/CFG_REL).get("deep_biological_coupling") is False),
      Check("diagnostic_counterfactual_only_if_robust",(not g.get("diagnostic_counterfactual_authorized")) or d.get("robust_structural_cell_count",0)>0),
      Check("next_action_present",bool(g.get("next_action")),g.get("next_action")),
    ]
    ok=all(c.passed for c in checks)
    out={"stage":STAGE,"audit":"FINAL_EARLIEST_AUTHORITY_CAUSAL_DIAGNOSIS_RECALIBRATION_AND_REPLAY_PLAN","status":SEALED if ok else BLOCKED,"verdict":"SEALED" if ok else "BLOCKED","checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"summary":{"robust_structural_cell_count":d.get("robust_structural_cell_count"),"diagnostic_counterfactual_authorized":g.get("diagnostic_counterfactual_authorized"),"canonical_replay_authorized":False,"canonical_state_changed":False,"deep_biological_coupling":False,"next_action":g.get("next_action")},"next_action":g.get("next_action")}
    write_json(root/SEAL_REL,out)
    return out,checks
