from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcana_worldsim.scientific_engines import (  # noqa:E402
    Nemo242R36BAdapter, Nemo242MappingSpec, NemoQTLArchitectureSpec,
    build_qtl_realization, canonical_r36b_scenarios, scenario_to_experiment,
    write_qtl_realization, write_scenario,
)
from arcana_worldsim.scientific_engines.serialization import save_evidence, save_experiment  # noqa:E402


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare the governed ARCANA R3.6B NEMO 2.4.2 QTL ensemble benchmark suite.")
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--replicates", type=int, default=8)
    ap.add_argument("--seed", type=int, default=36062026)
    ap.add_argument("--loci-per-trait", type=int, default=64)
    ap.add_argument("--individuals", type=int, default=2000)
    ap.add_argument("--q-star", type=float, default=0.045)
    ap.add_argument("--nemo-template", type=Path, default=None, help="Version-validated NEMO 2.4.2 template. If absent, preparation-only mode is enforced.")
    ap.add_argument("--nemo-executable", default="nemo2.4.2")
    args = ap.parse_args()
    if args.replicates < 1:
        raise ValueError("replicates must be >=1")
    if abs(args.q_star - 0.045) > 1e-15:
        raise ValueError("R3.6B canonical reference fixes q*=0.045; alternate q requires a new governed sensitivity stage")

    root = args.outdir
    root.mkdir(parents=True, exist_ok=True)
    scenarios = canonical_r36b_scenarios(q_star=args.q_star, n_individuals=args.individuals)
    qspec = NemoQTLArchitectureSpec(loci_per_trait=args.loci_per_trait, individual_sample_size=args.individuals)
    records = []

    for si, scenario in enumerate(scenarios):
        sroot = root / scenario.name
        write_scenario(scenario, sroot / "scenario_authority")
        for rep in range(args.replicates):
            seed = int(args.seed + si * 100_000 + rep)
            exp = scenario_to_experiment(scenario, seed=seed, replicate_id=rep)
            rroot = sroot / f"rep_{rep:03d}"
            save_experiment(exp, rroot / "experiment")

            realization = build_qtl_realization(
                scenario.normalized_trait_means,
                scenario.normalized_additive_variance,
                trait_axes=(0, 1), seed=seed, spec=qspec,
                individuals_per_patch=scenario.population_individuals,
            )
            nemo_root = rroot / "nemo"
            write_qtl_realization(realization, nemo_root / "qtl", [str(x) for x in exp.arrays["component_ids"]])
            shutil.copytree(sroot / "scenario_authority", nemo_root / "scenario", dirs_exist_ok=True)

            adapter = Nemo242R36BAdapter(Nemo242MappingSpec(
                population_units_to_individuals=1.0,
                carrying_capacity_multiplier=1.0,
                quantitative_trait_axes=(0, 1),
                loci_per_trait=args.loci_per_trait,
                generations=scenario.generations,
                template_path=str(args.nemo_template) if args.nemo_template else None,
                executable=args.nemo_executable,
            ))
            ev = adapter.run(exp, nemo_root)
            save_evidence(ev, rroot / "evidence")
            records.append({
                "scenario": scenario.name,
                "replicate": rep,
                "seed": seed,
                "experiment_sha256": exp.semantic_sha256,
                "qtl_realization_sha256": realization.semantic_sha256,
                "evidence_sha256": ev.semantic_sha256,
                "status": ev.status,
                "max_expected_mean_abs_error": float(np.max(np.abs(realization.expected_means - realization.target_means))),
                "max_expected_va_abs_error": float(np.max(np.abs(realization.expected_variances - realization.target_variances))),
                "max_sampled_mean_abs_error": float(np.max(np.abs(realization.sampled_means - realization.target_means))),
                "max_sampled_va_abs_error": float(np.max(np.abs(realization.sampled_variances - realization.target_variances))),
            })

    summary = {
        "schema": "ARCANA_NEMO_R36B_QTL_ENSEMBLE_SUITE_V1",
        "stage": "v0.6D1-R3.6B",
        "status": "PREPARED_REFERENCE_INPUTS" if args.nemo_template is None else "ENGINE_RUNS_ATTEMPTED",
        "engine": "NEMO",
        "engine_version_required": "2.4.2",
        "q_star": args.q_star,
        "loci_per_trait": args.loci_per_trait,
        "replicates_per_scenario": args.replicates,
        "scenario_count": len(scenarios),
        "record_count": len(records),
        "template_supplied": args.nemo_template is not None,
        "canonical_write_allowed": False,
        "automatic_calibration_allowed": False,
        "records": records,
    }
    (root / "R3_6B_NEMO_QTL_ENSEMBLE_SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("stage", "status", "engine_version_required", "scenario_count", "record_count", "canonical_write_allowed")}, indent=2))
    return 0 if all(r["status"] != "ENGINE_FAILED" for r in records) else 2


if __name__ == "__main__":
    raise SystemExit(main())
