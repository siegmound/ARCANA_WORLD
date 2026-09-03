from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.scientific_engines.r37h_closed_loop_binding import (
    BRANCH_K,
    R37HClosedLoopConfig,
    compare_closed_loop_branches,
    run_closed_loop_branch,
)


def _load_inputs():
    common = np.load(ROOT / "outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz", allow_pickle=False)
    a1 = np.load(ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz", allow_pickle=False)
    md = json.loads((ROOT / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    rows = md["species"] if isinstance(md, dict) and "species" in md else md
    return common, a1, rows


def run_one(label: str, end_age_ma: float, smoke: bool, out_dir: Path) -> Path:
    common, a1, rows = _load_inputs()
    cfg = R37HClosedLoopConfig(
        end_age_ma=end_age_ma,
        diagnostic_smoke=smoke,
        branch_label=label,
        adaptive_k_eff=BRANCH_K[label],
    )
    t0 = time.time()
    out = run_closed_loop_branch(common, a1, rows, cfg)
    out["wall_seconds"] = time.time() - t0
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"210_to_{str(end_age_ma).replace('.', 'p')}Ma_R3_7H_{label}.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--end-age-ma", type=float, default=150.0)
    ap.add_argument("--diagnostic-smoke", action="store_true")
    ap.add_argument("--branch", choices=["K_LOW", "K_CENTER", "K_HIGH"])
    ap.add_argument("--aggregate-only", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "local_runs/v0_6D1_R3_7H")
    args = ap.parse_args()

    if args.aggregate_only:
        branches = {}
        for label in ("K_LOW", "K_CENTER", "K_HIGH"):
            p = args.out_dir / f"210_to_{str(args.end_age_ma).replace('.', 'p')}Ma_R3_7H_{label}.json"
            branches[label] = json.loads(p.read_text(encoding="utf-8"))
        comp = compare_closed_loop_branches(branches)
        governed = bool((not args.diagnostic_smoke) and comp["all_branches_valid"] and comp["all_branches_clear_of_ceiling"] and comp["qualitative_ceiling_coherence"])
        summary = {
            "schema": "ARCANA_R37H_CLOSED_LOOP_THREE_BRANCH_VALIDATION_V1",
            "stage": "v0.6D1-R3.7H",
            "verdict": (
                "PASS_CLOSED_LOOP_THREE_BRANCH_VALIDATION__PROMOTION_REVIEW_REQUIRED"
                if governed else
                "REVIEW_CLOSED_LOOP_THREE_BRANCH_VALIDATION__PROMOTION_NOT_AUTHORIZED"
            ),
            "end_age_ma": args.end_age_ma,
            "diagnostic_smoke": bool(args.diagnostic_smoke),
            "comparison": comp,
            "production_promotion_gate": {
                "all_branches_valid": comp["all_branches_valid"],
                "all_branches_clear_of_ceiling": comp["all_branches_clear_of_ceiling"],
                "qualitative_ceiling_coherence": comp["qualitative_ceiling_coherence"],
                "governed_closed_loop_pass": governed,
            },
            "governance": {
                "production_runtime_replacement_authorized": False,
                "promotion_requires_post_run_review": True,
                "scalar_K_eff_production_authorized": False,
            },
        }
        sp = args.out_dir / f"210_to_{str(args.end_age_ma).replace('.', 'p')}Ma_R3_7H_summary.json"
        sp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        if not args.diagnostic_smoke and not governed:
            raise SystemExit(2)
        return

    if args.branch:
        p = run_one(args.branch, args.end_age_ma, args.diagnostic_smoke, args.out_dir)
        out = json.loads(p.read_text(encoding="utf-8"))
        print(json.dumps({
            "stage": out["stage"], "branch": out["branch_label"], "K_eff": out["K_eff"],
            "wall_seconds": out["wall_seconds"], "biology_steps": out["biology_steps"],
            "peak_q": out["peak_q"], "clipping_contacts": out["clipping_contacts"],
            "final_total_population": out["final_total_population"], "species_count": out["species_count"],
            "component_count": out["component_count"], "event_counts": out["event_counts"],
            "closed_loop_gate_pass": out["closed_loop_gate_pass"], "result": str(p),
        }, indent=2))
        if not out["closed_loop_gate_pass"]:
            raise SystemExit(2)
        return

    # Sequential convenience mode. The PowerShell runner launches branches in
    # parallel on Windows; this path remains useful for smoke/debug.
    for label in ("K_LOW", "K_CENTER", "K_HIGH"):
        run_one(label, args.end_age_ma, args.diagnostic_smoke, args.out_dir)
    sys.argv = [sys.argv[0], "--end-age-ma", str(args.end_age_ma), "--out-dir", str(args.out_dir), "--aggregate-only"] + (["--diagnostic-smoke"] if args.diagnostic_smoke else [])
    main()


if __name__ == "__main__":
    main()
