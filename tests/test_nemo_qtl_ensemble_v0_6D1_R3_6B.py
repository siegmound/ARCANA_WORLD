from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pytest

from arcana_worldsim.scientific_engines import (
    Nemo242R36BAdapter, Nemo242MappingSpec, NemoQTLArchitectureSpec,
    build_qtl_realization, canonical_r36b_scenarios, scenario_to_experiment,
    write_qtl_realization, write_scenario,
)


def test_canonical_suite_has_four_controlled_scenarios_and_fixed_qstar():
    suite = canonical_r36b_scenarios(q_star=0.045, n_individuals=200)
    assert [s.name for s in suite] == [
        "B0_EQUILIBRIUM_NO_FLOW",
        "B1_TWO_DEME_ADMIXTURE",
        "B2_FRAGMENTATION_RECONNECTION",
        "B3_HIGH_ADMIXTURE_STRESS",
    ]
    assert all(np.allclose(s.normalized_additive_variance, 0.045) for s in suite)
    assert suite[2].phases[1].name == "FRAGMENTED"
    assert suite[2].phases[2].name == "RECONNECTED"


def test_qtl_expected_moments_reconstruct_targets_to_numerical_precision():
    s = canonical_r36b_scenarios(n_individuals=300)[3]
    r = build_qtl_realization(
        s.normalized_trait_means, s.normalized_additive_variance,
        trait_axes=(0, 1), seed=99,
        spec=NemoQTLArchitectureSpec(loci_per_trait=64, individual_sample_size=300),
        individuals_per_patch=s.population_individuals,
    )
    assert np.max(np.abs(r.expected_means - r.target_means)) < 1e-10
    assert np.max(np.abs(r.expected_variances - r.target_variances)) < 1e-10
    assert np.all((r.allele_frequencies > 0) & (r.allele_frequencies < 1))
    assert r.effect_sizes.shape == (2, 64)


def test_qtl_realizations_are_seed_reproducible_but_ensemble_distinct():
    s = canonical_r36b_scenarios(n_individuals=200)[1]
    spec = NemoQTLArchitectureSpec(loci_per_trait=32, individual_sample_size=200)
    a = build_qtl_realization(s.normalized_trait_means, s.normalized_additive_variance, trait_axes=(0,1), seed=1, spec=spec, individuals_per_patch=s.population_individuals)
    b = build_qtl_realization(s.normalized_trait_means, s.normalized_additive_variance, trait_axes=(0,1), seed=1, spec=spec, individuals_per_patch=s.population_individuals)
    c = build_qtl_realization(s.normalized_trait_means, s.normalized_additive_variance, trait_axes=(0,1), seed=2, spec=spec, individuals_per_patch=s.population_individuals)
    assert a.semantic_sha256 == b.semantic_sha256
    assert a.semantic_sha256 != c.semantic_sha256
    assert np.array_equal(a.genotype_counts[0], b.genotype_counts[0])
    assert not np.array_equal(a.genotype_counts[0], c.genotype_counts[0])


def test_qtl_writer_never_claims_npz_is_native_nemo_input(tmp_path: Path):
    s = canonical_r36b_scenarios(n_individuals=100)[0]
    r = build_qtl_realization(s.normalized_trait_means, s.normalized_additive_variance, trait_axes=(0,1), seed=3, spec=NemoQTLArchitectureSpec(loci_per_trait=16, individual_sample_size=100), individuals_per_patch=s.population_individuals)
    write_qtl_realization(r, tmp_path, ["P0", "P1"])
    man = json.loads((tmp_path / "qtl_ensemble_manifest.json").read_text())
    assert man["model"]["nemo_import_semantics"].startswith("REQUIRES_VERSION_VALIDATED")
    assert man["authority"]["canonical_write_allowed"] is False
    assert (tmp_path / "qtl_genotype_realization.npz").exists()


def test_arcana_exchange_is_converted_to_row_stochastic_nemo_forward_matrix(tmp_path: Path):
    s = canonical_r36b_scenarios(n_individuals=100)[1]
    exp = scenario_to_experiment(s, seed=7, replicate_id=0)
    adapter = Nemo242R36BAdapter(Nemo242MappingSpec(population_units_to_individuals=1.0, carrying_capacity_multiplier=1.0, loci_per_trait=16, generations=s.generations))
    adapter.prepare(exp, tmp_path)
    raw = np.loadtxt(tmp_path / "arcana_exchange_matrix.tsv", delimiter="\t")
    nemo = np.loadtxt(tmp_path / "nemo_forward_dispersal_matrix.tsv", delimiter="\t")
    assert np.allclose(np.diag(raw), 0.0)
    assert np.allclose(nemo.sum(axis=1), 1.0)
    assert np.allclose(nemo - np.diag(np.diag(nemo)), raw)
    assert np.allclose(np.diag(nemo), 1.0 - raw.sum(axis=1))


def test_nonzero_arcana_exchange_diagonal_is_rejected(tmp_path: Path):
    s = canonical_r36b_scenarios(n_individuals=100)[0]
    exp0 = scenario_to_experiment(s, seed=8, replicate_id=0)
    arrays = dict(exp0.arrays)
    arrays["exchange_matrix"] = np.eye(2) * 0.1
    from arcana_worldsim.scientific_engines import ScientificExperiment, NEMO_242
    exp = ScientificExperiment(
        experiment_id="bad-diag", arcana_stage="v0.6D1-R3.6B", age_ma=191.0,
        engine=NEMO_242, source_state_sha256="c"*64, random_seed=8, arrays=arrays,
    )
    adapter = Nemo242R36BAdapter(Nemo242MappingSpec(population_units_to_individuals=1.0, carrying_capacity_multiplier=1.0))
    with pytest.raises(ValueError, match="zero diagonal"):
        adapter.prepare(exp, tmp_path)


def test_fragmentation_scenario_writes_explicit_phase_authority(tmp_path: Path):
    s = canonical_r36b_scenarios(n_individuals=100)[2]
    write_scenario(s, tmp_path)
    payload = json.loads((tmp_path / "scenario.json").read_text())
    assert len(payload["phases"]) == 3
    assert payload["phases"][1]["name"] == "FRAGMENTED"
    assert payload["phases"][2]["start_generation"] == 650
    for p in payload["phases"]:
        assert (tmp_path / p["exchange_file"]).exists()


def test_synthetic_scenario_hash_is_semantic_not_placeholder():
    s = canonical_r36b_scenarios(n_individuals=100)[0]
    a = scenario_to_experiment(s, seed=1, replicate_id=0)
    b = scenario_to_experiment(s, seed=2, replicate_id=1)
    assert a.source_state_sha256 == b.source_state_sha256
    assert a.source_state_sha256 != "0" * 64
    assert a.semantic_sha256 != b.semantic_sha256
