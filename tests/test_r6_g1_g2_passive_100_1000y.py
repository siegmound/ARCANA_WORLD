"""Synthetic numerical contract checks; FAIR source integration is separate."""
import math
import numpy as np
import pytest

from experiments.global_t0_kinematic_baseline_v1.benchmark import unit_xyz, rotate_xyz
from experiments.plate58_deforming_explore_v1.g1_g2_passive_100_1000y import (
    assess_g2_column, triangle_metric_drift, CouplingError,
)


def pre():
    return {
        "crust_thickness_m":28000.,
        "mantle_lithosphere_thickness_m":52000.,
        "crust_density_kg_m3":2750.,
        "mantle_density_kg_m3":3300.,
        "lab_depth_m":80000.,
        "surface_temperature_k":280.,
        "moho_temperature_k":1050.,
        "lab_temperature_k":1600.,
        "layer1_z0_m":0.,"layer1_z1_m":28000.,
        "layer2_z0_m":28000.,"layer2_z1_m":80000.,
        "layer1_c0_k":280.,"layer1_c1_k_m":(1050.-280.)/28000.,
        "layer1_c2_k_m2":0.,"layer1_c3_k_m3":0.,
        "layer2_c0_k":1050.,"layer2_c1_k_m":(1600.-1050.)/52000.,
        "layer2_c2_k_m2":0.,"layer2_c3_k_m3":0.,
    }


def test_two_layer_source_profile_passes_without_material_approval():
    result=assess_g2_column(pre())
    assert result["eligible"] is True
    assert result["crust_temperature_k"]==(280.,1050.)
    assert result["mantle_temperature_k"]==(1050.,1600.)
    assert result["areal_column_mass_proxy_kg_m2"]==pytest.approx(2750*28000+3300*52000)
    assert result["thermal_LAB_is_not_mechanical_LAB"] is True
    assert "material_authorized" not in result


def test_invalid_lithospheric_layer_is_reported_not_filled():
    p=pre()
    p["layer2_z0_m"]+=3
    result=assess_g2_column(p)
    assert not result["eligible"]
    assert result["reason"]=="INVALID_SOURCE_LAYER_GEOMETRY"


def test_nonfinite_thermal_polynomial_fails_closed():
    p=pre()
    p["layer1_c1_k_m"]=math.nan
    r=assess_g2_column(p)
    assert not r["eligible"]
    assert r["reason"]=="INVALID_SOURCE_THERMAL_CUBIC"


@pytest.mark.parametrize("years",[100,1000])
def test_one_plate_pure_rigid_rotation_gives_zero_strain_metric(years):
    xyz=unit_xyz([[10,-159],[10,-158],[11,-158],[11,-159]])
    faces=np.array([[0,1,2],[0,2,3]])
    omega=np.array([2.e-8,-1.e-8,7.e-9])
    moved=rotate_xyz(xyz,omega,years)
    delta=triangle_metric_drift(xyz,moved,faces)
    assert delta<1e-11


def test_synthetic_nonrigid_motion_detected():
    xyz=unit_xyz([[10,-159],[10,-158],[11,-158]])
    moved=xyz.copy()
    moved[1]=unit_xyz([[10,-157.95]])[0]
    delta=triangle_metric_drift(xyz,moved,[[0,1,2]])
    assert delta>1e-3


def test_nonfinite_kinematics_are_rejected():
    xyz=unit_xyz([[10,-159],[10,-158],[11,-158]])
    moved=xyz.copy()
    moved[0,0]=float("nan")
    with pytest.raises(CouplingError,match="METRIC_INPUT_INVALID"):
        triangle_metric_drift(xyz,moved,[[0,1,2]])

def test_thermal_moho_anchor_mismatch_detected():
    p=pre()
    p["moho_temperature_k"]=1051.
    r=assess_g2_column(p)
    assert r["reason"]=="THERMAL_PROFILE_ANCHOR_MISMATCH"


def test_thermal_ceiling_violation_detected():
    p=pre()
    p["lab_temperature_k"]=2000.
    p["layer2_c1_k_m"]=(2000.-1050.)/52000.
    r=assess_g2_column(p)
    assert r["reason"]=="GOVERNED_THERMAL_CEILING_VIOLATION"
