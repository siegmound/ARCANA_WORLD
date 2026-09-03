from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.scientific_engines.r37f_stress_window_shadow_replay import (
    R37FStressWindowConfig,
    run_stress_window_shadow,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--end-age-ma", type=float, default=188.0)
    ap.add_argument("--diagnostic-smoke", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "local_runs/v0_6D1_R3_7F")
    args = ap.parse_args()

    common = np.load(
        ROOT / "outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz",
        allow_pickle=False,
    )
    a1 = np.load(
        ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz",
        allow_pickle=False,
    )
    md = json.loads((ROOT / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text(encoding="utf-8"))
    rows = md["species"] if isinstance(md, dict) and "species" in md else md

    cfg = R37FStressWindowConfig(
        end_age_ma=float(args.end_age_ma),
        diagnostic_smoke=bool(args.diagnostic_smoke),
    )
    t0 = time.time()
    out = run_stress_window_shadow(common, a1, rows, cfg)
    out["wall_seconds"] = time.time() - t0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"210_to_{str(args.end_age_ma).replace('.', 'p')}Ma"
    full = args.out_dir / f"{tag}_R3_7F_shadow_replay.json"
    summary = args.out_dir / f"{tag}_R3_7F_summary.json"
    full.write_text(json.dumps(out, indent=2), encoding="utf-8")
    summary.write_text(json.dumps({k: v for k, v in out.items() if k != "records"}, indent=2), encoding="utf-8")

    print(json.dumps({
        "stage": out["stage"],
        "verdict": out["verdict"],
        "wall_seconds": out["wall_seconds"],
        "biology_steps": out["shadow"]["window"]["biology_steps"],
        "canonical_parity": out["canonical_parity"]["all_core_parity"],
        "event_counts": out["shadow"]["canonical_event_counts"],
        "legacy_peak_q": out["legacy_peak_q"],
        "legacy_steps_with_clipping": out["legacy_stress_diagnostics"]["steps_with_clipping"],
        "legacy_first_clipping_age_ma": out["legacy_stress_diagnostics"]["first_clipping_age_ma"],
        "shadow_peak_q": out["shadow_peak_q"],
        "shadow_ceiling_contacts": out["shadow"]["ceiling_contacts_by_variant"],
        "headroom_gain_vs_legacy_peak_q": out["headroom_gain_vs_legacy_peak_q"],
        "max_K_envelope_q_spread": out["shadow"]["trajectory_max_q"]["maximum_absolute_K_envelope_spread"],
        "final_S_median_relative_span": out["k_envelope_sensitivity"]["same_species_S_median"]["final_relative_span_vs_abs_center"],
        "stress_gate": out["stress_gate"],
        "summary": str(summary),
        "full": str(full),
    }, indent=2))

    if not args.diagnostic_smoke and not out["stress_gate"]["governed_stress_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
