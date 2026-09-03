from __future__ import annotations

from copy import deepcopy
import numpy as np
import pytest

from arcana_worldsim.scientific_engines.r321_present_lineage_registry import (
    R321Config,
    R321GateError,
    build_registry_from_loaded,
    functional_phenotype_fork_interface,
)


def fixture_state():
    metadata = {
        "age_ma": 0.0,
        "component_ids": ["D0", "D1", "D2", "D3"],
        "root_species": ["A", "A", "A", "C"],
        "current_species": ["A", "B", "B", "C"],
        "registry": {
            "A": {"species_id": "A", "parent_species_id": None, "root_species_id": "A", "guild_id": 1},
            "B": {"species_id": "B", "parent_species_id": "A", "root_species_id": "A", "guild_id": 1, "birth_age_ma": 1.0},
            "C": {"species_id": "C", "parent_species_id": None, "root_species_id": "C", "guild_id": 4},
            "X": {"species_id": "X", "parent_species_id": "A", "root_species_id": "A", "guild_id": 1},
        },
        "events": {
            "speciation": [
                {"event_type": "speciation", "parent_species_id": "A", "daughter_species_id": "B", "age_ma": 1.0}
            ],
            "ordinary_background_extinction": [
                {"event_type": "ordinary_background_extinction", "species_id": "X", "age_ma": 0.5}
            ],
        },
        "Deep_adaptation_enabled": False,
    }
    pop = np.zeros((4, 2, 3), dtype=float)
    pop[0, 0, 0] = 2.0
    pop[1, 0, 1] = 3.0
    pop[2, 1, 1] = 4.0
    pop[3, 1, 2] = 5.0
    arrays = {
        "pop": pop,
        "guild": np.asarray([1, 1, 1, 4], dtype=np.uint8),
        "trait": np.asarray([[1, 2, 3], [2, 3, 4], [2.5, 3.5, 4.5], [8, 9, 10]], dtype=float),
        "va": np.full((4, 3), 0.01, dtype=float),
        "gen": np.asarray([5, 5, 5, 10], dtype=float),
        "current_accessible": np.ones((2, 3), dtype=bool),
        "reduced_va_within": np.full((4, 3), 0.01, dtype=float),
        "reduced_ancestry_covariance": np.zeros((4, 3), dtype=float),
        "reduced_neutral_segregation_potential": np.zeros((4, 4, 3), dtype=float),
        "reduced_adaptive_coordinate": np.zeros((4, 3), dtype=float),
    }
    return metadata, arrays


def test_registry_is_read_only_and_closes_ancestry():
    metadata, arrays = fixture_state()
    before = arrays["pop"].copy()
    out = build_registry_from_loaded(
        metadata,
        arrays,
        source_hashes={"json_sha256": "synthetic", "npz_sha256": "synthetic"},
        cfg=R321Config(require_exact_r319_hashes=False),
        enforce_canonical_counts=False,
    )
    assert np.array_equal(before, arrays["pop"])
    rows = {x["species_id"]: x for x in out["present_lineages"]}
    assert sorted(rows) == ["A", "B", "C"]
    assert rows["B"]["ancestry_chain_root_to_present"] == ["A", "B"]
    assert rows["B"]["component_count"] == 2
    assert rows["B"]["population_total"] == 7.0
    assert rows["B"]["functional_phenotype"]["values"] is None
    assert out["closure"]["no_new_biology_executed"] is True
    assert out["closure"]["no_human_target"] is True
    assert all(
        out["closure"]["reduced_state_presence"][k]
        for k in (
            "va_within_present",
            "ancestry_covariance_present",
            "neutral_segregation_potential_present",
            "adaptive_coordinate_present",
        )
    )
    comp = {x["component_id"]: x for x in out["present_components"]}
    assert comp["D0"]["va_within"] == [0.01, 0.01, 0.01]
    assert comp["D0"]["adaptive_coordinate"] == [0.0, 0.0, 0.0]


def test_missing_parent_fails_closed():
    metadata, arrays = fixture_state()
    metadata = deepcopy(metadata)
    metadata["registry"]["B"]["parent_species_id"] = "MISSING"
    with pytest.raises(R321GateError, match="missing parent"):
        build_registry_from_loaded(metadata, arrays, enforce_canonical_counts=False)


def test_cycle_fails_closed():
    metadata, arrays = fixture_state()
    metadata = deepcopy(metadata)
    metadata["registry"]["A"]["parent_species_id"] = "B"
    with pytest.raises(R321GateError, match="cycle"):
        build_registry_from_loaded(metadata, arrays, enforce_canonical_counts=False)


def test_extinct_present_species_fails_closed():
    metadata, arrays = fixture_state()
    metadata = deepcopy(metadata)
    metadata["events"]["ordinary_background_extinction"].append(
        {"event_type": "ordinary_background_extinction", "species_id": "B", "age_ma": 0.2}
    )
    with pytest.raises(R321GateError, match="marked extinct"):
        build_registry_from_loaded(metadata, arrays, enforce_canonical_counts=False)


def test_deep_true_fails_closed():
    metadata, arrays = fixture_state()
    metadata = deepcopy(metadata)
    metadata["Deep_adaptation_enabled"] = True
    with pytest.raises(R321GateError, match="Deep biological coupling"):
        build_registry_from_loaded(metadata, arrays, enforce_canonical_counts=False)



def test_event_field_is_preserved_as_event_type_and_extinction_gate():
    metadata, arrays = fixture_state()
    metadata = deepcopy(metadata)
    metadata["events"] = [
        {"event": "deme_fission", "parent_component_id": "D0", "daughter_component_id": "D4", "age_ma": 2.0},
        {"event": "ordinary_background_extinction", "species_id": "B", "age_ma": 0.2},
    ]
    with pytest.raises(R321GateError, match="marked extinct"):
        build_registry_from_loaded(metadata, arrays, enforce_canonical_counts=False)

    metadata["events"] = [
        {"event": "deme_fission", "parent_component_id": "D0", "daughter_component_id": "D4", "age_ma": 2.0},
    ]
    out = build_registry_from_loaded(metadata, arrays, enforce_canonical_counts=False)
    assert out["historical_events"][0]["event_type"] == "deme_fission"


def test_missing_canonical_reduced_state_fails_closed():
    metadata, arrays = fixture_state()
    arrays = dict(arrays)
    arrays.pop("reduced_adaptive_coordinate")
    with pytest.raises(R321GateError, match="canonical reduced genetic state missing"):
        build_registry_from_loaded(metadata, arrays, enforce_canonical_counts=False)


def test_ancestry_covariance_component_trait_shape_mismatch_fails_closed():
    metadata, arrays = fixture_state()
    arrays = dict(arrays)
    arrays["reduced_ancestry_covariance"] = np.zeros((4, 4, 3), dtype=float)
    with pytest.raises(R321GateError, match="component-by-trait shape"):
        build_registry_from_loaded(metadata, arrays, enforce_canonical_counts=False)


def test_segregation_pairwise_shape_mismatch_fails_closed():
    metadata, arrays = fixture_state()
    arrays = dict(arrays)
    arrays["reduced_neutral_segregation_potential"] = np.zeros((4, 3), dtype=float)
    with pytest.raises(R321GateError, match="pairwise component-by-component-by-trait shape"):
        build_registry_from_loaded(metadata, arrays, enforce_canonical_counts=False)

def test_functional_fork_is_schema_only():
    fork = functional_phenotype_fork_interface()
    assert fork["composite_human_readiness_score"] is None
    assert fork["deep_coupling"] == "OFF"
    assert len(fork["domains_reserved_for_r3_22"]) == 10
    assert all(x["value"] is None for x in fork["domains_reserved_for_r3_22"])
    assert all(x["status"] == "UNDEFINED_UNTIL_R3_22" for x in fork["domains_reserved_for_r3_22"])
