from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import copy, json, math

from arcana_worldsim.scientific_engines import r44_discordance_adjudication as r44

STAGE="v0.6D1-R4.18"
PARENT_SEALED="PASS_R417_ARCANA_TARGET_EXTRACTOR_IMPLEMENTATION_AND_RECOVERED_METRIC_PROMOTION_CLOSURE_SEALED"
COMPLETE="PASS_R418_TARGET_MATERIALIZATION_VALIDATION_PARTIAL_READJUDICATION_AND_P2_BACKLOG_FREEZE_COMPLETE"
SEALED="PASS_R418_TARGET_MATERIALIZATION_VALIDATION_PARTIAL_READJUDICATION_AND_P2_BACKLOG_FREEZE_SEALED"
BLOCKED="BLOCKED_R418_PARENT_TARGET_VALIDATION_READJUDICATION_OR_BACKLOG_FREEZE_FAILURE"
NEXT_STRUCTURAL="BUILD_R419_POST_R418_STRUCTURAL_CAUSAL_DIAGNOSIS"
NEXT_BACKLOG="BUILD_R419_P2_ADAPTER_ENHANCEMENT_AND_TARGET_DESIGN_BACKLOG_EXECUTION_PLAN"
CFG=Path("configs/world1_r418_target_validation_partial_readjudication_v0_6D1_R4_18.json")
PSEAL=Path("outputs/v0_6D1_R4_17_SEAL/R4_17_FINAL_SEAL_AUDIT.json")
PTARGET=Path("outputs/v0_6D1_R4_17/R4_17_ARCANA_TARGET_EXTRACTOR_RESULTS.json")
PMETRIC=Path("outputs/v0_6D1_R4_17/R4_17_RECOVERED_METRIC_PROMOTION_CLOSURE.json")
PPLAN=Path("outputs/v0_6D1_R4_17/R4_17_R418_CLOSURE_PLAN.json")
P413=Path("outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json")
R44CFG=Path("configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json")
R43CFG=Path("configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json")
R42JOBS=Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")
R416PROT=Path("outputs/v0_6D1_R4_16/R4_16_ARCANA_TARGET_SEMANTIC_PROTOCOL_REGISTRY.json")
R414CENSUS=Path("outputs/v0_6D1_R4_14/R4_14_EVIDENCE_GAP_CENSUS.json")
R415REC=Path("outputs/v0_6D1_R4_15/R4_15_RETAINED_RUNTIME_METRIC_RECOVERY.json")
OUT=Path("outputs/v0_6D1_R4_18")
SEAL=Path("outputs/v0_6D1_R4_18_SEAL/R4_18_FINAL_SEAL_AUDIT.json")
CLASSES=["CONCORDANT","CALIBRATION_OFFSET","STRUCTURAL_DISAGREEMENT","SEMANTICALLY_NONCOMPARABLE","INSUFFICIENT_EVIDENCE"]

@dataclass(frozen=True)
class Check:
    name:str; passed:bool; detail:Any=None
    def d(self): return {"name":self.name,"pass":bool(self.passed),"detail":self.detail}

def load(p:Path)->Any: return json.loads(p.read_text(encoding="utf-8-sig"))
def write(p:Path,o:Any):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
def finite(x:Any)->float|None:
    try:
        y=float(x); return y if math.isfinite(y) else None
    except Exception:return None

def _metric_name(row:dict[str,Any])->str|None:
    m=row.get("metric")
    return str(m.get("name")) if isinstance(m,dict) and m.get("name") else None

def _target_scalar(materialized:dict[str,Any], metric_name:str)->tuple[str,float]|None:
    v=materialized.get("value")
    is_delta=metric_name.endswith("_delta")
    kind="delta" if is_delta else "ratio"
    if isinstance(v,dict):
        x=finite(v.get("delta" if is_delta else "ratio"))
    else:
        x=finite(v)
    if x is None:return None
    if kind=="ratio" and x<=0:return None
    return kind,x

def _protocol_record(protocols:dict[str,Any],w:str,d:str)->dict[str,Any]|None:
    for r in protocols.get("records") or []:
        if r.get("window_id")==w and r.get("domain")==d:return r
    return None

def _provenance_is_safe(mat:dict[str,Any])->bool:
    prov=mat.get("provenance")
    txt=json.dumps(prov,sort_keys=True,ensure_ascii=False).replace('\\','/').lower()
    extractor=str(mat.get("extractor") or "")
    if extractor=="R43_PRE_RESULT_CANONICAL_WINDOW_DESCRIPTOR_BRIDGE":
        h=mat.get("hash_check") or {}
        return h.get("declared_hash_match") is True and h.get("actual_artifact_present") is True and h.get("actual_sha256_match") is True
    # Explicit canonical target descriptors must not derive their value from R4 external-result namespaces.
    return "/v0_6d1_r4_" not in txt and "outputs/v0_6d1_r4_" not in txt

def _validate_candidate(root:Path,cfg:dict[str,Any],cfg44:dict[str,Any],protocols:dict[str,Any],parent_rows:list[dict[str,Any]],rec:dict[str,Any])->dict[str,Any]:
    w=str(rec.get("window_id") or ""); d=str(rec.get("domain") or "")
    mat=rec.get("materialized_target") or {}; cand=str(rec.get("candidate_comparability") or "")
    promoted=(cfg.get("candidate_comparability_promotion") or {}).get(cand)
    prot=_protocol_record(protocols,w,d)
    rows=[r for r in parent_rows if r.get("window_id")==w and r.get("domain")==d and r.get("authority_role")=="PRIMARY"]
    eligible=[]; row_checks=[]
    for r in rows:
        mn=_metric_name(r); allowed=((cfg44.get("domain_metric_candidates") or {}).get(str(r.get("engine")),{}) or {}).get(d,[])
        scalar=_target_scalar(mat,mn) if mn else None
        ok=bool(mn and mn in allowed and r.get("mapping_comparability") in ("DIRECT","NORMALIZABLE") and isinstance((r.get("metric") or {}).get("summary"),dict) and scalar)
        row_checks.append({"job_id":r.get("job_id"),"engine":r.get("engine"),"metric_name":mn,"mapping_comparability":r.get("mapping_comparability"),"metric_authorized_for_domain":bool(mn and mn in allowed),"target_scalar_available":scalar is not None,"eligible":ok})
        if ok: eligible.append((r,scalar))
    temporal=mat.get("temporal_basis")
    temporal_ok=bool(temporal) and (not isinstance(temporal,dict) or not temporal.get("window_id") or temporal.get("window_id")==w)
    strict_fields=all(mat.get(k) not in (None,"") for k in ["unit_basis","spatial_population_basis","transform","provenance","extractor"])
    protocol_ok=bool(prot and isinstance(prot.get("protocol"),dict) and prot.get("external_result_used_to_define_target") is False)
    provenance_ok=_provenance_is_safe(mat)
    comp_ok=promoted in ("DIRECT","NORMALIZABLE")
    valid=all([comp_ok,strict_fields,temporal_ok,protocol_ok,provenance_ok,bool(eligible)])
    reason="VALIDATED_PRE_RESULT_TARGET_AND_PRIMARY_METRIC_SEMANTIC_PAIR" if valid else "TARGET_OR_PRIMARY_METRIC_SEMANTIC_VALIDATION_FAILED"
    return {
        "window_id":w,"domain":d,"candidate_comparability":cand,"validated_comparability":promoted if valid else None,
        "validation_status":"VALIDATED_FOR_PARTIAL_READJUDICATION" if valid else "REJECTED_REMAINS_NONADJUDICATIVE",
        "reason":reason,"source":rec.get("selected_source"),"materialized_target":mat,"protocol_record_present":prot is not None,
        "strict_target_fields_present":strict_fields,"temporal_basis_matches_window":temporal_ok,"provenance_integrity_pass":provenance_ok,
        "primary_rows":row_checks,"eligible_primary_row_count":len(eligible),"result_selected_validation":False,
    }

def _validated_target(rec:dict[str,Any],metric_name:str,validated_comp:str)->dict[str,Any]|None:
    scalar=_target_scalar(rec.get("materialized_target") or {},metric_name)
    if not scalar:return None
    kind,val=scalar
    mat=rec.get("materialized_target") or {}
    return {"kind":kind,"value":val,"comparability":validated_comp,"source":"R4.18_VALIDATED_R4.17_MATERIALIZED_CANONICAL_TARGET","unit_basis":mat.get("unit_basis"),"temporal_basis":mat.get("temporal_basis"),"spatial_population_basis":mat.get("spatial_population_basis"),"transform":mat.get("transform"),"provenance":mat.get("provenance")}

def _recompute_cells(root:Path,rows:list[dict[str,Any]])->list[dict[str,Any]]:
    cfg44=load(root/R44CFG); r43cfg=load(root/R43CFG); jobs={x["job_id"]:x for x in (load(root/R42JOBS).get("jobs") or [])}
    cells=[]
    for wid,domains in (r43cfg.get("window_domain_scope") or {}).items():
        for domain in domains:
            rr=[r for r in rows if r.get("window_id")==wid and r.get("domain")==domain]
            prim=[r for r in rr if r.get("authority_role")=="PRIMARY"]; sec=[r for r in rr if r.get("authority_role")=="SECONDARY"]
            adjud=[r for r in prim if r.get("mapping_comparability") in ("NORMALIZABLE","DIRECT") and (r.get("target") or {}).get("comparability") in ("NORMALIZABLE","DIRECT") and r.get("discordance_class") in ("CONCORDANT","CALIBRATION_OFFSET","STRUCTURAL_DISAGREEMENT")]
            if any(r.get("discordance_class")=="STRUCTURAL_DISAGREEMENT" for r in adjud): cls="STRUCTURAL_DISAGREEMENT"; reason="AT_LEAST_ONE_PRIMARY_ADJUDICATIVE_STRUCTURAL_DISAGREEMENT"
            elif any(r.get("discordance_class")=="CALIBRATION_OFFSET" for r in adjud): cls="CALIBRATION_OFFSET"; reason="PRIMARY_ADJUDICATIVE_CALIBRATION_OFFSET_WITH_NO_STRUCTURAL_DISAGREEMENT"
            elif any(r.get("discordance_class")=="CONCORDANT" for r in adjud): cls="CONCORDANT"; reason="PRIMARY_ADJUDICATIVE_CONCORDANCE_WITH_NO_HIGHER_SEVERITY_PRIMARY_FINDING"
            elif prim and all(r.get("discordance_class")=="SEMANTICALLY_NONCOMPARABLE" for r in prim): cls="SEMANTICALLY_NONCOMPARABLE"; reason="ALL_PRIMARY_EVIDENCE_SEMANTICALLY_NONCOMPARABLE"
            else: cls="INSUFFICIENT_EVIDENCE"; reason="NO_PRIMARY_NORMALIZABLE_RESULT_TARGET_PAIR"
            boundaries=sorted({jobs.get(r.get("job_id"),{}).get("earliest_replay_boundary") for r in adjud if r.get("discordance_class")=="STRUCTURAL_DISAGREEMENT" and jobs.get(r.get("job_id"),{}).get("earliest_replay_boundary")},key=lambda x:(cfg44.get("replay_boundary_order") or []).index(x) if x in (cfg44.get("replay_boundary_order") or []) else 999)
            cells.append({"window_id":wid,"domain":domain,"discordance_class":cls,"reason":reason,"primary_evidence_rows":len(prim),"secondary_context_rows":len(sec),"primary_adjudicative_rows":len(adjud),"earliest_affected_authority_candidate":boundaries[0] if boundaries else None,"canonical_change_authorized":False,"majority_vote":False})
    return cells

def _freeze_p2(root:Path)->dict[str,Any]:
    census=load(root/R414CENSUS) if (root/R414CENSUS).exists() else {}; rec=load(root/R415REC) if (root/R415REC).exists() else {}; metric=load(root/PMETRIC) if (root/PMETRIC).exists() else {}
    items=[]
    for g in census.get("gaps") or []:
        if g.get("closure_priority")=="P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION":
            items.append({"source_stage":"R4.14","window_id":g.get("window_id"),"domain":g.get("domain"),"engine":None,"reason":g.get("root_cause"),"closure_action":g.get("closure_action")})
    for r in rec.get("records") or []:
        if r.get("resolution_status")=="P0_CANDIDATE_EXHAUSTED_RECLASSIFIED_TO_P2":
            items.append({"source_stage":"R4.15-R1","window_id":r.get("window_id"),"domain":r.get("domain"),"engine":r.get("authorized_recovery_engine"),"reason":r.get("reclassification_reason"),"closure_action":"EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION"})
    for r in metric.get("records") or []:
        if r.get("next_priority")=="P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION":
            items.append({"source_stage":"R4.17","window_id":r.get("window_id"),"domain":r.get("domain"),"engine":r.get("engine"),"reason":r.get("reason"),"closure_action":r.get("closure_status")})
    return {"stage":STAGE,"status":"R418_P2_BACKLOG_FROZEN","cell_count":len(items),"records":items,"execution_authorized":False,"r42_registry_mutation_authorized":False}

def build(root:Path)->dict[str,Any]:
    cfg=load(root/CFG) if (root/CFG).exists() else {}; seal=load(root/PSEAL) if (root/PSEAL).exists() else {}; targ=load(root/PTARGET) if (root/PTARGET).exists() else {}; plan=load(root/PPLAN) if (root/PPLAN).exists() else {}; parent=load(root/P413) if (root/P413).exists() else {}; cfg44=load(root/R44CFG) if (root/R44CFG).exists() else {}; prot=load(root/R416PROT) if (root/R416PROT).exists() else {}
    ps=seal.get("summary") or {}; exp=cfg.get("expected_parent_counts") or {}; parent_rows=list(parent.get("evidence_rows") or []); parent_cells=list(parent.get("cells") or [])
    candidates=[r for r in targ.get("records") or [] if r.get("materialized_target") is not None and r.get("candidate_comparability") in ("DIRECT_CANDIDATE","NORMALIZABLE_CANDIDATE")]
    proxies=[r for r in targ.get("records") or [] if r.get("materialized_target") is not None and r.get("candidate_comparability")=="PROXY_ONLY"]
    checks=[
        Check("parent_r417_seal_present",(root/PSEAL).exists(),str(PSEAL)),Check("parent_r417_sealed",seal.get("status")==PARENT_SEALED,seal.get("status")),Check("parent_next_action_matches_r418",seal.get("next_action")=="BUILD_R418_TARGET_MATERIALIZATION_VALIDATION_PARTIAL_READJUDICATION_AND_P2_BACKLOG_FREEZE",seal.get("next_action")),
        Check("parent_exact_three_materialized_targets",ps.get("p1_target_materialized_cell_count")==exp.get("p1_target_materialized_cell_count"),ps.get("p1_target_materialized_cell_count")),Check("parent_exact_one_validation_candidate",ps.get("r418_target_comparability_validation_candidate_count")==exp.get("r418_target_comparability_validation_candidate_count") and len(candidates)==1,{"seal":ps.get("r418_target_comparability_validation_candidate_count"),"records":len(candidates)}),Check("parent_exact_two_proxy_materializations",ps.get("p1_proxy_only_materialized_count")==exp.get("p1_proxy_only_materialized_count") and len(proxies)==2,{"seal":ps.get("p1_proxy_only_materialized_count"),"records":len(proxies)}),Check("parent_exhausted_and_design_gap_counts",ps.get("p1_source_candidate_exhausted_count")==exp.get("p1_source_candidate_exhausted_count") and ps.get("p1_target_design_gap_count")==exp.get("p1_target_design_gap_count"),{"exhausted":ps.get("p1_source_candidate_exhausted_count"),"design_gap":ps.get("p1_target_design_gap_count")}),Check("parent_p2_p3_backlog_counts",ps.get("p2_backlog_cell_count")==exp.get("p2_backlog_cell_count") and ps.get("p3_backlog_cell_count")==exp.get("p3_backlog_cell_count"),{"p2":ps.get("p2_backlog_cell_count"),"p3":ps.get("p3_backlog_cell_count")}),Check("parent_r418_plan_frozen",plan.get("status")=="R417_TARGET_EXTRACTION_AND_PROMOTION_CLOSURE_FROZEN",plan.get("status")),
        Check("parent_r413_matrix_exact_75_cells",parent.get("cell_count")==75 and len(parent_cells)==75,{"declared":parent.get("cell_count"),"loaded":len(parent_cells)}),Check("policy_frozen",cfg.get("policy_freeze")=="FROZEN_PRE_TARGET_VALIDATION_AND_PARTIAL_READJUDICATION",cfg.get("policy_freeze")),Check("engine_execution_forbidden",cfg.get("engine_execution_performed") is False),Check("canonical_state_unchanged",cfg.get("canonical_state_changed") is False),Check("canonical_replay_not_authorized",cfg.get("canonical_replay_authorized") is False),Check("canonical_parameter_change_not_authorized",cfg.get("canonical_parameter_change_authorized") is False),Check("deep_off",cfg.get("deep_biological_coupling") is False),Check("majority_vote_forbidden",cfg.get("majority_vote") is False),Check("proxy_materializations_remain_context_only",all(r.get("adjudicative_target_authorized") is False for r in proxies)),
    ]
    if any(not c.passed for c in checks):
        out={"stage":STAGE,"status":BLOCKED,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.d() for c in checks],"canonical_state_changed":False}; write(root/OUT/"R4_18_INTEGRATED_AUDIT.json",out); return out
    validations=[_validate_candidate(root,cfg,cfg44,prot,parent_rows,r) for r in candidates]
    validated=[v for v in validations if v.get("validation_status")=="VALIDATED_FOR_PARTIAL_READJUDICATION"]
    revised=copy.deepcopy(parent_rows); changed_row_ids=[]
    for v in validated:
        w=v["window_id"]; d=v["domain"]; comp=v["validated_comparability"]
        for i,r in enumerate(revised):
            if r.get("window_id")!=w or r.get("domain")!=d or r.get("authority_role")!="PRIMARY" or r.get("mapping_comparability") not in ("DIRECT","NORMALIZABLE"): continue
            mn=_metric_name(r); ms=(r.get("metric") or {}).get("summary") if isinstance(r.get("metric"),dict) else None
            if not mn or not isinstance(ms,dict): continue
            allowed=((cfg44.get("domain_metric_candidates") or {}).get(str(r.get("engine")),{}) or {}).get(d,[])
            if mn not in allowed: continue
            tr=_validated_target(next(x for x in candidates if x.get("window_id")==w and x.get("domain")==d),mn,comp)
            if not tr: continue
            nr=copy.deepcopy(r); nr["stage"]=STAGE; nr["parent_stage"]=r.get("stage"); nr["parent_discordance_class"]=r.get("discordance_class"); nr["target"]=tr
            res=r44.classify_pair(tr,mn,ms,str(r.get("mapping_comparability")),cfg44)
            for k in ["discordance_class","reason","combined_comparability","target_direction","external_direction","target_value","external_median","external_q10","external_q90","magnitude_comparison_used"]: nr.pop(k,None)
            nr.update(res); nr["r418_partial_readjudication"]={"status":"APPLIED","target_validation":"VALIDATED_FOR_PARTIAL_READJUDICATION","result_selected":False,"canonical_change":False}
            revised[i]=nr; changed_row_ids.append({"job_id":nr.get("job_id"),"window_id":w,"domain":d,"new_class":nr.get("discordance_class")})
    cells=_recompute_cells(root,revised); counts={c:sum(1 for x in cells if x.get("discordance_class")==c) for c in CLASSES}
    old_by={(x.get("window_id"),x.get("domain")):x for x in parent_cells}; new_by={(x.get("window_id"),x.get("domain")):x for x in cells}; changed=[]
    for k,n in new_by.items():
        o=old_by.get(k,{})
        if o.get("discordance_class")!=n.get("discordance_class"): changed.append({"window_id":k[0],"domain":k[1],"old_class":o.get("discordance_class"),"new_class":n.get("discordance_class")})
    allowed_cells={(v["window_id"],v["domain"]) for v in validated}; illegal=[x for x in changed if (x["window_id"],x["domain"]) not in allowed_cells]
    p2=_freeze_p2(root); structural=counts.get("STRUCTURAL_DISAGREEMENT",0); next_action=NEXT_STRUCTURAL if structural else NEXT_BACKLOG
    checks += [
        Check("exact_one_candidate_receives_terminal_validation",len(validations)==1,len(validations)),Check("candidate_validation_is_result_independent",all(v.get("result_selected_validation") is False for v in validations)),Check("validated_candidate_count_at_most_one",len(validated)<=1,len(validated)),Check("all_proxy_targets_remain_nonadjudicative",all(r.get("candidate_comparability")=="PROXY_ONLY" and r.get("adjudicative_target_authorized") is False for r in proxies)),Check("partial_readjudication_only_on_validated_candidate_cells",not illegal,illegal),Check("readjudicated_rows_are_primary_only",all(any(r.get("job_id")==x["job_id"] and r.get("authority_role")=="PRIMARY" for r in revised) for x in changed_row_ids)),Check("revised_matrix_exact_75_cells",len(cells)==75,len(cells)),Check("five_class_accounting_complete",sum(counts.values())==75,counts),Check("no_secondary_only_promotion",all(not (x.get("discordance_class") in ("CONCORDANT","CALIBRATION_OFFSET","STRUCTURAL_DISAGREEMENT") and x.get("primary_adjudicative_rows")==0) for x in cells)),Check("p2_backlog_exact_six_and_frozen",p2.get("cell_count")==6,p2.get("cell_count")),Check("p2_execution_not_authorized",p2.get("execution_authorized") is False),Check("parent_nonvalidated_cells_semantically_preserved",not illegal),Check("engine_execution_not_performed",cfg.get("engine_execution_performed") is False),Check("canonical_state_still_unchanged",cfg.get("canonical_state_changed") is False),Check("canonical_replay_still_not_authorized",cfg.get("canonical_replay_authorized") is False),Check("canonical_parameter_change_still_not_authorized",cfg.get("canonical_parameter_change_authorized") is False),
    ]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    validation_out={"stage":STAGE,"status":status,"candidate_count":len(validations),"validated_count":len(validated),"rejected_count":len(validations)-len(validated),"proxy_context_only_count":len(proxies),"records":validations,"readjudication_authorized_only_for_validated_candidates":True}
    matrix={"stage":STAGE,"status":status,"cell_count":len(cells),"class_counts":counts,"cells":cells,"evidence_rows":revised,"parent_matrix":str(P413),"parent_matrix_preserved":True,"partial_readjudication_cell_count":len(allowed_cells),"engine_execution_performed":False,"canonical_state_changed":False,"scientific_agreement_claimed":False,"next_action":next_action}
    delta={"stage":STAGE,"status":status,"validated_candidate_cell_count":len(validated),"readjudicated_primary_row_count":len(changed_row_ids),"changed_cell_count":len(changed),"changed_cells":changed,"parent_class_counts":parent.get("class_counts"),"new_class_counts":counts,"canonical_change_authorized":False,"next_action":next_action}
    p2["status"]=status if status==COMPLETE else BLOCKED; p2["next_action"]=next_action
    out={"stage":STAGE,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.d() for c in checks],"target_validation_candidate_count":len(validations),"target_validated_for_partial_readjudication_count":len(validated),"proxy_target_context_only_count":len(proxies),"partial_readjudication_changed_cell_count":len(changed),"class_counts_after_partial_readjudication":counts,"structural_disagreement_count_after_partial_readjudication":structural,"p2_backlog_cell_count":p2.get("cell_count"),"p3_backlog_cell_count":ps.get("p3_backlog_cell_count"),"engine_execution_performed":False,"canonical_state_changed":False,"next_action":next_action}
    write(root/OUT/"R4_18_TARGET_MATERIALIZATION_VALIDATION.json",validation_out); write(root/OUT/"R4_18_PARTIAL_READJUDICATED_MATRIX.json",matrix); write(root/OUT/"R4_18_READJUDICATION_DELTA.json",delta); write(root/OUT/"R4_18_P2_BACKLOG_FREEZE.json",p2); write(root/OUT/"R4_18_INTEGRATED_AUDIT.json",out); return out

def final_seal(root:Path)->dict[str,Any]:
    parent=load(root/PSEAL) if (root/PSEAL).exists() else {}; audit=load(root/OUT/"R4_18_INTEGRATED_AUDIT.json") if (root/OUT/"R4_18_INTEGRATED_AUDIT.json").exists() else {}; val=load(root/OUT/"R4_18_TARGET_MATERIALIZATION_VALIDATION.json") if (root/OUT/"R4_18_TARGET_MATERIALIZATION_VALIDATION.json").exists() else {}; mat=load(root/OUT/"R4_18_PARTIAL_READJUDICATED_MATRIX.json") if (root/OUT/"R4_18_PARTIAL_READJUDICATED_MATRIX.json").exists() else {}; p2=load(root/OUT/"R4_18_P2_BACKLOG_FREEZE.json") if (root/OUT/"R4_18_P2_BACKLOG_FREEZE.json").exists() else {}
    checks=[Check("parent_r417_sealed",parent.get("status")==PARENT_SEALED,parent.get("status")),Check("r418_complete",audit.get("status")==COMPLETE,audit.get("status")),Check("r418_zero_process_failures",audit.get("checks_failed")==0,audit.get("checks_failed")),Check("exact_one_target_validation_disposition",val.get("candidate_count")==1,val.get("candidate_count")),Check("proxy_context_count_two",val.get("proxy_context_only_count")==2,val.get("proxy_context_only_count")),Check("readjudicated_matrix_75_cells",mat.get("cell_count")==75,mat.get("cell_count")),Check("class_accounting_complete",sum((mat.get("class_counts") or {}).values())==75,mat.get("class_counts")),Check("p2_backlog_frozen_six",p2.get("cell_count")==6,p2.get("cell_count")),Check("p2_execution_not_authorized",p2.get("execution_authorized") is False),Check("no_engine_execution",audit.get("engine_execution_performed") is False),Check("canonical_state_unchanged",audit.get("canonical_state_changed") is False),Check("next_action_present",bool(audit.get("next_action")),audit.get("next_action"))]
    ok=all(c.passed for c in checks)
    out={"stage":STAGE,"audit":"FINAL_TARGET_MATERIALIZATION_VALIDATION_PARTIAL_READJUDICATION_AND_P2_BACKLOG_FREEZE","status":SEALED if ok else BLOCKED,"verdict":"SEALED" if ok else "BLOCKED","checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.d() for c in checks],"summary":{"target_validation_candidate_count":audit.get("target_validation_candidate_count"),"target_validated_for_partial_readjudication_count":audit.get("target_validated_for_partial_readjudication_count"),"proxy_target_context_only_count":audit.get("proxy_target_context_only_count"),"partial_readjudication_changed_cell_count":audit.get("partial_readjudication_changed_cell_count"),"class_counts_after_partial_readjudication":audit.get("class_counts_after_partial_readjudication"),"structural_disagreement_count_after_partial_readjudication":audit.get("structural_disagreement_count_after_partial_readjudication"),"p2_backlog_cell_count":audit.get("p2_backlog_cell_count"),"p3_backlog_cell_count":audit.get("p3_backlog_cell_count"),"engine_execution_performed":False,"canonical_state_changed":False,"canonical_replay_authorized":False,"canonical_parameter_change_authorized":False,"deep_biological_coupling":False,"next_action":audit.get("next_action")},"next_action":audit.get("next_action")}; write(root/SEAL,out); return out
