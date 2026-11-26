import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_native_preflight as c


def test_controller_zero_pt_without_warnings():
    p=c.PreflightDialogue()
    raw=c.dialogue.PROJECT
    assert p.next_response(raw)==b"c03d\n"
    raw+=c.dialogue.BULK
    assert p.next_response(raw)==b"n\n"
    raw+=c.dialogue.PT
    assert p.next_response(raw)==b"0 0\n"
    assert p.state=="SENTINEL_SENT"


def test_controller_allows_only_exact_silicon_diagnostic():
    p=c.PreflightDialogue()
    raw=c.dialogue.PROJECT
    p.next_response(raw)
    raw+=b"\n"+c.dialogue.SI013+b"\n"+c.dialogue.WARNING
    assert p.next_response(raw)==b"y\n"
    assert p.acknowledged==["013"]


@pytest.mark.parametrize("code",["017","059","966","968"])
def test_forbidden_warning(code):
    p=c.PreflightDialogue()
    with pytest.raises(ValueError,match="FORBIDDEN_NATIVE_DIAGNOSTIC"):
        p.next_response(c.dialogue.PROJECT+b"\n**warning ver"+code.encode()+b"** bad")


def test_unknown_warning_rejected():
    p=c.PreflightDialogue()
    raw=c.dialogue.PROJECT
    p.next_response(raw)
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        p.next_response(raw+b"\n**warning ver999** unknown\n"+c.dialogue.WARNING)


def test_heading_readback():
    assert c.heading_tokens("Saturated phase components:\n\n H2O\n\n","Saturated phase components:")==["H2O"]
    assert c.heading_tokens("no such section","Saturated phase components:") is None


def test_o2_retained_as_component_not_phase():
    assert "O2" in c.ORDER and "O2" in c.EXCLUDED and "H2O" not in c.ORDER
    assert len(c.ORDER)==9 and len(c.EXCLUDED)==8


def test_section_rows():
    assert c.section_rows("begin saturated phase component list\nH2O\nend saturated phase component list\n","saturated phase component list")==["H2O"]
    assert c.section_rows("begin saturated component list\n\nend saturated component list\n","saturated component list")==[]
