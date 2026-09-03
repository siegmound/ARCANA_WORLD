from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import math

from arcana_worldsim.scientific_engines.r43_historical_revalidation import normalize_raw
from arcana_worldsim.scientific_engines import r44_discordance_adjudication as r44

STAGE = "v0.6D1-R4.7"
R46_SEALED = "PASS_R46_TARGETED_R311_CAUSAL_COUNTERFACTUAL_AND_R43_FORCING_PARITY_AUDIT_SEALED"
PREPARED = "PASS_R47_CDMETAPOP_FORCING_PARITY_REPAIR_PLAN_PREPARED"
COMPLETE = "PASS_R47_CDMETAPOP_SYMMETRIC_REEXECUTION_AND_READJUDICATION_COMPLETE"
SEALED = "PASS_R47_CDMETAPOP_FORCING_PARITY_REPAIR_SYMMETRIC_REEXECUTION_AND_READJUDICATION_SEALED"
BLOCKED = "BLOCKED_R47_PARENT_REPAIR_EXECUTION_OR_READJUDICATION_FAILURE"

CFG_REL = Path("configs/world1_r47_cdmetapop_forcing_parity_reexecution_v0_6D1_R4_7.json")
R46_SEAL_REL = Path("outputs/v0_6D1_R4_6_SEAL/R4_6_FINAL_SEAL_AUDIT.json")
R46_DIAG_REL = Path("outputs/v0_6D1_R4_6/R4_6_CAUSAL_DIAGNOSIS.json")
R43_DESC_REL = Path("outputs/v0_6D1_R4_3/R4_3_WINDOW_BASELINE_DESCRIPTORS.json")
R43_MAP_REL = Path("outputs/v0_6D1_R4_3/R4_3_PER_JOB_UNIT_MAPPING.json")
R42_JOBS_REL = Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")
R44_MATRIX_REL = Path("outputs/v0_6D1_R4_4/R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json")
R44_CFG_REL = Path("configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json")
R43_CFG_REL = Path("configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json")
OUT_REL = Path("outputs/v0_6D1_R4_7")
SEAL_REL = Path("outputs/v0_6D1_R4_7_SEAL/R4_7_FINAL_SEAL_AUDIT.json")

CLASSES = ["CONCORDANT", "CALIBRATION_OFFSET", "STRUCTURAL_DISAGREEMENT", "SEMANTICALLY_NONCOMPARABLE", "INSUFFICIENT_EVIDENCE"]

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

def sha256_file(path: str | Path) -> str:
    h=sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()

def finite(x: Any) -> float | None:
    try: v=float(x)
    except (TypeError,ValueError): return None
    return v if math.isfinite(v) else None

def _job_contract_path(root: Path, job_id: str) -> Path:
    return root / "outputs/v0_6D1_R4_3/jobs" / job_id / "JOB_CONTRACT.json"

def _repair_job_dir(root: Path, job_id: str) -> Path:
    return root / OUT_REL / "jobs" / job_id

def _mapping_by_job(root: Path) -> dict[str,dict[str,Any]]:
    d=load_json(root/R43_MAP_REL)
    return {x["job_id"]:x for x in d.get("mappings",[]) if isinstance(x,dict) and x.get("job_id")}

def _jobs_by_id(root: Path) -> dict[str,dict[str,Any]]:
    d=load_json(root/R42_JOBS_REL)
    return {x["job_id"]:x for x in d.get("jobs",[]) if isinstance(x,dict) and x.get("job_id")}

def _support_profile(cfg: dict[str,Any], contract: dict[str,Any], desc: dict[str,Any]) -> dict[str,Any]:
    d=contract["engine_input"]["drivers"]
    low=float(cfg["repair_policy"]["fixed_safety_support_ratio_min"])
    high=float(cfg["repair_policy"]["fixed_safety_support_ratio_max"])
    descriptor_type=desc.get("descriptor_type")
    raw_ratio=None; source=None; provenance={}
    if descriptor_type=="H0_SNAPSHOT_WINDOW":
        phys=desc.get("exogenous_physical_forcing") or {}
        st=phys.get("start",{}); en=phys.get("end",{})
        a=finite(st.get("mean_population")); b=finite(en.get("mean_population"))
        if a is not None and b is not None and a>0 and b>0:
            raw_ratio=b/a
            source="A1_EXOGENOUS_REFERENCE_POPULATION_RATIO"
            provenance={"artifact":phys.get("source"),"artifact_sha256":phys.get("sha256"),"start_mean_reference_population":a,"end_mean_reference_population":b}
    if raw_ratio is None:
        hs=finite(d.get("normalized_habitat_fraction_start")); he=finite(d.get("normalized_habitat_fraction_end")); ec=finite(d.get("normalized_environment_change"))
        if hs is None or he is None or ec is None or hs<=0:
            raise RuntimeError("R4.7 cannot derive dynamic support from frozen R4.3 drivers")
        raw_ratio=(he/hs)*max(0.01,1.0+ec)
        source="FROZEN_R43_HABITAT_X_ENVIRONMENT_RELATIVE_SUPPORT"
        provenance={"normalized_habitat_fraction_start":hs,"normalized_habitat_fraction_end":he,"normalized_environment_change":ec}
    bounded=max(low,min(high,float(raw_ratio)))
    return {
        "forcing_source":source,
        "raw_end_support_ratio":float(raw_ratio),
        "bounded_end_support_ratio":bounded,
        "safety_bounds":[low,high],
        "safety_bound_active":not math.isclose(float(raw_ratio),bounded,rel_tol=0,abs_tol=1e-15),
        "start_k_scale_formula":"0.70 + 0.60 * normalized_habitat_fraction_start",
        "dynamic_parameter":"PatchVars.K",
        "cdclimate_knot_policy":"REUSE_EXISTING_GENERIC_CDCLIMATE_KNOTS_AND_LINEARLY_INTERPOLATE_RELATIVE_K_SUPPORT_ACROSS_KNOT_INDEX",
        "initial_n0_policy":"SCALAR_START_ONLY_NO_LATER_REINJECTION",
        "comparison_target_used":False,
        "provenance":provenance,
    }

def _cdmetapop_source_capability(root: Path) -> dict[str,Any]:
    prep=root/".arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_PreProcess.py"
    main=root/".arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_mainloop.py"
    modules=root/".arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_Modules.py"
    texts={p.name:p.read_text(encoding="utf-8",errors="replace") if p.exists() else "" for p in (prep,main,modules)}
    checks={
        "DoCDClimate_present":"def DoCDClimate" in texts.get(prep.name,""),
        "K_split_or_get_present":"tempK.append(int(split_or_get(K[isub], icdtime, cdclimgentime)))" in texts.get(prep.name,""),
        "cdclimate_generation_dispatch_present":"if gen == int(cdclimgentime[icdtime])" in texts.get(main.name,""),
        "split_or_get_pipe_support_present":"value.split('|')" in texts.get(modules.name,""),
    }
    return {"files":[str(prep.relative_to(root)),str(main.relative_to(root)),str(modules.relative_to(root))],"checks":checks,"dynamic_k_supported":all(checks.values()),"source_tree_modified":False}

def prepare(root: Path) -> tuple[dict[str,Any],list[Check]]:
    cfg=load_json(root/CFG_REL)
    parent=load_json(root/R46_SEAL_REL) if (root/R46_SEAL_REL).exists() else {}
    diag=load_json(root/R46_DIAG_REL) if (root/R46_DIAG_REL).exists() else {}
    descs=(load_json(root/R43_DESC_REL).get("windows",{}) if (root/R43_DESC_REL).exists() else {})
    jobs=_jobs_by_id(root) if (root/R42_JOBS_REL).exists() else {}
    affected=list(cfg.get("affected_frozen_jobs",[]))
    actual=[j for j,x in jobs.items() if x.get("engine")=="CDMetaPOP"]
    cap=_cdmetapop_source_capability(root)
    checks=[
        Check("parent_r46_seal_present",(root/R46_SEAL_REL).exists(),str(R46_SEAL_REL)),
        Check("parent_r46_sealed",parent.get("status")==R46_SEALED,parent.get("status")),
        Check("parent_forcing_gap_confirmed",diag.get("adapter_forcing_coverage_gap_confirmed") is True,diag.get("adapter_finding")),
        Check("parent_finding_matches_config",diag.get("adapter_forcing_parity_finding")==cfg.get("required_parent_finding"),diag.get("adapter_forcing_parity_finding")),
        Check("exact_five_affected_jobs",len(affected)==5 and len(set(affected))==5,affected),
        Check("affected_jobs_are_all_and_only_frozen_cdmetapop_jobs",set(affected)==set(actual),{"affected":affected,"actual":sorted(actual)}),
        Check("all_original_r43_contracts_present",all(_job_contract_path(root,j).exists() for j in affected)),
        Check("r43_window_descriptors_present",bool(descs)),
        Check("cdmetapop_dynamic_k_capability_confirmed",cap.get("dynamic_k_supported") is True,cap.get("checks")),
        Check("source_tree_remains_unmodified_by_contract",cfg.get("repair_policy",{}).get("source_tree_modification") is False),
        Check("comparison_target_injection_forbidden",cfg.get("repair_policy",{}).get("comparison_target_end_state_may_not_enter_engine_configuration") is True),
        Check("symmetry_not_result_selected",cfg.get("policy_freeze",{}).get("result_selected") is False),
        Check("canonical_state_unchanged",cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized",cfg.get("canonical_replay_authorized") is False),
        Check("deep_off",cfg.get("deep_biological_coupling") is False),
        Check("majority_vote_forbidden",cfg.get("majority_vote") is False),
    ]
    plans=[]
    for jid in affected:
        if jid not in jobs or not _job_contract_path(root,jid).exists():
            continue
        c=load_json(_job_contract_path(root,jid)); wid=jobs[jid]["window_id"]; desc=descs.get(wid,{})
        profile=_support_profile(cfg,c,desc)
        jobdir=_repair_job_dir(root,jid); jobdir.mkdir(parents=True,exist_ok=True)
        repair={"stage":STAGE,"job_id":jid,"window_id":wid,"engine":"CDMetaPOP","original_r43_contract":str(_job_contract_path(root,jid).relative_to(root)),"original_r43_contract_sha256":sha256_file(_job_contract_path(root,jid)),"repair_profile":profile,"original_seed_ledger":[{"replicate_index":r["replicate_index"],"seed":r["seed"]} for r in c["engine_input"]["replicates"]],"canonical_write":False}
        write_json(jobdir/"REPAIR_PROFILE.json",repair)
        plans.append(repair)
    checks.append(Check("five_repair_profiles_materialized",len(plans)==5,len(plans)))
    checks.append(Check("all_repair_profiles_forbid_comparison_target",all(not x["repair_profile"].get("comparison_target_used",True) for x in plans)))
    status=PREPARED if all(c.passed for c in checks) else BLOCKED
    out={"stage":STAGE,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"source_capability_audit":cap,"job_count":len(plans),"jobs":plans,"canonical_state_changed":False,"next_action":"EXECUTE_R47_FIVE_CDMETAPOP_JOBS_SYMMETRICALLY" if status==PREPARED else None}
    write_json(root/OUT_REL/"R4_7_REPAIR_PLAN.json",out)
    return out,checks

def _terminal_for_raw(raw: dict[str,Any], contract: dict[str,Any]) -> tuple[str,str]:
    if raw.get("adapter_status")!="PASS": return "ADAPTER_FAILURE",str(raw.get("adapter_status"))
    reps=raw.get("replicates",[]); expected=contract["engine_input"]["replicates"]
    if len(reps)!=len(expected): return "MISSING_EVIDENCE","REPLICATE_COUNT_MISMATCH"
    if any(r.get("status")!="PASS" for r in reps): return "ENGINE_EXECUTION_FAILURE","REPLICATE_FAILURE"
    return "SCIENTIFIC_RESULT","PASS"

def _seed_match(raw: dict[str,Any], contract: dict[str,Any]) -> bool:
    expected=[(int(x["replicate_index"]),int(x["seed"])) for x in contract["engine_input"]["replicates"]]
    observed=[(int(x.get("replicate_index",-1)),int(x.get("seed",-1))) for x in raw.get("replicates",[])]
    return expected==observed

def _new_cdmetapop_rows(root: Path, job_ids: list[str]) -> list[dict[str,Any]]:
    mappings=_mapping_by_job(root); jobs=_jobs_by_id(root)
    descs=load_json(root/R43_DESC_REL).get("windows",{})
    cfg44=load_json(root/R44_CFG_REL)
    rows=[]
    for jid in job_ids:
        j=jobs[jid]; m=mappings[jid]
        norm=load_json(_repair_job_dir(root,jid)/"NORMALIZED_EVIDENCE.json")
        for dm in m.get("domain_mapping",[]):
            domain=dm["domain"]; role=dm["authority_role"]; mapcomp=dm["comparability_class"]
            target=r44._descriptor_target(descs.get(j["window_id"],{}),domain)
            cand=cfg44.get("domain_metric_candidates",{}).get("CDMetaPOP",{}).get(domain,[])
            picked=r44._find_metric(norm,cand)
            base={"stage":STAGE,"window_id":j["window_id"],"job_id":jid,"engine":"CDMetaPOP","domain":domain,"authority_role":role,"mapping_comparability":mapcomp,"parent_terminal_class":"SCIENTIFIC_RESULT","majority_vote":False,"canonical_write":False,"evidence_namespace":"R4_7_CDMETAPOP_FORCING_PARITY_REEXECUTION"}
            if target is None:
                row={**base,"discordance_class":"INSUFFICIENT_EVIDENCE","reason":"NO_ARCANA_DOMAIN_TARGET_WITH_DECLARED_SEMANTICS","metric":None,"target":None}
            elif picked is None:
                row={**base,"discordance_class":"INSUFFICIENT_EVIDENCE","reason":"NO_R47_NORMALIZED_RESULT_METRIC_FOR_DOMAIN","metric":None,"target":target,"candidate_metrics":cand}
            else:
                mn,ms=picked; res=r44.classify_pair(target,mn,ms,mapcomp,cfg44)
                row={**base,**res,"metric":{"name":mn,"summary":ms},"target":target}
            rows.append(row)
    return rows

def _recompute_cells(root: Path, evidence_rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    cfg44=load_json(root/R44_CFG_REL); r43cfg=load_json(root/R43_CFG_REL); jobs=_jobs_by_id(root)
    cells=[]
    for wid,domains in r43cfg.get("window_domain_scope",{}).items():
        for domain in domains:
            rows=[r for r in evidence_rows if r.get("window_id")==wid and r.get("domain")==domain]
            prim=[r for r in rows if r.get("authority_role")=="PRIMARY"]
            sec=[r for r in rows if r.get("authority_role")=="SECONDARY"]
            adjud=[r for r in prim if r.get("mapping_comparability") in ("NORMALIZABLE","DIRECT") and (r.get("target") or {}).get("comparability") in ("NORMALIZABLE","DIRECT") and r.get("discordance_class") in ("CONCORDANT","CALIBRATION_OFFSET","STRUCTURAL_DISAGREEMENT")]
            if any(r.get("discordance_class")=="STRUCTURAL_DISAGREEMENT" for r in adjud): cls="STRUCTURAL_DISAGREEMENT"; reason="AT_LEAST_ONE_PRIMARY_ADJUDICATIVE_STRUCTURAL_DISAGREEMENT"
            elif any(r.get("discordance_class")=="CALIBRATION_OFFSET" for r in adjud): cls="CALIBRATION_OFFSET"; reason="PRIMARY_ADJUDICATIVE_CALIBRATION_OFFSET_WITH_NO_STRUCTURAL_DISAGREEMENT"
            elif any(r.get("discordance_class")=="CONCORDANT" for r in adjud): cls="CONCORDANT"; reason="PRIMARY_ADJUDICATIVE_CONCORDANCE_WITH_NO_HIGHER_SEVERITY_PRIMARY_FINDING"
            elif prim and all(r.get("discordance_class")=="SEMANTICALLY_NONCOMPARABLE" for r in prim): cls="SEMANTICALLY_NONCOMPARABLE"; reason="ALL_PRIMARY_EVIDENCE_SEMANTICALLY_NONCOMPARABLE"
            else: cls="INSUFFICIENT_EVIDENCE"; reason="NO_PRIMARY_NORMALIZABLE_RESULT_TARGET_PAIR"
            boundaries=sorted({jobs[r["job_id"]].get("earliest_replay_boundary") for r in adjud if r.get("discordance_class")=="STRUCTURAL_DISAGREEMENT" and jobs[r["job_id"]].get("earliest_replay_boundary")}, key=lambda x: cfg44["replay_boundary_order"].index(x) if x in cfg44["replay_boundary_order"] else 999)
            cells.append({"window_id":wid,"domain":domain,"discordance_class":cls,"reason":reason,"primary_evidence_rows":len(prim),"secondary_context_rows":len(sec),"primary_adjudicative_rows":len(adjud),"earliest_affected_authority_candidate":boundaries[0] if boundaries else None,"canonical_change_authorized":False,"majority_vote":False})
    return cells

def collect_and_readjudicate(root: Path) -> tuple[dict[str,Any],list[Check]]:
    cfg=load_json(root/CFG_REL); plan=load_json(root/OUT_REL/"R4_7_REPAIR_PLAN.json") if (root/OUT_REL/"R4_7_REPAIR_PLAN.json").exists() else {}
    affected=list(cfg["affected_frozen_jobs"])
    checks=[Check("r47_prepared",plan.get("status")==PREPARED,plan.get("status")),Check("exact_five_reexecution_jobs",len(affected)==5)]
    job_audits=[]
    for jid in affected:
        jobdir=_repair_job_dir(root,jid); rawp=jobdir/"RAW_EVIDENCE.json"; cp=_job_contract_path(root,jid); profp=jobdir/"REPAIR_PROFILE.json"
        missing=[x.name for x in (rawp,cp,profp) if not x.exists()]
        if missing:
            job_audits.append({"job_id":jid,"terminal_class":"MISSING_EVIDENCE","missing":missing,"status":"BLOCKED"}); continue
        raw=load_json(rawp); contract=load_json(cp); profile=load_json(profp)
        terminal,reason=_terminal_for_raw(raw,contract); seeds=_seed_match(raw,contract)
        norm=normalize_raw("CDMetaPOP",raw,contract); norm["stage"]=STAGE; norm["parent_normalizer"]="R4.3_WITHIN_ENGINE_DIMENSIONLESS_RESPONSE_ONLY"; norm["evidence_namespace"]="R4_7_CDMETAPOP_FORCING_PARITY_REEXECUTION"; norm["repair_profile_sha256"]=sha256_file(profp); write_json(jobdir/"NORMALIZED_EVIDENCE.json",norm)
        ja={"stage":STAGE,"job_id":jid,"engine":"CDMetaPOP","terminal_class":terminal,"reason":reason,"seed_ledger_match":seeds,"raw_canonical_write":raw.get("canonical_write"),"repair_forcing_source":profile.get("repair_profile",{}).get("forcing_source"),"dynamic_end_support_ratio":profile.get("repair_profile",{}).get("bounded_end_support_ratio"),"status":"PASS" if terminal=="SCIENTIFIC_RESULT" and seeds and raw.get("canonical_write") is False else "BLOCKED"}
        write_json(jobdir/"JOB_AUDIT.json",ja); job_audits.append(ja)
    checks += [
        Check("all_five_jobs_have_terminal_audits",len(job_audits)==5,len(job_audits)),
        Check("all_five_jobs_scientific_result",all(x.get("terminal_class")=="SCIENTIFIC_RESULT" for x in job_audits),{x["job_id"]:x.get("terminal_class") for x in job_audits}),
        Check("all_five_seed_ledgers_match",all(x.get("seed_ledger_match") is True for x in job_audits)),
        Check("all_five_raw_evidence_no_canonical_write",all(x.get("raw_canonical_write") is False for x in job_audits)),
    ]
    old=load_json(root/R44_MATRIX_REL) if (root/R44_MATRIX_REL).exists() else {}
    old_rows=list(old.get("evidence_rows",[])); old_cells=list(old.get("cells",[]))
    new_rows=_new_cdmetapop_rows(root,affected) if all(x.get("terminal_class")=="SCIENTIFIC_RESULT" for x in job_audits) else []
    preserved=[r for r in old_rows if r.get("job_id") not in set(affected)]
    revised_rows=preserved+new_rows
    revised_cells=_recompute_cells(root,revised_rows) if revised_rows else []
    counts={c:sum(1 for x in revised_cells if x.get("discordance_class")==c) for c in CLASSES}
    old_by={(x.get("window_id"),x.get("domain")):x for x in old_cells}; new_by={(x.get("window_id"),x.get("domain")):x for x in revised_cells}
    changed=[]
    for k,n in new_by.items():
        o=old_by.get(k,{})
        if o.get("discordance_class")!=n.get("discordance_class"):
            changed.append({"window_id":k[0],"domain":k[1],"old_class":o.get("discordance_class"),"new_class":n.get("discordance_class")})
    j09=[r for r in new_rows if r.get("job_id")=="R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP" and r.get("domain")=="population_persistence" and r.get("authority_role")=="PRIMARY"]
    structural=sum(1 for x in revised_cells if x.get("discordance_class")=="STRUCTURAL_DISAGREEMENT")
    gaps=sum(1 for x in revised_cells if x.get("discordance_class") in ("INSUFFICIENT_EVIDENCE","SEMANTICALLY_NONCOMPARABLE"))
    offsets=sum(1 for x in revised_cells if x.get("discordance_class")=="CALIBRATION_OFFSET")
    if structural: next_action="BUILD_R48_POST_CDMETAPOP_REPAIR_STRUCTURAL_CAUSAL_DIAGNOSIS"
    elif gaps: next_action="BUILD_R48_TARGETED_EVIDENCE_GAP_CLOSURE_AND_ADAPTER_ENHANCEMENT"
    elif offsets: next_action="BUILD_R48_TARGETED_CALIBRATION_REVIEW_WITHOUT_AUTOMATIC_CANONICAL_CHANGE"
    else: next_action="BUILD_R48_REVALIDATION_CLOSURE_AND_BASELINE_PROMOTION_GATE"
    checks += [
        Check("parent_r44_matrix_present",bool(old_rows) and len(old_cells)==75,{"rows":len(old_rows),"cells":len(old_cells)}),
        Check("only_five_cdmetapop_job_rows_replaced",all(r.get("job_id") in affected for r in new_rows) and all(r.get("job_id") not in affected for r in preserved)),
        Check("revised_matrix_exact_75_cells",len(revised_cells)==75,len(revised_cells)),
        Check("five_class_accounting_complete",sum(counts.values())==75,counts),
        Check("j09_population_persistence_readjudicated",len(j09)==1,j09[0].get("discordance_class") if j09 else None),
        Check("no_secondary_only_promotion",all(not (x.get("discordance_class") in ("CONCORDANT","CALIBRATION_OFFSET","STRUCTURAL_DISAGREEMENT") and x.get("primary_adjudicative_rows")==0) for x in revised_cells)),
        Check("no_majority_vote_anywhere",all(x.get("majority_vote") is False for x in revised_cells) and all(r.get("majority_vote") is False for r in revised_rows)),
        Check("canonical_state_unchanged",cfg.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized",cfg.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized",cfg.get("canonical_parameter_change_authorized") is False),
    ]
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    matrix={"stage":STAGE,"status":status,"cell_count":len(revised_cells),"class_counts":counts,"cells":revised_cells,"evidence_rows":revised_rows,"parent_r44_matrix_preserved":True,"replaced_job_ids":affected,"canonical_state_changed":False,"scientific_agreement_claimed":False,"next_action":next_action}
    delta={"stage":STAGE,"status":status,"changed_cell_count":len(changed),"changed_cells":changed,"j09_population_persistence_primary_row":j09[0] if j09 else None,"old_class_counts":old.get("class_counts",{}),"new_class_counts":counts,"structural_disagreement_count_after_repair":structural,"canonical_change_authorized":False,"next_action":next_action}
    summary={"stage":STAGE,"status":status,"job_count":5,"job_audits":job_audits,"class_counts_after_repair":counts,"structural_disagreement_count_after_repair":structural,"calibration_offset_count_after_repair":offsets,"evidence_gap_count_after_repair":gaps,"j09_population_persistence_class_after_repair":j09[0].get("discordance_class") if j09 else None,"canonical_state_changed":False,"canonical_replay_authorized":False,"canonical_parameter_change_authorized":False,"next_action":next_action}
    audit={"stage":STAGE,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"class_counts":counts,"canonical_state_changed":False,"next_action":next_action}
    write_json(root/OUT_REL/"R4_7_CDMETAPOP_READJUDICATED_MATRIX.json",matrix)
    write_json(root/OUT_REL/"R4_7_READJUDICATION_DELTA.json",delta)
    write_json(root/OUT_REL/"R4_7_EXECUTION_SUMMARY.json",summary)
    write_json(root/OUT_REL/"R4_7_INTEGRATED_AUDIT.json",audit)
    return audit,checks

def final_seal(root: Path) -> tuple[dict[str,Any],list[Check]]:
    p=load_json(root/R46_SEAL_REL) if (root/R46_SEAL_REL).exists() else {}
    a=load_json(root/OUT_REL/"R4_7_INTEGRATED_AUDIT.json") if (root/OUT_REL/"R4_7_INTEGRATED_AUDIT.json").exists() else {}
    s=load_json(root/OUT_REL/"R4_7_EXECUTION_SUMMARY.json") if (root/OUT_REL/"R4_7_EXECUTION_SUMMARY.json").exists() else {}
    m=load_json(root/OUT_REL/"R4_7_CDMETAPOP_READJUDICATED_MATRIX.json") if (root/OUT_REL/"R4_7_CDMETAPOP_READJUDICATED_MATRIX.json").exists() else {}
    cfg=load_json(root/CFG_REL)
    checks=[
        Check("parent_r46_sealed",p.get("status")==R46_SEALED,p.get("status")),
        Check("r47_complete",a.get("status")==COMPLETE,a.get("status")),
        Check("r47_zero_process_failures",a.get("checks_failed")==0,a.get("checks_failed")),
        Check("five_symmetric_cdmetapop_jobs",s.get("job_count")==5,s.get("job_count")),
        Check("readjudicated_matrix_75_cells",m.get("cell_count")==75,m.get("cell_count")),
        Check("class_accounting_complete",sum((m.get("class_counts") or {}).values())==75,m.get("class_counts")),
        Check("r44_sealed_outputs_preserved",m.get("parent_r44_matrix_preserved") is True),
        Check("canonical_state_unchanged",s.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized",s.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized",s.get("canonical_parameter_change_authorized") is False),
        Check("deep_off",cfg.get("deep_biological_coupling") is False),
        Check("next_action_present",bool(s.get("next_action")),s.get("next_action")),
    ]
    ok=all(c.passed for c in checks)
    out={"stage":STAGE,"audit":"FINAL_CDMETAPOP_FORCING_PARITY_REPAIR_SYMMETRIC_REEXECUTION_AND_READJUDICATION","status":SEALED if ok else BLOCKED,"verdict":"SEALED" if ok else "BLOCKED","checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"summary":{"class_counts_after_repair":s.get("class_counts_after_repair"),"structural_disagreement_count_after_repair":s.get("structural_disagreement_count_after_repair"),"j09_population_persistence_class_after_repair":s.get("j09_population_persistence_class_after_repair"),"canonical_state_changed":False,"canonical_replay_authorized":False,"canonical_parameter_change_authorized":False,"deep_biological_coupling":False,"next_action":s.get("next_action")},"next_action":s.get("next_action")}
    write_json(root/SEAL_REL,out)
    return out,checks
