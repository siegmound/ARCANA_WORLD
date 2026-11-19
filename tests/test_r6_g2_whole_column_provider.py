"""Numerical full-column G2 candidate engine, synthetic tests only."""
import json
import hashlib
import numpy as np
import pytest

from experiments.plate58_deforming_explore_v1.full_column import (
    evaluate_full_column, G2InputError, brittle_shear_pa,
)
from experiments.plate58_deforming_explore_v1.g2_candidate_runner import (
    evaluate_candidate,
)


def pre():
    return {"crust_thickness_m":100.,"mantle_lithosphere_thickness_m":100.,
     "crust_density_kg_m3":1000.,"mantle_density_kg_m3":1000.,
     "layer1_z0_m":0.,"layer1_z1_m":100.,"layer2_z0_m":100.,"layer2_z1_m":200.,
     "layer1_c0_k":800.,"layer1_c1_k_m":0.,"layer1_c2_k_m2":0.,"layer1_c3_k_m3":0.,
     "layer2_c0_k":800.,"layer2_c1_k_m":0.,"layer2_c2_k_m2":0.,"layer2_c3_k_m3":0.}


def law():
    return {"source_reference":"TEST_SYNTHETIC_CONSTANT_STRESS_NOT_A_ROCK_LAW",
    "A_pa_minus_n_s_inv":1e-30,"n":1.,"E_j_mol":0.,"V_m3_mol":0.,
    "fugacity_exponent":0.,"water_fugacity_pa":None,"reference_fugacity_pa":None,
    "invariant_to_friction_shear_factor":1.,
    "shear_conversion_reference":"TEST_IDENTITY_SYNTHETIC_ONLY",
    "stress_convention":"ASPECT_2ETA_EPS_INVARIANT_SCALE",
    "valid_temperature_k":[200.,1000.],"valid_pressure_pa":[0.,1e8],
    "valid_strain_rate_s_inv":[1e-16,1e-12]}


def spec():
    by={"mode":"BYERLEE_1978_REFERENCE",
        "source_reference":"BYERLEE_1978_REFERENCE__NOT_R6_MATERIAL",
        "normal_stress_over_lithostatic":1.,"biot_coefficient":1.,
        "pore_pressure_over_lithostatic":0.2,
        "valid_effective_normal_pressure_pa":[0.,1.7e9]}
    return {"authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
            "source_identifier":"TEST_SYNTHETIC_VARIANT_01",
            "gravity_m_s2":10.,"strain_rate_s_inv":1e-14,
            "layers":{"crust":{"ductile":law(),"brittle":by},
                      "mantle":{"ductile":law(),
                      "brittle":{"mode":"DUCTILE_ONLY_EXPLICIT_HYPOTHESIS",
                      "rationale":"TEST FIXTURE only, never geology."}}},
            "integration":{"subintervals_per_layer":64,
                          "max_relative_discretization_error":0.01}}


def test_analytical_brittle_plus_ductile():
    out=evaluate_full_column(pre(),spec())
    expected=0.85*0.8*1000*10*100**2/2 + 1e16*100
    assert np.isclose(out["full_lithosphere_integrated_effective_shear_strength_pa_m"],expected)
    assert out["mechanical_solve_authorized"] is False


def test_missing_pressure_fails():
    s=spec()
    del s["layers"]["crust"]["brittle"]["biot_coefficient"]
    with pytest.raises(G2InputError):
        evaluate_full_column(pre(),s)


def test_unvalidated_lab_domain_rejects():
    s=spec()
    s["layers"]["crust"]["ductile"]["valid_temperature_k"]=[973.,1473.]
    with pytest.raises(G2InputError,match="OUTSIDE_CALIBRATED_DOMAIN"):
        evaluate_full_column(pre(),s)


def test_authorial_promotion_rejected():
    s=spec()
    s["authority"]="RATIFIED"
    with pytest.raises(G2InputError,match="PROMOTION"):
        evaluate_full_column(pre(),s)


def test_water_exponent_requires_fugacity():
    s=spec()
    s["layers"]["crust"]["ductile"]["fugacity_exponent"]=1.
    with pytest.raises(G2InputError):
        evaluate_full_column(pre(),s)


def test_high_pressure_continuous_byerlee():
    s=spec()["layers"]["crust"]["brittle"]
    p=np.asarray([0.,2e8/0.8,4e8/0.8])
    result=brittle_shear_pa(p,s)
    assert np.allclose(result,[0.,1.7e8,2.9e8])


def test_runtime_candidate_requires_25_source_bound_columns(tmp_path):
    coupling=tmp_path/"coupling"
    coupling.mkdir()
    cols=[{"parent_id":i,"source_PRE":pre()} for i in range(1,26)]
    pre_bind={"source_columns":cols,"effective_constitutive_closure":None}
    geo={"geometry":{"source_halo_parent_node_ids":list(range(1,26))}}
    tr={"actual_interface_tangent":None,"actual_effective_load":None,
        "mechanical_solve_authorized":False}
    for k,obj in (("G2_PRE_BINDING.json",pre_bind),("GEOMETRY.json",geo),
                  ("G3_A_TRANSFER_CONTRACT.json",tr)):
        (coupling/k).write_text(json.dumps(obj))
    manifest={"status":"PASS_G2_G3_A_SOURCE_INTERFACE_BOUND__PHYSICAL_CLOSURE_OPEN",
        "files":{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in coupling.iterdir()},
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True}
    (coupling/"MANIFEST.json").write_text(json.dumps(manifest))
    cand=tmp_path/"candidate.json"
    cand.write_text(json.dumps(spec()))
    output=tmp_path/"out"
    r=evaluate_candidate(coupling,cand,output)
    assert r["column_count"]==25
    assert r["solver_runs"]==0
    assert (output/"G2_CANDIDATE.json").exists()
