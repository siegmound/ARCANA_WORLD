from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import csv, fnmatch, json, math, re

STAGE="v0.6D1-R4.15"
REPAIR_REVISION="R4.15-R1"
REPAIR_FINDING="R415_INITIAL_P0_RECOVERY_GATE_WAS_OVERBROAD_ACROSS_ALL_PRIMARY_ENGINES"
PARENT_SEALED="PASS_R414_MULTI_ENGINE_EVIDENCE_GAP_CLOSURE_AND_TARGETED_ADAPTER_ENHANCEMENT_PLAN_SEALED"
COMPLETE="PASS_R415_RETAINED_RUNTIME_METRIC_RECOVERY_AND_TARGET_SEMANTIC_MATERIALIZATION_AUDIT_COMPLETE"
SEALED="PASS_R415_RETAINED_RUNTIME_METRIC_RECOVERY_AND_TARGET_SEMANTIC_MATERIALIZATION_AUDIT_SEALED"
BLOCKED="BLOCKED_R415_PARENT_RECOVERY_OR_TARGET_MATERIALIZATION_FAILURE"
NEXT="BUILD_R416_RECOVERED_METRIC_PROMOTION_GATE_AND_ARCANA_TARGET_SEMANTIC_PROTOCOL_FORMALIZATION"
CFG=Path("configs/world1_r415_retained_metric_target_semantics_v0_6D1_R4_15.json")
PSEAL=Path("outputs/v0_6D1_R4_14_SEAL/R4_14_FINAL_SEAL_AUDIT.json")
CENSUS=Path("outputs/v0_6D1_R4_14/R4_14_EVIDENCE_GAP_CENSUS.json")
PLAN=Path("outputs/v0_6D1_R4_14/R4_14_TARGETED_ADAPTER_ENHANCEMENT_PLAN.json")
CAP=Path("outputs/v0_6D1_R4_14/R4_14_RETAINED_EVIDENCE_CAPABILITY_AUDIT.json")
OUT=Path("outputs/v0_6D1_R4_15")
SEAL=Path("outputs/v0_6D1_R4_15_SEAL/R4_15_FINAL_SEAL_AUDIT.json")

AUTHORIZED_RECOVERY_RE = re.compile(r"^RETAINED_(NEMO|SLIM|CDMETAPOP)_RUNTIME_METRIC_RECOVERY_CANDIDATE$")
SUPPORTED_RECOVERY_ENGINES={"NEMO","SLiM","CDMetaPOP"}

@dataclass(frozen=True)
class Check:
    name:str; passed:bool; detail:Any=None
    def d(self): return {"name":self.name,"pass":bool(self.passed),"detail":self.detail}

def load(p:Path): return json.loads(p.read_text(encoding="utf-8-sig"))
def write(p:Path,o:Any): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def _runtime_roots(root:Path, job_id:str, engine:str)->list[Path]:
    c=[]
    for rel in [Path("outputs/v0_6D1_R4_3/jobs")/job_id/"runtime_work",Path("outputs/v0_6D1_R4_7/jobs")/job_id/"runtime_work"]:
        p=root/rel
        if p.exists(): c.append(p)
    return c

def _files(roots:list[Path], names:list[str])->list[Path]:
    out=[]
    for b in roots:
        try:
            for p in b.rglob("*"):
                if p.is_file() and any(fnmatch.fnmatch(p.name,n) for n in names): out.append(p)
        except OSError:
            continue
    return sorted(set(out))

def _nemo_qfreq(path:Path)->dict[str,Any]:
    vals={}
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines()[1:]:
        t=line.split()
        if len(t)<5: continue
        try: pop=int(float(t[0])); locus=int(float(t[2])); f=float(t[4])
        except Exception: continue
        vals.setdefault(pop,{})[locus]=f
    pops=sorted(vals); common=sorted(set.intersection(*(set(vals[p]) for p in pops))) if pops else []
    if not common: return {"status":"NO_COMMON_LOCI"}
    het=[2*vals[p][l]*(1-vals[p][l]) for p in pops for l in common]
    gaps=[]
    if len(pops)>=2:
        gaps=[abs(vals[pops[0]][l]-vals[pops[1]][l]) for l in common]
    return {"status":"PASS","population_count":len(pops),"locus_count":len(common),"mean_expected_heterozygosity":sum(het)/len(het),"mean_between_population_frequency_gap":(sum(gaps)/len(gaps) if gaps else None)}

def _cdm_summary(path:Path)->dict[str,Any]:
    with path.open(newline="",encoding="utf-8-sig",errors="replace") as f: rows=list(csv.DictReader(f))
    if not rows: return {"status":"EMPTY"}
    def total(s):
        if s is None:return None
        z=str(s).split("|")[0].strip()
        try:return float(z)
        except:return None
    n=[total(r.get("N_Initial")) for r in rows]
    gr=[]
    for r in rows:
        try: gr.append(float(str(r.get("GrowthRate") or "nan").split("|")[0]))
        except: gr.append(float("nan"))
    start=n[0]
    final=(n[-1]*gr[-1]) if n[-1] is not None and math.isfinite(gr[-1]) else None
    return {"status":"PASS" if start is not None and final is not None else "PARTIAL","row_count":len(rows),"initial_population":start,"final_population":final,"population_ratio":(final/start if start and final is not None else None)}

def _slim_tree(path:Path)->dict[str,Any]:
    try:
        import tskit
        ts=tskit.load(str(path))
    except Exception as e:
        return {"status":"TSKIT_LOAD_FAILURE","error":repr(e)}
    alive=[]
    for ind in ts.individuals():
        ns=[int(n) for n in ind.nodes if int(n)>=0]
        if ns and min(float(ts.node(n).time) for n in ns)==0.0: alive.append(ind)
    nodes=[int(n) for ind in alive for n in ind.nodes if int(n)>=0 and float(ts.node(int(n)).time)==0.0]
    bypop={}
    for n in nodes: bypop.setdefault(int(ts.node(n).population),[]).append(n)
    div=float(ts.diversity(sample_sets=[nodes])[0]) if len(nodes)>=2 else 0.0
    out={"status":"PASS","alive_individuals":len(alive),"current_genome_nodes":len(nodes),"population_node_counts":{str(k):len(v) for k,v in sorted(bypop.items())},"diversity_per_site":div,"tree_nodes":int(ts.num_nodes),"tree_edges":int(ts.num_edges),"mutations":int(ts.num_mutations)}
    if len(bypop)>=2:
        ss=[v for _,v in sorted(bypop.items()) if len(v)>=2]
        if len(ss)>=2:
            try: out["fst_between_current_populations"]=float(ts.Fst(sample_sets=ss[:2]))
            except Exception: out["fst_between_current_populations"]=None
    return out

def _authorized_recovery_engine(gap:dict[str,Any])->str|None:
    action=str(gap.get("closure_action") or "")
    m=AUTHORIZED_RECOVERY_RE.match(action)
    if not m: return None
    token=m.group(1)
    return {"NEMO":"NEMO","SLIM":"SLiM","CDMETAPOP":"CDMetaPOP"}[token]

def _extract_engine_record(root:Path, gap:dict[str,Any], eng:str, jid:str, authorized_engine:str|None)->dict[str,Any]:
    roots=_runtime_roots(root,jid,eng)
    rec={
        "engine":eng,
        "job_id":jid,
        "runtime_roots":[str(x) for x in roots],
        "metrics":[],
        "required_for_r414_p0_candidate_realization":eng==authorized_engine,
    }
    if eng=="NEMO":
        fs=_files(roots,["r43_nemo_1.qfreq"])
        rec["metrics"]=[{"source":str(p),"recovered":_nemo_qfreq(p)} for p in fs]
        rec["recovery_class"]="ALLELE_FREQUENCY_DERIVATIVES_RECOVERED_RAW_ONLY"
    elif eng=="SLiM":
        fs=_files(roots,["r43.trees"])
        rec["metrics"]=[{"source":str(p),"recovered":_slim_tree(p)} for p in fs]
        rec["recovery_class"]="TREE_SEQUENCE_DERIVATIVES_RECOVERED_RAW_ONLY"
    elif eng=="CDMetaPOP":
        fs=_files(roots,["summary_popAllTime.csv"])
        rec["metrics"]=[{"source":str(p),"recovered":_cdm_summary(p)} for p in fs]
        rec["recovery_class"]="SUMMARY_POPULATION_DERIVATIVES_RECOVERED_RAW_ONLY"
    else:
        rec["recovery_class"]="NO_FROZEN_EXTRACTOR"
    rec["source_file_count"]=len(rec["metrics"])
    rec["pass"]=len(rec["metrics"])>0 and all(m["recovered"].get("status") in {"PASS","PARTIAL"} for m in rec["metrics"])
    return rec

def _recover_p0(root:Path,gap:dict[str,Any])->dict[str,Any]:
    engs=gap.get("primary_engines") or []
    rows=gap.get("primary_rows") or []
    auth_engine=_authorized_recovery_engine(gap)
    r414_hits=(gap.get("retained_runtime_hits") or {}).get(auth_engine,[]) if auth_engine else []
    result={
        "window_id":gap.get("window_id"),
        "domain":gap.get("domain"),
        "closure_action":gap.get("closure_action"),
        "authorized_recovery_engine":auth_engine,
        "r414_authorized_engine_retained_hit_count":len(r414_hits),
        "r414_authorized_engine_sample_hits":list(r414_hits)[:12],
        "engine_records":[],
        "adjudicative_promotion_authorized":False,
        "repair_revision":REPAIR_REVISION,
    }
    for eng in engs:
        jids=sorted({str(r.get("job_id")) for r in rows if r.get("engine")==eng and r.get("job_id")})
        for jid in jids:
            result["engine_records"].append(_extract_engine_record(root,gap,eng,jid,auth_engine))

    required=[r for r in result["engine_records"] if r.get("required_for_r414_p0_candidate_realization")]
    candidate_predeclared=bool(auth_engine and r414_hits)
    realized=bool(required) and all(r.get("pass") is True for r in required)
    result["candidate_predeclared_by_r414"]=candidate_predeclared
    result["required_engine_record_count"]=len(required)
    result["recovery_pass"]=realized
    # Backward-compatible meaning: pass means retained metric actually recovered.
    result["pass"]=realized

    if not auth_engine:
        result["resolution_status"]="UNRESOLVED_INVALID_R414_CLOSURE_ACTION"
        result["resolved"]=False
        result["next_priority"]=None
    elif not candidate_predeclared:
        result["resolution_status"]="UNRESOLVED_R414_AUTHORIZED_ENGINE_LACKED_PREDECLARED_RETAINED_HIT"
        result["resolved"]=False
        result["next_priority"]=None
    elif realized:
        result["resolution_status"]="P0_RETAINED_RUNTIME_METRIC_RECOVERED"
        result["resolved"]=True
        result["next_priority"]="R416_DOMAIN_TRANSFORM_PROMOTION_GATE"
    else:
        # R4.14 froze this as a *candidate*. If its authorized retained source cannot
        # be cleanly re-extracted, P0 has been exhausted; do not silently rerun.
        result["resolution_status"]="P0_CANDIDATE_EXHAUSTED_RECLASSIFIED_TO_P2"
        result["resolved"]=True
        result["next_priority"]="P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION"
        result["reclassification_reason"]="R414_PREDECLARED_RETAINED_CANDIDATE_COULD_NOT_BE_CLEANLY_RECOVERED_BY_FROZEN_DOMAIN_EXTRACTOR"
    result["semantic_status"]="RECOVERED_RAW_METRIC_REQUIRES_R416_DOMAIN_TRANSFORM_PROMOTION_GATE" if realized else "NO_ADJUDICATIVE_METRIC_RECOVERED_P2_RECLASSIFICATION_ONLY"
    return result

def _artifact_hits(root:Path, domain:str, cfg:dict[str,Any], limit=40)->list[str]:
    pats=(cfg.get("domain_artifact_hints") or {}).get(domain,[]); hits=[]
    for sr in cfg.get("canonical_artifact_search_roots") or []:
        b=root/sr
        if not b.exists(): continue
        for p in b.rglob("*"):
            if not p.is_file(): continue
            low=p.name.lower()
            if any(fnmatch.fnmatch(low,pat.lower()) for pat in pats):
                s=str(p).replace("\\","/")
                if "/v0_6D1_R4_" in s: continue
                hits.append(s)
                if len(hits)>=limit:return hits
    return hits

def build(root:Path)->dict[str,Any]:
    cfg=load(root/CFG); seal=load(root/PSEAL) if (root/PSEAL).exists() else {}; census=load(root/CENSUS) if (root/CENSUS).exists() else {}; plan=load(root/PLAN) if (root/PLAN).exists() else {}; cap=load(root/CAP) if (root/CAP).exists() else {}
    gaps=census.get("gaps") or []
    p0=[g for g in gaps if g.get("closure_priority")=="P0_RETAINED_RUNTIME_REEXTRACTION_NO_ENGINE_RERUN"]
    p1=[g for g in gaps if g.get("closure_priority")=="P1_ARCANA_TARGET_SEMANTIC_MATERIALIZATION_FROM_EXISTING_CANONICAL_ARTIFACTS"]
    checks=[
      Check("parent_r414_seal_present",(root/PSEAL).exists(),str(PSEAL)),Check("parent_r414_sealed",seal.get("status")==PARENT_SEALED,seal.get("status")),Check("parent_gap_count_71",census.get("gap_count")==71,census.get("gap_count")),Check("exact_p0_count_4",len(p0)==4,len(p0)),Check("exact_p1_count_59",len(p1)==59,len(p1)),Check("parent_plan_frozen",plan.get("status")=="R414_GAP_CLOSURE_PLAN_FROZEN",plan.get("status")),Check("parent_retained_candidate_count_4",cap.get("retained_reextraction_candidate_cell_count")==4,cap.get("retained_reextraction_candidate_cell_count")),Check("policy_frozen",cfg.get("policy_freeze")=="FROZEN_PRE_RECOVERY_EXECUTION",cfg.get("policy_freeze")),Check("r415_r1_candidate_scope_repair_enabled",cfg.get("r415_r1_repair",{}).get("authorized_recovery_engine_is_defined_by_r414_closure_action") is True),Check("r415_r1_candidate_exhaustion_reclassification_enabled",cfg.get("r415_r1_repair",{}).get("unrecoverable_predeclared_p0_candidate_reclassifies_to_p2_without_rerun") is True),Check("engine_execution_forbidden",cfg.get("engine_execution_performed") is False),Check("canonical_state_unchanged",cfg.get("canonical_state_changed") is False),Check("canonical_replay_not_authorized",cfg.get("canonical_replay_authorized") is False),Check("canonical_parameter_change_not_authorized",cfg.get("canonical_parameter_change_authorized") is False),Check("deep_off",cfg.get("deep_biological_coupling") is False),Check("majority_vote_forbidden",cfg.get("majority_vote") is False)]
    if any(not c.passed for c in checks):
        out={"stage":STAGE,"repair_revision":REPAIR_REVISION,"status":BLOCKED,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.d() for c in checks],"canonical_state_changed":False}
        write(root/OUT/"R4_15_INTEGRATED_AUDIT.json",out); return out

    recovered=[_recover_p0(root,g) for g in p0]
    target=[]
    for g in p1:
        hits=_artifact_hits(root,str(g.get("domain")),cfg)
        target.append({"window_id":g.get("window_id"),"domain":g.get("domain"),"root_cause":g.get("root_cause"),"closure_action":g.get("closure_action"),"primary_engines":g.get("primary_engines"),"candidate_artifact_hits":hits,"candidate_artifact_count":len(hits),"materialization_status":"CANONICAL_SOURCE_CANDIDATES_FOUND_REQUIRES_EXPLICIT_TRANSFORM" if hits else "NO_CANONICAL_SOURCE_CANDIDATE_FOUND","adjudicative_target_authorized":False})

    p0pass=sum(bool(x.get("recovery_pass")) for x in recovered)
    p0resolved=sum(bool(x.get("resolved")) for x in recovered)
    p0exhausted=sum(x.get("resolution_status")=="P0_CANDIDATE_EXHAUSTED_RECLASSIFIED_TO_P2" for x in recovered)
    targethits=sum(1 for x in target if x["candidate_artifact_count"]>0)
    unresolved=[{"window_id":x.get("window_id"),"domain":x.get("domain"),"status":x.get("resolution_status")} for x in recovered if not x.get("resolved")]
    scope_mismatch=[{"window_id":x.get("window_id"),"domain":x.get("domain"),"authorized":x.get("authorized_recovery_engine")} for x in recovered if x.get("authorized_recovery_engine") not in SUPPORTED_RECOVERY_ENGINES]

    checks += [
      Check("all_four_p0_cells_attempted",len(recovered)==4,len(recovered)),
      Check("all_four_p0_candidates_resolved",p0resolved==4,{"resolved":p0resolved,"recovered":p0pass,"exhausted_to_p2":p0exhausted,"total":4}),
      Check("all_p0_authorized_recovery_engines_supported",not scope_mismatch,scope_mismatch),
      Check("no_p0_candidate_silently_dropped",not unresolved,unresolved),
      Check("all_recovered_metrics_nonadjudicative_until_r416",all(x.get("adjudicative_promotion_authorized") is False for x in recovered)),
      Check("all_exhausted_p0_candidates_reclassified_to_p2",all(x.get("next_priority")=="P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION" for x in recovered if not x.get("recovery_pass"))),
      Check("all_59_p1_cells_audited",len(target)==59,len(target)),
      Check("all_p1_targets_nonadjudicative_until_explicit_transform",all(x.get("adjudicative_target_authorized") is False for x in target)),
      Check("no_engine_execution",cfg.get("engine_execution_performed") is False),
      Check("no_target_leakage_rule",cfg.get("rules",{}).get("no_target_leakage") is True),
      Check("proxy_not_promoted",cfg.get("rules",{}).get("proxy_only_not_promotable") is True),
    ]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    registry={"stage":STAGE,"repair_revision":REPAIR_REVISION,"repair_finding":REPAIR_FINDING,"status":status,"p0_cell_count":4,"resolved_p0_cell_count":p0resolved,"recovered_p0_cell_count":p0pass,"exhausted_reclassified_p0_cell_count":p0exhausted,"records":recovered,"engine_execution_performed":False,"adjudicative_promotion_performed":False}
    targets={"stage":STAGE,"repair_revision":REPAIR_REVISION,"status":status,"p1_cell_count":59,"cells_with_canonical_source_candidates":targethits,"cells_without_candidate_hits":59-targethits,"records":target,"target_promotion_performed":False}
    r416_recovered=[{"window_id":x.get("window_id"),"domain":x.get("domain"),"authorized_recovery_engine":x.get("authorized_recovery_engine"),"resolution_status":x.get("resolution_status")} for x in recovered if x.get("recovery_pass")]
    p2_backlog=[{"window_id":x.get("window_id"),"domain":x.get("domain"),"authorized_recovery_engine":x.get("authorized_recovery_engine"),"resolution_status":x.get("resolution_status"),"next_priority":x.get("next_priority")} for x in recovered if not x.get("recovery_pass")]
    plan2={"stage":STAGE,"repair_revision":REPAIR_REVISION,"status":"R415_R1_P0_CANDIDATE_REALIZATION_AND_TARGET_SOURCE_REGISTRY_FROZEN" if status==COMPLETE else BLOCKED,"r416_required_gates":["DOMAIN_SPECIFIC_RECOVERED_METRIC_TRANSFORM_MUST_BE_FROZEN_PRE_PROMOTION","ARCANA_TARGET_VALUE_UNIT_TEMPORAL_AND_SPATIAL_BASIS_MUST_BE_EXPLICIT","NO_EXTERNAL_RESULT_MAY_DEFINE_ARCANA_TARGET","PROXY_ONLY_REMAINS_NONADJUDICATIVE","READJUDICATION_ONLY_AFTER_BOTH_METRIC_AND_TARGET_GATES_PASS"],"p0_resolved_cells":p0resolved,"p0_recovered_cells":p0pass,"p0_exhausted_reclassified_to_p2":p0exhausted,"r416_recovered_metric_promotion_batch":r416_recovered,"p2_reclassified_backlog":p2_backlog,"p1_source_candidate_cells":targethits,"engine_rerun_authorized":False,"canonical_change_authorized":False,"next_action":NEXT}
    out={"stage":STAGE,"repair_revision":REPAIR_REVISION,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.d() for c in checks],"parent_gap_count":71,"p0_resolved_cell_count":p0resolved,"p0_recovered_cell_count":p0pass,"p0_exhausted_reclassified_cell_count":p0exhausted,"p1_target_source_candidate_cell_count":targethits,"engine_execution_performed":False,"canonical_state_changed":False,"next_action":NEXT}
    write(root/OUT/"R4_15_RETAINED_RUNTIME_METRIC_RECOVERY.json",registry); write(root/OUT/"R4_15_ARCANA_TARGET_SOURCE_CANDIDATE_REGISTRY.json",targets); write(root/OUT/"R4_15_R416_PROMOTION_GATE_PLAN.json",plan2); write(root/OUT/"R4_15_INTEGRATED_AUDIT.json",out); return out

def final_seal(root:Path)->dict[str,Any]:
    parent=load(root/PSEAL) if (root/PSEAL).exists() else {}; audit=load(root/OUT/"R4_15_INTEGRATED_AUDIT.json") if (root/OUT/"R4_15_INTEGRATED_AUDIT.json").exists() else {}; rec=load(root/OUT/"R4_15_RETAINED_RUNTIME_METRIC_RECOVERY.json") if (root/OUT/"R4_15_RETAINED_RUNTIME_METRIC_RECOVERY.json").exists() else {}; targ=load(root/OUT/"R4_15_ARCANA_TARGET_SOURCE_CANDIDATE_REGISTRY.json") if (root/OUT/"R4_15_ARCANA_TARGET_SOURCE_CANDIDATE_REGISTRY.json").exists() else {}; plan=load(root/OUT/"R4_15_R416_PROMOTION_GATE_PLAN.json") if (root/OUT/"R4_15_R416_PROMOTION_GATE_PLAN.json").exists() else {}
    checks=[
      Check("parent_r414_sealed",parent.get("status")==PARENT_SEALED,parent.get("status")),
      Check("r415_r1_repair_applied",audit.get("repair_revision")==REPAIR_REVISION,audit.get("repair_revision")),
      Check("r415_complete",audit.get("status")==COMPLETE,audit.get("status")),
      Check("zero_process_failures",audit.get("checks_failed")==0,audit.get("checks_failed")),
      Check("exact_four_p0_candidates_resolved",rec.get("resolved_p0_cell_count")==4,rec.get("resolved_p0_cell_count")),
      Check("p0_recovery_and_exhaustion_accounting_complete",(rec.get("recovered_p0_cell_count",0)+rec.get("exhausted_reclassified_p0_cell_count",0))==4,{"recovered":rec.get("recovered_p0_cell_count"),"exhausted":rec.get("exhausted_reclassified_p0_cell_count")}),
      Check("exact_59_p1_audited",targ.get("p1_cell_count")==59,targ.get("p1_cell_count")),
      Check("no_metric_promotion",rec.get("adjudicative_promotion_performed") is False),
      Check("no_target_promotion",targ.get("target_promotion_performed") is False),
      Check("r416_plan_frozen",plan.get("status")=="R415_R1_P0_CANDIDATE_REALIZATION_AND_TARGET_SOURCE_REGISTRY_FROZEN",plan.get("status")),
      Check("no_engine_execution",audit.get("engine_execution_performed") is False),
      Check("canonical_state_unchanged",audit.get("canonical_state_changed") is False),
      Check("next_action_present",audit.get("next_action")==NEXT,audit.get("next_action")),
    ]
    ok=all(c.passed for c in checks)
    out={"stage":STAGE,"repair_revision":REPAIR_REVISION,"audit":"FINAL_RETAINED_RUNTIME_METRIC_RECOVERY_AND_ARCANA_TARGET_SEMANTIC_MATERIALIZATION_AUDIT","status":SEALED if ok else BLOCKED,"verdict":"SEALED" if ok else "BLOCKED","checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.d() for c in checks],"summary":{"p0_resolved_cell_count":rec.get("resolved_p0_cell_count"),"p0_recovered_cell_count":rec.get("recovered_p0_cell_count"),"p0_exhausted_reclassified_cell_count":rec.get("exhausted_reclassified_p0_cell_count"),"p1_target_source_candidate_cell_count":targ.get("cells_with_canonical_source_candidates"),"engine_execution_performed":False,"canonical_state_changed":False,"canonical_replay_authorized":False,"canonical_parameter_change_authorized":False,"deep_biological_coupling":False,"next_action":NEXT},"next_action":NEXT}
    write(root/SEAL,out); return out
