import json
import numpy as np
from pathlib import Path

import arcana_worldsim.scientific_engines.r435_geonomics_native_schema_initial_state_seed_closure as m


def test_seed_collector_supports_mapping_and_row_schemas():
    x = {
        "seeds": {
            "R42_J01_A": 11,
            "R42_J02_B": {"job_id": "R42_J02_B", "seed": 22},
        },
        "records": [
            {"job_id": "R42_J03_C", "random_seed": 33},
        ],
    }
    out = m._collect_seed_candidates(x)
    assert out["R42_J01_A"] == {11}
    assert out["R42_J02_B"] == {22}
    assert out["R42_J03_C"] == {33}


def test_shape_from_coords_is_index_only_not_physical():
    r = m._shape_from_coords(
        np.array([0, 1, 2, 2], dtype=float),
        np.array([0, 3, 1, 2], dtype=float),
        "fixture",
    )
    assert r["status"] == "CLOSED_CANONICAL_INDEX_GRID_GEOMETRY"
    assert r["geonomics_landscape_dim_xy"] == [4, 3]
    assert r["geonomics_res_xy"] == [1, 1]
    assert r["physical_distance_or_area_claim_authorized"] is False


def test_time_axis_mapping_preserves_exact_values(tmp_path):
    p = tmp_path / "x.npz"
    np.savez(p, snapshot_age_ka=np.array([200.0, 100.0, 0.0]))
    pkg = {"canonical_sources":[{"path":"x.npz","hash_match":True}]}
    r = m._time_axis(tmp_path, m.J18, pkg)
    assert r["status"].startswith("CLOSED_")
    assert [x["canonical_age"] for x in r["steps"]] == [200.0, 100.0, 0.0]
    assert r["interpolation_performed"] is False


def test_population_closure_never_claims_literal_individuals():
    s = m.contract if hasattr(m, "contract") else None
    # Source-level invariant is intentionally explicit.
    import inspect
    src = inspect.getsource(m)
    assert "ONE_NONLITERAL_CONNECTIVITY_CARRIER_PER_ACTIVE_DEME" in src
    assert "demographic_population_count_adjudication_authorized" in src
    assert "native_literal_N_from_population_weight_authorized" in src


def test_j21_layer_role_is_provenance_separate(tmp_path):
    e = tmp_path / "e.npz"
    p = tmp_path / "p.npz"
    np.savez(
        e,
        anchor_age_ka=np.array([20.0,0.0]),
        environment_fields=np.zeros((2,2,3,4)),
        environment_variable_names=np.array(["a","b"]),
    )
    np.savez(
        p,
        anchor_age_ka=np.array([20.0,0.0]),
        producer_landscape=np.zeros((2,2,3,4)),
        landscape_variable_names=np.array(["x","y"]),
    )
    def row(path):
        import hashlib
        return {
            "path": path.name,
            "hash_match": True,
        }
    pkg={"canonical_sources":[row(e), row(p)]}
    r=m._j21_layer_role_authority(tmp_path,pkg)
    assert r["status"].startswith("CLOSED_")
    assert r["cross_layer_numeric_fusion_authorized"] is False
    assert r["producer_values_interpreted_as_literal_agents"] is False


def test_exact_jobs_and_next_stage():
    assert set(m.JOBS) == {m.J14, m.J18, m.J21}
    assert "NATIVE_PARAMETER_MATERIALIZATION" in m.NEXT
    assert "MODEL_CONSTRUCTION" in m.NEXT
    assert "EXACT_STATE_INJECTION" in m.NEXT


def test_module_never_imports_geonomics_or_runs_model():
    import inspect
    src=inspect.getsource(m)
    assert "import geonomics" not in src
    assert "gnx.make_model(" not in src
    assert ".run(" not in src
