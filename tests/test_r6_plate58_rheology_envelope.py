"""Pure numerical tests of source-bound G2 lab/PT diagnostic, no solver."""
import math
import pytest
from experiments.plate58_deforming_explore_v1.rheology_envelope import (
    GT_A_MPA, GT_N, GT_LAB_TEMP_K, lithostatic_proxy_pa,
    log_triaxial_differential_stress_pa, nominal_flow_stress_pa,
    polynomial_temperature, slope_only_fit_check,
)


def synthetic_pre():
    return {
        "layer1_z0_m":0., "layer1_z1_m":28_000.,
        "layer1_c0_k":280., "layer1_c1_k_m":0.02,
        "layer1_c2_k_m2":0., "layer1_c3_k_m3":0.,
        "layer2_z0_m":28_000.,"layer2_z1_m":80_000.,
        "layer2_c0_k":840.,"layer2_c1_k_m":0.01,
        "layer2_c2_k_m2":0.,"layer2_c3_k_m3":0.,
        "crust_thickness_m":28_000.,"lab_depth_m":80_000.,
        "crust_density_kg_m3":2750.,"mantle_density_kg_m3":3300.,
    }


def test_temperature_polynomial_degree_one_reference():
    p=synthetic_pre()
    assert polynomial_temperature(p,1,0)==280.
    assert polynomial_temperature(p,1,28_000)==840.
    assert polynomial_temperature(p,2,80_000)==1360.


def test_temperature_layer_bounds_reject():
    with pytest.raises(ValueError,match="PRE_TEMPERATURE_DEPTH"):
        polynomial_temperature(synthetic_pre(),1,28_001)


def test_lithostatic_pressure_is_continuous_at_moho():
    p=synthetic_pre()
    assert lithostatic_proxy_pa(p,28_000)==pytest.approx(9.82*2750*28000)
    assert lithostatic_proxy_pa(p,80_000)==pytest.approx(
        9.82*(2750*28000+3300*52000))


def test_pressure_depth_rejected():
    with pytest.raises(ValueError,match="PRE_PRESSURE_DEPTH"):
        lithostatic_proxy_pa(synthetic_pre(),-1)


def test_flow_law_round_trip_of_triaxial_stress():
    n=4.0
    a=GT_A_MPA*1e6**(-n)
    rate=1e-14
    t=1200.
    q=223000.
    v=nominal_flow_stress_pa(log_triaxial_differential_stress_pa(
        eps_s=rate,temperature_k=t,a_pa_n_s=a,exponent_n=n,q_j_mol=q))
    recovered=a*v**n*math.exp(-q/(8.31446261815324*t))
    assert recovered==pytest.approx(rate,rel=1e-12)


def test_log_stress_correct_pressure_dependence():
    kwargs=dict(eps_s=1e-14,temperature_k=1300.,a_pa_n_s=1e-16,
                exponent_n=3.5,q_j_mol=530000.,
                activation_volume_m3_mol=14e-6)
    x=log_triaxial_differential_stress_pa(**kwargs,p_pa=0.)
    y=log_triaxial_differential_stress_pa(**kwargs,p_pa=2e9)
    assert y>x


def test_common_exponent_is_slope_only_and_pivot_exact():
    widths=[{"width_km":w,"nominal_extension_rate_s_inv":1e-14*100/w}
            for w in (10,100,300)]
    d=slope_only_fit_check(widths,0.267857)
    assert d["errors_by_law_and_width"]["GT_QUARTZITE"]["100"]["stress_fit_over_lab_ratio"]==1
    assert d["max_slope_only_absolute_pct"]>3.1
    assert d["max_slope_only_absolute_pct"]<5.0
    assert d["does_not_check_prefactor_or_full_depth_integral"]


def test_missing_width_rejected():
    with pytest.raises(ValueError,match="WIDTH_INVENTORY_CHANGED"):
        slope_only_fit_check([{"width_km":100,"nominal_extension_rate_s_inv":1e-14}],0.267857)


def test_ambient_lab_window_converted_from_celsius():
    assert GT_LAB_TEMP_K==(1173.15,1373.15)


@pytest.mark.parametrize("rate",[0.,-1.,float("nan")])
def test_nonphysical_rate_rejected(rate):
    with pytest.raises(ValueError,match="INVALID_STRAIN_RATE"):
        log_triaxial_differential_stress_pa(
            eps_s=rate,temperature_k=1000.,a_pa_n_s=1e-28,
            exponent_n=4.,q_j_mol=223000.)
