from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import numpy as np
import pytest

from arcana_worldsim.scientific_engines import (
    ENGINE_REGISTRY, NEMO_242, GEONOMICS,
    ScientificExperiment, Nemo242Adapter, Nemo242MappingSpec,
    calibration_candidate, deny_direct_canonical_write, CanonicalWriteDenied,
)
from arcana_worldsim.scientific_engines.serialization import save_experiment, load_experiment


def _exp(extra=None):
    arrays = {
        "component_ids": np.array(["D0", "D1"]),
        "component_root_species": np.array(["S", "S"]),
        "component_species": np.array(["S", "S"]),
        "component_guild": np.array([1, 1], dtype=np.uint8),
        "population_total": np.array([10.0, 8.0]),
        "trait_mean": np.array([[0.0, 0.2, 1.0], [0.4, 0.3, 1.1]]),
        "additive_variance": np.array([[0.08, 0.02, 0.01], [0.09, 0.03, 0.01]]),
        "generation_time_years": np.array([5.0, 5.0]),
        "exchange_matrix": np.array([[0.0, 0.1], [0.1, 0.0]]),
    }
    arrays.update(extra or {})
    return ScientificExperiment(
        experiment_id="R36A-TEST", arcana_stage="v0.6D1-R3.5", age_ma=191.0,
        engine=NEMO_242, source_state_sha256="a" * 64, random_seed=1234,
        metadata={"purpose": "test"}, arrays=arrays,
        assumptions=("controlled microbenchmark",), requested_outputs=("VA", "trait_mean"),
    )


def test_external_engines_are_never_direct_canonical_writers():
    assert set(ENGINE_REGISTRY) == {"NEMO", "Madingley", "Geonomics", "CDMetaPOP", "RangeShifter"}
    assert all(not x.canonical_write_allowed for x in ENGINE_REGISTRY.values())


def test_scientific_experiment_copies_and_freezes_arrays():
    raw = np.array([1.0, 2.0])
    exp = ScientificExperiment(
        experiment_id="freeze", arcana_stage="R3.5", age_ma=150.0, engine=GEONOMICS,
        source_state_sha256="b" * 64, random_seed=1, arrays={"x": raw},
    )
    raw[0] = 99.0
    assert exp.arrays["x"][0] == 1.0
    assert exp.arrays["x"].flags.writeable is False
    with pytest.raises(ValueError):
        exp.arrays["x"][0] = 2.0


def test_experiment_hash_is_deterministic_and_roundtrips(tmp_path: Path):
    exp = _exp()
    h = exp.semantic_sha256
    save_experiment(exp, tmp_path)
    loaded = load_experiment(tmp_path)
    assert loaded.semantic_sha256 == h
    assert np.array_equal(loaded.arrays["trait_mean"], exp.arrays["trait_mean"])
    assert loaded.arrays["trait_mean"].flags.writeable is False


def test_nemo_242_preparation_writes_neutral_bridge_without_guessing_ini(tmp_path: Path):
    exp = _exp()
    adapter = Nemo242Adapter(Nemo242MappingSpec(
        population_units_to_individuals=10.0, carrying_capacity_multiplier=1.5,
        loci_per_trait=32, generations=100,
    ))
    prepared = adapter.prepare(exp, tmp_path)
    assert (tmp_path / "arcana_patches.tsv").exists()
    assert (tmp_path / "arcana_quantitative_traits.tsv").exists()
    assert (tmp_path / "arcana_exchange_matrix.tsv").exists()
    assert (tmp_path / "arcana_nemo_bridge.json").exists()
    assert (tmp_path / "NEMO_TEMPLATE_REQUIRED.txt").exists()
    assert prepared.command[0] == "python"
    ev = adapter.run(exp, tmp_path)
    assert ev.status == "PREPARED_REFERENCE_INPUTS"
    assert ev.metrics["execution_attempted"] is False
    assert "does not uniquely determine" in ev.unsupported_mappings[0]


def test_nemo_requires_explicit_exchange_matrix(tmp_path: Path):
    exp = _exp()
    arrays = dict(exp.arrays)
    arrays.pop("exchange_matrix")
    bad = ScientificExperiment(
        experiment_id=exp.experiment_id, arcana_stage=exp.arcana_stage, age_ma=exp.age_ma,
        engine=exp.engine, source_state_sha256=exp.source_state_sha256, random_seed=exp.random_seed,
        arrays=arrays,
    )
    adapter = Nemo242Adapter(Nemo242MappingSpec(population_units_to_individuals=10.0, carrying_capacity_multiplier=1.2))
    with pytest.raises(ValueError, match="exchange_matrix"):
        adapter.prepare(bad, tmp_path)


def test_nemo_rejects_nonconservative_exchange_rows(tmp_path: Path):
    exp = _exp(extra={"exchange_matrix": np.array([[0.0, 1.1], [0.0, 0.0]])})
    adapter = Nemo242Adapter(Nemo242MappingSpec(population_units_to_individuals=10.0, carrying_capacity_multiplier=1.2))
    with pytest.raises(ValueError, match="row sums"):
        adapter.prepare(exp, tmp_path)


def test_evidence_requires_explicit_review_before_calibration():
    exp = _exp()
    adapter = Nemo242Adapter(Nemo242MappingSpec(population_units_to_individuals=10.0, carrying_capacity_multiplier=1.2))
    # Parse a prepared run in a temp-like manual way is covered elsewhere; here
    # the governance invariant itself is the target.
    with pytest.raises(CanonicalWriteDenied):
        deny_direct_canonical_write({"va": 0.1})


def test_calibration_candidate_never_auto_promotes(tmp_path: Path):
    exp = _exp()
    adapter = Nemo242Adapter(Nemo242MappingSpec(population_units_to_individuals=10.0, carrying_capacity_multiplier=1.2))
    ev = adapter.run(exp, tmp_path)
    cand = calibration_candidate("C1", [ev], {"candidate_action": "cadence_review"}, "independent evidence")
    assert cand.status == "REVIEW_REQUIRED"
    assert cand.evidence_sha256 == (ev.semantic_sha256,)
