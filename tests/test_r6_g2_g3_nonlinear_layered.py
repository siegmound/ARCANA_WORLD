"""Synthetic nonlinear two-layer G2 and spherical G3 A coupled tests."""
import numpy as np
import pytest
from experiments.plate58_deforming_explore_v1.nonlinear_layered_g3 import (
    column_potential_gradient_tangent, spherical_candidate_element,
    ConstitutiveCandidateError, Q_3D_PLANE_STRESS_KINEMATIC, invariant_rate,
)
from experiments.plate58_deforming_explore_v1.spherical_exterior import frames_and_cartesian


def pre():
    return {"crust_thickness_m":28000.,"mantle_lithosphere_thickness_m":52000.,
        "crust_density_kg_m3":2750.,"mantle_density_kg_m3":3200.,
        "layer1_z0_m":0.,"layer1_z1_m":28000.,
        "layer2_z0_m":28000.,"layer2_z1_m":80000.,
        "layer1_c0_k":850.,"layer1_c1_k_m":0.,"layer1_c2_k_m2":0.,
        "layer1_c3_k_m3":0.,
        "layer2_c0_k":1450.,"layer2_c1_k_m":0.,"layer2_c2_k_m2":0.,
        "layer2_c3_k_m3":0.}


def spec(n1=4.,n2=3.5):
    def creep(n):
        return {"source_reference":"SYNTHETIC_DISLOCATION_LAW_NOT_ARCANA",
            "stress_convention":"ASPECT_2ETA_EPS_INVARIANT_SCALE",
            "A_pa_minus_n_s_inv":1e-30, "n":n,
            "E_j_mol":2.4e5, "V_m3_mol":0.,
            "fugacity_exponent":0.,"water_fugacity_pa":None,
            "reference_fugacity_pa":None,
            "valid_temperature_k":[200.,1800.],
            "valid_pressure_pa":[0.,5e9],
            "valid_strain_rate_s_inv":[1e-19,1e-10]}
    return {"authority":"ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED",
        "source_identifier":"SYNTHETIC_TWO_LAYER_NONLINEAR_TEST",
        "gravity_m_s2":9.81,"regularization_strain_rate_s_inv":1e-17,
        "integration":{"gauss_points_per_layer":12},
        "layers":{"crust":{"brittle_mechanical_closure":None,"ductile":creep(n1)},
                  "mantle":{"brittle_mechanical_closure":None,"ductile":creep(n2)}}}


def test_3d_incompressible_invariant_positive():
    e=np.array([1.,2.,3.])
    assert invariant_rate(e)==pytest.approx(np.sqrt(e@Q_3D_PLANE_STRESS_KINEMATIC@e))
    assert np.min(np.linalg.eigvalsh(Q_3D_PLANE_STRESS_KINEMATIC))>0


def test_two_exponents_energy_gradient_and_jacobian_finite_difference():
    x=np.array([2.e-14,-1.e-14,0.8e-14]); p=pre(); s=spec()
    st=column_potential_gradient_tangent(p,s,x)
    assert st["exponents_by_layer"]==pytest.approx([0.25,1/3.5])
    assert st["different_creep_exponents_supported"] is True
    assert np.min(np.linalg.eigvalsh(st["tangent_N_s_per_m"]))>0
    for j in range(3):
        h=1e-18; dx=np.eye(3)[j]*h
        plus=column_potential_gradient_tangent(p,s,x+dx)
        minus=column_potential_gradient_tangent(p,s,x-dx)
        grad=(plus["potential_N_per_m_s"]-minus["potential_N_per_m_s"])/(2*h)
        tangent=(plus["stress_resultant_N_per_m"]-minus["stress_resultant_N_per_m"])/(2*h)
        assert np.isclose(grad,st["stress_resultant_N_per_m"][j],rtol=2e-7)
        assert np.allclose(tangent,st["tangent_N_s_per_m"][:,j],rtol=5e-7)


def test_zero_velocity_regularized_tangent_and_zero_stress():
    z=column_potential_gradient_tangent(pre(),spec(),[0.,0.,0.])
    assert z["potential_N_per_m_s"]==0.
    assert np.all(z["stress_resultant_N_per_m"]==0)
    assert np.min(np.linalg.eigvalsh(z["tangent_N_s_per_m"]))>0


def test_missing_water_fugacity_fails_closed():
    s=spec();s["layers"]["crust"]["ductile"]["fugacity_exponent"]=1.
    with pytest.raises(ValueError):
        column_potential_gradient_tangent(pre(),s,[2e-14,0,0])


def test_lab_pt_window_fails_closed():
    s=spec();s["layers"]["crust"]["ductile"]["valid_temperature_k"]=[1000.,1800.]
    with pytest.raises(ConstitutiveCandidateError,match="DOMAIN_NOT_COVERED"):
        column_potential_gradient_tangent(pre(),s,[2e-14,0,0])


def test_material_authority_and_brittle_blocked():
    s=spec();s["authority"]="AUTHOR_RATIFIED"
    with pytest.raises(ConstitutiveCandidateError,match="AUTHORITY"):
        column_potential_gradient_tangent(pre(),s,[2e-14,0,0])
    s=spec();s["layers"]["crust"]["brittle_mechanical_closure"]={"cohesion_pa":0.}
    with pytest.raises(ConstitutiveCandidateError,match="BRITTLE_CLOSURE"):
        column_potential_gradient_tangent(pre(),s,[2e-14,0,0])


def test_spherical_nonnewtonian_element_jacobian():
    ll=np.array([[11.,20.],[11.,20.2],[11.2,20.]])
    v=np.array([0.,0.,3e-9,-2e-9,1e-9,-1e-9])
    s=spec()
    out=spherical_candidate_element(ll,v,pre(),s)
    assert out["consistent_tangent_N_s_per_m"].shape==(6,6)
    assert out["ShellSet_parity"] is False
    assert out["G3_external_force"] is None
    for j in range(6):
        h=1e-13
        dx=np.eye(6)[j]*h
        plus=spherical_candidate_element(ll,v+dx,pre(),s)
        minus=spherical_candidate_element(ll,v-dx,pre(),s)
        fd=(plus["internal_force_N"]-minus["internal_force_N"])/(2*h)
        assert np.allclose(fd,out["consistent_tangent_N_s_per_m"][:,j],rtol=5e-4,atol=1e-4)


def test_three_rigid_rotations_zero_internal_strain_on_facets():
    ll=np.array([[11.,20.],[11.,21.],[12.,20.]])
    xyz,_,east,north=frames_and_cartesian(ll)
    for omega in np.eye(3)*1e-15:
        v=np.cross(omega,xyz)
        vel=np.stack((np.einsum("ij,ij->i",v,east),
                      np.einsum("ij,ij->i",v,north)),axis=1).ravel()
        out=spherical_candidate_element(ll,vel,pre(),spec())
        assert out["strain_rate_s_inv"]<1e-23
        assert out["mechanical_solve_authorized"] is False


def test_two_triangle_global_nonlinear_tangent_reproducible():
    from experiments.plate58_deforming_explore_v1.nonlinear_layered_g3 import (
        assemble_candidate_exterior,
    )
    nodes=[101,102,103,104]
    faces={700:(101,102,103),701:(101,103,104)}
    ll={101:(11.,20.),102:(11.,20.2),103:(11.2,20.2),104:(11.2,20.)}
    v={101:(0.,0.),102:(3e-9,-2e-9),103:(1e-9,1e-9),104:(2e-9,3e-9)}
    p={tid:{**pre(),"PRE_projection_provenance":
            "EXPLICIT_TEST_COLUMN_NOT_VALIDATED_FOR_REAL_T0"} for tid in faces}
    laws={700:spec(4.,3.5),701:spec(3.5,3.5)}
    result=assemble_candidate_exterior(nodes,faces,ll,v,p,laws)
    K=result["global_consistent_tangent_N_s_per_m"]
    f=result["global_internal_force_N"]
    assert K.shape==(8,8) and np.allclose(K,K.T)
    assert result["source_parent_triangle_count"]==2
    assert result["PRE_projection_validated_for_real_T0"] is False
    assert result["global_external_and_basal_force_N"] is None
    dv=1e-13
    plus={n:tuple(x) for n,x in v.items()}
    minus={n:tuple(x) for n,x in v.items()}
    plus[103]=(v[103][0]+dv,v[103][1])
    minus[103]=(v[103][0]-dv,v[103][1])
    fp=assemble_candidate_exterior(nodes,faces,ll,plus,p,laws)["global_internal_force_N"]
    fm=assemble_candidate_exterior(nodes,faces,ll,minus,p,laws)["global_internal_force_N"]
    assert np.allclose((fp-fm)/(2*dv),K[:,4],rtol=5e-4,atol=1e-3)


def test_global_missing_PRE_projection_fails_closed():
    from experiments.plate58_deforming_explore_v1.nonlinear_layered_g3 import (
        assemble_candidate_exterior,
    )
    with pytest.raises(ConstitutiveCandidateError,match="PRE_INTERPOLATION_UNQUALIFIED"):
        assemble_candidate_exterior(
            [1,2,3,4],{1:(1,2,3)},
            {1:(11,20),2:(11,20.2),3:(11.2,20),4:(11.2,20.2)},
            {n:(0,0) for n in [1,2,3,4]},
            {1:pre()}, {1:spec()})


def test_n1_newtonian_limit_matches_previous_membrane_tensor():
    from experiments.plate58_deforming_explore_v1.nonlinear_layered_g3 import (
        Q_3D_PLANE_STRESS_KINEMATIC,
    )
    s=spec(1.,1.)
    for name in ("crust","mantle"):
        s["layers"][name]["ductile"]["E_j_mol"]=0.
        s["layers"][name]["ductile"]["A_pa_minus_n_s_inv"]=1e-18
    out=column_potential_gradient_tangent(pre(),s,[1e-14,-1e-14,0.4e-14])
    viscosity=(0.5/1e-18)*(28000+52000)
    expected=4*viscosity*Q_3D_PLANE_STRESS_KINEMATIC
    assert np.allclose(out["tangent_N_s_per_m"],expected,rtol=1e-12)
