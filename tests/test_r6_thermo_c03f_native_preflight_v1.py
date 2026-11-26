import pytest
from experiments.r6_thermo_provider_pilot_v1 import run_c03f_native_preflight as r


def ready():
    p=r.ClosedDialogue()
    p.state="AWAIT_PT"
    p.acknowledged=["966","968","013"]
    return p


def test_two_field_sentinel_waits_for_complete_line():
    p=ready()
    prompt=r.dialogue.PT+b" T(K) P(bar)"
    assert p.next_response(prompt) is None
    assert p.next_response(prompt+b"\n")==b"0 0\n"
    assert p.state=="SENTINEL_SENT"


def test_reject_saturated_prompt():
    with pytest.raises(ValueError,match="PT_FIELDS"):
        ready().next_response(r.dialogue.PT+b" T(K) P(bar) Y(CO2)\n")


def test_ack_guard():
    p=ready()
    p.acknowledged=[]
    with pytest.raises(ValueError,match="ACK_SEQUENCE"):
        p.next_response(r.dialogue.PT+b" T(K) P(bar)\n")


@pytest.mark.parametrize("code",["017","046","049","093","536"])
def test_unapproved_native_warning(code):
    with pytest.raises(ValueError,match="UNAPPROVED_DIAGNOSTIC"):
        ready().next_response(("**warning ver"+code+"**").encode())


def test_warning_counts_preserve_duplicates():
    assert r.warning_codes(b"**warning ver013**\n**warning ver013**")=={b"013":2}
