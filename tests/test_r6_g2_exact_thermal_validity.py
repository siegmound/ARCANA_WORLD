import numpy as np
import pytest
from experiments.plate58_deforming_explore_v1.g2_exact_thermal_validity import (
    exact_layer_temperature_bounds_k, require_laboratory_temperature_coverage,
    ThermalValidityError,
)


def pre(c=(800.,200./30000.,-200./30000.**2,0.)):
    return {"layer1_z0_m":0.,"layer1_z1_m":30000.,
            "layer1_c0_k":c[0],"layer1_c1_k_m":c[1],
            "layer1_c2_k_m2":c[2],"layer1_c3_k_m3":c[3],
            "layer2_z0_m":30000.,"layer2_z1_m":80000.,
            "layer2_c0_k":1450.,"layer2_c1_k_m":0.,
            "layer2_c2_k_m2":0.,"layer2_c3_k_m3":0.}


def test_midlayer_temperature_extremum_exact_not_gauss_sample():
    row=pre()
    mn,mx=exact_layer_temperature_bounds_k(row,1)
    assert (mn,mx)==pytest.approx((800.,850.))
    # 12-point Gauss quadrature does not sample x=0.5 precisely.
    gauss,_=np.polynomial.legendre.leggauss(12)
    zz=30000*(gauss+1)/2
    sampled_max=max(800+200*(zz/30000)-(200*(zz/30000)**2))
    assert sampled_max<850
    cap=(sampled_max+850)/2
    with pytest.raises(ThermalValidityError,match="OUTSIDE_VALIDITY"):
        require_laboratory_temperature_coverage(row,1,
                         {"valid_temperature_k":[300.,cap]})


def test_monotone_profile_bounds_at_endpoints():
    row=pre(c=(280.,.02,0.,0.))
    assert exact_layer_temperature_bounds_k(row,1)==pytest.approx((280.,880.))


def test_cubic_two_real_interior_extrema():
    # T(t)= 1000 + 100*(t-.2)*(t-.5)*(t-.8)
    c0=1000+100*(-.2)*(-.5)*(-.8)
    c1=100*(.2*.5+.2*.8+.5*.8)/30000.
    c2=-100*(.2+.5+.8)/(30000.**2)
    c3=100/(30000.**3)
    mn,mx=exact_layer_temperature_bounds_k(pre((c0,c1,c2,c3)),1)
    t=np.linspace(0,1,100001)
    y=1000+100*(t-.2)*(t-.5)*(t-.8)
    assert mn==pytest.approx(y.min(),abs=1e-7)
    assert mx==pytest.approx(y.max(),abs=1e-7)


def test_constant_profile_and_complete_laboratory_range():
    row=pre()
    assert exact_layer_temperature_bounds_k(row,2)==pytest.approx((1450.,1450.))
    out=require_laboratory_temperature_coverage(row,2,
                              {"valid_temperature_k":[1200.,1600.]})
    assert out["whole_layer_temperature_covered"] is True
    assert out["rock_identity_author_ratified"] is False


def test_gt95_cannot_be_used_for_cold_crust_by_extrapolation():
    row=pre(c=(280.,.02,0.,0.))
    with pytest.raises(ThermalValidityError,match="OUTSIDE_VALIDITY"):
        require_laboratory_temperature_coverage(row,1,
                     {"valid_temperature_k":[1173.15,1373.15]})


def test_invalid_negative_temperature_is_fail_closed():
    with pytest.raises(ThermalValidityError,match="INVALID_TEMPERATURE"):
        exact_layer_temperature_bounds_k(pre((-200.,0.,0.,0.)),1)


def test_nonfinite_cubic_is_fail_closed():
    with pytest.raises(ThermalValidityError,match="PRE_INVALID"):
        exact_layer_temperature_bounds_k(pre((800.,float("nan"),0.,0.)),1)
