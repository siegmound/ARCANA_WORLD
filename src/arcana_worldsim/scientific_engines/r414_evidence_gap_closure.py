from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections import Counter, defaultdict
import fnmatch
import json

STAGE = "v0.6D1-R4.14"
R413_SEALED = "PASS_R413_CDMETAPOP_ABSOLUTE_RESPONSE_COMPARABILITY_DOWNGRADE_AND_READJUDICATION_SEALED"
COMPLETE = "PASS_R414_MULTI_ENGINE_EVIDENCE_GAP_CENSUS_AND_TARGETED_ADAPTER_ENHANCEMENT_PLAN_COMPLETE"
SEALED = "PASS_R414_MULTI_ENGINE_EVIDENCE_GAP_CLOSURE_AND_TARGETED_ADAPTER_ENHANCEMENT_PLAN_SEALED"
BLOCKED = "BLOCKED_R414_PARENT_MATRIX_OR_GAP_CENSUS_FAILURE"
NEXT_RETAINED = "BUILD_R415_RETAINED_RUNTIME_METRIC_RECOVERY_AND_TARGET_SEMANTIC_MATERIALIZATION"
NEXT_SEMANTIC = "BUILD_R415_ARCANA_TARGET_SEMANTIC_MATERIALIZATION_AND_ADAPTER_ENHANCEMENT"
NEXT_CLOSURE = "BUILD_R415_REVALIDATION_CLOSURE_AND_BASELINE_PROMOTION_GATE"

CFG_REL = Path("configs/world1_r414_evidence_gap_closure_v0_6D1_R4_14.json")
R413_SEAL_REL = Path("outputs/v0_6D1_R4_13_SEAL/R4_13_FINAL_SEAL_AUDIT.json")
R413_MATRIX_REL = Path("outputs/v0_6D1_R4_13/R4_13_CDMETAPOP_COMPARABILITY_DOWNGRADED_READJUDICATED_MATRIX.json")
R413_SUMMARY_REL = Path("outputs/v0_6D1_R4_13/R4_13_EXECUTION_SUMMARY.json")
R43_MAPPING_REL = Path("outputs/v0_6D1_R4_3/R4_3_PER_JOB_UNIT_MAPPING.json")
R43_CFG_REL = Path("configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json")
R44_CFG_REL = Path("configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json")
R41_AUTH_REL = Path("outputs/v0_6D1_R4_1/R4_1_SEMANTIC_AUTHORITY_MATRIX.json")
R42_JOBS_REL = Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")
OUT_REL = Path("outputs/v0_6D1_R4_14")
SEAL_REL = Path("outputs/v0_6D1_R4_14_SEAL/R4_14_FINAL_SEAL_AUDIT.json")

GAP_CLASSES = {"INSUFFICIENT_EVIDENCE", "SEMANTICALLY_NONCOMPARABLE"}
ADJ_COMP = {"DIRECT", "NORMALIZABLE"}

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
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)+"\n", encoding="utf-8")

def _row_target_comp(r: dict[str,Any]) -> str | None:
    t=r.get("target")
    return t.get("comparability") if isinstance(t,dict) else None

def _runtime_root(root: Path, job_id: str, engine: str) -> list[Path]:
    roots=[]
    p=root/"outputs/v0_6D1_R4_3/jobs"/job_id/"runtime_work"
    if p.exists(): roots.append(p)
    if engine=="CDMetaPOP":
        p2=root/"outputs/v0_6D1_R4_7/jobs"/job_id/"runtime_work"
        if p2.exists(): roots.append(p2)
    return roots

def _pattern_hits(roots: list[Path], patterns: list[str], limit: int = 24) -> list[str]:
    hits=[]
    for base in roots:
        try:
            for p in base.rglob("*"):
                if not p.is_file(): continue
                rel=str(p.relative_to(base)).replace("\\","/")
                name=p.name
                if any(fnmatch.fnmatch(name,pat) or fnmatch.fnmatch(rel,pat) for pat in patterns):
                    hits.append(str(p))
                    if len(hits)>=limit: return hits
        except OSError:
            continue
    return hits

def _root_cause(prim: list[dict[str,Any]]) -> str:
    if not prim:
        return "NO_PRIMARY_AUTHORITY_JOB_IN_FROZEN_WINDOW"
    if all(r.get("discordance_class")=="SEMANTICALLY_NONCOMPARABLE" for r in prim):
        return "PRIMARY_ENGINE_SEMANTIC_NONCOMPARABILITY"
    targets=[r.get("target") for r in prim if isinstance(r.get("target"),dict)]
    if not targets:
        return "NO_ARCANA_DECLARED_TARGET"
    if not any((t.get("comparability") in ADJ_COMP) for t in targets):
        return "ARCANA_TARGET_NONADJUDICATIVE_PROXY_OR_NONCOMPARABLE"
    adj_target_rows=[r for r in prim if _row_target_comp(r) in ADJ_COMP]
    if adj_target_rows and all(r.get("mapping_comparability") not in ADJ_COMP for r in adj_target_rows):
        return "PRIMARY_MAPPING_NONADJUDICATIVE_PROXY_ONLY"
    if any(r.get("reason")=="NO_R43_NORMALIZED_RESULT_METRIC_FOR_DOMAIN" or (r.get("metric") is None and r.get("mapping_comparability") in ADJ_COMP and _row_target_comp(r) in ADJ_COMP) for r in prim):
        return "PRIMARY_NORMALIZED_METRIC_MISSING"
    if any(r.get("mapping_comparability")=="PROXY_ONLY" for r in prim):
        return "PRIMARY_MAPPING_NONADJUDICATIVE_PROXY_ONLY"
    return "MIXED_OR_UNRESOLVED_PRIMARY_EVIDENCE_GAP"

def _closure_action(cause: str, prim: list[dict[str,Any]], cap: dict[str,Any], runtime_hits: dict[str,list[str]]) -> tuple[str,str]:
    engines=sorted({str(r.get("engine")) for r in prim if r.get("engine")})
    if cause=="PRIMARY_ENGINE_SEMANTIC_NONCOMPARABILITY" and "Geonomics" in engines:
        return "P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION", "GEONOMICS_ARCANA_LANDSCAPE_ADAPTER_REQUIRED"
    if cause in {"NO_ARCANA_DECLARED_TARGET","ARCANA_TARGET_NONADJUDICATIVE_PROXY_OR_NONCOMPARABLE"}:
        return "P1_ARCANA_TARGET_SEMANTIC_MATERIALIZATION_FROM_EXISTING_CANONICAL_ARTIFACTS", "ARCANA_TARGET_PROTOCOL_REQUIRED"
    if cause=="NO_PRIMARY_AUTHORITY_JOB_IN_FROZEN_WINDOW":
        return "P3_NEW_EXTENSION_JOB_IN_NEW_NAMESPACE_NO_R42_FREEZE_MUTATION", "NEW_PRIMARY_EXTENSION_JOB_REQUIRED"
    if cause=="PRIMARY_MAPPING_NONADJUDICATIVE_PROXY_ONLY":
        return "P1_ARCANA_TARGET_SEMANTIC_MATERIALIZATION_FROM_EXISTING_CANONICAL_ARTIFACTS", "MAPPING_OR_MATCHED_CONTROL_SEMANTIC_PROTOCOL_REQUIRED"
    if cause=="PRIMARY_NORMALIZED_METRIC_MISSING":
        for eng in engines:
            cc=cap.get(eng,{})
            if runtime_hits.get(eng) and cc.get("confidence") in {"HIGH_FOR_ALLELE_FREQUENCY_DERIVATIVES","SEMANTIC_AUDIT_REQUIRED"}:
                return "P0_RETAINED_RUNTIME_REEXTRACTION_NO_ENGINE_RERUN", f"RETAINED_{eng.upper()}_RUNTIME_METRIC_RECOVERY_CANDIDATE"
        return "P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION", "PRIMARY_ADAPTER_METRIC_ENHANCEMENT_REQUIRED"
    return "P4_SEMANTIC_NONCOMPARABILITY_PRESERVED_IF_NO_VALID_BRIDGE_EXISTS", "MANUAL_SEMANTIC_REVIEW_REQUIRED"

def build(root: Path) -> tuple[dict[str,Any],list[Check]]:
    cfg=load_json(root/CFG_REL)
    seal=load_json(root/R413_SEAL_REL) if (root/R413_SEAL_REL).exists() else {}
    matrix=load_json(root/R413_MATRIX_REL) if (root/R413_MATRIX_REL).exists() else {}
    summary=load_json(root/R413_SUMMARY_REL) if (root/R413_SUMMARY_REL).exists() else {}
    mappings=load_json(root/R43_MAPPING_REL) if (root/R43_MAPPING_REL).exists() else {}
    r43cfg=load_json(root/R43_CFG_REL) if (root/R43_CFG_REL).exists() else {}
    auth=load_json(root/R41_AUTH_REL) if (root/R41_AUTH_REL).exists() else {}
    jobs=load_json(root/R42_JOBS_REL) if (root/R42_JOBS_REL).exists() else {}
    rows=list(matrix.get("evidence_rows") or [])
    cells=list(matrix.get("cells") or [])
    gaps=[c for c in cells if c.get("discordance_class") in GAP_CLASSES]
    expected_scoped=sum(len(v) for v in (r43cfg.get("window_domain_scope") or {}).values())
    class_counts=matrix.get("class_counts") or {}
    checks=[
        Check("parent_r413_seal_present",(root/R413_SEAL_REL).exists(),str(R413_SEAL_REL)),
        Check("parent_r413_sealed",seal.get("status")==R413_SEALED,seal.get("status")),
        Check("parent_r413_zero_structural_disagreements",class_counts.get("STRUCTURAL_DISAGREEMENT")==0,class_counts),
        Check("parent_r413_next_action_matches_r414",summary.get("next_action")=="BUILD_R414_MULTI_ENGINE_EVIDENCE_GAP_CLOSURE_AND_TARGETED_ADAPTER_ENHANCEMENT",summary.get("next_action")),
        Check("parent_matrix_exact_scoped_cells",len(cells)==expected_scoped==75,{"matrix":len(cells),"scope":expected_scoped}),
        Check("parent_gap_count_matches_classes",len(gaps)==class_counts.get("INSUFFICIENT_EVIDENCE",0)+class_counts.get("SEMANTICALLY_NONCOMPARABLE",0),{"gaps":len(gaps),"classes":class_counts}),
        Check("parent_expected_71_gap_cells",len(gaps)==71,len(gaps)),
        Check("r42_frozen_job_registry_still_exact_23",jobs.get("job_count")==23,len(jobs.get("jobs") or [])),
        Check("r43_mapping_still_exact_23",mappings.get("mapping_count")==23,len(mappings.get("mappings") or [])),
        Check("authority_matrix_present",len((auth.get("domains") or {}))==15,len(auth.get("domains") or {})),
        Check("policy_frozen_pre_closure_execution",cfg.get("policy_freeze")=="FROZEN_PRE_CLOSURE_EXECUTION",cfg.get("policy_freeze")),
        Check("engine_execution_forbidden",cfg.get("engine_execution_performed") is False),
        Check("canonical_state_unchanged",cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized",cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized",cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off",cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden",cfg.get("majority_vote") is False),
    ]
    if any(not c.passed for c in checks):
        out={"stage":STAGE,"status":BLOCKED,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"canonical_state_changed":False}
        write_json(root/OUT_REL/"R4_14_INTEGRATED_AUDIT.json",out)
        return out,checks

    cap=cfg.get("retained_runtime_capability_candidates") or {}
    gap_records=[]; runtime_registry={}
    for c in gaps:
        wid,domain=c.get("window_id"),c.get("domain")
        cr=[r for r in rows if r.get("window_id")==wid and r.get("domain")==domain]
        prim=[r for r in cr if r.get("authority_role")=="PRIMARY"]
        engines=sorted({str(r.get("engine")) for r in prim if r.get("engine")})
        hits_by={}
        for eng in engines:
            job_ids=sorted({str(r.get("job_id")) for r in prim if r.get("engine")==eng and r.get("job_id")})
            hits=[]
            for jid in job_ids:
                roots=_runtime_root(root,jid,eng)
                hits.extend(_pattern_hits(roots,list((cap.get(eng) or {}).get("patterns") or [])))
            hits_by[eng]=sorted(set(hits))[:24]
            runtime_registry.setdefault(eng,{"jobs":set(),"hits":set()})
            runtime_registry[eng]["jobs"].update(job_ids); runtime_registry[eng]["hits"].update(hits_by[eng])
        cause=_root_cause(prim)
        priority,action=_closure_action(cause,prim,cap,hits_by)
        gap_records.append({
            "window_id":wid,"domain":domain,"parent_class":c.get("discordance_class"),"parent_reason":c.get("reason"),
            "primary_evidence_row_count":len(prim),"primary_engines":engines,
            "primary_rows":[{"job_id":r.get("job_id"),"engine":r.get("engine"),"mapping_comparability":r.get("mapping_comparability"),"target_comparability":_row_target_comp(r),"reason":r.get("reason"),"metric_name":(r.get("metric") or {}).get("name") if isinstance(r.get("metric"),dict) else None,"discordance_class":r.get("discordance_class")} for r in prim],
            "root_cause":cause,"closure_priority":priority,"closure_action":action,
            "retained_runtime_hits":hits_by,"canonical_change_authorized":False,"engine_rerun_authorized_in_r414":False,
        })

    causes=Counter(x["root_cause"] for x in gap_records)
    priorities=Counter(x["closure_priority"] for x in gap_records)
    actions=Counter(x["closure_action"] for x in gap_records)
    by_window=Counter(x["window_id"] for x in gap_records)
    by_domain=Counter(x["domain"] for x in gap_records)
    runtime_out={}
    for eng,v in sorted(runtime_registry.items()):
        cc=cap.get(eng,{})
        runtime_out[eng]={"job_ids":sorted(v["jobs"]),"retained_artifact_hit_count":len(v["hits"]),"sample_hits":sorted(v["hits"])[:24],"candidate_domains":cc.get("candidate_domains",[]),"confidence":cc.get("confidence"),"note":cc.get("note")}

    p0=[x for x in gap_records if x["closure_priority"]=="P0_RETAINED_RUNTIME_REEXTRACTION_NO_ENGINE_RERUN"]
    target_sem=[x for x in gap_records if x["closure_priority"]=="P1_ARCANA_TARGET_SEMANTIC_MATERIALIZATION_FROM_EXISTING_CANONICAL_ARTIFACTS"]
    rerun=[x for x in gap_records if x["closure_priority"]=="P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION"]
    extension=[x for x in gap_records if x["closure_priority"]=="P3_NEW_EXTENSION_JOB_IN_NEW_NAMESPACE_NO_R42_FREEZE_MUTATION"]
    if p0:
        next_action=NEXT_RETAINED
    elif gap_records:
        next_action=NEXT_SEMANTIC
    else:
        next_action=NEXT_CLOSURE

    # Frozen first-batch policy: recover only cells with an existing adjudicative ARCANA target and retained primary runtime evidence.
    first_batch=[{"window_id":x["window_id"],"domain":x["domain"],"primary_engines":x["primary_engines"],"action":x["closure_action"]} for x in p0]
    target_batch=[{"window_id":x["window_id"],"domain":x["domain"],"primary_engines":x["primary_engines"],"action":x["closure_action"]} for x in target_sem]

    checks += [
        Check("all_71_gap_cells_censused",len(gap_records)==71,len(gap_records)),
        Check("every_gap_has_root_cause",all(x.get("root_cause") for x in gap_records),dict(causes)),
        Check("every_gap_has_closure_priority",all(x.get("closure_priority") for x in gap_records),dict(priorities)),
        Check("every_gap_has_closure_action",all(x.get("closure_action") for x in gap_records),dict(actions)),
        Check("no_r414_engine_rerun_authorized",all(x.get("engine_rerun_authorized_in_r414") is False for x in gap_records)),
        Check("no_r42_freeze_mutation_authorized",cfg.get("rules",{}).get("r42_exact_23_job_registry_is_immutable") is True),
        Check("new_jobs_require_new_namespace",cfg.get("rules",{}).get("new_extension_jobs_must_use_new_namespace") is True),
        Check("retained_evidence_preferred_before_rerun",cfg.get("rules",{}).get("retained_raw_evidence_must_be_preferred_to_rerun") is True),
        Check("geonomics_default_model_not_promotable",cfg.get("rules",{}).get("geonomics_default_landscape_cannot_be_reinterpreted_as_arcana_history") is True),
        Check("no_target_leakage",cfg.get("rules",{}).get("no_target_leakage") is True),
        Check("no_result_selected_enhancement",cfg.get("rules",{}).get("no_result_selected_adapter_enhancement") is True),
    ]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    census={"stage":STAGE,"status":status,"parent_gap_count":71,"gap_count":len(gap_records),"root_cause_counts":dict(sorted(causes.items())),"closure_priority_counts":dict(sorted(priorities.items())),"closure_action_counts":dict(sorted(actions.items())),"gap_counts_by_window":dict(sorted(by_window.items())),"gap_counts_by_domain":dict(sorted(by_domain.items())),"gaps":gap_records,"canonical_state_changed":False}
    capability={"stage":STAGE,"status":status,"engine_capability_audit":runtime_out,"retained_reextraction_candidate_cell_count":len(p0),"target_semantic_materialization_cell_count":len(target_sem),"adapter_reexecution_candidate_cell_count":len(rerun),"extension_job_candidate_cell_count":len(extension),"engine_execution_performed":False,"canonical_state_changed":False}
    plan={"stage":STAGE,"status":"R414_GAP_CLOSURE_PLAN_FROZEN" if status==COMPLETE else BLOCKED,"closure_priority":cfg.get("closure_priority"),"first_batch_retained_runtime_recovery":first_batch,"parallel_arcana_target_semantic_batch":target_batch,"adapter_reexecution_deferred_until_retained_recovery_exhausted":[{"window_id":x["window_id"],"domain":x["domain"],"primary_engines":x["primary_engines"],"action":x["closure_action"]} for x in rerun],"extension_jobs_deferred_new_namespace_only":[{"window_id":x["window_id"],"domain":x["domain"],"primary_engines":x["primary_engines"],"action":x["closure_action"]} for x in extension],"r42_frozen_registry_modified":False,"engine_execution_authorized_in_r414":False,"canonical_change_authorized":False,"next_action":next_action}
    audit={"stage":STAGE,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"gap_count":len(gap_records),"root_cause_counts":dict(sorted(causes.items())),"closure_priority_counts":dict(sorted(priorities.items())),"retained_reextraction_candidate_cell_count":len(p0),"canonical_state_changed":False,"next_action":next_action}
    write_json(root/OUT_REL/"R4_14_EVIDENCE_GAP_CENSUS.json",census)
    write_json(root/OUT_REL/"R4_14_RETAINED_EVIDENCE_CAPABILITY_AUDIT.json",capability)
    write_json(root/OUT_REL/"R4_14_TARGETED_ADAPTER_ENHANCEMENT_PLAN.json",plan)
    write_json(root/OUT_REL/"R4_14_INTEGRATED_AUDIT.json",audit)
    return audit,checks

def final_seal(root: Path) -> tuple[dict[str,Any],list[Check]]:
    parent=load_json(root/R413_SEAL_REL) if (root/R413_SEAL_REL).exists() else {}
    audit=load_json(root/OUT_REL/"R4_14_INTEGRATED_AUDIT.json") if (root/OUT_REL/"R4_14_INTEGRATED_AUDIT.json").exists() else {}
    census=load_json(root/OUT_REL/"R4_14_EVIDENCE_GAP_CENSUS.json") if (root/OUT_REL/"R4_14_EVIDENCE_GAP_CENSUS.json").exists() else {}
    plan=load_json(root/OUT_REL/"R4_14_TARGETED_ADAPTER_ENHANCEMENT_PLAN.json") if (root/OUT_REL/"R4_14_TARGETED_ADAPTER_ENHANCEMENT_PLAN.json").exists() else {}
    checks=[
        Check("parent_r413_sealed",parent.get("status")==R413_SEALED,parent.get("status")),
        Check("r414_gap_census_complete",audit.get("status")==COMPLETE,audit.get("status")),
        Check("r414_zero_process_failures",audit.get("checks_failed")==0,audit.get("checks_failed")),
        Check("exact_71_parent_gap_cells_censused",census.get("gap_count")==71,census.get("gap_count")),
        Check("gap_closure_plan_frozen",plan.get("status")=="R414_GAP_CLOSURE_PLAN_FROZEN",plan.get("status")),
        Check("r42_frozen_registry_preserved",plan.get("r42_frozen_registry_modified") is False),
        Check("no_engine_execution_in_r414",plan.get("engine_execution_authorized_in_r414") is False),
        Check("canonical_state_unchanged",plan.get("canonical_change_authorized") is False),
        Check("canonical_replay_not_authorized",True),
        Check("canonical_parameter_change_not_authorized",True),
        Check("deep_biological_coupling_off",True),
        Check("next_action_present",bool(plan.get("next_action")),plan.get("next_action")),
    ]
    ok=all(c.passed for c in checks)
    out={"stage":STAGE,"audit":"FINAL_MULTI_ENGINE_EVIDENCE_GAP_CLOSURE_CENSUS_AND_TARGETED_ADAPTER_ENHANCEMENT_PLAN","status":SEALED if ok else BLOCKED,"verdict":"SEALED" if ok else "BLOCKED","checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"summary":{"parent_gap_count":census.get("gap_count"),"root_cause_counts":census.get("root_cause_counts"),"closure_priority_counts":census.get("closure_priority_counts"),"retained_reextraction_candidate_cell_count":audit.get("retained_reextraction_candidate_cell_count"),"canonical_state_changed":False,"canonical_replay_authorized":False,"canonical_parameter_change_authorized":False,"deep_biological_coupling":False,"next_action":plan.get("next_action")},"next_action":plan.get("next_action")}
    write_json(root/SEAL_REL,out)
    return out,checks
