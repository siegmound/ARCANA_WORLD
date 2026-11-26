import pytest
from experiments.r6_thermo_provider_pilot_v1 import c03d_r3_composition_audit as a
from experiments.r6_thermo_provider_pilot_v1 import c03d_native_dialogue as d

W966=(b"**warning ver966** EoS code 1 for O2 in data file hp02ver.dat requires "
      b"volumetric data. The code will automatically be set to 0")
W968=(b"**warning ver968** O2 is a name reserved for fluid species in hp02ver.dat "
      b"G(Pr,T) activity or fugacity of O2")
COMP={"SIO2","O2","CO2"}
ACTIVE={"SIO2","O2"}


def test_audit_comments_parentheses_and_exact_signed_sum():
    raw=b"|fake EoS = 2\n|O2(1)\nSi(s) EoS = 2 | metal\n | comment\nSIO2(1)O2(-1)\n"
    z=a.inventory(raw,COMP,ACTIVE)
    assert set(z)=={"Si(s)"} and z["Si(s)"]["total"]=="0"
    assert z["Si(s)"]["nonpositive"] and not z["Si(s)"]["outside_active_components"]


def test_outside_component_is_not_compatible():
    z=a.inventory(b"gph EoS = 2\nO2(-1)CO2(1)\n",COMP,ACTIVE)
    assert z["gph"]["nonpositive"] and z["gph"]["outside_active_components"]==["CO2"]


def test_malformed_record_rejected():
    with pytest.raises(ValueError,match="UNPARSED_COMPOSITION"):
        a.inventory(b"Si(s) EoS = 2\nSIO2(1) garbage\n",COMP,ACTIVE)


def test_duplicate_record_rejected():
    with pytest.raises(ValueError,match="DUPLICATE_EOS"):
        a.inventory(b"x EoS = 2\nO2(1)\nx EoS = 2\nO2(1)\n",COMP,ACTIVE)


def advance(allow):
    state=d.Dialogue(allow_si013=allow)
    raw=d.PROJECT
    assert state.next_response(raw)==b"c03d\n"
    raw+=W966+d.WARNING
    assert state.next_response(raw)==b"y\n"
    raw+=W968+d.WARNING
    assert state.next_response(raw)==b"y\n"
    return state,raw


def test_audited_si_warning_then_zero_pt():
    state,raw=advance(True)
    raw+=d.SI013+d.WARNING
    assert state.next_response(raw)==b"y\n"
    assert state.acknowledged==["966","968","013"]
    raw+=d.BULK
    assert state.next_response(raw)==b"n\n"
    raw+=d.PT
    assert state.next_response(raw)==b"0 0\n"


def test_si_warning_without_audit_fails_closed():
    state,raw=advance(False)
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        state.next_response(raw+d.SI013+d.WARNING)


def test_different_species_and_changed_message_fail_closed():
    for msg in (d.SI013.replace(b"Si(s)",b"SiC"),d.SI013.replace(b"<= 0",b"> 0")):
        state,raw=advance(True)
        with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
            state.next_response(raw+msg+d.WARNING)


def test_repeated_si_warning_fails_closed():
    state,raw=advance(True)
    raw+=d.SI013+d.WARNING
    assert state.next_response(raw)==b"y\n"
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        state.next_response(raw+d.SI013+d.WARNING)
