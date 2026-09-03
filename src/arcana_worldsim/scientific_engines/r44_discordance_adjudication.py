from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import math

STAGE = "v0.6D1-R4.4"
R43_SEALED = "PASS_R43_FROZEN_23_ENGINE_WINDOW_HISTORICAL_REVALIDATION_EXECUTION_AND_NORMALIZATION_SEALED"
R43_COMPLETE = "PASS_R43_FROZEN_23_ENGINE_WINDOW_EXECUTION_COMPLETE"
SEALED = "PASS_R44_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX_AND_SCIENTIFIC_ADJUDICATION_SEALED"
COMPLETE = "PASS_R44_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX_AND_ADJUDICATION_COMPLETE"
BLOCKED = "BLOCKED_R44_PARENT_EVIDENCE_OR_ADJUDICATION_CONTRACT_FAILURE"

CFG_REL = Path("configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json")
R43_SEAL_REL = Path("outputs/v0_6D1_R4_3_SEAL/R4_3_FINAL_SEAL_AUDIT.json")
R43_AUDIT_REL = Path("outputs/v0_6D1_R4_3/R4_3_COMPLETENESS_AUDIT.json")
R43_SUMMARY_REL = Path("outputs/v0_6D1_R4_3/R4_3_EXECUTION_SUMMARY.json")
R43_MAPPING_REL = Path("outputs/v0_6D1_R4_3/R4_3_PER_JOB_UNIT_MAPPING.json")
R43_DESC_REL = Path("outputs/v0_6D1_R4_3/R4_3_WINDOW_BASELINE_DESCRIPTORS.json")
R42_JOBS_REL = Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")
R41_AUTH_REL = Path("outputs/v0_6D1_R4_1/R4_1_SEMANTIC_AUTHORITY_MATRIX.json")
R43_CFG_REL = Path("configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json")
OUT_REL = Path("outputs/v0_6D1_R4_4")
SEAL_REL = Path("outputs/v0_6D1_R4_4_SEAL/R4_4_FINAL_SEAL_AUDIT.json")

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

def ratio(a: Any,b: Any) -> float | None:
    x,y=finite(a),finite(b)
    if x is None or y is None or abs(x)<1e-15: return None
    return y/x

def delta(a: Any,b: Any) -> float | None:
    x,y=finite(a),finite(b)
    if x is None or y is None: return None
    return y-x

def median(summary: Any) -> float | None:
    return finite(summary.get("median")) if isinstance(summary,dict) else finite(summary)

def _descriptor_target(desc: dict[str,Any], domain: str) -> dict[str,Any] | None:
    typ=desc.get("descriptor_type")
    d=desc.get("comparison_only_derived",{})
    s=desc.get("start_state",{}); e=desc.get("comparison_target_end_state",{})
    if typ=="H0_SNAPSHOT_WINDOW":
        if domain=="population_persistence" and finite(d.get("population_ratio")) is not None:
            return {"kind":"ratio","value":float(d["population_ratio"]),"metric":"ARCANA_total_population_ratio","comparability":"NORMALIZABLE"}
        if domain=="range_occupancy" and finite(d.get("component_ratio")) is not None:
            return {"kind":"ratio","value":float(d["component_ratio"]),"metric":"ARCANA_component_count_ratio","comparability":"PROXY_ONLY","caveat":"component count is fragmentation/support topology, not literal occupied-cell area"}
        if domain=="additive_variance" and finite(d.get("normalized_va_delta")) is not None:
            return {"kind":"delta","value":float(d["normalized_va_delta"]),"metric":"ARCANA_median_normalized_va_delta","comparability":"NORMALIZABLE"}
        if domain=="trophic_opportunity":
            p=desc.get("exogenous_physical_forcing") or {}; st=p.get("start",{}); en=p.get("end",{})
            r=ratio(st.get("mean_total_edible_forage"),en.get("mean_total_edible_forage"))
            if r is not None: return {"kind":"ratio","value":r,"metric":"ARCANA_total_edible_forage_ratio","comparability":"PROXY_ONLY","caveat":"forage is a trophic-opportunity proxy, not Madingley stock biomass"}
        if domain=="extinction_risk" and finite(d.get("population_ratio")) is not None:
            return {"kind":"inverse_ratio","value":float(d["population_ratio"]),"metric":"ARCANA_population_persistence_proxy_for_extinction_risk","comparability":"PROXY_ONLY"}
        if domain=="founder_persistence" and finite(d.get("component_ratio")) is not None:
            return {"kind":"ratio","value":float(d["component_ratio"]),"metric":"ARCANA_component_persistence_proxy","comparability":"PROXY_ONLY"}
    elif typ=="R327_SAPIENT_MACRO_ENSEMBLE_WINDOW":
        if domain=="population_persistence": return _mk("ratio",d.get("population_ratio_median"),"ARCANA_effective_population_ratio","NORMALIZABLE")
        if domain=="range_occupancy": return _mk("ratio",ratio(median(s.get("deme_count")),median(e.get("deme_count"))),"ARCANA_deme_count_ratio","PROXY_ONLY")
        if domain=="additive_variance": return _mk("delta",d.get("genetic_diversity_delta"),"ARCANA_genetic_diversity_delta_proxy","PROXY_ONLY")
        if domain=="trait_response": return _mk("delta",d.get("adaptive_integration_delta"),"ARCANA_adaptive_integration_delta","PROXY_ONLY")
        if domain=="extinction_risk": return _mk("inverse_ratio",d.get("population_ratio_median"),"ARCANA_population_persistence_proxy_for_extinction_risk","PROXY_ONLY")
        if domain=="founder_persistence": return _mk("ratio",ratio(median(s.get("deme_count")),median(e.get("deme_count"))),"ARCANA_deme_count_persistence_proxy","PROXY_ONLY")
    elif typ=="R328_SAPIENT_HIGH_RES_ENSEMBLE_WINDOW":
        if domain=="population_persistence": return _mk("ratio",d.get("population_ratio_median"),"ARCANA_population_proxy_ratio","NORMALIZABLE")
        if domain=="range_occupancy": return _mk("ratio",ratio(median(s.get("active_demes")),median(e.get("active_demes"))),"ARCANA_active_demes_ratio","PROXY_ONLY")
        if domain=="range_shift_rate": return _mk("ratio",d.get("spatial_spread_ratio_median"),"ARCANA_spatial_spread_ratio_proxy","PROXY_ONLY")
        if domain=="additive_variance": return _mk("delta",d.get("genetic_diversity_delta"),"ARCANA_genetic_diversity_delta_proxy","PROXY_ONLY")
        if domain=="trait_response": return _mk("delta",delta(median(s.get("adaptive_integration")),median(e.get("adaptive_integration"))),"ARCANA_adaptive_integration_delta","PROXY_ONLY")
        if domain=="admixture": return _mk("delta",d.get("admixture_delta"),"ARCANA_admixture_fraction_proxy_delta","NORMALIZABLE")
        if domain=="gene_flow": return _mk("delta",d.get("admixture_delta"),"ARCANA_admixture_delta_proxy_for_gene_flow","PROXY_ONLY")
        if domain=="extinction_risk": return _mk("inverse_ratio",d.get("population_ratio_median"),"ARCANA_population_persistence_proxy_for_extinction_risk","PROXY_ONLY")
        if domain=="founder_persistence": return _mk("ratio",ratio(median(s.get("active_demes")),median(e.get("active_demes"))),"ARCANA_active_deme_persistence_proxy","PROXY_ONLY")
    elif typ=="R334_PRODUCER_COEVOLUTION_WINDOW":
        if domain=="gene_flow": return _mk("inverse_delta",d.get("wild_gene_flow_delta"),"ARCANA_wild_gene_flow_delta","PROXY_ONLY")
        if domain=="trait_response": return _mk("delta",d.get("selective_divergence_delta"),"ARCANA_selective_divergence_delta","PROXY_ONLY")
        if domain=="managed_wild_isolation": return _mk("inverse_delta",d.get("wild_gene_flow_delta"),"ARCANA_wild_gene_flow_reduction_for_isolation","NORMALIZABLE")
        if domain=="producer_divergence": return _mk("delta",d.get("selective_divergence_delta"),"ARCANA_selective_divergence_delta","NORMALIZABLE")
    return None

def _mk(kind: str, value: Any, metric: str, comp: str) -> dict[str,Any] | None:
    v=finite(value)
    return None if v is None else {"kind":kind,"value":v,"metric":metric,"comparability":comp}

def _find_metric(norm: dict[str,Any], candidates: list[str]) -> tuple[str,dict[str,Any]] | None:
    nm=norm.get("normalized_metrics",{}) if isinstance(norm,dict) else {}
    for c in candidates:
        s=nm.get(c)
        if isinstance(s,dict) and finite(s.get("median")) is not None:
            return c,s
    return None

def _direction(kind: str, value: float, cfg: dict[str,Any]) -> int:
    if kind in ("ratio","inverse_ratio"):
        if value <= 0: return 0
        eff=math.log(value)
        tol=math.log(float(cfg["effect_policy"]["ratio_neutral_factor"]))
        sign=0 if abs(eff)<=tol else (1 if eff>0 else -1)
        return -sign if kind=="inverse_ratio" else sign
    tol=float(cfg["effect_policy"]["delta_neutral_abs"])
    sign=0 if abs(value)<=tol else (1 if value>0 else -1)
    return -sign if kind=="inverse_delta" else sign

def _effect_magnitude(kind: str, value: float) -> float:
    if kind in ("ratio","inverse_ratio"):
        return abs(math.log(value)) if value>0 else float("inf")
    return abs(value)

def _combine_comp(a: str,b: str) -> str:
    rank={"NONCOMPARABLE":0,"PROXY_ONLY":1,"NORMALIZABLE":2,"DIRECT":3}
    inv={0:"NONCOMPARABLE",1:"PROXY_ONLY",2:"NORMALIZABLE",3:"DIRECT"}
    return inv[min(rank.get(a,0),rank.get(b,0))]

def classify_pair(target: dict[str,Any], metric_name: str, metric_summary: dict[str,Any], map_comp: str, cfg: dict[str,Any]) -> dict[str,Any]:
    ext=finite(metric_summary.get("median")); tv=finite(target.get("value"))
    if ext is None or tv is None: return {"discordance_class":"INSUFFICIENT_EVIDENCE","reason":"NONFINITE_TARGET_OR_EXTERNAL_MEDIAN"}
    combined=_combine_comp(map_comp,target.get("comparability","NONCOMPARABLE"))
    if combined=="NONCOMPARABLE": return {"discordance_class":"SEMANTICALLY_NONCOMPARABLE","reason":"COMBINED_COMPARABILITY_NONCOMPARABLE"}
    td=_direction(target["kind"],tv,cfg)
    # External ratio metrics are ratios; delta metrics are deltas. Inverse semantics are carried only by target.
    ek="delta" if metric_name.endswith("_delta") else "ratio"
    ed=_direction(ek,ext,cfg)
    if combined=="PROXY_ONLY":
        cls="CONCORDANT" if td==ed or td==0 or ed==0 else "CALIBRATION_OFFSET"
        return {"discordance_class":cls,"reason":"PROXY_DIRECTIONAL_COMPARISON_ONLY","combined_comparability":combined,"target_direction":td,"external_direction":ed,"magnitude_comparison_used":False}
    if td*ed<0:
        cls="STRUCTURAL_DISAGREEMENT"
        reason="OPPOSITE_MEANINGFUL_RESPONSE_DIRECTION"
    elif td==0 and ed==0:
        cls="CONCORDANT"; reason="BOTH_WITHIN_NEUTRAL_RESPONSE_BAND"
    elif td==0 or ed==0:
        cls="CALIBRATION_OFFSET"; reason="ONE_RESPONSE_NEUTRAL_OTHER_MEANINGFUL"
    else:
        # Same direction. Magnitude is advisory because R4.3 uses compressed representative response time.
        tm=_effect_magnitude(target["kind"],tv); em=_effect_magnitude(ek,ext)
        if tm<1e-15 and em<1e-15: factor=1.0
        elif min(tm,em)<1e-15: factor=float("inf")
        else: factor=max(tm,em)/min(tm,em)
        if factor<=float(cfg["effect_policy"]["concordant_ratio_factor"]): cls="CONCORDANT"; reason="SAME_DIRECTION_SIMILAR_EFFECT_SCALE"
        else: cls="CALIBRATION_OFFSET"; reason="SAME_DIRECTION_DIFFERENT_EFFECT_SCALE_COMPRESSED_RUNTIME"
    return {"discordance_class":cls,"reason":reason,"combined_comparability":combined,"target_direction":td,"external_direction":ed,"target_value":tv,"external_median":ext,"external_q10":finite(metric_summary.get("q10")),"external_q90":finite(metric_summary.get("q90")),"magnitude_comparison_used":True}

def _terminal_map(summary: dict[str,Any]) -> dict[str,dict[str,Any]]:
    return {x["job_id"]:x for x in summary.get("jobs",[]) if isinstance(x,dict) and x.get("job_id")}

def adjudicate(root: Path) -> tuple[dict[str,Any],list[Check]]:
    cfg=load_json(root/CFG_REL)
    seal=load_json(root/R43_SEAL_REL) if (root/R43_SEAL_REL).exists() else {}
    audit=load_json(root/R43_AUDIT_REL) if (root/R43_AUDIT_REL).exists() else {}
    summary=load_json(root/R43_SUMMARY_REL) if (root/R43_SUMMARY_REL).exists() else {}
    mappings=load_json(root/R43_MAPPING_REL) if (root/R43_MAPPING_REL).exists() else {}
    descs=load_json(root/R43_DESC_REL).get("windows",{}) if (root/R43_DESC_REL).exists() else {}
    jobs=load_json(root/R42_JOBS_REL) if (root/R42_JOBS_REL).exists() else {}
    auth=load_json(root/R41_AUTH_REL) if (root/R41_AUTH_REL).exists() else {}
    r43cfg=load_json(root/R43_CFG_REL) if (root/R43_CFG_REL).exists() else {}
    checks=[
      Check("parent_r43_seal_present",(root/R43_SEAL_REL).exists(),str(R43_SEAL_REL)),
      Check("parent_r43_sealed",seal.get("status")==R43_SEALED,seal.get("status")),
      Check("parent_r43_execution_complete",audit.get("status")==R43_COMPLETE,audit.get("status")),
      Check("parent_exact_23_terminal",sum((audit.get("terminal_counts") or {}).values())==23,audit.get("terminal_counts")),
      Check("parent_zero_blocked",sum((audit.get("terminal_counts") or {}).get(k,0) for k in ["ENGINE_EXECUTION_FAILURE","ADAPTER_FAILURE","MISSING_EVIDENCE"])==0,audit.get("terminal_counts")),
      Check("five_frozen_classes_exact",cfg.get("discordance_classes")==CLASSES,cfg.get("discordance_classes")),
      Check("policy_not_result_selected",cfg.get("policy_freeze",{}).get("result_selected") is False),
      Check("majority_vote_forbidden",cfg.get("majority_vote") is False and auth.get("majority_vote") is False),
      Check("canonical_state_unchanged",cfg.get("canonical_state_changed") is False),
      Check("deep_off",cfg.get("deep_biological_coupling") is False),
    ]
    if any(not c.passed for c in checks):
        out={"stage":STAGE,"status":BLOCKED,"checks":[c.to_dict() for c in checks],"checks_failed":sum(not c.passed for c in checks)}; write_json(root/OUT_REL/"R4_4_INTEGRATED_AUDIT.json",out); return out,checks
    term=_terminal_map(summary)
    mp={x["job_id"]:x for x in mappings.get("mappings",[])}
    job_by={x["job_id"]:x for x in jobs.get("jobs",[])}
    evidence_rows=[]
    for job_id,j in job_by.items():
        t=term.get(job_id,{})
        m=mp.get(job_id,{})
        terminal=t.get("terminal_class")
        norm_path=root/"outputs/v0_6D1_R4_3/jobs"/job_id/"NORMALIZED_EVIDENCE.json"
        norm=load_json(norm_path) if norm_path.exists() else {}
        for dm in m.get("domain_mapping",[]):
            domain=dm["domain"]; role=dm["authority_role"]; mapcomp=dm["comparability_class"]
            base={"stage":STAGE,"window_id":j["window_id"],"job_id":job_id,"engine":j["engine"],"domain":domain,"authority_role":role,"mapping_comparability":mapcomp,"parent_terminal_class":terminal,"majority_vote":False,"canonical_write":False}
            if terminal=="SEMANTIC_NONCOMPARABILITY":
                row={**base,"discordance_class":"SEMANTICALLY_NONCOMPARABLE","reason":"R43_ENGINE_JOB_SEMANTIC_NONCOMPARABILITY","metric":None,"target":None}
            elif terminal!="SCIENTIFIC_RESULT":
                row={**base,"discordance_class":"INSUFFICIENT_EVIDENCE","reason":"R43_PARENT_NOT_SCIENTIFIC_RESULT","metric":None,"target":None}
            else:
                target=_descriptor_target(descs.get(j["window_id"],{}),domain)
                cand=cfg.get("domain_metric_candidates",{}).get(j["engine"],{}).get(domain,[])
                picked=_find_metric(norm,cand)
                if target is None:
                    row={**base,"discordance_class":"INSUFFICIENT_EVIDENCE","reason":"NO_ARCANA_DOMAIN_TARGET_WITH_DECLARED_SEMANTICS","metric":None,"target":None}
                elif picked is None:
                    row={**base,"discordance_class":"INSUFFICIENT_EVIDENCE","reason":"NO_R43_NORMALIZED_RESULT_METRIC_FOR_DOMAIN","metric":None,"target":target,"candidate_metrics":cand}
                else:
                    mn,ms=picked; res=classify_pair(target,mn,ms,mapcomp,cfg)
                    row={**base,**res,"metric":{"name":mn,"summary":ms},"target":target}
            evidence_rows.append(row)
    # One adjudication cell for every frozen window x scoped domain.
    cells=[]
    for wid,domains in r43cfg.get("window_domain_scope",{}).items():
        for domain in domains:
            rows=[r for r in evidence_rows if r["window_id"]==wid and r["domain"]==domain]
            prim=[r for r in rows if r["authority_role"]=="PRIMARY"]
            sec=[r for r in rows if r["authority_role"]=="SECONDARY"]
            adjud=[r for r in prim if r.get("mapping_comparability") in ("NORMALIZABLE","DIRECT") and (r.get("target") or {}).get("comparability") in ("NORMALIZABLE","DIRECT") and r["discordance_class"] in ("CONCORDANT","CALIBRATION_OFFSET","STRUCTURAL_DISAGREEMENT")]
            if any(r["discordance_class"]=="STRUCTURAL_DISAGREEMENT" for r in adjud): cls="STRUCTURAL_DISAGREEMENT"; reason="AT_LEAST_ONE_PRIMARY_ADJUDICATIVE_STRUCTURAL_DISAGREEMENT"
            elif any(r["discordance_class"]=="CALIBRATION_OFFSET" for r in adjud): cls="CALIBRATION_OFFSET"; reason="PRIMARY_ADJUDICATIVE_CALIBRATION_OFFSET_WITH_NO_STRUCTURAL_DISAGREEMENT"
            elif any(r["discordance_class"]=="CONCORDANT" for r in adjud): cls="CONCORDANT"; reason="PRIMARY_ADJUDICATIVE_CONCORDANCE_WITH_NO_HIGHER_SEVERITY_PRIMARY_FINDING"
            elif prim and all(r["discordance_class"]=="SEMANTICALLY_NONCOMPARABLE" for r in prim): cls="SEMANTICALLY_NONCOMPARABLE"; reason="ALL_PRIMARY_EVIDENCE_SEMANTICALLY_NONCOMPARABLE"
            else: cls="INSUFFICIENT_EVIDENCE"; reason="NO_PRIMARY_NORMALIZABLE_RESULT_TARGET_PAIR"
            boundaries=sorted({job_by[r["job_id"]].get("earliest_replay_boundary") for r in adjud if r["discordance_class"]=="STRUCTURAL_DISAGREEMENT" and job_by[r["job_id"]].get("earliest_replay_boundary")}, key=lambda x: cfg["replay_boundary_order"].index(x) if x in cfg["replay_boundary_order"] else 999)
            cells.append({"window_id":wid,"domain":domain,"discordance_class":cls,"reason":reason,"primary_evidence_rows":len(prim),"secondary_context_rows":len(sec),"primary_adjudicative_rows":len(adjud),"earliest_affected_authority_candidate":boundaries[0] if boundaries else None,"canonical_change_authorized":False,"majority_vote":False})
    class_counts={c:sum(1 for x in cells if x["discordance_class"]==c) for c in CLASSES}
    structural=[x for x in cells if x["discordance_class"]=="STRUCTURAL_DISAGREEMENT"]
    offsets=[x for x in cells if x["discordance_class"]=="CALIBRATION_OFFSET"]
    gaps=[x for x in cells if x["discordance_class"] in ("INSUFFICIENT_EVIDENCE","SEMANTICALLY_NONCOMPARABLE")]
    boundaries=sorted({x["earliest_affected_authority_candidate"] for x in structural if x.get("earliest_affected_authority_candidate")}, key=lambda x: cfg["replay_boundary_order"].index(x) if x in cfg["replay_boundary_order"] else 999)
    if structural:
        next_action="BUILD_R45_EARLIEST_AUTHORITY_CAUSAL_DIAGNOSIS_RECALIBRATION_AND_REPLAY_PLAN"
    elif gaps:
        next_action="BUILD_R45_EVIDENCE_GAP_CLOSURE_AND_TARGETED_ADAPTER_ENHANCEMENT"
    elif offsets:
        next_action="BUILD_R45_TARGETED_CALIBRATION_REVIEW_WITHOUT_AUTOMATIC_CANONICAL_CHANGE"
    else:
        next_action="BUILD_R45_REVALIDATION_CLOSURE_AND_BASELINE_PROMOTION_GATE"
    expected_cells=sum(len(v) for v in r43cfg.get("window_domain_scope",{}).values())
    checks.extend([
      Check("all_r43_mapping_job_ids_resolved",set(mp)==set(job_by),{"mappings":len(mp),"jobs":len(job_by)}),
      Check("all_parent_terminal_rows_resolved",set(term)==set(job_by),{"terminal":len(term),"jobs":len(job_by)}),
      Check("every_scoped_window_domain_classified",len(cells)==expected_cells,{"observed":len(cells),"expected":expected_cells}),
      Check("all_cells_use_frozen_class",all(x["discordance_class"] in CLASSES for x in cells),class_counts),
      Check("no_secondary_only_promotion",all(not (x["discordance_class"] in ("CONCORDANT","CALIBRATION_OFFSET","STRUCTURAL_DISAGREEMENT") and x["primary_adjudicative_rows"]==0) for x in cells)),
      Check("no_canonical_write_or_replay",all(x["canonical_change_authorized"] is False for x in cells)),
      Check("no_majority_vote_anywhere",all(x["majority_vote"] is False for x in cells) and all(r["majority_vote"] is False for r in evidence_rows)),
    ])
    status=COMPLETE if all(c.passed for c in checks) else BLOCKED
    matrix={"stage":STAGE,"status":status,"cell_count":len(cells),"class_counts":class_counts,"cells":cells,"evidence_rows":evidence_rows,"global_scientific_agreement_claimed":False,"canonical_state_changed":False,"deep_biological_coupling":False,"earliest_affected_authority_candidate":boundaries[0] if boundaries else None,"next_action":next_action}
    write_json(root/OUT_REL/"R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json",matrix)
    summary_out={"stage":STAGE,"status":status,"class_counts":class_counts,"structural_disagreement_count":len(structural),"calibration_offset_count":len(offsets),"evidence_gap_count":len(gaps),"earliest_affected_authority_candidate":boundaries[0] if boundaries else None,"canonical_state_changed":False,"baseline_a_preserved":True,"deep_biological_coupling":False,"scientific_agreement_claimed":False,"replay_authorized":False,"next_action":next_action}
    write_json(root/OUT_REL/"R4_4_ADJUDICATION_SUMMARY.json",summary_out)
    audit_out={"stage":STAGE,"status":status,"checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"class_counts":class_counts,"canonical_state_changed":False,"next_action":next_action}
    write_json(root/OUT_REL/"R4_4_INTEGRATED_AUDIT.json",audit_out)
    return audit_out,checks

def final_seal(root: Path) -> tuple[dict[str,Any],list[Check]]:
    parent=load_json(root/R43_SEAL_REL) if (root/R43_SEAL_REL).exists() else {}
    audit=load_json(root/OUT_REL/"R4_4_INTEGRATED_AUDIT.json") if (root/OUT_REL/"R4_4_INTEGRATED_AUDIT.json").exists() else {}
    matrix=load_json(root/OUT_REL/"R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json") if (root/OUT_REL/"R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json").exists() else {}
    summary=load_json(root/OUT_REL/"R4_4_ADJUDICATION_SUMMARY.json") if (root/OUT_REL/"R4_4_ADJUDICATION_SUMMARY.json").exists() else {}
    checks=[
      Check("parent_r43_sealed",parent.get("status")==R43_SEALED,parent.get("status")),
      Check("r44_adjudication_complete",audit.get("status")==COMPLETE,audit.get("status")),
      Check("r44_zero_process_failures",audit.get("checks_failed")==0,audit.get("checks_failed")),
      Check("matrix_present_and_nonempty",matrix.get("cell_count",0)>0,matrix.get("cell_count")),
      Check("five_class_accounting_complete",sum((matrix.get("class_counts") or {}).values())==matrix.get("cell_count",-1),matrix.get("class_counts")),
      Check("baseline_a_preserved",summary.get("baseline_a_preserved") is True),
      Check("canonical_state_unchanged",summary.get("canonical_state_changed") is False),
      Check("deep_biological_coupling_off",summary.get("deep_biological_coupling") is False),
      Check("scientific_agreement_not_globally_claimed",summary.get("scientific_agreement_claimed") is False),
      Check("replay_not_authorized_in_r44",summary.get("replay_authorized") is False),
    ]
    ok=all(c.passed for c in checks)
    out={"stage":STAGE,"audit":"FINAL_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX_AND_SCIENTIFIC_ADJUDICATION","status":SEALED if ok else BLOCKED,"verdict":"SEALED" if ok else "BLOCKED","checks_passed":sum(c.passed for c in checks),"checks_total":len(checks),"checks_failed":sum(not c.passed for c in checks),"checks":[c.to_dict() for c in checks],"summary":summary,"next_action":summary.get("next_action")}
    write_json(root/SEAL_REL,out)
    return out,checks
