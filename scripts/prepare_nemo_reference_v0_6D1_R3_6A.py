from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np

from arcana_worldsim.scientific_engines import NEMO_242, Nemo242Adapter, Nemo242MappingSpec, experiment_from_r3_state_npz
from arcana_worldsim.scientific_engines.serialization import save_experiment, save_evidence


def load_matrix(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".npy":
        return np.load(path, allow_pickle=False)
    if path.suffix.lower() == ".npz":
        with np.load(path, allow_pickle=False) as z:
            if len(z.files) != 1:
                raise ValueError("exchange .npz must contain exactly one array")
            return z[z.files[0]]
    return np.loadtxt(path, delimiter="\t")


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare a governed NEMO 2.4.2 reference bridge from an ARCANA R3/R3.5 state NPZ.")
    ap.add_argument("state_npz", type=Path)
    ap.add_argument("exchange_matrix", type=Path, help="Explicit NxN effective exchange matrix for selected demes (.npy/.npz/.tsv).")
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--indices", default=None, help="Comma-separated component indices; default all components.")
    ap.add_argument("--age-ma", type=float, required=True)
    ap.add_argument("--seed", type=int, default=917231)
    ap.add_argument("--replicate", type=int, default=0)
    ap.add_argument("--population-scale", type=float, required=True)
    ap.add_argument("--k-multiplier", type=float, default=1.5)
    ap.add_argument("--loci-per-trait", type=int, default=64)
    ap.add_argument("--generations", type=int, default=1000)
    ap.add_argument("--nemo-template", type=str, default=None)
    ap.add_argument("--nemo-executable", type=str, default="nemo2.4.2")
    args = ap.parse_args()

    idx = None if args.indices is None else [int(x) for x in args.indices.split(",") if x.strip()]
    G = load_matrix(args.exchange_matrix)
    exp = experiment_from_r3_state_npz(
        args.state_npz, engine=NEMO_242,
        experiment_id=f"R36A-NEMO-{args.age_ma:g}Ma-r{args.replicate}",
        arcana_stage="v0.6D1-R3.5", age_ma=args.age_ma, random_seed=args.seed,
        replicate_id=args.replicate, component_indices=idx,
        extra_arrays={"exchange_matrix": G},
        assumptions=("NEMO is independent reference evidence only", "ARCANA canonical state is immutable to this bridge"),
        requested_outputs=("trait_mean", "additive_variance", "allele_frequencies", "heterozygosity", "population_per_patch"),
    )
    root = args.outdir
    save_experiment(exp, root / "experiment")
    adapter = Nemo242Adapter(Nemo242MappingSpec(
        population_units_to_individuals=args.population_scale,
        carrying_capacity_multiplier=args.k_multiplier,
        loci_per_trait=args.loci_per_trait, generations=args.generations,
        template_path=args.nemo_template, executable=args.nemo_executable,
    ))
    evidence = adapter.run(exp, root / "nemo")
    save_evidence(evidence, root / "evidence")
    print(json.dumps({
        "stage": "v0.6D1-R3.6A", "experiment_sha256": exp.semantic_sha256,
        "evidence_sha256": evidence.semantic_sha256, "status": evidence.status,
        "canonical_write_allowed": False,
    }, indent=2))
    return 0 if evidence.status != "ENGINE_FAILED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
