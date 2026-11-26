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



def _si_prompt(block=None):
    return b"\n"+(c.dialogue.SI013 if block is None else block)+b"\n"+c.dialogue.WARNING


def test_r1_two_exact_si013_then_zero_pt():
    p=c.PreflightDialogue()
    raw=c.dialogue.PROJECT
    assert p.next_response(raw)==b"c03d\n"
    for occurrence in (1,2):
        raw+=_si_prompt()
        assert p.next_response(raw)==b"y\n"
        assert p.events[-1]["occurrence"]==occurrence
        assert p.next_response(raw) is None
    assert p.acknowledged==["013","013"]
    raw+=c.dialogue.BULK
    assert p.next_response(raw)==b"n\n"
    raw+=c.dialogue.PT
    assert p.next_response(raw)==b"0 0\n"
    assert p.state=="SENTINEL_SENT"


def test_r1_third_si013_rejected_without_advancing():
    p=c.PreflightDialogue()
    raw=c.dialogue.PROJECT
    p.next_response(raw)
    for _ in range(2):
        raw+=_si_prompt()
        assert p.next_response(raw)==b"y\n"
    cursor=p.cursor
    with pytest.raises(ValueError,match="SI013_REPEAT_LIMIT"):
        p.next_response(raw+_si_prompt())
    assert p.cursor==cursor and p.acknowledged==["013","013"]


@pytest.mark.parametrize("block",[c.dialogue.SI013.replace(b"Si(s)",b"Fe(s)"),
                                 b"**warning ver999** unknown"])
def test_r1_changed_or_unknown_second_warning_rejected(block):
    p=c.PreflightDialogue()
    raw=c.dialogue.PROJECT
    p.next_response(raw)
    raw+=_si_prompt()
    assert p.next_response(raw)==b"y\n"
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        p.next_response(raw+_si_prompt(block))
    assert p.acknowledged==["013"]


def test_r1_exact_warning_wrong_state_rejected():
    p=c.PreflightDialogue()
    raw=c.dialogue.PROJECT
    p.next_response(raw)
    raw+=c.dialogue.BULK
    assert p.next_response(raw)==b"n\n"
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        p.next_response(raw+_si_prompt())
    assert p.acknowledged==[]


@pytest.mark.parametrize("code",["017","059","966","968"])
def test_r1_forbidden_warning_after_exact_acknowledgement(code):
    p=c.PreflightDialogue()
    raw=c.dialogue.PROJECT
    p.next_response(raw)
    raw+=_si_prompt()
    assert p.next_response(raw)==b"y\n"
    with pytest.raises(ValueError,match="FORBIDDEN_NATIVE_DIAGNOSTIC"):
        p.next_response(raw+_si_prompt(b"**warning ver"+code.encode()+b"** bad"))


def test_r1_retry_archive_is_distinct():
    assert c.FAILED_OUT.name.endswith("NEW01")
    assert c.OUT.name.endswith("NEW02")
    assert c.OUT!=c.FAILED_OUT
    assert c.MAX_SI013_ACKNOWLEDGEMENTS==2
