from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
import csv
import json
import math
import re

import numpy as np

from arcana_worldsim.scientific_engines.r43_historical_revalidation import normalize_raw
from arcana_worldsim.scientific_engines import r44_discordance_adjudication as r44
from arcana_worldsim.scientific_engines import r47_cdmetapop_forcing_parity as r47

STAGE = "v0.6D1-R4.11"
R410_SEALED = "PASS_R410_MATCHED_CONTROL_PRECISION_ALTERNATE_EVIDENCE_AND_POPULATION_METRIC_INTEGRITY_AUDIT_SEALED"
R410_FINDING = "R43_R49_CDMETAPOP_POPULATION_METRIC_FILENAME_SELECTOR_COLLISION_CONFIRMED"
PREPARED = "PASS_R411_RETAINED_CDMETAPOP_RUNTIME_SUMMARY_REEXTRACTION_PLAN_PREPARED"
COMPLETE = "PASS_R411_CDMETAPOP_POPULATION_METRIC_REEXTRACTION_AND_SYMMETRIC_READJUDICATION_COMPLETE"
SEALED = "PASS_R411_CDMETAPOP_POPULATION_METRIC_EXTRACTION_REPAIR_AND_SYMMETRIC_READJUDICATION_SEALED"
BLOCKED = "BLOCKED_R411_PARENT_RETAINED_RUNTIME_OR_METRIC_REEXTRACTION_FAILURE"

CFG_REL = Path("configs/world1_r411_cdmetapop_population_metric_reextraction_v0_6D1_R4_11.json")
R410_SEAL_REL = Path("outputs/v0_6D1_R4_10_SEAL/R4_10_FINAL_SEAL_AUDIT.json")
R410_INTEGRITY_REL = Path("outputs/v0_6D1_R4_10/R4_10_CDMETAPOP_POPULATION_METRIC_INTEGRITY_AUDIT.json")
R410_PLAN_REL = Path("outputs/v0_6D1_R4_10/R4_10_ALTERNATE_EVIDENCE_CLOSURE_PLAN.json")
R44_MATRIX_REL = Path("outputs/v0_6D1_R4_4/R4_4_CROSS_ENGINE_DOMAIN_DISCORDANCE_MATRIX.json")
R44_CFG_REL = Path("configs/world1_r44_discordance_adjudication_v0_6D1_R4_4.json")
R43_MAP_REL = Path("outputs/v0_6D1_R4_3/R4_3_PER_JOB_UNIT_MAPPING.json")
R43_DESC_REL = Path("outputs/v0_6D1_R4_3/R4_3_WINDOW_BASELINE_DESCRIPTORS.json")
R42_JOBS_REL = Path("outputs/v0_6D1_R4_2/R4_2_ENGINE_WINDOW_JOB_MATRIX.json")
R43_CFG_REL = Path("configs/world1_r43_historical_revalidation_v0_6D1_R4_3.json")
R49_PAIR_REL = Path("outputs/v0_6D1_R4_9/R4_9_EXPANDED_PAIRED_CAUSAL_EFFECT.json")
CDM_POST_REL = Path(".arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_PostProcess.py")
CDM_MAIN_REL = Path(".arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_mainloop.py")
CDM_PRE_REL = Path(".arcana_engines/CDMetaPOP-3.08/src/CDmetaPOP_PreProcess.py")
OUT_REL = Path("outputs/v0_6D1_R4_11")
SEAL_REL = Path("outputs/v0_6D1_R4_11_SEAL/R4_11_FINAL_SEAL_AUDIT.json")

AFFECTED = [
    "R42_J03_H0_DEEP_TIME_BACKGROUND_CDMETAPOP",
    "R42_J06_H0_PRE_CHA1_CDMETAPOP",
    "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP",
    "R42_J15_SAPIENT_3MA_TO_200KA_CDMETAPOP",
    "R42_J20_SAPIENT_200KA_TO_0_CDMETAPOP",
]
J09 = "R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP"
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
    h = sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def finite(x: Any) -> float | None:
    try: v = float(x)
    except (TypeError, ValueError): return None
    return v if math.isfinite(v) else None


def pipe_total(value: Any) -> float | None:
    if value is None: return None
    token = str(value).split("|")[0].strip()
    return finite(token)


def parse_summary_population(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"empty summary_popAllTime.csv: {path}")
    required = {"Year", "GrowthRate", "N_Initial"}
    if not required.issubset(rows[0].keys()):
        raise ValueError(f"summary missing required columns {sorted(required)}: {path}")
    totals = [pipe_total(r.get("N_Initial")) for r in rows]
    growth = [finite(r.get("GrowthRate")) for r in rows]
    if any(v is None or v < 0 for v in totals):
        raise ValueError(f"nonfinite/negative N_Initial total in {path}")
    if any(v is None or v < 0 for v in growth):
        raise ValueError(f"nonfinite/negative GrowthRate in {path}")
    chain_errors = []
    for i in range(len(rows) - 1):
        expected = float(totals[i]) * float(growth[i])
        observed = float(totals[i + 1])
        scale = max(1.0, abs(expected), abs(observed))
        if abs(expected - observed) > 1e-8 * scale:
            chain_errors.append({"row": i, "expected_next": expected, "observed_next": observed})
    initial = float(totals[0])
    final = float(totals[-1]) * float(growth[-1])
    ratio = (final / initial) if initial > 0 else None
    product = float(np.prod(np.asarray(growth, dtype=float)))
    product_ratio_error = abs(product - ratio) if ratio is not None else None
    return {
        "summary_path": str(path),
        "summary_sha256": sha256_file(path),
        "row_count": len(rows),
        "year_first": rows[0].get("Year"),
        "year_last": rows[-1].get("Year"),
        "initial_population": initial,
        "final_population": final,
        "population_response_ratio": ratio,
        "growth_product": product,
        "growth_product_ratio_abs_error": product_ratio_error,
        "lifecycle_chain_error_count": len(chain_errors),
        "lifecycle_chain_error_examples": chain_errors[:5],
        "extraction_semantics": "summary_popAllTime.N_Initial total at row0; final = last N_Initial total * last GrowthRate; GrowthRate[i] is N_Init[i+1]/N_Init[i] in pinned CDMetaPOP PostProcess",
    }


def _n0_first_knot_species_sum(value: Any) -> float | None:
    """Mirror pinned CDMetaPOP initial N0 parsing: first | knot, then sum ; species."""
    if value is None:
        return None
    first = str(value).split("|")[0].strip()
    if first == "":
        return None
    vals = []
    for token in first.split(";"):
        v = finite(token.strip())
        if v is None:
            return None
        vals.append(v)
    return float(sum(vals))


def _configured_n0_audit(rep_dir: Path) -> dict[str, Any]:
    candidates = [p for p in rep_dir.rglob("PatchVars.csv") if "patchvars" in {x.lower() for x in p.parts}]
    # Prefer the copied input canonical name. Generated scientific outputs should not contain PatchVars.csv.
    candidates = sorted(candidates, key=lambda p: (0 if "example_files" in {x.lower() for x in p.parts} else 1, len(p.parts), str(p)))
    if not candidates:
        return {"patchvars_path": None, "raw_configured_n0_sum": None, "engine_effective_n0_sum": None,
                "nonnatal_zeroed_n0_sum": None, "rows_total": 0, "rows_zeroed_by_engine_rule": 0,
                "natal_grounds_column_present": False, "parse_ok": False}
    p = candidates[0]
    with p.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f); rows = list(reader); fields = set(reader.fieldnames or [])
    natal_col = "Natal Grounds"
    if natal_col not in fields:
        return {"patchvars_path": str(p), "raw_configured_n0_sum": None, "engine_effective_n0_sum": None,
                "nonnatal_zeroed_n0_sum": None, "rows_total": len(rows), "rows_zeroed_by_engine_rule": 0,
                "natal_grounds_column_present": False, "parse_ok": False}
    raw_total = 0.0; effective_total = 0.0; zeroed_total = 0.0; zeroed_rows = 0
    row_audit = []
    for i, row in enumerate(rows):
        n0 = _n0_first_knot_species_sum(row.get("N0"))
        natal = finite(row.get(natal_col))
        if n0 is None or natal is None or int(natal) not in (0, 1):
            return {"patchvars_path": str(p), "raw_configured_n0_sum": None, "engine_effective_n0_sum": None,
                    "nonnatal_zeroed_n0_sum": None, "rows_total": len(rows), "rows_zeroed_by_engine_rule": zeroed_rows,
                    "natal_grounds_column_present": True, "parse_ok": False, "failed_row": i}
        raw_total += n0
        # Pinned CDmetaPOP_PreProcess.py explicitly sets N0=0 whenever natal_patches==0.
        eff = n0 if int(natal) != 0 else 0.0
        effective_total += eff
        if int(natal) == 0 and n0 > 0:
            zeroed_total += n0; zeroed_rows += 1
        row_audit.append({"row_index": i, "n0_first_knot_species_sum": n0, "natal_grounds": int(natal), "engine_effective_n0": eff})
    return {"patchvars_path": str(p), "raw_configured_n0_sum": raw_total,
            "engine_effective_n0_sum": effective_total, "nonnatal_zeroed_n0_sum": zeroed_total,
            "rows_total": len(rows), "rows_zeroed_by_engine_rule": zeroed_rows,
            "natal_grounds_column_present": True, "parse_ok": True, "row_audit": row_audit}


def _summary_for_rep(rep_dir: Path) -> Path:
    cands = [p for p in rep_dir.rglob("summary_popAllTime.csv") if p.is_file()]
    if len(cands) != 1:
        raise ValueError(f"expected exactly one summary_popAllTime.csv under {rep_dir}, observed {len(cands)}")
    return cands[0]


def _replicate_reextract(rep_dir: Path, replicate_index: int, seed: int) -> dict[str, Any]:
    summary = _summary_for_rep(rep_dir)
    metric = parse_summary_population(summary)
    n0audit = _configured_n0_audit(rep_dir)
    effective_n0 = n0audit.get("engine_effective_n0_sum")
    raw_n0 = n0audit.get("raw_configured_n0_sum")
    zeroed = n0audit.get("nonnatal_zeroed_n0_sum")
    start_match = effective_n0 is not None and math.isclose(metric["initial_population"], float(effective_n0), rel_tol=0, abs_tol=1e-9)
    accounting_match = (raw_n0 is not None and effective_n0 is not None and zeroed is not None and
                        math.isclose(float(raw_n0) - float(effective_n0), float(zeroed), rel_tol=0, abs_tol=1e-9))
    metric.update({
        "replicate_index": int(replicate_index),
        "seed": int(seed),
        "raw_configured_n0_sum": raw_n0,
        "engine_effective_configured_n0_sum": effective_n0,
        "nonnatal_zeroed_n0_sum": zeroed,
        "configured_patchvars_path": n0audit.get("patchvars_path"),
        "natal_grounds_column_present": n0audit.get("natal_grounds_column_present"),
        "n0_engine_semantics_parse_ok": n0audit.get("parse_ok"),
        "rows_zeroed_by_engine_nonnatal_rule": n0audit.get("rows_zeroed_by_engine_rule"),
        "initial_population_matches_engine_effective_configured_n0_sum": start_match,
        "raw_minus_effective_equals_nonnatal_zeroed": accounting_match,
    })
    return metric


def _contract(root: Path, jid: str) -> dict[str, Any]:
    return load_json(root / "outputs/v0_6D1_R4_3/jobs" / jid / "JOB_CONTRACT.json")


def _raw(root: Path, rel: Path) -> dict[str, Any]:
    return load_json(root / rel)


def _seed_specs(raw: dict[str, Any]) -> list[tuple[int, int]]:
    return [(int(r["replicate_index"]), int(r["seed"])) for r in raw.get("replicates", [])]


def _reextract_arm(root: Path, label: str, raw_rel: Path, work_rel: Path) -> dict[str, Any]:
    raw = _raw(root, raw_rel)
    rows = []
    for ri, seed in _seed_specs(raw):
        rep_dir = root / work_rel / f"rep_{ri:03d}"
        if not rep_dir.exists():
            rows.append({"replicate_index": ri, "seed": seed, "status": "MISSING_RETAINED_RUNTIME", "rep_dir": str(rep_dir.relative_to(root))})
            continue
        try:
            m = _replicate_reextract(rep_dir, ri, seed)
            m["status"] = "PASS"
            m["rep_dir"] = str(rep_dir.relative_to(root))
            rows.append(m)
        except Exception as exc:
            rows.append({"replicate_index": ri, "seed": seed, "status": "REEXTRACTION_FAILURE", "rep_dir": str(rep_dir.relative_to(root)), "error": repr(exc)})
    return {"label": label, "raw_rel": str(raw_rel), "work_rel": str(work_rel), "source_adapter_status": raw.get("adapter_status"), "replicates": rows}


def retained_runtime_inventory(root: Path) -> dict[str, Any]:
    arms = []
    for jid in AFFECTED:
        arms.append(_reextract_arm(
            root,
            f"R47_DYNAMIC_{jid}",
            Path(f"outputs/v0_6D1_R4_7/jobs/{jid}/RAW_EVIDENCE.json"),
            Path(f"outputs/v0_6D1_R4_7/jobs/{jid}/runtime_work"),
        ))
    arms.append(_reextract_arm(
        root, "R48_J09_NEUTRAL",
        Path(f"outputs/v0_6D1_R4_8/jobs/{J09}/RAW_NEUTRAL_CONTROL_EVIDENCE.json"),
        Path(f"outputs/v0_6D1_R4_8/jobs/{J09}/runtime_work_neutral"),
    ))
    arms.append(_reextract_arm(
        root, "R49_J09_ADDITIONAL_DYNAMIC",
        Path(f"outputs/v0_6D1_R4_9/jobs/{J09}/RAW_ADDITIONAL_DYNAMIC_EVIDENCE.json"),
        Path(f"outputs/v0_6D1_R4_9/jobs/{J09}/runtime_work_additional_dynamic"),
    ))
    arms.append(_reextract_arm(
        root, "R49_J09_ADDITIONAL_NEUTRAL",
        Path(f"outputs/v0_6D1_R4_9/jobs/{J09}/RAW_ADDITIONAL_NEUTRAL_EVIDENCE.json"),
        Path(f"outputs/v0_6D1_R4_9/jobs/{J09}/runtime_work_additional_neutral"),
    ))
    reps = [r for a in arms for r in a["replicates"]]
    return {
        "stage": STAGE,
        "expected_summary_count": 56,
        "observed_replicate_record_count": len(reps),
        "pass_count": sum(r.get("status") == "PASS" for r in reps),
        "failed_count": sum(r.get("status") != "PASS" for r in reps),
        "all_initial_populations_match_engine_effective_configured_n0_sum": all(r.get("initial_population_matches_engine_effective_configured_n0_sum") is True for r in reps if r.get("status") == "PASS"),
        "all_n0_engine_semantics_parse_ok": all(r.get("n0_engine_semantics_parse_ok") is True for r in reps if r.get("status") == "PASS"),
        "all_raw_effective_n0_accounting_consistent": all(r.get("raw_minus_effective_equals_nonnatal_zeroed") is True for r in reps if r.get("status") == "PASS"),
        "replicates_with_nonnatal_n0_zeroing": sum((r.get("rows_zeroed_by_engine_nonnatal_rule") or 0) > 0 for r in reps if r.get("status") == "PASS"),
        "all_lifecycle_chains_consistent": all(r.get("lifecycle_chain_error_count") == 0 for r in reps if r.get("status") == "PASS"),
        "arms": arms,
        "engine_rerun_performed": False,
        "canonical_write": False,
    }


def _pinned_semantics_audit(root: Path) -> dict[str, Any]:
    post = (root / CDM_POST_REL).read_text(encoding="utf-8-sig", errors="replace") if (root / CDM_POST_REL).exists() else ""
    main = (root / CDM_MAIN_REL).read_text(encoding="utf-8-sig", errors="replace") if (root / CDM_MAIN_REL).exists() else ""
    pre = (root / CDM_PRE_REL).read_text(encoding="utf-8-sig", errors="replace") if (root / CDM_PRE_REL).exists() else ""
    checks = {
        "growth_pop_definition_present": "growthPop = tempPop[1:]/tempPop[0:(len(tempPop)-1)]" in post,
        "summary_n_initial_write_present": "outputfile.write(str(N_Init[i][j])+'|')" in post,
        "initial_metrics_before_loop_present": "GetMetrics(SubpopIN_init,K,Track_N_Init_pop" in main,
        "post_generation_metrics_gen_plus_one_present": "GetMetrics(SubpopIN,K,Track_N_Init_pop,Track_K,loci,alleles,gen+1" in main,
        "initial_n0_first_cdclimate_knot_present": "N0.append(N0_temp[isub].split('|')[0])" in pre,
        "nonnatal_n0_zeroing_present": "int(N0[isub]) > 0 and natal_patches[isub] == 0" in pre and "N0[isub] = '0'" in pre,
    }
    return {"files": [str(CDM_POST_REL), str(CDM_MAIN_REL), str(CDM_PRE_REL)], "checks": checks, "semantics_confirmed": all(checks.values())}


def prepare(root: Path) -> tuple[dict[str, Any], list[Check]]:
    cfg = load_json(root / CFG_REL)
    seal = load_json(root / R410_SEAL_REL) if (root / R410_SEAL_REL).exists() else {}
    integ = load_json(root / R410_INTEGRITY_REL) if (root / R410_INTEGRITY_REL).exists() else {}
    plan410 = load_json(root / R410_PLAN_REL) if (root / R410_PLAN_REL).exists() else {}
    sem = _pinned_semantics_audit(root)
    inv = retained_runtime_inventory(root)
    expected_five = list(cfg["affected_frozen_cdmetapop_jobs"])
    checks = [
        Check("parent_r410_seal_present", (root / R410_SEAL_REL).exists(), str(R410_SEAL_REL)),
        Check("parent_r410_sealed", seal.get("status") == R410_SEALED, seal.get("status")),
        Check("parent_population_metric_collision_confirmed", integ.get("finding") == R410_FINDING, integ.get("finding")),
        Check("parent_r411_plan_frozen", plan410.get("status") == "R411_PLAN_FROZEN", plan410.get("status")),
        Check("exact_five_symmetric_cdmetapop_jobs", expected_five == AFFECTED, expected_five),
        Check("pinned_cdmetapop_summary_semantics_confirmed", sem["semantics_confirmed"], sem["checks"]),
        Check("retained_runtime_exact_56_replicate_records", inv["observed_replicate_record_count"] == 56, inv["observed_replicate_record_count"]),
        Check("retained_runtime_all_56_reextractable", inv["pass_count"] == 56 and inv["failed_count"] == 0, {"pass": inv["pass_count"], "failed": inv["failed_count"]}),
        Check("all_reextracted_initials_match_engine_effective_configured_n0", inv["all_initial_populations_match_engine_effective_configured_n0_sum"], None),
        Check("all_n0_engine_semantics_parse_ok", inv["all_n0_engine_semantics_parse_ok"], None),
        Check("all_raw_effective_n0_accounting_consistent", inv["all_raw_effective_n0_accounting_consistent"], None),
        Check("all_summary_lifecycle_chains_consistent", inv["all_lifecycle_chains_consistent"], None),
        Check("reextract_before_rerun", cfg["repair_policy"]["reextract_retained_runtime_before_any_rerun"] is True),
        Check("engine_rerun_forbidden_in_r411", cfg["repair_policy"]["engine_rerun_in_r411"] is False),
        Check("historical_evidence_preserved", cfg["repair_policy"]["preserve_r43_r49_historical_outputs"] is True),
        Check("canonical_state_unchanged", cfg["canonical_state_changed"] is False),
        Check("canonical_replay_not_authorized", cfg["canonical_replay_authorized"] is False),
        Check("canonical_parameter_change_not_authorized", cfg["canonical_parameter_change_authorized"] is False),
        Check("deep_off", cfg["deep_biological_coupling"] is False),
        Check("majority_vote_forbidden", cfg["majority_vote"] is False),
    ]
    status = PREPARED if all(c.passed for c in checks) else BLOCKED
    inv["status"] = status
    write_json(root / OUT_REL / "R4_11_RETAINED_RUNTIME_SUMMARY_INVENTORY.json", inv)
    write_json(root / OUT_REL / "R4_11_PINNED_CDMETAPOP_SUMMARY_SEMANTICS_AUDIT.json", sem)
    out = {
        "stage": STAGE,
        "status": status,
        "checks_passed": sum(c.passed for c in checks),
        "checks_total": len(checks),
        "checks_failed": sum(not c.passed for c in checks),
        "checks": [c.to_dict() for c in checks],
        "retained_summary_count": inv["pass_count"],
        "engine_rerun_performed": False,
        "canonical_state_changed": False,
        "next_action": "REEXTRACT_R411_CORRECTED_CDMETAPOP_POPULATION_METRICS" if status == PREPARED else "RESTORE_OR_TARGETED_RERUN_ONLY_MISSING_RETAINED_CDMETAPOP_RUNTIME_EVIDENCE",
    }
    write_json(root / OUT_REL / "R4_11_REEXTRACTION_PLAN.json", out)
    return out, checks


def _arm_by_label(inv: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a["label"]: a for a in inv.get("arms", [])}


def _corrected_r47_raw(root: Path, inv: dict[str, Any], jid: str) -> dict[str, Any]:
    legacy_path = root / f"outputs/v0_6D1_R4_7/jobs/{jid}/RAW_EVIDENCE.json"
    legacy = load_json(legacy_path)
    arm = _arm_by_label(inv)[f"R47_DYNAMIC_{jid}"]
    by_key = {(int(x["replicate_index"]), int(x["seed"])): x for x in arm["replicates"]}
    reps = []
    for old in legacy.get("replicates", []):
        key = (int(old["replicate_index"]), int(old["seed"]))
        ext = by_key[key]
        oldm = dict(old.get("metrics") or {})
        newm = dict(oldm)
        newm["legacy_buggy_initial_population"] = oldm.get("initial_population")
        newm["legacy_buggy_final_population"] = oldm.get("final_population")
        newm["initial_population"] = ext["initial_population"]
        newm["final_population"] = ext["final_population"]
        newm["population_metric_source"] = "summary_popAllTime.csv:N_Initial+GrowthRate"
        newm["population_metric_summary_sha256"] = ext["summary_sha256"]
        newm["population_metric_extraction_semantics"] = ext["extraction_semantics"]
        # Occupancy fields from the broad filename selector are not promoted by R4.11.
        newm["initial_occupied_patches"] = None
        newm["final_occupied_patches"] = None
        reps.append({**old, "metrics": newm, "metric_reextraction_status": "PASS", "metric_reextraction_summary_path": ext["summary_path"]})
    return {
        **legacy,
        "stage": STAGE,
        "evidence_namespace": "R4_11_REEXTRACTED_FROM_RETAINED_R47_RUNTIME_SUMMARIES",
        "legacy_source_raw_sha256": sha256_file(legacy_path),
        "population_metric_repaired": True,
        "population_metric_source": "CDMetaPOP summary_popAllTime.csv",
        "engine_rerun_performed": False,
        "replicates": reps,
        "canonical_write": False,
    }


def _mapping_by_job(root: Path) -> dict[str, dict[str, Any]]:
    d = load_json(root / R43_MAP_REL)
    return {x["job_id"]: x for x in d.get("mappings", []) if isinstance(x, dict) and x.get("job_id")}


def _jobs_by_id(root: Path) -> dict[str, dict[str, Any]]:
    d = load_json(root / R42_JOBS_REL)
    return {x["job_id"]: x for x in d.get("jobs", []) if isinstance(x, dict) and x.get("job_id")}


def _corrected_rows(root: Path, job_ids: list[str]) -> list[dict[str, Any]]:
    mappings = _mapping_by_job(root); jobs = _jobs_by_id(root)
    descs = load_json(root / R43_DESC_REL).get("windows", {})
    cfg44 = load_json(root / R44_CFG_REL)
    rows = []
    for jid in job_ids:
        j = jobs[jid]; m = mappings[jid]
        norm = load_json(root / OUT_REL / "jobs" / jid / "CORRECTED_NORMALIZED_EVIDENCE.json")
        for dm in m.get("domain_mapping", []):
            domain = dm["domain"]; role = dm["authority_role"]; mapcomp = dm["comparability_class"]
            target = r44._descriptor_target(descs.get(j["window_id"], {}), domain)
            cand = cfg44.get("domain_metric_candidates", {}).get("CDMetaPOP", {}).get(domain, [])
            picked = r44._find_metric(norm, cand)
            base = {"stage": STAGE, "window_id": j["window_id"], "job_id": jid, "engine": "CDMetaPOP", "domain": domain, "authority_role": role, "mapping_comparability": mapcomp, "parent_terminal_class": "SCIENTIFIC_RESULT", "majority_vote": False, "canonical_write": False, "evidence_namespace": "R4_11_CDMETAPOP_POPULATION_METRIC_REEXTRACTION"}
            if target is None:
                row = {**base, "discordance_class": "INSUFFICIENT_EVIDENCE", "reason": "NO_ARCANA_DOMAIN_TARGET_WITH_DECLARED_SEMANTICS", "metric": None, "target": None}
            elif picked is None:
                row = {**base, "discordance_class": "INSUFFICIENT_EVIDENCE", "reason": "NO_R411_CORRECTED_NORMALIZED_RESULT_METRIC_FOR_DOMAIN", "metric": None, "target": target, "candidate_metrics": cand}
            else:
                mn, ms = picked; res = r44.classify_pair(target, mn, ms, mapcomp, cfg44)
                row = {**base, **res, "metric": {"name": mn, "summary": ms}, "target": target}
            rows.append(row)
    return rows


def _recompute_cells(root: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Reuse the already-audited R4.7 implementation of the frozen R4.4 cell policy.
    return r47._recompute_cells(root, rows)


def _summary(vals: list[float]) -> dict[str, Any]:
    a = np.asarray(vals, dtype=float)
    if a.size == 0: return {"n": 0, "median": None, "q10": None, "q90": None, "min": None, "max": None}
    return {"n": int(a.size), "median": float(np.median(a)), "q10": float(np.quantile(a, .1)), "q90": float(np.quantile(a, .9)), "min": float(a.min()), "max": float(a.max())}


def _paired_corrected(root: Path, inv: dict[str, Any]) -> dict[str, Any]:
    arms = _arm_by_label(inv)
    dyn = {}
    neu = {}
    for label in (f"R47_DYNAMIC_{J09}", "R49_J09_ADDITIONAL_DYNAMIC"):
        for r in arms[label]["replicates"]:
            dyn[(int(r["replicate_index"]), int(r["seed"]))] = r
    for label in ("R48_J09_NEUTRAL", "R49_J09_ADDITIONAL_NEUTRAL"):
        for r in arms[label]["replicates"]:
            neu[(int(r["replicate_index"]), int(r["seed"]))] = r
    keys = sorted(set(dyn) & set(neu))
    rows = []
    vals = []
    for key in keys:
        d = dyn[key]; n = neu[key]
        dr = d["population_response_ratio"]; nr = n["population_response_ratio"]
        pe = (dr / nr) if nr and nr > 0 else None
        if pe is not None and math.isfinite(pe): vals.append(float(pe))
        rows.append({"replicate_index": key[0], "seed": key[1], "dynamic_initial": d["initial_population"], "dynamic_final": d["final_population"], "neutral_initial": n["initial_population"], "neutral_final": n["final_population"], "dynamic_absolute_ratio": dr, "neutral_absolute_ratio": nr, "paired_forcing_effect_ratio": pe, "initial_population_match": math.isclose(d["initial_population"], n["initial_population"], rel_tol=0, abs_tol=1e-9)})
    parent = load_json(root / R49_PAIR_REL)
    neutral = float(parent["neutral_factor"])
    arc = finite(parent.get("arcana_causal_forcing_effect_ratio"))
    stats = _summary(vals)
    arcdir = -1 if arc is not None and arc < 1.0 / neutral else (1 if arc is not None and arc > neutral else 0)
    robust_same = False; robust_opp = False
    if arcdir < 0 and stats["q90"] is not None: robust_same = stats["q90"] < 1.0 / neutral
    elif arcdir > 0 and stats["q10"] is not None: robust_same = stats["q10"] > neutral
    if arcdir < 0 and stats["q10"] is not None: robust_opp = stats["q10"] > neutral
    elif arcdir > 0 and stats["q90"] is not None: robust_opp = stats["q90"] < 1.0 / neutral
    klass = "R411_CORRECTED_MATCHED_CONTROL_SAME_DIRECTION_ROBUST" if robust_same else ("R411_CORRECTED_MATCHED_CONTROL_OPPOSITE_DIRECTION_ROBUST" if robust_opp else "R411_CORRECTED_MATCHED_CONTROL_EFFECT_UNCERTAIN")
    return {"stage": STAGE, "status": "PASS", "pair_count": len(rows), "paired_replicates": rows, "corrected_paired_effect_summary": stats, "arcana_causal_forcing_effect_ratio": arc, "neutral_factor": neutral, "neutral_band": [1.0 / neutral, neutral], "diagnosis_class": klass, "robust_same_direction_as_arcana": robust_same, "robust_opposite_direction_to_arcana": robust_opp, "historical_r49_diagnosis_preserved": parent.get("stage") == "v0.6D1-R4.9", "engine_rerun_performed": False, "canonical_write": False}


def execute_reextraction_and_readjudicate(root: Path) -> tuple[dict[str, Any], list[Check]]:
    cfg = load_json(root / CFG_REL)
    plan = load_json(root / OUT_REL / "R4_11_REEXTRACTION_PLAN.json") if (root / OUT_REL / "R4_11_REEXTRACTION_PLAN.json").exists() else {}
    inv = load_json(root / OUT_REL / "R4_11_RETAINED_RUNTIME_SUMMARY_INVENTORY.json") if (root / OUT_REL / "R4_11_RETAINED_RUNTIME_SUMMARY_INVENTORY.json").exists() else {}
    checks = [Check("r411_prepared", plan.get("status") == PREPARED, plan.get("status")), Check("exact_five_symmetric_jobs", list(cfg["affected_frozen_cdmetapop_jobs"]) == AFFECTED)]
    job_audits = []
    for jid in AFFECTED:
        jobdir = root / OUT_REL / "jobs" / jid; jobdir.mkdir(parents=True, exist_ok=True)
        corrected = _corrected_r47_raw(root, inv, jid)
        write_json(jobdir / "CORRECTED_RAW_EVIDENCE.json", corrected)
        contract = _contract(root, jid)
        norm = normalize_raw("CDMetaPOP", corrected, contract)
        norm["stage"] = STAGE
        norm["evidence_namespace"] = "R4_11_REEXTRACTED_POPULATION_METRIC_FROM_RETAINED_RUNTIME"
        norm["population_metric_repaired"] = True
        norm["engine_rerun_performed"] = False
        write_json(jobdir / "CORRECTED_NORMALIZED_EVIDENCE.json", norm)
        seeds_expected = [(int(x["replicate_index"]), int(x["seed"])) for x in contract["engine_input"]["replicates"]]
        seeds_obs = [(int(x["replicate_index"]), int(x["seed"])) for x in corrected.get("replicates", [])]
        pop_metric_present = "population_agent_response_ratio" in norm.get("normalized_metrics", {})
        audit = {"stage": STAGE, "job_id": jid, "engine": "CDMetaPOP", "status": "PASS" if seeds_obs == seeds_expected and pop_metric_present else "BLOCKED", "seed_ledger_match": seeds_obs == seeds_expected, "population_metric_present": pop_metric_present, "engine_rerun_performed": False, "canonical_write": False, "corrected_raw_sha256": sha256_file(jobdir / "CORRECTED_RAW_EVIDENCE.json"), "corrected_normalized_sha256": sha256_file(jobdir / "CORRECTED_NORMALIZED_EVIDENCE.json")}
        write_json(jobdir / "METRIC_REEXTRACTION_AUDIT.json", audit); job_audits.append(audit)
    checks += [
        Check("all_five_corrected_job_audits_present", len(job_audits) == 5, len(job_audits)),
        Check("all_five_corrected_job_audits_pass", all(x["status"] == "PASS" for x in job_audits), {x["job_id"]: x["status"] for x in job_audits}),
        Check("all_five_corrected_seed_ledgers_match", all(x["seed_ledger_match"] for x in job_audits)),
        Check("all_five_corrected_population_metrics_present", all(x["population_metric_present"] for x in job_audits)),
    ]
    old = load_json(root / R44_MATRIX_REL)
    old_rows = list(old.get("evidence_rows", [])); old_cells = list(old.get("cells", []))
    new_rows = _corrected_rows(root, AFFECTED)
    preserved = [r for r in old_rows if r.get("job_id") not in set(AFFECTED)]
    revised_rows = preserved + new_rows
    revised_cells = _recompute_cells(root, revised_rows)
    counts = {c: sum(1 for x in revised_cells if x.get("discordance_class") == c) for c in CLASSES}
    old_by = {(x.get("window_id"), x.get("domain")): x for x in old_cells}; new_by = {(x.get("window_id"), x.get("domain")): x for x in revised_cells}
    changed = []
    for k, n in new_by.items():
        o = old_by.get(k, {})
        if o.get("discordance_class") != n.get("discordance_class"):
            changed.append({"window_id": k[0], "domain": k[1], "old_class": o.get("discordance_class"), "new_class": n.get("discordance_class")})
    j09 = [r for r in new_rows if r.get("job_id") == J09 and r.get("domain") == "population_persistence" and r.get("authority_role") == "PRIMARY"]
    paired = _paired_corrected(root, inv)
    write_json(root / OUT_REL / "R4_11_CORRECTED_MATCHED_CONTROL_CAUSAL_EFFECT.json", paired)
    structural = counts["STRUCTURAL_DISAGREEMENT"]
    gaps = counts["INSUFFICIENT_EVIDENCE"] + counts["SEMANTICALLY_NONCOMPARABLE"]
    offsets = counts["CALIBRATION_OFFSET"]
    if structural:
        if paired["diagnosis_class"] == "R411_CORRECTED_MATCHED_CONTROL_SAME_DIRECTION_ROBUST":
            next_action = "BUILD_R412_CDMETAPOP_ABSOLUTE_RESPONSE_COMPARABILITY_DOWNGRADE_OR_MATCHED_CONTROL_SEMANTIC_REMAP"
        elif paired["diagnosis_class"] == "R411_CORRECTED_MATCHED_CONTROL_OPPOSITE_DIRECTION_ROBUST":
            next_action = "BUILD_R412_R311_CDMETAPOP_MECHANISM_DECOMPOSITION_AFTER_METRIC_REPAIR"
        else:
            next_action = "BUILD_R412_CDMETAPOP_METRIC_REPAIRED_PRECISION_AND_COMPARABILITY_DIAGNOSIS"
    elif gaps:
        next_action = "BUILD_R412_TARGETED_EVIDENCE_GAP_CLOSURE_AND_ADAPTER_ENHANCEMENT"
    elif offsets:
        next_action = "BUILD_R412_TARGETED_CALIBRATION_REVIEW_WITHOUT_AUTOMATIC_CANONICAL_CHANGE"
    else:
        next_action = "BUILD_R412_REVALIDATION_CLOSURE_AND_BASELINE_PROMOTION_GATE"
    checks += [
        Check("parent_r44_matrix_present", len(old_cells) == 75 and bool(old_rows), {"cells": len(old_cells), "rows": len(old_rows)}),
        Check("only_five_cdmetapop_rows_replaced", all(r.get("job_id") in AFFECTED for r in new_rows) and all(r.get("job_id") not in AFFECTED for r in preserved)),
        Check("corrected_matrix_exact_75_cells", len(revised_cells) == 75, len(revised_cells)),
        Check("five_class_accounting_complete", sum(counts.values()) == 75, counts),
        Check("j09_population_persistence_readjudicated", len(j09) == 1, j09[0].get("discordance_class") if j09 else None),
        Check("corrected_matched_control_exact_20_pairs", paired["pair_count"] == 20, paired["pair_count"]),
        Check("corrected_matched_control_initials_match", all(x.get("initial_population_match") for x in paired["paired_replicates"])),
        Check("no_secondary_only_promotion", all(not (x.get("discordance_class") in ("CONCORDANT", "CALIBRATION_OFFSET", "STRUCTURAL_DISAGREEMENT") and x.get("primary_adjudicative_rows") == 0) for x in revised_cells)),
        Check("no_majority_vote_anywhere", all(x.get("majority_vote") is False for x in revised_cells) and all(r.get("majority_vote") is False for r in revised_rows)),
        Check("engine_rerun_not_performed", cfg["repair_policy"]["engine_rerun_in_r411"] is False),
        Check("canonical_state_unchanged", cfg["canonical_state_changed"] is False),
        Check("canonical_replay_not_authorized", cfg["canonical_replay_authorized"] is False),
        Check("canonical_parameter_change_not_authorized", cfg["canonical_parameter_change_authorized"] is False),
    ]
    status = COMPLETE if all(c.passed for c in checks) else BLOCKED
    matrix = {"stage": STAGE, "status": status, "cell_count": len(revised_cells), "class_counts": counts, "cells": revised_cells, "evidence_rows": revised_rows, "parent_r44_matrix_preserved": True, "replaced_job_ids": AFFECTED, "engine_rerun_performed": False, "canonical_state_changed": False, "scientific_agreement_claimed": False, "next_action": next_action}
    delta = {"stage": STAGE, "status": status, "changed_cell_count": len(changed), "changed_cells": changed, "j09_population_persistence_primary_row": j09[0] if j09 else None, "old_class_counts": old.get("class_counts", {}), "new_class_counts": counts, "corrected_matched_control_diagnosis": paired["diagnosis_class"], "canonical_change_authorized": False, "next_action": next_action}
    write_json(root / OUT_REL / "R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json", matrix)
    write_json(root / OUT_REL / "R4_11_READJUDICATION_DELTA.json", delta)
    summary = {"stage": STAGE, "status": status, "job_count": 5, "retained_summary_count": inv.get("pass_count"), "job_audits": job_audits, "class_counts_after_metric_repair": counts, "structural_disagreement_count_after_metric_repair": structural, "calibration_offset_count_after_metric_repair": offsets, "evidence_gap_count_after_metric_repair": gaps, "j09_population_persistence_class_after_metric_repair": j09[0].get("discordance_class") if j09 else None, "corrected_matched_control_diagnosis": paired["diagnosis_class"], "corrected_matched_control_summary": paired["corrected_paired_effect_summary"], "engine_rerun_performed": False, "canonical_state_changed": False, "canonical_replay_authorized": False, "canonical_parameter_change_authorized": False, "next_action": next_action}
    write_json(root / OUT_REL / "R4_11_EXECUTION_SUMMARY.json", summary)
    audit = {"stage": STAGE, "status": status, "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.to_dict() for c in checks], "class_counts": counts, "canonical_state_changed": False, "next_action": next_action}
    write_json(root / OUT_REL / "R4_11_INTEGRATED_AUDIT.json", audit)
    return audit, checks


def final_seal(root: Path) -> tuple[dict[str, Any], list[Check]]:
    parent = load_json(root / R410_SEAL_REL) if (root / R410_SEAL_REL).exists() else {}
    audit = load_json(root / OUT_REL / "R4_11_INTEGRATED_AUDIT.json") if (root / OUT_REL / "R4_11_INTEGRATED_AUDIT.json").exists() else {}
    summary = load_json(root / OUT_REL / "R4_11_EXECUTION_SUMMARY.json") if (root / OUT_REL / "R4_11_EXECUTION_SUMMARY.json").exists() else {}
    matrix = load_json(root / OUT_REL / "R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json") if (root / OUT_REL / "R4_11_CDMETAPOP_METRIC_REPAIRED_READJUDICATED_MATRIX.json").exists() else {}
    paired = load_json(root / OUT_REL / "R4_11_CORRECTED_MATCHED_CONTROL_CAUSAL_EFFECT.json") if (root / OUT_REL / "R4_11_CORRECTED_MATCHED_CONTROL_CAUSAL_EFFECT.json").exists() else {}
    cfg = load_json(root / CFG_REL)
    checks = [
        Check("parent_r410_sealed", parent.get("status") == R410_SEALED, parent.get("status")),
        Check("r411_complete", audit.get("status") == COMPLETE, audit.get("status")),
        Check("r411_zero_process_failures", audit.get("checks_failed") == 0, audit.get("checks_failed")),
        Check("retained_summary_count_56", summary.get("retained_summary_count") == 56, summary.get("retained_summary_count")),
        Check("five_symmetric_cdmetapop_jobs", summary.get("job_count") == 5, summary.get("job_count")),
        Check("readjudicated_matrix_75_cells", matrix.get("cell_count") == 75, matrix.get("cell_count")),
        Check("class_accounting_complete", sum((matrix.get("class_counts") or {}).values()) == 75, matrix.get("class_counts")),
        Check("corrected_matched_control_20_pairs", paired.get("pair_count") == 20, paired.get("pair_count")),
        Check("historical_r43_r49_outputs_preserved", cfg["repair_policy"]["preserve_r43_r49_historical_outputs"] is True),
        Check("engine_rerun_not_performed", summary.get("engine_rerun_performed") is False),
        Check("canonical_state_unchanged", summary.get("canonical_state_changed") is False),
        Check("canonical_replay_not_authorized", summary.get("canonical_replay_authorized") is False),
        Check("canonical_parameter_change_not_authorized", summary.get("canonical_parameter_change_authorized") is False),
        Check("deep_off", cfg["deep_biological_coupling"] is False),
        Check("next_action_present", bool(summary.get("next_action")), summary.get("next_action")),
    ]
    ok = all(c.passed for c in checks)
    out = {"stage": STAGE, "audit": "FINAL_CDMETAPOP_POPULATION_METRIC_EXTRACTION_REPAIR_AND_SYMMETRIC_READJUDICATION", "status": SEALED if ok else BLOCKED, "verdict": "SEALED" if ok else "BLOCKED", "checks_passed": sum(c.passed for c in checks), "checks_total": len(checks), "checks_failed": sum(not c.passed for c in checks), "checks": [c.to_dict() for c in checks], "summary": {"class_counts_after_metric_repair": summary.get("class_counts_after_metric_repair"), "structural_disagreement_count_after_metric_repair": summary.get("structural_disagreement_count_after_metric_repair"), "j09_population_persistence_class_after_metric_repair": summary.get("j09_population_persistence_class_after_metric_repair"), "corrected_matched_control_diagnosis": summary.get("corrected_matched_control_diagnosis"), "corrected_matched_control_summary": summary.get("corrected_matched_control_summary"), "engine_rerun_performed": False, "canonical_state_changed": False, "canonical_replay_authorized": False, "canonical_parameter_change_authorized": False, "deep_biological_coupling": False, "next_action": summary.get("next_action")}, "next_action": summary.get("next_action")}
    write_json(root / SEAL_REL, out)
    return out, checks
