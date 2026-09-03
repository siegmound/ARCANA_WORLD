from pathlib import Path
import hashlib, json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
import sys
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import rebased_deep_time_barrier_provider_v0_6D1_R3 as bp
import rebased_natural_control_runtime_v0_6D1_R3 as r3

A1P = ROOT / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"
D3P = ROOT / "src/d3_paleogeographic_history_v0_6_3D3_2C.py"
OUT = ROOT / "outputs/v0_6D1_R3"


def _a1():
    return np.load(A1P, allow_pickle=False)


def test_d3_2c_source_is_exact_surviving_authority():
    h = hashlib.sha256(D3P.read_bytes()).hexdigest()
    assert h == "5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730"


def test_full_a1_age_sequence_bound():
    a = _a1()
    assert a["age_ma"].astype(float).tolist() == [210.0,180.0,150.0,140.0,130.0,120.0,90.0,66.0,60.0,30.0,0.0]


def test_multibracket_catalog_inventory():
    c = bp.build_all_transition_schedules(_a1())
    assert c["summary"]["bracket_count"] == 10
    assert c["summary"]["event_cluster_count"] == 801
    assert c["summary"]["transition_cells_counted_across_brackets"] == 12366
    assert all(e["semantic_status"] == "DERIVED_ENDPOINT_CONSTRAINED_EVENT_CLUSTER_NOT_INDEPENDENT_GEOLOGICAL_OBSERVATION" for e in c["events"])


def test_all_land_endpoints_are_exact():
    a = _a1()
    for i, age in enumerate(a["age_ma"].astype(float)):
        e = bp.environment_at(float(age), a)
        np.testing.assert_array_equal(e["land_support"], a["land_mask"][i].astype(float))


def test_reference_total_interpolation_is_not_reinvented():
    a = _a1(); age = 195.0
    e = bp.environment_at(age, a)
    i0 = int(np.where(np.isclose(a["age_ma"],210.0))[0][0]); i1 = int(np.where(np.isclose(a["age_ma"],180.0))[0][0])
    target = 0.5*a["population"][i0].astype(float).sum(axis=(1,2)) + 0.5*a["population"][i1].astype(float).sum(axis=(1,2))
    np.testing.assert_allclose(e["reference_population"].sum(axis=(1,2)), target, rtol=0, atol=1e-10)


def test_d3_2b_permeability_anchor_at_threshold():
    cfg = bp.BarrierHistoryConfig(connectivity_land_support_threshold=0.25, connectivity_softness=0.10)
    x = np.asarray([[0.25]], dtype=float)
    p = bp.connectivity_permeability(x, cfg)
    assert abs(float(p[0,0]) - 0.5) < 1e-15


def test_initial_fragmentation_is_grandfathered_not_new_vicariance():
    cfg = r3.R3Config(end_age_ma=209.0)
    pop = np.zeros((1,5,3),float); pop[0,0,1]=1; pop[0,4,1]=1
    conn = np.zeros_like(pop); conn[0,0,1]=1; conn[0,4,1]=1
    state,mature = r3.update_vicariance_persistence_r3(["D"],pop,conn,["S"],500000.0,{},cfg)
    assert not mature
    assert state["D"]["baseline_fragmented"] is True
    assert state["D"]["armed_after_connected_state"] is False
    for t in [1_000_000.0,1_500_000.0,2_000_000.0,2_500_000.0,3_000_000.0]:
        state,mature = r3.update_vicariance_persistence_r3(["D"],pop,conn,["S"],t,state,cfg)
    assert not mature


def test_connected_then_new_split_matures_after_two_myr():
    cfg = r3.R3Config(end_age_ma=209.0)
    pop = np.zeros((1,5,3),float); pop[0,:,1]=1
    conn_connected = np.ones_like(pop)
    conn_split = np.ones_like(pop); conn_split[0,2,:] = 0
    state,_ = r3.update_vicariance_persistence_r3(["D"],pop,conn_connected,["S"],500000.0,{},cfg)
    # Create a real core split: population bridge remains but connectivity falls below core threshold.
    for t in [1_000_000.0,1_500_000.0,2_000_000.0,2_500_000.0,3_000_000.0]:
        state,mature = r3.update_vicariance_persistence_r3(["D"],pop,conn_split,["S"],t,state,cfg)
    assert "D" in mature
    assert mature["D"]["continuous_persistence_years"] >= 2_000_000.0


def test_rebased_fission_parent_identity_robustness():
    b = json.loads((OUT/"R3B_BASELINE_PREACTUATION_210_206.json").read_text())
    w = json.loads((OUT/"R3B_WIDE_PREACTUATION_210_206.json").read_text())
    t = json.loads((OUT/"R3B_WIDTH2_PREACTUATION_210_206.json").read_text())
    assert set(b["baseline_candidates"]) == set(w["wide_candidates"]) == set(t["width2_candidates"])
    assert len(b["baseline_candidates"]) == 13


def test_materialized_width_half_preserves_parent_identity():
    s = json.loads((OUT/"R3B_BARRIER_FISSION_SENSITIVITY_SUMMARY.json").read_text())
    assert s["materialized_210_205"]["baseline_fission_count"] == 18
    assert s["materialized_210_205"]["width_0p5_fission_count"] == 18
    assert s["materialized_210_205"]["parent_identity_exact"] is True
    assert s["preactuation_210_206"]["all_parent_candidate_sets_exact"] is True
