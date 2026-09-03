from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

STAGE="v0.6D1-R4.16"
PARENT_SEALED="PASS_R415_RETAINED_RUNTIME_METRIC_RECOVERY_AND_TARGET_SEMANTIC_MATERIALIZATION_AUDIT_SEALED"
PARENT_REVISION="R4.15-R1"
COMPLETE="PASS_R416_RECOVERED_METRIC_PROMOTION_GATE_AND_ARCANA_TARGET_SEMANTIC_PROTOCOL_FORMALIZATION_COMPLETE"
SEALED="PASS_R416_RECOVERED_METRIC_PROMOTION_GATE_AND_ARCANA_TARGET_SEMANTIC_PROTOCOL_FORMALIZATION_SEALED"
BLOCKED="BLOCKED_R416_PARENT_PROMOTION_OR_TARGET_PROTOCOL_FAILURE"
NEXT="BUILD_R417_ARCANA_TARGET_EXTRACTOR_IMPLEMENTATION_AND_RECOVERED_METRIC_PROMOTION_CLOSURE"
CFG=Path("configs/world1_r416_recovered_metric_target_protocol_v0_6D1_R4_16.json")
PSEAL=Path("outputs/v0_6D1_R4_15_SEAL/R4_15_FINAL_SEAL_AUDIT.json")
PREC=Path("outputs/v0_6D1_R4_15/R4_15_RETAINED_RUNTIME_METRIC_RECOVERY.json")
PTARG=Path("outputs/v0_6D1_R4_15/R4_15_ARCANA_TARGET_SOURCE_CANDIDATE_REGISTRY.json")
PPLAN=Path("outputs/v0_6D1_R4_15/R4_15_R416_PROMOTION_GATE_PLAN.json")
CENSUS=Path("outputs/v0_6D1_R4_14/R4_14_EVIDENCE_GAP_CENSUS.json")
OUT=Path("outputs/v0_6D1_R4_16")
SEAL=Path("outputs/v0_6D1_R4_16_SEAL/R4_16_FINAL_SEAL_AUDIT.json")

@dataclass(frozen=True)
class Check:
    name:str; passed:bool; detail:Any=None
    def d(self): return {"name":self.name,"pass":bool(self.passed),"detail":self.detail}

def load(p:Path): return json.loads(p.read_text(encoding="utf-8-sig"))
def write(p:Path,o:Any):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def recovered_metric_disposition(domain:str, engine:str, recovery_class:str)->dict[str,Any]:
    """Freeze semantic disposition only. R4.16 never promotes raw recovered metrics."""
    d=str(domain); e=str(engine); rc=str(recovery_class)
    base={
        "domain":d,"engine":e,"recovery_class":rc,
        "adjudicative_promotion_authorized":False,
        "promotion_performed":False,
        "requires_explicit_target_semantics":True,
    }
    if e=="CDMetaPOP":
        if d=="population_persistence":
            return {**base,"promotion_gate":"PROXY_ONLY_BY_R412_NEUTRAL_INVARIANCE_FAILURE","reason":"Absolute CDMetaPOP population response is non-invariant under the matched neutral control and remains PROXY_ONLY under R4.13."}
        return {**base,"promotion_gate":"NO_DOMAIN_IDENTITY_FROM_SUMMARY_POPULATION_DERIVATIVE","reason":"Recovered CDMetaPOP summary population derivatives do not identify this domain."}
    if e=="NEMO":
        if d=="additive_variance":
            return {**base,"promotion_gate":"TRANSFORM_REQUIRED_EFFECT_SIZE_MODEL_ABSENT","reason":"qfreq-derived heterozygosity/frequency structure is not additive genetic variance without trait effect sizes, ploidy/trait binding and aggregation semantics."}
        if d in {"gene_flow","connectivity","admixture","ancestry","managed_wild_isolation","producer_divergence"}:
            return {**base,"promotion_gate":"STRUCTURE_PROXY_ONLY_FLOW_OR_LABEL_IDENTITY_ABSENT","reason":"Allele-frequency gap/heterozygosity can support population structure but do not directly identify migration, ancestry, labelled isolation or divergence semantics."}
        return {**base,"promotion_gate":"NO_FROZEN_DOMAIN_TRANSFORM","reason":"No pre-result domain transform has been established from the recovered NEMO qfreq derivative to this ARCANA domain."}
    if e=="SLiM":
        if d=="additive_variance":
            return {**base,"promotion_gate":"TRANSFORM_REQUIRED_TRAIT_EFFECT_MAPPING_ABSENT","reason":"Tree-sequence diversity/FST does not identify additive trait variance without trait-effect mapping."}
        if d in {"gene_flow","connectivity","admixture","ancestry","managed_wild_isolation","producer_divergence"}:
            return {**base,"promotion_gate":"CONDITIONAL_STRUCTURE_METRIC_REQUIRES_LABEL_AND_TIME_BINDING","reason":"Tree-sequence derivatives may support structure/divergence only after explicit population-label, temporal and domain transform binding."}
        return {**base,"promotion_gate":"NO_FROZEN_DOMAIN_TRANSFORM","reason":"No pre-result domain transform has been established from the recovered SLiM tree derivative to this ARCANA domain."}
    return {**base,"promotion_gate":"UNSUPPORTED_RECOVERED_ENGINE","reason":"Recovered engine is outside the R4.16 frozen promotion catalogue."}

def _engine_from_record(rec:dict[str,Any])->tuple[str,str]:
    auth=str(rec.get("authorized_recovery_engine") or "")
    records=[r for r in rec.get("engine_records") or [] if r.get("required_for_r414_p0_candidate_realization")]
    if records:
        return str(records[0].get("engine") or auth), str(records[0].get("recovery_class") or "")
    return auth,""

def _target_protocol_record(rec:dict[str,Any], protocols:dict[str,Any])->dict[str,Any]:
    domain=str(rec.get("domain") or "")
    hits=list(rec.get("candidate_artifact_hits") or [])
    proto=protocols.get(domain)
    return {
        "window_id":rec.get("window_id"),
        "domain":domain,
        "root_cause":rec.get("root_cause"),
        "closure_action":rec.get("closure_action"),
        "candidate_artifact_hits":hits,
        "candidate_artifact_count":len(hits),
        "protocol":proto,
        "protocol_status":"DOMAIN_PROTOCOL_FROZEN_SOURCE_CANDIDATES_PRESENT_EXTRACTOR_REQUIRED" if proto and hits else ("DOMAIN_PROTOCOL_FROZEN_NO_CANONICAL_SOURCE_CANDIDATE" if proto else "BLOCKED_UNKNOWN_DOMAIN_PROTOCOL"),
        "target_value_materialized":False,
        "adjudicative_target_authorized":False,
        "external_result_used_to_define_target":False,
    }

def build(root:Path)->dict[str,Any]:
    cfg=load(root/CFG) if (root/CFG).exists() else {}
    parent=load(root/PSEAL) if (root/PSEAL).exists() else {}
    rec=load(root/PREC) if (root/PREC).exists() else {}
    targ=load(root/PTARG) if (root/PTARG).exists() else {}
    pplan=load(root/PPLAN) if (root/PPLAN).exists() else {}
    census=load(root/CENSUS) if (root/CENSUS).exists() else {}
    checks=[]
    psum=parent.get("summary") or {}
    checks += [
        Check("parent_r415_seal_present",(root/PSEAL).exists(),str(PSEAL)),
        Check("parent_r415_sealed",parent.get("status")==PARENT_SEALED,parent.get("status")),
        Check("parent_r415_r1_applied",parent.get("repair_revision")==PARENT_REVISION,parent.get("repair_revision")),
        Check("parent_next_action_matches_r416",parent.get("next_action")=="BUILD_R416_RECOVERED_METRIC_PROMOTION_GATE_AND_ARCANA_TARGET_SEMANTIC_PROTOCOL_FORMALIZATION",parent.get("next_action")),
        Check("parent_exact_four_p0_resolved",psum.get("p0_resolved_cell_count")==4,psum.get("p0_resolved_cell_count")),
        Check("parent_exact_two_p0_recovered",psum.get("p0_recovered_cell_count")==2,psum.get("p0_recovered_cell_count")),
        Check("parent_exact_two_p0_exhausted_to_p2",psum.get("p0_exhausted_reclassified_cell_count")==2,psum.get("p0_exhausted_reclassified_cell_count")),
        Check("parent_exact_59_p1_audited",targ.get("p1_cell_count")==59,targ.get("p1_cell_count")),
        Check("parent_exact_47_p1_source_candidate_cells",targ.get("cells_with_canonical_source_candidates")==47,targ.get("cells_with_canonical_source_candidates")),
        Check("parent_r416_plan_frozen",pplan.get("status")=="R415_R1_P0_CANDIDATE_REALIZATION_AND_TARGET_SOURCE_REGISTRY_FROZEN",pplan.get("status")),
        Check("policy_frozen",cfg.get("policy_freeze")=="FROZEN_PRE_PROMOTION_AND_TARGET_EXTRACTOR_IMPLEMENTATION",cfg.get("policy_freeze")),
        Check("engine_execution_forbidden",cfg.get("engine_execution_performed") is False),
        Check("canonical_state_unchanged",cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized",cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized",cfg.get("canonical_parameter_change_authorized") is False),
        Check("deep_off",cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden",cfg.get("majority_vote") is False),
    ]

    recovered=[r for r in rec.get("records") or [] if r.get("resolution_status")=="P0_RETAINED_RUNTIME_METRIC_RECOVERED"]
    metric_records=[]
    for r in recovered:
        eng,rc=_engine_from_record(r)
        disp=recovered_metric_disposition(str(r.get("domain") or ""),eng,rc)
        metric_records.append({
            "window_id":r.get("window_id"),"domain":r.get("domain"),"authorized_recovery_engine":r.get("authorized_recovery_engine"),
            "engine":eng,"recovery_class":rc,"source_record_semantic_status":r.get("semantic_status"),
            "disposition":disp,
        })

    protocols=cfg.get("domain_protocols") or {}
    target_records=[_target_protocol_record(r,protocols) for r in targ.get("records") or []]
    unknown=[{"window_id":r.get("window_id"),"domain":r.get("domain")} for r in target_records if r.get("protocol") is None]
    candidate_count=sum(r.get("candidate_artifact_count",0)>0 for r in target_records)
    nohit_count=sum(r.get("candidate_artifact_count",0)==0 for r in target_records)

    priority=(census.get("closure_priority_counts") or {})
    base_p2=int(priority.get("P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION",0) or 0)
    p3=int(priority.get("P3_NEW_EXTENSION_JOB_IN_NEW_NAMESPACE_NO_R42_FREEZE_MUTATION",0) or 0)
    exhausted=sum(r.get("resolution_status")=="P0_CANDIDATE_EXHAUSTED_RECLASSIFIED_TO_P2" for r in rec.get("records") or [])

    checks += [
        Check("exact_two_recovered_metrics_receive_promotion_disposition",len(metric_records)==2,len(metric_records)),
        Check("no_recovered_metric_auto_promoted",all(not r["disposition"].get("adjudicative_promotion_authorized") and not r["disposition"].get("promotion_performed") for r in metric_records)),
        Check("all_59_p1_cells_receive_domain_protocol",len(target_records)==59 and not unknown,{"records":len(target_records),"unknown":unknown}),
        Check("exact_47_candidate_source_cells_preserved",candidate_count==47,candidate_count),
        Check("exact_12_no_candidate_source_cells_preserved",nohit_count==12,nohit_count),
        Check("candidate_hits_not_promoted_to_targets",all(not r.get("adjudicative_target_authorized") and not r.get("target_value_materialized") for r in target_records)),
        Check("no_external_result_defines_arcana_target",all(r.get("external_result_used_to_define_target") is False for r in target_records)),
        Check("p2_backlog_includes_two_r415_exhausted_candidates",exhausted==2,exhausted),
        Check("p2_total_backlog_accounted",base_p2+exhausted==4,{"r414_p2":base_p2,"r415_exhausted":exhausted,"total":base_p2+exhausted}),
        Check("p3_frozen_extension_backlog_preserved",p3==6,p3),
        Check("no_readjudication_in_r416",cfg.get("rules",{}).get("no_readjudication_in_r416") is True),
        Check("no_target_leakage_rule",cfg.get("rules",{}).get("no_target_leakage") is True),
        Check("no_result_selected_transform",cfg.get("rules",{}).get("no_result_selected_transform") is True),
    ]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    metric_out={
        "stage":STAGE,"status":status,"recovered_metric_count":len(metric_records),"records":metric_records,
        "adjudicative_promotion_count":0,"promotion_performed":False,
        "interpretation":"R4.16 freezes semantic dispositions. Numerical/domain transforms remain deferred to R4.17; no raw derivative is promoted merely because it was recovered."
    }
    target_out={
        "stage":STAGE,"status":status,"p1_cell_count":len(target_records),"cells_with_source_candidates":candidate_count,
        "cells_without_source_candidates":nohit_count,"records":target_records,"target_value_materialization_performed":False,
        "adjudicative_target_count":0
    }
    plan={
        "stage":STAGE,"status":"R416_PROMOTION_AND_TARGET_SEMANTIC_PROTOCOL_FROZEN" if status==COMPLETE else BLOCKED,
        "r417_work_batches":{
            "A_RECOVERED_METRIC_DOMAIN_TRANSFORM_IMPLEMENTATION":{"cell_count":len(metric_records),"engine_execution_authorized":False,"readjudication_authorized":False},
            "B_CANONICAL_TARGET_EXTRACTOR_IMPLEMENTATION":{"cell_count":candidate_count,"source_candidate_only":True,"external_engine_results_forbidden_as_target_sources":True},
            "C_NO_SOURCE_CANDIDATE_TARGET_DESIGN":{"cell_count":nohit_count,"new_canonical_target_creation_not_authorized_in_r416":True},
            "D_P2_ADAPTER_BACKLOG":{"cell_count":base_p2+exhausted,"engine_execution_authorized":False,"note":"R4.17 may design, but not silently execute, symmetric adapter-enhancement reruns."},
            "E_P3_EXTENSION_JOB_BACKLOG":{"cell_count":p3,"r42_registry_mutation_forbidden":True}
        },
        "promotion_preconditions":[
            "metric identity and transform frozen before looking at adjudication outcome",
            "ARCANA target value/unit/time/space/population semantics explicitly extracted from canonical artifacts",
            "both sides share a declared comparability class DIRECT or NORMALIZABLE",
            "PROXY_ONLY remains contextual only",
            "readjudication occurs only in a later namespace after both gates pass"
        ],
        "canonical_change_authorized":False,"engine_execution_authorized":False,"next_action":NEXT
    }
    out={
        "stage":STAGE,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.d() for c in checks],
        "recovered_metric_promotion_gate_count":len(metric_records),"recovered_metric_adjudicative_promotion_count":0,
        "p1_protocolized_cell_count":len(target_records),"p1_source_candidate_cell_count":candidate_count,"p1_no_source_candidate_cell_count":nohit_count,
        "p2_backlog_cell_count":base_p2+exhausted,"p3_backlog_cell_count":p3,"engine_execution_performed":False,"canonical_state_changed":False,"next_action":NEXT
    }
    write(root/OUT/"R4_16_RECOVERED_METRIC_PROMOTION_GATE.json",metric_out)
    write(root/OUT/"R4_16_ARCANA_TARGET_SEMANTIC_PROTOCOL_REGISTRY.json",target_out)
    write(root/OUT/"R4_16_R417_EXECUTION_PLAN.json",plan)
    write(root/OUT/"R4_16_INTEGRATED_AUDIT.json",out)
    return out

def final_seal(root:Path)->dict[str,Any]:
    parent=load(root/PSEAL) if (root/PSEAL).exists() else {}
    audit=load(root/OUT/"R4_16_INTEGRATED_AUDIT.json") if (root/OUT/"R4_16_INTEGRATED_AUDIT.json").exists() else {}
    metric=load(root/OUT/"R4_16_RECOVERED_METRIC_PROMOTION_GATE.json") if (root/OUT/"R4_16_RECOVERED_METRIC_PROMOTION_GATE.json").exists() else {}
    targ=load(root/OUT/"R4_16_ARCANA_TARGET_SEMANTIC_PROTOCOL_REGISTRY.json") if (root/OUT/"R4_16_ARCANA_TARGET_SEMANTIC_PROTOCOL_REGISTRY.json").exists() else {}
    plan=load(root/OUT/"R4_16_R417_EXECUTION_PLAN.json") if (root/OUT/"R4_16_R417_EXECUTION_PLAN.json").exists() else {}
    checks=[
        Check("parent_r415_sealed",parent.get("status")==PARENT_SEALED,parent.get("status")),
        Check("r416_complete",audit.get("status")==COMPLETE,audit.get("status")),
        Check("r416_zero_process_failures",audit.get("checks_failed")==0,audit.get("checks_failed")),
        Check("exact_two_recovered_metric_dispositions",metric.get("recovered_metric_count")==2,metric.get("recovered_metric_count")),
        Check("zero_automatic_metric_promotions",metric.get("adjudicative_promotion_count")==0,metric.get("adjudicative_promotion_count")),
        Check("exact_59_target_protocol_records",targ.get("p1_cell_count")==59,targ.get("p1_cell_count")),
        Check("target_candidate_accounting_47_12",targ.get("cells_with_source_candidates")==47 and targ.get("cells_without_source_candidates")==12,{"with":targ.get("cells_with_source_candidates"),"without":targ.get("cells_without_source_candidates")}),
        Check("zero_automatic_target_promotions",targ.get("adjudicative_target_count")==0,targ.get("adjudicative_target_count")),
        Check("r417_plan_frozen",plan.get("status")=="R416_PROMOTION_AND_TARGET_SEMANTIC_PROTOCOL_FROZEN",plan.get("status")),
        Check("p2_backlog_4",audit.get("p2_backlog_cell_count")==4,audit.get("p2_backlog_cell_count")),
        Check("p3_backlog_6",audit.get("p3_backlog_cell_count")==6,audit.get("p3_backlog_cell_count")),
        Check("no_engine_execution",audit.get("engine_execution_performed") is False),
        Check("canonical_state_unchanged",audit.get("canonical_state_changed") is False),
        Check("next_action_present",audit.get("next_action")==NEXT,audit.get("next_action")),
    ]
    verdict="SEALED" if all(c.passed for c in checks) else "BLOCKED"
    status=SEALED if verdict=="SEALED" else BLOCKED
    out={
        "stage":STAGE,"audit":"FINAL_RECOVERED_METRIC_PROMOTION_GATE_AND_ARCANA_TARGET_SEMANTIC_PROTOCOL_FORMALIZATION",
        "status":status,"verdict":verdict,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.d() for c in checks],
        "summary":{
            "recovered_metric_disposition_count":metric.get("recovered_metric_count"),
            "recovered_metric_adjudicative_promotion_count":metric.get("adjudicative_promotion_count"),
            "p1_protocolized_cell_count":targ.get("p1_cell_count"),
            "p1_source_candidate_cell_count":targ.get("cells_with_source_candidates"),
            "p1_no_source_candidate_cell_count":targ.get("cells_without_source_candidates"),
            "p2_backlog_cell_count":audit.get("p2_backlog_cell_count"),"p3_backlog_cell_count":audit.get("p3_backlog_cell_count"),
            "engine_execution_performed":False,"canonical_state_changed":False,"canonical_replay_authorized":False,"canonical_parameter_change_authorized":False,"deep_biological_coupling":False,
            "next_action":NEXT
        },
        "next_action":NEXT
    }
    write(root/SEAL,out)
    return out
