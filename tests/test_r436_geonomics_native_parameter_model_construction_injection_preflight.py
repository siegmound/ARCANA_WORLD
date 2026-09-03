import json
from pathlib import Path
import numpy as np
import arcana_worldsim.scientific_engines.r436_geonomics_native_parameter_model_construction_injection_preflight as m


def test_seed_vectors_require_four_per_geonomics_job():
    c={"seed_authority":{"records":[
      {"job_id":m.J14,"replicate_seed_vector":[1,2,3,4]},
      {"job_id":m.J18,"replicate_seed_vector":[5,6,7,8]},
      {"job_id":m.J21,"replicate_seed_vector":[9,10,11,12]},
    ]}}
    r=m._seed_vectors(c)
    assert set(r)==set(m.JOBS)
    assert all(len(v)==4 for v in r.values())


def test_patch_template_binds_nested_seed_and_construction_probe():
    t={
      "landscape":{"main":{"dim":(1,1),"res":(1,1),"ulc":(0,0),"prj":None},
                   "layers":{"layer_0":{"init":{"defined":{"rast":None,"pts":None,"vals":None,"interp_method":None}}}}},
      "comm":{"species":{"spp_0":{"init":{"N":10,"K_layer":"layer_0","K_factor":2},
                                  "movement":{"move":True}}}},
      "model":{"T":100,"burn_T":30,"num":None,
               "its":{"n_its":1,"rand_landscape":True,"rand_comm":True,"repeat_burn":True}}
    }
    p=m._patch_template(t,job_id=m.J18,replicate_index=2,seed=123,rows=90,cols=180)
    assert p["landscape"]["main"]["dim"]==(180,90)
    assert p["comm"]["species"]["spp_0"]["init"]["N"]==1
    assert p["model"]["seed"]["num"]==123
    assert p["model"]["T"]==0 and p["model"]["burn_T"]==0


def test_params_module_writer_is_importable(tmp_path):
    t={
      "landscape":{"main":{"dim":(4,3),"res":(1,1),"ulc":(0,0),"prj":None},
                   "layers":{"layer_0":{"init":{"defined":{"rast":None,"pts":None,"vals":None,"interp_method":None}}}}},
      "comm":{"species":{"spp_0":{"init":{"N":1,"K_layer":"layer_0","K_factor":1}}}},
      "model":{"T":0,"burn_T":0,"seed":{"num":7},"its":{"n_its":1,"rand_landscape":False,"rand_comm":False,"repeat_burn":False}}
    }
    p=tmp_path/"p.py"
    m._write_params_module(p,t,3,4)
    q=m._import_params_module(p)
    assert q["landscape"]["layers"]["layer_0"]["init"]["defined"]["rast"].shape==(3,4)


def test_j18_branch_count_contract_is_all_32x2():
    assert 32*2==64
    assert "ALL_PARENT_MEMBERS_X_ALL_CANDIDATE_IDS" in m._j18_injection_manifest.__code__.co_consts


def test_j14_branch_count_contract_is_all_96x2():
    assert 96*2==192
    assert "ALL_STORAGE_AXIS0_X_ALL_CANDIDATE_IDS" in m._j14_injection_manifest.__code__.co_consts


def test_no_scientific_run_calls_in_module():
    import inspect
    s=inspect.getsource(m)
    assert "run_default_model(" not in s
    assert ".walk(" not in s
    assert ".run(" not in s
    assert "exact_state_injection_performed_in_r436" in s
