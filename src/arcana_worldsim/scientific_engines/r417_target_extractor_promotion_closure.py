from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import csv, hashlib, json, math

STAGE="v0.6D1-R4.17"
PARENT_SEALED="PASS_R416_RECOVERED_METRIC_PROMOTION_GATE_AND_ARCANA_TARGET_SEMANTIC_PROTOCOL_FORMALIZATION_SEALED"
COMPLETE="PASS_R417_ARCANA_TARGET_EXTRACTOR_IMPLEMENTATION_AND_RECOVERED_METRIC_PROMOTION_CLOSURE_COMPLETE"
SEALED="PASS_R417_ARCANA_TARGET_EXTRACTOR_IMPLEMENTATION_AND_RECOVERED_METRIC_PROMOTION_CLOSURE_SEALED"
BLOCKED="BLOCKED_R417_PARENT_TARGET_EXTRACTION_OR_PROMOTION_CLOSURE_FAILURE"
NEXT="BUILD_R418_TARGET_MATERIALIZATION_VALIDATION_PARTIAL_READJUDICATION_AND_P2_BACKLOG_FREEZE"
CFG=Path("configs/world1_r417_target_extractor_promotion_closure_v0_6D1_R4_17.json")
PSEAL=Path("outputs/v0_6D1_R4_16_SEAL/R4_16_FINAL_SEAL_AUDIT.json")
PMETRIC=Path("outputs/v0_6D1_R4_16/R4_16_RECOVERED_METRIC_PROMOTION_GATE.json")
PTARGET=Path("outputs/v0_6D1_R4_16/R4_16_ARCANA_TARGET_SEMANTIC_PROTOCOL_REGISTRY.json")
PPLAN=Path("outputs/v0_6D1_R4_16/R4_16_R417_EXECUTION_PLAN.json")
R43DESC=Path("outputs/v0_6D1_R4_3/R4_3_WINDOW_BASELINE_DESCRIPTORS.json")
OUT=Path("outputs/v0_6D1_R4_17")
SEAL=Path("outputs/v0_6D1_R4_17_SEAL/R4_17_FINAL_SEAL_AUDIT.json")

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
        y=float(x)
        return y if math.isfinite(y) else None
    except Exception:return None
def getpath(o:Any,path:str)->Any:
    cur=o
    for k in str(path).split('.'):
        if not isinstance(cur,dict) or k not in cur:return None
        cur=cur[k]
    return cur
_HASH_CACHE:dict[str,str]={}
_JSON_CACHE:dict[str,Any]={}
_DESCRIPTOR_CACHE:dict[tuple[str,str],dict[str,Any]|None]={}

def sha256(p:Path)->str:
    k=str(p.resolve())
    if k in _HASH_CACHE:return _HASH_CACHE[k]
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    _HASH_CACHE[k]=h.hexdigest(); return _HASH_CACHE[k]

def metric_terminal_disposition(rec:dict[str,Any])->dict[str,Any]:
    disp=rec.get("disposition") or {}
    gate=str(disp.get("promotion_gate") or "")
    base={
        "window_id":rec.get("window_id"),"domain":rec.get("domain"),"engine":rec.get("engine"),
        "recovery_class":rec.get("recovery_class"),"r416_promotion_gate":gate,
        "adjudicative_promotion_authorized":False,"promotion_performed":False,
        "contextual_evidence_preserved":True,
    }
    if gate.startswith("PROXY_ONLY"):
        return {**base,"closure_status":"CLOSED_NONADJUDICATIVE_PROXY_ONLY","next_priority":"P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION","reason":disp.get("reason")}
    if gate.startswith("TRANSFORM_REQUIRED"):
        return {**base,"closure_status":"CLOSED_NONADJUDICATIVE_REQUIRED_TRANSFORM_NOT_FROZEN","next_priority":"P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION","reason":disp.get("reason")}
    if gate.startswith("CONDITIONAL_"):
        return {**base,"closure_status":"CLOSED_NONADJUDICATIVE_LABEL_TIME_BINDING_NOT_ESTABLISHED","next_priority":"P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION","reason":disp.get("reason")}
    if "PROXY_ONLY" in gate or "IDENTITY_ABSENT" in gate or gate.startswith("NO_") or gate.startswith("STRUCTURE_PROXY"):
        return {**base,"closure_status":"CLOSED_NONADJUDICATIVE_DOMAIN_IDENTITY_NOT_ESTABLISHED","next_priority":"P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION","reason":disp.get("reason")}
    return {**base,"closure_status":"CLOSED_NONADJUDICATIVE_NO_PRE_RESULT_TRANSFORM_AUTHORITY","next_priority":"P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION","reason":"R4.17 contains no result-selected fallback transform; unresolved recovered derivatives remain contextual only."}

def _artifact_path(root:Path,s:str)->Path:
    p=Path(str(s).replace('\\','/'))
    return p if p.is_absolute() else root/p

def _generic_json_descriptor(path:Path,domain:str)->dict[str,Any]|None:
    ck=(str(path.resolve()),domain)
    if ck in _DESCRIPTOR_CACHE:return _DESCRIPTOR_CACHE[ck]
    if path.suffix.lower() not in {'.json','.jsonl'} or not path.exists() or path.stat().st_size>64*1024*1024:
        _DESCRIPTOR_CACHE[ck]=None; return None
    if path.suffix.lower()=='.jsonl': _DESCRIPTOR_CACHE[ck]=None; return None
    pk=str(path.resolve())
    try:
        if pk not in _JSON_CACHE:_JSON_CACHE[pk]=load(path)
        o=_JSON_CACHE[pk]
    except Exception:
        _DESCRIPTOR_CACHE[ck]=None; return None
    required={"value","unit_basis","temporal_basis","spatial_population_basis","transform","provenance"}
    candidates=[]
    def walk(x:Any):
        if isinstance(x,dict):
            for key in ("canonical_target","target_descriptor","arcana_target"):
                v=x.get(key)
                if isinstance(v,dict): candidates.append(v)
            if str(x.get("domain") or "")==domain and required.issubset(x): candidates.append(x)
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(o)
    for c in candidates:
        if str(c.get("domain") or domain)!=domain: continue
        if not required.issubset(c): continue
        val=c.get("value")
        if isinstance(val,(int,float)) and finite(val) is None: continue
        out={"value":val,"unit_basis":c.get("unit_basis"),"temporal_basis":c.get("temporal_basis"),"spatial_population_basis":c.get("spatial_population_basis"),"transform":c.get("transform"),"provenance":c.get("provenance"),"candidate_comparability":str(c.get("comparability") or "NORMALIZABLE_CANDIDATE"),"extractor":"GENERIC_EXPLICIT_JSON_TARGET_DESCRIPTOR"}
        _DESCRIPTOR_CACHE[ck]=out; return out
    _DESCRIPTOR_CACHE[ck]=None; return None

def _generic_csv_descriptor(path:Path,domain:str)->dict[str,Any]|None:
    if path.suffix.lower()!='.csv' or not path.exists() or path.stat().st_size>64*1024*1024:return None
    try:
        with path.open(newline='',encoding='utf-8-sig',errors='replace') as f:
            r=csv.DictReader(f)
            need={"domain","value","unit_basis","temporal_basis","spatial_population_basis","transform","provenance"}
            if not r.fieldnames or not need.issubset(set(r.fieldnames)):return None
            for row in r:
                if str(row.get('domain') or '')!=domain:continue
                v=finite(row.get('value'))
                if v is None:continue
                return {"value":v,"unit_basis":row.get("unit_basis"),"temporal_basis":row.get("temporal_basis"),"spatial_population_basis":row.get("spatial_population_basis"),"transform":row.get("transform"),"provenance":row.get("provenance"),"candidate_comparability":str(row.get("comparability") or "NORMALIZABLE_CANDIDATE"),"extractor":"GENERIC_EXPLICIT_CSV_TARGET_DESCRIPTOR"}
    except Exception:return None
    return None

def _r43_bridge(cfg:dict[str,Any],desc:dict[str,Any],window_id:str,domain:str,root:Path)->dict[str,Any]|None:
    d=(desc.get("windows") or {}).get(window_id)
    if not isinstance(d,dict):return None
    dtype=str(d.get("descriptor_type") or "")
    rule=(cfg.get("r43_descriptor_domain_bridges") or {}).get(domain)
    if not rule:return None
    if "allowed_descriptor_types" in rule:
        if dtype not in rule.get("allowed_descriptor_types",[]):return None
        spec=rule
    else:
        spec=rule.get(dtype)
        if not isinstance(spec,dict):return None
    value=None; transform=None
    if spec.get("value_path"):
        value=finite(getpath(d,spec["value_path"]))
        if value is None:return None
        transform=spec["value_path"]
    elif spec.get("start_path") and spec.get("end_path"):
        a=finite(getpath(d,spec["start_path"])); b=finite(getpath(d,spec["end_path"]))
        if a is None or b is None:return None
        value={"start":a,"end":b,"delta":b-a,"ratio":(b/a if a!=0 else None)}
        transform=f"start={spec['start_path']}; end={spec['end_path']}; delta=end-start"
    else:return None
    sel=d.get("selected_frozen_artifact") or {}
    artifact_rel=str(sel.get("path") or "")
    artifact=_artifact_path(root,artifact_rel) if artifact_rel else None
    hash_check={"declared_hash_match":sel.get("hash_match") is True,"actual_artifact_present":bool(artifact and artifact.exists()),"actual_sha256_match":None}
    if artifact and artifact.exists() and sel.get("observed_sha256"):
        try:hash_check["actual_sha256_match"]=sha256(artifact)==str(sel.get("observed_sha256"))
        except Exception:hash_check["actual_sha256_match"]=False
    target=d.get("target") or {}
    comp=str(spec.get("candidate_comparability") or "PROXY_ONLY")
    return {
        "value":value,"unit_basis":spec.get("unit_basis"),
        "temporal_basis":{"window_id":window_id,"start":target.get("start"),"end":target.get("end"),"unit":target.get("unit")},
        "spatial_population_basis":"Frozen ARCANA population/spatial aggregation encoded by the R4.3 pre-result window baseline descriptor and its selected canonical artifact.",
        "transform":transform,"provenance":{"bridge":"outputs/v0_6D1_R4_3/R4_3_WINDOW_BASELINE_DESCRIPTORS.json","selected_frozen_artifact":artifact_rel,"selected_frozen_artifact_sha256":sel.get("observed_sha256")},
        "candidate_comparability":comp,"source_semantics":spec.get("source_semantics"),"extractor":"R43_PRE_RESULT_CANONICAL_WINDOW_DESCRIPTOR_BRIDGE","hash_check":hash_check,
    }

def target_record(root:Path,cfg:dict[str,Any],r43:dict[str,Any],rec:dict[str,Any])->dict[str,Any]:
    w=str(rec.get("window_id") or ""); d=str(rec.get("domain") or "")
    hits=list(rec.get("candidate_artifact_hits") or [])
    inspections=[]; strict=[]
    bridge=_r43_bridge(cfg,r43,w,d,root)
    if bridge: strict.append({"source":"R4_3_WINDOW_BASELINE_DESCRIPTORS","materialized":bridge})
    for s in hits:
        p=_artifact_path(root,s)
        info={"source":str(s),"exists":p.exists(),"suffix":p.suffix.lower() if p.exists() else None,"size":p.stat().st_size if p.exists() else None,"strict_target_descriptor_found":False}
        x=None
        if p.exists():
            x=_generic_json_descriptor(p,d) or _generic_csv_descriptor(p,d)
        if x:
            info["strict_target_descriptor_found"]=True
            strict.append({"source":str(s),"materialized":x})
        inspections.append(info)
    # Never select among multiple strict targets by numerical result. Prefer frozen R4.3 bridge, then lexicographic source only.
    selected=None
    if strict:
        strict=sorted(strict,key=lambda x:(0 if x["source"]=="R4_3_WINDOW_BASELINE_DESCRIPTORS" else 1,str(x["source"])))
        selected=strict[0]
    if selected:
        mat=selected["materialized"]; comp=str(mat.get("candidate_comparability") or "PROXY_ONLY")
        status="TARGET_MATERIALIZED_PROXY_ONLY_NONADJUDICATIVE" if comp=="PROXY_ONLY" else "TARGET_MATERIALIZED_REQUIRES_R418_COMPARABILITY_VALIDATION"
        return {"window_id":w,"domain":d,"protocol_status":rec.get("protocol_status"),"candidate_source_count":len(hits),"candidate_sources_inspected":inspections,"strict_materialization_candidate_count":len(strict),"selected_source":selected["source"],"materialized_target":mat,"materialization_status":status,"candidate_comparability":comp,"adjudicative_target_authorized":False,"readjudication_authorized":False,"selection_rule":"PRE_RESULT_SEMANTIC_AUTHORITY_THEN_LEXICOGRAPHIC; NEVER NUMERICAL_FIT"}
    if hits:
        status="SOURCE_CANDIDATES_INSPECTED_NO_STRICT_TARGET_MATERIALIZED"
    else:
        status="NO_CANONICAL_SOURCE_CANDIDATE_TARGET_DESIGN_GAP"
    return {"window_id":w,"domain":d,"protocol_status":rec.get("protocol_status"),"candidate_source_count":len(hits),"candidate_sources_inspected":inspections,"strict_materialization_candidate_count":0,"selected_source":None,"materialized_target":None,"materialization_status":status,"candidate_comparability":None,"adjudicative_target_authorized":False,"readjudication_authorized":False}

def build(root:Path)->dict[str,Any]:
    cfg=load(root/CFG) if (root/CFG).exists() else {}
    parent=load(root/PSEAL) if (root/PSEAL).exists() else {}
    pm=load(root/PMETRIC) if (root/PMETRIC).exists() else {}
    pt=load(root/PTARGET) if (root/PTARGET).exists() else {}
    pp=load(root/PPLAN) if (root/PPLAN).exists() else {}
    r43=load(root/R43DESC) if (root/R43DESC).exists() else {"windows":{}}
    ps=parent.get("summary") or {}
    checks=[
        Check("parent_r416_seal_present",(root/PSEAL).exists(),str(PSEAL)),
        Check("parent_r416_sealed",parent.get("status")==PARENT_SEALED,parent.get("status")),
        Check("parent_next_action_matches_r417",parent.get("next_action")=="BUILD_R417_ARCANA_TARGET_EXTRACTOR_IMPLEMENTATION_AND_RECOVERED_METRIC_PROMOTION_CLOSURE",parent.get("next_action")),
        Check("parent_exact_two_recovered_metric_dispositions",pm.get("recovered_metric_count")==2,pm.get("recovered_metric_count")),
        Check("parent_zero_auto_metric_promotions",pm.get("adjudicative_promotion_count")==0,pm.get("adjudicative_promotion_count")),
        Check("parent_exact_59_target_protocol_records",pt.get("p1_cell_count")==59,pt.get("p1_cell_count")),
        Check("parent_candidate_accounting_47_12",pt.get("cells_with_source_candidates")==47 and pt.get("cells_without_source_candidates")==12,{"with":pt.get("cells_with_source_candidates"),"without":pt.get("cells_without_source_candidates")}),
        Check("parent_r417_plan_frozen",pp.get("status")=="R416_PROMOTION_AND_TARGET_SEMANTIC_PROTOCOL_FROZEN",pp.get("status")),
        Check("parent_p2_backlog_4",ps.get("p2_backlog_cell_count")==4,ps.get("p2_backlog_cell_count")),
        Check("parent_p3_backlog_6",ps.get("p3_backlog_cell_count")==6,ps.get("p3_backlog_cell_count")),
        Check("policy_frozen",cfg.get("policy_freeze")=="FROZEN_PRE_TARGET_EXTRACTION_AND_PROMOTION_CLOSURE",cfg.get("policy_freeze")),
        Check("engine_execution_forbidden",cfg.get("engine_execution_performed") is False),
        Check("canonical_state_unchanged",cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized",cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized",cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off",cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden",cfg.get("majority_vote") is False),
        Check("r43_pre_result_descriptor_present",(root/R43DESC).exists(),str(R43DESC)),
    ]
    metric_records=[metric_terminal_disposition(r) for r in pm.get("records") or []]
    target_records=[target_record(root,cfg,r43,r) for r in pt.get("records") or []]
    mat=sum(r.get("materialized_target") is not None for r in target_records)
    proxy=sum(r.get("candidate_comparability")=="PROXY_ONLY" for r in target_records)
    validation_ready=sum(r.get("materialized_target") is not None and r.get("candidate_comparability") in {"DIRECT_CANDIDATE","NORMALIZABLE_CANDIDATE"} for r in target_records)
    exhausted=sum(r.get("materialization_status")=="SOURCE_CANDIDATES_INSPECTED_NO_STRICT_TARGET_MATERIALIZED" for r in target_records)
    nohit=sum(r.get("materialization_status")=="NO_CANONICAL_SOURCE_CANDIDATE_TARGET_DESIGN_GAP" for r in target_records)
    nonpromoted=sum(not r.get("promotion_performed") for r in metric_records)
    checks += [
        Check("exact_two_recovered_metrics_receive_terminal_closure",len(metric_records)==2,len(metric_records)),
        Check("no_recovered_metric_result_selected_promotion",all(r.get("promotion_performed") is False and r.get("adjudicative_promotion_authorized") is False for r in metric_records)),
        Check("all_nonpromoted_recovered_metrics_have_explicit_next_priority",all(bool(r.get("next_priority")) for r in metric_records if not r.get("promotion_performed"))),
        Check("all_59_p1_protocol_records_processed",len(target_records)==59,len(target_records)),
        Check("source_candidate_accounting_preserved",sum(r.get("candidate_source_count",0)>0 for r in target_records)==47,sum(r.get("candidate_source_count",0)>0 for r in target_records)),
        Check("no_source_candidate_accounting_preserved",sum(r.get("candidate_source_count",0)==0 for r in target_records)==12,sum(r.get("candidate_source_count",0)==0 for r in target_records)),
        Check("no_materialized_target_is_adjudicative_in_r417",all(r.get("adjudicative_target_authorized") is False and r.get("readjudication_authorized") is False for r in target_records)),
        Check("proxy_targets_remain_nonadjudicative",all(r.get("adjudicative_target_authorized") is False for r in target_records if r.get("candidate_comparability")=="PROXY_ONLY")),
        Check("no_filename_only_numeric_target",all((r.get("materialized_target") is None) or bool(r.get("materialized_target",{}).get("extractor")) for r in target_records)),
        Check("no_readjudication_in_r417",cfg.get("rules",{}).get("readjudication_forbidden_in_r417") is True),
        Check("no_engine_execution",cfg.get("engine_execution_performed") is False),
        Check("no_target_leakage_rule",cfg.get("rules",{}).get("no_target_leakage") is True),
        Check("no_result_selected_transform",cfg.get("rules",{}).get("no_result_selected_transform") is True),
    ]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    p2=int(ps.get("p2_backlog_cell_count") or 0)+nonpromoted
    metric_out={"stage":STAGE,"status":status,"recovered_metric_count":len(metric_records),"adjudicative_promotion_count":0,"nonadjudicative_terminal_closure_count":nonpromoted,"records":metric_records,"p2_increment_from_nonpromoted_recovered_metrics":nonpromoted}
    target_out={"stage":STAGE,"status":status,"p1_cell_count":len(target_records),"source_candidate_cell_count":sum(r.get("candidate_source_count",0)>0 for r in target_records),"no_source_candidate_cell_count":sum(r.get("candidate_source_count",0)==0 for r in target_records),"materialized_target_cell_count":mat,"r418_comparability_validation_candidate_count":validation_ready,"proxy_only_materialized_target_count":proxy,"source_candidates_exhausted_without_strict_target_count":exhausted,"target_design_gap_count":nohit,"records":target_records,"readjudication_performed":False}
    plan={"stage":STAGE,"status":"R417_TARGET_EXTRACTION_AND_PROMOTION_CLOSURE_FROZEN" if status==COMPLETE else BLOCKED,"r418_work_batches":{"A_TARGET_COMPARABILITY_VALIDATION":{"cell_count":validation_ready,"readjudication_authorized_in_r417":False},"B_PROXY_TARGET_CONTEXT_ONLY":{"cell_count":proxy},"C_SOURCE_CANDIDATE_EXHAUSTION_TARGET_DESIGN":{"cell_count":exhausted},"D_NO_SOURCE_CANDIDATE_TARGET_DESIGN":{"cell_count":nohit},"E_P2_ADAPTER_BACKLOG":{"cell_count":p2,"includes_nonpromoted_recovered_metrics":nonpromoted},"F_P3_EXTENSION_BACKLOG":{"cell_count":int(ps.get("p3_backlog_cell_count") or 0)}},"rules":["R4.18 validates metric/target comparability before any partial readjudication","no target is selected by numerical agreement","proxy-only materializations remain contextual","P2/P3 execution remains separately authorized"],"next_action":NEXT}
    out={"stage":STAGE,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.d() for c in checks],"recovered_metric_count":len(metric_records),"recovered_metric_adjudicative_promotion_count":0,"recovered_metric_nonadjudicative_closure_count":nonpromoted,"p1_target_materialized_cell_count":mat,"r418_target_comparability_validation_candidate_count":validation_ready,"p1_proxy_only_materialized_count":proxy,"p1_source_candidate_exhausted_count":exhausted,"p1_target_design_gap_count":nohit,"p2_backlog_cell_count":p2,"p3_backlog_cell_count":int(ps.get("p3_backlog_cell_count") or 0),"engine_execution_performed":False,"readjudication_performed":False,"canonical_state_changed":False,"next_action":NEXT}
    write(root/OUT/"R4_17_RECOVERED_METRIC_PROMOTION_CLOSURE.json",metric_out)
    write(root/OUT/"R4_17_ARCANA_TARGET_EXTRACTOR_RESULTS.json",target_out)
    write(root/OUT/"R4_17_R418_CLOSURE_PLAN.json",plan)
    write(root/OUT/"R4_17_INTEGRATED_AUDIT.json",out)
    return out

def final_seal(root:Path)->dict[str,Any]:
    parent=load(root/PSEAL) if (root/PSEAL).exists() else {}
    audit=load(root/OUT/"R4_17_INTEGRATED_AUDIT.json") if (root/OUT/"R4_17_INTEGRATED_AUDIT.json").exists() else {}
    metric=load(root/OUT/"R4_17_RECOVERED_METRIC_PROMOTION_CLOSURE.json") if (root/OUT/"R4_17_RECOVERED_METRIC_PROMOTION_CLOSURE.json").exists() else {}
    targ=load(root/OUT/"R4_17_ARCANA_TARGET_EXTRACTOR_RESULTS.json") if (root/OUT/"R4_17_ARCANA_TARGET_EXTRACTOR_RESULTS.json").exists() else {}
    plan=load(root/OUT/"R4_17_R418_CLOSURE_PLAN.json") if (root/OUT/"R4_17_R418_CLOSURE_PLAN.json").exists() else {}
    checks=[
        Check("parent_r416_sealed",parent.get("status")==PARENT_SEALED,parent.get("status")),
        Check("r417_complete",audit.get("status")==COMPLETE,audit.get("status")),
        Check("r417_zero_process_failures",audit.get("checks_failed")==0,audit.get("checks_failed")),
        Check("exact_two_recovered_metric_closures",metric.get("recovered_metric_count")==2,metric.get("recovered_metric_count")),
        Check("zero_result_selected_metric_promotions",metric.get("adjudicative_promotion_count")==0,metric.get("adjudicative_promotion_count")),
        Check("exact_59_target_extractor_records",targ.get("p1_cell_count")==59,targ.get("p1_cell_count")),
        Check("target_candidate_accounting_47_12",targ.get("source_candidate_cell_count")==47 and targ.get("no_source_candidate_cell_count")==12,{"with":targ.get("source_candidate_cell_count"),"without":targ.get("no_source_candidate_cell_count")}),
        Check("no_readjudication",audit.get("readjudication_performed") is False),
        Check("r418_plan_frozen",plan.get("status")=="R417_TARGET_EXTRACTION_AND_PROMOTION_CLOSURE_FROZEN",plan.get("status")),
        Check("no_engine_execution",audit.get("engine_execution_performed") is False),
        Check("canonical_state_unchanged",audit.get("canonical_state_changed") is False),
        Check("next_action_present",audit.get("next_action")==NEXT,audit.get("next_action")),
    ]
    ok=all(c.passed for c in checks)
    out={"stage":STAGE,"audit":"FINAL_ARCANA_TARGET_EXTRACTOR_IMPLEMENTATION_AND_RECOVERED_METRIC_PROMOTION_CLOSURE","status":SEALED if ok else BLOCKED,"verdict":"SEALED" if ok else "BLOCKED","checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.d() for c in checks],"summary":{"recovered_metric_adjudicative_promotion_count":metric.get("adjudicative_promotion_count"),"recovered_metric_nonadjudicative_closure_count":metric.get("nonadjudicative_terminal_closure_count"),"p1_target_materialized_cell_count":targ.get("materialized_target_cell_count"),"r418_target_comparability_validation_candidate_count":targ.get("r418_comparability_validation_candidate_count"),"p1_proxy_only_materialized_count":targ.get("proxy_only_materialized_target_count"),"p1_source_candidate_exhausted_count":targ.get("source_candidates_exhausted_without_strict_target_count"),"p1_target_design_gap_count":targ.get("target_design_gap_count"),"p2_backlog_cell_count":audit.get("p2_backlog_cell_count"),"p3_backlog_cell_count":audit.get("p3_backlog_cell_count"),"engine_execution_performed":False,"readjudication_performed":False,"canonical_state_changed":False,"canonical_replay_authorized":False,"canonical_parameter_change_authorized":False,"deep_biological_coupling":False,"next_action":NEXT},"next_action":NEXT}
    write(root/SEAL,out)
    return out
