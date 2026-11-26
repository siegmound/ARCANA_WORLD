from experiments.r6_thermo_provider_pilot_v1 import run_c05_source_identity_design as r


def test_source_coordinate_is_not_nearest_neighbour():
    row={"layer":"crust","conditional_delta_P_kbar":5.77416,"source_temperature_K":892.5014857175009}
    links={r.coord(row):{"state_keys_by_case":{"C01_MORB_BASE":"a"}}}
    assert r.linked_keys(row,links)==["a"]
    assert r.linked_keys({**row,"source_temperature_K":892.501485717501},links)==[]
    assert r.linked_keys({**row,"layer":"mantle_lithosphere"},links)==[]


def test_source_link_does_not_rewrite_native_exact_keys():
    rows=[{"layer":"crust","fraction_of_layer":i/4,"source_depth_m":i,
           "source_temperature_K":300.+i,"conditional_delta_P_kbar":float(i),
           "cold_MORB_conditional_candidate_keys":[],"comparative_coordinate_matches":{}}
          for i in range(5)]
    states={"a":{"model_identity":"provider","native_chemistry_sha256":"chem"}}
    links={r.coord(rows[2]):{"state_keys_by_case":{"example":"a"}}}
    p=r.classify_profile(rows,states,links)
    assert p["depths"][2]["native_exact_keys"]==[]
    assert p["depths"][2]["source_design_link_keys"]==["a"]
    assert p["additional_source_link_depths"]==1
    assert p["same_recipe_full_profile_count"]==0
    assert p["actual_material"] is None


def test_original_design_roundoff():
    import math
    for K,C in ((892.5014857175009,619.3514857175009),(1414.525818001164,1141.375818001164)):
        assert math.nextafter(C,math.inf)==K-273.15
