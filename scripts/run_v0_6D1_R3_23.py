from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import hashlib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcana_worldsim.scientific_engines.r323_functional_ensemble import (  # noqa: E402
    R323Config, R323GateError, STAGE, EVIDENCE_SOURCES, HERITABILITY_PRIORS, RATE_REGIMES,
    audit_result, build_summary, sha256_file, simulate_ensemble, trait_calibration_registry,
    validate_inputs, write_json,
)


def manifest_for(out: Path, names: list[str]) -> dict:
    return {
        "stage": STAGE,
        "status": "CANDIDATE_OUTPUT_MANIFEST",
        "files": {n: {"sha256": sha256_file(out / n), "bytes": (out / n).stat().st_size} for n in names},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--output-dir", type=Path)
    ap.add_argument("--replicates-per-regime", type=int, default=32)
    ap.add_argument("--seed", type=int, default=230823)
    ns = ap.parse_args()
    root = ns.root.resolve()
    out = (ns.output_dir or (root / "outputs" / "v0_6D1_R3_23")).resolve()
    cfg = R323Config(replicates_per_regime=ns.replicates_per_regime, seed=ns.seed)

    try:
        inputs = validate_inputs(root)
        sim = simulate_ensemble(inputs, cfg)
        summary = build_summary(inputs, sim, cfg)
        audit = audit_result(inputs, sim, summary)
        if audit["checks_failed"]:
            raise R323GateError(f"R3.23 integrated audit failed: {audit['checks_failed']}")

        out.mkdir(parents=True, exist_ok=True)
        write_json(out / "R3_23_COMPARATIVE_CALIBRATION_AUTHORITY.json", {
            "stage": STAGE,
            "status": "COMPARATIVE_PRIOR_CALIBRATION_CANDIDATE",
            "evidence_sources": EVIDENCE_SOURCES,
            "heritability_priors": HERITABILITY_PRIORS,
            "rate_regimes": RATE_REGIMES,
            "trait_calibration": trait_calibration_registry(),
            "human_anchor": False,
            "deep_biological_coupling": False,
        })
        write_json(out / "R3_23_ROOT_ANCESTRAL_PRIOR_SUMMARY.json", {
            "stage": STAGE, "status": "ROOT_PRIOR_ENSEMBLE_INITIALIZATION",
            "root_count": len(sim["root_prior_records"]), "roots": sim["root_prior_records"],
        })
        write_json(out / "R3_23_PRESENT_FUNCTIONAL_SUMMARY.json", summary)
        write_json(out / "R3_23_INTEGRATED_AUDIT.json", audit)
        write_json(out / "R3_23_REPLAY_PROVENANCE.json", {
            "stage": STAGE,
            "parent_r322_seal_status": inputs["seal_audit"]["status"],
            "source_checkpoint": inputs["source_checkpoint"],
            "ensemble_members": int(sim["ensemble"].shape[0]),
            "replicates_per_regime": cfg.replicates_per_regime,
            "seed": cfg.seed,
            "rate_regime_member_order": sim["regimes"].tolist(),
            "component_order": sim["component_order"],
            "present_species_order": sim["present_species_order"],
            "functional_va_materialized": False,
            "functional_gcov_materialized": False,
            "plasticity_beta_materialized": False,
            "functional_applicability_code_materialized": False,
            "derived_capability_semantics": "CONDITIONAL_POTENTIAL_NOT_REALIZED_TOOL_BEHAVIOR_OR_HUMAN_READINESS",
            "h0_mutated": False,
            "human_target": False,
            "deep_biological_coupling": False,
        })
        np.savez_compressed(
            out / "R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz",
            functional_mean_z_ensemble=sim["ensemble"].astype(np.float64),
            species_mean_z_ensemble=sim["species_ensemble"].astype(np.float64),
            tool_use_potential_ensemble=sim["tool_use"].astype(np.float64),
            environmental_problem_solving_ensemble=sim["problem_solving"].astype(np.float64),
            rate_regime=sim["regimes"],
            trait_ids=np.asarray(summary["traits"] and [x["trait_id"] for x in summary["traits"]], dtype="U64"),
            component_ids=np.asarray(sim["component_order"], dtype="U64"),
            species_ids=np.asarray(sim["present_species_order"], dtype="U64"),
        )
        md = [
            "# ARCANA WorldSim v0.6D1-R3.23 — Integrated Audit",
            "",
            f"Status: `{audit['status']}`",
            f"Checks: **{audit['checks_passed']}/{audit['checks_total']} PASS**",
            f"Ensemble histories: **{sim['ensemble'].shape[0]}**",
            "",
            "R3.23 materializes an uncertainty-aware functional latent ensemble over the fixed H0 lineage history.",
            "It does not modify H0, enable Deep, select a human lineage, or claim ensemble uncertainty is additive genetic variance.",
            "",
        ]
        (out / "R3_23_AUDIT.md").write_text("\n".join(md), encoding="utf-8")
        names = sorted(p.name for p in out.iterdir() if p.is_file() and p.name != "R3_23_OUTPUT_MANIFEST.json")
        write_json(out / "R3_23_OUTPUT_MANIFEST.json", manifest_for(out, names))

        print(json.dumps({
            "stage": STAGE,
            "status": audit["status"],
            "output_dir": str(out),
            "summary": {
                "ensemble_members": int(sim["ensemble"].shape[0]),
                "rate_regimes": list(RATE_REGIMES),
                "present_species": len(summary["species"]),
                "present_components": len(summary["components"]),
                "primitive_traits": 31,
                "derived_capabilities": 2,
                "functional_va_materialized": False,
                "functional_gcov_materialized": False,
                "human_target": False,
                "deep_biological_coupling": False,
                "checks_passed": audit["checks_passed"],
                "checks_total": audit["checks_total"],
            },
        }, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"stage": STAGE, "status": "FAIL_CLOSED", "error": str(e)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
