from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.scientific_engines.r37h_closed_loop_binding import BRANCH_K
from arcana_worldsim.scientific_engines.r37i_production_runtime import (
    NOMINAL_K_LABEL,
    NOMINAL_K_REFERENCE,
    SEAL_SCHEMA,
    STAGE,
)

EXPECTED_STEPS = 480
BRANCHES = ("K_LOW", "K_CENTER", "K_HIGH")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_one(root: Path, suffix: str) -> Path:
    matches = sorted(p for p in root.rglob("*.json") if p.name.endswith(suffix))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {suffix}; found {len(matches)}")
    return matches[0]


def _load_results(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, str]]:
    sp = _find_one(root, "210_to_150p0Ma_R3_7H_summary.json")
    summary = json.loads(sp.read_text(encoding="utf-8"))
    branches = {}
    hashes = {"summary": sha256(sp)}
    for label in BRANCHES:
        p = _find_one(root, f"210_to_150p0Ma_R3_7H_{label}.json")
        branches[label] = json.loads(p.read_text(encoding="utf-8"))
        hashes[label] = sha256(p)
    return summary, branches, hashes


def review_evidence(summary: dict[str, Any], branches: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    def check(name: str, cond: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    check("summary_stage_r37h", summary.get("stage") == "v0.6D1-R3.7H", summary.get("stage"))
    gate = summary.get("production_promotion_gate", {})
    comp = summary.get("comparison", {})
    check("summary_governed_closed_loop_pass", gate.get("governed_closed_loop_pass") is True, gate)
    check("summary_all_branches_valid", comp.get("all_branches_valid") is True)
    check("summary_all_branches_clear_of_ceiling", comp.get("all_branches_clear_of_ceiling") is True)
    check("summary_qualitative_ceiling_coherence", comp.get("qualitative_ceiling_coherence") is True)

    for label in BRANCHES:
        b = branches[label]
        check(f"{label}_stage", b.get("stage") == "v0.6D1-R3.7H", b.get("stage"))
        check(f"{label}_label", b.get("branch_label") == label, b.get("branch_label"))
        try: kval = float(b.get("K_eff"))
        except Exception: kval = float("nan")
        check(f"{label}_K_exact", math.isfinite(kval) and abs(kval - BRANCH_K[label]) <= 1e-12, kval)
        check(f"{label}_480_steps", int(b.get("biology_steps", -1)) == EXPECTED_STEPS, b.get("biology_steps"))
        check(f"{label}_valid_steps", b.get("valid_biology_steps") is True)
        check(f"{label}_closed_loop_gate", b.get("closed_loop_gate_pass") is True)
        check(f"{label}_zero_clipping", int(b.get("clipping_contacts", -1)) == 0, b.get("clipping_contacts"))
        peak = float(b.get("peak_q", float("nan")))
        check(f"{label}_finite_peak_q", math.isfinite(peak) and peak < 0.08, peak)
        pop = float(b.get("final_total_population", float("nan")))
        check(f"{label}_finite_positive_population", math.isfinite(pop) and pop > 0.0, pop)
        check(f"{label}_positive_species_count", int(b.get("species_count", 0)) > 0, b.get("species_count"))
        check(f"{label}_positive_component_count", int(b.get("component_count", 0)) > 0, b.get("component_count"))

    # Macro/event divergence is evidence to report, not a fitted pass threshold.
    macro_review = {
        "peak_q_by_branch": comp.get("peak_q_by_branch"),
        "max_peak_q_spread": comp.get("max_peak_q_spread"),
        "final_population_by_branch": comp.get("final_population_by_branch"),
        "final_population_relative_span_vs_center": comp.get("final_population_relative_span_vs_center"),
        "species_count_by_branch": comp.get("species_count_by_branch"),
        "component_count_by_branch": comp.get("component_count_by_branch"),
        "event_counts_by_branch": comp.get("event_counts_by_branch"),
        "species_count_exactly_equal": comp.get("species_count_exactly_equal"),
        "component_count_exactly_equal": comp.get("component_count_exactly_equal"),
        "event_counts_exactly_equal": comp.get("event_counts_exactly_equal"),
        "review_semantics": "REPORTED_NOT_THRESHOLD_FITTED",
    }
    passed = all(x["pass"] for x in checks)
    return {
        "stage": STAGE,
        "status": "PASS_R37H_FULL_EVIDENCE_REVIEW" if passed else "FAIL_R37H_FULL_EVIDENCE_REVIEW",
        "checks_passed": sum(x["pass"] for x in checks),
        "check_count": len(checks),
        "checks": checks,
        "macro_and_event_divergence_review": macro_review,
        "promotion_eligible": passed,
    }


def _materialize_seal(review: dict[str, Any], hashes: dict[str, str], source_zip_hash: str | None) -> dict[str, Any]:
    return {
        "schema": SEAL_SCHEMA,
        "stage": STAGE,
        "parent_stage": "v0.6D1-R3.7H",
        "status": "PASS_PRODUCTION_PROMOTION_SEAL",
        "promotion_basis": "R3.7H_FULL_210_TO_150_THREE_BRANCH_CLOSED_LOOP_EVIDENCE_PLUS_R3.7A_G_CHAIN",
        "r37h_full_closed_loop_evidence": {
            "governed_closed_loop_pass": True,
            "source_zip_sha256": source_zip_hash,
            "json_sha256": hashes,
            "review_status": review["status"],
            "checks_passed": review["checks_passed"],
            "check_count": review["check_count"],
        },
        "nominal_reduced_order_reference": {
            "label": NOMINAL_K_LABEL,
            "K_eff": NOMINAL_K_REFERENCE,
            "semantic_role": "OPERATIONAL_REDUCED_ORDER_COORDINATE_REFERENCE_NOT_PHYSICAL_CONSTANT",
        },
        "uncertainty_sentinels": {
            "K_LOW": BRANCH_K["K_LOW"],
            "K_HIGH": BRANCH_K["K_HIGH"],
            "release_validation_required": True,
        },
        "authority": {
            "canonical_runtime_binding_authorized": True,
            "segregation_aware_gene_flow_variance_authorized": True,
            "segregation_aware_coalescence_pooling_authorized": True,
            "nominal_reduced_order_k_reference_authorized": True,
            "scalar_k_physical_constant_authorized": False,
            "k_low_high_release_sentinels_retained": True,
            "mu_b_or_ceiling_change_authorized": False,
            "migration_selection_ri_speciation_paleogeography_authority_changed": False,
        },
        "supersession": {
            "legacy_whole_trait_gene_flow_variance_production_authority": "RETIRED_FOR_WORLD1_RUNTIME",
            "legacy_whole_trait_coalescence_variance_production_authority": "RETIRED_FOR_WORLD1_RUNTIME",
            "r3_7h_closed_loop_binding": "PROMOTED_AS_R3_7I_CANONICAL_RUNTIME_IMPLEMENTATION",
        },
        "macro_and_event_review": review["macro_and_event_divergence_review"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--r37h-results-dir", type=Path)
    ap.add_argument("--r37h-results-zip", type=Path)
    ap.add_argument("--approve-promotion", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs/v0_6D1_R3_7I")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if bool(args.r37h_results_dir) == bool(args.r37h_results_zip):
        status = {
            "stage": STAGE,
            "status": "BLOCKED_R37H_FULL_EVIDENCE_PATH_REQUIRED",
            "promotion_seal_written": False,
        }
        (args.out_dir / "PRODUCTION_PROMOTION_REVIEW_v0_6D1_R3_7I.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(json.dumps(status, indent=2))
        raise SystemExit(2)

    temp = None
    source_zip_hash = None
    try:
        if args.r37h_results_zip:
            zp = args.r37h_results_zip.resolve()
            if not zp.exists():
                raise RuntimeError("R3.7H results zip not found")
            source_zip_hash = sha256(zp)
            temp = tempfile.TemporaryDirectory(prefix="arcana_r37i_")
            root = Path(temp.name)
            with zipfile.ZipFile(zp) as zf:
                zf.extractall(root)
        else:
            root = args.r37h_results_dir.resolve()
            if not root.exists():
                raise RuntimeError("R3.7H results directory not found")

        summary, branches, hashes = _load_results(root)
        review = review_evidence(summary, branches)
        review["source_zip_sha256"] = source_zip_hash
        rp = args.out_dir / "PRODUCTION_PROMOTION_REVIEW_v0_6D1_R3_7I.json"
        rp.write_text(json.dumps(review, indent=2), encoding="utf-8")

        if not review["promotion_eligible"]:
            print(json.dumps({
                "stage": STAGE,
                "status": review["status"],
                "promotion_seal_written": False,
                "review": str(rp),
            }, indent=2))
            raise SystemExit(2)

        if not args.approve_promotion:
            status = {
                "stage": STAGE,
                "status": "PASS_R37H_EVIDENCE__EXPLICIT_PROMOTION_APPROVAL_REQUIRED",
                "promotion_seal_written": False,
                "review": str(rp),
            }
            print(json.dumps(status, indent=2))
            return

        seal = _materialize_seal(review, hashes, source_zip_hash)
        sp = args.out_dir / "PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json"
        sp.write_text(json.dumps(seal, indent=2), encoding="utf-8")
        print(json.dumps({
            "stage": STAGE,
            "status": seal["status"],
            "promotion_seal_written": True,
            "seal": str(sp),
            "seal_sha256": sha256(sp),
            "review": str(rp),
        }, indent=2))
    finally:
        if temp is not None:
            temp.cleanup()


if __name__ == "__main__":
    main()
