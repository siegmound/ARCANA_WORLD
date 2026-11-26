from experiments.r6_thermo_provider_pilot_v1 import run_c04_integrated_research_library as r


def test_key_model_and_native_chemistry_are_distinct():
    assert r.identity("a","x",1.,2.)!=r.identity("b","x",1.,2.)
    assert r.identity("a","x",1.,2.)!=r.identity("a","y",1.,2.)


def test_exact_lookup_no_interpolation():
    k=r.identity("a","x",1.,2.)
    lib={"states":{k:{"value":1}}}
    assert r.lookup(lib,"a","x",1.,2.)["state"]=={"value":1}
    assert r.lookup(lib,"a","x",1.,2.00001)["state"] is None
    assert r.lookup(lib,"a","x",1.,2.)["assignment_authorized"] is False


def test_digest_preserves_native_chemistry_distinction():
    assert r.digest({"H2O":"0.2","O2":"0.1"})!=r.digest({"H2O":"1","O2":"0.1"})


def test_configuration_does_not_hash_recipe_specific_input():
    p={"solution_models":["Act(M)"],"excluded_phases":["foGL"],
       "files_sha256":{"c03d.dat":"one","hp02ver.dat":"same"}}
    first=r.native_configuration(p)
    p["files_sha256"]["c03d.dat"]="two"
    assert first==r.native_configuration(p)


def test_no_mutable_lookup_alias():
    k=r.identity("a","x",1.,2.)
    lib={"states":{k:{"value":1}}}
    r.lookup(lib,"a","x",1.,2.)["state"]["value"]=2
    assert lib["states"][k]["value"]==1
