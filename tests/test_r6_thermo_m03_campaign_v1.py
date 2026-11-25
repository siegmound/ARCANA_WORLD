import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_m03_fair as m


def fake(x,kind,cut,reverse=False):
    f=2*m.THRESHOLD if (x>=cut)!=reverse else 0.
    return {"case":str(x),"phases":{"g":f} if kind=="garnet" else {},
            "aggregate_mass_fractions":[1-f,f,0.] if kind=="melt" else [1.,0.,0.]}


@pytest.mark.parametrize("kind,reverse",[("garnet",False),("garnet",True),("melt",False)])
def test_bounded_opposite_bracket(kind,reverse):
    f=lambda x:fake(x,kind,.6,reverse)
    out=m.bracket((0.,f(0.)),(1.,f(1.)),kind,lambda x,i:f(x))
    assert out["lower_coordinate"]<=.6<=out["upper_coordinate"]
    assert out["width"]==.125
    assert (out["lower_mass_fraction"]>=m.THRESHOLD)!=(out["upper_mass_fraction"]>=m.THRESHOLD)
    assert not out["unique_or_monotone_boundary_proven"]


def test_unbracketed_rejected():
    f=lambda x:fake(x,"garnet",2.)
    with pytest.raises(ValueError,match="M03_NO_OPPOSITE_ENDPOINTS"):
        m.bracket((0.,f(0.)),(1.,f(1.)),"garnet",lambda x,i:f(x))


def test_absent_phase_and_threshold():
    a={"phases":{},"aggregate_mass_fractions":[1.,0.,0.]}
    assert not m.present(a,"garnet")
    a["phases"]["g"]=m.THRESHOLD
    assert m.present(a,"garnet")
    a["phases"]["g"]=float("nan")
    with pytest.raises(ValueError,match="M03_PHASE_FRACTION"):
        m.present(a,"garnet")


def test_melt_uses_aggregate_not_phase_alias():
    a={"phases":{"liq":.01},"aggregate_mass_fractions":[1.,0.,0.]}
    assert not m.present(a,"melt")
    a["aggregate_mass_fractions"]=[.99,.01,0.]
    assert m.present(a,"melt")


def test_budget_bounds():
    assert m.MAX_POINTS==2*m.STEPS+2+m.STEPS==11
