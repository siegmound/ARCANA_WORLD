from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'experiments/r6_thermo_provider_pilot_v1'))
from arcana_g37_independent_column_pressure import integrate_column,manufactured_selftest

def test_manufactured_pressure_branches():
    assert manufactured_selftest()['screen_pass']

@pytest.mark.parametrize('slope',[0.,.001,-.001])
def test_p_z_T_rho_analytic(slope):
    # Constant rho0, alpha and linear T(z): independent analytic p(z,T,rho).
    stop=np.array([5500.]); rho0=3300.; alpha=3e-5; t0=280.
    density=lambda h: rho0*(1-alpha*(t0+slope*h))
    actual=integrate_column(np.array([100.]),stop,np.array([9.82]),np.array([1000.]),np.array([1000.]),density)
    expect=9.82*rho0*((1-alpha*t0)*stop-alpha*slope*stop**2/2)
    assert actual[0]==pytest.approx(expect[0],rel=1e-14)

@pytest.mark.parametrize('stop,gravity,km', [(-1.,9.82,1000.),(100.,0.,1000.),(100.,9.82,0.),(301000.,9.82,1000.)])
def test_invalid_runtime_domain_rejected(stop,gravity,km):
    with pytest.raises(ValueError):
        integrate_column(*[np.array([v]) for v in (100.,stop,gravity,km,1000.)],lambda h: np.full_like(h,3000.))

def test_wrong_density_changes_pressure():
    args=[np.array([v]) for v in (100.,5500.,9.82,1000.,1000.)]
    good=integrate_column(*args,lambda h:np.full_like(h,3000.))
    wrong=integrate_column(*args,lambda h:np.full_like(h,3300.))
    assert abs(wrong[0]-good[0])/good[0]>.09


def test_last_valid_reference_interval_is_not_rejected():
    args=[np.array([v]) for v in (100.,299600.,9.82,1000.,1000.)]
    result=integrate_column(*args,lambda h:np.full_like(h,3000.))
    assert result[0]==pytest.approx(9.82*3000.*299600.,rel=1e-14)
