from __future__ import annotations
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))
import rebased_natural_control_runtime_v0_6D1_R3_3 as r33


def _metadata():
    rows = json.loads((ROOT / "references/v0_6D1_R3/D1_SPECIES_METADATA.json").read_text())
    return {x["species_id"]: x for x in rows}


def _cfg():
    return r33.R33Config(end_age_ma=209.0)


def test_reconnection_cadence_and_persistence_are_locked_to_vicariance():
    cfg = _cfg()
    assert cfg.reconnection_check_interval_years == cfg.deme_fission_check_interval_years
    assert cfg.reconnection_persistence_min_years == cfg.vicariance_persistence_min_years


def test_reconnection_requires_same_current_species_and_resets_on_contact_loss():
    cfg = _cfg()
    ids = ["A", "B"]
    contact = np.array([[0.0, 0.8], [0.8, 0.0]])
    ri = np.zeros((2, 2)); clock = np.zeros((2, 2))
    st, mature = r33.update_reconnection_persistence_r33(ids, ["S", "S"], contact, ri, clock, 0.0, {}, cfg)
    assert len(st) == 1 and not mature
    # Different current species: no de-speciation/coalescence candidate.
    st2, mature2 = r33.update_reconnection_persistence_r33(ids, ["S", "S_D01"], contact, ri, clock, 500_000.0, st, cfg)
    assert st2 == {} and mature2 == {}
    # Same species but contact below the inverse D3.0C exchange gate resets state.
    low = np.array([[0.0, 0.1], [0.1, 0.0]])
    st3, mature3 = r33.update_reconnection_persistence_r33(ids, ["S", "S"], low, ri, clock, 500_000.0, st, cfg)
    assert st3 == {} and mature3 == {}


def test_reconnection_matures_only_after_governed_two_myr():
    cfg = _cfg(); ids=["A","B"]; species=["S","S"]
    contact=np.array([[0.,.8],[.8,0.]]); ri=np.zeros((2,2)); clock=np.zeros((2,2)); st={}
    for t in [0., 500_000., 1_000_000., 1_500_000.]:
        st, mature = r33.update_reconnection_persistence_r33(ids,species,contact,ri,clock,t,st,cfg)
        assert mature == {}
    st, mature = r33.update_reconnection_persistence_r33(ids,species,contact,ri,clock,2_000_000.,st,cfg)
    assert list(mature) == [("A","B")]


def test_scipy_graph_coalescence_is_transitive_but_species_bounded():
    ids=["A","B","C","D"]
    species=["S","S","S","X"]
    mature={("A","B"):{},("B","C"):{},("C","D"): {}}
    groups=r33._mature_reconnection_groups(ids,species,mature)
    assert groups == [[0,1,2]]


def test_moment_pooling_conserves_population_first_and_second_moments():
    cfg=_cfg(); metadata=_metadata(); root="HSG_001"
    ids=["HSG_001_P001","HSG_001_P001_F01"]
    roots=[root,root]; cur=[root,root]; guild=np.array([1,1],np.uint8)
    pop=np.zeros((2,2,2)); pop[0,0,0]=2.; pop[1,0,1]=1.
    trait=np.array([[1.,.2,0.],[1.1,.25,.01]])
    m=metadata[root]; sc=np.array([m["thermal_niche_sigma_c"],m["aridity_niche_sigma"]/1.55,cfg.body_mass_scale])
    va=np.vstack([.02*sc**2,.02*sc**2]); gen=np.array([5.,5.])
    key=r33.r21._pair_key(*ids)
    res=r33.apply_mature_coalescences_r33(
        component_ids=ids,root_species=roots,current_species=cur,guild=guild,pop=pop,trait=trait,va=va,gen=gen,
        ri_state={key:0.0},clock_state={key:0.0},mature={key:{}},reconnection_state={key:{}},
        founder_state={},vicariance_state={},metadata=metadata,elapsed_year=3e6,age_ma=207.,cfg=cfg)
    assert res[0] == ["HSG_001_P001"]
    assert np.isclose(res[4].sum(),3.0,rtol=0,atol=1e-14)
    ev=res[-1][0]
    assert abs(ev["population_conservation_error"]) <= 1e-14
    assert ev["first_moment_conservation_max_abs"] <= 1e-12
    assert ev["second_moment_conservation_max_abs"] <= 1e-12
    assert ev["semantic_status"].endswith("NOT_DESPECIATION")


def test_merge_is_blocked_if_exact_pooled_variance_would_break_hard_ceiling():
    cfg=_cfg(); metadata=_metadata(); root="HSG_001"
    ids=["A","B"]; roots=[root,root]; cur=[root,root]; guild=np.array([1,1],np.uint8)
    pop=np.zeros((2,1,2)); pop[0,0,0]=1.; pop[1,0,1]=1.
    m=metadata[root]; sc=np.array([m["thermal_niche_sigma_c"],m["aridity_niche_sigma"]/1.55,cfg.body_mass_scale])
    # Means separated enough that exact pooling would exceed q=0.05 on thermal axis.
    trait=np.array([[0.,0.,0.],[1.0*sc[0],0.,0.]])
    va=np.vstack([.01*sc**2,.01*sc**2]); gen=np.array([5.,5.]); key=("A","B")
    res=r33.apply_mature_coalescences_r33(component_ids=ids,root_species=roots,current_species=cur,guild=guild,
        pop=pop,trait=trait,va=va,gen=gen,ri_state={key:0.},clock_state={key:0.},mature={key:{}},
        reconnection_state={key:{}},founder_state={},vicariance_state={},metadata=metadata,elapsed_year=3e6,age_ma=207.,cfg=cfg)
    assert len(res[0]) == 2
    assert res[-1] == []


def test_materialized_210_206_validation_has_bidirectional_deme_lifecycle_and_no_false_speciation():
    p=ROOT/"outputs/v0_6D1_R3_3/validation_210_206/210_to_206p0Ma_summary.json"
    d=json.loads(p.read_text())
    assert d["species_count"] == 120
    assert d["component_count"] == 145
    assert d["event_counts"].get("deme_fission") == 15
    assert d["event_counts"].get("deme_coalescence") == 3
    assert d["event_counts"].get("speciation",0) == 0
    assert 133 + d["event_counts"]["deme_fission"] - d["event_counts"]["deme_coalescence"] == d["component_count"]


def test_materialized_210_205_validation_reduces_net_component_growth_without_suppressing_vicariance():
    p=ROOT/"outputs/v0_6D1_R3_3/validation_210_205_final/210_to_205p0Ma_summary.json"
    d=json.loads(p.read_text())
    assert d["species_count"] == 120
    assert d["event_counts"].get("deme_fission") == 18
    assert d["event_counts"].get("deme_coalescence") == 4
    assert d["component_count"] == 147
    assert 133 + 18 - 4 == 147
