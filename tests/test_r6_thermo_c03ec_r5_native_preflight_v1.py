import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r5_native_preflight as r


def ready():
    p=r.PreflightDialogue()
    raw=r.dialogue.PROJECT
    assert p.next_response(raw)==b"c03d\n"
    raw+=r.dialogue.BULK
    assert p.next_response(raw)==b"n\n"
    return p,raw


def test_wait_for_complete_potential_line():
    p,raw=ready()
    raw+=r.dialogue.PT
    cursor=p.cursor
    assert p.next_response(raw) is None
    raw+=b" T(K) P(bar)"
    assert p.next_response(raw) is None and p.cursor==cursor
    raw+=b" Y(CO2)  \n"
    assert p.next_response(raw)==r.SENTINEL
    assert p.state=="SENTINEL_SENT"
    assert p.next_response(raw) is None


@pytest.mark.parametrize("fields",[b"T(K) P(bar)",b"P(bar) T(K) Y(CO2)",
                                   b"T(K) P(bar) Y(CO2) X",b"T(K) P(bar) X(CO2)"])
def test_unexpected_potential_fields(fields):
    p,raw=ready()
    with pytest.raises(ValueError,match="UNEXPECTED_POTENTIAL_FIELDS"):
        p.next_response(raw+r.dialogue.PT+b" "+fields+b"\n")


def test_duplicate_pt_rejected():
    p,raw=ready()
    prompt=r.dialogue.PT+b" T(K) P(bar) Y(CO2)\n"
    raw+=prompt
    assert p.next_response(raw)==r.SENTINEL
    with pytest.raises(ValueError,match="UNEXPECTED_PT_STATE"):
        p.next_response(raw+prompt)


def test_full_readback():
    p=r.PreflightDialogue()
    raw=r.dialogue.PROJECT
    assert p.next_response(raw)==b"c03d\n"
    raw+=b"\n"+r.r2.H2_WARNING+b"\n"+r.dialogue.WARNING
    assert p.next_response(raw)==b"y\n"
    raw+=r.dialogue.BULK
    assert p.next_response(raw)==b"n\n"
    raw+=r.dialogue.PT+b" T(K) P(bar) Y(CO2)\n"
    assert p.next_response(raw)==r.SENTINEL
    result={"dialogue":{"events":p.events,"state":p.state,"acknowledged_warning_codes":["013"],
                        "scientific_warning_acceptance":False},
            "warning_codes":["013"],"acknowledged_species":["H2"]}
    r.verify_readback(raw,b"c03d\ny\nn\n0 0 0\n",result)
    assert result["fluid_semantics_qualified"] is False
    with pytest.raises(ValueError,match="DIALOGUE_RECONCILIATION"):
        r.verify_readback(raw,b"c03d\ny\nn\n0 0\n",result)


def test_source_guard():
    src=(b"write (*,1070) (vname(jv(i)), i = 1, ipot)\n"
         b"read (*,*,iostat=ier) (v(jv(i)), i = 1, ipot)\n"
         b"if (ier.ne.0) cycle\nif (v(1).eq.0d0) exit\ncall meemum (bad)\n"
         b"Enter (T = 0 to quit)\n")
    assert r.verify_sentinel_source(src)["equilibrium_call_after_exit_guard"]
    with pytest.raises(ValueError,match="SENTINEL_SOURCE_DRIFT"):
        r.verify_sentinel_source(src.replace(b"if (ier.ne.0) cycle",b"continue"))


def test_new_archive():
    assert r.OUT.name.endswith("NEW05") and r.OUT!=r.r4.OUT
