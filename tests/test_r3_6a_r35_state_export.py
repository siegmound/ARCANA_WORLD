from __future__ import annotations

from pathlib import Path
import numpy as np

from arcana_worldsim.scientific_engines import NEMO_242, experiment_from_r3_state_npz


def test_r35_npz_export_selects_demes_without_mutating_source(tmp_path: Path):
    state = tmp_path / "state.npz"
    np.savez_compressed(
        state,
        population=np.arange(3*2*2, dtype=float).reshape(3,2,2),
        trait=np.arange(9, dtype=float).reshape(3,3),
        va=np.full((3,3), 0.02), generation_time=np.array([5.,6.,7.]),
        ri=np.eye(3), clock=np.ones((3,3)), contact=np.full((3,3),0.2), trait_distance=np.full((3,3),0.3),
        component_guild=np.array([1,2,3], dtype=np.uint8),
        component_ids=np.array(["D0","D1","D2"]), component_root_species=np.array(["R0","R1","R2"]),
        component_species=np.array(["S0","S1","S2"]),
    )
    exp = experiment_from_r3_state_npz(
        state, engine=NEMO_242, experiment_id="subset", arcana_stage="v0.6D1-R3.5",
        age_ma=150.0, random_seed=9, component_indices=[2,0],
        extra_arrays={"exchange_matrix": np.array([[0.,0.1],[0.1,0.]])},
    )
    assert exp.arrays["component_ids"].tolist() == ["D2","D0"]
    assert exp.arrays["ri"].shape == (2,2)
    assert exp.arrays["population_total"].shape == (2,)
    assert exp.metadata["full_source_component_count"] == 3
    assert len(exp.source_state_sha256) == 64
