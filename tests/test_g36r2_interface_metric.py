"""Portable metric/gate regression: NumPy only, no FAIR paths or mock imports."""
from pathlib import Path
import importlib.util
import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('interface_metrics', Path(__file__).parents[1] /
    'experiments/r6_thermo_provider_pilot_v1/arcana_interface_metrics.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_full_selftest():
    assert m.metric_selftest()['screen_pass']


@pytest.mark.parametrize('reaction,expected', [([-3.,-4.],0.),([3.,4.],2.),([0.,0.],1.),
    ([-2.97,-3.96],.01),([-30.,-40.],.9)])
def test_known_forces(reaction, expected):
    assert m.force_diagnostic([3.,4.],reaction)['action_reaction_relative'] == pytest.approx(expected)


@pytest.mark.parametrize('scale',[1e-200,1.,1e200])
def test_scale_and_exchange_invariance(scale):
    fl=np.array([3.,4.])*scale; fm=np.array([-2.,-4.])*scale
    a=m.force_diagnostic(fl,fm); b=m.force_diagnostic(fm,fl)
    assert a['action_reaction_relative']==pytest.approx(.2)
    assert a['action_reaction_relative']==b['action_reaction_relative']


@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-float('inf')])
def test_nonfinite_input_rejected(bad):
    with pytest.raises(ValueError): m.force_diagnostic([3.,4.],[bad,0.])


@pytest.mark.parametrize('fl,fm',[([],[]),([1.],[1.,2.]),([1j],[1.])])
def test_bad_shape_or_type_rejected(fl,fm):
    with pytest.raises(ValueError): m.force_diagnostic(fl,fm)


@pytest.mark.parametrize('fm',[[3.,4.],[0.,0.],[-2.97,-3.96]])
def test_real_balance_gate_rejects_wrong_reaction(fm):
    d=m.force_diagnostic([3.,4.],fm)
    assert not m.balance_screen(1.,1.,0.,0.,d['action_reaction_relative'],0.,0.,0.,d['nonzero_coupling'])


def test_zero_forces_do_not_qualify_coupling():
    d=m.force_diagnostic([0.,0.],[0.,0.])
    assert d['action_reaction_relative']==0.
    assert not m.balance_screen(1.,1.,0.,0.,0.,0.,0.,0.,d['nonzero_coupling'])


def test_old_formula_rejects_balanced_pair():
    fl=np.array([3.,4.]); fm=-fl
    legacy=np.linalg.norm((fl+fm)-fl)/np.linalg.norm(fl)
    assert legacy==1.
    assert not m.balance_screen(1.,1.,0.,0.,legacy,0.,0.,0.)
    assert m.balance_screen(1.,1.,0.,0.,m.force_diagnostic(fl,fm)['action_reaction_relative'],0.,0.,0.)


@pytest.mark.parametrize('value',[1e-11,float('nan'),float('inf'),-1.])
def test_threshold_and_nonfinite_gate(value):
    assert not m.balance_screen(1.,1.,0.,0.,value,0.,0.,0.)
