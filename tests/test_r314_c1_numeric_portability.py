import numpy as np
import pytest
from arcana_worldsim.late_cenozoic import cha2_nested_50y as c1


def test_platform_stable_equivalence_accepts_sub_tolerance_libm_drift():
    ref=np.linspace(-2.0,2.0,1001,dtype=float)
    cand=ref.copy()
    cand[333]=np.nextafter(np.nextafter(ref[333], np.inf), np.inf)
    m=c1._numeric_equivalence('synthetic libm drift',cand,ref)
    assert m['platform_stable_numeric_equivalence'] is True
    assert m['max_abs_error'] > 0.0


def test_platform_stable_equivalence_rejects_material_formula_change():
    ref=np.ones(32,dtype=float)
    cand=ref.copy(); cand[7]+=1e-6
    with pytest.raises(ValueError, match='numerical reconstruction mismatch'):
        c1._numeric_equivalence('material change',cand,ref)


def test_tolerance_is_strict_relative_to_physical_signal():
    assert c1.FORMULA_EQ_RTOL <= 1e-10
    assert c1.FORMULA_EQ_ATOL <= 1e-12


def test_seal_backed_anchor_state_prefers_sealed_arrays():
    obj=c1.CHA2Nested50YRecentProvider.__new__(c1.CHA2Nested50YRecentProvider)
    n=5
    obj.history={
        'time_year_before_book':np.arange(n,dtype=float),
        'atmospheric_carbon_gtc':np.arange(n,dtype=float)+10,
        'ocean_carbon_gtc':np.arange(n,dtype=float)+20,
        'biosphere_soil_carbon_gtc':np.arange(n,dtype=float)+30,
        'active_geologic_carbon_gtc':np.arange(n,dtype=float)+40,
        'ice_volume_index':np.linspace(.1,.2,n),
        'overturning_strength':np.linspace(.8,1.0,n),
        'freshwater_forcing_sv':np.linspace(0,.1,n),
        'carbon_flux_volcanic_gtc_yr':np.linspace(.01,.02,n),
        'carbon_flux_weathering_gtc_yr':np.linspace(.02,.03,n),
        'carbon_flux_airsea_gtc_yr':np.linspace(.03,.04,n),
        'carbon_flux_biosphere_gtc_yr':np.linspace(.04,.05,n),
        'carbon_flux_fire_gtc_yr':np.linspace(.05,.06,n),
        'global_temperature_anomaly_c':np.linspace(-1.0,0.0,n),
    }
    formula={'temperature_raw_c':np.linspace(-0.9,0.1,n)}
    out=obj._seal_backed_raw_100y_history(formula)
    for key in (
        'atmospheric_carbon_gtc','ocean_carbon_gtc','biosphere_soil_carbon_gtc',
        'active_geologic_carbon_gtc','ice_volume_index','overturning_strength',
        'freshwater_forcing_sv','carbon_flux_volcanic_gtc_yr',
        'carbon_flux_weathering_gtc_yr','carbon_flux_airsea_gtc_yr',
        'carbon_flux_biosphere_gtc_yr','carbon_flux_fire_gtc_yr'):
        assert np.array_equal(out[key],obj.history[key])
    assert np.array_equal(out['temperature_raw_c']-out['temperature_raw_c'][-1],obj.history['global_temperature_anomaly_c'])
