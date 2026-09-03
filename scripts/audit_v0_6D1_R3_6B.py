from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcana_worldsim.scientific_engines import (  # noqa:E402
    NEMO_242, Nemo242R36BAdapter, Nemo242MappingSpec,
    NemoQTLArchitectureSpec, build_qtl_realization,
    canonical_r36b_scenarios, scenario_to_experiment, write_qtl_realization,
)

EXPECTED_PARENT_HASHES = {
    "src/arcana_worldsim/scientific_engines/contracts.py": "4983b25cd3311448bd1bb8dd41b957e6e2d8a2200fcd660343d3e2eda9d47a5b",
    "src/arcana_worldsim/scientific_engines/nemo242.py": "6e4cea2620cfcd475328682c5458a4a54771c36bda8488da828cb9d7004202f5",
    "src/arcana_worldsim/scientific_engines/registry.py": "6706bfbb36490460e3ba16d1c9d4ad3b0550b6f30d1db246eb341870ee771a27",
    "src/rebased_natural_control_runtime_v0_6D1_R3_4.py": "087d05f532d84f53f8c99d08ae0099657792526eb3aa97bab7cb9e64cb342e45",
    "src/rebased_natural_control_runtime_v0_6D1_R3_5.py": "634237eb15383000e88180b890ead9b6facc281c0a77eb5ce00efe32f3d0bc95",
    "src/d3_additive_variance_v0_6_3D3_3A.py": "3b235b186e234f66a77443bec3a46c80ef699ecd715737be7d36103db01b4c21",
    "src/d3_paleogeographic_history_v0_6_3D3_2C.py": "5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730",
}


def digest(p: Path) -> str:
    return sha256(p.read_bytes()).hexdigest()


def main() -> int:
    checks = []
    def ck(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": str(detail)})

    cfg = json.loads((ROOT / "configs/world1_nemo_qtl_reference_v0_6D1_R3_6B.json").read_text())
    ck("stage_id", cfg["stage"] == "v0.6D1-R3.6B")
    ck("parent_r36a", cfg["parent_stage"] == "v0.6D1-R3.6A")
    ck("nemo_pinned_242", cfg["engine_version_required"] == "2.4.2" == NEMO_242.version)
    ck("reference_oracle", cfg["role"] == "REFERENCE_ORACLE")
    ck("canonical_write_false", cfg["canonical_write_allowed"] is False)
    ck("auto_calibration_false", cfg["automatic_calibration_allowed"] is False)
    ck("qstar_fixed", abs(float(cfg["q_star"]) - 0.045) < 1e-15)
    ck("two_primary_axes", cfg["trait_axes"] == [0, 1])
    ck("four_scenarios_declared", len(cfg["scenarios"]) == 4)
    ck("r36c_three_way_gate", cfg["r3_6c_required_comparison"] == ["ARCANA_CURRENT_125KYR", "ARCANA_5X25KYR", "NEMO_2_4_2_QTL_ENSEMBLE"])

    for rel, expected in EXPECTED_PARENT_HASHES.items():
        got = digest(ROOT / rel)
        ck(f"parent_authority_unchanged::{rel}", got == expected, got)

    suite = canonical_r36b_scenarios(q_star=0.045, n_individuals=200)
    ck("canonical_suite_four", len(suite) == 4)
    ck("all_scenarios_qstar", all(np.allclose(x.normalized_additive_variance, 0.045) for x in suite))
    ck("fragmentation_reconnection_present", [p.name for p in suite[2].phases] == ["CONNECTED_BURNIN", "FRAGMENTED", "RECONNECTED"])
    ck("all_exchange_zero_diagonal", all(np.max(np.abs(np.diag(p.exchange_matrix))) < 1e-15 for s in suite for p in s.phases))
    ck("all_exchange_rows_conservative", all(np.all(p.exchange_matrix.sum(axis=1) <= 1.0 + 1e-12) for s in suite for p in s.phases))

    s = suite[3]
    spec = NemoQTLArchitectureSpec(loci_per_trait=64, individual_sample_size=200)
    qtl = build_qtl_realization(s.normalized_trait_means, s.normalized_additive_variance, trait_axes=(0,1), seed=36, spec=spec, individuals_per_patch=s.population_individuals)
    ck("qtl_expected_mean_match", np.max(np.abs(qtl.expected_means-qtl.target_means)) < 1e-10)
    ck("qtl_expected_va_match", np.max(np.abs(qtl.expected_variances-qtl.target_variances)) < 1e-10)
    ck("qtl_frequency_interior", np.all((qtl.allele_frequencies > 0) & (qtl.allele_frequencies < 1)))
    qtl2 = build_qtl_realization(s.normalized_trait_means, s.normalized_additive_variance, trait_axes=(0,1), seed=36, spec=spec, individuals_per_patch=s.population_individuals)
    qtl3 = build_qtl_realization(s.normalized_trait_means, s.normalized_additive_variance, trait_axes=(0,1), seed=37, spec=spec, individuals_per_patch=s.population_individuals)
    ck("qtl_seed_reproducible", qtl.semantic_sha256 == qtl2.semantic_sha256)
    ck("qtl_ensemble_seed_distinct", qtl.semantic_sha256 != qtl3.semantic_sha256)

    exp = scenario_to_experiment(suite[1], seed=123, replicate_id=0)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        write_qtl_realization(qtl, td / "qtl", [f"P{i}" for i in range(4)])
        # Separate 2-deme experiment for dispersal semantics.
        adapter = Nemo242R36BAdapter(Nemo242MappingSpec(population_units_to_individuals=1.0, carrying_capacity_multiplier=1.0, loci_per_trait=64, generations=1000))
        prepared = adapter.prepare(exp, td / "bridge")
        raw = np.loadtxt(td / "bridge" / "arcana_exchange_matrix.tsv", delimiter="\t")
        nemo = np.loadtxt(td / "bridge" / "nemo_forward_dispersal_matrix.tsv", delimiter="\t")
        ck("nemo_forward_rows_sum_one", np.allclose(nemo.sum(axis=1), 1.0, atol=1e-12, rtol=0.0))
        ck("nemo_offdiag_preserves_arcana", np.allclose(nemo - np.diag(np.diag(nemo)), raw))
        ck("nemo_diagonal_is_self_retention", np.allclose(np.diag(nemo), 1.0 - raw.sum(axis=1)))
        ck("no_template_no_engine_execution", prepared.command[0] == "python")
        marker = (td / "bridge" / "NEMO_TEMPLATE_REQUIRED.txt").read_text()
        ck("template_guard_present", "No inferred/guessed NEMO parameter names" in marker)

    required = [
        "QUANTITATIVE_GENETICS_CROSS_ENGINE_REFERENCE_CONTRACT_v0_6D1_R3_6B.md",
        "NEMO_2_4_2_QTL_ENSEMBLE_MAPPING_CONTRACT_v0_6D1_R3_6B.md",
        "NEMO_DISPERSAL_SEMANTICS_AUDIT_v0_6D1_R3_6B.md",
        "README_R3_6B.md", "V0_6D1_R3_6B_STATUS.md", "NEXT_STAGE_HANDOFF_v0_6D1_R3_6B.md",
        "src/arcana_worldsim/scientific_engines/nemo_qtl_ensemble.py",
        "src/arcana_worldsim/scientific_engines/nemo_benchmarks.py",
        "src/arcana_worldsim/scientific_engines/nemo242_r36b.py",
        "scripts/prepare_nemo_qtl_ensemble_v0_6D1_R3_6B.py",
        "tests/test_nemo_qtl_ensemble_v0_6D1_R3_6B.py",
        "run_v0_6D1_R3_6B_checks.ps1", "check_nemo_242_wsl.ps1",
    ]
    for rel in required:
        ck(f"required_file::{rel}", (ROOT / rel).exists())

    passed = sum(int(x["pass"]) for x in checks)
    out = {
        "stage": "v0.6D1-R3.6B",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed": passed, "total": len(checks), "checks": checks,
        "verdict": "PASS_NEMO_2_4_2_GOVERNED_QTL_ENSEMBLE_REFERENCE_IMPLEMENTATION__ENGINE_EXECUTION_PENDING" if passed == len(checks) else "FAIL",
    }
    print(json.dumps(out, indent=2))
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
