import inspect
from pathlib import Path
import numpy as np
import arcana_worldsim.scientific_engines.r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run as m


def test_coords_digest_is_order_sensitive_and_exact():
    a=[[1.0,2.0],[3.0,4.0]]
    b=[[1.0,2.0],[3.0,4.0]]
    c=[[3.0,4.0],[1.0,2.0]]
    assert m._coords_digest(a)==m._coords_digest(b)
    assert m._coords_digest(a)!=m._coords_digest(c)


def test_payload_range_audit_rejects_out_of_range_without_scaling(tmp_path):
    p=tmp_path/"x.npy"
    np.save(p,np.array([[0.0,1.2]]),allow_pickle=False)
    man={"records":[{"payload_file":"x.npy","payload_sha256":m.sha256(p)}]}
    r=m._payload_range_audit(tmp_path,man)
    assert r["all_finite_and_native_geonomics_range_0_1"] is False
    assert r["automatic_rescaling_performed"] is False


def test_j21_writer_adds_support_plus_payload_names(tmp_path):
    base={
      "landscape":{"main":{"dim":(1,1),"res":(1,1),"ulc":(0,0),"prj":None},"layers":{}},
      "comm":{"species":{"spp_0":{"init":{"N":1,"K_layer":"x","K_factor":1},"movement":{"move":False}}}},
      "model":{"name":"x","T":0,"burn_T":0,"seed":{"num":1},"its":{"n_its":1,"rand_landscape":False,"rand_comm":False,"rand_genarch":False,"repeat_burn":False}}
    }
    recs=[
      {"layer_family":"environment","payload_file":"a.npy","payload_sha256":"h1","name":"A"},
      {"layer_family":"producer_support","payload_file":"b.npy","payload_sha256":"h2","name":"B","taxon_id":"T"},
    ]
    p=tmp_path/"p.py"
    mapping=m._write_j21_bound_params(p,base,recs,rows=90,cols=180,seed=7,replicate_index=0)
    s=p.read_text()
    assert "R437_CONSTRUCTION_SUPPORT" in s
    assert "R437_ENV_000" in s
    assert "R437_PRD_001" in s
    assert len(mapping)==2


def test_no_arcana_private_remove_or_add_calls():
    s=inspect.getsource(m)
    assert "._remove_individuals(" not in s
    assert "._add_individuals(" not in s


def test_public_model_add_individuals_is_used():
    s=inspect.getsource(m._mechanical_injection_dry_run_one_model)
    assert "mod.add_individuals(" in s
    assert "spp.burned = True" in s
    assert "spp.burned = burned_before" in s


def test_no_run_walk_default_model_calls():
    s=inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s


def test_next_action_is_exact_init_adapter_gate():
    assert m.NEXT=="BUILD_R438_GEONOMICS_EXACT_INITIALIZATION_ADAPTER_AND_CONSTRUCTION_PROBE_ELIMINATION_PREFLIGHT"
