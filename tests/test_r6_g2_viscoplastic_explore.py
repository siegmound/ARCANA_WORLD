"""Coupled Drucker-Prager/creep G2 potential tests: synthetic laws only."""
import numpy as np
import pytest
from experiments.plate58_deforming_explore_v1.g2_viscoplastic_explore import (
    potential_gradient_tangent, layer_material, DRUCKER_PRAGER_PRESSURE_TERMS,
)


def pre():
    return {"crust_thickness_m":30000.,"mantle_lithosphere_thickness_m":50000.,
            "crust_density_kg_m3":2800.,"mantle_density_kg_m3":3250.,
            "layer1_z0_m":0.,"layer1_z1_m":30000.,
            "layer2_z0_m":30000.,"layer2_z1_m":80000.,
            "layer1_c0_k":850.,"layer1_c1_k_m":0.,
            "layer1_c2_k_m2":0.,"layer1_c3_k_m3":0.,
            "layer2_c0_k":1450.,"layer2_c1_k_m":0.,
            "layer2_c2_k_m2":0.,"layer2_c3_k_m3":0.}


def candidate(n1=4.,n2=3.5):
    def material(n):
        return {
          "authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
          "ductile":{
              "source_reference":"SYNTHETIC_DISLOCATION_NOT_ARCANA",
              "stress_convention":"ASPECT_2ETA_EPS_INVARIANT_SCALE",
              "A_pa_minus_n_s_inv":1e-28,"n":n,
              "E_j_mol":200000.,"V_m3_mol":0.,
              "fugacity_exponent":0.,
              "water_fugacity_pa":None,"reference_fugacity_pa":None,
              "valid_temperature_k":[250.,1900.],
              "valid_pressure_pa":[0.,4e9],
              "valid_strain_rate_s_inv":[1e-19,1e-10]},
          "brittle":{
              "source_reference":"SYNTHETIC_DRUCKER_PRAGER_NO_ARCANA",
              "criterion":"DRUCKER_PRAGER_3D_CONTINUUM",
              "drucker_prager_pressure_convention":"ASPECT_RHEOLOGY_DP_3D_6P",
              "cohesion_pa":5e6,"friction_angle_deg":30.,
              "biot_coefficient":1.,
              "pore_pressure_over_lithostatic":0.3}}
    return {"authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
            "source_identifier":"SYNTHETIC_REFERENCE_VP_001",
            "regularization_strain_rate_s_inv":1e-18,
            "gravity_m_s2":9.80665,"gauss_points_per_layer":12,
            "layers":{"crust":material(n1),"mantle":material(n2)}}


def test_two_distinct_exponents_and_positive_tangent():
    out=potential_gradient_tangent(pre(),candidate(),[2e-14,-1e-14,1e-14])
    assert [x["n"] for x in out["layers"]]==pytest.approx([4,3.5])
    assert np.min(np.linalg.eigvalsh(out["tangent_N_s_per_m"]))>0
    assert out["mechanical_solve_authorized"] is False


def test_potential_gradient_and_tangent_consistent_finite_difference():
    x=np.array([2e-14,-1e-14,1e-14])
    state=potential_gradient_tangent(pre(),candidate(),x)
    for j in range(3):
        h=1e-18
        dx=np.eye(3)[j]*h
        a=potential_gradient_tangent(pre(),candidate(),x+dx)
        b=potential_gradient_tangent(pre(),candidate(),x-dx)
        pfd=(a["potential_N_per_m_s"]-b["potential_N_per_m_s"])/(2*h)
        sfd=(a["stress_resultant_N_per_m"]-b["stress_resultant_N_per_m"])/(2*h)
        assert pfd==pytest.approx(
            state["stress_resultant_N_per_m"][j],rel=2e-6)
        assert np.allclose(sfd,state["tangent_N_s_per_m"][:,j],rtol=2e-6)


def test_zero_rate_no_force_and_finite_regularized_tangent():
    state=potential_gradient_tangent(pre(),candidate(),[0.,0.,0.])
    assert state["potential_N_per_m_s"]==0.
    assert np.all(state["stress_resultant_N_per_m"]==0.)
    assert np.min(np.linalg.eigvalsh(state["tangent_N_s_per_m"]))>0


def test_pore_pressure_cannot_be_implicit():
    s=candidate()
    del s["layers"]["crust"]["brittle"]["pore_pressure_over_lithostatic"]
    with pytest.raises(ValueError,match="PORE_PRESSURE_RATIO_MISSING"):
        potential_gradient_tangent(pre(),s,[1e-14,0,0])


def test_laboratory_temperature_window_rejects_cold_source():
    s=candidate()
    s["layers"]["crust"]["ductile"]["valid_temperature_k"]=[1200,1400]
    with pytest.raises(ValueError,match="OUTSIDE_VALIDITY"):
        potential_gradient_tangent(pre(),s,[1e-14,0,0])


def test_water_fugacity_required_for_hydrated_flow_law():
    s=candidate()
    s["layers"]["mantle"]["ductile"]["fugacity_exponent"]=1.
    with pytest.raises(ValueError,match="FIELD_WATER_MISSING"):
        potential_gradient_tangent(pre(),s,[1e-14,0,0])


def test_source_lithology_and_brittle_yield_not_promoted():
    state=potential_gradient_tangent(pre(),candidate(),[2e-13,-1e-13,0])
    assert state["layers"][0]["effective_3D_DP_yield_min_max_Pa"][0]>0
    assert state["smooth_cap_not_ideal_Drucker_Prager_plasticity"]
    assert state["physical_material_G2_authorized"] is False


def test_dp_pressure_conventions_are_explicit_and_not_equivalent():
    """Both first-party ASPECT descriptions exist; require exact model ID."""
    import math
    source = candidate()["layers"]["crust"]
    pressure = np.array([1.e8, 3.e8])
    temperature = np.array([850., 950.])
    y = {}
    for variant in DRUCKER_PRAGER_PRESSURE_TERMS:
        law = {**source, "brittle":{**source["brittle"],
                "drucker_prager_pressure_convention":variant}}
        alpha, coeff, yield_stress = layer_material(
            law,temperature,pressure,1e-14)
        assert alpha == pytest.approx(0.25)
        assert np.all(coeff>0)
        y[variant]=yield_stress
    y6=y["ASPECT_RHEOLOGY_DP_3D_6P"]
    y2=y["ASPECT_LEGACY_VISCOPLASTIC_3D_2P"]
    phi=math.radians(30.)
    cohesion_term=(6*5e6*math.cos(phi))/(
                    math.sqrt(3)*(3+math.sin(phi)))
    assert np.all(y6>y2)
    assert np.allclose(y6-cohesion_term,3*(y2-cohesion_term),rtol=1e-12)


def test_dp_pressure_convention_cannot_be_silent():
    s=candidate()
    del s["layers"]["mantle"]["brittle"]["drucker_prager_pressure_convention"]
    with pytest.raises(ValueError,match="DP_PRESSURE_CONVENTION_UNDECLARED"):
        potential_gradient_tangent(pre(),s,[2e-14,-1e-14,1e-14])

def test_cubic_interior_temperature_maximum_cannot_escape_gauss_points():
    p=pre()
    L=p["crust_thickness_m"]
    p["layer1_c0_k"]=800.
    p["layer1_c1_k_m"]=200./L
    p["layer1_c2_k_m2"]=-200./L**2
    s=candidate()
    # True mid-layer maximum = 850 K, but 12-point Gauss max < 849.5 K.
    s["layers"]["crust"]["ductile"]["valid_temperature_k"]=[250.,849.5]
    with pytest.raises(ValueError,match="CREEP_LAB_PT_RATE_OUTSIDE_VALIDITY"):
        potential_gradient_tangent(p,s,[2e-14,-1e-14,1e-14])
