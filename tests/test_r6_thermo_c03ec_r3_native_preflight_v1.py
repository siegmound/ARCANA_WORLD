import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03ec_r3_native_preflight as r


def prompt(block):
    return b"\n"+block+b"\n"+r.dialogue.WARNING


def initial():
    p=r.PreflightDialogue()
    raw=r.dialogue.PROJECT
    assert p.next_response(raw)==b"c03d\n"
    return p,raw


def test_exact_observed_sequence_then_sentinel():
    p,raw=initial()
    for block in (r.dialogue.SI013,r.dialogue.SI013,r.r2.H2_WARNING):
        raw+=prompt(block)
        assert p.next_response(raw)==b"y\n"
        assert p.next_response(raw) is None
    assert p.species_counts=={"Si(s)":2,"H2":1}
    raw+=r.dialogue.BULK
    assert p.next_response(raw)==b"n\n"
    raw+=r.dialogue.PT
    assert p.next_response(raw)==b"0 0\n"
    assert p.state=="SENTINEL_SENT"


@pytest.mark.parametrize("block,limit",[(r.dialogue.SI013,2),(r.r2.H2_WARNING,1)])
def test_species_specific_limit(block,limit):
    p,raw=initial()
    for _ in range(limit):
        raw+=prompt(block)
        assert p.next_response(raw)==b"y\n"
    cursor=p.cursor
    with pytest.raises(ValueError,match="REPEAT_LIMIT"):
        p.next_response(raw+prompt(block))
    assert p.cursor==cursor


@pytest.mark.parametrize("block",[r.r2.H2_WARNING.replace(b"H2",b"H2O"),
                                 r.r2.H2_WARNING.replace(b"legitimate",b"unknown"),
                                 b"**warning ver999** unknown"])
def test_unknown_or_altered_rejected(block):
    p,raw=initial()
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        p.next_response(raw+prompt(block))


@pytest.mark.parametrize("code",["017","059","966","968"])
def test_forbidden(code):
    p,raw=initial()
    with pytest.raises(ValueError,match="FORBIDDEN_NATIVE_DIAGNOSTIC"):
        p.next_response(raw+prompt(b"**warning ver"+code.encode()+b"** bad"))


def test_h2_wrong_state():
    p,raw=initial()
    raw+=r.dialogue.BULK
    assert p.next_response(raw)==b"n\n"
    with pytest.raises(ValueError,match="UNAPPROVED_INTERACTIVE_WARNING"):
        p.next_response(raw+prompt(r.r2.H2_WARNING))


def test_new_archive():
    assert r.OUT not in (r.c.OUT,r.c.FAILED_OUT,r.r2.OUT)
    assert r.OUT.name.endswith("NEW03")
